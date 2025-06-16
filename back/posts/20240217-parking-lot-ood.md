---
title: 20240217-parking-lot-ood
date: 2024-02-17
tags:
  - object_oriented_design
updated: 2024-02-17
up:
  - "[[ood]]"
---
## Question
設計一個根據object-oriented principles的parking lot（停車場）
## Solution
- 跟interviewer討論支援什麼類別的車
- 假設
	- 停車場有多個level，每個level有多個spots
	- 停車長可以停摩托車、汽車及公車
	- 有摩托車停車、小客車停車場及大型停車場
	- 摩托車可以停在任何停車場
	- 小客車可以停在小客車、大型停車場
	- 公車只能停在大型停車場
- 建立一個車輛的abstract類別可以讓其他extend
- ParkingLot是多個Level的warpper
- 摩托車停車、小客車停車場及大型停車場可以繼承自ParkingLot

## Ref
