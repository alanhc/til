# SOL（Serial over LAN）

**SOL** 讓管理者透過網路存取主機（host）的序列埠 console，不必實體接一條 serial cable。BMC 把 host 的 serial 資料封裝進 IPMI over LAN 的封包，經網路轉送給遠端 client，達成遠端看 BIOS/開機訊息與登入 console。

network package

port

rmcp+

## 運作要點

- **RMCP+**：SOL 走 IPMI v2.0 的 **RMCP+**（Remote Management Control Protocol Plus）協定，相較舊版 RMCP 支援加密與更強的 session 驗證（RAKP 金鑰交換），較為安全。
- **port（連接埠）**：IPMI over LAN / RMCP+ 使用 **UDP port 623**。SOL 的序列資料就是包在這些 network package（封包）裡傳輸。
- **資料流向**：host serial ⇄ BMC（擷取/緩衝）⇄ 網路封包（RMCP+）⇄ 遠端 client 的虛擬終端機。

## 使用範例

```bash
# 啟動 SOL session
ipmitool -I lanplus -H <bmc-ip> -U <user> -P <pass> sol activate
```

- `-I lanplus` 即指定使用 IPMI v2.0 / RMCP+ 介面。
- 離開 SOL session 的預設跳脫序列為 `~.`。
