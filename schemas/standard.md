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
| `category` | enum | `operational` · `cybersecurity` · `privacy` · `industry` · `government` |
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
| `priority` | enum | `critical` · `high` · `medium` |
| `requires_policy` | bool | a statement of intent is needed |
| `requires_procedure` | bool | an operational process is needed |
| `requires_technical` | bool | an implementation is needed |
| `requires_evidence` | bool | a record of it having happened is needed |
| `keywords` | string[] | terms that suggest a document may answer this |
| `mapped_controls` | string[] | equivalent controls in other standards, as `<standard>:<control>` |

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

## Verification Checklist

- [ ] Every file in `standards/` is valid JSON and carries all nine required fields
- [ ] The filename equals the `id`
- [ ] Every `control.framework` equals the `id` of the standard it appears in
- [ ] Every `control.family` names a family declared in that standard
- [ ] Every `control.id` is unique within its standard
- [ ] `category`, `status` and `priority` carry only declared values
- [ ] A standard declaring `supersedes` names the prior edition in prose, and does not claim an `id` this corpus carries
- [ ] Every `mapped_controls` entry is `<standard>:<control>` and names a standard the corpus carries
- [ ] No standard records an organisation's adoption, score or evidence
- [ ] `weblisk_framework` is absent — it is generated from `schemas/`, not authored
- [ ] Every standard carries `applies_in` — optional in the schema so a customer's file still loads, filled in everywhere here
- [ ] Every `applies_in` entry is an ISO 3166-1 alpha-2 code, an ISO 3166-2 subdivision code, or `international`
- [ ] `international`, where it appears, is the only entry
- [ ] No `applies_in` names a subdivision of a country it already names
- [ ] No `applies_in` restates data residency — that is `jurisdiction` in `protocol/federation.md`, a different question
