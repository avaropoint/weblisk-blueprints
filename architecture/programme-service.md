<!-- blueprint
type: architecture
name: programme-service
version: 1.0.1
requires: [protocol/types, protocol/identity, patterns/workflow, architecture/content, architecture/orchestrator, architecture/admin]
platform: any
tier: free
adoption: opt-in
-->

# Weblisk Programme Service

The tenant service that holds the standing work an adopted programme brings:
its operations, its workflows and its notices. It also states what it hands
to execution, notification and the prompt worker, and how a person's decisions
reach the admin gateway's one inbox.

## Overview

[`schemas/programme.md`](../schemas/programme.md#the-package--what-a-programme-brings-besides-its-documents)
declares a programme's package and gives each block an owner. Content holds
the documents, forms and skills. Everything else in the table goes to the
**programme service**, which keeps it, and to the services that service hands
the work to:

| what | held by | run or delivered by | specified |
|---|---|---|---|
| an installed operation | the programme service | execution fires its clock and its events | here, [Endpoints](#endpoints) |
| an installed workflow definition | the programme service | execution holds its runs, waits and timers | here, and [`patterns/workflow`](../patterns/workflow.md) for the definition |
| an installed notice | the programme service | notification tells each position's holders, each their own way | here, [Notification](#notification) |
| an `agent:` instruction | the programme service records it on its operation or step | the prompt worker runs it | here, [The prompt worker](#the-prompt-worker) |
| a decision a person owes | the owner whose work waits on it | a person, through the admin gateway's one inbox | here, [The decision inbox](#the-decision-inbox) |

This document is the home of four things: the programme service's routes, the
capability each route needs, the rule for what only a person may do (and on
which token), and the contract each neighbouring service is handed. The
fields a programme author writes, their vocabularies and their refusals belong
to [`schemas/programme.md`](../schemas/programme.md), and are not restated
here.

> **Scope boundary.** No component blueprint implements this document yet,
> and a tenant today runs none of these services
> ([Known Gaps](#known-gaps)). Execution is the service
> [`architecture/domain`](domain.md) already names: cron, task and workflow
> merged into one. Until its blueprint exists,
> [`agents/workflow`](../agents/workflow.md) and
> [`agents/task`](../agents/task.md) describe the runner. Nothing here
> describes what is due, or occurrences, or readiness. Those are also the
> programme service's, and are not specified yet.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=3.0.0 <6.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category, retryable]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, via, action, target, status]
        # pass_routes is how the admin gateway learns which of these routes a
        # person's request may reach, and what each needs. See Who May Do What
        - name: AgentManifest
          fields_used: [name, capabilities, pass_routes]
        - name: PassRoute
          fields_used: [method, path, capabilities]
        - name: Capability
          fields_used: [name, resources]
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=2.0.0 <4.0.0"
    bindings:
      types:
        # type and aud say a person's request reached this service on a pass
        # addressed to it; cap is what it may use; identity_id names who acted;
        # act names the gateway that carried it
        - name: WLToken
          fields_used: [type, aud, act, cap, identity_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/workflow
    version: ">=2.0.0 <4.0.0"
    bindings:
      types:
        # What an installed workflow becomes, and what execution answers
        # get_workflow with (schemas/programme.md, How a workflow maps)
        - name: WorkflowDefinition
          fields_used: [name, description, trigger, phases]
        - name: WorkflowPhase
          fields_used: [name, agent, action, input, depends_on, approval]
        - name: WorkflowExecution
          fields_used: [id, workflow_name, status, phases, started_at, completed_at]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/content
    version: ">=4.0.0 <6.0.0"
    bindings:
      types:
        # The adopted map and adoption.md are read from content, never copied
        - name: ContentEntry
          fields_used: [path, identity, scope]
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
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/admin
    version: ">=4.0.0 <5.0.0"
    bindings:
      behaviors:
        # The one door a person's request arrives through
        - name: admin-gateway-authorization
          usage: Relied on, never called here. A person's request reaches this service only on a route its manifest declares among pass_routes, on a pass naming every capability that route declares
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
 person ──► admin gateway ──pass──► programme service ──► content (reads the map, adoption.md)
                  ▲                    │      ▲
                  │                    │      │ get_workflow, a does: action
                  │       definitions, │      │
                  │       schedules    ▼      │
                  │                  execution ──► prompt worker ──► model service
                  │                    │    (an agent: phase)         (not specified)
          one     │                    │
          inbox ◄─┴── decisions        └──► (a fact) ──► programme service ──notify──► notification
          (owners serve their own)
```

- **The programme service holds and never runs.** It keeps each installed
  operation, workflow and notice, with its state. It hands clocks and
  definitions to execution, and a notice that has advanced to notification.
- **Execution runs and never holds a programme.** It fires the clock and
  events, and keeps every run in its one run ledger
  ([`architecture/domain`](domain.md), Execution replaces the Workflow and
  Task agents). It fetches a definition from its owner with `get_workflow`,
  as it fetches a domain's.
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
  unmuted**
- What each installation could not hand to an owner, by block and `id`, with
  the missing service named
- The `WorkflowDefinition` each installed workflow becomes, served to
  execution with `get_workflow`
- Running each `does:` action an operation or a workflow phase names, when
  execution invokes it
- Deciding when a notice has advanced, and asking notification to tell its
  positions
- **The due answers**: occurrences, what is due and readiness. This document
  does not specify them ([Known Gaps](#known-gaps))

### Does NOT Own

- **The programme's files.** The map, specs, forms, skills and `adoption.md`
  are content's. The adoption itself is the person's act that writes them
  ([`schemas/programme.md`](../schemas/programme.md#adopting-a-programme))
- **Runs, timers and waits.** They are execution's, in its one run ledger
- **Who holds a position, and how a person is told.** The first is tenant
  data in content. The second is each person's preference, held by
  notification
- **A model.** The prompt worker asks the tenant's model service
- **Any decision.** A decision belongs to the owner whose work waits on it,
  and only a person makes one ([The decision inbox](#the-decision-inbox))

---

## Endpoints

| Method | Path | Operation | Auth | Capability | Purpose |
|--------|------|-----------|------|------------|---------|
| POST | /v1/programme/installations | InstallProgramme | yes | `programme:install` | Install an adopted programme's operations, workflows and notices at its organisation, every one muted. A pass only ([Who May Do What](#who-may-do-what)) |
| GET | /v1/programme/installations | ListInstallations | yes | `programme:read` | What is installed at each scope, and every block not handed to its owner, by name, with the missing service |
| DELETE | /v1/programme/installations/{programme} | WithdrawProgramme | yes | `programme:install` | Withdraw everything installed under one programme at a scope when it is un-adopted. Stops them and records it. Deletes no document. A pass only |
| GET | /v1/programme/operations | ListOperations | yes | `programme:read` | Installed operations in scope, each with its two switches and its next firing |
| GET | /v1/programme/operations/{id} | GetOperation | yes | `programme:read` | One operation, its declaration as installed, and its changes |
| POST | /v1/programme/operations/{id}/pause | PauseOperation | yes | `programme:operate` | Stop its clock. On an unmuted operation, a pass only |
| POST | /v1/programme/operations/{id}/resume | ResumeOperation | yes | `programme:operate` | Start its clock. On an unmuted operation, a pass only |
| POST | /v1/programme/operations/{id}/runs | RunOperation | yes | `programme:operate` | Ask execution to run it once, now. On an unmuted operation, a pass only |
| POST | /v1/programme/operations/{id}/mute | MuteOperation | yes | `programme:switch` | Withhold from people everything its runs produce |
| POST | /v1/programme/operations/{id}/unmute | UnmuteOperation | yes | `programme:switch` | Let its runs reach people |
| GET | /v1/programme/workflows | ListWorkflows | yes | `programme:read` | Installed workflow definitions in scope, each with its two switches |
| GET | /v1/programme/workflows/{id} | GetWorkflow | yes | `programme:read` | One definition, as the programme declared it and as execution is given it |
| POST | /v1/programme/workflows/{id}/pause | PauseWorkflow | yes | `programme:operate` | Start no new run. Runs already started continue. On an unmuted workflow, a pass only |
| POST | /v1/programme/workflows/{id}/resume | ResumeWorkflow | yes | `programme:operate` | Start runs again. On an unmuted workflow, a pass only |
| POST | /v1/programme/workflows/{id}/mute | MuteWorkflow | yes | `programme:switch` | Withhold from people everything its runs produce |
| POST | /v1/programme/workflows/{id}/unmute | UnmuteWorkflow | yes | `programme:switch` | Let its runs reach people |
| GET | /v1/programme/notices | ListNotices | yes | `programme:read` | Installed notices, each with its mute switch, and each time one advanced: when, which positions, and whether notification accepted it |
| POST | /v1/programme/notices/{id}/mute | MuteNotice | yes | `programme:switch` | Withhold the notice from people. It still advances, and each advance is recorded as not sent |
| POST | /v1/programme/notices/{id}/unmute | UnmuteNotice | yes | `programme:switch` | Let the notice reach its positions the next time it advances |
| GET | /livez | Livez | no | | Liveness, for the supervisor that restarts the service |
| GET | /readyz | Readyz | no | | Readiness, for the supervisor waiting on its start |

**A notice has its own mute switch and no clock.** A notice is a block of its
own in the map, belonging to no operation or workflow
([`schemas/programme.md`](../schemas/programme.md#notices--who-is-told-what)),
so it is muted and unmuted by itself, and has nothing to pause.

**Every request names its organisation and programme.** Installing names
both in its body. Every other route but `/livez` and `/readyz` carries the
organisation as the query parameter `organisation`, which is required. A route with
`{id}` in its path also requires the query parameter `programme`, a list
route takes it to narrow the list, and withdrawing names the programme in
its path. An item's `id` is local to its programme
([`schemas/programme.md`](../schemas/programme.md#notices--who-is-told-what)),
so `{id}` alone names nothing: the item is the one with that programme, `id`
and organisation. A route missing a parameter it requires is refused with
`INVALID_REQUEST`. Naming an organisation grants nothing: the route's
capability is checked as on any other request.

Each route in the table but `/livez` and `/readyz` is declared among the
manifest's `pass_routes`, with the one capability in its row and no body
requirement. The admin gateway carries a person's request here only on a
route that list declares ([`architecture/admin`](admin.md#contracts),
`admin-gateway-authorization`), so the list and the table MUST agree.

**`pass_routes` is not the only way in.** The pause, resume and run routes
of an operation or a workflow also admit a registered component's own
registration token carrying `programme:operate`, while the item is muted
([Who May Do What](#who-may-do-what), rule 3). Every other route admits a
pass only.

The service declares `programme:read`, `programme:install` and
`programme:operate` on its manifest. It checks `programme:switch` but never
holds it, as [`protocol/types`](../protocol/types.md#capability) requires of
a person-only capability.

---

## Interfaces

**Actions it answers** on [`POST /v1/message`](../protocol/spec.md#post-v1message)
(`agent:message`), from execution alone:

| action | answers |
|---|---|
| `get_workflow` | The `WorkflowDefinition` an installed workflow became, as [`patterns/workflow`](../patterns/workflow.md) Phase 2 fetches one from its source. A withdrawn workflow answers `NOT_FOUND` |
| any action a `does:` names | Runs that deterministic action for the operation or phase, and answers its outcome. A name this build does not run answers `NOT_FOUND`, never success |

**What it hands each neighbour:**

| to | what | how |
|---|---|---|
| execution | each operation's and each workflow's `schedule`, `on`, `when` or `for`, registered as its start. Pausing an item pauses its start there, so no new run begins | when a start fires, execution runs the definition it fetches with `get_workflow`, as [`architecture/domain`](domain.md) states for any owner's definition: `workflow.trigger` out, `workflow.completed` or `workflow.failed` back |
| notification | a notice that has advanced: its `says`, its `to` positions, and the fact it is about | [Notification](#notification) |
| the prompt worker | nothing directly. An `agent:` phase names the worker as its agent, and execution dispatches it | [The prompt worker](#the-prompt-worker) |

## Error Handling

| Code | When |
|---|---|
| `PASS_REQUIRED` | An operator token was presented on any route ([`protocol/identity`](../protocol/identity.md#the-pass), rule 4) |
| `PASS_AUDIENCE_MISMATCH` | A pass addressed to another component |
| `FORBIDDEN` | The pass does not carry the route's capability; or a route this document reserves to a pass was reached on any other token |
| `INVALID_REQUEST` | An installation asked for at a project rather than its organisation, naming the organisation; a body that is not an installation; or a route missing the `organisation` or `programme` it requires |
| `NOT_FOUND` | No installed item with that programme and `id` at the organisation named |

An installation that hands some blocks to their owners and not others is not
an error. It answers `200`, lists every block it could not hand over, and
does not call itself complete
([`schemas/programme.md`](../schemas/programme.md#the-package--what-a-programme-brings-besides-its-documents)).

---

## Data Flow

### Installing

1. A person adopts a programme at an organisation
   ([`schemas/programme.md`](../schemas/programme.md#one-act-by-a-person-at-the-organisation)).
   The files are written into content first.
2. The same person's client sends `POST /v1/programme/installations` through
   the admin gateway, on the person's own pass. It names the organisation and
   the programme.
3. The service reads the adopted `map.md` from content, as it is in the
   tenant's copy, never from the published template. It installs each
   operation, workflow and notice. Each is paused or running as its `start`
   says, and every one is muted.
4. It hands each schedule and definition to execution. It answers every block
   it could not hand to an owner, by name, with the missing service.
5. Nothing reaches a person until somebody holding `programme:switch` unmutes
   an item, on their own pass.

### Firing

1. Execution fires a clock or an event and starts a run in its own ledger.
2. It fetches the definition with `get_workflow`. It dispatches each phase:
   a `does:` phase to this service, and an `agent:` phase to the prompt
   worker.
3. What a muted item's run produces reaches nobody. It is kept in
   execution's run ledger, with the run, so that a person can compare it
   before unmuting. The programme service holds no run output, and the
   prompt worker keeps nothing.

### Telling

1. A fact one of the `on:` events names becomes true.
2. The service decides whether the notice has advanced. It advances when the
   fact first becomes true, and not again while it merely stays true.
3. If it has advanced and the notice is unmuted, the service asks
   notification to tell the `to` positions. It records that it asked, and
   what notification answered. A muted notice's advance is recorded as not
   sent, and nobody is told.

### Withdrawing

When a person un-adopts
([`schemas/programme.md`](../schemas/programme.md#un-adopting)), their client
sends `DELETE /v1/programme/installations/{programme}?organisation=…` on
their pass. Every item installed under the programme at that organisation
stops, the withdrawal is recorded, and
`get_workflow` answers `NOT_FOUND` for each of its definitions. Runs already
in execution's ledger stay there.

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
   person only; and pausing, resuming or running an item **while it is
   unmuted**, because starting or stopping work that reaches people is a
   person's decision. A registration or channel token on one of these is
   refused with `FORBIDDEN`, whatever capabilities it carries. An operator
   token is refused with `PASS_REQUIRED`, as on every route (rule 1).
3. **A service or an agent may operate muted work.** Holding
   `programme:operate` on its own registration, it may pause, resume or run
   an item while that item is muted. Nobody is reached. A service or an agent
   may also propose an adoption as content proposals, and a person decides
   them ([`architecture/content`](content.md#who-may-move-an-entry)).
4. **Work that runs unattended is the service's own, never a person's.** A
   firing runs under the programme service's manifest. A `needs:` ceiling
   narrows an agent's authority and never widens it. Neither inherits the
   authority of the person who installed or unmuted the item. That person is
   recorded as who switched it on, not as who ran it.
5. **No machine step decides.** No action, `needs` capability or worker
   approves, rejects, closes, attests or signs
   ([`schemas/programme.md`](../schemas/programme.md#workflows--multi-step-work-with-waits-and-approvals)).
   Those acts are a person's, in [the decision inbox](#the-decision-inbox).

Each act records an `AuditEntry`. On a pass, the person is the `actor` (by
the pass's `identity_id`) and the gateway that carried the request is `via`.

---

## The Services It Hands Work To

### Execution

Execution is [`architecture/domain`](domain.md)'s merged cron, task and
workflow service. Programme work asks of it only what a domain's work asks:
it runs `patterns/workflow` declarations, fetched from their owner, and keeps
every run, wait and timer in its one ledger. A programme's workflow becomes
one such declaration, as
[`schemas/programme.md`](../schemas/programme.md#how-a-workflow-maps-onto-patternsworkflow)
maps it.

**People read runs through the admin gateway's Workflows group.** Execution
is the provider of `GET /v1/admin/workflows` and `GET /v1/admin/workflows/{id}`
([`architecture/admin`](admin.md#the-admin-api-is-an-aggregate)). Each needs
`admin:read`, on a pass addressed to execution, and answers the shape
[`architecture/admin`](admin.md#get-v1adminworkflows) gives. A run of a
programme's workflow names its definition in `workflow_name`. A run with no
domain has no `domain_name`. Execution serves these two routes, and declares
them among its `pass_routes`, once its blueprint requires this one.
[`agents/workflow`](../agents/workflow.md) does neither yet, so until then
the gateway answers both with `ADMIN_GROUP_UNAVAILABLE`.

### Notification

Notification tells a person once, in their own way. From the programme
service it accepts a **notify by position**: the notice's `id`, its `says`,
its `to` positions and the fact it is about. It finds who holds each
position, words the message from `says`, and delivers by each holder's own
preference. [`patterns/notification`](../patterns/notification.md)
describes channels and delivery, and
[`agents/email-send`](../agents/email-send.md) is its email adapter.

A notice names positions only, never a person or a channel
([`schemas/programme.md`](../schemas/programme.md#notices--who-is-told-what)).
A notice that reaches nobody, because nobody holds a position it names, is
reported to the programme service, never treated as delivered.

### The prompt worker

The prompt worker is the tenant's one shared runner of `agent:` instructions.
A programme never brings an agent component
([`schemas/programme.md`](../schemas/programme.md#agents-are-instructions-never-components)).
Execution dispatches an `agent:` phase to it, with the instruction and the
`needs:` ceiling as the phase's `input`. The worker:

- runs with the intersection of the ceiling, its own manifest's declaration
  and the identity under the run, and never more;
- asks the tenant's model service for each completion, and reaches no model
  any other way;
- writes only through an owner's API, as a proposal where that owner requires
  one, and keeps nothing of its own. The run's record is execution's.

### The decision inbox

**Each owner serves its own decisions, and the admin gateway composes one
inbox from them.** There is no approval service. A decision is a person's
act, made on their own pass, at the owner whose work is waiting on it:

- a content proposal is decided at content, with
  `POST /v1/content/proposals/{id}/decision` and `content:decide`
  ([`architecture/content`](content.md#who-may-move-an-entry)). This is the
  one kind of decision a tenant can serve today;
- a workflow's `approval` or `task` step is a wait execution holds, and is
  decided at execution.

No machine makes a decision ([Who May Do What](#who-may-do-what), rule 5).
How each decision is shaped is
[`patterns/approval`](../patterns/approval.md)'s.

---

## Known Gaps

**No component blueprint implements any of this.** Nothing builds the
programme service, execution, notification or the prompt worker. A tenant
runs none of them, so an adoption today hands no block to an owner, and says
so.

**Execution's blueprint is not written.** Until it is,
[`architecture/domain`](domain.md) and the
[`agents/workflow`](../agents/workflow.md) and
[`agents/task`](../agents/task.md) blueprints describe the runner. None of
them requires this document, so `/v1/admin/workflows` stays
`ADMIN_GROUP_UNAVAILABLE`.

**How execution proves it is firing an owner's definition is not settled.**
[`architecture/domain`](domain.md) says a definition runs "on a pass minted
for the definition's owner". [`protocol/identity`](../protocol/identity.md#the-pass)
mints a pass only from a person's operator token. For unattended work, no
token satisfies both statements yet.

**A person's step has nowhere to be decided.** `patterns/workflow` has no
phase for a person's task or for approvers named by position
([`schemas/programme.md`](../schemas/programme.md#how-a-workflow-maps-onto-patternsworkflow)).
No capability in [`protocol/types`](../protocol/types.md#capability) names
deciding one, and no route at execution serves one, so the admin gateway's
inbox ([`architecture/admin`](admin.md#decision-inbox)) would list content's
open proposals and no step of execution's, and it lists neither until a
`PassRoute` can name the inbox group a route answers.

**Notification has no route, capability or blueprint.** The notify-by-position
call above has no declared action name or capability yet. Nothing is
specified for how a person sets their own preferences. Who holds a position
is the tenant's personal data, so content keeps it in the scope's records
repository ([`architecture/content`](content.md#where-an-entry-labelled-pii-is-kept)),
as a restricted register of who holds each
[position](../schemas/position.md). No schema declares that register yet,
so notification has nothing it can read a holder from.

**Two acts the capabilities name have no route.** [`protocol/types`](../protocol/types.md#capability)
gives `programme:operate` "reschedule" and `programme:switch` "who hears
them". No route here reschedules an installed item: its `schedule` is the
map's, and changes when the adopted map does. No route changes who hears an
item: a notice's `to` positions are the map's, and who holds them is the
register above. Until a route is specified, neither act is admitted
anywhere.

**The prompt worker has no model to call.** The tenant's model is served at
`POST /v1/admin/complete`, which is a person's route
([`architecture/orchestrator`](orchestrator.md#the-tenants-model)). A
registered component can reach a provider itself today, by declaring
`model:route` ([`protocol/types`](../protocol/types.md#capability)) and
reading `GET /v1/model/ceiling`
([`architecture/orchestrator`](orchestrator.md#a-model-is-a-destination)),
through enforcement's external boundary. The prompt worker does not: that
makes every component that runs agent work its own model route, and the
tenant service architecture puts the model in one model service instead.
That service is not specified, so no route lets a service ask the tenant's
model for unattended work. So an `agent:` operation or
step installs, and cannot run, until the model service is specified. It is
reported as not runnable, never as having run.

**Due answers are not specified here.** What is due, occurrences, counted
conditions and readiness are the programme service's. Their routes are not
in this document.

**The events `on:` names have no publisher here.** The facts an operation, a
workflow or a notice reacts to are named in
[`schemas/programme.md`](../schemas/programme.md#on--reacting-to-a-fact-instead-of-to-the-clock).
Which service publishes each one, and on what topic, is not specified.

---

## Types

```yaml
types:
  InstalledItem:
    description: One operation, workflow or notice the programme service holds at a scope
    fields:
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
        enum: [paused, running]
        required: false
        description: Absent on a notice, which has no clock of its own
      muted:
        type: bool
        required: true
        description: True from installation until a person unmutes it
      switched_by:
        type: string
        required: false
        description: The identity id of the person who last unmuted or muted it, from their pass
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
```

---

## Security

```yaml
security:
  trust_model:
    description: |
      The service trusts a person's authority only on a pass, and its own
      authority only for work that reaches nobody until a person unmutes it.
      It never holds a person's token, and never runs work under the
      authority of the person who switched it on.

  boundaries:
    - boundary: Person → Programme Service. Only through the admin gateway,
        on a pass addressed here. An operator token is refused
    - boundary: Programme Service → Content. Reads the adopted map. Writes
        nothing as a person
    - boundary: Execution → Programme Service. get_workflow, and the
        actions an operation or a phase names in does, from execution alone
    - boundary: Programme Service → Notification. Positions and a message.
        Never a person or a channel

  enforcement:
    - rule: Nothing reaches a person until a person unmutes it
      mechanism: Every item is installed muted. Unmute needs programme:switch,
        which is person only
    - rule: Work that reaches people is started and stopped by a person
      mechanism: Pause, resume and run on an unmuted item are admitted on a
        pass only
    - rule: An installation is never reported whole when it is not
      mechanism: Every block not handed to its owner is listed by name in
        the answer
    - rule: No machine decides
      mechanism: No action or worker capability approves, rejects, closes,
        attests or signs
```

---

## Implementation Notes

- Read the map from the tenant's adopted copy in content. A template edited
  by its organisation is the one that runs
  ([`schemas/programme.md`](../schemas/programme.md#the-tenants-copy-is-the-tenants)).
- Matching on programme, `id` and scope is what keeps a second installation
  from creating a second clock.
- A muted item's runs still produce output. Execution keeps it in its run
  ledger, so that a person can compare it with what they expected before
  they unmute. This service keeps no copy.
- Report a `does:` name this build does not run by name, with the names it
  does run. Never skip it.

---

## Verification Checklist

- [ ] Every route in [Endpoints](#endpoints) but `GET /livez` and `GET /readyz` is declared among the manifest's `pass_routes`, with the one capability its row gives
- [ ] An operator token on any route is refused with `PASS_REQUIRED`
- [ ] `POST /v1/programme/installations` on a registration or channel token is refused with `FORBIDDEN`, and installs nothing
- [ ] Every item an installation creates is muted, and is paused unless its `start` is `running`
- [ ] Installing the same programme twice at one scope creates no second item
- [ ] An installation asked for at a project is refused with `INVALID_REQUEST`, naming the organisation
- [ ] An installation lists every block it could not hand to an owner, with the owner named, and does not call itself complete
- [ ] A route other than `/livez`, `/readyz` and installing, missing `organisation`, or a route with `{id}` in its path missing `programme`, is refused with `INVALID_REQUEST`
- [ ] With one programme installed at two organisations, `DELETE /v1/programme/installations/{programme}` withdraws only the organisation it names
- [ ] The mute and unmute routes of operations, workflows and notices each need `programme:switch`, and the service never declares `programme:switch` on its own manifest
- [ ] Pausing, resuming or running an unmuted item on a component's registration token is refused with `FORBIDDEN`. The same act on a muted item is admitted with `programme:operate`
- [ ] A notice is sent once when its fact first becomes true, and not again while the fact stays true
- [ ] A muted notice that advances reaches nobody, and its advance is recorded as not sent; once unmuted, its next advance is sent
- [ ] Pausing a workflow starts no new run and lets a started run finish; `get_workflow` for a withdrawn workflow answers `NOT_FOUND`
- [ ] `DELETE /v1/programme/installations/{programme}` stops every item under it and deletes no document
- [ ] An `agent:` item is reported as not runnable while no model route is open to a service, and is never reported as having run
