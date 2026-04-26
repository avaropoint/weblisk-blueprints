<!-- blueprint
type: architecture
name: change-management
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/orchestrator, architecture/agent, architecture/lifecycle, patterns/messaging, patterns/versioning]
platform: any
-->

# Change Management

Dependency contracts, change cascade, reconciliation, and blue-green
agent versioning. This blueprint governs how the ecosystem responds
when any blueprint changes — ensuring zero-impact propagation through
self-governing agents.

## Overview

Every blueprint in the Weblisk ecosystem is a living specification.
When one changes, every agent that depends on it must evaluate the
impact, reconcile its own state, and potentially version-bump itself.
This creates a **reconciliation wavefront** — a controlled cascade
of self-governance that propagates through the dependency graph until
every affected agent has either adapted or flagged for intervention.

The protocol is built on three principles:

1. **Binding-level precision** — agents declare exactly which endpoints,
   types, fields, events, and config keys they consume from each
   dependency. Impact analysis is computed at the binding level, not
   the blueprint level.
2. **Self-governance** — each agent evaluates its own impact and
   reconciles autonomously. The orchestrator tracks progress but does
   not dictate agent behavior.
3. **Blue-green safety** — when reconciliation requires a version bump,
   the new version is built and validated alongside the old one before
   traffic cuts over. Rollback is always possible.

---

## Dependency Contracts

### Contract Schema

Every agent declares its dependencies as **contracts** — not just
references but precise bindings to the specific parts of each
dependency it consumes.

```yaml
contract_schema:
  blueprint:
    type: string
    description: Path to the dependency blueprint (e.g. protocol/spec)

  version:
    type: string
    format: semver-range
    description: >
      Semver range this agent is compatible with.
      Examples: ">=1.0.0 <2.0.0", "^1.2.0", "~1.3"

  bindings:
    description: >
      Explicit declarations of what this agent uses from the
      dependency. Only bound items are tracked for change impact.
    sections:
      endpoints:
        description: HTTP endpoints consumed
        fields:
          path:           { type: string, description: "Route path" }
          methods:        { type: string[], description: "HTTP methods used" }
          request_type:   { type: string, optional: true, description: "Request body type name" }
          response_fields: { type: string[], description: "Response fields consumed" }

      types:
        description: Type definitions consumed
        fields:
          name:           { type: string, description: "Type name from dependency" }
          fields_used:    { type: string[], description: "Specific fields consumed" }

      events:
        description: Event topics subscribed to from this dependency
        fields:
          topic:          { type: string, description: "Event topic name" }
          fields_used:    { type: string[], description: "Payload fields consumed" }

      config:
        description: Configuration keys referenced
        fields:
          key:            { type: string, description: "Config key name" }
          usage:          { type: string, description: "How this agent uses the value" }

      patterns:
        description: Pattern behaviors inherited
        fields:
          behavior:       { type: string, description: "Specific behavior name" }
          parameters:     { type: string[], description: "Parameters this agent configures" }

  on_change:
    description: >
      How the agent responds to changes in this dependency,
      classified by change severity.
    fields:
      compatible:
        type: string
        enum: [ignore, validate, validate-and-adopt]
        description: >
          Additive, non-breaking changes (new optional fields,
          new endpoints, new event topics).
      breaking:
        type: string
        enum: [halt-and-reconcile, version-bump, halt-immediately]
        description: >
          Changes that alter or remove bound items (renamed fields,
          changed types, removed endpoints).
      removed:
        type: string
        enum: [halt-immediately, degrade-gracefully]
        description: >
          Bound item no longer exists in the dependency.
```

### Example: Cron Agent Dependency Contract

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
          request_type: AgentManifest
          response_fields: [agent_id, token, services]
        - path: /v1/message
          methods: [POST]
          request_type: MessageEnvelope
          response_fields: [status, response]
        - path: /v1/health
          methods: [GET]
          response_fields: [status, details]
      types:
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: MessageEnvelope
          fields_used: [from, to, action, payload, trace_id]
        - name: HealthResponse
          fields_used: [status, details]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
          request_type: AgentManifest
          response_fields: [agent_id, token]
        - path: /v1/services
          methods: [GET]
          response_fields: [agents]
      events:
        - topic: system.agent.registered
          fields_used: [agent_name, manifest]
        - topic: system.agent.deregistered
          fields_used: [agent_name]
        - topic: system.shutdown
          fields_used: []
        - topic: system.blueprint.changed
          fields_used: [blueprint_name, version, diff]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: sqlite-engine
          parameters: [engine, tables, indexes, relationships, constraints]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

extends:
  - pattern: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: publish
          parameters: [topic, payload, source]
        - behavior: subscribe
          parameters: [topic, handler, consumer_group]
        - behavior: dead-letter
          parameters: [max_retries, dlq_topic]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/retry
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: retry-with-backoff
          parameters: [max_retries, backoff_strategy, timeout]
        - behavior: circuit-breaker
          parameters: [failure_threshold, recovery_timeout]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

### Version Ranges

Version compatibility uses semantic versioning ranges:

```yaml
version_semantics:
  major:
    meaning: Breaking changes — removed or restructured bindings
    impact: Agents pinned to previous major MUST version-bump
    example: "protocol/spec 1.x → 2.0 renames /v1/register to /v2/register"

  minor:
    meaning: Additive changes — new fields, endpoints, events
    impact: Agents MAY adopt new features, existing bindings unaffected
    example: "protocol/spec 1.2 → 1.3 adds 'tags' field to AgentManifest"

  patch:
    meaning: Bug fixes, documentation, clarifications
    impact: No binding changes — agents are unaffected
    example: "protocol/spec 1.2.0 → 1.2.1 fixes typo in description"
```

### Transitive Dependencies

If agent A depends on blueprint B, and B depends on blueprint C, a
change to C may affect A transitively.

```yaml
transitive_resolution:
  strategy: full-graph-walk

  process:
    1: Orchestrator maintains a complete dependency graph
    2: When blueprint C changes, compute all direct dependents (B)
    3: For each direct dependent, check if the change affects
       any binding that B exposes to its own dependents
    4: If yes, propagate assessment to B's dependents (A)
    5: Continue until no further propagation is needed

  depth_limit: 10
  cycle_detection: required
  cycle_resolution: >
    If a cycle is detected, flag for operator intervention.
    Cycles in the dependency graph are a design error and MUST
    be resolved by refactoring.

  example:
    change: "protocol/types adds 'priority' field to TaskRequest"
    direct: "protocol/spec uses TaskRequest → assess protocol/spec"
    transitive: >
      protocol/spec binding for TaskRequest unchanged (new field
      is optional, additive) → no propagation to spec's dependents.
      If spec had CHANGED its binding (e.g. made 'priority' required),
      then agents binding to spec's TaskRequest would be assessed.
```

---

## Change Detection

### Diff Computation

When a blueprint is updated, the orchestrator computes a structured
diff between the old and new versions:

```yaml
diff_schema:
  blueprint:     { type: string }
  version_from:  { type: string }
  version_to:    { type: string }
  timestamp:     { type: int64 }

  changes:
    - path:      { type: string, description: "Dot-notation path to changed element" }
      kind:      { type: string, enum: [added, modified, removed, renamed] }
      old_value: { type: any, optional: true }
      new_value: { type: any, optional: true }
      breaking:  { type: bool }

  # Example diff entries:
  examples:
    - path: "types.AgentManifest.fields.tags"
      kind: added
      new_value: { type: "string[]", optional: true }
      breaking: false

    - path: "endpoints./v1/register.methods"
      kind: modified
      old_value: [POST, DELETE]
      new_value: [PUT, DELETE]
      breaking: true

    - path: "types.TaskRequest.fields.priority"
      kind: removed
      old_value: { type: int, default: 0 }
      breaking: true
```

### Impact Classification

For each dependent agent, the orchestrator maps the diff against
the agent's declared bindings:

```yaml
impact_classification:
  none:
    description: No bound items affected
    example: "New endpoint added, agent doesn't use it"
    action: Log, no reconciliation needed

  compatible:
    description: Only additive changes to bound items
    example: "New optional field added to a type the agent uses"
    action: Agent's on_change.compatible rule applies

  breaking:
    description: Bound items modified or behavioral contract changed
    example: "Field type changed, endpoint method changed"
    action: Agent's on_change.breaking rule applies

  removed:
    description: Bound item no longer exists
    example: "Endpoint deleted, type removed, event topic renamed"
    action: Agent's on_change.removed rule applies

  out_of_range:
    description: New version outside agent's declared version range
    example: "Agent pins >=1.0.0 <2.0.0, dependency bumps to 2.0.0"
    action: Halt immediately, flag for version-bump
```

---

## Change Cascade Protocol

### Phase 1 — Detection

```
Trigger:  Blueprint X is updated (file change, API push, or
          system.blueprint.changed event)

Step 1:   Orchestrator loads old version (from storage) and new version
Step 2:   Compute structured diff (per diff_schema)
Step 3:   Classify each change as breaking or non-breaking
Step 4:   Build change_record:
            {blueprint, version_from, version_to, diff, timestamp}
Step 5:   Store change_record in change_history
Step 6:   Emit: system.blueprint.updated
            {blueprint, version_from, version_to, change_id}
```

### Phase 2 — Impact Assessment

```
Step 7:   Walk dependency graph — find all agents that declare
            requires: or extends: referencing blueprint X
Step 8:   For each dependent agent:
            a. Load agent's dependency contract for X
            b. Check version range — is new version in range?
            c. Map each diff entry against agent's bindings
            d. Classify impact: none | compatible | breaking | removed | out_of_range
            e. Build assessment:
                 {agent, change_id, impact, affected_bindings[],
                  recommended_action, on_change_rule}
Step 9:   Check transitive dependencies:
            a. For each dependent that ALSO exposes bindings
               (architecture docs, patterns)
            b. Assess whether the change flows through to their dependents
            c. If yes, add transitive assessments to the queue
Step 10:  Emit per agent: system.change.assessment
            {agent, change_id, impact, affected_bindings[],
             recommended_action, deadline}
Step 11:  Log: change.assessment_complete
            {change_id, agents_assessed, by_impact: {none, compatible, breaking, removed}}
```

### Phase 3 — Reconciliation

Each agent receives its assessment and self-governs:

```
Step 12:  Agent receives system.change.assessment
Step 13:  Agent evaluates impact against its own state:

          If impact = none:
            Log: change.acknowledged {change_id, result: "no_impact"}
            Emit: system.change.reconciliation.result
              {agent, change_id, result: "no_impact"}
            Done.

          If impact = compatible AND on_change = validate:
            Run self-validation (health check, test fixtures)
            If pass → log + emit result: "validated"
            If fail → escalate to breaking path

          If impact = compatible AND on_change = validate-and-adopt:
            Run self-validation
            If pass → adopt new bindings (update internal state)
            Log + emit result: "adopted" with {changes_adopted[]}
            If fail → escalate to breaking path

          If impact = breaking AND on_change = version-bump:
            Initiate blue-green deployment (see below)
            Log + emit result: "version_bump_initiated"
              with {new_version, deployment_id}

          If impact = breaking AND on_change = halt-and-reconcile:
            Pause active work (return 503 for new requests)
            Attempt migration (per patterns/versioning)
            If success → resume, log + emit result: "reconciled"
            If fail → rollback, emit result: "failed"
              with {error, rollback_applied: true}

          If impact = removed OR out_of_range:
            If on_change = halt-immediately:
              Enter degraded state
              Log: change.halted {change_id, reason}
              Emit: system.change.reconciliation.result
                {agent, change_id, result: "halted", requires_operator: true}
            If on_change = degrade-gracefully:
              Disable features that depend on removed bindings
              Continue operating with reduced capability
              Emit result: "degraded" with {disabled_features[]}
```

### Phase 4 — Ecosystem Tracking

```
Step 14:  Orchestrator collects all reconciliation results:
            Track: {change_id, total_agents, by_result:
              {no_impact, validated, adopted, reconciled,
               version_bump_initiated, halted, failed}}

Step 15:  If ALL agents report success (no_impact, validated,
          adopted, reconciled, or version_bump_initiated):
            Change is complete.
            Log: change.cascade_complete {change_id, duration}
            Emit: system.change.cascade.complete {change_id}

Step 16:  If ANY agent reports "failed":
            Evaluate failure scope:
            a. If failed agent is non-critical → log warning,
               continue (operator notified)
            b. If failed agent is critical → trigger ecosystem rollback

Step 17:  Ecosystem rollback (if triggered):
            a. Emit: system.change.rollback {change_id, reason}
            b. Restore blueprint X to previous version
            c. All agents that already reconciled receive a NEW
               assessment for the rollback (version_to → version_from)
            d. Agents reverse their reconciliation
            e. Track rollback completion same as forward cascade
            Log: change.rollback_complete {change_id, agents_rolled_back}

Step 18:  Deadline enforcement:
            If any agent has not reported reconciliation within
            the deadline (default: 5 minutes):
            a. Emit: system.change.reconciliation.timeout
                 {agent, change_id}
            b. Flag agent as unresponsive
            c. Operator notified — manual intervention required
```

---

## Blue-Green Agent Versioning

When reconciliation determines that an agent needs a version bump
(schema migration, behavioral change, new bindings), the agent
does NOT update in place. Instead, it deploys a new version alongside
the old one and performs a controlled cutover.

### When Blue-Green Is Required

```yaml
blue_green_triggers:
  - condition: on_change.breaking = version-bump
    description: Agent's contract declares version-bump for breaking changes

  - condition: Schema migration required
    description: Types or storage schema changes that need migration

  - condition: Behavioral contract change
    description: Action processing logic must change to match new dependency

  - condition: Manual version bump
    description: Operator or CI/CD initiates a version bump
```

### Deployment Phases

```
Phase 1 — Build
  Trigger:    Reconciliation identifies need for version bump
  Action:     Generate new agent specification:
                a. Increment agent version (per semver — major if
                   breaking contract change, minor otherwise)
                b. Update dependency contracts to pin new versions
                c. Update bindings to reflect new dependency shapes
                d. Generate storage migration plan (if schema changed)
  Validates:  New specification parses and passes schema validation
  Output:     New agent blueprint (version N+1), migration plan
  Emit:       system.agent.version.building
                {agent, current_version, new_version, change_id}

Phase 2 — Deploy
  Action:     Start new agent instance (version N+1):
                a. Instance starts with its own identity (new keypair)
                b. Follows standard startup lifecycle
                c. Registers with orchestrator as agent_name@vN+1
                d. Orchestrator recognizes this as a blue-green deploy
                   (same agent name, different version)
                e. Storage: connect to same database
                f. Run schema migration (if needed) with versioning
                   pattern (additive-only until cutover)
  Pre-check:  Current agent (vN) is healthy
  Validates:  New instance (vN+1) reaches "active" state
  On Fail:    Tear down vN+1, log error, emit deployment.failed
  Emit:       system.agent.version.deployed
                {agent, new_version, instance_id}

Phase 3 — Shadow
  Action:     New instance subscribes to the same event topics but
              in SHADOW MODE:
                a. Receives events but does not act on them
                b. Validates it CAN process each event correctly
                c. Runs action inputs through validation (no writes)
                d. Compares its decisions with vN's actual behavior
              Duration: config.shadow_duration (default: 60 seconds)
                or N successful shadow validations (default: 10)
  Validates:  Shadow pass rate >= config.shadow_threshold (default: 100%)
  On Fail:    If shadow pass rate < threshold:
                Log: version.shadow_failed {pass_rate, failures[]}
                Tear down vN+1
                Emit: system.agent.version.shadow_failed
                Reconciliation result: "failed"
  Emit:       system.agent.version.shadow_passed
                {agent, new_version, events_validated, pass_rate}

Phase 4 — Cutover
  Pre-check:  Phase 3 passed, vN healthy, vN+1 healthy
  Action:
    Step 1:   vN stops accepting new work (returns 503)
    Step 2:   vN drains in-flight work (per shutdown sequence)
    Step 3:   If schema migration has destructive steps
              (column removal, constraint tightening):
                Execute destructive migration steps now
    Step 4:   Orchestrator updates service directory:
                agent_name routes to vN+1 instance
    Step 5:   Message bus updates subscriptions:
                vN+1 subscriptions become active (exit shadow mode)
                vN subscriptions are removed
    Step 6:   vN+1 is now the active agent
  Validates:
    a. First real event processed successfully by vN+1
    b. Health check returns healthy
    c. No errors within first config.cutover_watch_period (default: 120s)
  On Fail:    Trigger automatic rollback (Phase 5)
  Emit:       system.agent.version.cutover
                {agent, from_version, to_version}

Phase 5 — Retire or Rollback
  On success (cutover validated):
    Step 1:   vN deregisters from orchestrator
    Step 2:   vN closes storage connections
    Step 3:   vN process exits
    Emit:     system.agent.version.retired
                {agent, retired_version, active_version, uptime}
    Log:      lifecycle.version_retired

  On failure (cutover failed):
    Step 1:   vN+1 stops immediately (no drain — it's the broken one)
    Step 2:   Orchestrator reverts service directory to vN
    Step 3:   Message bus reverts subscriptions to vN
    Step 4:   vN resumes accepting work (clear 503 state)
    Step 5:   If destructive migration was applied, run reverse migration
    Step 6:   vN+1 process is torn down
    Emit:     system.agent.version.rollback
                {agent, failed_version, restored_version, reason}
    Log:      lifecycle.version_rollback
    Reconciliation result: "failed" with {rollback_applied: true}
```

### Cutover Strategies

```yaml
cutover_strategies:
  immediate:
    description: >
      Full traffic shift at once. Previous version drains and exits.
    when: Schema migration is all-or-nothing
    risk: Highest — failure requires full rollback
    default: true

  canary:
    description: >
      Route a percentage of traffic to new version. Gradually
      increase if metrics are healthy.
    when: High-traffic agents where gradual validation is preferred
    risk: Lower — can stop at any percentage
    config:
      initial_percent: 10
      step_percent: 20
      step_interval: 60   # seconds between increases
      health_threshold: 99 # percent success rate to continue
      rollback_threshold: 95

  parallel:
    description: >
      Both versions process all events. Compare results.
      Only cut over when parity is confirmed.
    when: Critical agents where correctness must be verified
    risk: Lowest — old version continues handling real work
    duration: 300  # seconds of parallel operation
    parity_threshold: 100  # percent result match required
```

### Configuration

```yaml
blue_green_config:
  shadow_duration:
    type: int
    default: 60
    unit: seconds
    description: How long vN+1 runs in shadow mode

  shadow_events_required:
    type: int
    default: 10
    description: Minimum events validated during shadow phase

  shadow_threshold:
    type: float
    default: 1.0
    description: Required shadow pass rate (0.0 to 1.0)

  cutover_watch_period:
    type: int
    default: 120
    unit: seconds
    description: Post-cutover monitoring window

  cutover_strategy:
    type: string
    default: immediate
    enum: [immediate, canary, parallel]

  max_deployment_duration:
    type: int
    default: 600
    unit: seconds
    description: Total time allowed for build→deploy→shadow→cutover

  keep_retired_logs:
    type: bool
    default: true
    description: Retain vN logs after retirement
```

---

## Scaling Model

Multi-instance agents and change propagation require strict
communication rules.

### Inter-Agent Communication

```yaml
inter_agent:
  protocol: message-bus-only

  rules:
    - rule: All asynchronous agent-to-agent communication MUST go
            through the message bus
      reason: >
        Direct HTTP creates coupling to specific instances.
        The bus handles routing, load balancing, and failover.
      enforcement: >
        Agents publish to topics or send to agent NAMEs —
        never to specific host:port. The bus resolves the target.

    - rule: Synchronous request/response uses POST /v1/message
            via the orchestrator's routing
      reason: >
        The orchestrator's service directory resolves agent names
        to instances. Callers never hard-code target addresses.
      enforcement: >
        POST /v1/message addressed to agent name. Orchestrator
        or bus routes to a healthy instance.

    - rule: Agents MUST NOT discover or cache other agents' addresses
      reason: >
        Instance addresses change during scaling and blue-green
        deploys. Only the orchestrator and bus know current routing.
      exception: >
        Agents cache the service directory for target validation
        (e.g. cron checks if target_agent exists). But they never
        use cached addresses for direct communication.

  during_blue_green:
    - rule: During cutover, the bus routes to the designated version
    - rule: Shadow-mode instances receive events but responses are
            discarded by the bus
    - rule: After cutover, the old version's subscriptions are removed
            within one tick_interval
```

### Intra-Agent Coordination

```yaml
intra_agent:
  description: >
    Multiple instances of the SAME agent share storage and coordinate
    via leader election. This is distinct from inter-agent communication.

  coordination: shared-storage

  leader_election:
    mechanism: Storage lock with TTL (same pattern as cron_locks)
    responsibilities:
      leader: [tick_evaluation, schedule_advancement, cleanup, migration]
      follower: [health_reporting, action_handling, standby, event_subscription]
    promotion: Automatic when leader lock expires
    leader_count: Exactly 1 per agent type

  state_sharing:
    mechanism: Shared database
    consistency: >
      All instances read/write the same storage. If instance A
      pauses a task, instance B sees the status change on its
      next storage read. Consistency window = tick_interval.
    conflict_resolution: >
      Last-write-wins for simple fields. Storage constraints
      (unique, check) prevent invalid concurrent writes.
      Leader election prevents duplicate processing.

  event_handling:
    bus_events: >
      All instances subscribe to their agent's event topics.
      The bus delivers each event to ONE instance per consumer
      group (not all instances). Consumer group = agent_name.
    deduplication: >
      Actions that arrive via direct message may hit any instance.
      Idempotency via storage constraints (e.g. uq_task_natural_key)
      prevents duplicate processing.

  during_blue_green:
    - vN instances and vN+1 instances share the same database
    - vN+1 uses a separate consumer group during shadow phase
    - After cutover, vN consumer group is removed
    - Storage migration uses additive-only changes until cutover
      to ensure both versions can read/write simultaneously
```

### Message Routing During Versioning

```
Normal operation:
  message → bus → resolve agent_name → route to any healthy instance

Shadow phase:
  message → bus → resolve agent_name
    → route to vN instance (real processing)
    → copy to vN+1 instance (shadow — validate only, discard response)

Cutover (immediate):
  Step 1: vN stops accepting → bus removes vN from routing
  Step 2: vN+1 becomes primary → bus routes all new messages to vN+1
  Step 3: In-flight messages to vN complete normally

Cutover (canary):
  Step 1: Bus routes X% to vN+1, (100-X)% to vN
  Step 2: Orchestrator monitors health metrics
  Step 3: Gradually increase X% per cutover_strategies.canary config
  Step 4: At 100% → retire vN

Rollback:
  Step 1: Bus removes vN+1 from routing
  Step 2: vN resumes accepting messages
  Step 3: Any in-flight messages to vN+1 are re-routed to vN
           (if idempotent) or logged as lost (if not)
```

---

## Events

```yaml
events:
  # Change detection
  - topic: system.blueprint.updated
    source: orchestrator
    payload:
      blueprint:     { type: string }
      version_from:  { type: string }
      version_to:    { type: string }
      change_id:     { type: string, format: uuid-v7 }
      diff_summary:  { type: string, description: "Human-readable change summary" }
    when: Any blueprint is updated

  # Impact assessment (per affected agent)
  - topic: system.change.assessment
    source: orchestrator
    payload:
      agent:              { type: string }
      change_id:          { type: string }
      impact:             { type: string, enum: [none, compatible, breaking, removed, out_of_range] }
      affected_bindings:  { type: object[], description: "List of bindings affected" }
      recommended_action: { type: string }
      deadline:           { type: int64, description: "Reconciliation deadline timestamp" }
    when: Per agent after impact assessment

  # Reconciliation results (per agent)
  - topic: system.change.reconciliation.started
    source: affected-agent
    payload:
      agent:     { type: string }
      change_id: { type: string }
      strategy:  { type: string, enum: [validate, adopt, migrate, version-bump] }
    when: Agent begins reconciliation

  - topic: system.change.reconciliation.result
    source: affected-agent
    payload:
      agent:              { type: string }
      change_id:          { type: string }
      result:             { type: string, enum: [no_impact, validated, adopted, reconciled, version_bump_initiated, halted, degraded, failed] }
      changes_applied:    { type: string[], optional: true }
      requires_operator:  { type: bool, default: false }
      error:              { type: string, optional: true }
      rollback_applied:   { type: bool, default: false }
    when: Agent completes reconciliation

  - topic: system.change.reconciliation.timeout
    source: orchestrator
    payload:
      agent:     { type: string }
      change_id: { type: string }
      deadline:  { type: int64 }
    when: Agent did not report within deadline

  # Cascade tracking
  - topic: system.change.cascade.complete
    source: orchestrator
    payload:
      change_id:  { type: string }
      duration:   { type: int, unit: seconds }
      results:    { type: object, description: "Aggregated by_result counts" }
    when: All agents have reported reconciliation

  # Rollback
  - topic: system.change.rollback
    source: orchestrator
    payload:
      change_id:       { type: string }
      reason:          { type: string }
      failed_agents:   { type: string[] }
    when: Ecosystem-wide rollback triggered

  # Blue-green versioning
  - topic: system.agent.version.building
    source: affected-agent
    payload:
      agent:            { type: string }
      current_version:  { type: string }
      new_version:      { type: string }
      change_id:        { type: string }
    when: Agent begins building new version

  - topic: system.agent.version.deployed
    source: orchestrator
    payload:
      agent:        { type: string }
      new_version:  { type: string }
      instance_id:  { type: string }
    when: New version instance reaches active state

  - topic: system.agent.version.shadow_passed
    source: affected-agent
    payload:
      agent:              { type: string }
      new_version:        { type: string }
      events_validated:   { type: int }
      pass_rate:          { type: float }
    when: Shadow validation passes threshold

  - topic: system.agent.version.shadow_failed
    source: affected-agent
    payload:
      agent:        { type: string }
      new_version:  { type: string }
      pass_rate:    { type: float }
      failures:     { type: object[] }
    when: Shadow validation fails threshold

  - topic: system.agent.version.cutover
    source: orchestrator
    payload:
      agent:          { type: string }
      from_version:   { type: string }
      to_version:     { type: string }
      strategy:       { type: string, enum: [immediate, canary, parallel] }
    when: Traffic shifted to new version

  - topic: system.agent.version.retired
    source: orchestrator
    payload:
      agent:            { type: string }
      retired_version:  { type: string }
      active_version:   { type: string }
      uptime:           { type: int, unit: seconds }
    when: Old version shut down

  - topic: system.agent.version.rollback
    source: orchestrator
    payload:
      agent:             { type: string }
      failed_version:    { type: string }
      restored_version:  { type: string }
      reason:            { type: string }
    when: Blue-green deployment rolled back
```

---

## Types

```yaml
types:
  DependencyContract:
    description: An agent's binding-level dependency declaration
    fields:
      blueprint:
        type: string
        description: Path to dependency blueprint
      version:
        type: string
        format: semver-range
        description: Compatible version range
      bindings:
        type: BindingSet
        description: Specific items consumed from this dependency
      on_change:
        type: OnChangePolicy
        description: Response rules per change severity

  BindingSet:
    description: Collection of specific bindings to a dependency
    fields:
      endpoints:
        type: EndpointBinding[]
        optional: true
      types:
        type: TypeBinding[]
        optional: true
      events:
        type: EventBinding[]
        optional: true
      config:
        type: ConfigBinding[]
        optional: true
      patterns:
        type: PatternBinding[]
        optional: true

  EndpointBinding:
    fields:
      path:             { type: string }
      methods:          { type: string[] }
      request_type:     { type: string, optional: true }
      response_fields:  { type: string[] }

  TypeBinding:
    fields:
      name:             { type: string }
      fields_used:      { type: string[] }

  EventBinding:
    fields:
      topic:            { type: string }
      fields_used:      { type: string[] }

  ConfigBinding:
    fields:
      key:              { type: string }
      usage:            { type: string }

  PatternBinding:
    fields:
      behavior:         { type: string }
      parameters:       { type: string[] }

  OnChangePolicy:
    fields:
      compatible:
        type: string
        enum: [ignore, validate, validate-and-adopt]
      breaking:
        type: string
        enum: [halt-and-reconcile, version-bump, halt-immediately]
      removed:
        type: string
        enum: [halt-immediately, degrade-gracefully]

  ChangeRecord:
    description: Record of a blueprint change
    fields:
      change_id:
        type: string
        format: uuid-v7
      blueprint:
        type: string
      version_from:
        type: string
      version_to:
        type: string
      diff:
        type: DiffEntry[]
      timestamp:
        type: int64

  DiffEntry:
    fields:
      path:
        type: string
        description: Dot-notation path to changed element
      kind:
        type: string
        enum: [added, modified, removed, renamed]
      old_value:
        type: any
        optional: true
      new_value:
        type: any
        optional: true
      breaking:
        type: bool

  ChangeAssessment:
    description: Impact assessment for a single agent
    fields:
      agent:
        type: string
      change_id:
        type: string
        references: ChangeRecord.change_id
      impact:
        type: string
        enum: [none, compatible, breaking, removed, out_of_range]
      affected_bindings:
        type: object[]
      recommended_action:
        type: string
      deadline:
        type: int64

  ReconciliationResult:
    description: Outcome of an agent's reconciliation
    fields:
      agent:
        type: string
      change_id:
        type: string
        references: ChangeRecord.change_id
      result:
        type: string
        enum: [no_impact, validated, adopted, reconciled,
               version_bump_initiated, halted, degraded, failed]
      changes_applied:
        type: string[]
        optional: true
      requires_operator:
        type: bool
        default: false
      error:
        type: string
        optional: true
      rollback_applied:
        type: bool
        default: false
      timestamp:
        type: int64

  DeploymentRecord:
    description: Blue-green deployment tracking
    fields:
      deployment_id:
        type: string
        format: uuid-v7
      agent:
        type: string
      change_id:
        type: string
        references: ChangeRecord.change_id
      current_version:
        type: string
      new_version:
        type: string
      phase:
        type: string
        enum: [building, deployed, shadow, cutover, retired, rolled_back, failed]
      strategy:
        type: string
        enum: [immediate, canary, parallel]
      started_at:
        type: int64
      completed_at:
        type: int64
        optional: true
      shadow_pass_rate:
        type: float
        optional: true
```

---

## State Machine

```yaml
state_machine:
  change_cascade:
    initial: detected
    transitions:
      - from: detected
        to: assessing
        trigger: Diff computed, dependency graph walked
        validates: At least one dependent agent found

      - from: assessing
        to: reconciling
        trigger: All assessments emitted
        validates: Every dependent agent received assessment

      - from: reconciling
        to: complete
        trigger: All agents reported success
        validates: No "failed" or "halted" results

      - from: reconciling
        to: rolling_back
        trigger: Critical agent reported "failed"
        validates: Rollback decision made by orchestrator

      - from: reconciling
        to: partial
        trigger: Non-critical agent failed, others succeeded
        validates: Operator notified of degraded agents

      - from: rolling_back
        to: rolled_back
        trigger: All agents reversed reconciliation
        validates: Blueprint restored to previous version

      - from: reconciling
        to: timed_out
        trigger: Deadline exceeded for one or more agents
        validates: Timeout event emitted per agent

  blue_green_deployment:
    initial: building
    transitions:
      - from: building
        to: deployed
        trigger: New instance reaches active state
        validates: Health check passes

      - from: deployed
        to: shadow
        trigger: Shadow mode subscriptions active
        validates: First shadow event received

      - from: shadow
        to: cutover
        trigger: Shadow pass rate >= threshold
        validates: Both versions healthy

      - from: cutover
        to: retired
        trigger: Watch period elapsed, no errors
        validates: vN+1 processing successfully

      - from: cutover
        to: rolled_back
        trigger: Error during watch period
        validates: vN restored to active

      - from: shadow
        to: failed
        trigger: Shadow pass rate < threshold
        validates: vN+1 torn down

      - from: building
        to: failed
        trigger: New instance fails startup
        validates: vN unaffected
```

---

## Storage

The orchestrator maintains change management state:

```yaml
storage:
  engine: sqlite

  tables:
    change_records:
      source_type: ChangeRecord
      primary_key: change_id
      indexes:
        - name: idx_change_blueprint
          fields: [blueprint, timestamp]
          type: btree

    change_assessments:
      source_type: ChangeAssessment
      primary_key: [agent, change_id]
      indexes:
        - name: idx_assessment_change
          fields: [change_id]
          type: btree
        - name: idx_assessment_impact
          fields: [impact]
          type: btree

    reconciliation_results:
      source_type: ReconciliationResult
      primary_key: [agent, change_id]
      indexes:
        - name: idx_reconciliation_change
          fields: [change_id]
          type: btree
        - name: idx_reconciliation_result
          fields: [result]
          type: btree

    deployment_records:
      source_type: DeploymentRecord
      primary_key: deployment_id
      indexes:
        - name: idx_deployment_agent
          fields: [agent, started_at]
          type: btree
        - name: idx_deployment_phase
          fields: [phase]
          type: btree

  relationships:
    - name: change_assessments
      from: change_assessments.change_id
      to: change_records.change_id
      cardinality: many-to-one
      on_delete: cascade
      on_update: restrict

    - name: reconciliation_results
      from: reconciliation_results.change_id
      to: change_records.change_id
      cardinality: many-to-one
      on_delete: cascade
      on_update: restrict

    - name: deployment_change
      from: deployment_records.change_id
      to: change_records.change_id
      cardinality: many-to-one
      on_delete: restrict
      on_update: restrict

  retention:
    change_records:
      policy: 90 days
      cleanup: daily
    change_assessments:
      policy: 90 days
      cleanup: cascaded from change_records
    reconciliation_results:
      policy: 90 days
      cleanup: cascaded from change_records
    deployment_records:
      policy: 180 days
      cleanup: daily
```

---

## Constraints

```yaml
constraints:
  ordering:
    - Changes to the SAME blueprint MUST be processed serially
    - Changes to DIFFERENT blueprints MAY be processed concurrently
    - If concurrent changes share dependents, assessments are merged

  safety:
    - Blue-green deployment MUST NOT proceed if current version is unhealthy
    - Shadow phase MUST validate at least shadow_events_required events
    - Cutover MUST NOT proceed during another active blue-green deployment
      for the same agent
    - Rollback MUST always be possible — destructive migration steps are
      deferred until cutover confirmation

  limits:
    max_concurrent_changes: 5
    max_concurrent_deployments: 3
    reconciliation_deadline: 300  # seconds
    deployment_timeout: 600  # seconds
    max_dependency_depth: 10

  invariants:
    - Every ChangeRecord has at least one ChangeAssessment
    - Every ChangeAssessment eventually has a ReconciliationResult
      (or a timeout event)
    - A DeploymentRecord in "retired" phase is immutable
    - The dependency graph MUST be acyclic
```

---

## Verification Checklist

- [ ] Dependency contracts declare version ranges (semver)
- [ ] Bindings specify exact endpoints, types, fields, events used
- [ ] on_change rules defined for compatible, breaking, and removed
- [ ] Orchestrator computes structured diff on blueprint update
- [ ] Impact classification maps diff entries against agent bindings
- [ ] system.change.assessment emitted per affected agent
- [ ] Transitive dependencies resolved (full graph walk)
- [ ] Cycle detection flags circular dependencies
- [ ] Agents self-govern reconciliation per on_change policy
- [ ] Reconciliation results tracked per agent per change
- [ ] Ecosystem rollback triggers when critical agent fails
- [ ] Reconciliation deadline enforced with timeout events
- [ ] Blue-green: new version starts alongside old version
- [ ] Blue-green: shadow mode validates without side effects
- [ ] Blue-green: cutover shifts traffic atomically
- [ ] Blue-green: rollback restores previous version within seconds
- [ ] Blue-green: destructive migrations deferred until cutover confirmed
- [ ] Scaling: inter-agent communication is message-bus-only
- [ ] Scaling: intra-agent coordination via shared storage + leader election
- [ ] Scaling: message routing by agent name, never by instance address
- [ ] Scaling: during blue-green, bus routes shadow traffic correctly
- [ ] All events published with correct topics and payloads
- [ ] Change records, assessments, and results persisted with relationships
- [ ] Deployment records track full blue-green lifecycle
- [ ] Concurrent changes to same blueprint serialized
- [ ] Operator notified for halted/failed reconciliation
