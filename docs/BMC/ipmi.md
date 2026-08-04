# IPMI

**IPMI**（Intelligent Platform Management Interface）是伺服器的**頻外管理**（out-of-band management）標準介面，由 Intel 等廠商在 1998 年提出，目前廣泛使用的是 IPMI v2.0。

它的核心價值是：**即使主機的 OS 當掉、甚至主機根本沒開機，只要 BMC 有待機電源，管理者仍可透過網路遠端開關機、讀感測器、看 log**。這條管理路徑完全獨立於主機 CPU 與 OS。

## 架構

- **BMC**（Baseboard Management Controller）：板上的獨立管理晶片，是 IPMI 的執行者。
- **傳輸介面**：
  - **KCS**（Keyboard Controller Style）：主機 OS 透過 LPC/eSPI 對本機 BMC 下指令（in-band）。
  - **IPMI over LAN / RMCP+**：遠端透過網路下指令（out-of-band），走 UDP port 623，見 [SOL](./sol.md)。
  - **IPMB**：BMC 與板上其他管理裝置之間的 I2C 匯流排。
- **常用工具**：`ipmitool`（Linux 上最通用的 client）。

```bash
# 遠端讀取電源狀態
ipmitool -I lanplus -H <bmc-ip> -U <user> -P <pass> chassis power status

# 本機（主機 OS 內）透過 KCS 下指令
ipmitool -I open sensor list
```

## SEL（System Event Log）

**SEL** 是 BMC 內部的**系統事件日誌**，記錄硬體層級的重要事件：溫度超過門檻、電壓異常、風扇故障、電源開關機、ECC 記憶體錯誤等。

特性：
- 存在 BMC 的非揮發記憶體裡，**主機斷電也不會消失**，是事後追查當機原因的第一手資料。
- 每筆記錄含時間戳記、產生事件的 sensor、事件類型與 assert/deassert 狀態。
- 空間有限（常見數百到數千筆），滿了之後可能停止記錄或覆蓋舊資料，所以維運上要定期收走並清空。

```bash
ipmitool sel info      # 看容量、已用筆數、最後新增時間
ipmitool sel list      # 列出所有事件
ipmitool sel elist     # 列出並展開 SDR 資訊（比較好讀）
ipmitool sel clear     # 清空（清掉就沒了，先備份）
```

## SDR（Sensor Data Record）

**SDR** 是**感測器的描述資料**，不是感測器的讀值。它是一份存在 BMC 裡的清單，告訴管理端「這台機器上有哪些 sensor、各自的編號、名稱、單位、換算公式、警戒門檻是多少」。

為什麼需要它：BMC 從硬體讀到的是原始值（raw byte），必須靠 SDR 裡的換算係數才能轉成人看得懂的 °C / V / RPM，也必須靠 SDR 才知道這個值算不算異常。

- **SDR Repository**：所有 SDR 的集合，通常由板廠在產線燒錄，或由 BMC 韌體依機種產生。
- 一筆 SDR 包含：sensor number、sensor type（溫度/電壓/風扇…）、entity（屬於哪個實體元件）、單位、線性化公式、以及 upper/lower 的 non-critical / critical / non-recoverable 門檻。

```bash
ipmitool sdr list          # 列出所有 sensor 與當前讀值
ipmitool sdr type Temperature
ipmitool sensor list       # 更詳細，含各級門檻
```

## FRU（Field Replaceable Unit）

**FRU** 指「現場可更換單元」——主機板、電源供應器、風扇模組、背板這類可以單獨換掉的零件。在 IPMI 裡，FRU 通常指這些零件上 **EEPROM 內存放的身分資料**。

典型欄位（依 IPMI FRU Information Storage Definition 規範分成幾個 area）：
- **Chassis Info Area**：機箱型號、序號
- **Board Info Area**：製造商、板子名稱、序號、料號、製造日期
- **Product Info Area**：產品名稱、版本、序號、資產標籤

用途是資產盤點與 RMA 追蹤——遠端就能知道機櫃裡每台機器裝了什麼零件、序號多少，不必開機殼看貼紙。

```bash
ipmitool fru print         # 印出所有 FRU
ipmitool fru print 0       # 只印 FRU device 0
```

FRU EEPROM 實體上通常掛在 I2C bus 上，所以也可以用 `i2cdump` 直接讀，見 [hardware](./hardware.md)。

## IPMI raw command

當 `ipmitool` 沒有對應的子命令（例如廠商自訂的 **OEM command**），就用 **raw command** 直接送出原始的 IPMI 訊息位元組。

格式：

```
ipmitool raw <netfn> <cmd> [data bytes...]
```

- **NetFn**（Network Function）：功能分類碼。常見的有 `0x00` Chassis、`0x04` Sensor/Event、`0x06` App、`0x0a` Storage、`0x2c` DCMI、`0x2e`/`0x30` 起為 OEM 自訂區。
- **Cmd**：該分類下的指令碼。
- **data**：指令參數，逐 byte 給。
- 回傳也是一串 byte，要對照規格書（或廠商文件）自己解讀。

```bash
# NetFn 0x06 (App) / Cmd 0x01 = Get Device ID
ipmitool raw 0x06 0x01

# NetFn 0x00 (Chassis) / Cmd 0x02 = Chassis Control，0x01 = power up
ipmitool raw 0x00 0x02 0x01
```

raw command 是開發與除錯階段的主力：新功能還沒被 `ipmitool` 支援、或要驗證 BMC 韌體是否正確實作某個 command 時，都靠它。**風險是沒有任何保護**，打錯 NetFn/Cmd 可能觸發非預期行為，正式環境要謹慎。

## 與 Redfish 的關係

IPMI 是舊世代標準，安全性（明文、弱驗證）與擴充性都有侷限，DMTF 已推出 **Redfish**（基於 HTTPS + JSON 的 RESTful API）作為後繼者。目前實務上兩者並存：新平台以 Redfish 為主，但 IPMI 因為工具鏈成熟、腳本量大，仍被大量保留。OpenBMC 兩者都支援，見 [openbmc](./openbmc.md)。

## 參考

- [IPMI Specification v2.0（Intel）](https://www.intel.com/content/www/us/en/products/docs/servers/ipmi/ipmi-second-gen-interface-spec-v2-rev1-1.html)
- [ipmitool 官方專案](https://github.com/ipmitool/ipmitool)
