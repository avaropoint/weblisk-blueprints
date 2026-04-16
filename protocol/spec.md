<!-- blueprint
type: protocol
name: spec
version: 1.0.0
requires: [protocol/types]
platform: any
-->

# Weblisk Agent Protocol Specification v1

The universal wire protocol for all Weblisk agents and orchestrators.
Every implementation — regardless of language or platform — MUST conform
to this specification exactly. All communication is HTTP + JSON.

## Overview

The Weblisk Agent Protocol defines how autonomous agents register with
an orchestrator, receive tasks, execute domain-specific logic, communicate
with each other, and report results. The protocol supports the continuous
optimization lifecycle: strategize → observe → recommend → execute → feedback.

## Conventions

- All paths are prefixed with `/v1`
- All request/response bodies are `application/json`
- All timestamps are Unix epoch seconds (`int64`)
- All signatures are hex-encoded Ed25519 signatures (128 hex chars)
- All public keys are hex-encoded Ed25519 public keys (64 hex chars)
- Errors return `ErrorResponse` JSON (see [types.md](types.md)); at minimum `{"error": "message"}`
- IDs are 32-character hex strings (16 random bytes)
- Unknown JSON fields MUST be ignored (forward compatibility)
- Request bodies MUST be limited: 1 MB default, 10 MB for task execution

---

## Agent Endpoints

Every agent MUST serve these 5 endpoints on a single HTTP port:

### POST /v1/describe

Returns the agent's identity and capabilities. No auth required.

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
  "max_concurrent": 5
}
}
```

### POST /v1/execute

Executes a task. Requires auth token in the request body.

**Request:** `TaskRequest`
**Response:** `TaskResult`

The agent MUST:
1. Validate the request has a non-empty `id` and `token`
2. Update internal service directory from `context.services` (if provided)
3. Update workspace root from `context.workspace_root` (if provided)
4. Execute domain-specific logic
5. Return result with `task_id` matching request `id`
6. Sign the result with the agent's private key

```json
{
  "task_id": "a1b2c3d4e5f6...",
  "agent_name": "seo-analyzer",
  "status": "pending_approval",
  "summary": "Scanned 5 files, proposing 3 improvements",
  "changes": [
    {
      "path": "app/index.html",
      "action": "modify",
      "original": "<title>Home</title>",
      "modified": "<title>Weblisk — Modern Web Framework</title>",
      "diffs": [
        {"element": "title", "before": "Home", "after": "Weblisk — Modern Web Framework", "reason": "Title too short for SEO"}
      ]
    }
  ],
  "observations": [],
  "recommendations": [],
  "metrics": {"files_scanned": 5, "suggestions": 3},
  "signature": "<hex Ed25519 signature>",
  "timestamp": 1712160001
}
```

### GET /v1/health

Health check. No auth required.

**Response:** `HealthStatus`

```json
{
  "name": "seo-analyzer",
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "metrics": {"services_known": 3},
  "timestamp": 1712160000
}
```

### POST /v1/message

Direct agent-to-agent messaging for collaboration.

**Request:** `AgentMessage` (type: `request`)
**Response:** `AgentMessage` (type: `response`)

The agent MUST:
1. Accept only POST requests
2. If signature is present AND sender's public key is known from the
   service directory, verify the signature
3. Dispatch to the appropriate message handler based on `action`
4. Sign the response

Signature covers: `JSON.stringify({from, to, action, payload})`

### POST /v1/services

Accepts service directory updates pushed by the orchestrator.
The agent MUST update its internal service list (thread-safe).
Response: 200 OK (no body required).

**Request:** `ServiceDirectory`

---

## Orchestrator Endpoints

The orchestrator MUST serve these endpoints:

### POST /v1/register

Agent registration. No auth required (this is how agents GET auth).

**Request:** `RegisterRequest`
**Response:** `RegisterResponse`

The orchestrator MUST:
1. Validate: `manifest.name`, `manifest.url`, `manifest.public_key` are non-empty
2. Verify `signature` against `manifest.public_key` over `JSON.stringify(manifest)`
3. Reject if `|server_time - timestamp|` > 300 seconds (replay protection)
4. Generate unique `agent_id` (32 hex chars)
5. Issue auth token (WLT format) with capabilities from manifest, 24-hour TTL
6. Store agent in registry
7. Log audit entry
8. Respond with `RegisterResponse`
9. Asynchronously broadcast updated `ServiceDirectory` to all OTHER agents

**Error responses:**
- 400: Missing required fields
- 401: Invalid signature or stale timestamp
- 500: Internal error

### DELETE /v1/register

Agent deregistration. Requires valid auth token.

The orchestrator MUST:
1. Authenticate the request
2. Remove agent matching `token.sub` from registry
3. Log audit entry
4. Broadcast updated service directory
5. Respond: `{"status": "deregistered"}`

### POST /v1/task

Submit a task for execution. Requires valid auth token.

**Request:** `TaskRequest` with `payload.target_agent` naming the target
**Response:** Proxied `TaskResult` from the target agent

The orchestrator MUST:
1. Authenticate the request
2. Extract `target_agent` from `payload`
3. Look up target in registry (404 if not found)
4. Inject context: `workspace_root`, current service entries, entity context
5. Forward request to target agent's `/v1/execute`
6. Proxy the response back to the caller
7. Log audit entry

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

### GET /v1/services

Service directory. Requires valid auth token.

**Response:** `ServiceDirectory` (signed by orchestrator)

### GET /v1/health

Orchestrator health. No auth required.

**Response:** `HealthStatus` with metrics including agent count and channel count

### GET /v1/audit

Audit log. Requires valid auth token.

**Response:** Array of `AuditEntry` (most recent first)

### POST /v1/approve

Approve or reject pending recommendations. Requires valid auth token.

**Request:** `ApprovalRequest`
**Response:** `ApprovalResponse`

The orchestrator MUST:
1. Authenticate the request
2. Validate: `recommendation_ids` is non-empty, `decision` is `"accept"` or `"reject"`
3. If `decision` is `"reject"` and `reason` is empty, return 400
4. For each recommendation ID:
   a. Look up in recommendation store
   b. If not found or not `"pending"`, record error in result
   c. Update status: `"pending"` → `"accepted"` or `"rejected"`
   d. Store `reason` if provided
5. Log audit entry for each updated recommendation
6. If accepted recommendations belong to a paused workflow,
   notify the owning domain to resume execution
7. Respond with `ApprovalResponse`

### GET /v1/approve

List pending recommendations. Requires valid auth token.

**Response:** Array of `Recommendation` with status `"pending"`

**Query parameters:**
- `agent` — filter by recommending agent name
- `target` — filter by target path/URL
- `strategy` — filter by strategy ID
- `priority` — filter by priority level
- `cursor` — pagination cursor (opaque)
- `limit` — max results (default: 100)

### POST /v1/strategy

Create or update a strategy. Requires valid auth token.

**Request:** `Strategy`
**Response:** Stored `Strategy` with generated `id` if new

The orchestrator MUST:
1. Authenticate the request
2. Validate: `name`, `objective`, `targets` are non-empty
3. Store in strategy registry (create or update)
4. Log audit entry
5. Respond with stored strategy

### GET /v1/strategy

List strategies. Requires valid auth token.

**Response:** Array of `Strategy`

**Query parameters:**
- `status` — filter by `active`, `paused`, `completed` (default: all)

### POST /v1/context

Set or update entity context. Requires valid auth token.

**Request:** `EntityContext`
**Response:** Stored `EntityContext`

The orchestrator MUST:
1. Authenticate the request
2. Store as the system's entity context
3. Log audit entry
4. Respond with stored context

### GET /v1/context

Retrieve current entity context. Requires valid auth token.

**Response:** `EntityContext`

### GET /v1/observations

List observations. Requires valid auth token.

**Response:** Array of `Observation`

**Query parameters:**
- `agent` — filter by agent name
- `target` — filter by target path/URL
- `strategy` — filter by strategy ID
- `since` — Unix epoch seconds, observations after this time
- `cursor` — pagination cursor (opaque)
- `limit` — max results (default: 100)

---

## Auth Middleware

Applied to ALL orchestrator endpoints except:
- `GET /v1/health`
- `POST /v1/register`

Flow:
1. Check `Authorization: Bearer <token>` header
2. If no header, check request body for `token` field
3. Verify token signature against orchestrator's public key
4. Check token expiry
5. On failure: 401 `{"error": "valid token required — register first"}`
6. On success: pass decoded claims to handler

---

## Observability

### Trace ID Propagation

Every task submission SHOULD include a `trace_id` in `TaskContext`.
If the caller does not provide one, the orchestrator MUST generate a
unique `trace_id` (32 hex chars) and inject it before forwarding.

The `trace_id` MUST be propagated through ALL downstream calls:

```
Client → POST /v1/task (trace_id in context)
  → Orchestrator forwards to domain → POST /v1/execute (same trace_id)
    → Domain dispatches to agent → POST /v1/message (same trace_id)
```

Agents and domains MUST include `trace_id` in `AgentMessage` when
dispatching to other agents.

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
`task_id`, `phase`, `duration_ms`, `error`.

```json
{"ts":1712160001,"level":"info","msg":"task forwarded","component":"orchestrator","trace_id":"a1b2c3...","agent":"seo","action":"audit","task_id":"d4e5f6..."}
{"ts":1712160002,"level":"info","msg":"phase started","component":"seo","trace_id":"a1b2c3...","phase":"scan","agent":"seo-analyzer"}
{"ts":1712160005,"level":"info","msg":"phase completed","component":"seo","trace_id":"a1b2c3...","phase":"scan","duration_ms":3200}
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
  "error": "forwarding to agent failed — connection refused",
  "code": "AGENT_UNREACHABLE",
  "category": "transient",
  "retryable": true
}
```

See [types.md — Standard error codes](types.md) for the full table
of codes, HTTP statuses, and categories. The following maps HTTP
status responses to protocol usage:

| Status | When |
|--------|------|
| 400 | Invalid body, missing fields, unsupported protocol version |
| 401 | Bad token, bad signature, expired token |
| 403 | Missing required capability |
| 404 | Target agent or resource not found |
| 405 | Wrong HTTP method |
| 429 | Over concurrency/rate limit (include `Retry-After` header) |
| 500 | Internal server error |
| 502 | Orchestrator could not reach agent |
| 504 | Agent did not respond within timeout |

---

## Implementation Notes

- HTTP request bodies MUST be read with size limits (`io.LimitReader` or equivalent)
- All registries (agents, channels) MUST be thread-safe
- Service broadcasts are fire-and-forget (failures logged, not blocking)
- Channel tokens have 1-hour TTL; expired channels should be cleaned up
- The orchestrator is NOT an agent — it does not implement agent endpoints

## Verification Checklist

- [ ] Agent responds to `POST /v1/describe` with valid `AgentManifest`
- [ ] Agent responds to `GET /v1/health` with valid `HealthStatus`
- [ ] Agent accepts `POST /v1/services` and updates internal directory
- [ ] Agent handles `POST /v1/message` with signature verification
- [ ] Agent returns signed `TaskResult` from `POST /v1/execute`
- [ ] Orchestrator `GET /v1/health` returns without auth
- [ ] Orchestrator `GET /v1/services` requires valid token (401 without)
- [ ] Orchestrator `POST /v1/register` validates signature
- [ ] Orchestrator `POST /v1/register` enforces replay protection (300s window)
- [ ] Orchestrator `DELETE /v1/register` removes agent and broadcasts
- [ ] Orchestrator `POST /v1/task` routes to correct agent
- [ ] Orchestrator `POST /v1/channel` verifies `agent:message` capability
- [ ] Orchestrator `POST /v1/approve` transitions pending → accepted/rejected
- [ ] Orchestrator `POST /v1/approve` rejects empty reason on reject decision
- [ ] Orchestrator `GET /v1/approve` returns pending recommendations
- [ ] Orchestrator rejects unsupported protocol_version with `UNSUPPORTED_VERSION`
- [ ] RegisterResponse includes negotiated protocol_version
- [ ] All error responses use `ErrorResponse` format with `error` field
- [ ] Error responses include `code` and `category` when available
- [ ] Agent returns 429 with `RATE_LIMITED` when at max_concurrent capacity
- [ ] All protected endpoints reject requests without valid tokens
- [ ] Orchestrator `POST /v1/strategy` stores and returns strategy
- [ ] Orchestrator `GET /v1/strategy` lists strategies with optional status filter
- [ ] Orchestrator `POST /v1/context` stores entity context
- [ ] Orchestrator `GET /v1/context` returns stored entity context
- [ ] Orchestrator `GET /v1/observations` returns observations with pagination
- [ ] Orchestrator generates `trace_id` if not provided by caller
- [ ] `trace_id` is propagated through task forwarding and agent dispatch
- [ ] Structured logs include `ts`, `level`, `msg`, `component` fields
