# Why Kubernetes Is a Strong Security Architecture for Hermes AI

## Executive Summary

Hermes should not be treated as a simple chat service. It is an agentic system with tool-use capabilities. In practice, it may hold API keys, bot tokens, sessions, memory, and access to systems such as Discord, Telegram, Slack, GitHub, Google Calendar, Kubernetes, databases, browsers, and automation tools.

The primary security risk is not conversation itself. The risk is that external input or prompt injection may cause Hermes to invoke privileged tools or perform high-impact actions. Recent threat-modeling work on LLM-agent workflows similarly argues that systems with structured function calling, plugins, connectors, and agent protocols expand the attack surface from simple inputs to tools, protocols, and workflows [3].

Deploying Hermes on Kubernetes is valuable because it separates the "reasoning layer" from the "action layer" and uses Kubernetes-native controls for isolation, authorization, network boundaries, resource limits, and auditability.

In one sentence:

> Hermes gateway should handle conversation and decision-making only; high-risk tool execution, MCP, browser automation, Calendar, GitHub, and Kubernetes operations should be separated and controlled through Kubernetes isolation, authorization, network policy, and audit mechanisms.

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

The value of Kubernetes is that these capabilities can be separated, isolated, restricted, and audited. This direction is also aligned with recent AI agent security research. Zhang et al. argue that LLM agents deployed at scale should explicitly adopt traditional security principles such as defense-in-depth, least privilege, and complete mediation [1].

This risk model is also aligned with the AI agent security advisory published by Taiwan's Administration for Cyber Security on 2026-03-25. The advisory emphasizes that AI agent risk is not merely a single-vulnerability problem; it is an architectural and systemic risk. It highlights malicious instructions embedded in external webpages or social content, malicious third-party skills, and the possibility that long-running agents may lose safety rules after context compression [9].

## 2. Kubernetes Provides Security Layering for AI Agents

Hermes can be split across multiple Kubernetes namespaces, each with a different security policy:

```text
hermes-system      Hermes Gateway / Dashboard
hermes-tools       MCP Servers / Skills backend
hermes-sandbox     Shell / Browser / Code Runner
llm-serving        Ollama / vLLM / local model serving
observability      Logs / Metrics / Audit
```

This follows a defense-in-depth model. Prior research argues that agentic systems should not rely only on the model's own refusal behavior, but should embed security principles throughout the agent lifecycle and execution environment [1]:

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
```

With this posture, even if the gateway is manipulated through prompt injection, it does not automatically have a Kubernetes API token, host filesystem access, Docker socket access, or privileged container capabilities. This is consistent with privilege-usage research showing that when real-world tools are granted to an LLM agent, the associated privileges are effectively granted to the agent and the underlying model; therefore, the execution environment must explicitly constrain tool permissions [2].

In the recommended architecture, `hermes-system` should be treated as the core reasoning zone, with the gateway constrained through ServiceAccount configuration, Pod Security Standards, NetworkPolicy, and PVC controls.

## 4. Treat `/opt/data` as Highly Sensitive

Hermes stores configuration, API keys, sessions, skills, and memories under `/opt/data`. This directory is a sensitive data zone and should not be shared with general-purpose tools or sandbox workloads.

In Kubernetes, `/opt/data` should be managed explicitly through a PVC:

```text
/opt/data PVC
- Read/write only by Hermes gateway
- Dashboard should preferably mount it read-only
- Sandbox pods must not mount it
- Multiple gateway replicas should not write to the same PVC concurrently
- Use an encrypted storage class
- Take regular snapshots and backups
```

This is more controllable than scattering sensitive agent data across a single host filesystem. It also enables clearer backup, encryption, access control, and audit policies.

## 5. Use NetworkPolicy as a Default-Deny Boundary

Hermes should not run in an environment where every pod can freely connect to every service or to the internet.

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
  - to:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: llm-serving
```

If Hermes must call external LLM APIs such as OpenAI, Anthropic, or Gemini, native Kubernetes NetworkPolicy is not sufficient for FQDN-level control. Consider Cilium FQDN policies, an egress gateway, a service mesh, or centralizing all external LLM calls through an `llm-proxy`.

## 6. Separate Tool Execution from the Gateway

The highest-risk part of Hermes is usually not the model response. It is tool execution. Shell access, browser automation, and code runners are high-risk capabilities. GrantBox shows that even when models exhibit basic security awareness, they can still misuse real tool privileges under carefully crafted prompt-injection scenarios [2].

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

The sandbox namespace should be stricter than the gateway namespace:

1. Do not mount Hermes `/opt/data`.
2. Do not mount `hostPath`.
3. Do not automatically mount a Kubernetes service account token.
4. Deny internet egress by default.
5. Allow network access only through explicit allowlists.
6. Use a Job or ephemeral workspace for each task.
7. Limit CPU, memory, disk, and process count.
8. Return results only through a controlled API or object storage path.

This makes tool execution disposable, bounded, and auditable instead of allowing long-lived risk to accumulate inside the gateway. Kubernetes and Google Cloud have also introduced Agent Sandbox designs for AI agent runtimes, with the same goal of isolating agent workspaces, untrusted code execution, process boundaries, storage, and network access [6][7][8].

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

This ensures that even if Hermes is manipulated into using a tool, the blast radius is limited to the permissions that were explicitly approved in advance. This is aligned with MCP-Secure, which argues that MCP tool use should enforce scoped access, read-only defaults, and approval-gated privilege elevation instead of giving the agent full tool authority by default [5].

## 8. Govern Skills and Long-Term Memory

AI agent risk does not only come from the gateway or MCP servers. It also comes from extensible skills and long-term memory. LLM-agent ecosystem research identifies plugins, connectors, MCP, agent-to-agent protocols, and memory subversion as important attack surfaces in agent workflows [3].

Third-party skills should go through a formal review process before installation:

1. Do not install unreviewed skills directly into the production gateway.
2. Review skill source code manually.
3. Use tools such as Trivy, Grype, Semgrep, and secret scanning to detect suspicious behavior.
4. Treat skills as high-risk if they download external files, connect to unknown domains, execute shell commands, read tokens, or modify memory.
5. Production should only allow skills from an internal registry or an approved allowlist.

Long-term memory should also be treated as part of the security control plane. If Hermes relies on memory or system instructions to enforce security rules, those rules should not exist only in short-lived conversation context. Long-running agents or context compression may cause safety rules to be lost. Instruction hierarchy research identifies a core prompt-injection problem: models may confuse privileged system instructions with lower-priority external content, which means safety rules need stronger protection and enforcement boundaries than ordinary context [4].

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

## 10. Split Secrets by Service

At minimum, Kubernetes Secret can be used. A more mature enterprise setup may use:

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

## 12. Mapping to the Administration for Cyber Security's Five AI Agent Safeguards

Taiwan's Administration for Cyber Security published an advisory on AI agent risk and recommended five safeguards [9]. Hermes on Kubernetes maps to those safeguards as follows:

| ACS recommendation | Hermes on Kubernetes control |
| --- | --- |
| Enforce environment isolation | Use separate namespaces such as `hermes-system`, `hermes-tools`, `hermes-sandbox`, and `llm-serving`; run shell, browser, and code execution inside sandbox Jobs. |
| Minimize external account privileges | Use separate tokens for Calendar, Discord, GitHub, and Kubernetes MCP; use GitHub fine-grained tokens; start Kubernetes access with read-only MCP. |
| Add human review mechanisms | Require human approval for deleting data, sending messages, accessing credentials, running shell, or performing Kubernetes mutations. |
| Personally review skill extensions | Review and scan third-party skills before production use; allow only approved skills; do not install unreviewed skills directly into the gateway. |
| Write safety rules into long-term memory | Store core safety rules in startup configuration or core memory; version, back up, review, and audit changes. |

## 13. Literature Basis and Argument Mapping

I did not find a paper specifically about "Hermes on Kubernetes." This document therefore uses a paper-style argument: related research supports the architectural principles, and those principles are then mapped to Hermes on Kubernetes. The common direction across recent research and official materials is that AI agents should use isolation, least privilege, tool permission control, sandboxing, human approval, and protocol/MCP security design [1][2][3][5][6][7][8].

| Citation | Relevance to this document |
| --- | --- |
| [1] | Supports the overall principles of defense-in-depth, least privilege, and complete mediation; these map to namespace isolation, RBAC, NetworkPolicy, and MCP permission separation. |
| [2] | Supports the claim that the gateway should not directly own all tool permissions, and that high-risk tools should require sandboxing and human approval. |
| [3] | Supports the Hermes threat model, especially prompt injection, plugins, connectors, MCP, agent-to-agent protocols, and memory subversion. |
| [4] | Supports the argument that prompts alone are insufficient and external enforcement through Kubernetes, RBAC, and NetworkPolicy is required. |
| [5] | Supports `k8s-readonly-mcp`, disabled-by-default `k8s-admin-mcp`, and human approval gates. |
| [6][7][8] | Support the `hermes-sandbox` namespace, sandbox Jobs, gVisor/Kata, untrusted code execution isolation, and controlled workspaces. |

Therefore, this document does not claim that academia has proven Hermes must run on Kubernetes. The more accurate claim is that current AI agent security research and Kubernetes platform direction point toward the same design principles: defense-in-depth, least privilege, runtime access control, sandboxed execution, and human approval. Kubernetes provides a practical platform for implementing those controls.

## 14. Recommended Production Security Baseline

The first production version should implement at least:

1. Hermes gateway replicas = 1.
2. `/opt/data` uses a PVC and is treated as sensitive data.
3. Namespaces enforce Pod Security `restricted`.
4. NetworkPolicy uses default deny.
5. Gateway does not mount a Kubernetes service account token.
6. Docker socket is not mounted.
7. `hostPath` is not used.
8. Dashboard is not exposed to the internet.
9. MCP servers are split by permission and do not share tokens.
10. Sandbox pods do not mount the Hermes PVC.
11. Kubernetes MCP starts as read-only.
12. Destructive actions require human approval.
13. Third-party skills require security review and allowlisting.
14. Core safety rules are stored in startup configuration or long-term memory, with backup and audit controls.

Advanced controls:

1. Run sandbox workloads with gVisor or Kata Containers.
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

## 15. References

[1] Kaiyuan Zhang, Zian Su, Pin-Yu Chen, Elisa Bertino, Xiangyu Zhang, Ninghui Li, [LLM Agents Should Employ Security Principles](https://arxiv.org/abs/2505.24019), arXiv:2505.24019, 2025.

[2] Quan Zhang, Lianhang Fu, Lvsi Lian, Gwihwan Go, Yujue Wang, Chijin Zhou, Yu Jiang, Geguang Pu, [Evaluating Privilege Usage of Agents with Real-World Tools](https://arxiv.org/abs/2603.28166), arXiv:2603.28166, 2026.

[3] Mohamed Amine Ferrag, Norbert Tihanyi, Djallel Hamouda, Leandros Maglaras, Abderrahmane Lakas, Merouane Debbah, [From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows](https://arxiv.org/abs/2506.23260), arXiv:2506.23260, 2025.

[4] Eric Wallace, Kai Xiao, Reimar Leike, Lilian Weng, Johannes Heidecke, Alex Beutel, [The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions](https://arxiv.org/abs/2404.13208), arXiv:2404.13208, 2024.

[5] Gamini Singh, Vijay K. Madisetti, [MCP-Secure: A Runtime Access Control Layer for Privilege-Aware LLM Agent Tooling](https://www.researchgate.net/publication/400740740_MCP-Secure_A_Runtime_Access_Control_Layer_for_Privilege-Aware_LLM_Agent_Tooling/download), IEEE Open Journal of the Computer Society, 2026.

[6] Kubernetes Blog, [Running Agents on Kubernetes with Agent Sandbox](https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/), 2026.

[7] Google Cloud Documentation, [Isolate AI code execution with Agent Sandbox](https://docs.cloud.google.com/kubernetes-engine/docs/how-to/agent-sandbox), 2026.

[8] Kubernetes SIG Apps, [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox), GitHub repository.

[9] Administration for Cyber Security, Ministry of Digital Affairs, Taiwan, [AI agent security advisory and five safeguards for OpenClaw adoption](https://moda.gov.tw/ACS/press/news/press/19294), 2026-03-25.

## 16. Conclusion

The security value of running Hermes on Kubernetes is not merely containerization. It is the ability to build a security architecture suitable for agentic AI systems.

The Hermes gateway handles reasoning and decisions, but it does not directly own every action permission. MCP servers are split by permission scope. Sandbox Jobs handle high-risk execution. NetworkPolicy creates boundaries. RBAC controls Kubernetes access. PVCs and Secrets are treated as crown jewels. Audit logs provide traceability and accountability.

For enterprise environments, Hermes on Kubernetes is a stronger security architecture because it makes agent capabilities separable, restrictable, observable, and auditable.

A secure Hermes deployment is not just about running a Hermes pod. It is about separating the reasoning layer from the action layer from day one.
