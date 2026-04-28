<!-- blueprint
type: agent
kind: infrastructure
name: sync
version: 1.1.0
port: 9751
requires: [protocol/spec, protocol/types, architecture/agent]
extends: [patterns/offline, patterns/observability, patterns/storage, patterns/scope, patterns/policy, patterns/safety, patterns/contract, patterns/privacy, patterns/security, patterns/governance]
depends_on: []
platform: any
tier: free
-->

# Sync Agent

Background data synchronisation between client-side IndexedDB store
and server database. Supports conflict resolution strategies and
batched operations.

## Overview

The sync agent bridges offline-capable clients with the server's
persistent store. Clients accumulate changes in IndexedDB while
offline and push them when connectivity resumes. The agent also
runs on a schedule to pull server-side changes and push them to
connected clients via real-time channels.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
          request_type: AgentManifest
          response_fields: [agent_id, token, services]
        - path: /v1/message
          methods: [POST]
          request_type: AgentMessage
          response_fields: [status, response]
        - path: /v1/health
          methods: [POST]
          response_fields: [status, details]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskRequest
          fields_used: [id, from, target_agent, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: EventEnvelope
          fields_used: [from, to, action, payload, trace_id]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: startup-sequence
          parameters: [identity, storage, registration, health]
        - behavior: shutdown-sequence
          parameters: [drain, deregister, close]
        - behavior: health-reporting
          parameters: [status, details]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

extends:
  - pattern: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: metrics
          parameters: [gauge, counter, histogram]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: sqlite-engine
          parameters: [engine, tables, indexes, relationships, constraints]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: identity
          parameters: [keypair, signing, verification]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/governance
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: self-governance
          parameters: [reconciliation, change-assessment]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

depends_on: []
  # No runtime agent dependencies. The sync agent operates independently.
  # It communicates with clients directly and with the server database.
```

---

## Capabilities

```json
{
  "capabilities": [
    {"name": "database:read", "resources": ["*"]},
    {"name": "database:write", "resources": ["*"]},
    {"name": "realtime:publish", "resources": ["sync/*"]}
  ],
  "inputs": [
    {"name": "sync_push", "type": "json", "description": "Client change batch"}
  ],
  "outputs": [
    {"name": "sync_result", "type": "json", "description": "Merge result with resolved conflicts"}
  ],
  "collaborators": []
}
```

### Trigger Summary

| Trigger | Description |
|---------|-------------|
| `client.sync.push` | Client pushes accumulated offline changes |
| Schedule: `*/5 * * * *` | Every 5 minutes — pull server changes, notify clients |

## Configuration

```yaml
config:
  conflict_resolution: last-write-wins   # last-write-wins | client-wins | server-wins | manual
  batch_size: 100                        # max records per sync batch
  sync_interval: 300                     # seconds between scheduled syncs
  max_payload_size: 1048576              # 1 MB max per push
```

### Conflict Resolution Strategies

| Strategy | Description |
|----------|-------------|
| `last-write-wins` | Record with the latest timestamp wins |
| `client-wins` | Client version always takes priority |
| `server-wins` | Server version always takes priority |
| `manual` | Conflict is flagged for manual resolution |

## Execute Workflow

```
Phase 1 — Receive push:
  Parse client change batch from trigger payload.
  Validate batch size does not exceed config.batch_size.
  Each change record: {table, id, version, timestamp, data, deleted}

Phase 2 — Fetch server state:
  For each change record, load the current server-side version.
  Compare version vectors.

Phase 3 — Detect conflicts:
  A conflict exists when:
  - Server version > client's base version (server changed since client last synced)
  - Both client and server have modifications since last sync point

Phase 4 — Resolve conflicts:
  Apply configured conflict_resolution strategy.
  For "manual": mark record as conflicted, include both versions in result.
  For automatic strategies: pick the winner, discard the loser.

Phase 5 — Apply changes:
  Write resolved records to server database.
  Update version vectors.
  Track which records were applied, skipped, or conflicted.

Phase 6 — Respond:
  Return sync result with:
  - applied: records successfully written
  - conflicts: records requiring manual resolution (if strategy = manual)
  - server_changes: records changed on server since client's last sync
  - new_version: client's new sync checkpoint
```

## HandleMessage Actions

### sync_push

Client pushes a batch of offline changes.

- Input: `payload.changes` — array of change records
- Input: `payload.last_sync_version` — client's last known version
- Process: execute full sync workflow
- Output: `{applied: [...], conflicts: [...], server_changes: [...], new_version: "..."}`

### sync_pull

Client requests server changes since a checkpoint.

- Input: `payload.since_version` — version to pull from
- Process: query server for records changed since version
- Output: `{changes: [...], new_version: "..."}`

### get_status

Returns current sync state and statistics.

- Output: `{connected_clients: N, pending_conflicts: N, last_sync: timestamp}`

## Types

### ChangeRecord

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| table | string | yes | Target table/collection name |
| id | string | yes | Record ID |
| version | string | yes | Version vector or timestamp |
| timestamp | int64 | yes | When the change was made |
| data | object | no | Record data (null if deleted) |
| deleted | boolean | no | Whether this is a deletion |

### SyncResult

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| applied | []ChangeRecord | yes | Records successfully written |
| conflicts | []ConflictRecord | no | Unresolved conflicts |
| server_changes | []ChangeRecord | yes | Server changes client needs |
| new_version | string | yes | New sync checkpoint |

### ConflictRecord

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| table | string | yes | Table name |
| id | string | yes | Record ID |
| client_version | object | yes | Client's version of the record |
| server_version | object | yes | Server's version of the record |

---

## Storage

```yaml
storage:
  engine: sqlite

  tables:
    sync_versions:
      description: Version checkpoints per client
      fields:
        client_id: {type: string, primary_key: true}
        last_sync_version: {type: string}
        last_sync_at: {type: int64}
      indexes:
        - name: idx_sync_time
          fields: [last_sync_at]
          type: btree

    sync_conflicts:
      description: Unresolved conflicts awaiting manual resolution
      fields:
        conflict_id: {type: string, format: uuid-v7, primary_key: true}
        table: {type: string}
        record_id: {type: string}
        client_version: {type: object}
        server_version: {type: object}
        client_id: {type: string}
        created_at: {type: int64}
        resolved_at: {type: int64, optional: true}
        resolution: {type: string, enum: [pending, client_wins, server_wins, merged], default: pending}
      indexes:
        - name: idx_conflict_status
          fields: [resolution, created_at]
          type: btree
        - name: idx_conflict_record
          fields: [table, record_id]
          type: btree

  retention:
    sync_versions:
      policy: indefinite (one row per active client)
      cleanup: remove clients inactive > 90 days
    sync_conflicts:
      policy: 30 days after resolution
      cleanup: automatic sweep

  backup:
    sync_versions:
      frequency: daily
      format: JSON export
      path: .weblisk/backups/sync/versions_{ISO8601}.json
    sync_conflicts:
      frequency: daily
      format: JSON export of unresolved conflicts
      path: .weblisk/backups/sync/conflicts_{ISO8601}.json
```

---

## State Machine

```yaml
state_machine:
  agent:
    initial: created
    transitions:
      - from: created
        to: registered
        trigger: orchestrator_ack
        validates: agent_id assigned in response
      - from: registered
        to: active
        trigger: sync_processing_ready
        validates: storage connected, schema validated
      - from: active
        to: degraded
        trigger: storage_error
        validates: database write failed after retries
      - from: degraded
        to: active
        trigger: storage_recovered
        validates: successful write operation
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: signal received (SIGTERM, system.shutdown, or API)
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in_flight syncs = 0 OR drain timeout (30s) elapsed

  entity.SyncOperation:
    initial: received
    transitions:
      - from: received
        to: validating
        trigger: push_received
        validates: batch size within limits
      - from: validating
        to: conflict_detection
        trigger: validation_passed
        validates: all change records parse correctly
      - from: validating
        to: rejected
        trigger: validation_failed
        validates: error logged with details
      - from: conflict_detection
        to: resolving
        trigger: conflicts_found
        validates: at least one version mismatch
      - from: conflict_detection
        to: applying
        trigger: no_conflicts
        validates: all server versions match client base versions
      - from: resolving
        to: applying
        trigger: resolution_complete
        validates: all conflicts resolved or flagged for manual
      - from: applying
        to: completed
        trigger: writes_committed
        validates: all records written atomically
        side_effect: publish to sync/* realtime channel
      - from: applying
        to: failed
        trigger: write_error
        validates: transaction rolled back
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults
  Pre-check:   Process has read access to environment
  Validates:   All config values within constraints
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/sync/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize Storage
  Action:      Connect to storage engine
  Pre-check:   Storage engine available
  Validates:   SELECT 1 succeeds within 5 seconds
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE
  Backout:     Close partial connection

Step 4 — Validate Schema
  Action:      Verify sync_versions and sync_conflicts tables
  Pre-check:   Step 3 validated
  Validates:   Tables exist with correct schema and indexes
  On Fail:     Run migration → if fails EXIT with MIGRATION_FAILED
  Backout:     Reverse migration

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-4 validated
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (idempotent)

Step 6 — Subscribe to Events
  Action:      Subscribe to: client.sync.push, system.shutdown,
               system.blueprint.changed
  Pre-check:   Step 5 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT
  Backout:     Unsubscribe all, deregister, close storage

Step 7 — Initialize Realtime Channel
  Action:      Open sync/* publish channel for client notifications
  Pre-check:   Registration complete
  Validates:   Channel writable
  On Fail:     Enter degraded state (sync works, realtime push disabled)
  Backout:     None

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9751, conflict_resolution: config.conflict_resolution}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Syncs
  Action:      Return 503 for new sync_push requests
  Validates:   No new syncs accepted

Step 3 — Drain In-Flight
  Action:      Wait for active sync operations to complete (up to 30s)
  Validates:   in_flight = 0
  On Timeout:  Roll back any uncommitted transactions

Step 4 — Close Realtime Channel
  Action:      Close sync/* publish channel
  Validates:   Channel closed

Step 5 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges

Step 6 — Close Storage
  Action:      Close database connection

Step 7 — Exit
  Log: lifecycle.stopped {uptime_seconds, syncs_processed, conflicts_resolved}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - storage = connected
      - realtime_channel = available
    response:
      status: healthy
      details: {connected_clients, pending_conflicts, storage_status}

  degraded:
    conditions:
      - storage errors (but retrying)
      - realtime channel unavailable (sync still works via pull)
    response:
      status: degraded
      details: {reason, last_error}

  unhealthy:
    conditions:
      - storage unreachable after retries
    response:
      status: unhealthy
      details: {reason, since}
```

### Self-Update

```
Step 1 — Validate new blueprint
Step 2 — Check migration requirements
Step 3 — Execute migration (drain syncs, migrate, resume)
Step 4 — Reload configuration
Final:  Log lifecycle.version_updated {from, to}
```

---

## Implementation Notes

- **Idempotency**: Sync pushes MUST be idempotent. Repeated pushes of
  the same batch should produce the same result.
- **Batching**: Process changes in batches to avoid memory pressure.
  Reject batches exceeding `batch_size`.
- **Version vectors**: Use logical timestamps or version vectors rather
  than wall-clock time for conflict detection where possible.
- **Atomic writes**: All changes in a batch SHOULD be applied
  atomically (transaction). If any fails, roll back the entire batch.
- **Real-time push**: After processing a sync, publish changes to the
  `sync/*` real-time channel so other connected clients update.
- **Compression**: For large batches, implementations SHOULD support
  gzip compression on the wire.

---

## Triggers

```yaml
triggers:
  - name: client_push
    type: event
    topic: client.sync.push
    description: Client pushes accumulated offline changes

  - name: scheduled_pull
    type: schedule
    interval: config.sync_interval
    description: Pull server changes and notify connected clients

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "sync"
    description: Self-update if sync blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [sync_push, sync_pull, get_status, resolve_conflict]
    description: Agent-to-agent and operator actions
```

---

## Actions

### sync_push

Client pushes a batch of offline changes.

**Purpose:** Receive, validate, and merge client changes with server state.

**Input:** `{changes: ChangeRecord[], last_sync_version: string}`

**Processing:**

```
1. Validate batch:
   a. changes.length <= config.batch_size
   b. Total payload <= config.max_payload_size
   c. Each ChangeRecord parses correctly (table, id, version required)
2. For each change, fetch server-side version
3. Detect conflicts (server version > client base version)
4. Apply conflict_resolution strategy:
   a. last-write-wins: compare timestamps
   b. client-wins: always accept client
   c. server-wins: always reject client change
   d. manual: flag for manual resolution, store in sync_conflicts
5. Apply resolved changes atomically (transaction)
6. Update sync_versions checkpoint for this client
7. Collect server changes since last_sync_version
8. Publish to sync/* realtime channel
9. Return result
```

**Output:** `{applied: ChangeRecord[], conflicts: ConflictRecord[], server_changes: ChangeRecord[], new_version: string}`

**Errors:**

```yaml
errors:
  - code: BATCH_TOO_LARGE
    condition: changes.length > config.batch_size
    retryable: false
  - code: PAYLOAD_TOO_LARGE
    condition: Total payload > config.max_payload_size
    retryable: false
  - code: INVALID_CHANGE
    condition: ChangeRecord missing required fields
    retryable: false
  - code: STORAGE_ERROR
    condition: Database write failure
    retryable: true
```

**Side Effects:** Writes to server database, updates sync_versions, may write sync_conflicts. Publishes to sync/* channel.

**Idempotency:** Same batch with same last_sync_version produces same result.

---

### sync_pull

Client requests server changes since a checkpoint.

**Purpose:** Deliver server-side changes for client synchronization.

**Input:** `{since_version: string, limit?: int}`

**Processing:**

```
1. Validate since_version exists
2. Query server for records changed since version
3. Apply limit (default 1000)
4. Compute new version checkpoint
5. Return changes
```

**Output:** `{changes: ChangeRecord[], new_version: string}`

**Errors:** `INVALID_INPUT` if since_version is invalid.

**Side Effects:** None (read-only).

---

### get_status

Return current sync agent status.

**Purpose:** Provide operational visibility.

**Input:** `{}`

**Output:** `{connected_clients: int, pending_conflicts: int, last_sync: int64}`

**Side Effects:** None (read-only).

---

### resolve_conflict

Manually resolve a sync conflict.

**Purpose:** Allow operator to choose winner for manual-resolution conflicts.

**Input:** `{conflict_id: string, resolution: "client_wins" | "server_wins" | "merged", merged_data?: object}`

**Processing:**

```
1. Look up conflict_id in sync_conflicts
2. If not found → NOT_FOUND
3. Apply chosen resolution
4. Write winning version to server database
5. Update sync_conflicts with resolution and resolved_at
6. Publish to sync/* channel
```

**Output:** `{resolved: true, conflict_id}`

**Errors:** `NOT_FOUND`, `INVALID_INPUT`, `STORAGE_ERROR`

**Manual Override:** Operator-only action.

---

## Collaboration

```yaml
events_published:
  - topic: sync.push.completed
    payload: {client_id, applied_count, conflict_count, new_version}
    when: Client push processed successfully

  - topic: sync.conflict.detected
    payload: {conflict_id, table, record_id, strategy}
    when: Conflict detected during push

  - topic: sync.conflict.resolved
    payload: {conflict_id, resolution}
    when: Conflict resolved (automatic or manual)

events_subscribed:
  - topic: client.sync.push
    payload: {client_id, changes, last_sync_version}
    action: Process sync push

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "sync"
    action: Self-update procedure

direct_messages:
  - target: none
    reason: Sync agent communicates with clients directly, not with other agents
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All sync operations and conflict resolution are autonomous
  supervised:    Sync automatic; manual-strategy conflicts require operator
  manual-only:   All syncs require operator invocation

overridable_behaviors:
  - behavior: conflict_resolution
    default: config.conflict_resolution strategy
    override: Change per-table or per-record resolution strategy
    audit: logged

  - behavior: realtime_push
    default: enabled
    override: Disable realtime channel notifications
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: resolve_conflict
    description: Manually resolve a flagged sync conflict
    allowed: operator

  - action: force_sync
    description: Trigger immediate server-to-client sync cycle
    allowed: operator

  - action: purge_conflicts
    description: Remove resolved conflicts older than threshold
    allowed: operator

  - action: reset_client
    description: Reset a client's sync checkpoint to force full re-sync
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Operator identity from auth token
  why: Required
  storage: Appended to system audit log
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT modify records outside the scope of the sync request
    - MUST NOT push changes to clients that did not request them (except realtime subscribers)
    - Write rate bounded by config.batch_size per sync operation

  forbidden_actions:
    - MUST NOT accept batches exceeding config.max_payload_size
    - MUST NOT apply partial batches (all-or-nothing transactions)
    - MUST NOT auto-resolve conflicts when strategy = manual
    - MUST NOT delete sync_versions for active clients

  resource_limits:
    memory: 256 MB (process limit)
    batch_size: config.batch_size records max per push
    payload_size: config.max_payload_size bytes max
    sync_conflicts_rows: 100000 max (reject new conflicts if exceeded)
```

---

## Security

```yaml
security:
  permissions:
    - capability: database:read
      resources: ["*"]
      description: Read any table for sync comparison

    - capability: database:write
      resources: ["*"]
      description: Write merged records to any table

    - capability: realtime:publish
      resources: ["sync/*"]
      description: Push changes to connected clients

  data_sensitivity:
    - data: Sync payloads (change records)
      classification: high
      handling: Encrypted in transit (TLS), logged as record counts only

    - data: Conflict records (both versions)
      classification: high
      handling: Stored encrypted at rest, accessible only to operators

    - data: Client sync checkpoints
      classification: low
      handling: Logged freely

  access_control:
    - caller: Authenticated client (via session token)
      actions: [sync_push, sync_pull, get_status]

    - caller: Operator (auth token with operator role)
      actions: [sync_push, sync_pull, get_status, resolve_conflict,
                force_sync, purge_conflicts, reset_client]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Push batch with no conflicts
    action: sync_push
    input:
      changes:
        - {table: posts, id: post-1, version: "v2", timestamp: 1712160000, data: {title: "Updated"}}
        - {table: posts, id: post-2, version: "v1", timestamp: 1712160001, data: {title: "New"}, deleted: false}
      last_sync_version: "v1"
    expected:
      applied: [post-1, post-2]
      conflicts: []
      new_version: "v3"
    validates:
      - Records written atomically
      - Version checkpoint advanced
      - Realtime channel notified

  - name: Pull server changes
    action: sync_pull
    input: {since_version: "v1"}
    expected: {changes: [...], new_version: "v3"}
    validates:
      - Returns only changes since checkpoint

  - name: Get sync status
    action: get_status
    input: {}
    expected: {connected_clients: N, pending_conflicts: 0}
```

### Error Cases

```yaml
  - name: Batch exceeds max size
    action: sync_push
    input: {changes: "[101 records]", last_sync_version: "v1"}
    expected_error: BATCH_TOO_LARGE
    validates: Batch size limit enforced

  - name: Invalid change record
    action: sync_push
    input: {changes: [{id: "no-table"}], last_sync_version: "v1"}
    expected_error: INVALID_CHANGE
    validates: ChangeRecord schema validated

  - name: Resolve non-existent conflict
    action: resolve_conflict
    input: {conflict_id: nonexistent, resolution: client_wins}
    expected_error: NOT_FOUND
```

### Edge Cases

```yaml
  - name: Concurrent pushes from same client
    action: sync_push (x2 simultaneous)
    condition: Same client pushes two batches simultaneously
    expected: One succeeds, other may detect version conflict
    validates: Atomic transactions prevent corruption

  - name: Push with last-write-wins conflict
    action: sync_push
    condition: Server has newer version of record
    expected: Client version wins if timestamp is newer
    validates: Timestamp comparison correct

  - name: Manual conflict flagging
    action: sync_push
    condition: config.conflict_resolution = manual, conflict detected
    expected: ConflictRecord created in sync_conflicts, included in response
    validates: Conflict stored with both versions

  - name: Idempotent re-push
    action: sync_push
    condition: Same batch pushed twice with same last_sync_version
    expected: Second push produces identical result
    validates: Idempotency maintained

  - name: Realtime channel unavailable
    action: sync_push
    condition: sync/* channel down
    expected: Sync succeeds, clients get changes on next pull
    validates: Realtime failure does not block sync
```

---

## Scaling

```yaml
scaling:
  model: horizontal
  min_instances: 1
  max_instances: unbounded

  inter_agent:
    protocol: message-bus-only
    direct_http: forbidden
    routing: by agent name
    reason: Message bus routes to healthy instances

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: not required — each sync request is independent
      leader: []
      follower: [sync_processing, conflict_resolution]
      promotion: n/a
    state_sharing:
      mechanism: shared database
      consistency_window: immediate (transactional)
      conflict_resolution: >
        Database transactions ensure atomic writes. Sync_versions
        table uses optimistic locking on last_sync_version to
        prevent concurrent checkpoint updates for the same client.

  event_handling:
    consumer_group: sync
    delivery: one-per-group
    description: >
      Each client.sync.push event delivered to one instance.
      Database transactions prevent duplicate processing.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 5
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same database. Schema migrations
      additive-only during shadow phase.
    consumer_groups:
      shadow_phase: "sync@vN+1"
      after_cutover: "sync"
```

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| sync_push_total | counter | Push operations by result (success/conflict/error) |
| sync_pull_total | counter | Pull operations by result |
| sync_records_total | counter | Records processed by operation (applied/conflicted/skipped) |
| sync_batch_size | histogram | Records per sync batch |
| sync_duration_seconds | histogram | Time to complete a sync operation |
| sync_conflicts_total | counter | Conflicts detected by resolution strategy |
| sync_connected_clients | gauge | Currently connected sync clients |

## Error Handling

| Error | Handling |
|-------|----------|
| Batch exceeds max size | Reject with 400, include max_batch_size in error |
| Storage write failure | Roll back entire batch. Return transient error. |
| Invalid change record | Reject individual record, continue batch processing |
| Version conflict | Apply configured resolution strategy |
| Client disconnected | Queue server changes for next pull |
| Real-time channel unavailable | Log warning, sync still succeeds (pull on next connect) |

## Verification Checklist

- [ ] Agent registers with orchestrator and receives WLT token
- [ ] Client can push a batch of changes
- [ ] Server detects conflicts correctly
- [ ] Conflict resolution strategy is applied per configuration
- [ ] Client receives server-side changes in response
- [ ] Version checkpoint advances after sync
- [ ] Batch size limit is enforced (rejects oversized batches)
- [ ] Duplicate pushes are idempotent
- [ ] Deletions are handled correctly (soft delete with tombstone)
- [ ] Real-time notification is sent after sync
- [ ] Manual conflicts include both versions for resolution
- [ ] Atomic transaction rolls back on partial failure
- [ ] Metrics emit for all sync operations
- [ ] Health endpoint returns agent status and connected client count

Port: 9751
