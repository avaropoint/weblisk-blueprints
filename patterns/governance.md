<!-- blueprint
type: pattern
name: governance
version: 1.0.0
requires: [protocol/spec, protocol/types, protocol/identity, patterns/scope, patterns/policy, patterns/safety, patterns/approval, patterns/observability, patterns/messaging]
platform: any
tier: free
-->

# Governance Pattern

Compliance reporting, evidence collection, governance directives,
and audit for all Weblisk agents. This pattern is the compliance
and audit layer — it consumes policies, safety rules, scoping, and
approval flows defined elsewhere and provides the machinery to
prove conformance.

## Overview

Governance is the **compliance and audit layer** for the Weblisk
framework. It does not define policies (see
[patterns/policy](./policy.md)), safety rules (see
[patterns/safety](./safety.md)), or approval flows (see
[patterns/approval](./approval.md)). Instead, governance provides:

1. **Compliance profiles** — named bundles of policies mapped to
   external control IDs
2. **Evidence collection** — governance events tagged with control
   context, forming an auditable evidence trail
3. **Compliance reporting** — profile-scoped reports for audit
4. **Governance directives** — runtime policy injection via agent
   messaging
5. **Agent directives** — runtime capability adjustment
   (suspend/resume/rate-adjust)

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, capabilities, url, type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GovernanceDirective
          fields_used: [directive, data, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: IdentityToken
          fields_used: [sub, role, cap]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/scope
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ScopePolicy
          fields_used: [scope, target]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/policy
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GovernancePolicy
          fields_used: [scope, target, rules, enforcement, severity]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/safety
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: SafetyBoundary
          fields_used: [agent_kind, constraints]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/approval
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ApprovalRequest
          fields_used: [severity, authority_level]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: HealthResponse
          fields_used: [state, checks, metrics_snapshot]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: EventEnvelope
          fields_used: [topic, payload, scope, source]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Framework-agnostic compliance** — The governance pattern knows
   nothing about PCI-DSS, ISO 27001, SOC 2, HIPAA, or any standard.
   It provides generic compliance profiles that operators map to any
   regime.
2. **Evidence-first** — Every policy evaluation, safety decision,
   approval, and violation is recorded as structured evidence.
   Auditors work with evidence, not assertions.
3. **Profile composition** — Multiple compliance profiles can
   coexist. An operator may have an access-control profile AND a
   data-handling profile, each mapping different policies to
   different control IDs.
4. **Runtime directives** — Governance can update policies, revoke
   capabilities, suspend/resume agents, and adjust rate limits at
   runtime without redeployment.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: compliance-profiling
      description: Define compliance profiles mapping policies to control IDs
      parameters:
        - name: profile_name
          type: string
          required: true
          description: Named compliance profile
        - name: policies
          type: "[]object"
          required: true
          description: Policy-to-control mappings
      inherits: Profile structure, control ID tagging, report filtering
      overridable: true
      override_constraints: Cannot remove required control mappings

    - name: evidence-collection
      description: Record structured evidence from policy evaluations and safety decisions
      parameters:
        - name: event_topic
          type: string
          required: true
          description: Topic of the governance event being recorded
        - name: evidence
          type: object
          required: true
          description: Evidence block (input_hash, policy_version, timestamp, trace_id)
      inherits: Evidence structure, hash computation, event enrichment
      overridable: false

    - name: governance-directive
      description: Deliver runtime directives to agents for policy/capability changes
      parameters:
        - name: directive_type
          type: string
          required: true
          description: Directive type (policy_update, policy_revoke, capability_revoke, suspend, resume, rate_adjust)
        - name: target_agent
          type: string
          required: true
          description: Agent receiving the directive
        - name: data
          type: object
          required: true
          description: Directive payload
      inherits: Directive delivery, signature verification, response handling
      overridable: false

  types:
    - name: ComplianceProfile
      description: Named bundle of policies mapped to external control IDs
      inherited_by: Compliance Profiles section
    - name: GovernanceDirective
      description: Runtime instruction delivered to agents for policy updates or capability changes
      inherited_by: Governance Directives section
    - name: ComplianceReport
      description: Aggregated compliance report filtered by profile and control
      inherited_by: Compliance Reporting section
    - name: EvidenceRecord
      description: Structured evidence from a single policy evaluation or safety decision
      inherited_by: Evidence Collection section

  endpoints:
    - path: /admin/governance/report
      method: GET
      description: Generate compliance report filtered by profile and control
    - path: /admin/governance/evidence
      method: GET
      description: Export raw governance events for external audit

  events:
    - topic: governance.directive_issued
      description: Governance directive delivered to an agent
    - topic: governance.compliance_report_generated
      description: Compliance report was generated
    - topic: governance.evidence_exported
      description: Evidence export was requested
```

---

## Compliance Profiles

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

### Example Profiles

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

Individual policies (defined in [patterns/policy](./policy.md))
MAY carry control metadata directly:

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

---

## Evidence Collection

Every policy evaluation, safety decision, and approval outcome
emits a governance event enriched with compliance context. These
events form the raw evidence trail that auditors use to verify
conformance.

### Governance Events

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

These events flow to the audit log (see
[architecture/storage](../architecture/storage.md)) and the
messaging bus. They are the raw material for compliance evidence.

### Safety Evidence

Safety decisions (see [patterns/safety](./safety.md)) also emit
governance events:

```yaml
topic: governance.safety_evaluated
payload:
  boundary: <boundary-name>
  agent: <agent-name>
  constraint: <constraint-type>
  result: allowed | blocked
  evidence:
    input_hash: <sha256 of input>
    boundary_version: <boundary-version>
    timestamp: <unix-epoch>
    trace_id: <correlation-id>
```

### Approval Evidence

Approval decisions (see [patterns/approval](./approval.md)) emit:

```yaml
topic: governance.approval_decided
payload:
  request_id: <approval-request-id>
  authority_level: <level>
  decision: approved | denied | escalated
  approver: <approver-identity>
  evidence:
    request_hash: <sha256 of request>
    timestamp: <unix-epoch>
    trace_id: <correlation-id>
```

---

## Governance Directives

The orchestrator can issue runtime directives to agents via the
standard messaging endpoint. Directives modify agent behavior
without redeployment.

### Directive Delivery

Directives are delivered as `POST /v1/message` with action
`governance.directive`:

```json
{
  "action": "governance.directive",
  "directive": "<directive-type>",
  "data": { ... },
  "timestamp": 1713264000,
  "signature": "<orchestrator-ed25519-signature>"
}
```

### Directive Types

| Directive | Effect |
|-----------|--------|
| `policy_update` | Install or update a governance policy |
| `policy_revoke` | Remove a governance policy |
| `capability_revoke` | Immediately revoke a specific capability |
| `suspend` | Agent must stop accepting new tasks |
| `resume` | Agent may resume accepting tasks |
| `rate_adjust` | Temporarily adjust rate limits |

### Response Format

Agents respond via the `POST /v1/message` response payload:

```json
{
  "status": "accepted",
  "directive": "<directive-type>",
  "effective_at": 1713264000
}
```

### Signature Verification

Governance directives are signed by the orchestrator. Agents MUST
verify the signature before applying any directive. Unsigned or
incorrectly signed directives MUST be rejected with:

```json
{
  "status": "rejected",
  "reason": "invalid_signature"
}
```

### Directive Events

Every directive issuance emits a governance event:

```yaml
topic: governance.directive_issued
payload:
  directive: <directive-type>
  target_agent: <agent-name>
  data_hash: <sha256 of directive data>
  timestamp: <unix-epoch>
  result: accepted | rejected
  trace_id: <correlation-id>
```

---

## Compliance Reporting

The orchestrator aggregates governance events into compliance
reports. Reports are served via the admin API (see
[architecture/admin](../architecture/admin.md)).

### Compliance Report Endpoint

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
    "AC-1": {
      "evaluations": 45000,
      "allowed": 44990,
      "denied": 8,
      "audited": 2
    },
    "AC-3": {
      "evaluations": 62000,
      "allowed": 61950,
      "denied": 12,
      "audited": 38
    },
    "AC-5": {
      "evaluations": 8200,
      "allowed": 8200,
      "denied": 0,
      "audited": 0
    },
    "AC-6": {
      "evaluations": 39000,
      "allowed": 38980,
      "denied": 4,
      "audited": 16
    }
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
includes all evaluations.

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
| `governance_policy_evaluations_total` | counter | Evaluations by policy and result |
| `governance_violations_total` | counter | Violations by agent and policy |
| `governance_directives_issued_total` | counter | Directives by type |
| `governance_evidence_exported_total` | counter | Evidence exports by profile |
| `governance_compliance_reports_total` | counter | Reports generated by profile |

---

## Implementation Notes

- Governance consumes policy evaluation results from
  [patterns/policy](./policy.md), safety decisions from
  [patterns/safety](./safety.md), and approval outcomes from
  [patterns/approval](./approval.md). It does not perform these
  evaluations itself.
- Governance directives are delivered via the standard
  `POST /v1/message` endpoint. Agents that do not handle
  `governance.*` actions cannot receive runtime policy updates and
  are limited to deploy-time policies only.
- Governance events flow through the standard messaging bus (not
  direct HTTP) so the alerting agent can trigger on violations.
- The compliance report is generated on demand, not continuously.
  The orchestrator queries the governance event store.
- Evidence hashing uses SHA-256 over canonicalized JSON input.

---

## Verification Checklist

- [ ] Compliance profiles group policies with control IDs
- [ ] Governance events include evidence blocks (input_hash, policy_version)
- [ ] Compliance report filters by profile and control
- [ ] Evidence export streams raw events for audit
- [ ] Governance directives are signed by orchestrator
- [ ] Unsigned directives are rejected
- [ ] policy_update directive installs new policies at runtime
- [ ] suspend/resume directives control task acceptance
- [ ] Metrics emit for evaluations, violations, and directives
