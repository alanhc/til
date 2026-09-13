# Redfish

**Redfish** 是 DMTF 定義的 RESTful 管理介面標準，用 HTTPS + JSON 管理伺服器硬體，目標是取代老舊、二進位、難擴充的 **IPMI**。

特點：
- 資源導向：以 URI 表示硬體資源，標準動詞 `GET/POST/PATCH/DELETE`。
- JSON payload，並用 schema 定義每種資源的欄位。
- 從根 `GET /redfish/v1/` 開始，透過 hyperlink 逐層瀏覽。

常見資源：
- `/redfish/v1/Systems`：主機（電源狀態、開關機、boot override）。
- `/redfish/v1/Chassis`：機殼、感測器、電源/散熱。
- `/redfish/v1/Managers`：BMC 本身。
- `LogServices`、`UpdateService`、`EventService`、`AccountService`。

在 OpenBMC：
- 由 **bmcweb** 實作 Redfish server，把 D-Bus 上的資料對映成 Redfish 資源。

參考：https://www.dmtf.org/standards/redfish

相關筆記：event_service、sse、event_log、mctp。
