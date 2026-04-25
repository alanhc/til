可以把 Hermes on Kubernetes 的安全架構想成一句話：

Hermes gateway 只負責對話與決策；所有高風險工具執行、MCP、瀏覽器、自動化、Calendar/GitHub/K8S 操作都拆出去，用 Kubernetes 做隔離、授權、網路限制與審計。

1. 先定義威脅模型

Hermes 的風險不是「聊天」，而是它會：

1. 持有 API key / bot token / session / memory
2. 接收 Discord / Telegram / Slack / Webhook 外部輸入
3. 可能被 prompt injection 誘導使用工具
4. 可能執行 shell / browser / code
5. 可能連到 GitHub / Google Calendar / Kubernetes / DB
6. 可能寫入記憶、skills、session files

Hermes 官方 Docker 文件提到，container 會把 config、API keys、sessions、skills、memories 等使用者資料集中放在 /opt/data，所以這個 PVC 本身就要被視為高敏感資料儲存區。

2. 推薦整體架構
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

重點是：不要讓 Hermes gateway 直接擁有所有工具權限。

3. 安全分層設計
Layer 1：Namespace 隔離

建議至少拆 4 個 namespace：

hermes-system      跑 Hermes gateway / dashboard
hermes-tools       跑 MCP / Skills backend
hermes-sandbox     跑 shell / browser / code execution
llm-serving        跑本地 LLM，例如 Ollama / vLLM
observability      logs / metrics / audit

每個 namespace 套不同安全政策：

hermes-system:   restricted
hermes-tools:    restricted
hermes-sandbox:  restricted + 更嚴格 NetworkPolicy
llm-serving:     GPU node pool / 只允許 Hermes 呼叫

Kubernetes Pod Security Standards 有三個層級：Privileged、Baseline、Restricted；其中 Restricted 是依照目前 Pod hardening best practices 設計的較嚴格政策。

Namespace label 可以這樣設：

apiVersion: v1
kind: Namespace
metadata:
  name: hermes-system
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
Layer 2：Hermes gateway 權限最小化

Hermes gateway 是核心，但它不應該有 Kubernetes 管理權限。

建議：

不要給 cluster-admin
不要掛 Docker socket
不要掛 hostPath
不要 privileged
不要 hostNetwork
不要允許 privilege escalation
不要自動掛 service account token

Kubernetes 官方 RBAC good practices 建議只給使用者與 service account 必要權限、盡量用 namespace-level RoleBinding、避免 wildcard 權限，也建議避免不必要地自動掛載 service account token。

範例：

apiVersion: v1
kind: ServiceAccount
metadata:
  name: hermes-gateway
  namespace: hermes-system
automountServiceAccountToken: false

Deployment 安全設定：

apiVersion: apps/v1
kind: Deployment
metadata:
  name: hermes-gateway
  namespace: hermes-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hermes-gateway
  template:
    metadata:
      labels:
        app: hermes-gateway
    spec:
      serviceAccountName: hermes-gateway
      automountServiceAccountToken: false
      securityContext:
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: hermes
          image: nousresearch/hermes-agent:latest
          args: ["gateway", "run"]
          ports:
            - containerPort: 8642
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            runAsNonRoot: true
            capabilities:
              drop: ["ALL"]
          envFrom:
            - secretRef:
                name: hermes-secret
          volumeMounts:
            - name: hermes-data
              mountPath: /opt/data
            - name: tmp
              mountPath: /tmp
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2"
              memory: "4Gi"
      volumes:
        - name: hermes-data
          persistentVolumeClaim:
            claimName: hermes-data
        - name: tmp
          emptyDir: {}

注意：readOnlyRootFilesystem: true 時，要確定 Hermes 只寫 /opt/data 和 /tmp。如果啟動失敗，可以先拿掉，確認寫入路徑後再收緊。

4. /opt/data 要當成機密資料保護

因為 Hermes 會把 config、API keys、sessions、skills、memories 放在 /opt/data，這個 PVC 不能當普通資料看待。

建議：

1. PVC 使用加密 storage class
2. 定期 snapshot / backup
3. 僅 Hermes gateway 可讀寫
4. dashboard 最好 read-only mount
5. 不要讓 sandbox pod 掛同一份 /opt/data
6. 不要多個 gateway replicas 同時寫同一份 PVC

Dashboard 可以這樣掛：

volumeMounts:
  - name: hermes-data
    mountPath: /opt/data
    readOnly: true
5. NetworkPolicy：預設全拒絕，再逐項放行

Kubernetes NetworkPolicy 可以控制 Pod 與 Pod、namespace、外部 IP block 之間的 L3/L4 traffic，但前提是你的 CNI 必須支援 NetworkPolicy，例如 Calico、Cilium；如果 CNI 不支援，建立 NetworkPolicy 不會有實際效果。

5.1 預設拒絕所有 ingress / egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: hermes-system
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
5.2 只允許 Ingress Controller 進 Hermes gateway
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-to-hermes-gateway
  namespace: hermes-system
spec:
  podSelector:
    matchLabels:
      app: hermes-gateway
  policyTypes:
    - Ingress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8642
5.3 允許 Hermes 呼叫 MCP / LLM / DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-hermes-egress
  namespace: hermes-system
spec:
  podSelector:
    matchLabels:
      app: hermes-gateway
  policyTypes:
    - Egress
  egress:
    # DNS
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53

    # MCP tools
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: hermes-tools

    # local LLM serving
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: llm-serving
      ports:
        - protocol: TCP
          port: 8000
        - protocol: TCP
          port: 11434

如果要呼叫 OpenAI / Anthropic / Gemini 等外部 LLM API，原生 NetworkPolicy 對 FQDN 控制不夠好，建議用 Cilium FQDN policy、egress gateway、service mesh，或把所有外部 LLM 呼叫集中到一個 llm-proxy。

6. Tool / Shell / Browser 要和 Gateway 分離

Hermes 支援多種 terminal backend：local、docker、ssh、modal、daytona、singularity；官方文件也提醒 local backend 代表 agent 會直接擁有與使用者帳號相同的 filesystem access。

在 Kubernetes 裡面，不建議用 local backend 直接在 hermes-gateway pod 裡跑指令。

比較安全的設計：

Hermes gateway
    |
    v
tool-router / mcp-server
    |
    v
Kubernetes Job / sandbox pod

也就是：

不要：
Hermes gateway 裡面直接 shell command

建議：
Hermes 送任務 → sandbox job 執行 → 回傳結果

Hermes Docker backend 本身有一些安全強化，例如 dropped capabilities、no-new-privileges、PID limit、tmpfs size limits；但在 Kubernetes 裡，不建議把 host Docker socket 掛給 Hermes，因為 Docker socket 等同於高權限控制 host/container runtime。Hermes 官方設定文件提到 Docker backend 會透過 long-lived container 與 docker exec 執行命令，並有 --cap-drop、no-new-privileges、pids-limit 等 hardening。

7. Sandbox namespace 設計

hermes-sandbox 應該比 hermes-system 更嚴格。

sandbox pod 原則：
1. 不掛 Hermes /opt/data
2. 不掛 hostPath
3. 不掛 Kubernetes service account token
4. 預設無外網
5. 需要網路時白名單放行
6. 每次任務用 Job / ephemeral workspace
7. CPU / memory / disk / pids 全部限制
8. 結果只透過 API / object storage 回傳

範例 sandbox Job：

apiVersion: batch/v1
kind: Job
metadata:
  name: hermes-code-runner
  namespace: hermes-sandbox
spec:
  ttlSecondsAfterFinished: 300
  template:
    metadata:
      labels:
        app: hermes-code-runner
    spec:
      restartPolicy: Never
      automountServiceAccountToken: false
      securityContext:
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: runner
          image: python:3.12-slim
          command: ["python", "/workspace/task.py"]
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            runAsNonRoot: true
            capabilities:
              drop: ["ALL"]
          volumeMounts:
            - name: workspace
              mountPath: /workspace
            - name: tmp
              mountPath: /tmp
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
      volumes:
        - name: workspace
          emptyDir:
            sizeLimit: 1Gi
        - name: tmp
          emptyDir:
            sizeLimit: 256Mi
8. MCP / Skill 權限分級

不要讓一個 MCP server 擁有所有能力。建議按權限拆：

calendar-mcp
  - 只拿 Google Calendar token
  - 只能建立 / 查詢 event

discord-mcp
  - 只拿 Discord bot token
  - 只能管理特定 server / channel

github-mcp
  - 只拿 GitHub fine-grained token
  - 只允許指定 repo

k8s-readonly-mcp
  - 只能 get/list/watch pods, deployments, logs
  - 不能 create/delete/patch
  - 不能讀 secrets

k8s-admin-mcp
  - 預設停用
  - 需要人工核准
  - 短時間 token

如果 Hermes 要幫你看 Kubernetes 狀態，請先做 read-only K8S MCP。

RBAC 範例：

apiVersion: v1
kind: ServiceAccount
metadata:
  name: k8s-readonly-mcp
  namespace: hermes-tools
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: k8s-readonly
  namespace: target-app
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "events"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch"]

不要加：

verbs: ["*"]
resources: ["*"]

也不要讓 agent 可以讀：

secrets
serviceaccounts/token
pods/exec
pods/attach
persistentvolumes
mutatingwebhookconfigurations

Kubernetes 官方也特別提醒，list/watch secrets 實際上會讓使用者看到 Secret 內容；能建立 workload 的權限也可能間接取得 namespace 內的 Secret、ConfigMap、PersistentVolume 與 ServiceAccount 權限。

9. Dashboard 不要直接公開

Hermes Docker 文件提到 gateway port 8642 會暴露 OpenAI-compatible API server 與 health endpoint，也提醒在 internet-facing machine 上開 port 本身就是安全風險。

建議：

Hermes gateway 8642:
  - 不直接公開
  - 只允許 dashboard / internal service / ingress auth 後存取

Hermes dashboard 9119:
  - 不直接公開
  - 只走 VPN / Tailscale / Cloudflare Access / oauth2-proxy

比較好的做法：

外部 webhook / Discord:
  只進 gateway 需要的 endpoint

dashboard:
  只給 admin
  加 OIDC / SSO / Cloudflare Access
10. Secrets 管理

最低限度：

Kubernetes Secret

比較好：

External Secrets Operator + cloud secret manager
Sealed Secrets
SOPS + age
Vault

Secret 分級：

hermes-secret:
  LLM API key
  gateway token

calendar-mcp-secret:
  Google OAuth credential

discord-mcp-secret:
  Discord bot token

github-mcp-secret:
  GitHub fine-grained token

不要把所有 token 都塞進同一個 Hermes pod。原因很簡單：Hermes gateway 被 prompt injection 誘導時，它能用的權限越少越好。

11. Production 推薦安全基線
必做
1. Hermes gateway replicas = 1
2. /opt/data 使用 PVC，視為敏感資料
3. Pod Security enforce restricted
4. default deny NetworkPolicy
5. gateway 不掛 Kubernetes service account token
6. 不掛 Docker socket
7. 不使用 hostPath
8. dashboard 不公開到 internet
9. MCP 拆權限，不共用 token
10. sandbox pod 不掛 Hermes PVC
進階
1. gVisor / Kata Containers 跑 sandbox
2. Cilium FQDN egress policy
3. OPA Gatekeeper / Kyverno admission policy
4. image signing / cosign
5. Trivy / Grype image scanning
6. Falco runtime detection
7. Loki 保存 tool call logs
8. Human approval gate for destructive actions
9. 所有 agent tool call 都要 audit log
10. 每個使用者 / 每個 agent 一個 namespace + PVC
12. 最推薦的安全版架構
[User / Discord]
      |
      v
[Ingress + Auth]
      |
      v
[Hermes Gateway]
  - no K8S API token
  - no shell local execution
  - no Docker socket
  - PVC /opt/data only
      |
      +--> [LLM Proxy]
      |
      +--> [Calendar MCP]
      |
      +--> [Discord MCP]
      |
      +--> [K8S Readonly MCP]
      |
      +--> [Tool Router]
               |
               v
          [Sandbox Job]
          - no secrets by default
          - no egress by default
          - limited CPU/mem/disk
          - ephemeral workspace
一句話結論

Hermes on Kubernetes 的安全架構重點不是把 Hermes Pod 跑起來，而是把 Hermes 的「思考層」和「行動層」拆開。

Hermes gateway = brain
MCP servers = controlled hands
sandbox jobs = disposable workspace
NetworkPolicy = boundary
RBAC = permission
PVC / Secrets = crown jewels
Audit log = accountability

你真的要做得安全，第一版就照這個原則：

Hermes gateway 單一實例 + PVC
MCP 分權限
default deny network
sandbox 獨立 namespace
dashboard 不公開
K8S 權限 read-only 起步
destructive action 全部 human approval