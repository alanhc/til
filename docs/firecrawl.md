# Firecrawl

[Firecrawl](https://www.firecrawl.dev/) 是一個把網站轉成 LLM 可用資料的爬取工具。

## 特點

- 輸入一個 URL，就能回傳乾淨的 **markdown** 或結構化資料，省去自己處理 HTML。
- 會自動處理 JS 渲染、跳過雜訊（廣告、導覽列）。
- 主要功能：
  - `scrape`：抓取單一頁面。
  - `crawl`：遞迴走訪整個網站的所有子頁面。
  - `map`：快速列出網站上所有 URL。
  - `extract`：用 LLM 依 schema 擷取結構化資料。
- 提供 API、SDK（Python / Node）與 CLI，方便串進 RAG / agent pipeline。

https://www.firecrawl.dev/blog/introducing-firecrawl-skill-and-cli
