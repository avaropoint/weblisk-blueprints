---
name: domains
description: Create and start a Weblisk domain controller with the CLI. Use when adding a domain to a tenant, or when asked how domain logic is generated.
---

# Domains

What a domain controller must do is `architecture/domain.md`. This skill is
the command.

## Default

```
weblisk domain create billing
```

Platform defaults to `go`.

## Override

```
weblisk domain create billing --platform go
weblisk domain start billing
```

There is no `--from marketplace`; a domain built from someone else's
blueprints is a change, `weblisk change plan --adopt <ref>`.

Do not write a domain controller by hand. The command reads the domain
blueprint (and `architecture/domain.md`) and assembles the prompt.
