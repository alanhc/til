# Telemetry、OpenTelemetry、BMC 與 Grafana/Loki 的關係

> 一句話總結：**Telemetry 是資料本身；OpenTelemetry 是收集與傳輸的標準和工具；BMC 是硬體層的資料來源之一；Loki / Prometheus / Tempo 負責存，Grafana 負責看。**

---

## 1. Telemetry 是什麼

Telemetry（遙測）原意是「在遠端量測，把資料傳回來分析」。在電腦系統中，它指**把系統運作狀態收集起來，送到別處儲存與分析**。

軟體 observability 一般把 telemetry 分成三類訊號，近年再加上 profiles：[^3]

```mermaid
flowchart TB
    T["Telemetry 遙測資料"]
    T --> M["Metrics 指標<br/>數值時間序列<br/>例：CPU%、QPS、溫度"]
    T --> L["Logs 日誌<br/>帶時間戳的事件文字<br/>例：error、kernel log、SEL"]
    T --> TR["Traces 追蹤<br/>一個 request 跨服務的路徑與耗時<br/>由多個 span 組成"]
    T --> P["Profiles 剖析<br/>CPU / memory 熱點<br/>（第四類訊號）"]
```

三者各自回答的問題不同：

| 訊號 | 回答的問題 | 特性 |
|---|---|---|
| Metrics | 「有沒有出問題？多嚴重？」 | 便宜、可聚合、適合告警 |
| Logs | 「發生了什麼事？」 | 細節多、量大、較貴 |
| Traces | 「慢在哪一段？」 | 跨服務因果關係 |

### Trace 的樣子

一個 request 經過多個服務，每一段就是一個 span：

```mermaid
gantt
    title 一個 HTTP request 的 trace（示意）
    dateFormat X
    axisFormat %L ms
    section api-gateway
    GET /order          :0, 120
    section order-svc
    createOrder         :10, 100
    section inventory-svc
    checkStock          :20, 50
    section db
    SELECT stock        :25, 45
    section payment-svc
    charge              :55, 95
```

---

## 2. OpenTelemetry 是什麼

OpenTelemetry（OTel）是 CNCF 專案，2019 年由 **OpenTracing + OpenCensus** 合併而成。[^1][^2] 它的目標是**統一 telemetry 的產生與傳輸標準**，避免被特定廠商綁住；儲存與視覺化則刻意留給其他工具。[^1]

```mermaid
flowchart LR
    OT1["OpenTracing"] --> OTEL["OpenTelemetry<br/>(2019, CNCF)"]
    OC["OpenCensus"] --> OTEL
```

### OTel 的組成

```mermaid
flowchart TB
    subgraph OTEL["OpenTelemetry 專案"]
        API["API / SDK<br/>各語言函式庫，讓程式產生訊號"]
        OTLP["OTLP 協定<br/>gRPC / HTTP + protobuf"]
        COL["Collector<br/>receivers → processors → exporters"]
        SEM["Semantic Conventions<br/>service.name、host.name ..."]
    end
    NOT["❌ 不負責：儲存、視覺化"]
    OTEL -.-> NOT
```

### Collector 內部 pipeline

Collector 是整個 OTel 生態裡最實用的元件，可以把它想成 telemetry 的路由器：[^4]

```mermaid
flowchart LR
    subgraph R["Receivers 接收"]
        r1["otlp"]
        r2["prometheus（抓取）"]
        r3["syslog"]
        r4["filelog"]
    end
    subgraph P["Processors 加工"]
        p1["batch"]
        p2["attributes / resource<br/>加標籤、改名"]
        p3["filter<br/>丟掉雜訊"]
        p4["memory_limiter"]
    end
    subgraph E["Exporters 輸出"]
        e1["otlp → Tempo"]
        e2["prometheusremotewrite → Mimir"]
        e3["otlphttp → Loki"]
        e4["其他商用後端"]
    end
    R --> P --> E
```

送進 Loki 用的是 `otlphttp`：Loki 3.0 起原生接收 OTLP，[^10] 早期專用的 `loki` exporter 在 2024 年 7 月標為 deprecated，並已在 Collector contrib v0.131.0 移除。[^9]

**比喻：** OTel 定義了水管與插頭的規格。下游接什麼水庫（Loki、Prometheus）、用什麼儀表（Grafana），都可以自由替換。

---

## 3. 跟 BMC 的關係

BMC 是一個**硬體層、out-of-band 的 telemetry 來源**。即使 host OS 當機或還沒開機，BMC 仍然能回報狀態。

### In-band 與 Out-of-band

```mermaid
flowchart TB
    subgraph SERVER["一台伺服器"]
        subgraph HOST["Host（In-band）"]
            APP["應用程式<br/>OTel SDK"]
            OS["Linux<br/>node_exporter / journald"]
        end
        subgraph BMC["BMC（Out-of-band）"]
            SENS["Sensors<br/>溫度/電壓/風扇/功耗"]
            SEL["SEL / Event Log"]
            RF["Redfish / IPMI"]
        end
        HW["CPU、DIMM、PSU、Fan、NIC ..."]
    end
    HW -- "I2C / PMBus / PECI / GPIO" --> SENS
    HW -- "錯誤事件" --> SEL
    SENS --> RF
    SEL --> RF
    HOST -- "資料網路" --> NET1(("生產網路"))
    RF -- "獨立管理網口" --> NET2(("管理網路"))
```

|  | In-band（Host 端） | Out-of-band（BMC） |
|---|---|---|
| 典型工具 | OTel SDK、node_exporter | Redfish、IPMI |
| 資料 | 應用效能、OS 資源 | 溫度、電源、風扇、硬體錯誤 |
| Host 當機時 | ❌ 看不到 | ✅ 仍可回報 |
| 誕生背景 | 雲原生 / 微服務 | 伺服器硬體管理 |

### OpenBMC 內部的 telemetry 資料流

圖中的 sensor、telemetry daemon 與 Redfish 服務都是 OpenBMC 的上游元件。[^6][^7][^8]

```mermaid
flowchart LR
    subgraph HW["硬體"]
        hwmon["hwmon / I2C 裝置"]
    end
    subgraph BMC["OpenBMC"]
        ds["dbus-sensors /<br/>phosphor-hwmon"]
        dbus[("D-Bus<br/>xyz.openbmc_project.Sensor.Value")]
        tel["telemetry daemon<br/>xyz.openbmc_project.Telemetry"]
        plog["phosphor-logging"]
        jr["journald"]
        rsys["rsyslog"]
        web["bmcweb"]
    end
    hwmon --> ds --> dbus
    dbus --> tel
    dbus --> web
    tel --> web
    plog --> jr --> rsys
    web -- "Redfish API" --> OUT1(["外部抓取 / 訂閱"])
    rsys -- "remote syslog" --> OUT2(["外部 log server"])
```

### Redfish TelemetryService 資源結構

資源名稱依 DMTF 的 TelemetryService schema。[^5]

```mermaid
flowchart TB
    root["/redfish/v1/TelemetryService"]
    root --> MD["MetricDefinitions<br/>「有哪些 metric 可以收」"]
    root --> MRD["MetricReportDefinitions<br/>「要收哪些、多久收一次」"]
    root --> MR["MetricReports<br/>「實際產生的報表」"]
    root --> TG["Triggers<br/>「超過門檻時觸發」"]
    MRD -- "產生" --> MR
```

### Pull 與 Push 兩種取得方式

```mermaid
sequenceDiagram
    participant C as Collector / Exporter
    participant B as BMC (bmcweb)

    Note over C,B: 方式一：Pull（輪詢）
    loop 每 30 秒
        C->>B: GET /redfish/v1/Chassis/.../Sensors
        B-->>C: 溫度、電壓、風扇數值
    end

    Note over C,B: 方式二：Push（訂閱）
    C->>B: POST /redfish/v1/EventService/Subscriptions<br/>(或開 SSE 連線)
    B-->>C: 201 Created
    loop 每當產生 MetricReport / Event
        B-)C: 推送 MetricReport / Event
    end
```

---

## 4. Grafana、Loki 這些是什麼

它們是**後端儲存與視覺化**，位於 OTel 水管的下游。Grafana Labs 的整套工具常被稱為 **LGTM stack**：

```mermaid
flowchart TB
    subgraph LGTM["Grafana LGTM Stack"]
        L["<b>L</b>oki<br/>存 Logs<br/>查詢：LogQL"]
        G["<b>G</b>rafana<br/>UI / 儀表板 / 告警<br/>本身不存資料"]
        T["<b>T</b>empo<br/>存 Traces<br/>查詢：TraceQL"]
        M["<b>M</b>imir（或 Prometheus）<br/>存 Metrics<br/>查詢：PromQL"]
    end
    A["Alloy<br/>Grafana 的 collector<br/>（OTel Collector 發行版）"]
    A --> L & T & M
    L & T & M --> G
```

### Loki 為什麼便宜：只對 label 建索引

```mermaid
flowchart LR
    subgraph IDX["Index（很小）"]
        s1["{job=bmc, host=node01}"]
        s2["{job=bmc, host=node02}"]
        s3["{job=app, svc=order}"]
    end
    subgraph CH["Chunks（壓縮後放在 object storage）"]
        c1["原始 log 文字 ..."]
        c2["原始 log 文字 ..."]
        c3["原始 log 文字 ..."]
    end
    s1 --> c1
    s2 --> c2
    s3 --> c3
```

- **Elasticsearch**：對每個字建全文索引，查詢快，但儲存與運算都貴。
- **Loki**：log 內容本身不建索引，只用 label 找到 stream，再對 chunk 做 grep 式掃描。[^11]這種做法便宜，但 label 要設計好。高基數的欄位（如 request_id）不要放進 label。[^12]

---

## 5. 全部串起來：資料中心的整體架構

```mermaid
flowchart LR
    subgraph SRC["資料來源"]
        APP["應用程式<br/>(OTel SDK)"]
        NODE["Host<br/>node_exporter / journald"]
        BMCM["BMC Sensors<br/>(Redfish / IPMI)"]
        BMCL["BMC SEL / journal<br/>(rsyslog 轉發)"]
    end

    subgraph BRIDGE["轉接層"]
        RE["redfish_exporter /<br/>ipmi_exporter"]
    end

    subgraph COLL["收集層"]
        OC["OTel Collector / Alloy"]
    end

    subgraph STORE["儲存層"]
        MIM[("Prometheus / Mimir<br/>metrics")]
        LOKI[("Loki<br/>logs")]
        TEMPO[("Tempo<br/>traces")]
    end

    GRAF["Grafana<br/>儀表板 + 告警"]

    APP -- "OTLP" --> OC
    NODE -- "Prometheus 格式" --> OC
    BMCM --> RE -- "Prometheus 格式" --> OC
    BMCL -- "syslog" --> OC

    OC --> MIM
    OC --> LOKI
    OC --> TEMPO

    MIM --> GRAF
    LOKI --> GRAF
    TEMPO --> GRAF
```

### 分層對照

| 層 | 做什麼 | 代表 |
|---|---|---|
| 來源 | 產生 telemetry | 應用程式、Linux、**BMC** |
| 標準 / 傳輸 | 定義格式、搬運 | **OpenTelemetry**（SDK、OTLP、Collector） |
| 儲存 | 存與查詢 | Prometheus/Mimir、**Loki**、Tempo |
| 視覺化 | 看、告警 | **Grafana** |

---

## 6. 實際情境：把軟體和硬體資料關聯起來

同時收集 in-band 與 out-of-band 資料，價值在於能**跨層找出根因**：

```mermaid
sequenceDiagram
    participant U as 使用者
    participant G as Grafana
    participant T as Tempo
    participant M as Mimir
    participant L as Loki

    U->>G: 告警：order-svc p99 延遲飆高
    G->>T: 查 trace
    T-->>G: 慢的 span 都集中在 node07
    G->>M: 查 node07 的 metrics
    M-->>G: CPU 頻率下降<br/>BMC 回報 CPU 溫度 95°C
    G->>L: 查 node07 的 BMC log
    L-->>G: SEL：Fan2 轉速過低 / Fan failure
    Note over U,L: 根因：風扇故障 → 過熱 → CPU 降頻 → 服務變慢
```

如果只有 host 端的 OTel 資料，只能看到「node07 變慢」。加上 BMC 的 telemetry，才能一路追到「風扇壞了」。

---

## 7. 名詞速查

| 名詞 | 一句話 |
|---|---|
| Telemetry | 從系統收集回來的狀態資料（metrics / logs / traces / profiles） |
| Observability | 能從外部訊號推斷系統內部狀態的能力 |
| OpenTelemetry | 產生與傳輸 telemetry 的開放標準和工具 |
| OTLP | OTel 的傳輸協定 |
| OTel Collector | 接收、加工、轉送 telemetry 的 agent / gateway |
| BMC | 伺服器上獨立的管理控制器，提供 out-of-band 硬體遙測 |
| Redfish TelemetryService | Redfish 定義的 metric 報表與訂閱機制 |
| SEL | System Event Log，BMC 記錄的硬體事件 |
| Prometheus / Mimir | metrics 資料庫（Mimir 是可水平擴展的版本） |
| Loki | 只索引 label 的 log 資料庫 |
| Tempo | trace 資料庫 |
| Grafana | 視覺化與告警 UI，本身不存資料 |
| Alloy | Grafana 版的 OTel Collector[^13] |

## 參考資料

[^1]: OpenTelemetry, *What is OpenTelemetry?*（History 一節）. [https://opentelemetry.io/docs/what-is-opentelemetry/](https://opentelemetry.io/docs/what-is-opentelemetry/)
[^2]: CNCF, *A Brief History of OpenTelemetry (So Far)*, 2019-05-21. [https://www.cncf.io/blog/2019/05/21/a-brief-history-of-opentelemetry-so-far/](https://www.cncf.io/blog/2019/05/21/a-brief-history-of-opentelemetry-so-far/)
[^3]: OpenTelemetry Blog, *OpenTelemetry announces support for profiling*, 2024-03-19. [https://opentelemetry.io/blog/2024/profiling/](https://opentelemetry.io/blog/2024/profiling/)
[^4]: OpenTelemetry, *Collector Architecture*. [https://opentelemetry.io/docs/collector/architecture/](https://opentelemetry.io/docs/collector/architecture/)
[^5]: DMTF Redfish, *TelemetryService* schema. [https://redfish.dmtf.org/schemas/v1/TelemetryService.json](https://redfish.dmtf.org/schemas/v1/TelemetryService.json)
[^6]: openbmc/dbus-sensors. [https://github.com/openbmc/dbus-sensors](https://github.com/openbmc/dbus-sensors)
[^7]: openbmc/telemetry. [https://github.com/openbmc/telemetry](https://github.com/openbmc/telemetry)
[^8]: openbmc/bmcweb. [https://github.com/openbmc/bmcweb](https://github.com/openbmc/bmcweb)
[^9]: opentelemetry-collector-contrib, *CHANGELOG*（v0.131.0：移除 Loki Exporter）. [https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/CHANGELOG.md](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/CHANGELOG.md)
[^10]: Grafana Loki, *How is native OTLP endpoint different from Loki Exporter*. [https://grafana.com/docs/loki/latest/send-data/otel/native_otlp_vs_loki_exporter/](https://grafana.com/docs/loki/latest/send-data/otel/native_otlp_vs_loki_exporter/)
[^11]: Grafana Loki, *Understand labels*. [https://grafana.com/docs/loki/latest/get-started/labels/](https://grafana.com/docs/loki/latest/get-started/labels/)
[^12]: Grafana Loki, *Label best practices*. [https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/](https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/)
[^13]: Grafana Alloy, *Introduction*. [https://grafana.com/docs/alloy/latest/introduction/](https://grafana.com/docs/alloy/latest/introduction/)
