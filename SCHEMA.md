# Weblisk Blueprint Schema

> **This file is the entry point.** The complete schema system lives in the
> [`schemas/`](schemas/) directory. Every blueprint type has a dedicated
> schema definition with exact section specifications, field constraints,
> YAML block formats, and a copy-paste template.

## Schema System

The Weblisk schema system is the governance layer of the platform. It ensures
that every agent, protocol, pattern, architecture, platform, and domain
controller is built to a verifiable standard. Nothing operates in the
framework without a schema-compliant blueprint.

### Schema Files

| Schema | Governs | Applies To |
|--------|---------|------------|
| [schemas/common.md](schemas/common.md) | Shared rules inherited by all types | Every blueprint |
| [schemas/compliance.md](schemas/compliance.md) | Compliance levels, validation, enforcement, security boundaries | Every blueprint |
| [schemas/agent.md](schemas/agent.md) | Infrastructure agent blueprints (22 required sections) | `agents/` |
| [schemas/domain.md](schemas/domain.md) | Domain controller blueprints (27 sections) | Domain YAML specs in project `domains/` |
| [schemas/protocol.md](schemas/protocol.md) | Wire protocol specifications | `protocol/` |
| [schemas/pattern.md](schemas/pattern.md) | Cross-cutting pattern contracts | `patterns/` |
| [schemas/architecture.md](schemas/architecture.md) | System architecture components | `architecture/` |
| [schemas/platform.md](schemas/platform.md) | Platform implementation bindings | `platforms/` |

### Foundational Rule

> **Nothing operates in the Weblisk framework without a schema-compliant
> blueprint. If a schema doesn't define it, the framework doesn't allow it.**

### Compliance Levels

Every blueprint is validated and assigned a compliance level:

| Level | Status | Can Register | Can Publish | Can Be Consumed |
|-------|--------|:------------:|:-----------:|:---------------:|
| **Certified** | Fully compliant | ✅ Full | ✅ | ✅ |
| **Compliant** | Minor issues | ✅ Full | ❌ | ✅ |
| **Restricted** | Validation errors | ✅ Limited | ❌ | ❌ |
| **Non-Compliant** | Missing sections | ✅ Sandbox | ❌ | ❌ |
| **Rejected** | Security failures | ❌ | ❌ | ❌ |

See [schemas/compliance.md](schemas/compliance.md) for the full validation
pipeline, enforcement points, and security boundary model.

### Blueprint Types

| Type | Kind | Schema | Directory |
|------|------|--------|-----------|
| `agent` | `infrastructure`, `work`, `domain` | [schemas/agent.md](schemas/agent.md) | `agents/` |
| `domain` | `domain` | [schemas/domain.md](schemas/domain.md) | Domain YAML specs in project `domains/` |
| `protocol` | — | [schemas/protocol.md](schemas/protocol.md) | `protocol/` |
| `pattern` | — | [schemas/pattern.md](schemas/pattern.md) | `patterns/` |
| `architecture` | — | [schemas/architecture.md](schemas/architecture.md) | `architecture/` |
| `platform` | — | [schemas/platform.md](schemas/platform.md) | `platforms/` |

### Creating a New Blueprint

1. Identify the blueprint type
2. Open the corresponding schema file in `schemas/`
3. Copy the **Complete Template** section from that schema
4. Fill in every required section (do not skip or stub)
5. Validate against [schemas/common.md](schemas/common.md) shared rules
6. Run the compliance checklist from [schemas/compliance.md](schemas/compliance.md)
7. Ensure the blueprint is implementable from the document alone

See [schemas/README.md](schemas/README.md) for the full schema system
documentation.
