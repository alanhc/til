# Bootloader

**Bootloader** 是 CPU 上電後、OS 接手前跑的那段程式。它的任務很單純：**把硬體初始化到「足以載入 kernel」的程度，然後把 kernel 搬進記憶體並跳過去**。

聽起來簡單，但實際上一顆 SoC 剛上電時幾乎什麼都不能用——DRAM 沒初始化、時脈沒設好、儲存裝置的控制器沒啟動。所以現代平台不會用單一個 bootloader，而是**分成好幾個階段（stage），一階一階把系統叫醒**。

## 為什麼要分階段

核心矛盾是：**最早執行的程式碼必須存放在晶片內部的 ROM 或 SRAM，而這些空間極小（常見 16KB 以下）**。這麼小的空間塞不下 DRAM 初始化 + 檔案系統 + 韌體驗證的完整邏輯，所以只能：

1. 第一階段用極小的程式碼，把第二階段從 flash 讀到晶片內建的 SRAM。
2. 第二階段有比較多空間，可以初始化 DRAM。
3. DRAM 起來後，就有幾百 MB 可用，第三階段可以做完整的事情。

**每一階段負責把下一階段叫醒，並且驗證它的簽章**——這條鏈就是 secure boot 的基礎。

## 通用的階段命名：BL0 / BL1 / BL2 / BL31 / BL33

ARM 官方的 **TF-A**（Trusted Firmware-A）定義了一套通用命名，各家平台或多或少對應得上：

| 階段 | 慣稱 | 執行位置 | 任務 |
|---|---|---|---|
| **BL0** | Boot ROM | 晶片內部 ROM（唯讀，出廠燒死） | 上電第一段程式碼，驗證並載入 BL1/BL2 |
| **BL1** | AP Trusted ROM | 晶片內 SRAM | 最小初始化，載入 BL2 |
| **BL2** | Trusted Boot Firmware | SRAM | **初始化 DRAM**，載入後續所有 image |
| **BL31** | EL3 Runtime Firmware | DRAM | 常駐的 secure monitor，提供 PSCI（電源控制）等服務 |
| **BL32** | Secure Payload | DRAM（Secure World） | TEE / OP-TEE，可信執行環境 |
| **BL33** | Non-trusted Firmware | DRAM（Normal World） | **u-boot / UEFI / LK**，最後跳到 kernel |

要注意的是**這只是命名慣例，各家實作對應不一定整齊**。Qualcomm 叫 PBL/SBL/XBL，MediaTek 有自己的 preloader，BMC 用的 ASPEED 平台則相對簡單（Boot ROM → u-boot → kernel）。

更多 TF-A 細節見 [ARM Trusted Firmware 解析](./ARM_Trusted_Firmware_解析.md)。

## Android 平台的階段

[Booting process of Android devices（Wikipedia）](https://en.wikipedia.org/wiki/Booting_process_of_Android_devices) 整理的通用流程：

### Stage 1：PBL（Primary Bootloader）

也就是 **Boot ROM**，燒死在晶片內部，**無法更新**。

- 空間極小，通常小於 16 KB。
- 職責：設定最基本的 CPU 狀態、從預設的開機媒體（eMMC / UFS / SPI）讀出第二階段、**驗證其簽章**、跳過去。
- 因為不可更新，PBL 裡的漏洞是無法修補的（歷史上的 BootROM exploit 之所以珍貴就是這個原因）。
- 它同時是 **secure boot 的信任根（root of trust）**——晶片內的 eFuse 存著公鑰雜湊，PBL 拿它驗證下一階段。

### Stage 2：SBL（Secondary Bootloader）

在 SRAM 執行，主要任務是**初始化 DRAM**。DRAM 的初始化很麻煩（要跑 training 決定時序參數），這是為什麼它需要獨立一個階段。

Qualcomm 平台稱為 **SBL / XBL**（eXtensible Bootloader，較新的平台改用 UEFI 架構）。

### Stage 3：應用處理器 bootloader

DRAM 就緒後跳到這裡。Android 上這一階段通常是 **LK（Little Kernel）**，Qualcomm 平台上叫 **aboot**。

職責：
- 檢查是否要進 **fastboot 模式**（開機時按組合鍵，或 `adb reboot bootloader`）。
- 依開機原因決定要載入 `boot.img`、`recovery.img` 還是進 fastboot。
- 執行 **AVB（Android Verified Boot）** 驗證，決定裝置的 boot state（green / yellow / orange / red）。
- 把 kernel、ramdisk、dtb 載入 DRAM，設定 kernel command line，跳轉。

以 2018 年的統計，Android 市場約 90% 的 SoC 來自 Qualcomm、Samsung、MediaTek，其餘廠商包含 UNISOC、Rockchip、Marvell、Nvidia，以及早期的 Texas Instruments。**各家在這一階段的實作差異最大**，也是移植與逆向工程最常打交道的地方。

Qualcomm 的 ABL 逆向可參考 [ABL / AVB 逆向](./abl-avb-reversing.md)，MediaTek 的 preloader 見 [MTK Boot Deep Dive](./mtk-boot-deep-dive.md)，兩家的比較見 [Qualcomm vs MediaTek boot flow](./qualcomm-vs-mediatek-android-boot-flow.md)。

## LK（Little Kernel）

**LK 是一個極小的嵌入式作業系統核心**，不是傳統意義上「只會載入 kernel」的 bootloader。它提供：

- 搶佔式的多執行緒排程器
- 計時器、互斥鎖、事件等基本同步原語
- 簡單的裝置驅動框架
- 記憶體管理

因為麻雀雖小五臟俱全，很適合拿來當作需要跑 USB 協定堆疊（fastboot）、需要驅動螢幕（顯示開機畫面與警告）的 bootloader。

- 上游專案：[littlekernel/lk](https://github.com/littlekernel/lk)
- Android 的分支：[android.googlesource.com/kernel/lk](https://android.googlesource.com/kernel/lk/)
- **Qualcomm 的 aboot 是從 littlekernel/lk fork 出來的**，加上 fastboot、AVB、顯示等 Android 專屬功能。
- 生態資源整理：[awesome-littlekernel](https://github.com/milisarge/awesome-littlekernel?tab=readme-ov-file)

值得注意的是 Google 的 **Fuchsia** 作業系統，其 Zircon 微核心最早也是從 LK 演化而來。

## u-boot

嵌入式 Linux（包含 BMC）最常見的 bootloader，功能比 LK 更偏向「通用開機工具」：

- 互動式 console（開機時按任意鍵中斷）
- 豐富的儲存裝置與網路支援（TFTP 開機、USB、MMC、SPI flash）
- 環境變數系統（`fw_printenv` / `setenv`），可設定開機參數而不必重編
- `fdt` 指令可在跳轉前臨時修改 device tree

BMC 上的用法見 [BMC 開機流程](./BMC/bootup.md)。

## 相關筆記

- [x86 Linux Boot Flow](./booting/x86_linux_boot_flow.md)
- [RISC-V Linux Boot Flow](./booting/riscv_linux_boot_flow.md)
- [Android Boot Flow](./android_boot_flow.md)
- [OpenBMC Boot Flow](./BMC/openbmc_boot_flow.md)

## 參考

- [从零开始写一个简单的 bootloader](https://blog.csdn.net/lee_jimmy/article/details/82079342)
- [UBOOT 启动流程中的 BL0, BL1, BL2](https://blog.csdn.net/qq_49864684/article/details/118897622)
- [用于嵌入式操作系统的微内核（LK）](https://blog.csdn.net/guoqx/article/details/135433035)
- [Boot ROM（Wikipedia）](https://en.wikipedia.org/wiki/Boot_ROM)
