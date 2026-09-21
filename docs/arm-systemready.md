# Arm SystemReady：讓 Arm 平台做到「裝了就能開機」

## 為什麼需要 SystemReady

在 x86 上，你拿一個 Ubuntu 或 Fedora 的 ISO，不管是 Dell、HP 還是自己組的電腦，大多直接就能開機安裝。這背後靠的是業界幾十年累積的共同介面：UEFI、ACPI、PCI 列舉。作業系統不必知道板子的細節，韌體會把硬體資訊交給它。

Arm 生態走的是另一條路。每家 SoC 廠、每塊板子都有自己的 bootloader、自己的 device tree 和一堆沒進 upstream 的 kernel patch。結果是「一板一 image」：發行版要替每塊板子做專屬版本，裝置出貨後的 OS 升級、安全更新也綁死在原廠的 BSP 上。

Arm SystemReady 就是 Arm 為了解決這個碎片化問題推出的**標準加上認證計畫**。目標很單純：

> **通用、未經修改的作業系統映像檔，可以直接在符合規範的 Arm 硬體上開機並正常運作。**

## 發展脈絡

- **2018：Arm ServerReady**，只針對伺服器，確保 Linux 發行版與 Windows 能直接在 Arm 伺服器上跑。
- **2020：擴展成 SystemReady**，涵蓋伺服器以外的 edge、IoT 和嵌入式裝置，分成 SR、ES、IR、LS 幾個 band。
- **2024 年底重整**：簡化成兩個主要 band（見下文）。原本的 SR 和 ES 合併，IR 改名，LS（LinuxBoot）退場。

## 底層規範：SystemReady 認證的是什麼

SystemReady 本身不是一份新規格，而是把幾份 Arm 規範組合起來，再用測試驗證：

| 規範 | 範圍 |
|---|---|
| **BSA**（Base System Architecture） | 硬體層最低要求：CPU 架構版本、GIC 中斷控制器、Generic Timer、PCIe、SMMU、UART 等 OS 會預期存在的元件 |
| **SBSA**（Server BSA） | 在 BSA 之上針對伺服器的更嚴格要求 |
| **BBR**（Base Boot Requirements） | 韌體與開機介面。包含兩套 recipe：**SBBR**（UEFI + ACPI，伺服器風格）和 **EBBR**（UEFI + Devicetree，嵌入式風格） |
| **BBSR**（Base Boot Security Requirements） | 開機安全：UEFI Secure Boot、Capsule Update（韌體更新）、TPM Measured Boot |

一句話總結：**BSA 管硬體長什麼樣子，BBR 管韌體怎麼把硬體交給 OS，BBSR 管這個過程是否安全。**

## 兩個 Band

### SystemReady Band（UEFI + ACPI）

- 前身是 SR 和 ES
- 硬體符合 BSA（伺服器另外參考 SBSA），韌體符合 SBBR
- 用 ACPI 描述硬體，行為跟 x86 PC/伺服器最接近
- 目標是通用發行版（RHEL、SUSE、Ubuntu、Debian、Fedora 等）、Windows，以及 VMware ESXi 這類 hypervisor 直接裝
- 典型場景：資料中心、雲端、infrastructure edge、高階 edge 閘道器

### SystemReady Devicetree Band（UEFI + Devicetree）

- 前身是 IR（IoT Ready）
- 韌體符合 EBBR：提供 UEFI 介面，但硬體描述用 **Devicetree**，不用 ACPI
- 通常用 **U-Boot 的 UEFI 實作**，不必上完整的 EDK2
- 重點是 DTB 由韌體提供，而且要能用 upstream kernel 的 binding，OS 不必自帶板子專屬的 DTB
- 典型場景：IoT、嵌入式 Linux、工業控制、車用周邊

## 典型開機堆疊

```
┌─────────────────────────────────────────┐
│  Generic OS (Ubuntu / Fedora / Windows) │
├─────────────────────────────────────────┤
│  GRUB / systemd-boot (UEFI app)         │
├─────────────────────────────────────────┤
│  UEFI 介面                               │
│   ├─ ACPI tables  → SystemReady Band    │
│   └─ Devicetree   → Devicetree Band     │
│  EDK2 或 U-Boot (EFI)                    │
├─────────────────────────────────────────┤
│  TF-A (BL1/BL2/BL31) + PSCI / SMCCC     │
├─────────────────────────────────────────┤
│  BSA-compliant hardware                 │
│  (GIC, Generic Timer, PCIe, SMMU, UART) │
└─────────────────────────────────────────┘
```

OS 看不到板子細節，只透過 UEFI Boot/Runtime Services、ACPI 或 DT、PSCI（CPU 開關、電源管理）來跟平台溝通。這就是「一個 image 跑遍所有板子」的關鍵。

## 怎麼拿到認證：ACS 測試

Arm 在 GitHub 上提供 **Architecture Compliance Suite（ACS）**（[`ARM-software/arm-systemready`](https://github.com/ARM-software/arm-systemready)），會打包成可直接開機的測試映像，內容包括：

- **BSA / SBSA ACS**：在 UEFI shell 和 Linux 下檢查硬體是否符合 BSA
- **SCT（UEFI Self-Certification Test）**：驗證 UEFI 實作
- **FWTS（Firmware Test Suite）**：檢查 ACPI 表、SMBIOS 等韌體資料
- **BBSR 相關測試**：Secure Boot、TPM 測量等
- **Devicetree 驗證**：用 dt-schema 檢查 DTB 是否符合 upstream binding（Devicetree Band 用）
- **OS 相容性測試**：實際安裝、開機多個主流 Linux 發行版，確認沒有額外 patch 也能正常運作

跑完測試後把結果與 log 送到 Arm 審查，通過就會列在官方的認證清單上。

## 對產業的意義

1. **對 OS 廠商與發行版**：不必再逐板維護 image，可以用同一套 kernel 和 installer 支援整個 Arm 生態。
2. **對硬體廠商**：降低客戶導入門檻，「能裝標準 Ubuntu/RHEL」就是很好的賣點，特別是跟 x86 搶 edge 和伺服器市場時。
3. **對終端用戶**：產品生命週期拉長。OS 升級和安全更新可以直接來自發行版，不必苦等原廠 BSP，這在 EU Cyber Resilience Act 等法規要求長期安全更新的背景下越來越重要。
4. **對韌體工程**：韌體變成一個穩定的平台層，TF-A、EDK2、U-Boot 的角色和介面更清楚，也更強調 upstream-first。

## 限制與現實面

- **手機和 Android 不在範圍內**。Android 走的是自己的路線，用 GKI（Generic Kernel Image）加 vendor module 分離來處理類似問題，精神相近但機制不同。
- Devicetree Band 相對寬鬆，實際上能否「通用」，還是取決於 driver 有沒有進 upstream kernel。
- 認證本身是一次性的快照，韌體之後的更新能不能維持合規，要看廠商自己的紀律。
- 低階 MCU 等級（Cortex-M）裝置不適用，這些沒有 MMU、不跑通用 OS。

## 結語

SystemReady 在做的事，是把 Arm 從「每塊板子都是特例」推向「平台化」，讓 Arm 在伺服器和 edge 上也有 x86 那種即插即用的體驗。對韌體和平台工程師來說，理解 BSA、BBR、TF-A、UEFI 與 ACPI/DT 這一整套堆疊，已經是 Arm 平台工作的基本功，不管是資料中心的 SBSA 伺服器，還是嵌入式 SoC 平台都用得到。

## 參考資料

- [Arm SystemReady Compliance Program](https://www.arm.com/architecture/system-architectures/systemready-compliance-program)
- [Arm SystemReady Band](https://www.arm.com/architecture/system-architectures/systemready-compliance-program/systemready-band)
- [Arm SystemReady Devicetree Band](https://www.arm.com/architecture/system-architectures/systemready-compliance-program/systemready-devicetree-band)
- [SystemReady Devicetree Band Integration and Testing Guide v4.4](https://documentation-service.arm.com/static/695bd966d62b016405276517?token=)
- [ARM-software/arm-systemready (GitHub)](https://github.com/ARM-software/arm-systemready)
- [Integrate Arm SystemReady Band – UEFI and ACPI (UEFI Forum)](https://uefi.org/sites/default/files/resources/15.%20Integrate%20Arm%20SystemReady_Arm_Wang_FINAL.pdf)
