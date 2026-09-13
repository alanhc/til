# Android 年度版本升級方法論:Chip Vendor 的最大例行專案

> 系列文章之九。總覽請見《Chip Vendor 視角的 Android Build System》。

每年 Google 發新版 Android,chip vendor 就啟動一次「annual bringup」——把整個 BSP 搬到新版本,讓所有在售 SoC 平台能支援客戶的升級需求。這是把本系列所有主題(Soong、GKI、sepolicy、VINTF、簽章、xTS)一次全部踩過的總工程。本文整理方法論:評估、merge、bringup、收斂、認證,以及 GRF 這張免死金牌怎麼用。

---

## 一、時間軸與整體策略

Google 的節奏(大致):Q1–Q2 Developer Preview/Beta → Q3 正式發佈 + AOSP tag → 之後 QPR 季度更新。Chip vendor 的對應節奏:

```
Beta 期(Q2)      : 前哨評估——讀 release notes / CDD 草案,估工作量,GRF 決策
正式發佈(Q3)     : 主 merge + 公版 bringup 開跑
發佈後 2-4 個月    : 公版開機、功能收斂、xTS 首輪
發佈後 4-6 個月    : 公版全量 xTS 通過 → BSP release 給客戶
其後               : 支援客戶專案升級 + QPR 跟進
```

競爭現實:旗艦客戶希望新 Android 首發就有,你的 BSP release 時間直接影響商務。

---

## 二、Phase 0:評估(在寫任何 code 之前)

**必讀清單**,產出 gap 分析報告:

1. **CDD diff**:新舊版 CDD 對比,找新增的 MUST。特別注意硬體門檻類(performance class、記憶體要求、codec 要求)——這決定哪些舊平台**根本不該升**。
2. **VNDK/介面棄用清單**:哪些 HIDL 介面被移除、哪些機制退場(如 VNDK 在 15 的移除)、`BUILD_BROKEN_*` 逃生口哪些被收掉。
3. **Kernel 要求**:新版支援的 kernel 版本區間(launch 裝置的最低 kernel)、GKI/KMI 要求變化。**升 Android 不一定要升 kernel(GRF),但 launch 平台通常要**。
4. **sepolicy/VINTF 變化**:新增 neverallow、manifest 格式要求。
5. **自家債務盤點**:還剩多少 `.mk`、多少 HIDL HAL、多少 `BUILD_BROKEN_*` flag——新版本可能不再容忍。

**GRF(Google Requirements Freeze)決策**:GRF 允許 vendor/kernel 實作凍結在首發時的要求,沿用最多約 3–4 個版本升級(具體以當版政策為準)。策略意涵:

- **舊平台升級**:走 GRF,vendor image 與 kernel 不動,只換 system 側 → 工作量大減,但要驗證新 framework 配舊 vendor(這正是 Treble 承諾的場景,靠 VINTF + CTS-on-GSI 驗收)。
- **新平台 launch**:必須滿足當版全部要求,無 GRF 可用。
- 注意 GRF 凍結的是「要求」不是「bug」:security patch 仍要持續進。

---

## 三、Phase 1:Merge

### 3.1 Merge 策略

你的 tree = AOSP + 你的大量修改。兩種流派:

- **Rebase 流**:把自己的 patch 整理成 patch stack,rebase 到新 AOSP 上。乾淨,但要求平時紀律好(patch 原子化、標記清楚)。
- **Merge 流**:git merge 新 tag 進自己的 branch。歷史連續,但 conflict 集中爆發,且垃圾會累積。

不論流派,鐵律是一樣的:**自己的修改要最小化、模組化、可識別**(統一的 commit tag 如 `[MYVENDOR]`、能不改 framework 就不改、改了要有註解說明為什麼)。每年 merge 的痛苦程度,正比於你歷年入侵 AOSP 的深度——這也是為什麼 Treble/GKI 篇一直強調「把東西搬回 vendor 側」。

### 3.2 Conflict 的分類處理

conflict 分三類,處理優先序不同:

1. **上游重構撞到你的 hack** → 趁機把 hack 改成正規做法(HAL 化、搬 vendor)。
2. **上游功能與你的私有功能重疊** → 評估改用上游實作,刪自己的。
3. **純文字 conflict** → 機械解掉。

每年 merge 是唯一的「還債窗口」,只解 conflict 不還債,明年更痛。

---

## 四、Phase 2:公版 bringup

標準收斂順序(和新板 bringup 同構,見開機流程篇):

```
build 通過(m nothing → m)
 └─ 開機到 shell(必要時暫時 permissive、精簡 module)
     └─ 開機到桌面(HAL 逐支拉起、sepolicy 補齊)
         └─ 功能收斂(camera/media/connectivity/sensors 逐域驗證)
             └─ 效能功耗回歸(對照舊版 baseline)
                 └─ xTS 收斂(先 VTS/CTS-on-GSI,再全量)
```

實務要點:

- **build 修復期**:`.mk` 被禁的功能、Soong 新檢查(ELF 檢查、VINTF 檢查變嚴)、prebuilt 工具鏈 ABI 變化。設一個「build 綠燈」的 daily CI,分模組指派。
- **多 HAL 並行拉起**:每個 domain(camera、audio、display⋯⋯)一位 owner,共用一份「已知問題看板」,避免兩個人追同一個 root cause。
- **GSI 早驗**:公版能用 GSI 開機的那一刻,代表 Treble 邊界是乾淨的——越早達成,後面越順。
- **QPR 跟進策略**:正式版之後 Google 還有季度更新,決定你的 release 對齊哪個 QPR,避免客戶各自對不同 QPR。

---

## 五、Phase 3:認證與 release

xTS 全量收斂(方法見 xTS 篇)後,打包 BSP release 給客戶:

- **Release 內容**:manifest(指到凍結的 tag)、公版 device tree、prebuilt blobs、kernel(或 GKI + modules)、release notes(已知問題、與上版差異、客戶 porting guide)。
- **porting guide 的品質決定你的支援成本**:客戶從舊版升上來要改哪些檔、哪些介面變了、sepolicy 要補什麼——寫清楚一份,省掉一百張客戶 ticket。
- **公版 xTS 報告**隨 release 附上,作為客戶 fail 時的基線(「公版過的」)。

---

## 六、完全體情境:vendor 與 system 同時升級

前面 GRF 一節處理的是「vendor 凍結、只動 system」;新平台 launch 或決定不走 GRF 時,兩邊一起跳版本,方法論要升級成「有錨點的三段式」。

### 6.1 開發期:兩邊都在動,你需要一個不動的錨

同時升級最大的風險是「壞了不知道是誰壞的」。日程上兩邊重疊,但工程上必須串行化:

**Phase A:舊 vendor + 新 system(GSI 定錨)**
拿新版 GSI 配舊 vendor image 開機。這步驗的是 Treble 合約——連 GSI 都開不起來,表示舊 vendor 有偷依賴,先修掉。此階段所有 fail 都歸類為 system 側適配問題,範圍明確。

**Phase B:新 vendor,但只做「合規性升級」**
vendor 側升到新版最低要求:VINTF manifest 版本、新 HAL 版本、sepolicy 新規、AIDL freeze 對齊——**不加新功能、不改行為**。此時兩邊版本一致但變動最小,是整個升級最重要的穩定基線。

**Phase C:vendor 功能與行為升級**
新 feature、driver 大改、調校,全部疊在 Phase B 之上,出問題可 bisect 回 B。

**大忌:framework merge 與 vendor 重構混在同一批 commit 收斂。**

### 6.2 版本對齊的技術機制(build/boot 失敗高發區)

- **VINTF 雙向對帳**:新 FCM 會要求 HAL 升版或棄用(HIDL 退場),device manifest 要跟上;你的 DCM 宣告對新 system 也要成立。`m check-vintf-all` 最早跑。
- **Target FCM level**:vendor 一起升級時,target FCM level 要不要提升是明確決策——提升代表接受新版全部 vendor 要求(回不去了),不提升則保留部分舊規則。同時升級通常提升,但這是選擇,不是預設。
- **sepolicy 版本協商**:platform policy(system 帶)與 vendor policy 一起動,最容易撞 neverallow 新規——Phase B 的主要工作量。
- **kernel 是否連動**:KMI 不變則 GKI 可沿用;若 launch 要求逼你升 kernel,把它獨立成第四個 phase,錨定方法同上(舊 kernel 先跑新 userspace,或反之),不要三個變數一起動。

### 6.3 OTA:兩邊一起更新的原子性

- **A/B 讓 system+vendor 同步更新天然原子**:整包寫入 slot B、一起生效、一起 fallback——這正是 A/B 對跨版本大 OTA 的核心價值。
- **rollback index 保守遞增**:新組合在市場上穩定前別急著燒,否則出事想退舊版都不行。
- **跨大版本 incremental OTA 體積大**(兩邊都是大 diff),不少團隊對大版本升級只出 full OTA,省掉 diff 品質風險。
- **persist/校準資料相容**:vendor 大改時,新 driver 要讀得懂舊格式——OTA 不清 persist(見量產篇)。

### 6.4 測試矩陣的變化

| 組合 | 目的 |
|---|---|
| 新 system × 新 vendor | 出貨組合,全量 xTS |
| 新 GSI × 新 vendor | CTS-on-GSI(認證必要) |
| 新 system × 舊 vendor | bisect 用參考組合 |
| 升級 OTA 路徑(舊舊 → 新新) | 含中斷、fallback、userdata 保留驗證 |

最後一列最常被低估:**「升級上來的裝置」與「新刷機的裝置」是兩種狀態**(userdata 遺留、settings 遷移、apex data 版本)。市場端升級問題多出在前者,實驗室卻多半只測後者——升級路徑要進正式測試計畫。

---

## 七、降低明年痛苦的結構性投資

年復一年做下來,差距在這些地方拉開:

1. **AOSP 修改最小化**:每年統計「侵入 framework 的 patch 數」,當 KPI 往下壓。能上 upstream 的送 upstream(送進去的 code 明年不用 merge)。
2. **`.mk` → `.bp`、HIDL → AIDL 的持續遷移**:不要等被逼。
3. **CI 基礎建設**:daily build + 冒煙測試 + xTS 抽樣常態化,merge 期直接複用。
4. **Beta 期就參與**:用公版跑 Google Beta,提早發現自家 gap,也能在 Google 定案前反映問題(partner 管道)。
5. **文件化的 bringup checklist**:每年更新,新人也能照表操課。

---

## 結語

> **年度升級的工作量,不是新版本決定的,而是你過去一年的紀律決定的。** AOSP 改得少、邊界守得乾淨(Treble/GKI/VINTF)、債還得勤(.mk/HIDL)、CI 常備,升級就是幾個月的例行工程;反之,每年 Q3 都是一場災難片。GRF 能幫舊平台省力,但新平台的門檻年年墊高——把「可升級性」當成 BSP 架構的第一級設計目標,才是根本解。
