---
title: Embedded / 韌體 / 硬體 名詞表
sidebar_label: Embedded 名詞表
sidebar_position: 7
---

# Embedded / 韌體 / 硬體 名詞表

彙整知識庫中所有嵌入式系統、韌體、硬體與半導體筆記出現過的名詞，用於**從名詞反查回原始筆記**。文章清單見 [Embedded 系列索引](embedded_index.md)。

> ARM Trusted Firmware（BL1~BL33、EL0~EL3、TrustZone、Secure/Normal World、PSCI、SMC、TBBR、OP-TEE 等）術語不在此重複，見 [Android 名詞表](android_glossary.md) 第五節。

---

## 一、開機與 Bootloader

### 泛用概念

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Reset vector** | CPU 上電或 reset 後 PC 指向的固定位址，從此取第一條指令，執行 SoC 內建的 boot ROM／第一段 code | [開機流程（泛用概念）](../booting/boot.md) |
| **多階段開機（multi-stage）** | 早期程式空間極小（可能只有幾 KB SRAM），需分階段逐步載入，每階段初始化足夠硬體再交棒給下一階段 | [開機流程（泛用概念）](../booting/boot.md) |
| **Chain of trust（信任鏈）** | Secure boot 中每一階段驗證下一階段簽章後才執行 | [開機流程（泛用概念）](../booting/boot.md) |
| **Root of trust** | 信任鏈的起點，通常是不可竄改的 boot ROM | [開機流程（泛用概念）](../booting/boot.md) |

### x86（BIOS / UEFI / GRUB）

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Reset Vector `0xFFFFFFF0`** | x86 上電後 `CS:IP` 設為 `0xFFFF:0xFFF0`（映射至 `0xFFFFFFF0`），指向主機板 SPI Flash 上的韌體 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **BSP / AP** | 多核 CPU 中只有 **BSP（Bootstrap Processor）** 跑開機流程，其他核心 **AP（Application Processor）** 等待被喚醒 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **Real / Protected / Long Mode** | x86 CPU 模式：16-bit Real Mode（開機初期、只能定址 1MB）→ 32-bit Protected Mode → 64-bit Long Mode（現代 kernel 標準）→ 啟用 MMU | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **BIOS** | 傳統韌體。開機執行 POST，遍歷 Boot Order，經 `INT 13h` 讀取 MBR | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **POST（Power-On Self Test）** | 韌體開機時的硬體自我測試（CPU／DRAM／晶片組／儲存／VGA），出錯發出 beep code | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **MBR** | 磁碟第一個磁區（512 bytes），含 Stage 1 bootstrap code（446 bytes）、4 個分割表項與結尾 magic number；載入至 `0x7C00` 執行 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **Magic Number `0x55AA`** | MBR 結尾兩 bytes，BIOS 用來確認該磁區可開機 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **UEFI** | BIOS 的現代替代品，32/64-bit、支援 GPT、Secure Boot、圖形 UI 與 PXE 網路開機 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **SEC / PEI / DXE / BDS** | UEFI PI 規範四階段：SEC（Cache-as-RAM、最早信任根）→ PEI（Pre-EFI，初始化 DRAM、載入 DXE Core）→ DXE（Driver Execution Environment，載入驅動）→ BDS（Boot Device Selection，讀 NVRAM 的 `BootOrder`） | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **Cache-as-RAM** | DRAM 尚未初始化時，把 CPU 快取當 RAM 用，供 SEC 階段執行 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **ESP（EFI System Partition）** | FAT32 分割區，存放 `.efi` 開機程式（如 `BOOTX64.EFI`、`shimx64.efi`、`grubx64.efi`） | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **Secure Boot（PK / KEK / db）** | UEFI 逐層驗證簽章：Platform Key → Key Exchange Key → 簽章資料庫 `db` → shim／bootloader → kernel，防 Bootkit | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **shim** | Secure Boot 下的第一階 EFI 程式（`shimx64.efi`），再去載入 `grubx64.efi` | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **GRUB Stage 1 / 1.5 / 2** | Legacy GRUB 分階段：Stage 1（MBR，446 bytes，只夠跳轉）→ Stage 1.5（MBR Gap，提供檔案系統驅動）→ Stage 2（完整環境、讀 `grub.cfg`）。UEFI 模式 `grubx64.efi` 直接含完整 GRUB | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **e820 map** | BIOS/GRUB 傳給 kernel 的記憶體映射表 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **`vmlinuz` / `vmlinux`** | `vmlinuz` 為壓縮過的 kernel image，自帶解壓縮 stub 解出真正的 `vmlinux` ELF，再跳進 `start_kernel()` | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **initramfs / initrd** | kernel 內建的暫時 in-memory rootfs，載入掛載真 rootfs 前所需的模組（`dm_crypt`、RAID、NVMe…），完成後 `pivot_root`／`switch_root` 切換 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md)、[RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **`pivot_root` / `switch_root`** | 從 initramfs 切換到真正 rootfs 並執行 `/sbin/init` 的動作 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **MBR vs GPT** | 分割表格式：MBR 上限 2TB、4 主分割區；GPT 上限 9.4ZB、預設 128 分割區、有備份表與 GUID，配 UEFI 使用 | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **`systemd-analyze`** | 分析開機時間：`blame`（各服務耗時）、`critical-chain`（關鍵路徑）、`plot`（視覺化） | [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) |
| **`os-prober` / `update-grub`** | 灌 Windows 覆蓋 GRUB 後修復：`sudo os-prober` 找出其他 OS 分割區、`sudo update-grub` 重建選單 | [GRUB 修復](../grub.md) |

### RISC-V（OpenSBI / SBI）

| 名詞 | 說明 | 出處 |
|---|---|---|
| **ZSBL（Zero Stage Bootloader）** | 片上 ROM 內建、不可修改的第一段 code，初始化基本時鐘與 SRAM，把 FSBL 載入 SRAM 後跳轉 | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **FSBL（First Stage Bootloader）** | 第一階 bootloader（如 SiFive FSBL、oreboot、或由 U-Boot SPL 扮演），做 DRAM 初始化並載入 OpenSBI | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **OpenSBI** | 開源 M-mode 韌體，實作 SBI 介面、傳遞 FDT 位址、切換至 S-mode 跳進 U-Boot 或 kernel | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **SBI（Supervisor Binary Interface）** | 定義 S-mode（kernel）與 M-mode（韌體）之間標準介面，類比 x86 BIOS INT 或 ARM 的 PSCI | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **M / S / U-mode** | RISC-V 三個特權層級：M-mode（OpenSBI、bootloader，最高權）、S-mode（kernel、hypervisor）、U-mode（應用程式） | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **`ecall`** | S-mode 向下呼叫 M-mode 韌體的指令（類 syscall），SBI 呼叫的觸發方式 | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **SBI 呼叫慣例** | `a7`=Extension ID、`a6`=Function ID、`a0~a5`=參數；`ecall` 後 `a0`=錯誤碼、`a1`=返回值 | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **CSR（Control and Status Registers）** | M/S-mode 的控制暫存器，如 `mhartid`、`mstatus`、`mepc`、`mtvec`、`satp`、`sstatus`、`sepc` | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **hart** | Hardware Thread，RISC-V 的硬體執行緒。Hart 0 為 primary hart 跑開機流程，其餘 secondary hart `WFI` 等待喚醒 | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **HSM（Hart State Management）** | OpenSBI 的 SBI 擴充，負責多核 hart 的啟停管理（`sbi_hsm`） | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **PMP（Physical Memory Protection）** | M-mode 設定的實體記憶體保護，OpenSBI 初始化 M-mode 環境時設定 | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **`fw_jump` / `fw_payload` / `fw_dynamic`** | OpenSBI 三種韌體映像：`fw_payload`（把 U-Boot/kernel 打包進來，QEMU 常用）、`fw_jump`（跳轉到固定位址）、`fw_dynamic`（前階段動態傳遞下一階段資訊，現代主流） | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **FDT（Flattened Device Tree）** | 扁平化的 device tree，OpenSBI 把其位址放在 `a1` 暫存器傳給下一階段，kernel 以 `early_init_fdt()` 解析 | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **Sv39 / Sv48 / Sv57** | RISC-V 分頁模式：Sv39（39-bit 虛擬位址、3 層頁表、64-bit Linux 預設）、Sv48（4 層）、Sv57（5 層） | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **CLINT** | Core Local Interruptor，處理軟體中斷（IPI）與計時器中斷，每個 hart 各一組 | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **PLIC** | Platform-Level Interrupt Controller，處理外部中斷（UART、GPIO、NVMe…），可設各 hart 的優先權與 mask | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **`extlinux.conf`** | 類 GRUB 的 U-Boot 開機設定檔（`DEFAULT`／`LABEL`／`KERNEL`／`FDT`／`APPEND`） | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |

### U-Boot

| 名詞 | 說明 | 出處 |
|---|---|---|
| **U-Boot（Das U-Boot）** | 嵌入式平台最常見的開源 bootloader，初始化硬體、載入 kernel 與 device tree，提供互動式命令列 | [Das U-Boot](../Embedded/uboot.md)、[嵌入式系統背景知識](../embedded.md) |
| **U-Boot SPL vs Proper** | SoC 剛上電只有小容量 SRAM，先跑輕量 **SPL** 初始化 DRAM，再載入完整的 **U-Boot Proper** | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |
| **`bootcmd`** | U-Boot 環境變數：自動開機倒數結束後執行的指令 | [Das U-Boot](../Embedded/uboot.md) |
| **`bootargs`** | U-Boot 環境變數：傳給 Linux kernel 的 cmdline（如 `console=ttyS0,115200 root=/dev/mmcblk0p2`） | [Das U-Boot](../Embedded/uboot.md) |
| **`printenv` / `setenv` / `saveenv`** | 列出／設定／存回 flash（eMMC/NAND/SPI）中的環境變數 | [Das U-Boot](../Embedded/uboot.md) |
| **`tftp` / `fatload`** | 從網路（TFTP）或本地儲存（MMC FAT）把 kernel 與 dtb 載入到指定記憶體位址 | [Das U-Boot](../Embedded/uboot.md) |
| **`booti` / `bootm`** | 啟動 kernel。`booti` 三引數為 `<kernel>`、`<initrd>`（`-` 表無）、`<dtb>` 的載入位址 | [Das U-Boot](../Embedded/uboot.md) |
| **FIT Image** | Flattened Image Tree，把 kernel + DTB + initramfs 打包成一檔的 U-Boot 標準格式 | [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) |

---

## 二、建置系統

### Yocto

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Yocto Project** | 打造客製化 embedded Linux 發行版的建構框架——不是發行版，而是幫你建出專屬 toolchain／kernel／rootfs 的工具集 | [Yocto Project](../Embedded/yocto.md) |
| **BitBake** | Yocto 的任務排程與建構引擎，解析 recipe、處理相依、執行 fetch/compile/package 等 task | [Yocto Project](../Embedded/yocto.md) |
| **OpenEmbedded** | 與 BitBake 搭配的核心 metadata 集，提供大量基礎 recipe | [Yocto Project](../Embedded/yocto.md) |
| **Recipe（`.bb`）** | 描述如何建一個套件：原始碼來源（`SRC_URI`）、版本、相依（`DEPENDS`）、編譯與安裝步驟 | [Yocto Project](../Embedded/yocto.md) |
| **`SRC_URI`** | recipe 中指定原始碼來源的變數 | [Yocto Project](../Embedded/yocto.md) |
| **`DEPENDS`** | recipe 中指定建置相依的變數 | [Yocto Project](../Embedded/yocto.md) |
| **Layer（`meta-*`）** | 一組 recipe／設定的集合，可疊加組合（`meta`、`meta-poky`、BSP 的 `meta-<vendor>`），以 `bblayers.conf` 管理啟用哪些 layer | [Yocto Project](../Embedded/yocto.md) |
| **`MACHINE` / `DISTRO`** | `MACHINE` 指定目標硬體、`DISTRO` 指定發行版政策，設在 `conf/local.conf` | [Yocto Project](../Embedded/yocto.md) |
| **`oe-init-build-env`** | `source` 它以設定環境並進入 `build/` 目錄 | [Yocto Project](../Embedded/yocto.md) |
| **`bitbake core-image-minimal`** | 建構目標 image，產物在 `tmp/deploy/images/<machine>/`（含 kernel、dtb 與 `.wic`／`.ext4` 等 rootfs image） | [Yocto Project](../Embedded/yocto.md) |

### Buildroot

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Buildroot** | 另一套嵌入式建置系統，統管 kernel 與 U-Boot，kernel 底下再掛 Driver 與 Device Tree | [Buildroot](../Embedded/buildroot.md)、[嵌入式系統背景知識](../embedded.md) |
| **`make menuconfig`** | Buildroot 主設定入口（選套件、kernel、rootfs 等） | [Buildroot](../Embedded/buildroot.md) |
| **`make uboot-menuconfig`** | 設定 U-Boot 的入口 | [Buildroot](../Embedded/buildroot.md) |
| **`defconfig`** | 預設設定檔，建置系統與 kernel／U-Boot 設定的起點 | [嵌入式系統背景知識](../embedded.md) |

---

## 三、韌體工程實踐

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Release Channel（發布通道）** | 「正式 vs 非正式 image」對應的概念，經典是 Chrome 四通道 **Canary → Dev → Beta → Stable**：越前面越新越不穩、給早期測試踩雷，越後面越嚴謹 | [Firmware Image 管理](../firmware_image_management.md) |
| **Build Promotion（建置晉升）** | 同一個 build artifact 不重編譯，「一路晉升」通過各 gate（自動測試 → 候選 → 整合測試 → 正式），保證位元層級相同——**build once, promote many** | [Firmware Image 管理](../firmware_image_management.md) |
| **Nightly Build** | 每日／每晚自動出的 build，搭配 trunk-based development 隨時可產出非正式 image | [Firmware Image 管理](../firmware_image_management.md) |
| **Trunk-Based Development** | 主線隨時可出 build 的持續整合模式，原則是 **"master/trunk is always green"**，靠自動化擋掉壞 commit | [Firmware Image 管理](../firmware_image_management.md) |
| **Shift-Left Testing（測試左移）** | 把測試／整合往開發前段推，越早發現 bug 修復成本越低；非正式 image 是其載體 | [Firmware Image 管理](../firmware_image_management.md) |
| **Release Candidate（RC）** | 從 release branch 切出、凍結功能（feature freeze）、只修 bug、經完整 regression 才 sign-off 給 QA 的正式 image | [Firmware Image 管理](../firmware_image_management.md) |
| **CI/CD pipeline** | 承載 build promotion 與分支策略的自動化骨幹（Jenkins、GitLab CI 等） | [Firmware Image 管理](../firmware_image_management.md) |
| **LAVA** | Linaro 的自動化韌體/OS 測試框架，把 build flash 到實體板開機測試 | [Firmware Testing](../firmware_testing.md) |
| **openQA** | 開源自動化 OS 測試工具，常與 LAVA 一同出現在韌體 CI 議程 | [Firmware Testing](../firmware_testing.md) |
| **Linaro validation** | Linaro 的 validation 平台（validation.linaro.org），韌體驗證的參考基礎設施 | [Firmware Testing](../firmware_testing.md) |

---

## 四、硬體與週邊

| 名詞 | 說明 | 出處 |
|---|---|---|
| **嵌入式 Linux 四大組成** | Bootloader（上電最先執行、載入 kernel）→ Kernel（管理記憶體/排程/檔案系統/driver）→ rootfs（使用者空間、init 與應用）→ Driver（kernel 與硬體周邊的橋樑） | [嵌入式系統背景知識](../embedded.md) |
| **Device Tree（`.dts` / `.dtb`）** | 描述板上硬體資訊的資料結構，`.dts` 原始檔編譯成 `.dtb`，由 bootloader 傳給 kernel | [嵌入式系統背景知識](../embedded.md) |
| **交叉編譯（cross-compile）** | 在一個架構的主機上編譯出另一架構可執行的程式，需對應的 toolchain | [嵌入式系統背景知識](../embedded.md) |
| **kernel space vs user space** | 核心空間（driver、排程、記憶體管理）與使用者空間（函式庫、應用程式）的權限分界 | [嵌入式系統背景知識](../embedded.md) |
| **init（BusyBox init / systemd）** | rootfs 掛載後執行的第一個使用者空間程式，管理服務啟動 | [嵌入式系統背景知識](../embedded.md) |
| **State Machine（狀態機）** | 用「狀態＋事件＋轉換規則」描述系統行為的模型，嵌入式常用來管理開機/待機/工作等狀態；實作四步驟：定義狀態 → 定義事件 → 定義轉換規則 → 實作狀態機 | [State Machine](../Embedded/state_machine.md) |
| **`nvidia-smi`** | 查 NVIDIA GPU 狀態的指令：驅動版本、CUDA 版本、溫度功耗、佔用 VRAM 的 process | [NVIDIA GPU](../gpu_nvidia.md) |
| **`lsmod \| grep nvidia`** | 查 NVIDIA kernel 模組相依：`nvidia`、`nvidia_uvm`、`nvidia_drm`、`nvidia_modeset` | [NVIDIA GPU](../gpu_nvidia.md) |
| **CUDA** | NVIDIA 的 GPU 運算平台，`nvidia-smi` 會顯示其版本 | [NVIDIA GPU](../gpu_nvidia.md) |
| **Raspberry Pi Imager** | 官方燒錄工具，把 OS 寫入 microSD，開機前可預設 SSH／Wi-Fi／帳號 | [Raspberry Pi](<../raspberry pi.md>) |
| **GPIO** | 通用輸入輸出腳位，可接感測器與周邊，常用於 IoT、home server、自動化 | [Raspberry Pi](<../raspberry pi.md>)、[嵌入式系統背景知識](../embedded.md) |

---

## 五、半導體與製程

| 名詞 | 說明 | 出處 |
|---|---|---|
| **半導體** | 導電性介於導體與絕緣體之間的材料（最常見為矽 Si），可透過摻雜與外加電壓控制導電行為，是 IC 的基礎 | [半導體](../半導體/半導體.md) |
| **N 型 / P 型** | 摻入不同雜質形成多數載子為電子（n-type）或電洞（p-type） | [半導體](../半導體/半導體.md) |
| **摻雜（doping）** | 摻入雜質改變半導體導電行為的手段 | [半導體](../半導體/半導體.md) |
| **PN 接面（junction）** | 二極體的基礎，具單向導通特性 | [半導體](../半導體/半導體.md) |
| **MOSFET** | 現代 IC 最基本的開關元件，由 gate 電壓控制 source–drain 通道導通 | [半導體](../半導體/半導體.md) |
| **CMOS** | NMOS + PMOS 互補組成，靜態功耗低，是數位邏輯主流製程 | [半導體](../半導體/半導體.md) |
| **fabless** | 只做 IC 設計、不自建晶圓廠（如聯發科、NVIDIA、高通） | [半導體](../半導體/半導體.md) |
| **foundry（晶圓代工）** | 專做製造的晶圓廠（如台積電 TSMC） | [半導體](../半導體/半導體.md) |
| **OSAT（封裝測試）** | 委外封裝與測試廠（如日月光） | [半導體](../半導體/半導體.md) |
| **IDM** | 設計＋製造整合（如 Intel、三星） | [半導體](../半導體/半導體.md) |
| **光罩 / 微影 / 蝕刻 / 沉積 / 離子佈植** | 反覆堆疊的核心製程：photomask、lithography、etch、deposition、implant | [半導體](../半導體/半導體.md) |
| **製程節點** | 如 3nm、5nm，越先進單位面積電晶體越多、效能/功耗越好 | [半導體](../半導體/半導體.md) |

---

## 六、半導體量產測試

### 測試站點與設備

| 名詞 | 說明 | 出處 |
|---|---|---|
| **test insertion（測試站點）** | 晶片從晶圓到客戶手上經過的一連串測試站點，每加一站成本顯著上升 | [半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) |
| **CP（Chip Probing / Wafer Sort）** | 晶圓切割封裝**前**的測試，用探針卡扎裸 die 接點透過 ATE 篩壞品；核心價值是省封裝費並回饋晶圓良率給 fab | [CP 晶圓測試](../what-is-cp-wafer-test.md)、[半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) |
| **FT（Final Test）** | 晶片**封裝後**的測試，放進 socket 經 load board 接 ATE，驗封裝製程有無引入缺陷、補測 CP 測不了的項目、分 bin 出貨 | [FT 最終測試](../what-is-ft-final-test.md) |
| **SLT（System-Level Test）** | 出貨前把晶片放進類產品板開機跑韌體/OS，攔 ATE 結構性測試抓不到的漏網缺陷（test escape），把品質壓到客戶要求的 DPPM | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) |
| **ATE（Automated Test Equipment）** | 自動化測試**設備**（不是測試階段），CP 與 FT 共用的機台平台，把測試向量以電訊號打進接腳比對輸出 | [ATE 是什麼](../what-is-ate.md) |
| **Tester / Handler / Prober** | ATE 環境三要素：tester（機台本體）、prober（移動晶圓對準探針）、handler（抓取封裝品放進 socket、依結果分料） | [ATE 是什麼](../what-is-ate.md)、[FT 最終測試](../what-is-ft-final-test.md) |
| **probe card（探針卡）** | CP 用來接觸裸 die pad 的介面；分懸臂樑（Cantilever/CPC）、垂直（Vertical/VPC）、MEMS 三類，接觸電阻與寄生電感限制了高頻與大電流測試 | [CP 晶圓測試](../what-is-cp-wafer-test.md)、[ATE 是什麼](../what-is-ate.md) |
| **load board + socket** | FT/SLT 用來連接封裝品與機台的介面硬體 | [FT 最終測試](../what-is-ft-final-test.md) |
| **DUT（Device Under Test）** | 受測晶片 | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) |
| **wafer map** | CP 產出的晶圓好壞分布圖（以 ink 點或電子紀錄），封裝廠只取 good die | [CP 晶圓測試](../what-is-cp-wafer-test.md) |
| **WAT / PCM** | Wafer Acceptance Test（也稱 PCM），測晶圓切割道（scribe line）上的 test key 元件電性參數，監控 **fab 製程**是否穩定——與測產品的 CP 完全不同層次 | [CP 晶圓測試](../what-is-cp-wafer-test.md)、[半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) |
| **WLCSP** | 晶圓級封裝，產品在晶圓階段就完成封裝，CP 測完切割即出貨，無傳統 FT | [CP 晶圓測試](../what-is-cp-wafer-test.md)、[半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) |
| **盲封** | 製程成熟、良率穩定時跳過 CP 直接封裝的做法，風險自負 | [CP 晶圓測試](../what-is-cp-wafer-test.md) |
| **redundancy analysis / laser repair** | 記憶體 CP 特有：算出可修復位址，用雷射把 repairable die 救回，同時提升良率與可靠度 | [CP 晶圓測試](../what-is-cp-wafer-test.md) |

### 測試哲學與 DFT

| 名詞 | 說明 | 出處 |
|---|---|---|
| **結構性測試（Structural Test）** | CP/FT 主體：不驗功能而驗「電路結構有沒有做對」，依賴 DFT，有 fault model 可量化 coverage、測試時間秒級 | [半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md)、[ATE 是什麼](../what-is-ate.md) |
| **功能性測試（Functional Test）** | SLT 主體：直接模擬終端使用情境（開機、跑 OS、真實 workload），抓結構測試抓不到的缺陷，但無 coverage 理論、時間長、fail 難除錯 | [半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) |
| **DFT（Design for Test）** | 設計階段就埋進晶片的測試電路（scan chain、MBIST），讓 ATE 能控制與觀測內部節點 | [ATE 是什麼](../what-is-ate.md) |
| **ATPG（Automatic Test Pattern Generation）** | 自動產生測試向量的工具，配合 scan chain 控制/觀測內部節點 | [ATE 是什麼](../what-is-ate.md) |
| **scan chain** | 把晶片內部暫存器串成移位鏈，把深埋電路「攤開」給機台看 | [ATE 是什麼](../what-is-ate.md) |
| **MBIST（Memory Built-In Self-Test）** | 記憶體區塊內建自我測試電路，機台下指令收結果即可 | [ATE 是什麼](../what-is-ate.md) |
| **fault model（故障模型）** | 讓覆蓋率可精確計算的模型：stuck-at、transition、bridging 等 | [ATE 是什麼](../what-is-ate.md)、[半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) |
| **stuck-at fault** | 最常見的故障模型（節點卡在固定 0 或 1），可計算「pattern 覆蓋了 98.5% stuck-at fault」這類工程陳述 | [ATE 是什麼](../what-is-ate.md) |
| **fault coverage** | 一組 pattern 對某 fault model 的覆蓋率，可量化 | [ATE 是什麼](../what-is-ate.md)、[DFT 工程實務](../DFT_Design_for_Test_工程實務.md) |
| **transition / at-speed fault** | 節點會翻轉但翻得太慢的延遲型故障，需在功能頻率下用兩個 pattern（launch → capture）測 | [DFT 工程實務](../DFT_Design_for_Test_工程實務.md) |
| **shift / capture** | scan test 的兩個階段：shift 把測試向量沿 scan chain 移入移出（慢速時脈），capture 讓組合邏輯在一個時脈內把結果打進 FF | [DFT 工程實務](../DFT_Design_for_Test_工程實務.md) |
| **scan FF（scan flip-flop）** | 多一個 scan input 與 scan enable 的 FF，測試模式下串成 scan chain，是 scan design 的基本單元 | [DFT 工程實務](../DFT_Design_for_Test_工程實務.md) |
| **test compression** | 用解壓縮器／壓縮器把少量外部 channel 展開成大量內部 scan chain，壓 pattern 資料量與測試時間 | [DFT 工程實務](../DFT_Design_for_Test_工程實務.md) |
| **LBIST（Logic BIST）** | 邏輯自測：LFSR 產生偽隨機 pattern、MISR 把回應壓成 signature 比對，車用／安全等級晶片常要求開機自測 | [DFT 工程實務](../DFT_Design_for_Test_工程實務.md) |
| **LFSR / MISR** | 線性回授移位暫存器（產生偽隨機測試向量）與多輸入簽章暫存器（把大量回應壓成一個 signature），LBIST 的兩端 | [DFT 工程實務](../DFT_Design_for_Test_工程實務.md) |
| **Boundary Scan（IEEE 1149.1 / JTAG）** | 在 IO pad 旁串一圈 boundary scan cell，用 TAP（TCK/TMS/TDI/TDO）測板級焊接與晶片間連線，也是進 scan/BIST 的入口 | [DFT 工程實務](../DFT_Design_for_Test_工程實務.md) |
| **TAP controller** | JTAG 的 16 狀態機，由 TMS 驅動在 instruction／data register 之間切換；bringup 時讀得到 IDCODE 是第一個里程碑 | [DFT 工程實務](../DFT_Design_for_Test_工程實務.md)、[DFT Verification 面試準備](../DFT_Verification_面試準備.md) |
| **OCC（On-Chip Clock Controller）** | at-speed test 時在晶片內部切換 shift 慢速時脈與 capture 功能時脈的控制電路 | [DFT Verification 面試準備](../DFT_Verification_面試準備.md) |

### DFT 驗證（simulation 端）

| 名詞 | 說明 | 出處 |
|---|---|---|
| **VCS / Verdi** | Synopsys 的模擬器與 debug／波形工具；DFT verification 的日常組合——VCS 跑 RTL/gate sim，Verdi 做 signal tracing 與 FSDB 波形 debug | [DFT Verification 面試準備](../DFT_Verification_面試準備.md) |
| **gate-level simulation** | 在合成後 netlist 上跑模擬，用來驗 ATPG 產出的 pattern 與 ATE 預期一致 | [DFT Verification 面試準備](../DFT_Verification_面試準備.md) |
| **SDF back-annotation** | 把 Standard Delay Format 的實際延遲反標進 gate-level sim，才驗得到 setup/hold 相關問題 | [DFT Verification 面試準備](../DFT_Verification_面試準備.md) |
| **X-propagation** | 未初始化 FF／時脈 reset 問題導致的未知值在 netlist 上擴散，是 gate sim 最常見的殺手，debug 靠 driver trace 往回追 | [DFT Verification 面試準備](../DFT_Verification_面試準備.md) |
| **hierarchical verification（IP／cluster／full chip）** | 三層驗證策略：單一 macro 獨立驗 → 數個 IP 整合驗介面 → 整顆晶片驗 top 連線與 DFT mode 切換 | [DFT Verification 面試準備](../DFT_Verification_面試準備.md) |
| **chip bringup** | 矽從 fab 回來後第一次點亮：scan chain 通不通、JTAG IDCODE 讀不讀得到是早期關鍵里程碑 | [DFT Verification 面試準備](../DFT_Verification_面試準備.md)、[Bring-up 全紀錄](../bringup-article.md) |

### 分級、良率與品質度量

| 名詞 | 說明 | 出處 |
|---|---|---|
| **binning** | 依測試結果把晶片實體分料（physical binning），除好壞外還依效能等級分級 | [FT 最終測試](../what-is-ft-final-test.md) |
| **speed binning** | 依 Fmax／Vmin 把同一顆設計分成不同 speed grade 販售，決定 SKU 與定價 | [FT 最終測試](../what-is-ft-final-test.md)、[半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) |
| **Fmax / Vmin** | 最高工作頻率／最低工作電壓，FT 量測用於 speed binning 與系統軟體 DVFS 設定 | [FT 最終測試](../what-is-ft-final-test.md)、[ATE 是什麼](../what-is-ate.md) |
| **DPPM（Defective Parts Per Million）** | 每百萬顆的不良數，chip vendor 寫進合約的品質承諾；汽車客戶動輒要求個位數 | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) |
| **十倍法則** | 缺陷越晚被發現越貴：CP 攔到損失一顆 die、FT 多賠封裝費、逃到客戶產線要拆板重工、逃到終端是 field return 與品牌傷害 | [半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) |
| **test escape** | 逃過測試站點的漏網缺陷，SLT 的攔截對象 | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) |
| **SDC（Silent Data Corruption）** | 晶片不當機、只默默算錯的靜默資料損毀，多源自 timing margin 勉強及格的邊際缺陷，需特定指令/資料才觸發 | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md)、[ATE 是什麼](../what-is-ate.md) |
| **邊際缺陷（marginal defect）** | 電性「勉強及格」（timing margin 偏低但未低到 scan fail），特定電壓/溫度/資料下才出錯 | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) |
| **Shift Right + Shift Left** | 先在 SLT 攔系統級失效（shift right），再把失效模式回饋給 ATE pattern 與設計規則（shift left）形成閉環 | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) |
| **adaptive SLT** | 依前段測試資料用預測模型給每顆晶片打 DPPM 風險標籤，高風險跑完整測項、低風險精簡或跳過 | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) |
| **chiplet / 2.5D/3D 封裝** | 先進封裝讓「每顆 die 都 known-good」不等於「組起來 known-good-system」，引入 die-to-die interconnect、封裝應力、熱耦合等新失效模式 | [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) |

### MTBF 與系統整合

| 名詞 | 說明 | 出處 |
|---|---|---|
| **MTBF（Mean Time Between Failures）** | 教科書上是可修復系統的平均故障間隔（總運作時間 ÷ 故障次數）；在行動裝置產品線語境更常指**整機軟體穩定性指標**，客戶把門檻寫進出貨 exit criteria | [MTBF 與系統整合](../mtbf-and-why-si-owns-it.md) |
| **MTTF（Mean Time To Failure）** | 用於不可修復元件（壞了就換）的平均壽命，晶片、燈泡講 MTTF | [MTBF 與系統整合](../mtbf-and-why-si-owns-it.md) |
| **MTTR（Mean Time To Repair）** | 平均修復時間；`MTBF = MTTF + MTTR`，可用度 = `MTBF / (MTBF + MTTR)` | [MTBF 與系統整合](../mtbf-and-why-si-owns-it.md) |
| **Monkey** | Android 內建壓測工具，注入偽隨機（seed 可重現）使用者事件流對整個軟體堆疊施壓，是 MTBF 壓測核心 | [MTBF 與系統整合](../mtbf-and-why-si-owns-it.md) |
| **MTBF triage** | 把壓測收集的 crash 去重、初判、跨 stack log 分析後分派給 owner 團隊的循環；本質是「以統計形式呈現的跨團隊 log 分析」，落在系統整合（SI）團隊 | [MTBF 與系統整合](../mtbf-and-why-si-owns-it.md) |
| **系統整合（SI）** | 模組團隊對零件負責、SI 對「組起來撐不撐得住」負責；MTBF 與 SLT 都是其主場，需跨層 debug 能力歸因失效 | [MTBF 與系統整合](../mtbf-and-why-si-owns-it.md) |
