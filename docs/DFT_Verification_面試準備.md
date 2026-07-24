# DFT Verification Engineer 學習與面試準備筆記

> 以一份典型的「DFT Verification Engineer」職缺（JD）為藍本整理。重點說明：這個角色核心是**DFT 的驗證（simulation-based verification）**，不是純 DFT 設計。DFT 知識（Scan/ATPG/BIST/JTAG）在這類 JD 常被寫成加分項，真正的地基是驗證能力、debug、以及對 SoC 架構的理解。
>
> 設計端的對應筆記見 [DFT（Design for Test）工程實務整理](./DFT_Design_for_Test_工程實務.md)。

---

## 一、先看懂這個 JD 在找什麼人

把 JD 的職責與需求對照，可以歸納成四個能力群。準備時請照這個優先序投資時間。

| 能力群 | JD 對應句子 | 權重 |
|---|---|---|
| **驗證方法與 debug（核心）** | Strong debugging with RTL/Gate-level tracing (Verdi) + verification simulation (VCS)；verify at IP/cluster/full chip | ★★★★★ 必備、會被考 |
| **DFT 領域知識（差異化）** | Generating test patterns；Understanding of Scan/ATPG/BIST/JTAG is a plus | ★★★★ 加分但是差異化關鍵 |
| **SoC 架構常識** | Familiarity with SoC basic architecture (clock, reset, power rail, IO pad, package) | ★★★ 面試會問基本盤 |
| **腳本與流程自動化** | Collaborate with CAD to optimize simulation flow；Python/Perl/Tcl/C/C++ is a plus | ★★★ 加分、展現自動化能力 |

**一句話定位**：這是「用 VCS/Verdi 驗證 DFT 邏輯與 analog macro、產測試 pattern、並做 chip bringup」的職缺。你要證明的是——會驗證、會 debug 大型設計、懂 DFT 結構、能寫腳本把流程做順。

---

## 二、核心能力①：驗證方法與 Debug（VCS / Verdi）

這是整份 JD 最不能妥協的部分。「verify at IP level, cluster level, and full chip level」代表要能在不同抽象層次規劃與執行驗證。

### 驗證流程基本盤

- **Test planning / verification scope**：拿到 spec 後，定義要驗什麼、驗到什麼程度、用什麼 metric 收斂。JD 明確要你「determine verification scope, develop strategies, implement test planning」——這是 verification engineer 的核心軟實力。
- **層級化驗證（hierarchical verification）**：
  - *IP level*：單一 macro / block 獨立驗，環境小、跑得快、好定位。
  - *Cluster level*：數個 IP 整合後驗互動與介面。
  - *Full chip level*：整顆晶片，驗 top-level 連線、DFT mode 切換、pattern 灌入路徑。
- **收斂指標**：functional coverage、code coverage（line/toggle/FSM）、pattern pass/fail、DFT coverage 目標。

### VCS（Synopsys 模擬器）

- 編譯與模擬 RTL / gate-level netlist。
- 重點觀念：two-state vs four-state、`+define`、UCLI、跑 gate-level sim 時的 **SDF back-annotation**（時序反標）、以及 DFT pattern 的 gate-level simulation 驗證（把 ATPG 產出的 pattern 在 netlist 上重跑，確認和 ATE 預期一致）。

### Verdi（Synopsys debug / 波形工具）

- **RTL / Gate-level tracing**：JD 直接點名。要熟練用 Verdi 追訊號來源（active trace / driver tracing）、看 schematic、追一條錯訊號往回找根因。
- **波形 debug**：讀 FSDB、設定 signal、比對 expected vs actual、定位 X 的來源（X-propagation 在 DFT/gate sim 裡是常見殺手）。
- 面試常見情境題：「一條訊號在 gate sim 出現 X，你怎麼一步步找出來源？」——要能講出 driver trace → clock/reset 檢查 → uninitialized FF → SDF / setup-hold 的排查邏輯。

---

## 三、核心能力②：DFT 領域知識（差異化重點）

雖然 JD 寫「is a plus」，但職稱就叫 DFT Verification，這塊懂得越深越能拉開差距。以下是必須能清楚講出的四大結構（可搭配 [DFT 工程實務](./DFT_Design_for_Test_工程實務.md) 一起看）。

- **Scan**：把 FF 換成 scan FF 串成 scan chain，透過 shift-in → capture → shift-out 讓內部可控可觀察。驗證角度要懂：scan chain 連通性怎麼驗、shift/capture 時序、scan mode 下的 clock 控制。
- **ATPG**：自動產生測試 pattern。JD 的「generating test patterns」多半就是這件事。要懂 fault model（stuck-at、transition/at-speed）、test coverage、以及把 pattern 拿回 gate-level sim 驗證。
- **BIST**：MBIST（記憶體自測，March 演算法）、LBIST（LFSR + MISR 邏輯自測）。驗證角度要懂 BIST controller 的啟動、run、signature 比對怎麼在 sim 裡確認。
- **JTAG / Boundary Scan（IEEE 1149.1）**：TAP controller 狀態機（TCK/TMS/TDI/TDO）、instruction/data register 存取。DFT 常透過 JTAG 進入 scan/BIST，驗證時要驗 TAP 的存取路徑正確。

> 這類 JD 常見的一句特色需求：**「Verify our custom analog macros」**。DFT 對 analog/mixed-signal macro 常用 wrapper、測試模式切換、以及把類比區塊在 DFT mode 下的行為模型化來驗。準備時可補一點 mixed-signal DFT / analog test（如何在數位測試框架下處理類比巨集）的概念。

---

## 四、核心能力③：SoC 基本架構

JD 明列「clock, reset, power rail, IO pad, package」，這是面試基本盤，答不出來會扣分。

- **Clock**：clock tree、clock domain、CDC（跨時脈域）、DFT 下的 clock 控制（OCC — on-chip clock controller，做 at-speed test 時切換 functional clock 與 shift clock）。
- **Reset**：async/sync reset、reset 順序、reset 在 scan/bringup 時的狀態。
- **Power rail**：多電壓域、power domain、UPF/CPF 概念、DFT 在低功耗設計下的測試（如 isolation cell、power-aware ATPG）。
- **IO pad / Package**：pad ring、IO 種類、boundary scan 對 IO 的測試、package 對 bringup 的影響（bump/ball map、訊號怎麼拉出來量）。

---

## 五、核心能力④：腳本與流程自動化

JD：「Collaborate with CAD team to optimize & smooth our simulation flow」＋「Python/Perl/Tcl/C/C++ is a plus」。這反映實務上 DFT verification 有大量流程要自動化。

- **Tcl**：EDA 工具（VCS、Verdi、DFT 工具）幾乎都用 Tcl 當 scripting 介面，優先掌握。
- **Python / Perl**：處理 log parsing、pattern/report 分析、產環境、批次跑 regression、整理結果。
- **C/C++**：偶爾用在 testbench 的 DPI、或效能敏感的工具。
- 展現方式：面試時舉一個「我寫了什麼腳本把某個手動流程自動化、省了多少時間 / 抓到什麼問題」的具體例子，比列語言清單有力得多。

---

## 六、Chip Bringup（把矽帶起來）

JD：「Generating test patterns and perform chip bringup」。Bringup 是晶片從 fab 回來後，第一次在實驗室/ATE 上讓它動起來的過程。

- **DFT 在 bringup 的角色**：scan / JTAG 通常是第一批被驗的東西，因為它們是「能不能存取晶片內部」的入口。scan chain 通不通、JTAG IDCODE 讀不讀得到，是 bringup 早期的關鍵里程碑。
- **Pattern 的角色**：把 ATPG / functional pattern 在 ATE 上跑，比對實際矽的行為，篩出製造缺陷、也回頭驗證 DFT 結構正確。
- **Debug 迴路**：silicon 出問題 → 用 pattern + Verdi/波形 + design 知識定位是設計 bug、DFT bug、還是製造缺陷 → 回饋修正。這正是這個職缺跨 Design / Integration / TE / CAD 團隊協作的原因。

---

## 七、學習路徑建議（依 JD 優先序）

1. **先打穩驗證與 debug**：熟 VCS 跑 RTL/gate sim、熟 Verdi 做 signal tracing 與波形 debug。這是會被直接考的核心。
2. **補 gate-level 與時序概念**：SDF back-annotation、X-propagation、setup/hold，是 DFT 驗證常踩的地雷。
3. **建立 DFT 結構全貌**：Scan / ATPG / BIST / JTAG 各自「是什麼、怎麼驗」。（可用 [DFT 工程實務](./DFT_Design_for_Test_工程實務.md) 當底）
4. **SoC 架構常識**：clock/reset/power/IO/package 各能講出與 DFT 的關係。
5. **腳本自動化**：Tcl 優先，Python 處理 log/report，準備一個自動化的具體故事。
6. **英文**：JD 要求 fluent English communication——技術面試與跨國團隊協作都會用到，準備能用英文講清楚上面每個主題。

---

## 八、面試可能被問到的方向（自我檢查清單）

- 你會怎麼規劃一個 block 的驗證 scope 和 coverage 收斂？
- gate-level sim 出現 X，你的 debug 步驟？（Verdi trace 怎麼用）
- scan chain 連通性怎麼驗？shift 和 capture 的差別？
- ATPG 產出的 pattern 你怎麼在 sim 裡驗證它正確？
- stuck-at 和 at-speed（transition）測試差在哪？為什麼需要 OCC？
- JTAG TAP controller 的基本運作？怎麼透過它進 scan/BIST？
- 低功耗設計（多 power domain）對 DFT 測試有什麼影響？
- 你寫過什麼腳本改善驗證/模擬流程？解決了什麼？
- Chip bringup 時，DFT 相關的第一批要驗什麼？為什麼？

---

## 九、名詞速查（對應 JD）

| 縮寫 | 全名 | 對這個 JD 的意義 |
|---|---|---|
| VCS | Verilog Compiler Simulator | JD 指定的模擬工具，跑 RTL/gate sim |
| Verdi | — | JD 指定的 debug 工具，做 RTL/gate tracing |
| ATPG | Automatic Test Pattern Generation | 對應「generating test patterns」 |
| Scan | Scan Design | DFT 地基，驗連通性與 shift/capture |
| BIST | Built-In Self-Test | MBIST/LBIST，驗自測邏輯 |
| JTAG | IEEE 1149.1 Boundary Scan | 晶片內部存取入口，bringup 關鍵 |
| OCC | On-Chip Clock Controller | at-speed test 的時脈切換 |
| SDF | Standard Delay Format | gate sim 時序反標 |
| CDC | Clock Domain Crossing | SoC 架構常識，clock 相關 |
| TE | Test Engineering | JD 提到的協作團隊（量產測試） |
| Bringup | Chip/Silicon Bringup | 矽回來後第一次點亮與驗證 |

---

*本筆記是照著一份 JD 反推的準備導向整理，不代表任何公司的實際做法。實際面試與工作請以該公司內部 methodology 與所用工具版本為準。*
