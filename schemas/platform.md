# Platform Schema

Defines the complete structure for platform blueprints (`type: platform`).
Platform blueprints provide implementation guidance for a specific runtime
environment — language-specific conventions, project structure, build
commands, dependency management, and platform-specific constraints.

---

## Frontmatter

```markdown
<!-- blueprint
type: platform
name: <platform-name>
version: <semver>
requires: [protocol/types, <type/name>, ...]
platform: <go|cloudflare|node|rust>
tier: free|pro
-->
```

### Required Fields

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `type` | enum | Must be `platform` | Blueprint type |
| `name` | string | `[a-z][a-z0-9-]*`, max 64, matches filename | Unique identifier |
| `version` | semver | `MAJOR.MINOR.PATCH` | Blueprint version |
| `requires` | list | References existing blueprints | Dependencies |
| `platform` | enum | Must be a specific platform (not `any`) | Target runtime |
| `tier` | enum | `free` or `pro` | Availability tier |

### Fields NOT Used

Platform blueprints do NOT use: `kind`, `port`, `extends`, `depends_on`.

### Special Constraint

The `platform` field MUST match the `name` field. A platform blueprint
describes itself — `name: go` implies `platform: go`.

---

## Required Section Order

| # | Section | Heading | Required | Description |
|---|---------|---------|----------|-------------|
| 1 | Frontmatter | `<!-- blueprint -->` | **Yes** | YAML metadata |
| 2 | Title | `# Name` | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | **Yes** | Scope description, why this platform fits Weblisk |
| 4 | Dependencies | `## Dependencies` | **Yes** | Dependency contracts |
| 5 | Project Structure | `## Project Structure` | **Yes** | Directory layout for orchestrator and agents |
| 6 | Runtime Requirements | `## Runtime Requirements` | **Yes** | Language version, dependencies, build tools |
| 7 | Build and Run | `## Build and Run` | **Yes** | Build commands, run commands, environment setup |
| 8 | Platform-Specific Conventions | `## Platform-Specific Conventions` | **Yes** | Language idioms, concurrency model, IO patterns |
| 9 | Type Mapping | `## Type Mapping` | **Yes** | How schema types map to language types |
| 10 | Security | `## Security` | **Yes** | Platform-specific security practices |
| 11 | Testing | `## Testing` | **Yes** | Test framework, test structure, CI guidance |
| 12 | Implementation Notes | `## Implementation Notes` | **Yes** | Practical guidance |
| 13 | Verification Checklist | `## Verification Checklist` | **Yes** | Testable assertions (min 5) |

### Optional Sections

| Section | Insert After | When Needed |
|---------|-------------|-------------|
| `## Deployment` | Build and Run | Platform-specific deployment guidance |
| `## Performance` | Platform-Specific Conventions | Performance tuning for this runtime |
| `## Examples` | Any section | Code examples in the target language |

---

## Section Specifications

### Project Structure (`## Project Structure`)

Defines the directory layout. Must include separate structures for:

1. **Orchestrator** — the central coordinator
2. **Agent** — a template agent implementation

```markdown
### Orchestrator
```
directory/
  file.ext    # Description
  file.ext    # Description
```

Build: `<build-command>`
Run: `<run-command>`

### Agent
```
agents/<name>/
  file.ext    # Description
  file.ext    # Description
```

Build: `<build-command>`
Run: `<run-command>`
```

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

If the platform achieves zero external dependencies (like Go), state this
explicitly and list only standard library packages used.

### Build and Run (`## Build and Run`)

Step-by-step instructions:

```markdown
### Build
```
<exact-build-commands>
```

### Run
```
<exact-run-commands-with-flags>
```

### Configuration Parameters
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Listen port | no | 9800 | Listen port |
```

### Platform-Specific Conventions (`## Platform-Specific Conventions`)

Language-specific implementation rules:

```markdown
### Concurrency
- <How the platform handles concurrent access>

### IO Safety
- <Request body limits, timeout handling>

### Error Handling
- <Language-idiomatic error patterns>

### Logging
- <Structured logging approach for this language>

### The HTTP Surface
- <A table mapping the endpoint's Operation to each symbol's spelling>
- <Where the routed paths are declared>
- <How a path and method reach a handler>
- <How a wrong method and an unmatched path answer>
```

The mapping table is **required** and MUST be exhaustive for the kinds of
symbol this platform generates — path constant, handler, request type and
response type at minimum:

| Symbol | Spelling | Example |
|---|---|---|
| Path constant | `Path<Operation>` | `PathRegister` |
| Handler | `handle<Operation>` | `handleRegister` |

An architecture blueprint declares an endpoint's `Operation`; this table is how
that one declared name becomes an identifier in this language, and it is the
ONLY place a platform may decide spelling. "Follow the language's conventions"
is not a rule two generations apply identically — casing, prefix and suffix MUST
be written down. A platform blueprint MUST NOT introduce a name the declaring
blueprint did not state. See [Declared Names](common.md#declared-names).

`### The HTTP Surface` states how the endpoints an architecture blueprint
declares become routes in this language. It is required for the same reason
the type mapping is: the architecture states `POST /v1/register`, and without
a stated convention each generation invents its own arrangement.

That is not a style preference. A generated component whose HTTP surface is
arranged differently on each build changes the symbols every other file depends
on, so files that were correct become non-compliant and are rebuilt — the churn
described in [`architecture/generation`](../architecture/generation.md) under
"A rebuild input MUST NOT be something the build changes". The convention MUST
be specific enough that two builds of the same blueprints produce the same
arrangement, and MUST NOT constrain how patterns are *spelled* — a named
constant is better than a repeated literal, and a platform blueprint exists to
make the artifact good, not to make a checker's job easy.

### Type Mapping (`## Type Mapping`)

How schema scalar types map to language types:

```markdown
| Schema Type | <Language> Type | Notes |
|-------------|----------------|-------|
| `string` | `string` | |
| `int` | `int32` | |
| `int64` | `int64` | Used for timestamps |
| `float` | `float64` | |
| `bool` | `bool` | |
| `object` | `map[string]any` | Or typed struct |
| `list` | `[]T` | Typed slice |
| `uuid` | `string` | Validated format |
```

### Security (`## Security`)

Platform-specific security practices:

```markdown
### Input Validation
- <Request body size limits>
- <Input sanitization approach>

### Cryptography
- <Which crypto libraries to use>
- <Key management approach>

### Dependencies
- <Dependency audit requirements>
- <Supply chain security>
```

### Testing (`## Testing`)

```markdown
### Framework
- <Test framework name and version>

### Structure
```
tests/
  unit/       # Unit tests
  integration/ # Integration tests
```

### Running Tests
```
<exact-test-commands>
```

### Coverage
- <Minimum coverage requirements>
```

## Complete Template

````markdown
<!-- blueprint
type: platform
name: <platform-name>
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, architecture/orchestrator]
platform: <platform-name>
tier: free
-->

# Platform: <Platform Name>

<One-sentence summary of why this platform fits Weblisk.>

## Overview

<2–5 sentences describing the platform, its strengths, and how it
maps to Weblisk's architecture.>

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: ["*"]   # the whole type; quoted because a bare * is a YAML alias
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Project Structure

### Orchestrator
```
<directory-layout>
```

### Agent
```
<directory-layout>
```

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

### Build
```
<commands>
```

### Run
```
<commands>
```

---

## Platform-Specific Conventions

### Concurrency
- <rules>

### IO Safety
- <rules>

---

## Type Mapping

| Schema Type | <Language> Type | Notes |
|-------------|----------------|-------|
| `string` | | |
| `int` | | |
| `int64` | | |

---

## Security

- <Platform-specific security practices>

---

## Testing

- <Test framework and approach>

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
