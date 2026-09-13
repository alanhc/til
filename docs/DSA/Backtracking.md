---
sidebar_label: 回溯 Backtracking
---

# 回溯（Backtracking）

**回溯（Backtracking）** 是一種系統化窮舉所有可能的方法：一步步做選擇往下探，走到底或走不通就**退回上一步、還原狀態，換另一個選擇再試**。它本質上是帶「撤銷」動作的 DFS，是解決「列出所有排列 / 組合 / 子集 / 路徑」這類題目的萬用框架。面試裡只要你認得出題目在要「**窮舉所有可能**」，幾乎都能套同一個模板。

## 核心：選擇 → 遞迴 → 撤銷

回溯的骨架永遠是這三個動作，缺一不可：

1. **做選擇**：把當前選項加進路徑（`path.append(x)`）。
2. **遞迴深入**：帶著這個選擇往下一層探索。
3. **撤銷選擇**：遞迴回來後，把剛剛的選項移除（`path.pop()`），還原到做選擇之前的狀態，好讓迴圈試下一個選項。

第 3 步「撤銷」是回溯的靈魂，也是名字的由來。它保證每次進入新分支時，狀態都是乾淨的——你在同一個 `path` 物件上做選擇又還原，等於在一棵**決策樹**上走遍每條路徑。

通用模板長這樣：

```python
def backtrack(path, choices):
    if is_solution(path):
        result.append(path[:])   # 存快照！path 之後還會被改
        return
    for choice in choices:
        # 做選擇
        path.append(choice)
        # 遞迴深入（choices 通常會依 choice 縮小）
        backtrack(path, next_choices(choices, choice))
        # 撤銷選擇
        path.pop()
```

有兩個容易錯的細節：

- **存答案要存快照** `path[:]`（或 `list(path)`）。因為 `path` 是同一個 list 一直被改，直接存參考的話，最後所有答案都會變成同一個（空的）list。
- **撤銷必須和做選擇一一對應**。若在遞迴前改了多個狀態（例如同時標記了棋盤的列、對角線），回來後每一個都要還原。

## 與 DFS 的關係

回溯就是 **DFS + 狀態還原**。差別在：

- 一般在「已建好的圖」上做 DFS，走過的節點是既有的。
- 回溯是在一棵**隱式的決策樹**上做 DFS——這棵樹不存在記憶體裡，而是由你「每一步能做哪些選擇」動態長出來的。走完一條分支就把選擇撤掉，回到父節點再長出下一條分支。

所以你會看到回溯的程式碼幾乎都是 DFS 遞迴，只是多了 `append` / `pop` 這對招式在維護「當前走到哪」。

## 剪枝：讓指數搜尋變可行

窮舉本質是指數級的，暴力走完整棵決策樹常常大到跑不動。**剪枝（Pruning）** 是回溯真正能用的關鍵：在探索途中發現「這條分支不可能通向合法解」，就**提早 return**，整片子樹連碰都不碰。

剪枝的效果可能非常巨大。以 N-queens 為例，8×8 棋盤若真的窮舉每格放不放，是 2⁶⁴ 種；就算限制每列一個皇后也有 8⁸；但加上「同行、同對角線不能有皇后」這個剪枝後，實際搜的分支少到瞬間可解。**同樣的框架，剪不剪枝差在能不能跑完。**

剪枝的常見形式：

- **合法性剪枝**：當前選擇會違反約束（皇后互相攻擊、和已超標）就不往下。
- **去重剪枝**：有重複元素時，跳過同一層裡重複的選項，避免產生重複答案。
- **順序剪枝**：規定選擇只能遞增（如組合題只往後選），天然避免 `[1,2]` 和 `[2,1]` 被當成兩種答案。

## 經典題示範

### 1. 全排列 Permutations（LeetCode 46）

給定不重複的陣列，回傳所有排列。

**思路**：每一層從「還沒用過」的數字裡挑一個。用一個 `used` 陣列標記哪些用過。因為排列講究順序，每一層都要能選到任何還沒用的數。

```python
def permute(nums):
    result = []
    used = [False] * len(nums)

    def backtrack(path):
        if len(path) == len(nums):
            result.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue          # 剪枝：用過的跳過
            used[i] = True        # 做選擇
            path.append(nums[i])
            backtrack(path)       # 遞迴
            path.pop()            # 撤銷
            used[i] = False       # 撤銷（used 也要還原）
    backtrack([])
    return result
```

共 n! 種排列，每種花 O(n) 複製，時間 O(n·n!)。注意 `used` 和 `path` 這兩個狀態都要成對地還原。

### 2. 組合 Combinations（LeetCode 77）

從 `1..n` 中選 `k` 個數的所有組合（不論順序）。

**思路**：組合和排列的關鍵差別是**不管順序**，`[1,2]` 和 `[2,1]` 算同一個。解法是規定「只能往後選」——用一個 `start` 參數，下一層只從 `start` 之後挑。這既是去重、也是剪枝。

```python
def combine(n, k):
    result = []

    def backtrack(start, path):
        if len(path) == k:
            result.append(path[:])
            return
        # 剪枝：剩下的數字不夠湊滿 k 個就不用試
        for i in range(start, n - (k - len(path)) + 2):
            path.append(i)
            backtrack(i + 1, path)   # 下一層從 i+1 開始，不回頭
            path.pop()
    backtrack(1, [])
    return result
```

那個迴圈上界 `n - (k - len(path)) + 2` 是剪枝：如果剩下的數字連湊滿 `k` 個都不夠，這個 `start` 就不必試了。

### 3. 子集 Subsets（LeetCode 78）

回傳陣列的所有子集（冪集）。

**思路**：子集不限長度，所以**每個節點都是一個合法答案**（一路上經過的 `path` 都要收集，不只在葉節點）。一樣用 `start` 保證只往後選、避免重複。

```python
def subsets(nums):
    result = []

    def backtrack(start, path):
        result.append(path[:])           # 每個節點都是答案
        for i in range(start, len(nums)):
            path.append(nums[i])         # 做選擇
            backtrack(i + 1, path)       # 下一層從 i+1 開始
            path.pop()                   # 撤銷
    backtrack(0, [])
    return result
```

共 2ⁿ 個子集（每個元素選或不選），所以是 O(2ⁿ)。

### 4. N 皇后 N-Queens（LeetCode 51）

在 N×N 棋盤放 N 個皇后，使彼此不能攻擊（不同行、不同列、不同對角線），回傳所有擺法。這是剪枝威力的代表題。

**思路**：一列放一個皇后（天然保證不同列），逐列往下擺。放之前檢查同一行、兩條對角線上有沒有別的皇后——這就是剪枝。用集合記錄被佔用的行與對角線，判斷是 O(1)。

- 同一「主對角線」上 `row - col` 相同；
- 同一「反對角線」上 `row + col` 相同。

```python
def solve_n_queens(n):
    result = []
    cols = set()          # 被佔用的行
    diag1 = set()         # row - col
    diag2 = set()         # row + col
    board = [-1] * n      # board[r] = 該列皇后所在的行

    def backtrack(row):
        if row == n:
            result.append(build(board, n))
            return
        for col in range(n):
            # 剪枝：這格會被攻擊就跳過
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            cols.add(col); diag1.add(row - col); diag2.add(row + col)
            board[row] = col
            backtrack(row + 1)
            # 撤銷：三個集合都要還原
            cols.remove(col); diag1.remove(row - col); diag2.remove(row + col)
    backtrack(0)
    return result

def build(board, n):
    return ['.' * c + 'Q' + '.' * (n - c - 1) for c in board]
```

這題完美示範了「做選擇 / 遞迴 / 撤銷」對三個狀態集合的成對操作，也示範剪枝把不可行的分支整片砍掉。

### 5. 電話號碼字母組合（LeetCode 17）

給像 `"23"` 的數字串，回傳所有可能的字母組合（2→abc、3→def⋯⋯）。

**思路**：這是最乾淨的回溯——第 `i` 層對應第 `i` 個數字，該層的選擇就是那個數字對應的幾個字母。走到字串長度就是一個答案。

```python
def letter_combinations(digits):
    if not digits:
        return []
    mapping = {'2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
               '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'}
    result = []

    def backtrack(index, path):
        if index == len(digits):
            result.append(''.join(path))
            return
        for ch in mapping[digits[index]]:
            path.append(ch)              # 做選擇
            backtrack(index + 1, path)   # 下一個數字
            path.pop()                   # 撤銷
    backtrack(0, [])
    return result
```

### 附帶：組合總和 Combination Sum（LeetCode 39）

給一組不重複的正整數和目標 `target`，每個數可**重複使用**，找出所有和為 `target` 的組合。

**思路**：和「組合」很像，但同一個數可以再選，所以遞迴時 `start` 傳的是 `i` 而不是 `i+1`（允許停在原地重選）。剪枝：當前總和已超過 `target` 就停。

```python
def combination_sum(candidates, target):
    result = []
    candidates.sort()        # 排序後可提早 break

    def backtrack(start, path, remain):
        if remain == 0:
            result.append(path[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remain:
                break               # 排序後，這個超了後面更大，整段剪掉
            path.append(candidates[i])
            backtrack(i, path, remain - candidates[i])   # 傳 i：可重選
            path.pop()
    backtrack(0, [], target)
    return result
```

## 複雜度：為何常是 O(N!) 或 O(2ⁿ)

回溯的複雜度直接反映決策樹的大小：

- **排列**型：第一層 n 種選、第二層 n-1 種⋯⋯共 **n!** 條路徑 → O(n·n!)。
- **子集 / 選或不選**型：每個元素兩種可能（選、不選），共 **2ⁿ** 條 → O(2ⁿ)（或 O(n·2ⁿ) 含複製）。
- **每格多選項**型（如電話號碼、N-queens）：接近 O(kⁿ)，k 是每層平均分支數。

這些都是指數或階乘級，本質上就是「答案本身就有指數個」——你要列出 2ⁿ 個子集，再快也逃不掉 O(2ⁿ)。剪枝不會改變最壞複雜度的上界，但能讓實際跑的分支大幅減少，是能不能在時限內跑完的關鍵。

## 什麼時候該改用 DP

回溯窮舉「所有解」；DP 求「一個最優值或方案數」。兩者常在同一題交界，判斷標準是：

- 題目要**列出所有具體解**（所有排列、所有路徑）→ 只能回溯，答案本來就有指數個。
- 題目只要**最大 / 最小 / 總數**這個「數字」，而且子問題會重複 → 改用 DP。硬用回溯會重複計算大量子問題而 TLE。

典型例子：coin change 若問「有幾種湊法」或「最少幾枚」，用回溯窮舉會超時，因為同一個「剩餘金額」子問題被反覆探索——這時記憶化 / DP 才是正解。反過來，「列出所有湊法的具體硬幣組合」就得回溯，因為要輸出每一組。

一個判斷口訣：**「求所有具體方案」用回溯，「求一個最優值/方案數且子問題重疊」用 DP。** 有時面試官會先問回溯版，再追問「如果只要數量呢」引導你轉 DP——這是很常見的進階提問。

## 面試角度：認出模式就套框架

回溯在面試裡的最大好處是**辨識度高、模板固定**。看到這些字眼，先想回溯：

- 「列出**所有**⋯⋯」「找出**全部**的組合 / 排列 / 子集 / 路徑」
- 「有哪些**可能**的方式」
- 需要**窮舉**再逐一驗證是否合法（如數獨、單詞搜索、括號生成）

認出後，把三步框架（選擇 → 遞迴 → 撤銷）默寫出來，再針對題目補三件事：**(1) 什麼是一個完整解（終止條件）、(2) 每一層有哪些選擇、(3) 哪些選擇可以剪枝**。把這三點對面試官講清楚，程式碼幾乎是照抄模板。這種「框架穩、變化在細節」的特性，讓回溯成為 CP 值很高的面試準備重點。

## LeetCode 對照

| 題號 | 題目 | 重點 |
|------|------|------|
| 46 | Permutations | 排列，用 `used` 標記 |
| 78 | Subsets | 子集，每個節點都是答案 |
| 77 | Combinations | 組合，用 `start` 去重 + 剪枝 |
| 51 | N-Queens | 剪枝威力，多狀態成對還原 |
| 17 | Letter Combinations of a Phone Number | 每層固定選項，最乾淨的模板 |
| 39 | Combination Sum | 可重複選，`start` 傳 `i` |
