# 開機流程與 Bootloader 實戰:Chip Vendor 視角

> 系列文章之七。總覽請見《Chip Vendor 視角的 Android Build System》。

「開不了機」是 BSP 工程師的日常。要在幾分鐘內判斷卡在哪一階段、該抓什麼 log,前提是把整條開機鏈刻在腦子裡。本文從上電第一條指令走到桌面,並附各階段的除錯手法。

---

## 一、完整開機鏈

```
上電
 └─ ① BootROM / PBL(SoC 內建 ROM,信任根)
     └─ ② SBL / XBL / preloader(SoC vendor 的早期 loader:DDR init、電源樹)
         └─ ③ Bootloader(ABL/LK/U-Boot:AVB 驗證、選 slot、組 boot 參數)
             ├─ fastboot mode(刷機)
             ├─ recovery / rescue mode
             └─ ④ Kernel(GKI)+ ⑤ first-stage init(ramdisk)
                 └─ ⑥ second-stage init(/system/bin/init:解析 init.rc、載入 sepolicy、起 daemon)
                     └─ ⑦ zygote + system_server
                         └─ ⑧ Launcher(BOOT_COMPLETED)
```

### ① BootROM / PBL

燒在 SoC 矽片裡,不可改。工作:初始化最小硬體、從 boot device(UFS/eMMC 的固定位址)載入下一階段,並用 fuse 裡的 key hash 驗證其簽章。**這是整條 verified boot 鏈的信任根**。它也提供最底層的救磚介面(如 Qualcomm EDL、MTK BROM mode)——量產時要注意這些模式的存取管制,它們本身就是攻擊面。

### ② SBL / preloader(名稱依 SoC 廠而異)

Chip vendor 自己的 code:DDR 訓練與初始化、PMIC 設定、時脈樹、載入 TrustZone(TEE)與 bootloader。此階段掛掉的典型症狀是**完全黑屏、serial 只有幾行**——DDR 參數錯誤、電源時序問題都在這裡爆。

### ③ Bootloader(ABL / Little Kernel / U-Boot 衍生)

工作清單:

- 讀 **misc partition** 的 BCB(bootloader control block)決定進 normal / recovery / fastboot。
- **A/B slot 選擇**:讀 slot metadata(retry count、successful flag),失敗次數超限自動切 slot——這段邏輯在你手上,寫錯就是「更新後變磚」。
- **AVB 驗證**:驗 `vbmeta` → 驗 `boot`/`vendor_boot`/`dtbo`;鎖定狀態(LOCKED/UNLOCKED)決定驗證失敗是擋下還是警告。`fastboot flashing unlock` 會清 userdata(CDD 要求)。
- 組合 **device tree**(base DTB + DTBO overlay)與 **kernel cmdline / bootconfig**,跳進 kernel。

### ④→⑤ Kernel 與 first-stage init

GKI kernel 起來後,執行 ramdisk(`init_boot.img` 的 generic ramdisk + `vendor_boot.img` 的 vendor ramdisk 合併)裡的 first-stage init:

1. 掛 `/dev`、`/proc`、`/sys`
2. 載入 **first-stage kernel modules**(`vendor_boot` 裡的 `modules.load`)——storage、display 基本 driver
3. 解析 **fstab**(`fstab.<hardware>`),用 dm-verity/AVB 掛載 `super` 裡的 system/vendor/product
4. `switch_root` 到真正的 `/`,執行 second-stage init

**Storage driver 沒進 first-stage module list → 掛不了 system → 卡在這裡**,是 GKI porting 最經典的死法(詳見 GKI 篇)。

### ⑥ Second-stage init

`/system/bin/init` 開始跑 init 語言:

- 載入 SELinux policy,切換 enforcing
- 解析 `init.rc` 及所有 `/vendor/etc/init/*.rc`(你的 HAL service 都在這)
- 按 trigger 分階段:`early-init` → `init` → `late-init` → `on boot`,途中 `mount_all`、起 `servicemanager`、`hwservicemanager`、各 HAL
- property service 啟動,`ro.*` 定案

你的 `.rc` 檔語法錯誤、依賴的 property 沒人設、sepolicy 擋住 exec——都在這階段以「某個 service 沒起來」的形式出現。

### ⑦→⑧ Zygote 到桌面

`zygote` 預載 framework class 後 fork 出 `system_server`;system_server 起 AMS/WMS/PMS 等數十個系統服務,掃描 APK,最後發 `BOOT_COMPLETED`。BSP 常見的雷:HAL 沒 ready 導致 system_server 起服務時卡住或 crash 重啟(表現為 boot animation 無限轉圈)。

---

## 二、各階段除錯手法對照

| 卡住位置 | 症狀 | 抓什麼 |
|---|---|---|
| PBL/SBL | 全黑、無 USB 列舉 | **Serial console(UART)**,幾乎是唯一手段;檢查 boot device、DDR |
| Bootloader | 有 logo 後停住 / 進不了 fastboot | serial log 的 AVB 錯誤碼、slot metadata(`fastboot getvar all`) |
| Kernel early | logo 後重開機循環 | serial 上的 kernel panic;`pstore`/ramoops(重開後讀 `/sys/fs/pstore`) |
| first-stage init | 卡住不動 | serial 上 init 的 log(`init: ...`);檢查 fstab、modules.load |
| second-stage | 卡 boot animation | `adb logcat`(此時 adb 通常已通)、`logcat -b all`、看哪個 service 反覆 crash |
| zygote 之後 | 轉圈不進桌面 | logcat 找 system_server crash / watchdog;`dumpsys` |

三個要內建成肌肉記憶的工具:

```bash
# serial console:BSP 的生命線,新板 bringup 沒 UART 等於裸奔
# pstore:上一次 panic 的 kernel log 會留在 RAM
adb shell cat /sys/fs/pstore/console-ramoops-0

# bootloader 資訊
fastboot getvar all          # slot、unlock 狀態、AVB 狀態
adb reboot bootloader / recovery
```

**開機時間分析**:`adb shell su 0 bootstat` 之外,標準做法是 `dmesg` 時間戳 + `systrace/perfetto` 的 boot trace;init 支援 `androidboot.init_perf` 類參數輸出各階段耗時。優化順序通常是:kernel driver probe 平行化 → init.rc 依賴梳理 → zygote preload 與 dex 預編譯。

---

## 三、Chip vendor 的實務重點

**Bringup 順序**:新板子的標準路徑是 serial 先通 → SBL/DDR 穩定 → bootloader 進 fastboot(可刷機就有救)→ kernel 到 shell(先 permissive、砍掉非必要 module)→ 逐步把 driver、sepolicy、AVB 加回來。**一次只變一個變數**。

**Recovery/rescue 路徑**:量產裝置必須保證「任何 OTA 失敗都有路可退」:A/B fallback 是第一道,misc + recovery 是第二道,SoC 的 EDL/BROM 救磚是最後一道(通常僅工廠可用)。三條路都要在出貨前實測。

**boot 參數的傳遞**:kernel cmdline(舊)與 **bootconfig**(Android 12+ 建議,`vendor_boot` 攜帶)承載 `androidboot.*` 參數,init 與 framework 靠它們判斷硬體版本、序號、開機模式。參數名稱是介面,亂改會斷 framework 的假設。

**與 AVB/簽章的交叉**(詳見 OTA 篇):unlock 狀態的行為、orange/yellow/red state 的 UI、rollback index 的遞增時機,都是 bootloader 的責任。

---

## 結語

> **開機鏈是一條「信任與控制權逐級移交」的鏈:fuse 信 SBL,SBL 信 bootloader,bootloader 信 kernel,kernel 信 init,init 按劇本把整個 userspace 拉起來。除錯的本質就是找出移交在哪一環斷掉——而 serial console 是你在斷點前方唯一的眼睛。**
