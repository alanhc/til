---
title: "在 QEMU 上從原始碼拼出完整 Secure Boot 鏈：TF-A + OP-TEE + TA 實作紀錄"
date: 2026-11-05
tags: [TF-A, OP-TEE, QEMU, TrustZone, BL31, BL32, PSCI, TA, xtest, AArch64, Firmware]
description: "不用 OP-TEE build repo，而是分別從原始碼 build TF-A、OP-TEE OS、optee_client、optee_test 和 kernel，拼成 BL1→BL2→BL31→BL32→BL33 五段開機鏈並跑完 xtest。記錄只有自己動手才會遇到的九個坑：QEMU -S 被探測連線破壞、secure UART 看不到輸出、U-Boot 搬不動大 kernel、initramfs 沒有 /dev/console、cross-compile xtest 的 header 與 linker 問題。"
---

# 在 QEMU 上從原始碼拼出完整 Secure Boot 鏈

> **系列文章**：[（一）TF-A](./tf-a.md) ｜ [（二）OP-TEE](./optee.md) ｜ [（三）U-Boot](./u-boot.md) ｜ **實作篇（本文）**
>
> 前三篇是對照 upstream 原始碼的概念與架構。這篇是動手的部分：**不走 [OP-TEE build repo](https://github.com/OP-TEE/build) 的 `make -f qemu_v8.mk`**，而是五個元件各自從原始碼 build 起來再接在一起。

## TL;DR

- OP-TEE 官方的 `build` repo 一條指令就能跑起 QEMU v8 環境，**但它把所有接縫都藏起來了**。自己拼一次才會知道每個 build 參數在解決什麼問題。
- 最後的成果：`BL1 → BL2 → BL31 → BL32(OP-TEE) → BL33(Linux)` 五段開機鏈，normal world 跑 `xtest`，**10608 個 subtest 全過**。
- 九個坑裡，只有兩個跟 TrustZone 概念有關（secure UART、world switch 的方向判斷）；**其餘七個都是 build system 與 QEMU 的操作細節**——而這些恰好是文件不會寫的部分。
- 最反直覺的一個：**用 `/dev/tcp` 或 `nc` 探測 QEMU 的 gdb port，會讓 `-S` 失效**。因為那個探測本身就是一個 debug 連線。

## 為什麼不用官方的 build repo

OP-TEE 的 `build` repo 很好用，`make -f qemu_v8.mk run` 就有一個可以玩的環境。但它用 repo manifest 抓十幾個 tree、用自己的 makefile 把參數組好，**你看不到 TF-A 的 `SPD=opteed` 是怎麼跟 OP-TEE 的三個 binary 對應的**，也不會知道為什麼 kernel 要特別處理。

想真正熟悉 TF-A，自己接一次的學習效率高得多。代價是會撞上一堆官方流程已經幫你繞過的問題——而那些問題才是這篇的主體。

## 整體結構

五個元件，依相依順序：

| 元件 | 角色 | 產出 |
|---|---|---|
| `optee_os` | BL32，S-EL1 的 Trusted OS | `tee-header_v2.bin` + `tee-pager_v2.bin` + `tee-pageable_v2.bin`，以及 TA dev kit |
| `optee_client` | normal world 的 userspace | `libteec`（CA 連結用）、`tee-supplicant`（服務 secure world 的 RPC） |
| `optee_test` | 測試 | `xtest` 與 21 個 TA |
| `linux` | BL33 | `Image`（含內建 cmdline 與 initramfs） |
| `arm-trusted-firmware` | BL1/BL2/BL31 + 打包 | `qemu_fw.bios` |

TF-A 要放在最後，因為 FIP 要把 OP-TEE 和 kernel 都包進去：

```bash
make -j$(nproc) PLAT=qemu CROSS_COMPILE=aarch64-linux-gnu- DEBUG=1 \
  SPD=opteed BL32_RAM_LOCATION=tdram ARM_LINUX_KERNEL_AS_BL33=1 \
  BL32=$OUT/optee-os/core/tee-header_v2.bin \
  BL32_EXTRA1=$OUT/optee-os/core/tee-pager_v2.bin \
  BL32_EXTRA2=$OUT/optee-os/core/tee-pageable_v2.bin \
  BL33=$OUT/linux/arch/arm64/boot/Image \
  all fip
```

`BL32` 要三個檔案，是因為 OP-TEE 的 image 本身就是分段的：header、常駐的 pager 部分、可換頁的部分。它們在 FIP 裡是三個獨立的 image ID（4、21、22）。

## 坑 1：兩種互斥的開機方式

TF-A 的 QEMU port 有兩種載入方式，而**混用會安靜地 hang 住，沒有任何輸出**：

- **semihosting**：`-bios bl1.bin`，其餘 image 從 QEMU 的工作目錄載入。
- **flash**：`-bios qemu_fw.bios`，build 時已經把 `bl1.bin` 和 `fip.bin` 串接好，整包放在 secure FLASH0。

我第一次用 `-bios bl1.bin` 但 build 的是 flash 流程，結果就是黑畫面。`docs/plat/qemu.rst` 寫得很清楚，這是我沒先讀文件的代價。後來固定用 flash：

```bash
qemu-system-aarch64 -machine virt,secure=on -cpu cortex-a57 -smp 2 -m 3072 \
  -no-reboot -bios qemu_fw.bios -display none \
  -serial chardev:ns -serial chardev:sec
```

## 坑 2：secure world 的輸出在第二個 UART

OP-TEE 跑起來了，但 console 上什麼都沒有。排查方式是把 QEMU 產生的 DTB dump 出來看：

```bash
dtc -I dtb -O dts virt.dtb | grep -A5 'pl011@9040000'
```

結果：

```
pl011@9040000 {
    secure-status = "okay";
    status = "disabled";      ← normal world 看不到這個裝置
};
```

QEMU `virt` 有兩個 pl011。第二個在 `0x09040000`，被標成「secure 可用、normal 停用」——**而 OP-TEE 就是印在這一個上面**（`optee_os/core/arch/arm/plat-vexpress/platform_config.h` 裡 `CONSOLE_UART_BASE` 指向 `UART1_BASE`）。

所以要兩個 `-serial`。只給一個的話，secure world 永遠是沉默的，而你會誤以為 OP-TEE 沒跑起來。

> TF-A 自己的 boot console 是 UART0（`PLAT_QEMU_BOOT_UART_BASE`），所以 TF-A 的 `NOTICE:` 訊息跟 Linux 一起出現在第一個 serial；只有 OP-TEE 在第二個。這兩件事很容易搞混。

## 坑 3：探測 gdb port 會讓 `-S` 失效

要用 GDB 走開機鏈，得讓 QEMU 停在第一條指令：`-s -S`。但我連上去之後 `$pc` 不是 0，看起來像是 `-S` 被忽略了。

原因是我在連 GDB 之前，先用這種方式確認 port 開了沒：

```bash
# 這就是問題所在
timeout 1 bash -c 'echo > /dev/tcp/127.0.0.1/1234' && echo "port ready"
```

**那個探測本身就是一個 gdb 連線。**QEMU 看到 debugger 連上又斷開，就繼續執行了。等 GDB 真的連上時，開機已經跑過頭。

正確做法是不要探測，直接讓 GDB 當第一個連線，並且在 script 開頭驗證：

```gdb
target remote :1234
printf "ATTACH_PC=%#lx  (must be 0x0, or -S was not honoured)\n", $pc
```

這類「觀測行為改變被觀測對象」的坑，在 debug 工具上特別容易中。

另外 GDB 會噴一堆 `Internal error: pc 0x0 in read in CU`，那是**無害的**：ELF 是按 ROM 位址連結的，而 QEMU 把它映射在 0，所以每個 `add-symbol-file` 都要加 `-o 0`。

## 坑 4：不要自己算 struct offset

我想看 BL2 交給 BL31 的 `entry_point_info`，一開始用手算的 offset：

```gdb
printf "pc   = %#lx\n", *(unsigned long *)($x0 + 16)
printf "spsr = %#lx\n", *(unsigned int  *)($x0 + 24)
```

結果印出 `pc=0x3cd`、`spsr=0xe065250`——**兩個值對調了**。因為 `entry_point_info_t` 開頭是一個 `param_header_t`，我少算了它的大小。

既然 `DEBUG=1` build 有完整的 debug info，直接讓 GDB 自己解就好：

```gdb
break bl1_print_next_bl_ep_info
continue
print *bl_ep_info
printf "  .pc   = %#lx\n", bl_ep_info->pc
printf "  .spsr = %#lx   (0x3cd = EL3h)\n", bl_ep_info->spsr
```

得到 `pc=0xe090000 spsr=0x3cd`，`0x3cd` 解開來是 EL3h——**證實 BL31 確實是在 EL3 被進入的**。

> 這裡順帶確認了一件概念上容易弄錯的事：**印出 `BL1: Booting BL31` 的是 BL1，不是 BL2**。BL2 跑在 EL1，沒辦法自己跳到 EL3，所以它用 `smc(BL1_SMC_RUN_IMAGE, ...)` 回到 BL1（`bl2/bl2_main.c`），由 BL1 的 EL3 vector 接手再進 BL31。從 log 看會以為是 BL2 直接跳過去的。

## 坑 5：world switch 的方向不能只看 FID

追 `opteed_smc_handler` 時，我一開始把所有 SMC 都標成「NS→S」，結果看到 `0xbe000000` 和 `0xbe000006` 也被當成 normal world 的請求。

這是錯的。`0xbe00000N` 是 `TEESMC_OPTEED_RETURN_*`（`optee_os/core/arch/arm/include/sm/teesmc_opteed.h`），是 **OP-TEE 往上回報給 dispatcher** 的，不是 normal world 發出的請求。

方向由**呼叫者**決定，不是由 FID 決定。判斷依據是 `flags` 的 bit 0（`SMC_FROM_NON_SECURE`，`include/lib/smccc.h`）：

```gdb
if flags & 1
printf ">>> NS->S  fid=%#x", smc_fid
else
printf "<<< S->NS  fid=%#x", smc_fid
end
```

`flags = 0` 就代表 `is_caller_secure()`，呼叫來自 secure world。光看 FID 數值會得到相反的結論。

## 坑 6：U-Boot 搬不動 50 MB 的 kernel

原本的路徑是 BL33 跑 U-Boot，再由 U-Boot 載 kernel。但我的 kernel 有 50 MB（含內建 initramfs 8 MB），U-Boot 掛掉：

```
loading kernel to address 40400000 size 3232a00 initrd 44000000 size 7fede9
Failed to allocate memory for the image at 0x40400000
zimage: Bad magic!
```

把 `-m` 加到 3 GB **完全沒有幫助**，所以不是 RAM 不夠，是 U-Boot 的 qfw bootflow 本身搬不動這組東西。

解法是直接把 U-Boot 從開機路徑上拿掉——TF-A 有現成的選項：

```
ARM_LINUX_KERNEL_AS_BL33=1
```

kernel 直接當 BL33。開機鏈變成 `BL1 → BL2 → BL31 → BL32 → Linux`，少一層。

> 這個決定有代價：U-Boot 不在路徑上之後，就沒辦法順便觀察 BL33 的 DT fixup 和 bootflow。如果 kernel 小一點（不內嵌 initramfs），U-Boot 的路徑是可以走的。

## 坑 7：kernel 在 FIP 裡，就沒有 QEMU command line 了

kernel 變成 BL33 塞進 FIP 之後，QEMU 的 `-append` 直接報錯：

```
-append only allowed with -kernel option
```

`-initrd` 同理。因為 kernel 不是 QEMU 載的，是 BL2 從 FIP 裡拉出來的，QEMU 根本不知道有 kernel 這回事。

解法是**把 cmdline 和 initramfs 都編進 kernel**：

```bash
./scripts/config -e CMDLINE_FORCE \
                 --set-str CMDLINE "console=ttyAMA0 rdinit=/init" \
                 --set-str INITRAMFS_SOURCE "$OUT/initramfs-ta.cpio.gz"
```

`CONFIG_CMDLINE_FORCE` 是必要的——沒有它，內建的 cmdline 只是 fallback，而 BL2 傳進來的 DT 裡 `/chosen/bootargs` 是空的，會把它蓋掉。

## 坑 8：`unable to open an initial console`

終於開機成功，`/init` 確實跑了（kernel log 看得出來），但**它所有的 `echo` 都不見了**。線索是這行警告：

```
Warning: unable to open an initial console
```

原因：我是用非 root 身分打包 cpio 的，**沒辦法建立 `/dev/console` 這個 device node**。所以 init 啟動時 stdin/stdout/stderr 無處可接，所有輸出直接進黑洞。

解法是讓 init 自己先把 devtmpfs 掛起來，再把自己的輸出接上去——**順序很重要，這四行必須在任何 `echo` 之前**：

```sh
#!/bin/sh
mount -t devtmpfs none /dev 2>/dev/null
exec >/dev/console 2>&1
mount -t proc none /proc
```

這個坑的麻煩之處在於：init 其實好好地跑完了，沒有任何錯誤，只是你看不到。很容易誤判成 init 根本沒執行。

## 坑 9：cross-compile xtest 的 header 與 linker

這部分跟 TrustZone 無關，純粹是跨架構 build 的細節，但花的時間最多。

**host 的 OpenSSL header 會搶贏。** xtest 需要 arm64 的 OpenSSL，但把 `-I` 加在 `CFLAGS` 裡，`/usr/include/openssl` 還是會被優先找到。`optee_test` 的 Makefile 其實有專門的變數（`host/xtest/Makefile`）：

```
OPENSSL_INSTALL_PATH=$SSL_PREFIX
```

**不要覆寫 `CFLAGS`，要用 `CPPFLAGS`。** 覆寫 `CFLAGS` 會把 Makefile 自己的 `-I` 清單丟掉，然後 `adbg.h`、`ta_storage.h` 都找不到。

**`opensslconf.h` 在另一個目錄。** multiarch 下這個 header 是架構相依的，不在 `/usr/include/openssl`，而在 `/usr/include/aarch64-linux-gnu/openssl/`。兩邊要合併成一個目錄才能用單一 `-I`。

**`-L` 不足以滿足 transitive `DT_NEEDED`。** `libssl.so` 自己依賴 `libz.so.1` 和 `libzstd.so.1`，連結時會找不到。這種間接依賴要用 `-Wl,-rpath-link=`，單純的 `-L` 無效：

```
-L$SSL_PREFIX/lib -Wl,-rpath-link=$SSL_PREFIX/lib
```

**`LDFLAGS` 不能同時給 host 和 TA 用。** 這是最後一個坑：上面那組 `LDFLAGS` 給 `xtest` target 沒問題，但 TA 的 build 是直接呼叫 `ld.bfd`，它不認得 `-Wl,` 這個包裝：

```
aarch64-linux-gnu-ld.bfd: unrecognized option '-Wl,-rpath-link=...'
```

結果是兩個 shared library TA（`os_test_lib`、`os_test_lib_dl`）連結失敗。解法是把 `LDFLAGS` 只給 `xtest`，`ta` target 另外跑一次：

```bash
make ... LDFLAGS="-L... -Wl,-rpath-link=..." xtest
make ... ta
```

**另外跳過 `libteeacl`。** `optee_client` 預設會 build 它，而它需要 target 的 libuuid header。`tee-supplicant` 並不依賴 teeacl，所以指名 target 就好：

```bash
make build-libteec build-tee-supplicant build-libckteec
```

## 成果

```
--- 1. did the kernel find the OP-TEE driver? ---
OF: reserved mem: 0x0e100000..0x0effffff (15360 KiB) nomap optee_core@e100000
OF: reserved mem: 0x42000000..0x421fffff (2048 KiB) nomap optee_shm@42000000
optee: revision 4.11 (4370df5008de9aef)
optee: dynamic shared memory is enabled
optee: initialized driver

--- 2. the TEE device nodes ---
crw------- 245, 0   /dev/tee0        ← CA 走這個
crw------- 245, 16  /dev/teepriv0    ← tee-supplicant 走這個
```

兩塊 reserved memory 是理解記憶體隔離的好例子：`optee_core` 那 15 MB 被標 `nomap`，**Linux 永遠不會碰它**；`optee_shm` 那 2 MB 才是兩個 world 共用的信箱。而 `revision 4.11` 後面的 hash 正好等於我 build 的 `optee_os` commit——證明 normal world 問到的真的是這份 secure OS。

三組測試：

```
regression_1004 Test User Crypt TA        10 subtests, 0 failed
regression_1008 TEE internal client API   75 subtests, 0 failed
regression_4001-4006 crypto             10523 subtests, 0 failed
```

每一個 `OK` 背後都是 `/dev/tee0` ioctl → OP-TEE driver → `SMC` → BL31 的 opteed dispatcher → world switch → S-EL1 的 TA 真的算完 → 原路返回。

secure console 這邊看到同一件事的另一面：

```
I/TC: Primary CPU switching to normal world boot
I/TC: Secondary CPU 1 initializing          ← PSCI CPU_ON 也會通知 OP-TEE
M/TA: waiting 2000                          ← 這是 TA 自己的 printf
E/TC:? 0 tee_ta_open_session:787 Failed for TA c3f6e2c0-... error 0xffff0000
```

`M/TA:` 前綴表示這是**在 secure world 裡執行的 TA 程式碼**在對 secure console 說話，不是 OP-TEE core。

那個 `E/TC:` 錯誤**不是失敗**，是 `regression_1008.4 Load corrupt TA` 刻意餵一個被改壞的 TA 進去，OP-TEE 驗章失敗拒絕載入——xtest 對這個結果判定 `OK`。這其實是整個實驗裡最有意義的一行：**TA 必須通過簽章驗證才能進 secure world，而驗證確實在運作**。

## 幾個「不是 bug」的訊息

自己 build 會看到一堆看起來像錯誤的東西，先知道比較不會白花時間：

- `BL2: Skip loading image id 22`——`tee-pageable_v2.bin` 是 0 bytes，因為 pager 預設關閉。
- `CPU_SUSPEND` 永遠不會觸發——QEMU 沒有真正的 idle state。追 PSCI 時會發現 `CPU_ON` 出現兩次而且參數完全相同（SMP bringup 和手動 re-online），**firmware 分不出來**；`CPU_OFF` 不帶參數，因為一顆 CPU 只能關掉自己。
- cortex-a57 的 errata workaround 報 "missing"——QEMU 沒有 CPU revision register。
- `WARNING (insecure configuration)` 與 `Failed to get monotonic counter for REE FS`——QEMU 沒有真的 RPMB，secure storage 的防回滾計數器是假的。真板子上這會是 eMMC RPMB 分區。

## QEMU 教不了你的事

這點值得誠實說清楚。QEMU 可以練 boot flow、SMC 分派、PSCI、world switch、TA 開發，但**有幾件事它結構上就做不到**：

- **沒有真正的電源管理**：PSCI 呼叫會成功返回，但沒有任何東西真的斷電。
- **沒有 ROM**：BL1 是可寫的，所以沒辦法研究一個真正鎖住的 root of trust。
- **沒有真的 TZASC**：secure memory 的隔離是模擬出來的，不是由記憶體控制器強制。
- **errata workaround 無法驗證**。

`TRUSTED_BOARD_BOOT=1` 倒是可以跑，基礎熟了之後值得加上去——那是唯一能在 QEMU 上真正練到的安全機制。

## 參考資料

- Trusted Firmware-A Documentation — QEMU virt Armv8-A: https://trustedfirmware-a.readthedocs.io/en/latest/plat/qemu.html（兩種開機方式、`ARM_LINUX_KERNEL_AS_BL33` 的權威來源）
- TF-A 原始碼: https://github.com/ARM-software/arm-trusted-firmware（`bl1/bl1_main.c`、`bl2/bl2_main.c`、`lib/psci/psci_main.c`、`services/spd/opteed/`、`include/lib/smccc.h`）
- OP-TEE OS: https://github.com/OP-TEE/optee_os（`core/arch/arm/plat-vexpress/platform_config.h`、`core/arch/arm/include/sm/teesmc_opteed.h`）
- OP-TEE Documentation — QEMU v8: https://optee.readthedocs.io/en/latest/building/devices/qemu.html
- OP-TEE build repo（官方的一條龍流程，想直接玩的話用這個）: https://github.com/OP-TEE/build
