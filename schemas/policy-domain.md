# Policy Domain Schema

Schema governing [`../policy-domains/`](../policy-domains/) — everything the
platform can say about a **subject area of governance**: access control,
incident response, occupational health and safety.

A programme declares `domains:`. This family says what each of those words
*means*, where it stops, and — the substance — **what a programme claiming it
must provide**.

It has two written halves and a third body of fact that is never written at
all:

| | where | job |
|---|---|---|
| **declaration** | `policy-domains/catalogue/*.json` | **that** a domain exists, and the keywords that classify a document into it. Read by the classifier |
| **commentary** | `policy-domains/<id>.md` | what it covers, where it stops, what claiming it requires. Read by the completeness report |
| **derived** | nowhere — computed on read | which programmes claim it, which artifacts answer it, what work they raise, who is responsible |

**The first two are never merged.** A matcher cannot be compiled from prose,
and a boundary statement cannot be reviewed as a keyword array. Merging them
would also put `keywords` within reach of a hand edit meant for a sentence,
which is the one field where a mistake reclassifies documents in silence.

> **A file here is not a declaration that the domain exists.** Domains are
> declared by the **policy-domain catalogue** in
> [`../policy-domains/catalogue/`](../policy-domains/catalogue/README.md) — the
> other half of this family, and what the classifier reads. This family is
> commentary and requirement on domains the catalogue has already declared, and
> a file here for a domain the catalogue does not declare is **reported, never
> honoured**.

---

## Why it is not called `domains/`

`domain` already means something else in this corpus, with code behind it.
[`domain.md`](domain.md) governs `type: domain` blueprints — **domain
controllers**: agent processes that own a business function, hold a port in
9700–9999, extend `patterns/domain-controller` and dispatch work to other
agents. [`common.md`](common.md) assigns those specs a directory, and the
directory it assigns them is `domains/`. There is a `weblisk domain` CLI verb
and a skill for driving it.

So a `domains/` at this corpus's root would be the second thing called a domain
sitting in the second directory called `domains/`, and the two are not related:
one is a running process, the other is a subject a policy is about.

The product already has a word for the second one and uses it everywhere the
distinction matters — `PolicyDomain`, `PolicyDomains()`, the `policy_domain`
field on a classified document, and
[`programme.md`](programme.md)'s own table: *"the **policy domains** this
programme operates in"*. Taking that word here costs one hyphen and closes the
collision. Inventing a third noun would be the fault
`platform` / `provider` / `integration` was split to fix.

**The field on a programme map stays `domains:`.** Inside a programme map there
is no ambiguity, no programme file changes, and a rename there would detach
every map in every customer repository from a word that was never wrong.

---

## Why the derived half is never written down

Measured across `programmes/`, the corpus already knows, for every domain:
which programmes claim it, which artifacts answer it (through the controls they
`satisfies`, whose own `domains` are declared), what those artifacts are —
policy, procedure, register — what recurring work they raise, who is
responsible, who approves, what is kept and for how long.

Writing any of that down a second time produces a copy that is wrong the first
time a programme changes, and the wrongness is invisible because **both halves
look right on their own**. That is the failure this corpus names for
`satisfies`/`implements`, that [`position.md`](position.md) names for role
briefs, and that the CLI's embedded-skill guard exists to catch.

So the derived half is **never written down**. It is computed on read, from the
programmes an installation has actually loaded.

## What the commentary half is for

Two things, and only two:

1. **What the domain covers, and where it stops.** `access_control`,
   `hr_security` and `physical_security` all touch a person arriving at a
   building with a badge and a laptop, and somebody has to say where the line
   is. No derivation reaches that: it is a decision, not a fact.
2. **What a programme claiming it must provide.** A domain that requires
   nothing cannot be under-served, so nothing about it can ever be reported.

---

## The declaration half — `policy-domains/catalogue/*.json`

The declaration. JSON rather than Markdown for the reason standards are: it is
a matcher's vocabulary, read by code on every classification, with no prose in
it worth diffing.

```json
{
  "version": "1",
  "domains": [
    {
      "id": "access_control",
      "name": "Access Control",
      "description": "Authentication, authorization, identity management, privilege",
      "category": "technical",
      "requires_policy": true,
      "requires_procedure": true,
      "requires_technical": true,
      "requires_evidence": true,
      "keywords": ["access", "authentication", "authorization", "rbac", "…"]
    }
  ]
}
```

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | what a programme's `domains:`, a control's `domains` and a document's `policy_domain` all join on |
| `name` | string | yes | what a person is shown |
| `description` | string | yes | one line, in a list |
| `category` | string | no | `administrative`, `technical`, `operational` — how the catalogue is grouped for reading |
| `requires_*` | bool ×4 | no | policy / procedure / technical / evidence: what the **coverage engine** looks for. Distinct from `requires:` on the commentary half, which is what the **completeness report** looks for |
| `keywords` | string[] | yes in practice | the classifier's matching vocabulary. A domain nobody can match documents into scores nothing |

**A file may declare any number of domains**, so an industry pack ships one file
rather than one per domain.

**`keywords` may not be copied into the `.md` half.** It is the one field where
a second copy does not merely drift, it *silently reclassifies documents* — and
the symptom is evidence attaching to the wrong subject with nothing anywhere to
notice. That is why the commentary half has no `name`, `description`,
`category` or `keywords` either: all four belong to the declaration, and the
rule is easier to keep as "the declaration's fields stay in the declaration"
than as one exception.

**Order is part of the contract.** Ties break on declaration order — the
classifier takes the first highest-scoring domain — so the catalogue is an
ordered list, files load in filename order, and an entry an installation
overrides keeps the **position** of the one it replaces. Ranging a map here once
produced a document that classified differently on different runs of the same
binary.

### How it reaches an installation

The blueprint path, with a floor:

| | |
|---|---|
| **embedded** | Studio compiles this catalogue in byte-for-byte, so an installation with no corpus checkout still classifies. A drift guard fails its build if the two disagree |
| **seeded** | materialised into `<root>/.weblisk/content/domains` on first start, never overwritten. Overridable without being visible is a capability nobody can reach |
| **overridden** | any `*.json` there adds a domain, or replaces a shipped one of the same id — no code change, no release |

**The embedded copy is a floor, not a second authority.** It is kept because
the catalogue is read on paths that have no corpus in reach, and the honest
behaviour of an empty catalogue is to classify nothing and score nothing —
a confident zero across every governance surface at once. The floor is also
what "override" is defined against: a pack **adds** to the built-ins and keeps
their positions, which needs built-ins to exist.

---

## The commentary half — format

`policy-domains/<domain-id>.md` — Markdown with YAML frontmatter, for the reason
programme specs and position guides are: the valuable part is prose and a
paragraph inside a JSON string cannot be reviewed, diffed or edited. Standards
are JSON here for the opposite reason.

**The filename is the id**, including its underscores: `access_control.md`. A
file declaring an `id` other than its own basename is refused. The id is what a
programme map's `domains:`, a control's `domains` and a classified document's
`policy_domain` all join on, and a file whose id has drifted from its filename
is invisible to the loader and findable by a person, which is the worst of both.

## Frontmatter

| field | type | required | means |
|---|---|---|---|
| `id` | string | **yes** | the domain id the catalogue declares. Equals the filename |
| `requires` | string[] | no | what a programme claiming this domain must provide. A **closed** vocabulary, below |
| `boundaries` | map | no | domain id → one sentence saying where this domain stops and that one starts |

**There is deliberately no `name`, no `description`, no `category` and no
`keywords`.** All four are already in the policy-domain catalogue, which is what
declares the domain in the first place. `keywords` in particular is the
classifier's vocabulary and must stay with the classifier: a copy here would
drift, and the drift would silently reclassify documents.

**There is deliberately no `programmes:` and no `standards:`.** Which programmes
claim a domain and which controls map to it are both projections over data that
already exists, for the same reason [`position.md`](position.md) has no
`programmes:`.

`source` is set by the loader and may not be claimed: provenance is a property
of where a file was found, not of its bytes.

### `requires` — a closed vocabulary

Open sets of domains, closed sets of capabilities — the same split
[`kinds.md`](kinds.md) makes, for the same reason. A domain is data and an
installation may declare its own. What a domain may *require* is code, because a
requirement nothing can evaluate reports a confident zero, which is worse than
reporting nothing.

| requirement | met when some artifact attributed to this domain… |
|---|---|
| `policy` | has `kind: policy` — the organisation has stated its position, not only its steps |
| `procedure` | has `kind: procedure` or `kind: sop` — somebody can be told how to do it |
| `register` | is a register, or `declares` one — the domain produces evidence, not only intent |
| `triggered-work` | declares an obligation with `for:` — work is raised by something happening, not only by the calendar |
| `approval` | names `approved_by` — somebody in a named position puts it in force |
| `retention` | declares a register `retention` — there is a keeping period with an authority behind it |
| `template` | names a `template` — there is a blank form, so the first use does not begin with drafting one |

**Each of these earned its place by discriminating.** The left-hand column is
the measurement that chose the vocabulary, over the 71 programme-domain claims
the corpus made at the time; the right-hand column is where the same
measurement stands over today's 72, after the sixty-six findings it produced
were worked through.

| | when the vocabulary was chosen | today |
|---|---:|---:|
| `register` | 70 / 71 | 72 / 72 |
| `procedure` | 67 / 71 | 69 / 72 |
| `triggered-work` | 47 / 71 | 60 / 72 |
| `approval` | 42 / 71 | 65 / 72 |
| `policy` | 31 / 71 | 59 / 72 |
| `retention` | 15 / 71 | 63 / 72 |
| `template` | 12 / 71 | 35 / 72 |

**A requirement nothing now fails has not stopped discriminating — it has been
answered.** Every gap the left-hand column exposed was closed by writing the
missing artifact, not by relaxing the rule, and the numbers move back the moment
a programme is added. The one to watch is `register`, which is now provided by
every claim: it is near-universal by the corpus's habits rather than by
construction, and if it is still at 72 / 72 after several more programmes it is
a sentence rather than a requirement.

Four candidates were **rejected for being always true**: an obligation existing
at all, its `cadence`, its `responsible` and its `escalate` are each provided by
70 of 71 claims, and the one exception is the same claim in every case — one
that nothing attributes to at all, which is already its own finding. A
requirement that cannot fail is not a requirement; it is a sentence that makes a
report look thorough.

`register` and `procedure` are near-universal in *today's* corpus and are kept
anyway, because they are near-universal by the corpus's habits rather than by
construction: a programme can perfectly well be written without either, and when
one is, that is exactly the thing worth saying.

### `boundaries` — and why they are reciprocal

A boundary declared on one side only is how two domains both come to believe
they own a subject. So a boundary is **reported when it is one-sided**: if
`access_control` says where it stops relative to `hr_security`, `hr_security`
must say where it stops relative to `access_control`.

The two sentences need not agree in wording and are not checked for agreement —
that would be a machine grading prose. They must merely both exist, so that a
person comparing them can see a disagreement at all.

## Body — a closed set of headings

Three `##` headings, and no others. A heading outside the set is **refused**,
not ignored: the renderer places these in a fixed order, and a section it did
not recognise would be dropped without a word.

| heading | answers |
|---|---|
| `## What this covers` | the one paragraph somebody reads first |
| `## Why these requirements` | why `requires` is that list and not a longer or shorter one |
| `## How it goes wrong` | the failure modes, named, so they are recognisable in progress |

**Every section is optional, and at least one must have content.** A file
answering one heading well is better than one written to fill slots.

There is deliberately **no heading for the boundary**: `boundaries:` is the
boundary statement, and a prose section restating it would be the second copy
this schema spends its first page refusing.

## A domain may not restate derived fact

**Enforced at load.** A file is refused when its prose contains:

- an **artifact id** — `ohs.policy`, `cohs.site-inspections` — the shape
  `<prefix>.<hyphenated-name>`
- a **register path** — `registers/site-inspections.md`

Those two and no others, and the rule is the same one
[`position.md`](position.md) enforces, for the same reason. A domain is a
subject, not a programme: prose naming an artifact has pinned a general
statement to one programme's implementation of it, and will be wrong the next
time that programme is edited, in a different file in a different family, with
nothing to notice.

Prose that says *"the hard case is the contractor who has a badge and no
contract"* is a person writing about a boundary and must stay allowed.

## What the generator may do to these files

**Nothing.** It reads them and never writes one. The seam is a **file
boundary**, not a managed region: a generator that owns part of a file
eventually owns the rest of it, and the first time somebody edits inside the
markers the tool either loses their work or stops regenerating — both silently.

---

## How a claim is attributed to a domain

This is the part that decides whether the report is worth reading, so it is
stated here rather than left to the implementation.

A programme's artifacts are attributed to a domain through the **controls they
already cite**: a spec's `satisfies` names `framework:control`, every control
declares its own `domains`, and the artifact is attributed to those — then
**intersected with the domains the programme itself claims**.

The intersection is not a detail, it is the whole reason this works. Measured:
every one of the 1431 controls in the 61 shipped frameworks carries at least one
domain, so the join always resolves. But taken raw it is far too generous — the
12 programmes' artifacts reach **70 domains their programmes never claimed**,
because a control is mapped to several domains and a spec citing it inherits all
of them. Intersected with the author's own `domains:` the attribution is exact:
the programme author declared the scope, and the control mapping only says which
part of that declared scope each artifact lands in.

**A spec with no `satisfies` is attributed to nothing**, and that is reported as
unassessable rather than as absent. 33 of the corpus's 212 specs are in that
position today, and a programme citing no framework at all is explicitly valid
([`programme.md`](programme.md)) — so a report that turned "we cannot tell" into
"you have none" would be a confident zero on a programme that may be complete.

## What is reported rather than refused

Nothing here refuses a programme. A deliberately narrow programme is
legitimate, and a rule that cannot be declined gets exempted rather than met.

| | |
|---|---|
| a programme claims a domain the catalogue does **not** declare | `unknown` — a typo, or a domain that needs declaring. It cannot be measured at all |
| a programme claims a domain and **no** artifact attributes to it | `unanswered` — the claim is decoration |
| an attributed domain is missing something its `requires` names | `incomplete`, naming the requirement |
| a programme's artifacts cite **no** controls at all | `unassessable` — stated once for the programme, never as one absence per requirement |
| a domain the catalogue declares with **no** file here | `undescribed` — claimable, with no stated boundary and no requirements |
| a file here for a domain the catalogue does **not** declare | `orphan` — either an id typo, or a domain dropped from the catalogue |
| a boundary declared on one side only | `one-sided boundary`, naming both |

These are a **separate category from the catalogue's load problems**. A
programme with an incomplete domain has not failed to load; it has loaded
perfectly and said something about itself that is worth knowing. Mixing the two
counts would make a report of substance indistinguishable from a broken file.

---

## Verification Checklist

### The declaration half

- [ ] Every entry has an `id`, a `name`, a `description` and at least one keyword
- [ ] No two entries in the catalogue share an `id`
- [ ] The embedded copy in a consumer is byte-identical to this one, and a guard says so
- [ ] A domain added here has a `policy-domains/<id>.md` beside it, or is knowingly left `undescribed`

### The commentary half

- [ ] The filename, without `.md`, equals the declared `id`
- [ ] The `id` is a domain the policy-domain catalogue declares
- [ ] Every `requires` entry is one of the seven closed values
- [ ] Every `boundaries` key is a declared domain id, and is not this domain
- [ ] Every boundary is declared on both sides
- [ ] Every `##` heading is one of the three above, spelled exactly
- [ ] At least one recognised section has content
- [ ] No artifact id and no register path appears anywhere in the body
- [ ] No `name`, `description`, `category`, `keywords`, `programmes` or `standards` field
- [ ] No individual is named, and no tenant, customer or project is named
