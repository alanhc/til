---
title: Android / Pixel 系列文章索引
sidebar_label: Android 系列索引
sidebar_position: 0
---

# Android / Pixel 系列文章索引

本頁整理知識庫中所有 Android、AOSP、Pixel 相關筆記，依主題分類。
名詞定義請參考 [Android 名詞表](android_glossary.md)。

---

## 一、入門與總覽

| 文章 | 內容 |
|---|---|
| [Android 平台架構](../android.md) | Android 五層架構圖、kernel 位置、booting 參考資料 |
| [Android 知識整理摘要](../分析/android-summary.md) | 跨筆記的總整理：架構、boot flow、AOSP 環境、ADB、Root |
| [Learning Pixel / Android 學習路線](../android_pixel_learning.md) | Step 1~5 學習規劃：從 Cuttlefish 編譯 → BeagleBone/RPi bring-up → GKI → MTE 除錯 → 效能對標 |

---

## 二、開機流程與 Bootloader

| 文章 | 內容 |
|---|---|
| [韌體安全全景](../firmware_security.md) | **總圖**：把韌體安全當領域組織的五道防線——供應鏈金鑰／開機信任鏈／執行期隔離／韌體更新／攻擊面。串起 [Secure Boot 解析](../Secure_Boot_解析.md)、[TF-A 解析](../ARM_Trusted_Firmware_解析.md)、[SELinux](../selinux.md) 三篇深入版，並補上執行期保護、攻擊面（含 MTK BROM exploit）、供應鏈等目前沒展開的塊 |
| [Android Boot Flow](../android_boot_flow.md) | 完整開機流程：Boot ROM → Bootloader → Kernel → Init → Zygote → System Server → Launcher，含 partition 結構與除錯方法 |
| [Bootloader](../bootloader.md) | Little Kernel (LK)、Aboot、PBL/SBL 兩階段 bootloader、SoC 廠商生態 |
| [ARM Trusted Firmware (ATF)](../atf.md) | BL1~BL33 各階段、Exception Level (EL0~EL3)、TrustZone、OP-TEE、Secure/Normal World、CCA 演進時間軸 |
| [ARM Trusted Firmware 元件](../arm_trust_firmware.md) | TF-A 主要元件：PSCI、SMC Dispatcher、SiP service、Root of Trust |
| [ARM Trusted Firmware (TF-A) 解析](../ARM_Trusted_Firmware_解析.md) | **深入版**：BL1~BL33 各階段職責、TBBR 憑證鏈如何銜接 AVB、BL31 常駐的 Secure Monitor／PSCI／中斷路由、各家 SoC 階段命名對照（高通 PBL/XBL/TZ、MTK Preloader/ATF/LK）、platform port 與 QEMU 上手路徑 |
| [Secure Boot 解析](../Secure_Boot_解析.md) | **深入版**（上篇姊妹篇，講「憑什麼信任」）：簽章 vs 加密、Boot ROM 與 eFuse 兩個錨點、TBBR 的 X.509 憑證鏈與金鑰隔離、AVB 2.0 與 rollback index、boot state 四色、攻擊面（glitching／TOCTOU／EDL／checkm8）、導入 checklist |
| [Android Verified Boot (AVB) 深入解析](../Android-Verified-Boot-AVB.md) | **深入版**（把上面 Secure Boot 提到的 AVB 展開）：硬體信任根 → `vbmeta` 樞紐（hash／hashtree／chain partition／kernel cmdline descriptor）→ dm-verity 區塊級執行期驗證 → rollback index 防降級 → GREEN／YELLOW／ORANGE／RED 四狀態與 Keystore attestation；含刷機實務（`--disable-verity`／`--disable-verification`、`avb_custom_key` 自簽走 YELLOW、`avbtool info_image`、重新上鎖變磚的坑） |
| [把 ABL 拆開看：AVB 驗證在真機上到底怎麼跑](../abl-avb-reversing.md) | **上篇的實作對照版**：把 Qualcomm 手機的 ABL（UEFI application）從 `abl.img` 剝殼成 PE32+ 丟進 Ghidra，用字串（`androidboot.verifiedbootstate=`、`AVB0` magic、`avb_slot_verify.c`）當錨點定位 AVB；再逐步走 `avb_slot_verify()` → vbmeta header 解析 → SHA + RSA 驗簽 → descriptor（hash／hashtree／chain／cmdline）→ rollback index → 綠黃橙紅四色 → 組 kernel cmdline。核心結論：libavb 是通用密碼學骨架，**真正決定安不安全的是廠商在 `AvbOps` 回呼裡有沒有偷工**（金鑰比對、rollback 接 RPMB、鎖狀態）。附逆向常踩的坑 |
| [MTK Preloader Combo Header 與 OTA](../mtk-preloader-combo-header-ota.md) | MTK boot chain（BROM → Preloader → LK）中 preloader 住在 eMMC boot0/UFS boot LU；device header 三型態（`EMMC_BOOT`／`UFS_BOOT`／`COMBO_BOOT`）與 device header → BRLYT → GFH 三層結構，以及怎麼接上 Google A/B OTA（`update_engine` byte-level 寫入故 image 需自帶 header、by-name symlink、header 型態不一致導致 source hash mismatch 的故障排查）。各節標註公開來源 vs 內部推論 |

---

## 三、建置：AOSP 平台與 App

| 文章 | 內容 |
|---|---|
| [Pixel 8 AOSP 完整工作流程](../aosp_pixel_full_workflow.md) | **主線教學**：build ID ↔ AOSP tag ↔ vendor driver 三者對齊 → repo sync → vendor blob → lunch/m → fastboot flashall，含常見錯誤與救磚 |
| [Pixel 8 AOSP Full Workflow (EN)](../aosp_pixel_full_workflow_EN.md) | 上篇的英文版 |
| [Android Build Project](../android_build_project.md) | 環境套件安裝、repo init/sync、Cuttlefish 虛擬機建置、詞彙表（ACK、GKI、VNDK） |
| [AOSP Codebase](../aosp_codebase.md) | `.repo/manifests/default.xml` 查目前 branch revision |
| [Android Build Number 解析](../Android_build_number.md) | `BP4A.251205.006` 各欄位含義（代號／分支／日期／patch） |
| [搞懂三種 Build Variant：user／userdebug／eng](../android-build-variants.md) | 三者的定位與底層差異：`ro.secure`／`ro.debuggable` 兩個屬性怎麼決定能不能 `adb root`、模組安裝範圍（eng 全裝 vs user 只裝 product 要求）、dexpreopt 最佳化開關與效能落差；附完整對照表與「重現使用者問題／量效能／QA 一律用 `userdebug` 而非 `eng`」的實務原則 |
| [Android Product Flavor 完整教學](../android-product-flavor-完整教學.md) | **App 層（Gradle）**：一份程式碼產出多個 App——build type／product flavor／build variant 三者關係、Groovy 與 Kotlin DSL 兩種寫法、flavor 能客製什麼（`applicationId`／`BuildConfig`／manifest placeholder／source set 資源與程式碼覆寫）、flavor dimensions 多維度組合、免費版 vs 付費版實戰、依 flavor 加依賴，以及常見陷阱 |

---

## 四、Pixel 硬體與刷機

| 文章 | 內容 |
|---|---|
| [Pixel 硬體代號](../pixel_hardware.md) | `zuma` = Tensor G3 SoC、`shiba` = Pixel 8、kernel 分支 `android-gs-zuma-*` |
| [Pixel Study](../pixel_study.md) | 實作全紀錄：ADB 安裝、開發者模式、repo sync、lunch、flashall log、anti-rollback 錯誤、`flash-all.sh` 救磚 |
| [Pixel Fastboot Deep Dive](../pixel_fastboot_deepdive.md) | `fastboot flashall -w` 完整輸出逐行紀錄 |
| [Pixel Image 來源對照](../pixel_img.md) | 哪些 image 是 `m` build 出來的、哪些是 vendor blob、哪些是 Google 原廠 binary |
| [Pixel Flash Debug](../pixel_flash_debug.md) | `Failed to find AVB_MAGIC at offset: 0` 根因分析——不該加 `--disable-verity`，含成功 flash 紀錄 |
| [用 Android Flash Tool 刷不同版本](../pixel_flash_another_version.md) | 網頁版 flash.android.com 操作重點 |
| [Pixel Driver](../pixel_driver.md) | Root 權限與 kernel module 載入前置作業 |

---

## 五、Root 與權限

| 文章 | 內容 |
|---|---|
| [Pixel Root](../pixel_root.md) | Magisk（user-space，patch `init_boot.img`）vs KernelSU（kernel-space，改 `boot.img`）比較 |
| [Pixel 無法 adb root](../pixel_can_not_run_as_root.md) | `adbd cannot run as root in production builds` 的解法：Magisk patch init_boot，含 `/sys/class/` 節點列表 |

---

## 六、工具與除錯

| 文章 | 內容 |
|---|---|
| [adb（Android Debug Bridge）](../android_adb.md) | 常用指令速查、多裝置 `-s`、`adb root`/`remount`、無線除錯 |
| [Android SEPolicy / SELinux](../android_sepolicy.md) | 速查：Security context、`.te` 檔、`allow`/`neverallow`、AVC denied 判讀、`audit2allow` |
| [SELinux 是什麼？為什麼 Android 韌體工程師必須懂它](../selinux.md) | **深入版**：MAC vs DAC、LSM hooks / AVC / selinuxfs 元件、Treble 後的 sepolicy 四層架構、從 denial 反推 owner 的四種方法、為何是 CTS/GMS 出貨硬條件 |
| [adb logcat 與 UART：Android 除錯的兩把刀](../adb-logcat-vs-uart.md) | 兩者為何不能互相取代：logcat 走 Android log buffer（tag／優先級／`--pid`／crash buffer 過濾），UART 是硬體直連的序列 console，看得到 bootloader／`printk`／panic 死前最後幾行。附開機七階段（Boot ROM → SPL/BL1·BL2 → U-Boot/ABL → Kernel → init → Zygote → Boot completed）與 JTAG／UART／adb 的可用性對照表與圖，以及 watchdog／ANR／tombstone／bootloop 等相關名詞速查 |
| [從 `mount -o remount` 到 OverlayFS：Driver 開發者必須弄懂的 remount 機制](../android-remount-deep-dive.md) | **深入版**：為何現代 Android 分區改不動——dm-verity／AVB、dynamic partition right-sizing 沒有剩餘空間、EROFS 根本不可寫三道約束；AOSP 的解法是把 `adb remount` 重新實作成 **overlayfs**（lower = 唯讀原分區，upper = `/cache/overlay` 或 `super` 裡的 `scratch` 邏輯分區），所以你看到的是「出廠 image + 你的 diff」的合成視圖。含標準流程、對 driver／HAL／firmware／`init.*.rc`／vendor sepolicy 的迭代價值，以及九條踩坑（first stage init 與 ramdisk 蓋不到、空間會爆、remount 過的機器不能吃 OTA、bootloader fastboot 刷機不會被偵測到） |
| [SurfaceFlinger：Android 畫面是怎麼被「合成」出來的](../surfaceflinger-composition-and-debugging.md) | 從「開分割畫面就耗電、滑動掉幀但 App profiler 正常」這類 bug 出發：SurfaceFlinger 的定位、BufferQueue → **BLAST**（Android 12+）的資料流變化、VSYNC 與 Choreographer 的節奏。核心是**Device Composition（HWC 硬體合成）vs Client Composition（GPU 合成）這個分歧點**——fallback 到 GPU 為何直接反映在功耗與溫度上、哪些情況會 fallback（層數超過、格式/縮放不支援、有 blur/圓角）、平板多視窗場景為何特別容易踩到。除錯五件套：`dumpsys SurfaceFlinger`、TimeStats、Perfetto、Winscope/Layer Trace 與建議的檢查順序 |
| [效能實驗：Codec 判讀](../performance_experient.md) | YouTube debug overlay 判讀硬解／軟解、`[exo2]` vs `[plat]`、VP9 Profile 2 HDR fallback、掉幀分析 |

---

## 七、AI 與工作流

| 文章 | 內容 |
|---|---|
| [韌體開發與 Agentic AI](../android_firmware_development_and_agentic_ai.md) | 把 AOSP build pipeline 封裝成 AI Agent Skill、AI/人的介入邊界設計、三個真實踩坑紀錄 |
| [Android 工程師 Agent Skills 規劃](../android_engineer_skills.md) | 10 個適合系統整合團隊的 skill 提案（build 對齊、error triage、flash rescue、bring-up checklist、log analyzer 等） |

---

## 八、周邊與延伸平台

| 文章 | 內容 |
|---|---|
| [Android Automotive OS（AAOS）開發者入門](../AAOS-開發者入門.md) | 先把 Android Auto（手機投影）／AAOS（跑在車機上的 OS）／AAOS + GAS 三者分清楚；為何值得投入（生態複用、量產車廠、SDV 趨勢）、車用專屬的六塊核心元件（VHAL 把車速／空調／檔位抽象成 property、`android.car` 的 `CarPropertyManager`、`car-ui-lib` 與 System UI、多 display／多 user、template 化的車用 app 範式、Car Audio 分區與開機效能），以及開發者入門路徑與常見坑 |
| [工程機](../工程機.md) | 高通工程機相關影片筆記 |

---

## 九、Android 供應鏈與長期維護

> 一個系列，從 **Google／晶片商／系統廠**三方視角，看 Android 為什麼能承諾七年更新的制度地基：Treble 切開 system/vendor、GRF 凍結 vendor 要求、GKI 收編 kernel。建議依序讀。

| 文章 | 內容 |
|---|---|
| [Android Migration](../android-migration.md) | **系列第一篇（總論）**：Android 大版本遷移為何是一條跨三家公司的串行供應鏈、一次升級的工作分解（晶片商 BSP → OEM framework rebase → CTS/VTS 認證 → OTA）、Project Treble 如何用 HIDL/AIDL + VINTF/FCM 切開 system/vendor，以及 Treble 沒解決的「要求年年追加」如何通往後兩篇 |
| [Vendor Freeze](../vendor-freeze.md) | **系列第二篇**：GRF／Longevity GRF 的凍結機制與三方賽局——`ro.board.first_api_level` 等 board property、VINTF／FCM 相容性合約、「3 年一次 kernel 大版本升級」條款、功能天花板如何在 SoC 選型那一刻就被決定 |
| [Android Kernel](../android-kernel.md) | **系列第三篇**：Android kernel = Linux + Android 補丁（Binder／wakelock／ION 的上游化史）、GKI 之前的四層 fork 碎片化、GKI／KMI 如何把 kernel 切成 Google 核心本體 + vendor module，以及三方各自的角色與工程實務 |

---

## 十、虛擬化、隔離與安全研究

> 當 UID sandbox + SELinux 的前提「kernel 是可信的」不再成立時，Android 往兩個方向走：**把機密計算搬進 kernel 讀不到的 VM**（AVF / Microdroid），以及**持續被攻破的實證**（協同處理器 driver）。兩篇對照著讀最有感。

| 文章 | 內容 |
|---|---|
| [Microdroid：Android 為什麼要在手機裡再開一台 Android](../Microdroid.md) | AVF / pKVM / crosvm / pVM / Microdroid 五個名詞的層次拆解；pKVM 把 **host kernel 降權到 EL1、hypervisor 留在 EL2**，用記憶體捐贈 + stage 2 讓 Android kernel 讀不到 guest 記憶體（配套：MMIO guard、IOMMU/SMMU、FF-A proxy）。Microdroid 有什麼沒什麼（無 Zygote／SystemServer／`android.*`／HAL，payload 是 native `.so`）、磁碟分割表為何長得像一台手機、開機鏈七步（pvmfw → bootloader → kernel/init → `microdroid_manager` → apexd → zipfuse → payload）、sealing key／attestation key 從量測值推導、`instance` 分割區與 rollback counter，以及 debuggable vs non-debuggable 的安全意義 |
| [當防護開滿反而露出破口：Pixel 8 GXP DSP 漏洞與 MTE 繞過](../pixel8-gxp-dsp.md) | HITCON 2025（STAR LABS SG）議程整理：攻擊面選擇邏輯（越邊緣防護越薄）→ SELinux policy 反推出「有 server 代開 `/dev/gxp` 再傳 FD」→ 漏洞本體是 `gxp_mapping_create()` **直接信任 user 傳入的 DMA direction**，不與 VMA 屬性比對 → 取得 **write read-only memory primitive**（MTE 完全看不到，因為它保護的是 CPU 端存取）→ Frida replay attack 取代硬啃 firmware → camera provider library hijacking → modprobe → 關 SELinux → root。含修補方向與防禦視角 |

---

## 十一、Chip Vendor 視角系列（16 篇）

> 一個完整系列，從 **SoC 廠（chip vendor）維護 BSP** 的角度重走 Android 平台工程：你的地盤在哪、Google 劃了哪些邊界、交付什麼給客戶、出貨前要過哪些關。與第九節（供應鏈三篇）互補——那邊講制度，這邊講日常操作。
>
> 建議照編號順序讀；01 是總覽，16 附系列全目錄。

| 文章 | 內容 |
|---|---|
| [01 Android Build System：Chip Vendor 視角](../01-android-build-system-chip-vendor.md) | **系列總覽**：repo + manifest 如何把 AOSP／SoC BSP／客戶專案三種來源組起來、`envsetup` → `lunch` → Soong/Kati → Ninja 的引擎鏈、product 層 vs board 層兩條設定軸線與繼承鏈（SoC 公版 → 客戶專案）、Treble／GKI／sepolicy 三道邊界，以及最終產出的 partition 與 image |
| [02 GKI 與 Kleaf Kernel Build](../02-gki-kleaf-kernel-build.md) | kernel 碎片化的四層蛋糕（上游 LTS + Google patch + SoC patch + ODM patch）如何逼出 GKI；從 `build.sh` 到 **Kleaf**（Bazel-based）的實際操作、vendor 自己的 `BUILD.bazel`、接回 platform build；**KMI** 的工程紀律：symbol list 要先登記、ABI 檢查、boot image 重組，附常見坑 |
| [03 Soong 與 Android.bp：vendor variant 與 VNDK](../03-soong-android-bp-vendor-vndk.md) | Soong 的宣告式哲學、`cc_defaults` 與 `soong_config` 條件式設定；重點是 **`vendor: true` 到底做了什麼**——image variant 概念、vendor module 能 link 誰、VNDK 的歷史與現況、runtime 第二道牆 linker namespace。含交付 prebuilt blob、stable AIDL HAL、`.mk` → `.bp` 遷移三個典型場景 |
| [04 SELinux Sepolicy 除錯實戰](../04-selinux-sepolicy-debugging.md) | Treble 後 policy 的目錄結構，以及一套系統化流程：Step 0 先確認真的是 SELinux → 抓 denial → `audit2allow` 產候選規則 → **放進正確的 `.te` 檔** → 確認 label 本身是對的 → 重 build 驗證。關鍵在「`audit2allow` 之外：判斷該不該 allow」與 neverallow／chip vendor 特有的坑 |
| [05 OTA 與簽章流程](../05-ota-signing-flow.md) | 金鑰體系（APK 四把 platform key、AVB 金鑰、其他）、**target-files 是簽章與 OTA 的中樞**、`sign_target_files_apks` 換 key、`ota_from_target_files` 產包；A/B seamless update 機制與 full/incremental 包差異、量產前檢查清單，以及「開發期正常、換 release key 後開不了機」這類常見事故現場 |
| [06 xTS 認證測試：CTS/VTS/GTS/STS](../06-xts-compliance-testing.md) | **過不了 xTS，客戶拿不到 GMS 授權就不能出貨**。四套測試的分工與誰最痛、與 chip vendor 最相關的 VTS（Treble 合約的執法者）／CTS-V／STS（security patch 查核）、Tradefed 工作流與分析 fail 的標準流程，以及把 xTS 工程化的做法 |
| [07 開機流程與 Bootloader](../07-boot-flow-bootloader.md) | 完整開機鏈 BootROM/PBL → SBL/preloader → ABL/LK/U-Boot → kernel → first/second stage init → Zygote → 桌面，重點是**各階段能用什麼手段除錯**的對照表（卡在哪一階段決定你該抓什麼 log） |
| [08 HAL 開發實戰：AIDL 介面到開機起服務](../08-hal-development-aidl.md) | **把 03（Android.bp）／04（sepolicy）／01（VINTF）串成一條線**：以一支 thermal 擴充 HAL 為例，從 HIDL → stable AIDL 的背景，走完定義 `aidl_interface` → 實作 service → `init.rc` + VINTF 讓它開機起來且被找到 → sepolicy 讓它活下來 → 掛進 product 驗證 → 版本演進與多實例 |
| [09 Android 年度版本升級方法論](../09-annual-android-upgrade.md) | chip vendor 最大的例行專案：時間軸與策略、Phase 0 評估（寫 code 之前）、Merge 策略與 conflict 分類、公版 bringup、認證 release；含「vendor 與 system 同時升級」的完全體情境（開發期需要一個不動的錨、版本對齊機制、OTA 原子性、測試矩陣變化）與降低明年痛苦的結構性投資 |
| [10 效能與功耗調校](../10-performance-power-tuning.md) | 控制點地圖（kernel 層／HAL-framework 邊界／framework 之上各自誰在決定快慢耗電）、量測工具鏈以 **Perfetto** 為主力加功耗量測與基準場景庫；調校方法論分 jank 與功耗兩條標準流程，並把 thermal 定位成「效能與功耗的仲裁者」 |
| [11 Camera 與多媒體 Pipeline](../11-camera-multimedia-pipeline.md) | 三條 pipeline（相機／Codec2 編解碼／顯示）與它們共用的地基 **graphics buffer 的一生**；各自的架構、chip vendor 的責任區與踩坑，附除錯工具速查。這是 BSP 中最複雜、xTS fail 最集中的領域 |
| [12 Ramdump 與穩定性除錯](../12-ramdump-stability-debugging.md) | 症狀分類（kernel panic／watchdog／native crash／ANR／低機率當機）先分流；kernel 層取證用 **pstore/ramoops**（最便宜的黑盒子）與 ramdump 全記憶體解剖，userspace 用 tombstone／ANR trace／bugreport；低機率問題的攻堅方法，以及「穩定性是指標不是事件」的組織面 |
| [13 工廠與量產流程](../13-factory-production-flow.md) | 網路上資料最少但每家都要做的一塊：量產軟體的組成、典型產線流程，以及燒錄、**校準（calibration）**、序號化與金鑰灌注、出貨態 final fusing 四個關鍵技術點，加上返修售後路徑與交付形式 |
| [14 Android 上的 Rust](../14-rust-on-android.md) | 動機很直接——歷年 Android 安全漏洞約七成是記憶體安全問題。Rust 目前已進入系統的哪些位置、Soong 的原生支援（`rust_binary`／`rust_library`）、chip vendor 的採用策略（先吃甜區、kernel driver 該不該上、組織準備） |
| [15 Project Mainline 與 APEX](../15-mainline-apex-vendor-impact.md) | Treble 拆開 vendor/system，Mainline 更進一步把 system 的一部分交給 Google 從 Play 直接更新——代表**你以為凍結的 framework 其實每月都在變**。APEX 容器與模組群、「配置漂移」對驗證組合的衝擊、MTS 與認證，以及反過來把 vendor APEX 為己所用 |
| [16 多專案 BSP 的 Branch 與 Manifest 管理](../16-bsp-branch-manifest-management.md) | **系列完結**：面對「5 顆 SoC × 3 個 Android 版本 × 上百個客戶專案 × 每月 security patch」，repo/manifest 的管理模式、三層分支模型與版本維度、與客戶的邊界、CI 與工程紀律，以及常見反模式。文末附系列全目錄 |

---

## 建議閱讀順序

**想從零 build 一個 Pixel ROM：**

```
Android Build Number 解析
   → Pixel 硬體代號
   → Pixel 8 AOSP 完整工作流程   ← 主線
   → Pixel Flash Debug（遇到 AVB 錯誤時）
   → Pixel Study（對照實作 log）
```

**想理解系統怎麼跑起來：**

```
Android 平台架構
   → Bootloader
   → ARM Trusted Firmware (ATF)
   → ARM Trusted Firmware (TF-A) 解析   ← 深入 EL3：誰在跑
   → Secure Boot 解析                   ← 姊妹篇：憑什麼信任它
   → Android Boot Flow
   → Android SEPolicy
```

---

## 待補主題

用第一性原理盤點：一個 Android 系統整合工程師的心智地圖，是 **kernel → HAL → framework → app** 四層，外加 **build、update、security、debug** 四條橫軸。下表是這張地圖上重要、但目前筆記還沒有專門文章的缺口，依重要性排序。部分名詞已在 [Android 名詞表](android_glossary.md) 出現，但還沒展開成文章。

| 主題 | 為什麼重要 | 狀態 |
|---|---|---|
| **Binder / IPC 深入** | Android 一切跨程序溝通的底座——system service 呼叫、AIDL、app 生命週期、`dumpsys` 全都跑在 Binder 上。名詞表有列 Binder，但沒有一篇講它的 driver 機制、transaction、`ServiceManager` 註冊流程 | 待補 |
| **A/B Seamless OTA 機制** | 刷機（fastboot）已有完整筆記，但**線上更新**怎麼送——`update_engine`、payload 結構、寫入備用 slot、開機失敗自動 rollback——完全沒有。這是出貨後維運的關鍵 | ✅ 已補：[05 OTA 與簽章流程](../05-ota-signing-flow.md) |
| **init / property system 深入** | `init.rc` 語言、`.rc` trigger、property service 與 `ro.*`/`persist.*` 的儲存與 selabel。Boot flow 帶到 init，但沒有把 Android Init Language 與 property 機制單獨講清楚 | 待補 |
| **HIDL / AIDL HAL 撰寫實作** | 不只是「知道有這個介面」，而是實際寫一支 HAL：`.aidl` 定義 → 產生 stub → binderized service 註冊 → framework 端呼叫。整合團隊天天碰 | ✅ 已補：[08 HAL 開發實戰](../08-hal-development-aidl.md) |
| **Perfetto / systrace / ANR 分析** | `adb` 筆記涵蓋基本指令，但系統化的 framework 除錯——用 Perfetto 抓 trace、判讀 ANR、看 scheduling／binder latency——是效能與卡頓問題的主戰場 | ✅ 已補：[10 效能與功耗調校](../10-performance-power-tuning.md)、[12 Ramdump 與穩定性除錯](../12-ramdump-stability-debugging.md)、[SurfaceFlinger](../surfaceflinger-composition-and-debugging.md) |
| **CTS / VTS 實際跑法** | SELinux 那篇點出 CTS 是出貨硬條件，但沒有一篇講怎麼實際跑 `run cts`、判讀 fail、VTS 測 HAL 相容性。GMS 認證的實務缺口 | ✅ 已補：[06 xTS 認證測試](../06-xts-compliance-testing.md) |
| **FBE 檔案系統加密** | dm-verity 與 AVB 已在 [AVB 深入解析](../Android-Verified-Boot-AVB.md) 涵蓋，但**檔案加密**這塊還沒有：File-Based Encryption、metadata encryption、`/data` 如何綁定硬體金鑰、解鎖為何一定清資料的根因 | 待補 |

> 已補上的缺口：**GKI／KMI** 見 [Android Kernel](../android-kernel.md)、**Treble／VINTF** 見 [Vendor Freeze](../vendor-freeze.md)（第九節）、**SoC bring-up** 見 [Bring-up](../bringup-article.md)（列於 [Embedded 系列索引](embedded_index.md)）。
