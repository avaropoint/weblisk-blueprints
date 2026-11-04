---
family: schemas/family@1
version: 1.2.0
kind: specification
noun: language
match: [languages/*.md]
capabilities: [author, versioned, depends, publishable]
generates: none
---
# Language Schema

Defines the complete structure for language blueprints (`type: language`).
A language blueprint says **what is essential when building in one programming
language** — dependency policy, project layout, concurrency, error handling, and
the primitives its standard library does and does not supply.

It says nothing about *what* is being built, and nothing about where it runs.
Those are [`architecture.md`](architecture.md) and [`platform.md`](platform.md).

## Header

The family `schemas/language`, declared for the files `languages/` are written in
today, the older form, which is read as its own family until each file is
rewritten into rules of [`schemas/mapping`](mapping.md) (`file-names-family`).
A file in the older form has no header: its identity is the `<!-- blueprint -->`
comment, which a walk reads as text. A file with a header has been rewritten,
names `schemas/mapping@1`, and is never walked against this family, so a
header here is refused. New files are written to `schemas/mapping`, and this
family has no template.

```yaml
header:
  schema: {type: object, maxProperties: 0}
```

## Sections

```yaml
sections:
  undeclared: {policy: report, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: true, count: {min: 1, max: 1}, use: navigates}
    - {slot: overview, heading: Overview, required: true, use: navigates}
    - {slot: dependencies, heading: Dependencies, required: true, use: depends}
    - {slot: primitives, heading: Primitive Mapping, required: true, use: binds}
    - {slot: project-structure, heading: Project Structure, required: true, use: binds}
    - {slot: domain-structure, heading: "Project Structure: Domain Controller", required: false, use: instructs}
    - {slot: runtime, heading: Runtime Requirements, required: true, use: binds}
    - {slot: build, heading: Build and Run, required: true, use: instructs}
    - {slot: conventions, heading: Language Conventions, required: true, use: instructs}
    - {slot: concurrency, heading: {starts_with: "Concurrency ("}, required: false, use: instructs}
    - {slot: type-mapping, heading: Type Mapping, required: true, use: binds}
    - {slot: storage-mapping, heading: {starts_with: "Storage Mapping ("}, required: false, use: binds}
    - {slot: security, heading: Security, required: true, use: binds}
    - {slot: testing, heading: Testing, required: true, use: instructs}
    - {slot: structure-queries, heading: Structure Queries, required: false, use: binds}
    - {slot: examples, heading: Examples, required: false, use: illustrates}
    - {slot: implementation-notes, heading: Implementation Notes, required: true, use: instructs}
    - {slot: verification, heading: Verification Checklist, required: true, use: verifies}
```

The slots are the [Required Section Order](#required-section-order) below and
its optional sections, in that order: a required section missing is refused,
a section out of order is reported, and a heading outside the set is reported
as undeclared, so each is a counted finding and none is lost.

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
| 6 | Project Structure | `## Project Structure` | yaml:layout | **Yes** | Module and package layout, as [The layout block](#the-layout-block) declares it |
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
| `## Structure Queries` | Testing | The language answers `structure` checks ([The structure block](#the-structure-block)) |
| `## Examples` | Any section | Code examples |

---

## Section Specifications

### Primitive Mapping (`## Primitive Mapping`)

One row per primitive the specification blueprints require, naming what supplies it
**in this language's standard library**, or what must be brought in when it does not.

This is the language's own question, and it is not the platform's. A standard library
either ships a memory-hard key-derivation function or it does not, whatever the code
later runs on.

Which primitives there are is [`schemas/concepts`](concepts.md#concepts)' list
under `identity-primitive/`, and how one is answered, with its package, its source
and the verdict UNFILLED where nothing answers it, is a rule of that class in
[`schemas/mapping`](mapping.md#classes). Neither is restated here; the table a
language file carries today is the form those rules replace.

### Project Structure (`## Project Structure`)

#### The layout block

The section carries one `yaml` block whose root is `layout`. It is how this
language arranges code, stated as data so a generator derives a component's
package plan from it before a model is asked for anything, and validates the
model's plan against it
([`architecture/generation`](../architecture/generation.md#the-plan)). Each
language declares its own. A language file with no `layout` block leaves the
package plan unstated, and a generation for it is refused before any model
call, naming the language, as a concept a mapping leaves UNFILLED is
([`schemas/mapping`](mapping.md#requirements), `unfilled-is-stated`).

```yaml
layout:
  module_root: <path>             # where the module manifest sits, relative to the tenant root
  manifest: <file>                # the module manifest's file name
  name: <spelling>                # how a blueprint's name becomes a package name: as-is | drop-hyphens | snake
  contract:
    package: <path>               # the one package every declared name lives in
    holds: [<kind>, ...]          # which declared names, from the closed list below
  packages:                       # ordered; the first rule whose from matches a blueprint wins
    - from: <type>/{name}         # a blueprint path, {name} its file name
      package: <path>             # where that blueprint's code goes; {name} spelled by name
      role: contract | component | library
      when: component             # optional: the rule matches only a component (below)
  entry: <path>                   # a component's entry file; {service} is the name it registers under
  imports:                        # for each role, what a package of it may import
    entry: [<what>, ...]
    component: [<what>, ...]
    library: [<what>, ...]
    contract: [<what>, ...]
  rules:                          # what belongs in each package, each with an id
    - id: <part id>
      text: <the rule, as a model is given it>
```

| Key | Means |
|---|---|
| `holds` | Declared names of these kinds live in the contract package and nowhere else. The kinds are a closed list: `type` (a `yaml:types` type, with fields or an enum), `enum-constant`, `path-constant`, `request-type`, `response-type` and `error-code`, each spelled as the language's mappings spell it |
| `role` | `contract` is the package `holds` names. `component` is a running thing: the blueprint a row of [`schemas/programme`](programme.md#the-services-in-the-order-they-are-built)'s services table names, for a service in a process of its own, an agent or a domain, and `architecture/gateway`, which [`schemas/config`](config.md) declares as `gateway`. `library` is every other blueprint whose requirements some code answers |
| `imports` | What a package of each role may import: `own-component` (an entry, its own component's package), `library` (any library package), `required-library` (the package of a library blueprint the importer's blueprint `requires`, outside any `requires` cycle with it) and `contract`. Nothing else, and nothing a role's list leaves out |
| `rules` | Binding statements of where code goes, each with an id a plan's validation cites when it refuses a plan. They are passed to the model as written |

**What a layout leaves to the model.** Within a package: which files exist,
what each is called, how the package's work is divided between them, and the
names of what no blueprint declares. No caller observes any of them, and no
blueprint declares them ([`architecture/generation`](../architecture/generation.md#what-the-model-still-decides)).

### Structure Queries (`## Structure Queries`)

#### The structure block

A `structure` check ([`schemas/blocks`](blocks.md#checks)) names a query and
what it must find. The query's text is the language's, because it is a
question about one language's parse tree, so it is declared here, once, and
every blueprint's checks cite it by name. The engine runs it with the parser
the block names and holds no query of its own.

```yaml
structure:
  parser: {grammar: <tree-sitter grammar>, version: "<range>"}
  files: <glob>                  # the source files of the language
  queries:
    <query name>:                # a part id, the name a check cites
      text: <what it finds, in words>
      query: <a tree-sitter query>
      value: <regex>             # optional: one group, applied to each capture's text
```

| Key | Means |
|---|---|
| `parser` | A [tree-sitter](https://tree-sitter.github.io/tree-sitter/using-parsers/queries) grammar and the versions of it the queries are written against. A query language over a grammar is data any engine can run, and it names no Weblisk concept |
| `query` | Captures are read by name. `@value` is a value the query finds; `@exclude` is a value removed from them, by its text; `@unread` is something the query cannot judge, such as a pattern held in a constant, and makes the check unread where it occurs; a capture whose name begins `_` is the query's own. `${name}` is filled from the check's `args` |
| `value` | Applied to each `@value` and `@exclude` capture's text; the first group is the value. The whole text when absent |

A check's `expect` is read over the values: `none` (no `@value`), `some`,
`includes` (every listed value found) or `subset_of` (every value is one the
named query also finds). Its `scope` is the files read: the `component`'s
package, the whole `module`, the `contract` package the layout block names, or
every file `outside-contract`.

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

```yaml
layout:
  module_root: "."
  manifest: <manifest file>
  name: as-is
  contract:
    package: <path>
    holds: [type, enum-constant, path-constant, request-type, response-type, error-code]
  packages:
    - {from: "protocol/{name}", package: <path>, role: contract}
    - {from: "architecture/{name}", package: "<path>/{name}", role: component, when: component}
    - {from: "architecture/{name}", package: "<path>/{name}", role: library}
  entry: "<path>/{service}/<entry file>"
  imports:
    entry: [own-component, library, contract]
    component: [library, contract]
    library: [required-library, contract]
    contract: []
  rules: []
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
