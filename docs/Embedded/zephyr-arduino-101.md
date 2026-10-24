# 在 Arduino 101 上跑 Zephyr（Windows + WSL）

Arduino 101（海外版叫 Genuino 101）用的是 Intel Curie 模組，裡面是 Quark SE C1000：一顆 32 MHz 的 x86（Quark）核心加一顆 ARC EM 感測器子系統核心，兩顆共用記憶體、同時運作。這篇記錄在 Windows 11 上用 WSL 編譯 Zephyr、從 Windows 用 DFU 燒進板子、讓板上 LED 閃起來的完整步驟。

## 先講結論：踩坑重點

- **只能用 Zephyr 1.14 LTS**。`arduino_101`／`arduino_101_sss` 兩個 board 在 v1.14 還在，v2.0.0 就整個移除了（Quark SE 支援一起拿掉）。工具鏈搭配同時期的 **Zephyr SDK 0.10.3**（含 `i586-zephyr-elfiamcu` 與 ARC 的 GCC 8.3），版本對齊最省事。
- **原廠 bootloader 不用動**。Zephyr 從 1.4 起就不再用 QMSI bootloader，原廠 boot ROM 直接支援 DFU 燒錄。
- **DFU 模式只有 5 秒**。按 MASTER_RESET 後板子會以另一個 USB ID 出現約 5 秒，dfu-util 必須在這段時間內開始寫入。
- **Windows 上最卡的是驅動**。DFU 模式的 USB ID 預設沒有驅動，要用 Zadig 裝 WinUSB，而且很容易裝錯裝置（見下文）。
- **console 不走 USB**。Zephyr 的 `printk` 從 pin 0/1 的 UART 輸出（115200），要看 log 得另接 USB 轉 TTL 線。所以第一支程式選 `blinky`，用 LED 確認有跑起來最直接。

## 兩個 USB ID

| 模式 | VID:PID | Windows 看到的 | 用途 |
|---|---|---|---|
| 一般執行 | `8087:0AB6` | USB 序列裝置（COM port） | 原廠／Arduino 韌體的 CDC 序列埠 |
| DFU | `8087:0ABA` | `GENUINO 101`（沒有驅動時狀態是 Error） | 燒錄，按 reset 後只出現約 5 秒 |

## 一、在 WSL 建置環境（不需要 sudo）

WSL 的 Ubuntu 24.04 內建 Python 3.12 與 CMake 3.28，對 2019 年的 Zephyr 1.14 都太新。這裡用 [uv](https://docs.astral.sh/uv/) 另外裝一個獨立的 Python 3.8 venv，CMake 用 pip 版本鎖在 3.20 以下，全程不需要 sudo。

```bash
mkdir -p ~/zephyr-a101 && cd ~/zephyr-a101

# uv：拿來裝 Python 3.8 與建 venv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH=~/.local/bin:$PATH

# Zephyr 1.14 LTS（只要 zephyr 本體，arduino_101 用不到額外的 west module）
git clone --depth 1 --branch v1.14-branch https://github.com/zephyrproject-rtos/zephyr.git

uv venv --python 3.8 .venv
. .venv/bin/activate
uv pip install -r zephyr/scripts/requirements.txt ninja "cmake<3.20"

# Zephyr SDK 0.10.3：含 i586 IAMCU 與 ARC 工具鏈，以及 dtc 等 host 工具
wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.10.3/zephyr-sdk-0.10.3-setup.run
chmod +x zephyr-sdk-0.10.3-setup.run
./zephyr-sdk-0.10.3-setup.run -- -d ~/zephyr-sdk-0.10.3 -y
```

### 缺 gperf

第一次 `cmake` 會停在 `Unable to find gperf`。沒有 sudo 的話，可以只下載 `.deb` 解開來用：

```bash
mkdir -p ~/zephyr-a101/hosttools && cd ~/zephyr-a101/hosttools
apt-get download gperf
dpkg-deb -x gperf_*.deb root
export PATH=~/zephyr-a101/hosttools/root/usr/bin:$PATH
```

## 二、編譯 blinky（只跑 x86 核心）

```bash
cd ~/zephyr-a101
. .venv/bin/activate
export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
export ZEPHYR_SDK_INSTALL_DIR=~/zephyr-sdk-0.10.3
export PATH=~/zephyr-a101/hosttools/root/usr/bin:$PATH
. zephyr/zephyr-env.sh

cmake -GNinja -B build-blinky -S zephyr/samples/basic/blinky \
  -DBOARD=arduino_101 -DCONFIG_ARC_INIT=n
ninja -C build-blinky
```

- `BOARD=arduino_101` 是 x86 核心；ARC 核心的 board 叫 `arduino_101_sss`，要另外編、另外燒。
- `CONFIG_ARC_INIT=n`：不讓 x86 去喚醒 ARC 核心。只用 x86 時這樣最單純，ARC 那邊原本燒了什麼都不會被跑起來。
- 板子的 device tree 有定義 `led0`（`gpio0` pin 8），所以 `blinky` 不用改就能跑。
- 產物是 `build-blinky/zephyr/zephyr.bin`，只有約 11 KB（flash 144 KB、SRAM 52 KB 都只用了 7% 左右）。

編譯時會看到 `HAS_SPI_DW ... has direct dependencies SPI with value n` 的 Kconfig 警告和 `distutils` 的 DeprecationWarning，都可以忽略。

## 三、Windows 端：dfu-util 與 WinUSB 驅動

dfu-util 直接用官方的 Windows binary（[dfu-util 0.11](https://dfu-util.sourceforge.net/releases/)，解開後用 `win64/dfu-util.exe`）。

接著要幫 **`8087:0ABA`** 裝 WinUSB 驅動，用 [Zadig](https://zadig.akeo.ie)：

1. **Device → Create New Device**，名稱隨意（例如 `GENUINO 101 DFU`）。
2. USB ID 填 `8087`、`0ABA`，第三格留空。
3. 驅動選 **WinUSB**，按 **Install Driver**。

用 Create New Device 的好處是板子不必剛好在那 5 秒內出現，Zadig 會把驅動預先放進系統，下次 `0ABA` 出現就會自動套用。

**實際踩到的坑**：Zadig 的 Create New Device 會預填下拉選單目前選到的裝置。板子平常插著時，選到的是 `8087:0AB6`（序列埠），一不注意就會把驅動裝到 `0AB6`。我前兩次都是這樣：第一次裝成 USB Serial (CDC)，第二次裝成 WinUSB，結果 COM port 不見、DFU 還是沒驅動。**按 Install 前務必確認第二格是 `0ABA`**。

確認驅動有沒有裝對：

```powershell
pnputil /enum-drivers | Select-String -Context 2,6 'libwdi'
```

`Signer Name` 那行要出現 `USB\VID_8087&PID_0ABA`。

如果像我一樣不小心把 `0AB6` 換成了 WinUSB，到裝置管理員對「GENUINO 101」選「解除安裝裝置」並勾選刪除驅動，就會恢復成內建的序列埠驅動。不過燒了 Zephyr 之後，平常模式本來就不會有序列埠了，原因見後面「原廠 bootloader 拆解」那一節。

## 四、燒錄

按一下板子上的 **MASTER_RESET**，5 秒內執行：

```powershell
dfu-util.exe -d 8087:0aba -a x86_app -D zephyr.bin
```

- `-a x86_app` 是 x86 核心的 application 分區；ARC 的 image 寫到 `-a sensor_core`。
- 出現 `Warning: Invalid DFU suffix signature` 可以忽略，原廠 bootloader 不檢查 suffix。
- 看到 `Download done.` 和 `Done!` 就是寫入成功。

5 秒很難靠手動抓準，可以用 PowerShell 輪詢，等裝置出現就立刻燒：

```powershell
$dfu = ".\dfu-util.exe"
while (-not ((& $dfu -l 2>&1 | Out-String) -match '8087:0aba')) { Start-Sleep -Milliseconds 150 }
& $dfu -d 8087:0aba -a x86_app -D zephyr.bin
```

燒完後 **LED 沒有馬上閃**，等了一會兒才開始每秒閃一次。我的理解是 bootloader 要等 DFU 視窗結束才會跳進 application，所以燒完先別急著判定失敗。

## 五、原廠 bootloader 拆解

燒完之後我好奇原廠 bootloader 到底做了什麼，於是用 DFU 的 **upload（`-U`，從板子讀回電腦，不會寫入）**把每個分區讀出來，再對照 Arduino 官方上傳工具 [arduino101load](https://github.com/arduino/arduino101load) 的原始碼與 Zephyr 1.14 的 board 設定。

### 它是誰

原廠 bootloader 是一支跑在 **x86（Quark）端**的 DFU bootloader，放在內部 flash 最前面。整塊板子有三顆晶片：x86、ARC，以及負責藍牙的 **Nordic nRF51822**。三顆的韌體都經由它的 DFU 介面更新，藍牙那顆是 bootloader 透過 UART 轉送寫入的。

### 9 個 DFU 分區

`dfu-util -l` 會列出 9 個 alt setting：

| alt | 名稱 | 讀回大小 | 讀回來看到的內容 |
|---|---|---|---|
| 0 | `x86_rom` | 8 KB | 開頭是 `$FA!` 標頭與一段出廠資料；推測是 Quark SE 的 OTP ROM 區（未找到官方文件確認） |
| 1 | `x86_boot` | 60 KB | **bootloader 本體**：標頭 `$B!N`、版本 ID `ATP1LAKBLR-1541C5640`，以及 `do_dfu_upload`／`do_dfu_download` 等 DFU 狀態機字串 |
| 2 | `x86_app` | 144 KB | 開頭和燒進去的 `zephyr.bin` 逐位元組相同；後面還殘留原本 Intel x86 韌體的字串——DFU 只覆寫映像實際的長度 |
| 3–6 | `config`／`panic`／`events`／`logs` | — | 這次讀回的內容和其他分區重複，**不可信**（見下方「upload 計數器」）。`logs` 讀到約 2 MB，與板上 W25Q16 SPI flash 的容量相符，但僅是推論 |
| 7 | `sensor_core` | 152 KB | ARC 端的程式，也就是 Arduino sketch |
| 8 | `ble_core` | 讀到 64 KB 時逾時 | nRF51822 的藍牙韌體，開頭與 Arduino 官方的 `ble_core.bin` 一致；經 UART 轉送所以很慢 |

### 內部 flash 位址

用 Zephyr 編出來的 ELF（`readelf -l`）與 board 的 Kconfig 交叉確認：

```
0x40000000  x86_boot     bootloader
0x40010000  x86_app      x86 程式（144 KB），入口在 +0x30 = 0x40010030
0x40034000  sensor_core  ARC 程式（CONFIG_SS_RESET_VECTOR 指向這裡）
```

**入口在 +0x30** 是這個 bootloader 的約定：Zephyr 的 commit 寫著它「expects the text section at +0x30 from the physical load address」，所以 arduino_101 預設 `CONFIG_TEXT_SECTION_OFFSET=0x30`。從板子讀回的 `x86_app` 也看得到：最前面 0x30 bytes 全是 `66 90`（NOP 填充），之後才是第一條真正的指令。

### 原本的 Arduino 是怎麼分工的

讀 `arduino101load` 的原始碼可以看到：

- **Arduino sketch 跑在 ARC 上**，上傳時用 `dfu-util -d 8087:0ABA -D sketch.bin --alt 7 -R` 寫進 `sensor_core`。
- **x86 跑的是 Intel 的 RTOS 韌體**（`quark.bin`，版本字串 `firmware_1.8.0_arduino101`），負責 USB 序列埠、藍牙控制，以及 IDE 用 1200 baud「觸碰」序列埠讓板子重開進 DFU。
- IDE 的 **Burn Bootloader**（programmer 選 *Arduino/Genuino 101 Firmware Updater*）**其實不會燒 bootloader**：它把 `quark.bin` 寫進 alt 2、`ble_core.bin` 寫進 alt 8。上傳前，工具也會讀回這兩個分區固定 offset 的版本字串，用來判斷要不要更新。

所以把 Zephyr 燒進 `x86_app`，等於**換掉了 Intel 那套 x86 韌體**。這會帶來兩個後果：

- 平常模式下板子不再提供 USB 序列埠（blinky 沒有 USB 功能）。
- IDE 的 1200 baud 自動重開失效，之後只能手動按 reset 進 DFU。

想回到 Arduino，就在 IDE 選 Firmware Updater 執行 Burn Bootloader，提示時按 MASTER_RESET，把 `quark.bin` 寫回去即可。bootloader 本身從頭到尾都沒被動到。

### 三個坑

- **upload 計數器不會隨 alt 歸零**。`arduino101load` 每次讀分區前都會先跑一次 `-U <tmp> --alt N -K 1`，原始碼註解寫著「reset DFU interface counter」。我連續讀 9 個分區時沒做這一步，所以後面幾個分區讀回來的內容和前面的重複。要可靠地讀，每個 alt 都要先歸零再讀。
- **不要寫 `x86_boot`／`x86_rom`**。Arduino 官方明確警告燒錯 bootloader 會變磚，只能靠 JTAG 救。若要還原原廠 boot ROM，Zephyr 文件指向 Intel 的 Flashpack Utility。
- **版本 ID 的格式**：bootloader 的 `ATP1LAKBLR-1541C5640` 與藍牙韌體的 `ATP1BLE00R-1631C4439` 格式相同。我猜中間的 `1541`、`1631` 是「年份加週數」的 build 日期碼，但沒有找到來源。

## 參考

- [Zephyr v1.14 的 arduino_101 board 目錄與文件](https://github.com/zephyrproject-rtos/zephyr/tree/v1.14-branch/boards/x86/arduino_101)
- [Zephyr commit：arduino 101: make factory bootloader config the default](https://github.com/zephyrproject-rtos/zephyr/commit/ecf96d2cfaf2d188bf14b61bc2610b3b41484d79)（+0x30 offset 與 flash 範圍的來源）
- [arduino/arduino101load](https://github.com/arduino/arduino101load)（sketch 寫 alt 7、Firmware Updater 寫 alt 2 與 alt 8 的原始碼）、[arduino/ArduinoCore-arc32](https://github.com/arduino/ArduinoCore-arc32)（`upload.use_1200bps_touch`、Firmware Updater programmer）
- [Arduino blog：Intel releases the Arduino 101 firmware source code](https://blog.arduino.cc/2016/04/21/intel-releases-the-arduino-101-firmware-source-code/)（燒錯 bootloader 需 JTAG 救的警告）
- [Zephyr SDK 0.10.3 release](https://github.com/zephyrproject-rtos/sdk-ng/releases/tag/v0.10.3)
- [dfu-util](https://dfu-util.sourceforge.net/)、[Zadig](https://zadig.akeo.ie)
