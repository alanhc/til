---
title: SoC Android 專案一頁摘要範本
sidebar_label: SoC Android 一頁摘要範本
---

# ［晶片代號］Android 軟體專案 — 規劃啟動摘要

**撰寫人**：［姓名］　**日期**：［YYYY-MM-DD］　**狀態**：［初版，多項待確認］

> 這是**給主管的一頁摘要範本**。主管通常只會逐字看完這一頁，所以先寫它，寫完再回頭補
> [規劃書](soc-android-planning-proposal-template.md)。判斷依據見
> [規劃方法論](soc-android-planning-methodology.md)，試算見
> [工作表](soc-android-planning-worksheet.md)。
>
> 標記 `［　］` 的欄位是要填的；文中數字皆為業界常見區間，非任何特定專案的實際值。

**本專案定案項目**：Vendor API Level = ［　］；System = ［　］

---

## 一、時程錨點與現況

| 項目 | 值 | 來源 |
|---|---|---|
| 目標 Android 版本公開發布 | ［　］ | ［Google 窗口確認］ |
| MP 目標日 | ［YYYY-MM-DD］ | ［來源］ |
| 距今 | ［N 週 / N 個月］ | |

**反推結果（若今日才 kick-off）：**

| 專案型態 | M0→MP 所需 | 缺口 |
|---|---|---|
| 全新架構 | 約 104 週 | ［剩餘週數 − 104］ |
| 衍生型 | 約 64 週 | ［剩餘週數 − 64］ |

> 若既有 vendor 基線與目標相差數代，本專案**不能按「衍生型」規劃**。理由見第二節。
>
> 上表假設今天才啟動；實務上晶片若要在該日期 MP，矽晶端應已在進行。
> **第一件要查證的事：實際 tape-out / silicon back 日期。**

---

## 二、選定新世代 Vendor API Level 的三個直接後果

### 後果 1：工作量要用「雙軸」估，不是單軸

若既有基線與目標 vendor level 相差數代，等於跨越中間各代累積的要求。
這些成本**與晶片本身的 IP 差異無關**，是額外疊加的：

> **估算人月 ＝ 前一代實際人月 ×（IP 軸係數 ＋ 版本軸係數）**
>
> - IP 軸：這顆晶片相對前一代的硬體差異（沿用 0.1／升版 0.4／新開發 1.2）
> - 版本軸：跨代的介面與合規重做（大 0.6／中 0.3／小 0.1）

[工作表](soc-android-planning-worksheet.md)的 WBS 已內建此模型，並額外算出一個數字：
**「純版本軸成本」——就算晶片跟前一代一模一樣，光是跨版本就要付的代價。**
這是說明「不能當衍生型估」的關鍵證據。

主要的版本軸工作（衝擊通常為「大」）：Kernel／GKI 世代跳躍、Graphics、Camera、Media、
Security/TEE、VINTF、16 KB page size 全面驗證、AOSP rebase、xTS、GMS。

### 後果 2：合規基準與該 Android 版本同步定版 —— 沒有早期存取就不可能

vendor 建在尚未定版的世代，代表對應的 VSR / VTS 會隨該 Android 版本一起定版。
若 MP 排在公開發布後不久，等於整合與 xTS 必須在**公開發布之前**完成。

**這需要 Google EAP / PDK 早期存取（通常發布前 3～6 個月取得）。這是 Go/No-Go 級前提，不是風險項。**

同時要接受：選最新世代就放棄了較舊 vendor API level 可享的 GRF freeze 緩衝，
必須即時跟上最新要求，並為晚期條款變動預留返工 buffer。

### 後果 3：承諾了多代 OS 升級的長期維運

vendor N 可支援 system N 至 N+3。這是選新世代換來的產品壽命，但也代表 MP 後需編列
**數年**的 OS 升級與月度 security patch 人力。這筆錢常在規劃階段被漏掉。

---

## 三、需要主管拍板的事

| # | 決策事項 | 狀態 |
|---|---|---|
| 1 | Vendor API Level | ［　］ |
| 2 | 是否確保取得 Google EAP / PDK 早期存取 | ［待決 —— Go/No-Go］ |
| 3 | Internal MP 是否含 GMS 認證與 xTS 全綠 | ［待釐清，影響約 6 週排程］ |
| 4 | 時程若壓不下來，優先犧牲什麼（功能降級／加人／延期） | ［待評估後提案］ |

---

## 四、需要立即查證的三件事

| # | 待確認 | 找誰 | 需回覆日 |
|---|---|---|---|
| 1 | 實際 tape-out / silicon back / EVB 到手日期 | 晶片 PM | ［日期］ |
| 2 | 目標 Android 版本確切發布日、EAP 取得時程、**對應的 GKI kernel 版本** | Google 窗口 | ［日期］ |
| 3 | 是否已有較新 vendor 世代的專案基線可參考（可降低版本軸成本） | 架構師 / Release Engineering | ［日期］ |

> 第 2 項的 kernel 版本尤其關鍵：Google 未公布對應 GKI branch 前，
> kernel 與 vendor module 適配的工時只能給 ±30% 的區間。

---

## 五、下一步

1. 本週寄出[工作表](soc-android-planning-worksheet.md)「資訊收集清單」的 12 題，設定回覆期限
2. 確認 EAP 取得狀況 —— 若確定拿不到，時程需整個重設，這件事最優先
3. 取得 tape-out 實際日期後，重算缺口並回報
4. 完成 IP Delta Map ＋ 版本軸評分後，才提出人力需求數字

---

*本文 Android 版本代號與 kernel 版本對應為依公開資訊整理，正式引用前請以 AOSP 官方文件與 Google 窗口確認。*
