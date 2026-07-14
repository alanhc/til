# Heap

Heap 是一種完全二元樹（complete binary tree），滿足 **heap property**：

- **Max heap**：每個節點都 ≥ 其子節點，root 為最大值。
- **Min heap**：每個節點都 ≤ 其子節點，root 為最小值。

因為是完全二元樹，通常用 array 實作（省去指標）。對索引 `i`（0-based）：

- parent：`(i - 1) / 2`
- left child：`2 * i + 1`
- right child：`2 * i + 2`

## 主要操作與時間複雜度

| 操作 | 複雜度 |
| --- | --- |
| 取得 top（peek） | O(1) |
| push（插入後 sift-up） | O(log n) |
| pop（移除 top 後 sift-down） | O(log n) |
| build heap（heapify 整個 array） | O(n) |

- `sift-up`（往上浮）：插入放到尾端，與 parent 比較並交換直到滿足 heap property。
- `sift-down`（往下沉）：把 root 換成尾端元素後，與較大（或較小）的 child 交換往下修正。
- **Heapify**：從最後一個非葉節點 `n/2 - 1` 往前逐一 sift-down，整體 O(n)。

## Priority queue

Heap 是實作 **priority queue** 的常見結構：每次取出優先權最高的元素。

- 應用：Dijkstra、Prim、Huffman coding、事件排程、top-k。
- **Heap sort**：build heap 後反覆 pop 最大值放到尾端，時間 O(n log n)、空間 O(1)。
