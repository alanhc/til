# Kubernetes as a Defense-in-Depth Platform for AI Agent Systems: A Security Architecture Design Using Hermes as an Example

**Alan Tseng**

---

## Abstract

Large language model (LLM)-driven agent systems are not merely text-generation services. They may also hold API credentials, tool-execution permissions, and long-term memory, giving them a much broader attack surface than traditional chat services. This paper uses Hermes, an AI agent system with tool-calling capabilities, as the subject of analysis and systematically discusses a security architecture for deploying it on Kubernetes. The core argument is that Kubernetes-native capabilities, including namespace isolation, role-based access control (RBAC), NetworkPolicy, Pod Security Standards, Persistent Volume management, and audit mechanisms, can establish effective security boundaries between an AI agent's "reasoning layer" (gateway) and "action layer" (tool execution). This paper also proposes permission-separated deployment strategies for Model Context Protocol (MCP) servers, sandboxed tool-execution isolation, runtime policy mechanisms, and governance frameworks for Skills and long-term memory. These design principles are aligned with recent AI agent security research on defense-in-depth, least privilege, and complete mediation [1][2][3].

**Keywords:** AI agent security, Kubernetes security architecture, prompt injection, MCP, least privilege, defense-in-depth, tool-execution isolation, LLM agent

---

## 1. Introduction

As LLM capabilities improve, AI agent systems based on function calling, tool use, and agent protocols are increasingly being deployed in enterprise production environments. The distinctive security challenge of these systems is that their risk does not come from model output alone, but from the **external tool actions** that the model may be induced to perform, including calling APIs, operating databases, executing shell commands, writing memory, or triggering automation workflows.

Hermes is an AI agent system with these capabilities. It may connect simultaneously to Discord, Telegram, Slack, GitHub, Google Calendar, Kubernetes clusters, and browser automation tools, while holding corresponding API keys, bot tokens, sessions, and long-term memory. As a result, Hermes' primary threat vector is not "conversation quality," but whether high-privilege tools can be abused through external input or prompt injection.

Zhang et al. (2025) point out that the threat model of LLM agents has expanded beyond input validation to include tools, protocols, and workflow layers [3]. Wallace et al. (2024) argue that security rules expressed only through prompts may be overridden when instruction-priority conflicts occur [4]. Together, these observations point to one conclusion: AI agent security cannot rely solely on the model itself. It must be enforced by the execution environment through external constraints.

This paper argues that Kubernetes provides an architectural foundation for meeting those requirements. Compared with single-node Docker deployment or VM deployment, Kubernetes' core advantage is that its namespace isolation, RBAC, NetworkPolicy, Pod Security Standards, PVC management, and audit log mechanisms can impose **mandatory, auditable, and fine-grained constraints** on the capability boundaries of AI agents without modifying the model itself.

Section 2 analyzes the Hermes threat model. Section 3 introduces the overall Kubernetes security architecture. Sections 4 through 9 discuss each security mechanism. Section 10 maps the design to existing regulatory guidance. Section 11 proposes a production security baseline. Section 12 concludes the paper.

---

## 2. Threat Model Analysis

### 2.1 Attack Surface Identification

Hermes' threat sources can be divided into the following categories:

**External input vectors:** Discord, Telegram, Slack, webhooks, and similar channels can all carry malicious instructions. Attackers may inject prompt-injection instructions, including indirect prompt injection, through messages, social comments, webpage content, and other external content [3].

**Tool-execution vectors:** Hermes may be induced to execute shell commands, browser automation, code runners, or direct Kubernetes API calls. Once high-risk tools are directly accessible from the gateway, the impact of prompt injection becomes equivalent to the permission scope of those tools [2].

**Credential-leakage vectors:** If API keys and bot tokens held by Hermes are colocated in the same runtime environment as the gateway, a single vulnerability may expose credentials for multiple services.

**Memory and Skill vectors:** If long-term memory can be modified by external input, attackers may plant persistent malicious instructions. If third-party Skills are not reviewed, they may directly introduce malicious code [3][9].

### 2.2 Core Risk Assumptions

This security design is based on the following assumption:

> **Any input from an external channel may contain malicious prompt-injection instructions; any tool output must not be treated as a trusted high-priority instruction.**

This assumption is also aligned with Saltzer and Schroeder's (1975) principle of complete mediation: every access to a protected resource must be authorized, rather than being authorized only once during initialization [1].

### 2.3 Sensitivity of `/opt/data`

Hermes' data directory, `/opt/data`, typically stores configuration, API keys, sessions, skills, and memories. It should be treated as enterprise "crown jewels" rather than as a normal application data directory. Access-control design for this directory directly affects the overall security posture.

---

## 3. Overall Security Architecture

### 3.1 Design Principles

The architecture in this paper follows these principles:

1. **Defense-in-depth:** Security controls are distributed across multiple layers, so the failure of a single layer does not cause full compromise.
2. **Least privilege:** Each component holds only the minimum permission set required to perform its function.
3. **Complete mediation:** Every tool call must be independently authorized.
4. **Explicit isolation:** The reasoning layer (gateway) and action layer (tool execution) are forcibly isolated through namespaces, NetworkPolicy, and RBAC.

### 3.2 Namespace Layering

In Kubernetes, Hermes is split across the following namespaces:

```text
hermes-system      Hermes Gateway, Dashboard
hermes-tools       MCP Servers (Calendar, Discord, GitHub, Kubernetes, etc.)
hermes-sandbox     Shell, Browser, Code Runner, and other high-risk tools
llm-serving        Ollama / vLLM / local or remote LLM services
observability      Prometheus, Loki, Grafana, audit logs
```

This layered architecture maps to the following security semantics:

```text
hermes-system    -> Reasoning layer: handles conversation and decisions, without directly holding action permissions
hermes-tools     -> Controlled action layer: holds scoped tokens for specific services
hermes-sandbox   -> Isolated execution layer: disposable and restricted workspace
llm-serving      -> Model inference layer: provides inference services to the gateway and tools
observability    -> Observability layer: collects audit and monitoring data across namespaces
```

### 3.3 Overall Architecture Diagram

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
|  - replicas: 1 *            |
|  - /opt/data PVC (RWO)      |
|  - no cluster-admin         |
|  - no hostPath              |
|  - no Docker socket         |
|  - no privileged container  |
|                             |
|  hermes-dashboard           |
|  - internal only            |
|  - admin access only        |
+-------------+---------------+
              |
              | service-to-service traffic only where explicitly allowed
              v
+-----------------------------+
| namespace: hermes-tools     |
|  calendar-mcp               |
|  discord-mcp                |
|  github-mcp                 |
|  k8s-readonly-mcp           |
+-------------+---------------+
              |
              v
+-----------------------------+
| namespace: hermes-sandbox   |
|  code-runner Job (ephemeral)|
|  browser-sandbox Pod        |
|  strict NetworkPolicy       |
|  no /opt/data mount         |
+-----------------------------+

+-----------------------------+    +-----------------------------+
| namespace: llm-serving      |    | namespace: observability    |
|  Ollama / vLLM / NIM        |    |  Prometheus / Loki / Grafana|
|  (or egress to cloud API)   |    |  tool-call audit log        |
+-----------------------------+    +-----------------------------+
```

> **\*** The technical limitation of `replicas: 1` comes from the PVC `ReadWriteOnce` (RWO) access mode. RWO allows only a single node to mount the volume for read/write access at a time. Forcing multiple replicas to write to `/opt/data` concurrently may cause race conditions and break data consistency. If high availability is required, use a storage class that supports `ReadWriteMany` (RWX), such as NFS or CephFS, together with application-level distributed locking.

---

## 4. Gateway Least-Privilege Design

### 4.1 Design Rationale

The Hermes gateway is the decision-making core of the system and is also the component most likely to become the target of prompt injection. Zhang et al. (2026) argue that once real-world tools are given to an LLM agent, the permissions attached to those tools are effectively transferred to the agent and its underlying model. Therefore, tool permissions must be explicitly constrained by the execution environment rather than relying only on the model's self-restraint [2].

Based on this, the gateway should follow these restrictions:

| Restriction | Rationale |
|---|---|
| Do not grant `cluster-admin` | Prevent the gateway from operating arbitrary Kubernetes resources |
| Do not mount the Docker socket | Prevent container escape to the host |
| Do not mount `hostPath` | Prevent access to the host filesystem |
| Do not use a `privileged` container | Prevent syscall-level privilege escalation |
| Do not use `hostNetwork` | Prevent bypassing NetworkPolicy |
| Do not allow privilege escalation | Prevent setuid/setcap-based escalation |
| `automountServiceAccountToken: false` | Prevent the gateway from holding a Kubernetes API token |

### 4.2 ServiceAccount Configuration

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: hermes-gateway
  namespace: hermes-system
automountServiceAccountToken: false
```

### 4.3 Pod Security Context Configuration

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

This configuration aligns with the `restricted` level of the Kubernetes Pod Security Standards (Kubernetes >= 1.25).

---

## 5. Sensitive Data Management

### 5.1 Access-Control Principles for `/opt/data`

`/opt/data` contains all sensitive operational data for Hermes and should be strictly controlled:

```text
/opt/data PVC access matrix:
  hermes-gateway     -> ReadWriteOnce (RWO)
  hermes-dashboard   -> ReadOnly (optional)
  hermes-tools       -> must not mount
  hermes-sandbox     -> must not mount
```

### 5.2 Split Secrets by Service

Minimize the exposure scope of Secrets. Each MCP service should hold only the credentials it requires:

```text
hermes-system/hermes-secret:
  LLM_API_KEY, GATEWAY_TOKEN

hermes-tools/calendar-mcp-secret:
  GOOGLE_OAUTH_CREDENTIAL

hermes-tools/discord-mcp-secret:
  DISCORD_BOT_TOKEN

hermes-tools/github-mcp-secret:
  GITHUB_FINE_GRAINED_TOKEN
```

More mature approaches can be used to manage the Secret lifecycle:

- **External Secrets Operator** + cloud secret management services such as AWS Secrets Manager or GCP Secret Manager
- **Sealed Secrets** for GitOps workflows
- **SOPS + age** for local encryption
- **HashiCorp Vault** for enterprise-grade secret management

---

## 6. Network Isolation Design

### 6.1 Default-Deny Policy

Each namespace should apply a default-deny NetworkPolicy so all traffic must be explicitly declared:

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

### 6.2 Allowed Traffic Paths

```text
Ingress Controller   -> hermes-gateway
hermes-gateway       -> hermes-tools (MCP servers)
hermes-gateway       -> llm-serving (model inference)
All pods             -> kube-system/CoreDNS (DNS resolution)
observability        -> All namespaces (metrics/log scraping)
```

### 6.3 Gateway Egress Example

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

### 6.4 FQDN Control for External LLM APIs

Native Kubernetes NetworkPolicy supports only IP CIDR rules and does not support DNS/FQDN rules. If Hermes must call external LLM APIs such as OpenAI, Anthropic, or Google Gemini, implement FQDN egress control through one of the following approaches:

- **Cilium FQDN Policy** for DNS-aware rules at the CNI layer
- **Egress Gateway** for centralized outbound proxying
- **llm-proxy middleware** to centralize all external LLM calls through a single proxy service

---

## 7. Tool-Execution Isolation

### 7.1 The Gateway Must Not Directly Execute High-Risk Tools

Shell, browser automation, and code runners are high-risk capabilities. Even if the model has basic safety awareness, carefully designed prompt-injection scenarios may still induce it to misuse tool permissions [2]. Therefore, **the gateway must not directly execute shell commands or local programs inside the same Pod**.

The recommended tool-execution path is:

```text
hermes-gateway
    -> Tool Router / MCP Server
        -> Kubernetes Job (ephemeral) / Sandbox Pod
            -> Execution result returned through API or object storage
```

This design makes each tool execution an independent, lifecycle-bound, resource-limited work unit.

### 7.2 Sandbox Namespace Security Restrictions

The `hermes-sandbox` namespace should apply stricter restrictions than the gateway namespace:

1. Do not mount the `hermes-system` `/opt/data` PVC.
2. Do not mount `hostPath`.
3. Set `automountServiceAccountToken: false`.
4. Default-deny internet egress through NetworkPolicy and allowlist only when needed.
5. Use a `Job` for each task (ephemeral and deleted after completion), not a long-running Pod.
6. Apply resource limits (`limits`) for CPU, memory, ephemeral storage, and pids.
7. Return execution results only through a controlled API or object storage, not through a shared volume.

Advanced isolation can use gVisor (`runsc`) or Kata Containers as the sandbox runtime to further isolate syscall-level risk. Kubernetes and Google Cloud have introduced Agent Sandbox designs for AI agent runtimes, with the goal of isolating agent workspaces, untrusted code execution, process boundaries, storage, and network boundaries [6][7][8].

---

## 8. MCP Server Permission Separation

### 8.1 Separation Principle

Hermes should not hold one all-powerful MCP server. After separation by capability, each MCP server should hold only the minimum token scope required by its service:

| MCP Server | Credential Held | Allowed Operations |
|---|---|---|
| `calendar-mcp` | Google OAuth credential | Create and query Calendar events |
| `discord-mcp` | Discord bot token | Manage specified servers/channels |
| `github-mcp` | GitHub fine-grained token | Operate specified repositories |
| `k8s-readonly-mcp` | Restricted RBAC ClusterRole | Read-only Kubernetes resources |
| `k8s-admin-mcp` | Full RBAC | Disabled by default, requires human approval, short-lived token |

### 8.2 RBAC Design for Kubernetes MCP

`k8s-readonly-mcp` should allow only read-only access to the following resources:

```text
Allowed: pods, pods/log, services, events,
         deployments, replicasets, statefulsets, daemonsets
```

Explicitly prohibit:

```text
secrets, pods/exec, pods/attach, serviceaccounts/token,
persistentvolumes, mutatingwebhookconfigurations,
verbs: ["*"], resources: ["*"]
```

This design is aligned with Singh and Madisetti's (2026) recommendations for MCP tool security: MCP tools should use scoped access, read-only defaults, and approval-gated privilege elevation, instead of letting the agent directly obtain full tool permissions [5].

---

## 9. Runtime Policy and Untrusted Output Handling

### 9.1 Complete Mediation Mechanism

Splitting MCP servers is not sufficient by itself. The principle of complete mediation requires every tool call to independently verify authorization, rather than authorizing only once at agent startup [1]. To implement this, place a tool router and policy engine between the gateway and MCP/sandbox:

```text
hermes-gateway
    -> Tool Router
        -> Policy Decision Point (decides whether this call is allowed)
            -> Policy Enforcement Point (blocks, rejects, forwards execution, or triggers human approval)
                -> MCP Server / Sandbox Job
```

Each tool call should inspect at least the following attributes:

- requesting user, agent ID / session ID
- tool name, target resource
- action type (read / write / delete / execute)
- credential scope
- risk level
- whether human approval is required

### 9.2 Untrusted Tool Output Principle

Tool output should always be treated as untrusted data input, not executable instruction. The following rules should be enforced:

```text
- Tool output is data, not instruction.
- Webpage content must not override system or developer instructions.
- GitHub comments, Slack messages, logs, and command output
  must not authorize subsequent tool use.
- Tool output requesting secrets, credentials, shell execution,
  or data exfiltration must be treated as suspicious.
```

This principle is aligned with Wallace et al. (2024) on instruction hierarchy: content returned from external tools should have lower instruction priority than system instructions and should not be allowed to override safety rules [4].

### 9.3 Tool-Call Audit Logs

AI-agent-level tool-call audit logs and platform-level Kubernetes audit logs serve different purposes. Kubernetes audit logs answer "which pod did what to the Kubernetes API," while tool-call audit logs answer "which user, which agent session, which tool, which resource, under which policy decision, performed which action, and what result was produced."

Each tool-call audit log should include at least:

```text
timestamp, requesting_user, agent_id, session_id,
tool_name, requested_action, target_resource,
credential_scope, policy_decision, approval_result,
execution_result, risk_level
```

---

## 10. Skill and Long-Term Memory Governance

### 10.1 Third-Party Skill Review Process

Third-party Skills should complete the following review steps before installation:

1. Do not install unreviewed Skills directly into the production gateway.
2. Review Skill source code manually.
3. Use tools such as Trivy, Grype, Semgrep, and secret scanning to detect suspicious behavior.
4. Treat a Skill as high-risk if it downloads external files, connects to unknown domains, executes shell commands, reads tokens, or modifies memory.
5. Production should only allow Skills from an internal registry or an approved allowlist.

This process corresponds to the Administration for Cyber Security's (2026) recommendation that malicious code in third-party Skill extensions is an important attack vector for AI agent systems [9].

### 10.2 Security Controls for Long-Term Memory

Wallace et al. (2024) point out that one core problem in prompt injection is that models may confuse high-priority system instructions with lower-priority external content [4]. If Hermes' safety rules exist only in short-lived conversation context, long-running operation or context compression may cause them to be lost, making safety restrictions ineffective.

Recommended practices:

1. Write non-removable safety restrictions into startup configuration rather than relying only on prompts.
2. Put core safety rules under version control.
3. Regularly back up and manually review memory files.
4. Create audit logs for memory changes.
5. Do not allow the agent to remove high-risk safety rules without human approval.

The following operation types should require human approval:

```text
- Deleting any persistent data (database records, files, memory)
- Sending external emails or messages
- Accessing Secrets, credentials, or tokens
- Executing shell commands, browser automation, or Kubernetes mutations
- Sending /opt/data, sessions, memory, or credentials to external services
```

---

## 11. Dashboard and Gateway Access Control

Hermes gateway API endpoints and the dashboard management interface should not be directly exposed to the public internet. The recommended access-control matrix is:

| Component | Access Method | Allowed Users |
|---|---|---|
| hermes-gateway | Expose only necessary endpoints after ingress authentication | Authorized users |
| hermes-dashboard | VPN / Tailscale / Cloudflare Access / oauth2-proxy | Administrators |

Testing environments may use `kubectl port-forward` to verify services. Production environments should use controlled Ingress and should not directly expose gateway or dashboard ports to the internet.

---

## 12. Platform Governance and Observability Integration

Hermes on Kubernetes can directly integrate with existing platform governance tools, bringing AI agent operation into the enterprise's existing security governance, monitoring, and compliance processes:

| Tool | Purpose |
|---|---|
| Prometheus / Grafana | System metrics monitoring |
| Loki | Centralized log storage, including tool-call logs |
| Kubernetes audit log | Kubernetes API operation records |
| Kyverno / OPA Gatekeeper | Admission policy enforcement |
| Trivy / Grype | Container image vulnerability scanning |
| Falco | Runtime anomaly detection |
| cosign | Container image signature verification |
| External Secrets Operator | Secret lifecycle management |

---

## 13. Mapping to Cybersecurity Regulatory Guidance

In its 2026 press release on AI agents becoming cybersecurity risks, Taiwan's Administration for Cyber Security proposed five safeguards for AI agent systems [9]. The Hermes on Kubernetes architecture maps to them as follows:

| ACS recommendation | Hermes on Kubernetes control |
|---|---|
| Enforce environment isolation | Use `hermes-system`, `hermes-tools`, `hermes-sandbox`, and `llm-serving` namespace isolation; run shell, browser, and code runners in sandbox Jobs |
| Minimize external account privileges | Use separate scoped tokens for Calendar, Discord, GitHub, and Kubernetes MCP; start Kubernetes access with read-only MCP; re-validate credential scope for every tool call |
| Add human review mechanisms | Add human approval gates for deleting data, sending messages, accessing credentials, executing shell commands, and Kubernetes mutations; record approval results |
| Personally review Skill extensions | Require manual code review, security scanning, and allowlisting for third-party Skills; prohibit direct production installation of unreviewed Skills |
| Write safety rules into long-term memory | Write core safety rules into startup configuration; include them in version control, backup, review, and change-audit processes |

---

## 14. Production Security Baseline

### 14.1 Minimum Requirements for the First Production Version

1. Hermes gateway `replicas: 1` due to PVC ReadWriteOnce limitations.
2. `/opt/data` uses a PVC and an encrypted storage class.
3. Namespaces enforce Pod Security Standards `restricted`.
4. NetworkPolicy uses default-deny-all.
5. Gateway sets `automountServiceAccountToken: false`.
6. Do not mount the Docker socket, do not use `hostPath`, and do not use privileged containers.
7. Dashboard is not directly exposed to the internet.
8. MCP servers are split by service and each holds its own independent token.
9. Sandbox pods do not mount the `hermes-system` PVC.
10. Kubernetes MCP starts as read-only and explicitly prohibits secrets, exec, and mutating operations.
11. Destructive actions require human approval.
12. Third-party Skills must complete security review and allowlist approval before use.
13. Core safety rules are written into startup configuration and included in backup and audit processes.
14. Every tool call must pass a policy check.
15. Tool output is treated as untrusted data and cannot directly authorize subsequent tool actions.
16. Tool-call audit logs include user, agent/session, tool, target, decision, approval, and result.

### 14.2 Advanced Security Hardening

1. Use gVisor (`runsc`) or Kata Containers as the sandbox runtime.
2. Use Cilium FQDN egress policy to control external API calls.
3. Use OPA Gatekeeper or Kyverno admission policy.
4. Use cosign image signing and verification.
5. Integrate Trivy/Grype image scanning into the CI/CD pipeline.
6. Use Falco for runtime anomaly detection.
7. Store tool-call audit logs centrally in Loki.
8. Use a separate namespace and PVC per user or per agent.
9. Use a Skill registry allowlist and admission policy.
10. Add memory file integrity checks and change notifications.
11. Use the tool router/policy engine as the unified Policy Enforcement Point for MCP and sandbox execution.
12. Apply schema validation, authn/authz, and rate limiting to MCP requests, tool-router requests, and agent-to-agent protocols.

---

## 15. Conclusion

This paper argues that the core security value of deploying Hermes on Kubernetes is that Kubernetes-native capabilities can impose mandatory external constraints on AI agent tool-execution capabilities without modifying the model itself.

Through namespace isolation (`hermes-system`, `hermes-tools`, `hermes-sandbox`), gateway least-privilege design, permission-separated MCP deployment, sandboxed tool execution, a runtime policy engine, NetworkPolicy boundary control, sensitive data management for PVCs and Secrets, Skill and memory governance, and tool-call-level audit logs, organizations can establish a production environment where AI agent capabilities can be separated, restricted, observed, and held accountable.

The architectural principles in this paper are aligned with the research directions of Zhang et al. (2025) [1], Zhang et al. (2026) [2], Ferrag et al. (2025) [3], and Wallace et al. (2024) [4]. They point to a shared conclusion: AI agent security cannot rely only on the model's own judgment. The execution environment must provide architectural enforcement of defense-in-depth, least privilege, and complete mediation.

A truly secure Hermes deployment should clearly separate the "reasoning layer" from the "action layer" from the first day of architecture design.

---

## References

[1] Kaiyuan Zhang, Zian Su, Pin-Yu Chen, Elisa Bertino, Xiangyu Zhang, Ninghui Li, "LLM Agents Should Employ Security Principles," arXiv:2505.24019, 2025. https://arxiv.org/abs/2505.24019

[2] Quan Zhang, Lianhang Fu, Lvsi Lian, Gwihwan Go, Yujue Wang, Chijin Zhou, Yu Jiang, Geguang Pu, "Evaluating Privilege Usage of Agents with Real-World Tools," arXiv:2603.28166, 2026. https://arxiv.org/abs/2603.28166

[3] Mohamed Amine Ferrag, Norbert Tihanyi, Djallel Hamouda, Leandros Maglaras, Abderrahmane Lakas, Merouane Debbah, "From Prompt Injections to Protocol Exploits: Threats in LLM-Powered AI Agents Workflows," arXiv:2506.23260, 2025. https://arxiv.org/abs/2506.23260

[4] Eric Wallace, Kai Xiao, Reimar Leike, Lilian Weng, Johannes Heidecke, Alex Beutel, "The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions," arXiv:2404.13208, 2024. https://arxiv.org/abs/2404.13208

[5] Gamini Singh, Vijay K. Madisetti, "MCP-Secure: A Runtime Access Control Layer for Privilege-Aware LLM Agent Tooling," *IEEE Open Journal of the Computer Society*, 2026.

[6] Kubernetes Blog, "Running Agents on Kubernetes with Agent Sandbox," 2026. https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/

[7] Google Cloud Documentation, "Isolate AI code execution with Agent Sandbox," 2026.

[8] Kubernetes SIG Apps, "kubernetes-sigs/agent-sandbox," GitHub repository. https://github.com/kubernetes-sigs/agent-sandbox

[9] Administration for Cyber Security, Ministry of Digital Affairs, Taiwan, "Beware of AI agents becoming cybersecurity risks: ACS reminds organizations to implement five cybersecurity safeguards when adopting AI agents," 2026-03-25. https://moda.gov.tw/ACS/press/news/press/19294
