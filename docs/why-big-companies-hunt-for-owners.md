# 為什麼大公司永遠在找 Owner?——從眾手問題到問責黑洞,以及 AI Agent 如何讓這一切重新洗牌

## 一個所有工程師都熟悉的場景

系統出問題了。跨部門會議開起來,螢幕上是一張紅色的 dashboard。主管開口的第一句話,不是「問題的根因是什麼」,而是——

「這個誰 own?」

接下來的二十分鐘,會議的主軸不是修復,而是一場精密的邊界劃定:這是 platform 的問題還是 driver 的問題?是 CI 環境的問題還是 code 本身的問題?是我們的 module 還是隔壁 team 的 dependency?每個人都在做同一件事:證明箭頭不指向自己。

如果你在大公司工作過,你會知道這不是哪家公司特別病態。這幾乎是所有大型組織的通用行為模式。而有趣的是,這個行為模式在學術上有超過四十年的研究譜系——它有名字、有理論、有解法,也有解法失效的完整記錄。更重要的是,當 AI agent 開始進入工作流,這個舊問題正在以新形態重新打開。

## 第一層:找 Owner 是理性的——眾手問題

先替組織說句公道話:找 owner 不是官僚病,而是對一個真實困境的理性回應。

政治學者 Dennis Thompson 在 1980 年將這個困境命名為「眾手問題(the problem of many hands)」[1]:當一個結果是由許多人的手共同造成的,就沒有任何一個人能被合理地究責。每個人都只貢獻了一小塊,每一小塊單獨看都無可指摘,但合起來就是一場災難——而災難發生時,你找不到那個「該負責的人」,因為他不存在。

心理學給了這個問題一個更早的實驗基礎。Darley 與 Latané 在 1968 年的旁觀者實驗證明了「責任分散(diffusion of responsibility)」效應 [2]:在場的人越多,任何一個人採取行動的機率越低。放到組織裡,這條定律的推論很殘酷——收件人越多的信,越沒有人回;與會者越多的會,越沒有人做決定;掛了越多名字的專案,越沒有人真正在看。

所以組織找 owner,本質上是在對抗物理定律般的人性。責任必須收斂到一個名字上,事情才會動。

## 第二層:業界的解法——一個名字,不能再多

科技業對眾手問題發展出了成熟的制度化解法,而且各大公司的版本驚人地一致:**把 accountable 的人數強制收斂到一。**

Apple 的版本叫 **DRI(Directly Responsible Individual)**:每一個專案、每一個 feature、每一場會議的每一個 action item,都必須掛一個名字。不是一個部門,不是一個 team,是一個名字。

Amazon 的版本叫 **single-threaded owner**,在《Working Backwards》中有完整記載 [3]:重要的事必須有一個「單執行緒」的負責人——這個人不能兼職,不能同時 own 別的東西,他醒著的每一刻都在想這件事。Amazon 的邏輯是:一個兼職的 owner 等於沒有 owner,因為當兩件事衝突時,總有一件會被犧牲,而被犧牲的那件事實質上處於無人狀態。

連最常被詬病的 RACI 矩陣,其設計原意也是同一件事:R(負責執行)可以有很多人,但 A(最終問責)在任何一格裡都只能填一個名字。RACI 在實務上的失敗,往往不是因為框架錯了,而是因為組織忍不住在 A 欄裡填了一堆名字——這等於親手把眾手問題又請了回來。

到這裡為止,故事是正面的:眾手問題是真的,單一 owner 制度是有效的解法。但事情沒有這麼簡單——這個解法有三個結構性的極限,而且都有紮實的實證研究。

## 第三層:解法的極限——有些系統天生眾手,而 Owner 會換人

**第一個極限:不是所有東西都能收斂到一個名字。**

軟體工程領域對 ownership 最經典的實證,是 Bird 等人 2011 年對 Windows Vista 與 Windows 7 的研究 [4]:一個元件的最大貢獻者擁有比例越低、低專業度貢獻者越多,它的 pre-release faults 與 post-release failures 就越多。這篇論文常被拿來當「單一 owner 有效」的證據——但同一份研究也揭示了反面:那些低專業度貢獻者去碰別人的 code,多數不是紀律問題,而是結構必然。他們往往是為了自己負責的元件的相依性與介面,不得不改動別人的地盤。元件之間耦合越深,「每個檔案都有明確 owner」就越接近幻覺。

平台層、CI pipeline、共用測試資源、跨產品線的基礎設施——這類「公共財」元件尤其如此:每個 team 都會碰、每個 team 都依賴,但把它掛給任何單一個人都名不符實。這也是為什麼敏捷陣營中存在一支主張 collective code ownership 的傳統:與其維持一個名不符實的單一 owner,不如讓整個團隊共同持有,用規範與測試取代邊界。

共同持有確實有一個著名的失敗模式:退化成無人持有,又回到眾手問題。但把失敗歸咎於「共同」是誤診。Freidson 在《Professionalism: The Third Logic》中指出 [34],協調工作只有三種邏輯:市場、科層,以及專業——而專業邏輯的成立條件,是由職業社群(而非雇主、也非價格)來定義什麼算勝任的實踐、什麼是可接受的風險,並賦予實踐者相應的裁量權。

把這個框架套上去,ownership 的三條路線立刻清晰了:**單一 owner 是科層解**(用權威指派收斂責任);**放任式的共同持有是市場解**(誰有空誰改,靠個體誘因自發協調),而它確實會退化;**專業解則是第三條路**——Linux 的 subsystem maintainer 制度、成熟開源專案的 code review 規範與 maintainership、任何運作良好的 platform team,靠的既不是單一名字也不是放任,而是社群規範、同儕審查與實踐者的裁量權。這與 Ostrom 對公共財治理的發現同源:被治理的公地不會必然悲劇,悲劇只發生在無治理的公地。

這個區分對本文的主線很重要,因為它給出了一個正面主張:公共財元件需要的不是更用力地找 owner,而是專業邏輯的治理條件。而這些條件——社群規範、同儕裁量、對「什麼算做好了」的定義權——恰好是絕對服從文化與百分比管理最先摧毀的東西。單一 owner 不是普遍解,而是一個適用範圍有限的科層工具;當組織把科層工具套用到需要專業邏輯的地方,它得到的不是責任收斂,而是一個名字。

**第二個極限:owner 是會換的,而換手的成本大到可以量化。**

組織圖上的 owner 欄位看起來是靜態的,現實中它持續在變:離職、轉組、reorg、產品線交接。而實證研究對這筆成本的估計相當不留情面。

Mockus 在 2010 年的研究發現,組織變動(人員離開、組織結構重組)的開發者中心度量,可以預測客戶回報的缺陷 [5]——換句話說,owner 換人這件事本身,就是一個缺陷的前導指標。他更早在 2009 年就提出了「succession(繼承)」的量測方法 [6]:當程式碼從離開者手上移轉給接手者,這個移轉的品質是可以被追蹤和評估的——這等於承認,owner 變更不是一次 HR 事件,而是一段有成本、有風險、需要被管理的工程過程。

Rigby 與 Mockus 等人 2016 年的研究則把這筆帳算到了極致 [7]:他們以 Chrome 與 Avaya 的專案為案例,借用財務風險分析的方法量化人員流動造成的知識損失,發現專案可能承受的損失可達預期損失的三倍以上,歷史模擬中甚至超過五倍。翻譯成管理語言:如果你用「平均交接成本」來規劃 owner 變更,你會系統性地低估尾部風險——最壞情況不是平均值的一點五倍,是三到五倍。

**第三個極限:組織自己不遵守自己的解法——兼職 owner 與百分比切人。**

Amazon 的 single-threaded 邏輯說得很清楚:owner 不能兼職。但現實中,多數組織出於人力成本,做的是完全相反的事——一個人同時掛系統整合與 module owner,而管理現場常見的配置方式,是一張「30% 在 A、70% 在 B」的百分比報表。這種做法在組織研究裡有正式名稱:**multiple team membership(MTM,多重團隊成員身份)**,而且它不是邊緣現象——Mortensen 與 Gardner 2017 年在《哈佛商業評論》的調查指出,在全球性企業裡,同時隸屬多個團隊對 81% 的管理者而言是常態 [9]。

這個領域的奠基理論來自 O'Leary、Mortensen 與 Woolley 2011 年的模型 [8]:組織用 MTM 追求生產力與學習的雙重紅利,但這個結構會對成員的注意力與資訊處理造成互相競爭的壓力,使兩者難以同時提升——成員身份的數量與多樣性需要謹慎平衡,而不是能無限疊加的資源。

問題出在「百分比」這個度量本身:它預設注意力像機台工時一樣可以線性切割——投 30% 的時間,收 30% 的產出。但實證研究否定這個假設。Zika-Viktorsson 等人 2006 年對多專案環境的研究提出了「project overload(專案過載)」的概念 [10]:多專案並行造成的時間碎裂與頻繁切換,與心理壓力反應及能力發展受阻相關——碎片化不只吃掉產出,還吃掉人的成長。軟體工程領域則有 Vasilescu 等人 2016 年以 GitHub 大規模縱貫資料做的檢驗 [11]:開發者的產能取決於專案數量、專注度與專案多樣性之間的平衡,多工存在可量測的認知極限——論文標題《The Sky Is Not the Limit》本身就是結論。業界流傳最廣的經驗法則來自 Weinberg:每多一個並行專案,約有 20% 的時間損耗在切換上——這是經驗法則而非嚴格實證,但它指出的方向與後來的研究一致:切換成本不會出現在任何一張百分比報表上,它是報表以外的隱形稅。

而百分比切人還有一個更深的矛盾,直接回到 Amazon 的邏輯:當那個 30% 的角色與 70% 的角色衝突時,30% 那件事實質上處於無人狀態。百分比不是承諾的強度,是被犧牲的優先順序——一個被切成兩半的 owner,不是兩個半職 owner,而是兩個隨時可能歸零的 owner。百分比報表製造了一種「每件事都有人 cover」的會計幻覺,但注意力不是會計科目。

這三個極限合起來,解釋了大公司裡一個常被忽略的現象:**組織裡存在一整類角色——系統整合、build/CI 維運、跨團隊 triage、program management——他們的工作內容,本質上就是在為眾手問題與 owner 變更持續買單;而諷刺的是,這些角色往往也正是最常被百分比切割的人。** 單一 owner 制度並沒有消滅眾手問題,它只是把問題推到了元件的邊界上;而邊界上的碰撞、名字換掉之後的知識斷層、以及切換本身的隱形稅,需要有人天天去接。這些角色的存在不是組織的低效,而是組織對「解法極限」誠實的定價——前提是,組織有誠實地定價,而不是假裝百分比報表已經把成本算完了。

## 第四層:夾在中間的人——邊界角色的結構性困境

上一層說有人在為系統買單。這一層要看的是:買單的人自己過得怎麼樣。答案是,組織研究對這個位置有將近五十年的研究,而結論相當一致——**站在邊界上的人,承受的是位置帶來的結構性懲罰,而不是個人表現的問題。**

先看這個角色有多關鍵。Tushman 1977 年在《Administrative Science Quarterly》的奠基研究(R&D 實驗室 345 名受試者、58 個專案)辨識出 gatekeeper 與 liaison 這類特殊邊界角色 [12]:有效的跨界資訊流動,只由少數同時對內、對外都連結良好的個人完成。換句話說,整合與協調不是「誰都能做的雜事」,而是稀缺能力——這是這條文獻線的第一個結論,也是最常被組織遺忘的一個。

但關鍵不等於好過。Kahn 等人 1964 年的角色衝突經典 [13] 描述了「焦點人物(focal person)」的處境:一個同時被多個 role sender(主管、合作團隊、下游客戶)投以期待的人,當這些期待互不相容,他承受的就是角色衝突——Kahn 等人的原文說,這種衝突在持續而極端的形態下「不只是惱人,而是摧毀身份認同的」。而這個研究傳統裡有兩個發現,精準命中了「夾心餅乾」的痛點:第一,後續分析顯示,經驗到的衝突強度與 role set 的多樣性相關——跟組織其他部門頻繁接觸的人衝突最強,而且 role set 的組織距離越遠(跨越的層級與部門越多),衝突越大。第二,Kahn 的主要發現之一是:客觀存在的衝突要轉化為主觀壓力,條件是 role set 的權力高。把兩個發現疊起來:**一個低職等的人,面對一圈高權力、高多樣性、高組織距離的 role sender——這是角色衝突理論能描述的最痛的組態,而它正是大公司裡系統整合角色的日常。**

再看「被 challenge」這件事。社會學對中介位置(brokerage)的綜述——Stovel 與 Shaw 2012 年發表於《Annual Review of Sociology》[14]——指出 brokerage 有根本的雙面性:一方面它促成互動、活絡經濟、推動協作;另一方面它常伴隨對圖利的懷疑、剝削的指控與不平等的加劇。被質疑「資源用錯」是 broker 位置的結構性質疑,不是個人操守問題:**兩邊的人都只看得見你花在自己這邊的成本,誰也看不見你為整體省下的協調成本**——因為協調成本被省下的時候,它不會出現在任何人的報表上;只有協調失敗的時候,大家才會突然看見你。中間人的產出天生是反事實的(counterfactual):你做得越好,越沒有人知道你做了什麼。

最後是職等的問題,而這裡有一個比績效制度更深的成因。Abbott 在《The System of Professions》中論證 [35],專業地位的來源是**管轄權(jurisdiction)**:一個職業對某個抽象知識體系取得排他的控制權,才能在專業系統的競爭中站穩位置;職業之間的衝突,本質上是管轄權的邊界爭奪。

用這把尺量一下邊界角色:系統整合有專屬的抽象知識體系嗎?有證照、有公認的實踐標準、有能對「什麼算整合得好」下定義的社群嗎?沒有。它是各個管轄權之間的縫隙——每個專業都宣告自己的地盤到哪裡為止,而剩下的部分就是整合者的工作。**一個由「其他人的管轄權之外」定義的角色,結構上不可能擁有管轄權。** 這是低職等的真正來源:不是他的工作不重要,而是他的工作沒有一個社群能為它的重要性背書。

制度層面的證據隨之而來。Babcock 等人 2017 年在《American Economic Review》提出「低晉升性任務(non-promotable tasks)」的概念 [15]:組織裡存在一類工作,對組織運作關鍵、但對執行者的晉升無益,而這類工作的分配具有系統性偏差——它傾向落在拒絕成本較高的人身上。工程圈的實務版本是 Reilly 的〈Being Glue〉:把跨團隊協調、拆解模糊問題、確保事情不掉在地上的工作稱為 glue work,並點出一個殘酷的不對稱——同樣的工作,資深的人做叫 leadership,資淺的人做,考核時卻可能被說「不夠 technical」。

注意這句「不夠 technical」的語法:它不是說你沒做事,是說你做的事不算數。**這正是管轄權的裁決在績效面談裡的形態。** 於是一個自我強化的迴圈閉合了:**協調工作沒有管轄權背書 → 不被計入晉升 → 職等停在原地 → 低職等讓「資源用錯」的 challenge 更容易成立 → 而 challenge 成立又進一步壓低這份工作的能見度。** 迴圈的每一步都合乎各方的局部理性,合起來卻是對組織最稀缺角色的系統性折舊。

這一層的結論值得直說:如果你發現自己是那個夾在中間的人,文獻給你的不是安慰,是診斷——你經歷的衝突、質疑與職等停滯,是邊界位置的結構產物,五十年前就被寫進教科書了。真正該被 challenge 的問題是:一個依賴邊界角色運轉的組織,為什麼把它的邊界角色放在最沒有權力的位置上?

## 第五層:陰暗面——當找 Owner 變成問責黑洞

經濟學家 Dan Davies 在 2024 年的《The Unaccountability Machine》裡提出了一個近兩年在管理圈迅速走紅的概念:**accountability sink(問責黑洞)**[16]。

Davies 的觀察是:大型組織會演化出一種結構——把決策委託給規則手冊、標準流程或電腦系統,讓「做決定的人」從系統中消失。當你的航班被取消、你的保險理賠被拒絕、你的請購單被退回,櫃檯後面那個人會告訴你:「這是系統規定,我也沒辦法。」他說的是實話。決策確實不是他做的——但也不是任何一個你找得到的人做的。責任被吸進一個黑洞,再也出不來。

Davies 有一個關鍵的洞察:accountability sink 要成立,必須切斷一條連結——**受決策影響的人的回饋,必須無法回到做決策的系統**。回饋斷了,錯誤就無法歸屬,也無法修正。

而這裡出現了一個令人不舒服的推論:**組織熱衷於找 owner,有時候不是為了解決問題,而是為了預先安排 blame 的落點。** 公部門研究者 Christopher Hood 在《The Blame Game》中系統性地記錄了這種行為 [17]:組織會精心設計結構來轉移和分配咎責,而「指定一個 owner」正是最便宜的咎責保險——出事的時候,黑洞已經挖好了,名字已經填好了。

這解釋了那個會議室裡的詭異現象:為什麼大家花二十分鐘劃界而不是修問題。因為每個人都憑直覺知道,此刻被指定為 owner,拿到的不是資源和授權,而是一張預付的咎責支票。

## 第六層:名字找得到,Ownership 找不到

這裡有一組被組織長期混用、但學術上截然不同的概念。

管理學者 Pierce、Kostova 與 Dirks 的「心理所有權(psychological ownership)」研究指出 [18]:「被指派為 owner」和「真心覺得這是我的」是兩回事。前者是一個組織圖上的標籤,後者是一種心理狀態——而只有後者會產生組織真正想要的行為:主動維護、長期投入、把系統的健康當成自己的事。

心理所有權的三個來源是:對目標物的控制感、對它的深入了解、以及在它身上投注的自我。注意這三項的共同點:它們都無法透過指派產生。你可以在組織圖上把一個 legacy system 掛到某個工程師名下,但如果他對這個系統沒有控制權(改動要過五層審批)、沒有深入了解(文件失傳、原作者離職)、也沒有投注過自我(去年才接手),那麼你得到的是一個 owner 的名字,和零 ownership。

大公司找 owner 的真正困境在此:**組織需要的是 ownership,但制度只能生產 owner。** 名字填上去了,黑洞挖好了,但那個「醒著的每一刻都在想這件事」的人,並不會因為一封指派信而出現。

## 第七層:AI Agent 進場,舊問題重新打開

以上六層,是 AI 出現之前的故事。而 agentic AI 的進場,正在讓這個四十年的老問題以新形態復活。

哲學家 Andreas Matthias 在 2004 年就預言了這件事,他稱之為「責任落差(responsibility gap)」[19]:傳統的責任歸屬建立在兩個條件上——控制與可預見性。你控制了行為、你能預見後果,所以你負責。但學習型自主系統的行為,會超出設計者能預測的範圍;當系統做出沒有任何人指示、也沒有任何人能預見的行為時,責任歸屬的鏈條就斷了。

Santoni de Sio 與 Mecacci 在 2021 年進一步指出 [20]:AI 帶來的責任落差不是一個問題,而是至少四個相互關聯的落差——罪責(culpability)、道德問責、公共問責、主動責任——而且 AI 的引入會讓原本的眾手問題更加尖銳,因為資料與決策在鏈條上的更多節點被引入和加工,受影響的人更難找到該找誰。

把這個抽象論述翻譯成工程現場的語言:

一個 AI agent 在你的 CI pipeline 裡自主修了一個 bug、開了一個 PR、被 merge 進了 production,三週後炸了。現在,會議室裡那句「這個誰 own?」要怎麼回答?寫 prompt 的人?批准 agent 上線的主管?Review 那個 PR 的工程師(他花了 90 秒)?模型的供應商?還是那個被掛名為「agent owner」、但既沒有寫那段 code、也沒有看過那段 code 的人?

組織的直覺反應是沿用舊解法:找一個 owner,把 agent 掛到他名下。但這正是問題所在——**這個 owner 被要求為他沒有寫過、沒有看過、也無法完全預測的產出負起全責。**

寫到這裡,必須先面對一個有力的反駁,因為它會從最值得說服的那類讀者口中說出來:**這不正是專業的定義嗎?** 結構技師在他沒有親手畫的圖上蓋章;主治醫師為住院醫師的處置負責;機長為整架飛機負責,而他無法預測每一顆引擎的狀態。專業之所以是專業,恰恰因為它承擔了超出個人控制範圍的後果。照上面的邏輯,全世界的專業都是空心的。

這個反駁成立,而回應它會讓論點更精確。回到 Freidson 的三邏輯 [34]:專業之所以能為自己沒有完全控制的結果負責,是因為三件事同時到位——他有拒絕蓋章的權力;判準來自專業社群而非雇主;執照制度讓他的責任與他的權威等長。責任超出控制範圍是可以的,前提是**權威也超出被指派的範圍**。

那麼組織對 agent owner 做了什麼?它拿走了專業的問責,保留了科層的控制。這個 owner 不能否決 agent、不能定義它的邊界、不能對「什麼算可接受的產出」下定義——但出事時他是那個名字。Evetts 為這種變形提供了精確的命名 [36]:這是 **organizational professionalism(組織專業主義)**——由管理者「從上」施加的專業話語,運作方式是科層決策、層級權威與標準化程序;它的對照組是 **occupational professionalism(職業專業主義)**,由專業社群「從內」控制,包含實踐者對工作的裁量權與自我規制。同一個「專業」的詞,兩套相反的權力方向。

所以真正的診斷不是「他無法預測,所以不能 own」——那條路會誤傷所有真實存在的專業。真正的診斷是:**他沒有權威,所以不能 own。** 他有 owner 的名字,卻不可能有心理所有權的三個來源:控制感(他無權停掉或重劃 agent 的邊界)、深入了解(產出量遠超人類可讀範圍)、自我投注(那不是他的作品)。這不是空心的專業,這是被抽走職業自主的專業主義——**責任是專業的,權威是科層的。** 兩者一旦脫鉤,ownership 在結構上就注定是空的。

而第三層談的換手成本,在這裡會以更糟的形態重現:agent 本身不會離職,但 agent 的 owner 會。當一個人類 owner 交接的是自己寫的系統,他至少還有文件、commit history 和腦中的決策脈絡可以移轉;當他交接的是一個 agent 與它累積的設定、prompt、邊界規則和例外清單——一套連他自己都只有部分理解的東西——succession 研究裡那個「三到五倍」的尾部風險,恐怕還是低估。

**而當組織開始要求員工「平行」處理多件事、「平行」監督多個 agent,百分比會計連殘餘的合理性都失去了。**

第一個問題在認知層。心理學的雙任務研究早已確立,人類的中央認知處理存在序列瓶頸(central bottleneck)[29]:兩件需要思考的事沒辦法真的同時做,只能排隊。Rubinstein、Meyer 與 Evans 2001 年的實驗進一步量測了切換的代價 [30]:任務間的每一次切換都有可測量的時間成本,而且任務越複雜、越不熟悉,成本越高。所謂「平行處理」,在認知上的真實形態是高頻的序列切換,加上每一次切換被課的稅——這筆稅,百分比報表裡沒有科目。

第二個問題,是「監督多個自主系統」這件事本身早就被量化研究過——只是在另一個領域。人機互動研究在無人載具的脈絡下發展了 **fan-out 模型**:Olsen 與 Wood 2004 年在 CHI 提出 [31],一個人能同時操控的自主系統數量,取決於系統的 neglect time(它能被放著不管多久)與 interaction time(每次介入需要多久)的比值;robot attention demand 與 interaction effort 是這個領域的標準度量。這套研究有兩個對 agent 時代極具警示性的發現:其一,後續模型加入等待時間與注意力切換成本後,可行的 fan-out 比原始估計更低;其二,即使是專門研究此事的領域,對「一個人最多能監督幾台」的預測方法至今結果不一——**連無人機領域用二十年都沒算準的東西,管理現場用一張百分比報表就決定了。**

第三個問題在時間結構。監督型工作是突發、中斷驅動的:agent 什麼時候需要人,不由 owner 的行事曆決定。Mark 等人 2008 年對中斷工作的經典研究發現 [32],被中斷的工作者會以更快的速度完成任務作為補償——代價是顯著更高的壓力、挫折感與時間壓力。而佇列理論的基本結果(Reinertsen 將其系統性地引入產品開發管理 [33])指出:當資源利用率逼近 100%,等待時間非線性暴增——把一個人用百分比填到滿,等於保證他監督的每一個 agent 在需要人的時刻都在排隊。**Agent 可以平行跑,但 agent 的 owner 的注意力不能平行給。**

三個問題合起來,結論是:百分比會計在人類多工的時代只是不準,在 agent 監督的時代則是量錯了維度。它量測的是時間如何被切分,但監督工作的真實成本是注意力的中斷分佈與佇列延遲。真正該問的不是「你花多少 % 在每件事上」,而是「你的 interaction time 加總之後,這個系統還剩多少 neglect tolerance」——而後者,目前沒有出現在任何一張管理報表上。

而 Davies 的警告在此刻變得格外刺耳:把決策委託給演算法,是建造 accountability sink 最便利的方式。如果組織不重新設計問責結構,AI agent 不會解決眾手問題——它會成為史上最大的一隻手,一隻沒有名字、沒有心理狀態、無法被咎責的手。而掛在它名下的那個人類 owner,只是黑洞入口處的一塊招牌。

**最後,AI 的到來還給個別員工帶來了一個全新的雙重束縛。**

現在很多組織對員工同時發出兩道指令。第一道是明的:「你要花 X% 的時間研究 AI」——但第三層已經證明,百分比是會計幻覺;而在所有活動裡,學習恰好是對時間碎裂最敏感的一種。Zika-Viktorsson 的 project overload 研究早就指出 [10],多工碎裂受損最重的不只是產出,還有能力發展本身。被切成細片的「研究 AI 時間」,買到的不是研究,是一種研究過的紀錄。

第二道指令是暗的,而且方向相反。Reif、Larrick 與 Soll 2025 年發表於《PNAS》的四個預註冊實驗(4,439 名受試者)發現 [21]:在工作中使用 AI 的人,預期也實際收到關於能力與動機的負面社會評價——被視為更懶、能力更差、更可取代,而且這個懲罰跨職業、年齡與性別一致地存在;更諷刺的是,給出最嚴厲評價的,正是自己不常使用 AI 的評估者。研究者將此定性為一個悖論:提升生產力的工具,同時損害使用者的專業聲譽。後果是可預測的——受試者顯著地更不願意向主管與同事揭露自己使用了 AI。

從專業主義的角度看,這個懲罰一點也不非理性:**它是專業規範的制裁。** 「你交出的作品必須出自你的手」是專業身分的核心承諾之一,而使用 AI 觸犯的正是這條規範。這解釋了論文裡最耐人尋味的兩個發現:為什麼懲罰跨職業、年齡與性別一致(因為它針對的不是特定人群,是規範本身),以及為什麼最嚴厲的評審是不用 AI 的人(規範的守衛者往往是最恪守它的人)。

而這指向一個比「工作被取代」更深的威脅。回到 Freidson 的定義:專業之所以是第三種邏輯,是因為它握有對「什麼算勝任」的定義權。當勝任的標準逐漸由模型能力決定——當一個人的產出無論如何都追不上 agent、當「做得夠好」的基準線由工具重設——職業社群就失去了那項定義權。**AI 對專業的核心威脅,不是取代從業者,是解除職業對勝任的定義權;定義權一旦失去,第三邏輯就崩解,剩下的只有市場與科層。** 而本文從第一層到這裡的整個故事,講的正是市場與科層如何處理責任:一個用價格,一個用名字。

把兩道指令疊起來看,這是 Bateson 意義上的雙重束縛 [22]:「你必須採用 AI」與「採用 AI 會被懲罰」同時成立,而且——這是 Argyris 對組織防衛慣例的經典描述 [23]——**這個矛盾本身是不可討論的**。在絕大多數組織裡,沒有人能在會議上說出「我們一邊要求員工學 AI,一邊懲罰他們用 AI」——因為指出 mixed message 的人,通常會被當成問題本身。Argyris 指出,組織防衛的完整套路正是:傳遞不一致的訊息、否認不一致的存在、再讓這個否認變得不可討論。

但 Argyris 描述了不可討論性,沒有說明它是**怎麼被生產出來的**。Fournier 補上了這一塊 [37]:當「專業」的話語被輸出到傳統上不屬於專業的職業領域,它會成為一種遠距治理的紀律邏輯——把自主的實踐預先寫進一個問責網絡裡。她的核心命題值得慢讀:專業勞動之所以是自主勞動,是因為自主的條件已經被編碼進「專業勝任」這個概念本身。你可以自由行動,只要你的自由選擇恰好是專業所要求的那些。

這一塊補上之後,本文前面幾層的一個空缺才被填起來。前面說的都是結構如何施加,沒有說個人為何接受——而答案是:**因為拒絕的成本是被說「不夠專業」。** Babcock 的「低晉升性任務會流向拒絕成本最高的人」,在工程組織裡有一個具體形態:拒絕成本就是專業身分的損失。glue work 不需要強迫,只需要讓拒絕變成人格瑕疵;百分比報表不需要辯護,只需要讓抱怨它的人顯得斤斤計較;而矛盾之所以不可討論,是因為指出矛盾的人首先要付出「不夠專業」的代價。

這條線比 Argyris 更鋒利,因為它不需要指控任何人的惡意。沒有人在操作這套機制。**專業主義同時是組織最省力的紀律工具,也是員工唯一的抵抗語言**——當你說「這樣做不專業」,你使用的正是那把鎖住你的鑰匙。

**而資源匱乏會把這個雙重束縛擰得更緊。** 當人力已經不夠,員工在 AI 上的每一分鐘都會同時遭到兩個方向的質疑——這兩種質疑在各行各業的說法驚人地一致,而且各自有經典理論的名字。

第一種質疑來自管理端:「本業都做不完,為什麼在弄 AI?」這是 March 1991 年在組織學習經典中描述的結構性偏誤 [24]:組織天然傾向 exploitation(利用既有能力換取確定、近期的回報)而犧牲 exploration(探索新能力,回報遙遠且不確定)——因為探索的收益在時間上更遠、在機率上更散,它在每一次資源競爭中都處於劣勢。Nohria 與 Gulati 1996 年的實證則補上了 slack 的角色 [25]:slack(超出最低必要量的餘裕資源)與創新呈倒 U 關係——**在沒有 slack 的組織裡,實驗根本無法維持,因為實驗的產出天生高變異**。翻譯過來:一個資源匱乏的組織要求員工「研究 AI」,等於要求他在一個結構上不允許失敗的環境裡,做一件統計上注定會失敗幾次的事。Mullainathan 與 Shafir 對匱乏的研究 [26] 進一步解釋了管理端的視野:匱乏會使注意力隧道化(tunneling)——被塞滿眼前緊急事務的人,認知頻寬被課稅,結構上看不見長期投資的價值。管理者不是不理解 AI 重要,是匱乏讓所有人只看得見隧道裡的本業。

第二種質疑來自同儕:「為什麼你有多的時間弄 AI?」這來自另一條線。Adams 的公平理論(equity theory)[27] 指出,人會持續比較自己與他人的投入產出比,感知到的不公平會引發強烈的修正動機——在人人救火的環境裡,任何花在非救火事務上的可見時間,都會被直接讀成「你的負載比我輕」,無論那是不是被指派的任務。而 Bellezza 等人 2017 年的研究 [28] 補上了文化層:在忙碌本身已成為地位象徵(busyness as a status symbol)的職場文化裡,可見的非核心時間不只是負載訊號,更是一種地位違規。於是在匱乏的組織裡,「花 X% 研究 AI」的指令讓執行者三面受敵:管理端的 exploitation 偏誤、同儕的公平比較、加上自己也被匱乏隧道化的注意力——**指令發出的那一刻,組織就已經同時佈署好了懲罰它被執行的所有機制。**

而這個雙重束縛與本文的主線在此合流:當 AI 導入失敗,組織會找 owner 問「為什麼推不動」;當 AI 使用出錯,組織會找 owner 問「為什麼要用」。同一個人完全可能同時是這兩個問題的 owner。面對這種組態,員工最理性的個體反應是 shadow AI——偷偷用、不揭露——而 shadow AI 恰好是問責結構的最壞情況:**使用量最大化,可問責性最小化。** 組織用自己的評價文化,親手把 AI 的使用推進了黑洞裡。

## 結語:給組織的四個問題

這篇文章沒有要提供一套完整解法——那需要另一篇文章的篇幅。但在組織急著為每一個 AI agent 指派 owner 之前,有三個問題值得先回答:

**第一,你在找 owner,還是在找 blame 的落點?** 測試方法很簡單:看這個 owner 拿到的是授權還是義務。如果他有權停掉 agent、改變 agent 的邊界、否決 agent 的產出,那是 ownership;如果他只是出事時要寫報告的人,那是 accountability sink 的招牌。

**第二,你的問責結構有沒有保留回饋鏈?** Davies 的判準值得反覆引用:黑洞的成立條件是回饋斷裂。受 agent 產出影響的人(下游團隊、客戶、被 review 疲勞轟炸的工程師),他們的回饋能不能真實地改變 agent 的運作方式?如果不能,你已經在挖黑洞了。

**第三,你想要的到底是一個名字,還是一種心理狀態?** 如果是後者,那麼指派是不夠的。心理所有權來自控制、了解與投注——這意味著 agent 的 owner 必須參與 agent 的邊界設計、必須有工具穿透 agent 的行為、必須有時間把它當成自己的作品來經營。這很貴。但一個空心的 owner 更貴,只是帳單晚一點到。

**第四,你們口中的「專業」,是誰在定義?** 這是最不舒服的一問,也是前三問的底層。如果「專業」意味著實踐者對自己的工作握有裁量權、對「什麼算做好了」有發言權,那麼它是 ownership 的來源。如果「專業」只是一個用來讓人接下沒人要做的事、並且不抱怨的形容詞,那麼它是 accountability sink 的潤滑劑。同一個詞,兩個相反的用途,而它們的差別只有一個判準:**定義權在誰手上。** 一個組織如果希望它的員工像專業人士一樣為 AI 的產出負責,就必須讓他們像專業人士一樣,有權說「這個我不簽」。

四十年前,Thompson 告訴我們眾手問題無解,只能管理。科技業用 DRI 和 single-threaded owner 管理了它三十年。現在,AI agent 帶著史上最多的一雙手走進辦公室——組織要嘛重新設計問責,要嘛就會發現,那句「這個誰 own?」的答案,正在變成「沒有人,而且這次是真的沒有人」。

---

*本文描述的情境為跨產業通例的合成描寫,所有場景均可在引用文獻的實證樣本(涵蓋 Windows、Chrome、Avaya、GitHub、全球企業管理者調查等)中找到對應,不指涉任何特定組織或個人。*

---

## 參考文獻

1. Thompson, D. F. (1980). *Moral Responsibility of Public Officials: The Problem of Many Hands.* American Political Science Review, 74(4), 905–916. https://doi.org/10.2307/1954312
   — 「眾手問題」原始出處:當結果由許多人共同造成,便沒有任何個人能被合理究責。

2. Darley, J. M., & Latané, B. (1968). *Bystander Intervention in Emergencies: Diffusion of Responsibility.* Journal of Personality and Social Psychology, 8(4), 377–383.
   — 責任分散效應的經典實驗:在場人數越多,個人採取行動的機率越低。

3. Bryar, C., & Carr, B. (2021). *Working Backwards: Insights, Stories, and Secrets from Inside Amazon.* St. Martin's Press.
   — 記載 Amazon 的 single-threaded leadership 制度:重要事務必須有不可兼職的單一負責人。

4. Bird, C., Nagappan, N., Murphy, B., Gall, H., & Devanbu, P. (2011). *Don't Touch My Code! Examining the Effects of Ownership on Software Quality.* ESEC/FSE '11, 4–14. https://doi.org/10.1145/2025113.2025119
   — 以 Windows Vista 與 Windows 7 為對象的實證:最大貢獻者擁有比例越低、低專業度貢獻者越多,pre-release faults 與 post-release failures 越多;並發現低專業度貢獻多源於相依性與介面等結構性原因,無法單純禁止。

5. Mockus, A. (2010). *Organizational Volatility and Its Effects on Software Defects.* FSE '10, 117–126. https://doi.org/10.1145/1882291.1882311
   — 以開發者為中心的組織變動度量(人員離開、組織重組)可預測客戶回報缺陷,發現組織變動與品質下降相關。

6. Mockus, A. (2009). *Succession: Measuring Transfer of Code and Developer Productivity.* ICSE '09.
   — 提出量測開發者之間程式碼移轉(succession)的方法,將 owner 變更視為可追蹤、可評估的知識轉移過程,而非單純的人事異動。

7. Rigby, P. C., Zhu, Y. C., Donadelli, S. M., & Mockus, A. (2016). *Quantifying and Mitigating Turnover-Induced Knowledge Loss: Case Studies of Chrome and a Project at Avaya.* ICSE '16, 1006–1016. https://doi.org/10.1145/2884781.2884851
   — 借用財務風險分析方法量化人員流動造成的知識損失(以被遺棄的原始碼檔案為量測對象),發現專案可能承受的損失可達預期損失的三倍以上,歷史模擬中超過五倍;並回顧先前研究:維護被遺棄程式碼的留任者與新人生產力下降、更易出錯。

8. O'Leary, M. B., Mortensen, M., & Woolley, A. W. (2011). *Multiple Team Membership: A Theoretical Model of Its Effects on Productivity and Learning for Individuals and Teams.* Academy of Management Review, 36(3), 461–478.
   — MTM 的奠基理論:組織以多重團隊成員身份追求生產力與學習,但此結構對注意力與資訊造成互相競爭的壓力,兩者難以同時提升;成員身份的數量與多樣性需謹慎平衡。

9. Mortensen, M., & Gardner, H. K. (2017). *The Overcommitted Organization.* Harvard Business Review, 95(5), 58–65.
   — 指出在全球性企業中,同時隸屬多個團隊對 81% 的管理者而言是常態;探討組織層級的多重承諾如何侵蝕團隊效能。

10. Zika-Viktorsson, A., Sundström, P., & Engwall, M. (2006). *Project Overload: An Exploratory Study of Work and Management in Multi-Project Settings.* International Journal of Project Management, 24(5), 385–394.
   — 提出「專案過載」概念:多專案並行造成的時間碎裂與頻繁切換,與心理壓力反應及能力發展受阻相關。

11. Vasilescu, B., Blincoe, K., Xuan, Q., Casalnuovo, C., Damian, D., Devanbu, P., & Filkov, V. (2016). *The Sky Is Not the Limit: Multitasking Across GitHub Projects.* ICSE '16, 994–1005. https://doi.org/10.1145/2884781.2884875
   — 以 GitHub 大規模縱貫資料檢驗跨專案多工:開發者產能取決於專案數量、專注度與專案多樣性的平衡,多工存在可量測的認知極限。

12. Tushman, M. L. (1977). *Special Boundary Roles in the Innovation Process.* Administrative Science Quarterly, 22(4), 587–605.
   — 邊界跨越研究的奠基之作(R&D 實驗室 345 名受試者、58 個專案):辨識出 gatekeeper 與 liaison 等特殊邊界角色,發現有效的跨界資訊流動僅由少數同時對內、對外連結良好的個人完成。

13. Kahn, R. L., Wolfe, D. M., Quinn, R. P., Snoek, J. D., & Rosenthal, R. A. (1964). *Organizational Stress: Studies in Role Conflict and Ambiguity.* Wiley.
   — 角色衝突理論原典:焦點人物承受多個 role sender 的不相容期待;主要發現之一為客觀衝突須在 role set 權力高時才轉化為主觀壓力;後續研究顯示 role set 越多樣、組織距離越大,經驗到的衝突越強。

14. Stovel, K., & Shaw, L. (2012). *Brokerage.* Annual Review of Sociology, 38, 139–158.
   — 中介位置的社會學綜述:brokerage 具根本雙面性,一方面促成互動、經濟活動與協作,另一方面常伴隨圖利懷疑、剝削指控與不平等的加劇。

15. Babcock, L., Recalde, M. P., Vesterlund, L., & Weingart, L. (2017). *Gender Differences in Accepting and Receiving Requests for Tasks with Low Promotability.* American Economic Review, 107(3), 714–747.
   — 提出「低晉升性任務(non-promotable tasks)」:對組織關鍵但對個人晉升無益的工作,其分配具系統性偏差,傾向落在拒絕成本較高的人身上。

16. Davies, D. (2024). *The Unaccountability Machine: Why Big Systems Make Terrible Decisions—And How the World Lost Its Mind.* Profile Books.
   — 提出「accountability sink」:組織以規則手冊、標準流程或電腦系統吸收決策責任,切斷決策者與受影響者之間的回饋連結,使錯誤無從歸屬與修正。

17. Hood, C. (2011). *The Blame Game: Spin, Bureaucracy, and Self-Preservation in Government.* Princeton University Press.
   — 系統性記錄組織如何設計結構來轉移與分配咎責(blame avoidance)。

18. Pierce, J. L., Kostova, T., & Dirks, K. T. (2001). *Toward a Theory of Psychological Ownership in Organizations.* Academy of Management Review, 26(2), 298–310. https://doi.org/10.5465/amr.2001.4378028
   — 心理所有權理論:區分「被指派的 owner」與「真實的擁有感」,後者來自控制、深入了解與自我投注,無法透過指派產生。

19. Matthias, A. (2004). *The Responsibility Gap: Ascribing Responsibility for the Actions of Learning Automata.* Ethics and Information Technology, 6(3), 175–183. https://doi.org/10.1007/s10676-004-3422-1
   — 「responsibility gap」概念原典:學習型自主系統的行為超出可預測範圍時,傳統責任歸屬條件(控制與可預見性)失效。

20. Santoni de Sio, F., & Mecacci, G. (2021). *Four Responsibility Gaps with Artificial Intelligence: Why They Matter and How to Address Them.* Philosophy & Technology, 34, 1057–1084. https://doi.org/10.1007/s13347-021-00450-x
   — 主張 AI 的責任落差是四種相互關聯的落差(culpability、moral accountability、public accountability、active responsibility),且 AI 的引入使眾手問題更加尖銳。

21. Reif, J. A., Larrick, R. P., & Soll, J. B. (2025). *Evidence of a Social Evaluation Penalty for Using AI.* Proceedings of the National Academy of Sciences, 122(19), e2426766122. https://doi.org/10.1073/pnas.2426766122
   — 四個預註冊實驗(N = 4,439):在工作中使用 AI 的人預期並實際收到關於能力與動機的負面評價(更懶、能力更差、更可取代),懲罰跨職業、年齡、性別一致存在;自己不常用 AI 的評估者給出最嚴厲評價;受試者因此更不願揭露 AI 使用。

22. Bateson, G., Jackson, D. D., Haley, J., & Weakland, J. (1956). *Toward a Theory of Schizophrenia.* Behavioral Science, 1(4), 251–264.
   — 「雙重束縛(double bind)」概念原典:個體同時收到互相矛盾的指令,且無法對矛盾本身提出討論或逃離該情境。本文借用其結構描述組織對 AI 採用的矛盾要求,不涉及其原始臨床脈絡。

23. Argyris, C. (1990). *Overcoming Organizational Defenses: Facilitating Organizational Learning.* Allyn & Bacon.
   — 組織防衛慣例的經典:組織傳遞不一致的訊息(mixed messages)、否認不一致的存在、並使該否認不可討論,從而阻斷組織學習。

24. March, J. G. (1991). *Exploration and Exploitation in Organizational Learning.* Organization Science, 2(1), 71–87. https://doi.org/10.1287/orsc.2.1.71
   — 組織學習的奠基框架:組織天然傾向 exploitation(確定、近期的回報)而犧牲 exploration(遙遠、不確定的回報),因為探索的收益在時間與機率上皆處劣勢,在資源競爭中系統性落敗。

25. Nohria, N., & Gulati, R. (1996). *Is Slack Good or Bad for Innovation?* Academy of Management Journal, 39(5), 1245–1264.
   — 實證 slack(超出最低必要量的餘裕資源)與創新呈倒 U 關係:沒有 slack 時,實驗因產出高變異而無法維持;slack 過多則失去紀律。

26. Mullainathan, S., & Shafir, E. (2013). *Scarcity: Why Having Too Little Means So Much.* Times Books.
   — 匱乏心理學:匱乏使注意力隧道化(tunneling)並對認知頻寬課稅,使人系統性地忽視隧道外的長期投資。

27. Adams, J. S. (1965). *Inequity in Social Exchange.* In L. Berkowitz (Ed.), Advances in Experimental Social Psychology (Vol. 2, pp. 267–299). Academic Press.
   — 公平理論原典:人持續比較自己與他人的投入產出比,感知不公平時產生強烈的修正動機。

28. Bellezza, S., Paharia, N., & Keinan, A. (2017). *Conspicuous Consumption of Time: When Busyness and Lack of Leisure Become a Status Symbol.* Journal of Consumer Research, 44(1), 118–138.
   — 忙碌作為地位象徵的實證:在當代職場文化中,忙碌與缺乏閒暇被解讀為能力與稀缺性的訊號,可見的餘裕時間因此帶有地位成本。

29. Pashler, H. (1994). *Dual-Task Interference in Simple Tasks: Data and Theory.* Psychological Bulletin, 116(2), 220–244.
   — 雙任務干擾的經典綜述:人類中央認知處理存在序列瓶頸,需要思考的任務無法真正平行執行,只能排隊。

30. Rubinstein, J. S., Meyer, D. E., & Evans, J. E. (2001). *Executive Control of Cognitive Processes in Task Switching.* Journal of Experimental Psychology: Human Perception and Performance, 27(4), 763–797.
   — 實驗量測任務切換成本:每次切換均有可測量的時間代價,且任務越複雜、越不熟悉,成本越高。

31. Olsen, D. R., Jr., & Wood, S. B. (2004). *Fan-out: Measuring Human Control of Multiple Robots.* CHI '04, 231–238. ACM.
   — 提出 fan-out 模型:一人可同時操控的自主系統數量取決於系統的 neglect time 與 interaction time 之比;後續研究加入等待時間與切換成本後,可行 fan-out 更低。

32. Mark, G., Gudith, D., & Klocke, U. (2008). *The Cost of Interrupted Work: More Speed and Stress.* CHI '08, 107–110. ACM.
   — 中斷工作的經典實驗:被中斷者以更快的工作速度補償,代價是顯著更高的壓力、挫折感與時間壓力。

33. Reinertsen, D. G. (2009). *The Principles of Product Development Flow: Second Generation Lean Product Development.* Celeritas Publishing.
   — 將佇列理論系統性引入產品開發管理:資源利用率逼近 100% 時等待時間非線性暴增,高利用率的排程等於保證延遲。

### 專業主義文獻線(第 34–37 項)

以下四項構成貫穿本文第三、四、六、七層的專業主義論證線,依主題成組編列,不依首次出現順序。

34. Freidson, E. (2001). *Professionalism: The Third Logic.* University of Chicago Press.
   — 提出協調工作的三種邏輯:市場、科層、專業。專業邏輯的成立條件是職業自主控制——由專業社群而非雇主或價格,定義何謂勝任的實踐與可接受的風險,並賦予實踐者相應裁量權。

35. Abbott, A. (1988). *The System of Professions: An Essay on the Division of Expert Labor.* University of Chicago Press.
   — 專業地位源於對抽象知識體系的排他管轄權(jurisdiction);專業之間的衝突本質上是管轄權的邊界爭奪。本文用以解釋為何缺乏管轄權的邊界角色在職等上結構性受抑。

36. Evetts, J. (2003). *The Sociological Analysis of Professionalism: Occupational Change in the Modern World.* International Sociology, 18(2).
   — 區分 organizational professionalism(管理者「從上」施加的控制話語,以科層決策、層級權威與標準化程序運作)與 occupational professionalism(專業社群「從內」的控制,包含裁量權與自我規制)。

37. Fournier, V. (1999). *The Appeal to 'Professionalism' as a Disciplinary Mechanism.* The Sociological Review, 47(2), 280–307. https://doi.org/10.1111/1467-954X.00173
   — 論證「專業」話語被輸出到非傳統專業領域後,成為一種紀律邏輯:它把「自主的」專業實踐預先寫入一個問責網絡,並透過「專業勝任」這個概念遠距治理行為;專業勞動之所以自主,是因為自主的條件已被編碼進勝任的定義之中。

---

## 查證註記

> 1. 本次已透過網路查證出版資訊與標題、作者、年份相符的:第 1、4、7、8、10、11、12、13、14、16、19、20、21、24、25、31 項。其中第 16 項(Davies)英版由 Profile Books 出版(2024),美版由 University of Chicago Press 出版(2025),書籍無 DOI 屬正常;第 4 項(Bird et al.)DOI 10.1145/2025113.2025119、第 7 項(Rigby et al.)DOI 10.1145/2884781.2884851、第 11 項(Vasilescu et al.)DOI 10.1145/2884781.2884875、第 21 項(Reif et al.)DOI 10.1073/pnas.2426766122、第 24 項(March)DOI 10.1287/orsc.2.1.71 均已核對;第 25 項(Nohria & Gulati)卷期頁碼(AMJ 39(5), 1245–1264)與「無 slack 時實驗因高變異無法維持」的機制描述均經二手來源交叉核對;第 31 項(Olsen & Wood)之 CHI 2004 頁碼(231–238)、fan-out/neglect time/interaction time 定義、「後續模型加入等待時間與切換成本」(Goodrich 等人的延伸)、「fan-out 預測方法結果不一」(Crandall & Cummings 2007)均已核對。「損失可達預期三倍以上、模擬中超過五倍」為 Rigby et al. 摘要原述;「持續而極端的角色衝突是摧毀身份認同的」為 Kahn et al. 原書第 6 頁文句的翻譯轉述;第 21 項的「更懶、能力更差、更可取代」「不常用 AI 者評價最嚴厲」「不願揭露」均出自論文摘要、正文與 Duke Fuqua 官方報導,已交叉核對。第 26(Mullainathan & Shafir)、27(Adams)、28(Bellezza et al.)、29(Pashler)、30(Rubinstein et al.)、32(Mark et al.)、33(Reinertsen)項為經典書籍或知名期刊/會議文獻,本次未重新開啟原頁核對卷期頁碼;投正式場合前建議自行核對。
> 2. 第 8 項(O'Leary et al.)的卷期頁碼(AMR 36(3), 461–478)已核對,但不同來源引用的 DOI 有兩個版本(10.5465/amr.2011.61031807 與 10.5465/amr.2009.0275),故本文引用不掛 DOI;投正式場合前建議至 AMR 官網確認正式 DOI。第 9 項(Mortensen & Gardner, HBR)之「81% 管理者」數據為二手文獻(Rishani 2024 綜述)轉述,建議引用前核對 HBR 原文。
> 3. 第 13 項(Kahn et al.)行文中「role set 多樣性與衝突相關」出自 Snoek(1966)對同一資料集的後續分析、「組織距離越大衝突越強」出自 Miles(1977)的研究,本文以「後續分析/後續研究」表述,未將其歸給 Kahn 原書;若需具名引用建議補 Snoek(1966)與 Miles(1977)原始文獻。
> 4. 第 15 項(Babcock et al., AER)為知名文獻,本次未重新開啟 AER 原頁核對卷期頁碼;投正式場合前建議自行核對。Reilly〈Being Glue〉為業界實務演講/文章(noidea.dog/glue),非學術文獻,本文以實務觀點引述,未列入正式參考文獻;「資深做叫 leadership、資淺做被說不夠 technical」為其論點的概括轉述。第 22(Bateson et al.)、23(Argyris)項為教科書級經典,本次未重新核對卷期頁碼;Bateson 的 double bind 原始脈絡為臨床心理學,本文僅借用其「矛盾指令+矛盾不可討論」的結構,已在參考文獻說明中標示。另有一篇 2026 年的 arXiv preprint 以行為實驗發現受試者願付出個人成本懲罰使用 LLM 的同儕(懲罰強度隨使用強度遞增),與第 21 項結論方向一致,但因尚未經同儕審查,本文未引用。
> 5. 第 5(Mockus 2010)、6(Mockus 2009)項的書目資訊(會議、頁碼)見於多篇論文的引用列表且相互一致,但本次未開啟 ACM 原頁逐項核對 DOI;投正式場合前建議自行核對。
> 6. 第 2(Darley & Latané)、3(Bryar & Carr)、17(Hood)、18(Pierce et al.)項為教科書級經典文獻或知名出版品,本次未逐一重新核對 DOI;投正式場合前建議自行核對卷期頁碼。
> 7. Weinberg「每多一個並行專案損耗約 20% 時間」出自《Quality Software Management, Vol. 1: Systems Thinking》(Dorset House, 1992),為實務經驗法則而非嚴格實證,本文已在行文中明示其性質,未列入正式參考文獻。
> 8. Apple DRI 制度廣見於業界報導與二手描述(如 Fortune 對 Apple 管理制度的報導),但 Apple 官方並無公開的一手文件;本文以業界通識表述,未綁定特定出處。
> 9. 「RACI 的 A 欄只能有一人」為專案管理實務通則,見於 PMI 等機構的教材,本文未綁定特定論文。
> 10. 「collective code ownership」為極限編程(XP)實務傳統(Beck 等人),本文作為概念脈絡提及,未綁定特定論文。「單一 owner 是科層解、放任式共同持有是市場解、專業解是第三條路」為本文以 Freidson 三邏輯框架推導出的論證,非 Freidson 原文的分類;Linux subsystem maintainer 與開源 maintainership 為本文自舉的例證。文中提及的 Ostrom 公共財治理研究(*Governing the Commons*, 1990)本次未逐項核對,以概念類比方式提及,未列入正式參考文獻。
> 11. 專業主義文獻線(第 34–37 項)的查證狀態:第 37 項(Fournier)之卷期頁碼(The Sociological Review, 47(2), 280–307)與 DOI(10.1111/1467-954X.00173)已核對,「紀律邏輯」「遠距治理」「自主的條件已被編碼進專業勝任」等表述均對照論文摘要原文轉述。第 36 項(Evetts)的 organizational / occupational professionalism 區分與「discourse of control」定性已由多筆二手來源交叉核對,**但本次未能核對到原頁的卷期頁碼,故僅列卷期不列頁碼**;另需注意 Evetts 在 2009、2011、2013 年的多篇著作反覆申論同一區分,不同論文引用的年份不一,投正式場合前建議選定一個版本並核對。第 34 項(Freidson)、第 35 項(Abbott)為該領域的標準專著,本次未重新核對版次與頁碼。
> 12. 「結構技師在沒有親手畫的圖上蓋章」「機長為整架飛機負責」等類比,以及「責任是專業的,權威是科層的」「AI 對專業的威脅是解除職業對勝任的定義權」「專業主義同時是組織最省力的紀律工具,也是員工唯一的抵抗語言」等表述,均為本文以 Freidson、Evetts、Fournier 的框架推導出的自身論證,非引用。「不夠 technical 是管轄權裁決在績效面談裡的形態」為本文對 Abbott 框架的延伸應用。
> 13. 「把決策委託給演算法是建造 accountability sink 的便利方式」一句,為書評圈對 Davies 論點的延伸詮釋(Davies 書中確有將演算法決策與 accountability sink 連結的討論),本文以作者自己的論證推進表述,未直接掛引號。「百分比報表製造會計幻覺」「中間人的產出天生是反事實的」「對組織最稀缺角色的系統性折舊」等為本文自己的論證,非引用。
