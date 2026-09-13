# 從 `mount -o remount` 到 OverlayFS：Android Driver 開發者必須弄懂的 remount 機制

> 適合對象：做 BSP、kernel module、vendor HAL、firmware 整合的系統工程師。假設你已經知道 AOSP build 流程、fastboot、以及 Linux mount 的基本語意。

---

## 一、問題的起點：為什麼「改一個檔案」在 Android 上這麼貴

在一般 Linux 開發機上，改一個 driver 的流程是：`make modules` → `cp foo.ko /lib/modules/...` → `rmmod && insmod` → 看 dmesg。整個 loop 十秒鐘。

在 Android 裝置上，同一件事的預設路徑是：改 code → `m` 或 `mmm` → 產出 `vendor.img`（甚至整包 `super.img`）→ `fastboot flashall` → 開機 → 重新佈置測試環境 → 重現問題。一輪五到十五分鐘，而且很多時候會把你辛苦重現出來的現場狀態（充放電狀態、sensor calibration、modem 註冊狀態、某個只在跑了三小時後才出現的 race）整個洗掉。

`adb remount` 存在的唯一理由，就是把第二種流程壓回第一種。它是系統層開發者迭代速度的槓桿，而不是一個「把手機變成可寫」的 hack 小技巧。

但要正確使用它、並且知道它什麼時候會騙你，你必須理解 Android 為什麼一開始要把這些分區鎖成唯讀——那背後疊了三層彼此獨立的約束。

---

## 二、第一層理解：Linux 的 remount 到底做了什麼

`mount -o remount,rw /vendor` 這個操作，在 VFS 層的語意是「不卸載、不重新建立 mount point，只修改既有 superblock 的 mount flags」。

這個區別很重要。正常的 `umount` + `mount` 需要該檔案系統上沒有任何開啟中的檔案描述子、沒有任何 process 的 cwd 在裡面。對 `/system` 或 `/vendor` 而言這永遠不可能滿足——`init`、`vold`、每一個 HAL service 都在跑。所以 remount 是唯一可行的路徑：它在原地翻轉 `MS_RDONLY` flag，正在執行的 process 完全無感。

在 Android 4.x/5.x 的年代，事情就到此為止。`/system` 是一塊實體分區、格式是可寫的 ext4、也還沒有 verified boot，`adb remount` 真的就只是幫你對每個唯讀掛載點跑一次 `mount -o remount,rw`。

之後十年裡，三件事讓這個天真的模型徹底失效。

---

## 三、第二層理解：三道把分區鎖死的約束

### 3.1 dm-verity / AVB —— 完整性驗證

Verified Boot 的核心是 dm-verity：`/system`、`/vendor` 這些分區被建成一棵 Merkle hash tree，root hash 存在 `vbmeta` 裡並由 bootloader 用金鑰驗簽。kernel 透過 device-mapper 把分區包成一個 `dm-verity` 裝置，**每一次 block 讀取都會即時驗 hash**。

這意味著：即使你成功把分區 remount 成 rw 並寫了一個位元組進去，下一次讀到那個 block 時 dm-verity 會發現 hash 對不上，然後依 `verity mode` 設定直接 panic 或把整個裝置踢進 restart-bootloader。

換句話說，verity 沒關掉的情況下，remount 成功 = 稍後必炸。這就是為什麼標準流程一定是 `disable-verity` 先行、而且必須重開機才生效（bootloader 要在下一次開機時看到那個 flag，才會用不帶 verity 的方式建立 dm 裝置）。

現代裝置上這件事又分兩層：`adb disable-verity` 處理的是 dm-verity 本身；而 AVB 的 vbmeta 驗證則可能還要另外靠 `adb shell avbctl disable-verification`，或是在刷機時用 `fastboot --disable-verity --disable-verification flash vbmeta ...`。哪一種有效取決於你的 BSP 怎麼配置，這也是新手在別人家的板子上最常卡住的地方。

### 3.2 Dynamic Partitions —— 沒有可用的剩餘空間

從 Android 10 開始，`/system`、`/vendor`、`/product`、`/system_ext`、`/odm`、`/vendor_dlkm` 不再是實體分區，而是 `super` 這塊實體分區裡由 LP metadata 描述的 **logical partition**。

伴隨而來的是 right-sizing：build 系統會把每個 image 縮到剛好裝得下內容的大小，好把省下來的空間還給 `super` 的動態配置池。結果是 `/vendor` 的檔案系統上**幾乎沒有 free space**。你 remount 成功了，但 `cp` 一個 2MB 的 `.so` 進去會直接 `ENOSPC`。

### 3.3 EROFS / 壓縮唯讀檔案系統 —— 根本不可寫

再往後，為了省空間與提升讀取效能，許多裝置把唯讀分區改用 **EROFS**（Enhanced Read-Only File System），並在 block 層做去重（shared blocks）。

EROFS 在設計上就沒有寫入路徑。`mount -o remount,rw` 對它不是「被禁止」，而是**語意上不存在**。就算 verity 關了、空間夠了，你也寫不進去。而 shared blocks 更糟：多個檔案共用同一批 block，就算真的能寫，改一個檔案會連帶改到另一個毫不相干的檔案。

---

## 四、Google 的解法：把 remount 重新定義成 OverlayFS

面對這三道牆，AOSP 沒有選擇讓分區變回可寫，而是換掉了 `adb remount` 的實作。從 Android 10 起，`fs_mgr` 裡多了一套 overlayfs 整合邏輯（`system/core/fs_mgr/fs_mgr_overlayfs.cpp`，官方說明在 `README.overlayfs.md`）。

新的語意是：

- **lower layer**：原本的唯讀分區（ext4 + verity，或 EROFS），保持不動。
- **upper layer**：一塊實際可寫的 backing storage。
- 兩者用 overlayfs 疊起來掛在原本的掛載點上。

你 `adb push` 一個檔案到 `/vendor/lib/modules/foo.ko`，實際寫入的是 upper layer；讀取時 overlayfs 把 upper 蓋在 lower 上合併呈現，於是系統「看起來」就像 `/vendor` 被改了。底層的 EROFS image 一個位元組都沒動，verity hash 也就沒有被破壞的問題（前提還是要關 verity，因為 fs_mgr 需要在早期就介入建立 overlay）。

**最關鍵的認知轉變**：`adb remount` 之後你看到的檔案系統，已經不是出廠 image 的檔案系統了，而是一個「出廠 image + 你的 diff」的合成視圖。這個區別會在後面的踩坑清單裡反覆咬人。

### 4.1 Backing storage 放在哪裡

fs_mgr 會依裝置形態自動挑選，你不需要指定，但你必須知道它在哪，因為除錯時要去確認：

| 裝置形態 | Backing storage 位置 |
|---|---|
| 非 A/B 裝置 | `/cache/overlay/` |
| A/B 裝置（可用 LRAP） | `/mnt/scratch/overlay`，來自 `super` 裡動態建立的 `scratch` logical partition |
| A/B 裝置（retrofit dynamic partition） | 直接徵用另一個 slot，例如跑在 `_a` 就吃掉整個 `system_b` |

因此 `scratch` 是保留名稱，你的 BSP 不能拿去命名別的分區。另外注意最後一種情況相當暴力：**另一個 slot 的 metadata 與內容會被清掉**，之後想切回去 `_b` 開機是不行的。

值得注意的是，AOSP 明確做了一個架構決定：**不使用 `/data/overlay/`**，即使 userdata 空間幾乎無限。這是為了讓 overlay 能在開機極早期就掛上（`/data` 那時還沒掛、還可能是加密的）。代價就是 backing storage 的空間很緊，這是設計上的取捨而非疏忽。

### 4.2 為什麼「早期掛載」很重要

fs_mgr 會盡可能早地掛上 overlay——可以早到 **first stage init**，或是在 init rc 執行 `mount_all` 的時候。

這對 driver 開發者有直接意義：因為掛得夠早，你 push 進去的 **vendor SELinux policy、`init.*.rc`、以及 `/vendor/lib/modules` 底下的 `.ko`** 才能在 init 的各個 exec 階段之前就生效。如果 overlay 是等到系統跑起來才掛，這些東西全都來不及。

反過來說，這也劃出了一條硬邊界（見第七節）：**ramdisk 與 first stage init 本身無法被 overlay 覆蓋**。

---

## 五、實務流程

### 5.1 標準流程

```bash
adb root                    # 需要 userdebug / eng build
adb disable-verity          # 需要 bootloader unlocked
adb reboot
adb wait-for-device
adb root
adb remount
```

之後可以：

```bash
adb push out/target/product/<device>/vendor/lib/modules/foo.ko /vendor/lib/modules/
adb reboot
```

或整包同步：

```bash
adb shell stop
adb sync
adb shell start
```

### 5.2 快捷寫法

前兩步可以合併成一行：

```bash
adb remount -R
```

`-R` 會在需要時自動關 verity 並重開機；如果裝置**已經**處在 remount 狀態，它不會多此一舉重開機。日常腳本裡用這個比較乾淨。

### 5.3 確認它真的生效了

這步不能省。AOSP 文件自己都寫了：「backing storage 在遇到錯誤時會被丟棄或忽略，這會造成困惑；使用 adb remount 除錯時，建議重開機後確認更新確實還在。」

```bash
adb shell mount | grep -i overlay        # 看 overlay 有沒有掛上、掛在哪些點
adb shell df -h /mnt/scratch             # 看 backing storage 還剩多少
adb shell ls -l /vendor/lib/modules/     # 直接確認檔案的 timestamp / size
adb shell dmesg | grep -i overlayfs      # 掛載失敗的線索通常在這
```

養成「push 完 → reboot → 再確認一次檔案還在」的習慣。debug 一個其實根本沒被載入的新版 driver，是這個機制最常見也最浪費時間的失敗模式。

---

## 六、對 driver 開發到底省了什麼

把它拆開來看會更清楚價值在哪。以下都是 remount 之後可以秒級迭代的東西：

**Kernel modules（`/vendor/lib/modules/*.ko`、`vendor_dlkm`）**
改一行 `pr_debug`、調一個 timeout、加一段 tracepoint，push 完 `rmmod`/`insmod` 或重開機就能驗。搭配 `modules.load` 的順序調整、或臨時把某個 module 從載入清單拿掉來做二分法定位，都不用重新出 image。

**Vendor HAL（`/vendor/lib64/hw/*.so`、`/vendor/bin/hw/*`）**
HAL 跟 driver 的介面問題（IOCTL 參數、buffer 生命週期、HIDL/AIDL 行為）往往要兩邊一起試。remount 之後可以只 push 一邊，`adb shell setprop ctl.restart vendor.foo-hal-default` 重啟該 service，framework 完全不用動。

**Firmware blobs（`/vendor/firmware/`）**
做 firmware 版本的 A/B 比對——換一顆 blob、重開、看行為差異——這是 remount 最有價值的場景之一，因為 firmware 檔案通常很大，重新出 image 特別慢。

**`init.*.rc` 與 device-specific 設定**
調整 service 的啟動順序、`on boot` 觸發時機、`chown/chmod` 給 sysfs 節點的權限。這類問題本質上就是「試一次改一次」，沒有 remount 幾乎無法工作。

**Vendor SELinux policy（`/vendor/etc/selinux/`）**
新增一個 sysfs 節點或 device node，幾乎必然伴隨一輪 avc denial 的修補。push policy → reboot → 看 `dmesg | grep avc`，這個 loop 一天可能要跑二十次。

**各種 config / calibration 檔**
sensor 校正參數、display panel timing、thermal profile。這些檔案改動頻繁但體積小，最適合 overlay。

真正的價值不只是「快」，而是**不破壞現場**。很多硬體問題只在特定溫度、特定電量、跑了幾小時之後、或某個週邊處於某個狀態時才重現。能在不重刷、不清 data 的前提下換掉一個 module 再看一次，跟每次都要從頭重現，是完全不同量級的除錯能力。

---

## 七、你必須知道的邊界與踩坑

這一節是這篇文章真正的重點。以下每一條都對應到實際會浪費你半天的狀況。

### 7.1 first stage init 與 ramdisk 無法被覆蓋

**這是 driver 開發者最容易踩的坑。** 如果你的 module 是在 first stage init 從 ramdisk（`vendor_boot` 裡的 `lib/modules`）載入的——很多早期必要的 driver 都是，例如 storage、PMIC、clock、pinctrl——那麼 `adb remount` 對它完全無效。你 push 到 `/vendor/lib/modules` 的新版本根本不會被讀到，而你會困惑地看著一模一樣的 log。

這種 module 只能靠 `fastboot flash vendor_boot`（或 `boot`）處理。**在開始 debug 前先確認你的 module 是從哪裡載入的**：檢查 `vendor_boot` ramdisk 裡的 `modules.load`，以及 `/vendor/lib/modules/modules.load`。

同理，kernel image 本身、ramdisk、bootloader 都不在 overlay 的覆蓋範圍內。

### 7.2 只能覆蓋子目錄，不能覆蓋整個分區

fs_mgr 刻意只對分區底下的子目錄建立 overlay。用 overlayfs 蓋掉整個分區會導致裝置無法開機。這也代表某些位於分區根目錄的檔案是動不了的。

### 7.3 空間會用完，而且用完的方式很難看

backing storage 是 **file-by-file 複製**（overlayfs 的 copy-up 語意）。你改了一個 40MB `.so` 裡的一行，upper layer 就會多出完整的 40MB。scratch 分區並不大，push 幾輪之後就可能塞爆。

更麻煩的連鎖反應：`scratch` 佔用了 `super` 的空間，之後如果 OTA 或某個操作要把某個 logical partition 變大，可能會**因為 scratch 的存在而失敗**。解法是清掉 backing storage：

```bash
adb enable-verity            # 會釋放 overlay 並還原到修改前的狀態
# 或
fastboot flashall
```

然後重新佈署你的覆蓋內容。

### 7.4 空間門檻是硬編碼的

fs_mgr 是「探測檔案系統型態與剩餘空間」後**自動決定**用傳統 remount 還是 overlayfs。門檻寫死在程式碼裡：大致上如果分區還剩 1% 以上空間，它就不會啟用 overlayfs，而是走傳統直接 remount——但那點空間對實際開發往往根本不夠。

實務影響是：**同一套指令在不同板子、不同 build 上可能走到不同路徑**，行為不一致。這就是為什麼 5.3 節的驗證步驟不能省——先看清楚你這台裝置到底走的是哪條路。

### 7.5 remount 過的裝置不能吃 OTA

`fs_mgr_overlayfs_is_setup()` 回傳 true 時，update_engine 會拒絕運作。而 `adb enable-verity` 解除 overlay 之後，update engine 會執行**完整 OTA**（而非增量）。

如果你的測試流程涉及 OTA 驗證，remount 過的裝置必須先清乾淨。這兩件事在同一台機器上不能並存。

### 7.6 bootloader fastboot 刷機不會被偵測到

用 bootloader 的 fastboot（相對於 userspace 的 `fastbootd`）刷某個分區時，fs_mgr 偵測不到這件事，於是**舊的 overlay 內容會繼續留著蓋在新刷的分區上**。

這會製造出極其詭異的症狀：你明明刷了新 image，行為卻還是舊的。刷完之後養成 `adb enable-verity` 清一次的習慣。

### 7.7 backing storage 是「脆弱」的，且不保證通知你

AOSP 文件的原話是：backing storage 被視為 fragile，只要有其他東西需要那塊空間，它就會被清掉，而且**保留不通知你的權利**。

所以：**永遠不要把唯一一份修改放在 overlay 上。** 你的 patch 應該在 git 裡，overlay 只是一個暫時的部署快取。

### 7.8 kernel 需求

`CONFIG_OVERLAY_FS=y` 是必要條件。此外 4.4 以上的 kernel 需要 android-common 的 patch（`override_creds` mount option，用來處理 Android 嚴格的 SELinux least-privilege 模型與 overlayfs 預設行為的衝突），4.19 以上還額外需要 xattr recursion 的處理。用主線 kernel 自組的板子，這裡很容易出問題，症狀通常是 overlay 掛不上、或掛上了但 SELinux context 全錯。

### 7.9 remount 不解決的事情

最後釐清一件常見誤解：`adb remount` 只負責讓檔案「寫得進去」。以下問題完全不在它的職責範圍內，卻常被誤以為是 remount 沒做好：

- module 簽章驗證失敗（`CONFIG_MODULE_SIG_FORCE`）
- GKI 的 vermagic / KMI 不相容（`insmod` 回 `-EINVAL` 或 "version magic mismatch"）
- SELinux 拒絕存取你新增的節點（要改的是 policy，不是 mount flags）
- 檔案 push 進去了但 service 沒重啟，載入的還是舊的 `.so`

---

## 八、什麼時候該放棄 remount、老實刷機

建立一條清楚的界線，能省下大量無謂的除錯：

- **要驗證出廠行為時。** overlay 是合成視圖，不等於實際會出貨的 image。任何要簽核、要交付、要回報給客戶的驗證結果，都必須跑在完整刷機的裝置上。
- **改動涉及 ramdisk、first stage init、kernel、bootloader 時。**
- **改動涉及分區佈局、LP metadata、AVB descriptor 時。**
- **要測 OTA、factory reset、或 A/B slot 切換時。**
- **出現任何「行為與檔案內容對不上」的詭異症狀時。** 先 `adb enable-verity` 清乾淨、完整刷一次，排除 overlay 這個變因，再回頭 debug。這比在一個狀態不明的合成檔案系統上瞎猜快得多。

另外提醒安全面：整套機制只在 `userdebug` / `eng` build、且 bootloader 已解鎖的裝置上可用。這是設計意圖，不是限制。出貨的 user build 必須關掉 `ro.debuggable`、鎖上 bootloader、開著 verity——如果你的量產機能 `adb remount`，那是一個嚴重的安全漏洞，不是方便功能。

---

## 九、一句話的心智模型

> **`adb remount` 不是「把分區打開」，而是「在唯讀的出廠檔案系統上，臨時疊一層可拋棄的 diff」。**

抓住這個模型，前面所有的限制都變成推論而非需要背誦的規則：

- 因為是**臨時**的 → 會被清掉、不能當唯一備份、wipe data 後消失。
- 因為是**疊在上面**的 → 蓋不到 ramdisk 和 first stage init，因為那些階段還沒疊上去。
- 因為是**diff** → 空間按檔案計算、會爆、跟 OTA 的增量假設互相衝突。
- 因為底層**沒有真的改** → verity hash 沒被破壞，但也代表你驗的不是出貨的那個 image。

對做 driver 的人來說，這個機制的價值不在於它讓你能改系統檔案，而在於它把「改一行 code 到看到結果」的成本從十分鐘壓到十秒，同時保住了那些難得重現的現場。理解它的邊界，才能在它騙你的時候立刻認出來。

---

## 參考資料

- [Android OverlayFS Integration with adb Remount — AOSP `system/core/fs_mgr/README.overlayfs.md`](https://android.googlesource.com/platform/system/core/+/master/fs_mgr/README.overlayfs.md)
- [Implement dynamic partitions | Android Open Source Project](https://source.android.com/docs/core/ota/dynamic_partitions/implement)
- [platform_system_core/fs_mgr/README.overlayfs.md (aosp-mirror)](https://github.com/aosp-mirror/platform_system_core/blob/master/fs_mgr/README.overlayfs.md)
