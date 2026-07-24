# Android Automotive OS（AAOS）開發者入門指南

## 一、先把名詞分清楚

在深入之前，務必分清三個常被混用的名詞，否則整個心智模型都會歪掉：

| 名稱 | 運算在哪 | 本質 | 沒手機能用嗎 |
|------|----------|------|--------------|
| **Android Auto** | 手機 | 手機投影（projection），車機只是外接螢幕 | 不行 |
| **AAOS（Android Automotive OS）** | 車機硬體 | 直接跑在車上的完整作業系統，AOSP 的一支 | 可以 |
| **AAOS + GAS** | 車機硬體 | AAOS 再加上 Google Automotive Services（Play 商店、Google 地圖、Assistant） | 可以 |

一句話：**Android Auto 是投影協定，AAOS 是作業系統。** 本文談的是後者。

AAOS 本身是開源的（AOSP），車廠可以自由客製 UI、深度整合車輛硬體；需要 Google 服務的車廠則另外向 Google 授權 GAS。因此你會看到兩種車：有 Play 商店與 Google 地圖的（GAS 版），以及車廠自建生態的（純 AOSP 版，例如某些採用自家地圖與語音的品牌）。

## 二、為什麼值得投入

從工程與職涯角度，有三個實際理由：

**生態複用。** 車廠不必從零打造 OS 與開發者生態，可以沿用成熟的 Android framework、工具鏈（Android Studio、Gradle、adb）與龐大的 app 生態。對開發者而言，既有的 Android 技能可以直接遷移到車用領域。

**市場動能。** Volvo、Polestar、GM、Honda、Renault、Ford 等品牌都已量產採用 AAOS，它是目前車載 IVI（In-Vehicle Infotainment）作業系統的主流路線之一。

**SDV 趨勢核心。** 「軟體定義車輛（Software-Defined Vehicle）」是產業方向，車輛功能越來越由軟體決定並可 OTA 更新。AAOS 提供了一個標準化的軟體平台，讓車輛能力能像 app 一樣持續演進。

## 三、核心 Components

AAOS 建立在 AOSP 之上，多數 framework 與手機共用。真正的差異在「車用專屬」的這幾塊，這也是開發者要花心力的地方：

### 1. Vehicle HAL（VHAL）— 最核心的抽象層

VHAL 是 OS 與車輛硬體之間的邊界。它把「車速」「油量／電量」「空調溫度」「車門狀態」「檔位」等，統一抽象成一組標準化的 **property**，每個 property 有 ID、type、存取權限（讀／寫／訂閱）與變更通知機制。上層 app 只跟 property 打交道，完全不用管底層是哪家 ECU、走 CAN bus 還是其他匯流排。

property 分兩類：AOSP 定義的**標準 property**（`VehiclePropertyIds` 裡的常數，跨車廠一致），以及車廠自訂的 **vendor property**（用來暴露品牌專屬功能）。

### 2. Car Service 與 Car API（`android.car`）

這是給 app 開發者的入口。App 透過 `Car` 物件取得各種 manager，最常用的是 `CarPropertyManager`，用它去讀寫、訂閱 VHAL 暴露的 property。其他還有 `CarUxRestrictionsManager`（行車中的 UI 限制）、`CarAudioManager`（分區音訊）等。

### 3. Car UI Library（`car-ui-lib`）與 System UI

車廠透過 `car-ui-lib` 客製化系統外觀（狀態列、通知、清單元件），在維持一致互動邏輯的同時換上品牌視覺。System UI 則負責車機桌面、狀態列與導覽。

### 4. 多顯示與多使用者

一台車常有中控、數位儀表、抬頭顯示、副駕與後座娛樂等多個螢幕，AAOS 原生支援多 display 與多 user（例如駕駛與乘客不同帳號、不同權限）。

### 5. 車用專屬 app 範式

Dialer、Media、Messenger、車輛設定等都為駕駛情境重新設計：大觸控目標、語音優先、低視覺干擾。媒體與通訊類 app 走 **template 化**路線（見下節），由系統統一渲染 UI，確保行車安全。

### 6. Car Audio 與 Boot 效能

分區音訊（Car Audio Zones）讓不同區域播放不同來源；開機效能也是車用硬需求——例如倒車顯影必須在系統完全開機前就能顯示。

## 四、開發者入門路徑

### 步驟 0：確認你的角色

先想清楚你屬於哪一條路，資源重點差很多：

- **App 開發者**：重點在 `android.car` API、Car App Library、media/messaging template。不需要碰 AOSP 原始碼。
- **平台／車廠工程師**：重點在 VHAL 實作、HAL 整合、開機流程、客製 System UI，需要編譯 AOSP。

### 步驟 1：用 Emulator 起步（不用真車）

Android Studio 的 SDK Manager 內含 **Automotive system image**。安裝後在 Device Manager 建立一個 Automotive 虛擬裝置，就能跑起一個模擬車機，甚至能透過內建的車輛控制面板模擬改變車速、空調等 property 值——非常適合開發與除錯。

### 步驟 2：讀官方文件

以 `source.android.com/docs/automotive` 為權威起點，先把 VHAL 與 Car API 的概念讀通；App 開發面則參考 `developer.android.com` 的 Cars 專區。

### 步驟 3：寫第一段車輛資料存取

如果你已經會 Android 開發，從 `CarPropertyManager` 讀一個 property 開始。概念示意（Kotlin）：

```kotlin
// 1. 取得 Car 物件（實務上建議用 Car.createCar 的非同步版本並處理連線回呼）
val car = Car.createCar(context)

// 2. 取得 CarPropertyManager
val propertyManager =
    car.getCarManager(Car.PROPERTY_SERVICE) as CarPropertyManager

// 3. 讀取目前車速（PERF_VEHICLE_SPEED）
val speed = propertyManager.getFloatProperty(
    VehiclePropertyIds.PERF_VEHICLE_SPEED,
    /* areaId = */ 0
)

// 4. 訂閱變更，即時收到更新
propertyManager.registerCallback(
    object : CarPropertyManager.CarPropertyEventCallback {
        override fun onChangeEvent(value: CarPropertyValue<*>) {
            // 車速改變時被呼叫
        }
        override fun onErrorEvent(propId: Int, areaId: Int) {}
    },
    VehiclePropertyIds.PERF_VEHICLE_SPEED,
    CarPropertyManager.SENSOR_RATE_NORMAL
)
```

> 注意權限：存取車輛 property 需要對應的權限（例如車速類的 `android.car.permission.CAR_SPEED`），部分敏感或可寫入的 property 屬於 privileged/signature 權限，一般第三方 app 拿不到，需要車廠簽章或系統 app 身分。這也是車用開發跟一般 App 開發最大的體感差異之一。

### 步驟 4：依 app 類型選對 template

車用媒體與通訊 app 不自己畫 UI，而是實作對應的 service，由系統統一渲染，確保符合駕駛分心規範（driver distraction）。做地圖／導航、停車、充電類 app，則參考 **Android for Cars App Library** 的 template 模型。

### 步驟 5（平台向）：進 AOSP

想深入平台層，clone AOSP、編譯 automotive target，重點研讀 `packages/services/Car`（Car Service 與 API 實作）與 VHAL 的 reference 實作，學 property 如何定義、如何新增 vendor property、如何對接真實硬體。

## 五、常見坑與心法

- **別把手機思維直接搬過來**：行車中有 UX 限制（`CarUxRestrictions`），很多互動在車輛移動時會被系統擋掉，UI 要為「瞄一眼就懂」設計。
- **權限模型更嚴**：能讀不代表能寫，能在 emulator 測不代表第三方身分拿得到權限。早點確認你要的 property 屬於哪一級權限。
- **多螢幕與多帳號**：測試要涵蓋不同 display 與 user 情境，別只在單一中控畫面驗證。
- **先 emulator、後真機**：真車硬體與 VHAL 實作因車廠而異，先在模擬器把邏輯打穩，能省掉大量上車除錯的時間。

## 六、下一步

- App 開發者：從 emulator + 一支讀取車輛 property 的小 app 練手，再研究 media 或 App Library template。
- 平台工程師：編一次 automotive AOSP，讀懂 `packages/services/Car` 與 VHAL，試著加一個 vendor property 端到端跑通。

兩條路都建議搭配官方 codelab 與 Google I/O 的 automotive session，循序漸進最省力。

---

*註：AAOS 版本演進與 API 細節會隨 Android 版本更新，實作前請以 source.android.com 與 developer.android.com 上對應版本的最新文件為準。*
