# Architecture Schema

Defines the complete structure for architecture blueprints
(`type: architecture`). Architecture blueprints specify system-level
components — the orchestrator, agent framework, storage engine, domain
model, lifecycle management, and other structural concerns. They define
responsibilities, data flow, and interfaces that agents and domains
build on.

---

## Frontmatter

```yaml
<!-- blueprint
type: architecture
name: <component-name>
version: <semver>
requires: [<type/name>, ...]
platform: any|<specific>
tier: free|pro
-->
```

### Required Fields

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `type` | enum | Must be `architecture` | Blueprint type |
| `name` | string | `[a-z][a-z0-9-]*`, max 64, matches filename | Unique identifier |
| `version` | semver | `MAJOR.MINOR.PATCH` | Blueprint version |
| `requires` | list | References existing blueprints | Dependencies |
| `platform` | enum | `any`, `go`, `cloudflare`, `node`, `rust` | Target platform |
| `tier` | enum | `free` or `pro` | Availability tier |

### Fields NOT Used

Architecture blueprints do NOT use: `kind`, `port`, `extends`, `depends_on`.

---

## Required Section Order

| # | Section | Heading | Required | Description |
|---|---------|---------|----------|-------------|
| 1 | Frontmatter | `<!-- blueprint -->` | **Yes** | YAML metadata |
| 2 | Title | `# Name` | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | **Yes** | Scope description |
| 4 | Dependencies | `## Dependencies` | **Yes** | Dependency contracts |
| 5 | Architecture | `## Architecture` | **Yes** | Component diagram and responsibilities |
| 6 | Responsibilities | `## Responsibilities` | **Yes** | What this component owns and does NOT own |
| 7 | Interfaces | `## Interfaces` | **Yes** | Public API surface (methods, endpoints, events) |
| 8 | Data Flow | `## Data Flow` | **Yes** | How data moves through this component |
| 9 | Types | `## Types` | Conditional | Data structures in YAML (if component defines types) |
| 10 | Configuration | `## Configuration` | Optional | Component-level configuration |
| 11 | Security | `## Security` | Conditional | Required for components with trust/auth responsibilities |
| 12 | Implementation Notes | `## Implementation Notes` | **Yes** | Practical guidance |
| 13 | Verification Checklist | `## Verification Checklist` | **Yes** | Testable assertions (min 5) |

### Optional Sections

| Section | Insert After | When Needed |
|---------|-------------|-------------|
| `## Collaboration` | Data Flow | Multi-component interaction patterns |
| `## Error Handling` | Interfaces | Component-level error strategies |
| `## Scaling` | Implementation Notes | Scaling characteristics of this component |
| `## Examples` | Any section | Extended usage examples |

---

## Section Specifications

### Architecture (`## Architecture`)

A visual diagram (ASCII art) showing the component's internal structure
and its position relative to other components. Followed by a prose
description of each sub-component.

```markdown
## Architecture

```
┌──────────────────────────────┐
│  Component Name              │
│  ┌────────────────────────┐  │
│  │  Sub-component A       │  │
│  │  - responsibility 1    │  │
│  │  - responsibility 2    │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │  Sub-component B       │  │
│  └────────────────────────┘  │
└──────────────────────────────┘
```
```

### Responsibilities (`## Responsibilities`)

Two lists: what the component IS responsible for, and what it is NOT.

```markdown
## Responsibilities

### Owns
- Responsibility 1
- Responsibility 2

### Does NOT Own
- Thing explicitly excluded (and why)
- Another exclusion
```

Both lists are required. The "Does NOT Own" list prevents scope creep
and clarifies boundaries.

### Interfaces (`## Interfaces`)

The public surface that other components consume:

```yaml
interfaces:
  methods:
    - name: <MethodName>
      signature: <input> → <output>
      description: What this method does
      called_by: [<component-types>]

  endpoints:
    - path: /v1/<path>
      methods: [GET, POST, ...]
      description: What this endpoint does
      served_by: <this-component>

  events:
    - topic: <namespace>.<event>
      direction: publish|subscribe
      description: What this event carries
```

If the component defines a behavioral contract (like the agent framework's
Execute/HandleMessage/HandleEvent interface), document each method with:
- Signature (input types → output types)
- Purpose
- Who calls it
- What it returns

### Data Flow (`## Data Flow`)

Describes how data enters, moves through, and exits the component.
Use numbered flow descriptions or sequence diagrams:

```markdown
## Data Flow

### Registration Flow
1. Agent sends AgentManifest to orchestrator via POST /v1/register
2. Orchestrator validates manifest and signature
3. Orchestrator assigns agent_id and generates auth token
4. Orchestrator updates service directory
5. Orchestrator broadcasts updated directory to all agents

### Message Flow
1. Agent A sends AgentMessage to orchestrator via POST /v1/message
2. ...
```

Each flow must identify:
- Entry point (what triggers the flow)
- Each step with the component or actor responsible
- Data transformed or created at each step
- Exit point (what the flow produces)

### Types (`## Types`)

YAML format per [common.md](common.md) Types Section. Architecture types
define the structural contracts that agents and domains implement.

### Security (`## Security`)

Required for architecture components that have security responsibilities
(e.g., orchestrator trust model, identity management, gateway auth):

```yaml
security:
  trust_model:
    description: How trust is established and maintained
  boundaries:
    - boundary: <description>
  enforcement:
    - rule: <what-is-enforced>
      mechanism: <how>
```

---

## Complete Template

````markdown
<!-- blueprint
type: architecture
name: <component-name>
version: 1.0.0
requires: [<dependencies>]
platform: any
tier: free
-->

# <Component Name>

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

## Architecture

```
<ASCII diagram>
```

<Description of sub-components>

---

## Responsibilities

### Owns
- <Responsibility>

### Does NOT Own
- <Exclusion and rationale>

---

## Interfaces

```yaml
interfaces:
  methods:
    - name: <Method>
      signature: <input> → <output>
      description: <purpose>
      called_by: [<components>]
```

---

## Data Flow

### <Flow Name>
1. <Step>
2. <Step>

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

- <Practical guidance>

---

## Verification Checklist

- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
````
