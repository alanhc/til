# Server-Sent Events (SSE)

**SSE** 是一種基於 HTTP 的單向串流技術：client 開一條長連線，server 持續往下推送文字事件。Redfish 用它做事件即時推送。

特點：
- 單向（server → client），純文字，走一般 HTTP/HTTPS。
- MIME 型別 `text/event-stream`；資料格式為 `data: ...\n\n`，可帶 `event:`、`id:`。
- 比 WebSocket 簡單（免自訂協定、瀏覽器可自動重連），但只能單向。

在 Redfish：
- 對 `EventService` 的 SSE 端點開連線，即可即時收到事件串流，**免預先註冊 webhook destination**。
- 相較 push（webhook）需要一個可被 BMC 連到的 URL，SSE 適合由 client 主動拉起長連線的情境。

在 OpenBMC：
- 由 bmcweb 實作 SSE 端點。

相關筆記：event_service、redfish、event_log。
