# Ubuntu 常用指令

一些日常會用到的 Ubuntu 指令筆記。

## 硬體驅動

列出可用的裝置與建議驅動：

```
ubuntu-drivers devices
```

自動安裝建議的驅動（例如 NVIDIA 顯卡）：

```
sudo ubuntu-drivers autoinstall
```

## 套件管理 (apt)

```bash
sudo apt update              # 更新套件索引
sudo apt upgrade             # 升級已安裝的套件
sudo apt install <package>   # 安裝套件
sudo apt remove <package>    # 移除套件
apt list --installed         # 列出已安裝套件
```

## 服務管理 (systemctl)

```bash
sudo systemctl status <service>    # 查看服務狀態
sudo systemctl start/stop <service> # 啟動 / 停止服務
sudo systemctl enable <service>    # 設定開機自動啟動
journalctl -u <service>            # 查看服務 log
```

參考：[Ubuntu Server docs](https://documentation.ubuntu.com/server/)
