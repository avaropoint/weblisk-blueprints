<!-- blueprint
type: architecture
name: programme-service
version: 2.2.0
requires: [protocol/types, protocol/identity, patterns/workflow, patterns/messaging, patterns/scope, architecture/content, architecture/orchestrator, architecture/admin, architecture/execution, architecture/notification]
platform: any
tier: free
adoption: opt-in
-->

# Weblisk Programme Service

The tenant service that holds the standing work an adopted programme brings:
its operations, its workflows and its notices. It answers what is due — the
occurrences each obligation in force owes, which are late and whose they are,
and how ready each programme is — and it publishes the facts that work reacts
to. It also states what it hands to execution, notification and the prompt
worker, and how a person's decisions reach the admin gateway's one inbox.

## Overview

[`schemas/programme.md`](../schemas/programme.md#the-package--what-a-programme-brings-besides-its-documents)
declares a programme's package and gives each block an owner. Content holds
the documents, forms and skills. Everything else in the table goes to the
**programme service**, which keeps it, and to the services that service hands
the work to:

| what | held by | run or delivered by | specified |
|---|---|---|---|
| an installed operation | the programme service | execution holds its starts — its clock and the facts it reacts to — and runs it; the programme service runs its `does:` | here, [Endpoints](#endpoints), and [`architecture/execution`](execution.md) |
| an installed workflow definition | the programme service | execution holds its starts, runs, waits and timers | here, [`patterns/workflow`](../patterns/workflow.md) for the definition, and [`architecture/execution`](execution.md) |
| an installed notice | the programme service | notification tells each position's holders, each their own way | here, [Notification](#notification), and [`architecture/notification`](notification.md) |
| an `agent:` instruction | the programme service records it on its operation or step | the prompt worker runs it | here, [The prompt worker](#the-prompt-worker), and [`architecture/prompt-worker`](prompt-worker.md) |
| an obligation in force, and what it owes | the document that declares it, in content | the programme service answers what is due, and announces what advances | here, [What Is Due](#what-is-due) |
| a decision a person owes | the owner whose work waits on it | a person, through the admin gateway's one inbox | here, [The decision inbox](#the-decision-inbox) |

This document is the home of the programme service's routes, the capability
each route needs, the rule for what only a person may do (and on which
token), what is due and how it is computed, the events it publishes, the
`does:` actions it runs, and the contract each neighbouring service is
handed. The fields a programme author writes, their vocabularies and their
refusals belong to [`schemas/programme.md`](../schemas/programme.md), and are
not restated here.

> **Scope boundary.** Execution is [`architecture/execution`](execution.md),
> the service [`architecture/domain`](domain.md) names: cron, task and
> workflow merged into one. Notification is
> [`architecture/notification`](notification.md), the prompt worker
> [`architecture/prompt-worker`](prompt-worker.md) and the model service
> [`architecture/model-service`](model-service.md). This document states what each is
> handed, and never how it does its own work. A tenant that does not run one
> of them is told so by name, item by item ([Installing](#installing)).

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    # 6.4.0 is where programme:dispatch, programme:notify and
    # PROGRAMME_ITEM_NOT_RUNNING are registered; AuditEntry's authorisation
    # and run are 6.2.0's
    version: ">=6.4.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category, retryable]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, via, authorisation, run, action, target, status]
        # pass_routes is how the admin gateway learns which of these routes a
        # person's request may reach, and what each needs. publishes claims the
        # three namespaces of Events it publishes; subscriptions are Events it
        # hears. See Registration and Standalone Operation
        - name: AgentManifest
          fields_used: [name, capabilities, pass_routes, publishes, subscriptions]
        - name: PassRoute
          fields_used: [method, path, capabilities]
        - name: Subscription
          fields_used: [pattern, scope]
        - name: Capability
          fields_used: [name, resources]
        - name: ServiceDirectory
          fields_used: [services, updated_at, signature]
        - name: ServiceEntry
          fields_used: [name, capabilities, lease_state]
        - name: WorkAuthorisation
          fields_used: [id, owner, definition, actors, capabilities, not_after]
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    # 3.1.0 is where the work pass, and its definition and run claims, exist
    version: ">=3.1.0 <4.0.0"
    bindings:
      types:
        # type and aud say a person's request reached this service on a pass
        # addressed to it, or a firing reached it on a work pass; cap is what it
        # may use; identity_id names who acted; act names the gateway or the
        # actor that carried it; definition and run are a work pass's
        - name: WLToken
          fields_used: [type, aud, act, cap, identity_id, cid, definition, run]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/workflow
    version: ">=4.0.0 <5.0.0"
    bindings:
      types:
        # What an installed workflow becomes, and what execution answers
        # get_workflow with (schemas/programme.md, How a workflow maps)
        - name: WorkflowDefinition
          fields_used: [name, description, trigger, phases]
        - name: WorkflowPhase
          fields_used: [name, agent, action, input, depends_on, approval, approvers, approval_order, task, escalate]
        - name: WorkflowTask
          fields_used: [activity, responsible, due]
        - name: WorkflowEscalation
          fields_used: [after, to]
        - name: WorkflowExecution
          fields_used: [id, workflow_name, status, phases, started_at, completed_at]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/messaging
    version: ">=3.0.0 <4.0.0"
    bindings:
      types:
        # Every fact it publishes, and every content event it hears
        - name: EventEnvelope
          fields_used: [event_id, topic, source, scope, correlation_id, timestamp, version, payload]
      behaviors:
        - name: event-publishing
        - name: event-subscribing
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/scope
    version: ">=2.3.0 <4.0.0"
    bindings:
      types:
        # A register's recorded scope decides whether a row's cells or a
        # subject's label may leave this service (What a person is answered)
        - name: ScopeLevel
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/content
    version: ">=4.0.0 <6.0.0"
    bindings:
      types:
        # The adopted map, adoption.md, every document that declares an
        # obligation and every register are read from content, never copied
        - name: ContentEntry
          fields_used: [path, identity, scope]
        - name: ContentRepository
          fields_used: [id, scope_path, records]
        # Who wrote a register row, and on which run (Hearing a row)
        - name: ContentChange
          fields_used: [path, actor, proposal, statement]
        - name: ContentProposal
          fields_used: [id, actor, agent, run]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/orchestrator
    # 4.2.0 is where the orchestrator holds work authorisations and mints
    # work passes (work-exchange)
    version: ">=4.2.0 <5.0.0"
    bindings:
      behaviors:
        # What a pass this service accepts rests on. Relied on, never called
        - name: token-exchange
          usage: Every pass this service accepts was minted by the exchange, for an operator token the orchestrator judged live then, carrying no capability the person could not use then
        # What a work pass this service accepts, or its actors carry, rests on
        - name: work-exchange
          usage: Relied on, never called by this service for itself, except as an actor of a does item it runs. Every work pass it accepts was minted under a live work authorisation a person made for one installed item
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/admin
    version: ">=4.0.0 <6.0.0"
    bindings:
      behaviors:
        # The one door a person's request arrives through
        - name: admin-gateway-authorization
          usage: Relied on, never called here. A person's request reaches this service only on a route its manifest declares among pass_routes, on a pass naming every capability that route declares
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/execution
    # 1.2.0 is where RunScheduleNow takes a RunNow, and InstructionTask
    # carries the programme and the item
    version: ">=1.2.0 <2.0.0"
    bindings:
      types:
        # Every installed operation's and workflow's start is registered and
        # switched at execution, on this service's registration token holding
        # execution:register: PUT and DELETE /v1/execution/schedules/{schedule},
        # and its /pause, /resume and /runs (Registering the starts)
        - name: ScheduleRegistration
          fields_used: [definition, organisation, project, clock, on, when, for, state, muted]
        - name: Clock
          fields_used: [cadence, local_time, weekday, day, timezone]
        - name: Condition
          fields_used: [event, where, within, across, count]
        - name: RecordStart
          fields_used: [records]
        - name: Schedule
          fields_used: [uid, key, state, muted, held, dropped, missed, next_fire]
        # What an agent: phase's input carries: the instruction, its
        # ceiling, the adopted map and the programme's skills, each file a
        # ContentRef (The prompt worker)
        - name: InstructionTask
          fields_used: [instruction, source, needs, skills, programme, item]
        - name: ContentRef
          fields_used: [repository, path]
        # A run agent work asks for: POST /v1/execution/schedules/{schedule}/runs
        # with the asking run as parent (What agent work may start and tell)
        - name: RunNow
          fields_used: [parent, not_before, muted, reason]
        - name: RunNowResult
          fields_used: [run, timer, muted]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/notification
    # 1.2.0 is where agent work is told under its own item
    version: ">=1.2.0 <2.0.0"
    bindings:
      types:
        # How a notice that advanced, an occurrence that advanced, and what an
        # agent: item's work asked to say are told: NotifyByPosition, on this
        # service's registration token (Telling)
        - name: NotifyRequest
          fields_used: [authorisation, run, organisation, project, notice, positions, says, why, fact]
        - name: Notification
          fields_used: [id, outcome]
        - name: NoticeRef
          fields_used: [programme, id]
        - name: NoticeFact
          fields_used: [event, occurred_at, obligation, subject, due_at]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
 person ──► admin gateway ──pass──► programme service ──► content (the map, adoption.md,
                  ▲                    │      ▲  ▲          obligations, registers)
                  │                    │      │  │
                  │       definitions, │      │  └── content.changed (a register moved)
                  │       clocks,      │      │
                  │       starts       ▼      │ get_workflow, a does: action
                  │                  execution ──► prompt worker ──► model service
                  │                    │    (an agent: phase)         (architecture/model-service)
          one     │                    │
          inbox ◄─┴── decisions        └──► (a run's result)
          (owners serve their own)
                                       programme service ──publish──► obligation.* · register.* · programme.*
                                                         ──notify───► notification
```

- **The programme service holds and never runs a definition.** It keeps each
  installed operation, workflow and notice, with its state. It registers each
  operation's and workflow's starts at execution and switches them there, and
  serves execution the definitions. It runs its own `does:` actions when
  execution invokes them.
- **It answers what is due from the documents, never from a table of tasks.**
  Every obligation in force is read from the document that declares it, every
  occurrence is derived from the obligation and the register it records into,
  and nothing about either is stored. What it keeps is what it has already
  announced, so that nothing is announced twice ([What it keeps](#what-it-keeps)).
- **It publishes the facts work reacts to**, because it is the one service
  that can see them: an occurrence advancing, a register gaining a row, a
  programme being adopted.
- **Execution runs and never holds a programme.** It holds every start an
  owner registers — a clock, the facts an `on:` names, a `when:` count, a
  `for:` register — fires them, and keeps every run in its one run ledger
  ([`architecture/execution`](execution.md)). It fetches a definition
  from its owner with `get_workflow`, as it fetches a domain's.
- **Notification tells and never decides who.** It is given positions and a
  message. Who holds a position, and how each holder wants to be told, are
  not the programme's to decide.
- **The prompt worker answers and never keeps.** It runs one `agent:`
  instruction under a ceiling. What it produces is written through an owner's
  API, and the run is execution's record, not the worker's.

## Responsibilities

### Owns

- Each installed operation, workflow definition and notice, at the scope of
  the organisation that adopted its programme, matched back to its programme
  and its `id` so that installing twice creates nothing twice
- Each installed item's two switches: **paused or running**, and **muted or
  unmuted**, and a schedule a person set in place of the map's
- Each installation: what it installed, what it could not hand to an owner,
  by block and `id`, with the missing service named, and the build plan that
  would hand it over ([`schemas/programme`](../schemas/programme.md#adoption-emits-a-build-plan))
- The `WorkflowDefinition` each installed workflow becomes, served to
  execution with `get_workflow`
- Running each `does:` action an operation or a workflow phase names, when
  execution invokes it ([The `does:` Actions](#the-does-actions))
- **What is due**: every obligation in force at an organisation, its
  occurrences and their states, what is late and whose it is, and
  readiness ([What Is Due](#what-is-due))
- Publishing the facts in [Events it publishes](#events-it-publishes), and
  registering each item's starts at execution
  ([Starting on a fact](#starting-on-a-fact))
- Deciding when a notice has advanced, and asking notification to tell its
  positions; and telling an obligation's `responsible` and `escalate.to`
  positions when one of its occurrences advances

### Does NOT Own

- **The programme's files.** The map, specs, forms, skills and `adoption.md`
  are content's. The adoption itself is the person's act that writes them
  ([`schemas/programme.md`](../schemas/programme.md#adopting-a-programme))
- **The obligation and the record.** Both are documents in content. This
  service reads them and derives; it writes no document, no row and no
  attestation
- **Runs, timers and waits.** They are execution's, in its one run ledger
- **Who holds a position, and how a person is told.** The first is tenant
  data in content. The second is each person's preference, held by
  notification
- **A model.** The prompt worker asks the tenant's model service
  ([`architecture/model-service`](model-service.md))
- **Any decision.** A decision belongs to the owner whose work waits on it,
  and only a person makes one ([The decision inbox](#the-decision-inbox))

---

## Endpoints

| Method | Path | Operation | Auth | Capability | Purpose |
|--------|------|-----------|------|------------|---------|
| POST | /v1/programme/installations | InstallProgramme | yes | `programme:install` | Install an adopted programme's operations, workflows and notices at its organisation, every one muted. Body `InstallationRequest`, answer `ProgrammeInstallation`. A pass only ([Who May Do What](#who-may-do-what)) |
| GET | /v1/programme/installations | ListInstallations | yes | `programme:read` | Installations at the organisation, each with every block not handed to its owner, by name, with the missing service, and its build plan. Answer `{installations: [ProgrammeInstallation]}` |
| GET | /v1/programme/installations/{programme} | GetInstallation | yes | `programme:read` | One programme's installation at the organisation, with its items, what was not handed over and its build plan as the tenant stands now |
| DELETE | /v1/programme/installations/{programme} | WithdrawProgramme | yes | `programme:install` | Withdraw everything installed under one programme at a scope when it is un-adopted. Stops them and records it. Deletes no document. A pass only |
| GET | /v1/programme/items | ListItems | yes | `programme:read` | Every installed item in scope, of every kind, each with its two switches, its schedule and its authorisation. Narrowed by `kind`, `programme`, `state` and `muted`. Answer `{items: [InstalledItem]}` |
| GET | /v1/programme/items/{uid} | GetItem | yes | `programme:read` | One installed item by its `uid` |
| GET | /v1/programme/operations | ListOperations | yes | `programme:read` | Installed operations in scope, each with its two switches and its next firing |
| GET | /v1/programme/operations/{id} | GetOperation | yes | `programme:read` | One operation, its declaration as installed, and its changes |
| POST | /v1/programme/operations/{id}/pause | PauseOperation | yes | `programme:operate` | Stop its clock. On an unmuted operation, a pass only |
| POST | /v1/programme/operations/{id}/resume | ResumeOperation | yes | `programme:operate` | Start its clock. On an unmuted operation, a pass only |
| POST | /v1/programme/operations/{id}/runs | RunOperation | yes | `programme:operate` | Run it once, now or at the body's `not_before`, from its start at execution. Body `ItemRun`, optional; answer `RunNowResult`. On an unmuted operation, a pass only, or a work pass from an `agent:` item of the same programme carrying `programme:dispatch` ([What agent work may start and tell](#what-agent-work-may-start-and-tell)) |
| POST | /v1/programme/operations/{id}/schedule | RescheduleOperation | yes | `programme:operate` | Set the clock it runs on in place of the map's, body `ItemSchedule`. On an unmuted operation, a pass only ([Rescheduling](#rescheduling)) |
| DELETE | /v1/programme/operations/{id}/schedule | RestoreOperationSchedule | yes | `programme:operate` | Return it to the map's clock. On an unmuted operation, a pass only |
| POST | /v1/programme/operations/{id}/mute | MuteOperation | yes | `programme:switch` | Withhold from people everything its runs produce |
| POST | /v1/programme/operations/{id}/unmute | UnmuteOperation | yes | `programme:switch` | Let its runs reach people |
| GET | /v1/programme/workflows | ListWorkflows | yes | `programme:read` | Installed workflow definitions in scope, each with its two switches |
| GET | /v1/programme/workflows/{id} | GetWorkflow | yes | `programme:read` | One definition, as the programme declared it and as execution is given it |
| POST | /v1/programme/workflows/{id}/pause | PauseWorkflow | yes | `programme:operate` | Start no new run. Runs already started continue. On an unmuted workflow, a pass only |
| POST | /v1/programme/workflows/{id}/resume | ResumeWorkflow | yes | `programme:operate` | Start runs again; execution delivers what it held while the workflow was paused. On an unmuted workflow, a pass only |
| POST | /v1/programme/workflows/{id}/runs | RunWorkflow | yes | `programme:operate` | Start one run of it, now or at the body's `not_before`, from its start at execution. Body `ItemRun`, optional; answer `RunNowResult`. On an unmuted workflow, a pass only, or a work pass from an `agent:` item of the same programme carrying `programme:dispatch` ([What agent work may start and tell](#what-agent-work-may-start-and-tell)) |
| POST | /v1/programme/workflows/{id}/schedule | RescheduleWorkflow | yes | `programme:operate` | Set the clock it starts on in place of the map's, body `ItemSchedule`. On an unmuted workflow, a pass only |
| DELETE | /v1/programme/workflows/{id}/schedule | RestoreWorkflowSchedule | yes | `programme:operate` | Return it to the map's clock. On an unmuted workflow, a pass only |
| POST | /v1/programme/workflows/{id}/mute | MuteWorkflow | yes | `programme:switch` | Withhold from people everything its runs produce |
| POST | /v1/programme/workflows/{id}/unmute | UnmuteWorkflow | yes | `programme:switch` | Let its runs reach people |
| GET | /v1/programme/notices | ListNotices | yes | `programme:read` | Installed notices, each with its mute switch, and each time one advanced: when, which positions, and whether notification accepted it |
| POST | /v1/programme/notices/{id}/mute | MuteNotice | yes | `programme:switch` | Withhold the notice from people. It still advances, and each advance is recorded as not sent |
| POST | /v1/programme/notices/{id}/unmute | UnmuteNotice | yes | `programme:switch` | Let the notice reach its positions the next time it advances |
| POST | /v1/programme/notifications | NotifyFromItem | yes | `programme:notify` | Tell the holders of positions the programme names what an `agent:` item's work says, under that item's work authorisation. Body `ItemNotice`, answer the `Notification` notification answered. A work pass only, never a pass ([What agent work may start and tell](#what-agent-work-may-start-and-tell)) |
| GET | /v1/programme/actions | ListActions | yes | `programme:read` | The `does:` actions this build runs, each with the capabilities it reads with. Answer `{actions: [ProgrammeAction]}` ([The `does:` Actions](#the-does-actions)) |
| GET | /v1/programme/obligations | ListObligations | yes | `programme:read` | Every obligation in force at the organisation and its projects, each with its counts of occurrences by state over the window, or why it is undeclarable. Answer `{obligations: [Obligation], not_read: [NotRead]}` |
| GET | /v1/programme/obligation | GetObligation | yes | `programme:read` | One obligation by `ref`, with its occurrences over the window `from`–`to` |
| GET | /v1/programme/occurrences | ListOccurrences | yes | `programme:read` | Occurrences over the window `from`–`to`, narrowed by `obligation`, `state`, `responsible`, `overdue` and `escalated`. Answer `{occurrences: [Occurrence], not_read: [NotRead]}` |
| GET | /v1/programme/occurrence | GetOccurrence | yes | `programme:read` | One occurrence by `ref` |
| GET | /v1/programme/due | DueList | yes | `programme:read` | What is due within `within` from now, and everything overdue whenever it fell due, most overdue first. Narrowed by `responsible`, `programme` and `project`. Answer `DueList` ([What is due](#what-is-due-now)) |
| GET | /v1/programme/readiness | GetReadiness | yes | `programme:read` | Each installed programme's readiness at the organisation: documented per tier, operating, and whether anything chases it. Narrowed by `programme` and `tier`. Answer `{programmes: [ProgrammeReadiness]}` ([Readiness](#readiness)) |
| POST | /v1/message | Message | yes | | The actions in [Interfaces](#interfaces), from execution on a work pass |
| POST | /v1/event | Event | yes | | The events in [Events it hears](#events-it-hears), delivered as [`patterns/messaging`](../patterns/messaging.md) delivers them |
| POST | /v1/services | Services | yes | | Accept the signed service directory the orchestrator pushes, as [`protocol/spec`](../protocol/spec.md#post-v1services) specifies |
| GET | /livez | Livez | no | | Liveness, for the supervisor that restarts the service |
| GET | /readyz | Readyz | no | | Readiness, for the supervisor waiting on its start |

**A notice has its own mute switch and no clock.** A notice is a block of its
own in the map, belonging to no operation or workflow
([`schemas/programme.md`](../schemas/programme.md#notices--who-is-told-what)),
so it is muted and unmuted by itself, and has nothing to pause or reschedule.

**Every request names its organisation and programme.** Installing names
both in its body. Every other route but `/livez`, `/readyz`, `/v1/message`,
`/v1/event` and `/v1/services` carries the organisation as the query parameter
`organisation`, which is required, and the due routes may add `project` to
narrow to one project under it. A route with `{id}` in its path also requires
the query parameter `programme`, a list route takes it to narrow the list,
and withdrawing and `GetInstallation` name the programme in their path. An
item's `id` is local to its programme
([`schemas/programme.md`](../schemas/programme.md#notices--who-is-told-what)),
so `{id}` alone names nothing: the item is the one with that programme, `id`
and organisation. A `uid` names one item alone. A route missing a parameter
it requires is refused with `INVALID_REQUEST`. Naming an organisation grants
nothing: the route's capability is checked as on any other request.

**A window is two instants.** `from` and `to` are instants as
[`protocol/conventions`](../protocol/conventions.md) writes them. Absent,
`to` is now and `from` is `status_window` before it
([Configuration](#configuration)). `within` is a duration, `<n>d` or `<n>h`,
and absent is `due_soon_window`. A window longer than `max_window` is refused
with `INVALID_REQUEST`.

Each route in the table but `/livez`, `/readyz`, `/v1/message`, `/v1/event`,
`/v1/services` and `NotifyFromItem` is declared among the manifest's `pass_routes`, with the
one capability in its row and no body requirement. The admin gateway carries
a person's request here only on a route that list declares
([`architecture/admin`](admin.md#contracts),
`admin-gateway-authorization`), so the list and the table MUST agree.

**`pass_routes` is not the only way in.** The pause, resume, run, reschedule
and restore routes of an operation or a workflow also admit a registered
component's own registration token carrying `programme:operate`, and a work
pass whose `cap` carries it, while the item is muted
([Who May Do What](#who-may-do-what), rule 3). An `agent:` item's own work,
on a work pass, also reaches the due, occurrence, obligation and readiness
routes with `programme:read`, the two run routes with `programme:dispatch`,
and `NotifyFromItem`, which admits nothing else, with `programme:notify`
([What agent work may start and tell](#what-agent-work-may-start-and-tell)).
Every other route admits a pass only. `/v1/message` admits a work pass only
([Interfaces](#interfaces)); `/v1/event` and `/v1/services` admit what
[`patterns/messaging`](../patterns/messaging.md) and
[`protocol/spec`](../protocol/spec.md#post-v1services) admit there.

The service declares `programme:read`, `programme:install`,
`programme:operate`, `programme:dispatch`, `programme:notify`, `content:read`, `content:describe`, `content:propose`,
`fabric:read`, `fabric:observe`, `work:exchange`, `execution:register`, `notification:send`,
`agent:message` and `event:observe` on its manifest. The content and fabric
names are there because a work pass under an item's authorisation carries
only what its owner's manifest declares as well
([`protocol/identity`](../protocol/identity.md#the-work-pass)): without
`content:propose` no `agent:` item could propose a change, without
`fabric:observe` none could propose a relationship, and without
`content:read` and `content:describe` notification could read no holder.
`execution:register` registers its starts, `notification:send` asks
notification to tell, and `event:observe` hears content's events at scope
`*`. It checks `programme:switch` but never holds it, as
[`protocol/types`](../protocol/types.md#capability) requires of a person-only
capability.

---

## Interfaces

**Actions it answers** on [`POST /v1/message`](../protocol/spec.md#post-v1message),
from execution alone, on a work pass whose `identity_id` is this service's own
and whose `definition` names an item installed here now. Any other token, and
a work pass naming no such item, is refused, the second with `NOT_FOUND`
([`protocol/identity`](../protocol/identity.md#the-work-pass) rule 11):

| action | answers |
|---|---|
| `get_workflow` | The `WorkflowDefinition` an installed workflow became, as [`patterns/workflow`](../patterns/workflow.md) Phase 2 fetches one from its source. A withdrawn workflow answers `NOT_FOUND` |
| any action a `does:` names | Runs that deterministic action for the operation or phase, and answers its outcome ([The `does:` Actions](#the-does-actions)). A name this build does not run answers `NOT_FOUND`, never success |

### Events it publishes

This service claims the namespaces `obligation.*`, `register.*` and
`programme.*` on its manifest's `publishes`, and publishes each topic below
as [`patterns/messaging`](../patterns/messaging.md) `event-publishing` does,
with `scope` `"*"`. These are the facts a programme's `on:`, `when:` and
`for:` name ([`schemas/programme`](../schemas/programme.md#on--reacting-to-a-fact-instead-of-to-the-clock)),
under the topic each word is published as. Execution hears them for the
starts it holds ([`architecture/execution`](execution.md#interfaces)):

| Topic | The programme's word | Published when | Payload |
|---|---|---|---|
| `obligation.due_soon` | `obligation.due_soon` | An occurrence first falls inside `due_soon_window` and is not yet recorded ([How an occurrence advances](#how-an-occurrence-advances)) | `ObligationAdvanced` |
| `obligation.overdue` | `obligation.overdue` | An occurrence first becomes overdue, or an overdue lapse's outstanding count first crosses a step | `ObligationAdvanced` |
| `obligation.escalated` | `obligation.escalated` | An overdue occurrence first passes its obligation's `escalate.after` | `ObligationAdvanced` |
| `obligation.attested` | `attestation` | An occurrence first reads `attested` | `ObligationAdvanced` |
| `register.row_added` | `register.row_added` | A row arrives in a register an installed item hears ([Hearing a row](#hearing-a-row)) | `RowAdded` |
| `programme.adopted` | `adopted` | An installation is first recorded for a programme at an organisation, and not on a repeat | `ProgrammeAdopted` |

A topic is published only from what a sweep or a delivery observed, never from
a person's read: reading what is due changes nothing and announces nothing.
An event names an occurrence, a row or an installation by its identity, and
carries no cell of a register above `internal`
([What a person is answered](#what-a-person-is-answered)).

### Events it hears

| Topic | From | Why |
|---|---|---|
| `content.changed` | content | A register an installed item hears may have gained a row ([Hearing a row](#hearing-a-row)) |
| `content.proposal_decided` | content | The same, for a change that applied a proposal, and the proposal names the run that made it |

It subscribes with `scope` `"*"` and reads nothing from an event it could not
read from content itself: an event says which entry moved, and the service
reads the entry.

### What it hands each neighbour

| to | what | how |
|---|---|---|
| execution | each operation's and each workflow's starts, registered with `PUT /v1/execution/schedules/{schedule}` on this service's registration token, paused or running and muted as the item is; switched there with `…/pause`, `…/resume` and `…/runs` and replaced on a mute, unmute or reschedule; withdrawn with `DELETE` ([Starting on a fact](#starting-on-a-fact)) | when a start fires, execution runs the definition it fetches with `get_workflow`, as [`architecture/execution`](execution.md#firing) states for any owner's definition |
| notification | a notice that has advanced: its `says`, its `to` positions, the fact it is about, and its work authorisation. And an occurrence that advanced: the obligation's `activity`, the stage, the `responsible` or `escalate.to` position it is told to, and the `due-sweep`'s work authorisation | `NotifyByPosition` ([Notification](#notification)) |
| the prompt worker | nothing directly. An `agent:` phase names the worker as its agent, with the instruction, its `needs:`, the adopted map as `source` and the programme's skills in its `input`, and execution dispatches it | [The prompt worker](#the-prompt-worker) |
| the orchestrator | nothing but reads. It reads `GET /v1/work/authorisations` for the authorisations that name it as owner, and revokes those of what it withdraws | [Installing](#installing), [Withdrawing](#withdrawing) |

## Error Handling

| Code | When |
|---|---|
| `PASS_REQUIRED` | An operator token was presented on any route ([`protocol/identity`](../protocol/identity.md#the-pass), rule 4) |
| `PASS_AUDIENCE_MISMATCH` | A pass or a work pass addressed to another component |
| `FORBIDDEN` | The token does not carry the route's capability; or a route this document reserves to a pass was reached on any other token |
| `INVALID_REQUEST` | An installation asked for at a project rather than its organisation, naming the organisation; a body that is not an `InstallationRequest` or an `ItemSchedule`; an `ItemSchedule` outside the closed vocabulary [`schemas/programme`](../schemas/programme.md#schedule--a-small-closed-vocabulary-and-not-the-obligations) gives; a `ref` that does not parse; a window longer than `max_window`; or a route missing the `organisation` or `programme` it requires |
| `NOT_FOUND` | No installed item with that programme and `id`, or that `uid`, at the organisation named; no obligation or occurrence with that `ref` in force there |
| `PROGRAMME_NOT_ADOPTED` | An installation asked for a programme the organisation has no `adoption.md` for in any of its repositories. Nothing is installed |
| `PROGRAMME_ITEM_NOT_RUNNING` | Agent work asked to start an item that is paused, withdrawn or has no live work authorisation, or asked to tell through an item that is muted, paused or withdrawn ([What agent work may start and tell](#what-agent-work-may-start-and-tell)). Nothing starts and nobody is told |
| `EXECUTION_START_LOOP` | Relayed from execution: the run agent work asked for would start a definition its own run's chain already holds ([`architecture/execution`](execution.md#starting-one-run-now)) |
| `INVALID_STATE` | Pausing, resuming, running or rescheduling a notice, a withdrawn item, or an item whose state already is the one asked for; rescheduling an item whose map declares no `schedule` |

**Each code's HTTP status is the one [`protocol/types`](../protocol/types.md#error-handling)
registers for it.** `PROGRAMME_NOT_ADOPTED` and `PROGRAMME_ITEM_NOT_RUNNING`
are this service's, registered there among the programme service codes.

An installation that hands some blocks to their owners and not others is not
an error. It answers `200`, lists every block it could not hand over, and
does not call itself complete
([`schemas/programme.md`](../schemas/programme.md#the-package--what-a-programme-brings-besides-its-documents)).
Installing a programme already installed at the organisation answers `200`
with the installation as it stands, and creates nothing.

**A due answer that could not read something says so, and is not an error.**
A register, a document or a repository it could not read is listed in
`not_read`, by what and why, and every obligation that reads from it is
reported `unverifiable` with that reason, never as met and never as missing
([What Is Due](#what-is-due)).

---

## Data Flow

### Installing

1. A person adopts a programme at an organisation
   ([`schemas/programme.md`](../schemas/programme.md#one-act-by-a-person-at-the-organisation)).
   The files are written into content first.
2. The same person's client sends `POST /v1/programme/installations` through
   the admin gateway, on the person's own pass. It names the organisation and
   the programme.
3. The service reads the organisation's `adoption.md` for that programme from
   content, and the adopted `map.md` beside it, as it is in the tenant's copy,
   never from the published template. With no adoption record it refuses with
   `PROGRAMME_NOT_ADOPTED`. It installs each operation, workflow and notice
   and mints each a `uid`. Each is paused or running as its `start` says, and
   every one is muted.
4. It registers each operation's and workflow's starts at execution
   ([Starting on a fact](#starting-on-a-fact)). It answers every block
   it could not hand to an owner, by name, with the missing service, and the
   build plan, in the order [`schemas/programme`](../schemas/programme.md#adoption-emits-a-build-plan)
   gives, of the services the tenant does not run, read from the service
   directory it holds.
5. The same person's client asks the orchestrator, on the person's own token,
   for a work authorisation for each operation, workflow and notice
   installed, each naming as its `definition` the item's `uid`, with the
   capabilities the item's ceiling comes to
   ([What a `needs:` ceiling comes to](#what-a-needs-ceiling-comes-to)) and
   the actors that run it ([`architecture/admin`](admin.md#work-authorisations)).
   An item with no live authorisation installs and does not run, and this
   service reports it as not authorised, never as running.
6. `programme.adopted` is published, once, for the first installation of that
   programme at that organisation.
7. Nothing reaches a person until somebody holding `programme:switch` unmutes
   an item, on their own pass.

### Firing

1. A start fires at execution — a clock, a fact, a count, a row, or a person
   running the item — and execution starts a run in its own ledger
   ([`architecture/execution`](execution.md#firing)).
2. It fetches the definition with `get_workflow`. It dispatches each phase:
   a `does:` phase to this service, and an `agent:` phase to the prompt
   worker.
3. What a muted item's run produces reaches nobody. It is kept in
   execution's run ledger, with the run, so that a person can compare it
   before unmuting. The programme service holds no run output, and the
   prompt worker keeps nothing.

### Starting on a fact

**Execution holds every start; this service registers and switches them.** An
item's starts are registered with `PUT /v1/execution/schedules/{schedule}`, one
`ScheduleRegistration` for each way the item starts, because a registration
carries exactly one of `clock`, `on`, `when` and `for`:

| the item declares | registered as | `{schedule}` |
|---|---|---|
| `schedule` | `clock`: its `cadence`, `at` as `local_time`, `weekday`, `day`, and the tenant's `timezone` ([Configuration](#configuration)); or the clock a person set ([Rescheduling](#rescheduling)) | `<uid>.clock` |
| `on:` | `on`: the topics [Events it publishes](#events-it-publishes) gives each word | `<uid>.on` |
| `when:` | `when`, as written | `<uid>.when` |
| `for:` | `for`, the register | `<uid>.for` |

`<uid>` is the installed item's, and the registration's `definition` is the
`uid` too, so two organisations that adopt one programme register two starts
and never one. Each is registered paused or running and muted as the item is,
at the item's organisation.

What a start does when it fires is execution's: coalescing a burst of facts
into one run, latching a count, holding `for:` rows and an `adopted` while a
start is paused, and refusing a row whose chain already holds a run of the
same workflow ([`architecture/execution`](execution.md#firing)). This service
publishes the facts and the rows, with the run that wrote each row where the
change names one ([Hearing a row](#hearing-a-row)), and switches the starts:

| a person or a component | here | at execution |
|---|---|---|
| pauses or resumes an item | its `state` | `POST …/pause` or `…/resume` on each of its starts |
| runs an item | — | `POST …/runs` on its first start |
| mutes or unmutes an item | its `muted` | each start registered again, with `muted` changed |
| reschedules or restores an item | its `schedule_set` | its `clock` start registered again |
| withdraws an installation | each item `withdrawn` | `DELETE` of each start |

A start execution could not be reached to register or switch is reported on
the item, and the item is not reported running until it is.

**A notice hears only its own programme's obligations.** An obligation
belongs to every programme installed at the organisation whose adopted copy
has a spec declaring an obligation with its `id`, and each `obligation.*`
event names them in `programmes`. A notice advances on an `obligation.*` fact
only where the obligation belongs to its programme, so two programmes that
each declare a notice on `obligation.escalated` each tell their own
escalations, and one escalation is never told twice by them.

### Telling

1. A sweep finds that an occurrence has advanced
   ([How an occurrence advances](#how-an-occurrence-advances)), or a fact one
   of a notice's `on:` events names has been published.
2. **An occurrence tells its own positions.** Advancing to `due_soon` or
   `overdue` tells the obligation's `responsible` position; advancing to
   `escalated` tells its `escalate.to` position as well, and the responsible
   one keeps the duty. This is told under the `due-sweep` operation that
   observed it, and only while that operation is unmuted: a muted sweep
   records each advance as not sent, and nobody is told. No notice is
   declared for it, and one declared for it would tell the same person twice.
3. **A notice advances** when a fact it names first becomes true at its
   organisation, about an obligation that belongs to its programme
   ([Starting on a fact](#starting-on-a-fact)), and not again while that fact
   merely stays true. If it has advanced and the notice is unmuted, the
   service asks notification to tell the `to` positions.
4. **Either is told with `NotifyByPosition`**, on this service's own
   registration token, naming the work authorisation it is told under — the
   notice's own, or the `due-sweep`'s for an occurrence — and an id it gives
   the advance as `run` ([`architecture/notification`](notification.md#notifying)).
   An occurrence is told as `notice` the `due-sweep` operation that observed
   it, with the obligation's `activity` as `says` and the occurrence in
   `fact`, because no notice is declared for it.
   It records that it asked, and the outcome notification answered. A muted
   notice's or sweep's advance is recorded as not sent, and nobody is told.
5. An advance whose outcome is `reached_nobody`, `not_authorised` or
   `holders_unreadable` is recorded as not delivered, with the outcome and the
   positions notification reports `unheld`, and never as sent
   ([`architecture/notification`](notification.md#outcomes)). A request
   notification did not answer is sent again with the same `run`, which tells
   nobody twice.

### Rescheduling

A person may move an operation's or a workflow's clock without editing the
adopted map: the hour it runs is operating it, not authoring it, and
`programme:operate` names reschedule
([`protocol/types`](../protocol/types.md#capability)).

1. `POST …/schedule` carries an `ItemSchedule`, in the closed vocabulary of a
   map's `schedule`. Anything else is refused with `INVALID_REQUEST`.
2. The item records it as `schedule_set`, with who set it and when, beside the
   map's `schedule`, which is unchanged and still reported.
3. The item's clock start is registered at execution again, with the new
   clock in place of the old one. A run already started is not touched.
4. `DELETE …/schedule` removes `schedule_set`, and the clock start is
   registered again with the map's clock.

An item whose map declares no `schedule` has no clock to move, and is refused
with `INVALID_STATE`: a clock added to an `on:`-only item would be standing
work the programme did not declare. When the adopted map's `schedule` changes,
`schedule_set` stays, and the item reports both, so the person who set it can
see the map has moved.

**Who hears an item is not switched here.** A notice's `to`, an obligation's
`responsible` and `escalate.to` are positions the map declares, and who holds
each is the register of position holders in content
([`schemas/position`](../schemas/position.md)). A person changes who hears by
changing who holds the position, or by editing the tenant's copy of the map,
each recorded where it is made. The switch this service holds over hearing is
whether anyone hears at all: mute.

### Withdrawing

When a person un-adopts
([`schemas/programme.md`](../schemas/programme.md#un-adopting)), their client
sends `DELETE /v1/programme/installations/{programme}?organisation=…` on
their pass. Every item installed under the programme at that organisation
stops and is recorded `withdrawn`, the withdrawal is recorded, the service
revokes every work authorisation that names one of those items as its
owner's definition (`DELETE /v1/work/authorisations/{id}`,
[`protocol/identity`](../protocol/identity.md#the-work-pass) rule 4), every
start it registered at execution is withdrawn there, and `get_workflow` answers `NOT_FOUND` for each of
its definitions. Runs already in execution's ledger stay there.

---

## What Is Due

What an organisation owes, derived every time it is asked from the documents
that say so and the registers that record it. This is the tenant's one
implementation of the obligation model
[`schemas/programme`](../schemas/programme.md#declaresobligation) declares;
the field meanings, vocabularies and refusals are that schema's, and are not
restated here.

**Derived, never stored.** An occurrence is a function of an obligation, a
period or a row, and a register. A stored due date goes stale the moment
somebody does the work early, and then the record and the task disagree with
no way to tell which is right. So nothing below is a table: every answer is
computed from content as it stands, and what this service keeps is only what
it has already announced ([What it keeps](#what-it-keeps)).

### Where an obligation is read from

**An obligation is in force when a document in content declares it.** The
service reads the `obligations:` list in the frontmatter of every entry in the
repositories at the organisation's `scope_path` and at each of its projects',
as [`schemas/programme`](../schemas/programme.md#declaresobligation) gives
its fields. A spec's `declares.obligation` is not yet in force: it becomes so
when the document drafted from that spec carries it. Readiness reports a
spec's obligation whose document does not exist as *declared, not in force*
([Readiness](#readiness)).

An obligation's identity is its `ref`: the repository's `id`, the path of the
document that declares it, and its `id`, written `<repository>:<path>#<id>`.
Its `id` defaults to the document's `id` as the schema says, so renaming an
activity orphans nothing.

**A document is the tenant's, not a validated programme.** A word in it
outside a closed vocabulary does not stop the read: the obligation is
reported `undeclarable`, with which field and why, and produces no
occurrences. An unknown `interval_basis` is read as unstated, as
[`schemas/programme`](../schemas/programme.md#authority-and-interval_basis--whose-interval-is-it)
requires of a tenant's document.

### Occurrences

One obligation owes **occurrences**, each named by a **key** that is unique
within the obligation, and an occurrence's identity is its `ref`, the
obligation's `ref` and the key: `<obligation ref>/<key>`.

| the obligation declares | one occurrence per | its key | due at |
|---|---|---|---|
| `cadence` | period, at each place `applies_to` expands to | the period: `2026-08-13` daily and each working day, `2026-W33` weekly, `2026-08` monthly, `2026-Q3` quarterly, `2026` yearly | the last instant of the period |
| `cadence` and `per:` | period per subject live in it | `<subject key>/<period>` | the last instant of the period |
| `for:` | row of the trigger register | the row's `for.key` value | the instant `for.due` gives from the date that row carries |

- **A period is expected only once it can have happened.** A period that has
  not ended owes nothing yet; a working-day cadence owes nothing on a
  Saturday or a Sunday.
- **A subject is live in a period its window overlaps**, from its `from` to
  its `until`, an empty `until` meaning still.
- **A key round-trips.** A period key parses back to the period it names, and
  that is the only way its due instant is found, so a key and its date can
  never disagree.
- **Places.** `applies_to` naming the organisation gives one place, the
  organisation; naming each workspace gives one place per project under it.
  A place is part of the occurrence and is reported with it.

### The three states, and a fourth

| state | means | counted as met |
|---|---|---|
| `missing` | the occurrence is due and nothing in `records:` records it | no |
| `recorded` | a row in `records:` records it, and nobody has stood behind that row | **no** |
| `attested` | the row that records it was written by a change carrying a person's verified statement ([`architecture/content`](content.md#the-change-statement)) | yes |
| `unverifiable` | the obligation names no `records:`, or what it reads could not be read; `note` says which | no, and never as missing either |

**A row records an occurrence** when it carries the occurrence's key: the
period key in a cell, the subject in the column the recording register's
relation onto the subject register names, and for `for:`, the trigger row's
key. A row carrying two candidate keys for one obligation records both, and
attests neither, because choosing between them would be this service deciding
which period somebody meant to certify.

**`attested` reads the change log, never a flag.** The row's change is found in
the register's change log, and its part is `signed` only where that change
carries a verified `statement`
([`architecture/content`](content.md#who-signs)). An agent, a schedule and a
service sign nothing there, so no machine work reaches `attested`. The first
signed change that recorded the occurrence names `attested_by` and
`attested_at`; a later one does not move them.

### Escalation

An occurrence is **escalated** when it is overdue, is neither `recorded` nor
`attested`, and has been overdue longer than its obligation's
`escalate.after`. It then also belongs to the `escalate.to` position, and the
`responsible` position keeps it: escalation adds an owner and never moves the
duty. An `escalate` that does not parse escalates nothing, as
[`schemas/programme`](../schemas/programme.md#which-mistakes-stop-the-file-and-which-do-not)
says, and this service reports it on the obligation as unreadable rather than
silently.

### How an occurrence advances

What is announced, and when, is decided by **stage** and **size**, so that
nothing is announced twice and a lapse that grows is not announced once.

- **Stage**, in order: `due_soon` (due within `due_soon_window` and not yet
  recorded), `overdue`, `escalated`; and, separately, `attested`.
- **Size** is how many occurrences of one obligation, at one place and for
  one subject, are overdue at once. It is counted in **steps**: 3, 10, 30,
  100, 300 and 1000.

A sweep advances an occurrence when its stage rises above the highest stage
already announced for it, or its size crosses a step above the highest
already announced. Each advance publishes its topic once
([Events it publishes](#events-it-publishes)) and is told once
([Telling](#telling)). The highest stage and step announced are remembered,
so an occurrence that briefly reads less severe does not announce again when
it returns. An occurrence that stops being due is forgotten: missed again next
period, it is a new lapse and is announced again. A sweep forgets only what is
at the place it swept.

### What is due now

`GET /v1/programme/due` answers a `DueList`: each **entry** is one obligation
at one place and for one subject, with how many occurrences are outstanding,
the oldest one's key and due instant, whether it is overdue or escalated, and
its `responsible` and `escalated_to` positions. Every overdue entry is
included whatever `within` says, because a window that hid a lapse from last
year would hide the one that matters most. Entries are ordered most overdue
first.

**Positions, never people.** An entry names positions. Who holds one is the
tenant's register of position holders, read by the client on the person's own
pass; this service does not resolve a position to a person, so no answer here
carries a person's name. A client asking for "mine" passes the positions its
person holds as `responsible`.

**What nothing chases is said.** `unchased` lists each programme installed at
the organisation whose obligations no running, authorised `due-sweep`
operation covers. Its occurrences are still answered when asked; nothing will
announce them.

### Counted conditions

A `when:` is counted by execution, which holds it as a start
([`architecture/execution`](execution.md#firing)). What it counts is what
this service publishes: the `obligation.*` events and `register.row_added`.
A `count.distinct` naming a field no event of the type carries counts
nothing forever, so this service reports it on the item at install, naming the
field and the event type, as a condition that can never fire. An `across`
broader than the organisation was refused at install.

### Hearing a row

A **heard register** is one a running item names: a `for.records`, or a
`when.where.register` on `register.row_added`. Only heard registers are read
for rows.

1. On `content.changed` or `content.proposal_decided` for a heard register,
   the service reads the register and the change.
2. **A row arrives** when its key, by the register's key column, was not in
   the register before; where the register has no key column, by its whole
   text, so correcting a typo in a keyless register reads as an arrival. That
   is the limit of reading rows from bytes, and it is stated rather than
   hidden. An edited row arrives nothing.
3. The keys already seen are kept per heard register. A register first heard
   has every row it holds then taken as seen, and announces none of them:
   rows written before an item heard the register are not news.
4. **The writer is read from the change.** A change that applied a proposal
   names it, and the proposal names its `run` ([`architecture/content`](content.md#who-a-change-was-for)).
   A direct write by a person has no run. A change or proposal this service
   cannot read leaves the writer unknown.
5. Each arrival publishes one `register.row_added`, carrying the run that
   wrote it, or `writer: unknown`, from which execution starts each `for:`
   workflow on that register and stops a loop
   ([`architecture/execution`](execution.md#firing)). An arrival of more than
   `max_rows_per_change` rows from one change publishes that many and one
   more naming how many were not announced.

### Readiness

Readiness is two numbers, and the second is the one a binder cannot fake.

- **Documented**, per tier, cumulative through `requires`: of the artifacts
  the tier places, how many are `present`, `present_stale`, `present_uncited`,
  `missing` or `unknown`, and the share that is `present`. An artifact is
  matched to a document that declares it, by the document's frontmatter
  `artifact:` naming the spec's `id`, or, where none does, to a document the
  fabric records as answering every control the spec cites
  ([`architecture/fabric`](fabric.md)). Where the fabric cannot be read, an
  artifact no document declares is `unknown`, never `missing`.
- **Operating**, over `status_window`: of the obligations in force under the
  programme, how many are **operating** — at least one occurrence in the
  window, and every one `attested` — how many are not, and how many are
  **undetermined**, with no occurrence in the window, which a yearly
  obligation is for eleven months of twelve. Undetermined is never counted
  against. An obligation at several places is operating only where it is
  operating at every one.

`measured` is false, and `unmeasured` says why in words, wherever a number is
a floor rather than a measurement: a repository that could not be read, an
artifact that could not be judged. A spec's obligation not yet in force is
listed in `not_in_force`, and counts in neither number.

### What a person is answered

Every due answer is computed on this service's own registration, reading
content with `content:read`, and is served to a person who can use
`programme:read`. So it carries **identities, states and dates, and never
what a record says**:

- a subject's `label`, and a row's columns, only from a register whose
  recorded scope is `public` or `internal`. From any other register the key
  alone is answered, and a client reads the rest from content on the person's
  own pass, where content's own check applies;
- no cell of any register in an event.

### What it keeps

| store | holds | lost, costs |
|---|---|---|
| installations and items | every installation and installed item, with its switches, `schedule_set` and who switched what | the tenant's installed standing work: the items, their switches and who set them. This is the system of record for them |
| announcement marks | per occurrence, the highest stage and step announced | a second announcement of everything currently due, once |
| seen keys | per heard register, the keys already seen | nothing: the next read takes every row as seen |
| advances of notices | per notice, each advance: when, which positions, and what notification answered | the history `ListNotices` shows |

Nothing here is a due date, an occurrence or a state. Those are derived.

---

## The `does:` Actions

The tenant's `does:` vocabulary is this table. A `does:` naming anything else
is reported at install by name, with these, and answers `NOT_FOUND` if it is
ever invoked ([`schemas/programme`](../schemas/programme.md#does-names-an-action-the-platform-has-and-the-list-is-the-platforms)).
`GET /v1/programme/actions` answers the same list from the running build.

| action | does | reads with |
|---|---|---|
| `due-sweep` | Computes what is due at the item's organisation, advances what has advanced ([How an occurrence advances](#how-an-occurrence-advances)), publishes each advance, and tells each advanced occurrence's positions while the operation is unmuted ([Telling](#telling)). Execution starts every item whose `on:` names a topic it published. Answers a `SweepResult` | `content:read` |
| `programme-readiness` | Computes the readiness of every programme installed at the item's organisation, and answers it as `{programmes: [ProgrammeReadiness]}`. Announces nothing | `content:read`, `fabric:read` |

**A `does:` item is this service's own work, and its reads ride on work
passes.** Execution invokes the action on a work pass addressed here, with an
empty `cap` ([`protocol/identity`](../protocol/identity.md#the-work-pass)
rule 11). Each read the action then makes of content or the fabric is carried
on a work pass this service obtains as an **actor** of the same item's
authorisation, whose capabilities are the action's *reads with*. So a `does:`
item's authorisation names execution, this service and notification as its
actors, and its *reads with* as its ceiling.

---

## Who May Do What

This is the **person and pass rule** for programme work. The token rules
themselves are [`protocol/identity`](../protocol/identity.md#the-pass)'s, and
they are not restated here.

1. **A person reaches this service only on a pass.** Every person's request
   arrives through the admin gateway, on a pass addressed to this service. An
   operator token is refused on every route.
2. **Some acts are a person's alone, and are admitted only on a pass:**
   installing and withdrawing a programme, because adopting and un-adopting
   are a person's acts; muting and unmuting, because `programme:switch` is
   person only; and pausing, resuming, running, rescheduling or restoring an
   item's schedule **while it is unmuted**, because starting, stopping or
   moving work that reaches people is a person's decision. A registration,
   channel or work token on one of these is refused with `FORBIDDEN`,
   whatever capabilities it carries. An operator token is refused with
   `PASS_REQUIRED`, as on every route (rule 1).
3. **A service or an agent may operate muted work.** Holding
   `programme:operate` on its own registration, or on a work pass, it may
   pause, resume, run or reschedule an item while that item is muted. Nobody
   is reached. A service or an agent may also propose an adoption as content
   proposals, and a person decides them
   ([`architecture/content`](content.md#who-may-move-an-entry)).
4. **Work that runs unattended is the service's own, never a person's.** A
   firing runs under the programme service's manifest. A `needs:` ceiling
   narrows an agent's authority and never widens it. Neither inherits the
   authority of the person who installed or unmuted the item. That person is
   recorded as who switched it on, not as who ran it. Each request a firing
   makes of a component is carried on a **work pass**: this service is its
   owner, the component doing the work is its actor, and it rests on a work
   authorisation a person made for that one item, whose capabilities bound
   every pass under it ([`protocol/identity`](../protocol/identity.md#the-work-pass)).
   The person who made the authorisation is recorded as who allowed the
   work, never as who ran it.
5. **No machine step decides.** No action, `needs` capability or worker
   approves, rejects, closes, attests or signs
   ([`schemas/programme.md`](../schemas/programme.md#workflows--multi-step-work-with-waits-and-approvals)).
   Those acts are a person's, in [the decision inbox](#the-decision-inbox).
   No due answer moves an occurrence to `attested`: only a person's signed
   change does ([The three states, and a fourth](#the-three-states-and-a-fourth)).

Each act records an `AuditEntry`. On a pass, the person is the `actor` (by
the pass's `identity_id`) and the gateway that carried the request is `via`.
On a work pass, the `actor` is the owner, `via` the actor, and `authorisation`
and `run` are the pass's.

### What a `needs:` ceiling comes to

What each `needs:` word comes to is stated once, by the prompt worker, its one
consumer ([`architecture/prompt-worker`](prompt-worker.md#needs-comes-to-these-capabilities)),
and the capabilities an `agent:` item's work authorisation is asked for are
exactly those, for the words its `needs:` names, `read` where it names none.

Every item's authorisation names as its actors every service its blocks hand
work to: execution for any operation or workflow; the prompt worker for an
`agent:`; this service for a `does:`; notification for a notice, for a step
that waits for a person, for a `due-sweep`, and for an `agent:` whose
`needs:` names `notify`. A `does:` item's ceiling is
its action's *reads with* ([The `does:` Actions](#the-does-actions)), and a
`due-sweep`'s adds `content:describe`; a notice's is `content:read` and
`content:describe`, which notification reads its positions' holders with
([`architecture/notification`](notification.md#resolving-holders)); a step
that waits for a person comes to the same two, which execution reads the
positions it awaits with ([`architecture/execution`](execution.md#who-holds-a-position));
an `agent:` whose `needs:` names `notify` adds the same two, which
notification reads the holders it tells with; a workflow's is the union over
its steps.

### What agent work may start and tell

An `agent:` item's work reaches this service on a work pass the prompt worker
obtains under the item's own authorisation, so its `identity_id` is this
service's own and its `definition` names the item: this service admits it only
where the item is installed here now
([`protocol/identity`](../protocol/identity.md#minting-a-work-pass), rule 11).
What the pass may then do here is what its `cap` carries, and nothing more:

1. **Read what is due.** With `programme:read`, the due, occurrence,
   obligation and readiness routes answer it exactly as they answer a person
   ([What a person is answered](#what-a-person-is-answered)), at the item's
   organisation and its projects only. A request naming another organisation
   is refused with `FORBIDDEN`.
2. **Start work of its own programme.** With `programme:dispatch`,
   `RunOperation` and `RunWorkflow` start one run of an operation or a
   workflow **of the same programme, installed at the same organisation**. A
   target of another programme, or none, is `NOT_FOUND`. A target that is
   paused, withdrawn or has no live authorisation is refused with
   `PROGRAMME_ITEM_NOT_RUNNING`: a person stopped it, and agent work never
   starts what a person stopped. This service asks execution for the run with
   `RunScheduleNow` on its own registration token, with a `RunNow` naming
   the pass's `run` as `parent`, and the body's `not_before` and `reason`
   ([`architecture/execution`](execution.md#starting-one-run-now)), and
   answers what execution answered. So the run is muted wherever the asking
   run or the target is, a loop is refused with `EXECUTION_START_LOOP`, and
   the run's authority is the target's own authorisation, never the asking
   item's.
3. **Tell positions.** With `programme:notify`, `NotifyFromItem` asks
   notification to tell the positions the body names what the work says.
   Every position named must be one the programme's adopted map names, in an
   `approved_by`, a `responsible`, an `approvers`, an `escalate.to` or a
   notice's `to`; any other is refused with `INVALID_REQUEST`, naming it, and
   nobody is told. An item that is muted, paused or withdrawn is refused with
   `PROGRAMME_ITEM_NOT_RUNNING`. Otherwise it sends `NotifyByPosition` on its
   own registration token, as [Telling](#telling) does, naming the item's
   authorisation, the item as `notice`, the body's `says` and `why`, and as
   `fact` the event `instruction` at the moment it asked. The `run` it gives
   is the pass's `run` and the digest of the body, so the same words asked
   twice in one run tell once. It answers the `Notification` notification
   answered, whose outcome says whether anybody was reached.

None of the three is a switch. Rule 2 above stands: pausing, resuming,
rescheduling, muting and unmuting stay a person's. **Starting a run of
running, unmuted work is not one of them**: a person made the target run and
reach people, and a person authorised the asking item with `dispatch`; agent
work adds one run of what they chose, recorded with `trigger` `run` and the
asking run as `parent`. Telling, likewise, reaches only positions the adopted
programme already names, in words the prompt worker checked may leave the
tenant ([`architecture/prompt-worker`](prompt-worker.md#scope)). Each act is
recorded with this service as `actor`, the prompt worker as `via`, and the
pass's authorisation and run.

---

## The Services It Hands Work To

### Execution

Execution is [`architecture/domain`](domain.md)'s merged cron, task and
workflow service. Programme work asks of it only what a domain's work asks:
it runs `patterns/workflow` declarations, fetched from their owner, and keeps
every run, wait and timer in its one ledger. A programme's workflow becomes
one such declaration, as
[`schemas/programme.md`](../schemas/programme.md#how-a-workflow-maps-onto-patternsworkflow)
maps it, named by the installed item's `uid`. An operation becomes a
declaration of one phase. Its starts are registered there
([Starting on a fact](#starting-on-a-fact)).

**People read runs through the admin gateway's Workflows group.** Execution
is the provider of `GET /v1/admin/workflows` and `GET /v1/admin/workflows/{id}`
([`architecture/execution`](execution.md#endpoints)). Each needs `admin:read`,
on a pass addressed to execution, and answers the shape
[`architecture/admin`](admin.md#get-v1adminworkflows) gives. A run of a
programme's workflow names its definition in `workflow_name`. A run with no
domain has no `domain_name`.

### Notification

Notification is [`architecture/notification`](notification.md). From the
programme service it accepts a **notify by position**, `NotifyByPosition`:
the notice or the occurrence that advanced, what to say, the positions to
tell, the fact it is about, and the work authorisation it is told under. It
finds who holds each position in the
[position-holders register](../schemas/position.md#who-holds-a-position),
words the message, and delivers by each holder's own preference. Nobody is
present when a notice advances, so it reads the holders on work passes under
that authorisation, which names notification as an actor
([`protocol/identity`](../protocol/identity.md#the-work-pass)).

A notice names positions only, never a person or a channel
([`schemas/programme.md`](../schemas/programme.md#notices--who-is-told-what)).
A notice that reaches nobody, because nobody holds a position it names, is
answered as that outcome, and this service records it as not delivered
([Telling](#telling)).

### The prompt worker

The prompt worker is the tenant's one shared runner of `agent:` instructions.
A programme never brings an agent component
([`schemas/programme.md`](../schemas/programme.md#agents-are-instructions-never-components)).
Execution dispatches an `agent:` phase to it, with the instruction and the
`needs:` ceiling as the phase's `input`. The worker:

- runs with the intersection of the ceiling, its own manifest's declaration
  and the identity under the run, and never more. The identity under the run
  is the item's owner, this service, narrowed by the work authorisation a
  person made for the item; the worker is its actor, and reaches content only
  on work passes minted under that authorisation
  ([`protocol/identity`](../protocol/identity.md#the-work-pass));
- asks the tenant's model service for each completion, at
  `POST /v1/model/complete` on its own registration token, stating the run and
  phase it works for, and reaches no model any other way
  ([`architecture/model-service`](model-service.md#asking-the-model-unattended));
- hands back, with its phase result, each completion's id, the model that ran
  and the usage the model service reported, which execution writes on the
  run's record ([`architecture/model-service`](model-service.md#usage-and-cost));
- writes only through an owner's API, as a proposal where that owner requires
  one, and keeps nothing of its own. The run's record is execution's;
- reads what is due, starts work of its own programme and tells the positions
  its programme names only through this service's routes, as
  [What agent work may start and tell](#what-agent-work-may-start-and-tell)
  bounds them.

Its component blueprint is [`architecture/prompt-worker`](prompt-worker.md):
how execution hands it a phase, the closed tool set an instruction may be
given, which capabilities each `needs:` word comes to, how a programme's
`skills` reach the instruction, and what a phase answers, including that it
was not runnable.

**What an `agent:` phase is handed.** At install, each `agent:` operation or
step becomes a phase whose `input` is an `InstructionTask`: the instruction,
its `needs:`, `source`, the adopted `map.md` it was read from in content,
`skills`, each skill file the programme brings with no `for`
([`schemas/programme`](../schemas/programme.md#skills--files-the-programme-brings)),
and `programme` and `item`, the programme's id and the operation's or
workflow's id, which the worker names when its tools ask this service to start
or tell ([What agent work may start and tell](#what-agent-work-may-start-and-tell)).

### The decision inbox

**Each owner serves its own decisions, and the admin gateway composes one
inbox from them.** There is no approval service. A decision is a person's
act, made on their own pass, at the owner whose work is waiting on it:

- a content proposal is decided at content, with
  `POST /v1/content/proposals/{id}/decision` and `content:decide`
  ([`architecture/content`](content.md#who-may-move-an-entry)). This is the
  one kind of decision a tenant can serve today;
- a workflow's `approval` or `task` step is a wait execution holds, and is
  decided there with `POST /v1/execution/waits/{wait}/decision` and
  `execution:decide`, by a person holding a position the wait awaits
  ([`architecture/execution`](execution.md#deciding)).

No machine makes a decision ([Who May Do What](#who-may-do-what), rule 5).
How each decision is shaped is
[`patterns/approval`](../patterns/approval.md)'s.

---

## Registration and Standalone Operation

The programme service is a component in the mesh: it registers with the
orchestrator, claims the `obligation.*`, `register.*` and `programme.*`
namespaces exclusively in `publishes`, subscribes to `content.changed` and
`content.proposal_decided`, verifies caller tokens against the orchestrator's
public key, and takes a person's request only on a pass addressed to it. As
every registrant does, it serves `POST /v1/services` exactly as
[`protocol/spec`](../protocol/spec.md#post-v1services) specifies, and never
answers a push `404`. The directory it holds is what its build plan reads to
know which services the tenant runs.

Its manifest declares `protocol_version` `"1"`, every route the
[Endpoints](#endpoints) table admits a pass on as a pass route with the one
capability its row gives, and the capabilities named there.

### Startup Sequence

```
1. Load configuration and open its store (What it keeps)
2. Load or generate the ML-DSA-65 key pair
3. Construct the authenticator WITHOUT an issuer key: it refuses every token
   until one arrives
4. Register HTTP routes and start listening
5. Register with the orchestrator, if an orchestrator URL is configured
6. On the registration response, set the issuer public key on the
   authenticator
7. Read the authorisations that name it as owner, and report each item's
   authorisation state
8. Register every installed item's starts at execution again, if execution
   is registered, which a repeated registration under one key does not
   double; a start that could not be registered is reported on its item,
   never dropped
9. Serve until signalled
```

Steps 3 to 6 are in that order for the reason
[`architecture/content`](content.md#startup-sequence) gives: a service that
needs the issuer key to construct its authenticator exits before it can obtain
it.

**An orchestrator is not required in order to start.** Where no orchestrator
URL is configured, the service starts, serves `GET /livez` live and
`GET /readyz` not ready, and refuses every protected route with `401` and an
`ErrorResponse`, because it holds no issuer key. Where one IS configured,
registration failure is fatal.

---

## Known Gaps

**Nothing is built from these blueprints yet.** This service, execution,
notification and the prompt worker are each specified, and no tenant runs
any of them, so an adoption today hands no block to an owner, and says so.

**A person's step can wait and not yet be decided**, until a tenant holds
the position-holders register ([`architecture/execution`](execution.md#known-gaps)).

**An `on:` start hears every obligation at its organisation.** A notice hears
only its own programme's obligations ([Starting on a fact](#starting-on-a-fact)),
and an `on:` start at execution is registered with topics and nothing to
narrow them to a programme, so an `on: [obligation.escalated]` operation
runs for every escalation at its organisation. Each event names the
`programmes` its obligation belongs to, for a start that can be narrowed by
them once execution's registration can say so.

**Agent work starts and tells within its own programme only.** A `dispatch`
reaches an operation or a workflow of the asking item's programme, and a
`notify` the positions that programme names
([What agent work may start and tell](#what-agent-work-may-start-and-tell)).
Starting another programme's work, or telling a position no adopted
programme names, has no route: each would let one programme's agent work act
on authority a person granted for another, and is the owner's to decide.

**An agent records an occurrence only as a proposal of a whole register**
([`architecture/prompt-worker`](prompt-worker.md#known-gaps)). A row a person
accepts that way reads `recorded`, never `attested`
([The three states, and a fourth](#the-three-states-and-a-fourth)).

**An `agent:` operation or step installs and cannot run yet.** No hub serves
the model service's route ([`architecture/model-service`](model-service.md#known-gaps))
and no tenant runs the prompt worker, so it is reported as not runnable, never
as having run.

**An attestation is not yet checked against the positions that must give
it.** `attested` needs a person's signed change
([The three states, and a fourth](#the-three-states-and-a-fourth)). Where a
register declares `review: required` and `approvers`, the positions that must
approve a row are not checked against who signed it: this service does not
yet read the position-holders register
([`schemas/position`](../schemas/position.md#who-holds-a-position)) when it
judges an attestation. Until it does, `attested` says a person
stood behind the record, and not that the person held the position the
register names.

**A document's own sign-off has no tenant owner.** `approved_by` on a spec
names the positions that put a document in force, and no tenant service
raises or records that sign-off. So the programme word `attestation` is
published as `obligation.attested`, which is about a record, and nothing
publishes a document's sign-off.

**Programme objectives have no routes here.** The admin gateway names this
service as the provider of a programme's objectives
([`architecture/admin`](admin.md)), and no route or type in this document
serves one, so the gateway reports them unavailable.

---

## Types

```yaml
types:
  InstallationRequest:
    description: What a person's client sends to install an adopted programme
    fields:
      organisation:
        type: string
        required: true
        description: The organisation the programme was adopted at
      programme:
        type: string
        required: true
        description: The adopted programme's id, as its adoption.md names it
  ProgrammeInstallation:
    description: One programme installed at one organisation
    fields:
      uid:
        type: string
        required: true
        description: Minted at the first installation, 32 lowercase hex characters, never reused
      programme:
        type: string
        required: true
      organisation:
        type: string
        required: true
      state:
        type: string
        enum: [installed, withdrawn]
        required: true
      installed_by:
        type: string
        required: true
        description: The identity id of the person who installed it, from their pass
      installed_at:
        type: timestamp
        required: true
      withdrawn_by:
        type: string
        required: false
      withdrawn_at:
        type: timestamp
        required: false
      items:
        type: "[]string"
        required: true
        description: The uid of every item installed under it
      not_handed_over:
        type: "[]NotHandedOver"
        required: true
        description: Every block not given to its owner. Empty only when every block was
      build_plan:
        type: "[]BuildStep"
        required: true
        description: The services the programme needs that the tenant does not run, in the order schemas/programme gives. Empty only when the tenant runs every one
  BuildStep:
    description: One service a programme needs and the tenant does not run
    fields:
      order:
        type: int
        required: true
        description: Its place in the plan, from 1. A service needs every one before it
      service:
        type: string
        required: true
        description: The service's name, as schemas/programme's table of services names it
      blueprint:
        type: string
        required: true
        description: The blueprint it is built from, as that table names it
      state:
        type: string
        enum: [not-running, unspecified]
        required: true
        description: unspecified where the corpus the tenant builds from holds no such blueprint
      needed_for:
        type: "[]string"
        required: true
        description: The blocks that need it, each as <block>:<id>
  InstalledItem:
    description: One operation, workflow or notice the programme service holds at a scope
    fields:
      uid:
        type: string
        required: true
        description: Minted at installation, 32 lowercase hex characters, never reused. The definition its work authorisation and execution name
      installation:
        type: string
        required: true
        description: The uid of the installation it was installed under
      programme:
        type: string
        required: true
        description: The adopted programme's id
      id:
        type: string
        required: true
        description: The item's id in the map. With programme and scope, what installing twice matches on
      kind:
        type: string
        enum: [operation, workflow, notice]
        required: true
      scope:
        type: string
        required: true
        description: The organisation the programme was adopted at
      state:
        type: string
        enum: [paused, running, withdrawn]
        required: true
        description: A notice is running from installation until withdrawn, and is never paused
      muted:
        type: bool
        required: true
        description: True from installation until a person unmutes it
      schedule:
        type: ItemSchedule
        required: false
        description: The map's schedule, as installed. Absent where the map declares none
      schedule_set:
        type: ItemSchedule
        required: false
        description: The schedule a person set in its place. Absent until one is
      schedule_set_by:
        type: string
        required: false
      switched_by:
        type: string
        required: false
        description: The identity id of the person who last unmuted or muted it, from their pass
      authorisation:
        type: ItemAuthorisation
        required: true
      next_firing:
        type: timestamp
        required: false
        description: When its clock next fires, as execution reports it. Absent while paused or with no clock
  ItemSchedule:
    description: A clock, in the closed vocabulary of a map's schedule (schemas/programme)
    fields:
      cadence:
        type: string
        enum: [hourly, daily, weekly, monthly]
        required: true
      at:
        type: string
        required: false
        description: A time of day, not an instant, written HH:MM, 24-hour, in the installation's local time. Required except hourly
      weekday:
        type: string
        enum: [monday, tuesday, wednesday, thursday, friday, saturday, sunday]
        required: false
        description: Required for weekly
      day:
        type: int
        required: false
        description: 1 to 31, required for monthly
  ItemRun:
    description: The optional body of RunOperation and RunWorkflow
    fields:
      not_before:
        type: timestamp
        required: false
        description: Start it at this instant rather than now. Execution holds it as a start timer (architecture/execution, Starting one run now)
      reason:
        type: string
        required: false
        description: Why it was asked for. Recorded on the run; data, never acted on
  ItemNotice:
    description: The body of NotifyFromItem, sent by the prompt worker for an agent item's work
    fields:
      programme:
        type: string
        required: true
        description: The asking item's programme. Must be the programme of the item the work pass's definition names
      item:
        type: string
        required: true
        description: The asking item's id within its programme
      organisation:
        type: string
        required: true
        description: The item's organisation
      project:
        type: string
        required: false
      positions:
        type: "[]string"
        required: true
        description: The positions to tell, each one the programme's adopted map names. At least one
      says:
        type: string
        required: true
        description: What the work asks to say, in the model's words. Data, worded by notification and never acted on
      why:
        type: string
        required: false
  ItemAuthorisation:
    description: The work authorisation an item runs under, as the orchestrator reports it
    fields:
      id:
        type: string
        required: false
        description: Absent while none names the item
      state:
        type: string
        enum: [live, none, expired, revoked]
        required: true
      not_after:
        type: timestamp
        required: false
  NotHandedOver:
    description: A block an installation could not give to its owner
    fields:
      block:
        type: string
        required: true
        description: The map's key, such as workflows or domain_services
      id:
        type: string
        required: true
      owner:
        type: string
        required: true
        description: The service that would own it
      reason:
        type: string
        required: true
        description: In words, such as the owner is not running, or the workflow has a person's step
  ProgrammeAction:
    description: One does action this build runs
    fields:
      name:
        type: string
        required: true
      reads_with:
        type: "[]string"
        required: true
        description: The capabilities its reads ride on, which an item's authorisation ceiling must hold
  Obligation:
    description: One obligation in force, as the document that declares it says, and how it stands
    fields:
      ref:
        type: string
        required: true
        description: <repository>:<path>#<id>
      id:
        type: string
        required: true
      repository:
        type: string
        required: true
      path:
        type: string
        required: true
      activity:
        type: string
        required: true
      cadence:
        type: string
        required: false
      for:
        type: map
        required: false
        description: records, due and key, as schemas/programme declares for
      per:
        type: map
        required: false
        description: listed_in, key, label, from, until and recorded_as, as schemas/programme declares per
      applies_to:
        type: string
        required: false
      responsible:
        type: string
        required: false
        description: A position
      records:
        type: string
        required: false
      escalate:
        type: map
        required: false
        description: after and to, as declared
      authority:
        type: string
        required: false
      interval_basis:
        type: string
        enum: [required, chosen]
        required: false
        description: Absent where unstated, or where the document's word is outside the pair
      satisfies:
        type: "[]string"
        required: false
      organisation:
        type: string
        required: true
      project:
        type: string
        required: false
        description: The project whose repository declares it, where one does
      undeclarable:
        type: bool
        required: true
      undeclarable_reason:
        type: string
        required: false
        description: Which field could not be read, and what to write instead
      counts:
        type: map
        required: true
        description: Occurrences in the window, keyed by state
  Occurrence:
    description: One occurrence an obligation owes
    fields:
      ref:
        type: string
        required: true
        description: <obligation ref>/<key>
      obligation:
        type: string
        required: true
        description: The obligation's ref
      key:
        type: string
        required: true
      period:
        type: string
        required: false
        description: The period key, on an occurrence of a cadence
      subject:
        type: string
        required: false
        description: The subject's key, on an obligation with per
      subject_label:
        type: string
        required: false
        description: Only from a register whose recorded scope is public or internal
      origin:
        type: string
        enum: [schedule, records]
        required: true
      state:
        type: string
        enum: [missing, recorded, attested, unverifiable]
        required: true
      due:
        type: timestamp
        required: true
      overdue:
        type: bool
        required: true
      escalated:
        type: bool
        required: true
      escalated_to:
        type: string
        required: false
        description: A position
      responsible:
        type: string
        required: false
        description: A position
      organisation:
        type: string
        required: true
      project:
        type: string
        required: false
        description: The project it is expected at, where applies_to expands to projects
      records:
        type: string
        required: false
      attested_by:
        type: string
        required: false
        description: The identity id of the person whose signed change first recorded it
      attested_at:
        type: timestamp
        required: false
      note:
        type: string
        required: false
        description: Why it is unverifiable, where it is
  DueList:
    description: What is due at an organisation, now
    fields:
      as_of:
        type: timestamp
        required: true
      within:
        type: string
        required: true
      entries:
        type: "[]DueEntry"
        required: true
      unchased:
        type: "[]string"
        required: true
        description: Programmes installed here whose obligations no running, authorised due-sweep covers
      not_read:
        type: "[]NotRead"
        required: true
  DueEntry:
    description: One obligation's outstanding occurrences at one place, for one subject
    fields:
      obligation:
        type: string
        required: true
      activity:
        type: string
        required: true
      organisation:
        type: string
        required: true
      project:
        type: string
        required: false
      subject:
        type: string
        required: false
      oldest:
        type: string
        required: true
        description: The ref of the oldest outstanding occurrence
      due:
        type: timestamp
        required: true
        description: The oldest outstanding occurrence's due instant
      outstanding:
        type: int
        required: true
      overdue:
        type: bool
        required: true
      escalated:
        type: bool
        required: true
      responsible:
        type: string
        required: false
      escalated_to:
        type: string
        required: false
      authority:
        type: string
        required: false
      interval_basis:
        type: string
        required: false
      creates:
        type: string
        required: false
        description: The form an occurrence is filled in on, where the obligation declares creates
  NotRead:
    description: Something a due answer could not read, and why
    fields:
      repository:
        type: string
        required: true
      path:
        type: string
        required: false
        description: Absent where the whole repository could not be read
      reason:
        type: string
        required: true
  ProgrammeReadiness:
    description: One installed programme's readiness at an organisation
    fields:
      programme:
        type: string
        required: true
      tier:
        type: string
        required: false
        description: The tier the adoption record names, or the one asked for
      tiers:
        type: "[]TierReadiness"
        required: true
        description: Base first, each cumulative
      operating:
        type: OperatingReadiness
        required: false
        description: Absent where obligations could not be read at all, which is not zero
      measured:
        type: bool
        required: true
      unmeasured:
        type: "[]string"
        required: true
      not_in_force:
        type: "[]string"
        required: true
        description: Obligation ids a spec in the programme declares that no document carries
      chased:
        type: bool
        required: true
        description: Whether a running, authorised due-sweep covers this organisation
  TierReadiness:
    description: One tier's documented readiness, cumulative
    fields:
      tier:
        type: string
        required: true
      total:
        type: int
        required: true
      present:
        type: int
        required: true
      stale:
        type: int
        required: true
      uncited:
        type: int
        required: true
      missing:
        type: int
        required: true
      unknown:
        type: int
        required: true
      documented:
        type: int
        required: true
        description: present as a whole percentage of total
      measured:
        type: bool
        required: true
  OperatingReadiness:
    description: How many obligations in force are producing attested records
    fields:
      total:
        type: int
        required: true
      operating:
        type: int
        required: true
      not_operating:
        type: int
        required: true
      undetermined:
        type: int
        required: true
  SweepResult:
    description: What one due-sweep found and did
    fields:
      as_of:
        type: timestamp
        required: true
      advanced:
        type: map
        required: true
        description: Advances by topic
      told:
        type: int
        required: true
      not_told:
        type: int
        required: true
        description: Advances recorded and not sent, because the sweep is muted or nobody holds the position
      not_read:
        type: "[]NotRead"
        required: true
  ObligationAdvanced:
    description: The payload of every obligation topic
    fields:
      occurrence:
        type: string
        required: true
        description: The occurrence's ref
      obligation:
        type: string
        required: true
      activity:
        type: string
        required: true
      stage:
        type: string
        enum: [due_soon, overdue, escalated, attested]
        required: true
      from_stage:
        type: string
        required: false
        description: The highest stage announced before, where one was
      outstanding:
        type: int
        required: true
      grew:
        type: bool
        required: true
        description: True where it advanced because its size crossed a step, not its stage
      due:
        type: timestamp
        required: true
      responsible:
        type: string
        required: false
      escalated_to:
        type: string
        required: false
      organisation:
        type: string
        required: true
      project:
        type: string
        required: false
      programmes:
        type: "[]string"
        required: true
        description: The programmes installed at the organisation that the obligation belongs to. Empty for the tenant's own
  RowAdded:
    description: The payload of register.row_added
    fields:
      repository:
        type: string
        required: true
      register:
        type: string
        required: true
        description: The register's path
      key:
        type: string
        required: true
      columns:
        type: map
        required: false
        description: The row's cells, only from a register whose recorded scope is public or internal
      run:
        type: string
        required: false
        description: The run that wrote it, where the change applied a proposal naming one
      writer:
        type: string
        enum: [person, run, unknown]
        required: true
      organisation:
        type: string
        required: true
      project:
        type: string
        required: false
      not_announced:
        type: int
        required: false
        description: On the one extra event of a change past max_rows_per_change, how many rows were not announced
  ProgrammeAdopted:
    description: The payload of programme.adopted
    fields:
      installation:
        type: string
        required: true
      programme:
        type: string
        required: true
      organisation:
        type: string
        required: true
```

---

## Resources

What a person sees and operates of this service, declared as `schemas/resource` says. The kinds are
[`schemas/kinds`](../schemas/kinds.md#declared-kinds)'.

```yaml
resources:
  - kind: programme-adoption
    owner: programme-service
    type: ProgrammeInstallation
    identity: {field: uid, form: minted}
    label: programme
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: programme, access: create, present: text}
      - {name: organisation, access: create, present: text}
      - {name: state, access: read-only, present: choice}
      - {name: installed_by, access: read-only, present: text}
      - {name: installed_at, access: read-only, present: instant}
      - {name: withdrawn_by, access: read-only, present: text}
      - {name: withdrawn_at, access: read-only, present: instant}
      - {name: items, access: read-only}
      - {name: not_handed_over, access: read-only}
      - {name: build_plan, access: read-only}
    operations:
      list: {capability: "programme:read", binds: ListInstallations, items: installations, filters: [programme, state]}
      get: {capability: "programme:read"}
      create: {capability: "programme:install", binds: InstallProgramme}
    verbs:
      - name: withdraw
        capability: "programme:install"
        transition: withdraw
        preconditions:
          - the programme's installation at the organisation is installed
        in_flight:
          handling: drains
          says: every item under it stops starting runs and its starts at execution are withdrawn; a run already started finishes in execution's ledger
        effect: every item under it is withdrawn, every work authorisation naming one is revoked, and get_workflow answers NOT_FOUND for each; no document is deleted
        reversible: false
    states:
      initial_state: installed
      entity_type: ProgrammeInstallation
      state_field: state
      states:
        installed: {description: its items are held and may run}
        withdrawn: {description: its programme was un-adopted and every item stopped, terminal: true}
      transitions:
        - {name: withdraw, from: installed, to: withdrawn, trigger: manual, description: a person un-adopts the programme}
    events: [created, withdraw]

  - kind: installed-item
    owner: programme-service
    type: InstalledItem
    identity: {field: uid, form: minted}
    label: id
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: installation, access: read-only, present: reference, kind: programme-adoption}
      - {name: programme, access: read-only, present: text}
      - {name: id, access: read-only, present: text}
      - {name: kind, access: read-only, present: choice}
      - {name: scope, access: read-only, present: text}
      - {name: state, access: read-only, present: choice}
      - {name: muted, access: read-only, present: boolean}
      - {name: schedule, access: read-only}
      - {name: schedule_set, access: read-only}
      - {name: schedule_set_by, access: read-only, present: text}
      - {name: switched_by, access: read-only, present: text}
      - {name: authorisation, access: read-only}
      - {name: next_firing, access: read-only, present: instant, volatile: true}
    operations:
      list: {capability: "programme:read", binds: ListItems, items: items, filters: [kind, programme, state, muted]}
      get: {capability: "programme:read", binds: GetItem}
    verbs:
      - name: pause
        capability: "programme:operate"
        transition: pause
        preconditions:
          - the item is an operation or a workflow
        in_flight:
          handling: drains
          says: its starts at execution are paused and no new run starts; a run already started finishes
        effect: the item is paused
        reversible: {by: resume}
      - name: resume
        capability: "programme:operate"
        transition: resume
        preconditions:
          - the item is an operation or a workflow
        in_flight:
          handling: none
          says: a paused item has no run starting
        effect: the item is running, and its starts at execution resume, delivering what execution held for them
        reversible: {by: pause}
      - name: run
        capability: "programme:operate"
        body: ItemRun
        preconditions:
          - the item is an operation or a workflow, and not withdrawn
          - it has a live work authorisation
        in_flight:
          handling: continues
          says: a run already under way is unaffected; this starts one more
        effect: the item's first start at execution runs it once, now, or holds it until the body's not_before
        reversible: false
      - name: reschedule
        capability: "programme:operate"
        body: ItemSchedule
        preconditions:
          - the item is an operation or a workflow, and not withdrawn
          - its map declares a schedule
        in_flight:
          handling: continues
          says: a run already under way is unaffected; the next start follows the new clock
        effect: schedule_set is the body, schedule_set_by names the person, and its clock start is registered again with it
        reversible: {by: restore-schedule}
      - name: restore-schedule
        capability: "programme:operate"
        preconditions:
          - the item carries a schedule_set
        in_flight:
          handling: continues
          says: a run already under way is unaffected; the next start follows the map's clock
        effect: schedule_set is removed and its clock start is registered again with the map's clock
        reversible: {by: reschedule}
      - name: mute
        capability: "programme:switch"
        preconditions:
          - the item is unmuted and not withdrawn
        in_flight:
          handling: continues
          says: a run under way continues, and nothing it produces from now reaches a person
        effect: the item is muted and switched_by names the person
        reversible: {by: unmute}
      - name: unmute
        capability: "programme:switch"
        preconditions:
          - the item is muted and not withdrawn
        in_flight:
          handling: continues
          says: a run under way continues, and what it produces from now reaches people
        effect: the item is unmuted and switched_by names the person
        reversible: {by: mute}
    states:
      initial_state: paused
      entity_type: InstalledItem
      state_field: state
      states:
        paused: {description: installed, and its clock and its facts start nothing}
        running: {description: its starts at execution are running}
        withdrawn: {description: its installation was withdrawn, terminal: true}
      transitions:
        - {name: start, from: paused, to: running, trigger: installed with start running, or a notice installed, description: the map says it starts}
        - {name: pause, from: running, to: paused, trigger: manual, description: a person or muted-work operator pauses it}
        - {name: resume, from: paused, to: running, trigger: manual, description: a person or muted-work operator resumes it}
        - {name: withdraw, from: [paused, running], to: withdrawn, trigger: its installation is withdrawn, description: it stops for good}
    events: [created, paused, running, withdrawn, run, reschedule, restore-schedule, mute, unmute]
    relations:
      - {relation: installed_under, to: programme-adoption, field: installation}

  - kind: obligation
    owner: programme-service
    type: Obligation
    identity: {field: ref, form: declared-name}
    label: activity
    fields:
      - {name: ref, access: read-only, present: text}
      - {name: id, access: read-only, present: text}
      - {name: repository, access: read-only, present: text}
      - {name: path, access: read-only, present: text}
      - {name: activity, access: read-only, present: text}
      - {name: cadence, access: read-only, present: text}
      - {name: applies_to, access: read-only, present: text}
      - {name: responsible, access: read-only, present: text}
      - {name: records, access: read-only, present: text}
      - {name: authority, access: read-only, present: text}
      - {name: interval_basis, access: read-only, present: choice}
      - {name: satisfies, access: read-only}
      - {name: organisation, access: read-only, present: text}
      - {name: project, access: read-only, present: text}
      - {name: undeclarable, access: read-only, present: boolean}
      - {name: undeclarable_reason, access: read-only, present: text}
      - {name: counts, access: read-only, volatile: true}
    operations:
      list: {capability: "programme:read", binds: ListObligations, items: obligations, filters: [responsible, records, undeclarable, project]}
      get: {capability: "programme:read", binds: GetObligation}

  - kind: occurrence
    owner: programme-service
    type: Occurrence
    identity: {field: ref, form: declared-name}
    label: key
    fields:
      - {name: ref, access: read-only, present: text}
      - {name: obligation, access: read-only, present: reference, kind: obligation}
      - {name: key, access: read-only, present: text}
      - {name: period, access: read-only, present: text}
      - {name: subject, access: read-only, present: text}
      - {name: subject_label, access: read-only, present: text}
      - {name: origin, access: read-only, present: choice}
      - {name: state, access: read-only, present: choice, volatile: true}
      - {name: due, access: read-only, present: instant}
      - {name: overdue, access: read-only, present: boolean, volatile: true}
      - {name: escalated, access: read-only, present: boolean, volatile: true}
      - {name: escalated_to, access: read-only, present: text}
      - {name: responsible, access: read-only, present: text}
      - {name: organisation, access: read-only, present: text}
      - {name: project, access: read-only, present: text}
      - {name: records, access: read-only, present: text}
      - {name: attested_by, access: read-only, present: text}
      - {name: attested_at, access: read-only, present: instant}
      - {name: note, access: read-only, present: text}
    operations:
      list: {capability: "programme:read", binds: ListOccurrences, items: occurrences, filters: [obligation, state, responsible, overdue, escalated]}
      get: {capability: "programme:read", binds: GetOccurrence}
    relations:
      - {relation: occurrence_of, to: obligation, field: obligation}
```

**An obligation and an occurrence are derived, and a person changes neither
here.** Each declares `list` and `get` and nothing else. An obligation is
changed by editing the document that declares it, through content; an
occurrence moves when a row is written into its register, and reaches
`attested` only by a person's signed change there. Neither announces a
lifecycle event: what advances is published as the topics in
[Events it publishes](#events-it-publishes).

**The verbs are the routes' acts, at the uniform address.** `pause`,
`resume`, `run`, `reschedule`, `restore-schedule`, `mute` and `unmute` are the
acts of the operation and workflow routes in [Endpoints](#endpoints), keyed by
the item's `uid` rather than by programme and `id`, under the same rules
([Who May Do What](#who-may-do-what)); `withdraw` is `WithdrawProgramme`'s. A
notice is refused every verb but `mute` and `unmute` with `INVALID_STATE`.

---

## Configuration

```yaml
programme_service:
  due_soon_window: 30d        # how far ahead an occurrence is due soon, and
                              # what GET /v1/programme/due shows by default
  status_window: 90d          # the window an obligation's counts, its
                              # occurrences and operating readiness are taken
                              # over when a request names none
  max_window: 400d            # the longest window a request may ask for
  max_rows_per_change: 100    # rows of one change announced one by one
  steps: [3, 10, 30, 100, 300, 1000]   # the sizes at which an overdue lapse
                                       # is announced again
  timezone: <IANA name>       # the installation's local time, which a map's
                              # `at` and every period boundary are read in
```

Each value may be changed by an operator in the tenant's configuration, and
none is a programme's to set: a programme declares what is owed, never how
far ahead the tenant looks.

---

## Security

```yaml
security:
  trust_model:
    description: |
      The service trusts a person's authority only on a pass, and its own
      authority only for work that reaches nobody until a person unmutes it,
      and for reads a person allowed on a work authorisation. It never holds a
      person's token, never runs work under the authority of the person who
      switched it on, and never answers what a restricted record says.

  boundaries:
    - boundary: Person → Programme Service. Only through the admin gateway,
        on a pass addressed here. An operator token is refused
    - boundary: Programme Service → Content. Reads the adopted map, the
        documents that declare obligations, registers and their change
        logs. Writes nothing
    - boundary: Programme Service → Execution. Its own starts, registered and
        switched on its registration token holding execution:register
    - boundary: Execution → Programme Service. get_workflow, and the
        actions an operation or a phase names in does, from execution alone,
        on a work pass naming an item installed here
    - boundary: Every component a firing reaches. Only on a work pass, under
        a work authorisation a person made for the item, within its
        capabilities
    - boundary: Programme Service → Notification. Positions and a message.
        Never a person or a channel
    - boundary: Programme Service → every subscriber. Identities, states and
        dates. No cell of a register above internal

  enforcement:
    - rule: Nothing reaches a person until a person unmutes it
      mechanism: Every item is installed muted. Unmute needs programme:switch,
        which is person only. A muted due-sweep tells nobody
    - rule: Work that reaches people is started, stopped and moved by a person
      mechanism: Pause, resume, run and reschedule on an unmuted item are
        admitted on a pass only
    - rule: An installation is never reported whole when it is not
      mechanism: Every block not handed to its owner is listed by name in
        the answer, with the build plan that would hand it over
    - rule: No machine decides
      mechanism: No action or worker capability approves, rejects, closes,
        attests or signs. Only a person's signed change reads attested
    - rule: What a record says does not leave through a due answer
      mechanism: Labels and cells are answered and published only from
        registers at public or internal
```

---

## Implementation Notes

- Read the map from the tenant's adopted copy in content. A template edited
  by its organisation is the one that runs
  ([`schemas/programme.md`](../schemas/programme.md#the-tenants-copy-is-the-tenants)).
- Matching on programme, `id` and scope is what keeps a second installation
  from creating a second clock. The `uid` is minted once and kept.
- A muted item's runs still produce output. Execution keeps it in its run
  ledger, so that a person can compare it with what they expected before
  they unmute. This service keeps no copy.
- Report a `does:` name this build does not run by name, with the names it
  does run. Never skip it.
- Reading every entry at an organisation for its frontmatter is the cost of
  deriving obligations. A cache keyed by each entry's `ContentIdentity` is
  allowed, because a changed entry has a changed identity; it is rebuilt from
  content and never cited.
- Compute an occurrence's due instant from its key, never carry it beside the
  key, so that the two cannot disagree. Every period key round-trips.
- An empty register and a register that could not be read are different
  answers. The first owes `missing`; the second is `unverifiable` with a
  `not_read` entry.

---

## Verification Checklist

- [ ] Every route in [Endpoints](#endpoints) but `GET /livez`, `GET /readyz`, `POST /v1/message`, `POST /v1/event`, `POST /v1/services` and `POST /v1/programme/notifications` is declared among the manifest's `pass_routes`, with the one capability its row gives ([Endpoints](#endpoints))
- [ ] An operator token on any route is refused with `PASS_REQUIRED` ([Who May Do What](#who-may-do-what) rule 1, [Error Handling](#error-handling))
- [ ] `POST /v1/programme/installations` on a registration or channel token is refused with `FORBIDDEN`, and installs nothing ([Who May Do What](#who-may-do-what) rule 2, [Error Handling](#error-handling))
- [ ] An installation for a programme the organisation has no `adoption.md` for is refused with `PROGRAMME_NOT_ADOPTED`, and installs nothing ([Installing](#installing), [Error Handling](#error-handling))
- [ ] Every item an installation creates is muted, carries a `uid`, and is paused unless its `start` is `running` ([Installing](#installing))
- [ ] Installing the same programme twice at one scope creates no second item and publishes no second `programme.adopted` ([Installing](#installing), [Events it publishes](#events-it-publishes))
- [ ] An installation asked for at a project is refused with `INVALID_REQUEST`, naming the organisation ([Error Handling](#error-handling))
- [ ] An installation lists every block it could not hand to an owner, with the owner named, and a `build_plan` of every service it needs that the tenant's directory does not list, and does not call itself complete ([Installing](#installing), [Error Handling](#error-handling))
- [ ] A route other than `/livez`, `/readyz`, `/v1/message`, `/v1/event`, `/v1/services` and installing, missing `organisation`, or a route with `{id}` in its path missing `programme`, is refused with `INVALID_REQUEST` ([Endpoints](#endpoints), [Error Handling](#error-handling))
- [ ] With one programme installed at two organisations, `DELETE /v1/programme/installations/{programme}` withdraws only the organisation it names ([Withdrawing](#withdrawing))
- [ ] The mute and unmute routes of operations, workflows and notices each need `programme:switch`, and the service never declares `programme:switch` on its own manifest ([Endpoints](#endpoints))
- [ ] Pausing, resuming, running or rescheduling an unmuted item on a component's registration token or a work pass is refused with `FORBIDDEN`. The same act on a muted item is admitted with `programme:operate` ([Endpoints](#endpoints), [Who May Do What](#who-may-do-what) rules 2 and 3)
- [ ] Pausing, running or rescheduling a notice or a withdrawn item, and rescheduling an item whose map declares no `schedule`, is refused with `INVALID_STATE` ([Error Handling](#error-handling), [Rescheduling](#rescheduling))
- [ ] An `ItemSchedule` outside the map's `schedule` vocabulary is refused with `INVALID_REQUEST`; one inside it is recorded as `schedule_set` beside the map's `schedule`, and `DELETE` of it hands execution the map's clock again ([Rescheduling](#rescheduling), [Error Handling](#error-handling))
- [ ] A notice is sent once when its fact first becomes true, and not again while the fact stays true ([Telling](#telling))
- [ ] An advance answered `reached_nobody`, `not_authorised` or `holders_unreadable` is recorded as not delivered, with the positions answered `unheld` ([Telling](#telling))
- [ ] Every `agent:` phase's `input` is an `InstructionTask` carrying the instruction, its `needs:`, the adopted map as `source` and the programme's skills with no `for` ([The prompt worker](#the-prompt-worker))
- [ ] A muted notice that advances reaches nobody, and its advance is recorded as not sent; once unmuted, its next advance is sent ([Telling](#telling), [Endpoints](#endpoints))
- [ ] An occurrence that advances under a muted `due-sweep` tells nobody and is recorded as not sent; under an unmuted one, `overdue` tells its `responsible` position and `escalated` tells its `escalate.to` position as well ([Telling](#telling))
- [ ] Pausing a workflow starts no new run and lets a started run finish; `get_workflow` for a withdrawn workflow answers `NOT_FOUND` ([Endpoints](#endpoints), [Withdrawing](#withdrawing), [Interfaces](#interfaces))
- [ ] `DELETE /v1/programme/installations/{programme}` stops every item under it, withdraws each of its starts at execution and deletes no document ([Endpoints](#endpoints), [Withdrawing](#withdrawing))
- [ ] An `agent:` item is reported as not runnable while no prompt worker runs, or while the model service's route is not served, and is never reported as having run ([Known Gaps](#known-gaps))
- [ ] An installed item with no live work authorisation is reported as not authorised and never run ([Installing](#installing))
- [ ] A work pass whose `definition` names an installed `agent:` item and whose `cap` carries `programme:read` is answered `GET /v1/programme/due` at the item's organisation, and refused with `FORBIDDEN` naming another organisation ([What agent work may start and tell](#what-agent-work-may-start-and-tell) 1)
- [ ] `POST /v1/programme/workflows/{id}/runs` on such a work pass carrying `programme:dispatch` starts a run of a running workflow of the same programme by `RunScheduleNow` with the pass's `run` as `parent`; naming a paused one is refused with `PROGRAMME_ITEM_NOT_RUNNING`, and one of another programme with `NOT_FOUND` ([What agent work may start and tell](#what-agent-work-may-start-and-tell) 2, [Error Handling](#error-handling))
- [ ] The same request on a work pass that does not carry `programme:dispatch`, or on an unmuted workflow on a registration token, is refused with `FORBIDDEN` and starts nothing ([What agent work may start and tell](#what-agent-work-may-start-and-tell), [Who May Do What](#who-may-do-what) rule 2)
- [ ] `POST /v1/programme/notifications` on a pass is refused with `FORBIDDEN`; on a work pass carrying `programme:notify` naming a position the adopted map does not name it is refused with `INVALID_REQUEST`, and for a muted item with `PROGRAMME_ITEM_NOT_RUNNING`, and nobody is told ([What agent work may start and tell](#what-agent-work-may-start-and-tell) 3, [Error Handling](#error-handling))
- [ ] `NotifyFromItem` sent twice in one run with the same body makes one notification ([What agent work may start and tell](#what-agent-work-may-start-and-tell) 3)
- [ ] `get_workflow` and a `does:` action are answered only on a work pass whose `identity_id` is this service's and whose `definition` names an item installed here, and one naming no such item is refused with `NOT_FOUND` ([Interfaces](#interfaces))
- [ ] Withdrawing a programme revokes every work authorisation naming one of its items ([Withdrawing](#withdrawing))
- [ ] An `agent:` item's authorisation is asked for with the capabilities its `needs:` words come to in [`architecture/prompt-worker`](prompt-worker.md#needs-comes-to-these-capabilities), and none other; an empty `needs:` comes to `read`'s ([What a `needs:` ceiling comes to](#what-a-needs-ceiling-comes-to))
- [ ] A `does:` naming an action outside [The `does:` Actions](#the-does-actions) is reported at install with the actions this build runs, and `GET /v1/programme/actions` answers the same list
- [ ] Every obligation reported is one a document in content declares; a spec's obligation no document carries is reported in readiness's `not_in_force` and owes no occurrence ([Where an obligation is read from](#where-an-obligation-is-read-from), [Readiness](#readiness))
- [ ] An obligation with a word outside a closed vocabulary is reported `undeclarable` with the field and why, and has no occurrences ([Where an obligation is read from](#where-an-obligation-is-read-from))
- [ ] A cadence obligation owes one occurrence per ended period at each place, and per live subject where it declares `per:`; a working-day cadence owes none on a Saturday or a Sunday; every period key parses back to the period it names ([Occurrences](#occurrences))
- [ ] A `for:` obligation owes one occurrence per trigger row, due as `for.due` gives from that row's date ([Occurrences](#occurrences))
- [ ] An occurrence with a row and no signed change reads `recorded`, never `attested`; one whose recording change carries a verified statement reads `attested`, with `attested_by` the person who signed it ([The three states, and a fourth](#the-three-states-and-a-fourth))
- [ ] An obligation with no `records:`, or whose register could not be read, reports its occurrences `unverifiable` with a `note`, and the unread register in `not_read` ([The three states, and a fourth](#the-three-states-and-a-fourth), [Error Handling](#error-handling))
- [ ] An occurrence overdue past `escalate.after` and neither recorded nor attested is `escalated`, keeps its `responsible` position and adds `escalated_to` ([Escalation](#escalation))
- [ ] A sweep publishes each topic once per occurrence per stage, and again only when an overdue lapse's size crosses a step; three sweeps with nothing changed publish nothing after the first ([How an occurrence advances](#how-an-occurrence-advances))
- [ ] `GET /v1/programme/due` includes every overdue entry whatever `within` says, orders most overdue first, names positions and never a person, and lists in `unchased` every installed programme no running, authorised `due-sweep` covers ([What is due now](#what-is-due-now))
- [ ] Reading what is due publishes nothing and changes no announcement mark ([Events it publishes](#events-it-publishes))
- [ ] A subject's label, a row's columns and an event's cells come only from registers whose recorded scope is `public` or `internal` ([What a person is answered](#what-a-person-is-answered))
- [ ] A register first heard announces none of the rows it already holds; an edited row announces nothing; each new row announces one `register.row_added` ([Hearing a row](#hearing-a-row))
- [ ] A notice advances on an `obligation.*` fact only where the obligation belongs to the notice's programme, and every `obligation.*` event names those programmes ([Starting on a fact](#starting-on-a-fact))
- [ ] Every installed operation and workflow has one start at execution for each of its `schedule`, `on:`, `when:` and `for:`, keyed `<uid>.clock`, `<uid>.on`, `<uid>.when` and `<uid>.for`, registered paused or running and muted as the item is; pausing, resuming, running, muting, unmuting and rescheduling the item switch or re-register them there ([Starting on a fact](#starting-on-a-fact))
- [ ] Every `register.row_added` names the run that wrote the row where the change applied a proposal naming one, and `writer: unknown` where the change or proposal could not be read ([Hearing a row](#hearing-a-row))
- [ ] A `when:` whose `count.distinct` names a field no event of its type carries is reported on its item at install as a condition that can never fire ([Counted conditions](#counted-conditions))
- [ ] Readiness reports documented per tier, cumulative, and operating as operating, not operating and undetermined; an obligation with no occurrence in the window is undetermined and never counted against; a number that is a floor sets `measured` false and says why ([Readiness](#readiness))
- [ ] An artifact no document declares is `unknown`, never `missing`, while the fabric cannot be read ([Readiness](#readiness))
- [ ] The manifest claims `obligation.*`, `register.*` and `programme.*` in `publishes`, and every topic in [Events it publishes](#events-it-publishes) is published with the payload its row names ([Registration and Standalone Operation](#registration-and-standalone-operation))
- [ ] With no orchestrator URL configured, the service starts, `GET /livez` answers live, `GET /readyz` answers not ready, and every protected route answers `401` ([Registration and Standalone Operation](#registration-and-standalone-operation))
- [ ] The uniform address serves `programme-adoption`, `installed-item`, `obligation` and `occurrence` as [Resources](#resources) declares them, and refuses a notice every verb but `mute` and `unmute` with `INVALID_STATE` ([Resources](#resources))
