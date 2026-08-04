# 讀電路圖（Schematic）

Datasheet 告訴你「這顆晶片怎麼用」（見 [spec](./spec.md)），**電路圖告訴你「這顆晶片在這塊板子上怎麼接」**。移植感測器時，device tree 裡要填的 bus 編號與 slave address，答案全在電路圖裡。

## I2C topology（匯流排拓樸）

第一件事是把整張板子的 I2C 樹畫出來：**哪條 bus 從 BMC 的哪個控制器出來、中間經過哪些 mux、最後掛了哪些裝置**。

```
BMC SoC
├─ I2C0 ── PSU1 (0x58) ── PSU2 (0x59)
├─ I2C5 ── PCA9548 mux (0x70)
│            ├─ ch0 ── TMP75 (0x48)  風扇板
│            ├─ ch1 ── TMP75 (0x49)  風扇板
│            └─ ch2 ── EEPROM (0x50) 風扇板 FRU
└─ I2C7 ── TMP75 (0x4c) 進風口
         ── EEPROM (0x51) 主板 FRU
```

### bus 編號的對應

**電路圖上的 `I2C7` 不保證等於 Linux 的 `/dev/i2c-7`**。Linux 的編號取決於 device tree 裡 `aliases` 節點的宣告與註冊順序。確認方式：

```bash
i2cdetect -l
```

```
i2c-7   i2c    Aspeed I2C Bus 7    I2C adapter
i2c-8   i2c    i2c-7-mux (chan_id 0)   I2C adapter
```

輸出裡的描述字串會標明它是哪個實體控制器、或是哪個 mux 的哪個 channel。**mux 底下的每個 channel 在 Linux 看來都是一條獨立的 bus，會拿到新的編號**，這是新手最容易搞混的地方——電路圖上是「I2C5 的 mux channel 0」，Linux 上卻叫 `i2c-8`。

### I2C mux

一條 I2C bus 上的位址只有 128 個（7-bit），而且同型號的晶片位址範圍有限（TMP75 只有 8 個），所以板子上會用 **mux**（如 PCA9548，8 選 1）擴展。

- Mux 本身也是一顆 I2C 裝置（常見 `0x70`–`0x77`），BMC 先寫它的暫存器選擇 channel，之後的交易才會被轉送到該 channel。
- Linux 的 `i2c-mux` 框架會自動處理切換，driver 不必自己管。
- device tree 裡 mux 節點底下每個 channel 是一個 `i2c@N` 子節點，裝置再掛在裡面。

**Mux 之後的位址可以重複**——這正是用 mux 的主要原因。上面例子裡兩顆 TMP75 若不透過 mux，就必須用不同位址。

## Address table（位址表）

板廠通常會附一張 I2C 位址表，是移植時最重要的參考。核心欄位：

| 欄位 | 說明 |
|---|---|
| Bus | 掛在哪條 I2C（要再對應成 Linux 編號） |
| Device | 晶片型號 |
| 7-bit address | Linux / device tree 使用的格式 |
| 8-bit address | 含 R/W bit 的格式，datasheet 常用 |
| Mux / Channel | 若在 mux 後面 |
| 用途 | 這顆量什麼 |

### 7-bit vs 8-bit 位址

**這是 I2C 最經典的混淆點。**

I2C 在線上實際傳的第一個 byte 是「7-bit 位址左移一位，最低位放 R/W 旗標」：

```
線上傳輸:  A6 A5 A4 A3 A2 A1 A0 R/W
```

所以同一顆裝置會有三種寫法：

| 寫法 | TMP75 (A2A1A0=100) |
|---|---|
| 7-bit address | `0x4C` |
| 8-bit write address | `0x98`（`0x4C << 1`） |
| 8-bit read address | `0x99`（`0x4C << 1 \| 1`） |

**Linux（device tree 的 `reg`、`i2cdetect`、`i2cget`）一律用 7-bit**。datasheet 與電路圖則常寫 8-bit。看到位址大於 `0x77` 就要警覺——7-bit 位址不可能超過這個範圍，八成拿到的是 8-bit 版本，除以 2 才對。

## Timing（訊號時序與電氣）

電路圖上還要確認幾件會影響能不能通訊的事：

### 上拉電阻

I2C 是 **open-drain**，SDA/SCL 必須有上拉電阻才能拉回高電位。電路圖上會標明阻值（常見 2.2kΩ / 4.7kΩ / 10kΩ）。

- **阻值太大**：上升緣太慢，高速時抓不到正確位準 → 讀值間歇性錯誤或整條 bus 讀不到。
- **阻值太小**：驅動電流過大，超出晶片規格。
- **一條 bus 只該有一組上拉**。多塊板子串接時，若每塊板子各有一組，等效阻值會變得太小。

### 速度

| 模式 | 時脈 |
|---|---|
| Standard mode | 100 kHz |
| Fast mode | 400 kHz |
| Fast mode plus | 1 MHz |

device tree 用 `clock-frequency` 設定，**必須取這條 bus 上所有裝置支援的最低值**。有一顆只支援 100kHz，整條 bus 就只能跑 100kHz。

```dts
&i2c7 {
    status = "okay";
    clock-frequency = <100000>;
};
```

### 電壓域

板上常同時存在 3.3V 與 1.8V 的裝置。跨電壓域必須有 **level shifter**（如 PCA9306），電路圖上會畫出來。若漏看而直接接，會讀不到或損壞晶片。

### 上電順序

有些裝置要等自己的電源 rail 起來才會回應 I2C。若 BMC 開機比主機電源早（正常情況就是如此），太早去讀會失敗。這也是為什麼有些感測器要等主機開機後才 probe 得到——相關的電源時序由 CPLD 控制，見 [cpld](./cpld.md)。

## 對照電路圖填 device tree

以「電路圖顯示 TMP75 掛在 I2C7、A2A1A0 接 100（位址 `0x4c`）」為例：

```dts
&i2c7 {
    status = "okay";
    clock-frequency = <100000>;

    tmp75@4c {
        compatible = "ti,tmp75";
        reg = <0x4c>;
    };
};
```

若在 mux 後面：

```dts
&i2c5 {
    status = "okay";

    i2c-switch@70 {
        compatible = "nxp,pca9548";
        reg = <0x70>;
        #address-cells = <1>;
        #size-cells = <0>;

        i2c@0 {
            #address-cells = <1>;
            #size-cells = <0>;
            reg = <0>;

            tmp75@48 {
                compatible = "ti,tmp75";
                reg = <0x48>;
            };
        };
    };
};
```

驗證流程見 [sensor_porting](./sensor_porting.md)。

## 參考

- [I2C-bus specification（NXP UM10204）](https://www.nxp.com/docs/en/user-guide/UM10204.pdf)
- [Linux kernel — i2c mux](https://docs.kernel.org/i2c/muxes/i2c-mux-gpio.html)
