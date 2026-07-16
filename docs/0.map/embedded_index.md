---
title: Embedded / 韌體 / 硬體 文章索引
sidebar_label: Embedded 系列索引
sidebar_position: 5
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
