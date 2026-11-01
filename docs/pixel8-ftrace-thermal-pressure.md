# 用 ftrace 看 Pixel 8 的熱節流：cpu_frequency 說滿頻，thermal_pressure 說沒有

在 Pixel 8 上跑 llama.cpp 時，用到 X3 的那組數字標準差特別大。直覺是熱節流，但 `cpu_frequency`
trace 從頭到尾都說 X3 在跑 2914 MHz。這篇記錄怎麼用 ftrace 找到真正的訊號：
**`thermal_pressure_update`**。每一步的指令都在。

結論：

- `cpu_frequency` 回報的是 governor 要的頻率，**看不到熱節流**。
- 熱節流是透過 **thermal pressure**（scheduler 眼中「這顆核心變小了多少」）讓 kernel 知道的。
  開跑 2.65 秒後 X3 就被扣 capacity，多數時間約 20%，最多 47%；A715 只扣 5–10%。
- pressure 的單位是 **capacity**，不是「每 1024」：A715 的 capacity 是 725，被扣 73 就是 10%。

環境同 [Pixel 8 上的 llama.cpp 實測](llama-cpp-pixel8-neon-sve-kleidiai.md)：
`shiba` userdebug、kernel `6.1.99-android14-11`、`adb root`。

---

## 一、看有哪些 event

```bash
adb root
adb shell 'ls /sys/kernel/tracing/events/power /sys/kernel/tracing/events/thermal'
adb shell 'ls /sys/kernel/tracing/events | grep -iE "thermal|pressure"'
```

這次用到：

| event | 意義 |
|---|---|
| `power/cpu_frequency` | cpufreq 設定頻率時發出 |
| `power/cpu_frequency_limits` | 上下限變動 |
| `thermal/thermal_temperature`、`thermal/cdev_update` | thermal zone 溫度、cooling device 狀態 |
| `thermal_pressure/thermal_pressure_update` | `drivers/base/arch_topology.c` 更新 thermal pressure 時發出 |

各叢集的 capacity：

```bash
adb shell 'for c in 0 4 8; do echo cpu$c $(cat /sys/devices/system/cpu/cpu$c/cpu_capacity); done'
# cpu0 182 / cpu4 725 / cpu8 1024
```

---

## 二、錄 trace 的腳本

`trace-thermal.sh`（在手機上跑）：

```sh
#!/system/bin/sh
T=/sys/kernel/tracing
cd /data/local/tmp/llm
while [ $(cat /sys/class/thermal/thermal_zone0/temp) -gt 38000 ]; do sleep 5; done

echo 0 > $T/tracing_on
echo > $T/trace
echo 16384 > $T/buffer_size_kb
for e in power/cpu_frequency power/cpu_frequency_limits thermal/thermal_temperature thermal/cdev_update; do
  echo 1 > $T/events/$e/enable
done
for e in $(ls $T/events/thermal_pressure | grep -v -e enable -e filter); do
  echo 1 > $T/events/thermal_pressure/$e/enable
done

echo 1 > $T/tracing_on
echo START > $T/trace_marker
taskset 1f0 ./llama-bench-kleidi -m models/qwen2.5-0.5b-instruct-q8_0.gguf -t 5 -p 512 -n 0 -r 8 2>/dev/null | grep -i q8_0
echo END > $T/trace_marker
echo 0 > $T/tracing_on

for e in power thermal thermal_pressure; do echo 0 > $T/events/$e/enable; done
cat $T/trace > /data/local/tmp/llm/thermal-trace.txt
```

```bash
adb push trace-thermal.sh /data/local/tmp/llm/
adb shell sh /data/local/tmp/llm/trace-thermal.sh
adb pull /data/local/tmp/llm/thermal-trace.txt raw/
grep -v '^#' raw/thermal-trace.txt | awk '{print $5}' | sort | uniq -c
```

> **坑：不要用 `/proc/uptime` 對時間。** 我第一次在腳本裡 `echo "START $(cat /proc/uptime)"`，
> 結果跟 trace 的時間戳差了一大截，整條時間軸都錯了——trace clock 跟 uptime 不是同一個時鐘。
> 改成寫 `trace_marker`，START／END 就會變成 trace 裡的 `tracing_mark_write` 事件，時間保證一致。

事件統計：688 個 `cpu_frequency`、29 個 `thermal_pressure_update`。
**`thermal_temperature` 和 `cpu_frequency_limits` 一個都沒有**——這台的 thermal zone 不走那條路
（使用者空間的 thermal HAL 才是主控，見 [Pixel 8 CPU/GPU/NPU 量測](pixel8-cpu-gpu-npu-benchmark.md)）。

---

## 三、解析

```bash
python3 - <<'EOF'
import re
L = open('raw/thermal-trace.txt').read().splitlines()
ts = lambda l: float(re.search(r'\s(\d+\.\d+):', l)[1])
st = [ts(l) for l in L if 'tracing_mark_write: START' in l][0]
en = [ts(l) for l in L if 'tracing_mark_write: END' in l][0]
print('duration %.2fs' % (en - st))

freq, press = {}, []
for l in L:
    m = re.search(r'\s(\d+\.\d+): cpu_frequency: state=(\d+) cpu_id=(\d+)', l)
    if m: freq.setdefault(int(m[3]), []).append((float(m[1]) - st, int(m[2]) // 1000))
    m = re.search(r'\s(\d+\.\d+): thermal_pressure_update: cpu=(\d+) thermal_pressure=(\d+)', l)
    if m: press.append((round(float(m[1]) - st, 2), int(m[2]), int(m[3])))

D = en - st
for cpu in (4, 8):
    s = sorted(freq.get(cpu, []))
    out = []
    for k in range(int(D * 2) + 1):            # 每 0.5 s 取當下生效的頻率
        cur = [f for t, f in s if t <= k / 2]
        out.append(cur[-1] if cur else None)
    print(f'cpu{cpu} MHz @0.5s:', out)
print('thermal_pressure (t, cpu, pressure):', [p for p in press if -0.5 < p[0] < D + 0.5])
EOF
```

---

## 四、結果

kleidi Q8_0 pp512，X3+A715 五執行緒，r=8，共 7.6 秒，870 ± 31 t/s。

**`cpu_frequency`**：

```text
cpu4 MHz @0.5s: [None, 402, 402, 402, 402, 2367, 2367, ...]
cpu8 MHz @0.5s: [None, 2914, 2914, 2914, 2914, 2914, 2914, ...]
```

X3 從頭到尾 2914 MHz；A715 前 2 秒 402 MHz 是載入模型（單執行緒），之後 2367 MHz。
**只看這個會以為完全沒節流。**

**`thermal_pressure_update`**（節錄）：

```text
(2.65, 8, 362) (2.76, 8, 80) (3.07, 8, 126) (3.28, 8, 194) (3.59, 8, 218) (3.59, 4, 38)
(4.01, 8, 218) ... (5.77, 8, 477) ... (6.61, 4, 73) (7.02, 8, 270) (7.13, 4, 73)
```

| 叢集 | capacity | 被扣的範圍 | 比例 |
|---|---:|---|---|
| X3（cpu8） | 1024 | 80–477，多數 194–218 | 8–47%，多數 19–21% |
| A715（cpu4–7） | 725 | 38–73 | 5–10% |

- 開跑 **2.65 秒**後 X3 開始被扣，之後約每 0.1 秒更新一次。
- governor 要的是滿頻，真正的上限是熱管理在別處壓的；scheduler 只透過 thermal pressure 知道「X3 變小了」。
- 這解釋了 t5 標準差大：X3 最快、也最先被壓，而 llama.cpp 平均分工，整體被最慢的 thread 拖住。

---

## 五、誰在呼叫

在 Pixel kernel 原始碼（取得方式見 [用 Kleaf 編 Pixel 8 vendor module](pixel8-kleaf-vendor-module-tpstat.md)）：

```bash
grep -rn "arch_update_thermal_pressure" private/google-modules/soc/gs/drivers/cpufreq/
sed -n '/^void topology_update_thermal_pressure/,/^}/p' aosp/drivers/base/arch_topology.c
```

公開的 [google-modules/soc/gs](https://android.googlesource.com/kernel/google-modules/soc/gs/) 裡，
cpufreq driver 把節流上限設成兩個 thermal actor 的較小值，再交給 `arch_update_thermal_pressure()`：

```c
arch_capped_freq = min(domain->capped_freq[TJ], domain->capped_freq[TSKIN]);
arch_update_thermal_pressure(maskp, arch_capped_freq);
```

- **TJ** 是晶片接面溫度，**TSKIN** 是機殼（皮膚）溫度。
- 呼叫時持有 domain 的 spinlock → 想掛 probe 的話，probe 在 atomic context。

`arch_topology.c` 這邊：

```c
trace_thermal_pressure_update(cpu, th_pressure);

for_each_cpu(cpu, cpus) {
    WRITE_ONCE(per_cpu(thermal_pressure, cpu), th_pressure);
    trace_android_rvh_update_thermal_stats(cpu);
}
```

**tracepoint 每個 cpufreq domain 只發一次**，cpu 參數是 domain 的第一顆。所以 trace 裡只會看到 cpu4 和 cpu8，
cpu5–7 的值要自己展開。下一篇的 module 就是做這件事。

---

## 六、坑整理

| 坑 | 解法 |
|---|---|
| 用 `/proc/uptime` 當開始時間 | 寫 `trace_marker` |
| 只看 `cpu_frequency` 判斷節流 | 看 `thermal_pressure_update` |
| 把 pressure 當成「每 1024」 | 除以該核心的 `cpu_capacity` |
| 以為 cpu5–7 沒被節流 | tracepoint 一個 domain 只發一次 |
| 等 `thermal_temperature` 事件 | 這台不發，溫度要直接讀 `thermal_zone*/temp` |
