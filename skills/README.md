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
| [changes](changes/SKILL.md) | `weblisk component`, `weblisk test` | `architecture/generation.md`, `architecture/testing.md` |
| [kinds](kinds/SKILL.md) | (every tool that classifies or relates) | `schemas/kinds.md` |
| [go](go/SKILL.md) | `--platform go` | `platforms/go.md` |
| [node](node/SKILL.md) | `--platform node` | `platforms/node.md` |
| [rust](rust/SKILL.md) | `--platform rust` | `platforms/rust.md` |
| [cloudflare](cloudflare/SKILL.md) | `--platform cloudflare` | `platforms/cloudflare.md` |

The CLI installs the skills for the verb it is running, plus `blueprints`, plus
the skill for the platform it is generating for. Every platform the corpus
specifies has one, and a platform with a blueprint and no skill is a failure
rather than a quiet omission. Content is the same for every model. The CLI
writes `.agents/skills/` (vendor-neutral) and the generating tool's native path
(`.claude/skills/` or `.grok/skills/`).

A tenant is changed far more often than it is created, so `changes` rides with
`tenant` as well as with the verbs that change one — skills travel with the
tenant, and every tenant is eventually rebuilt.

**These files are embedded into the CLI** at `internal/dispatch/skills/`, so a
tenant can be generated without this corpus present. That is two copies of one
file. `TestTheEmbeddedSkillsMatchTheBlueprintCorpus` fails when they differ, and
reports rather than skips when this repository is not checked out beside the
CLI. Author here; copy the file over.

## These are builder's skills, and that is now said out loud

Every skill in the table is for somebody **building the platform**: which CLI
verb to run, how to read a blueprint, what a platform binding provides. Not one
is for a person doing a job **inside a tenant** — the supervisors, coordinators
and officers the programmes are written for.

That second audience is served from [`../positions/`](../positions/README.md)
and is **derived**, not authored: what a programme expects of a position is
already declared in every obligation's `responsible`, every `escalate.to`, every
register's `approvers` and every artifact's `approved_by`, and a hand-written
role skill would be a second copy of it.

It is deliberately **not** a directory in here. A skill in this family is named
for a verb, is installed by the CLI when that verb runs, and is embedded in the
CLI byte-for-byte — a contract a generated file cannot keep. Feeding machine
output to a byte-for-byte guard makes its red light mean *"you forgot to run the
generator"* instead of *"two copies disagree"*, which is the one thing that
guard exists to say.

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
