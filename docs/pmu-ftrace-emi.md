# PMU、Ftrace、EMI：SoC 效能問題的三個觀測層次

在讀韌體或 kernel 相關的討論串時，PMU、Ftrace、EMI 這三個縮寫常常混在同一段話裡出現。第一次遇到會覺得毫無關聯 —— 一個像硬體、一個像 kernel 工具、一個看起來像電磁相容測試。但如果把它們放在「一個效能問題該從哪裡看」這個脈絡下，其實是三個互補的觀測層次：**CPU 微架構層、作業系統層、記憶體子系統層**。

這三個詞都有一詞多義的問題，先把定義釐清，再談怎麼串起來用。

---

## PMU：兩個完全不同的東西

### Performance Monitoring Unit

ARM 核心內建的硬體計數器單元（ARMv8 對應的規格是 PMUv3）。它提供一組可程式化的 event counter，加上一個獨立的 cycle counter，能夠計數這類事件：

- CPU cycle 數與 retired instruction 數（兩者相除即為 IPC）
- L1/L2 cache access 與 refill（miss）
- TLB miss
- Branch misprediction
- Memory-bound stall cycle（部分核心提供 frontend/backend stall 分類）

Linux 的 `perf` 子系統就是這組硬體的軟體介面。使用者透過 `perf_event_open()` 設定要計數的 event，kernel 負責分配實體 counter、處理 context switch 時的存取。

```bash
perf stat -e cycles,instructions,cache-misses,branch-misses ./workload
perf record -e cycles -g ./workload && perf report
```

實務上要注意的兩件事：

1. **counter 數量有限。** 一般 ARM 核心大約 6 個 general-purpose counter 加 1 個 cycle counter。要求的 event 超過這個數量時，kernel 會啟動 multiplexing —— 分時輪流計數再按比例推估。`perf stat` 輸出的百分比欄位就是實際取樣覆蓋率，數字明顯低於 100% 時，結果只能當趨勢參考。
2. **big.LITTLE 上的 event 編碼不一致。** 不同 microarchitecture 的 event ID 對應的實體意義可能不同，跨 cluster 比較數據前要先確認。

### Power Management Unit

同一個縮寫在電源相關的討論裡指的是電源管理單元 —— 可能是 SoC 內部的電源控制邏輯，也可能泛指外掛的 PMIC。負責 power domain 的開關、voltage rail 的調節、開關機時序。

**怎麼判斷是哪一個：** 上下文出現 perf、counter、IPC、cache miss，是 Performance Monitoring Unit；出現 regulator、rail、suspend/resume、開關機序列，是 Power Management Unit。

---

## Ftrace：kernel 內建的追蹤框架

Ftrace 是 Linux kernel 內建的追蹤基礎設施，介面掛在 `/sys/kernel/tracing`（舊路徑是 `/sys/kernel/debug/tracing`）。它不需要額外安裝任何東西，只要 kernel config 有開，就能直接用檔案系統操作。

常用的 tracer：

| Tracer | 用途 |
|---|---|
| `function` | 記錄每個 kernel 函式的進入點 |
| `function_graph` | 記錄函式進出，附帶呼叫層級與各層耗時 |
| `irqsoff` / `preemptoff` | 找出 interrupt 或 preemption 被關閉最久的路徑 |
| `wakeup` / `wakeup_rt` | 量測排程喚醒延遲 |
| `nop` | 只收 tracepoint，不做函式追蹤 |

除了 tracer 之外，Ftrace 也是 tracepoint 與 kprobe 的輸出通道。靜態的 tracepoint（如 `sched:sched_switch`、`irq:irq_handler_entry`）成本極低，可以常駐開著；kprobe 則能動態插到幾乎任何 kernel 函式上。

一個典型的用法：

```bash
cd /sys/kernel/tracing
echo function_graph > current_tracer
echo 'foo_driver_*' > set_ftrace_filter   # 只追特定前綴，避免資料量爆炸
echo 1 > tracing_on
# ... 重現問題 ...
echo 0 > tracing_on
cat trace > /data/local/tmp/trace.txt
```

**幾個實務重點：**

- **filter 一定要設。** 全開 `function` tracer 的資料量會在幾秒內塞滿 ring buffer，而且 tracing 本身的 overhead 會讓 timing 相關的 bug 消失。
- **可以在 boot 階段就啟用。** 透過 kernel cmdline 的 `ftrace=function_graph`、`ftrace_filter=`、`trace_buf_size=` 等參數，能追到 init 之前的行為，這是排查開機慢或早期 panic 的主要手段。
- **Android 上你其實一直在用它。** atrace 與 Perfetto 的 kernel 端資料來源就是 ftrace，systrace 上看到的 sched、freq、irq 軌道都是 ftrace tracepoint 轉出來的。
- **user space 對應的工具是 uftrace。** 概念類似但作用域在應用程式，需要編譯期插樁配合。

---

## EMI：在 SoC 語境下通常不是電磁干擾

### External Memory Interface

在 SoC 的程式碼與文件裡，EMI 多半是指 **External Memory Interface** —— 連接外部 DRAM 的控制器子系統。它是整顆晶片上所有 master（CPU、GPU、APU、ISP、video codec、display）搶頻寬的匯流點，因此是效能分析裡非常關鍵的一層。

跟 EMI 相關、比較常在 log 或 kernel 討論中出現的有兩塊：

**EMI MPU（Memory Protection Unit）**
把實體記憶體切成若干 region，為每個 region 設定哪些 master domain 可以讀、可以寫。TEE、secure boot、以及各種 secure buffer 的隔離都依賴它。當有 master 存取了不該碰的區段，硬體會產生 violation 中斷，driver 端會在 kernel log 印出違規的位址與來源 master —— 這種 log 是追查 memory corruption 的重要線索，因為它直接指出「是誰」踩到記憶體，而不只是「哪裡」壞掉。

**頻寬監測**
部分平台在 EMI 側提供頻寬計數器，可以看到各個 master 佔用的 DRAM 頻寬比例。當 CPU 的 IPC 明顯偏低、PMU 顯示大量 backend stall 時，這裡的數據能區分是「程式自己的 cache 行為差」還是「整顆 SoC 的記憶體頻寬已經飽和」。這兩者的解法完全不同。

實作面上，這類控制器的 driver 一般落在 kernel 的 `drivers/memory/` 底下，但實際暴露的介面與功能高度依賴平台，看自己專案的 source 為準。

### Electromagnetic Interference

在硬體設計、layout、法規認證（EMC/EMI test）的語境下，EMI 指的是電磁干擾。這個意思在 kernel 或韌體程式碼裡基本上不會出現，看到檔名或 driver 名稱裡有 EMI，都是前者。

---

## 串起來：一個效能問題怎麼分層看

假設遇到的問題是「某個場景下畫面偶爾卡頓」，這三個工具分別回答不同的問題：

**第一層 —— Ftrace：時間花在哪裡？**

先用 tracepoint 拿到全域圖像。sched tracepoint 看是不是被搶佔或沒被排到；irq tracepoint 看是不是某個中斷處理過久；`irqsoff` tracer 看有沒有長時間關中斷的區段。這一層回答「是排程/鎖/中斷的問題，還是純粹計算太慢」。

**第二層 —— PMU：CPU 在忙什麼？**

如果 Ftrace 顯示 CPU 確實一直在跑但就是跑不完，用 `perf stat` 看 IPC。IPC 偏低代表 CPU 大量時間在等，接著看 cache miss 與 TLB miss 的比例，判斷是資料局部性差、還是在等記憶體。這一層回答「這些 cycle 是有效工作還是 stall」。

**第三層 —— EMI：記憶體子系統扛得住嗎？**

如果 PMU 指向記憶體等待，但程式本身的存取模式看起來合理，就要往上一層看整顆 SoC 的頻寬狀況。同時有 camera、video encode、display 在搬資料時，DRAM 頻寬可能已經接近上限，單看 CPU 端永遠找不到原因。這一層回答「這是我的問題，還是鄰居的問題」。

實務上這三層經常需要來回跳。但先確立分層的概念，至少能避免一個常見的浪費：拿著 `perf` 的數據死盯 CPU，而真正的瓶頸在別的 master 上。

---

## 小結

| 縮寫 | 主要意義 | 觀測層次 | 主要工具 |
|---|---|---|---|
| PMU | Performance Monitoring Unit | CPU 微架構 | `perf` |
| PMU | Power Management Unit（另一義） | 電源子系統 | regulator / PMIC driver |
| Ftrace | Function Tracer | Linux kernel | `/sys/kernel/tracing`、trace-cmd、Perfetto |
| EMI | External Memory Interface | SoC 記憶體子系統 | 平台專屬（MPU violation log、頻寬計數器） |
| EMI | Electromagnetic Interference（另一義） | 硬體/法規 | EMC 測試設備 |
