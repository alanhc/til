# 在 BeagleBone Black 上驗證 arm32 kexec，順便修掉一個 cpsw 的 kexec bug

接續[自己編的 Linux 7.3 開機](./bbb-kernel-7.3-bringup.md)：這次要讓 u-root 的 `kexec` 在 32-bit arm 真機上，從一顆 kernel 直接跳進另一顆 kernel，不經過 U-Boot。過程中在 u-root 和 Linux 各抓到一個只有實機才會出現的 bug。

## 背景

u-root 的 arm32 kexec 支援我之前寫過一版（[u-root#3736](https://github.com/u-root/u-root/pull/3736)），單元測試和 CI 全綠，但 u-root 的 AI 政策要求「AI 寫的東西要在自己摸得到的硬體上驗證過」，當時板子上的 Debian kernel 沒開 `CONFIG_KEXEC`，所以自己先關掉了。

現在 kernel 是自己編的，`omap2plus_defconfig` 本來就有 `CONFIG_KEXEC=y`，條件湊齊了。

```bash
grep -E '^CONFIG_(KEXEC|SMP|PM_SLEEP_SMP)=' build-arm/.config     # 三個都是 y，不用重編
```

## 準備：把舊分支接到最新的 main、交叉編譯

```bash
cd ~/u-root
git fetch fork arm32-kexec && git fetch origin main
git log --oneline -2 fork/arm32-kexec        # 6dc15ba arm32 kexec、fc5ff96 zimage 修正（後者已經 merge 成 #3735）
git worktree add -b arm32-kexec-v2 ../u-root-arm32 origin/main
cd ../u-root-arm32 && git cherry-pick 6dc15ba
# 唯一的衝突：load_other_linux.go 的 build tag，main 已經多了 riscv64，合起來：
#   //go:build !amd64 && !arm && !arm64 && !riscv64
git add pkg/boot/linux/load_other_linux.go && git cherry-pick --continue

go test ./pkg/boot/linux/ ./pkg/boot/zimage/
GOARCH=arm GOARM=7 go vet ./pkg/boot/linux/
GOARCH=arm GOARM=7 CGO_ENABLED=0 go build -o ~/bbb-bringup/kexec-arm ./cmds/core/kexec
file ~/bbb-bringup/kexec-arm                  # ELF 32-bit LSB executable, ARM, EABI5, statically linked
```

`GOARCH=arm go vet ./pkg/boot/kexec/` 會報 `memory_map_linux_test.go:77` 常數溢位：那是 main 上原本就有的測試，只在 32-bit 下編得出來，跟這次的改動無關。

## 用法上的兩個坑

- **arm32 沒有 `kexec_file_load`**，u-root 的 `kexec` 預設會先試它，一定要加 `-L` 走 `kexec_load`。
- **不要讓 kexec 碰 SD 卡**。`kexec -l` 會先把 kernel 複製到 `/tmp`，那天剛好觸發 7.3 的 `sdhci-omap` 卡死（`mmc0: Timeout waiting for hardware interrupt`），之後的 SSH 指令全卡在 I/O 上。改成 binary 和 kernel 都放 `/dev/shm`、`TMPDIR=/dev/shm` 就避開了。後來用壓力測試（寫讀 1.3 GB）沒能重現這個 timeout，原因還沒查清楚。

最後穩定下來的做法（[`kexec-test.sh`](https://github.com/alanhc/til/blob/main/static/bbb/kexec-test.sh) 就是把這些串起來，並在 `kexec -e` 後把 serial 上的關鍵行抓出來）：

```bash
# PC：binary 和要跳過去的 kernel 都直接拷進 RAM
scp ~/bbb-bringup/kexec-arm ~/bbb-bringup/tftp/zImage-bringup debian@192.168.10.242:/dev/shm/

# 板子上（root）：先 load，確認 kernel 接受了
cd /dev/shm
sudo env TMPDIR=/dev/shm ./kexec-arm -d -L -l zImage-bringup \
    -c 'console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlycon net.ifnames=0 bringup.boot=kexec-1'
cat /sys/kernel/kexec_loaded                   # 1

# 再 exec；放背景讓 SSH 先回來，結果從 serial log 看
sync; sudo sh -c 'nohup /dev/shm/kexec-arm -e > /dev/shm/kexec-exec.log 2>&1 &'
```

中間的嘗試：

- 第一次照習慣把檔案放在家目錄、帶 `--dtb`（從 build 目錄拿的原始 dtb），結果卡在下面那個 u-root bug。改好之後**拿掉 `--dtb`**，讓 u-root 讀 `/sys/firmware/fdt`，也就是 U-Boot 已經修正過記憶體大小、正在跑的那份 DTB，這也是 LinuxBoot 實際的用法。
- 有一輪 load 一直沒回應，serial 上不停出現 `mmc0: Timeout waiting for hardware interrupt` 和 SDHCI 暫存器 dump：u-root 把 5.7 MB 的 kernel 複製到 SD 上的 `/tmp` 時，`sdhci-omap` 卡死了，SSH 上所有要讀檔的指令都跟著卡住。之後才改成全放 `/dev/shm`。
- 另一輪是我的腳本 bug：用 `bbbssh.sh true` 判斷 SSH 起來沒，但它最後一段是 `grep -v`，輸出為空時結束碼是 1，迴圈永遠不會提早結束。改成 `bbbssh.sh "echo ssh-ok" | grep -q ssh-ok`。

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

修完之後在板子上再 load 一次，記憶體配置就讀對了：

```text
Mem map:
{addr: [0x80000000, 0x8ffe4000), type: System RAM}
{addr: [0x8ffe4000, 0x8fffd000), type: Reserved}
{addr: [0x8fffd000, 0xa0000000), type: System RAM}
zImage decompresses to 0x136f844 bytes (text+data 0x132d250, bss 0x425f4), reserving 0x18ac800
Added 0x56e5b0 byte (size 0x18ac800) kernel at [0x80008000, 0x818bd000) with offset 0x8000
Added 98780 byte device tree at [0x818bd000, 0x818d6000)
Entry: 0x80008000
```

送 PR 前的檢查：

```bash
go test ./pkg/dt/ ./pkg/boot/...
~/go/bin/golangci-lint run ./pkg/dt/... ./pkg/boot/kexec/...
GOARCH=arm GOARM=7 go build ./pkg/dt/ ./pkg/boot/kexec/
```

測試另外做了突變檢查：故意把關鍵行改壞（忽略 cells、`reserved-memory` 子節點誤用 root 的 cells、只解第一組、丟掉高位 cell、拿掉長度檢查、允許 0 個 cell），確認每一種都會讓測試失敗，再還原。

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

```bash
mkdir -p ../build-arm-dbg && cp ../build-arm/.config ../build-arm-dbg/.config
scripts/config --file ../build-arm-dbg/.config --set-str LOCALVERSION "-bringup-dbg" \
    --enable DEBUG_LL --enable DEBUG_AM33XXUART1 --enable DEBUG_UNCOMPRESS --enable EARLY_PRINTK
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- O=../build-arm-dbg olddefconfig
grep -E '^CONFIG_(DEBUG_LL|DEBUG_UART_PHYS|DEBUG_UNCOMPRESS)=' ../build-arm-dbg/.config
#   DEBUG_UNCOMPRESS 沒被設上 → 去看 arch/arm/Kconfig.debug 才知道它要求 !ARCH_MULTIPLATFORM
```

本機 hack（`arch/arm/boot/compressed/Makefile`，用環境變數開關，用完就 `git checkout` 還原）：

```make
ifeq ($(BBB_ZIMAGE_DEBUG),1)
AFLAGS_head.o += -DDEBUG
endif
```

```bash
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- O=../build-arm-dbg BBB_ZIMAGE_DEBUG=1 -j28 zImage
cp ../build-arm-dbg/arch/arm/boot/zImage ~/bbb-bringup/tftp/zImage-dbg
# 第一顆 kernel 照舊，只有 kexec 的目標換成 debug 版
KEXEC_KERNEL=zImage-dbg \
KEXEC_CMDLINE='console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlyprintk net.ifnames=0 bringup.boot=kexec-dbg' \
  ./kexec-test.sh
```

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

```bash
grep -E ' cpsw_driver_init$' ../build-arm-dbg/System.map     # cpsw.c 和 cpsw_new.c 的 initcall 同名，一次擋兩個
KEXEC_KERNEL=zImage-dbg \
KEXEC_CMDLINE='... earlyprintk net.ifnames=0 initcall_blacklist=cpsw_driver_init bringup.boot=kexec-nocpsw' \
  ./kexec-test.sh
# 新 kernel 沒網路，從 serial 登入取證：寫進 logs/tx.fifo 代打帳號密碼和指令
printf 'debian\r' > logs/tx.fifo; printf '<password>\r' > logs/tx.fifo
printf 'uname -a; cat /proc/cmdline; uptime\r' > logs/tx.fifo
```

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

```bash
arm-linux-gnueabihf-addr2line -f -i -e ../build-arm-dbg/vmlinux 0xc0915f30   # cpts_fifo_read, cpts.c:127
grep -n 'devm_request_irq(.*misc_irq\|misc_en' drivers/net/ethernet/ti/cpsw_new.c drivers/net/ethernet/ti/cpsw_priv.c
grep -n 'INIT_LIST_HEAD(&cpts->pool)' drivers/net/ethernet/ti/cpts.c          # 在 cpts_register() 裡
```

先確認上游沒人修過：lore 有防機器人驗證，curl 查不到（「查不到」不能當成「沒人修」），改直接抓 netdev 的樹看 rc7 之後有沒有相關 commit：

```bash
git fetch https://git.kernel.org/pub/scm/linux/kernel/git/netdev/net.git main:refs/remotes/netdev/net
git log --oneline v7.3-rc7..netdev/net -- drivers/net/ethernet/ti/cpsw*.c drivers/net/ethernet/ti/cpts.c
```

修正以 `net` 樹為基底，另開一個 worktree。本機樹是淺層歷史，找 `Fixes:` 的目標要用 GitHub API 把 `cpsw_new.c` 的 67 個 commit 一個個翻：

```bash
gh api "repos/torvalds/linux/commits?path=drivers/net/ethernet/ti/cpsw_new.c&per_page=100" --jq '.[].sha' |
tac | while read s; do
  gh api "repos/torvalds/linux/commits/$s" \
    --jq '.files[] | select(.filename=="drivers/net/ethernet/ti/cpsw_new.c") | .patch' |
  grep -qE '^\+.*(misc_irq|cpsw_misc_interrupt|misc_en)' &&
  gh api "repos/torvalds/linux/commits/$s" --jq '"\(.sha[0:12]) \(.commit.message|split("\n")[0])"'
done
# 84ea9c0a95d7 net: ethernet: ti: cpsw: enable cpts irq          ← probe 時 request misc IRQ
# 2b5668733050 net: ethernet: ti: cpsw: fix cpts irq after suspend ← 把 misc_en=0x10 移到 ndo_open
```

### 修了四次才對

| 版本 | 做法 | 結果 | 學到什麼 |
|---|---|---|---|
| 1 | probe 時、`request_irq` 前把 wrapper 的 `misc_en` 清 0 | 一樣 oops | 中斷早就被記下了，而且 `cpsw_misc_interrupt()` 結尾會自己再寫 `misc_en = 0x10` |
| 2 | `cpts_create()` 裡把 CPTS 停掉（`control = 0`） | 一樣 oops | handler 的 `cpts_fifo_pop()` 成功了，代表停掉 CPTS 不會清空 FIFO |
| 3 | 遮中斷、把 FIFO pop 乾淨、再停掉 CPTS，並印出暫存器 | 一樣 oops | 見下 |
| 4 | 遮中斷、把 FIFO pop 乾淨，**不停 CPTS** | 成功 | |

每一版的改法、建置和測試流程都一樣：

```bash
cd ~/bbb-bringup/linux-cpsw          # net 樹的 worktree
make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- O=../build-cpsw -j28 zImage W=1
cp ../build-cpsw/arch/arm/boot/zImage ~/bbb-bringup/tftp/zImage-cpswfix
touch ~/bbb-bringup/logs/break.flag
# 第一顆用沒修的 kernel 冷開機，kexec 進修正版，這次不擋 cpsw
KERNEL=zImage-bringup DTB=am335x-boneblack-bringup.dtb INITRD= ./tftpboot.sh
KEXEC_KERNEL=zImage-cpswfix KEXEC_CMDLINE='... earlyprintk net.ifnames=0 bringup.boot=kexec-cpswfixN' ./kexec-test.sh
ping -c1 192.168.10.242
```

第 1 版，`cpsw_new.c` probe：

```c
	writel(0, &cpsw->wr_regs->misc_en);	/* 加在 devm_request_irq(misc_irq) 前 */
```

第 2 版，`cpts_create()`：

```c
	cpts_write32(cpts, 0, int_enable);
	cpts_write32(cpts, 0, control);
```

第 3 版，`cpts_create()`，同時印出狀態（診斷輸出只放在 debug build）：

```c
	u32 c0 = cpts_read32(cpts, control);
	u32 e0 = cpts_read32(cpts, int_enable);
	u32 r0 = cpts_read32(cpts, intstat_raw);

	cpts_write32(cpts, 0, int_enable);
	for (i = 0; i < CPTS_FIFO_DEPTH; i++) {
		if (!(cpts_read32(cpts, intstat_raw) & TS_PEND_RAW))
			break;
		cpts_write32(cpts, EVENT_POP, event_pop);
	}
	cpts_write32(cpts, 0, control);
	dev_info(dev, "BBB-DEBUG cpts_create: control=%#x int_enable=%#x intstat_raw=%#x, dropped %d, intstat_raw now %#x\n",
		 c0, e0, r0, i, cpts_read32(cpts, intstat_raw));
```

第 4 版就是把第 3 版的 `cpts_write32(cpts, 0, control);` 拿掉，診斷輸出顯示 `intstat_raw now 0x0`、沒有 oops。

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

`Fixes` 的目標就是上面用 GitHub API 翻出來的 `84ea9c0a95d7`。

最終版的驗證，一次上電測兩種情況：U-Boot 直接 TFTP 冷開機修正版（確認對正常開機沒有副作用），再從它 kexec 進同一顆：

```bash
KERNEL=zImage-cpswfinal DTB=am335x-boneblack-bringup.dtb INITRD= \
  BOOTARGS='... earlycon net.ifnames=0 bringup.boot=cold-cpswfinal' ./tftpboot.sh
./bbbssh.sh 'uname -r; ip -4 -br addr show eth0; cat /sys/class/ptp/ptp0/clock_name'
KEXEC_KERNEL=zImage-cpswfinal KEXEC_CMDLINE='... bringup.boot=kexec-cpswfinal' ./kexec-test.sh
sudo python3 ptpread.py      # 讀三次 /dev/ptp0，每 0.5 秒要前進約 0.5 秒
```

[`ptpread.py`](https://github.com/alanhc/til/blob/main/static/bbb/ptpread.py) 用 `clock_gettime((~fd << 3) | 3)` 直接讀 PHC。

整理成 patch：

```bash
git checkout -b cpts-kexec-stale-events
git commit -F msg.txt                                    # 不加 -s：Signed-off-by 要送出者自己加
git format-patch -1 --subject-prefix='PATCH net' -o ../outgoing-cpts/
./scripts/checkpatch.pl --strict ../outgoing-cpts/*.patch
./scripts/get_maintainer.pl --nogit --nogit-fallback ../outgoing-cpts/*.patch
grep -n 'TI ETHERNET SWITCH DRIVER (CPSW)' -A8 MAINTAINERS   # cpts.c 不在 F: pattern 裡，reviewer 要自己補
```

checkpatch 剩下的三項都是預期內的：引用 oops 的長行（引用 log 不折行）、淺層樹查不到 `84ea9c0a95d7`、缺 `Signed-off-by`（由送出者加）。寄之前先 `git send-email --dry-run` 確認收件人。

## 送 kernel patch 時的 AI 規定（2026-10 的現況）

讀規定要讀**你要送的那棵樹**裡的版本。v7.3-rc7 的 `Documentation/process/coding-assistants.rst` 還要求加 `Assisted-by:`，但 `net` 樹已經合了 `1e035297ff`（2026-10-13）：

- **`Assisted-by` 標記取消了**，checkpatch 也不再認它。工具怎麼用的改寫在 cover letter 或 patch 的 `---` 下方。
- **AI 不能加 `Signed-off-by`**，DCO 只能由人簽；**AI 不能自己寄出**。這兩條沒變。
- 依 `threat-model.rst`，要 root 才觸發得了的 oops（kexec 需要 `CAP_SYS_BOOT`）是一般 bug，照一般流程寄 netdev。

另外 `get_maintainer.pl` 在淺層樹上會把一個巨大 merge commit 的作者算成 commit signer，要加 `--nogit --nogit-fallback`；`cpts.c` 不在 MAINTAINERS 的 `cpsw*` pattern 裡，TI 的 reviewer、`linux-omap`、PTP 維護者和 `Fixes` 的作者要自己補 Cc。

## 還沒解的

- kexec 目標換成**沒有 DEBUG_LL** 的 kernel 時，`Bye!` 之後完全沒有輸出；debug 版一切正常，差在哪還沒查。
- 7.3 `sdhci-omap` 的 timeout 沒能重現。用 [`sdstress.sh`](https://github.com/alanhc/til/blob/main/static/bbb/sdstress.sh) 跑了 20 輪（每輪複製 5 次 5.7 MB 的 kernel，再寫入 64 MB + `fsync`、清 page cache、讀回），總共約 1.3 GB，0 次 timeout：

  ```bash
  sudo sh -c 'N=20 MB=64 nohup sh /dev/shm/sdstress.sh > /dev/shm/sdstress.log 2>&1 &'
  tail /dev/shm/sdstress.log      # iter N done in ~13s timeouts=0
  ```
- 那天 BBB 的 console 好幾次出現 `sysrq: HELP ...` 和亂碼：UART RX 收到雜訊被當成 serial break，比較可能是杜邦線接觸不穩。
