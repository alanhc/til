# 感測器移植（Sensor Porting）

板子上多了一顆溫度或電壓感測器，要讓它一路顯示到 Redfish / IPMI，中間要打通四層：

```
硬體（I2C 上的感測晶片）
   ↓  kernel driver + device tree
hwmon           ← kernel 把讀值以 sysfs 檔案曝露出來
   ↓  entity-manager 依 JSON 設定判斷這顆該不該存在
dbus-sensors    ← 讀 sysfs，把讀值掛上 D-Bus
   ↓
bmcweb / ipmid  ← 從 D-Bus 取值，對外提供 Redfish / IPMI
```

每一層卡住的症狀不同，先確認自己卡在哪一層，是移植最省時間的做法。

## hwmon

**hwmon**（hardware monitoring）是 Linux kernel 的硬體監控子系統。任何感測器 driver probe 成功後，都會在 sysfs 建立一個 `hwmonX` 目錄，把讀值以純文字檔案的形式曝露給 user space。

```bash
ls /sys/class/hwmon/
# hwmon0  hwmon1  hwmon2 ...

cat /sys/class/hwmon/hwmon3/name
# tmp75

ls /sys/class/hwmon/hwmon3/
# name  temp1_input  temp1_max  temp1_max_hyst  ...

cat /sys/class/hwmon/hwmon3/temp1_input
# 42500
```

檔案命名有固定慣例：

| 檔名樣式 | 意義 | 單位 |
|---|---|---|
| `temp<N>_input` | 溫度讀值 | 千分之一 °C（`42500` = 42.5°C） |
| `in<N>_input` | 電壓讀值 | mV |
| `curr<N>_input` | 電流讀值 | mA |
| `power<N>_input` | 功率讀值 | µW |
| `fan<N>_input` | 風扇轉速 | RPM |
| `<type><N>_max` / `_min` / `_crit` | 各級門檻 | 同上 |
| `<type><N>_label` | 這一路的名稱 | 字串 |

**全部用整數表示**（乘上 1000 或更多倍），避免 kernel 裡做浮點運算。

`sensors` 指令（`lm-sensors` 套件）就是把這些檔案讀出來排版顯示。

驗證順序：

```bash
i2cdetect -y 7                    # 1. 硬體在不在？看到位址數字或 UU
dmesg | grep -i tmp75             # 2. driver 有沒有 probe 成功？
ls /sys/class/hwmon/              # 3. hwmon 節點有沒有出現？
cat /sys/class/hwmon/hwmonX/temp1_input   # 4. 讀值合不合理？
```

任何一步失敗就不必往上查了：位址讀不到是硬體或 device tree 問題（見 [device_tree](./device_tree.md)），probe 失敗多半是 `compatible` 對不上，讀值離譜則通常是換算格式錯（見 [pmbus](./pmbus.md)）。

## entity-manager

**entity-manager** 是 OpenBMC 用來處理「同一份韌體要跑在多種硬體配置上」的元件。

問題背景：一台伺服器可能有 4 種不同的風扇背板、PSU 可能插 2 顆也可能插 4 顆、不同 SKU 的感測器數量不同。如果把感測器清單寫死在韌體裡，每種配置就要出一版韌體，不可維護。

entity-manager 的做法是**執行期偵測**：

1. 讀取 `/usr/share/entity-manager/configurations/` 底下的 JSON 設定檔，每個檔案描述一種硬體（一塊板子、一個模組）。
2. 每個設定檔有一段 `Probe` 條件，通常是「某個 FRU EEPROM 的 `PRODUCT_PRODUCT_NAME` 欄位等於某字串」。
3. 條件成立才把該設定檔裡宣告的感測器、風扇、GPIO 等物件建立到 D-Bus 上。

一個簡化的設定檔長這樣：

```json
{
  "Exposes": [
    {
      "Address": "0x4c",
      "Bus": 7,
      "Name": "Inlet Temp",
      "Thresholds": [
        { "Direction": "greater than", "Name": "upper critical",
          "Severity": 1, "Value": 55 }
      ],
      "Type": "TMP75"
    }
  ],
  "Name": "My Board",
  "Probe": "xyz.openbmc_project.FruDevice({'PRODUCT_PRODUCT_NAME': 'MYBOARD'})",
  "Type": "Board"
}
```

- **`Probe`**：偵測條件。這個板子的 FRU 讀出來產品名稱是 `MYBOARD` 時，底下的設定才生效。
- **`Exposes`**：這塊板子上有哪些東西。每個項目的 `Type` 對應到 dbus-sensors 裡的某個 daemon。
- **`Thresholds`**：警戒門檻，超過時會產生事件。

結果會出現在 D-Bus 的 `xyz.openbmc_project.EntityManager` 服務底下：

```bash
busctl tree xyz.openbmc_project.EntityManager
```

## FruDevice

**FruDevice** 是 entity-manager 裡的一支子程式，負責**掃描所有 I2C bus，找出 FRU EEPROM 並解析內容**。

它做的事：

1. 逐一掃描各條 I2C bus 上常見的 EEPROM 位址（`0x50`–`0x57`）。
2. 讀出內容，檢查開頭是不是合法的 IPMI FRU header（第一個 byte 是版本 `0x01`，後面是各 area 的 offset，最後有 checksum）。
3. 解析出 Board / Product / Chassis 各區的欄位，掛到 D-Bus 的 `xyz.openbmc_project.FruDevice` 服務上。

```bash
busctl tree xyz.openbmc_project.FruDevice
busctl introspect xyz.openbmc_project.FruDevice /xyz/openbmc_project/FruDevice/MYBOARD
```

**FruDevice 是整條鏈的起點**：它先認出「這是哪塊板子」，entity-manager 的 `Probe` 才有東西可以比對，後面的感測器才會被建立。所以移植新板子時，若 FRU EEPROM 沒燒好或位址不對，會出現「什麼感測器都沒有」的症狀。

FRU 資料格式細節見 [ipmi](./ipmi.md) 的 FRU 章節。

## dbus-sensors

**dbus-sensors** 是一組獨立的 daemon，每一支負責一類感測器，把讀值從 kernel（或直接從 I2C）搬到 D-Bus 上。

常見的幾支：

| daemon | 負責 |
|---|---|
| `hwmontempsensor` | 從 hwmon sysfs 讀溫度 |
| `psusensor` | PSU / PMBus 裝置的電壓電流功率 |
| `adcsensor` | SoC 內建 ADC 讀到的電壓 |
| `fansensor` | 風扇轉速與 PWM 控制 |
| `intrusionsensor` | 機殼開闔偵測 |

運作方式：

1. 監聽 entity-manager 在 D-Bus 上發出的 `InterfacesAdded` signal。
2. 看到自己負責的 `Type`（例如 `TMP75`）時，依設定裡的 bus/address 找到對應的 hwmon 路徑。
3. 定時輪詢該 sysfs 檔案，把讀值寫成 D-Bus 上的 `xyz.openbmc_project.Sensor.Value` property。
4. 讀值跨過門檻時，更新 `xyz.openbmc_project.Sensor.Threshold.*` 並發出事件。

驗證：

```bash
busctl tree xyz.openbmc_project.HwmonTempSensor
busctl get-property xyz.openbmc_project.HwmonTempSensor \
  /xyz/openbmc_project/sensors/temperature/Inlet_Temp \
  xyz.openbmc_project.Sensor.Value Value
```

上到 D-Bus 之後，`bmcweb`（Redfish）與 `ipmid`（IPMI）就會自動把它呈現出去，不需要再改這兩層。

## 移植檢查清單

1. **硬體**：`i2cdetect` 看得到位址嗎？看不到就先確認接線、bus 編號、上拉電阻（見 [schemantic](./schemantic.md)）。
2. **device tree**：節點加了嗎？`compatible` 和 driver 對得上嗎？`status = "okay"` 了嗎？
3. **driver**：`dmesg` 有沒有 probe 訊息或錯誤？kernel config 有沒有把該 driver 打開？
4. **hwmon**：`/sys/class/hwmon/` 底下有新目錄嗎？讀值合理嗎？
5. **FRU**：`busctl tree xyz.openbmc_project.FruDevice` 認得出這塊板子嗎？
6. **entity-manager**：JSON 設定檔放進去了嗎？`Probe` 條件成立嗎？
7. **dbus-sensors**：`busctl tree` 看得到感測器物件嗎？
8. **對外**：`ipmitool sdr list` 與 Redfish 的 `/redfish/v1/Chassis/.../Thermal` 有值嗎？

## 參考

- [Linux kernel — hwmon sysfs interface](https://www.kernel.org/doc/html/latest/hwmon/sysfs-interface.html)
- [OpenBMC — entity-manager](https://github.com/openbmc/entity-manager)
- [OpenBMC — dbus-sensors](https://github.com/openbmc/dbus-sensors)
