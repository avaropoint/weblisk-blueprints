<!-- blueprint
type: pattern
name: state-machine
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/observability, patterns/expression]
platform: any
tier: free
-->

# State Machine Pattern

Standard format for declaring state machines in agent and domain
blueprints. Defines states, transitions, guards, side effects, and
event emission. Agents `extends: patterns/state-machine` and declare
their specific states — the pattern provides the structural contract
and runtime behavior.

## Overview

State machines appear throughout the Weblisk framework:

- **Incident response**: detected → triaging → executing → resolved
- **Health monitoring**: unknown → online → degraded → offline
- **Cron jobs**: pending → running → completed → failed
- **Blue-green deployments**: building → shadowing → active → retired
- **Webhook deliveries**: pending → delivering → success → failed

Each agent invents its own format. This pattern standardizes the
declaration so that tools can visualize, validate, and enforce state
machines consistently.

---
## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TypeDefinition
          fields_used: [name, fields, description]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: LogEvent
          fields_used: [event_type, level, detail, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/expression
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ExpressionGrammar
          fields_used: [path, comparison, logical_operators]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Declarative over imperative** — State machines are declared in YAML, not coded; tools can visualize, validate, and enforce them from the declaration alone.
2. **Persist before effect** — State changes are persisted to storage before side effects execute, ensuring consistency even when effects fail.
3. **Atomic transitions** — State transitions use optimistic locking to prevent race conditions; no entity can be in two states simultaneously.
4. **Terminal states are final** — Once an entity enters a terminal state, no further transitions are valid, enforcing lifecycle completion.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: state-transition
      description: Validate and execute state transitions with guards and effects
      parameters:
        - name: entity_type
          type: string
          required: true
          description: The type this state machine governs
        - name: state_field
          type: string
          required: true
          description: Which field on the entity holds the current state
        - name: initial_state
          type: string
          required: true
          description: Starting state for new entities
      inherits: State validation, guard evaluation, and effect execution pipeline
      overridable: true
      override_constraints: Must declare all states and transitions; initial_state must be valid
    - name: timeout-auto-transition
      description: Automatically transition entities when a timeout duration expires
      parameters:
        - name: duration
          type: int
          required: true
          description: Seconds before auto-transition fires
        - name: transition
          type: string
          required: true
          description: Target state on timeout
      inherits: Timer-based escalation and recovery
      overridable: true
      override_constraints: Duration must be > 0
  types:
    - name: StateMachineDefinition
      description: Complete state machine declaration with states, transitions, guards, and effects
      inherited_by: State Declaration section
    - name: StateDefinition
      description: Individual state with description, terminal flag, and optional timeout
      inherited_by: States section
    - name: TransitionDefinition
      description: Transition with from/to states, trigger, guard, and effects
      inherited_by: Transitions section
    - name: EffectDefinition
      description: Side effect executed on transition (emit_event, send_alert, update_field, etc.)
      inherited_by: Effects section
  events:
    - topic: state.transition_completed
      description: Emitted after a successful state transition
      payload: {entity_type, entity_id, from, to, trigger, timestamp}
    - topic: state.transition_rejected
      description: Emitted when a guard prevents a transition
      payload: {entity_type, entity_id, from, attempted_to, guard, reason, timestamp}
```

---
## State Declaration

```yaml
state_machines:
  <machine_name>:
    description: <one-line>
    initial_state: <state_name>
    entity_type: <TypeName>        # the type this machine governs
    state_field: <field_name>      # which field holds the state

    states:
      <state_name>:
        description: <one-line>
        terminal: <bool>           # default: false — terminal states cannot transition out
        timeout:                   # optional — auto-transition after duration
          duration: <seconds>
          transition: <target_state>
          
    transitions:
      - name: <transition_name>
        from: <state> | [<states>]
        to: <state>
        trigger: <event_name> | manual
        guard: <condition>         # optional — must be true for transition
        effects: [<effect_names>]  # optional — side effects on transition
        description: <one-line>
```

---

## States

Each state has:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| description | string | yes | What this state represents |
| terminal | boolean | no | If true, no transitions out are allowed. Default: false |
| timeout | object | no | Auto-transition after duration expires |
| timeout.duration | int | yes (if timeout) | Seconds before auto-transition |
| timeout.transition | string | yes (if timeout) | Target state on timeout |

### Terminal States

Terminal states represent completed lifecycles. Once an entity enters
a terminal state, no further transitions are valid:

```yaml
states:
  resolved:
    description: Incident fully resolved
    terminal: true
  expired:
    description: Delivery attempts exhausted
    terminal: true
```

### Timeout States

Timeout states auto-transition when a duration expires. Used for
escalation, retry scheduling, and circuit breaker recovery:

```yaml
states:
  awaiting_operator:
    description: Waiting for human acknowledgment
    timeout:
      duration: 3600           # 1 hour
      transition: escalated    # auto-escalate if no response
```

---

## Transitions

Each transition has:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Unique identifier for this transition |
| from | string or []string | yes | Source state(s) |
| to | string | yes | Target state |
| trigger | string | yes | Event or `manual` |
| guard | string | no | Condition expression that must be true |
| effects | []string | no | Side effects executed on transition |
| description | string | yes | What this transition represents |

### Guards

Guards are boolean conditions evaluated before a transition is
allowed. If the guard returns false, the transition is rejected:

```yaml
transitions:
  - name: retry
    from: failed
    to: pending
    trigger: retry_requested
    guard: "attempts < max_retries"
    description: Re-queue for retry if attempts remain

  - name: deactivate_subscriber
    from: active
    to: inactive
    trigger: delivery_failed
    guard: "consecutive_failures >= 3"
    description: Deactivate subscriber after repeated failures
```

Guards reference fields on the governed entity type. Guard expressions
use the [expression language](expression.md) with the **State Machine
Context** — paths resolve against `entity.*` (current entity fields),
`transition.*` (from, to, trigger), and `now` (current timestamp).

### Multi-Source Transitions

A transition may originate from multiple states:

```yaml
transitions:
  - name: force_offline
    from: [online, degraded, unknown]
    to: offline
    trigger: admin_override
    description: Admin forces component offline for maintenance
```

---

## Effects

Effects are side actions executed when a transition completes. They
run AFTER the state change is persisted.

```yaml
effects:
  <effect_name>:
    type: <effect_type>
    config: <type-specific config>
```

### Effect Types

| Type | Description | Config |
|------|-------------|--------|
| `emit_event` | Publish event to message bus | `{event: "<name>", data: <template>}` |
| `send_alert` | Route alert to alerting agent | `{severity: "<level>", title: "<text>"}` |
| `schedule_timeout` | Start a timeout timer | `{duration: <seconds>, transition: "<name>"}` |
| `cancel_timeout` | Cancel a pending timeout | `{state: "<state_name>"}` |
| `update_field` | Set a field on the entity | `{field: "<name>", value: <expression>}` |
| `log` | Write to structured log | `{level: "<level>", message: "<text>"}` |

### Example Effects

```yaml
effects:
  notify_state_change:
    type: emit_event
    config:
      event: "incident.state_changed"
      data:
        incident_id: "$entity.id"
        from: "$transition.from"
        to: "$transition.to"
        timestamp: "$now"

  alert_escalation:
    type: send_alert
    config:
      severity: high
      title: "Incident $entity.id escalated — no operator response in $timeout.duration seconds"

  reset_failure_counter:
    type: update_field
    config:
      field: consecutive_failures
      value: 0

  start_escalation_timer:
    type: schedule_timeout
    config:
      duration: 3600
      transition: escalate
```

---

## Complete Example: Incident Lifecycle

```yaml
state_machines:
  incident:
    description: Incident detection through resolution lifecycle
    initial_state: detected
    entity_type: Incident
    state_field: state

    states:
      detected:
        description: Alert received, incident created
      triaging:
        description: Correlating with other alerts and system state
      runbook_executing:
        description: Automated runbook in progress
      auto_resolved:
        description: Runbook resolved without human intervention
        terminal: true
      escalated:
        description: Automated remediation insufficient
      awaiting_operator:
        description: Waiting for human acknowledgment
        timeout:
          duration: 3600
          transition: escalated
      resolved:
        description: Incident closed by operator or confirmed auto-resolution
        terminal: true

    transitions:
      - name: begin_triage
        from: detected
        to: triaging
        trigger: correlation_complete
        effects: [notify_state_change]
        description: Begin correlating alert with system state

      - name: start_runbook
        from: triaging
        to: runbook_executing
        trigger: runbook_matched
        effects: [notify_state_change, start_runbook_timer]
        description: Matching runbook found, begin execution

      - name: auto_resolve
        from: runbook_executing
        to: auto_resolved
        trigger: runbook_succeeded
        effects: [notify_state_change, generate_post_incident_report]
        description: Runbook remediation succeeded

      - name: escalate_from_runbook
        from: runbook_executing
        to: escalated
        trigger: runbook_failed
        effects: [notify_state_change, alert_escalation]
        description: Runbook remediation failed

      - name: escalate_timeout
        from: awaiting_operator
        to: escalated
        trigger: timeout
        effects: [notify_state_change, alert_escalation]
        description: No operator response within timeout

      - name: await_operator
        from: [triaging, escalated]
        to: awaiting_operator
        trigger: operator_needed
        effects: [notify_state_change, start_escalation_timer]
        description: Human judgment required

      - name: resolve
        from: [awaiting_operator, escalated, runbook_executing]
        to: resolved
        trigger: operator_resolved
        effects: [notify_state_change, cancel_escalation_timer, generate_post_incident_report]
        description: Operator resolves incident

    effects:
      notify_state_change:
        type: emit_event
        config:
          event: "incident.state_changed"
          data:
            incident_id: "$entity.id"
            from: "$transition.from"
            to: "$transition.to"

      alert_escalation:
        type: send_alert
        config:
          severity: high
          title: "Incident $entity.id requires escalation"

      start_runbook_timer:
        type: schedule_timeout
        config:
          duration: 300
          transition: escalate_from_runbook

      start_escalation_timer:
        type: schedule_timeout
        config:
          duration: 3600
          transition: escalate_timeout

      cancel_escalation_timer:
        type: cancel_timeout
        config:
          state: awaiting_operator

      generate_post_incident_report:
        type: emit_event
        config:
          event: "incident.report_requested"
          data:
            incident_id: "$entity.id"
```

---

## Validation Rules

State machine declarations are validated at agent startup:

1. `initial_state` MUST reference a declared state
2. Every transition `from` and `to` MUST reference declared states
3. Terminal states MUST NOT appear as `from` in any transition
4. Every non-terminal state MUST have at least one outbound transition
5. Every state MUST be reachable from `initial_state` via transitions
6. Effect names in transitions MUST reference declared effects
7. Guard expressions MUST reference valid fields on `entity_type`
8. Timeout transitions MUST reference valid transition names

---

## Visualization

State machines can be rendered as Mermaid diagrams for documentation:

```
stateDiagram-v2
    [*] --> detected
    detected --> triaging: correlation_complete
    triaging --> runbook_executing: runbook_matched
    triaging --> awaiting_operator: operator_needed
    runbook_executing --> auto_resolved: runbook_succeeded
    runbook_executing --> escalated: runbook_failed
    awaiting_operator --> escalated: timeout
    escalated --> awaiting_operator: operator_needed
    awaiting_operator --> resolved: operator_resolved
    escalated --> resolved: operator_resolved
    auto_resolved --> [*]
    resolved --> [*]
```

Implementations SHOULD auto-generate Mermaid from the YAML declaration.

---

## Implementation Notes

- **Persistence**: State changes MUST be persisted before effects
  execute. If effects fail, the state change is still valid.
- **Idempotency**: Applying the same transition twice to an entity
  already in the target state SHOULD be a no-op (not an error).
- **Concurrency**: State transitions MUST be atomic — use optimistic
  locking (check current state before update) to prevent race
  conditions.
- **Audit trail**: Every state transition SHOULD be logged with
  timestamp, from/to states, trigger, and acting entity.
- **Effect ordering**: Effects execute in array order. If an effect
  fails, subsequent effects still execute (effects are best-effort).

## Verification Checklist

- [ ] All states declared with descriptions
- [ ] initial_state references a valid state
- [ ] Terminal states have no outbound transitions
- [ ] All non-terminal states have at least one outbound transition
- [ ] All states reachable from initial_state
- [ ] Guards reference valid entity fields
- [ ] Effects declared for all referenced effect names
- [ ] Timeout states auto-transition after duration
- [ ] State transitions are atomic (optimistic locking)
- [ ] State changes persisted before effects execute
- [ ] Transition audit trail logged
