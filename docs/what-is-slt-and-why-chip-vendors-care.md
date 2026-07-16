---
sidebar_label: SLT 系統級測試
---

# SLT 是什麼？為什麼對 Chip Vendor 這麼重要

> 本文是半導體量產測試系列的一篇，全流程概觀見[〈半導體量產測試全景：CP、FT、SLT 與 ATE〉](./semiconductor-test-overview-cp-ft-slt-ate.md)。

## TL;DR

SLT（System-Level Test，系統級測試）是晶片量產測試流程的最後一道關卡：不再對晶片「打測試向量」，而是把晶片放進一個貼近終端產品的系統環境，實際開機、跑韌體與作業系統、驅動 I/O，驗證它「當成產品用起來是好的」。對 chip vendor 而言，SLT 的價值不在於取代 ATE，而在於攔截 ATE 結構性測試抓不到的漏網缺陷（test escape），把出貨品質壓到客戶要求的 DPPM 水準——因為缺陷越晚被發現，成本越高，而最貴的發現地點就是客戶的產線和終端使用者手上。

---

## 1. SLT 在測試流程中的位置

半導體量產測試通常分成幾個 insertion（測試站點）：

```
Wafer 製造
   │
   ▼
CP (Chip Probe / Wafer Sort)   ← 晶圓階段，ATE 打測試向量，篩掉壞 die
   │
   ▼ 封裝
FT (Final Test)                 ← 封裝後，ATE 再測一次，抓封裝製程引入的缺陷
   │
   ▼
SLT (System-Level Test)         ← 放進模擬終端系統的環境，實際開機運作
   │
   ▼
出貨給客戶（OEM / ODM / Hyperscaler）
```

CP 和 FT 都在 ATE（Automated Test Equipment）上進行：測試工程師事先產生 test pattern（例如 ATPG 產生的 scan pattern），機台把電訊號打進 DUT（Device Under Test），比對輸出。這類「結構性測試」（structural test）有完整的理論基礎——fault model、fault coverage 都可以量化計算，數十年來支撐了整個產業的品質保證。

SLT 則完全不同：它是「應用導向」的功能測試。以手機 SoC 為例，SLT 就是把晶片放到一塊代表性的手機主機板上，開機、載入作業系統、跑目標應用情境。測試的不是「電路結構對不對」，而是「這顆晶片組成系統之後能不能正常工作」——包括韌體、軟體、I/O 協定堆疊、記憶體子系統、電源與熱條件的真實互動。

---

## 2. 為什麼 ATE 測過了還會有漏網之魚

這是理解 SLT 存在意義的核心問題。ATE 的結構性測試理論上覆蓋率很高，但有幾類缺陷它先天抓不到：

**（1）跨 IP block 的互動缺陷。** 現代 SoC 整合了 CPU cluster、GPU、NPU、modem、各種 I/O IP。ATE 的 scan test 把電路拆成可控可觀測的結構來驗證，但 IP 與 IP 之間在真實 clock/power/thermal 條件下的互動——不同電源域切換、DVFS 動態調頻、跨 clock domain 的資料傳遞——很難用預先產生的向量完整涵蓋。

**（2）邊際缺陷（marginal defect）。** 有些晶片電性上「勉強及格」：timing margin 偏低但沒有低到讓 scan test fail。這種晶片在 ATE 上全數通過，卻可能在真實 workload 的特定電壓/溫度/資料組合下出錯。近年資料中心業界高度關注的 SDC（Silent Data Corruption，靜默資料損毀）很大一部分就源自這類缺陷——晶片不會當機，只是默默算錯，而且往往需要特定的指令序列和資料模式才會觸發。

**（3）軟硬體互動的缺陷。** 開機流程（boot chain）、韌體載入、driver 初始化順序——這些行為根本不存在於 ATE 的測試模型裡，只有真的開機才測得到。

**（4）先進封裝引入的新失效模式。** Chiplet、2.5D/3D 封裝讓「每顆 die 都是 known-good-die」不再等於「組起來是 known-good-system」。die-to-die interconnect、封裝應力、熱耦合都是新的缺陷來源，而這些只在系統層級的運作條件下才會顯現。

理論上你可以無限堆高 ATE 的 fault coverage 來逼近這些缺陷，但覆蓋率超過某個程度後，pattern 數量、測試時間、tester memory 的邊際成本呈指數上升。SLT 提供了另一條路：不去窮舉電路狀態，直接用終端使用情境當測試內容。

---

## 3. 對 Chip Vendor 來說，SLT 為什麼重要

### 3.1 DPPM 是寫進合約的承諾

Chip vendor 出貨給客戶時，品質水準是以 DPPM（Defective Parts Per Million，每百萬顆的不良數）量化承諾的。汽車、資料中心、高階手機這些應用對 DPPM 的要求極為嚴苛——汽車客戶動輒要求個位數 DPPM。ATE 測試把 DPPM 壓到某個水準之後就會遇到天花板，剩下的 escape 只有 SLT 這種模擬實際運作的測試才攔得住。換句話說：**SLT 是 vendor 兌現 DPPM 承諾的最後手段。**

### 3.2 缺陷逃逸的成本是乘數級的

一顆壞晶片如果在 CP 就被篩掉，損失是一顆 die；如果逃到 FT 才被抓到，多賠上封裝成本；如果逃出廠、在客戶的 SMT 產線上才發現，客戶要拆板重工、可能停線、vendor 要處理客訴與 RMA；如果一路逃到終端使用者手上，代價就是 field return、品牌傷害，在汽車或資料中心情境甚至是安全事故或大規模服務異常。測試成本歷史上約占晶片總成本的 2%，且隨複雜度持續上升——但相對於 quality escape 在下游引爆的成本，這仍然是便宜的保險。

### 3.3 大客戶正在把系統層級的品質要求推回 vendor

這幾年一個明顯的趨勢：hyperscaler（Meta、Google 等）在自家機房大規模觀察到 SDC 之後，把失效特徵回饋給 SoC 供應商，要求 vendor 在 SLT 加入針對性的測試內容（例如提高運算資料隨機性的 bare-metal 測試程式）。汽車 Tier-1 也一樣，會在進料品管做自己的系統級驗證。這意味著 SLT 不再只是 vendor 內部的品管手段，而是**客戶關係的一部分**——客戶在現場發現的問題會直接變成你的 SLT 測項需求。

### 3.4 SLT fail 是回饋設計與測試的閉環資料

業界目前常見的策略是「Shift Right + Shift Left」：先在 SLT 攔下系統級失效（shift right），再把失效模式回饋給 ATE pattern 和設計規則（shift left），形成閉環優化。SLT 抓到的 fail 對 vendor 有雙重價值——短期攔截這一顆壞品，長期則揭露「哪類缺陷正在逃過前面的測試站」，據此補強 ATE 測項、甚至修改下一代設計。SLT 還有一個 ATE 難以取代的除錯優勢：當客戶回報某個使用情境會出錯時，SLT 可以直接把該情境做成測項立即部署，不需要先做完整的故障分析把問題追到電晶體層級。

### 3.5 SLT 的測試內容，本質上是平台軟體

這點對做系統整合/BSP 的人特別有感：SLT 跑的東西——bootloader、kernel、driver、壓力測試 workload——就是平台軟體團隊每天在維護的那套東西。SLT 測試內容的品質直接取決於 vendor 對自家軟體堆疊的掌握程度。一個 SLT fail 的 triage 也經常需要跨硬體與軟體的 log 分析能力：到底是矽的邊際缺陷、板子的問題，還是韌體的 race condition？這是 chip vendor 內部測試工程與平台軟體工程少數天然交會的地方。

---

## 4. 代價與限制：SLT 不是免費的

SLT 的重要性不代表它沒有問題，vendor 導入時面對的權衡很現實：

**測試時間長一到兩個數量級。** ATE 測試時間以 10 秒為單位，SLT 以 1–10 分鐘為單位（開機本身就要時間）。要維持產能與成本，必須靠大規模平行化——現代 SLT 測試設備可以做到數百個 test site 同時測試（業界方案已有高達 720 個平行站點的整合測試單元）。

**測試設備高度客製。** SLT 的載板本質上是一塊「模擬終端產品」的板子，隨產品應用而異，經常由晶片公司自行設計，不像 ATE 有標準化的商用平台。

**覆蓋率無法量化。** 結構性測試有 fault model 和 coverage 數字；SLT 沒有等價的理論框架，你很難回答「這套 SLT 測項的缺陷覆蓋率是多少」，也難以系統性地判斷測項該加什麼、能減什麼。這是學界公認 SLT 目前最大的方法論缺口。

**Fail 難以除錯。** SLT fail 只告訴你「系統在某個情境下不對」，從這裡追到根因（矽缺陷？板級問題？軟體 bug？）需要大量跨領域的分析工作。

因應成本壓力，業界的方向是 **adaptive SLT**：不是每顆晶片都跑完整 SLT，而是根據前段測試資料（parametric 數據、wafer 位置等）用預測模型給每顆晶片打上 DPPM 風險標籤，高風險的跑完整測項、低風險的跑精簡版甚至跳過，在測試成本與 DPPM 之間動態取捨。隨著 AI 加速器與 chiplet 架構讓測試負擔持續膨脹，測試內容在 wafer sort 到 SLT 各站點之間的動態分配，正在成為新的產業課題。

---

## 5. 小結

| 面向 | ATE (CP/FT) | SLT |
|---|---|---|
| 測試性質 | 結構性測試，打預生成向量 | 功能性測試，模擬終端使用 |
| 理論基礎 | fault model / coverage 可量化 | 無統一 coverage 理論 |
| 單顆測試時間 | ~10 秒級 | 1–10 分鐘級 |
| 擅長抓 | 電晶體級缺陷、製程缺陷 | 跨 IP 互動、邊際缺陷、軟硬體互動 |
| 對 vendor 的意義 | 品質的主力防線 | DPPM 承諾的最後防線、客戶回饋的承接點 |

對 chip vendor 來說，SLT 的重要性可以濃縮成一句話：**ATE 保證晶片的電路是對的，SLT 保證晶片作為產品是好的——而客戶買的是後者。**

---

## References

1. Teradyne, "System Level Test" — https://www.teradyne.com/system-level-test/
2. Introspect Technology, "What Is SLT?" — https://introspect.ca/blog/what-is-system-level-test-or-slt/
3. Teradyne, "Emerging Technologies Are Driving System Level Test Adoption" — https://www.teradyne.com/2023/01/03/emerging-technologies-drive-system-level-test-adoption/
4. Semiconductor Engineering, "Mission-Critical Devices Drive System-Level Test Expansion" — https://semiengineering.com/mission-critical-devices-drive-system-level-test-expansion/
5. Semiconductor Engineering, "Strategies For Detecting Sources Of Silent Data Corruption" — https://semiengineering.com/strategies-for-detecting-sources-of-silent-data-corruption/
6. Semiconductor Engineering, "System Level Test — A Primer" — https://semiengineering.com/system-level-test-a-primer/
7. H. H. Chen et al., "Adaptive test method on production system-level testing (SLT) to optimize test cost, resources and defect parts per million (DPPM)," IEEE — https://ieeexplore.ieee.org/document/8373239
8. I. Polian et al., "Exploring the Mysteries of System-Level Test," arXiv:2103.06656 — https://arxiv.org/abs/2103.06656
9. SemiVision Research, "Semiconductor IC Testing: A Comprehensive Analysis from Core Processes to Advanced Packaging Challenges" — https://tspasemiconductor.substack.com/p/semiconductor-ic-testing-a-comprehensive
10. EDN, "How AI is driving a new paradigm in test distribution" — https://www.edn.com/how-ai-is-driving-a-new-paradigm-in-test-distribution/
11. Electronics360, "Chip complexity drives surge in system-level testing" — https://electronics360.globalspec.com/article/23099/chip-complexity-drives-surge-in-system-level-testing
