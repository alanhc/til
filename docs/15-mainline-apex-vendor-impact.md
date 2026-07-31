# Project Mainline 與 APEX:對 Chip Vendor 的影響

> 系列文章之十五。總覽請見《Chip Vendor 視角的 Android Build System》。

Treble 把 vendor 和 system 拆開(讓 OEM 能獨立更新 system),Mainline 則更進一步:**把 system 的一部分拆成可以由 Google 直接透過 Play 更新的模組**。對 chip vendor,這代表「你以為凍結的 framework,其實有一部分每月都在變」。本文講清楚機制,以及它與 BSP 的交互作用。

---

## 一、機制:APEX 與 Mainline 模組

### 1.1 APEX 容器

**APEX** 是系統元件的更新單元:一個帶簽章的容器,內含 native lib/binary/設定,開機早期(apexd)掛載生效——它讓「更新 libc」這種事可以像更新 app 一樣進行,但生效層級在系統底層。

- 每個 APEX 有版本、簽章(payload key + container key)、可回滾機制(brick 保護:更新後開機失敗自動 rollback)。
- `/apex/<name>/` 掛載點;預載版本在 system image,更新版本裝在 data 分區,優先生效。

### 1.2 Mainline 模組群

Google 透過 Play(Google Play System Update)按月更新的模組,逐版擴張,重點包括:ART(Android Runtime)、Conscrypt(TLS)、Media codec framework 與 extractor、DNS resolver、NNAPI runtime、Tethering、Wi-Fi/藍牙/UWB stack(部分)、Permission controller、adbd 等數十個。

**關鍵理解**:這些原本是「system image 的一部分、隨年度大版本走」的元件,現在版本節奏獨立於你的 BSP release 與 OEM 的 OTA。裝置上的 framework 行為 = 出廠 system image + 疊加的 Mainline 更新。

---

## 二、對 chip vendor 的實際影響

### 2.1 「配置漂移」:你驗證過的組合會變

BSP 驗證是對「某個 system 版本 + 你的 vendor」做的;裝置到消費者手上後,Mainline 模組持續更新,組合就漂移了。實務含義:

- **Media 模組是重災區**:codec framework 更新後與你的 Codec2 HAL 互動行為改變(buffer 協商、時序),市場端才爆的多媒體 bug,第一個要問「media APEX 版本多少」。
- **除錯 SOP 要加一條**:收集 `adb shell pm list packages --apex-only --show-versioning`(或 `dumpsys package` 的 APEX 段),把 Mainline 版本納入 bug 報告的必要欄位。
- **實驗室要能重現**:測試機隊要有「最新 Mainline」與「出廠態」兩種配置,回歸測試至少覆蓋前者。

### 2.2 介面紀律又多一層

Mainline 模組與系統其餘部分的邊界是受管理的 stable API(從早期 `@SystemApi` 級管控演進到正式介面機制);模組更新不應破壞 vendor——**前提是你沒有偷依賴內部行為**。Treble 篇講的紀律在這裡再次適用:你的元件若依賴了 media framework 的未公開行為,Mainline 每月更新都是俄羅斯輪盤。

### 2.3 MTS 與認證

- **MTS(Mainline Test Suite)** 驗證裝置與 Mainline 模組的相容性(見 xTS 篇)。
- GMS 要求裝置支援 Google Play System Update;OEM 不能任意抽換 Google 簽章的模組。部分模組允許 OEM/vendor 客製(AOSP 版本 vs Google 簽章版本的選擇),但選了 Google 版就是 Google 簽、Google 更新,你客不了製。
- **升級評估時**(見升級篇):注意當版有哪些元件「Mainline 化」了——曾經你能 patch 的 framework 檔案,可能已搬進 APEX,你的舊 patch 無處可放,必須改走正規介面。

### 2.4 Vendor APEX:機制為你所用

APEX 不只是 Google 的工具,vendor 也可以用:

```python
apex {
    name: "com.myvendor.hardware.camera",
    manifest: "manifest.json",
    key: "com.myvendor.apex.key",
    file_contexts: "file_contexts",
    vendor: true,
    binaries: ["vendor.myvendor.camera-service"],
    native_shared_libs: ["libmyvendor_isp"],
    prebuilts: ["myvendor_camera_config"],
}
```

**Vendor APEX** 把一組 HAL/lib/設定打包成單一版本化單元,好處:

- **原子性**:HAL service + 依賴 lib + 設定檔一起換,不會出現「lib 換了設定沒換」的半套狀態。
- **可獨立交付**:給客戶出 camera stack 熱修時,交付一個 APEX 而不是一堆散檔 + patch 說明。
- **版本管理**:APEX 版本號成為你和客戶之間清楚的基線語言。

成本:簽章與開機掛載的整合、sepolicy 調整(`/apex` 路徑的 label)、以及團隊要適應「以模組為單位思考」。新平台起步時就規劃 vendor APEX 邊界,比事後重構容易得多。

---

## 三、心智模型

```
                更新節奏
system image     年度大版本(OEM OTA)
Mainline APEX    每月(Google Play,繞過 OEM)      ← framework 的活動部件
vendor image     跟你的 BSP release
vendor APEX      你自己決定(可熱修)               ← 你的活動部件
kernel(GKI)     Google 更新 boot.img(LTS 節奏)
vendor modules   跟你的 BSP release
```

整台裝置是**多個獨立更新節奏的元件疊加**,「出廠即凍結」的舊心智模型已經不成立。穩定性來自每條邊界上的合約:VINTF(system↔vendor)、KMI(kernel↔modules)、Mainline stable API(模組↔系統)、AIDL freeze(HAL↔framework)。

---

## 結語

> **Mainline 把「system 會動」從年度事件變成月度常態;chip vendor 的對策只有一個字:合約。** 不依賴未公開行為、把 Mainline 版本納入除錯與回歸的維度、並反過來用 vendor APEX 把自己的交付也模組化——邊界另一側永遠在變,守住合約的人不用陪著它變。
