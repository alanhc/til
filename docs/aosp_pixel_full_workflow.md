---
title: AOSP 完整工作流程：從 repo init、repo sync 到燒錄進 Pixel 手機
sidebar_position: 1
---

# AOSP 完整工作流程：從 repo init、repo sync 到燒錄進 Pixel 手機

本篇記錄從零開始下載 AOSP 原始碼、編譯，一路到用 `fastboot` 燒錄進 Pixel 8（代號 `shiba`）的完整流程，以及常見錯誤與救磚方法。

:::tip 我的機器版本
本機 Pixel 8（`shiba`）目前系統版本為 **BP4A.251205.006**，對應 **Android 16 QPR2**（2025 年 12 月 2 日釋出）。  
Build ID 格式解析：`B`(Baklava=Android 16) `P`(Support Vertical) `4A`(Branch) `.251205`(分支日期 2025/12/05) `.006`(patch 序號)
:::

---

## 1. 環境準備

### 硬體需求

- **主機**：Ubuntu 22.04 / 24.04 LTS（x86_64），建議 RAM ≥ 32 GB、硬碟空間 ≥ 300 GB
- **手機**：Pixel 8（`shiba`）或 Pixel 8 Pro（`husky`）

### 安裝系統套件

```bash
sudo apt-get update
sudo apt-get install -y \
  git-core gnupg flex bison build-essential zip curl \
  zlib1g-dev gcc-multilib g++-multilib libc6-dev-i386 \
  libncurses5 lib32ncurses5-dev x11proto-core-dev libx11-dev \
  lib32z1-dev libgl1-mesa-dev libxml2-utils xsltproc unzip fontconfig
```

### 安裝 `repo` 工具

```bash
mkdir -p ~/bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo
export PATH=~/bin:$PATH
```

建議將 `export PATH=~/bin:$PATH` 加到 `~/.bashrc` 或 `~/.zshrc` 中，避免每次重新設定。

### 安裝 ADB / fastboot

```bash
sudo apt install -y android-tools-adb android-tools-fastboot
# 確認版本
adb version
fastboot --version
```

---

## 2. 下載 AOSP 原始碼

### 建立工作目錄

```bash
mkdir -p ~/aosp && cd ~/aosp
```

### `repo init`

以下指令使用 `--partial-clone` 加速下載，並指定 `--no-use-superproject` 避免部分機器上的網路問題：

```bash
repo init \
  --partial-clone \
  --no-use-superproject \
  -b android-latest-release \
  -u https://android.googlesource.com/platform/manifest
```

執行完會看到：

```
repo has been initialized in /home/alanhc/aosp
```

目錄結構會多出 `.repo/`：

```
.repo/
├── manifest.xml
├── manifests/
├── manifests.git/
└── repo/
```

> **針對 BP4A.251205.006（Android 16 QPR2）**：使用 `android-latest-release` 即可（2026 年 4 月 AOSP 已推送此版本的原始碼）。若要精確 pin 住特定 tag，請至 [source.android.com/docs/setup/reference/build-numbers](https://source.android.com/docs/setup/reference/build-numbers) 查詢 `BP4A.251205.006` 對應的 `android-16.0.0_r*` tag，再改用：
> ```bash
> repo init -u https://android.googlesource.com/platform/manifest -b android-16.0.0_rXX
> ```
> 其中 `XX` 為查表得到的號碼。
>
> **Android 14 舊版範例**（`ap1a.240305.019`）：
> ```bash
> repo init -u https://android.googlesource.com/platform/manifest -b android-14.0.0_r17
> ```

### `repo sync`

```bash
repo sync -c -j8 2>&1 | tee -a repo_sync.log
```

- `-c`：只 sync 目前 branch，節省空間
- `-j8`：8 個並行執行緒（**建議不要用 `$(nproc)` 全開**，容易遇到 fetch error）
- `tee -a repo_sync.log`：同時輸出到 log 檔方便事後查錯

完成後看到：

```
repo sync has finished successfully.
```

整個過程視網路狀況約需 30～90 分鐘。若中途遇到錯誤，可重跑指令，`repo sync` 支援斷點續傳。

> **AI 輔助除錯**：sync 過程若遇到奇怪的 fetch error，可以貼 log 給 Gemini CLI 或 Claude 幫忙分析。

---

## 3. 下載 Vendor Proprietary Drivers

Google 的閉源驅動（Baseband、Vendor image 等）需另外從官方下載，放進 AOSP 目錄才能成功編譯 Pixel 版本。

前往：  
**https://developers.google.com/android/drivers**（正式版，依裝置 + Build ID 查詢）

**針對 BP4A.251205.006（Android 16 QPR2）**，在該頁面搜尋 `shiba` + `BP4A.251205.006`，取得對應的下載連結（URL 格式如下），SHA-256 以頁面上的為準：

```bash
cd ~/aosp
# 將下方 URL 的 <HASH> 換成頁面上標示的實際 checksum 前段
wget https://dl.google.com/dl/android/aosp/google_devices-shiba-bp4a.251205.006-<HASH>.tgz
tar -xzf google_devices-shiba-bp4a.251205.006-*.tgz
# 執行解壓腳本（需同意授權協議，輸入 'I ACCEPT' 即可）
./extract-google_devices-shiba.sh
```

> **Android 14 AP1A 舊版範例**（僅供參考，請務必下載與自己 Build ID 相符的版本）：
> ```bash
> wget https://dl.google.com/dl/android/aosp/google_devices-shiba-uq1a.231205.015-9a0b48c0.tgz
> ```

成功後會在 `vendor/google_devices/shiba/` 產出以下內容：

```
vendor/google_devices/shiba/proprietary/
├── bootloader.img
├── radio.img
├── vendor.img
├── vendor_dlkm.img
├── vbmeta_vendor.img
├── device-vendor.mk
├── Android.bp / Android.mk
└── ...（其他 .so 與 .apk）
```

---

## 4. 設定 Build 環境與選擇目標

```bash
cd ~/aosp
source build/envsetup.sh
```

接著執行 `lunch` 選擇編譯目標。對 Pixel 8（`shiba`）使用 userdebug variant：

```bash
lunch aosp_shiba-trunk_staging-userdebug
```

成功後會輸出當前 build 設定（Android 16 版本範例）：

```
============================================
PLATFORM_VERSION_CODENAME=REL
PLATFORM_VERSION=16
TARGET_PRODUCT=aosp_shiba
TARGET_BUILD_VARIANT=userdebug
TARGET_ARCH=arm64
HOST_OS=linux
BUILD_ID=BP4A.251205.006
OUT_DIR=out
============================================
```

> **Pixel 8 Pro（husky）** 的 lunch target 為 `aosp_husky-trunk_staging-userdebug`。  
> **16 KB page size 支援**（Android 16 新功能）：Pixel 8 亦可選擇 `aosp_shiba_pgagnostic-trunk_staging-userdebug`，但一般開發用 `aosp_shiba-trunk_staging-userdebug` 即可。

---

## 5. 編譯

```bash
m
```

`m` 等同 `make`，會自動偵測 CPU 核心數。首次編譯視硬體需要 1～3 小時：

```
#### build completed successfully (01:03:22 (hh:mm:ss)) ####
```

編譯產物位於：

```bash
echo $PRODUCT_OUT
# out/target/product/shiba
```

---

## 6. 連接 Pixel 手機（ADB 設定）

### 手機端設定

1. **設定 → 關於手機 → 連點「版本號」7 下**，開啟開發人員選項
2. **開發人員選項 → 打開「USB 偵錯」**
3. **開發人員選項 → 打開「OEM 解鎖」**（第一次燒錄 AOSP 必須）
4. 用 USB 線接到電腦，手機跳出授權視窗選「允許」

### 主機端確認連線

```bash
adb devices
# List of devices attached
# 38011FDJH00C9F  device
```

狀態是 `device` 代表連線成功；`unauthorized` 代表手機還沒授權，點選手機的允許即可。

### 常見問題：unauthorized 無法解決

```bash
# 清除舊有金鑰並重啟 daemon
rm -f ~/.android/adbkey ~/.android/adbkey.pub
adb kill-server
adb start-server
adb devices
```

---

## 7. 進入 Bootloader 並燒錄

### 進入 fastboot 模式

```bash
adb reboot bootloader
```

手機螢幕會進入黑底的 fastboot 介面。確認 fastboot 有看到裝置：

```bash
fastboot devices
# 38011FDJH00C9F   fastboot
```

### 解鎖 Bootloader（第一次必做，會清除資料）

```bash
fastboot flashing unlock
```

手機螢幕會出現確認畫面，用音量鍵選「Unlock the bootloader」後按電源鍵確認。

### 燒錄所有分區

```bash
cd ~/aosp
source build/envsetup.sh
lunch aosp_shiba-trunk_staging-userdebug   # 或你選的 target
cd "$(get_build_var PRODUCT_OUT)"
fastboot flashall -w
```

`-w` 代表同時清除 userdata（相當於恢復出廠設定）。完整輸出範例：

```
--------------------------------------------
Bootloader Version...: ripcurrent-16.4-14097582
Baseband Version.....: g5300i-250909-251024-B-14326967
Serial Number........: 38011FDJH00C9F
--------------------------------------------
Checking 'product'                                 OKAY [  0.000s]
Setting current slot to 'a'                        OKAY [  0.074s]
Sending 'boot_a' (65536 KB)                        OKAY [  1.596s]
Writing 'boot_a'                                   OKAY [  0.099s]
...（中間略）
Sending sparse 'super' 9/9 (211236 KB)             OKAY [  5.163s]
Writing 'super'                                    OKAY [  0.333s]
Rebooting                                          OKAY [  0.000s]
Finished. Total time: 65.786s
```

燒錄完成後手機會自動重開機，進入剛才編譯的 AOSP 系統。

---

## 8. 常見錯誤排解

### 錯誤：`image (bl1_a): rejected, anti-rollback`

```
(bootloader) image (bl1_a): rejected, anti-rollback
FAILED (remote: 'failed to flash partition (bootloader_a): -7')
```

**原因**：試圖刷入比目前 bootloader 版本更舊的 bootloader，反回滾機制擋下。  
**解法**：下載與目前 bootloader 版本相符（或更新）的官方 factory image 來刷。

### 錯誤：`Device version-bootloader is X. Update requires Y.`

```
Device version-bootloader is 'ripcurrent-16.4-14097582'.
Update requires 'ripcurrent-14.4-11322024'.
fastboot: error: requirements not met!
```

**原因**：factory image 的版本比目前 bootloader 舊。  
**解法**：到 [https://developers.google.com/android/images](https://developers.google.com/android/images) 下載**最新版**或與目前 bootloader 版本相符的 factory image。

### 燒錄後無法開機（變磚）

按住 **電源 + 音量下鍵** 強制進入 fastboot，然後用官方 factory image 救回：

```bash
# 1. 到 https://developers.google.com/android/images 下載對應機型的 factory image
# 2. 解壓縮
cd ~/shiba-bp4a.260205.001
# 3. 執行官方燒錄腳本
./flash-all.sh
```

成功輸出的最後幾行：

```
Rebooting                                          OKAY [  0.000s]
Finished. Total time: 189.060s
```

這樣就救回來了。

---

## 9. 重新 sync 並重新燒錄的快速流程

之後要更新 AOSP 並重燒，只需：

```bash
# 1. 更新原始碼
cd ~/aosp
repo sync -c -j8 2>&1 | tee repo_sync.log

# 2. 重新編譯
source build/envsetup.sh
lunch aosp_shiba-trunk_staging-userdebug
m

# 3. 燒錄
adb reboot bootloader
cd "$(get_build_var PRODUCT_OUT)"
fastboot flashall -w
```

---

## 10. 補充：停用 AVB 並以 R/W 模式 Remount

如果需要修改系統分區（例如推 `.so` 到 `/system`），需要先停用 AVB：

```bash
fastboot -w --disable-verity --disable-verification flashall
```

燒錄完畢後，在 adb shell 中 remount：

```bash
adb root
adb remount
```

---

## 參考資料

- [AOSP 官方建置指南](https://source.android.com/docs/setup/start?hl=zh-tw)
- [AOSP Build Numbers & Tags 對照表](https://source.android.com/docs/setup/reference/build-numbers)（查 BP4A.251205.006 對應的 `android-16.0.0_rXX` tag）
- [Google Pixel Factory Images](https://developers.google.com/android/images)
- [Google Pixel Vendor Drivers](https://developers.google.com/android/drivers)（下載 shiba + BP4A.251205.006 的 proprietary blobs）
- [Android 16 QPR2 Factory Images](https://developer.android.com/about/versions/16/qpr2/download)
- [LineageOS Pixel 8 Build Guide](https://wiki.lineageos.org/devices/shiba/build/)
