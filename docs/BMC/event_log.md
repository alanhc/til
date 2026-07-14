# Event Log

OpenBMC 的事件/錯誤紀錄機制，把硬體與系統事件記成結構化 log，供本機除錯與遠端（Redfish）查詢。

phosphor-logging：
- 核心服務，提供建立與儲存 log 的 D-Bus 介面（`xyz.openbmc_project.Logging`）。
- log entry 有 `Severity`、`Message`、時間戳與 `AdditionalData`（key=value 附加資訊）。
- 開發者用 `lg2` / `elog` API 產生 log；嚴重事件可帶 callout（指出故障零件）。

對外呈現：
- 透過 Redfish **LogService**（`/redfish/v1/Systems/system/LogServices/EventLog/Entries`）讀取。
- 也可映射成 IPMI SEL（見 sel_logger 筆記）。

常見操作：
- `busctl` 查詢 `/xyz/openbmc_project/logging/entry/*`。
- journal（`journalctl`）看底層 daemon log。

參考：https://github.com/openbmc/phosphor-logging

相關筆記：sel_logger、event_service、redfish。
