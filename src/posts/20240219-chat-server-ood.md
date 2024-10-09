---
title: 20240219-chat-server-ood
date: 2024-02-19
tags:
  - object_oriented_design
updated: 2024-02-19
up:
  - "[[ood]]"
---
## Question
- 請解釋你會怎麼設計一個chat server，請說明你會怎麼設計Backend Component的細節、Class及Method，可能需要解決最困難的問題是什麼
## Solution
- 這問題很大，一開始要scope problem，一開始建議從廣下手，但focus可以再inerview完成的部分
- focus 使用者管理（新增、建立對話、更新狀態）
- 先不管網路、資料怎麼傳送給client等問題
- 要加入聯絡人，要兩方都是才是，支援群組聊天、一對一私人對話，不考慮語、音通話或檔案傳輸
### What specific action does it need to support?
- 與interviewer討論，for example:
	- singing online and offline
	- 加入request(sending, accepting and rejeccting)
	- 更新狀態
	- 建立private 及群組訊息
	- 在private及群組對話加入訊息
### What can we learn about these requirements?
- 我們需要有使用者、新增request狀態、線上狀態、訊息
### What are the core components of the system?
- 使用database永久儲存資料，SQL很好，如果要scalability，可以使用BigTable之類
- client-server溝通可以使用XML，因為人跟機器可讀，但他不是最好壓縮過的格式
- 資料可能被切分在不同機器，為了避免single point of failure，資料會複製好幾份在不同機器
### What are the key objects and methods
- key objects, includes users, conversations, status message
	- UserManager
		- userById: map(int=>User)
		- userByAccountName: map(string=>User)
		- onlineUsers: map(int=>User)
		- addUser()
		- approveAddRequest()
		- rejectAddRequest()
		- iserSignedOn() 
		- iserSignedOff()
### What problems would be the hardest to solve(or the most interesting)?
- 可能會interviewer討論以下問題
- Q1: How do we know If someone is online--I mean, really know?
	- 有可能使用者忘記登出，定時去ping client看是否還在
- Q2: How do we deal with conflicting information
	- 有些存databse，有些存電腦的memory，如果有些out of sync怎麼辦？哪個才正確？
- Q3: How do we make our server scale?
	- 如何設計可以擴展的系統，真實世界資料可能要拆分在不同機器，怎麼處理不同步資料



## Ref
