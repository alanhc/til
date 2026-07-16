---
title: AI / Agent 文章索引
sidebar_label: AI 系列索引
sidebar_position: 2
---

# AI / Agent 文章索引

本頁整理知識庫中所有 AI、LLM、Agent 相關筆記，依主題分類：從 Claude Code 生態、MCP 開發、本機推論，到 Agent 安全架構與組織導入的觀點文章。
名詞定義請參考 [AI 名詞表](ai_glossary.md)。

---

## 一、總覽與觀點文章

| 文章 | 內容 |
|---|---|
| [AI 生態總覽](../AI.md) | 速記與對照表：OpenAI／Google／Anthropic／Perplexity 在 Chat、POC、Browser、筆記工具、地端 IDE、CLI、Agent framework 各格的對應產品；另一張表比較三家的 Agent framework（MCP + Agents SDK vs ADK/Vertex vs Claude Agent SDK）、Web IDE、本地 IDE、CLI 與筆記工具；含 AI 簡史（2020 GPT-3 → 2022 ChatGPT → 2023 GPT-4）與 self-host 選型（JAN vs LM Studio、ollama vs vLLM） |
| [為什麼公司推不動 Agentic AI](../ai-why-companies-struggle-agentic-ai.md) | **長篇觀點文**：導入 agentic AI 卡住的四道組織的牆——①管理層覺得不好管（能力—部署驗證落差）②出事沒人負責（accountability gap，用委託代理問題與眾手問題解釋「責任蒸發」）③同事怕被取代（STARA awareness、配合但不投入）④agent 拆解角色後責任滑到 code review。附 security vs RD 斷層、四個務實抓手，與「agent 不是病因、是顯影劑」的結論。19 筆文獻含逐項查證狀態 |
| [Why Companies Can't Get Agentic AI Off the Ground (EN)](../ai-why-companies-struggle-agentic-ai-en.md) | 上篇的英文版 |
| [AI 時代的「基本功」](../ai_basic_knowledge.md) | **觀點文**：拆解「工具會變、基本功最重要」這句話——基本功是事後追認的（組語、手動記憶體管理都當過基本功）、這句話無法被證偽所以只提供安慰；但「什麼都會過時」也是逃避，因為技術棧各層半衰期不均勻。結論：AI 讓「驗證輸出對不對」的能力空前值錢。附 Deming & Noray、GitHub Copilot 生產力研究等文獻 |
| [AI 整理（Excalidraw）](../ai整理.excalidraw.md) | Obsidian Excalidraw 畫布檔，內容為壓縮後的繪圖資料，純文字閱讀看不到內容，需用 Excalidraw 檢視 |

---

## 二、Claude Code 生態與 Agent Skills

| 文章 | 內容 |
|---|---|
| [Claude Code](../claude_code.md) | 官方 agentic CLI 簡介，含 Chrome 整合（透過瀏覽器擴充讓 agent 導覽、點擊、讀取頁面） |
| [Claude Code 安裝](../claude_install.md) | `npm install -g @anthropic-ai/claude-code` 全域安裝、Node.js 需求、首次啟動登入流程，並提醒以官方 setup 文件為準 |
| [Claude Code Channels](../claude_channel.md) | 佔位頁，目前只有一句說明與官方 channels 文件連結 |
| [Claude](../claude.md) | 佔位頁，目前只有一張截圖，無文字內容 |
| [Claude UI](../claude_ui.md) | 佔位頁，兩張 Claude 使用介面截圖 |
| [用 Ollama 跑 Claude Code](../claude_use_ollama.md) | `ollama launch claude` 的模型選單實錄：`minimax-m2.5:cloud`、`glm-5:cloud`、`kimi-k2.5:cloud` 等雲端模型，以及 `glm-4.7-flash`（~25GB）、`qwen3:8b`（~11GB）等本地模型 |
| [Claude Skills](../claude_skills.md) | 連結收藏：`npx skills add anthropics/claude-plugins-official --skill skill-creator`、`/plugin marketplace add anthropics/skills`，以及 anthropics/skills repo、官方 Skill 建置指南 PDF 與中文教學 |
| [Agent Skills](../skills.md) | 概念說明：skill 是可重複使用的技能模組，安裝後可在對話中自動或手動觸發；示範 `npx skills add vercel-labs/agent-skills` |
| [Agent Skills（skills.sh）](../vercel_skills.md) | 佔位頁：Vercel 的 skills.sh 平台（瀏覽／安裝／分享 skill），一條連結加一張截圖 |

---

## 三、MCP 與 Agent 開發

| 文章 | 內容 |
|---|---|
| [MCP](../mcp.md) | **實作主線**：用 python-sdk 的 FastMCP 寫 MCP server（`@mcp.tool()` / `@mcp.resource()` / `@mcp.prompt()` 三種裝飾器範例）、`uv run --with mcp main.py` 執行、用 `cloudflared tunnel` 暴露到公網，再到 ChatGPT 的「連接器」設定填入 `/mcp` 網址並直接呼叫 |
| [使用自訂義的 GPTs](../gpts.md) | 完整實作：用 FastAPI + yt-dlp 寫一支抓 YouTube 字幕的 backend（含 VTT 解析與 5 秒內字幕合併邏輯）、`cloudflared tunnel` 對外、在 GPTs 用 `openapi.json` 匯入動作，最後撰寫 prompt 測試 |
| [Agent 相關收藏](../agent.md) | 佔位頁，目前只有五條 GitHub 連結（agency-agents、MiroFish、impeccable、OpenViking、nanochat），無說明文字 |
| [遠端 Playwright MCP 控制本機 Chrome](../claude_remote_playwright_mcp.md) | **深入版**：從遠端 Linux 控制 Windows 上 Chrome 的完整方案。原理是 Chrome DevTools Protocol（`--remote-debugging-port=9222` 會開一個 HTTP + WebSocket 伺服器），Playwright 用 `connectOverCDP()` 連既有瀏覽器；四步驟教學（獨立 `--user-data-dir` 啟 Chrome → `ssh -N -R` 反向隧道 → Linux 端 curl 驗證 → Playwright MCP 用 `--cdp-endpoint`），並強調 CDP 完全沒有驗證機制，絕不能把 9222 直接暴露公網 |
| [AI 測試（Playwright Agent）](../ai_testing.md) | 極簡速記：Playwright agent 的三個角色 Planner／Generator／Healer，以及 Playwright MCP Server（瀏覽器自動化）與 Playwright Test MCP Server（測試工作流程）的分工 |
| [Firecrawl](../firecrawl.md) | 把網站轉成 LLM 可用資料的爬取工具：輸入 URL 回傳乾淨 markdown、自動處理 JS 渲染與雜訊；四個主要功能 `scrape`／`crawl`／`map`／`extract`，可串進 RAG / agent pipeline |
| [aisuite](../deeplearning_ai_aisuite.md) | Andrew Ng 團隊開源的 Python 套件，用 OpenAI 風格的統一介面呼叫多家供應商，以 `provider:model` 字串（如 `openai:gpt-4o`）切換模型，附最小範例 |

---

## 四、本機推論與自架服務

| 文章 | 內容 |
|---|---|
| [本機 LLM 推論工具](../ai_inference.md) | **選型主線**：lm studio（桌面 GUI）／ollama（CLI + API server，適合當服務）／jan（開源 Apache license）三者比較，底層都是 llama.cpp（負責 GGUF 量化模型的 CPU/GPU 推論）。一句話選型：要 GUI 選 lm studio 或 jan、要開源選 jan、要給多人或程式呼叫選 ollama |
| [Jan.ai](../ai_jan_ai.md) | Apache 2.0 授權、可完全離線的本機 LLM 桌面應用，底層 llama.cpp，可下載 GGUF 模型也能連遠端 API 供應商；定位類似 LM Studio 但開源 |
| [讓 Ollama 對區網／VPN 開放](../ollama_export_in_vpn.md) | `export OLLAMA_HOST=0.0.0.0` + `ollama serve` 讓 Ollama 從只聽 127.0.0.1 改為監聽所有介面，附「等於開放給網路上所有可連到的裝置」的安全提醒 |
| [Open WebUI](../openwebui.md) | 用 `curl -N` 打 Open WebUI 的 `/api/chat/completions`（Bearer token、`text/event-stream`、`"stream": true`）測試串流回應的實例 |
| [OpenClaw](../openclaw.md) | 指令速記：`ssh -N -L` 轉發 18789 port（含 `Address already in use` 錯誤實錄）、`pnpm add -g clawhub` 與 `clawhub search`／`install`、`openclaw skills list`、`openclaw pairing approve telegram`、`openclaw channels status --probe`、`nvidia-smi` 查佔用 |
| [OpenClaw + Jan.ai](../openclaw_jan_ai.md) | 極短速記：用 `curl` 打 Jan 在 `127.0.0.1:1337` 的 `/v1/models`，以及 WSL2 `.wslconfig` 設 `networkingMode=mirrored` 讓 Windows 連得到 WSL 內服務 |

---

## 五、各家模型、IDE 與服務

| 文章 | 內容 |
|---|---|
| [ChatGPT](../ai_chatgpt.md) | 極短：用 AI 生網頁的流程——先生成 Figma、對過邏輯後再實作，兩張截圖 |
| [Google AI](../ai_google_ai.md) | Google AI 產品雜記（Project Mariner、Jules）＋ Antigravity `task.md` 的詳細解說：任務工件包含目的、需求約束、Agent 計畫、成果摘要、待辦事項；因為 Antigravity 是 agent-first IDE，每件事背後都有計畫＋追蹤文件，比「AI 直接改檔案」更透明可控 |
| [Google AI Studio](../ai_google_ai_studio.md) | 使用體感：建了類似 Anki 的閃卡 App，從下載的資料夾結構（`App.tsx`、`components/`、`services/geminiService.ts`、`vite.config.ts`）判斷是 CSR。反思是「可以先在別的地方跟 AI 討論完，再來這實作 POC」 |
| [Google Antigravity](../ai_google_antigravaty.md) | 操作筆記：Fast（直接執行）vs Planning（先計畫、產生 artifacts）兩種 mode、把每次請求定義成 task、Knowledge 記錄學到的知識、Agent Manager 與 Editor window 避免開一堆視窗、前端的 browser-in-the-loop 與視覺化編輯、在 `.agent/rules` 下新增 rule |
| [Google Gemini CLI](../ai_google_gemini.md) | `brew install gemini-cli` 安裝、執行 `gemini` 互動、首次需 Google 帳號授權，附官方 repo 與互動式網頁截圖 |
| [Gemini CLI](../gemini.md) | 佔位頁，一句簡介加一條中文教學連結 |
| [用 Gemini CLI 串 Google Sheet](../gemini_google_sheet.md) | 真實對話紀錄：讓 Gemini CLI 用視覺能力辨識圖片金額、重寫 `parse_accounts.py` 解析多行 Key: Value 並補上 amount 欄位產生 CSV；接著問「怎麼連到 Google Sheet」，得到手動匯入 vs 用 `gspread` + 服務帳戶 JSON 金鑰自動上傳兩種方法（含把 sheet 分享給 `client_email` 的關鍵步驟） |
| [Google NotebookLM](../ai_google_notebook_lm.md) | AI 研究與筆記助理，特色是以「你上傳的資料源」為依據回答並附引用來源；Audio Overview 可生成雙人對談 podcast 式語音摘要 |
| [Apple Intelligence](../ai_apple_intelligence.md) | 佔位頁，目前只有 Apple 官方支援文件與產品頁連結，加一張截圖 |
| [在 VSCode 使用 AI coding 工具](../ai_vscode.md) | VSCode 透過 extension 整合各家 agent（Copilot、Claude Code、Codex）；以 Codex extension 為例，可在側邊欄讓 agent 讀工作區、提修改建議並套用 diff |

---

## 六、AI Agent 安全與 Kubernetes 部署（Hermes 系列）

> 三篇同一主題、三種深度：`hermes.md` 是入口、`hermes_kubernetes.md` 是可貼上跑的 YAML 實作、`HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md` 是加上威脅模型與文獻的論文版。

| 文章 | 內容 |
|---|---|
| [Hermes Agent](../hermes.md) | 佔位頁：Nous Research 基於 Hermes 系列開源模型的 agent 系統，兩條連結（官方文件、Hermes vs OpenClaw 技術比較） |
| [Hermes on Kubernetes](../hermes_kubernetes.md) | **實作版**：以 YAML 為主的安全架構。威脅模型六點、五個 namespace 分層、gateway 權限最小化的 ServiceAccount/Deployment 完整範例、`/opt/data` PVC 當機密資料保護、default-deny NetworkPolicy 三段範例、sandbox Job 範例、MCP 依權限拆（calendar／discord／github／k8s-readonly／k8s-admin）與 read-only RBAC Role、Dashboard 不公開（8642／9119 port）、Secrets 分級，最後是必做 10 項＋進階 10 項的 production 基線 |
| [Kubernetes 作為 AI 代理系統之縱深防禦平台](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) | **論文版**：上篇的學術化重寫。加入威脅模型分析（外部輸入／工具執行／憑證洩漏／記憶與 Skill 四類向量）、縱深防禦／最小權限／完整仲裁三原則、Tool Router + Policy Decision Point / Enforcement Point 的 runtime policy、「tool output is data, not instruction」原則、tool-call audit log 欄位設計、第三方 Skill 的分層掃描流程與長期記憶治理，並對應資安署五項防護建議。附引用文獻查核紀錄（含一筆被判定為幻覺引用而替換的紀錄） |
| [Kubernetes as a Defense-in-Depth Platform for AI Agent Systems (EN)](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE_EN.md) | 上篇的英文版（引用已與中文版同步，含引用查核附錄） |

---

## 七、應用實作

| 文章 | 內容 |
|---|---|
| [VAD 語音喚醒](../VAD語音喚醒.md) | 瀏覽器端語音活動偵測的評估筆記：效能看 Real-time factor（`RTF < 1` 才能即時）、每秒處理 frame 數（用 `onFrameProcessed` 估算）、CPU 壓力下是否掉 frame；準確度看 false positive／false negative 與起始／結束延遲（直接影響 UX）。含 Sonos torch-to-nnef demo 與自建的 vad-bench 連結 |
| [Whisper / Breeze ASR](../ai_whisper.md) | 極短：繁體中文語音辨識可用聯發科的 Breeze-ASR-25，附 `snapshot_download('MediaTek-Research/Breeze-ASR-25')` 下載指令 |
| [AI 輔助 BMC 開發](../ai_bmc.md) | 把 AI 用進 OpenBMC 韌體開發：六個適合場景的工具對照表（查 IPMI/PMBus spec、寫 hwmon driver 骨架、解讀 dmesg、Yocto recipe、D-Bus interface、Redfish 測試腳本）、可直接複製的 prompt 範本、OpenBMC 架構 mermaid 圖與各層對應的 AI 使用場景，以及三點注意事項（kernel API 版本差異、PMBus page/phase 易錯、D-Bus 名稱大小寫敏感） |

---

## 建議閱讀順序

**想開始用 AI agent 寫程式：**

```
AI 生態總覽              ← 先知道有哪些工具
   → Claude Code 安裝
   → Claude Code
   → Agent Skills        ← 把重複的流程包成技能
   → 在 VSCode 使用 AI coding 工具
```

**想自己做一個 agent 的工具（tool）：**

```
MCP                      ← 主線：FastMCP 寫 server + cloudflared 對外
   → 使用自訂義的 GPTs   ← 換個平台的同一件事（OpenAPI 動作）
   → Firecrawl           ← 現成的網頁擷取工具
   → 遠端 Playwright MCP 控制本機 Chrome  ← 進階：CDP 與隧道
```

**想在自己的機器上跑模型：**

```
本機 LLM 推論工具        ← 先搞懂 llama.cpp / ollama / jan / lm studio 的關係
   → Jan.ai
   → 讓 Ollama 對區網／VPN 開放
   → Open WebUI
   → 用 Ollama 跑 Claude Code
```

**想把 agent 放進正式環境：**

```
Hermes Agent
   → Hermes on Kubernetes                        ← 先看 YAML 怎麼寫
   → Kubernetes 作為 AI 代理系統之縱深防禦平台    ← 再看為什麼要這樣寫
   → 為什麼公司推不動 Agentic AI                  ← 技術之外，組織的四道牆
```

---

## 待補主題

用第一性原理拆 LLM 應用的骨架：**模型 → prompt → 檢索／context → 工具／agent → 評估 → 服務**。目前筆記在**工具與操作**（Claude Code、MCP、本機推論）很紮實，但**概念層**——為什麼這樣做、怎麼衡量好壞——有明顯缺口。下表依重要性排序，部分名詞散見於各篇但沒有專門文章。

| 主題 | 為什麼重要 | 狀態 |
|---|---|---|
| **RAG（檢索增強生成）** | LLM 應用的第一號模式。[Firecrawl](../firecrawl.md) 提到「串進 RAG pipeline」，但 RAG 本身——chunking、檢索、reranking、把結果塞回 context——沒有任何一篇。要讓模型回答自己的資料，這是起點 | 待補 |
| **Embedding / 向量資料庫 / 語意搜尋** | RAG 的檢索層底座，也能獨立用於語意搜尋、去重、分類。向量怎麼來、相似度怎麼算、向量庫（FAISS／pgvector 等）怎麼選，目前完全空白 | 待補 |
| **模型評估（eval / LLM-as-judge）** | [AI 時代的基本功](../ai_basic_knowledge.md) 自己的結論是「驗證輸出對不對」最值錢，但整個知識庫沒有一篇講怎麼系統化衡量 LLM 輸出——測試集、rubric、LLM-as-judge、回歸。這是與自身論點最不一致的缺口 | 待補 |
| **Agent 設計模式** | Hermes 系列講的是 agent 的**部署與安全**，但 agent 本身怎麼設計——ReAct、plan-execute、reflection、多 agent 分工——沒有文章。這決定 agent 到底能不能把事做對 | 待補 |
| **Function calling / structured output 原理** | [MCP](../mcp.md) 講的是「工具怎麼接上」的協定，但底層 LLM 怎麼決定呼叫工具、`tool_use` 與 JSON schema 怎麼運作、structured output 怎麼強制格式，是另一層機制，沒有展開 | 待補 |
| **Prompt engineering 系統化** | few-shot、chain-of-thought、role/context/format 結構、prompt 版本管理。目前散在各篇實作裡，沒有一篇把方法論收攏 | 待補 |
| **量化與模型格式（GGUF / Q4 / GPTQ / AWQ）** | [本機推論](../ai_inference.md) 一直用到 GGUF 量化模型，但「量化是什麼、Q4 與 Q8 差在哪、GGUF vs GPTQ vs AWQ、掉多少精度換多少記憶體」從沒解釋。決定本機能不能跑得動的關鍵 | 待補 |
| **Context 管理與 token 成本** | context window 限制、token 怎麼算、長對話的壓縮與截斷、成本估算。每個實際 LLM 應用都會撞到，但沒有專門筆記 | 待補 |
| **推論最佳化（vLLM / KV cache / batching）** | [AI 生態總覽](../AI.md) 把 vLLM 列進 self-host 選型，但沒有文章講它為何比 ollama 適合多人服務——KV cache、continuous batching、throughput vs latency 的取捨 | 待補 |
