---
title: 工具 / 其他 文章索引
sidebar_label: 工具與其他索引
sidebar_position: 8
---

# 工具 / 其他 文章索引

這是**雜項分類**：收的是不屬於 Android、Embedded、Linux、BMC 等其他八類的筆記——開發工具速查、雲端服務、自動化、資安、資料結構、side project 構想。性質偏向速查與隨手紀錄，篇幅落差很大，有幾篇目前仍是佔位頁（下表會逐一註明）。

---

## 一、開發工具與環境

| 文章 | 內容 |
|---|---|
| [Git 速查](../git.md) | 極短速查卡：`git diff` 的 `--stat`／`--cached`、`git reset`、`git commit` 的 `-s`（sign off）／`-m`／`--amend`，共約十行 |
| [Docker 網路除錯](../docker_debug_network.md) | 實戰全紀錄：忘記 ollama 由哪份 docker-compose 啟動，先用 `docker inspect -f '{{json .NetworkSettings.Networks}}'` 比對三個容器的網段，再讀 `com.docker.compose.project.config_files` label 反推專案路徑；接著改用 Caddy 當對外入口做 Bearer token 驗證（`openssl rand -base64 32` 產 token、ollama 本體不開 port），附 401／200 的 curl 驗證輸出 |
| [Ubuntu 常用指令](../ubuntu_cmds.md) | 速查：`ubuntu-drivers devices`／`autoinstall` 裝顯卡驅動、apt 套件管理（`sudo apt install <package>` 等）、systemctl 啟停服務與 `journalctl -u <service>` 看 log |
| [Ubuntu PPA 404 錯誤](../ubuntu_ppa_error.md) | 單一問題排除：`apt update` 出現 PPA `404 Not Found` 時，用 `grep -r` 在 `/etc/apt/sources.list.d/` 與 `sources.list` 找出已被移除或更名的 PPA，處理掉再更新 |
| [Obsidian](../obsidian.md) | local-first 的 markdown 筆記軟體：`[[筆記名稱]]` 雙向連結與反向連結、graph view、plugin 生態（Dataview／Templater／Excalidraw），檔案是本機純文字所以能直接 Git 版控 |
| [Chrome Extension 清單](../chrome_extension.md) | 純連結收藏，無說明文字：YouTube（DeepSRT、vidiq）、頁面（Smart TOC）、翻譯（Immersive Translate）、開發（Wappalyzer、Cookie-Editor）四類 |
| [畫圖／白板工具](../tool.md) | **注意與下一篇是不同檔案**。主題是線上白板：Miro（完整團隊協作平台、範本庫、適合 workshop／sprint planning）vs Excalidraw（開源輕量、手繪風、可自架），末尾有兩者取捨的一段比較 |
| [好用工具清單](../tools.md) | **與上一篇僅檔名相似，內容不重疊**。是一份泛用工具收藏：Screen Studio（螢幕錄影，自動縮放與滑鼠平滑，適合做 demo）、Timelinize（把照片／位置／社群資料匯整成本機時間軸） |

---

## 二、雲端與服務

| 文章 | 內容 |
|---|---|
| [Cloudflare Tunnel](../cloudflare.md) | 佔位性質，只有指令片段沒有說明：`cloudflared tunnel create` 建 tunnel → 編 `~/.cloudflared/config.yml` 的 ingress 規則（把網域導到 `localhost:3000`）→ `cloudflared tunnel route dns` 綁 DNS |
| [Supabase](../supabase.md) | 開源的 Firebase 替代方案：以 PostgreSQL 為核心，含 Row Level Security 控權、Auth（email／OAuth／magic link）、Storage、Realtime 訂閱、Deno 跑的 Edge Functions，並自動依資料表產生 REST／GraphQL API，附 Docker self-host 文件連結 |
| [Discord Bot 開發](../discord.md) | 開發前置：Developer Portal 建 Application 取 Bot Token、要開哪些 Privileged Gateway Intents（Message Content Intent 才讀得到訊息）、OAuth2 URL Generator 產邀請連結、discord.py／discord.js 選擇，以及現代做法用 Slash Commands 取代前綴指令 |
| [遠端 Server 控制方式](../remote_server_idea.md) | 草稿筆記：依情境挑做法——一次性小資料用 stdin pipe 或 ssh 帶 args、一堆檔案用 rsync、頻繁讀寫同一份用 sshfs 或 ControlMaster + scp、兩邊程式要互相讀寫則 SSH port forward + Redis/sqlite |

---

## 三、自動化與爬蟲

| 文章 | 內容 |
|---|---|
| [Automation（n8n 試作）](../automation.md) | 零散實驗筆記：用 n8n 拿財經號角與股癌做摘要測試，摘要用 Claude API、YouTube 直接抓字幕、Apple Podcast 抓音檔後用 whisper 轉文字；誠實記下缺點是「拆不夠細」，另附 Dify 與 Agent Builder 連結 |
| [用 n8n 自動總結 YouTube 影片](../n8n/youtube總結.md) | 把上篇整理成流程：觸發（手動輸入網址或 Schedule／RSS 監看頻道）→ 取字幕／transcript → 丟 LLM 節點產生摘要 → 輸出到 email／Notion／Discord／Telegram，含一張流程截圖 |
| [網路爬蟲](../crawler.md) | 概念釐清 crawler（走訪連結、廣度探索）vs scraper（擷取結構化資料）、`robots.txt` 與 rate limit 的分寸、JS 動態網站需 headless browser；工具面介紹 Apify 的 Actor 模式、現成 Actor、proxy／排程／API，以及其維護的開源 Crawlee |

---

## 四、資安

| 文章 | 內容 |
|---|---|
| [promptfoo（LLM 測試工具）](../security.md) | 單一工具筆記：開源的 LLM 應用評測與紅隊測試工具——用 YAML 定義測試案例與 assertion 對多組 prompt／模型／參數做批次比較並接 CI 做回歸，紅隊面則自動產生對抗性輸入測 prompt injection、jailbreak、資料外洩 |
| [CausalArmor 論文導讀](../security_paper_CausalArmor.md) | **長篇深入導讀，寫給主管／決策者**：間接提示注入（IPI）為何是「AI 忠實執行讀到的指令」而非被駭、防禦本身造成的「過度防禦困境」；CausalArmor 用 Leave-One-Out 消融量測「主導權翻轉」（Dominance Shift）、可調門檻 `τ` 作為風險旋鈕、針對性清洗與回溯式思維鏈遮蔽（不抹掉推理軌跡會讓模型把攻擊再幻覺一次）；含 DoomArena 數據表（不防禦時攻擊成功率 88.9%、分類器把正常任務成功率砍到 55.1%、CausalArmor 為 3.7%／71.0%），並誠實列出 split-context 拆分攻擊等自承弱點與最小權限建議 |

---

## 五、資料結構與演算法（DSA）

| 文章 | 內容 |
|---|---|
| [Single Linked List](../DSA/Linked_List/0.linked_list.md) | **本系列主線**：用 `main.c`／`list.h`／`list.c` 三檔從零實作，先解釋 dummy head node 為何能省掉空串列特判（附 ASCII 對照圖）；完整 C 實作涵蓋 insert_head／insert_tail、delete_node、fast-slow pointer 找中間節點、delete_dup、swap（含相鄰節點特例）、reverse、reverseK 分組反轉、帶 comparator function pointer 的 merge sort，末尾附 `gcc -Wall` 編譯與執行輸出 |
| [Doubly Linked List](../DSA/Linked_List/1.double_linked_list.md) | prev／next 雙指標結構、已知節點指標時插入刪除為 O(1)（single list 得先找前驅）、哨兵節點簡化邊界；附與 array 的四項比較表（隨機存取／插入刪除／記憶體 cache friendly／動態成長），結論是適合 LRU cache、deque |
| [LeetCode 題目清單](../DSA/Linked_List/2.leetcode.md) | **佔位頁**：只有六行題號（2095、82、24、25、2487、23），對應主線實作的各項操作，尚無任何解題內容或說明 |
| [Linux Kernel Linked List](../DSA/Linked_List/3.linux_linked_list.md) | kernel 的 `list_head` 為何是 intrusive／doubly／circular：結構內嵌使用者 struct 因此同一結構可掛多個串列、環狀讓插刪不必特判 NULL、空串列即 `head->next == head`；`container_of` 如何由成員指標回推外層 struct，以及 `list_add`／`list_del`／`list_for_each_entry` 等巨集與「走訪中刪除要用 `_safe` 版本」的原因 |
| [Binary Tree](../DSA/Tree/binary_tree.md) | 節點結構與四種走訪（preorder／inorder／postorder／level order，並點出 BST 中序走訪得遞增序列、前三者可遞迴或用 stack、層序用 queue），附 invert binary tree 的遞迴 C 實作與 O(n)／O(h) 複雜度 |
| [Heap](../DSA/Tree/heap.md) | max／min heap 的 heap property、因為是完全二元樹所以用 array 實作及 parent／left／right 的索引公式、peek／push／pop／build heap 複雜度表、sift-up 與 sift-down 的動作、heapify 從 `n/2 - 1` 往前為何是 O(n)；並延伸到 priority queue 應用（Dijkstra、Prim、Huffman、top-k）與 heap sort |
| [Boyer-Moore 投票法](../dsa_Boyer-Moore.md) | 找多數元素（出現 > n/2 次）的 O(n) 時間／O(1) 空間演算法：維護 `candidate` + `count` 兩兩對消、正確性直覺（多數元素抵消完必有剩）、需否二次遍歷驗證，附 Python 實作與逐步走表；經典題 LeetCode 169，進階 229（> n/3 維護兩個候選人） |

---

## 六、Side Projects

| 文章 | 內容 |
|---|---|
| [用問卷找回你的時間精力](../side-projects/用問卷找回你的時間精力.md) | 已有 demo：用簡短問卷收集各活動的時間投入與精力感受（充電／耗電），視覺化後看出哪些活動 CP 值低，目標是把「感覺很忙但沒成就感」轉成可行動的調整建議 |
| [緩解焦慮 App（呼吸日記）](../side-projects/緩解焦慮app.md) | 已有 demo：2／5／8 分鐘三種放鬆時長、圓圈呼吸動畫與語音引導，結束後替情緒命名、寫下感受與一個願意走的小步驟；紀錄只存本機、不需帳號不上雲，可回顧哪個日期／每週區間較焦慮，含三張介面截圖 |
| [評論音樂段落](../side-projects/評論音樂段落.md) | **僅構想稿**（三行概念，尚未實作）：讓使用者針對歌曲特定 timestamp 區間（如 1:20–1:45）留言而非只給整首評分，累積後看出最打動人的段落，類似 SoundCloud 波形留言但聚焦段落級分析 |

---

## 七、其他

| 文章 | 內容 |
|---|---|
| [Data Viz](../data_viz.md) | 三種圖表的零散筆記：Sankey diagram 的節點／流結構與 plotly `go.Sankey` 能源流向範例（並提醒不適用於沒有「守恆」概念的資料）、Chord diagram 強調雙向關係與 Sankey 的差異、Treemap 僅一張截圖 |
| [軟體工程隨筆](../software_engineering.md) | 隨手速記（原文有錯字未修）：sustainability 與 scale 是核心議題、海勒姆法則（被觀察到的行為終將被依賴成為系統的一部分）、「Because I said so」是萬惡之源、公車指數，以及 CI 的 Beyoncé rule |
| [Preflight Check](../preflight.md) | **佔位頁**：同一段 preflight check 的定義被 LLM 以英文／簡體中文／繁體中文各寫一次（航空、軟體開發、韌體開發的類比），尚未整理成自己的筆記 |

---

## 建議閱讀順序

這一類多半是速查，可各取所需。唯一有明顯先後的是 DSA 的 linked list 主線：

```
Single Linked List          ← 主線，從零實作與各種操作
   → Doubly Linked List     ← 多一個 prev 指標換來什麼
   → Linux Kernel Linked List  ← 真實世界怎麼做：intrusive + circular
   → LeetCode 題目清單      ← 拿題目對照練（目前僅題號）
```
