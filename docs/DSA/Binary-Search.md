---
sidebar_label: 二分搜尋 Binary Search
---

# 二分搜尋（Binary Search）

**二分搜尋（Binary Search）** 是「每次把搜尋範圍砍一半」的技巧，在有序資料上把 O(n) 的線性搜尋降到 **O(log n)**。概念人人會講，但真正在面試白板上寫對的人不多——因為它的難不在主概念，而在**邊界處理**。off-by-one、無窮迴圈、`lo`/`hi` 該不該加減一，這些細節才是它真正考的東西。

這篇不只講「怎麼找一個數字」，而是把三件事講清楚：一個不會寫錯的模板、兩個最容易混淆的變體（lower_bound / upper_bound），以及進階的「在答案空間二分」——後者是 Google 高頻進階題的核心套路。

## 為什麼二分搜尋是面試常客

它是那種「五分鐘講完概念，但要你當場寫出零 bug 的版本」的題目。面試官考的往往不是「你知不知道二分搜尋」，而是：

- 你能不能把**迴圈不變式（loop invariant）**講清楚，而不是靠試誤湊出邊界？
- 你知不知道 `mid = (lo + hi) / 2` 在大陣列上會 **整數溢位（integer overflow）**？在 firmware / 系統程式（C/C++、32 位元甚至更窄的型別）這是真的會發生的 bug。
- 你能不能把一個看起來不像二分搜尋的最佳化問題，轉成「可行性判定 + 二分」？

換句話說，二分搜尋是檢驗「你寫程式嚴不嚴謹」的試金石。

## 基本二分：在有序陣列找一個目標

最單純的版本：陣列 `nums` 已排序，找 `target` 的索引，找不到回傳 `-1`。

```python
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1      # 閉區間 [lo, hi]
    while lo <= hi:
        mid = lo + (hi - lo) // 2  # 避免 overflow
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

這裡有兩個必須講清楚的關鍵，面試官很愛追問。

### 為什麼是 `mid = lo + (hi - lo) // 2`？

數學上它等於 `(lo + hi) // 2`，但寫法不同。`lo + hi` 在 `lo`、`hi` 都很大時可能超過整數上限而溢位——在 C/C++ 用 `int`（通常 32 位元，上限約 21 億）時，兩個十億級索引相加就爆了。這正是 2006 年 Google 一位工程師公開承認「幾乎所有二分搜尋實作都有的 bug」的著名案例（Java 標準庫的 `Arrays.binarySearch` 就中過）。

`lo + (hi - lo) // 2` 先算差值 `hi - lo`（一定 `≤ hi`，不會溢位），再加回 `lo`，數學等價但永遠不溢位。Python 整數無上限，不受影響，但**面試官問的是你懂不懂底層**，而在 firmware 這種寫 C 的場景，這是真 bug，一定要用這個寫法並能解釋原因。

### 為什麼是 `lo <= hi` 而不是 `lo < hi`？

這取決於你的**區間定義**，也就是迴圈不變式。上面用的是**閉區間 `[lo, hi]`**：`lo` 和 `hi` 都是還沒排除、仍可能是答案的位置。

- 既然 `hi` 本身是候選，當 `lo == hi`（區間剩一個元素）時還必須檢查它，所以條件是 `lo <= hi`。
- 排除某個位置時，因為是閉區間，要用 `mid + 1` / `mid - 1` 跳過已經檢查過的 `mid`，否則 `mid` 沒被排除掉，可能無窮迴圈。

一句話記住不變式：**「答案如果存在，一定在 `[lo, hi]` 之內」**。每次迴圈都維持這個性質，邊界就不會錯。只要你能對面試官複述這句話並解釋每一步怎麼維持它，就不會靠背。

## 邊界變體：lower_bound 與 upper_bound

這是二分搜尋**最容易寫錯**的地方，也是最常被考的地方。當陣列有重複元素，或找不到 target 時你想知道「它該插在哪」，就需要這兩個變體：

- **lower_bound**：第一個 **`≥ target`** 的位置（C++ `std::lower_bound`）。
- **upper_bound**：第一個 **`> target`** 的位置（C++ `std::upper_bound`）。

兩者都回傳「插入點」——把 target 插進去仍保持有序的最左位置。這裡我改用**半開區間 `[lo, hi)` + `lo < hi`** 的模板，它天生適合處理「找邊界」，而且不需要處理 `mid - 1`：

```python
def lower_bound(nums, target):
    """第一個 >= target 的 index；全部都 < target 時回傳 len(nums)"""
    lo, hi = 0, len(nums)          # 半開區間 [lo, hi)，注意 hi = len
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] < target:     # mid 太小，答案在右邊
            lo = mid + 1
        else:                      # nums[mid] >= target，mid 可能就是答案
            hi = mid               # 收縮但保留 mid，所以不是 mid - 1
    return lo

def upper_bound(nums, target):
    """第一個 > target 的 index"""
    lo, hi = 0, len(nums)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] <= target:    # 唯一差別：<= 而不是 <
            lo = mid + 1
        else:
            hi = mid
    return lo
```

**lower_bound 和 upper_bound 的程式碼只差一個符號**（`<` vs `<=`），這是最漂亮也最容易記混的地方。直覺：

- lower_bound 想「跳過所有 `< target` 的」，所以 `nums[mid] < target` 時往右。
- upper_bound 想「跳過所有 `<= target` 的（連等於也跳過）」，所以 `nums[mid] <= target` 時往右。

半開區間版本的不變式：**`[0, lo)` 全部不滿足條件，`[hi, len)` 全部滿足條件**，迴圈結束時 `lo == hi` 就是那條分界線。因為 `hi` 是「開」的（不含），收縮時寫 `hi = mid` 而不是 `mid - 1`——`mid` 本身還沒被排除，只是變成新的「開」邊界。

有了這兩個，很多問題迎刃而解：某值出現的次數 = `upper_bound - lower_bound`；`target` 是否存在 = `lower_bound` 指到的值是不是 `target`。

## 兩種模板的取捨

面試時你會看到兩派模板，別混用：

| 模板 | 區間 | 迴圈條件 | 收縮方式 | 適合 |
|------|------|----------|----------|------|
| 閉區間 `[lo, hi]` | `hi = len-1` | `lo <= hi` | `lo = mid+1` / `hi = mid-1` | 找「剛好等於」某值 |
| 半開 `[lo, hi)` | `hi = len` | `lo < hi` | `lo = mid+1` / `hi = mid` | 找邊界、插入點、lower/upper_bound |

**建議：挑一個練到爛熟。** 我的建議是主力用半開區間版本，因為它能統一處理「找邊界」這類最容易錯的情況，而「找剛好等於」也能用 lower_bound 找到後再檢查一次值。面試當下不要臨時發明模板，用你練過幾十次、閉著眼睛都不會錯的那個。

## 進階：在「答案空間」二分

這是二分搜尋從「查表工具」升級成「解題武器」的關鍵，也是 **Google 面試的高頻進階套路**。核心洞察：

> 二分搜尋不一定要作用在「陣列」上。只要你的答案落在一個範圍內，而且答案有**單調性**（小於某臨界值都不行、大於等於就都行，或反過來），你就能對「答案本身」二分。

這把一個**最佳化問題**（求最小/最大值）轉成一連串**可行性判定問題**（給定一個值，可不可行？）。判定通常好寫得多。

### 模式：「最小化最大值」/「最大化最小值」

看到題目描述長這樣，就要想到答案空間二分：

- 「在 D 天內看完所有書，求**最小**的每天閱讀速度」
- 「把陣列分成 k 段，求**最小的最大段和**」
- 「切木頭 / 分配資源，讓**最大負載最小**」

以 **LeetCode 875 (Koko Eating Bananas)** 為例：Koko 每小時吃 `k` 根香蕉，要在 `h` 小時內吃完所有堆，求最小的 `k`。

關鍵觀察：**`k` 越大，吃完需要的時間越短，這是單調的**。所以「能不能在 `h` 小時內吃完」對 `k` 而言有一條分界線——小於某個 `k` 都不行，大於等於都行。這正是 lower_bound 的形狀：找**第一個「可行」的 `k`**。

```python
import math

def min_eating_speed(piles, h):
    def can_finish(k):                       # 可行性判定
        return sum(math.ceil(p / k) for p in piles) <= h

    lo, hi = 1, max(piles)                   # k 的答案空間
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if can_finish(mid):
            hi = mid                         # mid 可行，但也許還能更小
        else:
            lo = mid + 1                     # mid 太慢，加大
    return lo
```

注意這個結構跟 lower_bound **一模一樣**：把 `nums[mid] < target` 換成 `not can_finish(mid)`。你要做的只是想清楚兩件事：

1. **答案空間的上下界**是什麼？（這裡 `k` 最小 1，最大 = 最大那堆，再大也沒意義。）
2. **判定函式**怎麼寫，以及單調性方向對不對？（`k` 增加 → 時間減少 → 從某點起都可行。）

**LeetCode 410 (Split Array Largest Sum)** 是同一個模子的更難版本：把陣列分成 `k` 段使「最大段和」最小。答案空間是 `[max(nums), sum(nums)]`，判定函式是「若限制每段和不超過 `x`，貪婪地切，需要幾段？`≤ k` 就可行」。認出模式後，難題也變成填空。

複雜度：外層二分 `O(log(答案範圍))`，每次判定掃一遍 `O(n)`，總共 `O(n log(range))`——非常划算。

**面試陷阱**：很多人卡在「這題跟排序陣列沒關係，怎麼二分？」——要練到看到「最小化最大值 / 最大化最小值 / 求最小的可行值」就反射性地問自己「答案有沒有單調性？」。這是能不能解出這類題的分水嶺。

## 旋轉排序陣列

**LeetCode 33 (Search in Rotated Sorted Array)** 是另一種經典變體，考「就算整體無序，只要局部有序就能二分」。

一個排序陣列在某點旋轉後（例如 `[4,5,6,7,0,1,2]`），不再整體有序，但**任意切一刀，`mid` 左右至少有一半是完全有序的**。利用這點判斷 target 在哪一半：

```python
def search_rotated(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:            # 左半 [lo, mid] 有序
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1                 # target 在有序的左半
            else:
                lo = mid + 1
        else:                                # 右半 [mid, hi] 有序
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1                 # target 在有序的右半
            else:
                hi = mid - 1
    return -1
```

**陷阱**：判斷哪一半有序時，`nums[lo] <= nums[mid]` 的 `=` 不能漏（`mid == lo` 時退化，等號讓左半仍算「有序」）。還有一個常見追問：**陣列有重複元素怎麼辦？**（LeetCode 81）——當 `nums[lo] == nums[mid] == nums[hi]` 時無法判斷哪半有序，只能 `lo += 1` 退化成線性，最壞 O(n)。面試官問這個是想看你有沒有意識到重複會破壞單調性假設。

## 常見錯誤清單（面試自查）

寫完二分搜尋，用這幾點快速檢查：

1. **無窮迴圈**：閉區間卻用 `hi = mid`（沒減一），或半開區間卻用 `hi = mid - 1`。收縮方式必須配合區間定義。
2. **off-by-one**：`hi` 初值該是 `len` 還是 `len - 1`？取決於半開還是閉區間，別混。
3. **overflow**：C/C++ 一律 `lo + (hi - lo) / 2`，不要 `(lo + hi) / 2`。
4. **邊界收斂性**：確認每次迴圈區間**嚴格縮小**（`lo` 增或 `hi` 減），否則可能卡住。
5. **講得出不變式**：如果你只能靠「試幾個小案例看看對不對」來調邊界，代表你還沒真懂——面試官會要你解釋為什麼，講不出來就露餡。

## 相關 LeetCode 題目

| 題號 | 題目 | 考點 |
|------|------|------|
| 704 | Binary Search | 最基本的模板 |
| 35 | Search Insert Position | lower_bound（找插入點） |
| 34 | Find First and Last Position | lower_bound + upper_bound 組合 |
| 33 | Search in Rotated Sorted Array | 旋轉陣列、局部有序 |
| 875 | Koko Eating Bananas | 答案空間二分（最小化速度） |
| 410 | Split Array Largest Sum | 答案空間二分（最小化最大值） |

## 一句話總結

二分搜尋的難度不在概念，而在紀律：**先定義區間與不變式，再讓每一步維持它**。基本查找練到零 bug，記熟 lower_bound / upper_bound 只差一個符號，最後把「最小化最大值」這類最佳化問題認出來、轉成可行性判定——這三層練透，二分搜尋這關就穩了。
