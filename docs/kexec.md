# kexec：讓 Linux kernel 自己當 bootloader

> TL;DR：kexec 讓一個正在執行的 Linux kernel 直接載入並跳進另一個 kernel，跳過韌體與 bootloader。它是 kdump 的基礎，也是 LinuxBoot 這類「用 Linux 當韌體」方案的核心。代價是硬體不會被韌體重置，driver 的 shutdown 路徑寫得好不好會直接決定成敗。

## 1. 為什麼需要 kexec

一般的開機流程大致是：

```
Power on → Boot ROM → 韌體 (UEFI / BIOS / TF-A + U-Boot) → Bootloader → Linux kernel → init
```

重開機時整條路要重走一次。在伺服器上，韌體階段（POST、記憶體訓練、PCIe 列舉、option ROM）常常就要數分鐘。

kexec 的做法是把這條路短路掉：

```
舊 kernel ──(kexec)──> purgatory ──> 新 kernel → init
```

新 kernel 由舊 kernel 直接放進記憶體並跳入，韌體完全不參與。

## 2. 兩個 syscall

kexec 在 userspace 的入口是兩個 syscall，以下資訊出自 `kexec_load(2)` man page [1]：

| | `kexec_load()` | `kexec_file_load()` |
|---|---|---|
| 首次出現 | Linux 2.6.13 | Linux 3.17 |
| 輸入 | userspace 自己切好的記憶體 segment 陣列 | kernel image 與 initrd 的 file descriptor，加上 cmdline |
| 誰負責解析 image | userspace（kexec-tools） | kernel 自己 |
| 簽章驗證 | 無法由 kernel 驗證 | 可以（見第 7 節） |

兩者都可以帶 crash 相關的 flag（`KEXEC_ON_CRASH` / `KEXEC_FILE_ON_CRASH`），表示這次載入的是 panic 時要用的 capture kernel，而非一般重開機用的 kernel [1]。

目前載入狀態可以從 sysfs 查：

```bash
cat /sys/kernel/kexec_loaded        # 一般 kexec 是否已載入
cat /sys/kernel/kexec_crash_loaded  # crash kernel 是否已載入
```

`kexec_file_load()` 的設計動機很直接：`kexec_load()` 讓 userspace 決定要往記憶體哪裡寫什麼，kernel 無從驗證內容，在 Secure Boot 環境下等於開了一個執行任意 kernel code 的後門。改由 kernel 自己讀檔、自己解析，才有辦法在中間插入簽章驗證。

## 3. 執行流程

整體可以拆成「載入」和「切換」兩段。

**載入階段**發生在系統正常運作時。kernel image、initrd、cmdline（ARM64 還有 device tree）被放進記憶體中的若干 segment，另外還有一小段叫 **purgatory** 的程式碼。這時什麼都還沒發生，舊 kernel 照常跑。

**切換階段**由 `reboot(LINUX_REBOOT_CMD_KEXEC)` 觸發 [1]，大致步驟是：

1. 呼叫各 driver 的 shutdown callback，讓裝置停止活動。
2. 停掉其他 CPU，只留一顆。
3. 進入架構相關的 `machine_kexec()`，關閉 MMU／切換到 identity mapping，把 segment 搬到最終位置（載入時的暫存位置不一定就是目標位置）。
4. 跳進 purgatory。purgatory 會檢查各 segment 的 SHA-256，確認搬移過程沒有被破壞，然後設定好新 kernel 期望的暫存器狀態並跳到它的 entry point。

之所以叫 purgatory（煉獄），是因為它夾在兩個 kernel 之間，不屬於任何一邊。

在 ARM64 上，新 kernel 看到的 CPU 狀態必須符合 `booting.rst` 描述的開機協定 [2]，例如 MMU 關閉、`x0` 指向 device tree。另外 secondary CPU 需要能被正確關掉再重新帶起來，實務上這仰賴 PSCI（Power State Coordination Interface）；平台若沒有正確實作 PSCI 的 CPU off，kexec 在多核心上會卡住。這一點是依據 ARM64 開機協定與 CPU hotplug 的機制推論出的常見失敗原因，實際表現視平台而定。

## 4. 實際操作：kexec-tools

userspace 工具是 `kexec-tools` [3]：

```bash
# 載入新 kernel，沿用目前的 cmdline
kexec -l /boot/vmlinuz --initrd=/boot/initrd.img --reuse-cmdline

# 使用 kexec_file_load()（可配合簽章驗證）
kexec -s -l /boot/vmlinuz --initrd=/boot/initrd.img --reuse-cmdline

# 立即切換，不經過 init 的正常關機流程
kexec -e

# 卸載已載入的 kernel
kexec -u
```

`kexec -e` 會直接切換，不會先停服務、卸載檔案系統。在 systemd 系統上比較安全的做法是 `systemctl kexec` [4]，它會先走完正常的 shutdown 流程，最後才執行 kexec。

## 5. kdump：kexec 最重要的用途

kdump 是 kexec 最廣泛的應用，官方文件見 [5]。概念是：

1. 開機時透過 kernel 參數 `crashkernel=` 預留一塊記憶體，例如 `crashkernel=256M`。
2. 系統起來後，用 `kexec -p` 把一個 capture kernel 載入這塊預留區。
3. 主 kernel panic 時，不重開機，而是直接 kexec 進 capture kernel。
4. capture kernel 只使用預留區，所以主 kernel 當下的記憶體內容完整保留，並以 ELF 格式透過 `/proc/vmcore` 暴露出來。
5. 用 `cp` 或 `makedumpfile`（可過濾、壓縮）把 vmcore 存下來，之後用 `crash` 工具分析。

```bash
# 載入 capture kernel
kexec -p /boot/vmlinuz --initrd=/boot/initrd-kdump.img \
      --append="irqpoll nr_cpus=1 reset_devices"

# 在 capture kernel 中
makedumpfile -l -d 31 /proc/vmcore /var/crash/vmcore
```

`reset_devices`、`irqpoll`、`nr_cpus=1` 這類參數存在的理由，正是因為 panic 當下的硬體狀態不可預期，capture kernel 需要盡量保守地初始化裝置 [5]。

## 6. LinuxBoot：用 Linux 取代韌體

另一個有趣的應用是 LinuxBoot [6]。它把一個精簡的 Linux kernel 加上 userspace（常見的是用 Go 寫的 u-root [7]）放進 SPI flash，取代 UEFI 的 DXE 以後大部分階段。這個小 Linux 負責初始化硬體、找出要開的 OS，最後用 kexec 跳過去。

好處是：

- 用 Linux driver 取代韌體 driver，程式碼可審查、可除錯、可更新。
- 開機流程可以用一般的 Linux 工具（網路、檔案系統、加密）撰寫。

這套做法在 OCP（Open Compute Project）與大型資料中心的伺服器韌體圈很活躍，和 OpenBMC 屬於同一個「把封閉韌體換成開源 Linux」的脈絡。更早期類似概念的還有 petitboot（常見於 POWER 平台）。

## 7. 安全性

kexec 本質上就是「以 kernel 權限執行任意程式碼」，所以在強調信任鏈的系統上必須受限：

- **Kernel lockdown**：lockdown 模式啟用時，`kexec_load()` 會被禁止，只剩 `kexec_file_load()` 可用，且會要求 image 通過簽章驗證 [8]。
- **`CONFIG_KEXEC_SIG`**：讓 `kexec_file_load()` 驗證 kernel image 的簽章。
- **`kernel.kexec_load_disabled`**：sysctl，設為 1 後就無法再載入 kexec image，而且這個設定是單向的，設了就不能改回來，適合在開機完成後鎖死。

```bash
sysctl -w kernel.kexec_load_disabled=1
```

## 8. 常見陷阱

**裝置狀態殘留**是 kexec 最大的麻煩。正常重開機時韌體會重置硬體，kexec 不會。只要有 driver 的 `.shutdown` 沒把裝置停乾淨，就可能出現：

- 還在跑的 DMA 寫進新 kernel 的記憶體，造成隨機的記憶體破壞。
- 中斷在新 kernel 還沒準備好時就觸發。
- GPU、NIC 等有內部韌體的裝置停在舊 kernel 設定的狀態，新 driver probe 失敗。
- IOMMU 保留舊的 mapping 設定。

**韌體介面的交接**也要注意。在 UEFI 系統上，EFI runtime service 的 mapping 必須在兩個 kernel 之間保持一致；ARM64 上則要把 device tree（或 ACPI table 的位置）正確傳遞下去。

**除錯困難**：kexec 失敗時，常常是新 kernel 連 early console 都還沒起來就死了，畫面一片空白。這時可以先確認新 kernel 開了 `earlycon`，並檢查舊 kernel 的 shutdown 階段 log。

## 9. 在嵌入式與 Android 上

以下為推論，非來自官方文件。

在 x86 伺服器上，kexec 與 kdump 已經是成熟的標準配備。但在 SoC 與嵌入式平台上，kexec 的可用性很依賴 BSP 品質：driver 的 shutdown callback 常被假設成之後會斷電，而 kexec 之後會立刻重新 probe 同一個裝置，兩者的前提不同，就容易露出問題。

Android 量產裝置一般不會依賴 kexec，一方面是 Verified Boot 的信任鏈是從 bootloader 一路建立起來的，kexec 會繞過這條鏈；另一方面 Android 生態有自己的 crash 收集機制（例如 ramoops/pstore 搭配 bootloader 的 ramdump）。不過在 bring-up 或 kernel 開發階段，kexec 仍可以當作不必重刷 boot image 就快速換 kernel 測試的手段。

## 參考資料

1. `kexec_load(2)` — Linux manual page. [https://man7.org/linux/man-pages/man2/kexec_load.2.html](https://man7.org/linux/man-pages/man2/kexec_load.2.html)
2. Booting AArch64 Linux — The Linux Kernel documentation. [https://docs.kernel.org/arch/arm64/booting.html](https://docs.kernel.org/arch/arm64/booting.html)
3. kexec-tools source repository. [https://git.kernel.org/pub/scm/utils/kernel/kexec/kexec-tools.git](https://git.kernel.org/pub/scm/utils/kernel/kexec/kexec-tools.git)
4. `systemctl(1)` — systemd manual. [https://www.freedesktop.org/software/systemd/man/latest/systemctl.html](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
5. Documentation for Kdump — The kexec-based Crash Dumping Solution. [https://docs.kernel.org/admin-guide/kdump/kdump.html](https://docs.kernel.org/admin-guide/kdump/kdump.html)
6. LinuxBoot. [https://www.linuxboot.org/](https://www.linuxboot.org/)
7. u-root. [https://github.com/u-root/u-root](https://github.com/u-root/u-root)
8. `kernel_lockdown(7)` — Linux manual page. [https://man7.org/linux/man-pages/man7/kernel_lockdown.7.html](https://man7.org/linux/man-pages/man7/kernel_lockdown.7.html)
