<!-- blueprint
type: architecture
name: orchestrator
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types]
platform: any
-->

# Weblisk Orchestrator Blueprint

The orchestrator is the central coordination service. It does NOT execute
agent logic — it manages registration, routing, security, and discovery.

## Responsibilities

1. **Agent Registration** — accept agents, verify identity, issue tokens
2. **Service Directory** — maintain and broadcast the registry of live agents
3. **Task Routing** — accept tasks and forward them to the correct agent
4. **Channel Brokering** — establish secure direct connections between agents
5. **Auth Enforcement** — verify tokens on all protected endpoints
6. **Audit Logging** — record every operation in an append-only log
7. **Health Aggregation** — report overall system health

## Startup Sequence

```
1. Load or generate Ed25519 identity (name: "orchestrator")
2. Initialize empty agent registry, channel registry, audit log
3. Register HTTP routes for all protocol endpoints
4. Start HTTP server on configured port
5. Print startup info (URL, public key, how to register agents)
6. Block and serve requests
```

## Registration Flow (POST /v1/register)

```
1. Read request body → parse RegisterRequest
2. Validate: manifest.name, manifest.url, manifest.public_key must be non-empty
3. Verify signature:
   a. Serialize manifest to JSON (same field order as received)
   b. Verify Ed25519 signature against manifest.public_key
   c. If invalid → 401 "invalid signature — agent identity cannot be verified"
4. Replay protection:
   a. Check |server_time - request.timestamp| < 300 seconds
   b. If stale → 401 "timestamp too old — possible replay"
5. Generate unique agent ID (32 hex chars)
6. Flatten capabilities to string list (e.g., ["file:read", "llm:chat"])
7. Create auth token with claims:
   - sub: agent name
   - iss: "orchestrator"
   - iat: now
   - exp: now + 24 hours
   - cap: flattened capabilities
8. Store agent in registry: {manifest, agentID, token, registeredAt, lastSeen, status:"online"}
9. Log audit entry: actor=orchestrator, action=register, target=agent_name
10. Build current ServiceDirectory
11. Respond with RegisterResponse
12. Asynchronously broadcast updated ServiceDirectory to ALL OTHER agents
```

## Deregistration Flow (DELETE /v1/register)

```
1. Authenticate request (extract and verify token)
2. Remove agent matching token.sub from registry
3. Log audit entry
4. Broadcast updated ServiceDirectory
5. Respond: {"status": "deregistered"}
```

## Task Routing (POST /v1/task)

```
1. Authenticate request
2. Parse TaskRequest from body
3. Extract target_agent from payload.target_agent
4. Look up target in registry → 404 if not found
5. Inject context: workspace_root, current service entries
6. Set task.from = requesting agent's name
7. Generate task.id if not set
8. Log audit entry
9. Forward TaskRequest to target agent's URL + /v1/execute (HTTP POST)
10. Proxy the response back to the caller
11. On connection error → 502 "forwarding to agent failed"
```

## Channel Brokering (POST /v1/channel)

```
1. Authenticate request
2. Parse ChannelRequest from body
3. Verify from_agent matches token.sub (can't request channels for others)
4. Verify token has "agent:message" capability → 403 if missing
5. Look up to_agent in registry → 404 if not found
6. Generate channel ID (32 hex chars)
7. Create channel token:
   - sub: "from_agent↔to_agent"
   - iss: "orchestrator"
   - iat: now
   - exp: now + 1 hour
   - cid: channelID
8. Store active channel: {channelID, from, to, purpose, createdAt, expiresAt}
9. Log audit entry
10. Build ChannelGrant with target URL, target public key, channel token
11. Sign the grant with orchestrator's private key
12. Respond with ChannelGrant
```

## Service Directory (GET /v1/services)

```
1. Authenticate request
2. Build ServiceDirectory from current registry
3. Sign the services array with orchestrator's key
4. Respond with ServiceDirectory
```

## Service Broadcasting

After any registration/deregistration:
```
1. Build current ServiceDirectory
2. For each registered agent (except the one that just changed):
   a. Asynchronously POST ServiceDirectory to agent_url + /v1/services
   b. On failure: log but don't block
```

## Auth Middleware

Applied to all endpoints except /health and POST /register:
```
1. Check Authorization header for "Bearer <token>"
2. If no header, check request body for "token" field
3. Verify token against orchestrator's public key
4. Check expiry
5. On failure → 401 {"error": "valid token required — register first"}
6. On success → pass TokenClaims to handler
```

## Audit Logging

Every operation creates an AuditEntry:
```
{
  id: generateID(),
  timestamp: now(),
  actor: who performed the action,
  action: "register" | "deregister" | "task" | "channel" | "message",
  target: affected agent or resource,
  detail: human-readable description,
  status: "ok" | "denied" | "failed"
}
```

Log to stderr in real-time AND store in memory (append-only).
Format: `[audit] HH:MM:SS actor → target: detail [status]`

## Health (GET /v1/health)

No auth. Returns:
- name: "orchestrator"
- status: "healthy"
- version: from build constants
- uptime: seconds since start
- metrics: {agents: count, channels: count}

## Data Structures

### Agent Registry
Map of agent name → registered agent info.
Thread-safe (concurrent reads/writes from HTTP handlers).

### Channel Registry
Map of channel ID → active channel info.
Channels have TTL (1 hour default) — expired channels should be cleaned up.

## Configuration

- Port: configurable via flag (--port) or env (WL_ORCH_PORT), default 9800
- Identity keys stored in working directory under .weblisk/keys/

## Helper Functions Needed

- `writeJSON(w, statusCode, value)` — serialize and write JSON response
- `writeError(w, statusCode, message)` — write error JSON
- `jsonReader(data)` — create io.Reader from byte slice
- `flattenCapabilities(caps)` — extract capability names to string slice
- `hasCapability(caps, name)` — check if capability list includes name
- `abs(n)` — absolute value of int64
- `truncateKey(hex)` — show first/last 8 chars of key for display
