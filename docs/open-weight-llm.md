# Open-weight LLM 是什麼？

## 一句話定義

**Open-weight LLM（開放權重大型語言模型）**：模型訓練完成後的**權重（weights / parameters）公開釋出**，任何人都可以下載到自己的機器上執行、微調或部署的語言模型。

對比之下，GPT、Claude 這類 **closed-weight（閉源權重）** 模型只能透過 API 或官方產品使用，權重本身不公開。

---

## 權重是什麼？

一個 LLM 可以粗略拆成三個部分：

| 組成 | 說明 | Open-weight 通常有公開嗎？ |
|---|---|---|
| **架構 / 推論程式碼** | Transformer 結構、tokenizer、forward pass | ✅ 通常有 |
| **權重（weights）** | 訓練後得到的數十億～上兆個浮點數，就是模型「學到的知識」 | ✅ **這就是 open-weight 的核心** |
| **訓練資料 + 訓練程式碼 + 訓練流程** | 資料集、清洗 pipeline、超參數、RLHF 資料 | ❌ 大多**不**公開 |

所以 open-weight = 「你拿得到成品，但不一定知道它是怎麼煉出來的」。

---

## Open-weight ≠ Open-source

這是最常被混淆的地方。

- **Open-weight**：只公開權重（通常加上推論程式碼）。授權條款可能有限制。
- **Open-source AI**（依 OSI 的 Open Source AI Definition）：除了權重，還要提供足以**重現**模型的資訊——訓練資料的說明/取得方式、完整訓練程式碼，且授權允許自由使用、修改、再散布。

類比軟體世界：

> Open-weight 比較像拿到一個**可以自由執行、也能 patch 的 binary**；Open-source 則是連**原始碼和 build system** 一起給你。

多數知名的「開源模型」嚴格來說都只是 open-weight。真正接近完整開源的例子如 AI2 的 **OLMo**、EleutherAI 的 **Pythia**，它們連訓練資料和 checkpoint 都公開。

---

## 授權條款差很多

「open」不代表「無限制」，下載前要看 license：

| 授權類型 | 特點 | 例子 |
|---|---|---|
| **寬鬆授權**（Apache 2.0 / MIT） | 可商用、可修改、限制極少 | Mistral 部分模型、Qwen 多數模型、DeepSeek 系列、OpenAI gpt-oss |
| **自訂社群授權** | 可商用但有條件（如使用者規模上限、可接受使用政策、需標示） | Meta Llama 系列、Google Gemma |
| **非商用 / 研究用** | 只能研究，不能商業使用 | 部分學術釋出模型 |

> ⚠️ 各模型、各版本的授權可能不同，實際使用前以官方 model card / LICENSE 為準。

---

## 常見的 Open-weight 模型家族

- **Kimi**（Moonshot AI / 月之暗面）
- **GLM**（Z.ai / 智譜）
- **MiMo**（小米）
- **MiniMax**
- **Meta Llama**
- **Mistral / Mixtral**（Mistral AI）
- **Qwen**（阿里巴巴）
- **DeepSeek**（V 系列、R1 推理模型）
- **Nemotron**（NVIDIA）
- **Gemma**（Google）
- **Phi**（Microsoft，小模型）
- **gpt-oss**（OpenAI）
- **OLMo**（AI2，完全開源）

大多可以在 **Hugging Face Hub** 上找到。

---

## 目前排名（2026 年 9 月）

> 排名變動很快，以下是 2026-09-24 查到的快照。不同榜單的測法不同，名次也會不一樣。

### Artificial Analysis Intelligence Index（open-weight 前段）

資料來源：Artificial Analysis 綜合智力指數，這是一個整合多項 benchmark 的綜合分數（The Open Weights 網站有轉載並提供較完整的列表）。

| 名次 | 模型 | 開發者 | 分數 |
|---|---|---|---|
| 1 | MiMo-V2.6-Pro | Xiaomi（小米） | ~46 |
| 2 | GLM-5.3 | Z.ai（智譜） | ~45 |
| 3 | Kimi K3 | Moonshot AI（月之暗面） | ~44 |
| 4 | GLM-5.3 Flash | Z.ai | ~42 |
| 5 | Qwen3.8 2.4T-A95B | Alibaba Qwen | ~40 |
| 6 | Qwen3.8-Flash-Next | Alibaba Qwen | ~40 |
| 7 | DeepSeek V4.1 Flash | DeepSeek | ~40 |
| 8 | DeepSeek V4 Pro | DeepSeek | ~36 |

**對照閉源模型：** 同一榜單上最高的是 Claude Opus 5.5，約 58 分。open-weight 第一名落後約 12 分。
**差距的變化：** 2026 年 4 月 Kimi K2.6、MiMo V2.5 Pro 推出時，曾經追到只差 3–6 分。後來新一代閉源模型推出，差距又被拉開了。

### 主要模型規格

| 模型 | 總參數 / 啟用參數 | 授權 | Context | 特色 |
|---|---|---|---|---|
| **Kimi K3** | 2.8T / 50B（MoE） | Modified MIT | 1M | 目前最大的 open-weight 模型，多模態，擅長推理與長時程 agent 任務 |
| **GLM-5.x** | 744B / 40B（MoE） | MIT | — | coding 最強之一（Terminal-Bench、SWE-bench Pro） |
| **DeepSeek V4-Pro** | 1.6T / 49B（MoE） | MIT | 1M | 推理強，SWE-bench 約 80% |
| **DeepSeek V4-Flash** | 284B / 13B（MoE） | MIT | 1M | CP 值高，兩張 GPU 就能跑到接近前沿的水準 |
| **Llama 4 Maverick** | 400B / 17B（MoE） | Llama 4 Community | 1M | 多模態通用型，但排名已明顯落後中國模型 |
| **Mistral Small 4** | 119B / 6.5B（MoE） | Apache 2.0 | — | 輕量、硬體需求低，適合 agentic coding |
| **NVIDIA Nemotron Ultra** | 253B（dense） | NVIDIA Open Model | — | 針對推理與 RAG 最佳化 |
| **Qwen3.8 27B** | 27B（dense） | Apache 2.0 | 256K | 單卡就能跑的小模型裡表現突出 |

### 觀察

- **前段幾乎都是中國實驗室**：小米、智譜、月之暗面、阿里、DeepSeek。美國的 open-weight 代表（Llama、gpt-oss、Nemotron）排名在後面。
- **MoE 是主流**：總參數動輒上兆，但每個 token 只啟用 13B–95B，推論成本遠低於同規模的 dense 模型。
- **1M context 已經很常見**。
- **授權越來越寬鬆**：前段模型大多採用 MIT 或 Apache 2.0。
- **想在本機跑的話**：前幾名的完整模型需要多張資料中心等級的 GPU。筆電或單卡比較實際的選擇是 Qwen3.8 27B、Mistral Small 4、gpt-oss，或各家的 Flash / 小型版本加上量化。

### 追蹤排名的網站

- [Artificial Analysis – LLM Leaderboard](https://artificialanalysis.ai/leaderboards/models)（可以篩選只看 open weights）
- [The Open Weights – LLM Intelligence](https://theopenweights.com/leaderboards/llm-intelligence)
- [LMArena](https://huggingface.co/spaces/lmarena-ai/arena-leaderboard)（依人類盲測投票計算 Elo）
- [Hugging Face Trending Models](https://huggingface.co/models?sort=trending)

---

## 為什麼要用 Open-weight？

**優點**

- **資料隱私 / 地端部署**：資料不離開自己的機器或內網，適合企業機密、法規要求場景
- **可微調（fine-tuning）**：用 LoRA / QLoRA 等方法針對特定領域客製化
- **成本可控**：大量推論時，自建可能比 API 便宜；也沒有 rate limit
- **可研究、可檢查**：能做 interpretability、量化、剪枝、安全性分析
- **不被供應商綁定**：模型不會突然下架或改行為
- **邊緣裝置執行**：量化後可以在筆電、手機、嵌入式 NPU 上跑

**缺點**

- 最頂尖的能力通常仍在閉源模型（差距有縮小，但依任務而異）
- 要自己處理硬體（GPU 記憶體）、部署、維運、監控
- 安全護欄需要自己負責；權重一旦釋出就無法收回
- 訓練資料不透明，難以完全評估偏誤或版權風險

---

## 怎麼跑一個 Open-weight 模型？

常見工具：

| 工具 | 用途 |
|---|---|
| **Ollama** | 最簡單的本機執行，一行指令下載並跑 |
| **llama.cpp** | C/C++ 推論引擎，支援 GGUF 量化格式，CPU/GPU/Apple Silicon 都能跑 |
| **vLLM / SGLang** | 高吞吐量的伺服器端推論 |
| **Hugging Face Transformers** | Python 生態系標準，研究與微調常用 |
| **LM Studio** | 圖形介面的本機模型管理 |

範例：

```bash
# Ollama
ollama run llama3.1

# llama.cpp
./llama-cli -m model-Q4_K_M.gguf -p "What is an open-weight model?"
```

**硬體粗估**（FP16 下每十億參數約需 2 GB 記憶體）：

| 精度 | 7B 模型約需 | 70B 模型約需 |
|---|---|---|
| FP16 | ~14 GB | ~140 GB |
| INT8 | ~7 GB | ~70 GB |
| INT4（Q4） | ~4 GB | ~35–40 GB |

> 實際還要加上 KV cache 與 context 長度所需的記憶體。

---

## 重點整理

1. **Open-weight = 公開模型權重**，可下載、本機執行、微調。
2. **不等於 open-source**：訓練資料與流程通常不公開。
3. **授權差異大**，商用前一定要看 license。
4. 適合重視**隱私、客製化、成本控制、地端/邊緣部署**的場景。
5. 生態系成熟：Hugging Face + Ollama / llama.cpp / vLLM 就能上手。
