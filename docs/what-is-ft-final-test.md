---
sidebar_label: FT 最終測試
---

# FT 是什麼：最終測試（Final Test）

> 本文是半導體量產測試系列的一篇，全流程概觀見[〈半導體量產測試全景：CP、FT、SLT 與 ATE〉](./semiconductor-test-overview-cp-ft-slt-ate.md)。

## TL;DR

FT（Final Test）是晶片**封裝完成後**的測試：封裝品放進測試 socket、透過 load board 接上 ATE，驗證封裝製程沒有引入新缺陷、補測 CP 階段測不了的項目，並依效能分 bin/grade。只有 FT pass 的晶片才會出貨。CP 可以視情況省略，FT 幾乎一定要做——它是出貨前在 ATE 上的最後一道關卡。

---

## 1. 為什麼 CP 測過了還要再測

這是初學者最自然的疑問：封裝前不是已經篩過壞品了嗎？兩個原因：

1. **封裝製程本身會引入缺陷。** 打線/凸塊接合不良、封裝應力、參數漂移——FT 良率直接度量封裝廠的製程水準，就像 CP 良率度量 fab 一樣。
2. **有些項目 CP 根本測不了。** 探針卡的接觸電阻、寄生電感和電流承受力限制了高頻與大電流測試，這些只能等封裝好、透過 socket 的低阻抗連接來測。所以 FT 的測項雖然看起來比 CP 少（很多項 CP 測過就免測），但都是關鍵項目、判定條件嚴格。

## 2. 測試環境與測項

FT 的設備組合是 **ATE（tester）+ handler（自動取放機）+ load board + socket**。Handler 把封裝品從 tray 抓進 socket、依測試結果分料，有些還能控制測試溫度（高低溫測試）。

常見測項包括：

- **Open/Short**：接腳有無開路短路——封裝接合品質的第一道檢查
- **DC 參數**：電流、電壓準位
- **AC 參數**：時序、輸出訊號品質
- **Function test**：邏輯功能驗證
- **DFT 測試**：scan、BIST 等結構性測試
- **RF 測試**：含射頻模組的晶片，驗證 RF 功能與效能參數
- **eFlash 測試**：內嵌快閃記憶體的讀寫、耗電、速度
- 部分產品還會做待機電流等應用面向的測試

## 3. FT 不只判生死：Binning 與分級

FT 的輸出不是單純的 pass/fail。測試程式會依結果做 **physical binning**——handler 把晶片實體分到不同料盒。分 bin 的依據除了好壞，還有**效能等級**：量測 Fmax（最高工作頻率）、Vmin（最低工作電壓），把同一顆設計分成不同 speed grade 販售，這些參數同時是系統軟體 DVFS 設定的依據。換句話說，FT 是「同一顆晶片賣出幾種 SKU」的決定點。

Pass 的晶片依封裝型式裝進 Tray、Tube 或 Reel 包材，送往客戶的 SMT 產線上板。

## 4. FT 的難點與其後的 SLT

FT 的工程挑戰是**在最短時間內完成足夠的出貨保證**——測試時間直接是成本，每一秒都要跟 DPPM 目標做取捨。而對複雜 SoC 來說，即使 FT 全過，仍有 ATE 結構性測試先天抓不到的缺陷（跨 IP 互動、邊際缺陷、軟硬體互動），這些由 FT 之後加測的 SLT 站點兜底，詳見[〈SLT 是什麼〉](./what-is-slt-and-why-chip-vendors-care.md)。

---

## References

1. Fountyl, "Semiconductor technology and equipment: chip testing and equipment" — https://www.fountyltech.com/news/semiconductor-technology-and-equipment-chip-testing-and-equipment/
2. 知乎, 「半导体测试概述」 — https://zhuanlan.zhihu.com/p/37363859
3. 每日頭條, 「晶片測試的幾個術語及解釋（CP、FT、WAT）」 — https://kknews.cc/news/rzg8qjr.html
4. SwayChat（痞客邦）, 「聊聊～半導體基礎概論 IC測試 (FT)」 — https://justabread.pixnet.net/blog/post/121150284
5. CSDN, 「芯片常见测试手段：CP测试和FT测试」 — https://blog.csdn.net/qq_36045093/article/details/132214551
6. Downey's blog, 「IC講解：如何區分CP測試和FT測試」 — https://downey9527.wordpress.com/2019/10/17/ic講解：-如何區分cp測試和ft測試/
