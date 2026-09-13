---
sidebar_label: ATE（測試設備）
---

# ATE 是什麼：結構性測試的基礎設施

> 本文是半導體量產測試系列的一篇，全流程概觀見[〈半導體量產測試全景：CP、FT、SLT 與 ATE〉](./semiconductor-test-overview-cp-ft-slt-ate.md)。

## TL;DR

ATE（Automated Test Equipment，自動化測試設備）是半導體量產測試的核心機台：把預先產生的測試向量以電訊號打進晶片接腳，比對輸出是否符合預期。CP（晶圓測試）和 FT（最終測試）都跑在 ATE 上。它的力量來自結構性測試的理論完備——fault coverage 可以量化——以及秒級的測試速度；它的極限則是抓不到系統層級的互動缺陷，這是 SLT 存在的原因。

---

## 1. ATE 是設備，不是測試階段

初學者最常見的混淆：CP、FT、SLT 是測試流程中的「站點」，ATE 是其中 CP 和 FT 共用的「設備平台」。一套完整的 ATE 測試環境包含：

- **Tester（測試機台本體）**：提供電源、訊號產生與量測的硬體資源
- **介面硬體**：晶圓階段用探針卡（probe card），封裝品用 load board + socket，建立晶片與機台的電氣連接
- **Handler / Prober**：自動化取放設備——prober 移動晶圓對準探針，handler 抓取封裝品放進 socket
- **測試程式**：測試工程師在機台平台上開發的軟體，定義測項、判定準則與 binning 邏輯

## 2. 它怎麼測：DFT、ATPG 與結構性測試

ATE 測試的主體是**結構性測試（structural test）**：不驗證晶片「功能上做什麼」，而是驗證「電路結構有沒有做對」。這高度依賴設計階段就埋好的 DFT（Design for Test）架構：

- **Scan chain**：把晶片內部的暫存器串成移位鏈，讓 ATPG（Automatic Test Pattern Generation）工具產生的向量可以控制和觀測內部節點——等於把深埋在晶片裡的電路「攤開」給機台看。
- **MBIST（Memory Built-In Self-Test）**：記憶體區塊內建自我測試電路，機台只要下指令、收結果。
- **Fault model**：stuck-at、transition、bridging 等故障模型讓覆蓋率可以精確計算——「這組 pattern 覆蓋了 98.5% 的 stuck-at fault」是一個可以驗證的工程陳述。

這套理論體系是數十年的科學成果：它讓品質保證在電路複雜度指數成長的年代仍然可行、且成本可控。完備的 DFT 設計讓測試可以用最短時間篩出故障晶片——ATE 單顆測試時間通常以 10 秒為單位。

除了結構測試，ATE 也做 DC/AC 參數量測（漏電流、電壓準位、時序）、open/short 檢查，以及量測 Fmax/Vmin 等效能參數——後者直接用於 speed binning 和系統軟體 DVFS 的設定依據。

## 3. 市場格局

ATE 市場高度集中：**Advantest** 與 **Teradyne** 兩家合計超過七成市占，其中 Advantest 在 AI 與先進製程晶片的 ATE 供應上幾乎壟斷。Teradyne 常見機種如 J750（低成本）與 UltraFlex（高效能）；台灣的致茂（Chroma）則在亞洲市場快速成長。周邊的 handler 與 prober 則多由日系廠商（TEL、東京精密）主導。這種供應鏈集中度讓先進晶片的測試產能本身成為一種戰略資源。

## 4. ATE 的極限（以及為什麼有 SLT）

隨著晶片軟硬體複雜度上升，越來越多問題**無法抽象成故障模型**：

- 跨 IP block 在真實 clock/power/thermal 條件下的互動
- timing margin 勉強及格的邊際缺陷（在特定 workload 下才出錯，是 Silent Data Corruption 的主要來源之一）
- 韌體、driver、作業系統層級的軟硬體互動

理論上可以無限堆高 ATE 覆蓋率去逼近，但 pattern 數量、tester memory、測試時間的邊際成本呈指數上升。這就是 SLT 的切入點：不窮舉電路狀態，直接拿終端使用情境當測試內容。兩者是互補——而業界的長期方向，是把 SLT 攔到的失效模式回饋給 ATE 測項（shift left），持續縮小需要靠 SLT 兜底的範圍。

---

## References

1. 知乎, 「半导体测试概述」 — https://zhuanlan.zhihu.com/p/37363859
2. SemiVision Research, "Semiconductor IC Testing: A Comprehensive Analysis from Core Processes to Advanced Packaging Challenges" — https://tspasemiconductor.substack.com/p/semiconductor-ic-testing-a-comprehensive
3. Fountyl, "Semiconductor technology and equipment: chip testing and equipment" — https://www.fountyltech.com/news/semiconductor-technology-and-equipment-chip-testing-and-equipment/
4. Teradyne, "Emerging Technologies Are Driving System Level Test Adoption" — https://www.teradyne.com/2023/01/03/emerging-technologies-drive-system-level-test-adoption/
5. Semiconductor Engineering, "Strategies For Detecting Sources Of Silent Data Corruption" — https://semiengineering.com/strategies-for-detecting-sources-of-silent-data-corruption/
6. I. Polian et al., "Exploring the Mysteries of System-Level Test," arXiv:2103.06656 — https://arxiv.org/abs/2103.06656
