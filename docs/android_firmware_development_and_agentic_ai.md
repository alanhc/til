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
2. 查詢對應的 AOSP source tag
3. 下載對應的 Vendor proprietary blob，驗證 SHA-256
4. `repo init` → `repo sync`（30–90 分鐘）
5. 解壓 vendor blob，同意授權條款
6. `lunch aosp_shiba-userdebug` → `m`（1–3 小時）
7. `fastboot flashall` 燒錄

其中需要人真正思考的步驟有幾個？大概只有：版本對不齊的時候、編譯錯誤的時候、硬體出現異常的時候。其他步驟，本質上都是在等待和執行固定程序。

## 解法：封裝成 AI Agent Skill

AI Agent Skills 的核心概念是：把一段有明確輸入、明確輸出、可重複執行的流程，封裝成 AI 可以自主執行的單元。人只需要定義「什麼情況下要做什麼」，剩下的交給 AI。

以 AOSP build pipeline 為例，我設計了一個 skill，輸入只有一個：**Build ID**（例如：`BP4A.251205.006`）。

Skill 接著自動完成整條 pipeline：

```
Build ID
   ↓
查詢 AOSP source tag + Vendor driver URL
   ↓
repo init / repo sync
   ↓
下載 vendor blob → SHA-256 驗證
   ↓
解壓 + 同意授權
   ↓
lunch + m（編譯）
   ↓
fastboot flashall（含安全確認）
```

整個過程中，AI 會在每個階段記錄狀態、處理可預期的失敗（如網路中斷自動 retry、repo sync 降低並行數）、並在遇到需要判斷的問題時暫停，通知工程師介入。

## 設計介入邊界

這是整個架構中最重要的設計決策：哪些交給 AI，哪些留給人？

| 交給 AI | 留給人 |
|---------|--------|
| repo sync / build / flash 的執行 | bootloader unlock（會清除資料） |
| SHA-256 驗證 | 版本對齊決策（找不到對應 tag 時） |
| 可預期的錯誤處理（retry） | 非預期的編譯錯誤分析 |
| 進度記錄與通知 | 硬體異常判斷 |

關鍵原則是：**凡是不可逆的操作，或是需要上下文判斷的問題，AI 不自動執行，一律暫停等人確認。**

## 實際效益

導入這套架構後，最明顯的改變不是「速度變快」，而是工程師可以同時持有多個 project 的狀態。

- **以前**：一次只能專注一個 build，等待期間的注意力是碎片化的。
- **以後**：三個 project 的 build pipeline 同時跑，工程師只需要處理每個 pipeline 的「例外狀況」。

這本質上是把工程師的角色從**執行者**轉變成**監督者**——而這個轉變，正是 Agentic AI 最有價值的地方。

## 結語

Agentic AI 不是要取代工程師，而是要把工程師從重複性的等待和執行中解放出來。Embedded / Firmware 開發中有大量這樣的 routine，而這些 routine 正是 AI Agent Skills 最適合接管的工作。

**讓 AI 跑 Build。你來解難題。**

---

本文相關的 AOSP build skill 已開源：[github.com/alanhc/aosp-build](https://github.com/alanhc/aosp-build)
