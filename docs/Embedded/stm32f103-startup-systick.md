# 自己寫 STM32F103 的 startup 和 SysTick 中斷：用 GDB 看 CPU 從向量表走到 main、再被中斷打斷

[上一篇](./stm32f103-rom-bootloader.md)把 ST 的 ROM bootloader 讀出來反組譯，一路追「向量表 → 啟動組語 → RAM 初始化 → `main`」。讀別人的程式碼很容易看過就忘，所以這篇反過來：**自己寫一支最小的程式，把同一條路走一遍**，每一步都用 GDB 停下來，看 RAM 和暫存器實際變成什麼。

分兩課：

1. **startup**：不用 HAL、CMSIS、libc，自己寫向量表、`Reset_Handler`、linker script，讓 LED 閃。看 `.data` 怎麼從 flash 搬到 RAM、`.bss` 怎麼清成 0，再趁程式在跑的時候直接改 RAM 裡的變數。
2. **SysTick 中斷**：LED 改由中斷翻轉。看中斷進來的瞬間硬體 push 了什麼、`LR` 為什麼是 `0xFFFFFFF9`，再故意把 VTOR 寫錯，看中斷會跑去哪裡。

做的過程中挖到一個原本沒料到的坑：**app 開始跑時，時脈不是 reset 預設的 8MHz**，因為 bootloader 已經改過了。

版本說明：

- 板子、除錯器同前幾篇：STM32F103C8T6 Blue Pill、[FT232H + OpenOCD](./ft232h-jtag-stm32.md)（xPack OpenOCD 0.12.0、Arm GNU Toolchain 14.3 的 GCC／GDB）。
- flash 前 8KB 是 [dapboot](./dapboot-bluepill.md)，所以兩課的程式都放在 **`0x0800_2000`**，開機流程是「dapboot → 我們的 app」。
- 以 `-O0` 編譯，方便對照原始碼行號。

程式和腳本放在 [`static/code/stm32f103-startup-systick/`](https://github.com/alanhc/til/tree/main/static/code/stm32f103-startup-systick)：

| 檔案 | 用途 |
|---|---|
| `startup-lab.c` | 第一課：最小 startup + 閃燈，約 60 行 |
| `systick-lab.c` | 第二課：SysTick 中斷版，可用 `-D` 編出兩個 VTOR 寫錯的版本 |
| `link.ld` | 兩課共用的 linker script |
| `build.sh` | 編出 `lab.elf`、`tick.elf`、`tick-novtor.elf`、`tick-badvtor.elf` |
| `startup-lab.gdb` | 第一課：燒錄後停在 startup 每個階段看 RAM |
| `systick-lab.gdb` | 第二課：看中斷進入、量 tick 數 |
| `variant.gdb` | 第二課：讓任一版本跑 1 秒，看 VTOR 和 CPU 停在哪 |

## 先講結論

- **startup 就是兩個迴圈加一個呼叫**：從 flash 複製 `.data` 到 RAM、把 `.bss` 填 0、呼叫 `main()`。在這之前，C 語言對全域變數的保證（有初值、沒初值就是 0）都還不成立。GDB 在 `Reset_Handler` 開頭讀到的是上一支程式留在 RAM 的亂碼。
- **變數就是 RAM 的一個位址**。`speed` 這個名字只存在 ELF 的符號表裡；用 `set var speed = ...` 和 `set {unsigned int}0x20000000 = ...` 效果一模一樣，改完 LED 當場變速。
- **中斷進來時，硬體自動 push 8 個暫存器**（`r0-r3`、`r12`、`lr`、`pc`、`xPSR`），再把 `LR` 設成 `0xFFFFFFF9` 這個暗號。handler 結束時 `bx lr` 碰到這個值就自動 pop 回去，所以 handler 能寫成普通 C 函式。從 SysTick 歸零到 handler 第一條指令約 13 個 cycle。
- **bootloader 會留下狀態**。dapboot 為了 USB 把時脈切到 72MHz（`RCC_CFGR = 0x001DC40A`），跳到 app 後不會改回來。照「reset 後 8MHz」算 SysTick，計時快了 9 倍。
- **VTOR 寫錯不會當機，只會「沒反應」**。寫成 `0x0800_0000` 時，SysTick 每 1ms 照樣發生，但查的是 dapboot 的向量表，跳進一個只有 `bx lr` 的空函式就返回了。LED 不閃，`main` 照跑，沒有任何錯誤。

---

# 第一課：最小的 startup

## 步驟 1：程式本體

整個程式分成五塊，從下往上讀比較符合 CPU 實際執行的順序：

```c
/* ---------- 1. registers we touch (addresses from RM0008) ---------- */
#define RCC_APB2ENR (*(volatile uint32_t *)0x40021018)
#define GPIOC_CRH   (*(volatile uint32_t *)0x40011004)
#define GPIOC_ODR   (*(volatile uint32_t *)0x4001100C)
#define SCB_VTOR    (*(volatile uint32_t *)0xE000ED08)

/* ---------- 2. two globals, one per RAM section ---------- */
uint32_t speed = 200000;        /* has a value  -> .data (copied from flash) */
uint32_t blink_count;           /* no value     -> .bss  (must be zeroed)    */

/* ---------- 3. the program ---------- */
int main(void)
{
    RCC_APB2ENR |= (1u << 4);           /* turn on GPIOC's clock          */
    GPIOC_CRH = (GPIOC_CRH & ~(0xFu << 20)) | (0x2u << 20); /* PC13 = output */

    for (;;) {
        GPIOC_ODR ^= (1u << 13);        /* flip the LED                   */
        blink_count++;
        for (volatile uint32_t i = 0; i < speed; i++) {
        }
    }
}

/* ---------- 4. the startup: what runs BEFORE main ---------- */
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _estack;  /* from the .ld */

void Reset_Handler(void)
{
    SCB_VTOR = 0x08002000;              /* our vector table, not dapboot's */

    uint32_t *src = &_sidata;           /* .data: copy initial values      */
    uint32_t *dst = &_sdata;            /*        from flash into RAM      */
    while (dst < &_edata)
        *dst++ = *src++;

    for (dst = &_sbss; dst < &_ebss; )  /* .bss: fill with zero            */
        *dst++ = 0;

    main();
    for (;;) {
    }
}

/* ---------- 5. the vector table: the first thing the CPU reads ---------- */
__attribute__((section(".isr_vector"), used))
void (*const vectors[])(void) = {
    (void (*)(void))&_estack,   /* [0] initial SP  */
    Reset_Handler,              /* [1] reset       */
    Default_Handler,            /* [2] NMI         */
    Default_Handler,            /* [3] HardFault   */
};
```

（`Default_Handler` 是一個空的無窮迴圈，完整檔案見 `startup-lab.c`。）

幾個刻意的安排：

- **兩個全域變數各放一區**：`speed` 有初值，會進 `.data`；`blink_count` 沒有，會進 `.bss`。這樣兩個迴圈各自都有東西可以看。
- **暫存器直接用位址**：每個 `#define` 都能在 RM0008 查到。GPIOC 的 `CRH` 每 4 bit 管一支腳，PC13 是 bit 23:20，`0x2` 代表「推挽輸出，2MHz」。
- **`volatile`**：延遲迴圈的 `i` 和暫存器都要加，不然編譯器會認為「寫了沒人讀」而把它們最佳化掉。

## 步驟 2：linker script 決定東西放哪

```ld
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08002000, LENGTH = 56K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 20K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);    /* stack starts at the top of RAM */
ENTRY(Reset_Handler)

SECTIONS
{
    .isr_vector : { KEEP(*(.isr_vector)) } > FLASH   /* must be first */
    .text       : { *(.text*) *(.rodata*) } > FLASH

    _sidata = LOADADDR(.data);                      /* where .data sits in flash */
    .data : { _sdata = .; *(.data*) _edata = .; } > RAM AT > FLASH
    .bss  : { _sbss = .; *(.bss*) *(COMMON) _ebss = .; } > RAM
}
```

重點是 `.data` 那一行的 `> RAM AT > FLASH`：**執行時的位址在 RAM，但內容存在 FLASH**。`_sidata` 記的是 flash 上那份內容的位址，`_sdata`／`_edata` 是 RAM 上的範圍。`Reset_Handler` 裡用的這幾個符號全部來自這裡，C 程式只是用 `extern` 借來當位址。

## 步驟 3：編譯，看產物

```bash
arm-none-eabi-gcc -mcpu=cortex-m3 -mthumb -O0 -g -ffreestanding -nostdlib -Wall \
    -T link.ld -Wl,-Map=lab.map -o lab.elf startup-lab.c
arm-none-eabi-size -A lab.elf
```

```text
.isr_vector         16   134225920      ← 0x08002000
.text              216   134225936      ← 0x08002010
.data                4   536870912      ← 0x20000000
.bss                 4   536870916      ← 0x20000004
```

`-nostdlib` 表示不連結 libc，也不用它的 startup（`crt0`），所有開機前要做的事都在我們自己的 `Reset_Handler` 裡。`-ffreestanding` 告訴編譯器沒有標準函式庫可用。

向量表的 16 bytes：

```bash
arm-none-eabi-objdump -s -j .isr_vector lab.elf
```

```text
 8002000 00500020 75200008 e1200008 e1200008  .P. u ... ... ..
```

little-endian 倒過來讀：

| 格 | 值 | 意思 |
|---|---|---|
| `[0]` | `0x2000_5000` | 初始 SP，RAM 頂端（`_estack`） |
| `[1]` | `0x0800_2075` | `Reset_Handler`（`0x0800_2074`）+ 1，bit0 是 Thumb bit |
| `[2]`、`[3]` | `0x0800_20E1` | `Default_Handler` + 1 |

各符號的位址：

```bash
arm-none-eabi-nm -n lab.elf
```

```text
08002010 T main
08002074 T Reset_Handler
080020e8 A _sidata           ← speed 的初值存在 flash 這裡
20000000 D _sdata
20000000 D speed
20000004 D _edata
20000004 B _sbss
20000004 B blink_count
20000008 B _ebss
20005000 R _estack
```

flash 上那份初值：

```bash
arm-none-eabi-objdump -s -j .data lab.elf
```

```text
 20000000 400d0300                             @...
```

`0x0003_0D40` = 200000。objdump 標的是 RAM 位址 `0x2000_0000`，但這 4 bytes 實際燒在 flash 的 `0x0800_20E8`。

## 步驟 4：ELF 裡到底有什麼

`lab.elf` 有 11156 bytes，但真正燒進晶片的只有一小部分：

```bash
arm-none-eabi-objcopy -O binary lab.elf lab.bin   # 236 bytes
xxd -l 4 lab.elf                                  # 7f45 4c46 = "\x7fELF"
arm-none-eabi-readelf -S lab.elf
```

| 區段 | 內容 | 進晶片嗎 |
|---|---|---|
| `.isr_vector`、`.text` | 向量表、機器碼 | ✓ |
| `.data` | `speed` 的初值 | ✓ 燒進 flash，開機時複製到 RAM |
| `.bss` | 只記「要留 4 bytes」，類型是 `NOBITS`，檔案裡沒有內容 | ✗ |
| `.symtab`、`.strtab` | 符號表：`speed` 在 `0x2000_0000`、`main` 在 `0x0800_2010` | ✗ 給 GDB 用 |
| `.debug_*` | 原始碼行號、型別 | ✗ 給 GDB 用 |

晶片完全不知道 `speed` 這個名字。GDB 能 `print speed`，是因為它查 `.symtab` 得到位址，查 `.debug_info` 得到型別，再透過 JTAG 去讀那個位址。這也是為什麼：

- GDB 的 `load` 和 OpenOCD 吃 `.elf`：位址寫在檔案裡。
- `dfu-util`、ROM bootloader 吃 `.bin`：純 bytes，位址要另外指定（[dapboot 那篇](./dapboot-bluepill.md)用 `dfu-util` 燒的就是 `.bin`）。

## 步驟 5：燒錄，停在 startup 每個階段看 RAM

先開 OpenOCD：

```bash
openocd -f ft232h-jtag.cfg -f target/stm32f1x.cfg
```

再跑 GDB 腳本：

```bash
arm-none-eabi-gdb -q -batch -x startup-lab.gdb
```

腳本先把 `0x0800_2000` 原本的 app 備份成 `app-backup.bin`，再 `load` 燒錄，然後 `monitor reset halt`。之後從真正的 reset 開始跑：dapboot 先執行，檢查我們的向量表 `[0]` 落在 RAM，再跳過來。

### A. 剛進 `Reset_Handler`

```gdb
hbreak Reset_Handler
continue
```

```text
34	    SCB_VTOR = 0x08002000;
pc=0x0800207a sp=0x20004ff0 (from our vector [0])
speed=134224405 blink_count=134224416   <- RAM leftovers, nothing copied yet
```

- `speed` 和 `blink_count` 都是亂碼（`0x0800_xxxx` 開頭，看起來是 dapboot 留在 RAM 的指標）。**這時 C 語言說的「`speed` 初值是 200000」還不成立**。
- SP 是 `0x2000_4FF0`，不是向量表的 `0x2000_5000`。差的 16 bytes 是 `-O0` 編出的函式開頭（prologue）先 push 了暫存器，GDB 的 `hbreak 函式名` 會停在 prologue 之後。

### B. `.data` 複製完

```gdb
hbreak startup-lab.c:41      # .bss 迴圈開頭
continue
```

```text
speed=200000   <- copied from flash 0x080020e8
blink_count=134224416   <- not zeroed yet
```

`speed` 有值了，是從 flash `0x0800_20E8` 搬過來的。`blink_count` 還是亂碼。

### C. 到 `main`

```text
speed=200000 blink_count=0
```

`.bss` 清完了。C 標準保證「沒初值的全域變數是 0」，是靠這個迴圈兌現的，硬體不會自動清。

### D. `main` 在跑

在 `blink_count++` 那行停三次：

```text
blink_count=0 PC13 ODR bit=0
blink_count=1 PC13 ODR bit=1
blink_count=2 PC13 ODR bit=0
```

每圈 PC13 翻轉一次。腳本最後 `monitor reset run`，LED 開始閃。

對照上一篇：ROM bootloader 的 `__scatterload` 做的就是 B 和 C，只是 Keil 寫成查表的形式。

## 步驟 6：程式在跑的時候改變數

OpenOCD 開著，手動進 GDB：

```bash
arm-none-eabi-gdb -q lab.elf
```

```text
(gdb) target extended-remote localhost:3333
0x0800205a in main () at startup-lab.c:24
24	        for (volatile uint32_t i = 0; i < speed; i++) {
```

**GDB 一連上 CPU 就停了**（OpenOCD 在 GDB 連線時會 halt），LED 停在亮或暗。連續 `print blink_count` 幾次，數字都不變：CPU 停住時 RAM 也凍結。

```text
(gdb) print &speed
$1 = (uint32_t *) 0x20000000 <speed>
(gdb) x/1xw 0x20000000
0x20000000 <speed>:     0x00030d40
```

變數就是 RAM 第一格。接著改它：

| 指令 | 板子上 |
|---|---|
| `set var speed = 1000000` → `continue` | LED 變很慢 |
| `Ctrl+C` | 停住 |
| `set {unsigned int}0x20000000 = 50000` → `continue` | 變快。不用變數名稱，直接寫位址也一樣 |
| `Ctrl+C` → `monitor resume` → `quit` | 離開，LED 照目前速度繼續閃 |

最後按板子的 reset 鍵：速度回到 200000。`Reset_Handler` 又從 flash 複製了一次初值，蓋掉剛剛手動改的值。

---

# 第二課：SysTick 中斷

## 步驟 7：讓中斷來翻 LED

改動三處（完整檔案見 `systick-lab.c`）：

```c
#define SYST_CSR    (*(volatile uint32_t *)0xE000E010)   /* SysTick control   */
#define SYST_RVR    (*(volatile uint32_t *)0xE000E014)   /* SysTick reload    */
#define SYST_CVR    (*(volatile uint32_t *)0xE000E018)   /* SysTick current   */

uint32_t half_period_ms = 500;  /* .data: LED toggles every 500 ms          */
volatile uint32_t ms;           /* .bss : counted up by the interrupt       */

/* Runs by itself every 1 ms. Nobody calls it: the CPU jumps here. */
void SysTick_Handler(void)
{
    ms++;
    if (ms % half_period_ms == 0)
        GPIOC_ODR ^= (1u << 13);
}

int main(void)
{
    /* ...GPIO setup as before... */
    SYST_RVR = 72000 - 1;       /* 72 MHz: 72000 ticks = 1 ms (see step 9) */
    SYST_CVR = 0;
    SYST_CSR = 0x7;             /* bit2 CPU clock, bit1 interrupt, bit0 on  */

    for (;;)
        __asm volatile ("wfi"); /* sleep until the next interrupt           */
}
```

- **`SysTick_Handler` 沒有任何人呼叫**。CPU 在 SysTick 數到 0 時自己跳過去。
- `ms` 加了 `volatile`：它在中斷裡被改，`main` 的角度看不到誰在改它。
- `main` 設好之後就 `wfi`（wait for interrupt）睡覺，有中斷才醒。

向量表要擴充到 16 格，因為 Cortex-M 規定前 16 格的用途，SysTick 是第 15 格（offset `0x3C`）：

```c
__attribute__((section(".isr_vector"), used))
void (*const vectors[16])(void) = {
    [0]  = (void (*)(void))&_estack,
    [1]  = Reset_Handler,
    [2]  = Default_Handler,     /* NMI        */
    [3]  = Default_Handler,     /* HardFault  */
    [4]  = Default_Handler,     /* MemManage  */
    [5]  = Default_Handler,     /* BusFault   */
    [6]  = Default_Handler,     /* UsageFault */
                                /* 7-10 reserved, left 0 */
    [11] = Default_Handler,     /* SVCall     */
    [12] = Default_Handler,     /* DebugMon   */
                                /* 13 reserved */
    [14] = Default_Handler,     /* PendSV     */
    [15] = SysTick_Handler,     /* SysTick    */
};
```

編出來：

```text
 8002000 00500020 d1200008 3d210008 3d210008
 8002010 3d210008 3d210008 3d210008 00000000
 8002020 00000000 00000000 00000000 3d210008
 8002030 3d210008 00000000 3d210008 41200008   ← [15] = 0x08002041
```

`SysTick_Handler` 剛好排在向量表後面，位址 `0x0800_2040`。

## 步驟 8：看中斷進來的瞬間

```bash
arm-none-eabi-gdb -q -batch -x systick-lab.gdb
```

### A. VTOR 和第 15 格

```text
VTOR=0x08002000 (set by Reset_Handler)
vector[15] at VTOR+0x3C = 0x08002041, SysTick_Handler = 0x08002040
```

CPU 收到 SysTick 時做的事就是：讀 `VTOR + 15 × 4`，拿到位址，跳過去。

### B. 停在 handler 的第一條指令

這次用 `hbreak *SysTick_Handler`（加 `*` 表示停在函式的**第一個位址**，不跳過 prologue），這時 SP 指的正好是硬體 push 的那 8 個字：

```text
IPSR=15 (15 = SysTick)  lr=0xfffffff9  sp=0x20004fc8
hardware pushed 8 words onto the stack:
  r0=0x00000001 r1=0x20000004 r2=0x00000007 r3=0xe000e010
  r12=0x0000000f lr=0x0800211f pc=0x080020b8 xpsr=0x21000200
main + 52 in section .text
```

- **`IPSR = 15`**：xPSR 的低 9 bit 記錄目前在處理幾號例外。
- **stack 上的 `pc = main + 52`**：被打斷的位置，也就是 `wfi` 那一行。中斷結束後從這裡繼續。
- **stack 上的 `xpsr` bit9 = 1**：硬體為了讓 stack 對齊 8 bytes 多墊了 4 bytes，返回時要拿掉。
- **`lr = 0xFFFF_FFF9`** 不是真的位址，叫 **EXC_RETURN**。`0xF9` 表示「返回 Thread mode、用 MSP」。handler 結尾編譯器產生的是普通的 `bx lr` 或 `pop {..., pc}`，CPU 看到 PC 被設成 `0xFFFF_FFxx`，就知道這是例外返回，自動把那 8 個字 pop 回暫存器。

這套機制讓 handler 能寫成普通 C 函式，不需要特別的組語進出口。

### C. 再停三次

```text
ms=1  SysTick CVR=71986
ms=2  SysTick CVR=71986
ms=3  SysTick CVR=71986
```

SysTick 從 71999 倒數，歸零時觸發中斷並重新載入。停在 handler 第一條指令時已經數到 71986，差了 13 個 cycle：Cortex-M3 的中斷延遲是 12 個 cycle，大部分花在 push 那 8 個字上。三次都是 71986，表示這個延遲是固定的。

### D. 跑 2 秒數 tick

```text
ms went from 3 to 2010: 2007 ticks in ~2000 ms
```

`monitor sleep 2000` 的時間不精確，加上 JTAG 通訊的時間，多出幾 ms 合理。

## 步驟 9：一開始快了 9 倍

第一版我照「reset 後跑 HSI 8MHz」寫 `SYST_RVR = 8000 - 1`，結果 2 秒數到 **18050**，LED 閃得像在抖。讀時脈暫存器：

```text
在 app 裡：RCC_CR = 0x03035583  RCC_CFGR = 0x001DC40A
剛 reset： RCC_CR = 0x00005583  RCC_CFGR = 0x00000000
```

拆 `RCC_CFGR = 0x001D_C40A`（RM0008 的 RCC 章節）：

| bit | 值 | 意思 |
|---|---|---|
| 3:2 SWS | `10` | 系統時脈 = PLL |
| 16 PLLSRC | `1` | PLL 輸入 = HSE（板上 8MHz 石英） |
| 21:18 PLLMUL | `0111` | ×9 |

8MHz × 9 = **72MHz**。`RCC_CR` 的 bit16/17（HSEON／HSERDY）和 bit24/25（PLLON／PLLRDY）也都是 1。dapboot 跑 USB 需要 48MHz 的 USB 時脈，所以先把系統切到 72MHz，跳到 app 時沒有改回來。18050 ÷ 9 ≈ 2000，剛好對上。

改成 `72000 - 1` 之後就正確了。**app 開始執行時，CPU 不是剛 reset 的乾淨狀態**：時脈、VTOR、有開的周邊，都是 bootloader 用過之後留下的樣子。正式的專案會在 startup 裡自己把時脈設一遍（CMSIS 的 `SystemInit()` 就是做這件事），不依賴前面的人。

## 步驟 10：VTOR 寫錯會怎樣

`systick-lab.c` 的 VTOR 那行可以用編譯參數換掉：

```c
#ifndef VTOR_VALUE
#define VTOR_VALUE 0x08002000
#endif
#ifndef NO_VTOR
    SCB_VTOR = VTOR_VALUE;
#endif
```

`build.sh` 會編出三個版本，各自燒進去，用 `variant.gdb` 讓它從 reset 跑 1 秒再停下來看：

```bash
arm-none-eabi-gdb -q -batch -ex "file tick-badvtor.elf" -x variant.gdb
```

| 版本 | VTOR | 1 秒後 `ms` | LED |
|---|---|---|---|
| `tick.elf` | `0x0800_2000` | 約 1000 | 正常 |
| `tick-novtor.elf`（不寫） | `0x0000_2000` | 968 | **正常** |
| `tick-badvtor.elf`（寫成 `0x0800_0000`） | `0x0800_0000` | **0** | **不閃** |

**不寫也能跑**：dapboot 跳過來之前已經把 VTOR 設成 `0x2000`（`APP_BASE_ADDRESS & 0xFFFF`）。STM32F1 從 flash 開機時 flash 會映射到位址 0，所以 `0x2000` 跟 `0x0800_2000` 是同一塊。但這是靠 bootloader 剛好幫忙，換一支 bootloader 就不一定了。

**寫錯的版本**輸出：

```text
VTOR=0x08000000  vector[15] there=0x08000695  IPSR=0
pc=0x080020b8  ms=0
main + 52 in section .text
```

CPU 還在 `main` 的 `wfi` 迴圈裡，沒有當機，但 `ms` 一直是 0。看 dapboot 向量表第 15 格指到哪：

```text
(gdb) x/2i 0x08000694
   0x8000694:	bx	lr
   0x8000696:	b.n	0x8000696
```

一個只有 `bx lr` 的空函式。dapboot 是用 libopencm3 寫的，沒用到的中斷都指到這種預設的空 handler（下一個位址 `b .` 是另一種會卡住的預設 handler）。所以 SysTick 每 1ms 照常觸發，CPU 照常跳進去、照常返回，**只是從來沒進到我們的 `SysTick_Handler`**。

這就是 [dapboot 那篇](./dapboot-bluepill.md)提到「app 的 VTOR 寫死成 `0x0800_0000` 會跳回 bootloader 的向量表」的實際樣子。不會 HardFault、不會重開，只是「沒反應」，是最難 debug 的那一類錯誤。查這種問題的第一步：讀 `VTOR`，再看 `VTOR + 4 × 例外編號` 那格指到哪。

---

## 踩到的坑

- **OpenOCD 同時只接受一個 GDB 連線**。手動開的 GDB 沒 `quit`，腳本再連就會出現 `Remote communication error`，OpenOCD log 裡是 `rejected 'gdb' connection, no more connections allowed`。
- **GDB `detach` 之後 CPU 不會自動繼續跑**。要先 `monitor resume`（或 `monitor reset run`）再 `detach`／`quit`，不然 LED 停在原狀，看起來像程式壞了。我第一次就是因為這樣，讀到的 `blink_count` 一直停在同一個數字。
- **`monitor halt` 之後 `$pc` 可能是舊的**。`monitor` 指令繞過 GDB 直接叫 OpenOCD 停下 CPU，GDB 不知道狀態變了，暫存器還是快取的舊值（我讀到的是 `load` 時設的進入點）。要先 `maintenance flush register-cache`。記憶體不受影響，所以 `ms` 是對的、`pc` 是錯的。
- **`hbreak 函式名` 停在 prologue 之後**，SP 已經被 push 改過；要看函式進入那一刻的 stack（例如中斷的 8 個字），用 `hbreak *函式名`。
- **bootloader 會改時脈**。在 bootloader 後面跑的 app，不要假設時脈是 reset 預設值；不確定就讀 `RCC_CFGR`。
- **燒錄會蓋掉 `0x0800_2000` 原本的 app**。`startup-lab.gdb` 會先 `dump binary memory` 備份。
- Windows 上的 GDB 偶爾印 `could not convert ... from the host encoding (CP1252)`，是型別名稱顯示時的編碼警告，不影響結果。

## 參考資料

- [RM0008：STM32F10x Reference Manual](https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-stm32f105xx-and-stm32f107xx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)（RCC_CFGR／RCC_CR、GPIO CRH、boot 映射）
- PM0056：STM32F10xxx/20xxx/21xxx/L1xxxx Cortex-M3 programming manual（向量表、例外進入與返回、EXC_RETURN、SysTick、VTOR；在 ST 官網搜尋文件編號）
- [Arm Cortex-M3 Technical Reference Manual](https://developer.arm.com/documentation/ddi0337/latest/)（中斷延遲 12 cycle）
- [dapboot](https://github.com/devanlai/dapboot)（app 位址 `0x0800_2000`、跳轉前設 VTOR）
- [libopencm3](https://github.com/libopencm3/libopencm3)（dapboot 用的函式庫，預設的空中斷 handler）
