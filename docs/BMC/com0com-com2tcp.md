# com0com / com2tcp 筆記

> Windows 上的虛擬序列埠與 serial-over-TCP 橋接工具

---

## 1. com0com 是什麼

com0com 是 Windows 上的**虛擬 null-modem 驅動**（開源，kernel-mode driver）。安裝後它會成對建立虛擬序列埠，預設名稱是 `CNCA0 ↔ CNCB0`（可改成 `COM10`/`COM11` 之類）。

兩個埠的行為就像被一條 null-modem 線接在一起：

```
  App A  ──→  COM10 (CNCA0)  ═══  COM11 (CNCB0)  ──→  App B
                          虛擬對，無實體硬體
```

A 端寫進去的 byte，B 端立刻讀得到，完全不需要實體 UART 或 USB-serial。

## 2. com2tcp 是什麼

com0com 套件附的命令列工具，把一個 COM 埠橋接到 TCP socket：

- 可當 **client**（主動連到遠端）
- 可當 **server**（監聽某個 port）

同套件還有更強的 `hub4com`，能一對多分流（一個來源餵多個目的），並支援 **RFC2217**（telnet 序列埠協定，可協商 baud rate / 流控 / DTR、RTS）。

---

## 3. 為什麼重要

對做 BSP / firmware / 平台整合的人來說，serial console 幾乎是唯一在 kernel panic、bootloader 掛掉時還活著的通道。這兩個工具解決的問題：

| 情境 | 解法 |
|---|---|
| 沒有實體線也要測 serial 程式 | 虛擬對：一端跑你的程式，一端跑模擬器 / script |
| 兩個只會講 COM 的程式要互接 | 老 flash tool、廠商 debug utility 寫死只吃 COM 埠，虛擬對當膠水 |
| 一個 port 要給多個程式看 | 搭配 hub4com：一邊 log 到檔案，一邊你還在 terminal 互動 |
| 遠端的板子 UART 要拉到桌上 | 板子接 USB-serial 到遠端 Linux → 網路 → 本機虛擬 COM，PuTTY 打開就像板子在旁邊 |
| CI 自動化抓 boot log | 同上，console 變成可程式化的 TCP stream |
| BMC / SOL、QEMU、VM 的 serial 導出 | 同樣模式 |

---

## 4. 安裝

從 SourceForge 取得 com0com。**注意**：官方 3.0.0.0 的 x64 driver 沒有簽名，Win10/11 需要：

- 使用社群提供的 signed build（較建議），或
- 暫時開啟 test signing / 關閉 driver signature enforcement

Secure Boot 開著的機器要一併考慮。

### 用 setupc.exe 管理（需 admin，在安裝目錄下）

```bat
setupc.exe list
setupc.exe install PortName=COM10 PortName=COM11
setupc.exe change CNCA0 EmuBR=yes,EmuOverrun=yes
setupc.exe remove 0
```

也可以用 GUI 的 `setupg.exe`。

### 兩個關鍵參數

| 參數 | 說明 |
|---|---|
| `EmuBR=yes` | 真的模擬 baud rate 的傳輸速度。預設是全速，不管你設 115200。只有測 timing 敏感的程式才需要 |
| `EmuOverrun=yes` | **建議打開**。否則另一端沒人讀時，buffer 滿了會把寫入端整個卡住 |

---

## 5. com2tcp 用法

### 當 client：連到遠端序列埠伺服器

```bat
com2tcp --baud 115200 --parity n --data 8 --stop 1 ^
        \\.\CNCB0 192.168.1.50 5000
```

然後用 PuTTY 開 `COM10`（也就是 CNCA0 那一端），就通到遠端板子了。

### 當 server：把本機實體 COM3 開放給網路

```bat
com2tcp --baud 115200 \\.\COM3 5000
```

### RFC2217 模式（遠端可改 baud、控制 DTR/RTS）

```bat
com2tcp-rfc2217.bat \\.\CNCB0 192.168.1.50 2217
```

這支 batch 實際上是呼叫 `hub4com`。

---

## 6. Linux 對應端

### 把實體序列埠開成 TCP server

`ser2net` 設定檔（傳統格式）：

```
5000:raw:0:/dev/ttyUSB0:115200 8DATABITS NONE 1STOPBIT
```

臨時用 socat：

```bash
socat TCP-LISTEN:5000,reuseaddr,fork /dev/ttyUSB0,raw,b115200
```

### Linux 上做虛擬對（com0com 的對應物）

```bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
```

或安裝 `tty0tty`（kernel module 版，支援 modem control 訊號）。

---

## 7. 典型組合

```
[Windows 桌機]                         [遠端 Linux]        [目標板]
 PuTTY
   │
  COM10 (CNCA0)
   ║  com0com 虛擬對
  COM11 (CNCB0)
   │
 com2tcp ──────── TCP:5000 ────────→ ser2net ── USB-serial ──→ UART
```

---

## 8. 常見坑

- **COM 號衝突**：埠名撞到系統記憶的「已使用」COM 號時 `setupc` 會警告。直接指定沒人用的高號碼（COM10 以上）比較安全。
- **baud 設定是裝飾品**：虛擬對上的 baud / parity 預設不生效，真正決定速率的是 com2tcp 與實體端那邊的設定。
- **斷線不自動重連**：com2tcp 是純 raw 轉發。長時間 CI 用建議外面包個重試迴圈，或改用 hub4com。
- **驅動簽章**：每次 Windows 大版本更新後可能要重新處理簽章 / 重裝驅動。
- **buffer 卡死**：忘了設 `EmuOverrun=yes`，沒人讀的那端會把寫入端 block 住。

---

## 9. 替代方案

| 類型 | 選項 |
|---|---|
| 商業虛擬 COM | HW Virtual Serial Port、Virtual Serial Port Driver（Eltima） |
| Windows 免驅動 | `plink -serial`、Python `pyserial` + socket 自己寫 20 行 |
| Linux 虛擬對 | `socat` pty pair、`tty0tty` |
| Linux serial server | `ser2net`、`socat`、`conserver` |
| 硬體方案 | 序列埠 console server（Opengear、Digi、Raritan 等） |

---

## 參考

- [com0com 專案](https://sourceforge.net/projects/com0com/)
- com0com README（含 setupc 完整參數與 hub4com 說明）
- [ser2net](https://sourceforge.net/projects/ser2net/)
