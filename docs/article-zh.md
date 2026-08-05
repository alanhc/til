# 在沒有 Play 商店的 Pixel 8 上，把 CPU、GPU、NPU 都量出來

我手上這台 Pixel 8（代號 shiba，Tensor G3）跑的是自己編的 `AOSP_on_shiba` userdebug build。沒有 GMS、沒有 Play 商店，所以 Geekbench、3DMark、AITuTu 那條路一開始就斷了。

一開始我以為這是個純粹的麻煩。做完之後我的想法變了：**正因為沒有現成的跑分 App，我被迫直接面對系統暴露的原始介面，也才發現三個單元各自都有一個「會給出合理但錯誤數字」的陷阱**——而那些陷阱，包裝好的跑分工具只會幫你把它們藏起來。

這篇是完整的實作紀錄，從探勘裝置開始，到最後一支能一鍵跑完三個單元的 runner。所有程式碼都在 [github.com/alanhc/pixel-bench](https://github.com/alanhc/pixel-bench)。

---

## 一、先問裝置：你到底暴露了什麼

在決定用什麼工具之前，先看系統願意給我什麼。

```bash
adb root
adb shell 'cat /proc/cpuinfo | grep -E "^processor|^CPU part" | paste - -'
```

九顆核心分成三群：`0xd46` ×4（Cortex-A510，1.704 GHz）、`0xd4d` ×4（Cortex-A715，2.367 GHz）、`0xd4e` ×1（Cortex-X3，2.914 GHz），對應 `cpufreq` 的 `policy0`／`policy4`／`policy8`。預設 governor 是 Pixel 自家的 `sched_pixel`，但 `scaling_available_governors` 裡有 `performance` 和 `powersave`——代表**我可以鎖頻**，這是能不能做出可重現量測的關鍵。

GPU 在 `/sys/devices/platform/1f000000.mali`：

```
$ cat gpuinfo
Mali-G715 7 cores r1p2 0x0B080A02
$ cat available_frequencies
890000 850000 807000 723000 649000 580000 521000 467000 419000 376000 337000 302000 150000
```

13 個 DVFS 檔位，而且目錄下有 `power_policy`、`scaling_min_freq`、`scaling_max_freq`、`time_in_state`、`utilization`。同樣可以鎖頻，而且 `time_in_state` 給的是「每個頻率累積待了多少毫秒」——這後來變成整篇文章最有價值的一個檔案。

NPU 的部分讓我意外：

```
$ ls -l /dev/ | grep -i edgetpu
lrwxrwxrwx  edgetpu -> /dev/edgetpu-soc
crw-rw----  system system  edgetpu-soc
$ lsmod | grep -iE "rio|gxp"
gxp   483328  3
rio   430080  4 gxp
```

`rio` 就是 Tensor G3 的 TPU 驅動，而且 `/dev/edgetpu-soc` 的權限是 `system:system 0660`。再往上查：

```
$ adb shell service list | grep -i neural
44  android.hardware.neuralnetworks.IDevice/google-edgetpu
```

**NNAPI 的 EdgeTPU HAL 在純 AOSP build 上是活著的**。這不需要 GMS。我原本以為 TPU 是 Google 自家 App 專屬的東西，結果整條路是通的。

至於現成工具，掃過一遍：`simpleperf`、`perfetto`、`atrace`、`dmabuf_dump` 都在；`flatland`、`stressapptest`、`vulkaninfo` 都不在。所以 CPU 有官方工具可用，GPU 得自己想辦法。

---

## 二、CPU：simpleperf 與三個會說謊的地方

`/system/bin/simpleperf` 就在系統裡，而且 `/proc/sys/kernel/perf_event_paranoid` 是 `-1`，權限完全開放。`/sys/bus/event_source/devices/` 底下有三種 PMU：`armv8_pmuv3`（每核心）、`arm_dsu_0`（cluster 共用的 L3）、`arm_cmn_0`（interconnect，246 個事件）。對想理解「我的程式慢在哪」的人來說，這三層加起來幾乎什麼都能回答。

第一次跑就踩到坑：

```bash
$ adb shell simpleperf stat -e cycles -- sleep 1
simpleperf E event_type.cpp:507] Unknown event_type 'cycles'
```

事件名是 `cpu-cycles` 不是 `cycles`。這種錯誤至少會直接失敗。真正麻煩的是接下來三個**不會失敗、只會給你錯數字**的。

### 陷阱一：`task-clock` 必須放進事件清單

我拿自己寫的一支驅動測試程式量，X3 大核鎖在 2.914 GHz，結果 simpleperf 報 **0.75 GHz**。

原因是 simpleperf 計算「GHz」時的分母：事件清單裡**有** `task-clock` 時用 CPU 時間，**沒有**時退回 wall-clock。那支程式大部分時間在 `ppoll` 上睡覺，wall-clock 遠大於實際運算時間，頻率就被稀釋成四分之一。

驗證很直接：

```
13078186 cycles ÷ 5.539 ms = 2.361 GHz   ← 與 simpleperf 印的一致
```

**結論：`task-clock` 永遠放進去。** 而且要注意，就算放了，若程式會睡眠，你也只該比較 `instructions / cpu-cycles` 這個純比值。

### 陷阱二：一次最多三個硬體事件

這個最陰險。我把想看的都放進去——`cpu-cycles`、`instructions`、`branch-instructions`、`branch-misses`、`L1-dcache-loads`、`L1-dcache-load-misses`——然後量到的頻率變成 1.355 GHz。

在 `scaling_cur_freq` 確認實際跑在 2914000 kHz 的前提下，逐步增加事件數量：

| 硬體事件數 | 回報時脈 |
|---|---|
| 3 | 2.916 GHz ✅ |
| 4 | 2.073 GHz |
| 5 | 1.679 GHz |
| 6 | 1.355 GHz |

這是 **counter multiplexing**：硬體計數器不夠用時，核心會輪流啟用它們。正常的 perf 工具會用 `time_enabled / time_running` 把計數回推補償，但這裡沒有補償——**而 `task-clock` 是軟體事件，硬體計數器被輪換出去時它照跑**。分子縮水、分母不變，所有以它為分母的比值就被系統性壓低。

沒有任何警告。你只會得到一組看起來很合理、但全部偏低三到五成的數字。

解法是把量測拆成多趟，每趟最多三個硬體事件，並在每趟都帶上 `cpu-cycles` 以便交叉比對。

### 陷阱三：通用事件別名不可攜，而且無聲失敗

拆成多趟之後，頻率對了，但 X3 的分支預測失敗率變成 `0.000%`，偶爾又跳成 9.85%——跟中核的 1.06% 完全對不上。

答案在 `simpleperf list raw` 裡。它會標示每個事件支援哪些核心：

```
raw-br-immed-retired  (supported on cpu 0-7)
raw-br-retired        (supported on cpu 0-8)
raw-l1d-cache-refill-rd (supported on cpu 0-3,8)
raw-l1d-cache-refill    (supported on cpu 0-8)
```

`branch-instructions` 這個通用別名對應的是 `raw-br-immed-retired`，**只支援 cpu 0-7**——X3 是 cpu8，不在裡面。同樣地 `L1-dcache-load-misses` 對應 `raw-l1d-cache-refill-rd`，只支援 cpu 0-3 和 8，所以中核那組也是錯的。

換成全核心都支援的原生事件之後：

```
little  br=14062449  miss=803687  5.715%
mid     br=13964980  miss=147998  1.060%
big     br=13945621  miss=130603  0.937%
```

三個叢集的分支總數收斂在 **14M**——同一份指令流本來就該如此。這後來變成腳本內建的自我檢查：**如果三個叢集的分支數對不上，就代表事件選錯了**。壞掉的別名在 X3 上只給 1.7M，一眼就能看出來。

順帶一提，DSU 和 CMN 這兩個 uncore PMU **無法用 per-process 模式開啟**（回 `EINVAL`），必須用 `-a` 系統全域模式，所以那組數字會包含全系統活動。

### CPU 的結果

鎖頻綁核之後（`taskset 0f` / `f0` / `100` 對應小、中、大核），拿 64 MB 的 sha256sum 當負載：

| 叢集 | 核心 | 時脈 | IPC | 分支失敗率 |
|---|---|---|---|---|
| little | Cortex-A510 ×4 | 1.73 GHz | 0.81 | 5.8% |
| mid | Cortex-A715 ×4 | 2.38 GHz | 1.17 | 1.1% |
| big | Cortex-X3 ×1 | 2.84 GHz | 1.13 | 1.0% |

IPC 和分支預測能力的排序正好反映三種微架構的定位。另外加上 `-g powersave` 可以量低功耗情境——三個叢集分別停在 324／402／500 MHz，約峰值的 17–19%，這正好是 `cpuinfo_min_freq` 的值，兩個獨立來源互相印證。

---

## 三、GPU：沒有跑分工具，就換個角度量

這台沒有 `vulkaninfo`、沒有 `flatland`、沒有任何 GPU 跑分 App。AOSP 樹裡雖然有 `flatland` 和 `deqp` 的原始碼，但我的機器 `soong_build` 尖峰吃 26.4 GB、磁碟只剩 24 G，為了一支小工具去啟動全樹分析不划算。

轉機來自一個發現：**我為了測 NPU 而推到裝置上的 TFLite `benchmark_model`，本身就帶 GPU delegate**，走 OpenCL（`/vendor/lib64/libOpenCL.so` 在）。這代表我可以用**同一個工具、同一批模型**比較 CPU、GPU、NPU，數字直接可比。

第一次量的結果很掃興：

```
float32 MobileNet v1，GPU delegate：21.8 ms
float32 MobileNet v1，CPU：       20.3 ms
```

GPU 跟 CPU 一樣快，等於沒用。差點就此下結論說「Mali G715 不值得用」。

### 陷阱四：預設 governor 根本沒升頻

線索在待機時的 `cur_freq`：150000。也就是最低檔。

於是鎖頻再測一次：

```bash
echo always_on > power_policy
echo 890000 > scaling_max_freq
echo 890000 > scaling_min_freq
```

（三個都要寫，缺一不可。）

```
float32：21.8 ms → 6.99 ms   （3.1 倍）
int8：  24.0 ms → 7.83 ms
```

`time_in_state` 解釋了一切。在未鎖頻的一次執行前後各讀一次、相減：

1801 ms 之中有 **1204 ms 待在 150 MHz 的地板**，最高只摸到 376 MHz。加權平均的有效頻率是 **208 MHz，只有 890 MHz 峰值的 23%**。

原因不難理解：每次推論只要 20 毫秒就結束，governor 還沒反應過來就沒事做了。這不是故障，是短促工作負載下 DVFS 的正常行為——但量測時如果不知道，結論就會完全相反。

所以我讓腳本的**每一列都回報 `EFF-MHz`**，由 `time_in_state` 差值反推。這是 GPU 版的「證據」：鎖頻那列如果顯示 890 MHz、駐留 100%，就證明鎖生效了；如果有效頻率偏低，代表鎖沒吃到，而不是 GPU 慢。

### 頻率掃描

既然能鎖任一檔位，乾脆把 13 個檔位全掃一遍：

26 個量測點的 `%PINNED` 全部 100%。有趣的是**時脈拉了 5.9 倍，效能只提升 3.0 倍**——大約 580 MHz 以上就明顯遞減，代表這個工作負載在高頻已經轉為頻寬受限。如果目標是每瓦效能而非絕對延遲，鎖在 580–650 MHz 能拿到大部分好處。

---

## 四、NPU：EdgeTPU 與「它到底有沒有在跑」

有了 `benchmark_model`，指向 EdgeTPU 只是一個參數：

```bash
benchmark_model --graph=mobilenet_v1_1.0_224_quant.tflite \
  --use_nnapi=true --nnapi_accelerator_name=google-edgetpu
```

```
NNAPI accelerators available: [google-edgetpu,nnapi-reference]
Replacing 31 out of 31 node(s) with delegate (TfLiteNnapiDelegate)
Inference (avg): 1000.91 us
```

**1.00 ms，對比 CPU 單執行緒的 33.8 ms——快 34 倍。** 而且這一切都在沒有 GMS 的 AOSP build 上。

但接下來才是重點。

### 陷阱五：NNAPI 會無聲退回 CPU

拿 float32 模型指定同一個加速器：

```
INFO: NNAPI delegate created.
INFO: Though NNAPI delegate is explicitly applied, the model graph
      will not be executed by the delegate.
INFO: Inference (avg): 21140.3 us
```

它照樣印出「delegate created」，甚至回報 31/31 節點被委派，然後**默默退回 XNNPACK 跑在 CPU 上**。21.1 ms 這個數字看起來完全合理——如果不去翻日誌深處那一行，你會以為自己量到了 TPU。

只有 int8 量化圖能上這顆加速器。

### 唯一能一槌定音的證據

`/sys/devices/platform/1a000000.rio/` 底下有 `inference_count`——驅動維護的硬體推論計數器。前後差值應該等於實際推論次數：

```
inference_count 前：1475
inference_count 後：2938        差值 = 1463
benchmark 自報：   480 + 983  = 1463   ✅
```

完全吻合。這是唯一在無聲退回時仍然會露餡的訊號：CPU 執行時差值恆為 0。所以腳本的每一次 NNAPI 執行都做這個檢查，表格裡的 `TPU-INF` 欄就是這個差值。

### 兩個容易忽略的成本

**編譯成本很可觀。** 把 MobileNet 編譯給 TPU 要 1.1–2.1 秒，每個 process 一次。單次推論才 1 ms，所以短命的工作負載根本不該 offload——這一欄往往比 speedup 更能決定架構選擇。

**餵資料的核心會影響加速器成績。** 同一顆 TPU、同一個模型，只因為 host thread 綁在 A510 而不是 X3：

| 綁核 | EdgeTPU 延遲 |
|---|---|
| little (A510) | 1.53 ms |
| big (X3) | 0.93 ms |

**差 62%**，而 TPU 的計算完全沒變——差的是 CPU 側的 delegate 派發開銷。不綁核等於把這個變數交給排程器，數字就沒有可重現性。

---

## 五、串起來：一支 runner

三支腳本各自能跑之後，包成一個 `bench-all.sh`。重點不只是串起來，而是三件事：

**一、必須循序，不能重疊。** CPU 腳本會把所有 cpufreq policy 鎖成 `performance`、GPU 腳本會鎖 Mali 時脈，任一個都會扭曲另一個。而且 GPU/NPU 的成績本來就取決於 CPU 餵資料的速度。

**二、熱量會跨階段累積。** 待機 32–34°C，單一階段峰值到 43°C。接著跑的項目起跑就是熱的，讀數偏慢。所以每個階段前都等所有相關 thermal zone 降到門檻以下：

```
== npu
  cooling: BIG 43.0C > 38C (2s/120s) → 40.0C (10s) → 39.0C (17s) → thermal ok (36.0C)
```

**三、收尾要驗證裝置狀態。** 三支腳本各自有 `trap ... EXIT INT TERM` 還原，但萬一被硬砍，手機會停在鎖頻狀態。Runner 最後會檢查 governor 不是 `performance`、GPU policy 不是 `always_on`，不對就警告並印出修復指令。

跨單元的結果：

| 後端 | 延遲 | 相對單執行緒 |
|---|---|---|
| CPU，1 執行緒 | 33.98 ms | 1.0x |
| GPU，預設 governor | 23.88 ms | 1.4x |
| CPU，8 執行緒 | 20.71 ms | 1.6x |
| GPU，鎖 890 MHz | 7.79 ms | 4.4x |
| EdgeTPU | 1.00 ms | 34x |

（這張表的 CPU 與 TPU 數字取自 NPU 那趟記錄、GPU 數字取自 GPU 那趟，兩趟的 `cpu-8thr` 差約 6%——同一台機器同一天的執行間變異，量級感受不受影響，但要知道它不是單一次執行的快照。）

順帶一個反直覺的觀察：**多執行緒不一定更快**。EfficientNet-Lite0 在單執行緒只要 5.7 ms，開到 8 執行緒反而變成 25.8 ms——同步開銷加上 A510 小核拖後腿，蓋過了平行化的好處。

---

## 六、幾個 Bash 層面的教訓

過程中修掉三個 bug，都不是量測邏輯的問題，但都很值得記：

**`adb shell ... | grep -q` 在 `pipefail` 下是競態。** `grep -q` 一比對到就結束，上游 `adb shell` 收到 SIGPIPE，整條管線被判失敗——誰先寫完誰決定，所以是間歇性的。改成先收進變數再比對。

**awk 不允許同一個名字既當陣列又當純量。** 我在標籤定位用了 `ly[]` 陣列，後面畫圖例時又寫 `ly = H - 18`，直接 fatal error。

**awk 收到不存在的檔案會中止，不會跳過。** 產生報表時傳入了不存在的 `gpu.log`，它在第一個檔案就停下，連後面的 `npu.log` 都沒讀——而 `2>/dev/null` 把錯誤藏起來了，症狀只是「表格是空的」。

---

## 七、NNAPI 已經 deprecated，那之後呢

寫到這裡有個必須交代的問題：**NNAPI 在 Android 15 已被標記為 deprecated**。

先講好消息：**這套工具大部分已經在接班人上了**。`benchmark_model` 本身就是 LiteRT（TFLite 改名後）自己的工具，CPU 的 XNNPACK 和 GPU 的 `--use_gpu` 走的都是現行、未被 deprecated 的 LiteRT delegate。

真正沒有替代品的只有 NPU 那一段：

- LiteRT 的 NPU delegate 目前只有 **Qualcomm** 和 **Intel**，Google Pixel 列在「coming」。
- 走新版 CompiledModel API 的 **Google Tensor SDK 只支援 Tensor G5**（Pixel 10），而且還在 Beta、要申請。Pixel 8 的 G3 不在名單上。

那能不能想辦法繞過去？我實際試了這台上唯一剩下的可能性——`benchmark_model` 有 `--external_delegate_path`，可以載入任意廠商的 delegate `.so`。而 `/vendor/etc/public.libraries.txt` 裡確實列了 `libedgetpu_client.google.so`。

結果：

```
INFO: External delegate path: [/vendor/lib64/libedgetpu_client.google.so]
INFO: EXTERNAL delegate created.
Segmentation fault
```

`inference_count` 差值：**0**。

把符號表拉出來看就懂了——那支函式庫匯出 115 個 C++ 的 `android::darwinn` / `platforms::darwinn` 符號，**沒有任何 C ABI，也沒有 `tflite_plugin_create_delegate`**。TFLite 印的「EXTERNAL delegate created」只是 `dlopen` 成功後的樂觀訊息，接著呼叫不存在的進入點就崩了。

**所以在 Tensor G3 上，deprecated 的 NNAPI 目前仍是唯一的公開 TPU 路徑**，而且它還能用。未來有 G3 可用的 delegate 出現時，`--external_delegate_path` 就是接口，這套腳本不用改。

順帶修正一個流傳的說法：有 issue 稱「Tensor G3 不提供 OpenCL，所以無法做 GPU 推論」。在這台上是錯的——`libOpenCL.so` 就列在 `/vendor/etc/public.libraries.txt`，代表連一般 App 都能透過 sphal namespace 取用，本文所有 GPU 數字都是走它量到的。

---

## 結語

回頭看，這次真正的收穫不是那些數字，而是一個原則：

**量測必須自帶證據。**

三個單元、三種證據：CPU 用「三個叢集的分支總數必須一致」證明事件選對了；GPU 用 `time_in_state` 反推的有效頻率證明鎖頻生效；NPU 用硬體 `inference_count` 證明加速器真的執行了。

這三個檢查都不是為了好看。少了任何一個，我都會得到一組看起來很合理、可以拿去簡報、但是錯的數字——而且錯得毫無徵兆。包裝精美的跑分 App 不會告訴你這些，因為它們的存在意義就是把這一層藏起來。

程式碼、圖表產生器和完整報告都在 [github.com/alanhc/pixel-bench](https://github.com/alanhc/pixel-bench)。

---

## 附錄：本文主張的來源

依照我自己的規矩，公開的技術主張要標明是實測還是引述。

**實測（可在 repo 的 `report/` 或本文指令重跑驗證）**

- CPU 三叢集的拓撲、時脈、IPC、分支與 L1D 失敗率
- `task-clock` 缺席導致的頻率低估
- 事件數 3→6 的時脈衰減（2.916 / 2.073 / 1.679 / 1.355 GHz）
- `simpleperf list raw` 的事件支援遮罩，以及換用原生事件後三叢集分支數收斂於 14M
- DSU／CMN uncore PMU 需要 `-a`
- `powersave` 下三叢集停在 324／402／500 MHz
- Mali 未鎖頻的 `time_in_state` 分布與 208 MHz 有效頻率
- 13 檔位的頻率掃描曲線
- NNAPI EdgeTPU 在 AOSP build 上可用，以及 `inference_count` 1463 對 1463
- float32 模型的無聲退回
- 綁核造成的 TPU 62% 差異
- `libedgetpu_client.google.so` 的符號表內容與 external delegate 的 segfault
- `libOpenCL.so` 列於 `/vendor/etc/public.libraries.txt`

**引述文件（未親自驗證，查證日期 2026-08-05，此類資訊會變動）**

- NNAPI 於 Android 15 deprecated — [NNAPI Migration Guide](https://developer.android.com/ndk/guides/neuralnetworks/migration-guide)
- LiteRT NPU delegate 現況（Qualcomm／Intel 已有，Google Pixel 列為 coming）— [LiteRT NPU overview](https://developers.google.com/edge/litert/android/npu/overview)
- Google Tensor SDK 僅支援 Tensor G5、處於 Beta — [Google Tensor with LiteRT](https://developers.google.com/edge/litert/next/tensor-sdk)

**環境**

Pixel 8（shiba），`AOSP_on_shiba` userdebug，Android 15 `BP1A.250505.005.B1`，kernel `6.1.99-android14-11`。其他 Tensor 裝置需要修改 sysfs 路徑：Mali 節點（`1f000000.mali`）、TPU 節點（`1a000000.rio`）與叢集配置都是 shiba 專屬。
