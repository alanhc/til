# adb（Android Debug Bridge）

adb 是 Android SDK Platform Tools 提供的命令列工具，用來與裝置或模擬器溝通。

## 常用指令
```bash
adb devices                 # 列出已連線裝置
adb shell                   # 進入裝置 shell
adb shell <command>         # 執行單一指令
adb logcat                  # 檢視系統 log
adb logcat -s MyTag         # 只看指定 tag
adb push <local> <remote>   # 電腦 → 裝置 傳檔
adb pull <remote> <local>   # 裝置 → 電腦 傳檔
adb install app.apk         # 安裝 APK（-r 覆蓋安裝）
adb uninstall <package>     # 移除套件
adb reboot                  # 重開機
adb reboot bootloader       # 重開進 bootloader/fastboot
adb reboot recovery         # 重開進 recovery
```

## 小技巧
- 多裝置時用 `adb -s <serial> <command>` 指定目標。
- `adb root` / `adb remount` 需在可 root 的 build（如 userdebug/eng）上使用。
- `adb tcpip 5555` 後 `adb connect <ip>:5555` 可做無線除錯。
