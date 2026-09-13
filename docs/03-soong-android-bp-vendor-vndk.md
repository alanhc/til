# Soong 與 Android.bp 實戰:vendor variant 與 VNDK

> 系列文章之三。總覽請見《Chip Vendor 視角的 Android Build System》。

Soong 是 AOSP 現行的 build system 主力,`Android.bp` 是它的設定檔。對 chip vendor 來說,寫 `Android.bp` 不只是語法問題——`vendor: true` 背後牽動的是 Treble 的 system/vendor 分離、VNDK 的連結規則,以及「你的 library 到底能 link 誰」這個每天都會撞到的問題。

---

## 一、Soong 基礎:宣告式,不寫邏輯

### 1.1 設計哲學

`Android.mk` 時代最大的災難是:Make 是圖靈完備的,人人都在裡面寫巧妙的邏輯,結果 build 行為無法分析、無法平行、無法快取。Soong 的解法很激進:

- `Android.bp` 是**純宣告**,JSON-like 語法,**沒有條件式、沒有迴圈、沒有變數運算**(只有簡單的變數與串接)。
- 需要邏輯?兩條路:用 Soong 內建的 `soong_config_module` 機制,或(極少數情況)寫 Go plugin。
- Soong 解析所有 `.bp` → 產生 Ninja 規則;還沒遷移的 `.mk` 由 Kati 轉譯,兩者合併成一份 `build.ninja`。

### 1.2 基本語法

一個典型的 HAL library:

```python
cc_library_shared {
    name: "libmyvendor_camera_utils",
    vendor: true,                      // 這行是 chip vendor 的靈魂,見第二節
    srcs: [
        "src/utils.cpp",
        "src/pipeline.cpp",
    ],
    local_include_dirs: ["include"],
    shared_libs: [
        "liblog",
        "libutils",
        "libcutils",
    ],
    static_libs: ["libmyvendor_isp_algo"],   // 原始碼不公開的演算法常做成 static prebuilt
    cflags: [
        "-Wall",
        "-Werror",
        "-DMYVENDOR_SOC=1",
    ],
    proprietary: true,
}
```

常用 module 類型速查:

| Module type | 用途 |
|---|---|
| `cc_library_shared` / `cc_library_static` / `cc_library` | C/C++ library(`cc_library` 同時產 shared+static) |
| `cc_binary` | native 執行檔(HAL service、daemon) |
| `cc_defaults` | 共用設定的「基底」,用 `defaults: [...]` 引用 |
| `cc_prebuilt_library_shared` | prebuilt `.so`(交付 blob 的標準做法) |
| `aidl_interface` | stable AIDL HAL 介面定義 |
| `android_app` / `android_app_import` | APK(源碼 / prebuilt) |
| `prebuilt_etc` | 安裝設定檔到 `/vendor/etc` 等 |
| `sh_binary` | shell script |
| `filegroup` | 檔案集合,供其他 module 引用 |

### 1.3 cc_defaults:公版工程的必備

Chip vendor 支援多專案時,用 `cc_defaults` 收斂共同設定:

```python
cc_defaults {
    name: "myvendor_hal_defaults",
    vendor: true,
    relative_install_path: "hw",
    cflags: ["-Wall", "-Werror"],
    shared_libs: ["liblog", "libbase"],
}

cc_binary {
    name: "android.hardware.camera.provider-service.myvendor",
    defaults: ["myvendor_hal_defaults"],
    srcs: ["service.cpp"],
    init_rc: ["camera-provider.rc"],
    vintf_fragments: ["camera-provider.xml"],
}
```

注意 `init_rc` 與 `vintf_fragments`:HAL service 的 init script 與 VINTF manifest 片段直接掛在 module 上,安裝時自動放到正確位置——比 `PRODUCT_COPY_FILES` 乾淨得多。

### 1.4 條件式設定:soong_config

`.bp` 不能寫 if,但 SoC 廠不可能一份 code 只有一種 build。官方解法:

```python
// 定義變數(通常在公版的 Android.bp)
soong_config_module_type {
    name: "myvendor_cc_defaults",
    module_type: "cc_defaults",
    config_namespace: "myvendor",
    variables: ["soc_gen"],
    properties: ["cflags", "srcs"],
}

soong_config_string_variable {
    name: "soc_gen",
    values: ["gen1", "gen2"],
}

// 使用變數
myvendor_cc_defaults {
    name: "myvendor_soc_defaults",
    soong_config_variables: {
        soc_gen: {
            gen1: { cflags: ["-DSOC_GEN=1"] },
            gen2: { cflags: ["-DSOC_GEN=2"], srcs: ["gen2_extra.cpp"] },
        },
    },
}
```

變數值在 product 的 `.mk` 裡設定:

```makefile
SOONG_CONFIG_NAMESPACES += myvendor
SOONG_CONFIG_myvendor += soc_gen
SOONG_CONFIG_myvendor_soc_gen := gen2
```

儀式感很重,但這是把「每個專案不同」收斂進宣告式世界的正規管道。

---

## 二、vendor variant:`vendor: true` 到底做了什麼

### 2.1 image variant 的概念

Treble 之後,同一個 library 可能要同時存在於 system 與 vendor 世界,而兩邊的依賴規則不同。Soong 因此引入 **image variant**:一個 module 可以有 core(system)、vendor、product 等多個變體,各自獨立編譯、獨立連結。

三個關鍵屬性:

```python
vendor: true              // 只 build vendor variant,裝到 /vendor
vendor_available: true    // system 與 vendor variant 都 build(給兩邊用的共用庫)
product_available: true   // 同理,for /product
```

- 你的 HAL、自家 daemon → `vendor: true`
- 你維護、但 system 端元件也要 link 的共用庫 → `vendor_available: true`(會編出兩份 `.so`,分別進 `/system/lib64` 與 `/vendor/lib64`)

### 2.2 連結規則:vendor module 能 link 誰?

這是日常撞牆最多的地方。原則:**vendor variant 只能 link 到「也有 vendor variant 的東西」**。

```
vendor module 可以 link:
  ✔ 其他 vendor: true 的 module
  ✔ vendor_available: true 的 module(link 到它的 vendor variant)
  ✔ LL-NDK library(liblog, libc, libm, libdl, libEGL...)
  ✘ 純 system library(framework 內部庫)→ build error
```

典型錯誤訊息:

```
error: module "libmyvendor_foo" variant "android_vendor.34_arm64_armv8-a_shared":
  depends on module "libbinderthreadstate" which is not visible / has no vendor variant
```

解法優先序:改用 stable AIDL/NDK 介面 > 請該庫 owner 加 `vendor_available` > 把功能搬進自己的 code。**不要**用 hack 繞過,VTS 與 linker namespace 在 runtime 還有第二道關卡(見 2.4)。

### 2.3 VNDK:歷史與現況

**VNDK(Vendor Native Development Kit)** 是 Treble 初期的機制:Google 挑選一批 system library 標成 `vndk: { enabled: true }`,快照(snapshot)版本化後放在 `/system/lib64/vndk-<ver>`,保證舊 vendor image 配新 system image 時還能找到相容的庫。

分類(理解舊 code 時仍會遇到):

| 類別 | 意義 |
|---|---|
| **LL-NDK** | ABI 永久穩定的底層庫(libc, liblog...),vendor 直接用 |
| **VNDK** | vendor 可用的 system 庫,隨 system 出貨、版本快照 |
| **VNDK-SP** | Same-Process HAL 用的子集(graphics 相關) |
| **VNDK-private** | 只有 VNDK 內部互相使用 |

**重要的現況**:Google 已在 **Android 15 起正式棄用並移除 VNDK**(vendor 端全面轉向 NDK / stable AIDL / `vendor_available` 機制),`ro.vndk.version` 走入歷史。但 chip vendor 的現實是同時維護多代產品——手上跑 Android 12–14 的專案,VNDK 規則依然天天生效;升級到 15 時,則要清掉對 VNDK snapshot 的依賴。**判斷方法**:看你分支裡 `BOARD_VNDK_VERSION` / `ro.vndk.version` 是否還存在。

### 2.4 Runtime 的第二道牆:linker namespace

Build 過了不代表跑得起來。Runtime 上,`/vendor` 的 process 活在獨立的 **linker namespace**,`ld.config.txt` 定義了它能 `dlopen`/link 的路徑白名單。常見症狀:

```
CANNOT LINK EXECUTABLE "/vendor/bin/hw/my-service":
  library "libfoo.so" not found: needed by main executable
```

→ 該庫不在 vendor namespace 的搜尋路徑。正解仍是把依賴改成合規的(NDK/AIDL/vendor 庫),而不是改 `ld.config.txt`(GSI 一刷就破功,VTS 也擋)。

---

## 三、Chip vendor 的典型場景

### 3.1 交付 prebuilt blob

演算法、ISP pipeline 這類核心 IP 不給源碼,標準做法:

```python
cc_prebuilt_library_shared {
    name: "libmyvendor_isp",
    vendor: true,
    strip: { none: true },        // 已 strip 過的話
    arch: {
        arm64: { srcs: ["lib64/libmyvendor_isp.so"] },
        arm:   { srcs: ["lib32/libmyvendor_isp.so"] },
    },
    shared_libs: ["liblog", "libutils"],
    check_elf_files: false,       // ELF 依賴檢查過不了時的逃生口(慎用)
}
```

配套紀律:blob 的依賴要越少越好(最好只依賴 LL-NDK),否則客戶升級 Android 版本時,你的 blob 就是相容性炸彈。

### 3.2 stable AIDL HAL

```python
aidl_interface {
    name: "vendor.myvendor.hardware.thermal",
    vendor_available: true,
    srcs: ["vendor/myvendor/hardware/thermal/*.aidl"],
    stability: "vintf",           // 宣告為 VINTF stable,凍結後不可亂改
    owner: "myvendor",
    backend: {
        cpp: { enabled: false },
        ndk: { enabled: true },
    },
    versions_with_info: [
        { version: "1", imports: [] },
    ],
}
```

`stability: "vintf"` + 凍結版本(`m <name>-freeze-api`)後,介面變更就受 API review 管制——這是你對客戶與 Google 的合約。

### 3.3 .mk → .bp 遷移

每年升級都要還的債。工具:

```bash
androidmk Android.mk > Android.bp   # 自動轉換,複雜邏輯要手工
```

轉不過去的常見原因:`.mk` 裡的 `ifeq` 邏輯(→ 改 soong_config)、shell 呼叫(→ 改 `genrule`)、動態產生的檔案清單(→ `filegroup` + glob)。

### 3.4 除錯工具箱

```bash
m nothing                          # 只跑解析與依賴檢查,驗 .bp 語法最快
m libmyvendor_foo                  # 單編 module
out/soong/module-graph.json        # module 依賴圖
m blueprint_tools && outdir/... bpfmt -w .   # .bp 格式化
grep -r "name: \"libfoo\"" --include=Android.bp .   # 找 module 定義
```

查一個 module 最後裝到哪、屬於哪個 variant:看 `out/soong/Android-<product>.mk` 或 `m <module> showcommands`。

---

## 結語

`Android.bp` 的語法半天就能學會,真正的知識在 image variant 的規則:

> **`vendor: true` 不是「裝到 /vendor」的路徑設定,而是一份連結合約——它宣告這個 module 活在 Treble 邊界的 vendor 側,從此只能透過 NDK、stable AIDL 與 vendor 庫跟世界往來。**

把這份合約內化成團隊紀律(依賴最小化、介面走 stable AIDL、blob 只靠 LL-NDK),每年的 Android 版本升級就會從災難變成例行公事。
