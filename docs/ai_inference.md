# 本機 LLM 推論工具

在本機執行 LLM 推論的常見工具比較，底層多半基於 `llama.cpp`。

- **lm studio**：桌面 GUI 應用，方便下載模型、切換與試玩，適合個人在本機互動使用。
- **ollama**：以指令列與 API server 為主，適用多使用者，方便部署成服務讓多端存取。
- 上面兩者底層都是 llama.cpp（負責量化模型的 CPU/GPU 推論）。
- **llama.cpp**：以 C/C++ 實作的推論引擎，支援 GGUF 量化模型，是上述工具的核心。
- **jan**：有點像 lm studio，但 apache licence（開源、可離線），底層同樣是 llama.cpp。 https://www.jan.ai/

> 選型概念：要 GUI 試玩選 lm studio 或 jan；要開源選 jan；要當服務給多人/程式呼叫選 ollama。
