#!/usr/bin/env python3
import os, sys, json, subprocess, textwrap
from pathlib import Path
from openai import OpenAI

# --- 讀 .env（避免 hook 抓不到環境變數） ---
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if line.strip() and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    sys.stderr.write("OPENAI_API_KEY not found (set in .env or environment)\n")
    sys.exit(0)  # 不要阻斷 commit，讓 Git 回到手動輸入

client = OpenAI(api_key=API_KEY)

# --- 讀取 staged diff ---
try:
    diff = subprocess.run(
        ["git", "diff", "--staged", "-U0", "--no-color"],
        stdout=subprocess.PIPE, check=True, text=True
    ).stdout.strip()
except subprocess.CalledProcessError:
    diff = ""

if not diff:
    sys.exit(0)

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")  # 你可改成 gpt-5

SYSTEM = "You are a senior software engineer. Write clear, concise Conventional Commit messages."
USER = f"""
Generate a Conventional Commit for the following git staged diff.
Rules:
- Return ONLY JSON with keys: type, scope, summary, body, footer.
- type in: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert.
- summary <= 72 chars, imperative mood, no trailing period.
- body wrapped at 72 chars per line (may be empty).
- footer for issue refs or BREAKING CHANGE (may be empty).

Diff (unified, no color):
{diff}
"""

def assemble_message(d):
    type_   = d.get("type","chore")
    scope   = d.get("scope","")
    summary = d.get("summary","update")
    body    = (d.get("body","") or "").strip()
    footer  = (d.get("footer","") or "").strip()

    header = f"{type_}{f'({scope})' if scope else ''}: {summary}"
    out = [header]
    if body:
        if "\n" not in body:
            body = "\n".join(textwrap.wrap(body, width=72))
        out += ["", body]
    if footer:
        out += ["", footer]
    return "\n".join(out).strip() + "\n"

def write_out(msg):
    out_path = sys.argv[1] if len(sys.argv) > 1 else ".git/COMMIT_EDITMSG"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(msg)

payload_msgs = [
    {"role": "system", "content": SYSTEM},
    {"role": "user",   "content": USER},
]

# --- Path 1: Responses API + Structured Outputs (新 SDK) ---
try:
    SCHEMA = {
        "type": "object",
        "properties": {
            "type":   {"type": "string"},
            "scope":  {"type": "string"},
            "summary":{"type": "string"},
            "body":   {"type": "string"},
            "footer": {"type": "string"}
        },
        "required": ["type","summary"],
        "additionalProperties": False
    }
    resp = client.responses.create(
        model=MODEL,
        input=payload_msgs,
        response_format={"type": "json_schema", "json_schema": {"name":"commit","schema":SCHEMA}}
    )
    # 新 SDK：取 output_text 或第一段 text
    text = getattr(resp, "output_text", None)
    if not text:
        # 兼容另一種結構
        text = resp.output[0].content[0].text  # 可能會因版本不同而失敗
    data = json.loads(text)
    msg = assemble_message(data)
    write_out(msg)
    sys.exit(0)
except TypeError:
    # 舊 SDK：不支援 response_format 參數，改走 Chat Completions
    pass
except Exception:
    # 任何解析失敗都回退
    pass

# --- Path 2: Chat Completions + JSON 模式（舊 SDK 穩定） ---
try:
    chat = client.chat.completions.create(
        model=MODEL,
        messages=payload_msgs,
        response_format={"type": "json_object"}  # 要求回傳 JSON 物件
    )
    content = chat.choices[0].message.content
    data = json.loads(content)
    msg = assemble_message(data)
    write_out(msg)
    sys.exit(0)
except Exception as e:
    # 最後防呆：不要讓 commit 中斷，留空讓你手動輸入
    sys.stderr.write(f"[ai-commit] fallback failed: {e}\n")
    sys.exit(0)
