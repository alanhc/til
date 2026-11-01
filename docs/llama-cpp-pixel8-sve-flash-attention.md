# 在 Pixel 8 上追一個 llama.cpp 的 SVE 效能退化：從綁核實驗到 flash attention

> **2026-11 更正**：本文第五節「真正的原因」把根因歸到 `vec.h` 的展開因子，後來直接反組譯熱點位址，
> 看到的是 `simd-gemm.h` 的 **scalar fallback**（SVE build 被排除在 SIMD microkernel 之外）。
> 前面的實驗與二分結果仍成立，根因請看 [Pixel 8 上的 llama.cpp：NEON、SVE、KleidiAI 三種 build 的逐步實測](llama-cpp-pixel8-neon-sve-kleidiai.md)。

我原本要做的是一件很單純的事：在 Pixel 8 上量 llama.cpp 綁不同 CPU 核心組合的效能差異，看看「把 thread 綁在大核」到底值不值得。

做完之後，我手上有四個東西是一開始沒預期的：

1. 一個交叉編譯的靜默陷阱，會讓你的二進位檔完全沒有 dotprod 和 i8mm，而 cmake 不會警告。
2. 一個推翻我上一篇文章前提的發現：**在 Pixel 上 `scaling_governor` 設成 `performance` 幾乎沒有意義**。
3. 一個可重現的 llama.cpp 效能退化：開啟 SVE 會讓 prompt processing 慢 1.59 倍，而原因不在任何量化 kernel。
4. 一串被我自己的數據推翻的假設 —— 包括四次我以為找到 root cause 的時候，以及**綁核實驗本身的結論在我重跑時翻轉了**。

第 4 點是這篇文章真正想寫的東西。追效能問題時，最貴的不是找不到答案，是**找到一個看起來很對的答案然後停下來**。這篇裡我停下來過四次，每次都以為結束了。

---

## 一、環境與一個編譯期的靜默陷阱

裝置是 Pixel 8（代號 shiba，Tensor G3），跑自己編的 `AOSP_on_shiba` userdebug build，kernel `6.1.99-android14-11`。九顆核心：`cpu0-3` 是 Cortex-A510（1.704 GHz）、`cpu4-7` 是 Cortex-A715（2.367 GHz）、`cpu8` 是 Cortex-X3（2.914 GHz）。

指令集方面 `/proc/cpuinfo` 給的是：

```
asimddp ... sve ... svei8mm svebf16 i8mm bti
```

`asimddp`（dotprod）、`i8mm`、`sve`、`sve2` 都在。用 NDK r29 交叉編譯，照著直覺下指令：

```bash
cmake -B build \
  -DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK/build/cmake/android.toolchain.cmake \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-34 \
  -DCMAKE_BUILD_TYPE=Release -DGGML_OPENMP=OFF
```

cmake 印出這一行：

```
-- Adding CPU backend variant ggml-cpu:
```

冒號後面是空的。看起來只是排版問題，實際上是災難。用 objdump 數指令：

```
smmla (i8mm)  : 0
sdot (dotprod): 0
```

**整個二進位檔一個 dotprod、一個 i8mm 都沒有。**

原因在 `ggml/src/ggml-cpu/CMakeLists.txt`：

```cmake
if (GGML_NATIVE)
    ...  # -mcpu=native 偵測，交叉編譯時 GGML_NATIVE 自動關閉
else()
    if (GGML_CPU_ARM_ARCH)
        list(APPEND ARCH_FLAGS -march=${GGML_CPU_ARM_ARCH})
    elseif(GGML_CPU_ALL_VARIANTS)
        ...
    endif()
endif()
```

交叉編譯時 `GGML_NATIVE` 是關的，`GGML_CPU_ALL_VARIANTS` 預設也是關的，如果你沒設 `GGML_CPU_ARM_ARCH`，兩個分支都不中，`ARCH_FLAGS` 就是空的，`-march` 退回 NDK 預設的 `armv8-a`。不是退回 NEON，是退到 2011 年的基準線。

正確的做法是明確指定：

```bash
-DGGML_NATIVE=OFF -DGGML_CPU_ARM_ARCH="armv8.5-a+fp16+i8mm"
```

這也是上游 CI（`.github/workflows/build-android.yml`）用的值。

順帶一提，`docs/android.md` 建議的是另一套：`-DCMAKE_C_FLAGS="-march=armv8.7a"`。用巨集展開檢查一下：

```
-march=armv8.7a           -> __ARM_FEATURE_BF16, DOTPROD, MATMUL_INT8
-march=armv8.5-a+fp16+i8mm -> DOTPROD, FP16_VECTOR_ARITHMETIC, MATMUL_INT8
```

`armv8.7a` 開了 BF16 卻**沒開** fp16 vector arithmetic（fp16 是 optional extension，不隨版本自動開），CI 那套則相反。兩邊都不完整。而且該文件宣稱「llama.cpp includes runtime checks for available CPU features」—— 那只在 `GGML_CPU_ALL_VARIANTS` + backend DL 的建置下成立，而它推薦的 recipe 不是。

**教訓：cmake 印出來的東西要當成假設，用 objdump 驗證。** 這個習慣在後面救了我不只一次。

---

## 二、`performance` governor 是裝飾品

我上一篇 Pixel 8 跑分的文章寫過一句話：「`scaling_available_governors` 裡有 `performance`，代表我可以鎖頻，這是能不能做出可重現量測的關鍵。」

這句話是錯的。

把三個 cluster 的 governor 都設成 `performance`、確認 `scaling_cur_freq` 等於 `cpuinfo_max_freq` 之後開始跑，跑到一半取樣：

```
bigmax=1164000 bigcur=1164000 midmax=1065000  BIG=63000 MID=62000 soc=44136
```

大核的 `scaling_max_freq` 是 **1.164 GHz**，額定 2.914 GHz 的 40%。而 BIG 的 die 溫度只有 63°C、SoC 44°C —— 以晶片標準完全是冷的。

查下去發現三件事：

```
$ cat /sys/class/thermal/thermal_zone0/mode
disabled
```

**kernel 的 thermal zone 是關的**，`step_wise` governor 根本沒在管。真正在控制的是 userspace：

```
$ ps -A | grep thermal
system  1787  android.hardware.thermal-service.pixel
```

這個 HAL 直接寫 cpufreq cooling device 的 `cur_state`：

```
thermal-cpufreq-0 (LITTLE) cur=2/9   → 1704 → 1425 MHz
thermal-cpufreq-1 (MID)    cur=9/14  → 2367 → 1065 MHz
thermal-cpufreq-2 (BIG)    cur=12/14 → 2914 → 1164 MHz
```

而它的判斷依據不是晶片溫度：

```
$ dumpsys android.hardware.thermal.IThermal/default | grep VIRTUAL-SKIN
 Name: VIRTUAL-SKIN CachedValue: 39319
```

是 HAL 自己估算的**機殼溫度**，39.3°C。還有一個加重因素：

```
 Name: VIRTUAL-USB-THROTTLING CachedValue: 1
```

**插著 USB 這件事本身就是一個 mitigation 觸發源** —— 而跑 adb 就必須插著。

`governor=performance` 只決定「在 `[scaling_min_freq, scaling_max_freq]` 區間內選最高」，而 `scaling_max_freq` 是 HAL 在改的。所以我把 governor 釘死，完全沒有阻止降頻。

### 這個 cap 會在相鄰的兩次執行之間漂移

這才是真正致命的地方。同一個 build、同一個 `taskset`、同一個模型，相隔幾分鐘跑兩次：

| | `scaling_max_freq` (mid/big) | pp512 |
|---|---|---:|
| 第一次 | 910 / 1164 MHz | 49.28 ± 0.09 |
| 第二次 | 712 / 880 MHz | 38.91 ± 0.01 |

每一次量測本身都極穩定（±0.09、±0.01），但兩次之間差 27%。

我因此製造出一個假數據。在對照兩個 build 時，我量到「SVE 慢 2.15×」，隔一輪再量是「2.16×」，我當時的推理是「比值在兩輪之間一致，所以可信」。

那個推理是錯的。兩輪之所以一致，是因為**系統性偏差在兩輪都存在** —— 兩次都剛好是 build-a 先跑（cap 較鬆）、build-b 後跑（cap 已收緊）。在相同頻率下重測，真實倍數是 **1.59×**。

一致性不等於正確性。當你的誤差來源是系統性的，重複量測會給你信心而不是真相。

### 記憶體頻率完全鎖不住

還有一個我一開始整個漏掉的變因：

```
$ cat /sys/class/devfreq/17000010.devfreq_mif/cur_freq
845000        # 上限是 3744000，governor 是 interactive
```

記憶體介面（MIF）頻率有 9 倍的變動範圍，而且：

```bash
$ echo 3744000 > /sys/class/devfreq/17000010.devfreq_mif/min_freq
$ cat min_freq
3744000
# 五秒後
$ cat min_freq
421000
```

**寫進去五秒內被 daemon 改回去。** 我沒找到能停掉它又不失去熱保護的方法。

這個變因害我又報廢一組數據：同一個 build、同一個 taskset、**相同的 CPU 頻率上限**，兩次 `tg128` 是 10.25 和 4.17 —— 差 2.5 倍。因為 token generation 是記憶體頻寬受限的。

後來的量測顯示 `pp512` 對 MIF 幾乎不敏感（MIF 平均值在 918–1340 MHz 之間變動時，pp512 穩定在 24.5±0.1），但 `tg128` 非常敏感。

### 最後採用的協定

既然鎖不住，就記錄下來並讓漂移對所有受測對象平均分攤：

1. `adb root`（thermal zone 和 devfreq 都需要）
2. 每組配置**用它自己的工作點**先跑約 60 秒 conditioning（cap 進入平台期需要約 40 秒）
3. 輪詢 `scaling_max_freq` 直到連續 3 次不變才開始量
4. 量測期間以 1 Hz 取樣 cpufreq + `devfreq_mif` + `devfreq_dsu`，**把頻率印在每一列數據旁邊**
5. 比較多個 build 時**交錯執行**（a, b, c, a, b, c），不要跑完 a 的所有重複再跑 b

第 4 點是重點：不能控制的變因，至少要讓它可見。任何一列數據都應該能被讀者拿去檢查「這是在什麼頻率下量的」。

---

## 三、`-t` 的預設值在 ARM 大小核上等於全部核心

llama-bench 在這台機器上的預設 thread 數是 **9**，也就是全部核心。來源是 `common/common.cpp`：

```c
int32_t common_cpu_get_num_math() {
#if defined(__x86_64__) && defined(__linux__) && !defined(__ANDROID__)
    ...  is_hybrid_cpu() / cpu_count_math_cpus()   // P-core/E-core 偵測
#elif defined(__powerpc64__) || defined(__powerpc__)
    ...
#endif
    return common_cpu_get_num_physical_cores();     // ARM 走這裡
}
```

**混合核心的偵測邏輯只有 x86 有，而且明確排除 Android。** ARM 一律掉到 `common_cpu_get_num_physical_cores()`，那個函式在 Linux 上是數 `/sys/devices/system/cpu/cpuN/topology/thread_siblings` 的唯一值。Pixel 8 沒有 SMT，九顆核心 = 九個唯一值 = 回傳 9。

（函式尾端那個 `n_threads <= 4 ? n_threads : n_threads / 2` 的保底邏輯只有在 sysfs 讀不到時才會走到。）

`-t 9` 在 token generation 上確實比較差，這個方向在我每一輪量測中都成立（同一輪內 `-t 9` 是 6.60 t/s，`-t 4` 是 8.72）。

但我還觀察到一件**沒能穩定重現**的事，寫出來是因為它可能對別人有意義。三次 `default-t9` 的逐次取樣：

```
第一次  tg128: [2.05, 2.82, 5.21, 10.93, 3.66]   → ±3.55
第二次  tg128: [0.52, 1.05,  9.19,  9.10, 2.33]   → ±4.35   最好與最差差 18 倍
第三次  tg128: [6.30, 6.60,  6.19,  7.15, 6.76]   → ±0.39   完全正常
```

前兩次出現極端的執行間跳動，第三次沒有。同一次執行裡的 `pp512` 全都穩定在 ±0.1 以內，頻率取樣也顯示 cap 沒有變動 —— 所以那兩次的跳動不是熱造成的。但我找不出第三次跟前兩次的差異在哪（唯一的變化是 conditioning 從 22 秒拉長到 60 秒），**所以我不能說這是 `-t 9` 的性質**。它可能是排程器的某種偶發狀態，也可能是我的量測環境還有沒控制到的東西。

我原本想把這個現象跟 [#21763](https://github.com/ggml-org/llama.cpp/issues/21763)（MediaTek Dimensity 9500s 上 threads 超過大核數時的 100 倍崩潰，被 stale bot 關掉、沒有 maintainer 回應）連起來，但一個自己重現不出來的觀察不該拿去附和別人的 bug report。留在這裡當作紀錄。

至於預設值本身該不該改，上游已經有討論：[#14532](https://github.com/ggml-org/llama.cpp/pull/14532) 提議在 AArch64 上偵測大核，還開著；[#13079](https://github.com/ggml-org/llama.cpp/pull/13079) 的 futex barrier 針對的是混合架構上的同步效率。

---

## 四、綁核矩陣：答案對了，但不穩定

量測用 Qwen2.5-1.5B-Instruct Q4_K_M，`-r 5`，全部在第二節那套穩態協定下跑。前五組的 CPU 頻率上限完全相同，可以直接比：

| 配置 | pp512 (t/s) | tg128 (t/s) | little/mid/big GHz | MIF 平均 MHz |
|---|---:|---:|---|---:|
| 不綁定 `-t 9`（llama-bench 預設） | 35.01 ± 0.08 | 6.60 ± 0.39 | 0.610 / 0.712 / 0.880 | 957 |
| 不綁定 `-t 4` | 36.31 ± 0.12 | 8.72 ± 0.09 | 0.610 / 0.712 / 0.880 | 1054 |
| 不綁定 `-t 8` | 34.29 ± 0.85 | 8.58 ± 0.34 | 0.610 / 0.712 / 0.880 | 1186 |
| **`taskset 1f0 -t 5`（X3 + 4× A715）** | **38.96 ± 0.04** | **10.07 ± 0.10** | 0.610 / 0.712 / 0.880 | 1180 |
| `taskset f0 -t 4`（4× A715） | 31.15 ± 0.02 | 8.50 ± 0.03 | 0.610 / 0.712 / 0.880 | 1081 |
| `taskset 100 -t 1`（單 X3） | 14.53 ± 0.01 | 3.61 ± 0.01 | 0.953 / 0.712 / 0.880 | 605 |
| `taskset f -t 4`（4× A510） | 14.52 ± 0.04 | 4.24 ± 0.01 | 0.955 / 0.712 / 0.880 | 646 |

綁在 X3 + 4 顆 A715（`taskset 1f0 -t 5`）在兩個指標上都是第一，pp512 比第二名高 7%、tg128 高 15%，而且變異最小。看起來就是教科書答案：綁大核和中核，避開小核。

**但這個結論不穩定。**

我第一次跑同一個矩陣時，贏家是 `unbound -t 8`（pp512 44.15 vs 38.87）。差別在頻率分配：

| | little | mid | big |
|---|---|---|---|
| 第一次 | **0.925–0.993 GHz** | 0.712 | 0.880 |
| 第二次 | **0.610 GHz** | 0.712 | 0.880 |

第一次小核被分到 0.93–0.99 GHz，**比大核的 0.880 還高** —— 那個情況下刻意排除小核就是丟掉最快的核心。第二次小核只有 0.610 GHz，遠低於大核，排除它就變成正確選擇。

同樣的 `taskset` 遮罩，兩次拿到的頻率預算不同，結論就翻轉。而我無法控制那個分配。

更進一步：看 `big-t1` 和 `little-t4` 這兩列，它們的 little cap 被放寬到 0.953/0.955 GHz，MIF 也掉到 605/646 MHz。**HAL 的頻率分配會回應你選了哪些核心** —— 用得少、發熱少，它就把預算還給你一部分。這不是量測雜訊，是系統的真實行為，也代表在這台機器上「綁哪些核心」和「拿到多少頻率」這兩件事無法分離。

所以我對原始問題的回答是：

- **在單一 session 內，綁 X3 + A715 通常是對的**，而且值得做 —— 比預設值快 11%（pp）和 53%（tg）。
- **但不要把某次量到的倍數當成常數。** 我兩次量到相反的排名，兩次的數據本身都乾淨（±0.04 到 ±0.85）。
- **`-t 9`（預設值）在 tg 上是明顯最差的**，這個方向在兩輪都成立。如果只能記一件事，就是**別用預設的 thread 數**。

另外兩個小觀察：4 顆 A510（14.52）和 1 顆 X3（14.53）的 pp512 幾乎相同，但 tg128 是小核贏（4.24 vs 3.61）—— 在記憶體受限的 token generation 上，四顆慢核比一顆快核有用。

---

## 五、SVE：五次假設，四次被自己推翻

這條線是意外撿到的。

我一開始建了兩個 build 做對照：`armv8.5-a+fp16+i8mm`（無 SVE）和 `armv9-a+fp16+dotprod+i8mm+sve2`。想法很單純 —— Pixel 8 是 ARMv9，有 SVE2，那就開起來。

結果 SVE 版的 pp512 明顯較慢。

在往下講之前，先講一個編譯旗標的陷阱：我另外建了一個 `armv9-a+fp16+dotprod+i8mm`（沒寫 `+sve2`），出來的二進位檔跟有寫的**一模一樣**。因為 **SVE2 在 ARMv9-A 是強制的**，clang 自動打開。要關掉只能明確寫 `+nosve`。

也就是說，任何人看到 Pixel 8 是 ARMv9 就填 `-march=armv9-a` —— 最直覺的選擇 —— 就會踩到，而且完全沒有警告。

更重要的是，**官方 Android build 也會踩到**。`ggml/src/CMakeLists.txt` 裡有 Android 專屬的執行期 variant 清單：

```cmake
ggml_add_cpu_backend_variant(android_armv8.6_1  DOTPROD FP16_VECTOR_ARITHMETIC MATMUL_INT8)       # 無 SVE
ggml_add_cpu_backend_variant(android_armv9.0_1  DOTPROD MATMUL_INT8 FP16_VECTOR_ARITHMETIC SVE2)  # 有 SVE2
```

實測確認 —— 把這個 `GGML_CPU_ALL_VARIANTS` build 推到裝置上跑，dispatcher 自己說了：

```
load_backend: loaded CPU backend from .../libggml-cpu-android_armv9.0_1.so
```

Pixel 8 拿到的是含 SVE2 的那個。任何有 SVE2 而無 SME 的 ARMv9 手機在這套規則下應該都是同樣結果，不過我手上只有這一台，其他機型算推論。

那實際差多少？把 `libggml-cpu-android_armv9*.so` 移出搜尋路徑，強迫 dispatcher 退回 `android_armv8.6_1`（i8mm、無 SVE），兩者交錯對照：

| dispatcher 選到 | pp512 (t/s) | tg128 (t/s) |
|---|---:|---:|
| `android_armv9.0_1`（預設） | 34.85 ± 0.01 | 14.00 ± 0.10 |
| `android_armv8.6_1`（強制退回） | **56.55 ± 0.08** | 14.06 ± 0.08 |

**1.62×**，跟我用自訂 `-march` 量到的 1.59× 一致。而且這裡沒有任何自訂編譯旗標 —— 這就是官方 `GGML_CPU_ALL_VARIANTS` build 在這台裝置上的行為。`tg128` 一如既往沒有差異。

### 假設一：手機核心的 SVE 算術吞吐量比較低

合理的猜測。Cortex-X3/A715/A510 的 SVE 可能只是為了 ARMv9 相容性而實作，微架構上不如同寬的 NEON。

寫了 microbenchmark 驗證：8 個獨立累加器（量吞吐量而非延遲鏈）、結果換算成 **cycles/op**（讀 `scaling_cur_freq` 歸一化，因為 HAL 會在測試中途改頻率）、NEON 和 SVE 交錯執行取最佳值。

```
                    NEON c/op   SVE c/op  SVE/NEON
dot   (sdot/svdot)     0.256      0.258     0.990   <- Cortex-X3
mmla  (smmla/svmmla)   0.256      0.284     0.900
```

三顆核心的比值都在 0.90–1.00。**假設一否定。**

### 假設二：SVE 的載入比較慢

第一版 probe 顯示 SVE 載入只有 NEON 的 1/3 吞吐量。看起來是個漂亮的答案 —— 量化 kernel 是載入密集的，這完全說得通。

然後我用 objdump 檢查了自己的 benchmark：

```
neon_load :      17 add                    <- 0 個載入指令
sve_load  :      16 add       8 ld1
```

**編譯器把 NEON 版的載入 hoist 出迴圈了**（位址不變，LICM 直接搬走），SVE 版沒有。我量的是「SVE 真的載入」對上「NEON 什麼都不做」。

加上編譯器屏障重測，比值變成 0.93–1.01。**假設二否定，而且是被我自己的方法學問題製造出來的。**

（不過這次除錯有個副產品：NEON 用 `ldp` 一道指令載入兩個 128-bit 向量，SVE 沒有對應的 load-pair。這個觀察後來變成答案的一部分。）

### 假設三：退化幅度是 2.15×

前面已經講過了 —— 頻率漂移造成的假象，真實值 1.59×。**假設三否定。**

### 假設四：`svmad_f32_m` 的 merging predication

這個假設是有紮實依據的。`ggml/src/ggml-cpu/simd-mappings.h` 的 SVE 分支：

```c
#define GGML_F32xt_FMA_IMPL(pg, a, b, c)  svmad_f32_m(pg, b, c, a)
#define GGML_F32xt_ADD_IMPL(pg, a, b)     svadd_f32_m(pg, a, b)
#define GGML_F32xt_MUL_IMPL(pg, a, b)     svmul_f32_m(pg, a, b)
```

全部用 merging predication（`_m` 後綴）。`_m` 的語意是「非作用中的 lane 保留第一個運算元」，所以目的暫存器必須是那個運算元。但 `DEFAULT_PG` 是 `svptrue_b32()` —— **所有 lane 都作用，`_m` 和 `_x` 語意完全相同**，那個 merging 保證是白付的。

實測：

| | NEON `vfmaq` | SVE `svmad_f32_m` | SVE `svmad_f32_x` | `_m` 代價 |
|---|---:|---:|---:|---:|
| Cortex-X3 | 0.2522 | **1.0094** | 0.2538 | **4.00×** |
| Cortex-A715 | 0.5036 | **1.0071** | 0.5035 | **2.00×** |
| Cortex-A510 | 0.6357 | **1.5967** | 0.6351 | **2.51×** |

`_m` 慢 2–4 倍，`_x` 跟 NEON 完全等速。編出來的指令也對得上：`_m` → `fmad`（目的暫存器是被乘數），`_x` → `fmla`（累加器形式）。而 `MUL` 不受影響（比值 1.000）。

旁證更強：**同一個檔案的 F16 版本已經是 `_x` 了**（`simd-mappings.h:229`：`svmad_f16_x`）。F32 那行看起來就是漏改的。

我把它改成 `_x`、重編、重測。

**端到端效果是零。** 24.48 vs 24.55，在誤差內。**假設四否定。**

答案在反組譯裡。把 SVE build 的 `ggml_compute_forward_flash_attn_ext` 裡的 SVE 指令抓出來：

```
25 st1w    21 ld1w    19 fmul    8 mov    2 fadd
```

載入–乘法–儲存，**一個 FMA 都沒有**。熱迴圈是 `ggml_vec_scale_f32`，它只用 MUL。我修的是一條根本沒被執行到的路徑。

指令層級的發現不等於瓶頸。這是這次最貴的一課。

### 用二分法找到範圍

停止猜測，改用切割。在 `ggml/src/ggml-cpu/CMakeLists.txt` 的 `target_compile_options` 之後插入：

```cmake
if (GGML_EXPERIMENT_NOSVE_FILES)
    set_source_files_properties(${GGML_EXPERIMENT_NOSVE_FILES}
        PROPERTIES COMPILE_OPTIONS "-march=armv9-a+fp16+dotprod+i8mm+nosve")
endif()
```

這樣可以**指定單一編譯單元退回 NEON，其餘保持 SVE**。用 objdump 確認隔離真的生效（`ops.cpp.o` 的 SVE 指令數變成 0，`quants.c.o` 還有 141 個），然後逐檔測。

全部在相同 CPU 頻率上限 `[mid 712 / big 880 MHz]` 下，交錯執行多輪：

| build | 說明 | pp512 (t/s) | 相對全 SVE |
|---|---|---:|---:|
| b | 全 SVE | 24.59 | — |
| j | 只有 `vec.cpp` 編 NEON | 25.49 | +3.7% |
| **i** | **只有 `ops.cpp` 編 NEON** | **38.59** | **+56.9%** |
| h | 兩個都編 NEON | 39.08 | +58.9% |
| a | 全 NEON | 39.13 | +59.1% |

`i` 和 `j` 的效果相加幾乎等於 `h`，代表兩者獨立可加。**`ops.cpp` 一個檔案解釋了 96.6% 的退化。** 而 `h` 和 `a` 相差 0.1% —— **保留全部 SVE 量化 kernel 完全沒有代價**。

simpleperf 給出獨立的第二條證據：

| 函式 | 全 NEON | 全 SVE |
|---|---:|---:|
| `ggml_gemm_q4_K_8x8_q8_K` | 56.78% | 33.28% |
| **`ggml_compute_forward_flash_attn_ext`** | **6.01%** | **34.17%** |

兩個 build 的 GEMM 走同一份 NEON i8mm 程式碼，拿它當內部基準：`flash_attn / gemm` 的比值從 0.106 變成 1.027，**flash attention 貴了 9.7 倍**。

### 真正的原因

> **2026-11 更正**：下面這段的推論有誤。這裡數的是 FA 裡的 **SVE 指令**，而真正的熱迴圈是 **scalar** `fmadd`，
> 不會出現在這種統計裡。用 `simpleperf report --sort vaddr_in_file` 找熱位址再反組譯，熱點落在
> `simd-gemm.h` 的 scalar `simd_gemm`：`#if defined(GGML_SIMD) && !defined(__ARM_FEATURE_SVE) ...` 讓 SVE build
> 的 tiled flash attention 退回三層純量迴圈。`ops.cpp` 編回 NEON 能修好，是因為 `simd-gemm.h` 就是被 `ops.cpp` include 的。
> 詳見[新文第五、六節](llama-cpp-pixel8-neon-sve-kleidiai.md)；上游 issue
> [ggml-org/llama.cpp#30051](https://github.com/ggml-org/llama.cpp/issues/30051)。

`vec.h` 的 `ggml_vec_scale_f32`，SVE 路徑：

```c
const int sve_register_length = ggml_cpu_get_sve_cnt() * 8;
const int ggml_f32_epr  = sve_register_length / 32;   // SVE128:4, SVE256:8
const int ggml_f32_step = 2 * ggml_f32_epr;           // <- 展開因子寫成「暫存器數」
```

NEON 路徑用的是 `GGML_F32_STEP 16`（4 個暫存器 × 4 個 float）。

在 **256-bit** 機器上，`2 × 8 = 16`，剛好等於 NEON 的 16 —— 完全打平。
在 **128-bit** 機器上，`2 × 4 = 8`，**只有 NEON 的一半**。

同樣的工作要跑兩倍的迴圈次數。加上另外兩個效應：

- **SVE 沒有 `ldp`/`stp`**，連續向量載入/儲存需要兩倍的記憶體指令
- **`ggml_f32_epr` 是執行期值**（來自跨編譯單元的 `ggml_cpu_get_sve_cnt()`，沒有 LTO），編譯器無法常數摺疊、無法額外展開、只能用暫存器索引定址

反組譯直接看得到第三點：

```
SVE : ld1w { z16.s }, p0/z, [x13, x9, lsl #2]    <- 暫存器索引
NEON: ldp  q16, q17, [x10, #0x20]                 <- 立即值偏移，一次兩個向量
```

三個效應同一個成因：**這段 SVE 程式碼是為「執行期未知、且通常較寬的向量長度」寫的**。在 256-bit 機器上第一點剛好抵銷，第二三點也被「一次處理兩倍資料」攤薄。128-bit 機器沒有這個補償。

而 microbenchmark 已經排除了微架構因素（逐指令吞吐量 SVE ≈ NEON），所以成本純粹來自指令數量和定址方式。

### 為什麼上游沒發現

查了 llama.cpp 所有跟 128-bit SVE 相關的 PR：

| PR | 測試硬體 | 宣稱 |
|---|---|---|
| [#9290](https://github.com/ggml-org/llama.cpp/pull/9290) | A64FX、Grace VM | 128-bit SVE 比 NEON 快 1.1–1.5× |
| [#15277](https://github.com/ggml-org/llama.cpp/pull/15277) | AWS Graviton3 | pp512 +28% |
| [#27491](https://github.com/ggml-org/llama.cpp/pull/27491) | NVIDIA Grace | 比 NEON 快 4–5% |

**全部是 server 級 Neoverse 核心。沒有一個在 ARM 手機核心上測過。**

而且值得注意：[#26957](https://github.com/ggml-org/llama.cpp/issues/26957) 回報 Snapdragon 8 Gen 2（Cortex-X3 + A715 + A510，跟 Tensor G3 同一組核心）上有 Android arm64 效能退化，回報者提到「runtime auto-selects the armv9.2 CPU variant」—— 那正是含 SVE 的 variant。

---

## 六、方法學：六個讓我上當的地方

寫給未來的自己。

**1. cmake 說了什麼不算數，objdump 說了才算。** `Adding CPU backend variant ggml-cpu:` 後面空白，二進位檔就是 0 個 SIMD 指令。

**2. 一致的比值不等於正確的比值。** 系統性偏差會在重複量測中重現，給你信心而不是真相。要對抗它，得交錯執行，並且記錄你懷疑的那個變因。

**3. 「頻率」在 SoC 上不只一個。** 我兩次宣稱「頻率穩定所以數據可比」，兩次都只檢查了 CPU 的 `scaling_max_freq`。記憶體介面頻率有 9 倍的變動範圍，而且鎖不住。

**4. 你的 microbenchmark 也需要被 review。** 那個「SVE 載入慢 3 倍」的結論，是因為編譯器把對照組的載入 hoist 出迴圈了。寫完 benchmark 要 objdump 檢查兩邊真的在做同樣的事。

**5. 指令層級的發現不等於瓶頸。** `svmad_f32_m` 慢 2–4 倍是真的，三顆核心一致。改掉它端到端效果是零，因為熱迴圈裡一個 FMA 都沒有。**先 profile，再優化** —— 這句話老掉牙，但我還是先優化了。

**6. 在一個你無法控制所有變因的系統上，一次乾淨的量測不等於一個穩定的結論。** 綁核矩陣我跑了兩次，兩次的數據都乾淨（標準差 ±0.04 到 ±0.85），但排名相反。差別是 thermal HAL 那次剛好怎麼分配頻率預算。乾淨的誤差棒只告訴你「這次量得很準」，不告訴你「換個時間再量還會是這樣」。要判斷後者，唯一的辦法是真的換個時間再量一次 —— 而我原本不打算做，是因為別的理由才重跑，才發現的。

真正有效的工具只有兩個：**profile 告訴你時間在哪**，**二分切割告訴你程式碼在哪**。`set_source_files_properties` 那招（讓單一編譯單元用不同的 `-march`）在追這類「整個 ISA 分支」的問題時特別好用，因為它不需要改任何一行 C 程式碼。

---

## 七、給想重現的人

所有量測用的腳本在 `~/llama.cpp/`：`bench-shiba-v2.sh`（綁核矩陣，含頻率取樣）、`abg-compare.sh`（多 build 交錯對照）、`sve-vs-neon-probe.c` 和 `fp-probe.c`（指令層級 microbenchmark）。

環境：llama.cpp commit `6657ded4faa3b8450221119fc6b4d002e35104a2`、NDK r29（clang 21.0.0）、`arm64-v8a` / `android-34`、Qwen2.5-1.5B-Instruct Q4_K_M、Pixel 8 kernel `6.1.99-android14-11`、Android 15 userdebug。

一個必須說清楚的限制：**這份數據全部是在 thermal HAL 施加的降頻狀態下量的**（big 0.880 GHz / mid 0.712 GHz，額定值的 30%）。這代表持續負載下的真實情境，但不代表短時互動的峰值效能。冷開機峰值我量不出可重複的數據 —— cap 解除的速度大約是每 80 秒降 0.12°C 的機殼溫度，要把七組配置各量一次得花好幾個小時，而且中途任何一次都會把裝置重新加熱。

MIF 頻率無法鎖定這件事也代表 `tg128` 的絕對值有一定的不確定性。`pp512` 對此不敏感（實測 MIF 在 918–1340 MHz 之間變動時 pp512 穩定在 ±0.1），所以 SVE 那條線的結論不受影響。
