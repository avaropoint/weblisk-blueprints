<!-- blueprint
type: agent
kind: infrastructure
name: workflow
version: 1.0.0
extends: [patterns/workflow, patterns/scope, patterns/policy, patterns/safety]
requires: [protocol/spec, protocol/types, architecture/agent, patterns/messaging]
platform: any
tier: free
port: 9780
-->

# Workflow Agent

Infrastructure agent that owns the workflow execution engine. Receives
`workflow.trigger` events, resolves DAG definitions from source
domains, dispatches phases via `task.submit` events, tracks execution
state, and publishes `workflow.completed` back to the invoker.

The Workflow Agent knows HOW to execute workflows — the domains define
WHAT workflows exist and WHY they run.

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
        - name: TaskRequest
          fields_used: [id, from, target_agent, action, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
        - name: WorkflowResult
          fields_used: [workflow_name, invoker, status, phase_results, observations, recommendations]
        - name: MessageEnvelope
          fields_used: [from, to, action, payload, trace_id]
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

  - blueprint: patterns/workflow
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: dag-resolution
          parameters: [phases, depends_on, topological_sort]
        - behavior: approval-gate
          parameters: [phase, approval, required_approvers]
        - behavior: on-error-strategy
          parameters: [fail, skip, retry]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

depends_on: [task]
  # Runtime dependency on the task agent. The workflow agent dispatches
  # phases via task.submit events. If task agent is unavailable,
  # workflow execution stalls (phases cannot be dispatched).
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  WorkflowExecution:
    description: Record of a single workflow execution
    fields:
      execution_id:
        type: string
        format: uuid-v7
        description: Unique execution identifier
      workflow_name:
        type: string
        description: Name of the workflow being executed
      invoker:
        type: string
        description: Agent or domain that triggered the workflow
      status:
        type: string
        enum: [running, completed, failed, cancelled, pending_approval]
        description: Current execution state
      correlation_id:
        type: string
        description: Correlation context from trigger
      trace_id:
        type: string
        description: Trace context for distributed tracing
      phase_results:
        type: array
        items: PhaseResult
        description: Results from each phase
      started_at:
        type: int64
        auto: true
        description: Execution start timestamp
      completed_at:
        type: int64
        optional: true
        description: Execution completion timestamp
      error:
        type: string
        optional: true
        description: Error message if failed
      callback_topic:
        type: string
        optional: true
        description: Topic to publish result to on completion
    constraints:
      - name: uq_execution_id
        type: unique
        fields: [execution_id]

  PhaseResult:
    description: Result of a single workflow phase
    fields:
      phase_name:
        type: string
        description: Phase identifier
      agent_name:
        type: string
        description: Agent that executed this phase
      status:
        type: string
        enum: [completed, failed, skipped, pending_approval]
        description: Phase outcome
      output:
        type: object
        optional: true
        description: Phase output data
      observations:
        type: array
        optional: true
        description: Observations extracted from phase
      recommendations:
        type: array
        optional: true
        description: Recommendations extracted from phase
      started_at:
        type: int64
        description: Phase start timestamp
      completed_at:
        type: int64
        optional: true
        description: Phase completion timestamp
      error:
        type: string
        optional: true
        description: Error message if failed

  WorkflowDefinition:
    description: DAG definition fetched from source domain
    fields:
      name:
        type: string
        description: Workflow name
      description:
        type: string
        optional: true
        description: What this workflow does
      phases:
        type: array
        items: PhaseDefinition
        description: Ordered phase definitions

  PhaseDefinition:
    description: Single phase in a workflow DAG
    fields:
      name:
        type: string
        description: Phase identifier
      agent:
        type: string
        description: Target agent (or "self" for invoker domain)
      action:
        type: string
        description: Action to execute on target agent
      depends_on:
        type: array
        items: string
        default: []
        description: Phase names this phase depends on
      input:
        type: object
        optional: true
        description: Input with $-reference resolution
      timeout:
        type: int
        default: 300
        unit: seconds
        description: Phase timeout
      condition:
        type: string
        optional: true
        description: Expression that must be truthy to execute
      on_error:
        type: string
        enum: [fail, skip, retry]
        default: fail
        description: Error handling strategy
      max_retries:
        type: int
        default: 0
        description: Retries for "retry" on_error strategy
      approval:
        type: string
        enum: [none, required]
        default: none
        description: Whether phase output requires approval
```

## Identity

| Field | Value |
|-------|-------|
| Name | `workflow` |
| Type | `infrastructure` |
| Port | `9780` (advisory) |
| Namespace | `workflow.*` |

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

`event:observe` is required to receive `task.complete` events scoped
to any workflow execution (not just self-initiated ones).

## Events

### Published (namespace: `workflow`)

| Topic | Scope | Payload | When |
|-------|-------|---------|------|
| `workflow.started` | invoker | `{workflow, execution_id}` | Execution begins |
| `workflow.phase.ready` | `task` | `{task_id, phase, agent, action, input}` | Phase dispatched |
| `workflow.phase.complete` | invoker | `{phase, status, output}` | Phase finished |
| `workflow.phase.failed` | invoker | `{phase, error}` | Phase errored |
| `workflow.phase.skipped` | invoker | `{phase, reason}` | Phase skipped |
| `workflow.approval.required` | invoker | `{phase, output_preview, workflow_id}` | Approval gate |
| `workflow.completed` | invoker | `WorkflowResult` | All phases done |
| `workflow.failed` | invoker | `{workflow, error, partial_results}` | Workflow errored |

### Subscribed

| Pattern | Scope | Group | Purpose |
|---------|-------|-------|---------|
| `workflow.trigger` | `self` | `workflow` | Receive workflow requests |
| `workflow.approval.decision` | `self` | `workflow` | Receive approval decisions |
| `task.complete` | `self` | `workflow` | Phase completion tracking |
| `task.failed` | `self` | `workflow` | Phase failure tracking |
| `system.agent.registered` | `self` | `workflow` | Cache invalidation |

## Manifest

```json
{
  "name": "workflow",
  "type": "infrastructure",
  "version": "2.0.0",
  "description": "Workflow execution engine — DAG resolution, phase coordination, approval gates",
  "url": "http://localhost:9780",
  "public_key": "<hex>",
  "capabilities": [
    {"name": "task:execute", "resources": []},
    {"name": "agent:message", "resources": []},
    {"name": "event:observe", "resources": []}
  ],
  "publishes": ["workflow"],
  "subscriptions": [
    {"pattern": "workflow.trigger", "scope": "self", "group": "workflow", "max_concurrent": 10},
    {"pattern": "workflow.approval.decision", "scope": "self", "group": "workflow"},
    {"pattern": "task.complete", "scope": "self", "group": "workflow", "max_concurrent": 20},
    {"pattern": "task.failed", "scope": "self", "group": "workflow"},
    {"pattern": "system.agent.registered", "scope": "self"}
  ]
}
```

## Core Logic

### HandleEvent: workflow.trigger

```
1. Parse trigger payload:
   { workflow, source_domain, input, callback_topic, entity, config }

2. Fetch workflow definition from source_domain:
   POST /v1/message to source_domain:
     action: "get_workflow"
     payload: { name: workflow }
   → Response: WorkflowDefinition
   Cache definition (invalidate on system.agent.registered for domain)

3. Create WorkflowExecution:
   id: UUID v7
   workflow_name: workflow
   invoker: source_domain
   correlation_id: from trigger event
   trace_id: from trigger event
   status: "running"
   started_at: now()

4. Publish: workflow.started (scope: invoker)

5. Resolve DAG:
   Topological sort by depends_on
   Group into execution levels
   Detect cycles → fail with "circular dependency"

6. Dispatch Level 0 phases → see Phase Dispatch below

7. Store execution record (flat-file JSONL)
```

### Phase Dispatch

For each phase ready to execute:

```
If phase.condition is set and evaluates to falsy:
  Mark phase "skipped"
  Publish: workflow.phase.skipped (scope: invoker)
  Return

Resolve input references:
  $task.payload.* → from trigger input
  $phases.<name>.output → from completed phase results
  $entity.* → from trigger entity context
  $config.* → from trigger config

If phase.agent == "self":
  POST /v1/message to invoker domain:
    action: phase.action
    payload: resolved_input
  Store result as phase output
  Advance DAG
Else:
  Generate task_id
  Publish: task.submit (scope: "task")
    payload: {
      task_id, workflow_id, phase: phase.name,
      target_agent: phase.agent, action: phase.action,
      input: resolved_input, timeout: phase.timeout,
      trace_id, correlation_id
    }
  Track: in_flight[workflow_id][phase.name] = task_id
```

### HandleEvent: task.complete

```
1. Extract workflow_id and phase from payload
2. Look up in-flight execution
3. Store PhaseResult: { phase_name, agent_name, status, output,
   started_at, completed_at }
4. Publish: workflow.phase.complete (scope: invoker)

5. Check approval gate:
   If phase.approval == "required":
     Store output (not exposed to downstream yet)
     Set status → "pending_approval"
     Publish: workflow.approval.required (scope: invoker)
     Return (wait for approval decision)

6. Check level completion:
   Are all phases in current level done?
   If no → wait for remaining
   If yes → advance to next level:
     Resolve input references for next-level phases
     Dispatch next-level phases

7. Check workflow completion:
   All levels done?
   If yes → aggregate results → Phase Complete below
```

### HandleEvent: task.failed

```
1. Extract workflow_id and phase from payload
2. Look up execution, get phase definition

3. Apply on_error strategy:
   "fail":
     Cancel all in-flight tasks (publish task.cancel)
     Skip all remaining phases
     Set workflow status → "failed"
     Publish: workflow.failed (scope: invoker)
   "skip":
     Mark phase "skipped"
     Publish: workflow.phase.skipped (scope: invoker)
     Downstream phases referencing this output → receive null
     Continue execution
   "retry":
     If retries < max_retries:
       Increment retry count
       Wait: base_delay × 2^retry (1s, 2s, 4s)
       Re-dispatch via task.submit
     Else:
       Treat as "fail"
```

### HandleEvent: workflow.approval.decision

```
1. Extract workflow_id, phase, decision, reason
2. Look up execution

3. If decision == "accept":
     Expose phase output to downstream references
     Set status → "running"
     Advance DAG to next level
4. If decision == "reject":
     Apply on_error strategy for the phase
```

### Workflow Completion

```
1. Collect all phase results
2. Build WorkflowResult:
   workflow_name, invoker, status, summary,
   phase_results, merged observations, merged recommendations,
   metrics: { phases_total, completed, failed, skipped, duration_ms }

3. Publish: workflow.completed (scope: invoker)
   payload: WorkflowResult

4. If callback_topic set:
   Publish result to callback_topic (scope: invoker)

5. Persist final WorkflowExecution record
```

## HandleMessage Actions

| Action | Purpose |
|--------|---------|
| `get_execution` | Return a specific WorkflowExecution by ID |
| `list_executions` | List recent executions (filterable by workflow, status, invoker) |
| `cancel_execution` | Cancel an in-flight workflow execution |

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
        validates: workflow.trigger subscription active
      - from: active
        to: degraded
        trigger: storage_error
        validates: retry count < max
      - from: degraded
        to: active
        trigger: storage_recovered
        validates: storage write succeeds
      - from: active
        to: degraded
        trigger: task_agent_unavailable
        validates: task.submit events not being processed
      - from: degraded
        to: active
        trigger: task_agent_restored
        validates: task.submit events flowing again
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
        validates: in_flight_workflows = 0 OR drain timeout (60s) elapsed

  entity.WorkflowExecution:
    initial: running
    transitions:
      - from: running
        to: completed
        trigger: all_phases_done
        validates: all phases completed or skipped
      - from: running
        to: failed
        trigger: phase_failed_with_fail_strategy
        validates: on_error = fail and retries exhausted
      - from: running
        to: pending_approval
        trigger: approval_gate_reached
        validates: phase.approval = required
      - from: pending_approval
        to: running
        trigger: approval_accepted
        validates: workflow.approval.decision with decision = accept
      - from: pending_approval
        to: failed
        trigger: approval_rejected
        validates: workflow.approval.decision with decision = reject
      - from: running
        to: cancelled
        trigger: cancel_requested
        validates: cancel_execution action received
      - from: pending_approval
        to: cancelled
        trigger: cancel_requested
        validates: cancel_execution action received
      - from: running
        to: failed
        trigger: workflow_timeout
        validates: execution duration > config.workflow_timeout
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/workflow/
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Open flat-file JSONL storage directory
  Validates:   Directory writable, existing execution records parseable
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE

Step 4 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 5 — Subscribe to Events
  Action:      Subscribe to: workflow.trigger, workflow.approval.decision,
               task.complete, task.failed, system.agent.registered,
               system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT with SUBSCRIPTION_FAILED

Step 6 — Recover In-Flight Executions
  Action:      Read executions.jsonl for running/pending_approval workflows
  Validates:   Records parse as WorkflowExecution type
  On Fail:     Enter degraded state, log warning
  Note:        Running executions are resumed from last completed phase.
               Pending approval executions wait for approval events.

Step 7 — Initialize Definition Cache
  Action:      Clear in-memory workflow definition cache
  Note:        Definitions fetched on-demand from source domains

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9780, in_flight_recovered: N}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Workflows
  Action:      Unsubscribe from workflow.trigger, return 503 for new triggers

Step 3 — Cancel In-Flight Phases
  Action:      Publish task.cancel for all dispatched phases
  Wait:        Up to 60s for task.complete/failed events
  On Timeout:  Mark remaining phases as failed

Step 4 — Fail Active Workflows
  Action:      For each running workflow:
               Set status → failed (reason: agent_shutdown)
               Publish: workflow.failed (scope: invoker)

Step 5 — Persist State
  Action:      Flush all execution records to storage

Step 6 — Deregister
  Action:      DELETE /v1/register

Step 7 — Exit
  Log: lifecycle.stopped {uptime_seconds, workflows_drained, workflows_failed}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - workflow.trigger subscription active
      - task.complete/failed subscriptions active
      - storage writable
      - in_flight < 80% of config.max_concurrent
    response:
      status: healthy
      details: {in_flight, max_concurrent, cached_definitions, storage}

  degraded:
    conditions:
      - storage errors (retrying)
      - task agent unavailable (phases cannot dispatch)
      - in_flight >= 80% of max_concurrent
    response:
      status: degraded
      details: {reason, in_flight, last_error}

  unhealthy:
    conditions:
      - storage unreachable after retry exhaustion
      - workflow.trigger subscription lost
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "workflow"`:

```
1. Parse new blueprint, verify against schema
2. Validate in-flight executions against updated types
3. Clear definition cache (will re-fetch from domains)
4. Apply new configuration values
5. Log: lifecycle.version_updated {from, to}
```

---

## Triggers

```yaml
triggers:
  - name: workflow_trigger
    type: event
    topic: workflow.trigger
    description: Receive workflow execution request

  - name: approval_decision
    type: event
    topic: workflow.approval.decision
    description: Receive approval/rejection for gated phase

  - name: task_complete
    type: event
    topic: task.complete
    description: Phase completed successfully

  - name: task_failed
    type: event
    topic: task.failed
    description: Phase failed

  - name: agent_registered
    type: event
    topic: system.agent.registered
    description: Invalidate definition cache for re-registered domains

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "workflow"
    description: Self-update if workflow blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [get_execution, list_executions, cancel_execution]
    description: Agent-to-agent and operator query actions
```

---

## Actions

### trigger (internal — triggered by workflow.trigger event)

**Purpose:** Start a new workflow execution from a DAG definition.

**Input:** `workflow.trigger` event payload:
`{workflow, source_domain, input, callback_topic, entity, config}`

**Processing:**

```
1. Fetch WorkflowDefinition from source_domain:
   POST /v1/message to source_domain: action = get_workflow
   Cache definition (invalidate on system.agent.registered)
2. Create WorkflowExecution record (status: running)
3. Topological sort phases by depends_on
   Detect cycles → fail with "circular dependency"
4. Group into execution levels
5. Publish: workflow.started (scope: invoker)
6. Dispatch Level 0 phases via task.submit events
7. Persist execution record
```

**Output:** Events: `workflow.started`, then per-phase events, then `workflow.completed` or `workflow.failed`

**Errors:** `DEFINITION_FETCH_FAILED` (transient), `CIRCULAR_DEPENDENCY` (permanent)

---

### get_execution

**Purpose:** Return a specific WorkflowExecution by ID.

**Input:** `{execution_id: string}`

**Output:** `WorkflowExecution`

**Errors:** `NOT_FOUND` (permanent)

---

### cancel_execution

**Purpose:** Cancel an in-flight workflow execution.

**Input:** `{execution_id: string, reason?: string}`

**Processing:**

```
1. Look up execution
2. Publish task.cancel for all dispatched phases
3. Skip remaining undispatched phases
4. Set status → cancelled
5. Publish: workflow.failed (scope: invoker) with reason
```

**Output:** Updated `WorkflowExecution`

---

## Execute Workflow

The workflow agent operates reactively on workflow.trigger events.
Core processing loop (also described in Core Logic above):

```
Phase 1 — Trigger Reception
  Trigger:   workflow.trigger event received
  Action:    Parse trigger payload
  Validate:  workflow name, source_domain present

Phase 2 — Definition Fetch
  Action:    Check cache for WorkflowDefinition
  If miss:   POST /v1/message to source_domain (action: get_workflow)
  Cache:     Store definition, invalidate on domain re-registration
  On Fail:   Retry 3x → publish workflow.failed

Phase 3 — DAG Resolution
  Action:    Topological sort by depends_on
  Group:     Phases with same dependency depth into execution levels
  Detect:    Cycles → workflow.failed with "circular dependency"

Phase 4 — Level Dispatch
  For each phase in current level:
    a. Evaluate condition (if set) → skip if falsy
    b. Resolve input references ($task.payload.*, $phases.<name>.output, etc.)
    c. If phase.agent == "self" → POST /v1/message to invoker domain
    d. Else → publish task.submit (scope: "task")
  Wait for task.complete/task.failed events for all phases in level

Phase 5 — Result Processing (per phase)
  On task.complete:
    Store PhaseResult
    If approval = required → pause, publish workflow.approval.required
    If level complete → advance to next level (back to Phase 4)
  On task.failed:
    Apply on_error strategy: fail / skip / retry

Phase 6 — Completion
  All levels done:
    Aggregate PhaseResults into WorkflowResult
    Publish: workflow.completed (scope: invoker)
    If callback_topic → publish to callback_topic
    Persist final WorkflowExecution record
```

## Storage

Workflow execution records are stored in flat-file JSONL:

```
.weblisk/data/workflow/executions.jsonl
```

Each line is a complete `WorkflowExecution` JSON object. The Workflow
Agent appends on state changes (started, phase complete, finished).

Definition cache (in-memory, invalidated on domain re-registration):

```
cache[domain_name][workflow_name] → WorkflowDefinition
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_WORKFLOW_PORT` | `9780` | Listen port |
| `WL_WORKFLOW_MAX_CONCURRENT` | `10` | Max concurrent workflow executions |
| `WL_WORKFLOW_TIMEOUT` | `600` | Default workflow timeout (seconds) |
| `WL_WORKFLOW_PHASE_TIMEOUT` | `300` | Default phase timeout (seconds) |
| `WL_WORKFLOW_DATA_DIR` | `.weblisk/data/workflow` | Storage directory |

---

## Collaboration

```yaml
events_published:
  - topic: workflow.started
    payload: {workflow, execution_id}
    scope: invoker
    when: Execution begins

  - topic: workflow.phase.ready
    payload: {task_id, phase, agent, action, input}
    scope: task
    when: Phase dispatched via task.submit

  - topic: workflow.phase.complete
    payload: {phase, status, output}
    scope: invoker
    when: Phase finished successfully

  - topic: workflow.phase.failed
    payload: {phase, error}
    scope: invoker
    when: Phase errored

  - topic: workflow.phase.skipped
    payload: {phase, reason}
    scope: invoker
    when: Phase condition evaluated to falsy

  - topic: workflow.approval.required
    payload: {phase, output_preview, workflow_id}
    scope: invoker
    when: Approval gate reached

  - topic: workflow.completed
    payload: WorkflowResult
    scope: invoker
    when: All phases done — consumed by lifecycle agent

  - topic: workflow.failed
    payload: {workflow, error, partial_results}
    scope: invoker
    when: Workflow errored — consumed by lifecycle agent

events_subscribed:
  - topic: workflow.trigger
    scope: self
    action: Start workflow execution from DAG definition

  - topic: workflow.approval.decision
    scope: self
    action: Process approval accept/reject for gated phase

  - topic: task.complete
    scope: self
    action: Track phase completion, advance DAG

  - topic: task.failed
    scope: self
    action: Track phase failure, apply on_error strategy

  - topic: system.agent.registered
    scope: self
    action: Invalidate definition cache for re-registered domains

  - topic: system.shutdown
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    filter: blueprint_name = "workflow"
    action: Self-update procedure

direct_messages:
  - target: variable (source_domain from workflow.trigger)
    action: get_workflow
    when: Fetching WorkflowDefinition from domain
    reason: Need synchronous response to resolve DAG before dispatch

  - target: task (via event bus)
    action: task.submit
    when: Phase dispatch
    reason: Task agent handles HTTP dispatch and tracking
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     Workflows execute and complete without intervention
  supervised:    Workflows execute; critical workflows require approval
  manual-only:   All workflows require manual trigger

overridable_behaviors:
  - behavior: automatic_execution
    default: enabled
    override: Set WL_WORKFLOW_PAUSED=true
    audit: logged

  - behavior: auto_advance_levels
    default: enabled
    override: Set WL_WORKFLOW_STEP_MODE=true (pause between levels)
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: cancel_execution
    description: Cancel an in-flight workflow
    allowed: operator

  - action: pause_all
    description: Pause all workflow execution (triggers queue)
    allowed: operator

  - action: resume_all
    description: Resume workflow execution
    allowed: operator

  - action: retry_execution
    description: Retry a failed workflow from the last failed phase
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
    - MUST NOT execute phases directly — always dispatches via task agent
    - MUST NOT modify domain workflow definitions
    - Workflow execution rate bounded by config.max_concurrent

  forbidden_actions:
    - MUST NOT bypass approval gates
    - MUST NOT re-order phases in violation of depends_on
    - MUST NOT execute phases with circular dependencies
    - MUST NOT dispatch to agents not in the service directory

  resource_limits:
    memory: 512 MB (process limit)
    max_concurrent_workflows: config.max_concurrent (default 10)
    max_phases_per_workflow: 50
    definition_cache_size: 100 entries
    execution_storage: indefinite (manual purge)
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: CIRCULAR_DEPENDENCY
      description: Workflow DAG contains cycles
    - code: NOT_FOUND
      description: Referenced execution_id does not exist
    - code: INVALID_DEFINITION
      description: WorkflowDefinition fails validation
    - code: PHASE_AGENT_NOT_FOUND
      description: Phase references an agent not in service directory

  transient:
    - code: DEFINITION_FETCH_FAILED
      description: Could not fetch workflow definition from source domain
      fallback: Retry 3x with exponential backoff, then fail workflow
    - code: TASK_DISPATCH_FAILED
      description: task.submit event not acknowledged
      fallback: Retry event publish, then fail phase
    - code: STORAGE_ERROR
      description: Storage read/write failure
      fallback: Continue execution in-memory, persist when recovered
    - code: APPROVAL_TIMEOUT
      description: No approval decision within timeout
      fallback: Apply on_error strategy for the gated phase
```

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| `workflow_execution_total` | counter | By workflow name and status |
| `workflow_execution_duration_seconds` | histogram | End-to-end duration |
| `workflow_phase_duration_seconds` | histogram | Per-phase by agent/action |
| `workflow_phase_total` | counter | Phase executions by status |
| `workflow_approval_wait_seconds` | histogram | Approval gate wait time |
| `workflow_inflight` | gauge | Currently executing workflows |

---

## Security

```yaml
security:
  permissions:
    - capability: event:observe
      resources: ["*"]
      description: Observe task.complete/failed for any workflow execution

    - capability: agent:message
      resources: ["*"]
      description: Fetch workflow definitions from any domain agent

    - capability: storage:read
      resources: [executions]
      description: Read own execution records

    - capability: storage:write
      resources: [executions]
      description: Write own execution records

  data_sensitivity:
    - data: Workflow definitions
      classification: medium
      handling: Cached in memory, contains domain logic structure

    - data: Phase inputs/outputs
      classification: variable
      handling: May contain domain data; logged as size only

    - data: Execution records
      classification: medium
      handling: Contains workflow results and phase outputs

    - data: Approval decisions
      classification: medium
      handling: Contains operator identity and decision rationale

  access_control:
    - caller: Any registered agent (via event bus)
      actions: [workflow.trigger]
      note: Any agent can trigger workflows

    - caller: lifecycle agent (via event bus)
      actions: [workflow.trigger, workflow.approval.decision]
      note: Lifecycle triggers strategy workflows and forwards approvals

    - caller: Any registered agent
      actions: [get_execution, list_executions]
      note: Read-only execution status

    - caller: Operator (auth token with operator role)
      actions: [get_execution, list_executions, cancel_execution,
                pause_all, resume_all, retry_execution]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Simple workflow executes all phases
    trigger: workflow.trigger
    input:
      workflow: site-health-check
      source_domain: health
      input: {url: "https://example.com"}
    precondition: Domain returns 3-phase DAG (no dependencies between phases)
    expected:
      All 3 phases dispatch concurrently via task.submit
      workflow.completed published with 3 PhaseResults
    validates:
      - WorkflowExecution created with status: running
      - Phases dispatched as Level 0 (no depends_on)
      - WorkflowResult includes merged observations/recommendations

  - name: DAG with dependencies dispatches in order
    trigger: workflow.trigger
    input: workflow with phases A (no deps), B (depends A), C (depends B)
    expected:
      Level 0: A dispatched
      Level 1: B dispatched after A completes
      Level 2: C dispatched after B completes
    validates:
      - Topological sort correct
      - Input references ($phases.A.output) resolved for B

  - name: Approval gate pauses execution
    trigger: workflow.trigger with phase having approval: required
    expected:
      Phase completes, execution pauses
      workflow.approval.required published
      After accept: execution resumes
    validates:
      - WorkflowExecution state: pending_approval
      - Downstream phases wait for approval
```

### Error Cases

```yaml
  - name: Circular dependency detected
    trigger: workflow.trigger
    precondition: DAG has cycle (A depends B, B depends A)
    expected:
      workflow.failed with error: CIRCULAR_DEPENDENCY
    validates:
      - Cycle detected before any dispatch

  - name: Phase fails with on_error = fail
    trigger: task.failed for a phase with on_error: fail
    expected:
      All in-flight phases cancelled
      workflow.failed published with partial_results
    validates:
      - task.cancel published for other in-flight phases

  - name: Phase fails with on_error = skip
    trigger: task.failed for a phase with on_error: skip
    expected:
      Phase marked as skipped
      Downstream phases receive null for skipped output
      Execution continues
    validates:
      - workflow.phase.skipped published

  - name: Definition fetch fails
    trigger: workflow.trigger, source domain unreachable
    expected:
      Retry 3x, then workflow.failed
    validates:
      - DEFINITION_FETCH_FAILED error after retries
```

### Edge Cases

```yaml
  - name: Approval rejected fails workflow
    trigger: workflow.approval.decision with decision = reject
    expected:
      on_error strategy applied for the gated phase
    validates:
      - If on_error = fail, workflow fails
      - If on_error = skip, phase skipped, execution continues

  - name: Workflow timeout cancels all phases
    precondition: config.workflow_timeout = 10, workflow takes 30s
    expected:
      After 10s: all in-flight phases cancelled
      workflow.failed with timeout reason
    validates:
      - task.cancel published for all dispatched phases

  - name: Domain re-registration invalidates definition cache
    trigger: system.agent.registered for a domain
    expected:
      Cached definition for that domain cleared
      Next workflow.trigger fetches fresh definition
    validates:
      - Stale definitions not used after domain update
```

---

## Scaling

```yaml
scaling:
  model: horizontal
  min_instances: 1
  max_instances: unbounded

  inter_agent:
    protocol: message-bus-only
    direct_http: to source domains only (definition fetch via /v1/message)
    routing: by agent name via service directory
    reason: >
      All phase dispatch goes through the task agent via events.
      Definition fetch requires synchronous response from domains.

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: file lock with TTL
      leader: [workflow_execution, dag_dispatch, definition_cache]
      follower: [health_reporting, action_handling, read_queries]
      promotion: automatic when leader lock expires
    state_sharing:
      mechanism: shared flat-file storage + in-memory execution state
      consistency_window: immediate (leader handles all execution)
      conflict_resolution: >
        Execution IDs are globally unique (UUID v7). Leader election
        prevents duplicate workflow execution. In-flight state is
        reconstructed from storage on leader promotion.

  event_handling:
    consumer_group: workflow
    delivery: one-per-group
    description: >
      Bus delivers each workflow.trigger event to ONE instance in
      the "workflow" consumer group. Leader handles execution.
      task.complete/failed events are also delivered one-per-group
      to prevent duplicate phase tracking.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 5
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same storage directory. Definition
      cache is in-memory and rebuilt per instance.
    consumer_groups:
      shadow_phase: "workflow@vN+1"
      after_cutover: "workflow"
```

---

## Implementation Notes

- **DAG resolution**: Topological sort uses Kahn's algorithm. Phases
  with no dependencies form Level 0, dispatched concurrently. Each
  subsequent level waits for the previous level to complete.
- **Input references**: The `$` prefix in phase inputs resolves at
  dispatch time. `$task.payload.*` reads from the trigger input.
  `$phases.<name>.output` reads from a completed phase's output.
  `$entity.*` and `$config.*` read from the trigger context.
- **Definition caching**: Workflow definitions are fetched from source
  domains via POST /v1/message (action: get_workflow). Cached in memory
  per domain+workflow name. Cache invalidated when domain re-registers
  (system.agent.registered event).
- **Approval gates**: When a phase has `approval: required`, the phase
  output is stored but NOT exposed to downstream phases until approval.
  The workflow enters `pending_approval` state and waits for a
  `workflow.approval.decision` event.
- **Persistence**: Execution records are appended to JSONL storage on
  every state change (started, phase complete, finished). This enables
  recovery on restart — the agent can resume from the last persisted state.
- **Timeout enforcement**: The workflow agent tracks a deadline per
  execution (started_at + config.workflow_timeout). On expiry, all
  in-flight phases are cancelled via task.cancel events.
- **Self-dispatch**: When `phase.agent == "self"`, the workflow agent
  sends a direct message to the invoker domain instead of going through
  the task agent. The response is treated as the phase output.

---

## Verification Checklist

- [ ] Subscribes to workflow.trigger (scope: self) and dispatches DAG
- [ ] Fetches workflow definitions from source domains via get_workflow message
- [ ] Caches definitions, invalidates on system.agent.registered
- [ ] Topological sort with cycle detection
- [ ] Phases dispatched concurrently within a level via task.submit events
- [ ] Phase results tracked from task.complete/task.failed events
- [ ] on_error strategies applied: fail, skip, retry
- [ ] Approval gates pause execution until workflow.approval.decision
- [ ] workflow.completed published with scope = invoker
- [ ] callback_topic receives result if specified
- [ ] WorkflowExecution persisted to flat-file storage
- [ ] Workflow-level timeout cancels all in-flight phases
- [ ] trace_id and correlation_id propagated through all events
- [ ] Dependencies declare version ranges and specific bindings
- [ ] on_change rules defined for all dependencies
- [ ] State machine transitions validated — no implicit states
- [ ] Startup sequence validation gates — each step has validates/on-fail
- [ ] Shutdown cancels in-flight phases and fails active workflows
- [ ] Health endpoint reports accurate status per health criteria
- [ ] Scaling: inter-agent communication via message bus (except definition fetch)
- [ ] Scaling: leader election prevents duplicate workflow execution
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Override audit records who, what, when, why
- [ ] Constraints enforced — max_concurrent, max_phases, no cycle bypass
- [ ] Security: all endpoints require valid token
- [ ] Self-dispatch handles phase.agent == "self" correctly
- [ ] Workflow timeout cancels all in-flight phases
