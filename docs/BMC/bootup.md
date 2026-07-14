# BMC 開機流程

BMC 通常是一顆 ARM SoC（如 ASPEED AST2500/AST2600），跑一套嵌入式 Linux。開機大致經過 **bootloader → kernel（zImage）→ rootfs** 三個階段。

bootloader

zImage

## 開機階段

1. **bootloader（u-boot）**：SoC 上電後由內建 ROM 載入 SPI flash 上的 u-boot。u-boot 負責初始化 DRAM、時脈與基本周邊，接著從 flash 讀取 kernel 與 device tree 到記憶體，最後跳轉執行 kernel。可透過序列埠中斷進入 u-boot console 手動下指令。
2. **kernel（zImage）**：`zImage` 是壓縮過的 ARM Linux kernel image，前段的解壓縮 stub 會先把自己解開再啟動真正的 kernel。kernel 搭配 device tree（.dtb）得知硬體配置後，初始化驅動並掛載 root filesystem。
3. **rootfs**：掛載根檔案系統後執行 init（OpenBMC 使用 systemd），啟動各項服務（如 Redfish、IPMI、感測器監控），BMC 正式進入可運作狀態。

## 相關概念

- Flash 上常見多個 image slot（如雙 image A/B）以支援 fail-safe 與 OTA 更新。
- 也可能使用 `uImage`（含 u-boot header）或 FIT image（kernel + dtb + ramdisk 打包）取代單純的 `zImage`。
