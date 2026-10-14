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

**A file carrying `extends` is a generated standard**
([Adopting a standard](#adopting-a-standard)): it requires only `id`, `extends`
and `adjustments`, and every other field is read through the link.

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
| `id` | string | the authority's own identifier — `A.5.15`, `COR-10`. **Never invented** for a published control: an auditor cites this. A control an organisation adds to its generated standard carries an id of its own, which no published control of the standard carries ([Adjustments](#adjustments-and-the-characteristics-they-answer)) |
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
    "version": "2022, incorporating Amd 1:2024",
    "digest": "sha256:…",
    "revision": "4883cfa88c55769560f8287d4a2fb4c94c5a6c98"
  },
  "adjustments": [
    {"control": "A.7.5", "text_digest": "sha256:…", "applies": false,
     "reason": "No premises of its own; every site is a client's",
     "basis": {"scope": "organisation", "characteristic": "premises"}},
    {"control": "A.8.24", "text_digest": "sha256:…", "priority": "critical",
     "reason": "Holds payment card data",
     "basis": {"scope": "organisation", "characteristic": "data held"}},
    {"add": {"id": "local-1", "family": "TECH", "name": "…", "description": "…",
             "priority": "high",
             "requires_policy": false, "requires_procedure": true,
             "requires_technical": false, "requires_evidence": true},
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
They follow a programme's per-file `resolved` entry
([`programme.md`](programme.md#the-adoption-record)) with three differences:
there is one file, so one entry and no map of paths; `version` holds the
**edition**, because a standard's version is its publisher's
([Required fields](#required-fields)); and `repository` appears only on a
project's link, below, because what an organisation links is outside the tenant.

**The generated file is the adoption record.** A standard has no `adoption.md`.
Its key is the organisation and the standard's `id`. A second adoption is any
`standards/<id>.json` carrying `extends` in the organisation's repositories,
and is answered *already adopted* or refused as
[`programme.md`](programme.md#adopting-twice-creates-nothing) says.
Un-adopting is a person removing that file, and removes nothing else.

**A generated standard carries no control it did not adjust.** The published
families and controls are read through the link at the pinned digest. A file
that restated them would be the copy this section refuses, and is refused.

### Adjustments, and the characteristics they answer

Each adjustment names one published control, with the `text_digest` of that
control at the pinned edition ([Outputs cite the control text](#outputs-cite-the-control-text-they-were-made-from)),
or adds one, and carries a `reason` in words and a `basis`:

| adjustment | means |
|---|---|
| `applies: false` | the control does not bind this scope. Never silent: an exclusion with no reason is refused, because an auditor asks for exactly this |
| `priority` | a different priority, from the closed set |
| `requires_policy` · `requires_procedure` · `requires_technical` · `requires_evidence` | a different answer to what kind of thing satisfies the control |
| `note` | the organisation's reading of the control, in its own words, beside the authority's — never replacing it |
| `add` | a control of the organisation's own, as a [control](#controls) whose `id` no published control of the standard carries, in a family the standard declares. It requires `id`, `family`, `name`, `description`, `priority` and the four `requires_*` flags; `framework` is the standard's `id` and may be left out; `derived_from`, `{control, text_digest}`, names the published control it was derived from, where it was; the rest are optional |

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
links the **organisation's** generated standard — its path as `standard`, the
organisation repository's `id` as **`repository`**, its digest — rather than
the published one. What a project is
measured against is the published standard, then the organisation's
adjustments, then the project's, each applied over the last. A project with no
file of its own is measured against its organisation's. A project's file is a
refinement of the organisation's adoption, never a second adoption, as a
programme's is.

**A link that cannot be read is said.** A generated standard whose linked file
cannot be reached at its pinned digest is **unscoreable** at that scope, naming
the link. It is never scored against nothing, and never against whatever the
source holds now.

### Outputs cite the control text they were made from

**The tenant holds no control text, only outputs.** What an organisation makes
from a standard — an adjusted control, a control of its own derived from a
published one, and every document, obligation and register a programme
generates against a control — keeps a reference to the **exact text** of the
control it was made from, and never a copy of that text. The reference is what
lets a later revision say which of the organisation's outputs it affects,
before anybody adopts it.

**A per-control digest.** The standard's `extends.digest` says *that* the
published file moved; it cannot say which controls did. So each control has a
digest of its own, the **text digest**:

- the **text** of a control is an object holding exactly its `framework`, `id`,
  `name`, `description` and its four `requires_*` flags, with the values the
  pinned edition publishes. For a control an organisation adds, `framework` is
  filled with the standard's `id` before hashing, whether or not the `add`
  wrote it;
- its digest is `sha256:` followed by the lowercase hexadecimal SHA-256 of the
  UTF-8 output of [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)
  canonicalisation of that object — the canonicalisation
  [`protocol/identity`](../protocol/identity.md) already requires for signing —
  so anybody can recompute it with no Weblisk code.

Every other field is left out: `family`, `keywords`, `mapped_controls`,
`domains` and `priority`, and any field a control carries that this schema does
not declare. They say where a control is filed and how it is found and ranked,
not what it requires, and a re-tuned keyword that marked every output built on
the control as needing review would teach people to ignore the signal.

This is a digest of a **declared projection**, not of stored bytes — the one
exception [`patterns/content-identity`](../patterns/content-identity.md) makes
to hashing what is stored, because a control is never stored on its own.

**What records the reference.** Two forms, and which one depends on the output:

- **The generated standard declares it.** Each adjustment carries
  `text_digest`, the text digest of the control it adjusts at the pinned
  edition, and an `add` derived from a published control names it in
  `derived_from` with that control's `text_digest`. Those fields are the
  **declared source**: the `generated_from` claim from the generated standard
  to each control is derived from them, and where the claim and the file
  disagree, the file wins.
- **Documents, obligations and registers carry nothing in their bytes.** For
  them the reference is a **fabric claim** only — `generated_from`, from the
  output to the `control` — recorded when adoption creates the output, never
  written into the document, because a relationship is never kept in a
  document ([`architecture/fabric`](../architecture/fabric.md#where-relationships-do-not-live)).

Either way the claim records the control's identity (`control:<standard>:<id>`),
the **edition** it was made against, and the **text digest** as the version it
cited ([`kinds.md`](kinds.md#relations) declares the relation;
[`architecture/fabric`](../architecture/fabric.md#health) owns what a cited
version means). It is stated through `Sync` by the producer that records the
adoption or reads the generated standard, at status `inferred`, as
[Who may assert what](../architecture/fabric.md#who-may-assert-what) allows a
producer; a person reviewing it uses `Attest` or `Decide`. A document that also
states which control it answers says so with `implements`, as it always has;
`generated_from` records what it was made from, which is a different claim.

**When a claim goes stale.** A control end's observed version is its text
digest **at the scope's pinned edition**. Before adoption, a new revision
changes no claim's health: the per-control report under
[Updates](#updates-to-the-published-standard) is how it is offered. Taking the
update moves the pin, and every claim citing a digest the new pin does not hold
reads `stale`, listing its output as needing a person's review. Nothing is
regenerated by it — staleness asks for a review, and a rebuild is a separate
decision ([Staleness and rebuild](../architecture/fabric.md#staleness-and-rebuild-are-different-questions)).

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
`behind`, and takes it as an update. A tenant holds no write permission on the
corpus, so a change wanted in a published standard is a proposal to the
publisher.

**What an export or an audit package carries.** An export or audit package that
reports against a generated standard includes the linked standard's bytes, read
at the pinned digest and verified against it, beside the generated file. A
package carrying only the adjustments would be unreadable without the source,
and one carrying bytes it had not verified would cite a ruler nobody can show
was the one adopted.

### Updates to the published standard

The published file moving is found by comparing its bytes and edition now with
`extends.digest` and `extends.version`:

- **A different edition** is a **new edition**: offered to the organisation as a
  choice, never as an update, because which edition it is measured against is
  its own decision.
- **The same edition with a moved digest** is **revised** — the corpus changed
  its reading of an edition its publisher did not change. Offered as an update.

**The offer is reported per control, before anybody adopts it.** The
per-control digests of the pinned edition and of the new file are compared, and
each control is reported as:

| state | means | the outputs listed |
|---|---|---|
| `changed` | the control is in both, and its text digest differs | every output with a `generated_from` claim onto the control — each to be reviewed |
| `removed` | the pinned edition has it and the new file does not | every output with a claim onto it — each left without the text it was made from |
| `added` | the new file has it and the pinned edition does not | none yet: a control the organisation has not adjusted or answered |
| *unchanged* | the same digest in both | not listed |

Outputs are listed by the control's identity, not by digest, and each shows
the digest it cites. One citing no digest — made before this rule, or by a
reader that records none — is listed as **cannot be compared**, never as
unaffected.

A control whose `id` changed between editions is reported `removed` and
`added`, never matched by guessing.

Either is offered as a regenerated standard: the new link and pin, with every
adjustment re-applied. An adjustment whose control is unchanged takes the new
digest; one whose control is `changed` keeps its old `text_digest` and is
listed for review until a person re-affirms it; one naming a control the new
file no longer has is reported by name rather than dropped. It is a proposal a person
applies, exactly as a programme's update is
([Updates arrive as proposals](programme.md#updates-arrive-as-proposals)).
Taking it replaces the generated standard in place; a scope never holds two
editions side by side. Neither is ever classed compatible, and neither is
`unmaintained`: an edition is its publisher's.

A change to an organisation's generated standard reaches each project's in the
same way: the project's link reads `behind`, and the project takes it.

### Known gaps

- **No reader computes a per-control digest yet**, and no producer asserts
  `generated_from` onto a control, so no output's staleness against a revision
  can be shown today. Programmes' specs cite controls by `satisfies` with no
  digest, and documents generated before this rule carry none: a claim citing no
  digest reads `unversioned`, which says honestly that nothing can be compared.

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

- [ ] Every published standard in this corpus is valid JSON and carries all nine required fields
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
- [ ] A source a generated standard links is edited only under write permission on that source, and a tenant holds none on the corpus
- [ ] The generated file is the standard's adoption record: a second `standards/<id>.json` carrying `extends` at the organisation is answered *already adopted* or refused, and un-adopting removes that file and nothing else
- [ ] A project's generated standard carries its organisation repository's `id` in `repository`, never in `source`
- [ ] Every `add` carries `id`, `family`, `name`, `description`, `priority` and the four `requires_*` flags
- [ ] An export or audit package against a generated standard includes the linked standard's bytes, verified against the pinned digest
- [ ] A new edition is offered as a choice and a revised one as an update, each as a regenerated standard a person applies, with every adjustment naming a missing control reported, never dropped
- [ ] A text digest is `sha256:` and the lowercase hex SHA-256 of the UTF-8 RFC 8785 output for an object of exactly the control's `framework`, `id`, `name`, `description` and four `requires_*` flags, with `framework` filled for an added control; `family` and every other field are excluded
- [ ] Every adjustment carries the `text_digest` of the control it adjusts, and every `add` derived from a published control names it in `derived_from` with that control's `text_digest`
- [ ] A generated standard's `text_digest` and `derived_from` are the declared source of its `generated_from` claims and win where they disagree; a document, obligation or register made against a control carries the reference only as a `generated_from` claim, never in its bytes, and no output holds the control's text
- [ ] Every `generated_from` claim onto a control records the control's identity, the edition and the text digest, stated through `Sync` at `inferred`
- [ ] A control end's observed version is its text digest at the scope's pinned edition; a revision not yet adopted changes no claim's health
- [ ] An update is reported per control as `changed`, `removed` or `added`, listing the outputs it affects by control identity with each one's cited digest and marking those citing none *cannot be compared*, before a person adopts it; a renamed control is `removed` and `added`, never matched by guess
- [ ] On taking an update, an adjustment to an unchanged control takes the new digest and one to a changed control keeps its old digest and is listed for review until a person re-affirms it
