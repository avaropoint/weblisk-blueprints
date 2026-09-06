# Authoring a Blueprint

> The one page to read before writing a blueprint — inside this repository or
> in a tenant's own. It states the order of work and points at the document
> that owns each rule. **It restates none of them**, because a rule copied into
> a second place is a rule that will disagree with itself.

---

## What a blueprint is

A specification a generator turns into code, and an auditor reads to know what
that code owes. Both readings must work from the same document, so a blueprint
is written to be **read by a parser and by a person at once** — never one at
the expense of the other.

Three consequences follow, and they are the whole of the discipline:

1. **Structure is never prose.** Prose is the only form that cannot be checked:
   a paragraph omitting half a contract reads exactly like one that does not.
2. **A name is declared, never inferred.** What a generator cannot find, it
   invents — and it invents differently next time.
3. **A requirement lives in exactly one blueprint.** Two statements are two
   rules the moment one is edited.

---

## Before writing

| Step | Do | Owner of the rule |
|---|---|---|
| 1 | Decide the **type** — `agent`, `domain`, `protocol`, `pattern`, `architecture`, `platform` | [`common`](common.md#frontmatter) |
| 2 | Read `schemas/<type>.md` **in full**, especially its Required Section Order | that schema |
| 3 | Check no existing blueprint already owns the subject | [`common`](common.md#declared-names) |
| 4 | Copy the section order exactly — every Required section, in that order | that schema |

Step 2 is the one that gets skipped, and skipping it is the origin of most
faults this repository has recorded. A schema is not a checklist to consult
afterwards; it is the shape of the document you are about to write.

---

## While writing

### The form of each section is declared, not chosen

Each schema's Required Section Order table carries a **`Form`** column —
`narrative`, `table`, `yaml`, `yaml:<root>` or `structured`. Write the section
in the form its schema declares. The forms and the rule for choosing between
them when a schema does not say are in
[`common` → Section Form](common.md#section-form).

### Name everything you declare

Endpoints carry an `Operation`, types carry their exact spelling, store
operations carry theirs. A platform blueprint spells a declared name in its
language and never invents one. See
[`common` → Declared Names](common.md#declared-names).

### Say MUST when you mean it

A sentence containing MUST, MUST NOT or SHALL is binding wherever it appears —
including in a narrative section. Write one only where the requirement is real,
and write the requirement once. See
[`architecture/generation` → How a blueprint is read](../architecture/generation.md#how-a-blueprint-is-read)
for how a generator is told to treat them.

### Reference; do not restate

If another blueprint already states a rule, link to it. If two blueprints need
the same rule, the one that **owns the subject** states it. The validator
enforces this as "one requirement, one blueprint".

### Every declared surface has a server

An endpoint declared in a pattern or the protocol is served by some component's
`## Endpoints` table, or the blueprint declares `adoption: opt-in` because the
surface is reached only when configured. See
[`common` → `adoption`](common.md#adoption).

---

## Before committing

```
weblisk validate
```

It reads every schema, derives the rules from them, and reports what
disagrees — required sections, section form, declared names, unserved
surfaces, restated rules. A finding names the schema that states the rule, so a
disagreement is traceable to a document rather than to tooling.

**A finding is a fault in the blueprint until proven otherwise.** Where the
validator is genuinely wrong, the fix is in the validator or the schema — never
a change to the blueprint that makes a real problem invisible.

---

## Authoring outside this repository

A tenant's own blueprints are the tenant's. Everything above still applies,
with two differences:

- **Resolution order.** A project's `blueprints/` directory is searched before
  the core corpus, so a tenant may override a core blueprint by name. An
  override is a *replacement*, not a patch — it states the whole document.
- **The core corpus is not editable in place.** A change wanted in a core
  blueprint is a change to this repository. Copying one into a tenant to edit
  it creates a fork that no longer receives corrections.

Run `weblisk validate` from the tenant. It resolves both sources and validates
what the tenant will actually build from.

---

## What this page deliberately does not contain

The rules themselves. Every one lives in the schema or blueprint that owns it,
and this page links there.

That is not a stylistic preference. A summary of a rule is a second statement
of it, and the summary is the copy that goes stale — which is precisely the
failure mode this page exists to help authors avoid.
