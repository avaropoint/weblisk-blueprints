---
name: blueprints
description: How to read a Weblisk blueprint — declaration blocks, section forms, and which sentences bind. Use when generating or editing a tenant, adding a component, or deciding whether code matches its specification.
---

# Blueprints

Blueprints are the specification. Generated code is one conformant
implementation. When the two disagree, the blueprint is right.

This skill is how to *read* them. It does not restate what they require.

## Where they resolve

First hit wins:

1. `blueprints/` in this tenant
2. `WL_BLUEPRINT_SOURCES`
3. the shared cache, `~/.weblisk/blueprints`

`weblisk doctor` names which copy a build will read. `weblisk validate`
checks this tenant against whatever resolved.

Read the blueprint **in full** before writing. Every section constrains the
others.

## Declaration block

A migrated blueprint carries one `declaration:` block:

| Key | Means |
|---|---|
| `requires` | blueprints this one is derived from — read those too |
| `declares` | names this blueprint OWNS. Nothing else may define them |
| `serves` | operations this component must expose |
| `checks` | expectations, each with an explicit subject |

A blueprint carries `## Declaration` **or** `## Dependencies`, never both. If
both exist, the file is mid-migration and the declaration wins.

A name in `declares` is used exactly as written. Do not invent a synonym.

## How a section binds

Each schema's Required Section Order table gives every section a form. The
form is the contract:

- A fenced yaml block with a root key **is the contract**. Every key is
  required output.
- A markdown table **is the contract**. Every row binds; columns are read by
  **header name**.
- Prose is context, except: a sentence containing MUST, MUST NOT or SHALL is
  binding wherever it appears.

A fenced block with no root key, in a section whose contract is a rooted
block, is an example. A path inside a narrative example is illustrative
unless a table or yaml block also declares it.

Where two blueprints disagree, the more specific wins. If neither is more
specific, say so — do not choose.

The `## Verification Checklist` is one assertion per line. Identifiers must
be in backticks or the check is silently disabled.

## Do not

- Restate a rule another blueprint already states
- Put a storage mechanism in a specification
- Fill a gap by inference; a missing name is a blueprint fault

The generator assembles its prompt from these files. Do not replace that
prompt with a hand-written one.
