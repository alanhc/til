# 搞懂 Android 的三種 Build Variant:user、userdebug 與 eng 差在哪

在 Android(AOSP)開發流程裡,`lunch` 選 target 時你一定看過類似 `aosp_arm64-userdebug` 這種寫法。中間那個 `userdebug` 就是 build variant(建置變體),它決定了刷出來的 image「多開放、多好除錯、多接近正式出貨版」。理解這三種 variant 的差異,是判斷「這顆 bug 該用哪種 image 重現」「效能數據能不能信」的基礎。

本文完整說明 `user`、`userdebug`、`eng` 三種 variant 的定位、底層屬性差異,以及實務上該怎麼選。

---

## 一、三種 variant 的定位

Build variant 本質上是同一份原始碼、用不同的編譯設定產生的三種 image。它們的差異不在功能,而在「安全鎖定程度」與「除錯便利性」的取捨。

**user——出貨版**

這是真正交到消費者手上的版本,鎖得最死。系統以最高安全性運作,不能 root,幾乎所有除錯管道都關閉。手機店裡買到的量產機跑的就是 `user` build。

**userdebug——可除錯的出貨版**

行為幾乎等同 `user`,做了同樣的最佳化,但額外保留了除錯能力(可提權為 root、開啟部分 log)。它是 QA、測試、driver 驗證的主力,因為它「跟出貨版夠像,又抓得到問題」。

**eng——工程版**

給開發者在實驗室快速迭代用的,開放程度最高。預設就是 root、debug 工具全開、不做效能最佳化,重視的是「改 code、重刷、驗證」的速度,而不是跑起來像不像正式機。

---

## 二、底層屬性差異

三種 variant 的差別,最終體現在幾個系統屬性(system property)與模組安裝規則上。以下逐項拆解。

### 1. ro.secure 與 root 權限

`ro.secure` 決定 adb daemon 是否以安全模式啟動:

- `eng`:`ro.secure=0`,adb 開機後直接就是 root,不需要任何提權動作。
- `userdebug`:`ro.secure=1`,但因為 `ro.debuggable=1`,可以用 `adb root` 重啟 adbd 取得 root。
- `user`:`ro.secure=1` 且 `ro.debuggable=0`,`adb root` 直接被拒絕,無法提權。

這是三者最常被感受到的差異:`eng` 隨手就 root,`userdebug` 要多打一個指令,`user` 根本不給。

### 2. ro.debuggable

這個屬性控制整個系統是否「可被除錯」,影響 `adb root`、`jdwp` 附加除錯器、部分 SELinux 與 log 行為:

- `eng` 與 `userdebug`:`ro.debuggable=1`
- `user`:`ro.debuggable=0`

換句話說,只要你需要接除錯器或看比較深的 log,就不能用 `user`。

### 3. 模組安裝規則(module tags)

AOSP 的 build 系統會依 variant 決定哪些模組要被包進 image。傳統上模組可以標 `eng`、`debug`、`user` 等 tag(現代寫法用 `LOCAL_MODULE_TAGS` 或對應的 Soong 屬性):

- `eng`:安裝標了 `eng`、`debug` 的模組,加上所有沒指定 variant 的產品模組——也就是「裝好裝滿」,連工程專用工具都在。
- `userdebug`:安裝標了 `debug` 的模組,以及 product 設定要求的模組,但**不含** `eng` 專屬模組。
- `user`:只安裝 product 明確要求的模組,最精簡。

所以有些只在 `eng` 才存在的測試工具或 binary,一旦切到 `userdebug` 就會消失——這常常是「在我機器上有、在測試機沒有」的原因。

### 4. dexpreopt 與效能最佳化

- `eng`:預設關閉 dexpreopt(APP 的 dex 不在編譯期預先最佳化)。好處是 build 快、改 framework 後重刷快;代價是**開機慢、跑起來慢**。
- `userdebug` / `user`:啟用 dexpreopt 等最佳化,開機與執行效能接近真實出貨狀態。

這一點對效能測試至關重要——**在 `eng` build 上量到的開機時間、流暢度、耗電都不能拿來當出貨依據**,因為它根本沒最佳化。

### 5. Log、assert 與其他行為

`eng` build 通常開著更多 verbose log、保留 `LOG_NDEBUG` 相關輸出,某些 assert/檢查也更嚴格(方便早期抓錯)。`user` build 則會關閉大量除錯 log 以節省效能與避免資訊外洩。`userdebug` 介於兩者之間,偏向 `user` 但保留關鍵除錯 log。

---

## 三、對照表

| 項目 | eng | userdebug | user |
|------|-----|-----------|------|
| 定位 | 工程開發版 | 可除錯的出貨版 | 正式出貨版 |
| `ro.secure` | 0 | 1 | 1 |
| `ro.debuggable` | 1 | 1 | 0 |
| 預設 root | 是(開機即 root) | 否(可 `adb root` 提權) | 否(無法提權) |
| 安裝模組 | eng + debug + 全部 | debug + product 要求 | 僅 product 要求 |
| dexpreopt / 最佳化 | 關閉 | 啟用 | 啟用 |
| 開機/執行效能 | 慢(未最佳化) | 接近出貨 | 出貨等級 |
| 除錯 log | 最多 | 中等 | 最少 |
| 主要用途 | 快速改 code、重刷 | QA/測試/driver 驗證 | 消費者 |

---

## 四、實務上該怎麼選

**用 eng 的時機**

你正在頻繁改 framework 或 native 層、需要立刻 root、需要工程專用工具、而且不在乎效能表現——例如 bring-up 新板子、debug 開機流程、快速試錯。重點是迭代速度。

**用 userdebug 的時機**

你要做 QA、驗收、跑效能測試,或是重現「只有在接近正式環境才會出現」的 bug。因為它做了與 `user` 相同的最佳化,量到的數據可信;又保留 root 與 log,問題抓得到。大多數測試部門的日常 image 都是 `userdebug`。

**用 user 的時機**

出貨前的最終驗證,以及實際交付給消費者。任何要送 CTS/GMS 認證、要模擬真實使用者環境、或要確認除錯管道確實關閉的場景,都必須用 `user`。

---

## 五、一句話總結

`eng` 是「全開、方便改,但離出貨版最遠」;`user` 是「完全鎖死的出貨版」;`userdebug` 則是「跟出貨版幾乎一樣,只是留了一道除錯後門」。

因此有一個實務原則值得記住:**要重現使用者問題、要量效能、要做 QA,請用 `userdebug` 而不是 `eng`**。`eng` 沒最佳化又裝了一堆工程模組,它的行為不能代表使用者手上的機器;而 `user` 又鎖到你抓不了問題。`userdebug` 正是為了這個「像出貨、又可除錯」的甜蜜點而存在。
