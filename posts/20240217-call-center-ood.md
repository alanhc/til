---
title: 20240217-call-center-ood
date: 2024-02-17
tags:
  - object_oriented_design
updated: 2024-02-17
up:
  - "[[ood]]"
---
## Question
有一個有三種level員工的call center，respondent, manager, director。當電話進來時，要assign給空閒的respondent，如果他不能回答，必須轉介給manager，也不行就往上給director，設計一個給這問題的class及資料結構，實作一個dispathchCall()指派電話給低一個可用的員工
## solution
- OOD有很多方式可以實作，跟面試官討論，trade off，保持彈性、可維護性設計。
- Call代表一則通話，並且call有最小的rank而且被指定給可以處理的第一個員工
- Employee 是superclass，且是一個abstract類別，不應該直接實例化
- respondent, manager, director可以extend Employee類別
## Ref
