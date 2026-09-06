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

## Overview

The abstract storage contract for every piece of persistent data in a tenant.
It defines WHAT must be stored, which component owns each store, and the
operations each store provides — by name, exactly.

It defines no implementation. Whether a store is a JSONL file, SQLite or a
managed service is the platform blueprint's answer, and every backend owes the
same operations under the same names. That is what lets a component be
generated once and run against any of them.

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
          fields_used: [id, timestamp, actor, action, target, status, previous_hash]
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

**Every operation name in this table is a declared name and is binding.** An
implementation MUST provide the operation under exactly the name written here.
It MUST NOT shorten it, drop the noun, add a qualifier, or substitute a
synonym: `GetAgent` is not `Get`, `AppendObservation` is not `Add`, and
`ClaimNamespace` is not `Claim`. See
[`schemas/common`](../schemas/common.md#declared-names).

The noun is part of the name deliberately. A store is not the only thing in the
package that holds it, and an operation called `Get` tells a reader nothing
about what it returns — but the reason it is *required* is narrower than
readability: these names are what every calling file is written against, so an
implementation that renames one makes every caller wrong, and a regeneration
that renames one makes every caller stale. One measured orchestrator build
regenerated ten compliant files because a plan had used `Get`, `Put` and `List`
where this table says `GetAgent`, `PutAgent` and `ListAgents`.

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

## Contracts

What a store owes, regardless of what provides it. These are the behaviours a
component binds when it declares a dependency on this blueprint — see
[`schemas/common`](../schemas/common.md#declared-names).

Stated because they were not. Eight blueprints bound behaviours from this
document — `sqlite-engine`, `backup-restore`, `durable-records` — and it
declared none, so every one of those bindings resolved to nothing while reading
as a stated dependency.

```yaml
contracts:
  behaviors:
    - name: durable-records
      description: A write survives the process that made it
      required: true
      rules:
        - A write MUST be readable after a restart of the component that made it
        - A write MUST be atomic — a reader never observes a partial record
        - The mechanism is the platform's; see Design Principle 6

    - name: cursor-pagination
      description: Every list and query is resumable
      required: true
      rules:
        - Every list and query operation MUST accept a cursor and a limit
        - A cursor MUST be opaque — implementations may use offsets, timestamps
          or encoded keys, so no caller may decode one
        - A cursor MUST remain valid across a restart or be refused explicitly,
          never silently reinterpreted

    - name: concurrent-access
      description: Operations are safe under concurrent use
      required: true
      rules:
        - Every operation MUST be safe for concurrent access
        - A reader MUST NOT block a reader
        - A component MUST NOT rely on operation ordering between callers

    - name: retention
      description: Data that has a lifetime is removed when it ends
      required: false
      rules:
        - A store with a declared retention MUST remove or archive expired records
        - Retention MUST be enforced by the store, not by each caller remembering
        - Removal MUST be recorded where the store is audited

    - name: backup-restore
      description: A store can be captured and returned to a known state
      required: false
      rules:
        - A backup MUST capture a consistent point, not a smear across writes
        - A restore MUST return the store to exactly the captured state
        - The format is the platform's; the guarantee is not
```

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
   embeddable or built into the platform. No implementation requires a
   database server.

6. **The blueprint names a contract, never a product** — this document
   specifies the operations a store MUST provide. It does not specify
   which engine provides them, and no blueprint may require a
   particular one. Flat-file JSONL is the default on every platform
   because it needs nothing beyond the standard library; any other
   backend — an embedded key-value store, SQLite, a relational or
   object store — is a CONSUMER's choice, expressed when the
   implementation is commissioned. A blueprint that mandates an engine
   has decided something that is not its to decide, and an
   implementation is non-conformant only if it fails the contract, never
   for the backend it satisfies it with.

## A Component Implements Only the Stores It Owns

Every store below names an **Owner**. That attribution is normative: an
implementation provides the stores its own blueprint owns and **MUST NOT**
provide the others.

This document describes all fourteen stores in one place because they share one
contract, one durability rule and one pagination model — not because any one
component holds them. The Orchestrator owns four: Agent Registry, Namespace
Registry, Channels, and the Audit Log. Seven belong to the Lifecycle Agent, one
each to the Workflow and Task agents, and two to the Gateway.

An orchestrator that also implements the workflow-execution store has taken on
state another component owns. Two writers then exist for one record, the audit
chain forks, and `architecture/change-management`'s impact assessment — which
maps a blueprint change onto the *declared* consumers of each binding — assesses
the wrong set.

The failure mode is quiet, which is why this is stated rather than assumed: a
generated orchestrator carrying `store_lifecycle.go` and `store_gateway.go`
compiles perfectly well and looks thorough.

---

## What a Backend Must Be

This document does not name a backend per platform. Naming one would be the same
mistake as naming an engine, one level up: which store satisfies this contract on
a given runtime is that runtime's question, and the **platform blueprint** answers
it. This section states what any answer must be true of.

| Requirement | Meaning |
|---|---|
| **Embeddable** | Runs inside the implementation's own process. No database server to install, configure or operate |
| **Available in the standard library where possible** | A backend needing no dependency is preferred to one that does, all else equal |
| **Durable across restart** | Every store survives the process ending, by any means the runtime offers |
| **Append-friendly** | The audit log is append-only with a hash chain, so the backend must make appends cheap and ordered |
| **Cursor-capable** | List operations paginate by opaque cursor, so the backend must support ordered traversal from a position |

**Flat-file JSONL satisfies all five with nothing beyond a standard library, on
any runtime with a filesystem** — which is why platform blueprints default to it
rather than merely permitting it. A runtime without a filesystem must offer its
own embedded equivalent, and its platform blueprint names it.

Any other backend is available and none is required. An embedded
key-value store, SQLite, a relational database, an object store — all are
valid the moment they satisfy the operations below. That choice belongs
to whoever commissions the implementation, is stated at that point, and
is not a property of the platform. Cloudflare is the one row where the
default differs, and only because the runtime has no filesystem to write
JSONL to.

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

```yaml
types:
  AgentEntry:
    fields:
      manifest:
        name: Manifest
        type: AgentManifest
        description: "Full manifest from registration"
      agent_id:
        name: AgentID
        type: string
        description: "Assigned ID (32 hex chars)"
      token:
        name: Token
        type: string
        description: "Current auth token"
      registered_at:
        name: RegisteredAt
        type: int64
        description: "Unix epoch seconds"
      last_seen:
        name: LastSeen
        type: int64
        description: "Last health check or request timestamp"
      status:
        name: Status
        type: string
        description: "`online`, `offline`, `degraded`"
```

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

```yaml
types:
  ObsFilter:
    fields:
      agent_name:
        name: AgentName
        type: string
        description: "Filter by agent (empty = all)"
      target:
        name: Target
        type: string
        description: "Filter by target path/URL (empty = all)"
      strategy_id:
        name: StrategyID
        type: string
        description: "Filter by strategy (empty = all)"
      since:
        name: Since
        type: int64
        description: "Unix epoch — observations after this time"
      until:
        name: Until
        type: int64
        description: "Unix epoch — observations before this time"
      cursor:
        name: Cursor
        type: string
        description: "Pagination cursor (opaque)"
      limit:
        name: Limit
        type: int
        description: "Max results per page (default: 100)"
```

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

```yaml
types:
  RecFilter:
    fields:
      status:
        name: Status
        type: string
        description: "`pending`, `accepted`, `rejected`, `applied` (empty = all)"
      agent_name:
        name: AgentName
        type: string
        description: "Filter by recommending agent"
      strategy_id:
        name: StrategyID
        type: string
        description: "Filter by strategy"
      priority:
        name: Priority
        type: string
        description: "Filter by priority level"
      cursor:
        name: Cursor
        type: string
        description: "Pagination cursor"
      limit:
        name: Limit
        type: int
        description: "Max results (default: 100)"
```

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

```yaml
types:
  MetricsUpdate:
    fields:
      add_observations:
        name: AddObservations
        type: int
        description: "Increment observation count"
      add_findings:
        name: AddFindings
        type: int
        description: "Increment finding count"
      add_recommendations:
        name: AddRecommendations
        type: int
        description: "Increment recommendation count"
      feedback_signal:
        name: FeedbackSignal
        type: string
        description: "`positive`, `negative`, `neutral` (for rate recalculation)"
```

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

```yaml
types:
  TaskFilter:
    fields:
      status:
        name: Status
        type: string
        description: "`queued`, `dispatched`, `running`, `completed`, `failed`, `cancelled` (empty = all)"
      agent_name:
        name: AgentName
        type: string
        description: "Filter by assigned agent"
      priority:
        name: Priority
        type: string
        description: "`critical`, `high`, `normal`, `low` (empty = all)"
      since:
        name: Since
        type: int64
        description: "Tasks created after this time"
      cursor:
        name: Cursor
        type: string
        description: "Pagination cursor"
      limit:
        name: Limit
        type: int
        description: "Max results (default: 100)"
```

---

## Store: Audit Log

**Owner:** Orchestrator
**Durability:** MUST survive restarts. SHOULD retain at least 90 days.

| Operation | Signature | Description |
|-----------|-----------|-------------|
| AppendAudit | `(entry AuditEntry) → error` | Append audit entry (computes hash chain) |
| QueryAudit | `(filter AuditFilter) → ([]AuditEntry, error)` | Query audit log |
| VerifyChain | `(since int64, until int64) → (valid bool, brokenAt string, error)` | Verify hash chain integrity over a time range |

### Hash Chain Integrity

Every audit entry includes a `previous_hash` field that chains it to
the preceding entry, forming a tamper-evident append-only log:

1. **Hash algorithm:** SHA-256.
2. **Input:** The complete JSON-serialized bytes of the previous entry
   (canonical form per [RFC 8785 / JCS](https://www.rfc-editor.org/rfc/rfc8785)).
3. **First entry:** Uses a zero hash (`0000...0000`, 64 hex chars).
4. **Append flow:** `AppendAudit` MUST read the last entry's
   serialized bytes, compute `SHA-256(previous_entry_bytes)`, and set
   `previous_hash` on the new entry before writing.
5. **Verification:** `VerifyChain` iterates entries in order and
   confirms each entry's `previous_hash` matches `SHA-256` of the
   preceding entry's serialized bytes. Returns the ID of the first
   broken link, or `valid: true` if the chain is intact.
6. **Concurrency:** `AppendAudit` MUST be serialized (single-writer)
   to prevent hash chain forks. Implementations use a mutex, Durable
   Object single-writer, or database transaction.

### AuditFilter

```yaml
types:
  AuditFilter:
    fields:
      actor:
        name: Actor
        type: string
        description: "Filter by actor (empty = all)"
      action:
        name: Action
        type: string
        description: "Filter by action type (empty = all)"
      since:
        name: Since
        type: int64
        description: "After this time"
      cursor:
        name: Cursor
        type: string
        description: "Pagination cursor"
      limit:
        name: Limit
        type: int
        description: "Max results (default: 100)"
```

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
| ClaimNamespace | `(namespace string, agent string) → error` | Record exclusive ownership (409 if already owned by another) |
| ReleaseNamespace | `(namespace string) → error` | Release on agent deregistration |
| GetOwner | `(namespace string) → (string, error)` | Look up which agent owns a namespace |
| ListNamespaces | `() → (map[string]string, error)` | All namespace → agent mappings |

**This store records ownership. It does not decide who may ask.**

`system.*` is reserved, and the rule is a REGISTRATION rule:
[`protocol/spec`](../protocol/spec.md) rejects an agent claiming it with 403
"reserved for orchestrator". The orchestrator itself claims `system` at startup —
[`architecture/orchestrator`](orchestrator.md)'s startup sequence — through this
same store.

An implementation that puts the reservation check inside `ClaimNamespace`
therefore refuses the one component that is supposed to own it. That happened:
a generated orchestrator died two seconds into startup with

```
startup: reserve namespace "system": namespace "system" is reserved
```

and its own health check then honestly reported `namespaces: degraded`, because
the orchestrator did not own the namespace it is required to own.

The general form is worth stating because it will recur: **a store records, a
policy decides.** Enforcement that belongs to a request path, placed in the
store beneath it, applies to every caller including the ones the rule exists to
serve.

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

```yaml
types:
  UserRecord:
    fields:
      user_id:
        name: UserID
        type: string
        description: "Unique user identifier (32 hex chars)"
      email:
        name: Email
        type: string
        description: "User email address (unique)"
      display_name:
        name: DisplayName
        type: string
        description: "Human-readable name"
      roles:
        name: Roles
        type: "[]string"
        description: "Assigned role names"
      groups:
        name: Groups
        type: "[]string"
        description: "Group memberships"
      email_verified:
        name: EmailVerified
        type: bool
        description: "Whether email has been verified"
      mfa_enabled:
        name: MFAEnabled
        type: bool
        description: "Whether MFA is configured"
      status:
        name: Status
        type: string
        description: "`active`, `inactive`, `locked`"
      created_at:
        name: CreatedAt
        type: int64
        description: "Unix epoch seconds"
      last_login_at:
        name: LastLoginAt
        type: int64
        description: "Unix epoch seconds (0 if never)"
```

### UserUpdate

```yaml
types:
  UserUpdate:
    fields:
      display_name:
        name: DisplayName
        type: "*string"
        description: "New display name (nil = no change)"
      roles:
        name: Roles
        type: "*[]string"
        description: "Replace roles (nil = no change)"
      groups:
        name: Groups
        type: "*[]string"
        description: "Replace groups (nil = no change)"
      email_verified:
        name: EmailVerified
        type: "*bool"
        description: "Set verification status (nil = no change)"
      mfa_enabled:
        name: MFAEnabled
        type: "*bool"
        description: "Set MFA status (nil = no change)"
      status:
        name: Status
        type: "*string"
        description: "Change status (nil = no change)"
```

### UserFilter

```yaml
types:
  UserFilter:
    fields:
      status:
        name: Status
        type: string
        description: "`active`, `inactive`, `locked` (empty = all)"
      role:
        name: Role
        type: string
        description: "Filter by role membership"
      group:
        name: Group
        type: string
        description: "Filter by group membership"
      cursor:
        name: Cursor
        type: string
        description: "Pagination cursor"
      limit:
        name: Limit
        type: int
        description: "Max results (default: 100)"
```

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

```yaml
types:
  SessionRecord:
    fields:
      session_id:
        name: SessionID
        type: string
        description: "Unique session identifier (32 hex chars)"
      user_id:
        name: UserID
        type: string
        description: "Owning user"
      client_fingerprint:
        name: ClientFingerprint
        type: string
        description: "Client binding hash (see client.md)"
      roles:
        name: Roles
        type: "[]string"
        description: "Cached roles at session creation"
      created_at:
        name: CreatedAt
        type: int64
        description: "Unix epoch seconds"
      expires_at:
        name: ExpiresAt
        type: int64
        description: "Unix epoch seconds"
      last_activity_at:
        name: LastActivityAt
        type: int64
        description: "Unix epoch seconds — updated on each request"
      ip_address:
        name: IPAddress
        type: string
        description: "Client IP at session creation"
```

### SessionUpdate

```yaml
types:
  SessionUpdate:
    fields:
      last_activity_at:
        name: LastActivityAt
        type: "*int64"
        description: "Update last activity timestamp"
      expires_at:
        name: ExpiresAt
        type: "*int64"
        description: "Extend or shorten session expiry"
```

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
- **Migrations**: Schema changes are versioned. The mechanism that applies a
  version change belongs to the backend, so the platform blueprint states it.
- **Retention**: Stores with retention policies (observations: 90d,
  feedback: 180d, audit: 90d) SHOULD rotate files by month and
  delete or archive expired segments.
- **Encryption**: Agents MAY encrypt data files at rest using
  AES-256-GCM with a key derived from the agent's signing secret.
  See [data-security.md](data-security.md) for key management.
- **Backup**: Production deployments SHOULD implement storage backup.
  This is platform-specific and outside the scope of this interface.
- **Concurrency**: All operations MUST be safe for concurrent access.
  Implementations use platform-appropriate mechanisms (mutex, Durable
  Object single-writer, database transactions).

## Verification Checklist

- [ ] A component implements exactly the stores its own blueprint owns, and none belonging to another component
- [ ] Every store operation exists under exactly the name in the store summary table — not shortened, requalified or renamed
- [ ] Stores record; they do not enforce request-path policy. `ClaimNamespace` accepts `system` from the orchestrator, and `protocol/spec`'s registration flow is what refuses it from an agent
- [ ] A freshly started orchestrator owns the `system` namespace and reports `namespaces: ok`
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
