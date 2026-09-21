# Language Schema

Defines the complete structure for language blueprints (`type: language`).
A language blueprint says **what is essential when building in one programming
language** — dependency policy, project layout, concurrency, error handling, and
the primitives its standard library does and does not supply.

It says nothing about *what* is being built, and nothing about where it runs.
Those are [`architecture.md`](architecture.md) and [`platform.md`](platform.md).

---

## Frontmatter

```markdown
<!-- blueprint
type: language
name: <language-name>
version: <semver>
requires: [protocol/types, <type/name>, ...]
language: <language-name>
tier: free|pro
-->
```

### Required Fields

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `type` | enum | Must be `language` | Blueprint type |
| `name` | string | `[a-z][a-z0-9-]*`, max 64, matches filename | Unique identifier |
| `version` | semver | `MAJOR.MINOR.PATCH` | Blueprint version |
| `requires` | list | References existing blueprints | Dependencies |
| `language` | string | Must match the `name` field | The language this describes |
| `tier` | enum | `free` or `pro` | Availability tier |

### Fields NOT Used

Language blueprints do NOT use: `kind`, `port`, `extends`, `depends_on`, `platform`.

### Why no `platform`

A language does not map to a platform, and declaring one would assert that it does.
TypeScript is TypeScript whether it runs on Node, on Workers or in a browser; Go is
Go whether the binary runs on a laptop or in a container.

The pairing is chosen by whatever is being generated — a platform blueprint declares
which language it runs, and a skill may require a specific combination where one is
genuinely load-bearing. Neither of those is a property of the language.

### Special Constraint

The `language` field MUST match the `name` field. A language blueprint describes
itself — `name: go` implies `language: go`.

---

## Required Section Order

| # | Section | Heading | Form | Required | Description |
|---|---|---|---|---|---|
| 1 | Frontmatter | `<!-- blueprint -->` | narrative | **Yes** | YAML metadata |
| 2 | Title | `# Language: Name` | narrative | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | narrative | **Yes** | What is essential when building in this language |
| 4 | Dependencies | `## Dependencies` | yaml:requires | **Yes** | Dependency contracts |
| 5 | Primitive Mapping | `## Primitive Mapping` | table | **Yes** | Where each required primitive comes from in this language |
| 6 | Project Structure | `## Project Structure` | narrative | **Yes** | Module and directory layout |
| 7 | Runtime Requirements | `## Runtime Requirements` | yaml:runtime | **Yes** | Language version, dependency policy, build tools |
| 8 | Build and Run | `## Build and Run` | table | **Yes** | Build and run commands |
| 9 | Language Conventions | `## Language Conventions` | table | **Yes** | Idiom, concurrency model, IO patterns, error handling, logging |
| 10 | Type Mapping | `## Type Mapping` | table | **Yes** | How schema types map to this language's types |
| 11 | Security | `## Security` | narrative | **Yes** | Input validation, cryptography, dependency policy, key handling |
| 12 | Testing | `## Testing` | narrative | **Yes** | Test framework, structure, CI guidance |
| 13 | Implementation Notes | `## Implementation Notes` | narrative | **Yes** | Practical guidance |
| 14 | Verification Checklist | `## Verification Checklist` | narrative | **Yes** | Testable assertions (min 5) |

### Optional Sections

| Section | Insert After | When Needed |
|---------|-------------|-------------|
| `## Storage Mapping (<Language>)` | Type Mapping | The language's answer for the storage contract |
| `## Concurrency (<Language>-Specific)` | Language Conventions | Concurrency needs more than the conventions table |
| `## Project Structure: Domain Controller` | Project Structure | Domain controllers differ structurally |
| `## Examples` | Any section | Code examples |

---

## Section Specifications

### Primitive Mapping (`## Primitive Mapping`)

One row per primitive the specification blueprints require, naming what supplies it
**in this language's standard library**, or what must be brought in when it does not.

This is the language's own question, and it is not the platform's. A standard library
either ships a memory-hard key-derivation function or it does not, whatever the code
later runs on.

```markdown
| Primitive required by | Provided in <Language> by | Status |
|---|---|---|
| `protocol/identity` — signature algorithm | <module, or a named dependency> | stdlib \| dependency |
| `protocol/types` — canonical JSON | <module> | stdlib |
```

A primitive the language cannot provide MUST be marked **UNFILLED** rather than
omitted or approximated, per [`common.md`](common.md#platform-neutrality). The rule
lives there and is not restated here.

### Language Conventions (`## Language Conventions`)

Idiom a generator must follow: concurrency model, IO safety, error handling, logging,
naming, and package or module organisation.

This section carries what is true of the language everywhere. Anything true only on
one runtime belongs to that runtime's platform blueprint.

### Runtime Requirements (`## Runtime Requirements`)

```yaml
runtime:
  language: <name>
  version: "<minimum-version>"
  dependencies:
    required:
      - name: <package>
        version: "<version>"
        purpose: <why-needed>
    optional:
      - name: <package>
        version: "<version>"
        purpose: <why-useful>
  build_tools:
    - name: <tool>
      version: "<version>"
      purpose: <what-it-does>
```

Where the language achieves zero external dependencies, state it explicitly and list
only standard library packages used.

---

## Complete Template

````markdown
<!-- blueprint
type: language
name: <language-name>
version: 1.0.0
requires: [protocol/types, protocol/identity]
language: <language-name>
tier: free
-->

# Language: <Language Name>

<One-sentence summary of what is essential when building in it.>

## Overview

<2–5 sentences: dependency policy, what the standard library gives you, and what
this blueprint decides.>

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
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Primitive Mapping

| Primitive required by | Provided in <Language> by | Status |
|---|---|---|
| `protocol/identity` — signature algorithm | <module or dependency> | stdlib |

---

## Project Structure

<Module layout.>

---

## Runtime Requirements

```yaml
runtime:
  language: <name>
  version: "<version>"
  dependencies:
    required: []
    optional: []
```

---

## Build and Run

| Step | Command |
|---|---|
| Build | `<command>` |
| Run | `<command>` |

---

## Language Conventions

| Concern | Convention |
|---|---|
| Concurrency | <idiom> |
| IO safety | <idiom> |
| Error handling | <idiom> |
| Logging | <idiom> |

---

## Type Mapping

| Schema type | <Language> type |
|---|---|
| `string` | <type> |

---

## Security

<Input validation, cryptography, dependency policy, key handling.>

---

## Testing

<Framework, structure, CI.>

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
