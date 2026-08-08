# TIL: Android Vendor 升級要跨過的四道牆

升級 Android 版本時，最直覺的預期是「改一改、重編、修 build error」。
實際上編譯錯誤是最不重要的部分 —— 它們有明確的錯誤訊息，改完就過。

真正花時間的是另一類問題：**編得過、燒得進、開不了機，或是開得了機但 VTS 全紅。**

這類問題的共同來源是：Android 的 vendor 升級本質上不是編譯問題，
而是**介面契約的重新協商**。每一道牆都是 Google 在某一版立下的一條契約，
而升級就是逐條檢查你有沒有違約。

以下按實際撞到的順序整理。

---

## 牆一：KMI —— kernel 與 vendor module 的契約

### 背景

Treble 把 vendor 和 system 切開之後，還剩一個問題沒解：
kernel 本身仍然是每家 SoC 廠自己維護的分支，
導致 Google 沒辦法獨立更新 kernel。

GKI（Generic Kernel Image）就是為此而生：
Google 提供通用 kernel binary，廠商的硬體支援全部做成 **vendor module** 掛上去。

兩者之間的介面就是 **KMI（Kernel Module Interface）**。

### 為什麼它會咬人

KMI 是**二進位層級**的契約，不是原始碼層級。
它包含函式簽章、struct layout、以及被匯出的 symbol 集合。

這代表：

- 你的 vendor module 用到的 symbol，必須在 KMI symbol list 裡
- struct 欄位順序改變 → ABI 破掉，即使原始碼看起來相容
- 症狀通常是模組載入失敗，或更糟：**載入成功但行為錯亂**

### 實務要點

- 升級 kernel 版本時，先跑 ABI 比對工具，把差異列出來當作工作清單
- 需要新 symbol 時，正規做法是走上游流程把它加進 symbol list，
  而不是繞過檢查
- 「這個 symbol 為什麼不在 list 上」這個問題，答案往往是
  「因為上游認為你不該用它」—— 值得先想清楚再要求加入

---

## 牆二：VINTF —— system 與 vendor 的相容性宣告

### 背景

Treble 之後，system image 和 vendor image 可以獨立升級。
但獨立升級的前提是：**要有辦法在組合起來之前就知道它們相不相容。**

VINTF（Vendor Interface）就是這個機制。核心是兩組檔案：

- **Manifest**：我提供什麼（各自宣告自己實作的介面與版本）
- **Compatibility Matrix**：我要求什麼（宣告對方至少要提供什麼）

Vendor manifest 對上 framework compatibility matrix，
framework manifest 對上 device compatibility matrix，兩兩交叉檢查。

### 為什麼它會咬人

這個檢查在 **build time 和 boot time 都會做**。

新版 framework 的 compatibility matrix 會要求更新版本的 HAL 介面。
如果 vendor manifest 還宣告舊版本，結果不是編譯錯誤，
而是**開機時直接停住** —— 而且第一次遇到時，log 未必指向明顯的原因。

### 實務要點

升級初期先把 framework compatibility matrix 拿出來，
和自己的 vendor manifest 做 diff。
這份 diff 幾乎就是接下來要做的 HAL 遷移清單。

---

## 牆三：HIDL → AIDL —— HAL 介面的世代更替

### 背景

Treble 初期用 **HIDL** 定義 HAL 介面。
後來 Google 判斷維護兩套 IDL（AIDL 用於 framework，HIDL 用於 HAL）沒有必要，
於是推動 **stable AIDL**，讓同一套 IDL 涵蓋所有場景。

HIDL 隨後進入淘汰流程，VNDK 機制也在較新版本中被移除。

### 為什麼它會咬人

這不是換個語法就好的遷移：

- **執行緒模型不同** —— HIDL 與 AIDL 的 threadpool 行為有差異，
  移植時常見「功能都對，但偶發卡住」
- **記憶體共享機制不同** —— HIDL 的 `hidl_memory` 要換成 AIDL 的對應機制
- **版本演進規則嚴格** —— stable AIDL 對介面變更有明確的相容性規範，
  加欄位、改順序各有各的限制

### 實務要點

遷移前先確認這個 HAL 是不是真的需要遷移。
有些介面在新版仍接受舊形式，優先處理 compatibility matrix 明確要求的那些。

---

## 牆四：SELinux —— 每一版都在收緊

### 背景

Android 的 sepolicy 分成 platform 與 vendor 兩部分，
中間靠 mapping file 銜接，讓不同版本的 platform policy 和 vendor policy 能共存。

### 為什麼它會咬人

每個新 API level 都會加入新的 **neverallow** 規則 ——
明確禁止某些權限組合，而且由測試強制檢查。

升級後跑起來，會看到大量 denial。
這時最容易犯的錯是**逐條 allow 下去**：

- 有些 denial 是良性雜訊，加了 rule 只是把噪音藏起來
- 有些 denial 指向真正的架構問題，加 rule 等於掩蓋它
- 而有些你想加的 rule，會直接撞上 neverallow，根本加不了 ——
  這時候要改的是程式架構，不是 policy

### 實務要點

把 denial 先分類再處理：

1. 撞到 neverallow 的 → 架構問題，最優先，因為修法可能很大
2. 重複大量出現的 → 通常是單一根因，處理一次解決一片
3. 零星出現的 → 最後再看，有些會在前兩類修完後自然消失

---

## 貫穿全程：信任鏈

上面四道牆處理完，還有一條橫向的線要顧：**開機的信任鏈**。

```
Bootloader 驗證 vbmeta
    ↓
vbmeta 記錄各 partition 的 hash / hashtree
    ↓
dm-verity 在執行期驗證 read-only partition
    ↓
rollback index 防止降級到有漏洞的舊版
```

升級時的典型症狀：
partition 內容變了但簽章資訊沒同步更新 → 驗證失敗 → 開不了機。

另外 rollback index 是**單向**的。
測試時如果不小心燒了一個較新的版本上去，
之後想燒回舊版可能會被防降級機制擋住。這一點在開發機上特別容易踩到。

---

## 方法論：先開機，再收尾

技術細節之外，我認為最重要的是**推進順序**。

殺死這類專案的通常不是移植本身，而是尾巴 ——
sepolicy denial 一條條清、module 對不上 KMI、測試零星 fail。
這些工作的共同特徵是：**在開機之前，你無法估計它們有多少。**

所以我的做法是：

> **盡早換到一個「能開機」的狀態，哪怕功能大量殘缺。**

理由不是為了看到桌面，而是為了**把未知變成可計數**。

- 開機前：你不知道還有多少問題，也無法回答「還要多久」
- 開機後：問題變成一份清單，可以排序、可以估時、可以砍

這個轉換點的價值遠大於它的技術含量。
在有時間壓力的情況下，能不能誠實地向上回報進度，
往往取決於你有沒有先跨過這條線。

---

## 心智模型

回頭看，這四道牆其實是同一件事的四個面向：

| 牆 | 契約雙方 | 檢查時機 |
|---|---|---|
| KMI | kernel ↔ vendor module | 載入時（二進位層級） |
| VINTF | system ↔ vendor | build time + boot time |
| AIDL/HIDL | framework ↔ HAL | 編譯 + 執行 |
| SELinux | process ↔ resource | 執行時 |

Android 的整個 Treble 架構，可以理解為
**把原本隱含的耦合，一條條變成顯式的、可驗證的契約**。

升級之所以痛，是因為這些契約被寫下來了、也被機器檢查了。
但也正因為如此，升級才是**可能的** ——
在 Treble 之前，換版本等於整個 BSP 重做一次。

痛，但是是進步造成的痛。

---

## 參考

- [Android Source: GKI](https://source.android.com/docs/core/architecture/kernel/generic-kernel-image)
- [Android Source: Vendor Interface Object (VINTF)](https://source.android.com/docs/core/architecture/vintf)
- [Android Source: AIDL for HALs](https://source.android.com/docs/core/architecture/aidl/aidl-hals)
- [Android Source: SELinux](https://source.android.com/docs/security/features/selinux)
- [Android Source: Verified Boot](https://source.android.com/docs/security/features/verifiedboot)
