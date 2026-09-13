# GKI 與 Kleaf Kernel Build 實戰:Chip Vendor 視角

> 系列文章之二。總覽請見《Chip Vendor 視角的 Android Build System》。

Android 12 之後,chip vendor 交付 kernel 的方式被徹底改寫:從「一顆自己魔改的完整 kernel」變成「Google 的 GKI + 你的 vendor modules」。本文說明這個轉變的來龍去脈、Kleaf(Bazel-based kernel build)的實際操作,以及 KMI 帶來的工程紀律。

---

## 一、為什麼有 GKI:kernel 碎片化的終局

在 GKI 之前,每家 vendor 的 kernel 都是「上游 LTS + Google patch + SoC patch + ODM patch」的四層蛋糕,結果是:

- 同一個 Android 版本,市面上有數千種 kernel 變體。
- 安全性修補(security patch)要逐家逐專案 backport,常常永遠到不了終端使用者。
- Google 無法獨立更新 kernel。

Google 的解法分三步走:

1. **ACK(Android Common Kernel)**:Google 維護的 kernel tree,基於上游 LTS,加上 Android 需要的 patch。所有 vendor 從 ACK 分支。
2. **GKI(Generic Kernel Image)**:直接由 ACK build 出的通用 kernel binary,Google 簽章、Google 發佈,**所有裝置共用同一顆**。
3. **KMI(Kernel Module Interface)**:GKI 對外承諾的穩定 ABI。你的 driver 以 module 形式掛載,只要 KMI 不變,Google 更新 GKI 不會弄壞你的 module。

時間線:Android 11(kernel 5.4)試行 GKI 1.0;**Android 12(kernel 5.10)起,GKI 2.0 成為強制要求**——arm64 新裝置必須使用 Google 簽章的 GKI boot image。

### 對 chip vendor 的意義

你的 kernel 工作被切成兩塊:

| | 內容 | 你能做什麼 |
|---|---|---|
| **GKI 本體** | core kernel、Google 認可的 config | 不能改。要改 core 行為只能 upstream,或申請 vendor hook |
| **Vendor modules** | 你所有的 driver(GPU、camera、modem、power⋯⋯) | 完全自主,但只能用 KMI 匯出的 symbol |

**Vendor hook** 是 ACK 提供的官方後門:Google 在 core kernel 關鍵路徑上放 tracepoint-like 的 hook 點(`android_vh_*`),你的 module 可以掛上去改變行為(例如 scheduler 調校),而不用 patch core code。想要新 hook 得跟 Google 提案。

---

## 二、Kleaf:Bazel-based 的 kernel build

### 2.1 從 build.sh 到 Kleaf

Android kernel 的 build 系統演進:

- **舊時代**:kernel source 放在 platform tree 裡,跟著 `m` 一起編,或用 `build/build.sh` + `build.config` 設定檔。
- **現在(kernel 5.15+ / Android 13+)**:改用 **Kleaf**——基於 Bazel 的 kernel build 系統。`build.sh` 在新分支已移除。

Kernel build 完全獨立於 Android platform build:**自己的 repo manifest、自己的 toolchain(hermetic Clang)、自己的輸出**。Platform build 只是把 kernel 產物當 prebuilt 拿來打包。

### 2.2 基本操作

Kernel tree 的頂層(以 ACK 為例):

```bash
# 同步 kernel manifest(與 platform manifest 是分開的)
repo init -u https://android.googlesource.com/kernel/manifest -b common-android14-6.1
repo sync

# Build GKI kernel 本體
tools/bazel build //common:kernel_aarch64

# Build 發佈用產物(kernel + modules + headers 打包)
tools/bazel run //common:kernel_aarch64_dist -- --dist_dir=out/dist
```

Bazel 的特性帶來的好處:**hermetic**(toolchain、依賴全部鎖定,不吃環境變數)、**正確的增量 build**、**remote cache 友善**。代價是學習曲線與 BUILD 檔的儀式感。

### 2.3 Vendor 的 BUILD.bazel:定義你自己的 kernel build

Chip vendor 不直接 build `//common:kernel_aarch64`,而是定義自己的 target,引用 GKI 並加上自家 modules。核心規則是 `kernel_build` 與 `kernel_module`:

```python
# //vendor_soc/BUILD.bazel
load("//build/kernel/kleaf:kernel.bzl",
     "kernel_build", "kernel_module", "kernel_modules_install", "kernel_images")

kernel_build(
    name = "myboard",
    outs = ["myboard/vmlinux"],
    base_kernel = "//common:kernel_aarch64",   # 以 GKI 為基底
    build_config = "build.config.myboard",
    kmi_symbol_list = "abi_symbollist.myboard", # 你需要的 KMI symbols
)

kernel_module(
    name = "myboard_camera",
    srcs = glob(["drivers/camera/**"]),
    outs = ["my_camera.ko"],
    kernel_build = ":myboard",
)

kernel_modules_install(
    name = "myboard_modules_install",
    kernel_build = ":myboard",
    kernel_modules = [":myboard_camera", ":myboard_gpu", ...],
)

kernel_images(
    name = "myboard_images",
    build_vendor_boot = True,
    build_vendor_dlkm = True,
    kernel_build = ":myboard",
    kernel_modules_install = ":myboard_modules_install",
)
```

```bash
tools/bazel run //vendor_soc:myboard_dist -- --dist_dir=out/dist
```

產物:`Image`(通常直接用 Google 的 GKI prebuilt)、你的 `.ko` 們、`vendor_boot.img` / `vendor_dlkm.img` 的原料。

### 2.4 接回 platform build

Platform 端把 kernel 產物當 prebuilt:

```makefile
# BoardConfig.mk
BOARD_USES_GENERIC_KERNEL_IMAGE := true
BOARD_KERNEL_BINARIES := kernel-6.1        # GKI prebuilt
BOARD_VENDOR_RAMDISK_KERNEL_MODULES := $(wildcard $(KERNEL_OUT)/first_stage/*.ko)
BOARD_VENDOR_KERNEL_MODULES := $(wildcard $(KERNEL_OUT)/*.ko)
```

Module 分兩批載入:**vendor_boot 裡的 first-stage modules**(開機初期就要的:storage、display 基本 driver)與 **vendor_dlkm 裡的其餘 modules**(mount 完 vendor 後載入)。分錯批 → 開不了機或黑屏,是 GKI porting 最常見的問題之一。

---

## 三、KMI:穩定 ABI 的工程紀律

### 3.1 KMI 是什麼

KMI = GKI kernel 對 modules 承諾不變的介面集合:**exported symbols + 相關資料結構的 ABI**。Google 用 `libabigail`/STG 工具比對 ABI,凍結(KMI freeze)後,ACK 分支上任何會改變 KMI 的 patch 都不能進。

### 3.2 Symbol list:你要用的 symbol 得先登記

GKI 並非匯出所有 symbol 給 module 用。Vendor 要維護一份 **KMI symbol list**,列出自家 modules 需要的 kernel symbols:

```bash
# 從你的 modules 萃取使用到的 symbols
tools/bazel run //vendor_soc:myboard_abi_update_symbol_list
```

這份 list 要**提交回 ACK**(`android/abi_gki_aarch64_<vendor>`),Google 合併後,這些 symbol 才會被 GKI 保留匯出。所以:

- 用到還沒登記的 symbol → module load 失敗(unknown symbol)。
- 想用的 symbol 沒被 export(`EXPORT_SYMBOL_GPL`)→ 要先送 patch 到 ACK/upstream 加 export,可能被拒。

### 3.3 ABI 檢查

```bash
tools/bazel build //vendor_soc:myboard_abi_dist   # build + ABI 比對
```

如果你的 kernel 改動破壞了 KMI(改了公用 struct 的 layout、變更函式簽名),ABI diff 會直接報錯。KMI freeze 之後,這類改動 = 不能出貨用 GKI = 重新設計。

**實務教訓**:所有「在 struct 裡加個欄位就好了」的老習慣都行不通了。正規做法是用 ACK 預留的 `android_vendor_data` / `android_kabi_reserve` 欄位,或改用自己模組內部的資料結構。

---

## 四、Boot image 的重組

GKI 時代的 boot 相關 image 分工:

```
boot.img         = GKI kernel(Google 簽章)+ generic ramdisk
init_boot.img    = generic ramdisk 獨立出來(Android 13+)
vendor_boot.img  = vendor ramdisk + first-stage modules + bootconfig
vendor_dlkm.img  = 其餘 vendor modules(動態分割區)
dtbo.img         = 板級 device tree overlay
```

出貨時 `boot.img` 可以直接用 Google 發佈的 **certified GKI boot image**;若你重編過 GKI(除錯用),量產仍須換回 Google 簽章版本,否則過不了 VTS 的 GKI 檢查。

---

## 五、常見坑與除錯

**Module load 失敗**
```
insmod: failed to load my_camera.ko: Unknown symbol in module
```
→ symbol 沒進 KMI symbol list,或 GKI 版本與 module 編譯時的 KMI 不符。用 `modinfo` 檢查 `vermagic` 與依賴。

**開機卡在 first stage**
→ storage/display driver 沒放進 vendor_boot 的 first-stage module list,或 `modules.load` 順序錯誤。從 serial console 看 init 的 log。

**ABI diff 過不了**
→ 檢查是不是動到了公共 header 的 struct。優先考慮 vendor hook / reserve 欄位,而不是硬改。

**Bazel 抱怨環境**
→ Kleaf 是 hermetic 的,不要試圖塞環境變數進去;設定應該進 `build.config` 或 BUILD 檔。

**升級 LTS(如 6.1 → 6.6)**
→ KMI 是「每個 kernel 版本一份」,升版 = 重新走一輪 symbol list + ABI 驗證 + 全部 module 重新驗證。

---

## 結語

GKI + Kleaf 把 chip vendor 的 kernel 工程從「維護一顆私有 kernel」轉變為「在穩定 ABI 上開發 modules」:

> **Core kernel 是 Google 的,module 是你的;KMI 是合約,Kleaf 是履約工具。**

短期是痛苦的遷移成本(build 系統重學、driver 模組化、symbol 治理),長期換到的是:security patch 由 Google 直接更新、kernel 升級與 vendor 開發解耦。這條路沒有回頭,越早把 driver 模組化、把 KMI 紀律建進 CI,升級成本越低。
