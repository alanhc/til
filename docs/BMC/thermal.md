# Thermal Management

BMC 的散熱管理：讀溫度感測器，依策略調整風扇轉速，在「不過熱」與「不吵/省電」之間取平衡。

概念：
- **thermal zone**：一個散熱分區，把一組熱源 sensor 與負責散熱的風扇綁在一起。
- **margin vs absolute**：控制常用「距離上限還有多少度」(thermal margin) 而非絕對溫度，便於跨不同元件統一調控。
- **failsafe**：sensor 異常/逾時就把風扇拉到安全高轉速。

在 OpenBMC：
- 實際的閉迴路由 **phosphor-pid-control** 執行（PID / Stepwise），設定多由 Entity Manager 動態提供。
- Linux kernel 亦有自己的 thermal framework（`/sys/class/thermal/thermal_zoneN/`，trip point、cooling device），視平台是否採用。

對外：
- 透過 Redfish `Chassis/.../Thermal`（或新版 `ThermalSubsystem`）呈現溫度與風扇狀態。

相關筆記：pid_control、hwmon、redfish。
