---
title: BMC / OpenBMC 文章索引
sidebar_label: BMC 系列索引
sidebar_position: 4
---

# BMC / OpenBMC 文章索引

本頁整理知識庫中所有 BMC / OpenBMC 筆記，依主題分類，方便從「想做什麼」找到對應文章。
名詞定義請參考 [BMC 名詞表](bmc_glossary.md)。

---

## 一、OpenBMC 架構與建置

| 文章 | 內容 |
|---|---|
| [OpenBMC 總覽](../BMC/openbmc.md) | 佔位頁：一段開源伺服器韌體演講連結，加上 recipe／`meta-layer`／bmcweb／entity manager 等關鍵字，尚未成文 |
| [D-Bus](../BMC/dbus.md) | 佔位頁：只有 dbus service／interface、`busctl tree`／`introspect`／`call` 等關鍵字，無說明文字 |
| [Entity Manager](../BMC/entity_manager.md) | 用 JSON（`Exposes`／`Probe`）描述板上硬體並開機時動態探測，命中後把設定放上 D-Bus 供 dbus-sensors／pid-control 訂閱；一份 image 支援多板型，新增硬體多半只加 JSON 不改 C++ |
| [Yocto Project](../BMC/yocto.md) | OpenBMC 的 firmware image 建置框架：bitbake／recipe(`.bb`)／`.bbappend`／layer(`meta-*`)，`. setup <machine>` 後 `bitbake obmc-phosphor-image`，產物落在 `tmp/deploy/images/` |
| [Git / Gerrit Workflow](../BMC/git.md) | OpenBMC 上游的 Gerrit code review 流程：一個 commit = 一個 change，用 `git review` 推送、`Change-Id` 追蹤修訂、`Code-Review +2` 才可合併、每個 commit 要 `Signed-off-by` |

---

## 二、管理介面（IPMI / Redfish / SSE / SOL）

| 文章 | 內容 |
|---|---|
| [IPMI](../BMC/ipmi.md) | 佔位頁：只有 ipmi intro／sel／sdr／fru／ipmi raw cmd 關鍵字，尚未成文 |
| [Redfish](../BMC/redfish.md) | DMTF 的 RESTful 管理介面（HTTPS + JSON），資源導向、標準動詞，目標取代 IPMI；OpenBMC 由 bmcweb 把 D-Bus 資料對映成 `/redfish/v1/` 底下的 Systems／Chassis／Managers 等資源 |
| [Redfish EventService](../BMC/event_service.md) | Redfish 事件訂閱機制：`POST` 到 `EventService/Subscriptions` 帶 `Destination` 與過濾條件，事件發生時 BMC 主動推送，免管理端輪詢；遞送方式分 push(webhook) 與 SSE |
| [Server-Sent Events (SSE)](../BMC/sse.md) | 基於 HTTP 的單向串流（`text/event-stream`），client 開一條長連線即時收事件，免預先註冊 webhook destination；比 WebSocket 簡單但只能單向 |
| [SOL（Serial over LAN）](../BMC/sol.md) | 概念與運作要點：BMC 把 host serial 封進 IPMI over LAN（RMCP+、UDP 623）轉給遠端 client，`ipmitool -I lanplus ... sol activate` 啟用，跳脫序列 `~.` |
| [Serial over LAN（完整版）](../BMC/serial_over_lan.md) | SOL 的詳版筆記：元件角色表、封包走向圖、RMCP+ 封包格式、`ipmitool` 指令表與使用場景，並提到 Redfish ConsoleService（WebSocket 串流）取代 IPMI SOL |

---

## 三、硬體存取與匯流排

| 文章 | 內容 |
|---|---|
| [Hardware（硬體存取）](../BMC/hardware.md) | 佔位頁：I2C／SMBus／PMBus、EEPROM／FRU、GPIO 工具（`gpiodetect`／`gpioset`）、`devmem`、ADC、SPI 等關鍵字清單 |
| [PMBus](../BMC/pmbus.md) | 佔位頁：probe／read-write 原語／`i2cdetect`／`P=IV`／linear-direct 等關鍵字 |
| [Porting PMBus Driver](../BMC/device_driver/porting_pmbus_driver.md) | 完整實作指南：讀 schematic 找 bus → 寫 device tree node（`compatible`／`reg`）→ Kconfig／defconfig／Makefile → 填 `pmbus_driver_info` 與 `.read_word_data` → binding yaml → 用 `dd` 拼 image 上板燒錄 → 用 `P=I*V` 驗證 |
| [Device Tree](../BMC/device_tree.md) | 佔位頁：dts／dtsi／dtb／dtc、`compatible`、binding yaml、phandle、`linux-aspeed` 原始碼路徑等關鍵字 |
| [CPLD](../BMC/cpld.md) | 板上可程式邏輯裝置（非揮發，開機即運作）：伺服器用它做 power sequencing、reset／clock 邏輯、glue logic、presence／strap 讀取；BMC 經 GPIO／I2C／JTAG 與它互動，並可在板做 in-system programming |
| [PCIe Retimer](../BMC/retimer.md) | retimer 用 CDR 重新取樣、重建 PCIe 訊號以延長走線（對比 redriver 只放大不重生時脈）；BMC 經 I2C／SMBus 讀 eye margin，並用 I2C 或 PLDM(Type 5) 更新其韌體 |
| [FRU（Field Replaceable Unit）](../BMC/fru.md) | FRU EEPROM（IPMI FRU 格式）存製造商／序號等資產資訊，掛在 I2C bus；有 `at24` driver 時 `hexdump -C eeprom`，無 driver 時用 `i2ctransfer` 直讀，`ipmitool fru` 解析成人類可讀欄位 |
| [GPIO Hog](../BMC/hog.md) | 在 device tree 用 `gpio-hog` 宣告某支 GPIO 開機時即被 kernel 佔用並設固定狀態（enable／reset／power-good），早於大部分服務啟動，但被 hog 的 pin 之後不能再被別的 driver 或 user space 請求 |
| [Linux 中斷處理（Interrupt）](../BMC/interrupt.md) | IRQ 機制與 `/proc/interrupts` 觀察；top half（interrupt context、不可睡眠、只做 ack 與記錄）／bottom half（softirq／tasklet／workqueue，其中 workqueue 可睡眠）；`request_irq()` 註冊 handler 回傳 `IRQ_HANDLED`／`IRQ_NONE` |
| [I2C Hotplug](../BMC/hotplug.md) | `i2c-hotplug`：在可熱插拔裝置（模組／cable card／riser）出現或消失時，由 presence GPIO／interrupt 觸發，動態建立或移除 I2C bus 與 device node，重點是拔除時要乾淨移除避免殘留 stale 節點 |
| [MCTP](../BMC/mctp.md) | DMTF PMCI 家族的傳輸協定，用 EID 定址、與底層匯流排無關，可跑在 SMBus／I2C、PCIe VDM、USB、Serial、KCS；上層承載 PLDM、NC-SI、SPDM，OpenBMC 以 libmctp／mctpd／pldmd 實作 |
| [Schematic 判讀](../BMC/schemantic.md) | 佔位頁：i2c topology／timing／address table／tmp75 等關鍵字 |
| [Spec / Datasheet 判讀](../BMC/spec.md) | 佔位頁：tmp75／eeprom datasheet、`i2cget`、block diagram 等關鍵字 |

> 本節另有一份統整頁 `BMC/device_driver/_index.md`（Driver 與 Device Tree 關係圖、SMBus／PMBus 筆記、Linear11 浮點格式，以及 user space → PMBus core → driver `read_word_data` → I2C 的呼叫鏈）。因檔名以底線開頭、Docusaurus 不產生路由，故此處以純文字標示、不做連結。

---

## 四、感測與熱控

| 文章 | 內容 |
|---|---|
| [hwmon](../BMC/hwmon.md) | Linux hwmon 子系統以統一 sysfs（`/sys/class/hwmon/hwmonN/`、`temp1_input` 等命名慣例）暴露溫度／電壓／電流／風扇／功率；driver 註冊成 hwmon device，phosphor-hwmon 讀值轉成 D-Bus 的 `xyz.openbmc_project.Sensor.Value` |
| [Sensor Porting](../BMC/sensor_porting.md) | 佔位頁：只列 sensor porting 四環節關鍵字（hwmon → dbus-sensors → entity manager → fru device） |
| [Thermal Management](../BMC/thermal.md) | BMC 散熱管理概念：thermal zone、thermal margin vs absolute、failsafe；OpenBMC 閉迴路由 phosphor-pid-control 執行（設定多由 Entity Manager 動態提供），對外經 Redfish `Chassis/.../Thermal` 呈現 |
| [PID Control](../BMC/pid_control.md) | phosphor-pid-control 閉迴路風扇控制 daemon：PID zone、thermal PID(`temp->margin`)／fan PID(`fan->pwm`)／Stepwise 查表、failsafe，P／I／D 與 setpoint 參數，設定多由 Entity Manager 產生的 D-Bus config 載入 |

---

## 五、事件與 Log

| 文章 | 內容 |
|---|---|
| [Event Log](../BMC/event_log.md) | OpenBMC 結構化事件／錯誤紀錄：phosphor-logging 提供 D-Bus 介面（log entry 有 `Severity`／`Message`／`AdditionalData`／callout），用 `lg2`／`elog` 產生，對外經 Redfish LogService 讀取 |
| [phosphor-sel-logger](../BMC/sel_logger.md) | 專責產生 IPMI 相容的 SEL：監聽 D-Bus 事件（sensor 越限等）寫成 SEL entry，`ipmitool sel list`／`sel clear` 查詢；對比 phosphor-logging 是通用 event／error log，本服務只負責 IPMI SEL 格式 |

---

## 六、開機流程

| 文章 | 內容 |
|---|---|
| [BMC 開機流程](../BMC/bootup.md) | 精簡版三階段（bootloader／u-boot → kernel `zImage` → rootfs／systemd）說明，附 flash 多 image slot（A/B fail-safe）與 `uImage`／FIT image 補充 |
| [OpenBMC Boot Flow](../BMC/openbmc_boot_flow.md) | 最完整的一篇：從 SoC 上電、Boot ROM、U-Boot SPL／Proper、kernel、OverlayFS rootfs、systemd target 到核心服務與 Host 電源管理，含 flash layout、kernel cmdline、除錯指令與常見開機失敗原因表 |
| [Flash 燒錄](../BMC/flash.md) | 佔位頁：只有 `flashcp`／mtd devices／`flash_erase`／`nand write`／`dd`／update bmc 等關鍵字 |
| [systemd](../BMC/systemd.md) | 佔位頁：systemd／journallog／service 與 target／檔案系統路徑等關鍵字 |

---

## 七、系統服務與網路

| 文章 | 內容 |
|---|---|
| [Network（phosphor-networkd）](../BMC/network.md) | OpenBMC 網路管理服務，負責 BMC 網卡的 IP／DNS／hostname／VLAN／NTP，底層搭 systemd-networkd 的 `.network`，對外經 Redfish `EthernetInterfaces` 或 IPMI LAN channel 讀寫 |
| [NTP 時間同步](../BMC/ntp.md) | systemd-timesyncd（SNTP client）+ phosphor-time-manager；TimeSyncMethod 分 NTP／Manual，經 Redfish `Managers/bmc/NetworkProtocol` 設定；BMC 常無 RTC 電池，NTP 對 event log／SEL／憑證時間戳一致性很重要 |

---

## 八、除錯與測試

| 文章 | 內容 |
|---|---|
| [BMC 除錯手法](../BMC/debug.md) | 資源有限的兩種除錯：BMC 端跑輕量 `gdbserver` + 開發主機 cross gdb `target remote` 動態除錯；`ulimit -c unlimited` 保 coredump 後 `gdb binary core` 看 `bt`，須用未 strip 的 binary，OpenBMC 多用 systemd-coredump 收集 |
| [韌體測試流程](../BMC/testing.md) | BMC 韌體驗證三步：test plan（範圍／環境／通過標準）→ functional testing（IPMI／Redfish 回應、感測讀值、開關機／SOL／更新）→ report；並補 stress／regression／recovery 與 Robot Framework 自動化 |

---

## 九、資料中心與叢集

| 文章 | 內容 |
|---|---|
| [資料中心叢集架構](../BMC/data_center.md) | cluster 節點角色分工（headnode／compute node／storage node、job scheduler 如 Slurm/PBS）與 BMC 的關係：每個節點內建 BMC，經 out-of-band 管理網路（IPMI／Redfish）遠端開關機、監控、更新韌體 |

---

## 建議閱讀順序

**想看懂 OpenBMC 怎麼從上電跑到服務就緒：**

```
BMC 開機流程（bootup）
   → OpenBMC Boot Flow          ← 主線：上電 → U-Boot → kernel → rootfs → 服務
   → systemd                    ← init 系統與 target 啟動順序
   → Yocto Project              ← 這些服務是怎麼被 build 進 image 的
   → Redfish / IPMI             ← 開機後對外的管理介面
```

**想在 OpenBMC 上加一顆新的 sensor：**

```
Schematic 判讀（i2c topology / address table）
   → Device Tree                ← 把新裝置寫進 dts
   → Porting PMBus Driver       ← 主線：driver 落地與驗證
   → hwmon                      ← 讀值怎麼出現在 /sys/class/hwmon
   → Sensor Porting             ← hwmon → dbus-sensors → entity manager → fru
   → Entity Manager             ← 用 JSON 描述硬體、動態探測
   → PID Control / Thermal      ← 讓風扇跟著這顆 sensor 轉
```

---

## 待補主題

用第一性原理拆 BMC：它的本質是「**獨立於主機、監控與控制伺服器**的管理處理器」，心智地圖是 **監控 → 控制 → 遠端介面 → 通訊協定 → OpenBMC 軟體棧 → 韌體更新 → 安全 → RAS**。目前筆記在 **監控（sensor／thermal／power）、OpenBMC 軟體棧、管理介面** 很紮實，但往「協定現代化、更新、安全、RAS」這幾條軸線走就出現缺口。下表依重要性排序。

| 主題 | 為什麼重要 | 狀態 |
|---|---|---|
| **韌體更新流程（Redfish UpdateService／code update／A/B image）** | [Flash 燒錄](../BMC/flash.md) 只是關鍵字佔位頁，講的是 `dd`／`flashcp` 這類低階燒錄工具；[OpenBMC Boot Flow](../BMC/openbmc_boot_flow.md) 只帶到 Dual Image A/B 的存在。真正的**更新服務**——Redfish `UpdateService`、image 簽章驗證、寫入備援 slot、開機失敗自動回滾——完全沒有。這是出貨後維運最常碰的一塊 | 待補 |
| **PLDM（Platform Level Data Model）** | [MCTP](../BMC/mctp.md) 這篇把 PLDM 當成「MCTP 上承載的訊息類型」一句帶過，但 PLDM 本身的酬載——監控（Type 2）、FRU（Type 4）、firmware update（Type 5）——沒有專篇。這是逐步取代 IPMI 的現代 DMTF 協定，`pldmd` 已在 boot flow 出現卻無文章 | 待補 |
| **BMC 安全（Secure Boot for BMC／SPDM attestation／Redfish 角色權限／host-BMC 隔離）** | 全知識庫沒有一篇談 BMC 側的安全；[MCTP](../BMC/mctp.md) 僅把 SPDM 當訊息類型提一下。BMC 是伺服器最高權限的旁路處理器，一旦被攻陷等於拿下整台機器，Secure Boot、attestation、Redfish AccountService 權限模型都是空白 | 待補 |
| **KVM / 虛擬媒體（iKVM、virtual media）** | [SOL](../BMC/sol.md) 與 [Serial over LAN](../BMC/serial_over_lan.md) 只涵蓋文字序列埠 console。遠端圖形畫面重導與掛載虛擬光碟／USB（裝 OS、進 BIOS 設定）是遠端管理的另一半，目前完全沒有 | 待補 |
| **RAS / crashdump（記憶體錯誤記錄、host 當機資訊收集）** | [Event Log](../BMC/event_log.md) 與 [sel-logger](../BMC/sel_logger.md) 記的是 BMC 自己的事件，但 host CPU/記憶體的 MCA/MCE、host crashdump（透過 PECI／PLDM 收集）這類 RAS 機制沒有。資料中心靠這個判斷該不該換機器 | 待補 |
| **KCS / BT / SSIF（BIOS ↔ BMC 的 in-band host interface）** | KCS 只在 [OpenBMC Boot Flow](../BMC/openbmc_boot_flow.md) 與 [MCTP](../BMC/mctp.md) 當成 IPMI 傳輸介面之一被提到。host 端 BIOS/OS 怎麼透過 KCS／BT／SSIF 與 BMC 溝通（送 SEL、要 boot option、post 狀態）這條 in-band 通道沒有專篇 | 待補 |
| **NC-SI（BMC 與主機共用網卡的 sideband）** | [Network](../BMC/network.md) 只講 phosphor-networkd 管 IP／DNS／VLAN；[MCTP](../BMC/mctp.md) 提了「NC-SI over MCTP」一詞。但 NC-SI 本身——BMC 如何透過 sideband 共用 host 的 NIC 做管理流量、與專用管理埠的取捨——沒有文章 | 待補 |
| **POST code / 主機開機除錯（port 80 BIOS POST code 透過 BMC 讀）** | host 卡在開機時，BMC 讀 port 80／LPC/eSPI 上的 BIOS POST code 是第一線除錯手段。[SOL](../BMC/sol.md) 能看 console 輸出，但 console 還沒起來時就得靠 POST code，目前無筆記 | 待補 |
