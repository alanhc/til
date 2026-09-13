---
sidebar_label: Vendor Freeze
---

# Vendor Freeze:一份 BSP 走七年——晶片商、Google 與系統廠的凍結賽局

> 面向對象:Android 產業鏈的工程師與 PM。本文拆解 vendor freeze(以 Google 的 GRF/Longevity GRF 為核心)的技術機制與商業邏輯,並從 chip vendor、Google、系統廠(OEM/ODM)三個角度分析各自的得失與實務眉角。可視為前一篇〈[Android Migration](./android-migration.md)〉的深入篇。

---

## 一、什麼是 Vendor Freeze?

**Vendor freeze 指的是:把裝置的 vendor 實作(kernel、HAL、driver、SoC 專屬軟體)凍結在某個 Android 版本的要求水準,之後升級 Android 大版本時,只更新 system/framework 側,vendor 側原封不動。**

這件事之所以可能,前提是 Project Treble 已經把 system 與 vendor 用穩定介面(HIDL/AIDL、VINTF manifest)切開。但 Treble 只解決了「介面相容」,沒有解決「要求追加」——在 GRF 之前,Google 每年新版本的 VSR(Vendor Software Requirements)、新 HAL 版本、新 kernel 最低版本要求,會**回溯適用**到升級中的舊裝置,晶片商還是得每年重做一次 vendor 實作。

2020 年底 Google 推出 **GRF(Google Requirements Freeze)**,正式承諾:[新的 kernel 與 HAL 要求不再回溯適用,vendor 實作凍結在晶片首發的 API level,同一份實作可沿用 3 個後續 Android 版本](https://www.esper.io/blog/android-dessert-bites-11-grf-323579)。2024 年底再推出 **Longevity GRF**,把可沿用版本數[拉長到 7 個](https://www.androidauthority.com/android-longevity-grf-3493006/)——例如凍結在 Android 15 的平台,理論上可以一路陪跑到 Android 22。首發平台是 Snapdragon 8 Elite。

一句話:**vendor freeze 是 Google 用「放寬合規要求」向晶片商交換「更長更新年限」的制度性交易。**

---

## 二、技術機制:凍結是怎麼運作的

### 2.1 三個關鍵 system property

凍結狀態由幾個 board-level property 宣告,整個平台的行為據此調整(參考 [AOSP: Vendor API level](https://source.android.com/docs/core/architecture/api-flags)):

| Property | 意義 |
|---|---|
| `ro.board.first_api_level` | 晶片**首發**時凍結的 vendor API level。由晶片商在 freeze 認證時設定,之後**不可變**——它是「這顆 SoC 的出生證明」 |
| `ro.board.api_level` | vendor 軟體**目前**支援的 API level。若晶片商後來真的更新了 vendor 實作,這個值才會往上調 |
| `ro.vendor.api_level` | 執行期實際生效的 vendor API level,取 board 與裝置首發 SDK level 的組合下界。framework 用它判斷「哪些新功能在這台裝置上不能開」 |

自 Android 14 QPR3 起,vendor API level 從整數改為 **YYYYMM 格式**(如 `202404`),正式與 SDK API level 脫鉤——因為 vendor 要求的演進節奏已經跟一年一版的 SDK 不同步了。

### 2.2 FCM 與 VINTF:相容性的合約書

凍結能成立,靠的是 VINTF(Vendor Interface)機制:framework 側宣告它相容哪些 FCM(Framework Compatibility Matrix)版本,vendor 側的 device manifest 宣告自己實作了哪些 HAL 版本,開機與 OTA 時做匹配驗證。[FCM lifecycle](https://source.android.com/docs/core/architecture/vintf/fcm) 定義了 Google 要為每個舊 FCM 版本維持多久的 framework 相容性——GRF/Longevity GRF 本質上就是把這個維持年限大幅拉長,並承諾新版 VTS 對凍結平台只驗「當年的要求」,不驗新要求。

### 2.3 凍結不是全免:kernel 條款與豁免清單

Longevity GRF 附帶幾個重要但常被忽略的條件:

- **3 年一次 kernel 大版本升級**:Google 對單一 android-common kernel 分支只承諾約四年支援,所以凍結平台在第 3 年必須升一次 kernel 大版本(例如 5.15 → 6.6),否則安全補丁 backport 會變成災難。這是凍結期間唯一「必須動 vendor 側」的大工程。
- **新機不得用太舊的凍結實作**:OEM [不能拿超過 4 個版本前的 vendor software 開新機](https://www.androidauthority.com/android-longevity-grf-3493006/),防止「舊平台無限翻新殼」。
- **安全要求不凍結**:每月 security patch、STS 相關要求仍持續適用,凍結的是功能性要求,不是安全性要求。

---

## 三、Google 的角度:用合規換壽命

### 3.1 Google 為什麼願意放水

GRF 表面上是 Google 對晶片商讓步——放棄「所有裝置都跑最新 vendor 要求」的純潔性。但 Google 算的帳是:

1. **更新覆蓋率 > 功能純潔性**。Android 生態最大的問題從來不是新功能不夠,而是安全補丁與新版本推不下去。一份能沿用 7 年的 BSP,直接把「晶片商不支援」這個最大的升級藉口拆掉了。
2. **監管與競爭壓力**。歐盟生態設計法規對更新年限的要求、iPhone 5~6 年的 iOS 支援、Pixel 自己帶頭的 7 年承諾,都逼著 Google 給整個生態一條做得到的路。
3. **GKI 讓凍結變得可控**。有了 GKI 之後,kernel 的安全更新由 Google 統一發布,vendor module 隔在 KMI 之後——凍結 vendor 側不再等於凍結整個核心的安全性。

### 3.2 Google 付出的代價:功能碎片化 2.0

代價是真實的:**新功能如果需要 vendor 側配合,凍結裝置就是沒有**。Esper 的分析就點名過 Android 12 的「關閉 2G」開關、USB 資料訊號控制等功能,[在凍結的舊 vendor 實作上直接不可用](https://www.esper.io/blog/android-dessert-bites-11-grf-323579);Google 甚至曾因為部分 OEM 的凍結平台做不到,而收回 multi-camera API 的強制要求。

所以 Google 的工程對策是把新功能設計成**「vendor-optional + framework 降級路徑」**:framework 讀 `ro.vendor.api_level`,凍結裝置自動走舊路徑。這讓 CDD/VSR 文件越來越像一張多維度的條件矩陣——「若 vendor API level ≥ 202604 則必須支援 X,否則建議支援」。對 Google 的平台團隊來說,每個新功能都要多設計一條退路,這是凍結制度的隱形稅。

---

## 四、Chip Vendor 的角度:凍結是商業模式的重構

### 4.1 從「年年重做」到「一次做深」

GRF 之前,晶片商的 vendor 維護是純沉沒成本:晶片賣出後,每年還要為每顆在役 SoC 重做一輪 HAL/kernel 適配,而這不帶來任何新營收。GRF 把這件事變成:

- **首發版本做深做穩**:凍結那一版 BSP 的品質決定未來 7 年的口碑,所以晶片商會在首發版本投入比過去更多的驗證量能(完整 VTS/CTS-on-GSI、長時間穩定性測試)。
- **後續版本只做「升級驗證包」**:每年新 Android 版本出來,晶片商交付的不再是新 BSP,而是一份「本平台凍結實作 + 新版 GSI/framework」的驗證報告與少量 bug fix。成本從「工程團隊 × 12 個月」降到「驗證團隊 × 2~3 個月」。
- **kernel upgrade 變成可規劃的單點工程**:3 年一次的 kernel 大版本升級,可以跨平台批次執行,而不是每年每平台各來一次。

高通在 GRF 初期就把承諾從 N+2 拉到 [N+3 個大版本、4 年安全更新](https://www.esper.io/blog/android-dessert-bites-11-grf-323579);到了 Longevity GRF,Snapdragon 8 Elite 直接簽下 7 版本的支援矩陣。這不是慈善——**支援年限已經變成旗艦 SoC 的規格表項目**,是對三星、小米等大客戶的競標籌碼。

### 4.2 晶片商的新難題

凍結也帶來新的工程與商業張力:

- **「凍結線」的取捨**:凍結越早,維護越省,但平台能支援的新功能越少;凍結越晚,對 OEM 越有吸引力,但等於替未上市的 Android 版本先做工。晶片商必須替每個平台選一條凍結線,這是產品企劃層級的決策。
- **選擇性 backport 的灰色地帶**:大客戶會要求「雖然凍結了,但這個新功能幫我 backport 一下」。做,就破壞了凍結的成本模型;不做,客戶可能轉單。實務上晶片商用「premium support 收費」或「只給旗艦平台」來處理。
- **中低階平台的凍結經濟學**:Longevity GRF 對旗艦是加分項,但入門 SoC 的產品生命週期本來就短,7 年支援反而是不必要的成本。所以會看到晶片商分層:旗艦平台進 Longevity GRF,入門平台維持 3 版本的基本 GRF。

---

## 五、系統廠的角度:天花板與地板同時被決定

### 5.1 凍結替系統廠決定了什麼

對 OEM/ODM 來說,晶片商的凍結決策等於同時劃下兩條線:

- **地板(能撐幾年)**:晶片商凍結實作的支援矩陣,直接決定這台裝置「不用自己扛 vendor 維護」能升到哪一版。想承諾 7 年更新?先確認你選的 SoC 進了 Longevity GRF。**SoC 選型會議從此多了一個必問項目:凍結版本與支援矩陣。**
- **天花板(功能上限)**:凍結在 Android 15 的平台,升到 Android 18 時,所有需要新 vendor HAL 的功能都不會有。產品企劃在規劃「明年 OTA 要主打什麼新功能」時,必須先對照 `ro.vendor.api_level` 的功能矩陣,否則行銷承諾會直接跳票。

### 5.2 升級專案變輕了,但沒有變不見

vendor freeze 讓系統廠的年度大版本升級少掉「等晶片商新 BSP」這個最大的串行依賴——新 AOSP 一出,理論上就能在凍結的 vendor 上開始 rebase 自家 framework 客製與 UI。但系統廠自己的工作一項都沒少:私有 patch rebase、CTS/GTS 認證、運營商 TA、OTA 運維。而且多了幾個新坑:

- **凍結相容性 bug 的歸屬爭議**:新 framework 踩到凍結 vendor 的邊角行為時,晶片商的標準答案可能是「凍結範圍內恕不修改」,系統廠得自己在 framework 側 workaround。合約裡的 support SLA 要把凍結期間的 bug fix 義務寫清楚。
- **第 3 年的 kernel 升級是隱藏火藥庫**:凍結期間最大的一次 vendor 側變動就是強制 kernel 大版本升級。板級 driver(觸控、充電、面板)如果當年寫得不乾淨,這一次升級的成本可能不亞於半次 bring-up。開案時就該要求板級 code 符合 upstream / GKI module 規範,替 3 年後的自己留活路。
- **超出凍結矩陣就是自己扛**:想比晶片商的支援矩陣多撐一版?意味著系統廠要[自行 port 缺少的 HAL 變更,而且晶片商大概率不提供支援](https://www.esper.io/blog/android-dessert-bites-11-grf-323579)。絕大多數系統廠的理性選擇是:支援年限承諾 = 晶片商凍結矩陣,一版都不多。

### 5.3 對產品線策略的影響

vendor freeze 也改變了系統廠的機型規劃:同一份凍結 BSP 可以支撐多代衍生機型(手機、平板、同平台的次年小改款),讓「一顆 SoC 榨三年」的策略在軟體維護上變得可行。但反過來,Google 的「新機不得用超過 4 版前的 vendor software」條款,也替這種翻新殼策略設了停損點。

---

## 六、三方視角對照與總結

| | Google | Chip Vendor | 系統廠(OEM/ODM) |
|---|---|---|---|
| **在凍結中得到** | 更新覆蓋率、7 年承諾的制度基礎、監管交代 | 維護成本銳減、支援年限變成可販售的規格 | 升級專案去掉最大串行依賴、長更新承諾變得可負擔 |
| **在凍結中付出** | 功能碎片化、每個新功能都要設計降級路徑 | 首發版本品質壓力、大客戶 backport 拉扯 | 功能天花板被鎖死、凍結邊界 bug 自己扛 |
| **關鍵決策** | 哪些要求可凍結、哪些(安全)不可 | 每個平台的凍結線劃在哪、進不進 Longevity | SoC 選型時就綁定支援矩陣與功能上限 |
| **技術抓手** | VINTF/FCM、vendor API level、VTS 豁免 | BSP 凍結認證、3 年 kernel upgrade 計畫 | `ro.vendor.api_level` 功能矩陣、板級 code 紀律 |

Vendor freeze 的本質,是 Android 生態在「功能演進速度」與「更新壽命」之間做出的制度性取捨:**Google 讓渡了要求的一致性,晶片商讓渡了首發版本的工程深度,系統廠讓渡了功能自由度,三方共同買到的是——一台手機可以被安全地用上七年。** 對工程師與 PM 而言,實務上最重要的一句話是:凍結決策發生在 SoC 選型那一刻,之後的七年都只是在執行它。

---

## 延伸閱讀

- [GRF: How Google Requirements Freeze Affects Android Updates — Esper](https://www.esper.io/blog/android-dessert-bites-11-grf-323579)
- [Vendor API level — AOSP](https://source.android.com/docs/core/architecture/api-flags)
- [FCM lifecycle — AOSP](https://source.android.com/docs/core/architecture/vintf/fcm)
- [How Google is making it easier for Android devices to get 7 years of updates (Longevity GRF) — Android Authority](https://www.androidauthority.com/android-longevity-grf-3493006/)
- [Google pushing for 7 years of updates, starting with Snapdragon 8 Elite — 9to5Google](https://9to5google.com/2024/10/23/google-android-7-years-updates-longeivity-program/)
