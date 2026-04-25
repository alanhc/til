---
title: x86 Linux Boot Flow
sidebar_position: 1
---

# x86 Linux Boot Flow（x86 Linux 開機流程）

從按下電源鍵到登入提示符，x86 架構的 Linux 開機流程跨越韌體、Bootloader、Kernel 與 Userspace 四個層次。本文整理完整流程，並涵蓋 BIOS/Legacy 與現代 UEFI 兩種路徑的差異。

## 整體流程概覽

```
Power On
   │
   ▼
CPU Reset Vector（0xFFFFFFF0）
   │
   ├─── Legacy ────────────────────────────────────────┐
   │                                                   │
   ▼                                                   ▼
BIOS（POST）                                      UEFI Firmware（POST）
   │                                                   │
   ▼                                                   ▼
MBR Bootloader                               UEFI Boot Manager
   │                                                   │
   ▼                                                   ▼
Stage 2 Bootloader（GRUB）               EFI Application（GRUB / systemd-boot）
   │                                                   │
   └────────────────────┬──────────────────────────────┘
                        │
                        ▼
               Linux Kernel（vmlinuz）
                        │
                        ▼
                  initramfs / initrd
                        │
                        ▼
                  pivot_root → 真正的 RootFS
                        │
                        ▼
                  init（systemd / SysVinit）
                        │
                        ▼
                  Login / Desktop
```

---

## 1. CPU Reset Vector

### 說明
x86 處理器上電或 Reset 後，CS:IP 被設置為固定位址 `0xFFFF:0xFFF0`（實際映射至 `0xFFFFFFF0`），這是 **Reset Vector**，CPU 從此處取第一條指令執行。

該位址映射至主機板 SPI Flash 上的**韌體（BIOS 或 UEFI）**。

### 硬體初始化背景
- CPU 初始進入 **Real Mode**（16-bit，只能定址 1MB）
- 多核心 CPU 只有 **BSP（Bootstrap Processor）** 執行開機流程
- 其他 CPU 核心（AP, Application Processor）等待被喚醒

---

## 2a. BIOS（Legacy）路徑

### POST（Power-On Self Test）
BIOS 執行一系列硬體自我測試：
- 偵測並初始化 CPU、記憶體（DRAM）、晶片組
- 偵測儲存裝置（IDE / SATA / NVMe）
- 初始化 VGA 顯示
- 若有錯誤，發出 POST Beep Code

### INT 13h 與 Boot Device 選擇
BIOS 遍歷啟動裝置順序（Boot Order），找到可開機裝置後：

```
從 Boot Device 的第一個磁區（512 bytes）讀取 MBR
   │
   ├─ 檢查結尾是否為 Magic Number 0x55AA
   │
   └─ 載入至記憶體位址 0x7C00 並跳轉執行
```

### MBR 結構（512 bytes）
```
┌──────────────────────────────────────┐  偏移 0x000
│  Bootstrap Code（Stage 1）           │  446 bytes
├──────────────────────────────────────┤  偏移 0x1BE
│  Partition Table Entry 1             │  16 bytes
│  Partition Table Entry 2             │  16 bytes
│  Partition Table Entry 3             │  16 bytes
│  Partition Table Entry 4             │  16 bytes
├──────────────────────────────────────┤  偏移 0x1FE
│  Magic Number：0x55AA                │  2 bytes
└──────────────────────────────────────┘
```

### MBR 限制
- 最多 4 個主要分割區
- 分割區大小最大 2TB（32-bit LBA）
- Stage 1 程式碼空間僅 446 bytes，功能極有限

---

## 2b. UEFI（現代）路徑

### UEFI 概覽
UEFI（Unified Extensible Firmware Interface）是 BIOS 的現代替代品，提供更豐富的功能：

| 特性 | BIOS | UEFI |
|---|---|---|
| 位元模式 | 16-bit Real Mode | 32/64-bit Protected Mode |
| 分割表 | MBR（最大 2TB） | GPT（最大 9.4ZB） |
| 安全開機 | 無 | Secure Boot |
| 開機介面 | 文字 | 圖形 UI |
| 網路開機 | 有限 | 完整支援（PXE via EFI） |

### UEFI 開機流程分階段（PI 規範）

```
SEC（Security Phase）
   │  初始化快取作為 RAM（Cache-as-RAM），執行最早期的信任根
   ▼
PEI（Pre-EFI Initialization）
   │  初始化 DRAM，載入 DXE Core
   ▼
DXE（Driver Execution Environment）
   │  載入驅動程式（儲存、網路、顯示...），初始化所有硬體
   ▼
BDS（Boot Device Selection）
   │  UEFI Boot Manager 讀取 NVRAM 中的 BootOrder 變數
   ▼
EFI Boot Application（e.g., GRUB、systemd-boot）
   │  從 ESP（EFI System Partition）中的 .efi 檔案執行
   ▼
OS Loader（handoff 到 Kernel）
```

### ESP（EFI System Partition）
```
ESP（FAT32 分割區）
└── EFI/
    ├── BOOT/
    │   └── BOOTX64.EFI      ← 預設開機項目（Fallback）
    ├── ubuntu/
    │   └── shimx64.efi      ← Secure Boot shim
    │   └── grubx64.efi
    └── systemd/
        └── systemd-bootx64.efi
```

### Secure Boot
```
UEFI Firmware 持有 PK（Platform Key）
   │
   └─ 驗證 KEK（Key Exchange Key）
         │
         └─ 驗證 db（Allowed Signatures Database）
               │
               └─ 驗證 shim / Bootloader 簽章
                     │
                     └─ 驗證 Kernel 簽章
```
Secure Boot 確保整條啟動鏈上的每個元件都有可信任的簽章，防止 Bootkit 攻擊。

---

## 3. GRUB（GRand Unified Bootloader）

GRUB 是 Linux 最廣泛使用的 Bootloader，支援 Legacy MBR 與 UEFI 兩種模式。

### GRUB 載入階段

#### Legacy 模式
```
Stage 1（MBR，446 bytes）
   │  位置有限，只夠儲存跳轉指令
   ▼
Stage 1.5（MBR Gap 或 Boot Partition）
   │  提供讀取檔案系統的基本驅動（ext4、XFS...）
   ▼
Stage 2（/boot/grub/）
   │  完整 GRUB 環境，顯示選單、讀取設定
   ▼
grub.cfg 解析與選單
```

#### UEFI 模式
```
grubx64.efi（直接從 ESP 載入）
   │  包含完整 GRUB，無需 Stage 1.5
   ▼
grub.cfg 解析（通常位於 /boot/grub/grub.cfg）
```

### grub.cfg 範例
```bash
menuentry 'Ubuntu 24.04 LTS' {
    insmod gzio
    insmod part_gpt
    insmod ext2
    set root='hd0,gpt2'
    linux   /boot/vmlinuz-6.8.0-45-generic \
            root=/dev/sda2 ro quiet splash
    initrd  /boot/initrd.img-6.8.0-45-generic
}
```

### GRUB 傳遞給 Kernel 的資訊
- **Kernel Image 路徑**（vmlinuz）
- **initrd/initramfs 路徑**
- **Kernel cmdline 參數**（`root=`、`ro`、`quiet`、`console=`...）
- **記憶體映射表**（e820 map）

---

## 4. Linux Kernel 初始化

Kernel 被載入至記憶體後開始執行，分為幾個明確的階段：

### 4.1 解壓縮階段（Decompression）
`vmlinuz` 是壓縮過的 Kernel Image，自帶解壓縮程式碼：
```
vmlinuz（壓縮 Image）
   │  執行頭部的解壓縮 stub
   ▼
vmlinux（解壓縮後的真實 Kernel ELF）
   │  位於記憶體中
   ▼
Kernel Entry Point（start_kernel()）
```

### 4.2 早期初始化（Arch Setup）
```c
// arch/x86/kernel/head_64.S → init/main.c
start_kernel()
   │
   ├─ setup_arch()        // CPU 架構設定、記憶體偵測
   ├─ mm_init()           // 記憶體管理初始化（buddy allocator、slab）
   ├─ sched_init()        // 排程器初始化
   ├─ irq_init()          // 中斷向量表設置
   ├─ time_init()         // 時鐘初始化（TSC / HPET / PIT）
   └─ rest_init()         // 啟動 kernel threads
```

### 4.3 CPU 模式切換
```
Real Mode（16-bit）
   │  BIOS/UEFI 期間
   ▼
Protected Mode（32-bit）
   │  Kernel 早期初始化
   ▼
Long Mode（64-bit）
   │  現代 x86-64 Kernel 標準模式
   ▼
啟用 MMU（虛擬記憶體分頁）
```

### 4.4 重要 Kernel 子系統初始化順序
```
記憶體管理（Memory Management）
   ↓
虛擬記憶體（VMM / paging）
   ↓
中斷與例外處理（IRQ / IDT）
   ↓
處理器排程（Scheduler / CFS）
   ↓
計時器（jiffies / hrtimer）
   ↓
驅動程式核心（Driver Core / sysfs）
   ↓
PCI 總線掃描
   ↓
儲存裝置驅動（AHCI / NVMe / virtio）
   ↓
虛擬檔案系統（VFS）
   ↓
掛載 initramfs
   ↓
執行 /init（第一個 userspace 程序）
```

### Kernel 參數（cmdline）常見參數
```bash
root=/dev/sda2         # RootFS 裝置
ro                     # 唯讀掛載 root（fsck 後重新 remount rw）
quiet                  # 抑制開機訊息
splash                 # 顯示開機動畫
console=tty0           # 主控台輸出至螢幕
console=ttyS0,115200   # 同時輸出至序列埠
init=/bin/bash         # 緊急模式：直接執行 bash
single                 # 進入單人模式（maintenance mode）
nomodeset              # 停用 KMS（顯示驅動問題時使用）
```

---

## 5. initramfs / initrd

### 為什麼需要 initramfs？
Kernel 本身不包含所有驅動程式（例如 LUKS 加密、RAID、特定 NVMe 驅動），但掛載 RootFS 前就需要這些驅動，形成「雞生蛋、蛋生雞」的問題。**initramfs** 是解法：在 Kernel 內建立一個暫時的 in-memory RootFS，提供必要工具後再切換至真正的 RootFS。

### initramfs 結構
```
initramfs（cpio + gzip/zstd 壓縮）
├── bin/              ← BusyBox 等基本工具
├── sbin/
│   └── init          ← 暫時的 init 腳本
├── lib/
│   └── modules/      ← 必要的 Kernel 模組（.ko）
├── etc/
└── scripts/          ← 掛載腳本（Debian 系）
```

### initramfs 主要工作
```
/init（initramfs 內）
   │
   ├─ 載入必要 Kernel 模組（insmod）
   │   例如：dm_crypt、raid1、nvme、xfs
   │
   ├─ 解鎖 LUKS 加密磁區（若有）
   │
   ├─ 組裝 RAID / LVM（若有）
   │
   ├─ 執行 fsck（檔案系統檢查）
   │
   └─ pivot_root / switch_root
         │
         └─ 切換至真正的 RootFS，執行 /sbin/init
```

---

## 6. systemd（現代 init）

### 說明
現代 Linux 發行版（Ubuntu、Fedora、Debian、Arch）幾乎全面採用 **systemd** 作為 PID 1 的 init 系統。

### 啟動 Target 順序

```
default.target（通常指向 graphical.target 或 multi-user.target）
   │
   ├─ graphical.target
   │     ├─ multi-user.target
   │     │     ├─ basic.target
   │     │     │     ├─ sysinit.target
   │     │     │     │     ├─ local-fs.target（掛載本地磁區）
   │     │     │     │     ├─ swap.target
   │     │     │     │     └─ systemd-udevd（裝置偵測）
   │     │     │     └─ network.target
   │     │     ├─ NetworkManager.service
   │     │     ├─ sshd.service
   │     │     └─ crond.service
   │     └─ display-manager.service（GDM / SDDM / LightDM）
```

### systemd 平行化啟動
systemd 的核心優勢是**平行啟動**：透過分析服務相依關係（`After=`、`Requires=`、`Wants=`），讓不相依的服務同時啟動，大幅縮短開機時間。

```bash
# 分析開機時間
systemd-analyze
systemd-analyze blame          # 各服務啟動耗時
systemd-analyze critical-chain # 關鍵路徑
systemd-analyze plot > boot.svg # 視覺化圖表
```

---

## 7. 磁碟分割架構比較

### MBR vs GPT

| 特性 | MBR | GPT |
|---|---|---|
| 最大磁碟大小 | 2 TB | 9.4 ZB |
| 最大分割區數 | 4 個主要分割區 | 128 個分割區（預設） |
| 備份分割表 | 無 | 有（磁碟尾部備份） |
| 開機方式 | BIOS / UEFI（CSM） | UEFI（推薦）|
| 識別方式 | 分割區編號 | GUID（全域唯一識別碼） |

### 典型 Linux 磁碟配置（UEFI + GPT）
```
磁碟（/dev/nvme0n1）
├── /dev/nvme0n1p1    ESP（FAT32, ~512MB）  ← /boot/efi
├── /dev/nvme0n1p2    /boot（ext4, ~1GB）   ← Kernel / initrd
├── /dev/nvme0n1p3    swap（或 swapfile）
└── /dev/nvme0n1p4    /（ext4 / XFS / btrfs）← RootFS
```

---

## 常見除錯方法

### 查看開機 log
```bash
# 查看 systemd 開機 log（本次開機）
journalctl -b

# 查看上次開機（崩潰或重啟後）
journalctl -b -1

# 查看 Kernel 訊息
dmesg
dmesg | grep -i "error\|fail\|warn"
dmesg --level=err,warn

# 查看開機時間分析
systemd-analyze blame
```

### GRUB 救援模式
```bash
# 在 GRUB 選單按 'e' 編輯開機參數
# 在 kernel 行末尾加入：
init=/bin/bash    # 直接進 bash（bypass init）
single            # 進入單人維護模式
ro recovery       # Ubuntu recovery mode
```

### 常見開機失敗原因

| 現象 | 可能原因 | 對策 |
|---|---|---|
| 黑畫面，無 GRUB | MBR/ESP 損壞，GRUB 未安裝 | GRUB rescue 或 Live CD 修復 |
| GRUB rescue 提示符 | GRUB 找不到 grub.cfg | `set root=`、`insmod`、手動 boot |
| Kernel panic: VFS mount fail | root= 參數錯誤、RootFS 損毀 | 確認 UUID/裝置名、fsck |
| initramfs 提示符 | fsck 失敗、模組缺失 | `fsck -y /dev/sda1` |
| systemd 服務失敗 | 服務設定錯誤、相依未滿足 | `journalctl -u <service>` |
| 開機卡在某服務 | 服務 timeout | `systemctl disable <service>` |

---

## BIOS vs UEFI 開機路徑對照

```
BIOS Legacy                          UEFI
─────────────────────────────────────────────────────────
Reset Vector (0xFFFFFFF0)            Reset Vector (0xFFFFFFF0)
       │                                    │
BIOS POST（Real Mode）              SEC → PEI（Cache-as-RAM）
       │                                    │
INT 13h 讀取 MBR                    DXE（驅動載入，Protected Mode）
       │                                    │
GRUB Stage 1（446 bytes）           BDS（BootOrder in NVRAM）
       │                                    │
GRUB Stage 1.5（MBR Gap）          GRUB / systemd-boot（.efi）
       │                                    │
GRUB Stage 2（grub.cfg）            grub.cfg（在 ESP 或 /boot）
       │                                    │
       └──────────── Linux Kernel ──────────┘
                          │
                     initramfs
                          │
                       systemd
```

---

## 參考資料

- [Linux Inside - Kernel Booting Process](https://0xax.gitbooks.io/linux-insides/content/Booting/)
- [UEFI Specification](https://uefi.org/specifications)
- [GRUB2 Manual](https://www.gnu.org/software/grub/manual/grub/)
- [systemd Boot Process](https://www.freedesktop.org/software/systemd/man/bootup.html)
- [The Linux Boot Process Explained](https://www.kernel.org/doc/html/latest/admin-guide/init.html)
- [OSDev Wiki - x86 Boot Sequence](https://wiki.osdev.org/Boot_Sequence)
