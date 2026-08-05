# Pixel 8 軟體整合層 Bringup：boot 流程、device tree、vendor HAL

這份文件記錄在一台 Pixel 8(shiba)上,把「driver 能載入」推進到「裝置從 device tree 描述它」的過程,以及沿路把 boot 流程拆開驗證的結果。

和現有三份文件的關係:

| | 內容 |
|---|---|
| [pixel8-kernel-tutorial.md](pixel8-kernel-tutorial.md) | 怎麼寫、怎麼編、怎麼載一支 module |
| [pixel8-driver-course.md](pixel8-driver-course.md) | 那支 driver 是怎麼一步步長出來的 |
| [upstream-runbook.md](upstream-runbook.md) | 怎麼把 patch 送出去 |
| **這份** | **module 以外的東西**:分割區、ramdisk、cmdline、dtbo、device tree、vendor HAL、image 手術 |

前三份談的是 `.ko` 檔本身。這份談的是它周圍那一整套 —— 裝置怎麼開機、kernel 從哪裡拿到硬體描述、你的 driver 憑什麼被 probe。

## ⚠ 這裡的「bringup」指哪一半

「Bringup」在兩個圈子裡指的範圍差很多,這份文件只涵蓋其中一半。

**沒有涵蓋的 —— 傳統嵌入式的 board bringup**:拿到一塊剛回來的新板子,硬體是未知數,
要證明它能動。電源時序、時鐘樹、reset 線、DDR training、bootloader 移植、把 serial
console 弄出來、對著電路圖做 pinmux、用示波器和邏輯分析儀一支腳一支腳確認。

**這份涵蓋的 —— 軟體整合層**:硬體早就被 Google bring up 過了。這裡加的 `hello` 是一個
**不存在的裝置**,driver 背後沒有真實電路(用 hrtimer 假裝中斷)。工作集中在:硬體描述
(device tree)、開機流程、driver 的 probe 路徑、以及 Android 特有的 HAL / SELinux /
VINTF / image 打包。

真正重疊的部分是實在的:**device tree 本來就是 bringup 的核心工作之一**,開機流程的解剖
換板子時每次都要重來,kernel↔module 的 ABI 相容性(§4.7、§5.11)在跨版本移植天天遇到,
而「只有一行 `avc: denied` 或一個 errno 可用,要推斷根因」更是 bringup 的日常 —— 這份
文件裡好幾個問題都是這個形狀:EACCES 但沒有 denial(§5.7)、build 成功但產物是空的
(§5.3)、`.ko` 的 vermagic 對卻載不進去(§4.7)。

反過來,SELinux policy、Treble 的 vendor/system 分界、HAL over Binder、AVB/dm-verity、
dynamic partition 這些是 Android 特有的,跑一般 Linux 的嵌入式板子完全不需要。

手機廠內部講 "bringup" 時常常就是指這一半;做 SoC 的公司講 bringup 多半指前一半。
兩邊都沒用錯,是分工不同,完整的產品 bringup 兩半都要。

**要補上硬體那一半,Pixel 8 做不到** —— 它沒有外露的 GPIO/I2C、bootloader 封閉、
kernel config 被 GKI 凍結(§3)。**§7 是用 BeagleBone Black 補這一塊的計畫**,重點在
兩件這裡完全沒碰到的事:U-Boot SPL 裡開源可改的 DDR 初始化,以及用邏輯分析儀把
driver 的每一次 `i2c_transfer()` 對到線上的波形。

**驗證狀態**:每一段輸出都是實機或 build 實際跑出來的,不是示意。

* §1~4 boot 流程與 device tree —— 已刷入實機,DT node 上線,driver 由 DT probe。
* §5.1~5.8 vendor HAL —— 已在實機運作:由 init 自動啟動、向 servicemanager 註冊、
  通過 Binder 完成 dma-buf fd 跨 process 傳遞,且檔案在刷入的 `vendor.img` 內而非
  overlay。
* §5.9 module 自動載入 —— 已刷入,冷開機後 modprobe 自動載入,全鏈零手動步驟。
* §5.10 system_ext 版本 —— 已部署到實機並與 vendor 版並存;Treble 邊界在 build time
  (`unknown type`)與 runtime(`avc: denied`)兩面都有實據。
* §5.11 Cuttlefish 對照組 —— VM 已啟動,HAL 由原始碼建進 vendor.img 並自動註冊;
  但 VM 是 6.6 kernel,`hello.ko` 載不進去,所以只驗整合路徑不驗 ioctl。

---

# 0. 工具鏈在哪裡

不用另外安裝任何東西。做 bringup 需要的工具全部在 kernel tree 的 prebuilts 裡:

```bash
ls ~/android14-6.1/prebuilts/kernel-build-tools/linux-x86/bin/
```

```text
avbtool  dtc  lz4  mkbootimg  mkdtboimg  mkdtimg  ufdt_apply_overlay  ...
```

加上 `~/android14-6.1/tools/mkbootimg/` 底下的 `unpack_bootimg.py` / `mkbootimg.py` / `repack_bootimg.py`。

整份文件都假設有這個環境變數:

```bash
export KBT=~/android14-6.1/prebuilts/kernel-build-tools/linux-x86/bin
```

**這台機器沒有系統版的 `lz4`。** 這件事後面會咬人,見 §1.4。

---

# 1. Boot 流程解剖

## 1.1 有哪些分割區

```bash
adb shell 'ls -l /dev/block/by-name/ | grep -iE "dtbo|boot"'
```

```text
boot_a               -> /dev/block/sda13      boot_b               -> /dev/block/sda23
dtbo_a               -> /dev/block/sda17      dtbo_b               -> /dev/block/sda27
init_boot_a          -> /dev/block/sda14      init_boot_b          -> /dev/block/sda24
vendor_boot_a        -> /dev/block/sda15      vendor_boot_b        -> /dev/block/sda25
vendor_kernel_boot_a -> /dev/block/sda16      vendor_kernel_boot_b -> /dev/block/sda26
```

A/B 兩套。目前跑哪一套: