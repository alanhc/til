# Hibernation:一份可以寫回 kernel 記憶體的快照

## 為什麼值得單獨寫一篇

大部分人對 hibernation 的理解停在一句話:「把記憶體存到硬碟,然後關機。」

這句話沒錯,但它遮住了真正有趣的部分。如果你把重點放在「省電」,hibernation 只是 suspend 的一個慢版本,而且在手機平台上根本用不到,不值得花時間。但如果你把重點放在另一句等價的敘述——

> **Hibernation image 是一份可以被完整寫回 kernel 記憶體的資料。**

——整件事的性質就變了。它不再是電源管理的一個 corner case,而是一個橫跨 driver 生命週期、freezer 協定、開機流程、以及 Secure Boot 信任鏈的結構性問題。本文從這個角度走一遍。

---

## 一、先把電源狀態的座標建立起來

ACPI 定義的 sleep states,以及它們在 Linux 的對應:

| State | 名稱 | RAM | 恢復時間 | 功耗 |
|---|---|---|---|---|
| S0 | Working | 供電 | — | 全速 |
| S0ix | Low Power Idle | 供電 | ms 級 | 極低 |
| S1 | Power-on standby | 供電 | ms | 中 |
| S3 | Suspend-to-RAM | self-refresh | < 1s | mW 級 |
| **S4** | **Suspend-to-Disk** | **斷電** | **秒~數十秒** | **≈ 0** |
| S5 | Soft off | 斷電 | 完整開機 | ≈ 0 |

這張表最關鍵的一列其實是 S4 和 S5 的比較:**它們在硬體上幾乎是同一件事**。兩者都真的斷電,主機板上的行為差異極小。唯一的差別是「有沒有在非揮發性儲存裡留下一份可還原的 image」。

這個觀察有兩個直接後果:

第一,從 bootloader 的角度看,**S4 resume 就是一次普通的冷開機**。firmware 不知道也不需要知道這次開機會變成一次還原,是 kernel 自己晚一點才發現「swap 裡有東西」。

第二,對管理平面來說,S4 和 S5 難以在 pin level 區分(後面第八節會回到這點)。

Linux 側的介面:

```
/sys/power/state       → freeze | standby | mem | disk
/sys/power/mem_sleep   → s2idle | shallow | deep
/sys/power/disk        → platform | shutdown | reboot | suspend | test_resume
/sys/power/image_size  → 期望的 image 大小上限
```

`/sys/power/disk` 的幾個 sub-mode 值得記一下,因為它們決定了「image 寫完之後要怎麼收尾」:

- **`platform`** — 透過 ACPI `_S4` 通知 firmware 這是 hibernate,firmware 可據此調整下次開機行為
- **`shutdown`** — 寫完直接關機,firmware 完全不知情
- **`reboot`** — 寫完立刻重開,測試時最省時間
- **`suspend`** — hybrid sleep:image 寫進 disk **之後**再進 S3。有電就從 RAM 快速起來,電池耗盡就 fallback 從 disk 還原。筆電上最實用的模式
- **`test_resume`** — 寫完 image 後立刻自我還原,不斷電。除錯神器

---

## 二、swsusp:snapshot 是怎麼做出來的

Linux 的實作叫 **swsusp**(swap suspend),程式碼在 `kernel/power/`,入口是 `hibernate()`。

流程大致如下:

```
1.  pm_notifier: PM_HIBERNATION_PREPARE
2.  freeze_processes()          ← userspace 全部停住
3.  freeze_kernel_threads()
4.  shrink_all_memory()         ← 騰出空間放 snapshot
5.  dpm_suspend_start(PMSG_FREEZE)   ← driver 的 freeze callbacks
6.  disable_nonboot_cpus() + local_irq_disable()
7.  swsusp_arch_suspend()       ← 存 CPU context,做 atomic copy
8.  解凍 devices / CPU / IRQ    ← driver 的 thaw callbacks
9.  swsusp_write()              ← 壓縮並寫入 swap
10. power_down()                ← driver 的 poweroff callbacks,然後斷電
```

這裡有個容易被跳過但很重要的設計:**為什麼要先複製到記憶體,再寫 disk?**

答案在 step 7。Snapshot 必須是原子的——所有 CPU 停下、IRQ 關閉、世界靜止的那一瞬間拍照。但寫 disk 需要 I/O,需要 interrupt、需要 driver 運作、需要 scheduler,不可能在 IRQ disabled 的狀態下完成。

所以只能分兩段:先在原子狀態下把整個記憶體**複製到記憶體的另一處**,然後解凍世界,再從那份副本慢慢寫進 swap。

這就是 hibernation 記憶體壓力的根源。要放得下副本,系統需要相當可觀的可用記憶體(概念上約需一半的 RAM,實際受壓縮和 `image_size` 影響),這也是 `Not enough free memory` 這類錯誤的來源,以及為什麼 `image_size` 這個 knob 存在。

### Image 在 swap 裡長什麼樣

Image 的第一個 page 是一個 header,關鍵欄位是兩個 signature 和一個 sector 指標:

```c
/* 示意,實際欄位請對照 kernel/power/swap.c */
struct swsusp_header {
    char reserved[...];
    u32 crc32;
    sector_t image;        /* image 起始 sector */
    unsigned int flags;
    char orig_sig[10];     /* 原本的 "SWAPSPACE2" */
    char sig[10];          /* 被覆寫成 "S1SUSPEND" */
} __packed;
```

機制很直白:hibernate 時把 swap 的 magic 從 `SWAPSPACE2` 覆寫成 `S1SUSPEND`,原本的值存到 `orig_sig`。Resume 時 kernel 讀第一個 page,看到 `S1SUSPEND` 就知道有 image;還原成功後把 `orig_sig` 寫回去,這顆 swap 就恢復普通身份。

這解釋了一個實務上的坑:**如果你 hibernate 之後用別的 OS 動過那顆 swap partition,resume 會直接失敗或更糟**。那份 magic 和 sector 指標是唯一的線索,沒有備援。

壓縮預設是 LZO。較新的 kernel 有 `CONFIG_HIBERNATION_COMP_*` 之類的選項可以換成 LZ4(拿壓縮率換速度),具體選項名稱與可用版本請對照自己 tree 的 Kconfig。

---

## 三、兩個 kernel:hibernation 最反直覺的地方

Resume 流程:

```
Bootloader
  → boot kernel 完整開機、初始化所有硬體
  → 讀取 resume= 指定的裝置
  → 發現 S1SUSPEND
  → 把 image kernel 還原到 RAM
  → 跳進 image kernel,boot kernel 就此消失
```

停在這裡想一下這個狀況的含意:

> **硬體是 boot kernel 初始化的,但接手的是 image kernel。**

兩個 kernel 對硬體狀態的認知完全不一致。image kernel 醒來時,它記憶中的「我剛才把這顆 controller 設成這樣」已經不成立了——那些 register 現在是 boot kernel 寫進去的值,或者是 firmware reset 後的預設值。

這就是為什麼 hibernation 在 driver 層需要一整套**獨立於 suspend/resume** 的 callback,而不是複用同一組。這件事是下一節的全部重點。

相關 kernel 參數:

```
resume=/dev/nvme0n1p3
resume_offset=<block>     ← 用 swapfile 時才需要,以 filefrag -v 取得
noresume                  ← 放棄 image,正常開機
```

---

## 四、`dev_pm_ops`:四組 callback 的語意差異

`struct dev_pm_ops` 為 hibernation 準備了三組額外的 callback(freeze / poweroff / restore),各自又有 `_late` 和 `_noirq` 變體:

```c
struct dev_pm_ops {
    int (*prepare)(struct device *dev);
    void (*complete)(struct device *dev);

    /* System suspend (S3) */
    int (*suspend)(struct device *dev);
    int (*suspend_late)(struct device *dev);
    int (*suspend_noirq)(struct device *dev);
    int (*resume_noirq)(struct device *dev);
    int (*resume_early)(struct device *dev);
    int (*resume)(struct device *dev);

    /* Hibernation: snapshot 前後 */
    int (*freeze)(struct device *dev);
    int (*freeze_late)(struct device *dev);
    int (*freeze_noirq)(struct device *dev);
    int (*thaw_noirq)(struct device *dev);
    int (*thaw_early)(struct device *dev);
    int (*thaw)(struct device *dev);

    /* Hibernation: 真正斷電前 */
    int (*poweroff)(struct device *dev);
    int (*poweroff_late)(struct device *dev);
    int (*poweroff_noirq)(struct device *dev);

    /* Hibernation: 從 image 還原之後 */
    int (*restore_noirq)(struct device *dev);
    int (*restore_early)(struct device *dev);
    int (*restore)(struct device *dev);
    /* ... */
};
```

四組的語意:

| Callback | 時機 | 該做什麼 |
|---|---|---|
| `freeze` | snapshot 前 | 停止 DMA 與 IRQ,**但不要斷電、不要改變硬體 config** |
| `thaw` | snapshot 後 | 讓 device 恢復可用,以便把 image 寫進 disk |
| `poweroff` | 斷電前 | 可以放心斷電、放心破壞狀態 |
| `restore` | 還原後 | **完整重新初始化硬體**,不假設任何先前狀態 |

`freeze` 那條限制的理由值得說清楚:**你在 `freeze` 裡對硬體做的任何設定,都會被拍進 image**。如果你在 freeze 階段把 controller 設成某個省電模式,那麼 image kernel 醒來後會認為硬體處在那個模式——但實際上硬體早就被斷電、被 boot kernel 重新初始化過了。認知與現實脫節。

同理,`freeze` 階段**不應該配置新的記憶體**。此時記憶體佈局需要保持穩定,而且 image 還沒建立,任何 allocation 的語意在還原後都會混亂。

### 最常見的 bug 模式

```c
/* 這個 macro 一次綁四組 */
#define SET_SYSTEM_SLEEP_PM_OPS(suspend_fn, resume_fn) \
    .suspend  = suspend_fn, .resume  = resume_fn, \
    .freeze   = suspend_fn, .thaw    = resume_fn, \
    .poweroff = suspend_fn, .restore = resume_fn,
```

很方便,而且**在你的 `resume_fn` 本來就做完整 re-init 的前提下是正確的**。

問題出在那些「聰明」的 resume 實作:只還原部分 register、假設其他值在 S3 期間被硬體保留下來、跳過 firmware 重新載入、沿用既有的 ring buffer 指標。這種寫法在 S3 完全正常——因為 RAM 和大部分 register 真的還在。但在 S4 就會 hang、資料錯亂、或者更惡劣地表現為「開機後某個功能靜默失效」。

需要跨 image 保存狀態的 device 幾乎都要分開實作,典型例子:

- 需要重新載入 firmware blob 的裝置(WiFi、GPU、DSP/NPU)
- 需要重建 DMA ring / descriptor 的 controller
- 需要重新協商 link 的介面(PCIe、USB、MIPI)
- 依賴 external clock / regulator 上電順序的 SoC 子系統

**除錯上的意義**:一個「S3 正常、S4 壞掉」的 bug,第一個該看的地方就是這裡。這幾乎是個模式識別題。

---

## 五、Freezer:協作式而非搶佔式

`freeze_processes()` 不是強制暫停 task,而是一套協作協定:

1. 設定全域的 freezing 狀態
2. 對每個 freezable task 送一個「假 signal」——只是把它從 sleep 喚醒,不是真的 signal
3. Task 在回到 userspace 的路上、或 kernel thread 在自己的迴圈裡呼叫 `try_to_freeze()`,發現 freezing 就把自己標成 frozen 並讓出 CPU
4. 等所有 freezable task 都 frozen,預設 timeout 20 秒

**關鍵設計:安全點是由 task 自己選的。** 這保證了 frozen 的瞬間,不會有 task 卡在持有 filesystem lock、或半完成的 I/O 中間。如果用搶佔式暫停,snapshot 裡就可能凍結一個不一致的狀態,還原後直接資料損壞。

標記 `PF_NOFREEZE` 的 kthread(例如 PM 自己的 worker)不參與。

寫 kthread 時如果會長時間 sleep,必須用 freezable 版本的等待,否則你就是那個讓 hibernate 失敗的人:

```c
/* 錯:hibernate 會 timeout */
wait_event(wq, condition);

/* 對 */
wait_event_freezable(wq, condition);

/* 或在迴圈裡主動檢查 */
if (kthread_freezable_should_stop(NULL))
        break;
```

看到這個訊息就是這件事:

```
Freezing of tasks failed after 20.00 seconds
```

dmesg 會把卡住的 task 名稱和 stack 印出來,直接對照它的等待點即可。

---

## 六、安全性:信任鏈在這裡斷開

回到開頭那句話。Hibernation image 是一份**可以被完整寫回 kernel 記憶體的 blob**,而它躺在 disk 上。

假設攻擊者可以離線讀寫這份 image:

**寫入方向**
- 改寫 kernel text → ring 0 任意程式碼執行
- 改寫 `cred` 結構 → 提權
- 改寫 LSM / lockdown 狀態 → 繞過所有既有 policy

**讀取方向**
- 直接取得記憶體中的 disk encryption key、session key、解密後的資料

而這**完全繞過 Secure Boot**。理由很直接:bootloader 驗證的是 boot kernel 的簽章,但 image 覆蓋掉的是「boot kernel 之後的一切」。驗證點在還原點之前,還原的內容不在驗證範圍內。簽章鏈在這裡斷了。

這跟 measured boot 的失效模式是同一類問題:**measurement chain 只要有一段被繞過,後面所有的驗證都失去意義**。ERoT / iRoT 那套架構之所以要求每一段都 measure 下一段,就是為了不留這種缺口。Hibernation 是一個在 threat model 裡沒有「攻擊者具備物理存取」時看起來完全合理、加進這條假設後整個信任結構就崩掉的機制。

業界的處理方式:

**1. Kernel lockdown 直接禁用**
`lockdown=integrity` 以上,`hibernate()` 回 `-EPERM`。這是為什麼很多開啟 Secure Boot 的發行版 hibernate 就是不能用——不是沒實作,是被政策擋掉。這也是最誠實的一種處理:承認問題沒解決,所以關掉功能。

**2. Windows**
`hiberfil.sys` 在 BitLocker 下被加密,TPM sealing policy 涵蓋 hibernate/resume 路徑。即使如此,在高安全需求場合的建議一直是關掉 hibernate。

**3. ChromeOS**
平台上有專責的 hibernate manager,把 image 用綁定到使用者登入憑證的 key 加密並做完整性驗證。這個設計的價值在於它**正面承認「image = kernel 記憶體」**,因此用與 user data 同等級的保護去對待它,而不是當成一個普通的 swap 檔案。如果你在追 coreboot / verified boot 這條線,這是很好的延伸閱讀。

**4. Upstream**
signed / encrypted snapshot 的 patch series 反覆提交多年,大方向是用 TPM sealed key 或 firmware 提供的 secret 對 image 做 AEAD、把 PCR 值納入 unseal policy。但通用方案長期沒有完整進主線。**這是一個活著的問題,不是已解決的問題。**

**5. 兩個容易被忽略的攻擊面**
- `resume=` 指向的裝置在 resume 流程中極早期就被讀取,此時大部分安全機制還沒建立。歷史上出現過 resume 路徑的 parsing 漏洞
- `/dev/snapshot`(uswsusp 的 ioctl 介面)本質上是「讀寫全部 kernel 記憶體」的 device node,權限管控必須極嚴

---

## 七、除錯手法

實務上最有用的一節。

### 分階段隔離

```bash
echo freezer    > /sys/power/pm_test   # 只測 freeze
echo devices    > /sys/power/pm_test   # 測到 device callbacks
echo platform   > /sys/power/pm_test
echo processors > /sys/power/pm_test
echo core       > /sys/power/pm_test
echo none       > /sys/power/pm_test   # 真的執行
```

由淺到深逐層測,第一個失敗的層級就是問題所在。

### 找出是哪個 device

```bash
echo 1 > /sys/power/pm_print_times      # 每個 callback 的耗時
echo 1 > /sys/power/pm_debug_messages   # 更詳細的 PM log
```

或在 cmdline 加 `initcall_debug`。

### 不斷電的往返測試

```bash
echo test_resume > /sys/power/disk
echo disk > /sys/power/state
```

寫完 image 立刻自我還原。這能在幾秒內驗證 snapshot 與 restore 路徑,不必真的關機再開,是迭代 driver 的 `restore` 實作時最有效率的方式。

### 掛在 console 關掉之後

最惱人的情況——什麼訊息都沒有。cmdline 加:

```
no_console_suspend
```

console 不會被 suspend,可以看到最後的輸出。搭配 `earlycon` 與實體 serial console 效果最好。

### 完全沒有輸出:pm_trace

```bash
echo 1 > /sys/power/pm_trace
```

它把「最後執行的 device callback 的 hash」寫進 RTC 的 scratch register。硬 reset 後開機,dmesg 會列出候選的 device / function 名單。

兩個代價要知道:**RTC 時間會被破壞**(之後記得校時),而且只能定位到 hash 碰撞範圍內的數個候選,不是精確答案。但在「完全沒有線索」的情況下,把範圍從整個 driver tree 縮到三五個候選已經非常有價值。

### Image 太大

```bash
cat /sys/power/image_size          # 預設值約為 RAM 的一個比例
echo 0 > /sys/power/image_size     # 盡可能壓小(較慢)
```

`Not enough free memory` 通常是 `image_size` 設太大,或 swap 空間不足(swap 必須 ≥ image 大小)。

---

## 八、ARM / Android 為什麼幾乎不用 S4

arm64 有 hibernation 實作(`arch/arm64/kernel/hibernate.c`),但實務上量產平台基本不啟用。原因是結構性的:

**1. 沒有 ACPI**
ARM 用 DT + PSCI,`CPU_SUSPEND` 只涵蓋 CPU / cluster 層級。平台級 S4 的語意得自己在 platform code 定義,沒有標準介面。

**2. Suspend 功耗已經夠低**
手機 SoC 的 deep suspend 在 μA~mA 級,待機數天沒問題。S4 省下的那點電不足以支付它的代價。

**3. Flash 寫入成本**
每次 hibernate 往 UFS 寫數 GB,對 endurance 和效能都是負擔。

**4. Resume 反而可能更慢**
從 UFS 讀數 GB 再解壓縮,可能比冷開機還久——尤其 Android 冷開機路徑已經被優化到很快。S4 唯一的賣點(比冷開機快)在這裡消失了。

**5. 與現代 arch 機制的互動很微妙**
KASLR、pointer authentication、MTE 都需要在 image 還原時正確處理。技術上可解,但沒有量產壓力去長期維護這條路徑。

所以在 MediaTek 這類平台上看到的省電機制,會是 s2idle / deep suspend 搭配 SPM、MCUPM 之類的 power firmware 協同,而不是 S4。

### 同名不同物:Android App Hibernation

這個一定要分清楚,因為在 Android 平台的文件、測試項目裡看到 "hibernation" 字樣,**通常指的是這個,跟電源狀態機毫無關係**。

Android 12 引入的 App Hibernation:長期未使用的 App 會被

- 撤銷 runtime permissions
- 清除 cache
- 停止背景執行、移除 job / alarm
- force-stop

實作在 `PermissionController`(`com.android.permissioncontroller`),由 `AppHibernationService` 管理,和 App Standby Buckets、Doze 屬於同一個省電治理家族。

```bash
adb shell cmd app_hibernation
```

如果在 CTS / GTS 或功耗測試報告裡看到 hibernation,先確認是哪一個。

---

## 九、管理平面視角

從 BMC 的角度,它不參與 hibernation,但需要**觀測**它:

- 監看 PCH 的 `SLP_S3#` / `SLP_S4#` / `SLP_S5#` 判斷 host 電源狀態
- IPMI 的 ACPI Power State sensor 回報 S0 / S3 / S4 / S5(sensor type 請對照 IPMI spec 表格確認)
- Redfish 的 `PowerState` 屬性

麻煩點正是第一節那個觀察的延伸:**S4 和 S5 在 pin level 難以區分**,因為硬體行為一樣。要靠 host firmware 透過 KCS / IPMI 主動通知,或觀察 ACPI `_S4` method 有沒有被呼叫,才能區別「關機」和「休眠中」。

不過伺服器平台通常直接不支援 S4——沒有電池、不需要保留狀態,而且第六節那些安全問題在多租戶環境下不可接受。問題就這樣消失了,這算是最省事的解法。

---

## 對照總結

| 面向 | Suspend (S3) | Hibernate (S4) |
|---|---|---|
| RAM | 保持供電 | 斷電 |
| 功耗 | mW 級 | ≈ 0 |
| Resume | < 1s | 秒~數十秒 |
| Driver callback | `suspend` / `resume` | `freeze` / `thaw` / `poweroff` / `restore` |
| 硬體狀態假設 | 大致保留 | 完全未知,需完整 re-init |
| 參與的 kernel 數 | 1 | 2(boot kernel + image kernel) |
| 儲存需求 | 無 | swap ≥ image size |
| Secure Boot | 相容 | 信任鏈斷裂,lockdown 下禁用 |
| ARM / Android | 常用 | 幾乎不用 |

---

## 收束

三個帶得走的點:

1. **Hibernation image 是可寫回的 kernel 記憶體,不是普通的資料檔案。** 這一句話同時解釋了 driver 為什麼需要獨立的 `restore` 語意、以及為什麼它會打斷 Secure Boot 的信任鏈。
2. **「S3 好、S4 壞」是一個有明確特徵的 bug pattern。** 幾乎都指向同一件事:`restore` 沿用了 `resume` 的部分還原邏輯。
3. **Hibernation 的安全問題目前沒有通用解。** 主流做法是「加密 + 綁定平台 key」或「乾脆禁用」。這是一個活著的 upstream 議題。

而最後這點的一般化版本,大概是這整篇文章真正想說的:

> 一個機制的安全性,取決於 threat model 裡有沒有那條你當初沒寫下來的假設。Hibernation 的設計假設是「disk 上的內容不會被惡意修改」——這條假設在 2000 年代的筆電上很合理,在加入物理存取的威脅模型後就完全不成立。而它從來沒有被明確寫在任何地方。

---

## 驗證備註

依我自己的引用原則,把確信程度分開標記:

**可直接對照 kernel source / Documentation 確認**
- `kernel/power/` 下的 `hibernate()`、`swsusp_write()`、freezer 實作
- `Documentation/power/` 下的 `swsusp.rst`、`basic-pm-debugging.rst`、`pm_qos_interface.rst` 等
- `struct dev_pm_ops` 定義於 `include/linux/pm.h`
- `SET_SYSTEM_SLEEP_PM_OPS` 的展開內容(同上檔案,注意不同版本可能改名或棄用)
- `arch/arm64/kernel/hibernate.c` 的存在
- `S1SUSPEND` / `SWAPSPACE2` signature
- `/sys/power/*` 各項介面與 `pm_test` 的合法值

**已刻意標為需自行核對**
- `swsusp_header` 的精確欄位與順序(文中標示為示意)
- `CONFIG_HIBERNATION_COMP_*` 的選項名稱與引入版本
- `/sys/power/image_size` 的預設比例
- IPMI ACPI Power State sensor 的 sensor type 編號

**屬於架構性論述而非可引用事實**
- ChromeOS hibernate manager 的加密設計細節(方向確信,實作細節請查該平台設計文件)
- upstream signed hibernation patch series 的當前狀態(長期未完整合併是確信的,具體進展會隨時間變動)
- 第八節列舉的五個 ARM 不用 S4 的原因——這是綜合推論,不是某份文件的結論
- 第六節將 hibernation 與 measured boot 失效模式類比,屬於我的論述

**未經量測的效能敘述**
文中所有恢復時間、功耗量級都是通用經驗值,不是特定平台的實測數據。若要在文章裡放具體數字,建議自己在目標平台上量。
