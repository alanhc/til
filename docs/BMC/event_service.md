# Redfish EventService

Redfish 的事件訂閱機制，讓管理端不必一直輪詢（polling），改由 BMC 在事件發生時主動送出通知（push style）。

運作方式：
- 資源根：`/redfish/v1/EventService`。
- 建立訂閱：`POST` 到 `EventService/Subscriptions`，帶 `Destination`（接收 URL）、`EventTypes` / `RegistryPrefixes` / `ResourceTypes` 等過濾條件、`Protocol`（通常 `Redfish`）。
- 事件發生時，BMC 對訂閱者的 `Destination` 送出 event payload。

兩種遞送方式：
- **Push（webhook）**：POST 到訂閱時登記的目標 URL。
- **SSE（Server-Sent Events）**：client 對 SSE URL 開一條長連線，事件即時串流下來（免預先註冊 destination）。

事件來源多半對映自 phosphor-logging 的 log 與 Redfish Message Registry。

參考：https://www.dmtf.org/standards/redfish

相關筆記：sse、event_log、redfish。
