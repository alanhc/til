---
title: Embedded / 韌體 / 硬體 文章索引
sidebar_label: Embedded 系列索引
sidebar_position: 6
---

# Embedded / 韌體 / 硬體 文章索引

本頁整理知識庫中所有嵌入式系統、韌體與硬體相關筆記，依主題分類：從開機流程、Bootloader、建置系統，到韌體工程實踐與底層硬體知識。

---

## 一、總覽與基礎

| 文章 | 內容 |
|---|---|
| [嵌入式系統背景知識](../embedded.md) | 嵌入式 Linux 四大組成：Bootloader → Kernel → rootfs → Driver，含 Device Tree、cross-compile、`defconfig`、BusyBox/systemd 等關鍵字 |
| [State Machine](../Embedded/state_machine.md) | 狀態機在嵌入式的用途與實作四步驟（定義狀態／事件／轉換規則／實作），附一支 C 寫的 LED 控制器範例（OFF／ON／BLINKING 三態） |
| [Tegra BSP 學習地圖](../tegra-bsp-learning-map.md) | 從 Yocto／開機鏈 → driver + device tree → Jetson Orin 實作 → 深度補強的四階段路線圖。核心是一張**開機鏈對照表**：把 STM32MP1 的 TF-A BL2／BL31／OP-TEE／U-Boot 逐格對到 Jetson Orin 的 MB1-MB2／BL31／OP-TEE／UEFI(EDK2)，建構與燒錄則是 Yocto vs L4T 工具鏈、`flash.sh`／`l4t_initrd_flash.sh`。附每階段的完成條件與練習（QEMU out-of-tree platform driver、I2C 感測器 driver + `make dt_binding_check`、meta-tegra 自建 layer）|

---

## 二、開機流程與 Bootloader

| 文章 | 內容 |
|---|---|
| [開機流程（泛用概念）](../booting/boot.md) | 跨架構的共通骨架：Reset vector → 韌體／初階 bootloader → Bootloader → Kernel，解釋多階段開機為何存在、chain of trust 與 root of trust |
| [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) | 從 Reset Vector `0xFFFFFFF0` 到 login：BIOS/POST/MBR 與 UEFI（SEC/PEI/DXE/BDS、ESP、Secure Boot）兩條路徑對照、GRUB 各載入階段、kernel 解壓縮與模式切換、initramfs、systemd target 順序、MBR vs GPT，含 `journalctl`／`systemd-analyze` 除錯與常見開機失敗原因 |
| [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) | ZSBL → FSBL → OpenSBI → U-Boot SPL/Proper → Kernel：M/S/U-mode 特權層級與 CSR、SBI 介面與呼叫慣例、OpenSBI 三種韌體映像（FW_JUMP/FW_PAYLOAD/FW_DYNAMIC）、DTB 傳遞鏈、PLIC/CLINT 中斷架構，並比較 QEMU virt、HiFive Unmatched、VisionFive 2、Milk-V Pioneer 各平台 |
| [Das U-Boot](../Embedded/uboot.md) | U-Boot 實用速查：`printenv`/`setenv`/`saveenv` 環境變數、`bootcmd` 與 `bootargs` 差異、用 `tftp`／`fatload` 載入 kernel 與 dtb 後 `booti` 啟動 |
| [ARMv8 開機鏈三部曲（三）：U-Boot](../u-boot.md) | 上一篇是指令速查，這篇是**原始碼層級的深入版**：U-Boot 作為 BL33 的角色、各 phase 切分、relocation、Driver Model、Standard Boot 與交棒 Linux 的協定。列在第三節與 TF-A／OP-TEE 兩篇同系列 |
| [MTK Boot 深入筆記:Preloader/DRAM Init 與 LK/AVB](../mtk-boot-deep-dive.md) | Part 1 是**這一節裡最貼近實機 bring-up 的一篇**：Preloader 作為 MTK 的 BL2 只能跑在幾百 KB SRAM、PMIC 上電與 DRAM 初始化這兩步佔了 bring-up 絕大多數問題；DRAM calibration 逐項拆解（MR discovery → ZQ → CA training → write leveling → DQS gating → RX/TX eye → DATLAT），以及 **Full-K vs Fast-K** 這個「改了 code 卻沒反應」的經典坑。判讀重點是 **window 寬度（margin）而非 pass/fail**，配合 shmoo 與 golden board 對照。附 coreboot 裡 MediaTek 官方開源的 DRAM calibration 程式碼當對照組。Part 2 轉到 LK 與 AVB，Android 視角見 [Android 系列索引](android_index.md) |
| [在 UEFI 階段用 gdb 除錯：從 QEMU 到 DXE dispatch 單步](../booting/uefi-gdb-dxe-debugging.md) | **把「SEC → PEI → DXE → BDS」那張架構圖變成能下中斷點的實作**，環境是 QEMU q35 + OVMF DEBUG build。前半是 build 會撞到的兩個坑：`GCC5` toolchain tag 已從 edk2 移除（除錯要選 `GCCNOLTO`，LTO 會把函式邊界打散讓 source-level stepping 對不上），以及 GCC 13 的 `-Werror=maybe-uninitialized` 要靠 DSC `[BuildOptions]` 而非 `tools_def.txt` 才修得掉。中段是讓 driver 停下來等你的土方法（entry point 放 `volatile` 旗標的等待迴圈，`-s` 不加 `-S`）與怎麼從 serial log 的 image base 自己算 section 位址（**不要背 `base + 0x240`**）。**核心是第四節**：`add-symbol-file <file> <addr>` 只重定位 `.text`，`.data` 沒搬，於是 backtrace 完全正確、全域變數卻讀出垃圾——症狀特別會騙人，要寫成 `-s .data <addr>` 才對。最後掛上 `DxeCore` 的 symbol 看見完整七層 dispatch 鏈，並在 `CoreDispatcher` 下中斷點觀察 Depex 分輪載入與 `mScheduledQueue` |
| [GRUB 修復](../grub.md) | 灌 Windows 後 GRUB 被覆蓋、無法進 Ubuntu 的實際排除紀錄：`sudo os-prober` 找出 Windows 分割區 → `sudo update-grub` 重建選單 |
| [從按下電源到 Linux：PC、伺服器、Android、ARM Server 開機流程由淺入深](../boot-flow-intro.md) | **這一節的入口總覽**，由淺入深五層：開機在做什麼 → PC 的 UEFI 五階段與「DXE 為何這麼肥」→ LinuxBoot／u-root 想砍掉 DXE → Android／嵌入式本來就沒有 DXE → ARM server 為何走回 PC 那一套。核心論點是**決定開機流程的是平台型態（開放通用 vs 垂直整合），不是 CPU 架構**；附 PC/UEFI 與 Android 各階段的對照表，以及「伺服器與手機都為了安全但出發點相反」（前者要換成看得見的程式碼，後者要從 BootROM 鎖死） |
| [LinuxBoot：用 Linux 取代韌體的開機流程](../linuxboot.md) | **概論**：LinuxBoot 是什麼、2017 年由 Google／Meta 等發起、源頭是 Ron Minnich 1999 年的 LinuxBIOS（後來變成 coreboot）；它只取代 UEFI「平台初始化完成之後」那一段，SEC/PEI 仍保留。含核心元件、採用現況（Google 的 NERF、OCP Open System Firmware）與和 OpenBMC 的關係 |
| [LinuxBoot 與 u-root：用 Linux 取代 UEFI DXE 的伺服器韌體架構](../linuxboot-u-root.md) | **深入版**：逐段對照 SEC/PEI/DXE/BDS 的職責、兩種實作方式（coreboot + LinuxBoot payload vs 保留廠商 SEC/PEI）、u-root 用 Go 寫 initramfs 的設計取捨與開機相關指令、`kexec` 怎麼繞過韌體直接換 kernel、為什麼只在資料中心流行、**為什麼 Android 用不到它**，以及和 OpenBMC 的分工 |
| [kexec：讓 Linux kernel 自己當 bootloader](../kexec.md) | **LinuxBoot 最後一步的機制本身**：`kexec_load()` 與 `kexec_file_load()` 的差別（後者讓 kernel 自己解析 image，才能做簽章驗證）、載入與切換兩段流程、purgatory 的角色、kdump 怎麼靠預留記憶體保住 panic 現場、lockdown 與 `kexec_load_disabled` 的限制，以及硬體不會被韌體重置帶來的陷阱 |
| [u-root 與 LinuxBoot：20 秒伺服器開機是怎麼做到的](../u-root-linuxboot-20s-boot.md) | **追一個常被誤傳的數字**：「20 秒」出自 Ron Minnich 2017 年在 coreboot mailing list 回報的 OCP Winterfell 開機實驗，量的是開機到 kexec，不是 build。拆解 dhclient → wget → gpgv → kexec 的流程，並逐項標出哪些加速原因有一手來源、哪些只是依架構推論；也整理 NERF／LinuxBoot／u-root／Heads 的命名沿革與 u-root 從 source mode 到 `gbb` mode 的構建方式。和上面兩篇 LinuxBoot 的差別：那兩篇講架構，這篇講一個具體數字從哪來 |
| [Arm SystemReady：讓 Arm 平台做到「裝了就能開機」](../arm-systemready.md) | Arm 對抗生態碎片化（「一板一 image」）的標準與認證計畫：從 2018 ServerReady → 2020 SystemReady 四個 band → **2024 年底重整成兩個 band**（SystemReady Band 走 UEFI+ACPI、Devicetree Band 走 UEFI+DT，LS/LinuxBoot band 退場）；底層規範（BSA／BBR 等）認證的是什麼、ACS 測試怎麼跑、對產業的意義與現實面的限制 |
| [Android Generic Bootloader（GBL）介紹](../android-gbl-intro.md) | **同一條 UEFI 線在 Android 上的落點**：Google 用 Rust 寫的 UEFI application 取代各家 vendor bootloader 的 Android 專屬邏輯，理由之一正是「與 Arm SystemReady 方向一致」。想看 UEFI protocol 當成廠商擴充點怎麼用，這篇是具體案例。Android 視角見 [Android 系列索引](android_index.md) |

---

## 三、ARM Trusted Firmware 與 Secure World

> 這三篇同時屬於 Android 分類。Android 視角的**深入版**請見 [ARM Trusted Firmware (TF-A) 解析](../ARM_Trusted_Firmware_解析.md) 與 [Secure Boot 解析](../Secure_Boot_解析.md)，完整清單見 [Android 系列索引](android_index.md)。

| 文章 | 內容 |
|---|---|
| [ARM Trusted Firmware (ATF)](../atf.md) | **名詞與對照表為主**：BL1~BL3-3 階段對應表（含 EL 層級）、EL0~EL3 權限分層表、TrustZone 的 Secure/Normal World 與 OP-TEE 元件樹、TrustZone vs 機密運算比較、ARMv7-A/v8-A/v9-A 安全模型演進表，以及 TrustZone → CCA 的 mermaid 時間軸 |
| [ARM Trusted Firmware（TF-A）](../booting/atf.md) | **散文式說明為主**（與上篇不同檔案）：逐段講 BL1（AP Trusted ROM）、BL2（Trusted Boot Firmware）、BL31（EL3 Runtime Firmware 常駐 Secure Monitor 並實作 PSCI）、BL32（OP-TEE）、BL33（U-Boot/UEFI）各自職責，附 Arm Juno 官方文件等參考連結 |
| [一支手機從開機到連上網，中間跨過了幾道信任邊界](../mobile-trust-boundaries.md) | 把 TF-A 的分階段模型放回一整支裝置的脈絡：BootROM 為何是不可變的信任根、efuse 存的是公鑰雜湊而非公鑰、簽章 ≠ 加密、anti-rollback 的單向代價；接著跨出 AP 談 **modem 這個獨立信任域**（協定處理器／基頻 DSP／RF 的分工、1 ms subframe 的硬性即時要求、IOMMU/SMMU 為何是 CP 值最高的緩解措施）；最後談整合階段：PSA 生命週期狀態、「有支援 ≠ 有生效」、**驗證「攻擊失敗」而非「機制存在」**，以及五類典型實作缺陷 |
| [ARM Trusted Firmware 元件](../arm_trust_firmware.md) | 速記卡：What／Why／When（ARMv8 引入 TrustZone + EL3、2013-14 首版、2015 成標準）、主要元件列表（BL 各階段、TF-A、PSCI、SMC Dispatcher、SiP service、憑證鏈／RoT）與待補的名詞清單 |
| [ARMv8 開機鏈三部曲（一）：Trusted Firmware-A](../tf-a.md) | **對照 upstream 原始碼的深入版**：BL1/BL2/BL31/BL32/BL33 分工、FIP 打包與 `fiptool`、以 ROTPK 為根的 TBB/TBBR 憑證鏈；BL31 常駐 EL3 後怎麼依 SMCCC 的 Function ID 把 SMC 分派給 PSCI、SiP service 與 SPD（`opteed`）；Linux 的 CPU hotplug／suspend／reboot 如何經 DT 的 `psci` node 走到 BL31；新架構 SPMD + SPMC（FF-A）如何取代「一個 Trusted OS 配一個專用 SPD」。附 QEMU v8 觀察開機 log 與面試 Q&A |
| [ARMv8 開機鏈三部曲（二）：OP-TEE](../optee.md) | BL32 視角：`optee_os`（S-EL1 核心 + S-EL0 TA）、Linux TEE subsystem／OP-TEE driver、`libteec` 與 `tee-supplicant` 四塊的分工；`TEEC_InvokeCommand()` 一路到 TA `TA_InvokeCommandEntryPoint()` 的完整呼叫鏈，以及反方向 RPC（secure world 請 normal world 幫忙配記憶體、存檔、載入 TA）；pseudo TA vs user TA、foreign interrupt 處理、TA crash 用 `symbolize.py` 解 abort dump。附 QEMU 跑 `xtest`／`hello_world` |
| [ARMv8 開機鏈三部曲（三）：U-Boot](../u-boot.md) | BL33 視角：TPL/VPL/SPL/U-Boot proper 各 phase（Rockchip、Allwinner 的 SPL 直接當 BL2 並用 `CONFIG_SPL_ATF` 載 BL31）、`board_init_f` → relocation → `board_init_r` 骨幹與 `gd`、Driver Model（uclass/udevice/`U_BOOT_DRIVER`）、從 `distro_bootcmd` 演進到 Standard Boot（bootdev/bootmeth/bootflow）、FIT verified boot；交棒 arm64 Linux 的協定（x0 = DTB、x1~x3 = 0、MMU off）與交棒前的 DT fixup；AVB／A/B／fastboot 整合與「量產 Android 手機多半不用 U-Boot」的現實 |

---

## 四、建置系統

| 文章 | 內容 |
|---|---|
| [Yocto Project](../Embedded/yocto.md) | Yocto 是建構框架而非發行版：BitBake 引擎、Recipe（`.bb`／`SRC_URI`／`DEPENDS`）、Layer（`meta-*`／`bblayers.conf`）、`MACHINE`/`DISTRO`，以及 `source oe-init-build-env` → `bitbake core-image-minimal` 的基本流程與產物位置 |
| [Buildroot](../Embedded/buildroot.md) | `make menuconfig` 與 `make uboot-menuconfig` 兩個設定入口，附 mermaid 圖說明 Buildroot 統管 kernel 與 U-Boot、kernel 底下再掛 Driver 與 Device Tree 的關係 |

---

## 五、韌體工程實踐

| 文章 | 內容 |
|---|---|
| [Bring-up：新硬體從「不會動」到「能量產」](../bringup-article.md) | 從一顆回廠的工程樣品到能量產的完整戰役，拆成**晶片（silicon）／板級（board）／軟體韌體**三層 bring-up：上電前阻抗檢查、電源/時脈/reset sanity、建 JTAG 通道、逐一驗 IP（DDR training、SerDes 眼圖、PVT corner shmoo）、first UART print → DDR init → kernel to shell 的軟體推進、分層隔離的 debug 方法論、常見坑（strap pin、pinmux、clock gating、cache coherency）、re-spin 決策的經濟學，以及「好的 bring-up 從 tape-out 前就開始」 |
| [Firmware Image 管理](../firmware_image_management.md) | 把「正式 vs 非正式 image」對應到五個軟體工程概念：Release Channels（Chrome 的 Canary/Dev/Beta/Stable）、Build Promotion（build once, promote many）、Nightly Build + Trunk-Based Development、Shift-Left Testing、Release Candidate 與 release branch 凍結 |
| [Firmware Testing](../firmware_testing.md) | 目前僅是連結收藏：FOSDEM 2022 的 LAVA/openQA 議程、Linaro validation 平台，以及韌體團隊 CI/CD、OpenWrt CI/CD 兩篇文章 |

---

## 六、硬體與晶片

| 文章 | 內容 |
|---|---|
| [半導體](../半導體/半導體.md) | 半導體基礎：N/P 型摻雜、PN 接面、MOSFET、CMOS；產業鏈分工（fabless／foundry／OSAT／IDM）與代表廠商；光罩、微影、蝕刻、沉積、離子佈植等製程與製程節點意義 |
| [晶片](../晶片.md) | 影片筆記：Apple M5 與 NVIDIA 路線的比較（「Copying Nvidia?」），含三張截圖 |
| [Chip](../chip.md) | 佔位頁：只有一條**私人 ChatGPT 對話連結**（外人無法開啟），尚無整理內容 |
| [NVIDIA GPU](../gpu_nvidia.md) | Linux 上確認 NVIDIA 驅動狀態的指令與實測輸出：`lsmod \| grep nvidia` 看 `nvidia`/`nvidia_uvm`/`nvidia_drm`/`nvidia_modeset` 模組相依、`nvidia-smi` 查 RTX 5070 Ti 的驅動版本、CUDA 版本、溫度功耗與佔用 VRAM 的 process |
| [VAD 與 Silero VAD 的晶片效能](../vad-silero-chip-performance.md) | VAD 是語音 pipeline 最前面的守門員（能量閾值 → WebRTC VAD 的 GMM → 小型 NN 的演進）；**Silero VAD** 規格（~1–2 MB、16 kHz 每 512 samples、STFT → CNN → 有狀態 LSTM、ONNX）；為什麼它是 always-on workload（每天約 270 萬次推論），關鍵指標是每次推論能耗、跑在哪個 core、能否讓 AP 睡覺、SRAM 佔用而非 TOPS；LSTM／batch=1／高頻 invoke 對 NPU 不友善之處；晶片廠為何在意與自行量測的方法表 |
| [Raspberry Pi](<../raspberry pi.md>) | 單板電腦筆記：用 Raspberry Pi Imager 燒錄 OS 並預先設定 SSH／Wi-Fi／帳號、GPIO 接周邊的應用場景、官方文件與一支影片連結 |

---

## 七、矽後驗證與半導體量產測試

> 兩段相接的故事。前半是 **post-silicon validation（矽後驗證）**——first silicon 從 fab 回來之後，在「跑得飛快但幾乎什麼都看不到」的條件下把 bug 找出來，並用電壓／頻率／溫度掃描決定這顆矽在什麼條件下能用。後半是**量產測試**——把驗證階段學到的東西，變成 CP／FT／SLT 上跑的 pattern 與分級規則。從系統整合／韌體工程師視角看，這整條線決定了拿到手的矽是什麼品質、怎麼分級，以及 MTBF 這類軟體穩定性度量為何落在整合團隊。

| 文章 | 內容 |
|---|---|
| [IC 設計的前段／中段／後段](../BMC/ic-design-flow.md) | **這條鏈的上游**：從 Spec 到 GDSII 的完整數位 IC 流程。前段（架構／微架構／RTL coding／驗證方法學：directed、constrained random、formal、emulation）；中段（Synthesis 與 SDC 約束太鬆/太緊的後果、DFT 的 Scan/MBIST/ATPG/JTAG/compression、LEC 等價性驗證）；後段（Floorplan→Placement→CTS→Routing→Signoff，含 STA/IR Drop/EM/DRC/LVS/Antenna/SI 檢查表）。另談「中段」邊界在各公司浮動、類比 IC 沒有合成步驟、流程實為迴授而非瀑布。**與下方量產測試系列直接相接**：DFT 決定了 ATE 上能測到什麼 |
| [Post-Silicon Validation 入門](../post-silicon-validation-introduction.md) | **tape-out 之後那一整段**：先用一張對照表講清楚 pre-Si 與 post-Si 的根本取捨——模擬什麼都看得到但跑不快，真晶片跑得飛快但只剩 pin 與 debug port，以及為何 state space、模擬深度、類比行為、製程變異、model 本身出錯這五件事讓 pre-Si 不可能做完。接著走完五個階段：階段 0 tape-out 前就要決定的 **DFD（Design-for-Debug）**（trace buffer、trigger、debug bus——**tape-out 後就沒得加**）、階段 1 bring-up 的檢查順序（power → clock/reset → JTAG → BIST → 第一條指令 → 開機）、階段 2 功能驗證（ISA、RIT 對 golden model、compliance、power virus、concurrency）、階段 3 用 shmoo 掃電氣角落、階段 4 debug 與 triage、階段 5 errata／workaround／stepping 決策。末尾是一個逐日推進的 debug case study（6 小時才當一次 → 建立重現性 → 敏感度掃描判定 setup violation → 找到加速條件把 MTTF 壓到 40 分鐘 → 縮測試回 pre-Si 定案 → metal fix 與 errata），與職務所需技能、相關職位分工 |
| [Shmoo 與電氣驗證](../shmoo-and-electrical-validation.md) | **上篇階段 3 的展開**：功能對了不等於能出貨，電氣驗證回答的是「在什麼條件下才不會算錯」。先講 V／F／T 三個旋鈕各自怎麼影響 timing（含 **temperature inversion**——先進製程低電壓下最壞角落可能是低溫而非高溫，這是常見的直覺陷阱），加上製程角落 SS/TT/FF 與 NBTI／HCI 老化。主體是**怎麼讀 shmoo plot**：乾淨斜線 = 正常 critical path；中間破洞 = PLL jitter／LDO 不穩／PDN 共振／lock 範圍邊界；左下角（高壓低頻）壞掉 = hold violation，降頻救不了；邊界毛躁 = 先懷疑環境再懷疑晶片。再談 **Vmin 是一個分布不是一個數字**（要外推到目標良率並疊 aging 與量測 margin，離群值要追），以及 Vmin 通常被 SRAM bitcell 與類比 IP 限制而非邏輯 critical path。最後是測試環境與時間成本（一次 characterization 動輒上百小時，自動化本身就是核心技能）、四個常見陷阱（量到的不是 die 上的電壓、溫度沒穩、測試順序的歷史效應、把環境問題當晶片問題），與資料最終如何變成 datasheet 規格、binning 規則與 DVFS 表 |
| [半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) | **系列總綱**：CP（晶圓）→ FT（封裝後）→ SLT（出貨前）三個 test insertion 加上 ATE（設備）的定位；結構性 vs 功能性兩種測試哲學、「缺陷越晚發現越貴」的十倍法則經濟學、四角色對照表，以及從 chip vendor 看品質過濾／良率歸因／產品分級／閉環回饋四件事 |
| [ATE 是什麼](../what-is-ate.md) | 破除最常見的混淆——ATE 是 CP/FT **共用的設備**，不是一個測試階段。DFT／ATPG／scan chain 的結構性測試原理、fault model 與 coverage、市場格局，以及 ATE 覆蓋率的先天極限（為何仍需要 SLT） |
| [CP 晶圓測試](../what-is-cp-wafer-test.md) | 封裝前用探針卡扎裸 die、產出 wafer map 篩壞品；探針卡的接觸電阻／寄生電感如何限制高頻與大電流測試、CP 能不能省（盲封），以及最容易混淆的 CP vs WAT（測產品 vs 測製程） |
| [FT 最終測試](../what-is-ft-final-test.md) | 封裝後為何要再測一次（封裝製程也引入缺陷）、socket／load board 環境、以及 FT 不只判生死還做 speed binning（Fmax／Vmin 分級，直接決定 SKU 與 DVFS 設定） |
| [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) | 出貨前把晶片放進類產品板開機跑軟體，攔 ATE 抓不到的跨 IP／邊際／軟硬互動缺陷；為何對 chip vendor 重要（DPPM 合約承諾、缺陷逃逸的乘數成本、大客戶把系統品質推回 vendor、閉環回饋），以及 SLT 本質是平台軟體 |
| [DFT（Design for Test）工程實務](../DFT_Design_for_Test_工程實務.md) | **設計端**：把上面「ATE 靠 DFT 才測得到內部」展開成設計方法——為何幾億電晶體只能靠幾百支 pin 觀測、fault model（stuck-at／transition／bridging）、Scan Design 的 shift-in→capture→shift-out 與實務重點、ATPG 覆蓋率指標與 test compression、MBIST／LBIST（LFSR + MISR）、Boundary Scan（JTAG／IEEE 1149.1）TAP 狀態機，以及 DFT 在設計鏈與 chip vendor 組織裡的位置 |
| [DFT Verification 學習筆記](../DFT_Verification_學習筆記.md) | **驗證端**：DFT 的 simulation-based 驗證需要的知識結構——VCS/Verdi 的 RTL/gate-level tracing 與 X-propagation debug、IP／cluster／full chip 三層驗證與收斂指標、SDF back-annotation、把 ATPG pattern 拉回 gate sim 驗證、SoC 基本盤（clock/reset/power rail/IO pad/package）與 DFT 的關係、Tcl/Python 自動化，附自我檢查清單與名詞速查 |
| [MTBF 與系統整合](../mtbf-and-why-si-owns-it.md) | **延伸篇**：前面講「矽」的品質，這篇講「軟體堆疊」的品質怎麼度量。為何 MTBF fail 天生沒 owner、是 build 層級度量、與 CI 同一套肌肉、直接面對客戶，因而落在系統整合（SI）的主場；附 MTBF triage 實務循環 |

---

## 八、Driver 與效能觀測

> 前面幾節講的是「板子怎麼開起來」；這一節講開起來之後——資料怎麼在硬體與 kernel 之間搬，以及效能出問題時該從哪一層看。

| 文章 | 內容 |
|---|---|
| [MediaTek UART APDMA：從 Virtual FIFO 硬體模型讀懂 `mtk-uart-apdma.c`](../mtk-uart-apdma.md) | 對照 upstream `drivers/dma/mediatek/mtk-uart-apdma.c` 與 `8250_mtk.c` 逐段讀：為何高速 UART（BT/GNSS/modem）需要 DMA、**VFF（Virtual FIFO）** 的 ring buffer + 硬體讀寫指標模型、用額外一個 wrap bit 解 full/empty 歧義、TX/RX 中斷門檻為何刻意不對稱、完整 register map、建立在 virt-dma 之上的三層結構、TX/RX/terminate 三條路徑，以及 DT 綁定與 32→35 bit 定址演進。附八點除錯清單，重點是**兩種無聲降級**（port 是 console 就強制關 DMA、`dma-names` 數量不對就靜默退回 PIO）。文末區分公開來源與作者推論 |
| [DMA-BUF Heaps 完整導覽：Android 記憶體共享機制的前世今生](../dma-heap-guide.md) | 一塊 buffer 要依序經過 camera sensor → ISP → GPU → encoder → display 五個不同廠商的 IP，各自對「實體連續／對齊／cacheability／TZ 保護」的要求彼此衝突——這就是需要專門配置器的起點。從 PMEM 群雄割據 → dma-buf 誕生（3.3）→ ION 的十年 → dma-heap 接班（5.6）講歷史包袱，再拆 exporter/importer 分工、`dma_buf_ops`／`dma_resv`／`dma_fence`／`sync_file` 各自負責什麼、System heap 與 CMA heap 的差別、page pool 與 deferred free 為何存在。六條核心 flow（註冊／配置／import 與 DMA 對映／CPU 存取與 cache 維護／釋放／fence 同步）逐段追。最後是 ION → dma-heap 遷移對照（**每個 heap 各自一個 `/dev/dma_heap/*` node，權限終於能用檔案模式與 SELinux 分開**）、`dmabuf_dump` 觀測，與六個踩雷（dma-buf 洩漏在記憶體統計上隱形、忘了 sync、對 CMA 期望過高、heap 名稱不可攜、GKI 下 vendor heap 註冊時機） |
| [Hibernation：一份可以寫回 kernel 記憶體的快照](../hibernation.md) | 換一個角度看 S4——重點不是省電，而是「**hibernation image 是一份可以被完整寫回 kernel 記憶體的資料**」。先建立 ACPI 電源狀態座標，再講 swsusp 怎麼做出 snapshot、image 在 swap 裡的長相；最反直覺的是**過程中存在兩個 kernel**（做 snapshot 的與 resume 時載入的）。`dev_pm_ops` 四組 callback（suspend/freeze/poweroff/restore）的語意差異與最常見的 bug 模式、freezer 為何是協作式而非搶佔式、**信任鏈在這裡斷開**的安全問題，以及分階段隔離／`pm_trace`／image 太大等除錯手法。最後解釋 ARM/Android 為何幾乎不用 S4，並區分同名不同物的 Android App Hibernation |
| [異構 SoC 的 IPC 與三種 Domain：一份自學地圖](../til-heterogeneous-ipc-and-domains.md) | 先解決「domain 一詞在不同文件指不同東西」造成的學不下去：拆成 **lifecycle（`remoteproc`）／power（`genpd`）／memory（IOMMU、carveout）** 三個獨立面向，三者在 device tree 的 `power-domains`／`iommus`／`mboxes`／`memory-region` 交會，一起讀才是一顆 IP 的完整身分。異構 IPC 不管叫 RPMsg／IPI／mailbox／SCPI，拆開都只有四個零件（共享記憶體 + vring、mailbox/doorbell 中斷、resource table、name service）。兩個實驗當對照組：**BeagleBone Black（AM3358 + PRU）**走完整 mainline remoteproc/rpmsg 四階段（跑通 loopback 並把 resource table 對到 `/proc/iomem`、拆解往返延遲後發現大頭在排程喚醒而非 IPC、故意弄壞它看 recovery、接上 power domain）；**Orange Pi Zero 2（H616，已無 ARISC）**則是無 SCP 的對照——BL31 直接寫 power sequence 暫存器。附 mainline 裡可讀的現成教材（`mtk_scp.c`、`mtk-pm-domains.c`、`mtk_iommu.c`、`mtk-cmdq-mailbox.c`、TF-A `plat/allwinner/`）與**從 patch series 反推系統架構**的讀法 |
| [PMU、Ftrace、EMI：SoC 效能問題的三個觀測層次](../pmu-ftrace-emi.md) | 三個常被混在一起的縮寫，其實是 **CPU 微架構層 / 作業系統層 / 記憶體子系統層** 三個互補視角。先拆一詞多義（PMU = Performance Monitoring Unit 或 Power Management Unit；EMI = External Memory Interface 或電磁干擾），再講各自怎麼用：`perf` 與 counter multiplexing、big.LITTLE 的 event 編碼陷阱；Ftrace 的 tracer 種類、filter 為何不能省、Android 上 atrace/Perfetto 的資料來源就是它；EMI MPU violation log 與頻寬計數器。最後用「畫面偶爾卡頓」示範三層怎麼串著看 |

---

## 九、RTOS 與 MCU

> 前面幾節幾乎都是「板子上跑 Linux」；這一節是不跑 Linux 的那一側——MCU 等級的即時作業系統。

| 文章 | 內容 |
|---|---|
| [在 Arduino 101 上跑 Zephyr（Windows + WSL）](../Embedded/zephyr-arduino-101.md) | 實作紀錄：Intel Curie（Quark SE C1000，x86 + ARC 雙核）**只有 Zephyr 1.14 LTS 支援，v2.0 起整個移除**，所以要配 SDK 0.10.3。WSL 裡用 uv 建 Python 3.8 venv、`apt-get download` 解開 gperf，全程不用 sudo；`-DCONFIG_ARC_INIT=n` 只跑 x86 核心的 `blinky`。Windows 端用 dfu-util 在按 reset 後的 **5 秒 DFU 視窗**內寫入 `x86_app` 分區。最大的坑是 Zadig：Create New Device 會預填目前選到的序列埠 ID（`0AB6`），WinUSB 很容易裝錯裝置，要裝的是 DFU 的 `8087:0ABA` |

---

## 建議閱讀順序

**想理解一塊板子怎麼從上電跑到 Linux：**

```
嵌入式系統背景知識
   → 開機流程（泛用概念）      ← 先抓共通骨架
   → x86 Linux Boot Flow       ← 熟悉的桌面平台先建立直覺
   → RISC-V Linux Boot Flow    ← 換架構看 OpenSBI/SBI 的位置
   → ARM Trusted Firmware（TF-A）
   → Das U-Boot                ← 真的敲指令的那一層
```

**想自己做一份 embedded Linux image：**

```
嵌入式系統背景知識
   → Buildroot                 ← 小而快
   → Yocto Project             ← 大而全
   → Das U-Boot                ← 把 image 開起來
   → Firmware Image 管理       ← 出貨前的通道與晉升機制
```

**想搞懂 first silicon 回來之後發生什麼事：**

```
IC 設計的前段／中段／後段        ← 上游：矽是怎麼被做出來的
   → Post-Silicon Validation 入門  ← 整體流程與 debug 方法論
   → Shmoo 與電氣驗證              ← 其中最工程的一段：V/F/T 掃描與 Vmin
   → 半導體量產測試全景            ← 驗證結論怎麼變成量產測試與分級
```

**想搞懂一顆晶片出廠前經過哪些測試：**

```
半導體量產測試全景          ← 先看四者定位與經濟學
   → CP 晶圓測試             ← 封裝前
   → FT 最終測試             ← 封裝後
   → SLT 系統級測試          ← 出貨前，攔漏網
   → ATE 是什麼              ← 前三站的共用設備
   → MTBF 與系統整合         ← 延伸：軟體堆疊的品質度量
```

---

## 待補主題

用第一性原理拆嵌入式系統：**硬體 → boot → kernel／driver → userspace**，外加 **工具鏈、除錯、週邊通訊** 三條橫軸。目前筆記在 **boot flow 與建置系統**（U-Boot、Yocto、Buildroot、各架構開機）很完整，但 **driver、硬體介面、除錯**——嵌入式工程師每天在做的事——幾乎空白。下表依重要性排序。

| 主題 | 為什麼重要 | 狀態 |
|---|---|---|
| **Device Tree 深入** | DTB 在 boot flow、Buildroot、U-Boot 幾乎每篇都被提到，但**它本身**——語法、binding、overlay、`&label`／phandle、常見 `status`／`reg` 錯誤——沒有專門文章。這是描述「板子上有什麼硬體」的核心 | 待補 |
| **交叉編譯工具鏈** | [嵌入式背景](../embedded.md) 帶了 cross-compile 一詞就沒了。target triplet（`arm-linux-gnueabihf`）、sysroot、`CC`/`CROSS_COMPILE`、libc 選擇（glibc／musl／uClibc）是 bring-up 第一道關卡 | 待補 |
| **Linux device driver 模型** | 從 char device、platform driver、`probe()`／device-tree match、到 `module_init`／sysfs。目前只有 BMC 分類零星碰到 driver，嵌入式視角的驅動撰寫沒有 | 待補 |
| **I2C / SPI / UART / GPIO 週邊匯流排** | 板子上感測器、EEPROM、周邊晶片幾乎都掛在這幾條匯流排上。每個嵌入式工程師都要會用 `i2cdetect`／`spidev`／sysfs GPIO 與對應的 kernel 子系統，目前散在 BMC 而無嵌入式專篇 | 待補 |
| **中斷、DMA 與 MMIO** | driver 與硬體對話的三種基本方式——記憶體映射暫存器、中斷（top/bottom half、threaded IRQ）、DMA。理解延遲與資料搬移瓶頸的基礎 | 待補 |
| **JTAG / OpenOCD / gdb 硬體除錯** | [TF-A 解析](../ARM_Trusted_Firmware_解析.md) 提到「最難的 bug 靠 JTAG」，但沒有一篇講怎麼實際接 JTAG、用 OpenOCD + gdb 單步跟 bootloader／kernel。printk 救不了時的最後一哩 | 待補 |
| **Flash 儲存（eMMC / UFS / SPI-NOR / MTD / UBIFS）** | image 最終要落到儲存裝置上。raw flash 與 managed flash 的差異、MTD 分割、UBI/UBIFS 對 NAND 的磨損平衡，是選型與開機失敗排查的常見來源 | 待補 |
| **Clock / Regulator / Power management** | SoC 上每個 IP 都要供電與時脈才會動，bring-up 時「裝置沒反應」常常是 clock／regulator 沒開。runtime PM、suspend/resume 路徑也是耗電與喚不醒問題的核心 | 待補 |
| **RTOS（FreeRTOS / Zephyr）** | 不是所有嵌入式都跑 Linux。MCU 等級的即時系統、task/scheduler/IPC 與 [State Machine](../Embedded/state_machine.md) 的 bare-metal 手法互補，目前只有一篇上手實作（[Arduino 101 跑 Zephyr](../Embedded/zephyr-arduino-101.md)），還缺 RTOS 本身的概念篇 | 起步 |
