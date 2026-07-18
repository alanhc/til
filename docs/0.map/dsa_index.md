---
title: 資料結構與演算法（DSA）文章索引
sidebar_label: DSA 系列索引
sidebar_position: 8
---

# 資料結構與演算法（DSA）文章索引

本頁整理知識庫中所有資料結構與演算法筆記，依主題分類。多數文章以 C 從零實作為主線，輔以複雜度分析與 LeetCode 對照。

---

## 一、Linked List

| 文章 | 內容 |
|---|---|
| [Single Linked List](../DSA/Linked_List/0.linked_list.md) | **本系列主線**：用 `main.c`／`list.h`／`list.c` 三檔從零實作，先解釋 dummy head node 為何能省掉空串列特判（附 ASCII 對照圖）；完整 C 實作涵蓋 insert_head／insert_tail、delete_node、fast-slow pointer 找中間節點、delete_dup、swap（含相鄰節點特例）、reverse、reverseK 分組反轉、帶 comparator function pointer 的 merge sort，末尾附 `gcc -Wall` 編譯與執行輸出 |
| [Doubly Linked List](../DSA/Linked_List/1.double_linked_list.md) | prev／next 雙指標結構、已知節點指標時插入刪除為 O(1)（single list 得先找前驅）、哨兵節點簡化邊界；附與 array 的四項比較表（隨機存取／插入刪除／記憶體 cache friendly／動態成長），結論是適合 LRU cache、deque |
| [Linux Kernel Linked List](../DSA/Linked_List/3.linux_linked_list.md) | kernel 的 `list_head` 為何是 intrusive／doubly／circular：結構內嵌使用者 struct 因此同一結構可掛多個串列、環狀讓插刪不必特判 NULL、空串列即 `head->next == head`；`container_of` 如何由成員指標回推外層 struct，以及 `list_add`／`list_del`／`list_for_each_entry` 等巨集與「走訪中刪除要用 `_safe` 版本」的原因 |
| [LeetCode 題目清單](../DSA/Linked_List/2.leetcode.md) | **佔位頁**：只有六行題號（2095、82、24、25、2487、23），對應主線實作的各項操作，尚無任何解題內容或說明 |

---

## 二、Tree

| 文章 | 內容 |
|---|---|
| [Binary Tree](../DSA/Tree/binary_tree.md) | 節點結構與四種走訪（preorder／inorder／postorder／level order，並點出 BST 中序走訪得遞增序列、前三者可遞迴或用 stack、層序用 queue），附 invert binary tree 的遞迴 C 實作與 O(n)／O(h) 複雜度 |
| [Heap](../DSA/Tree/heap.md) | max／min heap 的 heap property、因為是完全二元樹所以用 array 實作及 parent／left／right 的索引公式、peek／push／pop／build heap 複雜度表、sift-up 與 sift-down 的動作、heapify 從 `n/2 - 1` 往前為何是 O(n)；並延伸到 priority queue 應用（Dijkstra、Prim、Huffman、top-k）與 heap sort |

---

## 三、演算法

| 文章 | 內容 |
|---|---|
| [Boyer-Moore 投票法](../DSA/Boyer-Moore.md) | 找多數元素（出現 > n/2 次）的 O(n) 時間／O(1) 空間演算法：維護 `candidate` + `count` 兩兩對消、正確性直覺（多數元素抵消完必有剩）、需否二次遍歷驗證，附 Python 實作與逐步走表；經典題 LeetCode 169，進階 229（> n/3 維護兩個候選人） |
| [單調堆疊 Monotonic Stack](../DSA/Monotonic-stack.md) | 維持單調性的 stack 使用技巧：把「找左／右第一個更大／更小元素」（Next Greater/Smaller）從暴力 O(n²) 降到 O(n)——每個元素只 push/pop 一次；附遞減 stack 的 Python 實作與直覺，並點出它是 Largest Rectangle、Trapping Rain Water、Daily Temperatures 等一整類難題的鑰匙 |

---

## 建議閱讀順序

**Linked list 主線**（從零實作 → 進階 → 真實世界 → 練題）：

```
Single Linked List          ← 主線，從零實作與各種操作
   → Doubly Linked List     ← 多一個 prev 指標換來什麼
   → Linux Kernel Linked List  ← 真實世界怎麼做：intrusive + circular
   → LeetCode 題目清單      ← 拿題目對照練（目前僅題號）
```

---

## 待補主題

用第一性原理看一場 DSA 面試考的是三件事：**核心資料結構 + 演算法範式 + 複雜度分析**。對 firmware／Google／NVIDIA 這類系統性職位，再加上一條**位元運算與系統結構**的線（暫存器、緩衝區、快取）。下表是這張地圖上重要、面試常考、但目前筆記還沒有的缺口，依重要性排序。

| 主題 | 為什麼重要 | 狀態 |
|---|---|---|
| **Hash Table / Hash Map** | 最基礎卻缺席的資料結構。碰撞處理（chaining vs open addressing）、load factor、為何攤銷是 O(1)、最壞退化成 O(n)。幾乎每場面試的底層工具（去重、two-sum、計數），不懂它等於少一半解題手段 | 待補 |
| **位元運算（Bit Manipulation）** | **firmware 的日常**（暫存器 set／clear／toggle、mask、對齊、判 2 的次方），同時是 Google／NVIDIA 高頻題：`n & (n-1)` 消最低位 1、Brian Kernighan 數 bit、XOR 找落單的數、用位元做狀態壓縮。系統職位的必考交集 | 待補 |
| **二分搜尋與邊界變體** | 不只是「在排序陣列找值」，而是 lower_bound／upper_bound 的邊界處理、以及**在答案空間二分**（把最佳化問題轉成可行性判定）。Google 特別愛考，也最容易寫出 off-by-one | 待補 |
| **動態規劃（DP）** | 面試最大宗、也最能區分程度：狀態怎麼定、轉移怎麼寫、邊界、記憶化 vs 表格法、滾動陣列省空間。常見型（0/1 背包、LIS、編輯距離、區間 DP）認得出來就解得開 | 待補 |
| **Graph 表示 + BFS／DFS** | 鄰接表 vs 矩陣、BFS（最短步數／層序）、DFS（連通、環偵測）、拓撲排序、Dijkstra。系統依賴、排程、狀態機本質都是圖 | 待補 |
| **雙指標 / 滑動視窗** | 把一大類 O(n²) 掃描降到 O(n) 的模式（區間和、最長不重複子字串、快慢指標）。與已有的 [單調堆疊](../DSA/Monotonic-stack.md) 互補，是陣列／字串題的主力手法 | 待補 |
| **排序演算法總覽** | quick／merge／heap sort 的比較、穩定性、in-place、平均 vs 最壞、何時用哪個。目前 merge sort 只散在 linked list 那篇，缺一張總覽與「面試被要求手寫 quicksort partition」的準備 | 待補 |
| **Circular Buffer（環形緩衝區）** | **firmware 專屬高頻**：UART／DMA／log 的 ring buffer、head／tail 指標、full vs empty 怎麼區分、為何常用 2 的次方大小配 mask。嵌入式面試幾乎必問，但純軟體題庫少見 | 待補 |
| **LRU Cache** | 經典組合題（hash map + doubly linked list O(1) 存取與淘汰），你的 [Doubly Linked List](../DSA/Linked_List/1.double_linked_list.md) 已把它列為應用。LeetCode 146，快取設計面試的定番 | 待補 |
| **回溯（Backtracking）** | 排列／組合／子集／N-queens 的通用框架：DFS + 選擇/還原狀態 + 剪枝。一旦看懂框架，一整類「窮舉所有可能」的題都同一套寫法 | 待補 |
