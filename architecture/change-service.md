<!-- blueprint
type: architecture
name: change-service
version: 1.0.1
requires: [protocol/types, protocol/identity, protocol/spec, patterns/principal-identity, architecture/admin, architecture/engine, architecture/model-service, architecture/storage, schemas/change, schemas/run-statement]
platform: any
tier: free
adoption: opt-in
-->
<!-- wl:ids complete -->

# Weblisk Change Service

The tenant service that hosts the engine. Every change to what a tenant is
built from is planned, decided, applied, verified and stopped here, inside the
tenant, on the tenant's own model, and recorded in the tenant's own repository.
A client reaches it only through the admin gateway.

## Overview

[`architecture/engine`](engine.md#three-hosts) runs in three hosts: the CLI,
Studio, and the tenant. **This is the third.** It is a component of the tenant,
generated from this blueprint like every other, whose work is to import the
engine module and run the engine's operations against the tenant it belongs to.
It is how a client builds without ever holding the tenant's tree: Studio, and
the CLI on a person's own machine, call the routes below (`tenant-api`), and
the act happens here. No client runs a `cli-in-tenant` operation on a tenant
(`cli-in-tenant-through-tenant`).

It is the provider [`architecture/admin`](admin.md#changes-and-builds) has
named since the changes and builds group was written, the owner of
`.weblisk/changes/` ([`schemas/change`](../schemas/change.md#where-it-lives)),
of `.weblisk/build.lock` ([`schemas/build-lock`](../schemas/build-lock.md)),
and the writer of every run statement
([`schemas/run-statement`](../schemas/run-statement.md#where-it-lives)) and
transcript ([`architecture/engine`](engine.md#the-record)) the tenant keeps.

**It decides nothing the engine does not, and nothing a person must.** What a
plan holds, what a build step may do, which instruction a model is given and
what settles a criterion are [`architecture/engine`](engine.md) and
[`architecture/generation`](generation.md)'s, read from the corpus at the
change's pins. Whether a change may be applied is a person's signed decision
([Approval](#approval)). What this blueprint adds is where those acts happen,
on whose authority, in what order a rebuilt tenant is restarted, and what
every client may read while they happen.

**Why a blueprint of its own, and why this name.** A component kind is built
from one blueprint, its own ([`architecture/engine`](engine.md#what-a-component-owes)),
so a section of [`architecture/engine`](engine.md) would make the engine's
library criteria a component's own, and a section of
[`architecture/admin`](admin.md) would make the admin gateway owe them. The
corpus already names a service after the record it keeps:
[`schemas/programme`](../schemas/programme.md) is the record and
[`architecture/programme-service`](programme-service.md) the service, and
[`architecture/model-service`](model-service.md) the same. So this is
`architecture/change-service`, beside [`schemas/change`](../schemas/change.md),
and not `architecture/change.md`, which would sit beside
[`architecture/change-management`](change-management.md) as a third file
named for one word.

> **Scope boundary.** This document is the change service's routes, who may
> call each, where it writes, how it restarts what it rebuilt and itself, and
> what it announces. The change record is [`schemas/change`](../schemas/change.md)'s,
> the run statement [`schemas/run-statement`](../schemas/run-statement.md)'s,
> the lock [`schemas/build-lock`](../schemas/build-lock.md)'s; the build
> steps, the suite and the event envelope are
> [`architecture/engine`](engine.md)'s; who may approve is
> [`architecture/cli`](cli.md#who-may-approve-a-change)'s D25. None of them is
> restated here.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    # 6.7.0 is where the change capabilities are listed
    version: ">=6.7.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category, retryable, retry_after, detail]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, via, action, target, status]
        # pass_routes is the gateway's allow-list for this service: which of
        # its routes a person's request may reach, and what each needs
        - name: AgentManifest
          fields_used: [name, type, capabilities, publishes, subscriptions, pass_routes]
        - name: PassRoute
          fields_used: [method, path, capabilities, body, inbox]
        - name: BodyRequirement
          fields_used: [field, equals, capabilities]
        - name: InboxRoute
          fields_used: [query, items, withheld, decide_method, decide_path]
        - name: Capability
          fields_used: [name, resources]
        # A change awaiting a decision, as the decision inbox lists it
        - name: ApprovalRequest
          fields_used: [id, owner, change_id, requester, operation, environment, authority_required, position, development, justification, urgency, requested_at, expires_at, correlation_id]
        - name: ResourceEvent
          fields_used: ["*"]
        - name: ResourceEventPage
          fields_used: [events, position, gap]
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: LeaseRenewal
          fields_used: [ready, checks, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    # 3.5.0 is where weblisk/change-decision/v1 is registered
    version: ">=3.5.0 <4.0.0"
    bindings:
      types:
        # type and aud say a person's request reached this service on a pass
        # addressed to it; cap is what it may use; identity_id and
        # identity_key name who acted and with which identity key; act names
        # the gateway that carried it; record_keys are the keys the hub vouches
        # may sign a record; step_up_at admits a destructive act
        - name: WLToken
          fields_used: [type, aud, act, cap, identity_id, identity_key, cid, record_keys, step_up_at, sub]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/spec
    version: ">=4.0.0 <5.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
        - path: /v1/lease
          methods: [POST]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/principal-identity
    version: ">=2.0.0 <3.0.0"
    bindings:
      types:
        # The attestation a decision's signing key is vouched for by
        - name: Attestation
          fields_used: [identity_id, identity_public_key, credential_public_key, purpose, not_after]
      behaviors:
        - name: record-signing
          usage: A person's decision on a change is signed by their own sign-records credential, never by a key this service or a console holds
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/admin
    # 5.7.0 is where the changes and builds group names this blueprint
    version: ">=5.7.0 <6.0.0"
    bindings:
      behaviors:
        - name: admin-gateway-authorization
          usage: Relied on, never called. A person's request reaches this service only on a route its manifest declares among pass_routes, on a pass naming every capability that route declares
        - name: destructive-action-step-up
          usage: Applying a change and stopping a component through this service are destructive acts, named here
        - name: resource-api
          usage: The change and build-run kinds, served at the uniform address
        - name: resource-feed
          usage: Every change to a change or a build run, the engine's events among them, announced on GET /v1/admin/ws
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/model-service
    version: ">=1.1.0 <2.0.0"
    bindings:
      endpoints:
        # The tenant's model, asked on this service's own registration token
        - path: /v1/model/complete
          methods: [POST]
      types:
        - name: ServiceCompletionRequest
          fields_used: [request, run, phase]
        - name: ServiceCompletionResponse
          fields_used: [completion, response, usage]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/storage
    version: ">=2.1.0 <3.0.0"
    bindings:
      types:
        - name: RecordSnapshot
          fields_used: [snapshot, service, taken_at, store_format, files]
      behaviors:
        - name: backup-restore
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/engine
    version: ">=1.3.0 <2.0.0"
    bindings:
      types:
        # The envelope every engine event carries, which this service
        # announces on GET /v1/admin/ws as it runs an operation (Events)
        - name: Events
          fields_used: [operation, invocation, seq, at, type, body]
        # What an operation asks a person, relayed to the client that asked
        # for it and answered back to the invocation (Questions)
        - name: Questions
          fields_used: [kind, about, choices]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: schemas/change
    bindings:
      types:
        # What a plan says will be done to each node it reaches, and why
        # (Verdicts), as the change this service writes records it
        - name: Verdicts
          fields_used: [verdict, because]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: schemas/run-statement
    bindings:
      types:
        # The statement this service writes once for each run, in its DSSE
        # envelope, and serves at GET /v1/admin/build/statements/{statement}
        - name: RunStatement
          fields_used: [_type, predicateType, subject, predicate]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

The operations, the build steps and the record are read through the engine
the service imports. The build lock it writes has the shape
[`schemas/build-lock`](../schemas/build-lock.md) gives, and the configuration
it reads the shape [`schemas/config`](../schemas/config.md) gives; neither
declares a type a contract could bind, so neither is required here.

---

## Architecture

```
  person ──► client (CLI, Studio) ──► admin gateway ──pass──►┌───────────────────────────────┐
                    ▲                                         │  Change service               │
                    │  GET /v1/admin/ws  (feed)               │                               │
                    └─────────────────────────────────────────┤  Route layer                  │
                                                              │   pass · capability · step-up │
                                                              │  Decision Verifier            │
                                                              │  Run Journal (own store)      │
                                                              │  Engine host ───────────────┐ │
                                                              │   one writer at a time      │ │
                                                              │  Cut-over Supervisor        │ │
                                                              └──────────────┬──────────────┼─┘
            POST /v1/model/complete (own registration token) ◄───────────────┘              │
                                                                                            ▼
                         the tenant's repository: tree · .weblisk/changes · build.lock · provenance/
```

**Route layer** admits a person's request on a pass addressed to this service
and nothing else, checks the route's capability and, for a destructive act,
the step-up, and audits every write.

**Decision Verifier** rebuilds the `weblisk/change-decision/v1` statement from
the change it is recording a decision on and verifies the person's signature
over it ([Approval](#approval)).

**Run Journal** is this service's own record store: every build run it started,
the engine events each emitted in order, each open question, and each
cut-over under way. It is what lets a client follow a run, and what the service
reads when it starts again ([Supervision](#supervision)).

**Engine host** runs one engine invocation per build run, through the engine's
operations API, with the inputs the route was given. It owns the tenant's tree
while an invocation writes it.

**Cut-over Supervisor** restarts the components a change rebuilt, through the
engine's own component start and stop, one at a time, and restarts itself last.

---

## Responsibilities

### Owns

- Hosting the engine in the tenant, and running each operation of
  [The operation catalogue](#the-operation-catalogue) whose host it is
- The changes and builds group of the admin API: `/v1/admin/changes…` and
  `/v1/admin/build…` ([`architecture/admin`](admin.md#changes-and-builds))
- Recording a person's signed decision on a change, and refusing one that does
  not verify
- Writing the change, the build lock, every run statement and every transcript
  into the tenant's repository
- Restarting what a change rebuilt, and itself, and putting the previous build
  back where a restart fails
- Announcing every change to a change or a build run on the admin feed
- Listing the changes awaiting a decision for the decision inbox

### Does NOT Own

- **The engine.** The build steps, the suite, the event envelope and what a
  model may do are [`architecture/engine`](engine.md)'s, imported, never
  copied
- **The tenant's model.** It is chosen at `PUT /v1/admin/model` and run by the
  model gateway ([`architecture/model-service`](model-service.md)); this
  service asks it and keeps no backend, model name or provider of its own
- **Who holds a position.** That is the tenant's register in content
  ([`schemas/position`](../schemas/position.md))
- **A person's authority after their request.** Work this service does once
  a request is answered is its own, as [Who May Do What](#who-may-do-what)
  says, and carries no person's authority anywhere
- **Building a tenant that has none.** `tenant new` and `tenant rebuild` run
  on the host that will hold the tenant, before any change service exists
  there ([The operation catalogue](#the-operation-catalogue))

---

## Endpoints

Every route but the seven agent endpoints is reached on a pass, through the
admin gateway, and is declared among the manifest's `pass_routes` with the
capability its row gives. `Step-up` marks an act that is destructive under
[`architecture/admin`](admin.md#contracts)'s `destructive-action-step-up`.

| Method | Path | Operation | Auth | Capability | Step-up | Purpose |
|--------|------|-----------|------|------------|---------|---------|
| GET | /v1/admin/changes | ListChanges | yes | `change:read` | | `change list`. The tenant's changes, newest first, filtered by `state` and `kind`, cursor-paginated, as a `ChangePage`. With `awaiting=me`, also the open `ApprovalRequest`s the person on the pass may decide. The decision inbox's list route |
| POST | /v1/admin/changes | PlanChange | yes | `change:plan` | | `change plan`, and `change revert` with `kind` `revert`: a `ChangePlanRequest`. Starts a build run of the operation and answers `202` with a `BuildRunStarted`; the change is written when the plan completes |
| GET | /v1/admin/changes/{id} | GetChange | yes | `change:read` | | `change show`. One change, as [`schemas/change`](../schemas/change.md#shape) shapes it, with its `ETag` |
| POST | /v1/admin/changes/{id}/decision | DecideChange | yes | `change:decide` | | `change approve` and `change reject`: a `ChangeDecision`, signed by the person over the plan ([Approval](#approval)) |
| POST | /v1/admin/changes/{id}/apply | ApplyChange | yes | `change:apply` | yes | `change apply`: a `ChangeApplyRequest`. Starts a build run that builds, verifies and cuts over what the plan names, and answers `202` with a `BuildRunStarted` |
| POST | /v1/admin/changes/{id}/verify | VerifyChange | yes | `change:operate` | | `change verify`. Starts a build run that runs the suite against an applied change's tree and records `verify` on the change. Answers `202` with a `BuildRunStarted` |
| GET | /v1/admin/build | GetBuild | yes | `change:read` | | The tenant's build lock and its digest, and every run statement the tenant holds, each with its id, digest, component, result and the build run that wrote it, as a `BuildState` |
| GET | /v1/admin/build/runs | ListBuildRuns | yes | `change:read` | | Build runs, newest first, filtered by `operation`, `state` and `change`, cursor-paginated, as a `BuildRunPage` |
| POST | /v1/admin/build/runs | StartBuildRun | yes | `change:operate` | for `component stop` | `test run`, `tenant verify`, `component start`, `component stop` and `component logs`: a `BuildRunRequest`. Answers `202` with a `BuildRunStarted` |
| GET | /v1/admin/build/runs/{run} | GetBuildRun | yes | `change:read` | | `run status`. One `BuildRun`: its operation, state, the change it is for, the statements it wrote, its open question and its last event |
| GET | /v1/admin/build/runs/{run}/events | ListBuildRunEvents | yes | `change:read` | | The run's engine events after `after` (a `seq`), in order, waiting up to `wait` seconds (at most 25) where there are none yet, as a `BuildRunEvents` |
| POST | /v1/admin/build/runs/{run}/stop | StopBuildRun | yes | `change:operate` | | `change stop`. Ends a running build run `stopped` at the next boundary the engine can stop at |
| POST | /v1/admin/build/runs/{run}/answer | AnswerBuildRun | yes | `change:operate` | | Answer the run's open `question`: a `BuildRunAnswer`. Only the person who started the run |
| GET | /v1/admin/build/statements/{statement} | GetRunStatement | yes | `change:read` | | One run statement, as the tenant stores it: its DSSE envelope ([`schemas/run-statement`](../schemas/run-statement.md#signing)) |
| GET | /v1/admin/build/statements/{statement}/transcripts/{action} | GetTranscript | yes | `change:read` | | One model action's transcript, as the tenant stores it ([`architecture/engine`](engine.md#the-record)) |
| GET | /v1/admin/events/change | ChangeEvents | yes | `change:read` | | The feed route of the `change` kind: its events after a position, as a `ResourceEventPage` ([`architecture/admin`](admin.md#the-feed)) |
| GET | /v1/admin/events/build-run | BuildRunEvents | yes | `change:read` | | The feed route of the `build-run` kind, the engine's events among them, as a `ResourceEventPage` |
| GET | /v1/admin/records/change-service/snapshot | RecordSnapshot | yes | `admin:*` | | Every store this service owns, the run journal, at one instant between writes, as a ustar archive led by a `RecordSnapshot` ([`architecture/storage`](storage.md#the-snapshot-route)). No route restores it |
| POST | /v1/describe | Describe | yes | | | This service's manifest ([`protocol/spec`](../protocol/spec.md#post-v1describe)) |
| POST | /v1/services | Services | yes | | | The signed service directory the orchestrator pushes ([`protocol/spec`](../protocol/spec.md#post-v1services)) |
| POST | /v1/execute | Execute | yes | | | Answered `FORBIDDEN`, doing nothing: this service takes no task |
| POST | /v1/message | Message | yes | | | Answered `FORBIDDEN`, doing nothing: this service takes no message |
| POST | /v1/event | Event | yes | | | Answered `FORBIDDEN`, doing nothing: this service subscribes to nothing |
| GET | /livez | Livez | no | | | Liveness, for the supervisor that restarts the service |
| GET | /readyz | Readyz | no | | | Readiness, for the supervisor waiting on its start |

The change service MUST serve every route of the table above, at the method and path its row gives, and no other route. <!-- wl:id serves-the-endpoints -->

### The gateway's allow-list for this service

The admin gateway carries a person's request to a provider only on a route
that provider's manifest declares among its `pass_routes`
([`architecture/admin`](admin.md#contracts), `admin-gateway-authorization`).
These are this service's, and the whole of them:

```yaml
pass_routes:
  - {method: GET, path: /v1/admin/changes, capabilities: [change:read],
     inbox: {query: awaiting=me, items: approvals, withheld: withheld,
             decide_method: POST, decide_path: "/v1/admin/changes/{id}/decision"}}
  - {method: POST, path: /v1/admin/changes, capabilities: [change:plan]}
  - {method: GET, path: "/v1/admin/changes/{id}", capabilities: [change:read]}
  - {method: POST, path: "/v1/admin/changes/{id}/decision", capabilities: [change:decide]}
  - {method: POST, path: "/v1/admin/changes/{id}/apply", capabilities: [change:apply]}
  - {method: POST, path: "/v1/admin/changes/{id}/verify", capabilities: [change:operate]}
  - {method: GET, path: /v1/admin/build, capabilities: [change:read]}
  - {method: GET, path: /v1/admin/build/runs, capabilities: [change:read]}
  - {method: POST, path: /v1/admin/build/runs, capabilities: [change:operate]}
  - {method: GET, path: "/v1/admin/build/runs/{run}", capabilities: [change:read]}
  - {method: GET, path: "/v1/admin/build/runs/{run}/events", capabilities: [change:read]}
  - {method: POST, path: "/v1/admin/build/runs/{run}/stop", capabilities: [change:operate]}
  - {method: POST, path: "/v1/admin/build/runs/{run}/answer", capabilities: [change:operate]}
  - {method: GET, path: "/v1/admin/build/statements/{statement}", capabilities: [change:read]}
  - {method: GET, path: "/v1/admin/build/statements/{statement}/transcripts/{action}", capabilities: [change:read]}
  - {method: GET, path: /v1/admin/events/change, capabilities: [change:read]}
  - {method: GET, path: /v1/admin/events/build-run, capabilities: [change:read]}
  - {method: GET, path: /v1/admin/records/change-service/snapshot, capabilities: ["admin:*"]}
```

The manifest's `pass_routes` MUST be exactly the block above: every route of [Endpoints](#endpoints) but the seven agent endpoints, each with the capability its row gives, and `GET /v1/admin/changes` alone carrying the `inbox`. <!-- wl:id pass-routes-are-the-endpoints -->

**`/v1/admin/changes` matches no route twice.** `{id}` matches one path
segment, so `GET /v1/admin/changes` and `GET /v1/admin/changes/{id}` are two
routes, and `/v1/admin/build/runs` is never a `{statement}`
([`protocol/types`](../protocol/types.md#passroute): no two of one manifest's
pass routes may match one request).

**The snapshot route is guarded by `admin:*`, which the service never holds**,
for the reason execution's is
([`architecture/execution`](execution.md#endpoints)): it hands over every
record this service keeps.

### The manifest

The service registers under the name `change-service`, with `type`
`infrastructure`, no `subscriptions` and no `publishes`, and declares on its
manifest `change:read`, `change:plan`, `change:apply`, `change:operate` and
`llm:chat`. It checks `change:decide` on a pass and never holds it, as
[`protocol/types`](../protocol/types.md#capability) requires of a person-only
capability. `llm:chat` is what its own registration token asks the tenant's
model with ([Whose model](#whose-model)); no pass route names it, so no
person's request carries it here.

The change service MUST register under the name `change-service`, with type `infrastructure`, and declare exactly `change:read`, `change:plan`, `change:apply`, `change:operate` and `llm:chat` among its capabilities, never `change:decide` or `admin:*`. <!-- wl:id registers-as-change-service -->

---

## Interfaces

**What clients call** is [Endpoints](#endpoints), and nothing else: the CLI on
a person's machine and Studio reach every change operation of a tenant there,
as [`architecture/engine`](engine.md#three-hosts) requires of `tenant-api`.

**What it asks of the model service**: `POST /v1/model/complete`, on its own
registration token ([Whose model](#whose-model)).

**What it asks of the host it runs on**: to run the engine's toolchain
commands, to start and stop the tenant's component processes through the
engine's component operations, and to read and write the tenant's directory.
It is the one tenant component that does, because it is the one that builds.

**Events it publishes** on the bus: none. What it announces, it announces on
the admin feed, as its kinds' Resources entries name
([Resources](#resources)), so a client subscribed to `GET /v1/admin/ws`
follows a change or a build run without polling.

**Events it subscribes to**: none.

---

## Error Handling

The codes registered in [`protocol/types`](../protocol/types.md#error-handling),
and the change service's own, below, registered here alone, as
[`architecture/content`](content.md#error-handling) registers its own.

| Code | HTTP | Category | When |
|---|---|---|---|
| `PASS_REQUIRED` | 401 | auth | An operator token, on any route but the agent endpoints and the probes ([`protocol/identity`](../protocol/identity.md#the-pass), rule 4) |
| `PASS_AUDIENCE_MISMATCH` | 401 | auth | A pass addressed to another component |
| `FORBIDDEN` | 403 | auth | A token that is neither a pass nor an operator token on a pass route; a pass whose `cap` does not name the route's capability; `AnswerBuildRun` by anybody but the person who started the run; and every request to `POST /v1/execute`, `POST /v1/message` and `POST /v1/event` |
| `STEP_UP_REQUIRED` | 401 | auth | `ApplyChange`, or `StartBuildRun` for `component stop`, on a pass whose `step_up_at` is absent or more than 300 seconds old ([`architecture/admin`](admin.md#contracts), `destructive-action-step-up`). Nothing starts |
| `INVALID_REQUEST` | 400 | validation | A body that is not the route's type; a `ChangePlanRequest` whose `request` is empty or holds a path; `kind` `revert` without `reverts`, or `reverts` with another `kind`; a `BuildRunRequest` naming an operation [StartBuildRun](#starting-a-build-run-that-is-not-a-change) does not serve; a query parameter the route does not take |
| `NOT_FOUND` | 404 | validation | No change, build run, statement or transcript of that id |
| `INVALID_STATE` | 409 | conflict | A decision on a change that is not `planned`, or whose approval request has expired; verify of a change that is not `applied`; stop of a build run that has ended; an answer where the run has no open question, or naming another `seq` than the open one |
| `APPROVAL_SELF_DENIED` | 403 | policy | An approval by the person who requested the change, on a tenant that is not a development tenant ([`patterns/approval`](../patterns/approval.md#error-handling); [Approval](#approval)) |
| `CHANGE_DECISION_INVALID` | 400 | auth | A `ChangeDecision` whose statement does not verify, naming the condition of [Verifying a decision](#verifying-a-decision) that failed. Nothing is recorded. 400, not 401: the pass was accepted and the statement it carried was not |
| `CHANGE_POSITION_UNRESOLVED` | 503 | transient | A decision on a change that names an `approver_position`, while this service cannot read who holds that position. Nothing is recorded |
| `CHANGE_STALE` | 409 | conflict | A decision on, or an apply of, a change whose `base` no longer matches the tenant: another corpus revision at a pin, another lock digest, another fabric tip ([`schemas/change`](../schemas/change.md#reading-one)). Nothing starts. The client plans again |
| `CHANGE_CONFLICT_REFUSES` | 409 | policy | An approval of, or an apply of, a change whose `conflicts.found` refuses it ([`schemas/change`](../schemas/change.md#rules), `approval-conflicts`), with `without_approval` as without it |
| `CHANGE_NOT_APPROVED` | 409 | policy | An apply of a `planned` change with no approval and no `without_approval` |
| `CHANGE_WITHOUT_APPROVAL_REFUSED` | 403 | policy | An apply asking `without_approval` on a tenant whose configuration does not say `hub.environment: development` ([`schemas/config`](../schemas/config.md#the-environment-and-the-development-tenant)) |
| `CHANGE_BUSY` | 409 | transient | An apply, a verify, or a `component start` or `stop`, while another build run writes the tenant's tree or starts or stops its components. `detail.run` names that run. Nothing starts |
| `ADMIN_GROUP_UNAVAILABLE` | 503 | transient | Answered by the admin gateway for every route here while no change service is registered ([`architecture/admin`](admin.md#changes-and-builds)); never by this service |

A refusal changes nothing and is audited ([Audit](#audit)). **A failure inside
a build run is not an error on any route.** Once a run has started, what ends
it badly — a model refusal, a stale pin found mid-run, a component that would
not start — is the run's `finished` event, its state, and its record: the run
ends `failed` naming the code, and the change records the outcome. A run is
never reported as having done a step it did not do.

The model service's refusals (`MODEL_NOT_CONFIGURED`,
`MODEL_BACKEND_UNAVAILABLE`, `MODEL_NONE_LOADED`, `MODEL_BACKEND_LIMITED`,
`MODEL_BACKEND_FAILED`, `MODEL_UNRECORDED`, `SCOPE_MISSING`,
`SCOPE_CEILING_EXCEEDED`) reach a client in that event's body, as the model
service answered them ([`architecture/model-service`](model-service.md#error-handling)).

---

## Data Flow

### Planning a change

1. A person's client sends `POST /v1/admin/changes` with a
   `ChangePlanRequest`, on a pass carrying `change:plan`.
2. The service checks the body, records a build run of operation
   `change plan` with `requested_by` the pass's `identity_id`, and answers
   `202` with its id.
3. The engine host runs `change plan` through the engine, at the tenant's
   current sources, as [`architecture/generation`](generation.md#resolving-a-request-of-many-roots)
   resolves a request. It makes no model call, and writes nothing but
   `.weblisk/changes/<change id>.json`, in state `planned`.
4. The service opens the change's `ApprovalRequest` ([Approval](#approval))
   and announces the change `created` on the feed.
5. The run's `finished` event carries the change's id. A plan with no entries
   ends the run `failed`: an empty plan is a plan that could not be computed
   ([`schemas/change`](../schemas/change.md#rules), `plan-not-empty`).

Planning MUST make no model call and write nothing in the tenant's repository but the change file it plans. <!-- wl:id plan-writes-only-the-change -->

### Deciding a change

1. A person's own client builds the `weblisk/change-decision/v1` statement
   from the change it showed its person, has the person's sign-records
   credential sign it, and sends `POST /v1/admin/changes/{id}/decision` with
   a `ChangeDecision`, on a pass carrying `change:decide`.
2. The service reads the change, refuses one that is not `planned`, is stale,
   or, for an approval, has a refusing conflict.
3. It verifies the statement ([Verifying a decision](#verifying-a-decision)),
   and judges the decider ([Approval](#approval)).
4. It records `approval` or `rejection` on the change and moves it to
   `approved` or `rejected`, closes the `ApprovalRequest`, audits the
   decision, and announces it on the feed. It answers `200` with the change.

### Applying a change

1. A person's client sends `POST /v1/admin/changes/{id}/apply` with a
   `ChangeApplyRequest`, on a pass carrying `change:apply` and a `step_up_at`
   no more than 300 seconds old.
2. The service refuses a change that is stale, has a refusing conflict, or is
   `planned` with no approval and no `without_approval` admitted
   ([Approval](#approval)); and refuses with `CHANGE_BUSY` while another run
   writes the tree.
3. It records a build run of operation `change apply` and the destructive
   act's audit entry, takes the tree, and answers `202` with the run's id.
   The request is answered here; everything after it is the service's own
   work ([Who May Do What](#who-may-do-what)).
4. The engine host runs `change apply`: the eight build steps
   ([`architecture/engine`](engine.md#the-build-steps)), at the change's
   pins, never at a source's head, asking the tenant's model
   ([Whose model](#whose-model)), writing as [Where it writes](#where-it-writes)
   says, and journalling every event it emits.
5. The cut-over supervisor restarts what was built and accepted
   ([Supervision](#supervision)).
6. The change records its outcomes and `applied_run`, and moves to `applied`,
   or `failed`; the run ends with a `finished` event, the tree is released,
   and the feed announces both.

### Following a build run

A client follows a run one of two ways, and both carry the same objects:

- **The feed.** It subscribes on `GET /v1/admin/ws` to kind `build-run` and the
  run's uid, `after` the last position it saw. Each engine event the run
  emits is announced as the item's `updated` event, its data the run's `seq`
  and `last_event`, the event itself; each change of state as that state's
  event ([Resources](#resources)). After a reconnect, including the one the
  admin gateway's own restart forces, it subscribes again from where it was.
- **The events route.** `GET /v1/admin/build/runs/{run}/events?after=<seq>`
  answers every event after that `seq`, in order, and waits up to `wait`
  seconds where there is none yet. It is how a finished run is read back,
  and how a client with no WebSocket follows one.

Each event MUST be journalled before it is announced or answered, in the form the engine emitted it, so that every reader of a run, by the feed or the events route, before or after a restart of this service, reads the same objects in the same `seq` order. <!-- wl:id events-journalled-before-announced -->

### Stopping a build run

`POST /v1/admin/build/runs/{run}/stop` ends a running run at the next
boundary the engine can stop at: a model call under way is closed, which the
model service records as `cancelled`
([`architecture/model-service`](model-service.md#a-caller-closes-the-request));
a file being written is finished or not written; a component start under way
is finished, so no process is left half started. The run ends `stopped`, its
run statement says `stopped`
([`schemas/run-statement`](../schemas/run-statement.md#a-run-that-did-not-complete)),
and the change keeps the state it had: an approved change stays approved, and
applying it again resumes it, reusing every action already done
([`architecture/engine`](engine.md#how-the-record-makes-builds-incremental)).

**Stopping is not destructive.** It ends spending and writes nothing a later
apply cannot resume, so it asks for no step-up, as revoking a credential asks
for none ([`architecture/admin`](admin.md#contracts),
`credential-revocation-not-destructive`): a run that is spending the tenant's
model must be stoppable by whoever can see it running, at once.

Stopping a build run MUST be served without a step-up, and MUST leave the change in the state it had before the run, with the run ended `stopped`. <!-- wl:id stop-without-step-up -->

### Starting a build run that is not a change

`POST /v1/admin/build/runs` runs one of these engine operations, named by the
`BuildRunRequest`'s `operation`, and no other:

| `operation` | What the engine host does | Step-up |
|---|---|---|
| `test run` | Runs the suite against the tenant's tree, sealed; with `live` true, only the checks that declare `live: safe`, against the running tenant ([`architecture/engine`](engine.md#build-time-and-run-time)) | |
| `tenant verify` | Runs every `live: safe` check against the running tenant, and records the runtime verdicts | |
| `component start` | Starts one declared component, as [`architecture/cli`](cli.md#weblisk-component-name-start--stop--status--logs) says a start is made | |
| `component stop` | Stops one running component | yes |
| `component logs` | Streams what one component has written, as `item` events | |

Stopping a running component cuts every request it is serving, so it is
destructive. Starting one starts only what the tenant's configuration
declares, and is not.

`StartBuildRun` MUST refuse with `INVALID_REQUEST` any `operation` but the five above, and MUST refuse `component stop` without a recent step-up as a destructive act. <!-- wl:id build-run-operations-closed -->

---

## Who May Do What

1. **A person, only on a pass.** Every route but the agent endpoints and the
   probes admits a pass addressed to this service and nothing else, and
   records who acted by the pass's `identity_id` with the gateway's
   `act.identity_id` beside it ([`architecture/admin`](admin.md#contracts),
   `provider-accepts-pass`).
2. **One capability per route**, the one its row gives. `change:decide` is
   person only ([`protocol/types`](../protocol/types.md#capability)): no
   service, no agent and no work pass decides a change.
3. **A destructive act needs its person's own step-up**: `ApplyChange`, and
   `StartBuildRun` for `component stop`. Each is destructive by
   `destructive-action-step-up`, which governs it and is not restated here.
   Applying a change rewrites the tenant's code and runs its model; stopping
   a component cuts every request it serves.
4. **Only the person who started a run answers its question.** A question is
   asked of whoever is driving the operation, as
   [`architecture/engine`](engine.md#questions) says; another person who can
   read the run sees it and cannot answer it.
5. **The service's own work carries nobody's authority.** Once `ApplyChange`,
   `PlanChange`, `VerifyChange` or `StartBuildRun` is answered, the run is the
   service's own work, under its own registration. It presents no pass and no
   person's token anywhere, and acts on nothing outside its own host and its
   own model calls. What it may do is bounded by the change itself: an apply
   builds what the approved plan names, at the pins the plan read, and
   nothing else. The person's decision is a record of who decided, never an
   authority carried. This is the case
   [`architecture/admin`](admin.md#contracts)'s `admin-gateway-authorization`
   names as work a provider performs as its own, and the gap it records
   stands ([Known Gaps](#known-gaps)).

`ApplyChange`, and `StartBuildRun` for `component stop`, MUST each be served as a destructive act under `destructive-action-step-up`, refused `STEP_UP_REQUIRED` without a `step_up_at` no more than 300 seconds old, and starting nothing. <!-- wl:id destructive-acts-here -->

The change service MUST present no pass, operator token or work pass to any component in the work a build run does, and MUST make no request on a person's behalf once the request that started the run is answered. <!-- wl:id run-carries-no-authority -->

`AnswerBuildRun` MUST be admitted only from the person whose `identity_id` started the run. <!-- wl:id only-requester-answers -->

### Which roles carry what

[`architecture/admin`](admin.md#operator-roles)'s roles table gives the
change capabilities to roles. `change:apply` asks the tenant's model, which
spends what the tenant pays for, so it goes where `llm:chat` goes.

---

## Approval

**A change requires a person's signed decision under the rules that already
exist**: D25 ([`architecture/cli`](cli.md#who-may-approve-a-change)), the
change's rules ([`schemas/change`](../schemas/change.md#rules)), and the
decision inbox ([`architecture/admin`](admin.md#decision-inbox)). This
service is where they are enforced; a client only renders them.

- **Signed by the person.** A decision is a `ChangeDecision`: the person's
  sign-records credential's signature over the `weblisk/change-decision/v1`
  statement, with the attestation that vouches for that key. An unsigned
  decision is no decision.
- **By a holder of the named position**, for a knowledge change whose plan
  names `approver_position`. Who holds a position is read from the tenant's
  register; while this service cannot read it, it records no decision on such
  a change and answers `CHANGE_POSITION_UNRESOLVED` ([Known Gaps](#known-gaps)).
- **Never by the requester**, except on a development tenant, where the
  approval records `development: true` and is shown so wherever the change is.
- **Never of a change with a refusing conflict**, and never of a stale one.
- **One inbox.** A change awaiting a decision is an `ApprovalRequest` this
  service holds, with `id` the change's id and `change_id` the same, listed
  by `GET /v1/admin/changes?awaiting=me` under `approvals`, and so in the
  admin gateway's one decision inbox, decided at
  `POST /v1/admin/changes/{id}/decision`. Its `environment` is the tenant's
  `hub.environment`, `development` true on a development tenant, and its
  `expires_at` the change's `requested_at` plus `approval_expiry`
  ([Configuration](#configuration)). A request that expires undecided is
  closed denied, never approved; a decision on its change is then refused
  `INVALID_STATE`, and planning it again is a person's act.

Every change in state `planned` whose request has not expired MUST be held as one open `ApprovalRequest` whose `id` and `change_id` are the change's id, listed under `approvals` by `GET /v1/admin/changes?awaiting=me` to each person who may decide it now. <!-- wl:id change-awaits-in-inbox -->

A decision MUST be recorded only when its statement verifies under every condition of [Verifying a decision](#verifying-a-decision); one that does not is refused with `CHANGE_DECISION_INVALID` and nothing is recorded. <!-- wl:id decision-verified -->

An approval by the change's requester MUST be refused with `APPROVAL_SELF_DENIED` unless the tenant's configuration says `hub.environment: development`, read when the service started, and an approval admitted there MUST record `development: true`. <!-- wl:id self-approval-development-only -->

An approval of a change whose `conflicts.found` refuses it, and a decision on a stale change, MUST be refused, with `CHANGE_CONFLICT_REFUSES` and `CHANGE_STALE`. <!-- wl:id decision-refuses-conflict-and-stale -->

A decision on a change that names an `approver_position` MUST be recorded only when this service has read that the decider holds that position, and refused with `CHANGE_POSITION_UNRESOLVED` while it cannot read who does. <!-- wl:id decision-position-held -->

### Applying without an approval, in development only

A development tenant may apply a change nobody approved, on the operator's
word, by `without_approval: true` in the `ChangeApplyRequest`. The change
records `without_approval: true`, as
[`schemas/change`](../schemas/change.md#rules) shapes it, and is shown so
wherever it is. Outside development there is no such word: an apply of a
change nobody approved is refused, whoever asks.

The flag waives the approval and nothing else. A stale change, one with a
refusing conflict and one that has ended are refused with it as without it,
and the step-up is still required.

An apply of a `planned` change MUST be refused with `CHANGE_NOT_APPROVED` unless its request carries `without_approval: true` on a tenant whose configuration says `hub.environment: development`, and a request carrying it on any other tenant MUST be refused with `CHANGE_WITHOUT_APPROVAL_REFUSED`. <!-- wl:id without-approval-development-only -->

An apply MUST be refused with `CHANGE_STALE` where the change's `base` no longer matches the tenant, and with `CHANGE_CONFLICT_REFUSES` where its conflicts refuse it, `without_approval` or not. <!-- wl:id apply-refuses-stale-and-conflict -->

### Verifying a decision

```
"weblisk/change-decision/v1" 0x00 <change id> 0x00 <decision> 0x00 <plan_digest> 0x00 <position> 0x00 <signed_at>

<change id>    the change's id, 32 lowercase hex characters
<decision>     approve or reject
<plan_digest>  the change's plan digest, written sha256:<64 hex>
<position>     the position decided as, for a change naming approver_position;
               empty otherwise
<signed_at>    when the person signed, as protocol/conventions:instant writes it
```

It is a fixed-form statement
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)),
registered there. The person's own client builds it from the change it showed
its person, and never signs bytes this service hands it. **The service
rebuilds the statement; it never takes one**: from the change it is about to
record a decision on, it rebuilds the bytes and verifies the signature over
those, so a signature never attaches to a plan its signer did not see. The
`plan_digest` is the change's, as [`schemas/change`](../schemas/change.md#shape)
records it on `approval`. The statement is bound to one change by its id,
which is never reused, so it cannot be spent on another.

A `ChangeDecision` verifies when all of these hold, the conditions
[`architecture/content`](content.md#the-change-statement) holds a change
statement to:

1. The pass's `identity_id` is the attestation's `identity_id`, and the
   fingerprint of the attestation's `identity_public_key` is the pass's
   `identity_key`.
2. The attestation's `purpose` is `sign-records`, and its signature verifies
   under `identity_public_key`
   ([`patterns/principal-identity`](../patterns/principal-identity.md),
   `record-signing`).
3. Its `credential_public_key` is an ML-DSA-65 public key, and its
   `not_after` has not passed.
4. The fingerprint of `credential_public_key` is one of the pass's
   `record_keys`, and is not the pass's `cid`.
5. `signed_at` is within 300 seconds of the service's clock.
6. The signature verifies under `credential_public_key` over the rebuilt
   statement, with the decision and position the request names.

The change records the decision as [`schemas/change`](../schemas/change.md#shape)
shapes `approval` and `rejection`: `by` the pass's `identity_id`, `signature`,
`plan_digest`, `at` the statement's `signed_at`, and `attestation`, so an
auditor verifies it from the change alone.

Its test vectors are `change-decision-approve` and
`change-decision-reject-as-position` in
[`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json),
made with circl and verified with OpenSSL and @noble/post-quantum as every
statement's are ([`protocol/identity`](../protocol/identity.md#fixed-form-statements)).
A client that signs a decision and this service that verifies one each test
against them.

---

## Whose model

**The tenant's own.** Every model call a build run makes is
`POST /v1/model/complete` on this service's own registration token, which
names `llm:chat` ([`architecture/model-service`](model-service.md#who-may-ask)),
with `run` the build run's uid and `phase` the engine action's id. The
backend and the model are the tenant's `ModelConfig`, chosen at
`PUT /v1/admin/model` by a person; the service names neither, and the model
the backend reports is what the action records
([`schemas/run-statement`](../schemas/run-statement.md#actions)).

- **No fallback.** A refusal, `MODEL_NOT_CONFIGURED` or any other, ends the
  run `failed` naming it. Nothing runs on another backend, on the host's own
  model, or on a model the CLI that built this tenant used
  ([`architecture/engine`](engine.md#three-hosts), `model-is-the-acts-owner`).
- **Behind the tenant's gate.** `request.scope` is the highest scope of what
  the prompt carries: each input's declared scope, and the configured
  `default_level` of [`patterns/scope`](../patterns/scope.md#configuration)
  for an input that declares none. The model service's destination gate does
  the rest.
- **On the record.** Each call's `Completion` is the model service's record,
  and the action's transcript is this service's
  ([Where it writes](#where-it-writes)); the two join on `run` and `phase`.

Every model call a build run makes MUST be `POST /v1/model/complete` on this service's own registration token, naming the build run as `run`, and a refusal MUST end the run `failed` naming its code, with no call made to any other backend in its place. <!-- wl:id tenant-model-only -->

---

## Where it writes

| What | Where | Written by |
|---|---|---|
| The tenant's code and translated tests | the tenant's repository, at the paths the plan fixes ([`architecture/generation`](generation.md#the-plan)) | the engine, under the build steps' bounds |
| The change | `.weblisk/changes/<change id>.json` ([`schemas/change`](../schemas/change.md#where-it-lives)) | this service, and nothing else once it runs |
| The build lock | `.weblisk/build.lock` ([`schemas/build-lock`](../schemas/build-lock.md)) | this service, when an apply completes |
| Each run statement | `provenance/runs/<run id>.json`, in its DSSE envelope ([`schemas/run-statement`](../schemas/run-statement.md#where-it-lives)) | this service, once, never edited |
| Each model action's transcript | `provenance/transcripts/<run id>/<action id>.json`, cited by digest from the action ([`architecture/engine`](engine.md#the-record)) | this service |
| A configuration section a change wrote | `.weblisk/config.yaml`, recorded in the change's `config_written` ([`schemas/change`](../schemas/change.md#verdicts)) | this service, when apply builds the service it declares |
| The tenant's declared catalogue | `.weblisk/resources.json` ([`architecture/generation`](generation.md#resources)) | this service, whole, on every apply |
| Build runs, their events, open questions and cut-overs | the run journal, this service's own store ([`architecture/storage`](storage.md)) | this service |

The record is the tenant's, an answer about the customer's system, and no
client holds it ([`architecture/engine`](engine.md#the-record),
`record-in-tenant`). The journal is not a second record: it holds what a run
emitted and where it stands, and the run statement it wrote is the record of
what it did.

The change service MUST write only inside the tenant's directory and its own store, and only the files the table above names; it MUST NOT write a file outside the tenant's directory, a key, or a file a plan does not name. <!-- wl:id writes-only-the-tenant -->

**One writer at a time.** One build run at a time writes the tenant's tree or
starts and stops its components: an apply, a verify, a `component start` or a
`component stop`. The engine host takes the engine's tree lock for the
run's length, and the same lock is what the engine takes in a terminal at the
tenant's host, so the service and an operator at the host never write the
tree at once. A second such run is refused `CHANGE_BUSY`, naming the first.
Plans, reads and `test run` hold no lock.

At most one build run that writes the tenant's tree, or starts or stops a component, MUST run at a time, and another MUST be refused with `CHANGE_BUSY` naming the run that holds the tree. <!-- wl:id one-writer -->

---

## Supervision

### Restarting what a change rebuilt

A change is not applied until what it rebuilt is running. Once the build
gate has passed for a component
([`architecture/generation`](generation.md#the-verification-gate)), the
cut-over supervisor restarts it, through the engine's own `component stop`
and `component start`, which keep the one record of running processes the
tenant's host has, so a start from a terminal and one from here see each
other and a second instance is never started
([`architecture/cli`](cli.md#weblisk-server-start), `start-one-instance`).

1. **Only what is accepted.** A component is restarted only where its run's
   verdict is conformance `established`
   ([`schemas/run-statement`](../schemas/run-statement.md#the-verdict-a-run-ends-with)).
   A component that is not is left running as it was, and its outcome says
   why.
2. **In the services table's order**
   ([`schemas/programme`](../schemas/programme.md#the-services-in-the-order-they-are-built)),
   each after what it needs running first is running again, one at a time;
   this service is always last.
3. **Everything a start needs is in hand before anything is stopped**: each
   key passphrase its section names, read from its source as
   [`architecture/cli`](cli.md#weblisk-server-start) reads one. A source that
   does not answer stops nothing, and the cut-over ends `failed` with the old
   component still running.
4. **Started means answering.** The new process is waited on until its
   `GET /livez` answers live and then its `GET /readyz` answers ready, within
   `start_window` ([Configuration](#configuration)), and then the component's
   `live: safe` checks run against it.
5. **The previous build is kept until the new one is proven.** A component
   that does not answer live and then ready within the window, or that fails
   a `live: safe` check of a security criterion, is stopped, its previous
   build is put back and started, and its outcome is `failed`, with the
   change `failed`. The previous build is removed once the new one has passed.

The orchestrator's restart is a restart like any other: each registered
component renews its lease against it again, as
[`protocol/spec`](../protocol/spec.md#post-v1lease) says. The admin gateway's
restart closes every client's connection, the one following this run among
them; the run goes on, and the client subscribes again from its last position
([Following a build run](#following-a-build-run)).

A component MUST be restarted only once its run's verdict is conformance `established`, in the services table's order, with everything its start needs obtained before the running process is stopped. <!-- wl:id cut-over-after-the-gate -->

A component that does not answer live and then ready within `start_window`, or that fails a `live: safe` check of a security criterion once started, MUST be stopped and its previous build started again, and its outcome recorded `failed`. <!-- wl:id cut-over-falls-back -->

### Restarting itself

A change can rebuild the change service, because it is a component like
every other. It cannot stop itself and then start its successor, so it hands
over instead, and stays able to take back what it handed over:

1. It cuts over every other component first.
2. It writes a **handoff note** in its journal: the change, the build run,
   the digest of the new build and where its previous build is kept. It
   writes the run statement and the change's outcomes for everything else.
3. It closes its listener, deregisters, and marks itself stopped in the
   host's record of running processes, so its successor is no second
   instance.
4. It starts its successor through the engine's `component start`, and waits
   for it to answer live and then ready within `start_window`.
5. If the successor answers, the old process exits. The successor reads the
   handoff note when it starts, records its own outcome on the change, moves
   the change to `applied`, appends the run's last events after the old
   process's last `seq`, ends the run, and removes the note.
6. If it does not, the old process stops it, puts its previous build back,
   opens its listener again, registers again, and records its own outcome
   `failed`, with the change `failed`. It is the old process, still running,
   that takes it back, so no supervisor outside the tenant is needed.

A client following the run sees one stream throughout: the events before the
handoff from the old process, the events after it from the new, `seq` rising
by one across the two.

When a change rebuilds the change service, it MUST cut itself over last, by a handoff note in its journal, starting its successor while it is still running and taking its previous build back if the successor does not answer live and then ready within `start_window`. <!-- wl:id self-cut-over-by-handoff -->

### Surviving its own restart

The service may also stop with nothing handed over: a crash, a host that
restarts, an operator who stops it. When it starts, it reads its journal
before it answers anything:

- **A handoff note** is completed or taken back, as step 5 or 6 above says.
- **Every other run the journal holds as running or waiting** is ended
  `stopped`, with a `finished` event saying the change service restarted,
  and its run statement written `result: stopped` where the run had begun one
  ([`schemas/run-statement`](../schemas/run-statement.md#a-run-that-did-not-complete)).
  The tree lock it held is released. The change keeps its state.
- **It resumes nothing on its own.** A run spends the tenant's model, and a
  person decides whether it does: applying the change again resumes it, and
  every action already done is reused, never asked again
  ([`architecture/engine`](engine.md#how-the-record-makes-builds-incremental),
  `action-reused`).

On start, the change service MUST complete or take back a handoff note, and MUST end every other run its journal holds as running or waiting `stopped`, with a `finished` event, before it answers any route; it MUST NOT resume any run on its own. <!-- wl:id restart-ends-what-was-running -->

The change service MUST start with no terminal and its standard input closed, take its key's passphrase only as [`schemas/config`](../schemas/config.md#service-key-passphrases) gives it, and never prompt. <!-- wl:id starts-unattended -->

---

## The operation catalogue

[`architecture/engine`](engine.md#the-operation-catalogue) lists every
operation and its executor. This is where each `tenant-api` operation of a
change or a build is hosted, and which route a client's engine calls for it.
The executor of each is `tenant-api` in the catalogue; the act happens here,
in the engine this service hosts.

| Operation | Route | Capability | What happens here |
|---|---|---|---|
| `change plan` | `POST /v1/admin/changes` | `change:plan` | A build run of `change plan` ([Planning a change](#planning-a-change)) |
| `change revert` | `POST /v1/admin/changes`, `kind` `revert` | `change:plan` | A build run of `change plan` for a change of kind `revert` |
| `change list` | `GET /v1/admin/changes` | `change:read` | A read of `.weblisk/changes/` |
| `change show` | `GET /v1/admin/changes/{id}` | `change:read` | A read of one change |
| `change approve`, `change reject` | `POST /v1/admin/changes/{id}/decision` | `change:decide` | A signed decision recorded ([Approval](#approval)) |
| `change apply` | `POST /v1/admin/changes/{id}/apply` | `change:apply`, step-up | A build run of the eight build steps, then the cut-over |
| `change verify` | `POST /v1/admin/changes/{id}/verify` | `change:operate` | A build run of the suite against the applied tree; `verify` recorded on the change |
| `change stop` | `POST /v1/admin/build/runs/{run}/stop` | `change:operate` | The run ended `stopped` ([Stopping a build run](#stopping-a-build-run)) |
| `run status` | `GET /v1/admin/build/runs/{run}` | `change:read` | A read of one build run |
| `record show` | `GET /v1/admin/build`, `GET /v1/admin/build/statements/{statement}`, and its transcripts | `change:read` | A read of the lock, the statements and the transcripts |
| `test run` | `POST /v1/admin/build/runs` | `change:operate` | A build run of the suite |
| `tenant verify` | `POST /v1/admin/build/runs` | `change:operate` | A build run of the live checks |
| `component start`, `component logs` | `POST /v1/admin/build/runs` | `change:operate` | A build run of that operation on the tenant's host |
| `component stop` | `POST /v1/admin/build/runs` | `change:operate`, step-up | A build run of that operation on the tenant's host |

**A client's engine relays; the tenant's engine acts.** Where a person runs
one of these from the CLI or Studio, the engine in that front end calls the
route, and its stream is the run's events, read from the feed or the events
route, so the two front ends' streams of one operation are the same objects
([`architecture/engine`](engine.md#events), `streams-byte-equal`). Where a
read answers at once, the client's engine emits it as `item` events.

**What this service does not host**, and where each is:

| Operation | Where | Why not here |
|---|---|---|
| `tenant new` | `local`, on the host that will hold the tenant | No tenant, and so no change service, exists yet. The first change service a tenant runs is built by a `cli-in-tenant` change, as [`architecture/cli`](cli.md#until-a-tenant-runs-a-change-service) says, and every change after it is this service's |
| `tenant rebuild` | the host the rebuilt tenant will live on | The tenant it rebuilds is not running |
| `tenant export` | the tenant's host, `cli-in-tenant` | A bundle holds what the tenant is rebuilt from; how it leaves the tenant for a client is not specified ([Known Gaps](#known-gaps)) |
| `acceptance propose`, `acceptance decide` | — | [`schemas/change`](../schemas/change.md) holds no acceptance block yet, so there is nothing to propose into or record. The admin gateway answers them `ADMIN_GROUP_UNAVAILABLE` until this blueprint specifies their routes ([Known Gaps](#known-gaps)) |
| `build` | `local` | A scratch build outside any tenant |

The change service MUST run every operation it serves through the engine it hosts, and hold no build step, check, verdict rule, instruction or list of operations of its own. <!-- wl:id hosts-the-engine -->

---

## Audit

Every write is audited by this service, admitted or refused: a plan, a
decision, an apply, a verify, a stop, an answer and every build run started.
An `AuditEntry` records `actor` the pass's `identity_id`, `via` its
`act.identity_id`, `action` the route's operation, `target` the change or
build run, and `status`; a destructive act records the `step_up_at` it was
admitted on, before it takes effect
([`architecture/admin`](admin.md#contracts), `destructive-act-audited`). A
build run's own acts are recorded in its run statement, not as audit
entries: they are the service's, not a person's.

Every write this service serves MUST be audited, admitted or refused, with the pass's `identity_id` as `actor` and its `act.identity_id` as `via`, and an admitted destructive act MUST be audited with its `step_up_at` before it takes effect. <!-- wl:id every-write-audited -->

---

## Types

The change is [`schemas/change`](../schemas/change.md#shape)'s and the run
statement [`schemas/run-statement`](../schemas/run-statement.md#shape)'s, and
neither is restated here. `TenantChange` names the change as these routes
answer it, so the `change` kind has a type to declare its fields from.

```yaml
types:
  TenantChange:
    description: A change, as GET /v1/admin/changes/{id} answers it, in schemas/change's shape. Only the fields the change kind names are listed; every other member of that shape is answered as it is recorded
    fields:
      id: {type: string, required: true, description: 32 lowercase hex characters, minted when the change is planned}
      kind: {type: string, required: true, values: [adopt, upgrade, remove, revert]}
      state: {type: string, required: true, values: [planned, approved, rejected, applied, verified, failed, superseded]}
      request: {type: "list<string>", required: true}
      reverts: {type: string, required: false}
      requested_by: {type: string, required: true, description: The identity id of the person who asked}
      requested_at: {type: timestamp, required: true}
      strict: {type: bool, required: true}
      approver_position: {type: string, required: false}
      without_approval: {type: bool, required: false}
      applied_run: {type: string, required: false}
      run: {type: string, required: false, description: The build run that last acted on the change. Recorded by this service beside the change, never in its file}

  ChangePage:
    description: One page of GET /v1/admin/changes
    fields:
      changes: {type: "list<ref:TenantChange>", required: true}
      approvals: {type: "list<ref:ApprovalRequest>", required: false, description: "With awaiting=me only: each open request for a change the person on the pass may decide now, its id the change's id"}
      withheld: {type: integer, required: false, description: "With awaiting=me only: how many open requests this person may not read"}
      next_cursor: {type: string, required: false, description: Absent on the last page}

  ChangePlanRequest:
    description: The body of POST /v1/admin/changes
    fields:
      kind: {type: string, required: true, values: [adopt, upgrade, remove, revert]}
      request: {type: "list<string>", required: true, description: Each a ref or citation in the grammar of schemas/names, never a path}
      reverts: {type: string, required: false, description: The change a revert undoes. Present exactly when kind is revert}
      strict: {type: bool, required: false, default: false}
      drivers: {type: "list<string>", required: false, description: "Each <kind>.<backend>=<driver>: a backend driver change planned as though made, as architecture/cli's --driver"}
      replace_edited: {type: "list<ref:EditedFile>", required: false, description: Files a person names that the change may replace or remove, as architecture/cli's --replace-edited}

  EditedFile:
    description: One file a person names in a plan request, with why
    fields:
      path: {type: string, required: true}
      why: {type: string, required: true, min: 1}

  ChangeDecision:
    description: The body of POST /v1/admin/changes/{id}/decision. Verified as Verifying a decision says
    fields:
      decision: {type: string, required: true, values: [approve, reject]}
      plan_digest: {type: string, required: true, description: "sha256:<64 hex>: the change's plan digest, as the client showed it"}
      position: {type: string, required: false, description: The position decided as. Required where the change names approver_position}
      reason: {type: string, required: false, description: Required on reject}
      signed_at: {type: timestamp, required: true}
      attestation: {type: "ref:Attestation", required: true, description: The sign-records attestation vouching for the signing key (patterns/principal-identity)}
      signature: {type: string, required: true, description: "ML-DSA-65 by the attestation's credential_public_key over the weblisk/change-decision/v1 statement, unpadded base64url"}

  ChangeApplyRequest:
    description: The body of POST /v1/admin/changes/{id}/apply. Empty applies an approved change
    fields:
      without_approval: {type: bool, required: false, default: false, description: Development tenants only (Applying without an approval, in development only)}

  BuildRunRequest:
    description: The body of POST /v1/admin/build/runs
    fields:
      operation: {type: string, required: true, values: [test run, tenant verify, component start, component stop, component logs]}
      component: {type: string, required: false, description: The component a component operation acts on, by the name it registers under}
      live: {type: bool, required: false, default: false, description: test run only; run only the checks that declare live safe, against the running tenant}

  BuildRunStarted:
    description: The 202 answer of every route that starts a build run
    fields:
      run: {type: string, required: true, description: The build run's uid}
      events: {type: string, required: true, description: "The path of its events route, /v1/admin/build/runs/<uid>/events"}

  BuildRun:
    description: One engine invocation this service ran
    fields:
      uid: {type: string, required: true, description: Minted when the run is recorded. 32 lowercase hex characters}
      invocation: {type: uuid, required: true, description: The engine invocation's id, as its events carry it}
      operation: {type: string, required: true, description: The engine operation, noun and verb}
      change: {type: string, required: false, description: The change it is for, once known}
      component: {type: string, required: false}
      state: {type: string, required: true, values: [running, waiting, complete, failed, stopped]}
      requested_by: {type: string, required: true, description: The identity id of the person who started it}
      started_at: {type: timestamp, required: true}
      ended_at: {type: timestamp, required: false}
      stopped_by: {type: string, required: false, description: The identity id of who stopped it, absent where the service's own restart did}
      question: {type: "ref:EngineEvent", required: false, description: The open question event, while state is waiting}
      seq: {type: integer, required: true, description: The seq of its last event}
      last_event: {type: "ref:EngineEvent", required: true, description: Its last event}
      statements: {type: "list<string>", required: true, description: The run id of every run statement it wrote}
      reason: {type: string, required: false, description: The code it ended failed with, where it did}

  BuildRunPage:
    description: One page of GET /v1/admin/build/runs
    fields:
      runs: {type: "list<ref:BuildRun>", required: true}
      next_cursor: {type: string, required: false, description: Absent on the last page}

  BuildRunEvents:
    description: The answer of GET /v1/admin/build/runs/{run}/events
    fields:
      events: {type: "list<ref:EngineEvent>", required: true, description: Every event after the seq asked for, in seq order}
      ended: {type: bool, required: true, description: True once the run's finished event is among those it holds}

  BuildRunAnswer:
    description: The body of POST /v1/admin/build/runs/{run}/answer
    fields:
      seq: {type: integer, required: true, description: The seq of the question it answers}
      answer: {type: string, required: false, description: "For a choice, one of its choices; absent for confirm"}
      declined: {type: bool, required: false, default: false, description: True to decline, which ends the run refused, naming the question}

  EngineEvent:
    description: One event of an engine invocation, exactly the envelope architecture/engine's Events declares, under its six names and no others, in the RFC 8785 canonical form
    fields:
      operation: {type: string, required: true}
      invocation: {type: uuid, required: true}
      seq: {type: integer, required: true}
      at: {type: timestamp, required: true}
      type: {type: string, required: true}
      body: {type: object, required: true}

  BuildState:
    description: The answer of GET /v1/admin/build
    fields:
      lock: {type: object, required: false, description: The build lock as schemas/build-lock shapes it. Absent while the tenant holds none, never empty}
      lock_digest: {type: string, required: false, description: "sha256:<64 hex> of .weblisk/build.lock as stored"}
      statements: {type: "list<ref:StatementEntry>", required: true}

  StatementEntry:
    description: One run statement the tenant holds
    fields:
      id: {type: string, required: true, description: The run id it is stored under}
      digest: {type: string, required: true, description: "sha256:<64 hex> of the stored envelope"}
      component: {type: string, required: true}
      result: {type: string, required: true, values: [complete, failed, stopped]}
      build_run: {type: string, required: false, description: The build run that wrote it, absent for a statement no change service wrote}
```

A build run asks only `confirm` and `choice` questions. It asks no
passphrase, secret, vault or signature of anybody: the keys it uses are the
tenant's own, read as [`schemas/config`](../schemas/config.md#service-key-passphrases)
says, and a decision is signed at its own route, never inside a run.

A build run MUST ask no question but `confirm` and `choice`, and a question declined or left unanswered for `question_timeout` MUST end the run refused, naming the question. <!-- wl:id questions-confirm-and-choice -->

---

## Resources

```yaml
resources:
  - kind: change
    owner: change-service
    type: TenantChange
    identity: {field: id, form: minted}
    label: kind
    fields:
      - {name: id, access: read-only, present: text}
      - {name: kind, access: read-only, present: choice}
      - {name: state, access: read-only, present: choice}
      - {name: request, access: read-only, present: list}
      - {name: reverts, access: read-only, present: reference, kind: change}
      - {name: requested_by, access: read-only, present: text}
      - {name: requested_at, access: read-only, present: instant}
      - {name: strict, access: read-only, present: boolean}
      - {name: approver_position, access: read-only, present: text}
      - {name: without_approval, access: read-only, present: boolean}
      - {name: applied_run, access: read-only, present: text}
      - {name: run, access: read-only, present: reference, kind: build-run}
    operations:
      list: {capability: "change:read", binds: ListChanges, items: changes, filters: [state, kind]}
      get: {capability: "change:read", binds: GetChange}
    verbs:
      - name: decide
        capability: "change:decide"
        binds: DecideChange
        body: ChangeDecision
        preconditions:
          - the change is planned and its base still matches the tenant
          - for an approval, its conflicts do not refuse it, and the decider is not its requester unless the tenant is a development tenant
          - where it names approver_position, the decider holds that position
          - the decision's statement verifies, as Verifying a decision says
        in_flight:
          handling: none
          says: a planned change has no work under way
        effect: the approval or rejection is recorded on the change, which becomes approved or rejected, and its approval request is closed
        reversible: false
      - name: apply
        capability: "change:apply"
        step_up: true
        binds: ApplyChange
        body: ChangeApplyRequest
        preconditions:
          - the change is approved, or planned with without_approval on a development tenant
          - its base still matches the tenant and its conflicts do not refuse it
          - no other build run holds the tenant's tree
        in_flight:
          handling: none
          says: nothing writes the tree while another run holds it, so an apply starts only when none is under way
        effect: a build run of change apply is started; the change becomes applied or failed when it ends
        reversible: false
      - name: verify
        capability: "change:operate"
        binds: VerifyChange
        preconditions:
          - the change is applied
          - no other build run holds the tenant's tree
        in_flight:
          handling: none
          says: verify starts only when no run holds the tree
        effect: a build run of change verify is started; verify is recorded on the change when it ends
        reversible: false
    states:
      initial_state: planned
      entity_type: TenantChange
      state_field: state
      states:
        planned: {description: the plan is written and awaits a decision}
        approved: {description: a person approved it}
        rejected: {description: a person rejected it, terminal: true}
        applied: {description: what it builds is built and running}
        verified: {description: its verification passed, terminal: true}
        failed: {description: its apply or its verification failed, terminal: true}
        superseded: {description: a moved corpus, lock or ledger made it stale and a later change replaced it, terminal: true}
      transitions:
        - {name: approve, from: planned, to: approved, trigger: a person's verified decision at DecideChange, description: it may be applied}
        - {name: reject, from: planned, to: rejected, trigger: a person's verified decision at DecideChange, description: it will not be applied}
        - {name: apply, from: [approved, planned], to: applied, trigger: an apply run completes and its cut-over passes, description: it is built and running}
        - {name: fail, from: [approved, planned, applied], to: failed, trigger: an apply or verify run ends failed, description: it did not do what it planned}
        - {name: verify, from: applied, to: verified, trigger: a verify run passes, description: its verification passed}
        - {name: supersede, from: [planned, approved], to: superseded, trigger: a later plan replaces it, description: it will not be applied}
    events: [created, updated, approved, rejected, applied, verified, failed, superseded, decide, apply, verify]

  - kind: build-run
    owner: change-service
    type: BuildRun
    identity: {field: uid, form: minted}
    label: operation
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: invocation, access: read-only, present: text}
      - {name: operation, access: read-only, present: text}
      - {name: change, access: read-only, present: reference, kind: change}
      - {name: component, access: read-only, present: text}
      - {name: state, access: read-only, present: choice}
      - {name: requested_by, access: read-only, present: text}
      - {name: started_at, access: read-only, present: instant}
      - {name: ended_at, access: read-only, present: instant}
      - {name: stopped_by, access: read-only, present: text}
      - {name: question, access: read-only}
      - {name: seq, access: read-only, present: number}
      - {name: last_event, access: read-only}
      - {name: statements, access: read-only, present: list}
      - {name: reason, access: read-only, present: text}
    operations:
      list: {capability: "change:read", binds: ListBuildRuns, items: runs, filters: [operation, state, change]}
      get: {capability: "change:read", binds: GetBuildRun}
    verbs:
      - name: stop
        capability: "change:operate"
        binds: StopBuildRun
        transition: stop
        preconditions:
          - the run is running or waiting
        in_flight:
          handling: cancels
          says: the model call under way is closed and recorded cancelled; a file being written is finished or not written; a component start under way is finished; nothing further starts
        effect: the run is stopped, stopped_by names the person's identity id, its run statement says stopped, and the change keeps the state it had
        reversible: false
      - name: answer
        capability: "change:operate"
        binds: AnswerBuildRun
        body: BuildRunAnswer
        transition: answer
        preconditions:
          - the run is waiting on the question whose seq the body names
          - the person answering started the run
        in_flight:
          handling: continues
          says: the run resumes from the question it asked
        effect: the run is running again; a declined question ends it refused, naming the question
        reversible: false
    states:
      initial_state: running
      entity_type: BuildRun
      state_field: state
      states:
        running: {description: the engine is running the operation}
        waiting: {description: it asked a question and waits for its answer}
        complete: {description: the operation finished, terminal: true}
        failed: {description: it ended badly, naming why, terminal: true}
        stopped: {description: a person or the service's restart stopped it, terminal: true}
      transitions:
        - {name: ask, from: running, to: waiting, trigger: the engine emits a question, description: it waits for its requester}
        - {name: answer, from: waiting, to: running, trigger: manual, description: its requester answers}
        - {name: complete, from: running, to: complete, trigger: the engine emits finished with success, description: it ends well}
        - {name: fail, from: [running, waiting], to: failed, trigger: the engine emits finished with a failure, or a question is declined, description: it ends badly}
        - {name: stop, from: [running, waiting], to: stopped, trigger: manual, description: a person stops it}
    events: [created, updated, waiting, complete, failed, stopped, stop, answer]
```

**Each engine event is an `updated` event of its build run.** A run's `seq`
and `last_event` change with every event the engine emits, so each one is
announced as `weblisk.build-run.updated`, its data those two fields, and a
client subscribed to one run reads every event of it, in order, on the feed.
A run entering `waiting`, `complete`, `failed` or `stopped` is announced by
that state's event as well.

Every engine event a build run emits MUST be announced on the `build-run` feed as that run's `updated` event, carrying `seq` and `last_event`, in `seq` order with none left out. <!-- wl:id every-event-on-the-feed -->

The `stop` transition is the only manual one besides `answer`; a change's
transitions are fired by a verified decision or by a run's end, never by
hand, which is why the change kind's verbs fire none.

---

## Configuration

```yaml
change_service:
  port: 9809              # schemas/config's Port Conventions
  start_window: 120s      # how long a restarted component has to answer live, then ready
  question_timeout: 30m   # how long a run waits on its requester's answer
  approval_expiry: 336h   # how long an approval request stays open undecided
  event_retention: 9600h  # how long a finished run's events are kept in the journal
```

The section is [`schemas/config`](../schemas/config.md#change_service)'s.
A start window, a timeout and an expiry are the tenant's to set; none bounds
how long a model may work, which is the backend's own window and a person's
stop ([Stopping a build run](#stopping-a-build-run)).

---

## Security

```yaml
security:
  trust_model:
    description: |
      The change service trusts a person's authority only on a pass, and a
      person's decision only as their own signature over the plan it
      decides. It holds no person's token, and its build runs carry no
      person's authority anywhere: what a run may do is bounded by the
      change it runs, the pins that change read and the engine's build
      steps. It is the one tenant component that writes the tenant's code
      and restarts its components, so it is the one that must never act
      on anything but an approved plan, or, in development only, the
      operator's recorded word.

  boundaries:
    - boundary: Person → Change service. Only through the admin gateway, on a
        pass addressed here. An operator token is refused
    - boundary: Change service → Model service. Its own registration token
        and llm:chat, behind the tenant's destination gate
    - boundary: Change service → Tenant host. The tenant's directory, the
        engine's toolchain commands and the tenant's own component processes,
        and nothing outside them
    - boundary: Change service → Orchestrator. Registration and lease, as
        every component

  enforcement:
    - rule: Nothing is built that nobody approved
      mechanism: An apply needs a verified decision over the plan's digest,
        or, on a development tenant only, without_approval recorded on the
        change
    - rule: Nothing is built that nobody saw
      mechanism: An apply reads the corpus at the change's pins and refuses a
        stale change
    - rule: A destructive act is the person's own
      mechanism: Apply and component stop need a step_up_at at most 300
        seconds old
    - rule: A machine never decides
      mechanism: change:decide is person only, checked on a pass and never
        held
    - rule: A failed restart never leaves the tenant without a component it
        had
      mechanism: The previous build is kept until the new one answers live,
        ready and its live safe security checks
```

The model is given no tool, no file and no shell; the engine writes every file
itself after checking its path, as
[`architecture/engine`](engine.md#security) and
[`architecture/generation`](generation.md#security) say.

---

## Implementation Notes

- **Journal before acting.** A run is recorded before the route answers
  `202`; an event before it is announced; a handoff note before the listener
  closes. A restart then finds everything it must end or complete.
- **The feed and the events route read one journal.** The feed's position for
  a run's `updated` event and the event's `seq` rise together, so a client
  that switches from one to the other loses nothing.
- **Hold the tree lock across the cut-over.** The run that built a component
  restarts it, under the same lock, so no second run sees a tree whose
  processes are half restarted.
- **A stale change is a fact to show, not an error to hide.** `CHANGE_STALE`
  carries the base that moved in `detail`, so a client can say which.
- **Nothing here names a component, a kind or a route of another blueprint.**
  Restart order is the services table's, the start of each component is the
  engine's, and the checks are the corpus's, each read at run time.

---

## Known Gaps

- **A console holds no sign-records credential**
  ([`architecture/admin`](admin.md#contracts), `console-no-sign-records`), so
  a decision is signed on the person's own device, by the CLI, and a console
  sends one only where the person's own signer gives it the signature. How
  Studio carries that signature is Studio's to specify, and until it does,
  Studio shows a change's decision and does not make one.
- **Who holds a position cannot be read here yet.** The register is in
  content, and this service holds no work authorisation to read it with. A
  knowledge change's decision is refused `CHANGE_POSITION_UNRESOLVED` until
  one is specified.
- **Work that outlives a request rests on no carried authority.** A build run
  is this service's own work, bounded by the approved plan. The authority on
  an approver's behalf that `admin-gateway-authorization` records as missing
  is still missing; this blueprint does not invent one, and a run makes no
  request on anybody's behalf.
- **The `generation` credential does not exist.** Run statements are written
  unsigned until the credential layer does
  ([`schemas/run-statement`](../schemas/run-statement.md#signing)).
- **Acceptance.** `acceptance propose` and `acceptance decide` have no
  routes until [`schemas/change`](../schemas/change.md) holds an acceptance
  block ([`ACCEPTANCE_PLAN.md`](../ACCEPTANCE_PLAN.md)). Until then the
  cut-over admits conformance `established` alone.
- **Committing the record.** This blueprint writes the record into the
  tenant's working tree; whether and how a change is committed to the
  tenant's history is specified nowhere yet.
- **`tenant export` across the boundary.** How a bundle reaches a client is
  not specified, so the export stays at the tenant's host.
- **Every tenant should run one.** The kind's `count.min` is `0`, because
  every tenant built before this blueprint runs none, and a minimum of one
  would refuse them all. It becomes `1` when `tenant new` builds one.

---

## Declared Checks

Checks of the kinds [`schemas/blocks`](../schemas/blocks.md#checks) declares.
Joining the tenant is the Level 4 checks' of
[`architecture/testing`](testing.md#level-4-interoperability), which every
registering component owes, and is not declared again here.

```yaml
verifies:
- id: routes-answered
  covers: [serves-the-endpoints]
  check: exchange
  assertion: 'Every pass route is routed: a request without a token is answered by the route, never 404 or 405 and never a redirect.'
  live: safe
  exchange:
    steps:
    - as: anonymous
      request: {method: GET, path: /v1/admin/changes}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: POST, path: /v1/admin/changes, body: {}}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/changes/00000000000000000000000000000000}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: POST, path: /v1/admin/changes/00000000000000000000000000000000/decision, body: {}}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: POST, path: /v1/admin/changes/00000000000000000000000000000000/apply, body: {}}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: POST, path: /v1/admin/changes/00000000000000000000000000000000/verify, body: {}}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/build}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/build/runs}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: POST, path: /v1/admin/build/runs, body: {}}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/build/runs/00000000000000000000000000000000}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/build/runs/00000000000000000000000000000000/events}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: POST, path: /v1/admin/build/runs/00000000000000000000000000000000/stop, body: {}}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: POST, path: /v1/admin/build/runs/00000000000000000000000000000000/answer, body: {}}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/build/statements/conformance-probe}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/build/statements/conformance-probe/transcripts/conformance-probe}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/events/change}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/events/build-run}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
    - as: anonymous
      request: {method: GET, path: /v1/admin/records/change-service/snapshot}
      expect: {status_not: [301, 302, 303, 307, 308, 404, 405]}
- id: registration-token-refused
  covers: [serves-the-endpoints, pass-routes-are-the-endpoints]
  check: exchange
  assertion: A registration token is not a pass, so a read and an apply on one are refused FORBIDDEN, and nothing starts.
  live: safe
  exchange:
    start: {orchestrator: mock}
    steps:
    - as: test-agent
      request: {method: GET, path: /v1/admin/changes, token: own}
      expect: {status: 403, code: FORBIDDEN}
    - as: test-agent
      request: {method: POST, path: /v1/admin/changes/00000000000000000000000000000000/apply, token: own, body: {}}
      expect: {status: 403, code: FORBIDDEN}
    - as: test-agent
      request: {method: POST, path: /v1/admin/build/runs, token: own, body: {operation: component stop, component: conformance-probe}}
      expect: {status: 403, code: FORBIDDEN}
- id: agent-endpoints-take-nothing
  covers: [serves-the-endpoints]
  check: exchange
  assertion: The change service takes no task, message or event, so each is answered FORBIDDEN on a valid registration token.
  exchange:
    start: {orchestrator: mock}
    steps:
    - as: test-agent
      request: {method: POST, path: /v1/execute, token: own, body: {}}
      expect: {status: 403, code: FORBIDDEN}
    - as: test-agent
      request: {method: POST, path: /v1/message, token: own, body: {}}
      expect: {status: 403, code: FORBIDDEN}
    - as: test-agent
      request: {method: POST, path: /v1/event, token: own, body: {}}
      expect: {status: 403, code: FORBIDDEN}
- id: restarts-unattended
  covers: [starts-unattended]
  check: topology
  assertion: Started with no terminal and standard input closed, the service binds its port and answers live, and does so again after a restart.
  topology:
    instances:
    - {name: a, stdin: closed}
    acts:
    - {act: start, instance: a, expect: live, within: 20s}
    - {act: restart, instance: a, expect: live, within: 20s}
- id: change-error-codes-registered
  covers: ['languages/go:declared-type-enum-constant-path-operation']
  check: structure
  assertion: 'Every error code the code uses is a key of the central registry, the change service''s own codes among them.'
  structure:
    query: error-code-use
    scope: module
    expect: {subset_of: error-code-registered}
- id: change-no-path-literals
  covers: ['languages/go:routed-path-exported-path-operation-constant']
  check: structure
  assertion: Every routed path is a Path<Operation> constant, so a path is corrected in one place.
  structure: {query: path-literal, scope: outside-contract, expect: none}
```

---

## Verification Checklist

- [ ] Every route of [Endpoints](#endpoints) is served at its method and path, and a request without a token to each pass route is answered by that route, never as an unknown path or method and never by a redirect <!-- wl:check routes-answered covers serves-the-endpoints -->
- [ ] A registration token on `GET /v1/admin/changes`, on `ApplyChange` and on `StartBuildRun` is refused `FORBIDDEN` and nothing starts ([Error Handling](#error-handling)) <!-- wl:check registration-token-refused covers serves-the-endpoints pass-routes-are-the-endpoints -->
- [ ] `POST /v1/execute`, `POST /v1/message` and `POST /v1/event` are answered `FORBIDDEN` and do nothing ([Error Handling](#error-handling)) <!-- wl:check agent-endpoints-take-nothing covers serves-the-endpoints -->
- [ ] The manifest's `pass_routes` equal [The gateway's allow-list for this service](#the-gateways-allow-list-for-this-service), and only `GET /v1/admin/changes` carries an `inbox`, whose `decide_path` is `/v1/admin/changes/{id}/decision` <!-- wl:check pass-routes-match covers pass-routes-are-the-endpoints -->
- [ ] The service registers as `change-service`, type `infrastructure`, declaring `change:read`, `change:plan`, `change:apply`, `change:operate` and `llm:chat` and never `change:decide` or `admin:*` ([The manifest](#the-manifest)) <!-- wl:check manifest-as-declared covers registers-as-change-service -->
- [ ] A plan runs no model call and writes only `.weblisk/changes/<id>.json` in the tenant's repository; a plan with no entries ends its run `failed` ([Planning a change](#planning-a-change)) <!-- wl:check plan-writes-only-change covers plan-writes-only-the-change -->
- [ ] A decision whose statement fails any one of the six conditions is refused `CHANGE_DECISION_INVALID` naming it, and the change stays `planned` ([Verifying a decision](#verifying-a-decision), [Error Handling](#error-handling)) <!-- wl:check decision-conditions covers decision-verified -->
- [ ] A decision whose signature was made over another change's id or another plan digest does not verify ([Verifying a decision](#verifying-a-decision)) <!-- wl:check decision-bound-to-plan covers decision-verified -->
- [ ] An approval by the requester is refused `APPROVAL_SELF_DENIED` on a tenant whose `hub.environment` is not `development`, and on a development tenant is recorded with `development: true` ([Approval](#approval), [Error Handling](#error-handling)) <!-- wl:check self-approval covers self-approval-development-only -->
- [ ] An approval of a change with a refusing conflict is refused `CHANGE_CONFLICT_REFUSES`, and a decision on a stale change `CHANGE_STALE` ([Approval](#approval), [Error Handling](#error-handling)) <!-- wl:check decision-conflict-stale covers decision-refuses-conflict-and-stale -->
- [ ] A decision on a change naming `approver_position` is refused `CHANGE_POSITION_UNRESOLVED` while who holds the position cannot be read, and nothing is recorded ([Approval](#approval), [Error Handling](#error-handling)) <!-- wl:check position-unresolved covers decision-position-held -->
- [ ] A change awaiting a decision is listed under `approvals` by `GET /v1/admin/changes?awaiting=me` as an `ApprovalRequest` whose `id` and `change_id` are the change's id ([Approval](#approval)) <!-- wl:check change-in-inbox covers change-awaits-in-inbox pass-routes-are-the-endpoints -->
- [ ] `ApplyChange` without a `step_up_at` within 300 seconds is refused `STEP_UP_REQUIRED` and starts nothing ([Who May Do What](#who-may-do-what), [Error Handling](#error-handling)) <!-- wl:check apply-needs-step-up covers destructive-acts-here -->
- [ ] An apply of a `planned` change is refused `CHANGE_NOT_APPROVED` without `without_approval`; with it, it is refused `CHANGE_WITHOUT_APPROVAL_REFUSED` outside development and recorded `without_approval: true` in development ([Applying without an approval, in development only](#applying-without-an-approval-in-development-only), [Error Handling](#error-handling)) <!-- wl:check without-approval covers without-approval-development-only -->
- [ ] An apply of a stale change is refused `CHANGE_STALE`, and of a change with a refusing conflict `CHANGE_CONFLICT_REFUSES`, with `without_approval` as without it ([Applying without an approval, in development only](#applying-without-an-approval-in-development-only), [Error Handling](#error-handling)) <!-- wl:check apply-stale-conflict covers apply-refuses-stale-and-conflict -->
- [ ] While an apply runs, a second apply, a verify and a `component stop` are refused `CHANGE_BUSY` naming the running run, and a plan is admitted ([Where it writes](#where-it-writes), [Error Handling](#error-handling)) <!-- wl:check one-writer-at-a-time covers one-writer -->
- [ ] Every model call of an apply is `POST /v1/model/complete` on the service's registration token with `run` the build run's uid; with the tenant's model unconfigured the run ends `failed` naming `MODEL_NOT_CONFIGURED` and no other backend is called ([Whose model](#whose-model), [Error Handling](#error-handling)) <!-- wl:check tenant-model covers tenant-model-only -->
- [ ] An apply writes only the files [Where it writes](#where-it-writes) names, inside the tenant's directory and its own store <!-- wl:check writes-inside-tenant covers writes-only-the-tenant -->
- [ ] A client following a run on `GET /v1/admin/ws` and one reading `GET /v1/admin/build/runs/{run}/events` from `seq` 0 receive the same events in the same order, with none missing, across a restart of the admin gateway ([Following a build run](#following-a-build-run), [Resources](#resources)) <!-- wl:check one-stream-two-doors covers events-journalled-before-announced every-event-on-the-feed -->
- [ ] `StopBuildRun` on a running apply is admitted without a step-up, ends the run `stopped`, leaves the change `approved`, and a second apply reuses every action the first completed ([Stopping a build run](#stopping-a-build-run)) <!-- wl:check stop-and-resume covers stop-without-step-up -->
- [ ] `StartBuildRun` naming an operation outside the five is refused `INVALID_REQUEST`, and `component stop` without a recent step-up `STEP_UP_REQUIRED` ([Starting a build run that is not a change](#starting-a-build-run-that-is-not-a-change), [Error Handling](#error-handling)) <!-- wl:check build-run-operations covers build-run-operations-closed destructive-acts-here -->
- [ ] Once `ApplyChange` is answered, no request the run makes carries a pass, an operator token or a work pass ([Who May Do What](#who-may-do-what)) <!-- wl:check run-no-authority covers run-carries-no-authority -->
- [ ] An answer to a run's question by a person other than its requester is refused `FORBIDDEN` ([Who May Do What](#who-may-do-what), [Error Handling](#error-handling)) <!-- wl:check answer-by-requester covers only-requester-answers -->
- [ ] A run's question is only `confirm` or `choice`, and one declined or unanswered for `question_timeout` ends the run refused, naming it ([Types](#types)) <!-- wl:check run-questions covers questions-confirm-and-choice -->
- [ ] A component whose run's conformance is not `established` is not restarted; those that are restart in the services table's order with this service last, and a key-passphrase source that does not answer stops nothing ([Restarting what a change rebuilt](#restarting-what-a-change-rebuilt)) <!-- wl:check cut-over-order covers cut-over-after-the-gate -->
- [ ] A rebuilt component that never answers ready within `start_window` is stopped, its previous build is running again, its outcome is `failed` and the change is `failed` ([Restarting what a change rebuilt](#restarting-what-a-change-rebuilt)) <!-- wl:check cut-over-fallback covers cut-over-falls-back -->
- [ ] A change rebuilding the change service ends with the successor running and the run's events continuing in `seq`; with a successor that never answers ready, the old process is running and registered again with its previous build, and the change is `failed` ([Restarting itself](#restarting-itself)) <!-- wl:check self-handoff covers self-cut-over-by-handoff -->
- [ ] The service killed mid-apply and started again answers no route until it has ended that run `stopped` with a `finished` event, released the tree, and left the change `approved`; it starts no run on its own ([Surviving its own restart](#surviving-its-own-restart)) <!-- wl:check restart-ends-runs covers restart-ends-what-was-running -->
- [ ] Started with no terminal and standard input closed, the service answers live, and does so again after a restart ([Surviving its own restart](#surviving-its-own-restart)) <!-- wl:check restarts-unattended covers starts-unattended -->
- [ ] Each operation of [The operation catalogue](#the-operation-catalogue) this service hosts runs through the engine, and the service's source holds no build step, check, verdict rule, instruction or operation list of its own ([`architecture/engine`](engine.md#neutrality-the-engine-holds-no-corpus-knowledge)) <!-- wl:check runs-the-engine covers hosts-the-engine -->
- [ ] Every admitted and refused write is audited with `actor` and `via`, and an admitted apply's entry carries its `step_up_at` and is written before the run starts ([Audit](#audit)) <!-- wl:check writes-audited covers every-write-audited -->
- [ ] Every error code the code uses is registered, its own in [Error Handling](#error-handling) <!-- wl:check change-error-codes-registered -->
- [ ] Every routed path is a path constant of its operation <!-- wl:check change-no-path-literals -->
