<!-- blueprint
type: protocol
name: types
version: 2.0.0
requires: []
platform: any
tier: free
-->

# Weblisk Protocol Types

Canonical type definitions for the Weblisk Agent Protocol v1. Every
implementation — regardless of language — MUST use these exact field
names, types, and JSON serialization keys. These types define the
universal contract between agents, orchestrators, and tools.

## Overview

All types are defined in language-agnostic notation. JSON is the
wire format. Implementations MUST serialize to and deserialize from
JSON using the exact field names shown in the `json` column.

## Conventions

- All timestamps are Unix epoch seconds (`int64`)
- All IDs are 32-character hex strings (16 random bytes)
- All signatures are base64url-encoded ML-DSA-65 signatures (3309 bytes)
- All public keys are base64url-encoded ML-DSA-65 public keys (1952 bytes)
- Optional fields MAY be omitted from JSON when empty/null
- Unknown fields MUST be ignored (forward compatibility)

---

## Dependencies

```yaml
requires: []
  # protocol/types is the root type registry — it has no dependencies.
  # All other blueprints depend on this file.
```

---

## Errors

All error responses use a structured format. Simple error strings
(`{"error": "message"}`) are still valid for backward compatibility,
but implementations SHOULD use the full `ErrorResponse` when
category and retry information are available.

### ErrorResponse

```yaml
types:
  ErrorResponse:
    fields:
      error:
        name: Error
        type: string
        required: true
        description: "Human-readable error message"
      code:
        name: Code
        type: string
        required: false
        description: "Machine-readable error code (e.g., `AGENT_UNREACHABLE`, `INVALID_INPUT`)"
      category:
        name: Category
        type: string
        required: false
        description: "`\"transient\"`, `\"permanent\"`, or `\"partial\"`"
      retryable:
        name: Retryable
        type: bool
        required: false
        description: "Whether the caller SHOULD retry this request"
      retry_after:
        name: RetryAfter
        type: int
        required: false
        description: "Seconds to wait before retrying (present when `retryable` is true)"
      detail:
        name: Detail
        type: map
        required: false
        description: "Additional structured context (varies by error)"
```

**Categories:**
- `transient` — Temporary failure; retry is safe. Examples: network timeout, agent overloaded, upstream 503.
- `permanent` — Will not succeed on retry. Examples: invalid input, capability not available, unknown action.
- `partial` — Request partially succeeded. `detail` SHOULD include `completed` and `failed` sub-results.

**Standard error codes** are declared once, in [## Error Handling](#error-handling)
below, with their HTTP status, category and retryability.


**Enforcement error codes** (produced by `architecture/enforcement`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `ENFORCEMENT_QUARANTINED` | 403 | permanent | Agent is quarantined — all operations blocked |
| `ENFORCEMENT_POLICY_DENY` | 403 | permanent | Policy evaluation returned deny |
| `ENFORCEMENT_MISSING_INTENT` | 403 | permanent | Safety intent required but not filed |
| `ENFORCEMENT_CAPABILITY_MISMATCH` | 403 | permanent | Agent lacks declared capability for operation |
| `ENFORCEMENT_SCOPE_VIOLATION` | 403 | permanent | Resource scope exceeds agent operational scope |
| `ENFORCEMENT_SCOPE_LEAKAGE` | 403 | permanent | Payload scope exceeds the classification of a target `patterns/scope` gives no ceiling. A target with a ceiling refuses with `SCOPE_CEILING_EXCEEDED` |
| `ENFORCEMENT_BLOCKED_TARGET` | 403 | permanent | Target is on the blocked endpoint list, or is the address of a model provider and the caller's manifest does not declare `model:route` ([`architecture/enforcement`](../architecture/enforcement.md#external-proxy)) |
| `ENFORCEMENT_DATA_CONTRACT_VIOLATION` | 403 | permanent | Operation targets resources outside agent's declared data contract |
| `ENFORCEMENT_OUTPUT_CONTRACT_VIOLATION` | 403 | permanent | Response contains fields outside declared output contract |
| `ENFORCEMENT_OUTPUT_SCOPE_EXCEEDED` | 403 | permanent | Response scope exceeds agent's operational scope |
| `ENFORCEMENT_CALLER_SCOPE_EXCEEDED` | 403 | permanent | Response scope exceeds what the caller can receive |
| `ENFORCEMENT_CONSENT_REQUIRED` | 403 | permanent | Operation involves subject data requiring consent that is not active |

**Contract error codes** (produced by `patterns/contract`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `CONTRACT_VIOLATION` | 400 | permanent | Contract terms violated |
| `CONTRACT_UNKNOWN` | 404 | permanent | Referenced contract not found |
| `SCHEMA_INVALID` | 400 | permanent | Data does not match contract schema |

**Federation error codes** (produced by `protocol/federation`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `PEER_UNTRUSTED` | 403 | permanent | Federation peer not in trust store |
| `TRUST_EXPIRED` | 403 | permanent | Peer trust relationship has expired |
| `JURISDICTION_DENIED` | 403 | permanent | Data cannot cross jurisdiction boundary |
| `DATA_BOUNDARY_VIOLATION` | 400 | permanent | Payload violates federation data contract |

**Safety error codes** (produced by `patterns/safety`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `APPROVAL_TIMEOUT` | 408 | transient | Approval request timed out |

**Policy error codes** (produced by `patterns/policy`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `POLICY_DENIED` | 403 | permanent | Policy evaluation denied the operation |
| `POLICY_ESCALATED` | 202 | transient | Policy requires approval escalation before proceeding |
| `POLICY_NOT_FOUND` | 404 | permanent | Referenced policy does not exist |
| `POLICY_EVAL_FAILED` | 500 | transient | Policy engine encountered an internal error during evaluation |
| `POLICY_CONTEXT_INCOMPLETE` | 400 | permanent | Required policy context fields are missing — fail-closed deny |
| `POLICY_INVALID_DEFINITION` | 400 | permanent | Policy definition does not pass schema validation |
| `POLICY_LIFECYCLE_INVALID` | 409 | permanent | Invalid policy state transition (e.g., modifying an archived policy) |
| `POLICY_CONFLICT` | 409 | permanent | Conflicting active policies detected for the same scope |

**Operator token codes** (produced by the orchestrator's judgement of an
operator token, `architecture/admin`'s `token-status-on-use`, on its own routes
and at the token exchange, `POST /v1/token/exchange`, whose refusal the admin
gateway answers its client with):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `CREDENTIAL_REQUIRED` | 401 | permanent | The token is not an operator token carrying `cid` where one is required |
| `OPERATOR_UNKNOWN` | 401 | permanent | The hub records no operator of the token's `sub` |
| `OPERATOR_NOT_APPROVED` | 403 | permanent | The operator is registered and pending |
| `OPERATOR_REVOKED` | 401 | permanent | The operator was removed |
| `CREDENTIAL_UNKNOWN` | 401 | permanent | The hub holds no credential with the token's `cid` |
| `CREDENTIAL_OPERATOR_MISMATCH` | 401 | permanent | The credential the token's `cid` names is held by an operator other than its `sub` |
| `CREDENTIAL_REVOKED` | 401 | permanent | The credential was revoked |
| `CREDENTIAL_EXPIRED` | 401 | permanent | The credential's attestation has passed its `not_after` |

`architecture/admin` says when the orchestrator answers each and what a client
does next. The exchange can also refuse a token with `INVALID_SIGNATURE` or
`TOKEN_EXPIRED`, for a token whose signature does not verify or whose `exp`
has passed, and those two are registered with their status in
[Error Handling](#error-handling). The admin gateway, refusing a request
because the exchange refused the person's token, answers with the code
`TokenExchangeResponse.code` names and the status this table or Error Handling
gives it.

**Pass codes** (produced by a component that a person's request reaches,
[`protocol/identity`](identity.md#the-pass)):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `PASS_REQUIRED` | 401 | permanent | A component other than the orchestrator and the admin gateway was presented an operator token, which no holder may present there ([`protocol/identity`](identity.md#the-pass), rule 4). A person's request goes to the tenant's admin gateway, which carries it on a pass, and a tool call to the MCP surface on a credential [`patterns/auth-oauth`](../patterns/auth-oauth.md) issued for it ([`architecture/mcp`](../architecture/mcp.md)). Logged as a security event |
| `PASS_AUDIENCE_MISMATCH` | 401 | permanent | A pass was presented to a component its `aud` does not name, the orchestrator included. Logged as a security event |

**Destination codes** (produced by the destination gate of `patterns/scope`,
and answered by every sender it binds):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `SCOPE_MISSING` | 400 | permanent | An entity has no scope declaration where one is required: `reject_unscoped` is enabled, or it would be sent to a destination. At a destination, `detail` is a `DestinationRefusal` |
| `SCOPE_CEILING_EXCEEDED` | 403 | permanent | Content would be sent to a destination whose ceiling is below its scope. `detail` is a `DestinationRefusal` |

What the gate refuses, and what a `DestinationRefusal` carries, are
`patterns/scope`'s.

**Identity error codes** (produced by `protocol/identity`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `KEY_DECODE_ERROR` | 400 | permanent | Cryptographic key could not be decoded or parsed |

**Common error codes** (reusable across agents and components):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `INVALID_INPUT` | 400 | permanent | Request input fails validation (malformed, missing required fields, constraint violation) |
| `STORAGE_ERROR` | 500 | transient | Persistence layer operation failed (read, write, or query) |
| `INVALID_STATE` | 409 | permanent | Operation is invalid for the current state of the target resource |
| `TARGET_NOT_FOUND` | 404 | permanent | Dispatch target agent is not registered or unreachable |
| `DISPATCH_TIMEOUT` | 408 | transient | Task dispatch to target agent timed out before acknowledgement |
| `DISPATCH_ERROR` | 502 | transient | Task dispatch to target agent failed (transport or protocol error) |
| `PAYLOAD_TOO_LARGE` | 413 | permanent | Request payload exceeds the maximum allowed size |
| `DELIVERY_FAILED` | 502 | transient | Event or notification delivery to target failed after retries |
| `CAPABILITY_DENIED` | 403 | permanent | Peer or agent lacks the required capability grant |
| `BEHAVIORAL_CHANGE` | 403 | permanent | Entity behavior has deviated from its declared or historical pattern |
| `RETENTION_EXPIRED` | 410 | permanent | Requested data has been purged per retention policy |

#### Error Code Conventions

Error codes follow the convention: `DOMAIN_SPECIFIC_ERROR`. Domain
prefixes (`ENFORCEMENT_`, `CONTRACT_`, `POLICY_`, etc.) indicate the
originating subsystem.

**Registry vs. local codes:**
- All protocol-level, enforcement, policy, contract, federation,
  safety, operator token, destination, identity, and common codes are
  registered in this central table. These codes may appear in any
  component.
- Agent-local codes (specific to a single agent's domain logic) are
  defined in the agent's own blueprint. Agent-local codes MUST NOT
  collide with registered codes and SHOULD use a descriptive name
  that indicates the agent domain (e.g., `INVALID_SCHEDULE` in the
  cron agent, `HARD_BOUNCE` in the email-send agent).
- When an agent-local code is used by two or more unrelated agents,
  it SHOULD be promoted to the common codes table in this registry.
- A blueprint that reports or cites the code another component refuses
  with does not use that code in this sense, and the code stays local to
  the component that refuses with it. `schemas/programme` reports
  `CONTENT_RECORDS_REPOSITORY_REQUIRED` for what install did not create,
  because it is the code the content service would refuse the first write
  with, and `patterns/scope` and `schemas/programme` cite
  `CONTENT_SCOPE_LOWERED`, `CONTENT_SCOPE_UNDECLARED` and
  `CONTENT_CUSTODY_CEILING_EXCEEDED` as `architecture/content`'s refusals. Each
  is registered once, with its status, in `architecture/content`'s Error
  Handling, and each of those blueprints points there.

### AgentManifest

Describes an agent's identity, capabilities, and interface contract.
Returned by `POST /v1/describe` and sent during registration.

```yaml
types:
  AgentManifest:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Agent identifier (lowercase, no spaces)"
      type:
        name: Type
        type: string
        required: false
        description: "`\"domain\"` (domain controller), `\"agent\"` (work agent, default), or `\"infrastructure\"` (system-level: task, workflow, lifecycle)"
      version:
        name: Version
        type: string
        required: true
        description: "Semver version of the agent"
      protocol_version:
        name: ProtocolVersion
        type: string
        required: false
        description: "Protocol version this agent implements (default: `\"1\"`)"
      description:
        name: Description
        type: string
        required: true
        description: "Human-readable purpose"
      url:
        name: URL
        type: string
        required: true
        description: "Agent's HTTP base URL"
      public_key:
        name: PublicKey
        type: string
        required: true
        description: "Base64url-encoded ML-DSA-65 public key (1952 bytes)"
      capabilities:
        name: Capabilities
        type: "[]Capability"
        required: true
        description: "What this agent can do"
      inputs:
        name: Inputs
        type: "[]IOSpec"
        required: false
        description: "Expected input parameters"
      outputs:
        name: Outputs
        type: "[]IOSpec"
        required: false
        description: "What this agent produces"
      collaborators:
        name: Collaborators
        type: "[]string"
        required: false
        description: "Agent names this agent works with"
      approval:
        name: Approval
        type: string
        required: false
        description: "`\"required\"` or `\"auto\"` (default: `\"required\"`)"
      required_agents:
        name: RequiredAgents
        type: "[]string"
        required: false
        description: "Agents this domain needs (domain type only)"
      workflows:
        name: Workflows
        type: "[]string"
        required: false
        description: "Workflow names supported (domain type only)"
      max_concurrent:
        name: MaxConcurrent
        type: int
        required: false
        description: "Max concurrent executions (default: 1 — serial execution; 0 means unlimited)"
      publishes:
        name: Publishes
        type: "[]string"
        required: false
        description: "Namespace patterns this agent may publish to (e.g., `[\"workflow.*\"]`). The orchestrator enforces exclusive ownership — no two agents may claim the same namespace. See [spec.md — Namespace Control](spec.md#namespace-control)."
      subscriptions:
        name: Subscriptions
        type: "[]Subscription"
        required: false
        description: "Event subscription declarations. Each entry specifies a topic pattern, optional consumer group, scope, and concurrency limit. See [spec.md — Event Scoping](spec.md#event-scoping)."
      pass_routes:
        name: PassRoutes
        type: "[]PassRoute"
        required: false
        description: "Every route at which this component admits a person's request on a pass, with every capability each requires. Absent or empty: the admin gateway carries no person's request here. See [PassRoute](#passroute)"
```

### Capability

A single thing an agent can do, with optional resource scoping.

```yaml
types:
  Capability:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Capability identifier (e.g., `file:read`)"
      resources:
        name: Resources
        type: "[]string"
        required: false
        description: "Glob patterns scoping the capability"
```

**One home, one owner.** This section is the one home of every capability
name, and each bullet names its one **owner** in brackets: the unit whose
blueprint says what the capability admits and which judges it. A name with two
owners or none is a fault. An owner is named as a unit: `orchestrator`
([`architecture/orchestrator`](../architecture/orchestrator.md), with
[`architecture/admin`](../architecture/admin.md) its administrative surface),
`content`, `fabric`, `enforcement`, `gateway` and `domain` (each its
`architecture/` blueprint), and `programme` (`agents/programme`). `integrations`
and `telemetry` own names here before their blueprints are written, so those
names guard no route yet; they are listed now because a registration naming an
unlisted capability is refused ([`protocol/spec`](spec.md#post-v1register)).

**Standard capabilities:**
- `file:read` (enforcement) — read files (resources: glob patterns)
- `file:write` (enforcement) — write/modify files
- `llm:chat` (orchestrator) — use a language model. A person's request needs it to ask the tenant's model for a completion at `POST /v1/admin/complete` ([`architecture/orchestrator`](../architecture/orchestrator.md#administrative-endpoints)), and `architecture/admin`'s roles table says which roles carry it. It is the one capability a requester needs to ask a model, and no other is minted for that: the model capabilities below are for recording an agreement (`model:attest`) and for serving the tenant's model route (`model:route`)
- `agent:message` (orchestrator) — communicate with other agents
- `workflow:execute` (domain) — execute multi-agent workflows (domain controllers)
- `http:get` (enforcement) — make external HTTP requests
- `http:send` (enforcement) — make outbound HTTP requests
- `http:receive` (gateway) — receive inbound HTTP requests
- `database:read` (enforcement) — read from data store
- `database:write` (enforcement) — write to data store
- `event:observe` (orchestrator) — observe all events for a topic regardless of scope
- `realtime:publish` (gateway) — publish to real-time channels

**Content capabilities:**
- `content:read` (content) — read entries and list a content repository, read the proposals made against it, and read its change log
- `content:write` (content) — create, modify and remove entries directly. *Person only*
- `content:propose` (content) — stage a change to one entry for a person to decide. Writes nothing
- `content:decide` (content) — apply or reject a proposed change, and, beside `content:declare`, declare a repository's `self_decision_ceiling` or `scope_floor`. *Person only*
- `content:describe` (content) — read a repository's custody class, attestations and derived ceiling, its remotes, and its change log's head, and have that log sealed
- `content:declare` (content) — bring a store under governance. Adopting one that already holds bytes needs it alone only where the census does not report `keeps_history` and the declaration carries neither `scope_floor` nor `self_decision_ceiling`; adopting a store that keeps history must carry a `scope_floor`, so it also needs `content:decide`. Establishing a new store also needs `content:establish`
- `content:establish` (content) — create a store and declare it. Required in addition to `content:declare` for `disposition: establish`; adoption does not need it
- `content:reconcile` (content) — run custody reconciliation on a shared repository
- `content:replicate` (content) — declare a remote of a repository, and retire one. Declaring one also needs `content:connect`. *Person only*
- `content:connect` (content) — bind an integration to a destination outside the tenant's store, a remote's among them. It creates nothing: the credential is the integration's, and the content service holds none. Required in addition to `content:replicate` to declare a remote. *Person only*
- `content:declassify` (content) — lower a path's recorded scope. It guards no route yet: [`architecture/content`](../architecture/content.md) refuses every lowering until the tenant's approval queue can route such a request to a second person. *Person only*

*Person only* marks a capability that no service and no agent may hold.
[`patterns/principal-identity`](../patterns/principal-identity.md) keeps it out
of a service subject's grant and every token minted for one, and out of an
agent's authorisation (`service-subject-constraints` and `agent-delegation`).
[`protocol/spec`](spec.md) refuses a registration whose manifest declares one,
because a registered component is a service. Each refusal is
`CAPABILITY_PERSON_ONLY` ([Error Handling](#error-handling)). `content:propose` is
separate from `content:write` for the reason `fabric:attest` is separate from
`fabric:observe` below: agents propose and people apply, and one capability
covering both would make that unenforceable at the tenant. What each does to a
request is [`architecture/content`](../architecture/content.md#proposals).
`content:replicate` and `content:connect` are two capabilities so that sending
a repository outside the tenant takes two grants: a remote with no integration
bound reaches nothing, and an integration bound to no remote is sent nothing
([`architecture/content`](../architecture/content.md#who-may-declare-a-remote),
which also says whom the two grants separate today).

**Model capabilities:**
- `model:attest` (orchestrator) — record and withdraw an agreement attestation, which raises what a model provider may be sent ([`patterns/scope`](../patterns/scope.md#model-providers)). *Person only*
- `model:route` (enforcement) — send to a model provider's endpoint as the tenant's model route ([`patterns/scope`](../patterns/scope.md#the-gate)). Declared by a component that serves `patterns/api-ai`'s endpoints, and by nothing else. `POST /v1/admin/complete` is the orchestrator's own route and is served by no component, so nothing declares it there ([`patterns/scope`](../patterns/scope.md#the-gate), Where the tenant applies it)

`model:route` is how [`architecture/enforcement`](../architecture/enforcement.md#external-proxy)'s
external boundary tells the model route from a call made around it. It
admits a call to a provider's address and nothing past the destination gate:
the boundary still refuses whatever is above the provider's ceiling. Any
component may declare it on its signed manifest today, as it may any service
capability, because a registration is not yet an enrolment
([`protocol/spec`](spec.md#post-v1register)).

`model:attest` is person only because it decides what leaves the tenant for a
party outside it. It is not in the `admin` family, so `admin:*` does not carry
it, and a role carries it only where
[`architecture/admin`](../architecture/admin.md)'s roles table names it: today
only `admin` does, so every admin holds it. What keeps it apart from `admin:*`
is therefore that a token narrowed by `cap`, or a pass exchanged for a route
that needs `admin:*`, carries `admin:*` without it, and that a future role may
administer without attesting agreements. No service could raise a ceiling
through `admin:*` in any case: `/v1/admin/*` admits a person's operator token
at the orchestrator and a pass exchanged for one at any other provider, and
nothing else, whichever component serves the route
([`architecture/admin`](../architecture/admin.md#contracts),
`admin-gateway-authorization`).

**Fabric capabilities:**
- `fabric:read` (fabric) — read relationships, coverage, impact, lineage and the ledger projection
- `fabric:produce` (fabric) — state a producer's full current view for one partition
- `fabric:observe` (fabric) — report one relationship incrementally
- `fabric:attest` (fabric) — assert, judge or re-anchor a relationship as a person. *Person only*

`fabric:attest` is separate from `fabric:observe` for the reason
`architecture/fabric` is built around: only a person reaches `confirmed`. One
capability covering both would make that rule unenforceable at the boundary
where it has to hold, and for the same reason it is *person only*: a service or
an agent holding it would reach `confirmed` without a person. A person holds it,
and `fabric:read`, only through a role that
[`architecture/admin`](../architecture/admin.md)'s roles table gives it to, as
for every person-only capability. `fabric:produce` and `fabric:observe` are a
producer's, which is a registered component.

**Programme capabilities:**
- `programme:read` (programme) — read a programme's installed operations and what they have produced
- `programme:install` (programme) — install a programme's operations at a scope
- `programme:operate` (programme) — pause, resume, run and reschedule an installed operation
- `programme:switch` (programme) — decide whether an operation's runs reach people: mute, unmute, and who hears them. *Person only*

Which act needs which is `agents/programme`'s, under Who May Switch What. The
programme service declares the first three, because a grant to a caller is the
intersection of what it holds and what the serving manifest declares, and
checks `programme:switch` without ever holding it, as `content` does its own
person-only capabilities.

**Integration capabilities:**
- `integration:read` (integrations) — read the tenant's integrations: provider, account, method, scopes, owner, purposes, expiry and status, and never a secret
- `integration:manage` (integrations) — make, bind to a declared need, re-purpose, rotate and revoke an integration. *Person only*
- `integration:use` (integrations) — have an integration act for a need the holder's blueprint declares: a token, a signature or verdict, or a relayed call, and never the secret

An integration is one authenticated link to one account at one provider, and
`integrations` is the one unit that holds an outside credential.
`integration:use` is a component's, declared for a need its blueprint states,
and no role carries it. A person delegates only their own account, and an
integration they delegated lapses when they leave or lose the grant it was made
under. `content:connect` binds an integration to a content destination and
makes none.

**Telemetry capabilities:**
- `telemetry:read` (telemetry) — read the tenant's runtime: metrics, logs, traces, events, probe results and rule state
- `telemetry:push` (telemetry) — push a component's own signals to telemetry over OTLP, under a pass. Reads nothing

`telemetry:read` is not person only: an agent whose blueprint declares a read
of telemetry holds it within that declaration. A person holds it only through
a role, `admin` alone by default, and which roles carry it changes only through
the change cycle, never by a grant at run time. `telemetry:push` is declared by
every component that reports, and no role carries it.

**Action and admission capabilities:**
- `action:invoke` (orchestrator) — invoke an operator action a component's blueprint declares, where the action names no capability of that component's own family. *Person only*
- `scope:admit` (orchestrator) — admit the operational scope a component declares, the highest classification it may reach. *Person only*

Neither guards a route yet: no blueprint declares an operator action, and
`AgentManifest` has no operational scope. Both are listed so that each act has
one name before it is specified.

**Outside the `admin` family.** `telemetry:read`, `action:invoke` and
`scope:admit`, like `model:attest`, are not in the `admin` family, so `admin:*`
does not carry them, and a person holds one only where
[`architecture/admin`](../architecture/admin.md#operator-roles)'s roles table
names it. Adding one to the family would change what `admin:*` means to every
rule that names it. `programme:switch`, `integration:manage`, `action:invoke`
and `scope:admit` are person only because each is a decision a person makes and
answers for: what reaches people, which outside account the tenant acts as,
an operational control, and what data a component may reach.

A capability name is `family:verb`. A component that invents one is refused at
registration with `INVALID_REQUEST` — which is correct, and is why a component's
capabilities belong in this list before that component is built. The content
service was generated asking for `content.read`, with a dot and no declared
family, and the orchestrator rejected it exactly as it should.

**Administrative capabilities:**
- `admin:read` (orchestrator) — read administrative state: overview, agents, domains, workflows, operators
- `admin:approve` (orchestrator) — act on the approval queue
- `admin:strategy` (orchestrator) — create, amend and retire strategies
- `admin:audit` (orchestrator) — read the full audit log, including export
- `admin:*` (orchestrator) — every capability in the `admin` family

Administration is expressed in capabilities like everything else, and an
operator's **role is a bundle of them** — `architecture/admin` defines each
bundle in its Operator Roles table, `auditor` being `viewer` plus `admin:audit`,
and so on. That keeps
administration one authority system rather than a second one running alongside
the first: whatever asks to administer a component presents capabilities, and
the component checks them the same way it checks `agent:message`. On every
`/v1/admin/*` route, those capabilities arrive on a person's operator token
at the orchestrator and on a pass exchanged for one at any other component
([`protocol/identity`](identity.md#the-pass)), and on no other kind of token.
The orchestrator judges what the person may use: on its own routes as each
request arrives, and at the exchange for a pass.

`admin:*` is the only wildcard capability name. It exists because a full-access
role has to be nameable, and it denotes the whole family rather than a resource
glob — resource scoping stays in `resources`, as for every other capability.

> **Gap.** `architecture/admin`'s `admin` role relies on `admin:*` for operator
> management, agent deregistration and federation approval, none of which is
> separately nameable here. A deployment that wants an operator who may approve
> federation but not deregister agents cannot express it. A route another
> provider serves with the minimum `admin` is reached on a pass carrying
> `admin:*`, which that provider alone accepts and which reaches no route of
> the orchestrator's ([`protocol/identity`](identity.md#the-pass)), so the
> missing names cost precision, not containment. Naming those is
> `architecture/admin`'s to do, and this list will follow it — inventing the
> names here would put the wrong document in charge of what administration
> means.

**Exchange capability:**
- `token:exchange` (orchestrator) — have the orchestrator exchange the operator token a person has just presented for a pass addressed to one component ([`protocol/identity`](identity.md#the-pass); `architecture/orchestrator`, `token-exchange`). The admin gateway declares it, and no other blueprint does. No role carries it

`token:exchange` is what the admin gateway's registration declares, and the
only capability it declares: the gateway reads the service directory, which
any registration may, and exchanges, and holds no standing access to data
([`architecture/admin`](../architecture/admin.md#contracts),
`admin-gateway-authorization`). Nothing stops another component declaring it
on its signed manifest today, as it may declare any service capability,
because a registration is not yet an enrolment
([`protocol/spec`](spec.md#post-v1register)). That is a gap, and what it
admits is this. The exchange takes a live operator token and nothing else, and
no component but the admin gateway, and from it the orchestrator, is presented
one, so such a holder needs a person's token it has stolen. With one, it can have the token exchanged for a
pass to any component, carrying everything that person may use there:
`content:write`, `content:decide` and `fabric:attest` included, which no route
of the orchestrator's gives, and without the admin gateway's network controls,
its operator IP allowlist among them. So a stolen operator token reaches
further through a rogue `token:exchange` holder than at the orchestrator.
Admitting `token:exchange` only for the registration the tenant declares as
its admin gateway closes it, and waits on the tenant being able to declare
that component ([`architecture/orchestrator`](../architecture/orchestrator.md#what-the-directory-attests-and-what-it-does-not),
the gap that the declaration has nowhere to live).

### PassRoute

A route at which a component admits a person's request on a pass, and every
capability that request needs there. A component's manifest declares one for
each such route (`AgentManifest.pass_routes`), and the orchestrator republishes
them in its directory entry (`ServiceEntry.pass_routes`).

```yaml
types:
  PassRoute:
    fields:
      method:
        name: Method
        type: string
        required: true
        description: "HTTP method, in upper case"
      path:
        name: Path
        type: string
        required: true
        description: "The route's path as the component's blueprint writes it. A `{name}` segment matches any one non-empty path segment; nothing else is a pattern. No two of one manifest's pass routes may match one request, and registration refuses a manifest whose do, as it refuses one naming a capability this document does not list (architecture/orchestrator, Registration Flow)"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: true
        description: "Every capability the route requires on every request, all of them together"
      body:
        name: Body
        type: "[]BodyRequirement"
        required: false
        description: "Each capability the route requires because of what a request's body carries, beside `capabilities`"
```

### BodyRequirement

```yaml
types:
  BodyRequirement:
    fields:
      field:
        name: Field
        type: string
        required: true
        description: "A member at the top level of the request's JSON body"
      equals:
        name: Equals
        type: string
        required: false
        description: "The string value of `field` that calls for `capabilities`. Absent: `field` being present and not null calls for them"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: true
        description: "The capabilities the request requires, beside the route's own, when its body meets this"
```

**The admin gateway reads these, and nothing else, to carry a person's
request to a component other than the orchestrator.** It is generated from
`architecture/admin` alone, which cannot require every blueprint whose
component may serve people, so what each such route needs reaches it at
runtime, from the directory. A request goes to the one directory entry whose
`pass_routes` declare its method and path, on a pass whose scope names that
route's `capabilities` and those of each `BodyRequirement` its body meets, and
nothing more
([`architecture/admin`](../architecture/admin.md#contracts),
`admin-gateway-authorization`).

**Each entry is its blueprint's own statement of the route, and no wider.** A
component declares a route here only where its blueprint specifies both that
route and that it accepts a pass for it, with every capability that blueprint
requires for it. The component still judges each request against its
blueprint: a route declared with less than that blueprint requires is
refused at the component with `FORBIDDEN` for want of the capability the pass
did not carry, and one declared with more carries the excess to that
component alone, which is the pass's only audience. A pass route may name a
person-only capability, because it states what the component checks on a
person's pass, never what it holds: registration's refusal of a person-only
capability reads `capabilities` alone, and nothing in `pass_routes` reaches
the component's own token. Like any manifest field
it is the registrant's claim, and a registration is not yet an enrolment
([`protocol/spec`](spec.md#post-v1register)): what bounds a claimed route is
that the gateway never sends a person's request to a route two entries
declare, to a route of the orchestrator's own, or to an address
`architecture/orchestrator`'s Presenting a credential to a component does not
allow.

### IOSpec

Describes an input or output parameter.

```yaml
types:
  IOSpec:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Parameter name"
      type:
        name: Type
        type: string
        required: true
        description: "Data type: `file_list`, `json`, `text`"
      description:
        name: Description
        type: string
        required: true
        description: "Human-readable description"
```

---

## Workflows

Types used by domain controllers to define and execute multi-phase,
multi-agent workflows. [`patterns/workflow`](../patterns/workflow.md)
is the authoritative source for workflow declaration format, reference
expression grammar, execution engine, error strategies, and state
machine. See `architecture/domain.md` for the domain controller
specification that consumes these types.

### WorkflowDefinition

Declared in domain blueprint files. Describes a multi-phase process
that a domain controller can execute.

```yaml
types:
  WorkflowDefinition:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Workflow identifier (lowercase, hyphens)"
      description:
        name: Description
        type: string
        required: true
        description: "What this workflow does"
      trigger:
        name: Trigger
        type: string
        required: true
        description: "Task action that invokes this workflow"
      phases:
        name: Phases
        type: "[]WorkflowPhase"
        required: true
        description: "Ordered execution steps"
```

### WorkflowPhase

A single step in a workflow. Each phase dispatches to one agent.

```yaml
types:
  WorkflowPhase:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Phase identifier (unique within workflow)"
      agent:
        name: Agent
        type: string
        required: true
        description: "Target agent name"
      action:
        name: Action
        type: string
        required: true
        description: "`HandleMessage` action to invoke"
      input:
        name: Input
        type: map
        required: false
        description: "Input mapping — reference expressions resolve at runtime (see [Reference Expression Syntax](../architecture/domain.md#reference-expression-syntax))"
      output:
        name: Output
        type: string
        required: false
        description: "Key name under which this phase's result is stored"
      depends_on:
        name: DependsOn
        type: "[]string"
        required: false
        description: "Phase names that must complete first. Phases without dependencies MAY run in parallel"
      timeout:
        name: Timeout
        type: int
        required: false
        description: "Phase timeout in seconds (default: 300)"
      approval:
        name: Approval
        type: string
        required: false
        description: "`\"required\"` or `\"auto\"` (default: `\"auto\"`)"
      on_error:
        name: OnError
        type: string
        required: false
        description: "`\"fail\"` (default), `\"skip\"`, or `\"retry\"`"
      max_retries:
        name: MaxRetries
        type: int
        required: false
        description: "Retry count when `on_error` = `\"retry\"` (default: 0)"
      condition:
        name: Condition
        type: string
        required: false
        description: "Expression evaluated at runtime; phase is skipped if false"
```

**Input reference syntax:** See [Reference Expression Syntax](../architecture/domain.md#reference-expression-syntax) for the full grammar, including nested access, array indexing (`[0]`), array expansion (`[*]`), and resolution rules.

### WorkflowExecution

Runtime state of a workflow in progress or completed.

```yaml
types:
  WorkflowExecution:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique execution identifier"
      workflow_name:
        name: WorkflowName
        type: string
        required: true
        description: "Which workflow is executing"
      domain_name:
        name: DomainName
        type: string
        required: true
        description: "Executing domain controller"
      task_id:
        name: TaskID
        type: string
        required: true
        description: "Originating task ID"
      status:
        name: Status
        type: string
        required: true
        description: "`pending`, `running`, `completed`, `failed`"
      phases:
        name: Phases
        type: "[]PhaseResult"
        required: true
        description: "Results per phase"
      started_at:
        name: StartedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      completed_at:
        name: CompletedAt
        type: int64
        required: false
        description: "Unix epoch seconds"
```

### PhaseResult

Tracks the outcome of a single workflow phase.

```yaml
types:
  PhaseResult:
    fields:
      phase_name:
        name: PhaseName
        type: string
        required: true
        description: "Phase identifier"
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Agent that executed this phase"
      status:
        name: Status
        type: string
        required: true
        description: "`pending`, `running`, `completed`, `failed`, `skipped`"
      output:
        name: Output
        type: map
        required: false
        description: "Phase output data (referenced by subsequent phases)"
      started_at:
        name: StartedAt
        type: int64
        required: false
        description: "Unix epoch seconds"
      completed_at:
        name: CompletedAt
        type: int64
        required: false
        description: "Unix epoch seconds"
      error:
        name: Error
        type: string
        required: false
        description: "Error message if failed"
      retries:
        name: Retries
        type: int
        required: false
        description: "Number of retry attempts"
```

---

## Strategy

A strategy declares a business objective with measurable targets.
Multiple strategies run in parallel. The orchestrator decomposes
each into prioritized tasks assigned to domain agents.

### Strategy

```yaml
types:
  Strategy:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique hex identifier"
      name:
        name: Name
        type: string
        required: true
        description: "Strategy name"
      objective:
        name: Objective
        type: string
        required: true
        description: "What this strategy aims to achieve"
      targets:
        name: Targets
        type: "[]StrategyTarget"
        required: true
        description: "Measurable goals"
      priority:
        name: Priority
        type: int
        required: true
        description: "1 = highest priority"
      status:
        name: Status
        type: string
        required: true
        description: "`active`, `paused`, `completed`"
      created_at:
        name: CreatedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      updated_at:
        name: UpdatedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      metadata:
        name: Metadata
        type: map
        required: false
        description: "Arbitrary key-value data"
```

### StrategyTarget

```yaml
types:
  StrategyTarget:
    fields:
      metric:
        name: Metric
        type: string
        required: true
        description: "What is being measured"
      current:
        name: Current
        type: float64
        required: true
        description: "Current value"
      goal:
        name: Goal
        type: float64
        required: true
        description: "Target value"
      deadline:
        name: Deadline
        type: string
        required: true
        description: "ISO 8601 date (human-facing planning horizon, not a protocol timestamp)"
      unit:
        name: Unit
        type: string
        required: true
        description: "Unit of measurement"
      progress:
        name: Progress
        type: float64
        required: true
        description: "0.0 to 1.0"
      measurement_window:
        name: MeasurementWindow
        type: int
        required: false
        description: "Evaluation window in seconds (default: 86400)"
```

---

## Entity Context

The entity being optimized — a company, person, or project.
This grounds every agent's decisions in business reality.

### EntityContext

```yaml
types:
  EntityContext:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Entity name"
      type:
        name: Type
        type: string
        required: true
        description: "`company`, `person`, `project`, `site`"
      industry:
        name: Industry
        type: string
        required: true
        description: "Industry/sector"
      description:
        name: Description
        type: string
        required: true
        description: "What the entity does"
      positioning:
        name: Positioning
        type: string
        required: true
        description: "Market positioning statement"
      audiences:
        name: Audiences
        type: "[]Audience"
        required: false
        description: "Target audiences"
      competitors:
        name: Competitors
        type: "[]Competitor"
        required: false
        description: "Known competitors"
      keywords:
        name: Keywords
        type: "[]string"
        required: false
        description: "Core keywords/topics"
      tone:
        name: Tone
        type: string
        required: false
        description: "Brand voice (e.g., `professional`, `casual`)"
      geography:
        name: Geography
        type: string
        required: false
        description: "Primary geography"
      assets:
        name: Assets
        type: "[]Asset"
        required: false
        description: "Known digital assets"
      metadata:
        name: Metadata
        type: map
        required: false
        description: "Arbitrary key-value data"
```

### Audience

```yaml
types:
  Audience:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Audience segment name"
      description:
        name: Description
        type: string
        required: true
        description: "Who they are"
      pain_points:
        name: PainPoints
        type: "[]string"
        required: false
        description: "Their challenges"
      keywords:
        name: Keywords
        type: "[]string"
        required: false
        description: "Terms they search for"
```

### Competitor

```yaml
types:
  Competitor:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Competitor name"
      url:
        name: URL
        type: string
        required: false
        description: "Competitor URL"
      notes:
        name: Notes
        type: string
        required: false
        description: "Competitive notes"
```

### Asset

```yaml
types:
  Asset:
    fields:
      path:
        name: Path
        type: string
        required: true
        description: "File path or URL"
      type:
        name: Type
        type: string
        required: true
        description: "Asset type"
      purpose:
        name: Purpose
        type: string
        required: false
        description: "What this asset is for"
```

---

## Task Protocol

### TaskRequest

Sent to an agent's `POST /v1/execute` endpoint by the Task Agent,
or dispatched as part of a workflow phase.

```yaml
types:
  TaskRequest:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique task identifier"
      from:
        name: From
        type: string
        required: true
        description: "Who initiated (`user` or agent name)"
      action:
        name: Action
        type: string
        required: true
        description: "What to do (`execute`, custom actions)"
      payload:
        name: Payload
        type: map
        required: true
        description: "Task-specific data"
      context:
        name: Context
        type: TaskContext
        required: true
        description: "Runtime context"
      strategy_id:
        name: StrategyID
        type: string
        required: false
        description: "Associated strategy"
      token:
        name: Token
        type: string
        required: true
        description: "Auth token"
      signature:
        name: Signature
        type: string
        required: false
        description: "ML-DSA-65 signature of payload (3309 bytes, base64url-encoded)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### TaskContext

Runtime context provided with every task execution.

```yaml
types:
  TaskContext:
    fields:
      workspace_root:
        name: WorkspaceRoot
        type: string
        required: true
        description: "Absolute path to project root"
      services:
        name: Services
        type: "[]ServiceEntry"
        required: true
        description: "Current service directory"
      entity:
        name: Entity
        type: EntityContext
        required: false
        description: "Entity being optimized"
      config:
        name: Config
        type: map
        required: false
        description: "Additional configuration"
      trace_id:
        name: TraceID
        type: string
        required: false
        description: "Correlation ID for distributed tracing (propagated through all downstream calls)"
```

### TaskResult

Returned by an agent after task execution.

```yaml
types:
  TaskResult:
    fields:
      task_id:
        name: TaskID
        type: string
        required: true
        description: "Matches request ID"
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Which agent produced this"
      status:
        name: Status
        type: string
        required: true
        description: "`success`, `failed`, `pending_approval`"
      summary:
        name: Summary
        type: string
        required: true
        description: "Human-readable summary"
      changes:
        name: Changes
        type: "[]ProposedChange"
        required: false
        description: "File modifications"
      observations:
        name: Observations
        type: "[]Observation"
        required: false
        description: "Measurements taken"
      recommendations:
        name: Recommendations
        type: "[]Recommendation"
        required: false
        description: "Suggested actions"
      metrics:
        name: Metrics
        type: map
        required: false
        description: "Execution metrics"
      signature:
        name: Signature
        type: string
        required: false
        description: "ML-DSA-65 signature (3309 bytes, base64url-encoded)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### ProposedChange

A file modification proposed by an agent.

```yaml
types:
  ProposedChange:
    fields:
      path:
        name: Path
        type: string
        required: true
        description: "Relative file path"
      action:
        name: Action
        type: string
        required: true
        description: "`create`, `modify`, `delete`"
      original:
        name: Original
        type: string
        required: false
        description: "Original file content"
      modified:
        name: Modified
        type: string
        required: false
        description: "Modified file content"
      diffs:
        name: Diffs
        type: "[]ChangeDiff"
        required: false
        description: "Element-level changes"
```

### ChangeDiff

```yaml
types:
  ChangeDiff:
    fields:
      element:
        name: Element
        type: string
        required: true
        description: "What changed (e.g., `title`)"
      before:
        name: Before
        type: string
        required: true
        description: "Previous value"
      after:
        name: After
        type: string
        required: true
        description: "New value"
      reason:
        name: Reason
        type: string
        required: true
        description: "Why this change was made"
```

---

## Observations

Structured measurements captured every time an agent runs.

### Observation

```yaml
types:
  Observation:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique identifier"
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Which agent observed"
      target:
        name: Target
        type: string
        required: true
        description: "What was observed (file path, URL)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      measurements:
        name: Measurements
        type: "map[string]float64"
        required: true
        description: "Numeric measurements"
      findings:
        name: Findings
        type: "[]Finding"
        required: false
        description: "Issues discovered"
      content_hash:
        name: ContentHash
        type: string
        required: false
        description: "Hash of observed content"
      strategy_id:
        name: StrategyID
        type: string
        required: false
        description: "Associated strategy"
```

### Finding

```yaml
types:
  Finding:
    fields:
      rule_id:
        name: RuleID
        type: string
        required: true
        description: "Which rule triggered"
      severity:
        name: Severity
        type: string
        required: true
        description: "`critical`, `warning`, `info`"
      element:
        name: Element
        type: string
        required: true
        description: "What element is affected"
      current:
        name: Current
        type: string
        required: true
        description: "Current value"
      expected:
        name: Expected
        type: string
        required: true
        description: "Expected value"
      message:
        name: Message
        type: string
        required: true
        description: "Human-readable description"
      fixable:
        name: Fixable
        type: bool
        required: true
        description: "Whether auto-fix is available"
      fix:
        name: Fix
        type: string
        required: false
        description: "Suggested fix value"
```

---

## Recommendations

### Recommendation

```yaml
types:
  Recommendation:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique identifier"
      observation_id:
        name: ObservationID
        type: string
        required: true
        description: "Source observation"
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Recommending agent"
      strategy_id:
        name: StrategyID
        type: string
        required: false
        description: "Associated strategy"
      target:
        name: Target
        type: string
        required: true
        description: "Target file/resource"
      action:
        name: Action
        type: string
        required: true
        description: "What to do"
      element:
        name: Element
        type: string
        required: true
        description: "Target element"
      current:
        name: Current
        type: string
        required: true
        description: "Current value"
      proposed:
        name: Proposed
        type: string
        required: true
        description: "Proposed value"
      reason:
        name: Reason
        type: string
        required: true
        description: Justification
      priority:
        name: Priority
        type: string
        required: true
        description: "`critical`, `high`, `medium`, `low`"
      impact:
        name: Impact
        type: float64
        required: true
        description: "Estimated impact score"
      status:
        name: Status
        type: string
        required: true
        description: "`pending`, `accepted`, `rejected`, `applied`"
      created_at:
        name: CreatedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      resolved_at:
        name: ResolvedAt
        type: int64
        required: false
        description: "Unix epoch seconds"
```

---

## Approvals

### ApprovalRequest

Submitted by a user or external system to approve or reject one or
more pending recommendations or workflow phases.

```yaml
types:
  ApprovalRequest:
    fields:
      recommendation_ids:
        name: RecommendationIDs
        type: "[]string"
        required: true
        description: "IDs of recommendations to resolve"
      decision:
        name: Decision
        type: string
        required: true
        description: "`\"accept\"` or `\"reject\"`"
      reason:
        name: Reason
        type: string
        required: false
        description: "Human-provided justification (required for rejections)"
      token:
        name: Token
        type: string
        required: true
        description: "Auth token"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### ApprovalResponse

```yaml
types:
  ApprovalResponse:
    fields:
      updated:
        name: Updated
        type: int
        required: true
        description: "Count of recommendations updated"
      results:
        name: Results
        type: "[]ApprovalResult"
        required: true
        description: "Per-recommendation outcome"
```

### ApprovalResult

```yaml
types:
  ApprovalResult:
    fields:
      recommendation_id:
        name: RecommendationID
        type: string
        required: true
        description: "Which recommendation"
      previous_status:
        name: PreviousStatus
        type: string
        required: true
        description: "Status before this action"
      new_status:
        name: NewStatus
        type: string
        required: true
        description: "Status after this action"
      error:
        name: Error
        type: string
        required: false
        description: "Error if this one failed (e.g., already resolved)"
```

---

## Feedback

### Feedback

```yaml
types:
  Feedback:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique identifier"
      recommendation_id:
        name: RecommendationID
        type: string
        required: true
        description: "Which recommendation"
      type:
        name: Type
        type: string
        required: true
        description: "`metric`, `user`, `automated`"
      signal:
        name: Signal
        type: string
        required: true
        description: "`positive`, `negative`, `neutral`"
      detail:
        name: Detail
        type: string
        required: true
        description: "What happened"
      metric_before:
        name: MetricBefore
        type: float64
        required: false
        description: "Metric value before"
      metric_after:
        name: MetricAfter
        type: float64
        required: false
        description: "Metric value after"
      metric_name:
        name: MetricName
        type: string
        required: false
        description: "Which metric"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

---

## Agent Metrics

### AgentMetrics

```yaml
types:
  AgentMetrics:
    fields:
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Agent identifier"
      total_observations:
        name: TotalObservations
        type: int
        required: true
        description: "Cumulative count"
      total_findings:
        name: TotalFindings
        type: int
        required: true
        description: "Cumulative count"
      total_recommendations:
        name: TotalRecommendations
        type: int
        required: true
        description: "Cumulative count"
      adoption_rate:
        name: AdoptionRate
        type: float64
        required: true
        description: "% of accepted recommendations"
      accuracy:
        name: Accuracy
        type: float64
        required: true
        description: "% of correct findings"
      impact_score:
        name: ImpactScore
        type: float64
        required: true
        description: "Cumulative impact"
      false_positive_rate:
        name: FalsePositiveRate
        type: float64
        required: true
        description: "% of false positives"
```

---

## Messaging

### AgentMessage

Direct agent-to-agent or orchestrator-to-agent message.

```yaml
types:
  AgentMessage:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Message identifier"
      from:
        name: From
        type: string
        required: true
        description: "Sender agent name"
      to:
        name: To
        type: string
        required: true
        description: "Recipient agent name"
      type:
        name: Type
        type: string
        required: true
        description: "`request` or `response`"
      action:
        name: Action
        type: string
        required: true
        description: "Message action name"
      payload:
        name: Payload
        type: map
        required: true
        description: "Message data"
      token:
        name: Token
        type: string
        required: false
        description: "Auth or channel token"
      signature:
        name: Signature
        type: string
        required: false
        description: "ML-DSA-65 signature (3309 bytes, base64url-encoded)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      trace_id:
        name: TraceID
        type: string
        required: false
        description: "Correlation ID (propagated from TaskContext)"
```

**Signature covers:** `canonicalize({from, to, action, payload})` per
[RFC 8785 (JCS)](https://www.rfc-editor.org/rfc/rfc8785)

---

## Service Directory

### ServiceEntry

```yaml
types:
  ServiceEntry:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Agent name"
      url:
        name: URL
        type: string
        required: true
        description: "Agent base URL"
      public_key:
        name: PublicKey
        type: string
        required: true
        description: "Base64url-encoded ML-DSA-65 public key (1952 bytes)"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: true
        description: "Capability names"
      status:
        name: Status
        type: string
        required: true
        description: "`online`, `offline`, `degraded`"
      address_provenance:
        name: AddressProvenance
        type: string
        required: false
        description: "How the orchestrator came to hold `url`: `self-asserted` (a registrant claimed it and nothing confirmed it), `declared` (it matches the address the tenant declared for this component), `verified` (declared, and the registered key answered there). Absent means `self-asserted`."
      pass_routes:
        name: PassRoutes
        type: "[]PassRoute"
        required: false
        description: "The `pass_routes` this component's manifest declared, as its registration recorded them. Absent or empty: no person's request is carried here. See [PassRoute](#passroute)"
```

**`url` is what a registrant claimed; `address_provenance` is how much that is worth.**
The registration signature proves a key holder asserted an address. It proves
nothing about who chose the address or what answers at it, so a directory that
carries the address and not its provenance publishes an authentic statement
that reads as an authorised one.

An orchestrator that omits `address_provenance` has not verified, and a consumer MUST
read the absence as `self-asserted` rather than as a tenant too old to say.
There is no value meaning "unknown" for the same reason: an orchestrator always
knows which of the three it did.

What a client may do with each is
[`architecture/orchestrator`](../architecture/orchestrator.md), "Presenting a
credential to a component" — the one home for that rule, because the
orchestrator is what publishes the fact the rule reads.

### ServiceDirectory

```yaml
types:
  ServiceDirectory:
    fields:
      services:
        name: Services
        type: "[]ServiceEntry"
        required: true
        description: "All registered agents"
      routing_table:
        name: RoutingTable
        type: "map[string][]RouteEntry"
        required: true
        description: "Topic pattern → list of subscriber routes. Used by the framework to resolve event delivery targets locally."
      namespaces:
        name: Namespaces
        type: "map[string]string"
        required: true
        description: "Namespace → owning agent name. Used to validate publish rights."
      updated_at:
        name: UpdatedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      signature:
        name: Signature
        type: string
        required: false
        description: "Reserved for the orchestrator's signature over the directory, which has no signing input yet. Nothing verifies it, so no reader takes it for a check (protocol/spec, the gap under POST /v1/services)"
```

---

## Registration

### RegisterRequest

```yaml
types:
  RegisterRequest:
    fields:
      manifest:
        name: Manifest
        type: AgentManifest
        required: true
        description: "Agent's full manifest"
      signature:
        name: Signature
        type: string
        required: true
        description: "ML-DSA-65 signature of JSON(manifest) (3309 bytes, base64url-encoded)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### RegisterResponse

```yaml
types:
  RegisterResponse:
    fields:
      agent_id:
        name: AgentID
        type: string
        required: true
        description: "Assigned unique identifier"
      token:
        name: Token
        type: string
        required: true
        description: "Auth token (WLT format)"
      expires_at:
        name: ExpiresAt
        type: int64
        required: true
        description: "Token expiry (Unix epoch)"
      services:
        name: Services
        type: ServiceDirectory
        required: true
        description: "Current service directory"
      orchestrator:
        name: Orchestrator
        type: OrchestratorInfo
        required: true
        description: "Orchestrator info"
      protocol_version:
        name: ProtocolVersion
        type: string
        required: true
        description: "Negotiated protocol version (e.g., `\"1\"`)"
```

### OrchestratorInfo

```yaml
types:
  OrchestratorInfo:
    fields:
      url:
        name: URL
        type: string
        required: true
        description: "Orchestrator base URL"
      public_key:
        name: PublicKey
        type: string
        required: true
        description: "Base64url-encoded ML-DSA-65 public key (1952 bytes)"
      version:
        name: Version
        type: string
        required: true
        description: "Orchestrator software version"
      supported_versions:
        name: SupportedVersions
        type: "[]string"
        required: true
        description: "Protocol versions this orchestrator supports (e.g., `[\"1\"]`)"
```

**Version negotiation:** On registration, the orchestrator reads the
agent's `manifest.protocol_version` (default `"1"` if omitted). If the
orchestrator supports that version, registration succeeds and
`RegisterResponse.protocol_version` confirms the negotiated version.
If the requested version is not in `supported_versions`, the
orchestrator rejects with 400 and error code `UNSUPPORTED_VERSION`.

---

## Channels

### ChannelRequest

```yaml
types:
  ChannelRequest:
    fields:
      from_agent:
        name: FromAgent
        type: string
        required: true
        description: "Requesting agent name"
      to_agent:
        name: ToAgent
        type: string
        required: true
        description: "Target agent name"
      purpose:
        name: Purpose
        type: string
        required: true
        description: "Why the channel is needed"
      token:
        name: Token
        type: string
        required: true
        description: "Requestor's auth token"
      signature:
        name: Signature
        type: string
        required: true
        description: "ML-DSA-65 signature over `canonicalize({from_agent, to_agent, purpose})` (3309 bytes, base64url-encoded)"
```

### ChannelGrant

```yaml
types:
  ChannelGrant:
    fields:
      channel_id:
        name: ChannelID
        type: string
        required: true
        description: "Unique channel identifier"
      from_agent:
        name: FromAgent
        type: string
        required: true
        description: "Requesting agent"
      to_agent:
        name: ToAgent
        type: string
        required: true
        description: "Target agent"
      target_url:
        name: TargetURL
        type: string
        required: true
        description: "Target agent's URL"
      target_pub_key:
        name: TargetPubKey
        type: string
        required: true
        description: "Target's public key"
      channel_token:
        name: ChannelToken
        type: string
        required: true
        description: "Scoped channel token"
      expires_at:
        name: ExpiresAt
        type: int64
        required: true
        description: "Expiry (Unix epoch)"
      signature:
        name: Signature
        type: string
        required: true
        description: "Orchestrator signature"
```

### ChannelEntry

Stored record of an active channel in the orchestrator's channel registry.

```yaml
types:
  ChannelEntry:
    fields:
      channel_id:
        name: ChannelID
        type: string
        required: true
        description: "Unique channel identifier"
      from_agent:
        name: FromAgent
        type: string
        required: true
        description: "Requesting agent name"
      to_agent:
        name: ToAgent
        type: string
        required: true
        description: "Target agent name"
      purpose:
        name: Purpose
        type: string
        required: true
        description: "Why the channel was created"
      token:
        name: Token
        type: string
        required: true
        description: "Scoped channel token"
      created_at:
        name: CreatedAt
        type: int64
        required: true
        description: "Unix epoch of creation"
      expires_at:
        name: ExpiresAt
        type: int64
        required: true
        description: "Unix epoch of expiry"
```

---

## Health

### HealthStatus

```yaml
types:
  HealthStatus:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Component name"
      status:
        name: Status
        type: string
        required: true
        description: "`healthy`, `degraded`, `unhealthy`"
      version:
        name: Version
        type: string
        required: true
        description: "Component version"
      uptime:
        name: Uptime
        type: int64
        required: true
        description: "Seconds since start"
      checks:
        name: Checks
        type: map
        required: false
        description: "Per-subsystem health: subsystem name → `ok`, `degraded` or `failed`. A component that names a failing subsystem says WHERE it is unwell; one that reports only `status` says that it is"
      metrics:
        name: Metrics
        type: map
        required: false
        description: "Component-specific metrics"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

The component's own name is `name` and its age is `uptime`. Neither is
`component` nor `uptime_seconds`: those were bound by
[`architecture/observability`](../architecture/observability.md) from this type
for a while, and since this type never had them, a generated orchestrator
emitted the observability names, satisfied observability's assertion, and failed
`L1-01` against this definition. **This table is the authority and every other
blueprint binds the names in it.**

---

## Audit

### Operator

A person admitted to administer this tenant. An operator is always a person:
its credential signs only after its person's own act (`architecture/admin`,
Where the second factor is), and its role may carry a capability marked
*person only* ([Capability](#capability)). A service is never registered as
one. An admin approving a registration vouches that its subject is a person,
and the first operator is whoever presents the bootstrap secret. A service
reaches a tenant as a registered component ([`protocol/spec`](spec.md),
`POST /v1/register`).

Declared here because `architecture/orchestrator` binds it and
`architecture/admin` specifies its lifecycle — and until now no blueprint
defined it, so every implementation inferred its shape from the `fields_used`
list of whoever bound it.

```yaml
types:
  Operator:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Unique within the tenant. Lowercase letters, digits, dash and underscore, starting with a letter"
      public_key:
        name: PublicKey
        type: string
        required: true
        description: "Base64url-encoded ML-DSA-65 identity public key — an operator holds no password. It verifies registration and the attestations of the operator's credentials; tokens are minted with a credential, never with this key (`architecture/admin`). Replaced only by a change of identity key signed by this key and the new one"
      identity_id:
        name: IdentityID
        type: string
        required: true
        description: "The operator's identity id at this tenant: the fingerprint of the identity key its registration recorded, kept across every change of identity key. What tokens, credentials and records name the operator by, never the name. Never reused"
      retired_keys:
        name: RetiredKeys
        type: "[]RetiredKey"
        required: false
        description: "Identity keys this operator held before a change of identity key, oldest first, each with when it was retired. None is accepted again as any operator's identity key or credential, the operator's own included. A verifier that is not the hub reads them to check an attestation made before a change, and only for what was recorded before that key's retired_at"
      role:
        name: Role
        type: OperatorRole
        required: true
        description: "Determines capabilities. Capabilities are derived from the role and never stored per operator"
      status:
        name: Status
        type: OperatorStatus
        required: true
        description: "Whether this operator may obtain a token"
      created_at:
        name: CreatedAt
        type: int64
        required: true
        description: "Unix epoch seconds when the record was written"
      last_seen:
        name: LastSeen
        type: int64
        required: false
        description: "Unix epoch seconds of the most recent token issued to this operator"
```

### RetiredKey

An identity key an operator held before a change of identity key
(`architecture/admin`, Changing an identity key), and when the change took
it out of use.

```yaml
types:
  RetiredKey:
    fields:
      public_key:
        name: PublicKey
        type: string
        required: true
        description: "Base64url-encoded ML-DSA-65 identity public key the operator held"
      retired_at:
        name: RetiredAt
        type: int64
        required: true
        description: "Unix epoch seconds of the change that retired it. No attestation it signed vouches for anything recorded at or after this time, because the change revoked every credential it attested"
```

### OperatorRole

The four roles an operator may hold. Which capabilities each carries is
[`architecture/admin`](../architecture/admin.md#operator-roles)'s roles table,
and only that table: these values name the roles and do not restate it.

```yaml
types:
  OperatorRole:
    kind: enum
    base: string
    values:
      - value: viewer
        description: "Reads. The capabilities it carries are architecture/admin's roles table's"
      - value: auditor
        description: "Reads, and the full audit trail. The capabilities it carries are architecture/admin's roles table's"
      - value: operator
        description: "Day-to-day operations. The capabilities it carries are architecture/admin's roles table's"
      - value: admin
        description: "Full administration. The capabilities it carries are architecture/admin's roles table's"
```

`operator` was missing from this enum while `architecture/admin` named it in
both its roles table and the role column of every `operator+` endpoint. A
generated orchestrator follows the enum, so it produced three roles — and
`admin:approve` and `admin:strategy`, defined immediately above, ended up
granted to no role at all. The capability list and the enum have to be read
together: a capability no value of this enum carries is unreachable, and
nothing reports that.

### OperatorStatus

```yaml
types:
  OperatorStatus:
    kind: enum
    base: string
    values:
      - value: pending
        description: "Registered and awaiting an existing admin. No token is issued"
      - value: approved
        description: "May obtain a token"
      - value: revoked
        description: "Retained for the audit trail. No token is issued, and the name is not reusable"
```

### TokenExchangeRequest

What the admin gateway sends the orchestrator to have the operator token a
person has just presented exchanged for a pass addressed to one component
(`POST /v1/token/exchange`, `architecture/orchestrator`;
[`protocol/identity`](identity.md#the-pass)). Its fields are OAuth 2.0 Token
Exchange's (RFC 8693 §2.1) where it has one. The gateway authenticates with
its own registration token, in the `Authorization` header and nowhere else, so
the token exchanged travels in this body under a name the orchestrator never
reads as a caller's token.

```yaml
types:
  TokenExchangeRequest:
    fields:
      subject_token:
        name: SubjectToken
        type: string
        required: true
        description: "The operator token a person presented to the admin gateway in the request it is carrying, exactly as it arrived. Never the caller's own token, and never read as one"
      audience:
        name: Audience
        type: string
        required: true
        description: "The identity id of the one component the pass is for: the fingerprint of the public key that component's directory entry carries (ServiceEntry.public_key)"
      scope:
        name: Scope
        type: "[]string"
        required: true
        description: "The capabilities the request the gateway is carrying needs at that component, by the names the Capability list gives them, admin:* included"
```

### TokenExchangeResponse

What the orchestrator answers the admin gateway about the token it was asked
to exchange (`POST /v1/token/exchange`, `architecture/orchestrator`). Every
answer about the person's token is a 200 carrying this, so a status other
than 200 only ever judged the gateway's own request.

```yaml
types:
  TokenExchangeResponse:
    fields:
      issued:
        name: Issued
        type: bool
        required: true
        description: "True when a pass was minted"
      code:
        name: Code
        type: string
        required: false
        description: "Present when issued is false: FORBIDDEN where the person may use none of the capabilities scope names, and otherwise the code the orchestrator refuses that token with on its own routes, one of INVALID_SIGNATURE and TOKEN_EXPIRED (Error Handling) or an operator token code (Errors) — CREDENTIAL_REQUIRED, OPERATOR_UNKNOWN, OPERATOR_NOT_APPROVED, OPERATOR_REVOKED, CREDENTIAL_UNKNOWN, CREDENTIAL_OPERATOR_MISMATCH, CREDENTIAL_REVOKED or CREDENTIAL_EXPIRED. Each is registered here with its HTTP status"
      pass:
        name: Pass
        type: string
        required: false
        description: "Present when issued: the pass, a WLT of type pass addressed to the audience (protocol/identity, The pass)"
      expires_at:
        name: ExpiresAt
        type: int64
        required: false
        description: "Present when issued: the pass's exp, no more than 30 seconds after it was minted"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: false
        description: "Present when issued: the capabilities the pass carries, which are those scope named that the person may use now"
```

### AuditEntry

```yaml
types:
  AuditEntry:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique identifier"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      actor:
        name: Actor
        type: string
        required: true
        description: "Who performed the action"
      via:
        name: Via
        type: string
        required: false
        description: "Where a pass carried the request, the identity id of the gateway that obtained it, the pass's act.identity_id (protocol/identity, The pass). Absent, and omitted from the canonical JSON, otherwise"
      action:
        name: Action
        type: string
        required: true
        description: "Action type (see below)"
      target:
        name: Target
        type: string
        required: true
        description: "Affected resource"
      detail:
        name: Detail
        type: string
        required: true
        description: "Human-readable description"
      status:
        name: Status
        type: string
        required: true
        description: "`ok`, `denied`, `failed`"
      previous_hash:
        name: PreviousHash
        type: string
        required: true
        description: "SHA-256 hex digest of the previous entry's canonical JSON bytes; `\"0000...0000\"` (64 zeros) for the first entry — see [storage.md — Hash Chain Integrity](../architecture/storage.md#hash-chain-integrity)"
```

**Action types:** `register`, `deregister`, `channel`, `message`,
`event`, `namespace_grant`, `namespace_release`, and the model routes'
`model_set`, `model_complete`, `model_agreement_record` and
`model_agreement_withdraw`. The orchestrator's
[Audit Actions](../architecture/orchestrator.md#audit-actions) table says what
each one it writes records

---

## Events

Types used by the HTTP-based pub/sub event system. Events are the
primary coordination mechanism between agents. See
[spec.md — Event Publishing](spec.md#event-publishing-framework-behavior)
for the delivery protocol and
[spec.md — Event Scoping](spec.md#event-scoping) for scope semantics.

### EventEnvelope

The standard wrapper for all events delivered via `POST /v1/event`.

```yaml
types:
  EventEnvelope:
    fields:
      event_id:
        name: EventID
        type: string
        required: true
        description: "Globally unique event identifier (UUID v7 recommended — time-sortable)"
      topic:
        name: Topic
        type: string
        required: true
        description: "Dot-separated topic name (e.g., `workflow.completed`)"
      source:
        name: Source
        type: string
        required: true
        description: "Name of the publishing agent"
      scope:
        name: Scope
        type: string
        required: true
        description: "Target agent name, or `\"*\"` for global delivery"
      correlation_id:
        name: CorrelationID
        type: string
        required: false
        description: "Links all events in a single execution chain (e.g., one workflow run)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "Distributed trace context (propagated through all downstream operations)"
      version:
        name: Version
        type: string
        required: true
        description: "Schema version of the payload"
      payload:
        name: Payload
        type: map
        required: true
        description: "Event-specific data, typed per topic"
      token:
        name: Token
        type: string
        required: false
        description: "Auth token for delivery verification"
```

### Subscription

Declared in the agent manifest. Each entry registers interest in a
topic pattern with scope and concurrency controls.

```yaml
types:
  Subscription:
    fields:
      pattern:
        name: Pattern
        type: string
        required: true
        description: "Topic or wildcard pattern (supports `*` for single segment, `#` for multi-segment)"
      group:
        name: Group
        type: string
        required: false
        description: "Consumer group name. Events are load-balanced within a group. Defaults to agent name."
      scope:
        name: Scope
        type: string
        required: false
        description: "`\"self\"` (default), `\"*\"` (requires `event:observe`), or a specific agent name"
      max_concurrent:
        name: MaxConcurrent
        type: int
        required: false
        description: "Max parallel event processing for this subscription (default: 1)"
```

### RouteEntry

A single entry in the routing table. Represents one subscriber for a
topic pattern.

```yaml
types:
  RouteEntry:
    fields:
      agent:
        name: Agent
        type: string
        required: true
        description: "Subscriber agent name"
      url:
        name: URL
        type: string
        required: true
        description: "Subscriber's event endpoint (agent URL + `/v1/event`)"
      group:
        name: Group
        type: string
        required: false
        description: "Consumer group name"
      scope:
        name: Scope
        type: string
        required: true
        description: "Scope filter for this subscriber"
```

### DeadLetterEntry

An event that could not be delivered after all retry attempts.

```yaml
types:
  DeadLetterEntry:
    fields:
      original_event:
        name: OriginalEvent
        type: EventEnvelope
        required: true
        description: "The event that failed delivery"
      failure_reason:
        name: FailureReason
        type: string
        required: true
        description: "Error category (`HANDLER_ERROR`, `UNREACHABLE`, `TIMEOUT`, `REJECTED`)"
      last_error:
        name: LastError
        type: string
        required: true
        description: "Last error message from delivery attempt"
      attempts:
        name: Attempts
        type: int
        required: true
        description: "Total delivery attempts"
      first_attempt:
        name: FirstAttempt
        type: int64
        required: true
        description: "Unix epoch seconds of first attempt"
      last_attempt:
        name: LastAttempt
        type: int64
        required: true
        description: "Unix epoch seconds of final attempt"
      subscriber:
        name: Subscriber
        type: string
        required: true
        description: "Name of the subscriber that could not receive"
```

---

## Protocol Paths

All paths are prefixed with `/v1`.

| Path | Method | Auth | Component | Purpose |
|------|--------|------|-----------|---------|
| `/v1/describe` | POST | no | agent | Return manifest |
| `/v1/execute` | POST | yes | agent | Execute task |
| `/v1/health` | POST | no | agent | Health check |
| `/v1/message` | POST | yes | agent | Synchronous request/response |
| `/v1/services` | POST | yes | agent | Receive service directory updates |
| `/v1/event` | POST | yes | agent | Receive event delivery (pub/sub) |
| `/v1/register` | POST | no | orchestrator | Agent registration |
| `/v1/register` | DELETE | yes | orchestrator | Agent deregistration |
| `/v1/services` | GET | yes | orchestrator | Service directory + routing table |
| `/v1/channel` | POST | yes | orchestrator | Broker channel |
| `/v1/health` | GET | no | orchestrator | Orchestrator health |
| `/v1/audit` | GET | yes | orchestrator | Audit log |
| `/v1/rotate-key` | POST | yes | orchestrator | Key rotation (see identity.md) |
| `/v1/token/exchange` | POST | yes | orchestrator | Exchange the operator token a person has just presented to the admin gateway for a pass addressed to one component (`TokenExchangeResponse`). The admin gateway's alone |
| `/v1/model/ceiling` | GET | yes | orchestrator | What a model backend may be sent now, and where it is reached. Platform-provided (architecture/orchestrator) |

---

## Error Handling


```yaml
error_format:
  type: ErrorResponse
  required_fields: [error]
  optional_fields: [code, category, retryable, retry_after, detail]

error_codes:
  - code: INVALID_REQUEST
    status: 400
    category: permanent
    retryable: false
    description: Missing or malformed fields
  - code: INVALID_SIGNATURE
    status: 401
    category: permanent
    retryable: false
    description: ML-DSA-65 signature verification failed
  - code: TOKEN_EXPIRED
    status: 401
    category: transient
    retryable: true
    description: Token past expiry — re-register to get a new one
  - code: FORBIDDEN
    status: 403
    category: permanent
    retryable: false
    description: Missing required capability
  - code: CAPABILITY_PERSON_ONLY
    status: 403
    category: permanent
    retryable: false
    description: A registration manifest, a grant to a service subject, a token minted for one, or an agent's authorisation names a capability this document marks person only (see Capability). Nothing is issued. The wire form of patterns/principal-identity's capability_person_only
  - code: NOT_FOUND
    status: 404
    category: permanent
    retryable: false
    description: Agent or resource not in registry
  - code: RATE_LIMITED
    status: 429
    category: transient
    retryable: true
    description: Too many requests — respect `Retry-After` header
  - code: INTERNAL_ERROR
    status: 500
    category: transient
    retryable: true
    description: Unexpected server error
  - code: AGENT_UNREACHABLE
    status: 502
    category: transient
    retryable: true
    description: Orchestrator could not reach target agent
  - code: AGENT_TIMEOUT
    status: 504
    category: transient
    retryable: true
    description: Target agent did not respond within timeout
  - code: UNSUPPORTED_VERSION
    status: 400
    category: permanent
    retryable: false
    description: Agent requested an unsupported protocol version
  - code: NAMESPACE_CONFLICT
    status: 409
    category: permanent
    retryable: false
    description: Requested publish namespace already owned by another agent
  - code: NAMESPACE_RESERVED
    status: 403
    category: permanent
    retryable: false
    description: Requested namespace is reserved (e.g., `system.*`)
  - code: ADDRESS_CONFLICT
    status: 409
    category: permanent
    retryable: false
    description: A registration's `url` contradicts the address the tenant declared for that component. Nothing is recorded (architecture/orchestrator, What the directory attests)
  - code: SCOPE_UNAUTHORIZED
    status: 403
    category: permanent
    retryable: false
    description: Subscription scope requires missing capability or collaborator relationship
  - code: EVENT_REJECTED
    status: 400
    category: permanent
    retryable: false
    description: Event envelope is malformed or topic is unowned
  - code: PHASE_FAILED
    status: 500
    category: varies
    retryable: varies
    description: Workflow phase failed — check `detail.phase_name`
  - code: PARTIAL_FAILURE
    status: 207
    category: partial
    retryable: varies
    description: Some phases succeeded, some failed
```
All errors across the protocol use the `ErrorResponse` type defined in the
Errors section above. Error categories (`transient`, `permanent`, `partial`)
determine retry behavior. Standard error codes are enumerated in the
ErrorResponse section with their HTTP status mappings.

Implementations MUST:
- Always return at minimum `{"error": "message"}`
- Include `code` and `category` when the information is available
- Use exact error codes from the central registry (agent-local codes are permitted — see Error Code Conventions)
- Map error codes to the correct HTTP status codes

---

## Scope

`ScopeLevel` and `ScopeDeclaration` are
[`patterns/scope`](../patterns/scope.md#types)'s, and are defined there alone.
A blueprint that uses either binds it from `patterns/scope`.

---

## Policy

### PolicyRule

A single declarative rule within a policy definition.

```yaml
types:
  PolicyRule:
    fields:
      rule:
        name: Rule
        type: string
        required: true
        description: "Rule type (e.g., `scope_required`, `rate_limit`, `capability_required`)"
      params:
        name: Params
        type: map
        required: true
        description: "Rule-specific parameters"
```

### PolicyDecision

Result of evaluating a policy against an operation context.

```yaml
types:
  PolicyDecision:
    fields:
      policy_name:
        name: PolicyName
        type: string
        required: true
        description: "Which policy was evaluated"
      decision:
        name: Decision
        type: DecisionResult
        required: true
        description: "Policy evaluation result — uses the canonical `DecisionResult` enum"
      rule_matched:
        name: RuleMatched
        type: string
        required: false
        description: "Which rule triggered the decision"
      reason:
        name: Reason
        type: string
        required: false
        description: "Human-readable explanation"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "When the decision was made"
```

---

## Safety

### OperationIntent

Pre-flight declaration of what an operation intends to do,
evaluated before the operation executes.

```yaml
types:
  OperationIntent:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique intent identifier"
      agent:
        name: Agent
        type: string
        required: true
        description: "Agent requesting the operation"
      operation:
        name: Operation
        type: string
        required: true
        description: "Operation class: `read`, `list`, `query`, `create`, `modify`, `delete`, `destroy`"
      resource:
        name: Resource
        type: string
        required: true
        description: "Target resource identifier"
      resource_class:
        name: ResourceClass
        type: string
        required: true
        description: "`ephemeral`, `application`, `system`, `critical`"
      scope:
        name: Scope
        type: string
        required: true
        description: "ScopeLevel of the target resource"
      environment:
        name: Environment
        type: string
        required: true
        description: "`development`, `staging`, `production`"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### IntentDecision

Response to an OperationIntent — whether the operation may proceed.

```yaml
types:
  IntentDecision:
    fields:
      intent_id:
        name: IntentID
        type: string
        required: true
        description: "Which intent this decides"
      decision:
        name: Decision
        type: DecisionResult
        required: true
        description: "Canonical decision outcome (see Decision Taxonomy)"
      authority:
        name: Authority
        type: string
        required: true
        description: "Who/what made the decision"
      conditions:
        name: Conditions
        type: "[]string"
        required: false
        description: "Conditions attached to approval"
      reason:
        name: Reason
        type: string
        required: false
        description: Explanation
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

---

## Decision Taxonomy

All components that produce access decisions — enforcement boundaries,
safety gates, and policy evaluators — use a unified decision vocabulary.
Each component produces decisions from its own subset; enforcement
resolves them into a final action using most-restrictive-wins.

### DecisionResult

Canonical decision outcomes across all evaluation layers.

| Value | Ordinal | Description | Produced By |
|-------|---------|-------------|-------------|
| `allow` | 0 | Operation permitted | enforcement, safety, policy |
| `audit` | 1 | Operation permitted but logged for review | policy |
| `require_approval` | 2 | Operation held pending operator/admin approval | enforcement, safety |
| `escalate` | 3 | Operation held pending elevated authority approval | safety, policy |
| `deny` | 4 | Operation rejected | enforcement, safety, policy |
| `quarantine` | 5 | Operation rejected and agent isolated | enforcement |

Comparison: ordinal-based; higher ordinal = more restrictive.
Most-restrictive-wins: when multiple evaluations produce different
decisions, the highest ordinal prevails.

### Decision Mapping

When combining decisions from different layers, enforcement maps
each layer's output to the canonical DecisionResult:

| Layer | Layer Decision | Maps To |
|-------|---------------|---------|
| Policy | `allow` | `allow` |
| Policy | `audit` | `audit` — operation proceeds, decision logged for review |
| Policy | `escalate` | `escalate` — treated as `require_approval` with elevated authority |
| Policy | `deny` | `deny` |
| Safety | `allow` | `allow` |
| Safety | `require_approval` | `require_approval` |
| Safety | `deny` | `deny` |
| Safety | `escalate` | `escalate` |
| Enforcement | `allow` | `allow` |
| Enforcement | `require_approval` | `require_approval` |
| Enforcement | `deny` | `deny` |
| Enforcement | `quarantine` | `quarantine` — only enforcement can issue quarantine |

### Severity

Unified severity levels used by enforcement violations, security
events, and safety classifications.

| Value | Description |
|-------|-------------|
| `info` | Informational — no action required |
| `low` | Minor issue — logged |
| `medium` | Notable issue — may trigger alerts |
| `high` | Serious issue — immediate escalation |
| `critical` | Emergency — may trigger quarantine or kill-switch |

---

## Enforcement

### EnforcementDecision

Result of boundary inspection by the enforcement layer.

```yaml
types:
  EnforcementDecision:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique decision identifier"
      boundary:
        name: Boundary
        type: string
        required: true
        description: "`message`, `storage`, `external`, `response`"
      agent:
        name: Agent
        type: string
        required: true
        description: "Agent whose operation was inspected"
      action:
        name: Action
        type: string
        required: true
        description: "DecisionResult value"
      violations:
        name: Violations
        type: "[]string"
        required: false
        description: "Policy/scope/privacy violations detected"
      privacy_actions:
        name: PrivacyActions
        type: "[]string"
        required: false
        description: "Privacy actions applied (masking, minimization)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "Correlation with distributed trace"
```

---

## Identity

### KeyRotationRequest

[`protocol/identity`](identity.md#types)'s, and defined there alone, for
[agent key rotation](identity.md#rotation-flow). A blueprint that uses it binds
it from `protocol/identity`.

---

## Logging

### LogEntry

Structured log entry emitted by agents. See [patterns/logging](../patterns/logging.md)
for the full logging specification.

```yaml
types:
  LogEntry:
    fields:
      ts:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds (consistent with all protocol timestamps)"
      level:
        name: Level
        type: string
        required: true
        description: "`debug`, `info`, `warn`, `error`, `fatal`"
      log_type:
        name: LogType
        type: string
        required: true
        description: "`app`, `access`, `audit`, `security`"
      msg:
        name: Message
        type: string
        required: true
        description: "Human-readable log message"
      component:
        name: Component
        type: string
        required: true
        description: "Agent or subsystem name"
      component_type:
        name: ComponentType
        type: string
        required: true
        description: "`agent`, `orchestrator`, `gateway`"
      trace_id:
        name: TraceID
        type: string
        required: false
        description: "Distributed trace correlation"
      span_id:
        name: SpanID
        type: string
        required: false
        description: "Span within trace"
      error:
        name: Error
        type: string
        required: false
        description: "Error message (when level is error/fatal)"
```

### TraceContext

Distributed trace propagation context (W3C Trace Context compatible).

```yaml
types:
  TraceContext:
    fields:
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "32-char hex trace identifier"
      span_id:
        name: SpanID
        type: string
        required: true
        description: "16-char hex span identifier"
      parent_span_id:
        name: ParentSpanID
        type: string
        required: false
        description: "Parent span for nesting"
      sampled:
        name: Sampled
        type: bool
        required: false
        description: "Whether this trace is sampled (default: true)"
```

---

## Types

```yaml
types:

  WorkflowResult:
    description: The outcome of a completed workflow execution, as reported to its invoker
    fields:
      workflow_name:
        type: string
        description: The workflow that ran
      status:
        type: string
        description: Terminal state of the execution
        constraints:
          enum: [completed, failed, partial, cancelled]
      invoker:
        type: string
        description: The agent or principal that triggered the workflow
      phase_results:
        type: array
        items: PhaseResult
        description: One entry per phase, in execution order
      observations:
        type: array
        items: Observation
        description: Observations produced during execution
      recommendations:
        type: array
        items: Recommendation
        description: Recommendations produced during execution

  TaskPayload:
    description: The action and arguments a task carries, separated from its envelope
    fields:
      action:
        type: string
        description: The action the target agent is asked to perform
      payload:
        type: map
        description: Arguments for the action, shaped by the target's declared inputs
      trace_id:
        type: string
        description: Correlation identifier propagated across every hop of this task

  FileRecord:
    description: A stored file and the addresses it can be retrieved from
    fields:
      id:
        type: string
        description: Stable identifier for the stored file
      filename:
        type: string
        description: Original filename as supplied, sanitised
      mime_type:
        type: string
        description: Detected content type, determined from content rather than filename
      size:
        type: int64
        description: Size in bytes
      owner_id:
        type: string
        description: The principal the file belongs to
      visibility:
        type: string
        description: Who may retrieve it
        constraints:
          enum: [private, scoped, public]
      urls:
        type: map
        description: Retrieval addresses by variant, where variants exist

  RateLimitConfig:
    description: How a component limits request rates
    fields:
      algorithm:
        type: string
        description: The limiting algorithm in use
        constraints:
          enum: [token-bucket, fixed-window, sliding-window]
      defaults:
        type: map
        description: Limits applied where a route declares none
      routes:
        type: map
        description: Per-route overrides, keyed by route path
      storage:
        type: string
        description: Where counters are held. A limiter whose counters are per-instance does not limit a distributed component
```

---

## Security

```yaml
security:
  transport:
    - Types are serialized as JSON over HTTP
    - All string fields MUST be validated for maximum length before processing
    - No executable content in any type field
  signing:
    algorithm: ML-DSA-65
    key_type: 1952-byte public / 4032-byte private (FIPS 204)
    process: Signature fields contain base64url-encoded ML-DSA-65 signatures
  verification:
    process: All signature fields verified against sender public key
  type_safety:
    - Required fields MUST be validated before processing
    - Enum fields MUST be validated against allowed values
    - IDs MUST be validated as 32-char hex strings
    - Timestamps MUST be validated as positive integers
    - Unknown fields MUST be silently ignored (forward compatibility)
  string_limits:
    - Identifiers (name, agent_name, topic, action): max 128 characters
    - Descriptions and messages: max 1024 characters
    - Payload fields (JSON objects): max 1 MiB serialized
    - URL fields: max 2048 characters
    - Base64url-encoded keys/signatures: validated by expected decoded byte lengths (1952 for public keys, 3309 for signatures)
```

---

## Implementation Notes

- Types are language-agnostic — implementations map to native types
- JSON is the sole wire format; field names in the `json` column are canonical
- Optional fields omitted from JSON are treated as zero values (empty string, 0, null, false)
- The `map` type serializes as a JSON object with string keys
- `int64` timestamps MUST NOT use floating point — JSON `number` with no decimal
- Protocol Paths table is the single source of truth for endpoint definitions
- Types are versioned with the protocol — all types share the blueprint version

---

## Verification Checklist

- [ ] All IDs are 32-character hex strings (16 random bytes) and all timestamps are Unix epoch seconds (int64)
- [ ] ML-DSA-65 signatures serialize as base64url-encoded 3309 bytes; public keys serialize as base64url-encoded 1952 bytes
- [ ] ErrorResponse includes `error` (required), `code`, `category`, `retryable`, and `detail` fields with exact JSON keys
- [ ] Error categories are constrained to `transient`, `permanent`, or `partial` and each standard error code maps to the correct HTTP status
- [ ] Unknown JSON fields are silently ignored on deserialization (forward compatibility); optional fields are omitted when empty/null
- [ ] AgentManifest requires `name`, `version`, `description`, `url`, `public_key`, and `capabilities`; includes `publishes` and `subscriptions` for event system
- [ ] EventEnvelope requires `event_id`, `topic`, `source`, `scope`, `timestamp`, `trace_id`, `version`, and `payload`
- [ ] Subscription requires `pattern`; `scope` defaults to `"self"`; `group` defaults to agent name
- [ ] RouteEntry requires `agent`, `url`, and `scope`
- [ ] ServiceDirectory includes `services`, `routing_table`, and `namespaces`
- [ ] WorkflowPhase `on_error` supports `fail`, `skip`, and `retry`; `max_retries` applies only when `on_error` = `"retry"`
- [ ] WorkflowExecution `status` transitions follow `pending` → `running` → `completed` | `failed`; PhaseResult adds `skipped`
- [ ] TaskRequest requires `id`, `from`, `action`, `payload`, `context`, `token`, and `timestamp`; TaskResult status is `success`, `failed`, or `pending_approval`
- [ ] AgentMessage `signature` covers `canonicalize({from, to, action, payload})` per RFC 8785 and `trace_id` propagates through downstream calls
- [ ] Finding includes all required fields: `rule_id`, `severity`, `element`, `current`, `expected`, `message`, and `fixable`
- [ ] RegisterResponse includes `agent_id`, `token`, `expires_at`, `services`, `orchestrator`, and negotiated `protocol_version`
- [ ] ChannelGrant includes `channel_id`, scoped `channel_token`, `target_url`, `target_pub_key`, and `expires_at`
- [ ] Protocol paths are all prefixed with `/v1` and method/auth requirements match the Protocol Paths table
- [ ] DeadLetterEntry includes `original_event`, `failure_reason`, `last_error`, `attempts`, and `subscriber`
- [ ] PolicyDecision requires `policy_name`, `decision`, and `timestamp`; decision uses DecisionResult enum
- [ ] OperationIntent requires `id`, `agent`, `operation`, `resource`, `resource_class`, `scope`, `environment`, and `timestamp`; operation includes `list` and `query`
- [ ] IntentDecision requires `intent_id`, `decision`, `authority`, and `timestamp`; decision uses DecisionResult enum
- [ ] EnforcementDecision requires `id`, `boundary`, `agent`, `action`, `timestamp`, and `trace_id`; boundary includes `response`
- [ ] DecisionResult enum is constrained to `allow`, `audit`, `require_approval`, `escalate`, `deny`, `quarantine` with ordinal-based comparison
- [ ] Severity enum is constrained to `info`, `low`, `medium`, `high`, `critical` — used consistently across enforcement, security, and safety
- [ ] Decision mapping table resolves policy/safety/enforcement decisions to canonical DecisionResult using most-restrictive-wins
- [ ] All protocol-level error codes (standard, enforcement, contract, federation, safety, policy, operator token, destination, identity, common) are registered centrally; agent-local codes use domain-descriptive names and do not collide with registered codes
- [ ] Every code a `TokenExchangeResponse` may carry in `code` is registered here with its HTTP status, so the admin gateway, refusing a request whose token the exchange refused, answers with that status and never a guessed one
- [ ] `PASS_REQUIRED` and `PASS_AUDIENCE_MISMATCH` are registered with status 401, and `token:exchange` is in the Capability list
- [ ] `ADDRESS_CONFLICT` is registered with status 409, beside `NAMESPACE_CONFLICT`
- [ ] `content:declassify` is in the Content capabilities and marked *person only*, so a registration whose manifest declares it is refused with `CAPABILITY_PERSON_ONLY`
- [ ] Administrative authority is expressed as `admin:` capabilities in the standard list — not as a separate role model — and `admin:*` denotes the whole family
- [ ] Every capability bullet in Capability names exactly one owner in brackets, and no capability name is listed twice
- [ ] `programme:switch`, `integration:manage`, `action:invoke` and `scope:admit` are marked *person only*; `programme:read`, `programme:install`, `programme:operate`, `integration:read`, `integration:use`, `telemetry:read` and `telemetry:push` are not
- [ ] `telemetry:read`, `action:invoke` and `scope:admit` are outside the `admin` family, so `admin:*` carries none of them
- [ ] `content:connect` binds an integration to an outside destination and creates no credential
