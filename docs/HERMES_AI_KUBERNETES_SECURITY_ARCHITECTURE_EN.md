# Hermes on Kubernetes: Isolation, Permissions, and Audit Architecture for AI Agents

## Executive Summary

Hermes should not be treated as a simple chat service. It is an agentic system with tool-use capabilities. In practice, it may hold API keys, bot tokens, sessions, memory, and access to systems such as Discord, Telegram, Slack, GitHub, Google Calendar, Kubernetes, databases, browsers, and automation tools.

The primary security risk is not conversation itself. The risk is that external input or prompt injection may cause Hermes to invoke privileged tools or perform high-impact actions.

Deploying Hermes on Kubernetes is valuable because it separates the "reasoning layer" from the "action layer" and uses Kubernetes-native controls for isolation, authorization, network boundaries, resource limits, and auditability.

In one sentence:

> Hermes gateway should handle conversation and decision-making only; high-risk tool execution, MCP, browser automation, Calendar, GitHub, and Kubernetes operations should be separated and controlled through Kubernetes isolation, authorization, network policy, and audit mechanisms.

## Important Assumptions

Kubernetes does not automatically make Hermes secure. The security value described in this article depends on the following assumptions:

1. The cluster uses a CNI that supports NetworkPolicy enforcement, such as Cilium, Calico, or OVN-Kubernetes.
2. Namespaces enforce the Pod Security Admission `restricted` baseline.
3. Gateway, MCP, sandbox, and LLM-serving components use separate ServiceAccounts, Secrets, PVCs, and NetworkPolicies.
4. Secrets are encrypted at rest, or are managed through External Secrets, Vault, or a cloud secret manager.
5. High-risk tool calls are enforced by a tool router or policy engine, not only by LLM self-restraint.
6. If the sandbox executes untrusted code, it uses stronger isolation such as gVisor, Kata Containers, or Firecracker.
7. Observability data, logs, memory, and session files are treated as sensitive data.
8. Gateway, MCP servers, and dashboard use explicit service-to-service authentication, such as mTLS, service mesh identity, or short-lived API tokens.
9. External input channels have rate limiting, basic content filtering, and source verification, so agents cannot be cheaply triggered by large volumes of messages or obvious malicious prompts.

## 1. Hermes Threat Model

Hermes is risky because it is an agentic system, not because it generates text. A production deployment may involve:

1. Holding API keys, bot tokens, sessions, and memory.
2. Receiving external input from Discord, Telegram, Slack, or webhooks.
3. Being manipulated through prompt injection into invoking tools.
4. Running shell commands, browsers, or code runners.
5. Connecting to GitHub, Google Calendar, Kubernetes, or databases.
6. Writing memory, skills, session files, or configuration.

Hermes user data is commonly centralized under `/opt/data`, including configuration, API keys, sessions, skills, and memories. For enterprise security purposes, `/opt/data` should be treated as a highly sensitive data store rather than a normal application data directory.

If the Hermes gateway, tool execution, browser automation, API tokens, sessions, and memory all live in the same execution environment, a compromised or manipulated gateway may gain excessive power.

The value of Kubernetes is that these capabilities can be separated, isolated, restricted, and audited.

This risk model is also aligned with the AI agent security advisory published by Taiwan's Administration for Cyber Security on 2026-03-25. The advisory emphasizes that AI agent risk is not merely a single-vulnerability problem; it is an architectural and systemic risk. It highlights malicious instructions embedded in external webpages or social content, malicious third-party skills, and the possibility that long-running agents may lose safety rules after context compression.

Although that advisory uses OpenClaw as its example, the risks it describes, including external input, skill extensions, long-term memory, and high-privilege tool operations, also apply to Hermes-like agent systems that can invoke tools.

## 2. Kubernetes Provides Security Layering for AI Agents

Hermes can be split across multiple Kubernetes namespaces, each with a different security policy:

```text
hermes-system      Hermes Gateway / Dashboard
hermes-tools       MCP Servers / Skills backend
hermes-sandbox     Shell / Browser / Code Runner
llm-serving        Ollama / vLLM / local model serving
observability      Logs / Metrics / Audit
```

This follows a defense-in-depth model:

```text
Hermes gateway = brain
MCP servers = controlled hands
sandbox jobs = disposable workspace
NetworkPolicy = boundary
RBAC = permission
PVC / Secrets = crown jewels
Audit log = accountability
```

Recommended high-level architecture:

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

The key principle is simple: do not allow the Hermes gateway to directly own every tool permission.

External input is also part of the security boundary. Messages from Discord, Telegram, Slack, webhooks, or forms should not be passed directly into the LLM and tool planner without preprocessing. The ingress or gateway layer should add source verification, rate limiting, content filtering, and basic sanitization, such as limiting message size, rejecting suspicious attachments, and flagging prompts that ask the model to ignore system instructions, reveal secrets, or execute shell commands. These events should also be written to audit logs. This does not fully solve prompt injection, but it reduces the chance that cheap, obvious malicious input immediately reaches the tool layer.

## 3. Keep the Gateway Least-Privileged

The Hermes gateway is the core service, but it should not have Kubernetes administration privileges, direct shell execution privileges, or access to the Docker socket.

Recommended restrictions:

1. Do not grant `cluster-admin`.
2. Do not mount the Docker socket.
3. Do not mount `hostPath`.
4. Do not run as a privileged container.
5. Do not use `hostNetwork`.
6. Do not allow privilege escalation.
7. Do not automatically mount the Kubernetes service account token.

Example ServiceAccount:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: hermes-gateway
  namespace: hermes-system
automountServiceAccountToken: false
```

Example pod security settings:

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

With this posture, even if the gateway is manipulated through prompt injection, it does not automatically have a Kubernetes API token, host filesystem access, Docker socket access, or privileged container capabilities.

`readOnlyRootFilesystem: true` is useful hardening, but it may conflict with real Hermes behavior. Hermes may need to write to `/tmp`, cache, logs, plugin state, SQLite, or session files. If the root filesystem is read-only, explicitly mount writable paths such as `/opt/data`, `/tmp`, and required cache directories. Production deployments should first identify the actual write paths, then narrow the writable surface as much as possible.

In the recommended architecture, `hermes-system` should be treated as the core reasoning zone, with the gateway constrained through ServiceAccount configuration, Pod Security Standards, NetworkPolicy, and PVC controls.

`replicas: 1` is a conservative starting point, not a high-availability architecture. The reason is to avoid multiple gateway replicas writing concurrently to the same `/opt/data` PVC and corrupting or racing over session, memory, or SQLite state. It also means the gateway becomes a single point of failure. If production requires HA, handle the state layer before scaling replicas:

1. Use ReadWriteMany storage such as NFS, CephFS, EFS, or another multi-writer storage class, and validate that Hermes can safely handle concurrent file access.
2. Move session, memory, queue, and approval state to Redis, PostgreSQL, or a dedicated state service so the gateway can become mostly stateless.
3. Keep tool execution state in the tool router, Job controller, or workflow engine rather than in the gateway local filesystem.
4. Add readiness probes, PodDisruptionBudgets, rolling updates, and short timeouts so node maintenance does not remove the only entry point.

If state cannot be externalized or RWX storage cannot be validated, `replicas: 1` is safer but less available. Scaling out should be treated as a state-consistency architecture problem, not just a Deployment setting.

## 4. Treat `/opt/data` as Highly Sensitive

Hermes may store configuration, API keys, sessions, skills, and memories under `/opt/data`. This directory is a sensitive data zone and should not be shared with general-purpose tools or sandbox workloads.

Ideally, `/opt/data` should not directly store long-lived API keys or high-privilege tokens. Credentials should be separated into Kubernetes Secret, External Secrets, Vault, or a cloud secret manager. `/opt/data` should primarily store Hermes runtime state, memory, non-secret configuration, and required session metadata. If Hermes still writes tokens into `/opt/data` in practice, the PVC must be treated as secret-equivalent storage: encrypted, backed up carefully, mounted narrowly, protected from snapshot access, and audited.

In Kubernetes, `/opt/data` should be managed explicitly through a PVC:

```text
/opt/data PVC
- Read/write only by Hermes gateway
- Dashboard should not mount the full /opt/data directory directly
- Sandbox pods must not mount it
- Multiple gateway replicas should not write to the same PVC concurrently
- Use an encrypted storage class
- Take regular snapshots and backups
```

This is more controllable than scattering sensitive agent data across a single host filesystem. It also enables clearer backup, encryption, access control, and audit policies.

Even a read-only dashboard mount of `/opt/data` can leak secrets, because reading a secret is itself high risk. A safer design is for the dashboard to obtain filtered state through the Hermes gateway or a metadata API, rather than directly reading API keys, session files, raw memory files, or credentials.

## 5. Use NetworkPolicy as a Default-Deny Boundary

Hermes should not run in an environment where every pod can freely connect to every service or to the internet.

Important: NetworkPolicy is not a firewall rule executed by the kube-apiserver. It must be implemented by the CNI plugin. If the CNI does not support NetworkPolicy, for example in some default or simplified environments, default deny may not actually take effect. Production should explicitly use a CNI that supports NetworkPolicy, such as Calico, Cilium, or OVN-Kubernetes, and verify enforcement with test pods.

Each namespace should start with a default-deny NetworkPolicy:

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

Then allow only required traffic:

```text
Ingress Controller -> Hermes Gateway
Hermes Gateway -> MCP servers
Hermes Gateway -> LLM serving
Pods -> CoreDNS
```

For example, Hermes gateway should only be allowed to call tool and model namespaces:

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

Production should not rely only on `namespaceSelector`. It should also restrict `podSelector` and `ports`, so the gateway cannot connect to every unexpected service in an allowed namespace.

If Hermes must call external LLM APIs such as OpenAI, Anthropic, or Gemini, native Kubernetes NetworkPolicy is not sufficient for FQDN-level control. Consider Cilium FQDN policies, an egress gateway, a service mesh, or centralizing all external LLM calls through an `llm-proxy`.

## 6. Separate Tool Execution from the Gateway

The highest-risk part of Hermes is usually not the model response. It is tool execution. Shell access, browser automation, and code runners are high-risk capabilities.

The Hermes gateway should not directly run local shell commands inside the same pod. A safer architecture is:

```text
Hermes Gateway
    -> Tool Router / MCP Server
        -> Kubernetes Job / Sandbox Pod
```

In other words:

```text
Do not:
Hermes gateway directly executes shell commands

Recommended:
Hermes submits task -> sandbox job executes -> result is returned
```

The sandbox namespace should be stricter than the gateway namespace. Standard container isolation is not a strong sandbox. If the sandbox executes untrusted code, browses unknown webpages, or runs externally supplied scripts, Kubernetes Pod isolation alone is not enough. Prefer gVisor, Kata Containers, or Firecracker-style isolation, combined with seccomp, AppArmor, read-only root filesystem, no service account token, no `hostPath`, no privileged mode, and either no egress or allowlisted egress.

1. Do not mount Hermes `/opt/data`.
2. Do not mount `hostPath`.
3. Do not automatically mount a Kubernetes service account token.
4. Deny internet egress by default.
5. Allow network access only through explicit allowlists.
6. Use a Job or ephemeral workspace for each task.
7. Limit CPU, memory, disk, and process count.
8. Return results only through a controlled API or object storage path.

This makes tool execution disposable, bounded, and auditable instead of allowing long-lived risk to accumulate inside the gateway.

## 7. Split MCP by Permission Scope

Hermes should not rely on one all-powerful MCP server. MCP servers should be split by capability and permission boundary:

```text
calendar-mcp
  - Holds only the Google Calendar token
  - Can only create / query events

discord-mcp
  - Holds only the Discord bot token
  - Can only manage approved servers / channels

github-mcp
  - Holds only a GitHub fine-grained token
  - Can only access approved repositories

k8s-readonly-mcp
  - Can only get/list/watch pods, deployments, and logs
  - Cannot create/delete/patch
  - Cannot read secrets

k8s-admin-mcp
  - Disabled by default
  - Requires human approval
  - Uses short-lived tokens
```

Kubernetes MCP should start as read-only and allow only resources such as:

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

It should not allow:

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

This ensures that even if Hermes is manipulated into using a tool, the blast radius is limited to the permissions that were explicitly approved in advance.

Gateway-to-MCP calls also need authentication; NetworkPolicy is not enough. NetworkPolicy can restrict which pods can connect, but if an attacker gains control of a pod that can reach an MCP server, they may try to call it directly and bypass the gateway's policy decision. Production should use at least one form of service-to-service authentication:

1. Service mesh mTLS, such as Istio, Linkerd, or Cilium service mesh, so the MCP server can verify the caller workload identity.
2. Short-lived API tokens or signed requests from gateway to MCP, with the MCP server verifying audience, issuer, expiry, and scope.
3. A centralized tool router that proxies MCP calls, where MCP servers accept only the tool router identity and reject direct calls from general pods.
4. Request-level authorization for high-risk MCP calls, checking user, agent, tool, action, resource, and approval id.

In other words, MCP servers should not trust requests merely because they come from inside the cluster. NetworkPolicy, mTLS, token scope, and audit logs should be used together.

## 8. Govern Skills and Long-Term Memory

AI agent risk does not only come from the gateway or MCP servers. It also comes from extensible skills and long-term memory.

Third-party skills should go through a formal review process before installation:

1. Do not install unreviewed skills directly into the production gateway.
2. Review skill source code manually.
3. Use tools such as Trivy, Grype, Semgrep, and secret scanning to detect suspicious behavior.
4. Treat skills as high-risk if they download external files, connect to unknown domains, execute shell commands, read tokens, or modify memory.
5. Production should only allow skills from an internal registry or an approved allowlist.

Long-term memory should also be treated as part of the security control plane. If Hermes relies on memory or system instructions to enforce security rules, those rules should not exist only in short-lived conversation context. Long-running agents or context compression may cause safety rules to be lost.

Recommended practices:

1. Write non-removable safety restrictions into core memory or startup configuration.
2. Put core safety rules under version control.
3. Regularly back up and review memory files.
4. Create audit logs for memory changes.
5. Do not allow the agent to remove high-risk safety rules without human approval.

Examples:

```text
- Human approval is required before deleting data.
- Human approval is required before sending external emails or messages.
- Human approval is required before accessing secrets, credentials, or tokens.
- Human approval is required before running shell, browser automation, or Kubernetes mutation.
- /opt/data, sessions, memory, and credentials must not be sent to external services.
```

The human approval gate should not be just the model asking "Are you sure?" A better design is to enforce approval in the tool router or policy engine, not in the LLM's self-restraint. High-risk tool calls should first produce a dry-run plan with target, parameters, blast radius, and rollback strategy. A human then approves the request in an independent UI, CLI, or chat command. The approval record should be written to audit logs and tied to user, time, tool call, parameters, and execution result.

A practical approval flow can look like this:

```text
1. LLM generates a tool intent
2. Tool router classifies action risk
3. High-risk action creates pending approval only; it does not execute
4. Slack / Teams / Web UI / CLI displays the dry-run plan
5. Human approval issues a short-lived approval token
6. Tool router verifies approval token, action hash, expiry, and approver
7. Tool call executes
8. Audit log and execution result are written
```

The approval token should be bound to a specific action, not act as a general pass. It should include at least tool name, action, resource, arguments hash, approver, expiry, and request id. If parameters change after approval, the previous approval should become invalid. If implemented with Kubernetes Jobs, the tool router can create a `PendingApproval` custom resource or queue item first, and an approval controller can create the real execution Job only after receiving an external webhook.

## 9. Do Not Expose the Dashboard or Gateway Directly to the Internet

The Hermes gateway may provide API and health endpoints. The dashboard is an administrative interface. Neither should be directly exposed to the internet.

Recommended posture:

```text
gateway:
  Expose only required endpoints behind ingress authentication

dashboard:
  Restrict to VPN / Tailscale / Cloudflare Access / oauth2-proxy
  Admin access only
```

Port-forwarding is acceptable for testing. Production should use controlled ingress and should avoid directly exposing gateway or dashboard ports to the internet.

Ingress / WAF should not remain just a box in the diagram. Production should explicitly define:

1. Authentication: OAuth2/OIDC, Cloudflare Access, Tailscale ACL, mTLS client certificates, or an enterprise IdP. A hidden URL is not enough.
2. Authorization: separate normal users, operators, and admins. Dashboard and tool approval UI should be available only to narrow roles.
3. Rate limiting: limit by user, source IP, channel, and agent id to avoid external messages triggering excessive agent work or LLM API spend.
4. Request constraints: limit body size, attachment types, URL-fetch behavior, and webhook replay windows.
5. WAF / bot rules: block obvious scanning, brute-force attempts, abnormal user agents, and known attack payloads.
6. Audit: record who triggered which agent request from which entry point, after secret and PII redaction.

Rate limiting is especially important for chat integrations. Discord, Telegram, Slack, and webhooks can all trigger large volumes of agent work, causing repeated tool planning, LLM calls, or external API calls. The entry layer should enforce per-channel, per-user, per-agent, and global quotas; high-risk actions should have even lower limits and require approval.

## 10. Split Secrets by Service

At minimum, Kubernetes Secret can be used, but Kubernetes Secret is not a complete solution. Secret values are base64 encoded by default, which is not encryption. Production should enable etcd encryption at rest or use External Secrets, Vault, or a cloud secret manager. A more mature enterprise setup may use:

```text
External Secrets Operator + cloud secret manager
Sealed Secrets
SOPS + age
Vault
```

Secrets should be split by service:

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

Do not put every token into the Hermes gateway pod. The reason is straightforward: if the gateway is manipulated through prompt injection, it should have as few usable permissions as possible.

## 11. Kubernetes Integrates with Existing Security Governance

Another advantage of running Hermes on Kubernetes is that it can be integrated with existing platform security and governance tooling:

```text
Prometheus / Grafana    metrics
Loki                    logs
Kubernetes audit log    API operation records
Kyverno / Gatekeeper    admission policy
Trivy / Grype           image scanning
Falco                   runtime detection
cosign                  image signing
External Secrets        secret lifecycle management
```

This makes Hermes more than a running container. It allows Hermes to become part of the enterprise's existing security monitoring, compliance, audit, and operational governance model.

The observability stack should also be treated as a sensitive system. Tool-call logs, prompts, responses, and error traces may contain credentials, personal data, or confidential content, including user input, tool arguments, API responses, email, calendar, repository, chat content, or secrets leaked in stack traces. Production should include secret redaction, PII redaction, log retention policy, access control, and audit logs for queries.

## 12. Mapping to the Administration for Cyber Security's Five AI Agent Safeguards

Taiwan's Administration for Cyber Security published an advisory on AI agent risk and recommended five safeguards. The advisory discusses OpenClaw, not Hermes itself. The mapping below does not claim that the two systems have the same architecture; it uses a Hermes-like agentic tool-use architecture to map the same class of AI agent risks to the safeguards:

| ACS recommendation | Hermes on Kubernetes control |
| --- | --- |
| Enforce environment isolation | Use separate namespaces such as `hermes-system`, `hermes-tools`, `hermes-sandbox`, and `llm-serving`; run shell, browser, and code execution inside sandbox Jobs. |
| Minimize external account privileges | Use separate tokens for Calendar, Discord, GitHub, and Kubernetes MCP; use GitHub fine-grained tokens; start Kubernetes access with read-only MCP. |
| Add human review mechanisms | Require human approval for deleting data, sending messages, accessing credentials, running shell, or performing Kubernetes mutations. |
| Personally review skill extensions | Review and scan third-party skills before production use; allow only approved skills; do not install unreviewed skills directly into the gateway. |
| Write safety rules into long-term memory | Store core safety rules in startup configuration or core memory; version, back up, review, and audit changes. |

Reference: [Administration for Cyber Security press release, 2026-03-25: AI agent security advisory and five safeguards for OpenClaw adoption](https://moda.gov.tw/ACS/press/news/press/19294).

## 13. Deployment Trade-Offs and Operational Cost

The architecture above is closer to an enterprise or high-risk security baseline. Its main value is limiting unauthorized operations caused by prompt injection, but it increases latency, operational complexity, and platform requirements. Before adopting it, confirm whether the team can operate Kubernetes, CNI policy, sandbox runtimes, GitOps, and observability, and whether the product experience can tolerate sandbox startup latency.

The first trade-off is latency. Running every high-risk tool call as a Kubernetes Job or a fresh sandbox Pod improves isolation, but starting a Pod often takes one to several seconds. If image pull, admission webhooks, runtime sandboxing, or node scheduling are slow, latency can be higher. AI agents often use ReAct-style loops: think, write code, execute, inspect errors, modify, and execute again. If every code runner or browser call creates a new Pod, user-visible wait time can grow from seconds to tens of seconds or minutes.

In practice, treat sandboxing by risk tier:

1. Low-risk, short-lived operations can use a warm sandbox pool or prestarted workers, while still restricting tokens, filesystem access, and egress.
2. High-risk operations should use one-shot Jobs, stronger isolation, and stricter audit.
3. A single user task may reuse the same ephemeral sandbox for a limited time, then destroy it at task completion.
4. Common images should be pre-pulled to nodes, with resource requests set to avoid uncontrolled cold starts.
5. The tool router should record sandbox startup time, execution time, and queue time separately; otherwise UX latency is hard to debug.

The second trade-off is the limit of container isolation. Kubernetes Pods with Pod Security, seccomp, AppArmor, read-only root filesystem, no service account token, no `hostPath`, and no privileged mode reduce risk significantly, but ordinary Linux containers still share the host kernel. If the sandbox executes untrusted code, browses unknown webpages, extracts external files, or runs user-supplied scripts, treat gVisor, Kata Containers, or Firecracker-style isolation as a required control rather than a nice-to-have. Otherwise, kernel exploits or container-escape vulnerabilities may still expand the blast radius to the worker node.

The third trade-off is data transfer friction. It is correct that the gateway should not share `/opt/data` with the sandbox, but sandbox-generated files, reports, screenshots, ZIPs, and scraping results still need to get back to the user. Sharing a PVC reopens the isolation boundary. A safer pattern is:

1. The sandbox writes output to internal object storage such as S3, MinIO, or a cloud bucket.
2. The tool router returns only artifact id, metadata, hash, size, MIME type, and short-lived download URL.
3. The gateway reads only artifacts that passed scanning, size limits, and allowlist checks.
4. Artifacts go through malware scanning, content-type validation, secret scanning, and retention policy.
5. Large or sensitive outputs should not be inserted directly into prompt context; use summaries or references instead.

This means the system also needs an artifact service or internal object storage. That adds engineering and operational cost, but avoids giving the sandbox direct access to gateway state or Hermes memory.

The fourth trade-off is egress management. AI agents may need to call LLM APIs, GitHub, search services, documentation sites, package registries, or internal enterprise APIs. Endpoint IPs change frequently, so IP allowlists are hard to maintain. FQDN policy, egress gateways, or service mesh usually require Cilium, Istio, or equivalent platform capabilities, along with DNS policy, TLS inspection, certificates, sidecars, or eBPF datapath operations. For smaller teams, a practical starting point is to centralize outbound access through a few proxies, such as `llm-proxy`, `web-fetch-proxy`, and `package-proxy`, then gradually introduce finer egress policy.

The fifth trade-off is operational overhead. Splitting calendar, discord, github, k8s, browser, and code runner capabilities into separate MCP servers creates clearer security boundaries, but it also adds Deployments, ServiceAccounts, Secrets, RBAC, NetworkPolicies, Ingress rules, alerts, and dashboards. Without CI/CD, Helm or Kustomize, Terraform or Pulumi, Argo CD or Flux, policy-as-code, and automated validation, this can quickly become YAML hell. A more practical path is:

1. Group capabilities into low-risk, sensitive, and destructive tiers instead of creating a namespace for every small tool at the beginning.
2. Manage Kubernetes manifests through GitOps to avoid manual `kubectl` drift.
3. Package MCP servers, Secrets, NetworkPolicies, and ServiceAccounts as reusable templates.
4. For every new Skill or MCP server, automatically generate a threat model, RBAC diff, egress diff, and approval policy.
5. Validate security policy in CI, for example by rejecting privileged pods, `hostPath`, `cluster-admin`, or Secrets without owner labels.

Therefore, this architecture is best suited for bank-grade, enterprise, multi-tenant, or untrusted-tool execution environments. For a personal experiment or a small internal bot, it may be better to start with a few high-value controls: no Docker socket, no cluster-admin, split Secrets, restrict egress, keep audit logs, and require human approval for destructive actions. Upgrade to full Kubernetes sandboxing and stronger runtimes when the system reaches production, multi-tenant use, or high-risk tool execution.

## 14. Recommended Production Security Baseline

The first production version should implement at least:

1. Hermes gateway replicas = 1.
2. If HA is required, use RWX storage or externalize session, memory, and approval state before scaling the gateway.
3. `/opt/data` uses a PVC and is treated as sensitive data.
4. Namespaces enforce Pod Security `restricted`.
5. Use a CNI that supports NetworkPolicy enforcement and verify that default deny actually works.
6. Gateway does not mount a Kubernetes service account token.
7. Docker socket is not mounted.
8. `hostPath` is not used.
9. Dashboard is not exposed to the internet.
10. Ingress uses explicit authentication such as OAuth/OIDC, VPN, Cloudflare Access, Tailscale ACL, or mTLS.
11. External input channels have rate limiting, source verification, and basic content filtering.
12. MCP servers are split by permission and do not share tokens.
13. Gateway-to-MCP calls use mTLS, short-lived API tokens, signed requests, or service mesh identity.
14. Sandbox pods do not mount the Hermes PVC.
15. Kubernetes MCP starts as read-only.
16. High-risk operations require human approval enforced by a tool router or policy engine.
17. Approval tokens are bound to action hash, resource, expiry, and approver.
18. Third-party skills require security review and allowlisting.
19. Core safety rules are stored in startup configuration or long-term memory, with backup and audit controls.
20. Secrets use etcd encryption at rest, or External Secrets, Vault, or a cloud secret manager.
21. Observability, logs, memory, and session files are handled as sensitive data.

Advanced controls:

1. Run sandbox workloads with gVisor, Kata Containers, or Firecracker.
2. Use Cilium FQDN egress policy.
3. Enforce admission policy with OPA Gatekeeper or Kyverno.
4. Use image signing with cosign.
5. Scan images with Trivy or Grype.
6. Use Falco for runtime detection.
7. Store tool-call logs in Loki.
8. Require human approval for destructive actions.
9. Audit all agent tool calls.
10. Use a separate namespace and PVC per user or per agent.
11. Use a skill registry allowlist and admission policy.
12. Add memory file integrity checks and change notifications.
13. In multi-tenant environments, use per-user or per-agent namespaces, ServiceAccounts, PVCs, Secrets, quotas, and NetworkPolicies.

Multi-tenant deployments should be more conservative. If multiple users, teams, or agents share a cluster, do not rely only on an application-level tenant id to separate data. A safer baseline gives each tenant or high-risk agent an isolated namespace, PVC, Secret, ServiceAccount, ResourceQuota, LimitRange, NetworkPolicy, and audit labels. Then a prompt injection or tool misuse in one agent does not naturally expose another tenant's memory, sessions, tokens, or sandbox output.

## 15. Conclusion

The security value of running Hermes on Kubernetes is not merely containerization. It is the ability to build a security architecture suitable for agentic AI systems.

The Hermes gateway handles reasoning and decisions, but it does not directly own every action permission. MCP servers are split by permission scope. Sandbox Jobs handle high-risk execution. NetworkPolicy creates boundaries. RBAC controls Kubernetes access. PVCs and Secrets are treated as crown jewels. Audit logs provide traceability and accountability.

For enterprise environments, Hermes on Kubernetes is a stronger security architecture because it makes agent capabilities separable, restrictable, observable, and auditable.

A secure Hermes deployment is not just about running a Hermes pod. It is about separating the reasoning layer from the action layer from day one.
