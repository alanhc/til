# 為何 Hermes 架設在 Kubernetes 是較佳的安全框架

## 摘要

Hermes 不應被視為單純的聊天服務。它是一個具備工具調用能力的代理系統，可能持有 API keys、bot tokens、sessions、memory，並且可能連接 Discord、Telegram、Slack、GitHub、Google Calendar、Kubernetes、資料庫或瀏覽器自動化工具。

因此，Hermes 的主要風險不在於「對話」，而在於它可能被外部輸入或 prompt injection 誘導去執行高權限工具操作。

將 Hermes 部署在 Kubernetes 上的最大安全價值，是可以把「思考層」與「行動層」拆開，並用 Kubernetes 原生能力建立隔離、授權、網路邊界、資源限制與審計機制。

一句話來說：

> Hermes gateway 只負責對話與決策；高風險工具執行、MCP、瀏覽器、自動化、Calendar、GitHub、Kubernetes 操作都拆出去，由 Kubernetes 負責隔離與管控。

## 一、Hermes 的主要威脅模型

Hermes 的風險來自它具備代理能力，而不是單純的文字生成。實際部署時，Hermes 可能同時涉及：

1. 持有 API key、bot token、session、memory。
2. 接收 Discord、Telegram、Slack、Webhook 等外部輸入。
3. 可能被 prompt injection 誘導使用工具。
4. 可能執行 shell、browser、code runner。
5. 可能連接 GitHub、Google Calendar、Kubernetes、DB。
6. 可能寫入記憶、skills、session files。

Hermes 相關使用者資料通常會集中在 `/opt/data`，包含 config、API keys、sessions、skills、memories 等。因此 `/opt/data` 對企業而言應被視為高敏感資料儲存區，而不是一般應用資料目錄。

如果 Hermes gateway、工具執行、瀏覽器、自動化、API token、session、memory 全部集中在同一個執行環境，一旦 gateway 被濫用，攻擊者可能取得過多能力。

Kubernetes 的價值在於讓這些能力可以被拆開、隔離、限制與審計。

這個風險判斷也符合數位發展部資通安全署在 2026-03-25 發布的 AI 代理資安提醒。該新聞稿指出，AI 代理的資安風險不是單一漏洞問題，而是架構層面的系統性風險；其中包含外部網頁或社群留言中的惡意指令、第三方 Skill 擴充套件暗藏惡意程式，以及長時間運作後因內容壓縮導致安全守則遺失等情境。

## 二、Kubernetes 提供適合 AI Agent 的安全分層

在 Kubernetes 中，Hermes 可以拆成多個 namespace，每個 namespace 套用不同安全政策：

```text
hermes-system      Hermes Gateway / Dashboard
hermes-tools       MCP Servers / Skills backend
hermes-sandbox     Shell / Browser / Code Runner
llm-serving        Ollama / vLLM / 本地模型服務
observability      Logs / Metrics / Audit
```

這種架構符合深度防禦原則：

```text
Hermes gateway = brain
MCP servers = controlled hands
sandbox jobs = disposable workspace
NetworkPolicy = boundary
RBAC = permission
PVC / Secrets = crown jewels
Audit log = accountability
```

建議的整體架構如下：

```text
Internet / Discord / Telegram / Slack
        |
        v
[Ingress / Gateway Auth / WAF]
        |
        v
+-----------------------------+
| namespace: hermes-system    |
|                             |
|  hermes-gateway             |
|  - replicas: 1              |
|  - /opt/data PVC            |
|  - no cluster-admin         |
|  - no hostPath              |
|  - no Docker socket         |
|                             |
|  hermes-dashboard           |
|  - internal only            |
|  - admin access only        |
+-------------+---------------+
              |
              | only allowed service-to-service traffic
              v
+-----------------------------+
| namespace: hermes-tools     |
|                             |
|  calendar-mcp               |
|  discord-mcp                |
|  github-mcp                 |
|  read-only-k8s-mcp          |
+-------------+---------------+
              |
              v
+-----------------------------+
| namespace: hermes-sandbox   |
|                             |
|  code-runner Job            |
|  browser-sandbox Pod        |
|  ephemeral workspace PVC    |
|  strict NetworkPolicy       |
+-----------------------------+

+-----------------------------+
| namespace: llm-serving      |
|                             |
|  local Ollama / vLLM / NIM  |
|  or egress to cloud LLM API |
+-----------------------------+

+-----------------------------+
| namespace: observability    |
|                             |
|  Prometheus / Loki / Grafana|
|  audit logs                 |
+-----------------------------+
```

重點是：不要讓 Hermes gateway 直接擁有所有工具權限。

## 三、Gateway 維持最小權限

Hermes gateway 是核心服務，但它不應該擁有 Kubernetes 管理權限，也不應該直接執行 shell 或掛載 Docker socket。

建議限制如下：

1. 不給 `cluster-admin`。
2. 不掛 Docker socket。
3. 不掛 `hostPath`。
4. 不使用 privileged container。
5. 不使用 `hostNetwork`。
6. 不允許 privilege escalation。
7. 不自動掛載 Kubernetes service account token。

範例 ServiceAccount：

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: hermes-gateway
  namespace: hermes-system
automountServiceAccountToken: false
```

範例 Pod 安全設定：

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
containers:
  - name: hermes
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      runAsNonRoot: true
      capabilities:
        drop: ["ALL"]
```

這代表 gateway 即使被 prompt injection 誘導，也不會自然擁有 Kubernetes API token、host filesystem、Docker socket 或 privileged container 能力。

在建議架構中，`hermes-system` 應被定位為核心腦袋區域，並透過 ServiceAccount、Pod Security Standards、NetworkPolicy 與 PVC 管理 gateway 的執行環境。

## 四、將 `/opt/data` 視為高敏感資料

Hermes 的 `/opt/data` 會保存 config、API keys、sessions、skills、memories 等資料。這個目錄本質上是高敏感資料區，不應被一般工具或 sandbox 共用。

在 Kubernetes 中，應使用 PVC 明確管理 `/opt/data`：

```text
/opt/data PVC
- 僅 Hermes gateway 可讀寫
- dashboard 最好只讀掛載
- sandbox pod 不得掛載
- 不建議多個 gateway replicas 同時寫入
- 使用加密 storage class
- 定期 snapshot / backup
```

這比把資料散落在單機 filesystem 更容易制定備份、加密、存取控制與稽核策略。

## 五、NetworkPolicy 建立預設拒絕的網路邊界

Hermes 的安全重點之一，是不能讓任何 pod 預設自由連線到所有服務或外網。

在 Kubernetes 中，可以先對每個 namespace 套用 default deny：

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

再逐項放行必要流量：

```text
Ingress Controller -> Hermes Gateway
Hermes Gateway -> MCP servers
Hermes Gateway -> LLM serving
Pods -> CoreDNS
```

例如 Hermes gateway 僅允許呼叫工具端與模型端：

```yaml
egress:
  - to:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: hermes-tools
  - to:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: llm-serving
```

如果需要呼叫 OpenAI、Anthropic、Gemini 等外部 LLM API，原生 Kubernetes NetworkPolicy 對 FQDN 控制不足，建議透過 Cilium FQDN policy、egress gateway、service mesh，或將所有外部 LLM 呼叫集中到一個 `llm-proxy`。

## 六、工具執行與 Gateway 分離

Hermes 最大的風險通常不是模型回答，而是工具執行。Shell、browser、code runner 都屬於高風險能力。

因此不建議讓 Hermes gateway 在同一個 pod 裡直接執行 local shell。較安全的架構是：

```text
Hermes Gateway
    -> Tool Router / MCP Server
        -> Kubernetes Job / Sandbox Pod
```

也就是：

```text
不要：
Hermes gateway 直接執行 shell command

建議：
Hermes 送任務 -> sandbox job 執行 -> 回傳結果
```

Sandbox namespace 應採用更嚴格的限制：

1. 不掛 Hermes `/opt/data`。
2. 不掛 `hostPath`。
3. 不自動掛載 Kubernetes service account token。
4. 預設無外網。
5. 需要網路時白名單放行。
6. 每次任務使用 Job 或 ephemeral workspace。
7. CPU、memory、disk、pids 全部限制。
8. 結果只透過 API 或 object storage 回傳。

這讓工具執行變成一次性的、可限制的、可審計的工作單元，而不是在 gateway 內部長期累積風險。

## 七、MCP 依權限拆分，避免單一 Token 過大

Hermes 不應該有一個萬能 MCP server。比較安全的方式是依能力拆分：

```text
calendar-mcp
  - 只持有 Google Calendar token
  - 只能建立 / 查詢 event

discord-mcp
  - 只持有 Discord bot token
  - 只能管理特定 server / channel

github-mcp
  - 只持有 GitHub fine-grained token
  - 只允許指定 repo

k8s-readonly-mcp
  - 只能 get/list/watch pods, deployments, logs
  - 不能 create/delete/patch
  - 不能讀 secrets

k8s-admin-mcp
  - 預設停用
  - 需要人工核准
  - 短時間 token
```

例如 Kubernetes MCP 應先從 read-only 開始，只允許：

```text
pods
pods/log
services
events
deployments
replicasets
statefulsets
daemonsets
```

不應允許：

```text
secrets
pods/exec
pods/attach
serviceaccounts/token
persistentvolumes
mutatingwebhookconfigurations
verbs: ["*"]
resources: ["*"]
```

這樣即使 Hermes 被誘導使用工具，能造成的影響也會被限制在事先批准的範圍內。

## 八、Skill 與長期記憶治理

AI Agent 的風險不只來自 gateway 或 MCP server，也來自可擴充的 Skill 與長期記憶內容。

第三方 Skill 在安裝前應納入正式審查流程：

1. 禁止在 production gateway 直接安裝未審查 Skill。
2. Skill 原始碼需先經過人工 review。
3. 應使用 Trivy、Grype、Semgrep、secret scanning 等工具檢查可疑行為。
4. 若 Skill 會下載外部檔案、連線到不明網域、執行 shell、讀取 token 或修改記憶，應列為高風險。
5. Production 僅允許從內部 registry 或經批准的 allowlist 安裝 Skill。

長期記憶也應視為安全控制面的一部分。若 Hermes 依賴 memory 或 system instruction 維持安全規則，這些規則不應只存在於短期對話上下文中，否則長時間運作或內容壓縮後可能遺失。

建議做法：

1. 將不可刪除的安全限制寫入核心記憶或啟動設定。
2. 將核心安全規則納入版本控管。
3. 定期備份與審閱 memory files。
4. 對 memory 變更建立 audit log。
5. 高風險安全規則不可由 agent 自行移除，需人工核准。

例如：

```text
- 刪除資料前必須經人工核准。
- 發送外部郵件或訊息前必須經人工核准。
- 存取 Secret、credential、token 前必須經人工核准。
- 執行 shell、browser automation、Kubernetes mutation 前必須經人工核准。
- 不得將 /opt/data、session、memory 或 credentials 傳送到外部服務。
```

## 九、Dashboard 與 Gateway 不直接公開到 Internet

Hermes gateway 可能提供 API 與 health endpoint，dashboard 則屬於管理介面。兩者都不應直接暴露在 Internet。

較佳做法是：

```text
gateway:
  僅允許 ingress auth 後存取必要 endpoint

dashboard:
  僅限 VPN / Tailscale / Cloudflare Access / oauth2-proxy
  僅 admin 可用
```

測試環境可以使用 port-forward 驗證服務；正式環境則應使用受控 ingress，並避免直接開放 gateway 或 dashboard port 給 Internet。

## 十、Secrets 管理應依服務拆分

最低限度可以使用 Kubernetes Secret。更完整的企業做法可以採用：

```text
External Secrets Operator + cloud secret manager
Sealed Secrets
SOPS + age
Vault
```

Secret 應依服務拆分：

```text
hermes-secret:
  LLM API key
  gateway token

calendar-mcp-secret:
  Google OAuth credential

discord-mcp-secret:
  Discord bot token

github-mcp-secret:
  GitHub fine-grained token
```

不要把所有 token 都塞進同一個 Hermes pod。原因很簡單：Hermes gateway 被 prompt injection 誘導時，它能用的權限越少越好。

## 十一、Kubernetes 可接入既有資安治理與審計

Hermes on Kubernetes 的另一個優點，是可以直接接上既有平台治理工具：

```text
Prometheus / Grafana    metrics
Loki                    logs
Kubernetes audit log    API 操作紀錄
Kyverno / Gatekeeper    admission policy
Trivy / Grype           image scanning
Falco                   runtime detection
cosign                  image signing
External Secrets        secret lifecycle 管理
```

這些能力讓 Hermes 不只是「跑起來」，而是可以被納入企業既有的資安治理、監控、合規與稽核流程。

## 十二、對應資安署 AI 代理五項防護建議

數位發展部資通安全署在「小心 AI 代理變資安破口」新聞稿中，提醒導入 AI Agent 應落實五項防護。Hermes on Kubernetes 的架構可以對應如下：

| 資安署建議 | Hermes on Kubernetes 對應措施 |
| --- | --- |
| 落實環境隔離 | 使用 `hermes-system`、`hermes-tools`、`hermes-sandbox`、`llm-serving` 等 namespace 隔離；shell、browser、code runner 放到 sandbox Job。 |
| 外部帳號權限最小化 | Calendar、Discord、GitHub、Kubernetes MCP 分別使用獨立 token；GitHub 使用 fine-grained token；Kubernetes 從 read-only MCP 起步。 |
| 設置人類審核機制 | 對刪除資料、發送訊息、存取憑證、執行 shell、Kubernetes mutation 等高風險操作加入 human approval gate。 |
| 親自審查 Skill 擴充套件 | 第三方 Skill 先經人工 code review、掃描與 allowlist 才能進 production；禁止 gateway 直接安裝未審查 Skill。 |
| 將安全守則寫入長期記憶 | 將核心安全規則寫入啟動設定或核心記憶，納入版本控管、備份、審閱與變更稽核。 |

參考來源：[資通安全署新聞稿，2026-03-25：小心 AI 代理變資安破口，資安署提醒導入 OpenClaw 應落實五項資安防護](https://moda.gov.tw/ACS/press/news/press/19294)。

## 十三、Production 建議安全基線

第一版 production 建議至少做到：

1. Hermes gateway replicas = 1。
2. `/opt/data` 使用 PVC，並視為敏感資料。
3. Namespace 啟用 Pod Security `restricted`。
4. NetworkPolicy 採 default deny。
5. Gateway 不掛 Kubernetes service account token。
6. 不掛 Docker socket。
7. 不使用 `hostPath`。
8. Dashboard 不公開到 Internet。
9. MCP 依權限拆分，不共用 token。
10. Sandbox pod 不掛 Hermes PVC。
11. Kubernetes MCP 從 read-only 開始。
12. 破壞性操作必須 human approval。
13. 第三方 Skill 必須先經安全審查與 allowlist。
14. 核心安全守則必須寫入啟動設定或長期記憶，並納入備份與稽核。

進階安全強化：

1. gVisor / Kata Containers 跑 sandbox。
2. Cilium FQDN egress policy。
3. OPA Gatekeeper / Kyverno admission policy。
4. image signing / cosign。
5. Trivy / Grype image scanning。
6. Falco runtime detection。
7. Loki 保存 tool call logs。
8. Human approval gate for destructive actions。
9. 所有 agent tool call 都要 audit log。
10. 每個使用者或每個 agent 使用獨立 namespace 與 PVC。
11. Skill registry allowlist 與 admission policy。
12. Memory file integrity check 與變更通知。

## 十四、結論

Hermes 架設在 Kubernetes 上的安全價值，不只是容器化部署，而是可以建立一套適合 AI agent 的安全框架。

Hermes gateway 負責思考與決策，但不直接擁有所有行動權限。MCP servers 依權限拆分，sandbox jobs 負責高風險工具執行，NetworkPolicy 建立網路邊界，RBAC 控制 Kubernetes 權限，PVC 與 Secrets 被視為核心敏感資產，audit log 則提供事後追蹤與問責能力。

因此，Hermes on Kubernetes 是較適合企業環境的安全架構，因為它讓 AI agent 的能力可以被拆分、限制、觀測與審計。

真正安全的 Hermes 部署，不是把 Hermes pod 跑起來，而是從第一天就把「思考層」與「行動層」分開。
