---
title: 效能 / Benchmark 名詞表
sidebar_label: 效能 Benchmark 名詞表
sidebar_position: 11
---

# 效能 / Benchmark 名詞表

從一個陌生的縮寫反查回原始筆記。文章清單見 [效能 / Benchmark 索引](perf_index.md)。

> Android 平台專有名詞（simpleperf 以外的 systrace、Perfetto、HWUI 等）見 [Android 名詞表](android_glossary.md)；
> kernel 與 driver 層的觀測機制另見 [Embedded 名詞表](embedded_glossary.md)。

---

## 一、跑分工具與指標

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Geekbench** | 跨平台跑分，分 CPU、Compute（GPU）與 **AI** 三種榜單，各有獨立的結果頁 | [iPad Air 4](../benchmark_ipad_air.md)、[Benchmark 收集](../benchmark.md) |
| **PCMark** | 用**貼近真實使用情境**的工作負載（文書、瀏覽、視訊、影像編修）評整機，並提供 **Battery Life** 測續航與耗電 | [功耗／效能工具](../power_benchmark.md) |
| **3DMark / Antutu** | 前者偏 GPU 與遊戲圖形，後者是綜合跑分。和 PCMark 的差別在「量的是峰值還是日常」 | [功耗／效能工具](../power_benchmark.md) |
| **WASM 的限制** | 網頁跑分的天花板：WebAssembly 拿不到的硬體資訊與指令集能力，決定了瀏覽器 benchmark 能量到什麼、不能量到什麼 | [瀏覽器效能 Benchmark](../browser_performance_benchmark.md) |
| **沒有 GMS 就沒有跑分 App** | 自編的 AOSP build 沒有 Play 商店，Geekbench／3DMark／AITuTu 那條路直接斷掉——反而必須面對系統暴露的原始介面 | [Pixel 8 三個單元](../pixel8-cpu-gpu-npu-benchmark.md) |
| **「合理但錯誤的數字」** | 這一類的核心警告：CPU、GPU、NPU 各有一個陷阱會給出看起來正常、實際上量錯的結果；包裝好的跑分工具只會幫你把它藏起來 | [Pixel 8 三個單元](../pixel8-cpu-gpu-npu-benchmark.md) |

## 二、觀測的三個層次

| 名詞 | 說明 | 出處 |
|---|---|---|
| **PMU（一詞兩義）** | 在 CPU 語境是 **Performance Monitoring Unit**（硬體效能計數器，cycles、cache miss、branch miss）；在電源語境是 Power Management Unit。看到 PMU 要先問是哪一個 | [PMU／Ftrace／EMI](../pmu-ftrace-emi.md) |
| **Ftrace** | kernel 內建的追蹤框架，觀測的是**作業系統層**：排程、中斷、函式進出 | [PMU／Ftrace／EMI](../pmu-ftrace-emi.md) |
| **EMI（SoC 語境）** | 在 SoC 討論裡通常**不是**電磁干擾，而是**外部記憶體介面**那一層——記憶體頻寬與延遲的瓶頸就看這裡 | [PMU／Ftrace／EMI](../pmu-ftrace-emi.md) |
| **三層互補** | 一個效能問題先決定從哪一層看：**CPU 微架構（PMU）→ 作業系統（Ftrace）→ 記憶體子系統（EMI）**。跳層猜根因是最常見的浪費 | [PMU／Ftrace／EMI](../pmu-ftrace-emi.md) |
| **`simpleperf`** | Android 上的取樣分析工具；文章整理了它**三個會說謊的地方**（量到的和你以為量的不同） | [Pixel 8 三個單元](../pixel8-cpu-gpu-npu-benchmark.md) |
| **EdgeTPU「有沒有在跑」** | NPU 量測的第一個問題不是快不快，而是**工作到底有沒有落到 NPU 上**；judge 錯了後面全錯 | [Pixel 8 三個單元](../pixel8-cpu-gpu-npu-benchmark.md) |
| **NNAPI deprecated** | Android 的 NNAPI 已標示 deprecated，NPU 的存取路徑正在改變，量測方法也要跟著換 | [Pixel 8 三個單元](../pixel8-cpu-gpu-npu-benchmark.md) |

## 三、頻率、電源與排程

| 名詞 | 說明 | 出處 |
|---|---|---|
| **DVFS** | Dynamic Voltage and Frequency Scaling。功耗大致與**電壓平方乘以頻率**成正比，所以降頻降壓省電有感 | [CPU DVFS](../cpu_dvfs.md) |
| **`cpufreq` governor** | Linux 決定調頻策略的模組：`performance`（固定最高頻）、`powersave`（固定最低頻）、`ondemand`／`schedutil` 等依負載調整 | [CPU DVFS](../cpu_dvfs.md) |
| **P-state** | Intel 的效能狀態（`intel_pstate` driver），與 ARM 平台的 `cpufreq` governor 對應但實作不同 | [CPU DVFS](../cpu_dvfs.md) |
| **Priority Inversion** | 高優先權 task 等在低優先權 task 持有的 lock 上，中優先權 task 又搶走 CPU，於是高優先權被間接卡死。經典案例：**Mars Pathfinder** | [Priority Inversion](../os_priority_inversion.md) |
| **Priority Inheritance** | 解法：持有資源的低優先權 task 暫時繼承等待者的優先權，釋放後再降回來 | [Priority Inversion](../os_priority_inversion.md) |
| **`swsusp` / hibernation image** | 把整份 kernel 記憶體做成快照存進 swap。關鍵視角是——**它是一份可以被完整寫回 kernel 記憶體的資料**，所以是安全問題而不只是電源問題 | [Hibernation](../hibernation.md) |
| **「兩個 kernel」** | hibernation 最反直覺的地方：做 resume 的 kernel 和被還原的 kernel 不是同一個執行體，這解釋了大量 resume 失敗的症狀 | [Hibernation](../hibernation.md) |
| **freezer（協作式）** | 凍結行程的機制是**協作式而非搶佔式**——有 task 不配合就會卡住整個流程 | [Hibernation](../hibernation.md) |
| **`dev_pm_ops` 四組 callback** | suspend／resume／freeze／thaw／poweroff／restore 的語意差異，寫錯 driver 就會在 hibernation 路徑上壞掉 | [Hibernation](../hibernation.md) |

## 四、影片解碼與畫面

| 名詞 | 說明 | 出處 |
|---|---|---|
| **軟解 vs 硬解的判讀** | 看 YouTube 偵錯面板的 `Codecs` 與 `Color` 欄位就能判斷——走軟解時 CPU 負載與耗電會完全不同 | [影片解碼效能觀察](../performance_experient.md) |
| **VP9 Profile 2 / `smpte2084 (PQ)` / `bt2020`** | HDR10 內容的特徵字串；Profile 2 代表 10-bit，PQ 是轉換曲線，bt2020 是色域 | [影片解碼效能觀察](../performance_experient.md) |
| **SurfaceFlinger** | Android 的畫面合成器；「卡頓」類 bug 的落點之一 | [SurfaceFlinger](../surfaceflinger-composition-and-debugging.md) |

## 五、調校與迭代

| 名詞 | 說明 | 出處 |
|---|---|---|
| **控制點地圖** | 調校前先問「誰在決定快慢與耗電」：kernel、BSP、framework、App 各有旋鈕，**槓桿大多握在 BSP 層** | [效能與功耗調校實戰](../10-performance-power-tuning.md) |
| **先量再調** | 方法論的第一條：沒有 baseline 的調校等於猜 | [效能與功耗調校實戰](../10-performance-power-tuning.md) |
| **迭代速度也是效能** | 「改一行 → full build → 燒整包 → 開機驗證」是最大的時間黑洞；**大多數驗證不需要 full build，也不需要燒整包** | [Build Time 優化](../android-build-time-optimization.md) |
