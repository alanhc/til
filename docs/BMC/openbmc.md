# OpenBMC

**OpenBMC** 是 Linux Foundation 底下的開源 BMC 韌體專案，由 IBM、Intel、Google、Microsoft 等共同維護。它取代過去各家自行開發的封閉 BMC 韌體，提供一套可共用、可審計的基礎。

技術組成大致是：**Yocto 建置系統 + 嵌入式 Linux + systemd + D-Bus + 一群 phosphor-\* daemon**。

- 建置由 [Yocto](#yocto-建置系統) 負責。
- 服務由 [systemd](./systemd.md) 管理。
- 元件之間的溝通全走 [D-Bus](./dbus.md)。
- 對外介面是 [Redfish](#redfish) 與 [IPMI](./ipmi.md)。

> 延伸閱讀：[The overview and future of Open Source FW for server industry](https://youtu.be/cnC4zmxm5AY?si=c0G3e_4zOFUZe7g2)

## Yocto 建置系統

OpenBMC 用 **Yocto Project**（透過 `bitbake` 工具）從原始碼建出整個韌體 image。

### recipe（`.bb`）

**recipe** 是「怎麼建置某個軟體套件」的描述檔，副檔名 `.bb`（BitBake）。一份 recipe 說明：從哪裡抓原始碼、依賴什麼、怎麼設定、怎麼編、檔案要裝到哪裡。

```bitbake
SUMMARY = "My BMC daemon"
LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."

SRC_URI = "git://github.com/example/my-daemon;branch=main;protocol=https"
SRCREV = "abc123..."

DEPENDS = "sdbusplus phosphor-dbus-interfaces boost"

inherit meson pkgconfig systemd

SYSTEMD_SERVICE:${PN} = "my-daemon.service"
```

幾個關鍵變數：
- `SRC_URI` / `SRCREV`：原始碼位置與要抓的 commit。
- `DEPENDS`：**建置期**依賴（編譯時要用到的函式庫）。
- `RDEPENDS`：**執行期**依賴（跑起來才需要的東西）。
- `inherit`：套用共用的 class，`meson` 表示用 meson 建置、`systemd` 表示要註冊 systemd service。
- `${PN}`：package name，recipe 檔名去掉版本號的部分。

### bbappend（`.bbappend`）

**`.bbappend` 用來在不修改原始 recipe 的前提下，覆寫或補充它的內容**。這是 Yocto 的核心設計哲學——上游的 recipe 保持乾淨，各家的客製化放在自己的 layer 裡。

檔名必須和目標 recipe 同名（版本號可用 `%` 萬用字元）：

```
recipes-phosphor/sensors/phosphor-hwmon_%.bbappend
```

內容通常是加自己的 patch 或設定檔：

```bitbake
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://0001-my-fix.patch"
SRC_URI += "file://my-board.conf"

do_install:append() {
    install -d ${D}${datadir}/my-board
    install -m 0644 ${WORKDIR}/my-board.conf ${D}${datadir}/my-board/
}
```

**移植新板子時，九成的工作是在寫 bbappend 與新增設定檔，而不是改上游程式碼。**

### meta-layer

**layer** 是一組 recipe 的集合，目錄名慣例以 `meta-` 開頭。Layer 之間分層覆蓋，優先權由 `BBFILE_PRIORITY` 決定。

OpenBMC 的典型分層：

| Layer | 內容 |
|---|---|
| `poky/meta` | Yocto 核心，基礎系統套件 |
| `meta-openembedded` | 大量第三方套件 |
| `meta-phosphor` | OpenBMC 的核心元件（phosphor-\* 全家桶） |
| `meta-aspeed` / `meta-nuvoton` | SoC 廠支援（kernel、u-boot、SoC 專屬設定） |
| `meta-<vendor>` | 系統廠自己的 layer |
| `meta-<vendor>/meta-<board>` | 單一機種的設定 |

一個 layer 的骨架：

```
meta-myboard/
├── conf/
│   ├── layer.conf              # layer 本身的設定與優先權
│   └── machine/myboard.conf    # machine 定義：用哪顆 SoC、哪個 kernel、image 大小
├── recipes-phosphor/           # 覆寫 phosphor 元件
│   └── sensors/
│       └── phosphor-hwmon_%.bbappend
├── recipes-kernel/
│   └── linux/
│       └── linux-aspeed_%.bbappend   # kernel patch 與 device tree
└── recipes-bsp/
    └── u-boot/
```

Layer 要在 `build/conf/bblayers.conf` 裡登記才會生效。

### 建置流程與路徑

```bash
git clone https://github.com/openbmc/openbmc
cd openbmc

# 設定目標機種，會產生 build/<machine>/ 並進入該目錄
. setup <machine-name>

# 建置完整韌體 image
bitbake obmc-phosphor-image
```

建置產物與工作目錄：

| 路徑 | 內容 |
|---|---|
| `build/<machine>/tmp/deploy/images/<machine>/` | **最終 image**（`.mtd`、`.tar`、各分割檔） |
| `build/<machine>/tmp/work/<arch>/<recipe>/<version>/` | 各套件的工作目錄（解壓的原始碼、編譯中間檔） |
| `build/<machine>/tmp/work/.../image/` | 該套件「將被裝進 rootfs」的檔案樹 |
| `build/<machine>/tmp/sysroots/` | 交叉編譯用的 sysroot |
| `build/<machine>/workspace/sources/<recipe>/` | `devtool modify` 取出的可編輯原始碼 |

常用指令：

```bash
bitbake -c cleansstate <recipe>   # 清掉某套件的建置快取，強制重編
bitbake -c devshell <recipe>      # 進入該套件的建置環境，手動編譯除錯
bitbake -e <recipe> | grep ^SRC_URI=   # 看某個變數最終被解析成什麼

devtool modify linux-aspeed       # 把 kernel 原始碼取出來改（見 device_tree 頁）
devtool build linux-aspeed
devtool reset linux-aspeed
```

### rootfs 路徑與唯讀設計

OpenBMC 的 rootfs **預設是唯讀的**（`rofs`），可寫入的部分是另外一個 overlay 分割（`rwfs`）。這樣設計是為了：韌體本體不會被意外改壞、更新時只要換掉唯讀那份、斷電也不會造成檔案系統損毀。

實際影響：

- **在 BMC 上直接改 `/usr/` 底下的檔案，重開機後會消失**（或根本不允許改）。
- 需要持久化的東西放 `/var/lib/`、`/etc/`（這些在 overlay 上）。
- 開發時要臨時替換某支 binary，可以 `mount -o remount,rw /`，但這只是暫時的。

```bash
mount | grep -E 'rofs|rwfs|overlay'
df -h                              # 看 rwfs 還剩多少空間
```

flash 分割與更新方式見 [flash](./flash.md)。

## 核心元件

### phosphor-dbus-interfaces

**所有 OpenBMC D-Bus 介面的定義來源**。裡面是一堆 YAML 檔，用宣告式的方式描述每個 interface 有哪些 property / method / signal 與型別。

```yaml
# xyz/openbmc_project/Sensor/Value.interface.yaml
description: Implement to provide sensor value.
properties:
    - name: Value
      type: double
      description: The sensor value.
    - name: Unit
      type: enum[self.Unit]
      description: The unit of the sensor value.
```

建置時會自動產生 C++ binding，daemon 只要繼承產生出來的 class 並實作行為即可。**新增自訂功能的第一步就是在這裡定義介面**，這樣其他元件（含 bmcweb）才知道怎麼跟你溝通。

### entity-manager

執行期偵測硬體配置，決定要建立哪些感測器與裝置物件。讓同一份韌體能跑在多種硬體 SKU 上。詳見 [sensor_porting](./sensor_porting.md)。

### phosphor-logging

**OpenBMC 的統一日誌與錯誤記錄框架**，分兩個層次：

1. **一般 log**：透過 `lg2`（新版）或 `phosphor::logging::log()` API 寫出的訊息，最終進到 systemd journal，用 `journalctl` 讀（見 [systemd](./systemd.md)）。

   ```cpp
   lg2::error("Failed to read sensor {NAME}, rc={RC}", "NAME", name, "RC", rc);
   ```

   結構化欄位（大寫的 `NAME`、`RC`）會被 journal 記成可查詢的中繼資料，之後可以用 `journalctl NAME=inlet` 過濾。

2. **Error log / Event log**：需要被管理者看到、需要持久保存的硬體事件（感測器超標、PSU 故障、風扇停轉）。這些會：
   - 被寫入持久儲存（重開機不消失）
   - 在 D-Bus 上以 `xyz.openbmc_project.Logging.Entry` 物件呈現
   - 透過 Redfish 的 `/redfish/v1/Systems/system/LogServices/EventLog/` 對外
   - 對應到 IPMI 的 SEL（見 [ipmi](./ipmi.md)）

   ```bash
   busctl tree xyz.openbmc_project.Logging
   # 或用 Redfish 查詢
   ```

### 事件子系統

「感測器超過門檻」到「管理者收到通知」中間的流程：

```
dbus-sensors 偵測到讀值跨過 threshold
   ↓  發出 D-Bus signal（PropertiesChanged）
phosphor-logging 建立一筆 Error Log entry
   ↓
├→ 寫入持久儲存 + journal
├→ bmcweb 轉成 Redfish Event，推送給訂閱者
└→ ipmid 轉成一筆 SEL 記錄
```

關鍵在於**各元件不直接互相呼叫，而是靠 D-Bus signal 解耦**——新增一個消費者（例如把事件轉發到 Syslog server）不需要改動產生事件的那一端。

## 對外介面

### Redfish

**Redfish** 是 DMTF 制定的伺服器管理標準，用 **HTTPS + JSON + RESTful** 取代老舊的 IPMI。

特點：
- 資源以樹狀 URI 組織，每個資源是一份 JSON。
- 有正式的 schema 定義，可自我描述（`@odata.type` 標明型別）。
- 用標準的 HTTP 驗證與 TLS，安全性遠優於 IPMI。

```bash
# 服務根目錄
curl -k https://<bmc-ip>/redfish/v1/

# 取得 session token
curl -k -X POST https://<bmc-ip>/redfish/v1/SessionService/Sessions \
  -H "Content-Type: application/json" \
  -d '{"UserName":"root","Password":"0penBmc"}' -D -

# 常用資源
# /redfish/v1/Systems/system              主機資訊與電源狀態
# /redfish/v1/Chassis/                    機箱、感測器、風扇
# /redfish/v1/Managers/bmc                BMC 本身
# /redfish/v1/UpdateService               韌體更新
# /redfish/v1/Systems/system/LogServices  事件記錄
```

### bmcweb

**bmcweb** 是 OpenBMC 實作 Redfish 的 web server（C++ 寫的輕量 HTTP server）。它的角色是**翻譯層**：

```
HTTP request → bmcweb → D-Bus 查詢 → 組成 JSON → HTTP response
```

也就是說，**感測器的值並不是 bmcweb 自己讀的**，它是去 D-Bus 上跟 `dbus-sensors` 要的。這解釋了為什麼移植感測器只要做到「上 D-Bus」這一層，Redfish 就自動有了。

bmcweb 同時也提供：
- Web UI 的靜態檔案託管
- KVM（`/kvm/0`，走 WebSocket）
- 虛擬媒體
- Session / 帳號管理

### SSE（Server-Sent Events）

Redfish 事件有兩種送法：

| 方式 | 說明 |
|---|---|
| **Push（Webhook）** | BMC 主動 HTTP POST 到你註冊的 URL。需要你這端有一個對外可達的 server |
| **SSE** | 你發起一個長連線，BMC 把事件持續推過來。**不需要對外開 port** |

**SSE** 是 HTML5 的標準機制，`Content-Type: text/event-stream`，伺服器保持連線不關閉、有事件就送一段文字。相較 WebSocket 更簡單（單向、純 HTTP、自動重連）。

```bash
curl -k -N -u root:0penBmc \
  https://<bmc-ip>/redfish/v1/EventService/SSE
```

連上之後就會持續收到事件：

```
id: 1
data: {"@odata.type":"#Event.v1_4_0.Event","Events":[{...}]}
```

適合的場景是監控端在 NAT 後面、或不想為了收事件而開一個對外服務。

## 參考

- [OpenBMC 官方 repo](https://github.com/openbmc/openbmc)
- [OpenBMC docs](https://github.com/openbmc/docs)
- [bmcweb](https://github.com/openbmc/bmcweb)
- [Redfish Specification（DMTF）](https://www.dmtf.org/standards/redfish)
- [Yocto Project Reference Manual](https://docs.yoctoproject.org/ref-manual/index.html)
