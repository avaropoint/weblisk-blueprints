<!-- blueprint
type: architecture
name: orchestrator
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types]
platform: any
tier: free
-->

# Weblisk Orchestrator Blueprint

The orchestrator is the trust anchor and registry service. It manages
agent registration, identity verification, namespace ownership, service
directory distribution, and channel brokering.

The orchestrator does NOT execute agent logic, route tasks, manage
strategies, store observations, or handle approvals. Those concerns
belong to infrastructure agents (Workflow, Task, Lifecycle) that
register like any other agent.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: RegisterResponse
          fields_used: [agent_id, token, expires_at, services]
        - name: ServiceDirectory
          fields_used: [agents, routing_table, namespaces]
        - name: ChannelRequest
          fields_used: [from_agent, to_agent, purpose]
        - name: ChannelGrant
          fields_used: [channel_id, token, target_url, target_public_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Ed25519Identity
          fields_used: [public_key, private_key, sign, verify]
        - name: SignatureVerification
          fields_used: [verify_signature, check_replay]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, version, url, public_key, capabilities, publishes, subscriptions]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, action, target, detail, status]
        - name: TokenClaims
          fields_used: [sub, iss, iat, exp, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Responsibilities

1. **Agent Registration** — accept agents, verify identity, issue tokens,
   enforce namespace ownership
2. **Service Directory** — maintain and broadcast the registry of live
   agents, the routing table, and the namespace map
3. **Namespace Control** — enforce exclusive namespace ownership at
   registration, reserve `system.*` for itself
4. **Channel Brokering** — establish secure direct connections between agents
5. **Auth Enforcement** — verify tokens on all protected endpoints
6. **Audit Logging** — record every operation in an append-only log
7. **Health Aggregation** — report overall system health
8. **System Events** — publish to `system.*` namespace (agent lifecycle events)

See [Protocol Specification](../protocol/spec.md) for the authoritative
endpoint contracts.
See [Agent Architecture](agent.md) for the 6-endpoint agent protocol.
See [Lifecycle](lifecycle.md) for the continuous optimization loop.

## Endpoints

The orchestrator exposes exactly 6 endpoints:

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | /v1/register | no* | Agent registration (identity-verified) |
| DELETE | /v1/register | yes | Agent deregistration |
| GET | /v1/services | yes | Service directory (routing table + namespaces) |
| POST | /v1/channel | yes | Request direct agent-to-agent channel |
| GET | /v1/health | no | Orchestrator and hub health |
| GET | /v1/audit | yes | Query audit log |

\* Registration uses Ed25519 identity verification instead of tokens.

---

## Startup Sequence

```
1. Load or generate Ed25519 identity (name: "orchestrator")
2. Initialize empty agent registry, namespace map, routing table, audit log
3. Reserve "system" namespace for orchestrator
4. Register HTTP routes for all 6 endpoints
5. Start HTTP server on configured port
6. Print startup info (URL, public key, how to register agents)
7. Block and serve requests
```

---

## Registration Flow (POST /v1/register)

See [Protocol Specification — POST /v1/register](../protocol/spec.md)
for the authoritative registration contract.

**Orchestrator implementation notes:**

```
1.  Parse and validate per spec.md contract
2.  Verify signature and replay protection (see protocol/identity.md)
3.  Validate namespace claims:
    a. For each namespace in manifest.publishes:
       - Check: is namespace already owned by another agent?
         → 409 NAMESPACE_CONFLICT {"conflict": "<owner-name>"}
       - Check: is namespace in reserved list (system.*)?
         → 403 NAMESPACE_RESERVED
       - If clear → grant ownership: namespace_map[namespace] = agent_name
    b. No publishes declared → agent is subscription-only (no conflict possible)
4.  Validate subscription scopes:
    a. For each subscription in manifest.subscriptions:
       - scope "self" → always allowed
       - scope "*" → check agent has "event:observe" capability → 403 if missing
       - scope "<name>" → check collaborator relationship → 403 if unauthorized
5.  Generate agent ID and auth token (WLT format — see
    [protocol/identity.md Token System](../protocol/identity.md#token-system)):
    - Token type: WLT (Weblisk Token) with Ed25519 signature
    - Claims: sub=agent_name, iss="orchestrator", cap=manifest.capabilities
    - Expiry: 24 hours (configurable via WL_TOKEN_TTL)
6.  Store agent in registry:
    {manifest, agentID, token, registeredAt, lastSeen, status: "online"}
7.  Build routing table entries for this agent's subscriptions:
    For each subscription → add RouteEntry to routing_table[pattern]
8.  Log audit entry: actor=orchestrator, action=register, target=agent_name
9.  Respond with RegisterResponse (includes agent_id, token, service directory)
10. Publish system.agent.registered event (scope: "*")
11. Asynchronously broadcast updated ServiceDirectory to ALL OTHER agents
    via POST /v1/services (includes routing_table and namespaces)
```

### Namespace Enforcement Rules

| Condition | Response |
|-----------|----------|
| Namespace unclaimed | Grant ownership, add to namespace_map |
| Namespace already owned by same agent (re-registration) | Allow (idempotent) |
| Namespace owned by different agent | 409 NAMESPACE_CONFLICT |
| Namespace is `system` or `system.*` | 403 NAMESPACE_RESERVED |
| Agent re-registers with FEWER namespaces | Release dropped namespaces |

### Domain Dependency Tracking

When `manifest.type = "domain"`, the orchestrator tracks whether the
domain's `required_agents` are all registered:

```
1. Extract required_agents from manifest
2. Check each against current registry
3. Store domain dependency status:
   - "ready": all required agents registered
   - "degraded": some missing (log which)
4. Include dependency status in ServiceDirectory
5. On future registrations: re-evaluate all domains that list the
   newly-registered agent in required_agents
```

---

## Deregistration Flow (DELETE /v1/register)

```
1. Authenticate request (extract and verify token)
2. Remove agent matching token.sub from registry
3. Release all namespaces owned by the agent:
   For each namespace where namespace_map[ns] == agent_name:
     delete namespace_map[ns]
4. Remove all routing table entries for this agent
5. Log audit entry
6. Publish system.agent.deregistered event (scope: "*")
7. Broadcast updated ServiceDirectory to all remaining agents
8. Respond: {"status": "deregistered"}
```

---

## Service Directory (GET /v1/services)

Returns the complete service directory including the routing table
and namespace map:

```json
{
  "agents": [
    {
      "name": "seo-analyzer",
      "url": "http://localhost:9801",
      "capabilities": ["task:execute", "agent:message"],
      "type": "agent",
      "domain": "seo",
      "status": "online"
    }
  ],
  "routing_table": {
    "workflow.completed": [
      {"agent": "seo", "url": "http://localhost:9805/v1/event", "group": "seo", "scope": "self"},
      {"agent": "lifecycle", "url": "http://localhost:9810/v1/event", "group": "lifecycle", "scope": "*"}
    ],
    "task.complete": [
      {"agent": "workflow", "url": "http://localhost:9808/v1/event", "group": "workflow", "scope": "self"}
    ]
  },
  "namespaces": {
    "system": "orchestrator",
    "workflow": "workflow",
    "task": "task",
    "lifecycle": "lifecycle",
    "seo": "seo",
    "content": "content",
    "health": "health"
  }
}
```

### Routing Table Structure

The routing table maps topic patterns to subscriber entries. Each
entry includes the subscriber's event endpoint URL, consumer group,
and scope filter.

When a topic is subscribed with a wildcard pattern (`*` or `#`),
the orchestrator stores the pattern as-is. Publishing agents resolve
matches locally using the pattern matching rules from
[patterns/messaging](../patterns/messaging.md).

### Service Broadcasting

After any registration or deregistration, the orchestrator
asynchronously pushes the current `ServiceDirectory` to every other
registered agent via `POST /v1/services`. Failures are logged but
never block.

---

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

---

## Auth Middleware

Applied to all endpoints except `/v1/health` and `POST /v1/register`:

```
1. Check Authorization header for "Bearer <token>"
2. If no header, check request body for "token" field
3. Verify token against orchestrator's signing key
4. Check expiry
5. On failure → 401 {"error": "valid token required — register first"}
6. On success → pass TokenClaims to handler
```

---

## System Events

The orchestrator owns the `system.*` namespace and publishes lifecycle
events that all agents may subscribe to:

| Topic | Scope | Published When |
|-------|-------|----------------|
| `system.agent.registered` | `*` | New agent successfully registered |
| `system.agent.deregistered` | `*` | Agent deregistered |
| `system.shutdown` | `*` | Orchestrator is shutting down gracefully |

System events are published via the same HTTP-based pub/sub mechanism.
The orchestrator resolves subscribers from its own routing table and
delivers via `POST /v1/event`.

---

## Audit Logging

Every operation creates an AuditEntry:

```json
{
  "id": "<generated>",
  "timestamp": 1712160000,
  "actor": "orchestrator",
  "action": "register",
  "target": "seo-analyzer",
  "detail": "Agent registered, namespace 'seo' granted",
  "status": "ok"
}
```

### Audit Actions

| Action | Description |
|--------|-------------|
| `register` | Agent registered |
| `deregister` | Agent deregistered |
| `channel` | Channel brokered |
| `namespace_grant` | Namespace ownership granted |
| `namespace_release` | Namespace ownership released |
| `event` | System event published |

Log to stderr in real-time AND persist to append-only flat-file
storage (JSONL).

Format: `[audit] HH:MM:SS actor → target: detail [status]`

---

## Health (GET /v1/health)

No auth. Returns:

```json
{
  "name": "orchestrator",
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "metrics": {
    "agents": 8,
    "domains": 3,
    "channels": 2,
    "namespaces": 7
  }
}
```

---

## Data Structures

See [Storage](storage.md) for the canonical abstract store interfaces
and [protocol/types.md](../protocol/types.md) for type definitions.

**Key implementation notes:**

- **Agent Registry** — Thread-safe map of agent name → registered agent
  info. Entries include `manifest.type` for domain dependency tracking.
- **Namespace Map** — Map of namespace → owner agent name. Thread-safe.
  Mutations only at registration/deregistration.
- **Routing Table** — Map of topic pattern → []RouteEntry. Rebuilt from
  agent subscriptions at registration. Distributed as part of the
  service directory.
- **Domain Dependency Map** — Map of domain name → `{required_agents: [], status}`.
  Recalculated on every registration/deregistration.
- **Channel Registry** — Map of channel ID → active channel info, with
  1-hour TTL. Expired channels cleaned up periodically.
- **Audit Log** — Append-only flat-file (JSONL). In-memory buffer for
  recent entries, flushed periodically.

---

## Configuration

| Setting | Flag | Env Var | Default |
|---------|------|---------|---------|
| Port | `--port` | `WL_ORCH_PORT` | `9800` |
| Identity key path | `--keys` | `WL_KEYS_DIR` | `.weblisk/keys/` |
| Audit log path | `--audit` | `WL_AUDIT_PATH` | `.weblisk/audit.jsonl` |
| Channel TTL | — | `WL_CHANNEL_TTL` | `3600` (1 hour) |

---

## Implementation Notes

- The orchestrator is the single entry point for agent registration; it must be the first component started
- Namespace ownership is exclusive — once claimed, a namespace is locked to the registering agent
- Service directory broadcasts are pushed to all agents after every registration or deregistration change
- Channel brokering creates short-lived tokens scoped to a specific agent pair
- Auth middleware validates Ed25519 signatures and WLT tokens on every request (except /v1/health)
- The orchestrator should be stateless where possible — registry data can be backed by the storage engine

---

## Verification Checklist

- [ ] POST /v1/register verifies Ed25519 signature and replay protection
- [ ] POST /v1/register enforces exclusive namespace ownership (409 on conflict)
- [ ] POST /v1/register rejects reserved namespace claims (403)
- [ ] POST /v1/register validates subscription scopes (event:observe for "*")
- [ ] POST /v1/register returns RegisterResponse with agent ID, token, and service directory
- [ ] DELETE /v1/register releases owned namespaces and routing table entries
- [ ] Service directory includes routing_table and namespaces map
- [ ] Service directory broadcast to ALL agents after every registration/deregistration
- [ ] POST /v1/channel verifies from_agent matches token.sub
- [ ] POST /v1/channel requires agent:message capability (403 if missing)
- [ ] Channel tokens expire after configured TTL
- [ ] Auth middleware rejects unauthenticated requests on protected endpoints
- [ ] GET /v1/health returns 200 without auth with agent/domain/channel/namespace counts
- [ ] system.agent.registered event published after successful registration
- [ ] system.agent.deregistered event published after deregistration
- [ ] Every operation creates an AuditEntry logged to stderr and persisted to JSONL
- [ ] Domain dependency status recalculated on registration/deregistration
- [ ] Orchestrator does NOT handle tasks, strategies, context, observations, or approvals
