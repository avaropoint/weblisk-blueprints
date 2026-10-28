<!-- blueprint
type: architecture
name: model-service
version: 1.1.0
requires: [protocol/types, protocol/identity, architecture/orchestrator, patterns/scope]
platform: any
tier: free
-->

# Weblisk Model Service

The one place every tenant component gets a completion from the tenant's
model, for work nobody is watching: the backend a person chose, behind the
destination gate, with one audit entry pair and one usage record for every
completion.

## Overview

A tenant has one model, and it is the tenant's. A person chooses its backend
at `PUT /v1/admin/model`, and a person asks it for a completion at
`POST /v1/admin/complete`
([`architecture/orchestrator`](orchestrator.md#the-tenants-model)). Neither
route admits a registered component: `/v1/admin/` admits a person's operator
token alone. So a component doing unattended work, the prompt worker first
([`architecture/prompt-worker`](prompt-worker.md)),
had two choices: no model at all, or a provider of its own reached through
enforcement's external boundary on `model:route`, which makes every component
that runs agent work its own model route.

This document specifies the third: **the model service**. It is the model
gateway the CLI already installs in the orchestrator's process, which gains
one route for a registered component, `POST /v1/model/complete`. That route
runs a completion exactly as `POST /v1/admin/complete` does, on the same
configuration, behind the same gate, recorded in the same audit log. What it
adds is what unattended work needs and a person's request did not: it is
reached on the component's own registration token, it says which run a
completion was for, and it reports what the completion used, so that the run's
record can say what its model work cost.

**The model service is the model gateway, not a component beside it** (an
owner decision; [Design Principles](#design-principles), 1). One place chooses
the backend: the tenant's `ModelConfig`, changed only at
`PUT /v1/admin/model`. One place runs every completion: the model gateway. One
audit records every completion: the orchestrator's hash-chained log, as two
`model_complete` entries.

> **Scope boundary.** This document specifies the service route, what a
> caller may ask and on which token, the usage each completion reports, the
> `Completion` record, and the refusals the service route adds. The model
> configuration, the backends, the person's completion route, agreements,
> ceilings and the recording route for a person's request stay
> [`architecture/orchestrator`](orchestrator.md#the-tenants-model)'s, and are
> cited here, never restated. What may be sent to a model is
> [`patterns/scope`](../patterns/scope.md#model-providers)'s.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    # 6.2.0 is where MODEL_BACKEND_LIMITED is registered beside RunUsage
    version: ">=6.2.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category, retryable, retry_after, detail]
        # The audit log the service records every completion in
        - name: AuditEntry
          fields_used: [id, timestamp, actor, action, target, detail, status]
        # A caller asks the model on its own registration, which names it
        - name: AgentManifest
          fields_used: [name, capabilities]
        # The one usage type, shared with the run record
        - name: RunUsage
          fields_used: [prompt_tokens, completion_tokens, total_tokens, cost]
        - name: RunCost
          fields_used: [amount, currency]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=2.0.0 <4.0.0"
    bindings:
      types:
        # A registration token: no type, no cid; cap is what its manifest
        # declares; identity_id names who asked
        - name: WLToken
          fields_used: [sub, cap, cid, type, identity_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/orchestrator
    version: ">=4.1.0 <5.0.0"
    bindings:
      types:
        # The one configuration that chooses the backend and the model
        - name: ModelConfig
          fields_used: [provider, model, base_url, roles]
        # What a completion asks, and what it answers, on either route
        - name: CompletionRequest
          fields_used: [messages, system, role, scope]
        - name: CompletionResponse
          fields_used: [content, provider, model]
        # The service route records through POST /v1/model/audit, which the
        # orchestrator serves, and its Auth Middleware judges the caller's
        # token there (Recording what the model routes do)
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/scope
    version: ">=3.0.0 <4.0.0"
    bindings:
      types:
        - name: ScopeLevel
        - name: DestinationRefusal
          fields_used: [destination, ceiling, items]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
 prompt worker ─┐                                      ┌─► the tenant's backend
 (any component │  POST /v1/model/complete             │   (ModelConfig.provider)
 declaring      ├──── registration token ──► model ────┤
 llm:chat)      │                           gateway    │
                │                           (in the    └─► .weblisk/model-completions.jsonl
 person ── admin gateway ── operator token  orchestrator's     (Completion records)
                POST /v1/admin/complete ──► process)
                                              │  in process
                                              ▼
                       POST /v1/model/audit  ·  POST /v1/admin/model/audit
                                              │
                                              ▼
                              the orchestrator's audit log (hash chain)
```

- **The model gateway is the model service.** It is the code the CLI installs
  in the orchestrator's process ([`architecture/orchestrator`](orchestrator.md#administrative-endpoints)).
  It serves the person's model routes, which the orchestrator specifies, and
  the service route, which this document specifies. Both run a completion by
  one procedure, on one configuration.
- **The orchestrator judges every token and keeps the one audit log.** The
  gateway judges nothing on a token's shape: it has the orchestrator judge
  the caller's token when it appends the completion's first entry, as
  [Recording what the model routes do](orchestrator.md#recording-what-the-model-routes-do)
  says of the person's route.
- **The backend is the tenant's, and only answers.** Which kinds of backend
  the gateway may run, and what makes one available, are the orchestrator's
  ([The tenant's model](orchestrator.md#the-tenants-model)).

## Responsibilities

### Owns

- `POST /v1/model/complete`: a completion asked by a registered component, on
  its own registration token
- The `Completion` record of every completion the model gateway runs, on
  either route: who asked, for which run, what ran, how it ended, and what it
  used as the backend reported it
- The usage a completion reports to its caller, which a run's record takes
  its model, tokens and cost from
- Relaying the backend's own limit as the backend's, with
  `MODEL_BACKEND_LIMITED`

### Does NOT Own

- **The choice of backend and model.** It is the tenant's `ModelConfig`,
  changed only at `PUT /v1/admin/model`
  ([`architecture/orchestrator`](orchestrator.md#the-tenants-model)). No
  request names a backend or a model, on either route
- **Which backends are available.** `GET /v1/admin/model/providers` says so,
  and the gateway runs only one it reports available
- **A ceiling, or an agreement that raises one.** Both are the
  orchestrator's ([A model is a destination](orchestrator.md#a-model-is-a-destination))
- **The audit log.** It is the orchestrator's hash chain; the gateway appends
  to it through the orchestrator's recording routes
- **A run.** The run, its ledger and its record are execution's
  ([`architecture/domain`](domain.md)). The service records the `run` a
  caller states, and keeps no run
- **What a prompt may carry.** The caller states the scope of its prompt, and
  the gate refuses what is above the ceiling
  ([`patterns/scope`](../patterns/scope.md#the-gate)). What the prompt worker
  may read for a run is the worker's, under its run's ceiling
- **A prompt or an answer.** Neither is kept, recorded or logged

---

## Endpoints

| Method | Path | Operation | Auth | Capability | Purpose |
|--------|------|-----------|------|------------|---------|
| POST | /v1/model/complete | ModelComplete | yes | `llm:chat` | Run a completion on the tenant's model for a registered component, on its own registration token, behind the destination gate; answer what ran and what it used. Platform-provided ([Asking the model unattended](#asking-the-model-unattended)) |

The route is `provided: platform`
([`schemas/architecture`](../schemas/architecture.md#provided-platform--declared-and-not-generated)):
the CLI's model gateway serves it, for the reason the person's model routes
are the CLI's. It is held to this document as generated code is held to its
blueprint.

It is not under `/v1/admin/`, so the admin gateway carries no request to it
([`architecture/admin`](admin.md#contracts), `admin-gateway-authorization`),
and a person never reaches it. A person asks the tenant's model at
`POST /v1/admin/complete`.

The service serves no `/livez` or `/readyz` of its own: it is in the
orchestrator's process, whose probes answer for it.

---

## Interfaces

**Consumed by every registered component that asks the tenant's model**, the
prompt worker first. A component declares `llm:chat` on its signed manifest
([`protocol/types`](../protocol/types.md#capability)), and its registration
token then carries it.

**Consumed by execution, through the caller.** A `ServiceCompletionResponse`
carries the `Completion` id, the backend and model that ran, and the
`RunUsage`. The prompt worker hands those back with its phase result,
and execution writes them on the run's record, as the run record's model,
tokens and cost ([Usage and cost](#usage-and-cost)).

**What a caller reads an answer as:**

| Answer | The caller reads it as |
|---|---|
| `200` | The completion ran. `response.model` is the model the backend says ran, absent where it said none |
| `MODEL_NOT_CONFIGURED`, `MODEL_BACKEND_UNAVAILABLE`, `MODEL_NONE_LOADED` | The tenant has no model this route can run now. The work is not runnable, and is never reported as having run |
| `SCOPE_MISSING`, `SCOPE_CEILING_EXCEEDED` | What the prompt carries may not go to this backend. Nothing was sent |
| `MODEL_BACKEND_LIMITED` | The backend's own limit refused it. Nothing ran. Retry no sooner than `retry_after`, where it is given |
| `MODEL_BACKEND_FAILED` | The backend failed, or refused its model. Nothing else ran |
| `404` | No model gateway serves the route at this hub. The work is not runnable |

## Error Handling

| Code | HTTP | When |
|---|---|---|
| `INVALID_REQUEST` | 400 | The body is not a `ServiceCompletionRequest`: `request` is absent, carries no message, or names `provider` or `model`; or `run` or `phase` is present and empty |
| `FORBIDDEN` | 403 | An operator token, a channel token or the admin gateway's registration token; or a registration token whose `cap` does not name `llm:chat` ([Who may ask](#who-may-ask)) |
| `PASS_AUDIENCE_MISMATCH` | 401 | A pass was presented. The orchestrator is the audience of none ([`protocol/identity`](../protocol/identity.md#the-pass), rule 3) |
| `CREDENTIAL_REQUIRED` | 401 | An attestation token was presented ([Auth Middleware](orchestrator.md#auth-middleware), step 5) |
| `SCOPE_MISSING` | 400 | `request.scope` is absent ([`patterns/scope`](../patterns/scope.md#the-gate)). `detail` is a `DestinationRefusal` |
| `SCOPE_CEILING_EXCEEDED` | 403 | `request.scope` is above the ceiling, or is `restricted` or above whatever the ceiling. `detail` is a `DestinationRefusal` |
| `MODEL_NOT_CONFIGURED` | 409 | The hub holds no model configuration, as at `POST /v1/admin/complete` ([`architecture/orchestrator`](orchestrator.md#the-tenants-model)) |
| `MODEL_BACKEND_UNAVAILABLE` | 409 | The configured backend is not one this hub can run now, as at `POST /v1/admin/complete` |
| `MODEL_NONE_LOADED` | 409 | The configuration names no model for the role and the backend, a local model server, reports none loaded, as at `POST /v1/admin/complete` |
| `MODEL_BACKEND_LIMITED` | 429 | The backend refused it under its own rate or quota limit. `retry_after` is the seconds until the backend said its window resets, and is absent where it said nothing. `detail` names the backend. Nothing ran ([Limits](#limits)) |
| `MODEL_BACKEND_FAILED` | 502 | The backend failed to answer, or refused the model it was asked for, as at `POST /v1/admin/complete` |
| `MODEL_UNRECORDED` | 503 | The route could not record what it was about to do, so it did not do it, or what it did, so it does not answer with it, as at `POST /v1/admin/complete` |

`MODEL_NOT_CONFIGURED`, `MODEL_BACKEND_UNAVAILABLE`, `MODEL_NONE_LOADED`,
`MODEL_BACKEND_FAILED` and `MODEL_UNRECORDED` are the orchestrator's codes,
registered with their status in its
[The tenant's model](orchestrator.md#the-tenants-model). The service route
answers them because it is the same gateway running the same procedure, and
means by each what the person's route means.
`MODEL_BACKEND_LIMITED` is registered in
[`protocol/types`](../protocol/types.md#error-handling).

`MODEL_UNAVAILABLE` is not answered here. It is
[`patterns/api-ai`](../patterns/api-ai.md)'s: a model a request names is on
an unhealthy provider. A request here names no model, and nothing runs in
place of the tenant's backend.

---

## Data Flow

### Asking the model unattended

1. A registered component holding `llm:chat` sends
   `POST /v1/model/complete` with its own registration token in the
   `Authorization` header, and a `ServiceCompletionRequest`: the
   `CompletionRequest` it would send a person's route, the `run` it works for
   and the `phase` of that run, where it works for one.
2. Once the gateway has read the body, it appends the completion's first
   entry through `POST /v1/model/audit`, in its own process, with the
   caller's token: action `model_complete`, the caller's `run` and `phase`,
   the `role`, the `scope`, the backend, and the model it will ask for or that
   the backend chooses. The orchestrator judges the token there
   ([Who may ask](#who-may-ask)). A refusal of the token is relayed as the
   orchestrator gave it, and nothing else happens.
3. It refuses a body that is not a `ServiceCompletionRequest`, with
   `INVALID_REQUEST`.
4. It finds the backend and the model as `POST /v1/admin/complete` finds
   them: the configuration chooses, the model is the one `roles` gives the
   request's `role`, else `model`, else the backend's choice
   ([`architecture/orchestrator`](orchestrator.md#the-tenants-model)). It
   refuses with the orchestrator's codes where it cannot.
5. It applies the destination gate before it sends anything, with the
   ceiling `GET /v1/model/ceiling` would answer for that backend and model
   ([A model is a destination](orchestrator.md#a-model-is-a-destination)).
6. It runs the completion on that backend, and nothing else in its place.
7. It appends the completion's second entry through `POST /v1/model/audit`:
   the model the backend reported running, or that it reported none, and
   how it ended, `ok`, `denied` or `failed`, with the code it ended with
   ([Recording what the model routes do](orchestrator.md#recording-what-the-model-routes-do)).
8. It appends the `Completion` record ([The Completion record](#the-completion-record)).
9. Only then does it answer: a `ServiceCompletionResponse` where the backend
   answered, or the refusal. A route that could not record in step 7 or 8
   answers `MODEL_UNRECORDED`, and discloses no answer.

### A person's completion

`POST /v1/admin/complete` runs as
[`architecture/orchestrator`](orchestrator.md#the-tenants-model) specifies.
The one thing this document adds is step 8 above: the gateway appends a
`Completion` record for it too, with `route` `admin`, so that every
completion the tenant's model runs has one record whichever route asked.

### A caller closes the request

Where the caller closes its connection before the answer, the gateway stops
the completion where the backend lets it, and records it as it records any
other ending: a second entry `failed`, and a `Completion` whose `ended` is
`cancelled`. A completion is never left with one entry.

---

## Design Principles

1. **The model service is the model gateway gaining a route** (owner
   decision). The tenant's architecture puts the model in one model service,
   and the CLI's model gateway is already where the tenant's model is chosen,
   run and recorded. Making the model service a component beside it would
   put a second runner, a second reader of the configuration and a second
   writer of completion records beside the first. Making it the gateway keeps
   one of each, and adds one route. The alternatives are recorded in
   [Known Gaps](#known-gaps).
2. **One capability asks a model.** `llm:chat` is already "the one capability
   a requester needs to ask a model, and no other is minted for that"
   ([`protocol/types`](../protocol/types.md#capability)). A person carries it
   through a role; a component declares it on its manifest. Nothing new is
   minted for the service route.
3. **Unattended work asks on the component's own registration.** Work that
   runs unattended is the service's own, never a person's
   ([`architecture/programme-service`](programme-service.md#who-may-do-what),
   rule 4). The caller is the component, recorded by its `identity_id`.
4. **The run is the caller's statement.** The service cannot see a run. It
   records the `run` and `phase` a caller states under the caller's identity,
   as it records the `scope` a caller states, and never treats either as more
   than that.
5. **Usage is what the backend reported.** Tokens and cost are taken from the
   backend's own answer, never estimated, and never computed from a price the
   service holds. A backend that reports none has its usage absent, never
   zero ([Usage and cost](#usage-and-cost)).
6. **No limit nobody set.** The service imposes no count, token cap or
   deadline of its own. A backend's own limit is relayed as the backend's
   ([Limits](#limits)).

---

## Who may ask

The token rules are [`protocol/identity`](../protocol/identity.md#the-pass)'s
and [Auth Middleware](orchestrator.md#auth-middleware)'s, and are not restated.
What this route admits:

1. **A registration token, and no other kind.** The route is a registered
   component's, outside `/v1/admin/`, so Auth Middleware step 6 admits a
   registration token and refuses an operator token and a channel token with
   `FORBIDDEN`. Step 5 refuses a pass with `PASS_AUDIENCE_MISMATCH` and an
   attestation token with `CREDENTIAL_REQUIRED`. The admin gateway's own
   registration token is refused with `FORBIDDEN`, as at every route but the
   three step 6 names for it.
2. **Whose `cap` names `llm:chat`.** A registration token carries what the
   component's signed manifest declares. A token that does not name it is
   refused with `FORBIDDEN`, judged at `POST /v1/model/audit` before anything
   runs.
3. **The same gate for every caller.** The ceiling is the backend's and the
   model's, as the orchestrator answers it. An agreement names no caller
   ([`patterns/scope`](../patterns/scope.md#model-providers)), so no caller is
   sent more than another. `restricted` and above go to no caller's
   completion.
4. **A `needs:` ceiling is not enforced here.** A programme's `needs:` bounds
   what an `agent:` instruction may do at the owners it writes through
   ([`schemas/programme.md`](../schemas/programme.md#needs-is-a-ceiling-on-an-agent-and-is-refused-beside-does)).
   Asking the model is what an `agent:` instruction is, so no `needs:` value
   adds or removes it. What bounds the model is the worker's `llm:chat` and the
   gate.

### What the model service requires of a work pass

Unattended work reaches the owners it writes through on a **work pass**
([`protocol/identity`](../protocol/identity.md#the-work-pass)). The model
service takes none, and relies on three things the work pass already is:

1. **It is never addressed to the orchestrator.** The orchestrator is the
   audience of no work pass and refuses one with `PASS_AUDIENCE_MISMATCH`
   ([`protocol/identity`](../protocol/identity.md#minting-a-work-pass),
   rule 7), and the model service is in its process. A worker that holds a
   work pass for its run presents it to the owners it writes through, and its
   own registration token here.
2. **The run it is minted for has the id execution records.** A work pass
   carries its `run`; the worker states the same id here as `run`, so that
   the model work of a run and the writes made on its passes join on one id.
3. **Its `cap` is not how a model is reached.** A work pass's `cap` needs no
   `llm:chat` for the worker to ask the model, and grants nothing here. If
   the model service becomes a component of its own (alternative B,
   [Known Gaps](#known-gaps)), this route would take a work pass instead of
   the registration token, and nothing else here changes.

---

## Usage and cost

Every completion that reaches the backend reports a `RunUsage`, the one
usage type a completion's record and a run's record share
([`protocol/types`](../protocol/types.md#runs)):

- **`prompt_tokens`, `completion_tokens` and `total_tokens`**, as the
  backend's own answer counts them. Each is absent where its answer counts
  none, and none is worked out from the others.
- **`cost`**, an amount and its currency, as the backend's own answer states
  it. Absent where it states none. The service holds no price, and a cost is
  never worked out from tokens.

A completion refused before it reached the backend has no usage. Absent
means not known, and is never read as zero: a run whose record sums its
completions' usage says its total is unknown wherever one completion's is
absent, and never presents a partial sum as the whole. Costs in two
currencies are not summed.

## Limits

- **The service sets none of its own.** It counts nothing against a caller,
  caps no completion's tokens, and puts no deadline on a completion. A caller
  that stops waiting closes the request ([A caller closes the request](#a-caller-closes-the-request)).
- **A backend's own limit is the backend's.** Where the backend refuses under
  its rate or quota limit, the service answers `MODEL_BACKEND_LIMITED`, with
  `retry_after` from the reset the backend reported, and absent where it
  reported none. It never invents a reset, and never runs another backend.
- **A per-caller budget is not specified.** A tenant cannot yet say how much
  of its model one component may use ([Known Gaps](#known-gaps)).

---

## The Completion record

A `Completion` is the record of one completion, whichever route asked it.
The gateway appends it once the completion has ended and its second audit
entry is appended, as one canonical JSON line in
`.weblisk/model-completions.jsonl` under the hub's root, beside
`.weblisk/model.json`. It is appended and never rewritten.

It carries who asked, for which run, what ran, how it ended and what it used,
and the ids of the completion's two audit entries. It never carries a prompt,
an answer or a key. The audit log is the one audit: a `Completion` adds the
usage an `AuditEntry` cannot carry in structure, and a reader checks it
against the two entries it names.

---

## Resources

The kinds a person sees here, in the form
[`schemas/resource.md`](../schemas/resource.md) defines. The model service is
the model gateway in the orchestrator's process, so the component that holds
a `completion` is the orchestrator, and the block names it as `owner`. The
records are kept in `.weblisk/model-completions.jsonl`, one line each, and
read at the uniform address
([`architecture/admin`](admin.md#resources-one-api-for-every-kind)), since no
route of this blueprint lists them.

The tenant's `model` configuration is a declared kind
([`schemas/kinds`](../schemas/kinds.md#declared-kinds)) and not a block here:
there is one per tenant, so it has no item identity for the uniform address to
name. It is read at `GET /v1/admin/model` with `admin:read` and set at
`PUT /v1/admin/model` with `admin:*`, each recorded as
[`architecture/orchestrator`](orchestrator.md#the-tenants-model) says.

```yaml
resources:
  - kind: completion
    owner: orchestrator
    type: Completion
    identity: {field: id, form: minted}
    label: id
    fields:
      - {name: id, access: read-only, present: text}
      - {name: route, access: read-only, present: choice}
      - {name: caller, access: read-only, present: text}
      - {name: run, access: read-only, present: reference, kind: run}
      - {name: phase, access: read-only, present: text}
      - {name: role, access: read-only, present: text}
      - {name: scope, access: read-only}
      - {name: provider, access: read-only, present: text}
      - {name: model, access: read-only, present: text}
      - {name: ended, access: read-only, present: choice}
      - {name: code, access: read-only, present: text}
      - {name: usage, access: read-only}
      - {name: started_at, access: read-only, present: instant}
      - {name: ended_at, access: read-only, present: instant}
      - {name: audit, access: read-only, present: list}
    operations:
      list: {capability: "admin:read", filters: [run, caller, route, ended]}
      get: {capability: "admin:read"}
    events: [created]
    relations: []
```

A `completion` is never updated or deleted: it is the record of something
that happened. Running a completion, on either route, creates one; no person
creates one by asking for it.

---

## Types

```yaml
types:
  ServiceCompletionRequest:
    description: The body of POST /v1/model/complete
    fields:
      request:
        name: Request
        type: CompletionRequest
        required: true
        description: "What a person's route would be sent (architecture/orchestrator). It names no backend and no model, and its scope is the highest scope of what the prompt carries, as the tenant reported it to the caller"
      run:
        name: Run
        type: string
        required: false
        description: "The id of the run the completion is for, as execution records it. The caller's statement. Absent where the caller works for no run"
      phase:
        name: Phase
        type: string
        required: false
        description: "The phase of that run, by its name in the definition. Only beside run"

  ServiceCompletionResponse:
    description: The answer of POST /v1/model/complete where the backend answered
    fields:
      completion:
        name: Completion
        type: string
        required: true
        description: "The id of the Completion record"
      response:
        name: Response
        type: CompletionResponse
        required: true
        description: "The answer, the backend that ran it, and the model its answer says ran, as POST /v1/admin/complete answers them"
      usage:
        name: Usage
        type: RunUsage
        required: true
        description: "What the completion used, as the backend reported it. Its members are absent where the backend reported none"

  Completion:
    description: The record of one completion the model gateway ran, on either route
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "A uid minted when the first audit entry is appended"
      route:
        name: Route
        type: string
        required: true
        description: "`service` for POST /v1/model/complete, `admin` for POST /v1/admin/complete"
        constraints:
          enum: [service, admin]
      caller:
        name: Caller
        type: string
        required: true
        description: "The identity id of the token that asked: the component's registration, or the person's"
      run:
        name: Run
        type: string
        required: false
        description: "The run the caller stated. Absent where it stated none, and on route admin"
      phase:
        name: Phase
        type: string
        required: false
        description: "The phase the caller stated"
      role:
        name: Role
        type: string
        required: false
        description: "The role the request stated"
      scope:
        name: Scope
        type: ScopeLevel
        required: false
        description: "The scope the request stated. Absent where it stated none, which the gate refused"
      provider:
        name: Provider
        type: string
        required: false
        description: "The backend the configuration named. Absent where the hub held no configuration"
      model:
        name: Model
        type: string
        required: false
        description: "The model the backend's answer says ran. Absent where it ran nothing or named none; never the model it was asked for"
      ended:
        name: Ended
        type: string
        required: true
        description: "`answered` where the backend answered; `refused` where the gate or the route refused it before it ran; `failed` where the backend failed, refused its model or refused under its limit; `cancelled` where the caller closed the request"
        constraints:
          enum: [answered, refused, failed, cancelled]
      code:
        name: Code
        type: string
        required: false
        description: "The code it ended with. Absent where it was answered"
      usage:
        name: Usage
        type: RunUsage
        required: false
        description: "Absent where nothing reached the backend"
      started_at:
        name: StartedAt
        type: timestamp
        required: true
        description: "The first audit entry's timestamp"
      ended_at:
        name: EndedAt
        type: timestamp
        required: true
        description: "The second audit entry's timestamp"
      audit:
        name: Audit
        type: "[]string"
        required: true
        description: "The ids of its two model_complete audit entries, first then second"
```

---

## Security

```yaml
security:
  trust_model:
    description: |
      The model service trusts the orchestrator's judgement of every token,
      and nothing about a token's shape. It trusts a caller's statement of
      the scope of its prompt and of the run it works for exactly as far as
      a statement goes: the gate applies the scope, and the run is recorded
      under the caller's identity as the caller's. It holds no key and no
      secret, and runs only a backend the orchestrator reports available.

  boundaries:
    - boundary: Component → Model Service. POST /v1/model/complete on the
        component's own registration token carrying llm:chat. No pass, no
        operator token, no channel token
    - boundary: Person → Model Service. Only POST /v1/admin/complete, through
        the admin gateway, as architecture/orchestrator specifies
    - boundary: Model Service → Orchestrator. In process, POST /v1/model/audit
        and POST /v1/admin/model/audit, with the token of the request it records
    - boundary: Model Service → backend. Only the backend the tenant's
        configuration names, behind the destination gate. A provider is a
        destination with a ceiling (patterns/scope)

  enforcement:
    - rule: One place chooses the backend
      mechanism: No request names a backend or a model, on either route, and
        one naming either is refused with INVALID_REQUEST
    - rule: Every completion is audited before it runs and when it ends
      mechanism: Two model_complete entries in the orchestrator's hash chain;
        a completion that cannot be recorded is not run, or not answered
    - rule: Nothing above a provider's ceiling leaves the tenant
      mechanism: The destination gate on request.scope before anything is
        sent; restricted and above are refused whatever the ceiling
    - rule: A component asks the model only by declaring that it does
      mechanism: llm:chat on its signed manifest, judged on its registration
        token at the first audit entry
    - rule: Nothing a model is sent or answers is kept
      mechanism: The audit entries and the Completion record carry no prompt,
        no answer and no key
```

---

## Implementation Notes

- The service route and the person's route are one procedure with two front
  doors. Write the procedure once; the routes differ only in the token they
  admit, the recording route they append through, and the body they read.
- Take usage from the backend's own answer: an HTTP backend's usage member,
  a command-line client's structured output. Where the backend's answer has
  no such member, leave usage absent. Never estimate tokens by counting
  characters.
- Take a reset time for `MODEL_BACKEND_LIMITED` from the backend's own answer,
  such as a `Retry-After` header or the reset a command-line client reports.
  Without one, send no `retry_after`.
- Keep `.weblisk/model-completions.jsonl` beside `.weblisk/model.json`. It is
  the tenant's record, not a cache: removing it loses what the tenant's model
  work used.
- A local model server is asked what it has loaded on every completion, on
  the service route as on the person's
  ([`architecture/orchestrator`](orchestrator.md#the-tenants-model)).

---

## Known Gaps

**No hub serves the service route yet.** The CLI's model gateway serves four
of the person's routes ([`architecture/orchestrator`](orchestrator.md#the-tenants-model),
the gap note), and not `POST /v1/model/complete`. Being `provided: platform`,
the route is not generated either, so a request to it is answered `404`, and a
caller reads that as not runnable ([Interfaces](#interfaces)). Closing it is
the CLI's: serve the route as this document specifies, record through
`POST /v1/model/audit`, and append a `Completion` for both routes.

**No hub serves a `Completion` at the uniform address yet.** The records'
`list` and `get` are read at the admin gateway's uniform address
([Resources](#resources)), and no hub serves either. Until one does, a person
reads what each completion did from the audit log's `model_complete` entries,
and a run's usage from its record.

**No per-caller budget.** A tenant cannot say how many tokens, or how much
money, one component may spend on its model in a window. The alternatives,
for the owner: a budget per component in the tenant's configuration,
enforced here, since every completion passes here; or a budget per programme
at the programme service, which would have to read usage back from here.
Neither is invented as a default.

**The model service is in the trust anchor's process.** Unattended model work
runs beside the orchestrator's keys, as a person's completions already do. The
alternatives, recorded for the owner:

- **B. A model component of its own, holding the whole model job.** The
  configuration, the backends, both completion routes, the agreements and the
  ceilings move to a registered component the CLI supplies, reached by a
  person through the admin gateway on a pass and by a component on a work
  pass. It takes the model out of the orchestrator's process, and
  it is the end state if the owner wants that. It moves
  `architecture/orchestrator`'s model surface, and it needs a component route for recording into the one audit
  log, which nothing specifies. The service route, the `Completion` record,
  the usage and the codes here would move unchanged; only the token rule in
  [Who may ask](#who-may-ask) would change.
- **C. A model component for services only, beside the gateway.** Rejected:
  two runners of one configuration, and two writers of the record of what the
  tenant's model did.

---

## Verification Checklist

- [ ] `POST /v1/model/complete` with a registration token whose `cap` names `llm:chat` and a valid `ServiceCompletionRequest` answers `200` with a `ServiceCompletionResponse` naming the backend the tenant's `ModelConfig` names ([Asking the model unattended](#asking-the-model-unattended))
- [ ] A registration token whose `cap` does not name `llm:chat` is refused with `FORBIDDEN`, and nothing is sent to the backend ([Who may ask](#who-may-ask) rule 2, [Error Handling](#error-handling))
- [ ] An operator token and a channel token are each refused with `FORBIDDEN`, and a pass with `PASS_AUDIENCE_MISMATCH` ([Who may ask](#who-may-ask) rule 1, [Error Handling](#error-handling))
- [ ] A `request` naming `provider` or `model` is refused with `INVALID_REQUEST`, and no backend is asked ([Error Handling](#error-handling), [Security](#security))
- [ ] A `request` with no `scope` is refused with `SCOPE_MISSING`, and one whose `scope` is `restricted` with `SCOPE_CEILING_EXCEEDED`, each carrying a `DestinationRefusal` and sending nothing ([Error Handling](#error-handling), [Asking the model unattended](#asking-the-model-unattended) step 5)
- [ ] Every completion on the service route appends exactly two `model_complete` entries through `POST /v1/model/audit`, the first before the gate, and the answer is sent only after the second ([Asking the model unattended](#asking-the-model-unattended))
- [ ] A completion whose first or second entry cannot be appended answers `MODEL_UNRECORDED` and discloses no answer ([Asking the model unattended](#asking-the-model-unattended) step 9, [Error Handling](#error-handling))
- [ ] Every completion on either route appends one `Completion` to `.weblisk/model-completions.jsonl`, naming its two audit entries, and none carries a prompt or an answer ([The Completion record](#the-completion-record), [A person's completion](#a-persons-completion))
- [ ] `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens` and `usage.cost` are each absent where the backend's answer reported none, and are never `0` in its place ([Usage and cost](#usage-and-cost))
- [ ] A backend refusing under its own limit is answered `MODEL_BACKEND_LIMITED`, with `retry_after` only where the backend reported a reset, and no other backend is run ([Limits](#limits), [Error Handling](#error-handling))
- [ ] `response.model` is the model the backend's answer says ran, and is absent where it says none ([Asking the model unattended](#asking-the-model-unattended), [Types](#types))
- [ ] The `run` and `phase` a caller states are recorded on its first audit entry and on its `Completion`, under the caller's `identity_id` ([Asking the model unattended](#asking-the-model-unattended) step 2, [Design Principles](#design-principles) 4)
- [ ] A caller that closes the request leaves a second `model_complete` entry `failed` and a `Completion` whose `ended` is `cancelled` ([A caller closes the request](#a-caller-closes-the-request))
