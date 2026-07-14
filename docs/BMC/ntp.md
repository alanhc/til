# NTP 時間同步

BMC 需要正確時間，讓 event log、SEL、憑證有效期等有一致的時間戳。透過 **NTP** 與外部時間伺服器同步。

元件：
- **systemd-timesyncd**：輕量 SNTP client，底層負責向 NTP server 對時（開/關、指定 server）。
- **phosphor-time-manager**：OpenBMC 服務，管理時間模式與對外設定介面（D-Bus `xyz.openbmc_project.Time.*`）。

時間模式（TimeSyncMethod）：
- **NTP**：由 NTP server 決定時間（timesyncd 生效）。
- **Manual**：手動設定時間（停用 NTP）。

設定方式：
- Redfish：`Managers/bmc/NetworkProtocol` 設定 NTP server、開關 NTP。
- 也可用 `busctl` 改 Time manager 屬性，或 IPMI 相容介面。

注意：BMC 常無 RTC 電池或會漂移，NTP 對 log 對時很重要。

參考：https://github.com/openbmc/phosphor-time-manager

相關筆記：network、event_log。
