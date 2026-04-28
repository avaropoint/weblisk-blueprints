<!-- blueprint
type: protocol
name: spec
version: 1.0.0
requires: [protocol/types, protocol/identity]
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
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, version, description, url, public_key, capabilities, inputs, outputs, collaborators, approval, max_concurrent, publishes, subscriptions]
        - name: TaskRequest
          fields_used: [id, from, action, payload, context, token, signature, timestamp]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, changes, observations, recommendations, metrics, signature, timestamp]
        - name: AgentMessage
          fields_used: [id, from, to, type, action, payload, token, signature, timestamp, trace_id]
        - name: EventEnvelope
          fields_used: [event_id, topic, source, scope, correlation_id, timestamp, trace_id, version, payload, token]
        - name: ErrorResponse
          fields_used: [error, code, category, retryable, detail]
        - name: ServiceDirectory
          fields_used: [services, routing_table, namespaces, updated_at, signature]
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: RegisterResponse
          fields_used: [agent_id, token, expires_at, services, orchestrator, protocol_version]
        - name: ChannelRequest
          fields_used: [from_agent, to_agent, purpose, token, signature]
        - name: ChannelGrant
          fields_used: [channel_id, from_agent, to_agent, target_url, target_pub_key, channel_token, expires_at, signature]
        - name: HealthStatus
          fields_used: [name, status, version, uptime, metrics, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Ed25519KeyPair
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
```

---

## Conventions

- All paths are prefixed with `/v1`
- All request/response bodies are `application/json`
- All timestamps are Unix epoch seconds (`int64`)
- All signatures are hex-encoded Ed25519 signatures (128 hex chars)
- All public keys are hex-encoded Ed25519 public keys (64 hex chars)
- Errors return `ErrorResponse` JSON (see [types.md](types.md)); at minimum `{"error": "message"}`
- IDs are 32-character hex strings (16 random bytes); event IDs use UUID v7
  (time-sortable, 32 hex chars when formatted without hyphens)
- Unknown JSON fields MUST be ignored (forward compatibility)
- Request bodies MUST be limited: 1 MB default, 10 MB for task execution

---

## Agent Endpoints

Every agent MUST serve these 6 endpoints on a single HTTP port.
All endpoints use POST for uniformity — this simplifies agent
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
  "public_key": "<64-char hex Ed25519 public key>",
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
1. Validate the request has a non-empty `id` and `token`
2. Update internal service directory from `context.services` (if provided)
3. Execute domain-specific logic
4. Return result with `task_id` matching request `id`
5. Sign the result with the agent's private key

This endpoint is for direct, synchronous task execution. It is called
by the Task Agent when dispatching queued work, or directly by other
agents for immediate execution. The caller blocks until the result
is returned.

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
  "signature": "<hex Ed25519 signature>",
  "timestamp": 1712160001
}
```

### POST /v1/health

Health check. No auth required. No body required.

The health endpoint contract — response fields, sub-component checks,
state derivation rules, and metrics snapshot — is defined in
[`patterns/observability`](../patterns/observability.md#health-endpoint).
That pattern is the single source of truth for health response structure.

**Response (summary):**

```json
{
  "name": "seo-analyzer",
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "metrics": { ... },
  "timestamp": 1712160001
}
```

### POST /v1/message

Direct agent-to-agent messaging for synchronous request/response.

**Request:** `AgentMessage` (type: `request`)
**Response:** `AgentMessage` (type: `response`)

Use `/v1/message` when the caller needs a response. For fire-and-forget
event delivery, use `/v1/event` instead.

The agent MUST:
1. Accept only POST requests
2. If signature is present AND sender's public key is known from the
   service directory, verify the signature
3. Dispatch to the appropriate message handler based on `action`
4. Sign the response

Signature covers: `canonicalize({from, to, action, payload})` per
[RFC 8785 (JCS)](https://www.rfc-editor.org/rfc/rfc8785) — see
[identity.md](identity.md#sign-json) for the canonical JSON requirement.

### POST /v1/services

Accepts service directory and routing table updates pushed by the
orchestrator. The agent MUST update its internal service list and
routing table (thread-safe). Response: 200 OK (no body required).

**Request:** `ServiceDirectory` (now includes `routing_table` and
`namespaces` — see [types.md](types.md))

### POST /v1/event

Receives event deliveries from other agents via HTTP-based pub/sub.
Requires auth token in the event envelope.

**Request:** `EventEnvelope`
**Response:** 200 OK (no body required — fire-and-forget acknowledgment)

The agent MUST:
1. Accept only POST requests
2. Validate the `EventEnvelope` structure (event_id, topic, source,
   scope, timestamp, payload are present)
3. Verify the event's auth token (optional — framework-level)
4. Check idempotency: if `event_id` has already been processed,
   return 200 OK immediately (skip duplicate processing)
5. Match the event's `topic` against registered event handlers
6. Dispatch to the matching handler(s)
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
  "timestamp": 1712160001,
  "trace_id": "abc123def456789012345678",
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

The orchestrator manages agent lifecycle, service discovery, namespace
control, event routing, channel brokering, and audit. It does NOT
execute tasks, run workflows, manage strategies, or store observations.
Those concerns belong to dedicated infrastructure agents.

### POST /v1/register

Agent registration. No auth required (this is how agents GET auth).

**Request:** `RegisterRequest`
**Response:** `RegisterResponse`

The orchestrator MUST:
1. Validate: `manifest.name`, `manifest.url`, `manifest.public_key` are non-empty
2. Verify `signature` against `manifest.public_key` over `canonicalize(manifest)` per RFC 8785
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
7. Issue auth token (WLT format) with capabilities from manifest, 24-hour TTL
8. Store agent in registry
9. Log audit entry: actor=orchestrator, action=register, target=agent_name
10. Respond with `RegisterResponse` (includes routing table)
11. Asynchronously broadcast updated `ServiceDirectory` (with routing table)
    to ALL OTHER agents via `POST /v1/services`

**Error responses:**
- 400: Missing required fields
- 401: Invalid signature or stale timestamp
- 403: Reserved namespace or unauthorized scope
- 409: Namespace already owned by another agent
- 500: Internal error

### DELETE /v1/register

Agent deregistration. Requires valid auth token.

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

**Response:** `ServiceDirectory` (signed by orchestrator)

The response includes:
- `services` — all registered agents with URL, public key, capabilities, status
- `routing_table` — topic pattern → subscriber list (URL, group, scope)
- `namespaces` — namespace → owning agent name
- `updated_at` — timestamp of last change
- `signature` — orchestrator's Ed25519 signature

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

Rotates an agent's Ed25519 key pair. The request must be dual-signed — once with the current key and once with the new key — to prove possession of both.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agent_id | string | yes | Agent identifier |
| new_public_key | string | yes | Hex-encoded new Ed25519 public key |
| current_signature | string | yes | Manifest signed with current private key |
| new_signature | string | yes | Same manifest signed with new private key |

**Response:** 200 with updated `RegisterResponse`. The orchestrator updates the agent's public key in the service directory and issues a `system.agent.key_rotated` event.

**Error cases:**
- 401 if current_signature is invalid
- 400 if new_signature verification fails
- 409 if a rotation is already in progress

### GET /v1/health

Orchestrator health. No auth required.

**Response:** `HealthStatus` with metrics including agent count,
namespace count, and active channel count.

### GET /v1/audit

Audit log. Requires valid auth token.

**Response:** Array of `AuditEntry` (most recent first)

**Query parameters:**
- `actor` — filter by actor name
- `action` — filter by action type
- `target` — filter by target
- `since` — Unix epoch seconds, entries after this time
- `cursor` — pagination cursor (opaque)
- `limit` — max results (default: 100)

---

## Namespace Control

Event namespaces are the foundation of safe pub/sub communication.
Every event topic follows a hierarchical naming convention:

```
<namespace>.<entity>.<action>
```

The top-level segment is the **namespace**. Namespace ownership is
exclusive — exactly one agent may publish to a given namespace.

### Namespace Rules

1. **Exclusive ownership** — A namespace is owned by exactly one agent.
   No two agents may publish to the same namespace.
2. **Reserved namespaces** — `system.*` is owned by the orchestrator.
   No agent may claim it.
3. **Implicit sub-namespaces** — Owning `workflow` grants publish
   rights to `workflow.*` at all depths (e.g., `workflow.phase.ready`,
   `workflow.approval.required`).
4. **Registration enforcement** — The orchestrator validates
   `manifest.publishes` at registration time. Namespace conflicts are
   rejected before the agent joins the hub.
5. **Publishing validation** — When an agent publishes an event, the
   framework verifies the topic's namespace matches one of the agent's
   declared `publishes` entries. Events to unowned namespaces are
   rejected locally (never sent).

### Standard Namespaces

| Namespace | Owner | Purpose |
|-----------|-------|---------|
| `system` | orchestrator | Agent lifecycle events (registered, deregistered, shutdown) |
| `workflow` | workflow agent | Workflow triggers, phase progression, completion |
| `task` | task agent | Task submission, queuing, dispatch, completion |
| `lifecycle` | lifecycle agent | Strategies, observations, recommendations, approvals |
| `system.dead_letter` | orchestrator | Undeliverable events after retry exhaustion |

Domain controllers and work agents own their own namespaces
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

## Types

All types referenced in this specification are defined in
[protocol/types.md](types.md). This includes:

- `AgentManifest` — Agent identity and capability contract
- `TaskRequest` / `TaskResult` — Task execution protocol
- `AgentMessage` — Direct agent-to-agent messaging
- `EventEnvelope` — Pub/sub event delivery
- `ErrorResponse` — Structured error format
- `ServiceDirectory` — Service discovery and routing
- `RegisterRequest` / `RegisterResponse` — Agent registration
- `ChannelRequest` / `ChannelGrant` — Channel brokering
- `Subscription` / `RouteEntry` — Event routing declarations
- `DeadLetterEntry` — Failed event delivery

See [types.md](types.md) for the complete type registry with field
specifications, constraints, and JSON serialization keys.

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
   - event_id: UUID v7 (time-sortable, globally unique)
   - topic: the topic
   - source: this agent's name
   - scope: provided scope value
   - correlation_id: provided or inherited from current context
   - trace_id: inherited from current trace context
   - timestamp: now
   - version: agent's event schema version
   - payload: the event data
   - token: this agent's auth token
3. Resolve subscribers from local routing table:
   a. Match topic against subscription patterns (exact, *, #)
   b. Apply scope filtering (see Scope Resolution above)
   c. For consumer groups: select one subscriber per group (round-robin)
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
   HTTP POST to subscriber.url + "/v1/event"
   Body: EventEnvelope as JSON
   Headers:
     Content-Type: application/json
     X-Event-Id: <event_id>
     X-Trace-Id: <trace_id>
5. On 2xx response: delivery acknowledged, proceed
6. On 429 response: respect Retry-After header, retry later
7. On other failure: retry per patterns/retry (exponential backoff)
8. On retry exhaustion: store in local dead-letter queue
```

### Dead-Letter Handling

Events that fail delivery after all retries are stored locally by the
publishing agent's framework in a dead-letter log. The framework exposes
dead-letter entries for inspection and replay:

- Dead-letter entries include: original event, failure reason, last error,
  attempt count, subscriber name
- Dead-letter retention: 7 days by default (`WL_DLQ_RETENTION`)
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
| dead_lettered_at | int64 | Unix timestamp of dead-lettering |

---

## Authentication

Applied to ALL orchestrator endpoints except:
- `GET /v1/health`
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

---

## Token Renewal

Agent auth tokens expire after 24 hours (configurable via `WL_TOKEN_TTL`).
Agents MUST re-register before their token expires to obtain a fresh token.
Re-registration is idempotent — the orchestrator updates the existing
registration entry rather than creating a duplicate.

**Renewal flow:**

```
1. Agent tracks its token expiry (from RegisterResponse.expires_at)
2. When remaining TTL < 10% of total TTL (e.g., < 2.4 hours for 24h tokens):
   a. Agent re-sends POST /v1/register with its current manifest and signature
   b. Orchestrator validates, issues new token, updates agent registry
   c. Agent receives new token in RegisterResponse
3. On 401 response to any request (token already expired):
   a. Agent immediately re-registers
   b. If re-registration fails: log error, enter degraded state, retry
      with exponential backoff per patterns/retry
```

**Key constraints:**
- Re-registration is the ONLY token renewal mechanism (no separate refresh endpoint)
- The orchestrator MUST accept re-registration from an agent with an
  expired token (the registration endpoint does not require auth)
- Namespace ownership is preserved across re-registrations (idempotent)
- In-flight requests that fail with 401 SHOULD be retried after renewal

---

## Observability

### Trace ID Propagation

All events, tasks, and messages MUST propagate `trace_id` through the
entire execution chain. If the originator does not provide a `trace_id`,
the framework MUST generate one (32 hex chars) at the point of origin.

```
Domain publishes workflow.trigger (trace_id: "abc123")
  → Workflow Agent receives event (same trace_id)
  → Workflow Agent publishes task.submit (same trace_id)
  → Task Agent receives event (same trace_id)
  → Task Agent calls POST /v1/execute (same trace_id in context)
  → Work Agent executes (same trace_id)
```

### Correlation ID Propagation

The `correlation_id` field in events links all events belonging to a
single logical operation (e.g., one workflow execution). Unlike
`trace_id` (which may span multiple operations), `correlation_id` is
specific to one execution chain.

### Structured Log Format

All components SHOULD emit structured logs as JSON lines to stderr.
Each log entry MUST include:

| Field | Description |
|-------|-------------|
| `ts` | Unix epoch seconds (same as protocol timestamps) |
| `level` | `debug`, `info`, `warn`, `error` |
| `msg` | Human-readable message |
| `component` | Component name (e.g., `orchestrator`, `seo`, `seo-analyzer`) |
| `trace_id` | Correlation ID (when available) |

Optional fields (when applicable): `agent`, `target`, `action`,
`task_id`, `phase`, `duration_ms`, `error`, `event_id`,
`correlation_id`, `scope`.

```json
{"ts":1712160001,"level":"info","msg":"event published","component":"seo","trace_id":"a1b2c3...","topic":"workflow.trigger","scope":"workflow","correlation_id":"corr-001"}
{"ts":1712160002,"level":"info","msg":"event received","component":"workflow","trace_id":"a1b2c3...","topic":"workflow.trigger","event_id":"evt-001"}
{"ts":1712160003,"level":"info","msg":"task dispatched","component":"task","trace_id":"a1b2c3...","agent":"seo-analyzer","task_id":"d4e5f6..."}
```

**Audit log** entries (specified in [orchestrator.md](../architecture/orchestrator.md))
are a separate persistent record. Structured logs are operational and
ephemeral — they are for debugging and monitoring, not compliance.

---

## Error Handling

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

---

## Security

```yaml
security:
  transport:
    - All endpoints MUST be served over HTTPS in production (TLS 1.2+)
    - Localhost-only communication permitted during development
    - No cleartext secrets in request/response bodies
  signing:
    algorithm: Ed25519
    key_type: 32-byte public / 64-byte private
    process: See protocol/identity for full signing specification
  verification:
    process: All signed messages verified against sender public key from service directory
  trust_model:
    description: >
      Zero-trust agent model. Every agent authenticates via Ed25519 signature
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

- HTTP request bodies MUST be read with size limits (`io.LimitReader` or equivalent)
- All registries (agents, namespaces, channels) MUST be thread-safe
- Service directory broadcasts are fire-and-forget (failures logged, not blocking).
  If an agent fails to receive a broadcast, it operates with a stale routing table
  until the next broadcast. Agents MUST periodically refresh their routing table
  by calling `GET /v1/services` on the orchestrator (recommended interval: 60
  seconds, configurable via `WL_ROUTING_REFRESH`). The orchestrator includes an
  `updated_at` timestamp in the ServiceDirectory — agents compare this with their
  cached version and skip processing if unchanged.
- Channel tokens have 1-hour TTL; expired channels should be cleaned up
- The orchestrator is NOT an agent — it does not implement agent endpoints
  (it implements orchestrator endpoints)
- The orchestrator publishes to the `system.*` namespace. It delivers
  system events to subscribers via the same `POST /v1/event` mechanism.
- Event delivery is agent-to-agent via HTTP. The orchestrator is NOT
  in the event delivery path. It only manages the routing table.
- The routing table is distributed to all agents as part of the service
  directory. Agents resolve subscribers locally — no call to the
  orchestrator is needed to publish events.

---

## Verification Checklist

### Agent Protocol
- [ ] Agent responds to `POST /v1/describe` with valid `AgentManifest` including `publishes` and `subscriptions`
- [ ] Agent responds to `POST /v1/health` with valid health response
- [ ] Agent accepts `POST /v1/services` and updates internal directory and routing table
- [ ] Agent handles `POST /v1/message` with signature verification
- [ ] Agent returns signed `TaskResult` from `POST /v1/execute`
- [ ] Agent accepts `POST /v1/event` and dispatches to matching handlers
- [ ] Agent returns 200 OK immediately on event receipt (processing is async)
- [ ] Agent returns 429 with `Retry-After` when at event processing capacity
- [ ] Agent deduplicates events by `event_id`

### Event Publishing
- [ ] Framework validates topic namespace ownership before publishing
- [ ] Framework resolves subscribers from local routing table
- [ ] Framework applies scope filtering during subscriber resolution
- [ ] Framework selects one subscriber per consumer group (round-robin)
- [ ] Framework retries failed deliveries with exponential backoff
- [ ] Framework dead-letters events after retry exhaustion
- [ ] Events include event_id, topic, source, scope, correlation_id, trace_id

### Orchestrator Protocol
- [ ] Orchestrator `POST /v1/register` validates namespace ownership (409 on conflict)
- [ ] Orchestrator `POST /v1/register` validates subscription scopes (403 on unauthorized)
- [ ] Orchestrator `POST /v1/register` enforces replay protection (300s window)
- [ ] Orchestrator `POST /v1/register` rejects `system.*` namespace claims (403)
- [ ] Orchestrator `DELETE /v1/register` releases namespaces and routing entries
- [ ] Orchestrator `GET /v1/services` returns service directory with routing table and namespace map
- [ ] Orchestrator `POST /v1/channel` verifies `agent:message` capability
- [ ] Orchestrator `GET /v1/health` returns without auth
- [ ] Orchestrator `GET /v1/audit` returns audit entries with pagination
- [ ] Orchestrator broadcasts updated service directory on registration changes
- [ ] Orchestrator rejects unsupported protocol_version with `UNSUPPORTED_VERSION`
- [ ] RegisterResponse includes negotiated protocol_version and routing table

### Cross-Cutting
- [ ] All error responses use `ErrorResponse` format with `error` field
- [ ] Error responses include `code` and `category` when available
- [ ] `trace_id` is propagated through all events, tasks, and messages
- [ ] `correlation_id` links all events in a single execution chain
- [ ] Agent returns 429 with `RATE_LIMITED` when at max_concurrent capacity
- [ ] All protected endpoints reject requests without valid tokens
