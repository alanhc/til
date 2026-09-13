---
sidebar_label: Tailscale + Finder 整合
---

# 把整個 Tailnet 接進 macOS Finder：VNC、Taildrop 與 Taildrive 實戰

> 從「為什麼 Finder 只看得到一台機器」出發，一路踩到 Taildrive 的兩段式授權陷阱，以及一次「看起來完美但其實是巧合」的誤判。本文記錄完整的診斷過程與可直接複製的設定。

---

## 一、問題：Finder 的「共享」區永遠只有一台

手上有一個二十台裝置的 tailnet，Mac、Linux、Windows、手機都有。Tailscale 連線一切正常，`tailscale status` 列得出所有機器，`ssh` 也通。但打開 Finder，側邊欄的「共享」區只有孤零零一台。

原因不在 Tailscale，而在 **Finder 的探索機制**。

Finder 側邊欄的「共享」區靠 **Bonjour / mDNS 多播**探索區網服務（`_rfb._tcp` 是螢幕共享、`_smb._tcp` 是檔案共享）。mDNS 的運作前提是**多播封包能到達**——它送到 `224.0.0.251:5353`，TTL 為 1，設計上就只在同一個廣播網域內流動。

而 Tailscale 是一個**點對點的 L3 overlay**：它建立的是 unicast 的 WireGuard 隧道，不轉發多播。所以 tailnet 上的機器**永遠不會**自己出現在 Finder。你看到的那一台，是剛好接在同一個 Wi-Fi 上被 Bonjour 掃到的。

這不是 bug，是兩種技術的本質差異。結論很直接：**tailnet 的機器必須手動指定位址**，或是想辦法把「手動指定」這件事自動化。

---

## 二、先盤點：哪些機器開了什麼服務

在設定之前，先確認每台機器實際開了什麼。用 MagicDNS 名稱直接探測，避免之後 IP 變動：

```bash
for h in mac-mini macbook-pro linux-desktop linux-laptop; do
  echo "=== $h ==="
  for p in 5900 445 22 3389; do
    nc -z -G 2 -w 2 "$h" $p 2>/dev/null && echo "  $p OPEN" || echo "  $p closed"
  done
done
```

結果：

| 機器 | OS | VNC 5900 | SMB 445 | SSH 22 | RDP 3389 |
| --- | --- | --- | --- | --- | --- |
| mac-mini | macOS | ✅ | ❌ | ✅ | — |
| macbook-pro | macOS | ✅ | ❌ | ✅ | — |
| linux-desktop | Linux | ✅ | ❌ | ✅ | ✅ |
| linux-laptop | Linux | ❌ | ❌ | ✅ | ✅ |

一個都沒開 SMB。這決定了後面的路線：**與其去每台開檔案共享，不如用 Tailscale 自己的檔案方案**。

MagicDNS 這裡要確認一下有生效：

```bash
tailscale status --json | jq -r '.MagicDNSSuffix'
# tailnet-name.ts.net
dscacheutil -q host -a name mac-mini
# ip_address: 100.97.183.18
```

有 MagicDNS 就一律用主機名，別寫 100.x 的 IP——節點重裝或重新登入時 IP 會變，主機名不會。

---

## 三、VNC：用 `.vncloc` 做 Finder 原生捷徑

macOS 有一類很少人用的檔案叫 **Internet Location File**，副檔名依協定而不同：`.webloc`（http）、`.ftploc`、`.afploc`，以及螢幕共享用的 **`.vncloc`**。

它的內容就是一個帶 `URL` 鍵的 plist：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>URL</key>
	<string>vnc://mac-mini.tailnet-name.ts.net</string>
</dict>
</plist>
```

存成 `xxx.vncloc`，雙擊就會用「螢幕共享」連過去。驗證它真的被系統認得：

```bash
mdls -name kMDItemContentType xxx.vncloc
# kMDItemContentType = "com.apple.vnc-internet-location"
```

要確認哪個 App 會接手，可以翻 LaunchServices 的註冊表（不用真的開啟它）：

```bash
/System/Library/Frameworks/CoreServices.framework/Frameworks/\
LaunchServices.framework/Support/lsregister -dump | grep -B3 "bindings:.*vnc:"
# bundle:  Screen Sharing (0x42c)
# bindings: vnc:
```

比起要人記住 `⌘K` 再貼網址，這種捷徑檔可以整理成資料夾、加 emoji、放進側邊欄，體驗好非常多。

### 3.1 自動產生：只列出「現在線上」的機器

手寫捷徑檔沒有意義，因為機器上上下下。`tailscale status --json` 有 `Peer[].Online` 欄位，寫個腳本定期重建即可：

```bash
#!/bin/bash
TS=/Applications/Tailscale.app/Contents/MacOS/Tailscale
"$TS" status --json | python3 -c '
import json,sys
d=json.load(sys.stdin)
for p in (d.get("Peer") or {}).values():
    if p.get("Online"):
        print(f"{p[\"HostName\"]}\t{p[\"DNSName\"].rstrip(\".\")}\t{p.get(\"OS\",\"\")}")
'
```

再對每台探測 5900 / 445 / 3389，開著才產生對應捷徑。搭配 LaunchAgent 每五分鐘跑一次：

```xml
<key>ProgramArguments</key>
<array><string>/Users/alanhc/Tailscale/.bin/ts-refresh</string></array>
<key>RunAtLoad</key><true/>
<key>StartInterval</key><integer>300</integer>
```

寫檔時記得**先比對內容再覆蓋**（`cmp -s`），不然 Finder 每五分鐘閃一次。

### 3.2 踩雷：Finder 側邊欄無法用程式加入

想把資料夾自動加進側邊欄的「喜好項目」，結論是**做不到**。

清單存在 `~/Library/Application Support/com.apple.sharedfilelist/`，是 `NSKeyedArchiver` 格式的 `.sfl3`。而且這個目錄受 TCC 保護——沒有「完整取用磁碟」權限時，`ls` 不會報錯，只會回傳**空的列表**，很容易誤判成目錄不存在：

```bash
ls -la ~/Library/Application\ Support/com.apple.sharedfilelist/
# total 0        ← 不是真的空
```

系統內建的 `sfltool` 也只有 `list` / `clear` / `archive`，**沒有 add**。第三方的 `mysides` 在近期 macOS 上已不可靠。

務實的做法：把資料夾放好，請使用者拖一次進側邊欄（只需一次）。另外可以用 `defaults` 把它加進 Dock 當堆疊，這條路是通的：

```bash
defaults write com.apple.dock persistent-others -array-add '<dict>
  <key>tile-data</key><dict>
    <key>file-data</key><dict>
      <key>_CFURLString</key><string>file:///Users/alanhc/Tailscale/</string>
      <key>_CFURLStringType</key><integer>15</integer>
    </dict>
    <key>file-type</key><integer>2</integer>
    <key>showas</key><integer>3</integer>
  </dict>
  <key>tile-type</key><string>directory-tile</string>
</dict>'
killall Dock
```

---

## 四、Taildrop：單向推檔，加一個 Finder droplet

`tailscale file cp` 可以把檔案推到 tailnet 上任何裝置，不需要對方開任何服務：

```bash
tailscale file cp report.pdf mac-mini:
```

注意結尾那個冒號，這是 `scp` 風格的語法。

包裝成 macOS **droplet**（可拖放的 AppleScript App）就能融進 Finder。用 `osacompile` 編譯一個含 `on open` handler 的腳本即可：

```applescript
on run
	set theFiles to choose file with multiple selections allowed
	doSend(theFiles)
end run

on open theFiles
	doSend(theFiles)
end open
```

`osacompile -o 傳送檔案到裝置.app droplet.applescript` 產出的 bundle，Info.plist 會自動帶上接受所有型別的 `CFBundleDocumentTypes`：

```bash
/usr/libexec/PlistBuddy -c "Print :CFBundleDocumentTypes" \
  傳送檔案到裝置.app/Contents/Info.plist
# CFBundleTypeExtensions = Array { * }
```

一個實用細節：`tailscale file cp` **不吃資料夾**。在腳本裡先用 `ditto` 壓成 zip 再送：

```bash
ditto -c -k --sequesterRsrc --keepParent "$dir" "$tmp/$(basename "$dir").zip"
```

### 4.1 Linux 端自動接收：systemd user unit 不需要 sudo

Taildrop 送到 Linux 之後，檔案會停在 inbox，要手動 `tailscale file get` 才會落地。用 `--loop` 常駐就能自動接收。

關鍵在於這件事**完全不需要 root**——用 systemd **user** unit：

```ini
# ~/.config/systemd/user/taildrop.service
[Unit]
Description=Taildrop auto-receive
Documentation=https://tailscale.com/kb/1106/taildrop

[Service]
Type=simple
ExecStartPre=/bin/mkdir -p %h/Downloads
ExecStart=/usr/bin/tailscale file get --loop --verbose --conflict=rename %h/Downloads
Restart=always
RestartSec=15

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now taildrop.service
```

`--conflict=rename` 讓同名檔自動加編號，預設的 `skip` 會讓檔案卡在 inbox。

要讓它在**沒有登入時**也運作，使用者需要開啟 linger：

```bash
loginctl show-user "$USER" -p Linger
# Linger=yes
```

若是 `no`，`loginctl enable-linger $USER` 需要 polkit 授權（通常等於要密碼）。這是整套流程唯一可能需要提權的地方。

### 4.2 踩雷：非 root 使用 Taildrop 需要 operator

在其中一台 Linux 上收檔一直失敗：

```
getting WaitingFiles: Access denied: file access denied
To not require root, use 'sudo tailscale set --operator=$USER' once.
```

`tailscale status` 這類唯讀操作非 root 可用，但**收檔屬於寫入操作**，需要該使用者被登記為 operator。檢查方式：

```bash
tailscale debug prefs | grep -i operatoruser
# "OperatorUser": "alanhc",     ← 沒有這行就是沒設
```

修正只需一次：`sudo tailscale set --operator=$USER`。

---

## 五、Taildrive：真正的 Finder 掛載

Taildrop 是單向推檔。要在 Finder 裡**瀏覽並讀寫**遠端檔案，Tailscale 的方案是 **Taildrive**——就是 iPhone「檔案」App 裡看到的那個 Tailscale。它底層是 WebDAV，所有支援的裝置上都跑一個伺服器在 `http://100.100.100.100:8080`。

分享目錄（Linux / Windows 用 CLI）：

```bash
tailscale drive share home "$HOME"
tailscale drive share downloads "$HOME/Downloads"
tailscale drive list
```

macOS 的 GUI 版**不支援 CLI**，會直接擋下來：

```
Taildrive CLI commands are not supported when using the macOS GUI app.
Please use the Tailscale menu bar icon to configure Taildrive in Settings.
```

要從 Mac 分享目錄只能走選單列 → Settings → Taildrive。但**存取**別人的分享不受此限，CLI 與 Finder 都正常。

### 5.1 最大的坑：兩段式授權

這是整趟最花時間的地方，而且文件沒有講清楚。**Taildrive 需要兩個獨立的 ACL 設定，缺一不可。**

**第一段，`nodeAttrs`——開啟功能：**

```json
"nodeAttrs": [
  {
    "target": ["autogroup:member"],
    "attr":   ["drive:share", "drive:access"],
  },
],
```

沒有這段的症狀很明確，CLI 會直接告訴你：

```
Access denied: taildrive sharing not enabled,
please add the attribute "drive:share" to this node in your ACLs' "nodeAttrs" section
```

**第二段，`grants`——授予讀寫權限：**

```json
"grants": [
  {
    "src": ["autogroup:member"],
    "dst": ["autogroup:member"],
    "app": {
      "tailscale.com/cap/drive": [{
        "shares": ["*"],
        "access": "rw",
      }],
    },
  },
],
```

`access` 只有 `rw` 與 `ro`；`shares` 可以是 `["*"]` 或具體的分享名稱。

**只做第一段的症狀極具誤導性**：`tailscale drive share` 成功、`tailscale drive list` 列得出來、檔案伺服器程序也確實在跑——看起來一切正常。但從別台 PROPFIND 過去，裝置層是空的。

真正的線索藏在**分享端**的日誌裡：

```bash
journalctl -u tailscaled --since "-30min" | grep -i drive
# starting taildrive file server with sudo as user "alanhc"
# peerapi: taildrive: not permitted        ← 就是這行
```

時間戳會剛好對上你發出請求的那一刻。看到 `not permitted` 就是 grants 沒給。

### 5.2 用 API 改 ACL 的安全流程

在 admin console 手改容易漏存（我就遇到「以為存好了但其實沒有」）。用 API 比較可靠，而且可以先驗證：

```bash
# 1. 取出目前的 policy（HuJSON，含註解）
curl -s -H "Authorization: Bearer $TSKEY" -H "Accept: application/hujson" \
  https://api.tailscale.com/api/v2/tailnet/-/acl -o acl.hujson

# 2. 改完先驗證，回 {} 表示沒問題
curl -s -X POST -H "Authorization: Bearer $TSKEY" \
  -H "Content-Type: application/hujson" --data-binary @acl.new.hujson \
  https://api.tailscale.com/api/v2/tailnet/-/acl/validate

# 3. 帶 ETag 套用，避免覆蓋掉別人同時的修改
ETAG=$(curl -s -D - -o /dev/null -H "Authorization: Bearer $TSKEY" \
  https://api.tailscale.com/api/v2/tailnet/-/acl | grep -i '^etag:' | awk '{print $2}')

curl -s -X POST -H "Authorization: Bearer $TSKEY" \
  -H "Content-Type: application/hujson" -H "If-Match: $ETAG" \
  --data-binary @acl.new.hujson \
  https://api.tailscale.com/api/v2/tailnet/-/acl
```

三個要點：

- 用 `Accept: application/hujson` 取回**帶註解的原始格式**，用一般 JSON 會把註解全部洗掉
- **一定要先 validate**，語法錯誤的 policy 套下去可能把自己鎖在門外
- `If-Match` 帶 ETag 做樂觀鎖，這是多人 tailnet 的基本禮貌

### 5.3 另一個坑：路徑用的是小寫 DNS 名，不是 Hostname

ACL 補齊後，一台 Linux 的分享正常出現，另一台卻怎麼都是 404。

先講結論，因為我在這裡繞了遠路：**404 的原因是我自己把 URL 裡的裝置名拼錯了大小寫。**

Taildrive 的 WebDAV 路徑結構是 `/<tailnet>/<裝置>/<share>/`，其中 `<裝置>` 用的是**全小寫的 MagicDNS 名稱**，不是 `tailscale status` 顯示的 Hostname。這兩者在某些機器上並不一樣：

| 來源 | 值 |
| --- | --- |
| Hostname（`tailscale status` 顯示） | `linux-Laptop-G614PR` |
| MagicDNS 名稱／WebDAV 路徑 | `linux-laptop-g614pr` |

路徑是大小寫敏感的，用 Hostname 去拼就是 404。正確做法是**不要自己拼路徑**，從上一層 PROPFIND 回應裡把 `<D:href>` 直接拿來用：

```bash
curl -s -X PROPFIND -H "Depth: 1" http://100.100.100.100:8080/<tailnet>/ \
  | grep -oE '<D:href>[^<]*</D:href>'
```

掛載之後更簡單，直接看目錄名就是權威答案：

```bash
ls /Volumes/100.100.100.100/<tailnet>/
```

### 5.4 那個誤判本身更值得記

上面那個 404，我第一次的結論是錯的，而且錯得很有說服力。過程是這樣：

先確認 **404 是本機 client 產生的，請求根本沒送出去**——去分享端的 journal 看，完全沒有對應時間的 peerapi 記錄。這正確地排除了授權問題（授權問題會是 `not permitted`，而且日誌看得到）。

然後比對兩台在 netmap 裡的 peer 記錄，發現只有一個欄位不同：

```
正常那台   Cap: 142   tailscale 1.102.2
404 那台   Cap: 138   tailscale 1.98.10
```

`Cap` 是 `tailcfg` 的協議能力版本。「新版 client 不向舊 Cap 節點查詢分享清單」完美解釋了「請求連發都不發」，於是我就收工了，還寫進了筆記。

但這是**相關性，不是因果**。真正的差別是：正常那台的 Hostname 本來就全小寫，所以我隨手拼的路徑剛好對；另一台有大寫字母，就錯了。升級 tailscale 對這個問題毫無幫助。

教訓有兩層：

1. **找到一個「看起來完美」的差異時，先確認它能解釋全部現象，也要確認沒有更平凡的解釋。** 任兩台機器之間永遠找得到差異，第一個找到的不一定是原因。
2. **驗證成本通常遠低於推論成本。** 這個假設只要把 404 的 URL 換成 PROPFIND 回傳的 href 再試一次就會被推翻，三十秒的事——比讀 netmap、比對版本、查 `Cap` 語意都快。**能便宜地證偽時，不要先花力氣建構理論。**

---

## 六、在 Finder 掛載 Taildrive

設定完成後，Finder 按 `⌘K`：

```
http://100.100.100.100:8080
```

**不會跳帳密視窗**——Taildrive 的身分驗證靠 tailnet 本身，WebDAV 層不需要憑證。

腳本化掛載用 AppleScript 的 `mount volume`（比 `mount_webdav` 好，後者需要 root）：

```bash
osascript -e 'mount volume "http://100.100.100.100:8080"'
```

掛上後的結構：

```
/Volumes/100.100.100.100/
└── you@example.com/          ← tailnet 名稱，不是設定錯
    ├── machine-a/
    │   ├── home/
    │   └── downloads/
    └── machine-b/
```

確認伺服器能力：

```bash
curl -s -i -X OPTIONS http://100.100.100.100:8080/ | grep -i '^dav:'
# Dav: 1, 2
```

`Dav: 2` 代表支援 LOCK，這是 Finder 正常運作的必要條件。

### 6.1 開機自動掛載

登入時 `tailscaled` 未必就緒，所以要重試。寫成腳本配 LaunchAgent：

```bash
#!/bin/bash
VOL="/Volumes/100.100.100.100"
URL="http://100.100.100.100:8080"
for i in $(seq 1 30); do
  /sbin/mount | grep -q " on ${VOL} " && exit 0
  if /usr/bin/curl -s -m 5 -X PROPFIND -H "Depth: 0" "$URL/" -o /dev/null; then
    /usr/bin/osascript -e "mount volume \"$URL\"" >/dev/null 2>&1
    /bin/sleep 2
    /sbin/mount | grep -q " on ${VOL} " && exit 0
  fi
  /bin/sleep 10
done
exit 1
```

LaunchAgent 設 `RunAtLoad` 加 `StartInterval` 600，被手動卸載或網路中斷後會自己掛回來。

### 6.2 兩個 Finder 上的限制

**卷宗名稱改不掉。** WebDAV 掛載的名稱來自 URL 的 host，側邊欄只會顯示 `100.100.100.100`。想要好認的名字，只能另外放捷徑檔。

**沒有本機快取。** Finder 預覽或雙擊大檔會整份拉過網路。日常瀏覽、改文字檔、拖數十 MB 沒問題，大檔請改用 Taildrop。

---

## 七、安全提醒

**分享整個家目錄要想清楚。** `tailscale drive share home "$HOME"` 很方便，但 PROPFIND 列得出 `~/.ssh`、`~/.bash_history`、`~/.aws`、各種 token 檔。單人 tailnet 的暴露對象是自己的裝置，風險可控；但只要 tailnet 有第二個人，或你在手機上也裝了 Tailscale，就該收斂成具體目錄：

```bash
tailscale drive unshare home
tailscale drive share workspace ~/workspace
```

也可以在 grants 裡用 `"shares": ["workspace"]` 精確控制，而不是 `["*"]`。

**API key 用完就撤銷。** `tskey-api-*` 具備改寫整份 ACL 的權限，等同 tailnet 的管理權。用完到 admin console 的 Keys 頁面撤銷，別留在 shell history 或設定檔裡。

---

## 八、總結

| 需求 | 方案 | 需要 sudo？ |
| --- | --- | --- |
| 遠端桌面 | `.vncloc` 捷徑 + 定期重建腳本 | 否 |
| 推檔給任何裝置（含手機） | Taildrop + AppleScript droplet | 否 |
| Linux 自動收檔 | systemd **user** unit + linger | 否（除非要設 operator） |
| Finder 瀏覽讀寫遠端檔案 | Taildrive + WebDAV 掛載 | 否 |

幾個帶得走的心得：

1. **mDNS 不過 overlay 網路**——Finder 的自動探索在 VPN 情境下必然失效，這是設計使然，不用浪費時間找設定開關。
2. **Taildrive 是兩段式授權**——`nodeAttrs` 開功能、`grants` 給權限。只做一半的症狀是「看起來都成功但就是空的」，去分享端的 journal 找 `not permitted`。
3. **404 和 not permitted 是完全不同的故事**——前者是請求根本沒送出（多半是自己的路徑打錯），後者是送到了被拒（授權問題）。先分清楚再往下查。
4. **能便宜地證偽時，不要先花力氣建構理論**——我為 404 找到一個「兩台機器版本不同」的完美解釋，實際上只是 URL 大小寫拼錯。任兩台機器之間永遠找得到差異，第一個找到的不一定是原因。
5. **systemd user unit 比想像中能幹**——常駐服務不一定要 root，配上 linger 就能在未登入時運作。
6. **macOS 有很多不能程式化的角落**——Finder 側邊欄受 TCC 保護且無官方 API，Dock 反而可以用 `defaults` 改。遇到這種情況，接受它並設計成「使用者拖一次」的流程，比硬鑽有效率。
