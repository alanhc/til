# Pixel 代號體系

Google Pixel 的開發文件裡會出現各種代號，容易混淆的關鍵是：**同一台手機同時有「SoC 代號」與「裝置代號」兩個名字，用在不同地方**。

| 代號類型 | 例子 | 指的是 | 什麼時候會看到 |
|---|---|---|---|
| **SoC 代號** | `zuma` | Google Tensor G3 晶片本身 | Kernel 分支、kernel 設定、SoC 層級的 driver |
| **裝置代號** | `shiba` | Pixel 8 這台手機 | `lunch` 目標、device tree、vendor blob、factory image 檔名 |

一顆 SoC 會被多台裝置共用，所以是一對多的關係：

```
zuma (Tensor G3)
├── shiba    → Pixel 8
└── husky    → Pixel 8 Pro
```

## Kernel 側：用 SoC 代號

Android kernel 的分支命名是 `android-gs-<soc>-<version>` 的形式，例如：

```
android-gs-zuma-6.1-android14
```

`gs` 代表 **Google Silicon**。因為 kernel 處理的是晶片層級的東西（CPU、記憶體控制器、GPU、各種 IP block），這些由 SoC 決定，同一顆 SoC 的裝置共用同一份 kernel 樹。

## AOSP 側：用裝置代號

編譯系統映像檔時要指定**裝置**代號，因為螢幕、相機模組、感測器配置這些是每台手機各自不同的：

```bash
source build/envsetup.sh
lunch aosp_shiba-userdebug
m
```

`lunch` 選定目標後，build system 才知道要載入哪一份 device tree（DTS）與哪些硬體抽象層（HAL）設定。選錯代號會編出跑不起來的 image。

`lunch` 目標的格式是 `<product>-<release>-<variant>`（新版）或 `<product>-<variant>`（舊版）：

| variant | 說明 |
|---|---|
| `user` | 出貨版本，不可 root、關閉 adb root |
| `userdebug` | 可 `adb root`、保留除錯工具，開發用的主力 |
| `eng` | 完整除錯，開機較慢、部分最佳化關閉 |

## 其他常見代號

| 裝置代號 | 機型 | SoC 代號 |
|---|---|---|
| `shiba` | Pixel 8 | `zuma` |
| `husky` | Pixel 8 Pro | `zuma` |
| `akita` | Pixel 8a | `zuma` |
| `ripcurrent` | Tensor 開發板 | — |

**查證方式**：Google 的 [factory image 頁面](https://developers.google.com/android/images) 每一列的下載連結裡就是裝置代號，是最可靠的對照來源。

也可以直接問裝置自己：

```bash
adb shell getprop ro.product.device      # 裝置代號，如 shiba
adb shell getprop ro.board.platform      # SoC 平台代號，如 zuma
adb shell getprop ro.build.id            # Build ID，如 BP4A.251205.006
```

Build ID 的解讀見 [Android Build Number](./Android_build_number.md)。

## 相關筆記

- [AOSP Pixel 完整流程](./aosp_pixel_full_workflow.md)
- [Pixel image 對照](./pixel_img.md)
- [Pixel Root：Magisk vs KernelSU](./pixel_root.md)
