# PID Control (phosphor-pid-control)

OpenBMC 的風扇/散熱閉迴路控制 daemon，依感測器讀值動態調整風扇 PWM，避免過熱也避免全速空轉。

核心概念：
- **PID zone**：一個散熱分區，包含一組輸入 sensor 與輸出風扇。
- **控制迴路**：
  - `temp -> margin/setpoint`（thermal PID）：讀溫度算出目標。
  - `fan -> pwm`（fan PID）：以風扇轉速 (RPM) 為回授做閉迴路。
  - 也支援 `Stepwise`（查表式）非 PID 控制。
- **failsafe**：sensor 失聯或超時時，風扇拉到安全高轉速。
- 參數：`proportionalCoeff`(P)、`integralCoeff`(I)、`derivativeCoeff`(D)、`setpoint`、`samplePeriod`。

設定來源：
- 傳統用 `/etc/phosphor-pid-control/config.json`。
- 現多改由 Entity Manager 產生的 D-Bus 設定動態載入（`Pid`, `Pid.Zone`, `Stepwise`, `Fan` 等 config type）。

參考：https://github.com/openbmc/phosphor-pid-control

相關筆記：thermal、hwmon、entity_manager。
