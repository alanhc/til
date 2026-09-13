# Post-Silicon Validation 入門：晶片回來之後，我們在做什麼

## 一、先講一個場景

假設你是一家 CPU 公司的工程師。設計團隊花了兩年，寫了幾千萬行 RTL，跑了幾十萬個 regression test，模擬結果全綠。專案送去晶圓廠，三個月後，第一批晶片（first silicon）裝在盒子裡送到辦公室。

大家圍在實驗室裡，把晶片插上測試板，按下電源。

**然後呢？**

「然後」的這一整段，就是 post-silicon validation（矽後驗證，業界常簡稱 post-Si）。

---

## 二、Pre-Silicon vs. Post-Silicon：兩個世界

理解 post-Si 最快的方式，是先看它跟 pre-silicon 的差別。

| | Pre-Silicon（矽前） | Post-Silicon（矽後） |
|---|---|---|
| 驗證對象 | RTL 程式碼、gate-level netlist | 實體晶片 |
| 平台 | Simulator、Emulator、FPGA prototype | 真實硬體 + 測試板 |
| 執行速度 | 幾 Hz ~ 幾 MHz | 全速（GHz） |
| 可觀測性 | **極高** — 任何內部訊號、任何 cycle 都看得到 | **極低** — 只有 pin、debug port、有限的 on-chip trace |
| 可重現性 | 完全確定性，同樣輸入必定同樣結果 | 受溫度、電壓、製程變異影響，bug 可能偶發 |
| 修 bug 成本 | 改一行 code，重跑 | 一次 respin 數個月 + 數百萬美金 |
| 能跑的東西 | 小型 directed test | 完整 OS、真實應用、壓力測試 |

這張表其實只講了一件事：

> **Pre-silicon 什麼都看得到，但跑不快；post-silicon 跑得飛快，但什麼都看不到。**

這個「速度 vs. 可觀測性」的取捨，決定了 post-Si 這個職位所有的工作方法。

### 為什麼 pre-silicon 做不完？

常見的誤解是「模擬做得夠好就不需要 post-Si」。實際上做不到，原因有幾個：

1. **State space 太大**。一顆現代 SoC 的合法狀態組合遠超過任何模擬能覆蓋的量。Pre-Si 靠的是 coverage model 挑重點打，一定會有漏網。
2. **模擬跑不到「深度」**。開機到 Linux login prompt，在 RTL simulator 上可能要跑幾個月；在真晶片上是幾秒鐘。很多 bug 要跑幾十億個 cycle 才會浮現。
3. **類比與電氣行為模擬不出來**。PLL jitter、SerDes eye diagram、IR drop、電源雜訊、溫度梯度——這些在 RTL 世界根本不存在。
4. **製程變異是真的**。同一張光罩出來的晶片，快的跟慢的可以差 20%。慢角落（slow corner）的晶片在特定電壓會掛，快角落不會。
5. **Model 本身可能是錯的**。Memory model、IP vendor 給的 behavioral model 跟真實矽的行為對不上，是很常見的 bug 來源。

---

## 三、Post-Si 的工作流程

### 階段 0：Pre-Si 準備期（晶片還沒回來）

好的 post-Si 團隊在晶片回來前半年就開始準備了。這段時間做的事：

- **寫測試程式**：bring-up script、self-test、stress test，先在 emulator 或 FPGA 上驗證測試本身是對的
- **設計 debug 能力（DFD, Design-for-Debug）**：這一點很關鍵。晶片上要放什麼 trace buffer、要拉出哪些訊號到 debug port、要不要放 on-chip logic analyzer——這些都必須在 tape-out 前決定。**Tape-out 之後就沒得加了。**
- **準備測試板與環境**：validation board、power supply、thermal chamber、ATE program、量測儀器
- **建立 pre-Si / post-Si 的測試共用架構**：理想上同一份 test content 兩邊都能跑，這樣 post-Si 找到的 bug 可以拿回 pre-Si 環境用高可觀測性 debug

### 階段 1：Bring-Up（第一次通電）

First silicon 回來的頭幾天到幾週。目標很低但很關鍵：**讓晶片活著**。

典型檢查順序：

1. **Power-on**：電流量測正常嗎？有沒有短路？各組 power rail 電壓對嗎？
2. **Clock & Reset**：PLL 有 lock 嗎？reset 序列走完了嗎？
3. **基本 I/O**：JTAG 通不通？能不能讀到 device ID？
4. **Scan / BIST**：內建自我測試（MBIST for memory、LBIST for logic）過不過？
5. **第一條指令**：CPU 能不能從 boot ROM 抓到並執行第一條指令？
6. **開機**：Firmware → bootloader → OS

這個階段最容易出現「什麼訊息都沒有」的狀況——晶片不動，也不知道卡在哪。這正是 DFD 設計好不好的照妖鏡。

業界一個粗略的指標：能在幾天內 boot 到 OS，代表設計品質不錯；如果卡在 bring-up 好幾週，通常代表有系統性問題。

### 階段 2：功能驗證（Functional Validation）

晶片活了之後，開始大規模跑內容找 bug：

- **Architectural / ISA validation**：指令行為、例外處理、記憶體排序（memory ordering）、虛擬記憶體
- **Random instruction test (RIT)**：用亂數產生器生出大量合法指令序列，跟 golden reference model（架構模擬器）比對結果。這是找 CPU corner case 的主力武器
- **OS & application**：跑 Linux/Windows、跑 benchmark、跑真實工作負載
- **Compliance & interop**：PCIe、USB、DDR、乙太網路等介面跟第三方裝置的互通性
- **Stress / power virus**：刻意寫出讓晶片功耗與切換率飆到極限的程式，測供電與散熱極限
- **Concurrency**：多核心同時操作、cache coherency、race condition

### 階段 3：電氣特性與角落測試（Electrical Validation / Characterization）

功能對了不代表能量產。這階段要回答的是：**這顆晶片在什麼條件下能穩定工作？**

核心工具是 **shmoo plot**：把電壓當 X 軸、頻率當 Y 軸，每個組合跑一次測試，畫出「過」與「不過」的邊界圖。

```
         Frequency (GHz)
   3.6 | . . . . X X X X
   3.4 | . . . X X X X X
   3.2 | . . X X X X X X
   3.0 | . X X X X X X X
   2.8 | X X X X X X X X
       +----------------
        0.8  0.9  1.0  1.1   Voltage (V)

   X = PASS    . = FAIL
```

理想的 shmoo 是一條平滑的斜線（電壓越高、能跑越快）。如果中間出現一塊奇怪的破洞（hole），那通常代表某個電路有問題——這是很經典的 post-Si 線索。

同時要掃的還有：溫度（-40°C ~ 125°C）、製程角落（拿 fast/typical/slow 晶片各測一批）、老化（burn-in）。

### 階段 4：Debug 與 Triage

找到 fail 只是開始，真正花時間的是**定位**。

一個 post-Si 工程師拿到「跑 Linux 開機到第 40 秒 hang 住」這種現象時，要回答的問題鏈是：

1. **重現得了嗎？** 100 次會發生幾次？換一顆晶片還會嗎？換一片板子還會嗎？
2. **是哪一層的問題？** 測試環境 / 板子 / 電源 / firmware / 晶片設計？
3. **對什麼敏感？** 降頻會不會好？加電壓會不會好？降溫會不會好？
   - 加電壓變好 → 通常是 timing path 問題（setup violation）
   - 降電壓變好 → 可能是 hold violation 或雜訊問題
   - 降溫變好 → 洩漏電流或熱相關
   - 都沒差 → 比較像純功能性邏輯 bug
4. **縮小範圍**：把 failing test 從幾十億條指令縮到幾百條（test narrowing / bisection）
5. **拿內部狀態**：用 scan dump 把整顆晶片的 flip-flop 值抓出來、用 trace buffer 回放最後幾千個 cycle
6. **回到 pre-Si 重現**：把縮小後的 case 拿回 simulator，這時候就有完整可觀測性了

這個流程很像軟體的 debug，差別在於：你的 printf 只有幾個 bit 寬，而且加一個 printf 要等三個月。

### 階段 5：收斂與出貨

- **Errata**：確認是 bug 但決定不修（或來不及修）的問題，寫進勘誤表公開給客戶
- **Workaround**：用 microcode patch、firmware、BIOS、driver 或 compiler 繞過硬體 bug。Intel/AMD 的 CPU microcode update 很多就是在做這件事
- **Stepping 決策**：哪些 bug 嚴重到必須做新的 metal fix 或 full-layer respin？每一次都是時間與金錢的取捨
- **量產測試程式**：把 validation 學到的東西轉成 ATE 上跑的 production test pattern 與 binning 規則

---

## 四、幾個關鍵概念

**Silicon Debug 的核心矛盾**
你要找的 bug 通常是「跑三小時才發生一次」的機率性事件，但你能記錄的內部狀態只有最後幾千個 cycle。所以 post-Si debug 的本質是：**設計一個能把偶發現象變成可重現現象的實驗**。

**DFD (Design-for-Debug)**
晶片上專門為了 debug 而加的硬體：trace buffer、trigger 邏輯、breakpoint、performance counter、可觀測的 debug bus。這些會佔面積、耗電、可能影響時序，所以永遠在跟設計團隊搶資源。但 first silicon 出問題時，這些就是你唯一的眼睛。

**Scan Chain**
測試用的架構：把晶片內所有 flip-flop 串成一條（或多條）鏈，可以把整顆晶片的狀態「掃描」出來看，也可以把想要的狀態掃描進去。缺點是掃描的時候晶片必須停下來，所以只能看到 snapshot，看不到動態過程。

**Stepping / Respin**
晶片改版。只改上層金屬層叫 metal fix（較便宜、較快，但能改的有限）；全部重做叫 all-layer respin（貴、慢）。所以 post-Si 團隊的一個隱含 KPI 是：**在下一次 respin 之前，盡可能把該找的 bug 都找出來，一次修完。**

**Errata**
每一顆商用 CPU 都有勘誤表。Intel、AMD、ARM 都公開發佈。有興趣可以去搜尋任何一顆 CPU 的 "specification update" PDF，會看到幾百條已知 bug 與對應的 workaround——那基本上就是 post-Si 團隊的工作成果目錄。

---

## 五、這個工作需要什麼技能

**硬技能**

- **程式**：C 與組合語言（測試程式要跑在裸機上）、Python（自動化、資料分析、儀器控制）
- **架構知識**：CPU 微架構、cache coherency、memory ordering、匯流排協定（AXI、PCIe、DDR）
- **數位設計基礎**：看得懂 RTL、理解 timing（setup/hold）、知道 clock domain crossing 是什麼
- **儀器操作**：示波器、logic analyzer、protocol analyzer、power supply、thermal chamber
- **測試方法**：JTAG、scan、BIST、ATE 基本概念
- **資料分析**：shmoo 資料、良率資料、大量 test log 的統計分析

**軟技能（其實更關鍵）**

- **系統性 debug 思維**：能在資訊極度不足時建立假設、設計實驗、逐步排除
- **耐得住模糊**：很多時候你會花兩週證明「這不是我們的問題」
- **跨團隊溝通**：post-Si 站在設計、firmware、軟體、製造、客戶的交會點，大部分時間在協調而不是自己動手
- **紀錄能力**：實驗條件、觀察、假設都要寫清楚，因為三個月後你（或別人）要重看

---

## 六、Post-Si 在組織裡的位置

實際公司裡，相關的職位名稱與分工大致是：

- **Post-Silicon Validation Engineer / Silicon Validation Engineer**：本文主要描述的角色
- **DV (Design Verification) Engineer**：pre-silicon，寫 UVM testbench
- **DFT (Design-for-Test) Engineer**：負責 scan、BIST、ATE 相關的可測試性設計
- **Product Engineer (PE)**：量產階段的良率、測試成本、binning
- **Firmware / BSP Engineer**：跟 post-Si 高度重疊，很多 bring-up 工作是一起做的
- **Characterization Engineer**：專做電氣特性掃描

在小公司這些可能是同一個人；在 Intel、NVIDIA、Apple 這種規模則是完全分開的大團隊。

---

## 七、為什麼這個領域有趣（也很折磨）

**有趣的地方**：你面對的是一個真實存在、行為不完全可知的物理系統。沒有原始碼可以讀（那些 RTL 已經變成幾十億顆電晶體了），只能靠實驗與推理。找到一個 bug 的成就感很高，因為那個 bug 可能會影響幾千萬顆出貨的晶片。

**折磨的地方**：迭代週期以月為單位。你可能花三個月追一個 bug，最後發現是測試板上一顆電容的問題。而且時程壓力極大——晶片出貨日期通常是先定好的，validation 永遠是被壓縮的那一段。

如果你喜歡的是「快速迭代、當天看到結果」，這個領域可能不適合。但如果你享受那種偵探式的、資訊不完整下的推理過程，post-Si 大概是硬體業界最接近偵探的工作。

---

## 八、一個 Debug Case Study：追一個「偶爾當機」的 bug

以下是一個綜合虛構的案例，但每個步驟都是 post-Si 的日常。目的是讓你看到「資訊不足下如何推理」的實際樣貌。

### Day 1：現象

自動化測試機台回報：某台跑 Linux stress test 的機器，在連續跑了 **6 小時 42 分**之後 hang 住。序列埠沒有任何輸出，機器完全沒反應。

你手上有的資訊只有：一份 UART log（最後一行是正常的測試進度）、一顆掛掉的晶片、和一句「它壞了」。

**第一個問題不是「為什麼壞」，而是「這值得追嗎」。**
先看嚴重度：會 hang 住整台機器 = 系統當機 = 客戶一定會遇到 = 必追。

### Day 2–4：建立可重現性

Debug 的第一場硬仗永遠是重現。你做三件事：

1. **重跑同一顆晶片**：跑 5 次，2 次在 5～8 小時之間掛掉。→ 可重現，但是機率性的（約 40%）。
2. **換晶片**：拿 10 顆不同晶片跑。7 顆會掛，3 顆跑 24 小時都沒事。→ **跟晶片個體有關**，這是重要線索。設計 bug 通常每顆都會中；只有部分晶片會中，指向製程變異 + 時序邊界。
3. **換板子**：同一顆晶片換三片板子都會掛。→ 排除板子問題。

到這裡你已經可以寫第一份報告：「可重現，機率約 40%，晶片相依，非板級問題。」

### Day 5–8：找敏感度（Sensitivity Sweep）

機率性 + 晶片相依，強烈暗示這是**時序邊界**問題。驗證方法是掃參數，看什麼條件會讓它變好或變壞。

| 條件 | 結果 |
|---|---|
| 核心電壓 +50mV | MTTF（平均失效時間）從 6 小時拉長到 30 小時以上 |
| 核心電壓 −50mV | 40 分鐘內就掛 |
| 頻率降 200MHz | 24 小時無失效 |
| 環境溫度 85°C | 更快掛（約 2 小時） |
| 環境溫度 0°C | 較慢掛（約 15 小時） |

**這張表就是診斷書。** 加電壓變好、降頻變好、升溫變壞——三個訊號一致指向 **setup timing violation**（訊號跑不贏 clock）。如果是 hold violation，加電壓通常反而會更糟；如果是純邏輯 bug，這些參數應該完全沒影響。

同時把電壓降到 −50mV 當作**加速條件**：原本 6 小時才發生一次的事，現在 40 分鐘一次。這件事極度關鍵——**把 MTTF 從 6 小時壓到 40 分鐘，等於把你剩下的 debug 效率提升 9 倍**。Post-Si debug 有很大一部分工作就是在找這種加速條件。

### Day 9–15：縮小範圍

現在要知道「掛在哪」。手段：

1. **Scan dump**：掛住的當下，用 JTAG 把整顆晶片的 flip-flop 狀態掃出來。發現：CPU core 3 的 pipeline 停在等待一個記憶體回應，而 memory controller 那邊顯示這筆交易已經完成了。
   → **有一筆交易「消失」了**。請求送出去，回應沒回來，core 就永遠在等。

2. **On-chip trace buffer**：把 trigger 設在「core 3 stall 超過 10000 cycle」，把 hang 前最後 4096 個 cycle 的匯流排交易錄下來。回放後發現：問題發生在一個 cache line 的 eviction 跟另一個 core 的 snoop request 撞在同一個 cycle 的時候。

3. **縮小測試**：原本的 stress test 有幾十個 thread。用二分法一個個關掉，最後發現只要兩個特定的 memory-intensive thread 綁在特定的兩個 core 上，就能觸發。測試從「6 小時的完整 OS」縮到「一支 200 行的裸機程式，30 秒內觸發」。

**這是整個過程中價值最高的一步。** 有了 30 秒的小測試，你才有辦法拿回 pre-silicon 環境。

### Day 16–20：回到 Pre-Si 定案

把那支 200 行的程式丟進 RTL simulator 跑（真的跑得完了，因為只有 30 秒的 workload）。這次你有完整可觀測性，直接看波形：

某個 arbiter 在同時收到 eviction 與 snoop 時，有一條組合邏輯路徑特別長。在 slow corner + 低電壓 + 高溫的條件下，這條路徑會 setup violation，導致 arbiter 的狀態機進到一個未定義狀態，把那筆交易吃掉。

**Root cause 確認。** 這條路徑在 STA（static timing analysis）裡因為一個錯誤的 false path 設定被排除了，所以 pre-Si 完全沒抓到。

### Day 21：決策

問題找到了，接下來是產品決策，不是技術決策：

- **能不能 workaround？** 可以——用 firmware 關掉某個 prefetch 功能，就不會產生這個 timing 組合。代價是約 3% 效能損失。
- **要不要 respin？** 這條路徑只需要改 metal layer 插一個 buffer，屬於 metal fix，成本相對低。決定併入下一版 stepping。
- **短期怎麼辦？** 現行 stepping 標成 errata，附上 firmware workaround，並把量產頻率規格下修一格保守出貨。

### 這個案例的通用教訓

1. **重現性優先於理解**。不能穩定重現的 bug 無法 debug，先花時間建立重現條件。
2. **敏感度掃描是最便宜的診斷工具**。電壓/頻率/溫度三個旋鈕，就能把問題分成 timing、電氣、邏輯三大類。
3. **找加速條件**。把 MTTF 壓短是 post-Si 的核心技巧。
4. **縮小測試才能回到 pre-Si**。Post-Si 的最終目標往往不是自己找到 root cause，而是把問題壓縮到 pre-Si 能處理的大小。
5. **Root cause 只是中場**。真正的產出是 workaround、errata 與 respin 決策。

---

## 九、想進一步了解可以看什麼

- 任何一顆商用 CPU 的 **Specification Update / Errata 文件**（Intel、AMD 官網公開）——看真實的 bug 長什麼樣
- **JTAG (IEEE 1149.1)** 與 **IJTAG (IEEE 1687)** 標準的入門介紹
- 學術上的關鍵字：`post-silicon validation`、`silicon debug`、`design for debug`、`assertion-based post-silicon`、`trace signal selection`
- 實作面：買一片 FPGA 開發板，自己寫一個小 SoC，然後試著只用 UART 跟 LED 去 debug 它——那個感覺就對了

---

*本文為概念性介紹，各公司實際流程、術語與分工會有差異。*
