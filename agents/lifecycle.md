<!-- blueprint
type: agent
kind: infrastructure
name: lifecycle
version: 1.0.0
extends: [patterns/scope, patterns/policy]
requires: [protocol/spec, protocol/types, architecture/agent, architecture/lifecycle, patterns/messaging]
platform: any
tier: free
port: 9782
-->

# Lifecycle Agent

Infrastructure agent that owns the continuous optimization loop.
Manages strategies, entity context, observations, recommendations,
approvals, feedback, and agent metrics. Subscribes globally
(scope: `"*"`) to workflow completion events to capture results
across the entire hub.

See [architecture/lifecycle.md](../architecture/lifecycle.md) for the
full lifecycle specification.

---

## Dependencies

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
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
        - name: WorkflowResult
          fields_used: [workflow_name, invoker, status, phase_results, observations, recommendations]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: startup-sequence
          parameters: [identity, storage, registration, health]
        - behavior: shutdown-sequence
          parameters: [drain, deregister, close]
        - behavior: health-reporting
          parameters: [status, details]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/lifecycle
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: observation-loop
          parameters: [observe, recommend, approve, apply, feedback]
        - behavior: strategy-management
          parameters: [create, decompose, track, complete]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: publish
          parameters: [topic, payload, source]
        - behavior: subscribe
          parameters: [topic, handler, consumer_group]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

depends_on: []
  # No runtime agent dependencies. The lifecycle agent subscribes
  # to workflow.completed/failed with scope "*" but does not require
  # any specific agent to be running. If workflow agent is unavailable,
  # lifecycle simply receives no events.
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  Strategy:
    description: High-level optimization objective
    fields:
      strategy_id:
        type: string
        format: uuid-v7
        description: Unique strategy identifier
      name:
        type: string
        max: 128
        description: Human-readable strategy name
      objective:
        type: string
        max: 512
        description: What this strategy aims to achieve
      targets:
        type: array
        items: StrategyTarget
        description: Measurable targets for this strategy
      priority:
        type: string
        enum: [critical, high, normal, low]
        description: Strategy priority
      status:
        type: string
        enum: [active, paused, completed, abandoned]
        description: Current strategy state
      created_at:
        type: int64
        auto: true
        description: Creation timestamp
      updated_at:
        type: int64
        auto: true
        description: Last modification timestamp

  StrategyTarget:
    description: Measurable target within a strategy
    fields:
      metric_name:
        type: string
        description: Metric to track
      domain:
        type: string
        description: Source domain for this metric
      current_value:
        type: float
        optional: true
        description: Last observed value
      target_value:
        type: float
        description: Desired value
      progress:
        type: float
        min: 0.0
        max: 1.0
        description: Progress toward target (0.0 to 1.0)

  Observation:
    description: Recorded observation from a workflow execution
    fields:
      observation_id:
        type: string
        format: uuid-v7
        description: Unique observation identifier
      agent_name:
        type: string
        description: Agent that produced this observation
      target:
        type: string
        description: Entity or resource observed
      strategy_id:
        type: string
        optional: true
        description: Linked strategy (if applicable)
      measurements:
        type: object
        description: Key-value measurements from the observation
      findings:
        type: array
        items: string
        description: Notable findings
      status:
        type: string
        enum: [success, failed, partial]
        description: Observation outcome
      created_at:
        type: int64
        auto: true
        description: Observation timestamp

  Recommendation:
    description: Actionable recommendation from an observation
    fields:
      recommendation_id:
        type: string
        format: uuid-v7
        description: Unique recommendation identifier
      observation_id:
        type: string
        description: Source observation
      strategy_id:
        type: string
        optional: true
        description: Linked strategy
      priority:
        type: string
        enum: [critical, high, normal, low]
        description: Recommendation priority
      impact:
        type: string
        max: 256
        description: Expected impact if applied
      status:
        type: string
        enum: [pending, accepted, rejected, applied]
        description: Current decision state
      reason:
        type: string
        optional: true
        description: Rejection reason (if rejected)
      created_at:
        type: int64
        auto: true
        description: Creation timestamp

  Feedback:
    description: Post-application feedback on a recommendation
    fields:
      feedback_id:
        type: string
        format: uuid-v7
        description: Unique feedback identifier
      recommendation_id:
        type: string
        description: Source recommendation
      signal:
        type: string
        enum: [positive, negative, neutral]
        description: Feedback signal
      detail:
        type: string
        optional: true
        max: 512
        description: Additional context
      created_at:
        type: int64
        auto: true
        description: Feedback timestamp

  AgentMetrics:
    description: Running metrics for a participating agent
    fields:
      agent_name:
        type: string
        description: Agent identifier
      total_observations:
        type: int
        default: 0
        description: Total observations recorded
      total_findings:
        type: int
        default: 0
        description: Total findings across observations
      total_recommendations:
        type: int
        default: 0
        description: Total recommendations generated
      accuracy:
        type: float
        optional: true
        description: Recommendation acceptance rate
      last_active:
        type: int64
        description: Last workflow participation timestamp

  EntityContext:
    description: Hub-level entity context for targeting
    fields:
      entity_type:
        type: string
        description: Type of entity (e.g., website, service)
      entity_id:
        type: string
        description: Entity identifier (e.g., URL, service name)
      metadata:
        type: object
        description: Entity-specific metadata
      updated_at:
        type: int64
        auto: true
        description: Last update timestamp
```

## Identity

| Field | Value |
|-------|-------|
| Name | `lifecycle` |
| Type | `infrastructure` |
| Port | `9782` (advisory) |
| Namespace | `lifecycle.*` |

## Capabilities

```json
{
  "capabilities": [
    {"name": "task:execute", "resources": []},
    {"name": "agent:message", "resources": []},
    {"name": "event:observe", "resources": []}
  ]
}
```

`event:observe` is required because the Lifecycle Agent subscribes to
`workflow.completed` and `workflow.failed` with scope `"*"` — it needs
to observe ALL workflow results, not just ones addressed to it.

## Events

### Published (namespace: `lifecycle`)

| Topic | Scope | Payload | When |
|-------|-------|---------|------|
| `lifecycle.observation.recorded` | `*` | `{observation_id, agent, target}` | Observation stored |
| `lifecycle.recommendation.created` | `*` | `{recommendation_id, priority, target}` | New recommendation |
| `lifecycle.recommendation.accepted` | invoker | `{recommendation_id}` | Approved |
| `lifecycle.recommendation.rejected` | invoker | `{recommendation_id, reason}` | Rejected |
| `lifecycle.recommendation.applied` | invoker | `{recommendation_id}` | Change applied |
| `lifecycle.strategy.updated` | `*` | `{strategy_id, progress}` | Strategy progress changed |
| `lifecycle.feedback.recorded` | `*` | `{feedback_id, signal}` | Feedback captured |

### Subscribed

| Pattern | Scope | Group | Purpose |
|---------|-------|-------|---------|
| `workflow.completed` | `*` | `lifecycle` | Capture observations + recommendations |
| `workflow.failed` | `*` | `lifecycle` | Record failure observations |
| `system.agent.registered` | `self` | `lifecycle` | Track new agents for metrics |
| `system.agent.deregistered` | `self` | `lifecycle` | Update agent status |

## Manifest

```json
{
  "name": "lifecycle",
  "type": "infrastructure",
  "version": "2.0.0",
  "description": "Continuous optimization — strategies, observations, recommendations, approvals, feedback, agent metrics",
  "url": "http://localhost:9782",
  "public_key": "<hex>",
  "capabilities": [
    {"name": "task:execute", "resources": []},
    {"name": "agent:message", "resources": []},
    {"name": "event:observe", "resources": []}
  ],
  "publishes": ["lifecycle"],
  "subscriptions": [
    {"pattern": "workflow.completed", "scope": "*", "group": "lifecycle", "max_concurrent": 10},
    {"pattern": "workflow.failed", "scope": "*", "group": "lifecycle"},
    {"pattern": "system.agent.registered", "scope": "self"},
    {"pattern": "system.agent.deregistered", "scope": "self"}
  ]
}
```

## Core Logic

### HandleEvent: workflow.completed

```
1. Parse WorkflowResult from event payload

2. Extract observations:
   For each phase result that contains observations:
     Store observation in observation history
     Link to strategy_id (if present in workflow trigger)
     Publish: lifecycle.observation.recorded (scope: "*")

3. Extract recommendations:
   For each phase result that contains recommendations:
     Create Recommendation entry:
       status: "pending"
       observation_id: linked observation
       strategy_id: from workflow context
     Apply auto-approval rules:
       If source domain approval == "auto" AND priority != "critical":
         status → "accepted"
         Publish: lifecycle.recommendation.accepted (scope: invoker)
       Else:
         Publish: lifecycle.recommendation.created (scope: "*")
         Await human review

4. Update agent metrics:
   For each agent that participated:
     Increment total_observations
     Increment total_findings
     Increment total_recommendations

5. Update strategy progress:
   If strategy_id present:
     Query latest observations for strategy targets
     Recalculate target.progress
     If progress changed:
       Publish: lifecycle.strategy.updated (scope: "*")
     If progress >= 1.0:
       Set strategy status → "completed"
```

### HandleEvent: workflow.failed

```
1. Parse failure info from event payload
2. Record failure observation:
   { agent_name, target, status: "failed", error, timestamp }
3. Publish: lifecycle.observation.recorded (scope: "*")
4. Update agent metrics: increment failure count
```

### HandleMessage: create_strategy

```
Request: { name, objective, targets: [], priority, status }

1. Validate: name, objective, targets must be non-empty
2. Generate strategy ID
3. Store strategy in strategy store
4. Return stored strategy with ID

5. Optionally trigger initial workflow:
   Map strategy targets to domains (metric_name → domain)
   For each mapped domain:
     Publish: workflow.trigger (scope: "workflow")
       payload: { workflow: inferred_workflow, source_domain: domain,
                  strategy_id, ... }
```

### HandleMessage: approve_recommendation

```
Request: { recommendation_id, decision: "accept"|"reject", reason }

1. Look up recommendation by ID
2. If not found → error
3. If already decided → error (immutable decisions)

4. Update status:
   "accept" → "accepted"
   "reject" → "rejected" (store reason)

5. Publish:
   lifecycle.recommendation.accepted or .rejected (scope: invoker)

6. If accepted and recommendation belongs to a paused workflow:
   Publish: workflow.approval.decision (scope: "workflow")
     payload: { workflow_id, phase, decision: "accept" }
```

### HandleMessage: set_context

```
Request: EntityContext object

1. Validate structure
2. Store as the hub's entity context
3. Return stored context
```

### HandleMessage: get_context

```
1. Return current EntityContext
```

### Additional HandleMessage Actions

| Action | Purpose |
|--------|---------|
| `get_strategy` | Return a strategy by ID |
| `list_strategies` | List strategies (filterable by status, priority) |
| `get_observations` | Query observation history (by agent, target, strategy, time range) |
| `get_recommendations` | Query recommendations (by status, priority, agent) |
| `get_feedback` | Query feedback entries |
| `get_agent_metrics` | Return AgentMetrics for a specific agent or all agents |
| `record_feedback` | Manually record feedback for a recommendation |

---

## State Machine

```yaml
state_machine:
  agent:
    initial: created
    transitions:
      - from: created
        to: registered
        trigger: orchestrator_ack
        validates: agent_id assigned in response
      - from: registered
        to: active
        trigger: subscriptions_established
        validates: workflow.completed and workflow.failed subscriptions active
      - from: active
        to: degraded
        trigger: storage_error
        validates: retry count < max per patterns/retry
      - from: degraded
        to: active
        trigger: storage_recovered
        validates: storage write succeeds
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: signal received (SIGTERM, system.shutdown, or API)
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in-flight event processing = 0 OR drain timeout (30s) elapsed

  entity.Strategy:
    initial: active
    transitions:
      - from: active
        to: paused
        trigger: operator_pause
        validates: strategy exists
      - from: paused
        to: active
        trigger: operator_resume
        validates: strategy exists
      - from: active
        to: completed
        trigger: all_targets_met
        validates: all target.progress >= 1.0
      - from: active
        to: abandoned
        trigger: operator_abandon
        validates: reason provided
      - from: paused
        to: abandoned
        trigger: operator_abandon
        validates: reason provided

  entity.Recommendation:
    initial: pending
    transitions:
      - from: pending
        to: accepted
        trigger: approval_decision
        validates: decision = accept
      - from: pending
        to: rejected
        trigger: approval_decision
        validates: decision = reject, reason provided
      - from: pending
        to: accepted
        trigger: auto_approval
        validates: domain approval = auto AND priority != critical
      - from: accepted
        to: applied
        trigger: workflow_applied
        validates: downstream workflow confirms application
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults
  Validates:   All config values within declared constraints
  On Fail:     EXIT with CONFIG_INVALID

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/lifecycle/
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Open flat-file JSONL storage directory
  Validates:   Directory writable, existing files parseable
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE

Step 4 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 5 — Subscribe to Events
  Action:      Subscribe to: workflow.completed (scope: "*"),
               workflow.failed (scope: "*"),
               system.agent.registered, system.agent.deregistered,
               system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT with SUBSCRIPTION_FAILED

Step 6 — Load Active Strategies
  Action:      Read strategies.jsonl for active strategies
  Validates:   All records parse as Strategy type
  On Fail:     Enter degraded state, log warning

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9782, strategies_loaded: N}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Events
  Action:      Unsubscribe from all event topics

Step 3 — Drain In-Flight
  Action:      Wait for processing events to complete (up to 30s)
  On Timeout:  Log incomplete processing, persist partial state

Step 4 — Flush Storage
  Action:      Ensure all in-memory state persisted to JSONL files
  Validates:   All pending writes flushed

Step 5 — Deregister
  Action:      DELETE /v1/register

Step 6 — Exit
  Log: lifecycle.stopped {uptime_seconds, observations_processed}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - event subscriptions active (workflow.completed, workflow.failed)
      - storage writable
    response:
      status: healthy
      details: {subscriptions, storage, active_strategies, pending_recommendations}

  degraded:
    conditions:
      - storage errors (retrying)
      - event subscription partially lost
    response:
      status: degraded
      details: {reason, last_error, retry_count}

  unhealthy:
    conditions:
      - storage unreachable after retry exhaustion
      - all event subscriptions lost
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "lifecycle"`:

```
1. Parse new blueprint, verify against schema
2. Validate active strategies against updated types
3. Apply new configuration values
4. Log: lifecycle.version_updated {from, to}
```

---

## Triggers

```yaml
triggers:
  - name: workflow_completed
    type: event
    topic: workflow.completed
    scope: "*"
    description: Capture observations and recommendations from any workflow

  - name: workflow_failed
    type: event
    topic: workflow.failed
    scope: "*"
    description: Record failure observations from any workflow

  - name: agent_registered
    type: event
    topic: system.agent.registered
    description: Track new agents for metrics

  - name: agent_deregistered
    type: event
    topic: system.agent.deregistered
    description: Update agent status in metrics

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "lifecycle"
    description: Self-update if lifecycle blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [create_strategy, approve_recommendation, set_context,
             get_context, get_strategy, list_strategies, get_observations,
             get_recommendations, get_feedback, get_agent_metrics,
             record_feedback]
    description: Agent-to-agent and operator actions
```

---

## Actions

### create_strategy

**Purpose:** Create a new optimization strategy with measurable targets.

**Input:** `{name, objective, targets: [StrategyTarget], priority, status?}`

**Processing:**

```
1. Validate: name, objective, targets must be non-empty
2. Generate strategy_id (UUID v7)
3. Store strategy in strategies.jsonl
4. Map strategy targets to domains (metric_name → domain)
5. For each mapped domain:
   Publish: workflow.trigger (scope: "workflow")
     payload: {workflow: inferred_workflow, source_domain: domain, strategy_id}
6. Return stored strategy with ID
```

**Output:** `Strategy`

**Errors:** `INVALID_INPUT` (permanent), `STORAGE_ERROR` (transient)

---

### approve_recommendation

**Purpose:** Accept or reject a pending recommendation.

**Input:** `{recommendation_id, decision: "accept"|"reject", reason?}`

**Processing:**

```
1. Look up recommendation by ID
2. If not found → NOT_FOUND
3. If already decided → INVALID_STATE (immutable decisions)
4. Update status: accept → accepted, reject → rejected
5. Publish: lifecycle.recommendation.accepted or .rejected
6. If accepted and belongs to paused workflow:
   Publish: workflow.approval.decision (scope: "workflow")
```

**Output:** Updated `Recommendation`

**Errors:** `NOT_FOUND` (permanent), `INVALID_STATE` (permanent)

---

### set_context / get_context

**Purpose:** Store or retrieve the hub's entity context.

**Input (set):** `EntityContext` object
**Input (get):** `{}`

**Processing:** Validate structure, store/retrieve from entity_context.json.

**Output:** `EntityContext`

---

## Execute Workflow

The lifecycle agent operates reactively on workflow completion events:

```
Phase 1 — Event Reception
  Trigger:   workflow.completed or workflow.failed event received
  Action:    Parse WorkflowResult from event payload
  Validate:  Required fields present

Phase 2 — Extract Observations
  For each phase result containing observations:
    a. Create Observation record
    b. Link to strategy_id (if present in workflow trigger)
    c. Store in observations.jsonl
    d. Publish: lifecycle.observation.recorded (scope: "*")

Phase 3 — Extract Recommendations
  For each phase result containing recommendations:
    a. Create Recommendation record (status: pending)
    b. Apply auto-approval rules:
       If domain approval == "auto" AND priority != "critical":
         status → accepted
         Publish: lifecycle.recommendation.accepted
       Else:
         Publish: lifecycle.recommendation.created (scope: "*")
         Await human review

Phase 4 — Update Agent Metrics
  For each participating agent:
    Increment total_observations, total_findings, total_recommendations
    Update last_active timestamp
    Recalculate accuracy

Phase 5 — Update Strategy Progress
  If strategy_id present in workflow context:
    Query latest observations for strategy targets
    Recalculate target.progress for each target
    If progress changed:
      Publish: lifecycle.strategy.updated (scope: "*")
    If all targets progress >= 1.0:
      Strategy state → completed

Phase 6 — Persist
  Flush all updated records to storage
  Emit metrics
```

## Storage

All data stored in flat-file JSONL:

```
.weblisk/data/lifecycle/
  strategies.jsonl          # Strategy records
  observations.jsonl        # Observation history
  recommendations.jsonl     # Recommendation records
  feedback.jsonl            # Feedback entries
  agent_metrics.jsonl       # Running agent metrics
  entity_context.json       # Current entity context (single file)
```

Retention defaults:
- Observations: 90 days
- Recommendations: 90 days
- Feedback: 180 days
- Strategies: indefinite
- Agent metrics: indefinite (running aggregates)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_LIFECYCLE_PORT` | `9782` | Listen port |
| `WL_LIFECYCLE_MAX_CONCURRENT` | `20` | Max concurrent event processing |
| `WL_LIFECYCLE_DATA_DIR` | `.weblisk/data/lifecycle` | Storage directory |
| `WL_LIFECYCLE_OBS_RETENTION` | `7776000` | Observation retention (seconds, 90d) |
| `WL_LIFECYCLE_REC_RETENTION` | `7776000` | Recommendation retention (seconds, 90d) |
| `WL_LIFECYCLE_FB_RETENTION` | `15552000` | Feedback retention (seconds, 180d) |

---

## Collaboration

```yaml
events_published:
  - topic: lifecycle.observation.recorded
    payload: {observation_id, agent, target}
    scope: "*"
    when: Observation stored from workflow result

  - topic: lifecycle.recommendation.created
    payload: {recommendation_id, priority, target}
    scope: "*"
    when: New recommendation pending human review

  - topic: lifecycle.recommendation.accepted
    payload: {recommendation_id}
    scope: invoker
    when: Recommendation approved (auto or manual)

  - topic: lifecycle.recommendation.rejected
    payload: {recommendation_id, reason}
    scope: invoker
    when: Recommendation rejected

  - topic: lifecycle.recommendation.applied
    payload: {recommendation_id}
    scope: invoker
    when: Downstream workflow confirms application

  - topic: lifecycle.strategy.updated
    payload: {strategy_id, progress}
    scope: "*"
    when: Strategy progress changed

  - topic: lifecycle.feedback.recorded
    payload: {feedback_id, signal}
    scope: "*"
    when: Feedback captured

events_subscribed:
  - topic: workflow.completed
    scope: "*"
    action: Extract observations, recommendations, update metrics

  - topic: workflow.failed
    scope: "*"
    action: Record failure observations, update metrics

  - topic: system.agent.registered
    action: Initialize agent metrics entry

  - topic: system.agent.deregistered
    action: Mark agent inactive in metrics

  - topic: system.shutdown
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    filter: blueprint_name = "lifecycle"
    action: Self-update procedure

direct_messages:
  - target: workflow (via event bus)
    action: workflow.trigger
    when: Strategy decomposition triggers domain workflows
    reason: Lifecycle initiates workflows to gather observations

  - target: workflow (via event bus)
    action: workflow.approval.decision
    when: Accepted recommendation belongs to paused workflow
    reason: Unblock waiting approval gates
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     Auto-approval for all non-critical recommendations
  supervised:    Auto-approval for auto-flagged domains; human review for others
  manual-only:   All recommendations require human approval

overridable_behaviors:
  - behavior: auto_approval
    default: enabled (for domains with approval = "auto")
    override: Set WL_LIFECYCLE_AUTO_APPROVE=false
    audit: logged

  - behavior: strategy_workflow_trigger
    default: enabled
    override: Set WL_LIFECYCLE_AUTO_TRIGGER=false
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: create_strategy
    description: Create optimization strategy
    allowed: operator

  - action: approve_recommendation
    description: Accept or reject pending recommendation
    allowed: operator

  - action: abandon_strategy
    description: Mark strategy as abandoned
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Operator identity from auth token
  why: Required — operator must provide reason
  storage: Appended to system audit log
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT modify observations or recommendations after creation
      (append-only data model)
    - MUST NOT trigger workflows targeting agents not in the service directory
    - Strategy progress updates bounded by workflow completion rate

  forbidden_actions:
    - MUST NOT apply recommendations directly — only approve/reject
    - MUST NOT auto-approve critical-priority recommendations
    - MUST NOT delete strategies — only transition to completed/abandoned

  resource_limits:
    memory: 256 MB (process limit)
    max_active_strategies: 1000
    max_pending_recommendations: 10000
    observations_storage: governed by config.WL_LIFECYCLE_OBS_RETENTION
    recommendations_storage: governed by config.WL_LIFECYCLE_REC_RETENTION
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_INPUT
      description: Missing required fields or constraint violation
    - code: NOT_FOUND
      description: Referenced strategy, recommendation, or agent not found
    - code: INVALID_STATE
      description: Action not valid for current entity state
      example: Approving an already-decided recommendation

  transient:
    - code: STORAGE_ERROR
      description: Storage read/write failure
      fallback: Enter degraded state, buffer in memory, retry on next event
    - code: WORKFLOW_TRIGGER_FAILED
      description: Failed to publish workflow.trigger event
      fallback: Retry 3x with exponential backoff, log warning
    - code: EVENT_DELIVERY_FAILED
      description: Published event not acknowledged by bus
      fallback: Retry with backoff, log warning, continue processing
```

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| `lifecycle_observations_total` | counter | Observations recorded by agent |
| `lifecycle_recommendations_total` | counter | Recommendations by status and priority |
| `lifecycle_approvals_total` | counter | Approval decisions by outcome |
| `lifecycle_feedback_total` | counter | Feedback entries by signal type |
| `lifecycle_strategy_progress` | gauge | Current progress per strategy |
| `lifecycle_agent_accuracy` | gauge | Per-agent recommendation accuracy |

---

## Security

```yaml
security:
  permissions:
    - capability: event:observe
      resources: ["*"]
      description: Observe workflow.completed/failed from all agents

    - capability: agent:message
      resources: ["*"]
      description: Trigger workflows via event bus

    - capability: storage:read
      resources: [strategies, observations, recommendations, feedback, agent_metrics, entity_context]
      description: Read own data stores

    - capability: storage:write
      resources: [strategies, observations, recommendations, feedback, agent_metrics, entity_context]
      description: Write own data stores

  data_sensitivity:
    - data: Observations
      classification: medium
      handling: May contain site performance data and findings

    - data: Recommendations
      classification: medium
      handling: Contain actionable suggestions with priority levels

    - data: Strategies
      classification: low
      handling: Optimization objectives are not sensitive

    - data: Entity context
      classification: medium
      handling: Contains site metadata and configuration

  access_control:
    - caller: Any registered agent
      actions: [get_strategy, list_strategies, get_observations,
                get_recommendations, get_feedback, get_agent_metrics, get_context]
      note: Read-only access to lifecycle data

    - caller: Operator (auth token with operator role)
      actions: [create_strategy, approve_recommendation, set_context,
                record_feedback, abandon_strategy]
      note: Full management access

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Workflow result creates observations and recommendations
    trigger: workflow.completed
    input:
      phase_results:
        - agent: seo-analyzer
          observations: [{metric: page_speed, value: 2.1}]
          recommendations: [{action: optimize_images, priority: normal}]
    expected:
      Observation created and stored
      Recommendation created with status: pending
    validates:
      - lifecycle.observation.recorded event published
      - lifecycle.recommendation.created event published

  - name: Auto-approval for auto domain
    trigger: workflow.completed
    precondition: Domain approval config = "auto", priority = normal
    expected:
      Recommendation status: accepted (auto-approved)
    validates:
      - lifecycle.recommendation.accepted event published
      - No human review required

  - name: Strategy progress updates
    action: create_strategy
    input: {name: "Improve SEO", targets: [{metric: score, target_value: 90}]}
    then: workflow.completed with observation showing score = 85
    expected:
      Strategy target progress updated
    validates:
      - lifecycle.strategy.updated event published
```

### Error Cases

```yaml
  - name: Approve already-decided recommendation
    action: approve_recommendation
    input: {recommendation_id: already_accepted, decision: reject}
    expected_error: INVALID_STATE

  - name: Create strategy with empty targets
    action: create_strategy
    input: {name: "No targets", objective: "test", targets: []}
    expected_error: INVALID_INPUT

  - name: Workflow result during storage outage
    trigger: workflow.completed while storage unreachable
    expected:
      Agent enters degraded state
      Data buffered in memory
      Persisted when storage recovers
```

### Edge Cases

```yaml
  - name: Critical recommendation never auto-approved
    trigger: workflow.completed with priority: critical recommendation
    precondition: Domain approval = "auto"
    expected:
      Recommendation status remains pending (not auto-approved)
    validates:
      - Auto-approval rule excludes critical priority

  - name: Strategy completes when all targets met
    precondition: Strategy with 3 targets, 2 already at progress 1.0
    trigger: workflow.completed showing third target at target_value
    expected:
      Strategy state → completed
    validates:
      - All targets checked, strategy status updated
```

---

## Scaling

```yaml
scaling:
  model: horizontal
  min_instances: 1
  max_instances: 3

  inter_agent:
    protocol: message-bus-only
    direct_http: forbidden
    routing: by agent name, never by instance address

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: file lock with TTL
      leader: [event_processing, strategy_updates, metric_aggregation]
      follower: [health_reporting, action_handling, read_queries]
      promotion: automatic when leader lock expires
    state_sharing:
      mechanism: shared flat-file storage directory
      consistency_window: 5 seconds
      conflict_resolution: >
        Observation and recommendation IDs are globally unique (UUID v7).
        Leader election prevents duplicate processing of the same
        workflow.completed event.

  event_handling:
    consumer_group: lifecycle
    delivery: one-per-group
    description: >
      Bus delivers each workflow.completed event to ONE instance in
      the "lifecycle" consumer group. Prevents duplicate observation
      and recommendation extraction.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 5
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same storage directory. Schema changes
      are additive-only during shadow phase.
    consumer_groups:
      shadow_phase: "lifecycle@vN+1"
      after_cutover: "lifecycle"
```

---

## Implementation Notes

- **Global scope subscription**: The lifecycle agent uses `scope: "*"` for
  workflow.completed/failed. This requires the `event:observe` capability.
  Without it, the agent would only see events addressed to itself.
- **Append-only data model**: Observations, recommendations, and feedback
  are never modified after creation. Status changes on recommendations
  are the only mutation, and are tracked via the state machine.
- **Strategy decomposition**: Mapping metric names to domains requires
  knowledge of which domain owns which metrics. This mapping is derived
  from the service directory (agent manifests declare capabilities).
- **Accuracy calculation**: Agent accuracy = accepted recommendations /
  total recommendations. Updated after each approval decision.
- **Persistence**: All data MUST be persisted to JSONL storage. In-memory
  buffering is acceptable only during transient storage errors.
- **Retention**: Observation and recommendation cleanup runs on a
  background timer (every hour). Records older than retention TTL are
  deleted. Strategies are retained indefinitely.

---

## Verification Checklist

- [ ] Subscribes to workflow.completed (scope: "*") and extracts observations + recommendations
- [ ] Subscribes to workflow.failed (scope: "*") and records failure observations
- [ ] Strategies created via create_strategy message action
- [ ] Strategy decomposition maps targets to domains and publishes workflow.trigger
- [ ] Observations stored with measurements, findings, and strategy links
- [ ] Recommendations created with priority, impact, and pending status
- [ ] Auto-approval applied when domain approval is "auto" and priority != "critical"
- [ ] Human approval via approve_recommendation message action
- [ ] Accepted recommendations trigger workflow.approval.decision for paused workflows
- [ ] Agent metrics updated after every workflow completion
- [ ] Strategy progress recalculated from latest observations
- [ ] Entity context stored and retrievable via set_context/get_context
- [ ] All data persisted to flat-file JSONL storage
- [ ] Lifecycle events published for every state transition
- [ ] Dependencies declare version ranges and specific bindings
- [ ] on_change rules defined for all dependencies
- [ ] State machine transitions validated — no implicit states
- [ ] Startup sequence validation gates — each step has validates/on-fail
- [ ] Shutdown drains in-flight events before exit
- [ ] Health endpoint reports accurate status per health criteria
- [ ] Scaling: inter-agent communication via message bus only
- [ ] Scaling: leader election prevents duplicate event processing
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Override audit records who, what, when, why
- [ ] Constraints enforced — append-only data, no auto-approve critical
- [ ] Security: all endpoints require valid token
- [ ] Retention cleanup runs for observations and recommendations
