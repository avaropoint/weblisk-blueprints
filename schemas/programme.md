# Programme Schema

Schema governing **programmes** — the definitions in `programmes/` that declare
which artifacts a body of work requires, what each answers, and the recurring
work the organisation takes on by adopting it: occupational health and safety,
document control, quality management, a maintenance regime.

Derived from the implementation that already reads these files — Weblisk
Studio's `internal/program` — and from the two packs authored against it, rather
than designed ahead of them. Every field below is one the loader places, and
every refusal below is one it makes. Where a rule is enforced somewhere other
than the loader, this says so, because the difference decides whether a mistake
stops the file or is discovered months later by somebody reading a readiness
number. [Scope](#scope) is declared by this schema rather than taken from the
loader, and where the two differ, this schema is the one that is right.

> **A programme is not a standard.** A standard declares what an authority
> requires ([`standard.md`](standard.md)); a programme declares what an
> organisation must *build and operate* to answer it. One cites the other and
> neither contains it. See [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md).

---

## What a programme is, and is not

A programme is **a curated selection of artifacts, tiered**, in the same sense
that a standard is a curated selection of controls. The artifacts live outside
it and are cited by it, so one artifact serves several programmes without being
written twice — and adopting a second overlapping framework mostly adds
citations to documents that already exist rather than adding documents.

It declares what ought to exist. It does not declare what any particular
organisation's document *says*: that is drafted from the `brief`, grounded in
that organisation's own context, and it must never be canned. **Programmes are
generic until a tenant customises them.**

It also holds no evidence, no score and no org chart. Who holds a position, what
was inspected on Tuesday, and whether the programme is 40% complete are **tenant
content** — the customer's, in the customer's repositories.

---

## Format

**Markdown with YAML frontmatter.** The most valuable field in an artifact spec
is the `brief` and the most valuable field in a tier is its `rationale` — both
paragraphs a domain expert will rewrite fifty times. A paragraph inside a JSON
string cannot be reviewed, cannot be diffed usefully, and cannot be opened in an
editor, which is why standards are JSON here and programmes are not.

A `.yaml` or `.yml` file is accepted for a generated programme, with `brief:` or
`overview:` as a block scalar. In a `.md` file **the body wins** over a
frontmatter `brief:`/`overview:`, because the body is the form a person edits
and a file carrying both answers the same question twice.

### Three file kinds, and where a file sits decides

    programmes/<programme>/map.md                a programme map
    programmes/<programme>/specs/<name>.md       an artifact specification
    programmes/<programme>/templates/<name>.md   a blank form

**Where a file sits alone says what it is.** The map is one file at the
programme's own root; a file under `specs/` is a specification; a file under
`templates/` is a form somebody fills in; a file under anything else is ignored
entirely. The segment above them names the **programme**, so provenance survives
the merge — "which programme claimed this" is the first question asked of a
programme somebody did not write.

Two more directories travel with a programme without being programme files:
`skills/`, holding the [skill files](#skills--files-the-programme-brings) its map
names, and `domains/`, holding the blueprint of each
[domain service](#domain_services--a-domain-service-the-programme-asks-to-have-built)
it asks for. The loader ignores both; adoption delivers them.

A root that *is* a single programme loads too, with its `map.md` and `specs/` at
the top. One rule covers both shapes, so nobody has to learn a nesting depth.

**Every earlier spelling still loads, and always will**: `artifacts/` for
`specs/`, and `programs/` or `programmes/` for the directory the map used to sit
in. A programme is content in somebody's repository, and a convention that
stopped recognising what it wrote last month would orphan a tenant's adopted copy
and every programme an organisation authored. There is no cutover.

A path convention rather than a `type:` field because a programme is a repository
of content: directories are what a person browsing one already sees, and a
discriminator field is a thing to get wrong in a file whose whole point is being
hand-authored. Which is also why the names have to be right. `specs/` was
`artifacts/`, and *artifact* everywhere else in this product means a real
document at a real path — the directory said the opposite of what it held.

### Not in the blueprint type registry, yet

These files carry `---` YAML frontmatter, not the `<!-- blueprint -->`
declaration block [`common.md`](common.md#frontmatter) requires, and they declare
no `type:`. That is the state of the product that reads them, recorded here
rather than wished away. `CORPUS_SHAPE.md` names the reconciliation of the two
forms as open work: one wins and the loser is converted, not left as a second
dialect. Until that is decided, this schema describes the form that loads.

### One bad file is one bad file

A file that will not parse or will not validate is **skipped and reported**,
never fatal. A single malformed file emptying the catalogue presents as "this
installation has no programmes" and sends somebody looking in entirely the wrong
place. Every refusal below produces a problem naming the file, and the rest of
the pack loads.

---

## Versioning

A programme map and an artifact specification each carry a **`version:`** —
`MAJOR.MINOR.PATCH`, the same field and the same three meanings
[`common.md`](common.md#versioning) already gives every other blueprint. There
is no second vocabulary here, deliberately: a family that classified its own
changes differently from the rest of the corpus would be a fourth spelling of a
question already answered three times.

Programmes are the family a tenant **adopts**, and the only one that had no
version. Measured against this corpus at `4778c25`:

| family | carries `version:` |
|---|---|
| `architecture` · `patterns` · `platforms` · `protocol` · `agents` | **81 of 81** (the five `README.md` are the only files without one) |
| `standards/*.json` | 61 of 61 — but see below |
| programme maps | 0 of 12 |
| artifact specs | 0 of 222 |

So the one body of work an organisation takes on, is measured against, and is
audited on was the one thing that could not say which version of itself it was.

> **Two different things are called "standards" and only one of them is this.**
> [`framework.md`](framework.md#versioning) says *"standards … are not versioned
> in frontmatter … version tracking is by git history"*. That sentence is about
> the **framework guidance documents** in `frameworks/<name>/` — the things a
> project blueprint names in `extends: frameworks/weblisk/pages` — which were
> called `standards/` before [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md) renamed
> them. It is **not** about the compliance standards in
> [`../standards/`](../standards/README.md), and it is not an argument against
> versioning a programme. "By git history" is in any case unavailable to the
> people who need it: the corpus reaches an installation as a checkout, a path
> in an environment variable, or a cache — and on a customer's machine it may be
> none of those. A provenance scheme that needs the publisher's git history is
> not provenance.

> **A standard's `version:` is a different axis and must not be confused with
> this one.** It records the **publisher's edition** — `"2022, incorporating
> Amd 1:2024"`, `"R.S.O. 1990, c. O.1, consolidated to 27 November 2025"` — and
> 59 of the 61 are not semver-shaped at all. We do not version somebody else's
> published framework; we cite which edition of it we read. A programme is ours
> (or the tenant's) to publish, so a programme's version is a claim we may
> actually make.

### What each part of the number means, for a programme

`common.md` fixes the three classes — **MAJOR** breaking, **MINOR** additive,
**PATCH** clarification — and [`framework.md`](framework.md#versioning) names
the same three as *restrictive*, *additive* and *clarification*. What follows is
only which programme edit falls where. It is the author's judgement to make; the
table is what the judgement is made against.

**On a map:**

| class | edits |
|---|---|
| **MAJOR** | `id` changed · a tier removed or renamed · **any change to which artifacts a tier contains**, including moving one between tiers · an artifact dropped from the map · an `operations` entry removed or its `does` changed · a `workflows` entry removed, or a step added, removed or reordered, or a step's `task`, `approval`, `does` or `needs` changed · an operation's `agent:` changed · a workflow's `schedule`, `on`, `when`, `for` or `start` changed · a step's `agent:`, `after` or `escalate` changed · a `notices` entry removed or its `on` or `to` changed · a `skills` entry removed or its `file` changed · a `domain_services` entry removed or its `blueprint` changed |
| **MINOR** | a new tier **above** the current top · an artifact placed at an existing tier · a new operation · a new workflow, notice or skill · a skill's `for` changed · a new `domain_services` entry · a new `domains` or `conforms_to` entry |
| **PATCH** | `title` · `rationale` · the overview body · `order` · a `why` · a notice's `says` · the bytes of a skill file the map brings |

**A domain service's blueprint is versioned on its own.** It is a `type: domain`
blueprint and carries its own `version:`, so a change to its bytes is classified
by that blueprint's bump under [`common.md`](common.md#versioning), not by the
map; only pointing the map at another blueprint is the map's MAJOR.

**Any change to a tier's membership is MAJOR**, in both directions, and that is
the one rule here worth arguing with. A tier is a **threshold**: readiness is
reported per tier, and an organisation that was 100% conformant is not
conformant any more the moment the line moves, whether the line moved up or
down. A threshold that moves without a major bump silently re-scores an
organisation against a line it never agreed to, and the number it re-scores is
the one somebody puts in front of an auditor.

**On an artifact specification:**

| class | edits |
|---|---|
| **MAJOR** | `id` changed · **an entry removed from `satisfies`** · **any change under `declares.obligation` other than the `activity`'s wording** — `cadence`, `applies_to`, `per`, `for`, `records`, `responsible`, `escalate`, `authority` · a register column removed, rekeyed or retyped · a `relation` target changed · `approved_by` gained or changed · `requires` gained · `kind` or `register.layout` changed · **`artifact_scope` or a column's `scope` declared, changed or removed** · `pii` added to or removed from any labels |
| **MINOR** | an entry added to `satisfies` · a register column added · `template` first named · a new optional field · a label other than `pii` added or removed |
| **PATCH** | the `brief` body · `title` · `path` · `structure` |

Three of those deserve their reason stated, because each was measured in this
corpus's own history rather than imagined:

- **Withdrawing a `satisfies` entry is MAJOR.** It removes coverage of a control
  the organisation is measured on. **22 specs** lost citations between their
  first commit and `4778c25`; a tenant holding the earlier copy believes it
  answers controls the corpus no longer claims.
- **Changing `declares.obligation.records` is MAJOR.** The records path is where
  occurrences land. **36 specs** moved theirs (`registers/construction/…` →
  `registers/…`), and a tenant taking that change without noticing orphans every
  record already written against the old path.
- **Changing `applies_to` or adding `per` is MAJOR.** It changes *how many
  occurrences exist*. **19 specs** went from `each project` to `the
  organisation` and **15** gained a `per` block — the single most consequential
  edit a programme can make: the amount of work owed changes, and every
  readiness number computed from it changes with it.

`approved_by` gaining an entry is restrictive for the same reason `common.md`
calls a new required field restrictive — a document that was in force now needs
a signature it did not need.

**A change of scope is MAJOR in both directions**, for the reason a tier's
membership is. A scope decides where a document may be kept. Raising it can put
a document a tenant already holds above its repository's ceiling; lowering it
tells a tenant it may keep less protected what it already protects. `pii`
decides which repository a register may live in, so adding or removing it is
MAJOR too.

### Unversioned is a real answer, and is never 1.0.0

A file that declares no `version:` is **unversioned**. It is not `1.0.0`, not
`0.0.0` and not "assume compatible". Nothing may be pinned against it, and an
adoption of it is describable only by content hashes.

This is the state of every programme file in this corpus except
`document-control`'s map and four specs, which arrived from Studio's source tree
already carrying versions; its five templates declare none, like every other
form. It is reported rather than defaulted. Studio's loader (`internal/program/version.go`) reads the field, and
`Catalogue.Versions()` names every file that declares none — because a reader
that filled the gap with a number would be inventing the one fact an adoption
most depends on.

A version that is present and **will not parse** is refused, and the file is
named. That is the same treatment a malformed `satisfies` citation gets and for
the same reason: an unverifiable claim that is admitted reads downstream as a
claim that was checked. `1.0`, `v1.0.0` and `1.0.0-rc1` are all refused rather
than repaired — a reader that completed them would be deciding what the author
meant.

### `version` and `version_hash` are not alternatives

A tenant's adoption records **both**, because each answers what the other
cannot.

| | `version:` | `version_hash` |
|---|---|---|
| asserted by | the **author**, deliberately | the **bytes**, computably |
| answers | *may I take this change?* | *is this the thing I took?* |
| checked by | comparing against a declared range | `sha256sum`, no parser and no network |
| can it be wrong | **yes** — an author forgets to bump | no |
| cannot see | an edit nobody bumped for | the difference between a typo and a withdrawn control |

The failure mode is not hypothetical. Measured in this corpus: **81 of 81
blueprint files have been edited since `dea7caf` ("Set all blueprint versions to
1.0.0 for v1 baseline", 2026-04-28), and three of them say so.** A version alone
would report seventy-eight changed files as unchanged. A hash alone reports a
reworded brief and a withdrawn control claim in identical words.

Held together they also produce a third answer neither gives alone:

| hash | version | what it means |
|---|---|---|
| same | same | current |
| changed | changed | classify by the bump, and act on the declared `on_change` |
| changed | **same** | **unmaintained** — upstream moved and made no claim about it. Never auto-adopt; report it and ask a person |
| same | changed | the version moved with no content change. Harmless, and worth saying once |

`unmaintained` is the row that makes the pair worth carrying. It is exactly the
state 78 blueprint files are in, and neither field alone can name it.

### What a tenant pins against

The default is **a compatible range on the version, plus the hash of what was
actually taken**:

```yaml
extends:
  - blueprint: programmes/records-management
    version: ">=1.0.0 <2.0.0"
    resolved:
      map.md:
        digest:     sha256:…
        version:    1.2.0
        revision:   4883cfa88c55769560f8287d4a2fb4c94c5a6c98
        repository: 0192f7c4-…
      specs/rec.policy.md:
        digest:     sha256:…
        version:    unversioned
        revision:   4883cfa88c55769560f8287d4a2fb4c94c5a6c98
        repository: 0192f7c4-…
    on_change:
      compatible: validate-and-adopt
      breaking:   version-bump
      removed:    halt-immediately
```

The **range is the permission** — a compatible improvement is offered under
`on_change.compatible`, and a person takes it
([Updates arrive as proposals](#updates-arrive-as-proposals)). The **hash is the
record** — it says exactly what was taken, so *"did it move?"* is answerable
without trusting that anyone bumped anything. Where this block is kept, and
what else the act of adopting records and refuses, is
[Adopting a programme](#adopting-a-programme)'s.

A range is the default rather than an exact pin because a governance programme
is pinned against a body of law that moves. An organisation that froze
`construction-ohs-ca` in April would have missed forty-three statutory citations
added since — and would have had no signal at all, because a frozen pin reports
nothing. The default must permit improvement and **report** the rest.

Freezing is legitimate and is already expressible with no new field: an exact
`version: "1.4.0"`, or `on_change.compatible: validate` instead of
`validate-and-adopt`. It is the right choice inside an audit window or a
certification period, where the thing being measured must not move underneath
the measurement. It is a decision made per adoption, by a person, with a reason.
It is not a default, because a default nobody chose that quietly stops a safety
programme from receiving a regulator's change is a default that will eventually
hurt somebody.

### When versioning began, and why nothing is back-filled

This field was introduced after the corpus's programmes already existed. Every
programme file's version therefore **opens at `1.0.0` when it is first
declared**, and says nothing about what happened before.

That is not a convenient fiction, and the alternative is the fiction. Measured
across the programme corpus's eleven commits, **114 changes that this section
classifies as MAJOR have already happened** — withdrawn citations, moved records
paths, changed `applies_to`. Numbering a file `2.0.0` to describe them would
assert that a `1.0.0` was published and could have been pinned against. None
was. Inventing a release history to describe changes nobody could have depended
on is a worse lie than an honest baseline.

So the rule is:

- A version claims compatibility **from the moment it is declared**, forward.
- An adoption made **before** the file carried a version records
  `version: unversioned` and its `resolved:` entries. It is never back-filled to
  `1.0.0`, because that would assert the tenant agreed to a number that did not
  exist.
- The hashes are what make those adoptions checkable at all, which is the
  concrete reason the hash is not optional.

---

## The programme map

One file per programme: `map.md`, at the programme's own root.

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | stable identifier. What everything else cites, and what an override replaces |
| `version` | string | no | `MAJOR.MINOR.PATCH` — the author's compatibility claim, and what a tenant's adoption pins a range against. Absent means **unversioned**, never `1.0.0`; present and unparseable is refused. See [Versioning](#versioning) |
| `title` | string | no | display name. Defaults to `id` |
| `domains` | string[] | no | the policy domains this programme operates in — the same catalogue the classifier uses, so a programme is measurable through machinery that already exists. Each one is defined in [`../policy-domains/`](../policy-domains/README.md), which also states **what claiming it requires**; a claim on a domain nothing declares is reported, and so is a claim nothing answers. A subject area only: a domain **service** the programme asks to have built is [`domain_services`](#domain_services--a-domain-service-the-programme-asks-to-have-built) |
| `conforms_to` | string[] | no | the standard `id`s this programme is built to answer. **Context, not a constraint**: a programme with no framework at all is valid |
| `tiers` | array | no | the progression, below |
| `artifacts` | array | no | `{id, tier}` placements, below |
| `operations` | array | no | the standing machine work adopting it takes on — [below](#operations--the-standing-work-a-programme-installs) |
| `workflows` | array | no | multi-step work with waits and approvals — [below](#workflows--multi-step-work-with-waits-and-approvals) |
| `notices` | array | no | who is told what, by position — [below](#notices--who-is-told-what) |
| `skills` | array | no | skill files the programme brings — [below](#skills--files-the-programme-brings) |
| `domain_services` | array | no | domain controllers the programme asks to have built — [below](#domain_services--a-domain-service-the-programme-asks-to-have-built) |
| `order` | int | no | display position in the catalogue. A catalogue that reorders itself between runs of the same binary is one nobody can document |
| *body* | prose | no | the `overview` — what this programme is and why it is drawn this way |

`pack`, `source` and `builtin` are **set by the loader and may not be claimed**.
A file declaring them is not honoured: provenance is a property of where a file
was found, not of its bytes, and a pack able to assert `builtin: true` could
claim to have shipped with the product.

Maps sort by `order`, then `id`. An override — a map sharing an `id` with one
already loaded — **replaces it in place** and inherits the original's `order`
when it states none, so correcting a programme's wording does not move it in the
catalogue.

### Tiers

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | unique within the programme |
| `title` | string | no | display name. Defaults to `id` |
| `rationale` | string | no | prose — why this line sits where it does |
| `requires` | string | no | the tier immediately beneath. **Empty marks the base** |

**Tiers are the most important idea in this schema.** Without them, adopting a
standard means being handed two hundred gaps at once, which is
indistinguishable from being told the programme is hopeless. A target tier turns
a wall into a roadmap: readiness is reported per tier — three honest numbers
instead of one demoralising one.

Three properties are enforced rather than assumed:

- **The author declares them.** No maturity model ships with the platform,
  because a maturity model is domain knowledge and domain knowledge is data. A
  tier may mirror an accreditation body's thresholds, a regulator's phase-in
  dates or a customer's rollout, and nothing in the engine can tell the
  difference.
- **They are cumulative and ordered.** `requires` makes a chain, so resolving
  the second tier always includes everything the first asked for.
- **A programme may have NO tiers at all.** A four-artifact maintenance plan
  with one obligation and no framework must work through exactly this
  machinery. If the smallest programme needs ceremony, the model is wrong.

`rationale` is worth writing. *"Below this line the organisation is exposed, not
merely unaccredited"* is the sentence that makes a tier a decision rather than a
label.

### Artifacts

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | an artifact spec's `id` |
| `tier` | string | no | which tier it belongs to. **Empty means in scope at every tier**, which is what makes an untiered programme work without a special case |

An artifact listed twice keeps its **first (lowest)** placement: the earliest
tier that needs a document is the tier that has to have it.

**An artifact the map cites and no pack defines is still returned**, carrying
only its id. Dropping it would report a broken map as a smaller programme, and
nobody could tell "this tier is light" from "four specs are missing".

---

## The artifact specification

One file per artifact, under `specs/`. Standalone, and deliberately **not
nested inside a programme**: one training-record matrix serves several
programmes at once.

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | stable identifier. What a map places and what other specs `require` |
| `version` | string | no | `MAJOR.MINOR.PATCH`, as on a map. Withdrawing a `satisfies` entry and changing anything under `declares.obligation` are both MAJOR — see [Versioning](#versioning) |
| `kind` | string | no | the artifact's own noun — what the created document declares about itself. The vocabulary is [`kinds.md`](kinds.md) |
| `title` | string | no | display name. Defaults to `id` |
| `structure` | string | no | the document structure it is **checked** against — the `id` of a [structure](#the-structures-a-document-is-checked-against). `policy`, `procedure`, `standard` and `guideline` are seeded, one file each in [`structures/`](structures/), and a tenant may add or remove them |
| `path` | string | no | a **suggestion** for where the document goes. Required only for a standing register |
| `satisfies` | string[] | no | the controls this artifact answers, as `framework:control` |
| `requires` | string[] | no | artifact `id`s this one depends on — the DAG that orders generation |
| `template` | string | no | a doc template this organisation starts documents of this kind from. The **shape**, never the content |
| `approved_by` | string[] | no | the **positions** that must sign this artifact off before it is in force |
| `artifact_scope` | string | no | the `ScopeLevel` of the document this artifact creates. Never spelled `scope:` — see [Scope](#scope) |
| `artifact_scope_metadata` | mapping | no | `custom_labels`, the labels that go with `artifact_scope`, such as `pii`. See [Scope](#scope) |
| `declares` | mapping | no | what creating this artifact also creates — `obligation` and `register`, below |
| `register` | mapping | no | the schema, when this artifact **is** a register. Requires `kind: register` |
| *body* | prose | no | the `brief` — what this document must establish for THIS organisation |

`pack`, `source`, `builtin` and `derived_from` are **set by the loader and may
not be claimed**, as on a map.

### `structure` need not be the same word as `kind`

A plan and a procedure share a shape. An organisation that has no "plan"
structure would otherwise see the checklist report a plan as having no expected
sections — **which reads as "this document is fine"**.

### The structures a document is checked against

A structure is the set of headings a kind of document is expected to have, and
what belongs under each. It drives the structure checklist and the brief a
model is handed when somebody asks it to fill a missing section. The seeded
ones are corpus content, **one file per structure** in
[`structures/`](structures/), named `<id>.md`:

    schemas/structures/policy.md
    schemas/structures/procedure.md
    schemas/structures/standard.md
    schemas/structures/guideline.md

Markdown with YAML frontmatter, as every programme file is. The frontmatter is
the structure; the body says, for a person, what the structure is for, and no
tool reads it.

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | what a spec's `structure` names. Lowercase, singular, and the file's own name |
| `version` | string | no | `MAJOR.MINOR.PATCH`, as on a map. Adding a required section, making one required, or removing one is MAJOR: each changes which documents the checklist reports complete |
| `label` | string | no | display name. Defaults to `id` |
| `order` | integer | no | where the structure sits in a list of them. Lowest first |
| `sections` | list | **yes** | the expected headings, in the order a document should carry them. At least one |
| `sections[].title` | string | **yes** | the heading. Unique within the structure, ignoring case |
| `sections[].required` | boolean | no | `true` when a document without this section is incomplete. Default `false`: most documents of the kind have one, and missing it is not a gap |
| `sections[].aliases` | string[] | no | other headings that satisfy this one, so an organisation that writes "Statements" is not told it lacks "Policy Statements" |
| `sections[].guidance` | string | no | what belongs here, in a sentence. Shown beside a gap, and the brief a model is given to fill it |
| `sections[].authority` | string | no | a control of a standard the **tenant has adopted** that requires this section, as `framework:control` — the form `satisfies` takes |

A heading satisfies a section when it equals the title or an alias, ignoring
case. A structure with no sections is refused, because it would report every
document as complete. So is one in which a title or an alias equals another
title or alias of the same structure, ignoring case — two sections' titles, a
title and another section's alias, or two aliases — because one heading would
then satisfy two sections and the checklist could not say which.

**The seeded structures cite no standard.** They are conventions of document
writing, not obligations, and a framework clause written into them would be
standards content resident in a file no adoption chose — the same text held
twice, cited by a tenant that never adopted it. `authority` is how a tenant
says a section is required by something it *has* adopted, and it is empty in
every seeded file.

**Which structure a document is checked against**, first match wins:

1. the `structure` in the document's own frontmatter, which a form's
   `frontmatter:` block writes ([A form's `frontmatter:`](#a-forms-frontmatter));
2. the `structure` of the spec that created it;
3. for a document no form or spec created, its kind as [`kinds.md`](kinds.md)
   classifies it, resolved through `specializes`: the structure whose `id` is
   the kind, else the one whose `id` is the kind it specializes, and so on up
   the chain. `document` is never reached this way — it means unclassified,
   and an unclassified document is not checked as anything. So an `sop`,
   runbook or playbook with no structure of its own is checked as a
   `procedure`, while a `reference` has no check.

A structure declares no path of its own: a second list of folder names beside
the classification stems in `kinds.md` would drift from them. A document whose
resolution ends without a structure has **no check**, and says so; it is never
reported as complete.

**Only an organisation's own documents fall back by kind.** Step 3 applies to
what a tenant authors. Published content has no structure check: an industry
standard delivered and adopted as [`standard.md`](standard.md) declares, and
any file of this corpus read as a source. `kinds.md` classifies the `standards`
and `schemas` segments as `standard`, so without this rule every adopted
standard and every schema file — the files in [`structures/`](structures/)
among them — would be reported as an organisation standard lacking Overview
and Requirements: a gap in a document nobody in the organisation writes. A
published file is reported as not checked, never as incomplete.

**Whose copy is checked.** The seeded files are published content: delivered
into a tenant, where an organisation may edit, add or remove structures, and
the tenant's set is the one its documents are checked against. A client holds
no copy of either. No route of [`architecture/content`](../architecture/content.md)
yet names where a tenant's structures live, so a client that cannot read them
reports that the check did not run rather than checking against a list of its
own.

**What tests this.** The corpus has no test harness of its own, and no test yet
reads these files. The Verification Checklist row below is a person's check
until Studio lane S19 (which reads these structures live and removes its own
copies) adds a test against the pinned corpus that fails when a file in
[`structures/`](structures/) does not parse, has no section, repeats a title or
alias, or carries an `authority`; when a shipped spec's or form's `structure`
names no file there; or when this section stops linking the directory.

### `path` is a suggestion

The organisation's folder conventions are its own, and a spec that fixed the
location would be usable once per workspace. The exception is a standing
register, whose path is its identity and is refused when absent.

### `requires` orders generation, and that ordering is the point

A procedure drafted before its parent policy invents its own scope, and then two
documents disagree about who the programme applies to. The DAG also gives
correct parallelism for free — everything at the same depth is independent.

A spec that requires itself is refused. A cycle among artifacts in scope is
refused, naming the participants.

**An artifact placed at a lower tier than something it requires is reported**
against the map that placed it. Resolving at the dependent's tier would hand the
planner a procedure whose parent policy is not in the plan.

### `approved_by` names positions, never people

It is the one thing in a programme that genuinely cannot be worked out from
anything else. An obligation says who *performs* recurring work; a register may
say who approves a *record*; nothing anywhere says who accepts the document
itself — and deriving it from the obligation's responsible position would be
wrong in the common and important case, because the person who does the work is
rarely the person who signs off that it is the right work.

Positions, because people change jobs and the approval belongs to the position.
Resolving them to humans happens when the sign-off is raised, against the
holders at that moment. **Empty means nobody is asked**, which is a legitimate
choice for a document an organisation does not formally adopt, and is reported
as unasked rather than as approved.

### `template` and `brief` are not two ways of saying the same thing

A template is what a person opens and fills in by hand; a brief is what an agent
drafts from. A pack shipping both for one document with no link between them
gives the organisation a hand-written copy and a drafted copy that need not
resemble each other, both correct by their own lights. Name the template; do not
inline it.

---

## `declares.obligation`

The recurring work an artifact commits the organisation to. Field for field the
shape the engine reads out of the generated document's frontmatter, so
generating the document and starting the programme loop are one act.

| field | type | required | means |
|---|---|---|---|
| `id` | string | no | stable and local to the artifact — what a record cites to say which obligation it discharges. **Defaults to the artifact `id`**, because renaming the activity must not orphan two years of records |
| `activity` | string | **yes** | what must happen. An obligation with no activity is a cadence for nothing |
| `cadence` | string | conditional | how often — a **closed vocabulary**, below. Mutually exclusive with `for` |
| `authority` | string | no | what requires the activity, cited the way its own world writes it. Free text, deliberately: the platform must never hold a list of which laws exist |
| `interval_basis` | string | no | whose interval this is — `required` or `chosen`, a **closed pair**, below |
| `responsible` | string | no | the **position** that owns it, never a person |
| `applies_to` | string | no | **where** each occurrence is expected in the organisation — a **closed vocabulary**, below |
| `per` | mapping | no | **what** each occurrence is about — one occurrence per period per subject, below. Requires `cadence`; mutually exclusive with `for` |
| `records` | string | no | the register each occurrence is written into. Empty means the platform cannot tell whether the activity happened |
| `satisfies` | string[] | no | the controls this activity answers, as `framework:control` |
| `for` | mapping | conditional | a **record-origin** trigger, below. Mutually exclusive with `cadence` |
| `escalate` | mapping | no | `{after, to}` — what happens when an occurrence stays overdue |
| `creates` | mapping | no | `{template, path}` — the document each occurrence is discharged by filling in, below |

**An obligation with no `records:` is a statement that something must happen and
no way to tell whether it did.** That is worth saying — an unverifiable
obligation is a governance finding — and it is never counted as met.

### `per` — one occurrence per period, per subject

| field | type | required | means |
|---|---|---|---|
| `listed_in` | string | **yes** | the register whose rows ARE the subjects |
| `key` | string | **yes** | the column carrying each subject's identity — what a record cites |
| `label` | string | no | the column a person reads. Identity and name are different columns because the name changes and the join must not |
| `from` | string | no | the column saying when a subject enters |
| `until` | string | no | and when it leaves. An empty cell means still |
| `recorded_as` | string | no | the column in `records:` that cites the subject. **Derived when absent** from the relation that register already declares — see below |

`applies_to` and `per` answer different questions, and keeping them apart is the
whole point:

```yaml
applies_to: the organisation          # WHERE — the org holds the register
per:                                  # WHAT  — one card per live job site
  listed_in: registers/projects.md
  key: project_id
  label: name
  from: start_on
  until: finished_on
cadence: each quarter
records: registers/first-aid-station-inspections.md
```

That declaration expects one first aid inspection **per live site per quarter**.
Fourteen sites, fourteen cards, each one nameable and each one dischargeable on
its own.

**Why this is not `applies_to: each project`.** It reads as though it were, and
that is exactly the trap. `applies_to` expands over the *placement* tree —
tenant, organisation, workspace — and a construction firm running fourteen job
sites from one workspace was expected to produce **one** inspection between them.
Measured on a real programme: a monthly obligation over a register of four jobs
produced four occurrences, one per month for the whole company, and would have
produced the same four with forty sites. Worse than a gap, because the first site
to file discharged it for all of them: a false clean bill, the same shape as
`applies_to: each crew`.

**Why it is not fourteen workspaces either.** A subject's identity is already in
the data — every recording register carries a relation column onto the subject
register, and the rows join on it today. Minting a workspace per site would make
a second identity for one thing, and the occurrence would then join on a slug
while the record joined on the id. A subject also has a *life*: `start_on` and
`finished_on` are columns, so "expected only while the job is running" is a fact
the register already states, and a workspace has no such window. Placement means
something else again — where content sits and who can see it — and job sites are
not a visibility boundary.

**Liveness is overlap, not a point.** A subject is expected to have work done on
it in any period its window overlaps. A job that ran to the 28th of August owed
August's inspection; judging liveness at the moment the record was due — the
31st — writes off the last period of every job the organisation ever ran.

**The join is derived, not declared twice.** The recording register already says
which of its columns cites a subject:

```yaml
- {key: project, label: Project, type: relation,
   target: /registers/projects.md#records, display: project_id}
```

That relation *is* the join, so `recorded_as:` exists only for a register with no
schema fence. A recording register that declares no such relation reports its
occurrences **unverifiable**, naming the missing column — never matched by date
alone, because one site's inspection credited to all fourteen is the failure this
section exists to remove.

**A register of subjects that cannot be read is said, not counted as nothing.**
A renamed, moved or not-yet-created register reports one unverifiable occurrence
with the reason attached. An empty register and a missing one are different
answers.

### `for` — one occurrence per record, not per period

| field | type | required | means |
|---|---|---|---|
| `records` | string | **yes** | the **trigger** register whose rows create the work |
| `due` | string | **yes** | the deadline measured from a date that row carries — a **closed form**, below |
| `key` | string | no | the column whose value identifies each record. Defaults to `id` |

"Investigate this within three days", "renew this before it expires",
"re-inspect after this repair" have no period: an incident happens once, at a
time, and asking which week it belongs to has no answer. A record trigger raises
one occurrence per row, due relative to that row's own date, and collapses what
looks like three features — incidents, corrective actions, expiry — into one
mechanism.

`key` must name a column that is **stable**. A row number renumbers under a
signature that still verifies.

### `escalate` — who it becomes the problem of

| field | type | required | means |
|---|---|---|---|
| `after` | string | **yes** | how long past due — a **closed form**, below |
| `to` | string | **yes** | the position it then belongs to. Never a person |

Declared rather than inferred, because there is no role hierarchy to infer from:
positions are deliberately flat — a construction firm's and a hospital's have no
common shape — so "the position above" is not a question the platform can
answer. It is also where the judgement belongs: a late inspection and a late
incident investigation do not escalate to the same person.

### `creates` — a document per occurrence, not a row

| field | type | required | means |
|---|---|---|---|
| `template` | string | **yes** | the `id` of a form under this programme's `templates/` — the blank the card starts from |
| `path` | string | **yes** | where each card is created. `{key}` is replaced by the subject's or the trigger row's key **as a slug** — lower-cased, with every character other than `a-z`, `0-9`, `-` and `_` turned into `-` and leading and trailing `-` trimmed — and `{date}` by the day the card is created, `YYYY-MM-DD`. Nothing else is substituted. Two keys that differ only in what the slug folds land at one path, and the second card answers with the first |

Some work is discharged by filling in a **document**, not a cell: a field-level
hazard assessment carries a list of hazards, a signature per crew member and
photographs, and none of that fits a row. `creates` names the form each
occurrence is filled in on and where the filled-in card is kept. The obligation
still names `records:`, and the register keeps one row per completed card.

**Taken, and the form the engine already reads.** Studio's obligation engine
reads `creates: {template, path}` from a document's frontmatter today; this is
that shape, with no second spelling. It was once left out of this schema
because a pack that declared it had it silently dropped by the programme
loader. A field the schema declares and a reader drops is the same fault, so a
reader that does not yet place `creates` **refuses the spec**, naming the
field, rather than loading it without the card
([Known gaps](#known-gaps)).

**Creating a card does not discharge the occurrence.** An occurrence is
recorded when its row is in `records:`, and the row is written when the card is
completed, never when the blank is created. A blank card counted as done would
report a day's work as finished at the moment somebody pressed the button.

**A card is never overwritten.** A card already at the resolved path is
somebody's filled-in record, and creating one again answers with the card that
is there.

Refused at load, and the file is named: a `creates` with no `template` or no
`path`; a `template` that names no form in the programme's `templates/`; a
`path` that is absolute or leaves the repository; a `path` with no `{key}` on
an obligation that has `per:` or `for:`, or with no `{date}` on one that has a
`cadence`, because every subject's or every period's card would then be
created at one path, and only the first could exist.

---

## Registers

A register is the document an obligation's records are written to, and **its
columns are declared, never briefed.** Every other artifact in a programme is
prose drafted by a model from a brief; a register is read by the *platform* —
the occurrence engine walks its rows to decide whether the activity happened —
so a schema a model invented is a register the platform cannot reliably read. A
declared register is derived; a drafted one is a guess the engine then treats as
fact.

**Two forms, one shape.**

| form | declared as | its path | its id |
|---|---|---|---|
| an obligation's **record log** — one row per occurrence | `declares.register` on the artifact declaring the obligation | the obligation's `records:` | `<artifact id>.register`, derived |
| a **standing register** — the list of sites, documents, certificates whose rows are the *subjects* obligations multiply over | `register:` on an artifact with `kind: register` | its own `path` | its own `id` |

Both become a real artifact, so everything downstream — coverage, gap lists,
tier readiness, the plan — works on them with no special case. A record log's id
and path are both **derived and unauthorable**: the failure being prevented is
an obligation and its register disagreeing about where the records live, and two
fields a person can set differently is how that happens.

An artifact may not be a standing register **and** declare a record log: a
register's own rows are not its obligation's records.

| field | type | required | means |
|---|---|---|---|
| `title` | string | no | what the document is called. Defaults to the obligation's activity, or the spec's title |
| `note` | string | no | prose for the person opening it: what belongs in a row and what does not |
| `columns` | array | **yes** | at least one, below |
| `layout` | enum | no | `form` — or omitted for a table. **Closed** |
| `review` | enum | no | `required` — a submission waits for approval. **Closed**, and needs `layout: form` |
| `approvers` | string[] | no | the **positions** that must sign a submission off. Needs `layout: form` |
| `approval_order` | enum | no | `sequential` — ask them one at a time. **Closed**, and needs `approvers` |
| `retention` | mapping | no | how long the records must be kept, below |

### `layout` decides whether rows are evidence or notes

A table commits every keystroke, so a half-finished record lands in the
governance repository as it is being typed — **and a half-filled record
committed to a governance repository is a false statement.** A form drafts in
the browser and commits once, as one attributable version, which is also what
gives an occurrence a single act to attest.

A register whose rows discharge an obligation should almost always be a form. It
is **not the default**, because defaulting it would rewrite the derived output of
every pack already installed. So a pack asks.

Every incoherent combination is **refused rather than degraded** — `review:` or
`approvers:` without a form, `approval_order` with no approvers, any value
outside the closed set. Each is a case where the author asked for a protection
the derived document would not have, and dropping it quietly is how a register
comes to look reviewed and be typed into.

### `retention`

| field | type | required | means |
|---|---|---|---|
| `keep` | string | **yes** | whole years, months or days — `7y`, `18m`, `90d`. **Never a Go duration** |
| `from` | string | no | when the clock starts. `created` (default) or `modified`; anything else names an event on the record |
| `authority` | string | no | the citation being implemented. Free text, deliberately: the platform must never hold a list of which laws exist |
| `reason` | string | no | why, for a reader who was not in the room |

Declared, because a keeping period is a legal requirement the author knows and
the platform cannot infer, and **an unset retention on a statutory record is the
one gap that gets worse with time rather than better.** A keeping period with no
`authority` is a number somebody chose; with one it is a requirement somebody
can defend.

`7 years` is not 61,320 hours in any month containing a leap day, and a schedule
that drifts by a day a decade is one somebody will eventually have to defend —
so the unit vocabulary is years, months and days, and a duration expression is
refused rather than converted.

A `from` naming something other than creation or modification — the end of an
employment, the closure of a project — is **accepted and reported as
unresolvable until that event is recorded**, which keeps the record rather than
disposing of it early.

**A cumulative register counts from `modified`.** The engine resolves `from`
against the register's file, and a register is one file that rows are appended
to — so `created`, the default, starts the clock at the first row ever written
and disposes of a file holding last month's records. Every declaration in the
shipped corpus therefore says `from: modified`; the newest entry governs the
file. `created` is right only for a document written once and never added to.

### Columns

| field | type | required | means |
|---|---|---|---|
| `key` | string | **yes** | unique within the register. What a trigger and a discharge cite |
| `label` | string | no | the header a person reads. Defaults to `key` |
| `type` | string | no | the column type. Defaults to text |
| `required` | bool | no | the field must be answered |
| `options` | string[] | conditional | the choices, for a `select` |
| `target` | string | conditional | the register a `relation` points at. **Required for `relation`** |
| `display` | string | no | which of the target's columns is shown |
| `scope` | string | no | the `ScopeLevel` of what the column holds. See [Scope](#scope) |
| `scope_metadata` | mapping | no | `custom_labels`, the labels that go with `scope`, such as `pii` |

Two columns sharing a `key` are refused: the second silently wins on every read,
so one of the two answers is never recorded. A `relation` with no `target` is
refused: it offers no choices, so the field is unanswerable and the record
cannot be completed.

**`type` is deliberately not validated against a list here.** The column types
are declared once, in the renderer's own registry, and a second list in a schema
would be a second source of truth that drifts. The types that registry declares
are `text`, `longtext`, `number`, `int`, `currency`, `percent`, `date`, `bool`,
`select`, `link`, `formula`, `user`, `signature`, `attachment`, `relation` and
`rollup`. **An unrecognised type renders as text** — a degradation a reader can
see, not a silent failure.

A `relation` cell stores the target row's **key**, never its rendered value, so
renaming a site does not rewrite every record that cites it.

---

## Scope

A spec may say how much protection the document it creates deserves: its
**scope**, a `ScopeLevel` ([`patterns/scope`](../patterns/scope.md#level-hierarchy)),
with the labels that go with it. What a scope does once the document exists —
where the document may be kept, that its scope only rises, and what reads it —
is [`architecture/content`](../architecture/content.md#an-entrys-scope)'s.
This section says where a programme declares one.

| field | on | means |
|---|---|---|
| `artifact_scope` | a spec | the scope of the document the spec creates |
| `artifact_scope_metadata` | a spec | `custom_labels`: the labels that go with it, such as `pii` |
| `scope` | a register column | the scope of what the column holds |
| `scope_metadata` | a register column | `custom_labels`, as on a spec |
| `scope` | a form's `frontmatter:` | the scope of the document the form creates |
| `scope_metadata` | a form's `frontmatter:` | `custom_labels`, as on a spec |

`custom_labels` is `patterns/scope`'s field, and nothing else under the two
`_metadata` keys is read. A label is refused where no level is declared beside
it, and a value that is not a `ScopeLevel` is refused too, and the file is
named. How a label and the level beside it combine is
[`patterns/scope`](../patterns/scope.md#a-label-and-its-level)'s.

### `artifact_scope` is never spelled `scope`

A spec file is itself a document in the repository that holds the programme,
and `architecture/content` reads a top-level `scope:` in a document's
frontmatter as that document's own level. A spec that wrote `scope: restricted`
to describe the incident register it creates would make the spec restricted,
and with it the repository the programme is kept in, though the spec names
nobody. So the spec's field is `artifact_scope`. A top-level `scope:` or
`classification:` on a spec or a map is the file's own level, and says nothing
about the document the spec creates.

### A form's `frontmatter:`

A blank form under `templates/` carries a `frontmatter:` block: the frontmatter
the document created from it opens with. `scope:` and `scope_metadata:` in that
block are the created document's own level and labels. They are never the form
file's own, because they are not top-level in it. They are refused as a spec's
are: a label with no level beside it, and a value that is not a `ScopeLevel`.

### What the created document carries

A document created from a spec carries its scope as `scope:` in its own
frontmatter, and its labels as `scope_metadata: {custom_labels: […]}`. For a
register those are the register's level, below, and every label its spec or
any of its columns carries. A document created from a form carries what the
form's `frontmatter:` gives. Whatever creates the document writes them, from
the spec or the form. A model never chooses them.

A document that already exists is never rewritten on open to carry them. The
client that writes the next change a person makes to it MUST add them in that
change, from the spec or the form, wherever the document lacks them. Where the
entry's recorded scope is higher than the spec's, the client writes the
recorded one, because a change never declares less
([`architecture/content`](../architecture/content.md#a-scope-only-rises)).

### A register's level

A register is at the highest of the `artifact_scope` of the spec that declares
it and every column's `scope`, whether or not any row holds a value in that
column. That is the escalation
[`patterns/scope`](../patterns/scope.md#scope-escalation) requires of anything
composed. It holds for both forms: a standing register takes its own spec's
`artifact_scope`, and a record log declared under `declares.register` takes
the declaring spec's. A register nothing gives a level is created with no
`scope:` of its own. In a repository declared with a `scope_floor` it is at
the floor, and the write that creates it declares the floor
([Where a record holding `pii` lives](#where-a-record-holding-pii-lives)).
Anywhere else it is unclassified.

### Records about a person

A register whose rows are **about a person** — any row of it may have one
identifiable person as its subject, and records something about them — is
`restricted` and labelled `pii`, whatever its other rows record. So is a
document a form creates about one person. These are such records:

- a register any row of which may record an injury to a person or the state of
  a person's health: incidents, first-aid treatments, occupational illness,
  health assessments, fitness for duty, return to work, and accommodation of a
  medical need;
- a register of the credentials a person holds, of complaints made by or about
  a person, of the end of a person's employment, or of requests a person makes
  about their own personal information;
- the incident report, first-aid record, health assessment or other document a
  form creates about one person.

What each declares:

- Every column that names the person, or describes what happened to them,
  their body or their health, declares `scope: restricted` and
  `scope_metadata: {custom_labels: [pii]}`.
- A standing register's own spec declares the same, as `artifact_scope` and
  `artifact_scope_metadata`.
- A form's `frontmatter:` declares the same, as `scope:` and
  `scope_metadata:`.
- A column naming who recorded, reviewed or approved the row names a person
  acting, not the person the row is about, and is not labelled for that.

`restricted`, not `critical`. `critical` admits a document only to a store no
other authority can reach
([`architecture/content`](../architecture/content.md#derived-scope-ceiling)).
`restricted` also admits a shared store whose access can be listed, whose
changes can be attributed and whose history can be traversed.

### Where a record holding `pii` lives

A register **holds `pii`** when its spec or any of its columns is labelled
`pii`, and a document a form creates holds `pii` when the form's
`frontmatter:` labels it so. Each is kept in its scope's **records
repository**, the one repository
[`architecture/content`](../architecture/content.md#where-an-entry-labelled-pii-is-kept)
lets hold an entry labelled `pii`, and refuses it anywhere else. What a records
repository may be copied to is `architecture/content`'s
([Effective custody](../architecture/content.md#effective-custody)), and what
may be sent from it to a model provider is `patterns/scope`'s
([Model providers](../patterns/scope.md#model-providers)).

It is kept apart because the programme's other documents are policies and
procedures that people edit where they work, often in a shared store, and that
the tenant may want copied elsewhere. Kept with them, the register would need
that whole repository to hold `restricted`, and its rows would stay in that
repository's history, so every copy of the policies would have to be able to
hold them as well.

**Install resolves the records repository.** Whatever installs a programme at
a scope finds that scope's records repository once, at install: the repository
`GET /v1/content/repositories` reports with `records: true` for that
`scope_path`.

- A register holding `pii` is created at its path — a standing register's
  `path`, a record log's `records:` — in the records repository. A document a
  form creates that holds `pii` is created at the form's `path:` there too.
- Every other document the programme creates is created at its path in the
  repository that holds the programme's documents.
- Where the scope has no records repository, install creates nothing that
  holds `pii`. It reports each register and form it did not create with
  `CONTENT_RECORDS_REPOSITORY_REQUIRED`, the code its first write would be
  refused with ([`architecture/content`](../architecture/content.md#error-handling)),
  naming the scope that has no records repository. It reports
  every obligation that records into one as unable to record. Nothing that
  holds `pii` is created in the programme's repository instead.

**A path resolves by what it names.** A path a spec gives names a document,
never a repository: a register's `path`, an obligation's `records:`, a
`for.records`, and a `relation` column's `target`. It resolves in the records
repository when the register it names holds `pii`, and in the programme's
repository otherwise. Install, derive, the occurrence engine and every other
reader resolve it the same way. So a register of incidents in the records
repository relates each row to a project register in the programme's
repository by the target path its spec gives, and the relation cell holds the
project row's key ([Columns](#columns)).

**The records repository comes before enforcement begins.** Enforcement of a
repository begins when `architecture/content` records it `declared`. From then
on every write into it is checked against its ceiling and against where an
entry labelled `pii` may be kept. So, in this order:

1. The records repository is established or adopted, and declared as its
   scope's records repository.
2. The repository that holds the programme's other documents is declared,
   where it is not already. Its spec files declare no level of their own
   ([`artifact_scope` is never spelled `scope`](#artifact_scope-is-never-spelled-scope)),
   so a declaration made for it MUST carry a `scope_floor`
   ([`architecture/content`](../architecture/content.md#scope_floor-covers-what-declares-nothing)).
   A person chooses its level. Only a person may declare one, it is at least
   the `highest_scope` an adoption's census reports, and this schema names
   no level for it: what a tenant's programmes may hold is the tenant's
   judgement.
3. The programme is installed. Every document it creates is written through
   the content service's write route into the repository its path resolves
   to, each record holding `pii` into the records repository, and only then
   is the first row written. Each write declares a scope on the change: the
   higher of the level the spec or form gives the document and its path's
   recorded scope, which in a floored repository is never below the floor.
   Where the document carries `scope:`, it carries that level too
   ([What the created document carries](#what-the-created-document-carries)).
   A write there that declares none, or less, is refused with
   `CONTENT_SCOPE_LOWERED`
   ([`architecture/content`](../architecture/content.md#a-scope-only-rises)).

A repository that is not declared accepts no write, so install never writes
into a store ahead of its declaration.

**Install is a person's act.** Step 2's declaration carries a `scope_floor`,
which needs `content:decide` beside `content:declare`, and step 3's writes
need `content:write`, and both are *person only*. The content service takes
them only on a pass addressed to it, which the tenant's admin gateway obtains
for each of the person's requests, naming every capability that request needs,
and which carries only those the person may use when it is exchanged
([`architecture/content`](../architecture/content.md#who-may-move-an-entry);
[`architecture/admin`](../architecture/admin.md#contracts),
`admin-gateway-authorization`). So whatever installs a programme sends steps 2
and 3 through the admin gateway on the token of the person installing it, and
step 1 too wherever that declaration carries a `scope_floor`, as an adoption
of a store that keeps history must. A service
or an agent that installs on its own declares nothing that carries a floor
and writes nothing: it stages each document as a proposal
(`content:propose`) into a repository a person has declared, and a person
decides them. Until a person does, the programme is not installed, and
install reports so rather than reporting success.

Placed anywhere else, every write to a record holding `pii` is refused with
`CONTENT_RECORDS_REPOSITORY_REQUIRED` from the moment the repository it sits in
is declared, and the obligation that records into it records nothing. A row written before the record moved stays in the
history of the store it was written in. An environment profile that only
audits `restricted`
([`patterns/scope`](../patterns/scope.md#environment-profiles)) does not
postpone any of this: the rows are about real people whatever the profile
says.

What installing a programme owes is checked by the
[Installation Checklist](#installation-checklist), not by the checklist for a
programme's files.

---

## The closed vocabularies

**This is the section that earns the document.** Each vocabulary below is closed
in the engine, and a phrase outside it does not stop the file loading. It loads,
looks right in review, and is then reported as *undeclarable* somewhere a pack
author is not looking — or, worse, produces a number that is wrong in the
flattering direction.

### `applies_to` — where each occurrence is expected

| accepted | means |
|---|---|
| *(omitted)*, `the organisation`, `organization`, `org`, `company`, `business`, `tenant`, `programme`, `program`, `whole` | one occurrence, at the scope the artifact lives in |
| `each workspace`, `workspaces`, `each project`, `projects` | one occurrence **per workspace** in scope |

Determiners are stripped before matching, so `each workspace`, `every workspace`,
`all workspaces` and `per workspace` are one declaration written four ways.

**`each workspace` is the spelling to use.** `each project` is an accepted alias
and is not going away — ids are what records join on and must not move — but the
word is doing two jobs and only one of them is this one. A **workspace** is the
placement level in the platform's own tree: tenant → organisation → workspace,
the unit that carries sources, standards and visibility. A **project** in a
construction programme is a job site, and the organisation keeps those as rows in
a register. Writing `each project` and meaning the second is the most expensive
mistake this document can prevent.

If what you mean is "one per job site", "one per vehicle", "one per ward", the
declaration you want is [`per`](#per--one-occurrence-per-period-per-subject) —
not this field.

**`each crew`, `each shift` and `each site` are refused.** Not because they are
unreasonable, but because a *place* in this model is a tenant, an org or a
workspace — there is no fourth axis for them to expand along — and accepting one
would mean quietly mapping somebody's concept onto ours.

Refused, not defaulted, and the reason is measured. A daily assessment written
`applies_to: each crew` once read as "the organisation" and expected **one**
record a day for the whole company. Twenty crews file twenty records, one of
them discharges the single expected occurrence, and the programme reports one
hundred per cent while nineteen twentieths of the work is invisible. Not a gap —
a false clean bill.

**The workaround is not "write `each project`"**, which silently discards the
distinction in exactly the same way — two crews on one site become one record a
day for the site, and fourteen sites in one workspace become one record a day for
the company. Expand on the thing instead:

| what you mean | how to say it |
|---|---|
| one per job site, vehicle, ward, vessel — things the organisation keeps a register of | `per:` over that register |
| one per crew per day, one per incident, one per certificate | `for:` over a register with one row per piece of work |
| one per department, division, business unit — things that are *placements* | `applies_to: each workspace` |

The first two arrive through the data rather than through a taxonomy this product
would have to invent and somebody would have to maintain.

### `cadence` — how often

| accepted | period |
|---|---|
| `day`, `daily`, `1d` | daily |
| `working day`, `work day`, `workday`, `business day`, `weekday` | each working day |
| `week`, `weekly`, `1w`, `7d` | weekly |
| `month`, `monthly`, `1m` | monthly |
| `quarter`, `quarterly`, `3m` | quarterly |
| `year`, `yearly`, `annual`, `annually`, `1y` | annual |

A leading `every ` or `each ` is stripped, so `each quarter` and `quarterly` are
the same declaration.

Anything else is **refused rather than guessed**. Inventing "probably monthly"
would produce expected records nobody ever agreed to, and then a compliance
figure derived from an assumption the author never made.

### `authority` and `interval_basis` — whose interval is it

`each month` is two different statements depending on where the month came from,
and a product that renders them identically eventually tells an auditor that a
preference is a requirement.

| `interval_basis` | means |
|---|---|
| `required` | the `authority` sets this interval |
| `chosen` | **this organisation** sets it. The `authority`, if one is cited, requires the activity and not the frequency |

Anything else is **refused at load**, quoting the word. A pack author who wrote
one believes the product is now saying whose interval this is, and accepting an
undefined word and then showing nothing would leave that belief intact and wrong.
Case is folded before matching, so `Required` and `required` are one declaration.

**Refused in a pack; read as unstated in a tenant's document.** The same unknown
word in the frontmatter of somebody's own procedure does *not* stop the file. It
is read as **unstated** — and it is not passed through either. A pack is content
this corpus governs, so a word nobody defined is an authoring mistake and the
file is skipped; a tenant's procedure is the customer's, and Studio is a client
of their repository rather than a validator of it. What a client may not do is
put a label nobody checked beside a due date, where a reader has no way to tell
whether `mandated` meant anything. So the asymmetry is in what happens to the
file, never in what the word is allowed to mean.

**Absent is absent.** An obligation that declares neither field is unaffected and
gains no default — not `chosen`, not "policy", not any word chosen on the
author's behalf. It renders as nothing at all, and that gap is itself worth
seeing: it means nobody has written down why this often.

**Two fields rather than one, because the two facts are independent.** A rule can
require an activity and set no interval whatsoever — "as often as is necessary" —
and the organisation's answer is a month it picked. Both halves are true at the
same time, and one free-text field can only hold them as a sentence something
downstream would have to read:

    obligation:
      activity: A recurring check
      cadence: each month
      authority: Reg. 213/91 s. 11      # requires the check
      interval_basis: chosen            # …but not monthly. That is ours.

`authority` is **free text and is never parsed, validated or resolved** — the
same posture as `retention.authority`, for the same reason. `satisfies` is
strictly `framework:control` because it is a claim against a framework this
platform holds; an authority is a reference to something outside it, written the
way its own world writes it, and checking one would mean holding a list of which
rules exist.

The basis says nothing about **consequence**. Whether lateness invalidates
something, or is simply a breach, belongs in the text of the artifact that cites
the rule. The platform does not grade citations; it only refuses to confuse an
interval somebody was given with one somebody picked.

The same pair applies to a `for:` obligation, whose interval is the `due`
deadline rather than a cadence.

### `for.due` — the deadline on a triggered record

    <n><h|d|w> (after|before) <field>

`3d after reported_on` · `24h after reported` · `30d before expires_on`

Hours, days and weeks only. `<field>` may name the column by its **key or its
label**: a pack declaring `{key: expires_on, label: Expires on}` may write
either, because the rendered header carries the label and a later label edit
would otherwise break the trigger silently — no rows found, and an obligation
producing no occurrences looks exactly like one with nothing due.

### `escalate.after` — how long past due

    ^\d+\s*(h|d|w)$

`48h` · `7d` · `2w`. **Deliberately no months.** "Escalate after 1 month" past a
three-day deadline is not an escalation path, and a vocabulary that allows one
invites it.

Anything else is **silently inert**, which is the one refusal in this schema that
is not reported anywhere — see the table at the end of the next section.

### `retention.keep` — the keeping period

`<n>y` · `<n>m` · `<n>d`, written the way a records schedule writes it. Never a
Go duration.

### The single-valued ones

| field | the only accepted value |
|---|---|
| `layout` | `form` |
| `review` | `required` |
| `approval_order` | `sequential` |

Each is single-valued because there is exactly one behaviour behind it today.
They are declared as words rather than as booleans so a second behaviour is
additive.

---

## The rules that are load-bearing

**A citation is `framework:control`, strictly parsed, and an unparseable one
rejects the whole spec.** A citation is a compliance claim; one that cannot even
be parsed is a claim nobody can check, and admitting it would put an
unverifiable assertion into the evidence chain where it reads as a verified one.
One colon exactly; neither half may be empty. This applies to `satisfies` on the
spec and on the obligation alike.

Note what is *not* checked at load: the framework and control are **not resolved
against the corpus**. An artifact may cite a standard this installation has not
installed — that is a different report, not a malformed file. Neither
`conforms_to` nor `domains` is resolved either.

**`cadence` and `for:` are mutually exclusive.** An obligation is on a schedule
or on a set of records. Declaring both is a contradiction reported as
undeclarable rather than resolved by preference — which clock wins is not the
platform's to decide.

**A `declares.register` requires an obligation that names `records:`.** The
register's path *is* the obligation's `records`, so a register declared without
one has nowhere to go, and a register declared with no obligation has nothing
writing into it. An independently-citable register is authored as its own
artifact with `kind: register` and its own `path`.

**A trigger register must differ from the register the work is recorded in.**
The engine asks whether the trigger row's key appears in the obligation's own
register; when they are the same file the answer is trivially yes for every row,
so **every occurrence discharges itself at the moment it is created** and the
programme reports one hundred per cent having checked nothing. The shape that
works is two registers: incidents trigger investigations, controlled documents
trigger reviews. A register carrying its own next-due date wants a `cadence`, or
a second register to record the work in.

**A chain of triggers terminates in a cadence.** Each link is triggered by a row
in the register before it; the last link is a periodic sweep of what is open and
late, for the same reason.

**No two artifacts may produce the same document.** A declared register
colliding with an authored artifact at the same path — or with another pack's
declared register — is reported. One would overwrite the other, and the losing
obligation could never record anything.

**An obligation writing into a document nothing produces is reported.** Measured
across both shipped packs before this was enforced: **nine obligations out of
nine** named a `records:` document no artifact created. Nobody was ever asked to
create them, every occurrence had nowhere to be recorded, and the operating
number was pinned at zero by the pack format rather than by the organisation's
conduct.

**`approved_by`, `responsible`, `approvers` and `escalate.to` all name positions,
never people.** People change jobs and the duty does not.

### Which mistakes stop the file, and which do not

| refused at load — the file is skipped and reported | accepted at load, reported later as **undeclarable** |
|---|---|
| a spec with no `id`; a map with no `id` | an unreadable `cadence` |
| an unparseable `satisfies` citation | an `applies_to` outside the vocabulary |
| an obligation with no `activity` | `cadence` **and** `for:` together |
| an `interval_basis` outside `required`/`chosen` | — |
| a self-requiring artifact, or a cycle | a `for:` with no `records`, or an unreadable `due` |
| a register with no columns, a duplicate column `key`, a `relation` with no `target` | a trigger register that is also the recording register |
| `layout`/`review`/`approval_order` outside their closed set, or without what they need | — |
| a `retention.keep` that is not whole years, months or days | a `retention.from` naming an event not yet recorded |
| a tier declared twice, requiring an unknown tier, or in a cycle | — |
| an artifact placed at an undeclared tier | an artifact placed below something it requires *(reported against the map)* |
| a `register:` schema on an artifact whose `kind` is not `register`, or with no `path` | — |
| an `artifact_scope` or a column `scope` that is not a `ScopeLevel`, or `custom_labels` with no level declared beside them | — |
| a `creates` with no `template` or `path`, a `template` naming no form in the programme, or a `path` missing the `{key}` or `{date}` its obligation needs | — |

The right-hand column is the one to read twice. Those mistakes produce a file
that loads, renders and reviews cleanly, and are discovered when somebody asks
why a programme reports nothing due.

**And one mistake is in neither column.** An `escalate.after` that does not
parse — or an `escalate` with no `to` — is not refused and is not reported. The
occurrence simply never escalates, which is indistinguishable from an obligation
that declared no escalation at all: overdue work stays the problem of whoever has
already not done it, and nothing on any screen says the path exists and cannot be
read. Write it as `<n>h`, `<n>d` or `<n>w` and check it, because nothing else
will.

---

## `operations` — the standing work a programme installs

A programme that declares thirty-six obligations and nothing that RUNS has
handed the organisation a filing system and a hope. `operations:` on the
programme map is the standing machine work adopting the programme takes on: the
sweeps, the checks, the passes. Installing the programme creates them as real
schedules; they are visible in the product, each one named, with its clock, its
reason, and what it may touch.

**Measured before this existed.** A live installation running a programme with
thirty-six obligations held **one** scheduled job, typed in by hand months after
the documents landed. Nothing in the programme said one was needed, and nothing
in the product said it was missing.

### What is declared here, and what is deliberately not

The *need* for a due sweep is **derived, not declared**, and stays that way. A
programme with obligations needs chasing by construction; a second statement of
that fact in a file would disagree with the first the moment somebody changed
one. Studio's `program_chasing.go` reports a programme nothing is chasing and
offers a schedule, whether or not this block exists.

What derivation cannot answer is everything *else* about the work:

- **when** — 06:00 is right for a crew dispatched before seven and wrong for an
  office, and a derived sweep has to pick a number on the author's behalf;
- **what else** — that sub-trade clearance certificates want a weekly look of
  their own, separate from the daily sweep, is a judgement about an industry;
  identically shaped obligations in a hospital's medication regime produce a
  different answer;
- **what it may touch** — an operation that runs a model must say so, because
  the alternative is that it inherits whatever the scheduler holds.

So a programme with no `operations:` at all is valid and unchanged. This block
adds what a programme knows and the engine cannot infer.

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | stable and local to the programme. An installed schedule is matched back to it, so installing twice does not create the work twice |
| `title` | string | no | what a person reads in the schedule list. Defaults to `id` |
| `does` | string | conditional | a **deterministic action** the platform runs. Mutually exclusive with `agent` |
| `agent` | string | conditional | an instruction for a model, in the author's own words. Mutually exclusive with `does` |
| `needs` | string[] | no | the capabilities the agent may use — a **closed set**, below. A ceiling, never a grant |
| `schedule` | mapping | conditional | the clock — `{cadence, at, weekday, day}`, below |
| `on` | string[] | conditional | the events it reacts to — a **closed set**, below |
| `why` | string | no | prose for whoever finds this running at three in the morning and wants to know who asked for it |
| `start` | enum | no | `paused` (default) or `running` |

An operation needs **a `schedule`, or an `on`, or both**. Both is the useful
combination: react when something lapses, and sweep anyway in case the event was
missed while the server was down.

### `start` defaults to `paused`, and that is the design

A schedule runs unattended and sends people work. An install that started doing
that would be acting on a cadence the organisation never chose — the same
refusal Studio already makes when it *offers* a due sweep rather than creating
one. What changes is that the offer is now concrete: the work **exists**, named,
with its schedule and its permissions on screen, and starting it is one switch
instead of a form somebody has to fill in from nothing.

`start: running` is available and no shipped programme uses it. Writing one is a
decision to have adoption change an organisation's behaviour the same day.

### `does` names an action the platform has, and the list is the platform's

The vocabulary is **not restated here**, deliberately, and not held in the
programme loader either: it is the engine's own list of scheduled actions, and a
second copy in a schema is a second answer about what can run. An operation
naming an action a build does not have is **reported by name, with the
alternatives**, at the point of install — never silently skipped, because a
skipped operation presents as a programme that installed and produced less
standing work than it declared, with nothing anywhere saying so.

At the time of writing the engine runs `due-sweep`, `compliance-scan`,
`coverage-analysis`, `impact-analysis`, `gap-analysis`, `evidence-scan`,
`validate-blueprints`, `generate-policies`, `standards-drift`,
`standards-verify`, `programme-readiness` and `drift-prepare`. Ask the
installation (`GET /api/jobs/actions`) rather than trusting that sentence.

### `needs` is a ceiling on an agent, and is refused beside `does`

The closed set is `read`, `write`, `delete`, `integrations`, `dispatch`.

**Empty means read, and nothing else.** An author who forgets a capability gets
an operation that cannot do the thing and will notice; the other default gives
them one that can do everything and nobody will.

It is a **ceiling**, not a grant. What the run actually gets is this
∩ the agent's own declaration ∩ what the identity underneath may do, so a
programme can never hand an agent authority the agent did not ask for.

A capability outside the set **stops the file**, quoting the word. Dropping it
would leave the author believing the operation was permitted to do something it
cannot — and the mirror case, a word nobody checked being honoured, would give
an operation more authority than the programme asked for.

**`needs:` beside `does:` is refused.** A built-in action's authority is the
action's own; a declaration there would be read by nothing, and whoever wrote it
would believe the action was bounded by it.

Three things no capability grants, at any authority: **attesting or signing**
(the whole obligation model rests on automation being unable to produce one),
**changing its own authority**, and **silent egress**.

### `schedule` — a small closed vocabulary, and not the obligation's

| field | required | accepted |
|---|---|---|
| `cadence` | **yes** | `hourly` · `daily` · `weekly` · `monthly` |
| `at` | required except `hourly` | `HH:MM`, 24-hour, in the installation's local time |
| `weekday` | required for `weekly` | `monday` … `sunday` |
| `day` | required for `monthly` | 1–31. A day past the end of a short month lands on that month's last day |

**Deliberately not the same words an obligation's `cadence` uses.** They answer
different questions: an obligation's cadence is how often the *work* must
happen, and this is how often the *machine looks*. Sharing the vocabulary would
invite an author to write `each working day` here and get a silently different
clock.

`once` is absent on purpose. A programme declares *standing* work; installing it
twice would otherwise produce two one-off tasks with nothing to say they were
the same intention.

**A weekly cadence with no `weekday` is refused**, and a daily, weekly or
monthly one with no `at`. The scheduler refuses both outright, so a declaration
without them is one that could never be installed — and the refusal belongs
against the file rather than against the operator who tried.

### `on` — reacting to a fact instead of to the clock

The allow-list is `obligation.due_soon`, `obligation.overdue`,
`obligation.escalated` and `attestation`. It is an allow-list rather than a free
string because dispatching an agent emits events of its own: a job triggered on
machine chatter re-triggers itself, forever, spending money each time.

`register.row_added` is **not** in it, and may only be *counted* — see `when:`.
It fires once for each row a save adds to a document whose frontmatter says
`kind: register` (an incident, an inspection finding, a corrective action), and
carries the register's path, the row's key and the row's columns. A row that is
**edited** emits nothing: the question these events answer is what has happened,
and a correction to last week's entry is not a new incident.

Reacting to each one is refused for the reason the list exists. An agent can
*write* a register row — it stages one, an approval lands it — so an operation
subscribed to every row that records a corrective action records one, hears
about it, and records another. `on:` also has no way to say *which* register, so
"react to incidents" is unsayable; the closest is "react to every row in every
register", which is the loop. A counted condition names the register and latches.

A burst **coalesces** — a sweep that finds forty lapsed obligations emits forty
events and the job runs once — and the instruction the agent receives says so.
An agent that believed it was handling a single item would report on one of
forty and read as complete.

### `when` — reacting to HOW MUCH happened

`on:` fires on each occurrence, which is right for a lapse and wrong for a
pattern. *"Alert me any time more than one type of incident occurs across
projects"* is not a list of event names at all: it needs a count, a count of
**distinct** values, a **window**, and the **level** the counting pools at.

```yaml
when:
  - event: register.row_added
    where: {register: registers/incidents.md}
    within: 7d
    across: org
    count: {distinct: type, at_least: 2}
```

| field | required | accepted |
|---|---|---|
| `event` | **yes** | any `on:` event, plus `register.row_added`. Nothing outside that closed set |
| `where` | no | exact, case-insensitive matches against the event's fields. Empty counts every event of the type |
| `within` | **yes** | `<n>h`, `<n>d`, `<n>w`, up to `90d` |
| `across` | no | `project` (default) · `org` · `tenant` — the level events are pooled at |
| `count.distinct` | no | an event field whose **distinct values** are counted, instead of the events |
| `count.at_least` | **yes** | the threshold, inclusive. "More than one" is `2` |

**It fires on the edge, once.** The moment the count crosses the threshold, and
not again until the window has emptied back below it. A condition that
re-announced the same pattern on every subsequent event is the alert people
learn to filter — the same reasoning notices follow, where a stage is announced
when it *advances* and not while it merely persists.

That latch is also the loop guard. A register row can be written by an agent, so
a job reacting to a row whose agent writes a row would otherwise re-trigger
itself; a latched condition cannot, because the count only goes up.

**`across` is not a way to see more than the operation's own scope.** An
operation only ever observes events at or below where its programme is
installed. `across` says how the events it can *already* see are bucketed —
`org` pools every project together, `project` counts each one separately. A
programme is installed at an organisation ([Adopting a
programme](#one-act-by-a-person-at-the-organisation)), so an operation sees its
organisation's events and those of every project under it, and `across: tenant`
asks for more than that: it is **refused at install**, naming the level, because
the alternative is one organisation's events in a tenant-shaped bucket reporting
a pattern it looked at a fraction of.

**A condition that cannot be evaluated says so.** `distinct:` naming a field no
event carries counts zero forever, and zero renders identically to "nothing
happened". The installation emits one warning naming the operation, the field
and the event type, and says the condition will never fire while that is true.

**`within` is capped at 90d** because the installation remembers one observation
per event for the whole window. A question about a year is a question about a
trend, and a register's own counts answer that from its bytes with no state at
all.

### The refusals

| refused at load — the file is skipped and reported | reported at install, naming the operation |
|---|---|
| an operation with no `id`, or two with one `id` | a `does:` this build does not have |
| neither `does:` nor `agent:`, or both | an `on:` event outside the allow-list |
| no `schedule`, no `on:` and no `when:` | a `when.event` outside the allow-list |
| a `when` with no `event`, a `within` that is not `<n><h\|d\|w>`, an `across` outside `project`/`org`/`tenant`, or a `count.at_least` below 1 | a `when.across` broader than the level the programme is installed at |
| a `within` longer than `90d` | — |
| a `cadence` outside the closed set | — |
| `weekly` with no `weekday`; a missing or malformed `at`; `monthly` outside 1–31 | — |
| a `needs:` capability outside the closed set | — |
| `needs:` beside `does:` | — |
| a `start:` other than `paused` or `running` | — |

The right-hand column is at install rather than at load for one reason: what a
*build* can run is not a property of the file. The same programme is correct on
a newer installation and short of an action on an older one, and refusing the
file would make a programme unreadable rather than partly installable.

---

## The package — what a programme brings besides its documents

Adopting a programme creates more than documents: the standing work, the
multi-step work, who is told what, the skills its people and its agent work
read, and any domain service it needs built. **The map is the package
manifest.** Nothing else lists the pieces, because a second list would
disagree with the map the first time either changed.

**Every block names the tenant service that owns it**, so that adoption knows
where to send it and nothing is held by a client. The owner is fixed by the
block, not chosen per entry:

| block | owned by | run or held by | what adoption asks of the owner |
|---|---|---|---|
| specs, forms, `skills` | content | content | write each file into the adopting scope's repository ([Adopting a programme](#adopting-a-programme)) |
| `operations` | the programme service | execution fires the clock and the events | install each, paused unless it says otherwise |
| `workflows` | the programme service | execution holds the definition's runs, waits and timers | install each definition, paused unless it says otherwise |
| `notices` | the programme service | notification delivers, by position, each person their own way | install each |
| `agent:`, in an operation or a workflow step | the programme service records it | the prompt worker runs it through the model service, under the step's ceiling | nothing more: it is an instruction, never a component |
| `domain_services` | the domain controller, once built | it registers with the orchestrator like any other component; execution runs its workflows | nothing: adoption reports each as requested, and a person starts its build |

These are the tenant services of the tenant service architecture the owner approved on 2026-10-05, recorded in Weblisk Studio's `TENANT_RUNTIME_MAP.md`; no document in this corpus states it yet. **None of the programme service,
execution, notification, the model service, the prompt worker or the admin
gateway's decision inbox is specified in this corpus yet**, and a tenant today runs none of them, so adopting can create documents
and nothing else. An adoption reports every block it could not hand to its
owner, by name, with the service that is missing — never a smaller programme
presented as a whole one.

**What reads these blocks today.** Studio's programme loader reads
`operations`; it reads none of `workflows`, `notices`, `skills` or
`domain_services`, and the YAML decoder discards a key it cannot place. A map
carrying one loads, and the block is dropped. So whatever adopts a programme
MUST read the map's keys itself and report every block it does not act on, by
name, as not installed.

### Agents are instructions, never components

A programme gets machine help one way: an **`agent:` instruction**, in the
author's own words, on an [operation](#operations--the-standing-work-a-programme-installs)
or a [workflow step](#workflows--multi-step-work-with-waits-and-approvals),
under a `needs:` ceiling. The tenant's shared prompt worker runs it. A model is
a worker and never an owner, so an agent keeps no state of its own: what it
produces is written through an owner's API, as a proposal where the owner
requires one.

**There is no `agents:` block, and a programme never asks for an agent to be
generated or registered.** Expertise is data and authority is code: a
programme supplies the expertise as instructions and skills, and the authority
an agent runs with is the intersection of its ceiling, the worker's own
declaration and the identity underneath. An agent a programme could ask for
would be authority a programme granted itself.

**A domain service is not an agent request.** A domain service the programme
asks for ([below](#domain_services--a-domain-service-the-programme-asks-to-have-built))
is the one component a programme may ask to have built. Its blueprint names, in
`depends_on`, the work agents it dispatches to, as [`domain.md`](domain.md)
requires — and those must be agents that already exist: published in the
corpus's [`agents/`](../agents/README.md) or already running in the tenant. A
programme brings no agent blueprint for one, and a domain service depending on
an agent nobody publishes or runs is reported rather than built.

### `workflows` — multi-step work with waits and approvals

An obligation says a thing must happen, on a clock or per record. A workflow
says **how a piece of work moves**: a submission is reviewed, then approved,
then filed; an incident is triaged, investigated, and its corrective action
verified. Each step waits for the one before it, and some wait for a person.

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | stable and local to the programme. An installed definition is matched back to it, so installing twice does not create it twice |
| `title` | string | no | what a person reads. Defaults to `id` |
| `schedule` · `on` · `when` | — | conditional | what starts a run on a clock or a fact — the same three fields, vocabularies and allow-lists as an [operation](#operations--the-standing-work-a-programme-installs), with one event more on `on:`, [`adopted`](#adopted--one-off-work-adopting-owes). Any of them, or `for` |
| `for` | mapping | conditional | `{records}` — **one run per row added** to the named register, [below](#for--one-run-per-record). Mutually exclusive with `schedule`, `on` and `when` |
| `steps` | array | **yes** | at least one, below |
| `why` | string | no | prose for whoever finds a run waiting and wants to know who asked for it |
| `start` | enum | no | `paused` (default) or `running`, as on an operation and for the same reason |

Each step:

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | unique within the workflow. What a run records each step's outcome against |
| `title` | string | no | defaults to `id` |
| `task` | mapping | conditional | a person's work: `{activity, responsible, due}`. `responsible` is a **position**; `due` is `<n><h\|d\|w>` from the moment the step opens |
| `approval` | mapping | conditional | a decision: `{approvers, approval_order}` — **positions**, and `sequential` or omitted, as on a register |
| `does` | string | conditional | a deterministic action the platform runs, from the same list an operation's `does:` names |
| `agent` | string | conditional | an instruction for a model. Takes `needs:`, on the closed set and default an operation's has |
| `needs` | string[] | no | the agent's ceiling. Only beside `agent:` |
| `after` | string[] | no | the steps this one waits for. **Absent means the step listed before it**; the first step waits for nothing |
| `escalate` | mapping | no | `{after, to}`, on an obligation's closed form, for a `task` or `approval` step left open |

Exactly one of `task`, `approval`, `does` and `agent` on each step.

**A step that waits for a person announces itself.** A `task` or `approval`
step opening is told to its position by the step, so no notice is declared for
it, and a notice declared for one would tell the same person twice.

**A workflow decides nothing a person must.** An `agent:` or `does:` step may
prepare, check or propose. Approving and closing are decisions, and a decision
is an `approval` or `task` step a person completes: no `does:` action and no
`needs` capability lets a machine step approve, reject or close anything.
Separately, the three things no `needs` grants on an operation — attesting or
signing, changing its own authority, and silent egress — are granted on no
step either.

#### What starts a run

The two workflows above each begin with **one record** — a submission, an
incident — and the operation vocabulary cannot say that: `on:` refuses
`register.row_added`, and `when:` only counts it. A programme also owes
**one-off work** the day it is adopted — appoint the coordinator, post the
policy, run the first inspection — and `schedule` deliberately has no `once`.
So a workflow has two starts an operation does not.

##### `adopted` — one-off work adopting owes

`adopted` is an event on a workflow's `on:`, and only there. It fires **once,
when an adoption of this programme completes** at an organisation, and is heard
only by that programme's own workflows, carrying the programme's `id` and the
organisation.

It is safe to start work on because adoption is idempotent: a second adoption
under the same id [writes nothing](#adopting-twice-creates-nothing), so it
fires nothing, and taking an update is not an adoption and fires nothing
either. Un-adopting and adopting again is a new adoption, and fires it again —
the set-up work a returning programme owes is owed again.

**A workflow installed paused hears `adopted` when it is first started**: the
event is held for it, once, and delivered on first start. Workflows install
paused by default, and an event delivered to a paused workflow and lost would
mean the set-up work adoption owes never ran. Un-adopting discards an
undelivered one.

It is not on an operation's allow-list, because an operation is standing work
and set-up is not; a `does:` or `agent:` step in a workflow started by
`adopted` is how one-off machine work at adoption is declared.

##### `for` — one run per record

| field | type | required | means |
|---|---|---|---|
| `records` | string | **yes** | the register whose added rows each start a run. A path, resolved as every [path a spec gives](#where-a-record-holding-pii-lives) |

Each row added to that register starts **one run, carrying the row's key and
columns**. Rows are delivered one at a time and **never coalesced**: a burst of
twelve incidents is twelve investigations, and coalescing them — right for an
operation, which looks at a pile — would close eleven of them unexamined. A row
that is edited starts nothing, for the reason it emits nothing to an operation.

**Rows added while the workflow is paused are not lost.** Each is held and
delivered when the workflow is started, or, where it cannot be held, reported
as missed, naming the row. A row is never dropped silently: an incident added
while its workflow was paused and then forgotten is an investigation nobody
knows is owed.

This is safe where `on: [register.row_added]` is not, for the two reasons that
event is refused there. **It names the register**, so "react to incidents" is
sayable without reacting to every row everywhere. And **a run never starts
itself, directly or round a loop**: a row written by a run carries that run's
chain — the run and every run that, through `for`, started it. A row whose
chain already holds a run of workflow W does not start W. So a step of an
incident workflow that records a corrective action in another register may
start that register's workflow, once; and a step of that workflow writing back
into the incident register starts nothing, because its chain already holds the
incident workflow's run.

`for` is exclusive of `schedule`, `on` and `when` because a run per record and
a run per tick are different counts of the same work, and declaring both would
multiply them.

#### How a workflow maps onto `patterns/workflow`

[`patterns/workflow`](../patterns/workflow.md) is the authoritative workflow
declaration ([`protocol/types`](../protocol/types.md#workflows)), and
**execution runs `patterns/workflow` declarations** — there is no second engine
and no second format at run time. A programme's workflow is the author-facing
form, installed by the programme service as one `WorkflowDefinition`:

| a programme workflow | a `patterns/workflow` declaration |
|---|---|
| `id` | the workflow's name |
| `title`, `why` | `description` |
| `schedule`, `on`, `when`, `for` | `trigger` — the action the programme service invokes when the start fires |
| a step | a phase |
| step `id` | phase `name` |
| `after` (absent: the step before) | `depends_on` (absent: none) — written out in full at install |
| `does:` | a phase whose `agent` is the programme service and whose `action` is the named action |
| `agent:` with `needs:` | a phase whose `agent` is the prompt worker, its `input` the instruction and the ceiling |
| `approval` | a phase with `approval: required` |

Three things a programme workflow says have **no field in `patterns/workflow`
yet**, and are gaps in the pattern rather than licence for a second format:

- **`approval.approvers` and `approval_order`.** The pattern's approval gate
  waits for one decision event and does not say whose; the positions that must
  decide, and their order, have nowhere to go.
- **`task`, and its `due`.** The pattern has no phase that is a person's work:
  every phase names an agent and an action. A task step needs a phase that waits
  for a person and a deadline measured from when it opened, which a phase
  `timeout` in seconds does not express.
- **`escalate`.** The pattern fails a phase on timeout; it does not hand it to
  another position.

Until the pattern carries them, a workflow with a `task`, an `approval` naming
positions, or an `escalate` is reported at adoption as not installable, naming
the step — never installed with the step dropped.

### `notices` — who is told what

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | stable and local to the programme |
| `on` | string[] | **yes** | the events it tells about — the [`on:` allow-list](#on--reacting-to-a-fact-instead-of-to-the-clock) an operation uses, and nothing outside it |
| `to` | string[] | **yes** | the **positions** told. Never a person, and never a channel |
| `says` | string | **yes** | what the notice says, in the author's words. The notification service words the message from it |
| `why` | string | no | prose for whoever receives it and wonders why |

**Told once, when it advances.** A notice is sent when the fact it is about
first becomes true — an obligation turning overdue, an escalation — and not
again while it merely stays true. A notice repeated on every sweep is the
notice people learn to filter.

**How a person is told is theirs.** Email, chat, a digest or nothing outside
working hours is each person's preference, held by the notification service. A
programme names who and what, never how: a programme that chose the channel
would overrule every person it reached.

### `skills` — files the programme brings

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | unique within the programme. Never `map` |
| `file` | string | **yes** | the skill's file, under this programme's `skills/` directory, and never named `map.md` |
| `for` | string[] | no | the positions it is written for. Absent means it is read by this programme's `agent:` work |
| `why` | string | no | what it is for |

A skill is **a file and nothing more**: no identity, no store, no schedule. It
is delivered with the programme into content and read from there, by a person
holding a position it names or by the prompt worker running this programme's
agent work.

**Not the corpus's [`skills/`](../skills/README.md).** Those are builders'
skills, installed by a CLI verb and embedded in the CLI. A programme's skills
are for the people doing the work and for the agent work that helps them.

**Not a role brief.** What a position does under a programme is derived on read
from every programme the organisation adopted, and is never a file
([`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md), step 7). A skill is guidance a
derivation cannot reach, and is refused, as a position guide is, if it names an
artifact id or a register path — the two shapes that drift.

A skill file carries no `version:` of its own. A change to it is a PATCH on the
map that brings it, because a skill is guidance and changes nothing a tenant is
measured on.

### `domain_services` — a domain service the programme asks to have built

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | the domain controller's `name` — [`domain.md`](domain.md)'s rule, `[a-z][a-z0-9-]*`. Never `map` |
| `blueprint` | string | **yes** | its `type: domain` blueprint, at exactly `domains/<id>.md` in this programme |
| `why` | string | **yes** | what business logic the programme needs that operations and workflows cannot express |

`domains:` names the subject areas a programme operates in. A programme may
also need **business logic of its own** — entity context, scoring, rules over
its records — that no operation or workflow expresses. It asks for that as a
domain service: a domain controller
([`architecture/domain`](../architecture/domain.md)) built for the tenant from
a blueprint the programme brings.

**Asking is not building** — the reading of the owner's decision this schema
takes, **for the owner to confirm**. Adoption delivers the blueprint with the
programme and reports each domain service as *requested, not built*. A build is
a person's act, to be made through the CLI (`weblisk domain create`) on the
tenant's change cycle: it is model-written, at a build's cost, and the
component it produces registers like any other component. Adopting a
programme never starts a build, and un-adopting one never removes a component.
`weblisk domain create` cannot yet be pointed at a blueprint a programme
delivered ([Known gaps](#known-gaps)).

`why` is required because a domain service is the most expensive thing a
programme can ask for. A programme whose need is a sweep, a chain of steps or a
notice declares that instead.

### The package's refusals

| refused at load — the file is skipped and reported | reported at adoption, naming the entry |
|---|---|
| a workflow, notice, skill or domain service with no `id`, or two of one block sharing one | a workflow step's `does:` this build does not have |
| a workflow with no `steps`, or with none of `schedule`, `on`, `when` and `for` | an `on:` or `when.event` outside the allow-list |
| a workflow with `for` beside `schedule`, `on` or `when`; a `for` with no `records`; `adopted` on anything but a workflow's `on:` | a workflow step `patterns/workflow` cannot yet carry — a `task`, an `approval` naming positions, an `escalate` |
| a step with none, or more than one, of `task`, `approval`, `does` and `agent` | a block whose owning service the tenant does not run |
| a step `after` a step the workflow does not declare, or steps in a cycle | a domain service whose blueprint fails [`domain.md`](domain.md) |
| a `task` with no `activity` or `responsible`, or a `due` outside `<n><h\|d\|w>` | — |
| an `approval` with no `approvers`, or an `approval_order` other than `sequential` | — |
| `needs:` on a step that is not `agent:`, or a capability outside the closed set | — |
| a notice with no `on`, `to` or `says` | — |
| a skill whose `id` is `map`, whose `file` is not under `skills/`, is named `map.md` or does not exist, or which names an artifact id or a register path | — |
| a domain service whose `id` breaks the name rule or is `map`, whose `blueprint` is not `domains/<id>.md` or does not exist, or with no `why` | a domain service whose `depends_on` names an agent neither the corpus's `agents/` publishes nor the tenant runs |
| — | a domain service whose `port` is taken by another agent or domain the tenant runs, or by another domain service the same adoption requests — [`domain.md`](domain.md) requires a port unique across all agents and domains |
| an `agents:` block | — |

`responsible`, `approvers`, `to` and `escalate.to` name positions everywhere
here, as they do on an obligation.

---

## Adopting a programme

A programme is a template. An organisation **adopts** it when it is ready, and
adopting is the act that turns the template into the organisation's own:
documents in its repositories, standing work in its services, and a record of
exactly what was taken.

**A standard is adopted by the same act.** The rules below that are not about
a programme's files and blocks — that adopting is a person's act at an
organisation, the pin's per-file entry, adopting twice, updates arriving as
proposals, un-adopting — hold for a standard as written here, and
[`standard.md`](standard.md#adopting-a-standard) states only what differs: a
standard is never copied but generated for the organisation, as a link to the
published standard and the organisation's own adjustments. Every document,
obligation and register a programme's adoption creates against a control
records the control text it was made from, by the per-control digest
[`standard.md`](standard.md#outputs-cite-the-control-text-they-were-made-from)
defines.

### One act, by a person, at the organisation

- **Adoption is a person's act**, made through the tenant's admin gateway on
  that person's own pass, and recorded in the tenant's change log like any
  change. Nothing is adopted when a client starts, connects or upgrades. A
  service or an agent may propose an adoption; it never makes one
  ([Install is a person's act](#where-a-record-holding-pii-lives)).
- **Adoption is made at an organisation.** A project inherits every programme
  its organisation adopted, and is measured against it. A project does not
  adopt: an adoption asked for at a project is refused, naming the
  organisation, and a project that needs a programme its organisation lacks
  asks for an organisation adoption.
- **A project refines what it inherits** by keeping, in a repository at its own
  scope, a map or spec with the same `id`. It replaces the organisation's for
  that project only, in place, as any override does
  ([The programme map](#the-programme-map)). A refinement carries no adoption
  record and is offered no update: it is the project's own document.

### What is written

Every file the map resolves to — the map, every spec it places and every spec
those require, every form a spec names, every skill file, every domain service
blueprint — is written into the organisation's programme repository under
**`programmes/<id>/`**, `<id>` being the template's id, at the path it has in
the template, **its bytes unchanged**.

**A file already at a path is never overwritten.** Adoption writes only where
nothing is. A file already there whose bytes are the template's is reported
*already there*; one whose bytes differ is reported *edited*, left exactly as
it is, and recorded in `resolved` with the template's digest, so it reads
`edited` from the first moment. Overwriting it would destroy somebody's work
in the name of setting things up. Nothing is added on the
way in, because the digest of the tenant's copy is how anyone answers *"has
this changed?"* with `sha256sum` and no parser. Records about a person go to
the records repository instead
([Where a record holding `pii` lives](#where-a-record-holding-pii-lives)).

Each block in the [package](#the-package--what-a-programme-brings-besides-its-documents)
is then handed to its owner. An adoption that stops part way reports every
file and block it did not write, and is never reported as adopted.

### The adoption record

One file per adopted programme, **`adoption.md`**, at the programme's own root
in the repository the programme was written into, beside its `map.md`. The
loader ignores it ([Three file kinds](#three-file-kinds-and-where-a-file-sits-decides)),
and it declares `kind: reference`, so it counts for nothing.

```yaml
---
kind: reference
programme: records-management
tier: conformant
source: weblisk-blueprints
extends:
  - …                      # the pin, exactly as in "What a tenant pins against"
---
```

| field | required | means |
|---|---|---|
| `kind` | **yes** | `reference` |
| `programme` | **yes** | the template map's `id`, **unchanged**. An adoption cannot rename a programme: there is no field or option that adopts one under an id of the tenant's choosing |
| `tier` | no | the tier the organisation is working to. Absent means none was chosen, and readiness is reported for every tier |
| `source` | **yes** | where the template was read from — a locator, never an identity. Nothing joins on it |
| `extends` | **yes** | one entry: the [pin](#what-a-tenant-pins-against), whose example is the one this record carries. `version` is the range, or `unversioned` for a template that declared none. `resolved` holds an entry for **every** file written, keyed by its path in the template |

Each `resolved` entry:

| field | required | means |
|---|---|---|
| `digest` | **yes** | `sha256:` and the hex digest of the bytes written |
| `version` | **yes** | the file's own `version:` when it was taken, or `unversioned` when it declared none. Never a number the file did not state |
| `revision` | **yes** | the source's commit the file was read at, as its full 40- or 64-character object name, or `none` where the source has no commit |
| `repository` | **yes** | the `id` of the content repository the file was written into ([`ContentRepository`](../architecture/content.md#types)) — the programme's repository, or the records repository for what [holds `pii`](#where-a-record-holding-pii-lives). The id, never a name or an address, because both move |

**Per file, because files move separately.** A digest alone says *that* a
template file moved, never how: classifying an update needs the version the
file had when it was taken beside the version it has now
([`version` and `version_hash`](#version-and-version_hash-are-not-alternatives)),
and an update a person takes for one file and declines for another leaves the
two at different versions and revisions. One `version` or `revision` for the
whole adoption would be wrong for one of them the first time that happened.

**Who and when are not fields.** The change that wrote the record records
both, in the repository's log.

**The record is written after the files, in the same sitting, by the same
person.** It records what was taken, not what is held: an edit to an adopted
file never touches it.

### Adopting twice creates nothing

**The key is the organisation and the programme's `id`** — the template's id,
which the adoption record carries unchanged. Before anything is written, every
`adoption.md` in the organisation's repositories is read, and an adoption whose
`programme` is the same id, or an id the template's map lists under `formerly`,
is the same programme.

- **Asked again under the same id,** it writes nothing and hands nothing to any
  owner. It answers *already adopted*, reporting each file as already there and
  each operation, workflow and notice as already installed. Repeating the act
  is safe because it does nothing.
- **Asked into another directory or another repository** at the same
  organisation, it is **refused**, naming the adoption that exists. Two
  adoptions of one template in one organisation are two copies drifting apart,
  each measured as the programme.
- **Asked under another id** is recognised **only through `formerly`**: a
  template published under a new id, whose map lists the old one, is the same
  programme and is refused or answered as above. Two templates with no
  `formerly` between them are two programmes as far as any tool can tell, and
  this schema claims no more. Once maps record `formerly`, nothing else is
  needed; until then, a renamed template is not recognised. `formerly` is not
  yet a field of this schema ([Known gaps](#known-gaps)).

### The tenant's copy is the tenant's

An adopted file is edited **in place**, through the content service, like any
document in the repository that holds it. Every edit is a recorded change in
the tenant's log. Adoption gives the publisher no say over the copy.

Three digests say where each file stands, and none needs a parser: the copy
now, its `resolved` entry's `digest`, and the template's file now. The entry's
`version` beside the template file's `version:` now classifies a `behind` or
`diverged` file's update.

| the copy, against `resolved` | the template, against `resolved` | state |
|---|---|---|
| same | same | `current` |
| same | moved | `behind` — an update is offered |
| changed | same | `edited` — the tenant's own version; nothing is offered |
| changed | moved | `diverged` — both moved |

A template that cannot be reached leaves the state `unknown`, never `current`.
The states are computed on a person's request, by whatever can read both sides,
and never stored.

### Updates arrive as proposals

- **A `behind` file is offered, never taken.** The offer is a content proposal
  into the organisation's programme repository, classified by the
  [hash and version](#version-and-version_hash-are-not-alternatives) and shown
  in the admin gateway's one decision inbox. `on_change.compatible:
  validate-and-adopt` means the proposal is validated before it is offered, and
  a person applies it. Nothing writes an update silently.
- **A breaking change needs a new range.** It is offered only once a person has
  widened `extends.version` to admit it.
- **A removed template halts.** Nothing is withdrawn or deleted on the
  publisher's account; the adoption is reported as having no template, and a
  person decides.
- **An update over an `edited` or `diverged` file needs a person to merge.** No
  tool merges one. The person takes the new file, keeps theirs, or edits theirs
  toward it, and the change that does it is in the log.
- **Taking an update replaces that file's `resolved` entry** — `digest`,
  `version` and `revision` — in the same sitting. A file a person kept keeps
  its old entry, so it goes on reporting the update it has not taken.

An update to a block is handed to its owner the same way, as a proposal a
person applies.

### Un-adopting

**Un-adopting is also a person's act.** The person removes `adoption.md`, and
in the same sitting the programme service withdraws the operations, workflows
and notices installed under it: they stop, and their withdrawal is recorded.

What the programme created stays. Documents and records are the
organisation's, held under their own retention, and removing one is a separate
act. A domain service that was built stays registered until a person retires it.
Adopting the same programme again later is a new adoption, which finds the
files already there and reports an edited one as `edited`.

---

## Known gaps

Stated because a schema that describes only what works teaches an author to
write something that is silently ignored.

**[`creates`](#creates--a-document-per-occurrence-not-a-row) is declared, and
the programme loader does not read it yet.** Studio's obligation engine reads
the field from a document's frontmatter; its programme loader's obligation type
has no place for it, and the YAML decoder discards what it cannot place. Until
the loader places it, a spec declaring it loads without its card — the fault
this schema requires a reader to refuse instead — so no shipped spec declares
it yet.

That failure mode is not hypothetical here. `for:` and `escalate:` were both
declared by packs and absent from the loader's type for a period, so prepared
programmes arrived with no trigger and no escalation path — an obligation with
no clock at all, correctly reported as undeclarable three layers from the cause.

**The package is declared, and nothing reads it or receives it yet.**
[`workflows`, `notices`, `skills` and `domain_services`](#the-package--what-a-programme-brings-besides-its-documents)
are declared here, each with its owning service. No loader reads them, no
validator checks them, and no tenant runs the programme service, execution or
notification that would receive them, so no shipped map declares one yet. **Who
holds a position** stays configured by hand: it is tenant data, and belongs to
the customer rather than to a programme.

**No content entry records the run that wrote it**, so the chain
[`for`](#for--one-run-per-record) relies on to stop a loop is not carried by any
specified service yet.

**No workflow with a person's step is installable yet.** An `approval` naming
positions and a `task` have no field in `patterns/workflow`
([How a workflow maps](#how-a-workflow-maps-onto-patternsworkflow)), so a
workflow with either is reported at adoption as not installable — which today
is every workflow a person takes part in.

**`weblisk domain create` takes no blueprint path.** It is given a domain's
name and resolves the spec itself
([`architecture/cli`](../architecture/cli.md#weblisk-domain-create)), and
nothing says it looks in a programme's `domains/` in the tenant's content. So a
domain service a programme requests cannot yet be built from the blueprint the
programme delivered; the verb needs a way to be given one.

**`formerly` is not declared here yet.** [Adopting twice](#adopting-twice-creates-nothing)
recognises a renamed template only through the earlier ids its map lists, and
no map field lists them in this schema. Until one does, an adoption under an id
a template used to have is not recognised as the same programme.

**Nothing performs an adoption yet.** [Adopting a programme](#adopting-a-programme)
states the act, the record, the refusals and the update rule. No tool writes
`adoption.md`, computes the four states or offers an update, and a tenant whose
content service is not running cannot hold an adopted programme at all.

**An operation is created paused and nothing enables it.** That is deliberate —
see `operations` above — but it means an organisation that installs a programme
and never opens the schedule list has standing work that exists and does not
run. The product reports it as paused; nothing yet insists.

**`kind` is not validated against the declared kinds.** Packs in use carry kinds
that [`kinds.md`](kinds.md) does not declare, and nothing reports it. Kinds are
open data by design, so this may be correct; it is at least undecided, and an
author should not read the silence as approval.

**Nothing in the corpus carries a `version:` yet.** The field is declared
[above](#versioning), is read by the loader, and is reported when absent —
**0 of 12 maps and 0 of 222 specs declare one at `4778c25`**, so every one of
them is reported `unversioned` and nothing may be pinned against them. That is
the honest state and not a silent default. Versioning the corpus is a separate
act of authorship: each file opens at `1.0.0`, and every release after that is
classified against the tables above by the person making it.

**A programme map and an artifact spec are not declared kinds, and one of them
classifies wrongly.** [`kinds.md`](kinds.md) permits `extends` only
`blueprint → blueprint` and declares no kind for either file, so an adoption's
`extends` edge onto a programme would be skipped rather than recorded. Measured
through the one classifier: `programmes/<p>/map.md` and most specs fall through
to `document` (unclassified), but
`programmes/construction-ohs-ca/specs/cohs.policy.md` matches the `policy`
**filename** stem and classifies as a **policy** — a chain member with
`counts-as-coverage` and `opens-gap`. A *specification of* a policy would count
as the policy. Neither the missing kind nor the mis-classification is fixed
here; both are one row in `kinds.md`, and both must be settled before an
adoption's `extends` is built.

**No shipped register or form declares a scope yet.** Measured at `6aa4aa7`:
**0 of 222 specs** declare `artifact_scope` or a column `scope`, and **0 of 19
forms** carry `scope:` under `frontmatter:`. So every record
[Records about a person](#records-about-a-person) calls `restricted` — the
incident, first-aid, return-to-work, accommodation, credential and privacy
request registers and the incident report form among them — is created
unclassified, and nothing keeps it in a records repository, until its spec or
form declares one. Declaring them is authorship, one file at a time, each with
its version bump.

**`retention` is declared on a minority of registers.** Measured across the
shipped corpus: **71 of 204** registers declare a keeping period, every one of
them with an `authority` and a `reason`, and no policy domain now reports
`retention` as missing. The remaining 133 are the honest gap — they are
overwhelmingly registers whose period is genuinely somebody else's to set, and
an invented number on them would be worse than the absence. Where a period was
declared against no citation, the `authority` says so in those words rather
than naming a statute that does not exist.


---

## Verification Checklist

- [ ] The map is `map.md` at the programme's root, every spec is directly under `specs/`, every form directly under `templates/`, and nothing relies on a `type:` field to say which it is
- [ ] Every map and every spec carries an `id`, unique within the pack
- [ ] Every `version:` is `MAJOR.MINOR.PATCH` and nothing else — no `v`, no two-part number, no pre-release suffix
- [ ] A file with no `version:` is reported as **unversioned**, and nothing anywhere reads it as `1.0.0`
- [ ] Any edit this release makes that the [Versioning](#versioning) tables call MAJOR has a major bump beside it — most of all a moved tier boundary, a withdrawn `satisfies` entry, or a changed `declares.obligation`
- [ ] No file declares `pack`, `source`, `builtin` or `derived_from`
- [ ] Every `satisfies` entry is `framework:control` with exactly one colon and neither half empty
- [ ] Every tier's `requires` names a declared tier; exactly one tier has none; there is no cycle
- [ ] Every `artifacts[].tier` names a declared tier
- [ ] No artifact sits at a tier lower than something it `requires`
- [ ] Every artifact `id` a map places is defined by some spec in the pack, or is knowingly supplied by another
- [ ] Every obligation declares an `activity`, and a `cadence` **or** a `for:` — never both
- [ ] Every `cadence` is in the declared vocabulary; every `applies_to` is `the organisation` or `each workspace`
- [ ] Nothing says `each project` meaning *a job site* — that is `per:`, and the check is whether the organisation keeps a register of them
- [ ] Every obligation with `per:` records into a register carrying a relation column onto the subject register
- [ ] Every `interval_basis` is `required` or `chosen`, and every interval the organisation picked itself says `chosen` — an interval with a citation beside it and no basis reads as imposed
- [ ] Every `for.due` matches `<n><h|d|w> (after|before) <field>`, and `<field>` names a column of the trigger register
- [ ] Every operation has a `schedule`, an `on:` or a `when:`; every `when.within` is `<n><h|d|w>` and at most `90d`; every `when.across` is `project`, `org` or `tenant`; every `when.count.at_least` is 1 or more
- [ ] Every `when.count.distinct` names a field the declared `event` actually carries — for `register.row_added` that is a **column of the register named in `where`**
- [ ] Every `for.records` names a register **other than** the obligation's own `records:`
- [ ] Every `escalate` declares both `after` — `<n><h|d|w>`, no months — and `to`
- [ ] Every obligation names `records:`, and some artifact produces that document
- [ ] Every declared register has at least one column, with unique keys, and a `target` on every `relation`
- [ ] `review`, `approvers` and `approval_order` appear only with `layout: form`, and only with their declared values
- [ ] Every `retention.keep` is `<n>y`, `<n>m` or `<n>d`, and declares its `authority`
- [ ] Every `retention` on a register that is appended to says `from: modified`, and every `authority` either cites the instrument setting the period or says in words that none does
- [ ] `responsible`, `approved_by`, `approvers` and `escalate.to` name positions, no individual is named anywhere
- [ ] Every `artifact_scope` and column `scope` is a `ScopeLevel`, and every `custom_labels` sits beside a declared level
- [ ] No spec writes a top-level `scope:` to mean the document it creates; that is `artifact_scope`
- [ ] Every register whose rows are about a person — any row of which may record an injury to them or their health, a credential they hold, a complaint by or about them, the end of their employment, or a request about their own personal information — is `restricted` and labelled `pii` on each column about the person, and on its own spec when it is a standing register
- [ ] Every form whose document is about one person carries `scope: restricted` and `scope_metadata: {custom_labels: [pii]}` under `frontmatter:`, and no form carries a top-level `scope:` meaning the document it creates
- [ ] Every `creates` names a form in the programme's `templates/` and a relative `path` carrying `{key}` where its obligation has `per:` or `for:` and `{date}` where it has a `cadence` — and no shipped spec declares one until the programme loader places it
- [ ] No map declares `agents:`; every agent is an `agent:` instruction on an operation or a workflow step, with its `needs:`
- [ ] Every workflow has an `id`, a `schedule`, `on:` or `when:`, and at least one step; every step has an `id` and exactly one of `task`, `approval`, `does` and `agent`; every `after` names a declared step and no steps form a cycle
- [ ] Every `task` names an `activity`, a `responsible` position and a `due` of `<n><h|d|w>`; every `approval` names positions; no machine step approves, signs or closes anything
- [ ] Every notice names its `on` events from the allow-list, the positions it goes `to`, and what it `says` — and never a person or a channel
- [ ] Every skill's `file` is under the programme's `skills/` and exists, and names no artifact id or register path
- [ ] Every domain service names a `type: domain` blueprint under the programme's `domains/`, and says `why` an operation or a workflow would not do
- [ ] Every agent a domain service's blueprint names in `depends_on` is published in the corpus's `agents/` or run by the tenant, and its `port` collides with no agent or domain the tenant runs and no other domain service the adoption requests
- [ ] Every workflow starts on `schedule`, `on` or `when`, or on `for` alone; `adopted` appears only on a workflow's `on:`; and every step `patterns/workflow` cannot yet carry is reported at adoption rather than dropped
- [ ] Every operation declares an `id` unique within the programme, and a `does:` **or** an `agent:` — never both
- [ ] Every operation has a `schedule`, an `on:`, or both, and every `cadence`, `weekday` and `at` is in the declared vocabulary
- [ ] Every `does:` names an action the target installation actually runs — ask `GET /api/jobs/actions`, do not trust a list in a document
- [ ] Every `needs:` entry is `read`, `write`, `delete`, `integrations` or `dispatch`, and no operation declares `needs:` beside `does:`
- [ ] Every operation that runs a model states what it may touch, even when that is only `read`
- [ ] Every operation says `why:`, in terms that answer somebody who finds it running at three in the morning
- [ ] No operation declares `start: running` unless adopting the programme is genuinely meant to change behaviour that day
- [ ] Every artifact's body is a brief for **this organisation** — not the document itself, and not a recital of the standard
- [ ] Every `structure` a shipped spec or form names is the `id` of a file in [`structures/`](structures/), and every file there parses, has at least one section, repeats no title or alias and carries no `authority`

---

## Installation Checklist

What whatever installs a programme into a tenant owes. The
[Verification Checklist](#verification-checklist) above is for a programme's
files; these are acts of the tenant and the client that installs into it.

- [ ] The scope's records repository is found once, at install, as the repository `GET /v1/content/repositories` reports with `records: true` for that `scope_path`
- [ ] A register holding `pii`, and a document a form creates that holds `pii`, is created in the records repository, and nothing holding `pii` is created anywhere else
- [ ] Where the scope has no records repository, nothing holding `pii` is created, each register and form not created is reported with `CONTENT_RECORDS_REPOSITORY_REQUIRED`, and every obligation that records into one is reported as unable to record
- [ ] A register's `path`, an obligation's `records:`, a `for.records` and a `relation` column's `target` resolve in the records repository when the register named holds `pii`, and in the programme's repository otherwise, for install, derive and the occurrence engine alike
- [ ] The records repository, and the repository that holds the rest of the programme, are declared before install creates anything, and every document install creates is written through the content service's write route into the repository its path resolves to
- [ ] The declaration of the repository that holds the rest of the programme carries a `scope_floor` a person chose, and every write install makes into it declares on the change the higher of the level the spec or form gives the document and the floor
- [ ] The client writing a person's next change to a document created from a spec or a form adds `scope:` and `scope_metadata:` from the spec or form where the document lacks them, never on open, and never below the entry's recorded scope
- [ ] An install that copies a programme from a repository outside a tenant says with its answer that where the copy came from is not recorded in the tenant, because no field of `architecture/content` records it ([Repositories Outside a Tenant](../architecture/content.md#repositories-outside-a-tenant))
- [ ] An adoption is made by a person, at an organisation; one asked for at a project is refused, naming the organisation
- [ ] Every file an adoption writes goes under `programmes/<id>/` with the template's bytes and path, nothing already at a path is overwritten — a file there is reported *already there* or *edited* — and `adoption.md` is written after them in the same sitting, with `kind: reference`, `programme` (the template's id, unchanged), `source` and one `extends` entry whose `resolved` holds, for every file written, its `digest`, its own `version` or `unversioned`, the full `revision` it was read at, and the `repository` it went to
- [ ] A second adoption of the same programme at the same organisation writes nothing and answers *already adopted*; one into another directory or repository is refused, naming the adoption that exists; one under another id is recognised only through `formerly`
- [ ] Every block of the package is handed to its owning service, or reported by name with the service that is missing — never dropped
- [ ] An update is offered as a content proposal and applied by a person; none is taken over an `edited` or `diverged` file without a person merging it; an unreachable template reports `unknown`, and no state is stored
- [ ] Un-adopting removes `adoption.md` and withdraws the operations, workflows and notices installed under it, and removes no document, record or built domain service
