# BeagleBone Black 的 SPL 原始碼導讀：從 Boot ROM 到 DRAM

[上一篇](./bbb-uboot-bringup.md)從記憶體的角度走了一次開機：Boot ROM 把 MLO 搬進 SRAM，SPL 叫醒 DDR，再把 U-Boot 搬進 DRAM。那篇只講「搬到哪」，這篇照著 U-Boot 原始碼，一行一行看 SPL 是**怎麼**做到的：上電後第一條指令在哪、ROM 留了什麼給 SPL、DDR 起來之前 C 程式靠什麼跑、DDR 參數從哪來、最後怎麼找到 `u-boot.img`。

版本說明：

- 板子上原廠的 SPL 是 U-Boot 2019.04。這篇讀的是 mainline [`709a97a05`](https://github.com/u-boot/u-boot/tree/709a97a05df66e394f40d249105d0baade46f107)（v2027.01-rc2 之後），流程和 2019.04 一樣，只有名字改了（例如 `CONFIG_SPL_BUILD` 變成 `CONFIG_XPL_BUILD`）。
- 文中的位址與大小是用 `am335x_evm_defconfig`（BBB 用的 defconfig）實際 build 出來再讀的，不是抄文件。
- 下文程式碼連結都指向同一個 commit；引用的片段有刪減，`...` 表示省略。

## 全圖：三個地方、七個步驟

開機時會用到三個地方，性質完全不同：

| 地方 | 位址 | 上電就能用？ | 誰在用 |
|---|---|---|---|
| Boot ROM | `0x4002_0000` 起 | 是，唯讀 | ROM code（TI 燒死，沒有原始碼） |
| 內部 SRAM（OCMC） | `0x402F_0400` – `0x4030_FFFF` | 是 | ROM 放 MLO；SPL 前半段的 code、stack、`gd` |
| DRAM（DDR3L 512 MiB） | `0x8000_0000` 起 | **否**，要等 SPL 設好 EMIF | SPL 後半段的 BSS、malloc、stack；U-Boot proper |

SPL 的工作可以濃縮成一句：**在只有 SRAM 的世界裡，把 DRAM 變成可以用的記憶體，然後搬到 DRAM 去，再把 U-Boot 載進來。**

![SPL 開機流程：九個步驟由上而下，四條直欄是 SD 卡、Boot ROM、內部 SRAM、DRAM。ROM 把 MLO 複製進 SRAM 0x402F0400 並以 r0 傳 boot parameters 指標；reset 把 r0 存到 0x4030B424；_main 在 0x4030FF00 設 stack 與 gd；early_system_init 解析 ROM 參數、讀 EEPROM；prcm_init 先調 PMIC 電壓再鎖 PLL；sdram_init 設好 EMIF 後 DRAM 才可用；BSS 在 0x80A00000、gd 與 stack 搬到 0x82000000；board_init_r 把 u-boot.img 從 SD 載到 0x80800000；最後跳過去。SPL 程式碼全程在 SRAM 執行](../assets/bbb/spl-flow-zh-light.svg#gh-light-mode-only)
![SPL 開機流程：九個步驟由上而下，四條直欄是 SD 卡、Boot ROM、內部 SRAM、DRAM。ROM 把 MLO 複製進 SRAM 0x402F0400 並以 r0 傳 boot parameters 指標；reset 把 r0 存到 0x4030B424；_main 在 0x4030FF00 設 stack 與 gd；early_system_init 解析 ROM 參數、讀 EEPROM；prcm_init 先調 PMIC 電壓再鎖 PLL；sdram_init 設好 EMIF 後 DRAM 才可用；BSS 在 0x80A00000、gd 與 stack 搬到 0x82000000；board_init_r 把 u-boot.img 從 SD 載到 0x80800000；最後跳過去。SPL 程式碼全程在 SRAM 執行](../assets/bbb/spl-flow-zh-dark.svg#gh-dark-mode-only)

| # | 在哪跑 | 原始碼 | 做什麼 |
|---|---|---|---|
| 0 | ROM | （閉源） | 依 SYSBOOT 找開機裝置，把 MLO 複製到 SRAM `0x402F_0400`，r0 帶著參數指標跳過去 |
| 1 | SRAM | `arch/arm/cpu/armv7/start.S` `reset` | 第一件事：把 r0 存起來 |
| 2 | SRAM | `arch/arm/cpu/armv7/start.S` | 設 SVC mode、`cpu_init_cp15`（關 MMU／cache） |
| 3 | SRAM | `arch/arm/lib/crt0.S` `_main` | 在 SRAM 設 stack 和 `gd`，呼叫 `board_init_f` |
| 4 | SRAM | `arch/arm/mach-omap2/am33xx/board.c` `board_init_f` | 關 watchdog、UART、解析 ROM 參數、讀 EEPROM、PMIC 電壓、PLL、**DDR** |
| 5 | SRAM→DRAM | `crt0.S` | 清 DRAM 裡的 BSS，stack 和 `gd` 搬到 DRAM |
| 6 | DRAM stack | `common/spl/spl.c` `board_init_r` | malloc、driver model、依 ROM 給的開機裝置載入 `u-boot.img` |
| 7 | DRAM | `jump_to_image` | 跳進 U-Boot proper（`0x8080_0000`） |

下面照順序走。

## ⓪ Boot ROM：沒有原始碼，但留下了兩樣東西

ROM 是 TI 燒死的，看不到 code，只能從 TRM 和 U-Boot 這邊「接手的程式」反推它做了什麼：

- 讀 SYSBOOT 腳位決定開機裝置順序（BBB 預設 eMMC 優先，按住 S2 上電改成 SD 優先）。
- 從 MMC/SD 開機時，ROM 會先試 raw 模式（在固定的幾個 sector 偏移找 TOC），找不到再到第一個 FAT 分割區找叫 `MLO` 的檔案。
- 照 MLO 的 GP header 把 image 複製到 SRAM。GP header 只有 8 bytes：image 大小和載入位址。用這篇 build 出來的 MLO 看：

```bash
$ xxd -s 0x200 -l 8 MLO
00000200: f885 0100 0004 2f40      ....../@
```

  little-endian 讀：大小 `0x000185f8`（99,832 bytes），載入位址 `0x402f0400`。跟 `CONFIG_SPL_TEXT_BASE=0x402F0400` 一致。

ROM 留給 SPL 的兩樣東西：

1. **SRAM 裡的一塊「boot parameters」結構**，記錄這次是從哪個裝置開機、用 raw 還是 FAT。
2. **r0 暫存器**：指向那塊結構。跳進 SPL 時就放在 r0 裡。

SPL 後面「要從哪裡載 U-Boot」完全是照 ROM 的答案走，所以第一步就要把 r0 救下來。

## ① 第一條指令：先救 r0

ROM 跳到 `0x402F_0400`，那裡是 `_start`，也就是 ARM 的 exception vector table，第一格是 `b reset`。用 `nm` 對得起來：

```text
402f0400 T _start
402f0444 T reset
```

[`arch/arm/cpu/armv7/start.S`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/arch/arm/cpu/armv7/start.S)：

```asm
reset:
	/* Allow the board to save important registers */
	b	save_boot_params
save_boot_params_ret:
```

`save_boot_params` 預設是空的 weak 函式，OMAP 系列在 [`arch/arm/mach-omap2/lowlevel_init.S`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/arch/arm/mach-omap2/lowlevel_init.S) 覆寫它：

```asm
ENTRY(save_boot_params)
	ldr	r1, =OMAP_SRAM_SCRATCH_BOOT_PARAMS
	str	r0, [r1]
	b	save_boot_params_ret
ENDPROC(save_boot_params)
```

這時還沒有 stack、沒有 C，只能用 assembly 把 r0 寫到 SRAM 的固定位置。這個位置怎麼算出來（[`arch-am33xx/omap.h`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/arch/arm/include/asm/arch-am33xx/omap.h)、`omap_common.h`）：

```c
#define NON_SECURE_SRAM_START	0x402F0400
#define NON_SECURE_SRAM_END	0x40310000
#define NON_SECURE_SRAM_IMG_END	0x4030B800
#define SRAM_SCRATCH_SPACE_ADDR	(NON_SECURE_SRAM_IMG_END - SZ_1K)	/* 0x4030B400 */
#define OMAP_SRAM_SCRATCH_BOOT_PARAMS	(SRAM_SCRATCH_SPACE_ADDR + 0x24)	/* 0x4030B424 */
```

`0x402F_0400`–`0x4030_B800` 是 ROM 給下載 image 的區域（約 109 KB），再上去到 `0x4031_0000` 是 ROM 自己的 stack 和資料。scratch 區放在 image 區的最後 1 KB，SPL 的 code 不會長到那裡（見下面的大小限制）。

接著 `start.S` 把 CPU 切到 SVC mode、關中斷，`cpu_init_cp15` 把 MMU 和 cache 設成關閉狀態，然後 `bl _main`。

## ② `_main`：在 SRAM 裡生出 C 的執行環境

C 程式至少要有 stack；U-Boot 還多要一個 `gd`（global data，所有 phase 共用的狀態，ARM 上固定放在 r9）。這時只有 SRAM，所以兩個都放 SRAM。

[`arch/arm/lib/crt0.S`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/arch/arm/lib/crt0.S)：

```asm
ENTRY(_main)
	...
	ldr	r0, =(SYS_INIT_SP_ADDR)		/* 0x4030ff00 */
	bic	r0, r0, #7	/* 8-byte alignment for ABI compliance */
	mov	sp, r0
	bl	board_init_f_alloc_reserve
	mov	sp, r0
	/* set up gd here, outside any C code */
	mov	r9, r0
	bl	board_init_f_init_reserve
	...
	mov	r0, #0
	bl	board_init_f
```

- `SYS_INIT_SP_ADDR` 來自 `CONFIG_CUSTOM_SYS_INIT_SP_ADDR=0x4030ff00`，SRAM 的頂端。
- `board_init_f_alloc_reserve` 從 stack 頂往下切一塊給 `gd` 和早期 malloc（`CONFIG_SPL_SYS_MALLOC_F_LEN=0x2000`，8 KB），stack 從它下面開始往下長。

**這裡有個重點**：SPL 的 BSS 不在 SRAM，而在 DRAM（`CONFIG_SPL_BSS_START_ADDR=0x80a00000`）。看 build 出來的 section：

```text
  [ 1] .text    PROGBITS  402f0400 ... 01307c
  [ 2] .rodata  PROGBITS  4030347c ... 003f50
  [ 3] .data    PROGBITS  403073cc ... 000be2
  [ 5] .bss     NOBITS    80a00000 ... 003860
```

但 DRAM 要到 `board_init_f` 跑完才能用。所以 `board_init_f` 這整段**不能碰全域變數的 BSS**，狀態只能放在 `gd` 或 stack。`CONFIG_SPL_EARLY_BSS` 沒開，`CLEAR_BSS` 也就排在 `board_init_f` 之後（見第 ④ 步）。

為什麼 BSS 要放 DRAM？因為 SRAM 太擠了。`CONFIG_SPL_MAX_SIZE=0x1b000`（110,592 bytes），而 text + rodata + data 已經用掉約 99.8 KB。我在 v2026.10 用 Ubuntu 24.04 的 gcc 13.3 build 同一個 defconfig，link 直接失敗：

```text
arm-linux-gnueabihf-ld: region `.sram' overflowed by 120 bytes
```

同一個 compiler build 現在的 main 則過得去，MLO 是 100,344 bytes。SPL 的大小真的是以百 bytes 在計較。

## ③ `board_init_f`：只靠 SRAM 把 DDR 叫醒

AM33xx 的 `board_init_f` 在 [`arch/arm/mach-omap2/am33xx/board.c`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/arch/arm/mach-omap2/am33xx/board.c)，短到一眼看完：

```c
void board_init_f(ulong dummy)
{
	hw_data_init();
	early_system_init();
	board_early_init_f();
	sdram_init();
	/* dram_init must store complete ramsize in gd->ram_size */
	gd->ram_size = get_ram_size(
			(void *)CFG_SYS_SDRAM_BASE,
			CFG_MAX_RAM_BANK_SIZE);
}
```

### 3a. `early_system_init`：watchdog、UART、ROM 參數、EEPROM

```c
void early_system_init(void)
{
	...
	watchdog_disable();
	set_uart_mux_conf();
	setup_early_clocks();
	uart_soft_reset();
#ifdef CONFIG_XPL_BUILD
	/*
	 * Save the boot parameters passed from romcode.
	 * We cannot delay the saving further than this,
	 * to prevent overwrites.
	 */
	save_omap_boot_params();
#endif
	...
	spl_early_init();
	...
#ifdef CONFIG_TI_I2C_BOARD_DETECT
	do_board_detect();
#endif
	...
}
```

順序都有理由：

1. **`watchdog_disable`**：ROM 離開時 watchdog 還在跑，SPL 做 DDR 初始化要花時間，不關掉板子會自己 reset。
2. **UART pinmux、時脈、reset**：之後才印得出東西。
3. **`save_omap_boot_params`**：第 ① 步只存了「指標」，這裡才去讀指標指向的結構。註解說不能再晚，因為那塊 SRAM 之後可能被蓋掉。
4. **`do_board_detect`**：讀 I2C0 上的板子 EEPROM（`0x50`）。

`save_omap_boot_params` 在 [`arch/arm/mach-omap2/boot-common.c`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/arch/arm/mach-omap2/boot-common.c)，ROM 的結構長這樣：

```c
struct omap_boot_parameters {
	unsigned int reserved;
	unsigned int boot_device_descriptor;
	unsigned char boot_device;
	unsigned char reset_reason;
};
```

```c
void save_omap_boot_params(void)
{
	u32 boot_params = *((u32 *)OMAP_SRAM_SCRATCH_BOOT_PARAMS);
	...
	if ((boot_params < NON_SECURE_SRAM_START) ||
	    (boot_params > NON_SECURE_SRAM_END))
		return;
	omap_boot_params = (struct omap_boot_parameters *)boot_params;
	boot_device = omap_boot_params->boot_device;
	...
	gd->arch.omap_boot_device = boot_device;
	...
		boot_params = omap_boot_params->boot_device_descriptor;
		...
		boot_params = *((u32 *)(boot_params + DEVICE_DATA_OFFSET));
		...
		boot_mode = *((u32 *)(boot_params + BOOT_MODE_OFFSET));
	...
	gd->arch.omap_boot_mode = boot_mode;
}
```

- 先檢查指標有沒有落在 SRAM 範圍內，不在就放棄（例如不是 ROM 直接帶起來的情況）。
- 讀出兩件事：**開機裝置**（SD、eMMC、UART…）和 **MMC 的開機模式**（raw 還是 FAT），存進 `gd`。注意存的是 `gd`，不是全域變數，因為 BSS 還不能用。

`do_board_detect` 在 [`board/ti/am335x/board.c`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/board/ti/am335x/board.c)：

```c
void do_board_detect(void)
{
	enable_i2c0_pin_mux();
	enable_i2c2_pin_mux();
	if (ti_i2c_eeprom_am_get(CONFIG_EEPROM_BUS_ADDRESS,
				 CONFIG_EEPROM_CHIP_ADDRESS))
		printf("ti_i2c_eeprom_init failed\n");
}
```

EEPROM 裡的板名決定了後面所有參數。BBB 的板名是 `A335BNLT`，就是上一篇 U-Boot `printenv` 看到的 `board_name`：

```c
static inline int board_is_bone_lt(void)
{
	return board_ti_is("A335BNLT");
}
```

**同一份 MLO 可以開 EVM、BeagleBone 白板、BBB、PocketBeagle，靠的就是這一步。** 這也是「為什麼讀 EEPROM 一定要在 DDR 之前」：不知道是哪塊板子，就不知道 DDR 要怎麼設。

### 3b. `board_early_init_f`：pinmux、PMIC 電壓、PLL

```c
int board_early_init_f(void)
{
	set_mux_conf_regs();
	prcm_init();
	...
}
```

`prcm_init` 在 [`arch/arm/mach-omap2/am33xx/clock.c`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/arch/arm/mach-omap2/am33xx/clock.c)：

```c
void prcm_init(void)
{
	scale_vcores();
	setup_dplls();
}
```

**先調電壓，再拉頻率**，順序反過來 CPU 會在電壓不夠時跑高頻。

- `scale_vcores`：BBB 的電源是 TPS65217 PMIC，透過 I2C0 把 DCDC2（MPU）和 DCDC3（core）調到目標電壓。
- `setup_dplls`：依序鎖 core、MPU、PER、DDR 四組 PLL：

```c
static void setup_dplls(void)
{
	const struct dpll_params *params;

	params = get_dpll_core_params();
	do_setup_dpll(&dpll_core_regs, params);

	params = get_dpll_mpu_params();
	do_setup_dpll(&dpll_mpu_regs, params);

	params = get_dpll_per_params();
	do_setup_dpll(&dpll_per_regs, params);
	...
	params = get_dpll_ddr_params();
	do_setup_dpll(&dpll_ddr_regs, params);
}
```

PLL 參數又回到 board 檔，用 EEPROM 的結果選：

```c
const struct dpll_params *get_dpll_ddr_params(void)
{
	...
	else if (board_is_pb() || board_is_bone_lt() || board_is_icev2())
		return &dpll_ddr3_400MHz[ind];
	...
}

const struct dpll_params *get_dpll_mpu_params(void)
{
	...
	if (bone_not_connected_to_ac_power())
		freq = MPUPLL_M_600;

	if (board_is_pb() || board_is_bone_lt())
		freq = MPUPLL_M_1000;
	...
}
```

BBB：DDR 400 MHz、MPU 1 GHz。讀程式碼才會注意到的細節：前面那個 `if` 說沒接 DC 電源就降到 600 MHz，但緊接著 BBB（`bone_lt`）又被設回 1000，所以在這個版本裡，BBB 不管用什麼供電，SPL 都把 MPU 設成 1 GHz。

### 3c. `sdram_init`：把 DDR3L 的參數寫進 EMIF

```c
void sdram_init(void)
{
	...
	else if (board_is_pb() || board_is_bone_lt())
		config_ddr(400, &ioregs_bonelt,
			   &ddr3_beagleblack_data,
			   &ddr3_beagleblack_cmd_ctrl_data,
			   &ddr3_beagleblack_emif_reg_data, 0);
	...
}
```

`ddr3_beagleblack_*` 這三個結構裡全是一個顆粒的參數：`MT41K256M16HA125E`，BBB 上那顆 Micron DDR3L（256M × 16 bit = 512 MiB）。例如 EMIF 的時序：

```c
static struct emif_regs ddr3_beagleblack_emif_reg_data = {
	.sdram_config = MT41K256M16HA125E_EMIF_SDCFG,
	.ref_ctrl = MT41K256M16HA125E_EMIF_SDREF,
	.sdram_tim1 = MT41K256M16HA125E_EMIF_TIM1,
	.sdram_tim2 = MT41K256M16HA125E_EMIF_TIM2,
	.sdram_tim3 = MT41K256M16HA125E_EMIF_TIM3,
	...
};
```

**AM335x 的 DDR 參數是 U-Boot 裡寫死的常數**，不是在開機時 training 出來的。換一顆不同的 DDR 顆粒，就要改這幾個值（TI 有算這些值的試算表）。這跟有些 SoC 需要一包 DDR training firmware 的做法很不一樣。

`config_ddr` 在 [`arch/arm/mach-omap2/am33xx/emif4.c`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/arch/arm/mach-omap2/am33xx/emif4.c)，照硬體需要的順序寫暫存器：

```c
void config_ddr(unsigned int pll, const struct ctrl_ioregs *ioregs,
		const struct ddr_data *data, const struct cmd_control *ctrl,
		const struct emif_regs *regs, int nr)
{
	ddr_pll_config(pll);
	config_vtp(nr);
	config_cmd_ctrl(ctrl, nr);

	config_ddr_data(data, nr);
#ifdef CONFIG_AM33XX
	config_io_ctrl(ioregs);

	/* Set CKE to be controlled by EMIF/DDR PHY */
	writel(DDR_CKE_CTRL_NORMAL, &ddrctrl->ddrckectrl);
#endif
	...
	/* Program EMIF instance */
	config_ddr_phy(regs, nr);
	set_sdram_timings(regs, nr);
	...
		config_sdram(regs, nr);
}
```

VTP（I/O 阻抗校正）→ 命令線和資料線的 PHY 延遲比例 → I/O 設定 → 把 CKE 交給 EMIF → PHY 讀延遲 → 時序 → 最後寫 `sdram_config` 讓 EMIF 開始對 DDR 下初始化命令。

最後回到 `board_init_f` 的 `get_ram_size`：在 `0x8000_0000` 起試寫試讀，量出實際大小，這就是 U-Boot 印的 `DRAM: 512 MiB` 的來源。

## ④ 回到 `_main`：搬家到 DRAM

`board_init_f` 返回後，DRAM 已經能用了。`crt0.S` 接著做 SPL 專屬的那一段：

```asm
#if !defined(CONFIG_XPL_BUILD) || CONFIG_IS_ENABLED(FRAMEWORK)

#if !defined(CONFIG_XPL_BUILD) || !defined(CONFIG_SPL_EARLY_BSS)
	CLEAR_BSS
#endif

# ifdef CONFIG_XPL_BUILD
	/* Use a DRAM stack for the rest of SPL, if requested */
	bl	spl_relocate_stack_gd
	cmp	r0, #0
	movne	sp, r0
	movne	r9, r0
# endif
	...
	ldr	pc, =board_init_r	/* this is auto-relocated! */
```

1. `CLEAR_BSS`：清 `0x80a0_0000` 起的 BSS。現在才清，因為現在 DRAM 才存在。
2. `spl_relocate_stack_gd`（[`common/spl/spl.c`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/common/spl/spl.c)）：把 `gd` 複製到 DRAM，stack 也換到 DRAM。

```c
ulong spl_relocate_stack_gd(void)
{
#if CONFIG_IS_ENABLED(STACK_R)
	gd_t *new_gd;
	ulong ptr = CONFIG_SPL_STACK_R_ADDR;		/* 0x82000000 */
	...
	if (CONFIG_SPL_STACK_R_MALLOC_SIMPLE_LEN) {	/* 1 MiB */
		ptr -= CONFIG_SPL_STACK_R_MALLOC_SIMPLE_LEN;
		gd->malloc_base = ptr;
		...
	}
	...
	ptr -= roundup(sizeof(gd_t), 16);
	gd->start_addr_sp = ptr;
	new_gd = (gd_t *)ptr;
	memcpy(new_gd, (void *)gd, sizeof(gd_t));
	...
	return ptr;
```

注意 SPL **沒有搬 code**，code 還是在 SRAM 跑；搬的只有資料（`gd`、stack、malloc）。這跟 U-Boot proper 的 relocation（把整份自己搬到 DRAM 頂端）是兩回事。

搬完之後，SPL 用到的記憶體：

| 東西 | 位址 | 大小 | 設定 |
|---|---|---|---|
| SPL code + data | SRAM `0x402F_0400` | 約 99.8 KB（上限 `0x1b000`） | `SPL_TEXT_BASE`、`SPL_MAX_SIZE` |
| ROM boot params 指標 | SRAM `0x4030_B424` | 4 bytes | `OMAP_SRAM_SCRATCH_BOOT_PARAMS` |
| `board_init_f` 時的 stack／`gd` | SRAM `0x4030_FF00` 往下 | — | `CUSTOM_SYS_INIT_SP_ADDR` |
| BSS | DRAM `0x80A0_0000` | `0x3860`（上限 512 KB） | `SPL_BSS_START_ADDR` |
| malloc | DRAM `0x80A8_0000` | 8 MiB | 接在 BSS 上限之後，`SPL_SYS_MALLOC_SIZE` |
| simple malloc | DRAM `0x81F0_0000` | 1 MiB | `SPL_STACK_R_MALLOC_SIMPLE_LEN` |
| `gd` 與之後的 stack | DRAM `0x8200_0000` 往下 | — | `SPL_STACK_R_ADDR` |

## ⑤ `board_init_r`：照 ROM 的答案去找 U-Boot

[`common/spl/spl.c`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/common/spl/spl.c) 的 `board_init_r` 是所有平台共用的，AM335x 只透過幾個 hook 參與：

```c
void board_init_r(gd_t *dummy1, ulong dummy2)
{
	...
	spl_set_bd();

	if (IS_ENABLED(CONFIG_SPL_SYS_MALLOC)) {
		mem_malloc_init(SPL_SYS_MALLOC_START, SPL_SYS_MALLOC_SIZE);
		gd->flags |= GD_FLG_FULL_MALLOC_INIT;
	}
	if (!(gd->flags & GD_FLG_SPL_INIT)) {
		if (spl_init())
			hang();
	}
	timer_init();
	...
	board_boot_order(spl_boot_list);

	ret = boot_from_devices(&spl_image, spl_boot_list,
				ARRAY_SIZE(spl_boot_list));
	...
	os = spl_image.os;
	if (os == IH_OS_U_BOOT) {
		debug("Jumping to %s...\n", xpl_name(xpl_next_phase()));
	} else if ...
	} else if (CONFIG_IS_ENABLED(OS_BOOT) && os == IH_OS_LINUX) {
		...
		jumper = &jump_to_image_linux;
	}
	...
}
```

`board_boot_order` 預設只放一個裝置：`spl_boot_device()` 的回傳值。OMAP 的實作就是把第 ③ 步存進 `gd` 的答案拿出來：

```c
u32 spl_boot_device(void)
{
	return gd->arch.omap_boot_device;
}

u32 spl_mmc_boot_mode(struct mmc *mmc, const u32 boot_device)
{
	return gd->arch.omap_boot_mode;
}
```

**ROM 從 SD 讀到 MLO，SPL 就從 SD 讀 U-Boot；ROM 用 FAT，SPL 就用 FAT。** 這就是第 ① 步非救 r0 不可的原因。

MMC 那條路在 [`common/spl/spl_mmc.c`](https://github.com/u-boot/u-boot/blob/709a97a05df66e394f40d249105d0baade46f107/common/spl/spl_mmc.c) 的 `spl_mmc_load`：

```c
	boot_mode = spl_mmc_boot_mode(mmc, bootdev->boot_device);
	ret = -EINVAL;
	switch (boot_mode) {
	...
	case MMCSD_MODE_RAW:
		debug("spl: mmc boot mode: raw\n");

		if (!spl_start_uboot()) {
			ret = mmc_load_image_raw_os(spl_image, bootdev, mmc);
			if (!ret)
				return 0;
			...
		}
		...
		ret = mmc_load_image_raw_sector(spl_image, bootdev, mmc, ...);
		if (!ret)
			return 0;
		...
		/* If RAW mode fails, try FS mode. */
		fallthrough;
#ifdef CONFIG_SYS_MMCSD_FS_BOOT
	case MMCSD_MODE_FS:
		debug("spl: mmc boot mode: fs\n");

		ret = spl_mmc_do_fs_boot(spl_image, bootdev, mmc, filename);
		if (!ret)
			return 0;

		break;
#endif
```

- **FAT 模式**：到第 1 個分割區（`SYS_MMCSD_FS_BOOT_PARTITION=1`）找 `u-boot.img`（`SPL_FS_LOAD_PAYLOAD_NAME`）。BBB 的 SD 卡是這條路。
- **raw 模式**：從 sector `0x300`（384 KiB 處，`SYS_MMCSD_RAW_MODE_U_BOOT_SECTOR`）讀，失敗再退回 FAT。
- `spl_start_uboot()` 是 **Falcon mode** 的開關：`am335x_evm_defconfig` 開了 `SPL_OS_BOOT`，SPL 可以跳過 U-Boot 直接開 Linux。BBB 的實作（`board/ti/am335x/board.c` 的 `spl_start_uboot`）是：UART 收到 `c` 就開 U-Boot；否則讀 env，`boot_os` 不是 `1` 也開 U-Boot。SPL 的 env 是 `ENV_IS_NOWHERE`（只有預設值，沒設 `boot_os`），所以預設情況下一定進 U-Boot。

`u-boot.img` 是 FIT（`SPL_LOAD_FIT=y`），裡面除了 U-Boot 本體，還有多份 DTB。SPL 用 `board_fit_config_name_match` 依 EEPROM 板名挑出 BBB 那份，又是第 3a 步的結果。

## ⑥ 交棒：跳到 `0x8080_0000`

U-Boot proper 被放到 `CONFIG_TEXT_BASE=0x8080_0000`，`jump_to_image` 跳過去，SPL 的任務結束。之後 U-Boot proper 又從 `start.S` 的 `reset` 開始跑一次（同一份程式碼，`CONFIG_XPL_BUILD` 沒定義的那個版本），這次 `_main` 會走 relocation 那條路，把自己搬到 DRAM 頂端，就是上一篇看到的 `relocaddr = 0x9ff59000`。

## 自己驗證：不用動板子

```bash
git -C u-boot worktree add --detach ../ub-spl 709a97a05
cd ../ub-spl
make O=../ub-spl-out CROSS_COMPILE=arm-linux-gnueabihf- am335x_evm_defconfig
make O=../ub-spl-out CROSS_COMPILE=arm-linux-gnueabihf- -j$(nproc)

cd ../ub-spl-out
grep -E 'SPL_TEXT_BASE|SPL_MAX_SIZE|SPL_BSS_START|SPL_STACK_R_ADDR|CUSTOM_SYS_INIT_SP' .config
arm-linux-gnueabihf-readelf -S spl/u-boot-spl | grep -E 'text|data|bss'   # code 在 SRAM、BSS 在 DRAM
arm-linux-gnueabihf-nm spl/u-boot-spl | grep -E ' (_start|reset|save_boot_params|board_init_f|board_init_r)$'
xxd -s 0x200 -l 8 MLO                                                      # GP header
```

板子上能對照的：

```text
=> md.l 0x4030b424 1     # ROM boot params 指標（U-Boot proper 沒蓋掉的話）
=> md.l 0x44e10040 1     # CONTROL_STATUS：SYSBOOT 鎖存值
=> printenv board_name   # A335BNLT
```

## 小結

- SPL 一開始只有 SRAM，所以第一條指令就要先救 ROM 留下的 r0，因為後面「從哪裡載 U-Boot」全靠它。
- `board_init_f` 跑在沒有 DRAM 的世界：狀態只能放 `gd` 和 stack，不能碰 BSS。
- DDR 參數的來源鏈：EEPROM 板名 → `board_is_bone_lt()` → 寫死的 MT41K256M16HA125E 常數 → EMIF。
- DRAM 起來之後，SPL 只搬資料（BSS、malloc、stack、`gd`），code 仍留在 SRAM。
- 每一步的順序都是被硬體逼出來的：watchdog 先關、先調電壓再拉頻率、先讀 EEPROM 才設 DDR、DRAM 好了才清 BSS。

## 下一步

- 錄一份真正的 SPL log：UART 轉接器改插主機板直連埠（見上一篇的 USB hub 坑），開 `CONFIG_SPL_SERIAL` 的 debug 輸出，對照這篇的每一步。
- 換自己 build 的 MLO 上板，用 `CONFIG_DEBUG_UART` 在 `board_init_f` 之前就印東西。
- 試 Falcon mode：SPL 直接開 kernel，量省下多少時間。
- 同一條路線換成 arm64 與「SPL 當 BL2」形態（SPL 載 BL31、BL31 再把 U-Boot proper 當 BL33）：[SPL 當 BL2：arm64 pre-relocation 的三個約束，與 QEMU 的極限](./spl-as-bl2-arm64-internals.md)。
