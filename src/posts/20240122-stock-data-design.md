---
title: 20240122-stock-data
date: 2024-01-22
tags:
  - system_design
updated: 2024-01-22
up:
  - "[[system design]]"
---
## Question
設計一個可以有1000 client 可以取得最後的開高收低，已經有資料、可以自行決定儲存，要怎麼設計client說明幾種不同的方法及為甚麼使用，可以用任意技術及可以選擇任意分散機制
## Solutions
先考慮以下幾點
- Client Ease of use: 對顧客使用簡單且有用
- Ease for Our selves: 對我們來說好實作且好維護
- Flexibility for future demand: 如何根據真實世界需求彈性調整
- Scalability and Efficiency: 注意解決有效性 
### Propsal 1 file
使用簡單text file，且讓顧客透過FTP下載
- Pros
	- 簡單好維護、方便閱讀、備份
- Cons
	- 搜尋、排序困難
	- 新增資料會break paring mechanism
### Propsal 2 SQL
- Pros
	- 方便查詢且有效率
	- rolling back, backing up, security 已經有，不用重新造輪子
	- 方便整合現有應用，因為SQL幾乎是軟體開發標準
- Cons
	- 笨重，會複雜化系統
	- 人類難閱讀
	- 對於client要注意、不該給的權限、使否執行昂貴、沒效率的queries
### Propsal 3 XML
- Pros
	- easy to distirbute, 對機器、人類好閱讀
	- 大部分程式都支援XML
	- 很好新增 插入
	- 有很多工具可以back up 
- Cons
	- 執行query 需要取得全部data
	- client 會有全部資料，會沒有效率
沒有正確的答案，雖然看起來file的做法最不好，每種方法都有trade off


## Ref
