# SSH Tunnel：從協定機制到多人系統下的安全邊界

> 本文整理 SSH port forwarding 的協定層原理、實務操作，以及在共用（multi-user）機器上使用時真正的威脅模型。內容全部取材自公開規格（RFC 4251/4253/4254）與 OpenSSH man page，不涉及任何非公開資訊。

---

## 為什麼值得把原理搞清楚

大部分人對 SSH tunnel 的認識停在「`-L` 可以連內網」。這在會用的層次夠了，但一旦要回答下面這幾個問題就會卡住：

- 為什麼 `-L 3306:localhost:3306` 裡的 `localhost` 不是我這台？
- `ssh -J bastion` 和 `ssh -L` 走跳板，差在哪？
- 大檔案走 tunnel 為什麼特別慢？
- 在多人共用的 build server 上開 tunnel，到底安不安全？

這些答案都在協定的 channel 機制與端點的 socket 語意裡。

---

## 一、SSH 的三層結構

RFC 把 SSH 拆成三層，各自獨立：

| 層 | RFC | 負責 |
|---|---|---|
| Transport Layer | RFC 4253 | 金鑰交換、伺服器認證、對稱加密、完整性保護、壓縮 |
| Authentication Layer | RFC 4252 | 使用者認證（publickey / password / keyboard-interactive） |
| Connection Layer | RFC 4254 | **在單一加密連線上多工出多條 channel** |

Tunnel 完全是第三層的產物。Transport layer 提供了一條「已加密、已認證、可靠」的位元組管道，Connection layer 則在這條管道裡切出多條邏輯通道。

### Channel 的意義

一條 TCP 連線（通常 port 22）上，可以同時存在：

```
        ┌──────────────── 單一加密 TCP 連線 ────────────────┐
        │  channel 0 : session      (你的互動 shell)        │
        │  channel 1 : session      (另一個 sftp subsystem) │
        │  channel 2 : direct-tcpip (你的 -L 8080 轉發)     │
        │  channel 3 : direct-tcpip (同一個 -L 的第二個連線) │
        └───────────────────────────────────────────────────┘
```

每條 channel 有獨立編號、獨立的流量控制視窗（`SSH_MSG_CHANNEL_WINDOW_ADJUST`），彼此不干擾。這就是為什麼你可以在同一個 ssh session 裡一邊操作 shell、一邊跑著幾條 port forwarding。

關鍵認知：**channel 傳的是 TCP 的 payload（application data），不是 IP 封包。** SSH tunnel 因此是 application-layer 的 TCP relay，不是 L3 的 VPN。這一點決定了它所有的能力上限與安全性質。

---

## 二、三種 forwarding 的協定行為

### `-L`：Local forwarding → channel type `direct-tcpip`

```bash
ssh -L 8080:jenkins.example.com:80 alan@bastion
```

發生的事：

1. **client** 在本機 `bind()` + `listen()` 127.0.0.1:8080
2. 有人 `connect()` 進來 → client 送出 `SSH_MSG_CHANNEL_OPEN`，channel type 為 `direct-tcpip`，附帶欄位：
   - `host to connect` = `jenkins.example.com`
   - `port to connect` = `80`
   - `originator IP address` / `originator port`（連進來的人是誰）
3. **server** 收到後，由**它自己**去 `connect()` 目標，成功則回 `CHANNEL_OPEN_CONFIRMATION`
4. 之後雙向搬 `SSH_MSG_CHANNEL_DATA`

> **這解釋了第一個常見誤解**：`host to connect` 是字串，交給 server 端解析與連線。所以 `-L 3306:localhost:3306` 的 `localhost` 指的是 **bastion 的 localhost**，不是你的機器。同理，內網才有的 DNS 名稱在這裡是可以用的。

### `-R`：Remote forwarding → global request + `forwarded-tcpip`

```bash
ssh -R 9000:localhost:3000 alan@public-server
```

1. client 送出 **global request** `tcpip-forward`，請求 server 幫忙 listen 9000
2. server `bind()` + `listen()`（預設綁 127.0.0.1，受 `GatewayPorts` 控制）
3. 有人連進 server 的 9000 → **server** 送出 `CHANNEL_OPEN`，type 為 `forwarded-tcpip`
4. client 收到後由**它自己**去 `connect()` `localhost:3000`

方向完全相反：`direct-tcpip` 由 client 發起、server 負責連線；`forwarded-tcpip` 由 server 發起、client 負責連線。取消用 `cancel-tcpip-forward`。

`-R` 的價值在於**反轉連線方向**：防火牆／NAT 後面的機器連不進去，但它可以主動連出來。遠端 debug、把測試板暴露給外部 CI，都是這個模式。

### `-D`：Dynamic forwarding → SOCKS 前端 + `direct-tcpip`

```bash
ssh -D 1080 alan@bastion
```

協定上**沒有**新的 channel type。差別只在 client 端多實作了一個 SOCKS4/5 server：

1. client listen 1080，跑 SOCKS 交握
2. 從 SOCKS request 讀出「這次要連哪裡」
3. 用讀到的目標開一條 `direct-tcpip`

所以 `-D` = 「目標由每個連線動態決定的 `-L`」。因為目標名稱是交給遠端解析的，client 端要用 `socks5h`（h = hostname resolution at proxy）才能解內網域名：

```bash
curl --socks5-hostname localhost:1080 http://wiki.example.com/
git config --global http.proxy socks5h://localhost:1080
```

### 順帶一提：真正的 L3 tunnel

`-w` 搭配 sshd 的 `PermitTunnel yes` 會建立 `tun`/`tap` 介面，那才是 IP 層的 VPN（可以走 UDP、ICMP）。實務上很少用，效能與維運都不如 WireGuard，但知道它存在有助於區分「port forwarding」與「VPN」這兩件常被混談的事。

---

## 三、實務用法

### 基本三招

```bash
# -L：把遠端服務拉到本機
ssh -fN -L 8080:jenkins.example.com:80 alan@bastion

# -R：把本機服務推到遠端
ssh -fN -R 9000:localhost:3000 alan@public-server

# -D：動態 SOCKS proxy
ssh -fN -D 1080 alan@bastion
```

`-f` 背景執行、`-N` 不執行遠端指令（只做轉發）。

### 一定要加的 `ExitOnForwardFailure`

```bash
ssh -fN -o ExitOnForwardFailure=yes -L 8080:jenkins.example.com:80 bastion
```

預設情況下，**forwarding 失敗時 ssh 不會退出**，只印一行 warning 就繼續跑。加上 `-f` 之後你根本看不到。結果就是你以為 tunnel 開好了，實際上 8080 上聽著的是別的東西。這個選項務必打開。

### 寫進 `~/.ssh/config`

```
Host bastion
    HostName bastion.example.com
    User alan
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ExitOnForwardFailure yes

Host buildsrv
    HostName build01.example.com
    User alan
    ProxyJump bastion
    LocalForward 8080 jenkins.example.com:80
    LocalForward 5555 dut-board.example.com:5555

Host *
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
```

之後 `ssh buildsrv` 就自動帶起跳板與兩條轉發。

### 對已存在的連線動態增減轉發

`ControlMaster` 除了讓第二次連線瞬開，還開放了 control 指令：

```bash
ssh -O check   buildsrv                        # master 還活著嗎
ssh -O forward -L 9090:other.example.com:80 buildsrv   # 事後追加
ssh -O cancel  -L 9090:other.example.com:80 buildsrv   # 移除
ssh -O exit    buildsrv                        # 關閉 master
```

### 長時間不斷線

`ServerAliveInterval` 只負責**偵測**斷線，不會重連。要自動重連：

```bash
autossh -M 0 -fN \
  -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" \
  -o "ExitOnForwardFailure=yes" \
  -L 8080:jenkins.example.com:80 bastion
```

`-M 0` 表示不用 autossh 自己的 monitoring port，把存活判斷交給 ServerAlive 機制。要開機自動跑就包成 systemd user unit 或 launchd plist。

---

## 四、`ProxyJump` 與 `LocalForward` 的加密邊界差異

這是最容易被忽略、但影響最大的一組差異。

**用 `-L` 手動穿跳板：**

```
你 ══加密══> bastion ──明文──> target
```

Bastion 上那一段是**解密後**再重新連出去的。Bastion 的 root（或任何能 dump 該 process memory 的人）看得到完整內容，包含你打進 web UI 的帳密。

**用 `-J` / `ProxyJump`：**

```
你 ══════════加密════════════> target
      (bastion 只搬密文)
```

Bastion 只是把你的 SSH 位元組流往前送（`direct-tcpip` 到 target:22），你和 target 之間有獨立的一組金鑰交換與 host key 驗證。Bastion 看不到內容，也無法冒充 target。

```bash
ssh -J bastion target-host
ssh -J bastion1,bastion2 target       # 多層
scp -J bastion file.zip target:/tmp/
rsync -e "ssh -J bastion" -av src/ target:/dst/
```

**結論：只要目標本身能跑 SSH，一律用 `-J`，不要用 `-L` 手動疊跳板。** `-L` 留給「目標不是 SSH 服務」的情況（web UI、資料庫、VNC）。

---

## 五、多人系統下的威脅模型

前面談的加密，防的是**網路上的竊聽者**。但在共用機器上，真正的威脅是**同一台機器上的其他 local user**，而 SSH tunnel 對這個威脅**幾乎沒有任何防護**。

原因很單純：**loopback 上的 TCP port 沒有 per-user 存取控制**。核心不會問「哪個 UID 在連 127.0.0.1:8080」。

### 風險 1：你開的 forward，全機器共用

```bash
ssh -fN -L 8080:jenkins.example.com:80 bastion
```

這台機器上任何帳號執行 `curl http://localhost:8080/`，都會透過**你的 SSH session、以你的身分**進到內網 Jenkins。`-D 1080` 更嚴重 —— 等於幫全機器的人開了一個進內網的 SOCKS proxy，而且無法限制目標。

### 風險 2：Port squatting（搶 port）

如果你習慣固定用 8080，其他使用者可以**搶先** bind 它，架一個假的服務。你之後執行 `-L 8080:...` 會失敗，但：

- 沒加 `ExitOnForwardFailure` → ssh 不會退出
- 加了 `-f` → 你看不到 warning

於是你把瀏覽器指向 `localhost:8080`，帳密直接送給對方。這是實際可行的攻擊，不是理論推演。緩解：`ExitOnForwardFailure=yes` + 隨機高位 port + 開完用 `ss -lntp | grep <port>` 確認 listener 是自己的 process。

### 風險 3：Agent forwarding（`-A`）—— 最嚴重的一項

`ssh -A` 會把 `$SSH_AUTH_SOCK` 暴露到遠端。那個 socket 權限是 0600，但：

- **root 可以直接使用它**
- 任何以你的 UID 執行的 process 都可以使用它（跑錯的 script、被入侵的 CI job）

攻擊者**不需要你的私鑰**，只要在你連線期間借用 agent 簽章，就能登入所有你有權限的機器。

**在共用機器上永遠不要用 `-A`。** 需要跳板就用 `ProxyJump`（它根本不碰 agent 轉發）。真的必須用 agent 時：

```bash
ssh-add -c -t 3600 ~/.ssh/id_ed25519    # -c 每次簽章跳確認，-t 一小時後自動移除
```

### 風險 4：ControlMaster socket

`~/.ssh/cm-*` 檔案權限擋得住一般使用者，擋不住 root，也擋不住任何以你 UID 執行的程式。連上該 socket 就是**免認證**直接進 target。共用機器上建議關掉 `ControlMaster`，或至少把 `ControlPersist` 縮到很短。

### 風險 5：稽核歸屬

Bastion 的 log 記錄的是你的帳號。別人透過你的 tunnel 做的任何事，事後追查全部算在你頭上。

### 緩解：改用 Unix domain socket

OpenSSH 6.7 起，`-L` / `-R` 支援 Unix domain socket。這樣**檔案系統權限就成了存取控制**：

```bash
mkdir -p ~/.tunnels && chmod 700 ~/.tunnels
ssh -fN -L ~/.tunnels/jenkins.sock:jenkins.example.com:80 bastion

curl --unix-socket ~/.tunnels/jenkins.sock http://jenkins.example.com/
```

限制是不是所有 client 都支援 Unix socket：`curl`、`docker`、`psql`、`nc -U` 可以，一般瀏覽器不行。

`-R` 方向要在 server 端補上：

```
StreamLocalBindMask 0177        # socket 建成 0600
StreamLocalBindUnlink yes       # 重連時清掉舊 socket
```

### 最好的答案

**不要在共用機器上開 tunnel。** Tunnel 開在自己的筆電，需要在遠端跑東西時用 `ssh -J` 把指令送過去。這句話解掉上面全部五項。

---

## 六、Server 端強化

如果你是管跳板機的人，預設值不該直接上線：

```
# /etc/ssh/sshd_config

# 全域預設：全關
AllowAgentForwarding no
AllowTcpForwarding   no
GatewayPorts         no
PermitTunnel         no
X11Forwarding        no

# 只對特定群組開，且白名單目標
Match Group tunnel-users
    AllowTcpForwarding yes
    PermitOpen jenkins.example.com:80 gerrit.example.com:29418
    PermitListen 127.0.0.1:9000
    ForceCommand /bin/false
```

重點選項：

| 選項 | 作用 |
|---|---|
| `PermitOpen` | `-L` / `-D` 可以連往的目標白名單。**最關鍵的一項** |
| `PermitListen` | `-R` 可以 listen 的位址白名單 |
| `GatewayPorts` | `-R` 是否允許綁 0.0.0.0（預設 no，維持 no） |
| `ForceCommand /bin/false` | 只能轉發、不能開 shell |

也可以下放到單一金鑰，避免整組帳號都放寬：

```
# ~/.ssh/authorized_keys
restrict,port-forwarding,permitopen="jenkins.example.com:80" ssh-ed25519 AAAA... alan@laptop
```

`restrict` 會先關掉所有功能，再逐項開回來 —— 比手寫一長串 `no-agent-forwarding,no-X11-forwarding,no-pty,...` 更不容易漏掉新版本新增的功能。

---

## 七、效能：為什麼大檔案走 tunnel 特別慢

兩個獨立的原因疊在一起：

**1. TCP-over-TCP meltdown**

內層 TCP 和外層 TCP 各自有重傳與壅塞控制。外層丟包重傳造成延遲抖動，內層誤判為壅塞而自己也重傳並縮小視窗，兩層互相放大，吞吐量崩塌。這是所有 TCP-in-TCP 隧道的共通問題（也是 WireGuard 選 UDP 的原因之一）。

**2. Channel window（流量控制視窗）**

RFC 4254 的 channel 有自己的視窗機制，接收端用 `CHANNEL_WINDOW_ADJUST` 通知可再收多少。OpenSSH 的預設視窗是固定值，在**高頻寬 × 高延遲**（大 BDP）的路徑上會成為瓶頸 —— 傳送端把視窗塞滿後就得停下來等對方 adjust。跨國連線特別明顯。

> 註：具體的預設視窗大小在 OpenSSH 各版本間有調整過，需要精確數字請查對應版本的 `channels.c`（`CHAN_TCP_WINDOW_DEFAULT`）。歷史上 HPN-SSH patch set 主要就是在放大這個視窗與緩衝區。

**實務建議：純檔案傳輸不要走 forward，直接用 `-J`：**

```bash
scp -J bastion bigfile.tar.gz target:/tmp/
rsync -e "ssh -J bastion" -avP src/ target:/dst/
```

這樣只有一層 TCP，也避開了 forward channel 的視窗限制。

---

## 八、常見錯誤訊息對照

| 訊息 | 原因 |
|---|---|
| `bind: Address already in use` | 本機 port 被佔。`lsof -i :8080` 或 `ss -lntp` 查 |
| `channel N: open failed: administratively prohibited` | server 端 `AllowTcpForwarding no`，或 `PermitOpen` 未放行該目標 |
| `channel N: open failed: connect failed` | server 連得到 sshd，但連不到你指定的目標（DNS 錯、目標沒開、目標防火牆） |
| `Warning: remote port forwarding failed for listen port 9000` | server 上該 port 被佔，或被 `PermitListen` 擋下 |
| 連上了但拿到錯誤的服務 | `-L` 目標的 `localhost` 被解讀成 server 端的 localhost；或被 port squatting |

---

## 檢查清單

日常使用：

- [ ] 一律加 `ExitOnForwardFailure=yes`
- [ ] 目標是 SSH 服務就用 `-J`，不要用 `-L` 疊跳板
- [ ] 用完就關（`ssh -O exit`），不留過夜
- [ ] 不用固定 port，用隨機高位 port
- [ ] `-f` 之後確認 `ss -lntp` 的 listener 真的是自己的 process

共用機器：

- [ ] **絕不使用 `-A`**；必要時 `ssh-add -c -t`
- [ ] 關閉或縮短 `ControlMaster` / `ControlPersist`
- [ ] 能用 Unix domain socket 就用，靠 0700 目錄權限保護
- [ ] 絕不 `GatewayPorts yes` + `-R 0.0.0.0:...`

管理端：

- [ ] 全域 `AllowTcpForwarding no`，用 `Match` 群組例外
- [ ] 一定要設 `PermitOpen` 白名單
- [ ] 純 tunnel 帳號配 `ForceCommand /bin/false`
- [ ] `authorized_keys` 用 `restrict` 起手再逐項開放

---

## 一句話總結

SSH tunnel 的加密只保護「兩台機器之間」那一段；tunnel 的兩個**端點**都是本機 socket，而本機 socket 的存取控制不歸 SSH 管。理解這條邊界在哪，就能判斷什麼時候該用 `-J`、什麼時候該用 Unix socket、什麼時候根本不該在這台機器上開 tunnel。

---

## 參考資料

- RFC 4251 — The Secure Shell (SSH) Protocol Architecture
- RFC 4252 — The Secure Shell (SSH) Authentication Protocol
- RFC 4253 — The Secure Shell (SSH) Transport Layer Protocol
- RFC 4254 — The Secure Shell (SSH) Connection Protocol（channel 機制、`direct-tcpip` / `forwarded-tcpip` / `tcpip-forward` 定義）
- `ssh(1)`、`ssh_config(5)`、`sshd_config(5)`、`ssh-agent(1)`、`ssh-add(1)` man pages
- OpenSSH release notes（Unix domain socket forwarding 自 6.7 起、`ProxyJump` 自 7.3 起）
