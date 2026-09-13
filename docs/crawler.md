# 網路爬蟲 (Web Crawler / Scraper)

爬蟲工具與相關概念筆記。

## 概念

- **Crawler**：自動走訪連結、抓取多個頁面（廣度優先探索網站）。
- **Scraper**：從頁面中擷取結構化資料（例如商品價格、標題）。
- 需注意 `robots.txt`、rate limit 與網站服務條款，避免對目標網站造成負擔。
- 動態網站（JS 渲染）通常需要 headless browser（Playwright、Puppeteer、Selenium）。

## Apify

[Apify](https://apify.com/) 是雲端爬蟲 / 自動化平台：

- 以 **Actor**（可重複執行的雲端程式）為單位執行爬蟲任務。
- 內建大量現成 Actor（Google Maps、Instagram、電商網站等），可直接使用。
- 提供 proxy、排程、資料儲存與 API，方便串接後續流程。
- 開源的 [Crawlee](https://crawlee.dev/) 函式庫即由 Apify 維護。
