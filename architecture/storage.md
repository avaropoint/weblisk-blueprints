<!-- blueprint
type: architecture
name: storage
version: 1.0.0
requires: [protocol/types, architecture/orchestrator, architecture/domain, architecture/gateway, agents/workflow, agents/task, agents/lifecycle]
platform: any
tier: free
-->

# Weblisk Storage Interface

Abstract storage contract for all persistent data in the Weblisk system.
This document defines WHAT must be stored and the operations available —
not HOW storage is implemented. Platform documents
([go.md](../platforms/go.md), [cloudflare.md](../platforms/cloudflare.md))
map this interface to concrete backends.

> **Scope boundary:** This file defines **system-level store interfaces**
> across the orchestrator and infrastructure agents (agent registry,
> strategies, observations, workflow executions, task records, etc.).
> For the **agent-level schema declaration format** (types, constraints,
> relationships, migrations), see
> [`patterns/storage`](../patterns/storage.md).

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, version, capabilities]
        - name: Strategy
          fields_used: [id, name, targets, priority, status]
        - name: Observation
          fields_used: [id, agent_name, target, measurements, findings]
        - name: Recommendation
          fields_used: [id, observation_id, action, priority, status]
        - name: Feedback
          fields_used: [id, recommendation_id, signal, metric_before, metric_after]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, action, target, status]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentEntry
          fields_used: [Manifest, AgentID, Token, Status]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: DomainWorkflow
          fields_used: [name, phases]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: agents/workflow
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: WorkflowExecution
          fields_used: [id, workflow, status, phases, started_at]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: agents/task
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskRecord
          fields_used: [id, agent, action, status, priority]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: agents/lifecycle
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentMetrics
          fields_used: [total_observations, accuracy, adoption_rate, impact_score]
        - name: EntityContext
          fields_used: [entity_name, entity_type, metadata]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Responsibilities

### Owns
- Abstract store interface definitions for all persistent system data
- Storage backend selection and tier progression rules (JSONL → compressed → columnar)
- File layout conventions for `.weblisk/data/` directory structure
- Pagination contract (cursor-based, opaque cursors)
- Retention policy definitions (observations: 90d, feedback: 180d, audit: 90d)
- Concurrency safety requirements for all store operations

### Does NOT Own
- Concrete storage implementations (owned by platform documents: go.md, cloudflare.md, node.md)
- Agent-level schema declarations (owned by patterns/storage)
- Encryption key management (owned by architecture/data-security)
- Backup scheduling and execution (platform-specific, out of scope)
- Business logic that reads/writes stores (owned by respective agents)

---

## Interfaces

The storage interface is defined as a set of typed store operations
per data domain. Each store section below declares its full API
surface. Summary of stores:

| Store | Owner | Operations |
|-------|-------|------------|
| Agent Registry | Orchestrator | PutAgent, GetAgent, DeleteAgent, ListAgents |
| Strategies | Lifecycle Agent | PutStrategy, GetStrategy, ListStrategies |
| Observations | Lifecycle Agent | AppendObservation, QueryObservations, CountObservations |
| Recommendations | Lifecycle Agent | PutRecommendation, GetRecommendation, ListRecommendations, UpdateStatus |
| Feedback | Lifecycle Agent | AppendFeedback, QueryFeedback |
| Agent Metrics | Lifecycle Agent | GetMetrics, UpdateMetrics |
| Entity Context | Lifecycle Agent | SetContext, GetContext |
| Workflow Executions | Workflow Agent | PutExecution, GetExecution, ListExecutions, UpdatePhase |
| Task Records | Task Agent | PutTask, GetTask, ListTasks, UpdateStatus |
| Audit Log | Orchestrator | AppendAudit, QueryAudit |
| Channels | Orchestrator | PutChannel, GetChannel, DeleteChannel, CleanExpired |
| Namespace Registry | Orchestrator | ClaimNamespace, ReleaseNamespace, GetOwner, ListNamespaces |
| Users | Gateway | CreateUser, GetUser, GetUserByEmail, UpdateUser, DeleteUser, ListUsers, VerifyCredential, SetCredential |
| Sessions | Gateway | CreateSession, GetSession, UpdateSession, DeleteSession, DeleteUserSessions, CleanExpired |

---

## Data Flow

1. Agent receives a task via `POST /v1/execute` and produces results
2. Results (observations, recommendations) are returned to the calling infrastructure agent
3. Lifecycle Agent appends observations to the observation store (JSONL)
4. Lifecycle Agent creates recommendation entries in the recommendation store
5. On approval, the recommendation status is updated; audit entry is appended
6. Feedback entries are appended after measurement workflows complete
7. Agent metrics are incrementally updated from feedback signals
8. Workflow Agent records execution state to enable resumption after restart
9. Task Agent records task lifecycle (queued → dispatched → running → completed/failed)
10. Orchestrator appends audit entries for every registration, deregistration, and channel operation

---

## Design Principles

1. **Interface, not implementation** — storage is a set of operations.
   Any backend that satisfies the contract is valid.
2. **Portability** — an agent built against the storage interface works
   on any platform without code changes to business logic.
3. **Minimal surface** — only the operations the system actually needs.
   No generic query language, no ORM.
4. **Idempotent writes** — all store operations are safe to retry.
5. **Zero external dependencies** — storage backends MUST be
   embeddable or built into the platform. SQLite for Go and Node.js,
   Durable Objects + KV for Cloudflare. External databases
   (PostgreSQL, MySQL, etc.) MAY be used as optional backends but
   are never required.

## Storage Backends by Platform

| Platform | Orchestrator | Infrastructure Agents | Work Agents |
|----------|-------------|----------------------|-------------|
| Go (local) | Flat-file (JSONL) | Flat-file (JSONL) per agent | Flat-file (JSONL) per agent |
| Cloudflare | Durable Objects + KV | Durable Objects + KV | Durable Objects + KV |
| Node.js | Flat-file (JSONL) or SQLite | Flat-file (JSONL) or SQLite per agent | Flat-file (JSONL) or SQLite per agent |

All backends are embedded — no external database server is required.
External databases (PostgreSQL, MySQL, etc.) MAY be supported as
optional backends for teams that prefer them, but Weblisk's default
storage is always self-contained.

Implementations MAY use in-memory storage for development/testing,
but production deployments MUST use persistent backends.

### Flat-File Storage Tiers

The default storage format is flat-file JSONL (JSON Lines). As data
volume grows, implementations MAY upgrade to more efficient formats
without changing the store interface.

| Tier | Format | Compression | Use Case |
|------|--------|-------------|----------|
| Default | JSONL | None | All agents, < 100k records |
| Compressed | JSONL + ZSTD | Zstandard | Observations, audit logs, > 100k records |
| Columnar | Parquet | Built-in | Analytics, historical queries, > 1M records |

**Tier selection rules:**

1. All agents start with JSONL (zero dependencies, human-readable).
2. When a store exceeds 100k records or 100 MB on disk, the agent
   SHOULD compress rotated files with ZSTD.
3. For read-heavy analytical workloads (e.g., observation trends),
   agents MAY convert historical data to Parquet.
4. Active (hot) data always remains JSONL for append performance.
5. Tier transitions are transparent to the store interface — callers
   never see the underlying format.

**File layout:**

```
.weblisk/data/
  orchestrator/
    agents.jsonl              # Agent registry (active)
    audit.jsonl               # Audit log (active)
    audit.2025-04.jsonl.zst   # Rotated + compressed
  lifecycle/
    strategies.jsonl
    observations.jsonl
    observations.2025-03.parquet  # Historical (columnar)
    recommendations.jsonl
    feedback.jsonl
    agent_metrics.jsonl
    entity_context.jsonl
  workflow/
    executions.jsonl
  task/
    tasks.jsonl
    queue.jsonl
  gateway/
    users.jsonl
    sessions.jsonl
    credentials.jsonl          # Separate file, mode 0600
  <agent-name>/
    <agent-specific>.jsonl
```

---

## Store: Agent Registry

**Owner:** Orchestrator
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutAgent | `(name string, entry AgentEntry) → error` | Store or update an agent registration |
| GetAgent | `(name string) → (AgentEntry, error)` | Retrieve agent by name |
| DeleteAgent | `(name string) → error` | Remove agent from registry |
| ListAgents | `(filter AgentFilter) → ([]AgentEntry, error)` | List agents, optionally filtered by type/status |

### AgentEntry (internal)

| Field | Type | Description |
|-------|------|-------------|
| Manifest | AgentManifest | Full manifest from registration |
| AgentID | string | Assigned ID (32 hex chars) |
| Token | string | Current auth token |
| RegisteredAt | int64 | Unix epoch seconds |
| LastSeen | int64 | Last health check or request timestamp |
| Status | string | `online`, `offline`, `degraded` |

---

## Store: Strategies

**Owner:** [Lifecycle Agent](../agents/lifecycle.md)
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutStrategy | `(strategy Strategy) → error` | Create or update a strategy |
| GetStrategy | `(id string) → (Strategy, error)` | Retrieve by ID |
| ListStrategies | `(status string) → ([]Strategy, error)` | List, optionally filtered by status |

---

## Store: Observations

**Owner:** [Lifecycle Agent](../agents/lifecycle.md) (stores), domains (produce via events)
**Durability:** MUST survive restarts. SHOULD retain at least 90 days.

| Operation | Signature | Description |
|-----------|-----------|-------------|
| AppendObservation | `(obs Observation) → error` | Append to observation log |
| QueryObservations | `(filter ObsFilter) → ([]Observation, error)` | Query by agent, target, strategy, time range |
| CountObservations | `(filter ObsFilter) → (int, error)` | Count matching observations |

### ObsFilter

| Field | Type | Description |
|-------|------|-------------|
| AgentName | string | Filter by agent (empty = all) |
| Target | string | Filter by target path/URL (empty = all) |
| StrategyID | string | Filter by strategy (empty = all) |
| Since | int64 | Unix epoch — observations after this time |
| Until | int64 | Unix epoch — observations before this time |
| Cursor | string | Pagination cursor (opaque) |
| Limit | int | Max results per page (default: 100) |

---

## Store: Recommendations

**Owner:** [Lifecycle Agent](../agents/lifecycle.md)
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutRecommendation | `(rec Recommendation) → error` | Create or update a recommendation |
| GetRecommendation | `(id string) → (Recommendation, error)` | Retrieve by ID |
| ListRecommendations | `(filter RecFilter) → ([]Recommendation, error)` | Query by status, agent, strategy |
| UpdateStatus | `(id string, status string, reason string) → error` | Transition recommendation status |

### RecFilter

| Field | Type | Description |
|-------|------|-------------|
| Status | string | `pending`, `accepted`, `rejected`, `applied` (empty = all) |
| AgentName | string | Filter by recommending agent |
| StrategyID | string | Filter by strategy |
| Priority | string | Filter by priority level |
| Cursor | string | Pagination cursor |
| Limit | int | Max results (default: 100) |

---

## Store: Feedback

**Owner:** [Lifecycle Agent](../agents/lifecycle.md)
**Durability:** MUST survive restarts. SHOULD retain at least 180 days.

| Operation | Signature | Description |
|-----------|-----------|-------------|
| AppendFeedback | `(fb Feedback) → error` | Record feedback entry |
| QueryFeedback | `(recommendationID string) → ([]Feedback, error)` | Feedback for a specific recommendation |

---

## Store: Agent Metrics

**Owner:** [Lifecycle Agent](../agents/lifecycle.md)
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| GetMetrics | `(agentName string) → (AgentMetrics, error)` | Current metrics for an agent |
| UpdateMetrics | `(agentName string, update MetricsUpdate) → error` | Incrementally update metrics |

### MetricsUpdate

| Field | Type | Description |
|-------|------|-------------|
| AddObservations | int | Increment observation count |
| AddFindings | int | Increment finding count |
| AddRecommendations | int | Increment recommendation count |
| FeedbackSignal | string | `positive`, `negative`, `neutral` (for rate recalculation) |

---

## Store: Entity Context

**Owner:** [Lifecycle Agent](../agents/lifecycle.md)
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| SetContext | `(ctx EntityContext) → error` | Store or replace entity context |
| GetContext | `() → (EntityContext, error)` | Retrieve current entity context |

---

## Store: Workflow Executions

**Owner:** [Workflow Agent](../agents/workflow.md)
**Durability:** MUST survive restarts (allows workflow resumption)

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutExecution | `(exec WorkflowExecution) → error` | Create or update execution |
| GetExecution | `(id string) → (WorkflowExecution, error)` | Retrieve by ID |
| ListExecutions | `(workflowName string, limit int) → ([]WorkflowExecution, error)` | Recent executions for a workflow |
| UpdatePhase | `(execID string, phase PhaseResult) → error` | Update a single phase result |

---

## Store: Task Records

**Owner:** [Task Agent](../agents/task.md)
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutTask | `(task TaskRecord) → error` | Create or update a task record |
| GetTask | `(id string) → (TaskRecord, error)` | Retrieve by ID |
| ListTasks | `(filter TaskFilter) → ([]TaskRecord, error)` | Query by status, agent, priority |
| UpdateStatus | `(id string, status string) → error` | Transition task status |

### TaskFilter

| Field | Type | Description |
|-------|------|-------------|
| Status | string | `queued`, `dispatched`, `running`, `completed`, `failed`, `cancelled` (empty = all) |
| AgentName | string | Filter by assigned agent |
| Priority | string | `critical`, `high`, `normal`, `low` (empty = all) |
| Since | int64 | Tasks created after this time |
| Cursor | string | Pagination cursor |
| Limit | int | Max results (default: 100) |

---

## Store: Audit Log

**Owner:** Orchestrator
**Durability:** MUST survive restarts. SHOULD retain at least 90 days.

| Operation | Signature | Description |
|-----------|-----------|-------------|
| AppendAudit | `(entry AuditEntry) → error` | Append audit entry |
| QueryAudit | `(filter AuditFilter) → ([]AuditEntry, error)` | Query audit log |

### AuditFilter

| Field | Type | Description |
|-------|------|-------------|
| Actor | string | Filter by actor (empty = all) |
| Action | string | Filter by action type (empty = all) |
| Since | int64 | After this time |
| Cursor | string | Pagination cursor |
| Limit | int | Max results (default: 100) |

---

## Store: Channels

**Owner:** Orchestrator
**Durability:** MAY be in-memory (channels are short-lived, 1h TTL)

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutChannel | `(id string, channel ChannelEntry) → error` | Store active channel |
| GetChannel | `(id string) → (ChannelEntry, error)` | Retrieve by ID |
| DeleteChannel | `(id string) → error` | Remove channel |
| CleanExpired | `() → (int, error)` | Remove all expired channels, return count |

---

## Store: Namespace Registry

**Owner:** Orchestrator
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| ClaimNamespace | `(namespace string, agent string) → error` | Register exclusive ownership (409 if taken) |
| ReleaseNamespace | `(namespace string) → error` | Release on agent deregistration |
| GetOwner | `(namespace string) → (string, error)` | Look up which agent owns a namespace |
| ListNamespaces | `() → (map[string]string, error)` | All namespace → agent mappings |

---

## Store: Users

**Owner:** [Gateway](gateway.md)
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| CreateUser | `(user UserRecord) → error` | Create a new user (409 if user_id exists) |
| GetUser | `(userID string) → (UserRecord, error)` | Retrieve user by ID |
| GetUserByEmail | `(email string) → (UserRecord, error)` | Retrieve user by email address |
| UpdateUser | `(userID string, update UserUpdate) → error` | Update user fields |
| DeleteUser | `(userID string) → error` | Soft-delete user (mark inactive) |
| ListUsers | `(filter UserFilter) → ([]UserRecord, error)` | List users with optional filter |
| VerifyCredential | `(userID string, credential string) → (bool, error)` | Verify password hash (timing-safe) |
| SetCredential | `(userID string, credential string) → error` | Store bcrypt/argon2id hash |

### UserRecord

| Field | Type | Description |
|-------|------|-------------|
| UserID | string | Unique user identifier (32 hex chars) |
| Email | string | User email address (unique) |
| DisplayName | string | Human-readable name |
| Roles | []string | Assigned role names |
| Groups | []string | Group memberships |
| EmailVerified | bool | Whether email has been verified |
| MFAEnabled | bool | Whether MFA is configured |
| Status | string | `active`, `inactive`, `locked` |
| CreatedAt | int64 | Unix epoch seconds |
| LastLoginAt | int64 | Unix epoch seconds (0 if never) |

### UserUpdate

| Field | Type | Description |
|-------|------|-------------|
| DisplayName | *string | New display name (nil = no change) |
| Roles | *[]string | Replace roles (nil = no change) |
| Groups | *[]string | Replace groups (nil = no change) |
| EmailVerified | *bool | Set verification status (nil = no change) |
| MFAEnabled | *bool | Set MFA status (nil = no change) |
| Status | *string | Change status (nil = no change) |

### UserFilter

| Field | Type | Description |
|-------|------|-------------|
| Status | string | `active`, `inactive`, `locked` (empty = all) |
| Role | string | Filter by role membership |
| Group | string | Filter by group membership |
| Cursor | string | Pagination cursor |
| Limit | int | Max results (default: 100) |

**Credential storage:** Passwords MUST be hashed with Argon2id
(recommended) or bcrypt (minimum cost 12). Raw passwords are NEVER
stored. The `VerifyCredential` operation performs a timing-safe
comparison against the stored hash.

---

## Store: Sessions

**Owner:** [Gateway](gateway.md)
**Durability:** MUST survive restarts (production); MAY be in-memory (development)

| Operation | Signature | Description |
|-----------|-----------|-------------|
| CreateSession | `(session SessionRecord) → error` | Create a new session |
| GetSession | `(sessionID string) → (SessionRecord, error)` | Retrieve session by ID |
| UpdateSession | `(sessionID string, update SessionUpdate) → error` | Update session fields (e.g., last activity) |
| DeleteSession | `(sessionID string) → error` | Invalidate session |
| DeleteUserSessions | `(userID string) → (int, error)` | Invalidate all sessions for a user (logout everywhere) |
| CleanExpired | `() → (int, error)` | Remove all expired sessions, return count |

### SessionRecord

| Field | Type | Description |
|-------|------|-------------|
| SessionID | string | Unique session identifier (32 hex chars) |
| UserID | string | Owning user |
| ClientFingerprint | string | Client binding hash (see client.md) |
| Roles | []string | Cached roles at session creation |
| CreatedAt | int64 | Unix epoch seconds |
| ExpiresAt | int64 | Unix epoch seconds |
| LastActivityAt | int64 | Unix epoch seconds — updated on each request |
| IPAddress | string | Client IP at session creation |

### SessionUpdate

| Field | Type | Description |
|-------|------|-------------|
| LastActivityAt | *int64 | Update last activity timestamp |
| ExpiresAt | *int64 | Extend or shorten session expiry |

---

## Implementation Notes

- **Flat-file first**: The default storage backend is JSONL files —
  one file per store, append-only for writes. This eliminates the
  need for SQLite or any database engine. Implementations that prefer
  SQLite MAY use it as an alternative backend.
- **Transactions**: Operations that update multiple stores (e.g.,
  approval updating recommendation + audit) SHOULD be atomic where
  the backend supports it. Otherwise, apply in order: data first,
  audit last. For JSONL, atomic rename of temporary files provides
  crash-safety for single-store updates.
- **Pagination**: All list/query operations support cursor-based
  pagination. Cursors are opaque strings — implementations may use
  offsets, timestamps, or encoded keys.
- **Migrations**: Schema changes are versioned. Each platform doc
  specifies how migrations are applied (e.g., SQLite `user_version`
  pragma for Go, Durable Object migration tags for Cloudflare).
- **Retention**: Stores with retention policies (observations: 90d,
  feedback: 180d, audit: 90d) SHOULD rotate files by month and
  delete or archive expired segments.
- **Encryption**: Agents MAY encrypt data files at rest using
  AES-256-GCM with a key derived from the agent's Ed25519 secret.
  See [data-security.md](data-security.md) for key management.
- **Backup**: Production deployments SHOULD implement storage backup.
  This is platform-specific and outside the scope of this interface.
- **Concurrency**: All operations MUST be safe for concurrent access.
  Implementations use platform-appropriate mechanisms (mutex, Durable
  Object single-writer, database transactions).

## Verification Checklist

- [ ] All stores survive process restart
- [ ] Observations are retained for at least 90 days
- [ ] Audit entries are retained for at least 90 days
- [ ] Audit log is append-only with hash chain integrity
- [ ] Expired channels are cleaned up automatically
- [ ] All list operations support cursor-based pagination
- [ ] Concurrent reads/writes do not corrupt data
- [ ] Agent metrics are incrementally updated (not recomputed)
- [ ] Workflow executions support resumption after restart
- [ ] No external database server required for default operation
- [ ] User passwords are hashed with Argon2id or bcrypt (cost >= 12); raw passwords are never stored
- [ ] Session expiry is enforced: CleanExpired removes stale sessions; GetSession rejects expired records
- [ ] DeleteUserSessions invalidates all sessions for a user (logout everywhere)
- [ ] Audit log entries include a `previous_hash` field forming a hash chain: `SHA-256(previous_entry_bytes)` — the first entry uses a zero hash
