---
title: 20240125-web_srawler_design
date: 2024-01-25
tags:
  - system_design
updated: 2024-01-25
up:
  - "[[system design]]"
---
## Question
再設計爬蟲時，如何避免無限迴圈


## Solutions
問題：無限迴圈何時發生？因為我們將鏈結化作graph，所以有可能有無限迴圈，有可能使用`hashtable[v]=true`及BFS ，但v怎麼設定？
但遇到URL parameters可能會有問題，比如example.com?pid=google及example.com?pid=apple可能是不同，但example.com?foo=hi 跟example.com是相同網頁
根據內容？使用 相似度，首先爬取children，計算子頁相似度極優先度，如下
1. 開啟網頁、建立page signature根據 頁面、url
2. query database看簽名是否最近被爬取過
3. 如果有，新增到db到low priority
4. 如果沒有，爬取網頁並新增資料庫
