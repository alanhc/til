---
sidebar_label: 雜湊表 Hash Table
---

# 雜湊表（Hash Table）

**雜湊表（Hash Table）** 是把「鍵（key）」對應到「值（value）」的資料結構，理想情況下 `insert`／`search`／`delete` 都是 **平均 O(1)**。它幾乎是所有語言標準函式庫的內建型別（C++ `unordered_map`、Python `dict`／`set`、Java `HashMap`、Go `map`），也是演算法面試裡出現頻率最高的工具——很多題目的最佳解，本質就是「用一個 hash 表換掉一層迴圈」，把 O(n²) 壓到 O(n)。

## 核心想法：為什麼平均是 O(1)

底層其實是一個陣列，稱為 bucket 陣列。給一個 key，我們用 **hash function** 把它算成一個整數，再對 bucket 數量取模，得到它該放的索引：

```
index = hash(key) % num_buckets
```

陣列用索引存取是 O(1)，所以只要「算 hash」和「取模」都是常數時間，理論上就能一步定位到 key 的位置。這就是 O(1) 的來源——**它不靠比較大小或走訪，而是直接用 key 算出位址**。

但這裡的 O(1) 是 **平均（攤銷）** 而非最壞。兩個不同的 key 可能算出同一個 index，這叫 **碰撞（collision）**。碰撞無法避免（鴿籠原理：key 的空間遠大於 bucket 數量），所以雜湊表真正的設計重點，其實是「碰撞怎麼處理」以及「如何讓碰撞夠少」。

## 碰撞處理：兩大流派

### Chaining（鏈結法）

每個 bucket 不直接存元素，而是存一個 **鏈結串列（linked list）**。碰撞時就把新元素接到那條串列後面。查詢時先定位到 bucket，再沿著串列線性找。

- 優點：實作簡單、刪除容易（直接從串列摘掉節點）、load factor 可以大於 1 也還能運作、對「刪除頻繁」的場景友善。
- 缺點：每個節點要額外存指標，記憶體開銷大；節點散落在 heap 各處，**cache 不友善**（走訪串列常常 cache miss）。

### Open Addressing（開放定址法）

所有元素都直接住在 bucket 陣列裡，不用額外串列。碰撞時就照某個規則「往後找下一個空位」。最簡單的規則是 **linear probing（線性探測）**：`index`、`index+1`、`index+2`⋯ 逐格找空位。其他變體有 quadratic probing（跳 1、4、9 格）和 double hashing（用第二個 hash function 決定步長）。

- 優點：元素連續存放在同一陣列，**cache 非常友善**，實務上（load factor 不高時）常比 chaining 快。
- 缺點：load factor 一逼近 1 就急遽變慢（好位子被占光，probe 越跑越長）；刪除麻煩——不能直接把格子清空，否則會截斷後面元素的探測路徑，必須用「墓碑（tombstone）」標記，久了又要清理。

一句話對照：

| | Chaining | Open Addressing |
| --- | --- | --- |
| 元素存放 | bucket 外掛串列 | 全部住 bucket 陣列內 |
| cache 行為 | 較差（指標亂跳） | 較好（連續記憶體） |
| load factor 上限 | 可 `>` 1 | 必須 `<` 1（通常 `<=` 0.7） |
| 刪除 | 直接摘節點 | 需 tombstone |
| 誰在用 | Java `HashMap`、Python `dict`（早期概念） | Python `dict`（實際）、Go `map`、多數高效能實作 |

## Load factor 與 rehash

**Load factor（負載因子）** = 元素數量 ÷ bucket 數量。它衡量表有多滿。load factor 越高，碰撞越頻繁，平均查詢時間就從 O(1) 往上飄。

當 load factor 超過門檻（chaining 常設 1.0，open addressing 常設 0.7），就要 **rehash（擴容）**：配置一個更大的 bucket 陣列（通常翻倍），把所有既有元素重新算 hash、搬進新表。

- 為什麼要 rehash：bucket 變多，取模後元素分得更散，碰撞率降回來，維持平均 O(1)。
- 攤銷成本：單次 rehash 是 O(n)，看起來很貴。但因為容量是「翻倍」成長，n 次插入頂多觸發 log n 次 rehash，把總搬移量攤到每次插入上仍是 **攤銷 O(1)**——這和動態陣列（vector）擴容是同一套攤銷分析。
- 面試陷阱：如果每次滿了只「加固定數量」而非「翻倍」，攤銷會退化成 O(n)。成長倍率必須是常數倍。

## 最壞情況：退化成 O(n)

平均 O(1) 有個大前提：**hash function 把 key 均勻打散**。如果所有 key 都碰撞到同一個 bucket，chaining 會變成一條長串列、open addressing 會變成整條探測鏈，查詢就退化成 **O(n)**。

好的 hash function 應具備：

- **均勻分布（uniform）**：輸出盡量鋪滿整個範圍，減少碰撞。
- **雪崩效應（avalanche）**：輸入改一個 bit，輸出要大幅改變，避免相近的 key 擠在一起。
- **確定性 + 夠快**：同一 key 每次算出同值，且計算便宜（否則 O(1) 的常數項太大就失去意義）。

## 面試最常見的四種用途

雜湊表在面試裡幾乎都是拿來「用空間換時間」，記住這四個模式，一半的 easy／medium 題就有思路了：

1. **去重 / 存在性判斷**：丟進 `set`，O(1) 問「看過沒」。
2. **計數（frequency map）**：`key -> 出現次數`，一遍掃完就有統計。
3. **Two Sum 型（補數查表）**：一邊掃一邊把 `目標 - 當前值` 拿去表裡查，把巢狀迴圈變單層。
4. **分組（grouping）**：算一個「正規化的鍵」當 bucket，把同類的丟一起，例如把字串排序後當 key 來 group anagrams。

## 簡化版實作（Python，chaining）

```python
class HashTable:
    def __init__(self, num_buckets=8):
        self.buckets = [[] for _ in range(num_buckets)]
        self.size = 0

    def _index(self, key):
        return hash(key) % len(self.buckets)

    def put(self, key, value):
        bucket = self.buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:            # key 已存在 -> 更新
                bucket[i] = (key, value)
                return
        bucket.append((key, value)) # 新 key -> 接到串列尾
        self.size += 1
        if self.size / len(self.buckets) > 0.75:
            self._rehash()

    def get(self, key):
        bucket = self.buckets[self._index(key)]
        for k, v in bucket:
            if k == key:
                return v
        raise KeyError(key)

    def remove(self, key):
        bucket = self.buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket.pop(i)       # chaining 刪除很單純
                self.size -= 1
                return
        raise KeyError(key)

    def _rehash(self):
        old = self.buckets
        self.buckets = [[] for _ in range(len(old) * 2)]  # 容量翻倍
        self.size = 0
        for bucket in old:
            for k, v in bucket:
                self.put(k, v)      # 每個元素重算 hash 搬過去
```

用 Python 內建的 `list` 當每個 bucket 的串列，雖然不是嚴格的 linked list，但概念一致：定位 bucket 是 O(1)，bucket 內線性找是碰撞的代價。

## 陷阱與冷知識

- **可變物件不能當 key**：key 一旦放進表，它的 hash 值就被「記住」在某個 bucket。如果之後你改了這個物件（例如把 list 內容改掉），它的 hash 變了，你再也找不到它——所以 Python 只允許 **可雜湊（hashable）、不可變** 的物件當 key（`tuple` 可以，`list` 不行）。面試被問「為什麼 list 不能當 dict 的 key」，答案就在這。
- **Hash flooding 攻擊**：如果 hash function 是可預測的，攻擊者可以刻意構造大量「都碰撞到同一 bucket」的 key（例如 HTTP 表單欄位），把 O(1) 打成 O(n)，用少量請求癱瘓伺服器（一種 DoS）。現代語言（如 Python、Java）因此在啟動時加入隨機 **hash seed（SipHash）**，讓外部無法預測碰撞。
- **底層一句話**：Python 的 `dict` 用 **open addressing**（並在 3.6+ 保證插入順序）；C++ 的 `unordered_map` 標準規定用 **chaining**（bucket + 串列），所以它的迭代順序無保證、cache 行為也常被詬病，追求極致效能時大家會換 `absl::flat_hash_map` 這類 open addressing 實作。
- **面試提醒**：被要求「O(1) 解」時，幾乎都是在暗示你用 hash 表；但要主動說明這是「平均 O(1)、最壞 O(n)」，並知道 `TreeMap`／`std::map`（紅黑樹，穩定 O(log n)、有序）是需要「排序 / 範圍查詢」時的替代選擇。這種 trade-off 的自覺，正是 firmware／Google／NVIDIA 面試官想聽到的。

## LeetCode 對照

- **1. Two Sum** — 補數查表，hash 表最經典的入門題。
- **49. Group Anagrams** — 用「排序後字串」當 key 分組。
- **3. Longest Substring Without Repeating Characters** — hash 表（或 set）配滑動視窗，記錄字元最後出現位置。
- **560. Subarray Sum Equals K** — 前綴和 + hash 表計數，把 O(n²) 壓到 O(n) 的代表題。
