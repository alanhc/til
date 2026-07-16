---
title: BMC 名詞表
sidebar_label: BMC 名詞表
sidebar_position: 4
---

# BMC 名詞表

彙整知識庫中所有 BMC / OpenBMC 筆記出現過的名詞。BMC 文章都集中在 `BMC/` 資料夾，文章清單直接走側邊欄即可（這類不另做索引），本表用於**從名詞反查回原始筆記**。

---

## 一、OpenBMC 架構與建置

### 專案與發行版

| 名詞 | 說明 | 出處 |
|---|---|---|
| **BMC (Baseboard Management Controller)** | 主機板上獨立於 Host CPU 的管理控制器。通常是一顆 ARM SoC 跑嵌入式 Linux，即使 Host 關機仍持續運作 | [bootup](../BMC/bootup.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **OpenBMC** | Linux Foundation 主導的開源 BMC 韌體專案，廣泛用於 ASPEED AST2500/AST2600、Nuvoton NPCM 等管理晶片 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[openbmc](../BMC/openbmc.md) |
| **Canopy (Canopy OpenBMC)** | 建立在 OpenBMC upstream 之上的**企業級發行版**，由 BlindSpot Software GmbH 維護。類比關係：Linux Kernel → Ubuntu，OpenBMC → Canopy | [openbmc_canopybmc](../openbmc_canopybmc.md) |
| **upstream-first** | Canopy 的核心策略：每週 rebase OpenBMC 最新版本，而非長年維護分叉。好處是不脫節、bug 可回饋社群 | [openbmc_canopybmc](../openbmc_canopybmc.md) |
| **Hardware CI** | 每個 commit 都真的 build firmware、flash 到實體機（如 Coffee Lake + AST2600）開機並測 IPMI / Redfish / Sensor / GPIO，而不只跑 bitbake 與 unit test | [openbmc_canopybmc](../openbmc_canopybmc.md) |
| **LTS (Long Term Support)** | Canopy 的長期維護版本（如 2026.06、2028.06），提供 security patch 與 bug fix，不像 upstream 只是不斷往前 | [openbmc_canopybmc](../openbmc_canopybmc.md) |

### D-Bus

| 名詞 | 說明 | 出處 |
|---|---|---|
| **D-Bus** | OpenBMC 的**服務溝通核心**。所有服務（bmcweb、ipmid、entity-manager、sensor、logging）都掛在同一條 message bus 上互相取用資料 | [dbus](../BMC/dbus.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **dbus-broker / dbus-daemon** | 實際承載 message bus 的程式 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **object / interface / property / signal** | D-Bus 的四個基本概念：物件路徑、介面、屬性、訊號 | [dbus](../BMC/dbus.md) |
| **`busctl`** | 查詢／操作 D-Bus 的命令列工具 | [dbus](../BMC/dbus.md) |
| **`busctl tree`** | 列出某個 service 底下的物件樹（如 `busctl tree xyz.openbmc_project.HwmonTempSensor`） | [dbus](../BMC/dbus.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **`busctl introspect`** | 檢視某物件提供哪些 interface / property / method | [dbus](../BMC/dbus.md) |
| **`busctl call` / `busctl get-property`** | 呼叫 method／讀取屬性值 | [dbus](../BMC/dbus.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **phosphor-dbus-interfaces** | OpenBMC 標準 D-Bus 介面定義的集中處 | [openbmc](../BMC/openbmc.md)、[ai_bmc](../ai_bmc.md) |
| **`xyz.openbmc_project.*`** | OpenBMC D-Bus 命名空間。**大小寫敏感**，AI 產生的 code 常拼錯 | [ai_bmc](../ai_bmc.md) |

### 服務

| 名詞 | 說明 | 出處 |
|---|---|---|
| **bmcweb** | 實作 Redfish server 與 Web UI 的服務，把 D-Bus 上的資料對映成 Redfish 資源（HTTP/HTTPS） | [redfish](../BMC/redfish.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **entity-manager** | 「描述硬體並動態探測」的服務。用 JSON 描述一塊板子有哪些 sensor/fan/FRU/電源，開機時依偵測結果決定啟用哪些設定 | [entity_manager](../BMC/entity_manager.md) |
| **`Exposes`** | Entity Manager JSON 中描述「該板提供哪些 sensor/裝置」的欄位 | [entity_manager](../BMC/entity_manager.md) |
| **`Probe`** | Entity Manager 的探測條件，常用 FRU EEPROM 內容（如 `PRODUCT_PRODUCT_NAME`）比對，命中才套用該設定 | [entity_manager](../BMC/entity_manager.md) |
| **`xyz.openbmc_project.Configuration.*`** | 探測成功後 Entity Manager 放上 D-Bus 的設定物件，供 dbus-sensors、phosphor-pid-control 等訂閱 | [entity_manager](../BMC/entity_manager.md) |
| **dbus-sensors** | 訂閱 Entity Manager 設定、動態建立 sensor 的服務群 | [entity_manager](../BMC/entity_manager.md)、[sensor_porting](../BMC/sensor_porting.md) |
| **Entity Manager 的價值** | 同一份 image 支援多種板型；新增硬體多半只要加 JSON，不必改 C++ | [entity_manager](../BMC/entity_manager.md) |

### Yocto 建置

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Yocto Project** | OpenBMC 用來產生 BMC firmware image 的嵌入式 Linux build 框架。**不是發行版，而是「幫你組出自己發行版」的工具鏈** | [yocto](../BMC/yocto.md) |
| **bitbake** | build 引擎，解析 recipe、處理相依、跑各 task（fetch / compile / install / package） | [yocto](../BMC/yocto.md) |
| **recipe (`.bb`)** | 描述單一軟體怎麼抓原始碼、編譯、安裝 | [yocto](../BMC/yocto.md)、[openbmc](../BMC/openbmc.md) |
| **`.bbappend`** | 覆寫／擴充既有 recipe（常搭配 `FILESEXTRAPATHS:prepend` 與 `SRC_URI += "file://xxx.patch"` 打 patch） | [yocto](../BMC/yocto.md)、[ai_bmc](../ai_bmc.md) |
| **layer (`meta-*`)** | 一組 recipe 與設定的集合，可疊加。OpenBMC 有 `meta-phosphor`、各廠 `meta-<vendor>` / `meta-<board>` | [yocto](../BMC/yocto.md)、[openbmc](../BMC/openbmc.md) |
| **image recipe** | 定義最終要放進 rootfs 的套件集合 | [yocto](../BMC/yocto.md) |
| **machine / distro conf** | 選硬體與發行版設定 | [yocto](../BMC/yocto.md) |
| **`bitbake obmc-phosphor-image`** | OpenBMC 標準 image 的建置指令（前置 `. setup <machine>`）。產物在 `tmp/deploy/images/<machine>/` | [yocto](../BMC/yocto.md) |
| **Buildroot** | 另一套嵌入式建置系統，同樣往下產出 kernel / u-boot / driver / device tree。改 driver 通常只會動到 **Driver** 與 **Device Tree** 兩塊 | `BMC/device_driver/_index.md`、[porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |

### Gerrit Workflow

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Gerrit** | OpenBMC 上游採用的 code review 系統。與 GitHub PR 不同：以「**每個 commit = 一個可審查的 change**」為單位 | [git](../BMC/git.md) |
| **`git review`** | 推送 change 到 Gerrit 的核心工具 | [git](../BMC/git.md) |
| **`Change-Id`** | commit message 尾端由 commit-msg hook 產生的識別碼，同一個 change 的多次修訂共用它 | [git](../BMC/git.md) |
| **修訂既有 change** | 改完後 `git commit --amend` 再 `git review`，會變成**同一 change 的新 patch set**，而不是新 change | [git](../BMC/git.md) |
| **`Code-Review +2` / `Verified +1`** | Gerrit 的 review 分數。`+2` 才可合併，`Verified +1` 多由 CI 給 | [git](../BMC/git.md) |
| **`Signed-off-by` (DCO)** | 每個 commit 都必須有，用 `git commit -s` 加上 | [git](../BMC/git.md) |

---

## 二、管理介面（IPMI / Redfish / SSE / SOL）

### IPMI

| 名詞 | 說明 | 出處 |
|---|---|---|
| **IPMI** | 傳統的伺服器管理協定，二進位格式、難擴充，正逐步被 Redfish 取代 | [ipmi](../BMC/ipmi.md)、[redfish](../BMC/redfish.md) |
| **ipmid** | OpenBMC 處理 IPMI 協定的服務（KCS / LAN channel） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **SDR (Sensor Data Record)** | IPMI 的感測器描述紀錄 | [ipmi](../BMC/ipmi.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **SEL (System Event Log)** | IPMI 的系統事件紀錄 | [ipmi](../BMC/ipmi.md)、[sel_logger](../BMC/sel_logger.md) |
| **FRU (Field Replaceable Unit)** | 可現場更換的單元（主機板、電源、風扇背板）。每片板子放一顆 EEPROM，以 **IPMI Platform Management FRU Information** 格式存製造商、產品名、序號、part number | [fru](../BMC/fru.md)、[ipmi](../BMC/ipmi.md) |
| **IPMI raw command** | 直接送原始 byte 的指令，如 `ipmitool raw 0x04 0x2d 0x01` | [ipmi](../BMC/ipmi.md)、[ai_bmc](../ai_bmc.md) |
| **KCS** | Keyboard Controller Style，Host 與 BMC 間的 IPMI 傳輸介面之一。`ipmid` 無回應時常見原因就是 KCS 驅動問題 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[mctp](../BMC/mctp.md) |
| **IPMI LAN channel** | 經網路下 IPMI 指令的通道，也可用來設定網路（相容舊工具） | [network](../BMC/network.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |

### Redfish

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Redfish** | DMTF 定義的 RESTful 管理介面標準，用 HTTPS + JSON 管理伺服器硬體，目標是取代 IPMI。資源導向、標準動詞 `GET/POST/PATCH/DELETE` | [redfish](../BMC/redfish.md) |
| **`/redfish/v1/`** | 根資源，透過 hyperlink 逐層瀏覽 | [redfish](../BMC/redfish.md) |
| **`/redfish/v1/Systems`** | 主機資源：電源狀態、開關機、boot override | [redfish](../BMC/redfish.md) |
| **`/redfish/v1/Chassis`** | 機殼、感測器、電源／散熱 | [redfish](../BMC/redfish.md) |
| **`/redfish/v1/Managers`** | BMC 本身。NTP 設定在 `Managers/bmc/NetworkProtocol` | [redfish](../BMC/redfish.md)、[ntp](../BMC/ntp.md) |
| **LogService / UpdateService / EventService / AccountService** | Redfish 常見的其他資源集合 | [redfish](../BMC/redfish.md) |
| **`ComputerSystem.Reset`** | Redfish 的開關機動作：`POST /redfish/v1/Systems/system/Actions/ComputerSystem.Reset` | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |

### EventService 與 SSE

| 名詞 | 說明 | 出處 |
|---|---|---|
| **EventService** | Redfish 的事件訂閱機制，讓管理端不必一直輪詢（polling），改由 BMC 主動推送。資源根 `/redfish/v1/EventService` | [event_service](../BMC/event_service.md) |
| **Subscription** | `POST` 到 `EventService/Subscriptions` 建立訂閱，帶 `Destination`（接收 URL）、`EventTypes` / `RegistryPrefixes` / `ResourceTypes` 過濾條件、`Protocol` | [event_service](../BMC/event_service.md) |
| **Push（webhook）** | 遞送方式之一：BMC 主動 POST 到訂閱時登記的目標 URL。**需要一個可被 BMC 連到的 URL** | [event_service](../BMC/event_service.md)、[sse](../BMC/sse.md) |
| **SSE (Server-Sent Events)** | 基於 HTTP 的**單向**串流（server → client）。client 開長連線，事件即時串流下來，**免預先註冊 webhook destination** | [sse](../BMC/sse.md)、[event_service](../BMC/event_service.md) |
| **`text/event-stream`** | SSE 的 MIME 型別。資料格式為 `data: ...` 後接空行，可帶 `event:`、`id:` | [sse](../BMC/sse.md) |
| **SSE vs WebSocket** | SSE 較簡單（免自訂協定、瀏覽器可自動重連），但只能單向 | [sse](../BMC/sse.md) |
| **Message Registry** | Redfish 事件訊息的定義來源，OpenBMC 事件多半由 phosphor-logging 的 log 對映而來 | [event_service](../BMC/event_service.md) |

### SOL（Serial over LAN）

| 名詞 | 說明 | 出處 |
|---|---|---|
| **SOL (Serial over LAN)** | 把 host 序列埠資料轉封包、經網路傳送、再還原成串列資料，讓管理者不必實體接 serial cable 就能看 BIOS/POST 與 console | [sol](../BMC/sol.md)、[serial_over_lan](../BMC/serial_over_lan.md) |
| **RMCP+** | Remote Management Control Protocol Plus。SOL 走 IPMI v2.0 的 RMCP+，相較舊版 RMCP 支援加密與更強的 session 驗證（RAKP 金鑰交換） | [sol](../BMC/sol.md)、[serial_over_lan](../BMC/serial_over_lan.md) |
| **UDP port 623** | IPMI over LAN / RMCP+ 使用的連接埠 | [sol](../BMC/sol.md)、[serial_over_lan](../BMC/serial_over_lan.md) |
| **SOL 封包內容** | `Payload Type = SerialOverLan`、`Sequence Number`、`Data`（真實串列字元）、`ACK/NACK` | [serial_over_lan](../BMC/serial_over_lan.md) |
| **`ipmitool sol activate` / `deactivate` / `info`** | 啟用／關閉／查詢 SOL session（需 `-I lanplus` 指定 IPMI v2.0 / RMCP+） | [sol](../BMC/sol.md)、[serial_over_lan](../BMC/serial_over_lan.md) |
| **`~.`** | 離開 SOL session 的預設跳脫序列 | [sol](../BMC/sol.md) |
| **obmc-console** | OpenBMC 的 SOL console 轉發服務 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **Console Redirection** | BIOS 設定，允許把畫面輸出轉導到串列埠 | [serial_over_lan](../BMC/serial_over_lan.md) |
| **Redfish ConsoleService** | 現代 BMC 用 Redfish（如 WebSocket 串流）取代 IPMI SOL 的作法 | [serial_over_lan](../BMC/serial_over_lan.md) |

---

## 三、硬體存取與匯流排

### I2C / SMBus

| 名詞 | 說明 | 出處 |
|---|---|---|
| **I2C** | BMC 存取板上晶片（sensor、EEPROM、CPLD、retimer）最主要的匯流排 | [hardware](../BMC/hardware.md) |
| **SMBus** | 基於 I2C 的系統管理匯流排協定 | [hardware](../BMC/hardware.md)、`BMC/device_driver/_index.md` |
| **`i2cdetect`** | 掃描 bus 上有哪些位址有裝置，也可用來查是否有 driver 佔用 | [hardware](../BMC/hardware.md)、[pmbus](../BMC/pmbus.md) |
| **`UU` vs 位址數字** | `i2cdetect` 輸出中：印出位址數字（如 `63`）代表 **no device driver**；印 `UU` 代表**目前有 driver 佔用** | `BMC/device_driver/_index.md` |
| **`i2cget` / `i2cset` / `i2ctransfer`** | 直接對 I2C 裝置讀寫。`-y` 不詢問直接執行、`-f` 強制存取（即使已被 driver 佔用） | [hardware](../BMC/hardware.md)、[fru](../BMC/fru.md) |
| **`i2cget -fy 7 0x63 0x8c w`** | 讀 bus 7、位址 0x63、command 0x8c 的 word——驗證 driver 讀值最快的方式 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **`13-0048`** | sysfs 上 I2C 裝置的命名：**bus 13 上位址 0x48 的裝置**，路徑 `/sys/bus/i2c/devices/13-0048` | [fru](../BMC/fru.md) |
| **`/sys/class/i2c-dev`** | I2C 在檔案系統上的介面路徑 | [hardware](../BMC/hardware.md) |
| **i2c topology / address table** | 看 schematic 時要確認的兩件事：bus 怎麼接、每顆裝置的位址。**schematic 的 bus 編號從 1 開始數** | [schemantic](../BMC/schemantic.md)、[porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **i2c-mux** | I2C 多工器，用來把一條 bus 擴展成多條子 bus | [hotplug](../BMC/hotplug.md) |
| **i2c-hotplug** | 在可熱插拔裝置（模組、cable card、riser）出現/消失時動態建立或移除 I2C bus 與 device node，不需重開機。由 presence GPIO 或 interrupt 觸發。**重點是拔除時要乾淨移除**，避免殘留 stale 的 `/sys/bus/i2c/devices/...` | [hotplug](../BMC/hotplug.md) |

### PMBus

| 名詞 | 說明 | 出處 |
|---|---|---|
| **PMBus (Power Management Bus)** | 建立在 SMBus 上的電源管理協定，用來讀電壓、電流、功率等 | [pmbus](../BMC/pmbus.md)、`BMC/device_driver/_index.md` |
| **PMBus 讀寫原語** | read byte / read word / write byte / write word | [pmbus](../BMC/pmbus.md) |
| **PMBus 資料格式** | **linear**（m=1）與 **direct** 兩種。格式定義在 `pmbus.h` | [pmbus](../BMC/pmbus.md)、[porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **Linear11** | 浮點編碼格式：N = 高 5 bit 有號整數、Y = 低 11 bit 有號整數，實際值 = Y 乘以 2 的 N 次方 | `BMC/device_driver/_index.md`、[ai_bmc](../ai_bmc.md) |
| **direct format 的 m / b / R** | direct 格式需依公式填入三個係數：`X = (1/m) * (Y * 10^(-R) - b)`，程式中設定 `info->m[...]`、`info->b[...]`、`info->R[...]` | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **`pmbus_driver_info`** | driver 的核心結構。`.pages` 指定裝置支援幾個 page、`.format[PSC_VOLTAGE_IN]` 指定資料格式、`.func[0]` 用 functionality bitmask 啟用支援的 PMBus 指令 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **`pmbus_do_probe(client, info)`** | probe 流程的第二步：填完 `pmbus_driver_info` 後呼叫它交給 PMBus core | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **`pmbus_read_word_data()`** | 送 PMBus 指令讀取指定 register 的 16-bit word。另有 `pmbus_read_byte_data()`、`pmbus_write_word_data()` | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md)、`BMC/device_driver/_index.md` |
| **`.read_word_data`** | driver 的 word 讀取 handler，負責讀出 sensor 值 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **`PMBUS_READ_VIN` 等常數** | PMBus register 常數，定義在 `pmbus.h` | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **VIN / VOUT / POUT / IOUT 對照** | function bitmask `PMBUS_HAVE_VIN` → reg `PMBUS_READ_VIN` → sysfs `in1`；VOUT → `in2`；POUT → `power2`；IOUT → `curr2` | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **`P = I * V` 驗證** | porting 完成後，用輸入輸出值是否滿足此式、且落在 schematic 標示的範圍內來驗證 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md)、[pmbus](../BMC/pmbus.md) |
| **呼叫鏈** | user space（如 `sensors`）→ PMBus core → driver 的 `read_word_data` → 底層 I2C 送 command code → 取得 word | `BMC/device_driver/_index.md` |

### Device Driver 與 Device Tree

| 名詞 | 說明 | 出處 |
|---|---|---|
| **`probe`** | driver 與裝置配對成功時被呼叫的初始化函式，porting 的核心工作之一 | [pmbus](../BMC/pmbus.md)、`BMC/device_driver/_index.md` |
| **Kconfig** | 定義 config 選項讓 kernel 能在 menuconfig 中辨識並啟用 driver。位置 `linux/drivers/hwmon/pmbus/Kconfig` | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md)、`BMC/device_driver/_index.md` |
| **defconfig** | 預設設定檔（`<linux>/arch/arm/configs/aspeed_<project>_defconfig`）。`y` = 編進 kernel、`m` = 編成模組 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **Makefile 一行** | `obj-$(CONFIG_SENSORS_XXX) += xxx.o`，告訴編譯器 `.config` 有這個選項時要 build | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **`MODULE_DEVICE_TABLE(i2c, ...)`** | 宣告 driver 支援的 i2c device id 表 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **`i2c_driver` 結構** | 含 `.driver.name`、`.of_match_table`、`.probe_new`、`.remove`、`.id_table`，最後用 `module_i2c_driver()` 註冊 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **dts / dtsi / dtb / dtc** | Device Tree 的原始檔／可被 include 的片段／編譯後的 binary／編譯器 | [device_tree](../BMC/device_tree.md) |
| **`compatible`** | device node 與 driver 配對的字串（如 `"mps,mpc42013"`），搭配 `reg` 指定 I2C 位址 | [device_tree](../BMC/device_tree.md)、[porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md)、[hwmon](../BMC/hwmon.md) |
| **binding yaml** | driver 的 device tree 文件，位置 `linux/Documentation/devicetree/bindings/hwmon/...`，用 `$id` / `$schema` / `properties` 描述 | [device_tree](../BMC/device_tree.md)、[porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **phandle** | Device Tree 中指向另一個 node 的參照 | [device_tree](../BMC/device_tree.md) |
| **device tree 階層** | 由 `.dts` 逐層 include `.dtsi`，如 `aspeed-<project>-<board>-evt.dts` → `...-ast2600-<board>.dtsi` → `...-swb.dtsi` → `...-swb-i2c.dtsi`。插入 node 前要先找對層級 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **i2c alias** | 在 `<board>-i2c-aliases.dtsi` 中用 `alias` 為 bus 取固定編號，避免編號浮動 | `BMC/device_driver/_index.md` |
| **`linux-aspeed`** | Yocto 建置樹中 kernel 原始碼的位置（`build/workspace/sources/linux-aspeed`） | [device_tree](../BMC/device_tree.md) |

### GPIO / 中斷 / 其他匯流排

| 名詞 | 說明 | 出處 |
|---|---|---|
| **GPIO 工具組** | `gpiodetect`（列 controller）、`gpioinfo`（列 line）、`gpioset` / `gpioget`（寫/讀）。sysfs 路徑 `/sys/class/gpio` | [hardware](../BMC/hardware.md) |
| **GPIO hog** | 在 device tree 中宣告某支 GPIO 於**開機時就被 kernel 佔用並設成固定狀態**，不需 driver 或 user space 介入。常用於 enable、reset、power-good select | [hog](../BMC/hog.md) |
| **`gpio-hog` 屬性** | 標示該子節點是一個 hog；方向用 `output-high` / `output-low` / `input`；`line-name` 命名 | [hog](../BMC/hog.md) |
| **hog 的取捨** | kernel 在 probe gpio controller 時就套用，**早於大部分服務**；但被 hog 的 pin 之後不能再被別的 driver/user space 請求。**要動態控制就別用 hog** | [hog](../BMC/hog.md) |
| **`devmem`** | 直接讀寫實體記憶體位址（暫存器）的工具 | [hardware](../BMC/hardware.md) |
| **ADC** | 類比數位轉換，BMC 用來讀電壓（AST2600 上的驅動為 `aspeed-adc`） | [hardware](../BMC/hardware.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **SPI（single / dual / quad / octal）** | 序列周邊介面，依資料線數量分級。BMC 的 U-Boot / kernel / rootfs 都放在 SPI Flash 上 | [hardware](../BMC/hardware.md) |
| **SCM / DCSCI** | 板卡/模組類別代號 | [hardware](../BMC/hardware.md) |
| **IRQ (Interrupt Request)** | 硬體通知 CPU 有事件發生，CPU 暫停當前工作轉去執行 irq handler，**不必忙碌輪詢即可即時反應** | [interrupt](../BMC/interrupt.md) |
| **`/proc/interrupts`** | 觀察每個 IRQ 編號、各 CPU 上的觸發次數、中斷控制器與裝置名稱。`watch -n1 cat /proc/interrupts` 可看哪個中斷正頻繁觸發 | [interrupt](../BMC/interrupt.md) |
| **top half** | 硬體中斷 handler，在 interrupt context 執行：**必須極短、不可睡眠**，通常只做硬體 ack 與記錄 | [interrupt](../BMC/interrupt.md) |
| **bottom half** | 延後處理機制：softirq、tasklet、workqueue（其中 workqueue 跑在 process context，**可睡眠**） | [interrupt](../BMC/interrupt.md) |
| **`request_irq()`** | driver 註冊中斷 handler。handler 回傳 `IRQ_HANDLED`（已處理）或 `IRQ_NONE`（非本裝置，用於共享 IRQ） | [interrupt](../BMC/interrupt.md) |

### EEPROM / FRU 讀取

| 名詞 | 說明 | 出處 |
|---|---|---|
| **EEPROM** | 存放 FRU 資訊的非揮發記憶體，掛在 I2C bus 上 | [fru](../BMC/fru.md)、[hardware](../BMC/hardware.md) |
| **`at24`** | 常見的 EEPROM kernel driver，綁定後會產生 `eeprom` sysfs 節點，可 `hexdump -C eeprom` 直接 dump | [fru](../BMC/fru.md) |
| **`i2ctransfer -y -f 13 w2@0x48 0x00 0x00 r128`** | 無 driver 時直接讀 EEPROM：對 bus 13、位址 0x48 先寫 2-byte 內部位址（word address），再連讀 128 bytes | [fru](../BMC/fru.md) |
| **Common Header** | FRU dump 開頭的區塊，內含指向 Chassis / Board / Product Info 各區塊的 offset | [fru](../BMC/fru.md) |
| **`ipmitool fru` / `frutool`** | 把 FRU raw bytes 解析成人類可讀欄位 | [fru](../BMC/fru.md) |

### 板上元件

| 名詞 | 說明 | 出處 |
|---|---|---|
| **CPLD** | Complex Programmable Logic Device，板上可程式邏輯裝置，容量介於 GAL 與 FPGA 之間。**非揮發**（開機即運作，不需外部載入 bitstream） | [cpld](../BMC/cpld.md) |
| **Power sequencing** | CPLD 的主要用途：依正確順序與時序拉起各組電源 rail，等 power-good 才進下一步。是開機流程中電源時序的關鍵一環 | [cpld](../BMC/cpld.md) |
| **Glue logic（膠合邏輯）** | 把各晶片間零散的訊號整合、解碼 | [cpld](../BMC/cpld.md) |
| **presence / strap 讀取** | CPLD 彙整板上偵測訊號給 BMC | [cpld](../BMC/cpld.md) |
| **in-system programming** | CPLD firmware 可更新，BMC 有時負責在板上更新 | [cpld](../BMC/cpld.md) |
| **Retimer** | 主動元件，把衰減的 PCIe 訊號**重新取樣、重建（re-clock）**，恢復乾淨眼圖、延長可用走線距離。常見於 PCIe Gen4/Gen5 跨 riser、cable、backplane 的長通道 | [retimer](../BMC/retimer.md) |
| **redriver vs retimer** | redriver 只做類比等化/放大（**不重生時脈**）；retimer 有 **CDR**，會完整重建訊號，等於一個新的訊號起點 | [retimer](../BMC/retimer.md) |
| **eye margin** | retimer 的訊號品質狀態，通常透過 I2C/SMBus 由 BMC 存取 | [retimer](../BMC/retimer.md) |
| **retimer 韌體更新** | BMC 常透過 I2C 或 **PLDM (Type 5, firmware update)** 更新並回報版本。**通常需在特定 power state 下進行**，避免影響鏈路 | [retimer](../BMC/retimer.md) |
| **tmp75** | 常見的 I2C 溫度感測晶片，看 datasheet 與 address table 時的典型例子 | [schemantic](../BMC/schemantic.md)、[spec](../BMC/spec.md)、[hwmon](../BMC/hwmon.md) |
| **block diagram** | 讀 spec / datasheet 時的入口，先看方塊圖再查暫存器 | [spec](../BMC/spec.md) |

### MCTP / PLDM

| 名詞 | 說明 | 出處 |
|---|---|---|
| **MCTP** | Management Component Transport Protocol，DMTF 定義的傳輸協定，讓平台管理元件（BMC、NIC、SSD、retimer、GPU）在各種實體匯流排上交換管理訊息 | [mctp](../BMC/mctp.md) |
| **PMCI** | Platform Management Communications Infrastructure，MCTP 所屬的 DMTF 標準家族 | [mctp](../BMC/mctp.md) |
| **EID (Endpoint ID)** | MCTP 的端點識別碼。MCTP 提供與底層匯流排無關的定址與封包傳送層 | [mctp](../BMC/mctp.md) |
| **binding** | MCTP 可跑的實體層：SMBus/I2C、PCIe VDM、USB、Serial、KCS | [mctp](../BMC/mctp.md) |
| **PLDM** | Platform Level Data Model，跑在 MCTP 上的訊息類型，涵蓋 sensor、FRU、firmware update | [mctp](../BMC/mctp.md)、[retimer](../BMC/retimer.md) |
| **NC-SI over MCTP / SPDM** | MCTP 承載的其他訊息類型（SPDM 用於安全驗證） | [mctp](../BMC/mctp.md) |
| **libmctp / mctpd / pldmd** | OpenBMC 中 MCTP 的函式庫與 daemon，負責建立端點、路由封包；`pldmd` 提供 PLDM over MCTP 支援 | [mctp](../BMC/mctp.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |

---

## 四、感測與熱控

### hwmon 與 sensor

| 名詞 | 說明 | 出處 |
|---|---|---|
| **hwmon** | Linux 的 hardware monitoring 子系統，用**統一介面**把溫度、電壓、電流、風扇轉速、功率暴露到 user space | [hwmon](../BMC/hwmon.md)、[sensor_porting](../BMC/sensor_porting.md) |
| **`/sys/class/hwmon/hwmonN/`** | hwmon 的 sysfs 節點位置 | [hwmon](../BMC/hwmon.md) |
| **`temp1_input` / `in0_input` / `fan1_input` / `curr1_input` / `power1_input`** | hwmon 的命名慣例，值多為毫度／毫伏／毫安 | [hwmon](../BMC/hwmon.md)、`BMC/device_driver/_index.md` |
| **`*_max` / `*_crit` / `*_label`** | 提供門檻與名稱的 hwmon 屬性 | [hwmon](../BMC/hwmon.md) |
| **找 driver 落在哪個 hwmon** | 逐一 `cat /sys/class/hwmon/hwmon*/name` 比對——hwmon 編號會浮動，不能寫死 | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **driver define** | 感測晶片（tmp75、adm1275、pmbus 裝置）的 kernel driver 註冊成 hwmon device，並定義提供哪些 channel/屬性 | [hwmon](../BMC/hwmon.md) |
| **phosphor-hwmon** | 讀 hwmon sysfs，把讀值轉成 D-Bus 上的 `xyz.openbmc_project.Sensor.Value` | [hwmon](../BMC/hwmon.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **`xyz.openbmc_project.Sensor.Value`** | 感測器讀值在 D-Bus 上的標準介面，供 Redfish / IPMI / 風扇控制取用 | [hwmon](../BMC/hwmon.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **phosphor-sensor-svcs** | 感測器讀值服務（溫度、電壓、風扇轉速） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **sensor porting 的四個環節** | hwmon → dbus-sensors → entity manager → fru device | [sensor_porting](../BMC/sensor_porting.md) |
| **感測器偵測流程** | Device Tree / JSON 設定 → Entity Manager → D-Bus 物件建立 → phosphor-hwmon 讀 `/sys/class/hwmon/hwmon*/` → 數值更新至 D-Bus → bmcweb（Redfish Sensors）與 ipmid（IPMI SDR）取用 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |

### 熱控

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Thermal Management** | 讀溫度感測器、依策略調整風扇轉速，在「不過熱」與「不吵／省電」之間取平衡 | [thermal](../BMC/thermal.md) |
| **thermal zone** | 一個散熱分區，把一組熱源 sensor 與負責散熱的風扇綁在一起 | [thermal](../BMC/thermal.md) |
| **thermal margin vs absolute** | 控制常用「**距離上限還有多少度**」而非絕對溫度，便於跨不同元件統一調控 | [thermal](../BMC/thermal.md) |
| **failsafe** | sensor 失聯／逾時時，風扇拉到安全高轉速 | [thermal](../BMC/thermal.md)、[pid_control](../BMC/pid_control.md) |
| **phosphor-pid-control** | OpenBMC 的風扇/散熱**閉迴路控制 daemon**，依感測器讀值動態調整風扇 PWM，避免過熱也避免全速空轉 | [pid_control](../BMC/pid_control.md) |
| **PID zone** | 一個散熱分區，包含一組輸入 sensor 與輸出風扇 | [pid_control](../BMC/pid_control.md) |
| **thermal PID** | `temp -> margin/setpoint`：讀溫度算出目標 | [pid_control](../BMC/pid_control.md) |
| **fan PID** | `fan -> pwm`：以風扇轉速（RPM）為回授做閉迴路 | [pid_control](../BMC/pid_control.md) |
| **Stepwise** | 查表式的**非 PID** 控制方式 | [pid_control](../BMC/pid_control.md)、[thermal](../BMC/thermal.md) |
| **PID 參數** | `proportionalCoeff`(P)、`integralCoeff`(I)、`derivativeCoeff`(D)、`setpoint`、`samplePeriod` | [pid_control](../BMC/pid_control.md) |
| **設定來源的演進** | 傳統用 `/etc/phosphor-pid-control/config.json`；現多改由 **Entity Manager** 產生的 D-Bus 設定動態載入（config type：`Pid`、`Pid.Zone`、`Stepwise`、`Fan`） | [pid_control](../BMC/pid_control.md)、[thermal](../BMC/thermal.md) |
| **phosphor-fan-presence** | 風扇存在偵測與轉速控制服務 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **`pwm-fan`** | kernel 的風扇控制驅動 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **Linux thermal framework** | kernel 自己的散熱框架：`/sys/class/thermal/thermal_zoneN/`、trip point、cooling device。視平台是否採用 | [thermal](../BMC/thermal.md) |
| **Redfish `Chassis/.../Thermal`** | 對外呈現溫度與風扇狀態的資源（新版為 `ThermalSubsystem`） | [thermal](../BMC/thermal.md) |

---

## 五、事件與 Log

| 名詞 | 說明 | 出處 |
|---|---|---|
| **Event Log** | OpenBMC 的事件/錯誤紀錄機制，把硬體與系統事件記成**結構化 log**，供本機除錯與遠端（Redfish）查詢 | [event_log](../BMC/event_log.md) |
| **phosphor-logging** | 核心服務，提供建立與儲存 log 的 D-Bus 介面（`xyz.openbmc_project.Logging`） | [event_log](../BMC/event_log.md)、[openbmc](../BMC/openbmc.md) |
| **log entry 欄位** | `Severity`、`Message`、時間戳、`AdditionalData`（key=value 附加資訊） | [event_log](../BMC/event_log.md) |
| **`lg2` / `elog`** | 開發者用來產生 log 的 API | [event_log](../BMC/event_log.md) |
| **callout** | 嚴重事件可帶的附加資訊，**指出故障零件** | [event_log](../BMC/event_log.md) |
| **`/xyz/openbmc_project/logging/entry/*`** | D-Bus 上的 log entry 路徑，可用 `busctl` 查詢 | [event_log](../BMC/event_log.md) |
| **Redfish LogService** | 對外讀取事件的介面：`/redfish/v1/Systems/system/LogServices/EventLog/Entries` | [event_log](../BMC/event_log.md) |
| **phosphor-log-manager** | 系統事件記錄服務（SEL / Event Log） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **phosphor-sel-logger** | 專責產生並維護 **IPMI SEL** 的服務：監聽 D-Bus 事件（sensor threshold 觸發等），寫成 IPMI SEL entry（含 sensor type、event data、時間戳） | [sel_logger](../BMC/sel_logger.md) |
| **`ipmitool sel list` / `sel clear`** | 查詢／清除 SEL 的傳統工具指令 | [sel_logger](../BMC/sel_logger.md) |
| **`/xyz/openbmc_project/Logging/IPMI`** | D-Bus 上 SEL entry 的相關路徑 | [sel_logger](../BMC/sel_logger.md) |
| **sel-logger vs phosphor-logging** | phosphor-logging 是**通用**的 OpenBMC event/error log；sel-logger 專責產生「**IPMI 相容**」的 SEL 格式 | [sel_logger](../BMC/sel_logger.md) |
| **journal / journald** | systemd 的底層 daemon log，用 `journalctl` 查看 | [event_log](../BMC/event_log.md)、[systemd](../BMC/systemd.md) |

---

## 六、開機流程

### 階段

| 階段 | 說明 | 出處 |
|---|---|---|
| **Boot ROM（Chip ROM）** | SoC 內建**不可修改**的程式碼，CPU Reset 後從固定位址開始執行（AST2600 的 reset vector 為 `0x00000000`）。初始化最基本時鐘與 SRAM、決定 boot source、把 U-Boot SPL 複製到內部 SRAM | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[bootup](../BMC/bootup.md) |
| **U-Boot SPL (Secondary Program Loader)** | SoC 剛上電時只有內部 SRAM（64KB ~ 256KB）容不下完整 U-Boot，因此先跑輕量 SPL：初始化 **DRAM Controller（DDR4 training）**，把 U-Boot Proper 載入 DRAM | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **U-Boot Proper** | 初始化周邊（NCSI/RGMII 網路、USB、I2C、SPI、GPIO）、讀環境變數、從 SPI Flash 讀 FIT Image、傳 DTB 給 kernel、設 kernel cmdline。可透過序列埠中斷進入 console 手動下指令 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[bootup](../BMC/bootup.md) |
| **Linux Kernel** | 解壓縮 zImage → 讀 DTB 識別硬體 → 初始化驅動 → 從 MTD 掛載 SquashFS rootfs → 執行 `/sbin/init` | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[bootup](../BMC/bootup.md) |
| **rootfs** | 掛載根檔案系統後執行 init（OpenBMC 用 systemd），啟動 Redfish、IPMI、感測器監控等服務，BMC 正式可運作 | [bootup](../BMC/bootup.md) |

### 相關名詞

| 名詞 | 說明 | 出處 |
|---|---|---|
| **BMC boot vs Host boot** | 兩條**相互獨立**的路徑。BMC 在 Host 開機前數秒到數十秒先完成啟動，之後持續運行等待 power on 指令 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **+5VSB（Standby Power）** | 主機板插上 AC 後 ATX 輸出的待機電壓。**BMC 先上電，Host CPU 仍 Power Off** | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **SCU (System Control Unit)** | ASPEED 的暫存器區，決定 Boot Strap（開機引腳配置），可設定從 SPI / UART / eMMC 開機 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **`zImage`** | 壓縮過的 ARM Linux kernel image，前段的解壓縮 stub 會先把自己解開再啟動真正的 kernel | [bootup](../BMC/bootup.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **`uImage`** | 含 u-boot header 的 kernel image | [bootup](../BMC/bootup.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **FIT Image (Flattened Image Tree)** | 把 kernel + DTB + initramfs 打包成一個檔，OpenBMC 的標準作法 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[bootup](../BMC/bootup.md) |
| **`bootcmd` / `bootargs`** | U-Boot 環境變數。典型 `flashboot` 為 `sf probe && sf read ... && bootm ${loadaddr}` | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **kernel cmdline** | 如 `console=ttyS4,115200n8`（UART console）、`rootfstype=squashfs`、`root=/dev/mtdblock4`、`rw` | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **Flash layout（典型）** | SPI Flash（通常 128MB）依序放：U-Boot SPL（~64KB）→ U-Boot Proper（~512KB）→ U-Boot Env（~64KB）→ Linux Kernel FIT Image（~8MB）→ RootFS（剩餘空間） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **Dual Flash / Dual Image (A/B)** | Flash A 正常使用、Flash B 備援，供 OTA 更新或 Flash A 損壞時切換（fail-safe）。U-Boot 讀 GPIO 或環境變數決定從哪個 image 開機 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[bootup](../BMC/bootup.md) |
| **SquashFS / UBIFS / OverlayFS** | rootfs 以 **SquashFS（唯讀，在 Flash 上）** 搭配 **UBIFS / tmpfs（可讀寫層）**，透過 **OverlayFS** 對上層呈現統一可讀寫視圖。因此**韌體更新不影響使用者設定**，**工廠重置 = 清除可讀寫層** | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **initramfs** | 開機時的暫時根檔案系統（OpenBMC 中為可選） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **ASPEED AST2500 / AST2600** | 最常見的 BMC SoC。AST2500 為 ARM Cortex-A7、AST2600 為 Cortex-A7 雙核，OpenBMC 主線 kernel 6.x | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[bootup](../BMC/bootup.md) |
| **Nuvoton NPCM750 / NPCM845** | 另一系列 BMC SoC，分別為 Cortex-A9 / Cortex-A35 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **`aspeed-i2c` / `aspeed-adc` / `aspeed-vuart`** | AST 平台的 kernel 驅動：I2C bus、電壓感測器、Virtual UART（SOL 用） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **phosphor-state-manager** | 管理 Host 電源狀態的服務。Redfish/IPMI 的開機請求最後會由它去控制 GPIO 的 **`PWRON#`**（電源按鈕訊號） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **Power Restore Policy** | `AlwaysOff`（BMC 就緒後 Host 保持關機）／`AlwaysOn`（自動開啟 Host）／`LastState`（恢復斷電前狀態） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |

### systemd

| 名詞 | 說明 | 出處 |
|---|---|---|
| **systemd (PID 1)** | OpenBMC 的 init 系統，管理所有服務的啟動順序與相依關係 | [systemd](../BMC/systemd.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **service / target** | systemd 的兩個基本單位：服務本身／同步點（一組服務的集合） | [systemd](../BMC/systemd.md) |
| **unit 檔案位置** | `/etc/systemd/`（設定）與 `/lib/systemd/system/`（系統 service 檔案） | [systemd](../BMC/systemd.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **標準 target 順序** | `sysinit.target` → `basic.target` → `network.target` → `multi-user.target`（bmcweb、ipmid、phosphor-log-manager、entity-manager、phosphor-fan-presence…） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **OpenBMC 特有 target** | `obmc-standby.target`（BMC 就緒、Host 仍關機）、`obmc-chassis-on@0.target`（Host 開機中）、`obmc-host-on@0.target`、`obmc-host-off@0.target` | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |

### Flash 燒錄

| 名詞 | 說明 | 出處 |
|---|---|---|
| **MTD (Memory Technology Device)** | Linux 的 flash 裝置抽象層，rootfs 從 `/dev/mtdblockN` 掛載 | [flash](../BMC/flash.md)、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **`flashcp` / `flash_erase` / `nand write` / `dd`** | 更新 BMC flash 的常用工具 | [flash](../BMC/flash.md) |
| **用 `dd` 拼 image** | 依 offset 把 u-boot（seek=65536）、uImage（seek=524288）、dtb（seek=12689408）分別寫進同一個 image 檔（`conv=notrunc bs=1`） | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |
| **上板燒錄** | `scp` image 到 BMC 的 `/var/`，再 `dd if=... of=/dev/mtdblock0 bs=64k seek=0` 後 `reboot` | [porting_pmbus_driver](../BMC/device_driver/porting_pmbus_driver.md) |

---

## 七、系統服務與網路

| 名詞 | 說明 | 出處 |
|---|---|---|
| **phosphor-networkd** | OpenBMC 的網路管理服務（daemon 名 `xyz.openbmc_project.Network`），負責 IP、DNS、hostname、VLAN、NTP 設定，並透過 D-Bus 曝露給 Redfish / IPMI | [network](../BMC/network.md) |
| **systemd-networkd** | 底層實際管理 `.network` 設定的服務 | [network](../BMC/network.md) |
| **`/xyz/openbmc_project/network/<interface>`** | 網路設定的 D-Bus 物件路徑 | [network](../BMC/network.md) |
| **Redfish `EthernetInterfaces`** | 對外讀寫網路設定的資源（static / DHCP IPv4、IPv6、gateway、DNS、hostname、MAC、VLAN） | [network](../BMC/network.md) |
| **NTP** | 與外部時間伺服器對時。**BMC 常無 RTC 電池或會漂移**，NTP 對 event log、SEL、憑證有效期的時間戳一致性很重要 | [ntp](../BMC/ntp.md) |
| **systemd-timesyncd** | 輕量 SNTP client，底層負責向 NTP server 對時 | [ntp](../BMC/ntp.md) |
| **phosphor-time-manager** | OpenBMC 的時間管理服務，D-Bus 介面為 `xyz.openbmc_project.Time.*` | [ntp](../BMC/ntp.md) |
| **TimeSyncMethod** | 時間模式：**NTP**（由 NTP server 決定，timesyncd 生效）／**Manual**（手動設定，停用 NTP） | [ntp](../BMC/ntp.md) |
| **Redfish `Managers/bmc/NetworkProtocol`** | 設定 NTP server 與 NTP 開關的資源 | [ntp](../BMC/ntp.md) |

---

## 八、除錯與測試

### 除錯

| 名詞 | 說明 | 出處 |
|---|---|---|
| **BMC 除錯的限制** | 資源有限（記憶體小、無 GUI），因此靠遠端 gdbserver 動態除錯與事後 coredump 分析 | [debug](../BMC/debug.md) |
| **`gdbserver`** | BMC 端只跑輕量的 gdbserver（`gdbserver :2345 /usr/bin/my-daemon` 或 `gdbserver :2345 --attach <pid>`），完整 gdb 跑在開發主機上 | [debug](../BMC/debug.md) |
| **cross gdb + `target remote`** | 開發主機用對應 target 的 cross gdb（如 `arm-linux-gnueabi-gdb`）連線：`target remote <bmc-ip>:2345` | [debug](../BMC/debug.md) |
| **coredump analysis** | crash 時保留 core 檔，事後 `gdb /path/to/binary /path/to/core` 再 `bt` 印 backtrace 找 crash 位置。需先 `ulimit -c unlimited` | [debug](../BMC/debug.md) |
| **debug symbol / strip** | 分析時**務必用帶 debug symbol 的未 strip 版本 binary**，backtrace 才能對應到原始碼行號 | [debug](../BMC/debug.md) |
| **`systemd-coredump` / `coredumpctl`** | OpenBMC 多以 systemd-coredump 收集 core，用 `coredumpctl list` / `coredumpctl gdb` 取用 | [debug](../BMC/debug.md) |
| **`dmesg`** | 查 kernel log，如 `dmesg \| grep -i "i2c\|aspeed\|sensor"` | `BMC/device_driver/_index.md`、[openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| **`journalctl`** | `journalctl -b`（本次開機所有 log）、`-u bmcweb`（特定服務）、`-f`（即時追蹤） | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md)、[systemd](../BMC/systemd.md) |
| **`systemctl list-units --failed`** | 列出啟動失敗的服務。也可用 `systemctl list-units "phosphor*" "obmc*" "bmcweb*"` 看 OpenBMC 服務群 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |

### 常見開機失敗原因

| 現象 | 可能原因 | 出處 |
|---|---|---|
| U-Boot 無輸出 | SPI Flash 損壞、Boot ROM 無法讀取 SPL | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| Kernel panic | DTB 錯誤、RootFS 損壞、MTD partition 錯誤 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| bmcweb 無法連線 | 網路設定錯誤、憑證問題、服務啟動失敗 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| 感測器無數據 | entity-manager 設定檔錯誤、I2C 裝置無回應 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |
| IPMI 無回應 | ipmid 服務崩潰、KCS 驅動問題 | [openbmc_boot_flow](../BMC/openbmc_boot_flow.md) |

### 測試

| 名詞 | 說明 | 出處 |
|---|---|---|
| **test plan（測試計畫）** | 測試前先定義測試範圍、對象版本、測試環境（硬體平台、連線方式）、通過標準與各項 test case。**讓測試有依據且可重複** | [testing](../BMC/testing.md) |
| **functional testing（功能測試）** | 依 test plan 逐項驗證：IPMI/Redfish 指令回應、感測器讀值、遠端開關機/SOL/韌體更新流程。**偏重「行為是否符合預期輸出」，而非內部實作** | [testing](../BMC/testing.md) |
| **report（測試報告）** | 彙整每個 test case 的 pass/fail、實際結果、log 與環境資訊，作為版本是否可釋出的判斷依據 | [testing](../BMC/testing.md) |
| **stress / regression / recovery test** | 完整驗證常再加上：長時間穩定度、回歸測試、斷電/更新失敗還原 | [testing](../BMC/testing.md) |
| **Robot Framework (`robot`)** | OpenBMC 上撰寫自動化測試腳本的工具 | [testing](../BMC/testing.md) |

### AI 輔助開發

| 名詞 | 說明 | 出處 |
|---|---|---|
| **適合用 AI 的場景** | 查 IPMI / PMBus spec、寫 driver 骨架（probe / Kconfig / Makefile 模板）、解讀 dmesg / journalctl 錯誤、理解 Yocto recipe、寫 D-Bus interface、產 Redfish 測試腳本 | [ai_bmc](../ai_bmc.md) |
| **AI 產出必須驗證的三處** | ①Kernel API 版本差異大（OpenBMC 常用 5.15 / 6.1）②PMBus 的 page / phase 參數容易出錯，務必對照 datasheet ③`xyz.openbmc_project.*` 大小寫敏感，AI 常拼錯 | [ai_bmc](../ai_bmc.md) |

---

## 九、資料中心與叢集

| 名詞 | 說明 | 出處 |
|---|---|---|
| **cluster（叢集）** | 資料中心的組織單位，透過高速網路把大量伺服器組成一個運算/儲存整體 | [data_center](../BMC/data_center.md) |
| **headnode（管理/登入節點）** | 又稱 management node 或 login node。負責使用者登入、作業排程、監控與部署，是進入叢集的入口，**通常不跑重負載運算** | [data_center](../BMC/data_center.md) |
| **compute node（運算節點）** | 實際執行運算的主力機器，數量最多。通常**無狀態（stateless）**，由 headnode 統一開機與派工 | [data_center](../BMC/data_center.md) |
| **storage node（儲存節點）** | 提供共享儲存，常搭配分散式/平行檔案系統（Ceph、Lustre、NFS），讓各 compute node 共用同一份資料 | [data_center](../BMC/data_center.md) |
| **job scheduler** | headnode 上的作業排程器，如 Slurm、PBS | [data_center](../BMC/data_center.md) |
| **out-of-band 管理** | 每個節點內建 BMC，透過獨立的管理網路（IPMI/Redfish）遠端開關機、監控感測器、更新韌體，**不必實體接觸機器** | [data_center](../BMC/data_center.md) |
