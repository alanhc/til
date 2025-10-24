# Device Driver


## 名詞
- Device Tree: 用來描述硬體設備的資料結構
- Kconfig: 用來設定 kernel 功能選項的系統
- Makefile: 用來定義如何編譯程式的檔案
- defconfig: 預設的 kernel 配置檔案，可以設定 `y` (built-in) 或 `m` (module) 選項，用來決定哪些驅動程式會被編譯進 kernel 或作為模組載入。另外還有其他選項如 `n` (not built) 表示該驅動程式不會被編譯。
    - `y`: 表示該驅動程式會被編譯進 kernel (vmlinux) 中，無法動態卸載。在系統啟動後，可以在 `/sys/module/` 目錄下看到該驅動程式的相關資訊。
    - `m`: 表示該驅動程式會被編譯成模組 (.ko 檔案)，可以在系統啟動後由 initramfs / udev / modprobe 載入，也可卸載（若未被其他模組相依）。


## driver 背後如何被載入？
對應的 Makefile 裡面，Kbuild 會根據 `Kconfig` 的值來決定是否編譯該驅動程式。例如：
```makefile
obj-$(CONFIG_SENSORS_MPC42013)	+= mpc42013.o
```
- 如果在 kernel config 裡面設定 `CONFIG_SENSORS_MPC42013=y`，那麼 `mpc42013.o` 會被編譯進 kernel 映像檔 (vmlinux) 中。
- 如果設定為 `CONFIG_SENSORS_MPC42013=m`，那麼 `mpc42013.o` 會被編譯成模組檔案 `mpc42013.ko`，可以在系統啟動後由 initramfs / udev / modprobe 載入。
- 如果設定為 `CONFIG_SENSORS_MPC42013=n`，那麼該驅動程式不會被編譯。

## 如何選擇啟動載入時機？
- `=y`（內建）
核心解壓後立刻可用（跟隨 initcall 流程初始化）。
適合 開機關鍵路徑 的驅動／檔案系統（例如：開機載 rootfs 所需的儲存/控制器/檔案系統）。
無法 rmmod 卸載，也不會出現在 lsmod。
- `=m`（模組）
生成 .ko，可由 modprobe/insmod 載入、rmmod 卸載。
透過 modalias + udev 可自動載入（常見於 PCI/USB/平台裝置）。
適合非啟動關鍵、可選配、要節省核心常駐記憶體或需要動態切換的功能/驅動。
## 記憶體占用與更新
- `=y`：程式碼與資料常駐記憶體；好處是啟動即用、少一層模組管理；壞處是增加 vmlinux 體積與常駐 RAM。
- `=m`：只有載入後才占 RAM，可按需載入/卸載；升級或測試單一驅動較靈活（不必重編整個核心，只需重裝 .ko 與對應 Module.symvers/簽章）。
## 安全性與簽章
- 啟用 Secure Boot 時，模組通常需要簽章（X.509），載入時會驗證。內建 =y 的程式碼不走模組簽章路徑。
- 想禁止某模組可用 blacklist（modprobe.d/blacklist.conf）或開機參數（如 modprobe.blacklist=...）。對內建 =y 就無效（只能用核心參數控制功能行為，不能阻止存在）。

## 除錯與可見性
- =m：
lsmod 可見、modinfo foo 可看版本/別名/相依。
可在不重開機情況下重載模組，方便迭代除錯。
- =y：
不在 lsmod，無法卸載重載；除錯多靠啟動日誌、tracepoints、dynamic debug、ftrace、BPF 等

## initramfs / rootfs 考量
- 開機要用到的東西（例：系統根檔案系統、儲存控制器、必需檔案系統與加密/RAID 層）
    - 若設成 =m，就必須把 .ko 放進 initramfs 並在早期掛載前載入；
    - 否則改成 =y 最單純可靠。
- 非關鍵驅動（網卡、USB 週邊、調試選項等）多半可用 =m。


## 如何操作
在 defconfig/.config 中會看到：
```
CONFIG_SENSORS_MPC42013=y
```
或
```
CONFIG_SENSORS_MPC42013=m
```
- 互動式設定：
    - make menuconfig / nconfig：三態項目通常用 Y/M/N 切換；二態只能 Y/N。
    - 產生 defconfig：常見流程是 make savedefconfig 把和預設不同的選項寫回 defconfig。

## 何時選 y？何時選 m？
建議準則（供快速決策）：
- 選 =y（內建）
開機鏈路必要（rootfs 相關：儲存控制器、SATA/NVMe、必需檔案系統、LVM/RAID/加密層）。
早期初始化必備、且極少需要熱插拔或動態卸載。
想避免 initramfs 相依、或環境極簡（嵌入式最常見）。
- 選 =m（模組）
非啟動關鍵，依裝置是否存在按需載入（一般驅動、檔案系統、網卡、USB 裝置）。
需要熱插拔／節省常駐 RAM／方便維護與快速迭代。
可能需要在不同機型上彈性取捨、或由發行版自動裝載。