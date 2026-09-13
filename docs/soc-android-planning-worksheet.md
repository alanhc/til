---
title: SoC Android 軟體專案規劃工作表
sidebar_label: SoC Android 規劃工作表
---

# SoC Android 軟體專案規劃工作表

**專案**：［晶片代號］　**版本**：［v0.1］　**更新日**：［YYYY-MM-DD］

> 這是一份**空白工作表**。方法與判斷依據見
> [規劃方法論](soc-android-planning-methodology.md)；
> 彙總後填入 [規劃書範本](soc-android-planning-proposal-template.md) 與
> [一頁摘要範本](soc-android-planning-onepager-template.md)。
>
> 使用順序：先填第 1 節（12 題）→ 再填第 5 節（WBS）→ 再填第 6 節（人力）→ 最後更新第 7 節（風險）。
> 標記 `［　］` 的欄位是要填的。表中所有數字為業界常見區間，非任何特定專案的實際值。

**先釘住三個前提，後面才有意義：**

| 項目 | 值 |
|---|---|
| 既有基線 | vendor ［　］ + system ［　］ |
| 本專案目標 | vendor ［　］ + system ［　］ |
| 時程錨點 | ［internal MP 或客戶 MP 目標日］ |

---

## 1. 資訊收集清單（第 1 週的唯一任務）

| # | 類別 | 要問到什麼 | 問誰 | 為什麼決定一切 | 狀態 | 若拿不到的最壞假設 |
|---|---|---|---|---|---|---|
| 1 | 矽晶時程 | 「明年」指的是 tape-out、silicon back，還是客戶 MP？ | 晶片 PM | 三者差 12～18 個月，最常見的雞同鴨講 | ［　］ | 以最保守者（MP）認定 |
| 2 | 矽晶時程 | Tape-out / A0 silicon back / EVB 到手的預定日期 | 晶片 PM | 所有里程碑的錨點 | ［　］ | 以前一代同型晶片實際日期推估 |
| 3 | 矽晶時程 | 是否有 pre-silicon 平台、何時可用 | 驗證團隊主管 | 可省 6～9 個月 | ［　］ | 假設無，bring-up 全排在 silicon back 後，+6 個月 |
| 4 | IP Delta | 參考基線是哪一顆晶片？哪個 branch 可 fork？ | 架構師 | 決定可沿用程式碼比例 | ［　］ | 假設無可用基線，全視為新開發 |
| 5 | IP Delta | IP delta 清單，逐項標沿用／升版／全新 | 架構師、SoC 定義文件 | 工時的唯一真實來源 | ［　］ | 以「全部升版」估算，標記低信心 |
| 6 | Google | 目標世代對應的 GKI kernel 版本 | Google 窗口 | 未定前 kernel 工時只能給區間 | ［　］ | 以前一代 GKI branch 為基準，預留 ±30% |
| 7 | Google | 目標 VSR 條款與定版時程 | 合規主管 | vendor 建在尚未定版的世代時，規格會隨該版一起收斂 | ［　］ | 以前一代 VSR 為基準，預留晚期返工 buffer |
| 8 | Google | 是否有 EAP / PDK 早期存取？何時拿得到 code？ | Google 窗口 | MP 緊貼公開發布時為 Go/No-Go 級前提 | ［　］ | 若無，時程需整個重設 |
| 9 | Google | Internal MP 是否含 GMS 認證與 xTS 全綠 | 業務／合規 | 影響約 6 週排程 | ［　］ | 假設不含認證 |
| 10 | 客戶 | 首發客戶、量產目標日、產品型態、目標市場 | 業務、PM | 反推時程的起點 | ［　］ | 以業務口頭目標日再往前抓 1 個月 |
| 11 | 客戶 | 客戶特殊需求 delta | 業務、客戶 FAE | 常是隱形的最大工作包 | ［　］ | 預留 10% 總工時作客製 buffer |
| 12 | 內部 | 各域現有人力、可用度、上一代**實際**投入工時 | 主管、PMO | 人力估算的類比基礎 | ［　］ | 以當初估算值 ×1.3 代用 |

> **用法**：把這張表直接寄給對應的人，標明「請於 X 日前回覆，未回覆將以最壞假設寫入規劃書」。

---

## 2. 版本相容矩陣（Vendor API Level 決策依據）

**規則**：Google 保證 system 相容於最近 3 代 vendor 實作，即 vendor N 可搭配 system N ~ N+3。

### 2.1 代號對照（公開資訊）

| 代號 | Android 版本 | GKI Kernel | 公開發布 |
|---|---|---|---|
| U | Android 14 | 5.15 / 6.1 | 2023 |
| V | Android 15 | 6.6 | 2024 |
| B | Android 16 (Baklava) | 6.12 | 2025-06 |
| C | Android 17 (Cinnamon Bun) | 6.18 | 2026 Q2 |
| D | Android 18 | 待 Google 公布 | 待公布 |

> 更新的世代以 Google 官方公布為準。

### 2.2 相容矩陣（N+3 規則的展開）

| Vendor ＼ System | N | N+1 | N+2 | N+3 | N+4 |
|---|---|---|---|---|---|
| **vendor N** | OK | OK | OK | **OK（極限）** | **超出，不受支援** |

實際評估時把 N 代入自家既有基線的 vendor level，就能看出既有 vendor 還能搭到哪一版 system、
哪一版開始必須升 vendor。

### 2.3 選項評估

| 選項 | 可支援 System 範圍 | 可沿用既有程式碼的程度 | 評估 |
|---|---|---|---|
| 目標世代 ［　］ | ［　］ | ［　］ | ［　］ |
| 前一世代 ［　］ | ［　］ | ［　］ | ［　］ |
| 維持現行 ［　］ | ［　］ | 高 | ［是否搭得到目標 system？］ |

> 判斷原則：vendor level 選得越新，可支援的 system 代數越長（產品壽命越長），
> 但可沿用的既有程式碼越少、且必須即時跟上尚未凍結的合規條款。

---

## 3. Vendor 端跨代差異檢查清單

> 這是工作量的隱藏來源。每一項都要逐版對照最新 VSR / CDD 文件確認，這是估工時前必須先做完的功課。
> 「自哪一代引入」欄請依實際目標世代填寫；衝擊等級為通用經驗值，需依專案調整。

| # | 項目 | 對 Vendor 的影響 | 典型衝擊 | 適用本專案？ | 已確認？ |
|---|---|---|---|---|---|
| 1 | GKI / Kernel 世代跳躍 | 跨數個 GKI 世代時，所有 vendor modules 需重新對 KMI 適配與重編 | 高 | ［　］ | ［　］ |
| 2 | HIDL → AIDL HAL 遷移 | HIDL 持續淘汰，多數 HAL 需改寫為 AIDL 介面 | 高 | ［　］ | ［　］ |
| 3 | 16 KB page size 支援 | 所有 native code、driver、prebuilt library 需重新對齊與驗證 | 高 | ［　］ | ［　］ |
| 4 | VSR 條款逐代累積 | 每代新增功能與非功能要求，需逐版做 gap review | 高 | ［　］ | ［　］ |
| 5 | Vendor module 簽章與 KMI 穩定性 | 模組載入、簽章、版本控管流程調整 | 中 | ［　］ | ［　］ |
| 6 | Security：Keymint / StrongBox / provisioning | TEE 端介面與金鑰佈建流程升版 | 中 | ［　］ | ［　］ |
| 7 | Camera / Media / Audio HAL 新版要求 | AIDL 化與新增 feature 支援（含 ITS 測項增加） | 高 | ［　］ | ［　］ |
| 8 | Virtualization / pKVM | 若產品需要，需新增支援 | 中 | ［　］ | ［　］ |
| 9 | Graphics：Vulkan 版本與 driver 要求提升 | GPU driver 需符合新版一致性要求 | 中 | ［　］ | ［　］ |
| 10 | xTS 測項跨代大量新增 | CTS/VTS/GTS 測項數量與難度顯著增加，測試人力需重估 | 高 | ［　］ | ［　］ |
| 11 | 目標世代 VSR / VTS 定版時間風險 | vendor 建在尚未定版的世代時，合規基準與該 Android 版本同步定版 | 高 | ［　］ | ［　］ |
| 12 | 放棄 GRF freeze 緩衝 | 選較舊 vendor level 可享 Google Requirements Freeze 緩衝；選最新世代換取壽命，代價是必須即時跟上 | 中 | ［　］ | ［　］ |
| 13 | 目標世代 GKI branch 尚未公開 | 版本未定前 kernel 工作無法精確估算 | 高 | ［　］ | ［　］ |
| 14 | 多代 OS 升級的長期維運承諾 | vendor N 支援至 system N+3，MP 後需編列數年升級與月度 patch 人力 | 中 | ［　］ | ［　］ |

> **結論**：只要目標 vendor level 跨了既有基線好幾代，就不要當成「沿用前一代 vendor」來估工時。

---

## 4. 里程碑反推時程

**錨點**：MP 目標日 = ［YYYY-MM-DD］
**基準**：下表前置週數為「全新架構」起手值；衍生型專案請另行縮短（見方法論第 3 節區間表）

| 代號 | 里程碑 | Exit Criteria | MP 前置週數 | 推算日期 | 距今 | 負責人 |
|---|---|---|---|---|---|---|
| M0 | Kick-off / SW Plan Freeze | 範圍、WBS、人力、時程通過簽核 | 104 | ［　］ | ［　］ | ［　］ |
| M1 | Pre-silicon 環境就緒 | FPGA / Emulator 可跑 kernel boot | 90 | ［　］ | ［　］ | ［　］ |
| M2 | Silicon Back（A0 到手） | EVB 上電成功、JTAG 可連 | 66 | ［　］ | ［　］ | ［　］ |
| M3 | Boot to Shell | GKI + 最小 vendor modules，adb shell 可用 | 64 | ［　］ | ［　］ | ［　］ |
| M4 | Boot to Home | Android UI 出畫面，顯示／觸控可用 | 60 | ［　］ | ［　］ | ［　］ |
| M5 | Alpha SDK | 核心功能 demo-able，可交付 lead customer | 48 | ［　］ | ［　］ | ［　］ |
| M6 | Beta SDK（Feature Complete） | 全 HAL 到位，VINTF 宣告完成 | 34 | ［　］ | ［　］ | ［　］ |
| M7 | xTS Green | CTS / VTS / CTS-on-GSI / GTS 全綠 | 22 | ［　］ | ［　］ | ［　］ |
| M8 | PV / RC SDK | 效能功耗達標，程式碼凍結 | 14 | ［　］ | ［　］ | ［　］ |
| M9 | GMS 認證通過 | Reference design 取得認證 | 6 | ［　］ | ［　］ | ［　］ |
| M10 | MP + 進入 LTS | 量產版釋出，月度 patch 機制上線 | 0 | ［　］ | ［　］ | ［　］ |

### 缺口分析

| 項目 | 值 |
|---|---|
| 距 MP 剩餘週數 | ［　］ |
| 全新架構所需（M0→MP） | 約 104 週 |
| 衍生型所需（M0→MP） | 約 64 週 |
| **缺口：全新架構** | ［剩餘週數 − 104］ |
| **缺口：衍生型** | ［剩餘週數 − 64］ |

**三個注意事項：**

1. 上表以 internal MP 為錨點。**若 internal MP 需含 GMS 認證，錨點要再往前約 6 週。**
2. 若 internal MP 排在 Android 公開發布後不久，代表整合與 xTS 必須在公開發布**之前**完成 —— 沒有 Google EAP / PDK 早期存取，這種日期在物理上不可能達成，屬 Go/No-Go 級前提。
3. 上表假設今天才 kick-off。實務上晶片若已在進行，矽晶端進度可能已覆蓋前段里程碑。
   **務必先查證實際 tape-out 日期** —— 若矽晶進度符合，軟體側缺口會小得多。

### 排程必須卡住的三個外部相依

1. Google AOSP source drop（2026 起每年 Q2 / Q4）—— rebase 窗口
2. 每月 Android Security Bulletin —— SPL 承諾綁住維運人力
3. IP 供應商 driver release（GPU / Modem 廠）—— 最常見的隱形要徑

---

## 5. WBS 工作分解與人月估算（雙軸模型）

> **估算人月 ＝ 前一代實際人月 ×（IP 軸係數 ＋ 版本軸係數）**
>
> - **IP 軸**（這顆晶片的硬體差異）：沿用 `0.1`／升版 `0.4`／新開發 `1.2`
> - **版本軸**（跨 vendor API level 的介面與合規重做）：大 `0.6`／中 `0.3`／小 `0.1`
>
> 兩者獨立發生，必須相加。範例：某模組前一代 18 人月，IP 軸「升版」(0.4) + 版本軸「大」(0.6) = 18 × 1.0 = **18.0 人月**。
> 版本軸欄位下方標的是「跨數代時的典型等級」，請依實際跨代幅度調整；同代升級時版本軸接近 0。

| 域 | 模組 | IP 軸狀態 | 版本軸 | 前一代人月 | 估算人月 | 信心度 | 負責人 |
|---|---|---|---|---|---|---|---|
| Vendor | Boot chain（LK/ABL、fastboot、AVB、DTBO） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Kernel（GKI branch、vendor modules、KMI、device tree） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Graphics（GPU driver、Gralloc、HWC、Vulkan/GLES CTS） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Camera（ISP tuning、Camera HAL、ITS、sensor 矩陣） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Media（Codec2、硬體編解碼、Widevine L1、HDCP） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Audio（Audio HAL、DSP firmware、低延遲路徑） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Connectivity（Wi-Fi / BT / GNSS HAL 與 firmware 綁版） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Modem / RIL | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Security / TEE（TEE OS、Keymint、StrongBox、provisioning） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | AI / NPU（NN HAL、compiler/runtime、model 驗證） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Power / Thermal / Perf（Power HAL、DVFS、benchmark） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Sensors / USB / Vibrator / Health / Display panel | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | VINTF（manifest、compatibility matrix、Vendor API Level 宣告） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | 16 KB page size 全面驗證 | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| Vendor | Release Engineering（build system、CI、SDK 打包、交付） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| System | AOSP rebase 策略與 branch 管理（對齊 Q2/Q4 drop） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| System | GSI boot 測試（Treble 合規證明） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| System | Framework 客製與 RRO overlay | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| System | xTS（CTS / CTS-V / CTS-on-GSI / GTS / STS / MTS / ITS / BTS） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| System | GMS 導入（GMS Requirements、MADA、認證窗口） | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| System | Security 維運（月度 SPL、patch 回移、支援年限） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |
| System | 客戶 SDK 文件、reference app、除錯工具鏈 | ［　］ | 小 (0.1) | ［　］ | ［　］ | ［　］ | ［　］ |
| 跨域 | 跨域整合 debug / 三方聯調 | ［　］ | 大 (0.6) | ［　］ | ［　］ | ［　］ | ［　］ |
| 跨域 | 客戶 FAE 支援 | ［　］ | 小 (0.1) | ［　］ | ［　］ | ［　］ | ［　］ |
| 跨域 | 專案管理 / PMO | ［　］ | 小 (0.1) | ［　］ | ［　］ | ［　］ | ［　］ |
| 跨域 | 多代 OS 升級的長期維運（MP 後） | ［　］ | 中 (0.3) | ［　］ | ［　］ | ［　］ | ［　］ |

### 彙總

| 項目 | 人月 |
|---|---|
| Vendor Domain 小計 | ［　］ |
| System Domain 小計 | ［　］ |
| 跨域小計 | ［　］ |
| 由下而上合計 | ［　］ |
| 整合與 debug 稅係數 | ×1.3 |
| **調整後總人月** | **［　］** |
| **參考：純版本軸成本**（假設所有 IP 皆沿用） | **［　］** |

> **「純版本軸成本」的用途**：這個數字是「就算晶片跟前一代一模一樣，光是跨 vendor API level 就要付的代價」。
> 算法：Σ（各模組前一代人月 × 該模組版本軸係數）。用來說明為何不能當衍生型估。

### 交叉驗證（三種方法各估一次）

| 方法 | 估算結果（人月） | 信心度 |
|---|---|---|
| 類比法（上一代實際 × Delta 比例） | ［　］ | ［　］ |
| 由下而上（WBS 加總 ×1.3） | ［　］ | ［　］ |
| 由上而下（競品團隊規模反推） | ［　］ | ［　］ |

> 三者差距超過 30%，代表 Delta Map 有洞，回頭補資訊，不要取平均。

---

## 6. 人力配置表（人月／季）

> 把第 5 節的估算人月分配到各季，缺口出現負數即代表該季超載。

| 職能 | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | 合計 |
|---|---|---|---|---|---|---|---|---|---|
| Kernel / BSP | | | | | | | | | |
| Graphics | | | | | | | | | |
| Camera | | | | | | | | | |
| Media | | | | | | | | | |
| Audio | | | | | | | | | |
| Connectivity | | | | | | | | | |
| Modem / RIL | | | | | | | | | |
| Security / TEE | | | | | | | | | |
| AI / NPU | | | | | | | | | |
| Power / Perf | | | | | | | | | |
| Sensors / 周邊 | | | | | | | | | |
| VINTF / 合規 | | | | | | | | | |
| xTS 測試 / 自動化 | | | | | | | | | |
| Release Engineering | | | | | | | | | |
| 客戶支援 / FAE | | | | | | | | | |
| 專案管理 / PMO | | | | | | | | | |
| **需求合計** | | | | | | | | | |
| **可用人力** | | | | | | | | | |
| **缺口（可用 − 需求）** | | | | | | | | | |

> **別漏算**：測試自動化維護、客戶 FAE 支援、月度 security patch、跨域整合 debug、release engineering。
> 這幾項合計通常佔總工時 25～35%。若承諾多代 OS 升級，還要再加上 MP 後數年的維運人力。

---

## 7. 風險登記

> 等級 = 機率分數 × 影響分數（高=3、中=2、低=1）。等級 6 以上請在規劃書正文單獨一頁說明。
> 下表為通用風險清單與典型評級，請依專案實況重評機率與影響。

| # | 風險 | 類別 | 觸發訊號 | 機率 | 影響 | 等級 | 減緩做法 |
|---|---|---|---|---|---|---|---|
| 1 | Silicon 延期或 A0 有重大 bug 需 A1 | 矽晶 | Tape-out 日期反覆變動 | ［　］ | ［　］ | ［　］ | Pre-silicon 覆蓋率目標；預備 A1 情境的第二版時程 |
| 2 | 拿不到 Google 早期 code（EAP/PDK） | Google | EAP 申請尚未確認 | ［　］ | ［　］ | ［　］ | MP 緊貼公開發布時為 Go/No-Go 級；先以公開 AOSP 開發，rebase 預留 4～6 週 buffer |
| 3 | IP 供應商 driver 延遲（GPU / Modem） | 供應鏈 | 供應商未給書面日期 | ［　］ | ［　］ | ［　］ | 列為要徑並要求書面承諾；準備 fallback 版本 |
| 4 | VSR / CDD 新增需求導致返工 | 合規 | 尚未取得最新版需求文件 | ［　］ | ［　］ | ［　］ | 每次 AOSP source drop 後排一次合規 gap review |
| 5 | 人力未到位 | 資源 | HC 尚未核准 | ［　］ | ［　］ | ［　］ | 分階段招募計畫；備妥功能降級的 Plan B |
| 6 | 客戶需求擴張（scope creep） | 客戶 | 首發客戶需求未定案 | ［　］ | ［　］ | ［　］ | 明訂 feature freeze 日與變更控制流程 |
| 7 | Feature Complete 到 GMS 的期程被壓縮 | 時程 | 主管只認到 feature complete | ［　］ | ［　］ | ［　］ | 在規劃書明列 M6→M9 需 3～5 個月，並列入簽核項目 |
| 8 | MP 後維運人力未編列 | 維運 | 無 LTS / SPL 承諾規劃 | ［　］ | ［　］ | ［　］ | MP 前 3 個月啟動維運團隊編制與 patch 流程演練 |
| 9 | 目標世代 VSR / VTS 晚期條款變動導致返工 | 合規 | vendor 建在尚未定版的世代 | ［　］ | ［　］ | ［　］ | 透過 EAP 追蹤 preview/beta 要求；預留晚期返工 buffer |
| 10 | 目標世代 GKI kernel 版本未定 | 技術 | Google 尚未公布對應 GKI branch | ［　］ | ［　］ | ［　］ | 先以前一代 GKI branch 為基準規劃；kernel 工作預留 ±30% 彈性 |
| 11 | 多代升級承諾的長期維運人力未編列 | 資源 | 僅規劃到 MP，未規劃 MP 後 | ［　］ | ［　］ | ［　］ | MP 前 3 個月啟動維運編制；升級人力納入年度預算 |

---

*本表 Android 版本代號對應與 kernel 版本為依公開資訊整理，正式引用前請以 AOSP 官方文件與 Google 窗口確認。*
