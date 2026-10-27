<!-- blueprint
type: architecture
name: storage
version: 2.0.0
requires: [protocol/types, protocol/identity, patterns/principal-identity, architecture/orchestrator, architecture/domain, architecture/gateway, agents/workflow, agents/task, agents/lifecycle]
platform: any
tier: free
-->

# Weblisk Storage Interface

Abstract storage contract for all persistent data in the Weblisk system.
This document defines WHAT must be stored and the operations available —
not HOW storage is implemented. Language and platform documents
([go.md](../languages/go.md), [cloudflare.md](../platforms/cloudflare.md))
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
    version: ">=1.0.0 <7.0.0"
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
  # Sealing a Chained Log: the log key is an ML-DSA-65 key pair held as rule 7
  # holds an operating credential, and the owner's long-lived key is held as
  # rule 8 requires. Every key entry, succession entry and checkpoint is a
  # fixed-form statement signed and verified as Sign and Verify Signature say,
  # and names each key by its Key Fingerprint
  - blueprint: protocol/identity
    version: ">=2.1.0 <4.0.0"
    bindings:
      types:
        - name: SigningKeyPair
          fields_used: [algorithm, public_key, private_key]
        - name: Signature
          fields_used: [algorithm, value]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/principal-identity
    version: ">=1.5.0 <3.0.0"
    bindings:
      types:
        # A key entry names the protection of the key that signed it
        - name: Identity
          fields_used: [key_protection]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=3.0.0 <5.0.0"
    bindings:
      types:
        - name: AgentEntry
          fields_used: [manifest, agent_id, token, registered_at, last_seen, lease, last_renewal]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        - name: DomainWorkflow
          fields_used: [name, phases]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: agents/workflow
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        - name: WorkflowExecution
          fields_used: [id, workflow, status, phases, started_at]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: agents/task
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        - name: TaskRecord
          fields_used: [id, agent, action, status, priority]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: agents/lifecycle
    version: ">=1.0.0 <3.0.0"
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

## Architecture

The abstract storage contract. One component owns each store; the backend is the
only boundary storage does not control on both sides.

```
   Component (owner)
        │  get · put · delete, scoped to its own stores
        ▼
   ┌─────────────────────────────┐
   │ STORE                       │
   │  ownership declared         │
   │  precondition on write      │
   │  cursor-based traversal     │
   └────────────┬────────────────┘
                │ the one boundary not controlled on both sides
                ▼
           Backend (named by the platform blueprint)
```

**Responsibilities.** Declaring what must be stored, which component owns each
store, and the operations each provides by name. Preconditions on write, ordered
traversal by cursor, and the rule that absence is not an error.

**Not responsibilities.** Naming a backend — that is the platform blueprint's
answer. Deciding who may read a record, which is `architecture/enforcement`.
Encrypting data in motion, which is `architecture/data-security`.

---

## Responsibilities

### Owns
- Abstract store interface definitions for all persistent system data
- Storage backend selection and tier progression rules (JSONL → compressed → columnar)
- File layout conventions for `.weblisk/data/` directory structure
- Pagination contract (cursor-based, opaque cursors)
- Retention policy definitions (observations: 90d, feedback: 180d, audit: 90d)
- Concurrency safety requirements for all store operations
- The hash chain every chained log uses, and how a chained log is sealed: its
  key and checkpoint entries, the statements they sign, and how a verifier
  checks them offline

### Does NOT Own
- Concrete storage implementations (owned by platform documents: go.md, cloudflare.md, node.md)
- Whether a given log is sealed, and what its own entries hold (owned by the
  blueprint that owns the log)
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

    - name: sealed-log
      description: A chained log its owner signs, which anyone can verify
        offline. Bound by the blueprint of a log that is sealed
      required: false
      rules:
        - Every entry MUST be stored as its RFC 8785 canonical bytes and one line feed, and MUST NOT be re-serialised
        - seq MUST start at 1 and rise by one. previous_digest MUST be the SHA-256 of the previous stored line without its line feed, and 64 zeros on the first entry
        - Checkpoints MUST be signed by a log key, an ML-DSA-65 key held in memory only, whose key entry, signed by the log's authority, is in the log before the log key signs
        - Once weblisk/log-key/v2, weblisk/log-checkpoint/v2 and weblisk/log-succession/v1 have test vectors (protocol/identity, Fixed-Form Statements), the owner MUST mint a log key when its process starts, and MUST mint the next and append its key entry to each log before the current log key's not_after passes. Sealing then pauses only while the long-lived key cannot sign that key entry. Until those vectors are published the owner mints no log key, so no log key is available and nothing is sealed (Sealing a Chained Log, The log key)
        - While a log key is available, and whenever the tip has moved since the last checkpoint, a checkpoint MUST be issued at each checkpoint_interval, at clean shutdown, and on request. A checkpoint entry does not move the tip
        - A change of the owner's long-lived key MUST be recorded in each log that has an authority by a succession entry both keys sign, before the incoming key signs anything in that log, wherever the owner still holds the outgoing key. A log with no key entry has no authority and takes no succession entry, and until weblisk/log-key/v2, weblisk/log-checkpoint/v2 and weblisk/log-succession/v1 have test vectors no log has a key entry
        - An unavailable log key MUST stop sealing and MUST NOT stop appending. Unsealed entries MUST be counted wherever the log is reported
        - A key entry MUST NOT be removed or replaced. A checkpoint is judged against the key and succession entries before it
        - The owner MUST verify its log from the latest checkpoint to the tip before its first append after it starts and before each checkpoint. It MUST NOT append to or seal a log that fails, and MUST go on serving reads of it
        - A break in the chain MUST be reported where it is and MUST NOT be repaired, truncated or re-chained
        - Every checkpoint MUST be reported uncountersigned. It is the owner's own statement, and nothing in this contract has anyone else countersign it
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
| ListAgents | `(filter AgentFilter) → ([]AgentEntry, error)` | List agents, optionally filtered by type. A lease's state is derived from the entry's `lease` when read, never stored ([`architecture/orchestrator`](orchestrator.md#data-structures)), so the store neither holds it nor filters by it |

`AgentEntry` is [`architecture/orchestrator`](orchestrator.md#agententry)'s,
the store's owner, and is defined there alone.

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
        type: timestamp
        description: "Observations after this time"
      until:
        name: Until
        type: timestamp
        description: "Observations before this time"
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
        type: timestamp
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
| VerifyChain | `(since timestamp, until timestamp) → (valid bool, brokenAt string, error)` | Verify hash chain integrity over a time range |

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
        type: timestamp
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
a generated orchestrator failed its startup two seconds in with

```
startup: reserve namespace "system": namespace "system" is reserved
```

and its own health check, as the spec then had it, honestly reported
`namespaces: degraded`, because the orchestrator did not own the namespace it
is required to own. Under today's spec the same fault is the orchestrator's
`GET /readyz` answering not ready ([`protocol/types`](../protocol/types.md#readiness)).

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
        type: timestamp
      last_login_at:
        name: LastLoginAt
        type: timestamp
        description: "Absent if never"
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
        type: timestamp
      expires_at:
        name: ExpiresAt
        type: timestamp
      last_activity_at:
        name: LastActivityAt
        type: timestamp
        description: "Updated on each request"
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
        type: timestamp
        description: "Update last activity timestamp"
      expires_at:
        name: ExpiresAt
        type: timestamp
        description: "Extend or shorten session expiry"
```

---

## Sealing a Chained Log

A chained log ([Hash Chain Integrity](#hash-chain-integrity)) shows that no
entry was changed or removed after a later one was written. It does not show
who wrote it: anyone who can write the file can write a new chain that is just
as consistent. **Sealing** closes that gap. The log's owner signs the log's tip
from time to time, with ML-DSA-65, so a verifier can tell the log its owner
signed from any other.

This section says how any chained log is sealed. The blueprint that owns a log
says whether it is sealed, and binds `sealed-log` when it is.
[`architecture/content`](content.md#the-change-log) seals each repository's
change log.

### What a sealed log holds

A sealed log keeps the chain rules above, under these field names and in this
stored form:

- **One line per entry.** An entry is stored as its RFC 8785 canonical bytes
  followed by one line feed (0x0A). Canonical JSON holds no raw line feed, so a
  line is exactly one entry. The stored bytes are never re-serialised: what was
  written is what is hashed, served and verified.
- **Position.** Every entry carries `seq`, `previous_digest` and `recorded_at`.
  The first entry has `seq` 1, and each later entry's `seq` is one more than the
  one before it. `previous_digest` is the lowercase hex SHA-256 of the previous
  entry's stored line, without its line feed. On the first entry it is 64
  zeros.
- **Log id.** A log is named by its **log id**: the SHA-256 of its first
  entry's stored line. The first entry records what the log is for and when it
  began, so no two logs share an id.
- **Three kinds of entry of its own.** Beside the owner's entries, a sealed
  log holds **key entries** (`LogKey`), each of which introduces a key that
  signs checkpoints; **succession entries** (`LogSuccession`), each of which
  records a change of the owner's long-lived key; and **checkpoint entries**
  (`LogCheckpoint`), each of which signs the tip. All three are ordinary entries
  in the chain, so the next checkpoint covers them too.

An append is serialised, as rule 6 of Hash Chain Integrity requires, and is
durable before it is reported written.

Every key named here is ML-DSA-65.
[`patterns/principal-identity`](../patterns/principal-identity.md) Design
Principle 6 lets a classical key prove a live session and nothing more, and a
seal is meant to outlive every session.

### The log key

The owner does not sign checkpoints with its long-lived key. It signs them with
a **log key**: an ML-DSA-65 key pair it mints itself, holds in memory only and
never writes anywhere. That is what
[`protocol/identity`](../protocol/identity.md) rule 7 requires of a service's
operating credential, and the log key's lifetime is that rule's. The long-lived
key stays where rule 8 protects it, and signs one statement for each log key
and each log that key will seal:

```
"weblisk/log-key/v2" 0x00 <log id> 0x00 <key id> 0x00 <not_after> 0x00 <key_protection>

<log id>          the log's id, as 64 lowercase hex characters
<key id>          the fingerprint (protocol/identity, Key Fingerprint) of the
                  log key's public key
<not_after>       the last instant the log key may sign, as
                  protocol/conventions:instant writes it
<key_protection>  how the long-lived key is protected, as the key_protection
                  value patterns/principal-identity gives it
```

The owner appends the statement, the log key's public key and the long-lived
public key that signed it as a key entry, before the log key signs anything in
that log. A key entry is never removed and never replaced. A new log key gets a
new key entry.

**A log key is replaced before it expires, not only at start.** The owner
mints its first log key when its process starts. Before that key's `not_after` passes, it mints the
next, in memory as it minted the first, and appends the next key entry to each
log it seals. A process that outlives a log key goes on sealing under the next
one, and a log key whose `not_after` has passed signs nothing more. From then,
sealing pauses only while the long-lived key cannot sign a new key entry, as
when the secret source that holds it is locked or out of reach, and resumes
with the first key entry it can sign.

**The log's statements have test vectors.** The key entry, the checkpoint and
the succession entry are fixed-form statements, and this corpus publishes
vectors for all three, `weblisk/log-key/v2`, `weblisk/log-checkpoint/v2` and
`weblisk/log-succession/v1`
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)). In
them `key id`, `outgoing` and `incoming` are fingerprints of published vector
keys, so an owner and a verifier test each statement against the very keys it
names.

A long-lived key whose `key_protection` is `development-only` is a key under
`kdf = none`. `protocol/identity` rule 6 requires such a key to be reported as
development-only, and a verifier reports every checkpoint sealed under it that
way.

### A change of long-lived key

At each position in a sealed log, one long-lived key is the log's
**authority**: the key whose key entries introduce the log keys that may sign
there. The first authority is the key that signed the log's first key entry.

When the owner replaces its long-lived key while it still holds the one it is
replacing, as a rotation does
([`protocol/identity`](../protocol/identity.md#rotation-flow)), it appends a
**succession entry** to each log that has an authority, before the incoming key
signs anything there. A log with no key entry yet has no authority to hand
over, and its first key entry makes the incoming key its first. The outgoing
key and the incoming key each sign:

```
"weblisk/log-succession/v1" 0x00 <log id> 0x00 <outgoing> 0x00 <incoming>

<outgoing>  the fingerprint of the key that was the authority, as 64 lowercase
            hex characters
<incoming>  the fingerprint of the key that becomes the authority, in the same
            form
```

The outgoing key's signature says that the key the log already trusted handed
over. The incoming key's signature says that the new key takes on the log as it
stands. So a verifier that trusts either key trusts the other, and a verifier
that trusts the key the owner uses now trusts every key a line of succession
entries leads back to. That is why a verifier needs one fingerprint, and not
one for every key the owner has used. Once a succession entry is in a log, no
log key an earlier authority introduced signs another checkpoint in it.

An owner that no longer holds the outgoing key, because it was lost or never
kept, cannot append a succession entry. Its next key entry is signed by a key
that is not the authority, and that key becomes the authority **unvouched**:
nothing in the log links it to the one before. A verifier then trusts the
authorities on each side of that entry only where it has a fingerprint for each
from somewhere other than the log.

### The checkpoint

```
"weblisk/log-checkpoint/v2" 0x00 <log id> 0x00 <seq> 0x00 <tip> 0x00 <issued_at>

<seq>        the seq of the last entry the checkpoint covers, in decimal
<tip>        the SHA-256 of that entry's stored line, as 64 lowercase hex
             characters
<issued_at>  when the checkpoint was signed, as protocol/conventions:instant
             writes it
```

A decimal field has no sign and no leading zeros. Every statement in this
section is a fixed-form statement
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)).

The owner issues a checkpoint whenever the tip has moved since the last one:
every `checkpoint_interval` its blueprint configures, when it shuts down
cleanly, and when a caller asks for one in order to export the log. A
checkpoint entry does not count as moving the tip. A checkpoint covers entries
before its own, and is signed with a log key whose key entry is already in the
log, was signed by the authority at the checkpoint's position, and has a
`not_after` that has not passed.

An entry is **sealed** once a checkpoint covers it, and **unsealed** until then.
A log key that is unavailable stops sealing and nothing else. Entries are still
appended, and the next checkpoint seals all of them at once. Wherever the owner
reports a log, it reports how many entries are unsealed, so a pause in sealing
is visible and never read as a sealed log.

### Verifying a sealed log

A verifier needs three things:

- the log's stored lines, exactly as stored, from the first to the checkpoint
  being checked;
- the fingerprint of one long-lived key the owner has signed with, from a
  source other than the log: normally the key the owner uses now, which the
  blueprint that owns the log says where to find. Succession entries carry that
  trust to every authority they link. An authority that became one unvouched is
  trusted only where the verifier has its fingerprint too. The log names every
  key it uses, and cannot vouch for any of them on its own;
- SHA-256, and an ML-DSA-65 verifier that behaves as `protocol/identity`'s
  Verify Signature does.

It needs no canonicaliser, no service and no network. Every digest is over
stored bytes, and every signed statement is rebuilt from fields the log holds.

1. **Chain.** Line 1 has `seq` 1 and a `previous_digest` of 64 zeros. Each
   later line has a `seq` one more than the line before it, and a
   `previous_digest` equal to the SHA-256 of that line. The log id is the
   SHA-256 of line 1.
2. **Keys.** Walk the key and succession entries in log order, keeping the
   authority, which starts as the `attesting_key` of the first key entry.
   - A succession entry passes when its `outgoing` is the authority at its
     position; the fingerprints of `outgoing_key` and `incoming_key` equal
     `outgoing` and `incoming`; and `outgoing_signature` verifies under
     `outgoing_key`, and `incoming_signature` under `incoming_key`, over the
     succession statement rebuilt from the log id, `outgoing` and `incoming`.
     Its incoming key becomes the authority. One that fails changes nothing.
   - A key entry passes when the fingerprint of `attesting_key` equals
     `attested_by`; the fingerprint of `public_key` equals `key_id`; and
     `signature` verifies under `attesting_key` over the log-key statement
     rebuilt from the log id, `key_id`, `not_after` and `key_protection`. One
     that passes, and whose attesting key is not the authority, makes that key
     the authority, unvouched. One that fails changes nothing.

   The verifier **trusts** an authority whose fingerprint it brought, and every
   authority joined to a trusted one by succession entries that passed.
3. **Checkpoint.** `tip` equals the SHA-256 of line `seq`, and `seq` is below
   the checkpoint entry's own; the key entry whose `key_id` is the checkpoint's
   `key` comes earlier in the log, passed step 2, was signed by the authority
   at the checkpoint's position, which the verifier trusts, and has a
   `not_after` no earlier than `issued_at`; and `signature` verifies under that
   key's `public_key` over the checkpoint statement rebuilt from the log id,
   `seq`, `tip` and `issued_at`.

What a verifier reports is computed from the log each time and never stored:

| Verdict | Values |
|---|---|
| Chain | `continuous`; `broken`, at the first `seq` that fails step 1; `unreadable`, where a line cannot be parsed |
| Sealing | sealed through `seq` N, by the latest checkpoint that passes step 3, with the number of entries after N that are unsealed; `unsealed` where no checkpoint passes step 3 |
| Authority | `unvouched`, for each authority the verifier does not trust, with the checkpoints signed under it, none of which passes step 3 |
| Key protection | `development-only`, for each checkpoint signed under a log key whose key entry says so |
| Countersignature | `uncountersigned`, for every checkpoint that no party but the owner has signed. This contract defines no countersignature, so every checkpoint made under it is `uncountersigned` |

A break is reported where it is. It is never repaired, truncated or re-chained.
A line that cannot be parsed is `unreadable`, not `broken`: a verifier that
could not read a line has refuted nothing.

**A checkpoint is the owner's own statement**, which is what `uncountersigned`
says. An owner holding its keys can write a different log and seal it. What
exposes that is an earlier checkpoint somebody else kept: the log must still
hold, at that `seq`, a line whose SHA-256 is that `tip`. A verifier SHOULD keep
each checkpoint it verifies, with the log id.

The verdict was once called `unwitnessed`. It was renamed because
[`architecture/content`](content.md#who-a-change-was-for) uses *witnessed* for
a party the service took from a token it verified, which is the owner
vouching, not a second party countersigning. Renaming a value an implementer
reports would break that implementer, and it was taken as a minor version
only because none reports it: the verdict was introduced and renamed before
any sealed log was built, and a blueprint that names the verdict requires
1.3.0 or later.

### An owner checks its own log

The owner checks its log from its latest checkpoint to the tip: step 1 over
those lines, and, for that checkpoint, that its `tip` is the SHA-256 of line
`seq` and that its signature verifies under the key its key entry introduced.
A log with no checkpoint yet is checked from its first line. The owner checks
before its first append after it starts, so a log changed while it was stopped
is found before anything is added to it, and before each checkpoint, so it
never seals a chain that does not hold. This is the owner's check on itself and
covers only those lines. Verifying the whole log is the verifier's, above.

A log that fails the check, because a line breaks the chain or cannot be read,
is never appended to or sealed. The owner goes on serving reads of it: refusing
to read would hide the evidence somebody now needs. Wherever it reports the
log, it reports the failure as the Chain verdict names it, `broken` or
`unreadable`, at the `seq` where the check failed. What a refused append means
to the owner's callers is for its blueprint to say.

---

## Types

```yaml
types:

  StoreInterface:
    description: The three operations every store owes, whatever backend satisfies it
    fields:
      get:
        type: string
        description: Retrieve one record by identifier, or report its absence. Absence is not an error
      put:
        type: string
        description: Write one record, subject to the precondition the caller supplied
      delete:
        type: string
        description: Remove one record. Deleting an absent record succeeds, so a retry is safe

  LogKey:
    description: The payload of a sealed log's key entry. Introduces a log key,
      signed by the owner's long-lived key. Never removed and never replaced.
      See Sealing a Chained Log
    fields:
      key_id:
        type: string
        required: true
        description: The fingerprint of public_key, as protocol/identity defines
          a fingerprint. What a checkpoint's key names
      public_key:
        type: string
        required: true
        description: The log key's ML-DSA-65 public key, base64url
      not_after:
        type: timestamp
        required: true
        description: The last instant at which the log key may sign
      key_protection:
        type: string
        required: true
        description: How the long-lived key that signed this entry is protected.
          One of the values patterns/principal-identity declares for
          Identity.key_protection, which this document does not repeat
      attested_by:
        type: string
        required: true
        description: The fingerprint of attesting_key
      attesting_key:
        type: string
        required: true
        description: The owner's long-lived ML-DSA-65 public key, base64url. A
          verifier trusts it only when its fingerprint is one the verifier
          obtained from somewhere other than the log
      signature:
        type: string
        required: true
        description: ML-DSA-65 signature by attesting_key over the
          weblisk/log-key/v2 statement, base64url

  LogSuccession:
    description: The payload of a sealed log's succession entry. Records that
      the owner's long-lived key changed, signed by the outgoing key and the
      incoming key. See Sealing a Chained Log
    fields:
      outgoing:
        type: string
        required: true
        description: The fingerprint of outgoing_key. The authority before this
          entry
      outgoing_key:
        type: string
        required: true
        description: The outgoing long-lived ML-DSA-65 public key, base64url
      incoming:
        type: string
        required: true
        description: The fingerprint of incoming_key. The authority from this
          entry on
      incoming_key:
        type: string
        required: true
        description: The incoming long-lived ML-DSA-65 public key, base64url
      outgoing_signature:
        type: string
        required: true
        description: ML-DSA-65 signature by outgoing_key over the
          weblisk/log-succession/v1 statement, base64url
      incoming_signature:
        type: string
        required: true
        description: ML-DSA-65 signature by incoming_key over the same
          statement, base64url

  LogCheckpoint:
    description: The payload of a sealed log's checkpoint entry. A signature
      over the log's tip. See Sealing a Chained Log
    fields:
      seq:
        type: integer
        required: true
        description: The seq of the last entry the checkpoint covers. Below the
          checkpoint entry's own seq
      tip:
        type: string
        required: true
        description: The SHA-256 of entry seq's stored line, lowercase hex
      issued_at:
        type: timestamp
        required: true
        description: When the checkpoint was signed
      key:
        type: string
        required: true
        description: The key_id of the log key that signed it, introduced by a
          key entry earlier in the log
      signature:
        type: string
        required: true
        description: ML-DSA-65 signature by that log key over the
          weblisk/log-checkpoint/v2 statement, base64url
```

---

## Security

```yaml
security:
  trust_model:
    description: |
      A store trusts its owner and nothing else. Ownership is declared, one
      component per store, so a caller reaching a store it does not own is a fault
      rather than a permission question. The backend is the only boundary a store
      does not control on both sides, and what it guarantees is what the platform
      blueprint says it does.
  boundaries:
    - boundary: Caller → Store. Every operation is confined to a store the caller
        owns, resolved before any I/O
    - boundary: Store → Backend. The one boundary not controlled on both sides;
        its guarantees are the platform's, stated rather than assumed
    - boundary: Record scope → Backend capability. A record whose scope requires
        protection the backend cannot provide does not reach it
    - boundary: Store → Installation state. Keys, secrets and run state are never
        reachable through a store operation
  enforcement:
    - rule: A component reads and writes only the stores it owns
      mechanism: Ownership declared per component; bindings carry only its own
        stores
    - rule: An identifier supplied by a caller cannot select another owner's store
      mechanism: Store resolved from the component's own declaration, never from
        a caller-supplied name
    - rule: A write whose scope exceeds what the backend can protect is refused,
        never downgraded
      mechanism: Ceiling check before the operation reaches the backend
    - rule: Deleting an absent record succeeds
      mechanism: Delete is idempotent, so a retry after a partial failure is safe
    - rule: Absence is not an error
      mechanism: Get reports absence distinctly from failure, so a caller does not
        treat a missing record as a fault
    - rule: A sealed log can be told from any other log, by anyone, without the
        owner
      mechanism: Checkpoints signed with ML-DSA-65 by a log key its owner's
        long-lived key introduced in the log itself, over statements a verifier
        rebuilds from stored fields. One long-lived key's fingerprint comes from
        somewhere other than the log, and succession entries both keys sign
        carry it to the rest
    - rule: No key that seals a log is ever written to disk
      mechanism: The log key is minted in memory and replaced before its
        not_after, per protocol/identity rule 7
    - rule: A log that does not verify is never added to or sealed
      mechanism: The owner checks from its latest checkpoint before its first
        append after start and before each checkpoint, and refuses to append to
        or seal a broken log while still serving reads of it
    - rule: No checkpoint is reported as more than its owner's word
      mechanism: Every checkpoint is reported uncountersigned
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
- [ ] A sealed log stores each entry as its RFC 8785 bytes and one line feed, and every `previous_digest` after the first is the SHA-256 of the stored line before it
- [ ] Once `weblisk/log-key/v2`, `weblisk/log-checkpoint/v2` and `weblisk/log-succession/v1` have test vectors, a checkpoint verifies with nothing but the log's lines, one long-lived key's fingerprint from outside the log and an ML-DSA-65 verifier, over a `weblisk/log-checkpoint/v2` statement rebuilt from `seq`, `tip` and `issued_at`
- [ ] Once `weblisk/log-key/v2`, `weblisk/log-checkpoint/v2` and `weblisk/log-succession/v1` have test vectors, a key entry signed by the log's authority precedes every checkpoint its log key signs, and the log key is found in no file
- [ ] Once `weblisk/log-key/v2`, `weblisk/log-checkpoint/v2` and `weblisk/log-succession/v1` have test vectors, a process that runs past its log key's `not_after` has appended the next key entry before it, and goes on sealing
- [ ] Once `weblisk/log-key/v2`, `weblisk/log-checkpoint/v2` and `weblisk/log-succession/v1` have test vectors, rotating the owner's long-lived key appends a succession entry, signed by both keys, to each log that has an authority before the new key signs anything there, and a verifier that has only the new key's fingerprint verifies checkpoints sealed before the rotation
- [ ] Once `weblisk/log-key/v2`, `weblisk/log-checkpoint/v2` and `weblisk/log-succession/v1` have test vectors, a key entry signed by a key that is not the authority, with no succession entry before it, makes a verifier that lacks that key's fingerprint report `unvouched`, and no checkpoint under it passes
- [ ] An owner whose log fails its check from the latest checkpoint appends nothing and seals nothing, still serves reads of the log, and reports where it fails
- [ ] Every checkpoint is reported `uncountersigned`
- [ ] With the log key unavailable, appends continue, no checkpoint is written, and the reported count of unsealed entries rises
- [ ] For every vector in [`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json) under `weblisk/log-key/v2`, `weblisk/log-checkpoint/v2` or `weblisk/log-succession/v1`, the owner, which signs those statements, and a verifier of them each pass the test [`architecture/generation`](generation.md#published-test-vectors) gives for a component that signs and one that verifies
- [ ] Changing one byte of an entry a checkpoint covers fails verification — the chain is `broken` at the next entry's `seq`, or, for the entry the checkpoint names, its `tip` no longer matches — and the failure is reported rather than repaired
