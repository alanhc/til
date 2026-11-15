# 把 STM32F103 的 ROM bootloader 讀出來：從向量表、啟動組語一路追到 C 的 main

[上一篇](./dapboot-bluepill.md)在 Blue Pill 上跑開源的 dapboot。這篇回頭看晶片**出廠就燒好**的那支 bootloader：BOOT0 拉高開機時執行的 system memory bootloader（`0x1FFF_F000`）。

它不開源，ST 只公開協定文件（[AN2606](https://www.st.com/resource/en/application_note/an2606-introduction-to-system-memory-boot-mode-on-stm32-mcus-stmicroelectronics.pdf)、[AN3155](https://www.st.com/resource/en/application_note/an3155-usart-protocol-used-in-the-stm32-bootloader-stmicroelectronics.pdf)）。不過 ROM 沒有讀保護，接上 JTAG 就能整塊讀出來。這篇分兩半：

1. **靜態**：把 ROM dump 下來，用 `objdump`、`xxd`、`grep` 從向量表一路追到 C 的 `main`，每一步都附指令和輸出。
2. **動態**：不動 BOOT0 跳線，用 GDB 把 PC 指到 ROM 的進入點，**讓它在板子上真的跑一次**，在每個階段停下來看暫存器怎麼變。

走的是一條典型的開機路線：

> 硬體從向量表取 SP 和 PC → 啟動組語 → 初始化 RAM → 跳進 C 的 `main` → 設時脈、周邊 → 進入命令迴圈

版本說明：

- 板子是正版 STM32F103C8T6（medium-density，`DBGMCU_IDCODE 0x20036410`），除錯器沿用 [FT232H + OpenOCD](./ft232h-jtag-stm32.md)（xPack OpenOCD 0.12.0、Arm GNU Toolchain 14.3 的 GDB）。
- 讀出的 2KB system memory，SHA-256 開頭 `8e094a8b`。同型號不同批次的 ROM 內容可能不同，**以下位址是我這顆的**，照做時請對照自己的反組譯。
- 文中只節錄幾行反組譯來說明。**ROM 的 binary 和完整反組譯是 ST 的程式碼，不放進 repo**，要看請用腳本從自己的板子讀。

腳本放在 [`static/code/stm32f103-rom-bootloader/`](https://github.com/alanhc/til/tree/main/static/code/stm32f103-rom-bootloader)：

| 檔案 | 用途 |
|---|---|
| `dump_rom.tcl` | OpenOCD 腳本，讀出 system memory 和 option bytes |
| `disasm.sh` | 用 objdump 反組譯 |
| `run-rom.gdb` | GDB 腳本，在板子上一段一段跑 ROM（第二部分） |

## 先講結論

- 向量表只有 4 格：MSP `0x2000_01FC`、Reset、NMI、HardFault。**bootloader 只用 SRAM 開頭 512 bytes**。
- 啟動流程是 ARM 編譯器（Keil/ARMCC）的標準樣式：`Reset_Handler` → `__main` → `__scatterload` → `main`。
- 「初始化 RAM」在這顆 MCU 上只是設 SP、複製 `.data`、清 `.bss`。這支 ROM 的 scatter-load 表**是空的**，連 `.data`／`.bss` 都沒有，狀態全部放在 stack 上。
- `main` 不用外部石英：HSI/2 × 6 = **24MHz**，設好 PA9／PA10，再用 **SysTick 量主機送來的 `0x7F`** 算出鮑率。
- `main` 開頭複製到 stack 上的 16 bytes 常數，正好是 AN3155 **GET 指令的回應**：bootloader 版本 2.2 和支援的指令清單。
- 在板子上實跑驗證：`RCC_CFGR` 變成 `0x0010000A`、`GPIOA_CRH` 變成 `0x444444B4`、假設量到 115200 baud 時 `USART_BRR = 208`、`CR1 = 0x340C`，ACK 送出後 `USART_SR` 的 TXE/TC 都是 1。

## 先講清楚：MCU 沒有「DRAM 初始化」

看 Linux SoC 的開機流程時，常會看到 BL2 或 SPL 花很多力氣做 DDR 初始化（設控制器、PHY、training），因為外接 DRAM 不設定好根本不能用。

STM32F103 只有晶片內建的 **20KB SRAM**，上電就能讀寫，不需要任何初始化。所以 MCU 啟動碼裡的「RAM 初始化」指的是 C 語言執行環境的準備：

1. 設 stack pointer（Cortex-M 由硬體從向量表 `[0]` 載入，啟動碼常會再設一次）
2. 把有初值的全域變數（`.data`）從 flash 複製到 RAM
3. 把沒初值的全域變數（`.bss`）清成 0

做完這三件事才能跳進 C 的 `main`。下面就照這個順序看 ROM 怎麼做。

---

# 第一部分：靜態分析

## 步驟 1：把 ROM 讀出來

STM32F103 medium-density 的記憶體裡，跟這篇有關的區塊：

| 位址 | 大小 | 內容 |
|---|---|---|
| `0x0800_0000` | 64KB | 主 flash（使用者程式） |
| `0x1FFF_F000` | 2KB | **system memory**（ROM bootloader） |
| `0x1FFF_F800` | 16B | option bytes |
| `0x2000_0000` | 20KB | SRAM |

OpenOCD 腳本：

```tcl
# dump_rom.tcl
init
reset halt
dump_image sysmem.bin   0x1FFFF000 0x800
dump_image optbytes.bin 0x1FFFF800 0x10
echo [format "rom\[0\] MSP   = 0x%08x" [read_memory 0x1FFFF000 32 1]]
echo [format "rom\[1\] Reset = 0x%08x" [read_memory 0x1FFFF004 32 1]]
echo [format "F_SIZE       = %d KB"   [read_memory 0x1FFFF7E0 16 1]]
reset run
shutdown
```

執行：

```bash
openocd -f ft232h-jtag.cfg -f target/stm32f1x.cfg -f dump_rom.tcl
```

```text
Info : JTAG tap: stm32f1x.cpu tap/device found: 0x3ba00477 ...
Info : JTAG tap: stm32f1x.bs tap/device found: 0x16410041 ...
rom[0] MSP   = 0x200001fc
rom[1] Reset = 0x1ffff021
F_SIZE       = 64 KB
```

確認檔案：

```bash
ls -l sysmem.bin optbytes.bin
sha256sum sysmem.bin
```

```text
-rw-r--r-- 1 user 197121 2048 sysmem.bin
-rw-r--r-- 1 user 197121   16 optbytes.bin
8e094a8ba47344b5d6e8b5c36009b0671d842b4655210bd6f42805c319f6b9e9  sysmem.bin
```

這裡**不需要把 BOOT0 拉高**。除錯器直接讀 `0x1FFF_F000`，跟晶片從哪裡開機無關。我讀了兩次，hash 一樣。

順便看一下 option bytes：

```bash
xxd optbytes.bin
```

```text
00000000: a55a ff00 ff00 ff00 ff00 ff00 ff00 ff00  .Z..............
```

第一個 byte `0xA5` 是 RDP（讀保護）的「未保護」值，後面的 `0x5A` 是它的補數。如果 RDP 不是 `0xA5`，除錯器就讀不到 flash，但 system memory 還是讀得到。

## 步驟 2：反組譯

```bash
arm-none-eabi-objdump -D -b binary -marm -Mforce-thumb \
  --adjust-vma=0x1FFFF000 sysmem.bin > sysmem.dis
wc -l sysmem.dis
```

```text
783 sysmem.dis
```

三個參數的意思：

- `-b binary`：輸入是 raw binary，沒有 ELF 標頭。
- `-Mforce-thumb`：Cortex-M 只有 Thumb 指令，但 raw binary 沒有符號告訴 objdump，不加的話會當成 ARM 指令亂翻。
- `--adjust-vma=0x1FFFF000`：檔案裡的 offset 0 其實是位址 `0x1FFF_F000`。加了之後，反組譯顯示的位址、`bl` 的目標都會是真實位址，可以直接拿去 GDB 下中斷點。

**注意：objdump 會把所有東西都當成指令翻**，包括向量表和常數。看到 `UNDEFINED`、沒意義的 `lsls`，或一串 `ffff ffff`，多半是資料。所以下面會一直搭配 `xxd -e`（以 32-bit little-endian 顯示）來讀常數。

## 步驟 3：讀向量表

```bash
xxd -e -l 16 sysmem.bin
```

```text
00000000: 200001fc 1ffff021 1ffff765 1ffff767  ... !...e...g...
```

| offset | 值 | 意義 |
|---|---|---|
| `[0]` | `0x2000_01FC` | 初始 MSP |
| `[1]` | `0x1FFF_F021` | Reset |
| `[2]` | `0x1FFF_F765` | NMI |
| `[3]` | `0x1FFF_F767` | HardFault |

只有 4 格，`0x1FFF_F010` 就開始是程式碼了。這支 ROM 完全不用中斷（等事件都用輪詢），所以不需要完整的向量表。

幾個觀察：

- **MSP = `0x2000_01FC`**：stack 從 SRAM 第 512 bytes 往下長，整支 bootloader 只動 `0x2000_0000`～`0x2000_01FF`。AN2606 說 bootloader 會用到 RAM 開頭那一塊，從這裡就看得出來。
- **位址 bit0 都是 1**：這是 Thumb bit。Reset 寫 `0x1FFF_F021`，實際程式在 `0x1FFF_F020`。
- BOOT0 = 1 開機時，system memory 會被映射到 `0x0000_0000`，硬體從 `0x0` 讀向量表，讀到的就是這 4 格。

順手看 NMI 和 HardFault 做什麼：

```bash
grep -A1 -E '^1ffff764|^1ffff766' sysmem.dis
```

```text
1ffff764:	4770      	bx	lr
1ffff766:	f7ff bc67 	b.w	0x1ffff038
```

```bash
awk '/^1ffff038/,/^1ffff03e/' sysmem.dis
xxd -e -s 0x42c -l 8 sysmem.bin
```

```text
1ffff038:	49fd      	ldr	r1, [pc, #1012]	@ (0x1ffff430)
1ffff03a:	48fc      	ldr	r0, [pc, #1008]	@ (0x1ffff42c)
1ffff03c:	6008      	str	r0, [r1, #0]
1ffff03e:	4770      	bx	lr
0000042c: 05fa0004 e000ed0c
```

- NMI：`bx lr`，直接返回，等於忽略。
- HardFault：把 `0x05FA_0004` 寫到 `0xE000_ED0C`（`SCB->AIRCR`）。`0x05FA` 是 VECTKEY，bit2 是 `SYSRESETREQ`，也就是**出錯就整顆重開**。

## 步驟 4：Reset_Handler

Reset 指到 `0x1FFF_F020`：

```bash
awk '/^1ffff020/,/^1ffff024/' sysmem.dis
xxd -e -s 0x024 -l 4 sysmem.bin
```

```text
1ffff020:	4800      	ldr	r0, [pc, #0]	@ (0x1ffff024)
1ffff022:	4700      	bx	r0
1ffff024:	f011 1fff 	tst.w	r1, #16711935	@ 0xff00ff
00000024: 1ffff011
```

`0x1FFF_F024` 那行 objdump 翻成 `tst.w`，但它其實是 `ldr r0, [pc, #0]` 要讀的常數（literal pool）。用 `xxd -e` 看就清楚了：`0x1FFF_F011`。

所以 `Reset_Handler` 只做一件事：跳到 `0x1FFF_F010`（bit0 是 Thumb bit）。

這跟 Keil 啟動檔 `startup_stm32f10x_md.s` 的寫法一樣：

```text
Reset_Handler   PROC
                LDR     R0, =__main
                BX      R0
```

`__main` 是 ARM 編譯器 runtime 提供的進入點，不是你寫的 `main`。

## 步驟 5：`__main`

```bash
awk '/^1ffff010/,/^1ffff01c/' sysmem.dis
```

```text
1ffff010:	f8df d004 	ldr.w	sp, [pc, #4]	@ 0x1ffff018
1ffff014:	f000 fbaa 	bl	0x1ffff76c
1ffff018:	01fc      	lsls	r4, r7, #7
1ffff01a:	2000      	movs	r0, #0
1ffff01c:	4700      	bx	r0
```

- `ldr.w sp, [pc, #4]`：從 `0x1FFF_F018` 讀 SP。那裡的兩個 halfword `01fc 2000` 合起來是 `0x2000_01FC`，跟向量表 `[0]` 一樣。硬體其實已經設過了，啟動碼保險起見再設一次。
- `bl 0x1ffff76c`：呼叫 `__scatterload`。
- `0x1FFF_F01C` 的 `bx r0` 是一個小跳板，等一下 `__scatterload` 會用它跳進 `main`。

## 步驟 6：`__scatterload`，也就是 RAM 初始化

```bash
awk '/^1ffff76c/,/^1ffff786/' sysmem.dis
xxd -e -s 0x78c -l 12 sysmem.bin
```

```text
1ffff76c:	4c07      	ldr	r4, [pc, #28]	@ (0x1ffff78c)
1ffff76e:	4d08      	ldr	r5, [pc, #32]	@ (0x1ffff790)
1ffff770:	e006      	b.n	0x1ffff780
1ffff772:	68e0      	ldr	r0, [r4, #12]
1ffff774:	f040 0301 	orr.w	r3, r0, #1
1ffff778:	e894 0007 	ldmia.w	r4, {r0, r1, r2}
1ffff77c:	4798      	blx	r3
1ffff77e:	3410      	adds	r4, #16
1ffff780:	42ac      	cmp	r4, r5
1ffff782:	d3f6      	bcc.n	0x1ffff772
1ffff784:	4803      	ldr	r0, [pc, #12]	@ (0x1ffff794)
1ffff786:	f7ff fc49 	bl	0x1ffff01c
0000078c: 1ffff7a8 1ffff7a8 1ffff34d
```

翻成 C 大概是：

```c
struct region { void *src, *dst; uint32_t len; void (*fn)(void*, void*, uint32_t); };

for (struct region *r = table_start; r < table_end; r++)
    r->fn(r->src, r->dst, r->len);   /* 複製 .data、清 .bss，或解壓縮 */

main();                               /* r0 = 0x1FFFF34D, bx r0 */
```

ARM 編譯器不像 GCC 那樣在啟動碼裡寫死「複製 `.data`、清 `.bss`」兩個迴圈，而是由 linker 產生一張**區段表**，每筆 16 bytes：來源、目的、長度、處理函式。`__scatterload` 只負責逐筆呼叫。

literal pool 裡三個常數：

| 位址 | 值 | 意義 |
|---|---|---|
| `0x1FFF_F78C` | `0x1FFF_F7A8` | 區段表起點 |
| `0x1FFF_F790` | `0x1FFF_F7A8` | 區段表終點 |
| `0x1FFF_F794` | `0x1FFF_F34D` | `main`（帶 Thumb bit） |

**起點等於終點**，迴圈一次都不會執行。也就是說，這支 ROM 沒有任何需要初始化的全域變數。以 2KB 的 bootloader 來說很合理：狀態全部放在 `main` 的 stack frame 裡，連 `.bss` 都省了。

這也回答了「沒有符號表，怎麼找 `main`」：**`__scatterload` 最後載入的那個位址就是 `main`**。

對照 GCC：[dapboot](./dapboot-bluepill.md) 用的 libopencm3 是在 `reset_handler` 裡直接寫迴圈，用 linker script 給的 `_data_loadaddr`、`_data`、`_edata`、`_ebss` 這些符號複製和清零，再 `main()`。兩邊做的事情一樣，只是工具鏈不同。

## 步驟 7：先認出常用的小函式

`main` 很長，直接讀會迷路。先統計哪些函式最常被呼叫：

```bash
grep -oE 'bl\s+0x1ffff[0-9a-f]+' sysmem.dis | sort | uniq -c | sort -rn | head -6
```

```text
     29 bl	0x1ffff040
     23 bl	0x1ffff028
     15 bl	0x1ffff1e2
      8 bl	0x1ffff056
      5 bl	0x1ffff132
      5 bl	0x1ffff04a
```

這些函式都只有幾條指令，再搭配 literal pool 就能認出來：

```bash
xxd -e -s 0x428 -l 24 sysmem.bin
```

```text
00000428: 40013000 05fa0004 e000ed0c 40022000  .0.@......... .@
00000438: 45670123 cdef89ab                    #.gE....
```

- `0x4001_3000` + `0x800` = `0x4001_3800`：**USART1**
- `0x4002_2000`：**FLASH 介面暫存器**
- `0x4567_0123`、`0xCDEF_89AB`：RM0008 裡解鎖 flash 的 KEY1、KEY2

| 函式 | 內容 | 身分 |
|---|---|---|
| `0x1FFF_F028` | 寫 `USART1_DR`，等 `SR` bit6（TC） | **putc** |
| `0x1FFF_F1E2` | 迴圈裡餵 IWDG（`KR = 0xAAAA`），等 `SR` bit5（RXNE），讀 `DR` | **getc** |
| `0x1FFF_F040` | 輪詢 `FLASH_SR` bit0（BSY） | **等 flash 忙完** |
| `0x1FFF_F056` | 把 KEY1、KEY2 寫進 `FLASH_KEYR` | **解鎖 flash** |
| `0x1FFF_F04A` | 把 KEY1、KEY2 寫進 `FLASH_OPTKEYR` | **解鎖 option bytes** |

例如 getc：

```bash
awk '/^1ffff1e2/,/^1ffff1f6/' sysmem.dis
```

```text
1ffff1e2:	4a91      	ldr	r2, [pc, #580]	@ (0x1ffff428)
1ffff1e4:	f64a 20aa 	movw	r0, #43690	@ 0xaaaa
1ffff1e8:	4996      	ldr	r1, [pc, #600]	@ (0x1ffff444)
1ffff1ea:	e000      	b.n	0x1ffff1ee
1ffff1ec:	6008      	str	r0, [r1, #0]
1ffff1ee:	f8b2 3800 	ldrh.w	r3, [r2, #2048]	@ 0x800
1ffff1f2:	069b      	lsls	r3, r3, #26
1ffff1f4:	d5fa      	bpl.n	0x1ffff1ec
1ffff1f6:	f8b2 0804 	ldrh.w	r0, [r2, #2052]	@ 0x804
```

`r2 = 0x4001_3000`，`[r2, #0x800]` 是 `USART1_SR`。`lsls r3, r3, #26` 把 bit5 推到 bit31（符號位元），`bpl` 就是「bit5 為 0 就繼續等」。等待期間一直寫 `0xAAAA` 到 `0x4000_3000`（`IWDG_KR`）餵狗。最後從 `0x4001_3804`（`USART1_DR`）讀出一個 byte。

`lsls #N` 加 `bpl`／`bmi` 是 ARM 編譯器測試單一位元的慣用寫法：把 bit `31-N` 推到符號位元，再用條件分支判斷。後面會一直看到。

## 步驟 8：讀 `main` 的前段

`main` 從 `0x1FFF_F34C` 開始。先把它用到的常數一次讀出來：

```bash
xxd -e -s 0x444 -l 4 sysmem.bin
xxd -e -s 0x464 -l 24 sysmem.bin
```

```text
00000444: 40003000
00000464: 40021000 42420000 00100002 444444b4  ...@..BB.....DDD
00000474: 40010000 40013804                    ...@.8.@
```

| 常數 | 對照 RM0008 |
|---|---|
| `0x4000_3000` | IWDG |
| `0x4002_1000` | RCC |
| `0x4242_0000` | RCC 的 **bit-band 別名區** |
| `0x0010_0002` | 要寫進 `RCC_CFGR` 的值 |
| `0x4444_44B4` | 要寫進 `GPIOA_CRH` 的值 |
| `0x4001_0000` | AFIO／GPIO 區（`+0x800` 是 GPIOA） |
| `0x4001_3804` | `USART1_DR` |

接著一段一段看：

```bash
awk '/^1ffff34c/,/^1ffff3aa/' sysmem.dis
```

### 8-1：把 GET 回應複製到 stack、關中斷

```text
1ffff34c:	e92d 4ff0 	stmdb	sp!, {r4, ..., lr}
1ffff350:	a140      	add	r1, pc, #256	@ (adr r1, 0x1ffff454)
1ffff352:	c93c      	ldmia	r1!, {r2, r3, r4, r5}
1ffff354:	b0c5      	sub	sp, #276	@ 0x114
1ffff356:	a801      	add	r0, sp, #4
1ffff358:	c03c      	stmia	r0!, {r2, r3, r4, r5}
1ffff35a:	f000 fa23 	bl	0x1ffff7a4
```

從 `0x1FFF_F454` 讀 16 bytes 放到 stack 上的區域變數。內容：

```bash
xxd -s 0x454 -l 16 sysmem.bin
```

```text
00000454: 790b 2200 0102 1121 3143 6373 8292 7900  y."....!1Ccs..y.
```

```text
79  0B  22  00 01 02 11 21 31 43 63 73 82 92  79
ACK N   版本 └────────── 支援的指令 ──────────┘ ACK
```

這就是 AN3155 **GET 指令（`0x00`）的回應**：

- `0x0B`：後面還有 11 + 1 = 12 bytes（版本 + 11 個指令）
- `0x22`：bootloader 版本 2.2
- 指令：Get、Get Version、Get ID、Read Memory、Go、Write Memory、Erase、Write Protect、Write Unprotect、Readout Protect、Readout Unprotect

在 C 裡大概就是 `uint8_t get_reply[] = { 0x79, 0x0B, 0x22, ... };` 這種區域陣列，編譯器把初值放在 ROM，進函式時複製到 stack。

`bl 0x1ffff7a4` 呼叫的是：

```text
1ffff7a4:	b672      	cpsid	i
1ffff7a6:	4770      	bx	lr
```

`__disable_irq()`，關中斷。

### 8-2：IWDG

```text
1ffff35e:	4a39      	ldr	r2, [pc, #228]	@ (0x1ffff444)   ; IWDG
1ffff360:	f245 5055 	movw	r0, #21845	@ 0x5555
1ffff364:	6010      	str	r0, [r2, #0]                      ; KR = 0x5555
1ffff366:	2006      	movs	r0, #6
1ffff368:	6050      	str	r0, [r2, #4]                      ; PR = 6
1ffff36a:	f64a 23aa 	movw	r3, #43690	@ 0xaaaa
1ffff36e:	6013      	str	r3, [r2, #0]                      ; KR = 0xAAAA
```

`0x5555` 解鎖 `PR`／`RLR` 的寫入，`PR = 6` 是最大的 /256 預除頻，`0xAAAA` 重新載入計數。

注意它**沒有寫 `0xCCCC`**（啟動看門狗），所以 IWDG 正常情況下不會被它打開。這段是為了 option bytes 設了「硬體看門狗」（上電自動啟動）的情況：把逾時拉到最長，再搭配 getc 裡的餵狗，bootloader 等主機時才不會被重開。

### 8-3：時脈切到 PLL 24MHz

```text
1ffff370:	483c      	ldr	r0, [pc, #240]	@ (0x1ffff464)   ; RCC
1ffff372:	f44f 1180 	mov.w	r1, #1048576	@ 0x100000
1ffff376:	6041      	str	r1, [r0, #4]                      ; CFGR = 0x00100000
1ffff378:	4c3b      	ldr	r4, [pc, #236]	@ (0x1ffff468)   ; 0x42420000
1ffff37a:	2101      	movs	r1, #1
1ffff37c:	6621      	str	r1, [r4, #96]	@ 0x60              ; PLLON = 1
1ffff37e:	6801      	ldr	r1, [r0, #0]
1ffff380:	0189      	lsls	r1, r1, #6
1ffff382:	d5fc      	bpl.n	0x1ffff37e                        ; 等 PLLRDY
1ffff384:	4837      	ldr	r0, [pc, #220]
1ffff386:	4939      	ldr	r1, [pc, #228]                    ; 0x00100002
1ffff388:	6041      	str	r1, [r0, #4]                      ; CFGR = 0x00100002
1ffff38a:	f244 0104 	movw	r1, #16388	@ 0x4004
1ffff38e:	6181      	str	r1, [r0, #24]                     ; APB2ENR = 0x4004
```

- `RCC_CFGR = 0x0010_0000`：bit21:18 `PLLMUL = 0100` 是 ×6，bit16 `PLLSRC = 0` 是 HSI/2。8MHz / 2 × 6 = **24MHz**。
- `0x4242_0060`：**bit-band 別名**。公式是 `0x4200_0000 + (周邊 offset × 32) + (bit × 4)`，代入 `RCC_CR`（offset `0x2_1000`）的 bit24（PLLON）：`0x4200_0000 + 0x42_0000 + 0x60` = `0x4242_0060`。寫 1 就只改這一個位元，不用讀－改－寫。
- `lsls r1, r1, #6` + `bpl`：測 bit25（PLLRDY），等 PLL 鎖定。
- `RCC_CFGR = 0x0010_0002`：bit1:0 `SW = 10`，系統時脈切到 PLL。
- `RCC_APB2ENR = 0x4004`：bit14 USART1EN、bit2 IOPAEN。

只用內部 HSI 的好處是：不管板子上接了什麼石英，甚至沒接，bootloader 都能跑。代價是 HSI 有約 ±1% 的誤差，所以鮑率不能寫死，要現場量。

### 8-4：VTOR、GPIO、SysTick

```text
1ffff390:	2400      	movs	r4, #0
1ffff392:	f04f 26e0 	mov.w	r6, #3758153728	@ 0xe000e000
1ffff396:	f8c6 4d08 	str.w	r4, [r6, #3336]	@ 0xd08        ; VTOR = 0
1ffff39a:	4836      	ldr	r0, [pc, #216]                    ; 0x40010000
1ffff39c:	4934      	ldr	r1, [pc, #208]                    ; 0x444444B4
1ffff39e:	f8c0 1804 	str.w	r1, [r0, #2052]	@ 0x804        ; GPIOA_CRH
1ffff3a2:	2104      	movs	r1, #4
1ffff3a4:	6131      	str	r1, [r6, #16]                     ; SysTick CTRL = 4
1ffff3a6:	00c1      	lsls	r1, r0, #3
1ffff3a8:	6171      	str	r1, [r6, #20]                     ; SysTick LOAD
```

- `SCB->VTOR = 0`：BOOT0 = 1 時位址 0 映射到 system memory，向量表就在那裡。
- `GPIOA_CRH = 0x4444_44B4`：每個腳位 4 bits。PA9 是 `0xB`（`MODE = 11` 50MHz 輸出、`CNF = 10` 複用推挽），當 **TX**；PA10 是 `0x4`（浮接輸入），當 **RX**。
- `SysTick CTRL = 4`：時脈源用核心時脈，先不啟動。
- `LOAD = 0x4001_0000 << 3`：左移 3 位後超出 32 bit 的部分被截掉，剩 `0x0008_0000`。編譯器借用了暫存器裡現成的值來省一條指令。

## 步驟 9：自動鮑率偵測

```bash
awk '/^1ffff3aa/,/^1ffff3f4/' sysmem.dis
```

```text
1ffff3aa:	ldr.w	r1, [r0, #2056]	@ 0x808   ; GPIOA_IDR
1ffff3ae:	lsls	r1, r1, #21                   ; bit10 = PA10
1ffff3b0:	bpl.n	0x1ffff3aa                    ; 等 RX = 1（閒置）
1ffff3b2:	ldr.w	r1, [r0, #2056]
1ffff3b6:	lsls	r1, r1, #21
1ffff3b8:	bmi.n	0x1ffff3b2                    ; 等 RX = 0（起始位元）
1ffff3ba:	ldr.w	r1, [r0, #2056]
1ffff3be:	lsls	r1, r1, #21
1ffff3c0:	bpl.n	0x1ffff3ba                    ; 等 RX = 1（bit0）
1ffff3c2:	movs	r1, #5
1ffff3c4:	str	r1, [r6, #16]                 ; SysTick 啟動
1ffff3c6:	ldr.w	r1, [r0, #2056]
1ffff3ca:	lsls	r1, r1, #21
1ffff3cc:	bmi.n	0x1ffff3c6                    ; 等 RX = 0（bit7）
1ffff3ce:	ldr	r0, [r6, #24]                 ; SysTick VAL
1ffff3d0:	movs	r1, #0
1ffff3d2:	rsb	r5, r0, #524288	@ 0x80000   ; r5 = 0x80000 - VAL
1ffff3d6:	ldr	r0, [pc, #160]                ; 0x40013804
1ffff3d8:	strh	r1, [r0, #0]                  ; USART1_DR = 0
1ffff3da:	movs	r4, #7
1ffff3dc:	udiv	r4, r5, r4                    ; r4 = r5 / 7
1ffff3e0:	strh	r4, [r0, #4]                  ; USART1_BRR
...
1ffff3ec:	movw	r1, #13324	@ 0x340c
1ffff3f0:	strh	r1, [r0, #8]                  ; USART1_CR1 = 0x340C
1ffff3f2:	movs	r0, #121	@ 0x79
1ffff3f4:	bl	0x1ffff028                    ; putc(0x79)，ACK
```

AN3155 規定主機要先送一個 `0x7F`。UART 先送 LSB，所以線上的波形是：

```text
閒置  起始  b0 b1 b2 b3 b4 b5 b6  b7  停止
 1     0    1  1  1  1  1  1  1   0    1
            └──── 7 個位元時間 ───┘
```

從 bit0 上升開始計時，到 bit7 下降停止，剛好是 **7 個位元時間**。SysTick 是遞減計數器，所以經過的 tick 數是 `LOAD - VAL`。

SysTick 和 USART1 都吃同一個 24MHz 時脈，所以「每個位元有幾個 tick」直接就是 `USART_BRR` 該填的值：

```text
USART_BRR = f_PCLK2 / baud = (每位元的 tick 數) = elapsed / 7
```

不必知道實際的時脈是多少，HSI 的誤差也在這一步被抵消了。

`USART1_CR1 = 0x340C` 的位元：

| bit | 名稱 | 意義 |
|---|---|---|
| 13 | UE | 開 USART |
| 12 | M | 9 bit 字長 |
| 10 | PCE | 開 parity |
| 9 | PS = 0 | even parity |
| 3 | TE | 開發送 |
| 2 | RE | 開接收 |

9 bit 裡有 1 bit 是 parity，所以實際是 **8 data + even parity + 1 stop（8E1）**，正是 AN3155 規定的格式。最後送出 `0x79`（ACK），告訴主機鮑率已經對上了。

## 步驟 10：命令迴圈

```text
1ffff3fa:	ldr	r0, [pc, #72]          ; IWDG
1ffff3fc:	movw	r1, #43690	@ 0xaaaa
1ffff400:	str	r1, [r0, #0]           ; 餵狗
1ffff402:	bl	0x1ffff1e2             ; r4 = getc()  指令碼
1ffff406:	mov	r4, r0
1ffff408:	bl	0x1ffff1e2             ; r0 = getc()  補數
1ffff40c:	eor.w	r1, r0, r4
1ffff410:	cmp	r1, #255
1ffff412:	beq.n	0x1ffff416
1ffff414:	movs	r4, #85	@ 0x55         ; 不是補數 → 當成無效指令
1ffff416:	cmp	r4, #49	@ 0x31         ; 0x31 Write Memory？
1ffff418:	beq.n	0x1ffff518
...
```

AN3155 的每個指令都是「指令碼 + 補數」（例如 GET 是 `0x00 0xFF`），兩個 byte 的 XOR 必須是 `0xFF`。不對就把指令碼改成 `0x55`（不在清單裡），讓後面的分派回 NACK。

後面那串 `cmp` / `beq` / `bgt` 是編譯器把 `switch (cmd)` 翻成的**二分搜尋**：先比 `0x31`，大於就跳到另一半去比，小於再比 `0x02`……

## 步驟 11：ROM 尾端的常數

```bash
xxd -s 0x7a8 -l 0x58 sysmem.bin
```

`0x1FFF_F7A8` 之後是一串 `ffff`（未使用），最後一段不是程式：

```bash
xxd -s 0x7e0 -l 8 sysmem.bin
```

```text
000007e0: 4000 ffff cd06 2905                      @.....).
```

- `0x1FFF_F7E0`：Flash 大小，`0x0040` = 64KB
- `0x1FFF_F7E8` 起 12 bytes：96-bit 的晶片 UID（每顆不同，這裡不列）

這兩個在 RM0008 裡叫 device electronic signature，是工廠寫入的，和 bootloader 放在同一塊唯讀區。

---

# 第二部分：在板子上實際跑一次

靜態讀完，接著讓它真的跑。**不需要動 BOOT0 跳線**：用除錯器把 MSP 和 PC 設成 ROM 向量表的值，就等於模擬「從 system memory 開機」。

做法：

1. `monitor reset halt`：重開並停在第一條指令。這時所有周邊都是重開後的初始值。
2. 手動載入 MSP、PC、xPSR（Thumb bit）。
3. 在關鍵位址下硬體中斷點（ROM 不能寫軟體中斷點，一定要 `hbreak`），每停一次就讀暫存器。

開兩個終端機。第一個開 OpenOCD：

```bash
openocd -f ft232h-jtag.cfg -f target/stm32f1x.cfg
```

第二個跑 GDB 腳本：

```bash
arm-none-eabi-gdb -q -batch -x run-rom.gdb
```

下面把腳本拆開，逐段看輸出。

## 步驟 12：模擬 BOOT0 = 1

```gdb
target extended-remote localhost:3333
monitor reset halt
x/4xw 0x1FFFF000
set $xpsr = 0x01000000
set $msp = *(unsigned*)0x1FFFF000
set $pc  = *(unsigned*)0x1FFFF004 & ~1
printf "msp=0x%08x pc=0x%08x\n", $msp, $pc
```

```text
[stm32f1x.cpu] halted due to debug-request, current mode: Thread
xPSR: 0x01000000 pc: 0x08001040 msp: 0x20005000
0x1ffff000:	0x200001fc	0x1ffff021	0x1ffff765	0x1ffff767
msp=0x200001fc pc=0x1ffff020
```

`reset halt` 停在 `0x0800_1040`，那是 flash 裡 dapboot 的 Reset。接著把 MSP 和 PC 換成 ROM 的：

- `$xpsr = 0x01000000`：bit24 是 T（Thumb）位元，Cortex-M 必須是 1。
- `$pc` 要把 bit0 清掉（`& ~1`）。硬體從向量表載入時會自動處理 Thumb bit，手動設 PC 時要自己做。

## 步驟 13：逐條跑 Reset_Handler 和 `__main`

```gdb
set $i = 0
while $i < 4
  x/i $pc
  stepi
  printf "   -> pc=0x%08x r0=0x%08x sp=0x%08x\n", $pc, $r0, $sp
  set $i = $i + 1
end
```

```text
=> 0x1ffff020:	ldr	r0, [pc, #0]	@ (0x1ffff024)
   -> pc=0x1ffff022 r0=0x1ffff011 sp=0x200001fc
=> 0x1ffff022:	bx	r0
   -> pc=0x1ffff010 r0=0x1ffff011 sp=0x200001fc
=> 0x1ffff010:	ldr.w	sp, [pc, #4]	@ 0x1ffff018
   -> pc=0x1ffff014 r0=0x1ffff011 sp=0x200001fc
=> 0x1ffff014:	bl	0x1ffff76c
   -> pc=0x1ffff76c r0=0x1ffff011 sp=0x200001fc
```

和靜態分析一致：`r0` 載入 `0x1FFF_F011`，`bx` 後 PC 落在 `0x1FFF_F010`（bit0 被拿去當 Thumb bit），設 SP，然後進 `__scatterload`。

## 步驟 14：確認區段表是空的，進入 `main`

```gdb
stepi
stepi
printf "r4(table start)=0x%08x r5(table end)=0x%08x\n", $r4, $r5
hbreak *0x1FFFF34C
continue
printf "pc=0x%08x lr=0x%08x sp=0x%08x\n", $pc, $lr, $sp
```

```text
r4(table start)=0x1ffff7a8 r5(table end)=0x1ffff7a8
Breakpoint 1, 0x1ffff34c in ?? ()
pc=0x1ffff34c lr=0x1ffff78b sp=0x200001fc
```

`r4 == r5`，迴圈不會執行，直接到 `main`。`lr = 0x1FFF_F78B` 是 `bl 0x1ffff01c` 的下一條（帶 Thumb bit），也就是 `main` 如果 return 會回到 `__scatterload` 後面。實際上 `main` 是無窮迴圈，不會回來。

## 步驟 15：`main` 每個階段的暫存器

先記下初始值：

```gdb
printf "before: RCC_CR=0x%08x RCC_CFGR=0x%08x APB2ENR=0x%08x GPIOA_CRH=0x%08x\n", \
  *(unsigned*)0x40021000, *(unsigned*)0x40021004, *(unsigned*)0x40021018, *(unsigned*)0x40010804
```

```text
before: RCC_CR=0x00005583 RCC_CFGR=0x00000000 APB2ENR=0x00000000 GPIOA_CRH=0x88844444
```

重開後的狀態：`RCC_CR` 只有 HSION／HSIRDY（加上出廠的 HSI 校正值），`CFGR = 0` 表示跑在 HSI 8MHz，`GPIOA_CRH` 是預設的浮接輸入（`0x4`）。PA13～PA15 是 `0x8`（帶上下拉的輸入），因為它們是 JTAG 腳。

**複製 GET 回應、關中斷之後**（`hbreak *0x1FFFF35E`）：

```text
[stack copy] sp=0x200000c4, GET reply on stack:
0x200000c8:	0x79	0x0b	0x22	0x00	0x01	0x02	0x11	0x21
0x200000d0:	0x31	0x43	0x63	0x73	0x82	0x92	0x79	0x00
PRIMASK=1
```

- SP 從 `0x2000_01FC` 降到 `0x2000_00C4`：push 9 個暫存器（36 bytes）加 `sub sp, #276`，共 312 bytes。整支 bootloader 的 stack 用量在這裡就差不多定了，離 `0x2000_0000` 還有 196 bytes。
- 那 16 bytes 確實出現在 stack 上（`sp + 4`）。
- `PRIMASK = 1`：中斷已關。

**PLL 鎖定後**（`hbreak *0x1FFFF384`）：

```text
[PLL]  RCC_CR=0x03005583 RCC_CFGR=0x00100000
```

`RCC_CR` 多了 `0x0300_0000`：bit24 PLLON、bit25 PLLRDY。

**切換時脈、開周邊時脈後**（`hbreak *0x1FFFF390`）：

```text
[SW]   RCC_CFGR=0x0010000a APB2ENR=0x00004004
```

寫進去的是 `0x0010_0002`，讀回來是 `0x0010_000A`。多出來的 `0x8` 是 bit3:2 **SWS = 10**，硬體回報「系統時脈已經是 PLL」。從這一刻起 CPU 跑在 24MHz。

**GPIO、SysTick 設定後**（`hbreak *0x1FFFF3AA`）：

```text
[IO]   VTOR=0x00000000 GPIOA_CRH=0x444444b4 SysTick CTRL=0x4 LOAD=0x80000
```

全部和靜態分析算出來的一樣。

## 步驟 16：看它卡在自動鮑率迴圈

```gdb
set $i = 0
while $i < 6
  x/i $pc
  stepi
  set $i = $i + 1
end
printf "GPIOA_IDR=0x%04x PA10=%d\n", *(unsigned*)0x40010808, (*(unsigned*)0x40010808 >> 10) & 1
```

```text
=> 0x1ffff3aa:	ldr.w	r1, [r0, #2056]	@ 0x808
=> 0x1ffff3ae:	lsls	r1, r1, #21
=> 0x1ffff3b0:	bpl.n	0x1ffff3aa
=> 0x1ffff3b2:	ldr.w	r1, [r0, #2056]	@ 0x808
=> 0x1ffff3b6:	lsls	r1, r1, #21
=> 0x1ffff3b8:	bmi.n	0x1ffff3b2
GPIOA_IDR=0x57ff PA10=1
```

PA10 讀到 1（線路閒置），第一個「等 RX = 1」馬上通過，接著在第二個迴圈（`0x1FFF_F3B2`～`0x1FFF_F3B8`）**一直繞**，等起始位元。我的 PA10 沒有接 USB 轉 UART，所以它會永遠等下去。

## 步驟 17：假裝量到 115200 baud

沒有真的 UART，就用除錯器跳過量測，直接把「量到的 tick 數」塞進 `r5`：

```text
r5 = 24,000,000 / 115,200 × 7 ≈ 1458
```

```gdb
set $pc = 0x1FFFF3D6
set $r5 = 1458
set $r1 = 0
hbreak *0x1FFFF3F2
continue
printf "[USART1] BRR=0x%04x (%d) CR1=0x%04x\n", *(unsigned*)0x40013808, *(unsigned*)0x40013808, *(unsigned*)0x4001380C
```

```text
Breakpoint 6, 0x1ffff3f2 in ?? ()
[USART1] BRR=0x00d0 (208) CR1=0x340c
```

`1458 / 7 = 208`，而 `24MHz / 115200 = 208.3`，對上了。`CR1 = 0x340C` 就是 8E1。

再往下跑過 `putc(0x79)`：

```gdb
hbreak *0x1FFFF3F8
continue
printf "[ACK]  0x79 sent, USART1_SR=0x%04x\n", *(unsigned*)0x40013800
x/6i $pc
```

```text
Breakpoint 7, 0x1ffff3f8 in ?? ()
[ACK]  0x79 sent, USART1_SR=0x00c0
=> 0x1ffff3f8:	ldr	r7, [pc, #48]	@ (0x1ffff42c)
   0x1ffff3fa:	ldr	r0, [pc, #72]	@ (0x1ffff444)
   0x1ffff3fc:	movw	r1, #43690	@ 0xaaaa
   0x1ffff400:	str	r1, [r0, #0]
   0x1ffff402:	bl	0x1ffff1e2
   0x1ffff406:	mov	r4, r0
```

`USART1_SR = 0xC0`：bit7 TXE（發送緩衝空）、bit6 TC（發送完成），ACK 已經從 PA9 送出去了。如果 PA9 有接 USB 轉 UART、終端機設成 115200 8E1，這時會收到一個 `0x79`。

下一步是 `bl 0x1ffff1e2`（getc），會在那裡等主機送指令。到這裡整條開機路徑就走完了。

最後讓板子回到正常狀態：

```gdb
monitor reset run
detach
```

`reset run` 會照 BOOT0 = 0 從 flash 開機，回到 dapboot 和 app。

---

## 跟開源 bootloader 對照

ST 的 SDK 沒有這支 ROM 的原始碼，但 [STM32CubeF1](https://github.com/STMicroelectronics/STM32CubeF1/tree/c7656f1fee178058be2f8ebfc8df9eaf91dc565e) 有 IAP 範例（USART + Ymodem），放在 `Projects/STM3210E_EVAL/Applications/IAP/`。它跳到 app 的寫法，跟 dapboot 幾乎一樣：

```c
/* IAP_Main/Src/main.c */
if (((*(__IO uint32_t*)APPLICATION_ADDRESS) & 0x2FFE0000) == 0x20000000)
{
  JumpAddress = *(__IO uint32_t*) (APPLICATION_ADDRESS + 4);
  JumpToApplication = (pFunction) JumpAddress;
  __set_MSP(*(__IO uint32_t*) APPLICATION_ADDRESS);
  JumpToApplication();
}
```

|  | ROM bootloader | STM32CubeF1 IAP 範例 | dapboot |
|---|---|---|---|
| 位置 | system memory `0x1FFF_F000` | flash `0x0800_0000` | flash `0x0800_0000` |
| 進入條件 | BOOT0 = 1 | 按鍵按下 | `BKP_DR1` magic、BOOT1、app SP 無效 |
| 時脈 | HSI → PLL 24MHz | HSE → PLL 72MHz | HSE → PLL 72MHz |
| 傳輸 | USART1，自動鮑率 | USART，Ymodem | USB DFU |
| `.data`／`.bss` | 無（scatter-load 表為空） | 有 | 有 |
| app 位址 | 由主機的 Go 指令決定 | `0x0800_4000` | `0x0800_2000` |
| 誰設 app 的 VTOR | 不設 | app 自己（`VECT_TAB_OFFSET`） | bootloader 跳之前先設 |
| app 有效性檢查 | 無 | 初始 SP 在 RAM | 初始 SP 在 RAM |

`& 0x2FFE0000 == 0x20000000` 這個檢查在 Cube 範例和 dapboot 裡一模一樣，是 STM32 社群通用的寫法：只確認 app 向量表 `[0]` 指到 SRAM 範圍，沒有 CRC 也沒有簽章。

網路上自己寫 bootloader 的教學也幾乎都照抄這行，例如這篇在 STM32F767 上用 Keil 做跳轉的[教學](https://blog.csdn.net/hxj0323/article/details/108414536)：app 放在 `0x0800_8000`、`VECT_TAB_OFFSET` 改成 `0x8000`，跳轉前一樣用 `0x2FFE0000` 檢查 SP。

照抄時要注意這個 mask 的範圍：`0x2FFE0000` 只留下 bit17 以上，所以只接受 `0x2000_0000`～`0x2001_FFFF`，也就是 **RAM 前 128KB**。F103 只有 20KB，怎麼放都在範圍內；但 F767 有 512KB SRAM，如果 app 的初始 SP 設在 RAM 頂端（GCC／CubeIDE 的 linker script 通常把 `_estack` 放在 `0x2008_0000`），檢查會失敗，bootloader 就不會跳。Keil 的啟動檔通常把 stack 配置在 RAM 前段，所以那篇用 Keil 才沒遇到。RAM 比較大的型號，應該改成直接比較 SP 是否落在該晶片的 SRAM 起訖位址之間。

如果想讀「照 ROM bootloader 協定寫的開源實作」，ST 在較新系列的 Cube 套件裡有 **OpenBootloader**（例如 [STM32CubeG0](https://github.com/STMicroelectronics/STM32CubeG0) 的 `Middlewares/ST/OpenBootloader`）。STM32CubeF1 裡沒有這個 middleware。

## 踩到的坑

- **OpenOCD 的 `echo` 字串裡寫 `[0]`**，Tcl 會把它當成指令替換，報 `invalid command name "0"`。要寫成 `\[0\]`。
- **objdump 把資料也當指令反組譯**：向量表、literal pool、GET 回應那 16 bytes 都會被翻成看起來很怪的指令。看到 `UNDEFINED` 或沒有意義的 `lsls` 時，先用 `xxd -e` 以 32-bit 看一次，通常是位址常數。
- **ROM 上只能用 `hbreak`**：一般的 `break` 要把指令改成 `bkpt`，ROM 寫不進去。Cortex-M3 有 6 個硬體中斷點，腳本裡每用完一個就 `delete`，才不會用光。
- **GDB 設 `$msp` 時印出 `Invalid state, unable to determine sp alias, assuming msp`**：沒有 ELF 時 GDB 不確定目前用 MSP 還是 PSP，無害，可以忽略。
- **手動設 PC 要清掉 bit0**，同時 `xPSR` 的 T 位元要是 1，不然第一條指令就 HardFault。
- **第一次跑到一半中斷的腳本**，下次連上時 CPU 還停在 ROM 裡。腳本開頭的 `monitor reset halt` 會處理。

## 參考資料

- [AN2606：STM32 microcontroller system memory boot mode](https://www.st.com/resource/en/application_note/an2606-introduction-to-system-memory-boot-mode-on-stm32-mcus-stmicroelectronics.pdf)（BOOT 腳位、bootloader 使用的 RAM、HSI 與 IWDG）
- [AN3155：USART protocol used in the STM32 bootloader](https://www.st.com/resource/en/application_note/an3155-usart-protocol-used-in-the-stm32-bootloader-stmicroelectronics.pdf)（`0x7F` 同步、8E1、GET 回應格式）
- [RM0008：STM32F10x Reference Manual](https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-stm32f105xx-and-stm32f107xx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)（RCC、IWDG、USART、GPIO CRH、FLASH_KEYR、bit-band、boot 映射、electronic signature）
- [STM32CubeF1](https://github.com/STMicroelectronics/STM32CubeF1/tree/c7656f1fee178058be2f8ebfc8df9eaf91dc565e)（IAP 範例）
- [Arm Compiler：scatter-loading 與 `__main`](https://developer.arm.com/documentation/dui0474/latest/)
- [devanlai/dapboot](https://github.com/devanlai/dapboot)
- [STM32 Bootloader 跳轉 App 的實作（STM32F767、Keil）](https://blog.csdn.net/hxj0323/article/details/108414536)
