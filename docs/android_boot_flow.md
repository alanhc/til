---
title: Android Boot Flow
sidebar_position: 2
---

# Android Boot Flow（Android 開機流程）

Android 裝置從按下電源鍵到看見 Launcher 桌面，背後經歷了一連串複雜的啟動流程。本文整理完整的 Android Boot Flow，從最底層的硬體到最上層的應用框架。

## 整體流程概覽

```
Power On
   │
   ▼
Boot ROM (PBL)
   │
   ▼
Bootloader (ABL / LK / U-Boot)
   │
   ▼
Linux Kernel
   │
   ▼
Init (PID 1)
   │
   ├─► Early Init (tmpfs, /dev, /proc 掛載)
   ├─► Init.rc 解析與執行
   ├─► HAL / Vendor Services
   │
   ▼
Zygote (app_process)
   │
   ▼
System Server
   │
   ├─► Activity Manager Service (AMS)
   ├─► Package Manager Service (PMS)
   ├─► Window Manager Service (WMS)
   └─► ...其他系統服務
   │
   ▼
Launcher（Home Screen）
```

---

## 1. Power On & Boot ROM（PBL）

### 說明
當裝置電源開啟後，CPU 會從一個**固定的記憶體位址**開始執行程式碼，這段程式碼存放在晶片內部的 **Boot ROM（Primary Bootloader, PBL）**，是唯讀且無法被修改的。

### 主要工作
- 初始化基本硬體（時鐘、DRAM controller）
- 從儲存裝置（eMMC / UFS）載入下一階段的 Bootloader
- 進行基本的**安全驗證**（Secure Boot 第一步）

### 特點
- 大小極小，通常 < 16 KB
- 由 SoC 廠商（高通、聯發科、三星）燒錄，無法修改
- 若驗證失敗會進入 Emergency Download Mode（EDL）

---

## 2. Bootloader（ABL / LK / U-Boot）

### 說明
Bootloader 是介於韌體與作業系統之間的橋梁，Android 常見的 Bootloader 有：

| Bootloader | 廠商 | 說明 |
|---|---|---|
| **ABL (UEFI-based)** | 高通 | Android Boot Loader，現代高通平台使用 |
| **LK (Little Kernel)** | 高通（舊） | 曾廣泛用於 Android 裝置 |
| **U-Boot** | 開源 | 多用於 AOSP 開發板 |

### 主要工作
- 初始化 DRAM、顯示器、儲存裝置
- 載入並驗證 `boot.img`（包含 Linux Kernel + ramdisk）
- **Verified Boot（AVB）**：驗證 kernel 和 system partition 的簽章
- 決定開機模式：
  - 正常開機（Normal Boot）
  - Recovery Mode
  - Fastboot Mode

### A/B Partition（無縫更新）
現代 Android 裝置（Android 7.0+）採用 **A/B Slot** 機制：
- 系統有兩份 partition（`_a` 和 `_b`）
- OTA 更新寫入備用 Slot，成功後切換
- 失敗可自動 Rollback，提升更新安全性

---

## 3. Linux Kernel 初始化

### 說明
Bootloader 將 kernel 解壓縮並載入記憶體後，CPU 跳轉至 kernel 入口點執行。

### 主要工作
1. **架構初始化**：設置 CPU 模式、MMU（記憶體管理單元）、中斷向量表
2. **驅動程式初始化**：依序初始化各硬體驅動（GPIO、I2C、USB、Wi-Fi...）
3. **掛載 initramfs**：`init_boot.img` 內的 ramdisk 被掛載為根目錄
4. **啟動第一個 userspace 程式**：執行 `/init`（PID 1）

### Android 特有的 Kernel 元件
- **Binder**：Android IPC（程序間通訊）機制，高效能的 driver
- **Ashmem**：Android 共享記憶體機制（現代版本改用 memfd）
- **ION**：多媒體記憶體分配器
- **Wakelocks**：電源管理，防止系統進入休眠

---

## 4. Init（PID 1）

### 說明
`/init` 是 Android userspace 的第一個程式，其 PID 為 1。原始碼位於 `system/core/init/`。

### 啟動階段

#### Early Init
- 掛載 `tmpfs`、`devtmpfs`、`proc`、`sysfs`
- 設置 SELinux 策略（`/system/etc/selinux/`）
- 建立基本目錄（`/dev`, `/sys`, `/proc`）

#### Init.rc 解析
Android 使用 `.rc` 腳本（Android Init Language）來描述服務和啟動動作：

```rc
# 範例：啟動 surfaceflinger
service surfaceflinger /system/bin/surfaceflinger
    class core animation
    user system
    group graphics drmrpc readproc
    capabilities SYS_NICE
    onrestart restart zygote
```

**重要的 rc 檔案**：
- `init.rc` — 核心系統服務
- `init.{hardware}.rc` — 硬體平台相關（如 `init.qcom.rc`）
- `init.{ro.boot.hardware.platform}.rc` — SoC 平台相關

#### Vendor Init
- 啟動 HAL（Hardware Abstraction Layer）服務
- 初始化 `hwservicemanager`、`vndservicemanager`

---

## 5. Zygote

### 說明
Zygote（「受精卵」）是所有 Android App 程序的父程序，透過 **fork** 機制讓新 App 快速啟動。

### 啟動流程

```
init → app_process → ZygoteInit.java
         │
         ├─ 預載入常用 Java Classes（~1500+ 類別）
         ├─ 預載入 Resources（drawable、strings）
         └─ 開啟 Socket 等待連線 (/dev/socket/zygote)
```

### 為什麼用 fork？
- **Copy-on-Write（COW）**：fork 後子程序與父程序共享記憶體頁面
- 預載入的 classes 和 resources 不需重複載入
- App 啟動時間大幅縮短

### Zygote64 & Zygote32
現代 64-bit Android 裝置同時運行兩個 Zygote：
- `zygote64`：for 64-bit app
- `zygote32`：for 32-bit app（相容性）

---

## 6. System Server

### 說明
Zygote fork 出 **System Server**，這是 Android Framework 的核心程序，負責啟動所有系統服務。

### 關鍵系統服務

| 服務 | 功能 |
|---|---|
| **ActivityManagerService (AMS)** | 管理 Activity 生命週期、App 程序 |
| **PackageManagerService (PMS)** | 管理 APK 安裝、權限 |
| **WindowManagerService (WMS)** | 視窗管理、Surface 合成 |
| **PowerManagerService** | 電源管理、Wakelock |
| **InputManagerService** | 觸控、按鍵事件分發 |
| **TelephonyRegistry** | 電話狀態管理 |
| **ConnectivityService** | 網路管理 |

### 啟動完成通知
System Server 啟動完成後，AMS 會發送：
```
ACTION_BOOT_COMPLETED
```
此廣播代表系統已完全啟動，App 可以接收並執行開機自動啟動的任務。

---

## 7. Launcher（Home Screen）

System Server 的 AMS 啟動後，會呼叫 `startHomeActivity()` 啟動預設的 **Launcher App**，使用者看到桌面，開機流程完成。

---

## Boot Partition 結構（現代 Android）

```
┌─────────────────────────────────────────┐
│  boot_a / boot_b                        │  ← Kernel + generic ramdisk
├─────────────────────────────────────────┤
│  init_boot_a / init_boot_b              │  ← Generic Init ramdisk (Android 13+)
├─────────────────────────────────────────┤
│  vendor_boot_a / vendor_boot_b          │  ← Vendor ramdisk + DTB
├─────────────────────────────────────────┤
│  dtbo_a / dtbo_b                        │  ← Device Tree Blob Overlay
├─────────────────────────────────────────┤
│  vbmeta_a / vbmeta_b                    │  ← Verified Boot metadata
├─────────────────────────────────────────┤
│  system_a / system_b                    │  ← /system（Framework）
├─────────────────────────────────────────┤
│  vendor_a / vendor_b                    │  ← /vendor（HAL、驅動）
└─────────────────────────────────────────┘
```

---

## 常見除錯方法

### 查看開機 log
```bash
# 透過 ADB 查看 kernel log
adb shell dmesg | grep -i "boot\|init\|zygote"

# 查看 Android logcat（開機期間）
adb logcat -b all | grep -i "bootanim\|system_server\|zygote"

# 查看 bootloader log（部分裝置）
adb shell cat /proc/last_kmsg
```

### 常見開機失敗原因
| 現象 | 可能原因 |
|---|---|
| 卡在 Boot Logo | Kernel panic、驅動初始化失敗 |
| 卡在 Android 動畫 | System Server 崩潰、關鍵服務啟動失敗 |
| 卡在 Recovery | AVB 驗證失敗、system partition 損毀 |
| 快速重啟 | Init 重啟關鍵服務失敗超過閾值 |

---

## 參考資料

- [Android Platform Architecture](https://developer.android.com/guide/platform)
- [Booting process of Android devices - Wikipedia](https://en.wikipedia.org/wiki/Booting_process_of_Android_devices)
- [Android Verified Boot (AVB)](https://source.android.com/docs/security/features/verifiedboot)
- [Android Init Language](https://android.googlesource.com/platform/system/core/+/master/init/README.md)
- [Generic Boot Partition - Android 13](https://source.android.com/docs/core/architecture/partitions/generic-boot)
