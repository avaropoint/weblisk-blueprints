<!-- blueprint
type: pattern
name: task-dispatch
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/messaging, patterns/retry]
platform: any
tier: free
-->

# Task Dispatch Pattern

Unified task submission, priority queuing, dispatch, and lifecycle
tracking across all Weblisk agents. This pattern is the single
coordination mechanism for agent execution — every unit of work
flows through task dispatch. Agents that submit or receive work
`extends: patterns/task-dispatch` and inherit the submission
envelope, status lifecycle, and event contracts.

## Overview

Task dispatch is the foundational coordination primitive in Weblisk.
No agent executes work directly on another agent — all execution
requests are submitted as tasks, routed through a priority queue,
dispatched to target agents via `POST /v1/execute`, and tracked
through a defined status lifecycle.

This pattern covers:

- **Submission**: Structured envelope for requesting agent execution
- **Queuing**: Priority-aware, concurrency-aware task queuing
- **Dispatch**: HTTP-based delivery to target agents with timeout
- **Tracking**: Full lifecycle from submission to completion/failure
- **Dead-letter**: Capture of failed tasks after retry exhaustion

The Task Agent (`agents/task`) is the canonical implementation of
this pattern. Other agents interact with task dispatch exclusively
through the event and type contracts defined here.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/execute
          methods: [POST]
          request_type: TaskRequest
          response_fields: [status, summary, output]
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
        - name: TaskRequest
          fields_used: [id, from, target_agent, action, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
        - name: MessageEnvelope
          fields_used: [from, to, action, payload, trace_id]
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
```

---

## Design Principles

1. **Single Dispatch Point** — All agent work flows through task dispatch. No direct agent-to-agent execution calls. This guarantees observability, priority enforcement, and concurrency control for every unit of work in the system.
2. **Priority-Aware Ordering** — Tasks declare a priority level; the dispatch queue honors it. Within the same priority, tasks are dispatched in FIFO order. Critical tasks preempt the queue.
3. **Concurrency-Aware** — Dispatch respects per-agent concurrency limits declared in agent manifests. Tasks exceeding capacity are queued until a slot opens, preventing agent overload.
4. **Observable** — Every task state transition emits an event. Submitters can track task progress from submission through completion without polling.
5. **Dead-Letter Safety** — Tasks that fail after retry exhaustion are captured in a dead-letter store with full failure context. No task is silently dropped.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: task-submission
      description: Submit a unit of work for dispatch to a target agent
      parameters:
        - name: target_agent
          type: string
          required: true
          description: Name of the agent to dispatch work to
        - name: action
          type: string
          required: true
          description: Action name for the target agent to execute
        - name: input
          type: object
          required: false
          description: Payload delivered to the target agent
        - name: priority
          type: TaskPriority
          required: false
          default: normal
          description: Dispatch priority level
        - name: timeout
          type: int
          required: false
          default: 300
          description: Execution timeout in seconds
      inherits: Task submission envelope, async handle, status tracking
      overridable: false
      override_constraints: Submission envelope format is fixed; extenders cannot alter fields

    - name: priority-queuing
      description: Queue tasks by priority when target agent is at capacity
      parameters:
        - name: priority
          type: TaskPriority
          required: true
          description: Priority level determining queue position
        - name: max_queue_depth
          type: int
          required: false
          default: 10000
          description: Maximum queued tasks before rejecting submissions
      inherits: Priority-ordered FIFO queue semantics
      overridable: true
      override_constraints: Must preserve priority ordering; may adjust max_queue_depth

    - name: dispatch-execution
      description: Deliver task to target agent via HTTP POST and track result
      parameters:
        - name: target_url
          type: string
          required: true
          description: Target agent URL from service directory
        - name: timeout
          type: int
          required: true
          description: Per-task execution timeout in seconds
        - name: max_retries
          type: int
          required: false
          default: 3
          description: Maximum dispatch retry attempts on transient failure
      inherits: HTTP dispatch, timeout enforcement, retry on transient errors
      overridable: false
      override_constraints: Dispatch protocol is fixed (POST /v1/execute)

    - name: concurrency-control
      description: Track in-flight tasks per agent and enforce capacity limits
      parameters:
        - name: max_concurrent
          type: int
          required: true
          description: Maximum simultaneous tasks for a target agent
        - name: default_capacity
          type: int
          required: false
          default: 5
          description: Default capacity when agent manifest omits max_concurrent
      inherits: Per-agent in-flight tracking, capacity-gated dispatch
      overridable: true
      override_constraints: Must not exceed agent manifest declared max_concurrent

    - name: dead-letter-handling
      description: Capture failed tasks after retry exhaustion for later inspection
      parameters:
        - name: max_retries
          type: int
          required: true
          description: Retry count before dead-lettering
        - name: retention
          type: int
          required: false
          default: 604800
          description: Dead-letter retention period in seconds (default 7 days)
      inherits: Dead-letter capture, failure context preservation
      overridable: true
      override_constraints: Must preserve original task envelope and failure reason

  types:
    - name: TaskSubmission
      description: Envelope used by agents to submit work for dispatch
      inherited_by: Types section
    - name: TaskHandle
      description: Async handle returned to the submitter on task acceptance
      inherited_by: Types section
    - name: TaskResult
      description: Completion or failure envelope returned after execution
      inherited_by: Types section
    - name: TaskPriority
      description: Priority levels controlling dispatch ordering
      inherited_by: Types section
    - name: TaskStatus
      description: Lifecycle states a task transitions through
      inherited_by: Types section
    - name: DeadLetterEntry
      description: Captured failed task with full failure context
      inherited_by: Types section
    - name: AgentCapacity
      description: Tracked concurrency capacity for a target agent
      inherited_by: Types section

  events:
    - topic: task.submit
      description: New task submitted for dispatch
      payload: {task_id, target_agent, action, input, priority, timeout, trace_id, correlation_id}
    - topic: task.accepted
      description: Task accepted and queued for dispatch
      payload: {task_id, position, priority}
    - topic: task.dispatched
      description: Task sent to target agent via HTTP
      payload: {task_id, target_agent, dispatched_at}
    - topic: task.completed
      description: Target agent finished task successfully
      payload: {task_id, workflow_id, phase, result, duration_ms}
    - topic: task.failed
      description: Target agent reported failure or dispatch exhausted retries
      payload: {task_id, workflow_id, phase, error, retry_count}
    - topic: task.timeout
      description: Task exceeded execution timeout
      payload: {task_id, timeout_seconds, target_agent}
    - topic: task.cancelled
      description: Task cancelled by requester
      payload: {task_id, reason}
    - topic: task.dead-letter
      description: Task moved to dead-letter after max retries exhausted
      payload: {task_id, target_agent, action, error, attempts, original_submission}
```

---

## Submission Envelope

Agents submit tasks by publishing a `task.submit` event. The
envelope is the universal interface for requesting agent execution.

### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| task_id | string (uuid-v7) | yes | Unique task identifier (caller-generated) |
| target_agent | string | yes | Name of the agent to execute |
| action | string | yes | Action name for the target agent |
| input | object | no | Payload delivered to the target agent |
| priority | TaskPriority | no | Dispatch priority (default: `normal`) |
| timeout | int | no | Execution timeout in seconds (default: 300) |
| trace_id | string | yes | Distributed trace context |
| correlation_id | string | no | Workflow correlation identifier |
| workflow_id | string | no | Parent workflow execution ID |
| phase | string | no | Workflow phase name |

### Example Submission

```json
{
  "task_id": "019012a3-7c8e-7f00-a1b2-c3d4e5f60001",
  "target_agent": "seo-analyzer",
  "action": "analyze_page",
  "input": {
    "url": "https://example.com",
    "checks": ["meta", "headings", "links"]
  },
  "priority": "normal",
  "timeout": 120,
  "trace_id": "trace-abc123",
  "workflow_id": "wf-001",
  "phase": "seo-check"
}
```

---

## Priority Queue

Tasks are dispatched in priority order. When a target agent is at
capacity, tasks queue and dispatch in priority-then-FIFO order.

### Priority Levels

| Priority | Value | Semantics |
|----------|-------|-----------|
| `critical` | 0 | Immediate dispatch; preempts the queue |
| `high` | 1 | Dispatched before normal and lower tasks |
| `normal` | 2 | Default priority for all tasks |
| `low` | 3 | Dispatched when no higher-priority tasks are waiting |
| `background` | 4 | Best-effort; dispatched only when queue is empty |

Within the same priority level, tasks dispatch in FIFO order
(submission timestamp).

### Queue Depth Limits

Implementations MUST enforce a maximum queue depth (default 10,000).
When the queue is full, new submissions are rejected with a
`queue_full` error and the submitter receives `task.failed`
immediately. Critical-priority tasks bypass the depth check.

---

## Dispatch Protocol

### HTTP Dispatch

Tasks are delivered to target agents via `POST /v1/execute`:

```
POST <target_agent_url>/v1/execute
Authorization: Bearer <dispatch_token>
X-Trace-Id: <trace_id>
Content-Type: application/json

{
  "id": "<task_id>",
  "action": "<action>",
  "payload": <input>,
  "context": {
    "trace_id": "<trace_id>",
    "correlation_id": "<correlation_id>",
    "services": { ... },
    "workspace_root": "<path>"
  }
}
```

### Response Handling

| Response | Action |
|----------|--------|
| 2xx + `status: "success"` | Publish `task.completed` with result |
| 2xx + `status: "failed"` | Publish `task.failed` with error summary |
| 429 (Rate Limited) | Re-queue task with `Retry-After` delay |
| 5xx / connection error | Retry per `patterns/retry` (exponential backoff) |
| No response within timeout | Publish `task.timeout` |

### Timeout Enforcement

Each task has an execution timeout (from submission or default 300s).
The timeout starts when the HTTP request is sent (dispatch time),
not when the task is queued. If the target agent does not respond
within the timeout, the task is marked `timeout` and
`task.timeout` is published.

---

## Concurrency Control

The dispatcher tracks in-flight tasks per target agent and gates
dispatch based on declared capacity.

### Capacity Model

```
capacity: map[agent_name] → int    (from agent manifest max_concurrent)
in_flight: map[agent_name] → int   (currently dispatched count)
queue: priority_queue[TaskSubmission]
```

### Dispatch Gate

```
if in_flight[target_agent] < capacity[target_agent]:
    dispatch immediately
else:
    enqueue (priority-ordered)

on task completion/failure/timeout:
    in_flight[target_agent] -= 1
    if queue has tasks for target_agent:
        dequeue and dispatch next
```

### Default Capacity

When an agent manifest does not declare `max_concurrent`, the
dispatcher applies defaults based on agent type:

| Agent Type | Default max_concurrent |
|------------|----------------------|
| Infrastructure | 20 |
| Domain controller | 10 |
| Work agent | 5 |

### Capacity Updates

Agent capacity is refreshed on:
- `system.agent.registered` — new or updated manifest received
- `system.agent.deregistered` — agent removed from dispatch pool

When an agent deregisters, all in-flight and queued tasks targeting
that agent are failed immediately with `agent_unavailable`.

---

## Task Status Lifecycle

Every task transitions through a defined set of states. Each
transition emits an event.

### States

| Status | Description |
|--------|-------------|
| `submitted` | Task received via `task.submit` event |
| `queued` | Task accepted and placed in priority queue |
| `dispatched` | HTTP request sent to target agent |
| `running` | Target agent acknowledged execution (optional) |
| `completed` | Target agent returned success |
| `failed` | Target agent returned failure or dispatch exhausted retries |
| `timeout` | Execution exceeded timeout |
| `cancelled` | Requester cancelled the task |
| `dead-letter` | Failed task captured after retry exhaustion |

### State Transitions

```yaml
state_machine:
  initial: submitted
  transitions:
    - from: submitted
      to: queued
      trigger: submission_accepted
      event: task.accepted
    - from: queued
      to: dispatched
      trigger: http_call_sent
      event: task.dispatched
    - from: dispatched
      to: completed
      trigger: success_response
      event: task.completed
    - from: dispatched
      to: failed
      trigger: error_response
      event: task.failed
    - from: dispatched
      to: timeout
      trigger: timeout_exceeded
      event: task.timeout
    - from: dispatched
      to: queued
      trigger: rate_limited
      event: none (internal re-queue)
    - from: queued
      to: cancelled
      trigger: cancel_event
      event: task.cancelled
    - from: dispatched
      to: cancelled
      trigger: cancel_event
      event: task.cancelled
    - from: queued
      to: failed
      trigger: agent_deregistered
      event: task.failed
    - from: failed
      to: dead-letter
      trigger: retry_exhausted
      event: task.dead-letter
```

---

## Dead-Letter Handling

Tasks that fail after exhausting all retries are captured in a
dead-letter store. Dead-lettered tasks are never silently dropped.

### Dead-Letter Entry

Each dead-letter entry preserves:

| Field | Type | Description |
|-------|------|-------------|
| task_id | string | Original task ID |
| target_agent | string | Agent the task was dispatched to |
| action | string | Action that was requested |
| original_submission | object | Full original TaskSubmission envelope |
| error | string | Final failure reason |
| attempts | int | Total dispatch attempts |
| first_attempt_at | int64 | Timestamp of first dispatch attempt |
| dead_lettered_at | int64 | Timestamp of dead-letter capture |
| trace_id | string | Trace context for correlation |

### Retention

Dead-letter entries are retained for a configurable period (default
7 days). Implementations MUST support:
- Listing dead-letter entries (filterable by agent, action, time range)
- Replaying a dead-letter entry (re-submit as new task)
- Purging entries older than retention period

---

## Types

```yaml
types:
  TaskSubmission:
    description: Envelope agents use to submit work for dispatch
    fields:
      task_id:
        type: string
        format: uuid-v7
        description: Unique task identifier (caller-generated)
      target_agent:
        type: string
        description: Name of the agent to dispatch to
      action:
        type: string
        description: Action name for the target agent
      input:
        type: object
        optional: true
        description: Payload delivered to the target agent
      priority:
        type: TaskPriority
        default: normal
        description: Dispatch priority level
      timeout:
        type: int
        default: 300
        unit: seconds
        description: Execution timeout
      trace_id:
        type: string
        description: Distributed trace context
      correlation_id:
        type: string
        optional: true
        description: Workflow correlation identifier
      workflow_id:
        type: string
        optional: true
        description: Parent workflow execution ID
      phase:
        type: string
        optional: true
        description: Workflow phase name

  TaskHandle:
    description: Async handle returned to the submitter on acceptance
    fields:
      task_id:
        type: string
        format: uuid-v7
        description: Task identifier for tracking
      status:
        type: TaskStatus
        description: Current task status (initially queued)
      position:
        type: int
        optional: true
        description: Queue position (if queued behind other tasks)
      accepted_at:
        type: int64
        description: Acceptance timestamp

  TaskResult:
    description: Completion or failure envelope after execution
    fields:
      task_id:
        type: string
        format: uuid-v7
        description: Task identifier
      status:
        type: string
        enum: [completed, failed, timeout]
        description: Terminal task status
      summary:
        type: text
        max: 1024
        optional: true
        description: Truncated result or error message
      output:
        type: object
        optional: true
        description: Full result payload (on success)
      duration_ms:
        type: int
        optional: true
        description: Execution duration in milliseconds
      timestamp:
        type: int64
        description: Completion timestamp

  TaskPriority:
    description: Priority levels controlling dispatch ordering
    enum:
      - critical
      - high
      - normal
      - low
      - background

  TaskStatus:
    description: Lifecycle states a task transitions through
    enum:
      - submitted
      - queued
      - dispatched
      - running
      - completed
      - failed
      - timeout
      - cancelled
      - dead-letter

  DeadLetterEntry:
    description: Captured failed task with full failure context
    fields:
      task_id:
        type: string
        format: uuid-v7
        description: Original task identifier
      target_agent:
        type: string
        description: Agent the task was dispatched to
      action:
        type: string
        description: Requested action
      original_submission:
        type: TaskSubmission
        description: Full original submission envelope
      error:
        type: text
        max: 2048
        description: Final failure reason
      attempts:
        type: int
        description: Total dispatch attempts
      first_attempt_at:
        type: int64
        description: Timestamp of first dispatch attempt
      dead_lettered_at:
        type: int64
        description: Timestamp of dead-letter capture
      trace_id:
        type: string
        description: Trace context for correlation

  AgentCapacity:
    description: Tracked concurrency capacity for a target agent
    fields:
      agent_name:
        type: string
        description: Agent identifier
      max_concurrent:
        type: int
        description: Maximum concurrent tasks (from manifest)
      in_flight:
        type: int
        default: 0
        description: Currently dispatched task count
      last_seen:
        type: int64
        description: Last registration or health timestamp
```

---

## Configuration

```yaml
config:
  default_timeout:
    type: int
    default: 300
    unit: seconds
    overridable: true
    min: 10
    max: 3600
    description: Default execution timeout when submission omits timeout
  default_priority:
    type: string
    default: normal
    overridable: false
    description: Priority assigned when submission omits priority
  max_queue_depth:
    type: int
    default: 10000
    overridable: true
    min: 100
    max: 1000000
    description: Maximum queued tasks before rejecting submissions
  max_retries:
    type: int
    default: 3
    overridable: true
    min: 0
    max: 10
    description: Maximum dispatch retry attempts on transient failure
  dead_letter_retention:
    type: int
    default: 604800
    unit: seconds
    overridable: true
    min: 3600
    max: 2592000
    description: Dead-letter entry retention period (default 7 days)
  default_capacity:
    type: int
    default: 5
    overridable: true
    min: 1
    max: 100
    description: Default max_concurrent when agent manifest omits it
```

---

## Error Handling

### Submission Errors

| Error | Code | Recovery |
|-------|------|----------|
| Unknown target agent | `agent_not_found` | Reject immediately, publish `task.failed` |
| Queue full | `queue_full` | Reject immediately, publish `task.failed` |
| Invalid envelope | `invalid_submission` | Reject immediately, publish `task.failed` |
| Missing required field | `validation_error` | Reject immediately, publish `task.failed` |

### Dispatch Errors

| Error | Code | Recovery |
|-------|------|----------|
| Connection refused | `dispatch_failed` | Retry per `patterns/retry` |
| 5xx response | `agent_error` | Retry per `patterns/retry` |
| 429 rate limited | `rate_limited` | Re-queue with `Retry-After` delay |
| Timeout exceeded | `timeout` | Publish `task.timeout`, no retry |
| Agent deregistered | `agent_unavailable` | Fail immediately, publish `task.failed` |
| Retries exhausted | `retries_exhausted` | Dead-letter the task |

### Error Events

All errors that affect task state produce events. Submitters MUST
subscribe to `task.failed`, `task.timeout`, and `task.dead-letter`
to handle failures in their workflow.

---

## Implementation Notes

- **Caller-generated IDs**: Submitters generate `task_id` (uuid-v7)
  before publishing `task.submit`. This enables idempotent
  submission — duplicate task IDs are detected and rejected.
- **Timeout starts at dispatch**: The execution timeout begins when
  the HTTP request is sent, not when the task enters the queue.
  Queue wait time is unbounded (within queue depth limits).
- **Re-queue on 429**: When a target agent returns 429, the task
  re-enters the queue with the `Retry-After` delay. This does NOT
  count as a retry attempt against `max_retries`.
- **Graceful drain**: On shutdown, the dispatcher stops accepting
  new tasks, waits for in-flight tasks to complete (up to 30s
  drain timeout), then fails remaining tasks.
- **State recovery**: On startup, tasks persisted as `queued` are
  re-queued. Tasks persisted as `dispatched` are marked `failed`
  (HTTP state cannot be recovered across restarts).
- **Capacity cache**: Agent capacity is cached from manifests
  received via `system.agent.registered`. The cache is rebuilt
  from the service directory on startup.
- **Trace propagation**: The `trace_id` from the submission envelope
  is forwarded to the target agent in the `X-Trace-Id` header and
  included in all published events for end-to-end correlation.
- **No payload in events**: Task events carry metadata (IDs, status,
  timestamps) but NOT the full input/output payload. Consumers
  that need payloads query the task record directly.
- **Idempotent completion**: If a `task.completed` or `task.failed`
  arrives for a task already in a terminal state, it is ignored.
  This prevents duplicate events from retry storms.

---

## Verification Checklist

- [ ] Tasks submitted via `task.submit` receive a `task.accepted` event with task ID and queue position
- [ ] Tasks are dispatched in priority order (critical > high > normal > low > background)
- [ ] Within the same priority, tasks dispatch in FIFO order
- [ ] Dispatch respects per-agent `max_concurrent` — excess tasks queue
- [ ] Queued tasks dispatch immediately when an in-flight slot opens
- [ ] Target agents receive `POST /v1/execute` with correct envelope format
- [ ] Successful execution produces `task.completed` with result
- [ ] Failed execution produces `task.failed` with error context
- [ ] Timeout enforcement publishes `task.timeout` after configured seconds
- [ ] 429 responses re-queue the task with `Retry-After` delay (not counted as retry)
- [ ] Transient failures (5xx, connection error) retry per `patterns/retry`
- [ ] Tasks failing after `max_retries` are dead-lettered with full context
- [ ] Dead-letter entries are queryable and replayable
- [ ] `task.cancelled` is published when a queued or in-flight task is cancelled
- [ ] Agent deregistration fails all in-flight and queued tasks for that agent
- [ ] Queue depth limit rejects new submissions when exceeded
- [ ] Duplicate `task_id` submissions are detected and rejected
- [ ] All events include `trace_id` for distributed tracing
- [ ] Events carry metadata only — no full payloads in event bodies
- [ ] Graceful shutdown drains in-flight tasks before exiting
