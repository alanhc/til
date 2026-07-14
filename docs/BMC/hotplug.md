# I2C Hotplug

`i2c-hotplug`

處理可熱插拔的 I2C 裝置（例如插上/拔除的模組、cable card、riser），在裝置出現/消失時動態建立或移除對應的 I2C bus 與 device node，而不需重開機。

概念：
- 由一支「偵測用」訊號（presence GPIO 或 interrupt）觸發。
- 插入時：動態把子 bus（常在 i2c mux 之後）與其上的 device 加入 kernel。
- 拔除時：移除對應 device，釋放資源。

在 OpenBMC / device tree 生態，常見做法：
- 用 `i2c-mux` + overlay 或 driver 在偵測到 presence 後掛載子 bus。
- 搭配 Entity Manager 依偵測結果動態產生該裝置的設定與 sensor。

重點是「拔除時要乾淨移除」，避免殘留 stale 的 `/sys/bus/i2c/devices/...` 造成讀取錯誤。

相關筆記：entity_manager、device_tree。
