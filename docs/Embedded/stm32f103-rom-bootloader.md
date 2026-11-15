# 把 STM32F103 的 ROM bootloader 讀出來：從向量表、啟動組語一路追到 C 的 main

[上一篇](./dapboot-bluepill.md)在 Blue Pill 上跑開源的 dapboot。這篇回頭看晶片**出廠就燒好**的那支 bootloader：BOOT0 拉高開機時執行的 system memory bootloader（`0x1FFF_F000`）。

它不開源，ST 只公開協定文件（[AN2606](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)、[AN3155](https://www.st.com/resource/en/application_note/an3155-usart-protocol-used-in-the-stm32-bootloader-stmicroelectronics.pdf)）。不過 ROM 沒有讀保護，接上 JTAG 就能整塊讀出來反組譯。這篇的目標是沿著一條典型的路線把它走完：

> 硬體從向量表取 SP 和 PC → 啟動組語 → 初始化 RAM → 跳進 C 的 `main` → 設時脈、周邊 → 進入命令迴圈

版本說明：

- 板子是正版 STM32F103C8T6（medium-density，`DBGMCU_IDCODE 0x20036410`），除錯器沿用 [FT232H + OpenOCD](./ft232h-jtag-stm32.md)。
- 讀出的 2KB system memory，SHA-256 開頭 `8e094a8b`。同型號不同批次的 ROM 內容可能不同，以下位址是我這顆的。
- 文中只節錄幾行反組譯來說明。**ROM 的 binary 和完整反組譯是 ST 的程式碼，不放進 repo**，要看請用下面的腳本從自己的板子讀。

腳本放在 [`static/code/stm32f103-rom-bootloader/`](https://github.com/alanhc/til/tree/main/static/code/stm32f103-rom-bootloader)。

## 先講結論

- 向量表只有 4 格：MSP `0x2000_01FC`、Reset、NMI、HardFault。**bootloader 只用 SRAM 開頭 512 bytes**，這和 AN2606 說的一致。
- 啟動流程是 ARM 編譯器（Keil/ARMCC）的標準樣式：`Reset_Handler` → `__main` → `__scatterload` → `main`。
- 「初始化 RAM」在這顆 MCU 上只是設 SP、複製 `.data`、清 `.bss`。這支 ROM 的 scatter-load 表**是空的**，連 `.data`／`.bss` 都沒有，所有狀態都放在 stack 上。
- `main` 不用外部石英：HSI/2 × 6 = **24MHz**，開 IWDG，設好 PA9／PA10，再用 **SysTick 量主機送來的 `0x7F`** 算出鮑率。
- `main` 開頭複製到 stack 上的 16 bytes 常數，正好是 AN3155 **GET 指令的回應**：bootloader 版本 2.2 和支援的指令清單。

## 先講清楚：MCU 沒有「DRAM 初始化」

看 Linux SoC 的開機流程時，常會看到 BL2 或 SPL 花很多力氣做 DDR 初始化（設控制器、PHY、training），因為外接 DRAM 不設定好根本不能用。

STM32F103 只有晶片內建的 **20KB SRAM**，上電就能讀寫，不需要任何初始化。所以 MCU 啟動碼裡的「RAM 初始化」指的是 C 語言執行環境的準備：

1. 設 stack pointer（Cortex-M 由硬體從向量表 `[0]` 載入，啟動碼常會再設一次）
2. 把有初值的全域變數（`.data`）從 flash 複製到 RAM
3. 把沒初值的全域變數（`.bss`）清成 0

做完這三件事才能跳進 C 的 `main`。下面就照這個順序看 ROM 怎麼做。

## 讀出 ROM

STM32F103 medium-density 的 system memory 在 `0x1FFF_F000`，長 2KB；後面緊接著 option bytes（`0x1FFF_F800`）。

```tcl
# dump_rom.tcl
init
reset halt
dump_image sysmem.bin   0x1FFFF000 0x800
dump_image optbytes.bin 0x1FFFF800 0x10
reset run
shutdown
```

```bash
openocd -f ft232h-jtag.cfg -f target/stm32f1x.cfg -f dump_rom.tcl
arm-none-eabi-objdump -D -b binary -marm -Mforce-thumb --adjust-vma=0x1FFFF000 sysmem.bin > sysmem.dis
```

`--adjust-vma` 讓反組譯顯示真正的位址；`-Mforce-thumb` 是因為 raw binary 沒有符號告訴 objdump 這是 Thumb 指令。

這裡不需要把 BOOT0 拉高。除錯器直接讀 `0x1FFF_F000`，跟晶片從哪裡開機無關。

## 第一站：向量表

```text
1FFFF000: 200001FC   [0] 初始 MSP
1FFFF004: 1FFFF021   [1] Reset
1FFFF008: 1FFFF765   [2] NMI
1FFFF00C: 1FFFF767   [3] HardFault
```

只有 4 格，後面馬上接程式碼。這支 ROM 完全不用中斷（等事件都用輪詢），所以不需要完整的向量表。

- **MSP = `0x2000_01FC`**：stack 從 SRAM 第 512 bytes 往下長，整支 bootloader 只動 `0x2000_0000`～`0x2000_01FF`。這就是 AN2606 說 bootloader 會用到 RAM 開頭 512 bytes 的原因，用 bootloader 燒程式時，那塊 RAM 的內容不保證。
- **NMI** 指到一條 `bx lr`，直接返回。
- **HardFault** 跳去寫 `AIRCR = 0x05FA_0004`（`VECTKEY` + `SYSRESETREQ`），出錯就整顆重開。
- 位址 bit0 都是 1（Thumb bit），所以 Reset 是 `0x1FFFF021`，實際程式在 `0x1FFFF020`。

BOOT0 = 1 開機時，system memory 會被映射到位址 `0x0000_0000`。硬體從 `0x0` 讀向量表，讀到的就是這 4 格。

## 第二站：啟動組語

```text
; Reset_Handler
1FFFF020: ldr   r0, [pc, #0]      ; r0 = 0x1FFFF011
1FFFF022: bx    r0                ; → __main

; __main
1FFFF010: ldr.w sp, [pc, #4]      ; sp = 0x200001FC
1FFFF014: bl    0x1FFFF76C        ; → __scatterload
```

`Reset_Handler` 只有兩條指令：載入一個位址然後跳過去。這跟 Keil 啟動檔 `startup_stm32f10x_md.s` 的寫法一樣：

```text
Reset_Handler   PROC
                LDR     R0, =__main
                BX      R0
```

`__main` 是 ARM 編譯器 runtime 提供的進入點。它先把 SP 再設一次（硬體其實已經從向量表載過了），然後呼叫 `__scatterload`。

GCC 的專案沒有 `__main`，通常在 `Reset_Handler` 裡直接寫迴圈複製 `.data`、清 `.bss`，再 `bl main`。[dapboot](./dapboot-bluepill.md) 用的 libopencm3 就是這樣。兩邊做的事情一樣，只是工具鏈不同。

## 第三站：`__scatterload`，也就是 RAM 初始化

```text
1FFFF76C: ldr   r4, =0x1FFFF7A8   ; 區段表起點
1FFFF76E: ldr   r5, =0x1FFFF7A8   ; 區段表終點
1FFFF770: b     check
loop:
1FFFF772: ldr   r0, [r4, #12]     ; 這一筆要呼叫的函式
1FFFF774: orr.w r3, r0, #1        ;   補上 Thumb bit
1FFFF778: ldmia r4, {r0, r1, r2}  ;   來源、目的、長度
1FFFF77C: blx   r3                ;   複製或清零
1FFFF77E: adds  r4, #16           ; 下一筆（每筆 16 bytes）
check:
1FFFF780: cmp   r4, r5
1FFFF782: bcc   loop
1FFFF784: ldr   r0, =0x1FFFF34D   ; main
1FFFF786: bl    0x1FFFF01C        ; → bx r0
```

ARM 編譯器不像 GCC 那樣在啟動碼裡寫死「複製 `.data`、清 `.bss`」兩個迴圈，而是由 linker 產生一張**區段表**。每一筆 16 bytes：來源位址、目的位址、長度，再加一個處理函式（複製、清零，或解壓縮）。`__scatterload` 只負責逐筆呼叫。

這支 ROM 的區段表**起點等於終點**，迴圈一次都不會執行。也就是說，它沒有任何需要初始化的全域變數。以 2KB 的 bootloader 來說很合理：狀態全部放在 `main` 的 stack frame 裡，連 `.bss` 都省了。

表的後面就是 `main` 的位址。`bl 0x1FFFF01C` 跳到一條 `bx r0`，從這裡進入 C。

## 第四站：C 的 `main`

`main` 從 `0x1FFFF34C` 開始。下面把它前段的暫存器寫入，對照 [RM0008](https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-stm32f105xx-and-stm32f107xx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf) 翻成白話：

| 動作 | 意義 |
|---|---|
| 從 ROM 複製 16 bytes 常數到 stack | `79 0B 22 00 01 02 11 21 31 43 63 73 82 92 79`：GET 指令的回應，見下一節 |
| 關中斷（`cpsid i`） | 全程輪詢，不用中斷 |
| `IWDG_KR = 0x5555`、`IWDG_PR = 6`、`IWDG_KR = 0xAAAA` | 解鎖獨立看門狗、預除頻設成最大的 /256、重新載入計數。如果 option bytes 設了硬體看門狗，bootloader 也不會被咬死 |
| `RCC_CFGR = 0x0010_0000` | PLLMUL = ×6，PLL 來源 = HSI/2 |
| `RCC_CR.PLLON = 1`，等 `PLLRDY` | PLLON 是透過 bit-band 別名（`0x4242_0060`）寫的，單一位元寫入不用讀－改－寫 |
| `RCC_CFGR = 0x0010_0002` | 系統時脈切到 PLL：4MHz × 6 = **24MHz** |
| `RCC_APB2ENR = 0x4004` | 開 USART1（bit14）和 GPIOA（bit2）的時脈 |
| `SCB->VTOR = 0` | 向量表在位址 0。BOOT0 = 1 時 0 就是 system memory |
| `GPIOA_CRH = 0x4444_44B4` | PA9 = `0xB`（複用推挽輸出，50MHz），當 TX；PA10 = `0x4`（浮接輸入），當 RX |
| `SysTick->CTRL = 4`、`LOAD = 0x80000` | SysTick 用核心時脈，先不啟動 |

只用內部 HSI 的好處是：不管板子上接了什麼石英，甚至沒接，bootloader 都能跑。代價是 HSI 有 ±1% 左右的誤差，所以鮑率不能寫死，要現場量。

### 自動鮑率偵測

接著是一段輪詢 `GPIOA_IDR` bit10（PA10，也就是 RX 腳）的迴圈：

```text
等 RX = 1           ; 線路閒置
等 RX = 0           ; 起始位元
等 RX = 1           ; bit0 開始
SysTick 啟動
等 RX = 0           ; bit7
elapsed = 0x80000 - SysTick->VAL
USART1_BRR = elapsed / 7
```

AN3155 規定主機要先送一個 `0x7F`。UART 先送 LSB，所以線上的波形是：

```text
閒置  起始  b0 b1 b2 b3 b4 b5 b6  b7  停止
 1     0    1  1  1  1  1  1  1   0    1
            └──── 7 個位元時間 ───┘
```

從 bit0 上升開始計時，到 bit7 下降停止，剛好是 **7 個位元時間**。SysTick 和 USART1 都吃同一個 24MHz 時脈，所以「每個位元有幾個 tick」直接就是 `USART_BRR` 該填的值，除以 7 就好，不必知道實際的時脈是多少。HSI 的誤差也在這一步被抵消了。

然後設定 USART1：

- `CR1 = 0x340C`：`UE`、`M`（9 bit 字長）、`PCE`（parity 開啟，`PS = 0` 是 even）、`TE`、`RE`。9 bit 裡有 1 bit 是 parity，所以實際是 **8 data + even parity**，正是 AN3155 規定的格式。
- 送出 `0x79`（ACK），告訴主機鮑率已經對上了。

### 命令迴圈

最後進入命令迴圈：

1. 重新載入 IWDG（`KR = 0xAAAA`）
2. 收兩個 byte：指令碼和它的補數
3. 兩個 byte 的 XOR 不是 `0xFF` 就當成無效指令
4. 依指令碼分派到各個處理函式

AN3155 的每個指令都是「指令碼 + 補數」，就是在這裡檢查的。

### GET 回應藏在 `main` 的開頭

`main` 一進來就從 ROM 複製 16 bytes 到 stack，內容是：

```text
79  0B  22  00 01 02 11 21 31 43 63 73 82 92  79
ACK N   版本 └────────── 支援的指令 ──────────┘ ACK
```

- `0x0B`：後面還有 11+1 bytes
- `0x22`：bootloader 版本 2.2
- 指令清單：Get、Get Version、Get ID、Read Memory、Go、Write Memory、Erase、Write Protect、Write Unprotect、Readout Protect、Readout Unprotect

和 AN3155 的表格逐一對得上。這就是這顆晶片收到 GET（`0x00`）時會原封不動送回去的那串 bytes。

### ROM 尾端的兩個常數

system memory 的最後一段不是程式：

- `0x1FFF_F7E0`：Flash 大小，讀到 `0x0040` = 64KB
- `0x1FFF_F7E8`：96-bit 的晶片 UID

這兩個在 RM0008 裡叫 device electronic signature，是工廠寫入的，和 bootloader 放在同一塊唯讀區。

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

如果想讀「照 ROM bootloader 協定寫的開源實作」，ST 在較新系列的 Cube 套件裡有 **OpenBootloader**（例如 [STM32CubeG0](https://github.com/STMicroelectronics/STM32CubeG0) 的 `Middlewares/ST/OpenBootloader`）。STM32CubeF1 裡沒有這個 middleware。

## 踩到的坑

- **OpenOCD 的 `echo` 字串裡寫 `[0]`**，Tcl 會把它當成指令替換，報 `invalid command name "0"`。要寫成 `\[0\]`。
- **objdump 把資料也當指令反組譯**：向量表、literal pool、GET 回應那 16 bytes 都會被翻成看起來很怪的指令。看到 `UNDEFINED` 或沒有意義的 `lsls` 時，先用 `xxd -e` 以 32-bit 看一次，通常是位址常數。
- **找不到 `main`**：沒有符號表，要從 `__scatterload` 最後載入的那個位址往回推，那就是 `main`。

## 參考資料

- [AN2606：STM32 microcontroller system memory boot mode](https://www.st.com/resource/en/application_note/an2606-stm32-microcontroller-system-memory-boot-mode-stmicroelectronics.pdf)（BOOT 腳位、bootloader 使用的 RAM、HSI 與 IWDG）
- [AN3155：USART protocol used in the STM32 bootloader](https://www.st.com/resource/en/application_note/an3155-usart-protocol-used-in-the-stm32-bootloader-stmicroelectronics.pdf)（`0x7F` 同步、8E1、GET 回應格式）
- [RM0008：STM32F10x Reference Manual](https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-stm32f105xx-and-stm32f107xx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)（RCC、IWDG、USART、GPIO CRH、boot 映射、electronic signature）
- [STM32CubeF1](https://github.com/STMicroelectronics/STM32CubeF1/tree/c7656f1fee178058be2f8ebfc8df9eaf91dc565e)（IAP 範例）
- [Arm Compiler：scatter-loading 與 `__main`](https://developer.arm.com/documentation/dui0474/latest/)
- [devanlai/dapboot](https://github.com/devanlai/dapboot)
