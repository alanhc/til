---
title: serial over lan
hackmd:
  url: https://hackmd.io/YCvG3CJFSAmUFEWuB_doHA
  title: serial over lan
  lastSync: 2025-06-05T05:54:53.556Z
---
##  什麼是 SoL？
- **Serial over LAN** 是一種技術，允許使用者透過網路（通常是 Ethernet）來**遠端存取主機的序列埠（Serial Port）**，也就是說SoL是將傳統串列埠資料轉封包，經網路傳送，再還原為串列資料的過程。
## 爲什麼需要 SoL？
- 傳統串列埠（如 RS-232）需直接接線，非常不方便遠端操作。
- BMC（Baseboard Management Controller）透過 SoL：
	- 在作業系統開機前也能觀察主機輸出（BIOS/UEFI/Post）。
	- 可搭配 IPMI 或 Redfish 管理介面啟用/停止 SoL。
	- 達到「無人值守的伺服器管理」。

## Components

|組件|本質角色|解釋|
|---|---|---|
|主機 COM1|實體輸出|主機 BIOS/OS 的序列輸出通常連到此|
|BMC UART|中繼橋接|BMC 接收主機 UART 資料|
|IPMI LAN|傳輸媒介|BMC 將 UART 資料轉封包送往管理者|
|管理端|控制台|使用 `ipmitool sol activate` 之類指令遠端接收輸出|
## SoL 封包走向

```
+--------------------------------------+
| 主機 UART (串列埠 COM)                |
+--------------------------------------+
        |
        | UART 字元流 (bytes)
        V
+--------------------------------------+
| BMC UART 接收緩衝區                   |
| 將 bytes 包裝成 IPMI 封包 (RMCP+ UDP) |
+--------------------------------------+
        |
        | UDP/IP 封包 (IPMI SoL payload)
        V
+--------------------------------------+
| 遠端管理者 IPMI Console (ipmitool)     |
| 將封包還原成 UART 字元                |
+--------------------------------------+
```

## 封包格式（IPMI v2.0）
- SoL 是使用 **RMCP+（Remote Management Control Protocol）封包**，透過 UDP port `623`。
- 封包內包含：
	- `Payload Type = SerialOverLan`
	- `Sequence Number`
	- `Data`：真實的串列字元
	- `ACK/NACK`：可靠傳輸確認

## 常見 `ipmitool` 指令

| 指令                                                                 | 功能              |
| ------------------------------------------------------------------ | --------------- |
| `ipmitool -I lanplus -H <BMC_IP> -U <user> -P <pw> sol info`       | 查看 SoL 狀態       |
| `ipmitool -I lanplus -H <BMC_IP> -U <user> -P <pw> sol activate`   | 啟用 SoL，進入串列監控畫面 |
| `ipmitool -I lanplus -H <BMC_IP> -U <user> -P <pw> sol deactivate` | 關閉 SoL          |
| `ipmitool sol set timeout 15`                                      | 設定閒置 timeout    |
| `ipmitool sol set privilege-level admin`                           | 設定存取權限          |

## 常見使用場景（Usecases）
| Usecase              | 解釋                                             |
| -------------------- | ---------------------------------------------- |
| ✅ 遠端開機畫面觀察           | BIOS/POST 階段出現錯誤可即時察看                          |
| ✅ OS kernel panic 偵錯 | 如果有串列 console 輸出，可保留錯誤紀錄                       |
| ✅ 安裝 OS 時遠端互動        | Debian / CentOS / Ubuntu netinstall 可以完全透過 SoL |
| ✅ 偵錯無法登入的系統          | 無 SSH 時仍可存取 Console 觀察                         |
| ✅ 無人值守測試             | 搭配 PXE boot + SoL 可自動部署伺服器                     |

## 延伸
| 概念                         | 說明                                              |
| -------------------------- | ----------------------------------------------- |
| **Console Redirection**    | BIOS 設定，允許將畫面輸出轉導到串列埠                           |
| **IPMI v2.0**              | 所有 SoL 操作依據 IPMI v2.0 中 SerialOverLAN 指令定義      |
| **Redfish ConsoleService** | 現代 BMC 支援透過 Redfish 取代 IPMI SoL（如 WebSocket 串流） |


