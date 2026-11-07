---
title: "SPL 當 BL2：arm64 pre-relocation 的三個約束，與 QEMU 的極限"
date: 2026-11-07
tags: [u-boot, spl, arm64, tf-a, bl31, qemu, zynqmp, device-tree, bootph, gdb]
description: "用 GDB 實測 arm64 SPL 在 relocation 之前的執行環境：gd 為什麼綁 x18、malloc_limit 在 board_init_f 為什麼是 0、BSS 清零的真正時機（下毒驗證）、gd 搬家為什麼要修 DM 的環狀 list，以及 fdtgrep 用 bootph-* 把 DTB 砍掉 10 倍的實際數字。最後記錄把 ZynqMP 的 SPL-as-BL2 搬到 QEMU 時撞到的硬體依賴牆。"
---

# SPL 當 BL2：arm64 pre-relocation 的三個約束，與 QEMU 的極限

> **相關文章**：[BeagleBone Black 的 SPL 原始碼導讀](./bbb-spl-source-walkthrough.md)（armv7、真板子、從 Boot ROM 講到 DRAM）｜[ARMv8 開機鏈三部曲（三）：U-Boot](../u-boot.md)（BL33 的角色與 relocation 理論）

[BBB 那篇](./bbb-spl-source-walkthrough.md)已經把 SPL 的流程走過一遍：Boot ROM 把 SPL 搬進 SRAM、`board_init_f` 只靠 SRAM 把 DDR 叫醒、再搬家到 DRAM。這篇不重複那條路線，而是補三個那篇沒細講、而且**我用 GDB 一個一個量出來**的點：

1. `board_init_f` 階段的「不能用」到底是哪幾種不能用——其中有一個是 `malloc` **必定回 NULL**，原因不是慣例而是一個欄位還沒被設。
2. `gd` 搬家時為什麼要特別修 Driver Model 的指標。
3. SPL 的 device tree 是**剪**出來的，`bootph-*` 砍掉多少。

平台換成 arm64（ZynqMP），形態也換成 **SPL 當 BL2**：SPL 不是去載 U-Boot proper，而是先載 TF-A 的 BL31，再由 BL31 把 U-Boot proper 當 BL33 叫起來。U-Boot 官方文件[^spl-doc]把這個用途寫在 SPL 章節的第一條：

> Launching BL31 of ARM Trusted Firmware which invokes main U-Boot as BL33

文章最後會記錄一件事：**這條路在 QEMU 上跑不完**，而且卡住的理由本身很有啟發性。

本文所有位址、大小都是從 `xilinx_zynqmp_virt_defconfig` 實際 build 出來的產物，以及 QEMU + GDB 實測抓的，不是抄文件。每一節都附可自己重跑的指令。

## 一切的根源：256 KB

ZynqMP 剛上電時 DDR 還沒初始化，能用的只有 **OCM**（on-chip memory）：

```text
OCM 視窗：0xfffc0000 .. 0xffffffff = 256 KB
```

這 256 KB 要同時容納三樣東西：

| 東西 | 位址範圍 | 大小 |
|---|---|---|
| SPL image（`.text`+`.rodata`+`.data`） | `0xfffc0000` .. `0xfffde390` | 120.9 KB |
| BL31（TF-A）載入位置 | `0xfffea000` .. `0xffff9607` | 61.5 KB |
| stack（往下長） | 從 `0xfffffff0` 往下 | 剩 26.5 KB |

```text
0xffffffff ┌────────────────────┐
           │ stack ↓            │  gd + early malloc 也在這一段
0xfffffff0 │ ← 初始 sp          │
0xffff9607 ├────────────────────┤
           │ BL31      61.5 KB  │  ← SPL 要把 TF-A 載到這裡
0xfffea000 ├────────────────────┤
           │ (gap  47 KB)       │
0xfffde390 ├────────────────────┤
           │ SPL image 120.9 KB │
0xfffc0000 └────────────────────┘
```

BL31 載完之後，stack 頂端到 BL31 尾端只剩 **27,125 bytes**。

**後面每一個「SPL 為什麼這麼彆扭」的答案都是從這張圖來的**，和 BBB 上 SRAM 太擠所以 BSS 要丟 DRAM 是同一種壓力，只是這裡還多了一個 BL31 要分地方。

自己量：

```bash
aarch64-linux-gnu-nm -n spl/u-boot-spl | grep -E '__image_copy_start|_end'
aarch64-linux-gnu-size -A spl/u-boot-spl
```

## `gd` 為什麼是暫存器

`arch/arm/include/asm/global_data.h`[^gd-h]：

```c
#ifdef CONFIG_ARM64
#define DECLARE_GLOBAL_DATA_PTR		register gd_t *gd asm ("x18")
#else
#define DECLARE_GLOBAL_DATA_PTR		register gd_t *gd asm ("r9")
#endif
```

arm64 綁 `x18`，armv7 綁 `r9`（BBB 那篇看到的就是 `mov r9, r0`）。理由在 `crt0_64.S`[^crt0] 的註解講得最白：

```asm
	bl	board_init_f_alloc_reserve
	mov	sp, x0
	/* set up gd here, outside any C code */
	mov	x18, x0
	bl	board_init_f_init_reserve
```

為什麼一定要 outside any C code？因為普通全域變數住在 `.data` / `.bss`，而這個時間點：

- `.bss` **還沒清零**（下一節會證明清零在更後面）
- SPL 可能是 XIP，`.data` 根本不可寫

**「存放全域狀態的地方」本身還不能用，所以唯一可靠的儲存空間只剩暫存器。** `x18` 在 AAPCS64 裡是 platform register，正好允許被 firmware 徵用。

GDB 在 reset 當下看到的：

```text
pc = 0xfffc0000   EL = 3   sp = 0   x18 = 0
```

`sp` 和 `x18` 都還是 0——什麼都還沒有。順帶一提 `EL = 3`：SPL 當 BL2 必須在 EL3 跑，因為它接下來要載入並跳進 BL31。

## gd 和 early malloc 是從 sp 往下切出來的

`common/init/board_init.c`[^board-init]：

```c
ulong board_init_f_alloc_reserve(ulong top)
{
	top -= CONFIG_VAL(SYS_MALLOC_F_LEN);                    /* 先切 early malloc */
	top = rounddown(top - sizeof(struct global_data), 16);  /* 再切 gd */
	return top;
}
```

算術和實測完全對上：

```text
CONFIG_SPL_STACK            = 0xfffffffc
bic sp, x0, #0xf            = 0xfffffff0   ← GDB 看到的 incoming top
  − SYS_MALLOC_F_LEN 0x8000 = 0xffff7ff0   ← gd->malloc_base（實測值）
  − sizeof(gd) 376, 16-align = 0xffff7e70  ← gd 本體（實測值），sp 也從這裡開始
```

GDB 實測：

```text
base (where gd will live)   : 0xffff7e70
sp now                      : 0xffff7e70
x18 (gd) now                : 0xffff7e70
sizeof(struct global_data)  : 376
gd->malloc_base             : 0xffff7ff0
```

**pre-relocation 的全部家當就是 376 bytes 的 `gd` 加 32 KB 的 early malloc arena，都擠在 OCM 頂端。**

## `board_init_f` 裡 malloc 必定失敗——而且不是因為沒空間

這是我這次實測才看清楚的細節。注意 GDB 抓到的三個欄位：

```text
gd->malloc_base  = 0xffff7ff0   ← 有設
gd->malloc_limit = 0            ← 是 0
gd->malloc_ptr   = 0
```

`malloc_limit` 在 `board_init_f` 期間是 **0**。而 `common/malloc_simple.c`[^malloc-simple] 的配置函式長這樣：

```c
addr = ALIGN(gd->malloc_base + gd->malloc_ptr, align);
new_ptr = addr + bytes - gd->malloc_base;
if (new_ptr > gd->malloc_limit) {
	log_err("alloc space exhausted ptr %lx limit %x\n", new_ptr,
		gd->malloc_limit);
	return NULL;
}
```

`limit` 是 0 時，任何 `bytes > 0` 都會讓 `new_ptr > 0` 成立而被打回來。

誰設 `limit`？`common/spl/spl.c` 的 `spl_common_init()`[^spl-c]：

```c
if (setup_malloc) {
	gd->malloc_limit = CONFIG_VAL(SYS_MALLOC_F_LEN);
	gd->malloc_ptr = 0;
}
```

而 `spl_common_init()` 是從 **`board_init_r`** 呼叫的，不是 `board_init_f`。

> 所以「`board_init_f` 不要呼叫 malloc」不是風格建議或慣例，**是 arena 的上限還沒被設，呼叫了就一定拿到 NULL**。錯誤訊息還會說 "alloc space exhausted"，看起來像空間不足，實際上是階段不對。

## BSS 在 DDR，而且清零的時機比直覺晚

link map 第一眼很荒謬：

```text
.text  @ 0xfffc0000   (OCM)
.bss   @ 0x1000       (DDR)       ← 差了快 4 GB
.bss size = 360 bytes
```

答案在 `arch/arm/cpu/armv8/u-boot-spl.lds`[^lds]：

```ld
MEMORY { .sram  : ORIGIN = IMAGE_TEXT_BASE,            LENGTH = IMAGE_MAX_SIZE }
#ifdef CONFIG_SPL_SEPARATE_BSS
MEMORY { .sdram : ORIGIN = CONFIG_SPL_BSS_START_ADDR,  LENGTH = CONFIG_SPL_BSS_MAX_SIZE }
#endif
```

`CONFIG_SPL_SEPARATE_BSS=y` 時 BSS 放 `>.sdram`（DDR 的 `0x1000`，在 `memory@0` 的 2 GB 範圍內），code 留 `>.sram`（OCM）。動機和 BBB 一樣是空間，只是這裡要讓位給 BL31。

代價是 `board_init_f` 之前不能碰任何 BSS 變數——那時 DDR 還沒 init。

### 用「下毒」證明清零時機

`crt0_64.S`[^crt0] 的清零迴圈位置很關鍵，在 `board_init_f` **之後**、`board_init_r` **之前**：

```asm
	bl	board_init_f
	...
/* Clear BSS section */
	adrp	x0, __bss_start
	adrp	x1, __bss_end
clear_loop:
	str	xzr, [x0], #8
	cmp	x0, x1
	b.lo	clear_loop

	mov	x0, x18			/* gd_t */
	bl	board_init_r
```

與其相信我讀對了，直接做實驗：在 `board_init_f` 裡寫一個毒值，到 `board_init_r` 檢查還在不在。

```gdb
break board_init_f
continue
set *(unsigned long*)0x1000 = 0xdeadbeefcafebabe

break board_init_r
continue
printf "BSS[0] = %#lx\n", *(unsigned long*)0x1000
```

結果：

```text
== inside board_init_f ==
BSS[0] now = 0xdeadbeefcafebabe
== at board_init_r ==
BSS[0] = 0
```

**毒值被抹掉了，證實清零確實發生在兩階段之間。** 所以在 `board_init_f` 寫 BSS 不只是「不保證保留」，而是寫了之後一定會被清掉——這比「不要用」的說法具體得多。

## gd 搬家，與一個容易忽略的指標修補

同一個實驗意外證明了第二件事：`gd` 搬家了。

```text
board_init_f 時：x18 = 0xffff7e70   (OCM)
board_init_r 時：x18 = 0x17fffe80   (DDR)
```

機制在 `spl_relocate_stack_gd()`[^spl-c]：

```c
ulong ptr = CONFIG_SPL_STACK_R_ADDR;        /* 0x18000000 */
ptr -= roundup(sizeof(gd_t), 16);           /* − 384 */
new_gd = (gd_t *)ptr;
memcpy(new_gd, (void *)gd, sizeof(gd_t));
dm_fixup_for_gd_move(new_gd);
```

算術再次對上：`0x18000000 − 384 = 0x17fffe80`，正是實測值。

`crt0_64.S` 換 `gd` 的寫法也值得一看——因為 `sp` 不能當 conditional move 的運算元，只好先用 `csel` 處理 `x18`：

```asm
	bl	spl_relocate_stack_gd		/* may return NULL */
	cmp	x0, #0
	csel	x18, x0, x18, ne		/* gd = (x0 != NULL) ? x0 : gd */
```

### 為什麼 memcpy 完還要修指標

`drivers/core/root.c`[^root-c]：

```c
void dm_fixup_for_gd_move(struct global_data *new_gd)
{
	/* The sentinel node has moved, so update things that point to it */
	if (gd->dm_root) {
		new_gd->uclass_root->next->prev = new_gd->uclass_root;
		new_gd->uclass_root->prev->next = new_gd->uclass_root;
	}
}
```

`uclass_root` 是一個**嵌在 `gd` 結構裡面**的環狀 list sentinel。`memcpy` 整個 `gd` 之後，list 上鄰居的 `next` / `prev` 還指著舊位址，所以要手動接回來。

**這是「含有自我指標的結構不能單純 memcpy」的一個真實案例**，而且它只修 `uclass_root`——因為其他欄位存的都是指向 `gd` 外部的位址，搬家不影響。

## SPL 的 device tree 是剪出來的

這段和在 Linux 上標 `bootph-*` 的工作直接相關。[U-Boot 文件](https://docs.u-boot.org/en/latest/develop/spl.html)[^spl-doc]說 build 時 fdtgrep 會把完整 DTB 過濾成 SPL 專用的小 DTB：

- 保留 mandatory 節點（`/aliases`、`/chosen`、`/config`）
- 保留帶 pre-relocation 屬性的節點：`bootph-all`、`bootph-pre-ram`（TPL 是 `bootph-pre-sram`，VPL 是 `bootph-verify`）
- 然後**把這些 `bootph-*` 屬性本身也刪掉**

實測效果：

```text
完整 dtb：49,176 bytes、238 個節點
SPL  dtb： 4,687 bytes、 23 個節點      ← 10 倍差距
SPL dtb 裡殘留的 bootph-*：0 個
```

`bootph-*` 是**選擇器，用完就丟**。

活下來的 23 個節點，本身就是「SPL 需要什麼」的答案：

```text
firmware/zynqmp-firmware/{power-management, clock-controller}   ← 時脈
axi/{spi@…, mmc@…, mmc@…}                                      ← 從哪載入下一階段
axi/{serial@…, serial@…}                                       ← console
zynqmp-ipi/mailbox@…                                           ← 跟 PMU 溝通
{pss-ref-clk, video-clk, pss-alt-ref-clk, …}                   ← 時脈來源
aliases, chosen                                                ← mandatory
```

「SPL 只需要能載入下一階段的最小硬體集合」這句話，在這份清單裡是字面意義上的真。

自己量：

```bash
dtc -I dtb -O dts spl/u-boot-spl.dtb | grep -c '{'
dtc -I dtb -O dts spl/u-boot-spl.dtb | grep -c bootph
```

## 完整的 pre-relocation 路徑

每一個都實測可下中斷點：

```text
_start                       (0xfffc0000, EL3)
  └─ save_boot_params
  └─ apply_core_errata
  └─ crt0_64.S
       sp = SPL_STACK & ~0xf                  → 0xfffffff0
       board_init_f_alloc_reserve(sp)         → 0xffff7e70
       sp = x18 = 0xffff7e70                  ← gd 誕生
       board_init_f_init_reserve(base)        memset(gd,0)、設 malloc_base
       debug_uart_init                        ← <debug_uart> 那行的來源
       board_init_f(0)                        ← 此時無 BSS、malloc 必失敗
       ---- clear_loop：清 BSS @0x1000 ----
       spl_relocate_stack_gd()                → gd 搬到 0x17fffe80
       board_init_r(gd, relocaddr)
         └─ spl_init() → spl_common_init()
              bootstage_init
              log_init
              fdtdec_setup                    ← 沒有 DTB 的話這裡回 −EINVAL
              dm_init_and_scan
              dm_autoprobe
         └─ board_boot_order / spl_boot_device
         └─ boot_from_devices
         └─ spl_invoke_atf                    ← 交棒 BL31
```

`<debug_uart>` 那行出自 `include/debug_uart.h` 的 `_DEBUG_UART_ANNOUNCE`[^debug-uart]；只看到它而看不到後續訊息，意思是 DM console 還沒接起來，此時所有 `printf` 都會進黑洞——這個現象在下一節會變成一個很好的除錯訊號。

## QEMU 的極限：一道硬體依賴牆

想在 QEMU 上跑完這條路，結果是**跑不完**。記錄下來是因為卡住的理由比成功更有資訊量。

先說結論：`CONFIG_SPL_ATF` 的 defconfig 幾乎全是 Rockchip，而 **Rockchip 在 QEMU upstream 完全不存在**（在 QEMU master 的 `MAINTAINERS` 裡搜 `rockchip` 是 0 筆）；Intel socfpga 同樣沒有 machine。能跑 SPL-as-BL2 又被 QEMU 模擬的平台，交集只有 Xilinx 的 `xlnx-zcu102`。而 ZynqMP 的 `doc/board/xilinx/` 從頭到尾沒提過 QEMU——**這條路本來就不在上游支援範圍內**。

硬推的話會依序撞到這些牆，每一道都是「真板子上有、QEMU 沒有」的硬體：

| 症狀 | 根因 | 處置 |
|---|---|---|
| `psu_init` 的 `mask_poll` 無限迴圈 | 等 IOPLL lock，CRL_APB 沒被模擬 | 關 `SPL_ZYNQMP_PSU_INIT_ENABLED`（QEMU 不需要 PLL/DDR bring-up，這是正解不是 hack） |
| 讀 boot mode 暫存器失敗 | 同一個 CRL_APB 區塊沒被模擬 | 開 `SPL_ZYNQMP_ALT_BOOTMODE_ENABLED` + `JTAG_MODE`，直接寫死 boot mode 繞過那個讀取 |
| `spl_init()` 回 **−22**（`−EINVAL`） | `CONFIG_OF_BOARD=y`，SPL 預期前一階段在 runtime 餵一份 DTB；QEMU 不餵 | 載 `u-boot-spl-dtb.bin`，並把 dtb 放到 `XILINX_OF_BOARD_DTB_ADDR` |
| `panic("PMUFW version error")` | 向 PMU firmware 問版本，而 PMU 是一顆 QEMU 不跑的 MicroBlaze | 關 SPL 的 firmware/FPGA 支援 |
| `serial_zynq: failed to get clock` | **走不下去** | — |

前四道都過了之後 SPL 的 console 真的活了（開始自己報錯，而不是只有 `<debug_uart>` 一行），但最後一道是真正的循環依賴，從 DTB 本身就看得出來：

```text
serial@ff010000  clocks = <&clock-controller …>
  └─ clock-controller  compatible = "xlnx,zynqmp-clk"
       └─ 它是 zynqmp-firmware 的子節點，method = "smc"
```

UART 要時脈 → 時脈要問 PMU firmware → **PMU 是 QEMU 不跑的另一顆核**；就算改走 SMC 到 EL3，BL31 在這個階段還沒被載入（SPL 正是要去載它的那個人）。

U-Boot 有 `CONFIG_SPL_CLK_STUB`，描述寫著 "a stub clock driver in SPL for non-essential clock controllers"，看起來正是為這種情況設計的。但它的 `of_match` 只列 Qualcomm 的 compatible，沒有 `xlnx,zynqmp-clk`，所以開了沒有效果。要過這關就得改上游原始碼去遷就模擬器缺的硬體，那已經不是在學 SPL 了。

**不過形態 B 的結構在 build 層面是驗證成立的。** TF-A 的 zynqmp 平台強制 `RESET_TO_BL31 := 1`，整個 build 只產出一個 BL：

```console
$ find . -name 'bl*.bin' -printf '%f\n'
bl31.bin
```

沒有 `bl1.bin`、沒有 `bl2.bin`——因為 BL1/BL2 的角色由 SPL 擔任了。而 FIT 裡看得到完整的交棒結構：

```console
$ dumpimage -l u-boot.itb
 Image 0 (uboot)   Load Address: 0x08000000    ← DDR，U-Boot proper 當 BL33
 Image 1 (atf)     Load Address: 0xfffea000    ← OCM，BL31
```

`0xfffea000` 正是本文第一張圖裡 BL31 的位置——「剛上電只有 SRAM 可用」這個約束的具體數字。

## 小結

- **OCM 只有 256 KB，而且要分給 BL31**，這一條推導出後面所有限制。
- `gd` 綁 `x18`（armv7 是 `r9`）不是風格選擇：那個時間點 `.bss` 沒清零、`.data` 可能不可寫，暫存器是唯一可靠的儲存空間。
- `board_init_f` 裡 `malloc` 必定回 NULL，因為 `malloc_limit` 要到 `board_init_r` 的 `spl_common_init()` 才被設。錯誤訊息說 "alloc space exhausted"，但真正的原因是階段不對。
- BSS 清零排在 `board_init_f` **之後**——用下毒法可以直接看到毒值被抹掉。
- `gd` 搬家後要 `dm_fixup_for_gd_move()`，因為 `uclass_root` 是嵌在 `gd` 裡的環狀 list sentinel。
- `bootph-*` 把 DTB 從 238 節點砍到 23 節點（49 KB → 4.7 KB），而且屬性本身用完就被刪掉。
- 在模擬器上追開機鏈，**撞到的牆往往就是「這塊硬體真板子上由誰負責」的答案**：CRL_APB、PMU firmware、前一階段餵的 DTB，三件事在 QEMU 上都沒人做。

## 參考

[^spl-doc]: U-Boot, "Generic SPL framework" — https://docs.u-boot.org/en/latest/develop/spl.html
[^gd-h]: `arch/arm/include/asm/global_data.h` — https://github.com/u-boot/u-boot/blob/master/arch/arm/include/asm/global_data.h
[^crt0]: `arch/arm/lib/crt0_64.S` — https://github.com/u-boot/u-boot/blob/master/arch/arm/lib/crt0_64.S
[^board-init]: `common/init/board_init.c` — https://github.com/u-boot/u-boot/blob/master/common/init/board_init.c
[^malloc-simple]: `common/malloc_simple.c` — https://github.com/u-boot/u-boot/blob/master/common/malloc_simple.c
[^spl-c]: `common/spl/spl.c` — https://github.com/u-boot/u-boot/blob/master/common/spl/spl.c
[^lds]: `arch/arm/cpu/armv8/u-boot-spl.lds` — https://github.com/u-boot/u-boot/blob/master/arch/arm/cpu/armv8/u-boot-spl.lds
[^root-c]: `drivers/core/root.c` — https://github.com/u-boot/u-boot/blob/master/drivers/core/root.c
[^debug-uart]: `include/debug_uart.h` — https://github.com/u-boot/u-boot/blob/master/include/debug_uart.h
