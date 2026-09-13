# 你的手機在 Android 發表前就準備好了：聊聊 PDK 與 aosp.xml

每年 Google 發表新版 Android 的時候，總會有一批手機在幾個月內就跟著升級。這件事其實有點違反直覺——原始碼不是剛剛才公開嗎？晶片廠和手機廠是怎麼做到的？

答案是：他們早就拿到了。這中間有一層東西叫 **PDK**。

## PDK 是什麼

PDK 的全名是 **Platform Development Kit**，平台開發套件。

Android 雖然是開源專案，但「開源」跟「所有人同時拿到」是兩回事。Google 會在新版 Android 正式公開之前，透過 NDA 把平台的原始碼與相關資源先交給合作夥伴——主要是 SoC 廠（聯發科、高通這些做晶片的）和手機品牌廠。

為什麼要這樣做？因為晶片的驅動、電源管理、相機 pipeline、視訊編解碼這些東西，都得跟著新版 Android 的框架改動一起調整。如果等到程式碼公開才開始做，等 BSP 弄好、驗證完、送進手機廠，市面上的機器大概要再等一年才升得上去。

所以 PDK 的存在，本質上是**把整條供應鏈的時間軸往前推**。等 AOSP 公開發布那天，晶片廠手上的東西早就跑起來了。

值得一提的是，Android 這幾年推的 Treble、GKI（Generic Kernel Image）這些架構調整，也都在往同一個方向使力：讓晶片層跟框架層盡量解耦，讓升級不用整包重來。PDK 是流程上的提前，Treble 是架構上的鬆綁，兩件事在解同一個問題。

## 那 aosp.xml 又是什麼

拿到 PDK 之後，接下來的問題是：這麼多程式碼要怎麼交付？

Android 的原始碼不是一個 git repo，而是**幾百上千個獨立的 git repo**。framework 是一個、bionic 是一個、每個 app、每個 library 都可能各自是一個。所以 Google 做了一個工具叫 `repo`，專門管理這種「一堆 git repo 組成的專案」。

而 `repo` 要怎麼知道該抓哪些 repo、每個要抓哪個版本、要放到本機的哪個資料夾？靠的就是 **manifest 檔案**——一份 XML 清單。

`aosp.xml` 就是其中一份典型的 manifest。它大致長這樣（示意）：

```xml
<manifest>
  <remote name="aosp" fetch="..." />
  <default remote="aosp" revision="android-XX.X.X_rX" />

  <project path="frameworks/base" name="platform/frameworks/base" />
  <project path="system/core"      name="platform/system/core" />
  <!-- ...以下數百行 -->
</manifest>
```

一行一個專案，指明「從哪抓、抓哪個版本、放到哪」。你下 `repo init -u <url> -m aosp.xml` 再 `repo sync`，它就照著清單把整棵樹拉下來。

在實際的交付情境裡，manifest 通常不會只有一份。純 AOSP 的部分歸 `aosp.xml`，晶片廠自己的 BSP 與私有模組放另一份，手機廠再疊一層自己的客製專案。三份合起來，才是一棵能 build 出韌體的完整原始碼樹。

這種分法有個很實際的理由：**權責分離**。哪些是 Google 的、哪些是晶片廠的、哪些是自己的，一看 manifest 就清楚。出問題時也知道該找誰。

## 一個容易踩的觀念

manifest 裡的 `revision` 通常會被**釘死在特定的 tag 或 commit**，而不是指向某個 branch 的最新狀態。

這點常讓剛接觸的人困惑：「我 sync 到最新的不是比較好嗎？」

不是。因為晶片廠的 BSP 是針對**那個特定版本**的 AOSP 開發與驗證的。你把 AOSP 那部分偷偷往前推，另外兩層卻沒動，介面對不上，輕則 build 不過，重則 build 得過但跑起來行為詭異——後者更麻煩，因為你會花很久才發現問題出在這裡。

**整棵樹是一個經過驗證的組合**，不是三個可以各自更新的獨立元件。這個心智模型比任何指令都重要。

## 小結

- **PDK** 是 Google 提前交付給合作夥伴的平台開發套件，讓晶片廠和手機廠能在 Android 公開前就開始準備
- **`repo`** 是管理 Android 這種多 git repo 專案的工具，**manifest** 則是它的清單
- **`aosp.xml`** 是描述 AOSP 部分的 manifest，實務上會跟晶片廠、品牌廠的 manifest 疊在一起用
- manifest 裡的版本是**刻意鎖定**的，那是一個驗證過的組合，不要隨手往前推

下次看到某支手機在 Android 發表後兩個月就升級了，你就知道背後這條線是從什麼時候開始拉的了。

---

*本文只談公開的概念與工具用法，不涉及任何廠商的具體交付內容。*
