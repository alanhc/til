# 當組織把你設計成備援:單點故障恐懼、過載,與成就感的消失

## 引言:N+1 冗餘的隱形帳單

在基礎設施工程裡,N+1 redundancy 是常識:任何關鍵系統都不能只靠一台機器,一台掛了,備援要能無縫接手。這個原則救過無數次生產環境,沒有人會質疑它。

問題是,當組織把同樣的邏輯套用在「人」身上,帳單卻記在另一個地方——記在每個工程師的成就感上。

軟體工程界用 bus factor 來量化這個風險:一個專案裡有多少人「被公車撞到」之後,專案就會停擺。bus factor 為 1,就是單點故障。理性的組織會盡一切努力拉高這個數字:輪調、cross-training、強制知識分享、每個系統至少兩個人 cover、每個人至少 cover 兩個系統。

這些措施每一項單獨看都對。但把它們加總起來,再疊上大企業永遠做不完的待辦清單,你會得到一種奇特的工作型態:**每個人都負責很多事,但沒有一件事真正屬於任何人。** 你是三個系統的備援、五個專案的聯絡窗口、無數張 ticket 的 assignee——然後某天你發現,你已經很久沒有「完成」過任何東西了。

這篇文章想論證:成就感的流失不是個人抗壓性問題,而是兩股組織設計力量疊加的結構性結果——**冗餘設計消滅了任務的完整性,過載消滅了進展的感受**。而且這兩件事,學術文獻各自都研究了幾十年。

## 第一堵牆:冗餘設計如何拆解「你的工作」

### 成就感的來源:工作特徵模型

要理解成就感為什麼消失,得先知道它從哪裡來。Hackman & Oldham (1976) 的工作特徵模型(Job Characteristics Model)是這個領域的基石,它指出內在動機來自五個工作特徵:技能多樣性、任務完整性(task identity)、任務重要性、自主性、回饋。

其中 task identity 的定義值得逐字看:「完成一件完整的、可辨識的工作的程度——從頭到尾做完一件事,並看到可見的成果。」

現在對照冗餘導向的組織設計:當你是某系統的「第二個知道的人」,你永遠不是從頭到尾做完它的人。當知識被刻意打散到多人身上,「可見的成果」也被打散了——沒有任何一個成果能指著說「這是我做的」。冗餘設計在系統層面創造韌性的同時,在個人層面系統性地摧毀 task identity。

### 冗餘的已知代價:文獻怎麼說

這不只是感受,作業研究與組織理論早有量化證據:

- **Cross-training 的邊際效益遞減。** Eitzen & Panton (2004) 研究維持員工跨技能水準的排程問題,發現當任務種類與所需技能數增加時,多能工整合的效益會被侵蝕——技能廣度是有成本的,而且成本隨廣度非線性上升。
- **技能配置錯位傷害滿意度。** Eiselt & Marianov (2008) 指出,員工與工作的錯誤配對會導致滿意度顯著下降,進而透過缺勤、申訴、勞資關係惡化反噬效率。被指派去「backup 一個你不熟的系統」正是一種制度化的錯位。
- **功能性冗餘製造角色模糊。** 矩陣式組織中刻意設計的技能重疊(functional redundancy),若缺乏清楚的權責切分,直接產生 role ambiguity——而 Jackson & Schuler (1985) 與 Abramis (1994) 的後設分析都確認,角色模糊與工作滿意度呈中度負相關。

換句話說:組織買韌性的貨幣,是個人的角色清晰度與任務完整性。這筆交易在風險管理報表上看得到收益,在員工的內在動機帳戶上看不到支出——直到離職率反映出來。

### 一個工程師都懂的類比

硬體冗餘裡,備援機器平常是 idle 或跑低負載的,這是冗餘的成本,大家都接受。但組織對「人的冗餘」卻不肯付這個成本:它要你當備援,又要你 100% utilization。結果是每個人同時扮演多個系統的 standby,而每個 standby 角色都需要持續投入維持知識新鮮度(context 會過期,code base 會演進)。你付出了冗餘的維護成本,卻沒有任何一個系統給你完整的 ownership 回報。

## 第 1.5 堵牆:R&R 模糊——當每件事都有兩個 owner,就沒有 owner

### 五十年的研究線:從 Kahn 到 Tubre & Collins

角色模糊(role ambiguity)不是新概念。Kahn et al. (1964) 的《Organizational Stress: Studies in Role Conflict and Ambiguity》開啟了這個領域;Rizzo, House & Lirtzman (1970) 隨後開發了沿用至今的測量量表,將 role ambiguity 定義為「缺乏關於職位期望的必要且清楚的資訊」——你不確定自己的職責是什麼、被期待哪些行為、成功的標準在哪裡。此後約 85% 的角色壓力研究都使用這套量表,累積了半世紀的實證。

後設分析的結論高度一致,而且有一個對本文論點至關重要的不對稱:Tubre & Collins (2000) 更新 Jackson & Schuler (1985) 的後設分析後發現,role ambiguity 與工作績效呈顯著負相關(r = −.21),但 role conflict 與績效的關係微弱到可忽略(r = −.07)。翻譯成日常語言:**「要求彼此矛盾」還能撐,「不知道自己到底負責什麼」才是真正的績效殺手。** 在滿意度端,Jackson & Schuler (1985) 與 Abramis (1994) 確認角色模糊與工作滿意度呈中度負相關;Schmidt et al. (2014) 的後設分析更進一步,確認它與憂鬱症狀的連結——傷害不止於績效報表,而直達心理健康。

Jackson & Schuler (1985) 還提出一個對工程組織特別刺眼的假說:績效高度依賴「與他人互動」的職位,比績效取決於「完成明確任務」的職位更容易經歷角色模糊;且工作越複雜,績效與評價之間的關聯越不清楚。系統整合、跨團隊協調、project team——這些正是互動密集、產出難以歸屬的角色原型。

### 備援制度是制度化的角色模糊

現在把這條研究線接回冗餘設計,因果鏈變得很清楚:

1. **Primary/backup 的責任邊界天然模糊。** 當系統 X 有一位 primary 和一位 backup,「backup 該投入多少」「哪些決定 backup 可以自己做」「出事時誰負責」幾乎從未被明文定義。組織理論早就指出,矩陣式組織中刻意設計的功能性冗餘若缺乏權責切分,直接產生角色模糊——而備援制度正是最普遍、最不被明文管理的功能性冗餘。
2. **「共同負責」在實務上退化為「沒人負責」。** 社會心理學的社會性懈怠(social loafing; Latané, Williams & Harkins, 1979)與責任分散(diffusion of responsibility)研究顯示,當產出無法歸屬到個人,個體的投入與當責感會系統性下降。這不是道德瑕疵,是可預測的心理機制。工程界的老話「兩個人的 on-call 等於沒有 on-call」有五十年的實驗心理學背書。
3. **模糊回頭放大過載的傷害。** 挑戰-阻礙框架中,role ambiguity 被一致歸類為純阻礙型壓力源(hindrance stressor)——它沒有任何激勵成分。當你的工作清單很長(overload)但每項的責任邊界清楚,那還可能是挑戰;當清單很長**且**每項都不確定自己算不算真正的 owner,阻礙成分就佔滿了全部。這解釋了為什麼同樣忙碌,有些團隊士氣高昂、有些團隊集體倦怠:差別不在工時,在 R&R 的清晰度。

於是三堵牆連成一個結構:冗餘設計拆掉 task identity(第一堵),同時必然製造 R&R 模糊(第 1.5 堵),而模糊把過載從「可能的挑戰」轉化為「純粹的阻礙」(第二堵)。成就感不是被單一因素殺死的,是被這條因果鏈絞殺的。

## 第二堵牆:過載如何消滅「進展感」

### Role overload 與它的後設分析

Role overload——被期待做的事超過時間與資源允許——是組織行為學裡 role stress 三型之一(另兩型是角色模糊與角色衝突)。後設分析的圖像是一致的:Bowling et al. (2015) 對 workload 的後設分析、Eatough et al. (2011) 對 role stressors 與組織公民行為的後設分析、Gilboa et al. (2008) 對工作需求壓力源與績效的後設分析,都指向過載透過心理壓力(psychological strain)侵蝕滿意度與表現。Ford et al. (2011) 進一步確認心理壓力變項與各類工作績效指標呈中至強度負相關。

值得誠實面對的是,文獻裡 role overload 的直接效果其實是混合的——挑戰-阻礙壓力源框架(challenge-hindrance framework; Podsakoff et al., 2007)指出,過載同時含有挑戰成分(可能激發動機)與阻礙成分(製造耗竭)。但這個框架反而強化了本文的論點:**決定過載是挑戰還是阻礙的關鍵,正是任務是否完整、可完成、有回饋。** 十件有頭有尾的事是挑戰;三十件永遠處於 30% 完成度的事是純粹的阻礙。

### Attention residue:碎片化的認知稅

Leroy (2009) 發表於 Organizational Behavior and Human Decision Processes 的經典研究提出了 attention residue(注意力殘留):當你在任務 A 未完成時切換到任務 B,一部分認知資源會持續黏在 A 上,實驗顯示這顯著降低 B 的表現——而且任務越是未完成、越有時間壓力,殘留越重。這篇論文被引用超過五百次,後續研究(Mark et al., 2016; Bailey & Konstan, 2006)確認數位中斷會增加重新聚焦的時間與主觀壓力。

把這個發現放回冗餘組織的日常:當你是五個系統的備援,你的一天就是五種 context 的連續切換,而且每一個 context 都永遠處於「未完成」狀態——因為備援的本質就是沒有完成的一天。attention residue 不是偶發的干擾,而是這種工作設計的**穩態**。

### Progress Principle:成就感的最小單位

Amabile & Kramer (2011) 分析了 238 位知識工作者的近 12,000 篇工作日誌,得到一個簡單到殘酷的結論:內在工作生活(inner work life)最強的正向驅動力,是「在有意義的工作上取得進展」——哪怕是小進展。反過來,最強的負向事件是挫折(setbacks)與阻力。

過載 + 碎片化的組合,正好把「進展」變成統計上的稀有事件。你每天都很忙,但每件事都只推進了一點點,而且推進的部分明天可能被改需求歸零。日誌上寫滿了活動(activity),卻找不到進展(progress)。Amabile 的資料說,這就是內在動機死亡的方式——不是一次大挫敗,而是持續缺乏可感知的前進。

## 隱藏的第三堵牆:分工不均——過載為什麼精準砸在可靠者頭上

前兩堵牆解釋了過載與模糊的傷害,但還有一個問題沒回答:過載從來不是均勻分布的。每個工程團隊都知道那個現象——工作像水一樣流向最不會拒絕、最能把事做完的人。這不是主管偏心,是有實驗證據的分配機制。

### 請求流向預期會說「好」的人

Babcock, Recalde, Vesterlund & Weingart (2017) 發表於 American Economic Review 的實驗研究,考察「大家都希望別人去做」的任務(寫報告、參加委員會、各種 glue work)如何被分配。他們的發現以性別為切入點:女性比男性更常自願承接、更常被要求承接、也更常答應承接這些低升遷價值(low-promotability)任務,而核心驅動因素是一個信念——「大家相信她會答應」。研究者甚至坦承,他們自己需要找人做非升遷型任務時,也傾向去找預期會說好的人。

機制的一般形式比性別面向更普遍:**任務請求系統性地流向拒絕成本最高、答應機率最大的人。** 在工程組織裡,這個人就是那位最可靠的資深工程師——每一次準時交付都在訓練整個組織把下一件事也丟給他。而 Babcock 等人指出,低升遷任務的績效改善回報天然低於高升遷任務:接下越多 glue work,可見產出佔工時的比例越低,職涯反而越慢。「能者多勞」的下半句,文獻已經寫好了:多勞者不多得。

### 公平理論:不均感受如何轉化為行為

Adams (1963, 1965) 的公平理論(equity theory)是分配正義研究的源頭:員工以「自己的投入/產出比」與參照對象比較來判斷公平,投入包括努力、時間、技能與犧牲,產出包括薪酬、升遷與認可。感知到不公平(underpayment inequity)的可預測後果是不滿意、降低投入,或離開——組織正義研究(Greenberg, 1990; Colquitt et al., 2001)半世紀來反覆確認這條鏈。

社會心理學還補了一個更尖銳的機制:Kerr (1983) 的實驗顯示,當有能力的成員發現自己在替搭便車者扛工作時,會刻意收回努力以避免成為「冤大頭」(sucker effect)。換言之,分工不均不需要等到離職才造成損失——它先讓最有生產力的人主動降速,作為一種理性的自我保護。

### 與冗餘設計的惡性呼應

分工不均和第一堵牆之間存在一個特別惡毒的迴圈:**最可靠的人會被指派最多的備援角色。** 可靠性讓知識向他集中,知識集中讓他成為組織最恐懼的單點故障,於是組織一邊最依賴他、一邊最急著攤薄他——他同時承受最重的主線負載、最多的備援職責、最頻繁的「你順便看一下」。組織風險管理的目光鎖定在他身上,但給出的處方(更多 cross-training 責任、更多知識轉移會議)全部是加法。他的 input/output 比率惡化得最快,而公平理論預測的三個出口——不滿、降速、離開——每一個都正中組織的要害。

分工不均因此不是管理疏失的雜訊,而是前兩堵牆的放大器:它保證過載以最傷的方式集中,保證 R&R 模糊的成本由最少數人吸收,並保證離職名單的第一行是組織最輸不起的名字。

## 第四堵牆:絕對服從——當自主性被沒收

前三堵牆都關於工作「怎麼被切、被分」;最後一堵牆關於工作「怎麼被管」。風險趨避的組織不只切碎任務,還傾向收緊決策權——標準流程、層層簽核、「照做就對了」。這種絕對服從文化對成就感與留任的傷害,有兩條成熟的研究線。

### 自主性是基本心理需求,不是福利

Deci & Ryan 的自我決定理論(Self-Determination Theory, SDT)是過去四十年動機研究的主導框架,它將自主(autonomy)——體驗到自己是行為發起者、行為反映真實意志而非外部壓力——列為三大基本心理需求之一,與能力感、歸屬感並列。Van den Broeck et al. (2016) 的後設分析確認:需求被滿足時,人們更自主地被激勵、表現更好、福祉更高;需求受挫(need frustration)則與離職意圖、缺勤等指標清楚連結。

SDT 對絕對服從文化最尖銳的診斷,是「受控型動機」(controlled motivation)這個概念。Gagné & Deci (2005) 與 Deci, Olafsen & Ryan (2017) 的系統回顧顯示:受控型動機與較差的福祉、更高的焦慮、情緒耗竭與離職意圖相關——而且關鍵不在動機的「量」:**一個人可以在受控狀態下高度賣力,卻仍然燃燒殆盡,因為這種動機燃料在心理上是腐蝕性的。** 這解釋了絕對服從組織裡一個常見的悖論:團隊看起來很拼、產出不差,離職率卻居高不下——儀表板上的動機量測不出動機的品質。

值得注意的是,自主性正是 Hackman & Oldham 五個核心工作特徵之一(第一堵牆),所以這堵牆與第一堵在理論上同源:冗餘設計沒收 task identity,服從文化沒收 autonomy,五根成就感支柱倒了兩根。

### 威權領導的實證:華人組織自己的研究

「絕對服從」在領導研究裡有精確的學術對應:家長式領導(paternalistic leadership)三元模型中的威權領導(authoritarian leadership)維度——這個框架由鄭伯壎(Cheng Bor-Shiuan)等台灣學者發展(Cheng et al., 2004),後成為華人組織研究的主導理論,對本文讀者格外切身。

實證圖像相當一致。以台灣連鎖服務業員工為樣本的結構方程研究發現,威權領導與離職意圖顯著正相關,仁慈與德行領導則相反。跨研究層面,Bedi (2020) 的後設分析直接證實:威權領導與多數正向員工結果(如工作滿意度、組織承諾)呈負向關聯、與離職意圖等負向結果呈正向關聯,而仁慈與德行領導的方向恰好相反;Hiller et al. (2019) 涵蓋 152 個研究、14 個國家、總樣本近七萬人的多語言後設分析,則從更大的樣本基礎確認了威權與仁慈兩維在各項員工結果上一貫分歧的模式。此外,對創新的後設分析(69 個中國樣本研究)也顯示威權領導與員工創新負相關(r = −0.151),而仁慈(r = 0.396)與德行(r = 0.329)領導正相關。

誠實起見,必須記錄反面證據:一項中國企業的縱貫研究(六個月後追蹤**實際**離職而非意圖)發現威權領導無法直接預測實際離職,其效果受分配正義與程序正義調節。這個 nuance 其實深化了論點:威權製造的是離職**意圖**,但意圖是否兌現取決於公平感與外部機會——也就是說,絕對服從文化在勞動市場緊的時候看不出代價,一旦外部選項出現(例如附近開了新的外商研發中心),累積的意圖會集中兌現。

### Exit, Voice, Loyalty:服從文化只留下一個出口

把這堵牆與離職章節接起來的最優雅框架,是 Hirschman (1970) 的經典三分:組織成員面對不滿只有三種反應——離開(exit)、發聲(voice)、忠誠(loyalty)。絕對服從文化的定義性特徵,就是封鎖 voice:質疑決策被視為挑戰權威,回饋管道形同虛設,組織沉默(organizational silence; Morrison & Milliken, 2000)成為集體均衡。當 voice 被封死,所有不滿只剩一個出口。組織以為它買到的是紀律與執行力,實際上它只是把異議的表達形式從「會議室裡的爭論」換成了「離職信」——而後者不附帶任何可供改進的資訊。

這與第一堵牆形成完整的閉環:風險趨避讓組織既把工作切碎(降低對個人的依賴),又把決策收緊(降低個人犯錯的空間)。兩個動作都在防禦「人的不可靠」,兩個動作也都在沒收讓人願意留下的東西。

## 交會點:為什麼這兩堵牆會同時出現

冗餘設計與過載不是巧合地共存,它們是同一個組織邏輯的兩面:

1. **風險趨避產生冗餘需求。** 組織害怕單點故障(合理),所以要求每個關鍵知識至少兩人持有。
2. **成本壓力禁止真正的冗餘。** 真正的冗餘需要 headcount buffer,但預算邏輯要求每個人滿載。於是「冗餘」不是加人,而是把現有的人攤薄——每人多 cover 幾個領域。
3. **攤薄製造碎片化,碎片化製造 residue,residue 降低效率,降低的效率讓待辦清單更長。** 這是一個自我強化的迴圈。
4. **量化偏誤讓問題隱形。** bus factor、coverage、utilization 都可量化,會出現在風險報告裡;task identity、進展感、attention residue 不可量化,只會出現在離職面談裡。組織優化它能測量的東西——這是 Goodhart's law 在組織設計上的又一次應驗。

諷刺的是,這個迴圈最終反而**降低**了組織想要的韌性:過載與低成就感是離職意圖的可靠預測因子(Boswell et al., 2004),而每一次離職都讓 bus factor 重新歸零,觸發新一輪更急迫的知識攤薄。組織用犧牲個人成就感的方式對沖單點故障,結果製造出更多的單點故障。

## 終點站:文獻早就算出這條鏈的出口

如果前面三堵牆的分析成立,它應該有一個可驗證的預測:這種工作設計會系統性地推高離職率。離職研究恰好是組織行為學裡後設分析最密集的領域,而證據完全吻合。

### 通用路徑:壓力源 → 滿意度 → 離職意圖 → 離職

Tett & Meyer (1993) 確立了離職研究的標準路徑模型:工作滿意度與組織承諾降低 → 離職意圖升高 → 實際離職。本文討論的所有壓力源,都是透過這條路徑通往出口的。兩代最全面的後設分析——Griffeth, Hom & Gaertner (2000) 與 Rubenstein et al. (2018)——一致確認工作滿意度是自願離職最可靠的前因之一,後者更把 person-organization fit 列為中等效果量的預測因子:當組織的設計邏輯(把人當備援)與個人的動機結構(需要完整任務與進展感)根本不相容,fit 的惡化不是意外,是設計結果。

更精確的是 Podsakoff et al. (2007) 的區分:阻礙型壓力源與離職意圖及實際離職**正**相關,挑戰型壓力源反而與離職**負**相關。這給了本文論證一個可怕的推論——同樣的高工作量,在 R&R 清晰的組織裡可能留住人(挑戰),在 R&R 模糊的組織裡加速趕走人(阻礙)。決定員工去留的不是工作量本身,而是組織設計把工作量呈現為哪一種壓力源。

### IT 專屬證據:三堵牆在工程師樣本裡被一次驗證

對工程組織而言最有分量的一項證據,是 Moore (2000) 發表於 MIS Quarterly 的結構方程模型研究——它幾乎是本文四堵牆框架的實證預演。Moore 分析 270 名 IT 專業人員,在同一個模型裡測試四個影響工作耗竭(work exhaustion)的因素:工作過載、角色模糊與角色衝突、缺乏自主性、缺乏獎酬,而工作耗竭再部分中介這些因素對離職意圖的效果。結果有兩點對本文格外關鍵:其一,耗竭程度越高的技術工作者,離職意圖越強;其二,在四個因素中,**工作過載是耗竭最強的貢獻者**。換言之,本文的第二堵牆(過載)、第 1.5 堵牆(角色模糊/衝突)、第四堵牆(自主性)並非各自獨立的推論,它們早在二十五年前就被放進同一個 IT 樣本的同一個模型裡驗證,而過載正如本文所主張,是其中最沉重的一根。

Joseph et al. (2007) 隨後發表於 MIS Quarterly 的後設分析結構方程模型研究,涵蓋 1985–2005 年的 IT 離職文獻,進一步鞏固了這條鏈:role ambiguity 與 role conflict 透過降低工作滿意度提高離職意圖,workload 則經由 work exhaustion 走向同一個出口。兩篇合起來,把本文從理論推演升級為 IT 領域有二十年實證背書的既有結論。

換句話說:本文的論證不需要推測終點,IT 離職文獻已經用二十年的量化證據畫出了這條鏈的出口。

### 反諷的完成式

現在可以把第「交會點」一節的反諷補完整。組織用知識攤薄對沖單點故障 → 攤薄製造角色模糊與過載 → 兩者透過滿意度路徑推高離職 → 每次離職都摧毀既有的知識冗餘、觸發更急迫的攤薄。離職研究還補了一刀:社會比較研究顯示,當離開的同事與留下者在技術能力與背景上相似時,留下者的離職可能性更高——離職會傳染,而且在同質性高的工程團隊裡傳染得最快。組織風險管理最害怕的骨牌效應,正是由它自己的風險管理措施起頭的。

## 出路:把冗餘的成本記在正確的帳上

本文不主張放棄冗餘——單點故障的風險是真的。主張的是三件事:

**第一,冗餘要付費,而且要顯性付費。** 硬體備援佔預算科目,人的備援也應該佔 capacity 科目。如果一個人要當三個系統的備援,他的主要任務負載就該打七折,而不是疊加。拒絕付這筆錢的組織,實際上是在用員工的內在動機做無息貸款。

**第二,冗餘的單位應該是「完整任務」,不是「碎片知識」。** 與其讓五個人各懂一個系統的 20%,不如用輪值制(rotation with full ownership)讓每個人在一段時間內完整擁有一個系統——task identity 得以保留,知識轉移發生在交接時而非稀釋在日常。這也是 Leroy 研究的直接應用:減少切換頻率、讓任務有明確的完成點,attention residue 才有機會清空。

**第三,把「進展感」當成一級指標管理。** Amabile 的研究給了管理者一份清單:清除阻力、給予自主、讓小勝利可見。在工程組織裡,這可以具體到「每個人每週至少有一件能標記為 done 的完整事項」——聽起來卑微,但文獻說這正是內在動機的最小維生劑量。

單點故障值得害怕。但一個組織如果解決它的方式,是讓每個成員都感覺不到自己完成過任何事,那它只是把故障從系統層搬到了人心層——而後者的 MTTR,長得多。

---

## 參考文獻

- Abramis, D. J. (1994). Work role ambiguity, job satisfaction, and job performance: Meta-analyses and review. *Psychological Reports*, 75(3), 1411–1433.
- Adams, J. S. (1963). Towards an understanding of inequity. *Journal of Abnormal and Social Psychology*, 67(5), 422–436.
- Adams, J. S. (1965). Inequity in social exchange. In L. Berkowitz (Ed.), *Advances in Experimental Social Psychology* (Vol. 2, pp. 267–299). Academic Press.
- Babcock, L., Recalde, M. P., Vesterlund, L., & Weingart, L. (2017). Gender differences in accepting and receiving requests for tasks with low promotability. *American Economic Review*, 107(3), 714–747.
- Bedi, A. (2020). A meta-analytic review of paternalistic leadership. *Applied Psychology: An International Review*, 69(3), 960–1008.
- Cheng, B.-S., Chou, L.-F., Wu, T.-Y., Huang, M.-P., & Farh, J.-L. (2004). Paternalistic leadership and subordinate responses: Establishing a leadership model in Chinese organizations. *Asian Journal of Social Psychology*, 7(1), 89–117.
- Deci, E. L., Olafsen, A. H., & Ryan, R. M. (2017). Self-determination theory in work organizations: The state of a science. *Annual Review of Organizational Psychology and Organizational Behavior*, 4, 19–43.
- Deci, E. L., & Ryan, R. M. (2000). The "what" and "why" of goal pursuits: Human needs and the self-determination of behavior. *Psychological Inquiry*, 11(4), 227–268.
- Gagné, M., & Deci, E. L. (2005). Self-determination theory and work motivation. *Journal of Organizational Behavior*, 26(4), 331–362.
- Hiller, N. J., Sin, H.-P., Ponnapalli, A. R., & Ozgen, S. (2019). Benevolence and authority as WEIRDly unfamiliar: A multi-language meta-analysis of paternalistic leadership behaviors from 152 studies. *The Leadership Quarterly*, 30(1), 165–184.
- Hirschman, A. O. (1970). *Exit, Voice, and Loyalty: Responses to Decline in Firms, Organizations, and States*. Harvard University Press.
- Morrison, E. W., & Milliken, F. J. (2000). Organizational silence: A barrier to change and development in a pluralistic world. *Academy of Management Review*, 25(4), 706–725.
- Van den Broeck, A., Ferris, D. L., Chang, C.-H., & Rosen, C. C. (2016). A review of self-determination theory's basic psychological needs at work. *Journal of Management*, 42(5), 1195–1229.
- Colquitt, J. A., Conlon, D. E., Wesson, M. J., Porter, C. O. L. H., & Ng, K. Y. (2001). Justice at the millennium: A meta-analytic review of 25 years of organizational justice research. *Journal of Applied Psychology*, 86(3), 425–445.
- Greenberg, J. (1990). Organizational justice: Yesterday, today, and tomorrow. *Journal of Management*, 16(2), 399–432.
- Kerr, N. L. (1983). Motivation losses in small groups: A social dilemma analysis. *Journal of Personality and Social Psychology*, 45(4), 819–828.
- Amabile, T. M., & Kramer, S. J. (2011). *The Progress Principle: Using Small Wins to Ignite Joy, Engagement, and Creativity at Work*. Harvard Business Review Press.
- Bailey, B. P., & Konstan, J. A. (2006). On the need for attention-aware systems. *Computers in Human Behavior*, 22(4), 685–708.
- Boswell, W. R., Olson-Buchanan, J. B., & LePine, M. A. (2004). Relations between stress and work outcomes. *Journal of Vocational Behavior*, 64(1), 165–181.
- Bowling, N. A., Alarcon, G. M., Bragg, C. B., & Hartman, M. J. (2015). A meta-analytic examination of the potential correlates and consequences of workload. *Work & Stress*, 29(2), 95–113.
- Eatough, E. M., Chang, C.-H., Miloslavic, S. A., & Johnson, R. E. (2011). Relationships of role stressors with organizational citizenship behavior: A meta-analysis. *Journal of Applied Psychology*, 96(3), 619–632.
- Eiselt, H. A., & Marianov, V. (2008). Employee positioning and workload allocation. *Computers & Operations Research*, 35(2), 513–524.
- Eitzen, G., Panton, D., & Mills, G. (2004). Multi-skilled workforce optimisation. *Annals of Operations Research*, 127(1), 359–372.
- Ford, M. T., Cerasoli, C. P., Higgins, J. A., & Decesare, A. L. (2011). Relationships between psychological, physical, and behavioural health and work performance: A review and meta-analysis. *Work & Stress*, 25(3), 185–204.
- Gilboa, S., Shirom, A., Fried, Y., & Cooper, C. (2008). A meta-analysis of work demand stressors and job performance. *Personnel Psychology*, 61(2), 227–271.
- Griffeth, R. W., Hom, P. W., & Gaertner, S. (2000). A meta-analysis of antecedents and correlates of employee turnover: Update, moderator tests, and research implications for the next millennium. *Journal of Management*, 26(3), 463–488.
- Joseph, D., Ng, K.-Y., Koh, C., & Ang, S. (2007). Turnover of information technology professionals: A narrative review, meta-analytic structural equation modeling, and model development. *MIS Quarterly*, 31(3), 547–577.
- Moore, J. E. (2000). One road to turnover: An examination of work exhaustion in technology professionals. *MIS Quarterly*, 24(1), 141–168. [SEM, N=270; work overload 為 work exhaustion 最強前因,耗竭部分中介離職意圖]
- Rubenstein, A. L., Eberly, M. B., Lee, T. W., & Mitchell, T. R. (2018). Surveying the forest: A meta-analysis, moderator investigation, and future-oriented discussion of the antecedents of voluntary employee turnover. *Personnel Psychology*, 71(1), 23–65.
- Tett, R. P., & Meyer, J. P. (1993). Job satisfaction, organizational commitment, turnover intention, and turnover: Path analyses based on meta-analytic findings. *Personnel Psychology*, 46(2), 259–293.
- Hackman, J. R., & Oldham, G. R. (1976). Motivation through the design of work: Test of a theory. *Organizational Behavior and Human Performance*, 16(2), 250–279.
- Kahn, R. L., Wolfe, D. M., Quinn, R. P., Snoek, J. D., & Rosenthal, R. A. (1964). *Organizational Stress: Studies in Role Conflict and Ambiguity*. Wiley.
- Latané, B., Williams, K., & Harkins, S. (1979). Many hands make light the work: The causes and consequences of social loafing. *Journal of Personality and Social Psychology*, 37(6), 822–832.
- Rizzo, J. R., House, R. J., & Lirtzman, S. I. (1970). Role conflict and ambiguity in complex organizations. *Administrative Science Quarterly*, 15(2), 150–163.
- Schmidt, S., Roesler, U., Kusserow, T., & Rau, R. (2014). Uncertainty in the workplace: Examining role ambiguity and role conflict, and their link to depression—A meta-analysis. *European Journal of Work and Organizational Psychology*, 23(1), 91–106.
- Tubre, T. C., & Collins, J. M. (2000). Jackson and Schuler (1985) revisited: A meta-analysis of the relationships between role ambiguity, role conflict, and job performance. *Journal of Management*, 26(1), 155–169.
- Jackson, S. E., & Schuler, R. S. (1985). A meta-analysis and conceptual critique of research on role ambiguity and role conflict in work settings. *Organizational Behavior and Human Decision Processes*, 36(1), 16–78.
- Leroy, S. (2009). Why is it so hard to do my work? The challenge of attention residue when switching between work tasks. *Organizational Behavior and Human Decision Processes*, 109(2), 168–181.
- Mark, G., Iqbal, S. T., Czerwinski, M., Johns, P., & Sano, A. (2016). Neurotics can't focus: An in situ study of online multitasking in the workplace. *Proceedings of CHI 2016*.
- Podsakoff, N. P., LePine, J. A., & LePine, M. A. (2007). Differential challenge stressor–hindrance stressor relationships with job attitudes, turnover intentions, turnover, and withdrawal behavior: A meta-analysis. *Journal of Applied Psychology*, 92(2), 438–454.
- Örtqvist, D., & Wincent, J. (2006). Prominent consequences of role stress: A meta-analytic review. *International Journal of Stress Management*, 13(4), 399–422.
