---
title: 20240205-Deck-of-cards
date: 2024-02-15
tags:
  - object_oriented_design
updated: 2024-02-15
up:
  - "[[ood]]"
---
## Question
Deck of cards：設計一個給一副牌的generic資料結構，解釋如何設計black-jack(21點)資料結構的子類別

## Solution
- 首先跟面試關確認generic的定義，給Uno、pocker-like還是？
- 假設是poker card:
	- Suit
		- club, diamond, heart, spade
		- value
		- getValue()
		- getSuitFromValue()
	- Deck
		- `cards=[]`
		- shuffle()
		- remainintCards()
		- dealHand()
		- dealCard()
	- Card
		- faceValue
		- suit
		- isAvaliable()
		- setAvaliable(state)
	- Hand
		- `cards=[]`
		- score()
		- addCard()
	- BlackJackHand extends Hand

備註：這邊我除了看書內容，可以問bard: 21點遊戲規則是什麼，請解釋並說明如何使用OOP方式實作
## Ref
