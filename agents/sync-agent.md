<!-- blueprint
type: agent
kind: infrastructure
name: sync-agent
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent]
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

## Triggers

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

## Verification Checklist

- [ ] Client can push a batch of changes
- [ ] Server detects conflicts correctly
- [ ] Conflict resolution strategy is applied
- [ ] Client receives server-side changes in response
- [ ] Version checkpoint advances after sync
- [ ] Batch size limit is enforced
- [ ] Duplicate pushes are idempotent
- [ ] Deletions are handled correctly
- [ ] Real-time notification is sent after sync
- [ ] Manual conflicts include both versions
