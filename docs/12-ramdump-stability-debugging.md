# Ramdump 與穩定性除錯實戰:Chip Vendor 視角

> 系列文章之十二。總覽請見《Chip Vendor 視角的 Android Build System》。

量產百萬台之後,十萬分之一的重啟率就是每天一堆客訴。穩定性除錯是 BSP 團隊的長期戰爭:kernel panic、watchdog、native crash、ANR、低機率當機。本文整理症狀分類、事後取證工具鏈(pstore/ramdump/tombstone),與低機率問題的攻堅方法。

---

## 一、症狀分類:先搞清楚是哪種「當」

| 症狀 | 層級 | 第一手證據 |
|---|---|---|
| 直接重開機 | kernel panic / HW reset | pstore、ramdump、PMIC reset reason |
| 卡死後重開 | watchdog(HW 或 SW) | watchdog 咬人前的 log、ramdump |
| 畫面凍結但沒重開 | system_server 卡死 / display pipeline | watchdog trace、`dumpsys` |
| 單一 app/service 掛 | native crash / Java crash | tombstone / dropbox |
| 「畫面跳一下」 | system_server crash 重啟(soft reboot) | dropbox 的 system_server crash |
| 無回應幾秒後恢復 | ANR | `/data/anr/` trace |
| 自己關機 | 熱保護 / PMIC / 電量計 | PMIC 事件、thermal log |

**Reset reason 是第一個要建的基礎設施**:PMIC/SoC 記錄上次重啟原因(power-on、watchdog、kernel panic、thermal⋯⋯),開機時寫進 property/log。沒有它,統計「重啟率」時連分類都做不到。

---

## 二、Kernel 層取證

### 2.1 pstore/ramoops:最便宜的黑盒子

Panic 時把 kernel log、console log 存進保留 RAM,重開機後讀出:

```bash
adb shell ls /sys/fs/pstore/
# console-ramoops-0   ← panic 前的 console log
# dmesg-ramoops-0     ← panic 時的 kernel log(含 backtrace)
```

DT 裡保留一塊 RAM 給 ramoops 是 BSP 標配。量產 user build 也要開(成本極低),它是現場問題唯一必然存在的證據。

### 2.2 Ramdump:全記憶體事後解剖

Panic/watchdog 後,由 bootloader 或 debug 機制把整個 DRAM 導出(進特殊 dump 模式經 USB 拉出,或 dump 到 storage)。分析工具:

- **Crash utility**(搭配 vmlinux)看 kernel 資料結構:`bt`(各 CPU backtrace)、`ps`、`log`、`runq`、鎖的持有者。
- 各 SoC 廠自家的 parser(解析自家 IP 的暫存器區塊)。
- 常見結論:NULL deref(backtrace 直指兇手)、spinlock 死鎖(兩顆 CPU 互等)、記憶體踩踏(poison pattern、SLUB debug 資訊)、HW hang(某 IP 的 bus 不回應 → 看 IP 暫存器)。

**Watchdog 的分層**:HW watchdog(SoC 級,最後防線)、kernel soft lockup/hung task 偵測、framework watchdog(system_server 的 handler 卡 60 秒 → 殺掉重啟並留 trace)。每層咬人留下的證據不同,先判斷是哪層咬的。

### 2.3 主動偵錯配置

Debug build 常開:`CONFIG_SLUB_DEBUG`、`CONFIG_DEBUG_LIST`、KASAN(記憶體錯誤神器,但性能損耗大,只能實驗室用)、lockdep(鎖順序驗證)。**KASAN 抓到的問題,在 user build 上表現為隨機當機**——實驗室多跑 KASAN,量產少燒香。

---

## 三、Userspace 取證

### 3.1 Tombstone:native crash

crash 時 `crash_dump` 收屍,寫進 `/data/tombstones/`:

```
signal 11 (SIGSEGV), code 1 (SEGV_MAPERR), fault addr 0x0
backtrace:
  #00 pc 00012345  /vendor/lib64/libmyvendor_isp.so (isp_process_frame+52)
  ...
```

還原符號:

```bash
# 用帶符號的 .so(out/target/product/<board>/symbols/)
llvm-addr2line -e symbols/vendor/lib64/libmyvendor_isp.so 0x12345
# 或整份 tombstone 餵 development/scripts/stack
```

**符號檔管理是基礎建設**:每個 release 的 `symbols/` 目錄要歸檔(對照 OTA 篇的 target_files 歸檔),否則客戶回報的 tombstone 是天書。

### 3.2 ANR 與 Java crash

- ANR trace 在 `/data/anr/`:主線程卡在哪(等鎖?等 binder?binder 對端是誰?)。**vendor HAL 慢是 app ANR 的常見底層原因**——binder call 鏈一路追到你的 service。
- Java crash / system_server 異常進 **dropbox**:`adb shell dumpsys dropbox --print`。

### 3.3 bugreport:全家桶

```bash
adb bugreport bugreport.zip   # logcat + dmesg + dumpsys + anr + tombstone 全打包
```

客訴回報的標準格式;學會快速在裡面找 reset reason、crash 時間軸。

---

## 四、低機率問題攻堅

萬分之一機率的問題,方法論比技術重要:

1. **統計先行**:建立 crash 上報管道(量產裝置回傳 reset reason + 摘要),先知道 top issue 是哪幾個 signature,別追長尾。
2. **Signature 聚類**:同一個 backtrace/panic PC 聚成一個 issue,追出現頻率與版本相關性(哪個 build 開始出現 → 對 commit 範圍)。
3. **加速重現**:壓力腳本(monkey、開關機循環、suspend/resume 循環、溫度箱)+ 放大條件(KASAN、降頻、減記憶體)。**重現週期從一週壓到一小時,問題就解了一半**。
4. **加 instrumentation 等下一次**:改 log/加 trace 的 debug build 灑到測試機隊,等它再發生——很多硬問題是「三次 ramdump 對比」看出規律的。
5. **硬體排除**:批次性、溫度電壓相關性、特定顆粒(DRAM vendor)相關性——與硬體團隊的 shmoo/margin 測試對齊,別把 HW marginal 當 SW bug 追。

---

## 五、組織面:穩定性是指標不是事件

- **KPI 化**:重啟率(次/千台/日)、crash 率分 signature 追蹤,release 進出有門檻(如 `<0.x%`)。
- **實驗室常備**:MTBF 跑機房(數百台跑壓力場景)+ 溫度箱,新版本先過 MTBF 再出門。
- **與客戶的分工**:客戶回報附 bugreport + ramdump 是合約等級的要求;你提供 parser 工具與符號伺服器,縮短來回。

---

## 結語

> **穩定性除錯的核心是「證據鏈」:reset reason 告訴你哪一類,pstore/ramdump/tombstone/ANR trace 告訴你死在哪,統計聚類告訴你先追哪個。** 工具鏈(ramoops、dump 模式、符號歸檔、上報管道)都是要在出貨前建好的基礎設施——問題發生後才想收集證據,永遠慢一步。
