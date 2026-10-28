<!-- blueprint
type: architecture
name: execution
version: 1.0.0
requires: [protocol/types, protocol/identity, patterns/workflow, patterns/scheduling, patterns/task-dispatch, patterns/approval, patterns/messaging, architecture/orchestrator, architecture/admin, architecture/domain]
platform: any
tier: free
adoption: opt-in
-->

# Weblisk Execution

The tenant service that runs work: it fires every standing start, runs every
`patterns/workflow` declaration an owner hands it, dispatches each machine
step, holds each step that waits for a person until a person decides it, and
keeps every run, step, wait and timer in one ledger.

## Overview

Execution is the merger of the cron, task and workflow agents into one
service, as the tenant service architecture the owner approved on 2026-10-05
decided (recorded in Weblisk Studio's `TENANT_RUNTIME_MAP.md`, §3.4). One
service, so that a tenant has **one run ledger and one retry layer**: every
clock that fires, every definition that runs and every step that waits is
recorded in one place, read through one surface, and retried by one rule.

Execution **runs and never owns what it runs.** A definition belongs to the
component that declares it: a domain controller
([`architecture/domain`](domain.md)) or the programme service
([`architecture/programme-service`](programme-service.md)). Execution fetches
each definition from its owner with `get_workflow`, as
[`patterns/workflow`](../patterns/workflow.md#phase-2--resolve-definition)
states, and runs it as written. It holds a definition's **starts** — its
clock, the events it reacts to, the counted conditions and the register whose
added rows each start one run — because the owner registers them here, and it
switches each start as its owner says.

**Execution decides nothing a person must.** A step that waits for a person —
a `task` or an `approval` ([`patterns/workflow`](../patterns/workflow.md#a-persons-phase))
— is a **wait**. It is listed in the admin gateway's one decision inbox
([`architecture/admin`](admin.md#decision-inbox)) and decided by a person, on
their own pass, at [`POST /v1/execution/waits/{wait}/decision`](#endpoints).
No action, event, agent or capability a service may hold closes a wait.

**What this replaces.** [`agents/cron`](../agents/cron.md),
[`agents/task`](../agents/task.md) and [`agents/workflow`](../agents/workflow.md)
described the runner before this blueprint existed. They are **superseded and
kept as interim descriptions**: nothing in them is deleted, a tenant that runs
them keeps running them, and none of them serves a person's step, approvers by
position, `escalate`, a pass on any route, or `/v1/admin/workflows`. Retiring
them from the corpus is an owner decision this blueprint does not make
([Known Gaps](#known-gaps)).

> **Scope boundary.** This document is execution's routes, its ledger, its
> rules for who may do what, and the contracts it holds each neighbour to.
> The workflow declaration format, the reference expression grammar and the
> state machine are [`patterns/workflow`](../patterns/workflow.md)'s. The
> cron expression and missed-tick rules are
> [`patterns/scheduling`](../patterns/scheduling.md)'s. The fields a
> programme author writes are [`schemas/programme`](../schemas/programme.md)'s.
> None of them is restated here.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=6.1.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category, retryable]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, via, action, target, status]
        # pass_routes is how the admin gateway learns which of these routes a
        # person's request may reach, what each needs, and which one lists
        # this service's open decisions for the decision inbox
        - name: AgentManifest
          fields_used: [name, type, capabilities, publishes, subscriptions, pass_routes]
        - name: PassRoute
          fields_used: [method, path, capabilities, inbox]
        - name: InboxRoute
          fields_used: [query, items, decide_method, decide_path]
        - name: Capability
          fields_used: [name, resources]
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: LeaseRenewal
          fields_used: [ready, checks, timestamp]
        # What a machine step is dispatched as, and what it answers
        - name: TaskRequest
          fields_used: [id, from, action, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, changes]
        - name: EventEnvelope
          fields_used: [event_id, topic, payload, source, scope, correlation_id]
        # The shape GET /v1/admin/workflows answers
        - name: WorkflowExecution
          fields_used: [id, workflow_name, domain_name, task_id, status, phases, started_at, completed_at]
        - name: PhaseResult
          fields_used: [phase_name, agent_name, status, output, started_at, completed_at, error, retries]
        # The run record this service keeps, and every client reads
        - name: Run
          fields_used: ["*"]
        - name: RunStep
          fields_used: ["*"]
        - name: RunToolCall
          fields_used: ["*"]
        - name: RunUsage
          fields_used: ["*"]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=2.1.0 <4.0.0"
    bindings:
      types:
        # type and aud say a person's request reached this service on a pass
        # addressed to it; cap is what it may use; identity_id names who
        # acted; act names the gateway that carried it
        - name: WLToken
          fields_used: [type, aud, act, cap, identity_id, sub]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/workflow
    version: ">=4.0.0 <5.0.0"
    bindings:
      types:
        - name: WorkflowDefinition
          fields_used: [name, description, trigger, timeout, phases]
        - name: WorkflowPhase
          fields_used: [name, agent, action, input, output, depends_on, timeout, approval, approvers, approval_order, task, escalate, on_error, max_attempts, condition]
        - name: WorkflowTask
          fields_used: [activity, responsible, due]
        - name: WorkflowEscalation
          fields_used: [after, to]
      behaviors:
        - name: workflow-execution
          usage: Every run, whoever owns its definition
        - name: phase-dispatch
          usage: Every machine phase, through this service's own dispatcher
        - name: approval-gate
          usage: A machine phase whose output waits for a person's decision
        - name: person-phase
          usage: A task or approval phase, held as a wait and decided only at this service's decision route
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/scheduling
    version: ">=2.0.0 <3.0.0"
    bindings:
      behaviors:
        - name: schedule-evaluation
          usage: Each clock start, evaluated as the pattern's evaluation flow says
        - name: distributed-locking
          usage: One evaluation cycle at a time, however many instances run
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/task-dispatch
    version: ">=3.0.0 <4.0.0"
    bindings:
      behaviors:
        - name: dispatch-execution
          usage: Each machine phase sent to its target's POST /v1/execute
        - name: concurrency-control
          usage: In-flight steps per target, against the target's declared capacity
        - name: dead-letter-handling
          usage: A step whose attempts are exhausted is recorded, never dropped
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/approval
    version: ">=1.1.0 <4.0.0"
    bindings:
      behaviors:
        # Its self-approval rejection, applied to every approval wait
        - name: approval-decision
          usage: A wait is never accepted by the person who started its run or did the work it approves
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

  - blueprint: architecture/orchestrator
    version: ">=3.0.0 <5.0.0"
    bindings:
      behaviors:
        # What a pass this service accepts rests on. Relied on, never called
        - name: token-exchange
          usage: Every pass this service accepts was minted by the exchange, for an operator token the orchestrator judged live then, carrying no capability the person could not use then
      events:
        - topic: system.agent.registered
          fields_used: [agent_name, manifest]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/admin
    version: ">=5.0.0 <6.0.0"
    bindings:
      behaviors:
        # The one door a person's request arrives through, and the inbox it
        # composes from this service's open waits
        - name: admin-gateway-authorization
          usage: Relied on, never called here. A person's request reaches this service only on a route its manifest declares among pass_routes, on a pass naming every capability that route declares
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/domain
    version: ">=3.0.0 <4.0.0"
    bindings:
      types:
        # Which definitions a domain owns
        - name: DomainManifest
          fields_used: [workflows]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
  owner (programme service, domain) ──PUT start──►┌─────────────────────────────┐
         ▲  get_workflow, a self/does: phase      │  Execution                  │
         └────────────────────────────────────────┤                             │
                                                  │  Start Registry             │
  events (workflow.trigger, the allow-list) ─────►│   clock · on · when · for   │
                                                  │  Clock and Timer Wheel      │
                                                  │  Run Engine (DAG)           │
                                                  │  Dispatcher ──service pass──┼──► work agent, prompt worker
                                                  │  Wait Holder                │       (POST /v1/execute)
  person ──► admin gateway ──pass──► decide ─────►│  Run Ledger (one)           │
                    ▲                             └──────────────┬──────────────┘
                    │ inbox: GET /v1/execution/waits             │ a wait opened, escalated
                    └────────────────────────────────────────────┘──► notification (not specified)
```

**Start Registry** holds each start an owner registered: what fires it, the
definition it runs, the scope it runs at, and its two switches, paused or
running and muted or unmuted. A start is registered, changed, switched and
withdrawn by its owner alone ([Who May Do What](#who-may-do-what)).

**Clock and Timer Wheel** holds every instant something is owed: a clock
start's next firing, a machine phase's timeout, a retry's backoff, a task's
due and an escalation. Each is a [`timer`](#resources). One evaluation cycle
runs at a time, under [`patterns/scheduling`](../patterns/scheduling.md)'s
`distributed-locking`.

**Run Engine** resolves a definition's phases into levels and advances a run
through them, as [`patterns/workflow`](../patterns/workflow.md#execution-engine-event-driven)
specifies. It is one engine for every owner's definitions.

**Dispatcher** sends each machine phase to its target, under
[`patterns/task-dispatch`](../patterns/task-dispatch.md)'s capacity, priority
and dead-letter rules, on the authority [Unattended authority](#unattended-authority)
says. It replaces the task agent: there is no `task.submit` round trip inside
one service.

**Wait Holder** opens a wait for each person's phase, resolves the positions
it names to the people who hold them, answers the inbox, and accepts a
decision only from a person holding a named position.

**Run Ledger** is the one record of every run, step, wait and timer. It is
this service's own record store, under exclusive custody. A run is never
deleted while its retention lasts, and what a muted run produced is kept here
and nowhere else.

---

## Responsibilities

### Owns

- Every start an owner registers, and firing it: a clock, an event on the
  allow-list, a counted condition, or one run per added register row
- Every run, from the start that fired it to its end, with each step's
  dispatch, attempts, output and outcome
- Every wait: who it awaits, by position and in what order; when it is due;
  its escalation; and each decision recorded on it
- Every timer the above owe
- Dispatching every machine phase, and retrying it by one rule
- The workflow runs group of the admin API, `GET /v1/admin/workflows` and
  `GET /v1/admin/workflows/{id}` ([`architecture/admin`](admin.md#the-admin-api-is-an-aggregate))
- Listing its open waits for the decision inbox, and the route each is
  decided at

### Does NOT Own

- **Any definition.** A workflow definition is its owner's, fetched with
  `get_workflow` and never edited here. Execution keeps the copy it fetched,
  with its digest, as the record of what it ran
- **Whether an owner's item runs or reaches people.** A programme's pause and
  mute are the programme service's switches, set there by a person; execution
  holds the start's state as its owner last said
- **Who holds a position.** That is the tenant's register in content
  ([`schemas/position.md`](../schemas/position.md#known-gaps)); execution
  reads it and keeps no copy
- **How a person is told.** Notification's, by each person's preference
- **A model.** An `agent:` phase is the prompt worker's, which asks the
  tenant's model service
- **Any decision.** A person makes it, here, on their own pass
- **What is due.** Occurrences, the due list and readiness are the programme
  service's, and the `obligation.*` facts are published by whoever that
  service's blueprint names

---

## Endpoints

| Method | Path | Operation | Auth | Capability | Purpose |
|--------|------|-----------|------|------------|---------|
| GET | /v1/admin/workflows | ListWorkflowRuns | yes | `admin:read` | The admin API's workflow runs group: every run, newest first, cursor-paginated, in the shape [`architecture/admin`](admin.md#get-v1adminworkflows) gives. A pass only |
| GET | /v1/admin/workflows/{id} | GetWorkflowRun | yes | `admin:read` | One run in the same shape, its phases with timing and output. A pass only |
| GET | /v1/execution/runs | ListRuns | yes | `execution:read` | `Run`s, newest first, filtered by `definition`, `definition_kind`, `agent`, `parent`, `status`, `owner`, `schedule` and `organisation`, cursor-paginated, as a `RunPage` |
| GET | /v1/execution/runs/{run} | GetRun | yes | `execution:read` | One `Run` |
| POST | /v1/execution/runs/{run}/cancel | CancelRun | yes | `execution:operate` | Stop a run: cancel its in-flight steps, close its open waits, and end it `cancelled` |
| POST | /v1/execution/runs/{run}/retry | RetryRun | yes | `execution:operate` | Queue a new run of a `failed` or `cancelled` run's definition, from the phase it ended at, with this run as its `parent` |
| GET | /v1/execution/waits | ListWaits | yes | `execution:read` | Waits, filtered by `state`, `run` and `organisation`. With `for=me`, the waits the person on the pass may decide now. The decision inbox's list route |
| GET | /v1/execution/waits/{wait} | GetWait | yes | `execution:read` | One `Wait`, with every decision recorded on it |
| POST | /v1/execution/waits/{wait}/decision | DecideWait | yes | `execution:decide` | Decide a wait: complete or decline a task, accept or reject an approval. A pass only |
| GET | /v1/execution/schedules | ListSchedules | yes | `execution:read` | Starts, filtered by `owner`, `state` and `organisation`, each with its two switches and its next firing |
| GET | /v1/execution/schedules/{schedule} | GetSchedule | yes | `execution:read` | One `Schedule`, with its last run and what it holds while paused |
| PUT | /v1/execution/schedules/{schedule} | PutSchedule | yes | `execution:register` | Register or replace one of the caller's own starts. A registration token only |
| DELETE | /v1/execution/schedules/{schedule} | WithdrawSchedule | yes | `execution:register` | Withdraw one of the caller's own starts. Starts nothing again; deletes no run. A registration token only |
| POST | /v1/execution/schedules/{schedule}/pause | PauseSchedule | yes | `execution:register` | Start no new run from it. Runs already started continue. A registration token only |
| POST | /v1/execution/schedules/{schedule}/resume | ResumeSchedule | yes | `execution:register` | Start runs from it again, delivering what it held while paused. A registration token only |
| POST | /v1/execution/schedules/{schedule}/runs | RunScheduleNow | yes | `execution:register` | Start one run now, as its next firing would. A registration token only |
| POST | /v1/event | Event | yes | | Receive a delivered event: `workflow.trigger`, the allow-listed facts a start names, and the orchestrator's `system.agent.*` ([`protocol/spec`](../protocol/spec.md#post-v1event)) |
| POST | /v1/services | Services | yes | | Accept the signed service directory the orchestrator pushes, as [`protocol/spec`](../protocol/spec.md#post-v1services) specifies |
| GET | /livez | Livez | no | | Liveness, for the supervisor that restarts the service |
| GET | /readyz | Readyz | no | | Readiness, for the supervisor waiting on its start |

**The rest is read at the uniform address.** A run's steps, its tool calls,
timers and the definitions execution fetched are read through the admin
gateway's one API for every kind
([`architecture/admin`](admin.md#resources-one-api-for-every-kind)), which this
service serves for each kind whose operations bind none of the routes above
([Resources](#resources)).

**A person's routes and an owner's routes are different routes.** Every
route above but the three schedule-switching routes, `PUT` and `DELETE` on a
schedule, `POST /v1/event`, `POST /v1/services` and the probes is declared
among the manifest's `pass_routes`, with the one capability in its row and no
body requirement. The admin gateway carries a person's request here only on
a route that list declares ([`architecture/admin`](admin.md#contracts),
`admin-gateway-authorization`), so the list and the table MUST agree.

**`GET /v1/execution/waits` is declared as the inbox route.** Its
`PassRoute` carries an `inbox`
([`protocol/types`](../protocol/types.md#inboxroute)):

```yaml
method: GET
path: /v1/execution/waits
capabilities: [execution:read]
inbox:
  query: state=open&for=me
  items: waits
  decide_method: POST
  decide_path: /v1/execution/waits/{wait}/decision
```

It names no `withheld`: a wait record carries no step output
([Types](#types), `Wait`), so a listing omits nothing a person may not read.
A run's output is read with `GET /v1/execution/runs/{run}`, under its own
capability.

**Scope parameters.** A list route takes `organisation` to narrow to one
organisation's runs, waits or starts, and lists every scope without it.
Naming an organisation grants nothing: the route's capability is checked as on
any other request. A route missing a parameter its row requires, or naming a
value outside its closed set, is refused with `INVALID_REQUEST`.

The service declares `execution:read`, `execution:operate`,
`execution:register`, `agent:message` and `event:observe` on its manifest. It checks
`execution:decide` but never holds it, as
[`protocol/types`](../protocol/types.md#capability) requires of a person-only
capability. An owner that registers starts here declares `execution:register`
on its own manifest.

---

## Interfaces

**What it asks of an owner**, on [`POST /v1/message`](../protocol/spec.md#post-v1message),
on its own registration token:

| action | asked of | answers |
|---|---|---|
| `get_workflow` | the definition's owner, by the name the start or trigger gives | The `WorkflowDefinition`. `NOT_FOUND` ends the run `failed`, recording that the owner no longer has it |
| a phase's `action`, where its `agent` is the owner or `self` | the definition's owner | The phase's outcome, under the owner's own authority. The programme service runs a `does:` action this way ([`architecture/programme-service`](programme-service.md#interfaces)) |

**What it answers**, on [`POST /v1/message`](../protocol/spec.md#post-v1message):

| action | from | does |
|---|---|---|
| `record_turn` | the agent a running step was dispatched to, on its own registration token, for that step alone | Records one model turn as a `RunStep` of `step_type` `model-turn`, and each tool call it made as a `RunToolCall` of that step, with the backend, model, usage and cost as the backend reported them ([`protocol/types`](../protocol/types.md#runs)). Any other caller, or a step that is not running, is refused with `FORBIDDEN` |

**What it sends a work agent or the prompt worker**: a `TaskRequest` to its
`POST /v1/execute`, on a service pass ([Unattended authority](#unattended-authority)),
as [`patterns/task-dispatch`](../patterns/task-dispatch.md) dispatches one.
An `agent:` phase is sent to the prompt worker with `action`
`run_instruction` and an `InstructionTask` as its `payload`
([The prompt worker](#the-prompt-worker)).

**Events it publishes** (namespaces `workflow` and `execution`, claimed at
registration):

| Topic | Scope | Payload | When |
|---|---|---|---|
| `workflow.started` | the owner | `{execution_id, workflow_name, invoker, timestamp}` | A run begins |
| `workflow.completed` | the owner | `{execution_id, workflow_name, status, summary, phase_results}` | A run ends `completed` |
| `workflow.failed` | the owner | `{execution_id, workflow_name, failed_phase, error, timestamp}` | A run ends `failed` |
| `workflow.approval.decision` | the owner | `{workflow_id, phase, decision, reason}` | A person decided a wait here. A record of a decision made, never a way to make one |
| `execution.wait.opened` | the owner | `{wait, run, step, kind, positions, due_at}` | A wait opens in an unmuted run |
| `execution.wait.escalated` | the owner | `{wait, run, step, to, escalated_at}` | A wait's escalation fires |
| `execution.wait.closed` | the owner | `{wait, run, step, outcome}` | A wait is decided, cancelled or withheld |

A run's state changes, and each step, call and wait recorded, are announced on
the admin gateway's feed as each kind's Resources entry names its events
([Resources](#resources)), not as further topics here.

A run's callback, where its trigger named one, is published as
[`patterns/workflow`](../patterns/workflow.md#phase-6--aggregate) says.

**Events it subscribes to**: `workflow.trigger` (scope `self`), the
orchestrator's `system.agent.registered` and `system.agent.deregistered`, and
each fact the start allow-list names
([`schemas/programme.md`](../schemas/programme.md#on--reacting-to-a-fact-instead-of-to-the-clock)):
`obligation.due_soon`, `obligation.overdue`, `obligation.escalated`,
`attestation`, `register.row_added` and `adopted`, at scope `*`, which needs
`event:observe` on its manifest. Which service publishes those facts, and on
what topic, is not yet specified ([Known Gaps](#known-gaps)); execution
subscribes to the names that schema writes and follows the publisher's
blueprint when one exists.

---

## Error Handling

| Code | When |
|---|---|
| `PASS_REQUIRED` | An operator token was presented on any route ([`protocol/identity`](../protocol/identity.md#the-pass), rule 4) |
| `PASS_AUDIENCE_MISMATCH` | A pass addressed to another component |
| `FORBIDDEN` | The token does not carry the route's capability; a route this document reserves to a pass was reached on another token, or one reserved to a registration token was reached on a pass; or a registration token names a schedule or run another owner holds |
| `INVALID_REQUEST` | A missing or out-of-set parameter; a `ScheduleRegistration` with none or more than one of `clock`, `on`, `when` and `for`; or a `WaitDecision` whose `decision` does not fit the wait's kind |
| `NOT_FOUND` | No run, wait, schedule, timer or definition with that id |
| `INVALID_STATE` | Cancelling a run that has ended; retrying a run that is not `failed` or `cancelled`; deciding a wait that is not open; pausing a paused start or resuming a running one |
| `EXECUTION_NOT_A_HOLDER` | The person on the pass does not hold the position the decision names, or that position is not one the wait still awaits |
| `EXECUTION_DECISION_OUT_OF_ORDER` | A sequential approval decided as a position whose turn has not come |
| `EXECUTION_POSITION_UNRESOLVED` | Who holds the positions the wait names cannot be read, so nobody can be shown to hold one. Nothing is decided |
| `EXECUTION_MUTED` | A decision on a wait of a muted run, which reaches nobody |
| `EXECUTION_PASS_UNAVAILABLE` | `RunScheduleNow` or `RetryRun` needs a step dispatched on a service pass, and none can be obtained |
| `STEP_UP_REQUIRED` | `CancelRun` without a recent re-confirmation: cancelling is destructive ([Resources](#resources); [`architecture/admin`](admin.md#contracts), `destructive-action-step-up`). The run continues |
| `APPROVAL_SELF_DENIED` | An approval accepted by the person who started its run, or who completed a task it follows ([`patterns/approval`](../patterns/approval.md#error-handling)) |

Each code but `APPROVAL_SELF_DENIED` is registered in
[`protocol/types`](../protocol/types.md#errors), the five `EXECUTION_` codes
under Execution codes; `APPROVAL_SELF_DENIED` is
[`patterns/approval`](../patterns/approval.md#error-handling)'s. A refused
decision changes nothing: the wait stays open and nothing is recorded on it
but the refusal, in the audit.

A run that could not do what it was asked is not an error on any route. It
is a run in the ledger with its status and its reason: a step whose target is
not registered, a definition its owner no longer has, a service pass that
could not be obtained. A run is never reported as having run a step it did
not dispatch.

---

## Data Flow

### Registering a start

1. An owner sends `PUT /v1/execution/schedules/{schedule}` on its
   registration token carrying `execution:register`, with a
   `ScheduleRegistration`: the definition's name, the scope, exactly one of
   `clock`, `on`, `when` and `for`, and `state` and `muted`. `{schedule}` is
   the owner's own key for the start, such as `<programme>.<id>`; with the
   owner's identity id it is what registering twice matches on.
2. The service checks the start against its vocabulary
   ([`schemas/programme.md`](../schemas/programme.md#schedule--a-small-closed-vocabulary-and-not-the-obligations),
   `on`, `when` and `for`), refuses what it refuses, and records the owner as
   the registration token's `identity_id`.
3. It answers the `Schedule`, with its next firing where it has a clock. A
   start registered `paused` fires nothing until its owner resumes it.

The programme service registers one start per installed operation and
workflow, muted, as its install says
([`architecture/programme-service`](programme-service.md#installing)). A
domain controller registers a clock start for a definition it wants run on
one. A domain's `workflow.trigger` needs no registration.

### Firing

1. A clock reaches its instant, an allow-listed fact arrives, a counted
   condition crosses its threshold, a register row is added, or a domain
   publishes `workflow.trigger`. A trigger is run only for the domain that
   published it: an envelope whose `source` is not the `source_domain` it
   names starts nothing.
2. For a running start, the service queues a `Run`
   ([`protocol/types`](../protocol/types.md#run)): its definition, owner,
   organisation, the start or event that fired it, the start's `muted`, and the
   **chain**, the runs that through `for` started it. A burst of `on` facts
   within `coalesce_window` is one run carrying how many facts it covers. A
   `for` row whose chain already holds a run of this definition starts
   nothing ([`schemas/programme.md`](../schemas/programme.md#for--one-run-per-record)).
3. For a paused start, `for` rows and an `adopted` fact are held, once each,
   and delivered when the start resumes; every other fact is dropped and
   counted on the start. A held row that cannot be kept is recorded on the
   start as missed, naming the row.
4. It fetches the definition from its owner with `get_workflow`, records its
   digest, and resolves its phases into levels.

### Running a machine phase

1. A phase whose `condition` is false is `skipped`. Its inputs are resolved
   as [`patterns/workflow`](../patterns/workflow.md#reference-expression-syntax)
   says.
2. A phase whose `agent` is the owner or `self` is sent to the owner on
   `POST /v1/message`, on this service's registration token. Any other is
   dispatched to its target's `POST /v1/execute` on a service pass.
3. The step is recorded with each attempt. A failure is handled by the
   phase's `on_error`, and a retry waits as
   [`protocol/conventions`](../protocol/conventions.md) `backoff` says. A step
   whose attempts are exhausted is dead-lettered and recorded, never dropped.
4. A machine phase with `approval: required` keeps its output from later
   phases and opens a wait for it, as for a person's phase below.

### A person's phase

1. A `task` phase, an `approval` phase, or a machine phase awaiting approval
   opens a **wait**. It awaits the positions the phase names: a task's
   `responsible`, or an approval's `approvers` in `approval_order`. An
   approval with no `approvers` awaits any person holding `execution:decide`.
2. The service resolves who holds each awaited position at the run's scope
   ([Who holds a position](#who-holds-a-position)) and records whether it
   could.
3. In an unmuted run the wait is announced: `execution.wait.opened` is
   published, and notification is asked to tell the awaited positions. In a
   muted run the wait is recorded `withheld`, announced to nobody, and the
   run ends `withheld` there ([Muted runs](#muted-runs)).
4. A task's `due` starts a timer from the moment the wait opens; an
   `escalate` starts one at `after` past the due, or past the opening for an
   approval, which has no due.
5. The run is `waiting` while it has an open wait and no phase running. Time
   spent waiting counts towards no phase or run `timeout`.

### Deciding

1. A person's client sends `POST /v1/execution/waits/{wait}/decision`
   through the admin gateway, on the person's own pass, with a
   `WaitDecision`: the `decision`, the `position` they decide as, and a
   `reason`.
2. The service refuses it unless the pass carries `execution:decide`, the
   wait is open and its run unmuted, the position is one the wait still
   awaits (or its escalation position, once escalated), it is that position's
   turn in a sequential approval, and the pass's `identity_id` holds the
   position. One person fills one position of one wait.
3. An approval is not accepted by the person who started the run, or who
   completed a task the approval follows (`APPROVAL_SELF_DENIED`).
4. The decision is recorded on the wait, with the pass's `identity_id` as
   who decided and `act.identity_id` as the gateway that carried it.
5. A task `complete` closes the wait and completes the phase. A `decline`
   closes it and fails the phase, and its `on_error` applies. An approval
   `reject` by any awaited position closes it rejected and fails the phase.
   An `accept` closes it once every awaited position has accepted.
6. The run advances, `workflow.approval.decision` and `execution.wait.closed`
   are published, and the decision is written to the audit.

### Escalating

When an escalation timer fires on an open wait, the wait gains the
escalation's `to` position: a holder of it may now decide in place of the
position the wait awaits, in a sequential approval the current one and
otherwise the first still awaited in declared order. The awaited positions
may still decide. `execution.wait.escalated` is published and notification
asked to tell `to`. A wait escalates once.

### Cancelling and retrying

`POST /v1/execution/runs/{run}/cancel` cancels in-flight steps, closes open
waits `cancelled`, cancels the run's timers and ends it `cancelled`.
`POST /v1/execution/runs/{run}/retry` leaves the run as it is and queues a
new run of the same definition, with `parent` this run, `trigger` `person` and
`triggered_by` the person's identity id. It starts at the phase this run
failed or was cancelled at, with the outputs of the phases this run completed;
nothing this run did is run again. A definition its owner no longer has is
`NOT_FOUND`.

---

## Who May Do What

The token rules are [`protocol/identity`](../protocol/identity.md#the-pass)'s
and are not restated here.

1. **A person reaches this service only on a pass.** An operator token is
   refused on every route with `PASS_REQUIRED`.
2. **Only a person decides a wait, and only on a pass.** `execution:decide`
   is person only. A registration, channel or service pass on the decision
   route is refused with `FORBIDDEN`, whatever it carries. No event, action
   or phase output closes a wait, `workflow.approval.decision` included: that
   event is published here after a person has decided, and the service
   subscribes to no topic that would close a wait.
3. **A start is its owner's.** `PUT`, `DELETE`, pause, resume and run-now on
   a schedule are admitted only on the registration token of the component
   that registered it, carrying `execution:register`. A person switches a
   programme's item at the programme service, whose rules decide whether that
   person may, and the programme service switches the start here. A pass on
   these routes is refused with `FORBIDDEN`. This keeps one authority over
   each switch: a start paused here and running at its owner would be two
   answers to one question.
4. **A run may be cancelled or retried by a person or by its owner.** A pass
   carrying `execution:operate` reaches any run. A registration token
   carrying `execution:operate` reaches only runs of definitions its own
   identity owns.
5. **Unattended work runs under its owner's authority, never a person's.**
   A run that nobody started runs as its definition's owner
   ([Unattended authority](#unattended-authority)). A run a person's act
   started records that person in `triggered_by`, with `trigger` `person`,
   and does not run with their authority.
6. **Reading is `execution:read`, on a pass or a registration token.** The
   admin API's two workflow routes need `admin:read`, on a pass only.

Each act records an `AuditEntry`. On a pass, the person is the `actor` by the
pass's `identity_id` and the gateway is `via`.

### Unattended authority

A firing has no person behind it, so no pass
([`protocol/identity`](../protocol/identity.md#the-pass)) can carry it.
[`architecture/domain`](domain.md) says a definition runs "on a pass minted
for the definition's owner", and the identity lane of this corpus is
specifying that token, a **service pass**. Execution requires of it exactly
this, and dispatches on nothing weaker:

1. The orchestrator mints it, at execution's request, for one dispatch: its
   subject is the definition's **owner** (its registration's `identity_id`),
   its audience the one component the step is sent to, and its actor
   execution.
2. Its `cap` is never more than the intersection of what the owner's
   manifest declares and, for an `agent:` phase, the phase's `needs` ceiling.
   It never carries a person-only capability.
3. It is minted only while the owner's lease is current, lives no longer
   than one step's timeout, and is never exchanged again.
4. The component it reaches records the owner as who acted, and execution as
   who carried it.

**Two cases need no service pass.** A phase sent to the definition's own
owner runs under the owner's own registration, so execution sends it on its
own token, with `agent:message`. Reading and recording in its own ledger is
execution's own work.

Until the service pass is specified and the orchestrator mints it, a step
that needs one is **not dispatched**: it is recorded `failed` with
`EXECUTION_PASS_UNAVAILABLE`, its `on_error` applies, and the run says why.
Execution never dispatches such a step on its own registration token
instead, which would run every owner's work with execution's authority.

### Who holds a position

A wait names positions, never people. Whether the person on a pass holds one
is read from the tenant's register of who holds each position, in the
scope's records repository in content
([`schemas/position.md`](../schemas/position.md#known-gaps)). Execution reads
it on its own registration token, at the run's organisation, when a wait
opens and again at each decision, and keeps no copy.

That register's spec is not yet declared. Until it is, every wait is
recorded with `holders: unresolved`, `GET /v1/execution/waits?for=me` lists
every open wait in scope with that mark rather than an empty list, and every
decision on a wait naming a position is refused with
`EXECUTION_POSITION_UNRESOLVED`. A wait is never decided by capability alone
because its positions could not be read. An approval with no `approvers`
names no position and is decided by capability.

### Muted runs

A run keeps the `muted` its start had when it fired. What a muted run
produces reaches nobody and is kept in the ledger, so a person can compare it
before unmuting ([`architecture/programme-service`](programme-service.md#firing)).
Its machine phases run. At its first person's phase the wait is recorded
`withheld`, nobody is told, the inbox does not list it, and the run ends
`withheld`. Unmuting a start changes the runs it starts afterwards, never one
already recorded.

---

## The Services It Depends On

### The prompt worker

An `agent:` phase is sent to the prompt worker, the tenant's one runner of
`agent:` instructions ([`architecture/programme-service`](programme-service.md#the-prompt-worker)).
Its blueprint is not written. Execution holds it to this contract:

1. It receives a `TaskRequest` on `POST /v1/execute`, `action`
   `run_instruction`, with an `InstructionTask` as `payload`, on a service
   pass whose `cap` is the ceiling rule 2 of
   [Unattended authority](#unattended-authority) gives.
2. It answers a `TaskResult` within the phase's `timeout`: `status`
   `success` or `failed`, a `summary`, and in `changes` each proposal it made
   through an owner's API. It writes nothing except through an owner's API.
3. It keeps nothing. The run's record is execution's: the worker reports each
   model turn it takes, and each tool call that turn makes, to execution with
   `record_turn` ([Interfaces](#interfaces)) as it happens, with the backend,
   model, usage and cost the backend reported, and what it answers is
   recorded on the step.
4. Told that the run is muted, it makes no proposal a person would see, and
   says in `summary` what it would have proposed.

Until a prompt worker is registered, an `agent:` phase is recorded `failed`
with its target not registered, never as having run.

### Notification

When a wait opens or escalates in an unmuted run, execution asks
notification to tell the awaited positions: the wait's id, its kind, its
title or activity, its due, and its decide route. The notify-by-position
call has no declared name yet
([`architecture/programme-service`](programme-service.md#notification)).
Until notification's blueprint declares it, the wait records `announced:
false` with that reason, and the inbox still lists it: a wait nobody was told
of is still a wait.

### Content

Execution reads the position register from content. Every write a step makes
is made by the component the step reached, through content's own routes, as
a proposal where content requires one. A run's id and chain travel in each
dispatch's `context`, so that a row a run wrote can carry them once content
records them ([Known Gaps](#known-gaps)).

---

## Known Gaps

**The service pass is not yet specified.** [Unattended authority](#unattended-authority)
states what execution requires of it. Until
[`protocol/identity`](../protocol/identity.md#the-pass) specifies it and the
orchestrator mints it, every step dispatched to a component other than its
definition's owner is recorded failed, and so is every `agent:` phase. A
`does:` phase of the programme service and a domain's `self` phase run.

**Nobody can be shown to hold a position.** The register is not declared
([`schemas/position.md`](../schemas/position.md#known-gaps)), so every wait
naming a position is listed and cannot be decided
([Who holds a position](#who-holds-a-position)).

**Notification and the prompt worker have no blueprint.** A wait opens
unannounced and an `agent:` phase fails, each saying so.

**The facts a start reacts to have no publisher.** `obligation.*`,
`attestation`, `register.row_added` and `adopted` are named by
[`schemas/programme.md`](../schemas/programme.md#on--reacting-to-a-fact-instead-of-to-the-clock)
and published by no specified service
([`architecture/programme-service`](programme-service.md#known-gaps)), so an
`on`, `when` or `for` start registers and fires nothing until one is.

**No content entry records the run that wrote it.** Execution carries a
run's chain in every dispatch's context, and nothing yet writes it beside the
row, so a `for` loop is stopped only within execution's own records.

**The interim agents are not retired.** `agents/cron`, `agents/task` and
`agents/workflow` stay in the corpus, and `weblisk agent create` still builds
them. Whether they are retired, and when, is the owner's to decide.

---

## Types

A run's record is [`protocol/types`](../protocol/types.md#runs)' `Run`,
`RunStep` and `RunToolCall`, which every client of the admin API reads, and is
not restated here. These are execution's own.

```yaml
types:
  RunPage:
    description: One page of GET /v1/execution/runs, newest first
    fields:
      runs: {type: "[]Run", required: true}
      next_cursor: {type: string, required: false, description: Absent on the last page}

  Wait:
    description: A step held for a person. Carries no step output. An item of GET /v1/execution/waits
    fields:
      uid: {type: string, required: true, description: Minted by execution when the wait opens. 32 lowercase hex characters}
      id: {type: string, required: true, description: The same value as uid, under the name the decision inbox fills decide_path from}
      run: {type: string, required: true}
      step: {type: string, required: true, description: The RunStep that opened it}
      kind: {type: string, required: true, enum: [task, approval]}
      title: {type: string, required: true}
      activity: {type: string, required: false, description: A task's activity}
      positions: {type: "[]string", required: true, description: The positions awaited, in declared order. Empty for an approval that names none}
      approval_order: {type: string, required: false, enum: [sequential]}
      escalated_to: {type: string, required: false}
      due_at: {type: timestamp, required: false}
      opened_at: {type: timestamp, required: true}
      closed_at: {type: timestamp, required: false}
      holders: {type: string, required: true, enum: [resolved, unresolved]}
      announced: {type: bool, required: true}
      state: {type: string, required: true, enum: [open, completed, declined, accepted, rejected, cancelled, withheld]}
      decisions: {type: "[]WaitDecisionRecord", required: true}
      organisation: {type: string, required: true}
      project: {type: string, required: false}

  WaitPage:
    description: One page of GET /v1/execution/waits
    fields:
      waits: {type: "[]Wait", required: true}
      next_cursor: {type: string, required: false, description: Absent on the last page}

  WaitDecision:
    description: The body of POST /v1/execution/waits/{wait}/decision
    fields:
      decision: {type: string, required: true, enum: [complete, decline, accept, reject], description: complete or decline on a task, accept or reject on an approval}
      position: {type: string, required: false, description: The position decided as. Required where the wait names positions}
      reason: {type: string, required: true}

  WaitDecisionRecord:
    description: One decision recorded on a wait
    fields:
      decision: {type: string, required: true}
      position: {type: string, required: false}
      decided_by: {type: string, required: true, description: The pass's identity_id}
      via: {type: string, required: true, description: The pass's act.identity_id}
      reason: {type: string, required: true}
      decided_at: {type: timestamp, required: true}

  ScheduleRegistration:
    description: The body of PUT /v1/execution/schedules/{schedule}. Exactly one of clock, on, when and for
    fields:
      definition: {type: string, required: true, description: The name get_workflow is asked for}
      organisation: {type: string, required: true}
      project: {type: string, required: false}
      clock: {type: Clock, required: false}
      on: {type: "[]string", required: false, description: Facts on the allow-list}
      when: {type: "[]Condition", required: false}
      for: {type: RecordStart, required: false}
      state: {type: string, required: true, enum: [paused, running]}
      muted: {type: bool, required: true}

  Clock:
    description: schemas/programme's schedule vocabulary
    fields:
      cadence: {type: string, required: true, enum: [hourly, daily, weekly, monthly]}
      local_time: {type: string, required: false, description: "The programme's `at`: HH:MM, 24-hour, in timezone. Required except hourly"}
      weekday: {type: string, required: false}
      day: {type: int, required: false}
      timezone: {type: string, required: true, description: IANA name of the installation's local time}

  Condition:
    description: schemas/programme's when, as written there
    fields:
      event: {type: string, required: true}
      where: {type: map, required: false}
      within: {type: string, required: true}
      across: {type: string, required: false, enum: [project, org]}
      count: {type: map, required: true}

  RecordStart:
    description: schemas/programme's for
    fields:
      records: {type: string, required: true}

  Schedule:
    description: A registered start. GET /v1/execution/schedules/{schedule}
    fields:
      uid: {type: string, required: true, description: Minted by execution on first registration}
      owner: {type: string, required: true, description: The registering component's identity id}
      key: {type: string, required: true, description: The owner's own key; with owner, what registering twice matches on}
      definition: {type: string, required: true}
      organisation: {type: string, required: true}
      project: {type: string, required: false}
      registration: {type: ScheduleRegistration, required: true}
      state: {type: string, required: true, enum: [paused, running]}
      muted: {type: bool, required: true}
      held: {type: int, required: true, description: Rows and adopted facts held while paused}
      dropped: {type: int, required: true, description: Facts dropped while paused}
      missed: {type: "[]string", required: true, description: Held rows that could not be kept, by key}
      next_fire: {type: timestamp, required: false}
      last_run: {type: string, required: false}

  SchedulePage:
    description: One page of GET /v1/execution/schedules
    fields:
      schedules: {type: "[]Schedule", required: true}
      next_cursor: {type: string, required: false}

  Timer:
    description: An instant something is owed
    fields:
      uid: {type: string, required: true}
      kind: {type: string, required: true, enum: [start, phase, retry, due, escalate]}
      run: {type: string, required: false}
      wait: {type: string, required: false}
      schedule: {type: string, required: false}
      due_at: {type: timestamp, required: true}
      state: {type: string, required: true, enum: [pending, fired, cancelled]}

  FetchedDefinition:
    description: A definition as execution last fetched it from its owner
    fields:
      uid: {type: string, required: true, description: Minted by execution on first fetch, matched by owner and name}
      owner: {type: string, required: true}
      name: {type: string, required: true}
      digest: {type: string, required: true, description: "sha256:<hex> of the definition's RFC 8785 bytes"}
      fetched_at: {type: timestamp, required: true}
      definition: {type: WorkflowDefinition, required: true}

  InstructionTask:
    description: The payload of run_instruction, sent to the prompt worker
    fields:
      instruction: {type: string, required: true, description: The agent instruction, in the author's words}
      needs: {type: "[]string", required: true, description: The phase's ceiling. Empty means read}
      run: {type: string, required: true}
      step: {type: string, required: true}
      chain: {type: "[]string", required: true}
      organisation: {type: string, required: true}
      project: {type: string, required: false}
      muted: {type: bool, required: true}
      events: {type: int, required: false, description: How many facts this run covers, so a coalesced burst is never answered as one}
      record: {type: map, required: false}
```

---

## Resources

Every kind execution holds, declared as
[`schemas/resource`](../schemas/resource.md) says. **`run`, `run-step` and
`tool-call` are declared here, by their owner**, and nowhere else: until this
blueprint existed they were held for execution in
[`architecture/programme-service`](programme-service.md), and that block moves
here, unchanged but for what reconciling it with this blueprint requires
(the note after the block).

```yaml
resources:
  - kind: run
    owner: execution
    type: Run
    identity: {field: uid, form: minted}
    label: definition
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: definition, access: read-only, present: text}
      - {name: definition_kind, access: read-only, present: choice}
      - {name: owner, access: read-only, present: text}
      - {name: organisation, access: read-only, present: text}
      - {name: project, access: read-only, present: text}
      - {name: schedule, access: read-only, present: reference, kind: schedule}
      - {name: agent, access: read-only, present: reference, kind: agent}
      - {name: parent, access: read-only, present: reference, kind: run}
      - {name: chain, access: read-only, present: list}
      - {name: muted, access: read-only, present: boolean}
      - {name: trigger, access: read-only, present: choice}
      - {name: triggered_by, access: read-only, present: text}
      - {name: status, access: read-only, present: choice}
      - {name: queued_at, access: read-only, present: instant}
      - {name: started_at, access: read-only, present: instant}
      - {name: ended_at, access: read-only, present: instant}
      - {name: usage, access: read-only}
      - {name: error, access: read-only}
      - {name: cancelled_by, access: read-only, present: text}
      - {name: trace_id, access: read-only, present: text}
    operations:
      list: {capability: "execution:read", binds: ListRuns, items: runs, filters: [definition, definition_kind, agent, parent, status, owner, schedule, organisation]}
      get: {capability: "execution:read", binds: GetRun}
    verbs:
      - name: cancel
        capability: "execution:operate"
        step_up: true
        binds: CancelRun
        transition: cancel
        preconditions:
          - the run is queued, running or waiting
        in_flight:
          handling: cancels
          says: no further phase starts; a dispatched step is cancelled at its target, a model's turn under way is abandoned with the usage its backend reported recorded, a tool call already sent runs to its end and is recorded with its outcome, and every open wait closes cancelled
        effect: the run is cancelled, cancelled_by names the person's identity id, ended_at is set, and its timers are cancelled
        reversible: false
      - name: retry
        capability: "execution:operate"
        binds: RetryRun
        preconditions:
          - the run is failed or cancelled
          - its definition's owner still answers get_workflow for it
        in_flight:
          handling: none
          says: a failed or cancelled run has no work under way
        effect: a new run of the same definition is queued, starting at the phase this one failed or was cancelled at, with parent this run, trigger person and triggered_by the person's identity id; this run is unchanged
        reversible: false
    states:
      initial_state: queued
      entity_type: Run
      state_field: status
      states:
        queued: {description: accepted and not yet started}
        running: {description: a phase is under way}
        waiting: {description: a phase waits on a person and none is running}
        completed: {description: every phase finished, terminal: true}
        failed: {description: "a phase failed and its on_error fails the run, or it timed out", terminal: true}
        cancelled: {description: a person or the definition's owner stopped it, terminal: true}
        withheld: {description: "it reached a person's phase while muted, and stopped there", terminal: true}
      transitions:
        - {name: start, from: queued, to: running, trigger: the run is dispatched, description: its first phase starts}
        - {name: wait, from: running, to: waiting, trigger: a wait opens and no phase is running, description: it stops until a person decides}
        - {name: resume, from: waiting, to: running, trigger: a person decides a wait at DecideWait, description: the next phase starts}
        - {name: complete, from: running, to: completed, trigger: the last phase completes, description: it ends well}
        - {name: fail, from: [running, waiting], to: failed, trigger: a phase fails or the run times out, description: it ends badly}
        - {name: withhold, from: running, to: withheld, trigger: a person's phase opens in a muted run, description: nothing reaches anyone}
        - {name: cancel, from: [queued, running, waiting], to: cancelled, trigger: manual, description: a person stops it}
    events: [created, running, waiting, completed, failed, cancelled, withheld, retry]
    relations:
      - {relation: run_by, to: agent, field: agent}
      - {relation: spawned_by, to: run, field: parent}
      - {relation: fired_by, to: schedule, field: schedule}

  - kind: run-step
    owner: execution
    type: RunStep
    identity: {field: uid, form: minted}
    label: name
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: run, access: read-only, present: reference, kind: run}
      - {name: seq, access: read-only, present: number}
      - {name: step_type, access: read-only, present: choice}
      - {name: name, access: read-only, present: text}
      - {name: status, access: read-only, present: choice}
      - {name: started_at, access: read-only, present: instant}
      - {name: ended_at, access: read-only, present: instant}
      - {name: backend, access: read-only, present: text}
      - {name: model, access: read-only, present: text}
      - {name: usage, access: read-only}
      - {name: content, access: read-only, present: text}
      - {name: reason, access: read-only, present: text}
      - {name: approval, access: read-only, present: text}
      - {name: wait, access: read-only, present: reference, kind: wait}
      - {name: error, access: read-only}
      - {name: span_id, access: read-only, present: text}
    operations:
      list: {capability: "execution:read", filters: [run, step_type, status]}
      get: {capability: "execution:read"}
    events: [created, updated]
    relations:
      - {relation: part_of, to: run, field: run}

  - kind: tool-call
    owner: execution
    type: RunToolCall
    identity: {field: uid, form: minted}
    label: tool
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: run, access: read-only, present: reference, kind: run}
      - {name: step, access: read-only, present: reference, kind: run-step}
      - {name: tool, access: read-only, present: text}
      - {name: provider_call_id, access: read-only, present: text}
      - {name: arguments, access: read-only}
      - {name: outcome, access: read-only, present: choice}
      - {name: refused_with, access: read-only, present: text}
      - {name: result_digest, access: read-only, present: text}
      - {name: started_at, access: read-only, present: instant}
      - {name: ended_at, access: read-only, present: instant}
      - {name: span_id, access: read-only, present: text}
    operations:
      list: {capability: "execution:read", filters: [run, step, tool, outcome]}
      get: {capability: "execution:read"}
    events: [created, updated]
    relations:
      - {relation: part_of, to: run-step, field: step}

  - kind: wait
    owner: execution
    type: Wait
    identity: {field: uid, form: minted}
    label: title
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: run, access: read-only, present: reference, kind: run}
      - {name: step, access: read-only, present: reference, kind: run-step}
      - {name: kind, access: read-only, present: choice}
      - {name: title, access: read-only, present: text}
      - {name: activity, access: read-only, present: text}
      - {name: positions, access: read-only, present: list}
      - {name: approval_order, access: read-only, present: choice}
      - {name: escalated_to, access: read-only, present: text}
      - {name: due_at, access: read-only, present: instant}
      - {name: opened_at, access: read-only, present: instant}
      - {name: closed_at, access: read-only, present: instant}
      - {name: holders, access: read-only, present: choice}
      - {name: announced, access: read-only, present: boolean}
      - {name: state, access: read-only, present: choice}
      - {name: decisions, access: read-only, present: list}
      - {name: organisation, access: read-only, present: text}
    operations:
      list: {capability: "execution:read", binds: ListWaits, items: waits, filters: [state, run, organisation]}
      get: {capability: "execution:read", binds: GetWait}
    verbs:
      - name: decide
        capability: "execution:decide"
        binds: DecideWait
        body: WaitDecision
        preconditions:
          - the wait is open and its run is not muted
          - the position the body names is one the wait still awaits, or its escalation position once it has escalated, and in a sequential approval it is that position's turn
          - the person on the pass holds that position at the run's organisation, as the position register reads now
          - for an accept, the person neither started the run nor completed a task the approval follows
        in_flight:
          handling: none
          says: a wait has no work under way; the run is waiting on it
        effect: the decision is recorded on the wait; a complete, a decline, a reject, or the last accept closes it, and the run's next phase starts or the phase fails as its on_error says
        reversible: false
    states:
      initial_state: open
      entity_type: Wait
      state_field: state
      states:
        open: {description: awaiting a person}
        completed: {description: the task was done, terminal: true}
        declined: {description: the task was declined, terminal: true}
        accepted: {description: every awaited position accepted, terminal: true}
        rejected: {description: an awaited position rejected, terminal: true}
        cancelled: {description: its run was cancelled, terminal: true}
        withheld: {description: it opened in a muted run and reached nobody, terminal: true}
      transitions:
        - {name: complete, from: open, to: completed, trigger: a holder of the responsible position decides complete, description: the phase completes}
        - {name: decline, from: open, to: declined, trigger: a holder of the responsible position decides decline, description: the phase fails}
        - {name: accept, from: open, to: accepted, trigger: the last awaited position decides accept, description: the phase completes}
        - {name: reject, from: open, to: rejected, trigger: an awaited position decides reject, description: the phase fails}
        - {name: cancel, from: open, to: cancelled, trigger: its run is cancelled, description: nothing more is awaited}
        - {name: withhold, from: open, to: withheld, trigger: it opens in a muted run, description: nobody is told}
    events: [created, updated, decide, completed, declined, accepted, rejected, cancelled, withheld]
    relations:
      - {relation: part_of, to: run-step, field: step}

  - kind: timer
    owner: execution
    type: Timer
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: kind, access: read-only, present: choice}
      - {name: run, access: read-only, present: reference, kind: run}
      - {name: wait, access: read-only, present: reference, kind: wait}
      - {name: schedule, access: read-only, present: reference, kind: schedule}
      - {name: due_at, access: read-only, present: instant}
      - {name: state, access: read-only, present: choice}
    operations:
      list: {capability: "execution:read", filters: [kind, run, wait, schedule, state]}
      get: {capability: "execution:read"}
    events: [created, fired, cancelled]
    relations:
      - {relation: owed_by, to: run, field: run}
      - {relation: owed_by, to: wait, field: wait}
      - {relation: owed_by, to: schedule, field: schedule}
    states:
      initial_state: pending
      entity_type: Timer
      state_field: state
      states:
        pending: {description: its instant has not come}
        fired: {description: its instant came and what it owed was done, terminal: true}
        cancelled: {description: what it was owed for ended first, terminal: true}
      transitions:
        - {name: fire, from: pending, to: fired, trigger: its instant passes, description: the start fires, the phase times out, the retry is sent, the due passes or the escalation fires}
        - {name: cancel, from: pending, to: cancelled, trigger: its run, wait or schedule ends or changes, description: nothing is owed}

  - kind: schedule
    owner: execution
    type: Schedule
    identity: {field: uid, form: minted}
    label: key
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: owner, access: read-only, present: text}
      - {name: key, access: read-only, present: text}
      - {name: definition, access: read-only, present: text}
      - {name: organisation, access: read-only, present: text}
      - {name: state, access: read-only, present: choice}
      - {name: muted, access: read-only, present: boolean}
      - {name: held, access: read-only, present: number}
      - {name: dropped, access: read-only, present: number}
      - {name: missed, access: read-only, present: list}
      - {name: next_fire, access: read-only, present: instant, volatile: true}
      - {name: last_run, access: read-only, present: reference, kind: run}
    operations:
      list: {capability: "execution:read", binds: ListSchedules, items: schedules, filters: [owner, state, organisation]}
      get: {capability: "execution:read", binds: GetSchedule}
    events: [created, updated, deleted]
    relations:
      - {relation: starts, to: workflow-definition, field: definition}

  - kind: workflow-definition
    owner: execution
    type: FetchedDefinition
    identity: {field: uid, form: minted}
    label: name
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: owner, access: read-only, present: text}
      - {name: name, access: read-only, present: text}
      - {name: digest, access: read-only, present: text}
      - {name: fetched_at, access: read-only, present: instant}
      - {name: definition, access: read-only}
    operations:
      list: {capability: "execution:read", filters: [owner, name]}
      get: {capability: "execution:read"}
    events: [created, updated]
    relations: []
```

**What changed in moving the run kinds here**, so that the move is reviewable:

- `list` and `get` on `run`, `run-step` and `tool-call` need `execution:read`,
  not `admin:read`, and `cancel` and `retry` need `execution:operate`, not
  `action:invoke`. The acts are in the `execution` family execution holds,
  which [`schemas/resource`](../schemas/resource.md#verbs) requires a verb to
  name; and it lets `operator`, which carries `execution:operate` and not
  `action:invoke`, stop and retry a run
  ([`architecture/admin`](admin.md#operator-roles)).
- `run` binds `ListRuns`, `GetRun`, `CancelRun` and `RetryRun`; `run-step`
  and `tool-call` bind nothing and are served at the uniform address.
- `run` gains `owner`, `organisation`, `project`, `schedule`, `chain` and
  `muted`, the state `withheld`, and the relation `fired_by`; `run-step`
  gains `wait`, and `step_type` gains `task`
  ([`protocol/types`](../protocol/types.md#run)).
- `retry` keeps its meaning there: a new run with this one as `parent`.
- `unavailable` is gone: the owner is specified.

**`GET /v1/admin/workflows` is a view of the same ledger, not a second
record.** It answers [`architecture/admin`](admin.md#get-v1adminworkflows)'s
`WorkflowExecution` shape, projected from a `Run` and its `RunStep`s by one
rule: `id` is the run's `uid`; `workflow_name` its `definition`;
`domain_name` the owner's name where the owner is a domain controller, and
absent otherwise; `task_id` absent; `status` the run's, with `queued` written
`pending`; `phases` its `phase`, `task` and `approval` steps, each a
`PhaseResult` named by the step's `name`; and `started_at` and
`completed_at` its `started_at` and `ended_at`. Its states are the run's,
since [`patterns/workflow`](../patterns/workflow.md#workflow-state-machine)
names the same ones. Neither route has a rule of its own: each reads the
ledger the `run` kind reads.

**Some acts are not a person's verbs.** Registering, changing, pausing,
resuming, running now and withdrawing a start are its owner's, on the owner's
registration token ([Who May Do What](#who-may-do-what) rule 3), so `schedule`
declares no `create`, `update`, `delete` or verb: a person reaches those acts
through the owner, such as the programme service's pause and run routes, and
the uniform address offers none. A timer, a step, a tool call and a fetched
definition are records, and declare reads alone.

---

## Configuration

```yaml
execution:
  tick_interval: 15s          # how often clock starts and timers are evaluated,
                              # where the platform runs a resident process
  coalesce_window: 60s        # on facts arriving within it start one run
  max_in_flight: 200          # machine steps dispatched at once, across targets
  default_phase_timeout: 300  # seconds, for a machine phase that names none
  run_retention: 400d         # how long an ended run is kept
  dead_letter_retention: 30d
```

A start, a definition, a position and a switch are never configuration: each
is registered by its owner or read from the tenant at run time.

---

## Security

```yaml
security:
  trust_model:
    description: |
      Execution trusts a person's authority only on a pass, an owner's only
      on its own registration token, and runs unattended work only under its
      owner's authority on a service pass. It holds no person's token and
      never runs work as the person who started or switched it on. It decides
      nothing: every wait is closed by a person holding the position it names.

  boundaries:
    - boundary: Person → Execution. Only through the admin gateway, on a pass
        addressed here. An operator token is refused
    - boundary: Owner → Execution. Registers, switches and withdraws its own
        starts on its own registration token, and reaches no other owner's
    - boundary: Execution → Owner. get_workflow and the owner's own phases,
        on execution's registration token
    - boundary: Execution → Target component. A machine phase on a service
        pass for the definition's owner, addressed to that target alone
    - boundary: Execution → Content. Reads the position register. Writes
        nothing

  enforcement:
    - rule: No machine decides
      mechanism: execution:decide is person only and admitted on a pass only;
        no event, action or output closes a wait
    - rule: One authority per start
      mechanism: Schedule routes admit only the owner's registration token
    - rule: Unattended work never borrows a person's or execution's authority
      mechanism: A step to another component goes on a service pass for the
        owner, or is not dispatched
    - rule: Nothing a muted run produces reaches a person
      mechanism: A muted run's wait is withheld, unannounced and unlisted
    - rule: A wait is never decided by someone shown to hold nothing
      mechanism: Holder resolution is required for every position-named wait
```

---

## Implementation Notes

- Persist the ledger before acting on it: a run is recorded before its first
  dispatch, a step before it is sent, a decision before the run advances. A
  restart resumes every run from its ledger; a step in flight at the restart
  is retried as its `on_error` says.
- The definition is fetched once per run and its digest recorded on the
  run, so a person can tell which version of a definition a run followed.
  Cache definitions as [`patterns/workflow`](../patterns/workflow.md#implementation-notes)
  says.
- A wait's due and escalation are timers in the same wheel as clock starts,
  so one evaluation cycle owes them all.
- Report a run that did nothing as such: a fired start whose definition
  could not be fetched is a `failed` run, never an absent one.
- Serve `GET /v1/admin/workflows` from the ledger by the one projection
  [Resources](#resources) states, never from a store of its own.

---

## Verification Checklist

- [ ] Every route in [Endpoints](#endpoints) but `PUT` and `DELETE` on a schedule and its three switching routes, `POST /v1/event`, `POST /v1/services`, `GET /livez` and `GET /readyz` is declared among the manifest's `pass_routes` with the one capability its row gives, and `GET /v1/execution/waits` carries the `inbox` [Endpoints](#endpoints) shows ([Endpoints](#endpoints))
- [ ] An operator token on any route is refused with `PASS_REQUIRED` ([Who May Do What](#who-may-do-what) rule 1, [Error Handling](#error-handling))
- [ ] The manifest declares `execution:read`, `execution:operate`, `execution:register` and `agent:message`, and never `execution:decide` ([Endpoints](#endpoints))
- [ ] `POST /v1/execution/waits/{wait}/decision` on a registration token carrying `execution:decide` claims is refused with `FORBIDDEN`, and the wait stays `open` ([Who May Do What](#who-may-do-what) rule 2, [Error Handling](#error-handling))
- [ ] Publishing `workflow.approval.decision` to the service closes no wait ([Who May Do What](#who-may-do-what) rule 2)
- [ ] A decision as a position the person on the pass does not hold is refused with `EXECUTION_NOT_A_HOLDER` ([Deciding](#deciding), [Error Handling](#error-handling))
- [ ] In a sequential approval, a decision as the second position before the first has accepted is refused with `EXECUTION_DECISION_OUT_OF_ORDER` ([Deciding](#deciding), [Error Handling](#error-handling))
- [ ] An approval accepted by the person who completed the task it follows is refused with `APPROVAL_SELF_DENIED` ([Deciding](#deciding) step 3, [Error Handling](#error-handling))
- [ ] While the position register cannot be read, a decision on a wait naming a position is refused with `EXECUTION_POSITION_UNRESOLVED`, and `GET /v1/execution/waits?for=me` lists that wait with `holders` `unresolved` rather than answering an empty list ([Who holds a position](#who-holds-a-position), [Error Handling](#error-handling))
- [ ] An approval with two `approvers` closes `accepted` only after a holder of each accepts, and `rejected` on the first reject ([Deciding](#deciding) step 5)
- [ ] A task's escalation timer fires `after` past its `due`, adds `to`, and publishes `execution.wait.escalated` once ([A person's phase](#a-persons-phase) step 4, [Escalating](#escalating))
- [ ] A run of a muted start runs its machine phases, records its first wait `withheld`, lists it nowhere, announces it to nobody, and ends `withheld` ([Muted runs](#muted-runs))
- [ ] A decision on a wait of a muted run is refused with `EXECUTION_MUTED` ([Error Handling](#error-handling), [Muted runs](#muted-runs))
- [ ] `PUT /v1/execution/schedules/{schedule}` on a pass is refused with `FORBIDDEN`, and on another owner's schedule key from a second registration token is refused with `FORBIDDEN` ([Who May Do What](#who-may-do-what) rule 3, [Error Handling](#error-handling))
- [ ] Registering the same owner's start twice under one key creates one `Schedule` ([Registering a start](#registering-a-start))
- [ ] A `ScheduleRegistration` carrying both `clock` and `on` is refused with `INVALID_REQUEST` ([Error Handling](#error-handling), [Types](#types))
- [ ] A paused `for` start holds each added row and delivers it on resume, one run per row; a paused `on` start drops facts and counts them in `dropped` ([Firing](#firing) step 3)
- [ ] A `for` row whose chain already holds a run of the same definition starts nothing ([Firing](#firing) step 2)
- [ ] A `workflow.trigger` whose envelope `source` differs from its `source_domain` starts no run ([Firing](#firing) step 1)
- [ ] While no service pass can be obtained, a phase targeting a component other than the definition's owner is recorded `failed` with `EXECUTION_PASS_UNAVAILABLE` and is never sent on the service's own registration token ([Unattended authority](#unattended-authority))
- [ ] A `does:` phase of a programme workflow is sent to the programme service on `POST /v1/message` on the service's own registration token ([Running a machine phase](#running-a-machine-phase) step 2)
- [ ] Time a run spends `waiting` counts towards no phase or run timeout ([A person's phase](#a-persons-phase) step 5)
- [ ] `POST /v1/execution/runs/{run}/retry` on a `completed` run is refused with `INVALID_STATE`; on a `failed` run it queues a new `Run` whose `parent` is that run, starting at the phase it failed at, and leaves that run unchanged ([Cancelling and retrying](#cancelling-and-retrying), [Error Handling](#error-handling))
- [ ] `record_turn` from any agent but the one a running step was dispatched to is refused with `FORBIDDEN`, and one from that agent records a `model-turn` `RunStep` and its `RunToolCall`s with the usage the backend reported, absent where it reported none ([Interfaces](#interfaces))
- [ ] The run kind's `list` at the uniform address and `GET /v1/admin/workflows` describe the same runs, the second by the projection [Resources](#resources) states, with `queued` written `pending` ([Resources](#resources))
- [ ] `cancel` on a `run` through the admin gateway's uniform address without a recent step-up is refused with `STEP_UP_REQUIRED` and the run continues ([Resources](#resources); [`architecture/admin`](admin.md#writes-and-what-guards-them))
- [ ] `POST /v1/execution/runs/{run}/cancel` closes every open wait `cancelled` and ends the run `cancelled`, keeping the run in the ledger ([Cancelling and retrying](#cancelling-and-retrying))
- [ ] `GET /v1/admin/workflows` on a pass carrying `admin:read` answers the shape [`architecture/admin`](admin.md#get-v1adminworkflows) gives, with `domain_name` absent on a programme's run ([Endpoints](#endpoints), [Implementation Notes](#implementation-notes))
- [ ] A `Wait` returned by any route carries no step output ([Types](#types))
- [ ] Each decision is recorded on its wait and in an `AuditEntry` with the pass's `identity_id` as `actor` and its `act.identity_id` as `via` ([Deciding](#deciding) step 4, [Who May Do What](#who-may-do-what))
