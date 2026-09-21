# 從按下電源到 Linux：PC、伺服器、Android、ARM Server 開機流程由淺入深

> 這篇從「開機到底在做什麼」講起，一路談到 UEFI、LinuxBoot/u-root、Android/嵌入式，最後到 ARM server 和 NVIDIA Jetson。重點會放在**為什麼**各種平台的開機流程長得不一樣。
>
> 一句話結論：**決定開機流程的是平台型態（開放通用，或垂直整合），不是 CPU 架構（x86 或 ARM）。**

---

## Level 0：開機到底在做什麼？

剛通電時，CPU 幾乎什麼都沒有：

- **沒有 DRAM 可用**：記憶體控制器還沒設定，DRAM 還沒做 training。
- **沒有周邊**：時脈、電源、PCIe、儲存裝置都還沒初始化。
- **不知道 OS 在哪裡**：也不知道 OS 能不能信任。

所以開機就是一連串「**每一階段把環境準備得更多一點，然後把控制權交給下一階段**」的接力：

```
燒死的 ROM → 很小的韌體 → 比較大的韌體 → bootloader → OS kernel → 使用者空間
```

每一棒都要回答三個問題：

1. **我要初始化什麼硬體？**
2. **下一棒在哪裡？怎麼載入？**
3. **下一棒可以信任嗎？**（secure boot／verified boot）

後面所有平台的差異，都是這三個問題的答案不一樣。

---

## Level 1：PC 的 UEFI 開機流程

### 1.1 五個階段

x86 PC 和伺服器依照 UEFI／PI 規範開機：

```
SEC → PEI → DXE → BDS → Bootloader (GRUB / Windows Boot Manager) → OS
```

| 階段 | 白話 | 做什麼 |
|---|---|---|
| **SEC** | 起跑 | reset vector，把 CPU cache 當 RAM 用（Cache-as-RAM），建立信任根 |
| **PEI** | 把記憶體搞定 | DRAM training、CPU／chipset 基本初始化（Intel FSP、AMD AGESA） |
| **DXE** | 把所有硬體搞定 | 載入上百個 driver：PCIe 列舉、USB、NIC、NVMe、網路 stack、Setup UI |
| **BDS** | 選要從哪開 | 依照 boot order 選裝置 |
| **Bootloader** | 找 kernel | GRUB 讀檔案系統和設定檔，載入 kernel 和 initrd |

### 1.2 韌體交給 OS 的東西

- **ACPI tables**：描述這台機器有哪些硬體、怎麼做電源管理。
- **Memory map**：哪些記憶體可以用。
- **UEFI runtime services**：OS 開機後仍能呼叫的韌體服務，例如讀寫 EFI variables。

### 1.3 為什麼 DXE 這麼肥？

因為 **PC 是開放平台**：

- 韌體不知道使用者插了哪家的 PCIe 卡，只能**開機時探測**，還要執行卡上的 option ROM。
- 同一台機器要能開 Windows、各家 Linux、ESXi、BSD，所以需要一套**標準介面**，讓韌體和 OS 可以來自不同廠商。

DXE 就是這個「通用硬體抽象層」。代價是程式碼量龐大、大多閉源，而且它初始化的 driver 在 OS 起來之後幾乎全部被丟掉，由 Linux 再做一次。

---

## Level 2：LinuxBoot 與 u-root：伺服器想砍掉 DXE

### 2.1 想法

資料中心的業者（Google、Meta 等）發現：DXE 在做的事，Linux kernel 做得更好，而且程式碼自己看得到。那就乾脆**用 Linux 取代 DXE 以後的所有東西**：

```
傳統:      SEC → PEI → [ DXE → BDS → GRUB ]                     → OS kernel
LinuxBoot: SEC → PEI → [ Linux kernel + u-root initramfs ] --kexec--> OS kernel
```

- **保留 SEC/PEI**：DRAM training 和 silicon init 跟晶片綁得很深，通常只有廠商 blob（FSP/AGESA），換不掉。
- **DXE 以後換成精簡的 Linux kernel**，直接放在主機板的 SPI flash 裡。
- 這個 kernel 帶一個 initramfs（**u-root**），負責找到真正的 OS，再用 **kexec** 跳過去。

也就是說，flash 裡的 Linux 是「當 bootloader 用的 Linux」。

### 2.2 兩種實作

- **UEFI-based**：保留廠商的 SEC/PEI，用 UTK 之類的工具把 firmware volume 裡的 DXE driver 大量移除，再塞進 Linux kernel。
- **coreboot-based**：coreboot 的 bootblock → romstage（DRAM init）→ ramstage（PCI 列舉、產生 ACPI table）→ payload 為 LinuxBoot。

### 2.3 u-root

[u-root](https://github.com/u-root/u-root) 是用 Go 寫的 initramfs：

- **Busybox mode**：所有指令編成單一 Go binary，壓縮後大約幾 MB，放得進 SPI flash。
- **開機邏輯本身就是 Go 程式**：
  - `localboot`：掃描磁碟、解析 `grub.cfg`／syslinux／BLS。
  - `netboot`：DHCP 加上 HTTP(S)，使用 Linux 網路 stack 和 Go 的 TLS。
  - `boot`：整合前兩者的通用前端。
- **Debug 友善**：有 shell、`dmesg`、`lspci`、`ip`，也能寫測試、跑 CI。

### 2.4 kexec

kexec 讓正在執行的 kernel 不經過韌體，直接把控制權交給另一個 kernel：

1. `kexec_file_load` 把新 kernel 和 initrd 載入記憶體。
2. 目前的 kernel 讓裝置 quiesce。
3. 把 ACPI table 和 memory map（ARM 上是 DTB）交給新 kernel。
4. 跳到新 kernel 的 entry point。

**坑**：裝置沒有被完整 reset 時，新 kernel 接手的狀態會不乾淨；沒有 UEFI runtime services；Windows 開不了。

### 2.5 為什麼只在資料中心流行

| 優點 | 限制 |
|---|---|
| 開機從幾分鐘縮到幾十秒 | SPI flash 容量有限，kernel 必須裁剪 |
| 程式碼可稽核，漏洞可以自己修 | Windows、GPU option ROM 等依賴 UEFI |
| Linux driver 比 DXE driver 成熟 | silicon init 仍依賴 FSP/AGESA blob |
| 機群行為一致、方便自動化 | coreboot 不是每塊板子都有移植 |

資料中心的機器數量大、OS 固定是 Linux、業者有自己的韌體團隊，所以划算。一般 PC 需要支援 Windows 和各種周邊，就不划算。

---

## Level 3：Android／嵌入式：本來就沒有 DXE

### 3.1 開機鏈（以 MediaTek 為例）

```
BootROM → Preloader → TF-A (BL31) + TEE → LK → AVB 驗證
        → Linux kernel + DTB → first_stage_init (ramdisk) → second stage init → Android
```

其他 SoC 的名字不同，結構類似：Qualcomm 是 PBL → XBL → ABL，一般開發板常見的是 BootROM → SPL → U-Boot。

### 3.2 對照 PC

| PC/UEFI | 作用 | Android／嵌入式 |
|---|---|---|
| SEC | 最早的信任根 | **BootROM**（燒在晶片裡，不可改） |
| PEI | DRAM init | **Preloader／SPL／XBL** |
| — | Secure world | **TF-A BL31 + TEE**（TrustZone） |
| DXE + BDS + GRUB | 通用 driver、選裝置、載 kernel | **LK／U-Boot／ABL**：很小，只做載入加驗證 |
| ACPI | 描述硬體 | **Device Tree (DTB)** |

**嵌入式本來就是「韌體只做最少的事，driver 全部交給 Linux kernel」**，也就是 LinuxBoot 想在伺服器上達成的樣子。所以 Android 不需要 u-root。

### 3.3 為什麼長這樣？

**1. 硬體寫死，不用探測**
板子上有什麼在出廠時就確定了，用 Device Tree 靜態描述就好，不需要 PCIe 列舉或 option ROM。

**2. 只跑一個 OS**
SoC 廠、OEM、OS 是垂直整合的，bootloader 只要會載入這一個 kernel，不需要 UEFI 那套標準抽象層。

**3. 安全模型是一條硬體信任鏈**
- BootROM 用燒在 eFuse 裡的公鑰驗證下一階段，一棒接一棒驗證下去。
- 到 kernel 這一段交給 **AVB**（Android Verified Boot），搭配 dm-verity 和 rollback protection。
- 再加上 bootloader lock 和 TrustZone。

鏈越短、越固定越好驗證，在中間插一個通用 Linux 只會擴大攻擊面。

**4. 產品約束**
- 手機要在幾秒內亮螢幕，多開一個 kernel 再 kexec 是純成本。
- 映像檔放在 eMMC/UFS 的 boot partition，空間有成本。
- 更新走 A/B slot 加 OTA。

**5. ramdisk 的 init 綁定 Android 機制**
`first_stage_init` 處理 AVB、dm-verity、fstab、SELinux、A/B slot，這些都是 Android 專屬的，不可能換成 u-root 的 init。

### 3.4 伺服器和手機都為了安全，但出發點相反

- **伺服器**：面對的是厚重又閉源的 UEFI，所以要「換成自己看得到、可稽核的程式碼」，也就是 LinuxBoot。
- **手機**：面對的是被盜、被刷機、被植入的風險，所以要「從 BootROM 開始一路鎖死」，也就是 AVB 加 eFuse。

---

## Level 4：那 ARM Server 呢？

有了前面的背景，ARM server 就很好理解：**它是要跑任意 OS 的伺服器，所以走 PC 那一套；但它是 ARM，所以底層保留 ARM 的 secure boot 架構。**

### 4.1 開機鏈

```
BootROM
 → SCP/MCP firmware   (系統控制處理器：電源、時脈，有些平台由它做 DRAM init)
 → TF-A BL1/BL2       (≈ SEC/PEI)
 → TF-A BL31          (EL3 runtime：PSCI、SMC，常駐)
 → BL32 (選用)         (OP-TEE / Hafnium SPM)
 → BL33 = UEFI (EDK2) (DXE、BDS，跟 x86 同一套)
 → GRUB / shim → Linux (ACPI)
```

**前半段像手機，後半段像 PC。** OS 看到的是 **ACPI**，不是 Device Tree，所以 RHEL、Ubuntu、Windows、ESXi 可以用同一份映像檔開機。

### 4.2 Arm SystemReady 規範

ARM 為了讓伺服器像 x86 一樣隨插即用，訂了一組標準：

| 規範 | 內容 |
|---|---|
| **SBSA / BSA** | 硬體要求：GIC、timer、UART、PCIe ECAM 等必須符合標準 |
| **BBR** | 韌體要求：UEFI、ACPI、SMBIOS |
| **SystemReady SR** | 伺服器等級：UEFI + ACPI，可以開一般 distro |
| **SystemReady IR / EBBR** | 嵌入式等級：Device Tree 加上**由 U-Boot 提供精簡的 UEFI 介面** |

EBBR 是中間地帶：嵌入式板子繼續用 U-Boot 和 DT，但對外提供 UEFI API，讓標準 distro 的 GRUB/shim 也能開機。

### 4.3 LinuxBoot 在 ARM 上

一樣可行：**把 BL33 從 EDK2 換成 Linux kernel + u-root**，前面的 TF-A 不動。限制也一樣：OS 要 ACPI 時，得有人產生 ACPI table。

---

## Level 5：案例：NVIDIA 的兩條路線

### Grace（資料中心）

標準的 SystemReady SR 路線：TF-A 加上 UEFI + ACPI，搭配 BMC 管理。

### Jetson Orin（嵌入式／邊緣 AI）

從 JetPack 5 開始，Jetson 用 **UEFI（EDK2）** 當 bootloader，取代舊的 CBoot。開機鏈大致是：

```
BootROM → MB1 → MB2 → TF-A (BL31) + OP-TEE → UEFI → L4TLauncher → Linux kernel (DT)
```

- 前半段（BootROM、MB1/MB2、TF-A、OP-TEE、fuse-based secure boot）跟手機 SoC 同一種思維。
- 後半段用 UEFI 當 BL33，但 OS 端大多仍用 Device Tree，精神上接近 EBBR。

這是一個很好的例子：**嵌入式產品也可以選擇 UEFI**，目的是讓生態系（distro、工具、開發者）更標準化。

---

## 總整理

| | x86 PC | x86 Server + LinuxBoot | Android／嵌入式 | ARM Server | Jetson Orin |
|---|---|---|---|---|---|
| 早期初始化 | SEC/PEI | SEC/PEI 或 coreboot | BootROM → Preloader | BootROM → TF-A BL1/2 | BootROM → MB1/MB2 |
| Secure world | SMM | SMM | TF-A + TEE | TF-A + TEE | TF-A + OP-TEE |
| Bootloader 層 | DXE + BDS + GRUB | Linux + u-root | LK／U-Boot／ABL | UEFI + GRUB | UEFI + L4TLauncher |
| 交接方式 | UEFI → kernel | **kexec** | 直接跳 kernel | UEFI → kernel | UEFI → kernel |
| 硬體描述 | ACPI | ACPI | Device Tree | ACPI | Device Tree |
| 驗證機制 | UEFI Secure Boot | 自訂（TPM、簽章） | AVB + eFuse | UEFI Secure Boot | Fuse + UEFI Secure Boot |
| 設計重點 | 通用、相容 | 可控、快速 | 信任鏈、垂直整合 | 通用、標準化 | 兩者兼顧 |

**核心觀念：**

1. **開放平台**（要支援任意硬體、任意 OS）→ 需要厚重的標準韌體（UEFI + ACPI）。
2. **垂直整合產品**（硬體和 OS 固定）→ 韌體越薄越好，硬體交給 DT 和 kernel。
3. **LinuxBoot** 是伺服器想要「保留開放性，但把韌體變薄、變可控」的折衷。
4. **ISA 不決定開機流程**：ARM server 走 UEFI，x86 Chromebook 走 coreboot + depthcharge。

---

## 參考資料

- [LinuxBoot Book](https://book.linuxboot.org/)
- [LinuxBoot using coreboot, u-root and systemboot](https://book.linuxboot.org/coreboot.u-root.systemboot/)
- [u-root GitHub](https://github.com/u-root/u-root)
- [LinuxBoot mailing list：ARM64 支援討論](https://groups.google.com/g/linuxboot/c/hGWYRY1avFc)
- [Android Booting Shenanigans (Magisk)](https://topjohnwu.github.io/Magisk/boot.html)
- [U-Boot: Android Boot Image](https://docs.u-boot.org/en/stable/android/boot-image.html)
- [NVIDIA Jetson Linux Developer Guide：Orin Series Boot Flow](https://docs.nvidia.com/jetson/archives/r39.2.1/DeveloperGuide/AR/BootArchitecture/JetsonOrinSeriesBootFlow.html)
- [NVIDIA Jetson Linux Developer Guide：UEFI Adaptation](https://docs.nvidia.com/jetson/archives/r36.5.2/DeveloperGuide/SD/Bootloader/UEFI.html)
- [Jetson Orin UEFI boot sequence (ProventusNova)](https://proventusnova.com/blog/jetson-uefi-boot-flow-mb1-mb2-tfa-kernel)
