# Pixel 8 Kernel Driver 開發實戰

在 Pixel 8(codename `shiba`)上從零寫出 kernel driver 並在實機驗證的完整流程。

本文件分兩條路線:

* **快速路線** — 編譯 `.ko` 後 `adb push` + `insmod`,不刷機。已在實機完整驗證。
* **完整路線** — 把 module 整合進 Kleaf 與 `vendor_dlkm.img` 後刷機。未驗證,供參考。

先確認你屬於哪種情況:

| 你的裝置 | 建議路線 |
|---|---|
| userdebug / eng build,`adb root` 可用 | **快速路線**,不用刷機 |
| production build(市售機出廠狀態) | 完整路線,或先刷 userdebug 版本 |

**先跑這兩個指令判斷:**

```bash
adb shell getprop ro.build.type
```

```bash
adb root && adb shell id
```

看到 `userdebug`(或 `eng`)且 `uid=0(root)`,就走快速路線。

---

# Part 1:快速路線

以下每一步都在實機驗證過。

## 1.1 前置檢查

除了 root,還要確認 kernel 沒有強制模組簽章:

```bash
adb shell "zcat /proc/config.gz | grep -E 'CONFIG_MODULE_SIG_FORCE|CONFIG_MODVERSIONS|CONFIG_MODULES='"
```

理想結果:

```text
CONFIG_MODULES=y
CONFIG_MODVERSIONS=y
# CONFIG_MODULE_SIG_FORCE is not set
```

`CONFIG_MODULE_SIG_FORCE is not set` 是關鍵 — 表示未簽章的模組也能載入。若它是 `=y`,未簽章模組一律被拒,只能走完整路線。

記錄裝置的 kernel 版本,等下要對應 source branch:

```bash
adb shell uname -r
```

範例輸出:

```text
6.1.99-android14-11-gd7dac4b14270-ab12946699
```

拆解:`6.1.99` 是 kernel 版本,`android14` 是 GKI 世代,`gd7dac4b14270` 是 git commit。

## 1.2 安裝工具

```bash
sudo apt update && sudo apt install -y git curl repo adb fastboot python3 build-essential rsync zip unzip bc bison flex libssl-dev libelf-dev
```

Clang 工具鏈不用自己裝,kernel manifest 會一起同步 prebuilt 版本。

## 1.3 同步 GKI kernel source

**只需要 GKI common kernel,不需要整棵 Pixel device tree。** 這是快速路線省時間的關鍵 — GKI 約 18G,Pixel 完整 kernel tree 大得多。

branch 名稱對應 `uname -r` 裡的 GKI 世代:裝置是 `android14` + kernel `6.1`,所以用 `common-android14-6.1`。

```bash
mkdir -p ~/android14-6.1 && cd ~/android14-6.1
```

```bash
repo init -u https://android.googlesource.com/kernel/manifest -b common-android14-6.1 --depth=1
```

```bash
repo sync -c --no-tags -j8
```

同步約 15 分鐘、18G。完成後應看到:

```text
build  common  common-modules  external  kernel  prebuilts  tools  WORKSPACE
```

### 版本不完全相符沒關係

同步下來的 `common/` 通常比裝置新(例如 tree 是 6.1.175,裝置是 6.1.99)。**這不影響模組載入**,原因有兩個:

1. 開了 `CONFIG_MODVERSIONS` 時,kernel 的 `same_magic()` 會跳過 vermagic 開頭的版本字串,只比對符號 CRC。
2. `android14-6.1` 的 KMI(Kernel Module Interface)已凍結,匯出符號的 CRC 在整個 branch 生命週期內保持穩定。

驗證裝置的 commit 是否在這個 branch 上:

```bash
cd ~/android14-6.1/common && git describe --tags $(adb shell uname -r | sed 's/.*-g\([0-9a-f]*\)-.*/\1/')
```

有輸出(例如 `android14-6.1-2024-10_r15`)就表示 branch 選對了。

## 1.4 寫第一個 module

```bash
mkdir -p ~/android14-6.1/hello
```

`~/android14-6.1/hello/hello.c`:

```c
// SPDX-License-Identifier: GPL-2.0
#include <linux/init.h>
#include <linux/module.h>

static int __init hello_init(void)
{
	pr_info("hello: module loaded\n");
	return 0;
}

static void __exit hello_exit(void)
{
	pr_info("hello: module unloaded\n");
}

module_init(hello_init);
module_exit(hello_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Alan Tseng");
MODULE_DESCRIPTION("Hello world driver practice for Pixel 8");
```

`MODULE_LICENSE("GPL")` 不是形式 — 少了它,module 會被標記為 proprietary,無法使用大量標記為 GPL-only 的 kernel 符號,編譯時就會出現 unknown symbol 錯誤。

## 1.5 Kleaf `ddk_module`

**不要手寫 `Kbuild`。** Kleaf 的 `ddk_module`(Driver Development Kit)會自動產生 Kbuild,手寫的那份不會被使用,只會造成混淆。

`~/android14-6.1/hello/BUILD.bazel`:

```python
# SPDX-License-Identifier: GPL-2.0
load(
    "//build/kernel/kleaf:kernel.bzl",
    "ddk_module",
)

ddk_module(
    name = "hello",
    srcs = ["hello.c"],
    out = "hello.ko",
    kernel_build = "//common:kernel_aarch64",
    visibility = ["//visibility:public"],
    deps = ["//common:all_headers_aarch64"],
)
```

兩個 label 的意義:

* `kernel_build = "//common:kernel_aarch64"` — 要編給哪一個 kernel。GKI aarch64 build。
* `deps = ["//common:all_headers_aarch64"]` — kernel header。少了它會找不到 `linux/module.h`。

**先驗證 target 能解析再編譯**,可以省下數十分鐘的錯誤等待:

```bash
cd ~/android14-6.1 && tools/bazel query '//hello:hello'
```

參考範例:`common-modules/wonder/BUILD.bazel` 是 tree 裡結構完整的 `ddk_module` 實例,包含 `kconfig`、`defconfig`、`conditional_srcs` 等進階用法。

## 1.6 編譯

```bash
cd ~/android14-6.1 && tools/bazel build //hello:hello
```

第一次要連 GKI kernel 一起編,約 2–3 分鐘(實測 145 秒)。**之後的增量編譯約 4 秒** — 這是快速路線最大的價值。

編譯尾端會出現這個錯誤,**可以忽略**:

```text
SSL error:02000002:system library:OPENSSL_internal:No such file or directory
sign-file: ./certs/signing_key.pem
```

意思是找不到簽章金鑰。因為裝置沒開 `CONFIG_MODULE_SIG_FORCE`,未簽章模組照樣載入(kernel 會被標記 taint,`lsmod` 顯示 `(OE)`)。
