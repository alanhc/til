# Das U-Boot

U-Boot 是 embedded 平台最常見的 bootloader，負責初始化硬體、載入 kernel 與 device tree，並跳入 OS。提供互動式命令列，方便開發與除錯。

## 環境變數

U-Boot 用環境變數 (environment) 儲存開機設定，可存於 eMMC/NAND/SPI flash：

```
printenv                 # 列出所有變數
setenv bootargs 'console=ttyS0,115200 root=/dev/mmcblk0p2'
saveenv                  # 存回 flash
```

- `bootcmd`：自動開機時執行的指令（倒數結束後跑）。
- `bootargs`：傳給 Linux kernel 的 cmdline。

## 載入 kernel

從網路 (TFTP) 或本地儲存 (MMC) 載入 kernel 與 device tree 到記憶體，再 `booti` / `bootm` 啟動：

```
# 從 TFTP 載入到指定位址
tftp 0x80000000 Image
tftp 0x88000000 board.dtb
booti 0x80000000 - 0x88000000     # <kernel> <initrd> <dtb>

# 從 MMC 讀檔
fatload mmc 0:1 0x80000000 Image
fatload mmc 0:1 0x88000000 board.dtb
booti 0x80000000 - 0x88000000
```

`booti` 的三個引數為 kernel、initrd（`-` 表示無）、device tree blob 的載入位址。

參考：<https://docs.u-boot.org/>
