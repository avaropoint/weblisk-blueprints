<!-- blueprint
type: pattern
name: workflow
version: 4.0.1
requires: [protocol/types, patterns/storage, patterns/state-machine, patterns/messaging, patterns/observability, patterns/expression]
platform: any
tier: free
-->

# Workflow Pattern

Standard workflow engine specification for multi-phase, multi-agent
task execution via event-driven coordination. Defines how workflows
are declared, how phases bind data, how execution proceeds through a
dependency graph, and how errors, approvals, and parallelism are
handled — all through HTTP-based pub/sub events.

**Key architectural principle:** Owners declare workflows. The
executor runs them and dispatches their phases. A step that waits for a
person is decided by a person, at the executor, and by nothing else.

**The executor is [`architecture/execution`](../architecture/execution.md)**:
cron, task and workflow merged into one service, with one run ledger. Where
this pattern says the executor, that is the service it means. Before
execution existed, the executor was two agents, and
[`agents/workflow`](../agents/workflow.md) and
[`agents/task`](../agents/task.md) still describe that interim form, in which
the engine hands each phase to the dispatcher as a `task.submit` event. An
executor that holds the engine and the dispatcher in one service dispatches
directly, under the same capacity, timeout and dead-letter rules.

## Overview

A workflow is a directed acyclic graph (DAG) of phases. Each phase
targets an agent with resolved inputs, produces outputs, and feeds
those outputs to downstream phases. The workflow engine handles:

1. **Declaration** — YAML-based workflow definition with phases,
   triggers, and metadata (owned by domains)
2. **Data binding** — Reference expression syntax for wiring phase
   inputs to task data, prior outputs, entity context, and config
3. **Execution** — DAG traversal by the executor
4. **Dispatch** — Each machine phase sent to its target by the executor's dispatcher
5. **Error strategies** — Per-phase fail/skip/retry semantics
6. **Approval gates** — Pause execution until human review
7. **A person's phase** — A task or an approval, by position, that waits
   for a person and is decided only by one
8. **State tracking** — Durable execution history with phase-level detail

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, detail]
        - name: TaskRequest
          fields_used: [action, payload, context]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/storage
    version: ">=1.0.0 <3.0.0"
    bindings:
      types:
        - name: TypeDefinition
          fields_used: [name, fields, description]
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
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        - name: EventEnvelope
          fields_used: [topic, scope, payload, correlation_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/observability
    version: ">=1.0.0 <3.0.0"
    bindings:
      types:
        - name: MetricsSnapshot
          fields_used: [requests_total, errors_total, last_activity]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/expression
    version: ">=1.0.0 <3.0.0"
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

1. **Owners declare, the executor executes** — Owners (domains, the programme service) own workflow definitions (business logic); the executor runs the DAG and dispatches its phases.
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
      override_constraints: Cannot bypass the dispatcher's capacity, timeout and dead-letter rules
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
      inherits: Approval event publishing, and a decision taken only at the executor's decision route from a person
      overridable: true
      override_constraints: A decision is never taken from an event, an action or a phase's output
    - name: person-phase
      description: Hold a task or approval phase as a wait, awaiting the positions it names, until a person holding one decides it
      parameters:
        - name: task
          type: WorkflowTask
          required: false
          description: A person's work, by responsible position, with its due
        - name: approvers
          type: "[]string"
          required: false
          description: The positions whose holders must each accept
        - name: approval_order
          type: enum(sequential)
          required: false
          description: Ask the approvers one at a time, in declared order
        - name: escalate
          type: WorkflowEscalation
          required: false
          description: The position a wait left open becomes the problem of
      inherits: Wait opening, holder resolution, decision recording, escalation and audit
      overridable: false
      override_constraints: Only a person holding an awaited position decides; no machine closes a wait
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
    - name: WorkflowTask
      description: A person's work on a phase, by position, with its due
      inherited_by: Workflow Types section
    - name: WorkflowEscalation
      description: Where a person's phase left open goes, and after how long
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
      description: A person decided a phase at the executor. A record of the decision, published by the executor, and never a way to make one
      payload: {workflow_id, phase, decision, reason}
```

---

## Workflow Declaration

Workflows are declared by their owner: a domain blueprint (in `domains/`),
or a programme map, which the programme service installs as definitions
([`schemas/programme`](../schemas/programme.md#how-a-workflow-maps-onto-patternsworkflow)).
The owner defines what work needs to happen. The executor fetches each
definition from its owner and runs the DAG.

```yaml
workflows:
  <workflow-name>:
    description: <one-line purpose>
    trigger: <action-name>           # maps to event topic or task action
    timeout: <seconds>               # workflow-level timeout (default: 600)
    approval: required | auto        # workflow-level default (default: auto)

    phases:
      - name: <phase-name>
        agent: <agent-name> | self   # a machine phase: agent and action
        action: <action-name>
        task:                        # or a person's work (A Person's Phase)
          activity: <what is done>
          responsible: <position>
          due: <n><h|d|w>
        approvers: [<position>, ...] # or a person's decision
        approval_order: sequential   # optional, with approvers
        escalate: {after: <n><h|d|w>, to: <position>}  # optional, on a person's phase
        input:
          <key>: <value | $reference>
        output: <output-key>
        depends_on: [<phase-names>]  # optional
        timeout: <seconds>           # phase-level (default: 300)
        approval: required | auto    # phase-level override
        on_error: fail | skip | retry
        max_attempts: <int>           # when on_error = retry (default: 3)
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
| agent | phase | conditional | — | Target agent name, or `self` for caller. Required on a machine phase; absent on a person's |
| action | phase | conditional | — | Task action to invoke on target agent. Required with `agent` |
| task | phase | conditional | — | A person's work: `activity`, `responsible` position and `due` ([A Person's Phase](#a-persons-phase)) |
| approvers | phase | conditional | — | The positions whose holders must each accept ([A Person's Phase](#a-persons-phase)) |
| approval_order | phase | no | — | `sequential`; only with `approvers` |
| escalate | phase | no | — | `after` and `to`, on a phase with `task` or `approvers` |
| input | phase | no | — | Map of input keys to values or references |
| output | phase | no | — | Key name for storing phase result (omit if result not referenced)(omit if result not referenced) |
| depends_on | phase | no | [] | Phase names that must complete first |
| timeout | phase | no | 300 | Max seconds for this phase |
| approval | phase | no | workflow default | Phase-specific approval override |
| on_error | phase | no | fail | Error strategy: fail / skip / retry |
| max_attempts | phase | no | 3 | Total attempts when on_error = retry, the first included (`protocol/conventions:max-attempts`) |
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

The executor owns the execution engine. It receives workflow
trigger events, resolves the DAG, and dispatches each phase.

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

The executor (subscribed to `workflow.trigger`, scope `self`)
receives this event.

### Phase 2 — Resolve Definition

The executor fetches the workflow definition from the source
domain:

```
POST /v1/message to "seo":
  action: "get_workflow"
  payload: { name: "seo-audit" }
→ Response: workflow YAML definition
```

The executor caches definitions per domain. Cache is invalidated
on the domain's `system.agent.registered` event, which the orchestrator
publishes when the domain starts or its manifest changes, and not on a token
renewal (architecture/orchestrator, Registration Flow step 10). A deployment that changes a domain's workflow
definitions changes its manifest `version`, so its registration publishes.

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

  c. If the phase has task or approvers:
       Open a wait (A Person's Phase); the phase dispatches nothing
     Else if agent = "self":
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
           timeout: phase.timeout
         }
         (the event envelope carries the trace:
          protocol/spec#trace-propagation)

  d. The executor waits for corresponding task.completed or
     task.failed event (matched by workflow_id + phase name)
```

The executor subscribes to `task.completed` and `task.failed`
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

In the interim two-agent form the engine publishes `task.submit` and waits
for `task.completed` or `task.failed`, as above. An executor that holds its
dispatcher sends the same request to the target's `POST /v1/execute` itself,
and records the result on the phase, with no event between them.

### Phase 6 — Aggregate

```
Collect all phase results.
Build aggregated result:
  workflow_name, invoker, status (completed/failed),
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
| `retry` | Retry up to `max_attempts` with exponential backoff. After exhaustion, treat as `fail`. |

### Error Propagation

When a phase fails with `on_error: fail`:
1. Cancel all in-flight tasks at the same level
   (publish `task.cancel`, the request the task agent subscribes to, for
   pending tasks; the task agent answers each with `task.cancelled`, as
   `patterns/task-dispatch` declares)
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
1. Re-submit via `task.submit` (same phase, `attempts` incremented)
2. Wait as `protocol/conventions:backoff` says
3. After `max_attempts` exhausted → treat as `fail`

---

## Approval Gates

A machine phase with `approval: required` pauses the run after it has
produced its output:

```
1. Phase executes normally and produces output
2. Phase output stored but NOT exposed to downstream phases yet
3. A wait opens for the phase (A Person's Phase), awaiting its approvers,
   or any person holding the executor's decide capability where it names none
4. Workflow status → "waiting"
5. Publish: workflow.approval.required
   scope: invoker
   payload: { phase, output_preview, workflow_id }
6. A person decides at the executor's decision route, on their own pass
7. On accept → expose output to downstream phases, resume workflow
8. On reject → mark phase failed, apply on_error strategy
9. Publish: workflow.approval.decision, as the record of what the person decided
```

**A decision is taken only at the executor's decision route, from a person.**
The executor MUST NOT take a decision from an event, an action, a phase's
output or any token a service may hold. `workflow.approval.decision` is
published by the executor after a person has decided, and the executor
subscribes to no topic that would decide a phase. An executor that took the
event as the decision would let any publisher on the bus approve work.

Time a run spends waiting for a person counts towards no phase or workflow
`timeout`. A wait ends by a decision, by the run being cancelled, or by the
run failing.

---

## A Person's Phase

A phase may be a person's, not a machine's. It names no `agent` and no
`action`; it dispatches nothing; it opens a **wait** that only a person
closes. There are two:

| phase | written as | a person | closes it by |
|---|---|---|---|
| a task | `task: {activity, responsible, due}` | a holder of `responsible` | `complete`, or `decline` |
| an approval | `approvers: [<position>, ...]`, and `approval_order: sequential` or omitted | a holder of each named position, one person to a position | `accept` from every position, or `reject` from any |

A phase carries exactly one of `agent`, `task` and `approvers`. `approval:
required` on a machine phase is the [approval gate](#approval-gates), and
may name `approvers` beside its `agent` to say whose decision the gate waits
for.

**Positions, never people.** `responsible`, `approvers` and `escalate.to`
name positions, as a programme names them
([`schemas/programme`](../schemas/programme.md#the-rules-that-are-load-bearing)).
Whether a person holds one is the tenant's register of position holders,
read when the wait opens and again at each decision
([`schemas/position`](../schemas/position.md#known-gaps)). An executor that
cannot read it decides nothing on that wait, and says so; it never decides
by capability alone a wait that names a position.

**Order.** With `approval_order: sequential`, the approvers are asked one
at a time, in declared order, and a decision as a later position before an
earlier one has accepted is refused. Omitted, they may decide in any order.

**The due.** A task's `due` is `<n><h|d|w>` from the moment the wait opens.
Past it, the wait stays open; a due is what escalation is measured from,
never a timeout that fails the phase.

**Escalation.** `escalate: {after, to}` — `after` in
[`schemas/programme`](../schemas/programme.md#escalateafter--how-long-past-due)'s
closed form — fires once, `after` past a task's `due`, or past an
approval's opening, which has no due. It adds `to` as a position whose
holder may decide in place of the one still awaited (in a sequential
approval the current one, otherwise the first still awaited in declared
order). The awaited positions may still decide.

**Separation of duties.** An approval is not accepted by the person who
started the run, nor by one who completed a task the approval follows
([`patterns/approval`](approval.md#separation-of-duties)).

**Outcomes.** `complete` and `accept` complete the phase. `decline` and
`reject` fail it, and its `on_error` applies. The decision is recorded on the
run with who decided, as which position, and why.

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
      waiting:
        description: A person's phase or an approval gate is open, and no phase is running
      completed:
        description: All phases finished successfully
        terminal: true
      failed:
        description: Workflow failed
        terminal: true
      cancelled:
        description: Stopped by a person or by the definition's owner; open waits closed
        terminal: true
      withheld:
        description: Stopped at its first person's phase because its run may reach nobody (the executor says when, as architecture/execution's muted runs do)
        terminal: true

    transitions:
      - name: start
        from: pending
        to: running
        trigger: workflow.started event published
      - name: wait
        from: running
        to: waiting
        trigger: a wait opened and no phase is running
      - name: resume
        from: waiting
        to: running
        trigger: a person decided a wait at the executor's decision route, and a phase can run
      - name: complete
        from: running
        to: completed
        trigger: all phases done, workflow.completed event published
      - name: fail
        from: [running, waiting]
        to: failed
        trigger: phase failed (fail strategy) | timeout | approval rejected | task declined
      - name: cancel
        from: [pending, running, waiting]
        to: cancelled
        trigger: cancelled at the executor
      - name: retry
        from: failed
        to: running
        trigger: retried at the executor, from the phases that failed
      - name: withhold
        from: running
        to: withheld
        trigger: a person's phase opened in a run that may reach nobody
```

---

## Event Topics

The executor owns the `workflow.*` namespace. These are the
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
| `workflow.approval.decision` | invoker | A person decided at the executor; a record, never a decision |
| `workflow.completed` | invoker | All phases done |
| `workflow.failed` | invoker | Workflow failed |

---

## Workflow Types

These types are the canonical definitions for workflow state.
Referenced from `protocol/types.md`.

### WorkflowDefinition

```yaml
types:
  WorkflowDefinition:
    fields:
      name:
        type: string
        required: true
        description: "Workflow identifier (lowercase, hyphens)"
      description:
        type: string
        required: true
        description: "What this workflow does"
      trigger:
        type: string
        required: true
        description: "Action name that invokes this workflow"
      timeout:
        type: int
        required: false
        description: "Workflow-level timeout in seconds (default: 600)"
      phases:
        type: "[]WorkflowPhase"
        required: true
        description: "Ordered execution steps"
```

### WorkflowPhase

```yaml
types:
  WorkflowPhase:
    fields:
      name:
        type: string
        required: true
        description: "Phase identifier (unique within workflow)"
      agent:
        type: string
        required: false
        description: "Target agent or `self`. Required on a machine phase; absent on a person's"
      action:
        type: string
        required: false
        description: "Task action to invoke. Required with `agent`"
      task:
        type: WorkflowTask
        required: false
        description: "A person's work. Exclusive with `agent` and `approvers`"
      approvers:
        type: "[]string"
        required: false
        description: "Positions whose holders must each accept. Exclusive with `task`; beside `agent` only with `approval: required`"
      approval_order:
        type: string
        required: false
        description: "`sequential`, or absent for any order. Only with `approvers`"
      escalate:
        type: WorkflowEscalation
        required: false
        description: "Only on a phase with `task` or `approvers`"
      input:
        type: map
        required: false
        description: "Input mapping with reference expressions"
      output:
        type: string
        required: false
        description: "Key name for storing phase result"
      depends_on:
        type: "[]string"
        required: false
        description: "Phases that must complete first"
      timeout:
        type: int
        required: false
        description: "Phase timeout in seconds (default: 300)"
      approval:
        type: string
        required: false
        description: "`required` or `auto` (default: `auto`)"
      on_error:
        type: string
        required: false
        description: "`fail`, `skip`, or `retry` (default: `fail`)"
      max_attempts:
        type: int
        required: false
        description: Total attempts, the first included (protocol/conventions:max-attempts)
      condition:
        type: string
        required: false
        description: "Expression evaluated per [patterns/expression](expression.md) (Workflow Phase Context); phase skipped if falsy"
```

### WorkflowExecution

```yaml
types:
  WorkflowExecution:
    fields:
      id:
        type: string
        required: true
        description: "Unique execution identifier"
      workflow_name:
        type: string
        required: true
        description: "Which workflow is executing"
      invoker:
        type: string
        required: true
        description: "Agent that triggered the workflow"
      correlation_id:
        type: string
        required: true
        description: "Links all events in this execution"
      trace_id:
        type: string
        required: false
        description: "Distributed trace context"
      callback_topic:
        type: string
        required: false
        description: "Topic for result delivery"
      status:
        type: string
        required: true
        description: "pending / running / waiting / completed / failed / cancelled / withheld"
      phases:
        type: "[]PhaseResult"
        required: true
        description: "Results per phase"
      started_at:
        type: timestamp
        required: true
      completed_at:
        type: timestamp
        required: false
```

### PhaseResult

```yaml
types:
  PhaseResult:
    fields:
      phase_name:
        type: string
        required: true
        description: "Phase identifier"
      agent_name:
        type: string
        required: true
        description: "Agent that executed this phase"
      status:
        type: string
        required: true
        description: "pending / running / waiting / completed / failed / skipped"
      output:
        type: map
        required: false
        description: "Phase output data"
      started_at:
        type: timestamp
        required: false
      completed_at:
        type: timestamp
        required: false
      error:
        type: string
        required: false
        description: "Error message if failed"
      retries:
        type: int
        required: false
        description: "Number of retry attempts"
```

### WorkflowTask

```yaml
types:
  WorkflowTask:
    fields:
      activity:
        type: string
        required: true
        description: "What the person does, in the author's words"
      responsible:
        type: string
        required: true
        description: "The position whose holder does it. Never a person"
      due:
        type: string
        required: false
        description: "`<n><h|d|w>` from the moment the wait opens"
```

### WorkflowEscalation

```yaml
types:
  WorkflowEscalation:
    fields:
      after:
        type: string
        required: true
        description: "`<n><h|d|w>` past a task's due, or past an approval's opening"
      to:
        type: string
        required: true
        description: "The position it then also belongs to. Never a person"
```

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
| workflow_approval_wait_seconds | histogram | Time a wait stays open, approval or task |
| workflow_parallel_phases | gauge | Current parallel phase count |

---

## Implementation Notes

- Phases within a level MUST dispatch concurrently. Sequential
  dispatch within a level is a conformance violation.
- The executor MUST enforce the workflow-level timeout.
  When exceeded, cancel all in-flight tasks and fail the workflow.
- Phase timeouts are independent of workflow timeout. A phase can
  time out before the workflow does.
- The `self` agent target dispatches via `POST /v1/message` to the
  invoker domain — no task.submit event needed.
- Workflow executions MUST be persisted to durable storage (flat-file
  JSONL+ZSTD by default). If the executor crashes mid-execution,
  the record shows which phases completed and enables recovery.
- The trigger event's trace is carried to every task.submit event and
  downstream call as [`protocol/spec`](../protocol/spec.md#trace-propagation)
  says.
- The executor SHOULD cache workflow definitions fetched from
  domains. Cache invalidation occurs on `system.agent.registered`
  events for the source domain.

---

## Verification Checklist

- [ ] Workflows declared in YAML with required fields — [Declaration Fields](#declaration-fields)
- [ ] Reference expressions resolve correctly from every root — [Grammar](#grammar), [Roots](#roots)
- [ ] Array indexing and expansion produce correct results — [Array Indexing](#array-indexing), [Array Expansion](#array-expansion)
- [ ] Unresolvable references return null (not errors) — [Resolution Rules](#resolution-rules)
- [ ] The executor receives workflow.trigger events and resolves DAG — [Phase 1 — Trigger](#phase-1--trigger), [Phase 4 — Resolve Execution Order](#phase-4--resolve-execution-order)
- [ ] Phase dispatch through the executor's dispatcher — [Phase 5 — Execute Levels (Event-Driven)](#phase-5--execute-levels-event-driven)
- [ ] Task completion matched to workflow phase via workflow_id + phase name — [Phase 5 — Execute Levels (Event-Driven)](#phase-5--execute-levels-event-driven)
- [ ] DAG levels advance when all phases in a level complete — [Phase 5 — Execute Levels (Event-Driven)](#phase-5--execute-levels-event-driven)
- [ ] Independent phases within a level dispatch concurrently — [Phase 5 — Execute Levels (Event-Driven)](#phase-5--execute-levels-event-driven), [Implementation Notes](#implementation-notes)
- [ ] on_error: fail stops the entire workflow — [Error Strategies](#error-strategies), [Error Propagation](#error-propagation)
- [ ] on_error: skip marks phase skipped, dependents receive null — [Error Propagation](#error-propagation)
- [ ] on_error: retry re-submits via task.submit with backoff — [Error Propagation](#error-propagation)
- [ ] approval: required pauses workflow, publishes workflow.approval.required — [Approval Gates](#approval-gates)
- [ ] A decision resumes or fails the phase only when a person makes it at the executor's decision route; `workflow.approval.decision` published by any other component decides nothing — [Approval Gates](#approval-gates)
- [ ] A phase carrying `task` or `approvers` dispatches nothing and opens a wait — [A Person's Phase](#a-persons-phase), [Phase 5 — Execute Levels (Event-Driven)](#phase-5--execute-levels-event-driven)
- [ ] A phase carrying more than one of `agent`, `task` and `approvers` is refused at declaration — [A Person's Phase](#a-persons-phase)
- [ ] With `approval_order: sequential`, a decision as a later position before an earlier one has accepted is refused — [A Person's Phase](#a-persons-phase)
- [ ] An approval closes accepted only when every named position has accepted, and rejected on the first reject — [A Person's Phase](#a-persons-phase)
- [ ] An escalation fires once, `after` past a task's due or an approval's opening, and adds its `to` position — [A Person's Phase](#a-persons-phase)
- [ ] A wait naming a position whose holders cannot be read is decided by nobody — [A Person's Phase](#a-persons-phase)
- [ ] Time spent waiting for a person counts towards no phase or workflow timeout — [Approval Gates](#approval-gates)
- [ ] Workflow-level timeout cancels in-flight tasks — [Implementation Notes](#implementation-notes)
- [ ] Phase-level timeout cancels individual phase — [Implementation Notes](#implementation-notes)
- [ ] Circular dependency detection fails the workflow at init — [Phase 4 — Resolve Execution Order](#phase-4--resolve-execution-order)
- [ ] WorkflowExecution records persist to durable storage — [Phase 3 — Initialize Execution](#phase-3--initialize-execution), [Implementation Notes](#implementation-notes)
- [ ] workflow.completed published with scope = invoker — [Phase 6 — Aggregate](#phase-6--aggregate), [Event Topics](#event-topics)
- [ ] callback_topic receives result if specified — [Phase 6 — Aggregate](#phase-6--aggregate)
- [ ] Metrics emit for all workflow and phase executions — [Observability](#observability)
- [ ] trace_id and correlation_id propagate through all events — [Phase 5 — Execute Levels (Event-Driven)](#phase-5--execute-levels-event-driven), [Implementation Notes](#implementation-notes)
