# Android Product Flavor 完整教學:一份程式碼,多個 App

## 前言

在真實的 Android 開發裡,你經常會遇到這種需求:同一套 App 需要有免費版和付費版、需要賣給不同客戶做成白牌(white-label)、或是需要區分開發、測試、正式三種環境。

最直覺但最糟糕的做法,是把專案複製好幾份分別維護。這會讓你陷入災難——修一個 bug 要改好幾個地方,程式碼很快就會失去同步。

Android Gradle 的 **product flavor(產品風味)** 就是為了解決這個問題而生。它讓你從**同一份程式碼庫**,透過設定產生出多個彼此獨立、卻共用大部分程式碼的 App 版本。這篇文章會從概念一路帶到實戰。

---

## 一、核心概念:Build Type、Product Flavor、Build Variant

在動手之前,先搞懂三個名詞的關係,後面一切都建立在這上面。

### Build Type(建置類型)

Build type 描述的是「**這次建置是拿來做什麼用的**」。Android 專案預設就有兩種:

- `debug`:開發用,可除錯、不需簽章、通常會關掉程式碼混淆
- `release`:上架用,會做簽章、通常會開啟 R8/ProGuard 混淆與最佳化

Build type 關注的是「建置的品質與用途」,而不是「App 的內容差異」。

### Product Flavor(產品風味)

Product flavor 描述的是「**這是哪一個版本的產品**」。免費版 vs 付費版、客戶 A vs 客戶 B、國內版 vs 國際版——這些屬於產品層面的差異,就是 flavor 要處理的。

### Build Variant(建置變體)

**Build variant = Build type × Product flavor** 的組合。

假設你有兩個 flavor(`free`、`pro`)和兩個 build type(`debug`、`release`),Gradle 會自動幫你產生 2 × 2 = 4 個 build variant:

| | debug | release |
|---|---|---|
| **free** | freeDebug | freeRelease |
| **pro** | proDebug | proRelease |

你在 Android Studio 左下角的「Build Variants」面板,就能切換目前要建置哪一個變體。這是理解整套機制最關鍵的一張表。

---

## 二、第一個 Flavor 設定

Flavor 定義在模組層級的 `build.gradle`(或 `build.gradle.kts`)裡的 `android { }` 區塊。

從 Android Gradle Plugin 3.0 開始,每個 flavor **都必須屬於某個 flavor dimension(維度)**,即使你只有一個維度也一樣。

### Groovy 版本(`build.gradle`)

```gradle
android {
    // 宣告一個維度,名稱可自訂
    flavorDimensions "version"

    productFlavors {
        free {
            dimension "version"
            applicationId "com.example.myapp.free"
            versionNameSuffix "-free"
        }
        pro {
            dimension "version"
            applicationId "com.example.myapp.pro"
            versionNameSuffix "-pro"
        }
    }
}
```

### Kotlin DSL 版本(`build.gradle.kts`)

```kotlin
android {
    flavorDimensions += "version"

    productFlavors {
        create("free") {
            dimension = "version"
            applicationId = "com.example.myapp.free"
            versionNameSuffix = "-free"
        }
        create("pro") {
            dimension = "version"
            applicationId = "com.example.myapp.pro"
            versionNameSuffix = "-pro"
        }
    }
}
```

幾個重點:

- `applicationId` 不同,代表兩個版本可以**同時安裝在同一台手機上**,在 Google Play 上也是兩個獨立的 App。
- `versionNameSuffix`、`applicationIdSuffix` 讓你在既有版本號後面附加後綴,方便辨識。
- 沒有特別設定的屬性,會**繼承自 `defaultConfig`**。

---

## 三、每個 Flavor 可以客製什麼

Flavor 的威力在於它能覆寫的東西非常多,大致分成三類。

### 1. Gradle 設定層面

在 flavor 區塊裡可以覆寫幾乎所有 `defaultConfig` 的屬性:

```gradle
productFlavors {
    free {
        dimension "version"
        applicationId "com.example.myapp.free"
        minSdk 24
        // 用 BuildConfig 欄位在程式碼裡判斷
        buildConfigField "boolean", "IS_PRO", "false"
        buildConfigField "String", "API_BASE_URL", "\"https://api.example.com/free/\""
        // 用 resValue 動態產生資源
        resValue "string", "app_name", "MyApp Free"
    }
    pro {
        dimension "version"
        applicationId "com.example.myapp.pro"
        buildConfigField "boolean", "IS_PRO", "true"
        buildConfigField "String", "API_BASE_URL", "\"https://api.example.com/pro/\""
        resValue "string", "app_name", "MyApp Pro"
    }
}
```

在程式碼裡就能這樣用:

```kotlin
if (BuildConfig.IS_PRO) {
    unlockPremiumFeatures()
} else {
    showUpgradeBanner()
}

val client = ApiClient(baseUrl = BuildConfig.API_BASE_URL)
```

> 提醒:使用 `buildConfigField` 時,新版 AGP 需要在 `buildFeatures { buildConfig = true }` 明確開啟 BuildConfig 產生。

### 2. 資源覆寫(source set)

這是 flavor 最優雅的部分。每個 flavor 都有專屬的**目錄**,結構跟 `main` 完全一樣:

```
app/
└── src/
    ├── main/          ← 所有 flavor 共用
    │   ├── java/
    │   ├── res/
    │   └── AndroidManifest.xml
    ├── free/          ← 只有 free flavor 用
    │   └── res/
    │       ├── drawable/ic_launcher.png
    │       └── values/colors.xml
    └── pro/           ← 只有 pro flavor 用
        └── res/
            ├── drawable/ic_launcher.png
            └── values/colors.xml
```

當你建置 `freeRelease` 時,Gradle 會把 `main/` 和 `free/` 合併,`free/` 裡的資源會**覆蓋(override)** `main/` 裡同名的資源。所以你可以讓免費版和付費版有不同的 App 圖示、主色調、字串,而完全不動到程式邏輯。

### 3. 程式碼覆寫

同樣的邏輯也適用於程式碼。你可以在 `main/` 定義介面,在各 flavor 提供不同實作:

```
src/
├── main/java/com/example/analytics/AnalyticsTracker.kt   ← 介面
├── free/java/com/example/analytics/AnalyticsTrackerImpl.kt ← 免費版:接免費分析服務
└── pro/java/com/example/analytics/AnalyticsTrackerImpl.kt  ← 付費版:接進階分析服務
```

**重要規則**:某個類別如果在 flavor 目錄提供,就**不能**同時也放在 `main/`,否則會編譯衝突(重複類別)。要嘛全放 flavor、要嘛全放 main,不能兩邊都有同一個檔案。

---

## 四、多維度 Flavor(Flavor Dimensions)

真實情境常常有「兩個獨立的軸」。例如:

- 一個軸是**版本**:free / pro
- 另一個軸是**環境**:dev / prod

如果不用維度,你得手動列出 free-dev、free-prod、pro-dev、pro-prod 四種組合,非常笨。維度讓 Gradle 自動幫你做笛卡兒積:

```gradle
android {
    flavorDimensions "version", "environment"

    productFlavors {
        free {
            dimension "version"
            buildConfigField "boolean", "IS_PRO", "false"
        }
        pro {
            dimension "version"
            buildConfigField "boolean", "IS_PRO", "true"
        }
        dev {
            dimension "environment"
            applicationIdSuffix ".dev"
            buildConfigField "String", "API_URL", "\"https://dev.example.com/\""
        }
        prod {
            dimension "environment"
            buildConfigField "String", "API_URL", "\"https://api.example.com/\""
        }
    }
}
```

這樣會產生的 flavor 組合(再乘上 build type):

- freeDev, freeProd, proDev, proProd
- 各自再 × debug / release = **總共 8 個 build variant**

`flavorDimensions` 的**宣告順序決定優先權**:排在前面的維度優先權較高,當不同維度的設定衝突時,前面的會蓋過後面的。變體命名也是照維度順序:`free` + `dev` → `freeDev`。

對應的 source set 目錄則會多出「組合目錄」,例如 `src/freeDev/`,可以放只屬於這個特定組合的資源。

---

## 五、實戰情境:做出免費版與付費版

把前面的東西串起來,走一次完整流程。

**目標**:同一個記帳 App,免費版有廣告、限制帳戶數;付費版無廣告、無限制。

**步驟一:定義 flavor**

```gradle
android {
    buildFeatures { buildConfig = true }
    flavorDimensions "tier"

    productFlavors {
        free {
            dimension "tier"
            applicationId "com.example.budget.free"
            resValue "string", "app_name", "Budget Free"
            buildConfigField "boolean", "SHOW_ADS", "true"
            buildConfigField "int", "MAX_ACCOUNTS", "2"
        }
        pro {
            dimension "tier"
            applicationId "com.example.budget.pro"
            resValue "string", "app_name", "Budget Pro"
            buildConfigField "boolean", "SHOW_ADS", "false"
            buildConfigField "int", "MAX_ACCOUNTS", "999"
        }
    }
}
```

**步驟二:在程式碼裡用這些旗標**

```kotlin
class AccountViewModel : ViewModel() {
    fun canAddAccount(currentCount: Int): Boolean {
        return currentCount < BuildConfig.MAX_ACCOUNTS
    }
}

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (BuildConfig.SHOW_ADS) {
            adBanner.visibility = View.VISIBLE
            adBanner.loadAd()
        } else {
            adBanner.visibility = View.GONE
        }
    }
}
```

**步驟三:各自準備專屬圖示**

把免費版圖示放到 `src/free/res/mipmap-*/`,付費版放到 `src/pro/res/mipmap-*/`。

**步驟四:切換與建置**

在 Android Studio 的 Build Variants 面板切換,或用指令列:

```bash
# 建置付費版 release
./gradlew assembleProRelease

# 建置免費版 debug 並安裝
./gradlew installFreeDebug

# 一次建置所有變體
./gradlew assemble
```

Gradle 也會自動產生對應的 task,例如 `testFreeDebugUnitTest`、`connectedProDebugAndroidTest`,讓你能針對特定變體跑測試。

---

## 六、依賴管理:針對特定 Flavor 加套件

某些第三方 SDK 只有特定版本才需要。Gradle 提供 flavor 專屬的依賴設定,格式是 `<flavorName>Implementation`:

```gradle
dependencies {
    // 所有版本共用
    implementation "androidx.core:core-ktx:1.13.0"

    // 只有免費版才引入廣告 SDK
    freeImplementation "com.google.android.gms:play-services-ads:23.0.0"

    // 只有付費版才引入進階分析
    proImplementation "com.example:premium-analytics:1.2.0"
}
```

這能讓免費版不必背負付費版才需要的套件,反之亦然,有效控制 App 體積。

---

## 七、常見陷阱與最佳實踐

**每個 flavor 一定要指定 dimension。** 只要你宣告了 `flavorDimensions`,所有 flavor 都得歸屬某個維度,漏掉一個就會建置失敗。

**同名檔案別兩邊都放。** 程式碼類別不能同時存在於 `main/` 和 flavor 目錄;資源可以(會被覆寫),但程式碼會直接編譯衝突。

**善用 `defaultConfig` 收斂共同設定。** 相同的東西放 `defaultConfig`,只有真正不同的才寫進 flavor,避免重複。

**變體數量會爆炸。** 維度和 build type 是相乘關係,兩個維度各三個 flavor、再兩個 build type,就是 3 × 3 × 2 = 18 個變體。用 `variantFilter`(或新版的 `androidComponents { beforeVariants { } }`)過濾掉不需要的組合,能大幅縮短建置與同步時間。

```gradle
android {
    variantFilter { variant ->
        // 例如:不需要「dev 環境的 release 版」
        def names = variant.flavors*.name
        if (names.contains("dev") && variant.buildType.name == "release") {
            setIgnore(true)
        }
    }
}
```

**別把祕密資訊寫死在 `buildConfigField`。** API key、簽章密碼這類敏感資料不該硬編進 Gradle 檔並提交到版控,應改用 `local.properties`、環境變數或 secrets 管理機制讀入。

**flavor 不是萬能。** 如果版本之間差異極大(幾乎是兩個不同的 App),硬用 flavor 反而會讓程式碼充滿 `if (BuildConfig.XXX)` 判斷而難以維護。這種情況把共用邏輯抽成 library module、各版本各自建 app module,往往更清爽。

---

## 結語

Product flavor 的核心價值,是把「產品差異」和「程式邏輯」漂亮地分離開來:相同的功能只寫一次放在 `main`,不同的部分透過設定、資源覆寫和專屬 source set 來表達。

一旦你掌握了「build type × flavor = variant」這條主線,再理解維度如何做組合,就能從容應付免費/付費、多環境、白牌客製這些常見需求,而不必維護一堆平行的專案副本。建議先從單一維度、兩個 flavor 的小例子動手做一次,把 Build Variants 面板切換幾遍,感受一下資源覆寫的效果,概念會立刻變得具體。
