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
number.

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
| **MAJOR** | `id` changed · a tier removed or renamed · **any change to which artifacts a tier contains**, including moving one between tiers · an artifact dropped from the map · an `operations` entry removed or its `does` changed |
| **MINOR** | a new tier **above** the current top · an artifact placed at an existing tier · a new operation · a new `domains` or `conforms_to` entry |
| **PATCH** | `title` · `rationale` · the overview body · `order` |

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
| **MAJOR** | `id` changed · **an entry removed from `satisfies`** · **any change under `declares.obligation` other than the `activity`'s wording** — `cadence`, `applies_to`, `per`, `for`, `records`, `responsible`, `escalate`, `authority` · a register column removed, rekeyed or retyped · a `relation` target changed · `approved_by` gained or changed · `requires` gained · `kind` or `register.layout` changed |
| **MINOR** | an entry added to `satisfies` · a register column added · `template` first named · a new optional field |
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

### Unversioned is a real answer, and is never 1.0.0

A file that declares no `version:` is **unversioned**. It is not `1.0.0`, not
`0.0.0` and not "assume compatible". Nothing may be pinned against it, and an
adoption of it is describable only by content hashes.

This is the state of **every** programme file in this corpus today, and it is
reported rather than defaulted. Studio's loader (`internal/program/version.go`) reads the field, and
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
      map.md:              sha256:…
      specs/rec.policy.md: sha256:…
    on_change:
      compatible: validate-and-adopt
      breaking:   version-bump
      removed:    halt-immediately
```

The **range is the permission** — a compatible improvement flows in under
`on_change.compatible`. The **hash is the record** — it says exactly what was
taken, so *"did it move?"* is answerable without trusting that anyone bumped
anything.

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
  `version: unversioned` and its `resolved:` hashes. It is never back-filled to
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
| `domains` | string[] | no | the policy domains this programme operates in — the same catalogue the classifier uses, so a programme is measurable through machinery that already exists. Each one is defined in [`../policy-domains/`](../policy-domains/README.md), which also states **what claiming it requires**; a claim on a domain nothing declares is reported, and so is a claim nothing answers |
| `conforms_to` | string[] | no | the standard `id`s this programme is built to answer. **Context, not a constraint**: a programme with no framework at all is valid |
| `tiers` | array | no | the progression, below |
| `artifacts` | array | no | `{id, tier}` placements, below |
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
| `structure` | string | no | the document structure it is **checked** against — `policy`, `procedure`, `standard`, `guideline` are seeded, and a tenant may add or remove them |
| `path` | string | no | a **suggestion** for where the document goes. Required only for a standing register |
| `satisfies` | string[] | no | the controls this artifact answers, as `framework:control` |
| `requires` | string[] | no | artifact `id`s this one depends on — the DAG that orders generation |
| `template` | string | no | a doc template this organisation starts documents of this kind from. The **shape**, never the content |
| `approved_by` | string[] | no | the **positions** that must sign this artifact off before it is in force |
| `declares` | mapping | no | what creating this artifact also creates — `obligation` and `register`, below |
| `register` | mapping | no | the schema, when this artifact **is** a register. Requires `kind: register` |
| *body* | prose | no | the `brief` — what this document must establish for THIS organisation |

`pack`, `source`, `builtin` and `derived_from` are **set by the loader and may
not be claimed**, as on a map.

### `structure` need not be the same word as `kind`

A plan and a procedure share a shape. An organisation that has no "plan"
structure would otherwise see the checklist report a plan as having no expected
sections — **which reads as "this document is fine"**.

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
`org` pools every project together, `project` counts each one separately. An
operation installed at a project that asks to count across its org is **refused
at install**, naming the level, because the alternative is one project's events
in an org-shaped bucket reporting a pattern it looked at a fraction of.

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

## Known gaps

Stated because a schema that describes only what works teaches an author to
write something that is silently ignored.

**`creates:` is not in this schema.** An obligation discharged by filling in a
*document* rather than a register row — a card per site per day, with N hazards,
N signatures and N photos, which do not fit a cell — is expressible in the
engine as `creates: {template, path}`. **A pack declaring it has it silently
dropped**: the field exists only on the engine's own obligation type, and the
YAML decoder discards what it cannot place. Do not write it until this schema
says otherwise.

That failure mode is not hypothetical here. `for:` and `escalate:` were both
declared by packs and absent from the loader's type for a period, so prepared
programmes arrived with no trigger and no escalation path — an obligation with
no clock at all, correctly reported as undeclarable three layers from the cause.

**A programme can now declare its standing work, and not yet its people or its
forms.** `operations:` closes the scheduled half of what this gap used to
describe: sweeps, checks and event-driven passes are declarable, install with
the programme, and carry the capability ceiling they run under. What is still
configured by hand and still unannounced is **who holds a position**, **who is
notified**, and **the approval campaigns** a submission travels through. The
first of those is tenant data and belongs to the customer rather than to a
programme; the other two are `CORPUS_SHAPE.md` step 6's remainder.

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
- [ ] No spec declares `creates:`
- [ ] Every operation declares an `id` unique within the programme, and a `does:` **or** an `agent:` — never both
- [ ] Every operation has a `schedule`, an `on:`, or both, and every `cadence`, `weekday` and `at` is in the declared vocabulary
- [ ] Every `does:` names an action the target installation actually runs — ask `GET /api/jobs/actions`, do not trust a list in a document
- [ ] Every `needs:` entry is `read`, `write`, `delete`, `integrations` or `dispatch`, and no operation declares `needs:` beside `does:`
- [ ] Every operation that runs a model states what it may touch, even when that is only `read`
- [ ] Every operation says `why:`, in terms that answer somebody who finds it running at three in the morning
- [ ] No operation declares `start: running` unless adopting the programme is genuinely meant to change behaviour that day
- [ ] Every artifact's body is a brief for **this organisation** — not the document itself, and not a recital of the standard
