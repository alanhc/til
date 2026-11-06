# BeagleBone Black bring-up 練習：從 UART 到手動 bootz

用 BeagleBone Black（AM335x）練 bring-up 的第一天紀錄：接 debug UART、錄完整開機 log、在 U-Boot 裡直接戳 GPIO 暫存器點 LED，最後不靠 `bootcmd`，自己一步步把 Linux 開起來。

自編 Linux 7.3 走 TFTP 開機的完整過程另寫成一篇：[在 BeagleBone Black 上把自己編的 Linux 7.3 開起來](./bbb-kernel-7.3-bringup.md)。

## 接線

- Debug UART 在板子上的 6-pin **J1**：pin 1 GND、pin 4 RX（BBB 收）、pin 5 TX（BBB 送），接 3.3V 的 USB-TTL（我用 CP2102）。VCC 不接，TX/RX 交叉。
- 參數 115200 8N1，不開 flow control。
- 板子 mini-USB 另外會出一個 `/dev/ttyACM0`，那是 Linux 起來後才有的 USB gadget serial，**看不到 ROM/SPL/U-Boot**，bring-up 一定要用 J1。

| 裝置 | USB ID | 用途 |
|---|---|---|
| `/dev/ttyUSB0` | `10c4:ea60` CP2102 | J1 debug UART，開機全程 |
| `/dev/ttyACM0` | `1d6b:0104` BeagleBone gadget | Linux 起來後的 console |

踩到的坑：CP2102 和 BBB 插在同一顆 USB hub 上，BBB 上電瞬間整顆 hub 重新列舉，`ttyUSB0` 掉線約 2 秒，SPL 那段 log 剛好就在這 2 秒內印完而漏錄。錄 log 的程式要能斷線自動重連；想錄到 SPL，UART 轉接器要插主機板直連埠，或 BBB 改用 DC 供電。

### 先確認是哪個裝置、線有沒有通

```bash
udevadm info /dev/ttyUSB0 | grep -E 'ID_MODEL=|ID_VENDOR_ID|ID_MODEL_ID'   # CP2102_USB_to_UART_Bridge_Controller
udevadm info /dev/ttyACM0 | grep ID_MODEL=                                 # TI_AM335x_BeagleBone_Black
id | grep -o dialout                                                       # 自己要在 dialout 群組
# 送一個 Enter，4 秒內有回應就代表雙向都通
stty -F /dev/ttyUSB0 115200 cs8 -cstopb -parenb -crtscts raw -echo
(timeout 4 cat /dev/ttyUSB0 > probe.txt &); sleep 0.5; printf '\r' > /dev/ttyUSB0; sleep 4; cat -v probe.txt
```

### 錄 log 和送指令的工具

minicom 是給人看的，要讓程式（和 Claude Code）讀得到、也能代打指令，我另外寫了兩支小工具：

- [`serial_console.py`](https://github.com/alanhc/til/blob/main/static/bbb/serial_console.py)：每行加主機時間戳寫進 log；寫進 `logs/tx.fifo` 的東西會送給板子；`logs/break.flag` 存在時負責攔 autoboot（見下一節）；USB 斷線會自動重連。
- [`ub.sh`](https://github.com/alanhc/til/blob/main/static/bbb/ub.sh)：送一條 U-Boot 指令，等到下一個 `=>` 再把輸出印出來。

```bash
mkdir -p ~/bbb-bringup/logs && cd ~/bbb-bringup
python3 serial_console.py /dev/ttyUSB0 logs/current.log &     # pyserial 要用系統的 python3
printf 'bdinfo\r' > logs/tx.fifo                              # 直接送
./ub.sh 'printenv bootcmd'                                     # 送並等 =>
```

注意 logger 開著時 `/dev/ttyUSB0` 被它佔住，要自己開 minicom 前先把它停掉。

## 正常開機長什麼樣

先錄一份原廠完整開機 log 當對照組，之後弄壞東西時才知道哪裡不一樣。

開機鏈的每一層，以及這次在哪一層踩到坑（橘色）：

![BeagleBone Black 開機鏈：Boot ROM、SPL、U-Boot、Linux kernel、systemd 與 userspace，SPL、U-Boot、userspace 三層標出這次踩到的坑](../assets/bbb/boot-chain-zh-light.svg#gh-light-mode-only)
![BeagleBone Black 開機鏈：Boot ROM、SPL、U-Boot、Linux kernel、systemd 與 userspace，SPL、U-Boot、userspace 三層標出這次踩到的坑](../assets/bbb/boot-chain-zh-dark.svg#gh-dark-mode-only)

| 階段 | 看到什麼 |
|---|---|
| U-Boot | `U-Boot 2019.04`、`DRAM: 512 MiB`、從 EEPROM 讀到 `board_name=A335BNLT` |
| 找開機設定 | 依序找 `/uEnv.txt`、`/boot.scr`，最後在 SD 的 `/boot/uEnv.txt` 找到，跑 `uname_boot` |
| 載入 | vmlinuz → dtb → initrd，`bootz 0x82000000 0x88080000:size 0x88000000` |
| kernel 早期 | `OF: fdt: Machine model`、`earlycon: omap8250 at MMIO 0x44e09000`（UART0） |
| 儲存 | `mmcblk0` = SD、`mmcblk1` = eMMC |
| rootfs → systemd → login | 約 50 秒到 login |

正常板子也會印的無害訊息：btrfs superblock checksum（U-Boot 在試探檔案系統類型）、`ti-sysc ... error -16`、`l3-aon-clkctrl failed to disable`、`tps65217 Failed to locate of_node`。

## 中斷 autoboot

這塊板子 `bootdelay=0`，`Press SPACE to abort autoboot in 0 seconds` 幾乎沒時間按。解法是上電前就開始每 20ms 送一個空白，看到 `=>` 提示符才停。U-Boot 在 `bootdelay=0` 時仍會檢查一次 UART 有沒有輸入。

```bash
touch logs/break.flag    # 上電前先打開；攔到 => 之後 serial_console.py 會自己刪掉它
# 然後拔電再插回去
grep -n 'autoboot interrupted' logs/current.log | tail -1
```

這個「攔 autoboot」的邏輯改了四版才穩，每一版都是被實際上電打臉：

| 版本 | 做法 | 出了什麼事 |
|---|---|---|
| 1 | flag 存在就一直每 20ms 送空白 | 攔得到，但空白也灌進了 Linux：login prompt 收到一長串空白，那次軟重開還卡在關機（後來證實卡住另有原因） |
| 2 | 只在看到 `U-Boot 20xx` banner 之後、`Starting kernel` 之前送 | 沒攔到：只在最後 64 bytes 裡找 banner，但 CP2102 一次丟進幾百 bytes，banner 還沒檢查就被擠出去了 |
| 3 | 每收到一塊資料就整塊掃描 `U-Boot 20` / `Board:` / `DRAM:` / `Starting kernel` | 又漏一次：USB hub 重新列舉花了 4 秒，port 回來時 U-Boot 已經印到 `Board:` 之後 |
| 4 | port 重新打開時，只要 flag 還在，先**盲送 4 秒**，再接標記判斷 | 之後就穩了；但 hub 慢到 3 秒以上、資料一次湧進來時還是可能漏 |

改版時先用 pty 當假 serial port 模擬，不必每次都請人插拔一次：

```python
import os, pty, subprocess, time, tty
m, s = pty.openpty(); tty.setraw(s)
open("logs/break.flag", "w").close()
p = subprocess.Popen(["python3", "serial_console.py", os.ttyname(s), "logs/t.log"])
time.sleep(0.3)
os.write(m, b"[  1.0] systemd stuff\r\n")                    # Linux 階段：不該收到空白
os.write(m, b"U-Boot 2019.04 banner\r\n" + b"x" * 500 + b"\r\nPress SPACE\r\n")
time.sleep(0.3); os.set_blocking(m, False)
print(os.read(m, 4096).count(b" "), "spaces sent")         # 應該 > 0
os.write(m, b"=> "); time.sleep(0.5)
print("flag removed:", not os.path.exists("logs/break.flag"))
p.terminate()
```

根本的解法是硬體：UART 轉接器不要和 BBB 共用 USB hub。

## 從記憶體看開機：每一段跑在哪、把誰搬去哪

上面的開機鏈是「誰交棒給誰」，換成記憶體的角度看，每一段其實都在做同一件事：**下一段需要的空間，現在這段還沒有，或者會被蓋掉，所以先搬家**。

AM335x 開機時會用到三個地方，性質完全不同：

- **Boot ROM**：晶片內、唯讀，出廠就燒好，上電後 CPU 從這裡開始執行。
- **內部 SRAM**：晶片內，上電就能用，但只有約 109 KB 給 ROM 放下載的 image。
- **DRAM**：板子上外接的 DDR3，512 MiB，要等 SPL 設好 DDR 控制器（EMIF）才能讀寫。

| 東西 | 放在哪 | 位址 | 誰放的 |
|---|---|---|---|
| Boot ROM 程式 | 晶片內 ROM | `0x4002_0000` | 出廠燒死 |
| SPL（MLO 的內容） | 內部 SRAM | `0x402F_0400` | Boot ROM 從 SD 複製 |
| SPL 的 BSS、malloc | DRAM | `0x80A0_0000` | SPL 初始化 DDR 後自己移過去 |
| U-Boot（重定位前） | DRAM | `0x8080_0000` | SPL 從 SD 載入 |
| U-Boot（重定位後） | DRAM 頂端 | `0x9FF5_9000` | U-Boot 自己搬 |
| zImage | DRAM | `0x8200_0000` | `load`／`tftp` |
| DTB、initrd | DRAM | `0x8800_0000`／`0x8808_0000` → `0x8F5D_2000`／`0x8F5E_E000` | `load` 放，`bootz` 再搬 |
| kernel（解壓後） | DRAM | `0x8000_8000` | zImage 的解壓程式 |

UART0（`0x44E0_9000`）、GPIO1（`0x4804_C000`）、EMIF（`0x4C00_0000`）這些位址雖然也能用 `md` 讀，但它們是周邊暫存器（MMIO），不是記憶體。

下圖三條直欄就是三個地方（ROM 本身不放資料，所以只寫在左邊「跑在哪」）：

![開機五步驟，分成內部 SRAM、DRAM、SD 卡或網路三欄：Boot ROM 把 MLO 從 SD 複製進 SRAM 0x402F0400；SPL 在 SRAM 裡初始化 DDR，再把 u-boot.img 從 SD 搬進 DRAM 0x80800000；U-Boot 在 DRAM 裡把自己搬到 0x9FF59000；load 把 zImage、DTB、initrd 放到 0x82000000 起，bootz 再把 DTB、initrd 搬到 0x8F5D2000；zImage 把 kernel 解壓到 0x80008000](../assets/bbb/boot-memory-flow-zh-light.svg#gh-light-mode-only)
![開機五步驟，分成內部 SRAM、DRAM、SD 卡或網路三欄：Boot ROM 把 MLO 從 SD 複製進 SRAM 0x402F0400；SPL 在 SRAM 裡初始化 DDR，再把 u-boot.img 從 SD 搬進 DRAM 0x80800000；U-Boot 在 DRAM 裡把自己搬到 0x9FF59000；load 把 zImage、DTB、initrd 放到 0x82000000 起，bootz 再把 DTB、initrd 搬到 0x8F5D2000；zImage 把 kernel 解壓到 0x80008000](../assets/bbb/boot-memory-flow-zh-dark.svg#gh-dark-mode-only)

同樣五步畫在一張記憶體地圖上，外框標出 DRAM、內部 SRAM、Boot ROM 三個區域（圓圈數字對應上圖步驟，不按比例）：

![AM335x 開機時的記憶體地圖，分三個區域。DRAM 由高到低是 U-Boot 本體 0x9FF59000、bootz 搬移後的 DTB 與 initrd 0x8F5D2000、DTB 與 initrd 0x88000000、zImage 0x82000000、SPL 的 BSS 0x80A00000、重定位前的 U-Boot 0x80800000、kernel 解壓位置 0x80008000；中間隔著周邊暫存器；內部 SRAM 放 MLO 0x402F0400；Boot ROM 在 0x40020000](../assets/bbb/boot-memory-map-zh-light.svg#gh-light-mode-only)
![AM335x 開機時的記憶體地圖，分三個區域。DRAM 由高到低是 U-Boot 本體 0x9FF59000、bootz 搬移後的 DTB 與 initrd 0x8F5D2000、DTB 與 initrd 0x88000000、zImage 0x82000000、SPL 的 BSS 0x80A00000、重定位前的 U-Boot 0x80800000、kernel 解壓位置 0x80008000；中間隔著周邊暫存器；內部 SRAM 放 MLO 0x402F0400；Boot ROM 在 0x40020000](../assets/bbb/boot-memory-map-zh-dark.svg#gh-dark-mode-only)

位址的來源分兩種：`relocaddr`、`loadaddr`、bootz 搬移後的位址是這塊板子上實際讀到的；SRAM、U-Boot 載入位址、`bootm_size` 是 AM335x TRM 與 [U-Boot v2019.04 的 TI 預設設定](https://github.com/u-boot/u-boot/blob/v2019.04/include/configs/ti_armv7_common.h)。

### ① Boot ROM：DDR 還不能用，只有 SRAM

- 上電後 CPU 從晶片內的 ROM 開始跑，讀 SYSBOOT 腳位（鎖存在 `CONTROL_STATUS`，`0x44E1_0040`）決定從 MMC、eMMC、UART 還是 USB 開機。
- 這時 DDR 還沒初始化，ROM 唯一能放東西的地方是**內部 SRAM**：`0x402F_0400` 到 `0x4030_B800` 是給下載 image 的區域，約 109 KB。
- MLO 是 `mkimage -T omapimage` 包出來的：前 512 bytes 是 TOC（CHSETTINGS），接著 8 bytes 的 GP header 寫著 image 大小和載入位址。ROM 照它把 SPL 複製到 `0x402F_0400` 再跳過去。
- 這就是為什麼一定要有 SPL：完整的 U-Boot 好幾百 KB，SRAM 放不下。

### ② SPL：在 SRAM 裡把 DDR 叫醒

- SPL 設好 PLL、時脈、pinmux，再透過 EMIF 設 DDR3 時序。做完這步，`0x8000_0000` 起的 512 MiB 才能讀寫，U-Boot 印的 `DRAM: 512 MiB` 就是這裡來的。
- DDR 一起來，SPL 就把自己的 BSS 和 malloc 移到 DRAM（`0x80A0_0000` 起），不再擠在 SRAM。
- 接著從 SD 的 FAT 分割區讀 `u-boot.img`，放到 DRAM 的 `0x8080_0000` 再跳過去。這是**第一次從 SRAM 跨到 DRAM**。

### ③ U-Boot：先把自己搬到 DRAM 頂端

- U-Boot 一開始在 `0x8080_0000` 跑，`board_init_f` 量完 DRAM 大小、規劃好布局後，把整份自己複製到頂端的 `relocaddr = 0x9ff59000`，修正所有絕對位址，再跳到新位置繼續跑。
- 位移量是 `0x9ff59000 − 0x80800000 = 0x1f759000`，就是 `bdinfo` 的 `reloc off`。用 gdb／JTAG 下斷點時，重定位後的符號要加上這個值。
- 頂端往下依序是 U-Boot 本體、malloc 區、`bd`／`gd` 結構、stack。低位址整段空出來給 kernel。

### ④ load + bootz：放進低位址，再搬一次

- `load` 把 zImage、DTB、initrd 放到 `0x8200_0000`、`0x8800_0000`、`0x8808_0000`（細節和重疊檢查見[手動 load + bootz](#手動-load--bootz)）。
- `bootz` 會把 DTB 和 initrd 再搬一次。它們沒有搬到 DRAM 真正的頂端 `0x9FFx_xxxx`，而是落在 `0x8F5D_2000`，因為 TI 的預設 env 有 `bootm_size=0x10000000`：只能用 DRAM 前 256 MB，也就是 `0x9000_0000` 以下。arm32 kernel 早期只看得到 lowmem，DTB 和 initrd 放太高會讀不到。
- 可以用 `printenv bootm_size fdt_high initrd_high` 確認。

### ⑤ zImage：自己再解壓一次

- zImage 開頭是一段解壓程式，把真正的 kernel 解壓到 `PHYS_OFFSET + TEXT_OFFSET = 0x8000_8000`。
- `loadaddr` 選 `0x8200_0000`，就是在解壓目的地上方留 32 MB，解壓時不會蓋到 zImage 自己；萬一重疊，解壓程式會先把自己搬開。
- 開 MMU 之後，實體 `0x8000_0000` 對應到虛擬 `0xC000_0000`，之後 kernel log 裡看到的多半是虛擬位址。

在板子上對得起來的幾個指令：

```text
=> md.l 0x44e10040 1     # CONTROL_STATUS：SYSBOOT 鎖存值
=> bdinfo                # relocaddr、reloc off、DRAM bank
=> printenv bootm_size   # 0x10000000
```

```bash
xxd -s 0x200 -l 8 MLO    # GP header：image 大小、載入位址（預期是 00 04 2f 40）
```

## bdinfo / printenv 看到的東西

- DRAM 在 `0x8000_0000`，大小 `0x2000_0000`（512 MiB）。
- `relocaddr = 0x9ff59000`：U-Boot 會把自己搬到 DRAM 頂端，把低位址讓給 kernel（見上一節第 ③ 步）。
- `bootcmd` = `findfdt` → `init_console` → `envboot` → `distro_bootcmd`。
- `findfdt` 用 EEPROM 的 `board_name` / `board_rev` 決定 `fdtfile`，這就是 U-Boot 判斷「這是哪塊板子」的地方。
- 原廠 `boot` 腳本裡穿插 `gpio set 53..56`，那四個 GPIO 就是 USR0–3 LED，拿來當**開機進度條**。

## 用 md/mw 點 USR LED

USR0–3 接在 GPIO1 的 bit 21–24，GPIO1 基底 `0x4804_C000`。

讓一個 GPIO 動起來要依序過四關，下面每格的數值是這次在 U-Boot 實際讀到的：

![讓 GPIO 點亮 LED 的四步：時脈讀到 0x2、pinmux 讀到 0x27、GPIO_OE 一開始是 0xffffffff 要清 0、SETDATAOUT 寫 0x01e00000](../assets/bbb/gpio-led-zh-light.svg#gh-light-mode-only)
![讓 GPIO 點亮 LED 的四步：時脈讀到 0x2、pinmux 讀到 0x27、GPIO_OE 一開始是 0xffffffff 要清 0、SETDATAOUT 寫 0x01e00000](../assets/bbb/gpio-led-zh-dark.svg#gh-dark-mode-only)

先讀、不寫，確認前置條件：

```text
=> md.l 0x44e000ac 1     # CM_PER_GPIO1_CLKCTRL = 0x2：時脈開著、IDLEST=0
=> md.l 0x44e10854 4     # conf_gpmc_a5..a8 = 0x27：mode 7 (GPIO)、receiver on
=> md.l 0x4804c134 1     # GPIO_OE = 0xffffffff：全部是輸入！
=> md.l 0x4804c13c 1     # GPIO_DATAOUT = 0
```

再寫：

```text
=> mw.l 0x4804c134 0xfe1fffff   # OE 清 bit 21–24 → 輸出
=> mw.l 0x4804c194 0x01e00000   # SETDATAOUT：四顆全亮
=> mw.l 0x4804c190 0x00200000   # CLEARDATAOUT：只關 USR0
```

| 清掉的 bit | DATAOUT 讀回 | LED |
|---|---|---|
| 21 | `0x01c00000` | USR0 |
| 22 | `0x01800000` | USR1 |
| 23 | `0x01000000` | USR2 |
| 24 | `0x00000000` | USR3 |

學到的順序，也是 Linux `gpio-omap` + DTS `pinctrl` / `gpio-leds` 幫你做掉的事：

1. **時脈**：模組沒開 clock，讀寫暫存器會拿到垃圾或直接 data abort。
2. **pinmux**：pin 要切到 GPIO mode，不然接的是別的周邊。
3. **方向**：OE 清 0 才是輸出。「暫存器寫了 LED 不亮」最常見就是忘了這步。
4. **輸出值**：用 SET/CLEARDATAOUT，寫 1 的 bit 才有作用，不用 read-modify-write，也不會和別人搶。

## 手動 load + bootz

```text
=> part list mmc 0     # p1 FAT 36MB、p2 swap、p3 ext4 rootfs
=> ls mmc 0:3 /boot    # kernel / initrd / dtbs / uEnv.txt 都在 rootfs 的 /boot

=> load mmc 0:3 ${loadaddr} /boot/vmlinuz-6.12.45-bone34                  # 0x82000000
=> load mmc 0:3 ${fdtaddr}  /boot/dtbs/6.12.45-bone34/am335x-boneblack.dtb # 0x88000000
=> load mmc 0:3 ${rdaddr}   /boot/initrd.img-6.12.45-bone34                # 0x88080000
=> setenv rdsize ${filesize}    # filesize 每次 load 都會被覆蓋，要馬上存
```

載完先驗 header：

- `md.l ${loadaddr}`：`MZ`（EFI stub）+ 一串 ARM NOP `e1a00000`，offset 0x24 是 zImage magic **`016f2818`**。
- `md.b ${fdtaddr}`：**`d0 0d fe ed`**，FDT magic。
- 檢查三塊不重疊：kernel 8.8MB 到 `0x82876200` < dtb `0x88000000`；dtb 99KB 到 `0x88018493` < initrd `0x88080000`。很多 bring-up 失敗就是 kernel 變大蓋掉了 dtb。

`bootz` 前後 DRAM 裡的配置（紫色是 load 放的位置，青色是之後被搬去的位置，不按比例）：

![bootz 前後的 DRAM 配置：zImage 在 0x82000000、DTB 在 0x88000000、initrd 在 0x88080000，bootz 把 DTB 與 initrd 搬到 0x8F5D2000，U-Boot 本體在 0x9FF59000](../assets/bbb/bootz-memory-zh-light.svg#gh-light-mode-only)
![bootz 前後的 DRAM 配置：zImage 在 0x82000000、DTB 在 0x88000000、initrd 在 0x88080000，bootz 把 DTB 與 initrd 搬到 0x8F5D2000，U-Boot 本體在 0x9FF59000](../assets/bbb/bootz-memory-zh-dark.svg#gh-dark-mode-only)

```text
=> fdt addr ${fdtaddr}; fdt print / model    # "TI AM335x BeagleBone Black"
=> setenv bootargs console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlycon bringup.manual=alan
=> bootz ${loadaddr} ${rdaddr}:${rdsize} ${fdtaddr}
   Loading Ramdisk to 8f5ee000 ...
   Loading Device Tree to 8f5d2000 ...
Starting kernel ...
```

- 在 bootargs 塞一個自己的標記（`bringup.manual=alan`），kernel 的 `Kernel command line:` 印出來就能證明這次是自己的參數，不是 `bootcmd`。
- `bootz` 會把 initrd 和 DTB 再搬到 DRAM 頂端附近，真正交給 kernel 的是新位址（DTB 位址放在 `r2`）。
- 原廠 bootargs 裡的 `fsck.repair=yes`、`lpj=`、`rng_core.default_quality=` 拿掉照樣開得起來，不是必要參數。
- `setenv` 沒有 `saveenv` 就只活在這次開機，重開又回到原廠流程，可以放心亂試。

## 改走 TFTP

把 kernel / dtb / initrd 放到 PC 上的 TFTP root，U-Boot 從網路載，之後換自己 build 的 kernel 就不用再拔 SD 卡。

```text
=> setenv ipaddr 192.168.10.242; setenv serverip 192.168.10.154
=> ping ${serverip}
=> tftp ${loadaddr} zImage                  # 8.8MB, 5.8 MiB/s
=> tftp ${fdtaddr}  am335x-boneblack.dtb
=> tftp ${rdaddr}   initrd.img
=> setenv rdsize ${filesize}
=> setenv bootargs console=ttyS0,115200n8 root=/dev/mmcblk0p3 ro rootfstype=ext4 rootwait earlycon bringup.boot=tftp
=> bootz ${loadaddr} ${rdaddr}:${rdsize} ${fdtaddr}
```

PC 端沒有現成 TFTP server，用系統的 dnsmasq 只開 TFTP（`--port=0` 關掉 DNS、不開 DHCP），並用 `--interface` + `--bind-interfaces` 只綁接板子的那張網卡。

PC 這邊的準備：

```bash
mkdir -p ~/bbb-bringup/tftp && cd ~/bbb-bringup/tftp
# 先從板子把原廠的 kernel / initrd / dtb 拷回來當對照組
scp debian@192.168.10.242:/boot/vmlinuz-6.12.45-bone34 zImage
scp debian@192.168.10.242:/boot/initrd.img-6.12.45-bone34 initrd.img
scp debian@192.168.10.242:/boot/dtbs/6.12.45-bone34/am335x-boneblack.dtb .

# 有 sudo 的話直接跑 dnsmasq：
sudo dnsmasq -k --port=0 --enable-tftp --tftp-root=$PWD --tftp-secure \
     --interface=enp5s0 --bind-interfaces
# 當時沒有 sudo，改用 docker（使用者在 docker 群組）以 root 身分 chroot 回主機跑同一支 dnsmasq：
docker run -d --name bbb-tftp --net=host -v /:/host:ro debian:13-slim \
  chroot /host /usr/sbin/dnsmasq -k --port=0 --enable-tftp --tftp-root=$PWD --tftp-secure \
  --interface=enp5s0 --bind-interfaces --user=$USER --group=$USER --pid-file= --log-facility=-
ss -ulnp | grep ':69 '        # 確認綁在 192.168.10.154:69
```

之後整套「攔 U-Boot → tftp 三個檔 → 設 bootargs → bootz → 等 login」包成 [`tftpboot.sh`](https://github.com/alanhc/til/blob/main/static/bbb/tftpboot.sh)：

```bash
touch logs/break.flag
KERNEL=zImage DTB=am335x-boneblack.dtb INITRD=initrd.img ./tftpboot.sh   # 再去拔電插回
```

### 踩坑：封包有到，回覆卻從 Tailscale 出去

U-Boot `ping` 失敗、`tftp` 一直印 `T`（timeout）。在 PC 上 `tcpdump -ni enp5s0 host 192.168.10.242` 看得到板子的 ARP、ICMP echo request、TFTP RRQ，但**完全沒有回覆**。

```bash
sudo tcpdump -vv -ni enp5s0 'host 192.168.10.242'      # 同時在 U-Boot 跑 ping / tftp
```

```text
192.168.10.242 > 192.168.10.154: ICMP echo request, id 0, seq 3, length 8
192.168.10.242.3040 > 192.168.10.154.69: [no cksum] TFTP, length 38, RRQ "zImage" octet timeout 5 blksize 1468
（重送三次，PC 一個回覆都沒有）
```

先排除防火牆：`sudo nft list ruleset` 和 `sudo iptables -S INPUT` 的 INPUT 都是 accept。接著看回程：

```text
$ ip route get 192.168.10.242
192.168.10.242 dev tailscale0 table 52 src 100.x.y.z
```

tailnet 裡有節點宣告了 `192.168.10.0/24` 的 subnet route，而 Tailscale 的 policy rule（priority 5270，`lookup 52`）排在 main table（32766）前面，所以回給板子的封包全被送進 `tailscale0`。修法是加一條更前面的 rule，讓本地 LAN 走 main table：

```bash
sudo ip rule add to 192.168.10.0/24 lookup main priority 2500
```

教訓：「request 有到、reply 不見」時，先 `ip route get <對方 IP>` 看回程真正走哪張網卡，別先懷疑防火牆或板子。

## 自己 build kernel 走 TFTP 開機

```bash
sudo apt install gcc-arm-linux-gnueabihf
git -C linux worktree add --detach ../bbb-linux v7.3-rc7     # 不動原本的開發分支
cd bbb-linux
M="make ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf- O=../build-arm"
$M omap2plus_defconfig
scripts/config --file ../build-arm/.config --set-str LOCALVERSION "-bringup"
$M olddefconfig
$M -j28 zImage ti/omap/am335x-boneblack.dtb      # 28 核約 2 分鐘
```

- 新版 kernel 的 BBB dts 在 `arch/arm/boot/dts/ti/omap/`，make target 要寫 `ti/omap/am335x-boneblack.dtb`。
- `omap2plus_defconfig` 把 `MMC_OMAP_HS`、`EXT4_FS`、`SERIAL_8250_OMAP`、`TI_CPSW_SWITCHDEV` 都編成 built-in，所以**不帶 initrd** 也能直接掛 SD 上的 rootfs：`bootz ${loadaddr} - ${fdtaddr}`。SD 上的 initrd 和 `/lib/modules` 是 6.12 的，配 7.3 kernel 本來就不能用。
- 開機 log 第一行 `Linux version 7.3.0-rc7-bringup (alanhc@alanhc-14700)` 證明跑的是自己編的。

和原廠 6.12 + initrd 比：

| | 原廠 6.12 + initrd | 自編 7.3，無 initrd |
|---|---|---|
| rootfs 掛上 | 12.6 s | 4.5 s |
| 到 login | 約 56 s | 約 45 s |
| 網路 | eth0 拿到 IP | **沒 IP** |

預期中的失敗：`Failed to find module 'autofs4'`、`bb-usb-gadgets.service` 失敗（沒有 libcomposite 等 module）、`iwd.service` 失敗。都是 rootfs 裡沒有 7.3 的 modules。

不在預期內的：網路沒起來。log 裡有一行

```text
cpsw-switch 4a100000.switch end0: renamed from eth0
```

原廠 bootargs 有 `net.ifnames=0`，我手動精簡 bootargs 時拿掉了，systemd 就把網卡改名成 `end0`，而 rootfs 的網路設定寫的是 `eth0`，於是拿不到 IP。之前用原廠 kernel 手動 bootz 沒發現，是因為那時沒人去看網路有沒有起來。教訓：**刪 bootargs 參數前先確認它在管什麼**，「開得到 login」不代表沒壞東西。

補回 `net.ifnames=0` 再開一次，自編 7.3 kernel 的 log 出現 `cpsw-switch 4a100000.switch eth0: Link is Up - 100Mbps/Full`，開到 login 後 1 秒內 ping 得到。回頭翻 log 才發現，稍早用原廠 6.12 走 TFTP 開機那幾次也有 `end0: renamed from eth0`，網路其實一樣是壞的，只是當時沒去檢查。

最後 SSH 進板子確認：`uname -r` 是 `7.3.0-rc7-bringup`，`/proc/cmdline` 是自己設的那串，`eth0` 拿到 `192.168.10.242`，`systemctl --failed` 只剩 `bb-usb-gadgets` 和 `iwd`，都是缺 7.3 modules 的預期結果。

## 下一步

- 已完成的後續：[驗證 arm32 kexec 並修掉 cpsw 的 kexec bug](./bbb-kexec-cpts.md)、[寫一個最小的 platform driver](./bbb-platform-driver.md)、[SPL 原始碼導讀：從 Boot ROM 到 DRAM](./bbb-spl-source-walkthrough.md)。
- 追原廠 6.12 軟重開卡死：`systemctl reboot` 後停在 `Stopped serial-getty@ttyGS0` 就沒有輸出，網路還活著，可重現。從 `journalctl -b -1` 或 `systemd.log_level=debug` 下手。
- 刻意弄壞：拿掉 dtb、改壞 `console=`、`root=` 指錯，看各自停在哪。
- 按住 S2 開機，驗證目前的 U-Boot 2019.04 是不是來自 eMMC。
