---
sidebar_label: CP 晶圓測試
---

# CP 是什麼：晶圓測試（Chip Probing / Wafer Sort）

> 本文是半導體量產測試系列的一篇，全流程概觀見[〈半導體量產測試全景：CP、FT、SLT 與 ATE〉](./semiconductor-test-overview-cp-ft-slt-ate.md)。

## TL;DR

CP（Chip Probing，也稱 Circuit Probing 或 Wafer Sort/WS）是晶圓切割封裝**之前**的測試：用探針卡直接扎在裸 die 的接點上，透過 ATE 篩出壞的 die。核心價值是省錢——壞品不值得花封裝費——同時提供最直接的晶圓良率數據回饋給 fab。它受探針物理特性限制，測不了高頻和大電流項目，這些留給 FT。

---

## 1. 在流程中的位置與目的

晶圓從 fab 出來後，上面規則排列著數千顆裸 die，接腳全部裸露。CP 就在這個階段進行：prober 移動晶圓，讓探針卡的針尖精準接觸每顆 die 的 pad，接上 ATE 執行測試。

CP 的兩個目的：

1. **封裝前篩壞品，控制成本。** 封裝和後續 FT 都是晶片成本的大宗，把壞 die 攔在封裝前是最有利的成本控制點。測試結果以 ink 點標記或電子 wafer map 記錄，封裝廠只取 good die。
2. **監控晶圓良率。** CP 是 fab 製程水準最直接的度量——良率異常可以立即歸因回製程端。

## 2. 測什麼、不測什麼

CP 的測項偏重結構性測試與基本電性：open/short、漏電流（leakage）、DC 參數、scan/MBIST 等高故障率項目。實務上目標是在晶圓階段就篩出九成以上的缺陷，不浪費封裝與 FT 的成本。

但探針有物理限制：

- **高頻測試受限。** 探針卡的接觸電阻和寄生電感較大，測試頻率一般壓在 50–100 MHz 以內，高速介面測試留給 FT。
- **大電流項目不能測。** 探針容許電流有限，大電流測試只能在封裝後做。
- **Spec 比 FT 收得更緊。** 封裝會造成參數漂移，所以 CP 的判定門檻要比 FT 更嚴，才能確保封裝後的 FT 良率。

一個特例是記憶體產品：CP 階段會做 redundancy analysis，算出可修復的位址，再用 laser repair 把 repairable die 救回來——同時提升良率和可靠度。這也讓記憶體的 CP 程式比邏輯晶片複雜得多。

## 3. 探針卡：CP 的技術核心

CP 最難的部分是探針卡的製作與平行測試的干擾問題。探針卡依結構分幾類：

- **懸臂樑式（Cantilever, CPC）**：傳統結構，成本低，適合 pad 數少的產品
- **垂直式（Vertical, VPC）**：針密度高，適合 flip-chip 的 area array pad
- **MEMS 式**：微機電製程做的探針，精度與密度最高，先進製程主流

台灣在這個領域有完整的供應鏈聚落（如精測、旺矽主攻 CP 相關，穎崴、雍智偏 FT 端的測試介面）。

## 4. CP 可以省略嗎

可以，視產品而定。低單價產品加測 CP 會增加 cycle time 和成本；製程成熟、WAT 良率夠高時，有些公司選擇跳過 CP 直接封裝（俗稱盲封）——但風險自負，業界實際採用的不多，因為一批晶圓良率失控時損失巨大。反方向的特例是 WLCSP（晶圓級封裝）：產品在晶圓階段就完成封裝，CP 測完切割即可出貨，沒有傳統意義的 FT。

## 5. 容易混淆：CP vs. WAT

**WAT（Wafer Acceptance Test，也稱 PCM）不是 CP。** WAT 測的是晶圓切割道（scribe line）上專門設計的 test key，量測元件層級的電性參數（threshold voltage、導通電阻、擊穿電壓等），目的是監控 fab 各步製程是否正常穩定——它由 fab 執行、測的是製程監控圖形；CP 測的是產品 die 本身、判定的是這顆晶片的好壞。兩者層次完全不同。

---

## References

1. Fountyl, "Semiconductor technology and equipment: chip testing and equipment" — https://www.fountyltech.com/news/semiconductor-technology-and-equipment-chip-testing-and-equipment/
2. 知乎, 「半导体测试概述」 — https://zhuanlan.zhihu.com/p/37363859
3. 每日頭條, 「晶片測試的幾個術語及解釋（CP、FT、WAT）」 — https://kknews.cc/news/rzg8qjr.html
4. 優分析, 「【封測】測試市場的三大基本分類」 — https://uanalyze.com.tw/articles/141865423
5. 電子技術應用, 「芯片的几个重要测试-CP、FT、WAT」 — https://chinaaet.com/article/3000162517
6. Downey's blog, 「IC講解：如何區分CP測試和FT測試」 — https://downey9527.wordpress.com/2019/10/17/ic講解：-如何區分cp測試和ft測試/
