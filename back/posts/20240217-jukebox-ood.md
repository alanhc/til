---
title: 20240217-jukebox-ood
date: 2024-02-17
tags:
  - object_oriented_design
updated: 2024-02-17
up:
  - "[[ood]]"
---
## Question
使用object-oriented principles設計jukebox musical（點唱機）
## Solution
- 問interviewer釐清設計限制
	- 播放CD/錄影/MP3？
	- 在PC/實體點唱機？
- 假設
	- for example 電腦模擬，要接近實體點唱機
- basic component
	- Jukebox
	- CD
	- Song
	- Artist
	- Playlist
	- Display
- breakdown to find possible actions
	- Playlist creation（add/delete/shuffle)
	- CD selector
	- Song selector
	- Queuing up a song
	- get next song from playlist
- 使用者可以：
	- add
	- delete
	- credit infomation
- 
## Ref
