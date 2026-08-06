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
| [Bootloader](../bootloader.md) | 為何要分階段（最早的程式碼受限於晶片內 ROM/SRAM 的極小空間）；TF-A 的 **BL0/BL1/BL2/BL31/BL32/BL33** 通用命名表與各家對應不整齊的提醒；Android 三階段 **PBL（Boot ROM，不可更新、secure boot 的信任根）→ SBL/XBL（初始化 DRAM）→ LK/aboot（fastboot、AVB、載入 kernel）**；LK 其實是有排程器的極小 OS，Qualcomm 的 aboot 是它的 fork |
| [ARM Trusted Firmware (ATF)](../atf.md) | BL1~BL33 各階段、Exception Level (EL0~EL3)、TrustZone、OP-TEE、Secure/Normal World、CCA 演進時間軸 |
| [ARM Trusted Firmware 元件](../arm_trust_firmware.md) | TF-A 主要元件：PSCI、SMC Dispatcher、SiP service、Root of Trust |
| [ARM Trusted Firmware (TF-A) 解析](../ARM_Trusted_Firmware_解析.md) | **深入版**：BL1~BL33 各階段職責、TBBR 憑證鏈如何銜接 AVB、BL31 常駐的 Secure Monitor／PSCI／中斷路由、各家 SoC 階段命名對照（高通 PBL/XBL/TZ、MTK Preloader/ATF/LK）、platform port 與 QEMU 上手路徑 |
| [Secure Boot 解析](../Secure_Boot_解析.md) | **深入版**（上篇姊妹篇，講「憑什麼信任」）：簽章 vs 加密、Boot ROM 與 eFuse 兩個錨點、TBBR 的 X.509 憑證鏈與金鑰隔離、AVB 2.0 與 rollback index、boot state 四色、攻擊面（glitching／TOCTOU／EDL／checkm8）、導入 checklist |
| [Android Verified Boot (AVB) 深入解析](../Android-Verified-Boot-AVB.md) | **深入版**（把上面 Secure Boot 提到的 AVB 展開）：硬體信任根 → `vbmeta` 樞紐（hash／hashtree／chain partition／kernel cmdline descriptor）→ dm-verity 區塊級執行期驗證 → rollback index 防降級 → GREEN／YELLOW／ORANGE／RED 四狀態與 Keystore attestation；含刷機實務（`--disable-verity`／`--disable-verification`、`avb_custom_key` 自簽走 YELLOW、`avbtool info_image`、重新上鎖變磚的坑） |
| [把 ABL 拆開看：AVB 驗證在真機上到底怎麼跑](../abl-avb-reversing.md) | **上篇的實作對照版**：把 Qualcomm 手機的 ABL（UEFI application）從 `abl.img` 剝殼成 PE32+ 丟進 Ghidra，用字串（`androidboot.verifiedbootstate=`、`AVB0` magic、`avb_slot_verify.c`）當錨點定位 AVB；再逐步走 `avb_slot_verify()` → vbmeta header 解析 → SHA + RSA 驗簽 → descriptor（hash／hashtree／chain／cmdline）→ rollback index → 綠黃橙紅四色 → 組 kernel cmdline。核心結論：libavb 是通用密碼學骨架，**真正決定安不安全的是廠商在 `AvbOps` 回呼裡有沒有偷工**（金鑰比對、rollback 接 RPMB、鎖狀態）。附逆向常踩的坑 |
| [一支手機從開機到連上網，中間跨過了幾道信任邊界](../mobile-trust-boundaries.md) | **橫向總覽**（純公開規格：TF-A／AVB／GlobalPlatform／PSA／3GPP）：把整支手機當成一堆彼此不完全信任的處理器來看。三部分——(1) 開機信任鏈：BootROM 為何不可變、efuse 存公鑰雜湊、簽章 ≠ 加密、anti-rollback 的 efuse 代價、AVB/dm-verity 與四色 boot state；(2) **AP 之外的 modem**：協定處理器／基頻 DSP／RF 三塊分工，為何被 LTE 的 1 ms subframe 與約 3 ms HARQ 處理預算逼成硬性即時的獨立子系統，以及它「輸入來自空氣、攻擊面是數千頁 3GPP 規格、傳統上權限很高」三性質疊加後為何需要 IOMMU/SMMU 把爆炸半徑限制住；(3) 從開發到量產：PSA 生命週期狀態、「有支援 ≠ 有生效」、**驗證「攻擊失敗」而不是「機制存在」**的強／弱驗證對照表，與五類跨廠商反覆出現的實作缺陷（驗證失敗仍繼續、只驗 header、先載入再驗證的 TOCTOU、信任鏈斷點、回退路徑不驗證） |
| [高通與聯發科 Android 開機流程深度解析](../qualcomm-vs-mediatek-android-boot-flow.md) | **兩家 BSP 的橫向對照**（純公開文件：Qualcomm Linux Boot Guide、MediaTek IoT Yocto、TF-A、AOSP）：先用 ARM 的 BL 分層當共同語言建一張對照表（PBL/BootROM、XBL_Loader/Preloader、TZ/ATF BL31、QTEE/OP-TEE、Gunyah/GenieZone、ABL/LK），再逐家拆開——高通這邊 XBL 三塊分工、AOP 這顆常駐小核沒起來會讓 kernel 一堆 probe 失敗、ABL 是 UEFI application、以及 **GBL 讓 BL33 正在變成兩段式**；聯發科這邊 Preloader 跑在 SRAM、直接用上游 ATF BL31、LK 不走 UEFI。核心是**七項差異**：UEFI vs LK 的標準化／輕量化取捨、DRAM init 落在哪一階段（DDR training vs EMI calibration，決定你該挖哪份 log）、映像格式與簽章、協處理器載入（PIL/remoteproc vs 分散載入）、DTBO 匹配鍵、原廠下載工具鏈不通用、除錯基礎設施（ramdump vs AEE）。附**「卡在哪一段該看哪裡」對照表**與跨平台移植的痛點清單（最容易被低估的是產線流程） |
| [MTK Preloader Combo Header 與 OTA](../mtk-preloader-combo-header-ota.md) | MTK boot chain（BROM → Preloader → LK）中 preloader 住在 eMMC boot0/UFS boot LU；device header 三型態（`EMMC_BOOT`／`UFS_BOOT`／`COMBO_BOOT`）與 device header → BRLYT → GFH 三層結構，以及怎麼接上 Google A/B OTA（`update_engine` byte-level 寫入故 image 需自帶 header、by-name symlink、header 型態不一致導致 source hash mismatch 的故障排查）。各節標註公開來源 vs 推論 |
| [MTK Boot 深入筆記:Preloader/DRAM Init 與 LK/AVB](../mtk-boot-deep-dive.md) | 兩部分。**Part 1（多為社群／推論）**：Preloader 作為 BL2 跑在幾百 KB SRAM 的處境、通用 BL2 的平台初始化職責清單、DRAM calibration 在做什麼（讀 MR5/MR6/MR8 做 discovery → ZQ / CA training / write leveling / DQS gating / RX·TX eye / DATLAT）、**Full-K vs Fast-K**（改了 code 沒反應？先確認是不是吃到 flash 裡的舊 calibration blob）、window 寬度即 margin 的判讀與 shmoo。附**真正開源的對照組**：coreboot 裡 MediaTek 官方貢獻的 `dramc_pi_calibration_api.c`（MT8173/8183/8186）。**Part 2（規範等級）**：eFuse → Preloader → LK 的驗證鏈、AVB 2.0 三種 descriptor、rollback index 與 RPMB 防竄改儲存、四色 boot state 如何影響 KeyMint attestation 與 Play Integrity、A/B slot 的 `priority`/`tries_remaining`/`successful`、unlock 流程與強制 wipe。全文以 [規範]／[社群]／[推論] 標記依據強度 |

---

## 三、建置：AOSP 平台與 App

| 文章 | 內容 |
|---|---|
| [Pixel 8 AOSP 完整工作流程](../aosp_pixel_full_workflow.md) | **主線教學**：build ID ↔ AOSP tag ↔ vendor driver 三者對齊 → repo sync → vendor blob → lunch/m → fastboot flashall，含常見錯誤與救磚 |
| [Pixel 8 AOSP Full Workflow (EN)](../aosp_pixel_full_workflow_EN.md) | 上篇的英文版 |
| [Android Build Project](../android_build_project.md) | 環境套件安裝、repo init/sync、Cuttlefish 虛擬機建置、詞彙表（ACK、GKI、VNDK） |
| [AOSP Codebase](../aosp_codebase.md) | `repo` 與 manifest 的關係：`.repo/` 目錄結構、`default.xml` 的 `revision`／`remote`／`sync-j` 與個別 `<project>` 可覆蓋版本；**`repo manifest -r` 把浮動分支展開成固定 SHA**（重現 build 的唯一可靠做法）；`GLOBAL-PREUPLOAD.cfg` 的 preupload hook；`repo sync` 選項表；用 `local_manifests` 加自己的 repo 而不改上游 |
| [Android Build Number 解析](../Android_build_number.md) | `BP4A.251205.006` 各欄位含義（代號／分支／日期／patch） |
| [搞懂三種 Build Variant：user／userdebug／eng](../android-build-variants.md) | 三者的定位與底層差異：`ro.secure`／`ro.debuggable` 兩個屬性怎麼決定能不能 `adb root`、模組安裝範圍（eng 全裝 vs user 只裝 product 要求）、dexpreopt 最佳化開關與效能落差；附完整對照表與「重現使用者問題／量效能／QA 一律用 `userdebug` 而非 `eng`」的實務原則 |
| [Android Product Flavor 完整教學](../android-product-flavor-完整教學.md) | **App 層（Gradle）**：一份程式碼產出多個 App——build type／product flavor／build variant 三者關係、Groovy 與 Kotlin DSL 兩種寫法、flavor 能客製什麼（`applicationId`／`BuildConfig`／manifest placeholder／source set 資源與程式碼覆寫）、flavor dimensions 多維度組合、免費版 vs 付費版實戰、依 flavor 加依賴，以及常見陷阱 |

---

## 四、Pixel 硬體與刷機

| 文章 | 內容 |
|---|---|
| [Pixel 硬體代號](../pixel_hardware.md) | **SoC 代號 vs 裝置代號**的一對多關係（`zuma` → `shiba`/`husky`/`akita`）：kernel 側用 SoC 代號（`android-gs-zuma-*`，gs = Google Silicon），AOSP 側用裝置代號（`lunch aosp_shiba-userdebug`）；附 `user`/`userdebug`/`eng` variant 差異與 `getprop` 查證方式 |
| [Pixel Study](../pixel_study.md) | 實作全紀錄：ADB 安裝、開發者模式、repo sync、lunch、flashall log、anti-rollback 錯誤、`flash-all.sh` 救磚 |
| [Pixel Fastboot Deep Dive](../pixel_fastboot_deepdive.md) | `fastboot flashall -w` 完整輸出逐行紀錄 |
| [Pixel Image 來源對照](../pixel_img.md) | 哪些 image 是 `m` build 出來的、哪些是 vendor blob、哪些是 Google 原廠 binary |
| [Pixel Flash Debug](../pixel_flash_debug.md) | `Failed to find AVB_MAGIC at offset: 0` 根因分析——不該加 `--disable-verity`，含成功 flash 紀錄 |
| [用 Android Flash Tool 刷不同版本](../pixel_flash_another_version.md) | 網頁版 flash.android.com 操作重點 |
| [Pixel Driver](../pixel_driver.md) | Root 權限與 kernel module 載入前置作業 |
| [Pixel 8 Kernel Driver 開發實戰](../pixel8-kernel-tutorial.md) | **⚠ 撰寫中**：在 shiba 上從零寫 kernel module 並實機驗證。前置檢查（`CONFIG_MODULE_SIG_FORCE` 沒開 → 未簽章 module 照樣載入，只是 taint 成 `(OE)`）、只 sync GKI kernel source、用 Kleaf 的 `ddk_module` 而非手寫 Kbuild、vermagic 版本不完全相符為何仍可載入 |
| [從 hello world 到 Binder：一支 Android driver 的完整歷程](../pixel8-driver-course.md) | **⚠ 撰寫中**：上篇的「歷程版」——同一支 driver 怎麼一步步從 hello world 長出 sysfs、ioctl、dma-buf 到 Binder。開頭用兩個指令證明你不需要刷機、也不需要整棵 Pixel tree |
| [Pixel 8 軟體整合層 Bringup](../pixel8-bringup.md) | **⚠ 撰寫中**：`.ko` 以外的那一整套——分割區與 A/B、ramdisk、cmdline、dtbo、device tree、vendor HAL、image 手術。開頭釐清**兩種 bringup**：傳統板級（電源時序／DDR training／pinmux，Pixel 8 做不到，改用 BeagleBone 補）vs 軟體整合層（DT、probe 路徑、HAL／SELinux／VINTF） |
| [送出 kernel patch：實際跑過一遍的步驟](../upstream-runbook.md) | **⚠ 撰寫中**：投 ACK / Gerrit 的操作手冊。重點是**選題材的三道關卡**（這段程式碼在 mainline 存不存在？mainline 現在還錯不錯？`android-mainline` 現在還錯不錯？），`ANDROID:` 開頭的 commit 只能送 Gerrit 不能送 LKML，以及 `--depth=1` fetch `android-mainline` 來查證 |

---

## 五、Root 與權限

| 文章 | 內容 |
|---|---|
| [Pixel Root](../pixel_root.md) | Magisk vs KernelSU 對照表，並解釋**為何是不同的 image**（Android 13 後 generic ramdisk 拆成 `init_boot.img`，Magisk 換 `init` 所以改它；KernelSU 把 su 編進 kernel 所以改 `boot.img`）；解鎖 bootloader 前置、兩者的實際刷入步驟、以及 Play Integrity／OTA 覆蓋／刷錯版本變磚等注意事項 |
| [Pixel 無法 adb root](../pixel_can_not_run_as_root.md) | `adbd cannot run as root in production builds` 的解法：Magisk patch init_boot，含 `/sys/class/` 節點列表 |
| [Dirty SEPolicy 偵測：一種讓所有 Root 方案都現形的新向量](../dirty-sepolicy-detection.md) | 2026 年起銀行／金流 App（Shopee、BRImo、Birbank 等）採用的偵測手法：直接讀任何 App 都能開的 `/sys/fs/selinux/policy`，解析核心中**正在生效**的 binary policy，比對原廠指紋找污染痕跡（可疑 type／permissive domain／`untrusted_app` 異常權限）。之所以打擊面全覆蓋（Magisk／KernelSU 全分支／APatch），是因為**注入 sepolicy 規則是 root 的功能性必要條件，無法迴避**，傳統藏檔案／改包名的表層隱藏完全失效。反制思路是在核心 `security_read_policy` 路徑上 hook，對非特權 App 回傳乾淨副本（KernelSU 的 Hide SELinux modifications／APatch `selinux_hook` KPM）；附用 `strace` 自行驗證某 App 是否使用此向量的方法 |

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
| [DMA-BUF Heaps 完整導覽](../dma-heap-guide.md) | 從 PMEM 群雄割據 → ION 十年統治 → dma-heap 正式接班的歷史脈絡，解釋為何一塊 camera → ISP → GPU → encoder → display 的 buffer 需要專門的配置器（實體連續、對齊、cacheability、TZ 保護記憶體各方需求衝突）。含 heap/exporter/importer 元件拆解、`dma_buf_ops` 與 `dma_heap_add()`、allocate → attach → map → fence 的核心 flow、ION → dma-heap 遷移對照（每個 heap 一個 `/dev/dma_heap/*` node，終於能用檔案權限與 SELinux 分權），以及 `dmabuf_dump`／debugfs 觀測與常見踩雷 |
| [在沒有 Play 商店的 Pixel 8 上，把 CPU、GPU、NPU 都量出來](../article-zh.md) | 純 AOSP userdebug（無 GMS，跑不了 Geekbench／AITuTu）上自己量三個運算單元。核心是**五個會給出「合理但錯誤」數字的陷阱**：simpleperf 少了 `task-clock` 會用 wall-clock 當分母把時脈稀釋成 1/4、超過 3 個硬體事件觸發 counter multiplexing 但不補償（2.9 → 1.36 GHz）、通用事件別名（`branch-instructions`）在 X3 上無聲失效、Mali 預設 governor 整段跑在 150 MHz 地板讓 GPU 看起來跟 CPU 一樣快（鎖頻後 3.1 倍）、NNAPI 對 float32 模型**默默退回 CPU** 卻照印 delegate created。對應三種自帶證據：三叢集分支總數須收斂、`time_in_state` 反推有效頻率、EdgeTPU 的硬體 `inference_count` 差值。附 NNAPI deprecated 之後 Tensor G3 無替代路徑的實測（`libedgetpu_client.google.so` 無 C ABI，external delegate segfault） |
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
| [從 vendor 分割區看 Project Treble](../project-treble-移植開發者筆記.md) | **移植者視角的完整版**：從「一台陌生機器該問的五個問題」（`ro.treble.enabled`／`first_api_level`／`ro.vndk.version` vs `ro.vendor.api_level`／super／slot_suffix）出發，回頭講 Treble 的成因（Stagefright 與那條走不完的更新鏈）、分割區職責界線（system／vendor／odm／product／system_ext、動態分割區 super、A/B vs A-only）、Vendor Interface 的組成（VINTF manifest × compatibility matrix 的交叉比對、passthrough／binderized／SP-HAL、HIDL→AIDL 遷移、**VNDK 在 Android 15 的退場與 Vendor API level**、SELinux policy 拆分、VTS/CTS-on-GSI）；後半是 GSI 實戰（選映像、關 AVB、fastbootd 刷入、DSU 試跑）與開不了機的除錯路徑對照表，末尾談廠商魔改造成的「理論相容 ≠ 實際可用」落差、GKI/KMI，以及九年後的成果與瓶頸移位 |
| [你的手機在 Android 發表前就準備好了：聊聊 PDK 與 aosp.xml](../android-pdk-aosp-xml.md) | **入門向補充**：為何新版 Android 一發表就有手機跟著升級——**PDK（Platform Development Kit）**讓 Google 在公開前先把平台交給 SoC 廠與品牌廠，把整條供應鏈的時間軸往前推（與 Treble／GKI 是「流程上的提前」vs「架構上的鬆綁」，在解同一個問題）。後半解釋 `repo` 與 manifest：`aosp.xml` 的 `<remote>`／`<default>`／`<project>` 結構、實務上 AOSP／晶片廠 BSP／品牌廠客製三份 manifest 疊起來才是完整的樹（權責分離），以及**`revision` 是刻意釘死的**——整棵樹是一個驗證過的組合，偷偷把 AOSP 那層往前推會 build 不過或跑起來行為詭異 |
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

## 十二、SoC Android 專案規劃範本（4 篇）

> 一組**可直接套用的空白範本**：被指派規劃一顆新 SoC 的 Android 軟體專案時，從「還沒有任何數字」到「交得出可被質詢的規劃書」。與第十一節互補——那邊是 BSP 的日常操作，這邊是專案立項階段的方法與表單。所有數字皆為業界常見區間，不含任何專案實況。
>
> 讀法：先讀方法論理解判斷邏輯 → 用工作表把數字算出來 → 填規劃書 → 抽成一頁摘要給主管。

| 文章 | 內容 |
|---|---|
| [SoC Android 軟體專案規劃方法論](../soc-android-planning-methodology.md) | **入口**：Treble 兩域（Vendor / System）的責任切分表當骨架；第 1 週不要寫文件，先問完 12 個關鍵輸入（矽晶時程／IP delta／Google 面／客戶與內部），每題都標「問誰」與「拿不到時的最壞假設」；時程用**反推法**（M0 kick-off → M10 MP 的 11 個里程碑鏈 + 全新架構 vs 衍生型的區間表），反推後發現起跑日已過就是最該講的那句話；人力用**雙軸模型**（IP 軸 + 版本軸）並用類比／由下而上／由上而下三法交叉驗證；末尾是常見誤區與公開事實附錄（版本代號、GKI 對應、N+3 規則、Q2/Q4 source drop） |
| [SoC Android 軟體專案規劃工作表](../soc-android-planning-worksheet.md) | **試算主體**：12 題資訊收集清單（含最壞假設欄）、Vendor API Level 的 **N+3 相容矩陣**與選項評估、跨代差異 14 項檢查清單（GKI 世代跳躍／HIDL→AIDL／16 KB page size／VSR 累積／xTS 測項增加…）、里程碑反推表與缺口分析、**雙軸 WBS**（26 個模組逐項填 IP 軸狀態 × 版本軸係數 × 前一代人月）、人力配置表（人月／季）、11 項風險登記 |
| [SoC Android 軟體專案規劃書範本](../soc-android-planning-proposal-template.md) | **正式文件骨架**（12 章）：一頁摘要 → 背景與目標 → 範圍定義（含 Out of Scope）→ 技術基準（每格都得有答案，填「待確認」就要標低信心）→ IP Delta Map → 里程碑 → 工作分解與人力 → 品質與合規（xTS 六套的責任與達成里程碑）→ 風險 → 交付物 → 溝通治理 → **假設與待決事項**（這章保護你） |
| [SoC Android 專案一頁摘要範本](../soc-android-planning-onepager-template.md) | **給主管的一頁**：時程錨點與反推缺口 → 選新世代 vendor API level 的三個直接後果（雙軸估算／合規基準隨該版定版故 EAP 是 Go/No-Go 前提／承諾多代 OS 升級的長期維運）→ 要主管拍板的事 → 要立即查證的三件事 → 下一步 |

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
