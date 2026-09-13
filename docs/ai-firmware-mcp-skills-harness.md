# AI 輔助韌體開發：MCP、Skills 與 Harness 的三層拆解

> **本文引用原則**
> 文中所有量化數據都標註來源，可回溯至公開論文、官方規格或郵件列表。
> 標示 **［推論］** 的段落是我從這些事實推導出的判斷，不是被驗證過的結論。
> 所有程式碼範例都在本機實際執行過，輸出即文中所貼。
> 內容全部取自公開資料，不涉及任何雇主內部資訊。

---

## TL;DR

- 韌體開發的困難點不在模型不會寫 C，而在於**回饋迴圈昂貴、ground truth 不在原始碼裡**。
- `Agent = Model + Harness`。同一個模型換一套 harness，排名可以從 Top 30 跳到 Top 5（[Osmani, 2026](https://addyosmani.com/blog/agent-harness-engineering/)）。韌體場景的落差幾乎全部在 harness 這一側。
- 三層分工：**MCP 提供能力**（把 build/flash/console/verifier 變成可呼叫的動作）、**Skills 提供程序知識**（把資深工程師腦裡的分流流程寫成檔案）、**Harness 提供迴圈與約束**（預算、閘門、驗證、評估）。
- 最反直覺的一個數字：把萬能 shell 換成三個語意明確的專用 tool，Android build 修復率從 65.1% 提升到 81.4%（[AndroidBuildBench, 2025](https://arxiv.org/abs/2510.08640)）。**工具設計比模型選擇更能決定成敗。**
- 最該記住的一個數字：kernel crash 修復實驗中，74% 的 patch 讓 crash 消失，但只有約 20% 與開發者的真實修法等價（[Live-kBench, 2026](https://arxiv.org/html/2602.02690)）。**「build 過了」「不 crash 了」不等於「修對了」。**
- **除錯**（第 6.5 節）是韌體場景裡 harness 差距最大的一塊：不要把 GDB 原樣接給 agent，要接「一次跑完、回傳自足摘要」的函式層級介面——這個設計換來 6.2%–18.5% 的解決率提升（[ADI, 2026](https://arxiv.org/html/2604.24212)）。

---

## 1. 韌體為什麼是 AI 輔助的困難場景

先講清楚困難在哪，後面三層架構的每一個設計才有理由。

### 1.1 Ground truth 不在原始碼裡

Web 後端的正確性大致可以從程式碼與測試推導出來。韌體不行。一個 driver 讀對了暫存器、通過了編譯、通過了單元測試，接到真板子上仍然可能因為 clock domain 沒開、power sequence 差 2ms、或 device tree 的 `reg` 少填一個 range 而掛掉。

Espressif 在 2026 年一篇談用 AI 開發 Zephyr 應用的文章裡把這件事講得很直接：**「UART 才是 ground truth」**（UART as ground truth），驗證正確性要靠 trace 與實機證據，不能只靠檢視原始碼（[Espressif Developer Portal, 2026-06](https://developer.espressif.com/blog/2026/06/zephyr-coding-with-ai/)）。

**含意**：任何不能讓 agent 讀到實機輸出的 harness，本質上是在讓模型憑空猜測。

### 1.2 回饋迴圈的成本是好幾個數量級

| 場景 | 一次迴圈成本 |
|---|---|
| 前端專案 | `npm test`，秒級 |
| 一般後端 | CI，分鐘級 |
| AOSP full build | 30–90 分鐘，且要佔一台大機器 |
| Kernel + flash + boot | 建置 10–40 分鐘，燒錄與開機數分鐘，且要佔一塊實體板子 |

Agent 的典型工作模式是「試、失敗、再試」。當單次嘗試成本是一小時而不是一秒，**「讓 agent 多試幾次」這個策略在經濟上直接破產**，必須用預算、分流與靜態閘門把無效嘗試在進入 build 之前就攔掉。

### 1.3 錯誤訊號稀疏、跨層、而且量體巨大

一份 AOSP build log 動輒數十萬行；一次 kernel panic 的 dmesg 混雜了無關子系統的訊息。同一個根因會在下游產生數百條看似不同的錯誤。

把原始 log 丟進 context 是最常見也最昂貴的錯誤：既燒掉 context window，又讓真正的訊號被雜訊稀釋。

### 1.4 有些操作是不可逆的

`git push --force`、燒錄到錯誤的板子、覆寫別人正在用的 lab 資源、寫壞 bootloader 讓板子變磚。這些不是「重跑一次就好」的錯誤。

**［推論］** 這四點合起來解釋了為什麼「把 Claude Code 打開、指到 kernel tree、叫它修 bug」在韌體場景幾乎不會有好結果：不是模型不夠強，是缺了外面那一整圈。

---

## 2. 名詞定位：Agent = Model + Harness

在談三層架構之前，先把名詞定義清楚，因為這三個詞在中文社群裡經常被混用。

Addy Osmani 的定義最精簡：**「Agent = Model + Harness。如果你不是模型，你就是 harness。」** Harness 指的是模型外面的一切——system prompt 與知識檔案、tool 基礎設施、執行環境、編排邏輯、強制機制（hooks、middleware、compaction）、可觀測性（[Osmani, 2026](https://addyosmani.com/blog/agent-harness-engineering/)）。

他引用的一個對照很有說服力：在 Terminal Bench 2.0 上，同一個 Claude Opus 4.6 在不同 harness 裡的分數差距顯著；有團隊**只換 harness** 就從 Top 30 進到 Top 5。他的結論是「一個普通模型配好 harness，勝過一個好模型配爛 harness」。

那 MCP 與 Skills 在哪裡？兩者都是 harness 的組成部分，但解決的問題不同：

| | 解決什麼問題 | 形式 | 何時載入 |
|---|---|---|---|
| **MCP** | Agent **能做什麼**——把外部世界的動作變成可呼叫的介面 | 執行中的 server（stdio / HTTP） | tool schema 常駐在 context |
| **Skills** | Agent **該怎麼做**——把程序性知識與判斷準則變成檔案 | 檔案系統上的目錄（`SKILL.md` + 資源） | 三層漸進揭露 |
| **Harness** | Agent **在什麼約束下反覆做**——迴圈、預算、閘門、驗證 | 你自己寫的編排程式碼 | 全程 |

一個實用的判準：

- 需要**跨進程/跨機器**的能力（燒錄、控制電源、跑 solver、查資料庫）→ **MCP**
- 需要**流程與禁則**（先分類再修、不准放寬 `-Werror`）→ **Skills**
- 需要**強制執行**（違反禁則就攔下來、超過預算就停）→ **Harness**

**關鍵原則**：Skills 寫的規則是「建議」，模型可能不遵守；Harness 的閘門才是「強制」。安全相關的限制一定要放在 harness 或 tool 層，不能只寫在 prompt 或 SKILL.md 裡——因為 prompt 層的限制對 prompt injection 沒有任何防禦力。

---

## 3. 第一層：MCP —— 把韌體世界的介面變成 tool

### 3.1 目前的規格狀態（2026-07-28）

MCP 在 2026-07-28 版做了相當大幅的改動，其中幾項直接影響韌體 lab 的設計（[MCP Blog, 2026-07-28](https://blog.modelcontextprotocol.io/posts/2026-07-28/)）：

- **協定轉為 stateless**：移除 `initialize`/`initialized` 交握與 `Mcp-Session-Id` header，讓 server 可以在多個實例間做負載平衡而不需共享儲存。
- **Multi Round-Trip Requests (MRTR)**：server 可以在一次呼叫進行中反向向 client 要確認或補參數，不需要維持雙向長連線。
- **Tasks extension 正式化**：以 `tasks/get` / `tasks/update` 輪詢處理長時間工作。
- **Header-based routing**：method 與 tool 名稱改走 `Mcp-Method` / `Mcp-Name` HTTP header，讓 gateway 不必解析 JSON body 就能路由。
- **Cacheable list responses**：tools/prompts/resources 清單可帶 `ttlMs` 與 `cacheScope`。
- **授權強化**：要求 RFC 9207 issuer validation；正式棄用 Dynamic Client Registration，改用 Client ID Metadata Documents。
- **棄用**：Roots、Sampling、Logging 進入至少 12 個月的過渡期；HTTP+SSE 舊傳輸正式棄用。

對韌體 lab 的三個具體含意：

1. **stateless 意味著板子的擁有權必須自己顯式建模。** 以前可以偷懶把「這個 session 佔用了 board-03」放在連線狀態裡，現在必須做成明確的租約（lease）資源。
2. **Tasks extension 天生適合 build 與 flash。** 一次 AOSP build 30 分鐘，不該用一個同步 tool call 硬撐。
3. **MRTR 讓「燒錄前請人類確認」變得可實作**，而不必把確認邏輯外包給 client 的 UI。

### 3.2 設計原則：少而準，而不是萬能

這是本文最想強調的一點，而且有硬數據支撐。

[AndroidBuildBench / GradleFixer](https://arxiv.org/html/2510.08640v3)（1,019 個可重現的 build 失敗、43 個開源 Android 專案）做了一個直接的對照實驗。他們定義的問題叫**「reasoning–execution gap」**：模型知道該怎麼修，但透過通用 shell 執行時做不出來。

解法是把通用 shell 換成三個語意明確的 tool：`run_build`、`run_gradle`、`change_java_version`。

| 設定 | Pass@1 |
|---|---|
| GradleFixer（專用 tool） | **81.4%** |
| Gemini-CLI + shell | 65.1% |
| Coding-Assistant baseline | 30.2% |

消融實驗更能說明問題——**工具越專用，表現越好**：

| 提供的 tool | Pass@1 |
|---|---|
| `run_build`（最專用） | **63.4%** |
| `run_gradle`（較通用） | 55.8% |
| 只有 shell（最通用） | 54.3% |

**［推論］** 這個結果可以這樣理解：通用 shell 把「決定要下什麼指令」的負擔完全丟給模型，而這正是模型在陌生建置系統裡最容易出錯的地方。專用 tool 等於把資深工程師的知識編碼進了介面本身。

我從中導出三條 tool 設計規則：

1. **一個 tool = 一個工程師會做的動作**，不是一個 shell 指令。
2. **回傳結構化摘要，不回傳原始輸出。** 原始 log 落地成檔案，只回 path；agent 需要細節時再自己去讀那個檔案。
3. **破壞性操作預設關閉。** 這一點 [labgrid-mcp](https://github.com/onurcelep/labgrid-mcp) 做得很好：它把 47 個 tool 分成讀取、租用、driver、console、SSH、flash、metadata、刪除等類別，其中 **flash 與 place 刪除兩類預設停用**，必須由人類設定 `LABGRID_MCP_ALLOW` 才啟用；另有 `LABGRID_MCP_READONLY` 模式。

### 3.3 可跑的範例：`fw-lab-mcp`

以下是一個把上述原則落實的最小 MCP server。它用官方 Python SDK（`mcp` 1.27.0），在我的環境實際跑過。

```python
#!/usr/bin/env python3
"""fw-lab-mcp — 把韌體 lab 的操作介面包成 MCP tools。"""
from __future__ import annotations
import os, re, subprocess, time, uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("fw-lab")

# --- 安全閘門：破壞性動作預設關閉 -----------------------------------------
ALLOW = set(os.environ.get("FW_LAB_ALLOW", "").split(","))
LOG_DIR = Path(os.environ.get("FW_LAB_LOGS", "/tmp/fw-lab-logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
MAX_INLINE_CHARS = 4000          # 單次 tool 回傳的 token 預算上限


# --- 狀態：板子租用（stateless 協定下必須顯式建模）------------------------
@dataclass
class Lease:
    board: str
    token: str
    expires_at: float

_LEASES: dict[str, Lease] = {}

def _check_lease(board: str, token: str) -> None:
    lease = _LEASES.get(board)
    if lease is None or lease.token != token:
        raise ValueError(f"board {board!r} 未被此 token 租用；請先呼叫 acquire_board")
    if lease.expires_at < time.time():
        del _LEASES[board]
        raise ValueError(f"board {board!r} 的租約已過期，請重新 acquire_board")


# --- 結構化回傳型別 --------------------------------------------------------
class BuildResult(BaseModel):
    ok: bool
    duration_s: float
    log_path: str = Field(description="完整 log 落地路徑，agent 需要細節時再自己讀")
    error_count: int
    first_errors: list[str] = Field(description="前 N 筆錯誤，已去重")
    hint: str | None = None
```

真正的重點在這個摘要函式。它處理的是「同一個根因產生數百條錯誤」的問題：

```python
ERROR_PAT = re.compile(
    r"^(?P<file>[^\s:]+):(?P<line>\d+):(?:\d+:)?\s*(?:fatal\s+)?error:\s*(?P<msg>.+)$"
)

def _summarize_build_log(text: str, keep: int = 5) -> tuple[int, list[str], str | None]:
    """把幾萬行的 build log 壓成 agent 讀得動的東西。"""
    seen: dict[str, str] = {}
    for line in text.splitlines():
        m = ERROR_PAT.match(line.strip())
        if m:
            # 用「訊息樣板」去重：同一個 error 出現在 300 個檔案只算一類
            key = re.sub(r"'[^']*'", "'…'", m.group("msg"))
            seen.setdefault(key, line.strip())
    errors = list(seen.values())
    hint = None
    joined = " ".join(seen.keys())
    if "undefined reference" in joined or "undefined symbol" in joined:
        hint = "link 階段失敗：優先檢查 Kconfig/EXPORT_SYMBOL 與 module 相依，而不是改呼叫端。"
    elif "No such file or directory" in joined:
        hint = "缺 header：先確認 include path 與 device tree / vendor overlay 是否同步。"
    return len(errors), errors[:keep], hint
```

實測：丟進 300 行「同一個 implicit declaration 出現在不同行號」加上 1 行 link 錯誤，輸出是：

```
(2, ["drivers/gpu/vdisp_ovl.c:1:12: error: implicit declaration of function 'vdisp_ovl_layer_on'",
     "drivers/soc/vsoc_pm.c:44:1: error: undefined reference to 'vsoc_pm_get'"],
 'link 階段失敗：優先檢查 Kconfig/EXPORT_SYMBOL 與 module 相依，而不是改呼叫端。')
```

**301 行壓成 2 類。** 這一步省下的 context，比換一個更大的模型有用得多。

接著是四個動作 tool。注意閘門的位置：

```python
@mcp.tool()
def acquire_board(board: str, minutes: int = 30) -> dict:
    """租用一塊實體板子，取得後續操作所需的 token。

    MCP 2026-07-28 之後協定本身是 stateless 的，跨實例的板子擁有權
    必須由 server 自己顯式建模，不能再依賴 session id。
    """
    now = time.time()
    lease = _LEASES.get(board)
    if lease and lease.expires_at > now:
        raise ValueError(f"board {board!r} 目前已被租用，剩餘 {int(lease.expires_at - now)}s")
    token = uuid.uuid4().hex[:12]
    _LEASES[board] = Lease(board=board, token=token, expires_at=now + minutes * 60)
    return {"board": board, "lease_token": token, "expires_in_s": minutes * 60}


@mcp.tool()
def build_kernel(tree: str, defconfig: str,
                 target: Literal["kernel", "dtbs", "modules"] = "kernel",
                 jobs: int = 16) -> BuildResult:
    """在指定 tree 上做一次 kernel build，回傳結構化的失敗摘要（不是原始 log）。

    刻意不提供通用 shell：GradleFixer 的實驗顯示，語意明確的專用 tool
    比 shell 高出十幾個百分點的修復率（81.4% vs 65.1%）。
    """
    t0 = time.time()
    log_path = LOG_DIR / f"build-{int(t0)}-{target}.log"
    proc = subprocess.run(["make", f"-j{jobs}", f"O=out/{defconfig}", target],
                          cwd=tree, capture_output=True, text=True)
    text = proc.stdout + proc.stderr
    log_path.write_text(text)
    n_err, first, hint = _summarize_build_log(text)
    return BuildResult(ok=proc.returncode == 0, duration_s=round(time.time() - t0, 1),
                       log_path=str(log_path), error_count=n_err,
                       first_errors=first, hint=hint)


@mcp.tool()
def flash_target(board: str, lease_token: str, image: str,
                 method: Literal["fastboot", "dfu"] = "fastboot") -> dict:
    """把 image 燒進板子。破壞性動作，預設關閉。

    需要 FW_LAB_ALLOW=flash 才會啟用。這個閘門在 tool 層而不是 prompt 層，
    因為 prompt 層的限制對 prompt injection 沒有防禦力。
    """
    if "flash" not in ALLOW:
        raise PermissionError("flash 未啟用。請由人類設定 FW_LAB_ALLOW=flash 後重啟 server。")
    _check_lease(board, lease_token)
    if not Path(image).is_file():
        raise FileNotFoundError(image)
    return {"board": board, "image": image, "method": method, "status": "flashed"}


@mcp.tool()
def console_read(board: str, lease_token: str, seconds: int = 10,
                 grep: str | None = None) -> ConsoleChunk:
    """讀取 UART console。UART 才是韌體的 ground truth，原始碼不是。"""
    _check_lease(board, lease_token)
    log_path = LOG_DIR / f"console-{board}-{int(time.time())}.log"
    raw = _read_serial(board, seconds)        # 實作上接 labgrid / pyserial
    log_path.write_text(raw)
    lines = raw.splitlines()
    if grep:
        pat = re.compile(grep)
        lines = [l for l in lines if pat.search(l)]
    text = "\n".join(lines)
    truncated = len(text) > MAX_INLINE_CHARS
    if truncated:
        text = text[:MAX_INLINE_CHARS] + f"\n…（已截斷，完整內容見 {log_path}）"
    return ConsoleChunk(board=board, lines=len(lines), truncated=truncated,
                        log_path=str(log_path), text=text)
```

實測輸出（`console_read` 帶 `grep="Call trace|NULL"`）：

```json
{
  "board": "vsoc-evb-03",
  "lines": 2,
  "truncated": false,
  "log_path": "/tmp/fw-lab-logs/console-vsoc-evb-03-1788665477.log",
  "text": "[    2.881003] Unable to handle kernel NULL pointer dereference at 0000000000000018\n[    2.881120] Call trace:"
}
```

用錯的 lease token 呼叫 `flash_target`：

```
ToolError: Error executing tool flash_target: board 'vsoc-evb-03' 未被此 token 租用；請先呼叫 acquire_board
```

### 3.4 不必重造輪子：既有的韌體 MCP server

如果你的 lab 已經跑 labgrid，[labgrid-mcp](https://github.com/onurcelep/labgrid-mcp) 直接透過 gRPC 接上 coordinator（labgrid 24+），提供電源、console、I/O、SD/USB mux、flash、SSH forward 等 47 個 tool，並內建前述的 opt-in 安全設計。

單板 SWD/JTAG 場景則有 [embedded-debugger-mcp](https://github.com/adancurusul/embedded-debugger-mcp)，透過 probe-rs 或 OpenOCD 支援 ARM Cortex-M、RISC-V 與 Xtensa（ESP32），並提供 crash 診斷。

**［推論］** 我的建議是：lab 控制層直接用這些現成的，自己寫的 MCP server 應該專注在你們**內部特有**的東西——內部 build 系統、內部 log 格式、內部 issue tracker。這才是外面的人做不了、而回報最高的部分。

---

## 4. 第二層：Skills —— 把只存在資深工程師腦裡的流程變成檔案

### 4.1 格式與漸進揭露

Agent Skills 是檔案系統上的一個目錄，核心是 `SKILL.md`，YAML frontmatter 只有兩個必填欄位（[Claude Platform Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)）：

| 欄位 | 限制 |
|---|---|
| `name` | ≤ 64 字元，小寫字母／數字／連字號 |
| `description` | 非空、≤ 1024 字元，**必須同時說明「做什麼」與「何時用」** |

真正重要的是三層漸進揭露的 token 經濟學：

| 層級 | 內容 | 何時載入 | Token 成本 |
|---|---|---|---|
| L1 | frontmatter（`name` + `description`） | 啟動時常駐 | 每個 skill 約 100 tokens |
| L2 | `SKILL.md` 本文 | 被觸發時 | 建議 < 5k tokens |
| L3 | 額外 markdown、腳本、schema、範本 | 需要時才讀 | 未存取即為 0；**腳本只載入輸出，不載入程式碼** |

最後那一句是重點：**把確定性的邏輯寫成 L3 腳本，agent 只看到執行結果，程式碼本身完全不佔 context。**

### 4.2 為什麼分類要用腳本而不是模型

這是一個實務上很容易搞錯的決策。

分類 build 失敗這件事需要「同一份 log 每次得到同一個答案」。LWN 對 Sashiko（kernel patch 的 LLM 審查系統）的報導明確指出：**它的輸出是機率性的，連續兩次執行會得到不同結果**，而這造成開發者在迭代 patch 時的不可預測性（[LWN.net](https://lwn.net/Articles/1073583/)）。

**［推論］** 因此我的分工是：**分類用腳本（要確定性），修補用模型（要創造性）**。腳本負責把問題導向正確的分支，模型只在真正需要判斷力的那個分支裡工作。

### 4.3 可跑的範例：`aosp-build-triage` skill

目錄結構：

```
skills/aosp-build-triage/
├── SKILL.md                        # L2：流程與禁則
├── references/
│   └── taxonomy.md                 # L3：完整分類定義
└── scripts/
    └── classify_build_log.py       # L3：確定性分類器
```

`SKILL.md`：

```markdown
---
name: aosp-build-triage
description: Triage Android/AOSP and kernel build failures into an actionable owner + next step. Use when a soong/ninja/kbuild log fails, when CI reports a broken build, or when deciding whether a failure is code, config, environment, or infrastructure.
---

# AOSP / Kernel Build Triage

## 第一原則

**先分類，再修。** 大部分 build 失敗不是「改這一行程式」能解決的；
在分類出擁有者之前就開始改 code，是 agent 最常見的失敗模式。

## 流程

1. **不要把整份 log 讀進 context。** 先跑分類器：

   ```bash
   python scripts/classify_build_log.py <log_path> --json
   ```

   它回傳 `{category, confidence, owner, evidence, next_action}`。
   只有在 `confidence < 0.6` 時才去讀 log 原文，且用 `grep -n` 取前後 20 行。

2. **依 category 分流**（完整定義見 `references/taxonomy.md`）：

   | category | 誰的問題 | 你該做的事 |
   |---|---|---|
   | `env` | 建置環境 | 回報環境，**不要**改 source |
   | `infra` | CI / 網路 / repo sync | 重跑一次確認可重現，再回報 |
   | `config` | Kconfig / soong / DT | 改 config，不要改呼叫端 |
   | `api-break` | 上游或跨模組 | 找出引入的 commit，通知該模組 owner |
   | `code` | 這次改動 | 才進入修補迴圈 |

3. **只有 `code` 類別可以進入修補。** 其他類別產出報告就停。

4. **修補後必須重建驗證。** 沒有重建成功的修補不算完成，不要回報「應該可以了」。

## 硬性限制

- 不要為了讓 build 過而 `#if 0`、註解掉呼叫、或放寬 `-Werror`。
  這類修補在 review 一定會被打回，且會掩蓋真正的缺陷。
- 不要跨模組修改來繞過 API 變更；先確認上游意圖。
- 每次只改一件事，改完就重建。同時改三個地方會讓你無法歸因。
```

分類器的核心（L3，不佔 context）：

```python
RULES = [
    # (category, weight, pattern, owner, next_action)
    ("env", 3.0, r"(?i)unsupported java version|JAVA_HOME|python3?: command not found|No space left on device",
     "build-infra", "回報建置環境，不要改 source"),
    ("infra", 3.0, r"(?i)(repo sync|git fetch).*(fail|timeout)|Connection reset|502 Bad Gateway|Killed signal 9",
     "ci-oncall", "重跑一次；可重現才升級"),
    ("config", 2.0, r"(?i)undefined reference to|undefined symbol:|implicit declaration of function",
     "module-owner", "檢查 Kconfig / Android.bp 相依與 EXPORT_SYMBOL"),
    ("api-break", 2.5, r"(?i)too few arguments to function|conflicting types for|incompatible pointer type",
     "upstream-owner", "git log -S 定位引入 commit，通知上游"),
    ("code", 1.0, r"(?i)^\S+\.(c|cc|cpp|java|kt|rs):\d+:\d*:?\s*(fatal )?error:",
     "you", "進入修補迴圈，一次只改一處"),
]

def classify(text: str) -> dict:
    scores, evidence, meta = Counter(), {}, {}
    for line in text.splitlines():
        s = line.strip()
        for cat, w, pat, owner, action in RULES:
            if re.search(pat, s, re.MULTILINE):
                scores[cat] += w
                evidence.setdefault(cat, s[:200])
                meta[cat] = (owner, action)
    ...
    # api-break 的訊號蓋過 code：多檔案同型錯誤代表介面變了
    files = {m.group("file") for m in FILE_ERR.finditer(text)}
    if scores.get("api-break") and len(files) >= 3:
        scores["api-break"] += 2.0
    ...
```

那條加權規則是把工程師的直覺編碼進來：**四個不相干的檔案同時報同一種錯，那不是你的 code 壞了，是介面變了。**

實測四種 log：

```
== samples/api-break.log
{ "category": "api-break", "confidence": 0.75, "owner": "upstream-owner",
  "evidence": "drivers/gpu/drm/vsoc/vdisp_ovl.c:412:9: error: too few arguments to function 'vdisp_comp_init'",
  "affected_files": ["…vdisp_ovl.c", "…vdisp_rdma.c", "…vdisp_dpi.c", "…vdisp_dsi.c"],
  "next_action": "git log -S 定位引入 commit，通知上游" }

== samples/config.log
{ "category": "config", "confidence": 1.0, "owner": "module-owner",
  "evidence": "vsoc-pm-domains.c:(.text+0x1a4): undefined reference to `vsoc_smi_larb_get'",
  "next_action": "檢查 Kconfig / Android.bp 相依與 EXPORT_SYMBOL" }

== samples/env.log     → category=env,   exit=2（不進修補迴圈）
== samples/infra.log   → category=infra, exit=2（不進修補迴圈）
```

注意那個 **exit code 2**：`env` 與 `infra` 直接以非零退出，harness 據此停止，agent 連一行程式碼都不會碰到。

### 4.4 Skill 的另一個用途：累積失敗記憶

Espressif 那篇文章提到一個我覺得被低估的實務：維護一份 `journal.md` 記錄「troubleshooting 與 regression avoiders」，並且警告**不要在「整理專案」時把 debug journal 清掉**，否則 agent 會反覆嘗試已知失敗的路徑（[Espressif, 2026-06](https://developer.espressif.com/blog/2026/06/zephyr-coding-with-ai/)）。

**［推論］** 這正好對應 skill 的 L3 資源檔。`references/known-dead-ends.md` 這種檔案的價值會隨時間單調上升，而且它是團隊資產而非個人資產——這是把 skill 放進 git 而不是放在個人設定裡的主要理由。

---

## 5. 第三層：Harness —— 迴圈、預算、閘門、驗證

### 5.1 迴圈的形狀

OpenDev 的技術報告描述了一個終端型 coding agent 每次迭代的六個階段（[arXiv 2603.05344](https://arxiv.org/html/2603.05344v1)）：

1. 前置檢查與 context compaction（記憶體壓力下）
2. 選擇性的 thinking 階段
3. 選擇性的自我批判階段
4. LLM 行動階段（帶完整 tool schema）
5. Tool 執行與核可強制
6. 後處理與是否繼續的決策

它同時列了五層防禦：prompt 層護欄 → schema 層 tool 限制 → 執行期核可 → tool 層驗證與危險樣式阻擋 → 使用者定義的 lifecycle hooks。

Espressif 的實務版本更簡單，但強調節奏：**Plan → Execute → Commit → Test**，而且「測試後要回到 planning，而不是不斷疊加修補請求」。

### 5.2 可跑的範例：韌體修補迴圈

以下是我寫的最小 harness，把預算、閘門、驗證、獨立評估四件事都放進去。它可以直接執行（用假的模型與假的 build，讓迴圈邏輯本身可觀察）。

**預算**——agent 必須有硬性停止條件：

```python
@dataclass
class Budget:
    max_iters: int = 5
    max_wall_s: float = 1800
    max_hil_boots: int = 3      # 燒錄次數也是資源，flash 會磨損
    started: float = field(default_factory=time.time)
    iters: int = 0
    boots: int = 0

    def exhausted(self) -> str | None:
        if self.iters >= self.max_iters:
            return f"iteration budget 用盡（{self.max_iters}）"
        if time.time() - self.started > self.max_wall_s:
            return "wall-clock budget 用盡"
        if self.boots >= self.max_hil_boots:
            return f"HIL boot 次數用盡（{self.max_hil_boots}）"
        return None
```

`max_hil_boots` 是韌體場景特有的：**燒錄次數是有限資源**，flash 有寫入壽命，板子也是共用的。

**閘門**——把 SKILL.md 裡的「硬性限制」變成程式碼：

```python
FORBIDDEN = [
    (r"-Wno-error|Werror\s*:?=\s*$|-Wno-", "不得放寬編譯器警告等級來讓 build 過"),
    (r"^\+\s*//.*vdisp_", "不得註解掉呼叫來讓 build 過"),
    (r"#if 0", "不得用 #if 0 繞過"),
]

def gate_patch(diff: str) -> list[str]:
    return [why for pat, why in FORBIDDEN if re.search(pat, diff, re.M)]
```

**驗證**——`success is silent, failures are verbose`：

```python
def verify(build_log: Path) -> tuple[bool, str]:
    """回傳 (通過?, 給模型的訊息)。通過時訊息為空 —— 不要用成功訊息塞爆 context。"""
    r = classify(build_log)
    if r["category"] == "clean":
        return True, ""
    return False, (
        f"build 仍失敗 [{r['category']}] conf={r['confidence']}\n"
        f"證據：{r['evidence']}\n受影響檔案：{', '.join(r['affected_files'][:5]) or '(未定位)'}"
    )
```

**獨立評估者**——Osmani 指出，把評估與生成分成兩個 agent，表現優於讓模型評自己的作業，因為模型評自己時有 confirmation bias：

```python
def evaluate(diff: str, verify_msg: str) -> dict:
    """獨立的 reviewer。實作上換成另一個 model / 另一個 context。"""
    issues = gate_patch(diff)
    if issues:
        return {"accept": False, "reason": "; ".join(issues)}
    if "undefined reference" in verify_msg:
        return {"accept": False, "reason": "仍是 link 失敗，patch 沒有觸及根因"}
    if not verify_msg:
        return {"accept": True, "reason": "build 通過且未觸犯禁則"}
    return {"accept": False, "reason": "驗證未通過"}
```

**主迴圈**：

```python
def run(initial_log, propose_patch, apply_and_build, budget) -> dict:
    trace = []
    triage = classify(initial_log)
    trace.append({"phase": "triage", **triage})

    # 分流：只有 code / config 類別才進入修補迴圈
    if triage["category"] in ("env", "infra"):
        return {"status": "handoff", "to": triage["owner"], "trace": trace}

    feedback = triage["evidence"]
    while (why := budget.exhausted()) is None:
        budget.iters += 1
        diff = propose_patch(triage, feedback)

        blocked = gate_patch(diff)               # 靜態閘門：build 之前就攔掉
        if blocked:
            feedback = "patch 被閘門擋下：" + "; ".join(blocked)
            trace.append({"phase": "gate", "iter": budget.iters, "blocked": blocked})
            continue                              # 沒有花掉一次 build

        log = apply_and_build(diff)
        budget.boots += 1
        ok, msg = verify(log)
        verdict = evaluate(diff, msg)
        trace.append({"phase": "verify", "iter": budget.iters,
                      "build_ok": ok, "accept": verdict["accept"],
                      "reason": verdict["reason"]})
        if ok and verdict["accept"]:
            return {"status": "fixed", "iters": budget.iters, "trace": trace}
        feedback = msg or verdict["reason"]

    return {"status": "gave_up", "reason": why, "trace": trace, "handoff_note": feedback}
```

我用一個模擬「先偷懶、再繞過、最後改對地方」的假模型跑這個迴圈，實際輸出：

```json
{
  "status": "fixed",
  "iters": 3,
  "trace": [
    { "phase": "triage", "category": "config", "confidence": 1.0,
      "owner": "module-owner",
      "evidence": "vsoc-pm-domains.c:(.text+0x1a4): undefined reference to `vsoc_smi_larb_get'" },
    { "phase": "gate", "iter": 1, "blocked": ["不得放寬編譯器警告等級來讓 build 過"] },
    { "phase": "gate", "iter": 2, "blocked": ["不得註解掉呼叫來讓 build 過"] },
    { "phase": "verify", "iter": 3, "build_ok": true, "accept": true,
      "reason": "build 通過且未觸犯禁則" }
  ]
}
```

**前兩次嘗試連 build 都沒跑。** 在 AOSP 場景這代表省下大約一小時的機器時間。這就是靜態閘門在昂貴迴圈裡的價值：它不只是安全機制，也是成本控制機制。

### 5.3 Context 管理

OpenDev 列了五個機制（[arXiv 2603.05344](https://arxiv.org/html/2603.05344v1)）：動態 system prompt 組裝、tool 結果摘要與大輸出落地、雙記憶架構（episodic + working）、事件驅動的 system reminder、以及適應性 compaction。

**［推論］** 韌體場景裡最關鍵的是第二項——**tool 輸出落地**。前面 `console_read` 與 `build_kernel` 都回 `log_path` 而不是全文，就是這個設計。一份 dmesg 可以輕鬆吃掉 50k tokens，而 agent 真正需要的通常只有 call trace 那 10 行。

---

## 6. 五個場景的具體做法

### 6.1 BSP / Android 平台整合

**難點**：跨模組、跨團隊；同一個症狀的根因可能在 kernel、HAL、framework 或 vendor overlay 的任何一層；tree 大到不可能全部進 context。

**做法**：
- **MCP**：`build_kernel`、`build_soong_module`、`flash_target`、`console_read`、`dmesg_grep`、`dt_diff`（比對 device tree 前後差異）。
- **Skills**：`aosp-build-triage`（如上）、`gki-kmi-check`（把 GKI/KMI ABI 的檢查流程與常見違規寫成程序）。
- **Harness**：分流優先。分類為 `api-break` 時直接產出報告交給上游 owner，**不要讓 agent 在下游逐一 patch**——那是最容易產生一大堆看起來合理、但把問題掩蓋掉的 patch 的路徑。

**要注意的**：AndroidBuildBench 的 81.4% 是在**開源 Android app 專案**上測的（Gradle 建置），不是 AOSP platform build。AOSP 的相依複雜度高一個量級，不應直接外推這個數字。**［推論］** 但「專用 tool > 通用 shell」這個**方向性**結論我認為可以外推，因為它的機制（縮小行動空間、讓動作語意明確）與專案規模無關。

### 6.2 BMC / Embedded C

**難點**：裸機或 RTOS、沒有 MMU 保護、記憶體錯誤直接變成安全漏洞、長度欄位常來自不可信的對端。

有一篇研究直接量化了 LLM 生成韌體的風險：以 GPT-4 生成 FreeRTOS 韌體、在 QEMU 上用 AFL++ 與靜態分析驗證，三類主要漏洞是 buffer overflow (CWE-120)、race condition (CWE-362)、DoS (CWE-400)。加上驗證與修補 agent 之後，漏洞修復率從 **67.3% 提升到 92.4%**（[arXiv 2509.09970](https://arxiv.org/pdf/2509.09970)）。

反過來讀這個數字：**沒有驗證迴圈時，約三分之一的已知漏洞留在生成的韌體裡。**

**做法**：把驗證做成 harness 的強制閘門。我用一段典型的 PLDM/MCTP 解析程式碼實測了兩道閘門：

```c
/* 一段典型的 BMC 韌體訊息解析。buf/buf_len 完全由對端控制。 */
#define PLDM_MAX_PAYLOAD 64

struct pldm_msg {
    uint8_t type, cmd, len;
    uint8_t payload[PLDM_MAX_PAYLOAD];
};

int pldm_parse(const uint8_t *buf, size_t buf_len, struct pldm_msg *out)
{
    if (buf_len < 3)
        return -1;
    out->type = buf[0];
    out->cmd  = buf[1];
    out->len  = buf[2];
    memcpy(out->payload, &buf[3], out->len);   /* BUG: out->len 最大 255 */
    return 0;
}
```

**閘門 1：cppcheck 靜態分析**

```
$ cppcheck --enable=warning,style --error-exitcode=1 --quiet pldm_parse.c
cppcheck exit=0        ← 通過了
```

**閘門 2：對抗性輸入的 property test + ASan**

```c
int main(void) {
    uint8_t *attack = malloc(300);
    memset(attack, 0xAA, 300);
    attack[2] = 200;                    /* 宣稱 200 bytes payload */
    struct pldm_msg *m = malloc(sizeof *m);
    int r = pldm_parse(attack, 300, m);
    free(attack); free(m);
    return r == 0 ? 1 : 0;              /* 接受了就算測試失敗 */
}
```

```
$ gcc -fsanitize=address,undefined -g -O1 pldm_parse.c harness_test.c -o t && ./t
==2319==ERROR: AddressSanitizer: heap-buffer-overflow
WRITE of size 200 at 0x5070000000d3 thread T0
    #2 in pldm_parse pldm_parse.c:23
exit=141
```

**這是本節最重要的一個觀察：靜態分析靜悄悄地放行了，動態閘門抓到了。** 如果你的 harness 只跑 cppcheck 就宣告通過，你得到的是虛假的安心。

修好之後：

```c
    if (out->len > PLDM_MAX_PAYLOAD || (size_t)out->len + 3 > buf_len)
        return -1;
    memcpy(out->payload, &buf[3], out->len);
```

```
$ ./t2
parse returned -1 (期望 <0，代表拒絕過長宣告)
PASS exit=0
```

**［推論］** 對 embedded C，我認為 harness 的最低配置是：`-fsanitize=address,undefined` 的 host build + 一組**對抗性**（不是快樂路徑）的 property test。單靠 linter 不足以當閘門。

### 6.3 驗證與測試：一個必須誠實面對的落差

Frama-C + ACSL 這條路看起來是韌體 AI 化最理想的方向——形式驗證提供了機器可檢查的 ground truth，正好補上模型輸出不可信的缺口。但目前的數據沒有那麼樂觀。

一篇 2026 年的評估研究在 CASP 資料集的 355 支有效 C 程式上，比較了規則式腳本、Frama-C 的 RTE plugin，與三個 LLM 生成的 ACSL 標註（[arXiv 2602.13851](https://arxiv.org/html/2602.13851v1)）：

| 產生方式 | 平均證明成功率 | 求解器穩定性 |
|---|---|---|
| RTE plugin（工具生成） | **約 99%** | timeout 極少 |
| DeepSeek-V3.2 | 93–95% | **149 次執行中有 130 次 Alt-Ergo timeout** |
| OLMo 3.1 32B | 83% | 較穩定（CVC4/CVC5 零 timeout） |
| GPT-5.2 | 81–82% | Alt-Ergo timeout 數量最多（論文回報 272 次） |

論文的結論很值得引用：**「ACSL 生成的表達力提升，與求解器穩定性下降相關」**（increased expressiveness in ACSL generation correlates with reduced solver stability）。

**［推論］** 這個現象我的理解是：LLM 寫的規格比工具生成的更「聰明」也更異質，導致產生的 proof obligation 形狀不規則，把求解器推進了病態的搜尋空間。這對 harness 設計有一個直接的含意——**求解器 timeout 必須被當成一種明確的失敗類別，而不是「再等等看」**。

實務上我會這樣接：

- MCP 端提供 `frama_c_wp(file, function, timeout_s, solver)`，回傳 `{proved, unproved, timeout, goal_summary}` 這樣的結構化結果，而不是 Frama-C 的原始輸出。（我自己在做的 `frama-c-mcp` 就是這個方向。）
- Skill 端寫清楚「先用 RTE 產生基礎標註，LLM 只負責補 loop invariant 與 function contract」——**讓工具做工具擅長的部分**。
- Harness 端把 `timeout` 與 `unproved` 分開處理：timeout 觸發「簡化規格」的重試，unproved 才觸發「規格或程式有錯」的分支。

### 6.4 CI / Build 基礎設施：先看清楚天花板

Live-kBench 是一個持續從 Syzbot 抓取新 kernel bug 的自我演化基準（首版 534 個 bug，2024-04 至 2025-12），測試了 mini-SWE-agent、SWE-agent、OpenHands 三種 scaffold 配 Gemini 3 Pro/Flash 與 Claude Sonnet/Opus 4.5（[arXiv 2602.02690](https://arxiv.org/html/2602.02690)）。

關鍵數字：

| 指標 | 結果 |
|---|---|
| 首次嘗試消除 crash | **74%** |
| Patch 與開發者修法等價 | **約 20%** |
| 十次嘗試消除 crash | 90% |
| 十次嘗試等價修法 | 30% |
| 加入 crash 回饋後的改善 | +29% |
| 知識截止日**之前**的 bug 表現領先 | 高達 **25%** |

三個必須記住的推論：

1. **「不 crash 了」與「修對了」差了 54 個百分點。** 你的 harness 如果只用「症狀消失」當驗收條件，會有超過一半的 patch 是掩蓋而非修復。
2. **回饋迴圈值 29 個百分點。** 這比換模型的效益大。把 crash 訊息餵回去，是投資報酬率最高的單一改動。
3. **知識截止日前後的 25% 落差**意味著公開 benchmark 的分數對「你們自家還沒公開的新硬體」沒有參考價值。**［推論］** 在新平台 bring-up 這種最沒有訓練資料的場景，實際表現應該顯著低於 benchmark。

Patch review 那一側則有 Sashiko 的實際運行數據。Roman Gushchin 分析 1,500 個郵件討論串後回報：偽陽性約 **10%**、真陽性約 **85%**、在 critical/high severity 上的準確率接近 **97%**；上線七週內有 **140 次**在 kernel commit message 裡被提及（[LWN.net](https://lwn.net/Articles/1073583/)）。

同時被提出的抱怨也很有代表性：輸出非決定性、太過冗長、跨版本重複給同樣建議、以及 Christoph Hellwig 批評「開發者需要直接回饋，而不是反覆重新投稿」。

**［推論］** 90% 準確率在「輔助人類 review」的定位下非常有用，在「自動 gating」的定位下則完全不夠——10% 偽陽性乘上每天數百個 patch，會迅速消耗掉維護者的信任。這條界線值得在導入時就講清楚。

### 6.5 除錯迴圈：韌體場景裡 harness 差距最大的一塊

前四個場景都有一個共同性質：**可以無狀態地重試**。build 失敗了就再 build 一次，驗證沒過就再改一次規格。除錯不是這樣。

#### 6.5.1 為什麼互動式除錯對 agent 特別難

三個結構性的困難：

1. **它是狀態機。** 每一步的下一步取決於這一步觀察到什麼。斷點停下來的那個瞬間，**狀態存在板子上、不存在 context 裡**——agent 只要一次 compaction 就會忘記自己為什麼停在這裡。
2. **逐步驟進的成本是災難性的。** `step`、`next`、`print` 每一次都是一輪完整的 model round-trip。走 200 步就是 200 輪，而 200 步在真實的 driver 裡什麼都還沒走到。
3. **符號是偏移量，不是行號。** `vdisp_ovl_config+0x4c/0x1f0` 對模型是無意義的字串，必須先過一層解析才有語意。

這不只是我的觀察。一篇 2026 年的研究把這個問題直接命名並量化了：他們提出 **Agent-centric Debugging Interface (ADI)**，主張給 agent 的介面應該是**函式層級**而非逐行層級，核心資料結構是 **Frame Lifetime Trace**——一個函式一次執行的完整摘要（參數、回傳值、語句層級的狀態變化、呼叫關係），搭配八個高階指令（`break` / `continue` / `prev` / `step-into` / `step-out` / `call-tree` / `execute` / `clear`）。把 ADI 接進既有的 SOTA agent，SWE-bench-Verified 的解決率一致提升 **6.2% 到 18.5%**（[arXiv 2604.24212](https://arxiv.org/html/2604.24212)）。

**［推論］** 這個結果對韌體場景的含意是：**不要把 GDB 原樣接給 agent。** 要接的是「一次跑完、回傳自足摘要」的介面。下面三個範例就是照這個原則設計的。

#### 6.5.2 Post-mortem：把 panic log 壓成假設清單

這是最貼近日常 CI 的一條路——你手上只有一份 log，板子早就重開了。

`triage_panic.py` 做三件確定性的事：**判斷故障種類、把 symbol+offset 解析成位址、濾掉不是我們能改的 frame。**

```python
FAULT_KINDS = [
    (r"NULL pointer dereference at virtual address 0*([0-9a-f]+)", "null-deref",
     "偏移量就是 struct 成員位移：用 pahole / gdb ptype 反推是哪個欄位"),
    (r"Unable to handle kernel paging request", "bad-access",
     "位址不像小偏移量 → 多半是 use-after-free 或未初始化指標"),
    (r"KASAN: (slab-use-after-free|slab-out-of-bounds)", "kasan",
     "KASAN 已指出物件與存取範圍，直接讀它的 allocated/freed stack"),
    (r"watchdog: BUG: soft lockup", "soft-lockup",
     "不是記憶體問題：找沒有讓出 CPU 的迴圈或沒放掉的 spinlock"),
]

# 這些前綴屬於 kernel core / 泛用框架，不是你的 driver
FOREIGN_PREFIXES = ("drm_", "process_one_work", "worker_thread", "kthread",
                    "ret_from_fork", "__", "do_", "el0_", "el1_")
```

對一份 10 個 frame 的 ARM64 panic 實測：

```json
{
  "fault_kind": "null-deref",
  "fault_offset": "18",
  "hint": "偏移量就是 struct 成員位移：用 pahole / gdb ptype 反推是哪個欄位",
  "crash_pc": {
    "symbol": "vdisp_ovl_config", "offset": 76,
    "addr": "0xffffffc008a1024c",
    "addr2line": "addr2line -f -i -e vmlinux 0xffffffc008a1024c"
  },
  "frames_total": 10,
  "frames_ours": 4,
  "suspect_functions": ["vdisp_ovl_config", "vdisp_crtc_hw_init",
                        "vdisp_crtc_atomic_enable", "commit_tail"],
  "next_action": "故障位址 0x18 是小偏移量，代表對 NULL struct 取成員（+0x18）。在 vdisp_ovl_config 內找對應 offset 的欄位存取，並用 `git log -L :vdisp_ovl_config:<file>` 找最近改動。"
}
```

**10 個 frame 縮到 4 個，並且附上一個可以直接執行的下一步。**

不過請注意輸出裡的 `commit_tail`——**這是一個誤判**。它是 kernel core 的函式，不在我的前綴清單裡就被當成「我們的」。我刻意把這個缺陷留在範例裡，因為它說明了一件重要的事：**以符號名稱前綴判斷擁有權是很粗糙的啟發式**。正式使用時應該改成用**檔案路徑**對照 `MAINTAINERS`，或直接查你們內部的模組擁有權表。啟發式的價值在於它把 10 個變成 4 個；它的極限在於那 4 個裡還會混進雜訊，所以下游一定要有人（或另一個驗證步驟）能推翻它。

#### 6.5.3 軌跡 diff：把「猜哪裡錯」變成「讀一份差異」

**［推論］** 這是我認為最被低估、而且最適合 agent 的除錯形態。理由很簡單：模型不擅長從無到有推理硬體行為，但非常擅長讀結構化的差異。

情境是韌體最常見的那一種：**同一份 image，A 板正常、B 板失敗**。

用 `-finstrument-functions` 蒐集兩次執行的函式進出軌跡（韌體上的等價物是 ftrace function graph、ETM/ITM trace，或在關鍵函式插的 printk），然後找出第一個分歧點：

```
共同前綴：4 個事件（good 共 6 / bad 共 4）

      good                                    bad
        < lookup_cfg() @sensor.c:16             < lookup_cfg() @sensor.c:16
        > ovl_config_apply() @sensor.c:10       > ovl_config_apply() @sensor.c:10
>>>     < ovl_config_apply() @sensor.c:10     (未執行 / 已崩潰)
      < main() @sensor.c:26                   (未執行 / 已崩潰)

第一個分歧發生在事件 #4。
bad 進入 ovl_config_apply() 之後就沒有再出來。
→ 假設：崩潰發生在 ovl_config_apply() 內部。下一步用 debug_snapshot 在該函式設斷點，
  檢視它讀取的每個指標。
```

一個踩過的坑值得記下來：**軌跡輸出是有緩衝的，崩潰會吃掉緩衝區裡的最後幾筆。** 我第一版的 hook 只在函式離開時 `fflush`，結果 bad 的軌跡少了關鍵的最後一筆進入紀錄，工具給出的結論就偏了一格。在 enter 也 fflush 之後才定位正確。韌體上的等價陷阱是 UART 的 TX FIFO 與 printk 的 ring buffer——**panic 前的最後幾行往往就是最重要的那幾行**。

#### 6.5.4 狀態快照：一次跑完，不要逐步驟進

軌跡 diff 告訴你**哪個函式**，快照告訴你**哪個變數**。

`gdb_snapshot.py` 把一整段 GDB 腳本一次跑完，回傳一個自足的物件——這正是 6.5.1 提到的「函式層級介面」在 GDB 上的實作：

```python
GDB_SCRIPT = """
set pagination off
run {args}
echo \\n===SIGNAL===\\n
info program
echo \\n===FRAME===\\n
frame
echo \\n===BACKTRACE===\\n
bt
echo \\n===ARGS===\\n
info args
echo \\n===LOCALS===\\n
info locals
echo \\n===EXPR===\\n
{exprs}
quit
"""
```

實測：

```bash
$ python gdb_snapshot.py ./sensor --args ovl9 \
    --watch 'dev->cfg' --watch 'dev->name' --watch 'dev->cfg == 0'
```

```json
{
  "crashed": true,
  "signal": "SIGSEGV",
  "crash_site": "11\t    int w = dev->cfg->width;",
  "backtrace": [
    {"n": 0, "fn": "ovl_config_apply", "args": "dev=0x7fffffffa6d0, layer=3",
     "file": "sensor.c", "line": 11},
    {"n": 1, "fn": "main", "args": "argc=2, argv=0x7fffffffa818",
     "file": "sensor.c", "line": 30}
  ],
  "args": {"dev": "0x7fffffffa6d0", "layer": "3"},
  "locals": {"w": "0"},
  "watched": {
    "dev->cfg": "(struct ovl_config *) 0x0",
    "dev->name": "0x7fffffffaf2b \"ovl9\"",
    "dev->cfg == 0": "1"
  }
}
```

**整個診斷在一次呼叫裡完成**：`dev->name` 是 `"ovl9"`、`dev->cfg` 是 `0x0`——查表失敗回了 NULL，呼叫端沒檢查。若用逐步驟進，同樣的結論要花掉十幾輪往返。

包成 MCP tool 的簽章是：

```python
@mcp.tool()
def debug_snapshot(binary: str, args: str = "", breakpoints: list[str] = [],
                   watch: list[str] = []) -> Snapshot:
    """在指定斷點取一張自足的狀態快照。不提供 step/next——
    逐步驟進對 agent 是反模式（見 ADI 論文的 function-level 主張）。"""
```

注意它**刻意不提供** `step` / `next`。這回到第 3 節的原則：**tool 的設計就是在替模型做決定**，而「不要一步步走」正是資深工程師會給的建議。

#### 6.5.5 完整鏈路

三個工具串起來就是一條可執行的除錯流水線：

```
panic log ──triage_panic──► fault_kind + 4 個可疑函式
                                    │
good/bad 兩次執行 ──trace_diff──►  分歧點：ovl_config_apply
                                    │
                          gdb_snapshot ──► dev->cfg == 0x0
                                    │
                              假設成立 → 修補
```

實測串接的最後兩步：

```
$ python trace_diff.py ./sensor_traced trace.good trace.bad
→ 假設：崩潰發生在 ovl_config_apply() 內部。

$ python gdb_snapshot.py ./sensor --args ovl9 --watch 'dev->cfg'
crash: 11	    int w = dev->cfg->width;
watched: {'dev->cfg': '(struct ovl_config *) 0x0'}
```

#### 6.5.6 Harness 上的差異：假設紀錄

除錯迴圈與第 5 節的修補迴圈有一個關鍵不同：**它需要記憶**。

修補迴圈可以無狀態——每次拿最新的錯誤訊息重試就好。除錯不行：如果 agent 忘記「H2 已經被否證了」，它會在第五輪回頭再試一次 H2。這正是 OpenDev 提的 **episodic memory** 要解決的問題（[arXiv 2603.05344](https://arxiv.org/html/2603.05344v1)），也是 Espressif 那個 `journal.md` 的本質。

我在 `panic-triage` skill 裡把它做成強制的產出格式：

```
[H3] cfg 在 lookup 失敗時回 NULL 而呼叫端未檢查
     驗證方式：gdb_snapshot --watch 'dev->cfg'
     結果：確認 dev->cfg == 0x0  → 成立
```

以及兩條禁則：

- **不要用「加上 NULL 檢查」當作修復，除非你能說明為什麼它會是 NULL。** 這條直接對應 6.4 節那個 74% vs 20% 的落差——擋掉症狀而不解釋成因，正是「plausible 但不等價」的典型樣態。
- **不要同時改多處。** 改一處、重現一次、更新假設。

---

## 7. 風險與邊界

### 7.1 Log 與 commit message 是不可信輸入

這一點在韌體場景特別容易被忽略：agent 讀的 dmesg、UART 輸出、commit message、bug report，全都是**外部可影響的內容**。

LWN 的報導提到 Sashiko「可能被 commit message 的描述影響」——這不是假設性風險，是已經觀察到的行為。

**做法**：
- 所有從 log/console/issue 讀進來的內容，在 prompt 裡明確標記為**資料**而非指令。
- 破壞性 tool 的權限**不能**由 agent 自己升級（前面 `FW_LAB_ALLOW` 必須由人類設定並重啟 server，就是為了這個）。
- Prompt 層的規則對此無效，閘門一定要在 tool 或 harness 層。

### 7.2 非確定性

同一個輸入兩次執行結果不同。這對「修 bug」還可以接受，對「分類」「gating」「回歸判定」不可接受。這也是我把分類器寫成規則腳本的原因。

### 7.3 上游貢獻的合規要求

如果你的工作會回饋到 Linux kernel 上游，[官方的 AI coding assistants 文件](https://docs.kernel.org/process/coding-assistants.html)有明確規定：

- **必須**加上 `Assisted-by: LLM [TOOL1] [TOOL2]` 標籤，列出使用的專門分析工具（coccinelle、sparse、smatch、clang-tidy 等）；一般開發工具（git、gcc、make、編輯器）不列。
- **AI agent 不得加 `Signed-off-by` 標籤。** 只有人類能在法律上認證 DCO。
- 人類投稿者承擔全部責任：審查所有 AI 生成的程式碼、確認 GPL-2.0-only 授權相容、加上自己的 `Signed-off-by`、並在投稿前實際建置與測試過。

**［推論］** 這個政策的設計哲學值得放進任何團隊的流程：**AI 可以參與生產，但責任鏈上必須有一個具名的人**。把這一點寫進你的 harness——例如產出的 patch 一律進 draft 狀態、一律要求人類簽核——比事後補救便宜得多。

### 7.4 保密邊界

公司內部的 BSP、未公開的晶片文件、客戶專案程式碼，送進外部模型是實質的資料外洩。這件事的處理不在技術層而在流程層，但它會反過來限制你的架構選擇——**［推論］** 如果外部模型不可用，你的 harness 設計就必須為較弱的地端模型服務，而這正好讓「harness 比模型重要」這個結論更加成立。

---

## 8. 一個務實的導入順序

**［推論］** 以下是我的建議順序，原則是「每一步都要在下一步之前就產生獨立價值」：

1. **先做唯讀的 MCP。** log 查詢、build 狀態查詢、artifact 下載。零風險，立刻能用，而且能讓你觀察 agent 實際會怎麼用這些 tool。
2. **把 log 摘要器寫好。** 這是投報率最高的單一元件——它決定了後面所有步驟的 context 成本。
3. **把最痛的一個 triage 流程寫成 skill。** 選一個你每週都要做三次、而且有明確決策樹的流程。附上確定性的 L3 腳本。
4. **加靜態閘門。** 在還沒有任何自動修補之前就先加，因為它同時是安全網與成本控制。
5. **才開始做修補迴圈**，而且一開始只開放最低風險的類別（例如 `config`），產出一律進 draft 由人類簽核。
6. **加除錯三件組。** panic 分流腳本 → 軌跡 diff → 狀態快照。這三個都是唯讀的，風險低，而且是整套系統裡最快能讓人「有感」的部分。
7. **最後才碰實體硬體。** flash 與 power control 預設關閉，用 lease 明確建模擁有權，並保留完整操作稽核記錄。

不要反過來做。先做修補迴圈再補閘門，你會在第一週就燒掉團隊對這套系統的信任。

---

## 附錄：範例程式碼清單

本文所有範例都已實際執行驗證：

| 檔案 | 說明 |
|---|---|
| `fw_lab_mcp.py` | MCP server：board lease、build、flash（opt-in）、console；結構化摘要 |
| `skills/aosp-build-triage/SKILL.md` | Skill L2：分流流程與硬性限制 |
| `skills/aosp-build-triage/references/taxonomy.md` | Skill L3：五類失敗的完整定義 |
| `skills/aosp-build-triage/scripts/classify_build_log.py` | Skill L3：確定性分類器 |
| `harness.py` | 修補迴圈：預算、閘門、驗證、獨立評估 |
| `verify-demo/pldm_parse.c` + `harness_test.c` | 記憶體安全閘門示範 |
| `skills/panic-triage/SKILL.md` | Skill L2：除錯流程、假設紀錄格式與禁則 |
| `debug-demo/triage_panic.py` | Panic log → 故障種類 + 可疑函式（附 System.map 解析） |
| `debug-demo/trace_diff.py` | good/bad 執行軌跡的第一個分歧點 |
| `debug-demo/gdb_snapshot.py` | 一次跑完的 GDB 狀態快照（函式層級介面） |
| `debug-demo/sensor.c` + `trace_hook.c` | 除錯範例的目標程式與 `-finstrument-functions` 鉤子 |

環境：Python 3.11.15、`mcp` 1.27.0、gcc 13、cppcheck 2.13.0、GNU gdb 15.1、binutils（`addr2line`）。

---

## 引用來源

**規格與官方文件**

- [The 2026-07-28 Specification — Model Context Protocol Blog](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
- [Agent Skills Overview — Claude Platform Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [AI Coding Assistants — The Linux Kernel documentation](https://docs.kernel.org/process/coding-assistants.html)

**論文**

- [Automating Android Build Repair: Bridging the Reasoning-Execution Gap in LLM Agents with Domain-Specific Tools (arXiv:2510.08640)](https://arxiv.org/abs/2510.08640)
- [Outrunning LLM Cutoffs: A Live Kernel Crash Resolution Benchmark for All (arXiv:2602.02690)](https://arxiv.org/html/2602.02690)
- [Evaluating LLM-Generated ACSL Annotations for Formal Verification (arXiv:2602.13851)](https://arxiv.org/html/2602.13851v1)
- [Securing LLM-Generated Embedded Firmware through AI Agent-Driven Validation (arXiv:2509.09970)](https://arxiv.org/pdf/2509.09970)
- [Building AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned (arXiv:2603.05344)](https://arxiv.org/html/2603.05344v1)
- [Empowering Autonomous Debugging Agents with Efficient Dynamic Analysis (arXiv:2604.24212)](https://arxiv.org/html/2604.24212) — Agent-centric Debugging Interface / Frame Lifetime Trace
- [debug-gym: A Text-Based Environment for Interactive Debugging (arXiv:2503.21557)](https://arxiv.org/abs/2503.21557)

**實務與社群**

- [Agent Harness Engineering — Addy Osmani](https://addyosmani.com/blog/agent-harness-engineering/)
- [Reviewing kernel patches with LLMs — LWN.net](https://lwn.net/Articles/1073583/)
- [Introduce Sashiko (agentic review of Linux kernel changes) — LKML](https://lkml.iu.edu/hypermail/linux/kernel/2603.2/06886.html)
- [Developing a Zephyr IoT app with AI — Espressif Developer Portal](https://developer.espressif.com/blog/2026/06/zephyr-coding-with-ai/)

**工具**

- [labgrid-mcp](https://github.com/onurcelep/labgrid-mcp) — labgrid hardware-in-the-loop 的 MCP server（47 tools）
- [embedded-debugger-mcp](https://github.com/adancurusul/embedded-debugger-mcp) — probe-rs / OpenOCD，ARM Cortex-M / RISC-V / Xtensa
- [labgrid](https://github.com/labgrid-project/labgrid) — 嵌入式系統控制函式庫
