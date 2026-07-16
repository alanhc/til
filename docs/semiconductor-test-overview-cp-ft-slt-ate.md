---
sidebar_label: 半導體測試全景
---

# 半導體量產測試全景：CP、FT、SLT 與 ATE

## TL;DR

一顆晶片從晶圓出廠到交到客戶手上，要經過一連串測試站點（test insertion）：**CP**（晶圓測試）在封裝前篩掉壞 die，**FT**（最終測試）在封裝後驗證成品，**SLT**（系統級測試）在出貨前模擬終端使用情境做最後把關。前兩者在 **ATE**（自動化測試設備）上執行結構性測試，SLT 則是功能性的系統測試。整個測試策略的核心是一場經濟學：**缺陷越晚被發現越貴**，所以每個站點的任務是在自己這一關、用最低的成本，攔下該攔的缺陷。

---

## 1. 全流程一張圖

```
晶圓製造 (Fab)
   │
   ├─ WAT / PCM ──── 測切割道上的 test key，監控「製程」是否穩定（不是測產品）
   ▼
CP (Chip Probing / Wafer Sort)
   │                 探針卡扎裸 die 接點 → ATE 測試 → 產出 wafer map 標記好壞
   ▼
封裝 (Assembly)      只取 good die 封裝
   │
   ▼
FT (Final Test)
   │                 封裝品放進 socket → ATE 測試 → 抓封裝缺陷 + 分 bin/grade
   ▼
SLT (System-Level Test)
   │                 放進模擬終端產品的板子 → 開機跑軟體 → 攔 ATE 漏網缺陷
   ▼
出貨（Tray / Tube / Reel）→ 客戶 SMT 上板
```

各站點驗證的對象不同，這是最容易記的框架：

- **WAT 驗 fab 的製程**（電性參數監控，測的是 test key 不是產品）
- **CP 驗晶圓的良率**（順便省下封壞品的錢）
- **FT 驗封裝的良率**（封裝製程也會引入缺陷）
- **SLT 驗「當成產品用」的品質**（軟硬體一起上）

---

## 2. 兩種測試哲學：結構性 vs. 功能性

理解這套流程，關鍵是先分清楚兩種根本不同的測試方法：

**結構性測試（Structural Test）**——CP 和 FT 的主體。不關心晶片「功能上在做什麼」，而是驗證「電路結構有沒有做對」。依賴設計階段埋好的 DFT（Design for Test）電路：scan chain 讓 ATPG 工具產生的測試向量可以控制與觀測內部節點，MBIST 讓記憶體自我測試。它的最大優點是**理論完備**：有 fault model（如 stuck-at、transition fault），fault coverage 可以精確計算，測試時間短（秒級）。

**功能性測試（Functional Test）**——SLT 的主體。直接模擬終端使用情境：開機、跑作業系統、操作真實 workload。它抓的是結構性測試先天抓不到的東西——跨 IP 互動、邊際缺陷、軟硬體互動——但代價是**沒有 coverage 理論**、測試時間長（分鐘級）、fail 難以除錯。

ATE 是執行結構性測試的機台（也能跑部分功能測試），SLT 則通常跑在客製化的類產品板子上。兩者是互補關係，不是替代關係。

---

## 3. 測試站點的經濟學

每加一個 test insertion，測試成本就顯著上升，所以測試工程的核心課題是：**用最少的站點達到客戶要求的 DPPM（每百萬顆不良數）**。幾個實務上的取捨：

**「十倍法則」的成本階梯。** 壞 die 在 CP 被攔下，損失一顆裸 die；逃到 FT 才被攔下，多賠封裝費；逃出廠到客戶產線，是拆板重工和客訴；逃到終端使用者手上，是 field return 和品牌傷害。這決定了「能早測就早測」的大原則。

**但早期站點有物理限制。** CP 階段探針卡的接觸電阻和寄生電感較大，高頻測試受限（一般壓在 50–100 MHz 以內），大電流測試探針也承受不了——這些項目只能留給 FT。所以 CP 的重點放在 scan/MBIST 這類高故障率的結構測試，目標是在晶圓階段就篩出九成以上的缺陷，不浪費封裝與 FT 的成本。

**有些站點可以省。** 低單價產品、製程成熟良率穩定時，有些公司會省略 CP 直接封裝（俗稱盲封，風險自負）；反過來，WLCSP（晶圓級封裝）產品可能 CP 測完切割就直接出貨，沒有傳統 FT。SLT 則是複雜 SoC、車用、資料中心等高品質要求產品才加的站點——而且業界的長期目標其實是透過持續提高 ATE 覆蓋率，最終把 SLT 精簡甚至移除，因為它又慢又貴。

**測試結果不只是 pass/fail。** FT/CP 階段會量測 Fmax（最高工作頻率）、Vmin（最低工作電壓）等參數，用來做 speed binning（同一顆設計分成不同等級販售）以及系統軟體 DVFS 的設定依據。測試站點同時是產品分級的來源。

---

## 4. 四個角色的對照表

| | ATE | CP | FT | SLT |
|---|---|---|---|---|
| 是什麼 | 測試**機台**（設備） | 測試**站點**（晶圓階段） | 測試**站點**（封裝後） | 測試**站點**（出貨前） |
| 測試對象 | — | 裸 die（整片晶圓） | 封裝好的晶片 | 封裝好的晶片＋系統環境 |
| 連接方式 | — | 探針卡（probe card） | Load board + socket | 客製系統板 + socket |
| 測試性質 | 執行結構性測試為主 | 結構性測試 | 結構性＋部分功能測試 | 功能性測試 |
| 單顆時間 | — | 秒級 | 秒級 | 分鐘級 |
| 主要目的 | — | 封裝前篩壞品、監控晶圓良率 | 驗封裝品質、分 bin 出貨 | 攔漏網缺陷、壓 DPPM |
| 可否省略 | — | 視產品（低價品可能省） | 幾乎必做 | 高品質要求產品才加 |

（ATE 放在表裡是刻意的：初學者最常見的混淆就是把 ATE 當成一個測試「階段」。它不是——它是 CP 和 FT 共用的設備平台。）

---

## 5. 從 chip vendor 的角度看整條線

對 chip vendor 來說，這條測試流水線同時在做四件事：

1. **品質過濾**：一層層把缺陷攔在出貨之前，兌現對客戶的 DPPM 承諾。
2. **良率歸因**：CP 的結果歸因給 fab，FT 的結果歸因給封裝廠，SLT 的結果暴露前面所有站點的覆蓋缺口——每一站都是供應鏈品質的度量衡。
3. **產品分級**：Fmax/Vmin binning 直接決定同一顆設計能賣出幾個 SKU、每個 SKU 的定價。
4. **閉環回饋**：SLT 攔到的 fail 回饋給 ATE 測項與下一代設計（shift right + shift left），持續縮小 escape。

各站點的深入介紹，見獨立文章：

- [ATE 是什麼：結構性測試的基礎設施](./what-is-ate.md)
- [CP 是什麼：晶圓測試](./what-is-cp-wafer-test.md)
- [FT 是什麼：最終測試](./what-is-ft-final-test.md)
- [SLT 是什麼：為什麼對 Chip Vendor 這麼重要](./what-is-slt-and-why-chip-vendors-care.md)

---

## References

1. Fountyl, "Semiconductor technology and equipment: chip testing and equipment" — https://www.fountyltech.com/news/semiconductor-technology-and-equipment-chip-testing-and-equipment/
2. 知乎, 「半导体测试概述」 — https://zhuanlan.zhihu.com/p/37363859
3. 優分析, 「【封測】測試市場的三大基本分類」 — https://uanalyze.com.tw/articles/141865423
4. 每日頭條, 「晶片測試的幾個術語及解釋（CP、FT、WAT）」 — https://kknews.cc/news/rzg8qjr.html
5. 電子技術應用, 「芯片的几个重要测试-CP、FT、WAT」 — https://chinaaet.com/article/3000162517
6. SemiVision Research, "Semiconductor IC Testing: A Comprehensive Analysis from Core Processes to Advanced Packaging Challenges" — https://tspasemiconductor.substack.com/p/semiconductor-ic-testing-a-comprehensive
7. Teradyne, "System Level Test" — https://www.teradyne.com/system-level-test/
8. Semiconductor Engineering, "Mission-Critical Devices Drive System-Level Test Expansion" — https://semiengineering.com/mission-critical-devices-drive-system-level-test-expansion/
