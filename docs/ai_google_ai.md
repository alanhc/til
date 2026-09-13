
https://labs.google.com/mariner/landing

https://jules.google/
antigravity
Google Antigravity 的語境中，task.md 通常是 Agent 在執行任務時自動產生的「任務說明文件」(Task Artifact)。
## task.md 的用途是什麼？

在 Antigravity 裡，每當你讓 Agent 做一個任務，例如：
「幫我加一個 API endpoint」

「把這個 UI 改成深色模式」

「在 README 裡加入安裝教學」

「重構這個專案的目錄結構」

系統會產生一個 任務工件 (Artifact)，其中最常見的就是 task.md。

🔍 task.md 通常包含：
1. 任務目的 / Goal

說明你要求 AI 做什麼，以及這項任務想達到的結果。

2. 需求與約束條件

例如：

必須保留相容性

不可修改某些檔案

要符合 lint 規範

需在 browser/terminal/mcp 完整執行

3. Agent 計畫 / Implementation Plan

AI 會列出：

要修改的檔案

要新增的檔案

要做的步驟

如何驗證結果

4. 成果摘要 / Task Output Summary

任務完成後，Agent 會寫入：

已完成哪些變更

產生哪些 artifacts（browser recordings、screenshots、diffs 等）

5. 待辦事項 / Remaining Work

如果任務尚未完成，會列出剩下的部分。

🧪 為什麼 Antigravity 會做 task.md？

因為 Google Antigravity 是「agent-first 的 IDE」。

每件事背後都會產生一個計畫＋追蹤文件：

方便你追蹤工作

讓 Agent 有上下文可繼續工作

便於審查與回溯

讓多個 Agent 能共同協作同一個任務

這比傳統「AI 直接修改檔案」更透明、更可控。

📂 task.md 通常出現在哪裡？

在每個 Agent 工作空間（Workspace）的 Task List 內。

你可以在：

Agent Side Panel

Task Manager

Artifacts 面板

看到 task.md。

```
# Task: Add Signup API Endpoint

## Goal
Implement a /signup endpoint with email + password validation.

## Plan
1. Create route in routes/auth.js
2. Add validation logic
3. Update OpenAPI schema
4. Write basic tests

## Output Summary
- Added new route
- Updated schema
- Tests pending

## Remaining Work
- Write full integration tests
```