# xTS 認證測試實戰:CTS/VTS/GTS/STS,Chip Vendor 視角

> 系列文章之六。總覽請見《Chip Vendor 視角的 Android Build System》。

前面五篇講的是「怎麼 build 出來」;這一篇講「怎麼證明你 build 出來的東西可以出貨」。xTS 是各種相容性測試套件的統稱,對 chip vendor 而言,它不只是 QA 流程——**過不了 xTS,客戶拿不到 GMS 授權,裝置就不能預載 Google Play,等於不能出貨**。而 BSP 層的問題,最後都會變成客戶回報給你的 xTS fail。

---

## 一、xTS 家族總覽

| 套件 | 全名 | 驗什麼 | 誰最痛 |
|---|---|---|---|
| **CTS** | Compatibility Test Suite | API 行為與 CDD 相容性 | framework/BSP 都有 |
| **CTS-V** | CTS Verifier | 需要人工操作的測項(camera、sensor、NFC⋯⋯) | **chip vendor** |
| **CTS-on-GSI** | — | 刷上 GSI 後跑 CTS 子集 | **chip vendor** |
| **VTS** | Vendor Test Suite | vendor interface:HAL、kernel、Treble 合規 | **chip vendor** |
| **GTS** | GMS Test Suite | GMS app 整合、Google 服務要求 | OEM 為主 |
| **STS** | Security Test Suite | 安全性修補是否到位(security bulletin) | BSP/kernel |
| **MTS** | Mainline Test Suite | Mainline(APEX)模組相容性 | framework |
| **BTS** | Build Test Suite | build 產物檢查(test key、debuggable 等) | release 工程 |

認證邏輯:**CDD(Compatibility Definition Document)是法條,xTS 是執法**。每個 Android 版本一份 CDD,寫明「MUST/SHOULD/MAY」;xTS 把 MUST 變成自動化測項。結果上傳 Google 的 APFE(Android Partner Front End)審核,全數通過(或 waiver 核准)後才發 GMS 授權。

---

## 二、與 chip vendor 最相關的三套

### 2.1 VTS:Treble 合約的執法者

VTS 驗的正是系列文章前幾篇講的那些邊界:

- **HAL 測試**:每支宣告在 VINTF manifest 的 HAL,都有對應的 VTS 測項打真實 HAL 實作(如 `VtsHalCameraProviderV2_4Target`)。你實作的 HAL 行為不符介面定義 → fail。
- **Kernel 測試**:kernel config 白名單/黑名單(`CONFIG_*` 必開必關)、kernel ABI(GKI 裝置驗 KMI)、ltp(Linux Test Project)子集。
- **Treble 架構檢查**:sepolicy neverallow、linker namespace、`/vendor` 不得依賴 platform 私有庫、VNDK/穩定介面合規。
- **GKI 檢查**:boot.img 必須是 Google 簽章的 certified GKI(debug 自編 kernel 直接 fail)。

**CTS-on-GSI** 是 Treble 的終極驗收:把你的 vendor image 配上 Google 的 GSI(Generic System Image)開機,再跑 CTS 子集。這一關過了,才算真正證明你的 vendor 實作不偷接 framework 內部。

### 2.2 CTS / CTS-V:量大,且與硬體品質直接相關

CTS 一輪數十萬測項,絕大多數與 BSP 無關,但 fail 常落在:

- **媒體**:codec 行為(`CtsMediaTestCases`)——你的硬體 codec 輸出不符規範、edge case(奇數解析度、色彩空間轉換)出錯。
- **相機**:`CtsCameraTestCases` 對 Camera2 API 行為的嚴格檢查,ISP pipeline 的 metadata 正確性。
- **圖形**:`CtsDeqpTestCases`(數萬條 GPU 測項)——GPU driver 品質的照妖鏡,通常要 GPU IP vendor(ARM/IMG/Qualcomm)的 driver 更新配合。
- **Sensor/定位/連線**:精度、時間戳、功耗行為。

CTS-V 需要治具與人工操作(轉裝置測 sensor、拍測試圖卡測 camera),chip vendor 通常要提供公版的 CTS-V 通過基線給客戶。

### 2.3 STS:security patch 的查核

Google 每月發 security bulletin,STS 用 PoC 驗證已知 CVE 是否修補。GKI 時代 kernel CVE 由 Google 的 GKI 更新覆蓋,但 **vendor driver 的 CVE 是你的**——你的 driver 出現在 bulletin 上,你要出 patch 給所有在案客戶,而且他們的 `ro.build.version.security_patch` 聲明日期之前的洞都必須補完。

---

## 三、實際操作:Tradefed 工作流

所有 xTS 都跑在 **Tradefed(Trade Federation)** 測試框架上,操作模式一致:

```bash
# 下載對應 Android 版本與 patch level 的套件,解壓後:
./android-cts/tools/cts-tradefed
cts-tf > run cts                                   # 全量
cts-tf > run cts -m CtsMediaTestCases              # 單一 module
cts-tf > run cts -m CtsCameraTestCases -t android.hardware.camera2.cts.CaptureRequestTest#testAeMode
cts-tf > run retry --retry 0                       # 對上一輪的 fail 重跑
```

要點:

- **版本對應**:xTS 套件版本要對應裝置的 Android 版本 + security patch level,用錯版本白跑。
- **環境**:全量 CTS 要求穩定 WiFi、特定測試 AP 設定、數天的跑機時間;實驗室環境不穩定造成的 flaky fail 會浪費大量人力。
- **retry 機制**:官方允許 retry(排除 flaky);retry 後仍 fail 的才需要分析。
- **報告**:結果在 `results/` 下,`test_result.xml` + html 報告,上傳 APFE 用。

### 分析 fail 的標準流程

1. **先分類**:裝置問題 / 測試環境問題 / 測項本身的 bug(known issue)。Google 的 partner issue tracker 與 release notes 有 known issues 清單。
2. **重現**:單測項重跑 + `adb logcat`/`dmesg` 收 log。
3. **定位層級**:framework(通常升級 AOSP 就修)vs HAL vs driver vs 硬體限制。
4. **修不了的**:硬體限制且 CDD 允許例外 → 走 **waiver** 申請(APFE 提交,附技術理由),但 waiver 是例外不是常態,MUST 項基本不給。

---

## 四、Chip vendor 的 xTS 工程化

xTS 對 chip vendor 不是「出貨前跑一次」,而是持續性的工程:

**公版基線(reference pass)**:每個 SoC 平台 + Android 版本組合,你要維護一份「公版硬體全量 xTS 通過」的基線與報告。客戶專案 fail 時,第一個問題永遠是「公版過不過?」——過,就是客戶改壞的;不過,就是你的 BSP bug,而且所有客戶都中。

**CI 常態化**:全量 CTS 太慢,日常 CI 跑抽樣(BSP 相關 module:media/camera/graphics/sensor + VTS 全量),每月 security patch 合入後跑 STS,版本升級期間全量。

**與版本升級的耦合**:年度 Android 升級的收尾就是 xTS——新版本的新測項(每年 CDD 都加嚴)是升級工作量的重要來源,例如某年起強制的 performance class、新的 camera metadata 要求、新的 kernel config 白名單。**升級評估時就要先讀新版 CDD 與 xTS release notes**,而不是 build 通了才發現硬體達不到新門檻。

**GRF(Google Requirements Freeze)**:Google 允許 vendor 的 SoC 相關實作(kernel、vendor image)凍結在首發 API level,之後三個版本升級可沿用——這是 chip vendor 減少重複認證成本的重要機制,但 GRF 聲明了哪個版本、哪些 partition 沿用,VTS/CTS 會按 GRF 規則調整適用的測項集合,規劃時要與 OEM 對齊。

---

## 五、心智模型

```
CDD(法條)
  └─ xTS(執法)
       ├─ CTS / CTS-V ── API 與硬體行為 ──┐
       ├─ CTS-on-GSI ── Treble 驗收        ├─ 報告上傳 APFE
       ├─ VTS ── HAL/kernel/sepolicy 合約  │     └─ 全過或 waiver 核准
       ├─ GTS ── GMS 整合                  │           └─ GMS 授權 → 出貨
       └─ STS ── 安全修補                 ─┘
```

---

## 結語

把前幾篇的主題串起來看:Soong 的 vendor variant 規則、sepolicy 的 neverallow、GKI 的 certified boot image、簽章的 release key——**這些 build 時的紀律,每一條背後都有一個 xTS 測項在出口處等你**。所以 chip vendor 的正確姿勢是:

> **把 xTS 當成回歸測試而不是期末考——公版基線常備、BSP 相關 module 進 CI、新版 CDD 在升級規劃期就讀完。期末考才第一次看考古題的團隊,每年都會在出貨前夕加班。**

---

### 系列文章

1. 《Chip Vendor 視角的 Android Build System 總覽》
2. 《GKI 與 Kleaf Kernel Build 實戰》
3. 《Soong 與 Android.bp 實戰:vendor variant 與 VNDK》
4. 《SELinux Sepolicy 除錯實戰》
5. 《OTA 與簽章流程實戰》
6. **本文**:xTS 認證測試實戰
