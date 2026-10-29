# Weblisk Blueprint Schema System

Every blueprint in the Weblisk framework MUST conform to a schema definition
before it can be registered, consumed, or trusted by other components. There
are no exceptions. If a schema does not exist for a capability, that capability
does not exist in the framework.

This directory contains the authoritative schema definitions for every
blueprint type. Together they form the **governance layer** of the platform —
the contract that ensures every agent, protocol, pattern, architecture,
language or platform binding, and domain controller is built to a verifiable
standard.

## Why Strict Schemas

1. **Trust** — Agents interact with each other and with user data. Every
   capability must be declared, every boundary enforced, every deviation
   flagged. Without strict schemas, a single malformed agent can compromise
   the integrity of every other component it touches.

2. **Security** — Agents cannot acquire capabilities beyond what their
   blueprint declares. The schema defines the security boundary. An agent
   that doesn't declare `database:write` cannot write to storage. An agent
   that doesn't declare event subscriptions cannot receive events. The
   orchestrator enforces this at registration.

3. **Repeatability** — Every blueprint is machine-parseable. Tools, CLIs,
   CI pipelines, and AI models can validate, generate, and audit blueprints
   automatically. Human review is a complement, not a prerequisite.

4. **Interoperability** — When every blueprint follows the same structure,
   agents from different authors, organizations, and platforms can interoperate
   without custom integration work.

5. **Compliance** — The compliance framework (see [compliance.md](compliance.md))
   assigns a compliance level to every blueprint. Non-compliant blueprints
   are flagged, restricted, or rejected depending on severity. This protects
   the ecosystem from agents that could violate security, privacy, or
   operational boundaries.

## Foundational Rule

> **Nothing operates in the Weblisk framework without a schema-compliant
> blueprint. If a schema doesn't define it, the framework doesn't allow it.**

This applies to:
- Agent capabilities and permissions
- Event namespaces and subscriptions
- Storage tables and data access
- API endpoints and message handlers
- Workflow definitions and dispatch rules
- Configuration parameters and environment variables
- Inter-agent communication patterns

## Schema Files

Each schema below that opens with `family: schemas/family@1` is a family
declaration ([family.md](family.md)): its Header and Sections blocks are the
shape a walk holds a file to, and its prose stays as the reason. The
protocol, pattern, agent and domain declarations, like architecture's, state
the form a file takes once it is migrated; the position, policy-domain and
programme ones walk today's files in migration mode; the language, platform
and framework ones declare the older form their files keep until each is
rewritten into [mapping](mapping.md) rules; kinds and standard are
declarations with no `kind`, which no file is walked against.

| Schema | Governs | Applies To |
|--------|---------|------------|
| [authoring.md](authoring.md) | The order of work when writing a blueprint, and which document owns each rule | Every author |
| [common.md](common.md) | Shared rules inherited by all blueprint types | Every blueprint |
| [compliance.md](compliance.md) | Compliance levels, validation, enforcement, security boundaries | Every blueprint |
| [config.md](config.md) | Hub configuration file (`.weblisk/config.yaml`) | Every project |
| [agent.md](agent.md) | Infrastructure agent blueprints | `agents/` directory |
| [domain.md](domain.md) | Domain **controller** blueprints — an agent process owning a business function. **Not** a policy domain; see [policy-domain.md](policy-domain.md) | Domain YAML specs in project `domains/` |
| [protocol.md](protocol.md) | Wire protocol specifications | `protocol/` directory |
| [pattern.md](pattern.md) | Cross-cutting patterns | `patterns/` directory |
| [architecture.md](architecture.md) | System architecture components. The declaration of the family `schemas/architecture` (grammar 1), whose starting file is [`templates/architecture.md`](../templates/architecture.md), and the older form today's files are written in until they are migrated | `architecture/` directory |
| [language.md](language.md) | Programming language bindings — what is essential when building in one language | `languages/` directory |
| [platform.md](platform.md) | Platform implementation bindings — what a runtime offers | `platforms/` directory |
| [framework.md](framework.md) | Framework blueprints — what building *with* a framework requires | `frameworks/<name>/` directories |
| [standard.md](standard.md) | Industry standards — ISO, SOC 2, NIST, CSA — as JSON, and how a tenant adopts one: generated as a link and its own adjustments, never copied | `standards/` directory |
| [programme.md](programme.md) | Programmes — which artifacts a body of work requires, what each answers, the recurring work it commits an organisation to, what else adopting it brings, and what an adoption records | `programmes/` directory |
| [programme-map.md](programme-map.md), [programme-spec.md](programme-spec.md), [programme-template.md](programme-template.md) | The declarations of the three programme file families (grammar 1), in migration mode; their strict variants are in [strict/](strict/), applied once the files are migrated. What each field means stays in [programme.md](programme.md) | `programmes/*/map.md`, `programmes/*/specs/`, `programmes/*/templates/` |
| [position.md](position.md) | Positions — the hand-written judgement a role brief cannot derive | `positions/` directory |
| [policy-domain.md](policy-domain.md) | Policy domains — what a subject area covers, where it stops, and what a programme claiming it must provide | `policy-domains/` directory |
| [kinds.md](kinds.md) | What sorts of thing the platform can talk about, what each drives, and which relations join them | Every tool that classifies, relates or scores content |
| [names.md](names.md) | How anything is named: the id grammar, families, namespaces and how a short ref resolves. Its vectors are [`vectors/ids.json`](../vectors/ids.json) | Every ref, in every file and every tool |
| [family.md](family.md) | Grammar 1: how a family declaration says a file is written — header, slots, blocks, what each part is for — and the projection a walk of a file produces. It is itself a declaration, and validates against itself. Its vectors are [`vectors/grammar/`](../vectors/grammar/README.md) | Every family declaration, and every file walked against one |
| [blocks.md](blocks.md) | The block catalogue: every typed block a slot may hold, by root key, and the closed vocabulary a declared type's fields are written in | Every typed block in a file walked by grammar 1 |
| [mapping.md](mapping.md) | Mappings: how a neutral blueprint becomes something on one target, as rules on four axes (language, platform, framework, interface), the closed concept classes each axis owns, the one verdict vocabulary, a coverage report, and `subject_facility`. Its vectors are [`vectors/mapping/`](../vectors/mapping/README.md) and [`vectors/types.json`](../vectors/types.json) | Every language, platform, framework and interface binding, once it is written as rules |
| [concepts.md](concepts.md) | The concepts a mapping rule answers, by class: open data beside the closed classes | Every mapping rule, and every blueprint a mapping translates |
| [run-statement.md](run-statement.md) | What one generation run read and wrote, the model the backend reported, and what each output traces to: an in-toto statement with a SLSA Provenance predicate | The CLI writing a run's record; the fabric's `generation-statements` producer reading it |
| [change.md](change.md) | One change to what a tenant is built from: its plan and verdicts, the conflicts it introduces and clears, its approval, the executor of each change verb, and when one is well formed. Its vectors are [`vectors/change/`](../vectors/change/README.md) | The CLI and the tenant's change service writing a change; every client rendering one |
| [build-lock.md](build-lock.md) | The tenant's one lock: resolved versions only, never roots or reasons. Its vectors are [`vectors/change/`](../vectors/change/README.md) | The change service writing `.weblisk/build.lock`; every plan reading it |
| [resource.md](resource.md) | What a tenant holds or runs that a person may see and operate: the Resources block an owner's blueprint declares each kind in — fields, operations, verbs, authority, states, events, relations — and when one is well formed. Its vectors are [`vectors/resources/`](../vectors/resources/README.md) | Every component a person operates; the admin gateway, the CLI and every console reading the catalogue |

### kinds.md is different from the others

The schemas above describe **how a blueprint is written**. `kinds.md` describes
**what sorts of thing exist** — content, criteria, systems, executions — and what
each may be used for.

It is read at runtime by tools rather than checked against a document, and it is
**data, not code**: kinds are declared here and extended freely, while
*capabilities* are a closed set because each one is a contract with an
implementation. A tool that hard-codes a kind, a chain layer or a relation has
moved the specification out of the blueprints — the same fault
[common.md](common.md#adoption) names for adoption.

## Schema Hierarchy

```
common.md (inherited by all)
├── compliance.md (enforcement layer — applies to all)
├── config.md (hub configuration — .weblisk/config.yaml)
├── agent.md (type: agent)
├── domain.md (type: domain)
├── protocol.md (type: protocol)
├── pattern.md (type: pattern)
├── architecture.md (type: architecture)
├── language.md (type: language — languages/)
├── platform.md (type: platform — platforms/)
├── framework.md (frameworks/<name>/ — building WITH a framework)
├── standard.md (standards/ — industry standards, as JSON)
├── programme.md (programmes/ — programme maps and artifact specifications)
│   ├── programme-map.md, programme-spec.md, programme-template.md (their file families)
│   └── strict/ (the strict variants, applied after the migration)
├── position.md (positions/ — the hand-written half of a role brief)
├── policy-domain.md (policy-domains/ — what a subject area covers and requires)
├── kinds.md (what sorts of thing exist — read at runtime, not checked against a document)
├── names.md (how anything is named — the id grammar, bound by vectors/ids.json)
├── family.md (grammar 1 — how a family declaration says a file is written, bound by vectors/grammar/)
├── blocks.md (the typed blocks a slot may hold, and the field type vocabulary)
├── run-statement.md (what one generation run read, wrote and traced — the fabric's declared source)
├── change.md (one change to what a tenant is built from — plan, approval, executors, bound by vectors/change/)
├── build-lock.md (the tenant's resolved versions, and nothing else)
└── resource.md (what a person may see and operate of a tenant — declared by each owner, bound by vectors/resources/)
```

Every type-specific schema inherits all rules from `common.md`. Type-specific
schemas add required sections, field constraints, and validation rules that
are unique to that blueprint type.

## How Schemas Are Used

### 1. Blueprint Authoring
Authors use the type-specific schema as a template. Every required section
is present, every field is populated, every YAML block follows the declared
structure. The schema is the specification — the blueprint is the instance.

### 2. Validation (Pre-Registration)
Before a blueprint is registered with the orchestrator, it passes through
schema validation:
- Frontmatter fields are present and correctly typed
- All required sections exist with correct `##` headings
- YAML blocks parse and conform to field-level constraints
- Dependency references resolve to real blueprints
- Version ranges are valid semver expressions
- Security declarations are complete (capabilities, access control)
- Compliance level is computed and recorded

### 3. Runtime Enforcement
The orchestrator uses the validated blueprint as the agent's contract:
- Registration is rejected if the blueprint is non-compliant at level `rejected`
- Capabilities declared in the blueprint are the ONLY capabilities granted
- Event subscriptions are limited to declared topics
- Storage access is limited to declared tables
- Inter-agent messaging is limited to declared collaborators

### 4. Continuous Compliance
Running agents are periodically audited against their blueprint:
- Lease renewals must carry the readiness and checks declared in the blueprint
- Event publishing must stay within declared event namespaces
- Resource usage must stay within declared constraints
- Violations are logged, flagged, and escalated per compliance rules

## Creating a New Blueprint

1. Identify the blueprint type (`agent`, `domain`, `protocol`, `pattern`,
   `architecture`, `language`, `platform`)
2. Open the corresponding schema file in `schemas/`
3. Copy the **Complete Template** section from that schema
4. Fill in every required section — do not skip or stub out sections
5. Validate against the schema rules (field types, constraints, references)
6. Run the compliance checklist from [compliance.md](compliance.md)
7. Ensure the blueprint is detailed enough for "one-shot" implementation —
   a developer or AI model should build a compliant implementation from the
   blueprint alone, without follow-up questions

## Extending the Schema System

To add a new blueprint type:
1. Create a new schema file in `schemas/`
2. Inherit from `common.md` — declare which common sections apply
3. Define type-specific required and optional sections
4. Define all YAML block structures with field-level constraints
5. Add a compliance mapping (which compliance rules apply)
6. Add the type to the `common.md` type registry
7. Add the type to this README's schema table
8. Add the corresponding directory to the repository root

No blueprint type may exist without a schema definition. No schema may
exist without being registered in this index.

## Version

```
schema-system: 1.0.0
last-updated: 2026-04-26
```
