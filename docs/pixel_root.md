# Pixel Root：Magisk vs KernelSU

Android 取得 root 權限主要有兩套方案，差別在**它跑在哪一層、因此要改哪一個 image**。

| | Magisk | KernelSU |
|---|---|---|
| 執行層級 | **User-space** | **Kernel-space** |
| 修改對象 | `init_boot.img` 裡的 ramdisk | `boot.img`（含 kernel 本體） |
| 需要自編 kernel | 否 | 是（或用官方預編的 GKI image） |
| 權限管理 | 攔截 `su` 呼叫，由 app 授權 | kernel 內建的 `su` 實作 + uid 白名單 |
| 隱藏能力 | Zygisk / DenyList | kernel 層，更難被偵測 |

**選哪個**：想練 kernel 編譯的話 KernelSU 契合度更高，因為它本來就要你動 `boot.img`；只是要 root 來用，Magisk 生態系（模組）成熟得多。

## 為什麼是這兩個不同的 image

Android 13 之後把 generic ramdisk 從 `boot.img` 拆出來，獨立成 `init_boot.img`：

- **`boot.img`** = kernel + （舊版才有的）ramdisk
- **`init_boot.img`** = generic ramdisk（裡面有 `init`、`first_stage_init`）

Magisk 的做法是**把 `init` 換成自己的版本**，在開機早期插入自己的邏輯，所以它要改的是放 ramdisk 的那個 image——在 Pixel 8 這種新裝置上就是 `init_boot.img`。

KernelSU 是**直接把 su 的實作編進 kernel**，所以要換的是含 kernel 的 `boot.img`。

各個 image 的來源與用途整理見 [Pixel image 對照](./pixel_img.md)。

## 前置作業：解鎖 bootloader

兩者都需要先解鎖 bootloader。**這會清除裝置上所有資料，先備份。**

1. 在「設定 → 關於手機」連點版本號 7 次啟用開發者選項。
2. 開發者選項裡打開 **OEM 解鎖** 與 **USB 偵錯**。
   - 如果 OEM 解鎖是灰的，通常是還沒連過網路啟用、或裝置是電信商鎖版。
3. 進 bootloader 並解鎖：

```bash
adb reboot bootloader
fastboot flashing unlock
# 在裝置螢幕上用音量鍵選 "Unlock the bootloader"，電源鍵確認
```

解鎖後開機會看到橘色的警告畫面（AVB boot state = orange），這是正常的。

## Magisk 流程

1. 取得**你目前這台裝置對應版本**的 factory image，解壓出 `init_boot.img`。版本一定要對得上，不然會開不了機。
2. 把 `init_boot.img` 傳到手機，裝上 Magisk APK，用 Magisk 的「安裝 → 選擇並修補一個檔案」產生 `magisk_patched-xxx.img`。
3. 把修補後的檔案拉回電腦並刷入：

```bash
adb pull /sdcard/Download/magisk_patched-xxxxx.img
adb reboot bootloader
fastboot flash init_boot magisk_patched-xxxxx.img
fastboot reboot
```

開機後 Magisk app 會顯示已安裝。

## KernelSU 流程

有兩條路：

- **用官方預編的 GKI image**（快）：從 KernelSU 的 release 頁面下載對應 kernel 版本的 `boot.img` 直接刷。要先確認自己的 kernel 版本：

  ```bash
  adb shell uname -r
  # 例如 6.1.xx-android14-11-...
  ```

- **自己編**（想練 kernel 就走這條）：把 KernelSU 掛進 kernel 樹編譯，產出的 `boot.img` 再刷進去。這條路的好處是順便熟悉整個 Android kernel 的建置流程，見 [AOSP 完整流程](./aosp_pixel_full_workflow.md)。

刷入：

```bash
adb reboot bootloader
fastboot flash boot boot-ksu.img
fastboot reboot
```

再安裝 KernelSU manager APK 即可管理權限。

## 注意事項

- **root 後部分 app 會拒絕執行**（銀行、行動支付、部分遊戲）——它們透過 Play Integrity API 檢查裝置完整性。Magisk 的 DenyList 或相關模組可以部分規避，但這是持續的貓捉老鼠。
- **OTA 更新會覆蓋掉修補過的 image**，更新後需要重新做一次。
- **刷錯版本的 image 會開不了機**，救援方式是重新刷回原廠 factory image（`flash-all.sh`）。
- userdebug 的自編 kernel 若沒處理好 dm-verity 會 boot loop，相關踩坑見 [flash-pixel-aosp 筆記](./pixel_fastboot_deepdive.md)。

## 參考

- [在 Android 手機安裝 KernelSU（Ivon's Blog）](https://ivonblog.com/posts/kernelsu-android-root/)
- [Magisk 官方 repo](https://github.com/topjohnwu/Magisk)
- [KernelSU 官方文件](https://kernelsu.org/)
