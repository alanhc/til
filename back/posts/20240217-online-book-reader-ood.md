---
title: 20240217-online-book-reader-ood
date: 2024-02-17
tags:
  - object_oriented_design
updated: 2024-02-17
up:
  - "[[ood]]"
---
## Question
設計線上書本閱讀器的資料結構
## Solution
- 因為問題沒解釋很清楚，我們假設提供以下功能
	- 用戶帳戶建立、擴增
	- 搜尋資料庫的書
	- 看書
	- 同一時間只可以有一個線上使用者
	- 這個使用者指只會有一本acitve的書
- 有可能會有
	- User/Book/Library
	- get/set/update

## Ref
