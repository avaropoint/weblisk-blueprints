# Document families

The families an organisation's own documents are written to: what headings a
policy, a procedure, a standard or a guideline is expected to carry, and what
belongs under each. Each file here is a family declaration
([`schemas/family`](../../schemas/family.md)), so a document of one walks as
any other file does, and a missing section is a finding with the slot's
`guidance` beside it, which is also the brief a model is handed to fill it.

| Family | Declaration | Starts from |
|---|---|---|
| `documents/families/policy` | [`policy.md`](policy.md) | [`templates/policy.md`](../../templates/policy.md) |
| `documents/families/procedure` | [`procedure.md`](procedure.md) | [`templates/procedure.md`](../../templates/procedure.md) |
| `documents/families/standard` | [`standard.md`](standard.md) | [`templates/standard.md`](../../templates/standard.md) |
| `documents/families/guideline` | [`guideline.md`](guideline.md) | [`templates/guideline.md`](../../templates/guideline.md) |

They were the structures under `schemas/structures/`, and each section of a
structure is a slot here: its title the slot's heading, its aliases the
slot's aliases, its guidance the slot's `guidance`. A section that made a
document incomplete when missing is `required: report`, because a document
without it is incomplete, not unreadable: the walk reports it and refuses
nothing.

## Rules

- **They cite no standard.** They are conventions of document writing, not
  obligations, and a framework clause written into them would be standards
  content resident in a file no adoption chose. A slot's `authority` is how a
  tenant says a section is required by something it *has* adopted, and no slot
  here carries one.
- **No heading opens two slots.** A heading or alias equal to another slot's
  heading or alias, ignoring case, would let one heading satisfy two sections,
  and the walk could not say which was missing.
- **A family declares no path.** It has no `match`: a document is walked
  against a family by the resolution below, never by where it sits, because a
  second list of folder names beside the classification stems in
  [`schemas/kinds`](../../schemas/kinds.md#stems) would drift from them.

## Which family a document is walked against

First match wins:

1. the `family:` in the document's own header;
2. the `structure:` in the document's own header, which a form's
   `frontmatter:` block writes
   ([`schemas/programme`](../../schemas/programme.md#a-forms-frontmatter)), as
   the family `documents/families/<structure>`;
3. the `structure` of the spec that created it
   ([`schemas/programme-spec`](../../schemas/programme-spec.md));
4. for a document no form or spec created, its kind as
   [`schemas/kinds`](../../schemas/kinds.md) classifies it, resolved through
   `specializes`: the family whose name is the kind, else the one whose name is
   the kind it specializes, and so on up the chain. `document` is never
   reached this way — it means unclassified, and an unclassified document is
   not walked as anything. So an `sop`, runbook or playbook with no family of
   its own is walked as a `procedure`, while a `reference` is not walked.

A document whose resolution ends without a family has **no check**, and says
so; it is never reported as complete.

**Only an organisation's own documents fall back by kind.** Step 4 applies to
what a tenant authors. Published content has no such check: an industry
standard delivered and adopted as [`schemas/standard`](../../schemas/standard.md)
declares, and any file of this corpus read as a source. `schemas/kinds`
classifies the `standards` and `schemas` segments as `standard`, so without
this rule every adopted standard and every schema file would be reported as an
organisation standard lacking Overview and Requirements: a gap in a document
nobody in the organisation writes. A published file is reported as not
checked, never as incomplete.

## Whose copy is walked

These files are published content: **delivered into a tenant**, where the
content service holds them under the tenant's namespace with `extends` set to
the published declaration's digest (`adopt: {mode: copy, record: extends}`),
and an organisation may edit, add or remove them as its own act, with its own
history. The tenant's set is the one its documents are walked against. A
client holds no copy of either: it asks the tenant's content service for a
document's walk
([`architecture/content`](../../architecture/content.md#walking-an-entry)),
and where that cannot be answered it says the check did not run rather than
checking against a list of its own. Outside any tenant, a client reads the
families from the corpus repository it has open.

## What tests this

[`checks/families.py`](../../checks/families.py), from
[`checks/run.sh`](../../checks/run.sh): each template here walks against its
family with no refused finding, no family lets a heading open two slots, and
every `structure:` a programme's spec or form names is a family in this
directory. Each has a control: a spec naming a structure no family declares is
reported, and a family whose alias repeats another slot's heading is
reported.
