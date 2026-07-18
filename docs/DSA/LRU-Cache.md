---
sidebar_label: LRU Cache
---

# LRU 快取（LRU Cache）

**LRU（Least Recently Used）快取** 是一種「容量固定」的快取：當空間用滿、又要放新資料進來時，就淘汰掉 **最久沒被使用** 的那一筆。它是作業系統、資料庫、CPU 都在用的置換策略，也是面試裡的超高頻題（LeetCode 146），因為它剛好把 **hash 表** 和 **doubly linked list** 兩個資料結構優雅地縫在一起。

## 需求：get 和 put 都要 O(1)

題目要求實作一個容量為 `capacity` 的快取，支援兩個操作，而且 **兩者都必須是 O(1)**：

- `get(key)`：若 key 存在，回傳它的值，並把它標記為「剛用過（most recently used）」。
- `put(key, value)`：新增或更新 key，同樣標記為「剛用過」；若加入後超過容量，就 **淘汰最久未使用** 的 key。

難點就在那個「O(1)」。我們需要同時做到三件事，而且每件都要常數時間：

1. 用 key 快速查到值。
2. 快速知道「誰是最久沒用的」以便淘汰。
3. 每次存取後，快速把某筆資料「移到最新」。

## 為什麼是 hash map + doubly linked list

一個資料結構做不到全部，所以要組合兩個，讓它們各自補對方的短處：

**Doubly Linked List 負責「順序」。** 我們用一條串列表示使用順序：**頭部是最近用過的，尾部是最久沒用的**。

- 淘汰時，直接砍掉尾端節點 → O(1)。
- 每次存取後，要把某節點搬到頭部（表示剛用過）。搬動 = 從原位置刪除 + 插到頭部。

這裡就是 **「為什麼非 doubly 不可」** 的關鍵：要 O(1) 刪除「串列中間任意一個節點」，你必須能立刻接上它的「前一個」和「後一個」。**單向串列（single linked list）** 只有 `next`，要刪一個節點得先從頭走到它的前驅才能改指標，那是 O(n)——這樣整個設計就垮了。只有 doubly linked list 同時握有 `prev` 和 `next`，才能在 O(1) 內把節點從任意位置摘除並重接（這點在 [Doubly Linked List](./Linked_List/1.double_linked_list.md) 那篇已列為它的招牌應用）。

**Hash Map 負責「定位」。** 光有串列還不夠：`get(key)` 要先找到 key 對應的節點，如果沿串列線性找就是 O(n)。所以我們用一個 hash map 存 `key -> 該節點的指標`，直接 O(1) 拿到節點，再交給 doubly linked list 做 O(1) 的搬移。

**兩者合起來**：hash map 給你「瞬間找到節點」，doubly linked list 給你「瞬間移動 / 刪除節點」，缺一不可。這種「用一個結構的長處補另一個的短處」正是面試官想看到你講清楚的設計理由。

## dummy head/tail 哨兵：把邊界處理砍掉

搬移和刪除節點時，最容易出錯的是邊界：串列空的時候、只剩一個節點的時候、動到的是頭或尾的時候，指標的 `prev`／`next` 可能是 NULL，一不小心就 segfault 或漏改指標。

解法是放兩個 **哨兵節點（sentinel）**：一個 dummy `head`、一個 dummy `tail`，它們不存真實資料，永遠固定在串列兩端。這樣一來，**任何真實節點都保證有前驅也有後繼**，插入 / 刪除永遠是同一套指標操作，不用寫任何 `if node is None` 的特例判斷。這正是前一篇 doubly linked list 提到「常搭配 dummy head/tail 簡化邊界」的實戰體現。

約定：`head` 之後（`head.next`）是最新的，`tail` 之前（`tail.prev`）是最舊的、待淘汰的。

## 完整實作（Python）

```python
class Node:
    def __init__(self, key=0, value=0):
        self.key = key      # 存 key，淘汰時才能回頭刪 hash map 裡的紀錄
        self.value = value
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}                 # key -> Node
        # 兩個哨兵，串成 head <-> tail 的空串列
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node):            # 從串列摘掉任意節點，O(1)
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_front(self, node):         # 插到 head 之後（標記為最新），O(1)
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        node = self.cache[key]
        self._remove(node)              # 先摘下來
        self._add_front(node)           # 再放到最前 = 剛用過
        return node.value

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self._remove(self.cache[key])   # 舊節點先移除，等下重新放到最前
        node = Node(key, value)
        self.cache[key] = node
        self._add_front(node)
        if len(self.cache) > self.capacity:
            lru = self.tail.prev        # tail 前一個 = 最久沒用的
            self._remove(lru)
            del self.cache[lru.key]     # 別忘了同步從 hash map 刪掉
```

幾個容易漏掉、面試會被扣分的細節：

- **Node 裡要存 `key`**：淘汰時你只拿得到「最舊的節點」，卻要去 hash map 刪掉對應的紀錄。沒有存 key，就無法反查該刪哪個 entry。
- **`put` 到已存在的 key** 要當成「更新 + 移到最前」，別直接新增造成重複。
- **每次 `get` 都會改變順序**，這是 LRU 的定義——「讀取」也算「使用」。

## 變體與真實世界

- **LFU（Least Frequently Used）**：一句話帶過——LRU 淘汰「最久沒用」，LFU 改成淘汰「使用次數最少」的，需要額外維護每個 key 的頻率計數（通常用「頻率 -> 該頻率的節點串列」再配 hash map），實作更繁瑣，對應 LeetCode 460。
- **Page cache（作業系統分頁）**：實體記憶體滿了要換出分頁時，核心用 LRU 近似策略決定犧牲哪一頁。注意是「近似」——真正每次存取都維護精準 LRU 串列太貴，Linux 改用 **clock / second-chance** 這類靠 access bit 的低成本近似。
- **CPU cache**：cache line 的置換也用 LRU 近似（如 pseudo-LRU / tree-PLRU），因為硬體要在幾個 cycle 內決定，容不下維護完整順序串列的成本。這也是為什麼在 firmware / 硬體相關面試裡，理解「精準 LRU 的成本」和「為何實務常退而求近似」會是加分點。

## LeetCode 對照

- **146. LRU Cache** — 本篇主題，hash map + doubly linked list 的經典組合。
- **460. LFU Cache** — 進階變體，改以「使用頻率」為淘汰依據，難度明顯更高。
