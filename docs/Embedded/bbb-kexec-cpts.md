# 在 BeagleBone Black 上驗證 arm32 kexec，順便修掉一個 cpsw 的 kexec bug

接續[自己編的 Linux 7.3 開機](./bbb-kernel-7.3-bringup.md)：這次要讓 u-root 的 `kexec` 在 32-bit arm 真機上，從一顆 kernel 直接跳進另一顆 kernel，不經過 U-Boot。過程中在 u-root 和 Linux 各抓到一個只有實機才會出現的 bug。

## 背景

u-root 的 arm32 kexec 支援我之前寫過一版（[u-root#3736](https://github.com/u-root/u-root/pull/3736)），單元測試和 CI 全綠，但 u-root 的 AI 政策要求「AI 寫的東西要在自己摸得到的硬體上驗證過」，當時板子上的 Debian kernel 沒開 `CONFIG_KEXEC`，所以自己先關掉了。

現在 kernel 是自己編的，`omap2plus_defconfig` 本來就有 `CONFIG_KEXEC=y`，條件湊齊了。

## 用法上的兩個坑

- **arm32 沒有 `kexec_file_load`**，u-root 的 `kexec` 預設會先試它，一定要加 `-L` 走 `kexec_load`。
- **不要讓 kexec 碰 SD 卡**。`kexec -l` 會先把 kernel 複製到 `/tmp`，那天剛好觸發 7.3 的 `sdhci-omap` 卡死（`mmc0: Timeout waiting for hardware interrupt`），之後的 SSH 指令全卡在 I/O 上。改成 binary 和 kernel 都放 `/dev/shm`、`TMPDIR=/dev/shm` 就避開了。後來用壓力測試（寫讀 1.3 GB）沒能重現這個 timeout，原因還沒查清楚。

```bash
kexec -d -L -l zImage -c 'console=ttyS0,115200n8 root=/dev/mmcblk0p3 ... '
kexec -e
```

## u-root 的 bug：32-bit 的 `#address-cells`

第一次 `kexec -l` 直接失敗：

```text
memoryMapFromFDT(...): property value is not <u64x2>
```

`pkg/dt` 的 `Property.AsRegion()` 寫死 `reg` 一定是 16 bytes（64-bit address + 64-bit size）。arm64、riscv64 都是這樣，所以從沒出事；但 32-bit arm 的 device tree 是

```dts
#address-cells = <1>;
#size-cells = <1>;
memory@80000000 { device_type = "memory"; reg = <0x80000000 0x20000000>; };
```

`reg` 只有 8 bytes。修法是加一個依照父節點 cell 數解析的 `AsRegions(addressCells, sizeCells)`，`/memory` 用 root 的 cells、`reserved-memory` 的子節點用它自己的 cells；父節點沒寫 cells 時維持舊行為，現有測試不用改。送成 [u-root#3813](https://github.com/u-root/u-root/pull/3813)，arm32 kexec 疊在上面重送成 [u-root#3814](https://github.com/u-root/u-root/pull/3814)。

## 跳過去之後一片安靜：讓黑箱說話

修好之後 load 成功（`/sys/kernel/kexec_loaded` = 1），`kexec -e` 印出

```text
kexec_core: Starting new kernel
Bye!
```

然後就什麼都沒有了，連新 kernel 的 `earlycon` 都沒印。這時候猜原因沒有意義，該做的是**讓看不見的那一段有輸出**：另外編一顆只當 kexec 目標的 debug kernel。

- `CONFIG_DEBUG_LL` + `CONFIG_DEBUG_AM33XXUART1`：直接寫 UART0 暫存器，不需要 driver 也不需要 DTB。
- cmdline 加 `earlyprintk`：`setup_arch` 一開始就把 printk 從 DEBUG_LL 送出去；DTB 指標錯的話 `arch/arm/kernel/head.S` 也會直接印錯誤。
- decompressor 的除錯輸出：`DEBUG_UNCOMPRESS` 要求 `!ARCH_MULTIPLATFORM`，omap2plus 選不了。但 `arch/arm/boot/compressed/head.S` 在 `#ifdef DEBUG` 下有自己的 `putc`/`phex`，本機給 `head.o` 加 `-DDEBUG` 就會印出搬移位址（這是只放在自己 build 的 hack，不要 commit）。

結果整條路都看到了：

```text
kexec_core: Starting new kernel / Bye!
C:0x800080E0-0x80576320->0x81335F00-0x818A4140     ← decompressor 把自己搬開
Booting Linux on physical CPU 0x0
OF: fdt: Machine model: TI AM335x BeagleBone Black  ← r2 指的 DTB 正確
Kernel command line: ... bringup.boot=kexec-dbg      ← u-root 帶的 cmdline
...
Internal error: Oops: 805 [#1] SMP ARM               ← 開機 2 秒後
PC is at cpts_fifo_read+0xa4/0x3c8
```

`C:` 那行也順便驗證了 u-root 照 kexec-tools 算的 zImage 保留大小：decompressor 加上 stack 與 malloc 大約用到 `0x818B5000`，DTB 放在 `0x818BD000`，沒被蓋到，餘裕約 32 KiB。

用 `initcall_blacklist=cpsw_driver_init` 擋掉網卡 driver 後，kexec 後的 kernel 一路開到 login，`uname -r` 和 `/proc/cmdline` 都是新的。u-root 這邊的驗證到此完成。

## Linux 的 bug：cpsw CPTS 在 kexec 後 NULL deref

```text
Unable to handle kernel NULL pointer dereference at virtual address 00000010 when write
 cpts_fifo_read from cpsw_misc_interrupt
 ...
 __setup_irq from request_threaded_irq
```

backtrace 最底下是 `request_threaded_irq`：中斷在 **probe 註冊 IRQ 的當下**就進來了。

- cpsw 在 probe 時就 `request_irq` 了 misc IRQ（CPTS 事件中斷走這條）。
- CPTS 的事件 `pool` list 要到 `ndo_open` 呼叫 `cpts_register()` 才 `INIT_LIST_HEAD`。
- 冷開機時 CPTS 剛 reset，中斷是關的，這個順序沒問題。kexec 不會 reset 硬體，舊 kernel 留下的 CPTS 還開著中斷、FIFO 裡還有事件，所以一註冊就進 handler，從空的 `pool` 拿 entry，寫到位址 0x10。

### 修了四次才對

| 版本 | 做法 | 結果 | 學到什麼 |
|---|---|---|---|
| 1 | probe 時、`request_irq` 前把 wrapper 的 `misc_en` 清 0 | 一樣 oops | 中斷早就被記下了，而且 `cpsw_misc_interrupt()` 結尾會自己再寫 `misc_en = 0x10` |
| 2 | `cpts_create()` 裡把 CPTS 停掉（`control = 0`） | 一樣 oops | handler 的 `cpts_fifo_pop()` 成功了，代表停掉 CPTS 不會清空 FIFO |
| 3 | 遮中斷、把 FIFO pop 乾淨、再停掉 CPTS，並印出暫存器 | 一樣 oops | 見下 |
| 4 | 遮中斷、把 FIFO pop 乾淨，**不停 CPTS** | 成功 | |

第 3 版加的診斷輸出是轉捩點：

```text
cpts_create: control=0x1 int_enable=0x1 intstat_raw=0x1, dropped 1, intstat_raw now 0x1
```

kexec 後 CPTS 確實還在跑、中斷開著、FIFO 裡有 1 個事件；pop 一次就清空了，但**清 `CPTS_EN` 之後 `TS_PEND_RAW` 又讀回 1**，handler 拿到一個假事件照樣 crash。前兩版都是靠推論，每猜錯一次就要拔一次電；從第 3 版改成先把數字印出來，第 4 版就對了。

最終修正放在 `cpts_create()`（cpsw 新舊兩個 driver 共用）：

```c
	cpts_write32(cpts, 0, int_enable);
	for (i = 0; i < CPTS_FIFO_DEPTH; i++) {
		if (cpts_fifo_pop(cpts, &high, &low))
			break;
	}
```

用要送出的那份程式碼再測一次：冷開機正常；kexec（未修正 → 修正、修正 → 修正）都不再 oops，`eth0` 連線、ping 通，`/dev/ptp0` 時間會前進（讀 PTP 時間要靠 CPTS 事件經中斷送回來，所以中斷路徑也是好的）。整理成 `[PATCH net] net: ethernet: ti: cpts: drop stale events before the misc IRQ can fire`，`Fixes: 84ea9c0a95d7`。

`Fixes` 的目標是用 GitHub 上 torvalds/linux 的歷史一個個 commit 查出來的：本機 kernel 樹是淺層歷史，查不到 2020 年的 commit。

## 送 kernel patch 時的 AI 規定（2026-10 的現況）

讀規定要讀**你要送的那棵樹**裡的版本。v7.3-rc7 的 `Documentation/process/coding-assistants.rst` 還要求加 `Assisted-by:`，但 `net` 樹已經合了 `1e035297ff`（2026-10-13）：

- **`Assisted-by` 標記取消了**，checkpatch 也不再認它。工具怎麼用的改寫在 cover letter 或 patch 的 `---` 下方。
- **AI 不能加 `Signed-off-by`**，DCO 只能由人簽；**AI 不能自己寄出**。這兩條沒變。
- 依 `threat-model.rst`，要 root 才觸發得了的 oops（kexec 需要 `CAP_SYS_BOOT`）是一般 bug，照一般流程寄 netdev。

另外 `get_maintainer.pl` 在淺層樹上會把一個巨大 merge commit 的作者算成 commit signer，要加 `--nogit --nogit-fallback`；`cpts.c` 不在 MAINTAINERS 的 `cpsw*` pattern 裡，TI 的 reviewer、`linux-omap`、PTP 維護者和 `Fixes` 的作者要自己補 Cc。

## 還沒解的

- kexec 目標換成**沒有 DEBUG_LL** 的 kernel 時，`Bye!` 之後完全沒有輸出；debug 版一切正常，差在哪還沒查。
- 7.3 `sdhci-omap` 的 timeout 沒能重現。
- 那天 BBB 的 console 好幾次出現 `sysrq: HELP ...` 和亂碼：UART RX 收到雜訊被當成 serial break，比較可能是杜邦線接觸不穩。
