<!-- blueprint
type: pattern
name: data-sync
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/storage, patterns/state-machine]
platform: any
tier: free
-->

# Data Sync Pattern

Client-server data synchronisation for offline-first applications.
Defines the platform-wide contract for delta-based change transfer,
conflict resolution, version tracking, and offline queue management.
The sync agent (`agents/sync`) is the primary executor — this pattern
provides the reusable envelope format, state machine, and conflict
semantics that any agent or domain may adopt.

## Overview

Offline-first applications accumulate changes on the client while
disconnected. When connectivity resumes, those changes must be
reconciled with the server state and propagated to other clients.
This pattern formalises:

- **Sync envelope format** — a standardised delta batch container
  that carries changes, cursors, and metadata between client and
  server in both directions.
- **Conflict resolution strategies** — pluggable policies
  (last-write-wins, merge, manual review, server-wins, client-wins)
  declared per sync operation.
- **Version tracking** — sequence numbers and vector clocks for
  causality ordering and conflict detection.
- **Batch operation semantics** — chunked push/pull with size limits,
  pagination cursors, and atomic application.
- **Sync state machine** — a well-defined lifecycle from idle through
  syncing to resolution and completion.
- **Offline queue** — a client-side queue format for changes awaiting
  connectivity.
- **Bandwidth-aware transfer** — compression, pagination, and
  priority hints to minimise wire traffic.

Both push (client → server) and pull (server → client) use the
same envelope format and conflict semantics. The pattern is
bidirectional and symmetric.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TypeDefinition
          fields_used: [name, fields, description]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: sqlite-engine
          parameters: [engine, tables, indexes]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/state-machine
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: state-transitions
          parameters: [initial, transitions, guards]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Offline-First** — Clients operate fully offline. Sync is eventual, not blocking. Local writes never fail due to connectivity. The sync layer is responsible for eventual reconciliation when the network is available.
2. **Conflict-Explicit** — Every sync operation declares its conflict resolution strategy. No silent overwrites. When a conflict is detected the system MUST apply the declared strategy and log the outcome.
3. **Delta-Only Transfer** — Only changes travel over the wire. Full-state dumps are never used in normal operation. Deltas are computed against the client's last-known cursor and transmitted as ordered change records.
4. **Idempotent Application** — Applying the same delta batch twice produces the same result. Implementations MUST track applied batch IDs and de-duplicate on receipt.
5. **Bi-Directional** — Push and pull are symmetric operations using the same envelope format. The SyncEnvelope structure is identical regardless of direction.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: delta-push
      description: Push a batch of client-side changes to the server for merge
      parameters:
        - name: envelope
          type: SyncEnvelope
          required: true
          description: Delta batch with changes, cursor, and conflict strategy
        - name: compression
          type: string
          required: false
          default: none
          description: Wire compression (none, gzip, zstd)
        - name: priority
          type: string
          required: false
          default: normal
          description: Transfer priority hint (low, normal, high)
      inherits: Envelope validation, conflict detection, delta application, version advancement
      overridable: true
      override_constraints: Must preserve idempotent application semantics; must use declared conflict strategy

    - name: delta-pull
      description: Pull server-side changes since a cursor position
      parameters:
        - name: cursor
          type: SyncCursor
          required: true
          description: Opaque position marker from the client's last sync
        - name: max_batch_size
          type: int
          required: false
          default: 100
          description: Maximum number of change records per response batch
        - name: compression
          type: string
          required: false
          default: none
          description: Requested wire compression
      inherits: Cursor resolution, batched change retrieval, pagination
      overridable: true
      override_constraints: Must return changes in causal order; cursor must be opaque to clients

    - name: conflict-resolution
      description: Resolve conflicting changes between client and server versions
      parameters:
        - name: strategy
          type: ConflictStrategy
          required: true
          description: Resolution policy to apply
        - name: client_record
          type: ChangeRecord
          required: true
          description: Client version of the conflicting record
        - name: server_record
          type: ChangeRecord
          required: true
          description: Server version of the conflicting record
      inherits: Strategy dispatch, merge logic, audit logging
      overridable: true
      override_constraints: Must produce a ConflictResolution outcome; must never silently discard data

    - name: offline-queue
      description: Client-side queue for changes awaiting connectivity
      parameters:
        - name: max_queue_depth
          type: int
          required: false
          default: 10000
          description: Maximum queued entries before backpressure
        - name: flush_strategy
          type: string
          required: false
          default: oldest-first
          description: Order in which queued changes are flushed (oldest-first, priority, entity-grouped)
      inherits: Queue persistence, ordering guarantees, backpressure signalling
      overridable: true
      override_constraints: Must persist queue across app restarts; must flush in declared order

  types:
    - name: SyncEnvelope
      description: Batch container carrying delta changes, cursor, and sync metadata
      inherited_by: Types section
    - name: DeltaBatch
      description: Ordered list of change records within a single push or pull
      inherited_by: Types section
    - name: ChangeRecord
      description: Individual field-level change with entity, field, old/new values, and causality metadata
      inherited_by: Types section
    - name: ConflictStrategy
      description: Enumeration of supported conflict resolution policies
      inherited_by: Types section
    - name: ConflictResolution
      description: Outcome of a conflict resolution including strategy used, winner, and merged result
      inherited_by: Types section
    - name: SyncCursor
      description: Opaque position marker for incremental sync (sequence number or vector clock)
      inherited_by: Types section
    - name: SyncStatus
      description: Enumeration of sync operation states
      inherited_by: Types section
    - name: OfflineQueueEntry
      description: Queued change awaiting connectivity with priority and retry metadata
      inherited_by: Types section

  events:
    - topic: sync.push.started
      description: Client has initiated a push of local changes to the server
      payload: {client_id, batch_id, record_count, timestamp}
    - topic: sync.push.completed
      description: Push operation finished — all changes applied or conflicts raised
      payload: {client_id, batch_id, applied_count, conflict_count, duration_ms, timestamp}
    - topic: sync.pull.started
      description: Client has requested server-side changes since its last cursor
      payload: {client_id, cursor, timestamp}
    - topic: sync.pull.completed
      description: Pull operation finished — changes delivered to client
      payload: {client_id, record_count, new_cursor, duration_ms, timestamp}
    - topic: sync.conflict.detected
      description: A conflict was found during merge between client and server versions
      payload: {client_id, entity, record_id, strategy, client_version, server_version, timestamp}
    - topic: sync.conflict.resolved
      description: A conflict was resolved (automatically or via manual review)
      payload: {client_id, entity, record_id, strategy, resolution, winner, timestamp}
    - topic: sync.failed
      description: A sync operation failed after retries
      payload: {client_id, batch_id, direction, error_code, error_message, timestamp}
```

---

## Types

### SyncEnvelope

The top-level container for every sync request and response.
Both push and pull use this structure.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| envelope_id | string | yes | Unique ID for this envelope (UUID v7) |
| direction | string | yes | `push` or `pull` |
| client_id | string | yes | Originating client identifier |
| batch | DeltaBatch | yes | The delta changes |
| cursor | SyncCursor | yes | Position marker (before for push, after for pull) |
| conflict_strategy | ConflictStrategy | yes | Declared resolution strategy |
| compression | string | no | Wire encoding (`none`, `gzip`, `zstd`) |
| priority | string | no | Transfer hint (`low`, `normal`, `high`) |
| timestamp | int64 | yes | Envelope creation time (Unix ms) |
| metadata | object | no | Arbitrary key-value pairs for tracing |

### DeltaBatch

An ordered list of change records within a single envelope.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| batch_id | string | yes | Unique batch ID for idempotency checks |
| records | []ChangeRecord | yes | Ordered change records |
| record_count | int | yes | Number of records (redundant for validation) |
| total_bytes | int | no | Uncompressed payload size in bytes |
| page | int | no | Page number when batch is paginated |
| has_more | boolean | no | Whether additional pages remain |

### ChangeRecord

A single field-level change. Represents one mutation to one entity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| record_id | string | yes | Unique change record ID |
| entity | string | yes | Entity/table name |
| entity_id | string | yes | Primary key of the affected record |
| field | string | no | Specific field changed (null for whole-record ops) |
| old_value | any | no | Previous value (null for inserts) |
| new_value | any | no | New value (null for deletes) |
| operation | string | yes | `insert`, `update`, `delete` |
| version | string | yes | Version vector or sequence number |
| timestamp | int64 | yes | When the change was made (Unix ms) |
| source | string | yes | `client` or `server` |
| checksum | string | no | SHA-256 of the serialised record for integrity |

### ConflictStrategy

Enumeration of supported conflict resolution policies.

| Value | Description |
|-------|-------------|
| `last-write-wins` | Record with the latest timestamp wins |
| `merge` | Field-level merge — non-overlapping fields combined, overlapping fields use latest |
| `manual-review` | Conflict is flagged for human resolution |
| `server-wins` | Server version always takes priority |
| `client-wins` | Client version always takes priority |

### ConflictResolution

The recorded outcome of a conflict resolution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| conflict_id | string | yes | Unique conflict ID |
| entity | string | yes | Entity/table name |
| entity_id | string | yes | Record primary key |
| strategy | ConflictStrategy | yes | Strategy that was applied |
| winner | string | yes | `client`, `server`, or `merged` |
| client_version | object | yes | Client's version of the record |
| server_version | object | yes | Server's version of the record |
| merged_result | object | no | Merged output (when strategy is `merge`) |
| resolved_by | string | yes | `auto` or operator ID for manual resolution |
| resolved_at | int64 | yes | Resolution timestamp (Unix ms) |

### SyncCursor

Opaque position marker for incremental sync. Clients MUST treat
cursors as opaque strings — internal structure is implementation-defined.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| value | string | yes | Opaque cursor value |
| type | string | yes | `sequence` or `vector-clock` |
| issued_at | int64 | yes | When the cursor was issued |
| expires_at | int64 | no | Cursor expiry (after which a full re-sync is required) |

### SyncStatus

Enumeration of sync operation lifecycle states.

| Value | Description |
|-------|-------------|
| `idle` | No sync in progress |
| `pushing` | Client is pushing changes to the server |
| `pulling` | Server is sending changes to the client |
| `resolving` | Conflicts are being resolved |
| `complete` | Sync operation finished successfully |
| `failed` | Sync operation failed |

### OfflineQueueEntry

A queued change on the client awaiting connectivity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| queue_id | string | yes | Unique queue entry ID |
| change | ChangeRecord | yes | The queued change record |
| queued_at | int64 | yes | When the entry was queued (Unix ms) |
| priority | string | no | `low`, `normal`, `high` — affects flush order |
| retry_count | int | no | Number of failed push attempts for this entry |
| last_error | string | no | Last error message if a push attempt failed |
| status | string | yes | `pending`, `flushing`, `flushed`, `failed` |

---

## Sync State Machine

The sync operation lifecycle follows a deterministic state machine.
Agents extending this pattern inherit these transitions.

```yaml
state_machine:
  SyncOperation:
    initial: idle
    transitions:
      - from: idle
        to: pushing
        trigger: push_initiated
        guard: offline queue is non-empty
        side_effect: emit sync.push.started

      - from: idle
        to: pulling
        trigger: pull_initiated
        guard: cursor is valid and not expired
        side_effect: emit sync.pull.started

      - from: pushing
        to: resolving
        trigger: conflicts_detected
        guard: at least one version mismatch between client and server
        side_effect: emit sync.conflict.detected for each conflict

      - from: pushing
        to: complete
        trigger: push_applied
        guard: all changes applied without conflict
        side_effect: emit sync.push.completed

      - from: pulling
        to: resolving
        trigger: conflicts_detected
        guard: pulled changes conflict with pending local changes
        side_effect: emit sync.conflict.detected for each conflict

      - from: pulling
        to: complete
        trigger: pull_applied
        guard: all pulled changes applied cleanly
        side_effect: emit sync.pull.completed

      - from: resolving
        to: complete
        trigger: all_resolved
        guard: no unresolved conflicts remain
        side_effect: emit sync.conflict.resolved for each resolution

      - from: resolving
        to: failed
        trigger: resolution_failed
        guard: manual review required and timeout exceeded
        side_effect: emit sync.failed

      - from: pushing
        to: failed
        trigger: push_error
        guard: unrecoverable error (network, storage)
        side_effect: emit sync.failed

      - from: pulling
        to: failed
        trigger: pull_error
        guard: unrecoverable error (network, storage)
        side_effect: emit sync.failed

      - from: complete
        to: idle
        trigger: reset
        guard: always

      - from: failed
        to: idle
        trigger: reset
        guard: always
```

### State Diagram

```
              push_initiated           conflicts_detected
  ┌──────┐ ──────────────── ┌─────────┐ ──────────────── ┌───────────┐
  │ idle │                  │ pushing │                  │ resolving │
  └──┬───┘ ◄── reset ────  └────┬────┘                  └─────┬─────┘
     │                          │ push_applied                 │ all_resolved
     │ pull_initiated           ▼                              ▼
     │                     ┌──────────┐                   ┌──────────┐
     └───────────────────► │ pulling  │ ─── pull_applied ─► complete │
                           └────┬─────┘                   └──────────┘
                                │ pull_error / push_error
                                ▼
                           ┌──────────┐
                           │  failed  │
                           └──────────┘
```

---

## Configuration

```yaml
config:
  conflict_strategy:
    type: enum
    default: last-write-wins
    values: [last-write-wins, merge, manual-review, server-wins, client-wins]
    overridable: true
    description: Default conflict resolution strategy for sync operations

  batch_size:
    type: int
    default: 100
    min: 1
    max: 10000
    overridable: true
    description: Maximum change records per delta batch

  max_payload_size:
    type: int
    default: 1048576
    min: 1024
    max: 10485760
    overridable: true
    description: Maximum uncompressed envelope size in bytes (default 1 MB)

  cursor_ttl:
    type: int
    default: 604800
    min: 3600
    max: 2592000
    overridable: true
    description: Cursor expiry in seconds (default 7 days). Expired cursors require full re-sync.

  compression:
    type: enum
    default: none
    values: [none, gzip, zstd]
    overridable: true
    description: Wire compression for delta batches

  offline_queue_depth:
    type: int
    default: 10000
    min: 100
    max: 100000
    overridable: true
    description: Maximum offline queue entries before backpressure

  sync_timeout:
    type: int
    default: 30
    min: 5
    max: 120
    overridable: true
    description: Per-operation timeout in seconds

  retry_max_attempts:
    type: int
    default: 3
    min: 1
    max: 10
    overridable: true
    description: Maximum retry attempts for transient failures

  retry_backoff:
    type: string
    default: exponential
    values: [fixed, exponential]
    overridable: true
    description: Retry backoff strategy
```

---

## Error Handling

### Error Codes

| Code | Name | Description | Recovery |
|------|------|-------------|----------|
| `SYNC_BATCH_TOO_LARGE` | Batch size exceeded | Batch contains more records than `batch_size` | Split into smaller batches |
| `SYNC_PAYLOAD_TOO_LARGE` | Payload size exceeded | Envelope exceeds `max_payload_size` | Compress or paginate |
| `SYNC_CURSOR_EXPIRED` | Cursor expired | Client cursor older than `cursor_ttl` | Perform full re-sync |
| `SYNC_CURSOR_INVALID` | Invalid cursor | Cursor cannot be parsed or does not exist | Request new cursor |
| `SYNC_CONFLICT_UNRESOLVED` | Unresolved conflict | Manual review required but not completed | Resolve via operator action |
| `SYNC_VERSION_MISMATCH` | Version mismatch | Client base version does not match server | Re-pull then re-push |
| `SYNC_QUEUE_FULL` | Offline queue full | Queue depth exceeds `offline_queue_depth` | Flush queue or increase limit |
| `SYNC_CHECKSUM_FAILED` | Integrity check failed | Record checksum does not match payload | Re-transmit the batch |
| `SYNC_TIMEOUT` | Operation timeout | Sync exceeded `sync_timeout` | Retry with backoff |

### Error Response Format

Sync errors follow the protocol/spec `ErrorResponse` structure:

```json
{
  "code": "SYNC_BATCH_TOO_LARGE",
  "message": "Batch contains 250 records, maximum is 100",
  "detail": {
    "batch_id": "abc123",
    "record_count": 250,
    "max_allowed": 100
  }
}
```

### Retry Semantics

- Transient errors (`SYNC_TIMEOUT`, network failures) are retried
  up to `retry_max_attempts` with the configured backoff strategy.
- Permanent errors (`SYNC_CURSOR_EXPIRED`, `SYNC_CHECKSUM_FAILED`)
  are NOT retried — the client must take corrective action.
- Conflict errors (`SYNC_CONFLICT_UNRESOLVED`) are not retried; they
  require strategy change or manual resolution.

---

## Implementation Notes

- **Envelope is the unit of transfer**: All sync communication is
  wrapped in a SyncEnvelope. Implementations MUST NOT send raw change
  records outside an envelope.
- **Cursor opacity**: Clients MUST treat SyncCursor values as opaque.
  The server may use sequence numbers, vector clocks, or any internal
  representation. Clients store and return cursors without parsing.
- **Idempotency via batch ID**: Every DeltaBatch carries a unique
  `batch_id`. Servers MUST track applied batch IDs and skip
  re-application. Batch ID deduplication window should match
  `cursor_ttl` at minimum.
- **Atomic batch application**: All changes in a DeltaBatch SHOULD be
  applied atomically (single transaction). If any record fails, the
  entire batch is rolled back and an error returned.
- **Field-level merge**: When using the `merge` conflict strategy,
  non-overlapping field changes are combined. Overlapping fields use
  `last-write-wins` at the field level. The merged result is logged
  in the ConflictResolution record.
- **Version vectors**: Prefer vector clocks over wall-clock timestamps
  for conflict detection. Wall-clock is acceptable only when all
  participants have synchronised clocks (NTP within 1s tolerance).
- **Compression negotiation**: Clients declare desired compression in
  the envelope. Servers SHOULD honour the request but MAY fall back
  to `none`. The response envelope indicates the actual compression
  used.
- **Pagination**: For large pull responses, use the DeltaBatch
  `page` and `has_more` fields. Clients MUST continue pulling until
  `has_more` is `false`.
- **Offline queue persistence**: The offline queue MUST survive app
  restarts and device reboots. IndexedDB or SQLite are recommended
  client-side stores.
- **Checksum verification**: When `checksum` is present on a
  ChangeRecord, the receiver MUST validate it before application.
  Invalid checksums cause the entire batch to be rejected.
- **Backpressure**: When the offline queue reaches `offline_queue_depth`,
  implementations SHOULD signal backpressure to the application layer
  (e.g., reject new writes with a queue-full error) rather than
  silently dropping changes.

---

## Verification Checklist

### Envelope & Transfer

- [ ] All sync operations use the SyncEnvelope format — no raw change records on the wire
- [ ] Delta batches carry a unique `batch_id` and are de-duplicated on the server
- [ ] Applying the same DeltaBatch twice produces identical state (idempotency)
- [ ] Envelope `direction` field is set correctly for push and pull operations
- [ ] Batch `record_count` matches the actual length of the `records` array
- [ ] Payloads exceeding `max_payload_size` are rejected with `SYNC_PAYLOAD_TOO_LARGE`
- [ ] Batches exceeding `batch_size` are rejected with `SYNC_BATCH_TOO_LARGE`

### Conflict Resolution

- [ ] Every sync declares a `conflict_strategy` — no implicit default at the wire level
- [ ] Conflicts are detected when server version diverges from client's base version
- [ ] `last-write-wins` selects the record with the higher timestamp
- [ ] `merge` combines non-overlapping fields and applies LWW to overlapping fields
- [ ] `manual-review` flags the conflict without applying either version
- [ ] `server-wins` and `client-wins` deterministically select the correct side
- [ ] All conflict resolutions are logged with full audit trail (ConflictResolution type)

### Cursors & Versioning

- [ ] Clients treat SyncCursor values as opaque — no client-side parsing
- [ ] Expired cursors return `SYNC_CURSOR_EXPIRED` and require full re-sync
- [ ] Pull responses return changes in causal order relative to the cursor
- [ ] Cursor advances atomically with batch application

### Offline Queue

- [ ] Offline queue persists across app restarts
- [ ] Queue entries are flushed in the declared order (oldest-first by default)
- [ ] Queue depth limit is enforced — `SYNC_QUEUE_FULL` raised at capacity
- [ ] Failed flush attempts increment `retry_count` on the queue entry

### State Machine

- [ ] Sync operations follow the declared state machine transitions
- [ ] Events are emitted at each state transition (push/pull started, completed, failed)
- [ ] `sync.conflict.detected` fires for each conflict before resolution
- [ ] `sync.conflict.resolved` fires for each resolved conflict
- [ ] `sync.failed` fires on unrecoverable errors with error detail
- [ ] State resets to `idle` after `complete` or `failed`
