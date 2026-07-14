# 韌體測試流程

BMC 韌體驗證通常圍繞三件事展開：**test plan（測試計畫）→ functional testing（功能測試）→ report（測試報告）**。

functional testing

report

test plan

## 流程說明

1. **test plan（測試計畫）**：在測試前先定義測試範圍、對象版本、測試環境（硬體平台、連線方式）、通過標準與各項 test case。讓測試有依據且可重複。
2. **functional testing（功能測試）**：依 test plan 逐項驗證韌體功能是否符合規格，例如：
   - IPMI/Redfish 指令回應是否正確
   - 感測器讀值（溫度、電壓、風扇轉速）是否合理
   - 遠端開關機、SOL、韌體更新流程是否正常
   - 測試偏重「行為是否符合預期輸出」，而非內部實作。
3. **report（測試報告）**：彙整每個 test case 的 pass/fail、實際結果、log 與環境資訊，作為版本是否可釋出的判斷依據，也方便回歸追蹤。

## 補充

除功能測試外，完整驗證常再加上 stress test（長時間穩定度）、regression test（回歸測試）與 recovery test（斷電/更新失敗還原）。OpenBMC 上可用 `robot`（Robot Framework）撰寫自動化測試腳本。
