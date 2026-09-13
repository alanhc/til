# MCTP

**MCTP**（Management Component Transport Protocol）是 DMTF 定義的傳輸協定，讓平台管理元件之間（BMC、NIC、SSD、retimer、GPU 等）能在各種實體匯流排上交換管理訊息。

概念：
- 屬於 DMTF **PMCI**（Platform Management Communications Infrastructure）家族。
- 提供與底層匯流排無關的定址與封包傳送層；每個端點有一個 **EID**（Endpoint ID）。
- 可跑在多種 **binding** 上：SMBus/I2C、PCIe VDM、USB、Serial、KCS。

其上承載的訊息類型：
- **PLDM**：Platform Level Data Model（sensor、FRU、firmware update 等）。
- **NC-SI over MCTP**、**SPDM**（安全驗證）等。

在 OpenBMC：
- 相關專案有 `libmctp` 與 mctp 相關 daemon，負責建立端點、路由封包，供上層 PLDM 等使用。

參考：https://www.dmtf.org/standards/pmci

相關筆記：retimer、redfish。
