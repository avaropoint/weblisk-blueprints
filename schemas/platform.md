# Platform Schema

Defines the complete structure for platform blueprints (`type: platform`).
Platform blueprints provide implementation guidance for a specific runtime
environment — language-specific conventions, project structure, build
commands, dependency management, and platform-specific constraints.

---

## Frontmatter

```yaml
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

A platform blueprint MAY also carry a `### Generation Manifest` subsection
inside Project Structure — see below.

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
```

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

### Generation Manifest (`### Generation Manifest`)

**Optional.** A machine-readable form of the layout stated in Project Structure,
for tooling that GENERATES an implementation for this platform.

#### Status: optional to the framework, required by the tooling

These are different claims and both are true, so both are stated.

**Optional to the framework.** It is not the definition of a hub.
`protocol/spec.md` defines the wire contract and `architecture/testing.md` proves
an implementation meets it. A hub written by hand, produced by other tooling, or
written in a language with no platform blueprint is fully valid the moment it
serves the protocol and passes conformance. A platform blueprint with no manifest
is complete, and a manifest that disagrees with a working implementation is the
manifest's problem.

**Required by the reference tooling.** `weblisk server init` uses the manifest to
generate one file per call against a fixed file set. A platform blueprint without
one falls back to requesting a whole implementation in a single call, which has
no checkpoint, no attributable failure and no progress. That path exists and is
not recommended.

So: a platform MAY omit the manifest, and a platform that wants repeatable
generation MUST have one. Implementations of the framework are free to ignore
this section entirely; implementations of the reference CLI are not.

#### It is a versioned artifact

A manifest is content other tooling reads, so it changes under the same rules as
any other blueprint (`patterns/versioning`):

- Adding a file, or adding `must_define`/`must_serve` entries, is a MINOR change:
  existing generated implementations remain valid, and the next generation
  produces more.
- Removing a file, or renaming one, is a MAJOR change: an implementation
  generated from the previous manifest no longer matches the current one.
- A manifest MUST be validated against the rules below before publication.
  Reference implementation: `weblisk validate --manifest`.

A manifest that has never been exercised by a generation run MUST say so
(rule 7). An untested file list that reads like a tested one is the more
expensive kind of documentation.

#### Why it exists

Generating a whole implementation in one request has no checkpoint, no
attributable failure and no progress, and it leaves the FILE SET to the
generating model rather than to the blueprint. A manifest makes one route
repeatable: the same blueprints produce the same structure however many times,
and by whichever model.

Repeatability here means behavioural equivalence, not identical source. Two
models will name and split things differently. What is fixed is what a caller can
observe — the files that exist, what each exports, the endpoints served, and the
conformance result.

#### Structure

```yaml
generate:
  <target>:                 # orchestrator | agent | domain | gateway
    root: <dir>             # where files are written, relative to the project
    build: <command>        # must succeed before conformance is attempted
    files:
      - path: <relative>    # required
        purpose: <text>     # required — what this file is for
        must_define: []     # optional — symbols that must exist
        must_serve: []      # optional — "METHOD /path" this file must handle
    conformance: [L1]       # levels from architecture/testing.md
```

#### Validation Rules

1. Every `path` MUST be relative and MUST NOT traverse outside `root`.
2. `purpose` MUST be present on every file — a path with no stated purpose gives
   a generator nothing to generate.
3. `must_serve` entries MUST use endpoints defined in `protocol/spec.md`; a
   manifest MUST NOT introduce an endpoint the protocol does not define.
4. The union of `must_serve` across all files for the `orchestrator` target MUST
   cover every orchestrator endpoint in `protocol/spec.md`.
5. `build` MUST be a command that fails on a structurally invalid result.
6. `conformance` MUST name at least `L1`.
7. A manifest that has not been exercised by a generation run SHOULD say so, so
   that an untested file list is not mistaken for a tested one.

#### Consuming it

Tooling SHOULD generate one file per call rather than one call per
implementation, and SHOULD verify `must_define` and `must_serve` before running
`build`, and `build` before conformance. Each check is cheaper than the one after
it and localises the failure further.


---

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
          fields_used: [*]
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
