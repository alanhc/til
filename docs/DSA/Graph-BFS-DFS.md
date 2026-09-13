---
sidebar_label: 圖與 BFS/DFS
---

# 圖與 BFS/DFS

圖（graph）是演算法面試裡最會「換皮」的主題：迷宮、島嶼、課程依賴、社群網路、狀態轉移、build 系統，表面完全不同，本質都是「節點 + 邊」加上 **BFS 或 DFS** 兩把走訪的刀。認出「這其實是一張圖」通常就解決了一半，剩下的只是選對走訪方式。

這篇把圖的表示、兩種走訪、以及幾個從走訪長出來的經典模式（連通分量、環偵測、拓撲排序、最短路）串起來，並點出面試怎麼考、哪裡容易踩雷。

## 圖的表示：鄰接表 vs 鄰接矩陣

一張圖有 `V` 個節點、`E` 條邊。怎麼把它存進記憶體，直接決定你的時間與空間複雜度。

**鄰接表（adjacency list）**：每個節點掛一個「鄰居清單」。這是絕大多數題目的預設選擇。

```python
from collections import defaultdict

graph = defaultdict(list)
for u, v in edges:          # 無向圖兩邊都加
    graph[u].append(v)
    graph[v].append(u)
```

**鄰接矩陣（adjacency matrix）**：一個 `V x V` 的二維陣列，`matrix[u][v]` 表示 `u -> v` 有沒有邊（或權重）。

```python
matrix = [[0] * V for _ in range(V)]
for u, v in edges:
    matrix[u][v] = 1
    matrix[v][u] = 1
```

怎麼選？看下面這張對照：

| 面向 | 鄰接表 | 鄰接矩陣 |
|------|--------|----------|
| 空間 | `O(V + E)` | `O(V²)` |
| 查「u、v 之間有沒有邊」 | `O(deg(u))` | `O(1)` |
| 走訪某節點的所有鄰居 | `O(deg(u))`，剛好 | `O(V)`，要掃整列 |
| 適合的圖 | 稀疏圖（`E` 遠小於 `V²`） | 稠密圖，或頻繁查詢邊 |

**關鍵直覺**：現實世界的圖幾乎都是稀疏的（一個人臉書好友不會有幾百萬個），所以鄰接表是預設。鄰接矩陣的 `O(V²)` 空間在 `V` 上萬時就爆了；但如果 `V` 很小（例如 100 個節點的全連接圖）、或你要反覆查「這兩點相不相連」，矩陣的 `O(1)` 查詢反而香。

面試裡有個常被忽略的細節：**grid（格子）本身就是一張隱式的圖**，不需要真的建鄰接表。每個格子是節點，上下左右四個方向就是邊。這點在島嶼類題目非常關鍵，等下會回來講。

## BFS：一圈一圈往外擴

**BFS（Breadth-First Search，廣度優先）** 用一個 **queue（佇列）**，從起點開始「一圈一圈」往外擴散：先訪問所有距離 1 的節點，再訪問距離 2 的，以此類推。

```python
from collections import deque

def bfs(graph, start):
    visited = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        # 處理 node
        for nxt in graph[node]:
            if nxt not in visited:
                visited.add(nxt)      # 進 queue 的當下就標記
                queue.append(nxt)
```

**踩雷警告**：`visited` 一定要在「放進 queue 的當下」就標記，不是在「從 queue 拿出來」時才標記。否則同一個節點會被不同鄰居重複塞進 queue，輕則變慢，重則 TLE 或記憶體爆炸。這是 BFS 最常見的 bug。

### BFS 的殺手級應用：無權圖最短步數

BFS 逐層擴散的特性，天生就是「無權圖最短路徑」的答案：**第一次碰到某個節點時的層數，就是從起點到它的最短步數**。因為 BFS 保證先把近的走完才走遠的，不可能有更短的路徑被漏掉。

要記錄「距離」或「按層處理」，用經典的 **level-order（層序）** 寫法——先量出當前這層有幾個，一次處理一整層：

```python
def shortest_steps(graph, start, target):
    visited = {start}
    queue = deque([start])
    steps = 0
    while queue:
        for _ in range(len(queue)):   # 固定住「這一層」的大小
            node = queue.popleft()
            if node == target:
                return steps
            for nxt in graph[node]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        steps += 1                     # 整層處理完，步數 +1
    return -1
```

這個 `for _ in range(len(queue))` 的「凍結一層」技巧務必記熟，層序走訪、二元樹的 level order、多源 BFS 都靠它。

**注意前提**：BFS 給的是「邊數最少」的最短路，只在**無權圖**（或每條邊權重都相同）成立。一旦邊有不同權重，就要換 Dijkstra（後面談）。這是面試官很愛設的陷阱——題目描述有隱藏權重時你還用 BFS 就錯了。

## DFS：一條路走到底

**DFS（Depth-First Search，深度優先）** 反過來：沿著一條路一直往深處走，走到不能走了才回頭（backtrack）。可以用遞迴，也可以用一個 **stack**（顯式模擬）。

```python
def dfs(graph, node, visited):
    visited.add(node)
    # 處理 node
    for nxt in graph[node]:
        if nxt not in visited:
            dfs(graph, nxt, visited)
```

遞迴寫起來最短最直覺，但**遞迴深度就是 DFS 的走訪深度**。在 firmware / 系統面試裡這點特別要提：Python 預設遞迴上限約 1000，鏈狀的長圖（例如一條 10⁵ 節點的長鏈）會 `RecursionError`；C/C++ 則是爆 stack overflow。面對可能很深的圖，改用顯式 stack 是穩健做法：

```python
def dfs_iterative(graph, start):
    visited = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        # 處理 node
        for nxt in graph[node]:
            if nxt not in visited:
                stack.append(nxt)
```

### DFS 的應用一：連通分量

「這張圖分成幾塊互不相連的部分？」對每個還沒被訪問的節點發動一次 DFS，能一口氣訪問的就是同一塊，發動的次數就是連通分量數。

```python
def count_components(graph, nodes):
    visited = set()
    count = 0
    for node in nodes:
        if node not in visited:
            count += 1
            dfs(graph, node, visited)   # 把整塊染色
    return count
```

（進階：連通分量、合併問題也常用 **Union-Find（並查集）**，那是另一個值得專精的工具，這裡先用 DFS 帶過。）

### DFS 的應用二：環偵測

**無向圖**偵測環：DFS 過程中若碰到一個「已訪問、而且不是我來時的那個父節點」的鄰居，就有環。

**有向圖**偵測環比較微妙，要用「三色」概念——正在遞迴堆疊上的節點（灰色）如果又被碰到，代表有一條邊指回祖先，就是環：

```python
def has_cycle_directed(graph, nodes):
    WHITE, GRAY, BLACK = 0, 1, 2      # 未訪問 / 遞迴中 / 已完成
    color = {node: WHITE for node in nodes}

    def dfs(u):
        color[u] = GRAY
        for v in graph[u]:
            if color[v] == GRAY:      # 指回還在堆疊上的祖先 → 環
                return True
            if color[v] == WHITE and dfs(v):
                return True
        color[u] = BLACK              # u 的子樹都探完了，確定沒環
        return False
    return any(dfs(n) for n in nodes if color[n] == WHITE)
```

為什麼要區分 GRAY 和 BLACK？因為在有向圖裡，碰到一個「已完成（BLACK）」的節點不代表有環——那只是兩條路徑匯到同一個下游而已。只有碰到「還在當前遞迴路徑上（GRAY）」的節點，才真的形成回邊。這個區別是有向圖環偵測的核心，面試常考。

## 拓撲排序：把依賴攤平成一條線

**拓撲排序（topological sort）** 只對 **DAG（Directed Acyclic Graph，有向無環圖）** 有意義：把節點排成一列，使得每條邊 `u -> v` 都滿足 `u` 排在 `v` 前面。白話就是「解依賴」——要先修完先修課、先 build 完被依賴的 library。

有兩種標準做法。

**做法一：Kahn 演算法（BFS 版，數入度）**。維護每個節點的**入度（in-degree，指進來的邊數）**，把入度為 0 的（沒有任何前置依賴的）丟進 queue，取出一個就把它的鄰居入度減一，減到 0 就入列：

```python
from collections import deque

def topo_sort_kahn(graph, num_nodes):
    indegree = [0] * num_nodes
    for u in graph:
        for v in graph[u]:
            indegree[v] += 1

    queue = deque([i for i in range(num_nodes) if indegree[i] == 0])
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    # 若排出來的數量 < 節點總數，代表有環，無法完成拓撲排序
    return order if len(order) == num_nodes else []
```

Kahn 的一大好處：**它順便偵測環**。如果最後排進 `order` 的節點數少於總數，代表有些節點的入度永遠降不到 0——它們卡在一個環裡。這就是 LeetCode 207（課程表，問能不能修完所有課）的標準解。

**做法二：DFS 版**。對每個節點做 DFS，在「該節點的所有後代都處理完（回溯的那一刻）」把它推入結果，最後把結果反轉：

```python
def topo_sort_dfs(graph, nodes):
    visited, order = set(), []
    def dfs(u):
        visited.add(u)
        for v in graph[u]:
            if v not in visited:
                dfs(v)
        order.append(u)        # 後序：子孫都排完才輪到自己
    for n in nodes:
        if n not in visited:
            dfs(n)
    return order[::-1]         # 反轉才是拓撲序
```

**兩者怎麼選？** 面試裡通常寫 Kahn，因為它同時給你「拓撲序 + 是否有環」，邏輯也好講。DFS 版更精簡但要小心：純 DFS 版本沒有內建環偵測，若圖可能有環得另外加三色判斷。實務上 build 系統（make、bazel）、套件管理器（npm、pip 解相依）、Excel 公式重算順序，底層都是拓撲排序。

## 最短路：有權重就換 Dijkstra（點到為止）

前面說 BFS 只對「無權圖」給最短路。一旦每條邊有不同的正權重（例如城市間的距離、網路延遲），就要用 **Dijkstra**。

核心概念：用一個 **min-heap（最小堆）** 永遠先展開「目前已知總距離最小」的節點。它其實就是 BFS 的加權版——BFS 用 queue 是因為每步成本都是 1，先進先出剛好等於距離由近到遠；Dijkstra 把 queue 換成 heap，讓「距離最小的先出」，就能處理不同權重。

```python
import heapq

def dijkstra(graph, start, n):     # graph[u] = [(v, weight), ...]
    dist = [float('inf')] * n
    dist[start] = 0
    heap = [(0, start)]            # (累計距離, 節點)
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:            # 過期的舊紀錄，跳過
            continue
        for v, w in graph[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    return dist
```

這篇不深入 Dijkstra（heap 的用法可參考 heap 專篇），只要記住這條決策線：**無權/等權 → BFS；正權重 → Dijkstra；有負權 → Bellman-Ford**。面試官從 BFS 題臨時加一句「每條路有不同耗時」時，就是在測你會不會切換。

## 把 grid 當圖：島嶼問題

回到前面埋的伏筆。很多題目給你一個二維格子，其實就是一張隱式圖：**每個格子是節點，上下左右相鄰是邊**，不用真的建鄰接表。這類題目的代表就是 **LeetCode 200（島嶼數量）**——數有幾塊相連的陸地，本質就是「數連通分量」。

```python
def num_islands(grid):
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    count = 0

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != '1':
            return
        grid[r][c] = '0'                 # 直接改成 '0' 當作已訪問（沉島）
        dfs(r + 1, c)
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1               # 找到新島
                dfs(r, c)                # 把整座島沉掉
    return count
```

幾個 grid 題常見變體與陷阱：

- **原地標記省空間**：把訪問過的 `'1'` 直接改成 `'0'`，就省掉一個 `visited` 陣列。但這會**破壞輸入**——面試時先問一句「可以修改輸入嗎？」是加分行為，也是嚴謹的表現。不能改就另開 `visited`。
- **DFS 遞迴深度**：一整塊都是陸地的大 grid，DFS 深度可達 `rows × cols`，可能爆遞迴。穩健版用 BFS 或顯式 stack。
- **BFS 還是 DFS？** 純粹數島嶼兩者都行。但如果問「最短路徑」或「同時從多個源頭擴散」，就一定是 BFS。**LeetCode 994（腐爛的橘子）** 就是經典的**多源 BFS**：把所有一開始就爛的橘子全部先放進 queue 當第 0 層，一起往外擴散，層數就是全部腐爛所需的分鐘數。
- **LeetCode 733（Flood Fill）** 是最純粹的 grid DFS/BFS 染色，油漆桶工具的原理。

## 圖走訪的其他化身

同一套 BFS/DFS，換個場景就是新題：

- **狀態機 / 隱式圖**：節點不一定是實體的點，也可以是「一個狀態」。例如「每次可以把數字某位 +1 或 -1，最少幾步從 A 到 B」，把每個數字當節點、合法操作當邊，就是 BFS 最短步數。像單字接龍（Word Ladder）也是這類：每個單字是節點，改一個字母能到的單字是鄰居。
- **克隆圖 LeetCode 133**：深拷貝一張圖，一邊 DFS/BFS 走訪、一邊用 hash map 記錄「原節點 → 新節點」避免重複建立與無限迴圈。考點是你會不會用 map 打破環。
- **build 依賴 / 課程規劃 LeetCode 207、210**：前面講過的拓撲排序，是有向圖走訪的招牌應用。

## 面試小抄與常見陷阱

- **先問清楚圖的性質**：有向還無向？有沒有環？有沒有權重？連不連通？這幾個問題直接決定用哪個演算法，開場就問能展現系統性思考。
- **BFS 標記時機**：`visited` 在**入列時**標記，不是出列時。這是最高頻的 bug。
- **BFS = 無權最短路，DFS 不保證最短**：要最短步數就別用 DFS。
- **有向圖環偵測要三色**：GRAY（遞迴中）才算環，BLACK（已完成）不算。
- **遞迴深度**：長鏈圖用遞迴 DFS 會爆 stack，firmware / 系統向的面試尤其在意，改顯式 stack 或 BFS。
- **複雜度**：鄰接表上的 BFS/DFS 都是 `O(V + E)` 時間、`O(V)` 空間——每個節點訪問一次、每條邊看一次。能一句話講清楚這個是基本功。

單調堆疊那種「線性掃描」的模式解決的是一維陣列上的鄰居關係；圖走訪則把「鄰居關係」推廣到任意結構。當你發現問題裡的物件彼此有「連接 / 依賴 / 可達」的關係時，先停下來問一句：**這是不是一張圖？** 是的話，BFS 和 DFS 就是你的起手式。

## LeetCode 練習

| 題號 | 題目 | 考點 |
|------|------|------|
| 200 | Number of Islands | grid 當圖、連通分量、DFS/BFS 染色 |
| 733 | Flood Fill | 最純粹的 grid 走訪 |
| 994 | Rotting Oranges | 多源 BFS、層序計時 |
| 207 | Course Schedule | 拓撲排序（Kahn）、有向圖環偵測 |
| 133 | Clone Graph | DFS/BFS + hash map 破環 |
