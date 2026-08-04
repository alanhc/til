# 從 vendor 分割區看 Project Treble

### 一份寫給系統移植與 ROM 開發者的架構筆記

---

## 前言：這篇文章想解決的問題

如果你做過 Android 系統移植，大概都遇過這個場景：手上一台冷門機器，原廠停在 Android 11 再也不更新，你想知道能不能刷一個新版 GSI 上去。你 Google 了半天，找到一堆論壇貼文，每篇的指令都不太一樣，有的要刷 vbmeta，有的說要先 `delete-logical-partition`，有的說直接 `fastboot flash system` 就好。你照著做，手機卡在開機動畫，然後你不知道下一步該查什麼。

這篇文章的目的，是把 Project Treble 這套架構講清楚到一個程度：當你遇到上面那個場景，你知道要檢查哪些東西、為什麼要檢查、以及檢查結果代表什麼。

我會從「一台陌生機器怎麼判斷」開始，然後往回講架構與歷史，因為不知道 Treble 為什麼長這樣，你就只能背指令，遇到沒見過的狀況就卡住。最後回到實作，講 GSI 刷機的完整流程與除錯路徑。

適合的讀者：做過 AOSP 編譯、刷過機、看得懂 `fastboot` 與 `logcat`，但對 Treble 的內部運作只有模糊印象的人。

---

## 一、開場：一台陌生機器，你該問的五個問題

先給結論式的檢查清單。後面每一節會解釋清單裡每一項背後的原理。

假設你手上有一台機器，adb 通得了，你想知道它的 Treble 狀況：

```bash
# 1. 這台機器有沒有 Treble？
adb shell getprop ro.treble.enabled

# 2. 它「出廠時」是哪個 Android 版本？（決定了它遵守哪一代規則）
adb shell getprop ro.product.first_api_level
adb shell getprop ro.build.version.sdk

# 3. vendor 介面的版本（Android 15 前後看的東西不一樣）
adb shell getprop ro.vndk.version          # Android 14 以前
adb shell getprop ro.vendor.api_level      # Android 15 之後的新機制

# 4. 有沒有獨立的 vendor 分割區？是不是動態分割區？
adb shell ls -l /dev/block/by-name/ | grep -Ei 'super|vendor|system|product'

# 5. A/B 還是 A-only？
adb shell getprop ro.boot.slot_suffix       # 有輸出 _a 或 _b 就是 A/B
adb shell getprop ro.build.ab_update
```

這五個問題的答案，大致決定了你的移植難度：

| 檢查結果 | 意義 |
|---|---|
| `ro.treble.enabled=true` | 有 Treble，理論上可刷 GSI |
| `first_api_level >= 29` | Android 10 起出廠，幾乎必然是動態分割區（super） |
| 有 `ro.vndk.version` | Android 14 以前的相容性模型 |
| 有 `ro.vendor.api_level` | Android 15 之後的新模型 |
| `slot_suffix` 有值 | A/B 裝置，刷機要注意 slot |

如果第一項回 `false` 或空的，這台機器是 Treble 之前的設計，GSI 這條路基本不通，你只能走傳統的 device tree 移植。

好了，現在往回講，這些東西為什麼是這樣。

---

## 二、Treble 之前：那條走不完的更新鏈

### 2.1 一個修補要經過幾隻手

2015 年 Stagefright 漏洞爆發時，Android 的更新問題第一次被攤在檯面上。這個漏洞只要收到一則 MMS 就可能被遠端執行程式碼，影響的裝置數以億計。Google 很快就修好了，然後大部分使用者等了半年、一年，或者永遠等不到。

原因不是 Google 慢，而是一個修補要走完的鏈條太長：

```
Google 發布 AOSP 修補
    ↓
SoC 廠（Qualcomm / MediaTek / Exynos）整合到自家 BSP
    ↓
OEM（Samsung / Xiaomi / OPPO...）整合 BSP + 自家 UI 層
    ↓
電信商認證測試（北美尤其嚴重）
    ↓
使用者收到 OTA
```

每一環都要重新測試、重新認證。而且鏈條有個殘酷的特性：**SoC 廠一旦停止支援某顆晶片，後面所有環節就自動斷掉**。這也是為什麼很多手機的更新終點，不是 OEM 決定的，是晶片廠決定的。

Stagefright 之後，Google 建立了月度安全公告（Android Security Bulletin）機制，但這只解決了「Google 這一端有沒有及時修」，沒有解決「修補傳不下去」。

### 2.2 問題的技術根源：程式碼混在一起

真正的技術癥結在於：**Android 框架和廠商實作在原始碼層級是耦合的**。

Treble 之前，HAL（Hardware Abstraction Layer）是以 `.so` 動態函式庫的形式，被框架行程直接 `dlopen` 進來執行的（所謂 passthrough 模式）。這代表：

- HAL 和框架在同一個行程裡，共用同一份 C++ runtime、同一批系統函式庫
- 框架的 C++ ABI 一改，所有 HAL 都要重編
- 廠商的修改往往直接散落在 `frameworks/` 底下，而不是被隔離在特定目錄

所以升級一個大版本，實務上等於「拿新版 AOSP，把廠商的所有修改重新 rebase 一次」。這件事的工作量，跟 Google 改了多少東西成正比，而不是跟廠商自己改了多少東西成正比。對 OEM 來說，這是純成本，沒有收益。

**2017 年的數據可以說明結果**：Android 8.0 Oreo 在 2017 年 8 月發布，到 2018 年 1 月（五個月後），採用率只有個位數百分比。而根據 Google 後來公布的比較，Nougat 平均要 192 天才能推送到主要裝置上，Oreo 是 170 天。

### 2.3 Google 的解法：畫一條契約線

2017 年 5 月，Google 在 I/O 前後公布 Project Treble，隨 Android 8.0 一起出貨。

核心想法可以一句話講完：**在框架和廠商實作之間，定義一條有版本、可測試、向後相容的介面，讓兩邊可以獨立更新。**

這條介面叫 **Vendor Interface**。Google 的承諾是：只要廠商實作符合這條介面的規範，框架端（system 分割區）就可以單獨換成新版，不需要重編廠商的任何程式碼。

這個承諾對 ROM 社群的意義，其實比對 OEM 更大。因為它同時創造了一個副產品：**GSI（Generic System Image）**，一個純 AOSP 的、可以刷進任何 Treble 相容裝置的通用系統映像。這件事我們後面詳談。

---

## 三、Treble 切在哪一刀：分割區的職責界線

### 3.1 從兩個分割區開始

Treble 最直觀的改變是分割區佈局。Android 8.0 的核心切法：

- **`/system`** — Google 的框架、AOSP 的一切通用程式碼
- **`/vendor`** — SoC 廠與 OEM 的硬體相關實作：HAL、驅動、韌體

界線的判準是：**這段程式碼會不會因為換了一顆晶片就要重寫？** 會的話放 vendor，不會的話放 system。

### 3.2 後來又多出來的三個

實務上兩個不夠，因為 OEM 的客製化不全是硬體相關的。所以陸續多出：

- **`/odm`** — ODM 廠（代工廠）的客製，通常是同一顆 SoC 但不同機型的差異，例如感測器校正、板級配置。可以視為 vendor 的延伸，在沒有獨立 odm 分割區的機器上會退化成 `/vendor/odm` 符號連結。
- **`/product`** — OEM 的產品層客製，但**不屬於硬體**的部分：預裝 App、客製鈴聲桌布、地區性設定。Android 9 引入。
- **`/system_ext`** — Android 11 引入。放 OEM 對系統框架本身的擴充（例如客製的系統服務），這些東西不該進 `/system`（因為 GSI 要能覆蓋它），也不適合放 `/product`。

這幾個分割區的存在，對移植者有直接意義：**刷 GSI 的時候你換掉的是 `/system`，而 `/vendor`、`/odm` 原封不動保留。** 這是整件事能運作的前提。`/product` 和 `/system_ext` 則視 GSI 的打包方式而定，有些 GSI 會把 product 併進 system。

### 3.3 動態分割區：Android 10 的大改動

Android 10 引入 **Dynamic Partitions**（動態分割區），這是刷機流程改變最大的一次。

在此之前，`system`、`vendor`、`product` 是實體分割區，大小在出廠時就定死。動態分割區把它們全部塞進一個叫 **`super`** 的實體分割區裡，裡面用類似 LVM 的機制切出**邏輯分割區（logical partition）**，大小可以在 OTA 時調整。

Google 的動機是：系統升級時 `/system` 常常會變大，實體分割區改不動，OEM 只好一開始就預留一堆空間。動態分割區讓這個空間可以動態重分配。

**對刷機的實際影響**：

1. `fastboot flash system xxx.img` 在動態分割區裝置上，走的是 fastbootd（userspace fastboot），不是 bootloader 的 fastboot。你可能需要先 `adb reboot fastboot`（注意不是 `adb reboot bootloader`）進到 fastbootd。
2. 如果 GSI 比原本的 `system` 大，`super` 裡沒空間，刷不進去。這時常見做法是先刪掉用不到的邏輯分割區釋出空間：
   ```bash
   fastboot delete-logical-partition product
   fastboot delete-logical-partition product_a   # A/B 裝置注意 slot 後綴
   ```
   注意這會讓原廠系統無法開機，屬於不可逆操作（除非重刷原廠韌體）。
3. 判斷是不是動態分割區：看 `/dev/block/by-name/` 有沒有 `super`，或查 `ro.boot.dynamic_partitions`。

### 3.4 A/B 與 A-only

跟 Treble 沒有直接關係，但同樣影響刷機流程的是 **A/B（seamless update）** 機制。

A/B 裝置有兩套系統分割區（`system_a` / `system_b`），更新時寫入非使用中的那一套，重開機切換 slot。好處是更新失敗可以自動回滾，而且更新過程不阻塞使用。

對移植者的差別：

- **A/B**：注意目前在哪個 slot（`fastboot getvar current-slot`），刷的時候通常兩個 slot 都要處理，或明確指定 `fastboot flash system_a`
- **A-only**：只有一套，流程單純，但沒有回滾保護，刷壞了就得進 recovery

GSI 的檔名通常會標明適用哪一種，選錯了會刷不進去或開不了機。

---

## 四、Vendor Interface 的真面目

分割區只是物理上的分家。真正讓「換掉 system 而不動 vendor」可行的，是介面契約本身。這個契約由幾個部分組成。

### 4.1 VINTF：契約的具體形式

**VINTF（Vendor Interface Object）** 是這套契約的載體，實際上是一組 XML 檔案，分兩類：

- **Manifest（清單）** — 「我提供什麼」
  - `/vendor/etc/vintf/manifest.xml` — vendor 宣告它實作了哪些 HAL、哪些版本
  - `/system/etc/vintf/manifest.xml` — 框架宣告它提供什麼

- **Compatibility Matrix（相容性矩陣）** — 「我需要什麼」
  - Device compatibility matrix — 裝置對框架的要求
  - Framework compatibility matrix — 框架對裝置的要求

比對規則是交叉的：**框架的 manifest 必須滿足裝置的 matrix，裝置的 manifest 必須滿足框架的 matrix。** 這個比對會在開機時和 OTA 時執行，任一邊不符就拒絕。

實務上這是你刷 GSI 開不了機的常見原因之一。如果 GSI（新版框架）的 compatibility matrix 要求某個 HAL 至少是 v2.0，而你機器的 vendor manifest 只宣告 v1.1，比對就會失敗。

查看的方法：

```bash
adb shell cat /vendor/etc/vintf/manifest.xml
adb shell cat /system/etc/vintf/compatibility_matrix.xml
# 或直接用內建工具
adb shell vintf
```

### 4.2 HAL 的三種型態

Treble 對 HAL 的執行模型做了根本改動。三種型態：

- **Passthrough HAL** — 傳統模式，HAL 以 `.so` 被 `dlopen` 進框架行程。Treble 過渡期的相容方案。
- **Binderized HAL** — Treble 的目標形態。HAL 跑在自己的行程裡，框架透過 Binder IPC（實際上是專用的 `/dev/vndbinder` 通道）呼叫它。行程分離代表 ABI 不再是共用的，而是走序列化的介面定義。
- **Same-process HAL (SP-HAL)** — 少數對延遲極度敏感、必須在同行程執行的例外，例如 OpenGL ES / Vulkan 的實作。這類 HAL 有特殊的函式庫連結規則。

**Treble 之後出廠的裝置，原則上必須使用 binderized HAL。** 行程分離是整套架構能成立的關鍵——它把「共用 C++ ABI」這個最脆弱的耦合點拿掉了。

代價是效能：每次呼叫多一次 IPC。這也是為什麼圖形這類路徑要保留 SP-HAL 的特例。

### 4.3 從 HIDL 到 AIDL

介面要序列化，就需要一套 IDL（介面定義語言）。

**HIDL（HAL Interface Definition Language）** 是 Treble 隨附推出的，專為 HAL 設計。它有自己的語法、自己的產生器（`hidl-gen`）、自己的版本規則（`android.hardware.camera.provider@2.4` 這種寫法你應該很熟）。

問題是 Android 本來就已經有 AIDL 了——用在 App 和系統服務之間十幾年。維護兩套 IDL 是重複投資，而且 AIDL 後來也支援了穩定版本（Stable AIDL），能力上已經追平。

於是路線調整：

- **Android 11** — 開始支援用 AIDL 定義 HAL（AIDL for HALs），新 HAL 建議走 AIDL
- **Android 13** — HIDL 正式標記為棄用（deprecated）。以 Android 13 出廠的裝置必須提供 AIDL 版本的 HAL，不得提供對應的 HIDL 版本。既有的 HIDL HAL 仍受支援，但不再接受新的 HIDL 介面。

對移植者的實際意義：**你會在不同世代的機器上看到混合狀態。** 一台 Android 12 出廠、後來升到 14 的機器，它的 vendor 裡很可能還是一堆 HIDL HAL。刷新版 GSI 時，框架端要同時保留 HIDL 相容層才能跟它對話——這也是 GSI 為什麼會愈來愈肥的原因之一。

### 4.4 VNDK 以及它的退場

這一節對做移植的人特別重要，因為它是近年變動最大的部分。

**VNDK（Vendor Native Development Kit）** 要解決的問題是：vendor 分割區裡的程式碼，難免要用到一些系統層的 C/C++ 函式庫（`libbase`、`libcutils`、`libutils` 之類）。但這些函式庫屬於 `/system`，會隨著框架升級而改變 ABI。

VNDK 的做法是：挑出一批函式庫，做成「VNDK 版本快照」，每個 Android 版本凍結一份，安裝在 `/system` 底下的版本化目錄裡（例如 `/system/lib64/vndk-31/`）。vendor 程式碼連結的是這份凍結的快照，而不是框架當下在用的版本。

於是有了 `ro.vndk.version` 這個 property，它記錄 vendor 是照哪一版建置的。刷 GSI 時的傳統相容規則是：**GSI 的版本必須大於或等於裝置上 vendor 的 VNDK 版本**，因為新版 GSI 會內含舊版的 VNDK 快照。

**問題是這個設計愈來愈貴**：每多一個 Android 版本，system 分割區就要多背一份 VNDK 快照，而實際用到的裝置愈來愈少。

所以 **Android 15 開始棄用 VNDK**。新的模型是：

- 原本屬於 VNDK 的函式庫，直接安裝到 `vendor`（或 `product`）分割區，跟其他 vendor-available 函式庫一視同仁——**誰要用誰自己帶**，不再由 system 統一供應
- `ro.vndk.version` 這個 property，在為 Android 15 建置的 vendor/product 分割區上會被移除（事實上從 Android 14 QPR3 起就不再是 `system/core` 的一部分）
- 相容性判斷改用 **Vendor API level**（`ro.vendor.api_level`）。它由 SDK API level 推導而來，AOSP 也提供了 `AVendorSupport_getVendorApiLevelOf()` 讓程式碼查詢對應關係

**對刷 GSI 的影響**：舊的「比 VNDK 版本號」這條判準，在新舊機器上要分開處理。Android 15 之後的機器看 `ro.vendor.api_level`；Android 14 以前的機器仍然看 `ro.vndk.version`。你寫的檢測腳本要能處理兩種情況。

### 4.5 還有兩樣東西也在契約裡

除了 HAL 介面和函式庫，Vendor Interface 還包含兩塊常被忽略、但實際上最常炸掉的東西：

- **SELinux policy** — Treble 把 policy 拆成 platform 與 vendor 兩部分，各自版本化。GSI 的 platform policy 和你機器的 vendor policy 必須能合併成功，否則開機時 init 就會失敗。
- **System properties** — 同樣做了 owner 劃分。vendor 定義的 property 有命名規範（`ro.vendor.*`、`vendor.*`），框架不該去讀寫不屬於它的 property。

### 4.6 VTS：契約的執法者

規範沒有測試就是空話。**VTS（Vendor Test Suite）** 就是那把尺——一套自動化測試，驗證裝置的 vendor 實作是否符合 Vendor Interface 的規範。裝置要被認定為 Treble 相容，必須通過 VTS。

另外還有 **CTS-on-GSI**：把 GSI 刷上去之後跑 CTS，驗證「純 AOSP 框架 + 這台裝置的 vendor」這個組合真的能運作。這個測試的存在，等於 Google 用制度保證了 GSI 一定刷得起來——至少在原廠出貨的那個時間點。

理解這一點很重要：**GSI 能不能刷得動，很大程度取決於這台機器當初有沒有認真通過 CTS-on-GSI。** 這也是為什麼有些機器刷 GSI 順得不可思議，有些則是災難。

---

## 五、GSI 實戰

### 5.1 GSI 是什麼、去哪拿

GSI 是純 AOSP 建置的 system 映像，設計上可以刷進任何 Treble 相容裝置。它的存在其實是 Treble 的副產品：Google 需要一個東西來測試 vendor 實作的相容性，這個東西順手就成了 ROM 社群的基礎建設。

兩個來源：

- **官方 GSI**：Google 在 Android Developers 網站提供，純 AOSP，主要用途是開發者測試。品質穩定但功能陽春，而且對非 Pixel 裝置的相容性修補不多。
- **社群 GSI**：以 phhusson 的 `treble_experimentations` 和後來的 TrebleDroid 為代表。它們在 AOSP 基礎上加了大量針對特定裝置或特定 SoC 的修補。

社群 GSI 多做的事，大致分幾類：讓 GSI 能吃舊版或非標準的 vendor HAL、繞過某些 OEM 的 vendor 私有介面、修 SELinux policy 衝突、處理 OEM 對 init 腳本的魔改。**實務上，如果你的裝置不是 Pixel 或 Android One，社群 GSI 的成功率通常高得多。**

### 5.2 選對映像

GSI 的檔名帶有一串代號，代表適用的組合。你至少要搞清楚三個維度：

- **架構**：`arm64` / `arm` / `x86_64`
- **分割區佈局**：`ab`（A/B 裝置） vs `a-only`
- **變體**：是否內含 GApps（`gapps` / `vanilla` / `floss`）、是否為 permissive 版本

phhusson 系列還有一套較舊的縮寫命名（`arm64_bvN`、`arm64_bgS` 之類），字母分別對應 binder 位元數、GApps 與否、以及安全性設定。**這套命名在不同時期有過調整，我建議直接以你下載來源的 wiki 說明為準，不要憑記憶推測**——選錯變體是新手最常見的失敗原因。

### 5.3 刷機前置

**解鎖 bootloader**：

```bash
fastboot flashing unlock
# 部分裝置還需要
fastboot flashing unlock_critical
```

這會清除所有使用者資料。某些 OEM（小米、部分歐珀機型）還需要在原廠帳號系統申請解鎖權限並等待期限。

**關閉 AVB / dm-verity 驗證**：

Android Verified Boot（AVB）會驗證系統分割區的簽章。刷 GSI 之後簽章對不上，開機會被擋下來。標準做法是刷一個空的 vbmeta 並帶上停用旗標：

```bash
fastboot --disable-verity --disable-verification flash vbmeta vbmeta.img
```

A/B 裝置可能需要兩個 slot 都處理：

```bash
fastboot --disable-verity --disable-verification flash vbmeta_a vbmeta.img
fastboot --disable-verity --disable-verification flash vbmeta_b vbmeta.img
```

`vbmeta.img` 通常從原廠韌體包裡取，或用 AOSP 提供的空白 vbmeta。有些裝置沒有獨立的 vbmeta 分割區，處理方式各異，這時只能查該機型的社群討論。

### 5.4 刷入

**動態分割區裝置（Android 10 以後出廠）**：

```bash
adb reboot fastboot          # 進 fastbootd，不是 bootloader
fastboot getvar current-slot # 確認 slot（A/B 裝置）

# 空間不夠的話，先刪掉用不到的邏輯分割區
fastboot delete-logical-partition product_a

fastboot flash system system.img
fastboot -w                  # 清除 userdata，跨版本刷務必執行
fastboot reboot
```

**非動態分割區裝置**：

```bash
fastboot reboot bootloader
fastboot erase system
fastboot flash system system.img
fastboot -w
fastboot reboot
```

`fastboot -w` 這一步不能省。跨版本刷 GSI 時保留舊的 userdata，幾乎必然導致開機循環或大量 App 崩潰。

### 5.5 更安全的選項：DSU

如果你只是想試試看某個 GSI 跑不跑得動，不想冒著把機器刷成磚的風險，**DSU（Dynamic System Updates）** 是更好的入口。

DSU 是 Android 10 引入的機制，允許把一個 GSI 下載到裝置上，**以暫存的方式開機進去**，原本的系統完全不受影響。重開機就回到原系統，測完直接刪掉。

它需要解鎖 bootloader，並透過 `adb shell` 觸發（或用 Android Studio 的相關工具）。對「先驗證相容性再決定要不要真的刷」這個需求，DSU 是最省事的路。

---

## 六、開不了機：除錯路徑

刷完卡在開機動畫，或者根本沒過 bootloader，怎麼查。

### 6.1 先確認卡在哪一階段

- **完全黑屏、連 boot logo 都沒有** → bootloader 或 kernel 層級問題，通常跟 vbmeta / AVB 有關
- **停在 OEM logo** → kernel 起來了但 init 失敗
- **停在開機動畫（bootanimation）循環** → init 過了，框架起不來或一直崩潰
- **進得去但功能殘缺**（沒訊號、相機打不開） → HAL 對不上，這是「刷起來了但沒用」的典型

### 6.2 抓 log

開機循環時，log 是唯一的線索來源：

```bash
# 開機過程中持續抓，接上就開始錄
adb logcat -b all > boot.log

# kernel 層
adb shell dmesg > dmesg.log

# 上一次開機的 kernel log（開機循環時特別有用）
adb shell cat /proc/last_kmsg
adb shell cat /sys/fs/pstore/console-ramoops
```

如果 adb 起不來，只能靠 `last_kmsg` / pstore，或者有 serial console 的話走 UART。

### 6.3 常見死因對照

| 症狀 | 可能原因 | 查什麼 |
|---|---|---|
| init 失敗、SELinux denied 洗版 | vendor policy 與 GSI platform policy 衝突 | `dmesg` 裡的 `avc: denied` |
| VINTF 比對失敗 | vendor manifest 缺 GSI 要求的 HAL | `adb shell vintf`、logcat 搜 `vintf` |
| 找不到函式庫（`dlopen failed`） | VNDK 版本不符，或 Android 15 後函式庫沒被帶進 vendor | logcat 搜 `CANNOT LINK` |
| 沒有訊號 | RIL / telephony HAL 版本對不上 | logcat 搜 `Rild`、`RadioService` |
| 相機無法啟動 | camera provider HAL 介面版本不符 | logcat 搜 `CameraProvider` |
| 刷不進去、空間不足 | super 分割區容量不夠 | `fastboot getvar super-partition-name`、看邏輯分割區配置 |

### 6.4 心態上的提醒

移植失敗時，最沒效率的做法是不斷換 GSI 版本亂試。比較有效的順序是：

1. 先確認硬條件（Treble 有沒有、分割區佈局對不對、變體選對沒）
2. 抓 log，找到**第一個**錯誤——後面的錯誤往往是連鎖反應
3. 拿這個錯誤去該機型的社群討論搜，同型號的人很可能踩過同一個坑
4. 都不行才考慮換版本，而且要有假設地換（例如「懷疑是 VNDK 太新，降一版試」）

---

## 七、廠商魔改：理論相容 ≠ 實際可用

這是 Treble 最大的落差所在，也是文章一開始那個場景之所以令人挫折的根本原因。

Treble 保證的是「符合規範的 vendor 實作，可以搭配新版框架」。但規範只約束了**介面**，沒有約束**行為**。OEM 有太多方法可以在不違反字面規範的前提下，讓 GSI 跑不起來：

- **私有 HAL 擴充**：宣告了標準 HAL，但實際行為依賴自家框架送來的私有參數。標準 GSI 不會送，於是 HAL 行為異常。
- **init.rc 的魔改**：vendor 的 init 腳本假設 `/system` 裡有某個自家的服務或檔案。刷了 GSI 之後找不到，init 卡住。
- **非標準的 fstab / 掛載點**：分割區佈局跟 AOSP 預期不同，GSI 的 init 掛不起來。
- **綁定自家框架的驅動行為**：最典型是指紋、面部辨識、快充協定這類，OEM 常把邏輯拆一半在框架層，GSI 沒有那一半。
- **韌體載入路徑寫死**：`/vendor/firmware` 以外的路徑，GSI 不知道要去哪找。

結果是：**Treble 讓「開得起來」變得容易，但「所有功能都正常」仍然要逐台處理。** 這也解釋了社群 GSI 為什麼要維護一大堆針對特定機型的 hack——它們補的就是這個落差。

從另一個角度看，這其實不是 Treble 的設計失敗。Google 能做的就是定介面、寫測試、要求認證。OEM 願意在介面之外做多少事，是商業決策，不是技術問題。

---

## 八、GKI：另一半的刀

Treble 切的是使用者空間。核心（kernel）這一半，Google 另外開了一個專案處理。

### 8.1 核心的碎片化

Android 的核心碎片化問題比使用者空間更嚴重。一台出貨的手機，它的核心是這樣疊出來的：

```
Linux LTS 主線
  → Android Common Kernel（ACK，Google 加上 Android 專屬修改）
    → SoC 廠的 BSP 核心（Qualcomm/MediaTek 加上晶片支援）
      → OEM 的裝置核心（加上板級與客製）
```

每一層都可能有數十萬行的修改，而且大多不會回饋上游。結果是每台機器的核心事實上都是獨一無二的，升級核心版本等於重做一次整合。

### 8.2 GKI 的做法

**GKI（Generic Kernel Image）** 的策略跟 Treble 同構：把核心切成「通用核心」和「廠商模組」，中間定義穩定介面。

- **GKI kernel** — Google 建置的通用核心，同一個版本所有裝置共用
- **Vendor modules** — SoC 與板級支援移出核心本體，做成可動態載入的核心模組
- **KMI（Kernel Module Interface）** — 兩者之間的穩定介面，由符號清單（symbol list）定義

**KMI 凍結（KMI freeze）** 是關鍵機制：在一個平台版本推送到 AOSP 之前，對應的 ACK KMI 分支會被凍結，並在該分支的整個生命週期維持凍結——除非發現嚴重安全問題，否則不接受任何破壞 KMI 的變更。凍結之後，GKI 以季度節奏發布更新，vendor 模組不需要重編。

**時間點**：從 **Android 12** 起，出貨核心版本為 5.10 或更高的裝置，必須使用 GKI 核心。

### 8.3 對移植者的意義

GKI 對 ROM 開發是實打實的好消息：核心與 vendor 模組解耦之後，換核心不再必然要重編所有驅動。理論上你可以拿 Google 的 GKI 建置搭配原機的 vendor 模組。

但同樣有落差：OEM 對核心的客製如果超出 KMI 允許的範圍（例如直接改了核心內部結構），實際上還是綁死的。而且 KMI 只在同一個凍結分支內保證穩定，跨大版本仍然要重來。

---

## 九、九年之後：Treble 給了什麼、沒給什麼

### 9.1 可驗證的成果

更新速度確實改善了，而且有數據：

- Nougat 平均 192 天推送到主要裝置，Oreo 170 天，**Pie 降到約 118 天**
- 採用率的對比更明顯：2018 年 7 月底（Pie 發布前），Oreo 佔生態系 8.9%；2019 年 8 月底（Android 10 發布前），Pie 佔 **22.6%**
- Google 也表示，與晶片廠的合作讓平均升級時間縮短了三個月以上

架構上的成果也是實在的：分割區職責清楚了、HAL 行程隔離了、有了可執行的相容性測試、核心也走上同一條路。這些是真正的工程進步，不是行銷話術。

### 9.2 沒解決的部分

但如果問「Android 更新問題解決了嗎」，答案還是否定的，原因在於瓶頸已經移位：

- **UI 層客製仍是主要成本**。One UI、MIUI/HyperOS、ColorOS 這些皮膚的工作量，Treble 一點都沒減少。OEM 要花的時間仍然以「季」為單位。
- **SoC 廠的支援年限仍是硬上限**。Treble 讓框架可以獨立更新，但如果晶片廠不再提供新的驅動與韌體支援，機器一樣會停在某個版本。
- **商業意願才是決定因素**。這幾年 Pixel 與三星旗艦陸續給出七年更新承諾，主要驅動力是市場競爭與監管壓力，不是 Treble 讓它變便宜了。Treble 降低了技術門檻，但沒有創造更新的商業誘因。

### 9.3 誰是真正的受益者

一個有點反諷的觀察：**Treble 最大的受益者可能不是一般使用者，而是 ROM 社群。**

對一般使用者來說，能不能收到更新，取決於 OEM 的商業決定，Treble 幫不上忙。但對移植者來說，Treble 帶來的改變是質變的：

- GSI 的存在，讓「這台機器能不能跑新版 Android」從一個需要數月移植工作的問題，變成一個下午可以驗證的問題
- vendor 分割區保持不動，代表你不需要有驅動原始碼也能跑新框架——這在 Treble 之前幾乎不可能
- CTS-on-GSI 的認證要求，等於強迫 OEM 保證他們的機器至少能跑純 AOSP
- LineageOS 這類專案的機型支援廣度，跟 Treble 的普及是同步成長的

換句話說，Google 蓋這條路是為了讓 OEM 走，結果 OEM 走得零零落落，倒是社群把這條路走得最勤。

---

## 十、附錄：速查

### 10.1 檢測腳本

```bash
#!/bin/bash
# treble-check.sh — 快速盤點一台裝置的 Treble 狀況

echo "=== 基本資訊 ==="
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
adb shell getprop ro.product.first_api_level

echo "=== Treble ==="
adb shell getprop ro.treble.enabled
adb shell getprop ro.vndk.version          # Android 14 以前
adb shell getprop ro.vendor.api_level      # Android 15 以後

echo "=== 分割區 ==="
adb shell getprop ro.boot.dynamic_partitions
adb shell getprop ro.build.ab_update
adb shell getprop ro.boot.slot_suffix
adb shell ls /dev/block/by-name/ | grep -Ei 'super|vendor|odm|product|system'

echo "=== VINTF ==="
adb shell vintf 2>/dev/null | head -40
```

### 10.2 Property 對照

| Property | 意義 |
|---|---|
| `ro.treble.enabled` | 是否為 Treble 裝置 |
| `ro.product.first_api_level` | 出廠時的 API level，決定適用哪一代規則 |
| `ro.build.version.sdk` | 目前系統的 API level |
| `ro.vndk.version` | VNDK 快照版本（Android 14 以前） |
| `ro.vendor.api_level` | Vendor API level（Android 15 起的新機制） |
| `ro.boot.dynamic_partitions` | 是否使用 super 動態分割區 |
| `ro.boot.slot_suffix` | 目前 slot（`_a` / `_b`），A/B 裝置才有 |
| `ro.build.ab_update` | 是否支援 A/B 無縫更新 |

### 10.3 時間線

| 版本 | 年份 | 變更 |
|---|---|---|
| Android 8.0 | 2017 | Project Treble、Vendor Interface、HIDL、VNDK、binderized HAL |
| Android 9 | 2018 | `/product` 分割區 |
| Android 10 | 2019 | Dynamic Partitions（super）、Project Mainline / APEX、DSU |
| Android 11 | 2020 | `/system_ext` 分割區、AIDL for HALs 開始支援 |
| Android 12 | 2021 | 5.10 以上核心強制使用 GKI |
| Android 13 | 2022 | HIDL 正式棄用，新裝置須提供 AIDL HAL |
| Android 15 | 2024 | VNDK 棄用，改用 Vendor API level |

---

## 參考資料

**AOSP 官方文件**

- [Architecture overview](https://source.android.com/docs/core/architecture)
- [Partitions overview](https://source.android.com/docs/core/architecture/partitions)
- [Vendor interface object (VINTF)](https://source.android.com/docs/core/architecture/vintf)
- [Manifests](https://source.android.com/docs/core/architecture/vintf/objects)
- [Compatibility matrixes](https://source.android.com/docs/core/architecture/vintf/comp-matrices)
- [HAL overview](https://source.android.com/docs/core/architecture/hal)
- [HIDL](https://source.android.com/docs/core/architecture/hidl)
- [AIDL for HALs](https://source.android.com/docs/core/architecture/aidl/aidl-hals)
- [VNDK overview](https://source.android.com/docs/core/architecture/vndk)
- [Vendor API level](https://source.android.com/docs/core/architecture/api-flags)
- [Generic Kernel Image (GKI)](https://source.android.com/docs/core/architecture/kernel/generic-kernel-image)
- [Maintain a stable KMI](https://source.android.com/docs/core/architecture/kernel/stable-kmi)
- [Kernel modules overview](https://source.android.com/docs/core/architecture/kernel/modules)

**GSI 與社群資源**

- [Generic System Images (GSIs) — Android Developers](https://developer.android.com/topic/generic-system-image/)
- [GSI list — TrebleDroid wiki](https://github.com/TrebleDroid/treble_experimentations/wiki/Generic-System-Image-%28GSI%29-list)
- [treble_experimentations — phhusson](https://github.com/phhusson/treble_experimentations)

**歷史與數據**

- [Faster Adoption with Project Treble — Android Developers Blog, 2018](https://android-developers.googleblog.com/2018/05/faster-adoption-with-project-treble.html)
- [All About Updates: More Treble — Android Developers Blog, 2019](https://android-developers.googleblog.com/2019/10/all-about-updates-more-treble.html)
- [Google details Project Treble's impact on Android updates — 9to5Google, 2019](https://9to5google.com/2019/10/23/android-update-treble/)
- [Project Treble retrospective — Esper](https://www.esper.io/blog/android-dessert-bites-6-project-treble-retrospective-3195734)
