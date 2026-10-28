---
family: schemas/family@1
version: 1.1.0
kind: reference
noun: position
match: [positions/*.md]
capabilities: [author, versioned, publishable]
template: templates/position.md
location: positions/*.md
generates: none
---
# Position Schema

Schema governing the files in [`positions/`](../positions/) — the **hand-written
half** of what the platform can say about a job somebody holds inside an
organisation: a site supervisor, a health and safety lead, a privacy officer.

Derived from the derivation, not written ahead of it. Every field below exists
because the projection over `programmes/` could not reach it.

> **A position file is not a declaration that the position exists.** Positions
> are declared by being named in a programme — in an obligation's `responsible`,
> an `escalate.to`, a register's `approvers`, an artifact's `approved_by`. This
> family is commentary on positions the programmes have already declared, and
> a file here for a position nothing names is **reported, never honoured**.

---

## Header

The family `schemas/position`, declared in **migration mode**
([`schemas/family`](family.md#definitions)): a guide's own `id:` is reported,
because its path is its id, and a missing `version:` is reported; any other
key the header does not declare is refused. [Frontmatter](#frontmatter) says
what each key means, and [Body](#body--a-closed-set-of-headings) why a heading
outside the set is refused. The strict variant, which refuses `id:` and
requires `version:`, waits for the migration (`v2-migrate`).

```yaml
header:
  schema:
    type: object
    unevaluatedProperties: false
    properties:
      family:        {const: schemas/position@1}
      version:       {$ref: "schemas/blocks#/$defs/version"}
      title:         {type: string}
      also_known_as: {type: array, items: {type: string}}
  required:
    version: report
  legacy:
    id: report
```

## Sections

```yaml
sections:
  undeclared: {policy: refuse}
  slots:
    - {slot: purpose, heading: What this job is for, required: false, use: instructs}
    - {slot: first-week, heading: Your first week, required: false, use: instructs}
    - {slot: good, heading: What good looks like, required: false, use: instructs}
    - {slot: failure, heading: How it goes wrong, required: false, use: instructs}
    - {slot: personal, heading: What you cannot hand to anybody else, required: false, use: instructs}
```

---

## Why there are two halves at all

Measured across `programmes/`, the corpus already knows, for every position:
which obligations name it `responsible`, how often each one recurs, where each
occurrence is recorded, what authority requires it, which registers it approves
submissions to, which documents it puts in force, what escalates to it and from
whom, and what it escalates away and how fast. How many positions, named how
often, is measured once, in
[`../programmes/README.md`](../programmes/README.md#the-positions-a-programme-names).

Writing any of that down a second time — in a role guide, in a skill, in a
handbook — produces a copy that is wrong the first time a programme changes,
and the wrongness is invisible because **both halves look right on their own**.
That is the failure this corpus names for `satisfies`/`implements`, that Studio
names for platform/provider/integration, and that the CLI's embedded-skill guard
exists to catch.

So the derived half is **never written down**. It is rendered on read, from the
programmes an organisation has actually adopted, at the tier it is actually
targeting — because *which programmes* and *which tier* are the two facts that
decide what the job is, and neither is knowable here. The same position id under
two programmes is two different jobs:

| | obligations owned | escalations arriving |
|---|---:|---:|
| `health-safety-lead` under `construction_ohs_ca` | 15 | 17 |
| `health-safety-lead` under `ohs` | 15 | 1 |

A file committed here would have to pick one. The only defensible pick — the
union of everything the corpus ships — is wrong for every real organisation and
overstates the job by about double.

## What a hand-written half is for

Judgement. What to do first. What a good version of this job looks like. How it
goes wrong. What the trade calls it. None of that is derivable from a programme,
and none of it changes when a programme does.

---

## Format

`positions/<position-id>.md` — Markdown with YAML frontmatter. Markdown for the
reason programme specs are: the valuable part is prose, and a paragraph inside a
JSON string cannot be reviewed, diffed or edited.

**The filename is the id.** A file declaring an `id` other than its own basename
is refused. The id is not merely a name: it is what obligations, escalations,
approvals and a tenant's own holdings all join on, and a guide whose id has
drifted from its filename is invisible to the loader and findable by a person,
which is the worst of both.

**A position id must not move.** Renaming one detaches every obligation that
names it and every holding a tenant has recorded against it.

**A guide names no one.** It is published content about the job in any
organisation, so it names no individual, and no tenant, customer or project.

## Frontmatter

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | the position id the programmes name. Equals the filename |
| `title` | string | no | display name. The renderer otherwise spells the id out, which is never wrong and often clumsy |
| `also_known_as` | string[] | no | the other words for this job. Genuinely not derivable, and the reason somebody searching for *HSE Manager* finds anything |

`source` is set by the loader and may not be claimed, for the same reason `pack`,
`builtin` and `derived_from` may not be claimed on a programme: provenance is a
property of where a file was found, not of its bytes.

**There is deliberately no `reports_to`, no `responsibilities`, no `programmes`
and no `seniority`.** Every one of those is already in the programmes:
`reports_to` is `escalate.to`, responsibilities are obligations, and which
programmes name a position is a projection. A field here for any of them would
be the second copy this family exists to avoid.

## Body — a closed set of headings

Five `##` headings, and no others. A heading outside the set is **refused**, not
ignored: the renderer places these in a fixed order, and a section it did not
recognise would be dropped without a word — which is a person's writing lost to a
typo in a heading.

| heading | answers |
|---|---|
| `## What this job is for` | the one paragraph somebody reads first |
| `## Your first week` | what to do, in order, before you know anything |
| `## What good looks like` | the signal the job is working, as opposed to being performed |
| `## How it goes wrong` | the failure modes, named, so they are recognisable in progress |
| `## What you cannot hand to anybody else` | which of the derived duties are personal, and why |

**Every section is optional.** A guide answering one heading and leaving four
blank is better than one written to fill slots. A section written to fill a slot
is the thing a reader learns to skip, and then they skip the one that mattered.

`## What this job is for` is rendered at the top, above the derived material;
the other four render beneath it.

## A guide may not restate derived fact

**Enforced at load.** A guide is refused when its prose contains:

- an **artifact id** — `ohs.policy`, `cohs.site-inspections` — the shape
  `<prefix>.<hyphenated-name>`
- a **register path** — `registers/site-inspections.md`

Those two and no others. Prose that says *"the monthly rhythm is the spine of
this job"* is a person writing about their work and must stay allowed; prose
that names an artifact has pinned itself to a programme and will be wrong the
next time that programme is edited, in a different file in a different family,
with nothing to notice.

The rule is enforceable precisely *because* the derived half is never written
down: there is no legitimate reason for those strings to appear in a
hand-written file.

## What the generator may do to these files

**Nothing.** It reads them and never writes one.

There is no merge, no managed region, no generated block with markers around it.
A generator that owns part of a file eventually owns the rest of it: the first
time somebody edits inside the markers, the tool either loses their work or
stops regenerating, and both failures are silent. The seam is a **file
boundary** — the derived half is not a file at all, and the hand-written half is
a file the generator only reads.

## What is reported rather than refused

| | |
|---|---|
| a position named by a programme with **no** guide | the brief renders, and says the judgement is missing rather than inventing it |
| a guide for a position **no** programme names | reported as an orphan: either an id typo, which silently detaches the commentary from the job, or a role dropped from every programme whose guide now describes work nobody owns |

Both are honest gaps. A brief that read complete while four of its obligations
recorded into nothing would have told the reader the opposite of the truth.

---

## Who holds a position

Neither half above says who holds a position in one organisation. That is a
fact about the customer's organisation, so it is the tenant's to hold and
never a client's, and it is held in one register this schema declares: the
**position-holders register**. A programme names positions; this register is
where a tenant service finds the people.

### The register

It is a standing register
([`programme.md`](programme.md#registers)) that no programme declares,
because every programme that names a position relies on it, and none of them
owns it.

| | |
|---|---|
| id | `position-holders` |
| path | `registers/position-holders.md` |
| repository | the organisation's **records repository**: the one `GET /v1/content/repositories` reports with `records: true` for the organisation's `scope_path` |
| scope | `restricted`, labelled `pii` |
| layout | a table |

**Its rows are about a person,** so it is `restricted` and labelled `pii`
([`programme.md`](programme.md#records-about-a-person)), and kept in the
records repository, the one repository
[`architecture/content`](../architecture/content.md#where-an-entry-labelled-pii-is-kept)
lets hold an entry labelled `pii`. Written anywhere else, it is refused with
`CONTENT_RECORDS_REPOSITORY_REQUIRED`, as every such register is.

**One per organisation.** A holding is recorded at the organisation, because
a programme is adopted at the organisation
([`programme.md`](programme.md#one-act-by-a-person-at-the-organisation)) and
its positions are the organisation's. A holding limited to one project names
that project in its row. A project keeps no register of its own.

**Its file is a register's.** A person creates it, through content, in the
organisation's records repository, and it is read by its columns' keys. An
organisation with no such entry has no holder for any position. Its spec is
the block below, which takes the fields
[`programme.md`](programme.md#registers) gives a register:

```yaml
register:
  title: Who holds each position
  note: One row for each time a person holds a position. A holding that ends is given its last day, and is never removed.
  artifact_scope: restricted
  artifact_scope_metadata: {custom_labels: [pii]}
  columns:
    - {key: holding, label: Holding, type: text, required: true}
    - {key: position, label: Position, type: text, required: true}
    - {key: holder, label: Held by, type: user, required: true, scope: restricted, scope_metadata: {custom_labels: [pii]}}
    - {key: project, label: Limited to project, type: text}
    - {key: first_day, label: First day, type: date, required: true}
    - {key: last_day, label: Last day, type: date}
    - {key: note, label: Note, type: longtext, scope: restricted, scope_metadata: {custom_labels: [pii]}}
    - {key: recorded_by, label: Recorded by, type: user, required: true}
```

| column | holds |
|---|---|
| `holding` | the row's key: 32 lowercase hex characters minted when the row is written, never changed and never reused. What a record of an act cites to say which holding it was made under |
| `position` | a position id, as the programmes name it ([Format](#format)) |
| `holder` | the person's identity id at the tenant: the id tokens and records name an operator by ([`protocol/types`](../protocol/types.md#operator)). Never a name or an address |
| `project` | the scope path of a project in the organisation. Empty, the holding covers the whole organisation |
| `first_day`, `last_day` | the first and last day held, both included, as calendar dates in UTC. An empty `last_day` is a holding that has not ended |
| `note` | why, for a reader who was not there. It may describe the person, so it is labelled as `holder` is |
| `recorded_by` | the identity id of the person who wrote the row: a person acting, not the person the row is about, so not labelled `pii` ([`programme.md`](programme.md#records-about-a-person)) |

The `PositionHolding` type is one row as a tenant service reads it:

```yaml
types:
  PositionHolding:
    description: One row of the position-holders register
    fields:
      holding:
        type: string
        required: true
        description: The row's key, 32 lowercase hex characters, never reused
      position:
        type: string
        required: true
      holder:
        type: string
        required: true
        description: The holder's identity id at the tenant
      project:
        type: string
        required: false
        description: The scope path of the one project it covers. Absent, the whole organisation
      first_day:
        type: string
        required: true
        description: The first day held, a calendar date in UTC written YYYY-MM-DD
      last_day:
        type: string
        required: false
        description: The last day held, included, written as first_day is. Absent while the holding has not ended
      note:
        type: string
        required: false
      recorded_by:
        type: string
        required: true
        description: The identity id of the person who wrote the row
```

### Resolving a position to its holders

Every tenant service that turns a position named by a programme into people
— notification for a notice's `to`, and whatever decides an `approved_by`, a
register's `approvers`, an `escalate.to` or a `responsible` — resolves it by
one rule, for a position, a day and a scope:

1. A row **covers the day** when its `first_day` is on or before the day,
   and its `last_day` is empty or on or after it.
2. At a **project**, the holders are the people named by the covering rows
   for the position whose `project` is that project. Where there are none,
   they are the people named by the covering rows whose `project` is empty.
3. At the **organisation**, the holders are the people named by the
   covering rows whose `project` is empty.
4. A person named by two covering rows is one holder.
5. No covering row is **no holder**. It is reported as no holder, never as a
   person, and never as an error.

The day is the day the fact being resolved for became true, so a late
answer still names whoever held the position then.

### Who may read it

Reading it is reading a `restricted` entry of the records repository through
content: `content:read` on a request content admits at `restricted`
([`architecture/content`](../architecture/content.md#read-flow)). Two kinds of
reader do:

- **A person**, on their own pass through the admin gateway, whose role
  carries `content:read` ([`architecture/admin`](../architecture/admin.md#operator-roles)).
- **A tenant service resolving a position for work nobody is present for**,
  on a work pass under the work authorisation of that work, never on its own
  registration
  ([`protocol/identity`](../protocol/identity.md#the-work-pass)).
  [`architecture/notification`](../architecture/notification.md#resolving-holders)
  is the first. Content records each such read with the owner of the work as
  `actor`, the service as `via`, and the authorisation and run.

What it holds is never sent to a model provider: what may leave for one is
[`patterns/scope`](../patterns/scope.md#model-providers)'s, and a register
about people is `restricted`.

### Changing who holds a position

A holder is changed only by a person, as an entry of content changes, and
never by a service or an agent acting alone:

- **Directly**, by a person on their own pass, with `content:write`, which
  is person only; or
- **By proposal**: a person, a service or an agent proposes the change with
  `content:propose`, and a person decides it with `content:decide`
  ([`architecture/content`](../architecture/content.md#who-may-move-an-entry)).

**A holding ends; it is never removed.** A person who stops holding a
position is given a `last_day`. A row is never deleted and its `holding` never
reused, because an act recorded under a holding — an approval, an
attestation — is checked against who held the position on its day, and a
removed row would leave that check unanswerable. A row written in error is
ended on the day before its `first_day` and given a `note`.

**The change log is the audit.** Every change is one change in the records
repository's log: who made it, on which pass, the bytes before and after,
and the scope, signed where the repository requires a statement
([`architecture/content`](../architecture/content.md#the-change-log)). No
second record of holdings is kept anywhere, so no second record can disagree
with it.

### Resources

The kind a person sees a holding as, declared as
[`schemas/resource`](resource.md) says. Content holds the register, and its
blueprint does not yet serve a register's rows as items, so the kind is held
here and is `declared-unavailable` until it does; until then a person reads
and changes holdings as the register entry itself, through content's own
routes.

```yaml
resources:
  - kind: position-holder
    owner: content
    type: PositionHolding
    identity: {field: holding, form: minted}
    label: position
    fields:
      - {name: holding, access: read-only, present: text}
      - {name: position, access: create, present: text}
      - {name: holder, access: create, present: text}
      - {name: project, access: create, present: text}
      - {name: first_day, access: create, present: text}
      - {name: last_day, access: settable, present: text}
      - {name: note, access: settable, present: text}
      - {name: recorded_by, access: read-only, present: text}
    operations:
      list: {capability: "content:read", filters: [position, holder, project]}
      get: {capability: "content:read"}
      create: {capability: "content:write"}
      update: {capability: "content:write"}
    events: [created, updated]
    unavailable:
      reason: owner-unspecified
      says: content does not yet serve a register's rows as items; a holding is read and changed as the register entry, through content's routes
```

`delete` is not declared: a holding ends, and is never removed.

---

## Known gaps

**Content does not serve a register's rows as items.** The `position-holder`
kind is declared-unavailable until it does ([Resources](#resources)); a
holding is read and changed as the whole register entry.

**Nothing refuses a person recording themselves as a holder.** A person with
`content:write` may write a row naming themselves, including for a position
that approves. A change made by proposal is held to content's
[separation of duties](../architecture/content.md#separation-of-duties) where
the records repository's `self_decision_ceiling` is below `restricted`, and
a direct write is held to nothing but the log that records it.

**No act is checked against a holding yet.** The register says who held a
position on a day, and nothing yet checks that whoever approved, attested or
signed under a position held it then. The positions an approval, escalation
or obligation names are resolved by [the rule above](#resolving-a-position-to-its-holders);
which service resolves each, other than notification for a notice, is not
specified.

**No retention is declared.** The register declares no keeping period: how
long a tenant keeps who held its positions is the tenant's to set, and no
field yet lets a tenant set one for a register the corpus declares.

---

## Verification Checklist

- [ ] The filename, without `.md`, equals the declared `id` ([Format](#format))
- [ ] The `id` is a position at least one programme in `programmes/` names ([What is reported rather than refused](#what-is-reported-rather-than-refused))
- [ ] Every `##` heading is one of those [Body — a closed set of headings](#body--a-closed-set-of-headings) lists, spelled exactly
- [ ] At least one recognised section has content
- [ ] No artifact id and no register path appears anywhere in the body ([A guide may not restate derived fact](#a-guide-may-not-restate-derived-fact))
- [ ] Prose naming a cadence, an authority, an escalation target or an approver is not refused; only the two patterns the section lists are ([A guide may not restate derived fact](#a-guide-may-not-restate-derived-fact))
- [ ] No individual is named, and no tenant, customer or project is named ([Format](#format))

### The position-holders register

- [ ] It is written at `registers/position-holders.md` in the organisation's records repository, and a write of it anywhere else is refused with `CONTENT_RECORDS_REPOSITORY_REQUIRED` ([The register](#the-register))
- [ ] Every column the block declares is present, `holder` and `note` are `restricted` and labelled `pii`, and `recorded_by` is not labelled ([The register](#the-register))
- [ ] A row's `holder` is an identity id, never a name or an address ([The register](#the-register))
- [ ] At a project with a covering row for the position, only that project's holders are answered; with none, the organisation's are ([Resolving a position to its holders](#resolving-a-position-to-its-holders))
- [ ] A position with no covering row resolves to no holder, never to a person and never to an error ([Resolving a position to its holders](#resolving-a-position-to-its-holders))
- [ ] A holding that ends is given a `last_day`, and no row is removed ([Changing who holds a position](#changing-who-holds-a-position))
- [ ] A tenant service reads the register only on a work pass under the authorisation of the work it resolves for ([Who may read it](#who-may-read-it))
