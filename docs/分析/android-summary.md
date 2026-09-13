---
title: Android 知識整理摘要
sidebar_position: 1
---

# Android 知識整理摘要

> 本文整理自 TIL 知識庫中所有 Android / AOSP / Pixel 相關筆記，涵蓋從硬體到系統、從開發環境到 Root 的完整脈絡。

---

## 一、Android 平台架構

Android 的架構由下而上分為五層：

1. **Linux Kernel** — 硬體驅動、記憶體管理、電源管理
2. **HAL（Hardware Abstraction Layer）** — 硬體抽象層，屏蔽廠商差異
3. **Android Runtime（ART）** — 取代 Dalvik 的執行環境，支援 AOT 編譯
4. **Framework Layer** — AMS、PMS、WMS 等系統服務
5. **App Layer** — 使用者應用程式

參考：[Android 平台架構](https://developer.android.com/guide/platform?hl=zh-tw)

---

## 二、Android Boot Flow（開機流程）

Android 裝置從電源鍵到 Launcher 桌面，經歷以下完整流程：

```
Power On
   │
   ▼
Boot ROM (PBL)          ← 晶片內建，唯讀，SoC 廠商燒錄（< 16 KB）
   │
   ▼
Bootloader              ← ABL（高通 UEFI）/ LK / U-Boot
   │
   ▼
Linux Kernel            ← 核心初始化、掛載 rootfs
   │
   ▼
Init (PID 1)            ← 解析 init.rc，啟動 HAL / Vendor Services
   │
   ▼
Zygote (app_process)    ← 所有 App 的父程序，預載 Framework 類別
   │
   ▼
System Server           ← AMS / PMS / WMS 等核心系統服務
   │
   ▼
Launcher（Home Screen）
```

### 各階段要點

| 階段 | 關鍵工作 | 備註 |
|------|----------|------|
| Boot ROM (PBL) | 初始化 DRAM、Secure Boot 第一步 | 驗證失敗 → EDL 模式 |
| Bootloader | 驗證 kernel、選擇 A/B slot | fastboot 從此層操作 |
| Linux Kernel | 掛載 rootfs、啟動 init | 與標準 Linux 相同 |
| Init | 解析 `init.rc`、啟動 property service | PID = 1 |
| Zygote | fork 出所有 App 程序 | 加速啟動（預載 class） |
| System Server | 啟動 AMS/PMS/WMS | Java 程序，最重要的服務主機 |

---

## 三、AOSP 開發環境

### 硬體需求
- 作業系統：Ubuntu 20.04+
- 磁碟空間：300 GB+
- RAM：建議 16 GB+

### 環境安裝
```bash
sudo apt-get install git-core gnupg flex bison build-essential zip curl \
  zlib1g-dev libc6-dev-i386 x11proto-core-dev libx11-dev lib32z1-dev \
  libgl1-mesa-dev libxml2-utils xsltproc unzip fontconfig

# 安裝 repo 工具
mkdir -p ~/bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo
export PATH=~/bin:$PATH
```

### 取得原始碼
```bash
mkdir aosp && cd aosp
repo init --partial-clone -b android-latest-release \
  -u https://android.googlesource.com/platform/manifest
repo sync -c -j$(nproc)
```

目前使用的分支：`android16-qpr2-release`

### 編譯
```bash
source build/envsetup.sh
lunch aosp_shiba-userdebug    # Pixel 8 為 shiba
make -j$(nproc)
```

---

## 四、Pixel 8 硬體代號

| 代號 | 對應 |
|------|------|
| `zuma` | Google Tensor G3 SoC（晶片） |
| `shiba` | Pixel 8 裝置 |
| `ripcurrent` | Bootloader 版本前綴 |

核心分支：`android-gs-zuma-...`（gs = Google Silicon）

---

## 五、ADB 常用操作

```bash
# macOS 安裝
brew install android-platform-tools

# Ubuntu 安裝
sudo apt install -y android-tools-adb android-tools-fastboot

# 檢查連線
adb devices

# 安裝 APK
adb install app.apk

# 查詢 / 移除套件
adb shell pm list packages | grep 關鍵字
adb uninstall com.example.app

# 進入 shell
adb shell

# 進入 bootloader
adb reboot bootloader
```

### 開啟 USB 偵錯（Pixel）
設定 → 關於手機 → 連點「版本號」→ 開發人員選項 → 開啟 USB 偵錯

---

## 六、Fastboot 與刷機

### 解鎖 Bootloader
```bash
adb reboot bootloader
fastboot flashing unlock
```

### 刷入完整系統
```bash
fastboot flashall -w    # -w 會清除 userdata
```

Pixel 8 刷機時會寫入以下 partition：
- `boot_a` / `init_boot_a` / `dtbo_a`
- `vendor_boot_a` / `vendor_kernel_boot_a`
- `vbmeta_a` / `vbmeta_system_a` / `vbmeta_vendor_a`
- `system_a` / `system_ext_a` / `product_a` / `vendor_a`

### 線上刷機工具
- 官方 Flash Tool：https://flash.android.com/
- Factory Image 下載：https://developers.google.com/android/images

---

## 七、Root（取得 root 權限）

### 問題背景
```
adb root
→ adbd cannot run as root in production builds
```
正式 (production) build 無法直接使用 `adb root`，需透過 Root 工具。

### 兩種主流方案比較

| | Magisk | KernelSU |
|--|--------|----------|
| 執行層 | User-space | Kernel-space |
| 修改目標 | `init_boot.img`（Ramdisk） | `boot.img`（含 Kernel） |
| 特點 | 廣泛支援、社群豐富 | 更底層、適合 Kernel 開發者 |

### Magisk Root 步驟（Pixel 8）
```bash
# 1. 安裝 Magisk App
adb install Magisk_v30.7.apk

# 2. 用 Magisk App patch init_boot.img，取得 magisk_patched.img

# 3. 刷入 patched img
adb pull /sdcard/Download/magisk_patched-30700_uGZAZ.img ./
fastboot flash init_boot magisk_patched-30700_uGZAZ.img
fastboot reboot
```

---

## 八、SEPolicy

> 筆記尚在整理中，可參考 [Android SEPolicy 官方文件](https://source.android.com/docs/security/features/selinux)

---

## 九、學習資源

- [Android 平台架構](https://developer.android.com/guide/platform?hl=zh-tw)
- [AOSP 環境設定](https://source.android.com/docs/setup/start?hl=zh-tw)
- [Android Factory Images（Pixel）](https://developers.google.com/android/images)
- [KernelSU Root 教學](https://ivonblog.com/posts/kernelsu-android-root/)
- [Android Boot Process 詳解](https://www.linkedin.com/pulse/deep-dive-android-boot-process-step-by-step-breakdown-santilli-9cdbf/)

---

*最後更新：2026-04-08*
