# 讀 Datasheet / Spec

移植一顆新的 I2C 裝置時，手上會有兩份文件：**datasheet**（晶片廠給的規格書）與 **schematic**（板廠給的電路圖，見 [schemantic](./schemantic.md)）。Datasheet 動輒幾十上百頁，但寫 driver 真正會用到的其實只有固定幾個章節。

## 讀 datasheet 的固定順序

1. **Block Diagram** — 先建立整體概念
2. **Pin Description** — 對照電路圖確認接線
3. **Electrical Characteristics** — 供電、I2C 速度上限
4. **Device Address** — slave address 怎麼決定
5. **Register Map** — 每個暫存器的位址、預設值、bit 定義
6. **Data Format** — 讀到的原始值怎麼換算成物理量
7. **Timing** — 上電後多久才能讀、轉換要多久

## Block Diagram（方塊圖）

Datasheet 前幾頁的方塊圖，是理解整顆晶片最快的入口。它會畫出晶片內部的功能區塊與訊號流向，例如一顆溫度感測器的方塊圖通常是：

```
[溫度二極體] → [ADC] → [溫度暫存器]
                            ↓
[比較器] ← [T_HIGH/T_LOW 限值暫存器]
    ↓
  ALERT 腳                [I2C 介面] ← SDA/SCL
                              ↓
                        [位址解碼] ← A0/A1/A2
```

從方塊圖可以立刻回答幾個問題：
- 這顆晶片有幾個獨立的量測通道？（決定 driver 要註冊幾個 hwmon 檔案）
- 有沒有中斷/警報輸出腳？（決定要不要在 device tree 裡宣告 `interrupts`）
- 位址是由哪幾隻腳決定的？（決定同一條 bus 上最多能掛幾顆）

## TMP75 為例

TMP75 是 TI 的 I2C 數位溫度感測器，是 BMC 上最常見的溫度感測晶片之一，也是練習移植的標準教材。

### 位址

TMP75 的 7-bit slave address 由三隻腳 `A2/A1/A0` 決定，基底是 `1001xxx`：

| A2 | A1 | A0 | 位址 |
|---|---|---|---|
| 0 | 0 | 0 | `0x48` |
| 0 | 0 | 1 | `0x49` |
| 0 | 1 | 0 | `0x4A` |
| ... | | | ... |
| 1 | 1 | 1 | `0x4F` |

所以**一條 I2C bus 上最多掛 8 顆 TMP75**。板廠會在電路圖上標明每顆的三隻腳接高還是接低，據此填進 device tree 的 `reg`。

### 暫存器

| Pointer | 暫存器 | 說明 |
|---|---|---|
| `0x00` | Temperature | 溫度讀值（唯讀，2 byte） |
| `0x01` | Configuration | 解析度、shutdown、警報模式 |
| `0x02` | T_LOW | 警報下限 |
| `0x03` | T_HIGH | 警報上限 |

存取方式是**兩段式**：先寫一個 byte 的 Pointer Register 指定要操作哪個暫存器，再讀/寫資料。這正好對應 SMBus 的 Read Word 交易（見 [pmbus](./pmbus.md)）。

### 資料格式

溫度是 12-bit 有號數（預設解析度），放在 16-bit word 的**高位**，低 4 bit 無意義：

```
byte0 (MSB) : bit 11~4
byte1 (LSB) : bit 3~0 在高半部，低半部為 0
```

換算：**每個 LSB = 0.0625 °C**（即 1/16），負溫用二補數表示。

例如讀到 `0x2A80`：
- 取高 12 bit：`0x2A8` = 680
- `680 × 0.0625 = 42.5 °C`

**這一段是最容易寫錯的地方**——位移方向、有號數處理、LSB 權重任一個弄錯，讀出來就會是一個「數量級接近但不對」的值。

## EEPROM datasheet

FRU 資料存在 EEPROM 裡（見 [ipmi](./ipmi.md)），常見型號是 AT24C02 / AT24C64 這類 I2C EEPROM。讀 datasheet 時重點不同：

- **容量與位址寬度**：2Kbit（256 byte）以下用 1 byte 的 word address；再大就要 2 byte。**用錯位址寬度會讀到完全錯的位置**，這是最常見的錯誤。
- **Device address**：基底 `1010xxx`，即 `0x50`–`0x57`，由 A0/A1/A2 決定。所以掃描 FRU 時固定掃這個範圍。
- **Page size**：寫入時一次最多寫一頁（常見 8 / 16 / 32 byte），跨頁會 wrap around 蓋掉同頁開頭的資料。
- **Write cycle time**：寫入後需要 5ms 左右的內部寫入時間，這段期間裝置不回應 ACK。
- **Write protect 腳（WP）**：拉高則唯讀。板上常接到 GPIO，燒 FRU 前要先把它放掉。

## i2cget：手動驗證

寫 driver 之前，先用 `i2cget` 手動把值讀出來，確認「硬體通、位址對、換算公式懂了」。這一步能省下大量在 kernel 裡瞎猜的時間。

```bash
i2cget -y <bus> <chip-addr> <data-addr> <mode>
```

- `-y`：跳過確認提示。
- `<mode>`：`b` = read byte（預設）、`w` = read word（16-bit）、`c` = write byte/read byte。

```bash
# 讀 i2c-7 上 0x4c 的 TMP75 溫度暫存器（pointer 0x00），word 模式
i2cget -y 7 0x4c 0x00 w
# 0x802a
```

**注意 `i2cget -w` 的 byte order**：SMBus Read Word 規定低位 byte 先傳，但 TMP75 是高位先傳，所以讀回來的 `0x802a` 需要 byte swap 成 `0x2a80` 才是正確值。這個坑幾乎每個人都踩過一次。

搭配 `i2cdump` 可以一次把整片暫存器印出來：

```bash
i2cdump -y 7 0x50          # 傾印整顆 EEPROM，看 FRU header 對不對
```

**前提**：`i2cdetect` 顯示該位址是數字而不是 `UU`。若已經被 driver 佔用，手動存取會和 driver 搶匯流排（見 [pmbus](./pmbus.md) 的 i2cdetect 章節）。

## 從 datasheet 到 driver 的對應

| Datasheet 章節 | 對應到程式碼 |
|---|---|
| Device Address | device tree 的 `reg` |
| Register Map | driver 裡的 `#define XXX_REG 0x00` |
| Data Format | driver 的換算函式 |
| Configuration Register | `probe()` 裡的初始化寫入 |
| Timing / Conversion Time | 輪詢間隔、`msleep()` 長度 |
| ALERT / Interrupt | device tree 的 `interrupts` + `request_irq()` |

## 參考

- [TMP75 Datasheet（TI）](https://www.ti.com/product/TMP75)
- [i2c-tools 使用說明](https://www.kernel.org/doc/html/latest/i2c/i2c-tools.html)
