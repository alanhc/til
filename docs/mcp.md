
## 撰寫 MCP Server
先看 python 版本的 MCP server 範例：
https://github.com/modelcontextprotocol/python-sdk
```python
"""
FastMCP quickstart example.

Run from the repository root:
    uv run examples/snippets/servers/fastmcp_quickstart.py
"""

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo", json_response=True)


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```
執行：
```bash
uv run --with mcp main.py
```

這樣會有個 server 在 `http://localhost:8000`，

## export to public domain using cloudflare tunnel
```bash
cloudflared tunnel --url http://127.0.0.1:8000
```
會有類似
```
...
2025-11-22T13:26:44Z INF |  https://harbour-deborah-skating-replacement.trycloudflare.com 
...
```

## ChatGPT 使用 MCP server
接下來要去ChatGPT 設定 MCP server
去設定
![alt text](image-6.png)
連接器
![alt text](image-8.png)
建立
MCP Server URL 要填寫剛才cloudflare tunnel 提供的網址/mcp
![alt text](image-9.png)

## 直接在 ChatGPT 裡面呼叫剛才新增的 My MCP 
![alt text](image-10.png)

小範例參考
https://github.com/alanhc/yt-mcp-server