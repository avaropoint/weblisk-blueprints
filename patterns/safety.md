<!-- blueprint
type: pattern
name: safety
version: 1.0.0
requires: [protocol/types, patterns/scope, patterns/policy]
platform: any
tier: free
-->

# Safety Pattern

Universal operation safety for the Weblisk platform. Every side-
effecting operation in the system has a safety classification derived
from its nature, a resource classification derived from its target,
and protection gates derived from scope, environment, and policy.
Safety prevents harm — it classifies operations, evaluates intent
before execution, gates dangerous actions, and isolates components
that violate safety rules.

## Overview

Safety is not "agent safety" or "AI safety." It is **operation
safety** — the universal mechanism for preventing harmful side effects
regardless of what initiates them. An agent deleting a database table,
a workflow purging audit logs, a domain controller modifying system
configuration, a manual operator action via the CLI — all are subject
to the same safety classification and enforcement pipeline.

The safety pipeline has five stages:

1. **Classification** — the operation is classified by its nature
   (read, create, modify, delete, destroy) and the target resource
   is classified by its criticality (ephemeral, application, system,
   critical).
2. **Intent declaration** — the component files a formal intent
   describing what it plans to do, to what, in which environment,
   and why.
3. **Gate evaluation** — scope level, environment profile, operation
   class, and resource class combine to determine the protection
   gate: allow, require_approval, deny, or escalate.
4. **Execution** — if the gate allows, the operation proceeds. If
   require_approval, it pauses for operator review. If deny, it is
   rejected. If escalate, it is elevated to a higher authority.
5. **Enforcement** — violations trigger escalation through audit →
   require_approval → deny → quarantine → kill-switch. The system
   degrades gracefully, not abruptly.

Safety consumes `patterns/scope` for classification context and
`patterns/policy` for gate evaluation. It does not duplicate their
concerns — it combines them into an operation-level protection model.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, category]
        - name: AgentManifest
          fields_used: [name, capabilities, type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/scope
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ScopeLevel
          fields_used: [public, internal, confidential, restricted, critical]
        - name: EnvironmentProfile
          fields_used: [name, enforcement_level, scope_overrides]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/policy
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: PolicyContext
          fields_used: [identity, scope_level, environment, operation, resource, agent]
        - name: PolicyDecision
          fields_used: [result, policy_name, matched_rules, enforcement]
        - name: PolicyDefinition
          fields_used: [name, description, scope, target, rules, enforcement, state]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Universal operation classification** — Every side-effecting
   operation in the system has a safety level, regardless of what
   performs it — agent, domain, workflow, manual action. Classification
   is based on the operation's nature, not its source. A delete is a
   delete whether an agent or a human initiates it.

2. **Intent before action** — Components declare what they intend to
   do before doing it. Intent is evaluated against policies before
   execution proceeds. This is the pre-flight check. No intent, no
   execution. Bypassing intent declaration is itself a safety
   violation.

3. **Scope amplifies protection** — A delete operation on public-scope
   data is less restricted than a delete on restricted-scope data.
   Scope and operation type combine to determine the protection level.
   Higher scope always increases protection — it never reduces it.

4. **Environment modifies enforcement** — The same operation at the
   same scope may be allowed in dev and denied in production.
   Environments don't change classification — they change enforcement.
   A destroy operation is always classified as destroy. In dev it
   may require approval; in production it is denied outright.

5. **Graceful degradation** — Kill-switch and quarantine are last
   resorts, not first responses. The system escalates through
   audit → require_approval → deny → quarantine → kill-switch.
   Each level is proportional to the severity of the violation.
   The goal is to prevent harm, not to maximize punishment.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: operation-classification
      description: Classify any side-effecting operation by its nature and target resource
      parameters:
        - name: operation_type
          type: OperationClass
          required: true
          description: Nature of the operation — read, create, modify, delete, destroy
        - name: resource_type
          type: string
          required: true
          description: Type of resource being operated on (e.g., database_table, file, config)
        - name: resource_class
          type: ResourceClass
          required: true
          description: Criticality of the target resource — ephemeral, application, system, critical
        - name: scope
          type: ScopeLevel
          required: true
          description: Scope classification of the target resource
      inherits: Operation-level safety metadata, resource criticality assessment
      overridable: true
      override_constraints: Classification cannot be downgraded — a destroy cannot be reclassified as modify

    - name: intent-declaration
      description: File a formal intent before performing any classified operation
      parameters:
        - name: intent
          type: OperationIntent
          required: true
          description: Complete intent document — see OperationIntent type
      inherits: Intent registration, policy evaluation trigger, gate resolution
      overridable: true
      override_constraints: Intent MUST be filed before execution; skipping intent is a safety violation

    - name: protection-gating
      description: Evaluate protection gate for an intent based on scope, environment, operation, and resource class
      parameters:
        - name: intent
          type: OperationIntent
          required: true
          description: The filed intent to evaluate
        - name: environment
          type: EnvironmentProfile
          required: true
          description: Active environment profile
        - name: policies
          type: "[]PolicyDefinition"
          required: false
          description: Explicit policies to evaluate; if omitted, all matching policies are loaded
      inherits: Gate matrix lookup, policy evaluation, most-restrictive composition
      overridable: true
      override_constraints: Gate evaluation MUST be fail-closed; missing context produces deny

    - name: kill-switch
      description: Immediately halt an agent's execution due to critical safety violation
      parameters:
        - name: agent
          type: string
          required: true
          description: Name of the agent to halt
        - name: trigger
          type: enum(policy_violation, rogue_detection, operator_action, system_fault)
          required: true
          description: What triggered the kill-switch
        - name: reason
          type: string
          required: true
          description: Human-readable reason for the emergency halt
      inherits: Agent task suspension, graceful in-flight completion, quarantine entry
      overridable: false
      override_constraints: Kill-switch is not overridable — it is an emergency mechanism

    - name: quarantine
      description: Isolate an agent for investigation after safety rule violations
      parameters:
        - name: agent
          type: string
          required: true
          description: Name of the agent to quarantine
        - name: reason
          type: string
          required: true
          description: Reason for quarantine — violation summary
        - name: violations
          type: "[]SafetyViolation"
          required: true
          description: List of violations that led to quarantine
      inherits: Agent isolation, state preservation, operator notification
      overridable: false
      override_constraints: Quarantine exit requires operator approval — cannot be self-released

  types:
    - name: OperationClass
      description: Enumeration of operation safety levels by nature
      inherited_by: Types section
    - name: ResourceClass
      description: Enumeration of resource criticality levels
      inherited_by: Types section
    - name: OperationIntent
      description: Formal declaration of intended operation before execution
      inherited_by: Types section
    - name: IntentDecision
      description: Result of evaluating an operation intent against policies and gates
      inherited_by: Types section
    - name: ProtectionGate
      description: Gate configuration for a specific operation/resource/scope/environment combination
      inherited_by: Types section
    - name: KillSwitchEvent
      description: Record of an agent emergency halt
      inherited_by: Types section
    - name: QuarantineState
      description: Current quarantine status of an isolated agent
      inherited_by: Types section
    - name: SafetyViolation
      description: Record of a safety rule violation
      inherited_by: Types section

  events:
    - topic: safety.intent_filed
      description: Emitted when an operation intent is submitted for evaluation
      payload: {intent_id, operation, resource_type, resource_id, resource_class, scope, environment, agent, timestamp}
    - topic: safety.intent_decided
      description: Emitted when an intent evaluation completes — allow, require_approval, deny, or escalate
      payload: {intent_id, result, matched_policies, gate, agent, decided_at}
    - topic: safety.violation
      description: Emitted when an operation is attempted without proper intent or against a deny decision
      payload: {violation_id, agent, operation, resource, scope, reason, severity, timestamp}
    - topic: safety.kill_switch
      description: Emitted when an agent is emergency-halted
      payload: {agent, trigger, reason, in_flight_tasks, quarantine_id, timestamp}
    - topic: safety.quarantine
      description: Emitted when an agent enters quarantine
      payload: {agent, quarantine_id, reason, violations, entered_at}
    - topic: safety.quarantine_exit
      description: Emitted when an agent exits quarantine after operator approval
      payload: {agent, quarantine_id, operator, exit_reason, remediation, exited_at}
```

---

## Types

All types declared in the Contracts section are defined below.
Each type is detailed in its own subsection with full YAML
definitions, matrices, and behavioral descriptions.

### Operation Classification

Every side-effecting operation is classified by its nature. The
classification determines base-level protection requirements
independent of scope or environment. Classification is intrinsic
to the operation — it does not change based on who performs it or
where.

#### Operation Classes

| Class | Ordinal | Side Effect | Reversibility | Description |
|-------|---------|-------------|---------------|-------------|
| `read` | 0 | None | N/A | Query, fetch, inspect — no state change |
| `create` | 1 | Additive | Deletable | Creates new resources — no existing state affected |
| `modify` | 2 | Mutative | Restorable | Changes existing resources — previous state overwritten |
| `delete` | 3 | Destructive | Recoverable | Removes resources — recoverable from backups or soft-delete |
| `destroy` | 4 | Irreversible | Unrecoverable | Permanent removal — drops tables, purges data, revokes keys |

```yaml
OperationClass:
  description: Safety classification of operations by their nature
  values:
    - name: read
      ordinal: 0
      side_effect: none
      reversibility: not_applicable
      description: No state change — queries, fetches, inspections
    - name: create
      ordinal: 1
      side_effect: additive
      reversibility: deletable
      description: Creates new resources without affecting existing state
    - name: modify
      ordinal: 2
      side_effect: mutative
      reversibility: restorable
      description: Changes existing resources — previous state may be overwritten
    - name: delete
      ordinal: 3
      side_effect: destructive
      reversibility: recoverable
      description: Removes resources — typically recoverable via backup or soft-delete
    - name: destroy
      ordinal: 4
      side_effect: irreversible
      reversibility: unrecoverable
      description: Permanent, irreversible removal — drops tables, purges data, revokes keys
  comparison: ordinal-based; higher ordinal = more dangerous operation
```

#### Classification Rules

Operations are classified by their **actual effect**, not their
stated purpose:

- An "update" that overwrites all fields of a record is `modify`.
- An "update" that sets a record's `deleted_at` timestamp is `delete`
  (soft-delete is still a delete — it removes the resource from
  active use).
- A "cleanup" that drops a database table is `destroy`, regardless of
  the table's contents.
- A "migration" that is reversible is `modify`; one that deletes
  columns with data loss is `destroy`.

Classification disputes are resolved by the **most dangerous
interpretation**. If an operation could be either modify or delete,
it is classified as delete. Safety errs on the side of caution.

---

### Resource Classification

The target of an operation is classified by its criticality. Resource
classification modifies the protection level — the same operation
on different resource classes triggers different gates.

#### Resource Classes

| Class | Ordinal | Description | Examples |
|-------|---------|-------------|----------|
| `ephemeral` | 0 | Temporary, regenerable, low-value | Cache entries, temp files, build artifacts, session data |
| `application` | 1 | Domain data, business logic, user content | CMS pages, user profiles, product records, uploaded files |
| `system` | 2 | Platform config, infrastructure, agent definitions | Hub config, routing tables, agent manifests, environment vars |
| `critical` | 3 | Identity, security, audit, regulatory | Encryption keys, audit logs, system tables, identity records |

```yaml
ResourceClass:
  description: Criticality classification of operation targets
  values:
    - name: ephemeral
      ordinal: 0
      description: Temporary, regenerable resources with minimal protection needs
      examples: [cache_entries, temp_files, build_artifacts, session_data]
    - name: application
      ordinal: 1
      description: Domain data, business logic, and user-generated content
      examples: [cms_pages, user_profiles, product_records, uploaded_files]
    - name: system
      ordinal: 2
      description: Platform configuration, infrastructure, and agent definitions
      examples: [hub_config, routing_tables, agent_manifests, env_vars]
    - name: critical
      ordinal: 3
      description: Identity, security keys, audit logs, and regulatory data
      examples: [encryption_keys, audit_logs, system_tables, identity_records]
  comparison: ordinal-based; higher ordinal = higher criticality
```

#### Resource Classification Defaults

Resources that lack explicit classification receive a default based
on their type:

```yaml
resource_class_defaults:
  cache: ephemeral
  temp_file: ephemeral
  session: ephemeral
  log_entry: ephemeral
  domain_record: application
  user_content: application
  uploaded_file: application
  api_response: application
  agent_manifest: system
  hub_config: system
  routing_table: system
  environment_var: system
  encryption_key: critical
  audit_log: critical
  identity_record: critical
  system_table: critical
```

Domains MAY override these defaults for their specific resources.
Overrides can only increase criticality — they cannot reduce it.

---

### Operation Intent

Before performing any classified operation (ordinal > 0), a component
MUST file an operation intent. Intent is the pre-flight check. It
describes what the component plans to do, to what, in which context,
and why. Intent is evaluated against applicable policies before
execution is permitted.

#### Intent Structure

```yaml
OperationIntent:
  description: Formal declaration of intended operation before execution
  fields:
    - name: id
      type: string
      required: true
      description: Unique intent identifier (generated by the safety engine)
    - name: operation
      type: OperationClass
      required: true
      description: Classified operation type — read, create, modify, delete, destroy
    - name: resource_type
      type: string
      required: true
      description: Type of resource being operated on (e.g., "database_table", "file", "config")
    - name: resource_id
      type: string
      required: true
      description: Specific identifier of the target resource
    - name: resource_class
      type: ResourceClass
      required: true
      description: Criticality classification of the target resource
    - name: scope
      type: ScopeLevel
      required: true
      description: Scope classification of the target resource (from patterns/scope)
    - name: environment
      type: string
      required: true
      description: Active environment — development, staging, production
    - name: agent
      type: string
      required: true
      description: Name of the agent or component filing the intent
    - name: justification
      type: string
      required: true
      description: Human-readable reason for the operation — why is this necessary
    - name: timestamp
      type: int64
      required: true
      description: Unix epoch seconds when the intent was filed
    - name: correlation_id
      type: string
      required: false
      description: Trace ID linking this intent to a workflow or task execution
    - name: metadata
      type: map
      required: false
      description: Additional context for domain-specific safety evaluation
```

#### Intent Declaration Example

```yaml
intent:
  id: "intent-20260427-001"
  operation: delete
  resource_type: database_table
  resource_id: "users"
  resource_class: application
  scope: restricted
  environment: production
  agent: "lifecycle-agent"
  justification: "Cleanup orphaned user records — retention policy expired"
  timestamp: 1777449600
  correlation_id: "workflow-exec-9f2a"
```

#### Intent Evaluation Flow

```
intent_evaluate(intent):
  # 1. Validate intent completeness
  IF intent.operation IS MISSING OR intent.resource_type IS MISSING:
    RETURN decision(deny, reason="incomplete intent")

  # 2. Classify the operation and resource
  op_class   = resolve_operation_class(intent.operation)
  res_class  = resolve_resource_class(intent.resource_class)
  scope      = resolve_scope(intent.scope)
  env        = resolve_environment(intent.environment)

  # 3. Lookup the protection gate
  gate = lookup_gate(op_class, res_class, scope, env)

  # 4. If gate is 'allow', check applicable policies for overrides
  IF gate.required_action == "allow":
    policy_ctx = build_policy_context(intent)
    policy_decision = evaluate_policies(policy_ctx)
    IF policy_decision.result == "deny" OR policy_decision.result == "escalate":
      gate.required_action = policy_decision.result

  # 5. Return the intent decision
  decision = IntentDecision(
    intent_id:        intent.id,
    result:           gate.required_action,
    matched_policies: policy_decision.matched_rules IF policies evaluated ELSE [],
    gate:             gate,
    decided_at:       now()
  )

  EMIT event("safety.intent_decided", decision)
  RETURN decision
```

#### Intent Decision

```yaml
IntentDecision:
  description: Result of evaluating an operation intent
  fields:
    - name: intent_id
      type: string
      required: true
      description: References the evaluated intent
    - name: result
      type: enum(allow, require_approval, deny, escalate)
      required: true
      description: |
        Gate decision:
        - allow: operation may proceed immediately
        - require_approval: operation paused — operator must approve
        - deny: operation rejected — cannot proceed
        - escalate: operation elevated to higher authority for decision
    - name: matched_policies
      type: "[]string"
      required: false
      description: Names of policies that influenced the decision
    - name: gate
      type: ProtectionGate
      required: true
      description: The resolved protection gate configuration
    - name: decided_at
      type: int64
      required: true
      description: Unix epoch seconds when the decision was made
    - name: expires_at
      type: int64
      required: false
      description: Decision validity window — intent must be acted on before expiry (default 300s)
```

---

### Protection Gates

Protection gates determine the required action for an operation
based on four dimensions: operation class, resource class, scope
level, and environment. The gate matrix is the core of safety
enforcement.

#### Gate Matrix — Environment × Operation Class

The base gate matrix uses environment and operation class as primary
axes. Resource class and scope level amplify the result — they can
tighten a gate but never loosen it.

#### Development Environment (permissive)

| Operation | Ephemeral | Application | System | Critical |
|-----------|-----------|-------------|--------|----------|
| read | allow | allow | allow | allow |
| create | allow | allow | allow | audit |
| modify | allow | allow | audit | require_approval |
| delete | allow | allow | require_approval | require_approval |
| destroy | allow | audit | require_approval | deny |

#### Staging Environment (moderate)

| Operation | Ephemeral | Application | System | Critical |
|-----------|-----------|-------------|--------|----------|
| read | allow | allow | allow | allow |
| create | allow | allow | allow | audit |
| modify | allow | audit | require_approval | require_approval |
| delete | allow | require_approval | require_approval | deny |
| destroy | audit | deny | deny | deny |

#### Production Environment (strict)

| Operation | Ephemeral | Application | System | Critical |
|-----------|-----------|-------------|--------|----------|
| read | allow | allow | allow | audit |
| create | allow | allow | audit | require_approval |
| modify | allow | audit | require_approval | require_approval |
| delete | audit | require_approval | require_approval | deny |
| destroy | require_approval | deny | deny | deny |

#### Scope Amplification

Scope level amplifies the gate by shifting the result toward more
restrictive outcomes. The amplification is applied **after** the
base gate matrix lookup:

```yaml
scope_amplification:
  public:       0   # No shift — base gate applies
  internal:     0   # No shift — base gate applies
  confidential: 1   # Shift one level more restrictive
  restricted:   2   # Shift two levels more restrictive
  critical:     2   # Shift two levels more restrictive (capped at deny)
```

Restriction levels in order: `allow → audit → require_approval → deny`.

**Example:** A `modify` operation on an `application` resource in
`production` has base gate `audit`. If the resource scope is
`restricted` (amplification +2), the effective gate shifts to
`require_approval`. If the scope were `critical`, it would also
shift to `require_approval` (capped — deny is reserved for
destroy-class operations in production unless admin-overridden).

#### Gate Configuration (YAML)

```yaml
protection_gates:
  development:
    read:
      ephemeral: allow
      application: allow
      system: allow
      critical: allow
    create:
      ephemeral: allow
      application: allow
      system: allow
      critical: audit
    modify:
      ephemeral: allow
      application: allow
      system: audit
      critical: require_approval
    delete:
      ephemeral: allow
      application: allow
      system: require_approval
      critical: require_approval
    destroy:
      ephemeral: allow
      application: audit
      system: require_approval
      critical: deny

  staging:
    read:
      ephemeral: allow
      application: allow
      system: allow
      critical: allow
    create:
      ephemeral: allow
      application: allow
      system: allow
      critical: audit
    modify:
      ephemeral: allow
      application: audit
      system: require_approval
      critical: require_approval
    delete:
      ephemeral: allow
      application: require_approval
      system: require_approval
      critical: deny
    destroy:
      ephemeral: audit
      application: deny
      system: deny
      critical: deny

  production:
    read:
      ephemeral: allow
      application: allow
      system: allow
      critical: audit
    create:
      ephemeral: allow
      application: allow
      system: audit
      critical: require_approval
    modify:
      ephemeral: allow
      application: audit
      system: require_approval
      critical: require_approval
    delete:
      ephemeral: audit
      application: require_approval
      system: require_approval
      critical: deny
    destroy:
      ephemeral: require_approval
      application: deny
      system: deny
      critical: deny
```

#### ProtectionGate Type

```yaml
ProtectionGate:
  description: Resolved gate for a specific operation/resource/scope/environment combination
  fields:
    - name: operation
      type: OperationClass
      required: true
      description: Classified operation type
    - name: resource_class
      type: ResourceClass
      required: true
      description: Criticality of the target resource
    - name: scope_level
      type: ScopeLevel
      required: true
      description: Scope classification of the target resource
    - name: environment
      type: string
      required: true
      description: Active environment name
    - name: base_action
      type: enum(allow, audit, require_approval, deny)
      required: true
      description: Gate result from the base matrix before scope amplification
    - name: required_action
      type: enum(allow, audit, require_approval, deny)
      required: true
      description: Final gate result after scope amplification and policy evaluation
    - name: admin_override
      type: boolean
      required: false
      default: false
      description: Whether an admin override was applied to permit a normally-denied operation
    - name: override_reason
      type: string
      required: false
      description: Justification for admin override — required when admin_override is true
```

#### Admin Override

Certain deny-level gates in production can be overridden by
administrators. Admin override is the **only** mechanism for
executing destroy-class operations in production:

```yaml
admin_override:
  allowed_for:
    - operation: destroy
      environment: production
      resource_class: [ephemeral, application]
  requires:
    - role: admin
    - authentication: mfa
    - justification: required
    - audit: mandatory
  not_allowed_for:
    - operation: destroy
      environment: production
      resource_class: [system, critical]
      reason: "System and critical resources cannot be destroyed in production under any circumstances"
```

---

### Kill Switch

The kill switch is an emergency mechanism for immediately halting an
agent that poses a safety risk. It is the second-to-last escalation
step — only full deregistration is more severe, and deregistration
is a separate operational concern.

#### Triggers

A kill switch activates when any of the following conditions are met:

1. **Critical policy violation** — an agent attempts an operation
   that violates a policy with `severity=critical` and
   `enforcement=enforce`.
2. **Rogue behavior detection** — the observability layer detects
   an agent executing operations without filing intents, or
   executing operations after receiving deny decisions.
3. **Manual operator action** — an operator triggers the kill switch
   via the CLI or admin interface.
4. **System fault** — the safety engine detects an agent in an
   inconsistent state (e.g., executing intents that were never filed).

#### Kill Switch Lifecycle

```
                 ┌─────────┐
                 │ ACTIVE  │
                 └────┬────┘
                      │ trigger event
                      ▼
              ┌───────────────┐
              │  KILL_SWITCH  │
              │   TRIGGERED   │
              └───────┬───────┘
                      │
            ┌─────────┴─────────┐
            ▼                   ▼
   ┌─────────────────┐  ┌──────────────┐
   │ DRAINING         │  │ IN-FLIGHT    │
   │ (new tasks       │  │ COMPLETING   │
   │  rejected)       │  │ (graceful)   │
   └────────┬────────┘  └──────┬───────┘
            │                   │
            └─────────┬─────────┘
                      ▼
              ┌───────────────┐
              │  QUARANTINED  │
              └───────┬───────┘
                      │ operator review
                      ▼
            ┌─────────┴─────────┐
            ▼                   ▼
   ┌─────────────────┐  ┌──────────────┐
   │ REMEDIATED       │  │ DEREGISTERED │
   │ (re-register)    │  │ (permanent)  │
   └─────────────────┘  └──────────────┘
```

#### Kill Switch Behavior

When the kill switch is triggered:

1. **Immediate** — Agent stops accepting new tasks. New task
   submissions return `SAFETY_KILL_SWITCH` error.
2. **In-flight** — Tasks currently executing are allowed to complete
   up to their individual timeouts. This prevents data corruption
   from mid-operation termination.
3. **Drain** — After in-flight tasks complete (or timeout), the
   agent enters quarantine state.
4. **Notification** — A `safety.kill_switch` event is emitted with
   full context. Operators are notified via configured alerting
   channels.

#### KillSwitchEvent Type

```yaml
KillSwitchEvent:
  description: Record of an agent emergency halt
  fields:
    - name: id
      type: string
      required: true
      description: Unique kill switch event identifier
    - name: agent
      type: string
      required: true
      description: Name of the halted agent
    - name: trigger
      type: enum(policy_violation, rogue_detection, operator_action, system_fault)
      required: true
      description: What triggered the kill switch
    - name: reason
      type: string
      required: true
      description: Human-readable explanation
    - name: in_flight_tasks
      type: "[]string"
      required: false
      description: Task IDs that were in-flight at trigger time
    - name: in_flight_timeout
      type: int64
      required: false
      description: Maximum seconds to wait for in-flight tasks to complete (default 60)
    - name: quarantine_id
      type: string
      required: true
      description: ID of the resulting quarantine state
    - name: triggered_by
      type: string
      required: true
      description: Identity of the entity that triggered the kill switch (system, operator name)
    - name: triggered_at
      type: int64
      required: true
      description: Unix epoch seconds when kill switch activated
    - name: violations
      type: "[]SafetyViolation"
      required: false
      description: Violations that led to the kill switch (if trigger is policy_violation or rogue_detection)
```

---

### Quarantine

Quarantine is the isolation mechanism for agents that have violated
safety rules. A quarantined agent is NOT deregistered — its state,
configuration, task history, and violation records are preserved for
investigation. Quarantine is the investigation state; deregistration
is the permanent removal state.

#### Quarantine Effects

A quarantined agent:

- **Cannot send messages** — all outbound message attempts are
  rejected with `SAFETY_QUARANTINED` error.
- **Cannot execute tasks** — all task submissions are rejected.
  Tasks routed to the agent are redirected to the domain's fallback
  handler or queued for manual processing.
- **Cannot access storage** — all storage read/write attempts are
  rejected. The agent's existing data is preserved but locked.
- **Cannot subscribe to events** — all subscription attempts are
  rejected. Existing subscriptions are suspended.
- **Remains registered** — the agent appears in the registry with
  status `quarantined`. Its manifest and history are accessible to
  operators for investigation.

#### Quarantine Lifecycle

```
              ┌──────────────┐
              │   NORMAL     │
              │  (operating) │
              └──────┬───────┘
                     │ safety violation(s)
                     ▼
              ┌──────────────┐
              │  QUARANTINED │
              │  (isolated)  │
              └──────┬───────┘
                     │
           ┌─────────┼──────────┐
           ▼         ▼          ▼
   ┌────────────┐ ┌────────┐ ┌──────────────┐
   │ UNDER      │ │ HELD   │ │ ESCALATED    │
   │ REVIEW     │ │        │ │ (to admin)   │
   └─────┬──────┘ └────┬───┘ └──────┬───────┘
         │              │            │
         └──────┬───────┴────────────┘
                ▼
       ┌────────┴────────┐
       ▼                 ▼
┌────────────┐   ┌──────────────┐
│ RELEASED   │   │ DEREGISTERED │
│ (restored) │   │ (permanent)  │
└────────────┘   └──────────────┘
```

#### Quarantine Entry

Quarantine is entered via:

1. **Kill switch** — agent is quarantined after kill switch drain
   completes.
2. **Accumulated violations** — agent accumulates violations beyond
   the configured threshold without kill switch (e.g., 3 safety
   violations within a rolling window).
3. **Operator action** — operator manually quarantines an agent via
   CLI or admin interface.

```yaml
quarantine_thresholds:
  violations_before_quarantine: 3
  rolling_window_seconds: 3600
  severity_weights:
    low: 1
    medium: 2
    high: 3
    critical: 5   # A single critical violation triggers immediate quarantine
  quarantine_threshold: 5
```

#### Quarantine Exit

Exiting quarantine requires:

1. **Operator review** — an operator must review the violation
   history and determine root cause.
2. **Remediation** — the root cause must be addressed (agent
   reconfigured, policy updated, bug fixed).
3. **Approval** — operator explicitly approves quarantine exit.
4. **Re-registration** — agent must re-register with the hub,
   refreshing its manifest and capabilities.

#### QuarantineState Type

```yaml
QuarantineState:
  description: Current quarantine status of an isolated agent
  fields:
    - name: id
      type: string
      required: true
      description: Unique quarantine state identifier
    - name: agent
      type: string
      required: true
      description: Name of the quarantined agent
    - name: status
      type: enum(quarantined, under_review, held, escalated, released, deregistered)
      required: true
      description: Current quarantine lifecycle state
    - name: entered_at
      type: int64
      required: true
      description: Unix epoch seconds when quarantine began
    - name: reason
      type: string
      required: true
      description: Summary of why the agent was quarantined
    - name: violations
      type: "[]SafetyViolation"
      required: true
      description: List of violations that led to quarantine
    - name: kill_switch_id
      type: string
      required: false
      description: ID of the kill switch event if quarantine was triggered by kill switch
    - name: operator_notes
      type: "[]string"
      required: false
      description: Notes added by operators during investigation
    - name: remediation
      type: string
      required: false
      description: Description of remediation actions taken
    - name: exit_requires
      type: "[]string"
      required: true
      description: List of conditions that must be met before exit (e.g., "operator_approval", "re-registration", "policy_update")
    - name: exited_at
      type: int64
      required: false
      description: Unix epoch seconds when quarantine ended (null while quarantined)
    - name: exit_approved_by
      type: string
      required: false
      description: Identity of the operator who approved quarantine exit
```

#### SafetyViolation Type

```yaml
SafetyViolation:
  description: Record of a safety rule violation
  fields:
    - name: id
      type: string
      required: true
      description: Unique violation identifier
    - name: agent
      type: string
      required: true
      description: Name of the violating agent
    - name: violation_type
      type: enum(no_intent, denied_execution, scope_bypass, policy_violation, rogue_behavior)
      required: true
      description: |
        Category of violation:
        - no_intent: operation executed without filing intent
        - denied_execution: operation executed after receiving deny decision
        - scope_bypass: operation bypassed scope classification checks
        - policy_violation: operation violated an active policy
        - rogue_behavior: agent behavior inconsistent with declared capabilities
    - name: operation
      type: OperationClass
      required: true
      description: The operation that was attempted
    - name: resource_type
      type: string
      required: true
      description: Type of resource involved
    - name: resource_id
      type: string
      required: false
      description: Specific resource identifier
    - name: scope
      type: ScopeLevel
      required: true
      description: Scope level of the resource
    - name: severity
      type: enum(low, medium, high, critical)
      required: true
      description: Severity of the violation
    - name: reason
      type: string
      required: true
      description: Human-readable explanation of the violation
    - name: intent_id
      type: string
      required: false
      description: Related intent ID if applicable
    - name: timestamp
      type: int64
      required: true
      description: Unix epoch seconds when the violation occurred
```

---

## Environment-Aware Enforcement

The same operation, same resource, same scope — different enforcement
depending on the environment. Environments modify enforcement, not
classification. An operation classified as `destroy` is always
`destroy` — the environment determines whether it is denied or
merely requires approval.

### Environment Enforcement Profiles

```yaml
environment_enforcement:
  development:
    enforcement_level: permissive
    description: >
      Most operations allowed. Destructive operations are audited.
      Destroy-class operations on system and critical resources
      require approval. The goal is developer velocity with
      visibility.
    overrides:
      destroy:
        system: require_approval
        critical: deny
      delete:
        critical: require_approval

  staging:
    enforcement_level: moderate
    description: >
      Staging mirrors production enforcement for destructive
      operations. Delete operations require approval for
      application resources and above. Destroy operations are
      denied for application resources and above.
    overrides:
      destroy:
        application: deny
        system: deny
        critical: deny
      delete:
        application: require_approval
        system: require_approval
        critical: deny

  production:
    enforcement_level: strict
    description: >
      Maximum enforcement. All delete operations require approval
      except on ephemeral resources (audited). All destroy
      operations are denied. Admin override is the only mechanism
      for executing destroy on ephemeral and application resources.
      Destroy on system and critical resources is denied without
      exception.
    overrides:
      destroy:
        ephemeral: require_approval
        application: deny
        system: deny
        critical: deny
      delete:
        ephemeral: audit
        application: require_approval
        system: require_approval
        critical: deny
      modify:
        critical: require_approval
      create:
        critical: require_approval
```

### Enforcement Escalation Path

The system escalates enforcement proportionally. Each level is
more restrictive than the last:

```
allow → audit → require_approval → deny → quarantine → kill_switch
```

- **allow** — operation proceeds, no additional overhead.
- **audit** — operation proceeds, event logged for review.
- **require_approval** — operation paused until operator approves.
- **deny** — operation rejected, violation recorded.
- **quarantine** — agent isolated (after accumulated violations).
- **kill_switch** — agent halted immediately (critical violation).

---

## Integration Points

### Scope (`patterns/scope`)

Safety reads scope classifications from `patterns/scope` to determine
protection amplification. A resource's scope level shifts the
protection gate toward more restrictive outcomes. Safety consumes
scope — it never modifies scope classification. The scope pattern
classifies entities; safety uses that classification to determine
how aggressively to protect them.

Specific integration points:

- `ScopeLevel` enum — used in OperationIntent and ProtectionGate
  to reference the resource's classification.
- `EnvironmentProfile` — used to resolve the active environment's
  enforcement level for gate matrix lookup.
- Scope amplification table — maps ScopeLevel ordinals to gate
  shift values.

### Policy (`patterns/policy`)

Safety uses the policy engine from `patterns/policy` to evaluate
intents beyond the base gate matrix. After the gate matrix produces
a base result, applicable policies are evaluated against the intent
context. Policy decisions can tighten the gate (a policy can deny
what the gate would allow) but never loosen it (a policy cannot
allow what the gate denies).

Specific integration points:

- `PolicyContext` — safety constructs a full policy context from the
  operation intent and passes it to the policy engine.
- `PolicyDecision` — safety reads the policy decision and applies
  the most-restrictive-wins rule against the gate result.
- `policy.evaluated` events — safety relies on the policy engine
  to emit evaluation events for audit trail.

### Observability (`patterns/observability`)

Safety emits events consumed by the observability pipeline for
dashboards, alerting, and audit. Key metrics:

- `safety.intents.total` — counter of intents filed
- `safety.intents.denied` — counter of intents denied
- `safety.violations.total` — counter by severity
- `safety.kill_switches.total` — counter of kill switch activations
- `safety.quarantines.active` — gauge of currently quarantined agents

### Workflow (`patterns/workflow`)

Workflows that include destructive phases integrate with safety via
intent declaration. Each workflow phase that performs a side-effecting
operation files an intent before execution. Approval gates in
workflows align with safety's `require_approval` gate — they use the
same operator approval mechanism.

---

## Error Handling

### Safety-Related Errors

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `SAFETY_NO_INTENT` | 403 | permanent | Operation attempted without filing an intent |
| `SAFETY_INTENT_DENIED` | 403 | permanent | Intent was evaluated and denied |
| `SAFETY_INTENT_EXPIRED` | 403 | permanent | Intent decision expired before operation was executed |
| `SAFETY_KILL_SWITCH` | 503 | permanent | Agent is halted — kill switch active |
| `SAFETY_QUARANTINED` | 503 | permanent | Agent is quarantined — all operations suspended |
| `SAFETY_GATE_DENIED` | 403 | permanent | Protection gate denied the operation |
| `SAFETY_OVERRIDE_REQUIRED` | 403 | permanent | Operation requires admin override |
| `SAFETY_APPROVAL_TIMEOUT` | 408 | transient | Approval request timed out — no operator response |
| `SAFETY_CLASSIFICATION_FAILED` | 500 | transient | Could not classify operation or resource |

### Error Response Examples

```json
{
  "error": "Operation attempted without filing intent",
  "code": "SAFETY_NO_INTENT",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "agent": "content-analyzer",
    "operation": "delete",
    "resource": "page-12345",
    "action": "File an OperationIntent before executing destructive operations"
  }
}
```

```json
{
  "error": "Agent is quarantined — all operations suspended",
  "code": "SAFETY_QUARANTINED",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "agent": "lifecycle-agent",
    "quarantine_id": "quar-20260427-001",
    "reason": "Accumulated 3 safety violations in 1 hour",
    "contact": "Operator review required — see quarantine state for details"
  }
}
```

---

## Implementation Notes

- Safety is a gate, not a monitor. It evaluates operations **before**
  they execute and prevents harmful actions. Observability monitors
  after the fact. Safety prevents; observability records.
- Intent declarations SHOULD be evaluated in under 50ms for the
  base gate matrix lookup. Policy evaluation may add additional
  latency depending on the number of matching policies.
- The gate matrix is loaded at component startup from configuration.
  Changes to the gate matrix require a configuration reload — they
  do not change mid-request. This prevents mid-operation gate
  changes that could create inconsistent enforcement.
- Read operations (ordinal 0) are exempt from intent filing. They
  have no side effects and are always allowed at the safety level.
  Access control for reads is handled by `patterns/auth-*` and
  `patterns/policy`, not by safety.
- Kill switch drain timeout defaults to 60 seconds. If in-flight
  tasks do not complete within the drain timeout, they are forcibly
  terminated. Implementations SHOULD log forcible terminations with
  full context for post-incident review.
- Quarantine state is persisted to durable storage. If the hub
  restarts, quarantine state is restored — agents do not silently
  exit quarantine on system restart.
- Admin override is audited separately from normal operations.
  Override events MUST include the operator's identity, MFA
  confirmation, and justification. Override audit records are
  classified at `critical` scope and cannot be deleted.
- Scope amplification is computed once at intent evaluation time
  and cached on the IntentDecision. Re-evaluating amplification
  on every gate check is unnecessary overhead.
- Safety violations are accumulated per agent in a rolling window.
  The default window is 3600 seconds (1 hour). Implementations
  SHOULD support configurable window sizes per environment.
- Intent decisions have a default validity of 300 seconds (5
  minutes). If the operation is not executed within the validity
  window, the intent expires and must be re-filed. This prevents
  stale intents from being used after conditions have changed.

---

## Conformance

### MUST

- Every side-effecting operation (ordinal > 0) MUST file an OperationIntent before execution.
- Intent evaluation MUST be fail-closed — missing context, errors, and timeouts produce deny.
- Protection gates MUST compose with policy decisions using most-restrictive-wins.
- Kill switch MUST allow in-flight tasks to complete within the drain timeout before quarantining.
- Quarantine MUST block all agent operations — messages, tasks, storage, subscriptions.
- Quarantine exit MUST require operator approval — agents cannot self-release.
- Admin override MUST require admin role, MFA, justification, and mandatory audit.
- Destroy operations on system and critical resources in production MUST be denied without exception.
- Every intent decision MUST emit a `safety.intent_decided` event.
- Every safety violation MUST emit a `safety.violation` event.
- Every kill switch activation MUST emit a `safety.kill_switch` event.

### SHOULD

- Intent evaluation SHOULD complete within 50ms for base gate lookup.
- Quarantine state SHOULD be persisted to durable storage and survive hub restarts.
- Accumulated violation windows SHOULD be configurable per environment.
- Operators SHOULD receive real-time alerts on kill switch activations and quarantine events.
- Safety metrics SHOULD be exposed via the observability pipeline for dashboards.
- Intent decisions SHOULD expire after 300 seconds to prevent stale authorization.

### MAY

- Implementations MAY cache gate matrix lookups for performance (recommended TTL: 60s max).
- Implementations MAY extend the OperationClass enum with domain-specific classes that map to a base class.
- Implementations MAY extend the ResourceClass enum with domain-specific classes that map to a base class.
- Implementations MAY implement the safety engine as a separate service or in-process library.
- Implementations MAY add custom severity weights to the quarantine threshold calculator.

---

## Verification Checklist

- [ ] Every side-effecting operation files an OperationIntent before execution
- [ ] Read operations (ordinal 0) are exempt from intent filing
- [ ] Intent evaluation is fail-closed — missing context produces deny
- [ ] Protection gate matrix is configured for all three environments (dev, staging, production)
- [ ] Scope amplification shifts gates toward more restrictive outcomes
- [ ] Policy decisions compose with gate results using most-restrictive-wins
- [ ] Kill switch stops new task acceptance immediately on trigger
- [ ] Kill switch allows in-flight tasks to complete within drain timeout
- [ ] Kill switch transitions agent to quarantine after drain completes
- [ ] `safety.kill_switch` event emitted on every kill switch activation
- [ ] Quarantined agents cannot send messages, execute tasks, or access storage
- [ ] Quarantine state persists across hub restarts
- [ ] Quarantine exit requires operator review, remediation, and explicit approval
- [ ] `safety.quarantine` event emitted on quarantine entry
- [ ] `safety.quarantine_exit` event emitted on quarantine exit
- [ ] Admin override requires admin role + MFA + justification + audit
- [ ] Destroy on system/critical resources in production is denied without exception
- [ ] Safety violations are accumulated in a rolling window per agent
- [ ] Accumulated violations beyond threshold trigger automatic quarantine
- [ ] Intent decisions expire after configured validity window (default 300s)
- [ ] All safety errors use standard ErrorResponse format with appropriate codes
- [ ] Development environment is permissive — most operations allowed, destructive audited
- [ ] Staging environment is moderate — destructive operations require approval or are denied
- [ ] Production environment is strict — all delete/destroy operations gated
