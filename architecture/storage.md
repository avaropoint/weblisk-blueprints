<!-- blueprint
type: architecture
name: storage
version: 1.0.0
requires: [protocol/types, architecture/orchestrator, architecture/domain]
platform: any
-->

# Weblisk Storage Interface

Abstract storage contract for all persistent data in the Weblisk system.
This document defines WHAT must be stored and the operations available —
not HOW storage is implemented. Platform documents
([go.md](../platforms/go.md), [cloudflare.md](../platforms/cloudflare.md))
map this interface to concrete backends.

## Design Principles

1. **Interface, not implementation** — storage is a set of operations.
   Any backend that satisfies the contract is valid.
2. **Portability** — an agent built against the storage interface works
   on any platform without code changes to business logic.
3. **Minimal surface** — only the operations the system actually needs.
   No generic query language, no ORM.
4. **Idempotent writes** — all store operations are safe to retry.

## Storage Backends by Platform

| Platform | Orchestrator | Agent |
|----------|-------------|-------|
| Go (local) | SQLite file (`.weblisk/data.db`) | SQLite file per agent |
| Cloudflare | Durable Objects + KV | Durable Objects + KV |
| Node.js | SQLite or file-based JSON | SQLite or file-based JSON |

Implementations MAY use in-memory storage for development/testing,
but production deployments MUST use persistent backends.

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

**Owner:** Orchestrator
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutStrategy | `(strategy Strategy) → error` | Create or update a strategy |
| GetStrategy | `(id string) → (Strategy, error)` | Retrieve by ID |
| ListStrategies | `(status string) → ([]Strategy, error)` | List, optionally filtered by status |

---

## Store: Observations

**Owner:** Orchestrator (stores), domains (produce)
**Durability:** MUST survive restarts. SHOULD retain at least 30 days.

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

**Owner:** Orchestrator
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

**Owner:** Orchestrator
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| AppendFeedback | `(fb Feedback) → error` | Record feedback entry |
| QueryFeedback | `(recommendationID string) → ([]Feedback, error)` | Feedback for a specific recommendation |

---

## Store: Agent Metrics

**Owner:** Orchestrator
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

**Owner:** Orchestrator
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| SetContext | `(ctx EntityContext) → error` | Store or replace entity context |
| GetContext | `() → (EntityContext, error)` | Retrieve current entity context |

---

## Store: Workflow Executions

**Owner:** Domain controllers
**Durability:** SHOULD survive restarts (allows workflow resumption)

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutExecution | `(exec WorkflowExecution) → error` | Create or update execution |
| GetExecution | `(id string) → (WorkflowExecution, error)` | Retrieve by ID |
| ListExecutions | `(workflowName string, limit int) → ([]WorkflowExecution, error)` | Recent executions for a workflow |
| UpdatePhase | `(execID string, phase PhaseResult) → error` | Update a single phase result |

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

## Implementation Notes

- **Transactions**: Operations that update multiple stores (e.g.,
  approval updating recommendation + audit) SHOULD be atomic where
  the backend supports it. Otherwise, apply in order: data first,
  audit last.
- **Pagination**: All list/query operations support cursor-based
  pagination. Cursors are opaque strings — implementations may use
  offsets, timestamps, or encoded keys.
- **Migrations**: Schema changes are versioned. Each platform doc
  specifies how migrations are applied (e.g., SQLite `user_version`
  pragma for Go, Durable Object migration tags for Cloudflare).
- **Backup**: Production deployments SHOULD implement storage backup.
  This is platform-specific and outside the scope of this interface.
- **Concurrency**: All operations MUST be safe for concurrent access.
  Implementations use platform-appropriate mechanisms (mutex, Durable
  Object single-writer, database transactions).

## Verification Checklist

- [ ] All stores survive process restart
- [ ] Observations are retained for at least 30 days
- [ ] Audit entries are retained for at least 90 days
- [ ] Expired channels are cleaned up automatically
- [ ] All list operations support cursor-based pagination
- [ ] Concurrent reads/writes do not corrupt data
- [ ] Agent metrics are incrementally updated (not recomputed)
- [ ] Workflow executions support resumption after restart
