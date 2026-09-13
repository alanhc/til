# 工廠與量產流程實戰:Chip Vendor 視角

> 系列文章之十三。總覽請見《Chip Vendor 視角的 Android Build System》。

從 build server 上的 image 到產線上每分鐘下線一台的手機,中間隔著一整套很少有文件的工程:燒錄、校準、產測、序號化、防呆。這塊網路上資料最少,但每家 vendor 都要做——本文把骨架整理出來。

---

## 一、量產軟體的組成

量產用的不是日常的 userdebug image,而是一套「工廠軟體包」:

| 元件 | 用途 |
|---|---|
| **燒錄工具 + 燒錄 image** | 產線第一站:把全部 partition 寫進空白 flash |
| **工廠 build(factory image)** | 帶產測 app/daemon 的特殊 build,或 user build + 工廠模式開關 |
| **產測工具(PC 端)** | 治具控制、測試流程排程、結果上傳 MES |
| **校準工具鏈** | RF/sensor/camera/display 校準與資料寫入 |
| **量產 user build(正式簽章)** | 最終燒進裝置的軟體(見 OTA/簽章篇) |
| **檢查工具** | 出貨前的軟體狀態稽核(fuse、鎖定、版本) |

兩種常見策略:(a) 專用 factory build,測完重刷量產 build;(b) 量產 build 內建工廠模式(特殊組合鍵/AT 命令/adb 進入,出貨前禁用)。(b) 省一次燒錄時間,但要保證工廠後門在出貨態完全關閉——**這是安全審查重點**。

---

## 二、產線流程(典型)

```
SMT 貼片
 └─ ① 首次燒錄(空白 flash)
     │   SoC 進 ROM 燒錄模式(EDL/BROM,見開機流程篇)→ 燒錄工具灌全部 partition
 └─ ② 開機測試(PCBA 測試)
     │   產測程式跑:CPU/記憶體/storage 快篩、各 IP 基本功能
 └─ ③ 校準站(視產品:RF、sensor、camera、display)
 └─ ④ 組裝後整機測試(MMI 測試)
     │   人機互動測項:螢幕、觸控、喇叭/麥克風、震動、鍵、相機拍照
 └─ ⑤ 序號化與個人化
     │   寫入 SN、WiFi/BT MAC、IMEI(通訊產品)、DRM keybox(Widevine)、attestation key
 └─ ⑥ 出貨態設定
     │   燒 fuse(secure boot 正式生效)、鎖 bootloader、關工廠後門、重置資料
 └─ ⑦ 出貨檢查(OQC 抽檢)
```

每一站的結果上傳 **MES(製造執行系統)**,與 SN 綁定——追溯性是量產的生命線(某批次出問題時,靠它圈出受影響範圍)。

---

## 三、關鍵技術點

### 3.1 燒錄

- **ROM 模式燒錄**:利用 SoC BootROM 的下載模式(EDL/BROM/DFU),不依賴 flash 內容,是空板與救磚的通道。燒錄工具是 chip vendor 提供的核心資產;產線關心的只有兩件事:**速度**(決定產能,常用多口併燒)與**成功率**。
- **燒錄 image 的組裝**:與 `fastboot` 刷機包不同,通常是自家格式(分區表 + sparse image + 校驗),從 target_files/out 產物打包而來——這條打包 pipeline 也是 BSP 要維護的。
- **防呆**:image 與機型的匹配檢查(燒錯型號直接擋)、防降級。

### 3.2 校準(calibration)

硬體個體差異必須逐台校準,資料寫入專用分區(通常叫 `persist`、`nvdata`、`nvram` 類,**OTA 與恢復原廠都不得清除**):

| 類別 | 內容 |
|---|---|
| RF | WiFi/BT/蜂窩的功率、頻偏校準(儀器站,通訊產品的產能瓶頸) |
| Camera | 模組級(AWB golden、鏡頭 shading、雙攝標定)+ 整機級 |
| Sensor | gyro/accel 零偏、proximity 閾值、壓力計 |
| Display | 白點/gamma 校準(高階面板)、亮度對應 |
| 電量計 | 電池模型參數 |

BSP 的責任:校準資料的**讀寫工具與格式**、driver 開機載入校準值的路徑、資料遺失時的 fallback(golden 預設值 + 明確告警)。**persist 分區的備份/恢復機制**(壞了等於整機報廢級的維修)要在設計期就定案。

### 3.3 序號化與金鑰灌注

- SN/MAC/IMEI 寫入受控分區,寫入工具要有權限管制(IMEI 是法規敏感項)。
- **DRM keybox(Widevine L1)與 attestation key**:在受控環境灌入 TEE 保護的儲存區,金鑰來自 Google/DRM 授權方,產線要有金鑰管理流程(數量對帳、防重複灌注)。
- 這些資料同樣必須在 persist 類分區,且與 secure storage 綁定(防拷貝到另一台)。

### 3.4 出貨態(final fusing)

出貨前最後一站做的事不可逆,清單要死死管住(對照 OTA/簽章篇的量產檢查清單):

1. 燒 secure boot fuse(從此只認正式簽章)
2. `fastboot flashing lock` + 確認 AVB green state
3. 禁用工廠模式入口、debug 介面(serial console!)
4. 確認 `ro.debuggable=0`、非 test-keys、security patch 版本正確
5. rollback index 設定
6. 資料清除(factory reset),進入待售狀態

**檢查工具自動化**:每台出貨前跑一個 checker(讀 fuse 狀態、prop、分區摘要),不合格擋下——依賴人工核對必然漏。

---

## 四、返修與售後路徑

- **RMA 診斷**:售後站需要診斷工具(比產線 MMI 簡化),以及**授權的重刷通道**——鎖定裝置的重刷要走簽章授權(如簽過的 unlock token),不能給售後留萬能後門。
- **資料處理**:返修機的用戶資料處理流程(法務要求)。
- **維修後校準**:換件(主板、camera 模組)後對應的校準要重做——維修工具要能單站觸發。

---

## 五、組織與交付

Chip vendor 在這塊的交付物,常被低估但客戶天天用:

- 燒錄工具 + 文件(多口併燒、產線部署指南)
- 產測 framework(可讓 ODM 增刪測項的架構,而不是寫死的 app)
- 校準工具鏈 + 治具規格建議
- MES 對接的參考實作(結果格式、上傳協定)
- 《量產軟體 checklist》——把第 3.4 節做成正式文件隨 BSP release(見升級篇的 release 內容)

**產線問題的 debug 特性**:時間壓力極大(停線一小時 = 真金白銀)、環境難重現(治具、廠內網路、特定批次)。標準做法是產線問題分級 SOP + 遠端 log 通道 + 廠內駐點工程師的權限工具箱。

---

## 結語

> **量產流程的本質是「把個體差異變成資料,把不可逆操作變成受控步驟」:校準把硬體差異收進 persist,序號化把身份寫進裝置,fusing 把信任根鎖死。** 這些流程沒有 xTS 幫你把關,防呆與稽核工具就是你自己的 CTS——出貨態 checker 的每一條規則,背後都是一次真實事故。
