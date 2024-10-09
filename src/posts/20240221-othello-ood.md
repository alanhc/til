---
title: 20240221-othello-ood
date: 2024-02-21
tags:
  - object_oriented_design
updated: 2024-02-21
up:
  - "[[ood]]"
---
## Question
- 設計黑白棋的OOD，黑白棋是如果周遭（上下左右）被圍起來就更換中間（被包圍）顏色，到一方無法下任何棋結束。
## Solution
- core object: game, board, pieces, players
### Shold BlackPiece and WhitePiece be classes?
- 因為棋會一直被翻轉，有一個統一Piece Class可能比較好
### Do we need separate Board and Game classes?
- Pros
	- 邏輯上分開board跟game
- Cons
	- 需要額外layer
## Who keeps Score?
- 可能可以使用Group、Piece、Board group
- 我們暫時使用board存，這樣分數可以由Board分組
## Should Game be a Singleton class?
- Singleton 好處是所有人可呼叫，而不用每次都pass ref，但只能被初始化一次，與interviewer討論是否可以這樣做
## Ref
