# systemd

systemd 是現代多數 Linux 發行版的 **init system**（PID 1），負責開機後拉起並管理服務、掛載、裝置、socket 等。以平行化啟動與相依關係管理取代傳統 SysV init 的循序 script。

## Unit

systemd 管理的基本單位是 **unit**，依副檔名分類：

- `.service` — 服務（daemon）。
- `.target` — 一組 unit 的集合，類似傳統 runlevel（如 `multi-user.target`、`graphical.target`）。
- `.socket` / `.timer` / `.mount` / `.device` — socket 觸發、定時任務、掛載點、裝置等。

unit 檔常見於 `/usr/lib/systemd/system/`（套件提供）與 `/etc/systemd/system/`（本機覆寫，優先）。

## 常用 systemctl

```bash
systemctl status nginx          # 查看狀態
systemctl start/stop/restart nginx
systemctl enable/disable nginx  # 開機是否自動啟動
systemctl daemon-reload         # 改過 unit 檔後重新載入
systemctl list-units --type=service
```

## Journal (日誌)

systemd 用 `journald` 收集日誌，以 `journalctl` 查詢：

```bash
journalctl -u nginx        # 特定服務
journalctl -b              # 本次開機
journalctl -f              # 即時追蹤
```
