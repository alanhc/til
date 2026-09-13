---
title: 20220811-monorepo-development
date: 2022-08-11
tags:
  - frontend
  - monorepo
  - select
---

## Ref

前言
- LINE台灣用戶有2100萬
- LINE 跨國公司
正文
- 時間：2000年初
- 共享code，scale build system 及 version control 
- 使用公司：Google Facebook Microsoft Uber Airbnb Twitter
- Pros
    - code reuse：透過共享lib共享code
    - 簡化相依性管理：單一package.json，不容易造成版本衝突
    - 簡單重構：單一repo看得到整個架構
    - 跨團隊協作：靈活掌握，可以修改其他團隊code
- Cons
    - 權限控管：不能根據repo設定訪問權限
    - 預設設定會佔用空間：預設會下載整個專案，專案龐大會佔用開發者空間
- 障礙
    - Google monorepo 幾萬筆commit及80TB的monorepo
    - scale 版本控制軟體：2005年Google建構服務要10min. 2010年改進30s-1min
    - Scaling build software: 執行build及CI test會有問題


## 前言
> 許多網頁都有共用component，這些component不盡相同。

![](https://i.imgur.com/XqjBPCD.jpg)

## 為何要用monorepo?
現代的專案愈來愈龐大，一個品牌底下可能有很多不同的服務，然而服務間及服務間有許多功能是相似的，以前端來說，網頁組成大部分會寫成component的形式讓不同頁面可以共用，但不同服務呢，Monorepo就是解決這問題的好方法。

Monorepo的歷史可以追溯到2000年初期，為了解決不同專案間reuse code的概念誕生了讓專案維持在同一個codebase底下，不僅如此，單一的套件管理方式不易造成版本衝突，重構時也可以看到專案全貌針對問題彈性修改等好處，然而，這些好處同時，也可能違背最小權限原則的管理模式，較難根據repo設定訪問權限，由於專案建構時會一次建構整個專案，會造成時間及空間上的問題，對於版本控制也是一大問題，如Google的Monorepo每天處理上萬筆的commit及幾十TB的儲存空間，好的monorepo選擇也變得十分重要。
![](https://i.imgur.com/mtHvHZA.jpg)

單一codebase，共用component，單一共用的相依性

## 有哪些選擇?
nx turborepo rush bazel


https://en.wikipedia.org/wiki/Monorepo
https://circleci.com/blog/monorepo-dev-practices/
https://nx.dev/guides/why-monorepos
Monorepos - How the Pros Scale Huge Software Projects // Turborepo vs Nx: https://youtu.be/9iU_IE6vnJ8
https://www.robinwieruch.de/javascript-monorepos/
https://monorepo.tools/