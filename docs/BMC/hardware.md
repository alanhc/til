# BMC 週邊介面

BMC 要管理整台伺服器，靠的是幾條低速匯流排與一堆 GPIO。這頁整理 BMC 開發最常碰到的介面與對應的除錯指令。

## I2C

**I2C**（Inter-Integrated Circuit）是 Philips 提出的兩線式序列匯流排，是 BMC 最主要的對外介面——溫度感測器、EEPROM、PSU、mux 幾乎全掛在 I2C 上。

### 協定要點

- **兩條線**：`SCL`（時脈，由 master driving）與 `SDA`（雙向資料）。
- **open-drain**：裝置只能把線拉低，放開時靠上拉電阻回到高電位。這是 I2C 能多主多從共用一條線的關鍵，也是為什麼一定要有上拉電阻（見 [schemantic](./schemantic.md)）。
- **定址**：7-bit slave address，理論上可掛 128 個裝置（實際上有些位址保留）。
- **一次交易的結構**：

```
START → [7-bit addr + R/W] → ACK → [data byte] → ACK → ... → STOP
```

  每個 byte 之後接收端要拉低 SDA 一個時脈當作 **ACK**。沒有 ACK 就代表該位址上沒裝置，`i2cdetect` 正是靠這點掃描。

- **repeated START**：讀暫存器時常見的模式是「先寫 pointer，不放開 bus，直接再發一次 START 轉成讀」，避免中途被其他 master 插隊。
- **clock stretching**：slave 來不及時可以把 SCL 壓住，讓 master 等待。有些控制器對這行為支援不完整，是難查的相容性問題來源。

### 常用指令

```bash
i2cdetect -l                      # 列出系統上所有 i2c bus 及其來源
i2cdetect -y 7                    # 掃描 bus 7 上有哪些裝置
```

`i2cdetect` 輸出的三種狀態（`--` 無裝置、數字 = 有裝置未被佔用、`UU` = 已被 driver 佔用）意義見 [pmbus](./pmbus.md)。

```bash
i2cget -y 7 0x4c 0x00 w           # 讀：bus 7, 裝置 0x4c, 暫存器 0x00, word 模式
i2cset -y 7 0x4c 0x01 0x60        # 寫：把 0x60 寫進暫存器 0x01
i2cdump -y 7 0x50                 # 傾印整顆裝置的暫存器/內容
```

`i2ctransfer` 則可以組出任意的交易序列，處理 `i2cget`/`i2cset` 表達不了的情況（例如 2-byte 的暫存器位址）：

```bash
# 對 0x50 寫入 2 byte 位址 0x00 0x10，然後 repeated START 讀 8 byte
i2ctransfer -y 7 w2@0x50 0x00 0x10 r8
```

語法是一連串 `w<n>@<addr>` / `r<n>@<addr>`，`w2` 表示寫 2 個 byte，`r8` 表示讀 8 個 byte（沿用前一段的位址）。

**寫入類的指令具有破壞性**——`i2cset` 打錯暫存器可能改掉 PSU 的保護門檻或關掉輸出。正式機上務必先確認自己在寫什麼。

### sysfs 路徑

```bash
ls /sys/class/i2c-dev/            # i2c-0, i2c-1, ... 對應 /dev/i2c-N
cat /sys/class/i2c-dev/i2c-7/name # 這條 bus 的來源描述

ls /sys/bus/i2c/devices/          # 已被 driver 綁定的裝置，格式 <bus>-<addr>
                                  # 例如 7-004c 就是 bus 7 上的 0x4c
```

也可以在執行期手動綁定/解除 driver，這在測試新 driver 時很方便：

```bash
echo tmp75 0x4c > /sys/bus/i2c/devices/i2c-7/new_device
echo 0x4c       > /sys/bus/i2c/devices/i2c-7/delete_device
```

## SMBus

**SMBus**（System Management Bus）是 Intel 在 I2C 之上定義的一層規範，把「可以怎麼傳」收斂成「應該怎麼傳」。

與純 I2C 的差別：

| 項目 | I2C | SMBus |
|---|---|---|
| 時脈範圍 | 無下限，上限依模式 | 10 kHz ~ 100 kHz |
| 逾時機制 | 無 | 有（SCL 被壓超過 35ms 視為逾時，裝置要自行復位） |
| 交易型態 | 自由 | 定義好的固定型態（Read Byte / Write Word / Block…） |
| 錯誤檢查 | 無 | 可選的 **PEC**（Packet Error Checking，CRC-8） |
| 電氣位準 | 依電壓域 | 有明確規定 |

實務上的重點是：**SMBus 裝置可以掛在 I2C 控制器上，但反之不一定**。Linux 用 `i2c_smbus_*()` 系列 API 表達 SMBus 交易，控制器不支援時會用純 I2C 模擬。

各交易型態與對應 API 見 [pmbus](./pmbus.md)。

## PMBus

**PMBus** 又是建立在 SMBus 之上、專門給電源裝置用的協定，定義了一整套標準 command code（讀電壓、讀電流、設保護門檻）與資料格式。詳見 [pmbus](./pmbus.md)。

三層堆疊關係：**I2C（實體）→ SMBus（交易規範）→ PMBus（電源語意）**。

## EEPROM 與 FRU

**EEPROM** 是板上的小容量非揮發記憶體（常見 AT24C02 ~ AT24C256），透過 I2C 存取，位址落在 `0x50`–`0x57`。

**FRU**（Field Replaceable Unit）則是存在這些 EEPROM 裡的**資料格式**——依 IPMI 的 FRU Information Storage Definition 規範，記錄這塊板子/模組的製造商、型號、序號、製造日期。

兩者的關係是：EEPROM 是容器，FRU 是內容。

```bash
i2cdump -y 7 0x50                 # 直接看原始內容，開頭應該是 0x01（FRU 版本）
ipmitool fru print                # 透過 BMC 解析後的結果
busctl tree xyz.openbmc_project.FruDevice   # OpenBMC 解析後掛在 D-Bus 上的結果
```

FRU 欄位定義見 [ipmi](./ipmi.md)，OpenBMC 如何用它做硬體偵測見 [sensor_porting](./sensor_porting.md)。

## SCM 與 DC-SCM

**SCM**（System Controller Module）是把 BMC 與其周邊（flash、RAM、網路 PHY、TPM）從主機板拆出來做成一張獨立子卡的設計。主機板只留高速運算相關的元件，管理功能整包插拔。

好處：
- 主機板改版時管理子系統不必跟著重新驗證。
- 同一張 SCM 可以搭配多種主機板，降低開發成本。
- 管理韌體的更新與資安邊界更清楚。

**DC-SCM**（Datacenter-ready Secure Control Module）是 OCP（Open Compute Project）把這個概念標準化的規格，定義了子卡的尺寸、連接器與訊號腳位（稱為 **DC-SCI**，Datacenter-ready Secure Control Interface）。

- **DC-SCM**：那張卡。
- **DC-SCI**：卡與主機板之間的介面規格，走的訊號包含 LPC/eSPI、I2C/I3C、PCIe、USB、UART、以及一堆電源與 reset 控制線。
- 目前有 1.0（高密度連接器）與 2.0（改用標準化的邊緣連接器）兩個世代。

對 BMC 韌體開發者的實際影響：感測器與電源控制訊號不再全部直連 BMC，有一部分要跨過 DC-SCI 到主機板側，device tree 與 GPIO 對應表會因此改變。

## GPIO

BMC 用大量 GPIO 做 presence 偵測（模組插了沒）、reset 控制、power button、LED 與各種 strap 讀取。

### 新舊兩套介面

Linux 的 GPIO 介面經歷過一次大改版：

| | 舊：sysfs | 新：character device |
|---|---|---|
| 路徑 | `/sys/class/gpio/` | `/dev/gpiochipN` |
| 定址 | 全域編號（易衝突、不穩定） | `chip 名稱 + 該 chip 內的 offset` |
| 狀態 | **已 deprecated** | 目前標準 |
| 工具 | `echo` 到 sysfs | `libgpiod`（`gpioget` 等指令） |

舊介面的問題是全域編號會隨 kernel 版本與 probe 順序改變，腳本很容易失效。**新專案一律用 libgpiod。**

### libgpiod 指令

```bash
gpiodetect                        # 列出所有 gpiochip 及其行數
# gpiochip0 [1e780000.gpio] (232 lines)

gpioinfo gpiochip0                # 列出每一行的名稱、方向、目前用途、是否被佔用
# line  35: "PWRGD_PS_PWROK"  "power-good" input active-high [used]

gpioget gpiochip0 35              # 讀一行的值
gpioset gpiochip0 35=1            # 設一行為高電位
gpiomon gpiochip0 35              # 監看邊緣觸發事件
```

`gpioinfo` 印出的名稱來自 device tree 的 `gpio-line-names` property，**板廠有把名稱填好的話，這是對照電路圖最快的方式**。

### 舊 sysfs 介面（僅供讀懂舊腳本）

```bash
echo 456 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio456/direction
echo 1   > /sys/class/gpio/gpio456/value
cat        /sys/class/gpio/gpio456/value
echo 456 > /sys/class/gpio/unexport
```

其中 `456` 是全域編號，計算方式是 `gpiochip 的 base + offset`，可從 `/sys/class/gpio/gpiochipN/base` 查到。

## devmem

`devmem`（BusyBox 內建）可以直接讀寫實體記憶體位址，用來戳 SoC 的暫存器：

```bash
devmem 0x1e780000                 # 讀 32-bit
devmem 0x1e780000 32 0x000000ff   # 寫：位址 寬度 值
```

用途是**繞過 driver 直接驗證硬體**——懷疑 driver 沒把某個暫存器設對時，用 `devmem` 讀出來比對 SoC datasheet 即可確認。

**這是最危險的一個工具**：寫錯位址可能瞬間當機、關掉電源、或破壞正在運作的週邊。正式環境只用來讀，不要寫。

需要 kernel 有開 `CONFIG_DEVMEM`，且部分平台會因 `CONFIG_STRICT_DEVMEM` 限制可存取範圍。

## ADC

BMC SoC 內建 **ADC**（類比數位轉換器），把板上分壓後的電壓轉成數位值，用來監控各路電源 rail。

- 電路圖上會看到 rail 經過分壓電阻後接到 BMC 的 ADC 腳，**所以讀到的值要乘上分壓比才是真實電壓**。這個比例寫在 device tree 或 entity-manager 的設定裡。
- Linux 端由 **IIO**（Industrial I/O）子系統管理，OpenBMC 的 `adcsensor` 再把它接到 D-Bus。

```bash
ls /sys/bus/iio/devices/iio:device0/
cat /sys/bus/iio/devices/iio:device0/in_voltage0_raw
cat /sys/bus/iio/devices/iio:device0/in_voltage_scale
# 真實電壓 = raw × scale × 分壓比
```

## SPI

**SPI**（Serial Peripheral Interface）是四線式全雙工匯流排，速度遠高於 I2C。BMC 上主要用途是**接韌體 flash**，另外也用來存取 TPM 或存取主機的 BIOS flash。

四條線：`SCLK`（時脈）、`MOSI`（master 送出）、`MISO`（master 收入）、`CS`（晶片選擇，每個裝置一條）。沒有位址概念——**靠 CS 選擇裝置**，所以掛幾顆就要幾條 CS。

### Single / Dual / Quad / Octal

為了提高吞吐量，SPI flash 演化出多線模式，差別在**同時用幾條資料線傳輸**：

| 模式 | 資料線數 | 說明 |
|---|---|---|
| **Single** | 1 | 傳統模式，MOSI 送、MISO 收，各司其職 |
| **Dual** | 2 | MOSI/MISO 兩條都改成雙向資料線，頻寬 ×2 |
| **Quad** | 4 | 再借用 `WP#` 與 `HOLD#` 兩隻腳當資料線，頻寬 ×4 |
| **Octal** | 8 | 需要 8 條資料線的封裝，多見於 OSPI / xSPI 裝置 |

實務要點：
- 多線模式下，**指令與位址通常仍走 single 線，只有資料階段是多線**（不同的 opcode 決定，例如 `0x6B` = Quad Output Fast Read）。
- Quad 模式要先寫 flash 的 status register 打開 **QE bit** 才會生效。
- 開 Quad 之後 `WP#`/`HOLD#` 就不再是保護腳，硬體上要確認沒有其他電路在驅動它們。
- device tree 用 `spi-tx-bus-width` / `spi-rx-bus-width` 宣告要用幾線：

```dts
flash@0 {
    compatible = "jedec,spi-nor";
    reg = <0>;
    spi-max-frequency = <50000000>;
    spi-rx-bus-width = <4>;
};
```

BMC 開機時 SoC 的 boot ROM 通常只用 single 模式讀 u-boot（最保守可靠），u-boot 起來後才切到 quad 加速後續載入。相關的 flash 分割與更新見 [flash](./flash.md)。

## 參考

- [I2C-bus specification（NXP UM10204）](https://www.nxp.com/docs/en/user-guide/UM10204.pdf)
- [SMBus Specification](http://www.smbus.org/specs/)
- [OCP DC-SCM Specification](https://www.opencompute.org/documents/ocp-dc-scm-spec-rev-1-0-pdf)
- [libgpiod](https://git.kernel.org/pub/scm/libs/libgpiod/libgpiod.git/about/)
- [Linux kernel — IIO subsystem](https://docs.kernel.org/driver-api/iio/index.html)
