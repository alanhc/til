# pyftdi / FT2232H / PCA9555 筆記

用 PC 當主機去控制硬體低階匯流排（SPI / I²C / JTAG / GPIO）時常見的一組東西。

---

## FT2232H — USB 橋接晶片

FTDI 出的 USB 2.0 High-Speed 橋接晶片。

- 內含**兩個獨立通道**（Channel A / B），每個通道可各自設定成 UART、FIFO 或 **MPSSE** 模式。
- **MPSSE**（Multi-Protocol Synchronous Serial Engine）是重點：用硬體產生 SPI / I²C / JTAG 的時脈與訊號，所以一顆晶片就能讓 PC 直接當 SPI master、I²C master 或 JTAG debugger。
- 沒用到的腳位可以當 GPIO（每通道 16 支：ADBUS/ACBUS、BDBUS/BCBUS）。
- 常見載板：FT2232H Mini Module、FT2232H Breakout、以及很多 bring-up 用的 JTAG debugger／燒錄器底層都是它。

### 電氣特性

| 項目 | 值 |
|---|---|
| I/O 電壓 | 3.3V LVTTL（input 可耐 5V） |
| MPSSE 時脈 | 最高 30 MHz（SPI）；I²C 實務上 100k / 400k |
| USB | 2.0 High-Speed, 480 Mbps |
| 通道數 | 2（A / B 獨立） |

---

## pyftdi — Python 驅動層

純 Python 的 FTDI 驅動（走 libusb / pyusb，不需要 FTDI 的 D2XX），把 MPSSE 包成好用的 API。

```bash
pip install pyftdi
```

### I²C

```python
from pyftdi.i2c import I2cController

i2c = I2cController()
i2c.configure('ftdi://ftdi:2232h/1')   # URL: vendor:product/channel

dev = i2c.get_port(0x20)               # PCA9555 位址
dev.write([0x06, 0x00, 0x00])          # config reg：P0/P1 全部設為 output
dev.write([0x02, 0xFF, 0x00])          # output port0 = 0xFF, port1 = 0x00

val = dev.exchange([0x00], 2)          # 讀 input port 0/1
```

### SPI

```python
from pyftdi.spi import SpiController

spi = SpiController()
spi.configure('ftdi://ftdi:2232h/1')
slave = spi.get_port(cs=0, freq=10e6, mode=0)
resp = slave.exchange([0x9F], 3)       # e.g. SPI NOR JEDEC ID
```

### GPIO

```python
from pyftdi.gpio import GpioAsyncController

gpio = GpioAsyncController()
gpio.configure('ftdi://ftdi:2232h/2', direction=0x0F)
gpio.write(0x05)
```

### 其他

- `pyftdi.serialext`：把 UART 通道掛成 pyserial 裝置（`serial.serial_for_url('ftdi://...')`）。
- `python -m pyftdi.ftdi`（或 `ftdi_urls.py`）可列出目前接上的 FTDI 裝置 URL。

---

## PCA9555 — I²C GPIO Expander

NXP 的 16-bit I²C GPIO expander（TI 也有 pin-compatible 的 TCA9555）。

### 暫存器

| Cmd byte | 名稱 | 說明 |
|---|---|---|
| 0x00 / 0x01 | Input Port 0 / 1 | 讀腳位實際電位（唯讀） |
| 0x02 / 0x03 | Output Port 0 / 1 | 寫輸出值 |
| 0x04 / 0x05 | Polarity Inversion 0 / 1 | input 讀值反相 |
| 0x06 / 0x07 | Configuration 0 / 1 | 1 = input（預設）, 0 = output |

### 特性

- 兩個 8-bit port（P0.0–P0.7、P1.0–P1.7），共 16 支 GPIO。
- 位址腳 A0–A2 決定位址 **0x20–0x27**，一條 bus 最多掛 8 顆 = 128 支 GPIO。
- **INT#** 腳：input 有變化時拉低（open-drain），省得一直 polling；讀 input port 後自動清除。
- 輸出為 push-pull（相對地，PCF8574 是 quasi-bidirectional，行為不同，別搞混）。

---

## 組合起來

```
PC ──USB──> FT2232H ──I²C──> PCA9555 ──> 16x GPIO ──> DUT
     pyftdi   (MPSSE)          (0x20)              (reset / power_en /
                                                    boot strap / key sim)
```

典型用途是**自動化測試治具 / board farm**：用軟體撥 reset、power enable、boot mode strap、按鍵模擬這類訊號，不用人手插拔跳線。CI 就能自動 reboot、進 fastboot、切 download mode。

---

## 踩雷筆記

- **`ftdi_sio` 搶裝置**：Linux 上 kernel 會自動綁定 FTDI 為 `/dev/ttyUSBx`，pyftdi 就開不起來。先 unbind：
  ```bash
  sudo modprobe -r ftdi_sio   # 或針對單一介面 unbind
  ```
  長期解法是加 udev rule（設定 `MODE="0666"` 並讓非 root 可存取），pyftdi 文件有現成範例。
- **I²C 上拉電阻**：FT2232H 沒有內建，SDA/SCL 要外接（3.3V, 2.2k–4.7k 視 bus capacitance）。
- **MPSSE I²C 是半模擬的**：clock stretching 支援不佳，時序不精準；速度要求高或 slave 會 stretch 的場合要留意。
- **電壓域**：FT2232H 輸出 3.3V。DUT 若是 1.8V 域必須加 level shifter。
- **通道編號**：pyftdi URL 的 channel 是 1-based（`/1` = Channel A、`/2` = Channel B）。
- **Windows**：需要用 Zadig 把介面驅動換成 libusb-win32 / WinUSB，否則 pyftdi 抓不到。

---

## 參考

- [pyftdi 文件](https://eblot.github.io/pyftdi/)
- [FT2232H datasheet (FTDI)](https://ftdichip.com/products/ft2232hq/)
- [AN_108 — Command Processor for MPSSE](https://ftdichip.com/document/application-notes/)
- [PCA9555 datasheet (NXP)](https://www.nxp.com/products/PCA9555)
