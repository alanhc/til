# 韌體開發與 Agentic AI：讓 AI 跑 Build，你來解難題
# Firmware Development and Agentic AI: Let AI Handle the Builds, You Solve the Hard Parts

## 前言 | Introduction
身為在 IC 廠工作的 Embedded Software Engineer，我的日常有很大一部分是這樣的：

As an Embedded Software Engineer working at an IC design company, a large chunk of my day looks like this:

repo sync → build → flash → verify → repeat
每個 project 都要走一遍。每次改動都要重新跑。等 build 的時候能做什麼？通常是開另一個視窗，繼續等另一個 build。

Every project goes through the same cycle. Every change requires a full run. While waiting for a build to finish, what do you do? Usually — open another terminal and wait for another build.

這不是工程師獨有的問題，但在 Embedded / Firmware 開發中特別明顯：build time 長、環境依賴複雜、版本對齊嚴格。這些 routine 工作佔據了大量時間，卻幾乎不需要人的判斷力。

This isn't unique to firmware engineers, but it's especially pronounced in embedded development: long build times, complex environment dependencies, and strict version alignment requirements. These routine tasks consume enormous amounts of time while requiring almost no human judgment.

這篇文章分享我如何用 AI Agent Skills 把這套流程自動化，讓一個人可以同時推進多個 project，只在真正需要的時候介入。

This article shares how I used AI Agent Skills to automate this workflow — enabling one engineer to drive multiple projects simultaneously, intervening only when genuinely needed.

## 問題的本質 | The Core Problem
在開始談解法之前，先釐清問題。

Before talking about solutions, let's define the problem clearly.

AOSP 開發（以 Pixel 8 為例）的標準流程大概是這樣：

A standard AOSP development flow (using Pixel 8 as an example) looks roughly like this:

從手機讀取 Build ID（adb shell getprop ro.build.id）
查詢對應的 AOSP source tag
下載對應的 Vendor proprietary blob，驗證 SHA-256
repo init → repo sync（30–90 分鐘）
解壓 vendor blob，同意授權條款
lunch aosp_shiba-userdebug → m（1–3 小時）
fastboot flashall 燒錄
Read Build ID from device (adb shell getprop ro.build.id)
Look up the corresponding AOSP source tag
Download the matching vendor proprietary blob and verify SHA-256
repo init → repo sync (30–90 minutes)
Extract vendor blob and accept the license agreement
lunch aosp_shiba-userdebug → m (1–3 hours)
fastboot flashall to flash
其中需要人真正思考的步驟有幾個？大概只有：版本對不齊的時候、編譯錯誤的時候、硬體出現異常的時候。其他步驟，本質上都是在等待和執行固定程序。

How many of these steps actually require human thinking? Roughly: when versions don't align, when there's a compile error, when hardware behaves unexpectedly. Everything else is essentially waiting and executing fixed procedures.

## 解法：封裝成 AI Agent Skill | The Solution: Encapsulating into an AI Agent Skill
AI Agent Skills 的核心概念是：把一段有明確輸入、明確輸出、可重複執行的流程，封裝成 AI 可以自主執行的單元。人只需要定義「什麼情況下要做什麼」，剩下的交給 AI。

The core idea of AI Agent Skills is to encapsulate a workflow with clear inputs, clear outputs, and repeatable execution into a unit that AI can run autonomously. You define "what to do under what conditions" — the rest is delegated.

以 AOSP build pipeline 為例，我設計了一個 skill，輸入只有一個：

Using the AOSP build pipeline as an example, I designed a skill with a single input:

Build ID（例如：BP4A.251205.006）
Skill 接著自動完成：

The skill then automatically handles:

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
整個過程中，AI 會在每個階段記錄狀態、處理可預期的失敗（如網路中斷自動 retry、repo sync 降低並行數）、並在遇到需要判斷的問題時暫停，通知工程師介入。

Throughout the process, the AI logs status at each stage, handles predictable failures (auto-retry on network interruption, reducing parallelism on repo sync throttling), and pauses to notify the engineer when a decision requiring human judgment is encountered.

## 設計介入邊界 | Designing the Intervention Boundary
這是整個架構中最重要的設計決策：哪些交給 AI，哪些留給人？

This is the most critical design decision in the entire architecture: what to delegate to AI, and what to keep in human hands?

交給 AI	留給人
repo sync / build / flash 的執行	bootloader unlock（會清除資料）
SHA-256 驗證	版本對齊決策（找不到對應 tag 時）
可預期的錯誤處理（retry）	非預期的編譯錯誤分析
進度記錄與通知	硬體異常判斷
Delegate to AI	Keep in Human Hands
Executing repo sync / build / flash	Bootloader unlock (wipes data)
SHA-256 verification	Version alignment decisions (when no matching tag exists)
Predictable error handling (retry)	Unexpected compile error analysis
Progress logging and notification	Hardware anomaly diagnosis
關鍵原則是：凡是不可逆的操作，或是需要上下文判斷的問題，AI 不自動執行，一律暫停等人確認。

The key principle: any irreversible operation, or any problem requiring contextual judgment, is not executed automatically — the AI pauses and waits for human confirmation.

## 實際效益 | Real-World Impact
導入這套架構後，最明顯的改變不是「速度變快」，而是工程師可以同時持有多個 project 的狀態。

After adopting this architecture, the most noticeable change wasn't "things got faster" — it was that an engineer can now hold the state of multiple projects simultaneously.

以前：一次只能專注一個 build，等待期間的注意力是碎片化的。
以後：三個 project 的 build pipeline 同時跑，工程師只需要處理每個 pipeline 的「例外狀況」。

Before: focus on one build at a time, attention fragmented during waiting periods.
After: three project pipelines running simultaneously, the engineer only handles "exceptions" from each.

這本質上是把工程師的角色從執行者轉變成監督者——而這個轉變，正是 Agentic AI 最有價值的地方。

This fundamentally shifts the engineer's role from executor to supervisor — and that shift is precisely where Agentic AI delivers its greatest value.

## 結語 | Conclusion
Agentic AI 不是要取代工程師，而是要把工程師從重複性的等待和執行中解放出來。Embedded / Firmware 開發中有大量這樣的 routine，而這些 routine 正是 AI Agent Skills 最適合接管的工作。

Agentic AI isn't about replacing engineers — it's about freeing them from repetitive waiting and execution. Embedded and firmware development is full of exactly this kind of routine, and that routine is precisely what AI Agent Skills are best suited to take over.

讓 AI 跑 Build。你來解難題。

Let AI handle the builds. You solve the hard parts.

本文相關的 AOSP build skill 已開源：github.com/alanhc/aosp-build