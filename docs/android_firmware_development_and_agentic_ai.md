---
title: 韌體開發與 Agentic AI
sidebar_label: Firmware Dev & Agentic AI
---

# 韌體開發與 Agentic AI：讓 AI 跑 Build，你來解難題

*Firmware Development and Agentic AI: Let AI Handle the Builds, You Solve the Hard Parts*

## 前言

身為在 IC 廠工作的 Embedded Software Engineer，我的日常有很大一部分是這樣的：

```
repo sync → build → flash → verify → repeat
```

每個 project 都要走一遍。每次改動都要重新跑。等 build 的時候能做什麼？通常是開另一個視窗，繼續等另一個 build。

這不是工程師獨有的問題，但在 Embedded / Firmware 開發中特別明顯：build time 長、環境依賴複雜、版本對齊嚴格。這些 routine 工作佔據了大量時間，卻幾乎不需要人的判斷力。

這篇文章分享我如何用 AI Agent Skills 把這套流程自動化，讓一個人可以同時推進多個 project，只在真正需要的時候介入。

## 問題的本質

在開始談解法之前，先釐清問題。

AOSP 開發（以 Pixel 8 為例）的標準流程大概是這樣：

1. 從手機讀取 Build ID：`adb shell getprop ro.build.id`
2. 查詢對應的 AOSP source tag（例如：`android-15.0.0_r34`）
3. 下載對應的 Vendor proprietary blob，驗證 SHA-256
4. `repo init` → `repo sync`（30–90 分鐘）
5. 解壓 vendor blob，同意授權條款
6. `lunch aosp_shiba-bp1a-userdebug` → `m`（1–3 小時）
7. `fastboot flashall` 燒錄

其中需要人真正思考的步驟有幾個？大概只有：版本對不齊的時候、編譯錯誤的時候、硬體出現異常的時候。其他步驟，本質上都是在等待和執行固定程序。

值得注意的是，即使是「固定程序」，細節也會隨版本變化。例如 Android 14 之後，`lunch` 指令從兩段式（`aosp_shiba-userdebug`）改為三段式（`aosp_shiba-bp1a-userdebug`），中間多了 release config。這種無聲的規格變動，正是讓人在 debug 時浪費大量時間的地方。

## 解法：封裝成 AI Agent Skill

AI Agent Skills 的核心概念是：把一段有明確輸入、明確輸出、可重複執行的流程，封裝成 AI 可以自主執行的單元。人只需要定義「什麼情況下要做什麼」，剩下的交給 AI。

以 AOSP build pipeline 為例，我設計了一個 skill，輸入只有一個：**Build ID**（例如：`BP1A.250505.005.B1`）。

Skill 接著自動完成整條 pipeline：

```
Build ID
   ↓
查詢 AOSP source tag + Vendor driver URL（含 SHA-256）
   ↓
repo init / repo sync
   ↓
下載 vendor blob → SHA-256 驗證
   ↓
解壓 + 自動接受授權條款
   ↓
自動偵測 release config → lunch + m（編譯）
   ↓
fastboot flashall（含安全確認）
```

整個過程中，AI 會在每個階段記錄狀態、處理可預期的失敗（如網路中斷自動 retry、repo sync 降低並行數）、並在遇到需要判斷的問題時暫停，通知工程師介入。

## 設計介入邊界

這是整個架構中最重要的設計決策：哪些交給 AI，哪些留給人？

| 交給 AI | 留給人 |
|---------|--------|
| repo sync / build / flash 的執行 | bootloader unlock（不可逆，會清除資料） |
| SHA-256 驗證 | 版本對齊決策（找不到對應 tag 時） |
| 可預期的錯誤處理（retry、降低並行數） | 非預期的編譯錯誤分析 |
| 進度記錄與通知 | 硬體異常判斷 |
| vendor blob 解壓與 EULA 自動接受 | flash 參數選擇（`--wipe` 等破壞性操作） |
| 跨機器 image 打包與傳輸 | |

關鍵原則是：**凡是不可逆的操作，或是需要上下文判斷的問題，AI 不自動執行，一律暫停等人確認。**

## 真實踩坑：AI 如何診斷與修復

理論說完，來看實際發生的事。

### 坑一：Android 14 的 lunch 格式無聲改變

第一次 build 失敗，錯誤訊息是：

```
Invalid lunch combo: aosp_shiba-userdebug
Valid combos must be of the form <product>-<release>-<variant>
```

原因：Android 14 開始，lunch 格式從兩段式改為三段式，需要指定 release config。`BP1A.*` 對應的 release config 是 `bp1a`，正確指令是：

```bash
lunch aosp_shiba-bp1a-userdebug
```

舊版教學、舊版 script 全部失效，卻沒有任何明顯的遷移說明。AI 在錯誤訊息出現後，自動掃描 `build/release/release_configs/` 目錄偵測正確的 config 名稱，並更新了 skill 的 build 邏輯，下次不會再踩。

### 坑二：Vendor blob 靜默失敗，build 成功但開不了機

`m` 編譯完成，image 全部產出，flash 也沒有錯誤。但手機 flash 完之後一直在開機畫面和 fastboot 之間循環，進不了系統。

問題出在更早的步驟：vendor blob 解壓時，EULA 腳本需要兩次輸入（先按 Enter 翻頁，再輸入 `I ACCEPT`），但 script 只送了一次，導致解壓靜默中止。`vendor/google_devices/shiba/` 目錄根本是空的。

`m` 沒有報錯，因為它不知道 vendor 應該要有東西。編譯出來的 `super.img` 缺少 vendor library，手機開機時找不到必要的驅動就當掉。

修復方式：重新 extract vendor blob，incremental build 只花了 3 分鐘，再次 flash 成功。

AI 在這次事故後更新了 skill：build 開始前新增 vendor blob 存在性檢查，缺少時立即報錯並提示如何修復，而不是讓 build 跑完才發現問題。

### 坑三：跨機器 flash 的隱藏依賴

從 Linux build machine 把 image 複製到 Mac 上刷機。打包時用了 `*.img` glob，看起來完整，但 `fastboot flashall` 一執行就報錯：

```
fastboot: error: could not read android-info.txt
```

`android-info.txt` 不是 `.img`，不在 glob 範圍內，但 `flashall` 需要它來確認裝置型號。加上之後正常。

另一個坑：直覺上以為 userdebug build 需要 `--disable-verity --disable-verification` 才能開機，但在 fastboot 37+ / Pixel 8+ 上這個做法會報錯：

```
fastboot: error: Failed to find AVB_MAGIC at offset: 0
```

原因是 fastboot 試圖 patch 一個不存在於 image 目錄的 partition（`vbmeta_vendor_kernel_boot`）。實際上 `m` 在 userdebug build 時已經在 `vbmeta.img` 裡設定好正確的 AVB flags，不需要額外 patch。直接 `fastboot flashall -w` 就好。

## 實際效益

導入這套架構後，最明顯的改變不是「速度變快」，而是工程師可以同時持有多個 project 的狀態。

- **以前**：一次只能專注一個 build，等待期間的注意力是碎片化的。
- **以後**：三個 project 的 build pipeline 同時跑，工程師只需要處理每個 pipeline 的「例外狀況」。

這本質上是把工程師的角色從**執行者**轉變成**監督者**——而這個轉變，正是 Agentic AI 最有價值的地方。

值得一提的是，每次踩坑之後，skill 本身也在對話中被即時更新。每個遇到的問題都變成了文件和防護邏輯，下次同樣的坑不會再踩。這不是第一次就完美的系統，而是每次失敗都讓自己變得更強的系統。

## 結語

Agentic AI 不是要取代工程師，而是要把工程師從重複性的等待和執行中解放出來。Embedded / Firmware 開發中有大量這樣的 routine，而這些 routine 正是 AI Agent Skills 最適合接管的工作。

真正需要工程師的地方——版本衝突的判斷、異常硬體的診斷、架構層面的決策——一個都沒有少。只是那些不需要判斷力的時間，現在可以拿回來了。

**讓 AI 跑 Build。你來解難題。**

---

本文相關的 AOSP build skill 已開源：[github.com/alanhc/aosp-build](https://github.com/alanhc/aosp-build)