# Pixel 8 上的 llama.cpp：NEON、SVE、KleidiAI 三種 build 的逐步實測

這是一份**照著打就能重現**的學習筆記：在 Pixel 8（Tensor G3）上交叉編譯三種 llama.cpp CPU build，
量 prefill／decode，再用 simpleperf 和反組譯找出「開 SVE 反而變慢」的原因。每一步的指令都在。

結論先講：

1. **SVE build 的 prefill 比 NEON 慢 35–40%，prompt 越長越慘（pp512 只剩一半）。** 原因不在量化 kernel，
   而是 `simd-gemm.h` 的條件編譯把 SVE 排除在外，tiled flash attention 退回 **scalar** 三層迴圈。
2. **KleidiAI 讓 Q8_0／Q6_K 的 prefill 快 1.8–2.3 倍**；Q6_K 跟 Q8_0 一樣快，是因為載入時就被 repack 成 Q8。
   Q4_0 反而變慢，因為它蓋掉了 ggml 自己的 Q4_0 repack 路徑。
3. Decode（tg）三種 build 幾乎一樣，瓶頸是記憶體頻寬。

> **更正前文**：[在 Pixel 8 上追一個 llama.cpp 的 SVE 效能退化](llama-cpp-pixel8-sve-flash-attention.md)
> 把根因歸到 `vec.h` 的展開因子。這次直接反組譯熱點位址，看到的是 scalar `fmadd`，詳見第六節。

---

## 一、環境

| 項目 | 值 |
|---|---|
| 裝置 | Pixel 8（`shiba`），自編 `aosp_shiba` userdebug，bootloader 已解鎖 |
| Kernel | `6.1.99-android14-11` |
| 主機 | x86_64 Ubuntu |
| llama.cpp | upstream `0ec4027a2`（2026-10-30） |
| NDK | r27c |
| 模型 | [Qwen/Qwen2.5-0.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF) 官方 q8_0／q6_k／q4_0 |

### 1.1 先看裝置

```bash
adb devices -l
adb shell getprop ro.product.device          # shiba
adb shell getprop ro.build.type              # userdebug
adb shell getprop ro.boot.flash.locked       # 0 = 已解鎖
```

CPU 拓撲與指令集：

```bash
adb shell 'cat /proc/cpuinfo | grep "CPU part" | uniq -c'
adb shell 'cat /proc/cpuinfo | grep -m1 Features'
adb shell 'for c in 0 4 8; do echo cpu$c $(cat /sys/devices/system/cpu/cpu$c/cpufreq/cpuinfo_max_freq); done'
```

| cpu | 核心 | `CPU part` | 最高頻率 |
|---|---|---|---|
| 0–3 | Cortex-A510 | `0xd46` | 1.70 GHz |
| 4–7 | Cortex-A715 | `0xd4d` | 2.37 GHz |
| 8 | Cortex-X3 | `0xd4e` | 2.91 GHz |

Features 裡跟這次有關的：`asimddp i8mm sve sve2 svei8mm svebf16 bf16`。
**SVE 向量長度是 128-bit**，跟 NEON 一樣寬——這是後面一切的伏筆。

### 1.2 下載 NDK、模型、原始碼

```bash
mkdir -p ~/pixel8-llama/{dl,models,raw} && cd ~/pixel8-llama

curl -L -o dl/ndk.zip https://dl.google.com/android/repository/android-ndk-r27c-linux.zip
(cd dl && unzip -q ndk.zip)

for q in q8_0 q6_k q4_0; do
  curl -L -o models/qwen2.5-0.5b-instruct-$q.gguf \
    https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-$q.gguf
done

git clone https://github.com/ggml-org/llama.cpp src
git -C src log -1 --format='%h %cd %s'
```

---

## 二、交叉編譯三種 build

三種 build 只差 `GGML_CPU_ARM_ARCH` 和 KleidiAI 開關：

| 名稱 | `GGML_CPU_ARM_ARCH` | 其他 |
|---|---|---|
| neon | `armv8.2-a+dotprod+i8mm+fp16` | |
| sve | `armv9-a+i8mm+bf16` | |
| kleidi | `armv8.2-a+dotprod+i8mm+fp16` | `-DGGML_CPU_KLEIDIAI=ON` |

```bash
cd ~/pixel8-llama/src
NDK=~/pixel8-llama/dl/android-ndk-r27c

b() {
  name=$1; arch=$2; shift 2
  cmake -S . -B build-$name -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE=$NDK/build/cmake/android.toolchain.cmake \
    -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-31 \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
    -DGGML_OPENMP=OFF -DLLAMA_CURL=OFF -DLLAMA_OPENSSL=OFF \
    -DGGML_NATIVE=OFF -DGGML_CPU_ARM_ARCH=$arch "$@" &&
  cmake --build build-$name -j --target llama-bench llama-cli llama-completion
}

b neon   armv8.2-a+dotprod+i8mm+fp16
b sve    armv9-a+i8mm+bf16
b kleidi armv8.2-a+dotprod+i8mm+fp16 -DGGML_CPU_KLEIDIAI=ON
```

**確認 `-march` 真的有吃進去**（ninja 預設不印編譯指令，要去 `build.ninja` 找）：

```bash
for v in neon sve kleidi; do
  echo $v: $(grep -o 'march=[^ ]*' build-$v/build.ninja | sort -u | tr '\n' ' ')
done
```

kleidi 那份會多出一堆 `armv8.2-a+sve+...`，那是 KleidiAI 自己的多版本 kernel，正常。

### 2.1 strip 後推到手機

沒 strip 的 `llama-bench` 有 136 MB，strip 後 5.7 MB：

```bash
S=$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip
adb shell mkdir -p /data/local/tmp/llm/models
for v in neon sve kleidi; do
  $S -o ../raw/llama-bench-$v build-$v/bin/llama-bench
  adb push ../raw/llama-bench-$v /data/local/tmp/llm/
done
adb push ../models/. /data/local/tmp/llm/models/
adb shell chmod +x /data/local/tmp/llm/llama-bench-*
```

> 坑：這版 adb 的 `push` 沒有 `-q` 選項。

---

## 三、量測腳本

### 3.1 拿溫度要 root

```bash
adb shell cat /sys/class/thermal/thermal_zone0/type    # Permission denied
adb root                                                # userdebug 才可以
adb shell 'for z in /sys/class/thermal/thermal_zone*; do echo "$(cat $z/type)=$(cat $z/temp)"; done'
```

`thermal_zone0` 是 `BIG`（大核叢集），之後用它決定要不要等降溫。

### 3.2 先跑一次確認 CSV 欄位

```bash
adb shell 'cd /data/local/tmp/llm; taskset 100 ./llama-bench-neon \
  -m models/qwen2.5-0.5b-instruct-q4_0.gguf -t 1 -p 16 -n 4 -r 1 -o csv'
```

最後四欄是 `avg_ns,stddev_ns,avg_ts,stddev_ts`，用 `"` 切開後取倒數第 4、第 2 欄就是 t/s 和標準差。

### 3.3 `bench.sh`

三種 build × 三種 quant × 三種核心組合，每組開跑前等 BIG < 38°C：

```sh
#!/system/bin/sh
cd /data/local/tmp/llm
t() { cat /sys/class/thermal/thermal_zone0/temp; }
cool() { while [ $(t) -gt 38000 ]; do sleep 5; done; }
for v in neon sve kleidi; do
 for q in q8_0 q6_k q4_0; do
  for cfg in "100:1:X3x1" "f0:4:A715x4" "1f0:5:X3+A715" ; do
   mask=${cfg%%:*}; rest=${cfg#*:}; n=${rest%%:*}; name=${rest#*:}
   cool; t0=$(t)
   out=$(taskset $mask ./llama-bench-$v -m models/qwen2.5-0.5b-instruct-$q.gguf \
         -t $n -p 128 -n 32 -r 3 -o csv 2>/dev/null | tail -2)
   echo "$v,$q,$name,$t0,$(t),$(echo "$out" | sed -n 1p | awk -F'"' '{print $(NF-3)","$(NF-1)}')"
   echo "$v,$q,$name,$t0,$(t),$(echo "$out" | sed -n 2p | awk -F'"' '{print $(NF-3)","$(NF-1)}')"
  done
 done
done
```

`taskset` 的 mask：`100` = cpu8（X3）、`f0` = cpu4–7（A715）、`1f0` = cpu4–8。

```bash
adb push bench.sh /data/local/tmp/llm/
adb shell sh /data/local/tmp/llm/bench.sh | tee raw/bench.csv
```

---

## 四、結果

**pp128 prefill，tokens/s（± 為 r=3 標準差）**

| build | quant | X3×1 | A715×4 | X3+A715（t5） |
|---|---|---:|---:|---:|
| neon | Q8_0 | 200 ± 6 | 476 ± 3 | 592 ± 1 |
| neon | Q6_K | 113 ± 5 | 373 ± 3 | 394 ± 65 |
| neon | Q4_0 | 231 ± 24 | 490 ± 2 | 589 ± 59 |
| sve | Q8_0 | 125 ± 10 | 305 ± 2 | 367 ± 3 |
| sve | Q6_K | 104 ± 8 | 258 ± 0 | 311 ± 3 |
| sve | Q4_0 | 153 ± 6 | 312 ± 1 | 369 ± 21 |
| kleidi | Q8_0 | 293 ± 5 | **869 ± 28** | **1044 ± 11** |
| kleidi | Q6_K | 291 ± 26 | **858 ± 8** | **1072 ± 38** |
| kleidi | Q4_0 | 168 ± 12 | 429 ± 1 | 411 ± 42 |

**tg32 decode**：三種 build 幾乎一樣。Q8_0 約 33–35（X3×1）／55–58（A715×4）／57–60（t5）；
Q4_0 約 40–44／78–80／83–85。

每組開跑時 BIG 約 38°C，跑完 57–80°C。t5 那欄標準差大，是 X3 被熱節流
（另一篇：[用 ftrace 看 Pixel 8 的熱節流](pixel8-ftrace-thermal-pressure.md)）。

### 4.1 KleidiAI 為什麼讓 Q6_K 跟 Q8_0 一樣快

```bash
grep -n "want_q8" ggml/src/ggml-cpu/kleidiai/kleidiai.cpp
```

```c
const bool want_q8 = tensor->type == GGML_TYPE_Q8_0 || tensor->type == GGML_TYPE_Q6_K;
```

載入時把 Q6_K **repack 成 Q8 格式**，再交給 i8mm kernel。用比較大的權重記憶體換到整數矩陣指令的速度。

### 4.2 正確性 sanity check

```bash
adb shell 'cd /data/local/tmp/llm; for v in neon kleidi; do for q in q8_0 q6_k; do
  echo "== $v $q"
  taskset f0 ./llama-completion-$v -m models/qwen2.5-0.5b-instruct-$q.gguf \
    -t 4 --temp 0 -n 40 -no-cnv -p "The capital of France is" 2>/dev/null | tail -c 300
done; done'
```

四組輸出都通順，前約 20 個 token 一致，之後分岔（KleidiAI 的 activation 量化／累加順序不同，不會 bit-identical）。
**這只是 sanity check，不是正確性證據。**

---

## 五、SVE 為什麼變慢

### 5.1 先排除 GEMM

```bash
grep -n "get_optimal_repack_type" ggml/src/ggml-cpu/repack.cpp
```

repack 用哪個 kernel 是**執行期**決定的。Q4_0 要選 8x8 SVE 版需要 `ggml_cpu_get_sve_cnt() == QK8_0`（32 bytes），
手機只有 16 → 兩個 build 都選 4x8 i8mm（NEON）kernel。Q8_0、Q6_K 同理。所以主 GEMM 應該是同一份程式碼。

### 5.2 simpleperf

推沒 strip 的 binary 上去，才有符號：

```bash
for v in neon sve; do
  adb push build-$v/bin/llama-bench /data/local/tmp/llm/llama-bench-$v-sym
done
adb shell 'cd /data/local/tmp/llm; chmod +x *-sym; for v in neon sve; do
  simpleperf record -o perf-$v.data -e cpu-clock -g --call-graph fp \
    taskset f0 ./llama-bench-$v-sym -m models/qwen2.5-0.5b-instruct-q8_0.gguf -t 4 -p 128 -n 0 -r 3
  simpleperf report -i perf-$v.data --sort symbol | sed -n 1,22p
done'
```

把百分比乘上總時間（`Event count`）換成絕對秒數：

| | neon | sve |
|---|---:|---:|
| 總時間 | 5.24 s | 7.57 s |
| `ggml_gemm_q8_0_4x8_q8_0` | 68.0% = 3.57 s | 46.6% = 3.53 s |
| `ggml_compute_forward_flash_attn_ext` | 6.5% = 0.34 s | 31.4% = **2.38 s** |

**GEMM 的絕對時間一樣，flash attention 慢了 7 倍。** 只看百分比會被誤導——SVE build 的 GEMM 比例變小，
不是 GEMM 變快，是總時間被 FA 撐大了。

### 5.3 FA 裡面哪幾個位址最熱

```bash
adb shell 'cd /data/local/tmp/llm; simpleperf report -i perf-sve.data \
  --symbols ggml_compute_forward_flash_attn_ext --sort vaddr_in_file | sed -n 8,30p'
```

熱點集中在兩段：`0x476f14–0x476f2c` 和 `0x477724–0x477740`。

### 5.4 反組譯

```bash
OD=$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-objdump
$OD -d --no-show-raw-insn --start-address=0x476ef0 --stop-address=0x476f40 build-sve/bin/llama-bench
$OD -d -l --start-address=0x476f14 --stop-address=0x476f18 build-sve/bin/llama-bench | grep -E '\.(h|c|cpp):'
```

```text
476f14:  ldr   s1, [x13], #0x4
476f18:  ldr   s2, [x14]
476f1c:  subs  x15, x15, #0x1
476f20:  add   x14, x14, #0x100
476f24:  fmadd s0, s1, s2, s0
476f28:  b.ne  0x476f14
```

一次一個 float 的 **scalar `fmadd`**，B 以 `0x100`（64 個 float）跨步讀。`-l` 指到 `simd-gemm.h:259`。
第二段熱迴圈長得一樣，也指到同一行。

### 5.5 根因

```bash
grep -nE "^#(if|elif|else|endif)" ggml/src/ggml-cpu/simd-gemm.h
grep -n "simd_gemm(" ggml/src/ggml-cpu/ops.cpp
git log --format='%h %ad %s' --date=short -S'__ARM_FEATURE_SVE' -- ggml/src/ggml-cpu/simd-gemm.h
```

```c
#if defined(GGML_SIMD) && !defined(__ARM_FEATURE_SVE) && !defined(__riscv_v_intrinsic)
    /* NEON / AVX microkernel */
#elif defined(GGML_SIMD) && defined(__riscv_v_intrinsic)
    /* RVV microkernel */
#else // scalar path
static void simd_gemm(float * C, const float * A, const float * B, int M, int K, int N) {
    for (int64_t i = 0; i < M; i++)
        for (int64_t j = 0; j < N; j++) {
            float sum = C[i * N + j];
            for (int64_t kk = 0; kk < K; kk++)
                sum += A[i * K + kk] * B[kk * N + j];
            C[i * N + j] = sum;
        }
}
#endif
```

- 這個 guard 來自 commit `684b36101`（#19422，2026-02）的「add guard for sizeless vector types」：
  SVE 的 `svfloat32_t` 沒有固定大小，不能放進 microkernel 用的暫存器陣列。
- RVV 有自己的 `rvv_simd_gemm`，**SVE 沒有** → 一開 `__ARM_FEATURE_SVE` 就掉到 scalar。
- tiled flash attention 的 KQ（`ops.cpp` 的 `simd_gemm(KQ, Q, K, ...)`）和 VKQ 兩個矩陣乘都走這裡。

### 5.6 用 `-fa` 開關驗證

```bash
adb shell 'cd /data/local/tmp/llm; for q in q8_0 q4_0; do for v in neon sve; do for fa in 0 1; do
  taskset f0 ./llama-bench-$v -m models/qwen2.5-0.5b-instruct-$q.gguf -t 4 -p 128,512 -n 0 -fa $fa -r 3
done; done; done'
```

| | neon fa=0 | neon fa=1 | sve fa=0 | sve fa=1 |
|---|---:|---:|---:|---:|
| Q8_0 pp128 | 436 | 470 | 392 | 305 |
| Q8_0 pp512 | 384 | 460 | 327 | **232** |
| Q4_0 pp128 | 442 | 492 | 401 | 314 |
| Q4_0 pp512 | 387 | 467 | 328 | **234** |

- NEON 開 FA 會變快；SVE 開 FA 反而變慢，而且 prompt 越長差距越大（scalar GEMM 是 O(n²) 那一塊）。
- 關掉 FA 後 SVE 仍慢 10–15%，還有次要因素，這次沒追。

**實用結論：在 VL=128 的手機核心上不要開 `armv9-a`**；真的要開，至少先 `-fa 0`。

### 5.7 上游

[ggml-org/llama.cpp#30051](https://github.com/ggml-org/llama.cpp/issues/30051) 已經有人在 Google Axion（Neoverse V2）
上回報同一個根因，提議 SVE build 在這個 kernel 改用 NEON 暫存器。我把 Pixel 8 的數據補在
[這則留言](https://github.com/ggml-org/llama.cpp/issues/30051#issuecomment-6552441651)。

---

## 六、跟前一篇的差異

[前一篇](llama-cpp-pixel8-sve-flash-attention.md)（llama.cpp `6657ded4f`，2026-08）的觀察都還成立：
`ops.cpp` 單獨編回 NEON 就解釋 96.6% 的退化、simpleperf 顯示 flash attention 暴增。差在最後一步：

- 前一篇反組譯時統計的是 FA 裡的 **SVE 指令**（`st1w`／`ld1w`／`fmul`），推論熱迴圈是 `ggml_vec_scale_f32`，
  再把根因歸到 `vec.h` 的展開因子。
- 這次是用 `--sort vaddr_in_file` 先找**熱的位址**再反組譯，熱迴圈是 **scalar** `fmadd`，
  scalar 指令不會出現在「SVE 指令統計」裡，所以前一篇的方法看不到它。
- `simd-gemm.h` 是被 `ops.cpp` include 進去的，「`ops.cpp` 編成 NEON 就好了」跟這次的根因完全相容。
- `6657ded4f` 已包含 #19422 的 tiled FA，所以同一個 scalar fallback 很可能當時就在；
  但我沒有回到那個 commit 重做這次的反組譯，這點是推論。

教訓：**先讓 profiler 告訴你哪幾個位址熱，再反組譯那幾個位址**；從「我預期它用了什麼指令」去數指令，會漏掉預期外的東西。

---

## 七、坑整理

| 坑 | 解法 |
|---|---|
| `adb push -q` 不存在 | 拿掉 `-q` |
| `/sys/class/thermal` 讀不到 | userdebug 上 `adb root` |
| 看不到 cmake 實際的 `-march` | grep `build-*/build.ninja` |
| 手機時鐘跟主機差兩個月 | llama-bench CSV 的 `test_time` 不可信 |
| simpleperf 只看百分比 | 乘上 Event count 換成絕對時間再比 |
| 數 SVE 指令找熱點 | 用 `--sort vaddr_in_file` 找熱位址再反組譯 |

順帶一提：同一顆模型在 SpacemiT X60（RISC-V，IME1 矩陣擴充）上 Q6_K 的最佳化也是先 repack 成 int8 矩陣格式再用矩陣指令。
不過兩邊 llama.cpp 版本、時脈都不同，數字不能直接拿來比快慢。
