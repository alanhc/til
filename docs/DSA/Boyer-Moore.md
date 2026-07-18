---
sidebar_label: Boyer-Moore 投票法
---

# Boyer-Moore 投票法（Majority Element）

**Boyer-Moore 投票法（Boyer-Moore Voting Algorithm）** 是一個用來找出陣列中「多數元素」（majority element，出現次數超過 n/2 的元素）的經典演算法，最大的優點是只需要 **O(n) 時間、O(1) 空間**，一次遍歷就能完成。

## 核心想法

把它想像成一場「打群架互相抵消」：不同陣營的人兩兩對消，如果某個陣營的人數超過總數的一半，最後場上剩下的一定是那個陣營的人。

## 運作方式

維護兩個變數：`candidate`（目前的候選人）和 `count`（票數）。遍歷陣列時：

1. 如果 `count == 0`，把當前元素設為新的 `candidate`
2. 如果當前元素等於 `candidate`，`count + 1`
3. 否則 `count - 1`（互相抵消）

遍歷結束後，`candidate` 就是多數元素（前提是多數元素確實存在）。

## 範例走一遍

以 `[2, 2, 1, 1, 1, 2, 2]` 為例：

| 元素 | candidate | count |
|------|-----------|-------|
| 2    | 2         | 1     |
| 2    | 2         | 2     |
| 1    | 2         | 1     |
| 1    | 2         | 0     |
| 1    | 1         | 1     |
| 2    | 1         | 0     |
| 2    | 2         | 1     |

最後 candidate = 2，正確。

## 程式碼（Python）

```python
def majority_element(nums):
    candidate, count = None, 0
    for num in nums:
        if count == 0:
            candidate = num
        count += 1 if num == candidate else -1
    return candidate
```

## 幾個重點

**為什麼正確？** 多數元素出現超過 n/2 次，就算它每次都和別的元素一對一抵消，抵消完後它還會有剩，所以最後存活的 candidate 必然是它。

**注意事項：** 如果題目沒保證多數元素存在，需要**第二次遍歷**驗證 candidate 的出現次數是否真的超過 n/2。

**經典題目：** LeetCode 169 (Majority Element)。進階版 LeetCode 229 (Majority Element II) 找出現超過 n/3 次的元素，用同樣思路維護兩個候選人即可。