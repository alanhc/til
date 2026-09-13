---
title: 20240217-jigsaw-ood
date: 2024-02-17
tags:
  - object_oriented_design
updated: 2024-02-17
up:
  - "[[ood]]"
---
## Question
打造一個拼圖遊戲，設計資料結構以及解釋如何破解這個拼圖的演算法。你可以假設有一個fitsWith()，他可以檢查兩個拼圖是否可以拼在一起。

## Solution
- 我們需要針對每一片拼圖儲存位置，可能有兩種儲存情況
	- 絕對位置：(x,y)
	- 相對位置：還不知道在哪，但知道A在B旁邊
- 主要Class: Puzzle, Piece, Edge
- 形狀(shape): inner, outer, flat
- edge的方向: left, right, top, down
- Puzzle 會有個很多piece的list
- Piece 會有個hashtable(orientation=>edge)，有可能會rotate piece，所以hash有可能會變
### Algorithm to Solve the Puzzle
- 要可以rotate嘗試是否可以塞到角落
## Ref
