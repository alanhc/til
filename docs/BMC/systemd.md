# systemd

**systemd** 是現代 Linux 的 init 系統與服務管理員，PID 1 就是它。OpenBMC 直接採用 systemd 管理所有背景服務：Redfish server、IPMI daemon、感測器監控、電源狀態機……全部都是 systemd unit。

BMC 上「某個功能沒起來」時，第一件事幾乎都是用 `systemctl` 看服務狀態、用 `journalctl` 看它的 log。

## unit：systemd 的管理單位

systemd 把所有被管理的東西抽象成 **unit**，用副檔名區分型別：

| 型別 | 用途 |
|---|---|
| `.service` | 一支背景服務（daemon），最常見 |
| `.target` | 一組 unit 的集合，用來表達「系統到達某個狀態」 |
| `.socket` | socket 啟動（有連線才拉起對應 service） |
| `.timer` | 定時觸發（取代 cron） |
| `.mount` / `.path` | 掛載點 / 檔案路徑監看 |

### service

一個 `.service` 描述「怎麼啟動一支程式、失敗時怎麼辦、依賴誰」。典型內容：

```ini
[Unit]
Description=Phosphor Hwmon Sensor Monitor
After=xyz.openbmc_project.EntityManager.service

[Service]
ExecStart=/usr/bin/phosphor-hwmon-readd
Restart=always
Type=dbus
BusName=xyz.openbmc_project.Hwmon

[Install]
WantedBy=multi-user.target
```

幾個關鍵欄位：
- `ExecStart`：實際要執行的指令。
- `Type`：啟動型態。`simple` 是前景程式；`dbus` 表示服務要等到在 D-Bus 上註冊到 `BusName` 才算啟動完成（OpenBMC 大量使用）；`oneshot` 是跑完就結束的一次性工作。
- `Restart=always`：掛掉自動重啟，BMC 上的服務通常都設這個。
- `After` / `Requires` / `Wants`：定義啟動順序與依賴。`After` 只管順序，`Requires` 是強依賴（對方失敗自己也不啟動），`Wants` 是弱依賴。

### target

**target 是「同步點」，不是程式**。它本身什麼都不做，只用來表達「系統已經到達某個階段」，讓其他 unit 可以掛在它上面一起被拉起。可以把它想成 SysV init 時代 runlevel 的一般化版本。

常見 target：

| target | 意義 |
|---|---|
| `multi-user.target` | 一般多使用者文字模式（BMC 的預設目標） |
| `basic.target` | 基本系統已就緒 |
| `sysinit.target` | 早期初始化完成 |
| `poweroff.target` / `reboot.target` | 關機 / 重開 |

OpenBMC 另外定義了一整組自訂 target 來描述主機電源狀態機，例如 `obmc-chassis-poweron@0.target`、`obmc-host-start@0.target`。「開機主機」這個動作，實際上就是啟動對應的 target，然後掛在它底下的一連串 service 依序執行。

```bash
systemctl list-units --type=target      # 目前啟動了哪些 target
systemctl get-default                   # 預設開機目標
systemctl list-dependencies multi-user.target
```

## unit 檔在檔案系統的位置

同名 unit 依以下優先序覆寫，**越前面優先權越高**：

| 路徑 | 用途 |
|---|---|
| `/etc/systemd/system/` | 系統管理者自訂／覆寫，優先權最高 |
| `/run/systemd/system/` | 執行期產生（重開就消失） |
| `/lib/systemd/system/`（或 `/usr/lib/systemd/system/`） | 套件安裝的原始 unit，OpenBMC 各元件的 service 檔都在這 |

另外：
- **enable 的實作方式是符號連結**。`systemctl enable foo.service` 實際上是依 `[Install]` 段的 `WantedBy=`，在 `/etc/systemd/system/multi-user.target.wants/` 建一個指向原始 unit 的 symlink。
- **drop-in 覆寫**：想只改某幾個欄位而不整份複製，可在 `/etc/systemd/system/foo.service.d/override.conf` 放片段設定。`systemctl edit foo.service` 會幫你建這個檔。
- 改完 unit 檔一定要 `systemctl daemon-reload`，systemd 才會重新讀取。

```bash
systemctl cat foo.service        # 看實際生效的完整內容（含 drop-in）
systemctl show foo.service       # 看所有解析後的屬性
```

## 常用操作

```bash
systemctl status  <unit>     # 狀態 + 最近幾行 log（最常用）
systemctl start   <unit>
systemctl stop    <unit>
systemctl restart <unit>
systemctl enable  <unit>     # 設定開機自動啟動
systemctl disable <unit>
systemctl mask    <unit>     # 徹底禁用（連手動 start 都擋）

systemctl list-units --failed   # 找出所有啟動失敗的服務
systemctl list-unit-files       # 看每個 unit 的 enable/disable 狀態
```

## journal（journald）與 journalctl

systemd 的 log 由 **journald** 統一收集，存成**二進位格式**（不是純文字），所以必須用 `journalctl` 讀，不能直接 `cat`。它會把 kernel log、各 service 的 stdout/stderr、以及程式透過 syslog API 送出的訊息全部收在一起，並附上是哪個 unit、哪個 PID、什麼優先權。

```bash
journalctl -u <unit>            # 只看某個服務的 log
journalctl -f                   # 即時追蹤（等同 tail -f）
journalctl -b                   # 只看這次開機以來
journalctl -b -1                # 上一次開機的 log（查重開原因用）
journalctl -p err               # 只看 error 以上等級
journalctl --since "10 min ago"
journalctl -k                   # 只看 kernel 訊息（等同 dmesg）
journalctl --disk-usage         # journal 佔了多少空間
journalctl --vacuum-size=50M    # 清到只剩 50M
```

BMC 上要特別注意兩件事：

1. **journal 預設可能只存在記憶體**（`/run/log/journal/`），**一重開就沒了**。要保留跨重開的 log 需設定 `Storage=persistent`（存到 `/var/log/journal/`），但 BMC 的 flash 空間有限且有寫入壽命問題，要一併設定 `SystemMaxUse=` 之類的上限。
2. 追查當機原因時，`journalctl -b -1` 常常比什麼都有用——但前提是上面那點有設好。

## 參考

- [systemd.service(5)](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [systemd.unit(5)](https://www.freedesktop.org/software/systemd/man/systemd.unit.html)
- [OpenBMC — 電源狀態機與 target 設計](https://github.com/openbmc/docs/blob/master/architecture/openbmc-systemd.md)
