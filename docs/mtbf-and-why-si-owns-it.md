---
sidebar_label: MTBF
---

# MTBF 是什麼？為什麼它是 Chip Vendor 系統整合工程師的主場

> 本文可視為半導體量產測試系列的延伸篇——前面的 [CP/FT/SLT](./semiconductor-test-overview-cp-ft-slt-ate.md) 講的是「矽」的品質怎麼度量，這篇講「軟體堆疊」的品質怎麼度量。

## TL;DR

MTBF（Mean Time Between Failures，平均故障間隔時間）在教科書裡是硬體可靠度指標；但在 chip vendor 的行動裝置產品線語境中，它更常指**整機軟體穩定性指標**：一批裝置跑長時間自動化壓力測試，MTBF = 總運作時數 ÷ 故障次數，客戶把門檻寫進出貨條件。這個指標之所以天然落在系統整合（SI）團隊頭上，是因為它度量的對象——「整合後的系統撐不撐得住」——本身就是 SI 的產出物：模組團隊各自對零件負責，SI 對組合結果負責，而 MTBF 就是組合結果的量化語言。

---

## 1. 先把教科書定義釐清

可靠度工程裡有三個常被混用的指標：

- **MTBF（Mean Time Between Failures）**：用於**可修復**系統，兩次故障之間的平均運作時間。MTBF = 總運作時間 ÷ 故障次數。
- **MTTF（Mean Time To Failure）**：用於**不可修復**的元件（壞了就換），指平均壽命。晶片、燈泡講 MTTF；伺服器、產線設備講 MTBF。
- **MTTR（Mean Time To Repair）**：平均修復時間。

三者的關係：**MTBF = MTTF + MTTR**（一個故障週期 = 正常運作時間 + 修復時間），而固有可用度（inherent availability）= MTBF / (MTBF + MTTR)。

一個必須先打掉的誤解：**MTBF 是統計平均，不是保證壽命**。「硬碟 MTBF 100 萬小時」不代表一顆硬碟能用 114 年，而是指一大批同型裝置在正常壽命期內，平均每累積 100 萬個裝置小時出現一次故障。母體統計和單一個體的壽命分佈是兩回事。

## 2. 在 Chip Vendor，MTBF 是軟體穩定性的語言

行動裝置產業借用了這個詞，把它變成**整機軟體穩定性的量化指標**。做法大致是：

1. **佈署一批測試裝置**（數十到上百台），刷上待驗證的 build。
2. **跑長時間自動化壓力測試**：核心工具是 Android 內建的 Monkey——對系統注入偽隨機的使用者事件流（點擊、觸控、手勢、系統事件），以隨機但可重現（seed 控制）的方式對整個軟體堆疊施壓。再搭配情境化壓測：suspend/resume 循環、通話、多媒體播放、相機、連線切換等使用情境輪跑，持續數天到數週。
3. **收集所有故障事件**：kernel panic、native crash、Java crash、ANR、system server 重啟、watchdog 觸發的重開機、無預期斷電重啟——每一筆都要有對應的 log 與 dump。
4. **計算**：MTBF = 全部裝置的總運作時數 ÷ 計入統計的故障總數。

客戶（OEM）通常把 MTBF 門檻寫進各里程碑的 exit criteria——工程版、試產版、量產版各有遞增的小時數要求，達不到就不能進入下一階段。**它是合約層級的品質承諾**，跟矽那邊的 DPPM 是完全平行的邏輯：

| | DPPM | MTBF（穩定性語境） |
|---|---|---|
| 度量對象 | 矽（出廠缺陷） | 軟體堆疊（使用期故障） |
| 時間軸 | time-zero：出貨當下好不好 | in-use：用起來撐多久 |
| 把關站點 | CP / FT / SLT | 穩定性壓測（每週期 build） |
| 對客戶的意義 | 晶片品質承諾 | BSP/平台軟體品質承諾 |

（硬體語境的 MTBF/MTTF 當然也存在——那屬於可靠度測試的範疇，用 burn-in、HTOL 等加速老化手段對付浴缸曲線左端的早夭品，是另一條線，本文不展開。）

## 3. 為什麼 MTBF 是 SI 的主場

這是本文真正想回答的問題。一個 crash 進來，為什麼不是直接丟給某個 driver team，而是先經過系統整合？五個結構性原因：

### 3.1 MTBF fail 天生沒有 owner

一筆故障的根因可能在任何一層：driver 的 race condition、電源管理政策把系統逼進邊界狀態、thermal 降頻餓死 watchdog、記憶體邊際問題、framework 的資源洩漏，甚至是測試工具自己的 bug。單一模組團隊只看得到自己那層；**唯一有全 stack 視野、能把 log 從 kernel 一路追到 framework、再判定該分派給誰的角色，就是 SI**。MTBF triage 的本質是「以統計形式呈現的跨團隊 log 分析」——每個數字背後都是一疊等著被歸因的 crash。

### 3.2 它是 build 層級的度量，而 build 品質歸整合管

MTBF 不測任何單一功能，測的是「這個 build 作為整體」的存活能力——它是所有模組整合結果的函數。每週期 build 的 MTBF 趨勢是整合品質最誠實的儀表板：數字突然崩掉，代表新收進來的某批 change 引入了穩定性回歸，接下來的 bisect、change 追蹤、回退決策，都是整合與 CI 的職權範圍。

### 3.3 基礎設施跟 CI 是同一套肌肉

跑 MTBF 需要的東西——裝置機房、自動化測試調度、crash 自動偵測與 dump 收集、log 解析、統計報表——跟 CI pipeline 是同一類基礎設施，自然由同一批人維護。壓測框架的可靠度本身也是工程問題：測試 harness 不穩，統計就失真。

### 3.4 它直接面對客戶

MTBF 數字要交給客戶審，客戶的品質團隊會挑戰每一筆故障的處置。誰對客戶的 build 負責，誰就對這個數字負責——在 chip vendor 的分工裡，這就是整合團隊。

### 3.5 統計裁定需要中立裁判

MTBF 計算最敏感的部分不是除法，是**分子怎麼認定**：這筆 crash 算 vendor 的 BSP bug、客戶客製化改動造成的、還是可排除項（測試工具問題、已知第三方 app bug、重複計數）？每一筆判定都影響過不過門檻，也影響責任與工作量的分配。這個裁定需要一個不隸屬任何模組團隊、又有足夠技術深度看懂 log 的中立角色——組織結構上，SI 是唯一符合條件的位置。

一句話總結：**模組團隊負責零件好不好，SI 負責組起來之後撐不撐得住，MTBF 就是「撐不撐得住」的量化語言——所以它理所當然是 SI 的主要工作內容。**

## 4. MTBF Triage 的實務循環

日常運作大致是一個固定節奏的循環：

```
壓測執行（數天～數週）
   │
   ▼
故障自動收集（log / dump / 現場保存）
   │
   ▼
初步分類 ── 依故障型態分桶：kernel、native、framework、ANR、reboot...
   │
   ▼
去重與初判 ── 同 signature 的 crash 歸併；判斷新問題 vs. 已知問題
   │
   ▼
根因初析與分派 ── 全 stack log 分析，指出最可能的層，開單給 owner 團隊
   │
   ▼
修復驗證 ── fix 進入下一輪 build，確認該 signature 不再出現
   │
   ▼
統計與報告 ── 計算本輪 MTBF、判定排除項、趨勢比較、對客戶報告
```

其中最吃經驗的兩步是**去重**（同一個根因可能以多種表面症狀出現，錯誤歸併會高估或低估問題數）和**初判分派**（分錯團隊，問題就在 ping-pong 中損耗一週）。這也是為什麼 MTBF triage 很難外包給純測試團隊——它需要的是 debug 能力，不只是執行能力。

## 5. 小結：兩條品質軸線

把這篇跟前面的測試系列接起來，chip vendor 對客戶的品質承諾其實有兩條軸線：

- **矽的軸線**：CP → FT → SLT，攔出廠缺陷，語言是 DPPM。
- **軟體的軸線**：每週期 build 的穩定性壓測，度量使用期的故障率，語言是 MTBF。

兩條軸線在 SLT 和 MTBF 這兩端有著漂亮的對稱性：都是「不再逐項驗證，直接把整個系統當產品操」的系統級測試，都是合約層級的量化承諾，也都需要跨層 debug 能力來歸因失效。差別只在一個對矽負責、一個對軟體堆疊負責——而後者，就是系統整合工程師每天在做的事。

---

## 附註

本文第 2–4 節描述的穩定性測試實務為行動裝置產業的通行做法，各公司的故障分類命名、統計規則與門檻設定差異很大，細節以各自組織的定義為準。

## References

1. Android Developers, "UI/Application Exerciser Monkey" — https://developer.android.com/studio/test/other-testing-tools/monkey
2. Atlassian, "MTBF, MTTR, MTTA, and MTTF" — https://www.atlassian.com/incident-management/kpis/common-metrics
3. ReliaMag, "How to Calculate MTBF and MTTR: Methodology and Worked Examples" — https://reliamag.com/guides/how-to-calculate-mtbf-mttr/
4. M. Fazeli et al., "In-Field Logic Repair of Deep Sub-Micron CMOS Processors," arXiv:1509.09249（MTBF = MTTF + MTTR 與 availability 定義）— https://arxiv.org/abs/1509.09249
