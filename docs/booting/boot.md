# 開機流程 (泛用概念)

不論 x86、ARM 或 RISC-V，開機都是一段「愈來愈有能力」的接力：每一階段初始化足夠的硬體，把控制權交給下一階段，逐步從幾行 ROM code 走到完整 OS。

## 典型階段

1. **Reset vector**：CPU 上電或 reset 後，PC 指向一個固定位址開始取指令，執行 SoC 內建的 boot ROM / 第一段 code。
2. **Firmware / 初階 bootloader**：初始化時脈、DRAM 等最基本硬體。ARM 平台常見分層韌體（見 `atf.md`，即 ARM Trusted Firmware，負責 secure world 與 PSCI）。
3. **Bootloader**：如 U-Boot、GRUB，載入 OS kernel 與相關資料（device tree、initramfs），設定啟動參數後跳入。
4. **OS kernel**：接手後初始化其餘 subsystem 與 driver，最後啟動 user space。

## 幾個常見概念

- **多階段 (multi-stage)**：早期程式空間極小（可能只有幾 KB SRAM），需分階段載入。
- **Secure boot / chain of trust**：每一階段驗證下一階段的簽章後才執行。
- **Root of trust**：信任鏈的起點，通常是不可竄改的 boot ROM。

延伸：ARM 平台細節見同資料夾 `atf.md`；Linux 桌面/伺服器流程見 `Linux/booting.md`。
