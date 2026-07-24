---
title: 資料結構與演算法（DSA）文章索引
sidebar_label: DSA 系列索引
sidebar_position: 8
---

# 資料結構與演算法（DSA）文章索引

本頁整理知識庫中所有資料結構與演算法筆記，依主題分類。文章以 C／Python 從零實作為主線，輔以複雜度分析、面試常見陷阱與 LeetCode 對照——面向準備 firmware／Google／NVIDIA 面試的讀者。

---

## 一、線性資料結構：Linked List

| 文章 | 內容 |
|---|---|
| [Single Linked List](../DSA/Linked_List/0.linked_list.md) | **本系列主線**：`main.c`／`list.h`／`list.c` 三檔從零實作，dummy head 省空串列特判；insert／delete、fast-slow 找中點、delete_dup、swap、reverse／reverseK、帶 comparator 的 merge sort，附 `gcc -Wall` 輸出 |
| [Doubly Linked List](../DSA/Linked_List/1.double_linked_list.md) | prev／next 雙指標、已知節點插刪 O(1)、哨兵簡化邊界；與 array 的四項比較，適合 LRU cache、deque |
| [Linux Kernel Linked List](../DSA/Linked_List/3.linux_linked_list.md) | kernel `list_head` 為何 intrusive／doubly／circular；`container_of` 由成員回推外層 struct、`list_for_each_entry` 巨集、走訪中刪除要用 `_safe` 版 |
| [LeetCode 題目清單](../DSA/Linked_List/2.leetcode.md) | **佔位頁**：六行題號（2095、82、24、25、2487、23），尚無解題內容 |

---

## 二、雜湊與快取

| 文章 | 內容 |
|---|---|
| [雜湊表 Hash Table](../DSA/Hash-Table.md) | hash function → bucket 為何平均 O(1)；碰撞處理 chaining vs open addressing（linear probing）與 cache 行為、load factor／rehash 攤銷、**最壞退化 O(n)**、好 hash function 特性；去重／計數／two-sum／grouping 用途，附 chaining 實作；hash flooding 與可變物件當 key 的陷阱。LeetCode 1、49、3、560 |
| [LRU Cache](../DSA/LRU-Cache.md) | get／put 都要 O(1)、容量滿淘汰最久未用；**為何非 hash map + doubly linked list 不可**（single list 刪中間要 O(n) 找前驅）、dummy head／tail 哨兵、完整實作與易扣分細節；真實世界 page cache／CPU cache 的 LRU 近似。LeetCode 146（LFU 460） |

---

## 三、樹與堆積

| 文章 | 內容 |
|---|---|
| [Binary Tree](../DSA/Tree/binary_tree.md) | 節點結構與四種走訪（pre／in／post／level order，BST 中序得遞增序列、前三者可遞迴或用 stack、層序用 queue），附 invert 遞迴 C 實作與 O(n)／O(h) |
| [Heap](../DSA/Tree/heap.md) | max／min heap property、完全二元樹用 array 實作與索引公式、build heap 從 `n/2 - 1` 為何 O(n)、sift-up／down；延伸 priority queue（Dijkstra、Prim、top-k）與 heap sort |

---

## 四、圖

| 文章 | 內容 |
|---|---|
| [圖與 BFS/DFS](../DSA/Graph-BFS-DFS.md) | 鄰接表 vs 矩陣；BFS（queue、無權最短路、多源）、DFS（連通、環偵測——有向圖三色）、拓撲排序（Kahn／DFS 兩法，Kahn 順便偵環）、Dijkstra 概念、grid 當隱式圖（島嶼／flood fill／腐爛橘子）。LeetCode 200、207、994、733、133 |

---

## 五、搜尋與排序

| 文章 | 內容 |
|---|---|
| [二分搜尋 Binary Search](../DSA/Binary-Search.md) | 基本二分 + lower_bound／upper_bound 邊界（只差一個 `<` vs `<=`）、`mid = lo + (hi-lo)//2` 防溢位（2006 著名 bug）、閉區間 vs 半開區間模板；**答案空間二分**（最佳化轉可行性判定，Google 高頻）、旋轉排序陣列。LeetCode 704、34、33、875、410 |
| [潛伏九年的 binarySearch bug](../binary-search-bug.md) | **故事版**：Joshua Bloch 2006 年那篇〈Nearly All Binary Searches and Mergesorts are Broken〉——`(low + high) / 2` 在 Java 有號 int 溢位變負數、為何要陣列長度逼近 2³⁰ 才會爆所以九年沒人發現、三種修法（先取差再加回、無號右移 `>>> 1`、改用更大型別）與它們的適用語言，以及「測試涵蓋不到的邊界」與型別溢位的一般教訓 |
| [排序演算法總覽](../DSA/Sorting.md) | quick／merge／heap／counting／radix 全景比較表（平均/最壞/空間/穩定/in-place）、`Ω(n log n)` 下界；partition 手寫、mergesort 穩定性與外部排序、heapsort in-place；**何時用哪個**（firmware 記憶體受限、為何標準庫用 introsort/Timsort）。LeetCode 912、215（quickselect） |

---

## 六、演算法範式

| 文章 | 內容 |
|---|---|
| [動態規劃 DP](../DSA/Dynamic-Programming.md) | 兩前提（重疊子問題 + 最優子結構）、四步框架、**怎麼想出狀態**、記憶化 vs 表格法、滾動陣列；五經典（爬樓梯、0/1 背包、LIS、編輯距離、coin change），面試「暴力遞迴 → `@lru_cache` → bottom-up」推導。LeetCode 70、322、300、72、416 |
| [回溯 Backtracking](../DSA/Backtracking.md) | 選擇 → 遞迴 → 撤銷通用框架、與 DFS 的關係、剪枝把指數搜尋變可行；排列／組合／子集／N-queens／電話號碼，複雜度為何 O(N!)／O(2ⁿ)、何時該改用 DP。LeetCode 46、78、77、51、17、39 |

---

## 七、陣列／字串技巧

| 文章 | 內容 |
|---|---|
| [雙指標與滑動視窗](../DSA/Two-Pointers-Sliding-Window.md) | 對撞指標（有序 two-sum、判回文、三數之和）、快慢指標（Floyd 環偵測、找中點、原地去重）、滑動視窗（固定/可變窗、最長不重複子字串、最小覆蓋子字串）；把 O(n²)→O(n)、與單調堆疊分工、負數破壞單調性的陷阱。LeetCode 167、15、3、76、239 |
| [單調堆疊 Monotonic Stack](../DSA/Monotonic-stack.md) | 維持單調性的 stack：把「找左／右第一個更大／更小元素」從暴力 O(n²) 降到 O(n)（每元素只 push/pop 一次）；是 Largest Rectangle、Trapping Rain Water、Daily Temperatures 一整類題的鑰匙 |
| [Boyer-Moore 投票法](../DSA/Boyer-Moore.md) | 找多數元素（> n/2）的 O(n) 時間／O(1) 空間：`candidate` + `count` 兩兩對消、正確性直覺、需否二次驗證。LeetCode 169、229（> n/3） |

---

## 八、位元與系統結構（firmware 味）

| 文章 | 內容 |
|---|---|
| [位元運算 Bit Manipulation](../DSA/Bit-Manipulation.md) | set／clear／toggle／test bit、mask「先清再寫」公式；`n & (n-1)` 消最低位 1、`n & -n` 取最低位 1、判 2 次方、XOR 找落單、Brian Kernighan 數 bit、round up 到 2 次方；firmware 暫存器與對齊；陷阱（算術右移、移位量 UB、`&`/`==` 優先級）。LeetCode 191、136、231、338、260 |
| [環形緩衝區 Circular Buffer](../DSA/Circular-Buffer.md) | ring buffer 的 head／tail、**full vs empty 歧義**與兩種解法（留一格／記 count）、2 次方大小配 `& (size-1)` 取代取模、SPSC 免鎖與 memory barrier；firmware 應用（UART、DMA circular、log ring buffer），附完整 C 實作。LeetCode 622、641 |

---

## 建議閱讀順序

**Linked list 主線**（從零實作 → 進階 → 真實世界 → 練題）：

```
Single Linked List → Doubly Linked List → Linux Kernel Linked List → LeetCode 題目清單
```

**面試衝刺主軸**（核心資料結構 → 搜尋排序 → 範式 → 技巧）：

```
Hash Table          ← 最底層的工具
   → 二分搜尋        ← 最常考、最易寫錯
   → 排序總覽        ← partition 手寫、穩定性
   → 圖與 BFS/DFS    ← 走訪、拓撲、最短路
   → 動態規劃        ← 面試最大宗
   → 回溯            ← 窮舉框架
   → 雙指標/滑動視窗 ← 陣列字串主力手法
```

**firmware／嵌入式加分題**：位元運算、環形緩衝區、LRU Cache、Linux Kernel Linked List。

---

## 待補主題

interview 核心的十個缺口（hash table、二分、排序、圖、DP、回溯、雙指標、位元運算、環形緩衝、LRU）已補上。下一梯次值得補的（依重要性）：

| 主題 | 為什麼重要 | 狀態 |
|---|---|---|
| **Union-Find（並查集）** | 連通分量、動態合併、環偵測（Kruskal MST）；路徑壓縮 + 按秩合併近乎 O(1)。圖題的另一把鑰匙 | 待補 |
| **Trie（字典樹）** | 前綴匹配、自動補全、字典類題；與 hash 的取捨。LeetCode 208、212 | 待補 |
| **Segment Tree／BIT（區間查詢）** | 區間和／區間最值 + 單點更新 O(log n)；競賽與進階面試常見 | 待補 |
| **字串比對（KMP／Rabin-Karp）** | 子字串搜尋從 O(nm) 到 O(n+m)；failure function 的思路 | 待補 |
| **貪心（Greedy）** | 局部最優何時等於全域最優、如何證明（交換論證）；與 DP 的分界 | 待補 |
