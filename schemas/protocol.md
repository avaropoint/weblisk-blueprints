---
family: schemas/family@1
version: 2.1.0
kind: blueprint
noun: protocol
match: [protocol/*.md]
capabilities: [author, versioned, depends, generates, publishable, adoptable]
template: templates/protocol.md
generates: code
---
# Protocol Schema

Defines the complete structure for protocol blueprints (`type: protocol`).
Protocol blueprints specify wire-level specifications — endpoints,
message formats, authentication, identity, and shared types. They are
the foundation layer that every other blueprint type builds on.

## Header

The family `schemas/protocol` in grammar 1 ([`schemas/family`](family.md)): what a
file in `protocol/` is written as once the migration (`v2-migrate`) has
rewritten it, as [`schemas/architecture`](architecture.md#header) is for an
architecture blueprint. What each common field means is
[`schemas/common`](common.md#the-header-in-grammar-1)'s. The files are written
in the older form until then, which the sections from
[Frontmatter](#frontmatter) on describe and today's tooling reads; each of
its sections is a slot below under the heading files use today, so a file
being migrated walks with its narrative counted as what it is.

```yaml
header:
  schema:
    type: object
    required: [family, version]
    unevaluatedProperties: false
    properties:
      family:        {const: schemas/protocol@2}
      version:       {$ref: "schemas/blocks#/$defs/version"}
      requires:      {type: array, items: {$ref: "schemas/blocks#/$defs/requires-entry"}}
      tier:          {enum: [free, pro]}
      author:        {type: string}
      status:        {enum: [active, deprecated, end-of-life]}
      superseded_by: {$ref: "schemas/blocks#/$defs/ref"}
      end_of_life:   {$ref: "schemas/blocks#/$defs/date"}
      retired:       {$ref: "schemas/blocks#/$defs/retired"}
      formerly:      {type: array, items: {$ref: "schemas/blocks#/$defs/ref"}}
  uses:
    requires:   {use: depends, resolves: blueprint, send: always}
```

## Sections

```yaml
sections:
  undeclared: {policy: report, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: true, count: {min: 1, max: 1},
       prose: required, content: {max_paragraphs: 2}, use: navigates}
    - {slot: overview, heading: Overview, required: false, prose: required, use: navigates}
    - {slot: requirements, heading: Requirements, required: true, count: {min: 1, max: 1},
       blocks: [{type: requirements, count: {min: 1, max: 1}}], prose: forbidden,
       use: binds, produces: [code.behaviour]}
    - {slot: dependencies, heading: Dependencies, aliases: [Declaration], required: false, use: depends}
    - {slot: conventions, heading: Conventions, required: false, use: binds}
    - {slot: endpoints, heading: Endpoints, required: false, use: exposes}
    - {slot: interface, heading: Interface, aliases: [Interfaces],
       required: {when: {block_present: serves}},
       blocks: [{type: serves, count: {max: 1}}, {type: events, count: {max: 1}}],
       use: exposes, produces: [code.route, api.openapi, api.asyncapi]}
    - {slot: types, heading: Types, aliases: [Data Types], required: false,
       blocks: [{type: types, count: {max: 1}}], use: shapes, produces: [code.type, schema.json]}
    - {slot: authentication, heading: Authentication, required: false, use: binds}
    - {slot: errors, heading: Error Handling, aliases: [Errors], required: false,
       blocks: [{type: errors, count: {max: 1}}], use: shapes}
    - {slot: security, heading: Security, required: false, use: instructs}
    - {slot: verifies, heading: Verification, aliases: [Verification Checklist], required: true,
       blocks: [{type: verifies, count: {min: 1, max: 1}}], prose: forbidden,
       use: verifies, produces: [code.test, check]}
    - {slot: operation, heading: {starts_with: "Operation:"}, count: {min: 0},
       key: marker, prose: required, content: {no_rfc2119: true}, use: explains}
    - {slot: implementation-notes, heading: Implementation Notes, required: false, use: instructs}
    - {slot: migration-guide, heading: Migration Guide, required: false, use: instructs}
    - {slot: examples, heading: Examples, required: false, use: illustrates}
    - {slot: notes, heading: Notes, required: false, use: explains}
```

The slots follow [`schemas/architecture`](architecture.md#why-these-slots)'s
reasons: the contract is typed blocks in the slot each belongs to, every
requirement is covered by a check, an `Operation:` section explains one
requirement and states no rule, and a slot out of order is reported.

---

## Frontmatter

```markdown
<!-- blueprint
type: protocol
name: <protocol-name>
version: <semver>
requires: [<type/name>, ...]
platform: any
tier: free|pro
-->
```

### Required Fields

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `type` | enum | Must be `protocol` | Blueprint type |
| `name` | string | `[a-z][a-z0-9-]*`, max 64, matches filename | Unique identifier |
| `version` | semver | `MAJOR.MINOR.PATCH` | Blueprint version |
| `requires` | list | References existing blueprints | Dependencies |
| `platform` | enum | Typically `any` | Target platform |
| `tier` | enum | `free` or `pro` | Availability tier |

### Fields NOT Used

Protocol blueprints do NOT use: `kind`, `port`, `extends`, `depends_on`.
These are agent/domain-specific fields.

---

## Required Section Order

| # | Section | Heading | Form | Required | Description |
|---|---|---|---|---|---|
| 1 | Frontmatter | `<!-- blueprint -->` | narrative | **Yes** | YAML metadata |
| 2 | Title | `# Name` | narrative | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | narrative | **Yes** | Scope description |
| 4 | Dependencies | `## Dependencies` | yaml:requires | **Yes** | Dependency contracts |
| 5 | Conventions | `## Conventions` | narrative | **Yes** | Wire-level conventions (paths, content types, encoding) |
| 6 | Endpoints | `## Endpoints` | narrative | Conditional | Required for protocols that define HTTP endpoints |
| 7 | Types | `## Types` | yaml:types | Conditional | Data structures in YAML. **Required only where the blueprint declares types** — a protocol that references another's registry states that and does not restate it |
| 8 | Authentication | `## Authentication` | yaml:authentication | Conditional | Required for protocols that define auth |
| 9 | Error Handling | `## Error Handling` | yaml:error_codes | **Yes** | Error response format and codes |
| 10 | Security | `## Security` | yaml:security | **Yes** | Transport security, signing, verification |
| 11 | Implementation Notes | `## Implementation Notes` | narrative | **Yes** | Practical guidance |
| 12 | Verification Checklist | `## Verification Checklist` | narrative | **Yes** | Testable assertions (min 5) |

### Optional Sections

| Section | Insert After | When Needed |
|---------|-------------|-------------|
| `## Examples` | Any section | Extended request/response examples |
| `## Migration Guide` | Implementation Notes | Version upgrade instructions |

---

## Section Specifications

### Conventions (`## Conventions`)

Declares wire-level rules that all implementations must follow:

```markdown
- All paths are prefixed with `/v1`
- All request/response bodies are `application/json`
- All timestamps are `protocol/conventions:instant`
- ...
```

Each convention is a bullet point using RFC 2119 language (MUST, SHOULD, MAY).

### Endpoints (`## Endpoints`)

Each endpoint MUST be specified with:

```markdown
### <METHOD> <path>

**Purpose:** What this endpoint does

**Request:**
```yaml
request:
  headers:
    Content-Type: application/json
    Authorization: Bearer <token>  # if authenticated
  body:
    type: TypeName
    fields:
      - field: description
```

**Response (success):**
```yaml
response:
  status: <HTTP-status-code>
  body:
    type: TypeName
    fields:
      - field: description
```

**Response (error):**
```yaml
response:
  status: <HTTP-status-code>
  body:
    type: ErrorResponse
```

**Authentication:** Required|Optional|None

**Idempotency:** Yes|No — with explanation

**Rate Limit:** If applicable
```

#### Validation Rules

1. Every endpoint must have: Purpose, Request, Response (success), Response (error)
2. Request/Response types must reference types from the Types section
3. Authentication requirement must be stated explicitly
4. HTTP methods must be standard (GET, POST, PUT, DELETE, PATCH)
5. Paths must start with `/v1/`

### Types (`## Types`)

YAML format per [common.md](common.md) Types Section. Protocol types are
the canonical shared types — other blueprints reference them.

Protocol types MUST be comprehensive and self-contained. Every field,
every constraint, every relationship must be defined here. These types
are the single source of truth for the entire framework.

### Authentication (`## Authentication`)

If the protocol defines authentication mechanisms:

```yaml
authentication:
  mechanism: <token|signature|mutual-tls>
  token_format:
    structure: <description>
    fields: [field1, field2, ...]
    signing: <algorithm>
    expiry: <duration>
    verification: <process>
  flow:
    - step: <description>
```

### Error Handling (`## Error Handling`)

```yaml
error_format:
  type: ErrorResponse
  fields:
    error: string (required)
    code: string (optional, UPPER_SNAKE_CASE)
    details: object (optional)

error_codes:
  - code: <ERROR_CODE>
    status: <HTTP-status>
    description: <when-returned>
    retryable: true|false
```

### Security (`## Security`)

Protocol security specifications:

```yaml
security:
  transport:
    - requirement: <description>
  signing:
    algorithm: <algorithm>
    key_type: <key-type>
    process: <description>
  verification:
    process: <description>
  trust_model:
    description: <how-trust-is-established>
```

---

## Complete Template

````markdown
<!-- blueprint
type: protocol
name: <protocol-name>
version: 1.0.0
requires: [<dependencies>]
platform: any
tier: free
-->

# <Protocol Name>

<One-sentence summary.>

## Overview

<2–5 sentences describing scope and purpose.>

---

## Dependencies

```yaml
requires:
  - blueprint: <type/name>
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: <TypeName>
          fields_used: [<fields>]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately
```

---

## Conventions

- <Wire-level convention using RFC 2119 language>

---

## Endpoints

### <METHOD> /v1/<path>

**Purpose:** <description>

**Request:**
```yaml
request:
  body:
    type: <TypeName>
```

**Response (success):**
```yaml
response:
  status: 200
  body:
    type: <TypeName>
```

**Response (error):**
```yaml
response:
  status: <error-code>
  body:
    type: ErrorResponse
```

**Authentication:** Required
**Idempotency:** <Yes|No>

---

## Types

```yaml
types:
  <TypeName>:
    description: <description>
    fields:
      <field>:
        type: <type>
        description: <description>
```

---

## Authentication

```yaml
authentication:
  mechanism: <mechanism>
```

---

## Error Handling

```yaml
error_codes:
  - code: <CODE>
    status: <HTTP-status>
    description: <when>
    retryable: <bool>
```

---

## Security

```yaml
security:
  transport:
    - <requirement>
  signing:
    algorithm: ML-DSA-65
```

---

## Implementation Notes

- <Practical guidance>

---

## Verification Checklist

- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
````
