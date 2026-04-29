# Weblisk Blueprint Schema System

Every blueprint in the Weblisk framework MUST conform to a schema definition
before it can be registered, consumed, or trusted by other components. There
are no exceptions. If a schema does not exist for a capability, that capability
does not exist in the framework.

This directory contains the authoritative schema definitions for every
blueprint type. Together they form the **governance layer** of the platform —
the contract that ensures every agent, protocol, pattern, architecture,
platform binding, and domain controller is built to a verifiable standard.

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

| Schema | Governs | Applies To |
|--------|---------|------------|
| [common.md](common.md) | Shared rules inherited by all blueprint types | Every blueprint |
| [compliance.md](compliance.md) | Compliance levels, validation, enforcement, security boundaries | Every blueprint |
| [config.md](config.md) | Hub configuration file (`.weblisk/config.yaml`) | Every project |
| [agent.md](agent.md) | Infrastructure agent blueprints | `agents/` directory |
| [domain.md](domain.md) | Domain controller blueprints | Domain YAML specs in project `domains/` |
| [protocol.md](protocol.md) | Wire protocol specifications | `protocol/` directory |
| [pattern.md](pattern.md) | Cross-cutting patterns | `patterns/` directory |
| [architecture.md](architecture.md) | System architecture components | `architecture/` directory |
| [platform.md](platform.md) | Platform implementation bindings | `platforms/` directory |

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
└── platform.md (type: platform)
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
- Health endpoints must report the structure declared in the blueprint
- Event publishing must stay within declared namespaces
- Resource usage must stay within declared constraints
- Violations are logged, flagged, and escalated per compliance rules

## Creating a New Blueprint

1. Identify the blueprint type (`agent`, `domain`, `protocol`, `pattern`,
   `architecture`, `platform`)
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
