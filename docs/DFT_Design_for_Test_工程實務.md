# DFT（Design for Test）工程實務整理

> 給 IC 工程師的可測試性設計筆記：從為什麼要 DFT，到 scan、ATPG、BIST、boundary scan 的實作重點與量產考量。

---

## 一、DFT 到底在解決什麼問題

晶片流片（tape-out）之後，晶圓廠會把數百到上萬顆晶粒（die）製造出來。製造是物理過程，一定會有缺陷：微粒污染、光罩偏移、金屬短路或斷路、閘極氧化層破損等。這些缺陷會讓某些電晶體卡在 0 或卡在 1、讓某條連線斷掉或和鄰線橋接。

問題是：一顆現代晶片內部有數億個電晶體，但對外只有幾百到幾千支 pin。你沒辦法從外部接腳直接觀察或控制內部節點。如果只靠「跑功能測試看晶片會不會動」，覆蓋率極低、且很難定位故障。

DFT（Design for Test）就是在**設計階段主動加入額外電路與結構**，讓製造後的測試變得可控（controllable）、可觀察（observable）、快速、且覆蓋率高。核心代價是面積、功耗與少量效能開銷；換來的是量產可測性與良率篩選能力。

DFT 的三個衡量主軸：

- **Fault Coverage（故障覆蓋率）**：能偵測到的故障 / 全部可能故障。量產通常要求 stuck-at 95～99%+。
- **Test Cost（測試成本）**：ATE 測試時間、pattern 資料量、tester pin 數，直接影響每顆晶片的測試花費。
- **Test Area / Overhead**：DFT 邏輯佔的面積、繞線、時序影響。

---

## 二、故障模型（Fault Models）

DFT 測的不是「所有可能的物理缺陷」，而是把物理缺陷抽象成可計算的故障模型，讓 ATPG 工具能針對它生成 pattern。

| 故障模型 | 描述 | 主要抓什麼 |
|---|---|---|
| Stuck-at | 節點永久卡 0（SA0）或卡 1（SA1） | 最經典，抓開路/短路類靜態缺陷 |
| Transition / At-speed | 節點 0→1 或 1→0 轉態太慢 | 抓時序類、速度相關缺陷（delay defects） |
| Bridging | 兩相鄰節點短路 | 金屬層橋接 |
| Path Delay | 特定關鍵路徑延遲超標 | 針對 timing-critical path |
| IDDQ | 靜態電流異常偏高 | 抓漏電類缺陷（先進製程效果變差） |

實務上量產測試會混用：stuck-at 打底、transition/at-speed 補時序缺陷，先進節點再視情況加 path delay 或 cell-aware pattern。

---

## 三、Scan Design（掃描設計）— DFT 的地基

### 概念

Scan 是所有數位 DFT 的基礎。做法是把設計裡的一般正反器（flip-flop）替換成 **scan flip-flop**（多一個 mux 選擇輸入來源），再把它們串成一條或多條 **scan chain**。

每個 scan FF 有兩種模式：

- **Functional mode**：正常工作，D 來自原本的邏輯。
- **Shift mode**：D 來自前一個 scan FF 的輸出，整條鏈變成一個大移位暫存器。

### 測試流程（basic scan test）

1. **Scan-in / Shift**：把測試向量一位一位從 `scan_in` 移入整條鏈，設定所有 FF 的內部狀態（達成可控性）。
2. **Capture**：切回 functional mode，跑一個（或兩個）clock，讓組合邏輯的結果被 FF 抓住。
3. **Scan-out / Shift**：把抓到的結果一位一位移出到 `scan_out`，和預期值比對（達成可觀察性）。移出的同時通常也把下一組 pattern 移入。

這樣就把「深藏內部的節點」變成「從 scan chain 頭尾就能設定與觀察」。

### 實務重點

- **Scan insertion** 由工具（如 DFT Compiler / Tessent / Modus）在合成後自動完成，把 FF 換成 scan FF 並串鏈。
- **多條 scan chain**：鏈越長，shift 時間越久、測試時間越長。所以會切成多條平行鏈，鏈數受限於可用的 scan I/O pin 數。
- **Scan chain balancing**：讓每條鏈長度接近，避免最長鏈拖慢整體。
- **Shift 時的功耗**：shift 時大量 FF 同時翻轉，peak/average power 可能遠超功能模式，需注意 IR drop 與測試時的散熱。

---

## 四、ATPG（Automatic Test Pattern Generation）

### 做什麼

ATPG 是自動針對故障模型生成測試向量的工具與流程。輸入是 gate-level netlist + scan 結構 + 故障模型，輸出是一組 test pattern 與對應的 fault coverage 報告。

### 關鍵指標

- **Test Coverage**：可測故障中被測到的比例（實務最常看這個）。
- **Fault Coverage**：全部故障中被測到的比例。
- **ATPG Effectiveness**：工具處理每個故障的完成度。
- **Pattern count**：pattern 數量直接對應 ATE 測試時間與資料量，要在覆蓋率與成本間取捨。

### 提升覆蓋率的常見障礙

- **不可測故障（untestable）**：redundant logic、無法控制的節點。
- **黑盒子 / analog / memory**：需要另外處理（memory 用 MBIST，類比另走）。
- **未受約束的 X**：不確定值污染，需要用 X-masking 或適當 constraint 處理。

### 壓縮：Test Compression

pattern 資料量與測試時間是量產成本大宗。**Test compression**（如 Synopsys DFTMAX、Mentor/Siemens TestKompress、Cadence Modus）在 scan-in 端加 decompressor、scan-out 端加 compactor，用少數外部 scan pin 驅動內部大量短鏈，可把測試資料量與時間壓縮 10～100 倍。這是現代 SoC 的標配。

---

## 五、BIST（Built-In Self-Test）

把測試邏輯直接內建到晶片裡，讓晶片能自我測試，減少對外部 ATE pattern 的依賴。

### MBIST（Memory BIST）

記憶體密度高、缺陷模型特殊（不是 stuck-at 能涵蓋），且無法用一般 scan 測，所以幾乎所有內嵌 SRAM/ROM 都會配 MBIST：

- 內建 controller 產生 March 演算法序列（如 March C-）寫入/讀出比對，抓 stuck-at、transition、coupling、address decoder 等 memory 特有故障。
- 常搭配 **BIRA / BISR**（Built-In Redundancy Analysis / Repair）：有冗餘 row/column 時，量產可自動修復壞的記憶體位元，提高良率。

### LBIST（Logic BIST）

邏輯的自我測試，內建 **PRPG**（pseudo-random pattern generator，通常是 LFSR）產生亂數 pattern 灌入 scan chain，輸出用 **MISR**（multiple-input signature register）壓成一個 signature 比對。

- 優點：不需龐大外部 pattern、可在晶片上高速自測，適合 in-field / 開機自測（如車用安全 ISO 26262 的定期自檢）。
- 缺點：亂數 pattern 對 random-resistant fault 覆蓋率較低，常需插 test point 補強；設計裡不可有未受控的 X 源。

---

## 六、Boundary Scan（JTAG / IEEE 1149.1）

不是測晶片內部邏輯，而是測 **PCB 板上晶片與晶片之間的連線與焊點**。

- 在每個 I/O pin 加 boundary scan cell，串成邊界鏈。
- 透過標準 **TAP（Test Access Port）**：TCK、TMS、TDI、TDO（＋選配 TRST）四/五線介面，由 TAP controller 狀態機控制。
- 可做互連測試（interconnect test，抓開路/短路的焊接問題）、也常被複用作為晶片 debug、燒錄、以及進入內部 scan/BIST 的存取通道。
- 相關標準：IEEE 1149.1（基本）、1149.6（AC coupling / 差動）、1687（IJTAG，管理晶片內部大量 test instrument 的存取）。

---

## 七、典型 DFT 流程在設計鏈裡的位置

DFT 通常橫跨前端設計與後段測試，是兩者之間的橋樑：

1. **DFT 架構規劃**（RTL / 早期）：決定 scan 策略、compression 比、MBIST/LBIST 需求、JTAG 架構、test pin 規劃。
2. **RTL DFT check**：檢查可測性問題（unconnected clock/reset、無法控制的 clock gating、async path 等）並修 DRC。
3. **Scan insertion**（合成後）：插入 scan FF、串鏈、插 MBIST/BIST 邏輯。
4. **ATPG**：生成 pattern、看覆蓋率、迭代補強。
5. **Pattern 驗證與轉檔**：gate-level simulation 驗 pattern，轉成 ATE 能吃的格式（如 STIL / WGL）。
6. **量產測試（ATE）**：在測試機台上執行 test program，做 wafer sort 與 final test，篩掉壞晶片。
7. **Yield / 失效分析回饋**：從測試結果回饋良率與缺陷趨勢，必要時做 diagnosis 定位問題。

---

## 八、DFT 工程師在 chip vendor 裡的角色

在半導體公司（IC design house、IDM、或 fabless vendor），DFT 常是獨立的工程職能：

- **職責定位**：介於前端 RTL/合成團隊與後段 test/product engineering 之間，目標是「用最小面積、功耗、時序代價，換最高測試覆蓋率與最低量產測試成本」。
- **常用工具**：Synopsys（DFT Compiler、DFTMAX、TetraMAX/TestMAX ATPG）、Siemens EDA / Mentor（Tessent 系列：Scan、TestKompress、MBIST）、Cadence（Modus）。
- **需要的知識**：數位設計、時序、scan/ATPG 原理、故障模型、STA 基礎、ATE/test program 概念、以及跨團隊溝通（因為 DFT 會動到別人的設計）。
- **趨勢**：先進節點與大型 SoC 讓 hierarchical DFT、進階 compression、cell-aware ATPG、in-system test（車用/資料中心的 field test）、以及 IJTAG 管理變得越來越重要。

---

## 九、常見名詞速查

| 縮寫 | 全名 | 一句話 |
|---|---|---|
| DFT | Design for Test | 為了測試而在設計中加入的所有技術總稱 |
| Scan | Scan Design | 把 FF 串成移位鏈，讓內部可控可觀察 |
| ATPG | Automatic Test Pattern Generation | 自動生成測試向量 |
| BIST | Built-In Self-Test | 晶片內建自我測試 |
| MBIST | Memory BIST | 記憶體自測 |
| LBIST | Logic BIST | 邏輯自測（LFSR + MISR） |
| BISR | Built-In Self-Repair | 記憶體自我修復（配冗餘） |
| ATE | Automatic Test Equipment | 量產測試機台 |
| TAP | Test Access Port | JTAG 的存取介面 |
| DRC | Design Rule Check（DFT 語境） | 檢查可測性規則 |
| Stuck-at | Stuck-at Fault | 節點卡 0 / 卡 1 的故障模型 |
| IDDQ | Quiescent Supply Current | 用靜態電流異常抓漏電缺陷 |

---

*本文為工程實務導向的整理筆記，實作時請以所用 EDA 工具的官方流程與公司內部 methodology 為準。*
