<!-- blueprint
type: pattern
name: workflow
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/state-machine, patterns/messaging, patterns/observability]
platform: any
tier: free
-->

# Workflow Pattern

Standard workflow engine specification for multi-phase, multi-agent
task execution via event-driven coordination. Defines how workflows
are declared, how phases bind data, how execution proceeds through a
dependency graph, and how errors, approvals, and parallelism are
handled — all through HTTP-based pub/sub events.

**Key architectural principle:** Domains declare workflows. The
Workflow Agent executes them. The Task Agent dispatches individual
phases. All coordination happens via events — no synchronous proxy,
no embedded execution engine.

## Overview

A workflow is a directed acyclic graph (DAG) of phases. Each phase
targets an agent with resolved inputs, produces outputs, and feeds
those outputs to downstream phases. The workflow engine handles:

1. **Declaration** — YAML-based workflow definition with phases,
   triggers, and metadata (owned by domains)
2. **Data binding** — Reference expression syntax for wiring phase
   inputs to task data, prior outputs, entity context, and config
3. **Execution** — Event-driven DAG traversal via the Workflow Agent
4. **Dispatch** — Phase tasks submitted to the Task Agent via events
5. **Error strategies** — Per-phase fail/skip/retry semantics
6. **Approval gates** — Pause execution until human review
7. **State tracking** — Durable execution history with phase-level detail

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
        - name: TaskPayload
          fields_used: [action, payload, context]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/state-machine
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: StateMachineDefinition
          fields_used: [states, transitions, initial_state, entity_type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Event
          fields_used: [topic, scope, payload, correlation_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Metric
          fields_used: [name, type, labels, value]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Domains declare, agents execute** — Domains own workflow definitions (business logic); the Workflow Agent executes the DAG; the Task Agent dispatches individual phases.
2. **Event-driven coordination** — All coordination happens via HTTP-based pub/sub events; no synchronous proxy or embedded execution engine.
3. **Fail-safe by default** — Each phase declares its own error strategy (fail/skip/retry); the default is fail, which stops the workflow to prevent silent corruption.
4. **Durable execution** — Workflow executions persist to durable storage with phase-level detail, enabling recovery from agent crashes and full audit trails.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: workflow-execution
      description: Event-driven DAG execution with phase dispatch and result aggregation
      parameters:
        - name: workflow_name
          type: string
          required: true
          description: Identifier of the workflow to execute
        - name: timeout
          type: int
          required: false
          description: Workflow-level timeout in seconds (default 600)
      inherits: DAG resolution, phase dispatch, result aggregation, and state tracking
      overridable: true
      override_constraints: Must use event-driven coordination; cannot bypass Task Agent
    - name: phase-dispatch
      description: Submit individual workflow phases to target agents via task events
      parameters:
        - name: agent
          type: string
          required: true
          description: Target agent name or self
        - name: action
          type: string
          required: true
          description: Task action to invoke on the target agent
        - name: on_error
          type: enum(fail, skip, retry)
          required: false
          description: Error strategy for this phase (default fail)
      inherits: Task submission, timeout enforcement, and error strategy application
      overridable: true
      override_constraints: Must respect phase-level timeout and on_error strategy
    - name: approval-gate
      description: Pause workflow execution until human approval is received
      parameters:
        - name: approval
          type: enum(required, auto)
          required: false
          description: Whether phase output requires human review
      inherits: Approval event publishing and decision handling
      overridable: true
      override_constraints: Approval timeout falls back to workflow-level timeout
  types:
    - name: WorkflowDefinition
      description: Workflow declaration with phases, triggers, and metadata
      inherited_by: Workflow Types section
    - name: WorkflowPhase
      description: Individual phase with agent, action, input bindings, and error strategy
      inherited_by: Workflow Types section
    - name: WorkflowExecution
      description: Durable execution record with status, phases, and timing
      inherited_by: Workflow Types section
    - name: PhaseResult
      description: Per-phase execution result with status, output, and error
      inherited_by: Workflow Types section
  endpoints:
    - path: /v1/message
      description: Direct message dispatch for self-targeted phases
      inherited_by: Execution Engine section
  events:
    - topic: workflow.trigger
      description: External agent requests workflow execution
      payload: {workflow, source_domain, input, callback_topic, entity, config}
    - topic: workflow.started
      description: Workflow execution has begun
      payload: {execution_id, workflow_name, invoker, timestamp}
    - topic: workflow.completed
      description: All workflow phases finished
      payload: {execution_id, workflow_name, status, summary, phase_results}
    - topic: workflow.failed
      description: Workflow execution failed
      payload: {execution_id, workflow_name, failed_phase, error, timestamp}
    - topic: workflow.approval.required
      description: Phase output pending human approval
      payload: {workflow_id, phase, output_preview}
    - topic: workflow.approval.decision
      description: Human approved or rejected a phase
      payload: {workflow_id, phase, decision, reason}
```

---

## Workflow Declaration

Workflows are declared in domain blueprint files (in `domains/`).
Domains own the business logic and define what work needs to happen.
The Workflow Agent reads these definitions and executes the DAG.

```yaml
workflows:
  <workflow-name>:
    description: <one-line purpose>
    trigger: <action-name>           # maps to event topic or task action
    timeout: <seconds>               # workflow-level timeout (default: 600)
    approval: required | auto        # workflow-level default (default: auto)

    phases:
      - name: <phase-name>
        agent: <agent-name> | self
        action: <action-name>
        input:
          <key>: <value | $reference>
        output: <output-key>
        depends_on: [<phase-names>]  # optional
        timeout: <seconds>           # phase-level (default: 300)
        approval: required | auto    # phase-level override
        on_error: fail | skip | retry
        max_retries: <int>           # when on_error = retry (default: 0)
        condition: <expression>      # skip phase if falsy
```

### Declaration Fields

| Field | Level | Required | Default | Description |
|-------|-------|----------|---------|-------------|
| description | workflow | yes | — | Human-readable purpose |
| trigger | workflow | yes | — | Action name that invokes this workflow |
| timeout | workflow | no | 600 | Max seconds for entire workflow |
| approval | workflow | no | auto | Default approval mode for phases |
| phases | workflow | yes | — | Ordered list of phase declarations |
| name | phase | yes | — | Unique identifier within workflow |
| agent | phase | yes | — | Target agent name, or `self` for caller |
| action | phase | yes | — | Task action to invoke on target agent |
| input | phase | yes | — | Map of input keys to values or references |
| output | phase | yes | — | Key name for storing phase result |
| depends_on | phase | no | [] | Phase names that must complete first |
| timeout | phase | no | 300 | Max seconds for this phase |
| approval | phase | no | workflow default | Phase-specific approval override |
| on_error | phase | no | fail | Error strategy: fail / skip / retry |
| max_retries | phase | no | 0 | Retry attempts when on_error = retry |
| condition | phase | no | — | Expression; phase skipped if falsy |

---

## Reference Expression Syntax

Phase inputs use reference expressions to bind data from the trigger
payload, prior phase outputs, entity context, or configuration.

### Grammar

```
expression   = "$" root "." path
root         = "task" | "phases" | "entity" | "config"
path         = segment ( "." segment )*
segment      = identifier | identifier "[" index "]" | identifier "[*]"
identifier   = [a-z_][a-z0-9_]*
index        = non-negative integer
```

### Roots

| Root | Resolves To |
|------|-------------|
| `$task.payload.<key>` | Field from the original trigger payload |
| `$task.context.<key>` | Field from the trigger context |
| `$phases.<name>.output` | Full output map of a completed phase |
| `$phases.<name>.output.<key>` | Specific key from a phase's output |
| `$entity.<key>` | Field from EntityContext (injected via context) |
| `$config.<key>` | Domain-specific configuration value |

### Nested Path Access

Dot-separated segments traverse nested maps:

```
$phases.scan.output.files         → full "files" value
$phases.scan.output.summary.score → nested key "score" inside "summary"
```

### Array Indexing

Bracket notation accesses array elements:

```
$phases.scan.output.files[0]      → first element
$phases.scan.output.files[2]      → third element
```

Index out of bounds resolves to `null`.

### Array Expansion

The `[*]` wildcard collects a nested field from every array element:

```
$phases.scan.output.files[*].metadata.images
```

Produces a flat array of all `metadata.images` values across all
elements in the `files` array. If the source is not an array,
resolves to `null`.

### Resolution Rules

1. Expressions MUST start with `$` — literal strings without `$`
   are passed through as-is
2. Unresolvable references resolve to `null` (not an error)
3. If a required input resolves to `null`, the engine MUST fail the
   phase with error: `"unresolved reference: <expression>"`
4. No type coercion — resolved JSON values pass as-is
5. Circular references are impossible by construction (`depends_on`
   creates a DAG)

### Examples

```yaml
input:
  mode: "full"                                  # literal
  html_files: $task.payload.files               # trigger payload
  metadata: $phases.scan.output.files           # phase output
  first_file: $phases.scan.output.files[0]      # array index
  all_images: $phases.scan.output.files[*].metadata.images  # expansion
  brand_tone: $entity.tone                      # entity context
  max_issues: $config.max_issues_per_file       # configuration
```

---

## Execution Engine (Event-Driven)

The Workflow Agent owns the execution engine. It receives workflow
trigger events, resolves the DAG, and coordinates phase execution
through the Task Agent — all via HTTP-based pub/sub events.

### Phase 1 — Trigger

An agent (typically a domain controller) publishes a workflow trigger:

```
publish("workflow.trigger", {
  workflow: "seo-audit",
  source_domain: "seo",
  input: { files: ["index.html", "about.html"] },
  callback_topic: "seo.audit.result",
  entity: { ... },
  config: { max_issues_per_file: 10 }
}, scope: "workflow", correlation_id: "corr-001")
```

The Workflow Agent (subscribed to `workflow.trigger`, scope `self`)
receives this event.

### Phase 2 — Resolve Definition

The Workflow Agent fetches the workflow definition from the source
domain:

```
POST /v1/message to "seo":
  action: "get_workflow"
  payload: { name: "seo-audit" }
→ Response: workflow YAML definition
```

The Workflow Agent caches definitions per domain. Cache is invalidated
when `system.agent.registered` events indicate the domain has
re-registered (possible definition change).

### Phase 3 — Initialize Execution

Create a `WorkflowExecution` record (persisted to flat-file storage):

```yaml
execution:
  id: <generated-uuid>
  workflow_name: seo-audit
  invoker: seo
  correlation_id: corr-001
  trace_id: <from event>
  callback_topic: seo.audit.result
  status: running
  started_at: <now>
  phases: []
  input: { files: ["index.html", "about.html"] }
  entity: { ... }
  config: { max_issues_per_file: 10 }
```

Publish: `workflow.started` (scope: invoker)

### Phase 4 — Resolve Execution Order

Topological sort of phases by `depends_on`:

```
1. Build adjacency graph from depends_on declarations
2. Detect cycles → fail with "circular dependency: [phase names]"
3. Group into execution levels:
   L0: phases with no depends_on
   L1: phases depending only on L0
   L2: phases depending on L0 or L1
   ...
4. Validate all depends_on references exist in this workflow
```

### Phase 5 — Execute Levels (Event-Driven)

For each level, dispatch all phases concurrently via events:

```
for each phase in current level (concurrent):
  a. Check condition — if set and falsy, mark phase "skipped"
     Publish: workflow.phase.skipped

  b. Resolve input references from trigger payload + prior outputs

  c. If agent = "self":
       POST /v1/message to invoker domain:
         action: phase.action
         payload: resolved_input
       Store result as phase output
     Else:
       Publish event: task.submit
         scope: "task"
         correlation_id: execution.correlation_id
         payload: {
           task_id: <generated>,
           workflow_id: execution.id,
           phase: phase.name,
           target_agent: phase.agent,
           action: phase.action,
           input: resolved_input,
           timeout: phase.timeout,
           trace_id: execution.trace_id
         }

  d. Workflow Agent waits for corresponding task.complete or
     task.failed event (matched by workflow_id + phase name)
```

The Workflow Agent subscribes to `task.complete` and `task.failed`
(scope: `self`). When a task completion event arrives:

```
1. Match event to in-flight workflow execution via workflow_id + phase
2. Store PhaseResult: phase_name, agent_name, status, output,
   started_at, completed_at
3. If failed → apply on_error strategy (see Error Strategies)
4. Check: are all phases in current level done?
   If yes → advance to next level:
     a. Resolve input references for next-level phases
        (now including $phases.<prior>.output references)
     b. Publish task.submit for each ready phase
5. Check: are ALL levels done?
   If yes → go to Phase 6 (Aggregate)
```

### Phase 6 — Aggregate

```
Collect all phase results.
Build aggregated result:
  workflow_name, invoker, status (success/failed/pending_approval),
  summary, phase results, merged observations, merged recommendations,
  metrics (phases_total, completed, failed, skipped, duration_ms)

Publish: workflow.completed (scope: invoker)
  payload: aggregated result

If callback_topic set:
  Publish result to callback_topic (scope: invoker)

Store final WorkflowExecution record.
```

### Phase 7 — Record

```
Persist completed WorkflowExecution with all phase results.
Lifecycle Agent (subscribed to workflow.completed, scope: "*")
  stores observations and recommendations from the result.
```

---

## Error Strategies

Each phase declares its own error strategy via `on_error`:

| Strategy | Behavior |
|----------|----------|
| `fail` | Phase fails → entire workflow fails immediately. Default. |
| `skip` | Phase marked `skipped`. Dependents proceed without its output. |
| `retry` | Retry up to `max_retries` with exponential backoff. After exhaustion, treat as `fail`. |

### Error Propagation

When a phase fails with `on_error: fail`:
1. Cancel all in-flight tasks at the same level
   (publish `task.cancel` for pending tasks)
2. Skip all downstream phases
3. Set workflow status to `failed`
4. Publish `workflow.failed` (scope: invoker)
5. Return partial results from completed phases

When a phase fails with `on_error: skip`:
1. Mark the phase as `skipped` with the error message
2. Publish `workflow.phase.skipped`
3. Downstream phases that reference this phase's output receive `null`
4. Workflow continues

When a phase fails with `on_error: retry`:
1. Re-submit via `task.submit` (same phase, incremented retry count)
2. Apply exponential backoff: 1s, 2s, 4s (base × 2^attempt)
3. After `max_retries` exhausted → treat as `fail`

---

## Approval Gates

Phases with `approval: required` pause execution:

```
1. Phase executes normally and produces output
2. Phase output stored but NOT exposed to downstream phases yet
3. Workflow status → "pending_approval"
4. Publish: workflow.approval.required
   scope: invoker
   payload: { phase, output_preview, workflow_id }
5. Lifecycle Agent (subscribed, scope: "*") records pending approval
6. Wait for workflow.approval.decision event:
   payload: { workflow_id, phase, decision: "accept" | "reject", reason }
7. On accept → expose output to downstream phases, resume workflow
8. On reject → mark phase failed, apply on_error strategy
```

Approval timeout: if no decision within the workflow timeout, the
workflow fails with `"approval_timeout"`.

---

## Workflow State Machine

Every workflow execution follows this state machine:

```yaml
state_machines:
  workflow_execution:
    initial_state: pending
    entity_type: WorkflowExecution
    state_field: status

    states:
      pending:
        description: Workflow created, not yet executing
      running:
        description: Phases are executing
      pending_approval:
        description: Waiting for human approval on a phase
      completed:
        description: All phases finished successfully
        terminal: true
      failed:
        description: Workflow failed
        terminal: true

    transitions:
      - name: start
        from: pending
        to: running
        trigger: workflow.started event published
      - name: pause_for_approval
        from: running
        to: pending_approval
        trigger: workflow.approval.required event published
      - name: resume
        from: pending_approval
        to: running
        trigger: workflow.approval.decision (accept) event received
      - name: complete
        from: running
        to: completed
        trigger: all phases done, workflow.completed event published
      - name: fail
        from: [running, pending_approval]
        to: failed
        trigger: phase failed (fail strategy) | timeout | approval rejected
```

---

## Event Topics

The Workflow Agent owns the `workflow.*` namespace. These are the
standard events in the workflow lifecycle:

| Topic | Scope | Published When |
|-------|-------|----------------|
| `workflow.trigger` | `workflow` | External agent requests a workflow |
| `workflow.started` | invoker | Workflow execution begins |
| `workflow.phase.ready` | `task` | Phase inputs resolved, submitted for dispatch |
| `workflow.phase.complete` | invoker | Phase finished successfully |
| `workflow.phase.failed` | invoker | Phase errored |
| `workflow.phase.skipped` | invoker | Phase skipped (condition or error) |
| `workflow.approval.required` | invoker | Phase output pending approval |
| `workflow.approval.decision` | `workflow` | Human approved/rejected |
| `workflow.completed` | invoker | All phases done |
| `workflow.failed` | invoker | Workflow failed |

---

## Workflow Types

These types are the canonical definitions for workflow state.
Referenced from `protocol/types.md`.

### WorkflowDefinition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Workflow identifier (lowercase, hyphens) |
| description | string | yes | What this workflow does |
| trigger | string | yes | Action name that invokes this workflow |
| timeout | int | no | Workflow-level timeout in seconds (default: 600) |
| phases | []WorkflowPhase | yes | Ordered execution steps |

### WorkflowPhase

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Phase identifier (unique within workflow) |
| agent | string | yes | Target agent or `self` |
| action | string | yes | Task action to invoke |
| input | map | no | Input mapping with reference expressions |
| output | string | no | Key name for storing phase result |
| depends_on | []string | no | Phases that must complete first |
| timeout | int | no | Phase timeout in seconds (default: 300) |
| approval | string | no | `required` or `auto` (default: `auto`) |
| on_error | string | no | `fail`, `skip`, or `retry` (default: `fail`) |
| max_retries | int | no | Retry count when on_error = retry (default: 0) |
| condition | string | no | Expression; phase skipped if falsy |

### WorkflowExecution

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique execution identifier |
| workflow_name | string | yes | Which workflow is executing |
| invoker | string | yes | Agent that triggered the workflow |
| correlation_id | string | yes | Links all events in this execution |
| trace_id | string | no | Distributed trace context |
| callback_topic | string | no | Topic for result delivery |
| status | string | yes | pending / running / pending_approval / completed / failed |
| phases | []PhaseResult | yes | Results per phase |
| started_at | int64 | yes | Unix epoch seconds |
| completed_at | int64 | no | Unix epoch seconds |

### PhaseResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| phase_name | string | yes | Phase identifier |
| agent_name | string | yes | Agent that executed this phase |
| status | string | yes | pending / running / completed / failed / skipped |
| output | map | no | Phase output data |
| started_at | int64 | no | Unix epoch seconds |
| completed_at | int64 | no | Unix epoch seconds |
| error | string | no | Error message if failed |
| retries | int | no | Number of retry attempts |

---

## Observability

Workflows emit these metrics (in addition to base agent metrics
from patterns/observability):

| Metric | Type | Description |
|--------|------|-------------|
| workflow_execution_total | counter | Executions by workflow name and status |
| workflow_execution_duration_seconds | histogram | End-to-end workflow duration |
| workflow_phase_duration_seconds | histogram | Per-phase duration by agent and action |
| workflow_phase_total | counter | Phase executions by status |
| workflow_approval_wait_seconds | histogram | Time spent waiting for approval |
| workflow_parallel_phases | gauge | Current parallel phase count |

---

## Implementation Notes

- Phases within a level MUST dispatch concurrently. Sequential
  dispatch within a level is a conformance violation.
- The Workflow Agent MUST enforce the workflow-level timeout.
  When exceeded, cancel all in-flight tasks and fail the workflow.
- Phase timeouts are independent of workflow timeout. A phase can
  time out before the workflow does.
- The `self` agent target dispatches via `POST /v1/message` to the
  invoker domain — no task.submit event needed.
- Workflow executions MUST be persisted to durable storage (flat-file
  JSONL+ZSTD by default). If the Workflow Agent crashes mid-execution,
  the record shows which phases completed and enables recovery.
- The trace_id from the trigger event MUST be propagated to all
  task.submit events and downstream calls for distributed tracing.
- The Workflow Agent SHOULD cache workflow definitions fetched from
  domains. Cache invalidation occurs on `system.agent.registered`
  events for the source domain.

---

## Verification Checklist

- [ ] Workflows declared in YAML with required fields
- [ ] Reference expressions resolve correctly from all four roots
- [ ] Array indexing and expansion produce correct results
- [ ] Unresolvable references return null (not errors)
- [ ] Workflow Agent receives workflow.trigger events and resolves DAG
- [ ] Phase dispatch via task.submit events to Task Agent
- [ ] Task completion matched to workflow phase via workflow_id + phase name
- [ ] DAG levels advance when all phases in a level complete
- [ ] Independent phases within a level dispatch concurrently
- [ ] on_error: fail stops the entire workflow
- [ ] on_error: skip marks phase skipped, dependents receive null
- [ ] on_error: retry re-submits via task.submit with backoff
- [ ] approval: required pauses workflow, publishes workflow.approval.required
- [ ] Approval decision resumes or rejects via workflow.approval.decision
- [ ] Workflow-level timeout cancels in-flight tasks
- [ ] Phase-level timeout cancels individual phase
- [ ] Circular dependency detection fails the workflow at init
- [ ] WorkflowExecution records persist to durable storage
- [ ] workflow.completed published with scope = invoker
- [ ] callback_topic receives result if specified
- [ ] Metrics emit for all workflow and phase executions
- [ ] trace_id and correlation_id propagate through all events
