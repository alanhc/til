# 深入淺出 Android Build System:Chip Vendor 視角

App 開發者眼中的 Android build system 是 Gradle 與 AGP;但對 chip vendor(SoC 廠)而言,build system 是另一個世界——你不是在寫 `build.gradle`,而是在維護一份 **BSP(Board Support Package)**,讓 OEM/ODM 拿你的 SoC 能 build 出一整台裝置的所有 image。本文從 chip vendor 的日常出發,拆解 AOSP build system 的骨架、你的地盤在哪裡、Google 劃給你的邊界,以及最終產出物。

---

## 一、整體架構:repo → lunch → Soong/Ninja

### 1.1 原始碼管理:repo 與 manifest

AOSP 不是單一 git repo,而是**數百個 git repo 的集合**,用 Google 自家的 `repo` 工具加一份 manifest XML 統籌。Chip vendor 通常維護自己的 manifest server,把三種來源組合起來:

- AOSP 上游 repo(framework、bionic、art⋯⋯)
- 自家 BSP repo(kernel、HAL、driver、私有工具)
- 客戶專案 repo(device tree、客製 app)

```bash
repo init -u <your-manifest-url> -b <branch>
repo sync -j16
```

版本升級(例如 Android 14 → 15)的第一步,就是把 manifest 指到新的 AOSP tag,然後開始漫長的 merge 與 conflict 解決。

### 1.2 進入 build:envsetup 與 lunch

```bash
source build/envsetup.sh
lunch <your_product>-userdebug   # 選 TARGET_PRODUCT + build variant
m                                 # build 全部 image
```

`lunch` 做的事是設定一組環境變數(`TARGET_PRODUCT`、`TARGET_BUILD_VARIANT`、`TARGET_ARCH`⋯⋯),後續整個 build 都由這組變數驅動。

### 1.3 底層引擎:Soong + Kati → Ninja

AOSP build system 的執行流程:

```
Android.bp (Soong 解析) ─────┐
                              ├──▶ 合併成一份巨大的 build.ninja ──▶ Ninja 執行
Android.mk (Kati 轉譯) ──────┘
```

三個角色:

- **Soong**:讀取宣告式的 `Android.bp`(JSON-like 語法,刻意不能寫邏輯),是現在的主力。
- **Kati**:把還沒遷移的舊 `Android.mk`(GNU Make 語法)轉譯成 Ninja 規則。
- **Ninja**:最底層的執行引擎,只管照依賴圖平行執行,速度極快。

Vendor 的歷史包袱通常是 `.mk` 大戶——每次 Android 版本升級,Google 都會再禁用一批 Make 功能,逼你把 `.mk` 遷到 `.bp`。這筆技術債每年都要還一點。

> Soong/`Android.bp` 的細節(module 種類、vendor variant、VNDK)請見系列文章《Soong 與 Android.bp 實戰》。

---

## 二、你的地盤:device tree 與 product 繼承

Chip vendor 的程式碼主要落在四個地方:

```
device/<vendor>/<board>/     # 板級設定:BoardConfig.mk, device.mk, sepolicy, init.rc, fstab
vendor/<vendor>/             # proprietary blobs、私有工具、加值功能
hardware/<vendor>/           # HAL 實作(camera, audio, gpu, modem...)
kernel/                      # kernel source 或 prebuilt(GKI 時代改為獨立 build)
```

### 2.1 兩條設定軸線:product 層 vs board 層

初學者最容易混淆的就是這兩個檔案的分工:

**`device.mk`(product 層)——決定「裝什麼」:**

```makefile
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, device/myvendor/common/soc_common.mk)

PRODUCT_PACKAGES += \
    android.hardware.camera.provider-service \
    MyVendorCameraApp

PRODUCT_COPY_FILES += \
    device/myvendor/myboard/media_codecs.xml:$(TARGET_COPY_OUT_VENDOR)/etc/media_codecs.xml

PRODUCT_VENDOR_PROPERTIES += \
    ro.vendor.camera.max_res=4000x3000
```

**`BoardConfig.mk`(board 層)——決定「怎麼 build」:**

```makefile
TARGET_ARCH := arm64
TARGET_CPU_ABI := arm64-v8a
BOARD_KERNEL_CMDLINE := console=ttyS0 androidboot.hardware=myboard
BOARD_SUPER_PARTITION_SIZE := 9126805504
BOARD_USES_GENERIC_KERNEL_IMAGE := true
```

### 2.2 繼承鏈:SoC 公版 → 客戶專案

Chip vendor 的商業模式決定了 device tree 的結構:你提供一份 **SoC 公版(reference design)config**,ODM 用 `inherit-product` 繼承後,只疊上自己的差異(panel、camera module、BOM 選料)。繼承鏈可能長這樣:

```
aosp 的 core.mk
  └─ device/myvendor/common/soc_common.mk      (SoC 公版,你維護)
      └─ device/odm_x/project_y/device.mk       (客戶專案)
```

公版設計得好不好,直接決定你 support 一百個客戶專案時的維護成本。

### 2.3 Build variant:eng / userdebug / user

| Variant | 用途 | 特性 |
|---|---|---|
| `eng` | 內部開發 | 預設 root、包含 debug 工具、不最佳化 |
| `userdebug` | 給 OEM 調試 | 可 `adb root`、可 debug,但行為接近量產 |
| `user` | 量產出貨 | 不可 root、`ro.debuggable=0`、正式簽章 |

常見的出貨前地雷:整個開發週期都在 userdebug 上跑,量產前才切 user build + release key,結果 SELinux enforcing、簽章權限、`ro.secure` 的行為差異一次爆出來。**務必在專案中期就開始定期跑 user build。**

---

## 三、Treble 與 GKI:Google 劃給你的邊界

這是 chip vendor 最需要深入理解的部分,因為 Google 近十年的主軸就是:**把 vendor 的 code 從 system 與 kernel 裡趕出去,並用穩定介面隔開**。

### 3.1 Treble(Android 8+):system / vendor 分離

- 你的東西全部進 `/vendor` partition。
- Vendor 與 system 之間只能透過 **HAL** 溝通,早期是 HIDL,現在主推 **stable AIDL**。
- 介面相容性由 **VINTF**(vendor interface)機制把關:vendor 提供 manifest(我實作了哪些 HAL、什麼版本),framework 提供 compatibility matrix(我需要哪些 HAL),開機與 OTA 時互相檢查。
- 終極目標:Google 的 **GSI(Generic System Image)** 刷上你的裝置要能開機——**VTS 測試**就是在驗這件事,過不了 VTS 拿不到 GMS 認證。

### 3.2 GKI(Android 12+ 強制):kernel 也被拆了

你不能再交付整顆客製 kernel。取而代之:

- Google 提供 **GKI(Generic Kernel Image)**,即 `boot.img` 裡的 kernel 本體。
- 你的 driver 全部變成 **vendor modules(.ko)**,放在 `vendor_boot.img` / `vendor_dlkm.img`,只能透過 **KMI(Kernel Module Interface,穩定的 kernel ABI)** 掛進 GKI。
- Kernel 改用 **Kleaf(Bazel)** 在 Android platform tree 之外獨立 build。
- 想改 core kernel?只能走 upstream 或 ACK(Android Common Kernel)的 vendor hook。對習慣魔改 kernel 的 vendor,這是最大的文化衝擊。

> GKI/Kleaf 的 build 細節請見系列文章《GKI 與 Kleaf Kernel Build 實戰》。

### 3.3 SELinux sepolicy:同樣被切成兩半

Sepolicy 分成 platform policy(Google 管)與 vendor policy(你管)。你的每一支 HAL service、每一個 daemon 都要自己寫 policy;違反 Google 定義的 `neverallow` 規則會**直接 build fail**。

> Sepolicy 的除錯手法請見系列文章《SELinux Sepolicy 除錯實戰》。

---

## 四、產出物:partition 與 image

`m` 跑完後,產物在 `out/target/product/<board>/`:

| Image | 內容 | 主要負責者 |
|---|---|---|
| `boot.img` | GKI kernel + generic ramdisk | Google(你整合) |
| `vendor_boot.img` | vendor ramdisk + 早期載入的 kernel modules | **你** |
| `vendor_dlkm.img` | 其餘 kernel modules | **你** |
| `dtbo.img` | device tree overlay | **你** |
| `vendor.img` | HAL、blobs、vendor sepolicy | **你** |
| `odm.img` | ODM 客製(在你的 vendor 之上再疊一層) | ODM |
| `system.img` | AOSP framework | Google/OEM |
| `product.img` | OEM 加值 app 與設定 | OEM |
| `super.img` | 動態分割區容器(system/vendor/product 等打包進去) | build system |

**Dynamic partitions(super partition)** 是 Android 10 之後的標準:system/vendor/product 不再是固定大小的實體分割區,而是 super 裡的 logical partition,OTA 時可以調整大小。`BOARD_SUPER_PARTITION_SIZE` 算錯導致 image 塞不下,是每個 BSP 工程師都踩過的坑。

出貨相關的兩個關鍵命令:

```bash
m target-files-package    # 產生簽章與 OTA 的原料(target_files.zip)
m otapackage              # 產生 OTA 更新包
```

量產時用 `sign_target_files_apks` 把 test key 換成 release key。

> 完整流程請見系列文章《OTA 與簽章流程實戰》。

---

## 五、Chip vendor 的日常與生存技能

實務上,BSP 團隊的工作循環大致是:

1. **年度大版本升級**:merge 新版 AOSP、修 `.mk` → `.bp` 遷移、追新的 VNDK/sepolicy/VINTF 規定、重跑 CTS/VTS/GTS。
2. **維護 SoC 公版 device tree**,支援下游數十到數百個客戶專案。
3. **交付 proprietary blobs**:以 prebuilt module 或 `PRODUCT_COPY_FILES` 形式給客戶,原始碼不出門。
4. **認證**:CTS(相容性)、VTS(Treble/vendor interface)、GTS(GMS)全數過關,客戶才能出貨。

Build 效能是生存問題——full build 動輒 1–2 小時,所以:

- `m <module_name>` 單編一個 module,搭配 `adb sync` / `adb push` 局部驗證。
- `ccache` 對 C/C++ 大戶(kernel、HAL)效果顯著。
- `m installclean` 清 image 但保留中間產物,是「怪怪的但不想 rm -rf out」時的第一步。
- Incremental build 真的壞掉時,`rm -rf out` 換一小時安心——每個 BSP 工程師都懂這個取捨。

---

## 結語

一句話總結 chip vendor 眼中的 Android build system:

> **repo 管原始碼,lunch 選產品,Soong/Ninja 負責把幾萬個 module 編成十幾個 image;而 Treble 與 GKI 定義了你和 Google 的楚河漢界——你的世界在 `/vendor` 與 kernel modules,介面之外的事,Google 不准你碰,也不需要你碰。**

理解這個邊界,是 BSP 工程師所有日常工作——porting、除錯、認證、出貨——的共同前提。

---

### 系列文章

1. **本文**:Chip Vendor 視角的 Android Build System 總覽
2. 《GKI 與 Kleaf Kernel Build 實戰》
3. 《Soong 與 Android.bp 實戰:vendor variant 與 VNDK》
4. 《SELinux Sepolicy 除錯實戰》
5. 《OTA 與簽章流程實戰》
6. 《xTS 認證測試實戰:CTS/VTS/GTS/STS》
7. 《開機流程與 Bootloader 實戰》
8. 《HAL 開發實戰:AIDL End-to-End》
9. 《Android 年度版本升級方法論》
10. 《效能與功耗調校實戰》
11. 《Camera 與多媒體 Pipeline 實戰》
12. 《Ramdump 與穩定性除錯實戰》
13. 《工廠與量產流程實戰》
14. 《Android 上的 Rust》
15. 《Project Mainline 與 APEX 對 Vendor 的影響》
16. 《多專案 BSP 的 Branch 與 Manifest 管理》
