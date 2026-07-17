---
sidebar_label: Android Kernel
---

# Android Kernel:從手工藝品到標準化零件——一顆核心的供應鏈故事

> 面向對象:Android 產業鏈的工程師與 PM。本文介紹 Android kernel 的本質、它與 Linux 的關係、四層 fork 供應鏈的碎片化問題,以及 GKI 如何重構這一切;並延續系列前兩篇〈Android Migration〉與〈Vendor Freeze〉的視角,分析 Google、chip vendor、系統廠三方在 kernel 上各自的角色與工程實務。

---

## 一、Android Kernel 是什麼:Linux,加上一組 Android 補丁

Android kernel 本質上就是 Linux kernel。Google 沒有另起爐灶,而是在 Linux 之上維護一組 Android 專屬的功能補丁,其中最具代表性的包括:

- **Binder**:Android 整個 IPC(行程間通訊)體系的地基。app 與 system_server 之間、framework 與 HAL 之間的每一次跨行程呼叫都走 Binder driver。它是 Android 之所以是 Android 的核心元件,已於 2015 年前後正式進入 Linux 主線。
- **電源管理機制**:手機的使用情境要求裝置能長時間深度休眠(suspend)又能被即時喚醒,早期的 wakelock 機制與後來主線化的 autosleep/wakeup source 都源於此。
- **記憶體管理機制**:早期 Android 有自己的 ashmem(匿名共享記憶體)、ION(多媒體緩衝區配置)、lowmemorykiller(低記憶體殺手)。這三者如今已分別被主線方案取代:memfd、DMA-BUF heaps,以及 userspace 的 LMKD 搭配核心的 PSI(Pressure Stall Information)。

這段演變透露了一個重要趨勢:**Google 十多年來持續把 Android 補丁「上游化」(upstreaming)推回 Linux 主線**,Android kernel 與標準 Linux 的差異逐年縮小。這不是潔癖,而是為了讓 Android 能直接搭上 Linux LTS(長期支援版)的安全更新列車,減少自己維護 fork 的成本。

---

## 二、四層 Fork 鏈:碎片化是怎麼煉成的

在 GKI(下述)出現之前,一台 Android 手機裡的 kernel 是經過四層 fork 一路傳下來的:

```
Linux mainline / LTS          (Linus 樹與 LTS,如 5.15、6.1、6.6)
        │ fork + Android 補丁
Android Common Kernel (ACK)   (Google 維護的 android-common 分支)
        │ fork + SoC driver、電源/排程調校
SoC vendor kernel             (高通、聯發科的平台 kernel — 改動最大的一層)
        │ fork + 板級 driver(觸控、面板、充電、指紋)
Device kernel                 (系統廠出貨在裝置上的最終 kernel)
```

這條鏈的問題是結構性的:

1. **安全補丁滲透極慢**:一個 LTS 修補要到達使用者手上,得依序穿過四層 merge,每一層都可能因為衝突、排程或「這平台已停止維護」而卡住。
2. **碎片化失控**:每家晶片商 × 每個平台 × 每家系統廠 × 每台機型,各自維護一份 kernel。Google 曾統計市面上同時存在**數千種 kernel 變體**,核心安全狀態根本無從掌握。
3. **升級成本高昂**:如系列第一篇所述,kernel 是晶片商 BSP 裡最重的一塊。Android 大版本若要求新的 kernel 最低版本,整條鏈就要重走一遍——這正是 GRF 之前舊裝置升級卡關的最大原因之一。

---

## 三、GKI:把碎片化關進籠子

Android 11 起試行、Android 12 起在新平台強制的 **GKI(Generic Kernel Image)**,是 Google 對上述問題的結構性解法,如今[已是各種 form factor 的必要條件](https://source.android.com/docs/core/architecture/kernel/generic-kernel-image)。核心思路是把 kernel 一刀切成兩半:

- **GKI 核心本體**:由 Google 官方編譯、簽署的通用 boot image,所有裝置共用同一顆。SoC 與板級程式碼**不准再改核心本體**。
- **Vendor modules**:晶片商與系統廠的專屬程式碼全部改寫成可載入核心模組(loadable kernel modules),放在 vendor_boot / vendor_dlkm 分割區。

兩者之間用 **KMI(Kernel Module Interface)** 隔開:每條 GKI 分支在凍結後,Google 保證 KMI 穩定——核心本體可以持續吃安全更新,而 vendor module 不需要重編就能繼續載入。Google 並以 ABI monitoring 工具鏈持續監控,防止任何變更悄悄打破介面。

分支命名也標準化為「Android 版本-kernel 版本」的形式,例如 android14-6.1、android15-6.6,每個 Android 大版本對應少數幾條受支援的 GKI 分支([GKI release process](https://source.android.com/docs/core/architecture/kernel/gki-releases))。效果總結成三句話:**kernel 安全更新由 Google 統一出、晶片商只維護自己的 module、系統廠只維護板級 module。** kernel 從每台裝置一份的手工藝品,變成了標準化零件體系。

---

## 四、Google 的角度:收編核心,承擔核心

### 4.1 Google 得到什麼

GKI 讓 Google 第一次真正「擁有」了 Android 裝置上的核心:安全補丁不再依賴四層供應鏈的善意,而是 Google 編好、簽好、透過 OTA 直接更新 boot 分割區。對一個以「碎片化」聞名的生態,這是核心安全治理從不可能到可能的轉折。同時,上游化策略讓 Google 能直接複用 Linux LTS 社群的維護量能,而不是獨力供養一支平行的 kernel 團隊。

### 4.2 Google 付出什麼

代價是**支援承諾變成 Google 自己的義務**:每條 android-common/GKI 分支,Google 承諾約四年的支援與 LTS 補丁合入。這個「四年」直接塑造了整個生態的節奏——系列第二篇提過,Longevity GRF 之所以規定凍結平台**第 3 年必須做一次 kernel 大版本升級**(例如 6.1 → 6.6),根源就是 Google 不願意把單一 kernel 分支的支援無限延長,否則越到後期,主線修補的 backport 會越來越扭曲、風險越來越高。

KMI 凍結本身也是工程稅:Google 的 kernel 團隊每合一個 LTS 補丁,都要確保不打破已凍結的 KMI;真的非破不可時,得走 KMI 更新流程並與晶片商協調。自由度的讓渡是雙向的。

---

## 五、Chip Vendor 的角度:從「魔改核心」到「經營模組」

### 5.1 工作型態的轉變

GKI 之前,晶片商的 kernel 團隊習慣直接深入核心本體:改排程器餵自家 big.LITTLE 架構、改記憶體子系統配合自家 ISP pipeline、在核心裡埋各種平台 hook。GKI 之後,這些全部要重構成 KMI 之內的 module,或者透過 Google 提供的 **vendor hook**(核心預留的掛載點)實現。這場遷移在 Android 12~13 世代是晶片商相當痛的一役——多年累積的核心魔改要逐一分類:能 upstream 的推上游、能 module 化的改 module、真的需要 hook 的向 Google 提案。

### 5.2 新的平衡點

換來的是維護成本的結構性下降:核心本體的安全更新不再是晶片商的事,平台 kernel 的維護聚焦在自家 module 與 driver。搭配 GRF/Longevity GRF 的凍結制度,kernel 工作進一步收斂成兩種可規劃的工程:首發時的 module 開發與調校,以及第 3 年一次、可跨平台批次執行的 kernel 大版本升級。

但張力仍在:**效能調校是晶片商的差異化命脈**,而 KMI 限制了他們伸手進核心的深度。vendor hook 的數量與位置成為晶片商與 Google 之間持續談判的介面——hook 給太多,GKI 名存實亡;給太少,晶片商的排程與功耗優化施展不開。這條線的拉扯,每個 kernel 版本都在重新發生。

---

## 六、系統廠的角度:板級紀律決定三年後的成本

### 6.1 日常工作:板級 driver 與穩定性

系統廠碰 kernel 的部分主要是板級:觸控、顯示面板、充電 IC、指紋、感測器等周邊的 driver,以及整機的功耗與穩定性收斂(suspend/resume 穩定性、thermal 表現、待機電流)。GKI 世代,這些一律以 module 形式存在於 vendor_dlkm,不再碰核心本體。

### 6.2 真正的考驗:kernel 大版本升級

系列第二篇提過的結論值得在此展開:**凍結期間 vendor 側唯一的大工程就是第 3 年的 kernel 升級,而它的痛苦程度在開案第一天就被決定了。**

- 板級 driver 若照 upstream 風格與 GKI module 規範撰寫——用標準 kernel API、不依賴平台私有符號、device tree 乾淨——升級時理論上重編、回歸測試即可。
- 反之,若當年為了趕時程直接魔改、依賴晶片商 kernel 的內部符號、把邏輯寫死在特定 kernel 版本的行為上,升級成本就會膨脹成「半次 bring-up」:driver 逐支重寫、穩定性問題全面重收。

所以成熟系統廠會把「板級 code 的 upstream 紀律」寫進開案的工程規範與 code review 標準——這不是程式碼潔癖,是三年後的真金白銀。

### 6.3 PM 視角的檢核點

對 PM 而言,kernel 相關的專案風險可以收斂成幾個必問項目:這個平台用哪條 GKI 分支、Google 支援到何時?晶片商的 kernel 升級版本規劃與時程?我們的板級 driver 有多少支、GKI 合規率多少?第 3 年 kernel 升級的人力有沒有排進長期資源計畫?這幾題在 SoC 選型與開案階段就該有答案,而不是留到升級專案啟動時才發現。

---

## 七、三方對照與總結

| | Google | Chip Vendor | 系統廠(OEM/ODM) |
|---|---|---|---|
| **對 kernel 的角色** | 核心本體的擁有者與安全更新來源 | KMI 之內的平台 module 與調校 | 板級 driver module 與整機穩定性 |
| **得到** | 核心安全治理權、複用 LTS 社群量能 | 核心維護成本銳減、升級工程可規劃化 | 不再自扛核心安全、升級依賴降低 |
| **付出** | 每條分支約四年的支援義務、KMI 維護稅 | 放棄魔改核心的自由、hook 談判 | 板級紀律的前期投資 |
| **關鍵時點** | GKI 分支凍結與 EOL | 首發 module 開發、第 3 年批次升級 | 開案時的 code 規範、第 3 年升級專案 |

把三篇串起來看:Treble 切開了 system 與 vendor,GRF 凍結了 vendor 的要求,而 **GKI 切開並收編了 kernel**——三者共同構成 Android 長期支援的技術地基。Android kernel 的故事,本質上是一場持續十餘年的「去碎片化」工程:Google 出核心、晶片商出平台模組、系統廠出板級模組,每一方都讓渡了一部分自由,換來的是整個生態能對使用者許下七年的承諾。

---

## 延伸閱讀

- [Kernel overview — AOSP](https://source.android.com/docs/core/architecture/kernel)
- [Generic Kernel Image (GKI) project — AOSP](https://source.android.com/docs/core/architecture/kernel/generic-kernel-image)
- [GKI release process — AOSP](https://source.android.com/docs/core/architecture/kernel/gki-releases)
- [Kernel modules overview — AOSP](https://source.android.com/docs/core/architecture/kernel/modules)
- [GKI FAQ — AOSP](https://source.android.google.cn/docs/core/architecture/kernel/gki-faq)
