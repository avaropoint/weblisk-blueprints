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
| `domain` | [domain.md](domain.md) | Domain YAML specs in project `domains/` | Domain controller specifications |
| `protocol` | [protocol.md](protocol.md) | `protocol/` | Wire protocol specifications |
| `pattern` | [pattern.md](pattern.md) | `patterns/` | Cross-cutting pattern contracts |
| `architecture` | [architecture.md](architecture.md) | `architecture/` | System architecture components |
| `platform` | [platform.md](platform.md) | `platforms/` | Platform implementation bindings |
| `standard` | [standard.md](standard.md) | `standards/` | Framework standards and conventions |

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
| `author` | string | no | — | Original author or authoring organization of the blueprint |
| `publisher` | string | no | — | Entity publishing the blueprint to a marketplace. Must conform to marketplace validation and verification requirements. |
| `status` | enum | no | `active` | Lifecycle status: `active`, `deprecated`, `end-of-life` |
| `superseded_by` | string | no | — | Blueprint reference (`type/name`) that replaces this one. Required when `status` is `deprecated`. |
| `end_of_life` | date | no | — | ISO 8601 date after which the blueprint is unsupported. Required when `status` is `end-of-life`. |
| `adoption` | enum | no | `required` | `required` — every deployment serves this blueprint's surface. `opt-in` — only a deployment that explicitly configures it does. |

#### `adoption`

A blueprint that declares endpoints is normally stating a surface some component
MUST serve, and an endpoint no component serves is a gap. Some surfaces are not
like that: **federation exists only for communicating with other hubs, and a
deployment that does not federate serves none of it.** That is a correct
deployment, not an unfinished one.

`adoption: opt-in` says so. It MUST be declared rather than inferred — a
tool that treats an unserved endpoint as a gap needs to know which surfaces are
deliberately unadopted, and the alternative is a hard-coded exemption list in
the tooling, which is the specification moving out of the blueprints.

`opt-in` does NOT weaken the contract. A deployment that adopts the surface owes
every assertion in it. The field says whether the surface is reached, never how
completely it must be implemented once it is.

### Type-Specific Fields

| Field | Type | Required For | Description |
|-------|------|-------------|-------------|
| `kind` | enum | `agent`, `domain` | Agent kind: `domain`, `work`, or `infrastructure` |
| `port` | integer | `agent`, `domain` | Default port assignment (see architecture/agent port convention) |
| `depends_on` | list | `agent`, `domain` | Runtime agent dependencies. `[]` if none. Distinguishes build-time (`requires`) from run-time (`depends_on`) dependencies. |
| `domain` | string | `agent` (kind: work) | The domain this work agent belongs to. Must match an existing domain name defined in the project's domain configuration. |

### Field Constraints

- `name`: Must be `[a-z][a-z0-9-]*`. Max 64 characters. Must match the filename.
- `version`: Must be valid semver (`X.Y.Z`). No pre-release tags in published blueprints.
- `requires`: Each entry must resolve to an existing blueprint in the repository.
- `extends`: Each entry must be a pattern (`patterns/*`). The pattern must exist.
- `port`: Integer in range 9700–9999. Must not conflict with other assigned ports.
- `tier`: Only `free` or `pro`. Defaults to `free` if omitted (but SHOULD be explicit).
- `author`: Free-form string. Informational only — does not confer trust or authority.
- `publisher`: Must match a verified publisher identity in the target marketplace. Publisher conformance is validated at publish time, not at authoring time.
- `status`: Defaults to `active` if omitted. Transition rules: `active` → `deprecated` → `end-of-life`. No reverse transitions.
- `superseded_by`: Must reference a valid blueprint of the same type. The referenced blueprint must exist and be `active`.
- `end_of_life`: Must be a future or current date in ISO 8601 format (`YYYY-MM-DD`).

### Lifecycle Transitions

```
active ──→ deprecated ──→ end-of-life
```

- **active**: Blueprint is current and supported. Default state.
- **deprecated**: Blueprint is superseded. `superseded_by` MUST reference the replacement. Consumers SHOULD migrate. Validators emit a warning on dependency to a deprecated blueprint.
- **end-of-life**: Blueprint is unsupported after `end_of_life` date. `end_of_life` MUST be set. Validators emit an error on dependency to an end-of-life blueprint after the specified date.

### Revocation

Blueprint trust is mutual and revocable from either direction:

- **Publisher revocation**: A publisher can revoke a published blueprint by transitioning it to `end-of-life` with an immediate date. The marketplace MUST remove revoked blueprints from discovery. Existing consumers retain their cached copy but receive a compliance warning.
- **Consumer revocation**: A consumer can stop trusting a blueprint by removing it from their `requires` and `extends` declarations. No notification to the publisher is required.
- **Marketplace revocation**: A marketplace can revoke a blueprint if compliance validation fails, the publisher violates marketplace terms, or a security vulnerability is reported. Marketplace revocation is independent of publisher intent.

### The mechanism is not the blueprint's to choose

A `## Storage` section declares **what is stored and how it is recorded** —
tables, the type each row is, the indexes the component's own queries need,
relationships and retention.

It declares no engine, driver or file format. That rule belongs to
[`architecture/storage`](../architecture/storage.md), Design Principle 6 — "the
blueprint names a contract, never a product" — and is stated there, not here.

Recorded in this schema because the schema is what broke it. This construct
carried `engine: sqlite`, `schemas/agent` listed an `engine` declaration among
an agent's required storage fields, and six agent blueprints duly chose SQLite —
each one complying with a schema that required what the architecture forbids.

A schema that contradicts the blueprint it governs is worse than a blueprint
that drifts, because every document written from it inherits the fault.

### Validation Rules

1. `type` must be in the Type Registry above
2. `name` must match the file's basename (e.g., `name: cron` → `cron.md`)
3. `requires` entries must not include the blueprint itself (no self-reference)
4. `extends` entries must not include non-pattern blueprints
5. `depends_on` entries must reference blueprints of type `agent` or `domain`
6. If `type` is `agent` or `domain`, `kind` is required
7. If `type` is `agent` or `domain`, `port` is required
8. If `type` is `agent` or `domain`, `depends_on` is required (use `[]` for none)
9. If `type` is `agent` and `kind` is `work`, `domain` is required
10. All fields are case-sensitive
11. Unknown fields are rejected (no arbitrary metadata)
12. If `status` is `deprecated`, `superseded_by` is required
13. If `status` is `end-of-life`, `end_of_life` date is required
14. `superseded_by` must reference an `active` blueprint of the same `type`

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
```yaml
types:
  Bindings:
    fields:
      path:
        type: string
        required: true
        description: "HTTP path (must start with `/v1/`)"
      methods:
        type: list
        required: true
        description: "HTTP methods: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`"
      request_type:
        type: string
        required: false
        description: "Type name for request body (required for POST/PUT/PATCH)"
      response_fields:
        type: list
        required: true
        description: "Fields consumed from the response"
```

**types:**
```yaml
types:
  Bindings:
    fields:
      name:
        type: string
        required: true
        description: "Type name as declared in the dependency's Types section"
      fields_used:
        type: list
        required: true
        description: "Specific fields consumed from the type. `[*]` for all fields."
```

**patterns:**
```yaml
types:
  Bindings:
    fields:
      behavior:
        type: string
        required: true
        description: "Named behavior from the dependency"
      parameters:
        type: list
        required: true
        description: "Parameters used from the behavior"
```

**events:**
```yaml
types:
  Bindings:
    fields:
      topic:
        type: string
        required: true
        description: "Event topic in `namespace.event.name` format"
      fields_used:
        type: list
        required: true
        description: "Fields consumed from the event payload"
```

### fields_used

`fields_used` lists the JSON keys a consumer reads from a type. It is a YAML
sequence and MAY be written inline or wrapped:

```yaml
# inline
types:
  - name: TaskRequest
    fields_used: [id, action, payload]
```

```yaml
# wrapped across lines — the same sequence
types:
  - name: MetricsInfo
    fields_used: [listing_id, uptime_30d,
                  total_invocations_30d]
```

Both are valid YAML and MUST parse identically. A reader that requires the
closing bracket on the opening line returns an EMPTY list for the second form —
which is what happened, silently, so the fields of three types in `agents/hub`
reached generation as nothing at all.

To bind a whole type, write `["*"]`. The asterisk MUST be quoted: a bare `*` is
YAML's alias indicator and makes the block unparseable, which is what
`schemas/platform` did.

Omitting `fields_used` binds no field, and is correct for a type consumed as an
opaque whole — an enum, for instance, which declares values rather than fields.

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

### What is a type, and what is not

A `types:` block declares a TYPE — something a `fields_used` binding may
reference, carried between components or persisted by one. Those are declared
in the YAML form above, one form, parsed by a parser.

A field TABLE remains correct for two things that are not types:

- **A document's own fields.** `standards/global`'s `### Top-Level` describes
  what a global blueprint may declare. It is a schema, and nothing binds
  `TopLevel.name`.
- **Configuration options.** `standards/code`'s `| Field | Values | Effect |`
  tables list the settings a standard accepts.

The distinction is not cosmetic. Rendering either as a `types:` block would
claim they are types that a binding may reference, and the field-binding check
would then have opinions about fields no component consumes.

Fifty-one type tables in `protocol/types` and fifty more across the corpus were
converted to the YAML form on 2026-09-03, verified by comparing the extracted
field set before and after each file and refusing any file where it differed.
Nine tables remain, and all nine are one of the two cases above.

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
    min: <number>          # optional
    max: <number>          # optional
    enum: [val1, val2]     # optional
    unit: <unit>           # optional
    description: What this parameter controls
```

### Field Specifications

```yaml
types:
  Structure:
    fields:
      type:
        type: string
        required: true
        description: "Scalar type from the Types scalar types table"
      default:
        type: any
        required: true
        description: "Default value. Must satisfy all constraints."
      min:
        type: number
        required: false
        description: "Minimum value (numeric) or minimum length (string)"
      max:
        type: number
        required: false
        description: "Maximum value (numeric) or maximum length (string)"
      enum:
        type: list
        required: false
        description: "Allowed values"
      unit:
        type: string
        required: false
        description: "Unit of measurement"
      description:
        type: string
        required: true
        description: "What this parameter controls"
```

### Naming Convention

Configuration parameter names SHOULD follow a consistent naming scheme
within each implementation. The specification defines semantic parameter
names (e.g., `tick_interval`, `max_retries`). Platform implementations
MAY map these to environment variables, config files, or other mechanisms
using their own conventions.

### Validation Rules

1. Every config parameter must have `type`, `default`, and `description`
2. `default` must satisfy `min`, `max`, and `enum` constraints
3. No two blueprints may share the same configuration parameter name
4. Config parameters must not expose secrets — use `patterns/secrets` for sensitive values

---

## Storage Section

Blueprints that persist data MUST declare storage in a `## Storage`
section using YAML format. Storage tables MUST reference types from the
`## Types` section — fields are not redefined.

### Structure

```yaml
storage:
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

Assertions MAY be grouped under `###` subheadings. A group whose heading BEGINS
with a component name — `Agent`, `Orchestrator`, `Domain`, `Gateway`, `Content` — addresses
that component only. Every other group, and every ungrouped assertion, addresses
any implementation of the blueprint.

```markdown
## Verification Checklist

### Agent Protocol
- [ ] Agent responds to `POST /v1/describe` with a valid `AgentManifest`

### Orchestrator Protocol
- [ ] Orchestrator `POST /v1/register` validates namespace ownership (409 on conflict)

### Cross-Cutting
- [ ] All error responses use `ErrorResponse` format with an `error` field
```

### Why grouping is structural, not cosmetic

A protocol blueprint describes both ends of a conversation, so its checklist
contains assertions no single implementation can satisfy. An orchestrator does not
serve `POST /v1/describe`; an agent does. A tool that hands an orchestrator
generator all of `protocol/spec.md`'s assertions is grading it against another
component's obligations, and will report failures that are correct behaviour.

The group heading is how the blueprint says which component an assertion is
addressed to. A tool MUST read it from the heading rather than infer scope from
the assertion's wording, and MUST report excluded assertions with their count and
the component they belong to — an assertion left out silently is indistinguishable
from an assertion that was never written.

### Conditional assertions

An assertion whose obligation depends on a choice the implementation makes MUST
be written as `IF <premise>: <obligation>`:

```markdown
- [ ] IF SQLite was chosen: WAL journal mode, `user_version` pragma for migrations
```

Written without the prefix, such an assertion fails every implementation that
made a different — and permitted — choice. The `IF` is what lets a tool tell "this
does not apply" from "this is unmet".

### Rules

1. Every item must be a checkbox (`- [ ]`)
2. Every item must be a specific, testable assertion — not vague guidance
3. Items must cover: happy path, error cases, edge cases, security, compliance
4. Items must reference specific types, endpoints, actions, or constraints by name
5. Minimum 10 items for agent and domain blueprints
6. Minimum 5 items for all other types
7. A `###` group addressed to one component MUST begin with that component's name;
   an assertion belonging to no single component MUST NOT sit in such a group
8. An assertion conditional on a choice MUST be written `IF <premise>: <obligation>`

---

## Section Form

Every section is one of three **forms**, and the form is declared by the schema
that governs the blueprint — not chosen by whoever writes the section.

| Form | Written as | Chosen when | Read by |
|---|---|---|---|
| `narrative` | prose | there is nothing to enumerate | a person |
| `table` | a markdown table with named columns | uniform rows of one shape | column name |
| `yaml:<root>` | a fenced `yaml` block with that root key | nested or heterogeneous structure | a parser |
| `yaml` | a fenced `yaml` block, root key unpinned | the structure is fixed but its root name is not | a parser |
| `structured` | a table OR a fenced `yaml` block | the SHAPE varies by component and both are machine-readable | a parser |

**The choosing rule, once:** uniform rows of the same shape are a table; nested
or heterogeneous structure is YAML; nothing to enumerate is narrative.

### Why it is declared rather than inferred

The corpus was already 85% consistent — `## Dependencies` is YAML in all 79
blueprints that have it, `## Verification Checklist` is prose in all 79,
`## Endpoints` is a table everywhere. The convention existed; it was simply
never written down, so nineteen sections drifted to prose in blueprints whose
own type documents them as structured.

Prose is the only form that cannot be checked. A table with a wrong column name
fails; a YAML block with a wrong key fails; a paragraph that omits half the
contract reads exactly like one that does not. So **structure MUST NOT be
prose**, and the schema says which sections are structure.

Declaring the form also stops a validator guessing. One that inferred the
required construct from the first fenced block in a schema's own prose
mis-associated `## Verification Checklist` with a `requires:` block and reported
fifteen faults that were not faults. A `Form` column removes the inference.

### The Form column

Each schema's **Required Section Order** table carries a `Form` column. It is
the whole declaration:

```markdown
| # | Section | Heading | Form | Required | Description |
|---|---------|---------|------|----------|-------------|
| 3 | Overview | `## Overview` | narrative | **Yes** | Scope description |
| 7 | Endpoints | `## Endpoints` | table | Conditional | HTTP surface |
| 12 | Security | `## Security` | yaml:security | **Yes** | Trust model and boundaries |
```

A section with no `Form` is `narrative`, so a schema that has not been updated
imposes nothing new.

`structured` is for a section whose content legitimately differs in shape
between components. `## Configuration` is the case: the orchestrator's is a flat
list of settings, which the choosing rule makes a table, while the gateway's is
a nested policy tree, which the same rule makes YAML. Both are correct, and
forcing either into the other's form would make a readable document worse.

It is NOT a way to avoid deciding. The guarantee `structured` still gives is the
one that matters: **the section is machine-readable and is not prose.** A form
is only `structured` when the choosing rule genuinely produces different answers
for different components — not when nobody has looked.

`yaml` without a root is for the case where the shape is fixed and the KEY is
not: an architecture blueprint's `## Configuration` is rooted at the
component's own name — `content:`, `gateway:`, `data_security:` — so pinning it
to any one literal would make every other component wrong. The requirement is
that the section is parseable, not that every component chose the same word.

### A form is per blueprint TYPE, not per section name

`## Security` is `yaml:security` for an architecture blueprint and `narrative`
for a platform one, because a platform states input validation and cryptography
choices in prose while a component states a trust model a tool compares. The
same heading legitimately takes different forms in different schemas.

Measuring form corpus-wide rather than per type reported four platform
blueprints as drifting when each was following its own schema exactly.

---

## Writing a Verification Checklist

The `## Verification Checklist` is **prose, in every blueprint**, and stays that
way. It is the one surface that has never drifted — a checkbox list in all 87
blueprints that carry one — and it is what a person reads to know what a
component owes.

Two rules, and the first is not cosmetic.

### An identifier MUST be backticked

Type names, field names, paths, constants, commands and error codes are written
in backticks:

```markdown
- [ ] `RegisterResponse` includes `agent_id`, `token` and `expires_at`
- [ ] `POST /v1/register` verifies the ML-DSA-65 signature
```

**An unbackticked identifier silently disables the check that would have
verified it.** The structural checker reads JSON keys from backticked spans
only, so

    `RegisterResponse` includes `agent_id`, `token`     → keys found, check runs
    RegisterResponse includes agent_id, token           → no keys, check SKIPPED

and the second reports nothing at all — not a failure, an absence. 35 of the 59
route-bearing assertions in this corpus are unbackticked, which is a measurable
part of why 95 of 132 assertions were graded by opinion rather than verified.

Routes survive either form; keys do not. Backtick everything and the question
does not arise.

### An assertion states one thing, testably

An assertion is a claim about the artifact that a person could check by looking.
"The component is secure" is not one. "`GET /v1/services` answers 401 without a
token" is.

Where the claim can be checked mechanically, declare the check — in the
blueprint's `declaration:` block, NOT in the sentence. See
[Section Form](#section-form); the checklist stays prose and the machine-
readable part stays in the declaration.

---

## Declared Names

A generator turns a blueprint into code, and code is made of names. Every name
it writes comes from somewhere: either a blueprint declared it, or the generator
invented it. **Only the first is repeatable.**

### A blueprint MUST name what it declares

Anything a component is required to provide — a type, an endpoint, a store
operation, an event topic, an error code, a configuration parameter — MUST be
declared with an explicit identifier. It MUST NOT be left to be inferred from a
description, a path, a heading or a sentence.

Prose is for the reader. A name is for the contract.

```markdown
| Method | Path              | Operation | Auth | Purpose                    |
|--------|-------------------|-----------|------|----------------------------|
| POST   | /v1/register      | Register  | no   | Agent registration         |
```

`Register` is the declared name. `POST /v1/register` is the wire fact and
`Agent registration` is the description; neither is an identifier, and a
generator that derives one from either will derive a different one next time.

### A declared name is binding

Where a blueprint declares a name, every artifact generated from it MUST use
that name. A generator MUST NOT substitute a synonym, expand an abbreviation,
add a qualifier or drop one.

This is not a style rule — it is what makes a rebuild incremental. The symbols
one file declares are what every other file depends on, so a name changed
between two generations of the same blueprint makes every dependent file stale
and rebuilds work that was correct. One measured orchestrator build regenerated
ten compliant files for exactly this reason.

### The declaring blueprint owns the name

A name is declared once, in the blueprint that specifies the thing:

| What | Declared in | Read as |
|---|---|---|
| A type | the `## Types` section of its blueprint | the type's `name` |
| An endpoint | the `## Endpoints` table of the component that serves it | the `Operation` column |
| A store operation | the store contract's operations list | the operation as written |
| An event topic | the topic table of the blueprint that publishes it | the topic string |
| An error code | the central code registry | the code as written |
| A configuration parameter | the `## Configuration` section | the parameter's key |

A blueprint that consumes one of these refers to it; it does not restate it. Two
statements of a name are two names as soon as one of them is edited.

### A platform blueprint spells a name; it does not choose one

`platforms/` blueprints MUST state how a declared name is rendered in their
language, and MUST NOT introduce a different name.

`Register` becomes `PathRegister` and `handleRegister` in Go, `PATH_REGISTER` in
JavaScript and Rust. The operation is `Register` in all of them, so a change to
the blueprint reaches every platform, and a reader of any generated artifact can
find the line of the blueprint it came from.

A platform blueprint MUST state this mapping explicitly — casing, prefix and
suffix per kind of symbol — because "follow the language's conventions" is not a
rule two generations will apply identically.

### What this rules out

A generator MUST NOT hold a naming convention of its own. If a name cannot be
found in a blueprint, that is a gap **in the blueprint**, and it MUST be
reported as one rather than filled in.

A pipeline that names things when the specification does not has quietly become
the specification, and nothing it produces can be traced back to a document
anybody agreed to.

---

## Platform Neutrality

A blueprint is either a **specification** or a **translation**, and the two must
not mix.

### Specification blueprints — `protocol/`, `architecture/`, `patterns/`, `agents/`

These state requirements in terms of algorithms, formats, wire shapes and
behaviour. They MUST NOT name:

- a language, or a construct belonging to one
- a module, package, crate or library
- an API identifier or function signature
- a runtime facility not every platform has

A hub generated for one platform and a hub generated for another must be able to
verify each other's signatures, read each other's files and answer each other's
requests. That is only true if what they conform to is the algorithm and the
format, rather than one platform's way of reaching them.

Pseudocode is permitted in process descriptions provided its notation is declared
and is not an API. `verify(publicKey, data, signature)` names a primitive;
`ML_DSA_65.Verify(...)` names an identifier that exists in no Rust or JavaScript
implementation.

**Exception: a blueprint whose subject IS a platform facility.** `patterns/command`
specifies running operating-system processes, so it names exit codes, stdin and
SIGTERM because those are its subject rather than an assumption about how
something else is implemented. Such a blueprint MUST state, in its overview, that
the capability is unavailable where the facility is absent — a Worker cannot spawn
a process, and a blueprint about spawning processes has to say so rather than let
a generator discover it.

This exception is narrow. It covers a blueprint whose whole purpose is a facility;
it does not cover a blueprint that merely assumes one while specifying something
else. "An agent shuts down gracefully on SIGTERM" was the second kind: the
requirement is orderly shutdown, and the signal was one runtime's way of asking
for it.

### Platform blueprints — `platforms/`

These translate, and translation is their entire purpose. They MAY name modules,
packages, APIs and runtime facilities freely — that is the content nobody else
can carry.

They MUST NOT restate a requirement from a specification blueprint. Naming the
module that provides a primitive is translation; repeating the primitive's
standard, parameters or rationale creates a second normative statement, free to
drift from the first.

Every platform blueprint MUST carry a `## Primitive Mapping` section covering
every primitive the specification blueprints require, with one row per primitive.
A primitive the platform cannot provide MUST be marked **UNFILLED** rather than
omitted or approximated. An unfilled slot is a stated gap; an omitted one is
indistinguishable from a satisfied one.

### Why this is a rule and not a preference

Both directions have been violated, and each violation broke a build.

`platforms/go.md` said "standard library only, except one module" while
`protocol/identity` required a key-derivation function Go does not ship. Both
statements were reasonable; together they were unsatisfiable, and an
implementation that resolved the conflict correctly was reported as violating its
own platform's dependency policy.

`architecture/storage.md` carried a table of backends per platform, in the same
document as a design principle stating that a blueprint names a contract and never
a product. It contradicted itself, and the platform blueprints inherited the
contradiction: two of them mandated SQLite for storage the standard library
already handles.

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
| `domain` | project `domains/` | `<name>/blueprint.yaml` | `domains/greeting/blueprint.yaml` |
| `protocol` | `protocol/` | `<name>.md` | `protocol/spec.md` |
| `pattern` | `patterns/` | `<name>.md` | `patterns/messaging.md` |
| `architecture` | `architecture/` | `<name>.md` | `architecture/agent.md` |
| `platform` | `platforms/` | `<name>.md` | `platforms/go.md` |

Files must be lowercase, hyphen-separated, with `.md` extension.
The filename (without extension) MUST match the `name` field in frontmatter.
