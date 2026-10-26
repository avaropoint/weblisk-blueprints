---
family: schemas/family@1
version: 2.0.0
kind: blueprint
noun: blueprint
match: [architecture/*.md]
capabilities: [author, versioned, depends, generates, publishable, adoptable]
template: templates/architecture.md
adopt: {mode: link, record: build-lock}
generates: code
---
# Architecture Schema

The declaration of the family `schemas/architecture`: architecture blueprints,
each specifying one system-level component — the orchestrator, the admin
gateway, the agent framework, storage, lifecycle and the other structural
concerns agents and domains build on. A file written to it names `family:
schemas/architecture@2`, and starts from
[`templates/architecture.md`](../templates/architecture.md).

The blueprints in `architecture/` are still written in the older form: the
`<!-- blueprint -->` comment and the sections [The older form](#the-older-form)
describes, which today's tooling reads. The migration (`v2-migrate`) rewrites
each file to this family. Until it has, both forms are described here, each
once: the Header and Sections blocks are the family, and everything from The
older form on is what a file in the older form follows.

## Header

```yaml
header:
  schema:
    type: object
    required: [family, version]
    unevaluatedProperties: false
    properties:
      family:        {const: schemas/architecture@2}
      version:       {$ref: "schemas/blocks#/$defs/version"}
      requires:      {type: array, items: {$ref: "schemas/blocks#/$defs/requires-entry"}}
      depends_on:    {type: array, items: {$ref: "schemas/blocks#/$defs/ref"}}
      runs_with:     {type: array, items: {$ref: "schemas/blocks#/$defs/ref"}}
      cardinality:   {enum: [singleton, named]}
      provides:      {type: array, items: {$ref: "schemas/blocks#/$defs/ref"}}
      adoption:      {enum: [required, opt-in]}
      tier:          {enum: [free, pro]}
      author:        {type: string}
      status:        {enum: [active, deprecated, end-of-life]}
      superseded_by: {$ref: "schemas/blocks#/$defs/ref"}
      end_of_life:   {$ref: "schemas/blocks#/$defs/date"}
      retired:       {$ref: "schemas/blocks#/$defs/retired"}
      formerly:      {type: array, items: {$ref: "schemas/blocks#/$defs/ref"}}
  uses:
    requires:   {use: depends, resolves: blueprint, send: always}
    depends_on: {use: depends, resolves: blueprint, send: always}
    runs_with:  {use: depends, resolves: blueprint, send: always}
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
    - {slot: dependencies, heading: Dependencies, aliases: [Declaration], required: false,
       use: depends}
    - {slot: architecture, heading: Architecture, required: false, use: explains}
    - {slot: responsibilities, heading: Responsibilities, required: false, use: explains}
    - {slot: endpoints, heading: Endpoints, required: false, use: exposes}
    - {slot: interface, heading: Interface, aliases: [Interfaces],
       required: {when: {block_present: serves}},
       blocks: [{type: serves, count: {max: 1}}, {type: events, count: {max: 1}}],
       use: exposes, produces: [code.route, api.openapi]}
    - {slot: errors, heading: Error Handling, aliases: [Errors], required: false,
       blocks: [{type: errors, count: {max: 1}}], use: shapes}
    - {slot: data-flow, heading: Data Flow, required: false, use: explains}
    - {slot: design-principles, heading: Design Principles, required: false, use: explains}
    - {slot: collaboration, heading: Collaboration, required: false, use: explains}
    - {slot: types, heading: Types, aliases: [Data Types], required: false,
       blocks: [{type: types, count: {max: 1}}], use: shapes, produces: [code.type, schema.json]}
    - {slot: config, heading: Configuration, required: false,
       blocks: [{type: config, count: {max: 1}}], use: configures}
    - {slot: security, heading: Security, required: false, use: instructs}
    - {slot: verifies, heading: Verification, aliases: [Verification Checklist], required: true,
       blocks: [{type: verifies, count: {min: 1, max: 1}}], prose: forbidden,
       use: verifies, produces: [code.test, check]}
    - {slot: operation, heading: {starts_with: "Operation:"}, count: {min: 0},
       key: marker, prose: required, content: {no_rfc2119: true}, use: explains}
    - {slot: implementation-notes, heading: Implementation Notes, required: false,
       use: instructs}
    - {slot: scaling, heading: Scaling, required: false, use: explains}
    - {slot: examples, heading: Examples, required: false, use: illustrates}
    - {slot: notes, heading: Notes, required: false, use: explains}
```

## Why these slots

**The contract sits where it is explained.** Requirements, types, the
operations a component serves, its configuration, its errors and the checks
that prove it are typed blocks
([`schemas/blocks`](blocks.md#blocks)), each in the slot it belongs to and
beside the prose that gives its reasons. The header holds only identity and
dependencies, whose fields [`schemas/common`](common.md#the-header-in-grammar-1)
defines. A file names no `platform`: a blueprint is written for every platform
([Platform Neutrality](common.md#platform-neutrality)), and which one a build
targets is the build's choice.

**Every requirement is covered and every reason is addressable.** `Requirements`
and `Verification` are required, and each check's `covers` names the
requirements it proves. An `Operation:` section explains one requirement and
is keyed by its `wl:explains` marker, so a prompt that cites the requirement
can be sent its reason and nothing else; because it explains, it states no
new rule, which is why it may not say MUST.

**The older form's sections are slots too.** Overview, Architecture,
Responsibilities, Endpoints, Data Flow, Design Principles, Collaboration,
Security, Implementation Notes, Scaling and Examples are declared under the
headings files use today, and the older headings of a renamed slot
(`Interfaces`, `Verification Checklist`, `Declaration`) are its aliases. A file
being migrated therefore walks with its narrative counted as what it is, and
what no slot declares is reported, never refused, so the share of bytes
outside every slot is measured rather than hidden. `Dependencies` is carried
only until the migration folds it into the header's `requires`, which is its
home in this family.

**The order above is canonical.** In grammar 1 a slot written out of order is
reported (`slot-order`), and the grammar that follows the migration refuses it
([`schemas/family`](family.md#definitions)).

## The older form

The four sections that follow describe an architecture blueprint as it is
written before the migration: what `weblisk validate` and the generation
pipeline read today. They are retired, with this paragraph, when the last
file has been migrated.


## Frontmatter

```markdown
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

| # | Section | Heading | Form | Required | Description |
|---|---|---|---|---|---|
| 1 | Frontmatter | `<!-- blueprint -->` | narrative | **Yes** | YAML metadata |
| 2 | Title | `# Name` | narrative | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | narrative | **Yes** | Scope description |
| 4 | Declaration | `## Declaration` | yaml:declaration | Conditional | Everything machine-read, in one block. **Required once migrated** — see `CONTRACT_BLOCK_PLAN.md` |
| 4 | Dependencies | `## Dependencies` | yaml:requires | Conditional | Dependency contracts. **Required unless a `## Declaration` supersedes it** |
| 5 | Architecture | `## Architecture` | narrative | **Yes** | Component diagram and responsibilities |
| 6 | Responsibilities | `## Responsibilities` | narrative | **Yes** | What this component owns and does NOT own |
| 7 | Endpoints | `## Endpoints` | table | Conditional | HTTP surface as a table, with a required `Operation` column. **Required if the component serves any** — see below |
| 8 | Interfaces | `## Interfaces` | narrative | **Yes** | Public API surface (methods, endpoints, events) |
| 9 | Data Flow | `## Data Flow` | narrative | **Yes** | How data moves through this component |
| 10 | Types | `## Types` | yaml:types | Conditional | Data structures in YAML (if component defines types) |
| 11 | Configuration | `## Configuration` | structured | Optional | Component-level configuration |
| 12 | Security | `## Security` | yaml:security | **Yes** | Security posture, trust model, and boundaries |
| 13 | Implementation Notes | `## Implementation Notes` | narrative | **Yes** | Practical guidance |
| 14 | Verification Checklist | `## Verification Checklist` | narrative | **Yes** | Testable assertions (min 5) |

### Optional Sections

| Section | Insert After | When Needed |
|---------|-------------|-------------|
| `## Design Principles` | Data Flow | Numbered decisions the component's shape follows from. Used by most architecture blueprints; place it after Data Flow, as `storage`, `observability` and `threat-model` do |
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

### Endpoints (`## Endpoints`)

The component's HTTP surface, as a **markdown table**. Required for any
component that serves HTTP.

```markdown
## Endpoints

| Method | Path | Operation | Auth | Purpose |
|--------|------|-----------|------|---------|
| POST | /v1/register | Register | no* | Agent registration (identity-verified) |
| GET | /livez | Livez | no | Liveness, for the supervisor that restarts the component |
```

**The table form is load-bearing, not cosmetic.** Generation reads a component's
required endpoints from this section — it does not read the `endpoints:` list in
`## Interfaces`. A blueprint that declares its surface only in the YAML block
states it for a human reader and states nothing to the pipeline, so the plan is
never validated against those endpoints and a component can be generated
complete-looking with an endpoint missing.

Declare endpoints here, and describe them in `## Interfaces` alongside methods
and events if the component's consumers need more than the table carries.

#### `## Declaration` supersedes `## Dependencies`

A blueprint carries one or the other, never both.

Both is two statements of the same dependencies, and the second is free to
drift from the first. It is not a harmless overlap: a declaration is GENERATED
from the section it replaces, so it reproduces that section's faults exactly —
`architecture/orchestrator`'s declaration inherited a `ChannelEntry` binding
sourced from `architecture/storage`, which does not declare it. Fixing one copy
leaves the other wrong, and tooling reads both.

**Remove the superseded section in the same edit that adds the declaration.** A
migration that leaves both has added a surface rather than removed one, which is
the opposite of the point.

`## Endpoints` is NOT superseded. It stays as the human-readable HTTP surface,
alongside the declaration's machine-readable `serves:`; they must agree, and
that agreement is checked.

#### The Operation column

**Required.** `Operation` is the endpoint's name — the identifier every
generated artifact derives its symbols from, per
[Declared Names](common.md#declared-names).

It MUST be `PascalCase`, MUST be unique within the component, and MUST NOT
restate the method or the path. Two rows differing only by method are two
operations and take two names: `POST /v1/register` is `Register` and `DELETE
/v1/register` is `Deregister`.

Without it, a generator has only the path and the prose to work from, and it
will name the same endpoint differently on different runs — `handleRegister`,
then `handleAgentRegister`, then `registerHandler` — making every file that
called the previous name stale. That is not hypothetical: it is why this column
exists.

The platform blueprint states how the operation is spelled in its language; see
`schemas/platform.md`, "The HTTP Surface". The architecture blueprint MUST NOT
name a handler, a constant or a function — those are translations, and
[Platform Neutrality](common.md#platform-neutrality) forbids them here.

#### `provided: platform` — declared, and not generated

**Optional.** An endpoint whose implementation the platform supplies rather
than the model.

The component serves it and a client may rely on it, so it stays in the
declaration and in the endpoint table: removing it would make the blueprint
understate what the hub exposes. What the marker changes is who writes it — a
generator is not asked for it, and no generated file is expected to satisfy it.

Use it only where a generated component cannot implement the endpoint. The
case it exists for is the orchestrator's model routes: they find which model
backends the hub's own host can run, and run a completion through one, which a
generated component cannot do without reproducing the CLI's provider
catalogue. So the CLI installs them.

The marker changes who writes an endpoint, never whether its behaviour is
specified. The blueprint specifies a `provided: platform` endpoint as it does
any other — what it takes, what it answers and what it refuses — and the
platform's code is held to that statement as generated code is. An endpoint
whose behaviour no blueprint states has a contract only in the platform's
code, which its clients cannot read and which can change under them. The
model routes serve the tenant's model, which is the tenant's
([`architecture/orchestrator`](../architecture/orchestrator.md#the-tenants-model)),
so what they do is the orchestrator's to state even though the CLI writes
them.

Without the marker a generator is asked for an endpoint the tooling installs
anyway, and produces a handler that is shadowed at runtime and reached by
nothing — two implementations of one operation, with only one of them wired.

#### A declared endpoint MUST be specified in a required blueprint

If another blueprint documents an endpoint this component serves, the component
MUST list that blueprint in its `requires:`. Declaring the row is not enough:
the row says the endpoint exists, and the other blueprint says how it behaves.

`architecture/orchestrator` declared ten `/v1/admin/operators/*` endpoints and
did not require `architecture/admin`, which specifies the registration flow. The
orchestrator was therefore generated having never been shown that flow. It chose
a signature payload — sensibly, and differently from the client — and the first
real connection failed with `operator signature verification failed`, with
neither side wrong about anything it had been told.

A blueprint that documents paths and has **no `## Endpoints` section of its own**
is specifying a surface for another component to serve. One that has an
`## Endpoints` section is a peer stating what *it* serves: every component
serves `/livez` and `/readyz`, and two components sharing a path is not one specifying the
other.

#### Operations declared outside the endpoint table

A component that declares operations in any other form — a store contract's
operations list, a method table, an event topic table — is declaring names under
the same rule. Those names are binding, the generated artifact MUST use them
exactly, and a component MUST NOT invent a parallel vocabulary for the same
thing.

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

Required for all architecture components. Every component has a security
posture — even components without direct auth responsibilities must
declare their trust assumptions and boundaries:

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
