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
| **build variant** | `user`（正式）/ `userdebug`（可 adb root，效能測試用）/ `eng`（build 最快）。三者差異詳見 [搞懂三種 Build Variant](../android-build-variants.md) |
| **`ro.secure`** | 決定 adbd 是否以受限身分執行：`eng` 為 0（開機即 root），`userdebug`／`user` 為 1 |
| **`ro.debuggable`** | 決定系統是否可被除錯（`adb root` 提權、`jdwp` 附加、部分 log 行為）：`eng`／`userdebug` 為 1，`user` 為 0 |
| **dexpreopt** | 建置時預先 AOT 編譯 dex；`eng` 關閉（改 code 快但執行慢）、`userdebug`／`user` 啟用 |
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

### App 端（Gradle）

> 注意：AOSP 平台建置與 App 建置是兩套系統，「build variant」在兩邊意思不同。以下出自 [Android Product Flavor 完整教學](../android-product-flavor-完整教學.md)。

| 名詞 | 說明 |
|---|---|
| **build type（建置類型）** | Gradle 的「怎麼建」：`debug`／`release`，管簽章、`minifyEnabled`、可除錯與否 |
| **product flavor（產品風味）** | Gradle 的「建給誰」：免費／付費、白牌客戶 A／B、dev／staging／prod，共用同一份程式碼庫 |
| **build variant（建置變體，Gradle）** | build type × product flavor 的組合，如 `freeDebug`／`paidRelease`；與 AOSP 的 `user`/`userdebug`/`eng` 無關 |
| **flavor dimension** | flavor 的分類軸；多維度時各軸各取一個 flavor 再組合（如 `version × environment`） |
| **source set** | `src/free/`、`src/paid/` 等目錄，同名資源／程式碼會覆寫 `src/main/`，是 flavor 客製的主要機制 |
| **`applicationId` / `applicationIdSuffix`** | App 的唯一識別碼；不同 flavor 給不同 id 才能同機並存安裝 |
| **`BuildConfig`** | Gradle 產生的常數類別（需開 `buildFeatures { buildConfig = true }`），用 `buildConfigField` 把 flavor 差異帶進程式碼 |
| **manifest placeholder** | 用 `manifestPlaceholders` 把值注入 `AndroidManifest.xml`（如各 flavor 不同的 App 名稱、API key） |

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

> 深入說明見 [ARM Trusted Firmware (TF-A) 解析](../ARM_Trusted_Firmware_解析.md)（誰在跑）與 [Secure Boot 解析](../Secure_Boot_解析.md)（憑什麼信任它）；速查見 [ATF](../atf.md) 與 [ARM Trusted Firmware 元件](../arm_trust_firmware.md)。

| 名詞 | 說明 |
|---|---|
| **Exception Level (EL)** | ARMv8+ CPU 權限分層：**EL0**=App、**EL1**=OS kernel、**EL2**=Hypervisor、**EL3**=Secure Monitor |
| **TrustZone** | ARM 硬體級安全隔離，把系統切成 Secure World 與 Normal World。**是一種硬體層的 TEE 實作** |
| **Secure World / Normal World** | TrustZone 的兩個世界。Secure World 有自己的 EL0~EL3 |
| **NS bit** | AXI bus 上每筆 transaction 都帶的 Non-secure 標記。Secure RAM／secure peripheral（指紋 sensor SPI、crypto engine）在**硬體層**就拒絕 NS=1 的存取——TrustZone 的隔離不只是軟體概念 |
| **Secure Monitor** | 執行在 EL3，負責世界切換（SMC handler）。EL3 是**唯一**能在兩個世界間切換的地方 |
| **SMC (Secure Monitor Call)** | 觸發世界切換的指令。執行後 trap 進 EL3，由 Monitor 保存 context、翻轉 `SCR_EL3.NS`、跳進另一個世界 |
| **`SCR_EL3.NS`** | Secure Configuration Register 的 NS bit，world switch 時由 BL31 翻轉 |
| **TZASC / TZC-400** | TrustZone Address Space Controller，記憶體防火牆。由 TF-A 開機早期設定；**設錯一個 region，Normal World 就能直接讀到金鑰** |
| **TEE (Trusted Execution Environment)** | 可信執行環境 |
| **OP-TEE** | 開源 TEE 實作，由 Linaro 維護，跑在 Secure World（BL32 / Secure EL1） |
| **TA (Trusted Application)** | 跑在 Trusted OS 上的可信應用（`.ta`）。Android 上的 KeyMint/Keymaster、Gatekeeper、Widevine L1 DRM 本體都是 TA |
| **QTEE / Kinibi / TEEGRIS** | 量產手機常見的閉源 Trusted OS：高通 QTEE、Trustonic Kinibi、三星 TEEGRIS。開源代表則是 OP-TEE |
| **libteec** | Normal World 的 TEE Client API |
| **Root of Trust (ROT)** | 啟動過程中最早被信任的元件，通常是 SoC 內建 BootROM。ROM 不可修改，是整條信任鏈的錨點 |
| **ATF / TF-A (ARM Trusted Firmware)** | ARM 官方 Secure World 執行環境實作，正式名稱為 **Trusted Firmware-A**，BSD-3-Clause 開源，由 Linaro 主導的 trustedfirmware.org 維護。ARMv8 (2013-14) 首版，2015 成標準。是 TBBR/PSCI/SMCCC 等 ARM 規格的**參考實作**——各家量產韌體不是基於它，就是實作了相同介面 |
| **TBBR** | Trusted Board Boot Requirements (Arm DEN0006)。定義 X.509 憑證鏈設計：每個 image 附 content certificate 與 key certificate，一路鏈回 ROTPK |
| **key certificate / content certificate** | TBBR 中每個 image 配的兩張憑證：key cert 說「這 image 該用哪把公鑰驗」，content cert 說「這 image 的正確雜湊值」。**分層是為了金鑰隔離**——SoC 廠簽 BL2/BL31、手機廠簽 BL33，某層金鑰洩漏不必動到 ROTPK |
| **FIP (Firmware Image Package)** | TF-A 把各 image 與憑證打包的格式。用 `fiptool` 操作、`cert_create` 產憑證鏈 |
| **Secure Boot enable bit** | eFuse 裡的開關。未燒之前晶片什麼都肯跑（方便開發），燒下去後**不可逆**地強制驗證 |
| **HSM** | 硬體安全模組，簽署伺服器用來持有私鑰。原則是「產出即簽章，人手不碰私鑰」 |
| **glitching (fault injection)** | 在 ROM 執行「驗證是否通過」的分支瞬間，對電源／時脈打毛刺讓 CPU 跳錯分支。對策：冗餘比對、隨機延遲、把「驗證通過」編碼成非平凡常數而非 0/1 |
| **TOCTOU** | Time-of-check to time-of-use。驗完雜湊後、跳轉執行前，image 若還在攻擊者可寫的記憶體就可能被掉包。原則：**先搬進受保護記憶體，再驗證，再執行** |
| **kamakiri / mtkclient** | 聯發科 BROM 漏洞與其利用工具，與高通 EDL 同類：驗證邏輯還沒跑到，攻擊者已借下載模式取得執行權 |
| **PSCI** | Power State Coordination Interface (Arm DEN0022)。kernel 的 CPU hotplug、suspend-to-RAM、reboot 最後都是一個 SMC（`CPU_SUSPEND`、`SYSTEM_OFF`）進 BL31，由 platform code 操作電源控制器。device tree 的 `enable-method = "psci"` 就是它 |
| **SMCCC** | SMC Calling Convention (Arm DEN0028)。定義 SMC function ID 的配置，含保留給廠商的 vendor 區段 |
| **ROTPK** | Root of Trust Public Key。其 hash 燒在 eFuse 裡，BL1 用它驗證 BL2 簽章 |
| **eFuse / anti-rollback counter** | 一次性燒錄的硬體熔絲，存放 ROTPK hash 與版本計數，防止刷回舊版有漏洞的韌體 |
| **AP (Application Processor)** | 跑 Android/Linux 的主 CPU（Cortex-A），用來與 SoC 上其他處理器區分 |
| **SCP (System Control Processor)** | 管電源時序的獨立處理器，通常是顆 Cortex-M。實務上很多 SoC 在 AP 上電前還有 PMIC/SCP 的 boot 流程 |
| **SDEI** | Secure Delivery of Events Interface，BL31 提供的 runtime service 之一 |
| **SMC Dispatcher / SiP service** | TF-A 元件。SiP (Silicon Provider) service 用 SMCCC 保留的 vendor function ID 區段實作廠商自訂功能 |
| **`SMCCC_ARCH_WORKAROUND_*`** | BL31 提供的 Spectre/Meltdown 類漏洞 workaround 介面 |
| **platform port** | TF-A 移植層（`plat/<vendor>/` 目錄）。新晶片 bring-up 第一步，需實作 `plat_get_my_entrypoint`、console driver、DDR 初始化、`plat_psci_ops`（每個 power domain 怎麼開關） |
| **CCA (Confidential Compute Architecture)** | ARMv9 (2021) 引入，加入第三個 **Realm World**，對應 Intel TDX / AMD SEV |
| **Confidential Computing** | 讓資料「使用中 (in use)」仍受保護的理念，比 TrustZone 更廣（含 SGX、SEV、CCA） |
| **checkm8** | Apple BootROM 漏洞。經典案例：ROM 層的 bug 無法透過 OTA 修補、影響終生 |

### Boot Loader 階段對照

| 階段 | 常見名稱 | 任務 | 層級 |
|---|---|---|---|
| **BL1** | AP Trusted ROM / BootROM | 燒在晶片裡不可改。初始化少量 SRAM、從 boot media 載入 BL2，用 eFuse 裡的 ROTPK hash 驗證其簽章 | EL3 |
| **BL2** | Trusted Boot Firmware | 在 SRAM 執行。初始化 DDR、載入並驗證 BL31/BL32/BL33 與各家專屬韌體（DDR training、modem image） | EL3 |
| **BL31** | EL3 Runtime Firmware (ATF) | **開機後常駐**於 secure memory。Secure Monitor（world switch）、PSCI、GIC 中斷路由、SDEI/SiP 等 runtime service | EL3 |
| **BL32** | Trusted OS | Secure World 的 OS，提供 TA 執行環境。OP-TEE / QTEE / Kinibi / TEEGRIS | Secure EL1 |
| **BL33** | Non-secure Firmware | 一般講的 bootloader：高通 ABL、聯發科 LK、開發板 U-Boot。負責 fastboot、A/B slot 選擇、載入 `boot.img`、執行 AVB | EL2 / Non-secure EL1 |

順序：BL1 → BL2 → BL31 (EL3，常駐) → BL32 (Secure EL1) → BL33 (Non-secure) → Linux kernel → Android

**信任鏈的銜接**：BL1→BL2→BL33 由 **TBBR 憑證鏈**保證，BL33→kernel 由 **AVB** 保證。兩段合起來才是完整的 Verified Boot。

### 各家 SoC 的階段命名對照

| TF-A | 高通 | 聯發科 |
|---|---|---|
| BL1 | PBL | BootROM |
| BL2 | XBL / SBL | Preloader |
| BL31 | TZ | ATF |
| BL32 | TZ（QTEE） | — |
| BL33 | ABL | LK |

名字不同，角色對應得上。

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

> 深入說明見 [Secure Boot 解析](../Secure_Boot_解析.md)。TBBR 鏈驗到 BL33（bootloader）就結束，kernel 之後由 AVB 接手。

| 名詞 | 說明 |
|---|---|
| **AVB (Android Verified Boot)** | 開機時驗證各 partition 簽章。2.0 版以 vbmeta 為中樞 |
| **vbmeta** | AVB metadata，檔案開頭 magic 為 `AVB0`。存各 partition 的雜湊或 hashtree descriptor，本身由 OEM 金鑰簽署、由 bootloader 內建的公鑰驗證 |
| **hashtree descriptor** | 大 partition（system、vendor）用的 Merkle tree，執行期由 **dm-verity** 逐 block 驗證，避免開機時算整個 partition 的雜湊。小 partition（boot、dtbo）則用整體 hash |
| **rollback index** | vbmeta 裡的版本號。裝置把見過的最大版本記在防竄改儲存（**RPMB** 或 eFuse）。刷回舊版簽章仍有效但版本號過不了，擋掉「降級到有漏洞舊版再攻擊」 |
| **RPMB** | Replay Protected Memory Block，eMMC/UFS 上的防重放區塊，用來存 rollback index 等狀態 |
| **boot state（四色）** | **green**=鏈完整；**yellow**=鎖著但用使用者自訂金鑰驗證；**orange**=bootloader 已解鎖、不驗證（開機警告畫面）；**red**=驗證失敗拒絕開機 |
| **解鎖為何清 userdata** | 解鎖後 TEE 拒絕釋出綁在 verified 狀態上的金鑰，資料本來就再也解不開（同時是 Widevine 從 L1 掉到 L3 的原因），清除只是誠實面對 |
| **`avbtool`** | AVB 工具。`add_hash_footer` 加簽章尾、`verify_image` 驗證，是理解 descriptor 結構最快的方式 |
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

### Log 與低階除錯

> 出自 [adb logcat 與 UART：Android 除錯的兩把刀](../adb-logcat-vs-uart.md)。

| 名詞 | 說明 |
|---|---|
| **logd / logcat buffer** | logcat 背後的 daemon 與環形緩衝區；buffer 分 `main`／`system`／`crash`／`events`／`radio`，用 `-b` 指定 |
| **log 等級** | `V`／`D`／`I`／`W`／`E`／`F`，另有 `S`(Silent)；`MyTag:E *:S` 表示只看該 tag 的 Error 以上、其餘靜音 |
| **UART / serial console** | 硬體序列埠 console，用 USB-to-TTL 接出，看得到 bootloader、`printk`、driver 初始化與 panic 死前訊息；是唯一橫跨開機全程的觀察窗口 |
| **`earlycon`** | kernel cmdline 參數，讓 console 在正式 serial driver 起來前就能輸出，追早期開機問題用 |
| **JTAG / SWD** | 比 UART 更底層的硬體除錯介面，可下中斷點、讀暫存器；Boot ROM 階段幾乎只剩它可用 |
| **ramdump / coredump** | panic 或死當時把記憶體傾印出來事後分析 |
| **tombstone** | native crash 留在 `/data/tombstones/` 的墓碑檔（含 backtrace） |
| **watchdog / 餵狗** | 計時器，系統需定期重置它，卡死沒餵到就強制重啟；分硬體／軟體 watchdog，framework 另有監控 `system_server` 的 Watchdog |
| **ANR（Application Not Responding）** | App 主執行緒卡住超過門檻的無回應狀態 |
| **bootloop** | 開機無限重啟；依卡住階段決定該看 UART 還是 logcat |

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

> 深入說明見 [SELinux 是什麼？為什麼 Android 韌體工程師必須懂它](../selinux.md)；規則語法速查見 [Android SEPolicy](../android_sepolicy.md)。App 如何靠讀取核心中生效的 policy 反推裝置已被 root，見第二十二節。

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

---

## 十三、車用（AAOS）

> 出自 [Android Automotive OS（AAOS）開發者入門](../AAOS-開發者入門.md)。

| 名詞 | 說明 |
|---|---|
| **Android Auto** | 手機投影協定，運算在手機上，車機只是外接螢幕——與 AAOS 是兩回事 |
| **AAOS（Android Automotive OS）** | 直接跑在車機硬體上的完整作業系統，AOSP 的一支，開源可由車廠客製 |
| **GAS（Google Automotive Services）** | Google 另外授權的服務包（Play 商店、Google 地圖、Assistant）；有無 GAS 是兩種 AAOS 車的分界 |
| **VHAL（Vehicle HAL）** | OS 與車輛硬體的邊界，把車速／電量／空調／車門／檔位抽象成帶存取權限與訂閱通知的 **property**，上層不必管 CAN bus 或哪家 ECU |
| **vehicle property** | VHAL 的基本單位；分 AOSP 標準 property（`VehiclePropertyIds`）與車廠自訂的 vendor property |
| **`android.car` / Car API** | App 端入口，透過 `Car` 取得各種 manager，最常用 `CarPropertyManager` 讀寫／訂閱 property |
| **`CarUxRestrictionsManager`** | 行車中的 UI 限制管理（限制文字量、互動複雜度等） |
| **`car-ui-lib`** | Car UI Library，車廠客製狀態列／通知／清單等系統外觀，維持一致互動邏輯 |
| **Car Audio Zones** | 分區音訊，讓車內不同區域播放不同來源 |
| **IVI（In-Vehicle Infotainment）** | 車載資訊娛樂系統，AAOS 所競爭的類別 |
| **SDV（Software-Defined Vehicle）** | 軟體定義車輛：車輛功能由軟體決定並可 OTA 演進，是 AAOS 的產業背景 |

---

## 十四、AVB 真機逆向（ABL）

> 出自 [把 ABL 拆開看：AVB 驗證在真機上到底怎麼跑](../abl-avb-reversing.md)。規格層的定義見第五、七節。

| 名詞 | 說明 |
|---|---|
| **ABL（Android Boot Loader）** | Qualcomm 開機鏈 PBL → XBL → **ABL** → kernel 裡的最後一棒，本身是建構在 edk2 上的 **UEFI application**。信任鏈裡第一個改用 AVB 驗 Android 分區的階段（前面用的是 Qualcomm 自家 ELF 簽章格式） |
| **`QcomModulePkg`** | Qualcomm 在 edk2 下的模組包，`VerifiedBoot.c`／`BootLinux.c` 等廠商包裝層住在這；逆向時 `avb_*` 開頭的才是 Google 的 libavb 本體 |
| **`libavb`** | Google 的 AVB 參考實作，純 C、幾乎無混淆且滿是描述性字串，是逆向時的黃金錨點 |
| **`AvbOps`** | libavb 與廠商實作的分界線——一張函式指標表，把「怎麼讀分區／讀 rollback／裝置有沒有解鎖／公鑰對不對」等平台細節交給廠商。**AVB 的實際強度取決於這裡有沒有偷工** |
| **`validate_vbmeta_public_key`** | `AvbOps` 回呼，決定「簽 vbmeta 的這把公鑰是不是我認可的 OEM 金鑰」。libavb 只驗「有被某把私鑰簽過」，這一刀由廠商補上 |
| **`read_rollback_index` / `write_rollback_index`** | `AvbOps` 回呼，接到 **RPMB** 才有防回滾效果；被 stub 成永遠回 0 是常見的安全弱化 |
| **`read_is_device_unlocked`** | `AvbOps` 回呼，回報 bootloader 鎖定狀態，決定驗證失敗要不要擋開機 |
| **`avb_slot_verify()`** | libavb 總入口，吃 `requested_partitions`（`boot`／`init_boot`／`vendor_boot`／`dtbo`）、`ab_suffix`（`_a`／`_b`）等參數 |
| **`AVB0`** | vbmeta header 開頭 4 bytes 的 magic（小端讀成 `0x30425641`），逆向時用來定位 header 解析點。**header 所有多位元組欄位都是 big-endian** |
| **CHAIN_PARTITION descriptor** | 把某分區的驗證「轉交」給它自己的 vbmeta + 指定公鑰，是 `vbmeta_system` 等多份 vbmeta 存在的原因；逆向時漏追會少掉半條驗證鏈 |
| **`AVB_SLOT_VERIFY_FLAGS_ALLOW_VERIFICATION_ERROR`** | 解鎖裝置會帶的旗標，讓「驗證失敗」不等於「停止開機」；看漏它會誤以為某台機器根本沒在驗 |
| **`androidboot.verifiedbootstate=`** | 驗證結果（`green`／`yellow`／`orange`／`red`）透過 kernel cmdline 傳給 Android，後續影響 KeyMaster attestation。搜這個字串的 xref 是定位整段 AVB 流程最快的路 |

---

## 十五、remount 與 OverlayFS

> 出自 [從 `mount -o remount` 到 OverlayFS](../android-remount-deep-dive.md)。

| 名詞 | 說明 |
|---|---|
| **remount** | VFS 層語意是「不卸載、不重建 mount point，只改既有 superblock 的 mount flags」。因為 `/system`／`/vendor` 永遠有開啟中的 fd，`umount` + `mount` 不可行，remount 是唯一路徑 |
| **EROFS** | Enhanced Read-Only File System，壓縮唯讀檔案系統，並在 block 層做去重（shared blocks）。**設計上就沒有寫入路徑**，`remount,rw` 對它不是被禁止而是語意不存在 |
| **right-sizing** | build 系統把每個 logical partition 縮到剛好裝得下內容，好把空間還給 `super` 的動態配置池；結果是唯讀分區幾乎沒有 free space |
| **overlayfs（Android 用法）** | `adb remount` 從 Android 10 起的實作：lower = 唯讀原分區、upper = 可寫 backing storage，疊起來掛在原掛載點。**你看到的是「出廠 image + 你的 diff」的合成視圖，不是出廠 image** |
| **`scratch`** | A/B 裝置上 fs_mgr 在 `super` 裡動態建立、掛在 `/mnt/scratch/overlay` 的 backing storage 邏輯分區。**是保留名稱**，BSP 不能拿去命名別的分區 |
| **copy-up** | overlayfs 的語意：改動一個檔案會把**整個檔案**複製到 upper layer。改一行的 40 MB `.so` 就佔掉 40 MB，是 scratch 爆掉的主因 |
| **`adb remount -R`** | 需要時自動關 verity 並重開機；已在 remount 狀態則不多此一舉重開 |
| **`adb enable-verity`** | 解除 overlay、還原到修改前狀態；也是清掉 scratch、排除「行為與檔案內容對不上」這個變因的手段 |
| **`override_creds`** | android-common 為 overlayfs 加的 mount option，用來調和 Android 嚴格的 SELinux least-privilege 模型與 overlayfs 預設行為；主線 kernel 自組的板子容易在這裡出問題 |

---

## 十六、虛擬化與隔離（AVF / Microdroid）

> 出自 [Microdroid：Android 為什麼要在手機裡再開一台 Android](../Microdroid.md)。

| 名詞 | 說明 |
|---|---|
| **AVF（Android Virtualization Framework）** | 整套虛擬化框架的統稱，不是某個程式 |
| **pKVM（protected KVM）** | 做隔離的 hypervisor 本體，跑在 **EL2**；把 Android 的 Linux kernel 留在 EL1 並**降權**，使 host kernel 不再是 guest 的 TCB 的一部分 |
| **pVM（protected VM）** | 被 pKVM 保護的 guest，是容器概念；裡面裝 Microdroid 或別的 OS 都可以 |
| **Microdroid** | 裝進 pVM 的**極簡 Android based guest OS**。有 Bionic／Verified Boot／SELinux／APEX／Binder RPC；**沒有** `android.*` Java API、SystemServer、Zygote、UI、HAL |
| **crosvm** | Rust 寫的 VMM，模擬 virtio 裝置、組裝 composite disk image |
| **VirtualizationService / `virtmgr`** | Android 主機側的管理服務，配 CID、生成磁碟、以引用計數管理 VM 生命週期（client 放掉 `IVirtualMachine` 就關 VM） |
| **記憶體捐贈（memory donation）** | 建 pVM 時 host 把頁面捐給 guest，hypervisor 轉移所有權並從 host 的 **stage 2** 頁表拿掉；host 拿著實體位址也解不開。要通訊得由 guest 主動 hypercall 分享回去 |
| **MMIO guard** | guest 對 MMIO 的存取被 trap 給 hypervisor，而非任意穿透 |
| **FF-A（Firmware Framework for Arm）** | pKVM proxy SMC 到 TrustZone 時用的框架，防 confused deputy——host 不能叫 TrustZone 去讀它自己讀不到的 buffer |
| **`pvmfw`（protected VM firmware）** | guest 裡執行的第一段程式，角色等同實體裝置的 Boot ROM：驗下一階段 bootloader，並用 `instance` 映像維持這台 VM 的身分一致性 |
| **`microdroid_manager`** | VM 內部的驗證決策者：解密 instance 映像、讀公鑰與 rollback counter、用 Binder RPC 與 host 的 VirtualizationService 通訊、從 APK config 讀出 main binary 並執行 |
| **`zipfuse`** | Microdroid 的 FUSE 檔案系統，把 client APK（本質是 Zip）**不解壓縮**直接掛成檔案系統——省資源，也讓逐塊驗證能一路帶到讀取那一刻 |
| **`instance` 分割區** | 加密分割區，持久保存 per-instance 的 verified boot 資料（公鑰、rollback counter）。撐起「這台 VM 是同一台」這個概念 |
| **sealing key** | 從開機鏈量測值推導出的**穩定**封存金鑰。程式碼改了 → 量測值變了 → 金鑰變了 → 舊資料自動解不開，不需要額外的防竄改檢查 |
| **attestation key** | 簽章用，向外證明「我是誰、我跑的是什麼」 |
| **vsock** | pVM 唯一的通訊管道（沒有網路概念），用 32-bit **CID** 定位，類比 IP 位址 |
| **Binder RPC** | 把 Binder 從 kernel driver 上的 IPC 擴展成 socket 上的 RPC（client 用 `RpcSession`、server 用 `RpcServer`），使同一套 AIDL 介面可以跨 VM 邊界 |
| **AuthFS** | 跨 pVM 邊界、雙方互不信任時的檔案交換；在**每一次存取操作**做透明完整性檢查（類比 `fs-verity`），才擋得住 TOCTOU |
| **debug level（FULL / NONE）** | FULL 開放 adb／logcat／tombstone／gdb，NONE 全關。**差別是安全等級不是方便程度**——debuggable 的 pVM 等於把 guest 攤開給 host 看，production 應用 NONE |

---

## 十七、協同處理器攻擊面（GXP 案例）

> 出自 [Pixel 8 GXP DSP 漏洞與 MTE 繞過](../pixel8-gxp-dsp.md)。

| 名詞 | 說明 |
|---|---|
| **GXP（Google eXtended Processing）** | Google 自研的影像處理 DSP，2022 年隨 Pixel 7 引入；零公開文件、零 toolchain，Google Camera 等系統 App 依賴它 |
| **攻擊面分層** | Universal（unix socket／binder／pipe）→ Chipset-specific（Mali／Qualcomm GPU/DSP）→ Vendor-specific（Samsung NPU／KNOX）→ Model/Module-specific。**越往下防護越薄、影響範圍也越窄** |
| **DMA direction 信任錯誤** | `gxp_mapping_create()` 正確地從 VMA 取得 CPU 端屬性，卻直接採用 user 傳入的 `mapping_dir` 去設 DSP MMU，兩者未比對。傳 `DMA_BIDIRECTIONAL` 即可讓 DSP 認為唯讀頁面可寫 |
| **write read-only memory primitive** | CPU 端視為唯讀的實體頁面可透過 DSP 任意寫入。**MTE 對此完全無感**——它保護的是 CPU 端存取的合法性，不涉及 DMA 路徑 |
| **Replay attack（研究方法）** | 不硬啃閉源 firmware，改用「SELinux policy 找出誰在正常使用這個 device → Frida 錄下 production App 的實際 call flow → 把真實行為當非官方 SDK 重放」 |
| **Library hijacking + PID 遍歷** | 覆寫 camera provider 的 library 後，利用「開機早期 daemon 的 PID 落在小而穩定的範圍」逐一 kill，靠 init 自動拉起以觸發重載 |

---

## 十八、Chip Vendor BSP 與交付

> 出自 [Chip Vendor 視角系列](android_index.md) 01／03／16。既有的 Soong／`Android.bp`／VNDK／Treble／VINTF 定義見第三節。

| 名詞 | 說明 |
|---|---|
| **BSP（Board Support Package）** | Chip vendor 交付給 OEM/ODM 的整包東西：device tree、kernel、HAL、prebuilt blob、工具鏈。「維護一份 BSP 讓客戶能 build 出整台裝置的所有 image」就是 chip vendor 的工作定義 |
| **manifest server** | Chip vendor 自建的 manifest 服務，把 AOSP 上游、自家 SoC BSP、客戶專案三種來源組成一份可 `repo sync` 的 XML |
| **local manifest** | `.repo/local_manifests/` 底下的補充 XML，用來在不改主 manifest 的前提下增刪 project——客戶專案客製的常見手法 |
| **product 層 vs board 層** | 兩條互相獨立的設定軸線：product（`AndroidProducts.mk`／`device-vendor.mk`，決定「裝什麼軟體」）與 board（`BoardConfig.mk`，決定「硬體長什麼樣」）。分不清這兩條是新手改錯地方的主因 |
| **繼承鏈（product inheritance）** | SoC 公版 → 客戶專案層層 `$(call inherit-product,...)`；愈上層愈通用，客戶只覆寫差異部分 |
| **image variant** | 同一份原始碼因 `vendor: true` / `product: true` 等屬性被編成多份 variant，各自連結不同的 library 集合。這是 Treble 在 build 層的落實 |
| **`vendor: true`** | 把 module 標為 vendor variant，直接決定它裝到哪個 partition、能 link 誰。牽動 Treble 分離與 VNDK 連結規則 |
| **`cc_defaults`** | Soong 的設定範本，讓公版與多個客戶專案共用同一組編譯選項，是公版工程的必備 |
| **`soong_config`** | Soong 的條件式設定機制，用來在不 fork 原始碼的前提下依產品開關功能 |
| **linker namespace** | Runtime 的第二道牆：即使 build 期連結過關，執行期 linker 仍依 namespace 規則決定 vendor 程序能載入哪些 `.so` |
| **prebuilt blob 交付** | 以 prebuilt module 或 `PRODUCT_COPY_FILES` 形式把編好的二進位給客戶，原始碼不出門——chip vendor 保護 IP 的標準做法 |
| **三層分支模型** | 應對「SoC × Android 版本 × 客戶專案 × 每月 security patch」的組合爆炸：公版主線 → 版本分支 → 客戶專案分支，搭配明確的 cherry-pick 方向規範 |

---

## 十九、Kernel 交付：Kleaf 與 KMI

> 出自 [02 GKI 與 Kleaf Kernel Build](../02-gki-kleaf-kernel-build.md)。GKI 本身的定義見第三節。

| 名詞 | 說明 |
|---|---|
| **四層蛋糕** | GKI 之前每家 vendor 的 kernel ＝ 上游 LTS + Google patch + SoC patch + ODM patch，四層各自魔改導致無法共用更新，是 GKI 要終結的碎片化 |
| **Kleaf** | Bazel-based 的 kernel build 系統，取代舊的 `build.sh`。Vendor 用自己的 `BUILD.bazel` 定義 kernel build，再接回 platform build |
| **KMI（Kernel Module Interface）** | GKI 核心與 vendor module 之間的穩定 ABI；有了它 Google 才能單獨更新 kernel 而不重編 vendor module |
| **symbol list** | Vendor 要用的 kernel symbol 必須先登記進 symbol list，才會被納入 KMI 保護範圍。沒登記的 symbol 隨時可能消失 |
| **ABI 檢查** | build 時比對目前 kernel 的 ABI 與凍結的基準，任何破壞 KMI 的改動會直接擋下來——把「相容性」從人工紀律變成 CI 檢查 |

---

## 二十、量產、簽章與認證

> 出自 [05 OTA 與簽章](../05-ota-signing-flow.md)、[06 xTS 認證測試](../06-xts-compliance-testing.md)、[13 工廠與量產流程](../13-factory-production-flow.md)。

| 名詞 | 說明 |
|---|---|
| **target-files** | 簽章與 OTA 的中樞產物：一包含有所有 image 素材與 metadata 的 zip，換 key 與產 OTA 包都從它出發，而不是從已簽好的 image |
| **`sign_target_files_apks`** | 把 dev key 簽的 target-files 換成 release key 的工具。**「開發期正常、換 release key 後開不了機」的事故就發生在這一步的前後** |
| **`ota_from_target_files`** | 從 target-files 產出 OTA 包（full 或 incremental）的工具 |
| **release key vs test key** | AOSP 預設用公開的 test key（`releasekey`／`platform`／`shared`／`media` 四把的測試版）；量產必須換成自家保管的 release key，否則任何人都能簽出你的系統更新 |
| **Tradefed（Trade Federation）** | Google 的測試框架，xTS 全家都跑在上面；`run cts`／`run vts` 這類指令與結果報告都由它產生 |
| **MTS（Mainline Test Suite）** | 針對 Mainline 模組的測試套件，因 APEX 每月更新而存在 |
| **calibration（校準）** | 產線關鍵工序：RF 功率、sensor 零點、camera 色彩／對焦、螢幕白平衡等逐台量測並把參數寫進裝置。校準資料遺失＝機器功能不正常但外觀正常，返修最難查 |
| **序號化與金鑰灌注** | 產線寫入 IMEI／SN 與各種裝置專屬金鑰的步驟，通常在安全環境下進行且不可逆 |
| **final fusing（出貨態）** | 產線最後把 eFuse 燒成出貨狀態（鎖 bootloader、關 debug 通道、啟用 secure boot）。**燒完不可逆**，燒早了機器就無法再進產測 |
| **pstore / ramoops** | 保留一塊記憶體跨重開機存活，把 panic 前的 kernel log 留下來——「最便宜的黑盒子」，量產機上最常靠它取證 |
| **Perfetto** | Android 現行的主力 trace 工具（取代 systrace），同時涵蓋 kernel ftrace 與 userspace atrace，是 jank／功耗／binder latency 分析的主戰場 |

---

## 二十一、圖形合成（SurfaceFlinger）

> 出自 [SurfaceFlinger：Android 畫面是怎麼被「合成」出來的](../surfaceflinger-composition-and-debugging.md)。

| 名詞 | 說明 |
|---|---|
| **SurfaceFlinger** | 系統的合成器：把所有 App 與系統 UI 的 layer 合成為一張最終畫面送給顯示硬體 |
| **BufferQueue** | 傳統的 producer/consumer buffer 傳遞模型，App 是 producer、SurfaceFlinger 是 consumer |
| **BLAST（Buffer as LayerState）** | Android 12 之後的新模型，把 buffer 提交與 layer 狀態變更合併成一次 transaction，減少同步往返 |
| **VSYNC** | 顯示硬體的垂直同步訊號，是整個繪製與合成節奏的時基；SurfaceFlinger 依它排程 |
| **Choreographer** | App 端對應 VSYNC 的節拍器，決定 UI thread 何時執行 input／animation／draw |
| **HWC（Hardware Composer HAL）** | 決定每個 layer 由顯示硬體直接合成（**Device Composition**）還是丟回 GPU 畫（**Client Composition**）的仲裁者 |
| **Device vs Client Composition** | 本篇的核心分歧點：走 HWC 幾乎不耗 GPU，**fallback 到 GPU 合成則直接反映在功耗與溫度上**。層數超過硬體上限、格式／縮放不支援、有 blur/圓角等效果都可能觸發 fallback；平板多視窗場景特別容易踩到 |
| **TimeStats** | SurfaceFlinger 內建的統計式 jank 資料來源，適合回答「掉幀有多頻繁」而非「這一幀為什麼掉」 |
| **Winscope / Layer Trace** | 錄下 layer 樹與 transaction 變化並可逐幀回放的工具，用來查「畫面上為什麼多/少了一層」 |

---

## 二十二、Dirty SEPolicy 偵測與隱藏

> 出自 [Dirty SEPolicy 偵測：一種讓所有 Root 方案都現形的新向量](../dirty-sepolicy-detection.md)。SELinux 本身的定義見第十節、Root 工具見第九節。

| 名詞 | 說明 |
|---|---|
| **binary policy** | `checkpolicy` / `secilc` 編譯出、開機由 init 載入核心的二進位規則檔，之後存在記憶體的 `selinux_state` 裡。**同機型同版本的原廠 policy 位元級一致**，所以它有指紋，任何偏離都是異常 |
| **dirty sepolicy** | Root 方案為了運作而注入額外規則（開放 su domain、允許 App 與 root 服務通訊、把 domain 設 permissive、模組的 `sepolicy.rule`）後，核心中生效的 policy 偏離原廠的狀態 |
| **`/sys/fs/selinux/policy`** | selinuxfs 節點，**任何 App 都能讀**，讀到的正是當下記憶體裡完整生效的 binary policy。這是偵測方直接檢查核心狀態的窗口 |
| **偵測判準** | App 的 native SDK 自行解析 policy 後找：可疑自訂 type／domain（含 `magisk`／`su`／`ksu` 字樣）、**任何 permissive domain**、`untrusted_app` 被授予異常權限、規則總數或雜湊對不上該機型原廠 |
| **為何全覆蓋** | 傳統隱藏術（Magisk Hide／Shamiko／改包名）騙的是「App 能觀察到的周邊資訊」；但 **root 要能運作就必須真的改核心 policy，這是功能性的、不可迴避的**。Magisk／KernelSU 全分支／APatch 實作路徑各異，最終都會在這份 policy 上留痕 |
| **`security_read_policy`** | 核心中回應 policy 讀取請求的函式，是隱藏方的 hook 攔截點 |
| **Hide SELinux modifications / `selinux_hook`** | 分別是 KernelSU 的設定與 APatch 的 KPM：在核心讀取路徑上判斷呼叫者是否為非特權 App UID，是則回傳一份「原廠未修改」的 policy 副本，否則回傳真實（髒的）policy 讓 root 照常運作。因 hook 位於核心層，App 無法繞過 |
| **自行驗證方法** | 對目標行程 `strace`（或 frida 掛 libc），看功能被擋前是否出現 `openat(..., "/sys/fs/selinux/policy", O_RDONLY)` + `read`。隱藏生效時 `openat` 依然會發生，差別在讀回的內容已被換掉 |

---

## 二十三、裝置信任邊界與 Baseband

> 出自 [一支手機從開機到連上網，中間跨過了幾道信任邊界](../mobile-trust-boundaries.md)（純公開規格整理）。BL1~BL33／TrustZone 見第五節，AVB／dm-verity 見第七節。

| 名詞 | 說明 |
|---|---|
| **信任邊界（trust boundary）** | 「這邊的東西不能無條件相信那邊」的界線。一支手機裡有五到十幾顆各跑自己韌體的處理器，**失誤幾乎都發生在邊界上，而不是單一模組內部** |
| **BootROM / mask ROM** | 晶片製造時寫死在矽上的第一段程式碼，出廠後改不了——這個「不可變」就是**信任根（Root of Trust）**。代價是 bug 幾乎無法修補（checkm8、fusée gelée 都是此層漏洞），所以刻意寫得極簡 |
| **efuse / OTP** | 晶片上只能寫一次的記憶體。實務上放**公鑰的雜湊值**而非完整公鑰（公鑰跟映像檔一起放 flash，開機時算雜湊比對）。單向不可逆——既是安全價值也是報廢風險 |
| **簽章 ≠ 加密** | Secure boot 要的是**簽章驗證（完整性／來源）**，不是加密（機密性）。沒加密但簽章正確足夠安全；加密但不驗簽可能等於零安全。**把機密性當成安全機制，是一種會過期的保護** |
| **anti-rollback** | 映像檔帶單調遞增版本號，efuse 保留一組 bit 記錄「目前可接受的最低版本」。危險在 efuse bit 有限、推進後無法降版——所以推進時機通常非常保守 |
| **串聯電路模型** | 信任鏈不是「多一層多一分安全」的疊加，而是串聯：**九級做對、一級做錯等於零級**。要問的是「最弱的一級在哪」而不是「我們有幾層防護」 |
| **modem（數據機）子系統** | 不是加速器而是**真正獨立的子系統**：跑自己的 RTOS、有自己的記憶體與生命週期，**輸入不來自 AP 而來自空氣** |
| **協定處理器 vs 基頻 DSP** | 前者跑 3GPP 上層（RRC／NAS／PDCP/RLC/MAC），狀態機龐大，跑在即時導向核心 + RTOS；後者跑實體層（調變解調、Turbo/卷積/LDPC/Polar 編解碼、FFT、通道估測），用帶向量／SIMD 的專用 DSP |
| **1 ms subframe / HARQ 預算** | FDD LTE 下行 HARQ 回饋固定落在 subframe n+4，扣掉傳輸與上行準備，終端解調＋解碼＋CRC 的處理預算約 3 ms，且必須以每 1 ms 一次的節奏持續 pipeline。5G NR 在較高 subcarrier spacing 下 slot 更短（1 ms / 2^μ）。**這種硬性即時要求就是 modem 必須獨立於跑 Linux 的 AP 的原因** |
| **modem 三性質疊加** | (1) 輸入本質不可信——初始接取階段尚未雙向認證，SDR 成本已降到數百美金；(2) 攻擊面極大——數千頁規格、為向後相容保留的老機制、多套變長編碼（RRC 用 ASN.1 unaligned PER、NAS 用 IEI/TLV），解析器多半是 C 寫在無現代記憶體保護的 RTOS 上；(3) 傳統上權限高。合起來＝**不需使用者互動、只要在無線電範圍內即可觸發的遠端攻擊路徑** |
| **IOMMU / SMMU** | 放在 modem 與記憶體控制器之間的位址轉譯與權限檢查單元，由 AP 側安全軟體設定。把「modem 淪陷 = 全機淪陷」降級成「modem 淪陷 = modem 淪陷」——**不需要 modem 韌體完美就能限制爆炸半徑，投報率最高的單一措施** |
| **subsystem restart 的驗證缺口** | modem 崩潰重啟是常見復原機制，但**重啟路徑必須跟冷開機一樣做完整驗證**；為省時間跳過驗證等於在信任鏈上開後門 |
| **PSA 生命週期狀態** | Arm PSA Security Model 定義的裝置階段：Blank／Development（開發金鑰、除錯全開）／Production（量產金鑰、除錯關閉、secure boot 生效）／RMA。狀態記在 efuse，由硬體強制而非靠人記得改設定 |
| **PSA ADAC** | Authenticated Debug Access Control：受控的除錯授權機制。RMA 重開除錯的常見做法是用晶片唯一 ID 產生挑戰值、回原廠簽章後只解鎖那一顆晶片 |
| **「有支援」≠「有生效」** | BSP 支援 ＝ 程式碼寫好了；不等於這台出貨裝置上它正在運作。中間隔著 efuse 有沒有真的燒、燒的是量產還是開發金鑰、生命週期有沒有推進、量產 build 有沒有真的關掉除錯、anti-rollback 有沒有啟用 |
| **驗證「攻擊失敗」而非「機制存在」** | 弱驗證是查設定檔（secure boot enabled、console disabled、JTAG disabled、anti-rollback 已設定）；強驗證是實測（刷未簽章映像確認拒絕開機、實接 UART 確認無輸出、實接除錯器確認連不上、刷舊版本確認被拒）。**設定檔會說謊，實測不會** |
| **量產殘留** | 測試憑證、內部工具的特權介面、產線快速刷機路徑——共通點是「當初有正當理由」，然後沒人負責移除，因為**沒有人會因為多留了一個 debug hook 而測試失敗**。要靠流程關卡攔截而非測試 |
| **五類典型實作缺陷** | (1) 驗證失敗但只 log 一行就繼續執行；(2) 簽章只涵蓋 header，內容可替換；(3) 先載入到最終位址再原地驗證（其他 DMA 主控可改 → TOCTOU）；(4) 信任鏈斷點（信任鏈是樹不是線，漏掉一根枝條不易察覺）；(5) 回退／recovery／子系統重啟路徑不驗證。**共同點：都不是密碼學問題，破的是「什麼時候驗、驗多少、驗完怎麼辦」的工程決定** |

---

## 二十四、MTK Boot Chain 與 LK 端的 AVB

> 出自 [MTK Boot 深入筆記](../mtk-boot-deep-dive.md)。AVB 本體術語見上方第七節「Verified Boot」與第十四節，這裡只列 MTK 鏈路與 LK 端特有的部分。
> 記憶體共享（dma-buf / dma-heap）相關名詞見 [Embedded 名詞表](embedded_glossary.md) 第八節。

| 名詞 | 說明 |
|---|---|
| **MTK boot chain** | `BootROM → Preloader（BL2）→ ATF/TEE → LK（BL33）→ Kernel`。對照高通是 `PBL → XBL → TZ → ABL`（見上方第五節對照表） |
| **SBC key** | MTK Secure Boot 的信任起點：public key hash 燒在 eFuse 裡，BootROM 用它驗 Preloader 簽章。**整條鏈是「上一級驗下一級」，任何一環沒驗就是整條斷掉** |
| **Preloader 驗誰** | Preloader 除了把 DRAM 弄起來，還負責載入並驗證 `lk`、`tee`（ATF）、`gz`（GenieZone）。開機 logo／充電動畫不一定在 LK——逆向資料指出部分機種由 Preloader 負責 |
| **LK 的職責清單** | 進 fastboot mode、畫 logo／充電畫面、讀 `misc` 決定 recovery／fastbootd／normal、A/B slot 選擇、AVB 驗證、組 kernel cmdline 後載入 `boot`／`vendor_boot`／`dtbo`／`init_boot` |
| **hash vs hashtree 的取捨** | `boot.img` 幾十 MB，開機時算完整 hash 成本可接受；`system.img` 幾 GB 只能用 hashtree，把驗證成本攤到 runtime 每次 I/O。代價是 dm-verity 有持續開銷，且**壞 block 要讀到才會報錯，不是開機就抓到** |
| **tamper-evident storage** | AVB 規範要求 rollback index、驗證用金鑰、LOCKED/UNLOCKED 狀態都存在防竄改儲存；常見實作是 RPMB，由 TEE（如 OP-TEE）持金鑰存取。AVB 1.1 後另加 named persistent values 可存任意 key-value |
| **rollback index 規則** | 除非 `rollback_index[n] >= stored_rollback_index[n]` 對所有 n 成立，否則拒絕該 image；裝置會隨時間把 `stored_rollback_index[n]` 往上推。擋的是「**簽章合法但有已知漏洞的舊版 image**」 |
| **YELLOW vs ORANGE vs RED 的畫面行為** | YELLOW（鎖著＋使用者自燒 root of trust）與 ORANGE（已解鎖）都是顯示警告後**10 秒自動消失**繼續開機；RED（驗證失敗）的警告**不能由軟體自動關掉，必須使用者按實體鍵** |
| **`bootloader_message_ab`** | `misc` 分區裡的 slot metadata：`priority`（0–15，越大越優先）、`tries_remaining`、`successful_boot`。LK 挑 priority 最高且（successful 或 tries > 0）的 slot，每試一次 tries 減一；全用光就進 recovery |
| **AVB 與 A/B 正交** | 每個 slot 有自己的 vbmeta，各驗各的——兩套機制彼此獨立，不要混在一起想 |
| **`get_unlock_ability`** | 開發者選項的「OEM unlocking」寫下的 bit，存在防竄改區。`fastboot flashing unlock` 前 LK 會檢查它，並在解鎖時**強制 wipe userdata**——就是為了防止「撿到別人手機直接 unlock 拿資料」 |
| **只刷 boot 沒刷 vbmeta** | `vbmeta verification failed` 最常見的成因。開發時用 `fastboot --disable-verity --disable-verification flash vbmeta vbmeta.img` |
