# Weblisk Blueprint Schema

Every blueprint in this repository follows a standard structure. This ensures
that any tool, CLI, or AI model can reliably parse, validate, and build from
any blueprint — regardless of the blueprint's domain or purpose.

## Blueprint Types

| Type | Purpose | Directory |
|------|---------|-----------|
| `protocol` | Wire protocol specifications, security, types | `protocol/` |
| `architecture` | System architecture patterns (orchestrator, domain, agent, lifecycle) | `architecture/` |
| `platform` | Implementation guidance for a specific runtime | `platforms/` |
| `domain` | Domain controller specifications — workflow, agent dispatch, aggregation | `domains/` |
| `pattern` | Declarative API pattern specifications (REST, auth, webhooks, etc.) | `patterns/` |
| `agent` | Work agents and infrastructure service definitions | `agents/` |

### Agent Kinds

Agent blueprints use an additional `kind` metadata field:

| Kind | Purpose | Example |
|------|---------|---------|
| `domain` | Business-function controller — dispatches work to agents | `domains/seo.md` |
| `work` | Performs a specific task under a domain's direction | `agents/seo-analyzer.md` |
| `infrastructure` | System utility — runs independently of any domain | `agents/sync.md` |

## Required Sections

Every blueprint MUST include these sections as top-level `##` headings:

### 1. Header Block

The first lines of every blueprint MUST be a YAML-style metadata block
inside an HTML comment, followed by a `#` title and overview paragraph.

```markdown
<!-- blueprint
type: domain | protocol | architecture | platform | pattern | agent
kind: domain | work | infrastructure (agent type only)
name: seo
version: 1.0.0
requires: [protocol/spec, protocol/identity, architecture/agent]
platform: any | go | cloudflare | node | rust
-->

# SEO Domain Controller

One-paragraph overview of what this blueprint defines and why it exists.
```

**Fields:**
- `type` (required): One of `protocol`, `architecture`, `platform`, `domain`, `pattern`, `agent`
- `kind` (optional): Agent kind — `domain`, `work`, or `infrastructure` (only for `type: agent` or `type: domain`)
- `name` (required): Unique identifier (lowercase, hyphen-separated)
- `version` (required): Semver version of the blueprint
- `requires` (required): List of other blueprints this one depends on
- `platform` (optional): Which platform this applies to (`any` = all)

### 2. Overview (`## Overview`)

A concise description (2-5 sentences) of what this blueprint covers.
Must be self-contained — a reader should understand the scope without
reading other blueprints.

### 3. Specification (`## Specification`)

The normative content. For each blueprint type:

- **Protocol**: Endpoints, request/response schemas, error codes, auth rules
- **Architecture**: Component responsibilities, startup sequence, data flow
- **Platform**: Runtime requirements, project structure, build commands
- **Domain**: Workflows, required agents, dispatch rules, aggregation, feedback
- **Pattern**: Blueprint format, endpoints, request/response shapes, types
- **Agent**: Capabilities, triggers, execute workflow, message handlers, validation

Use RFC 2119 language (MUST, SHOULD, MAY) for requirements.

### 4. Types (`## Types`)

All data structures referenced in this blueprint. Use language-agnostic
JSON schema notation:

```markdown
### TypeName
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Human-readable name |
| url | string | yes | HTTP endpoint URL |
```

For blueprints that don't define new types, reference the canonical types:
`See: protocol/types.md`

### 5. Implementation Notes (`## Implementation Notes`)

Practical guidance for implementing this blueprint:
- Common pitfalls and how to avoid them
- Performance considerations
- Security requirements
- Testing approach

### 6. Verification Checklist (`## Verification Checklist`)

A concrete list of checks that MUST pass for an implementation to be
considered compliant:

```markdown
- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] Registration signature is verified against manifest.public_key
- [ ] Token expiry is checked on every verification
```

## Optional Sections

These sections MAY be included when relevant:

- `## Examples` — Complete request/response examples
- `## Collaboration` — How this component interacts with others
- `## Configuration` — Environment variables, flags, config files
- `## Error Handling` — Error codes, retry strategies, fallback behavior

## Referencing Other Blueprints

Use relative paths in the `requires` field and inline references:

```markdown
See [Protocol Specification](../protocol/spec.md) for endpoint details.
See [Identity Specification](../protocol/identity.md) for signing flow.
```

## Versioning

- Blueprints follow semver: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking protocol changes (new required endpoints, changed auth)
- MINOR: New optional capabilities, expanded domain knowledge
- PATCH: Clarifications, typo fixes, additional examples
- All blueprints in a release MUST be compatible with each other

## Creating a New Blueprint

1. Choose the correct type and directory
2. Copy this template structure
3. Fill in the metadata block with correct `requires` references
4. Write the specification using RFC 2119 language
5. Define all types in language-agnostic notation
6. Add a verification checklist with concrete, testable items
7. Ensure the blueprint is detailed enough for "one-shot" implementation —
   an AI model or developer should be able to build a compliant implementation
   from the blueprint alone, without needing to ask follow-up questions
