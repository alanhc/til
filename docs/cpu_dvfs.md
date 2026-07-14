# CPU DVFS（Dynamic Voltage and Frequency Scaling）

DVFS 是依負載動態調整 CPU 的頻率與電壓，以在效能與功耗之間取得平衡。功耗大致與電壓平方及頻率成正比，因此降頻降壓能顯著省電。

## Linux cpufreq
Linux kernel 以 `cpufreq` 子系統管理，透過 **governor** 決定調頻策略：
- **performance**：固定最高頻率，追求效能。
- **powersave**：固定最低頻率，最省電。
- **ondemand / conservative**：依負載動態升降頻（較舊的策略）。
- **schedutil**：由排程器提供的負載資訊驅動調頻，較新且反應快。

## 相關路徑
```bash
# 每顆 CPU 的 cpufreq 設定
/sys/devices/system/cpu/cpu0/cpufreq/
  scaling_governor          # 目前 governor
  scaling_available_governors
  scaling_cur_freq          # 目前頻率
  scaling_min_freq / scaling_max_freq
```

## P-state
x86（Intel/AMD）平台常用 `intel_pstate` / `amd-pstate` driver，以硬體定義的 P-state（效能狀態，P0 最高）進行調頻，通常由硬體或韌體協同 kernel 控制。
