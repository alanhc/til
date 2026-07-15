---
title: Android 名詞表
sidebar_label: Android 名詞表
sidebar_position: 1
---

# Android 名詞表

彙整知識庫中所有 Android / AOSP / Pixel 筆記出現過的名詞。
文章清單見 [Android / Pixel 系列文章索引](android_index.md)。

---

## 一、裝置與硬體代號

| 名詞 | 說明 | 出處 |
|---|---|---|
| **shiba** | Pixel 8 的**裝置**代號 | [pixel_hardware](../pixel_hardware.md) |
| **husky** | Pixel 8 Pro 的裝置代號 | [aosp_pixel_full_workflow](../aosp_pixel_full_workflow.md) |
| **shusky** | AOSP 中 shiba + husky 共用的 device 目錄（`device/google/shusky`） | [pixel_study](../pixel_study.md) |
| **zuma** | Google **Tensor G3** SoC（晶片）的代號 | [pixel_hardware](../pixel_hardware.md) |
| **ripcurrent** | Pixel 8 的 bootloader pack 版本前綴（如 `ripcurrent-16.4-14097582`），同時也是一個 lunch product | [pixel_study](../pixel_study.md) |
| **gs (Google Silicon)** | Kernel 分支命名前綴，如 `android-gs-zuma-...` | [pixel_hardware](../pixel_hardware.md) |
| **Tensor G3 / G5** | Google 自研 SoC。G5 為 Pixel 10 Pro 使用，TSMC 3nm、Imagination GPU | [android_pixel_learning](../android_pixel_learning.md) |
| **Baklava** | Android 16 的版本代號（Build ID 開頭的 `B`） | [Android_build_number](../Android_build_number.md) |
| **die shot** | 裸晶照片，可用來推測晶片資源配置與可能瓶頸 | [android_pixel_learning](../android_pixel_learning.md) |

---

## 二、Build ID 與版本對齊

| 名詞 | 說明 |
|---|---|
| **Build ID** | 如 `BP4A.251205.006`。`B`=Baklava(Android 16)、`P4A`=分支識別、`251205`=分支日期、`.006`=patch 序號 |
| **`ro.build.id`** | 用 `adb shell getprop ro.build.id` 查手機目前 build ID |
| **`ro.build.fingerprint`** | 完整版本指紋，如 `google/shiba/shiba:16/BP4A.251205.006/.../user/release-keys` |
| **AOSP source tag** | 對應 build ID 的原始碼 tag，如 `android-16.0.0_rXX`。查表：source.android.com/docs/setup/reference/build-numbers |
| **Vendor driver tarball** | Google 提供的閉源 blob 壓縮檔，如 `google_devices-shiba-bp1a.250505.005.b1-ef15dd6d.tgz` |
| **三者對齊** | **手機 build ID ↔ AOSP tag ↔ vendor driver** 必須指向同一個 build ID，否則會編譯失敗或開不了機 |
| **release config** | Android 14+ lunch 新增的中間欄位，即 build ID 分支代號小寫（`BP4A` → `bp4a`）。有效值見 `build/release/release_configs/` |
| **anti-rollback** | 防降級機制。刷入比目前更舊的 bootloader 會被拒絕：`image (bl1_a): rejected, anti-rollback` |

---

## 三、建置系統（Build System）

| 名詞 | 說明 |
|---|---|
| **repo** | Google 的多 git repository 管理工具 |
| **`repo init`** | 初始化 manifest。`--partial-clone` 減少下載量、`-b <tag>` 指定分支/tag |
| **`repo sync`** | 同步原始碼。`-c` 只 sync 當前 branch（省 ~50% 空間）、`-j8` 併行數（開太多易撞 503） |
| **manifest** | `.repo/manifests/default.xml`，記錄各 project 來源與 revision |
| **Soong / Blueprint** | 現代 AOSP 建置系統，設定檔為 `Android.bp` |
| **`Android.bp`** | Soong 的模組定義檔 |
| **`Android.mk`** | 舊版 Make-based 模組定義檔 |
| **Kati** | 將 `Android.mk` 轉譯為 Ninja 檔案的工具 |
| **Ninja** | 實際執行編譯的底層 build 工具 |
| **`source build/envsetup.sh`** | 載入 AOSP build 環境函式（lunch、m、get_build_var 等） |
| **`lunch`** | 選擇編譯目標。Android 14+ 為三段式：`aosp_shiba-bp1a-userdebug`（product-release-variant） |
| **`m`** | 編譯全部（等同 `make`）。Pixel 8 首次編譯約 1~3 小時 |
| **build variant** | `user`（正式）/ `userdebug`（可 adb root，效能測試用）/ `eng`（build 最快） |
| **`TARGET_PRODUCT`** | 編譯目標產品，如 `aosp_shiba` |
| **`TARGET_BUILD_VARIANT`** | 編譯變體，如 `userdebug` |
| **`PRODUCT_OUT`** | 產物目錄，如 `out/target/product/shiba`。用 `get_build_var PRODUCT_OUT` 取得 |
| **`AndroidProducts.mk`** | 定義該 device 有哪些 lunch 選項 |
| **`BoardConfig.mk`** | 板級硬體設定 |
| **`device-vendor.mk`** | vendor blob 整合進 build 系統的入口。**此檔不存在代表 extract 失敗** |
| **`android-info.txt`** | 裝置型號資訊檔。`fastboot flashall` 需要它，但**不在 `*.img` glob 範圍內**，跨機器打包容易漏 |
| **vendor proprietary blob** | 閉源驅動（modem firmware、camera HAL、ISP/GPU driver、Tensor 專屬模組），AOSP 樹不包含 |
| **`extract-google_devices-shiba.sh`** | 解壓 vendor blob 的腳本。EULA 需**兩次輸入**（Enter 翻頁 + `I ACCEPT`），只送一次會靜默失敗 |
| **Cuttlefish** | Google 官方 Android 虛擬裝置，用 `launch_cvd` 啟動。目標如 `aosp_cf_x86_64_phone-userdebug` |
| **ACK (Android Common Kernel)** | Android 共用 kernel 樹 |
| **GKI (Generic Kernel Image)** | 通用 kernel image。GKI 2.0 原則：Core kernel 不能改，驅動必須模組化到 `vendor_dlkm` |
| **VNDK** | Vendor Native Development Kit，vendor 可用的原生介面集合 |
| **VINTF** | Vendor Interface，透過 manifest 與 compatibility matrix 檢查 framework/vendor 相容性 |
| **HIDL / AIDL** | HAL 介面定義語言（AIDL 為現代作法） |

---

## 四、開機流程（Boot Flow）

### 各階段

| 名詞 | 說明 |
|---|---|
| **Boot ROM / PBL (Primary Bootloader)** | 晶片內建唯讀程式碼，< 16 KB，SoC 廠商燒錄不可改。初始化時脈/DRAM controller、Secure Boot 第一步 |
| **SBL (Secondary Bootloader)** | 第二階段 bootloader，如 Little Kernel |
| **EDL (Emergency Download Mode)** | PBL 驗證失敗時進入的緊急下載模式 |
| **LK (Little Kernel)** | 嵌入式微核心。高通 fork 自 `littlekernel/lk` 作為 Android bootloader（**Aboot**） |
| **Aboot** | 高通基於 LK 的 Android bootloader |
| **ABL** | Android Boot Loader，UEFI-based，現代高通平台使用 |
| **U-Boot** | 開源 bootloader，多用於 AOSP 開發板 |
| **Init (PID 1)** | userspace 第一個程式，原始碼在 `system/core/init/`。掛載 tmpfs/proc/sysfs、設定 SELinux、解析 `.rc` |
| **`init.rc` / Android Init Language** | 描述服務與啟動動作的腳本語言。另有 `init.{hardware}.rc`、`init.qcom.rc` 等 |
| **hwservicemanager / vndservicemanager** | HAL 服務註冊管理程序 |
| **Zygote** | 所有 App 程序的父程序，透過 `app_process` 啟動 `ZygoteInit.java`。預載 ~1500+ Java classes 與 resources，listen `/dev/socket/zygote` |
| **Copy-on-Write (COW)** | Zygote fork 後父子程序共享記憶體頁，是 App 快速啟動的關鍵 |
| **zygote64 / zygote32** | 64-bit 與 32-bit App 各自的 Zygote（Pixel 7a 等純 64-bit 環境已無 zygote32） |
| **System Server** | Zygote fork 出的 Framework 核心程序，啟動所有系統服務 |
| **Launcher** | 桌面 App，由 AMS 的 `startHomeActivity()` 啟動 |
| **`ACTION_BOOT_COMPLETED`** | System Server 啟動完成後發出的廣播 |
| **dexopt** | 首次開機時的 App 預先編譯，需 5~10 分鐘才進 launcher |

### System Server 關鍵服務

| 服務 | 功能 |
|---|---|
| **ActivityManagerService (AMS)** | 管理 Activity 生命週期、App 程序 |
| **PackageManagerService (PMS)** | 管理 APK 安裝、權限 |
| **WindowManagerService (WMS)** | 視窗管理、Surface 合成 |
| **PowerManagerService** | 電源管理、Wakelock |
| **InputManagerService** | 觸控、按鍵事件分發 |
| **TelephonyRegistry** | 電話狀態管理 |
| **ConnectivityService** | 網路管理 |

---

## 五、ARM 安全架構

| 名詞 | 說明 |
|---|---|
| **Exception Level (EL)** | ARMv8+ CPU 權限分層：**EL0**=App、**EL1**=OS kernel、**EL2**=Hypervisor、**EL3**=Secure Monitor |
| **TrustZone** | ARM 硬體級安全隔離，把系統切成 Secure World 與 Normal World。**是一種硬體層的 TEE 實作** |
| **Secure World / Normal World** | TrustZone 的兩個世界。Secure World 有自己的 EL0~EL3 |
| **Secure Monitor** | 執行在 EL3，負責世界切換（SMC handler） |
| **SMC (Secure Monitor Call)** | 觸發世界切換的指令 |
| **TZASC** | TrustZone Address Space Controller，記憶體區域隔離控制器 |
| **TEE (Trusted Execution Environment)** | 可信執行環境 |
| **OP-TEE** | 開源 TEE 實作，由 Linaro 維護，跑在 Secure World（BL3-2 / Secure EL1） |
| **TA (Trusted Application)** | 跑在 OP-TEE 上的可信應用（`.ta`） |
| **libteec** | Normal World 的 TEE Client API |
| **Root of Trust (ROT)** | 啟動過程中最早被信任的元件，通常是 SoC 內建 BootROM |
| **ATF / TF-A (ARM Trusted Firmware)** | ARM 官方 Secure World 執行環境實作。ARMv8 (2013-14) 首版，2015 成標準 |
| **PSCI** | Power State Coordination Interface，TF-A 元件之一 |
| **SMC Dispatcher / SiP service** | TF-A 元件 |
| **CCA (Confidential Compute Architecture)** | ARMv9 (2021) 引入，加入第三個 **Realm World**，對應 Intel TDX / AMD SEV |
| **Confidential Computing** | 讓資料「使用中 (in use)」仍受保護的理念，比 TrustZone 更廣（含 SGX、SEV、CCA） |

### Boot Loader 階段對照

| 階段 | 常見名稱 | 任務 | 層級 |
|---|---|---|---|
| **BL1** | ROM Code / BootROM | 硬體初始化、載入下一階 | EL3 |
| **BL2** | Trusted Boot Loader | 設定安全屬性、載入 U-Boot/TF-A | EL3 |
| **BL31** | ARM Trusted Firmware (ATF) | 實作 Secure Monitor | EL3 |
| **BL32** | OP-TEE OS | Secure World 的 OS | Secure EL1 |
| **BL33** | U-Boot / Linux Kernel | Normal World 的 OS | Non-secure EL1 |

順序：ROM → ATF (EL3) → OP-TEE (Secure EL1) → U-Boot (Non-secure EL1) → Linux

---

## 六、Kernel 元件

| 名詞 | 說明 |
|---|---|
| **Binder** | Android IPC（程序間通訊）機制，高效能 driver |
| **Ashmem** | Android 共享記憶體機制（現代版本改用 **memfd**） |
| **ION** | 多媒體記憶體分配器 |
| **Wakelock** | 電源管理機制，防止系統進入休眠 |
| **MMU** | 記憶體管理單元 |
| **dm-verity** | device-mapper 層的完整性驗證 |
| **MTE (Memory Tagging Extension)** | Pixel 8 起支援的硬體記憶體標記，用於精準抓 Buffer Overflow / Use-after-free，比軟體模擬的 **KASAN** 快且準 |

---

## 七、Partition 與 Image

### A/B 與動態分區

| 名詞 | 說明 |
|---|---|
| **A/B Slot (Seamless Update)** | Android 7.0+ 機制。兩份 partition（`_a`/`_b`），OTA 寫入備用 slot 成功後切換，失敗自動 rollback |
| **dynamic partition** | 動態分區，`system`/`vendor`/`product` 等都放在 `super` 內可彈性調整大小 |
| **super** | 容納各動態分區的實體分區 |
| **liblp** | 管理 super 內邏輯分區的函式庫（log 會出現 `[liblp] Partition system_a will resize...`） |
| **sparse image** | 稀疏格式 image，fastboot 會切分批傳送（`Sending sparse 'super' 1/9`） |

### 各 image 用途與來源

| Image | 內容 | 來源 |
|---|---|---|
| `boot.img` | Kernel + generic ramdisk | AOSP build |
| `init_boot.img` | Generic init ramdisk（Android 13+） | AOSP build |
| `vendor_boot.img` | Vendor ramdisk + DTB | AOSP build |
| `vendor_kernel_boot.img` | Vendor kernel modules | AOSP build |
| `dtbo.img` | Device Tree Blob Overlay | AOSP build |
| `pvmfw.img` | Protected VM firmware | AOSP build |
| `vbmeta.img` / `vbmeta_system.img` / `vbmeta_vendor.img` | AVB metadata | AOSP build |
| `system.img` / `system_ext.img` / `product.img` / `system_dlkm.img` | Framework 層 | AOSP build |
| `system_other.img` | — | AOSP build |
| `vendor.img` / `vendor_dlkm.img` | vendor 分區與 kernel modules | **Google vendor blob** |
| `bootloader.img` | 原廠 bootloader | **Google 原廠 binary（`m` 不會 build）** |
| `radio.img` | modem / baseband firmware | **Google 原廠 binary（`m` 不會 build）** |
| `userdata` / `metadata` | 使用者資料與 metadata | 首次開機時由 Android 自行 format |

### Verified Boot

| 名詞 | 說明 |
|---|---|
| **AVB (Android Verified Boot)** | 開機時驗證各 partition 簽章 |
| **vbmeta** | AVB metadata，檔案開頭 magic 為 `AVB0` |
| **`Failed to find AVB_MAGIC at offset: 0`** | 對 `fastboot flashall` 加 `--disable-verity --disable-verification` 導致的錯誤。fastboot 試圖 patch 不存在的 `vbmeta_vendor_kernel_boot`。**userdebug build 的 `vbmeta.img` 已含正確 flags，不需要 patch** |
| **`FLAGS_HASHTREE_DISABLED` / `FLAGS_VERIFICATION_DISABLED`** | `--disable-verity` / `--disable-verification` 寫入 vbmeta header 的 flag |

---

## 八、工具指令

### adb（Android Debug Bridge）

| 指令 | 用途 |
|---|---|
| `adb devices` | 列出已連線裝置（`unauthorized` 代表手機端未授權） |
| `adb shell` | 進入裝置 shell |
| `adb logcat` | 檢視系統 log；`-s MyTag` 只看指定 tag；`-b all` 看所有 buffer |
| `adb push` / `adb pull` | 傳檔 |
| `adb install` / `adb uninstall` | 安裝／移除 APK |
| `adb shell pm list packages` | 列出套件 |
| `adb reboot bootloader` / `recovery` | 重開進 bootloader / recovery |
| `adb root` / `adb remount` | 需 userdebug/eng build |
| `adb -s <serial>` | 多裝置時指定目標 |
| `adb tcpip 5555` + `adb connect <ip>:5555` | 無線除錯 |
| `adb shell dumpsys gfxinfo` | 效能分析（FPS、Jank） |
| `adb shell dmesg` | 查 kernel log |
| `adb shell cat /proc/last_kmsg` | 查上次開機 log（部分裝置） |
| **ADB_VENDOR_KEYS / `~/.android/adbkey`** | adb 授權金鑰，刪除後手機會重新跳出授權對話框 |

### fastboot

| 指令 | 用途 |
|---|---|
| `fastboot devices` | 列出 fastboot 模式裝置 |
| `fastboot getvar product` / `unlocked` | 查裝置型號 / 解鎖狀態 |
| `fastboot flashing unlock` | 解鎖 bootloader（**會清除 userdata**） |
| `fastboot flashall -w` | 燒錄全部 image，`-w` 清 userdata |
| `fastboot flash <partition> <img>` | 燒單一分區 |
| `ANDROID_PRODUCT_OUT=$(pwd)` | 指定 image 目錄（跨機器 flash 用） |
| `flash-all.sh` | Factory image 內附的救磚腳本 |
| **強制進 fastboot** | 按住 **電源 + 音量下鍵** |

### 其他

| 名詞 | 說明 |
|---|---|
| **platform-tools** | adb / fastboot 所在的 SDK 套件。macOS：`brew install android-platform-tools`；Ubuntu：`apt install android-tools-adb android-tools-fastboot` |
| **Android Flash Tool** | 網頁版刷機工具 flash.android.com，可刷 factory image / OTA / Beta，能降版 |
| **Factory Image** | developers.google.com/android/images，救磚用 |
| **USB debugging / OEM unlocking** | 開發人員選項中的兩個開關（設定 → 關於手機 → 連點版本號 7 下） |

---

## 九、Root

| 名詞 | 說明 |
|---|---|
| **`adbd cannot run as root in production builds`** | 正式 build 無法直接 `adb root`，需透過 Root 工具 |
| **Magisk** | 運作在 **User-space**，透過 patch **`init_boot.img`** 裡的 Ramdisk 取得權限。社群支援廣 |
| **KernelSU** | 運作在 **Kernel-space**，修改／替換 **`boot.img`**（含 kernel 本身）。適合 kernel 開發者 |
| **magisk_patched-*.img** | Magisk App patch 後產出的 image，用 `fastboot flash init_boot` 刷入 |

---

## 十、SELinux / SEPolicy

> 深入說明見 [SELinux 是什麼？為什麼 Android 韌體工程師必須懂它](../selinux.md)；規則語法速查見 [Android SEPolicy](../android_sepolicy.md)。

### 基本概念

| 名詞 | 說明 |
|---|---|
| **SELinux** | 強制存取控制（**MAC**），對每個 process 與資源標 security context。Android 4.3 引入、5.0 起全面 enforcing |
| **MAC vs DAC** | DAC（傳統 rwx、uid/gid）權限跟著 user 走、擁有者可自行決定；MAC 權限跟著 policy 定義的 domain 走。**即使是 root，沒有 policy 允許一律拒絕** |
| **Security context / label** | `user:role:type:level` 格式，如 `u:r:untrusted_app:s0`。權限判斷主要看 type |
| **Type Enforcement (TE)** | 以 type 為基礎的權限判斷機制 |
| **Enforcing / Permissive** | Enforcing 違規直接擋下並記 log（量產必須）；Permissive 只記 log 不阻擋（debug 用）。用 `getenforce` / `setenforce` 切換（userdebug build） |

### 元件

| 名詞 | 說明 |
|---|---|
| **LSM hooks** | kernel 在安全敏感操作點（open、exec、bind…）埋的掛鉤，SELinux 透過 LSM framework 接入 |
| **Security Server** | kernel 內做存取決策的核心 |
| **AVC (Access Vector Cache)** | 快取決策結果；denial log 開頭的 `avc:` 就是它印的 |
| **selinuxfs** | `/sys/fs/selinux`，與 userspace 溝通的介面 |
| **libselinux** | 查詢／設定 context 的 library |
| **`ls -Z` / `ps -Z`** | 查看檔案／process 的 label |
| **`restorecon` / `chcon`** | 重設／變更檔案 label |

### Policy 檔案

| 名詞 | 說明 |
|---|---|
| **`.te` 檔** | type enforcement 規則（`allow` / `neverallow` / `dontaudit` 等） |
| **`allow`** | `allow <source_type> <target_type>:<class> <permissions>;` |
| **`neverallow`** | 編譯期檢查的禁止規則，違反會導致 build 失敗。**vendor 不能違反 platform 的 neverallow，CTS 會抓** |
| **`dontaudit`** | 不記錄該 denial（消音），不影響實際權限 |
| **`file_contexts`** | 檔案路徑對應的 label |
| **`property_contexts`** | Android property 的 label |
| **`service_contexts`** | binder service 的 label |
| **`seapp_contexts`** | app 該跑在哪個 domain |
| **`genfs_contexts`** | sysfs / procfs 等虛擬檔案系統的 label |
| **CIL** | Common Intermediate Language，Android 各層 policy 開機時合併編譯的中間格式 |
| **`precompiled_sepolicy`** | 預先編譯好的 policy，開機時直接使用可省下合併時間 |

### sepolicy 分層（Treble 之後）

| 層 | 位置 | Owner |
|---|---|---|
| **Platform** | `system/sepolicy` | Google / AOSP，基本不能改 |
| **Platform-vendor 介面** | `system/sepolicy/vendor` | Google 定義 |
| **Vendor** | `device/<soc>/.../sepolicy`、`vendor/...` | SoC vendor |
| **ODM / OEM** | `odm/sepolicy` | OEM |

### Denial 判讀與 triage

| 名詞 | 說明 |
|---|---|
| **AVC denied** | 權限被拒的 audit log，出現在 `dmesg` / `logcat` |
| **scontext / tcontext / tclass** | AVC log 中的來源 context / 目標 context / class，用來反推需補的 `allow` |
| **`permissive=1`** | log 中帶此標記代表該 domain 是 permissive，denial 只記錄不阻擋，可先降優先級（但量產前必須清掉） |
| **`audit2allow`** | 由 AVC log 產生候選 allow 規則的工具。**只是建議不能無腦採用**——每條 allow 都是在攻擊面開洞 |
| **Ownership 判斷原則** | 依據不是「誰的 process」，而是**這條規則該定義在哪一層**：查 domain `.te` 定義位置 → 查 label 由哪層 `*_contexts` 打 → `git blame` → 看 vendor prefix（如 `mtk_*`） |

---

## 十一、測試與效能

| 名詞 | 說明 |
|---|---|
| **CTS** | Compatibility Test Suite |
| **VTS** | Vendor Test Suite（測 HAL） |
| **GTS** | Google Test Suite（App 相容性） |
| **STS** | Security Test Suite |
| **Jank** | 卡頓，與 FPS 一起用來衡量流暢度 |
| **Performance per Watt** | 能效比，對標 iPhone 時的關鍵指標 |
| **ART (Android Runtime)** | 取代 Dalvik 的執行環境，支援 AOT 編譯 |
| **HAL (Hardware Abstraction Layer)** | 硬體抽象層，屏蔽廠商差異 |

### Codec / 播放器

| 名詞 | 說明 |
|---|---|
| **MediaCodec** | Android 底層 codec API |
| **ExoPlayer / `[exo2]`** | Google 自家進階播放器，自管 buffer/demux/render scheduling |
| **`[plat]`** | Platform decoder，直接走 Android 原生 MediaPlayer/MediaCodec，不經 ExoPlayer |
| **`[mse]`** | Web 上的 Media Source Extensions |
| **`c2.{vendor}.xxx`** vs **`c2.google/android`** | 前者為硬解，後者為軟解（`dumpsys media.codec` 判讀） |
| **VP9 Profile 0 / Profile 2** | Profile 2 為 HDR，Tensor 上不支援硬解會 fallback 軟解 |
| **libvpx** | Chromium 內建的 VP9 軟解實作 |
| **smpte2084 (PQ) / bt2020** | HDR10 的傳輸函數與色域 |
| **ABR (Adaptive Bitrate) ladder** | YouTube 後端依 client 能力給的串流階梯 |
| **sCPN** | Session Client Playback Nonce |
| **tone mapping** | HDR → SDR 顯示轉換，CPU 做會週期性掉幀 |

---

## 十二、常見錯誤訊息

| 訊息 | 意義 |
|---|---|
| `Invalid lunch combo: aosp_shiba-userdebug` | Android 14+ 需三段式：`aosp_shiba-bp1a-userdebug` |
| `fastboot: error: could not read android-info.txt` | 跨機器打包時漏了 `android-info.txt`（不在 `*.img` glob 內） |
| `fastboot: error: Failed to find AVB_MAGIC at offset: 0` | 不該加 `--disable-verity --disable-verification` |
| `image (bl1_a): rejected, anti-rollback` | 刷的 bootloader 比手機目前舊 |
| `Bootloader is locked` | 需先 `fastboot flashing unlock` |
| `Device version-bootloader is 'X'. Update requires 'Y'.` | Factory image 的 bootloader 版本要求不符 |
| `adbd cannot run as root in production builds` | 正式 build 無法 `adb root` |
| **flash 完開機循環** | 通常是 vendor blob 缺失，檢查 `vendor/google_devices/shiba/proprietary/device-vendor.mk` 是否存在 |

### 看起來像錯誤但正常的訊息

| 訊息 | 為什麼正常 |
|---|---|
| `Erase successful, but not automatically formatting. File system type raw not supported.` | Android 首次 boot 會自動 format `/data` |
| `wipe task partition not found: cache` | Pixel 8 採 A/B + dynamic partition，沒有獨立 cache 分區 |
| `Setting current slot to 'b'` | A/B slot rotation，每次 flash 交替 |
| `Invalid sparse file format at header magic` | sparse image 分批傳送的正常現象 |
| `archive does not contain 'recovery.img'` | Pixel 8 無獨立 recovery 分區 |
