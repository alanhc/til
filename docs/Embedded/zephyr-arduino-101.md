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

如果像我一樣不小心把 `0AB6` 換成了 WinUSB，到裝置管理員對「GENUINO 101」選「解除安裝裝置」並勾選刪除驅動，就會恢復成內建的序列埠驅動。

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

## 參考

- [Zephyr v1.14 的 arduino_101 board 目錄與文件](https://github.com/zephyrproject-rtos/zephyr/tree/v1.14-branch/boards/x86/arduino_101)
- [Zephyr SDK 0.10.3 release](https://github.com/zephyrproject-rtos/sdk-ng/releases/tag/v0.10.3)
- [dfu-util](https://dfu-util.sourceforge.net/)、[Zadig](https://zadig.akeo.ie)
