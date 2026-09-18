# Schema: Kinds

What sorts of thing the platform can talk about, what each one drives, and which
relationships are meaningful between them.

**This is data, not code.** Studio and the CLI read this declaration; neither
keeps its own list. A tool that hard-codes a kind, a layer or a relation has
moved the specification out of the blueprints — see
[`schemas/common`](common.md#adoption) for the same argument about adoption.

---

## Why this exists

Five vocabularies for "what sort of thing is this" grew independently and
disagreed: a node kind, a document kind, a source role, a chain layer, and a set
of reference kinds declared only in a comment. The disagreements were not
cosmetic — `code` existed in three of them and not in the fourth, so the logic
switching on that fourth had no case for it and silently treated code as
something else.

A kind is also **part of identity**: a node's artifact key begins with its kind,
so a classifier that answers differently on different runs makes one document
into two nodes. Kinds therefore have to be declared once and resolved the same
way everywhere.

---

## The model: open kinds, closed capabilities

**Nothing switches on a kind.** Code asks whether a kind *can* something; the
declaration says which kinds can what.

```
Kinds          open      declared here, extended freely       data
Capabilities   CLOSED    each one is a contract with code     code
```

The asymmetry is the whole design, and it is the same one
`source_categories` already makes for sources: a capability a customer invents
would be a label nothing consumes, *"which is worse than not offering it, because
it looks like configuration and does nothing."*

What this buys:

- **Adding a kind is declaring it.** No code changes, in Studio or the CLI.
- **Adding a capability is deliberate**, because something has to implement it.
- **No `switch kind` anywhere.** A `switch` over kinds is a closed set written in
  the wrong place, and it is how five vocabularies came to disagree.

### Capabilities

Closed. Each names a real behaviour and the code that honours it.

| capability | what having it means |
|---|---|
| `versioned` | its content hashes to a version, so it can go **stale**. A published control cannot |
| `has-custody` | the bytes are somewhere we can reason about; without it no custody claim may be made |
| `chain-member` | participates in an evidence chain, at the `layer` it declares |
| `counts-as-coverage` | its presence is evidence toward a control |
| `opens-gap` | its **absence** is a finding |
| `is-criterion` | it is the thing measured against, not a thing measured |
| `agent-executable` | an agent may **perform** it — it carries steps, roles and required inputs |
| `traces-to-code` | its clauses are traced to the code implementing them |
| `generates-code` | the generation pipeline reads it and produces an implementation |
| `applies-to-platform` | it configures a system we do not own |
| `proves` | terminal evidence — the end of a chain, not a link in it |

**`counts-as-coverage` and `opens-gap` are separate on purpose.** A guideline has
neither: not following advice is not a finding, and following it is not
compliance. Collapsing them into one "mandatory" flag is what let advisory
material be scored as standard-level evidence.

### Data facets

Not capabilities — values a kind declares.

| facet | meaning |
|---|---|
| `specializes` | a kind it inherits capabilities from, or empty |
| `identity` | what makes two references the same thing |
| `origin` | `authored` · `derived` · `observed` · `published` — which producer may assert it |
| `layer` | where in an evidence chain, when `chain-member` is present |

---

## Declared kinds

| kind | specializes | identity | origin | layer | capabilities |
|---|---|---|---|---|---|
| `document` | — | source + path | authored | — | versioned, has-custody |
| `policy` | — | source + path | authored | policy | versioned, has-custody, chain-member, counts-as-coverage, opens-gap |
| `standard` | — | source + path | authored | standard | versioned, has-custody, chain-member, counts-as-coverage, opens-gap |
| `procedure` | — | source + path | authored | procedure | versioned, has-custody, chain-member, counts-as-coverage, opens-gap |
| `sop` | `procedure` | source + path | authored | procedure | **+ agent-executable** |
| `guideline` | `document` | source + path | authored | — | *(inherits only)* |
| `reference` | `document` | source + path | authored | — | *(inherits only)* |
| `specification` | — | source + path | authored | — | versioned, has-custody, traces-to-code |
| `blueprint` | `specification` | source + path | authored | blueprint | **+ chain-member, generates-code, counts-as-coverage** |
| `code` | — | source + path | derived | code | versioned, has-custody, chain-member |
| `evidence` | — | source + path | authored, observed | runtime | versioned, has-custody, chain-member, proves |
| `control` | — | **framework + control id** | **published** | — | **is-criterion** |
| `platform` | — | durable system id | observed | runtime | chain-member, applies-to-platform |
| `integration` | — | durable connection id | observed | — | *(none)* |
| `component` | — | tenant + component name | derived | runtime | versioned, chain-member |
| `obligation` | — | source + path + clause | authored | procedure | versioned, has-custody, chain-member, opens-gap, agent-executable |
| `register` | — | declared register id | authored | runtime | versioned, has-custody, chain-member, proves |
| `run` | — | run id | observed | runtime | chain-member |

### What the table says, in words

**`guideline` and `reference` have neither `counts-as-coverage` nor
`opens-gap`.** They inherit `versioned` and `has-custody` from `document` and
nothing else. Advice is not compliance and its absence is not a gap — which is
the fault this replaces.

**`control` has only `is-criterion`.** No version, no custody, no chain
membership. It is a clause of somebody else's published framework: it cannot go
stale, cannot be edited, nothing derives it, and nothing may attempt to hash it.
Every other kind is content that lives somewhere; a control is what content is
measured against.

**`sop` adds `agent-executable` to `procedure`.** Everything written for
procedures applies to it unchanged; an agent additionally may perform it.

**`blueprint` adds generation to `specification`.** Every specification traces to
the code implementing it; a blueprint also generates and participates in a chain.

**`run` is an execution, not content.** It is not versioned — an event does not
change — and it does not `prove`: an execution record is corroboration that
something happened, and durable evidence is an `evidence` artifact or an
attestation. See the audit join in the fabric design for the same distinction.

**`integration` has no capabilities**, and that is correct rather than an
omission. It is a boundary, not a subject: a service consumed to do a task
governs nothing, and saying so explicitly is what stops an ordinary consumption
reading as an ungoverned platform.

---
## Evidence chain layers

The chain runs from why, through what and how, to what is actually running. A
kind with `chain-member` declares which layer it occupies; the ORDER below is
the chain's order, and it is data because more than one view renders it.

| # | layer | asks |
|---|---|---|
| 0 | `policy` | why — the commitment |
| 1 | `standard` | what — the measurable requirement |
| 2 | `procedure` | how, who, when |
| 3 | `blueprint` | how, as a technical capability |
| 4 | `code` | how, as concrete logic |
| 5 | `runtime` | what is actually happening |

**A kind without `chain-member` has no layer and no position.** It is not placed
at the end, or in the middle, or anywhere — it is absent from the chain. Two
separate implementations used to default an unrecognised kind into a layer
(`standard` in one, `blueprint` in the other), which put unknown documents into
an evidence chain and scored them.

---

## Classification

How a document's kind is decided from where it sits, when nothing has declared
it explicitly.

### The rule

**Directories outrank filenames, and the nearest directory wins.** A directory
says what KIND of thing lives here; a filename says what this one is ABOUT. So
`patterns/policy.md` is a blueprint that discusses policy, while
`standards/policies/acceptable-use.md` is a policy, because the directory it
sits in says so.

Segments are read **deepest-first**, then the filename, then — if nothing
matches — the kind is `document`, meaning **unclassified**. `document` is not a
fallback that makes a file count as something; it is the honest absence of a
classification, and it contributes nothing to an evidence chain.

Within one segment, the **first stem in the table below** wins. The order is the
tie-break and is therefore part of the declaration.

### Stems

| kind | stems |
|---|---|
| `evidence` | evidence, proof, attestation |
| `sop` | sop, runbook, runbooks, playbook |
| `procedure` | procedure, procedures |
| `policy` | policy, policies |
| `guideline` | guideline, guidelines, guide, guides |
| `reference` | reference, references |
| `standard` | standard, standards, schemas |
| `blueprint` | blueprint, blueprints, architecture, patterns, protocol, platforms, agents |

`architecture`, `patterns`, `protocol`, `platforms` and `agents` are the family
directories of this corpus, and a document in one of them is a framework
blueprint. `schemas` states the structure blueprints must satisfy, which is a
measurable requirement — a standard.

**This is a weak signal and it is the one available before anything has been
classified.** It decides a node's kind, never whether a control is answered —
the control's own data does that — so a wrong guess mislabels a node rather than
inventing or hiding coverage. A document that states its own kind overrides it.

### Content signals

Where a path says nothing, the words a document uses are the next-weakest
evidence. Each kind may declare signal phrases and a weight; the highest score
wins, and **a tie leaves the document unclassified** rather than picking one.

| kind | weight | signals |
|---|---|---|
| `sop` | 3 | runbook, playbook, sop, standard operating, checklist, prerequisite |
| `procedure` | 2 | step 1, step 2, procedure, process, workflow, responsible:, trigger:, when to, how to |
| `evidence` | 2 | evidence, attestation, audit log, screenshot, certificate, test result, scan result |
| `policy` | 1 | shall, must, policy, commitment, organization shall, we will, our policy, mandatory |
| `standard` | 1 | requirement, shall implement, minimum, baseline, standard, specification, criteria |
| `blueprint` | 1 | blueprint, architecture, component, service, interface, capability, tier:, type: |
| `guideline` | 1 | should, recommend, consider, best practice, guidance, suggestion |

Weights are relative and deliberately coarse: `sop` outranks `procedure` because
a runbook is a procedure written in more detail, and a document showing both
should be read as the more specific.

**Scoring nothing means `document`.** The default used to be `reference`, which
was a chain member — so a file matching no signal at all was classified as
technical reference material and scored as standard-level evidence.

### One implementation

Deciding a kind is one question and must have one implementation. Two
classifiers make the same file two different nodes depending on which subsystem
asked, and because a kind is part of a node's identity, the edges recorded
against one are invisible from the other.

---

## Relations

Which relations are meaningful, between which kinds, in which direction. A
relation asserted outside this table is a fault in the producer, not a new
relation.

| relation | from | to | asserted by |
|---|---|---|---|
| `addresses` | policy, procedure, standard, document | `control` | conformance |
| `mentions` | any content kind | `control` | conformance |
| `implements` | blueprint, policy, procedure | blueprint, **control** | declared |
| `requires`, `extends`, `depends_on`, `supersedes` | blueprint | blueprint | declared |
| `implemented_by` | specification | `code` | implementation |
| `generated_from` | `code` | blueprint | generation |
| `applies_to` | `code` | `platform` | platform configuration |
| `reached_through` | `platform` | `integration` | integration |
| `enforced_by` | policy, standard, procedure | `platform`, `component` | platform |
| `deployed_as` | blueprint | `component` | composition |
| `discharges` | `evidence` | `obligation` | programme |
| `contains` | any | itself, unanchored | **synthesised, never stored** |

`implements` accepting `control` as a target is what allows an author to state
which control a document answers, instead of leaving it to keyword inference.

### Naming a target's kind

A declared target may qualify its kind as `kind:id`:

```yaml
implements: [control:A.5.15]        # this policy answers that control
requires:   [protocol/spec.md]      # unqualified: a blueprint, as before
```

An identifier alone cannot say what it is, and **guessing from its shape is how
a platform comes to assert something an author never said**. So an unqualified
target keeps its previous meaning — a blueprint — and anything else is named.

A prefix is only a qualifier when it is a **declared kind**, so a colon in a URL
or a path is left alone.

A pairing this table does not permit is **skipped**, not recorded: a claim
nothing can justify is worse than an absent one, and the corpus validator is
where an author is told about it.

---

## Rules

1. **Nothing switches on a kind.** Code asks for a capability. A `switch` over
   kind names is a closed set written in the wrong place — it is how five
   vocabularies came to disagree, and it is why adding a kind used to mean
   editing code in two repositories.
2. **An undeclared kind is representable and is reported as undeclared.** It is
   never silently defaulted, and it gains no capability by default. Openness is
   deliberate; an unknown must say it is unknown.
3. **A capability without an implementation must not be declared.** It would look
   like configuration and do nothing.
4. **A specialisation adds capabilities; it never removes them.** If a child
   needed to drop one, the parent was wrong.
5. **Identity is declared per kind.** A path is not an identity where several
   sources are in scope, and an address is never an identity for a platform.
6. **An absent capability is a real answer.** No `counts-as-coverage` means this
   never counts; no `chain-member` means it contributes nothing to a chain. These
   are not gaps to be filled by a default.
7. **One classifier.** Deciding a document's kind is one question and must have
   one implementation; two classifiers make the same file two nodes depending on
   which subsystem asked.

---

## Verification Checklist

- [ ] Every declared kind's `specializes` names a declared kind or is empty
- [ ] Every capability a kind declares is one this schema declares
- [ ] No specialisation removes a capability its parent declares
- [ ] A kind without `chain-member` contributes nothing to an evidence chain and renders as unclassified
- [ ] A kind without `counts-as-coverage` never raises a coverage figure
- [ ] A kind without `opens-gap` never produces a finding by its absence
- [ ] An undeclared kind is reported as undeclared and is granted no capability
- [ ] `control` declares only `is-criterion`, and nothing attempts to version or hash it
- [ ] No implementation switches on a kind name; capability is the only question asked
- [ ] A relation asserted between kinds this file does not pair is reported as a producer fault
- [ ] Two references to one artifact from different subsystems resolve to the same kind
