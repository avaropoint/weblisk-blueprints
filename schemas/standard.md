# Standard Schema

Schema governing **industry standards** — the documents in `standards/` that
declare the published criteria an organisation is measured against: ISO 27001,
ISO 45001, SOC 2, NIST 800-53, CSA B51, COR 2020.

Derived from the 37 standards already in the corpus — 167 families and 951
controls — rather than designed ahead of them. Every field below is one those
files carry.

> **Not to be confused with the earlier `schemas/standard.md`**, which governed
> the Weblisk client framework's project guidance. That is now
> [`framework.md`](framework.md), and the word `standards` means what it means to
> a customer. See [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md).

---

## What a standard is, and is not

A standard here is the **ruler, never the measurement.**

It declares what a published authority requires. It does not know who adopted
it, how well they do, or what evidence answers which control — those are
**tenant content**, the customer's, in the customer's repositories. A standard
that recorded an organisation's score would be one document doing two jobs, and
the second job belongs to somebody else.

## Format

**JSON, not Markdown.** A control set is data a tool reads, not prose a person
reads end-to-end, and a customer editing one should be able to use the tools
they already have. `MISSION.md` says complimentary content is "JSON and
Markdown"; this is the JSON half.

One file per standard, named for its `id`: `standards/<id>.json`.

---

## Required fields

| field | type | means |
|---|---|---|
| `id` | string | stable identifier, and the filename. What a programme's `conforms_to` cites |
| `name` | string | the standard as its authority names it |
| `version` | string | the edition — `"2018"`, `"Rev 5"` |
| `description` | string | what it requires and what distinguishes it. Prose, for a person choosing between standards |
| `authority` | string | who publishes it |
| `scope` | string | who it applies to |
| `category` | enum | `operational` · `cybersecurity` · `privacy` · `industry` · `government` · `code` |
| `status` | enum | `active` · `superseded` · `withdrawn` |
| `families` | array | its control families, below |

## Optional fields

| field | type | means |
|---|---|---|
| `applies_in` | string[] | where the standard has force — ISO 3166 codes, or `international`. Below |
| `official_url` | string | where the authority publishes it |
| `published_date` | date | when this edition was published |
| `effective_date` | date | when conformance is expected |
| `transition_deadline` | date | when the previous edition stops being accepted |
| `supersedes` | string | the prior edition, **named in prose** — `"SSAE 16 (2011)"`. Not an `id`: superseded editions are not carried here |
| `changes_summary` | string | what changed from the superseded edition |

**A superseded standard is not deleted.** Evidence was gathered against it, and
an audit of a past period is judged against what applied then. `status` and
`supersedes` are how an edition retires without its history becoming
unreadable — the same rule the fabric applies to a retired node.


## `applies_in` — where a standard has force

A standard is published by an authority with a reach. Ontario's *Occupational
Health and Safety Act* binds in Ontario; 29 CFR 1926 binds in the United States;
ISO 27001 binds nowhere at all until somebody adopts it. `applies_in` states
that reach as data, so *"which standards apply to an organisation operating in
Ontario"* is a question with an answer.

It was carried by convention until now — inside the `id`
(`ontario_building_code`, `quebec_law25`) and in `scope` prose. A convention is
unreadable to a tool and, worse, it is ambiguous to a person:
`construction_safety_ca` is Canada, and nothing short of reading the description
distinguishes it from California.

A **list**, because reach is plural. CSA publishes nationally and each province
adopts by reference; a data protection regulation covers a union and the states
that treat with it. A single value would force one of those to be a lie.

| entry | means | example |
|---|---|---|
| ISO 3166-1 alpha-2 | a country, and every subdivision of it | `CA`, `US`, `AU` |
| ISO 3166-2 | one subdivision, when the authority is sub-national | `CA-ON`, `CA-QC`, `US-CA` |
| `international` | published for adoption anywhere, binding nowhere by itself | ISO/IEC, SOC 2, PCI DSS |

ISO 3166 because this corpus already writes places that way —
[`../protocol/federation.md`](../protocol/federation.md) uses alpha-2 codes — and
a second geographic vocabulary in one repository is a translation table waiting
to be written. `EU` is ISO 3166-1's exceptionally reserved code for the European
Union, which is why GDPR can name its union and the three EEA states beside it.

Four rules keep two lists comparable:

- **`international` stands alone.** A standard is territorially bound or it is
  not; a list holding both claims both.
- **Never a subdivision of a country already listed.** `CA` already contains
  `CA-ON`, and writing both invites a reader to think the second adds something.
- **Ascending order**, so the same reach is the same text.
- **As ISO writes them** — upper case, hyphenated.

### `international` is a value, not an absence

ISO 27001 applies to an organisation in Ontario exactly as it applies to one in
Osaka: by adoption or by contract, never by law. That is a fact about the
standard, and `applies_in: ["international"]` records it. Leaving the field out
would record something else entirely — see below — and a filter answering
"standards for Ontario" would then have to choose between dropping ISO 27001 and
guessing.

### Force, never origin

`applies_in` says where the standard has force. Where its authority sits is
`authority`'s job, and the two disagree often: SOC 2 is AICPA's, PCI DSS is a
US-incorporated council's, SMACNA is a US trade association's, and all three
bind only where a contract makes them, anywhere on earth. A standard's reach
must not be inferred from its publisher's address, and this field must never be
read as a restatement of one.

### Absent means nobody has said, and nothing more

The field is **optional**, and that is deliberate: a customer's own standard
must still load without it, and a corpus older than this field must still be
readable by a build that has it. So an absent `applies_in` means *unstated* —
never *global*, never *local*, never *checked and found to be neither*. A
consumer filtering by place includes an unstated standard as a stated unknown or
excludes it and says so. Treating the gap as "applies everywhere" is the
confident zero this corpus exists to avoid.

Every standard in `standards/` carries one. Absence here is a gap to be filled,
not a shape to be copied.

### It is not `jurisdiction`, and not by accident

[`../protocol/federation.md`](../protocol/federation.md) already spends that
word: an orchestrator declares a `jurisdiction`, and a data contract carries a
`JurisdictionSpec.country_codes`. Both are **data residency** — where bytes may
come to rest — and both are enforced at routing time by rejecting a peer.

That is a different question with the same shape of answer, which is the
dangerous kind of collision: an ISO 3166 list under the same name, one
describing a legal authority's reach and the other where a payload may be
stored. A tenant can perfectly well be governed by Ontario law while contracting
that its data resides in Germany. So this field takes a different word, and no
consumer should ever resolve one from the other.

### It never records adoption

The ruler, never the measurement, applies here too. `applies_in` says where the
standard *has* force, not that any organisation there has adopted it, is
certified to it, or is being measured against it. Which standards an
organisation is held to is tenant content, in the customer's own repositories.

---

## Families

A family groups controls as the standard itself groups them — a clause, a
section, a control family. All four fields are required.

| field | type | means |
|---|---|---|
| `id` | string | unique within the standard |
| `name` | string | as the standard names it |
| `description` | string | what this part of the standard covers |
| `controls` | array | the controls, below |

---

## Controls

The unit a document answers, and what the fabric's `addresses` and `implements`
relations point at.

| field | type | means |
|---|---|---|
| `id` | string | the authority's own identifier — `A.5.15`, `COR-10`. **Never invented**: an auditor cites this |
| `name` | string | short title |
| `description` | string | what it requires |
| `family` | string | the family `id` this belongs to |
| `framework` | string | the standard `id` — carried so a control travels without its parent |
| `domains` | string[] | the policy domains it concerns. 25 are in use across the corpus |
| `priority` | enum | `critical` · `high` · `medium` · `low` |
| `requires_policy` | bool | a statement of intent is needed |
| `requires_procedure` | bool | an operational process is needed |
| `requires_technical` | bool | an implementation is needed |
| `requires_evidence` | bool | a record of it having happened is needed |
| `keywords` | string[] | terms that suggest a document may answer this |
| `mapped_controls` | string[] | equivalent controls in other standards, as `<standard>:<control>` |

### `code` and `low`

Two values are there for the framework catalogue generated from `schemas/`
([`../standards/README.md`](../standards/README.md#one-is-generated-and-is-here)):

- **`code`** is its `category`. Its controls are the sections the blueprint
  schemas list, and none of the five compliance domains describes that.
- **`low`** is the `priority` of its controls for the sections a blueprint
  schema marks optional, which a conforming blueprint may leave out and which
  no rung up to `medium` describes.

### The four `requires_*` flags are the point

They say **what kind of thing answers this control** — and a control answered by
the wrong kind is not answered. A policy does not satisfy a control requiring
evidence; an implementation does not satisfy one requiring a stated commitment.
Coverage computed without them counts documents rather than conformance.

### `keywords` suggest; they never decide

They are how a scan proposes that a document *may* answer a control. A proposal
is not an answer: the fabric records it as `inferred`, and only a person
confirms. A control marked answered because a word appeared is the confident
answer this framework exists to avoid.

### `mapped_controls` is an equivalence claim, and it is directional in practice

ISO 27001 A.5.15 and NIST AC-2 overlap; they are not identical. A mapping says
*evidence for one is likely to bear on the other*, not *satisfying one satisfies
the other*. Treating it as the second is how an organisation comes to believe it
holds an accreditation it has never been assessed for.

---

## Adopting a standard

A standard in `standards/` is published, and a tenant **adopts** it the way it
adopts a programme: one recorded act by a person, at an organisation, made once
and refused the second time, updated only by proposals a person applies, and
undone by an act of its own. Those rules are
[`programme.md`](programme.md#adopting-a-programme)'s and are not restated here.
This section says what is different, and one thing is: **a standard is never
copied into a tenant as it is published.**

### Generated, never copied

Adopting a standard **generates** the organisation's own standard into the
repository the person adopting chooses. It is the published standard as it
pertains to that organisation: the published file, **linked**, never
reproduced, plus the organisation's **adjustments** — what does not apply and
why, what applies more strictly, what the organisation adds.

A copy is refused because it answers the wrong question. A standard's controls
are written for every organisation the authority addresses; which of them bind
this one, how strictly and with what of its own beside them depends on where it
operates, what it does and what it holds. A copy taken as it is measures the
organisation against a ruler cut for nobody in particular, and the first
adjustment anybody needed would be made by editing the copy, with no record of
which words were the authority's and which were the organisation's.

One generated standard per standard per scope, at `standards/<id>.json` in the
chosen repository, keeping the published `id` — so a `framework:control`
citation and a programme's `conforms_to` resolve to it unchanged.

```json
{
  "id": "iso_27001",
  "extends": {
    "standard": "standards/iso_27001.json",
    "source": "weblisk-blueprints",
    "version": "2022",
    "digest": "sha256:…",
    "revision": "4883cfa88c55769560f8287d4a2fb4c94c5a6c98"
  },
  "adjustments": [
    {"control": "A.7.5", "applies": false,
     "reason": "No premises of its own; every site is a client's",
     "basis": {"scope": "organisation", "characteristic": "premises"}},
    {"control": "A.8.24", "priority": "critical",
     "reason": "Holds payment card data",
     "basis": {"scope": "organisation", "characteristic": "data held"}},
    {"add": {"id": "local-1", "family": "A.8", "name": "…", "description": "…",
             "requires_procedure": true},
     "reason": "A contract requires it",
     "basis": {"scope": "organisation", "decision": true}}
  ]
}
```

| field | required | means |
|---|---|---|
| `id` | **yes** | the published standard's `id`, unchanged |
| `extends` | **yes** | the link and its pin, below |
| `adjustments` | **yes** | the organisation's adjustments, below. Empty is allowed and means *adopted as published* — still a link, never a copy |

**`extends` is the link, pinned.** `standard` is the published file's path in
its source; `source` is a locator, never an identity; `version` is the
published edition as adopted; `digest` is `sha256:` over the published file's
bytes when it was read; `revision` is the source's commit, full, or `none`.
These are the per-file pin fields of
[`programme.md`](programme.md#the-adoption-record), with `version` holding the
**edition**, because a standard's version is its publisher's
([Required fields](#required-fields)).

**A generated standard carries no control it did not adjust.** The published
families and controls are read through the link at the pinned digest. A file
that restated them would be the copy this section refuses, and is refused.

### Adjustments, and the characteristics they answer

Each adjustment names one published control, or adds one, and carries a
`reason` in words and a `basis`:

| adjustment | means |
|---|---|
| `applies: false` | the control does not bind this scope. Never silent: an exclusion with no reason is refused, because an auditor asks for exactly this |
| `priority` | a different priority, from the closed set |
| `requires_policy` · `requires_procedure` · `requires_technical` · `requires_evidence` | a different answer to what kind of thing satisfies the control |
| `note` | the organisation's reading of the control, in its own words, beside the authority's — never replacing it |
| `add` | a control of the organisation's own, as a [control](#controls) whose `id` no published control of the standard carries, in a family the standard declares |

`basis` says where the adjustment came from: the **scope** whose
characteristic it answers — `tenant`, `organisation` or `project` — and the
**characteristic**, or `decision: true` where a person decided it with no
characteristic to point to. A characteristic is a fact the tenant holds about
itself at that scope: the places it operates, as ISO 3166 codes the way
[`applies_in`](#applies_in--where-a-standard-has-force) writes them; the work it
does; the data it holds.

**Generation proposes; a person adopts.** Whatever generates the standard reads
the characteristics from the tenant's content and proposes each adjustment with
its basis. An adjustment a tool can compute — a control bound to a place the
organisation does not operate in — is proposed as computed; one drafted by a
model is a proposal like any other. The person adopting reviews them, and the
file is written with the ones they kept. Nothing reaches the file on a model's
word alone.

**Tenant, organisation, project.** A repository sits at an organisation or a
project ([`architecture/content`](../architecture/content.md)), so the tenant's
characteristics are applied in each organisation's generated standard, with
`basis.scope: tenant`. A project that needs its own adjustments keeps a
generated standard of its own in a repository at the project, whose `extends`
links the **organisation's** generated standard — its path, the repository's
`id` as `source`, its digest — rather than the published one. What a project is
measured against is the published standard, then the organisation's
adjustments, then the project's, each applied over the last. A project with no
file of its own is measured against its organisation's. A project's file is a
refinement of the organisation's adoption, never a second adoption, as a
programme's is.

**A link that cannot be read is said.** A generated standard whose linked file
cannot be reached at its pinned digest is **unscoreable** at that scope, naming
the link. It is never scored against nothing, and never against whatever the
source holds now.

### Linking without adopting

A scope may **link** a published standard without adopting it: reading it from
its source, at a digest, to see what it asks. A link copies nothing and makes no
claim. A scope that has linked a standard and adopted none is shown as such —
measured against the published standard as linked, never presented as having
chosen it. Holding or linking a standard is not adopting it.

### Editing what is linked

The generated standard is the organisation's, edited in place through the
content service like any document, under that repository's permissions.

The **source** a generated standard links is edited only where the person
editing it holds write permission on that source — a standards repository the
tenant keeps itself, for instance. Such an edit is a change to the source,
recorded in the source's own history: every scope linking it then reads as
`behind`, and takes it as an update. The corpus's published standards are never
editable from a tenant; a change wanted there is a proposal to the publisher.

### Updates to the published standard

The published file moving is found by comparing its bytes and edition now with
`extends.digest` and `extends.version`:

- **A different edition** is a **new edition**: offered to the organisation as a
  choice, never as an update, because which edition it is measured against is
  its own decision.
- **The same edition with a moved digest** is **revised** — the corpus changed
  its reading of an edition its publisher did not change. Offered as an update.

Either is offered as a regenerated standard: the new link and pin, with every
adjustment re-applied, and every adjustment naming a control the new file no
longer has reported by name rather than dropped. It is a proposal a person
applies, exactly as a programme's update is
([Updates arrive as proposals](programme.md#updates-arrive-as-proposals)).
Taking it replaces the generated standard in place; a scope never holds two
editions side by side. Neither is ever classed compatible, and neither is
`unmaintained`: an edition is its publisher's.

A change to an organisation's generated standard reaches each project's in the
same way: the project's link reads `behind`, and the project takes it.

### Known gaps

- **Nothing reads a generated standard yet.** Readers of a tenant's
  `standards/*.json` expect the [required fields](#required-fields) and do not
  resolve `extends`, so a generated standard is unreadable to them until they
  do.
- **No schema declares a scope's characteristics.** Places, work and data held
  are named here by what they are; the tenant has no declared place to keep
  them, so `basis.characteristic` is a name nothing checks.
- **Nothing generates or adopts a standard yet**, and a tenant whose content
  service is not running cannot hold one.

---

## Verification Checklist

- [ ] Every file in `standards/` is valid JSON and carries all nine required fields
- [ ] The filename equals the `id`
- [ ] Every `control.framework` equals the `id` of the standard it appears in
- [ ] Every `control.family` names a family declared in that standard
- [ ] Every `control.id` is unique within its standard
- [ ] `category`, `status` and `priority` carry only declared values
- [ ] A standard declaring `supersedes` names the prior edition in prose, and does not claim an `id` this corpus carries
- [ ] Every `mapped_controls` entry is `<standard>:<control>` and names a standard the corpus carries
- [ ] No standard in this corpus records an organisation's adoption, score or evidence
- [ ] `weblisk_framework` is generated from `schemas/` and never edited by hand — see [`../standards/README.md`](../standards/README.md#one-is-generated-and-is-here)
- [ ] Every standard carries `applies_in` — optional in the schema so a customer's file still loads, filled in everywhere here
- [ ] Every `applies_in` entry is an ISO 3166-1 alpha-2 code, an ISO 3166-2 subdivision code, or `international`
- [ ] `international`, where it appears, is the only entry
- [ ] No `applies_in` names a subdivision of a country it already names
- [ ] No `applies_in` restates data residency — that is `jurisdiction` in `protocol/federation.md`, a different question
- [ ] Adopting a standard generates the organisation's own at `standards/<id>.json` in the chosen repository, keeping the published `id`, and never writes the published file as it is
- [ ] A generated standard carries `id`, `extends` — `standard`, `source`, `version` (the edition), `digest`, `revision` — and `adjustments`, and restates no published control it does not adjust
- [ ] Every adjustment names a published control, or adds one whose `id` the standard does not carry in a family it declares, and carries a `reason` and a `basis` naming its scope and characteristic, or `decision: true`
- [ ] No adjustment reaches the file without a person keeping it; a model's adjustment is a proposal
- [ ] A project's generated standard links its organisation's, not the published one, and is a refinement, never a second adoption
- [ ] A link that cannot be read at its pinned digest leaves the scope unscoreable, naming the link
- [ ] A source a generated standard links is edited only under write permission on that source; the corpus's published standards never are
- [ ] A new edition is offered as a choice and a revised one as an update, each as a regenerated standard a person applies, with every adjustment naming a missing control reported, never dropped
