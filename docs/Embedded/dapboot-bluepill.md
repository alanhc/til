# 在 Blue Pill 上跑 dapboot：用 GDB 單步看 bootloader 交棒，再用 USB DFU 換 app

[上一篇](./ft232h-jtag-stm32.md)用 FT232H 當 JTAG 除錯器，燒了一支裸機 blink。[MT7697 那篇](./mt7697-bootloader-walkthrough.md)則是讀了一份「存在 flash、搬到 RAM 執行、寫死位址跳過去」的 bootloader。這篇把兩件事接起來：在同一塊 STM32F103C8T6 Blue Pill 上燒一個開源的 USB DFU bootloader **[dapboot](https://github.com/devanlai/dapboot)**，然後：

1. 用 GDB 一條一條單步，看 bootloader 怎麼把控制權交給 app
2. 從 app 那邊回頭驗證它繼承了什麼狀態（VTOR、時脈）
3. 不動跳線，用 JTAG 寫 backup register 強制進 DFU
4. 透過 USB 用 `dfu-util` 燒一版新的 app，再讀回比對

dapboot 是 ISC 授權，整份程式不大，用 libopencm3 寫，不依賴 HAL，很適合拿來讀。

版本說明：

- dapboot [`8a1f099`](https://github.com/devanlai/dapboot/tree/8a1f099f6e43ce292eee3a326bd810b7e55f198f)（2025-02），build target `BLUEPILL`。下文原始碼連結都指向這個 commit。
- 板子是正版 STM32F103C8T6（`DBGMCU_IDCODE 0x20036410`、`CPUID 0x411FC231`、flash 64KB），**BOOT0 = 0**，從 flash 開機。
- 除錯器沿用上一篇的 FT232H + OpenOCD（xPack 0.12.0），GDB 是 Arm GNU Toolchain 14.3。主機是 Windows 11，dapboot 在 WSL 裡編譯。

完整檔案放在 [`static/code/dapboot-bluepill/`](https://github.com/alanhc/til/tree/main/static/code/dapboot-bluepill)。

## 先講結論

- dapboot 佔 flash 前 8KB，app 從 **`0x0800_2000`** 開始。它判斷 app 有不有效，只看 app 向量表 `[0]` 是不是落在 RAM，**沒有 CRC 也沒有簽章**。
- 交棒是 7 條指令：寫 VTOR、從 app 向量表讀 `[0]` 設 MSP、讀 `[1]` 然後 `blx`。用 GDB 單步可以逐條看到 VTOR 從 0 變 `0x2000`、MSP 換成 app 的、PC 落到 app 的 `Reset_Handler`。
- VTOR 寫的是 **`0x0000_2000`** 不是 `0x0800_2000`。能用是因為 STM32F1 從 flash 開機時，flash 會被映射到位址 0。
- app 會繼承 dapboot 設好的 **72MHz** 時脈。上一篇的 blink 以為自己跑在 8MHz，放到 dapboot 後面閃得快很多。
- app 的啟動碼如果把 VTOR 寫死成 `0x0800_0000`（上一篇的 blink 就是），中斷會跳回 bootloader 的向量表。**要改成 app 自己的位址。**
- OpenOCD 的 `verify_image` 會在 `0x2000_0000` 執行 CRC 小程式，**蓋掉 app 的 RAM**。在 app 跑到一半時驗證，之後讀到的變數都是垃圾。

## dapboot 在做什麼

先讀原始碼再上板，比較知道要看什麼。

### Flash 怎麼切

[`stm32f103x8.ld`](https://github.com/devanlai/dapboot/blob/8a1f099f6e43ce292eee3a326bd810b7e55f198f/src/stm32f103/stm32f103x8.ld) 給 bootloader 的空間是向量表 `0x150` 加程式 `0x1EB0`，剛好 8KB。[`dapboot.h`](https://github.com/devanlai/dapboot/blob/8a1f099f6e43ce292eee3a326bd810b7e55f198f/src/dapboot.h) 定義 app 的位置：

```c
#define APP_INITIAL_STACK ((vector_table_t*)APP_BASE_ADDRESS)->initial_sp_value  /* app [0] */
#define APP_ENTRY_POINT   ((vector_table_t*)APP_BASE_ADDRESS)->reset             /* app [1] */
#define BOOTLOADER_OFFSET 0x00002000
```

### 要不要留在 bootloader

[`main()`](https://github.com/devanlai/dapboot/blob/8a1f099f6e43ce292eee3a326bd810b7e55f198f/src/dapboot.c) **先設好時脈和 GPIO 再判斷**，下面三個條件任一成立就進 DFU：

| 條件 | 函式 | 說明 |
|---|---|---|
| `BKP_DR1 == 0x4F42` | `target_get_force_bootloader()` | app 想進 bootloader 時，寫這個值再 reset。讀到後**立刻清掉**，只有效一次 |
| BOOT1（PB2）為高 | 同上 | Blue Pill 的設定把板上的 **BOOT1 跳線**當按鈕，讀之前會等約 20ms 去彈跳 |
| app 無效 | `validate_application()` | 只有一行，見下面 |

```c
bool validate_application(void) {
    return ((uint32_t)(APP_INITIAL_STACK) & 0x2FFE0000) == 0x20000000;
}
```

只要 app 的初始 SP 落在 `0x2000_0000`～`0x2001_FFFF` 就算有效。空白 flash 讀起來是 `0xFFFFFFFF`，所以沒燒 app 時會停在 DFU。反過來說，燒進一份壞掉但開頭剛好像 SP 的 app，dapboot 也會照跳。

### 交棒

```c
static void jump_to_application(void) {
    if (APP_RELOCATE_VECTORS)
        target_relocate_vector_table();       /* SCB_VTOR = APP_BASE_ADDRESS & 0xFFFF */
    target_pre_main();                        /* F103 上是空的 weak function */
    __set_MSP((uint32_t)(APP_INITIAL_STACK));
    APP_ENTRY_POINT();
    while (1);
}
```

跟 MT7697 那份的差別：

| | MT7697 bootloader | dapboot |
|---|---|---|
| 在哪裡執行 | 從 XIP flash 搬到 SYSRAM | 直接在內部 flash 上執行 |
| 為什麼 | 要改寫自己所在的 SPI flash | F1 可以一邊執行一邊寫其他 page |
| app 入口 | 寫死 `0x10079001`，跳到第一個位元組 | 讀 app 向量表的 `[0]`、`[1]` |
| 誰設 VTOR | app 自己 | bootloader（`0x2000`） |
| 檢查 app | 沒有 | 只看初始 SP |
| 更新方式 | FOTA 分區、UART XMODEM | USB DFU |

## 編譯 dapboot

dapboot 用 `make` 加 libopencm3，libopencm3 的建置會用到 Python，在 Windows 上直接編比較麻煩，所以放在 WSL 裡做。手邊的 WSL 沒有裝 `arm-none-eabi-gcc`，但有之前跑 [Arduino 101 Zephyr](./zephyr-arduino-101.md) 留下的 Zephyr SDK 0.10.3，裡面有 `arm-zephyr-eabi-gcc` 8.3：

```bash
git clone https://github.com/devanlai/dapboot.git
cd dapboot
git checkout 8a1f099f6e43ce292eee3a326bd810b7e55f198f
git submodule update --init
cd src
make TARGET=BLUEPILL PREFIX=arm-zephyr-eabi-
```

兩個小坑：

- **`PREFIX` 要包含結尾的 `-`**。`rules.mk` 是 `CC := $(PREFIX)gcc`，寫成 `PREFIX=arm-zephyr-eabi` 會去找 `arm-zephyr-eabigcc`。
- **Zephyr SDK 0.10.3 沒有 newlib-nano**，連結時 `cannot find -lc_nano`。把 `rules.mk` 的 `LDFLAGS += -specs=nano.specs` 註解掉、改用完整 newlib 就好。dapboot 幾乎不用 libc，換掉之後 `dapboot.bin` 是 6,744 bytes，還在 8KB 內。用正常的 Arm GNU Toolchain 就不用這一步。

整理好的指令在 [`build-dapboot.sh`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/build-dapboot.sh)。

```text
.vectors  0x150 bytes  @ 0x08000000
.text     0x18f4 bytes @ 0x08000150
reset_handler          @ 0x08001040
```

## 準備一支放在 0x08002000 的 app

沿用上一篇的裸機 blink，改三個地方（[`app.c`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/app.c)、[`app.ld`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/app.ld)）：

1. linker script 的 `FLASH` 改成 `ORIGIN = 0x08002000, LENGTH = 56K`。
2. **`Reset_Handler` 原本第一行是 `SCB_VTOR = 0x08000000;`**。放在 bootloader 後面時，這行會把 VTOR 指回 dapboot 的向量表，app 一有中斷就跳進 bootloader。改成 `0x08002000`。
3. 進 `Reset_Handler` 第一件事，先把 dapboot 留下的 VTOR 和 `RCC_CFGR` 存到區域變數，清完 `.bss` 再寫進全域變數，讓 GDB 讀得到：

```c
uint32_t vtor_at_entry;   /* VTOR as dapboot left it */
uint32_t cfgr_at_entry;   /* RCC_CFGR as dapboot left it */

void Reset_Handler(void)
{
    uint32_t vtor = SCB_VTOR, cfgr = RCC_CFGR;   /* 什麼都還沒改之前先讀 */
    SCB_VTOR = 0x08002000;                       /* 指到自己的向量表 */
    /* ... 複製 .data、清 .bss ... */
    vtor_at_entry = vtor;                        /* .bss 清完才能寫 */
    cfgr_at_entry = cfgr;
    main();
}
```

編出來 312 bytes，向量表 `[0] = 0x2000_5000`（會通過 dapboot 的檢查）、`[1] = 0x0800_20A1`。

## 燒錄：先備份

板子原本的內容先用 JTAG 整片讀出來，之後要還原就寫回去（[`flash.tcl`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/flash.tcl)）：

```tcl
init
reset halt
wait_halt 2000
dump_image backup-before-dapboot.bin 0x08000000 0x10000
flash write_image erase dapboot.elf
flash write_image erase app.elf
verify_image dapboot.elf
verify_image app.elf
reset run
shutdown
```

兩份 ELF 都帶著自己的位址，所以 `write_image` 不用另外指定 offset。燒完讀兩個向量表確認：

```text
vec@0x08000000: 0x20005000 0x08001041   # dapboot
vec@0x08002000: 0x20005000 0x080020a1   # app
```

> 上一篇提過，`init` 之後直接 `halt` 會得到 `target was in unknown state when halt was requested`，後面的指令都不會跑。這次改用 `reset halt`：沒接 NRST 時 OpenOCD 會用 SYSRESETREQ 做軟體 reset，CPU 停在第一條指令。

## 實測 1：交棒之後 app 拿到什麼

`reset run` 之後讓它跑一下，再停下來讀（[`state.tcl`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/state.tcl)）：

```text
pc            = 0x0800202c
SCB_VTOR now  = 0x08002000
vtor_at_entry = 0x00002000
cfgr_at_entry = 0x001dc40a
blink_count   = 0x1b2
BKP_DR1       = 0x0000
GPIOB_IDR PB2 = 0
```

| 值 | 意思 |
|---|---|
| `pc = 0x0800_202C` | CPU 在 app 裡，正在跑 delay 迴圈 |
| `BKP_DR1 = 0`、PB2 = 0 | 兩個「留在 bootloader」的條件都不成立，所以跳去 app |
| `vtor_at_entry = 0x0000_2000` | 證實 `APP_BASE_ADDRESS & 0xFFFF` |
| `SCB_VTOR now = 0x0800_2000` | app 自己改成完整位址 |
| `cfgr_at_entry = 0x001D_C40A` | 見下面 |

`RCC_CFGR` 拆開：

| 欄位 | 位元 | 值 | 意思 |
|---|---|---|---|
| SWS | [3:2] | `10` | 系統時脈來自 PLL |
| PPRE1 | [10:8] | `100` | APB1 = HCLK / 2 |
| ADCPRE | [15:14] | `11` | ADC = PCLK2 / 8 |
| PLLSRC | [16] | `1` | PLL 輸入是 HSE（8MHz 晶振） |
| PLLMUL | [21:18] | `0111` | ×9 |
| USBPRE | [22] | `0` | USB = PLL / 1.5 = 48MHz |

8MHz × 9 = **72MHz**。上一篇的 blink 跑在 reset 預設的 8MHz HSI，同樣的 delay 迴圈在這裡快 9 倍，用眼睛就看得出來。

dapboot 留給 app 的東西，整理起來：

- 72MHz PLL 時脈。app 如果想自己設時脈，要先關 PLL 才能改倍頻。
- GPIOB、GPIOC 的時脈已開，PC13 是 open-drain 輸出。
- PA12（USB D+）被設成 push-pull 輸出、低電位，這是 dapboot 用來模擬 USB 斷線的。app 要用 USB 得自己把它改回來。
- VTOR = `0x2000`。

## 實測 2：GDB 單步看交棒

`main()` 和 `jump_to_application()` 都被編譯器 inline 進 `reset_handler`。反組譯找 `msr MSP`，交棒就在這 7 條指令：

```text
80013c2: mov.w r2, #0x2000        ; APP_BASE_ADDRESS & 0xFFFF
80013c6: ldr   r3, =0xE000ED08    ; SCB_VTOR
80013c8: str   r2, [r3]
80013ca: ldr   r3, =0x08002000    ; APP_BASE_ADDRESS
80013cc: ldr   r2, [r3, #0]       ; app [0]
80013ce: msr   MSP, r2
80013d2: ldr   r3, [r3, #4]       ; app [1]
80013d4: blx   r3
```

OpenOCD 開著當 GDB server，GDB 在 `0x080013c2` 下硬體中斷點，reset 之後一條一條 `stepi`，每步印暫存器（[`step-jump.gdb`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/step-jump.gdb)）：

```bash
openocd -f ft232h-jtag.cfg -f target/stm32f1x.cfg -c init
arm-none-eabi-gdb -q -batch -x step-jump.gdb dapboot.elf
```

```text
== at jump sequence: pc=0x080013c2 msp=0x20004fb8 VTOR=0x00000000
   app vector [0]=0x20005000 [1]=0x080020a1
mov.w r2, #8192      -> r2=0x00002000 r3=0x00000000 msp=0x20004fb8 VTOR=0x00000000
ldr   r3, [pc, #20]  -> r2=0x00002000 r3=0xe000ed08 msp=0x20004fb8 VTOR=0x00000000
str   r2, [r3, #0]   -> r2=0x00002000 r3=0xe000ed08 msp=0x20004fb8 VTOR=0x00002000
ldr   r3, [pc, #20]  -> r2=0x00002000 r3=0x08002000 msp=0x20004fb8 VTOR=0x00002000
ldr   r2, [r3, #0]   -> r2=0x20005000 r3=0x08002000 msp=0x20004fb8 VTOR=0x00002000
msr   MSP, r2        -> r2=0x20005000 r3=0x08002000 msp=0x20005000 VTOR=0x00002000
ldr   r3, [r3, #4]   -> r2=0x20005000 r3=0x080020a1 msp=0x20005000 VTOR=0x00002000
blx   r3             -> pc=0x080020a0

== now in app: Reset_Handler in section .text of app.elf
```

可以逐條看到：

- `str` 之後 VTOR 從 0 變成 `0x2000`。
- `msr MSP` 之後 MSP 從 dapboot 用到一半的 `0x2000_4FB8` 換成 app 的 `0x2000_5000`。
- `r3` 拿到 `0x0800_20A1`，bit0 = 1 是 Thumb bit，由 app 的向量表自己帶著，不像 MT7697 要手動 `| 1`。
- `blx` 之後 **PC 是 `0x0800_20A0`**：bit0 只用來告訴 CPU 指令集，不會留在 PC 裡。
- 用 `add-symbol-file app.elf` 載入 app 的符號，`info symbol $pc` 確認落在 `Reset_Handler`。

這裡 dapboot 用一般的 C 函式呼叫（`blx`）進 app，沒有用 inline asm。能這樣做是因為 MSP 已經換掉、函式又是 `noreturn`，不會再回到舊的 stack。

## 實測 3：不動跳線，強制進 DFU

app 想進 bootloader 的正規做法是寫 `BKP_DR1 = 0x4F42` 再 reset。這裡直接用 JTAG 代勞（[`enter_dfu.tcl`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/enter_dfu.tcl)）：

```tcl
init
halt
wait_halt 2000
# 開 PWR、BKP 時脈，解除 backup domain 寫保護，再寫入 magic
mww 0x4002101C [expr {[read_memory 0x4002101C 32 1] | (1<<27) | (1<<28)}]
mww 0x40007000 [expr {[read_memory 0x40007000 32 1] | (1<<8)}]
mwh 0x40006C04 0x4F42
reset run
```

backup domain 在系統 reset 時不會被清掉，所以 dapboot 讀得到這個值。reset 後停下來看：

```text
BKP_DR1 before reset = 0x4f42
pc after reset       = 0x080002e8    # st_usbfs_poll
BKP_DR1 after boot   = 0x0000
```

PC 在 `st_usbfs_poll`，也就是 `main()` 裡 `while (1) { usbd_poll(); }` 那個 DFU 迴圈；`BKP_DR1` 被清回 0。

### USB 有沒有接通，從晶片這邊看

第一次進 DFU 時 Windows 沒有出現裝置，後來晶片還自己跑回了 app。為了看清楚，改成進 DFU 之後**不 halt CPU**，每 300ms 讀一次 USB 周邊的暫存器（[`dfu_watch.tcl`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/dfu_watch.tcl)）：

```text
t=300ms  CNTR=0x9c00 FN=246  LCK=1 DADDR=0x81
t=600ms  CNTR=0x9c00 FN=559  LCK=1 DADDR=0x81
t=900ms  CNTR=0x9c00 FN=871  LCK=1 DADDR=0x81
...
t=2100ms CNTR=0x9c00 FN=44   LCK=1 DADDR=0x81
```

- `FN`（frame number）每 300ms 增加約 300，跑到 2047 再繞回來：主機每 1ms 送一個 SOF，晶片都有收到。
- `LCK = 1`：連續收到 SOF，frame timer 已鎖定。
- `DADDR = 0x81`：bit7 是 USB 功能啟用，主機分配的位址是 1。

這次 Windows 就認到了：

```text
Status FriendlyName           InstanceId
OK     DAPBoot DFU Bootloader USB\VID_1209&PID_DB42\263614876675545748FF7306
```

序號就是晶片的 96-bit UID（`target_get_serial_number()`）。**不用 Zadig**：dapboot 有回報 Microsoft OS 描述元（[`winusb.c`](https://github.com/devanlai/dapboot/blob/8a1f099f6e43ce292eee3a326bd810b7e55f198f/src/winusb.c)），Windows 第一次看到時自動綁 WinUSB。

至於第一次為什麼會跑回 app：[`dfu.c`](https://github.com/devanlai/dapboot/blob/8a1f099f6e43ce292eee3a326bd810b7e55f198f/src/dfu.c#L368-L379) 收到 USB bus reset 時，**只要已經被 set configuration 過**，就會當成 detach 直接 reset 晶片：

```c
static void dfu_on_usb_reset(void) {
    if (!dfu_enumerated) {
        return;
    }
    dfu_on_detach_complete(NULL, NULL);   /* scb_reset_system() */
}
```

這是為了讓「燒完後主機送 bus reset」就能切到新 app。所以第一次其實有被列舉，之後主機送了一次 bus reset，dapboot 就照設計重開；這時 `BKP_DR1` 已經清掉，重開後直接進 app。主機為什麼送那次 reset 沒有查出來，第二次（Windows 第一次安裝驅動那次）之後就穩定了。

## 實測 4：用 dfu-util 透過 USB 換 app

做一版把 delay 加大 10 倍的 v2（[`build-app.sh`](https://github.com/alanhc/til/blob/main/static/code/dapboot-bluepill/build-app.sh)），轉成 raw binary，用 dfu-util 0.11 燒：

```bash
dfu-util -l
```

```text
Found DFU: [1209:db42] ver=0111, devnum=1, cfg=1, intf=0, path="4-2", alt=0, name="DAPBoot DFU", serial="263614876675545748FF7306"
```

```bash
dfu-util -d 1209:db42 -a 0 -D app_v2.bin -R
```

```text
DFU state(2) = dfuIDLE, status(0) = No error condition is present
Device returned transfer size 1024
Download done.
DFU state(7) = dfuMANIFEST, status(0) = No error condition is present
Warning: Invalid DFU suffix signature
unable to read DFU status after completion (LIBUSB_ERROR_IO)
```

最後那行不是失敗。Blue Pill 的 build 預設 `DFU_WILL_DETACH = 1`，dapboot 在 manifest 階段就自己 reset 切到新 app 了，dfu-util 想再讀狀態時裝置已經不在。`Invalid DFU suffix` 是因為 `.bin` 沒加 DFU suffix，dapboot 不檢查。

用 JTAG 讀回 `0x0800_2000` 的 312 bytes，跟 `app_v2.bin` 逐位元組相同。量 1 秒內 `blink_count` 的增量是 **+3**，LED 明顯變慢。

### 坑：`verify_image` 會蓋掉 app 的 RAM

驗證 v2 時讀到的 `vtor_at_entry` 是 `0x4E0A_43C0`、`blink_count` 從 `0x2000_45xx` 這種像位址的值開始加，一度以為 DFU 之後的開機路徑跳過了 app 的 `Reset_Handler`。

換成普通 reset 再讀就正常了：

```text
after JTAG reset: pc=0x08002034 blink_count=0x3 vtor_at_entry=0x00002000 cfgr_at_entry=0x001dc40a
```

原因是驗證時我在 app 跑到一半下了 `verify_image`。OpenOCD 驗證時會下載一段算 CRC 的小程式到 target 的 working area 執行，**`stm32f1x.cfg` 的 working area 就是從 `0x2000_0000` 開始**，剛好是 app 的 `.bss`。resume 之後，app 就拿著被蓋掉的值繼續跑。`flash write_image` 也會用 working area，只是燒完通常會 reset 所以看不出來。

結論：**在 `verify_image` 或 `write_image` 之後讀 RAM，要先 reset**。

## 踩到的坑

- **`PREFIX` 少了結尾的 `-`**，make 會去找 `arm-zephyr-eabigcc`。
- **Zephyr SDK 0.10.3 沒有 newlib-nano**，要把 `-specs=nano.specs` 拿掉。
- **app 啟動碼把 VTOR 寫死成 `0x0800_0000`**，放到 bootloader 後面就會出事。
- **JTAG 掃描讀到全 1**：FT232H 重新插拔後就好了。同樣的症狀也可能是 Blue Pill 沒上電、TDO 沒接好，或 FT232H 的 I2C 開關沒關。
- **`init` 後直接 `halt` 回報 unknown state**：改用 `reset halt`。
- **Git Bash 呼叫 `wsl.exe`**：參數裡的 `/mnt/c/...` 會被 MSYS 改寫成 `C:/Program Files/Git/mnt/c/...`，要加 `MSYS_NO_PATHCONV=1`；`bash -lc '...'` 裡的 `$PATH` 也會先被 Git Bash 展開。把指令寫成腳本檔再交給 WSL 執行最省事。
- **第一次進 DFU 被主機的 bus reset 送回 app**：dapboot 的設計如此，再進一次就好。
- **`verify_image` 蓋掉 `0x2000_0000` 開始的 RAM**。

## 參考資料

- [devanlai/dapboot](https://github.com/devanlai/dapboot)（commit `8a1f099`）
- [libopencm3](https://github.com/libopencm3/libopencm3)
- [dfu-util](https://dfu-util.sourceforge.net/)
- [RM0008：STM32F10x Reference Manual](https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-stm32f105xx-and-stm32f107xx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)（RCC_CFGR、BKP、USB 的 FNR／DADDR、boot 映射）
- [USB Device Firmware Upgrade 1.1 規格](https://www.usb.org/sites/default/files/DFU_1.1.pdf)（`bitWillDetach`、manifest 狀態）
- [OpenOCD User's Guide：`working-area`](https://openocd.org/doc/html/CPU-Configuration.html)
