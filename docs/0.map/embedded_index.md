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

---

## 二、開機流程與 Bootloader

| 文章 | 內容 |
|---|---|
| [開機流程（泛用概念）](../booting/boot.md) | 跨架構的共通骨架：Reset vector → 韌體／初階 bootloader → Bootloader → Kernel，解釋多階段開機為何存在、chain of trust 與 root of trust |
| [x86 Linux Boot Flow](../booting/x86_linux_boot_flow.md) | 從 Reset Vector `0xFFFFFFF0` 到 login：BIOS/POST/MBR 與 UEFI（SEC/PEI/DXE/BDS、ESP、Secure Boot）兩條路徑對照、GRUB 各載入階段、kernel 解壓縮與模式切換、initramfs、systemd target 順序、MBR vs GPT，含 `journalctl`／`systemd-analyze` 除錯與常見開機失敗原因 |
| [RISC-V Linux Boot Flow](../booting/riscv_linux_boot_flow.md) | ZSBL → FSBL → OpenSBI → U-Boot SPL/Proper → Kernel：M/S/U-mode 特權層級與 CSR、SBI 介面與呼叫慣例、OpenSBI 三種韌體映像（FW_JUMP/FW_PAYLOAD/FW_DYNAMIC）、DTB 傳遞鏈、PLIC/CLINT 中斷架構，並比較 QEMU virt、HiFive Unmatched、VisionFive 2、Milk-V Pioneer 各平台 |
| [Das U-Boot](../Embedded/uboot.md) | U-Boot 實用速查：`printenv`/`setenv`/`saveenv` 環境變數、`bootcmd` 與 `bootargs` 差異、用 `tftp`／`fatload` 載入 kernel 與 dtb 後 `booti` 啟動 |
| [GRUB 修復](../grub.md) | 灌 Windows 後 GRUB 被覆蓋、無法進 Ubuntu 的實際排除紀錄：`sudo os-prober` 找出 Windows 分割區 → `sudo update-grub` 重建選單 |

---

## 三、ARM Trusted Firmware 與 Secure World

> 這三篇同時屬於 Android 分類。Android 視角的**深入版**請見 [ARM Trusted Firmware (TF-A) 解析](../ARM_Trusted_Firmware_解析.md) 與 [Secure Boot 解析](../Secure_Boot_解析.md)，完整清單見 [Android 系列索引](android_index.md)。

| 文章 | 內容 |
|---|---|
| [ARM Trusted Firmware (ATF)](../atf.md) | **名詞與對照表為主**：BL1~BL3-3 階段對應表（含 EL 層級）、EL0~EL3 權限分層表、TrustZone 的 Secure/Normal World 與 OP-TEE 元件樹、TrustZone vs 機密運算比較、ARMv7-A/v8-A/v9-A 安全模型演進表，以及 TrustZone → CCA 的 mermaid 時間軸 |
| [ARM Trusted Firmware（TF-A）](../booting/atf.md) | **散文式說明為主**（與上篇不同檔案）：逐段講 BL1（AP Trusted ROM）、BL2（Trusted Boot Firmware）、BL31（EL3 Runtime Firmware 常駐 Secure Monitor 並實作 PSCI）、BL32（OP-TEE）、BL33（U-Boot/UEFI）各自職責，附 Arm Juno 官方文件等參考連結 |
| [ARM Trusted Firmware 元件](../arm_trust_firmware.md) | 速記卡：What／Why／When（ARMv8 引入 TrustZone + EL3、2013-14 首版、2015 成標準）、主要元件列表（BL 各階段、TF-A、PSCI、SMC Dispatcher、SiP service、憑證鏈／RoT）與待補的名詞清單 |

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
| [Chip](../chip.md) | 佔位頁，目前只有一條 ChatGPT 對話連結，尚無整理內容 |
| [NVIDIA GPU](../gpu_nvidia.md) | Linux 上確認 NVIDIA 驅動狀態的指令與實測輸出：`lsmod \| grep nvidia` 看 `nvidia`/`nvidia_uvm`/`nvidia_drm`/`nvidia_modeset` 模組相依、`nvidia-smi` 查 RTX 5070 Ti 的驅動版本、CUDA 版本、溫度功耗與佔用 VRAM 的 process |
| [Raspberry Pi](<../raspberry pi.md>) | 單板電腦筆記：用 Raspberry Pi Imager 燒錄 OS 並預先設定 SSH／Wi-Fi／帳號、GPIO 接周邊的應用場景、官方文件與一支影片連結 |

---

## 七、半導體量產測試

> 一顆晶片從晶圓到客戶手上的測試流水線。從系統整合／韌體工程師視角看，這條線決定了拿到手的矽是什麼品質、怎麼分級，以及 MTBF 這類軟體穩定性度量為何落在整合團隊。

| 文章 | 內容 |
|---|---|
| [半導體量產測試全景](../semiconductor-test-overview-cp-ft-slt-ate.md) | **系列總綱**：CP（晶圓）→ FT（封裝後）→ SLT（出貨前）三個 test insertion 加上 ATE（設備）的定位；結構性 vs 功能性兩種測試哲學、「缺陷越晚發現越貴」的十倍法則經濟學、四角色對照表，以及從 chip vendor 看品質過濾／良率歸因／產品分級／閉環回饋四件事 |
| [ATE 是什麼](../what-is-ate.md) | 破除最常見的混淆——ATE 是 CP/FT **共用的設備**，不是一個測試階段。DFT／ATPG／scan chain 的結構性測試原理、fault model 與 coverage、市場格局，以及 ATE 覆蓋率的先天極限（為何仍需要 SLT） |
| [CP 晶圓測試](../what-is-cp-wafer-test.md) | 封裝前用探針卡扎裸 die、產出 wafer map 篩壞品；探針卡的接觸電阻／寄生電感如何限制高頻與大電流測試、CP 能不能省（盲封），以及最容易混淆的 CP vs WAT（測產品 vs 測製程） |
| [FT 最終測試](../what-is-ft-final-test.md) | 封裝後為何要再測一次（封裝製程也引入缺陷）、socket／load board 環境、以及 FT 不只判生死還做 speed binning（Fmax／Vmin 分級，直接決定 SKU 與 DVFS 設定） |
| [SLT 系統級測試](../what-is-slt-and-why-chip-vendors-care.md) | 出貨前把晶片放進類產品板開機跑軟體，攔 ATE 抓不到的跨 IP／邊際／軟硬互動缺陷；為何對 chip vendor 重要（DPPM 合約承諾、缺陷逃逸的乘數成本、大客戶把系統品質推回 vendor、閉環回饋），以及 SLT 本質是平台軟體 |
| [MTBF 與系統整合](../mtbf-and-why-si-owns-it.md) | **延伸篇**：前面講「矽」的品質，這篇講「軟體堆疊」的品質怎麼度量。為何 MTBF fail 天生沒 owner、是 build 層級度量、與 CI 同一套肌肉、直接面對客戶，因而落在系統整合（SI）的主場；附 MTBF triage 實務循環 |

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
| **RTOS（FreeRTOS / Zephyr）** | 不是所有嵌入式都跑 Linux。MCU 等級的即時系統、task/scheduler/IPC 與 [State Machine](../Embedded/state_machine.md) 的 bare-metal 手法互補，目前完全沒有 RTOS 視角 | 待補 |
