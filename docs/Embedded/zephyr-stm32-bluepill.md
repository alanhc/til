# 在 STM32 Blue Pill 上跑 Zephyr（只接 ST-Link）

手上有一塊 STM32F103C8T6 的 Blue Pill，只用一支 ST-Link V2 接 SWD 四條線（3.3V、SWDIO、SWCLK、GND），**沒有接 NRST，也沒有接 UART**。這篇記錄從確認晶片、備份原廠韌體、架 Zephyr 4.4 環境，到把 blinky 燒進去的完整指令，以及中間踩到的「韌體一睡眠，除錯器就連不上」的坑。

主機是 Ubuntu 24.04 x86_64。

## 先講結論：踩坑重點

- **Zephyr 用 `stm32_min_dev@blue` 這個 board**，LED 在 PC13、低電位點亮，console 預設走 USART1。
- **燒錄過一次之後，SWD 就可能再也連不上**：OpenOCD 回 `examination failed`，`st-info --probe` 讀到 `chipid: 0x000`。Zephyr 閒置時會執行 `WFI`，而這個接法沒有 NRST 可以用 connect-under-reset。
- **救援靠 BOOT0**：BOOT0 跳到 1、按 RESET，晶片改從內建的系統 bootloader 開機，不跑 Flash 裡的程式，SWD 就能穩定連上；燒完再把 BOOT0 跳回 0。
- **`CONFIG_STM32_ENABLE_DEBUG_SLEEP_STOP=y` 救不了這個情況**。韌體確實會在開機時打開睡眠時的除錯，但斷電重開、讓韌體先跑起來之後，一樣連不上。根本原因我沒有查到。
- **`st-info --probe` 會誤報**：同一個時間點 `st-info` 讀到 `0x000`，OpenOCD 卻連得上。要判斷能不能連，用 OpenOCD。
- **接上除錯器去觀察，可能會讀到錯的狀態**：有一段時間用 SWD 讀到的值全都在說「韌體卡住了」，實際上 LED 正常在閃。最後是斷電重開、不接除錯器，用眼睛看 LED 才確認韌體沒問題。

## 一、裝工具、確認晶片

```bash
sudo apt install openocd stlink-tools
```

`stlink-tools` 會裝 udev 規則，之後不用 sudo 就能存取 ST-Link。裝完讓規則生效：

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb --attr-match=idVendor=0483
```

確認 ST-Link 有接上，讀晶片資訊：

```bash
lsusb | grep 0483:3748
st-info --probe
```

```text
Found 1 stlink programmers
  version:    V2J45S7
  flash:      65536 (pagesize: 1024)
  sram:       20480
  chipid:     0x410
  dev-type:   STM32F1xx_MD
```

Blue Pill 上很常見 CKS32、CS32、APM32 這類相容晶片，chip ID 一樣回報 `0x410`。要分辨真假，用 OpenOCD 讀 CPU 核心的 CPUID 和幾個 ID 暫存器：

```bash
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
  -c init -c halt \
  -c 'echo "CPUID [mdw 0xE000ED00]"' \
  -c 'echo "IDCODE [mdw 0xE0042000]"' \
  -c 'echo "FLASHKB [mdh 0x1FFFF7E0]"' \
  -c 'echo "FLASH_OBR [mdw 0x4002201C]"' \
  -c 'echo "VEC [mdw 0x08000000 2]"' \
  -c resume -c shutdown 2>&1 | grep -E '^(CPUID|IDCODE|FLASHKB|FLASH_OBR|VEC)'
```

```text
CPUID 0xe000ed00: 411fc231
IDCODE 0xe0042000: 20036410
FLASHKB 0x1ffff7e0: 0040
FLASH_OBR 0x4002201c: 03fffffc
VEC 0x08000000: 20005000 08000345
```

| 暫存器 | 值 | 意義 |
|---|---|---|
| CPUID | `0x411FC231` | Cortex-M3 r1p1。正版 STM32F103 是 r1p1；常見相容晶片多半回報 r2p1（`0x412FC231`） |
| DBGMCU_IDCODE | `0x20036410` | DEV_ID `0x410`（F1 medium-density）、REV_ID `0x2003` |
| Flash size | `0x0040` | 64 KB |
| FLASH_OBR | `0x03FFFFFC` | RDPRT = 0，沒有讀取保護，可以自由讀寫 |
| 向量表 | `20005000 08000345` | 初始 SP 在 SRAM 頂端、reset handler 在 Flash，代表裡面已經有韌體 |

## 二、先備份原廠韌體

動手前先把整顆 64 KB 讀回來，之後隨時可以還原：

```bash
mkdir -p ~/stm32-bluepill/backup && cd ~/stm32-bluepill/backup
st-flash read original-firmware-64k.bin 0x08000000 0x10000
```

還原：

```bash
st-flash write original-firmware-64k.bin 0x08000000
```

## 三、架 Zephyr 環境

主機要有 `cmake`、`ninja`、`dtc`、`gperf`：

```bash
sudo apt install ninja-build device-tree-compiler gperf ccache
```

用 uv 建 Python 虛擬環境並裝 west。我刻意用系統的 Python 3.12，不用比較新的版本，避免 Zephyr 的相依套件還沒跟上：

```bash
mkdir -p ~/zephyrproject && cd ~/zephyrproject
uv venv -p /usr/bin/python3 .venv
source .venv/bin/activate
uv pip install west
```

初始化 Zephyr v4.4.2。完整的 `west update` 會抓下所有 HAL，好幾 GB；用 `project-filter` 只留下 CMSIS、STM32 HAL 和 SEGGER（之後 RTT 會用到），淺層 clone 大約 30 秒：

```bash
west init -m https://github.com/zephyrproject-rtos/zephyr --mr v4.4.2 -o=--depth=1 .
west config manifest.project-filter -- '-.*,+cmsis.*,+hal_stm32,+segger'
west update --narrow -o=--depth=1
```

裝 Python 相依套件、匯出 CMake package，再用 `west sdk` 只裝 ARM 工具鏈：

```bash
uv pip install -r zephyr/scripts/requirements-base.txt
west zephyr-export
west sdk install --version 1.0.1 -t arm-zephyr-eabi -b ~/opt
```

之後每次開新的 shell，先跑這兩行：

```bash
cd ~/zephyrproject && source .venv/bin/activate
export ZEPHYR_SDK_INSTALL_DIR=~/opt/zephyr-sdk-1.0.1
```

## 四、編 blinky

Blue Pill 在 Zephyr 4.4 裡叫 `stm32_min_dev`，有 `blue` 和 `black` 兩個 revision，差在 LED 接哪隻腳。`blue` 是 PC13、active-low：

```bash
west build -p always -b stm32_min_dev@blue -d build/blinky zephyr/samples/basic/blinky
```

```text
Memory region         Used Size  Region Size  %age Used
           FLASH:       15408 B        64 KB     23.51%
             RAM:        4112 B        20 KB     20.08%
```

## 五、燒錄

這個 board 預設的燒錄方式就是 OpenOCD，設定檔用 ST-Link：

```bash
west flash -d build/blinky
```

**第一次燒錄會成功**，LED 開始每秒閃一次。問題出在第二次。

## 六、坑：韌體一睡眠，除錯器就連不上

第二次 `west flash` 開始，OpenOCD 一直失敗：

```text
Warn : target stm32f1x.cpu examination failed
Error: jtag status contains invalid mode value - communication failure
```

`st-info --probe` 也讀到 `chipid: 0x000`。

第一個懷疑是 Zephyr 閒置時執行的 `WFI`：睡眠時核心時脈會被關掉，SWD 就碰不到核心。STM32 可以設定 `DBGMCU_CR` 讓睡眠時保留除錯，Zephyr 對應的選項是 `CONFIG_STM32_ENABLE_DEBUG_SLEEP_STOP`，預設只有跑 ztest 時才會打開：

```bash
grep STM32_ENABLE_DEBUG_SLEEP_STOP build/blinky/zephyr/.config
```

```text
# CONFIG_STM32_ENABLE_DEBUG_SLEEP_STOP is not set
```

打開它重編：

```bash
west build -p always -b stm32_min_dev@blue -d build/blinky zephyr/samples/basic/blinky \
  -- -DCONFIG_STM32_ENABLE_DEBUG_SLEEP_STOP=y
```

反組譯也確認韌體開機時確實會寫入 `DBGMCU_CR`（`0xE0042004`）的 bit 0–2（sleep、stop、standby 三種模式下保留除錯）。**但這沒有解決問題**：斷電重開、讓韌體先跑起來之後，不管用 1000 kHz 還是 200 kHz 去連，都是 0/5。

另外排除掉的幾個可能：

- **SWD 腳位被改成 GPIO**：STM32F1 的 PA13/PA14 可以被 AFIO 的 `SWJ_CFG` 釋放成一般 GPIO。但用 GDB 從 reset 一路跑過初始化，SWD 仍然連得上，中斷點也停得下來，所以不是這個。
- **其他程式碼清掉 `DBGMCU_CR`**：在原始碼和反組譯結果裡都只找到 `soc_config.c` 那一處寫入。

唯一能確定的規律是：**除錯器從 reset 就一路接著，沒問題；韌體先自己跑起來、之後才去連，就連不上**。根本原因我沒有查出來。

## 七、救援：BOOT0

Blue Pill 上有兩組跳線，BOOT0 那組決定 reset 後從哪裡開機：

| BOOT0 | 開機來源 |
|---|---|
| 0 | 主 Flash（`0x08000000`），也就是你的韌體 |
| 1 | System memory（`0x1FFFF000`），ST 燒在晶片裡的 bootloader |

BOOT0 跳到 1 再按 RESET，晶片就不會執行 Flash 裡的韌體，SWD 能穩定連上。用 OpenOCD 確認：

```bash
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
  -c init -c halt -c 'echo "PC [reg pc]"' -c shutdown 2>&1 | grep '^PC'
```

```text
PC pc (/32): 0x1ffff37e
```

PC 落在 `0x1FFFxxxx`，代表正在跑系統 bootloader。這時候燒錄：

```bash
west flash -d build/blinky
```

燒完把 BOOT0 跳回 0、按 RESET，新韌體就會開始跑。跳線之後**一定要按 RESET**：BOOT0 只在 reset 那一瞬間被讀取。

我把整個流程寫成一支小腳本。它會等 OpenOCD 連續 3 次都讀到這顆晶片的 IDCODE 才開始燒，避免剛好在韌體醒來的瞬間連上、燒到一半又斷線：

```bash
#!/bin/bash
# Flash a Zephyr build onto the Blue Pill using the BOOT0 recovery flow.
set -e
BUILD=${1:-build/blinky}
cd ~/zephyrproject
source .venv/bin/activate
export ZEPHYR_SDK_INSTALL_DIR=~/opt/zephyr-sdk-1.0.1

echo ">> Set BOOT0 = 1, then press RESET."
ok=0
for i in $(seq 1 120); do
	if timeout 10 openocd -f interface/stlink.cfg -f target/stm32f1x.cfg \
		-c init -c 'echo "ID [mdw 0xE0042000]"' -c shutdown 2>&1 | grep -q '^ID .*20036410'; then
		ok=$((ok + 1))
	else
		ok=0
	fi
	[ $ok -ge 3 ] && break
	sleep 1
done
[ $ok -ge 3 ] || { echo "!! Chip not reachable"; exit 1; }

west flash -d "$BUILD"
echo ">> Done. Set BOOT0 = 0, then press RESET to run the new firmware."
```

一開始我用 `st-info --probe` 判斷晶片能不能連，結果腳本一直卡在等待：**同一個時間點 `st-info` 讀到 `0x000`，OpenOCD 卻連得上**。所以判斷改用 OpenOCD。

成功的輸出：

```text
[stm32f1x.cpu] halted due to debug-request, current mode: Thread
xPSR: 0x01000000 pc: 0x1ffff020 msp: 0x200001fc
Info : device id = 0x20036410
Info : flash size = 64 KiB
Warn : Adding extra erase range, 0x08003c30 .. 0x08003fff
wrote 15408 bytes from file build/blinky/zephyr/zephyr.hex in 1.148692s (13.099 KiB/s)
```

`Adding extra erase range` 是正常的：Flash 只能整頁（1 KB）抹除，韌體結尾沒有對齊頁邊界，OpenOCD 就把最後一頁剩下的部分也一起抹掉。

## 八、坑：接上除錯器去觀察，看到的不一定是真的

在找出 BOOT0 這個方法之前，有一段時間 SWD 是連得上的，我就直接讀暫存器想看韌體在做什麼。結果每一項都在說「韌體卡住了」：

| 讀了什麼 | 讀到 | 看起來的意思 |
|---|---|---|
| GPIOC_ODR（`0x4001100C`） | 一直是 `0` | PC13 從來沒翻轉過 |
| kernel 的 `curr_tick` | 一直是 `0` | 開機到現在一個 tick 都沒累積 |
| DHCSR（`0xE000EDF0`） | `0x00050001` | 沒被 halt，但核心在睡眠（`S_SLEEP` = 1） |
| PC | 每次都是 `0x08002818` | 停在 idle 迴圈的 `__enable_irq` |

可是用 GDB 從 reset 開始跑，`main` 有進去，SysTick 的中斷處理函式 `sys_clock_isr` 也確實會被觸發，看起來又完全正常：

```bash
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg &
gdb-multiarch -q -batch build/blinky/zephyr/zephyr.elf \
  -ex 'target extended-remote :3333' \
  -ex 'monitor reset halt' \
  -ex 'break main' -ex 'break sys_clock_isr' \
  -ex 'continue' -ex 'bt 3' \
  -ex 'continue' -ex 'bt 5' \
  -ex 'monitor shutdown'
```

最後把 ST-Link 從 USB 拔掉再插回去，讓板子完全斷電、清掉所有除錯狀態，什麼都不接，**LED 正常每秒閃一次**。

所以那些讀數是除錯器在場時才會出現的狀態。能確定的是：`DHCSR` 裡的除錯致能位元一旦被除錯器打開，按 RESET 也清不掉，只有斷電才會清。至於為什麼會讓 tick 停住，我沒有查清楚。教訓是：**觀察低功耗的 MCU 時，先用最直接的方式（看 LED、量腳位）確認現象，再相信除錯器讀到的值**。

## 九、還沒做的

- **接上 NRST**：把 ST-Link 的 RST 接到 Blue Pill 的 R 腳，就能用 connect-under-reset，先把晶片按在 reset 裡、連上後才放開，不用再動 BOOT0：

  ```bash
  west flash -d build/blinky --cmd-pre-init "reset_config srst_only srst_nogate connect_assert_srst"
  ```

  這也能幫忙縮小上面那個問題的範圍：如果每次都成功，就能確認問題只出在「連上一顆已經在跑的晶片」。
- **用 RTT 看 printk**：沒有接 UART，可以讓 Zephyr 的 console 走 SEGGER RTT，再用 OpenOCD 透過 SWD 讀出來。
- **往上加難度**：改閃燈頻率、用按鍵觸發 GPIO 中斷、開 Zephyr shell、用 `k_thread` 跑兩個執行緒。
