## 名詞
adb

## Hardware
pixel8

## ADB
brew install android-platform-tools
adb version
Android Debug Bridge version 1.0.41
Version 36.0.2-14143358
Installed as /opt/homebrew/bin/adb
Running on Darwin 25.2.0 (arm64)

## 開發人員模式
- 手機 → 設定 → 關於手機 → 連點「版本號」開啟 **開發人員選項**
- 開發人員選項 → 打開 **USB 偵錯 (USB debugging)**
- 用 USB 線接到 Mac（第一次會跳出授權視窗，選「允許」）

adb devices
List of devices attached
38011FDJH00C9F	device


adb install AnTuTu\ AI\ Benchmark.apk 
Performing Streamed Install
Success

## 刪除
adb shell pm list packages | grep 關鍵字
adb uninstall com.example.app

