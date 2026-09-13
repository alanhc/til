# PMBus

**PMBus**（Power Management Bus）是電源管理裝置的標準通訊協定，建立在 [SMBus](./hardware.md) 之上（SMBus 又建立在 I2C 之上）。伺服器上的 PSU、VRM、hot-swap controller、eFuse 都用它，讓 BMC 可以讀出每一路電源的電壓、電流、功率與溫度，也能設定過壓/過流保護門檻、開關輸出。

三層關係：

```
PMBus   ← 定義了電源專用的 command code 與資料格式
  ↑
SMBus   ← 定義了 read byte / write word 等交易型態、逾時、PEC
  ↑
I2C     ← 定義了實體訊號、start/stop、ack
```

## P = IV：為什麼要在意讀值單位

`P = I × V`（功率 = 電流 × 電壓）是看 PMBus 資料時最基本的檢查工具。PMBus 裝置通常同時提供 `READ_VIN`、`READ_IIN`、`READ_PIN`（輸入側）與 `READ_VOUT`、`READ_IOUT`、`READ_POUT`（輸出側）。

實務上用途有三個：

1. **驗證換算有沒有寫錯**：把讀到的 V 和 I 相乘，若和裝置回報的 P 差很多，多半是 Linear/Direct 換算係數搞錯了。
2. **算轉換效率**：`efficiency = POUT / PIN`，一顆正常的 PSU 大概在 90% 上下。若算出超過 100%，一定是換算錯了。
3. **推估未提供的值**：有些裝置只給 V 和 I，功率要自己乘。

## 資料格式：Linear vs Direct

PMBus 的讀值不是直接的十進位數字，必須經過換算。有兩種格式，**同一顆晶片的不同 command 可能用不同格式，一定要查 datasheet**。

### Linear（線性格式）

以 2 的冪次表示，不需要每顆晶片各自的係數，最常見。

**Linear11**：一個 16-bit word 拆成兩段，都是**二補數有號數**。

```
bit  15 14 13 12 11 | 10 9 8 7 6 5 4 3 2 1 0
     [   N (5bit) ] | [      Y (11bit)      ]
```

$$
\text{Value} = Y \times 2^{N}
$$

`N` 是指數（-16 ~ 15），`Y` 是尾數（-1024 ~ 1023）。用於 `READ_IOUT`、`READ_TEMPERATURE_1`、`READ_PIN` 等大多數讀值。

**Linear16（ULINEAR16）**：專門給 `READ_VOUT` 用。這次整個 16-bit word 都是**無號**尾數 `Y`，指數 `N` 另外放在 `VOUT_MODE`（command `0x20`）這個暫存器的低 5 bit（有號）：

$$
\text{Voltage} = Y \times 2^{N}
$$

分開的原因是電壓需要更高解析度，把 16 bit 全給尾數。

### Direct（直接格式）

用每顆晶片自訂的三個係數做線性換算，精度較高但每顆的係數都不同：

$$
X = \frac{1}{m}\left( Y \times 10^{-R} - b \right)
$$

其中 `X` 是真實物理量、`Y` 是讀到的原始值，`m`（斜率）、`b`（偏移）、`R`（次方）由 datasheet 給定，也可以透過 `COEFFICIENTS`（command `0x30`）向裝置查詢。TI 的一些 hot-swap controller、部分 PSU 用這個格式。

**移植 driver 時最常見的 bug 就是格式判斷錯誤**——用 Linear 去解 Direct 的值，會得到一個看起來「有點像但就是不對」的數字。

## SMBus 交易型態

PMBus 指令都是透過底層的 SMBus 交易送出的，Linux 的 `i2c` 子系統對應以下 API：

| 交易 | 說明 | Linux API |
|---|---|---|
| **Read Byte** | 送出 command code，讀回 1 byte | `i2c_smbus_read_byte_data()` |
| **Read Word** | 送出 command code，讀回 2 byte（低位在前） | `i2c_smbus_read_word_data()` |
| **Write Byte** | 送出 command code + 1 byte | `i2c_smbus_write_byte_data()` |
| **Write Word** | 送出 command code + 2 byte | `i2c_smbus_write_word_data()` |
| **Block Read/Write** | 變動長度，第一個 byte 是長度 | `i2c_smbus_read_block_data()` |

命名邏輯很單純：**Read/Write 是方向，Byte/Word 是資料長度（1 或 2 個 byte）**。

**大多數 PMBus 讀值是 Read Word**（因為 Linear11/Linear16 都是 16-bit），狀態類的 `STATUS_BYTE` 則是 Read Byte，設定類的用 Write。

在 kernel PMBus core 之上，driver 呼叫的是包裝過的版本：

```c
int pmbus_read_word_data(struct i2c_client *client, u8 page, u8 phase, u8 reg);
int pmbus_read_byte_data(struct i2c_client *client, int page, u8 reg);
int pmbus_write_word_data(struct i2c_client *client, u8 page, u8 reg, u16 word);
```

多出來的 `page` 參數是 PMBus 的**分頁機制**：一顆多路輸出的晶片（例如雙輸出 VRM）用 `PAGE`（command `0x00`）切換目前操作的是哪一路，各路有各自的 `READ_VOUT` 等暫存器。

命令列上手動測試可以用 `i2cget`（見 [hardware](./hardware.md)）：

```bash
# 讀 i2c-7 上位址 0x63 的裝置，command 0x8b (READ_VOUT)，word 模式
i2cget -y 7 0x63 0x8b w
```

## 常用 command code

| Code | 名稱 | 說明 |
|---|---|---|
| `0x00` | `PAGE` | 切換操作的輸出路數 |
| `0x01` | `OPERATION` | 開關輸出 |
| `0x20` | `VOUT_MODE` | 回報 VOUT 用哪種格式與指數 |
| `0x78` | `STATUS_BYTE` | 綜合狀態旗標 |
| `0x79` | `STATUS_WORD` | 同上，16-bit 版本 |
| `0x88` | `READ_VIN` | 輸入電壓 |
| `0x89` | `READ_IIN` | 輸入電流 |
| `0x8B` | `READ_VOUT` | 輸出電壓 |
| `0x8C` | `READ_IOUT` | 輸出電流 |
| `0x8D` | `READ_TEMPERATURE_1` | 溫度 |
| `0x96` | `READ_POUT` | 輸出功率 |
| `0x97` | `READ_PIN` | 輸入功率 |
| `0x99` | `MFR_ID` | 製造商識別（block read） |

## probe：driver 如何認出裝置

PMBus driver 的 `probe()` 被呼叫的時機，是 [device tree](./device_tree.md) 中節點的 `compatible` 與 driver 的 `of_match_table` 配對成功時。probe 裡典型會做：

1. 確認裝置真的在（讀 `MFR_ID` 或某個已知暫存器，值不對就回 `-ENODEV`）。
2. 讀 `VOUT_MODE` 決定電壓的換算指數。
3. 填好 `struct pmbus_driver_info`：告訴 PMBus core 這顆晶片有幾個 page、支援哪些讀值、各自用什麼格式，必要時掛上自訂的 `read_word_data()` callback 處理非標準行為。
4. 呼叫 `pmbus_do_probe()`，由 core 去建立 hwmon 介面。

成功之後 user space 就會多出 `/sys/class/hwmon/hwmonX/` 下的一組檔案，`sensors` 指令也讀得到。整條資料流是：

```
使用者（sensors / cat sysfs）
   ↓
hwmon 子系統
   ↓
PMBus core（負責 Linear/Direct 換算）
   ↓
<driver>_read_word_data(client, page, reg)
   ↓
SMBus / I2C 實際傳輸 command code
```

## i2cdetect：確認裝置與 driver 的佔用狀況

```bash
i2cdetect -y 7
```

輸出中每個位址會顯示三種狀態之一：

| 顯示 | 意義 |
|---|---|
| `--` | 該位址沒有回應，沒有裝置 |
| 十六進位數字（如 `63`） | 有裝置回應，且**目前沒有 driver 佔用** |
| `UU` | 有 driver 已經綁定這個位址，`i2cdetect` 跳過不去打擾它 |

這個區分很重要：

- 移植 driver 時，看到 `63` 代表硬體有接對但 driver 沒 probe 起來 → 去查 `dmesg` 和 `compatible`。
- 看到 `UU` 代表 driver 已經接管 → 這時**不要**再用 `i2cget` 去戳同一個位址，會和 driver 搶匯流排造成讀值錯亂。

## 參考

- [PMBus Specification（SMBus/PMBus 官方）](https://pmbus.org/specification-archives/)
- [Linux kernel — PMBus core](https://www.kernel.org/doc/html/latest/hwmon/pmbus-core.html)
- [Power Management Bus（Wikipedia）](https://en.wikipedia.org/wiki/Power_Management_Bus)
