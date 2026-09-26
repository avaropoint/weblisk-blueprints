# Positions

**The hand-written half of what the platform can say about a job somebody holds
inside an organisation.**

Governed by [`../schemas/position.md`](../schemas/position.md).

A programme names positions: an obligation's `responsible`, an `escalate.to`, a
register's `approvers`, an artifact's `approved_by`. Across
[`../programmes/`](../programmes/) that is **twenty-one positions, named 475
times**. Everything those namings imply — how often the work recurs, where each
occurrence is recorded, what authority requires it, what escalates in and from
whom, what escalates away and how fast, what nobody else can sign — is
**derived**, on read, and is never written down here.

What is written here is the part derivation cannot reach: what to do first, what
a good version of the job looks like, how it goes wrong, and what the trade
calls it.

## Why the split is a file boundary

A guide that also listed the obligations would be a second copy of the
programmes, and it would be wrong the first time one changed — invisibly,
because both halves would look right on their own. That is the failure this
corpus already names for `satisfies`/`implements`, and the reason the CLI's
embedded skills are guarded byte-for-byte.

So there is **no merge, no managed region, and no generated block with markers
around it**. The generator reads these files and never writes one. A generator
that owns part of a file eventually owns the rest of it: the first time somebody
edits inside the markers, the tool either loses their work or stops
regenerating, and both failures are silent.

## Why the derived half is not a file either

Because it is a function of **which programmes an organisation adopted** and **at
which tier**, and neither is knowable here. The same position id under two
programmes is two different jobs:

| | obligations owned | escalations arriving |
|---|---:|---:|
| `health-safety-lead` under `construction_ohs_ca` | 15 | 17 |
| `health-safety-lead` under `ohs` | 15 | 1 |

A file committed here would have to pick, and the only defensible pick — the
union of everything shipped — is wrong for every real organisation.

## Not a roster

A position exists because a programme names it. These files are **commentary on
positions the programmes have already declared**, never a declaration that one
exists. A file here for a position nothing names is reported as an orphan; a
position with no file still renders a brief, which says the judgement is missing
rather than inventing it.

**A position id must not move.** Obligations, escalations, approvals and a
tenant's own record of who holds what all join on it.

## The shape on disk

    positions/<position-id>.md

Markdown with YAML frontmatter. The filename is the id. The body is five
`## ` headings from a closed set, every one optional, and a heading outside the
set is refused rather than dropped — a person's writing must not be lost to a
typo.

## What is here

| | |
|---|---|
| [`health-safety-lead.md`](health-safety-lead.md) | the position most heavily named across the corpus for *performing* work |
| [`site-supervisor.md`](site-supervisor.md) | the position that carries almost all of the daily and weekly work |
| [`senior-management.md`](senior-management.md) | the position that performs almost none of it and is the end of every escalation path |

Three, deliberately, and not fourteen. They are chosen to be the three
*different shapes* of job the derivation has to render legibly — one that
performs, one that performs on a daily clock, and one that only receives and
signs. A guide for a position nobody has thought hard about would be the thing a
reader learns to skip, and then they skip the one that mattered.

## Not the tenant's

What an organisation calls these jobs, who holds one, and what it adds to the
description is **the customer's**, in the customer's repositories. Nothing here
records a person, an organisation or a project.
