---
title: "BMC IPMI 驗證實戰（二）：各命令類別的測試重點"
sidebar_label: "IPMI 驗證（二）命令類別"
tags: [bmc, ipmi, ipmitool, validation]
---

# BMC IPMI 驗證實戰（二）：各命令類別的測試重點

> TL;DR：依照 IPMI 2.0 的 NetFn 分類，逐類整理命令、`ipmitool` 用法和測試重點。共通原則是[上一篇](./ipmi-validation-1-basics.md)講的：raw 與 string 雙驗證、Set → Get → 還原、負面測試、持久性，以及用實機行為和 SEL 判定結果。

> **BMC IPMI 驗證實戰系列**
> 1. [基礎觀念與通用測試方法](./ipmi-validation-1-basics.md)
> 2. [各命令類別的測試重點](./ipmi-validation-2-commands.md)
> 3. [OEM 命令、韌體更新與命令速查](./ipmi-validation-3-firmware-cheatsheet.md)

> 本系列依據公開的 IPMI v2.0 rev 1.1、DCMI v1.5 與 HPM.1 規格整理，搭配開源工具 `ipmitool`。內容是通用的測試思路，不針對任何特定廠商或平台；不同 BMC 韌體的實作可能不同，回傳值請以手上平台的規格為準。

---

## 1. App（NetFn 0x06）

### 1.1 Device 基本資訊

| 命令 | Cmd | ipmitool | 驗證重點 |
|---|---|---|---|
| Get Device ID | `0x01` | `mc info` | Firmware Revision、IPMI Version（`02` 代表 2.0）、Manufacturer ID（3 bytes，LS byte 在前）、Product ID |
| Cold Reset | `0x02` | `mc reset cold` | BMC 重啟後可重新連線；volatile 設定應回到預設值 |
| Warm Reset | `0x03` | `mc reset warm` | 部分平台不支援，可能回 `C1` |
| Get Self Test Results | `0x04` | `mc selftest` | `55h` = 無錯誤、`56h` = 未實作、`57h` = 有元件或資料損毀（第 2 byte 指出哪一項）、`58h` = 致命硬體錯誤 |
| Get/Set ACPI Power State | `0x07` / `0x06` | — | 讀回值應與系統目前狀態（S0/S5…）一致 |
| Get Device GUID | `0x08` | `mc guid` | 16 bytes，每次讀取結果應相同 |
| Get System GUID | `0x37` | — | 應與 SMBIOS Type 1 的 UUID 一致（注意 byte order） |

```bash
ipmitool raw 0x06 0x01          # Get Device ID
ipmitool raw 0x06 0x04          # Get Self Test Results → 預期 "55 00"
ipmitool raw 0x06 0x08          # Get Device GUID
```

### 1.2 Watchdog Timer

| 命令 | Cmd | 說明 |
|---|---|---|
| Reset Watchdog Timer | `0x22` | **啟動**或重新倒數 |
| Set Watchdog Timer | `0x24` | 只設定參數，不會啟動計時 |
| Get Watchdog Timer | `0x25` | 讀回設定和目前剩餘的倒數值 |

Set Watchdog Timer 的 request data：

| Byte | 內容 |
|---|---|
| 1 | Timer Use：bit[2:0] = 1 BIOS FRB2、2 BIOS/POST、3 OS Load、4 SMS/OS、5 OEM；bit6 = don't stop；bit7 = don't log |
| 2 | Timer Actions：bit[2:0] = 0 無動作、1 Hard Reset、2 Power Down、3 Power Cycle；bit[6:4] = pre-timeout interrupt |
| 3 | Pre-timeout interval（秒） |
| 4 | Timer Use Expiration Flags Clear（寫 1 清除對應 bit） |
| 5–6 | Initial countdown，單位 100 ms，LS byte 在前 |

```bash
# SMS/OS、逾時後 Hard Reset、倒數 10 秒（100 × 100ms = 0x0064）
ipmitool raw 0x06 0x24 0x04 0x01 0x00 0x10 0x64 0x00
ipmitool raw 0x06 0x25          # 讀回設定
ipmitool raw 0x06 0x22          # 開始倒數
ipmitool mc watchdog get        # string 版
ipmitool mc watchdog off        # 測完記得關閉
```

測試重點：
- Hard Reset、Power Down、Power Cycle 三種 action 都實際觸發一次，確認系統行為正確。
- SEL 中應出現 Watchdog 2 sensor 的 event；若設了 don't log bit，則不應有紀錄。
- `Get System Restart Cause`（Chassis `0x07`）應回報 watchdog expiration（`04h`）。
- 倒數期間持續送 Reset Watchdog，系統不應被重置。

### 1.3 BMC Global Enables 與 Message Flags

| 命令 | Cmd | ipmitool |
|---|---|---|
| Set/Get BMC Global Enables | `0x2E` / `0x2F` | `mc setenables` / `mc getenables` |
| Clear/Get Message Flags | `0x30` / `0x31` | — |

測試重點：逐一開關 System Event Logging、Event Message Buffer、Receive Message Queue 等 bit，讀回確認。關閉 SEL logging 時觸發 event，應**不會**寫入 SEL。

### 1.4 Session、Channel 與 Cipher Suite

| 命令 | Cmd | ipmitool |
|---|---|---|
| Get Channel Authentication Capabilities | `0x38` | — |
| Set/Get Channel Access | `0x40` / `0x41` | `channel setaccess` / `channel getaccess` |
| Get Channel Info | `0x42` | `channel info <ch>` |
| Get Channel Cipher Suites | `0x54` | `channel getciphers ipmi <ch>` |
| Get Session Info | `0x3D` | `session info all` |
| Close Session | `0x3C` | — |

Channel 編號慣例：`0x0E` = 目前使用的 channel、`0x0F` = system interface；LAN 通常是 1，但依平台而定。

測試重點：
- 用 `-C 3`、`-C 17` 等不同 cipher suite 連線，結果應符合平台支援的清單。
- **安全性檢查**：Cipher Suite 0（不認證）應停用；IPMI 1.5 的 `-I lan` 若非必要也應停用。
- 確認 session 數量上限，超過時新連線應被拒絕。

### 1.5 User 管理

| 命令 | Cmd | ipmitool |
|---|---|---|
| Set/Get User Access | `0x43` / `0x44` | `user priv <id> <level> <ch>` |
| Set/Get User Name | `0x45` / `0x46` | `user set name <id> <name>` |
| Set User Password | `0x47` | `user set password <id>` / `user test <id> 16\|20` |

Privilege level：1 = Callback、2 = User、3 = Operator、4 = Administrator、5 = OEM。

```bash
ipmitool user list 1
ipmitool user set name 3 testuser
ipmitool user set password 3          # 互動輸入
ipmitool user priv 3 2 1              # ID 3 在 channel 1 設為 User 權限
ipmitool user enable 3
```

測試重點：
- 低權限帳號執行管理命令（例如 `chassis power off`）應回 `D4`。
- 16 bytes 與 20 bytes 密碼都要測。
- 停用帳號後應無法登入。
- 測完要刪除或停用測試帳號。

### 1.6 System Info Parameters 與 System Interface Capabilities

- Set/Get System Info Parameters（`0x58` / `0x59`）：System Firmware Version、System Name、OS Name 等。可以拿 BIOS 實際版本來對照。
- Get System Interface Capabilities（`0x57`）：查詢 SSIF / KCS 支援的能力。

---

## 2. Chassis（NetFn 0x00）

| 命令 | Cmd | ipmitool | 說明 |
|---|---|---|---|
| Get Chassis Capabilities | `0x00` | — | 各 FRU/SDR/SEL device 的位址 |
| Get Chassis Status | `0x01` | `chassis status` | byte1 bit0 = power on；bit[6:5] = power restore policy |
| Chassis Control | `0x02` | `chassis power on/off/cycle/reset/soft` | data：0 Power Down、1 Power Up、2 Power Cycle、3 Hard Reset、4 Diagnostic Interrupt、5 ACPI Soft Shutdown |
| Chassis Identify | `0x04` | `chassis identify [sec\|force]` | byte1 = 亮燈秒數；byte2 bit0 = 恆亮 |
| Set Power Restore Policy | `0x06` | `chassis policy always-on\|previous\|always-off` | 0 Always Off、1 Previous、2 Always On、3 只查詢 |
| Get System Restart Cause | `0x07` | `chassis restart_cause` | 例如 1 = Chassis Control、2 = Reset 按鈕、3 = Power 按鈕、4 = Watchdog、6/7 = AC 恢復 |
| Set/Get System Boot Options | `0x08` / `0x09` | `chassis bootdev pxe\|disk\|bios [options=efiboot]` | Parameter 5 = Boot Flags |
| Set Front Panel Enables | `0x0A` | — | 停用 Power、Reset 按鈕 |
| Set Power Cycle Interval | `0x0B` | — | Power Cycle 時斷電持續的秒數 |
| Get POH Counter | `0x0F` | `chassis poh` | byte1 = 每個 count 代表的分鐘數，後 4 bytes 為累計值 |

```bash
ipmitool raw 0x00 0x01                # Get Chassis Status
ipmitool raw 0x00 0x02 0x02           # Power Cycle
ipmitool raw 0x00 0x04 0x0f           # Identify 亮燈 15 秒
ipmitool raw 0x00 0x06 0x03           # 只查詢目前的 restore policy
```

測試重點：
- 每個電源動作都要對照實機狀態：電源 LED、風扇、螢幕輸出、`chassis status` 的讀值。
- **Power Restore Policy** 三種設定都要實際拔插 AC 驗證。斷電後要等到電源完全放電再插回。
- **Restart Cause** 要跟觸發方式對得上（命令、按鈕、Watchdog、AC 恢復）。
- **Boot Options** 設定一次性開機裝置後重開，確認真的從該裝置開機，而且下一次開機會回到原本的順序（除非設定為 persistent）。
- 停用前面板按鈕後，實際按按鈕應沒有反應；測完要恢復。

---

## 3. Sensor / Event（NetFn 0x04）

### 3.1 Event

| 命令 | Cmd | ipmitool |
|---|---|---|
| Set/Get Event Receiver | `0x00` / `0x01` | — |
| Platform Event Message | `0x02` | `event <1\|2\|3>` 會送出預設的測試 event |

```bash
ipmitool raw 0x04 0x01                # Get Event Receiver → 通常為 "20 00"（BMC 位址 0x20、LUN 0）
ipmitool event 1                      # 送一筆測試 event
ipmitool sel elist last 3             # 確認 SEL 多了一筆
```

### 3.2 Sensor

| 命令 | Cmd | ipmitool |
|---|---|---|
| Get Sensor Reading | `0x2D` | `sensor reading "<name>"` |
| Set/Get Sensor Threshold | `0x26` / `0x27` | `sensor thresh "<name>" unc <val>` / `sensor get "<name>"` |
| Set/Get Sensor Hysteresis | `0x24` / `0x25` | — |
| Set/Get Sensor Event Enable | `0x28` / `0x29` | — |
| Re-arm Sensor Events | `0x2A` | — |
| Get Sensor Event Status | `0x2B` | — |
| Get Sensor Reading Factors | `0x23` | 非線性 sensor 才需要 |
| Set/Get Sensor Type | `0x2E` / `0x2F` | — |

Set Sensor Threshold 的 mask byte：bit0 LNC、bit1 LC、bit2 LNR、bit3 UNC、bit4 UC、bit5 UNR。後面依序接 6 個 raw 值。raw 值需要用 SDR 中的 M、B、R exp 換算成實際單位。

測試流程範例（溫度 sensor）：
1. `sensor get` 記下原本的 threshold。
2. 把 UNC 設到比目前讀值還低，人為觸發 Upper Non-Critical event。
3. 確認 SEL 出現 assertion event、`Get Sensor Event Status` 對應 bit 被設起、Web UI 和 LED 狀態（若有）有變化。
4. 把 threshold 改回來，確認出現 deassertion event。
5. 用 `mc reset cold` 或手動寫回，恢復原始設定並再次確認。

### 3.3 PEF 與 Alerting

| 命令 | Cmd | ipmitool |
|---|---|---|
| Get PEF Capabilities | `0x10` | `pef info` |
| Arm PEF Postpone Timer | `0x11` | — |
| Set/Get PEF Configuration Parameters | `0x12` / `0x13` | `pef list` |
| Set/Get Last Processed Event ID | `0x14` / `0x15` | `pef status` |
| Alert Immediate | `0x16` | — |

測試重點：
- 設定 LAN Alert Destination（LAN Config Parameter 18、19）指向測試機。觸發 event 或送 Alert Immediate 後，用 `tcpdump -i <if> udp port 162` 或 Wireshark 確認收到 SNMP Trap（PET）。
- PEF action（power off、reset、alert）要實際觸發一次確認行為。
- Postpone timer 倒數期間，PEF 不應執行 action。

---

## 4. Storage（NetFn 0x0A）

### 4.1 FRU

| 命令 | Cmd | ipmitool |
|---|---|---|
| Get FRU Inventory Area Info | `0x10` | — |
| Read FRU Data | `0x11` | `fru print <id>` / `fru read <id> <file>` |
| Write FRU Data | `0x12` | `fru write <id> <file>` / `fru edit` |

```bash
ipmitool raw 0x0a 0x10 0x00           # FRU 0 大小（LS byte 在前）與存取單位
ipmitool fru read 0 fru0_backup.bin   # ⚠️ 寫入前一定要先備份
```

測試重點：
- 寫入測試資料後讀回比對，最後**一定要寫回原始檔**，避免序號、MAC 等資料遺失。
- 寫入超出 area size 的資料，應回錯誤。
- 修改後 `fru print` 解析出的欄位應正確，checksum 也要正確。

### 4.2 SDR Repository

| 命令 | Cmd | ipmitool |
|---|---|---|
| Get SDR Repository Info | `0x20` | `sdr info` |
| Get SDR Repository Allocation Info | `0x21` | — |
| Reserve SDR Repository | `0x22` | — |
| Get SDR | `0x23` | `sdr list` / `sdr elist` / `sdr type <type>` |
| Add / Partial Add / Delete SDR | `0x24` / `0x25` / `0x26` | — |
| Clear SDR Repository | `0x27` | ⚠️ 會清掉所有 sensor 定義 |
| Get/Set SDR Repository Time | `0x28` / `0x29` | — |
| Run Initialization Agent | `0x2C` | — |

測試重點：
- `sdr info` 的 record 數量應與 `sdr elist` 列出的筆數一致。
- 對 Add 或 Clear 這類破壞性操作，先 `sdr dump <file>` 備份；也要確認平台有辦法還原（例如重刷韌體）。
- Run Initialization Agent 後，sensor threshold 應回到 SDR 中定義的預設值。

### 4.3 SEL（System Event Log）

| 命令 | Cmd | ipmitool |
|---|---|---|
| Get SEL Info | `0x40` | `sel info` |
| Get SEL Allocation Info | `0x41` | — |
| Reserve SEL | `0x42` | — |
| Get SEL Entry | `0x43` | `sel list` / `sel elist` / `sel get <id>` |
| Add SEL Entry | `0x44` | `sel add <file>` |
| Delete SEL Entry | `0x46` | `sel delete <id>` |
| Clear SEL | `0x47` | `sel clear` |
| Get/Set SEL Time | `0x48` / `0x49` | `sel time get` / `sel time set "<MM/DD/YYYY HH:MM:SS>"` |
| Get/Set SEL Time UTC Offset | `0x5C` / `0x5D` | — |

```bash
ipmitool raw 0x0a 0x42                        # Reserve SEL → 取得 Reservation ID，例如 "01 00"
ipmitool raw 0x0a 0x47 0x01 0x00 0x43 0x4c 0x52 0xaa   # Clear SEL（"CLR" + 0xAA 開始清除）
ipmitool raw 0x0a 0x47 0x01 0x00 0x43 0x4c 0x52 0x00   # 查詢清除進度（回 01 = 完成）
```

測試重點：
- `sel info` 的 Entries、Free Space、Last Add Time 要隨著新增、刪除、清除正確變化；Free Space 每筆通常是 16 bytes。
- Clear 之後通常會留下一筆「Log area reset/cleared」event。
- Reservation ID 被其他 reserve 取代後，用舊 ID 操作應回 `C5`。
- SEL 寫滿時，行為應符合平台設計（停止記錄或 overwrite），並應有對應的 event。
- SEL Time 要跟 BMC 時間、BIOS 時間一致；UTC Offset 設定後，顯示的時間要正確。

---

## 5. Transport（NetFn 0x0C）

### 5.1 LAN

| 命令 | Cmd | ipmitool |
|---|---|---|
| Set/Get LAN Configuration Parameters | `0x01` / `0x02` | `lan set <ch> ...` / `lan print <ch>` |
| Suspend BMC ARPs | `0x03` | — |
| Get IP/UDP/RMCP Statistics | `0x04` | `lan stats get <ch>` |

常用 parameter：3 = IP Address、4 = IP Source（1 static、2 DHCP）、5 = MAC Address、6 = Subnet Mask、12 = Default Gateway、18/19 = Alert Destination。

```bash
ipmitool raw 0x0c 0x02 0x01 0x03 0x00 0x00   # 讀 channel 1 的 IP；第一個 byte 為 parameter revision（通常為 11）
ipmitool lan print 1
ipmitool lan set 1 ipsrc static
ipmitool lan set 1 ipaddr <IP>
```

測試重點：
- 用 raw 讀出的各參數，要和 `lan print` 的結果一致。
- Static 與 DHCP 互相切換後，網路要能恢復連線。建議從 in-band 操作，避免把自己斷線。
- 如果平台有 dedicated NIC 與 shared NIC，兩條路徑都要測。
- Gratuitous ARP 的設定可以用封包擷取工具確認。

### 5.2 SOL（Serial over LAN）

| 命令 | Cmd | ipmitool |
|---|---|---|
| Set/Get SOL Configuration Parameters | `0x21` / `0x22` | `sol set <param> <val> <ch>` / `sol info <ch>` |
| Activate / Deactivate Payload | App `0x48` / `0x49` | `sol activate` / `sol deactivate` |

常用 parameter：1 = SOL Enable、5 = Non-volatile Bit Rate、6 = Volatile Bit Rate（6 = 9600、7 = 19200、8 = 38400、9 = 57600、`0x0A` = 115200）。

```bash
ipmitool sol info 1
ipmitool sol set volatile-bit-rate 115.2 1
ipmitool sol activate                 # 離開：輸入 ~.
```

測試重點：
- 每一種 baud rate 都要和 BIOS/OS 的 console 設定搭配，確認畫面正常、沒有亂碼。
- SOL 停用時 activate 應失敗；已有 session 時，再開第二個應被拒絕或踢掉前一個（依平台設計）。
- 重開機過程中，SOL 畫面應能看到 POST 與開機訊息。

---

## 6. DCMI（NetFn 0x2C，Group ID 0xDC）

| 命令 | Cmd | ipmitool |
|---|---|---|
| Get DCMI Capabilities Info | `0x01` | `dcmi discover` |
| Get Power Reading | `0x02` | `dcmi power reading` |
| Get/Set/Activate Power Limit | `0x03` / `0x04` / `0x05` | `dcmi power get_limit` / `set_limit` / `activate` |
| Get / Set Asset Tag | `0x06` / `0x08` | `dcmi asset_tag` / `dcmi set_asset_tag <str>` |
| Get DCMI Sensor Info | `0x07` | `dcmi sensors` |
| Get / Set Management Controller ID String | `0x09` / `0x0A` | `dcmi get_mc_id_string` / `dcmi set_mc_id_string <str>` |
| Get Temperature Readings | `0x10` | `dcmi get_temp_reading` |

測試重點：
- 支援的功能要和 `dcmi discover` 宣告的一致。
- 寫入 Asset Tag 和 MC ID 後讀回，再測超長字串的處理，最後恢復原值。
- 溫度讀值在開機和關機狀態下都要合理，並和 `sdr` 的讀值互相對照。

---

下一篇：[OEM 命令、韌體更新與命令速查](./ipmi-validation-3-firmware-cheatsheet.md)。

## 參考資料

- *Intelligent Platform Management Interface Specification v2.0 rev 1.1*
- *Data Center Manageability Interface (DCMI) Specification v1.5*
- *PICMG HPM.1 Firmware Upgrade Specification*
- `man ipmitool`
