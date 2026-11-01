# 用 Kleaf 編 Pixel 8 vendor module：從 hello 到記錄 thermal pressure 的 tpstat

這篇是在 Pixel 8（`shiba`）上，用**完整的 Pixel kernel 樹 + Kleaf** 編出 vendor module，
`adb push` + `insmod` 載入驗證，不刷機。從 hello world 開始，最後寫出一個掛在**沒匯出的 tracepoint** 上、
按 CPU 統計 thermal pressure 的 module。每一步的指令都在。

跟 [Pixel 8 Kernel Driver 開發實戰](pixel8-kernel-tutorial.md) 的差別：那篇只 sync GKI 原始碼、用 `ddk_module`；
這篇 sync 的是整個 Pixel 裝置 kernel manifest，用 `kernel_module` 規則，放在 `private/google-modules/` 底下。

背景：上一篇 [用 ftrace 看 Pixel 8 的熱節流](pixel8-ftrace-thermal-pressure.md) 找到 `thermal_pressure_update` 這個訊號，
這篇把它做成常駐的統計。

---

## 一、前置檢查

```bash
adb root
adb shell uname -r
# 6.1.99-android14-11-gd7dac4b14270-ab12946699
adb shell 'zcat /proc/config.gz | grep -E "^CONFIG_(MODULE_SIG|MODULE_SIG_FORCE|MODULE_SIG_PROTECT|MODVERSIONS|DEBUG_INFO_BTF|FTRACE|BPF_SYSCALL)="'
```

```text
CONFIG_MODULE_SIG=y
CONFIG_MODULE_SIG_PROTECT=y
CONFIG_MODVERSIONS=y
CONFIG_DEBUG_INFO_BTF=y
CONFIG_FTRACE=y
CONFIG_BPF_SYSCALL=y
```

- **沒有 `CONFIG_MODULE_SIG_FORCE`** → 沒簽章的 module 也能載入。
- `MODULE_SIG_PROTECT` 只保護 GKI 自己那份模組名單，不擋 vendor module。
- `MODVERSIONS=y` → 載入時比對的是**每個符號的 CRC**，不是 release 字串。

確認手機跑的 kernel 跟 AOSP 樹裡附帶的 prebuilt 是同一份：

```bash
lz4 -dc ~/aosp/device/google/shusky-kernels/6.1/<release>/Image.lz4 | strings | grep -m1 "Linux version"
```

---

## 二、取得 kernel 原始碼

列出 Pixel 8 系列（`shusky`）可用的 manifest 分支：

```bash
git ls-remote https://android.googlesource.com/kernel/manifest | grep -i shusky | awk '{print $2}'
```

```text
refs/heads/android-gs-shusky-6.1-android15-qpr2-beta
refs/heads/android-gs-shusky-6.1-android16
...
```

沒有非 beta 的 `android15-qpr2`，挑最接近手機 build 的 `android15-qpr2-beta`，shallow sync：

```bash
mkdir -p ~/pixel-kernel && cd ~/pixel-kernel
repo init -u https://android.googlesource.com/kernel/manifest \
  -b android-gs-shusky-6.1-android15-qpr2-beta --depth=1
repo sync -c -j16 --no-tags
du -sh .                                   # 約 10 GB
grep -E "^(VERSION|PATCHLEVEL|SUBLEVEL)" aosp/Makefile   # 6 / 1 / 99
```

樹的結構：`aosp/` 是 GKI common kernel，`private/devices/google/shusky/` 是裝置設定，
`private/google-modules/` 是各個 vendor driver，`build_shusky.sh` 是官方的整包建置入口。

---

## 三、hello module

### 3.1 檔案

`private/google-modules/misc/hello/hello.c`：

```c
// SPDX-License-Identifier: GPL-2.0
#include <linux/module.h>
#include <linux/printk.h>
#include <linux/utsname.h>

static int __init hello_init(void)
{
	pr_info("hello: loaded on %s\n", init_utsname()->release);
	return 0;
}

static void __exit hello_exit(void)
{
	pr_info("hello: unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);
MODULE_LICENSE("GPL");
```

`Kbuild`：

```make
obj-m += hello.o
```

`Makefile`（照 `private/google-modules/power/reset/Makefile` 的寫法）：

```make
KERNEL_SRC ?= /lib/modules/$(shell uname -r)/build
M ?= $(shell pwd)

modules modules_install clean:
	$(MAKE) -C $(KERNEL_SRC) M=$(M) $(@)
```

`BUILD.bazel`：

```python
load("//build/kernel/kleaf:kernel.bzl", "kernel_module")

kernel_module(
    name = "hello",
    srcs = [
        "Kbuild",
        "Makefile",
        "hello.c",
    ],
    outs = ["hello.ko"],
    kernel_build = "//private/devices/google/common:kernel",
)
```

### 3.2 編譯：三個坑

```bash
cd ~/pixel-kernel
tools/bazel build --config=shusky --config=no_download_gki --config=no_download_gki_fips140 \
  //private/google-modules/misc/hello:hello
```

這行是踩完三個坑之後的版本：

**坑 1：預設下載 GKI prebuilt，但那個 API 已經回 501。**
`device.bazelrc` 預設 `--config=download_gki`，會到 `androidbuildinternal.googleapis.com/.../builds/<id>/...` 下載：

```text
WARNING: Download from https://androidbuildinternal.googleapis.com/android/internal/build/v3/builds/12786694/kernel_aarch64/attempts/latest/artifacts/vmlinux/url?redirect=true failed: ... GET returned 501 Not Implemented
```

→ 加 `--config=no_download_gki --config=no_download_gki_fips140`，在本機從 `aosp/` 編 GKI。
第一次約 3 分鐘（14 代 i7），之後只改 module 是 4 秒。

**坑 2：放在 `private/hello` 會被 Bazel 可見性擋下。**

```text
ERROR: ... alias '//private/devices/google/common:kernel' referring to target '//private/devices/google/shusky:kernel' is not visible from target '//private/hello:hello'
```

→ 搬到 `private/google-modules/` 底下（現有的 vendor module 都在這裡）。

**坑 3：少了 `Makefile`。**

```text
make: *** No targets specified and no makefile found.  Stop.
```

→ Kleaf 的 external module 一定要有 `Makefile`，而且要列進 `srcs`。

產物在 `bazel-bin/private/google-modules/misc/hello/hello/hello.ko`。

### 3.3 載入

```bash
KO=bazel-bin/private/google-modules/misc/hello/hello/hello.ko
modinfo $KO | grep vermagic
adb push $KO /data/local/tmp/
adb shell 'dmesg -c >/dev/null; insmod /data/local/tmp/hello.ko; lsmod | grep hello; rmmod hello; dmesg | grep hello'
```

```text
vermagic:       6.1.99-android14-11-maybe-dirty SMP preempt mod_unload modversions aarch64
hello                  20480  0
hello: loaded on 6.1.99-android14-11-gd7dac4b14270-ab12946699
hello: unloaded
```

vermagic 寫 `maybe-dirty`，跟手機的 release 字串不一樣，但因為有 `modversions`，kernel 只比 CRC，照樣載得進去。

---

## 四、tpstat：按 CPU 記錄 thermal pressure

### 4.1 tracepoint 沒有匯出

```bash
cd ~/pixel-kernel/aosp
grep -n "EXPORT_TRACEPOINT.*thermal_pressure\|CREATE_TRACE_POINTS" drivers/base/arch_topology.c
grep -lw __tracepoint_thermal_pressure_update android/abi_gki_aarch64*      # 沒有結果
```

`thermal_pressure_update` 是在 `arch_topology.c` 用 `CREATE_TRACE_POINTS` 建的，沒有 `EXPORT_TRACEPOINT_SYMBOL`，
所以 module 不能直接呼叫 `register_trace_thermal_pressure_update()`。

**繞法**：`for_each_kernel_tracepoint()` 走訪所有 tracepoint，用名字找到 `struct tracepoint *`，
再用通用的 `tracepoint_probe_register()` 掛上去。

### 4.2 確認符號在 KMI 裡

GKI 只開放符號清單上的符號給 module。`.stg` 是完整的 GKI ABI，`_pixel` 是 Pixel 自己的清單：

```bash
for s in for_each_kernel_tracepoint tracepoint_probe_register tracepoint_probe_unregister \
         tracepoint_srcu synchronize_srcu synchronize_rcu thermal_pressure cpu_scale \
         cpufreq_cpu_get cpufreq_cpu_put debugfs_create_dir debugfs_create_file debugfs_remove \
         ktime_get_mono_fast_ns single_open seq_printf seq_read seq_lseek single_release; do
  printf "%-30s %s\n" $s "$(grep -lw $s android/abi_gki_aarch64.stg android/abi_gki_aarch64_pixel | xargs -n1 basename | tr '\n' ' ')"
done
```

全部都有。`tracepoint_synchronize_unregister()` 是 inline，展開後用到 `tracepoint_srcu` 和 `synchronize_srcu`，所以這兩個也要查。

### 4.3 設計

- 每顆 CPU 記：更新次數、目前值、最大值，以及**時間加權平均**——每次更新時累加「舊值 × 經過的 ns」，讀取時補到現在。
- **probe 在 atomic context**：呼叫端的 cpufreq driver 持有 spinlock 才呼叫 `arch_update_thermal_pressure()`，
  所以 probe 裡不能睡、不能 `cpufreq_cpu_get()`。
- **tracepoint 一個 cpufreq domain 只發一次**，cpu 參數是 domain 第一顆。init 時先對每顆 CPU 查好
  `cpumask_first(policy->related_cpus)`，probe 收到事件時套用到同一個 domain 的所有 CPU。
- 介面放 debugfs：`cat` 讀、寫任何東西就 reset。

### 4.4 原始碼

`private/google-modules/misc/tpstat/tpstat.c`：

```c
// SPDX-License-Identifier: GPL-2.0
/*
 * tpstat: per-CPU thermal pressure statistics.
 *
 * Hooks the thermal_pressure_update tracepoint (not exported to modules, so it
 * is looked up by name with for_each_kernel_tracepoint()) and keeps, per CPU,
 * the number of updates, the max/current pressure and a time-weighted average
 * since the last reset.
 *
 * The tracepoint fires once per cpufreq domain with the first CPU of the
 * domain, so each event is applied to every CPU that shares that policy.
 *
 *   cat /sys/kernel/debug/tpstat/stats
 *   echo 1 > /sys/kernel/debug/tpstat/stats    # reset
 */
#include <linux/arch_topology.h>
#include <linux/cpufreq.h>
#include <linux/cpumask.h>
#include <linux/debugfs.h>
#include <linux/module.h>
#include <linux/percpu.h>
#include <linux/seq_file.h>
#include <linux/spinlock.h>
#include <linux/string.h>
#include <linux/timekeeping.h>
#include <linux/tracepoint.h>

struct tp_cpu {
	u64 updates;
	unsigned long cur;
	unsigned long max;
	u64 last_ns;	/* time of the last update (or reset) */
	u64 area;	/* sum of pressure * ns since reset */
};

static DEFINE_PER_CPU(struct tp_cpu, tp_cpu);
static DEFINE_SPINLOCK(tp_lock);
static struct tracepoint *tp;
static struct dentry *tp_dir;
static u64 reset_ns;
/* First CPU of each CPU's cpufreq policy, i.e. the cpu the tracepoint reports. */
static int tp_first[NR_CPUS];

static void tp_update(struct tp_cpu *s, unsigned long pressure, u64 now)
{
	s->area += (u64)s->cur * (now - s->last_ns);
	s->last_ns = now;
	s->cur = pressure;
	if (pressure > s->max)
		s->max = pressure;
	s->updates++;
}

/* Called with the vendor driver's domain spinlock held: must not sleep. */
static void tp_probe(void *data, int cpu, unsigned long pressure)
{
	unsigned long flags;
	u64 now = ktime_get_mono_fast_ns();
	int c;

	if (cpu < 0 || cpu >= nr_cpu_ids)
		return;

	spin_lock_irqsave(&tp_lock, flags);
	for_each_possible_cpu(c)
		if (tp_first[c] == cpu)
			tp_update(per_cpu_ptr(&tp_cpu, c), pressure, now);
	spin_unlock_irqrestore(&tp_lock, flags);
}

static void tp_reset(void)
{
	unsigned long flags;
	u64 now = ktime_get_mono_fast_ns();
	int cpu;

	spin_lock_irqsave(&tp_lock, flags);
	for_each_possible_cpu(cpu) {
		struct tp_cpu *s = per_cpu_ptr(&tp_cpu, cpu);

		s->updates = 0;
		s->max = s->cur;
		s->area = 0;
		s->last_ns = now;
	}
	reset_ns = now;
	spin_unlock_irqrestore(&tp_lock, flags);
}

static int tp_show(struct seq_file *m, void *v)
{
	unsigned long flags;
	u64 now = ktime_get_mono_fast_ns();
	u64 span;
	int cpu;

	spin_lock_irqsave(&tp_lock, flags);
	span = now - reset_ns;
	seq_printf(m, "window_ms %llu\n", span / NSEC_PER_MSEC);
	seq_puts(m, "cpu domain capacity updates cur max avg\n");
	for_each_possible_cpu(cpu) {
		struct tp_cpu *s = per_cpu_ptr(&tp_cpu, cpu);
		u64 area = s->area + (u64)s->cur * (now - s->last_ns);

		seq_printf(m, "%d %d %lu %llu %lu %lu %llu\n", cpu, tp_first[cpu],
			   per_cpu(cpu_scale, cpu), s->updates, s->cur, s->max,
			   span ? div64_u64(area, span) : 0);
	}
	spin_unlock_irqrestore(&tp_lock, flags);
	return 0;
}

static int tp_open(struct inode *inode, struct file *file)
{
	return single_open(file, tp_show, NULL);
}

static ssize_t tp_write(struct file *file, const char __user *buf,
			size_t count, loff_t *ppos)
{
	tp_reset();
	return count;
}

static const struct file_operations tp_fops = {
	.owner = THIS_MODULE,
	.open = tp_open,
	.read = seq_read,
	.write = tp_write,
	.llseek = seq_lseek,
	.release = single_release,
};

static void tp_find(struct tracepoint *t, void *priv)
{
	if (!strcmp(t->name, "thermal_pressure_update"))
		tp = t;
}

static int __init tpstat_init(void)
{
	int cpu, ret;

	for_each_kernel_tracepoint(tp_find, NULL);
	if (!tp) {
		pr_err("tpstat: thermal_pressure_update tracepoint not found\n");
		return -ENODEV;
	}

	for_each_possible_cpu(cpu) {
		struct cpufreq_policy *policy = cpufreq_cpu_get(cpu);

		tp_first[cpu] = policy ? cpumask_first(policy->related_cpus) : cpu;
		if (policy)
			cpufreq_cpu_put(policy);
		/* Seed with the current value so the first interval is accounted. */
		per_cpu_ptr(&tp_cpu, cpu)->cur = per_cpu(thermal_pressure, cpu);
	}
	tp_reset();

	ret = tracepoint_probe_register(tp, tp_probe, NULL);
	if (ret)
		return ret;

	tp_dir = debugfs_create_dir("tpstat", NULL);
	debugfs_create_file("stats", 0600, tp_dir, NULL, &tp_fops);
	pr_info("tpstat: attached to %s\n", tp->name);
	return 0;
}

static void __exit tpstat_exit(void)
{
	debugfs_remove(tp_dir);
	tracepoint_probe_unregister(tp, tp_probe, NULL);
	tracepoint_synchronize_unregister();
}

module_init(tpstat_init);
module_exit(tpstat_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Per-CPU thermal pressure statistics");
```

`Kbuild` 是 `obj-m += tpstat.o`；`Makefile` 跟 hello 一樣；`BUILD.bazel` 把 hello 換成 tpstat。

### 4.5 編譯與載入

```bash
cd ~/pixel-kernel
tools/bazel build --config=shusky --config=no_download_gki --config=no_download_gki_fips140 \
  //private/google-modules/misc/tpstat:tpstat
adb push bazel-bin/private/google-modules/misc/tpstat/tpstat/tpstat.ko /data/local/tmp/
adb shell 'insmod /data/local/tmp/tpstat.ko; dmesg | grep tpstat'
# tpstat: attached to thermal_pressure_update
```

**坑 4：`/sys/kernel/debug` 是空的。** kernel 有 `CONFIG_DEBUG_FS=y`、`CONFIG_DEBUG_FS_ALLOW_ALL=y`，
但 Android 11 起開機後預設不掛 debugfs：

```bash
adb shell 'mount | grep debugfs'                         # 沒有
adb shell 'mount -t debugfs debugfs /sys/kernel/debug'    # userdebug 上手動掛
```

正式產品不該依賴 debugfs；要長期用的話應該改成 sysfs 或 procfs。

### 4.6 跑 benchmark 驗證

```bash
adb shell 'S=/sys/kernel/debug/tpstat/stats; cd /data/local/tmp/llm
  while [ $(cat /sys/class/thermal/thermal_zone0/temp) -gt 38000 ]; do sleep 5; done
  echo 1 > $S
  taskset 1f0 ./llama-bench-kleidi -m models/qwen2.5-0.5b-instruct-q8_0.gguf -t 5 -p 512 -n 0 -r 8
  cat $S
  rmmod tpstat'
```

```text
window_ms 7510
cpu domain capacity updates cur max avg
0 0 182 0 0 0 0
1 0 182 0 0 0 0
2 0 182 0 0 0 0
3 0 182 0 0 0 0
4 4 725 8 73 73 21
5 4 725 8 73 73 21
6 4 725 8 73 73 21
7 4 725 8 73 73 21
8 8 1024 27 218 362 116
```

| 叢集 | capacity | 更新次數 | 最大扣除 | 平均扣除 |
|---|---:|---:|---:|---:|
| A510（cpu0–3） | 182 | 0 | 0 | 0 |
| A715（cpu4–7） | 725 | 8 | 73 | 21（3%） |
| X3（cpu8） | 1024 | 27 | 362 | 116（11%） |

- domain 分成 0／4／8 三組，跟三個叢集一致；cpu4–7 的值相同。
- 跟 ftrace 一致：X3 被壓得比 A715 兇得多，約每 0.1 秒更新一次。
- 平均 11% 包含前 2–3 秒還沒開始節流的時段，穩態大約 19–21%。
- 閒置時（不跑 benchmark）完全沒有更新。

---

## 五、坑整理

| 坑 | 解法 |
|---|---|
| GKI prebuilt 下載 API 回 501 | `--config=no_download_gki --config=no_download_gki_fips140` |
| `private/hello` 可見性錯誤 | 放到 `private/google-modules/` 底下 |
| `No targets specified and no makefile found` | 補 `Makefile` 並列進 `srcs` |
| vermagic 不同 | 有 `MODVERSIONS` 就只比 CRC，不用管 |
| tracepoint 沒匯出 | `for_each_kernel_tracepoint()` + `tracepoint_probe_register()` |
| probe 裡呼叫會睡的函式 | 呼叫端持有 spinlock，資料要在 init 先準備好 |
| cpu5–7 沒資料 | tracepoint 一個 domain 只發一次，自己用 `related_cpus` 展開 |
| debugfs 看不到 | Android 預設不掛，`mount -t debugfs debugfs /sys/kernel/debug` |

## 六、還可以做的

- 分開記錄 TJ（晶片溫度）和 TSKIN（機殼溫度）各自觸發了幾次——要掛在 cpufreq driver 更上游，比這次深一層。
- `trace_android_rvh_update_thermal_stats` 是 per-CPU 的 vendor hook，但 restricted vendor hook 掛上去就拆不掉，module 也就卸不掉。
- 改用 BPF：kernel 有 `CONFIG_BPF_SYSCALL` 和 BTF，同樣的統計可以不寫 module。
