# Discord Bot 開發

開發 Discord bot 的筆記。

## 重點

- 到 [Discord Developer Portal](https://discord.com/developers/applications) 建立 Application，並在 Bot 頁面取得 **Bot Token**（勿外洩）。
- 需開啟必要的 **Privileged Gateway Intents**（例如 Message Content Intent 才能讀取訊息內容）。
- 用 OAuth2 URL Generator 產生邀請連結，將 bot 加入伺服器並授予權限。
- 常用函式庫：Python 的 [discord.py](https://discordpy.readthedocs.io/)、Node.js 的 [discord.js](https://discord.js.org/)。
- 現代做法多以 **Slash Commands (`/`)** 取代傳統的訊息前綴指令。

參考：https://ithelp.ithome.com.tw/articles/10350599
