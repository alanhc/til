---
title: "Android Vendor Hook：GKI 在 core kernel 裡挖的洞"
date: 2026-11-13
tags: [android, kernel, gki, kmi, vendor-hook, tracepoint, static-key]
description: "從 ACK 原始碼拆解 vendor hook：為什麼 GKI 需要它、一個 hook 由哪四個部分組成、底層其實是 tracepoint 加 static key、vh 與 rvh 的差別（能不能睡、能掛幾個、能不能拔），以及用一個真實的 ACK change 看 hook 關掉時為什麼會編不過、callback 該放在哪裡。"
---

# Android Vendor Hook：GKI 在 core kernel 裡挖的洞

> **相關文章**：[02 GKI 與 Kleaf Kernel Build](./02-gki-kleaf-kernel-build.md)（KMI、symbol list）｜[Android Kernel](./android-kernel.md)（GKI 前後晶片商工作型態的轉變）

[GKI 那篇](./02-gki-kleaf-kernel-build.md)只用一句話帶過 vendor hook：「Google 在 core kernel 關鍵路徑上放的 hook 點」。這篇把它拆開，回答四個問題：

1. 為什麼 GKI 需要它？
2. 一個 hook 由哪幾塊組成？
3. 底層怎麼做到「沒人掛的時候幾乎零成本」？
4. `android_vh_*` 和 `android_rvh_*` 差在哪？

最後用 ACK 上一個公開的 change 當案例，看 hook 寫錯地方會發生什麼事。

本文引用的程式碼都來自 ACK `android13-5.15` 分支（`kernel/common`），連結在文末。

## 為什麼需要 vendor hook

Android 12 起，手機要跑 **GKI（Generic Kernel Image）**：

- core kernel 是 Google 編好的同一顆 binary，晶片商不能再改它的原始碼。
- 晶片商的東西只能寫成 **vendor module（`.ko`）**，開機時載入。
- module 和 kernel 之間只能透過 **KMI（Kernel Module Interface）** 溝通，也就是一份凍結的 export symbol 清單。

大部分 driver 這樣就夠了。但有一類需求做不到：**要插在 core kernel 流程的中間**。例如在 CPU 下線的某一步之前先做一件事，或在 scheduler 選 CPU 時換成自己的演算法。這不是呼叫一個 export 函式能解決的。

Vendor hook 就是 Google 預先在 core kernel 挖好的洞：kernel 執行到那一行時，去呼叫 vendor module 掛上來的 callback；沒有人掛的時候，幾乎沒有成本。

## 一個 hook 的四個部分

以 `android_vh_cpufreq_offline` 為例，它跨了四個地方：

**(a) 宣告**：`include/trace/hooks/cpufreq.h`

```c
DECLARE_HOOK(android_vh_cpufreq_offline,
	TP_PROTO(struct device *dev, int val),
	TP_ARGS(dev, val));
```

這行會展開出兩個函式：給呼叫點用的 `trace_android_vh_cpufreq_offline()`，以及給 module 用的 `register_trace_android_vh_cpufreq_offline()`。

**(b) 實體與 export**：`drivers/android/vendor_hooks.c`

```c
EXPORT_TRACEPOINT_SYMBOL_GPL(android_vh_cpufreq_offline);
```

`vendor_hooks.c` 在 `CREATE_TRACE_POINTS` 底下 include 所有 hook header，真正產生 `struct tracepoint` 的實體；export 之後 module 才連結得到。

**(c) 呼叫點**：core kernel 裡，也就是「洞」挖在哪一行

```c
trace_android_vh_cpufreq_offline(&policy->cdev->device, true);
```

**(d) 掛上去**：vendor module 裡

```c
static void my_cb(void *data, struct device *dev, int val)
{
	...
}

register_trace_android_vh_cpufreq_offline(my_cb, NULL);
```

callback 的第一個參數永遠是 `void *data`，也就是註冊時傳的第二個引數；後面才是 `TP_PROTO` 宣告的參數。

## 底層：就是 tracepoint

`include/trace/hooks/vendor_hooks.h` 開頭：

```c
#if defined(CONFIG_TRACEPOINTS) && defined(CONFIG_ANDROID_VENDOR_HOOKS)

#define DECLARE_HOOK DECLARE_TRACE
```

`DECLARE_HOOK` 直接就是 Linux 原本的 tracepoint，和 ftrace、perf 用的是同一套：

- **沒人註冊時**：`trace_xxx()` 開頭是 `static_key_false()`。static key 在機器碼層級是一條 NOP，呼叫點經過幾乎零成本。
- **有人註冊後**：kernel 把那條 NOP 改寫成 jump，進去依序呼叫 tracepoint 的 `funcs[]` 陣列裡每一個 callback。

所以一個 `android_vh_*` 可以同時掛好幾個 callback，每個都會被呼叫。

## vh 與 rvh

另一種是 **restricted vendor hook**，用 `DECLARE_RESTRICTED_HOOK` 宣告，名稱前綴 `android_rvh_`。差別都能在原始碼裡找到：

| | `android_vh_*` | `android_rvh_*` |
|---|---|---|
| 宣告 | `DECLARE_HOOK` → `DECLARE_TRACE` | `DECLARE_RESTRICTED_HOOK` → 自己的 `DEFINE_HOOK_FN` |
| callback 能不能睡 | **不能** | **可以** |
| 能掛幾個 | 不限 | 最多 2 個（`ANDROID_RVH_NR_PROBES_MAX`） |
| 能不能拔掉 | 可以 unregister | **不能**，掛了 module 就卸不掉 |

**為什麼 vh 不能睡**：一般 tracepoint 的呼叫路徑 `__DO_TRACE` 在呼叫 callback 前會先 `preempt_disable_notrace()`，callback 跑在不可搶佔的 context 裡，裡面 `mutex_lock()` 或 `kmalloc(GFP_KERNEL)` 都可能睡下去，會出事。

**rvh 怎麼繞過**：restricted hook 的 `__DO_RESTRICTED_HOOK_CALL` 直接 `static_call()` 到 callback，沒有關搶佔，所以 callback 可以睡。代價是 Google 不在呼叫路徑上做 RCU 保護，也就沒辦法安全地讓 callback 消失。這就是為什麼原始碼裡寫著：

```c
	/* vendor hooks cannot be unregistered */
```

rvh 多半放在 scheduler、mm 這類核心路徑：vendor 要整段換掉邏輯，又可能需要拿 lock。

## 案例：一個 hook 關掉時編不過的 change

ACK 上有一個 2022 年合進 `android13-5.15` 的 change，替 cpufreq 加上 `android_vh_cpufreq_offline`，並在某個 SoC 的 cpufreq driver 裡掛上 callback。它的動機是：

- CPU 在 suspend 時下線，cpufreq 會解除註冊 cooling device，送出 uevent。
- Android 的 health HAL 用帶 `EPOLLWAKEUP` 的 epoll 在聽 uevent，netlink 收到後會持有 wakelock，讓系統睡不下去。
- 修法：在 `cpufreq_cooling_unregister()` 之前加 hook，callback 對那個 device 呼叫 `dev_set_uevent_suppress()`，不送 uevent。
- 同樣的修法在 upstream 沒被接受，commit message 附了 linux-pm 的 patchwork 連結。這也是 `ANDROID:` 前綴 patch 的慣例：說明為什麼 upstream 做不到。

合進去一週後，有人回報 `ARCH=arm defconfig` 編不過：

```text
error: implicit declaration of function 'register_trace_android_vh_cpufreq_offline'
```

原因在 `vendor_hooks.h` 的 `#else` 分支：

```c
#else /* !CONFIG_TRACEPOINTS || !CONFIG_ANDROID_VENDOR_HOOKS */
/* suppress trace hooks */
#define DECLARE_HOOK DECLARE_EVENT_NOP
```

hook 關掉時，`DECLARE_EVENT_NOP` 只產生空的 `trace_xxx()`，讓呼叫點 (c) 照樣編得過，但**不產生** `register_trace_xxx()`。這個設計的假設是：只有 vendor module 會呼叫 register，而 vendor module 一定跑在 hook 有開的 GKI 上。

這個 change 違反了假設：它把 register 寫在 **ACK 自己的 cpufreq driver** 裡。那些 driver 在一般 defconfig 下也會被編到，就爆掉了。後來的修正是在那兩個 driver 的 callback 和 register 外面補上：

```c
#if defined(CONFIG_TRACEPOINTS) && defined(CONFIG_ANDROID_VENDOR_HOOKS)
	ret = register_trace_android_vh_cpufreq_offline(soc_cpufreq_suppress, NULL);
#endif
```

### 從這個案例還能看到的事

讀 diff 時還有幾個值得注意的地方，都是寫 hook 時容易踩的：

- **register 的回傳值會蓋掉前面的錯誤**：其中一個 driver 是先 `ret = cpufreq_register_driver(...)`，失敗只印 log，接著 `ret = register_trace_...()` 再 `return ret`。driver 註冊失敗時，probe 仍可能回傳 0。
- **hook 的參數比被保護的函式更早解參考**：呼叫點傳的是 `&policy->cdev->device`。cooling device 註冊失敗時 `policy->cdev` 是 `NULL`；`cpufreq_cooling_unregister()` 自己有 `if (!cdev) return;`，但 hook 寫在它前面，傳出去的是一個由 `NULL` 加上偏移量算出的指標，callback 一用就 oops。沒有人掛 hook 時，static key 是關的，參數根本不會被使用，所以這個問題只在 hook 被掛上時才出現。
- **同一個 callback 被掛兩次**：兩個 driver 各自 register 一次。vh 不限數量，所以兩個都會被呼叫。

這個 hook 後來要移植到 `android14-6.1` 時，兩次都被 abandon，新分支沒有收這個做法。

## 申請一個新 hook 要準備什麼

從上面的 review 過程可以看出 Google 的要求：

- **hook 本身的 change**：宣告 + export + 呼叫點，commit 前綴 `ANDROID:`，說明 upstream 為什麼不行，並附 Bug 編號。
- **symbol list 的 change**：在自家的 `android/abi_gki_aarch64_<vendor>` 加上新的 tracepoint symbol，並更新 ABI 表示檔。reviewer 會要求兩個 change 一起送、排成一個 series，讓 ABI 檢查一次看到完整的變更。
- **callback 放在 vendor module 裡**，不要放在 ACK 自己的 driver 裡：這樣 hook 關掉的 config 不受影響，也不會讓 ACK 依賴特定廠商的行為。

每個新 hook 都是 KMI 上多一個要長期維護的 symbol。近年 ACK 的方向是 upstream first，新 hook 越來越難收。

## 參考資料

- `include/trace/hooks/vendor_hooks.h`：https://android.googlesource.com/kernel/common/+/refs/heads/android13-5.15/include/trace/hooks/vendor_hooks.h
- `drivers/android/vendor_hooks.c`：https://android.googlesource.com/kernel/common/+/refs/heads/android13-5.15/drivers/android/vendor_hooks.c
- `kernel/tracepoint.c`（`android_rvh_probe_register`）：https://android.googlesource.com/kernel/common/+/refs/heads/android13-5.15/kernel/tracepoint.c
- `include/linux/tracepoint.h`（`__DO_TRACE`）：https://android.googlesource.com/kernel/common/+/refs/heads/android13-5.15/include/linux/tracepoint.h
