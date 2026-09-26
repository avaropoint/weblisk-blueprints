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

## Why there are two halves at all

Measured across `programmes/`, the corpus already knows, for every position:
which obligations name it `responsible`, how often each one recurs, where each
occurrence is recorded, what authority requires it, which registers it approves
submissions to, which documents it puts in force, what escalates to it and from
whom, and what it escalates away and how fast. Twenty-one positions, named 475
times between them.

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

## Verification Checklist

- [ ] The filename, without `.md`, equals the declared `id`
- [ ] The `id` is a position at least one programme in `programmes/` names
- [ ] Every `##` heading is one of the five above, spelled exactly
- [ ] At least one recognised section has content
- [ ] No artifact id and no register path appears anywhere in the body
- [ ] Nothing in the body restates a cadence, an authority, an escalation target
      or an approver — all four are rendered from the programmes beside it
- [ ] No individual is named, and no tenant, customer or project is named
