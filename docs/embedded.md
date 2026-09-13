# 嵌入式系統背景知識

Bootloader kernel domain knowledge background — 嵌入式 Linux 系統從開機到執行的主要組成。

## 開機與軟體堆疊
1. **Bootloader**：上電後最先執行，負責初始化硬體、載入 kernel 到記憶體並移交控制權（如 U-Boot）。多階段開機常見：BootROM → SPL/first-stage → 完整 bootloader → kernel。
2. **Kernel**：Linux 核心，管理記憶體、行程排程、檔案系統與 driver，並掛載 root filesystem。裝置硬體資訊常由 **Device Tree（.dts/.dtb）** 描述。
3. **Root filesystem（rootfs）**：使用者空間，含 init 系統、函式庫與應用程式（常用 Buildroot 或 Yocto 建置）。
4. **Driver**：核心與硬體周邊（GPIO、I2C、SPI、UART 等）之間的橋樑。

## 常見關鍵字
- 交叉編譯（cross-compile）toolchain、`defconfig`。
- kernel space vs. user space。
- init：BusyBox init、systemd。
