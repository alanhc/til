# AI Agent 相關專案

收集的一些 agent 生態系專案，依用途分類。

## Agent 定義與工作流

- **[agency-agents](https://github.com/msitarzewski/agency-agents)** — 一套 200+ 個「專業角色」agent 定義檔的集合，涵蓋前端工程師、資安審查、社群經營等各種職能。每個 agent 是一份 Markdown，描述它的專長、工作流程與產出標準。可以直接複製到 Claude Code、Cursor、GitHub Copilot、Gemini CLI 等工具裡使用，等於一次組出一整個虛擬團隊。

- **[impeccable](https://github.com/pbakaus/impeccable)** — 專門提升 AI coding agent **前端設計品質**的指引系統。內含 23 個指令、59 條偵測規則，並支援瀏覽器即時迭代。核心價值是避免 AI 產出「一看就是樣板」的介面：先建立設計脈絡，再用 `/impeccable audit`、`/impeccable polish`、`/impeccable critique` 這類指令引導 agent 做出更有意圖的設計決策。可安裝到 Claude Code、Cursor、Copilot 等多種工具。

## Agent 記憶與脈絡管理

- **[OpenViking](https://github.com/volcengine/OpenViking)**（位元組跳動火山引擎）— 開源的 agent **context database**。它的設計取徑很特別：不用向量資料庫，而是把記憶、資源、技能全部組織成一個虛擬檔案系統（`viking://` 協定），讓 agent 用 `ls`、`tree`、`find` 這種熟悉的方式瀏覽自己的脈絡。搭配 L0（摘要）/ L1（概覽）/ L2（細節）的分層載入來節省 token，同時保有檢索過程的可觀察性。以 Rust 撰寫，支援 Claude Code、Codex、LangChain 等框架。

## 多 agent 模擬

- **[MiroFish](https://github.com/666ghj/MiroFish)** — 基於多 agent 技術的「預測引擎」。使用者用自然語言餵入種子資料（新聞、報告、故事），系統會生成一個由智慧 agent 組成的數位世界，透過成千上萬次的 agent 互動與模擬產生預測結果。應用場景包含輿情預測、金融預測與創意情境推演。後端 Python、前端 JavaScript。

## 從頭理解 LLM

- **[nanochat](https://github.com/karpathy/nanochat)**（Andrej Karpathy）— 極簡、可讀、可改的 LLM 訓練框架，目標是在**單一 GPU node** 上跑完整條 pipeline：tokenization → pretraining → finetuning → evaluation → inference。號稱約 100 美元的運算成本就能訓練出 GPT-2 等級的模型。用單一個 `depth` 參數收斂大部分超參數設定，降低入門門檻。想搞懂 agent 底下那顆模型到底怎麼來的，這是最好的教材。
