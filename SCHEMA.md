# Weblisk Blueprint Schema

> **This file is the entry point.** It says what the schema system is and where each
> part of it lives. It states no rule of its own — every rule belongs to the schema
> that owns it, and a copy here would be a second statement free to drift from the
> first.

## What the schema system is

The governance layer of the framework. Every agent, protocol, pattern, architecture
component, platform binding and domain controller is written to a declared shape, so
that a generator can produce one and an auditor can check one from the same document.

> **Nothing operates in the Weblisk framework without a schema-compliant blueprint.
> If a schema doesn't define it, the framework doesn't allow it.**

## Where to go

| If you are | Read |
|---|---|
| Writing a blueprint | [`schemas/authoring.md`](schemas/authoring.md) — the one page to read first |
| Looking for the schema of a type | [`schemas/README.md`](schemas/README.md) — every schema, what it governs, and where it applies |
| Checking what types exist | [`schemas/common.md`](schemas/common.md#type-registry) — the Type Registry |
| Checking a compliance level | [`schemas/compliance.md`](schemas/compliance.md) |
| Classifying content at runtime | [`schemas/kinds.md`](schemas/kinds.md) |

## Before committing

```
weblisk validate
```

It reads every schema, derives the rules from them, and reports what disagrees. A
finding names the schema that states the rule, so a disagreement is traceable to a
document rather than to tooling.
