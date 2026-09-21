# LinuxBoot 與 u-root：用 Linux 取代 UEFI DXE 的伺服器韌體架構

> TL;DR：LinuxBoot 保留韌體中負責 DRAM／silicon 初始化的 SEC、PEI（或 coreboot romstage），把 DXE 以後那一大段 UEFI 換成一個放在 SPI flash 裡的精簡 Linux kernel，加上 Go 寫的 initramfs（u-root）。u-root 找到真正要開機的 OS 之後，用 kexec 跳過去。這套做法主要用在資料中心伺服器，Android 的開機流程則不會用到它。

---

## 1. 傳統 UEFI 開機流程

x86 伺服器依照 UEFI／PI 規範開機，流程如下：

```
SEC → PEI → DXE → BDS → Bootloader (GRUB) → Linux kernel → OS
```

| 階段 | 職責 |
|---|---|
| **SEC** (Security) | reset vector，把 cache 當 RAM 用（Cache-as-RAM），建立最初的信任根 |
| **PEI** (Pre-EFI Initialization) | DRAM training、CPU 和 chipset 初始化，通常呼叫 Intel FSP 或 AMD AGESA |
| **DXE** (Driver Execution Environment) | 載入上百個 driver：PCIe、USB、NIC、SATA/NVMe、網路 stack（PXE/HTTP boot）、Setup UI、各種 protocol |
| **BDS** (Boot Device Selection) | 依照 boot order 選開機裝置 |
| **GRUB** | 再解析一次檔案系統、讀設定檔，最後載入 kernel |

**問題出在 DXE 以後：**

- 程式碼量龐大，大多是 IBV（AMI、Insyde、Phoenix）的閉源程式碼。
- 它其實在重做 Linux kernel 已經做得更好的事：NIC 與儲存 driver、網路 stack、檔案系統。
- OS 起來之後，這些 driver 幾乎全部被丟掉，由 Linux 再初始化一次。

---

## 2. LinuxBoot：用 Linux 取代 DXE 以後的所有東西

```
傳統:      SEC → PEI → [ DXE → BDS → GRUB ]                   → OS kernel
LinuxBoot: SEC → PEI → [ Linux kernel + u-root initramfs ] --kexec--> OS kernel
```

- **保留 SEC/PEI**：DRAM training 和 silicon init 跟晶片綁得很深，而且通常只有廠商提供的 blob（FSP/AGESA），這段換不掉，也沒必要換。
- **DXE 以後換成精簡的 Linux kernel**，直接放在主機板的 SPI flash 裡。
- kernel 帶一個 initramfs（**u-root**），負責找到真正要開機的 OS。
- 找到之後，用 **kexec** 直接跳進目標 kernel。

換句話說，flash 裡的 Linux 是「當 bootloader 用的 Linux」，跟最後執行的 OS kernel 是兩個不同的 kernel。

### 2.1 兩種實作方式

**UEFI-based**

- 保留廠商 UEFI 的 SEC/PEI。
- 用 UTK（UEFI Tool Kit）之類的工具，把 firmware volume 裡的 DXE driver 大量移除，再塞進 Linux kernel。
- 有些做法會留一個極小的 DXE core，專門負責載入 kernel。
- 優點是不需要重新移植整個平台。

**coreboot-based**

```
bootblock → romstage (DRAM init, 呼叫 FSP) → ramstage (PCI 列舉、產生 ACPI table) → payload: LinuxBoot
```

- coreboot 做最少量的硬體初始化，最後把 LinuxBoot 當成 payload 執行。
- 架構更乾淨、更開放，但前提是 coreboot 已經支援那塊主機板。

---

## 3. u-root 的角色

[u-root](https://github.com/u-root/u-root) 是用 Go 寫的 initramfs，提供這個「bootloader Linux」的使用者空間。

### 3.1 設計特點

- **Busybox mode**：所有指令編成單一 Go binary，用 symlink 分派。壓縮後大約幾 MB，放得進 SPI flash。
- **可讀、可測試**：整個 userland 都是 Go，沒有 shell script 那一堆魔法，可以寫 unit test 並跑 CI。
- **Debug 友善**：出問題時可以直接進 shell，有 `ip`、`dmesg`、`lspci`、`dd` 等常用工具，遠比 UEFI Shell 方便。

### 3.2 開機相關指令

| 指令 | 用途 |
|---|---|
| `localboot` | 掃描本機磁碟，解析 `grub.cfg`、syslinux、BLS 設定，找出 kernel 和 initrd |
| `netboot` / `pxeboot` | DHCP 加上 HTTP(S) 或 TFTP 抓 kernel。使用 Linux 網路 stack 和 Go 的 TLS 實作 |
| `boot` | 整合前兩者的通用前端（前身是 systemboot） |
| `kexec` | 載入目標 kernel 並跳轉 |

---

## 4. kexec：不經過韌體直接換 kernel

kexec 讓目前正在執行的 Linux kernel 把控制權直接交給另一個 kernel，中間不經過 firmware reset。

**流程：**

1. 透過 `kexec_file_load` / `kexec_load` 把新 kernel 和 initrd 載入記憶體。
2. 目前的 kernel 執行 shutdown hook，讓裝置 quiesce。
3. 把開機資訊交給新 kernel：x86 上是 ACPI table 和 e820 memory map，ARM 上是 device tree。
4. 跳到新 kernel 的 entry point。

**常見問題：**

- **裝置狀態殘留**：有些裝置沒有被正確 reset，新 kernel 接手時的狀態就不乾淨，常見於 NIC 和 GPU。
- **沒有 UEFI runtime services**：EFI variables 等依賴 UEFI 的功能不能用。
- **無法開 Windows**：Windows 需要完整的 UEFI 環境。

---

## 5. 為什麼資料中心特別愛用

| 動機 | 說明 |
|---|---|
| **開機速度** | DXE 加上 option ROM 列舉常常要好幾分鐘，LinuxBoot 可以縮到幾十秒以內。大量機器 reboot 時差異很明顯 |
| **可控與可稽核** | 閉源 DXE 出 bug 或有漏洞時只能等 BIOS 廠商修。換成 Linux + Go 之後，程式碼自己看得到、改得到 |
| **安全性** | 攻擊面變小，搭配 measured boot（TPM PCR）和 kernel 簽章驗證，網路開機也能走正規 TLS |
| **Driver 品質** | Linux 的 NIC 和 NVMe driver 比 UEFI DXE driver 成熟得多，新網卡也不用等廠商出 UEFI driver |
| **機群一致性** | 不同廠商的主機板跑同一套開機邏輯，行為一致，方便自動化 |
| **可 debug** | 有 shell、有 log，可以寫測試、進 CI |

**代表性採用者：**

- **Google**：最早的 NERF（Non-Extensible Reduced Firmware）專案，後來演變成 LinuxBoot。
- **Meta**：在 OCP 推 Open System Firmware，採用 coreboot + LinuxBoot。
- **OCP 社群**：LinuxBoot 是 OCP Open System Firmware 的核心元件之一。

---

## 6. 限制與取捨

- **SPI flash 容量**：kernel 加 initramfs 要放進 16/32/64MB 的 flash，而且還要跟 PEI 和其他資料共用空間，kernel 必須大幅裁剪。
- **生態綁定 UEFI**：Windows、需要 GOP option ROM 的 GPU、部分 OEM 管理工具都假設 UEFI 存在。
- **平台支援**：silicon init 仍依賴 FSP/AGESA 這類 blob，coreboot 也不是每塊板子都有移植。
- **kexec 的相容性**：裝置 reset 不完整時，問題往往很難追。

---

## 7. 那 Android 呢？

在正式的 Android 產品中**不會**使用 u-root 或 LinuxBoot。Android 的開機鏈是：

```
BootROM → SoC bootloader (LK/ABL、MTK preloader + LK、U-Boot) → AVB 驗證
        → GKI kernel → ramdisk 裡的 first_stage_init (C++) → 掛載 system/vendor → second stage init
```

- **沒有 DXE 那樣肥大的一層**：手機的 bootloader 本來就精簡，也跟 SoC 綁定，不存在「用 Linux 取代 DXE」的需求。
- **ramdisk 的 init 綁定 Android 機制**：AVB、dm-verity、fstab、SELinux、A/B slot 都寫在 Android 自己的 init 裡，不可能換成 u-root。
- **最接近的概念是 recovery 和 fastbootd**：都是「一個 Linux 環境做開機或維護用途」，但 Android 用的是自己的 C++ 實作。
- u-root 可以交叉編譯成 arm64，LinuxBoot 社群也討論過 ARM64 移植，但目標是 ARM server 和開發板，不是手機。

---

## 8. 跟 OpenBMC 的關係

伺服器上有兩套各自獨立的韌體：

```
┌──────────────────────────────┐      ┌───────────────────────────┐
│ Host CPU (x86 / ARM server)  │      │ BMC SoC (e.g. ASPEED)     │
│                              │ IPMI │                           │
│  SEC/PEI (或 coreboot)        │<────>│  OpenBMC                  │
│  └─ LinuxBoot + u-root        │Redfish│  (電源、感測器、SOL、     │
│      └─ kexec → OS            │ LPC  │   POST code、韌體更新)    │
└──────────────────────────────┘ eSPI └───────────────────────────┘
        Host firmware                     Management plane
```

- **OpenBMC** 跑在獨立的 BMC SoC 上，負責 management plane：電源控制、感測器、Serial-over-LAN、POST code、host 韌體更新。
- **LinuxBoot/u-root** 跑在 host CPU 的 firmware 裡，負責把 host 開起來。
- Hyperscaler 的方向是兩邊都換成開源：OpenBMC 加上 coreboot/LinuxBoot，形成完整開放的伺服器韌體 stack。這也是 OCP Open System Firmware 在推動的方向。

**兩者的交界：**
- BMC 透過 IPMI/Redfish 設定 host boot order 或 boot override。
- BMC 經由 LPC/eSPI 擷取 host 的 POST code（port 80）。
- BMC 觸發 host power cycle 或 reset，並負責更新 host 的 SPI flash。

---

## 參考資料

- [LinuxBoot Book](https://book.linuxboot.org/)
- [LinuxBoot using coreboot, u-root and systemboot](https://book.linuxboot.org/coreboot.u-root.systemboot/)
- [u-root GitHub](https://github.com/u-root/u-root)
- [LinuxBoot mailing list：ARM64 支援討論](https://groups.google.com/g/linuxboot/c/hGWYRY1avFc)
- [Android Booting Shenanigans (Magisk)](https://topjohnwu.github.io/Magisk/boot.html)
- [U-Boot: Android Boot Image](https://docs.u-boot.org/en/stable/android/boot-image.html)
