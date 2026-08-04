# D-Bus

**D-Bus** 是 Linux 上的行程間通訊（IPC）機制。OpenBMC 把它當成整個系統的骨幹：感測器讀值、電源狀態、韌體版本、事件記錄……各個 daemon 都把資料掛在 D-Bus 上，彼此透過 D-Bus 互相查詢與呼叫，而不是各自開 socket 或寫檔案。

理解 OpenBMC 的第一步，就是能用 `busctl` 把 D-Bus 上的東西翻出來看。

## 四個核心概念

D-Bus 的定址方式很像檔案系統加上物件導向，由外而內是四層：

| 名詞 | 說明 | 範例 |
|---|---|---|
| **service**（bus name） | 一支行程在 bus 上註冊的名字，代表「誰提供這些資料」 | `xyz.openbmc_project.Sensor.Monitor` |
| **object**（object path） | 該 service 底下的一個節點，路徑形式，代表「哪個東西」 | `/xyz/openbmc_project/sensors/temperature/inlet` |
| **interface** | 掛在 object 上的一組能力宣告，代表「這東西會什麼」 | `xyz.openbmc_project.Sensor.Value` |
| **member** | interface 裡的實際成員，分三種 | 見下 |

member 又分三類：

- **property（屬性）**：可讀（有時可寫）的狀態值，例如 `Value`（感測器當前讀值）、`Unit`（單位）。
- **method（方法）**：可被呼叫的函式，例如 `Reset()`、`SetPowerState()`。呼叫端會等回傳。
- **signal（訊號）**：由擁有者主動廣播的事件通知，訂閱者收到後自行處理，例如 `PropertiesChanged`（屬性變動時發出）、`InterfacesAdded`（新裝置出現）。

一句話串起來：**某個 service 在某個 object path 上，實作了某個 interface，interface 裡有 property / method / signal**。

## system bus 與 session bus

- **system bus**：全機唯一，跑系統服務用，需要 policy 授權才能存取。BMC 上用的都是這條。
- **session bus**：每個桌面登入 session 一條，桌面應用程式在用，BMC 上通常不會遇到。

`busctl` 預設操作 system bus，所以 BMC 上直接下指令即可。

## busctl 工具

`busctl` 是 systemd 提供的 D-Bus 檢視/操作工具，是 BMC 上除錯的第一把刀。

### 列出所有 service

```bash
busctl list
```

會看到一整排 `xyz.openbmc_project.*` 的服務名稱，每個對應一支 daemon。

### busctl tree — 看某個 service 的物件樹

```bash
busctl tree xyz.openbmc_project.Sensor.Monitor
```

輸出是樹狀的 object path，讓你知道這支服務底下掛了哪些東西：

```
└─ /xyz
  └─ /xyz/openbmc_project
    └─ /xyz/openbmc_project/sensors
      ├─ /xyz/openbmc_project/sensors/temperature
      │ └─ /xyz/openbmc_project/sensors/temperature/inlet
      └─ /xyz/openbmc_project/sensors/fan_tach
```

### busctl introspect — 看某個 object 有什麼

```bash
busctl introspect xyz.openbmc_project.Sensor.Monitor \
  /xyz/openbmc_project/sensors/temperature/inlet
```

輸出會列出這個 object 上所有 interface，以及每個 interface 裡的 property / method / signal、型別、是否可寫：

```
NAME                                TYPE      SIGNATURE  RESULT/VALUE  FLAGS
xyz.openbmc_project.Sensor.Value    interface -          -             -
.MaxValue                           property  d          127           emits-change
.MinValue                           property  d          -128          emits-change
.Unit                               property  s          "xyz.open..." emits-change
.Value                              property  d          42.5          emits-change writable
```

`introspect` 是最重要的一個指令——**不確定某個東西怎麼用時，就 introspect 它**。

### busctl get-property / set-property — 讀寫屬性

```bash
busctl get-property xyz.openbmc_project.Sensor.Monitor \
  /xyz/openbmc_project/sensors/temperature/inlet \
  xyz.openbmc_project.Sensor.Value Value
# d 42.5
```

### busctl call — 呼叫方法

```bash
busctl call SERVICE OBJECT_PATH INTERFACE METHOD SIGNATURE ARGS...
```

`SIGNATURE` 是參數的型別字串（D-Bus type signature），常見代碼：

| 代碼 | 型別 |
|---|---|
| `s` | string |
| `b` | boolean |
| `i` / `u` | int32 / uint32 |
| `d` | double |
| `a` | array（後接元素型別，如 `as` = string 陣列） |
| `v` | variant（任意型別） |

無參數時 signature 給空字串。下面這個例子呼叫標準的 `org.freedesktop.DBus.Properties` 介面的 `Get` 方法，簽章 `ss` 代表兩個 string 參數：

```bash
busctl call xyz.openbmc_project.State.BMC \
  /xyz/openbmc_project/state/bmc0 \
  org.freedesktop.DBus.Properties Get ss \
  xyz.openbmc_project.State.BMC CurrentBMCState
```

### busctl monitor — 即時觀察

```bash
busctl monitor xyz.openbmc_project.Sensor.Monitor
```

即時印出該服務收發的所有訊息，適合觀察 signal 何時被發出。

## 建立自己的 D-Bus service

在 OpenBMC 上寫一支新的 daemon 並掛上 D-Bus，大致要做四件事：

1. **定義 interface**：在 `phosphor-dbus-interfaces` 這個 repo 裡以 YAML 描述你的 interface（有哪些 property/method/signal、型別為何）。build 時會自動產生 C++ binding 程式碼。
2. **實作**：用 `sdbusplus`（OpenBMC 對 systemd `sd-bus` 的 C++ 封裝）繼承產生出來的 binding class，實作 method 的行為。
3. **註冊**：程式啟動時 `request_name()` 取得 bus name，再把 object 加到指定的 object path 上。
4. **打包**：寫一份 systemd service 檔讓它開機自動啟動（見 [systemd](./systemd.md)），並在 Yocto recipe 裡加入編譯規則（見 [openbmc](./openbmc.md)）。

命名慣例上，OpenBMC 的所有 interface 都以 `xyz.openbmc_project.` 為前綴，object path 則是把它換成斜線形式。

## 參考

- [D-Bus Specification](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [OpenBMC — phosphor-dbus-interfaces](https://github.com/openbmc/phosphor-dbus-interfaces)
- [sdbusplus](https://github.com/openbmc/sdbusplus)
