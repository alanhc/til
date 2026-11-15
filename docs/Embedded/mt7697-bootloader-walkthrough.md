# LinkIt 7697 的 bootloader 原始碼導讀：向量表、自我搬移與 jump_to

LinkIt 7697 是 MediaTek 的 Wi-Fi + BLE 開發板，晶片是 MT7697（Cortex-M4F）。MediaTek 在 GitHub 上公開了 Arduino 用的 SDK（[`MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK)），裡面有**完整的第二階段 bootloader 原始碼**。整份不到 700 行，很適合拿來學 Cortex-M bootloader 的三個核心動作：

1. 上電後 CPU 怎麼找到第一條指令（向量表）
2. 程式怎麼把自己從 flash 搬到 RAM 再繼續執行（self-relocation）
3. 怎麼把控制權交給 application（`jump_to`）

這篇照原始碼一段一段讀，並且拿 Arduino 板子套件裡**實際燒進板子的 `mt7697_bootloader.bin`** 反組譯對照，確認讀到的跟晶片上跑的一致。

版本說明：

- 原始碼讀的是 [`53acd43`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/tree/53acd43fbee57b034141068969fa643465dfd743)（2018-08，repo 最後一個 commit）。下文連結都指向這個 commit；引用的片段有刪減，`...` 表示省略。
- 對照的 binary 是 Arduino Board Manager 裝的 LinkIt 套件 `flash_tool 1.4.4` 裡的 `mt7697_bootloader.bin`（27,232 bytes），用 Arduino 附的 `arm-none-eabi-objdump`（gcc 4.8.3-2014q1）反組譯。
- 原始碼檔頭是 MediaTek 的專有授權，不是開源授權。這篇只引用理解流程所需的短片段，完整內容請看原 repo。

## 先講結論

- MT7697 有 **352KB SRAM**，但程式本身放在**外接 4MB SPI flash**，靠 XIP（execute in place）直接執行。bootloader 佔 flash 最前面的 32KB。
- bootloader 的 linker script 讓它「**存在 flash、連結在 RAM**」：上電時先在 flash 上跑一小段 `ResetISR`，把自己複製到 SYSRAM `0x2000_0000`，再長跳過去跑 `main()`。
- 向量表的 Reset 欄位**不能**直接寫 `ResetISR`，因為那個符號是 RAM 位址，上電當下 RAM 是空的。所以手動算出它在 flash 裡的位址：`0x10000000 + 0x80 + 1`。
- `jump_to` 只有三條指令：屏障、設 MSP、`bx`。而且它**不去讀 app 的向量表**，直接跳到 app 的第一個位元組 `0x10079001`。所以 app 的 linker script 必須把 `Reset_Handler` 放在最前面。
- 燒錄工具送進板子的 download agent（`da97.bin`），其實是**同一份 bootloader 打開選單、改連結在 RAM** 的版本。`ResetISR` 裡「我是不是已經在 RAM 裡了」的判斷，就是為它準備的。

## 硬體：MT7697 有哪些記憶體

| 項目 | 規格 |
|---|---|
| CPU | Arm Cortex-M4F（含 FPU），最高 192MHz |
| SRAM | 352KB |
| Boot ROM | 64KB（MediaTek 燒死，沒有原始碼） |
| Flash | 晶片內沒有。外接 serial flash，QPI 模式 + XIP；LinkIt 7697 板上是 4MB |
| Cache | 32KB，只快取 XIP flash |
| 無線 | 802.11 b/g/n 2.4GHz 1T1R、BLE 4.2 |
| 其他 CPU | Wi-Fi 子系統有自己的 32-bit RISC CPU（SDK 裡叫 N9），藍牙也有一顆 |
| 安全 | AES、DES/3DES、SHA2 硬體引擎；支援 secure boot from serial flash |
| 封裝 | 40nm，8×8mm QFN-68 |

來源是 [MediaTek 的 MT7697 頁面](https://labs-mediatek-com.pages.dev/en/chipset/MT7697)。官方只給 352KB 這個總數，沒有拆開。從 SDK 的 linker script 看得到兩塊：

| 區域 | 位址 | 大小 | 特性 |
|---|---|---|---|
| Boot ROM | `0x0000_0000` | linker script 只標 20KB 給 `ROM_CODE` | 唯讀 |
| TCM | `0x0010_0000` | 64KB | 零等待、CM4 專用、**DMA 存取不到** |
| SPI flash（XIP） | `0x1000_0000` | 4MB | 經過 cache 讀取 |
| SYSRAM | `0x2000_0000` | 256KB | 主要 RAM，bootloader 和 app 的 stack 都在這裡 |

SYSRAM 256KB + TCM 64KB + cache 32KB 剛好等於 352KB，但這是我自己湊出來的，沒有在官方文件上看到這種拆法。

## Flash 分區

[`flash_map.h`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/project/linkit7697_hdk/apps/bootloader/inc/flash_map.h) 把 4MB flash 切成六塊：

| 分區 | flash offset | XIP 位址 | 大小 | 內容 |
|---|---|---|---|---|
| Loader | `0x000000` | `0x1000_0000` | 32KB | 這篇的主角 |
| Reserved | `0x008000` | `0x1000_8000` | 32KB | |
| N9 RAM code | `0x010000` | `0x1001_0000` | 420KB | Wi-Fi 子處理器的韌體 |
| CM4 code | `0x079000` | `0x1007_9000` | 1972KB | Arduino sketch 編出來的程式 |
| FOTA | `0x266000` | `0x1026_6000` | 1576KB | OTA 更新的暫存區 |
| NVDM | `0x3F0000` | `0x103F_0000` | 64KB | 參數儲存 |

`CM4_CODE_BASE` = 32K + 32K + 420K = `0x79000`。這個數字後面 `jump_to` 會用到。

## 全圖：四個步驟

![MT7697 bootloader 開機流程：左欄 SPI flash 分區、右欄 SYSRAM。① Boot ROM 讀 flash 開頭向量表，MSP=0x20008E48、PC=0x10000081；② ResetISR 在 flash 上把 .text 與 .data 複製到 SYSRAM 0x20000000；③ main 在 SYSRAM 設 VTOR、打開 fault、檢查 FOTA；④ jump_to 設 MSP=0x20040000 並 bx 到 0x10079001，也就是 app 的 Reset_Handler](../assets/mt7697/boot-flow-zh-light.svg#gh-light-mode-only)
![MT7697 bootloader 開機流程：左欄 SPI flash 分區、右欄 SYSRAM。① Boot ROM 讀 flash 開頭向量表，MSP=0x20008E48、PC=0x10000081；② ResetISR 在 flash 上把 .text 與 .data 複製到 SYSRAM 0x20000000；③ main 在 SYSRAM 設 VTOR、打開 fault、檢查 FOTA；④ jump_to 設 MSP=0x20040000 並 bx 到 0x10079001，也就是 app 的 Reset_Handler](../assets/mt7697/boot-flow-zh-dark.svg#gh-dark-mode-only)

| # | 在哪裡執行 | 原始碼 | 做什麼 |
|---|---|---|---|
| ⓪ | ROM | （閉源） | 從 flash 開頭讀向量表 |
| ① | 硬體 | `__isr_vector` | `[0]` 載入 MSP、`[1]` 載入 PC |
| ② | flash（XIP） | `ResetISR()` | 開 cache、把自己複製到 SYSRAM、清 BSS、長跳到 `main` |
| ③ | SYSRAM | `main()` → `process_menu()` | VTOR 指到 RAM、開 fault、初始化 UART、檢查 FOTA |
| ④ | SYSRAM | `jump_to()` | 設 MSP、`bx` 到 app |

主要的程式碼都在 [`driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c)。資料夾叫 `mt7687`，是因為 MT7687（只有 Wi-Fi）和 MT7697 的 CM4 部分相同，共用同一份 bootloader。

## 先看 linker script：存在 flash，連結在 RAM

讀 C 程式碼之前要先看 [`MT7687_CM4_loader_inflash.ld`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/MT7687_CM4_loader_inflash.ld#L26-L42)，後面每一個奇怪的寫法都是因為它：

```ld
SECTIONS
{
    . = ORIGIN(SYSRAM);
    _text_lma_start = LOADADDR(.text);
    .text :
    {
        _text_start = .;
        *(.except_vectors)
        *(.reset_isr)
        *(.text .text.*)
        *(.rodata .rodata.*)
        _text_end = .;
    } > SYSRAM AT > XIP_LOADER_CODE
    ...
```

`> SYSRAM AT > XIP_LOADER_CODE` 的意思是 `.text` 有兩個位址：

- **LMA**（load address，實際存放的位置）：flash `0x1000_0000`
- **VMA**（virtual address，程式以為自己所在的位置）：SYSRAM `0x2000_0000`

所以整份 bootloader 都是照「在 RAM 裡執行」編譯連結的，只是上電時它躺在 flash 上。

為什麼要搬到 RAM？因為 bootloader 的工作包括**改寫 flash**（FOTA 把新韌體從暫存區複製到 CM4 分區）。SPI flash 在抹除或寫入時沒辦法同時讀取，程式如果還在用 XIP 從同一顆 flash 抓指令，CPU 會拿到錯的東西。先搬進 RAM 就沒這個問題。

段落順序也是刻意安排的：`.except_vectors`（向量表）第一個，`.reset_isr` 緊接在後面。

## ① 向量表：`__isr_vector[32]`

[`main.c#L126`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c#L126-L147)：

```c
static unsigned long KernelStack[2048];

__attribute__ ((section(".except_vectors"))) unsigned long __isr_vector[32] =
{
    ((unsigned long)(KernelStack)) + sizeof(KernelStack),         // Master stack pointer(MSP)
    (unsigned long) &_text_lma_start + sizeof(__isr_vector) + 1 , // 1, Reset, in XIP, +1 is for thumb mode
    (unsigned long) NMIISR,                                       // 2, NMI
    (unsigned long) FaultISR,                                     // 3, Hard fault
    (unsigned long) ExpDefHandler,                                // 4, MPU fault
    ...
    (unsigned long) 0,                                            // 15, Systick
    (unsigned long) ExpDefHandler,                                // 16, irq0, UART1
    (unsigned long) ExpDefHandler,                                // 17, irq1,
    /* ... */
};
```

Cortex-M 上電時，硬體只做兩件事：把向量表的 `[0]` 載入 MSP，把 `[1]` 載入 PC。

**`[0]`：初始 stack pointer**

`KernelStack` 是一個 8KB 的 `static` 陣列，放在 SYSRAM 的 `.bss`。stack 往低位址長，所以填的是陣列**尾端**。上電時 SYSRAM 的內容是垃圾也沒關係，stack 只需要一塊能寫的記憶體。

**`[1]`：Reset 向量，整份程式最精妙的一格**

直覺會寫成 `(unsigned long) ResetISR`，但這樣是錯的：`ResetISR` 這個符號的值是 VMA，大約在 `0x2000_0080`，上電當下那裡什麼都沒有，跳過去會立刻當機。

所以這格自己算 flash 上的位址：

```text
_text_lma_start          0x10000000   .text 在 flash 的起點
+ sizeof(__isr_vector)   + 0x80       32 個 entry × 4 bytes
+ 1                      + 1          Thumb bit
= 0x10000081
```

能這樣算，前提是 linker script 保證 `.reset_isr` 緊接在向量表後面。

最後的 `+1` 是 **Thumb bit**。Cortex-M 只會執行 Thumb 指令，載入 PC 的位址 bit0 必須是 1，否則一跳過去就觸發 INVSTATE UsageFault。

**其他格**

- NMI、HardFault 和其他 fault 都是 `while(1)`，接上 debugger 時會停在原地，方便看是哪一種。
- `[15]` SysTick 是 `0`，`[18]` 以後全部是 0（原始碼寫 `/* ... */`）。bootloader 不用中斷，UART 是輪詢的。所以**不能在 bootloader 裡打開 SysTick 或任何 NVIC 中斷**，不然會跳到位址 0。

**對照 binary**

`mt7697_bootloader.bin` 開頭 64 bytes：

```text
$ od -A x -t x4 -N 64 mt7697_bootloader.bin
000000 20008e48 10000081 20000c77 20000c79
000010 20000c7b 20000c7b 20000c7b 00000000
000020 00000000 00000000 00000000 20000c7b
000030 20000c7b 00000000 20000c7b 00000000
```

- `[0]` = `0x20008e48`：`KernelStack` 的尾端，在 SYSRAM。
- `[1]` = `0x10000081`：跟上面算的一樣，是 **flash** 位址。
- `[2]` 之後（`0x20000c77`、`0x20000c79`、`0x20000c7b`…）都是 **SYSRAM** 位址，而且是奇數（Thumb）。只有 Reset 這一格是 flash 位址，其他 handler 都要等搬到 RAM 之後才存在。

## ② `ResetISR()`：在 flash 上把自己搬進 RAM

[`main.c#L170`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c#L170-L284) 做四件事。

### 1. 打開 flash cache

```c
*CACHE_CTRL_BASE    = CACHE_DISABLE;
*CACHE_ENTRY_START  = CACHE_START_ADDR;   // 0x10000100
*CACHE_ENTRY_END    = CACHE_END_ADDR;     // 0x11000000
*CACHE_CHANNEL_EN   = 1;
*CACHE_CTRL_BASE    = CACHE_ENABLE;       // 0x30D
*CACHE_OP_BASE      = CACHE_INVALIDATE_ALL;
```

直接寫 `0x0153_xxxx` 的 cache 控制暫存器，讓接下來的 XIP 讀取（包括複製本身）快一點。

### 2. 判斷自己現在在哪裡

```c
__asm volatile(
    "       bl    getpc            \n\t"
    "getpc:                        \n\t"
    "       mov    %0, r14         \n\t"
            : "=r" (current_pc) ::
    );
if (current_pc > (unsigned long)&_text_start &&
    current_pc < ((unsigned long)&_text_start + text_sect_len)) {
    /* do nothing, we may be resident in SYSRAM(VMA) already. */
} else {
    /* resident in flash, do self-relocation */
    ...
}
```

Cortex-M 沒有指令可以直接讀 PC 的值。這裡的做法是 `bl` 到下一行，LR（r14）就會存著「下一條指令的位址」，等於目前的 PC。

如果 PC 已經落在 SYSRAM 的 `.text` 範圍內，就跳過複製。什麼情況下會「已經在 RAM 裡」？答案在後面「Download agent」那一節。

### 3. 複製 `.text` 和 `.data`

從 LMA 一個 word 一個 word 複製到 VMA，就是一般的 `for` 迴圈。

這裡有一段很值得讀的註解：這段 C 程式在**錯誤的位址**上執行（連結在 RAM，實際在 flash），之所以不會出錯，是**假設** GCC 會把存取全域符號的程式碼編成相對於 PC 的 `ldr rX, [pc, #imm]`。從 literal pool 讀出來的是符號的絕對位址，literal pool 本身則是用相對位址找到的，所以不管程式在哪裡執行都能讀對。

這只是假設，換一個編譯器或最佳化等級就可能不成立。原作者也在註解裡寫了比較穩的做法：用純組語寫。

### 4. 用組語清 BSS，再長跳到 `main`

```c
__asm volatile(
    "    ldr    r0, =_bss_start \n\t"
    "    ldr    r1, =_bss_end   \n\t"
    "loop:                      \n\t"
    "    cmp    r0, r1          \n\t"
    "    bcc    clear           \n\t"
    "    b      done            \n\t"
    "clear:                     \n\t"
    "    movs   r2, #0          \n\t"
    "    str    r2, [r0]        \n\t"
    "    adds   r0, #4          \n\t"
    "    b      loop            \n\t"
    "done:                      \n\t");

__asm volatile(
    "       ldr   r0, =main \n\t"
    "       bx    r0        \n\t");
```

**為什麼清 BSS 不能用 C 寫？** 因為 `KernelStack` 本身就在 `.bss` 裡。用 C 寫的話，迴圈變數存在 stack 上，清著清著就把自己的迴圈變數清成 0，迴圈會停不下來。用組語只碰 r0～r2 三個暫存器，完全不需要 stack。

**為什麼不能直接呼叫 `main()`？** 編譯器可能把 `main()` 編成相對於 PC 的 `bl`。現在 PC 還在 flash，相對跳躍就會跳到 **flash 上那份** `main`。`ldr r0, =main` 會從 literal pool 讀出 `main` 的**絕對 VMA**（SYSRAM），再用 `bx` 跳過去，這才是真正的長跳躍。從這一刻開始，程式改在 RAM 上執行。

### 對照 binary

把 binary 當成 flash 上的樣子（base `0x10000000`）反組譯 `0x10000080` 開始的地方：

```text
100000b6:  f000 f800   bl    0x100000ba          ; bl getpc
100000ba:  4671        mov   r1, lr              ; current_pc = LR
100000bc:  4299        cmp   r1, r3              ; r3 = _text_start = 0x20000000
...
100000ce:  4819        ldr   r0, [pc, #100]      ; _bss_start = 0x20006a60
100000d0:  4919        ldr   r1, [pc, #100]      ; _bss_end   = 0x20014028
...
100000e6:  4815        ldr   r0, [pc, #84]       ; =main → 0x20000c7d
100000e8:  4700        bx    r0
```

literal pool 裡的值跟原始碼的推論完全一致：

| literal | 值 | 意思 |
|---|---|---|
| `_text_lma_start` | `0x10000000` | flash 上的起點 |
| `_text_start` | `0x20000000` | SYSRAM 上的起點 |
| `_text_end` | `0x200055d8` | `.text` 長度 `0x55d8`（約 21.5KB） |
| `_bss_start` / `_bss_end` | `0x20006a60` / `0x20014028` | BSS 約 53KB，含 8KB 的 `KernelStack` |
| `=main` | `0x20000c7d` | SYSRAM 位址，bit0 = 1 |

可以看到 `ldr` 全部是 `[pc, #imm]` 形式，原作者對 GCC 的假設在這份 binary 上成立。

## ③ `main()`：換成 RAM 上的向量表

[`main.c#L587`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c#L587-L647)：

```c
__isr_vector[1] = (unsigned long)ResetISR;
NVIC_SetupVectorTable((unsigned long)__isr_vector);   // 寫 SCB->VTOR

SCB->SHCSR = SCB_SHCSR_USGFAULTENA_Msk |
             SCB_SHCSR_BUSFAULTENA_Msk |
             SCB_SHCSR_MEMFAULTENA_Msk;

top_xtal_init();
...
hw_uart_init();
hw_uart_puts("loader init \r\n");
__enable_irq();
flash_switch_mode(SPIQ);
process_menu();
```

- `__isr_vector` 跟著 `.text` 一起被複製到 SYSRAM `0x2000_0000` 了。把 VTOR 指過去，之後發生的例外都查 RAM 上這份表。`[1]` 改回正確的 VMA，只是讓這份表的內容前後一致。
- 打開 SHCSR 的三個 enable bit 之後，UsageFault、BusFault、MemManage 會各自進入自己的 handler，不會全部升級成 HardFault。
- 接著初始化時脈、GPIO、UART，把 flash 切到 SPI Quad 模式，然後進 `process_menu()`。

在 binary 裡對應的指令：

```text
20000c7c:  4827      ldr   r0, [pc, #156]    ; r0 = 0x20000000（__isr_vector）
20000c7e:  4b28      ldr   r3, [pc, #160]    ; r3 = 0x20000081（ResetISR 的 VMA）
20000c82:  6043      str   r3, [r0, #4]      ; __isr_vector[1] = ResetISR
20000c88:  4b26      ldr   r3, [pc, #152]    ; r3 = 0xe000ed00（SCB）
20000c8a:  f44f 22e0 mov.w r2, #0x70000
20000c8e:  625a      str   r2, [r3, #36]     ; SHCSR（0xE000ED24）= 0x70000
...
20000caa:  b662      cpsie i                 ; __enable_irq()
```

`0x70000` 就是 bit16～18：MEMFAULTENA、BUSFAULTENA、USGFAULTENA。

### `process_menu()`：FOTA 與（被關掉的）選單

[`process_menu()`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c#L524-L585) 依編譯選項做三件事：

1. **回復出廠設定**（`MTK_BOOTLOADER_RESTORE_DEFAULT_ENABLE`）：開機時讀某個 GPIO，是高電位就把 NVDM 分區整個抹掉。
2. **FOTA**（[`process_fota()`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c#L317-L347)）：FOTA 暫存分區有東西，就複製到 CM4 code 分區。這是單映像（single image）的 OTA。
3. **UART 選單**（`MTK_BOOTLOADER_MENU_ENABLE`）：印出 `1. Burn flash to ...` 等選項，用 XMODEM 收資料燒到 bootloader、CM4 或 N9 分區，60 秒沒有輸入就自動選 `c` 開機。

但實際燒在板子上的那份**沒有選單**。`project/.../bootloader/GCC/feature.mk` 寫的是 `MTK_BL_BOOT_MENU_ENABLE = n`，binary 裡也找不到 `Burn flash`、`FWVER`、`Your choose` 這些字串，只有：

```text
loader init
fota: upgrade
fota: start copy
fota: TMP is empty, skip upgrade
fota: upgrade done
fota: upgrade failed
jump to (%x)
```

另外，binary 裡的 FOTA 字串比 GitHub 上的 `process_fota()` 豐富很多，例如 `fota_head.m_bin_info[%d].m_sig_length`、`m_is_compressed`、`LZMA_flash_init fail`。看起來實際編進去的 FOTA 函式庫支援 LZMA 壓縮，header 裡也有簽章欄位。不過這部分的原始碼不在這個 repo 的 bootloader 資料夾裡，我沒有往下追。

那選單去哪了？在 download agent 裡，後面一節會講。

## ④ `jump_to()`：交棒給 app

[`main.c#L149`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c#L149-L164)：

```c
static void jump_to(unsigned long pc_addr, unsigned long sp_addr)
{
    __asm(
        "    isb                        \n\t"
        "    dsb                        \n\t"
        /* update MSP */
        "    mov   sp, %0               \n\t"
        /* jump to Reset ISR and never return */
        "    mov   r0, %1               \n\t"
        "    bx    r0                   \n\t"
        :: "r" (sp_addr), "r" (pc_addr) :
    );
}
```

[`process_menu()`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/driver/board/linkit7697_hdk/bootloader/src/mt7687/main.c#L547-L555) 呼叫時傳入的值：

```c
sp_addr = CM4_SYSRAM_END;                               // 0x20040000
pc_addr = (CM4_CODE_BASE + 0x10000000) | 0x1;           // 0x10079001
jump_to(pc_addr, sp_addr);
```

逐行看：

| 指令 | 作用 |
|---|---|
| `isb` / `dsb` | 屏障。`dsb` 等之前的記憶體存取（cache 設定、flash 寫入）全部完成，`isb` 清掉管線，確保之後抓的指令是新的。慣例順序是先 `dsb` 再 `isb`，這裡寫反了，實務上影響不大。 |
| `mov sp, %0` | reset 後 CONTROL.SPSEL = 0，SP 就是 MSP。這行等於把主 stack 換到 SYSRAM 尾端 `0x2004_0000`。從這一刻起 bootloader 自己的 stack 就作廢了，所以這個函式**絕對不能 return**。 |
| `mov r0, %1` / `bx r0` | 跳到 app。`bx` 會看目標位址的 bit0 決定指令集，所以前面要把 bit0 設成 1。 |

原始碼註解把 `| 0x1` 寫成「switch to ARM state」，這是**錯的**。Cortex-M 根本沒有 ARM state，bit0 = 1 的意思是「維持 Thumb」。如果是 0，`bx` 之後會觸發 INVSTATE UsageFault。

**對照 binary**：`jump_to` 被 inline 進 `main()` 了，就在 `0x20000d0a`：

```text
20000cfe:  4813        ldr   r0, [pc, #76]     ; "jump to (%x) \r\n"
20000d00:  4913        ldr   r1, [pc, #76]     ; 0x10079000
20000d02:  f000 f83a   bl    hw_uart_printf
20000d06:  4a13        ldr   r2, [pc, #76]     ; pc_addr = 0x10079001
20000d08:  4b13        ldr   r3, [pc, #76]     ; sp_addr = 0x20040000
20000d0a:  f3bf 8f6f   isb   sy
20000d0e:  f3bf 8f4f   dsb   sy
20000d12:  469d        mov   sp, r3
20000d14:  4610        mov   r0, r2
20000d16:  4700        bx    r0
```

跟原始碼一模一樣，連 `isb` 在 `dsb` 前面的順序也一樣。

這段程式還有幾個值得注意的地方：

- inline asm 改了 r0，卻沒有把它列進 clobber list。因為不會 return 所以不會出事，但其實直接寫 `bx %1` 就好。
- 跳之前**沒有**關中斷、沒有 deinit UART 和 GPIO、沒有關 cache、也沒有改 VTOR。這些狀態都原封不動交給 app，VTOR 還指著 bootloader 在 SYSRAM 的向量表。app 一定要自己重設這些東西。

## ⑤ App 怎麼接手

`jump_to` 直接跳到 `0x10079000` 的**第一個位元組**，所以那裡必須是程式碼。

Arduino core 的 [`mt7687_flash.ld`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/middleware/third_party/arduino/hardware/arduino/mt7697/variants/linkit_7697/linkscripts/mt7687_flash.ld#L27-L39) 是這樣安排的：

```ld
XIP_CODE (arx) : ORIGIN = 0x10079000, LENGTH = 0x001ED000
...
. = ORIGIN(XIP_CODE);
.text :
{
    _text_start = .;
    KEEP(*(.init))
    ...
```

[`startup_mt7687.s`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/middleware/third_party/arduino/hardware/arduino/mt7697/variants/linkit_7697/startup_mt7687.s#L185-L202) 把 `Reset_Handler` 放在 `.init` 段：

```asm
    .section .init
    .globl    Reset_Handler
Reset_Handler:
    ldr    sp, =__StackTop       /* set stack pointer */
    cpsid i
    ...
```

所以 `0x10079000` 就是 `Reset_Handler`。它一開始就重設 SP、關中斷，把 bootloader 留下的狀態蓋掉，接著複製 `.data`、搬程式到 TCM、清 BSS、呼叫 `SystemInit` 和 `main`。

app 自己的 `__isr_vector` 放在 `.data` 裡，會跟著被搬到 SYSRAM。重設 VTOR 的動作應該在 `SystemInit()` 裡，這點我沒有往下追。

## 跟 STM32 那類 bootloader 的差別

常見的 Cortex-M bootloader（例如很多 STM32 專案）把 app 的開頭當成**向量表**：

```c
uint32_t sp = *(uint32_t *)APP_BASE;
uint32_t pc = *(uint32_t *)(APP_BASE + 4);
SCB->VTOR = APP_BASE;
__set_MSP(sp);
((void (*)(void))pc)();
```

| | STM32 式 | MT7697 這份 |
|---|---|---|
| app 開頭放什麼 | 向量表 | `Reset_Handler` 的程式碼 |
| SP 從哪來 | app 向量表的 `[0]` | 寫死的常數 `0x20040000` |
| PC 從哪來 | app 向量表的 `[1]` | 寫死的常數 `0x10079001` |
| 誰設 VTOR | bootloader | app 自己 |
| app 換 linker script 會怎樣 | 只要向量表在開頭就能開機 | `Reset_Handler` 不在第一個位元組就會當機 |

MT7697 的做法比較省事，但 bootloader 和 app 的 linker script 綁得比較緊。

## Download agent：同一份程式的 RAM 版本

讀到這裡會有兩個疑問：

1. `ResetISR` 為什麼要判斷「是不是已經在 RAM 裡」？從 flash 開機明明一定是在 flash 上。
2. 選單被關掉了，Arduino IDE 是怎麼燒錄的？

答案都在燒錄工具裡。`flash_tool` 的 `upload.py` 流程是：

1. 用 USB-UART 的 RTS／DTR 把晶片重開，進入 **ROM 的 UART 下載模式**。ROM 會一直送字元 `C`，這是 XMODEM 的開始信號。
2. 用 XMODEM-1K 把 `da97.bin`（download agent）送進去。
3. 等 DA 印出 `@FWVER=...`，再送 `1`、`2` 或 `3` 選擇要燒哪個分區。

這個 `@FWVER=` 加上數字選單的流程，跟 `user_select()` 一模一樣。打開 `da97.bin` 看：

```text
vector: [0]=0x200099a8  [1]=0x20000081  [2]=0x20000d77 ...
strings:
  loader init
  @FWVER=%s
  1. Burn flash to 0x%x(BootLoader)
  2. Burn flash to 0x%x(XIP)
  3. Burn flash to 0x%x(FW)
  c. Boot from flash 0x%x(XIP)
  Your choose %c
  jump to (%x)
```

`da97.bin` 就是**同一份 bootloader 打開選單、改用 [`bootloader-ram.ld`](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK/blob/53acd43fbee57b034141068969fa643465dfd743/project/linkit7697_hdk/apps/bootloader/GCC/bootloader-ram.ld) 連結**的版本。那個 linker script 是 `.text > SYSRAM`，沒有 `AT >`，所以 LMA 也在 SYSRAM，Reset 向量算出來是 `0x20000000 + 0x80 + 1 = 0x20000081`。

ROM 透過 UART 把它直接放進 SYSRAM 執行。`ResetISR` 用 `bl getpc` 發現 PC 已經在 `.text` 範圍內，就跳過複製。這就是那個判斷存在的理由：**同一份原始碼可以編成「從 flash 開機」和「被 ROM 載進 RAM」兩種版本**。

這也說明了變磚之後怎麼救：bootloader 燒壞了，ROM 的 UART 下載模式還在，用 `upload.py -t ldr` 送 DA 再重燒 `mt7697_bootloader.bin` 就好。

## 自己動手驗證

裝好 Arduino IDE 的 LinkIt 7697 套件之後，檔案在：

- `%LOCALAPPDATA%\Arduino15\packages\LinkIt\tools\flash_tool\1.4.4\`：`mt7697_bootloader.bin`、`da97.bin`、`upload.py`
- `%LOCALAPPDATA%\Arduino15\packages\arduino\tools\arm-none-eabi-gcc\4.8.3-2014q1\bin\`：`arm-none-eabi-objdump`

向量表：

```bash
od -A x -t x4 -N 64 mt7697_bootloader.bin
```

把 binary 當成 flash 上的樣子（base `0x10000000`）看 `ResetISR`：

```bash
arm-none-eabi-objdump -D -b binary -m arm -M force-thumb \
  --adjust-vma=0x10000000 \
  --start-address=0x10000080 --stop-address=0x10000140 \
  mt7697_bootloader.bin
```

看搬到 RAM 之後的 `main` 和 `jump_to`（base 改成 `0x20000000`）：

```bash
arm-none-eabi-objdump -D -b binary -m arm -M force-thumb \
  --adjust-vma=0x20000000 \
  --start-address=0x20000c7c --stop-address=0x20000d60 \
  mt7697_bootloader.bin
```

同一份 binary 要用兩個不同的 base 來讀，這就是「LMA ≠ VMA」最直接的體會。

## 讀的時候踩到的坑

- **`system/linkit_7697/firmwares/` 底下也有一份 `mt7697_bootloader.bin`**，大小是 27,284 bytes，跟 `flash_tool` 那份（27,232 bytes）不一樣，`main` 的位址也差了一點（`0x2000106d` vs `0x20000c7d`）。這篇讀的是 `flash_tool` 那份，也就是 `bootloader_update` 腳本實際燒的那份。
- **raw binary 反組譯要加 `-M force-thumb`**。沒加的話 objdump 會用 ARM 指令集解，整片都是亂碼。
- **literal pool 會被當成指令反組譯**。看到 `ldr rX, [pc, #imm]` 要自己去讀那個位址的 4 bytes，不要看它後面反組譯出來的「指令」。
- **GitHub 上的原始碼不等於 binary**。選單、回復出廠設定是編譯選項，實際燒進去的版本是關掉的；FOTA 的實作也比 repo 裡的完整。讀原始碼時要先確認 feature 開關。

## 參考資料

- [MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK](https://github.com/MediaTek-Labs/Arduino-Add-On-for-LinkIt-SDK)（本文原始碼，commit `53acd43`）
- [MediaTek Labs：MT7697 chipset](https://labs-mediatek-com.pages.dev/en/chipset/MT7697)
- [MediaTek Labs：LinkIt 7697](https://labs-mediatek-com.pages.dev/en/platform/linkit-7697)
- [MediaTek：MT7697 產品頁](https://www.mediatek.com/products/home-networking/mt7697)
- [Arm：Cortex-M4 Devices Generic User Guide](https://developer.arm.com/documentation/dui0553/latest/)（向量表、VTOR、SHCSR、Thumb bit）
