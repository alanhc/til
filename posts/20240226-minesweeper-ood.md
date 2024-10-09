---
title: 20240226-minesweeper-ood
date: 2024-02-26
tags:
  - object_oriented_design
updated: 2024-02-26
up:
  - "[[ood]]"
---
## Question
踩地雷遊戲，玩家直到整個盤都探索完畢，玩家點選後如果是炸彈就輸掉，若是空白，消除所有鄰近空白及數字
## Solution
- focus key idea+structure out
### Design:Cell
- enum
### Design:Board
- init, flip
### Design: Game
- host game state
### Algorithm
#### placing the bomb
#### setting number cells
#### expanding a Blank Region


## Ref
