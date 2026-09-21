---
title: 效能 / Benchmark 文章索引
sidebar_label: 效能 Benchmark 索引
sidebar_position: 10
---

# 效能 / Benchmark 文章索引

這一類回答的是同一個問題的不同層次：**「它到底快不快，以及你憑什麼這樣說」**。
從怎麼設計一次量測、沒有現成工具時怎麼自己量，到量到數字之後該往哪一層追根因。

跨分類提醒：Android 平台的效能主題同時列在 [Android 系列索引](android_index.md)，
kernel 與 driver 層的觀測工具見 [Embedded 系列索引](embedded_index.md)。

---

## 一、量測方法與工具

| 文章 | 內容 |
|---|---|
| [瀏覽器效能 Benchmark](../browser_performance_benchmark.md) | 用網頁 benchmark 量一台機器的性能：有哪些指標、**CPU／GPU／memory 怎麼可能被網頁量到（底層原理）**、實驗怎麼設計、有哪些工具、以及**限制**——WASM 拿不到的東西決定了網頁跑分的天花板。另含「能不能用 onnx / tensorflow.js / transformers.js 測 AI」的探討 |
| [功耗 / 效能 Benchmark 工具](../power_benchmark.md) | 工具定位速查：**PCMark** 用貼近真實使用情境的工作負載（文書、瀏覽、視訊、影像編修）評整機，並有 **Battery Life** 測續航；3DMark 偏 GPU／遊戲圖形 |
| [Benchmark 數據收集](../benchmark.md) | 各層跑分的實測截圖：硬體資訊、CPU、Geekbench、圖形與 GPU，以及 **WASM 的限制與實際表現**對照 |
| [Benchmark：iPad Air 4](../benchmark_ipad_air.md) | 單一裝置的完整數據點：Geekbench CPU／Compute／**AI**、3DMark、Antutu、Memory、瀏覽器。當作對照組很好用 |

## 二、實作紀錄：沒有現成工具的時候怎麼量

| 文章 | 內容 |
|---|---|
| [在沒有 Play 商店的 Pixel 8 上，把 CPU、GPU、NPU 都量出來](../pixel8-cpu-gpu-npu-benchmark.md) | 自編的 `AOSP_on_shiba` userdebug build 沒有 GMS，Geekbench／3DMark／AITuTu 那條路一開始就斷了。結論反而是：**正因為沒有現成跑分 App，才被迫面對系統暴露的原始介面，也才看見三個單元各自「會給出合理但錯誤數字」的陷阱**——包裝好的工具只會幫你把它們藏起來。含 `simpleperf` 的三個會說謊的地方、GPU 換個角度量、EdgeTPU「到底有沒有在跑」的判定、一支一鍵 runner，以及 NNAPI deprecated 之後怎麼辦 |
| [在 Pixel 8 上追一個 llama.cpp 的 SVE 效能退化](../llama-cpp-pixel8-sve-flash-attention.md) | 起點只是「thread 綁大核到底值不值得」，做完卻拿到四個沒預期的東西。**量測設計 → 異常數字 → 往下追到 SVE 與 flash attention** 的完整過程，是這一類裡最接近真實除錯節奏的一篇 |
| [影片解碼效能觀察](../performance_experient.md) | 判讀練習：從 YouTube 偵錯面板的 `Codecs` 與 `Color` 欄位判斷**走軟解還是硬解**（VP9 Profile 2、`smpte2084 (PQ)`／`bt2020` HDR10），以及瀏覽器版與 App 版的關鍵差異 |

## 三、觀測層次與系統機制

| 文章 | 內容 |
|---|---|
| [PMU、Ftrace、EMI：SoC 效能問題的三個觀測層次](../pmu-ftrace-emi.md) | **這一節的骨架**：三個縮寫看似無關，放進「一個效能問題該從哪裡看」就是互補的三層——**CPU 微架構層（PMU）、作業系統層（Ftrace）、記憶體子系統層（EMI）**。三個詞都有一詞多義問題，文章先釐清定義再談怎麼串起來用 |
| [CPU DVFS](../cpu_dvfs.md) | 依負載調頻調壓的基本盤：功耗大致與**電壓平方及頻率**成正比，所以降頻降壓省電有感。Linux `cpufreq` 的 governor（performance／powersave／ondemand 等）、相關 sysfs 路徑與 Intel P-state |
| [Priority Inversion](../os_priority_inversion.md) | 高優先權 task 被低優先權 task 持有的 lock 卡住，中優先權又搶走 CPU。經典案例是 **Mars Pathfinder** 的系統重啟；解法是 priority inheritance 與 priority ceiling |
| [Hibernation：一份可以寫回 kernel 記憶體的快照](../hibernation.md) | 從效能／電源的角度看它只是慢版 suspend，但換個敘述——**hibernation image 是一份可以被完整寫回 kernel 記憶體的資料**——它就變成橫跨 driver 生命週期、freezer 協定、開機流程與 Secure Boot 信任鏈的結構性問題。含 `swsusp` snapshot 怎麼做、**「兩個 kernel」這個最反直覺的地方**、`dev_pm_ops` 四組 callback 的語意差異，以及信任鏈在哪裡斷開 |

## 四、平台級的調校與迭代速度

| 文章 | 內容 |
|---|---|
| [效能與功耗調校實戰：Chip Vendor 視角](../10-performance-power-tuning.md) | 跑分、順暢度、續航的控制點地圖（誰在決定快慢與耗電）、量測工具鏈、**「先量再調」的方法論**，以及這件事在組織層面的課題 |
| [優化 Android Platform Build Time](../android-build-time-optimization.md) | 另一種效能——**你自己的迭代速度**。核心觀念是「大多數驗證不需要 full build，也不需要燒整包」，含 build 端與燒錄端的分層優化與日常工作流 |
| [SurfaceFlinger：畫面是怎麼被合成出來的](../surfaceflinger-composition-and-debugging.md) | 「畫面卡頓」這類 bug report 的落點：合成路徑與除錯手法。Android 視角的完整脈絡見 [Android 系列索引](android_index.md) |

---

## 建議閱讀順序

**想量一台裝置有多快：**

```
瀏覽器效能 Benchmark        ← 先懂指標與「網頁憑什麼量得到」
   → 功耗 / 效能工具         ← 工具各自量什麼
   → Benchmark 數據收集      ← 看別人量出來長什麼樣
   → iPad Air 4              ← 一個完整的對照組
```

**量到怪數字，要往下追：**

```
PMU / Ftrace / EMI          ← 先決定該從哪一層看
   → CPU DVFS                ← 頻率與電壓是不是在騙你
   → Pixel 8 三個單元實作      ← 三個「合理但錯誤」的陷阱
   → llama.cpp SVE 退化       ← 一條完整的追因路徑
```

**做平台／BSP 的人：**

```
效能與功耗調校實戰           ← 控制點地圖
   → Hibernation             ← 電源狀態與 driver 生命週期
   → Priority Inversion       ← 排程層的經典坑
   → Build Time 優化          ← 讓自己的迴圈先快起來
```

## 待補主題

| 主題 | 為什麼重要 | 狀態 |
|---|---|---|
| **thermal throttling 與量測可重現性** | 跑分掉 20% 常常不是 code 變慢，而是機器熱了。連續跑、降溫間隔、環境溫度控制是 benchmark 可信度的前提，目前沒有專篇 | 待補 |
| **記憶體頻寬與 cache miss 的量法** | EMI／memory 那一層目前只有概念，缺 `perf stat` 等實際量測與判讀 | 待補 |
| **功耗量測的硬體方法** | 目前都是軟體側估算，缺電流探針／power monitor 的實作與與軟體數字的對照 | 待補 |
