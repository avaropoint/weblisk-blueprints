# Pattern Schema

Defines the complete structure for pattern blueprints (`type: pattern`).
Pattern blueprints specify cross-cutting concerns — reusable contracts,
types, and behaviors that agents and domains inherit via the `extends`
field. Patterns are the framework's composition mechanism.

---

## Frontmatter

```yaml
<!-- blueprint
type: pattern
name: <pattern-name>
version: <semver>
requires: [<type/name>, ...]
platform: any|<specific>
tier: free|pro
-->
```

### Required Fields

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `type` | enum | Must be `pattern` | Blueprint type |
| `name` | string | `[a-z][a-z0-9-]*`, max 64, matches filename | Unique identifier |
| `version` | semver | `MAJOR.MINOR.PATCH` | Blueprint version |
| `requires` | list | References existing blueprints | Dependencies |
| `platform` | enum | `any`, `go`, `cloudflare`, `node`, `rust` | Target platform |
| `tier` | enum | `free` or `pro` | Availability tier |

### Fields NOT Used

Pattern blueprints do NOT use: `kind`, `port`, `extends`, `depends_on`.
Patterns are extended by others — they do not extend other patterns
(use `requires` for pattern-to-pattern dependencies).

---

## Required Section Order

| # | Section | Heading | Required | Description |
|---|---------|---------|----------|-------------|
| 1 | Frontmatter | `<!-- blueprint -->` | **Yes** | YAML metadata |
| 2 | Title | `# Name` | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | **Yes** | Scope description |
| 4 | Dependencies | `## Dependencies` | **Yes** | Dependency contracts |
| 5 | Design Principles | `## Design Principles` | **Yes** | Core design decisions (numbered list) |
| 6 | Contracts | `## Contracts` | **Yes** | Behaviors that extenders inherit |
| 7 | Types | `## Types` | Conditional | Data structures in YAML (if pattern defines types) |
| 8 | Configuration | `## Configuration` | Optional | Default config extenders may override |
| 9 | Error Handling | `## Error Handling` | Optional | Error patterns extenders inherit |
| 10 | Implementation Notes | `## Implementation Notes` | **Yes** | Practical guidance |
| 11 | Verification Checklist | `## Verification Checklist` | **Yes** | Testable assertions (min 5) |

### Optional Sections

| Section | Insert After | When Needed |
|---------|-------------|-------------|
| `## Examples` | Any section | Usage examples showing how extenders adopt the pattern |
| `## Overrides` | Contracts | How extenders may customize inherited behavior |

---

## Section Specifications

### Design Principles (`## Design Principles`)

A numbered list of core design decisions that define the pattern's
philosophy. These are non-negotiable — extenders adopt these principles.

```markdown
## Design Principles

1. **Principle Name** — Description of the principle and why it matters.
2. **Another Principle** — Description.
```

Minimum 3 principles.

### Contracts (`## Contracts`)

The behaviors, interfaces, and structures that extenders inherit.
This is the pattern's public API — what agents and domains get when
they declare `extends: [patterns/<name>]`.

```yaml
contracts:
  behaviors:
    - name: <behavior-name>
      description: What this behavior provides
      parameters:
        - name: <param>
          type: <type>
          required: true|false
          default: <value>
          description: What this parameter controls
      inherits: <what extenders get automatically>
      overridable: true|false
      override_constraints: <limits on overrides>

  types:
    - name: <TypeName>
      description: Type provided to extenders
      inherited_by: <what section of the extender receives this type>

  endpoints:
    - path: /v1/<path>
      description: Endpoint contract provided to extenders
      inherited_by: <what section of the extender serves this>

  events:
    - topic: <pattern-namespace>.<event>
      description: Event contract provided to extenders
      payload: {<fields>}
```

#### Behavior Specification

Each behavior MUST include:

1. `name` — Unique identifier for the behavior
2. `description` — What the behavior provides
3. `parameters` — Configuration points with types and defaults
4. `inherits` — What the extender gets automatically (endpoints, types, logic)
5. `overridable` — Whether the extender can customize this behavior
6. `override_constraints` — Limits on what can be overridden

#### Validation Rules

1. Every behavior must have `name`, `description`, and `parameters`
2. Parameters must have `name`, `type`, and `description`
3. Types declared in contracts must be defined in the Types section
4. Events declared in contracts must define their payload structure
5. Overridable behaviors must declare `override_constraints`

### Types (`## Types`)

YAML format per [common.md](common.md) Types Section. Pattern types are
inherited by extenders — they become part of the extender's type system.

Pattern types SHOULD be generic and composable. They MUST NOT reference
agent-specific fields or domain-specific logic.

### Configuration (`## Configuration`)

Default configuration that extenders inherit. Extenders may override
specific values within declared constraints.

```yaml
config:
  parameter_name:
    type: <type>
    default: <value>
    overridable: true|false
    min: <number>
    max: <number>
    description: What this controls
```

### Overrides (`## Overrides`)

If the pattern supports customization, document what extenders can override:

```yaml
overrides:
  - target: <behavior-or-config-name>
    scope: <what-can-change>
    constraints: <limits>
    syntax: |
      <YAML showing override format in the extending blueprint>
```

---

## Complete Template

````markdown
<!-- blueprint
type: pattern
name: <pattern-name>
version: 1.0.0
requires: [<dependencies>]
platform: any
tier: free
-->

# <Pattern Name>

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

## Design Principles

1. **<Principle>** — <Description>
2. **<Principle>** — <Description>
3. **<Principle>** — <Description>

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: <behavior>
      description: <what-it-provides>
      parameters:
        - name: <param>
          type: <type>
          required: true
          description: <what-it-controls>
      inherits: <what-extenders-get>
      overridable: true
      override_constraints: <limits>
```

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

## Implementation Notes

- <Practical guidance for extenders>

---

## Verification Checklist

- [ ] <Testable assertion for extenders>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
````
