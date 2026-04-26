<!-- blueprint
type: agent
subtype: infrastructure
name: task
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, patterns/messaging, patterns/retry]
platform: any
tier: free
port: 9781
-->

# Task Agent

Infrastructure agent that owns task dispatch and tracking. Receives
`task.submit` events, dispatches work to target agents via
`POST /v1/execute`, tracks completion, and publishes `task.complete`
or `task.failed` back to the requester.

The Task Agent is the single dispatch point for all agent execution.
It handles priority queuing, concurrency awareness, timeout
enforcement, and dead-letter tracking for failed dispatches.

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

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| `task_dispatch_total` | counter | By target agent, action, and status |
| `task_dispatch_duration_seconds` | histogram | Time from submit to complete |
| `task_queue_depth` | gauge | Current queue depth per target agent |
| `task_inflight` | gauge | Currently dispatched tasks per agent |
| `task_timeout_total` | counter | Timed out tasks by agent |
| `task_retry_total` | counter | Dispatch retries by agent |

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
