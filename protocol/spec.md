<!-- blueprint
type: protocol
name: spec
version: 4.0.0
requires: [protocol/types, protocol/identity, protocol/conventions]
platform: any
tier: free
-->

# Weblisk Agent Protocol Specification

The universal wire protocol for all Weblisk agents and orchestrators.
Every implementation — regardless of language or platform — MUST conform
to this specification exactly. All communication is HTTP + JSON.

## Overview

The Weblisk Agent Protocol defines how autonomous agents register with
an orchestrator, discover each other, publish and receive events, execute
tasks, and communicate directly. The protocol uses HTTP as the sole
transport — pub/sub semantics are achieved through scoped event delivery
over standard HTTP endpoints.

**Key design principles:**

1. **One protocol** — HTTP is the only communication layer. No separate
   message broker, queue, or bus infrastructure.
2. **Event-driven** — Agents coordinate through namespaced, scoped events
   delivered via HTTP POST. Workflows, tasks, and lifecycle loops are
   all event-driven.
3. **Namespace ownership** — Every event namespace is exclusively owned
   by one agent. The orchestrator enforces this at registration,
   preventing collisions.
4. **Scoped delivery** — Events carry a `scope` field that limits
   delivery to the intended recipient. Agents only receive events
   addressed to them unless they have explicit permission to observe
   globally.
5. **Separation of concerns** — The orchestrator manages agent
   lifecycle, discovery, trust, and namespace control. It does NOT
   execute tasks, manage workflows, or store business state.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=3.0.0 <7.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, version, description, url, public_key, capabilities, inputs, outputs, collaborators, approval, max_concurrent, publishes, subscriptions, pass_routes]
        - name: PassRoute
          fields_used: [method, path, capabilities, body]
        - name: BodyRequirement
          fields_used: [field, equals, capabilities]
        - name: TaskRequest
          fields_used: [id, from, action, payload, context, token, signature, timestamp]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, changes, observations, recommendations, metrics, signature, timestamp]
        - name: AgentMessage
          fields_used: [id, from, to, type, action, payload, token, signature, timestamp, trace_id, span_id]
        - name: EventEnvelope
          fields_used: [event_id, topic, source, scope, correlation_id, timestamp, trace_id, span_id, version, payload, token]
        - name: TaskContext
          fields_used: [trace_id, span_id]
        - name: TraceContext
          fields_used: [trace_id, span_id, parent_span_id, sampled]
        - name: ErrorResponse
          fields_used: [error, code, category, retryable, detail]
        - name: ServiceDirectory
          fields_used: [services, routing_table, namespaces, updated_at, signature]
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: RegisterResponse
          fields_used: [agent_id, token, expires_at, services, lease, orchestrator, protocol_version]
        - name: ChannelRequest
          fields_used: [from_agent, to_agent, purpose, token, signature]
        - name: ChannelGrant
          fields_used: [channel_id, from_agent, to_agent, target_url, target_pub_key, channel_token, expires_at, signature]
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: Lease
          fields_used: [agent_id, duration, renewed_at, expires_at]
        - name: LeaseRenewal
          fields_used: [ready, checks, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.8.0 <4.0.0"
    bindings:
      types:
        - name: SigningKeyPair
          fields_used: [public_key, private_key]
        - name: WLToken
          fields_used: [header, payload, signature]
      endpoints:
        - path: /v1/register
          methods: [POST]
          request_type: RegisterRequest
          response_fields: [agent_id, token, services, orchestrator, protocol_version]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/conventions
    version: ">=1.0.0 <2.0.0"
    bindings:
      behaviors:
        - name: instant
        - name: uuid
        - name: duration
        - name: integer
        - name: max-attempts
        - name: backoff
        - name: path-param
        - name: task-timeout
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```


Every type this specification references is declared in
[protocol/types.md](types.md) and bound above. This blueprint declares none of
its own: a second statement of a type is a second thing to keep right.

---

## Conventions

- All paths are prefixed with `/v1`, but the two probes `/livez` and `/readyz`
  ([Probes](#get-livez-and-get-readyz))
- All request/response bodies are `application/json`
- Timestamps and IDs take the forms [types.md](types.md#conventions) states
- All signatures are base64url-encoded ML-DSA-65 signatures (3309 bytes decoded)
- All public keys are base64url-encoded ML-DSA-65 public keys (1952 bytes decoded)
- Errors return `ErrorResponse` JSON (see [types.md](types.md)); at minimum `{"error": "message"}`
- Event IDs use UUID v7 (time-sortable, 32 hex chars when formatted
  without hyphens)
- Unknown JSON fields MUST be ignored (forward compatibility)
- Request bodies MUST be limited: 1 MB default, 10 MB for task execution

---

## Agent Endpoints

Every agent MUST serve these 5 endpoints on a single HTTP port, beside the
two probes every component serves ([Probes](#get-livez-and-get-readyz)).
All five use POST for uniformity — this simplifies agent
implementation (a single HTTP handler dispatch) and avoids URL-encoded
query strings for future payload extensions on `/v1/describe`.

### POST /v1/describe

Returns the agent's identity, capabilities, event subscriptions, and
namespace ownership. No auth required.

**Response:** `AgentManifest` (see [types.md](types.md))

```json
{
  "name": "seo-analyzer",
  "type": "agent",
  "version": "1.0.0",
  "description": "Scans HTML files and analyzes SEO metadata",
  "url": "http://localhost:9710",
  "public_key": "<64-char hex ML-DSA-65 public key>",
  "capabilities": [
    {"name": "file:read", "resources": ["app/**/*.html"]},
    {"name": "llm:chat", "resources": []},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [
    {"name": "html_files", "type": "file_list", "description": "HTML files to analyze"}
  ],
  "outputs": [
    {"name": "seo_report", "type": "json", "description": "SEO analysis with proposed changes"}
  ],
  "collaborators": ["a11y-checker"],
  "approval": "required",
  "max_concurrent": 5,
  "publishes": [],
  "subscriptions": []
}
```

### POST /v1/execute

Executes a task synchronously. Requires auth token in the request body.

**Request:** `TaskRequest`
**Response:** `TaskResult`

The agent MUST:
1. Validate the request has a non-empty `id` and `token`, and a `context`
   carrying `trace_id` and `span_id`
2. Update internal service directory from `context.services` (if provided)
3. Execute domain-specific logic
4. Return result with `task_id` matching request `id`
5. Sign the result with the agent's private key

This endpoint is for direct, synchronous task execution. It is called
by the Task Agent when dispatching queued work, or directly by other
agents for immediate execution. The caller blocks until the result
is returned.

**Request example:**

```json
{
  "id": "a1b2c3d4e5f6...",
  "action": "analyze",
  "target": "seo-analyzer",
  "input": {"html_files": ["index.html", "about.html"]},
  "context": {
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "span_id": "00f067aa0ba902b7",
    "correlation_id": "corr-789",
    "services": {}
  },
  "token": "<WLT auth token>",
  "signature": "<hex ML-DSA-65 signature>",
  "timestamp": "2024-04-03T16:00:00.000Z"
}
```

**Response example:**

```json
{
  "task_id": "a1b2c3d4e5f6...",
  "agent_name": "seo-analyzer",
  "status": "success",
  "summary": "Scanned 5 files, proposing 3 improvements",
  "changes": [...],
  "observations": [...],
  "recommendations": [...],
  "metrics": {"files_scanned": 5, "suggestions": 3},
  "signature": "<hex ML-DSA-65 signature>",
  "timestamp": "2024-04-03T16:00:01.000Z"
}
```

### GET /livez and GET /readyz

The two probes. Every component serves them, the orchestrator included, on its
own listener, without authentication and outside the `/v1` prefix. They are
the only routes a component serves outside it.

| Route | Answers | Read by |
|-------|---------|---------|
| `GET /livez` | [`Liveness`](types.md#liveness): 200 `{"live": true}`, or 503 `{"live": false}` | the supervisor on the component's host, which restarts a component that fails it |
| `GET /readyz` | [`Readiness`](types.md#readiness): 200 `{"ready": true}`, or 503 `{"ready": false}` | the supervisor while it waits for a start to complete; the probe of the orchestrator |

Neither answer carries anything else. What each value means, and the rule that
liveness depends on no other component, are
[`protocol/types`](types.md#health)'s. A registered component's readiness
travels on its lease ([`POST /v1/lease`](#post-v1lease)), and nothing reads
`/readyz` to learn whether a registered component is present.

### POST /v1/message

Direct agent-to-agent messaging for synchronous request/response.

**Request:** `AgentMessage` (type: `request`)
**Response:** `AgentMessage` (type: `response`)

Use `/v1/message` when the caller needs a response. For fire-and-forget
event delivery, use `/v1/event` instead.

The agent MUST:
1. Accept only POST requests
2. Validate the message carries `trace_id` and `span_id`
3. If signature is present AND sender's public key is known from the
   service directory, verify the signature
4. Dispatch to the appropriate message handler based on `action`
5. Sign the response

Signature covers: `canonicalize({from, to, action, payload})` per
[RFC 8785 (JCS)](https://www.rfc-editor.org/rfc/rfc8785) — see
[identity.md](identity.md#sign-json) for the canonical JSON requirement.

**Request example:**

```json
{
  "from": "content-analyzer",
  "to": "seo-analyzer",
  "action": "check-overlap",
  "type": "request",
  "payload": {"url": "/blog/post-1", "keywords": ["seo", "performance"]},
  "signature": "<hex ML-DSA-65 signature>",
  "timestamp": "2024-04-03T16:00:00.000Z",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7"
}
```

### POST /v1/services

Accepts service directory and routing table updates pushed by the
orchestrator. The agent MUST update its internal service list and
routing table (thread-safe), from the body, or from
[`GET /v1/services`](#get-v1services), which it MAY read on its own token
when a push arrives instead of reading the body. Response: 200 OK (no body
required).

**Request:** `ServiceDirectory` (now includes `routing_table` and
`namespaces` — see [types.md](types.md))

**The push is signed.** The orchestrator signs each directory it pushes with
its signing key, the key whose public half its
registration answer gives as `orchestrator.public_key`
([`protocol/types`](types.md#orchestratorinfo)), and sends the signature, as
[Sign](identity.md#sign) gives it, in `ServiceDirectory.signature`. What it
signs is a [fixed-form statement](identity.md#fixed-form-statements):

```
"weblisk/directory/v2" 0x00 <updated_at> 0x00 <digest>

<updated_at>  the directory's updated_at, as protocol/conventions:instant
              writes it
<digest>      "sha256:" and the lowercase hex SHA-256 of the directory's
              canonical form, canonicalize(directory) per RFC 8785
              (identity.md, Sign JSON), with its signature member left out
```

The layout carries `updated_at` as an instant is written on the wire
(`protocol/conventions:instant`). `weblisk/directory/v1` carried it as a count of seconds;
that change of layout took this prefix, since a prefix names one layout for good
([`protocol/identity`](identity.md#fixed-form-statements)), and v1 is retired
([`RETIRED.md`](../RETIRED.md)).

<!-- wl:id directory-push-signed -->
- The orchestrator MUST sign every directory it pushes and every directory it
  answers [`GET /v1/services`](#get-v1services) with. It MUST give a directory
  that differs from the last it signed an `updated_at` greater than that of
  every directory it signed before, so no two different directories it signs
  carry the same `updated_at`: the time of the change, or one millisecond after
  the last `updated_at` it signed, whichever is later. It MUST keep that last
  value in its storage, so neither a restart nor a clock that steps back makes
  it sign a lower one; without it, every agent would refuse its pushes as
  stale until the clock caught up.
<!-- wl:id directory-push-refuse-unsigned -->
- An agent that takes a pushed body as its directory MUST first rebuild the
  statement from that body, the `updated_at` it carries and the digest of its
  canonical form as received, and verify `signature` over those bytes under
  the orchestrator public key its most recent registration answer carried
  ([Verify Signature](identity.md#verify-signature)). It MUST refuse a body
  with no `signature`, one whose signature does not verify, and any body when
  it holds no orchestrator key, with 401 `INVALID_SIGNATURE`, and change
  nothing.
<!-- wl:id directory-push-refuse-stale -->
- It MUST refuse with 409 `DIRECTORY_STALE`, and change nothing, a verified
  directory whose `updated_at` is lower than that of the directory it holds,
  or equal to it with a different digest. An equal `updated_at` with the same
  digest is the directory it holds, answered 200.
<!-- wl:id directory-push-seeded -->
- An agent that holds no directory yet, as when it has just started, MUST NOT
  take one from a push: it reads [`GET /v1/services`](#get-v1services) at its
  anchor first, and judges later pushes against what that read answered.
  Otherwise any directory the orchestrator ever signed, however old, would be
  newer than the nothing it holds.
- A refusal is never the end of the agent's directory: an agent that refused
  a push may read [`GET /v1/services`](#get-v1services) on its own token, as
  it may on any push. An agent that reads the directory that way takes
  nothing from the body, and need not verify it.

The digest is over the whole directory, so a signature over one directory is
never valid for another, and the `updated_at` order is what keeps a directory
the orchestrator once signed from replacing a later one. A pushed directory
says no more than one read from the orchestrator says
([`architecture/orchestrator`](../architecture/orchestrator.md#what-the-directory-attests-and-what-it-does-not)):
the signature proves that the orchestrator published it, not that the
addresses in it are the tenant's.

What the order does not stop is a replay of a directory newer than the one an
agent holds and older than the current one. An agent that missed the pushes
after the directory it holds takes any of them that a party who recorded it
sends, a directory naming an address a component has since given up
included, until the next push or its periodic read of `GET /v1/services`
(Implementation Notes) brings it the current one. That window is the
residual, and the periodic read is what bounds it.

**Compatibility.** An agent built to this version refuses every push from an
orchestrator that does not sign one, and an orchestrator built to it signs
pushes that an earlier agent ignores. Neither pairing loses the directory:
every agent already reads `GET /v1/services` periodically (Implementation
Notes), so a refused push costs the time until that read and nothing else.
That is why signing the push is a minor version of this protocol and not a
major one.

> **Gap — a task's `context.services` is not signed.** A task's
> `context.services`, from which [`POST /v1/execute`](#post-v1execute) step 2
> updates the same list, is whatever the task's caller sent. The admin
> gateway refuses every task, so it takes none, and it reads the directory
> only by `GET /v1/services` at its anchor
> ([`architecture/admin`](../architecture/admin.md#contracts),
> `admin-gateway-authorization`).

### POST /v1/event

Receives event deliveries from other agents via HTTP-based pub/sub.
Requires auth token in the event envelope.

**Request:** `EventEnvelope`
**Response:** 200 OK (no body required — fire-and-forget acknowledgment)

The agent MUST:
1. Accept only POST requests
2. Validate the `EventEnvelope` structure (event_id, topic, source,
   scope, timestamp, trace_id, span_id, payload are present)
3. Verify the event's auth token (optional — framework-level)
4. Check idempotency: if `event_id` has already been processed,
   return 200 OK immediately (skip duplicate processing)
5. Match the event's `topic` against registered event handlers
6. Dispatch to the matching handler(s)

**Request example:**

```json
{
  "event_id": "evt-a1b2c3d4",
  "topic": "workflow.completed",
  "source": "workflow",
  "scope": "seo",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "payload": {"workflow_id": "wf-123", "status": "success", "duration_ms": 4500},
  "token": "<WLT auth token>",
  "timestamp": "2024-04-03T16:00:00.000Z"
}
```
7. Return 200 OK immediately — event processing is asynchronous
   from the HTTP response. The publisher does not wait for processing
   to complete.

If the agent cannot accept events (at capacity), it MUST return
`429 Too Many Requests` with a `Retry-After` header. The publishing
agent's framework will retry delivery.

```json
{
  "event_id": "evt-a1b2c3d4e5f6",
  "topic": "workflow.completed",
  "source": "workflow",
  "scope": "seo",
  "correlation_id": "wf-exec-001",
  "timestamp": "2024-04-03T16:00:01.000Z",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "version": "1.0.0",
  "payload": {
    "workflow": "seo-audit",
    "status": "completed",
    "result": { ... }
  },
  "token": "<auth token>"
}
```

---

## Orchestrator Endpoints

The orchestrator manages agent lifecycle, presence (each component's
lease), service discovery, namespace control, event routing, channel brokering, and audit. It does NOT
execute tasks, run workflows, manage strategies, or store observations.
Those concerns belong to dedicated infrastructure agents.

### POST /v1/register

Agent registration. No auth required (this is how agents GET auth).

**Request:** `RegisterRequest`
**Response:** `RegisterResponse`

The orchestrator MUST:
1. Validate: `manifest.name`, `manifest.url`, `manifest.public_key` are non-empty.
   Refuse with 403 `CAPABILITY_PERSON_ONLY` if `manifest.capabilities` names a
   capability [`protocol/types`](types.md) marks *person only*. A registered
   component is a service, and a service never holds one
   ([`patterns/principal-identity`](../patterns/principal-identity.md),
   `service-subject-constraints`). The token of step 7 would otherwise carry it.
   Refuse with 403 `CAPABILITY_GATEWAY_ONLY` if `manifest.capabilities` names
   a capability `protocol/types` marks *admin gateway only*
   ([`protocol/types`](types.md#capability)) and the fingerprint of
   `manifest.public_key` is not the one the tenant declared as its admin
   gateway's, or the tenant declared none
   ([`architecture/admin`](../architecture/admin.md#registration-lease-and-identity)).
   Refuse with 400 `INVALID_REQUEST`, before anything is recorded, a manifest
   that names a capability `protocol/types` does not list, in `capabilities`
   or in a pass route (`pass_routes`, its `capabilities` or a body
   requirement), and one two of whose pass routes can match one request.
   [`architecture/orchestrator`](../architecture/orchestrator.md#registration-flow-post-v1register),
   step 1 of its notes, says when two can. Refuse with 409 `ADDRESS_CONFLICT`,
   before anything is recorded, a manifest whose `url` contradicts the
   address the tenant declared for that component;
   [`architecture/orchestrator`](../architecture/orchestrator.md#what-the-directory-attests-and-what-it-does-not)
   says when one does, and that no tenant can declare one yet
2. Verify `signature` against `manifest.public_key` over `canonicalize(manifest)` per RFC 8785,
   canonicalizing the manifest **as received** — see [Signing input](#signing-input) below
3. Reject if `|server_time - timestamp|` > 300 seconds (replay protection)
4. **Validate namespace ownership** (see Namespace Control below):
   a. For each namespace in `manifest.publishes`:
      - If the namespace is already owned by a DIFFERENT agent → 409 Conflict
      - If the namespace is `system` → 403 Forbidden (reserved for orchestrator)
   b. Record namespace → agent mapping in registry
5. **Build routing table entries** from `manifest.subscriptions`:
   a. For each subscription, validate scope:
      - `"self"` → always allowed
      - `"*"` → requires `event:observe` capability → 403 if missing
      - `"<agent-name>"` → agent must be in `manifest.collaborators` or
        the named agent must list this agent in its collaborators → 403 otherwise
   b. Add subscription entries to the routing table
6. Generate unique `agent_id` (32 hex chars)
7. Issue auth token (WLT format) with capabilities from manifest, `identity_id`
   the fingerprint of `manifest.public_key`
   ([`protocol/identity`](identity.md#payload-claims)), 24-hour TTL
8. Store agent in registry, and grant its first lease: `duration` from
   `orchestrator.lease_duration`, read as `not_ready` until the first renewal
   ([`POST /v1/lease`](#post-v1lease)). A re-registration of a registered
   agent with an unchanged manifest, which is how a token is renewed, changes
   no current lease: its last renewal and its `expires_at` stay as they were,
   so only a renewal moves a lease on. A re-registration with a changed
   manifest, or over a lease that has lapsed, or over one that was granted or
   last renewed before the orchestrator last started, is granted a lease as a
   first registration is, read as `not_ready` until its first renewal: no
   readiness from before a deployment, a lapse or an orchestrator restart is
   carried over. A component renews as soon as its registration is answered
   ([`protocol/types`](types.md#leaserenewal)), which is what keeps a
   component restarted with an unchanged manifest from reading the old
   process's readiness for longer than that first renewal takes
9. Log audit entry: actor=orchestrator, action=register, target=agent_name
10. Respond with `RegisterResponse` (includes routing table and the lease)
11. Asynchronously broadcast updated `ServiceDirectory` (with routing table),
    signed as [`POST /v1/services`](#post-v1services) states, to ALL OTHER
    agents via `POST /v1/services`

> **Gap — a registration is not yet an enrolment.** A registered component is a
> service subject ([`patterns/principal-identity`](../patterns/principal-identity.md)),
> and `service-subject-constraints` requires a service's enrolment to record a
> named human owner, to be vouched for by a holder of the authority to issue
> grants (principal-identity's `grant:issue`, which a hub carries as
> `admin:*`), and to carry an expiry. This endpoint does none of those: it admits a component on
> its signed manifest alone. Of those constraints it applies only step 1's
> refusals of a person-only capability, and of an admin-gateway-only one to a
> key the tenant did not declare. So it would admit a console that
> registered its own key as a component, which nothing here can tell from a
> component; `architecture/admin`'s `console-credential-use` forbids a console
> to do so, and that rule binds the console, not this endpoint. Closing the
> gap is also what would let a hub admit a console's own service identity
> deliberately, as no route does today
> ([`architecture/admin`](../architecture/admin.md#a-console-holds-a-credential-never-a-token)).

**Error responses:**
- 400: Missing required fields, a capability `protocol/types` does not list,
  or two pass routes that can match one request (`INVALID_REQUEST`)
- 401: Invalid signature or stale timestamp
- 403: Reserved namespace, unauthorized scope, a person-only capability, or
  an admin-gateway-only capability from a key the tenant did not declare as its
  admin gateway's (`CAPABILITY_GATEWAY_ONLY`)
- 409: Namespace already owned by another agent (`NAMESPACE_CONFLICT`), or a
  `url` that contradicts the address the tenant declared for that component
  (`ADDRESS_CONFLICT`)
- 500: Internal error

### DELETE /v1/register

Agent deregistration. Requires the deregistering agent's own registration
token ([Authentication](#authentication)).

The orchestrator MUST:
1. Authenticate the request
2. Remove agent matching `token.sub` from registry
3. Release all namespaces owned by the deregistering agent
4. Remove all routing table entries for the deregistering agent
5. Log audit entry
6. Broadcast updated service directory (with routing table)
7. Respond: `{"status": "deregistered"}`

### GET /v1/services

Service directory including routing table and namespace map.
Requires valid auth token.

**Response:** `ServiceDirectory`, signed as a push is
([`POST /v1/services`](#post-v1services)). What makes this answer the
orchestrator's for a reader that does not verify the signature is the
connection it opened to the orchestrator address it registered at.

The response includes:
- `services` — all registered agents with URL, public key, capabilities, `lease_state` and `lease_expires_at`
- `routing_table` — topic pattern → subscriber list (URL, group, scope)
- `namespaces` — namespace → owning agent name
- `updated_at` — the time of the last change, or one millisecond after the
  previous directory's when that is later, so it only ever rises
  ([`POST /v1/services`](#post-v1services))
- `signature` — the orchestrator's signature over the directory, the
  statement [`POST /v1/services`](#post-v1services) states

### POST /v1/channel

Broker a direct agent-to-agent channel. Requires valid auth token with
`agent:message` capability.

**Request:** `ChannelRequest`
**Response:** `ChannelGrant`

The orchestrator MUST:
1. Authenticate the request
2. Verify `from_agent` matches `token.sub`
3. Verify token has `agent:message` capability (403 if missing)
4. Look up `to_agent` in registry (404 if not found)
5. Generate channel ID and time-limited channel token (1-hour TTL)
6. Store active channel
7. Sign the grant with orchestrator's private key
8. Respond with `ChannelGrant`

### POST /v1/rotate-key

Rotates an agent's ML-DSA-65 key pair. The request must be dual-signed — once with the current key and once with the new key — to prove possession of both.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agent_id | string | yes | Agent identifier |
| new_public_key | string | yes | Base64url-encoded new ML-DSA-65 public key |
| current_signature | string | yes | Manifest signed with current private key |
| new_signature | string | yes | Same manifest signed with new private key |

**Response:** 200 with updated `RegisterResponse`. The orchestrator updates the agent's public key in the service directory and issues a `system.agent.key_rotated` event.

**A component's identity id changes with its key.** The token in that response carries `identity_id`, the fingerprint of the new key, as a registration's does. So what a component recorded or was recorded under before the rotation names it by one identity id, and what comes after by another. [`patterns/principal-identity`](../patterns/principal-identity.md)'s `identity-rotation` keeps a subject's identifier across a rotation, and `architecture/admin` does that for an operator. A registered component is not yet under that rule. This is the gap, stated as the enrolment gap under `POST /v1/register` is.

**Error cases:**
- 401 if current_signature is invalid
- 400 if new_signature verification fails
- 409 if a rotation is already in progress

### POST /v1/lease

Lease renewal. Requires the caller's registration token
([Authentication](#authentication)); the lease renewed is the token's `sub`'s.

**Request:** [`LeaseRenewal`](types.md#leaserenewal)
**Response:** [`Lease`](types.md#lease), its `expires_at` moved on by `duration`

The orchestrator MUST:
1. Refuse with 404 `NOT_FOUND` a renewal for a component it holds no
   registration of; the component registers again
2. Record `ready` and `checks` and move `expires_at`, whether or not the lease
   had lapsed: a renewal after a lapse restores the lease without a new
   registration
3. When an entry's `lease_state` changes, by a renewal or by a lapse,
   broadcast the updated `ServiceDirectory` as a registration does

A component renews on the cadence [`protocol/types`](types.md#leaserenewal)
sets. A lease that lapses
reads `unknown` from its `expires_at` on. The orchestrator never calls a
component to find out why: the lease is the presence fact, and a probe would be
a second one.

### GET /v1/audit

Audit log. Requires a registered component's registration token
([Authentication](#authentication)). A person reads the same log at
`GET /v1/admin/audit`, which needs `admin:audit`
([`architecture/orchestrator`](../architecture/orchestrator.md#administrative-endpoints)).

**Response:** Array of `AuditEntry` (most recent first)

**Query parameters:**
- `actor` — filter by actor name
- `action` — filter by action type
- `target` — filter by target
- `since` — an instant (`protocol/conventions:instant`), entries after it
- `cursor` — pagination cursor (opaque)
- `limit` — max results (default: 100)

---


### Two words that mean two things

Both collisions below cost a registration failure, and both read as a correct
implementation of the wrong specification. A component consuming these
blueprints consumes both sides of each.

**`scope`.** A subscription's `scope` is a DELIVERY scope — `self` (default),
`*` (requires `event:observe`), or a specific agent name. It is not a
`ScopeLevel` from [`patterns/scope`](../patterns/scope.md), which classifies
sensitivity as public, internal, confidential, restricted or critical. A
component that sets a subscription scope to `internal` is refused, because
`internal` is a classification and never an audience.

**`version`.** `protocol_version` is the WIRE protocol version: a bare major
number, `"1"`. It is not semver, and it is not the component's own `version`
field, which is semver. Nor is it a data-contract version, which
[`patterns/contract`](../patterns/contract.md) does express as semver and
compares with major/minor compatibility. Applying the contract check to the
protocol version rejects an orchestrator for answering `"1"` exactly as
specified.

A component MUST compare `protocol_version` for equality with the wire version
it implements, and MUST NOT parse it as semver.

### Endpoint paths are absolute

An orchestrator URL is an ORIGIN — scheme, host, port — and carries no path.
Every endpoint in this specification is written as the full path a client
requests, `/v1/register` and not `/register`, and a client composes a request as
`origin + path`.

Stated because the split is invisible in a single implementation: a component
that holds `/register` and an origin, and a base that happens to be mounted at
`/v1`, works until it meets an orchestrator that is not.

### The path prefix IS the protocol version

`/v1` in a protocol path is `protocol_version`. The same major number, in the
URL rather than the body.

Stated because it was not, and every reader had to infer it. The Conventions
above say all paths are prefixed with `/v1`; the version disambiguation below
says `protocol_version` is a bare major number, `"1"`. Nothing said they are
the same number, so nothing said what happens when it is not `1`.

**A wire protocol major bump MUST change the prefix.** Protocol 2 is served at
`/v2/...`. A client that composes `origin + /v1/register` is asking for
protocol 1 and MUST be answered by protocol 1 or refused — never by protocol 2
at the same path, which is how a client discovers a breaking change by
misreading a response.

**Both MAY be served at once, and that is the only supported way to move.** An
orchestrator serving `/v1` and `/v2` concurrently:

- MUST answer each prefix with that version's contract, including its
  `protocol_version` field — `POST /v1/register` answers `"1"` and
  `POST /v2/register` answers `"2"`, from the same process
- MUST NOT share state whose shape differs between the two, and MUST state in
  its own blueprint which stores are shared
- MUST report both in the service directory, so a client can see what is
  available rather than probing
- MAY stop serving the older prefix only after announcing it; removal is a
  breaking change to every client still using it

This is the protocol surface only. A tenant's own application surface versions
independently — see
[`architecture/gateway`](../architecture/gateway.md#the-route-map), which owns
the mapping between what a caller requests and what serves it.

### Signing input

The bytes a signature covers are `canonicalize(manifest)` where the manifest is
the JSON object **as it arrived on the wire**, not a re-serialization of the
verifier's own manifest type.

This is normative because the alternative is unimplementable. `protocol/types`
requires that unknown fields be ignored on decode, so a verifier that parses the
manifest into its own struct and canonicalizes THAT drops every field it does
not know — and the digest it verifies is then not the digest that was signed. Any
implementation carrying a field the verifier lacks produces a signature that can
never verify, and the failure reports as an invalid signature rather than as a
field asymmetry.

It happened: a content service signed a manifest carrying a `contracts` object,
the orchestrator's `AgentManifest` had no such field, and registration failed
with `manifest signature verification failed` on a signature that was correct.

Two rules follow:

- A verifier MUST canonicalize the received manifest object, preserving fields it
  does not recognise, and MUST NOT canonicalize a value re-serialized from a
  local type.
- A registering component MUST NOT add wire fields to its manifest beyond those
  `protocol/types` defines for `AgentManifest`. Extra fields are legitimate to
  carry and are the verifier's to preserve, but a component that invents them is
  relying on every peer implementing the rule above.

The same applies to every signed payload in this protocol, not only
registration: `canonicalize` is always applied to what was received.

## Namespace Control

Event namespaces are the foundation of safe pub/sub communication.
Every event topic follows a hierarchical naming convention:

```
<namespace>.<entity>.<action>
```

The top-level segment is the **event namespace**. Event namespace
ownership is exclusive — exactly one agent may publish to a given event
namespace.

An event namespace is not the namespace an id is named under
([`schemas/names`](../schemas/names.md#namespaces)): one partitions the
topics a hub routes, the other says whose a published name is. The two
never stand for each other. `system` is reserved in both senses.

### Namespace Rules

1. **Exclusive ownership** — An event namespace is owned by exactly one
   agent. No two agents may publish to the same event namespace.
2. **Reserved event namespaces** — `system.*` is owned by the
   orchestrator. No agent may claim it.
3. **Implicit sub-namespaces** — Owning `workflow` grants publish
   rights to `workflow.*` at all depths (e.g., `workflow.phase.ready`,
   `workflow.approval.required`).
4. **Registration enforcement** — The orchestrator validates
   `manifest.publishes` at registration time. Event namespace conflicts
   are rejected before the agent joins the hub.
5. **Publishing validation** — When an agent publishes an event, the
   framework verifies the topic's event namespace matches one of the
   agent's declared `publishes` entries. Events to unowned event
   namespaces are rejected locally (never sent).

### Standard Namespaces

| Namespace | Owner | Purpose |
|-----------|-------|---------|
| `system` | orchestrator | Agent lifecycle events (registered, deregistered, shutdown) |
| `workflow` | workflow agent | Workflow triggers, phase progression, completion |
| `task` | task agent | Task submission, queuing, dispatch, completion |
| `lifecycle` | lifecycle agent | Strategies, observations, recommendations, approvals |
| `system.dead_letter` | orchestrator | Undeliverable events after retry exhaustion |

Domain controllers and work agents own their own event namespaces
(e.g., `seo.*`, `content.*`, `health.*`).

### Federation Namespace Qualification

When events cross hub boundaries via federation, topics are prefixed
with the originating hub's identity:

```
Local:       workflow.completed
Federated:   acme-corp::workflow.completed
```

The `::` separator distinguishes hub-qualified topics from local ones.
Local subscriptions to `workflow.*` do NOT match `acme-corp::workflow.*`.
To receive federated events, agents subscribe to the hub-qualified
pattern explicitly.

See [Federation Protocol](federation.md) for cross-hub event routing
and data contract enforcement.

---


## Event Scoping

Every event carries a `scope` field that limits which subscribers
receive it. Scoping prevents noise (agents receiving events they
don't need) and enforces data isolation (agents can't observe events
meant for other agents without explicit permission).

### Scope Values

| Value | Meaning | Permission Required |
|-------|---------|---------------------|
| `"self"` (on subscription) | Agent receives only events where `scope` matches its own name | None (default) |
| `"*"` (on subscription) | Agent receives ALL events for the topic, regardless of scope | `event:observe` capability |
| `"<agent-name>"` (on subscription) | Agent receives only events scoped to the named agent | Must be a declared collaborator |
| `"<agent-name>"` (on event) | Event is addressed to the named agent | Set by publisher |
| `"*"` (on event) | Event is globally visible (system events, broadcasts) | Set by publisher |

### Scope Resolution at Delivery

When an agent publishes an event, the framework resolves subscribers
from the local routing table and applies scope filtering:

```
for each subscriber matching the topic pattern:
  if subscriber.scope == "*":
    deliver (agent has global visibility for this topic)
  elif subscriber.scope == "self":
    deliver ONLY IF event.scope == subscriber.agent_name
  elif subscriber.scope == "<specific-agent>":
    deliver ONLY IF event.scope == subscriber.scope
  else:
    skip — do not deliver
```

### Scope Propagation

Infrastructure agents propagate scope through execution chains. When
an agent triggers a workflow, the Workflow Agent records the invoker
and scopes all result events back to the invoker:
 — uses "workflow" as scope because
   the topic 'workflow.trigger' targets the workflow namespace owner
```
1. SEO domain publishes: workflow.trigger, scope: "workflow"
   (addressed to Workflow Agent — uses "workflow" as scope because
   the topic 'workflow.trigger' targets the workflow namespace owner)
2. Workflow Agent records invoker = "seo"
3. Workflow Agent publishes: task.submit, scope: "task"
   (addressed to Task Agent)
4. Task Agent publishes: task.complete, scope: "workflow"
   (result goes back to Workflow Agent)
5. Workflow Agent publishes: workflow.completed, scope: "seo"
   (result goes back to original invoker)
```

The scope chain ensures that intermediate events stay between
infrastructure agents, and final results are delivered only to the
agent that initiated the request.

### Multi-Hop Scope Propagation

When a workflow triggers a nested workflow (multi-hop), scope unwinds
one level at a time — each Workflow Agent execution records its own
invoker independently:

```
1. SEO domain publishes: workflow.trigger("seo-audit"), scope: "workflow"
   Workflow Agent records invoker = "seo"
2. During execution, phase N triggers a sub-workflow:
   Workflow Agent publishes: workflow.trigger("link-check"), scope: "workflow"
   A NEW Workflow Agent execution records invoker = "workflow"
   (the agent name of the outer Workflow Agent instance)
3. Sub-workflow completes:
   Inner Workflow Agent publishes: workflow.completed, scope: "workflow"
   (back to the outer Workflow Agent — its recorded invoker)
4. Outer workflow completes all phases:
   Outer Workflow Agent publishes: workflow.completed, scope: "seo"
   (back to the original domain — its recorded invoker)
```

The rule is: **scope unwinds to the immediate invoker, not the
original initiator.** Each execution level maintains its own invoker
record. The `correlation_id` field (propagated through all hops)
allows end-to-end tracing across the full chain, but scope delivery
is always single-hop return. This prevents inner workflows from
needing knowledge of the outer call stack.

---

## Event Publishing (Framework Behavior)

Publishing an event is a framework-level operation. The agent calls
`publish(topic, payload, scope, correlation_id)` and the framework
handles routing and delivery:

```
1. Validate namespace — topic must match one of agent's declared
   publishes entries. Reject if unowned.
2. Build EventEnvelope:
   - event_id: globally unique, time-sortable identifier
   - topic: the topic
   - source: this agent's name
   - scope: provided scope value
   - correlation_id: provided or inherited from current context
   - trace_id: inherited from current trace context
   - span_id: the span this agent opened for the publish
   - timestamp: now
   - version: agent's event schema version
   - payload: the event data
   - token: this agent's auth token
3. Resolve subscribers from local routing table:
   a. Match topic against subscription patterns (exact, *, #)
   b. Apply scope filtering (see Scope Resolution above)
   c. For consumer groups: select one subscriber per group
   d. For non-grouped subscribers: include all matching

### Subscription Pattern Grammar

| Pattern | Matches | Example |
|---------|---------|---------|
| `exact.topic` | Exact match only | `seo.audit.complete` |
| `domain.*` | Any single segment after prefix | `seo.*` matches `seo.audit` but not `seo.audit.complete` |
| `domain.#` | Any number of segments after prefix | `seo.#` matches `seo.audit` and `seo.audit.complete` |
| `*` | Any single segment (wildcard) | `*.audit` matches `seo.audit`, `health.audit` |
| `#` | All topics (catch-all) | Receives every published event |

Segments are delimited by `.` (period). Wildcards may only appear as complete segments — `seo.au*` is invalid.
4. For each resolved subscriber:
   Deliver EventEnvelope to subscriber's event endpoint
5. On acknowledgement: delivery complete, proceed
6. On rate limit: respect backoff, retry later
7. On other failure: retry per patterns/retry
8. On retry exhaustion: store in dead-letter queue
```

### Dead-Letter Handling

Events that fail delivery after all retries are stored locally by the
publishing agent's framework in a dead-letter log. The framework exposes
dead-letter entries for inspection and replay:

- Dead-letter entries include: original event, failure reason, last error,
  attempt count, subscriber name
- Dead-letter retention: configurable (default: 7 days)
- Replay: the framework can re-attempt delivery of dead-lettered events

For centralized dead-letter management, a hub MAY deploy a dead-letter
infrastructure agent that subscribes to `system.dead_letter` events
(published when an event is dead-lettered).

#### system.dead_letter

Published when an event exhausts all delivery retries. Payload:

| Field | Type | Description |
|-------|------|-------------|
| original_event | EventEnvelope | The undeliverable event |
| target_agent | string | Intended recipient agent name |
| failure_reason | string | Last delivery error |
| attempts | int | Total delivery attempts |
| dead_lettered_at | timestamp | When it was dead-lettered |

---

## Authentication


```yaml
authentication:
  mechanism: token
  token_format:
    structure: Weblisk Token — see protocol/identity, which declares it
    signing: The signature algorithm protocol/identity names
    verification: Verified against the orchestrator's public key
  exempt_endpoints:
    - GET /livez
    - GET /readyz
    - POST /v1/register
  flow:
    - step: "Read the token from the `Authorization: Bearer` header"
    - step: Where no header is present, read the `token` field from the body — EventEnvelope and TaskRequest carry it there
    - step: Where both are present, the header wins
    - step: Verify the token signature against the orchestrator's public key
    - step: Check expiry
    - step: On failure, return 401 and no detail about why beyond that a valid token is required
    - step: On success, pass the decoded claims to the handler
```
Applied to ALL orchestrator endpoints except:
- `GET /livez` and `GET /readyz`
- `POST /v1/register`

Flow:
1. Check `Authorization: Bearer <token>` header (preferred)
2. If no header, check request body for `token` field (fallback for
   `EventEnvelope` and `TaskRequest` which include token in the body)
3. If both present, the header takes precedence
4. Verify token signature against orchestrator's public key
5. Check token expiry
6. On failure: 401 `{"error": "valid token required — register first"}`
7. On success: pass decoded claims to handler

Every orchestrator endpoint here that takes a token takes a registered
component's registration token and no other kind: a person's operator token,
a channel token, a pass and an attestation token are each refused there.
[`architecture/orchestrator`](../architecture/orchestrator.md#auth-middleware)
states the whole sequence and the code each refusal carries, and serves
people's administrative routes under `/v1/admin/*`, which take a person's
operator token ([`protocol/identity`](identity.md#the-pass)).

---

## Token Renewal

Agent auth tokens expire after a configurable TTL (default: 24 hours).
Agents MUST re-register before their token expires to obtain a fresh token.
Re-registration is idempotent — the orchestrator updates the existing
registration entry rather than creating a duplicate.

**Renewal flow:**

```
1. Agent tracks its token expiry (from RegisterResponse.expires_at)
2. When remaining TTL falls below a renewal threshold (default: 10% of total TTL):
   a. Agent re-sends registration request with its current manifest and signature
   b. Orchestrator validates, issues new token, updates agent registry
   c. Agent receives new token in RegisterResponse
3. On authentication failure to any request (token already expired):
   a. Agent immediately re-registers
   b. If re-registration fails: log error, answer `GET /readyz` not ready
      (its lease cannot be renewed without a token, so it lapses to
      `unknown`), retry with backoff per patterns/retry
```

**Key constraints:**
- Re-registration is the ONLY token renewal mechanism (no separate refresh endpoint)
- The orchestrator MUST accept re-registration from an agent with an
  expired token (the registration endpoint does not require auth)
- Namespace ownership is preserved across re-registrations (idempotent)
- In-flight requests that fail with 401 SHOULD be retried after renewal

---

## Observability

### Trace Propagation

Every task, message and event belongs to a trace, and every request between
components carries the span that sent it. These are the rules for carrying a
trace, stated here and nowhere else. The values and their formats are
[`protocol/types`](types.md#tracecontext)'; when a span opens and closes, and
what it is named, are
[`architecture/observability`](../architecture/observability.md#distributed-tracing)'s.

- **Every HTTP request** a component sends carries the W3C `traceparent`
  header, naming the trace and the span the sender opened for this request:
  probes, `/v1/admin/*` requests and calls to the orchestrator included. No
  other header carries a trace.
- **Every envelope** a component builds (a `TaskRequest`'s `context`, an
  `AgentMessage`, an `EventEnvelope`) carries the same two values as its
  required `trace_id` and `span_id`, so the trace survives a queue, a retry or
  a dead letter where no header does. An envelope carries no flags, so a
  request sent from a stored envelope (a retry, a redelivery) sends flags
  `01`: a retry is recorded even in an unsampled trace, the one exception to
  sampling being decided once. Work resumed from a record that keeps only a
  `trace_id` (a stored task) continues that trace with no parent span.
- **A receiver continues the trace it is given.** Its span takes the arriving
  `trace_id` and records the arriving `span_id` as its `parent_span_id`. Where
  a request carries both a `traceparent` and an envelope and they differ, the
  envelope's values are used; the flags are always `traceparent`'s. A request
  with an envelope whose `traceparent` is missing or does not parse continues
  the envelope's trace with flags `01`, as a retry does.
- **A trace starts only where none can be continued**: a timer firing (each
  firing of a cron schedule starts its own), or a request with neither a
  `traceparent` that parses nor an envelope. Its `trace_id` is drawn from a
  cryptographic source, and whether it is
  sampled is decided there, once; every component inside honours the flags it
  receives, except where a rule above sends `01`.
- **A trace restarts at the trust boundary.** The gateway, the admin gateway
  and `POST /v1/federation/task` continue nothing a request from outside the
  tenant carries: neither its `traceparent` nor the `trace_id` and `span_id`
  of any envelope in it. Each starts a new trace there.
- **A trace identifier carries no subject data.** It is random, and nothing is
  derived from a request's content.

```
Domain publishes workflow.trigger        (trace T, span A)
  → Workflow Agent serves it in span B   (parent A); publishes task.submit (trace T, span C)
  → Task Agent serves it in span D       (parent C); calls POST /v1/execute
        traceparent: 00-T-E-01, context.trace_id T, context.span_id E
  → Work Agent serves it in span F       (parent E)
```

### Correlation ID Propagation

The `correlation_id` field in events links all events belonging to a
single logical operation (e.g., one workflow execution). Unlike
`trace_id` (which may span multiple operations), `correlation_id` is
specific to one execution chain.

### Structured Log Format

Every component writes [`LogEntry`](types.md#logentry) as
[`patterns/logging`](../patterns/logging.md) says.

**Audit log** entries (specified in [orchestrator.md](../architecture/orchestrator.md))
are a separate persistent record. Structured logs are operational and
ephemeral — they are for debugging and monitoring, not compliance.

---

## Error Handling


```yaml
error_format:
  type: ErrorResponse
  declared_by: protocol/types
  required_fields: [error]
  recommended_fields: [code, category, retryable]

error_codes:
  - code: INVALID_REQUEST
    raised_by: any endpoint, on a malformed or incomplete body
  - code: INVALID_SIGNATURE
    raised_by: POST /v1/register, POST /v1/services on a push that is
      unsigned or does not verify, and any signed request
  - code: TOKEN_EXPIRED
    raised_by: any authenticated endpoint
  - code: FORBIDDEN
    raised_by: any endpoint requiring a capability the caller lacks
  - code: NOT_FOUND
    raised_by: any endpoint addressing an agent or resource not in the registry
  - code: NAMESPACE_CONFLICT
    raised_by: POST /v1/register, where the namespace is already owned
  - code: NAMESPACE_RESERVED
    raised_by: POST /v1/register, for a reserved namespace
  - code: ADDRESS_CONFLICT
    raised_by: POST /v1/register, where the url contradicts the address the
      tenant declared for that component
  - code: CAPABILITY_PERSON_ONLY
    raised_by: POST /v1/register, where the manifest declares a capability
      protocol/types marks person only
  - code: CAPABILITY_GATEWAY_ONLY
    raised_by: POST /v1/register, where the manifest declares a capability
      protocol/types marks admin gateway only and its key is not the one the
      tenant declared for its admin gateway
  - code: SCOPE_UNAUTHORIZED
    raised_by: subscription, where the scope exceeds the caller's capability
  - code: EVENT_REJECTED
    raised_by: event publication, on a malformed envelope or unowned topic
  - code: DIRECTORY_STALE
    raised_by: POST /v1/services, on a verified directory older than the one
      the agent holds
  - code: RATE_LIMITED
    raised_by: any endpoint, with Retry-After
  - code: AGENT_UNREACHABLE
    raised_by: any dispatch, where the target did not accept the connection
  - code: AGENT_TIMEOUT
    raised_by: any dispatch, where the target did not answer in time
```

Status, category and description for each code are declared once, in
[protocol/types](types.md). This section says which endpoints raise them.
All errors MUST return JSON using the `ErrorResponse` format
(see [types.md](types.md)). At minimum, the `error` field is required.
Implementations SHOULD include `code`, `category`, and `retryable`
when the information is available.

```json
{
  "error": "namespace 'workflow' already owned by agent 'workflow'",
  "code": "NAMESPACE_CONFLICT",
  "category": "permanent",
  "retryable": false
}
```

See [types.md — Standard error codes](types.md) for the full table
of codes, HTTP statuses, and categories. The following maps HTTP
status responses to protocol usage:

| Status | When |
|--------|------|
| 400 | Invalid body, missing fields, unsupported protocol version |
| 401 | Bad token, bad signature, expired token |
| 403 | Missing required capability, reserved namespace, unauthorized scope |
| 404 | Target agent or resource not found |
| 405 | Wrong HTTP method |
| 409 | Namespace conflict at registration |
| 429 | Over concurrency/rate limit (include `Retry-After` header) |
| 500 | Internal server error |
| 502 | Could not reach target agent for event delivery |
| 504 | Agent did not respond within timeout |

### Task Execution Timeouts

The orchestrator enforces a per-task execution timeout. If an agent
does not respond to `POST /v1/execute` within the timeout, the
orchestrator returns 504 to the caller and marks the task as `failed`.

| Config Key | Default | Description |
|------------|---------|-------------|
| `task_timeout_seconds` | 300 | Maximum time to wait for task completion |
| `message_timeout_seconds` | 30 | Maximum time to wait for message response |

Agents MAY override `task_timeout_seconds` in their manifest
(`timeout` field). The orchestrator uses `min(agent_timeout, global_max)`
to prevent unbounded waits.

### Concurrency Control

Each agent declares `max_concurrent` in its manifest. The Task Agent
MUST NOT dispatch more than `max_concurrent` simultaneous tasks to an
agent. When the limit is reached:

1. The Task Agent queues excess tasks and dispatches them as slots free
2. If an agent receives a task above its limit (race condition), it
   MUST return 429 with a `Retry-After` header (in seconds)
3. The Task Agent retries after the indicated delay

If `max_concurrent` is omitted from the manifest, it defaults to 1
(serial execution). A value of 0 means unlimited.

---

## Security

```yaml
security:
  transport:
    - All endpoints MUST be served over HTTPS in production (TLS 1.2+)
    - Localhost-only communication permitted during development
    - No cleartext secrets in request/response bodies
  signing:
    algorithm: ML-DSA-65
    key_type: 1952-byte public / 4032-byte private (FIPS 204)
    process: See protocol/identity for full signing specification
  verification:
    process: All signed messages verified against sender public key from service directory
  trust_model:
    description: >
      Zero-trust agent model. Every agent authenticates via ML-DSA-65 signature
      at registration. All subsequent requests require WLT token issued by
      the orchestrator. Capabilities are declared in manifest and enforced
      at the orchestrator. Namespace ownership prevents event spoofing.
      Channel tokens scope agent-to-agent communication.
  input_validation:
    - Request body size limits enforced (1 MB default, 10 MB for task execution)
    - All IDs validated as 32-character hex strings
    - All timestamps validated as positive integers within replay window
    - Unknown JSON fields ignored (forward compatibility)
  replay_protection:
    window: 300 seconds
    applies_to: registration, key rotation
```

---

## Implementation Notes

- HTTP request bodies MUST be read with size limits enforced
- All registries (agents, namespaces, channels) MUST be thread-safe
- Service directory broadcasts are fire-and-forget (failures logged, not blocking).
  If an agent fails to receive a broadcast, it operates with a stale routing table
  until the next broadcast. Agents MUST periodically refresh their routing table
  by calling `GET /v1/services` on the orchestrator (recommended interval: 60
  seconds, configurable). The orchestrator includes an
  `updated_at` timestamp in the ServiceDirectory — agents compare this with their
  cached version and skip processing if unchanged.
- Channel tokens have a configurable TTL (default: 1 hour); expired channels should be cleaned up
- The orchestrator is NOT an agent — it does not implement agent endpoints
  (it implements orchestrator endpoints)
- The orchestrator publishes to the `system.*` namespace. It delivers
  system events to subscribers via the same event delivery mechanism.
- Event delivery is agent-to-agent. The orchestrator is NOT
  in the event delivery path. It only manages the routing table.
- The routing table is distributed to all agents as part of the service
  directory. Agents resolve subscribers locally — no call to the
  orchestrator is needed to publish events.

---

## Verification Checklist
- [ ] A subscription scope is a delivery scope and never a ScopeLevel ([Two words that mean two things](#two-words-that-mean-two-things))
- [ ] `protocol_version` is compared for equality with the wire version, not parsed as semver ([Two words that mean two things](#two-words-that-mean-two-things))
- [ ] A client composes requests as origin + absolute path; no endpoint constant omits its `/v1` prefix ([Endpoint paths are absolute](#endpoint-paths-are-absolute))
- [ ] A manifest carrying a field the verifier's own type does not define still verifies — canonicalization preserves it ([Signing input](#signing-input))
- [ ] A signed payload is canonicalized as received, never re-serialized from a local type before verification ([Signing input](#signing-input))

### Agent Protocol
- [ ] Agent responds to `POST /v1/describe` with a valid `AgentManifest` including `publishes` and `subscriptions` ([POST /v1/describe](#post-v1describe), [`AgentManifest`](types.md#agentmanifest))
- [ ] Every component serves `GET /livez` and `GET /readyz` without authentication, each answering as [GET /livez and GET /readyz](#get-livez-and-get-readyz) gives and nothing else
- [ ] A registered component renews its lease at `POST /v1/lease` on the cadence [`LeaseRenewal`](types.md#leaserenewal) sets, carrying `ready` ([POST /v1/lease](#post-v1lease))
- [ ] Agent accepts `POST /v1/services` and updates its internal directory and routing table ([POST /v1/services](#post-v1services))
- [ ] An agent that takes a pushed body as its directory refuses an unsigned push: `POST /v1/services` with a body carrying no `signature` answers 401 `INVALID_SIGNATURE` and leaves the agent's directory as it was ([POST /v1/services](#post-v1services)) <!-- wl:check unsigned-push-refused covers directory-push-refuse-unsigned -->
- [ ] At an agent that takes a pushed body as its directory, a push whose body differs by one byte from the directory the orchestrator signed answers 401 `INVALID_SIGNATURE` and changes nothing, and so does a push signed by any key but the orchestrator's ([POST /v1/services](#post-v1services)) <!-- wl:check wrongly-signed-push-refused covers directory-push-refuse-unsigned -->
- [ ] At an agent that takes a pushed body as its directory, a verified push older than the directory the agent holds answers 409 `DIRECTORY_STALE` and changes nothing; the same directory again answers 200 ([POST /v1/services](#post-v1services)) <!-- wl:check stale-push-refused covers directory-push-refuse-stale -->
- [ ] An agent that takes a pushed body as its directory and holds none yet takes nothing from a signed push, reads `GET /v1/services` at its anchor, and holds what that read answered ([POST /v1/services](#post-v1services)) <!-- wl:check unseeded-push-reads-anchor covers directory-push-seeded -->
- [ ] Agent handles `POST /v1/message` with signature verification ([POST /v1/message](#post-v1message))
- [ ] Agent returns signed `TaskResult` from `POST /v1/execute` ([POST /v1/execute](#post-v1execute))
- [ ] Agent accepts `POST /v1/event` and dispatches to matching handlers ([POST /v1/event](#post-v1event))
- [ ] Agent returns 200 OK immediately on event receipt (processing is async) ([POST /v1/event](#post-v1event))
- [ ] Agent returns 429 with `Retry-After` when at event processing capacity ([POST /v1/event](#post-v1event))
- [ ] Agent returns 429 with `RATE_LIMITED` when at max_concurrent capacity ([Concurrency Control](#concurrency-control), [Error Handling](#error-handling))
- [ ] Agent deduplicates events by `event_id` ([POST /v1/event](#post-v1event))

### Event Publishing
- [ ] Framework validates topic namespace ownership before publishing ([Namespace Rules](#namespace-rules))
- [ ] Framework resolves subscribers from local routing table ([Event Publishing](#event-publishing-framework-behavior))
- [ ] Framework applies scope filtering during subscriber resolution ([Scope Resolution at Delivery](#scope-resolution-at-delivery))
- [ ] Framework selects one subscriber per consumer group, as [`patterns/messaging`](../patterns/messaging.md#consumer-groups) balances them ([Event Publishing](#event-publishing-framework-behavior))
- [ ] Framework retries failed deliveries as [Event Publishing](#event-publishing-framework-behavior) says
- [ ] Framework dead-letters events after retry exhaustion ([Dead-Letter Handling](#dead-letter-handling))
- [ ] Every envelope the framework builds carries the fields [Event Publishing](#event-publishing-framework-behavior) builds it with

### Orchestrator Protocol
- [ ] Orchestrator `POST /v1/register` validates namespace ownership (409 on conflict) ([POST /v1/register](#post-v1register))
- [ ] Orchestrator `POST /v1/register` validates subscription scopes (403 on unauthorized) ([POST /v1/register](#post-v1register))
- [ ] Orchestrator `POST /v1/register` enforces replay protection over the window [POST /v1/register](#post-v1register) gives
- [ ] Orchestrator `POST /v1/register` rejects `system.*` namespace claims (403) ([POST /v1/register](#post-v1register), [Namespace Rules](#namespace-rules))
- [ ] Orchestrator `POST /v1/register` refuses a manifest whose `capabilities` names any capability [`protocol/types`](types.md#capability) marks person only, whichever it is, read from that list rather than from a copy of it, with 403 `CAPABILITY_PERSON_ONLY` ([Error Handling](types.md#error-handling)), and issues no token
- [ ] Orchestrator `POST /v1/register` refuses a manifest whose `capabilities` names a capability [`protocol/types`](types.md#capability) marks admin gateway only, from a key whose fingerprint is not the one the tenant declared as its admin gateway's, with 403 `CAPABILITY_GATEWAY_ONLY` ([Error Handling](types.md#error-handling)), and records and issues nothing; it admits the same manifest from the declared key
- [ ] Orchestrator `POST /v1/register` refuses with 400 `INVALID_REQUEST`, recording nothing, a manifest naming a capability `protocol/types` does not list, in `capabilities` or in a pass route, and one two of whose pass routes can match one request ([POST /v1/register](#post-v1register))
- [ ] The token `POST /v1/register` issues carries `identity_id`, the fingerprint of `manifest.public_key` ([POST /v1/register](#post-v1register))
- [ ] Orchestrator `DELETE /v1/register` releases namespaces and routing entries ([DELETE /v1/register](#delete-v1register))
- [ ] Orchestrator `GET /v1/services` returns service directory with routing table and namespace map ([GET /v1/services](#get-v1services))
- [ ] Orchestrator `POST /v1/channel` verifies `agent:message` capability ([POST /v1/channel](#post-v1channel))
- [ ] Orchestrator `POST /v1/lease` moves `expires_at` on by `duration`, restores a lapsed lease, and answers 404 `NOT_FOUND` for an unregistered caller ([POST /v1/lease](#post-v1lease))
- [ ] Orchestrator reads a lease past its `expires_at` as `unknown` and probes no component to learn more ([POST /v1/lease](#post-v1lease))
- [ ] Orchestrator `GET /v1/audit` returns audit entries with pagination ([GET /v1/audit](#get-v1audit))
- [ ] Orchestrator `GET /v1/audit` and `DELETE /v1/register` refuse a person's operator token and a channel token, so neither reads the audit log or deregisters an agent ([Authentication](#authentication))
- [ ] Orchestrator broadcasts updated service directory on registration changes ([POST /v1/register](#post-v1register), [DELETE /v1/register](#delete-v1register))
- [ ] Every directory the orchestrator pushes or answers `GET /v1/services` with is signed, and ordered by its `updated_at`, as [POST /v1/services](#post-v1services) says, the first it signs after a restart with its clock set back included <!-- wl:check orchestrator-signs-directory covers directory-push-signed -->
- [ ] Orchestrator rejects an unsupported `protocol_version` with `UNSUPPORTED_VERSION`, as [`protocol/types`](types.md#orchestratorinfo)'s version negotiation says
- [ ] RegisterResponse includes negotiated `protocol_version`, routing table and `lease` ([POST /v1/register](#post-v1register), [`RegisterResponse`](types.md#registerresponse))

### Cross-Cutting
- [ ] All error responses use `ErrorResponse` format with `error` field ([Error Handling](#error-handling))
- [ ] Error responses include `code` and `category` when available ([Error Handling](#error-handling))
- [ ] Every request between components, and every task, message and event, carries its trace as [Trace Propagation](#trace-propagation) says, and a receiver records the arriving span as its own span's `parent_span_id`
- [ ] `correlation_id` links all events in a single execution chain ([Correlation ID Propagation](#correlation-id-propagation))
- [ ] All protected endpoints reject requests without valid tokens ([Authentication](#authentication))
