---
family: schemas/family@1
version: 2.1.0
kind: blueprint
noun: pattern
match: [patterns/*.md]
capabilities: [author, versioned, depends, generates, publishable, adoptable]
template: templates/pattern.md
generates: code
---
# Pattern Schema

Defines the complete structure for pattern blueprints (`type: pattern`).
Pattern blueprints specify cross-cutting concerns — reusable contracts,
types, and behaviors that agents and domains inherit via the `extends`
field. Patterns are the framework's composition mechanism.

## Header

The family `schemas/pattern` in grammar 1 ([`schemas/family`](family.md)): what a
file in `patterns/` is written as once the migration (`v2-migrate`) has
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
      family:        {const: schemas/pattern@2}
      version:       {$ref: "schemas/blocks#/$defs/version"}
      requires:      {type: array, items: {$ref: "schemas/blocks#/$defs/requires-entry"}}
      tier:          {enum: [free, pro]}
      author:        {type: string}
      status:        {enum: [active, deprecated, end-of-life]}
      superseded_by: {$ref: "schemas/blocks#/$defs/ref"}
      end_of_life:   {$ref: "schemas/blocks#/$defs/date"}
      retired:       {$ref: "schemas/blocks#/$defs/retired"}
      formerly:      {type: array, items: {$ref: "schemas/blocks#/$defs/ref"}}
      adoption:      {enum: [required, opt-in]}
      drivers:       {type: array, items: {type: string}}
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
    - {slot: design-principles, heading: Design Principles, required: false, use: explains}
    - {slot: contracts, heading: Contracts, required: false, use: binds}
    - {slot: overrides, heading: Overrides, required: false, use: binds}
    - {slot: types, heading: Types, aliases: [Data Types], required: false,
       blocks: [{type: types, count: {max: 1}}], use: shapes, produces: [code.type, schema.json]}
    - {slot: config, heading: Configuration, required: false,
       blocks: [{type: config, count: {max: 1}}], use: configures}
    - {slot: errors, heading: Error Handling, aliases: [Errors], required: false,
       blocks: [{type: errors, count: {max: 1}}], use: shapes}
    - {slot: verifies, heading: Verification, aliases: [Verification Checklist], required: true,
       blocks: [{type: verifies, count: {min: 1, max: 1}}], prose: forbidden,
       use: verifies, produces: [code.test, check]}
    - {slot: operation, heading: {starts_with: "Operation:"}, count: {min: 0},
       key: marker, prose: required, content: {no_rfc2119: true}, use: explains}
    - {slot: implementation-notes, heading: Implementation Notes, required: false, use: instructs}
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

| # | Section | Heading | Form | Required | Description |
|---|---|---|---|---|---|
| 1 | Frontmatter | `<!-- blueprint -->` | narrative | **Yes** | YAML metadata |
| 2 | Title | `# Name` | narrative | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | narrative | **Yes** | Scope description |
| 4 | Dependencies | `## Dependencies` | yaml:requires | **Yes** | Dependency contracts |
| 5 | Design Principles | `## Design Principles` | narrative | **Yes** | Core design decisions (numbered list) |
| 6 | Contracts | `## Contracts` | yaml:contracts | **Yes** | Behaviors that extenders inherit |
| 7 | Types | `## Types` | yaml:types | Conditional | Data structures in YAML (if pattern defines types) |
| 8 | Configuration | `## Configuration` | structured | Optional | Default config extenders may override |
| 9 | Error Handling | `## Error Handling` | table | Optional | Error patterns extenders inherit |
| 10 | Implementation Notes | `## Implementation Notes` | narrative | **Yes** | Practical guidance |
| 11 | Verification Checklist | `## Verification Checklist` | narrative | **Yes** | Testable assertions (min 5) |

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
