# FRU（Field Replaceable Unit）

**FRU** 指「可現場更換的單元」（如主機板、電源、風扇背板）。每片板子上通常放一顆 **EEPROM**，以 **IPMI Platform Management FRU Information** 格式儲存製造商、產品名、序號、part number 等資料，供 BMC 讀取做資產盤點與識別。

EEPROM 掛在 I2C bus 上，透過 sysfs 存取：

```
/sys/bus/i2c/devices/13-0048
```

## 讀取 FRU EEPROM 的指令

1. 若 kernel 已綁定 `at24` 之類的 eeprom driver，會產生 `eeprom` 節點，可直接 dump 內容：

```
/sys/bus/i2c/devices/13-0048/# hexdump -C eeprom
```

其中 `13-0048` 代表 **I2C bus 13 上位址 0x48 的裝置**。

2. 若沒有 driver，也可用 `i2ctransfer` 直接對 EEPROM 做原始讀寫。下例對 bus 13、位址 0x48 先寫入 2-byte 的內部位址 `0x00 0x00`（word address），再連續讀出 128 bytes：

```
i2ctransfer -y -f 13 w2@0x48 0x00 0x00 r128
```

- `-y`：不詢問直接執行；`-f`：強制存取（即使裝置已被 driver 佔用）。
- `w2@0x48 0x00 0x00`：對 0x48 寫 2 bytes（設定讀取起始 offset）。
- `r128`：接著讀取 128 bytes。

## 解析

dump 出的 bytes 依 IPMI FRU 格式解析：開頭是 **Common Header**，內含指向 Chassis / Board / Product Info 各區塊的 offset。可用 `ipmitool fru` 或 `frutool` 直接解析成人類可讀欄位。
