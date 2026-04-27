# Protocol Schema

Defines the complete structure for protocol blueprints (`type: protocol`).
Protocol blueprints specify wire-level specifications — endpoints,
message formats, authentication, identity, and shared types. They are
the foundation layer that every other blueprint type builds on.

---

## Frontmatter

```yaml
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

| # | Section | Heading | Required | Description |
|---|---------|---------|----------|-------------|
| 1 | Frontmatter | `<!-- blueprint -->` | **Yes** | YAML metadata |
| 2 | Title | `# Name` | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | **Yes** | Scope description |
| 4 | Dependencies | `## Dependencies` | **Yes** | Dependency contracts |
| 5 | Conventions | `## Conventions` | **Yes** | Wire-level conventions (paths, content types, encoding) |
| 6 | Endpoints | `## Endpoints` | Conditional | Required for protocols that define HTTP endpoints |
| 7 | Types | `## Types` | **Yes** | All data structures in YAML |
| 8 | Authentication | `## Authentication` | Conditional | Required for protocols that define auth |
| 9 | Error Handling | `## Error Handling` | **Yes** | Error response format and codes |
| 10 | Security | `## Security` | **Yes** | Transport security, signing, verification |
| 11 | Implementation Notes | `## Implementation Notes` | **Yes** | Practical guidance |
| 12 | Verification Checklist | `## Verification Checklist` | **Yes** | Testable assertions (min 5) |

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
- All timestamps are Unix epoch seconds (`int64`)
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
    algorithm: Ed25519
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
