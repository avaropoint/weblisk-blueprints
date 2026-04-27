<!-- blueprint
type: pattern
name: storage
version: 1.0.0
requires: [protocol/spec, protocol/types]
platform: any
tier: free
-->

# Storage Pattern

Canonical schema format for agent and domain data persistence. Defines
the standard way to declare tables, types, constraints, relationships,
indexes, migrations, and cascade rules. Agents `extends: patterns/storage`
and declare only their tables — the pattern provides the structural
contract and storage lifecycle.

> **Scope boundary:** This pattern defines **agent-level schema
> declaration** (type format, constraints, relationships, migrations).
> For the **orchestrator and system-level store interfaces** (agent
> registry, strategies, observations, etc.), see
> [`architecture/storage`](../architecture/storage.md).

## Overview

Every agent that persists data needs a schema. Without a standard
format, each agent invents its own — some use JSON examples, others
use markdown tables, and only one (cron.md) uses the full YAML type
system with relationships and constraints. This pattern standardizes
the format so that:

1. **Schema generation** — tools can auto-generate DDL from YAML
2. **Validation** — type constraints are machine-checkable
3. **Relationships** — FK/cascade rules are explicit, not implicit
4. **Migrations** — version-to-version schema evolution is structured
5. **Agents stay small** — agents declare types; this pattern defines
   how types work

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
          fields_used: [name, fields, description, constraints]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Schema as declaration** — All persistent types are declared in YAML with explicit field types, constraints, and relationships; tools auto-generate DDL from declarations.
2. **Agents own their storage** — Each agent manages its own tables; cross-agent data access goes through agent messages, not direct database queries.
3. **Migrations are versioned and reversible** — Every schema change has both `up` and `down` steps, applied in version order and tracked in a migrations table.
4. **Retention is explicit** — Time-series data declares retention rules upfront; automatic purging prevents unbounded storage growth.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: type-declaration
      description: Declare persistent types with field-level constraints and validation
      parameters:
        - name: type_name
          type: string
          required: true
          description: PascalCase type name for the persistent entity
        - name: fields
          type: map
          required: true
          description: Field definitions with type, required flag, and constraints
      inherits: Standard type format with supported field types and constraint system
      overridable: true
      override_constraints: Must use supported field types; PascalCase naming required
    - name: schema-migration
      description: Version-to-version schema evolution with up and down steps
      parameters:
        - name: version
          type: string
          required: true
          description: Target version for this migration
        - name: up
          type: array
          required: true
          description: Forward migration steps
        - name: down
          type: array
          required: true
          description: Rollback migration steps
      inherits: Structured migration with add/drop/alter/rename actions
      overridable: true
      override_constraints: Must include both up and down sections
  types:
    - name: TypeDefinition
      description: Persistent type declaration with fields, constraints, and descriptions
      inherited_by: Type Declaration section
    - name: ConstraintDefinition
      description: Named constraint (unique, check, primary_key, foreign_key)
      inherited_by: Constraints section
    - name: RelationshipDefinition
      description: Foreign key relationship with cascade rules
      inherited_by: Relationships section
    - name: IndexDefinition
      description: Query optimization index declaration
      inherited_by: Indexes section
    - name: MigrationStep
      description: Individual schema migration action (add_field, drop_field, etc.)
      inherited_by: Migrations section
```

---

## Type Declaration

All persistent types are declared as YAML with field-level constraints:

```yaml
types:
  <TypeName>:
    description: <one-line>
    fields:
      <field_name>:
        type: <type>
        required: <bool>
        description: <one-line>
        default: <value>           # optional
        constraints: [<names>]     # optional — reference named constraints
```

### Supported Field Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | UTF-8 text | `"hello"` |
| `text` | Long-form text (no length limit) | Email body, HTML |
| `int` | 64-bit signed integer | `42` |
| `float` | 64-bit floating point | `3.14` |
| `boolean` | True/false | `true` |
| `timestamp` | Unix epoch seconds (int64) | `1713264000` |
| `json` | Arbitrary JSON object | `{"key": "value"}` |
| `[]<type>` | Array of type | `[]string` |
| `enum(<values>)` | Enumerated string values | `enum(active,suspended,deleted)` |
| `uuid` | UUID v4 string | `"a1b2c3d4-..."` |

### Example

```yaml
types:
  EmailQueueEntry:
    description: Queued email awaiting delivery
    fields:
      id:
        type: uuid
        required: true
        description: Unique queue entry ID
      to_address:
        type: string
        required: true
        description: Recipient email address
      subject:
        type: string
        required: true
        description: Email subject line
      template_id:
        type: string
        required: false
        description: Template to render (null for raw emails)
      status:
        type: enum(pending,sending,sent,failed)
        required: true
        default: pending
        description: Delivery status
      attempts:
        type: int
        required: true
        default: 0
        description: Number of delivery attempts
      created_at:
        type: timestamp
        required: true
        description: When the email was queued
      next_retry_at:
        type: timestamp
        required: false
        description: Next retry time (null if not retrying)
```

---

## Constraints

Named constraints enforce data integrity rules. They are declared
once and referenced by field or table.

```yaml
constraints:
  <constraint_name>:
    type: <constraint_type>
    fields: [<field_names>]
    condition: <expression>        # for check constraints
    description: <one-line>
```

### Constraint Types

| Type | Description |
|------|-------------|
| `unique` | Unique index across specified fields |
| `check` | Boolean expression that must be true |
| `not_null` | Field(s) cannot be null (implied by `required: true`) |
| `primary_key` | Primary key (composite if multiple fields) |
| `foreign_key` | Reference to another type's field |

### Example

```yaml
constraints:
  pk_email_queue:
    type: primary_key
    fields: [id]

  uq_idempotency:
    type: unique
    fields: [idempotency_key]
    description: Prevent duplicate sends for same request

  ck_valid_status:
    type: check
    fields: [status]
    condition: "status IN ('pending', 'sending', 'sent', 'failed')"

  ck_retry_needs_time:
    type: check
    fields: [status, next_retry_at]
    condition: "status != 'pending' OR next_retry_at IS NOT NULL OR attempts = 0"
    description: Retrying entries must have a next_retry_at
```

---

## Relationships

Foreign key relationships connect types across the agent's schema
or to types in dependency schemas.

```yaml
relationships:
  <relationship_name>:
    from:
      type: <TypeName>
      field: <field_name>
    to:
      type: <TypeName>
      field: <field_name>
    on_delete: <cascade | set_null | restrict | no_action>
    on_update: <cascade | restrict | no_action>
    description: <one-line>
```

### Cascade Rules

| Rule | Behavior |
|------|----------|
| `cascade` | Delete/update child rows when parent changes |
| `set_null` | Set FK field to null when parent is deleted |
| `restrict` | Prevent parent delete if children exist |
| `no_action` | No automatic action (application handles) |

### Cross-Agent References

When a type references a type owned by another agent, use the
`source_type` annotation:

```yaml
fields:
  task_id:
    type: string
    required: true
    description: Reference to the scheduling task
    source_type: cron.CronTask     # <agent>.<TypeName>
```

This is a logical reference — it documents the contract but does
not create a physical FK across agent boundaries (agents own their
own storage).

---

## Indexes

Indexes optimize query patterns. Declare them explicitly:

```yaml
indexes:
  <index_name>:
    type: <btree | hash | gin>     # default: btree
    fields: [<field_names>]
    unique: <bool>                  # default: false
    condition: <partial_condition>  # optional — partial index
    description: <one-line>
```

### Example

```yaml
indexes:
  idx_queue_pending:
    type: btree
    fields: [status, next_retry_at]
    condition: "status = 'pending'"
    description: Fast lookup for pending emails due for retry

  idx_queue_created:
    type: btree
    fields: [created_at]
    description: Time-ordered queue scan
```

---

## Storage Configuration

Agents declare their storage requirements:

```yaml
storage:
  engine: sqlite | postgres | memory
  tables:
    - type: <TypeName>
      retention: <duration>          # optional — auto-purge after duration
      partition_by: <field>          # optional — time-based partitioning
```

### Retention

Retention rules enable automatic purging of old records:

```yaml
storage:
  tables:
    - type: WebhookDelivery
      retention: 7d                  # purge deliveries older than 7 days
    - type: HealthSnapshot
      retention: 168h                # 7 days in hours
    - type: AuditLog
      retention: 90d                 # 90-day audit trail
```

The purge process runs on a configurable schedule (default: daily).
Records are deleted by timestamp field (convention: `created_at`
or agent-specified field).

---

## Migrations

Schema changes between versions follow a structured migration format:

```yaml
migrations:
  - version: "1.1.0"
    description: Add retry tracking fields
    up:
      - action: add_field
        type: EmailQueueEntry
        field:
          name: retry_count
          type: int
          required: true
          default: 0
      - action: add_index
        index:
          name: idx_retry_pending
          fields: [status, retry_count]
          condition: "status = 'failed'"
    down:
      - action: drop_index
        name: idx_retry_pending
      - action: drop_field
        type: EmailQueueEntry
        field: retry_count

  - version: "1.2.0"
    description: Rename status values
    up:
      - action: alter_field
        type: EmailQueueEntry
        field: status
        from_type: "enum(queued,sent,failed)"
        to_type: "enum(pending,sending,sent,failed)"
    down:
      - action: alter_field
        type: EmailQueueEntry
        field: status
        from_type: "enum(pending,sending,sent,failed)"
        to_type: "enum(queued,sent,failed)"
```

### Migration Actions

| Action | Description |
|--------|-------------|
| `add_field` | Add a new field to a type |
| `drop_field` | Remove a field from a type |
| `alter_field` | Change field type, default, or constraints |
| `rename_field` | Rename a field (preserving data) |
| `add_index` | Create a new index |
| `drop_index` | Remove an index |
| `add_constraint` | Add a named constraint |
| `drop_constraint` | Remove a named constraint |
| `add_type` | Create a new type/table |
| `drop_type` | Remove a type/table (requires empty or cascade) |

Every migration MUST have a `down` section for rollback. Migrations
are applied in version order and tracked in a `schema_migrations`
table.

---

## Implementation Notes

- **Agents own their storage**: Each agent manages its own tables.
  Cross-agent data access goes through agent messages, not direct
  DB queries.
- **Type names are PascalCase**: `EmailQueueEntry`, not
  `email_queue_entry`. Table names in DDL use snake_case
  automatically.
- **Timestamps are Unix epoch**: All timestamp fields store seconds
  since epoch as int64. Display formatting is a presentation concern.
- **UUIDs for IDs**: Use UUID v4 for all primary keys unless there
  is a specific reason for sequential IDs.
- **Soft deletes**: Prefer `status: deleted` over physical deletes
  for auditable records. Physical deletes are acceptable for
  retention-purged data.
- **Schema validation**: Implementations SHOULD validate the YAML
  schema at agent startup and reject agents with invalid schemas.

## Verification Checklist

- [ ] All persistent types declared in YAML with field types and descriptions
- [ ] Primary keys declared for every type
- [ ] Named constraints enforce business rules
- [ ] Relationships declared with explicit cascade rules
- [ ] Indexes declared for known query patterns
- [ ] Cross-agent references use source_type annotation
- [ ] Migrations have both up and down sections
- [ ] Migrations are versioned and applied in order
- [ ] Retention rules configured for time-series data
- [ ] Storage engine declared in agent config
