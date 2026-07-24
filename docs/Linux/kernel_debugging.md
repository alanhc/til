# Linux 核心除錯案例分析 — 學習筆記

> 原文：jserv〈[Linux 核心除錯案例分析](https://hackmd.io/@sysprog/kernel-debugging)〉
> 主題：如何讀懂 Oops，並從一則真實崩潰追出根因

---

## 一句話總結

崩潰點在 IPC 共享記憶體的 `shm_close()`，但那只是**症狀**；真兇是毫不相干的 CIFS 檔案系統裡潛伏 6 年的 off-by-one 越界寫入，跨越 `kmalloc` 邊界汙染了相鄰的 IPC 物件。**症狀與根因可以相隔十萬八千里**，這是記憶體損毀最難查之處。

---

## 案例現場

- 2017 年，SUSE Linux（核心 `3.0.101`）上的 Oops
- `shm_lock()` 回傳 `-EINVAL` → `IS_ERR()` 為真 → `BUG_ON(IS_ERR(shp))` 觸發（`ipc/shm.c:205`）
- 平台跑在 VMware 虛擬機（與後面 SMP / CSD lock 討論呼應）

### Oops 嚴重程度三級

| 等級 | 意義 | 後果 |
|---|---|---|
| **warning**（`WARN`/`WARN_ON`）| 軟性 assertion | 只打 `W` taint flag，系統照跑（除非 `panic_on_warn`）|
| **oops** | 較嚴重的非預期狀況 | 殺掉出事行程，核心可能存活但狀態不可信 |
| **panic** | 致命錯誤 | 系統徹底停擺，視設定觸發 crash dump / 重開機 |

> 真實站點常設 `panic_on_oops=1`：寧可重啟取得乾淨狀態，也不願在混亂核心上續跑。

---

## 逐欄解剖 Oops（讀崩潰報告的地圖）

### `----[ cut here ]----` 與 BUG 位置
- `cut here` 只是視覺分隔線
- `kernel BUG at shm.c:205` 由 `BUG()` 巨集產生；檔名行號來自 `CONFIG_DEBUG_BUGVERBOSE`（每個 `BUG()` 在 `__bug_table` 留一筆記錄，x86 約佔 70–100 KB）

### invalid opcode 與 `UD2`
- x86-64 的 `BUG()` 刻意發出非法指令 `UD2`（機器碼 `0F 0B`）觸發例外
- 為何不用 `call`？① `UD2` 只佔 2 bytes，縮小 I-cache footprint ② 保證觸發例外，執行流當場停住
- v4.11 起 `WARN()` 也改用此手法

### error code
- 緊接 `invalid opcode:` 的 `0000` 是例外 error code；對 invalid opcode 無意義（恆為 0）
- 真正有用是在 **page fault**，此時是 bitmask：

| bit | 意義 |
|---|---|
| 0 | Present（對映是否存在）|
| 1 | Write（讀/寫）|
| 2 | User（user/kernel 態）|
| 3 | Reserved bit violation |
| 4 | Instruction fetch |

### oops 計數器與 kconfig 狀態
- `[#1]`：本次開機第幾則 oops
- 其後 `SMP` / `PREEMPT` / `DEBUG_PAGEALLOC` / `KASAN` / `PTI` 等，透露核心怎麼編出來的

### 模組清單與 taint flag
- `Modules linked in`：當下載入的模組；括號字母是各自 taint flag

| flag | 意義 |
|---|---|
| `E` | unsigned（未簽章）|
| `X` | externally supported（SUSE 特有）|
| `P` | proprietary |
| `O` | out-of-tree |
| `F` | force-loaded |
| `C` | staging 樹 |
| `+`/`-` | 載入/卸載中 |

- `last unloaded: ppa`：最後卸載的模組（懷疑卸載清理不足時有用）
- taint 的意義：核心誠實標示自己被非開源/未簽章模組汙染過，維護者據此調整信任度

### `RIP` / `RSP` / `EFLAGS`：例外現場座標
- **RIP**（program counter）：凍結在出事那道指令。`shm_close+0x3e` = 函式起點後 0x3e 處，正是 `UD2`
  - `0010:` 前綴是 `CS`，值 `0x10` = `__KERNEL_CS`，RPL=0 → ring 0（核心態）；user 態會是 `0x33`
- **RSP**（stack pointer）：`0xffff8802...` 落在核心直接對映區 → 用核心 stack。backtrace 由此往下展開
- **EFLAGS** `0x00010202`：bit 9 `IF`（中斷開啟）、bit 16 `RF`；判斷是否在關中斷的 critical section

> 長模式下 `CS`/`SS`/`DS`/`ES` 的分段幾乎廢棄；真正還在用基底的是 `FS`（user TLS）與 `GS`（核心 per-CPU）。

### 通用暫存器：高位元樣式即身分

| 虛擬位址範圍 | 用途 |
|---|---|
| `0000...` – `00007FFF...` | user space |
| `DEAD0000...` | 指標毒值 |
| `FFFF8800...` – `FFFFC7FF...` | 實體記憶體直接對映 |
| `FFFFC900...` – `FFFFE8FF...` | vmalloc/ioremap |
| `FFFFEA00...` | vmemmap（`struct page` 陣列）|
| `FFFFFFFF80...` – `9FFFFFFF` | kernel text+data |
| `FFFFFFFFA0...` 起 | kernel 模組 |

- 關鍵發現：`RAX = 0xffffffffffffffea` = `-22` = **`-EINVAL`**
- `RAX` 是回傳值暫存器 → 極可能就是 `shm_lock()` 的結果 → 第一個謎底浮現

> 5-level paging（v4.14+）與 KASLR 會位移/隨機化各區段，但「高位元樣式對應區段」的判讀直覺不變。

### x86-64 呼叫慣例（解 Oops 的隨身手冊）

| 暫存器 | 用途 | 跨呼叫保存 |
|---|---|---|
| RAX | 回傳值 | ✗ |
| RDI/RSI/RDX/RCX/R8/R9 | 第 1–6 引數 | ✗ |
| RBX / RBP / R12–R15 | 區域變數 / frame base | ✓ |
| R10, R11 | scratch | ✗ |

- function vs syscall 差別：第 4 引數 function 用 `RCX`、syscall 用 `R10`（因 `RCX` 被 `syscall` 指令覆寫）
- **殘酷事實**：caller-saved 暫存器在深層呼叫後多半已被覆寫，原始引數往往遺失 → 後續偵查就是一場「哪些指標還活著」的追蹤

### 其他欄位
- **控制暫存器**：`CR2` = page fault 的錯誤位址（本例是 invalid opcode，故無意義）；`CR3` = 頂層 page table 實體位址
- **原始 stack 內容**：堆疊頂端原始傾印，混著回傳位址/暫存器/區域變數（v4.9 移除，但人工分析偶爾能撈出不在暫存器的值）
- **Call Trace**：unwinder 重建的呼叫鏈。`+0x24/0x80` = 函式內偏移 0x24 / 函式總長 0x80。前綴 `?` = 堆疊上疑似殘留、不在當前 frame
- **Code:**：`RIP` 周邊機器碼，`<0f> 0b` = `UD2`；丟給 `scripts/decodecode` 反組譯
- **結尾**：重複 `RIP`/`RSP`（防被 console 捲走）+ `oops_id`

---

## 本案例的情境判讀

Call Trace 顯示行程正在退出：
`sys_exit_group → do_exit → exit_mm → mmput → exit_mmap → remove_vma → shm_close`

**關鍵體悟：情境決定一切。** `shm_close()` 本身幾乎不可能有 bug，它只是受害的執行者。真正的問題是「為什麼此刻 `shm_lock()` 找不到對應的 shmid」。

---

## stack unwinding 的四種機制

| 機制 | 原理 | 優缺點 |
|---|---|---|
| **guess** | 掃堆疊，像指標的值就當回傳位址 | 簡單，但誤判多（滿滿 `?`）|
| **frame pointer** | 順 `RBP` 鏈往回追 | 快速可靠，但有 5–10% 效能衝擊 |
| **DWARF CFI** | 用 debuginfo 反推 | 慢、有時不可靠，已移除 |
| **ORC** | `objtool` 建構時產生 unwind 資料 | 快、可靠、執行期零衝擊，代價 2–4 MB（v4.14+ 主線預設）|

> 標準動作：`./scripts/faddr2line vmlinux shm_close+0x3e/0xb0` 把「函式+偏移」反查成原始行號。

---

## 順藤摸瓜：為何 `shm_lock()` 回傳 `-EINVAL`

`shm_lock()` → `ipc_lock()`，二條路徑會回傳 `-EINVAL`：
1. `idr_find()` 在 IPC 的 IDR 中找不到該 id
2. 找到了，但物件 `deleted` 旗標已設（`ipc_rmid()` 在自旋期間已釋放）

Oops 到此榨乾，下一步只能看 **crash dump**。

---

## 取得 crash dump：kexec + kdump

- 現行標準：**kexec-based kdump**
- `crashkernel=` 在開機極早期保留一塊記憶體，正常核心碰不到 → 即使野指標寫入失控也汙染不到 crash kernel
- panic 時 `crash_kexec()` 不重啟硬體、不回韌體，**直接跳進**早已就緒的精簡 crash kernel
- 舊核心記憶體原封保留，透過 ELF 格式的 `/proc/vmcore` 存取；`makedumpfile` 存檔並過濾無關頁面
- 載入路徑：`kexec_load(2)`（userspace 組段）vs `kexec_file_load(2)`（核心讀檔、驗簽，Secure Boot 必需）
- **為何非得另起核心**：崩潰的核心無法信任自己（可能持著死鎖、page table 損毀、配置器 list 已斷）

---

## 分析 crash dump：`crash` 工具

- Red Hat David Anderson 開發，理解多種傾印格式與部分核心結構（SLAB/SLUB、task、記憶體對映）
- 缺點：內嵌老舊 `gdb`、backtrace 不印區域變數、須同架構
- 常用命令：`dis`（反組譯）、`bt -FF`（豐富 backtrace，位址翻成符號/SLAB 物件）、`ipcs`、`search`、`struct`、`eval`、`kmem`
- 現代工具：**drgn**（Meta，Python 介面、可程式化、不受架構限制），與 `crash` 並存

---

## 案例破解：一步步找回 `shmid`

1. **反組譯確認指標如何遺失**：`vma`（RDI）→ `file`（RAX）→ `sfd`（RBX），但呼叫 `ipc_lock` 後 `mov %rax,%rbx` 把 `sfd` 覆寫掉 → 全部遺失
2. **借 SLAB cache 標記找回 `vma`**：`vma` 有專屬 SLAB cache，`crash` 的 `bt -FF` 自動把堆疊上落在該 cache 的指標標成 `[...:vm_area_struct]` → 找回 `vma = ffff88016d2319e0`
3. **逐層解出 shmid**：沿 `vm_file → private_data → shm_file_data` 走，得 `sfd->id = 13008988`
4. **`ipcs -m` 交叉比對**：表中沒有 `13008988`，但有可疑的 `13008943`（僅差 45），`NATTCH=12`
5. **確認哪個被汙染**：可疑 `shmid_kernel` 的 `shm_file` 與壞掉的 `shm_file_data.file` 相同 → 同一 segment。以該 `file` 指標 `search`，找到 12 個 `size-32` cache 物件：11 個 id 正常（`13008943`），僅 1 個被改成 `13008988`

**結論（什麼錯了）**：一個 `size-32` cache 物件的 `id` 欄位被越界寫入改寫。

---

## 從「什麼錯了」到「為何會錯」

- 不像 RAM bit flip（那通常同機冒出多種 bug）
- `size-32` cache 被所有 17–32 bytes 的 `kmalloc()` 共用 → 可能是 overflow 或 use-after-free
- 需要更多樣本。果然後續陸續冒出 `/proc/slabinfo`、SLAB linked list 損毀的崩潰 → 矛頭指向**對 `size-32` 鄰近物件的越界寫入**

### 跨多份傾印的共同簽名：`2f → 5c`

- SLAB 用 `list_head`（`next`/`prev` 互為反向參照），冗餘讓「壞指標」與「本該的值」一目了然
- 乾淨的傾印裡：壞掉的 `next` 只有一個位元組從 `2f` 變 `5c`

```
eval -b 13008943  → hex c6802f   (正確)
eval -b 13008988  → hex c6805c   (錯誤)
```

- **突破：換個編碼看** — `0x2f` = `/`、`0x5c` = `\`。誰會把 Linux 路徑分隔符 `/` 改成 Windows 的 `\`？→ **CIFS 的 `convert_delimiter()`**

> 除錯心法：數值看似無規律時，先換進位或編碼（十六進位 / ASCII）去看。

---

## 根因：CIFS 的 off-by-one

兇手是 `cifs_build_path_to_root()`（核心 `3.0.101`）：

```c
pplen   = strlen(vol->prepath);              // 不計尾端 null
dfsplen = strnlen(tcon->treeName, ...);      // 不計尾端 null
full_path = kmalloc(dfsplen + pplen + 1);    // +1 給 null，正確

strncpy(full_path, tcon->treeName, dfsplen);       // 寫滿 dfsplen 卻不補 null!
strncpy(full_path + dfsplen, vol->prepath, pplen); // 同樣不補 null
convert_delimiter(full_path, ...);                 // 依賴遇 null 才停 → 越界!
full_path[dfsplen + pplen] = 0;                    // 補 null 排在後面，太遲
```

- `strncpy(dst, src, n)`：`src` 長度 ≥ `n` 時**不補 null**
- `convert_delimiter()` 走訪到 null 才停，但字串沒有終止符 → 越過 `kmalloc` 邊界，把相鄰物件（某個 `shm_file_data`）的 `id` 從 `13008943` 改成 `13008988`
- **修法**：複製階段正確終止字串，或讓 `convert_delimiter()` 受長度約束、別依賴 null

### 為何這次只壞一個位元組？（little-endian）

`id = 13008943` = `0x00c6802f`，記憶體排列 `2f 80 c6 00`。
`convert_delimiter()` 越界後：`0x2f`(`/`)→`0x5c`(`\`) → 掃過 `0x80`、`0xc6`（非分隔符不動）→ 撞上高位的 `0x00` 被當字串終止而停手。
**是 id 數值本身的零高位元組讓越界乾淨收尾**，只留單一位元組改動，才有可辨識的共同簽名。

---

## 這個 bug 的上游歷史

- 約 2011 年、核心 `3.1` 引入（反向移植到 `3.0.x`）
- 2012 年、核心 `3.8` 被**無意間**修掉（那 commit 本意是修別的小問題）
- 客戶 2017 年才回報 → 已是 6 年的 bug，需特定 CIFS 設定（含頻繁重連）才觸發
- 折射的現實：嚴重 bug 可潛伏多年；修補可能無意發生；「一個 bug 只有一份回報」反而是運氣好

---

## 附錄：其他崩潰來源與除錯基礎建設

### 還有什麼會產生 Oops / panic
- **assertion**：`BUG_ON()`、`WARN_ON()`
- **記憶體存取**（看 `CR2`）：NULL 取值、page table 損毀、NX/SMEP/SMAP 違規、核心堆疊溢位、GPF、double fault
- **硬體**：MCE（不可修正硬體錯誤）、NMI（watchdog 逾時、匯流排異常）
- **顯式 `panic()`**：init 死亡、triple fault、開機關鍵配置失敗、`ext4 errors=panic`

### `panic()` 流程
關中斷/搶佔 → IPI 停住其餘 CPU → 印訊息 → panic notifier chain（pstore/netconsole）→ `crash_kexec()`（kdump）→ 依 `panic=` 秒數重開機

關鍵 sysctl：`panic_on_oops`、`panic_on_warn`、`panic_on_taint`、`panic`、`panic_print`

### lockup / stall 偵測
- **soft lockup**：核心態 >20 秒未排程（非搶佔核心）
- **hard lockup**：關中斷 >10 秒（靠 NMI perf event；v6.7 新增不依賴 NMI 的 buddy 偵測器）
- **hung task**：uninterruptible sleep >120 秒（`khungtaskd`）
- **RCU stall**：grace period 過長（預設 21 秒）

### SMP 特有 panic
- 跨 CPU deadlock（AB-BA，用 lockdep 提早抓）
- spinlock 持太久/忘釋放、IPI 與 CSD lock 逾時（VMware/KVM guest 常見）
- 缺 memory barrier 的發布/讀取 race（弱記憶體序的 arm64 才發作，KCSAN 抓）
- **診斷要領**：`bt -a` / `foreach bt` 同時看所有 CPU，別只盯崩潰那一個

### 除錯設施
- **printk / dynamic debug**：`pr_debug()` 可執行期開關（`/sys/kernel/debug/dynamic_debug/control`）；v5.10 無鎖 ringbuffer、v6.x nbcon atomic console
- **live debugging**：`/proc/kcore`（唯讀）、`kgdb`（遠端 gdb server）、`kdb`（核心內 shell）、UML（把核心當 user 行程跑，KUnit 推薦環境）
- **Magic SysRq**：凍結時的後門（口訣 *Raising Elephants Is So Utterly Boring*）
- **除錯用 kconfig**：`DEBUG_LIST`、`DEBUG_VM`、`PAGE_OWNER`、`DEBUG_PAGEALLOC`、`KASAN`（以效能換更早抓錯，但可能改變時序而掩蓋 race）

---

## 一頁速記

1. Oops 每一欄都是 CPU 刻意留下的線索，不是裝飾
2. `RAX` 看回傳值；高位元樣式判斷指標身分；caller-saved 暫存器在深層呼叫後多半已死
3. 情境（Call Trace）決定一切 — 崩潰點常是無辜受害者
4. Oops 榨乾就上 crash dump（kexec/kdump），用 `crash`/`drgn` 挖
5. 靠 SLAB cache 標記找回遺失指標，逐層走指標鏈
6. 數值無規律時換編碼看（hex / ASCII）→ `/` vs `\` 直指 CIFS
7. 根因是 `strncpy` 不補 null + `convert_delimiter` 依賴 null → off-by-one 越界汙染鄰居
8. 症狀（IPC）與根因（CIFS）毫無關聯，只因共用同一 `kmalloc` cache 的鄰接 slot
