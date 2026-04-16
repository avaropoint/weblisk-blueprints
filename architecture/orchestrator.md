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

1. **Agent Registration** — accept agents and domains, verify identity, issue tokens
2. **Service Directory** — maintain and broadcast the registry of live agents and domains
3. **Domain-Aware Task Routing** — route business tasks through domain controllers, infrastructure tasks directly
4. **Domain Dependency Tracking** — track required agent availability per domain
5. **Strategy Management** — store strategies, decompose into domain tasks
6. **Channel Brokering** — establish secure direct connections between agents
7. **Auth Enforcement** — verify tokens on all protected endpoints
8. **Audit Logging** — record every operation in an append-only log
9. **Health Aggregation** — report overall system health including domain status
10. **Lifecycle Coordination** — store observations, recommendations, and feedback

See [Domain Architecture](domain.md) for the domain controller spec.
See [Lifecycle](lifecycle.md) for the continuous optimization loop.

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

See [Protocol Specification — POST /v1/register](../protocol/spec.md)
for the authoritative registration contract.

**Orchestrator implementation notes:**

```
1. Parse and validate per spec.md contract
2. Verify signature and replay protection (see protocol/identity.md)
3. Generate agent ID and auth token
4. Store agent in registry: {manifest, agentID, token, registeredAt, lastSeen, status:"online"}
5. If manifest.type = "domain": evaluate required_agents availability
   (see Domain Dependency below)
6. Log audit entry: actor=orchestrator, action=register, target=agent_name
7. Respond with RegisterResponse
8. Asynchronously broadcast updated ServiceDirectory to ALL OTHER agents
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
5. Check target type from manifest:
   a. If type = "domain": route to domain (standard path for business tasks)
   b. If type = "infrastructure": route directly
   c. If type = "agent" (work agent): check if a registered domain
      declares it in required_agents. If yes, log advisory:
      "task targets work agent directly — consider routing through domain"
6. Inject context: workspace_root, current service entries, entity context
7. Set task.from = requesting agent's name
8. Generate task.id if not set
9. If strategy_id is set, inject strategy context
10. Log audit entry
11. Forward TaskRequest to target's URL + /v1/execute (HTTP POST)
12. Proxy the response back to the caller
13. If response contains observations → store in observation history
14. If response contains recommendations → store for approval tracking
15. On connection error → 502 "forwarding to agent failed"
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

See [Protocol Specification — GET /v1/services](../protocol/spec.md)
for the endpoint contract.

## Service Broadcasting

After any registration/deregistration, the orchestrator asynchronously
pushes the current `ServiceDirectory` to every other registered agent
via `POST /v1/services`. Failures are logged but never block.

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
- metrics: {agents: count, domains: count, channels: count}

## Strategy Management (POST/GET /v1/strategy)

Strategies are business objectives with measurable targets.
See [Lifecycle](lifecycle.md) for the full specification.

```
POST /v1/strategy — Create or update a strategy
  1. Authenticate request
  2. Parse Strategy from body
  3. Validate: name, objective, targets must be non-empty
  4. Store in strategy registry
  5. Log audit entry
  6. Return stored strategy with generated ID

GET /v1/strategy — List all strategies
  1. Authenticate request
  2. Return all strategies (filterable by status: active, paused, completed)
```

## Entity Context (POST/GET /v1/context)

Entity context grounds every agent's decisions in business reality.

```
POST /v1/context — Set or update entity context
  1. Authenticate request
  2. Parse EntityContext from body
  3. Store as the system's entity context
  4. Log audit entry
  5. Return stored context

GET /v1/context — Retrieve current entity context
  1. Authenticate request
  2. Return stored EntityContext
```

Entity context is automatically injected into TaskContext on every
task execution.

## Observation History (GET /v1/observations)

```
1. Authenticate request
2. Return stored observations (filterable by agent, target, strategy)
3. Support pagination via cursor parameter
```

## Approval Management (POST /v1/approve)

See [Protocol Specification — POST /v1/approve](../protocol/spec.md)
for the endpoint contract and [Lifecycle](lifecycle.md) for the
approval workflow in business context.

**Orchestrator implementation notes:**

- Recommendations arrive via domain task results (step 14 in Task Routing above)
- Accepted recommendations belonging to a paused workflow trigger
  a `POST /v1/message` to the owning domain with action `resume_workflow`
- Recommendation storage uses the Recommendation Store
  (see [Storage](storage.md))

### Recommendation Store

See [Storage — Store: Recommendations](storage.md) for the canonical
store interface. The orchestrator indexes by status (`pending`,
`accepted`, `rejected`) for the `GET /v1/approve` query.

## Data Structures

See [Storage](storage.md) for the canonical abstract store interfaces,
operations, and platform-specific mappings.

**Key implementation notes:**

- **Agent Registry** — Thread-safe map of agent name → registered agent info.
  Entries include `manifest.type` for routing decisions.
- **Domain Dependency Map** — Map of domain name → `{required_agents: [], status}`.
  Recalculated on every registration/deregistration.
- **Channel Registry** — Map of channel ID → active channel info, with
  1-hour TTL. Expired channels should be cleaned up periodically.
- **Strategy, Observation, Entity Context, and Recommendation stores** —
  See [Storage](storage.md) for the full interface contract.

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
