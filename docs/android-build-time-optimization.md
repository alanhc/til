# 優化 Android Platform Build Time:從 Full Build 到快速迭代工作流

在 Android platform(AOSP / vendor codebase)開發中,最常見的時間黑洞是「改一行 code → full build → 燒錄整包 → 開機驗證」這個迴圈。一次 full build 動輒數十分鐘到數小時,如果每次改動都走完整流程,一天能驗證的次數非常有限。

本文整理實務上縮短這個迭代迴圈的方法,核心觀念只有一個:**大多數驗證不需要 full build,也不需要燒整包。**

## 一、Build 端優化

### 1. 只 build 受影響的 image

改動不同層的 code,只需要重建對應的 partition image:

| 改動範圍 | Build 指令 | 產出 |
|---|---|---|
| Framework / system apps | `m systemimage` | `system.img` |
| Vendor HAL / driver | `m vendorimage` | `vendor.img` |
| Kernel / DTS | 重打 boot | `boot.img` / `dtbo.img` |
| 單一模組 | `m <module>` 或 `mmm <path>` | 單一 jar / so / apk |

在 Soong 增量編譯下,這通常是幾分鐘等級,而不是 full build 的幾小時。

### 2. 保護增量編譯狀態

首次 full build 之後,`out/` 目錄就是最重要的資產:

- 不要隨手 `make clean` / 刪 `out/`
- 固定 shell 環境:環境變數改變、`lunch` target 切換都會讓 Soong invalidate 大量目標,觸發近乎全量的重建
- 用 `out/build.trace.gz`(Chrome 的 `chrome://tracing` 可開)分析時間實際花在哪個階段

### 3. 善用 prebuilt 與 build farm

不常改動的 partition(kernel、vendor、bootloader)不必自己 build:

- 直接拿 daily build 的 image 來搭配自己重建的部分
- 公司內部若有 distributed build / remote execution / prebuilt binary 機制,確認自己有接上——這通常是單機調校無法比擬的加速

### 4. 硬體是最大槓桿

- Build 目錄放 NVMe SSD
- RAM 至少 64GB,避免高 `-j` 時 swap
- CPU 核心數對 build time 幾乎是線性影響

## 二、燒錄端優化

### 1. 單 partition 燒錄

只燒有改動的 partition,不要整包 download:

```bash
fastboot flash system system.img
fastboot flash vendor vendor.img
fastboot flash boot boot.img
```

各家 SoC 的原廠下載工具通常也有 partial download 選項(只勾選改動的 partition),效果相同。

### 2. 大多數驗證根本不用燒錄

在 userdebug / eng build 上,`adb remount` + `adb sync` 是最快的驗證迴圈:

```bash
adb root
adb remount        # dynamic partition 裝置會走 overlayfs
adb sync           # 把 out/ 中改動的檔案同步到裝置
adb reboot         # 或只重啟受影響的 process
```

常見情境:

- **改 framework**:push `framework.jar` 後重啟 zygote(`stop && start`)即可
- **改 HAL / native so**:push so 後 kill 對應 service 讓它重啟
- **改 app**:直接 `adb install -r`

這個迴圈是秒級到分鐘級,和 full build + 整包燒錄相比是數量級的差異。

### 3. Dynamic partition 與 overlayfs

Launch with dynamic partitions 的裝置,`adb remount` 會自動使用 overlayfs,改動疊在原 partition 之上——不必擔心 partition 空間不足,也可以隨時 `adb remount -R` 還原。

## 三、建議的日常工作流

```
日常迭代:
  改 code → m <module> → adb remount + sync → 驗證邏輯
  (秒級~分鐘級,一天可迭代數十次)

階段確認:
  邏輯 OK → m systemimage / vendorimage → fastboot 燒單一 partition
  (幾分鐘~十幾分鐘)

最終驗證:
  送 case / 出 release 前 → full build → 燒完整 image → 完整驗證
  (一天一次,或每個 milestone 一次)
```

Full build 的定位應該是「最終確認」,而不是「每次改動的必經之路」。

## 四、常見障礙與對策

**user build 無法 remount(verity / verified boot 擋住)**
向 build team 要同版本的 userdebug build 做日常開發,只在最終驗證用 user build。

**流程規定必須燒完整 image**
區分「開發驗證」和「正式驗證」:開發階段用快速迴圈收斂問題,正式驗證才走完整流程。這不是繞過流程,而是減少走完整流程的次數。

**增量 build 常常莫名變成全量**
檢查是否有 script 每次都改動環境變數、touch 到 build 設定檔,或 CI 與本機共用 out/ 目錄互相污染。

## 附:App 層(Gradle)的對應做法

如果瓶頸在 app build 而非 platform:

- 開啟 configuration cache 與 build cache
- `org.gradle.parallel=true`
- 用 KSP 取代 kapt
- 拆 module 讓改動只影響局部

## 小結

優化 build time 的最大收益不在 build 系統本身的調校,而在**改變工作流**:讓每次改動只重建、只部署受影響的最小單位。Full build 太久不是問題的本質,「每次都需要 full build」才是。
