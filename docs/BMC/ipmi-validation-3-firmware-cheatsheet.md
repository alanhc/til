---
title: "BMC IPMI 驗證實戰（三）：OEM 命令、韌體更新與命令速查"
sidebar_label: "IPMI 驗證（三）韌體與速查"
tags: [bmc, ipmi, ipmitool, validation]
---

# BMC IPMI 驗證實戰（三）：OEM 命令、韌體更新與命令速查

> TL;DR：OEM 命令一律以廠商規格為準，不要跨平台套用；韌體更新要用「方向 × 路徑 × 主機狀態 × 對象 × 異常」的矩陣來測，燒完檢查版本、SEL、LED 和設定是否保留。最後附上整個系列的命令速查與結語。

> **BMC IPMI 驗證實戰系列**
> 1. [基礎觀念與通用測試方法](./ipmi-validation-1-basics.md)
> 2. [各命令類別的測試重點](./ipmi-validation-2-commands.md)
> 3. [OEM 命令、韌體更新與命令速查](./ipmi-validation-3-firmware-cheatsheet.md)

> 本系列依據公開的 IPMI v2.0 rev 1.1、DCMI v1.5 與 HPM.1 規格整理，搭配開源工具 `ipmitool`。內容是通用的測試思路，不針對任何特定廠商或平台；不同 BMC 韌體的實作可能不同，回傳值請以手上平台的規格為準。

---

## 1. OEM 命令

NetFn `0x2E`/`0x2F` 的 request 前 3 bytes 是廠商的 IANA Enterprise Number（LS byte 在前），response 成功時也會帶回同樣 3 bytes。NetFn `0x30`–`0x3F` 則完全由廠商定義。

測試原則：
- 以廠商的 BMC 規格為準，每個命令都要確認參數格式和適用的平台。
- 不同專案或平台的 OEM 命令格式可能不同，不要直接套用其他平台的命令。
- 硬體層級的命令（暫存器、I2C、GPIO 讀寫）可能影響系統穩定，先在不重要的位址上驗證，並準備好還原的方法。

---

## 2. 韌體更新

常見的方式：
- **HPM.1**：`ipmitool hpm upgrade <file>.hpm`，也可以用 `hpm check` 先檢查 image。
- 廠商提供的燒錄工具，通常同時支援 in-band（KCS）與 out-of-band（LAN）。
- Redfish `UpdateService` 或 Web UI。

測試矩陣建議：

| 面向 | 項目 |
|---|---|
| 方向 | 升版（N-1 → N）、降版（N → N-1）、同版重燒 |
| 路徑 | In-band（主機 OS）、Out-of-band（遠端網路） |
| 主機狀態 | OS 運作中、主機關機（只有 BMC 有電） |
| 對象 | BMC、BIOS（若支援由 BMC 燒錄）、其他 FW（CPLD 等） |
| 異常 | 錯誤或損毀的 image、中途網路中斷、中途斷電（需確認平台有 recovery 機制） |

燒錄後檢查：
- `mc info` 的 Firmware Revision 和預期版本一致。
- SEL 有韌體更新相關的 event，而且沒有異常 event。
- 系統狀態 LED 正常，sensor 讀值正常。
- 設定（網路、使用者、SEL）是保留還是重置，要符合 release note 的說明。

---

## 3. 常用命令速查

```bash
# 資訊
ipmitool mc info                      # BMC 版本與廠商資訊
ipmitool mc selftest                  # 自我檢測
ipmitool fru print                    # FRU 資料
ipmitool sdr elist                    # 所有 sensor 與讀值
ipmitool sensor list                  # sensor 與 threshold
ipmitool sel elist                    # 事件紀錄
ipmitool lan print 1                  # 網路設定
ipmitool user list 1                  # 使用者
ipmitool channel getciphers ipmi 1    # 支援的 cipher suite

# 控制
ipmitool chassis status
ipmitool chassis power on|off|cycle|reset|soft
ipmitool chassis identify 15
ipmitool chassis policy previous
ipmitool chassis bootdev pxe options=efiboot
ipmitool mc reset cold

# Debug
ipmitool -v raw 0x06 0x01             # -v 顯示更多細節
ipmitool -vvv -I lanplus -H <IP> -U <USER> -E mc info   # 看 RMCP+ 交握過程
```

---

## 結語

把上面的內容濃縮成一句話：**每個測項都要問「怎麼證明它真的生效了」。**

- 設定類命令：讀回來一樣還不夠，要確認 reset、AC cycle 之後的狀態符合規格。
- 控制類命令：回 `00` 還不夠，要看到機器真的關了、真的重開了，而且 Restart Cause 和 SEL 都對得上。
- 權限與介面：不只測「能做」，也要測「不該做的做不了」。
- 測完還原：Watchdog 關掉、threshold 改回、FRU 寫回、測試帳號刪掉。這些不做好，下一個測項的結果就不可信。

IPMI 規格本身不難讀，難的是每家 BMC 的實作都有自己的解讀和 OEM 擴充。建議手邊一定要有 IPMI 2.0 規格書，遇到不確定的回傳值時，逐 byte 對照欄位定義，比任何人的經驗都可靠。

## 參考資料

- *Intelligent Platform Management Interface Specification v2.0 rev 1.1*
- *Data Center Manageability Interface (DCMI) Specification v1.5*
- *PICMG HPM.1 Firmware Upgrade Specification*
- `man ipmitool`
