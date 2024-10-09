---
title: 20220811-LINE-Blockchain-Developer-Intern
date: 2022-08-11
tags:
  - blockchain
  - LINE
  - select
updated: 2024-02-24
---
## 為何想去實習？
- 知道業界缺乏什麼樣的人才？
- 了解學界、業界差異
- 累積實戰經驗
- 同學都有好幾段實習經歷
- 看看自己的市場價值
## 我怎麼準備？
- 目標
	- Blockchain、雲端相關、Application
- 當時準備
	- ALG、DS、Behavior
- 檢討
	- 但可能比較重要還是 Side Project及你準備一下有多想進你申請公司的一些準備
	- 雖然我沒花啥時間準備Side Project的面試，原本想說都我寫的問不倒，但其實很多問題不是當下你的Project做了什麼，而是面試官會希望你講一下你可以怎麼優化你的Side Project跟旁敲側擊技術難度
- 我很幸運因為那時剛好是Blockchain牛市，Blockchain人才非常稀缺，我剛好很幸運拿到趨勢及LINE的Offer
## 投遞 Intern
- 目標：選可以學到最多的，讓自己成為很厲害的工程師
- 指標
	- 實習時間
	- 成長性
	- 未來發展
- 機會
	- 趨勢Web3 Team(暑期2 month) vs. LINE Blockchain Dev (一年期)
		- 最後選擇 LINE，因為我爸在美商從小嚮往像我爸公司的外商文化及實習時間長（預期可以學到比較多東西），但如果可以重新選我可能會選趨勢，因為那個比較偏分析交易+點一些Infra技能。
- 其她
	- 中研院：放棄
		- 一階過後放棄
	- 台灣微軟：未錄取
		- 4/28電話面試，BQ > 5/6  說明演算法、中英自我介紹（萬寶華）
		- 大概面到第四輪，應該是沒有Team match被刷，當時偏向找AR/VR。
		- 其實我不太喜歡他們委託給其他人力公司，很難從面試官獲得反饋，面試很像在跟沒靈魂的機器人對答。
	- 群暉 iOS/Android：無聲
		- 3/18 投遞 > 4/12 一面線上考 Link List > 4/21 二面考Tree 樹遍歷，不用queue等資料結構
		- 面到第三輪，考很細，都考DS的問題，因為是面Application所以LeetCode沒有很難，問很多OS、OOD及記憶體管理問題，無聲。
	- Garmin：無聲
		- 我實驗室同學(博翔)很早就上了，所以沒有機會ＱＱ
	- Amazon：沒上
		- Coding沒寫完。
	- Intel：放棄
		- 原本有TME(Technical Marketing Engineer)機會，但因為LINE先上＋我爸覺得年輕人做這沒有很好（他之前幹過這），所以婉拒。
	- ASUS：5/19 二面沒上
	- 趨勢：放棄
		- 3/25 Codility (120min) > 4/15通知二面 > 4/21 主管聊天（專案）
	- 緯創：放棄
	- LINE Blockchain：錄取
		- 3/19 投遞 > 4/28面試（聊履歷） > 5/11 確認錄取
- 結論
	- __感覺有什麼機會還是看當時就業市場需要什麼__
## 關於 LINE Blockchain Dev
- Background
	- LINE的組織架構很複雜...，從上到下都是，因為避稅關係，好像設立地點是在某太平洋小島，總之我算是在LINE做Blockchain的子公司LINE Next，底下的DOSI Store產品，主要就是NFT交易市場Team。
	- 因為我們的Product Owner是KR，所以Deadline很死、很操、沒辦法negotiate。
- Pros
	- 學習資源很多，LINE的Engineer文化就是分享（尤其是日本），Global Dev Relation很活躍會一直去邀請大佬來分享，有很多讀書會，裡面的人也熱愛分享。
	- 主管級很有Business的Sense，也會在讀書會跟員工討論分享，也不會有主管架子，新人意見可以很有效傳達到上面。
- Cons
	- 組織很扁平，可能會一直被skip(大主管)敲，Context Switch要很好。
	- 會議很多，跟KR、讀書會、自己Team，我感覺大概工作有一半時間都在開會 @@
- 總結
	- LINE 是一間很大的新創公司，相對其他大公司變動很快，無時不刻在創新。
	- 想比較多產品參與感可能要去比較在地化的Team，LINE Today、Travel、Music之類，否則還是去LINE Fukuoka（福岡）、LINE Tokyo（東京）、LINE Global(韓國)比較好

## 我學到了什麼？
- 使用 Monorepo Development 打造 Scalable Frontend
	- [[20220811-monorepo-development]]
	- Why?  Re-use Code
	- How? 由很像JSON結構去生前端，其實美商很多都這樣，這邊可能用graphql比較好
- Web2 公司如何做、進入Blockchain/web3
	- 公司私鏈、COSMOS（LINE Blockchain底層使用）
- 公司運作
	- Business
	- 避稅
- 各國文化差異
	- 日本：嚴謹，重Testing
	- 韓國：做事很快、嚴格
- 軟體開發
	- Dev Flow: ![](https://i.imgur.com/f2x8itN.png)
	- 開發流程 ![](https://i.imgur.com/P44twiK.png)
	- 增進Frontend (Alvin推薦)
		- clean code: design  
		- clean architecture: refactor
		- clean architecture  
		- white_check_mark  
		- eyes  
		- raised_hands
		- You Don't know JS ![](https://i.imgur.com/oOmi8k9.png)
		- https://github.com/getify/You-Dont-Know-JS
		- https://medium.com/%E6%89%8B%E5%AF%AB%E7%AD%86%E8%A8%98/react-swr-485b8e41ef78
		- https://medium.com/starbugs/%E9%96%8B%E6%BA%90%E5%B0%88%E6%A1%88%E8%AE%80%E8%B5%B7[…]1%E4%B8%8D%E8%A6%81%E6%9B%B4%E6%96%B0%E7%9A%84-swr-d02dadc1116b
		- https://medium.com/hulis-blog/frontend-engineer-guide-297821512f4e
		- https://roadmap.sh/frontend 
		- https://www.tenlong.com.tw/products/9786263332577
		- https://en.wikipedia.org/wiki/Multitier_architecture
		- https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93viewmodel
		- https://www.guru99.com/mvc-vs-mvvm.html
		- https://www.tutorialspoint.com/What-is-the-difference-between-session-and-cookies

## 我在實習做了什麼？
- 升級project workspace to React 18 [[20220721-upgrade-nx-repo-to-react-18]]
## 認知反直覺的事
- 景氣不好因為招聘放緩所以不太會裁員（台廠思維）
- 廣告的收益並不好
- 管理學第一步是要從自身利益開始
## 認識/厲害的人
- George (UIT Eng manager) 中央資管 (Skip) 半導體pm > LINE日本UIT > LINE TW
	- 以前是LINE日本的，後來來台灣是UIT的頭，我很常被他抓去討論Blockchain的事情😂。
- Coke (UIT Team Lead) 中央資管碩畢
	- 我的直屬主管，常常在開會的時候分享Code怎麼寫比較安全、我覺得他蠻棒ㄉ，資源也很Support，我那時說想去碰K8s他也給我一個K8s Task，也會跟我講要做哪些Task可以讓自己未來比較值錢，講話很好笑。
- Eric (Mentor) 交大資工實務組，yoe~1y
	- 交大實務組碩畢業，實作很強，但講話有點太直接。好像同時也在創業，很厲害的人。
- Alvin (UIT Senior) 輔大資工，YOE 5+
	- 算蠻資深UIT，以前在趨勢，他之前推薦我很多FE的學習資源，以及講解整個Project的架構、歷史，真的很抱歉打擾他很多時間XD
- Evan  (Dev Rel Lead) 東吳資管(?)，yoe 10+
	- 應該軟體開發圈沒人不認識他，Golang社群很活躍，以前在DSC也常常聽他分享學生該怎麼樣讓自己更有競爭力！
- Tom (DOSI ServerSide) 
	- 黑客松夥伴，很Carry，也指出了我一些Project的
- Water  (Travel Team ServerSide Intern) 台大資工所 
	- 我學姊ＸＤ 實驗室也很近，之前常常和她請教BE的一些技術、該學哪些之類，還有叫我不要延畢XD
- TU (Mobile Team Intern) 北科資工 -> 英國碩
	- 可能因為他實習時間待比較長？跟他聊蠻多Mobile方面還有業界比較看什麼
- Cipto (UIT) 北科互動，yoe 10+
	- 之前是Designer後來轉FE，之前有關UI問題都問他XD
- Steve (UIT Intern) 雲科電機
	- 有很多我不知道問題可以找誰的時候都是直接問他
- Jerry (QA Intern) 政大資管
	- 沒有很熟，之前Intern月會有小聊Blockchain，以前他在OurSong，但後來去日本露天
- Jonny (SRE Team Lead)
	- 之前K8s不知道怎用的時候都是去請教他，很厲害的人，人也很好，以前在騰訊
- Steve (SRE Intern)
	- 只有吃過幾次飯，sitcon 裡大神，貌似是大一休學
- Kyle (UIT Lead) 政大資管學 yoe 3-5y
	- FE 大佬，有出書很厲害，但後來貌似也不在LINE了
- Brian (Staff Engineer (?), Platform)
	- DevOps大佬，之前在IBM，上過他的內部training學到很多DevOps知識
- Penny (ML Team Lead) 外國碩->TSMC->LINE
	- 之前在TSMC，很厲害
- Tom (UIT Infra) 
	- UIT 優化、Infra很厲害
- Joey (Strategy)
	- 黑客松夥伴，對於Presentation 很厲害，很Carry
- YiHan
	- TW Intern -> LFK（福岡）
- OO (Blockchain) ??
	- 從幣安跳來LINE

## Ref
