# phosphor-sel-logger

OpenBMC 服務，負責產生並維護 **IPMI SEL**（System Event Log）——BMC 記錄硬體事件（感測器越限、power 事件等）的標準紀錄，供 `ipmitool sel` 這類傳統工具查詢。

運作方式：
- 監聽 D-Bus 上的事件（如 sensor threshold 觸發、其他服務發出的 SEL add 請求）。
- 把事件寫成 IPMI SEL entry（含 sensor type、event data、時間戳）。
- 對外經 IPMI SEL 指令存取；OpenBMC 也可把事件對映到 Redfish LogService。

常見操作：

```bash
ipmitool sel list
ipmitool sel clear
```

- D-Bus 上 SEL entry 約在 `/xyz/openbmc_project/Logging/IPMI` 相關路徑。

與 phosphor-logging 的差異：後者是通用的 OpenBMC event/error log，sel-logger 專責產生「IPMI 相容」的 SEL 格式。

參考：https://github.com/openbmc/phosphor-sel-logger

相關筆記：event_log、ipmi、redfish。
