---
sidebar_label: 單調堆疊 Monotonic Stack
---

# 單調堆疊（Monotonic Stack）

**Monotonic stack(單調堆疊)** 是一種使用技巧,不是新的資料結構——它就是普通的 stack,只是在使用時額外維持一個規則:stack 裡的元素從底到頂保持單調遞增或單調遞減。每當要 push 新元素時,先把所有會破壞單調性的元素 pop 掉,再放入新元素。

## 它解決什麼問題

它最經典的用途是回答這類問題:「對陣列中的每個元素,找出它右邊(或左邊)第一個比它大(或小)的元素」——也就是所謂的 **Next Greater Element / Next Smaller Element** 問題。

用暴力法,每個元素都要往後掃描,最壞是 O(n²)。用單調堆疊,每個元素只會被 push 一次、pop 一次,整體是 **O(n)**。這就是它重要的核心原因:把一大類看似需要平方時間的問題降到線性時間。

## 直覺理解

以「找右邊第一個更大的元素」為例,維持一個遞減的 stack:

```python
def next_greater(nums):
    res = [-1] * len(nums)
    stack = []  # 存 index,對應值由底到頂遞減
    for i, x in enumerate(nums):
        while stack and nums[stack[-1]] < x:
            res[stack.pop()] = x   # x 就是被 pop 元素的答案
            # 被 pop 的元素再也不需要了——x 比它大又比它新,
            # 之後的查詢用 x 就夠,這是 O(n) 的關鍵
        stack.append(i)
    return res
```

直覺是:stack 裡存的是「還在等待答案的元素」。當一個更大的數字出現,它就是 stack 頂那些較小元素的答案,可以把它們一一結案。被 pop 掉的元素永遠不用再回來,所以總工作量是線性的。

## 為什麼重要

第一,**複雜度的躍升**:O(n²) → O(n) 不是小優化,在大資料量下是能不能跑完的差別。

第二,**它是一整類難題的鑰匙**。很多知名的難題本質上都是單調堆疊問題,例如 Largest Rectangle in Histogram(直方圖最大矩形)、Trapping Rain Water(接雨水)、Daily Temperatures、Stock Span、Remove K Digits、Sliding Window Maximum(用它的變體 monotonic deque)。這些題目表面看起來毫無關係,但一旦你認出「每個元素在找它附近第一個更高/更低的邊界」這個模式,解法就自然浮現。

第三,**面試高頻**。它是那種「不知道就幾乎想不出來,知道了就變簡單」的技巧,所以在演算法面試中出現率很高,是值得專門練熟的模式。

一個實用的辨識訊號:題目裡出現「下一個更大」「第一個更小」「以某元素為最小值的區間」「能看到多遠」這類描述時,十之八九就是單調堆疊(或單調佇列)的場景。