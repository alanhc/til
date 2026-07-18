---
sidebar_label: 排序演算法總覽
---

# 排序演算法總覽（Sorting Algorithms）

排序是最基礎、也最容易被面試官拿來「探底」的主題。很多人以為「排序不就 `sort()` 一行」，但面試真正想知道的是：**你懂不懂每個演算法背後的取捨**——為什麼 quicksort 平均最快卻可能退化成 O(n²)？為什麼 mergesort 穩定但要額外空間？在 firmware 這種**記憶體受限**的場景該選哪個？為什麼 C++ 標準庫用 introsort、Python 用 Timsort，而不是純 quicksort？

這篇把三大比較排序（quick / merge / heap）、線性排序（counting / radix），以及「何時用哪個」的決策邏輯講清楚，並點出面試常見的手寫題與陷阱。

## 先看全景比較表

| 演算法 | 平均 | 最壞 | 額外空間 | 穩定 | in-place | 一句話特性 |
|--------|------|------|----------|------|----------|-----------|
| Quicksort | O(n log n) | O(n²) | O(log n)（遞迴堆疊） | 否 | 是 | 平均最快、常數小、快取友善 |
| Mergesort | O(n log n) | O(n log n) | O(n) | 是 | 否 | 最壞也穩定、可做外部排序 |
| Heapsort | O(n log n) | O(n log n) | O(1) | 否 | 是 | 最壞有保證、空間最省 |
| Counting sort | O(n + k) | O(n + k) | O(n + k) | 是 | 否 | 值域 `k` 小才划算 |
| Radix sort | O(d·(n + k)) | O(d·(n + k)) | O(n + k) | 是 | 否 | 固定長度整數/字串 |

（`k` = 值域大小，`d` = 位數。）

幾個要點先講在前面：

- **比較排序的下界是 `Ω(n log n)`**。任何只靠「兩兩比較」的排序，最好也只能到 n log n——因為 n 個元素有 n! 種排列，每次比較最多砍一半可能性，需要 `log₂(n!) ≈ n log n` 次比較。這是資訊理論的硬下界，quick/merge/heap 都在這條線上。要突破它，就得不靠比較（counting/radix）。
- **穩定（stable）**：相同鍵值的元素排完後相對順序不變。多鍵排序（先按 A 排、再按 B 排且要保留 A 的順序）時很重要。
- **in-place**：只用 O(1) 或 O(log n) 額外空間，不需要與輸入等量的緩衝區。

## Quicksort：平均最快，但要小心最壞

核心是 **partition（分割）**：選一個 pivot，把陣列重排成「左邊都 `≤ pivot`、右邊都 `≥ pivot`」，pivot 落到最終位置，再遞迴處理左右兩段。

partition 是面試最常要求**手寫**的部分，一定要能默寫。以下是經典的 Lomuto 分割（好記）：

```python
def quicksort(arr, lo, hi):
    if lo < hi:
        p = partition(arr, lo, hi)
        quicksort(arr, lo, p - 1)
        quicksort(arr, p + 1, hi)

def partition(arr, lo, hi):
    pivot = arr[hi]          # 取最右為 pivot
    i = lo                   # i 指向「小於 pivot 區」的下一個位置
    for j in range(lo, hi):
        if arr[j] < pivot:
            arr[i], arr[j] = arr[j], arr[i]
            i += 1
    arr[i], arr[hi] = arr[hi], arr[i]  # pivot 歸位
    return i
```

C 版本（firmware 面試常見，練一次手感）：

```c
int partition(int a[], int lo, int hi) {
    int pivot = a[hi], i = lo;
    for (int j = lo; j < hi; j++) {
        if (a[j] < pivot) {
            int t = a[i]; a[i] = a[j]; a[j] = t;
            i++;
        }
    }
    int t = a[i]; a[i] = a[hi]; a[hi] = t;
    return i;
}
```

**為什麼平均最快？** 雖然跟 merge/heap 同樣是 O(n log n)，但 quicksort 的**常數因子小**：內層迴圈只做比較和偶爾交換，且存取是連續的、對 CPU **快取友善（cache-friendly）**。這在實務上讓它通常比 heapsort 快好幾倍——複雜度一樣，常數差很多。

**最壞 O(n²) 從哪來？** 如果每次 pivot 都選到最大或最小值（例如**對已排序陣列固定取最右當 pivot**），partition 只能切掉一個元素，遞迴深度變成 n，退化成 O(n²)，還可能**遞迴堆疊爆掉（stack overflow）**。面試最愛的陷阱就是：「你的 quicksort 對已經排好序的輸入會發生什麼事？」

**怎麼避免？** pivot 選擇是關鍵：

- **隨機 pivot**：隨機挑一個位置，讓對手構造不出最壞輸入，期望 O(n log n)。
- **三數取中（median-of-three）**：取首、中、尾三者的中位數當 pivot，對已排序輸入特別有效。
- **introsort**：C++ `std::sort` 的做法——先用 quicksort，一旦遞迴深度超過 `2 log n`（偵測到退化）就切換成 heapsort，把最壞從 O(n²) 拉回**保證的 O(n log n)**，同時保留 quicksort 平均快的優點。這是「為什麼標準庫不用純 quicksort」的標準答案。

**注意 quicksort 不穩定**：partition 的交換會打亂相同鍵值的相對順序。

## Mergesort：穩定、最壞也漂亮、能做外部排序

核心是**分治（divide and conquer）**：把陣列對半切到剩單一元素，再兩兩**合併（merge）**成有序序列。

```python
def mergesort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    res, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:    # <= 是穩定性的關鍵
            res.append(left[i]); i += 1
        else:
            res.append(right[j]); j += 1
    res.extend(left[i:])
    res.extend(right[j:])
    return res
```

**為什麼穩定？** merge 時遇到相等的元素，`<=` 讓「來自左半（原本在前）」的先被放進去，相對順序就保住了。把 `<=` 改成 `<` 就會變不穩定——這是一行程式碼決定穩定性的經典例子，面試官可能故意問。

**為什麼最壞也是 O(n log n)？** 分治的樹高固定是 `log n`（每次對半，跟資料內容無關），每層 merge 總共 O(n)。不像 quicksort 依賴 pivot 運氣，mergesort **不管輸入長怎樣都是 n log n**，這是它「最壞有保證」的來源。

**代價是 O(n) 額外空間**：merge 需要一個與輸入等量的緩衝區，不是 in-place。這正是記憶體受限時的痛點。

**外部排序（external sort）**：mergesort 的分治結構天生適合「資料量大到塞不進記憶體」的場景——把大檔案切成能放進 RAM 的小塊，各自排序後寫回磁碟，再**多路合併（k-way merge）**。這是資料庫、大檔案排序的標準做法，也是 mergesort 不可取代的地方。**Timsort**（Python `sorted`、Java `Arrays.sort` for objects 採用）是 mergesort 的實務強化版，利用真實資料常有的「已排序片段（run）」加速，並保有穩定性。

## Heapsort：in-place、最壞有保證、但不穩定也不快取友善

核心是利用 [heap](./Tree/heap)：先把陣列 **build 成 max heap**（O(n)），然後反覆「把 root（最大值）跟尾端交換、縮小 heap、sift-down 修復」，最大值就一個個沉到尾端，最終得到升序。

```python
def heapsort(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):   # build max heap，O(n)
        sift_down(arr, i, n)
    for end in range(n - 1, 0, -1):
        arr[0], arr[end] = arr[end], arr[0]  # 最大值換到尾端
        sift_down(arr, 0, end)               # 對縮小的 heap 修復

def sift_down(arr, i, n):
    while True:
        largest, l, r = i, 2 * i + 1, 2 * i + 2
        if l < n and arr[l] > arr[largest]: largest = l
        if r < n and arr[r] > arr[largest]: largest = r
        if largest == i: break
        arr[i], arr[largest] = arr[largest], arr[i]
        i = largest
```

**heapsort 的獨特賣點**：它是唯一同時做到 **in-place（O(1) 額外空間）** 和 **最壞 O(n log n) 保證** 的比較排序。quicksort 省空間但最壞 O(n²)，mergesort 最壞 O(n log n) 但要 O(n) 空間，heapsort 兩者兼得。

**那為什麼標準庫不直接用它？** 因為它**存取記憶體是跳躍的**（parent/child 索引 `2i+1`、`2i+2` 到處跳），對 CPU 快取極不友善，常數因子大，實測往往比 quicksort 慢 2～3 倍。所以它多半是當「保底」——像 introsort 裡偵測到 quicksort 退化時的後備方案。

**heapsort 不穩定**：sift-down 的長距離交換會打亂相同鍵值的順序。

## 線性排序：跳出 n log n 下界

當元素不是「任意可比較物」而是**範圍有限的整數**時，可以不靠比較，突破 `Ω(n log n)`。

### Counting sort（計數排序）

統計每個值出現幾次，再依序輸出。時間 **O(n + k)**，`k` 是值域大小。

- **條件**：值域 `k` 不能太大。排 0～100 的成績很棒；排 0～10⁹ 的整數就慘了——要開 10 億大小的計數陣列，空間爆炸。
- 通常做成**穩定**版本（用前綴和決定輸出位置，從後往前放），因此可當 radix sort 的子程序。

```python
def counting_sort(arr, k):   # 值域 [0, k]
    count = [0] * (k + 1)
    for x in arr:
        count[x] += 1
    res = []
    for v in range(k + 1):
        res.extend([v] * count[v])
    return res
```

### Radix sort（基數排序）

從最低位到最高位，**逐位**用穩定的 counting sort 排。時間 **O(d·(n + k))**，`d` 是位數、`k` 是每位的基數（十進位是 10）。

- **條件**：適合**固定長度**的整數或字串（如 32 位元整數、等長字串）。
- 關鍵是**每一輪都必須用穩定排序**，否則低位排好的順序會被高位打亂。
- 當 `d`（位數）是常數、值域固定時，radix 是「線性排序」，能勝過 n log n。但若 `d` 很大（例如要排任意精度大數），優勢就消失。

**面試陷阱**：有人會說「radix sort 是 O(n)，比 quicksort 快」——這是誤導。它是 `O(d·n)`，`d` 是常數才線性；而且需要額外空間、只適用特定資料型別。面試官問「線性排序」多半是想聽你講**它的適用條件與限制**，而不是背複雜度。

## 何時用哪個：決策邏輯

複雜度表只是起點，真正的能力是**根據場景選對工具**：

- **一般泛用、追求平均最快** → quicksort（配隨機或 median-of-three pivot）。這也是為什麼多數語言的「排原始型別」預設用它的變體。
- **需要穩定排序**（多鍵排序、要保留原順序）→ mergesort / Timsort。Java 對物件排序、Python `sorted` 都保證穩定就是這原因。
- **需要最壞 O(n log n) 保證又不能用額外空間**（即時系統、對延遲敏感、記憶體極省）→ heapsort。
- **資料塞不進記憶體** → 外部排序，用 mergesort 的多路合併。
- **值域小的整數 / 固定長度鍵** → counting / radix，能壓到線性。

### firmware / 記憶體受限的取捨

在 firmware、嵌入式、bootloader 這類場景，記憶體是稀缺資源，遞迴堆疊也可能受限，選擇邏輯跟跑在大 RAM 伺服器上完全不同：

- **mergesort 的 O(n) 緩衝區可能直接不可行**——RAM 只有幾 KB 時，多一份輸入等量的複製是奢侈。
- **quicksort 的遞迴深度**在最壞情況會爆堆疊（嵌入式的 stack 往往只有幾 KB）；就算用，也要**改成尾遞迴 / 迴圈 + 先遞迴較小段**來限制深度到 O(log n)，或乾脆避開。
- **heapsort 常是嵌入式的好選擇**：O(1) 額外空間、無遞迴、最壞有保證、行為可預測（deterministic）——在意「最壞情況延遲上限」的即時系統特別看重這點，寧可平均慢一點也要沒有意外。
- 資料量很小（幾十個元素）時，**insertion sort** 反而最好：常數極小、in-place、穩定、對接近有序的資料接近 O(n)。這也是為什麼 introsort/Timsort 在子問題夠小時會**切換成 insertion sort**。

### 為什麼標準庫用 introsort / Timsort

把上面的取捨串起來就懂了：沒有單一演算法在所有維度都最好，所以標準庫用**混合策略**取各家之長：

- **introsort**（C++ `std::sort`）= quicksort（平均快）+ 偵測退化就轉 heapsort（保證最壞 n log n）+ 小陣列用 insertion sort（常數小）。
- **Timsort**（Python、Java 物件排序）= mergesort（穩定）+ 利用現實資料的已排序 run 加速 + 小段用 insertion sort。

面試若問「你會怎麼實作一個通用排序庫」，答案就是「不會只用一種」——這種混合思路本身就是加分點。

## 陷阱整理（面試自查）

1. **quicksort 對已排序輸入 + 固定 pivot = O(n²)**，還可能爆堆疊。務必講得出隨機化 / median-of-three / introsort 的補救。
2. **穩定性由細節決定**：merge 用 `<=` 是穩定、`<` 是不穩定；quicksort/heapsort 天生不穩定。被問「這重要嗎」要能舉多鍵排序的例子。
3. **「線性排序更快」是有條件的**：radix 是 `O(d·n)`、counting 需值域小，別無腦說它們贏 quicksort。
4. **空間別漏算**：mergesort O(n)、quicksort 的遞迴堆疊 O(log n)（最壞 O(n)）、heapsort O(1)。
5. **複雜度相同 ≠ 實際一樣快**：quick/merge/heap 都是 O(n log n)，但常數與快取行為差很多，quicksort 實測通常最快、heapsort 最慢。

## 相關 LeetCode 題目

| 題號 | 題目 | 考點 |
|------|------|------|
| 912 | Sort an Array | 手寫排序（quick / merge / heap 擇一，注意避開最壞情況） |
| 215 | Kth Largest Element | **quickselect**：quicksort 的 partition 思路，平均 O(n) 找第 k 大 |

**LeetCode 215 特別值得練**：它用 quicksort 的 partition，但每次只遞迴**一邊**（第 k 大落在的那半），平均 **O(n)** 就能找到第 k 大，不用整個排好。這是 partition 觀念的延伸應用，面試極高頻，能同時展示你對 quicksort 內部的理解。

## 一句話總結

排序面試考的不是背複雜度表，而是**取捨**：quicksort 平均最快但要防最壞、mergesort 穩定但吃空間、heapsort 省空間但慢又不穩定，而 counting/radix 只在特定條件下才能突破 n log n。能講清楚每個選擇背後的「為什麼」——尤其在 firmware 記憶體受限下該怎麼選——才是這關真正在測的東西。
