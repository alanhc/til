# 效能與功耗調校實戰:Chip Vendor 視角

> 系列文章之十。總覽請見《Chip Vendor 視角的 Android Build System》。

跑分、順暢度、續航——SoC 的市場評價一半來自這裡,而調校的槓桿大部分握在 BSP 層。本文整理 Android 效能/功耗的控制點地圖、量測工具鏈,以及調校的方法論。

---

## 一、控制點地圖:誰在決定快慢與耗電

### 1.1 Kernel 層

**CPU**:
- `cpufreq`(governor:`schedutil` 為主流)決定頻率;`cpuidle` 決定 idle 深度;core 的上下線與 isolation。
- **EAS(Energy Aware Scheduling)**:scheduler 依 **energy model**(每個 OPP 的 capacity/power 表,由你在 DT 提供)決定 task 放大核或小核。**energy model 填錯,整個調度就歪**——這是 SoC vendor 獨有的責任。
- big.LITTLE/DynamIQ 拓撲、cluster 的 capacity 標定(`capacity-dmips-mhz`)。

**GPU/DDR**:`devfreq` 管 GPU 與 DDR/bus 頻率;**bus DVFS / interconnect voting**(driver 對頻寬投票)是功耗大戶,vote 高了耗電、低了卡頓。

**Thermal**:kernel thermal framework(trip points、cooling device)+ 你的 IPA/自研 governor,決定過熱時砍誰。

### 1.2 HAL/framework 邊界(你的地盤)

- **Power HAL(`IPower`)**:framework 把場景 hint 丟下來(`INTERACTION`、`LAUNCH`、遊戲模式),你決定怎麼 boost(拉頻、遷核、鎖 idle)。**ADPF(Android Dynamic Performance Framework)** 是新一代機制:app/遊戲直接回報每幀工作量與目標時限(performance hint session),你的 HAL 據此精準給算力——比傳統「猜場景」精細得多。
- **Thermal HAL(`IThermal`)**:把溫度與 throttling 狀態上報 framework,app 可訂閱。
- **cgroup 配置**:`schedtune`/uclamp、cpuset(`top-app`/`foreground`/`background` 該用哪些核)由 init.rc 與你的設定檔決定。

### 1.3 Framework 之上(理解即可,通常不是你改)

Doze/App Standby、JobScheduler、WorkManager 管背景行為;跑分與實際體驗的差異常來自這層與你的 boost 策略的互動。

---

## 二、量測工具鏈:先量,再調

**鐵律:沒有 trace 不調校。** 猜出來的優化多半是安慰劑。

### 2.1 Perfetto:主力

```bash
# 抓 10 秒 systrace 級 trace(sched、freq、binder、atrace tag)
adb shell perfetto -o /data/misc/perfetto-traces/trace.pftrace -t 10s \
  sched freq idle am wm gfx view binder_driver hal dalvik

# 拉回來丟 ui.perfetto.dev 分析
```

看什麼:每幀時間軸(掉幀時 CPU 在幹嘛)、task 跑在哪顆核/什麼頻率、binder 往返延遲、你的 HAL 有沒有成為瓶頸。自家 daemon/HAL 記得埋 `ATRACE` 點,不然 trace 裡是黑盒。

### 2.2 功耗量測

- **硬體**:量測板(每路電源 rail 分開量)是 SoC vendor 的標配;整機用電池模擬器(如 Monsoon 類)。
- **軟體側**:`/sys/class/power_supply`、PMIC 的 fuel gauge;**power stats HAL(`IPowerStats`)** 上報各 rail/子系統能耗,`odpm`(on-device power monitor)資料進 batterystats。
- **歸因**:`dumpsys batterystats` + Battery Historian;wakeup source(`/sys/kernel/wakeup_reasons`)查誰吵醒系統。

### 2.3 基準場景庫

建立固定場景集,每次改動跑回歸:冷開機時間、app 啟動(`am start -W` 統計)、滑動列表 jank(`dumpsys gfxinfo`)、影片播放功耗、待機電流(飛航+滅屏,μA 級)、遊戲 30 分鐘熱穩態 fps。**baseline 進 CI,防止效能被日常 commit 蠶食**(對照升級篇:版本升級後第一件事就是跑這套)。

---

## 三、調校方法論

### 3.1 順暢度(jank)問題的標準流程

```
掉幀 → Perfetto 看該幀
 ├─ CPU 供不上:頻率太低?→ 查 governor/boost 是否觸發、util 是否被低估(uclamp)
 ├─ 跑錯核:重要 task 掉到小核?→ cpuset/EAS energy model/親和性
 ├─ 等 GPU:GPU 頻率/驅動瓶頸 → devfreq、driver 內部 trace
 ├─ 等 I/O:io schedule、UFS 頻率、f2fs GC
 └─ 等鎖/binder:對端 HAL 慢 → 對端埋點再追
```

### 3.2 功耗問題的標準流程

```
續航差 → 先分類:亮屏 or 滅屏?
 ├─ 滅屏:待機電流分解
 │   ├─ 睡不下去:wakelock / wakeup source / 中斷風暴(dmesg 統計 IRQ)
 │   ├─ 睡了但電流高:某 rail 沒關 → 量測板逐 rail 排查、driver runtime PM
 │   └─ 週期性喚醒:alarm/網路 → batterystats 歸因
 └─ 亮屏:場景功耗分解
     ├─ 頻率駐留分析(time_in_state):是否常駐高頻 → boost 過度、vote 未釋放
     ├─ display:亮度/更新率策略(LTPO)、GPU composition vs DPU
     └─ 大小核分佈:task 誤上大核 → EAS/energy model
```

**最常見的 vendor 級 bug**:driver 拿了 vote(頻寬/頻率/wakelock)忘記放。code review 時把「每個 get 都有對稱的 put」當紀律。

### 3.3 Thermal:效能與功耗的仲裁者

熱設計決定「持續效能」:跑分是 burst,遊戲是 sustained。調校點:trip point 的溫度階梯、cooling device 的優先順序(先砍 GPU 還是 CPU 大核?)、skin temperature 模型(表面溫度才是使用者感受)。**thermal 策略要和 Power HAL 的 boost 協同**——一邊 boost 一邊 throttle 是常見的自打架。

---

## 四、Chip vendor 的組織性課題

- **公版調校 vs 客戶客製**:公版給「均衡」預設,客戶(遊戲手機、平板)要不同 profile——把 tunable 做成設定檔(properties/overlay),不要讓客戶改 code。
- **跑分與真實體驗**:跑分白名單式 boost 有商譽與合規風險(媒體會抓),正道是把 ADPF 做好,讓真實 app 也拿得到效能。
- **每代 SoC 的 characterization**:新 SoC 量產前要完成 OPP 表定案、energy model 量測、thermal 模型校準——這些資料的品質,決定下游一切調校的天花板。

---

## 結語

> **效能功耗調校 = 在「算力供給曲線」上做資源分配:scheduler 決定誰用哪顆核、DVFS 決定核跑多快、thermal 決定上限、Power HAL 把 framework 的意圖翻譯給前三者。** 工具鏈(Perfetto + 量測板 + 固定場景庫)是望遠鏡,energy model 與 OPP 表是地基——地基準,策略才有意義;先量測,再動手,永遠如此。
