# Skills

Guides for a coding agent working on a Weblisk tenant. They are **not**
specifications.

Blueprints in this repository say what to build and how to verify it. Skills
say how to *read* those blueprints and which CLI verb to run. A skill that
restates a protocol table, an endpoint list, or a checklist is a second copy
of the spec and will drift.

## Rule

One home per fact:

- Behaviour, names, routes, types → the blueprint that declares them
- How to invoke the CLI, what the defaults are, how a blueprint is parsed →
  the skill named for that verb

Do not generate an orchestrator, agent, domain or gateway by hand. Run the
matching `weblisk` command. The command assembles the generation prompt from
the blueprints; the skill does not replace that prompt.

## Catalog

Named after the CLI verb they serve, not after a model.

| Skill | Verb | Points at |
|---|---|---|
| [blueprints](blueprints/SKILL.md) | (every generate) | schemas, declaration blocks |
| [tenants](tenants/SKILL.md) | `weblisk tenant` | `architecture/orchestrator.md` |
| [hubs](hubs/SKILL.md) | `weblisk server` | `architecture/orchestrator.md`, `architecture/hub.md` |
| [agents](agents/SKILL.md) | `weblisk agent` | `architecture/agent.md`, `agents/` |
| [domains](domains/SKILL.md) | `weblisk domain` | `architecture/domain.md` |
| [gateways](gateways/SKILL.md) | `weblisk gateway` | `architecture/gateway.md` |
| [operators](operators/SKILL.md) | `weblisk operator` | `architecture/admin.md`, `protocol/identity.md` |
| [go](go/SKILL.md) | `--platform go` | `platforms/go.md` |

The CLI installs the skills for the verb it is running, plus `blueprints`, plus
the platform skill when one exists. Content is the same for every model. The
CLI writes `.agents/skills/` (vendor-neutral) and the generating tool's native
path (`.claude/skills/` or `.grok/skills/`).

## Authoring

Each skill is `skills/<name>/SKILL.md` with YAML frontmatter:

```markdown
---
name: <name>
description: One line. Include "Use when …" so a coding agent loads it.
---
```

`name` MUST match the directory. Keep the body short. Point at the blueprint
and the command. If a fact is already in a blueprint, link it; do not copy it.
