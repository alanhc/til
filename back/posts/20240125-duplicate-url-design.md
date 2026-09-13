---
title: 20240125-duplicate-url-design
date: 2024-01-25
tags:
  - system_design
updated: 2024-01-25
up:
  - "[[system design]]"
---
## Question
如何儲存1000萬的url，每個字4 byte、頁面平均100字，這樣大約會有4TB


## Solutions

### Solution 1: Disk Storage
使用two pass
first pass: 將URL hash 儲存，分成 每個1G，共4000chunk，儲存URL u到`<x>.txt`
`<x>.txt where x = hash(u%4000)`
second pass: 讀入memory、建立hash table、尋找重複
### Solution 2: Multiple Machines
跟two pass一樣，只是在不同機器
- Pros
	- 可以平行處理，對大型資料效率佳
- Cons
	- 複雜、維護多個機器困難
