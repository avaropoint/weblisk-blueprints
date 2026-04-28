<!-- blueprint
type: pattern
name: scope
version: 1.0.0
requires: [protocol/spec, protocol/types]
platform: any
tier: free
-->

# Scope Pattern

Universal classification primitive that determines protection level
for any entity in the system — data fields, operations, messages,
agents, resources, and environments. Scope is the foundation that
policies, safety, privacy, and contracts all reference.

## Overview

Scope is the most foundational pattern in Weblisk. It provides a
five-level classification model — public, internal, confidential,
restricted, critical — that can be applied to anything. When an entity
is classified, protections activate automatically based on the level.

Weblisk is not a restrictive platform. Scope is opt-in protection.
Agents, domains, and operators choose what classification to apply.
The more sensitive the scope, the more policies activate — audit
logging, encryption, masking, approval gates, retention rules. Scope
is never silently dropped: when data moves between agents, hubs, or
clients, its scope travels with it.

This pattern is consumed by every other pattern in the system.
Messaging reads scope to filter delivery. Workflows read scope to
enforce approval gates. Storage reads scope to select encryption
strategies. Observability reads scope to control log redaction.
Scope is the primitive; everything else is a consumer.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, category]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Universal applicability** — Scope applies to ANY entity in the
   system: data fields, operations, messages, agents, resources,
   environments. It is not "data scope" or "agent scope" — it is
   scope, period. Every entity type uses the same classification
   model and the same enforcement pipeline.

2. **Propagation by default** — Scope is never silently dropped.
   When data moves between components — agent to agent, hub to hub,
   hub to client — its scope moves with it. The receiving component
   MUST honor the declared scope or reject the transfer. Silent
   scope loss is a conformance violation.

3. **Escalation to maximum** — In any composite entity (a message
   containing multiple data fields, a workflow spanning multiple
   agents, a response aggregating multiple sources), the effective
   scope is the HIGHEST scope of any component. A single restricted
   field in a public message makes the entire message restricted.

4. **Environment-relative enforcement** — The same scope level may
   be enforced differently in development vs production. Environments
   modify enforcement strictness, not classification. A field
   classified as `restricted` is always `restricted` — but in dev
   the enforcement may be audit-only, while in production it is
   fully enforced.

5. **Opt-in extensibility** — The five built-in levels cover most
   use cases. Domains MAY define custom labels that map to a base
   level for interoperability. Custom labels extend — they never
   replace — the built-in model. Unknown custom labels resolve to
   the mapped base level during cross-boundary transfers.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: scope-declaration
      description: Declare a scope level on any entity — data field, operation, message, agent, or resource
      parameters:
        - name: level
          type: enum(public, internal, confidential, restricted, critical)
          required: true
          description: Classification level from the built-in five-level model
        - name: context
          type: string
          required: false
          description: Domain or subsystem that owns the classification decision
        - name: propagation_rule
          type: enum(inherit, fixed, escalate)
          required: false
          default: inherit
          description: How scope behaves when the entity is composed or transferred
        - name: custom_labels
          type: "[]string"
          required: false
          description: Domain-specific labels that map to the base level for interoperability
      inherits: Scope metadata attachment, level validation, propagation rule assignment
      overridable: true
      override_constraints: Level must be one of the five built-in values or a registered custom label that maps to a built-in level

    - name: scope-propagation
      description: Carry scope across component boundaries — agent-to-agent, hub-to-hub, hub-to-client
      parameters:
        - name: source_scope
          type: ScopeDeclaration
          required: true
          description: Scope of the entity being transferred
        - name: target_component
          type: string
          required: true
          description: Identifier of the receiving component (agent name, hub ID, client ID)
        - name: transfer_mode
          type: enum(copy, reference)
          required: false
          default: copy
          description: Whether the receiving component gets a full scope copy or a reference to the source
      inherits: Envelope-level scope metadata, cross-boundary validation, rejection on scope mismatch
      overridable: true
      override_constraints: Must never silently drop scope; receiving component must validate or reject

    - name: scope-escalation
      description: Compute the effective scope of a composite entity from its components
      parameters:
        - name: components
          type: "[]ScopeDeclaration"
          required: true
          description: Scope declarations of all component parts
        - name: escalation_strategy
          type: enum(maximum, explicit)
          required: false
          default: maximum
          description: How to compute composite scope — maximum of components or explicitly declared
      inherits: Automatic highest-level computation, escalation event emission
      overridable: true
      override_constraints: Maximum strategy cannot be overridden to produce a LOWER scope than any component

    - name: scope-evaluation
      description: Compute the effective scope of an entity given its declaration, environment, and context
      parameters:
        - name: entity
          type: string
          required: true
          description: Identifier of the entity being evaluated
        - name: declared_scope
          type: ScopeDeclaration
          required: true
          description: The entity's declared scope level
        - name: environment
          type: EnvironmentProfile
          required: false
          description: Active environment profile that may modify enforcement
      inherits: Effective scope computation, environment overlay, enforcement level resolution
      overridable: true
      override_constraints: Evaluation must never produce an effective scope LOWER than declared scope

    - name: environment-profiling
      description: Define how environments modify scope enforcement without changing classification
      parameters:
        - name: environment_name
          type: enum(development, staging, production, custom)
          required: true
          description: Target environment identifier
        - name: enforcement_level
          type: enum(permissive, moderate, strict)
          required: true
          description: Base enforcement strictness for this environment
        - name: scope_overrides
          type: map
          required: false
          description: Per-level enforcement overrides (audit, enforce, block)
      inherits: Environment-aware enforcement pipeline, override resolution
      overridable: true
      override_constraints: Production environment must always enforce at strict level; overrides cannot weaken production enforcement

  types:
    - name: ScopeLevel
      description: Enumeration of the five built-in classification levels
      inherited_by: Scope Types section
    - name: ScopeDeclaration
      description: Complete scope metadata for any entity
      inherited_by: Scope Types section
    - name: ScopeEvaluation
      description: Result of evaluating an entity's effective scope in context
      inherited_by: Scope Types section
    - name: EnvironmentProfile
      description: Environment configuration that modifies scope enforcement
      inherited_by: Scope Types section
    - name: ScopeViolation
      description: Record of a scope boundary violation
      inherited_by: Scope Types section

  events:
    - topic: scope.violation
      description: Emitted when an entity's scope is accessed beyond its allowed level
      payload: {entity, expected_scope, actual_scope, component, action_taken, timestamp}
    - topic: scope.escalation
      description: Emitted when a composite's scope is escalated due to a higher-scoped component
      payload: {composite_entity, previous_scope, escalated_scope, escalation_source, timestamp}
    - topic: scope.override
      description: Emitted when an environment profile modifies scope enforcement
      payload: {entity, declared_scope, effective_enforcement, environment, reason, timestamp}
```

---

## Scope Levels

The five built-in levels form a strict hierarchy. Each level inherits
all protections from the levels below it. Higher levels add additional
protections — they never remove protections from lower levels.

### Level Hierarchy

```
critical > restricted > confidential > internal > public
```

Numeric values for programmatic comparison:

| Level | Ordinal | Description |
|-------|---------|-------------|
| `public` | 0 | Unrestricted; safe for external consumption |
| `internal` | 1 | Organization-internal; not for external exposure |
| `confidential` | 2 | Sensitive; requires access control and audit |
| `restricted` | 3 | Highly sensitive; requires encryption, masking, approval |
| `critical` | 4 | Regulatory or safety-critical; maximum protection |

### Scope Inheritance Table

Each level activates specific protections. Higher levels include all
protections from lower levels plus additional requirements:

| Level | Audit | Encryption | Masking | Approval | Retention |
|-------|-------|-----------|---------|----------|-----------|
| public | no | transport | none | none | default |
| internal | basic | transport | none | none | default |
| confidential | full | transport + at-rest | field-level | auto | policy-driven |
| restricted | full | transport + at-rest + field | full masking | operator | strict |
| critical | full + tamper-evident | transport + at-rest + field + envelope | full masking | admin + MFA | regulatory |

**Column definitions:**

- **Audit** — What level of audit logging is required. `basic` logs
  access events. `full` logs access + mutations + context.
  `full + tamper-evident` adds cryptographic audit trail integrity.
- **Encryption** — Required encryption layers. `transport` = TLS.
  `at-rest` = storage encryption. `field` = per-field encryption.
  `envelope` = entire message envelope encrypted.
- **Masking** — How the entity appears in logs, UI, and API responses
  when the accessor lacks sufficient clearance. `field-level` masks
  specific fields. `full masking` masks the entire value.
- **Approval** — What approval is needed to access or modify the
  entity. `auto` = system-level policy check. `operator` = human
  operator approval. `admin + MFA` = administrator with multi-factor
  authentication.
- **Retention** — How long the entity is retained. `default` = system
  default. `policy-driven` = domain-specific retention policy.
  `strict` = minimum necessary retention. `regulatory` = retention
  per applicable regulatory requirements.

---

## Types

```yaml
types:
  ScopeLevel:
    description: Enumeration of the five built-in classification levels
    values:
      - name: public
        ordinal: 0
        description: Unrestricted; safe for external consumption
      - name: internal
        ordinal: 1
        description: Organization-internal; not for external exposure
      - name: confidential
        ordinal: 2
        description: Sensitive; requires access control and audit
      - name: restricted
        ordinal: 3
        description: Highly sensitive; requires encryption, masking, approval
      - name: critical
        ordinal: 4
        description: Regulatory or safety-critical; maximum protection
    comparison: ordinal-based; higher ordinal = more restrictive scope

  ScopeDeclaration:
    description: Complete scope metadata attached to any entity
    fields:
      - name: level
        type: ScopeLevel
        required: true
        description: Classification level from built-in model
      - name: context
        type: string
        required: false
        description: Domain or subsystem that owns the classification (e.g., "seo", "billing", "identity")
      - name: propagation_rule
        type: enum(inherit, fixed, escalate)
        required: false
        default: inherit
        description: |
          How scope behaves during composition or transfer:
          - inherit: receiving component adopts the source scope
          - fixed: scope is locked and cannot be escalated by composition
          - escalate: scope participates in composite escalation (default behavior)
      - name: custom_labels
        type: "[]string"
        required: false
        description: Domain-specific labels that extend the base level (e.g., ["pii", "financial", "hipaa"])
      - name: declared_by
        type: string
        required: false
        description: Identifier of the agent or domain that applied this classification
      - name: declared_at
        type: int64
        required: false
        description: Unix epoch seconds when scope was declared

  ScopeEvaluation:
    description: Result of evaluating an entity's effective scope in context
    fields:
      - name: entity
        type: string
        required: true
        description: Identifier of the entity being evaluated
      - name: declared_scope
        type: ScopeDeclaration
        required: true
        description: The entity's declared scope
      - name: effective_scope
        type: ScopeLevel
        required: true
        description: Computed scope after environment and escalation rules
      - name: effective_enforcement
        type: enum(audit, enforce, block)
        required: true
        description: |
          How the effective scope is enforced in the current environment:
          - audit: log violations but allow access
          - enforce: deny access on violation
          - block: deny access and quarantine the entity
      - name: escalation_source
        type: string
        required: false
        description: If scope was escalated, the component that caused escalation
      - name: environment
        type: string
        required: false
        description: Environment name used for evaluation (dev, staging, production)

  EnvironmentProfile:
    description: Environment configuration that modifies scope enforcement
    fields:
      - name: name
        type: enum(development, staging, production, custom)
        required: true
        description: Environment identifier
      - name: enforcement_level
        type: enum(permissive, moderate, strict)
        required: true
        description: |
          Base enforcement strictness:
          - permissive: audit-only for most levels; enforce only critical
          - moderate: enforce confidential and above; audit internal
          - strict: enforce all levels at maximum
      - name: scope_overrides
        type: map[ScopeLevel → EnforcementOverride]
        required: false
        description: Per-level enforcement overrides that take precedence over base level
      - name: custom_name
        type: string
        required: false
        description: Human-readable name for custom environments

  EnforcementOverride:
    description: Per-level enforcement configuration within an environment
    fields:
      - name: enforcement
        type: enum(audit, enforce, block)
        required: true
        description: Override enforcement action for this scope level
      - name: reason
        type: string
        required: false
        description: Justification for the override (logged in scope.override events)

  ScopeViolation:
    description: Record of a scope boundary violation
    fields:
      - name: entity
        type: string
        required: true
        description: Identifier of the entity whose scope was violated
      - name: expected_scope
        type: ScopeLevel
        required: true
        description: Scope level the entity requires
      - name: actual_scope
        type: ScopeLevel
        required: true
        description: Scope level the accessor presented
      - name: accessor
        type: string
        required: true
        description: Identifier of the component that attempted access
      - name: action_taken
        type: enum(audit, deny, quarantine)
        required: true
        description: Enforcement action applied
      - name: timestamp
        type: int64
        required: true
        description: Unix epoch seconds when the violation occurred
      - name: environment
        type: string
        required: false
        description: Environment where the violation occurred
```

---

## Scope Propagation

Scope travels with the entity through every boundary crossing. This
section defines the rules for how scope propagates between components.

### Propagation Rules

When an entity crosses a boundary (agent-to-agent, hub-to-hub,
hub-to-client), its scope metadata is carried in the transfer
envelope. The receiving component MUST:

1. **Read** the scope metadata from the envelope
2. **Validate** that it is authorized to handle data at this scope level
3. **Adopt** the scope for all local operations on this data
4. **Propagate** the scope on any further transfers

If the receiving component is not authorized for the declared scope,
it MUST reject the transfer and emit a `scope.violation` event.

### Cross-Boundary Scenarios

**Agent A sends confidential-scoped data to Agent B:**

```
Agent A                          Agent B
  │                                │
  │ POST /v1/message               │
  │ { scope: "confidential",       │
  │   payload: { ... } }           │
  │ ───────────────────────────►   │
  │                                │ 1. Read scope: confidential
  │                                │ 2. Validate: agent authorized
  │                                │    for confidential? Yes.
  │                                │ 3. Process at confidential level
  │                                │ 4. Any output carries scope ≥
  │                                │    confidential
```

**Workflow combines public + restricted data:**

```
Phase 1 output: { scope: public,     data: "..." }
Phase 2 output: { scope: restricted, data: "..." }

Workflow result: { scope: restricted }
  ↑ Escalation: highest component scope wins
```

**Hub A sends data to Hub B (federation):**

```
Hub A                            Hub B
  │                                │
  │ Federated transfer             │
  │ envelope.scope: restricted     │
  │ ───────────────────────────►   │
  │                                │ 1. Read scope from envelope
  │                                │ 2. Validate against local
  │                                │    policies
  │                                │ 3. Apply local enforcement
  │                                │    (may be stricter)
```

**Client requests data:**

```
Agent                            Client SDK
  │                                │
  │ Response                       │
  │ { scope: "confidential",       │
  │   display_rules: {             │
  │     mask_fields: ["email"],    │
  │     log_access: true } }       │
  │ ───────────────────────────►   │
  │                                │ Client SDK enforces
  │                                │ display_rules locally
```

### Propagation in Message Envelopes

Scope metadata is carried in a standard `scope` field on all message
and event envelopes:

```json
{
  "event_id": "evt-a1b2c3d4e5f6",
  "topic": "task.complete",
  "source": "content-analyzer",
  "scope": "confidential",
  "scope_metadata": {
    "level": "confidential",
    "context": "content",
    "propagation_rule": "inherit",
    "custom_labels": ["pii"],
    "declared_by": "content-analyzer",
    "declared_at": 1712160001
  },
  "payload": { }
}
```

The `scope` field (string) provides backward-compatible simple scoping.
The `scope_metadata` field (object) carries full `ScopeDeclaration`
for components that support the scope pattern. Components that do not
support the scope pattern MUST still preserve both fields on any
forwarding or re-publishing.

---

## Scope Escalation

When multiple entities are composed — a message with multiple fields,
a workflow aggregating phase outputs, a response combining data from
multiple agents — the composite inherits the highest scope of any
component.

### Escalation Algorithm

```
function compute_effective_scope(components):
    max_level = public

    for each component in components:
        if component.scope.propagation_rule == "fixed":
            continue  # fixed-scope components are excluded from escalation
        if component.scope.level > max_level:
            max_level = component.scope.level
            escalation_source = component.identifier

    if max_level > composite.declared_scope:
        emit scope.escalation event
        composite.effective_scope = max_level

    return max_level
```

### Escalation Examples

**Message with mixed-scope fields:**

```yaml
message:
  effective_scope: restricted  # highest of all payload fields
  payload:
    user_name:
      value: "Alice"
      scope: public
    email:
      value: "alice@example.com"
      scope: restricted
    department:
      value: "Engineering"
      scope: internal
```

The message contains fields at public, internal, and restricted levels.
The effective scope is `restricted` — the highest component scope.

**Workflow with mixed-scope phases:**

```yaml
workflow_execution:
  effective_scope: confidential
  phases:
    - name: fetch-public-data
      output_scope: public
    - name: analyze-with-pii
      output_scope: confidential
    - name: format-results
      output_scope: public
  # Phase "analyze-with-pii" escalates the entire workflow to confidential
```

---

## Scope Evaluation

Scope evaluation computes the effective enforcement for an entity by
combining its declared scope with the active environment profile.

### Evaluation Algorithm

```
function evaluate_scope(entity, environment):
    declared = entity.scope.level
    profile = environment

    # Check for per-level override
    if declared in profile.scope_overrides:
        enforcement = profile.scope_overrides[declared].enforcement
    else:
        enforcement = resolve_from_base(declared, profile.enforcement_level)

    return ScopeEvaluation {
        entity: entity.id,
        declared_scope: entity.scope,
        effective_scope: declared,  # classification never changes
        effective_enforcement: enforcement,
        environment: profile.name
    }

function resolve_from_base(level, base_enforcement):
    if base_enforcement == "strict":
        return "enforce"  # all levels enforced
    if base_enforcement == "moderate":
        if level >= confidential:
            return "enforce"
        return "audit"
    if base_enforcement == "permissive":
        if level >= critical:
            return "enforce"
        return "audit"
```

### Key Distinction: Classification vs Enforcement

Classification is permanent. A field declared `restricted` is always
`restricted`, in every environment. Enforcement varies:

| | Development | Staging | Production |
|---|---|---|---|
| **Classification** | restricted | restricted | restricted |
| **Enforcement** | audit (log only) | enforce (deny) | enforce (deny) |

This separation allows developers to work with realistic data
classifications without being blocked in development, while
maintaining full protection in production.

---

## Environment Profiles

Environment profiles define how scope enforcement varies across
deployment environments. Classification is constant; enforcement
adapts.

### Built-in Profiles

```yaml
environments:
  development:
    enforcement_level: permissive
    scope_overrides:
      restricted:
        enforcement: audit
        reason: "Allow development access; log for awareness"
      critical:
        enforcement: enforce
        reason: "Critical data is always enforced, even in dev"

  staging:
    enforcement_level: moderate
    scope_overrides:
      confidential:
        enforcement: enforce
        reason: "Staging mirrors production for confidential+"

  production:
    enforcement_level: strict
    # No overrides — all scope levels enforced at maximum
```

### Enforcement Resolution

The enforcement for a specific scope level in a specific environment
is resolved as:

1. Check `scope_overrides` for the level → if present, use override
2. Fall back to `enforcement_level` base rules
3. Production MUST always resolve to `enforce` or `block` — never `audit`

### Custom Environments

Operators MAY define custom environment profiles:

```yaml
environments:
  qa-automated:
    enforcement_level: moderate
    custom_name: "QA Automated Testing"
    scope_overrides:
      restricted:
        enforcement: audit
        reason: "Automated tests need access to restricted test data"

  dr-failover:
    enforcement_level: strict
    custom_name: "Disaster Recovery Failover"
    # Mirrors production enforcement
```

---

## Configuration

```yaml
scope:
  default_level: internal                # applied when no scope is declared
  propagation_mode: inherit              # default propagation rule
  escalation_strategy: maximum           # default escalation strategy
  violation_action: deny                 # default action on scope violation
  environment: production                # active environment profile
  custom_labels: {}                      # domain-registered custom labels
  audit:
    log_all_access: false                # log every access, not just violations
    tamper_evident: false                # enable cryptographic audit integrity
  enforcement:
    reject_unscoped: false               # reject entities without scope declaration
    strict_propagation: true             # fail if scope cannot be propagated
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_SCOPE_DEFAULT_LEVEL` | `internal` | Scope applied to unclassified entities |
| `WL_SCOPE_ENVIRONMENT` | `production` | Active environment profile |
| `WL_SCOPE_VIOLATION_ACTION` | `deny` | Default enforcement on violation (`audit`, `deny`, `block`) |
| `WL_SCOPE_REJECT_UNSCOPED` | `false` | Whether to reject entities without scope declaration |
| `WL_SCOPE_STRICT_PROPAGATION` | `true` | Whether to fail on scope propagation failures |

---

## Scope Application Examples

Scope is universal. The same classification model applies to every
entity type. Here are practical examples of scope declarations on
different entity types.

### Data Fields

Individual fields in a data model carry their own scope:

```yaml
fields:
  email:
    type: string
    scope: restricted
    scope_metadata:
      custom_labels: ["pii"]
      propagation_rule: inherit
  display_name:
    type: string
    scope: public
  ssn:
    type: string
    scope: critical
    scope_metadata:
      custom_labels: ["pii", "regulatory"]
      propagation_rule: inherit
  department:
    type: string
    scope: internal
  salary:
    type: number
    scope: confidential
    scope_metadata:
      custom_labels: ["financial"]
      propagation_rule: inherit
```

### Operations

Operations carry scope that determines who can invoke them and what
approval is required:

```yaml
operations:
  delete_database:
    scope: critical
    scope_metadata:
      context: "infrastructure"
      custom_labels: ["destructive"]
  export_user_data:
    scope: restricted
    scope_metadata:
      context: "compliance"
      custom_labels: ["pii", "bulk-export"]
  read_record:
    scope: internal
  list_public_pages:
    scope: public
  update_billing:
    scope: confidential
    scope_metadata:
      context: "billing"
      custom_labels: ["financial"]
```

### Messages

Messages carry an effective scope computed from their payload fields:

```yaml
message:
  effective_scope: restricted  # highest of all payload fields
  payload:
    user_name:
      value: "Alice"
      scope: public
    email:
      value: "alice@example.com"
      scope: restricted
    preferences:
      value: { theme: "dark" }
      scope: internal
```

### Agents

Agents declare their operational scope — the maximum scope level
they are authorized to handle:

```yaml
agent:
  name: content-analyzer
  operational_scope: confidential
  scope_metadata:
    context: "content analysis pipeline"
    # This agent can handle public, internal, and confidential data
    # It MUST reject restricted or critical data
```

When an agent receives data above its operational scope, it MUST
reject the request and emit a `scope.violation` event:

```
content-analyzer receives restricted-scoped data
→ agent.operational_scope (confidential) < data.scope (restricted)
→ REJECT: emit scope.violation event
→ Return ErrorResponse { code: "SCOPE_EXCEEDED", category: "permanent" }
```

### Resources

Infrastructure resources carry scope to determine access controls:

```yaml
resources:
  user_database:
    scope: restricted
    scope_metadata:
      custom_labels: ["pii", "persistence"]
  cache_layer:
    scope: internal
  cdn_assets:
    scope: public
  encryption_keys:
    scope: critical
    scope_metadata:
      custom_labels: ["key-material"]
```

---

## Custom Scope Labels

The five built-in levels cover most classification needs. For
domain-specific requirements, custom labels extend the model without
replacing it.

### Label Registration

Custom labels are registered at the domain level and mapped to a
base scope level:

```yaml
custom_labels:
  pii:
    maps_to: restricted
    description: "Personally identifiable information"
  hipaa:
    maps_to: critical
    description: "Data subject to HIPAA regulations"
  financial:
    maps_to: confidential
    description: "Financial data requiring audit trail"
  export_controlled:
    maps_to: restricted
    description: "Data subject to export control regulations"
  telemetry:
    maps_to: internal
    description: "System telemetry and metrics data"
```

### Label Resolution

When a component encounters a custom label it does not recognize,
it resolves the label to its mapped base level:

```
Entity scope: { level: restricted, custom_labels: ["hipaa"] }

Component A (knows "hipaa"): applies HIPAA-specific protections
Component B (doesn't know "hipaa"): treats as "restricted" (mapped base level)
```

This ensures interoperability: custom labels add context for
components that understand them, but every component can fall back
to the base level.

---

## Scope in Federation

When entities cross hub boundaries via federation, scope is preserved
in the federation envelope:

```yaml
federation_transfer:
  source_hub: "acme-corp"
  target_hub: "partner-org"
  entity_scope:
    level: confidential
    custom_labels: ["pii"]
    declared_by: "acme-corp::content-analyzer"
  federation_policy:
    allow_scope_levels: [public, internal, confidential]
    deny_scope_levels: [restricted, critical]
```

### Federation Scope Rules

1. **Hub-level scope policy** — Hubs declare which scope levels they
   accept from federated peers. A hub may refuse restricted or
   critical data from external hubs.
2. **Scope preservation** — The receiving hub preserves the original
   scope declaration. It does not reclassify incoming data.
3. **Enforcement stacking** — The receiving hub applies its own
   environment profile on top of the preserved scope. If the
   receiving hub's policies are stricter, the stricter rules apply.
4. **Custom label passthrough** — Unknown custom labels are preserved
   in metadata but resolved to their base level for enforcement.

---

## Error Handling

### Scope-Related Errors

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `SCOPE_EXCEEDED` | 403 | permanent | Entity scope exceeds component's operational scope |
| `SCOPE_MISSING` | 400 | permanent | Entity has no scope declaration and `reject_unscoped` is enabled |
| `SCOPE_PROPAGATION_FAILED` | 500 | transient | Scope metadata could not be attached to transfer envelope |
| `SCOPE_INVALID_LEVEL` | 400 | permanent | Declared scope level is not a valid built-in level or registered custom label |
| `SCOPE_FEDERATION_DENIED` | 403 | permanent | Receiving hub does not accept this scope level from federated peers |

### Error Response Examples

```json
{
  "error": "Entity scope (restricted) exceeds agent operational scope (confidential)",
  "code": "SCOPE_EXCEEDED",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "entity_scope": "restricted",
    "agent_scope": "confidential",
    "agent": "content-analyzer"
  }
}
```

```json
{
  "error": "Entity has no scope declaration",
  "code": "SCOPE_MISSING",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "entity": "record-12345",
    "config": "reject_unscoped=true"
  }
}
```

---

## Implementation Notes

- Scope is metadata, not access control. Scope classifies entities;
  other patterns (auth, policies, governance) consume the classification
  to make access decisions. Scope itself does not authenticate or
  authorize — it informs.
- The `scope` string field on envelopes provides backward compatibility
  with components that predate the scope pattern. The `scope_metadata`
  object carries the full `ScopeDeclaration`. Both MUST be present on
  all envelopes.
- Scope evaluation SHOULD be performed once at the boundary (when data
  enters a component) and cached for the duration of the request.
  Re-evaluating scope on every field access is unnecessary overhead.
- Default scope (`WL_SCOPE_DEFAULT_LEVEL`) applies only to entities
  that have no explicit scope declaration. Implementations SHOULD
  log a warning when defaulting is applied, as it may indicate a
  missing classification.
- Custom labels are resolved to their base level during cross-boundary
  transfers. Components SHOULD preserve unknown labels in metadata
  for downstream components that may understand them.
- Environment profiles are loaded at component startup from
  configuration. Profile changes require a component restart or
  configuration reload — they do not change mid-request.
- Scope escalation in composites is computed at composition time, not
  at access time. When a message is assembled from multiple fields,
  the effective scope is computed once and attached to the message
  envelope.
- Federation scope policies are declared in the hub's configuration.
  They are evaluated at the federation boundary, before the entity
  enters the receiving hub's internal routing.
- Tamper-evident audit (for critical scope) uses cryptographic hashing
  of audit entries. The specific hash algorithm is implementation-
  dependent but MUST be collision-resistant (SHA-256 minimum).

---

## Verification Checklist

- [ ] Every entity type (data field, operation, message, agent, resource) can declare a scope level
- [ ] Scope levels form a strict ordinal hierarchy: public < internal < confidential < restricted < critical
- [ ] Undeclared entities receive the configured default scope level with a logged warning
- [ ] Scope metadata propagates across agent-to-agent transfers via message/event envelopes
- [ ] Scope metadata propagates across hub-to-hub transfers via federation envelopes
- [ ] Receiving components validate incoming scope against their operational scope
- [ ] Components reject entities that exceed their operational scope with `SCOPE_EXCEEDED` error
- [ ] Composite entities escalate to the highest scope of any non-fixed component
- [ ] Escalation emits a `scope.escalation` event with the escalation source
- [ ] Fixed propagation rule (`propagation_rule: fixed`) excludes a component from escalation
- [ ] Environment profiles modify enforcement without changing classification
- [ ] Development environment permits audit-only enforcement for restricted scope
- [ ] Production environment enforces all scope levels at maximum strictness
- [ ] Critical scope is enforced (not just audited) in ALL environments including development
- [ ] Custom labels map to a base built-in level for interoperability
- [ ] Unknown custom labels resolve to their mapped base level during cross-boundary transfers
- [ ] `scope.violation` events are emitted on every scope boundary violation
- [ ] `scope.override` events are emitted when environment profiles modify enforcement
- [ ] Both `scope` (string) and `scope_metadata` (object) fields present on all envelopes
- [ ] Scope-related errors use standard ErrorResponse format with appropriate codes
- [ ] Federation transfers preserve scope and apply receiving hub's enforcement policies
