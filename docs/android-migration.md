---
sidebar_label: Android Migration
---

# Android Migration:一次大版本升級,整條供應鏈要做什麼

> 面向對象:Android 產業鏈的工程師與 PM。本文是系列第一篇,拆解「Android 大版本遷移」這件事的全貌——為什麼升級這麼難、每年新版本落地時 Google、晶片商、系統廠三方各自要做什麼,以及 Project Treble 如何從架構上改寫遊戲規則。它是後兩篇〈[Vendor Freeze](./vendor-freeze.md)〉與〈[Android Kernel](./android-kernel.md)〉的起點。

---

## 一、問題:為什麼 Android 升級這麼慢

每年 Google 發一版新 Android,但對使用者而言,「什麼時候升到」的答案從一個月到永遠都有。這個生態長年被詬病的更新遲滯,根源是一台 Android 手機的軟體,是由三層來源疊起來的:

```
AOSP(Google 的開源基底:framework、system)
   +  SoC BSP(晶片商的 kernel、HAL、driver)
   +  OEM 客製(系統廠的 UI、app、板級 driver、運營商需求)
   =  一台裝置上實際跑的那份 Android
```

大版本遷移的困難,就在於這三層由不同公司維護、有不同的商業誘因,而升級要求它們**依序**動起來。相較之下,iPhone 的硬體、SoC、OS 全由 Apple 一手掌握,一次決策就能推;Android 的每一版升級,都是一次跨越三家公司的供應鏈協作。

---

## 二、遷移到底在遷什麼:一次升級的工作分解

當新一版 AOSP 釋出,一台既有裝置要升上去,底下這條鏈上的每一環都得完成:

1. **晶片商更新 BSP**:把 kernel、HAL、vendor 實作對齊新版 Android 的要求(新 HAL 版本、新 kernel 最低版本、新的 VSR),交付新的 BSP。**這一步是整條鏈的頭,也最重**。
2. **系統廠 rebase 自家客製**:OEM/ODM 把多年累積的 framework 私有 patch、UI、app,rebase 到新版 AOSP 上,再整合晶片商的新 BSP。
3. **板級適配**:觸控、面板、充電、感測器等 driver 隨新 kernel 重新驗證。
4. **合規認證**:重跑 CTS(相容性)、GTS(Google 服務)、VTS(HAL 相容),過不了不能出貨、不能帶 GMS。
5. **運營商與區域需求**:電信商 TA、各區域法規需求重新驗證。
6. **OTA 打包與推送**:產生升級包、灰度發佈、監控回報。

這條鏈的致命傷是**串行依賴**:系統廠要等晶片商的新 BSP 才能開工,而晶片商對一顆賣出幾年的舊 SoC 每年重做一輪適配,是不帶新營收的純沉沒成本——於是舊平台的升級,往往就卡在「晶片商不再支援」這一關。這正是後續 [Vendor Freeze](./vendor-freeze.md) 與 [GKI](./android-kernel.md) 兩套制度要拆解的核心痛點。

---

## 三、轉捩點:Project Treble

2017 年隨 Android 8.0 推出的 **Project Treble**,是這個生態第一次從架構上正面處理升級難題。它做的事只有一件,但影響深遠:**把 `system`(framework)與 `vendor`(晶片商實作)用一組穩定介面切開**。

- **穩定的 vendor 介面**:framework 與 HAL 之間改用版本化的 **HIDL**(後來演進為 **AIDL**)溝通,不再是編譯期綁死的直接呼叫。
- **VINTF 與相容性矩陣**:vendor 側的 manifest 宣告自己實作了哪些 HAL 版本,framework 側的 **FCM(Framework Compatibility Matrix)** 宣告它要求哪些,開機與 OTA 時做匹配。介面相容,兩邊就能各自獨立更新。
- **GSI(Generic System Image)**:Google 提供一份通用的 `system` image,可以蓋在任何 Treble 相容裝置的 vendor 之上開機——這既是相容性的測試手段,也證明了 system 與 vendor 確實被切開了。

Treble 的成果是:理論上,**換掉 framework 不必動 vendor**。這讓「新 AOSP 一出、系統廠就能在既有 vendor 上先 rebase framework」成為可能,拆掉了那條最長的串行依賴。

但 Treble 只解決了一半。它保證了**介面相容**,卻沒解決**要求追加**:Google 每年新版的 VSR、新 HAL 版本、新 kernel 最低版本,在早期仍會**回溯適用**到升級中的舊裝置,晶片商還是得年年重做一次 vendor 實作。這個「Treble 沒解決的另一半」,就是系列第二篇 [Vendor Freeze](./vendor-freeze.md) 的主題。

---

## 四、三方視角:遷移的工作怎麼分

同一次升級,三方看到的是完全不同的工作與誘因:

- **Google**:出 AOSP、定義 CDD/VSR/CTS 這套「合規契約」、維護 GSI 與相容性工具。它的目標是**更新覆蓋率**——讓安全補丁與新版本推得下去,因為這才是 Android 相對 iOS 最大的弱點。
- **晶片商(Chip Vendor)**:交付對齊新版的 BSP,是整條鏈的起點。對它而言,舊 SoC 的每年適配是純成本,如何用更少的工去支撐更長的年限,是商業模式問題。
- **系統廠(OEM/ODM)**:rebase 自家客製、跑認證、運維 OTA。它夾在中間——能升到哪一版,地板由晶片商的支援決定;要投多少工,取決於自家 code 當年寫得夠不夠乾淨。

這個三方框架,是理解整個系列的骨架:**每一項長期支援的制度(Treble、GRF、GKI),本質都是在重新分配這三方的工作與自由度。**

---

## 五、Treble 之後:通往 Freeze 與 GKI

Treble 切開了 system 與 vendor,但兩個結構性難題還在:

- **要求年年追加**,逼著晶片商重做 vendor 實作 → 系列第二篇 [Vendor Freeze](./vendor-freeze.md):Google 用 GRF/Longevity GRF 凍結要求,換取更長支援年限。
- **kernel 經過四層 fork**,碎片化到安全補丁滲不下去 → 系列第三篇 [Android Kernel](./android-kernel.md):GKI 把 kernel 切成 Google 核心本體 + vendor module。

一句話串起整個系列:**Treble 切開了 system 與 vendor,GRF 凍結了 vendor 的要求,GKI 收編了 kernel**——三者共同把「Android 大版本遷移」從一場每年重來的供應鏈苦役,逐步變成可規劃、可長期維護的工程。

---

## 六、三方對照與總結

| | Google | Chip Vendor | 系統廠(OEM/ODM) |
|---|---|---|---|
| **在遷移中的角色** | 出 AOSP、定合規契約、維護 GSI | 交付對齊新版的 BSP(鏈的起點) | rebase 客製、跑認證、運維 OTA |
| **核心誘因** | 更新覆蓋率、生態安全 | 用更少的工支撐更長年限 | 用更低成本升級、兌現更新承諾 |
| **最痛的地方** | 碎片化讓補丁推不下去 | 舊 SoC 的年年適配是純沉沒成本 | 卡在晶片商 BSP 的串行依賴 |
| **Treble 帶來的改變** | 有了 GSI 這把相容性量尺 | vendor 與 framework 解耦 | 能先在舊 vendor 上 rebase framework |

Android 大版本遷移的本質,是一條跨三家公司的串行供應鏈。它的歷史,就是 Google 用一套接一套的架構制度(Treble → GRF → GKI),把這條鏈上的依賴逐一切斷、把工作重新分配的過程。看懂這條主線,後面兩篇的凍結與 kernel 收編,就都只是同一個故事的不同章節。

---

## 延伸閱讀

- 系列第二篇:[Vendor Freeze:一份 BSP 走七年](./vendor-freeze.md)
- 系列第三篇:[Android Kernel:從手工藝品到標準化零件](./android-kernel.md)
- [Project Treble — Android Developers Blog](https://android-developers.googleblog.com/2017/05/here-comes-treble-modular-base-for.html)
- [Vendor Interface (VINTF) — AOSP](https://source.android.com/docs/core/architecture/vintf)
- [Generic System Image (GSI) — AOSP](https://source.android.com/docs/core/tests/vts/gsi)
- [Vendor Software Requirements (VSR) — AOSP](https://source.android.com/docs/compatibility/vsr)
