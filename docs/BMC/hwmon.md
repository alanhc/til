# hwmon

`driver define`

Linux 的 **hwmon**（hardware monitoring）子系統，統一介面暴露溫度、電壓、電流、風扇轉速、功率等 sensor 讀值到 user space。

sysfs 介面：
- 節點位於 `/sys/class/hwmon/hwmonN/`。
- 命名慣例：`temp1_input`、`in0_input`、`fan1_input`、`curr1_input`、`power1_input`（值多為毫度/毫伏/毫安）。
- `*_max`、`*_crit`、`*_label` 等提供門檻與名稱。

driver define：
- 感測晶片（如 tmp75、adm1275、pmbus 裝置）的 kernel driver 會註冊成 hwmon device，並定義它提供哪些 channel/屬性。
- 綁定方式常見於 device tree 的 `compatible`，或 i2c board info。

在 OpenBMC：
- `phosphor-hwmon` 讀 hwmon sysfs，把讀值轉成 D-Bus 上的 `xyz.openbmc_project.Sensor.Value`，供 Redfish/IPMI/風扇控制使用。

相關筆記：sensor_porting、pmbus、pid_control。
