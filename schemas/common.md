# Common Schema

Rules, structures, and formats inherited by every blueprint type. All
type-specific schemas (`agent.md`, `protocol.md`, etc.) extend this
common schema. A blueprint that violates any rule here is non-compliant
regardless of its type.

---

## Type Registry

Every blueprint declares exactly one type. The type determines which
type-specific schema governs the blueprint.

| Type | Schema | Directory | Description |
|------|--------|-----------|-------------|
| `agent` | [agent.md](agent.md) | `agents/` | Infrastructure service definitions |
| `domain` | [domain.md](domain.md) | `examples/domains/` | Domain controller specifications |
| `protocol` | [protocol.md](protocol.md) | `protocol/` | Wire protocol specifications |
| `pattern` | [pattern.md](pattern.md) | `patterns/` | Cross-cutting pattern contracts |
| `architecture` | [architecture.md](architecture.md) | `architecture/` | System architecture components |
| `platform` | [platform.md](platform.md) | `platforms/` | Platform implementation bindings |

---

## Frontmatter

Every blueprint MUST begin with an HTML comment block containing YAML
metadata. This is the machine-readable header that tools, validators,
and the orchestrator parse before reading the document body.

### Format

```markdown
<!-- blueprint
field: value
field: value
-->
```

The comment MUST be the first content in the file (no blank lines before it).
The opening `<!-- blueprint` MUST be on line 1. Fields are YAML key-value
pairs, one per line. The closing `-->` MUST be on its own line.

### Common Fields

These fields are defined for all blueprint types. Type-specific schemas
may add additional required fields.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | enum | **yes** | — | One of: `agent`, `domain`, `protocol`, `pattern`, `architecture`, `platform` |
| `name` | string | **yes** | — | Unique identifier. Lowercase, hyphen-separated. Must match filename (without `.md`). |
| `version` | semver | **yes** | — | Blueprint version in `MAJOR.MINOR.PATCH` format |
| `requires` | list | **yes** | `[]` | Blueprints this one depends on. Format: `[type/name, type/name]` |
| `extends` | list | conditional | `[]` | Patterns this blueprint inherits. Format: `[patterns/name]`. Required for `agent` and `domain` types. |
| `platform` | enum | **yes** | `any` | Target platform: `any`, `go`, `cloudflare`, `node`, `rust` |
| `tier` | enum | **yes** | `free` | Availability tier: `free` or `pro` |

### Type-Specific Fields

| Field | Type | Required For | Description |
|-------|------|-------------|-------------|
| `kind` | enum | `agent`, `domain` | Agent kind: `domain`, `work`, or `infrastructure` |
| `port` | integer | `agent`, `domain` | Default port assignment (see architecture/agent port convention) |
| `depends_on` | list | `agent`, `domain` | Runtime agent dependencies. `[]` if none. Distinguishes build-time (`requires`) from run-time (`depends_on`) dependencies. |

### Field Constraints

- `name`: Must be `[a-z][a-z0-9-]*`. Max 64 characters. Must match the filename.
- `version`: Must be valid semver (`X.Y.Z`). No pre-release tags in published blueprints.
- `requires`: Each entry must resolve to an existing blueprint in the repository.
- `extends`: Each entry must be a pattern (`patterns/*`). The pattern must exist.
- `port`: Integer in range 9700–9999. Must not conflict with other assigned ports.
- `tier`: Only `free` or `pro`. Defaults to `free` if omitted (but SHOULD be explicit).

### Validation Rules

1. `type` must be in the Type Registry above
2. `name` must match the file's basename (e.g., `name: cron` → `cron.md`)
3. `requires` entries must not include the blueprint itself (no self-reference)
4. `extends` entries must not include non-pattern blueprints
5. `depends_on` entries must reference blueprints of type `agent` or `domain`
6. If `type` is `agent` or `domain`, `kind` is required
7. If `type` is `agent` or `domain`, `port` is required
8. If `type` is `agent` or `domain`, `depends_on` is required (use `[]` for none)
9. All fields are case-sensitive
10. Unknown fields are rejected (no arbitrary metadata)

---

## Title and Overview

Immediately after the frontmatter closing `-->`, every blueprint MUST have:

1. A level-1 heading (`# Title`) — human-readable name of the blueprint
2. A 1–3 sentence summary paragraph directly below the heading
3. A `## Overview` section with 2–5 sentences expanding on scope and purpose

```markdown
# Cron Agent

Scheduled task execution with cron-style expressions. Supports
one-time and recurring tasks with retry logic, execution history,
and event-driven dispatch.

## Overview

The cron agent manages scheduled work within a Weblisk server. ...
```

### Validation Rules

1. Title must be a single `#` heading (not `##` or deeper)
2. Title must appear on the line immediately after `-->` (one blank line allowed)
3. Summary paragraph must be non-empty
4. `## Overview` must be the first `##` section in the document

---

## Dependencies Section

Every blueprint that declares `requires` or `extends` in frontmatter MUST
include a `## Dependencies` section containing a YAML code block. This
section is the contract surface — it declares exactly what the blueprint
uses from each dependency.

### Structure

```yaml
requires:
  - blueprint: <type/name>
    version: "<semver-range>"
    bindings:
      endpoints:        # Optional — HTTP endpoints consumed
        - path: /v1/...
          methods: [GET, POST, ...]
          request_type: TypeName
          response_fields: [field1, field2]
      types:            # Optional — types referenced
        - name: TypeName
          fields_used: [field1, field2, ...]
      patterns:         # Optional — behavioral patterns adopted
        - behavior: pattern-name
          parameters: [param1, param2, ...]
      events:           # Optional — events consumed or produced
        - topic: namespace.event.name
          fields_used: [field1, field2, ...]
    on_change:
      compatible: <action>
      breaking: <action>
      removed: <action>

extends:
  - pattern: <patterns/name>
    version: "<semver-range>"
    bindings:
      # Same structure as requires bindings
    on_change:
      compatible: <action>
      breaking: <action>
      removed: <action>

depends_on:
  # Runtime agent dependencies (agent and domain types only)
  # [] if no runtime dependencies
```

### Bindings

Bindings declare the specific contract surface consumed from each dependency.
They serve three purposes:

1. **Impact analysis** — When a dependency changes, the bindings show exactly
   which parts of this blueprint are affected.
2. **Validation** — The referenced endpoints, types, patterns, and events
   must actually exist in the dependency.
3. **Security scoping** — The agent is only granted access to the bindings
   it declares. Undeclared bindings are not available at runtime.

#### Binding Types

| Binding | Fields | Description |
|---------|--------|-------------|
| `endpoints` | `path`, `methods`, `request_type`, `response_fields` | HTTP endpoints consumed from the dependency |
| `types` | `name`, `fields_used` | Type definitions referenced from the dependency |
| `patterns` | `behavior`, `parameters` | Behavioral patterns adopted from the dependency |
| `events` | `topic`, `fields_used` | Events published to or subscribed from via the dependency |

#### Field Specifications

**endpoints:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | yes | HTTP path (must start with `/v1/`) |
| `methods` | list | yes | HTTP methods: `GET`, `POST`, `PUT`, `DELETE`, `PATCH` |
| `request_type` | string | conditional | Type name for request body (required for POST/PUT/PATCH) |
| `response_fields` | list | yes | Fields consumed from the response |

**types:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Type name as declared in the dependency's Types section |
| `fields_used` | list | yes | Specific fields consumed from the type. `[*]` for all fields. |

**patterns:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `behavior` | string | yes | Named behavior from the dependency |
| `parameters` | list | yes | Parameters used from the behavior |

**events:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | yes | Event topic in `namespace.event.name` format |
| `fields_used` | list | yes | Fields consumed from the event payload |

### Version Ranges

Version ranges use semver range syntax:

| Format | Meaning |
|--------|---------|
| `">=1.0.0 <2.0.0"` | Any 1.x release |
| `">=1.2.0 <1.3.0"` | Any 1.2.x release |
| `"1.0.0"` | Exactly version 1.0.0 |

Version ranges MUST be quoted strings in YAML.

### on_change Actions

Every dependency MUST declare how this blueprint responds when the
dependency changes.

| Action | When Used | Behavior |
|--------|-----------|----------|
| `validate-and-adopt` | Compatible changes | Validate new version against bindings, adopt if valid |
| `validate` | Compatible changes | Validate new version, continue with current if validation passes |
| `version-bump` | Breaking changes | Halt operation, require blueprint update to new version |
| `halt-immediately` | Removed dependencies | Stop all operations that depend on the removed blueprint |
| `halt-and-reconcile` | Breaking changes to critical deps | Halt, trigger reconciliation per change-management |
| `fallback` | Compatible or breaking | Switch to a declared fallback behavior |

### Validation Rules

1. Every `requires` entry in frontmatter must have a matching `requires` block in Dependencies
2. Every `extends` entry in frontmatter must have a matching `extends` block in Dependencies
3. `depends_on` must be declared (even if `[]`)
4. `version` must be a valid semver range string
5. At least one binding category (`endpoints`, `types`, `patterns`, or `events`) must be present per dependency
6. All `on_change` actions must be from the allowed actions table
7. All three `on_change` levels (`compatible`, `breaking`, `removed`) must be declared
8. Referenced types, endpoints, and events must exist in the dependency blueprint

---

## Types Section

Blueprints that define data structures MUST declare them in a `## Types`
section using YAML format. Types are the single source of truth — storage
tables, action inputs, event payloads, and API responses all reference
these definitions.

### Structure

```yaml
types:
  TypeName:
    description: What this type represents
    fields:
      field_name:
        type: <scalar-type>
        description: What this field contains
        # Additional constraints (all optional):
        required: true|false
        optional: true|false
        format: <format-hint>
        default: <value>
        min: <number>
        max: <number>
        enum: [value1, value2, ...]
        unit: <unit-name>
        auto: true
        references: TypeName.field_name
        required_when: <condition>
        exclusive_with: <field_name>
    constraints:
      - name: constraint_name
        type: unique|check|foreign_key
        fields: [field1, field2]
        expression: <SQL-style expression>  # for check constraints
        description: Why this constraint exists
```

### Scalar Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | UTF-8 text | `"hello"` |
| `text` | Long-form text (no max by default) | Multi-paragraph content |
| `int` | 32-bit signed integer | `42` |
| `int64` | 64-bit signed integer (timestamps, IDs) | `1712160001` |
| `float` | 64-bit floating point | `3.14` |
| `bool` | Boolean | `true` / `false` |
| `object` | Nested JSON object | `{"key": "value"}` |
| `list` | Ordered array | `[1, 2, 3]` |
| `uuid` | UUID string | `"550e8400-e29b-41d4-a716-446655440000"` |

### Format Hints

| Format | Applies To | Description |
|--------|-----------|-------------|
| `uuid-v7` | string | UUID version 7 (time-ordered) |
| `iso8601` | string | ISO 8601 datetime string |
| `email` | string | Email address |
| `url` | string | HTTP(S) URL |
| `hex` | string | Hex-encoded bytes |
| `cron` | string | Cron expression (5-field) |
| `semver` | string | Semantic version string |

### Field Constraint Properties

| Property | Type | Description |
|----------|------|-------------|
| `required` | bool | Field must be present. Default: `true` for non-optional fields |
| `optional` | bool | Field may be omitted. Mutually exclusive with `required: true` |
| `format` | string | Format hint from the table above |
| `default` | any | Default value when field is omitted |
| `min` | number | Minimum value (numeric types) or minimum length (strings) |
| `max` | number | Maximum value (numeric types) or maximum length (strings) |
| `enum` | list | Allowed values. Field must be one of these. |
| `unit` | string | Unit of measurement (e.g., `seconds`, `bytes`, `milliseconds`) |
| `auto` | bool | Field is system-generated (e.g., timestamps). Not user-supplied. |
| `references` | string | Foreign key reference in `TypeName.field_name` format |
| `required_when` | string | Conditional requirement expression (e.g., `schedule = "once"`) |
| `exclusive_with` | string | Mutual exclusion — exactly one of this field or the named field must be set |

### Constraint Types

| Type | Description |
|------|-------------|
| `unique` | Combination of `fields` must be unique across all rows |
| `check` | SQL-style boolean `expression` that must evaluate to true |
| `foreign_key` | Referential integrity — `fields` reference another type |

### Validation Rules

1. Every type name must be PascalCase
2. Every field must have a `type` from the scalar types table
3. Every field must have a `description`
4. `references` must point to a valid `TypeName.field_name` in the same blueprint or a required dependency
5. `enum` values must match the declared `type`
6. `min` and `max` must be appropriate for the field type
7. `required_when` expressions must reference fields in the same type
8. `exclusive_with` must reference a field in the same type
9. Constraint names must be lowercase with underscores
10. `check` constraints must use SQL-style expressions

---

## Configuration Section

Blueprints that accept runtime configuration MUST declare all parameters
in a `## Configuration` section using YAML format.

### Structure

```yaml
config:
  parameter_name:
    type: <scalar-type>
    default: <value>
    env: WL_<AGENT>_<PARAM>
    min: <number>          # optional
    max: <number>          # optional
    enum: [val1, val2]     # optional
    unit: <unit>           # optional
    description: What this parameter controls
```

### Field Specifications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | Scalar type from the Types scalar types table |
| `default` | any | yes | Default value. Must satisfy all constraints. |
| `env` | string | yes | Environment variable name. Must follow `WL_<AGENT>_<PARAM>` convention. |
| `min` | number | no | Minimum value (numeric) or minimum length (string) |
| `max` | number | no | Maximum value (numeric) or maximum length (string) |
| `enum` | list | no | Allowed values |
| `unit` | string | no | Unit of measurement |
| `description` | string | yes | What this parameter controls |

### Naming Convention

Environment variable names MUST follow: `WL_<AGENT_NAME>_<PARAMETER>`
- `WL_` prefix is mandatory
- `<AGENT_NAME>` is the blueprint name in UPPER_SNAKE_CASE
- `<PARAMETER>` is the parameter name in UPPER_SNAKE_CASE
- Example: `WL_CRON_TICK_INTERVAL`

### Validation Rules

1. Every config parameter must have `type`, `default`, `env`, and `description`
2. `default` must satisfy `min`, `max`, and `enum` constraints
3. `env` must follow the naming convention
4. No two blueprints may share the same `env` variable name
5. Config parameters must not expose secrets — use `patterns/secrets` for sensitive values

---

## Storage Section

Blueprints that persist data MUST declare storage in a `## Storage`
section using YAML format. Storage tables MUST reference types from the
`## Types` section — fields are not redefined.

### Structure

```yaml
storage:
  engine: sqlite

  tables:
    table_name:
      source_type: TypeName
      primary_key: field_name
      indexes:
        - name: idx_name
          fields: [field1, field2]
          type: btree|unique|hash
          description: Why this index exists

  relationships:
    - name: relationship_name
      from: table.field
      to: table.field
      cardinality: one-to-one|one-to-many|many-to-one|many-to-many
      on_delete: cascade|restrict|set_null|no_action
      on_update: cascade|restrict|set_null|no_action
      description: Why this relationship exists

  retention:
    table_name:
      policy: indefinite|<config-reference>|<duration>
      cleanup: manual|automatic <schedule>

  backup:
    table_name:
      frequency: daily|hourly|<cron>
      format: JSON|SQLite dump
      path: .weblisk/backups/<agent>/<table>_{ISO8601}.<ext>
```

### Validation Rules

1. `source_type` must reference a type defined in the blueprint's Types section
2. `primary_key` must be a field in the source type
3. Index `fields` must be fields in the source type
4. Relationship `from`/`to` must reference valid `table.field` combinations
5. Retention policy must be defined for every table
6. Backup must be defined for every table (use `backup: false` with `reason` to opt out)

---

## Verification Checklist Section

Every blueprint MUST include a `## Verification Checklist` section with
concrete, testable assertions. These are the acceptance criteria for any
implementation of the blueprint.

### Format

```markdown
## Verification Checklist

- [ ] Assertion that can be tested programmatically or manually
- [ ] Another assertion
```

### Rules

1. Every item must be a checkbox (`- [ ]`)
2. Every item must be a specific, testable assertion — not vague guidance
3. Items must cover: happy path, error cases, edge cases, security, compliance
4. Items must reference specific types, endpoints, actions, or constraints by name
5. Minimum 10 items for agent and domain blueprints
6. Minimum 5 items for all other types

---

## Implementation Notes Section

Every blueprint MUST include a `## Implementation Notes` section with
practical guidance for implementors.

### Required Content

1. Key design decisions and their rationale
2. Common pitfalls and how to avoid them
3. Performance considerations
4. Security requirements specific to this blueprint
5. Testing approach

---

## Section Ordering

Sections MUST appear in the order defined by the type-specific schema.
Common sections that appear in all types follow this base order:

1. Frontmatter (`<!-- blueprint ... -->`)
2. Title (`# Name`)
3. Summary paragraph
4. `## Overview`
5. `## Dependencies`
6. _(Type-specific sections — see type schema)_
7. `## Implementation Notes`
8. `## Verification Checklist`

Type-specific schemas define the full section order including where
type-specific sections are inserted.

---

## Cross-Referencing

### Internal References
References to other blueprints within the repository use relative paths:
```markdown
See [Protocol Specification](../protocol/spec.md) for endpoint details.
```

### Schema References
References to schema definitions use the `schemas/` path:
```markdown
Follows the agent schema defined in [schemas/agent.md](../schemas/agent.md).
```

### Type References
References to types use `TypeName` format in prose and YAML:
```markdown
The `CronTask` type defines the task structure.
```
```yaml
references: CronTask.task_id
```

---

## Versioning

### Blueprint Versions
- Follow semver: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes (removed fields, changed types, removed endpoints)
- **MINOR**: Additive changes (new optional fields, new actions, new events)
- **PATCH**: Non-functional changes (clarifications, typos, examples)
- All blueprints in a release MUST be compatible with each other

### Schema Versions
- Schema files themselves are versioned in their frontmatter
- Schema version changes follow the same semver rules
- A schema MAJOR version bump means all blueprints of that type must be updated

### Version Compatibility
- `requires` version ranges determine compatibility windows
- `on_change` rules determine what happens when dependencies move outside the window
- The orchestrator tracks version compatibility at runtime

---

## Reserved Words

The following words are reserved and MUST NOT be used as blueprint names,
type names, field names, or action names:

```
system, orchestrator, framework, schema, blueprint, weblisk, admin,
root, internal, private, public, global, all, any, none, null, undefined,
true, false
```

---

## File Naming

| Type | Directory | Naming Pattern | Example |
|------|-----------|----------------|---------|
| `agent` | `agents/` | `<name>.md` | `agents/cron.md` |
| `domain` | `examples/domains/` | `<name>.md` | `examples/domains/seo.md` |
| `protocol` | `protocol/` | `<name>.md` | `protocol/spec.md` |
| `pattern` | `patterns/` | `<name>.md` | `patterns/messaging.md` |
| `architecture` | `architecture/` | `<name>.md` | `architecture/agent.md` |
| `platform` | `platforms/` | `<name>.md` | `platforms/go.md` |

Files must be lowercase, hyphen-separated, with `.md` extension.
The filename (without extension) MUST match the `name` field in frontmatter.
