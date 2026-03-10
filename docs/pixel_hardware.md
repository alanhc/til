zuma: Google Tensor G3 晶片 (SoC) 的代號
shiba: Pixel 8 手機裝置 (Device) 的代號


核心分支名稱是 `android-gs-zuma-...`（gs 代表 Google Silicon）。

處理 AOSP (系統映像檔) 與 Device Tree 時看裝置代號
執行 `lunch aosp_shiba-userdebug`，這樣編譯系統才會載入 Pixel 8 專屬的 Device Tree (DTS) 和硬體抽象層 (HAL) 設定。