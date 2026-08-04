# 遠端控制 Server 的方式選擇

## 需求

我需要從本機傳送一些操作指令到遠端 server 去控制它。方式很多，差別在於**資料量、頻率、以及是單向下指令還是雙向互動**。

## 情境對照

| 情境 | 建議做法 | 為什麼 |
|---|---|---|
| 一次性的小資料 / 單一指令 | **stdin pipe** 或 `ssh + args` | 最輕量，不需要任何額外設定 |
| 一堆檔案要同步 | **rsync** | 只傳差異、可續傳、可保留權限與時間戳 |
| 要頻繁讀寫同一份檔案 | **sshfs** 或 **ControlMaster + scp** | 避免每次操作都重新建立 SSH 連線 |
| 兩邊程式要互相讀寫狀態 | **SSH port forward + Redis / SQLite** | 需要真正的雙向通道與共享狀態 |

## 各做法說明

### stdin pipe / ssh + args

最簡單的方式，直接把指令當參數傳過去：

```bash
# 直接下指令
ssh user@host 'systemctl restart myservice'

# 用 stdin 餵資料進去（適合腳本或小量資料）
cat script.sh | ssh user@host 'bash -s'
echo "$DATA" | ssh user@host 'cat > /tmp/data.txt'
```

優點是零設定、一行搞定。缺點是**每次執行都要重新建立一次 SSH 連線**（TCP 握手 + 金鑰交換），頻繁呼叫時延遲會很明顯。

### rsync

檔案多的時候不要用 `scp` 迴圈，用 `rsync`：

```bash
rsync -avz --progress ./build/ user@host:/opt/app/

# 常用選項
#   -a  archive，保留權限、時間戳、符號連結
#   -v  verbose
#   -z  傳輸時壓縮
#   -P  顯示進度並支援續傳
#   --delete  來源沒有的檔案在目標端也刪掉（做鏡像用，小心）
#   --exclude '*.o'  排除不需要的檔案
```

`rsync` 的核心價值是**只傳差異**：它會先比對兩端的檔案區塊，只送真正變動的部分。改一行程式碼重新部署時，差別非常大。

### ControlMaster：SSH 連線重用

如果就是要頻繁下指令，用 SSH 的 **ControlMaster** 把連線留著重複使用，之後每次 `ssh` 都走同一條既有連線，省掉握手成本。

在 `~/.ssh/config` 設定：

```
Host myserver
    HostName 192.168.1.100
    User alanhc
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
```

- `ControlMaster auto`：第一條連線當 master，之後的共用它。
- `ControlPath`：連線 socket 的存放路徑。
- `ControlPersist 10m`：最後一個 session 結束後，連線再保留 10 分鐘。

設定後 `ssh myserver 'uptime'` 的延遲會從數百毫秒降到幾乎瞬間。**這是最容易被忽略、但收益最大的一個設定。**

### sshfs：把遠端目錄掛到本機

```bash
sshfs user@host:/remote/path ~/mnt/remote
# 用完卸載
umount ~/mnt/remote            # macOS
fusermount -u ~/mnt/remote     # Linux
```

好處是之後所有本機工具（編輯器、`grep`、腳本）都能直接操作遠端檔案，不必意識到它在遠端。

**限制**：每次檔案操作都是一次網路往返，所以在上面跑 `find`、`grep -r` 或編譯會非常慢。適合「偶爾讀寫幾個檔案」，不適合「大量小檔案的密集 I/O」。

### SSH port forward + Redis / SQLite

當兩邊的**程式**需要互相讀寫狀態（而不只是我下指令、它執行），就需要一個真正的雙向通道。

```bash
# 本地 6379 轉發到遠端的 6379（遠端的 Redis 不必對外開 port）
ssh -N -L 6379:127.0.0.1:6379 user@host
```

- `-L`：**本地轉發**，本機的 port 連到遠端可達的位址。
- `-R`：**反向轉發**，遠端的 port 連回本機（本機在 NAT 後面時用這個）。
- `-N`：不執行遠端指令，只做轉發。

轉發建立後，本機程式連 `localhost:6379` 實際上就是在跟遠端的 Redis 說話，而 Redis 本身**完全不需要對公網開放**——所有流量都在 SSH 加密通道裡。

選 Redis 還是 SQLite：

- **Redis**：適合訊息佇列、即時狀態、pub/sub。兩邊都是常駐程式時的首選。
- **SQLite**：適合結構化的持久資料。但**不要透過 sshfs 掛載後多方寫入**——SQLite 的鎖依賴檔案系統的 locking 語意，網路檔案系統上會損毀資料庫。要共用 SQLite 就讓它待在單一台機器上，透過 API 存取。

## 選擇順序

1. 先試最簡單的 `ssh + args`。
2. 覺得慢 → 加 **ControlMaster**（多半就解決了）。
3. 要傳檔案 → **rsync**。
4. 要像本機一樣操作 → **sshfs**（但接受它慢）。
5. 程式要互相溝通 → **port forward + Redis**。

## 相關筆記

- [macmini / 遠端機器操作](./tools.md)
