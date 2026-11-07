---
title: "BMC IPMI 驗證實戰（一）：基礎觀念與通用測試方法"
sidebar_label: "IPMI 驗證（一）基礎與方法"
tags: [bmc, ipmi, ipmitool, validation]
---

# BMC IPMI 驗證實戰（一）：基礎觀念與通用測試方法

> TL;DR：IPMI 命令「回了 `00`」不代表功能正確。驗證一顆 BMC，要同時看 **byte-level 的回應**、**設定在重開後是否保留**、**權限與介面限制**，以及**實機行為和 SEL 紀錄是否對得上**。這篇先講 IPMI 命令的組成、連線方式、Completion Code，再整理一套可以套用到所有命令類別的測試方法。

> **BMC IPMI 驗證實戰系列**
> 1. [基礎觀念與通用測試方法](./ipmi-validation-1-basics.md)
> 2. [各命令類別的測試重點](./ipmi-validation-2-commands.md)
> 3. [OEM 命令、韌體更新與命令速查](./ipmi-validation-3-firmware-cheatsheet.md)

> 本系列依據公開的 IPMI v2.0 rev 1.1、DCMI v1.5 與 HPM.1 規格整理，搭配開源工具 `ipmitool`。內容是通用的測試思路，不針對任何特定廠商或平台；不同 BMC 韌體的實作可能不同，回傳值請以手上平台的規格為準。

---

## 0. 為什麼要認真測 BMC

BMC（Baseboard Management Controller）是伺服器主機板上一顆獨立的小電腦。主機關機時它還醒著，負責監控溫度、電壓、風扇，記錄硬體事件，也讓維運人員能從遠端開關機、看 console、更新韌體。在資料中心裡，當主機掛掉、OS 連不上時，BMC 往往是**唯一還能用的管道**。

IPMI（Intelligent Platform Management Interface）是 BMC 最基本的管理介面。現在新平台多半也支援 Redfish，但 IPMI 因為簡單、工具成熟、BIOS 和 OS 都依賴它（KCS 介面、SEL、Watchdog），仍然是驗證時繞不過去的一塊。

BMC 的 bug 有個麻煩的特性：**平常不會被發現，出事時才爆**。例如：
- Power Restore Policy 設成 Always On，停電復電後機器卻沒開起來。
- Watchdog 逾時沒有 reset，當機的主機就一直卡著。
- SEL 寫滿後不再記錄，事後查不到故障原因。
- 低權限帳號能下關機命令，變成安全漏洞。

所以 BMC 驗證的重點不只是「命令能不能跑」，而是「在各種情境下，行為是否符合規格」。


---

## 1. 基本觀念

### IPMI 命令的組成

每個 IPMI request 由 **NetFn（Network Function）+ Command + Request Data** 組成。response 的第一個 byte 是 **Completion Code**，`ipmitool raw` 預設只在出錯時顯示，成功（`00`）時會省略。

| NetFn | 名稱 | 主要內容 |
|---|---|---|
| `0x00` | Chassis | 電源控制、開機選項、Restart Cause |
| `0x04` | Sensor/Event（S/E） | Sensor、Event、PEF |
| `0x06` | App | BMC 本身、Watchdog、Session、User、Channel |
| `0x0A` | Storage | FRU、SDR、SEL |
| `0x0C` | Transport | LAN、Serial/Modem、SOL |
| `0x2C` | Group Extension | DCMI（Group ID `0xDC`）等 |
| `0x2E` | OEM/Group | 廠商自訂，前 3 bytes 為 IANA Enterprise Number |
| `0x30`–`0x3F` | OEM | 廠商自訂 |

### 連線介面

| 方式 | 介面 | ipmitool 用法 | 說明 |
|---|---|---|---|
| In-band | KCS / BT / SSIF | `ipmitool <cmd>`（Linux 需載入 `ipmi_devintf`、`ipmi_si`） | 從主機 OS 直接跟 BMC 溝通，不需帳密 |
| Out-of-band | RMCP+（IPMI 2.0） | `ipmitool -I lanplus -H <IP> -U <USER> -P <PASS> <cmd>` | 透過網路，需要認證 |

小技巧：用 `-E` 從環境變數 `IPMI_PASSWORD` 讀密碼，避免密碼留在 shell history。

```bash
export IPMI_PASSWORD='<PASS>'
alias ipmi='ipmitool -I lanplus -H <IP> -U <USER> -E'
ipmi mc info
```

### 常見 Completion Code

| Code | 意義 | 測試時常見情境 |
|---|---|---|
| `00` | 成功 | — |
| `C1` | Invalid Command | BMC 未實作這個命令 |
| `C5` | Reservation ID 無效或已取消 | SEL/SDR 操作中途被其他 reserve 打斷 |
| `C7` | Request data length invalid | 參數 byte 數不對 |
| `C9` | Parameter out of range | 數值超出允許範圍 |
| `CB` | Requested data not present | 不存在的 sensor、record、user ID |
| `CC` | Invalid data field | 欄位值不合法 |
| `D4` | Insufficient privilege | 權限不足，例如 User 等級的帳號執行 Admin 命令 |
| `D5` | Not supported in present state | 狀態不允許，例如某些命令只能從 system interface 執行 |
| `D6` | Sub-function disabled | 命令被 Set Command Enables 停用 |

---

## 2. 通用測試方法

每個命令類別都可以套用以下幾個面向。

1. **raw 與 string 雙驗證**：同一個功能分別用 `ipmitool raw` 和字串命令（例如 `mc info`）執行，兩者解析出的結果要一致。raw 驗證 BMC 的 byte-level 行為，string 驗證工具和實作的相容性。
2. **Set → Get → 還原**：寫入後讀回比對，測完務必恢復原值，避免影響後續測項。
3. **逐 byte 對照規格**：response 每個 byte 都要對照規格的欄位定義；保留（reserved）位元應為 0。
4. **負面測試**：
   - 不合法的參數 → 應回 `CC` / `C9` / `C7`
   - 不存在的 ID → `CB`
   - 權限不足 → `D4`
   - 規格限定只能走 system interface 的命令，從 LAN 送出 → 應被拒絕
5. **持久性**：設定在 `mc reset cold`、`mc reset warm`、AC power cycle 之後是保留還是回到預設值，要符合規格或平台定義（volatile / non-volatile）。
6. **實際行為驗證**：命令成功不代表功能正確。電源、Watchdog、Sensor event 這類測項要搭配實機現象（LED、螢幕、風扇、電源狀態）和 SEL 紀錄來判定。
7. **介面覆蓋**：重要命令在 in-band 和 out-of-band 都至少驗證一次。

---

下一篇：[各命令類別的測試重點](./ipmi-validation-2-commands.md)——把這套方法套到 App、Chassis、Sensor/Event、Storage、Transport、DCMI 六大類命令上。

## 參考資料

- *Intelligent Platform Management Interface Specification v2.0 rev 1.1*
- *Data Center Manageability Interface (DCMI) Specification v1.5*
- *PICMG HPM.1 Firmware Upgrade Specification*
- `man ipmitool`
