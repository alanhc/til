# VAD 是什麼？Silero VAD 跟晶片效能有什麼關係？

## 1. VAD 是什麼

**VAD（Voice Activity Detection，語音活動偵測）** 做的是一個二元判斷：這一小段音訊裡**有沒有人在說話**。

```
麥克風 PCM ──► [切成 10~32 ms 的 frame] ──► VAD ──► speech_prob ∈ [0,1]
                                                   │
                                     > threshold ──┴──► 喚醒後面的大模型（KWS / ASR / LLM）
```

VAD 本身不理解內容，它是語音 pipeline 最前面的**守門員（gatekeeper）**：

| 下游 | VAD 的作用 |
|---|---|
| Wake word / KWS（"Alexa"） | 沒人說話時不跑 KWS，省電 |
| ASR（Whisper 等） | 把靜音切掉，只送有聲段，降低算力與幻覺 |
| VoIP / 會議 | 靜音時不傳封包（DTX）、控制降噪與回音消除 |
| 語音 Agent | 判斷使用者說完了沒（end-of-turn / barge-in） |

### VAD 的演進

1. **能量閾值 / 過零率**：最便宜，但噪音一大就誤判。
2. **統計模型 GMM**：代表是 **WebRTC VAD**，很輕，但在嘈雜環境準確度差。
3. **小型神經網路**：代表是 **Silero VAD**，準確度大幅提升，但需要真正的 NN 推論。

---

## 2. Silero VAD：一個典型例子

Silero VAD 是 Silero 團隊開源的（MIT License）預訓練 VAD 模型，現在是開源語音界的**事實標準**之一（faster-whisper、WhisperX、LiveKit、Pipecat 等都內建或預設使用）。

大致特徵：

- **模型很小**：約 1~2 MB，參數量在百萬級以下。
- **輸入**：16 kHz 下每次 512 samples（≈ 32 ms），8 kHz 下 256 samples。
- **架構**：前端 STFT 類特徵 → 小型 CNN encoder → LSTM（有 state，要跨 frame 保存 hidden state）→ 輸出語音機率。
- **格式**：PyTorch JIT 與 **ONNX**，所以很容易丟到各種 runtime（ONNX Runtime、TFLite 轉換、廠商 NPU SDK）。
- **官方宣稱**：單一 CPU thread 處理一個 chunk 約 **< 1 ms**。

> 重點：它**不是**「大模型」，而是**永遠在跑的超小模型**。這正是晶片廠關心它的原因。

---

## 3. 跟晶片效能的關係

Silero VAD 的算力需求很小，所以問題從來不是「跑不跑得動」，而是：

> **在 always-on 情境下，用最低功耗、最少資源、最穩定的延遲，一天 24 小時不停地跑。**

### 3.1 它是 always-on workload

VAD 必須**一直聽**。以 32 ms 一個 frame 計算：

```
1 秒   ≈ 31 次推論
1 小時 ≈ 112,500 次推論
1 天   ≈ 2,700,000 次推論
```

單次推論再便宜，乘上這個次數後，**待機功耗（standby power）**就會直接反映在電池續航上。對平板、手機、智慧音箱、TWS 耳機來說，這是規格表和評測上看得到的數字。

### 3.2 真正的指標：不是 TOPS，而是這些

| 指標 | 為什麼重要 |
|---|---|
| **每次推論能耗（µJ/inference）** | always-on 功耗 = 能耗 × 頻率，最直接影響續航 |
| **在哪個 core 上跑** | 大核 CPU / 小核 CPU / DSP / NPU / 低功耗 sensor hub，功耗差可達數量級 |
| **能不能讓 AP 睡覺** | 如果 VAD 跑在 AP 上，SoC 很難進深度睡眠；放到低功耗 DSP/MCU 才能讓主系統 suspend |
| **Latency 與 jitter** | 32 ms 一個 frame，推論必須遠低於 32 ms 且穩定，否則 buffer 累積、語音掉頭 |
| **記憶體佔用（SRAM）** | 低功耗島（LPI / always-on domain）通常只有幾百 KB SRAM，模型 + activation + LSTM state 要塞得進去，不能跑去喚醒 DRAM |
| **準確度（量化後）** | INT8 / INT16 量化後 false accept / false reject 不能變差太多，否則要嘛誤喚醒耗電、要嘛漏聽 |

### 3.3 Silero 對硬體的「刁鑽」之處

它雖小，但結構對某些 NPU 不友善，所以很適合當 benchmark：

- **LSTM / 有狀態 RNN**：很多 NPU 對 Conv 最佳化，對 recurrent op 的支援較弱，可能 **fallback 回 CPU**，反而更耗電。
- **Batch = 1、極小 tensor**：NPU 的啟動、DMA、driver 呼叫的 **overhead 可能比運算本身還大**。「NPU 比 CPU 快 10 倍」在這種模型上不一定成立。
- **STFT / 前處理**：若 NPU 不支援，要切回 DSP/CPU，產生跨 core 資料搬移。
- **高頻率呼叫**：每秒 31 次的 invoke，考驗的是 runtime 與 scheduler 的效率，而不只是 MAC 數量。

所以 Silero VAD 是一個很好的**「小模型、高頻率、有狀態」**代表性 workload，跟 ResNet / MobileNet 這種「大 batch、純 conv」的 benchmark 考驗的是完全不同的東西。

---

## 4. 為什麼 chip vendor 會想知道這個效能

### 4.1 客戶會拿它來比

OEM / ODM（例如做平板、音箱、車機的客戶）在選 SoC 時會問：

- 「你們的 always-on 語音方案，待機功耗多少 mW？」
- 「Silero VAD / 我們的 KWS 模型放在你們的 DSP/NPU 上，能耗與延遲是多少？」

開源、大家都在用的模型，自然會變成**跨廠商比較的共同基準**。拿不出數字，或數字比競品差，就可能在 design-win 階段輸掉。

### 4.2 驗證「低功耗 AI 島」的價值

各家 SoC 都有專門的低功耗子系統（audio DSP、sensor hub、micro-NPU 等）。晶片廠需要證明：

> 「把 VAD 從 AP 移到我們的低功耗 core 上，待機功耗可以從 X mW 降到 Y mW。」

Silero VAD 是驗證這條路徑（模型轉換 → 量化 → 部署 → 功耗量測）最具代表性的案例之一。

### 4.3 找出 SDK / toolchain 的缺口

拿 Silero VAD 過一遍自家的 AI SDK（模型轉換器、量化工具、runtime），常會發現：

- LSTM 不支援或被拆成很多小 op
- 某些 op fallback 到 CPU
- 量化後準確度崩掉
- 每次 invoke 的固定 overhead 太大

這些都是需要回饋給 compiler / runtime / 硬體設計團隊的具體問題。

### 4.4 語音 Agent 讓 VAD 更重要

LLM 語音助理（即時對話、可插話）流行後，VAD 不只決定「要不要醒」，還決定**「使用者說完了沒」**。這直接影響對話的反應速度，所以 VAD 的延遲與穩定度變成使用者體驗的一部分，而不只是功耗問題。

### 4.5 系統層面的連鎖效應

VAD 放錯地方，影響的不只它自己：

```
VAD 在 AP 上跑
  → AP 無法進 deep suspend
  → DRAM 無法進 self-refresh
  → 待機功耗高好幾倍
  → 電池續航評測難看
```

所以晶片廠關心的不只是「VAD 跑多快」，而是**「整個 always-on 音訊路徑的系統功耗」**，VAD 是這條路徑的起點。

---

## 5. 一句話總結

> **Silero VAD 是一個很小、但 24 小時不停跑的神經網路。**晶片廠關心的不是它需要多少 TOPS，而是**能不能在最省電的 core 上、用最少的 SRAM、以穩定的低延遲跑它，並讓系統其他部分安心睡覺**。它開源、普及、結構又有代表性（小 batch + LSTM + 高頻呼叫），所以成了客戶比較 SoC always-on AI 能力時很自然的基準。

---

## 附錄：如果要自己量測，可以看這些

| 項目 | 方法 |
|---|---|
| 單次推論延遲 | 在目標 core 上重複 invoke 數千次，看平均值與 P99 |
| 每次推論能耗 | 電源量測儀器量 rail 電流，扣掉 idle baseline |
| 系統待機功耗 | 開 / 關 VAD 各量一次整機 standby power |
| Op fallback | 看 SDK 的 profiling / partition log，確認哪些 op 不在 NPU 上 |
| 量化準確度 | 用同一組帶噪測試音檔，比較 FP32 與 INT8 的 ROC / F1 |
| 喚醒路徑 | 追 VAD 觸發 → 喚醒 AP → 啟動 ASR 的端到端延遲 |
