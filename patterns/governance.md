<!-- blueprint
type: pattern
name: governance
version: 1.0.0
requires: [protocol/spec, protocol/types, protocol/identity, patterns/observability, patterns/messaging]
platform: any
tier: free
-->

# Governance Pattern

Policy definition, capability enforcement, behavioral boundaries,
approval authority, and compliance reporting for all Weblisk agents.
This pattern ensures agents operate within defined boundaries —
doing only what they're permitted to do, in the way they're
permitted to do it.

## Overview

Without governance, agents are trusted implicitly. The protocol
grants capabilities as string lists in tokens, but nothing prevents
an agent from acting outside its declared intent. This pattern adds
enforceable rules:

1. **Policy definition** — declarative rules for what agents can do
2. **Capability enforcement** — runtime validation beyond string matching
3. **Behavioral boundaries** — scope limits per agent kind and domain
4. **Approval authority** — who can approve what, with escalation
5. **Compliance reporting** — audit trail and conformance verification
6. **Agent directives** — runtime policy injection via governance endpoint

---

## Policy Definition

Policies are declarative rules that constrain agent behavior. They
are defined at the system level and enforced by the orchestrator
and agents.

### Policy Structure

```yaml
policies:
  <policy-name>:
    description: <one-line>
    scope: system | domain | agent
    target: <agent-name | domain-name | "*">
    rules:
      - rule: <rule-type>
        params: { ... }
    enforcement: enforce | audit | disabled
    severity: critical | high | medium | low
```

### Policy Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| description | string | yes | Human-readable purpose |
| scope | string | yes | `system` (all agents), `domain` (within domain), `agent` (single agent) |
| target | string | yes | Agent/domain name, or `*` for all |
| rules | []Rule | yes | Ordered list of rules to evaluate |
| enforcement | string | yes | `enforce` (block), `audit` (log only), `disabled` |
| severity | string | yes | Impact level of violations |

### Rule Types

| Rule Type | Description | Parameters |
|-----------|-------------|------------|
| `capability_required` | Agent must declare capability | `capability: <name>` |
| `capability_denied` | Agent must NOT have capability | `capability: <name>` |
| `resource_scope` | Restrict file/URL access to patterns | `allowed: [<globs>], denied: [<globs>]` |
| `rate_limit` | Maximum operations per time window | `max: <int>, window: <seconds>, operation: <name>` |
| `data_classification` | Restrict access to data by classification | `max_level: public | internal | confidential | restricted` |
| `time_window` | Restrict execution to time windows | `allowed_hours: [<start>-<end>], timezone: <tz>` |
| `approval_required` | Force approval for specific actions | `actions: [<action-names>]` |
| `output_restriction` | Restrict what an agent can produce | `denied_fields: [<field-paths>], max_changes: <int>` |
| `dependency_required` | Agent must have specific dependency | `agent: <name>, status: online` |

### Example Policies

```yaml
policies:
  work-agent-boundaries:
    description: Work agents cannot modify files outside their domain
    scope: system
    target: "*"
    rules:
      - rule: resource_scope
        params:
          allowed: ["$domain_root/**"]
          denied: [".weblisk/**", "config/**"]
    enforcement: enforce
    severity: high

  seo-write-limit:
    description: SEO agents can modify max 50 files per execution
    scope: domain
    target: seo
    rules:
      - rule: output_restriction
        params:
          max_changes: 50
    enforcement: enforce
    severity: medium

  critical-changes-approval:
    description: All critical-severity changes require admin approval
    scope: system
    target: "*"
    rules:
      - rule: approval_required
        params:
          actions: [apply_changes]
          condition: "severity == 'critical'"
    enforcement: enforce
    severity: critical
```

---

## Capability Enforcement

The protocol's capability system (`cap` claim in WLT tokens) is
extended with runtime enforcement:

### Capability Hierarchy

```
agent:*              → all agent operations
  agent:message      → send/receive messages
  agent:execute      → execute tasks
  agent:register     → register/deregister

file:*               → all file operations
  file:read          → read files
  file:write         → write/modify files
  file:delete        → delete files

workflow:*           → all workflow operations
  workflow:execute   → execute workflows
  workflow:approve   → approve workflow phases

http:*               → all HTTP operations
  http:get           → outbound GET requests
  http:send          → outbound POST/PUT/DELETE
  http:receive       → inbound webhook reception

database:*           → all storage operations
  database:read      → read from stores
  database:write     → write to stores

llm:*                → all LLM operations
  llm:chat           → conversational inference
  llm:embed          → embedding generation
```

### Enforcement Points

| Point | Enforcer | What's Checked |
|-------|----------|----------------|
| Registration | Orchestrator | Declared capabilities match allowed set |
| Task dispatch | Orchestrator/Domain | Caller has capability to reach target |
| Message send | Agent framework | Sender has `agent:message` capability |
| File access | Agent framework | Agent has `file:read`/`file:write` for path |
| HTTP outbound | Agent framework | Agent has `http:send` or `http:get` |
| Storage access | Agent framework | Agent has `database:read`/`database:write` |

### Enforcement Flow

```
1. Agent attempts an operation (file read, message send, etc.)
2. Framework intercepts the operation
3. Check agent's token capabilities against required capability
4. Check active policies for additional restrictions
5. If denied:
   a. Log governance violation event
   b. If enforcement = "enforce" → block operation, return FORBIDDEN
   c. If enforcement = "audit" → allow but log warning
6. If allowed → proceed
```

---

## Behavioral Boundaries

Each agent kind has inherent behavioral boundaries:

### Work Agents

```yaml
boundaries:
  can:
    - Execute tasks dispatched by their owning domain
    - Read files within their domain's scope
    - Send messages to collaborators declared in manifest
    - Propose changes (not apply directly)
  cannot:
    - Register workflows
    - Dispatch to other agents
    - Modify files directly (must propose changes)
    - Access other domains' data
    - Override governance policies
```

### Domain Controllers

```yaml
boundaries:
  can:
    - Execute workflows
    - Dispatch to their declared required_agents
    - Aggregate results
    - Apply approved changes within their domain scope
    - Send messages to infrastructure agents
  cannot:
    - Dispatch to agents outside their required_agents list
    - Access other domains' storage
    - Override system-level policies
    - Approve their own recommendations (separation of duties)
```

### Infrastructure Agents

```yaml
boundaries:
  can:
    - Respond to messages from any authenticated agent
    - Perform their declared function (send email, sync, schedule)
    - Access their own storage
  cannot:
    - Initiate work autonomously (except scheduled triggers)
    - Modify application data
    - Access other agents' storage
    - Bypass rate limits
```

---

## Approval Authority

Not all approvals are equal. The governance pattern defines an
approval authority matrix:

### Authority Levels

| Level | Who | Can Approve |
|-------|-----|-------------|
| `auto` | System | Low-risk changes matching auto-approval rules |
| `agent` | Domain controller | Medium-risk changes within domain scope |
| `operator` | Human operator | High-risk changes, cross-domain changes |
| `admin` | Administrator | Critical changes, policy overrides, system-level changes |

### Approval Matrix

```yaml
approval_authority:
  rules:
    - condition: "severity == 'low' AND confidence > 0.9"
      authority: auto
    - condition: "severity == 'medium'"
      authority: operator
    - condition: "severity == 'high'"
      authority: operator
    - condition: "severity == 'critical'"
      authority: admin
    - condition: "scope == 'cross-domain'"
      authority: admin
    - condition: "changes > 20"
      authority: operator

  escalation:
    timeout: 3600            # seconds before escalating
    escalate_to: admin       # escalation target
    notify: [alerting]       # notify via alerting agent
```

### Separation of Duties

| Rule | Enforcement |
|------|-------------|
| Agents cannot approve their own recommendations | Enforced by orchestrator |
| Domain controllers cannot approve cross-domain changes | Enforced by orchestrator |
| Critical changes require a different approver than the requester | Enforced by approval service |

---

## Governance Directives

Governance directives are delivered to agents via `POST /v1/message`
using the standard agent messaging protocol. Every agent that extends
this pattern MUST handle `governance.*` message actions:

### Request (via POST /v1/message)

```json
{
  "from": "orchestrator",
  "to": "seo-analyzer",
  "type": "request",
  "action": "governance.directive",
  "payload": {
    "directive": "<directive-type>",
    "data": { ... },
    "timestamp": 1713264000
  },
  "signature": "<hex Ed25519 signature>"
}
```

### Directive Types

| Directive | Description |
|-----------|-------------|
| `policy_update` | Install or update a governance policy |
| `policy_revoke` | Remove a governance policy |
| `capability_revoke` | Immediately revoke a specific capability |
| `suspend` | Agent must stop accepting new tasks |
| `resume` | Agent may resume accepting tasks |
| `rate_adjust` | Temporarily adjust rate limits |

### Response (via POST /v1/message response payload)

```json
{
  "status": "accepted",
  "directive": "<directive-type>",
  "effective_at": 1713264000
}
```

Governance directives are signed by the orchestrator. Agents MUST
verify the signature before applying any directive. Unsigned or
incorrectly signed directives MUST be rejected.

---

## Compliance Reporting

The governance pattern provides **compliance primitives** — the
mechanical substrate for proving conformance to any standard. The
framework is deliberately agnostic: it knows nothing about PCI-DSS,
ISO 27001, SOC 2, HIPAA, or any other standard. Instead, it provides
three building blocks that operators compose to satisfy whatever
compliance regime applies:

1. **Compliance profiles** — named bundles of policies mapped to
   external control IDs
2. **Evidence collection** — governance events tagged with control
   context, forming an auditable evidence trail
3. **Profile-scoped reporting** — compliance reports filtered by
   profile, producing audit-ready output

The agents, domains, and blueprints that **consume** these primitives
are what dictate the specific controls. The framework just makes the
mechanics work.

### Compliance Profiles

A compliance profile groups related policies under a named umbrella
and maps each policy to one or more opaque **control IDs**. The
framework does not interpret control IDs — they are pass-through
labels that appear in events and reports.

```yaml
compliance_profiles:
  <profile-name>:
    description: <one-line>
    version: <semver>
    policies:
      - policy: <policy-name>
        controls: [<control-id>, ...]
```

#### Example

```yaml
compliance_profiles:
  access-control-baseline:
    description: Baseline access control requirements
    version: 1.0.0
    policies:
      - policy: work-agent-boundaries
        controls: [AC-1, AC-3, AC-6]
      - policy: critical-changes-approval
        controls: [AC-3, CM-3]
      - policy: separation-of-duties
        controls: [AC-5]

  data-handling-baseline:
    description: Baseline data handling requirements
    version: 1.0.0
    policies:
      - policy: data-classification-enforcement
        controls: [SC-8, SC-28]
      - policy: seo-write-limit
        controls: [CM-5]
```

The control IDs (`AC-1`, `SC-8`, etc.) are arbitrary strings. An
operator maps them to whatever standard applies — NIST 800-53,
ISO 27001 Annex A, PCI-DSS requirements, internal control
frameworks, or any combination. The framework stores and reports
them without interpretation.

### Policy Control Metadata

Individual policies MAY carry control metadata directly:

```yaml
policies:
  separation-of-duties:
    description: Agents cannot approve their own recommendations
    scope: system
    target: "*"
    rules:
      - rule: approval_required
        params:
          actions: [apply_changes]
    enforcement: enforce
    severity: high
    controls: [AC-5, AC-6.1]         # opaque control IDs
    profile: access-control-baseline  # optional profile membership
```

The `controls` and `profile` fields are metadata — they do not
affect policy evaluation. They exist solely to tag governance
events for audit filtering.

### Governance Events

Every policy evaluation emits a governance event enriched with
compliance context:

```yaml
topic: governance.policy_evaluated
payload:
  policy: <policy-name>
  agent: <agent-name>
  action: <attempted-action>
  result: allowed | denied | audited
  rule_matched: <rule-type>
  controls: [<control-ids>]          # from policy metadata
  profile: <profile-name>            # from policy metadata
  evidence:
    input_hash: <sha256 of input>    # what was evaluated
    policy_version: <policy-version> # which policy version
    timestamp: <unix-epoch>
    trace_id: <correlation-id>
```

The `evidence` block provides tamper-evident context:
- **input_hash** — SHA-256 of the serialized input that was
  evaluated, proving what data the decision was based on
- **policy_version** — which version of the policy was active,
  proving which rules applied
- **timestamp** and **trace_id** — when and in what context

These events flow to the audit log (see `architecture/storage`)
and the messaging bus. They are the raw material for compliance
evidence.

### Compliance Report

The orchestrator aggregates governance events into compliance
reports. Reports are served via the admin API (see
[architecture/admin](../architecture/admin.md)):

```
GET /admin/governance/report
  Auth: admin (operator Ed25519 + MFA)
  Query:
    period=24h|7d|30d
    profile=<profile-name>           # optional — filter by profile
    control=<control-id>             # optional — filter by control
  Response: ComplianceReport
```

```json
{
  "period": "30d",
  "profile": "access-control-baseline",
  "total_evaluations": 154200,
  "by_control": {
    "AC-1": {"evaluations": 45000, "allowed": 44990, "denied": 8, "audited": 2},
    "AC-3": {"evaluations": 62000, "allowed": 61950, "denied": 12, "audited": 38},
    "AC-5": {"evaluations": 8200, "allowed": 8200, "denied": 0, "audited": 0},
    "AC-6": {"evaluations": 39000, "allowed": 38980, "denied": 4, "audited": 16}
  },
  "violations": [
    {
      "agent": "seo-analyzer",
      "policy": "work-agent-boundaries",
      "controls": ["AC-3", "AC-6"],
      "action": "file:write",
      "resource": "config/settings.json",
      "count": 3,
      "first_seen": 1713264000,
      "last_seen": 1713350400
    }
  ],
  "evidence_count": 154200,
  "report_generated_at": 1713436800
}
```

When no `profile` or `control` filter is provided, the report
includes all evaluations (same behavior as before profiles existed).

### Evidence Export

For external audit systems, the orchestrator SHOULD support
exporting raw governance events as structured evidence:

```
GET /admin/governance/evidence
  Auth: admin (operator Ed25519 + MFA)
  Query:
    profile=<profile-name>
    control=<control-id>
    since=<unix-epoch>
    until=<unix-epoch>
    format=json|csv
  Response: stream of governance events
```

This endpoint streams raw events — not aggregated reports — so
auditors can independently verify compliance claims against the
evidence trail.

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| governance_policy_evaluations_total | counter | Evaluations by policy and result |
| governance_violations_total | counter | Violations by agent and policy |
| governance_directives_issued_total | counter | Directives by type |
| governance_approval_decisions_total | counter | Approvals by authority level |
| governance_escalations_total | counter | Approval escalations |

---

## Implementation Notes

- Policies are evaluated in order. The first matching rule determines
  the outcome. If no rule matches, the default is `allow`.
- Governance directives are delivered via the standard `POST /v1/message`
  endpoint. Agents that do not handle `governance.*` actions cannot
  receive runtime policy updates and are limited to deploy-time
  policies only.
- Policy evaluation MUST be fast (< 1ms per evaluation). Policies
  are loaded into memory at startup and updated via directives.
- Governance events flow through the standard messaging bus (not
  direct HTTP) so the alerting agent can trigger on violations.
- The compliance report is generated on demand, not continuously.
  The orchestrator queries the governance event store.

---

## Verification Checklist

- [ ] Policies are declared with scope, target, rules, and enforcement
- [ ] Capability enforcement blocks unauthorized operations when enforcement = enforce
- [ ] Capability enforcement logs but allows when enforcement = audit
- [ ] Behavioral boundaries prevent work agents from dispatching
- [ ] Behavioral boundaries prevent domains from cross-domain access
- [ ] Approval authority matrix routes decisions to correct level
- [ ] Separation of duties prevents self-approval
- [ ] governance.directive message action accepts signed directives from orchestrator
- [ ] Unsigned directives are rejected
- [ ] policy_update directive installs new policies at runtime
- [ ] suspend/resume directives control task acceptance
- [ ] Governance events emit for every policy evaluation
- [ ] Governance events include controls and profile metadata when present
- [ ] Evidence block includes input_hash and policy_version
- [ ] Compliance profiles group policies with control IDs
- [ ] Compliance report filters by profile and control
- [ ] Evidence export streams raw governance events for audit
- [ ] Metrics emit for evaluations, violations, and directives
