## materials
- https://notebooklm.google.com/notebook/8ddd60a2-3f09-4ba0-ba8c-83983ec1f216
- https://chatgpt.com/c/6968ee3a-97e8-8331-a0be-c2cc4d54020a
- 
# Learning Pixel
- Hardware
- CPU
- GPU
	- OpenCL
	- Valcun
- 
# Learning Android 
# 問題
die shot（裸晶照片）可以推測「資源配置」與「可能的瓶頸」? [chip](chip.md)
OTA是什麼？
Android Boot Flow
Kernel Init Flow and init.S
MTE 練習 Native Crash 除錯
Fastboot 是什麼
ICE的操作，GDB per perfecto 等debug tool
Linux 核心設計: 追蹤與測試工具 https://hackmd.io/@RinHizakura/Sy0pT4TpT
Memory debug cortex cpu debug
Bootloader kernel domain knowledge background
# Learning Step
## Step 1: 軟體架構與編譯系統 (The Architect)
1. **AOSP Build System (Soong/Blueprint)：**
	1. **行動：** 下載 AOSP 原始碼，編譯 `aosp_cf_x86_64_phone-userdebug` 並成功啟動
	2. **核心技能：** 這是驗證你是否搞懂 `Android.bp` 與 `make` 邏輯的最快方式，比燒錄實體機快得多
2. (略) **純軟體 HAL (Pure Logic HAL)：**
	1. **行動：** 撰寫一個「假」的 HAL Service（例如控制虛擬 LED 寫 Log）
	2. **核心技能：** 專注於 **Binder IPC**、**SELinux Policy** 以及 **Service Manager** 的註冊流程，這些在虛擬機與實體機上完全一致
3. **自動化測試 (VTS/CTS)：**
	1. **行動：** 在 Cuttlefish 上執行 `run vts` 並分析 Log
	2. **核心技能：** 這是 Google 內部標準的驗證方式，是 SI 解 Bug 的基本功。
## Step 2: 嵌入式底層與 Bring-up (The Bring-up Engineer)
**目標：** 連結軟體與硬體，掌握 Bootloader 與驅動開發。 **硬體需求：** **BeagleBone Black** (純 Linux) + **Raspberry Pi 4** (Android) **預算：** 約 NT$ 3,000 - 5,000
1. **U-Boot 與 Kernel 啟動 (BeagleBone)：**
	1. **行動：** 透過 UART 觀察開機 Log，練習編譯 U-Boot 與最簡單的 Kernel Module (.ko)
	2. **核心技能：** 學習 CPU 上電後的第一條指令、SPL 載入流程與 Device Tree Overlay。這是 CPU Vendor BL 團隊的基本功。
2. **Android Board Bring-up (RPi 4)**
	1. **行動：** 使用 **GloDroid** 專案，練習修改 `BoardConfig.mk` 與 `.rc` 文件
	2. **核心技能：** 實作 **GPIO HAL**（控制實體燈號）與 **Audio HAL**（智慧音箱音訊路由），這些是虛擬機做不到的
	3. **優勢：** 樹莓派「不怕變磚」，SD 卡重刷即可，適合大膽實驗
## Step3: 現代 Android 標準與 GKI (The Modern SI)
**目標：** 掌握手機產業特有的分區結構與 Google 強制規範。 **硬體需求：** **Pixel 6a** 或 **Pixel 7a** **預算：** 約 NT$ 4,500 (二手機)
1. **GKI (Generic Kernel Image) 實戰：**
	1. **行動：** 練習掛載 `vendor_dlkm` 分區，編譯驅動模組
	2. **核心技能：** 理解「Core Kernel 不能動、驅動必須模組化」的 GKI 2.0 邏輯，這是 Android 14/15 的標準
2. **Fastboot 與救磚 (Unbrick)：**
	1. **行動：** 練習手動敲 `fastboot flash` 指令（非一鍵腳本），並嘗試刷掛分區後救回
	2. **核心技能：** 熟悉 **A/B Partition (Seamless Update)** 切換 Slot 的機制，以及如何關閉 **AVB (Android Verified Boot)** 進行 Remount R/W
3. **純 64-bit 環境 (Pixel 7a)：**
4. **行動：** 在沒有 Zygote32 的環境下測試 Native Library
5. **核心技能：** 提早適應如新平台移除 32-bit 支援後的系統行為。

## Step4: 進階除錯與新架構研究 (The Expert)
**目標：** 針對記憶體除錯與最新 SoC 架構進行深度研究。 **硬體需求：** **Pixel 8** 或 **Pixel 10 Pro** **預算：** NT$ 9,000 - 26,000
1. **記憶體除錯 (Pixel 8)：**
	1. **行動：** 開啟 **MTE (Memory Tagging Extension)** 進行 Native Crash 除錯
	2. **核心技能：** 利用硬體特性精準抓出 Buffer Overflow 或 Use-after-free，這比軟體模擬（KASAN）快且準
2. **次世代架構分析 (Pixel 10 Pro / Tensor G5)：**
	1. **行動：** 分析 **TSMC 3nm** 製程下的能效表現，以及 **Imagination GPU** 的 Vulkan 相容性
	2. **核心技能：** 觀察 Google 如何在 `1+5+2` 的 CPU 配置下調度 Scheduler，以及 TPU v4 如何處理 On-device Gen AI 的記憶體頻寬
## Step5: 競品對標與效能調校 (The Benchmarker)
**目標：** 建立「白箱」與「黑箱」測試標準，優化使用者體驗。 **硬體需求：** **iPhone** (黑箱) + **Pixel** (白箱)
1. **自動化腳本開發：**
	1. **行動：** 撰寫 Shell/Python 腳本自動執行 `am start`、`screencap` 與 `dumpsys gfxinfo`
	2. **核心技能：** 建立可重複（Repeatable）的測試環境，計算 FPS 與 Jank（卡頓）
2. **競品對標 (iPhone)：**
	1. **行動：** 使用 **Metal Performance HUD** 與 **Xcode Instruments**
	2. **核心技能：** 分析 iOS 的 **能效比 (Performance per Watt)** 與 **記憶體佔用 (Memory Footprint)**，作為優化 Android 產品的目標
	3. 