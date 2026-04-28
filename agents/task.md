<!-- blueprint
type: agent
kind: infrastructure
name: task
version: 1.0.0
port: 9781
requires: [protocol/spec, protocol/types, architecture/agent]
extends: [patterns/task-dispatch, patterns/messaging, patterns/retry, patterns/scope, patterns/policy]
depends_on: []
platform: any
tier: free
-->

# Task Agent

Infrastructure agent that owns task dispatch and tracking. Receives
`task.submit` events, dispatches work to target agents via
`POST /v1/execute`, tracks completion, and publishes `task.complete`
or `task.failed` back to the requester.

The Task Agent is the single dispatch point for all agent execution.
It handles priority queuing, concurrency awareness, timeout
enforcement, and dead-letter tracking for failed dispatches.

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
        - path: /v1/execute
          methods: [POST]
          request_type: TaskRequest
          response_fields: [status, summary, output]
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
        - behavior: dead-letter
          parameters: [max_retries, dlq_topic]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/retry
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

depends_on: []
  # No runtime agent dependencies. The task agent dispatches to
  # target agents, but if a target is unavailable the task is
  # retried or failed — the task agent itself does not degrade.
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  TaskRecord:
    description: Persistent record of a dispatched task
    fields:
      task_id:
        type: string
        format: uuid-v7
        description: Unique task identifier
      workflow_id:
        type: string
        optional: true
        description: Parent workflow execution (if applicable)
      phase:
        type: string
        optional: true
        description: Workflow phase name
      target_agent:
        type: string
        description: Agent to dispatch to
      action:
        type: string
        description: Action name for the target agent
      input:
        type: object
        optional: true
        description: Payload sent to target agent
      priority:
        type: string
        enum: [critical, high, normal, low]
        default: normal
        description: Dispatch priority
      status:
        type: string
        enum: [queued, dispatched, completed, failed, timeout, cancelled]
        description: Current task state
      timeout:
        type: int
        default: 300
        unit: seconds
        description: Execution timeout
      submitted_at:
        type: int64
        auto: true
        description: When task was submitted
      dispatched_at:
        type: int64
        optional: true
        description: When HTTP dispatch was sent
      completed_at:
        type: int64
        optional: true
        description: When task finished
      result_summary:
        type: text
        max: 1024
        optional: true
        description: Truncated result or error
      requester:
        type: string
        description: Agent that submitted the task
      trace_id:
        type: string
        description: Trace context for correlation
      correlation_id:
        type: string
        optional: true
        description: Workflow correlation context
      retry_count:
        type: int
        default: 0
        description: Number of dispatch retries
    constraints:
      - name: uq_task_id
        type: unique
        fields: [task_id]

  AgentCapacity:
    description: Tracked capacity for a target agent
    fields:
      agent_name:
        type: string
        description: Agent identifier
      max_concurrent:
        type: int
        description: Max concurrent tasks (from manifest)
      in_flight:
        type: int
        default: 0
        description: Currently dispatched task count
      last_seen:
        type: int64
        description: Last registration/health timestamp
```

## Identity

| Field | Value |
|-------|-------|
| Name | `task` |
| Type | `infrastructure` |
| Port | `9781` (advisory) |
| Namespace | `task.*` |

## Capabilities

```json
{
  "capabilities": [
    {"name": "task:execute", "resources": []},
    {"name": "agent:message", "resources": []}
  ]
}
```

## Events

### Published (namespace: `task`)

| Topic | Scope | Payload | When |
|-------|-------|---------|------|
| `task.accepted` | requester | `{task_id, position}` | Task queued |
| `task.dispatched` | requester | `{task_id, target_agent}` | HTTP call sent |
| `task.complete` | requester | `{task_id, workflow_id, phase, result}` | Agent returned success |
| `task.failed` | requester | `{task_id, workflow_id, phase, error}` | Agent returned failure or unreachable |
| `task.timeout` | requester | `{task_id, timeout_seconds}` | Task exceeded timeout |
| `task.cancelled` | requester | `{task_id, reason}` | Task cancelled by requester |

### Subscribed

| Pattern | Scope | Group | Purpose |
|---------|-------|-------|---------|
| `task.submit` | `self` | `task` | Receive task dispatch requests |
| `task.cancel` | `self` | `task` | Cancel in-flight tasks |
| `system.agent.registered` | `self` | `task` | Update agent capacity info |
| `system.agent.deregistered` | `self` | `task` | Remove agent from dispatch pool |

## Manifest

```json
{
  "name": "task",
  "type": "infrastructure",
  "version": "2.0.0",
  "description": "Task dispatch and tracking — priority queue, concurrency control, timeout enforcement",
  "url": "http://localhost:9781",
  "public_key": "<hex>",
  "capabilities": [
    {"name": "task:execute", "resources": []},
    {"name": "agent:message", "resources": []}
  ],
  "publishes": ["task"],
  "subscriptions": [
    {"pattern": "task.submit", "scope": "self", "group": "task", "max_concurrent": 50},
    {"pattern": "task.cancel", "scope": "self", "group": "task"},
    {"pattern": "system.agent.registered", "scope": "self"},
    {"pattern": "system.agent.deregistered", "scope": "self"}
  ]
}
```

## Core Logic

### HandleEvent: task.submit

```
1. Parse submit payload:
   { task_id, workflow_id, phase, target_agent, action,
     input, timeout, trace_id, correlation_id, priority }

2. Validate target agent exists in service directory
   If not found → publish task.failed immediately

3. Check agent capacity:
   Look up target_agent.max_concurrent from cached manifest
   Count in-flight tasks to this agent
   If at capacity → queue task (priority-ordered)

4. Publish: task.accepted (scope: requester from event source)

5. Dispatch:
   Build TaskRequest:
     id: task_id
     action: action
     payload: input
     context: { trace_id, correlation_id, services, workspace_root }
   POST target_agent.url + /v1/execute
     Timeout: task timeout (from submit payload or default)
     Headers: Authorization: Bearer <token>, X-Trace-Id: <trace_id>

6. Handle response:
   2xx + status "success":
     Publish: task.complete (scope: event.source)
       payload: { task_id, workflow_id, phase, result: response }
   2xx + status "failed":
     Publish: task.failed (scope: event.source)
       payload: { task_id, workflow_id, phase, error: response.summary }
   429:
     Re-queue with Retry-After delay
   5xx / connection error:
     Retry per patterns/retry (exponential backoff)
     After exhaustion → publish task.failed
   Timeout:
     Publish: task.timeout (scope: event.source)

7. Update in-flight tracking:
   Remove task from in-flight
   If queued tasks exist for this agent → dispatch next
```

### HandleEvent: task.cancel

```
1. Parse: { task_id, reason }
2. Look up task in in-flight tracking
3. If found and still running:
   a. Cancel HTTP request (if supported by runtime)
   b. Remove from in-flight
   c. Publish: task.cancelled (scope: original requester)
4. If found in queue:
   a. Remove from queue
   b. Publish: task.cancelled
5. If not found → ignore (already completed)
```

### HandleEvent: system.agent.registered

```
1. Extract agent name and manifest from event payload
2. Update capacity cache:
   agent_capacity[name] = manifest.max_concurrent (or default)
3. If agent was previously unreachable:
   Check queue for pending tasks targeting this agent
   Dispatch queued tasks
```

### HandleEvent: system.agent.deregistered

```
1. Extract agent name
2. Remove from capacity cache
3. Fail all in-flight tasks targeting this agent:
   Publish: task.failed for each
4. Fail all queued tasks targeting this agent:
   Publish: task.failed for each
```

## Priority Queue

Tasks are dispatched in priority order when queued:

| Priority | Value | Description |
|----------|-------|-------------|
| `critical` | 0 | Immediate dispatch, preempts queue |
| `high` | 1 | Dispatched before normal tasks |
| `normal` | 2 | Default priority |
| `low` | 3 | Dispatched when no higher-priority tasks waiting |

Within the same priority, tasks dispatch in FIFO order.

## Concurrency Control

The Task Agent tracks in-flight tasks per target agent:

```
in_flight: map[agent_name] → []task_id
queue: priority_queue[task_submit_event]
capacity: map[agent_name] → int (from manifest.max_concurrent)
```

When dispatching:
- If `len(in_flight[agent]) < capacity[agent]` → dispatch immediately
- Otherwise → enqueue (priority-ordered)
- On task completion → dequeue and dispatch next for that agent

Default capacity (when manifest doesn't declare max_concurrent):
- Domain controller: 10
- Work agent: 5
- Infrastructure agent: 20

## HandleMessage Actions

| Action | Purpose |
|--------|---------|
| `get_task` | Return task status by task_id |
| `list_tasks` | List tasks (filterable by status, agent, workflow) |
| `get_queue_depth` | Return queue depth per agent |
| `get_agent_capacity` | Return capacity info for all tracked agents |

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
        validates: task.submit subscription active
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
        validates: in_flight = 0 OR drain timeout (30s) elapsed

  entity.TaskRecord:
    initial: queued
    transitions:
      - from: queued
        to: dispatched
        trigger: http_call_sent
        validates: POST /v1/execute sent to target agent
      - from: dispatched
        to: completed
        trigger: success_response
        validates: 2xx with status = success
      - from: dispatched
        to: failed
        trigger: error_response
        validates: 2xx with status = failed OR 5xx after retry exhaustion
      - from: dispatched
        to: timeout
        trigger: timeout_exceeded
        validates: no response within TaskRecord.timeout
      - from: queued
        to: cancelled
        trigger: cancel_event
        validates: task.cancel received for this task_id
      - from: dispatched
        to: cancelled
        trigger: cancel_event
        validates: task.cancel received, HTTP request cancelled if possible
      - from: dispatched
        to: queued
        trigger: rate_limited
        validates: 429 received, re-queue with Retry-After delay
      - from: queued
        to: failed
        trigger: agent_deregistered
        validates: target agent removed from service directory
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/task/
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Open flat-file JSONL storage directory
  Validates:   Directory writable, existing task records parseable
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE

Step 4 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 5 — Subscribe to Events
  Action:      Subscribe to: task.submit, task.cancel,
               system.agent.registered, system.agent.deregistered,
               system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT with SUBSCRIPTION_FAILED

Step 6 — Rebuild In-Flight State
  Action:      Read tasks.jsonl for queued/dispatched tasks
  Validates:   Records parse as TaskRecord type
  On Fail:     Enter degraded state, log warning
  Note:        Queued tasks are re-queued; dispatched tasks are
               marked as failed (no way to recover HTTP state)

Step 7 — Build Agent Capacity Cache
  Action:      Query orchestrator GET /v1/services for registered agents
  Validates:   At least one agent registered
  On Fail:     Continue with empty cache, populate on system.agent.registered

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9781, pending_tasks: N, agents_cached: N}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Tasks
  Action:      Unsubscribe from task.submit, return 503 for new requests

Step 3 — Drain In-Flight
  Action:      Wait for dispatched HTTP calls to complete (up to 30s)
  On Timeout:  Record remaining dispatched tasks as timeout

Step 4 — Fail Queued Tasks
  Action:      Publish task.failed for all queued tasks
               (they will be re-submitted by workflow agent if needed)

Step 5 — Persist State
  Action:      Flush task records to storage

Step 6 — Deregister
  Action:      DELETE /v1/register

Step 7 — Exit
  Log: lifecycle.stopped {uptime_seconds, tasks_drained, tasks_failed}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - task.submit subscription active
      - storage writable
      - in_flight_total < 80% of config.max_concurrent
    response:
      status: healthy
      details: {in_flight, queue_depth, max_concurrent, agents_tracked}

  degraded:
    conditions:
      - storage errors (retrying)
      - queue_depth > 80% of config.queue_max
      - in_flight_total >= 80% of max_concurrent
    response:
      status: degraded
      details: {reason, queue_depth, in_flight}

  unhealthy:
    conditions:
      - storage unreachable after retry exhaustion
      - task.submit subscription lost
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "task"`:

```
1. Parse new blueprint, verify against schema
2. Validate in-flight tasks against updated types
3. Apply new configuration values
4. Log: lifecycle.version_updated {from, to}
```

---

## Triggers

```yaml
triggers:
  - name: task_submit
    type: event
    topic: task.submit
    description: Receive task dispatch request from workflow agent

  - name: task_cancel
    type: event
    topic: task.cancel
    description: Cancel queued or in-flight task

  - name: agent_registered
    type: event
    topic: system.agent.registered
    description: Update agent capacity cache

  - name: agent_deregistered
    type: event
    topic: system.agent.deregistered
    description: Fail tasks targeting removed agents

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "task"
    description: Self-update if task blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [get_task, list_tasks, get_queue_depth, get_agent_capacity]
    description: Agent-to-agent and operator query actions
```

---

## Actions

### dispatch (internal — triggered by task.submit event)

**Purpose:** Dispatch a task to the target agent via HTTP.

**Input:** `task.submit` event payload:
`{task_id, workflow_id, phase, target_agent, action, input, timeout, trace_id, correlation_id, priority}`

**Processing:**

```
1. Validate target agent exists in capacity cache
   If not found → publish task.failed immediately
2. Create TaskRecord (status: queued)
3. Check capacity: in_flight[agent] < capacity[agent]?
   If yes → dispatch immediately
   If no → enqueue (priority-ordered)
4. Publish: task.accepted (scope: requester)
5. Dispatch via POST target_agent.url + /v1/execute:
   Build TaskRequest with action, payload, context
   Headers: Authorization: Bearer <token>, X-Trace-Id: <trace_id>
   Timeout: task timeout
6. Handle response per state machine transitions
7. Update in-flight tracking, dispatch next queued if capacity freed
```

**Output:** Events: `task.accepted`, then `task.complete` or `task.failed` or `task.timeout`

**Errors:** `TARGET_NOT_FOUND` (permanent), `DISPATCH_TIMEOUT` (transient), `DISPATCH_ERROR` (transient)

---

### get_task

**Purpose:** Return task status by task_id.

**Input:** `{task_id: string}`

**Output:** `TaskRecord`

**Errors:** `NOT_FOUND` (permanent)

---

### list_tasks

**Purpose:** List tasks with optional filters.

**Input:** `{status?, target_agent?, workflow_id?, limit?, offset?}`

**Output:** `{tasks: TaskRecord[], total: int}`

---

## Execute Workflow

The task agent operates reactively on task.submit events:

```
Phase 1 — Task Reception
  Trigger:   task.submit event received
  Action:    Parse submit payload
  Validate:  target_agent, action, task_id present

Phase 2 — Capacity Check
  Query:     in_flight[target_agent] vs capacity[target_agent]
  If at capacity:
    Enqueue task in priority queue
    Publish: task.accepted {task_id, position: queue_position}
    Return (dispatched when capacity frees)
  If available:
    Proceed to Phase 3

Phase 3 — HTTP Dispatch
  Action:    POST target_agent.url + /v1/execute
  Payload:   TaskRequest {id, action, payload, context}
  Headers:   Authorization, X-Trace-Id, X-Correlation-Id
  Timeout:   From submit payload or config.default_timeout
  TaskRecord state: queued → dispatched

Phase 4 — Response Handling
  2xx + success:
    TaskRecord state: dispatched → completed
    Publish: task.complete (scope: requester)
  2xx + failed:
    TaskRecord state: dispatched → failed
    Publish: task.failed (scope: requester)
  429:
    TaskRecord state: dispatched → queued
    Re-queue with Retry-After delay
  5xx / connection error:
    Retry per patterns/retry (exponential backoff)
    After exhaustion: dispatched → failed
    Publish: task.failed
  Timeout:
    TaskRecord state: dispatched → timeout
    Publish: task.timeout (scope: requester)

Phase 5 — Queue Advancement
  Decrement in_flight[target_agent]
  If queued tasks exist for this agent:
    Dequeue highest-priority task
    Dispatch (back to Phase 3)

Phase 6 — Persist
  Append/update TaskRecord in tasks.jsonl
  Emit metrics
```

## Storage

Task records are stored in flat-file JSONL:

```
.weblisk/data/task/tasks.jsonl
```

Each line is a task record: `{task_id, workflow_id, phase, target_agent,
status, submitted_at, dispatched_at, completed_at, result_summary}`.

In-flight tracking and queue are in-memory (reconstructable from
pending tasks in storage on restart).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_TASK_PORT` | `9781` | Listen port |
| `WL_TASK_MAX_CONCURRENT` | `50` | Max concurrent task dispatches |
| `WL_TASK_DEFAULT_TIMEOUT` | `300` | Default task timeout (seconds) |
| `WL_TASK_QUEUE_MAX` | `1000` | Max queued tasks before rejecting |
| `WL_TASK_DATA_DIR` | `.weblisk/data/task` | Storage directory |

---

## Collaboration

```yaml
events_published:
  - topic: task.accepted
    payload: {task_id, position}
    scope: requester
    when: Task queued for dispatch

  - topic: task.dispatched
    payload: {task_id, target_agent}
    scope: requester
    when: HTTP call sent to target agent

  - topic: task.complete
    payload: {task_id, workflow_id, phase, result}
    scope: requester
    when: Target agent returned success

  - topic: task.failed
    payload: {task_id, workflow_id, phase, error}
    scope: requester
    when: Target agent returned failure or unreachable after retries

  - topic: task.timeout
    payload: {task_id, timeout_seconds}
    scope: requester
    when: Task exceeded timeout

  - topic: task.cancelled
    payload: {task_id, reason}
    scope: requester
    when: Task cancelled by requester

events_subscribed:
  - topic: task.submit
    scope: self
    action: Receive and dispatch task

  - topic: task.cancel
    scope: self
    action: Cancel queued or in-flight task

  - topic: system.agent.registered
    action: Update agent capacity cache from manifest

  - topic: system.agent.deregistered
    action: Fail all in-flight and queued tasks for that agent

  - topic: system.shutdown
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    filter: blueprint_name = "task"
    action: Self-update procedure

direct_messages:
  - target: variable (target_agent from task.submit)
    action: POST /v1/execute
    when: Task dispatch
    reason: Synchronous HTTP required to track success/failure
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All task dispatch is autonomous
  supervised:    Normal operation; queue purge requires operator
  manual-only:   All dispatch paused, operator triggers manually

overridable_behaviors:
  - behavior: automatic_dispatch
    default: enabled
    override: Set WL_TASK_DISPATCH_PAUSED=true
    audit: logged

  - behavior: automatic_retry
    default: enabled (per patterns/retry)
    override: Set WL_TASK_MAX_RETRIES=0
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: pause_dispatch
    description: Pause all task dispatch (tasks queue but don't fire)
    allowed: operator

  - action: resume_dispatch
    description: Resume task dispatch
    allowed: operator

  - action: purge_queue
    description: Cancel all queued tasks
    allowed: operator

  - action: force_dispatch
    description: Bypass capacity check for a specific task
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
    - MUST NOT modify data owned by target agents
    - MUST NOT send requests to agents not in the service directory
    - Dispatch rate bounded by config.max_concurrent

  forbidden_actions:
    - MUST NOT execute tasks locally — always dispatches to target agents
    - MUST NOT modify task payloads after submission
    - MUST NOT bypass priority queue ordering
    - MUST NOT dispatch to deregistered agents

  resource_limits:
    memory: 512 MB (process limit)
    max_queue_depth: config.queue_max (default 1000)
    max_concurrent_dispatches: config.max_concurrent (default 50)
    task_record_storage: indefinite (manual purge)
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: TARGET_NOT_FOUND
      description: target_agent not in service directory
    - code: NOT_FOUND
      description: Referenced task_id does not exist
    - code: QUEUE_FULL
      description: Queue depth >= config.queue_max
    - code: INVALID_INPUT
      description: Missing required fields in task.submit payload

  transient:
    - code: DISPATCH_TIMEOUT
      description: Target agent did not respond within timeout
      fallback: Record as timeout, publish task.timeout
    - code: DISPATCH_ERROR
      description: Target agent returned 5xx or connection error
      fallback: Retry per patterns/retry with exponential backoff
    - code: RATE_LIMITED
      description: Target agent returned 429
      fallback: Re-queue with Retry-After delay
    - code: STORAGE_ERROR
      description: Storage read/write failure
      fallback: Continue dispatch from in-memory state, persist when recovered
```

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| `task_dispatch_total` | counter | By target agent, action, and status |
| `task_dispatch_duration_seconds` | histogram | Time from submit to complete |
| `task_queue_depth` | gauge | Current queue depth per target agent |
| `task_inflight` | gauge | Currently dispatched tasks per agent |
| `task_timeout_total` | counter | Timed out tasks by agent |
| `task_retry_total` | counter | Dispatch retries by agent |

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Dispatch tasks to any registered agent via POST /v1/execute

    - capability: storage:read
      resources: [tasks]
      description: Read own task records

    - capability: storage:write
      resources: [tasks]
      description: Write own task records

  data_sensitivity:
    - data: Task payloads (input)
      classification: variable
      handling: May contain domain-specific data; logged as size only

    - data: Task results
      classification: variable
      handling: Truncated to 1 KB in storage, encrypted at rest

    - data: Agent capacity information
      classification: low
      handling: Operational metadata, logged freely

    - data: trace_id / correlation_id
      classification: low
      handling: Correlation identifiers, logged freely

  access_control:
    - caller: workflow agent
      actions: [task.submit, task.cancel]
      note: Primary task submitter

    - caller: Any registered agent
      actions: [get_task, list_tasks, get_queue_depth, get_agent_capacity]
      note: Read-only task status

    - caller: Operator (auth token with operator role)
      actions: [get_task, list_tasks, get_queue_depth, get_agent_capacity,
                pause_dispatch, resume_dispatch, purge_queue, force_dispatch]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Task dispatched and completed
    trigger: task.submit
    input:
      task_id: task_001
      target_agent: seo-analyzer
      action: analyze
      input: {url: "https://example.com"}
      priority: normal
    expected:
      task.accepted published
      POST /v1/execute sent to seo-analyzer
      task.complete published on success
    validates:
      - TaskRecord created with status: dispatched
      - TaskRecord updated to status: completed
      - trace_id propagated in HTTP headers

  - name: Priority queue ordering
    trigger: 3 task.submit events (low, critical, high) while agent at capacity
    expected:
      Queue order: critical, high, low
      Critical dispatched first when capacity frees
    validates:
      - Priority ordering within queue
      - FIFO within same priority level
```

### Error Cases

```yaml
  - name: Target agent not found
    trigger: task.submit with target_agent = "nonexistent"
    expected:
      task.failed published immediately
    validates:
      - TARGET_NOT_FOUND error, no HTTP dispatch attempted

  - name: Agent returns 5xx, retries exhausted
    trigger: task.submit to agent returning 500
    expected:
      Retries per patterns/retry
      task.failed after exhaustion
    validates:
      - Exponential backoff applied
      - retry_count incremented per attempt

  - name: Task timeout
    trigger: task.submit with timeout: 5, agent takes 10s
    expected:
      task.timeout published after 5 seconds
    validates:
      - HTTP request cancelled
      - TaskRecord status: timeout

  - name: Agent returns 429
    trigger: task.submit, agent returns 429 with Retry-After: 30
    expected:
      Task re-queued with 30s delay
    validates:
      - Retry-After header respected
      - TaskRecord state: dispatched → queued
```

### Edge Cases

```yaml
  - name: Cancel queued task
    trigger: task.cancel for a queued (not yet dispatched) task
    expected:
      task.cancelled published
      Task removed from queue
    validates:
      - TaskRecord status: cancelled

  - name: Cancel in-flight task
    trigger: task.cancel for a dispatched task
    expected:
      HTTP request cancelled if possible
      task.cancelled published
    validates:
      - Graceful cancellation attempted

  - name: Agent deregistered with in-flight tasks
    trigger: system.agent.deregistered for agent with 3 in-flight tasks
    expected:
      All 3 tasks fail with task.failed
      All queued tasks for that agent also fail
    validates:
      - Capacity cache updated
      - No orphaned tasks

  - name: Queue at max depth
    trigger: task.submit when queue_depth = config.queue_max
    expected_error: QUEUE_FULL
    validates:
      - Task rejected, not queued
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
    direct_http: to target agents only (POST /v1/execute)
    routing: by agent name via service directory
    reason: >
      Task dispatch requires synchronous HTTP to track success/failure.
      This is the ONLY synchronous call in the Weblisk architecture.
      All other communication is event-driven via the message bus.

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: file lock with TTL
      leader: [queue_management, capacity_tracking, dispatch_loop]
      follower: [health_reporting, action_handling, read_queries]
      promotion: automatic when leader lock expires
    state_sharing:
      mechanism: shared flat-file storage + in-memory queue
      consistency_window: immediate (leader handles all dispatch)
      conflict_resolution: >
        Task IDs are globally unique (UUID v7). Leader election
        prevents duplicate dispatch. In-memory queue is
        reconstructed from storage on leader promotion.

  event_handling:
    consumer_group: task
    delivery: one-per-group
    description: >
      Bus delivers each task.submit event to ONE instance in the
      "task" consumer group. Leader processes the dispatch.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 10
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same storage directory. Queue state
      is in-memory and reconstructed on startup.
    consumer_groups:
      shadow_phase: "task@vN+1"
      after_cutover: "task"
```

---

## Implementation Notes

- **Single sync call**: The `POST /v1/execute` dispatch is the only
  synchronous HTTP call in the Weblisk architecture. Everything else
  is event-driven. This is intentional — task dispatch needs a
  synchronous response to track success/failure.
- **In-memory queue**: The priority queue and in-flight tracking are
  in-memory for performance. On restart, queued tasks are reconstructed
  from storage (status = queued). Dispatched tasks at restart are
  marked as failed — the workflow agent will resubmit if needed.
- **Capacity defaults**: When an agent manifest doesn't declare
  `max_concurrent`, defaults apply: domain controller = 10,
  work agent = 5, infrastructure agent = 20.
- **Trace propagation**: `trace_id` and `correlation_id` from the
  submit event are propagated as HTTP headers to target agents.
- **Dead-letter**: Tasks that fail after retry exhaustion are persisted
  with status = failed. No automatic resubmission — the workflow agent
  decides whether to retry at the workflow level.
- **429 handling**: The task agent respects `Retry-After` headers from
  target agents. Tasks are re-queued with the specified delay, not
  counted as failures.

---

## Verification Checklist

- [ ] Subscribes to task.submit (scope: self) and dispatches to target agents
- [ ] Dispatches via POST /v1/execute with TaskRequest
- [ ] Publishes task.complete on successful execution
- [ ] Publishes task.failed on execution failure or unreachable agent
- [ ] Publishes task.timeout when task exceeds timeout
- [ ] Handles 429 from agents with re-queue and Retry-After
- [ ] Priority queue dispatches critical > high > normal > low
- [ ] Concurrency control respects agent max_concurrent
- [ ] Queued tasks dispatch when capacity frees up
- [ ] task.cancel removes from queue or cancels in-flight
- [ ] Agent capacity updated from system.agent.registered events
- [ ] Agent deregistration fails all in-flight and queued tasks for that agent
- [ ] Task records persisted to flat-file storage
- [ ] trace_id and correlation_id propagated to dispatched tasks
- [ ] Dependencies declare version ranges and specific bindings
- [ ] on_change rules defined for all dependencies
- [ ] State machine transitions validated — no implicit states
- [ ] Startup sequence validation gates — each step has validates/on-fail
- [ ] Shutdown drains in-flight tasks before exit
- [ ] Health endpoint reports accurate status per health criteria
- [ ] Scaling: inter-agent communication via message bus (except /v1/execute)
- [ ] Scaling: leader election prevents duplicate dispatch
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Override audit records who, what, when, why
- [ ] Constraints enforced — max_queue_depth, max_concurrent
- [ ] Security: all endpoints require valid token
- [ ] Dead-letter tasks persisted for analysis
