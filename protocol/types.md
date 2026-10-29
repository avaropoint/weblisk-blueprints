<!-- blueprint
type: protocol
name: types
version: 6.3.0
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

- Every `timestamp`, `uuid`, `duration` and `integer` is written as [`protocol/conventions`](conventions.md) says, and every field that holds an instant is a `timestamp`
- All IDs are 32-character hex strings (16 random bytes), except a span id ([TraceContext](#tracecontext))
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

**Token request codes** (produced by the orchestrator's judgement of a request
for an attestation token, `architecture/admin`'s `attestation-token-issuance`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `TOKEN_REQUEST_REPLAYED` | 401 | permanent | The request's `jti` was already recorded for that operator inside the replay window ([`architecture/admin`](../architecture/admin.md#obtaining-a-token), `attestation-token-issuance`). No token is issued; the client signs a new request with a fresh `jti`, and never registers for it |

**Step-up code** (produced by the component that serves a destructive act,
`architecture/admin`'s `destructive-action-step-up`, on an operator token or a
pass). Every such component MUST answer it with this status and no other.
<!-- wl:id step-up-required-registered -->

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `STEP_UP_REQUIRED` | 401 | permanent | A destructive act arrived without the step-up it needs. Nothing changes. When it is answered, what it carries and how a client answers it are [`architecture/admin`](../architecture/admin.md#contracts)'s `destructive-action-step-up`, stated nowhere else. The admin gateway returns it as the provider gave it |

**Work pass codes** (produced by the orchestrator's judgement of a work
authorisation at `POST /v1/token/work`, and answered in
`WorkExchangeResponse.code`, [`protocol/identity`](identity.md#the-work-pass)):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `WORK_AUTHORISATION_UNKNOWN` | 404 | permanent | The orchestrator holds no such work authorisation, or it does not name the caller among its actors. The two are answered alike |
| `WORK_AUTHORISATION_REVOKED` | 403 | permanent | The work authorisation was revoked. Nothing is minted |
| `WORK_AUTHORISATION_EXPIRED` | 403 | permanent | The work authorisation is past its `not_after`. Nothing is minted until a person renews it |
| `WORK_OWNER_UNREGISTERED` | 409 | transient | The work authorisation's owner is not registered now under the identity id it names. Nothing is minted |

**Programme service codes** (produced by the programme service,
[`architecture/programme-service`](../architecture/programme-service.md#error-handling)):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `PROGRAMME_NOT_ADOPTED` | 404 | permanent | An installation named a programme the organisation holds no `adoption.md` for in any of its repositories. Nothing is installed; a person adopts it first |

**Pass codes** (produced by a component that a person's request reaches,
[`protocol/identity`](identity.md#the-pass)):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `PASS_REQUIRED` | 401 | permanent | A component other than the orchestrator and the admin gateway was presented an operator token, which no holder may present there ([`protocol/identity`](identity.md#the-pass), rule 4). A person's request goes to the tenant's admin gateway, which carries it on a pass, and a tool call to the MCP surface on a credential [`patterns/auth-oauth`](../patterns/auth-oauth.md) issued for it ([`architecture/mcp`](../architecture/mcp.md)). Logged as a security event |
| `PASS_AUDIENCE_MISMATCH` | 401 | permanent | A pass or a work pass was presented to a component its `aud` does not name, the orchestrator included. Logged as a security event |

**Destination codes** (produced by the destination gate of `patterns/scope`,
and answered by every sender it binds):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `SCOPE_MISSING` | 400 | permanent | An entity has no scope declaration where one is required: `reject_unscoped` is enabled, or it would be sent to a destination. At a destination, `detail` is a `DestinationRefusal` |
| `SCOPE_CEILING_EXCEEDED` | 403 | permanent | Content would be sent to a destination whose ceiling is below its scope. `detail` is a `DestinationRefusal` |

What the gate refuses, and what a `DestinationRefusal` carries, are
`patterns/scope`'s.

**Resource codes** (produced by the owner of a resource kind, and by the admin
gateway at the uniform address, [`schemas/resource`](../schemas/resource.md);
when each is answered is
[`architecture/admin`](../architecture/admin.md#writes-and-what-guards-them)'s).
Every owner of a kind answers them with these statuses and no other.

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `RESOURCE_KIND_UNDECLARED` | 404 | permanent | The kind is not one the tenant's catalogue declares. An undeclared kind does not exist on the wire |
| `RESOURCE_OPERATION_UNDECLARED` | 405 | permanent | The kind is declared and the operation or verb is not one its declaration names. The answer's `Allow` header names the methods the address does serve |
| `RESOURCE_FIELD_NOT_SETTABLE` | 400 | permanent | A write names a field its declaration does not let a person set there: a `read-only` field, or a `create` field on `update`. `detail.fields` names each. Nothing changes |
| `RESOURCE_IF_MATCH_REQUIRED` | 428 | permanent | An `update`, a `delete` or a verb arrived with no `If-Match`. A write with no precondition acts on something its sender has not seen |
| `RESOURCE_PRECONDITION_FAILED` | 412 | permanent | `If-Match` does not equal the item's ETag now. Nothing changes. The answer carries the current ETag; the client reads the item again |

**Tenant structure codes** (produced by the orchestrator's organisations,
projects and grants, [`architecture/orchestrator`](../architecture/orchestrator.md#the-tenants-organisations-and-projects)):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `SCOPE_NAME_TAKEN` | 409 | permanent | An organisation, or a project of the same organisation, has held that name, retired ones included, so a `scope_path` naming it would name two things. Nothing is recorded |
| `GRANT_SELF_REFUSED` | 403 | permanent | A grant made naming the person making it, or revoked by the person it names. Nothing changes ([A role held at an organisation or a project](../architecture/orchestrator.md#a-role-held-at-an-organisation-or-a-project)) |

**Execution codes** (produced by [`architecture/execution`](../architecture/execution.md#error-handling)):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `EXECUTION_NOT_A_HOLDER` | 403 | permanent | The person deciding a wait does not hold the position the decision names, or that position is not one the wait still awaits. Nothing is decided |
| `EXECUTION_DECISION_OUT_OF_ORDER` | 409 | permanent | A sequential approval decided as a position whose turn has not come. Nothing is decided |
| `EXECUTION_POSITION_UNRESOLVED` | 503 | transient | Who holds the positions a wait names cannot be read, so no decider can be shown to hold one. Nothing is decided |
| `EXECUTION_MUTED` | 409 | permanent | A decision on a wait of a muted run, which reaches nobody |
| `EXECUTION_PASS_UNAVAILABLE` | 503 | transient | A request of a run must be carried on a work pass under its definition's work authorisation and none can be obtained. The step is not dispatched |

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
| `BEHAVIORAL_CHANGE` | 409 | permanent | The agent has a behavioural change awaiting admin review, and is suspended from federated work until it is approved ([`protocol/federation`](federation.md#change-detection)) |
| `RETENTION_EXPIRED` | 410 | permanent | Requested data has been purged per retention policy |

#### Error Code Conventions

Error codes follow the convention: `DOMAIN_SPECIFIC_ERROR`. Domain
prefixes (`ENFORCEMENT_`, `CONTRACT_`, `POLICY_`, etc.) indicate the
originating subsystem.

**Registry vs. local codes:**
- All protocol-level, enforcement, policy, contract, federation,
  safety, operator token, resource, tenant structure, destination, execution, identity, and common codes are
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
      resources:
        name: Resources
        type: "[]ResourceDeclaration"
        required: false
        description: "Each kind this component's blueprint declares in its Resources block, and no other. Absent or empty: it owns no kind a person may operate. See [Resources](#resources)"
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
owners or none is a fault. The vocabulary is what a manifest, a role and a
token's `cap` may name; a capability listing one hub publishes to another
([`architecture/hub`](../architecture/hub.md)) is named by the hub that
publishes it and is not part of it, so `architecture/hub`'s federation
examples, such as `inventory:check`, are listings and are not listed here. An owner is named as a unit: `orchestrator`
([`architecture/orchestrator`](../architecture/orchestrator.md), with
[`architecture/admin`](../architecture/admin.md) its administrative surface),
`content`, `fabric`, `enforcement`, `gateway`, `domain` and `execution` (each its
`architecture/` blueprint). `programme` is
[`architecture/programme-service`](../architecture/programme-service.md), which
no tenant runs yet, and `notification` is
[`architecture/notification`](../architecture/notification.md), which no
tenant runs yet. Two owners have no blueprint in this
corpus yet: `integrations` and `telemetry`. The names of these four guard no
running route until a component built from their owner's blueprint runs. Five names have a nominated owner
whose blueprint does not yet say what they admit: `file:read`, `file:write` and
`http:get` (enforcement) and `http:receive` and `realtime:publish` (gateway).
Those five are judged by no rule until their owner's blueprint states one. All
of these are listed now because a registration naming an unlisted capability is
refused ([`protocol/spec`](spec.md#post-v1register)).

**Standard capabilities:**
- `file:read` (enforcement) — read files (resources: glob patterns)
- `file:write` (enforcement) — write/modify files
- `llm:chat` (orchestrator) — use a language model. A person's request needs it to ask the tenant's model for a completion at `POST /v1/admin/complete` ([`architecture/orchestrator`](../architecture/orchestrator.md#administrative-endpoints)), and `architecture/admin`'s roles table says which roles carry it. A registered component needs it, declared on its own manifest, to ask the tenant's model at `POST /v1/model/complete`, the model service's route ([`architecture/model-service`](../architecture/model-service.md#who-may-ask)). It is the one capability a requester needs to ask a model, and no other is minted for that: the model capabilities below are for recording an agreement (`model:attest`) and for serving the tenant's model route (`model:route`)
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
- `content:connect` (content) — bind an integration to a destination outside the tenant's store, a remote's among them. It creates nothing in the content service: the credential is the integration's, and the content service holds none. Required in addition to `content:replicate` to declare a remote. *Person only*
- `content:declassify` (content) — lower a path's recorded scope. It guards no route yet: [`architecture/content`](../architecture/content.md) refuses every lowering until a route for it is specified: one person's decision made with a step-up, and a second person's too only where the tenant declares one. *Person only*

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
- `model:route` (enforcement) — send to a model provider's endpoint as the tenant's model route ([`patterns/scope`](../patterns/scope.md#the-gate)). Declared by a component that serves `patterns/api-ai`'s endpoints, and by nothing else. `POST /v1/admin/complete` and `POST /v1/model/complete` are served by the model gateway in the orchestrator's own process and by no component, so nothing declares it there ([`patterns/scope`](../patterns/scope.md#the-gate), Where the tenant applies it)

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
- `programme:read` (programme) — read a programme's installations and installed items and what they have produced, and what is due: obligations in force, their occurrences, the due list and readiness
- `programme:install` (programme) — install a programme's operations at a scope
- `programme:operate` (programme) — pause, resume, run and reschedule an installed operation or workflow
- `programme:switch` (programme) — decide whether an installed item's runs and advances reach people: mute and unmute. Who hears an item is not switched by it: that is the positions the map names and who holds them, each changed where it is held ([`architecture/programme-service`](../architecture/programme-service.md#rescheduling)). *Person only*

Which route needs which is
[`architecture/programme-service`](../architecture/programme-service.md#endpoints)'s.
No tenant runs a component built from that document yet, so these names guard
no running route. The programme
service is to declare the first three, because a grant to a caller is the
intersection of what it holds and what the serving manifest declares, and to
check `programme:switch` without ever holding it, as `content` does its own
person-only capabilities.

**Execution capabilities:**
- `execution:read` (execution) — read runs, their steps, waits and timers, registered starts, and the definitions execution fetched
- `execution:operate` (execution) — cancel a run, and retry a failed one. A registration token reaches only runs of definitions its own identity owns
- `execution:register` (execution) — register, change, pause, resume, run now and withdraw the caller's own starts. A component's, on its registration token; no role carries it
- `execution:decide` (execution) — decide a wait: complete or decline a person's task, accept or reject an approval, as a holder of a position the wait awaits. *Person only*

Which route needs which is [`architecture/execution`](../architecture/execution.md#endpoints)'s.
`execution:decide` is person only for the reason `content:decide` is: a
machine that could hold it could close a person's step. Holding it is not
enough to decide a wait that names a position; the decider must also hold
the position ([`architecture/execution`](../architecture/execution.md#who-holds-a-position)).

**Integration capabilities:**
- `integration:read` (integrations) — read the tenant's integrations: provider, account, method, scopes, owner, purposes, expiry and status, and never a secret
- `integration:manage` (integrations) — make, bind to a declared need, re-purpose, rotate and revoke an integration, where the consuming owner declares no capability of its own for the act (`content:connect` is the one for a remote's key). *Person only*
- `integration:use` (integrations) — have an integration act for a need the holder's blueprint declares: a token, a signature or verdict, or a relayed call, and never the secret

`integration:use` is a component's, declared for a need its blueprint states,
and no role carries it. Which roles carry the other two, and what a person may
delegate, is [`architecture/admin`](../architecture/admin.md#operator-roles)'s.

**Telemetry capabilities:**
- `telemetry:read` (telemetry) — read the tenant's runtime: metrics, logs, traces, events, probe results and rule state
- `telemetry:push` (telemetry) — push a component's own signals to telemetry over OTLP, under a pass. Reads nothing

`telemetry:read` is not person only: an agent whose blueprint declares a read
of telemetry holds it within that declaration. A person holds it only through
a role, and which roles carry it is
[`architecture/admin`](../architecture/admin.md#operator-roles)'s.
`telemetry:push` is declared by every component that reports, and no role
carries it.

**Action and admission capabilities:**
- `action:invoke` (orchestrator) — invoke an operator action a component's blueprint declares, where the action names no capability of that component's own family. *Person only*
- `scope:admit` (orchestrator) — admit the operational scope a component declares, the highest classification it may reach. *Person only*

`action:invoke` is what a verb in a Resources block names when its act is in
no capability family its owner holds ([`schemas/resource`](../schemas/resource.md#verbs)).
The first such verbs are execution's on a run, held until execution's
blueprint is written, so it guards no running route yet. `scope:admit` guards
none either: `AgentManifest` has no operational scope. Both are listed so that
each act has one name before it is specified.

No capability is listed here for a component recording into the one audit
ledger. No route for that write exists yet; whether it needs a capability is
decided where the route is specified, in
[`architecture/orchestrator`](../architecture/orchestrator.md), which owns the
audit routes and adds its name here first if it needs one.

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
- `token:exchange` (orchestrator) — have the orchestrator exchange the operator token a person has just presented for a pass addressed to one component ([`protocol/identity`](identity.md#the-pass); `architecture/orchestrator`, `token-exchange`). The admin gateway declares it, and no other blueprint does. No role carries it. *Admin gateway only*

`token:exchange` is what the admin gateway's registration declares, and the
only capability it declares: the gateway reads the service directory, which
any registration may, and exchanges, and holds no standing access to data
([`architecture/admin`](../architecture/admin.md#contracts),
`admin-gateway-authorization`). *Admin gateway only* marks a capability the
orchestrator admits for one registration alone: the one whose identity id is
the fingerprint the tenant declared as its admin gateway's key
(`orchestrator.admin_gateway_identity`,
[`schemas/config`](../schemas/config.md#orchestrator)). A registration whose
manifest declares it, by any other key or where the tenant declared none, is
refused with `CAPABILITY_GATEWAY_ONLY` ([Error Handling](#error-handling)),
and the exchange refuses any other caller
([`architecture/orchestrator`](../architecture/orchestrator.md#registration-flow-post-v1register),
step 1, and `token-exchange`). <!-- wl:id gateway-only-capability --> Without that refusal any registrant could
declare it, and with a person's stolen token have it exchanged for a pass to
any component, carrying everything that person may use there and passing none
of the admin gateway's network controls.

**Work capabilities:**
- `work:authorise` (orchestrator) — make, renew and revoke a work authorisation: allow a registered component's definition to run with nobody present, under that component's authority and within capabilities the person may use themselves ([`protocol/identity`](identity.md#the-work-pass), rules 1 and 2). *Person only*
- `work:exchange` (orchestrator) — have the orchestrator mint a work pass under a work authorisation that names this registration among its actors ([`protocol/identity`](identity.md#the-work-pass); `architecture/orchestrator`, `work-exchange`). No role carries it

`work:authorise` is person only because allowing work that runs with nobody
present is a judgement, and nothing that cannot judge may delegate
([`patterns/principal-identity`](../patterns/principal-identity.md#implementation-notes)).
It is not in the `admin` family, so `admin:*` does not carry it, and a person
holds it only where [`architecture/admin`](../architecture/admin.md#operator-roles)'s
roles table names it. `work:exchange` is a component's: any registration may
declare it, and it reaches nothing until a person names that registration as
an actor in an authorisation.

**Notification capabilities:**
- `notification:send` (notification) — ask notification to tell the holders of positions, for a notice whose work authorisation the caller owns or acts under ([`architecture/notification`](../architecture/notification.md#who-may-do-what), rule 3). No role carries it
- `notification:read` (notification) — read notifications and their deliveries: which positions were told, how many held each, the outcome, and each holder told by identity id, never an address
- `notification:receive` (notification) — read and set one's own notification preference, and read what one was told. It reaches no other person's. *Person only*

Which route needs which is
[`architecture/notification`](../architecture/notification.md#endpoints)'s.
`notification:send` is a component's: a person does not send a programme's
notice, so no role carries it and a pass is refused on the route it guards.
`notification:read` names people, by identity id, so
[`architecture/admin`](../architecture/admin.md#operator-roles)'s roles table
gives it to the roles that read people's records and not to `viewer`.
`notification:receive` is person only because a preference and a received
message are one person's own, and every role carries it. The service declares
the first two and checks the third without holding it, as `content` does its
own person-only capabilities.

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
      inbox:
        name: Inbox
        type: InboxRoute
        required: false
        description: "Present only on the one `GET` route that lists this component's open decisions for the admin gateway's decision inbox. See [InboxRoute](#inboxroute)"
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

### InboxRoute

How the admin gateway composes its decision inbox from an owner's own list,
without a line of code for that owner
([`architecture/admin`](../architecture/admin.md#decision-inbox)). An owner
declares it on the `PassRoute` of the one route that lists its open
decisions, and declares the decision route it names as a pass route too.

```yaml
types:
  InboxRoute:
    fields:
      query:
        name: Query
        type: string
        required: false
        description: "The query string the gateway sends with the list request, without its `?`, such as `state=open`. Absent: none"
      items:
        name: Items
        type: string
        required: true
        description: "The top-level member of the list's answer that holds the records, each an object carrying `id`. The gateway returns each record unchanged"
      withheld:
        name: Withheld
        type: string
        required: false
        description: "The top-level member holding the owner's count of open decisions it omitted because the person may not read them. Absent: the owner omits none"
      decide_method:
        name: DecideMethod
        type: string
        required: true
        description: "The method of the route a record is decided at, in upper case"
      decide_path:
        name: DecidePath
        type: string
        required: true
        description: "The path of that route, with exactly one `{name}` segment, which the gateway fills with the record's `id`. The same manifest MUST declare it among its `pass_routes`"
```

A manifest declares `inbox` on at most one route, and only on a `GET` route.
The gateway asks that route on a pass naming its `capabilities`, and pages
through it by the answer's `next_cursor` where it carries one. A record whose
`id` is missing is not listed, and the owner's answer is then reported
incomplete, never quietly shortened.

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
        required: false
        description: "Target agent name. Required on a machine phase; absent on a person's ([`patterns/workflow`](../patterns/workflow.md#a-persons-phase))"
      action:
        name: Action
        type: string
        required: false
        description: "`HandleMessage` action to invoke. Required with `agent`"
      task:
        name: Task
        type: WorkflowTask
        required: false
        description: "A person's work, by position. Exclusive with `agent` and `approvers`"
      approvers:
        name: Approvers
        type: "[]string"
        required: false
        description: "Positions whose holders must each accept. Exclusive with `task`; beside `agent` only with `approval: required`"
      approval_order:
        name: ApprovalOrder
        type: string
        required: false
        description: "`sequential`, or absent for any order. Only with `approvers`"
      escalate:
        name: Escalate
        type: WorkflowEscalation
        required: false
        description: "Only on a phase with `task` or `approvers`"
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
      max_attempts:
        name: MaxAttempts
        type: int
        required: false
        description: Total attempts, the first included (protocol/conventions:max-attempts)
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
        required: false
        description: "The domain controller whose definition ran. Absent on a run whose definition another owner declares, such as the programme service"
      task_id:
        name: TaskID
        type: string
        required: false
        description: "Originating task ID. Absent on a run no task started, such as one a start fired"
      status:
        name: Status
        type: string
        required: true
        description: "A state of patterns/workflow's Workflow State Machine: `pending`, `running`, `waiting`, `completed`, `failed`, `cancelled`, `withheld`"
      phases:
        name: Phases
        type: "[]PhaseResult"
        required: true
        description: "Results per phase"
      started_at:
        name: StartedAt
        type: timestamp
        required: true
      completed_at:
        name: CompletedAt
        type: timestamp
        required: false
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
        description: "`pending`, `running`, `waiting`, `completed`, `failed`, `skipped`"
      output:
        name: Output
        type: map
        required: false
        description: "Phase output data (referenced by subsequent phases)"
      started_at:
        name: StartedAt
        type: timestamp
        required: false
      completed_at:
        name: CompletedAt
        type: timestamp
        required: false
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

### WorkflowTask

A person's work on a phase ([`patterns/workflow`](../patterns/workflow.md#a-persons-phase)).

```yaml
types:
  WorkflowTask:
    fields:
      activity:
        name: Activity
        type: string
        required: true
        description: "What the person does, in the author's words"
      responsible:
        name: Responsible
        type: string
        required: true
        description: "The position whose holder does it. Never a person"
      due:
        name: Due
        type: string
        required: false
        description: "`<n><h|d|w>` from the moment the wait opens"
```

### WorkflowEscalation

Where a person's phase left open goes ([`patterns/workflow`](../patterns/workflow.md#a-persons-phase)).

```yaml
types:
  WorkflowEscalation:
    fields:
      after:
        name: After
        type: string
        required: true
        description: "`<n><h|d|w>` past a task's due, or past an approval's opening"
      to:
        name: To
        type: string
        required: true
        description: "The position it then also belongs to. Never a person"
```

---

## Resources

The wire form of a component's Resources block
([`schemas/resource`](../schemas/resource.md)), and what the admin gateway
answers for the one API every kind is served at
([`architecture/admin`](../architecture/admin.md#resources-one-api-for-every-kind)).
What each field means is `schemas/resource`'s; these types say only how it is
carried.

### ResourceDeclaration

One kind, as its owner declares it. A component's manifest carries one for
each kind its blueprint declares (`AgentManifest.resources`), and the
catalogue answers it for each kind it reports. It is the block with
`operations` written as a list, each entry carrying its key as `name`, since
this vocabulary cannot declare a map's value shape.

```yaml
types:
  ResourceDeclaration:
    fields:
      kind:
        name: Kind
        type: string
        required: true
        description: "A kind schemas/kinds declares"
      owner:
        name: Owner
        type: string
        required: true
        description: "The name of the component that holds the kind's items"
      type:
        name: Type
        type: string
        required: true
        description: "The type an item is answered as, by its name in the owner's blueprint or one it requires"
      list_type:
        name: ListType
        type: string
        required: false
        description: "The type of one list item, where it differs from `type`"
      identity:
        name: Identity
        type: ResourceIdentity
        required: true
        description: "The field that carries the item's identity, and its form"
      label:
        name: Label
        type: string
        required: false
        description: "The field a client shows as the item's name. Never its identity"
      fields:
        name: Fields
        type: "[]ResourceField"
        required: true
        description: "Every field a client may render or set"
      operations:
        name: Operations
        type: "[]ResourceOperation"
        required: true
        description: "Each operation the kind serves, and no other"
      verbs:
        name: Verbs
        type: "[]ResourceVerb"
        required: false
        description: "Each verb the kind serves, and no other"
      states:
        name: States
        type: object
        required: false
        description: "The kind's state machine, as patterns/state-machine declares one"
      events:
        name: Events
        type: "[]string"
        required: false
        description: "What the owner announces when an item changes"
      relations:
        name: Relations
        type: "[]ResourceRelation"
        required: false
        description: "Each relation an item holds, by the field that holds its target"
      unavailable:
        name: Unavailable
        type: ResourceUnavailable
        required: false
        description: "Present only where the block itself declares the kind unavailable: `owner-unspecified`"

  ResourceIdentity:
    fields:
      field:
        name: Field
        type: string
        required: true
        description: "The field of `type` that carries the identity, as a dotted path where it is nested"
      form:
        name: Form
        type: string
        required: true
        description: "`minted` or `declared-name`"

  ResourceField:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "A field of `type`, as a dotted path where it is nested"
      access:
        name: Access
        type: string
        required: true
        description: "`read-only`, `create` or `settable`"
      present:
        name: Present
        type: string
        required: false
        description: "One presentation schemas/resource declares. Absent: rendered read-only, as its value"
      sensitive:
        name: Sensitive
        type: bool
        required: false
        description: "True: never answered, in any answer, list or event"
      volatile:
        name: Volatile
        type: bool
        required: false
        description: "True: changes by observation, and is left out of the item's ETag"
      kind:
        name: Kind
        type: string
        required: false
        description: "For `present: reference`, the kind of the item the field names"

  ResourceOperation:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "`list`, `get`, `create`, `update` or `delete`"
      capability:
        name: Capability
        type: string
        required: true
        description: "The one capability a request must be able to use"
      step_up:
        name: StepUp
        type: bool
        required: false
        description: "True: a destructive act, governed by architecture/admin's destructive-action-step-up"
      approval:
        name: Approval
        type: object
        required: false
        description: "Who must approve the act before it is applied (schemas/resource, Authority)"
      method:
        name: Method
        type: string
        required: true
        description: "The method the owner serves the operation at"
      path:
        name: Path
        type: string
        required: true
        description: "The path the owner serves it at: the route its `binds` names, or the uniform address. A `{name}` segment matches any one non-empty segment, as in PassRoute"
      filters:
        name: Filters
        type: "[]string"
        required: false
        description: "For `list`: the fields a list may be narrowed by, each by equality"
      items:
        name: Items
        type: string
        required: false
        description: "For a `list` served at a bound route: the member of its answer that holds the items. Absent: `items`, as ResourceList answers"

  ResourceVerb:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "The verb, kebab-case"
      capability:
        name: Capability
        type: string
        required: true
        description: "The one capability a request must be able to use"
      step_up:
        name: StepUp
        type: bool
        required: false
        description: "True: a destructive act"
      approval:
        name: Approval
        type: object
        required: false
        description: "Who must approve the act before it is applied"
      method:
        name: Method
        type: string
        required: true
        description: "The method the owner serves the verb at, POST unless a bound route says otherwise"
      path:
        name: Path
        type: string
        required: true
        description: "The path the owner serves it at"
      transition:
        name: Transition
        type: string
        required: false
        description: "The transition of `states` the verb fires"
      body:
        name: Body
        type: string
        required: false
        description: "The type of the request's body. Absent: the body is empty"
      preconditions:
        name: Preconditions
        type: "[]string"
        required: true
        description: "What the owner checks before acting"
      in_flight:
        name: InFlight
        type: object
        required: true
        description: "`handling` (`none`, `drains`, `cancels` or `continues`) and `says`"
      effect:
        name: Effect
        type: string
        required: true
        description: "What is true once it is answered"
      reversible:
        name: Reversible
        type: string
        required: true
        description: "`false`, or the verb of the kind that undoes it"

  ResourceRelation:
    fields:
      relation:
        name: Relation
        type: string
        required: true
        description: "A relation schemas/kinds declares from this kind"
      to:
        name: To
        type: string
        required: true
        description: "The kind of its target"
      field:
        name: Field
        type: string
        required: true
        description: "The field that holds the target's identity"

  ResourceUnavailable:
    fields:
      reason:
        name: Reason
        type: string
        required: true
        description: "One reason schemas/resource declares"
      says:
        name: Says
        type: string
        required: true
        description: "Why, in a sentence a client shows as it is"
```

### ResourceCatalogue

What `GET /v1/admin/resources` answers: every kind the tenant declares,
available or not ([`architecture/admin`](../architecture/admin.md#the-catalogue)).

```yaml
types:
  ResourceCatalogue:
    fields:
      kinds:
        name: Kinds
        type: "[]CatalogueEntry"
        required: true
        description: "One entry per declared kind, available or not, sorted by kind"
      corpus:
        name: Corpus
        type: string
        required: false
        description: "The corpus revision the declared kinds were read from, where the tenant's declared catalogue names one"

  CatalogueEntry:
    fields:
      kind:
        name: Kind
        type: string
        required: true
        description: "The kind"
      status:
        name: Status
        type: string
        required: true
        description: "`available` or `declared-unavailable`"
      reason:
        name: Reason
        type: string
        required: false
        description: "For `declared-unavailable`: one reason schemas/resource declares"
      says:
        name: Says
        type: string
        required: false
        description: "For `declared-unavailable`: why, in a sentence"
      declaration:
        name: Declaration
        type: ResourceDeclaration
        required: true
        description: "The kind's declaration: the registered owner's, where one is registered, and otherwise the tenant's declared one"
```

### ResourceList

What a `list` served at the uniform address answers. A list bound to an
existing route answers that route's own shape, and its declaration names the
member holding the items (`ResourceOperation.items`).

```yaml
types:
  ResourceList:
    fields:
      items:
        name: Items
        type: "[]object"
        required: true
        description: "The items, each of the kind's list type, no sensitive field among them"
      next_cursor:
        name: NextCursor
        type: string
        required: false
        description: "Where the next page starts. Absent or empty: there is none"
      has_more:
        name: HasMore
        type: bool
        required: true
        description: "Whether a next page exists"
```

### ResourceEvent

One change to one item, as the feed carries it. Its attributes are the
required and the `subject` and `time` attributes of CloudEvents 1.0, so a
general tool reads it without knowing Weblisk.

```yaml
types:
  ResourceEvent:
    fields:
      specversion:
        name: SpecVersion
        type: string
        required: true
        description: "`1.0`"
      id:
        name: ID
        type: string
        required: true
        description: "The event's id, unique at its owner"
      source:
        name: Source
        type: string
        required: true
        description: "The kind's uniform address, `/v1/admin/r/<kind>`"
      type:
        name: Type
        type: string
        required: true
        description: "`weblisk.<kind>.<event>`, the event one of the kind's declared events"
      subject:
        name: Subject
        type: string
        required: true
        description: "The item's identity"
      time:
        name: Time
        type: timestamp
        required: true
        description: "When the change happened"
      datacontenttype:
        name: DataContentType
        type: string
        required: true
        description: "`application/json`"
      data:
        name: Data
        type: map
        required: true
        description: "The fields that changed, by name, with their values now, no sensitive field among them. A `deleted` event carries none"
      position:
        name: Position
        type: string
        required: true
        description: "Where this event sits in its owner's feed of the kind: opaque, and only ever rising"
      traceparent:
        name: TraceParent
        type: string
        required: false
        description: "The W3C traceparent of the request or work that made the change ([TraceContext](#tracecontext))"

  ResourceEventPage:
    fields:
      events:
        name: Events
        type: "[]ResourceEvent"
        required: true
        description: "The events after the position asked for, in order, that the request may read"
      position:
        name: Position
        type: string
        required: true
        description: "The position to ask after next"
      gap:
        name: Gap
        type: bool
        required: true
        description: "True: the owner no longer holds every event after the position asked for, so the reader has missed some and reads the items again"
```

---

## Runs

What execution keeps of a run: one record per run, of every step it took and
every tool call each step made, with the model each step ran, what the backend
reported it used and cost, the decisions it recorded and the approvals it
waited on. The kinds are `run`, `run-step` and `tool-call`
([`schemas/kinds`](../schemas/kinds.md#declared-kinds)); how a person reads
and stops one is their Resources block, in
[`architecture/execution`](../architecture/execution.md#resources).

A run's record holds what its steps said. It is classified at the scope of the
work it ran on, and is answered only to a request that may receive that scope
([`patterns/scope`](../patterns/scope.md)). Nothing in it is a secret: a
credential a step used is named by the integration it came through, never
carried.

### Run

```yaml
types:
  Run:
    fields:
      uid:
        name: UID
        type: string
        required: true
        description: "The run's id, minted by execution: 32 lowercase hex characters, never reused"
      definition:
        name: Definition
        type: string
        required: true
        description: "What ran: the workflow's name, the task's action, or the operation or step an `agent:` instruction belongs to"
      definition_kind:
        name: DefinitionKind
        type: string
        required: true
        description: "What sort of thing `definition` names"
        enum: [workflow, task, agent-instruction]
      agent:
        name: Agent
        type: string
        required: false
        description: "The agent that ran it: a work agent, or the prompt worker for an `agent:` instruction. Absent while queued, and on a workflow run"
      owner:
        name: Owner
        type: string
        required: false
        description: "The identity id of the component whose definition it ran: a domain controller or the programme service"
      organisation:
        name: Organisation
        type: string
        required: false
        description: "The organisation the run's work belongs to"
      project:
        name: Project
        type: string
        required: false
        description: "The project, where the work belongs to one"
      schedule:
        name: Schedule
        type: string
        required: false
        description: "The uid of the registered start that fired it, where one did"
      chain:
        name: Chain
        type: "[]string"
        required: false
        description: "The runs that, through a `for` start, started it, oldest first. A row a run writes carries it, so that no run starts itself round a loop"
      muted:
        name: Muted
        type: bool
        required: false
        description: "True when the start that fired it was muted: what it produces reaches nobody"
      parent:
        name: Parent
        type: string
        required: false
        description: "The run that started this one, where one did"
      trigger:
        name: Trigger
        type: string
        required: true
        description: "What started it"
        enum: [schedule, event, person, run]
      triggered_by:
        name: TriggeredBy
        type: string
        required: false
        description: "Who or what: a person's identity id, an event's id, or the parent run's uid"
      status:
        name: Status
        type: string
        required: true
        description: "A state of the run's state machine"
        enum: [queued, running, waiting, completed, failed, cancelled, withheld]
      queued_at:
        name: QueuedAt
        type: timestamp
        required: true
      started_at:
        name: StartedAt
        type: timestamp
        required: false
      ended_at:
        name: EndedAt
        type: timestamp
        required: false
      usage:
        name: Usage
        type: RunUsage
        required: false
        description: "The sum of its steps' usage, over the steps whose backend reported one"
      error:
        name: Error
        type: ErrorResponse
        required: false
        description: "Why it failed, where it did"
      cancelled_by:
        name: CancelledBy
        type: string
        required: false
        description: "The identity id of the person who cancelled it"
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "The trace it ran under ([TraceContext](#tracecontext))"
```

### RunStep

One stage of a run: a workflow phase, a model's turn, a decision the run
recorded, or a wait on an approval.

```yaml
types:
  RunStep:
    fields:
      uid:
        name: UID
        type: string
        required: true
        description: "The step's id, minted by execution, never reused"
      run:
        name: Run
        type: string
        required: true
        description: "The run it is part of"
      seq:
        name: Seq
        type: int
        required: true
        description: "Its place in the run, from 1"
      step_type:
        name: StepType
        type: string
        required: true
        description: "What sort of stage it is"
        enum: [phase, model-turn, decision, approval, task]
      name:
        name: Name
        type: string
        required: false
        description: "A phase's name, as its definition declares it"
      status:
        name: Status
        type: string
        required: true
        enum: [pending, running, waiting, completed, failed, skipped]
      started_at:
        name: StartedAt
        type: timestamp
        required: false
      ended_at:
        name: EndedAt
        type: timestamp
        required: false
      backend:
        name: Backend
        type: string
        required: false
        description: "For a model's turn: the backend it ran on, as the tenant's model configuration names it"
      model:
        name: Model
        type: string
        required: false
        description: "For a model's turn: the model, as the backend reported it ran, never as it was asked for"
      usage:
        name: Usage
        type: RunUsage
        required: false
        description: "What the backend reported this turn used. Absent where it reported nothing, which is never read as zero"
      content:
        name: Content
        type: text
        required: false
        description: "What the step said: a model's answer, or a decision as the run stated it"
      reason:
        name: Reason
        type: text
        required: false
        description: "For a decision: the reason the run gave for it"
      approval:
        name: Approval
        type: string
        required: false
        description: "For an approval gated by an `ApprovalRequest`: its id"
      wait:
        name: Wait
        type: string
        required: false
        description: "For a `task` or `approval` step held for a person: the uid of the wait execution holds ([`architecture/execution`](../architecture/execution.md#a-persons-phase))"
      error:
        name: Error
        type: ErrorResponse
        required: false
      span_id:
        name: SpanID
        type: string
        required: false
        description: "The step's span ([TraceContext](#tracecontext))"
```

### RunToolCall

One call a step made to a tool: an owner's API, an MCP tool, a declared action.

```yaml
types:
  RunToolCall:
    fields:
      uid:
        name: UID
        type: string
        required: true
        description: "The call's id, minted by execution, never reused"
      run:
        name: Run
        type: string
        required: true
        description: "The run it was made in"
      step:
        name: Step
        type: string
        required: true
        description: "The step that made it"
      tool:
        name: Tool
        type: string
        required: true
        description: "The tool's name, as the step called it"
      provider_call_id:
        name: ProviderCallID
        type: string
        required: false
        description: "The id the model's backend gave the call, where it gave one. Not an identity here"
      arguments:
        name: Arguments
        type: map
        required: false
        description: "The arguments as the step sent them"
      outcome:
        name: Outcome
        type: string
        required: false
        description: "How it ended. `refused`: a boundary refused it before the tool ran"
        enum: [ok, error, refused]
      refused_with:
        name: RefusedWith
        type: string
        required: false
        description: "For `refused`: the code the boundary refused it with"
      result_digest:
        name: ResultDigest
        type: string
        required: false
        description: "The digest of what the tool answered, written sha256:<hex>"
      started_at:
        name: StartedAt
        type: timestamp
        required: true
      ended_at:
        name: EndedAt
        type: timestamp
        required: false
      span_id:
        name: SpanID
        type: string
        required: false
        description: "The call's span ([TraceContext](#tracecontext))"
```

### RunUsage

What a backend reported a turn used, with the token counts named as
[`patterns/api-ai`](../patterns/api-ai.md)'s `Usage` names them. A field the
backend did not report is absent, never zero; the tenant computes no cost from
a price list of its own, because a figure it made up would read as one the
backend charged.

```yaml
types:
  RunUsage:
    fields:
      prompt_tokens:
        name: PromptTokens
        type: int64
        required: false
        description: "Input tokens, as the backend reported them"
      completion_tokens:
        name: CompletionTokens
        type: int64
        required: false
        description: "Output tokens, as the backend reported them"
      total_tokens:
        name: TotalTokens
        type: int64
        required: false
        description: "Total tokens, as the backend reported them"
      cost:
        name: Cost
        type: RunCost
        required: false
        description: "What the backend reported the turn cost, where it reported a cost"

  RunCost:
    fields:
      amount:
        name: Amount
        type: string
        required: true
        description: "A decimal number, as the backend wrote it, so no rounding is introduced"
      currency:
        name: Currency
        type: string
        required: true
        description: "An ISO 4217 code"
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
        type: timestamp
        required: true
      updated_at:
        name: UpdatedAt
        type: timestamp
        required: true
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
        type: timestamp
        required: true
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
        required: true
        description: "The trace this task belongs to ([TraceContext](#tracecontext))"
      span_id:
        name: SpanID
        type: string
        required: true
        description: "The sender's span for this call ([TraceContext](#tracecontext))"
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
        type: timestamp
        required: true
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
        type: timestamp
        required: true
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
        description: "`critical`, `warning`, `info`. A finding's own scale: [Severity](#severity) is the one for enforcement, security and safety"
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
        type: timestamp
        required: true
      resolved_at:
        name: ResolvedAt
        type: timestamp
        required: false
```

---

## Approvals

### ApprovalRequest

A decision an owner holds open for a person: an operation that
[`patterns/safety`](../patterns/safety.md)'s gate held for `require_approval`
or `escalate`, or a change the tenant's change service planned
([`schemas/change`](../schemas/change.md)). It is defined here alone, so the
tenant has one queue of them: the decision inbox lists each owner's open
requests ([`architecture/admin`](../architecture/admin.md#decision-inbox)), and
a change awaiting approval is one of them. How a request is routed, escalated
and decided is [`patterns/approval`](../patterns/approval.md)'s; who may approve
a change is [`architecture/cli`](../architecture/cli.md#who-may-approve-a-change)'s.
A request holds exactly one of `intent_id` and `change_id`.

```yaml
types:
  ApprovalRequest:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Minted by the owner that holds the request"
      owner:
        name: Owner
        type: string
        required: true
        description: "The component that holds the request open and at which it is decided"
      intent_id:
        name: IntentID
        type: string
        required: false
        description: "The OperationIntent the safety gate held; absent for a change"
      change_id:
        name: ChangeID
        type: string
        required: false
        description: "The change awaiting approval (`schemas/change`); absent for an operation"
      requester:
        name: Requester
        type: string
        required: true
        description: "Identity id of who asked: an agent, a service or an operator. Separation of duties is judged against it"
      operation:
        name: Operation
        type: string
        required: true
        description: "What would be done, in words a person decides on"
      operation_class:
        name: OperationClass
        type: string
        required: false
        description: "`patterns/safety`'s class of the held operation; required with `intent_id`"
      resource_class:
        name: ResourceClass
        type: string
        required: false
        description: "`patterns/safety`'s criticality of its target; required with `intent_id`"
      scope:
        name: Scope
        type: string
        required: false
        description: "`patterns/scope`'s `ScopeLevel` of the target; required with `intent_id`"
      environment:
        name: Environment
        type: string
        required: true
        description: "`development`, `staging` or `production`"
      authority_required:
        name: AuthorityRequired
        type: string
        required: true
        description: "`patterns/approval`'s minimum authority level, set by routing"
      position:
        name: Position
        type: string
        required: false
        description: "For a knowledge change, the position its spec names as approver: the request is decided by a holder of it"
      development:
        name: Development
        type: bool
        required: false
        description: "True on a tenant flagged as a development tenant, the only place a requester may approve their own request; shown wherever the request is"
      justification:
        name: Justification
        type: string
        required: true
        description: "Why it is needed"
      urgency:
        name: Urgency
        type: string
        required: true
        description: "`normal`, `urgent` or `emergency`"
      requested_at:
        name: RequestedAt
        type: timestamp
        required: true
        description: "When the request was filed"
      expires_at:
        name: ExpiresAt
        type: timestamp
        required: true
        description: "When it expires undecided; an expired request is denied, never approved"
      correlation_id:
        name: CorrelationID
        type: string
        required: false
        description: "Trace id of the workflow, task or change run it belongs to"
      metadata:
        name: Metadata
        type: map
        required: false
        description: "Owner-specific context"
```

A request is answered by the decision made at the route its owner names, not
by a type of this file. The recommendation-decision body this type replaced
in 5.0.0, and the two types that answered it, are retired
([`RETIRED.md`](../RETIRED.md)); 5.0.0 is MAJOR because fields were removed
([`schemas/common`](../schemas/common.md#blueprint-versions), Blueprint Versions).

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
        type: timestamp
        required: true
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
        type: timestamp
        required: true
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "The trace this message belongs to ([TraceContext](#tracecontext))"
      span_id:
        name: SpanID
        type: string
        required: true
        description: "The sender's span for this message ([TraceContext](#tracecontext))"
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
      lease_state:
        name: LeaseState
        type: string
        required: true
        description: "What this component's lease says now: `ready`, `not_ready` or `unknown`. See [LeaseState](#leasestate)"
      lease_expires_at:
        name: LeaseExpiresAt
        type: timestamp
        required: true
        description: "The instant at which the lease lapses unless the component renews it. From then on `lease_state` is `unknown`"
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
      resources:
        name: Resources
        type: "[]ResourceDeclaration"
        required: false
        description: "The `resources` this component's manifest declared, as its registration recorded them. See [Resources](#resources)"
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
        type: timestamp
        required: true
        description: "The time of the last change, or one millisecond after the previous directory's when that is later, so it only ever rises (protocol/spec, POST /v1/services)"
      signature:
        name: Signature
        type: string
        required: false
        description: "The orchestrator's ML-DSA-65 signature (3309 bytes, base64url-encoded) over the fixed-form statement weblisk/directory/v2, which signs updated_at and the digest of the rest of the directory. Required on a push, which an agent refuses without it (protocol/spec, POST /v1/services)"
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
        type: timestamp
        required: true
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
        type: timestamp
        required: true
        description: "Token expiry"
      services:
        name: Services
        type: ServiceDirectory
        required: true
        description: "Current service directory"
      lease:
        name: Lease
        type: Lease
        required: true
        description: "The lease this registration grants, which the component renews at `POST /v1/lease`. See [Lease](#lease)"
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
        type: timestamp
        required: true
        description: "Expiry"
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
        type: timestamp
        required: true
        description: "The instant of creation"
      expires_at:
        name: ExpiresAt
        type: timestamp
        required: true
        description: "The instant of expiry"
```

---

## Health

"Health" means **liveness and readiness, and nothing else**. They answer two
questions, and each has one owner, with the semantics of Kubernetes probes and
leases:

| Question | Answered by | Read by |
|----------|-------------|---------|
| Is the process live, or must it be restarted? | `GET /livez`, served by the component ([Liveness](#liveness)) | the supervisor on its host that restarts it, and nothing else |
| Is it present, and ready to serve? | the lease the component renews with the orchestrator, carrying its readiness ([Lease](#lease), [LeaseRenewal](#leaserenewal)) | every other party, through the service directory ([LeaseState](#leasestate)) |

Neither carries a version, an uptime, metrics or the state of another
component. What a component was built from is its manifest; how it is serving
its users is telemetry's to judge
([`architecture/observability`](../architecture/observability.md)). **Nothing
polls an internal component to learn whether it is present**: the lease
already says, and a second answer reached by polling would be a second
presence fact that can disagree with the first.

### Liveness

```yaml
types:
  Liveness:
    fields:
      live:
        name: Live
        type: bool
        required: true
        description: "`true` with status 200; `false` with status 503"
```

`GET /livez` is served by every component, the orchestrator included, without
authentication and outside the `/v1` prefix, like a Kubernetes probe. It
answers 200 with `{"live": true}` while the process can still make progress,
and 503 with `{"live": false}` once it knows it cannot recover without a
restart. A component that does not answer is not live. It says nothing else:
no name, version, reason or dependency, because anyone who can reach the
listener can read it.

A liveness answer MUST NOT depend on another component, a store or a network
peer. Its reader restarts what fails it, so a dependency's outage that failed
liveness would restart every dependant and turn one fault into many.

### Readiness

```yaml
types:
  Readiness:
    fields:
      ready:
        name: Ready
        type: bool
        required: true
        description: "`true` with status 200; `false` with status 503"
```

A component is **ready** when it has finished starting, holds what it needs to
serve its endpoints (its keys, its store, and the orchestrator's key it verifies
tokens with) and is not draining for a shutdown. A component that cannot verify
a token is therefore **not ready**: one started with no orchestrator, or before
its registration returns that key, can serve nothing a token protects, however
long it runs ([`architecture/testing`](../architecture/testing.md) L4-04). It
says so in two places, and they are one fact:

- **On its lease.** Every renewal carries `ready` ([LeaseRenewal](#leaserenewal)),
  and that is where every other party reads it.
- **At `GET /readyz`**, served like `/livez`: without authentication, outside
  `/v1`, 200 with `{"ready": true}` or 503 with `{"ready": false}`, and nothing
  else. Its reader is the supervisor on the component's host while it waits for
  a start to complete ([`architecture/cli`](../architecture/cli.md)), and the
  probe of the orchestrator, which holds no lease of its own. No one reads it to
  learn whether a registered component is present.

---

## Presence

### LeaseState

| Value | Means |
|-------|-------|
| `ready` | The lease is current and its last renewal said `ready: true` |
| `not_ready` | The lease is current and its last renewal said `ready: false`: the component is starting, draining, or missing something it needs |
| `unknown` | The lease has lapsed, or the registration predates the orchestrator's last restart and no renewal has arrived since. The orchestrator does not know, and says so |

`unknown` is never read as `ready`, and never as failed: a lapsed lease means
the orchestrator has not heard, not that the component is down. There is no
`online`, `offline` or `degraded`.

### Lease

```yaml
types:
  Lease:
    fields:
      agent_id:
        name: AgentID
        type: string
        required: true
        description: "The registration the lease belongs to"
      duration:
        name: Duration
        type: int64
        required: true
        description: "Seconds the lease lasts from each renewal (`orchestrator.lease_duration`)"
      renewed_at:
        name: RenewedAt
        type: timestamp
        required: true
        description: "The instant of the registration or renewal that set it"
      expires_at:
        name: ExpiresAt
        type: timestamp
        required: true
        description: "The instant at which it lapses unless renewed"
```

A first registration grants the first lease (`RegisterResponse.lease`), with
the component's readiness taken as `ready: false` until its first renewal says
otherwise. What a re-registration does to a lease, and why it never carries a
readiness over a lapse or an orchestrator restart, is
[`protocol/spec`](spec.md#post-v1register)'s (§POST /v1/register, step 8).

### LeaseRenewal

```yaml
types:
  LeaseRenewal:
    fields:
      ready:
        name: Ready
        type: bool
        required: true
        description: "The component's readiness now, as `GET /readyz` would answer it"
      checks:
        name: Checks
        type: map
        required: false
        description: "Subsystem name → `ready` or `not_ready`: each subsystem's readiness, saying where the component is short, whether or not that makes it not ready. It never changes the lease state, which `ready` alone sets. Carried on the lease only, never served at `/readyz`"
      timestamp:
        name: Timestamp
        type: timestamp
        required: true
```

A component renews at `POST /v1/lease` ([`protocol/spec`](spec.md#post-v1lease))
as soon as its registration is answered, and from then on
at intervals no longer than a third of `duration`, so that two lost renewals
still leave the lease current. What the orchestrator does with a renewal,
one after a lapse included, is [`protocol/spec`](spec.md#post-v1lease)'s. A component that is draining renews with
`ready: false` until it deregisters.

What the directory and its leases are the authority for, and who may probe
whom, is [`architecture/orchestrator`](../architecture/orchestrator.md#presence)
§Presence's.

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
        type: timestamp
        required: true
        description: "When the record was written"
      last_seen:
        name: LastSeen
        type: timestamp
        required: false
        description: "The instant of the most recent token issued to this operator"
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
        type: timestamp
        required: true
        description: "The instant of the change that retired it. No attestation it signed vouches for anything recorded at or after this time, because the change revoked every credential it attested"
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
        type: timestamp
        required: false
        description: "Present when issued: the pass's exp, no more than 30 seconds after it was minted"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: false
        description: "Present when issued: the capabilities the pass carries, which are those scope named that the person may use now"
```

### WorkAuthorisation

A person's allowance for one registered component's definition to run with
nobody present, under that component's authority, held by the orchestrator
([`protocol/identity`](identity.md#the-work-pass)). It is
`patterns/principal-identity`'s agent authorisation for a service subject.

```yaml
types:
  WorkAuthorisation:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Minted by the orchestrator, never reused. A work pass carries it as `cid`"
      owner:
        name: Owner
        type: string
        required: true
        description: "The identity id of the registered component whose definition it covers, and whose authority the work uses"
      definition:
        name: Definition
        type: string
        required: true
        description: "The one definition it covers, as its owner names it. Opaque to the orchestrator; the owner checks it (protocol/identity, The work pass, rule 11)"
      actors:
        name: Actors
        type: "[]string"
        required: true
        description: "The identity ids of the registered components that may obtain a work pass under it, at least one"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: true
        description: "Its ceiling, by the names the Capability list gives them, at least one. None is person only or in the admin family, and none is token:exchange, work:exchange or work:authorise"
      authorised_by:
        name: AuthorisedBy
        type: string
        required: true
        description: "The identity id of the person who made it, or who last renewed it"
      created_at:
        name: CreatedAt
        type: timestamp
        required: true
      not_after:
        name: NotAfter
        type: timestamp
        required: true
        description: "When it ends: no more than 90 days after it was made or last renewed"
      status:
        name: Status
        type: string
        required: true
        description: "`active` or `revoked`. One past its not_after is answered `active` with that not_after, and mints nothing"
      revoked_at:
        name: RevokedAt
        type: timestamp
        required: false
      revoked_by:
        name: RevokedBy
        type: string
        required: false
        description: "The identity id of the person, or of the owner component, that revoked it"
      reason:
        name: Reason
        type: string
        required: false
        description: "Why it was revoked, as its revoker gave it"
```

### WorkAuthorisationRequest

What a person's client sends the orchestrator to make work authorisations,
one for each definition, in one act
(`POST /v1/admin/work-authorisations`, `architecture/admin`).

```yaml
types:
  WorkAuthorisationRequest:
    fields:
      owner:
        name: Owner
        type: string
        required: true
        description: "The identity id of the registered component whose definitions they cover"
      definitions:
        name: Definitions
        type: "[]WorkDefinitionCeiling"
        required: true
        description: "One entry for each definition to authorise, at least one"
      actors:
        name: Actors
        type: "[]string"
        required: true
        description: "The identity ids of the registered components that may act under each"
      not_after:
        name: NotAfter
        type: timestamp
        required: true
        description: "When each ends, no more than 90 days ahead"
```

### WorkDefinitionCeiling

```yaml
types:
  WorkDefinitionCeiling:
    fields:
      definition:
        name: Definition
        type: string
        required: true
        description: "The definition, as its owner names it"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: true
        description: "Its ceiling, at least one capability"
```

### WorkExchangeRequest

What an actor sends the orchestrator for a work pass (`POST /v1/token/work`,
`architecture/orchestrator`). The actor authenticates with its own
registration token, in the `Authorization` header and nowhere else.

```yaml
types:
  WorkExchangeRequest:
    fields:
      authorisation:
        name: Authorisation
        type: string
        required: true
        description: "The id of the work authorisation to act under"
      audience:
        name: Audience
        type: string
        required: true
        description: "The identity id of the one component the work pass is for: the fingerprint of the public key that component's directory entry carries"
      scope:
        name: Scope
        type: "[]string"
        required: true
        description: "The capabilities the request needs at that component. May be empty only where the audience is the authorisation's owner (protocol/identity, The work pass, rule 11)"
      run:
        name: Run
        type: string
        required: true
        description: "The id of the run the request belongs to, which the work pass carries for every receiver to record"
```

### WorkExchangeResponse

Every answer about the authorisation is a 200 carrying this, so a status other
than 200 only ever judged the actor's own request.

```yaml
types:
  WorkExchangeResponse:
    fields:
      issued:
        name: Issued
        type: bool
        required: true
        description: "True when a work pass was minted"
      code:
        name: Code
        type: string
        required: false
        description: "Present when issued is false: one of the work pass codes (Errors), or FORBIDDEN where the intersection is empty"
      pass:
        name: Pass
        type: string
        required: false
        description: "Present when issued: the work pass, a WLT of type work addressed to the audience (protocol/identity, The work pass)"
      expires_at:
        name: ExpiresAt
        type: timestamp
        required: false
        description: "Present when issued: the work pass's exp, no more than 30 seconds after it was minted"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: false
        description: "Present when issued: the capabilities the work pass carries"
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
        type: timestamp
        required: true
      actor:
        name: Actor
        type: string
        required: true
        description: "Who performed the action"
      via:
        name: Via
        type: string
        required: false
        description: "Where a pass carried the request, the identity id of the gateway that obtained it, the pass's act.identity_id (protocol/identity, The pass); where a work pass did, the actor's, its act.identity_id (The work pass). Absent, and omitted from the canonical JSON, otherwise"
      authorisation:
        name: Authorisation
        type: string
        required: false
        description: "Where a work pass carried the request, the work authorisation it was minted under, its cid. Absent, and omitted from the canonical JSON, otherwise"
      run:
        name: Run
        type: string
        required: false
        description: "Where a work pass carried the request, its run. Absent, and omitted from the canonical JSON, otherwise"
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
`model_agreement_withdraw`, and the work pass's `work_authorise`,
`work_authorisation_renew`, `work_authorisation_revoke`,
`work_authorisation_rekey` and `work_exchange`. The orchestrator's
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
        type: timestamp
        required: true
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "The trace this event belongs to ([TraceContext](#tracecontext))"
      span_id:
        name: SpanID
        type: string
        required: true
        description: "The publisher's span for this publish ([TraceContext](#tracecontext))"
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
        type: timestamp
        required: true
        description: "The instant of first attempt"
      last_attempt:
        name: LastAttempt
        type: timestamp
        required: true
        description: "The instant of final attempt"
      subscriber:
        name: Subscriber
        type: string
        required: true
        description: "Name of the subscriber that could not receive"
```

---

## Protocol Paths

All paths are prefixed with `/v1` but the two probes, `/livez` and `/readyz`,
which every component serves outside the protocol version, as Kubernetes
probes are, and which say nothing a version could change ([Health](#health)).

| Path | Method | Auth | Component | Purpose |
|------|--------|------|-----------|---------|
| `/v1/describe` | POST | no | agent | Return manifest |
| `/v1/execute` | POST | yes | agent | Execute task |
| `/v1/message` | POST | yes | agent | Synchronous request/response |
| `/v1/services` | POST | yes | agent | Receive service directory updates |
| `/v1/event` | POST | yes | agent | Receive event delivery (pub/sub) |
| `/v1/register` | POST | no | orchestrator | Agent registration |
| `/v1/register` | DELETE | yes | orchestrator | Agent deregistration |
| `/v1/services` | GET | yes | orchestrator | Service directory + routing table |
| `/v1/channel` | POST | yes | orchestrator | Broker channel |
| `/v1/lease` | POST | yes | orchestrator | Renew the caller's lease, carrying its readiness ([LeaseRenewal](#leaserenewal)) |
| `/livez` | GET | no | every component | Liveness, for the supervisor that restarts it ([Liveness](#liveness)) |
| `/readyz` | GET | no | every component | Readiness, for the supervisor waiting on a start and the probe of the orchestrator ([Readiness](#readiness)) |
| `/v1/audit` | GET | yes | orchestrator | Audit log |
| `/v1/rotate-key` | POST | yes | orchestrator | Key rotation (see identity.md) |
| `/v1/token/exchange` | POST | yes | orchestrator | Exchange the operator token a person has just presented to the admin gateway for a pass addressed to one component (`TokenExchangeResponse`). The admin gateway's alone |
| `/v1/token/work` | POST | yes | orchestrator | Mint a work pass under a work authorisation that names the caller as an actor (`WorkExchangeResponse`) |
| `/v1/work/authorisations` | GET | yes | orchestrator | The work authorisations that name the caller as owner or actor |
| `/v1/work/authorisations/{id}` | DELETE | yes | orchestrator | Revoke a work authorisation that names the caller as owner |
| `/v1/model/ceiling` | GET | yes | orchestrator | What a model backend may be sent now, and where it is reached. Platform-provided (architecture/orchestrator) |
| `/v1/model/complete` | POST | yes | orchestrator | A completion on the tenant's model for a registered component holding `llm:chat`, on its own registration token. Platform-provided, the model service's (architecture/model-service) |
| `/v1/model/audit` | POST | yes | orchestrator | Append a registered component's completion's entry to the audit log, for the model gateway inside the orchestrator's process alone (architecture/orchestrator) |

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
  - code: TOKEN_REQUEST_REPLAYED
    status: 401
    category: permanent
    retryable: false
    description: An attestation-token request whose jti the hub already recorded for that operator inside the replay window (architecture/admin, attestation-token-issuance). Nothing is issued. The client signs a new request with a fresh jti; the refusal is never a reason to register
  - code: STEP_UP_REQUIRED
    status: 401
    category: permanent
    retryable: false
    description: A destructive act arrived without the step-up it needs. Nothing changes. When it is answered, what it carries and how a client answers it are architecture/admin's destructive-action-step-up, stated nowhere else
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
  - code: CAPABILITY_GATEWAY_ONLY
    status: 403
    category: permanent
    retryable: false
    description: A registration manifest declares a capability this document marks admin gateway only (see Capability), and its key is not the one the tenant declared as its admin gateway's, or the tenant declared none. Nothing is recorded or issued
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
  - code: MODEL_UNAVAILABLE
    status: 503
    category: transient
    retryable: true
    description: The model a request names is on an unhealthy provider and no other provider lists it under the same name. No other model runs instead (patterns/api-ai, Provider Health-Aware Routing)
  - code: MODEL_BACKEND_LIMITED
    status: 429
    category: transient
    retryable: true
    description: The tenant's model backend refused a completion under its own rate or quota limit, and nothing ran. retry_after is the seconds until the backend said its window resets, and is absent where it said nothing; the model service sets no limit of its own (architecture/model-service, Limits)
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
  - code: DIRECTORY_STALE
    status: 409
    category: permanent
    retryable: false
    description: A pushed ServiceDirectory whose signature verifies but whose updated_at is lower than that of the directory the agent holds, or equal to it with a different digest. Nothing changes (protocol/spec, POST /v1/services)
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
  - code: RESOURCE_KIND_UNDECLARED
    status: 404
    category: permanent
    retryable: false
    description: The kind is not one the tenant's catalogue declares (schemas/resource)
  - code: RESOURCE_OPERATION_UNDECLARED
    status: 405
    category: permanent
    retryable: false
    description: The operation or verb is not one the kind's declaration names. Allow names what the address serves
  - code: RESOURCE_FIELD_NOT_SETTABLE
    status: 400
    category: permanent
    retryable: false
    description: A write names a field its declaration does not let a person set there. Nothing changes
  - code: RESOURCE_IF_MATCH_REQUIRED
    status: 428
    category: permanent
    retryable: false
    description: An update, a delete or a verb arrived with no If-Match
  - code: RESOURCE_PRECONDITION_FAILED
    status: 412
    category: permanent
    retryable: false
    description: If-Match does not equal the item's ETag now. Nothing changes; the answer carries the current ETag
  - code: SCOPE_NAME_TAKEN
    status: 409
    category: permanent
    retryable: false
    description: An organisation, or a project of the same organisation, has held that name, retired ones included. Nothing is recorded (architecture/orchestrator)
  - code: GRANT_SELF_REFUSED
    status: 403
    category: permanent
    retryable: false
    description: A grant made naming the person making it, or revoked by the person it names. Nothing changes (architecture/orchestrator)
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
  - code: WORKER_PROPOSAL_WITHHELD
    status: 409
    category: permanent
    retryable: false
    description: The prompt worker did not make a proposal an agent instruction asked for, because the run is muted. The proposal is kept, with its bytes, in the phase's outcome and nowhere else, and reaches no person. Recorded on the refused tool call; never an HTTP answer (architecture/prompt-worker, Muted runs)
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
        type: timestamp
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
        type: timestamp
        required: true
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
        type: timestamp
        required: true
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
        type: timestamp
        required: true
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

The one log envelope's fields. Everything else about a log record is
[`patterns/logging`](../patterns/logging.md)'s.

```yaml
types:
  LogEntry:
    fields:
      ts:
        name: Timestamp
        type: timestamp
        required: true
        description: "When the line was written, e.g. `2026-04-25T10:30:01.123Z`"
      level:
        name: Level
        type: string
        required: true
        description: "`debug`, `info`, `warn` or `error`"
      log_type:
        name: LogType
        type: string
        required: true
        description: "A type from `patterns/logging`'s Log Types, or a custom type a blueprint declares"
      msg:
        name: Message
        type: string
        required: true
        description: "Human-readable summary (max 256 characters)"
      component:
        name: Component
        type: string
        required: true
        description: "The component's name, as the service directory names it"
      component_type:
        name: ComponentType
        type: string
        required: true
        description: "`agent`, `domain`, or the architecture blueprint the component is built from"
      trace_id:
        name: TraceID
        type: string
        required: false
        description: "The trace being served when the line was written ([TraceContext](#tracecontext))"
      span_id:
        name: SpanID
        type: string
        required: false
        description: "The span open when the line was written"
      task_id:
        name: TaskID
        type: string
        required: false
        description: "The task being processed"
      domain:
        name: Domain
        type: string
        required: false
        description: "The domain being operated within"
      workflow:
        name: Workflow
        type: string
        required: false
        description: "The workflow being executed"
      action:
        name: Action
        type: string
        required: false
        description: "The action being processed"
      duration_ms:
        name: DurationMS
        type: int64
        required: false
        description: "On completion of an operation"
      status:
        name: Status
        type: string
        required: false
        description: "On completion of an operation: `success`, `failed` or `timeout`"
      error:
        name: Error
        type: string
        required: false
        description: "Error message (when level is error)"
      error_code:
        name: ErrorCode
        type: string
        required: false
        description: "Structured error code"
      details:
        name: Details
        type: map
        required: false
        description: "Data typed by `log_type`, as `patterns/logging` declares for each"
```

### TraceContext

The trace a request belongs to, and the span within it that sent the request:
W3C Trace Context's. On an HTTP request it is the `traceparent` header,
`00-<trace_id>-<span_id>-<trace_flags>`, where `<trace_flags>` is `01` when the
trace is sampled and `00` when it is not. In a `TaskContext`, `AgentMessage` or
`EventEnvelope` it is that envelope's `trace_id` and `span_id`. Which requests
carry it, and what a receiver does with what arrives, are
[`protocol/spec`](spec.md#trace-propagation)'s, stated there once.

```yaml
types:
  TraceContext:
    fields:
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "32 lowercase hex characters (16 random bytes), never all zeros"
      span_id:
        name: SpanID
        type: string
        required: true
        description: "16 lowercase hex characters (8 random bytes), never all zeros"
      parent_span_id:
        name: ParentSpanID
        type: string
        required: false
        description: "The span that sent the request this span serves. Absent on a trace's first span"
      sampled:
        name: Sampled
        type: bool
        required: false
        description: "Whether this trace's spans are recorded: `traceparent` flags `01` is true and `00` is false (default: true)"
```

### Span

One operation a component performed within a trace, shaped as an
OpenTelemetry span: each field is the OpenTelemetry field of the same name,
`component` is the resource's `service.name`, and `start` and `end` become
`start_time_unix_nano` and `end_time_unix_nano` when pushed as OTLP. When a
span opens and closes, and what it is named, are
[`architecture/observability`](../architecture/observability.md#distributed-tracing)'s.

```yaml
types:
  Span:
    fields:
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "The trace this span belongs to ([TraceContext](#tracecontext))"
      span_id:
        name: SpanID
        type: string
        required: true
        description: "This span's id ([TraceContext](#tracecontext))"
      parent_span_id:
        name: ParentSpanID
        type: string
        required: false
        description: "The span that sent the request this span serves"
      name:
        name: Name
        type: string
        required: true
        description: "A span name `architecture/observability` declares"
      kind:
        name: Kind
        type: string
        required: true
        description: "`server`, `client`, `producer`, `consumer` or `internal`, as OpenTelemetry's SpanKind"
      component:
        name: Component
        type: string
        required: true
        description: "The component that performed it, as the service directory names it"
      start:
        name: Start
        type: timestamp
        required: true
      end:
        name: End
        type: timestamp
        required: true
      status:
        name: Status
        type: string
        required: true
        description: "`unset`, `ok` or `error`, as OpenTelemetry's status code"
      attributes:
        name: Attributes
        type: map
        required: false
        description: "The attributes its name declares, under OpenTelemetry semantic conventions where one exists"
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
        description: "The trace this task ran under, kept as a record and never a carrier ([TraceContext](#tracecontext))"

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

- [ ] Every ID, span id and timestamp is the form [Conventions](#conventions), [TraceContext](#tracecontext) and [`protocol/conventions`](conventions.md#instant) give it
- [ ] Signatures and public keys serialize as base64url ML-DSA-65 of the lengths [Conventions](#conventions) gives
- [ ] ErrorResponse carries the fields [ErrorResponse](#errorresponse) declares under its exact JSON keys, `error` required
- [ ] Error categories are only those [ErrorResponse](#errorresponse) lists, and each standard error code answers with the HTTP status [Error Handling](#error-handling) gives it
- [ ] Unknown JSON fields are ignored on deserialization and optional fields are omitted when empty, as [Conventions](#conventions) says
- [ ] AgentManifest requires the fields [AgentManifest](#agentmanifest) marks required, and carries `publishes` and `subscriptions` for the event system
- [ ] EventEnvelope requires every field [EventEnvelope](#eventenvelope) marks required
- [ ] Subscription requires `pattern`, and `scope` and `group` take the defaults [Subscription](#subscription) gives them
- [ ] RouteEntry requires every field [RouteEntry](#routeentry) marks required
- [ ] ServiceDirectory carries every field [ServiceDirectory](#servicedirectory) marks required
- [ ] WorkflowPhase `on_error` takes only the values [WorkflowPhase](#workflowphase) lists, and `max_attempts` applies only when `on_error` is `"retry"` ([`patterns/workflow`](../patterns/workflow.md#declaration-fields))
- [ ] WorkflowExecution `status` takes only the states, and moves only by the transitions, of [`patterns/workflow`](../patterns/workflow.md#workflow-state-machine); PhaseResult `status` adds `skipped` ([PhaseResult](#phaseresult))
- [ ] TaskRequest requires every field [TaskRequest](#taskrequest) marks required, and TaskResult `status` is one of the values [TaskResult](#taskresult) lists
- [ ] AgentMessage `signature` covers what [AgentMessage](#agentmessage) says it covers, canonicalized per RFC 8785
- [ ] Finding carries every field [Finding](#finding) marks required
- [ ] RegisterResponse carries every field [RegisterResponse](#registerresponse) marks required, `protocol_version` the negotiated one
- [ ] ServiceEntry carries `lease_state` and `lease_expires_at`, and `lease_state` is one of the values [LeaseState](#leasestate) gives ([ServiceEntry](#serviceentry))
- [ ] A lease past its `expires_at` reads `unknown`, never `ready` ([LeaseState](#leasestate))
- [ ] Lease and LeaseRenewal carry every field [Lease](#lease) and [LeaseRenewal](#leaserenewal) mark required, and a renewal's `checks` are never served at `/readyz`
- [ ] `GET /livez` answers as [Liveness](#liveness) says: without authentication, no other member, and depending on no other component
- [ ] `GET /readyz` answers as [Readiness](#readiness) says: without authentication and no other member
- [ ] ChannelGrant carries every field [ChannelGrant](#channelgrant) marks required, `channel_token` scoped
- [ ] Every protocol path, its prefix, method and auth, is as the [Protocol Paths](#protocol-paths) table gives it
- [ ] DeadLetterEntry carries every field [DeadLetterEntry](#deadletterentry) marks required
- [ ] PolicyDecision requires every field [PolicyDecision](#policydecision) marks required, and `decision` is a [DecisionResult](#decisionresult)
- [ ] OperationIntent requires every field [OperationIntent](#operationintent) marks required, and `operation` takes every class it lists, `list` and `query` among them
- [ ] IntentDecision requires every field [IntentDecision](#intentdecision) marks required, and `decision` is a [DecisionResult](#decisionresult)
- [ ] EnforcementDecision requires every field [EnforcementDecision](#enforcementdecision) marks required, and `boundary` takes every value it lists, `response` among them
- [ ] DecisionResult takes only the values [DecisionResult](#decisionresult) gives, compared by ordinal
- [ ] Severity takes only the values [Severity](#severity) gives, used alike by enforcement, security and safety
- [ ] Policy, safety and enforcement decisions resolve to a DecisionResult by the [Decision Mapping](#decision-mapping) table, most restrictive winning ([Decision Taxonomy](#decision-taxonomy))
- [ ] Every protocol-level error code is registered centrally and agent-local codes do not collide with it, as [Error Code Conventions](#error-code-conventions) says
- [ ] Every code a `TokenExchangeResponse` may carry in `code` ([TokenExchangeResponse](#tokenexchangeresponse)) is registered here with its HTTP status ([Errors](#errors), [Error Handling](#error-handling)), so the admin gateway, refusing a request whose token the exchange refused, answers with that status and never a guessed one
- [ ] `PASS_REQUIRED` and `PASS_AUDIENCE_MISMATCH` are registered with status 401 ([Errors](#errors)), and `token:exchange` is in the [Capability](#capability) list
- [ ] `STEP_UP_REQUIRED` is registered with status 401 in the error table ([Errors](#errors)) and in [Error Handling](#error-handling), and every component that serves a destructive act answers it <!-- wl:check step-up-code-registered covers step-up-required-registered -->
- [ ] `ADDRESS_CONFLICT` is registered with status 409, beside `NAMESPACE_CONFLICT` ([Error Handling](#error-handling))
- [ ] `token:exchange` is marked *admin gateway only* ([Capability](#capability)), and `CAPABILITY_GATEWAY_ONLY` is registered with status 403 in [Error Handling](#error-handling) <!-- wl:check gateway-only-registered covers gateway-only-capability -->
- [ ] `content:declassify` is in the Content capabilities and marked *person only*, so a registration whose manifest declares it is refused with `CAPABILITY_PERSON_ONLY` ([Capability](#capability))
- [ ] Administrative authority is expressed as `admin:` capabilities in the standard list, not as a separate role model, and `admin:*` denotes the whole family ([Capability](#capability))
- [ ] Every capability bullet in [Capability](#capability) names exactly one owner in brackets, and no capability name is listed twice
- [ ] Each capability [Capability](#capability) marks *person only* is person only and no other is, `programme:switch`, `integration:manage`, `action:invoke` and `scope:admit` among the first
- [ ] The capabilities [Capability](#capability) places outside the `admin` family, `telemetry:read`, `action:invoke` and `scope:admit` among them, are carried by no `admin:*`
- [ ] `content:connect` binds an integration to an outside destination and creates no credential ([Capability](#capability))
