# 從 hello world 到 Binder:一支 Android driver 的完整歷程

這份文件記錄在一台 Pixel 8 上,從零寫出一支 kernel driver 並逐步加上真實硬體驅動所需的每項機制的過程。

它和 [pixel8-kernel-tutorial.md](pixel8-kernel-tutorial.md) 的差別:

| | 手冊 | 這份 |
|---|---|---|
| 組織方式 | 按主題,方便查 | 按時間,照著走 |
| 內容 | 「怎麼做 X」 | 「為什麼是這個順序、當時錯在哪、怎麼發現的」 |
| 錯誤 | 整理成檢查清單 | 保留原始的診斷過程 |

**每一段輸出都是實機或 QEMU 跑出來的,不是示意。**

---

# 先看終點

最後那支 driver(約 1500 行)長這樣:

```text
/dev/hello0          64 bytes buffer     ┐ 兩個 instance,屬性來自各自的
/dev/hello1          256 bytes buffer    ┘ firmware node,狀態完全獨立

介面:
  read()             事件串流(阻塞 / O_NONBLOCK)
  write()            寫入訊息
  poll()             等事件
  mmap()             直接映射 DMA 頁面,取資料不進 kernel
  ioctl() × 12       結構化命令,含 dma-buf 匯出/匯入、非同步填充
  /sys/.../message   sysfs 屬性
  /sys/.../stats     內部狀態

底層:
  hrtimer(硬中斷)   → kfifo → workqueue → wait queue
  dma_alloc_coherent  → 唯讀共享頁面
  dma_buf             → 跨 driver / 跨 process 分享
  dma_fence           → 「什麼時候可以讀」
  runtime PM + suspend/resume
```

40 項自動測試,實機與開滿 lockdep 的 QEMU 都通過。

**但真正學到的東西不在這支 driver 裡**,而在這一路上每一個「以為對了但其實錯了」的地方。那些才是這份文件的重點。

---

# Part 1:先確認你不用刷機

## 1.1 兩個指令決定一切

```bash
adb shell getprop ro.build.type
```

```bash
adb shell "zcat /proc/config.gz | grep CONFIG_MODULE_SIG_FORCE"
```

看到 `userdebug` 且 `# CONFIG_MODULE_SIG_FORCE is not set`,就代表:

* 可以 `adb root`
* 未簽章的模組可以直接 `insmod`

**整個開發循環是 10 秒,不是 40 分鐘。** 大部分 Pixel kernel 教學一開頭就叫你解鎖 bootloader、同步 300GB、刷五個 partition —— 那是給沒有這兩個條件的人的。

實測本機:`AOSP_on_shiba`、Android 15、kernel `6.1.99-android14-11`。

## 1.2 只需要 GKI,不需要整棵 Pixel tree

branch 從 `uname -r` 讀:`6.1.99-android14-11` → GKI 世代是 `android14`、kernel 是 `6.1`。

```bash
repo init -u https://android.googlesource.com/kernel/manifest -b common-android14-6.1 --depth=1
```

```bash
repo sync -c --no-tags -j8
```

18G、約 15 分鐘。(完整 Pixel kernel tree 建議準備 250–300GB。)

## 1.3 版本不一致沒關係 —— 但要知道為什麼

同步下來是 6.1.175,裝置是 6.1.99。差 76 個小版本,模組照樣載入,因為:

1. `CONFIG_MODVERSIONS` 開啟時,kernel 的 `same_magic()` 會**跳過 vermagic 開頭的版本字串**,只比對符號 CRC
2. `android14-6.1` 的 KMI 已凍結,匯出符號的 CRC 在整個 branch 內穩定

這個「版本可以不同、CRC 不能不同」的規則,在 Part 10 會變成整件事的關鍵。

---

# Part 2:第一個模組

## 2.1 不要手寫 Kbuild

Kleaf 的 `ddk_module` 會自動產生 Kbuild。手寫的那份不會被使用,只會讓你困惑。

```python