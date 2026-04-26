<!-- blueprint
type: pattern
name: versioning
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, architecture/storage]
platform: any
tier: free
-->

# Versioning Pattern

Blueprint revision tracking, migration management, compatibility
enforcement, and audit trail for all Weblisk blueprints. Defines how
blueprints evolve, how running agents transition between versions,
and how the system maintains a complete history of every change.

## Overview

Every blueprint has a `version` field in its metadata. This pattern
defines what version changes mean, how to migrate between versions,
how running agents handle version transitions, and how the system
records the full revision history of every blueprint for audit and
rollback.

Agents that extend this pattern gain automatic version tracking,
migration validation, and rollback capabilities.

---

## Design Principles

1. **Semantic versioning** — MAJOR.MINOR.PATCH with strict meaning.
2. **Forward-only migrations** — Migrations are defined from version
   N to version N+1. Rollback re-applies the previous blueprint, not
   a reverse migration.
3. **Audit everything** — Every version change is recorded with who,
   when, why, and what changed.
4. **Zero-downtime transitions** — Version updates MUST NOT require
   agent downtime. The agent transitions while serving requests.
5. **Blueprint is source of truth** — The blueprint file IS the
   specification. Version history tracks the blueprint's evolution,
   not separate migration files.

---

## Semantic Versioning Rules

```
MAJOR.MINOR.PATCH
```

| Component | When to Increment | Compatibility |
|-----------|-------------------|---------------|
| MAJOR | Breaking changes — removed actions, changed storage schemas, altered behavior contracts | NOT backward-compatible. Migration REQUIRED. |
| MINOR | Additive changes — new actions, new optional fields, new events published | Backward-compatible. Old clients still work. |
| PATCH | Non-functional — typo fixes, clarifications, improved implementation notes | Fully compatible. No migration needed. |

### Compatibility Rules

| Upgrade | Direction | Migration | Downtime |
|---------|-----------|-----------|----------|
| 1.0.0 → 1.0.1 | PATCH | None | None |
| 1.0.0 → 1.1.0 | MINOR | Optional (add new defaults) | None |
| 1.0.0 → 2.0.0 | MAJOR | Required | None (zero-downtime migration) |
| 2.0.0 → 1.0.0 | Rollback | Re-apply 1.0.0 blueprint | None |

---

## Blueprint Revision Record

Every version of a blueprint is recorded as a revision:

```json
{
  "revision_id": "rev-a1b2c3d4",
  "blueprint_name": "cron",
  "blueprint_type": "agent",
  "version": "1.1.0",
  "previous_version": "1.0.0",
  "changed_by": "operator:admin",
  "changed_at": "2026-04-25T10:30:00Z",
  "change_type": "minor",
  "change_summary": "Added pause/resume actions",
  "changelog": [
    "Added action: pause",
    "Added action: resume",
    "Added field: CronTask.paused_at"
  ],
  "migration": {
    "required": false,
    "steps": []
  },
  "rollback_safe": true,
  "blueprint_hash": "sha256:abc123..."
}
```

### Revision Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| revision_id | string | yes | Unique revision identifier |
| blueprint_name | string | yes | Blueprint name from metadata |
| blueprint_type | string | yes | Blueprint type (agent, domain, pattern, etc.) |
| version | string | yes | New version |
| previous_version | string | yes | Version this replaces (null for initial) |
| changed_by | string | yes | Identity of who made the change |
| changed_at | string | yes | ISO 8601 timestamp |
| change_type | string | yes | `major`, `minor`, `patch` |
| change_summary | string | yes | Human-readable summary |
| changelog | string[] | yes | List of specific changes |
| migration | object | yes | Migration specification (see below) |
| rollback_safe | bool | yes | Whether rollback is safe without data loss |
| blueprint_hash | string | yes | SHA-256 hash of the blueprint content |

---

## Migration Specification

When a version change requires data transformation, the migration
is specified inline in the blueprint revision:

### Migration Steps

```json
{
  "migration": {
    "required": true,
    "steps": [
      {
        "order": 1,
        "type": "add_column",
        "table": "cron_tasks",
        "column": "priority",
        "column_type": "string",
        "default": "normal",
        "description": "Add priority field to task table"
      },
      {
        "order": 2,
        "type": "rename_column",
        "table": "cron_tasks",
        "old_column": "fire_at",
        "new_column": "scheduled_at",
        "description": "Rename fire_at to scheduled_at for clarity"
      },
      {
        "order": 3,
        "type": "backfill",
        "table": "cron_tasks",
        "column": "priority",
        "value": "normal",
        "condition": "priority IS NULL",
        "description": "Backfill priority for existing tasks"
      }
    ],
    "validation": {
      "post_migration_check": "SELECT COUNT(*) FROM cron_tasks WHERE priority IS NULL = 0",
      "rollback_steps": [
        {
          "order": 1,
          "type": "rename_column",
          "table": "cron_tasks",
          "old_column": "scheduled_at",
          "new_column": "fire_at"
        },
        {
          "order": 2,
          "type": "drop_column",
          "table": "cron_tasks",
          "column": "priority"
        }
      ]
    }
  }
}
```

### Migration Step Types

| Type | Description | Fields |
|------|-------------|--------|
| `add_column` | Add new column to table | table, column, column_type, default |
| `drop_column` | Remove column from table | table, column |
| `rename_column` | Rename existing column | table, old_column, new_column |
| `add_table` | Create new table | table, schema |
| `drop_table` | Remove table | table |
| `backfill` | Populate existing rows | table, column, value, condition |
| `transform` | Transform existing data | table, column, expression |
| `custom` | Agent-specific migration logic | description, handler |

### Migration Execution

```
1. Record migration start in audit log
2. For each step in order:
   a. Execute step
   b. If step fails → execute rollback_steps → abort migration
   c. Record step completion
3. Run post_migration_check
4. If check fails → execute rollback_steps → abort migration
5. Record migration success in audit log
6. Update running agent to use new blueprint
```

---

## Version Transition Protocol

How a running agent transitions to a new blueprint version:

### Zero-Downtime Transition

```
1. New blueprint version detected (via system.blueprint.changed event
   or manual trigger)
2. Agent enters "transitioning" state (still serving requests)
3. Validate new blueprint:
   a. Parse metadata — valid YAML, required fields present
   b. Check version increment — follows semver rules
   c. Check dependency compatibility — all requires still satisfied
   d. If MAJOR: validate migration steps present
4. If migration required:
   a. Execute migration steps (see above)
   b. During migration, agent serves requests using old schema
   c. On migration complete, switch to new schema
5. Reload agent configuration from new blueprint
6. Agent exits "transitioning" state → returns to "active"
7. Emit event: system.blueprint.updated
8. Log: lifecycle.version_updated with {from, to, duration_ms}
```

### Transition States

```
active → transitioning → active (success)
active → transitioning → active (rollback on failure)
```

The agent MUST NOT enter "degraded" or "unavailable" during version
transition. All in-flight requests complete normally.

---

## Rollback

### Automatic Rollback

If a migration fails at any step, the system automatically executes
the rollback_steps in reverse order:

```
1. Migration step 3 fails
2. Execute rollback_step 2 (reverse of step 2)
3. Execute rollback_step 1 (reverse of step 1)
4. Agent reverts to previous blueprint version
5. Log: lifecycle.version_rollback with {from, to, reason}
6. Emit alert: high severity
```

### Manual Rollback

Operators can trigger rollback to any previous version:

```
POST /v1/agent/{name}/rollback
{
  "target_version": "1.0.0",
  "reason": "Performance regression detected"
}
```

Manual rollback re-applies the target version's blueprint and
executes migration rollback steps for each intermediate version
in reverse order.

---

## Revision History Storage

### Table: blueprint_revisions

| Field | Type | Description |
|-------|------|-------------|
| revision_id | string | Primary key |
| blueprint_name | string | Indexed |
| version | string | Indexed |
| previous_version | string | |
| changed_by | string | |
| changed_at | int64 | Unix timestamp |
| change_type | string | major, minor, patch |
| change_summary | string | |
| changelog | json | Array of change descriptions |
| migration | json | Migration specification |
| rollback_safe | bool | |
| blueprint_hash | string | SHA-256 |
| blueprint_content | text | Full blueprint content at this revision |

### Retention

Blueprint revisions are retained indefinitely. They are part of the
audit trail and MUST NOT be pruned.

### Querying History

```
GET /v1/blueprints/{name}/revisions
GET /v1/blueprints/{name}/revisions/{revision_id}
GET /v1/blueprints/{name}/revisions/latest
GET /v1/blueprints/{name}/diff?from=1.0.0&to=2.0.0
```

---

## Compatibility Matrix

When the orchestrator loads blueprints, it validates cross-blueprint
compatibility:

```
1. For each blueprint B:
   a. For each entry R in B.requires:
      i. Load blueprint R
      ii. Check: is R.version compatible with what B was tested against?
      iii. If R had a MAJOR version bump since B was last updated:
           → emit warning: "Blueprint B may be incompatible with R v{new}"
2. If any hard incompatibility detected:
   a. Reject the blueprint update
   b. Return error with specific incompatibility details
```

### Compatibility Declaration

Blueprints MAY declare version constraints on their dependencies:

```yaml
requires:
  - name: protocol/spec
    version: ">=1.0.0 <2.0.0"
  - name: architecture/agent
    version: ">=1.0.0"
```

When `requires` is a simple list (current format), all versions are
assumed compatible. Version constraints are opt-in for stricter
control.

---

## Changelog Format

Every blueprint SHOULD maintain a changelog at the end of its
revision history. The changelog is automatically generated from
revision records:

```markdown
## Changelog

### 2.0.0 (2026-04-25)
- **BREAKING**: Renamed fire_at → scheduled_at in CronTask
- **BREAKING**: Removed deprecated one_shot action
- Added: priority field to CronTask
- Migration: backfill priority="normal" for existing tasks

### 1.1.0 (2026-04-20)
- Added: pause action
- Added: resume action
- Added: CronTask.paused_at field

### 1.0.0 (2026-04-15)
- Initial release
```

---

## Implementation Notes

- Blueprint content MUST be hashed (SHA-256) at each revision. This
  enables tamper detection — if the stored hash doesn't match the
  current file, the blueprint was modified outside the versioning
  system.
- Migration steps execute within a transaction where the storage
  backend supports it. On backends without transactions (e.g., some
  KV stores), migrations MUST be idempotent — safe to re-run if
  interrupted.
- The diff endpoint returns a structured diff, not a text diff. It
  shows added/removed/changed sections, actions, types, and
  configuration values.
- In federated environments, blueprint versions are local to each hub.
  Hubs MAY run different versions of the same blueprint. Federation
  compatibility is managed by protocol version, not blueprint version.

## Verification Checklist

- [ ] Version field follows semantic versioning (MAJOR.MINOR.PATCH)
- [ ] MAJOR changes include migration steps
- [ ] MINOR changes are backward-compatible
- [ ] PATCH changes are non-functional
- [ ] Revision records are created for every version change
- [ ] Revision records include complete changelog
- [ ] Blueprint hash is computed and stored per revision
- [ ] Migration steps execute in order
- [ ] Failed migrations trigger automatic rollback
- [ ] Post-migration validation runs after migration
- [ ] Manual rollback to any previous version works
- [ ] Revision history is retained indefinitely
- [ ] Compatibility matrix validates cross-blueprint dependencies
- [ ] Zero-downtime transition — agent serves requests during update
- [ ] Version transition events are emitted to the bus
