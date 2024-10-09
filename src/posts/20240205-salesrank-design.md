---
title: 20240205-salesrank-design
date: 2024-02-05
tags:
  - system_design
updated: 2024-02-05
up:
  - "[[system design]]"
---
## Question
設計一個有多類別的產品ranking網站
## Solutions
### Step 1 Scope the problem
- 只跟問題相關、而不是整個系統，包含前端及購買component
- 定義什麼是salesrank，包含前天、上週、上個月
- 假設有多個類別，且不會有子類別
### Step 2 Make Reasonable Assumptions
- 假設不用更新全部資料
- 熱門商品數字要精確、不熱門的可以不用那麼精確
- 熱門資料要每小時更新，其餘的超過7天不用很精確
### Step 3 Draw the Major Component
```mermaid
graph LR
A(Purchase System) --> |orders added to db| B(Database)
B(Database) --> |sort| C(Salesrank Data)
C(Salesrank Data) --> D(Frontend)
A(Purchase System) --> B(Database)
C(Salesrank Data) --> D(Frontend) 
```
### Step 4 Identity the Key Issues
- 分析非常昂貴
	- 若把資料全部存在一個表，每天會區要更新，所以可以拆分成ID+日期
	- example

| Prod ID | Total | Sun | Mon |
| ---- | ---- | ---- | ---- |
|  |  |  |  |
|  |  |  |  |

| Prod ID | Cat ID |
| --- | --- |
|  |  |
- 資料庫被頻繁寫入
	- 可能會需要batch write，在之前可能先cache在某種memory，但要考慮是否能放進hash table，假設有1000萬筆資料...
	- 注意更新sales rank與資料寫入的時間，確保不會有偏差
- join 查詢非常貴
	- 與其先將資料裡每個類別sort過再join，會花很多時間，不如一開始使用資料格式

| Prod ID | Cat | Total | Sun | Mon |
| ---- | ---- | ---- | ---- | ---- |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
- 資料庫查詢很昂貴
	- 如果write/search很昂貴可以使用類似log file像是map reduce
		- 每個query使用檔案及資料夾分類
#### Follower up
- 你如何會碰到接下來的bottleneck，如何解釋？
- 如果有子類別？
- 如果資料要很準確，達到30min內都是精確的
