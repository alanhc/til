---
sidebar_label: Bring-up
---

# Bring-up:新硬體從「不會動」到「能量產」的關鍵戰役

## 前言

在晶片與硬體產業,有一個時刻的張力不亞於火箭發射:tape-out 數個月後,第一批工程樣品(engineering sample)從封測廠送回實驗室,bring-up 團隊把晶片放上測試板、接上電源、按下開關。接下來幾小時到幾天內發生的事,將決定這顆花費數千萬甚至上億美元開發的晶片,是走向量產,還是走向 re-spin。

Bring-up 是整個產品開發流程中,設計與物理現實第一次正面對決的環節。模擬跑得再完整、formal verification 覆蓋率再高、FPGA prototype 驗得再久,都只是「模型對模型」的驗證;只有真實矽片在真實電路板上、以真實電壓與溫度運作時,才是最終的裁判。這篇文章以業界實務的角度,拆解晶片、板級與軟體三個層次的 bring-up 工作、常用的 debug 方法論、那些讓資深工程師半夜睡不著的常見坑,以及為什麼 bring-up 能力是硬體公司最稀缺的資產之一。

## Bring-up 在開發流程中的位置

以一顆 SoC 為例,典型的時間軸是:架構定義 → RTL 設計與驗證 → 實體設計(PD)→ tape-out → 晶圓製造(約 2–4 個月)→ 封裝測試 → 樣品回廠(silicon back)→ **bring-up 與 silicon validation** → 軟體整合 → 客戶送樣 → 量產(MP)。

注意 bring-up 的位置:它卡在「晶片回來」與「所有下游工作」之間。軟體團隊在等能開機的平台、驗證團隊在等能跑 pattern 的晶片、客戶在等送樣時程、業務在等量產承諾。晶片回來的那一天起,bring-up 就是整條產品線的 critical path——它多卡一週,產品上市就晚一週,而消費性電子的市場窗口往往以週計算。這也是為什麼各公司普遍把最資深、跨域能力最強的工程師投入 bring-up,並且常態性地日夜輪班(所謂的 "bring-up war room")。

更關鍵的是,bring-up 直接決定一個昂貴的商業決策:**要不要 re-spin**。先進製程的一次 full-mask re-spin,光罩成本動輒數百萬美元,加上 2–4 個月的製造週期;若只是 metal layer 的修改(metal fix / ECO spin)成本較低,但仍是以月為單位的延誤。Bring-up 做得快而徹底,公司才能盡早知道:這顆晶片能不能靠軟體 workaround 撐到量產?還是必須認賠改版?晚一週發現致命 bug,就是晚一週做決策,而競爭對手不會等你。

## 第一層:晶片 bring-up(Silicon Bring-up)

晶片 bring-up 的第一天,目標低到外人難以想像:**確認晶片沒有短路、電源拉得起來、時脈有在跑**。實務上的步驟大致如下。

**上電前檢查(pre-power checklist)。** 在通電之前,先用三用電表量各電源軌對地的阻抗,確認沒有 die-level 或封裝層級的短路。第一次上電通常用可設定電流上限的實驗室電源供應器(bench supply),把 current limit 設低,慢慢把電壓升上去,同時盯著電流表——異常的靜態電流(IDDQ)往往是第一個警訊,可能代表製程缺陷、latch-up,或 power domain 設計問題。

**電源與時脈的 sanity check。** 確認 PMIC 或板上的電源序列(power sequencing)符合 datasheet 要求,用示波器量測各電源軌的上電順序與 ramp 時間;接著確認晶振有起振、PLL 有 lock、reset 訊號的時序正確。業界經驗是:**bring-up 初期八成的「晶片完全沒反應」,root cause 都在電源、時脈、reset 這三件事**,而不是晶片本身的邏輯。

**建立 debug 通道。** 下一個里程碑是讓 JTAG(或 SWD)連上。一旦 debugger 能 halt CPU、讀寫暫存器與記憶體,bring-up 就從「盲人摸象」進入「有觀測手段」的階段。此時通常會先跑最小的 sanity test:讀 chip ID 暫存器、對 on-chip SRAM 做讀寫測試、確認中斷控制器基本運作。

**逐一驗證 IP block。** 接下來是有計畫的 per-IP validation:DDR 控制器(這幾乎永遠是最難的一關,牽涉 training、訊號完整性與時序邊界)、各高速介面(PCIe、USB、Ethernet SerDes 的 link training 與眼圖量測)、低速介面(I2C、SPI、UART)、多媒體與加速器模組。每個 IP 不只驗「會不會動」,還要掃 PVT corner——在不同電壓(±5–10%)、溫度(-40°C 到 125°C,依產品定位)下用 thermal chamber 做 shmoo plot,找出真正的操作邊界。一顆在室溫、標準電壓下正常的晶片,可能在低溫高壓的角落 corner 大量出錯,而那正是量產良率與現場退貨率的來源。

在這個階段,發現的每一個異常都會被登錄進 errata 清單,並分類為:可用軟體 workaround 繞過、需要 metal fix、或需要 full re-spin。這份 errata 文件會跟著晶片一輩子——你在任何一家 SoC 大廠的 datasheet 附錄看到的 errata sheet,都是當年 bring-up 團隊的血淚結晶。

## 第二層:板級 bring-up(Board Bring-up)

即使晶片本身沒問題,新設計的電路板也是一個獨立的風險來源。板級 bring-up 的核心,是把「layout 與 BOM 的假設」逐一對答案。

流程通常從**目視與阻抗檢查**開始:對照 BOM 確認關鍵料件沒放錯(尤其是阻值相近的電阻、極性元件的方向),量各電源軌阻抗。接著**分區上電**:許多團隊會刻意在 layout 上留 0 歐姆電阻或 jumper,讓各電源域可以獨立供電、獨立量測,一旦某一軌異常,可以立刻隔離範圍。

再來是**時脈樹與 reset 網路**的驗證,然後進入最花時間的部分:**訊號完整性(SI)與電源完整性(PI)**。DDR 走線的長度匹配是否如設計、高速差動對的眼圖是否張得開、電源軌在負載瞬變(load transient)下的 droop 是否在規格內、去耦電容的配置是否足夠。這些問題的表現往往極其詭異——「跑重載測試十分鐘後偶爾當機」這種症狀,root cause 可能是某顆 bulk capacitor 離電源 pin 太遠。

板級 bring-up 的一個實務重點是**改板決策**:第一版板子(EVT board)幾乎必然有 rework——飛線(blue wire)、換料、割線。Bring-up 團隊要把所有 rework 記錄下來,匯整成下一版 layout 的修改清單。EVT → DVT → PVT 每一版板子的迭代品質,直接取決於 bring-up 階段記錄的完整程度。

## 第三層:軟體/韌體 bring-up

硬體能動之後,戰場轉移到軟體:讓 bootloader 與作業系統第一次在這個平台上跑起來。以嵌入式 Linux 平台為例,典型的推進順序是一連串越來越大的里程碑:

第一個目標是 **ROM code 到 first-stage bootloader**:確認 boot strap pin 設定的開機來源(eMMC、SPI NOR、UART download)正確,ROM code 能載入並跳轉到 SPL。第二個目標是 **UART 印出第一個字元**——不要小看這件事,"first UART print" 在許多團隊是值得吃蛋糕慶祝的里程碑,因為它代表 CPU、時脈、UART controller、pinmux、板上的 level shifter 全部串通了。

接著是 **DDR 初始化**:移植並調校 DDR training code,這一步跨在硬體與軟體的交界上,通常需要 SI 工程師與韌體工程師並肩作戰。然後 **U-Boot 起來、能從儲存裝置載入 kernel**;再來是 **Linux kernel 開機到 shell**——這中間要寫 device tree、把各 driver 的 clock/reset/pinctrl 依賴串對、處理中斷路由。最後才是各周邊 driver 的逐一點亮:顯示、網路、USB、相機、音訊、電源管理(suspend/resume 往往是最後也最難纏的一關)。

手機業界說的「Android bring-up」就是這整條鏈再往上延伸:HAL、vendor partition、GPU driver、modem 整合,直到 CTS/VTS 過測。一個新 SoC 平台的完整軟體 bring-up,以人年計算是常態。

軟體 bring-up 還有一個常被低估的角色:**它是晶片 bug 的最大探測器**。很多 silicon bug 不是 validation pattern 抓到的,而是 kernel 在真實的並發、DMA、cache coherency 場景下踩出來的。軟體 bring-up 工程師回報的「這個 driver 在特定順序下會讀到髒資料」,追到最後常常是一條 RTL 的 bug——這也是為什麼 bring-up 階段軟硬體團隊必須坐在一起。

## Bring-up 的 debug 方法論

Bring-up debug 與一般軟體 debug 最大的差異在於:**你不能信任任何一層**。平常寫應用程式時,你假設 CPU 是對的、記憶體是對的、compiler 是對的;bring-up 時,從矽片、封裝、電路板、韌體到工具鏈,每一層都是嫌疑犯。因此方法論上有幾個核心原則。

**分層隔離(divide and conquer)。** 把系統切成可獨立驗證的層次,由下往上逐層建立信任:電源 → 時脈 → reset → JTAG → SRAM → DDR → boot → OS。每一層都用最小的測試確認後,才往上走。症狀出現時,第一個問題永遠是「這一層以下,我驗過了嗎?」

**改變一個變數。** 換板子、換晶片、換韌體版本、換溫度——一次只換一個。手上有多顆樣品與多塊板子時,交叉比對(這顆晶片在那塊板子上會不會重現?)是區分「晶片問題 vs. 板子問題 vs. 個體差異」最快的手段。

**善用觀測工具,並理解每種工具的盲區。** 示波器與邏輯分析儀看電氣層、protocol analyzer 看匯流排交易、JTAG debugger 看軟體狀態、on-chip trace(ETM/STM)看不能被打斷的即時行為、內建的 performance counter 與 error status 暫存器看晶片自己的告白。資深 bring-up 工程師的價值,一半在於知道「這個症狀該用哪個工具、量哪個點」。

**尊重統計。** 「偶爾發生」的 bug 是 bring-up 最昂貴的敵人。要建立自動化的壓力測試與 log 收集,讓失敗可以被統計:失敗率跟電壓有關嗎?跟溫度有關嗎?跟特定晶片個體有關嗎?一個 failure rate 對電壓的曲線,常常比十次人工重現更快指向 root cause。

## 常見的坑

每個做過幾次 bring-up 的工程師,都有自己的傷疤清單。以下是幾類出現頻率最高的:

**電源序列與 reset 時序。** datasheet 上寫的 power-up sequence 沒被板子滿足、reset 在電源穩定前就被放開、外部 PMIC 的預設 OTP 設定與晶片需求不符。症狀通常是「有時開得起來有時不行」,極難用功能測試定位。

**Strap pin 與預設值。** 開機模式、時脈來源、I/O 電壓由上電瞬間的 strap pin 電平決定,而板上某個外接元件在那一瞬間拉了不該拉的電平。這類問題的特徵是:單量每個訊號都對,合在一起就是不對。

**Pinmux 與 I/O 電壓域。** SoC 的每支腳位有多重功能,韌體把 pinmux 設錯,或 1.8V/3.3V 電壓域設定與板上實際不符——輕則不通,重則燒 I/O。

**時脈與 clock gating。** Driver 忘了開某個 upstream clock,存取該模組的暫存器直接 bus hang,CPU 完全卡死連 JTAG 都難救。這是嵌入式軟體 bring-up 的經典死法,對策是先讀懂 clock tree 再寫 driver。

**Cache 與 coherency。** DMA 寫入的資料,CPU 從 cache 讀到舊值;或 bring-up 初期為求簡單全關 cache,一切正常,開了 cache 之後各種詭異錯誤傾巢而出。

**「模擬跟矽片不一樣」。** RTL 模擬時的理想 reset 狀態、記憶體初始值為 X 或 0 的假設、類比 IP 的行為模型與真實電路的差距——這些縫隙就是 silicon bug 的藏身處。

## 為什麼 bring-up 重要:一個總結性的觀點

把前面的內容收攏,bring-up 的重要性可以歸納為四點。

**第一,它是唯一的真值時刻(moment of truth)。** 現代晶片開發把大量資源投在 pre-silicon verification,但驗證只能證明「設計符合模型」,不能證明「產品在物理世界可用」。Bring-up 是這條鴻溝上唯一的橋。

**第二,它坐在時程與金錢的槓桿點上。** Re-spin 的直接成本以百萬美元計,時程成本以月計,市場窗口的機會成本可能以產品線的生死計。Bring-up 的速度與徹底程度,直接決定這些決策的品質與時機。良好的 bring-up 不是「找到問題」而已,而是**盡早給出可信的判決**:能量產、能 workaround、或必須改版。

**第三,它定義了產品的真實規格。** 量產晶片的操作電壓、溫度範圍、時脈上限、errata 與 workaround 清單,全部來自 bring-up 與 validation 的實測數據。客戶拿到的 datasheet,本質上是 bring-up 報告的精煉版。

**第四,它鍛造稀缺的人才。** Bring-up 要求一個人同時看得懂示波器上的 ringing 和 kernel log 裡的 panic,能從一個「開不了機」的症狀,在電源、時脈、layout、韌體、RTL 之間做出正確的分診。這種跨域 debug 能力沒有捷徑,只能在一次次 bring-up 中累積——這也是為什麼在 SoC、伺服器、車用電子與手機公司,有實戰 bring-up 經驗的工程師始終供不應求。

## 給團隊的實務建議:好的 bring-up 從 tape-out 前開始

最後值得強調:bring-up 的成敗,七成在晶片回來之前就決定了。

在 tape-out 前,成熟的團隊會做這些準備:**撰寫 bring-up plan**,明列每個 IP 的驗證項目、順序、負責人、所需儀器與判準;**設計 for-bring-up 的硬體**——測試點、跳線、可隔離的電源域、備援的開機路徑、足夠的 debug 接口(不要為了省一個 UART 連接器,讓整個團隊在暗中摸索兩週);**在 FPGA 或 emulator 上預跑軟體**,讓 bootloader、DDR init code、基本 driver 在矽片回來前就已經寫好並驗過,晶片一到手就能直接開跑;**準備好自動化基礎建設**——電源控制、log 收集、溫控箱排程,讓壓力測試可以無人值守地跑整夜。

晶片回來後的每一天都極其昂貴。Bring-up 做得好的團隊,不是在那幾週特別英勇,而是在之前的幾個月特別紮實。

Bring-up 是硬體產品的接生過程:從一塊不會動的板子、一顆前途未卜的晶片,到一個能開機、能開發、能承諾量產的平台。它不浪漫,經常伴隨深夜的實驗室與焦慮的時程會議,但它是把數億元的設計投資轉換成真實產品的那道窄門——而守住這道門的能力,正是硬體公司之間真正的分水嶺。
