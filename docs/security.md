# 資安 / LLM 測試工具

## promptfoo
- 開源工具，用於 LLM 應用的評測（eval）與紅隊測試（red teaming）。
- **Prompt 評測**：對多組 prompt、模型、參數做批次比較，用測試案例與 assertion 檢查輸出品質，支援 CI 整合做回歸測試。
- **紅隊測試**：自動產生對抗性輸入，測試 prompt injection、jailbreak、資料外洩等風險。
- 可用設定檔（YAML）定義測試，或以 CLI / SDK 執行。
- 官網：https://www.promptfoo.dev/
- 原始碼：https://github.com/promptfoo/promptfoo
