---
title: AI 名詞表
sidebar_label: AI 名詞表
sidebar_position: 3
---

# AI 名詞表

彙整知識庫中所有 AI / LLM / Agent 筆記出現過的名詞。
文章清單見 [AI / Agent 文章索引](ai_index.md)。

---

## 一、Agent 與工具協定

| 名詞 | 說明 | 出處 |
|---|---|---|
| **MCP (Model Context Protocol)** | Anthropic 提出的 Agent 工具標準協定，讓 LLM 以一致方式呼叫外部工具 | [mcp](../mcp.md)、[AI](../AI.md) |
| **FastMCP** | MCP python-sdk 提供的高階寫法。`FastMCP("Demo", json_response=True)` 建立 server | [mcp](../mcp.md) |
| **`@mcp.tool()`** | 把一個 Python 函式註冊成 MCP tool（可被 agent 呼叫的動作） | [mcp](../mcp.md) |
| **`@mcp.resource()`** | 註冊 MCP resource，可帶路徑參數（如 `greeting://{name}`） | [mcp](../mcp.md) |
| **`@mcp.prompt()`** | 註冊可重複使用的 prompt 樣板 | [mcp](../mcp.md) |
| **streamable-http** | MCP server 的傳輸方式之一，`mcp.run(transport="streamable-http")` | [mcp](../mcp.md) |
| **Agent Skills / Skill** | 可重複使用的技能模組，安裝後可在對話中被自動或手動觸發 | [skills](../skills.md)、[claude_skills](../claude_skills.md) |
| **`npx skills add`** | 安裝 skill 的 CLI，如 `npx skills add vercel-labs/agent-skills` | [skills](../skills.md)、[claude_skills](../claude_skills.md) |
| **skills.sh** | Vercel 的 agent skills 平台，用於瀏覽／安裝／分享 skill | [vercel_skills](../vercel_skills.md) |
| **`/plugin marketplace add`** | Claude Code 內加入 plugin marketplace 的指令 | [claude_skills](../claude_skills.md) |
| **`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`** | 各家 CLI 在專案內產生的 agent 指示檔：Claude Code 用 `CLAUDE.md`、Codex 用 `AGENTS.md`、Gemini 用 `GEMINI.md` | [AI](../AI.md) |
| **Agent Builder** | OpenAI 的 Agent framework（platform.openai.com/agent-builder） | [AI](../AI.md) |
| **OpenAI Agents SDK** | OpenAI 的 Agent SDK，與 MCP 一起構成其 agent 標準 + SDK 組合 | [AI](../AI.md) |
| **ADK (Agent Development Kit)** | Google 的 Agent 開發套件，搭配 Vertex AI Agent Builder 做雲端部署 | [AI](../AI.md) |
| **Claude Agent SDK** | Anthropic 的 Agent SDK，搭配 Claude Code / Claude 模型 | [AI](../AI.md) |
| **aisuite** | Andrew Ng 團隊開源的 Python 套件，用統一介面呼叫多家供應商 | [deeplearning_ai_aisuite](../deeplearning_ai_aisuite.md) |
| **`provider:model`** | aisuite 指定模型的字串格式，如 `openai:gpt-4o`；換成 `anthropic:...` 即切換供應商 | [deeplearning_ai_aisuite](../deeplearning_ai_aisuite.md) |

---

## 二、Claude Code

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Claude Code** | Anthropic 官方的 agentic CLI，可讀專案、編輯檔案、執行指令、完成多步驟開發任務 | [claude_code](../claude_code.md) |
| **`@anthropic-ai/claude-code`** | Claude Code 的 npm 套件名，`npm install -g` 全域安裝，需 Node.js | [claude_install](../claude_install.md) |
| **Channels** | Claude Code 的功能，用於在不同介面／管道與 Claude Code 互動 | [claude_channel](../claude_channel.md) |
| **Claude Code Chrome 整合** | 透過瀏覽器擴充功能讓 agent 操作網頁（導覽、點擊、讀取頁面內容） | [claude_code](../claude_code.md) |
| **`ollama launch claude`** | 用 Ollama 啟動 Claude Code 並選擇底層模型的指令 | [claude_use_ollama](../claude_use_ollama.md) |
| **skill-creator** | anthropics 官方 plugin 提供的 skill，用於建立新 skill | [claude_skills](../claude_skills.md) |

---

## 三、本機推論與自架

| 名詞 | 說明 | 出處 |
|---|---|---|
| **llama.cpp** | 以 C/C++ 實作的推論引擎，支援 GGUF 量化模型；是 lm studio、ollama、jan 三者共同的核心 | [ai_inference](../ai_inference.md) |
| **GGUF** | llama.cpp 使用的量化模型格式 | [ai_inference](../ai_inference.md)、[ai_jan_ai](../ai_jan_ai.md) |
| **LM Studio** | 桌面 GUI 應用，方便下載模型、切換與試玩，適合個人本機互動 | [ai_inference](../ai_inference.md) |
| **Ollama** | 以指令列與 API server 為主，適合部署成服務讓多人／多端存取 | [ai_inference](../ai_inference.md) |
| **Jan** | 類似 LM Studio 但採 Apache 2.0 開源授權，可完全離線，資料不外流 | [ai_jan_ai](../ai_jan_ai.md)、[ai_inference](../ai_inference.md) |
| **vLLM** | self-host 推論選項之一，筆記中與 ollama 並列比較 | [AI](../AI.md) |
| **選型三句話** | 要 GUI 試玩選 lm studio 或 jan；要開源選 jan；要當服務給多人／程式呼叫選 ollama | [ai_inference](../ai_inference.md) |
| **`OLLAMA_HOST`** | Ollama 監聽位址。預設只聽 `127.0.0.1`，設為 `0.0.0.0` 才能讓區網／VPN 其他裝置存取 | [ollama_export_in_vpn](../ollama_export_in_vpn.md) |
| **Open WebUI** | 自架的 LLM 對話前端，提供 `/api/chat/completions` 端點（Bearer token + `text/event-stream` 串流） | [openwebui](../openwebui.md) |
| **OpenClaw** | AI agent 平台，俗稱「龍蝦」，在台灣廣泛使用；具高系統權限與 24 小時自主運作能力 | [openclaw](../openclaw.md)、[HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **clawhub** | OpenClaw 的 skill 市集與 CLI：`pnpm add -g clawhub`、`clawhub search` / `clawhub install` | [openclaw](../openclaw.md) |
| **`openclaw pairing approve`** | 核准頻道配對，如 `openclaw pairing approve telegram <pass>` | [openclaw](../openclaw.md) |
| **`openclaw channels status --probe`** | 探測各管道連線狀態 | [openclaw](../openclaw.md) |
| **`networkingMode=mirrored`** | WSL2 `.wslconfig` 設定，讓 Windows 與 WSL 共用網路，方便互連本機服務 | [openclaw_jan_ai](../openclaw_jan_ai.md) |
| **Hermes Agent** | Nous Research 基於 Hermes 系列開源模型打造的 agent 系統 | [hermes](../hermes.md) |

### 筆記中出現過的模型

| 模型 | 說明 | 出處 |
|---|---|---|
| **`minimax-m2.5:cloud`** | Ollama 推薦的雲端模型，主打快速、高效率的 coding 與實務生產力 | [claude_use_ollama](../claude_use_ollama.md) |
| **`glm-5:cloud` / `glm-4.7-flash`** | 推理與程式碼生成；`glm-4.7-flash` 為本地版，約 25GB | [claude_use_ollama](../claude_use_ollama.md) |
| **`kimi-k2.5:cloud`** | 多模態推理，帶 subagents | [claude_use_ollama](../claude_use_ollama.md) |
| **`qwen3:8b`** | 高效率的通用助理模型，約 11GB | [claude_use_ollama](../claude_use_ollama.md) |
| **`gemma3:12b`** | 用 `ollama pull` 下載的 Google 開源模型 | [openclaw](../openclaw.md) |
| **`ministral-3:latest`** | Open WebUI 測試串流時使用的模型 | [openwebui](../openwebui.md) |
| **Breeze-ASR-25** | 聯發科（MediaTek Research）開發的繁體中文語音辨識模型 | [ai_whisper](../ai_whisper.md) |

---

## 四、各家產品對照

| 類型 | OpenAI | Google | Anthropic | Perplexity |
|---|---|---|---|---|
| Chat | ChatGPT | — | — | Perplexity |
| POC | — | Google AI Studio | — | — |
| Browser | ChatGPT Atlas | Chrome AI 模式 | — | Perplexity Comet |
| AI 筆記與研究 | NotebookLM（實為 Google 產品，原表列於此欄） | — | — | — |
| 地端 IDE | — | Antigravity | Claude Code CLI | — |
| 企業 AI 搜尋 | — | Google Agentspace | — | — |
| CLI | Codex CLI | Gemini CLI | Claude Code CLI | — |
| Agent Framework | MCP + OpenAI Agents SDK | ADK / Vertex AI Agent Builder | Claude Agent SDK | — |

> 出處：[AI](../AI.md)（該筆記中同時有兩張對照表，欄位歸屬略有出入，此處合併整理）

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Antigravity** | Google 的 agent-first 本地 IDE | [ai_google_antigravaty](../ai_google_antigravaty.md) |
| **Google AI Studio** | Google 的 AI POC / 快速建 App 平台，產物為 Vite + React 的 CSR 前端專案 | [ai_google_ai_studio](../ai_google_ai_studio.md) |
| **NotebookLM** | Google 的 AI 研究與筆記助理，以「你上傳的資料源」為依據回答並附引用 | [ai_google_notebook_lm](../ai_google_notebook_lm.md) |
| **Audio Overview** | NotebookLM 依資料源生成的雙人對談 podcast 式語音摘要 | [ai_google_notebook_lm](../ai_google_notebook_lm.md) |
| **Project Mariner / Jules** | Google Labs 的兩個 AI 專案連結 | [ai_google_ai](../ai_google_ai.md) |
| **Gemini CLI** | Google 官方開源終端機 AI agent，`brew install gemini-cli` 安裝，首次需 Google 帳號授權 | [ai_google_gemini](../ai_google_gemini.md)、[gemini](../gemini.md) |
| **Codex / Codex CLI** | OpenAI 的 coding agent，有 VSCode extension 可在側邊欄互動、套用 diff | [ai_vscode](../ai_vscode.md)、[AI](../AI.md) |
| **GPTs 動作（Actions）** | 自訂 GPTs 呼叫外部 API 的機制，可從 `openapi.json` 網址匯入 | [gpts](../gpts.md) |
| **Apple Intelligence** | Apple 的 AI 功能（筆記中僅有官方文件連結） | [ai_apple_intelligence](../ai_apple_intelligence.md) |

---

## 五、Antigravity 專有名詞

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Task** | Antigravity 把每一次請求定義成一個 task，因為它的重點在於「Agent 如何工作」 | [ai_google_antigravaty](../ai_google_antigravaty.md) |
| **`task.md` / Task Artifact** | Agent 執行任務時自動產生的任務說明文件，含 Goal、需求與約束、Implementation Plan、Output Summary、Remaining Work 五段 | [ai_google_ai](../ai_google_ai.md) |
| **Fast mode / Planning mode** | Fast 直接執行；Planning 先計畫並產生 artifacts | [ai_google_antigravaty](../ai_google_antigravaty.md) |
| **Agent Manager** | 管理多個 agent 工作的面板，用於減少 context switching | [ai_google_antigravaty](../ai_google_antigravaty.md) |
| **Editor window** | Antigravity 的整合視窗，避免開一堆視窗 | [ai_google_antigravaty](../ai_google_antigravaty.md) |
| **Knowledge** | Antigravity 記錄「學到的知識」的機制 | [ai_google_antigravaty](../ai_google_antigravaty.md) |
| **browser-in-the-loop** | 前端開發時可透過瀏覽器打開或互動，並直接視覺化編輯 | [ai_google_antigravaty](../ai_google_antigravaty.md) |
| **`.agent/rules`** | Antigravity 新增 rule 後存放的專案目錄 | [ai_google_antigravaty](../ai_google_antigravaty.md) |

---

## 六、瀏覽器自動化與 CDP

| 名詞 | 說明 | 出處 |
|---|---|---|
| **CDP (Chrome DevTools Protocol)** | Chrome 的控制協議，收 JSON 指令回 JSON 結果（導航、點擊、截圖）。**沒有任何驗證機制**——連得上就等於完全控制瀏覽器 | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **`--remote-debugging-port=9222`** | Chrome 啟動參數，會開一個 HTTP + WebSocket 伺服器接受 CDP 指令。**預設只綁 127.0.0.1** | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **`--user-data-dir`** | Chrome 啟動參數。**必須指向獨立資料夾**，否則會附掛到已開啟的 Chrome 實例，debug port 掛不上 | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **`connectOverCDP()`** | Playwright 連接「已存在、開著 debug port」的瀏覽器，而非自己啟動一個 | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **`--cdp-endpoint`** | Playwright MCP 連既有瀏覽器的參數，給 `http://localhost:9222` 即可，它會自己去抓 `webSocketDebuggerUrl` | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **`webSocketDebuggerUrl`** | 從 `http://localhost:9222/json/version` 取得的帶 UUID 的 WS endpoint，格式為 `ws://localhost:9222/devtools/browser/<UUID>` | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **反向 SSH 隧道（`ssh -R`）** | `ssh -N -R 9222:localhost:9222 user@linux-server`，把 Linux 的 localhost:9222 反向轉發到 Windows 的 Chrome。標準解法，因為它同時給了加密與認證 | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **`GatewayPorts`** | sshd 設定。預設 `no` 表示反向轉發出來的 port 只綁 server 的 `127.0.0.1`——**保持預設就是安全的**，不要開 `yes` | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **`ssh -L`** | 本地轉發，如 `ssh -N -L 18789:127.0.0.1:18789 alanhc@<ip>`；port 撞號會出現 `Address already in use` | [openclaw](../openclaw.md) |
| **autossh / `ServerAliveInterval`** | `ssh -R` 斷線不會自動重連，長期跑要用 autossh 或加 keepalive 參數 | [claude_remote_playwright_mcp](../claude_remote_playwright_mcp.md) |
| **`cloudflared tunnel --url`** | 把本機服務（如 `http://127.0.0.1:8000`）暴露成公開 HTTPS 網址，會給一個 `*.trycloudflare.com` 域名 | [mcp](../mcp.md)、[gpts](../gpts.md) |
| **Playwright MCP Server** | 負責瀏覽器自動化任務的 MCP server | [ai_testing](../ai_testing.md) |
| **Playwright Test MCP Server** | 用於測試工作流程，使用 Playwright Agents 時自動啟用 | [ai_testing](../ai_testing.md) |
| **Planner / Generator / Healer** | Playwright agent 的三個角色 | [ai_testing](../ai_testing.md) |
| **Firecrawl `scrape` / `crawl` / `map` / `extract`** | 分別為：抓單一頁面／遞迴走訪整站／快速列出所有 URL／用 LLM 依 schema 擷取結構化資料 | [firecrawl](../firecrawl.md) |

---

## 七、AI Agent 安全（Hermes 系列）

### 核心原則

| 名詞 | 說明 | 出處 |
|---|---|---|
| **思考層 vs 行動層** | 本系列的核心論點：gateway 只負責對話與決策（brain），所有高風險工具執行拆出去（controlled hands）。從架構設計第一天就該分開 | [hermes_kubernetes](../hermes_kubernetes.md)、[HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **縱深防禦 (Defense-in-depth)** | 安全控制分佈多層，單一層失效不導致全面淪陷 | [HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **最小權限 (Least privilege)** | 每個元件只持有完成功能所需的最小權限集合 | [HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **完整仲裁 (Complete mediation)** | Saltzer & Schroeder (1975) 原則：每次存取受保護資源都要獨立授權，而非啟動時授權一次 | [HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **Prompt injection / 間接提示注入** | 透過訊息、社群留言、網頁內容注入惡意指令。核心風險假設：**任何外部輸入都可能含惡意指令** | [HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **權限移轉 (privilege transfer)** | 一旦真實工具交給 LLM agent，工具權限在實際效果上已移轉給 agent 與其底層模型 | [HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **Tool output is data, not instruction** | 工具輸出一律視為不可信資料。網頁內容、GitHub 留言、Slack 訊息、log 都不能授權後續工具使用 | [HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **Instruction hierarchy** | Wallace 等人 (2024)：外部工具回傳內容的指令優先級應低於系統指令，不得覆蓋安全規則 | [HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |
| **`/opt/data`** | Hermes 存放 config、API keys、sessions、skills、memories 的目錄。應視為企業密鑰庫（crown jewels），tools 與 sandbox 一律不得掛載 | [hermes_kubernetes](../hermes_kubernetes.md)、[HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md) |

### 命名空間分層

| Namespace | 角色 |
|---|---|
| `hermes-system` | 思考層：Hermes Gateway、Dashboard，不直接持有行動權限 |
| `hermes-tools` | 受控行動層：各 MCP server，持有特定服務的 scoped token |
| `hermes-sandbox` | 隔離執行層：Shell、Browser、Code Runner 等高風險工具，一次性受限工作空間 |
| `llm-serving` | 模型推論層：Ollama / vLLM / NIM，或 egress 到雲端 API |
| `observability` | 可觀測層：Prometheus / Loki / Grafana、稽核日誌 |

> 出處：[hermes_kubernetes](../hermes_kubernetes.md)、[HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md)

### Kubernetes 機制

| 名詞 | 說明 |
|---|---|
| **Pod Security Standards** | 三個層級：Privileged、Baseline、Restricted。`restricted` 依 Pod hardening best practices 設計，是本架構要求的等級（Kubernetes ≥ 1.25） |
| **`automountServiceAccountToken: false`** | 避免 gateway 持有 Kubernetes API token |
| **`allowPrivilegeEscalation: false`** | 避免 setuid/setcap 提權 |
| **`readOnlyRootFilesystem: true`** | 唯讀根檔案系統。**前提是確認應用只寫 `/opt/data` 與 `/tmp`**，啟動失敗時可先拿掉再收緊 |
| **`capabilities: drop: ["ALL"]`** | 丟掉所有 Linux capabilities |
| **`seccompProfile: RuntimeDefault`** | 套用預設 seccomp 設定檔 |
| **default-deny NetworkPolicy** | `podSelector` 留空物件、`policyTypes` 含 Ingress 與 Egress，強制所有流量明確宣告。**前提是 CNI 要支援 NetworkPolicy**（Calico、Cilium）；不支援時建立了也沒有實際效果 |
| **PVC ReadWriteOnce (RWO)** | 只允許單一節點掛載讀寫，這是 `replicas: 1` 的技術來源。要 HA 需改用 ReadWriteMany (RWX) 的 NFS / CephFS 並加分散式鎖 |
| **不掛 Docker socket** | Docker socket 等同於高權限控制 host/container runtime，掛了等於可 container escape |
| **不掛 `hostPath` / 不用 `hostNetwork`** | 前者避免存取 host filesystem，後者避免繞過 NetworkPolicy |
| **RBAC list/watch secrets 的陷阱** | Kubernetes 官方提醒：`list`/`watch` secrets 實際上會讓使用者看到 Secret 內容；能建立 workload 的權限也可能間接取得 namespace 內的 Secret |
| **明確禁止的資源** | `secrets`、`pods/exec`、`pods/attach`、`serviceaccounts/token`、`persistentvolumes`、`mutatingwebhookconfigurations`，以及 `verbs: ["*"]`、`resources: ["*"]` |
| **`ttlSecondsAfterFinished`** | sandbox Job 完成後自動刪除的秒數 |
| **Cilium FQDN Policy** | 原生 NetworkPolicy 只支援 IP CIDR、不支援 DNS/FQDN。要管控外部 LLM API 呼叫需用 Cilium FQDN policy、egress gateway，或集中到單一 llm-proxy |

> 出處：[hermes_kubernetes](../hermes_kubernetes.md)、[HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md)

### MCP 分權限

| MCP Server | 持有憑證 | 允許操作 |
|---|---|---|
| `calendar-mcp` | Google OAuth credential | 建立、查詢 Calendar event |
| `discord-mcp` | Discord bot token | 管理指定 server／channel |
| `github-mcp` | GitHub fine-grained token | 操作指定 repository |
| `k8s-readonly-mcp` | 受限 RBAC | 唯讀 pods / pods/log / services / events / deployments 等 |
| `k8s-admin-mcp` | 完整 RBAC | **預設停用**，需人工核准，短效 token |

> 出處：[hermes_kubernetes](../hermes_kubernetes.md)、[HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md)

### Runtime policy 與治理

| 名詞 | 說明 |
|---|---|
| **Tool Router** | gateway 與 MCP／sandbox 之間的中介，作為統一的 Policy Enforcement Point |
| **Policy Decision Point (PDP)** | 判斷此次呼叫是否被允許 |
| **Policy Enforcement Point (PEP)** | 攔截、拒絕、轉送執行或觸發人工核准 |
| **tool-call audit log** | 與 Kubernetes audit log 目的不同：後者答「哪個 pod 對 API 做了什麼」，前者才答「哪個使用者、哪個 session、用哪個工具、對哪個資源、在什麼 policy decision 下做了什麼」。欄位含 `timestamp`、`requesting_user`、`agent_id`、`session_id`、`tool_name`、`requested_action`、`target_resource`、`credential_scope`、`policy_decision`、`approval_result`、`execution_result`、`risk_level` |
| **human approval gate** | 強制人工核准的操作：刪除持久性資料、發送外部訊息、存取憑證、執行 shell／browser／Kubernetes mutation、把 `/opt/data` 或 memory 送到外部 |
| **長期記憶治理** | 安全規則若只存在短期對話上下文，長時間運作或壓縮後會遺失。應寫入啟動設定、納入版控、定期備份審閱、對變更建立 audit log |
| **第三方 Skill 審查** | 人工 code review + 靜態分析 + secret scanning（gitleaks、trufflehog）+ 沙箱行為驗證；production 只允許內部 registry 或 allowlist |

> 出處：[HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md)

### 相關工具與研究名詞

| 名詞 | 說明 |
|---|---|
| **gVisor (runsc) / Kata Containers** | 進階 sandbox runtime，進一步隔離系統呼叫層面的風險 |
| **OPA Gatekeeper / Kyverno** | Admission policy 強制執行 |
| **Trivy / Grype** | Container image 漏洞掃描 |
| **Falco** | Runtime 異常行為偵測 |
| **cosign** | Container image 簽章驗證 |
| **External Secrets Operator / Sealed Secrets / SOPS + age / HashiCorp Vault** | Secret 生命週期管理的四種方案，分別對應雲端密鑰服務、GitOps、本地加密、企業級 |
| **Agent Sandbox** | Kubernetes 與 Google Cloud 針對 AI agent runtime 推出的設計，目標是隔離 agent workspace、不可信程式碼執行、process、storage 與 network boundary |
| **GrantBox** | Zhang 等人 (2026) 提出的評估沙箱，讓 LLM agent 對真實工具行使真實權限以評估其權限使用 |
| **DDIPE** | 靜態分析要掃描的惡意指令嵌入模式之一 |
| **Data Thieves / Agent Hijackers** | Liu 等人 (2026) 掃描 98,380 個 Skill 後歸納的兩類惡意 Skill 攻擊模式：憑證竊取與決策劫持 |
| **SkillFortify** | Bhardwaj (2026) 提出的框架，以靜態分析結合 capability sandboxing，達 96.95% F1 偵測率 |
| **幻覺引用 (hallucinated reference)** | 論文版附錄的查核紀錄：原引用 [5] MCP-Secure 在學術資料庫查無此文，判定為幻覺引用並替換為兩篇可核實論文 |

> 出處：[HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE](../HERMES_AI_KUBERNETES_SECURITY_ARCHITECTURE.md)

---

## 八、組織與治理（觀點文名詞）

| 名詞 | 說明 | 出處 |
|---|---|---|
| **四道牆** | 推不動 agentic AI 的四個組織障礙：①管理層覺得不好管 ②出事沒人負責 ③同事怕被取代 ④agent 拆解角色後責任滑到 code review | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **能力—部署驗證落差** | Apostolou 等人 (2026)：公司做得出實驗性高階 AI，卻因缺乏產出驗證機制而無法放進生產流程。四個障礙為 LLM context window 限制、專有語言／協定表現不佳、非決定性、資料機密性 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Accountability gap（問責落差）** | IBM 的框架：企業缺乏監控 agent 行為、審查自動化決策、事後歸屬責任的能力 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Principal-agent problem（委託代理問題）** | 經濟學的絕妙雙關：委託 agent 做事會遇到資訊不對稱與目標不一致。傳統解法是**誘因契約**——但 AI agent 同時抽掉兩根支柱（推理黑箱無法觀察、沒有考績聲譽無法用誘因約束） | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **責任蒸發** | 流程從「某工程師負責」變成「某 agent 負責」時，責任不是轉移而是憑空消失 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **眾手問題 (problem of many hands)** | 應用倫理學概念：結果由許多人共同促成時，反而沒有單一個人能被清楚究責 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Causal responsibility vs Accountability** | 前者是「誰的疏漏造成 bug」，多因、事後查；後者是「誰對外負責」，制度**事先**指派。組織的痛苦多半來自以為在找前者，真正缺的是後者 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **機長比喻** | 機長對整架飛機負責，不代表每顆螺絲都是他鎖的。agent pipeline 天生沒有機長——merge authority 是**刻意造出來的** | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Moral hazard（道德風險）** | 不必承擔自己行為後果的人會怠於盡責。全自動 merge 或橡皮圖章式 review 就是溫床：問責一旦被稀釋，監督品質跟著滑落 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Goodhart's law** | 當一個衡量指標變成考核目標，它就不再是好的衡量指標。把「AI 建議接受率」設成 KPI 等於在衡量工程師願不願意關掉批判性思考 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **STARA awareness** | Brougham & Haar (2018)：員工對「智慧科技、AI、機器人、演算法」的覺察程度越高，組織承諾與職涯滿意度越低、離職意圖越高 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **配合但不投入** | 抵抗最難察覺的形式：訓練資料淺一層、agent 的錯不主動回報、最關鍵的隱性知識不寫進 skill | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **創新擴散（Rogers, 1962）** | 採用者分成創新者、早期採用者、早期大眾、晚期大眾、落後者。策略是**先賦權改革派**讓他們橫向擴散，而非把力氣花在安撫保守派 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Enthusiasts / Pragmatists / Cautious** | 實證研究把開發者分成熱衷者、務實者、謹慎者三群，對應 Rogers 的採用者類別 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **任務串接 (task chaining)** | 「取代 vs 增強」二分法不足；AI 實際上在角色內部移轉責任，並讓工作邊界被重畫 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Oversight burden（監督負擔）** | Garousi (2026)：AI 導入軟體工程最常被低估的隱藏成本，有時消耗的力氣比省下的還多 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **依風險分級的人類監督** | 「什麼都審」造成速度崩潰、「什麼都不審」造成不可稽核。GAIE 框架的 OCM 依法規影響、客戶接近度、可逆性、資料敏感度路由到 human-in-the-loop / human-over-the-loop / automated-with-monitoring 三級 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Minions（Stripe）** | Stripe 內部自主編碼 agent，每週產出 1,300+ 個零人類手寫程式碼的 PR，但**每一個仍由人類 review 後才 merge**。規模化關鍵是既有開發基礎設施（devbox 沙箱、測試、CI、確定性關卡）而非模型強弱 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Stop 區段 / allowlist / denylist** | agent 設定檔中由工程師親手寫下的能力邊界：絕不 merge、絕不刪除、絕不 push 到 main、不確定的丟給人看。「你沒寫進去的紅線，總有一天 agent 會替你踩過去」 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **Security vs RD 斷層** | DevSecOps 系統性回顧指出「人」的最大挑戰是開發與安全團隊衝突，根源是**目標函數不同**。agent 讓斷層位置改變：雙方第一次面對「連 RD 自己都沒把握的 AI 產出」，gate 從「管制 RD」變成「保護 RD」 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **顯影劑** | 全文結論：agent 不是這些病的病因，而是把公司平常靠默契糊住的裂縫一次照亮 | [ai-why-companies-struggle-agentic-ai](../ai-why-companies-struggle-agentic-ai.md) |
| **技能半衰期** | 技術棧各層貶值速度不均：框架約 2~3 年、程式語言約 10 年，但「拆解需求、判斷系統為何慢、讀懂爛程式碼、在兩個都有道理的方案間取捨」半衰期長得驚人 | [ai_basic_knowledge](../ai_basic_knowledge.md) |
| **無法證偽的話** | 「基本功最重要」永遠不會錯，因為詞的邊界可以隨時伸縮；一句不能被證偽的話提供的不是資訊，是安慰 | [ai_basic_knowledge](../ai_basic_knowledge.md) |

---

## 九、語音辨識

| 名詞 | 說明 | 出處 |
|---|---|---|
| **VAD (Voice Activity Detection)** | 語音活動偵測，判斷音訊中是否有人在說話 | [VAD語音喚醒](../VAD語音喚醒.md) |
| **Real-time factor (RTF)** | 處理時間 ÷ 音檔長度。**`RTF < 1` 才能即時** | [VAD語音喚醒](../VAD語音喚醒.md) |
| **`onFrameProcessed`** | VAD 的回呼，可用來估算每秒能處理多少音訊 frame | [VAD語音喚醒](../VAD語音喚醒.md) |
| **False positive / False negative** | 把靜音／噪聲誤判成說話，或漏判說話 | [VAD語音喚醒](../VAD語音喚醒.md) |
| **onset / offset lag** | 起始／結束延遲：開始講話多久才亮、停講多久才熄，**直接影響 UX** | [VAD語音喚醒](../VAD語音喚醒.md) |
| **torch-to-nnef** | Sonos 的轉檔工具，其 VAD demo 可在網頁直接體驗 | [VAD語音喚醒](../VAD語音喚醒.md) |
| **vad-bench** | 自建的 VAD 評測頁面 | [VAD語音喚醒](../VAD語音喚醒.md) |

---

## 十、AI 輔助 BMC 開發

| 名詞 | 說明 | 出處 |
|---|---|---|
| **PMBus Linear11** | PMBus 的數值格式：N = 高 5 bit 有號整數、Y = 低 11 bit 有號整數，`Value = Y × 2^N`。適合請 AI 代算 | [ai_bmc](../ai_bmc.md) |
| **hwmon driver 骨架** | 請 AI 產生 `drivers/hwmon/pmbus/xxx.c`（含 probe）、Kconfig 項目、Makefile 一行、DTS binding 範例 | [ai_bmc](../ai_bmc.md) |
| **bmcweb** | OpenBMC 的 Redfish / REST API 層，AI 適合協助產生 API 測試 script、理解 schema | [ai_bmc](../ai_bmc.md) |
| **phosphor-dbus-interfaces** | OpenBMC 的 D-Bus interface 定義。**名稱大小寫敏感，AI 有時會拼錯 `xyz.openbmc_project.*`** | [ai_bmc](../ai_bmc.md) |
| **`FILESEXTRAPATHS:prepend`** | Yocto recipe 語法，AI 可協助解釋 `SRC_URI += "file://xxx.patch"` 與 `${THISDIR}/${PN}` 這類寫法 | [ai_bmc](../ai_bmc.md) |
| **AI 產碼三個雷區** | ①Kernel API 版本差異大（OpenBMC 常用 5.15 / 6.1）②PMBus 的 page / phase 參數容易出錯，務必對照 datasheet ③D-Bus interface 名稱大小寫敏感 | [ai_bmc](../ai_bmc.md) |

---

## 十一、其他工具與指令

| 名詞 | 說明 | 出處 |
|---|---|---|
| **yt-dlp** | 下載 YouTube 資訊與字幕的套件。`skip_download` + `writesubtitles` + `writeautomaticsub` 只抓字幕；不限定語言時要用 `subtitleslangs` 收斂，否則抓全部自動字幕容易觸發 429 | [gpts](../gpts.md) |
| **VTT** | YouTube 字幕格式。筆記中的 `parse_vtt()` 會解析時間戳並把 5 秒內的相鄰字幕合併 | [gpts](../gpts.md) |
| **gspread** | Python 套件，用服務帳戶 JSON 金鑰串接 Google Sheets API | [gemini_google_sheet](../gemini_google_sheet.md) |
| **`client_email`** | 服務帳戶 JSON 裡的欄位（`xxx@xxx.iam.gserviceaccount.com`）。**必須把 Google Sheet 用「共用」分享給這個 Email 並給編輯者權限**，否則寫不進去 | [gemini_google_sheet](../gemini_google_sheet.md) |
| **CSR** | Client-Side Rendering。從 AI Studio 下載的專案結構（`App.tsx` + `vite.config.ts`）可判斷產物是 CSR | [ai_google_ai_studio](../ai_google_ai_studio.md) |
| **`snapshot_download`** | Hugging Face Hub 的下載函式，用 `uv run python -c "..."` 一行下載模型 | [ai_whisper](../ai_whisper.md) |
| **`nvidia-smi --query-compute-apps`** | 查詢佔用 GPU 的 process 與其 VRAM 用量，`--format=csv` 輸出 | [openclaw](../openclaw.md) |
