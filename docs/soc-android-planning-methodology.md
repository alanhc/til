---
title: SoC Android 軟體專案規劃方法論
sidebar_label: SoC Android 規劃方法論
---

# SoC Android 軟體專案規劃方法論（Vendor Domain + System Domain）

> 適用情境：被指派規劃一顆新 SoC 的 Android 軟體專案，手上還沒有數字。
> 本文的目的不是「教 Android 架構」，而是給一條**從零到能交出可被質詢的規劃書**的路徑。
>
> 配套文件：
> [規劃書範本](soc-android-planning-proposal-template.md)、
> [工作表](soc-android-planning-worksheet.md)、
> [一頁摘要範本](soc-android-planning-onepager-template.md)。
>
> 全文為公開資訊整理與通用方法，所有數字為業界常見區間，非任何特定專案的實際值。

---

## 0. 先把「D+D」的範圍在紙上釘死

這裡的 D+D 指 **Vendor Domain + System Domain**。Treble 之後，Android 軟體以 partition 為界切成兩個域，這是整份規劃書的骨架：

| 面向 | Vendor Domain | System Domain |
|---|---|---|
| Partition | vendor / vendor_dlkm / odm / odm_dlkm | system / system_ext / product |
| 誰擁有 | **晶片商** | Google AOSP + OEM 客製 |
| 內容 | Bootloader、Kernel（GKI + vendor modules）、所有 HAL、驅動、韌體、TEE、DSP/NPU stack | Framework、SystemUI、Settings、GMS、OEM app |
| 相容性依據 | Vendor API Level → **VSR-N** | CDD |
| 主要測試 | VTS、CTS-on-GSI | CTS、GTS、STS、MTS |
| 晶片商的槓桿 | 幾乎 100% 自己做 | 多半是「配合 + 驗證 + 客製 hook」 |

**開場第一件事**：確認負責範圍是「Vendor Domain 全包 + System Domain 配合」，還是「兩域都要含 reference design 的完整交付」。這兩者人力差 2～3 倍。

---

## 1. 第 1 週：不要寫文件，先收集 12 個關鍵輸入

規劃書的品質 = 輸入資訊的品質。以下每一項都寫清楚「問誰」與「拿不到時的最壞假設」。

### A. 矽晶時程（問：晶片 PM / RTL 主管）

| # | 要問到什麼 | 為什麼決定一切 |
|---|---|---|
| 1 | **「明年」指的是 tape-out、silicon back，還是客戶 MP？** | 這三者差 12～18 個月，是最常見的雞同鴨講 |
| 2 | Tape-out / A0 silicon back / EVB 到手 的預定日期 | 所有 milestone 的錨點 |
| 3 | 是否有 pre-silicon 平台（Emulator / FPGA / Virtual Platform）、何時可用 | 決定能提前多久開工，通常可省 6～9 個月 |

> 最壞假設：若無 pre-silicon，所有 bring-up 工作必須排在 silicon back 之後，時程直接往後推 6 個月以上，這點要在規劃書明寫成風險。

### B. 相對前一代的差異（問：架構師 / SoC 定義文件）

| # | 要問到什麼 |
|---|---|
| 4 | **參考基線是哪一顆晶片？** 哪個 branch 可以 fork？ |
| 5 | IP delta 清單：CPU / GPU / ISP / VPU / NPU / Modem / DSP / TEE / Memory subsystem，逐項標「沿用 / 升版 / 全新 / 換供應商」 |

> **這張 delta 表是整個專案工時的唯一真實來源。** 沒有它，人力估算就是拍腦袋。
> 「沿用」約 0.1 人月驗證；「升版」約前一代 30～50% 工時；「全新 IP」約前一代 100～150% 工時。
>
> 若目標 vendor API level 相對既有基線跨了好幾代，除了 IP 軸還要疊加版本軸，見第 6 節。

### C. Google 面（問：與 Google 對口的窗口 / 合規主管）

| # | 要問到什麼 | 判斷重點 |
|---|---|---|
| 6 | Target Android release 是哪一版？對應的 GKI kernel 版本？ | 版本未公布前，kernel 與 vendor module 適配工時只能給區間 |
| 7 | Target **Vendor API Level / VSR-N** | 若建在尚未定版的世代，需追蹤 preview/beta 條款 |
| 8 | 是否有 EAP / PDK 早期存取？何時拿得到 code？ | MP 若排在公開發布後不久，這是 Go/No-Go 級前提 |
| 9 | 目標是否含 GMS 認證（自家 reference design 先過，還是交給客戶過）？ | 決定 xTS 測試機台、人力、實驗室投資 |

### D. 客戶與內部（問：業務 / PM / 主管）

| # | 要問到什麼 |
|---|---|
| 10 | 首發客戶是誰、量產目標日、產品型態（手機 / 平板 / 車機 / IoT）、目標市場（是否含歐盟、中國、北美，影響法規與 GMS） |
| 11 | 客戶特殊需求 delta（自家 camera 演算法？自家 AI 框架？特殊 modem？） |
| 12 | 團隊現況：各域現有人力、下一年可用度、上一代專案**實際**投入工時（不是當初估的） |

> **實務建議**：把上面 12 題做成一頁表格，直接寄給對應的人，標明「請於 X 日前回覆，未回覆將以最壞假設寫入規劃書」。這比開會有效，而且留下書面依據。

---

## 2. 第 2 週：畫兩張圖，規劃書就有骨架了

### 圖一：Delta Map（工時來源）

橫軸是 Vendor Domain 的模組清單，縱軸標三種狀態，每格填「預估人月」與「信心度（高/中/低）」。
**若同時跨了 vendor API level，需要兩張：IP 軸一張、版本軸一張。**

### 圖二：Treble 責任分域圖

一張圖畫出 vendor / system 的分界，把每個模組歸位，並用顏色標「我方做 / 客戶做 / IP 供應商做 / Google 提供」。

這張圖的價值：**開會時所有「這誰做？」的爭論，指著圖講就結束了。**

---

## 3. 時程用「反推法」，不要用「順推法」

從客戶 MP 日往回推，這是唯一能讓主管買單的排法。典型里程碑鏈：

- **M0** Kick-off / SW Plan Freeze
- **M1** Pre-silicon 環境就緒（FPGA/Emulator 可跑 kernel boot）
- **M2** Silicon Back（A0 到手）
- **M3** Boot to Shell（kernel + 最小 vendor modules 起來）
- **M4** Boot to Home（Android UI 出畫面）
- **M5** Alpha SDK（核心功能 demo-able，可給 lead customer）
- **M6** Beta SDK（Feature Complete，全 HAL 到位）
- **M7** xTS Green（CTS / VTS / CTS-on-GSI / GTS 在 EVB 上全綠）
- **M8** PV / RC SDK（效能功耗達標，凍結）
- **M9** GMS 認證通過（reference design）
- **M10** MP Release + 進入 LTS / 月度 security patch 維運

**業界常見區間（可當作沒有內部數據時的起手值）：**

| 區段 | 全新架構 | 衍生型（derivative） |
|---|---|---|
| M0 → M2（pre-silicon） | 9～12 個月 | 4～6 個月 |
| M2 → M4（bring-up） | 4～8 週 | 1～3 週 |
| M4 → M6（feature complete） | 6～9 個月 | 3～5 個月 |
| M6 → M9（xTS + GMS） | 3～5 個月 | 2～3 個月 |
| **M0 → MP 合計** | **約 20～26 個月** | **約 12～16 個月** |

> 反推之後如果發現「起跑日已經過了」——**這正是要交給主管的最重要一句話**，而不是硬把格子塞滿。

**排程時務必卡住的三個外部相依：**

1. Google AOSP source drop（2026 起每年 Q2 / Q4）——rebase 窗口
2. 每月 Android Security Bulletin——SPL 承諾會綁住維運人力
3. IP 供應商 driver release（GPU / Modem 廠）——這是最常見的隱形要徑

---

## 4. Vendor Domain 工作分解

逐項標「沿用 / 升版 / 新開發」＋「跨版本衝擊（大/中/小）」：

- **Boot chain**：BootROM / SPL / LK 或 U-Boot / ABL、fastboot、AVB、Verified Boot、DTBO
- **Kernel**：GKI branch 選定、vendor modules、KMI 相容、DDK、device tree、pKVM/Virtualization
- **Graphics**：GPU driver、Gralloc、HWComposer、Vulkan/GLES 一致性（含 Khronos CTS）
- **Camera**：ISP tuning、Camera HAL3/AIDL、ITS 測試、HDR/Sensor 廠支援矩陣
- **Media**：Codec2、硬體編解碼、DRM / Widevine L1、HDCP
- **Audio**：Audio HAL、DSP firmware、低延遲路徑
- **Connectivity**：Wi-Fi / BT / GNSS HAL、供應商 firmware 版本綁定
- **Modem / RIL**（若有）：通常是單一最大工作包，要獨立列
- **Security / TEE**：TEE OS、Keymint、Gatekeeper、StrongBox、fTPM、fuse/provisioning 流程
- **AI / NPU**：NN HAL、compiler/runtime、model zoo 驗證
- **Power / Thermal / Perf**：Power HAL、thermal HAL、DVFS 調校、benchmark 目標
- **Sensors / USB / Vibrator / Health / Display panel**
- **VINTF**：manifest、compatibility matrix、Vendor API Level 宣告
- **16 KB page size**：所有 native code / driver / prebuilt library 的對齊與驗證
- **Release engineering**：build system、CI、SDK 打包、客戶交付流程

## 5. System Domain 工作分解

- AOSP rebase 策略與 branch 管理（對齊 Q2 / Q4 source drop）
- GSI boot 測試（Treble 合規證明）
- Framework 客製與 RRO overlay 策略
- xTS：CTS / CTS-V / CTS-on-GSI / GTS / STS / MTS / ITS / BTS 的機台與人力
- GMS 導入：GMS Requirements、MADA、認證窗口排隊時間
- Security：月度 SPL 承諾、patch 回移機制、支援年限
- 客戶 SDK 文件、reference app、除錯工具鏈

---

## 6. 人力估算：跨 vendor API level 時用雙軸模型

若目標 vendor API level 相對既有基線跨了數代，工作量有兩個獨立來源，必須相加：

> **估算人月 ＝ 前一代實際人月 ×（IP 軸係數 ＋ 版本軸係數）**
>
> - **IP 軸**：這顆晶片相對前一代的硬體差異 —— 沿用 0.1／升版 0.4／新開發 1.2
> - **版本軸**：跨代的介面與合規重做 —— 大 0.6／中 0.3／小 0.1
>
> 係數為經驗值起手區間，導入時應以自家上一代專案的實際工時回歸校正。

版本軸衝擊通常為「大」的模組：Kernel／GKI 世代跳躍、Graphics、Camera、Media、Security/TEE、VINTF、
16 KB page size、AOSP rebase、xTS、GMS。

**額外算一個數字：「純版本軸成本」** —— 假設所有 IP 皆沿用，光是跨版本要付多少人月。
這是說明「不能當衍生型估」的關鍵證據。

**三種方法交叉驗證：**

1. **類比法**：上一代專案實際人月 × Delta 比例係數
2. **由下而上**：WBS 每一項各自估，加總後 ×1.3（整合與 debug 稅）
3. **由上而下**：同級競品的軟體團隊規模反推

三者差距若超過 30%，代表 Delta Map 有洞，回頭補資訊，不要直接取平均。

> 別忘了把這些常被漏掉的人力算進去：測試自動化維護、客戶 FAE 支援、security patch 月更、
> 跨域整合 debug、release engineering。這幾項合計通常佔總工時 25～35%。
>
> 若 vendor API level 承諾了多代 OS 升級，還要額外編列 MP 後數年的升級維運人力。

---

## 7. 該寫進規劃書的風險（主管一定會問）

| 風險 | 觸發訊號 | 減緩做法 |
|---|---|---|
| Silicon 延期 / A0 有重大 bug 需 A1 | Tape-out 日期反覆變動 | Pre-silicon 覆蓋率目標、A1 情境的第二版時程 |
| 拿不到 Google 早期 code | EAP 申請未確認 | MP 緊貼公開發布時屬 Go/No-Go 級，需最優先確認 |
| IP 供應商 driver 延遲 | 供應商未給書面日期 | 列為要徑、要求書面承諾、準備 fallback 版本 |
| VSR / VTS 晚期條款變動 | vendor 建在尚未定版的世代 | 透過 EAP 追蹤 preview/beta 要求，預留返工 buffer |
| 目標世代的 GKI kernel 版本未定 | Google 尚未公布 | 先以前一代為基準規劃，kernel 工時預留 ±30% |
| 人力不到位 | HC 未核准 | 分階段招募計畫 + 功能降級的 Plan B |
| 客戶需求擴張 | 首發客戶未定案 | 明訂 feature freeze 日與變更控制流程 |
| 多代升級維運人力未編列 | 只規劃到 MP | MP 前 3 個月啟動維運編制與年度預算 |

---

## 8. 交給主管的第一版，只需要一頁

不要一開始就交 40 頁。第一次回報用一頁講清楚四件事：

1. **範圍**：這顆晶片的 Android 軟體工作 = Vendor Domain 全包 + System Domain 的 X、Y、Z
2. **反推時程結論**：客戶要 MP 的日子往回推，起跑日是 ____，目前落後/提前 ____ 個月
3. **關鍵未知**：第 1 節那 12 題裡，還有哪幾題沒答案，卡在誰身上
4. **要主管決定的事**：通常是 2～3 件

**主管要的不是完美的計畫，是「你知道哪裡有洞、需要他做什麼決定」。**

---

## 9. 常見誤區

- 資訊還沒收齊就開始填甘特圖 → 會做出一份沒人相信的漂亮圖
- 只規劃到「Feature Complete」→ 從 feature complete 到 GMS 過認證通常還要 3～5 個月，這段最容易被砍掉
- 忽略 System Domain → 以為晶片商只做 vendor，結果 xTS 和 GMS 沒人負責
- 忘了維運 → MP 只是開始，月度 security patch 與 LTS 是多年承諾
- 用「順推」排程 → 從今天往後排，得出的日期永遠對不上客戶要的 MP 日
- **只看 IP 差異估工時** → 跨版本的介面與合規重做是另一條獨立成本線

---

## 附錄：本文引用的外部事實

- Android 版本代號：U = Android 14、V = 15、B = 16（Baklava）、C = 17（Cinnamon Bun）、D = 18
- GKI 對應：Android 16 → android16-6.12；Android 17 → android17-6.18；更新世代以 Google 公布為準
- 2026 年起 Google 改為每年 Q2、Q4 兩次向 AOSP 發布原始碼
- Vendor API Level 決定適用的 VSR 版本；build against N 的 vendor image 可搭配 system 至 **N+3**
- Google 要求的測試套件包含 CTS、VTS、CTS-on-GSI、GTS、CTS-V、ITS、BTS、STS、MTS

上述為公開資訊整理，正式引用前請以 AOSP 官方文件與各自的 Google 窗口確認。
