# Flash 與韌體更新

BMC 的韌體存在板上的 **SPI NOR flash**（常見 32MB / 64MB）。這顆 flash 同時放 u-boot、kernel、device tree 與 rootfs，所以「更新 BMC」實質上就是把新的 image 寫進這顆 flash 的某些區段。

搞懂 MTD 分割、以及各個寫入工具的差異，才不會在更新時把機器寫成磚。

## MTD：Linux 對 flash 的抽象層

**MTD**（Memory Technology Device）是 Linux 用來管理 raw flash 的子系統。它和一般硬碟（block device）最大的差別是：

- **flash 不能直接覆寫**。要改一個 byte，必須先把整個 **erase block**（NOR 常見 4KB 或 64KB）擦成全 `0xFF`，再寫入。
- **有寫入壽命**，每個 block 大約幾萬到十萬次擦寫。
- NAND 還有 **bad block** 與 **ECC** 的問題，NOR 則沒有。

所以 MTD 提供的是「擦除 + 寫入」的介面，而不是 block device 的「任意位置覆寫」。

### 看目前的分割

```bash
cat /proc/mtd
```

```
dev:    size   erasesize  name
mtd0: 000e0000 00010000 "u-boot"
mtd1: 00020000 00010000 "u-boot-env"
mtd2: 00440000 00010000 "kernel"
mtd3: 01b00000 00010000 "rofs"
mtd4: 00400000 00010000 "rwfs"
```

- `size` 與 `erasesize` 都是十六進位，單位 byte。上面 `erasesize = 0x10000` 就是 64KB。
- 分割由 device tree 的 `partitions` 節點定義（見 [device_tree](./device_tree.md)），或由 u-boot 的 `mtdparts` 傳入。

### 兩種裝置節點

| 節點 | 型態 | 說明 |
|---|---|---|
| `/dev/mtd0` | character device | raw 存取，`flash_erase`、`flashcp` 等 MTD 工具用這個 |
| `/dev/mtdblock0` | block device | 包成 block 介面，可以 `mount`，但**寫入行為受限**，不要拿來寫 image |

**規則：讀可以用任一個，寫一律用 `/dev/mtdN`（char device）搭配 MTD 工具。**

## 寫入工具

### flashcp — 最推薦

`mtd-utils` 提供，一支指令完成「擦除 → 寫入 → 驗證」：

```bash
flashcp -v image.bin /dev/mtd2
```

- `-v`：顯示進度。
- `-A`：寫入後再讀回比對（部分版本預設就會驗證）。

它會自動處理 erase block 對齊，是**更新 flash 的首選**。

### flash_erase — 只擦除

```bash
flash_erase /dev/mtd2 0 0          # 從 offset 0 擦到底（第二個 0 = 全部）
flash_erase /dev/mtd2 0 4          # 從 offset 0 擦 4 個 erase block
```

`flashcp` 已經包含擦除，通常不必單獨用。需要單獨擦的情境是「清掉 u-boot 環境變數」或「確認某區段真的是空的」。

### nandwrite — NAND 專用

NAND flash 有 bad block，寫入時必須跳過壞塊，所以不能用 `dd`：

```bash
flash_erase /dev/mtd3 0 0
nandwrite -p /dev/mtd3 image.bin   # -p 表示自動 pad 到 page 邊界
```

BMC 主要用 SPI NOR，這個工具比較少用到；但外掛的儲存區、或某些平台的 rootfs 在 NAND 上時會遇到。

### dd — 通常不該用

```bash
dd if=image.bin of=/dev/mtdblock2   # ❌ 不要這樣做
```

`dd` **不會先擦除**。flash 的寫入只能把 bit 從 `1` 變成 `0`，不能從 `0` 變回 `1`，所以直接 `dd` 到沒擦過的區域，得到的會是舊資料與新資料的 bitwise AND——一份看起來寫成功、實際上完全壞掉的 image。

`dd` 只適合**讀出來備份**：

```bash
dd if=/dev/mtd2 of=/tmp/backup-kernel.bin
```

**更新前先備份，是唯一能救回自己的方法。**

## 更新 BMC 韌體

### 方式一：OpenBMC 的標準流程（建議）

OpenBMC 有一套完整的更新機制，會處理版本檢查、簽章驗證與 A/B 切換：

```bash
# 把 tarball 放到指定目錄，phosphor-software-manager 會自動處理
scp obmc-phosphor-image.static.mtd.tar root@<bmc-ip>:/tmp/images/

# 查看被辨識出來的 image 版本（會列出一組 ID）
busctl tree xyz.openbmc_project.Software.BMC.Updater
```

或走 Redfish：

```bash
curl -k -u <user>:<pass> -H "Content-Type: application/octet-stream" \
  -X POST -T image.tar \
  https://<bmc-ip>/redfish/v1/UpdateService/update
```

也可以用 `ipmitool` 的 HPM.1 流程，看平台支援哪一種。

### 方式二：直接寫 MTD（開發階段）

只在開發或救援時用，會跳過所有版本與簽章檢查：

```bash
# 1. 先備份
dd if=/dev/mtd0 of=/tmp/uboot.bak

# 2. 寫入
flashcp -v /tmp/image-kernel /dev/mtd2

# 3. 重開
reboot
```

### A/B 雙 image

多數平台把 flash 切成兩份完整 image（primary / secondary，或稱 A/B slot），配合板上的 CPLD 或 SoC 的 watchdog 做 **fail-safe**：更新只寫其中一份，開機失敗時自動切回另一份。這樣即使新韌體有問題也不會變磚。

更新前確認自己正在寫哪一份：

```bash
fw_printenv                # 讀 u-boot 環境變數（開機選哪個 slot）
```

### 更新 u-boot 的風險

`mtd0`（u-boot）是**唯一寫壞就無法用軟體救回**的區段——寫壞後機器連 console 都進不去，只能用 SPI 燒錄夾（如 CH341A、Dediprog）外接晶片重燒。

所以：
- 非必要不要更新 u-boot。
- 一定要更新的話，先 `dd` 備份、確認 image 正確、確保更新過程不會斷電。
- `mtd1`（u-boot-env）擦掉還有救（會回到編譯時的預設值），但自訂的開機參數會全部消失。

## 常見問題

| 症狀 | 可能原因 |
|---|---|
| `flashcp` 寫入後驗證失敗 | flash 有壞塊、或寫入中被中斷、或寫錯 MTD 編號 |
| 寫入成功但開機停在 u-boot | kernel 分割寫錯位置，或 image 格式不符（uImage vs FIT） |
| 更新後空間不足 | rwfs（可寫入區）滿了，`journalctl --vacuum-size` 或清 `/var/log` |
| `/dev/mtdX` 不存在 | kernel 的 MTD driver 沒編進去，或 device tree 沒定義 partitions |

## 參考

- [MTD 官方文件](http://www.linux-mtd.infradead.org/doc/general.html)
- [OpenBMC — Code Update 架構](https://github.com/openbmc/docs/blob/master/architecture/code-update/code-update.md)
