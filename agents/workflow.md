<!-- blueprint
type: agent
subtype: infrastructure
name: workflow
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, patterns/messaging, patterns/workflow]
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

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| `workflow_execution_total` | counter | By workflow name and status |
| `workflow_execution_duration_seconds` | histogram | End-to-end duration |
| `workflow_phase_duration_seconds` | histogram | Per-phase by agent/action |
| `workflow_phase_total` | counter | Phase executions by status |
| `workflow_approval_wait_seconds` | histogram | Approval gate wait time |
| `workflow_inflight` | gauge | Currently executing workflows |

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
