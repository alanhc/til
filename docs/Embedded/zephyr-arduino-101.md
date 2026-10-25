# 在 Arduino 101 上跑 Zephyr（Windows + WSL）

Arduino 101（海外版叫 Genuino 101）用的是 Intel Curie 模組，裡面是 Quark SE C1000：一顆 32 MHz 的 x86（Quark）核心加一顆 ARC EM 感測器子系統核心，兩顆共用記憶體、同時運作。這篇記錄在 Windows 11 上用 WSL 編譯 Zephyr、從 Windows 用 DFU 燒進板子、讓板上 LED 閃起來的完整步驟，接著拆解原廠 bootloader，最後讓 Zephyr 的藍牙（BLE）跑起來，從電腦連線控制 LED。

## 先講結論：踩坑重點

- **只能用 Zephyr 1.14 LTS**。`arduino_101`／`arduino_101_sss` 兩個 board 在 v1.14 還在，v2.0.0 就整個移除了（Quark SE 支援一起拿掉）。工具鏈搭配同時期的 **Zephyr SDK 0.10.3**（含 `i586-zephyr-elfiamcu` 與 ARC 的 GCC 8.3），版本對齊最省事。
- **原廠 bootloader 不用動**。Zephyr 從 1.4 起就不再用 QMSI bootloader，原廠 boot ROM 直接支援 DFU 燒錄。
- **DFU 模式只有 5 秒**。按 MASTER_RESET 後板子會以另一個 USB ID 出現約 5 秒，dfu-util 必須在這段時間內開始寫入。
- **Windows 上最卡的是驅動**。DFU 模式的 USB ID 預設沒有驅動，要用 Zadig 裝 WinUSB，而且很容易裝錯裝置（見下文）。
- **console 預設不走 USB**。Zephyr 的 `printk` 從 pin 0/1 的 UART 輸出（115200），要看 log 得另接 USB 轉 TTL 線。所以第一支程式選 `blinky`，用 LED 確認有跑起來最直接。真的需要 log 時，可以把 console 改成 USB CDC 序列埠（見第六節）。
- **藍牙要兩顆晶片一起改**。nRF51 要換成 Zephyr 的 `hci_uart`，x86 跑藍牙協定堆疊。照官方預設（1 Mbaud、RTS/CTS 流量控制）完全不會動，要改成 **250 kbaud + 只用 RTS 的半邊流量控制**，並拿掉 `CONFIG_BT_NRF51_PM`（見第六節）。

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

## 六、藍牙（BLE）：讓 Zephyr 驅動板上的 nRF51

目標是一支 x86 端的 BLE peripheral：廣播名稱 `A101 Zephyr`，提供一個自訂 GATT 服務，裡面有兩個特性——**LED**（可讀寫，寫 `01` 開燈、`00` 關燈）和 **Counter**（可讀、可訂閱通知，每秒加 1）。從 Windows 連上去讀寫，最後成功。

### 架構

| 晶片 | 跑什麼 | 燒到 |
|---|---|---|
| nRF51822 | Zephyr `samples/bluetooth/hci_uart`（board `curie_ble`），只當藍牙**控制器** | alt `ble_core` |
| x86（Quark） | 應用程式 + Zephyr 藍牙**協定堆疊**（host），用 H:4 透過 UART0 驅動 nRF51 | alt `x86_app` |

官方文件的做法就是這樣：nRF51 原廠的藍牙韌體 Zephyr 不支援，要換成 `hci_uart`。換掉之後 Arduino 的 CurieBLE 就不能用了，要回 Arduino 得用 IDE 的 Firmware Updater 把 `ble_core.bin` 燒回去。

### 照官方預設會卡在哪

照文件編好 `hci_uart`（`curie_ble`）和一支 peripheral，燒進去之後，**藍牙初始化永遠不會完成**：`bt_enable()` 的回呼一直沒被呼叫，也沒有廣播。從這裡一路往下拆，總共疊了四個問題：

| 問題 | 症狀 | 怎麼確認的 | 解法 |
|---|---|---|---|
| **1. nRF51 的 CTS 永遠不成立** | 開著 RTS/CTS 時 nRF51 完全不回應 | 見下方「診斷手法」 | 只用 RTS 那半邊的流量控制 |
| **2. 沒有流量控制時，1 Mbaud 會掉資料** | 前幾個 HCI 指令正常，68 bytes 的 Read Supported Commands 回應少了最後 8 bytes，初始化以 `-35`（`ENOTSUP`）失敗 | USB log | 兩邊降到 250 kbaud |
| **3. nRF51 reset 後立刻送 HCI 指令** | 第一個 HCI_Reset 被正在重開的 nRF51 丟掉，主機等不到 Command Complete，之後所有指令卡住 | 和診斷程式比對時序 | 拿掉 `CONFIG_BT_NRF51_PM` |
| **4. 連線後 x86 → nRF51 掉 byte** | 能廣播、能被連上，但 ATT 往返兩次就卡住，對方約 25 秒後斷線（reason `0x13`） | USB log 的時間點 | 就是問題 1 的「半邊流量控制」：保護 nRF51 只有 6 bytes 的接收 FIFO |

### 診斷手法：用 LED 和 UART 一步一步切

x86 端沒有 console 可看，所以先寫了幾支**不用藍牙協定堆疊**的小程式，結果用 LED 閃幾下回報：

1. **讀回 `ble_core`**：用 DFU upload 讀回 nRF51 的 flash，和 `hci_uart` 映像逐位元組比對，確定韌體真的寫進去了。
2. **`hci_probe`（x86）**：照驅動的方式 reset nRF51，直接對 UART0 送 `01 03 0C 00`（HCI_Reset），看有沒有收到 `04 0E 04 01 03 0C 00`。
   - 開著流量控制：x86 送得出去，但完全沒有回應。
   - 兩邊都關掉流量控制：**收到正確的 Command Complete**。
3. **`uart_beacon`（nRF51）+ `uart_listen`（x86）**：nRF51 一開機就不停送 `A101`、x86 只聽。收得到，代表 nRF51 有在跑、nRF51 → x86 的線路是好的。
4. **把 nRF51 的 RTS/CTS 對調再測**：x86 反而送不出去了。

綜合 2 和 4，兩條握手線的狀況是：

| 線 | nRF51 腳位 | 狀況 |
|---|---|---|
| nRF51 RTS → x86 CTS（nRF51 叫 x86 停） | pin 12 | ✅ 正常 |
| x86 RTS → nRF51 CTS（x86 叫 nRF51 停） | pin 10 | ❌ nRF51 一直看不到「可以送」 |

我只能確認現象，無法確定是模組上的接線，還是 x86 那支 RTS 的設定問題。腳位定義在 v1.9.0 和 v1.14 完全一樣，而 Zephyr 的 GitHub issue 裡，維護者在 v1.10 前後確實用 Arduino 101 連成功過，所以不排除跟板子批次或原廠 bootloader 版本有關。

### 開 USB log：Quark 的 USB 可以當 console

到後來 LED 已經不夠用了。Zephyr 1.14 的 `samples/subsys/usb/console` 在 `arduino_101` 上可用，所以做了一個除錯版，把 console 和藍牙 log 都改走 USB CDC 序列埠：

```ini
# usb_debug.conf（只用在除錯版）
CONFIG_USB=y
CONFIG_USB_DEVICE_STACK=y
CONFIG_USB_UART_CONSOLE=y
CONFIG_UART_INTERRUPT_DRIVEN=y
CONFIG_UART_LINE_CTRL=y
CONFIG_UART_CONSOLE_ON_DEV_NAME="CDC_ACM_0"
# Windows 的 usbser 要 IAD 才認得 CDC，1.14 只有 composite 模式會送 IAD
CONFIG_USB_COMPOSITE_DEVICE=y
CONFIG_LOG=y
CONFIG_BT_DEBUG_LOG=y
CONFIG_BT_DEBUG_HCI_CORE=y
CONFIG_BT_DEBUG_HCI_DRIVER=y
```

```dts
/* usb_debug.overlay */
/ {
	chosen {
		zephyr,console = &usb_cdc;
	};
};
```

兩個要注意的地方：

- **少了 `CONFIG_USB_COMPOSITE_DEVICE`，Windows 上序列埠會顯示錯誤（Code 10）**：資料介面被當成獨立的裝置。改完描述元後最好換一個 PID，避免 Windows 沿用快取的舊設定。
- **程式要等序列埠被打開（DTR）才開始初始化藍牙**，不然開機那段 log 會漏掉。反過來說，錄 log 的程式一關，log 就會塞住、連帶卡住藍牙執行緒，所以除錯版只在錄 log 時用。

有了 log，問題 2 和問題 4 都是直接從 HCI 封包的內容和時間點看出來的。例如一個 13 bytes 的 ATT 回應送出 5 秒後，nRF51 才回報完成，剛好是下一個指令的 byte 進來把它「湊滿」的時候。

### 最後的設定

**nRF51（`hci_uart` 改版）**：把 `samples/bluetooth/hci_uart` 複製一份，`prj.conf` 沿用範例的 `nrf5.conf`，另外加三樣東西：

```ini
# prj.conf 追加
CONFIG_CLOCK_CONTROL_NRF_K32SRC_RC=y      # 不依賴模組上有沒有 32 kHz 石英
CONFIG_CLOCK_CONTROL_NRF_K32SRC_500PPM=y
# CONFIG_UART_0_NRF_FLOW_CONTROL=y 保留
```

```dts
/* curie_ble.overlay */
&uart0 {
	current-speed = <250000>;
};
```

```c
/* src/curie_cts.c：UART 驅動在 PRE_KERNEL_1 把 CTS 設成浮接輸入，
 * 這裡在 POST_KERNEL 改成下拉 = 永遠成立，只留下 RTS 那半邊 */
static int curie_cts_pulldown(struct device *unused)
{
	ARG_UNUSED(unused);
	nrf_gpio_cfg_input(DT_NORDIC_NRF_UART_0_CTS_PIN, NRF_GPIO_PIN_PULLDOWN);
	return 0;
}
SYS_INIT(curie_cts_pulldown, POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEVICE);
```

**x86（應用程式）**：

```ini
# prj.conf
CONFIG_ARC_INIT=n
CONFIG_GPIO=y
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_DEVICE_NAME="A101 Zephyr"
CONFIG_BT_H4=y
# 不開 CONFIG_BT_NRF51_PM；UART0 的硬體流量控制維持板子預設（開）
```

```dts
/* arduino_101.overlay：放在應用程式目錄，Zephyr 1.14 會自動套用 */
&uart0 {
	current-speed = <250000>;
};
```

250 kbaud 的好處是兩邊都沒有誤差：x86 是 32 MHz ÷ (16 × 250000) = 8，nRF51 也原生支援 250000。每個 byte 是 40 µs，x86 的 16 bytes FIFO 能容忍 640 µs 的中斷延遲，沒有保護的那個方向（nRF51 → x86）也撐得住。

GATT 服務本身照 1.14 的寫法：`BT_GATT_PRIMARY_SERVICE` + `BT_GATT_CHARACTERISTIC` + `BT_GATT_CCC` 組成 `bt_gatt_attr` 陣列，再用 `bt_gatt_service_register()` 註冊；通知用 `bt_gatt_notify()`，傳入的是特性的宣告屬性。

### 從 Windows 測試的坑

手邊沒有手機的話，可以直接用 PowerShell 5.1 呼叫 WinRT 的 BLE API 測，但有一堆坑：

- **位址每次開機都會變**：控制器沒有公開位址，也沒開 settings 子系統，Zephyr 每次開機都產生新的靜態隨機位址（最高兩個 bit 為 1）。要用名稱或服務 UUID 找。
- **Windows 會主動斷線**：沒配對過的裝置，如果沒有用 `GattSession` 設 `MaintainConnection = true`，幾秒後就被 Windows 斷線（HCI reason `0x13`），進行中的呼叫會回 `0x800704C7`（已取消）。
- **讀取預設會拿快取**：`ReadValueAsync()` 要傳 `BluetoothCacheMode.Uncached`，不然計數器永遠是同一個值。
- **PowerShell 5.1 的 WinRT 投射很殘缺**：
  - 集合的 `Count` 和索引拿不到，要用 `ForEach-Object` 走訪。
  - 回傳的 `IBuffer` 不能直接丟給 `DataReader`，要用反射呼叫 `WindowsRuntimeBufferExtensions.ToArray(IBuffer)`。
  - 寫入要用 `AsBuffer(byte[])` 產生 buffer。
- **PowerShell 的小陷阱**：
  - 變數不分大小寫，`$led` 和參數 `$Led` 是同一個。
  - `Rd` 是 `Remove-Item` 的別名，不要拿來當函式名稱。

最後的測試結果：連上、找到服務、讀到 LED 和計數器，寫入 `0`／`1` 板上 LED 跟著熄滅／亮起，計數器 3 秒後加 3。

## 參考

- [Zephyr v1.14 的 arduino_101 board 目錄與文件](https://github.com/zephyrproject-rtos/zephyr/tree/v1.14-branch/boards/x86/arduino_101)
- [Zephyr commit：arduino 101: make factory bootloader config the default](https://github.com/zephyrproject-rtos/zephyr/commit/ecf96d2cfaf2d188bf14b61bc2610b3b41484d79)（+0x30 offset 與 flash 範圍的來源）
- [arduino/arduino101load](https://github.com/arduino/arduino101load)（sketch 寫 alt 7、Firmware Updater 寫 alt 2 與 alt 8 的原始碼）、[arduino/ArduinoCore-arc32](https://github.com/arduino/ArduinoCore-arc32)（`upload.use_1200bps_touch`、Firmware Updater programmer）
- [Arduino blog：Intel releases the Arduino 101 firmware source code](https://blog.arduino.cc/2016/04/21/intel-releases-the-arduino-101-firmware-source-code/)（燒錯 bootloader 需 JTAG 救的警告）
- [Zephyr SDK 0.10.3 release](https://github.com/zephyrproject-rtos/sdk-ng/releases/tag/v0.10.3)
- [dfu-util](https://dfu-util.sourceforge.net/)、[Zadig](https://zadig.akeo.ie)
- [Zephyr issue #5145：Arduino 101 上 peripheral CSC 連線失敗](https://github.com/zephyrproject-rtos/zephyr/issues/5145)（維護者在 v1.10 前後用 Arduino 101 連成功的紀錄）、[issue #3812：Arduino 101 藍牙 init failed (err -19)](https://github.com/zephyrproject-rtos/zephyr/issues/3812)
- [Zephyr HCI UART 範例說明](https://docs.zephyrproject.org/latest/samples/bluetooth/hci_uart/README.html)（預設 1 Mbaud + RTS/CTS）
