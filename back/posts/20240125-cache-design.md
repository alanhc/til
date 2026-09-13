---
title: 20240125-cache-design
date: 2024-01-25
tags:
  - system_design
updated: 2024-01-25
up:
  - "[[system design]]"
---
## Question
設計一個簡單搜尋引擎的webserver，假設系統有100台機器負責回應queries，有個昂貴的function，processSearch(string query)，機器的選擇是隨機的，同一台機器回應可能會不一樣，請設計最相關queries的caching機制，請解釋當資料改變時如何更新cache

## Solutions
與面試官討論假設
### Assumptions
沒有最正確的答案
- 所有的query 發生在機器最初呼叫時
- cache的queries要有百萬等級
- 在機器間呼叫要相對快
- 結果是order list，並且有50字以內title及200字summary
- 最熱門的會極端熱門，而且隨時都應該在cache
### System Requirements
- 根據key有效檢索
- 過期舊資料應該被刪除
### Step 1 design a cache for a single system
如何有效根據key新增及刪除資料？
- lined list 可以有效快速刪除特定節點、限制長度
- hashtable可以有效找尋data
使用hashmap map query 到特定node
### Step 2 Expand to many machines
#### Option 1: Each machine has its own cache
- Pros
	- 相對快、因為沒有machine-to-machine call
- Cons
	- 如果有很多重複的query會很沒有效率
#### Option 2: Each machine has a copy of the cache
- Pros
	- 在cache一定會找得到
- Cons
	- 更新、佔用空間大、cache總數會較小
#### Option 3: Each machine stores a segment of the cache
根據 `hash(query)%N`
- Pros
	- 相對可儲存多
- Cons
	- 增加machine-to-machine call
### Step 3 Updating results when contents change
數量大、太熱門會需要時間快取或按照需求快取(和interviewer討論)
確認什麼時候資料會怎麼改變
1. URL 裡面內容 改變
2. 根據page ranking改變
3. 根據特定query改變
1,2 可以使用hash table，根據特定URL cache query
資料不需同步的話，可以根據時間爬取
3 可以再快取裡面使用 auto-matic time out，只cache特定時間，否則timeout，可以確保資料定時更新
### Step 4: Further Enhancements
轉送情形可以在中間節點cache
重新設計架構，不是隨機導流，而是使用hash
導入資料time out機制，刪除過久資料
