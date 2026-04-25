---
title: OpenBMC Boot Flow
sidebar_position: 2
---

# OpenBMC Boot Flow（開機流程）

OpenBMC 是由 Linux Foundation 主導的開源 BMC（Baseboard Management Controller）韌體專案，廣泛應用於伺服器管理晶片（如 ASPEED AST2500/AST2600、Nuvoton NPCM）。本文整理完整的 OpenBMC 開機流程，從硬體上電到服務就緒。

## 整體流程概覽

```
BMC SoC Power On
      │
      ▼
Boot ROM（內建於 SoC）
      │
      ▼
U-Boot SPL（Secondary Program Loader）
      │   載入至 SRAM
      ▼
U-Boot Proper
      │   初始化 DRAM、Flash、網路
      ▼
Linux Kernel（zImage / uImage）
      │   載入 Device Tree Blob（DTB）
      ▼
initramfs（可選）
      │
      ▼
OpenBMC RootFS（Yocto 建置）
      │
      ▼
systemd（PID 1）
      │
      ├─► phosphor-* 服務群
      ├─► bmcweb（Redfish / Web UI）
      ├─► ipmid（IPMI）
      ├─► obmc-console（SOL）
      └─► Entity Manager / Sensor / Logging...
```

---

## 1. BMC SoC Power On

### 說明
伺服器主機板上的 BMC 晶片（如 **ASPEED AST2600**）通常比 Host CPU 更早上電，即使主機板處於待機狀態（Standby Power）時 BMC 已運行。

### 上電時序
```
主機板插上 AC 電源
   │
   ▼
ATX 電源輸出 +5VSB（待機電壓）
   │
   ▼
BMC SoC 上電
   │
   ▼
Host CPU 仍處於 Power Off 狀態
```

- BMC 的責任之一是管理 Host 的開機流程（透過 IPMI / Redfish）
- BMC 本身的 Boot 與 Host BIOS/UEFI 的 Boot 是**相互獨立**的兩條路徑

---

## 2. Boot ROM（WDT / Chip ROM）

### 說明
BMC SoC 內建一段**不可修改的 Boot ROM**，CPU Reset 後從固定位址開始執行。

以 ASPEED AST2600 為例：
- CPU 核心：ARM Cortex-A7（雙核）
- Reset vector：`0x00000000`（映射至內部 SRAM 或 Boot ROM）

### 主要工作
- 初始化最基本的時鐘、SRAM
- 決定 Boot Source：
  - **SPI Flash**（最常見，儲存 U-Boot）
  - UART / USB（韌體回復模式）
- 將 U-Boot SPL 從 SPI Flash 複製到內部 SRAM 執行

### ASPEED 特有機制
```
SCU（System Control Unit）暫存器
   │
   ├─ 決定 Boot Strap（開機引腳配置）
   └─ 可設定 Boot from SPI / UART / eMMC
```

---

## 3. U-Boot SPL（Secondary Program Loader）

### 說明
由於 SoC 剛上電時只有內部 SRAM 可用（通常 64KB ~ 256KB），無法容納完整的 U-Boot，因此需要一個輕量級的 **SPL** 先行初始化 DRAM。

### 主要工作
- 初始化 **DRAM Controller**（DDR4 training）
- 從 SPI Flash 載入 **U-Boot Proper** 到 DRAM
- 跳轉至 U-Boot Proper 執行

### Flash Layout（典型 OpenBMC）
```
SPI Flash（通常 128MB）
┌──────────────────────────────────┐  0x00000000
│  U-Boot SPL                      │  ~64KB
├──────────────────────────────────┤  0x00010000
│  U-Boot Proper                    │  ~512KB
├──────────────────────────────────┤  0x00090000
│  U-Boot Env（環境變數）           │  ~64KB
├──────────────────────────────────┤  0x000A0000
│  Linux Kernel（FIT Image）        │  ~8MB
├──────────────────────────────────┤  0x00900000
│  RootFS（SquashFS / UBIFS）       │  剩餘空間
└──────────────────────────────────┘
```

---

## 4. U-Boot Proper

### 說明
U-Boot 是 OpenBMC 中最常用的 Bootloader，負責初始化周邊並載入 Linux Kernel。

### 主要工作
1. **硬體初始化**：網路（NCSI/RGMII）、USB、I2C、SPI、GPIO
2. **讀取環境變數**（`bootcmd`、`bootargs`）
3. **載入 Kernel**：從 SPI Flash 讀取 FIT Image（Flattened Image Tree）
4. **傳遞 Device Tree**（DTB）給 Kernel
5. **設定 Kernel cmdline**：掛載 RootFS 位置、console 設定

### FIT Image（uImage.bin）
OpenBMC 使用 FIT Image 將多個元件打包：
```
FIT Image
├── Linux Kernel（zImage / uImage）
├── Device Tree Blob（.dtb）
└── initramfs（可選）
```

### 典型 bootcmd
```bash
# U-Boot 環境變數中的 bootcmd
bootcmd=run flashboot

flashboot=
  sf probe &&
  sf read ${loadaddr} ${kernel_addr} ${kernel_size} &&
  bootm ${loadaddr}
```

### Dual Flash / Dual Image（備援機制）
部分平台支援 A/B Image 切換：
```
Flash A (Primary)  ←── 正常使用
Flash B (Backup)   ←── OTA 更新或 Flash A 損壞時切換
```
U-Boot 可透過讀取 GPIO 或環境變數決定從哪個 Image 開機。

---

## 5. Linux Kernel 初始化

### 說明
U-Boot 將 Kernel 載入至 DRAM 後跳轉執行，Linux 開始初始化。

### BMC 常見 SoC 對應的 Kernel 配置

| SoC | 架構 | Kernel 版本（OpenBMC 主線） |
|---|---|---|
| ASPEED AST2500 | ARM Cortex-A7 | 6.x |
| ASPEED AST2600 | ARM Cortex-A7 (Dual) | 6.x |
| Nuvoton NPCM750 | ARM Cortex-A9 | 6.x |
| Nuvoton NPCM845 | ARM Cortex-A35 | 6.x |

### 主要工作
1. **解壓縮 zImage**（自解壓）
2. **讀取 DTB**：識別硬體（I2C 裝置、GPIO、PWM 風扇...）
3. **初始化驅動**：
   - `aspeed-i2c`：I2C bus 驅動
   - `aspeed-adc`：電壓感測器
   - `pwm-fan`：風扇控制
   - `aspeed-vuart`：Virtual UART（SOL 用）
4. **掛載 RootFS**：從 MTD 裝置掛載 SquashFS
5. **啟動 init**：執行 `/sbin/init`（systemd）

### 重要 Kernel cmdline 參數
```bash
console=ttyS4,115200n8        # UART console
rootfstype=squashfs           # RootFS 格式
root=/dev/mtdblock4           # RootFS 所在 MTD partition
rw                            # 可讀寫（overlay 掛載）
```

---

## 6. OpenBMC RootFS（Yocto 建置）

### 說明
OpenBMC 的 RootFS 由 **Yocto Project** 建置，以 `SquashFS`（唯讀）搭配 `UBIFS` 或 `OverlayFS`（可讀寫層）的方式運行。

### 目錄結構（簡化）
```
/
├── bin/         ← BusyBox 等基本工具
├── etc/
│   └── systemd/ ← service unit 設定
├── lib/
│   └── systemd/system/   ← 系統 service 檔案
├── usr/
│   ├── bin/     ← phosphor-*, bmcweb, ipmid...
│   └── lib/     ← 共用函式庫（D-Bus, Boost...）
├── run/         ← 執行期 socket、pid 檔
└── var/         ← 日誌、持久化設定（overlay 層）
```

### OverlayFS 機制
```
SquashFS（唯讀，在 Flash 上）
      +
UBIFS / tmpfs（可讀寫層）
      │
      ▼
OverlayFS（對上層呈現統一的可讀寫視圖）
```
- 韌體更新不影響使用者設定（存在可讀寫層）
- 工廠重置 = 清除可讀寫層

---

## 7. systemd 啟動流程

### 說明
OpenBMC 使用 **systemd** 作為 init 系統（PID 1），管理所有服務的啟動順序與相依關係。

### 關鍵 systemd target 順序

```
sysinit.target
      │
      ▼
basic.target
      │
      ▼
network.target
      │
      ├─► obmc-chassis-poweroff@0.target（初始電源狀態）
      │
      ▼
multi-user.target
      │
      ├─► bmcweb.service
      ├─► ipmid.service
      ├─► phosphor-log-manager.service
      ├─► phosphor-inventory-manager.service
      ├─► entity-manager.service
      ├─► phosphor-fan-presence.service
      └─► ...其他服務
```

### OpenBMC 特有 target
```
obmc-standby.target       ← BMC 準備就緒，Host 仍關機
obmc-chassis-on@0.target  ← Host 正在開機
obmc-host-on@0.target     ← Host 開機完成
obmc-host-off@0.target    ← Host 關機
```

---

## 8. 核心 OpenBMC 服務

### 服務架構（D-Bus 為核心）

```
┌─────────────────────────────────────────────────────┐
│                   D-Bus Message Bus                  │
│              (dbus-broker / dbus-daemon)             │
└──────┬──────┬──────┬──────┬──────┬──────┬──────────┘
       │      │      │      │      │      │
  bmcweb  ipmid entity  phosphor  pldmd  obmc-
              manager  -sensor-   ...   console
                       svc
```

### 主要服務說明

| 服務 | 功能 |
|---|---|
| **bmcweb** | Redfish API + Web UI，提供 HTTP/HTTPS 管理介面 |
| **ipmid** | IPMI 協定處理（KCS / LAN channel） |
| **phosphor-sensor-svcs** | 感測器讀值（溫度、電壓、風扇轉速） |
| **entity-manager** | 解析 JSON 設定檔，動態產生硬體 D-Bus 物件 |
| **phosphor-log-manager** | 系統事件記錄（SEL / Event Log） |
| **phosphor-fan-presence** | 風扇存在偵測與轉速控制 |
| **phosphor-hwmon** | 透過 hwmon sysfs 介面讀取感測器 |
| **obmc-console** | Serial Over LAN（SOL）console 轉發 |
| **pldmd** | PLDM over MCTP 協定支援 |
| **mctpd** | MCTP 傳輸層管理 |

---

## 9. 感測器與硬體偵測流程

```
Device Tree / JSON Configuration
      │
      ▼
Entity Manager
      │  解析 /etc/default/obmc/hwmon/*.json
      ▼
D-Bus 物件建立
(xyz.openbmc_project.Sensor.Value)
      │
      ▼
phosphor-hwmon / hwmon-svc
      │  讀取 /sys/class/hwmon/hwmon*/
      ▼
感測器數值更新至 D-Bus
      │
      ├─► bmcweb 透過 D-Bus 提供 Redfish /redfish/v1/Chassis/.../Sensors
      └─► ipmid 透過 D-Bus 提供 IPMI SDR / Sensor Reading
```

---

## 10. Host 開機管理

BMC 就緒後，負責管理 Host 的電源狀態：

```
Redfish POST /redfish/v1/Systems/system/Actions/ComputerSystem.Reset
    或
IPMI Chassis Control Command
      │
      ▼
phosphor-state-manager
      │
      ▼
GPIO 控制 PWRON#（電源按鈕訊號）
      │
      ▼
Host CPU 上電 → BIOS/UEFI → OS 開機
```

---

## 常見除錯方法

### 查看開機 log
```bash
# 透過 SOL (Serial Over LAN) 查看 BMC 開機訊息
ipmitool -I lanplus -H <BMC_IP> -U admin -P password sol activate

# SSH 進入 BMC 後查看 journald log
journalctl -b               # 本次開機所有 log
journalctl -u bmcweb        # 特定服務 log
journalctl -f               # 即時追蹤

# 查看 kernel log
dmesg | grep -i "i2c\|aspeed\|sensor"

# 查看 systemd 服務狀態
systemctl list-units --failed   # 列出失敗的服務
systemctl status entity-manager
```

### 查看感測器與 D-Bus
```bash
# 列出所有 D-Bus 物件（感測器）
busctl tree xyz.openbmc_project.HwmonTempSensor

# 讀取特定感測器數值
busctl get-property xyz.openbmc_project.HwmonTempSensor \
  /xyz/openbmc_project/sensors/temperature/CPU_Temp \
  xyz.openbmc_project.Sensor.Value Value

# 列出所有服務
systemctl list-units "phosphor*" "obmc*" "bmcweb*"
```

### 常見開機失敗原因

| 現象 | 可能原因 |
|---|---|
| U-Boot 無輸出 | SPI Flash 損壞、Boot ROM 無法讀取 SPL |
| Kernel panic | DTB 錯誤、RootFS 損壞、MTD partition 錯誤 |
| bmcweb 無法連線 | 網路設定錯誤、憑證問題、服務啟動失敗 |
| 感測器無數據 | entity-manager 設定檔錯誤、I2C 裝置無回應 |
| IPMI 無回應 | ipmid 服務崩潰、KCS 驅動問題 |

---

## BMC Boot vs Host Boot 關係

```
時間軸 →
────────────────────────────────────────────────────────────▶

BMC:  [ROM]──[U-Boot]──[Kernel]──[systemd]──[服務就緒]──────── 持續運行
                                                  │
                                                  │ 等待 Power On 指令
                                                  ▼
Host:                                      [BIOS/UEFI]──[OS]── 持續運行
```

- BMC 通常在 Host 開機前 **數秒到數十秒** 先完成啟動
- OpenBMC 可設定 **Power Restore Policy**：
  - `AlwaysOff`：BMC 就緒後 Host 保持關機
  - `AlwaysOn`：BMC 就緒後自動開啟 Host
  - `LastState`：恢復斷電前的狀態

---

## 參考資料

- [OpenBMC GitHub](https://github.com/openbmc/openbmc)
- [OpenBMC Documentation](https://github.com/openbmc/docs)
- [ASPEED AST2600 Datasheet](https://www.aspeedtech.com/server_bmc/)
- [Phosphor D-Bus Interfaces](https://github.com/openbmc/phosphor-dbus-interfaces)
- [OpenBMC Architecture Overview](https://github.com/openbmc/docs/blob/master/architecture/openbmc-architecture.md)
- [Yocto Project](https://www.yoctoproject.org/)
