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

### Two file kinds, and the parent directory decides

    programmes/<pack>/programs/<programme>.md      a programme map
    programmes/<pack>/artifacts/<artifact>.md      an artifact specification

**The parent directory alone says what a file is.** A file directly under
`programs/` is a map; one under `artifacts/` is a spec; a file under anything
else is ignored entirely. The segment above those two directories names the
**pack**, so provenance survives the merge — "which pack claimed this artifact"
is the first question asked of a programme somebody did not write.

`<root>/programs/…` also loads, for a root that *is* a single pack. One rule
covers both shapes, so nobody has to learn a nesting depth.

A path convention rather than a `type:` field because a pack is a repository of
content: directories are what a person browsing one already sees, and a
discriminator field is a thing to get wrong in a file whose whole point is being
hand-authored.

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

## The programme map

One file per programme, under `programs/`.

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | stable identifier. What everything else cites, and what an override replaces |
| `title` | string | no | display name. Defaults to `id` |
| `domains` | string[] | no | the policy domains this programme operates in — the same catalogue the classifier uses, so a programme is measurable through machinery that already exists |
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

One file per artifact, under `artifacts/`. Standalone, and deliberately **not
nested inside a programme**: one training-record matrix serves several
programmes at once.

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | stable identifier. What a map places and what other specs `require` |
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
| `applies_to` | string | no | where each occurrence is expected — a **closed vocabulary**, below |
| `records` | string | no | the register each occurrence is written into. Empty means the platform cannot tell whether the activity happened |
| `satisfies` | string[] | no | the controls this activity answers, as `framework:control` |
| `for` | mapping | conditional | a **record-origin** trigger, below. Mutually exclusive with `cadence` |
| `escalate` | mapping | no | `{after, to}` — what happens when an occurrence stays overdue |

**An obligation with no `records:` is a statement that something must happen and
no way to tell whether it did.** That is worth saying — an unverifiable
obligation is a governance finding — and it is never counted as met.

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
| `each project`, `projects`, `workspace`, `workspaces` | one occurrence **per project** in scope |

Determiners are stripped before matching, so `each project`, `every project`,
`all projects` and `per project` are one declaration written four ways.

**`each crew`, `each shift` and `each site` are refused.** Not because they are
unreasonable, but because a place in this model is a tenant, an org or a project
— there is no fourth axis for them to expand along — and accepting one would
mean quietly mapping somebody's concept onto ours.

Refused, not defaulted, and the reason is measured. A daily assessment written
`applies_to: each crew` once read as "the organisation" and expected **one**
record a day for the whole company. Twenty crews file twenty records, one of
them discharges the single expected occurrence, and the programme reports one
hundred per cent while nineteen twentieths of the work is invisible. Not a gap —
a false clean bill.

**The workaround is not "write `each project`"**, which silently discards the
distinction: two crews on one site become one record a day for the site. It is
to expand on the *work* instead — a register with one row per crew per day, and
a `for:` trigger over it, which raises one occurrence per row. The same
expansion, arriving through the data rather than through a taxonomy this product
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

**A programme cannot declare the agents, workflows, tasks or forms it needs.**
Documents, obligations, registers, escalation and retention are declarable.
Positions the work is assigned to, notifications, scheduled jobs and approval
campaigns are not — they are configured by hand, per organisation, after the
documents land, and nothing tells anybody it needs doing. `CORPUS_SHAPE.md`
step 6 is that work.

**`kind` is not validated against the declared kinds.** Packs in use carry kinds
that [`kinds.md`](kinds.md) does not declare, and nothing reports it. Kinds are
open data by design, so this may be correct; it is at least undecided, and an
author should not read the silence as approval.

**`retention` is declarable and unused.** No shipped pack declares one, so the
path from a declared keeping period to a disposal date is exercised by tests
rather than by content.

---

## Verification Checklist

- [ ] Every file lives directly under a `programs/` or `artifacts/` directory, and nothing relies on a `type:` field to say which it is
- [ ] Every map and every spec carries an `id`, unique within the pack
- [ ] No file declares `pack`, `source`, `builtin` or `derived_from`
- [ ] Every `satisfies` entry is `framework:control` with exactly one colon and neither half empty
- [ ] Every tier's `requires` names a declared tier; exactly one tier has none; there is no cycle
- [ ] Every `artifacts[].tier` names a declared tier
- [ ] No artifact sits at a tier lower than something it `requires`
- [ ] Every artifact `id` a map places is defined by some spec in the pack, or is knowingly supplied by another
- [ ] Every obligation declares an `activity`, and a `cadence` **or** a `for:` — never both
- [ ] Every `cadence` is in the declared vocabulary; every `applies_to` is `the organisation` or `each project`
- [ ] Every `interval_basis` is `required` or `chosen`, and every interval the organisation picked itself says `chosen` — an interval with a citation beside it and no basis reads as imposed
- [ ] Every `for.due` matches `<n><h|d|w> (after|before) <field>`, and `<field>` names a column of the trigger register
- [ ] Every `for.records` names a register **other than** the obligation's own `records:`
- [ ] Every `escalate` declares both `after` — `<n><h|d|w>`, no months — and `to`
- [ ] Every obligation names `records:`, and some artifact produces that document
- [ ] Every declared register has at least one column, with unique keys, and a `target` on every `relation`
- [ ] `review`, `approvers` and `approval_order` appear only with `layout: form`, and only with their declared values
- [ ] Every `retention.keep` is `<n>y`, `<n>m` or `<n>d`, and declares its `authority`
- [ ] `responsible`, `approved_by`, `approvers` and `escalate.to` name positions, no individual is named anywhere
- [ ] No spec declares `creates:`
- [ ] Every artifact's body is a brief for **this organisation** — not the document itself, and not a recital of the standard
