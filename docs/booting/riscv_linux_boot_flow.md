---
title: RISC-V Linux Boot Flow
sidebar_position: 2
---

# RISC-V Linux Boot Flow（RISC-V Linux 開機流程）

RISC-V 是一個開放的指令集架構（ISA），其開機流程與 x86 或 ARM 有顯著差異，引入了 **SBI（Supervisor Binary Interface）** 作為韌體與 OS 之間的標準介面。本文整理完整的 RISC-V Linux 開機流程，以主流平台（SiFive HiFive、StarFive VisionFive、QEMU virt）為範例說明。

## 整體流程概覽

```
Power On / Reset
      │
      ▼
ZSBL（Zero Stage Bootloader）
      │  ROM 內建，將 FSBL 從 Flash 載入 SRAM
      ▼
FSBL（First Stage Bootloader）
      │  e.g., SiFive FSBL、oreboot
      ▼
OpenSBI（Open Source Supervisor Binary Interface）
      │  提供 M-mode 韌體服務，初始化 SBI 介面
      ▼
U-Boot SPL（可選）
      │  初始化 DRAM（若 FSBL 未完成）
      ▼
U-Boot Proper
      │  載入 Kernel + DTB + initramfs
      ▼
Linux Kernel（riscv64）
      │  進入 S-mode，讀取 DTB
      ▼
initramfs
      │
      ▼
RootFS + init（systemd）
      │
      ▼
Userspace
```

---

## RISC-V 特權層級架構

RISC-V 定義了三個特權層級，開機流程在不同層級間切換：

```
┌─────────────────────────────────────────────────────┐
│  U-mode（User Mode）                                 │  應用程式
├─────────────────────────────────────────────────────┤
│  S-mode（Supervisor Mode）                           │  Linux Kernel、Hypervisor
├─────────────────────────────────────────────────────┤
│  M-mode（Machine Mode）                              │  OpenSBI、Bootloader
└─────────────────────────────────────────────────────┘
     最低特權                              最高特權 →
```

| 層級 | 全名 | 誰運行 | 可存取資源 |
|---|---|---|---|
| **M-mode** | Machine Mode | OpenSBI、FSBL | 所有硬體暫存器、CSR |
| **S-mode** | Supervisor Mode | Linux Kernel | 部分 CSR、透過 SBI 呼叫 M-mode |
| **U-mode** | User Mode | 應用程式 | 無直接硬體存取 |

### CSR（Control and Status Registers）重要暫存器

```
mhartid    — 目前 hart（硬體執行緒）的 ID
mstatus    — 全域狀態（中斷啟用、前一特權層級）
mepc       — M-mode 例外返回位址
mtvec      — M-mode 中斷向量表基址
satp       — 分頁模式（Sv39 / Sv48 / Sv57）+ 頁表基址
sstatus    — S-mode 狀態暫存器
sepc       — S-mode 例外返回位址
```

---

## 1. ZSBL（Zero Stage Bootloader）

### 說明
上電後 CPU hart 0 從固定位址執行片上 ROM（**ZSBL**），這是最原始的一段不可修改的程式碼。

### 主要工作
- 初始化最基本的時鐘與 SRAM
- 從 SPI Flash / SD Card / eMMC 讀取 FSBL
- 將 FSBL 複製到 SRAM 後跳轉執行

### 多 hart 處理
```
Hart 0（Primary Hart）→ 執行開機流程
Hart 1, 2, 3...（Secondary Harts）→ 等待 WFI（Wait For Interrupt）
                                     由 OpenSBI 的 HSM（Hart State Management）喚醒
```

---

## 2. FSBL（First Stage Bootloader）

### 常見實作

| FSBL | 使用平台 | 說明 |
|---|---|---|
| **SiFive Freedom U540 FSBL** | SiFive HiFive Unleashed | SiFive 官方 FSBL |
| **oreboot** | 實驗性平台 | Rust 實作的開源 FSBL |
| **coreboot + RISC-V payload** | 部分開發板 | |
| **U-Boot SPL** | StarFive VisionFive 2 | 直接由 U-Boot SPL 扮演 FSBL |

### 主要工作
- **DRAM 初始化**（DDR training，若 ZSBL 未完成）
- 從儲存裝置載入 **OpenSBI**（`fw_dynamic.bin` 或 `fw_jump.bin`）
- 可能同時載入 U-Boot 或直接跳轉至 OpenSBI

---

## 3. OpenSBI（Open Source Supervisor Binary Interface）

### SBI 是什麼？
SBI（Supervisor Binary Interface）是 RISC-V 特有的韌體規範，定義了 **S-mode（Kernel）與 M-mode（韌體）之間的標準介面**，類似於 x86 的 BIOS INT 呼叫或 ARM 的 PSCI。

```
Linux Kernel（S-mode）
      │  ecall 指令（類似 syscall，但往下呼叫韌體）
      ▼
OpenSBI（M-mode）
      │  處理硬體操作後返回
      ▼
回傳結果給 Kernel
```

### OpenSBI 三種韌體映像

| 韌體類型 | 說明 | 使用場景 |
|---|---|---|
| `fw_payload.bin` | 將 U-Boot / Kernel 打包在 OpenSBI 內 | 簡單部署，QEMU 常用 |
| `fw_jump.bin` | OpenSBI 初始化後跳轉至固定位址 | U-Boot 放置在已知位址 |
| `fw_dynamic.bin` | 由前一階段動態傳遞下一階段資訊 | 最靈活，現代主流方式 |

### OpenSBI 主要工作
1. **初始化 M-mode 環境**（設定 mtvec、PMP 保護）
2. **實作 SBI 擴充功能**：
   - `sbi_console_putchar`：序列埠輸出
   - `sbi_send_ipi`：處理器間中斷（IPI）
   - `sbi_set_timer`：定時器設定
   - `sbi_system_reset`：系統重置
   - `sbi_hsm`：Hart State Management（多核心管理）
3. **傳遞 FDT（Flattened Device Tree）** 位址給下一階段（放在 `a1` 暫存器）
4. 切換至 **S-mode** 並跳轉至 U-Boot 或 Kernel

### SBI 呼叫慣例（RISC-V Calling Convention）
```
a7 = SBI Extension ID（EID）
a6 = SBI Function ID（FID）
a0~a5 = 參數
─────────────────────────
ecall
─────────────────────────
a0 = 錯誤碼（0 = 成功）
a1 = 返回值
```

---

## 4. U-Boot（RISC-V）

### 說明
U-Boot 在 RISC-V 平台上執行於 **S-mode**，透過 SBI ecall 呼叫 OpenSBI 的硬體服務。

### U-Boot SPL vs U-Boot Proper

```
（若平台需要）U-Boot SPL
      │  執行於 M-mode 或 S-mode
      │  初始化 DRAM、載入 OpenSBI + U-Boot Proper
      ▼
U-Boot Proper（S-mode）
      │
      ├─ 初始化儲存裝置（SD / eMMC / NVMe）
      ├─ 讀取 /boot/extlinux/extlinux.conf 或 FIT Image
      ├─ 載入 Linux Kernel（Image 或 Image.gz）
      ├─ 載入 DTB（.dtb）
      ├─ 載入 initramfs（可選）
      └─ booti / bootm 啟動 Kernel
```

### 典型啟動指令
```bash
# 從 SD Card 啟動
load mmc 0:1 ${kernel_addr_r} /boot/Image
load mmc 0:1 ${fdt_addr_r} /boot/dtbs/starfive/jh7110-starfive-visionfive-2-v1.3b.dtb
load mmc 0:1 ${ramdisk_addr_r} /boot/initrd.img

booti ${kernel_addr_r} ${ramdisk_addr_r}:${filesize} ${fdt_addr_r}
```

### extlinux.conf（類 GRUB 設定）
```
DEFAULT linux
LABEL linux
  KERNEL /boot/Image
  FDT /boot/dtbs/starfive/jh7110-visionfive2.dtb
  APPEND root=/dev/mmcblk1p4 rw console=ttyS0,115200 earlycon rootwait
```

---

## 5. Linux Kernel 初始化（RISC-V）

### Kernel 進入點
U-Boot 透過 `booti` 命令跳轉至 Kernel，並依照 RISC-V Linux Boot Protocol 傳遞參數：

```
a0 = hartid（執行 Kernel 的 hart ID，通常為 0）
a1 = FDT 位址（Flattened Device Tree，DTB 的記憶體位址）
```

### Kernel Image 格式
```
RISC-V Linux Kernel Image 標頭（64 bytes）
┌────────────────────────────────────────┐
│ jump instruction（跳過 header）        │  8 bytes
│ magic number（0x5643534952 "RISCV"）   │  8 bytes
│ text offset                            │  8 bytes
│ image size                             │  8 bytes
│ flags                                  │  8 bytes
│ version                                │  4 bytes
│ reserved                               │  12 bytes
│ magic2（0x05435352）                   │  4 bytes
│ reserved                               │  4 bytes
└────────────────────────────────────────┘
```

### 早期初始化流程
```
_start（arch/riscv/kernel/head.S）
   │
   ├─ 設定初始頁表（setup_vm）
   ├─ 啟用 MMU（satp 暫存器設定分頁模式）
   ├─ 設定 trap handler（stvec）
   ├─ 呼叫 start_kernel()（init/main.c）
   │
start_kernel()
   ├─ setup_arch()          ← 解析 DTB、初始化記憶體
   ├─ mm_init()             ← 頁面分配器（buddy system）
   ├─ sched_init()          ← CFS 排程器
   ├─ irq_init()            ← PLIC（Platform-Level Interrupt Controller）
   ├─ time_init()           ← CLINT / Timer 驅動
   └─ rest_init()           ← 啟動 kernel thread，呼叫 init 程序
```

### RISC-V 分頁模式（MMU）
```
Sv39（39-bit 虛擬位址，512 GB 空間）← 64-bit Linux 預設
   │  3 層頁表（Page Global Directory → Page Middle Directory → Page Table）

Sv48（48-bit 虛擬位址，256 TB 空間）
   │  4 層頁表

Sv57（57-bit 虛擬位址，128 PB 空間）
   │  5 層頁表（最新規範，部分平台支援）
```

### 中斷控制器架構
```
CLINT（Core Local Interruptor）
   │  軟體中斷（IPI）、計時器中斷
   │  每個 hart 各自有一組

PLIC（Platform-Level Interrupt Controller）
   │  外部中斷（UART、GPIO、NVMe...）
   │  可設定各 hart 的中斷優先權與 mask
```

---

## 6. DTB（Device Tree Blob）在 RISC-V 的角色

RISC-V 平台高度依賴 DTB 描述硬體拓樸，因為 RISC-V 目標是支援各種不同硬體，沒有像 x86 的 ACPI 標準。

### DTB 傳遞鏈
```
FSBL / U-Boot
   │  將 DTB 位址存入 a1 暫存器
   ▼
OpenSBI
   │  可修改 DTB（加入 /chosen 節點，如 bootargs）
   ▼
Linux Kernel
   │  透過 early_init_fdt() 解析 DTB
   ▼
驅動程式
   │  透過 of_*() API 讀取硬體描述
```

### DTB 重要節點範例
```dts
/ {
    cpus {
        cpu@0 {
            compatible = "sifive,u74-mc";
            riscv,isa = "rv64imafdc";
            mmu-type = "riscv,sv39";
        };
    };

    soc {
        plic: interrupt-controller@c000000 {
            compatible = "sifive,plic-1.0.0";
            reg = <0xc000000 0x4000000>;
            riscv,ndev = <53>;
        };

        uart0: serial@10000000 {
            compatible = "ns16550a";
            reg = <0x10000000 0x100>;
            interrupts = <10>;
            interrupt-parent = <&plic>;
        };
    };

    chosen {
        bootargs = "console=ttyS0,115200 root=/dev/mmcblk0p2 rw";
        stdout-path = &uart0;
    };
};
```

---

## 7. initramfs 與 RootFS 掛載

流程與 x86 相同，但注意 RISC-V 平台的儲存驅動：

```
initramfs 載入
   │
   ├─ 載入必要模組：
   │   riscv_sbi.ko（SBI 驅動）
   │   plic.ko（中斷控制器）
   │   sifive_uart.ko / ns16550.ko（序列埠）
   │   dwmac.ko（網路，StarFive 平台）
   │
   ├─ 掛載真正 RootFS（ext4 / XFS / btrfs）
   │
   └─ switch_root → 執行 /sbin/init
```

---

## 8. systemd 與 Userspace

與 x86 Linux 一致，RISC-V 上的現代 Linux 發行版同樣使用 systemd 管理服務。

```bash
# 查看開機 log
journalctl -b
dmesg | grep -i "riscv\|plic\|clint\|sbi"

# 確認 SBI 版本
cat /sys/firmware/devicetree/base/firmware/sbi/compatible
dmesg | grep -i "OpenSBI"
```

---

## 各平台開機流程比較

### QEMU virt（開發/模擬）
```
QEMU 直接載入 fw_jump.bin（OpenSBI）
   │  -bios fw_jump.bin
   ▼
OpenSBI 初始化，跳轉至 U-Boot 或直接跳轉 Kernel
   │  -kernel Image -dtb virt.dtb
   ▼
Linux Kernel（無需真實 Bootloader 鏈）
```

**QEMU 啟動範例：**
```bash
qemu-system-riscv64 \
  -machine virt \
  -cpu rv64 \
  -m 4G \
  -smp 4 \
  -bios /usr/lib/riscv64-linux-gnu/opensbi/qemu/virt/fw_jump.elf \
  -kernel /boot/vmlinuz \
  -initrd /boot/initrd.img \
  -append "root=/dev/vda2 rw console=ttyS0" \
  -drive file=ubuntu-riscv.img,format=raw,id=hd0 \
  -device virtio-blk-device,drive=hd0 \
  -nographic
```

### SiFive HiFive Unmatched
```
ZSBL（ROM）→ FSBL（SPI Flash）→ OpenSBI + U-Boot SPL → U-Boot Proper → Linux
```

### StarFive VisionFive 2
```
ZSBL（ROM）→ SPL（eMMC/SD）→ OpenSBI（fw_dynamic）→ U-Boot Proper → Linux
```

### Milk-V Pioneer（SG2042，64 核心）
```
ZSBL → FSBL → OpenSBI → EDK2（UEFI）→ GRUB → Linux
```

---

## Flash / 儲存裝置 Layout（典型）

```
SD Card / eMMC
┌──────────────────────────────────────────┐  0 MB
│  GPT Header / MBR                        │
├──────────────────────────────────────────┤  1 MB
│  U-Boot SPL + OpenSBI（fw_dynamic.bin）  │  partition 1（raw）
├──────────────────────────────────────────┤  4 MB
│  U-Boot Proper（u-boot.itb）             │  partition 2（raw）
├──────────────────────────────────────────┤  8 MB
│  /boot（ext4）                           │  partition 3
│    ├─ Image（Kernel）                    │
│    ├─ *.dtb                              │
│    └─ initrd.img                         │
├──────────────────────────────────────────┤  512 MB
│  /（RootFS，ext4 / btrfs）              │  partition 4
└──────────────────────────────────────────┘
```

---

## 與其他架構開機流程比較

| 特性 | x86 (UEFI) | ARM (ATF) | RISC-V (OpenSBI) |
|---|---|---|---|
| 韌體規範 | UEFI / PI Spec | PSCI / TF-A | SBI / OpenSBI |
| 最高特權層 | SMM | EL3 | M-mode |
| OS 執行層 | Ring 0 | EL1 | S-mode |
| 硬體描述 | ACPI + SMBIOS | ACPI / DTB | DTB（主要） |
| 標準 Bootloader | GRUB / systemd-boot | U-Boot / GRUB | U-Boot |
| 多核啟動 | ACPI MADT / MP Table | PSCI `CPU_ON` | SBI HSM Extension |
| 安全開機 | Secure Boot（UEFI） | TrustZone / Secure Boot | 尚在發展中 |

---

## 常見除錯方法

### 查看 OpenSBI 資訊
```bash
# 從 dmesg 確認 OpenSBI 版本與功能
dmesg | grep -i "opensbi\|sbi"
# 輸出範例：
# [    0.000000] riscv: base ISA extensions acdfim
# [    0.000000] SBI specification v1.0 detected
# [    0.000000] SBI implementation ID=0x1 Version=0x10004

# 查看支援的 SBI 擴充
cat /proc/cpuinfo | grep isa
```

### UART 序列除錯
```bash
# 在 U-Boot 中透過 UART 觀察
# 連接 USB-to-UART 模組（3.3V）至開發板 Debug UART 腳位
screen /dev/ttyUSB0 115200
# 或
minicom -D /dev/ttyUSB0 -b 115200
```

### 常見開機失敗原因

| 現象 | 可能原因 | 對策 |
|---|---|---|
| UART 無任何輸出 | ZSBL 無法載入 FSBL、SPI Flash 損壞 | 確認 Flash 燒錄、Boot Mode 引腳 |
| OpenSBI 啟動後卡住 | DTB 錯誤、DRAM 初始化失敗 | 確認 DTB 版本相符 |
| U-Boot 找不到 Kernel | 分割區錯誤、檔案系統損壞 | 確認 `bootcmd` 與 partition 設定 |
| Kernel panic: no init | initramfs 損壞、root= 參數錯誤 | 確認 UUID/裝置名 |
| 多核心 hart 無法啟動 | SBI HSM 問題、CLINT 設定錯誤 | 確認 OpenSBI 版本、DTB 的 cpus 節點 |

---

## 參考資料

- [RISC-V SBI Specification](https://github.com/riscv-non-isa/riscv-sbi-doc)
- [OpenSBI GitHub](https://github.com/riscv-software-src/opensbi)
- [Linux RISC-V Boot Protocol](https://www.kernel.org/doc/html/latest/arch/riscv/boot.html)
- [RISC-V Linux Kernel Source - arch/riscv](https://github.com/torvalds/linux/tree/master/arch/riscv)
- [U-Boot RISC-V](https://docs.u-boot.org/en/latest/arch/riscv.html)
- [StarFive VisionFive 2 Software Documentation](https://doc.rvspace.org/)
- [RISC-V Privileged Architecture Spec](https://github.com/riscv/riscv-isa-manual)
