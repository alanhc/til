---
title: SoC Android 軟體專案規劃書範本
sidebar_label: SoC Android 規劃書範本
---

# ［晶片代號］Android 軟體專案規劃書

**Vendor Domain + System Domain**

> 這是一份**空白範本**。判斷依據見 [規劃方法論](soc-android-planning-methodology.md)，
> 明細試算見 [工作表](soc-android-planning-worksheet.md)，
> 給主管的縮版見 [一頁摘要範本](soc-android-planning-onepager-template.md)。
> 標記 `［　］` 的欄位是要填的；文中數字皆為業界常見區間，非任何特定專案的實際值。

| 項目 | 內容 |
|---|---|
| 文件版本 | ［v0.1 草稿］ |
| 撰寫人 | ［姓名／部門］ |
| 日期 | ［YYYY-MM-DD］ |
| 審核 | ［主管姓名］ |
| 核准 | ［決策者姓名］ |

---

## 1. 一頁摘要

> **填寫指引**：這一頁是主管唯一會逐字看完的部分。先寫這頁，寫完再回頭補後面。只講四件事，不要放技術細節。

### 1.1 範圍一句話

［本專案負責 ［晶片代號］ 的 Android Vendor Domain 全部軟體，以及 System Domain 的 ［xTS／GMS 認證／SDK 交付］］

### 1.2 反推時程結論

> **填寫指引**：從客戶 MP 日往回推得到的起跑日，以及與今天的落差。這是本文件最重要的一個數字。

［MP 目標日 ［YYYY-MM-DD］，反推起跑日為 ［YYYY-MM-DD］，目前 ［落後／提前］ ［N］ 個月］

### 1.3 關鍵未知

| 未決項目 | 卡在誰 | 需回覆日 |
|---|---|---|
| ［項目 1］ | ［姓名／單位］ | ［日期］ |
| ［項目 2］ | ［姓名／單位］ | ［日期］ |
| ［項目 3］ | ［姓名／單位］ | ［日期］ |

### 1.4 需要主管決定的事

| 決策事項 | 選項 | 建議 | 需決定日 |
|---|---|---|---|
| Vendor API Level | ［候選世代］ | ［建議］ | ［日期］ |
| Google EAP / PDK 早期存取 | 申請 / 不申請 | ［建議］ | ［日期］ |
| Internal MP 是否含 GMS 認證 | 含 / 不含 | ［建議］ | ［日期］ |

---

## 2. 專案背景與目標

### 2.1 晶片定位

> **填寫指引**：產品型態（手機／平板／車機／IoT）、市場區隔、目標市場（歐盟／中國／北美，影響法規與 GMS 範圍）。

［待填］

### 2.2 首發客戶與量產目標

| 項目 | 內容 |
|---|---|
| 首發客戶 | ［客戶名稱］ |
| Internal MP 目標日 | ［YYYY-MM-DD］ |
| 客戶 MP 目標日 | ［YYYY-MM-DD］ |
| 產品型態 | ［手機／平板／車機／IoT］ |
| 目標市場 | ［歐盟／中國／北美／其他］ |
| 預估出貨量 | ［數量］ |

### 2.3 專案成功定義

> **填寫指引**：用可驗收的條件寫，例如「於 YYYY-MM 前以 reference design 通過 GMS 認證」，不要寫「達成高品質」。

［待填］

---

## 3. 範圍定義

> **填寫指引**：這一章的目的是讓「這誰做？」的爭論一次結束。開會時指著這張表講。

### 3.1 Treble 分域責任

| 項目 | Vendor Domain | System Domain |
|---|---|---|
| Partition | vendor / vendor_dlkm / odm / odm_dlkm | system / system_ext / product |
| 擁有者 | 我方（晶片商） | Google AOSP + OEM 客製 |
| 內容 | Bootloader、Kernel（GKI + vendor modules）、全部 HAL、驅動、韌體、TEE、DSP/NPU stack | Framework、SystemUI、Settings、GMS、OEM app |
| 相容性依據 | Vendor API Level → ［VSR-N］ | CDD |
| 主要測試 | VTS、CTS-on-GSI | CTS、GTS、STS、MTS |
| 我方投入 | ［全包／部分］ | ［配合驗證／完整交付］ |

### 3.2 明確不在範圍內（Out of Scope）

> **填寫指引**：把不做的事寫清楚，比寫要做的事更能保護專案。

- ［例：客戶自有 UI 層客製］
- ［例：客戶端 GMS 認證送測作業］
- ［例：非 Android 作業系統支援］

---

## 4. 技術基準

> **填寫指引**：這一章的每一格都必須有明確答案。任何一格填「待確認」，後面的時程與人力就是假設，要在文中標記為低信心。

| 項目 | 值 | 來源／確認人 |
|---|---|---|
| Target Android Release | ［　］ | ［　］ |
| GKI Branch / Kernel 版本 | ［　］ | ［Google 窗口］ |
| Vendor API Level | ［　］ | ［　］ |
| 適用 VSR | ［　］ | ［合規主管］ |
| 可支援 System 版本 | ［N ~ N+3］ | N+3 規則 |
| AOSP Source Drop 對齊 | 2026 起 Google 每年 Q2、Q4 各發布一次 | ［Google 窗口］ |
| EAP / PDK 早期存取 | ［有／無，取得日期］ | ［Google 窗口］ |
| 既有基線 | vendor ［　］ + system ［　］ | 現況 |
| 可 fork 的 branch | ［branch 名稱］ | ［Release Engineering］ |
| GMS 認證負責方 | ［我方 reference design／客戶］ | ［業務／合規］ |
| Security Patch 承諾 | ［月度 SPL，支援 N 年］ | ［產品主管］ |

---

## 5. IP Delta Map

> **填寫指引**：這張表是 IP 軸工時的來源。逐項標狀態；沿用約 0.1、升版約 0.4、全新約 1.2 的係數。
> **注意**：若同時跨了 vendor API level，另有版本軸成本，見第 7 章。

| IP / 子系統 | 前一代 | 本代 | 狀態 | 軟體衝擊 |
|---|---|---|---|---|
| CPU | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| GPU | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| ISP / Camera | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| VPU / Codec | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| NPU / AI | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| Modem | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| DSP / Audio | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| TEE / Security | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| Memory / Interconnect | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |
| Connectivity | ［　］ | ［　］ | ［沿用／升版／全新］ | ［　］ |

---

## 6. 里程碑與時程

> **填寫指引**：數字請直接引用[工作表](soc-android-planning-worksheet.md)第 4 節，避免兩份文件不一致。
> 時程一律從 MP 日反推，不要從今天往後排。

| 代號 | 里程碑 | Exit Criteria | 日期 | 負責人 |
|---|---|---|---|---|
| M0 | Kick-off / SW Plan Freeze | 範圍、WBS、人力、時程通過簽核 | ［　］ | ［　］ |
| M1 | Pre-silicon 環境就緒 | FPGA / Emulator 可跑 kernel boot | ［　］ | ［　］ |
| M2 | Silicon Back（A0） | EVB 上電成功、JTAG 可連 | ［　］ | ［　］ |
| M3 | Boot to Shell | GKI + 最小 vendor modules，adb shell 可用 | ［　］ | ［　］ |
| M4 | Boot to Home | Android UI 出畫面，顯示／觸控可用 | ［　］ | ［　］ |
| M5 | Alpha SDK | 核心功能 demo-able，可交付 lead customer | ［　］ | ［　］ |
| M6 | Beta SDK（Feature Complete） | 全 HAL 到位，VINTF 宣告完成 | ［　］ | ［　］ |
| M7 | xTS Green | CTS / VTS / CTS-on-GSI / GTS 全綠 | ［　］ | ［　］ |
| M8 | PV / RC SDK | 效能功耗達標，程式碼凍結 | ［　］ | ［　］ |
| M9 | GMS 認證通過 | Reference design 取得認證 | ［　］ | ［　］ |
| M10 | MP + LTS | 量產版釋出，月度 patch 機制上線 | ［　］ | ［　］ |

### 6.1 外部相依的排程約束

- **Google AOSP source drop**：2026 年起每年 Q2、Q4 各一次，決定 rebase 窗口
- **每月 Android Security Bulletin**：綁住維運人力，MP 後長期投入
- **IP 供應商 driver release（GPU／Modem）**：最常見的隱形要徑，需書面承諾日期
- **目標 Android 版本公開發布日**：若 internal MP 排在其後不久，整合與 xTS 必須在發布前完成

---

## 7. 工作分解與人力需求

> **填寫指引**：明細請引用[工作表](soc-android-planning-worksheet.md)第 5、6 節；本文只放彙總與結論。

### 7.1 雙軸估算模型（跨 vendor API level 時適用）

若目標 vendor level 相對既有基線跨了數代，工作量有兩個獨立來源，必須相加：

> **估算人月 ＝ 前一代實際人月 ×（IP 軸係數 ＋ 版本軸係數）**
>
> - IP 軸：這顆晶片相對前一代的硬體差異（沿用 0.1／升版 0.4／新開發 1.2）
> - 版本軸：跨代的介面與合規重做（大 0.6／中 0.3／小 0.1）

### 7.2 人力彙總

| 項目 | 人月 | 說明 |
|---|---|---|
| Vendor Domain 小計 | ［　］ | ［　］ |
| System Domain 小計 | ［　］ | ［　］ |
| 跨域（整合 debug／FAE／PMO） | ［　］ | ［　］ |
| 整合與 debug 稅（×1.3） | ［　］ | 由下而上估算需加乘 |
| **調整後總人月** | ［　］ | |
| 現有可用人力 | ［　］ | |
| **缺口 / 需增補 HC** | ［　］ | ［分階段招募計畫］ |
| **參考：純版本軸成本** | ［　］ | 假設所有 IP 皆沿用，光是跨版本的代價 |

### 7.3 估算方法與交叉驗證

| 方法 | 估算結果（人月） | 信心度 |
|---|---|---|
| 類比法（上一代實際 × Delta 比例） | ［　］ | ［高／中／低］ |
| 由下而上（WBS 加總 ×1.3） | ［　］ | ［高／中／低］ |
| 由上而下（競品團隊規模反推） | ［　］ | ［高／中／低］ |

> 三者差距超過 30%，代表 Delta Map 有洞，回頭補資訊，不要直接取平均。

**常被漏算的人力**：測試自動化維護、客戶 FAE 支援、月度 security patch、跨域整合 debug、release engineering。
這幾項合計通常佔總工時 25～35%。若承諾多代 OS 升級，還要加上 MP 後數年的維運人力。

---

## 8. 品質與合規計畫

### 8.1 測試套件與責任

| 測試套件 | 範圍 | 負責單位 | 目標達成里程碑 |
|---|---|---|---|
| CTS | System Domain 相容性 | ［　］ | M7 |
| VTS | Vendor Domain HAL 實作 | ［　］ | M7 |
| CTS-on-GSI | Treble 合規 | ［　］ | M7 |
| GTS | GMS 相容性 | ［　］ | M9 |
| STS | Security 測試 | ［　］ | M8 |
| MTS / ITS / BTS / CTS-V | 模組／相機／藍牙／人工驗證 | ［　］ | M8 |

### 8.2 GMS 導入

> **填寫指引**：認證窗口有排隊時間，務必把等待期算進 M8→M9 的區間。

［待填：GMS Requirements 版本、MADA 狀態、送測窗口、測試機台與實驗室需求］

### 8.3 效能與功耗目標

［待填：benchmark 項目與目標值、與前一代及競品的對照基準］

---

## 9. 風險與對策

> **填寫指引**：等級 = 機率 × 影響（高=3、中=2、低=1）。等級 6 以上請在此逐項展開說明。
> 明細見[工作表](soc-android-planning-worksheet.md)第 7 節。

| 風險 | 機率 | 影響 | 等級 | 減緩做法 | 負責人 |
|---|---|---|---|---|---|
| Silicon 延期或 A0 需 A1 | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |
| 拿不到 Google 早期 code | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |
| IP 供應商 driver 延遲 | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |
| 目標世代 VSR / VTS 晚期條款變動 | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |
| 目標世代 GKI kernel 版本未定 | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |
| 人力未到位 | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |
| 客戶需求擴張 | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |
| M6→M9 期程被壓縮 | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |
| 多代升級維運人力未編列 | ［　］ | ［　］ | ［　］ | ［　］ | ［　］ |

---

## 10. 交付物清單

| 交付物 | 對象 | 里程碑 | 格式 |
|---|---|---|---|
| Alpha SDK | Lead customer | M5 | ［　］ |
| Beta SDK | 全客戶 | M6 | ［　］ |
| RC / PV SDK | 全客戶 | M8 | ［　］ |
| MP SDK | 全客戶 | M10 | ［　］ |
| xTS 測試報告 | 客戶／合規 | M7 | ［　］ |
| GMS 認證報告 | 客戶 | M9 | ［　］ |
| 整合文件與除錯工具 | 客戶 | M5 起滾動更新 | ［　］ |
| 月度 Security Patch | 客戶 | M10 起 | ［　］ |
| OS 升級版本 | 客戶 | MP 後逐年 | ［　］ |

---

## 11. 溝通與治理

| 機制 | 頻率 | 參與者 | 產出 |
|---|---|---|---|
| 專案週會 | 每週 | 各域 lead | 進度／阻礙清單 |
| 里程碑審查 | 每個 M | 主管、PMO、業務 | 通過／有條件通過／延期 |
| 主管報告 | 每月 | 部門主管 | 一頁摘要更新 |
| 客戶同步 | ［頻率］ | 業務、FAE、客戶 | 需求與問題追蹤 |
| 變更控制 | 需求發生時 | PMO、各域 lead | 變更影響評估與簽核 |
| Google 合規同步 | 每次 source drop 後 | 合規、各域 lead | VSR / CDD gap review |

---

## 12. 假設與待決事項

> **填寫指引**：凡是資訊未到位而採用的「最壞假設」，都必須在這裡列出，並註明何時會被實際資訊取代。
> 這一章能保護你。

| 編號 | 假設 / 待決事項 | 目前採用的假設 | 確認人 | 需確認日 |
|---|---|---|---|---|
| A1 | 目標 Android 版本公開發布確切日期 | ［　］ | ［Google 窗口］ | ［日期］ |
| A2 | 目標世代對應的 GKI kernel 版本 | ［以前一代為基準，±30% 彈性］ | ［Google 窗口］ | ［日期］ |
| A3 | EAP / PDK 早期存取 | ［　］ | ［Google 窗口］ | ［日期］ |
| A4 | Internal MP 是否含 GMS 認證 | ［　］ | ［主管］ | ［日期］ |
| A5 | 實際 tape-out / silicon back 日期 | ［　］ | ［晶片 PM］ | ［日期］ |
| A6 | ［　］ | ［　］ | ［　］ | ［日期］ |

---

*本文 Android 版本代號與 kernel 版本對應為依公開資訊整理，正式引用前請以 AOSP 官方文件與 Google 窗口確認。*
