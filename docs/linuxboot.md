# LinuxBoot：用 Linux 取代韌體的開機流程

## 前言

伺服器開機很慢，工程師早就習慣了。一台資料中心的機器從按下電源到進入作業系統，常常要好幾分鐘，大部分時間花在 UEFI 韌體裡：初始化各種驅動、掃描 PCIe 裝置、找開機裝置。這些工作 OS 起來之後通常還會再做一次。

LinuxBoot 的出發點很簡單：Linux kernel 本來就有最成熟、測試最多的驅動程式，那開機階段為什麼要在韌體裡另外維護一套？

## LinuxBoot 是什麼

LinuxBoot 是 Linux Foundation 底下的開源韌體專案，2017 年由 Google、Facebook（現在的 Meta）、Horizon Computing Solutions 和 Two Sigma 共同發起。它的想法源自 Ron Minnich，他在 1999 年就做過 LinuxBIOS，這個專案後來演變成 coreboot。

LinuxBoot 不是從頭寫一套完整的韌體。它把一個 Linux kernel 加上 initramfs 放進 SPI flash，用來取代韌體裡「平台初始化完成之後」那段邏輯。硬體最底層的初始化（CPU、記憶體訓練）還是交給原本的韌體，Linux 接手之後負責找 OS 並開機。

## 它取代了哪一段？

UEFI 的標準開機流程（PI 規格）大致是這樣：

```
SEC → PEI → DXE → BDS → OS Loader → OS
```

- **SEC / PEI**：最早期的初始化，包括 cache-as-RAM 和記憶體初始化（DRAM training），跟晶片高度相關，通常要靠廠商提供的程式碼（例如 Intel FSP）。
- **DXE**：載入大量驅動（儲存、網路、USB、圖形……），是 UEFI 裡最龐大、最複雜的部分。
- **BDS**：選擇開機裝置並載入 bootloader。

LinuxBoot 保留 SEC/PEI，把 **DXE 和 BDS 換成 Linux kernel 加 initramfs**：

```
SEC → PEI → [Linux kernel + initramfs] → kexec → 目標 OS
```

目標 OS 最後透過 `kexec` 載入。也就是說，開機用的 Linux 直接把控制權交給正式要跑的 kernel，不需要 GRUB 這類 bootloader。

底層不一定要是 UEFI PEI。LinuxBoot 也可以搭配 **coreboot**（coreboot 做硬體初始化，payload 是 LinuxBoot）或 **Slim Bootloader**。

## 核心元件

| 元件 | 角色 |
|---|---|
| **Linux kernel** | 精簡設定的 kernel，只編進開機需要的驅動 |
| **u-root** | 用 Go 寫的 userland，把 initramfs 做成單一 binary，功能類似 busybox，也內建多種 bootloader 實作 |
| **fiano / UTK** | Go 寫的 UEFI image 處理工具，可以拆解廠商的 BIOS image，移除 DXE 模組並塞進 Linux |
| **kexec** | 從開機用的 Linux 跳進目標 OS 的 kernel |

其他相關專案有 **Heads**（著重安全與 measured boot 的 LinuxBoot 發行版）和 **Petitboot**（IBM POWER 平台上類似概念的 bootloader）。

u-root 選 Go 是有意的決定：記憶體安全、交叉編譯容易、工具鏈單純，而且整個 initramfs 可以從原始碼重現地建置出來，對供應鏈稽核很有幫助。

## 為什麼要這樣做？

**1. 開機速度**
DXE 階段通常會初始化大量用不到的裝置。換成精簡的 Linux 之後，常見的報告是開機時間大幅縮短。對需要頻繁重開、做大規模 provisioning 的資料中心來說，差距很明顯。

**2. 可靠性**
Linux 的網路、NVMe、RAID 驅動經過全世界的伺服器長年驗證，品質通常比各家 UEFI 裡各自實作的驅動穩定。

**3. 安全性與可稽核性**
UEFI DXE 程式碼大多是閉源的，攻擊面大，出了漏洞只能等廠商修補。LinuxBoot 用開源的 kernel 和 userland 取代大部分邏輯，使用者可以自己審查、修補和重新建置。

**4. 可維運性**
開機環境本身就是 Linux，可以直接用熟悉的工具：網路開機走 HTTP(S)、用 shell 和 script 除錯、在韌體階段做 TPM measurement 和簽章驗證。工程師不必再學一套 UEFI shell 和 EDK II 的開發方式。

## 限制與挑戰

- **PEI / FSP 還是閉源**：記憶體初始化這段仍然要靠晶片廠的 binary blob，LinuxBoot 沒辦法完全「去廠商化」。
- **SPI flash 空間**：要把 kernel 加 initramfs 塞進有限的 flash，kernel 設定必須非常精簡。
- **平台支援有限**：主要用在伺服器平台（特別是 OCP 生態系），一般消費性主機板很少支援。
- **和既有生態系的相容性**：某些 OS 或工具依賴 UEFI runtime services 或特定的開機介面，需要另外處理。

## 實際採用

LinuxBoot 最主要的推動者是超大規模資料中心業者。Google 內部類似的做法叫 **NERF**（Non-Extensible Reduced Firmware），Meta 也在自家伺服器上部署 LinuxBoot。這個專案也和 **OCP（Open Compute Project）Open System Firmware** 計畫密切相關，目標是讓伺服器韌體更開放、更容易稽核。

## 和 BMC / OpenBMC 的關係

如果你熟悉伺服器的管理平面，可以這樣想：**OpenBMC 把 BMC 那一側開源化，LinuxBoot 則是把 host CPU 的開機韌體開源化。** 兩者都用 Linux 取代原本封閉的專有韌體，都是 OCP 推動「開放伺服器韌體堆疊」的一部分。在這樣的架構裡，從管理控制器到主處理器的開機路徑，大部分都能用開源、可重現建置的程式碼掌握。

## 結語

LinuxBoot 沒有要重寫整套韌體。它的做法很務實：晶片相關、只有廠商做得好的最底層交給廠商，之後那一大段容易出錯又難以稽核的邏輯交給 Linux。對重視開機速度、安全性和掌控度的資料中心來說，這個做法很有說服力。

想動手試試的話，可以從 u-root 開始：在 QEMU 上用 u-root 做一個 initramfs，搭配 kernel 開機，再用它 kexec 進另一個 kernel，就能體驗 LinuxBoot 的核心流程。

## 參考資料

- [LinuxBoot GitHub](https://github.com/linuxboot/linuxboot)
- [LinuxBoot FAQ](https://www.linuxboot.org/page/faq/)
- [All about u-root – LinuxBoot Book](https://book.linuxboot.org/u-root.html)
- [u-root GitHub](https://github.com/u-root/u-root)
- [LinuxBoot – Wikipedia](https://en.wikipedia.org/wiki/LinuxBoot)
- [Coreboot – Wikipedia](https://en.wikipedia.org/wiki/Coreboot)
