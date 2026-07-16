---
title: 知識地圖
sidebar_label: 知識地圖（總表）
sidebar_position: 0
---

# 知識地圖

整個知識庫的入口。文章依主題分成九類，每類會逐步長出自己的**文章索引**與**名詞表**。

四個技術大類（Android、AI、BMC、Embedded）已有索引或名詞表，其餘標「待建」——等該類文章累積到「靠側邊欄找不到東西」的程度再補，不預先建空殼。

## 分類總表

| 分類 | 內容 | 起點 | 索引 | 名詞表 |
|---|---|---|---|---|
| **Android / Pixel** | AOSP 建置、boot flow、TF-A、Pixel 刷機、SELinux、Root | [android.md](../android.md) | [Android 系列索引](android_index.md) | [Android 名詞表](android_glossary.md) |
| **AI / Agent** | Claude Code / Skills、MCP、Gemini、本地推論（Ollama、Jan AI）、AI 應用與文章 | [AI.md](../AI.md) | [AI 系列索引](ai_index.md) | [AI 名詞表](ai_glossary.md) |
| **BMC** | OpenBMC、CanopyBMC、IPMI / Redfish、sensor / thermal、Yocto | [BMC/openbmc_boot_flow.md](../BMC/openbmc_boot_flow.md) | [BMC 系列索引](bmc_index.md) | [BMC 名詞表](bmc_glossary.md) |
| **Linux / 系統** | Kernel、device tree / driver、systemd、memory、Ubuntu 指令、GRUB、Docker | [Linux/Linux.md](../Linux/Linux.md) | 走 `Linux/` 資料夾側邊欄 | 待建 |
| **Embedded / 韌體 / 硬體** | Bootloader、firmware testing / image management、Raspberry Pi、晶片與半導體 | [embedded.md](../embedded.md) | [Embedded 系列索引](embedded_index.md) | — |
| **效能 / Benchmark** | CPU DVFS、power / browser benchmark、codec 判讀 | [benchmark.md](../benchmark.md) | 待建 | — |
| **投資 / 理財** | 投資計劃、個股風險、程式交易、酒田戰法、房、銀行操作 | [投資.md](../投資.md) | 待建 | — |
| **職涯 / 生活 / 學習** | 面試、當責、說不、人際、健康、簡報、英文、書與電影 | [career.md](../career.md) | 待建 | — |
| **工具 / 其他** | Obsidian、Supabase、Cloudflare、n8n、爬蟲、DSA、資安、side projects | [tools.md](../tools.md) | [工具與其他索引](tools_index.md) | — |

篇數量級：BMC ≈ 40、AI ≈ 35、Android ≈ 25、工具其他 ≈ 25、職涯生活 ≈ 19、Embedded ≈ 15、Linux ≈ 12、投資 ≈ 9、效能 ≈ 7。

## 索引與名詞表的分工

兩者刻意分開，因為回答的是不同問題：

- **索引（`<主題>_index.md`）**——「這個主題有哪些文章、我該從哪篇開始讀？」依子主題分節的文章清單，每篇一句話說明內容，最後附建議閱讀順序。
- **名詞表（`<主題>_glossary.md`）**——「這個縮寫是什麼意思？在哪篇有講？」名詞定義加上出處連結，讓你從一個陌生的詞反查回原始筆記。

## 為什麼需要這層

大部分筆記平鋪在 `docs/` 根目錄（約 130 篇），側邊欄只能給你一長串檔名。索引與名詞表補上檔名給不了的東西：主題分組、閱讀順序、以及從名詞反查文章的能力。

## 維護慣例

- 新增索引／名詞表時放這個資料夾，命名為 `<主題>_index.md` 與 `<主題>_glossary.md`，並在上面的總表補一列。
- 從這裡連到根目錄的筆記要用相對路徑（`../xxx.md`）。`onBrokenMarkdownLinks: 'throw'` 會讓連結錯誤直接 build 失敗。
- 有些文章跨分類（ATF 同屬 Android 與 Embedded、`ai_bmc.md` 同屬 AI 與 BMC）。總表只指向各類索引，不列個別文章，所以重複歸類的問題留給各類索引自己決定。
