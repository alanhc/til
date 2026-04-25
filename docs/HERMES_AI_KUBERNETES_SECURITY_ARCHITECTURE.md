# Hermes on Kubernetes：AI Agent 的隔離、權限與審計架構設計

## 摘要

Hermes 不應被視為單純的聊天服務。它是一個具備工具調用能力的代理系統，可能持有 API keys、bot tokens、sessions、memory，並且可能連接 Discord、Telegram、Slack、GitHub、Google Calendar、Kubernetes、資料庫或瀏覽器自動化工具。

因此，Hermes 的主要風險不在於「對話」，而在於它可能被外部輸入或 prompt injection 誘導去執行高權限工具操作。

將 Hermes 部署在 Kubernetes 上的最大安全價值，是可以把「思考層」與「行動層」拆開，並用 Kubernetes 原生能力建立隔離、授權、網路邊界、資源限制與審計機制。

一句話來說：

> Hermes gateway 只負責對話與決策；高風險工具執行、MCP、瀏覽器、自動化、Calendar、GitHub、Kubernetes 操作都拆出去，由 Kubernetes 負責隔離與管控。

## 重要前提

Kubernetes 並不會自動讓 Hermes 變安全。本文所稱的安全價值，建立在以下條件成立時：

1. 使用支援 NetworkPolicy enforcement 的 CNI，例如 Cilium、Calico 或 OVN-Kubernetes。
2. Namespace 啟用 Pod Security Admission `restricted` baseline。
3. Gateway、MCP、sandbox、LLM serving 使用不同 ServiceAccount、Secret、PVC 與 NetworkPolicy。
4. Secrets 啟用 encryption at rest，或使用 External Secrets、Vault、cloud secret manager。
5. 高風險 tool call 由 tool router 或 policy engine 強制審核，而不是只依賴 LLM 自我約束。
6. Sandbox 若執行不可信程式碼，應使用 gVisor、Kata Containers、Firecracker 類型的強隔離 runtime。
7. Observability、logs、memory、session files 都視為敏感資料處理。
8. Gateway、MCP server 與 dashboard 之間有明確的 service-to-service authentication，例如 mTLS、service mesh identity 或短效 API token。
9. 外部輸入通道具備 rate limiting、基本內容過濾與來源驗證，避免 agent 被大量訊息或惡意 prompt 直接觸發。

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

雖然該新聞稿以 OpenClaw 為例，但其描述的 AI Agent 風險，包括外部輸入、Skill 擴充、長期記憶與高權限工具操作，也適用於 Hermes 這類具備工具調用能力的代理系統。

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

外部輸入也是防線的一部分。Discord、Telegram、Slack、Webhook 或表單進來的內容，不應未經處理就直接送進 LLM 與 tool planner。建議在 ingress 或 gateway 前段加入來源驗證、rate limiting、content filter 與基本 sanitization，例如限制訊息大小、拒絕可疑附件、標記「要求忽略系統指令」「要求輸出 secret」「要求直接執行 shell」等高風險內容，並把這些事件送進 audit log。這不能完全消除 prompt injection，但可以降低 agent 被低成本大量觸發或被明顯惡意指令直接推進工具層的機率。

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
    volumeMounts:
      - name: hermes-data
        mountPath: /opt/data
      - name: tmp
        mountPath: /tmp
      - name: cache
        mountPath: /var/cache/hermes
volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
```

這代表 gateway 即使被 prompt injection 誘導，也不會自然擁有 Kubernetes API token、host filesystem、Docker socket 或 privileged container 能力。

`readOnlyRootFilesystem: true` 是合理的 hardening，但可能和實際 Hermes 寫入行為衝突。Hermes 可能需要寫入 `/tmp`、cache、log、plugin state、SQLite 或 session 檔案；因此 root filesystem 設為唯讀時，應明確掛載可寫目錄，例如 `/opt/data`、`/tmp` 與必要 cache 目錄。正式環境應先確認實際寫入路徑，再收斂成最小可寫範圍。

在建議架構中，`hermes-system` 應被定位為核心腦袋區域，並透過 ServiceAccount、Pod Security Standards、NetworkPolicy 與 PVC 管理 gateway 的執行環境。

`replicas: 1` 是保守起點，不是 HA 架構。這個限制主要是為了避免多個 gateway 同時寫入同一份 `/opt/data` PVC，造成 session、memory 或 SQLite state 互相覆蓋。但它也代表 gateway 會成為單點故障。若 production 需要 HA，應先處理狀態層，而不是直接把 replicas 調高：

1. 使用 ReadWriteMany storage，例如 NFS、CephFS、EFS 或其他支援多點掛載的 storage class，並確認 Hermes 的檔案寫入模式能安全處理並發。
2. 將 session、memory、queue、approval state 移到外部 Redis、PostgreSQL 或專用 state service，讓 gateway 盡量 stateless。
3. 將 tool execution state 放在 tool router、Job controller 或 workflow engine，而不是放在 gateway 本地 filesystem。
4. 對 gateway 使用 readiness probe、PodDisruptionBudget、rolling update 與短 timeout，避免節點維護時中斷所有入口。

如果做不到狀態外移或 RWX storage 驗證，`replicas: 1` 是較安全但可用性較低的部署選擇；若要 scale out，應先把「狀態一致性」當成架構問題處理。

## 四、將 `/opt/data` 視為高敏感資料

Hermes 的 `/opt/data` 可能保存 config、API keys、sessions、skills、memories 等資料。這個目錄本質上是高敏感資料區，不應被一般工具或 sandbox 共用。

理想上，`/opt/data` 不應直接存放長期 API key 或高權限 token。Credentials 應拆到 Kubernetes Secret、External Secrets、Vault 或 cloud secret manager。`/opt/data` 主要保存 Hermes runtime state、memory、非機密設定與必要 session metadata。若現實上 Hermes 仍會把 token 寫進 `/opt/data`，則該 PVC 必須視為 secret-equivalent storage，需加密、備份、限制掛載、限制 snapshot 存取，並建立存取稽核。

在 Kubernetes 中，應使用 PVC 明確管理 `/opt/data`：

```text
/opt/data PVC
- 僅 Hermes gateway 可讀寫
- dashboard 不直接掛載完整 /opt/data
- sandbox pod 不得掛載
- 不建議多個 gateway replicas 同時寫入
- 使用加密 storage class
- 定期 snapshot / backup
```

這比把資料散落在單機 filesystem 更容易制定備份、加密、存取控制與稽核策略。

Dashboard 即使只讀掛載 `/opt/data` 仍然有洩密風險，因為讀取 secret 本身就是高風險能力。較安全的方式是讓 dashboard 透過 Hermes gateway 或 metadata API 取得經過過濾的狀態資訊，而不是直接讀取 API keys、session files、memory raw files 或 credentials。

## 五、NetworkPolicy 建立預設拒絕的網路邊界

Hermes 的安全重點之一，是不能讓任何 pod 預設自由連線到所有服務或外網。

注意：NetworkPolicy 不是 kube-apiserver 自己執行的防火牆規則，必須依賴 CNI plugin 實作。若使用的 CNI 不支援 NetworkPolicy，例如某些預設或簡化環境，default deny 可能不會真正生效。因此 production 應明確指定 Calico、Cilium、OVN-Kubernetes 等支援 NetworkPolicy 的 CNI，並用測試 pod 驗證阻擋效果。

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
        podSelector:
          matchLabels:
            app: tool-router
    ports:
      - protocol: TCP
        port: 8080
  - to:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: llm-serving
        podSelector:
          matchLabels:
            app: llm-gateway
    ports:
      - protocol: TCP
        port: 8000
```

正式環境不應只用 `namespaceSelector`，應同時限制 `podSelector` 與 `ports`，避免 gateway 可以任意連到同 namespace 中未預期的服務。

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

Sandbox namespace 應採用更嚴格的限制。一般 container isolation 不是強沙箱；若 sandbox 會執行不可信程式碼、瀏覽未知網頁或跑外部提供的 script，單純 Kubernetes Pod 隔離仍不足。此時應優先考慮 gVisor、Kata Containers、Firecracker 類型的強隔離 runtime，並搭配 seccomp、AppArmor、read-only root filesystem、無 service account token、無 `hostPath`、無 privileged、無外網或白名單 egress。

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

Gateway 呼叫 MCP server 時也需要認證，不能只依賴 NetworkPolicy。NetworkPolicy 可以限制「誰能連到誰」，但如果攻擊者已經取得 cluster 內某個可連線 pod 的能力，仍可能嘗試直接呼叫 MCP server，繞過 gateway 的 policy decision。正式環境應至少採用其中一種 service-to-service authentication：

1. Service mesh mTLS，例如 Istio、Linkerd 或 Cilium service mesh，讓 MCP server 驗證 caller workload identity。
2. Gateway 到 MCP 使用短效 API token 或 signed request，MCP server 端驗證 token audience、issuer、expiry 與 scope。
3. 由 tool router 統一代理 MCP 呼叫，MCP server 只接受 tool router identity，並拒絕一般 pod 直接呼叫。
4. 對高風險 MCP 加上 request-level authorization，檢查 user、agent、tool、action、resource 與 approval id。

換句話說，MCP server 不應只因為請求來自 cluster 內部就信任它。NetworkPolicy、mTLS、token scope 與 audit log 應一起使用。

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

Human approval gate 不應只是讓模型問一句「你確定嗎？」。較好的做法是由 tool router 或 policy engine 實作強制 gate，而不是依賴 LLM 自我約束。高風險 tool call 應先產生 dry-run plan，包含操作對象、參數、影響範圍與 rollback 方式，等待人類在獨立 UI、CLI 或 chat command 中批准後才執行。批准紀錄應寫入 audit log，並能追溯到使用者、時間、tool call、參數與執行結果。

一個可落地的 approval flow 可以長這樣：

```text
1. LLM 產生 tool intent
2. Tool router 判斷 action risk level
3. 高風險 action 只建立 pending approval，不執行
4. Slack / Teams / Web UI / CLI 顯示 dry-run plan
5. 人類核准後產生短效 approval token
6. Tool router 驗證 approval token、action hash、expiry、approver
7. 執行 tool call
8. 寫入 audit log 與 execution result
```

Approval token 應綁定具體 action，而不是泛用通行證。它至少應包含 tool name、action、resource、arguments hash、approver、expiry、request id。若參數在核准後被模型或使用者改動，原本的 approval 應失效。若用 Kubernetes Job 實作，也可以讓 tool router 先建立 `PendingApproval` custom resource 或 queue item，approval controller 收到外部 webhook 後才建立真正執行的 Job。

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

Ingress / WAF 不應只是一個方框。正式環境至少要明確定義：

1. 身分驗證：使用 OAuth2/OIDC、Cloudflare Access、Tailscale ACL、mTLS client cert 或企業 IdP，不應只靠隱藏 URL。
2. 授權：區分一般使用者、operator、admin；dashboard 與 tool approval UI 只允許少數角色。
3. Rate limiting：依 user、source IP、channel、agent id 限流，避免外部訊息大量觸發 agent 或燒掉 LLM API quota。
4. Request constraints：限制 body size、attachment type、URL fetch 行為與 webhook replay window。
5. WAF / bot rules：阻擋明顯掃描、暴力嘗試、異常 user agent 與已知攻擊 payload。
6. Audit：記錄誰從哪個入口觸發了哪個 agent request，但要先做 secret / PII redaction。

對聊天平台整合而言，rate limiting 特別重要。Discord、Telegram、Slack、Webhook 都可能被大量訊息觸發，導致 agent 不斷規劃工具、呼叫 LLM 或打外部 API。入口層應有 per-channel、per-user、per-agent 與全域 quota；高風險 action 則應有更低的速率限制與 approval gate。

## 十、Secrets 管理應依服務拆分

最低限度可以使用 Kubernetes Secret，但 Kubernetes Secret 不是萬靈丹。Secret values 預設只是 base64 編碼，不等於加密；正式環境應啟用 etcd encryption at rest，或改用 External Secrets、Vault、cloud secret manager 等外部 secret manager。更完整的企業做法可以採用：

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

Observability stack 也應視為敏感系統。Tool call logs、prompt、response、error trace 可能包含 credentials、個資或機密內容，例如使用者輸入、tool arguments、API response、email、calendar、repo、chat content，甚至 stack trace 裡的 secret。正式環境應加入 secret redaction、PII redaction、log retention policy、存取權限控管與查詢稽核。

## 十二、對應資安署 AI 代理五項防護建議

數位發展部資通安全署在「小心 AI 代理變資安破口」新聞稿中，提醒導入 AI Agent 應落實五項防護。該新聞稿討論的是 OpenClaw，不是 Hermes 本身；以下不是宣稱兩者架構相同，而是用 Hermes 類似的 agentic tool-use 架構，對應同一類 AI Agent 風險與防護建議：

| 資安署建議 | Hermes on Kubernetes 對應措施 |
| --- | --- |
| 落實環境隔離 | 使用 `hermes-system`、`hermes-tools`、`hermes-sandbox`、`llm-serving` 等 namespace 隔離；shell、browser、code runner 放到 sandbox Job。 |
| 外部帳號權限最小化 | Calendar、Discord、GitHub、Kubernetes MCP 分別使用獨立 token；GitHub 使用 fine-grained token；Kubernetes 從 read-only MCP 起步。 |
| 設置人類審核機制 | 對刪除資料、發送訊息、存取憑證、執行 shell、Kubernetes mutation 等高風險操作加入 human approval gate。 |
| 親自審查 Skill 擴充套件 | 第三方 Skill 先經人工 code review、掃描與 allowlist 才能進 production；禁止 gateway 直接安裝未審查 Skill。 |
| 將安全守則寫入長期記憶 | 將核心安全規則寫入啟動設定或核心記憶，納入版本控管、備份、審閱與變更稽核。 |

參考來源：[資通安全署新聞稿，2026-03-25：小心 AI 代理變資安破口，資安署提醒導入 OpenClaw 應落實五項資安防護](https://moda.gov.tw/ACS/press/news/press/19294)。

## 十三、落地取捨與維運成本

以上架構偏向企業級或高風險場景的安全基線。它的核心價值是把 prompt injection 造成的越權操作限制在可控範圍內，但代價是延遲、維運複雜度與平台能力要求都會上升。導入前應先確認團隊是否具備 Kubernetes、CNI、runtime、GitOps 與 observability 的維運能力，以及產品體驗是否能接受 sandbox 啟動延遲。

第一個取捨是 latency。每次高風險工具都用 Kubernetes Job 或新 sandbox Pod 執行，安全性較高，但啟動 Pod 通常需要 1 到數秒；若 image pull、admission webhook、runtime sandbox 或節點資源調度較慢，延遲會更高。AI Agent 常見的 ReAct 流程會反覆「思考 -> 寫程式 -> 執行 -> 看錯誤 -> 修改 -> 再執行」，如果每次 code runner 或 browser call 都建立新 Pod，使用者等待時間可能從幾秒變成數十秒甚至數分鐘。

實務上可以分級處理：

1. 低風險、短生命週期操作可使用 warm sandbox pool 或預先啟動的 worker，但仍要限制 token、filesystem 與 egress。
2. 高風險操作使用 one-shot Job、強隔離 runtime 與更嚴格審計。
3. 同一個使用者任務可以在有限時間內重用同一個 ephemeral sandbox，任務結束後銷毀。
4. 常用 image 應預先拉到節點，並設定 resource requests，避免 cold start 失控。
5. Tool router 應把 sandbox startup time、execution time、queue time 分開記錄，否則很難定位 UX 延遲來源。

第二個取捨是 container isolation 的上限。Kubernetes Pod 加上 Pod Security、seccomp、AppArmor、read-only root filesystem、無 service account token、無 `hostPath`、無 privileged，可以大幅降低風險，但一般 Linux container 仍與宿主機共用 kernel。若 sandbox 會執行不可信程式碼、瀏覽未知網頁、解壓外部檔案或執行使用者提供的 script，應把 gVisor、Kata Containers、Firecracker 這類強隔離 runtime 視為必要控制，而不是 nice-to-have。否則遇到 kernel exploit 或 container escape 類漏洞時，攻擊面仍可能延伸到 worker node。

第三個取捨是資料傳遞摩擦。Gateway 不共用 `/opt/data` 給 sandbox 是正確的，但 sandbox 產生的檔案、報表、截圖、ZIP、爬蟲結果仍需要回傳。若直接共用 PVC，會把隔離邊界打開；較安全的做法是：

1. Sandbox 將輸出寫到內部 object storage，例如 S3、MinIO 或雲端 bucket。
2. Tool router 只回傳 artifact id、metadata、hash、size、MIME type 與短效下載 URL。
3. Gateway 只讀取經過掃描、大小限制與 allowlist 檢查的 artifact。
4. 對 artifact 做 malware scan、content-type validation、secret scanning 與 retention policy。
5. 大檔案與高敏感輸出不直接進 prompt context，只給摘要或引用連結。

這代表系統還需要 artifact service 或內部 object storage。它增加了開發與維運成本，但能避免 sandbox 直接接觸 gateway state 或 Hermes memory。

第四個取捨是 egress 管理。AI Agent 可能需要呼叫 LLM API、GitHub、搜尋服務、文件網站、套件 registry 或企業內部 API；這些 endpoint 的 IP 經常變動，單靠 IP allowlist 很難維護。若要用 FQDN policy、egress gateway 或 service mesh 控制外連，通常需要 Cilium、Istio 或等價平台能力，並承擔 DNS policy、TLS inspection、憑證、sidecar 或 eBPF datapath 的維運成本。對小團隊而言，可以先集中所有外部連線到少數 proxy，例如 `llm-proxy`、`web-fetch-proxy`、`package-proxy`，再逐步導入更細的 egress policy。

第五個取捨是 operational overhead。把 calendar、discord、github、k8s、browser、code runner 全部拆成獨立 MCP server，安全邊界會更清楚，但也會帶來更多 Deployment、ServiceAccount、Secret、RBAC、NetworkPolicy、Ingress、alert rule 與 dashboard。若沒有 CI/CD、Helm/Kustomize、Terraform/Pulumi、Argo CD/Flux、policy-as-code 與自動化測試，很快會變成 YAML Hell。比較務實的做法是：

1. 先把能力按風險分成 low-risk、sensitive、destructive 三層，而不是一開始每個小工具都拆一個 namespace。
2. 用 GitOps 管理所有 Kubernetes manifests，避免手動 kubectl drift。
3. 把 MCP server、Secret、NetworkPolicy、ServiceAccount 包成可重用模板。
4. 每新增一個 Skill 或 MCP，就自動產生 threat model、RBAC diff、egress diff 與 approval policy。
5. 對安全政策做 CI 驗證，例如禁止 privileged、hostPath、cluster-admin、未標記 owner 的 Secret。

因此，本文架構比較適合銀行級、企業級、多租戶或會執行不可信工具的場景。若只是個人實驗或小型內部 bot，可以先採用其中幾個高價值控制：不要掛 Docker socket、不要給 cluster-admin、拆 Secret、限制 egress、保留 audit log、對 destructive action 做 human approval。等需求進入 production、多租戶或高風險工具執行時，再逐步升級到完整 Kubernetes sandbox 與強隔離 runtime。

## 十四、Production 建議安全基線

第一版 production 建議至少做到：

1. Hermes gateway replicas = 1。
2. 若需要 HA，先使用 RWX storage 或將 session / memory / approval state 外移，再 scale gateway。
3. `/opt/data` 使用 PVC，並視為敏感資料。
4. Namespace 啟用 Pod Security `restricted`。
5. 使用支援 NetworkPolicy enforcement 的 CNI，並驗證 default deny 確實生效。
6. Gateway 不掛 Kubernetes service account token。
7. 不掛 Docker socket。
8. 不使用 `hostPath`。
9. Dashboard 不公開到 Internet。
10. Ingress 使用 OAuth/OIDC、VPN、Cloudflare Access、Tailscale ACL 或 mTLS 等明確 auth。
11. 外部輸入通道具備 rate limiting、來源驗證與基本 content filtering。
12. MCP 依權限拆分，不共用 token。
13. Gateway 到 MCP 使用 mTLS、短效 API token、signed request 或 service mesh identity。
14. Sandbox pod 不掛 Hermes PVC。
15. Kubernetes MCP 從 read-only 開始。
16. 高風險操作由 tool router 或 policy engine 強制 human approval。
17. Approval token 綁定 action hash、resource、expiry 與 approver。
18. 第三方 Skill 必須先經安全審查與 allowlist。
19. 核心安全守則必須寫入啟動設定或長期記憶，並納入備份與稽核。
20. Secret 啟用 etcd encryption at rest，或使用 External Secrets、Vault、cloud secret manager。
21. Observability、logs、memory、session files 都依敏感資料控管。

進階安全強化：

1. gVisor / Kata Containers / Firecracker 跑 sandbox。
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
13. 多租戶環境使用 per-user 或 per-agent namespace、ServiceAccount、PVC、Secret、quota 與 NetworkPolicy。

多租戶部署要更保守。如果多個使用者、團隊或 agent 共用同一個 cluster，不應只用 app-level tenant id 區分資料。較安全的基線是每個 tenant 或高風險 agent 有獨立 namespace、PVC、Secret、ServiceAccount、ResourceQuota、LimitRange、NetworkPolicy 與 audit label。這樣即使某個 agent 被 prompt injection 或 tool misuse 影響，也不會自然讀到其他 tenant 的 memory、session、token 或 sandbox output。

## 十五、結論

Hermes 架設在 Kubernetes 上的安全價值，不只是容器化部署，而是可以建立一套適合 AI agent 的安全框架。

Hermes gateway 負責思考與決策，但不直接擁有所有行動權限。MCP servers 依權限拆分，sandbox jobs 負責高風險工具執行，NetworkPolicy 建立網路邊界，RBAC 控制 Kubernetes 權限，PVC 與 Secrets 被視為核心敏感資產，audit log 則提供事後追蹤與問責能力。

因此，Hermes on Kubernetes 是較適合企業環境的安全架構，因為它讓 AI agent 的能力可以被拆分、限制、觀測與審計。

真正安全的 Hermes 部署，不是把 Hermes pod 跑起來，而是從第一天就把「思考層」與「行動層」分開。
