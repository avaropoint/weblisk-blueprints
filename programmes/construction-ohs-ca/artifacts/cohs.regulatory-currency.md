---
id: cohs.regulatory-currency
kind: register
title: Register of Applicable Law, Standards and Editions
structure: standard
path: registers/construction/legal-requirements.md

satisfies:
  - cor_2020:COR-04
  - iso_45001:6.1.3
  - iso_45001:9.1.2

requires: [cohs.policy]

register:
  title: Register of Applicable Law, Standards and Editions
  note: >
    One row per instrument that binds this organisation. `consolidation_read` and
    `edition_named` are what make this different from a reading list: a statute
    listed and never read against is a citation, and an incorporated standard
    cited without the edition the regulation names is a compliance claim about
    the wrong document. `not_yet_in_force` exists because in this domain the
    most expensive surprises are scheduled ones.
  columns:
    - {key: instrument, label: Instrument, type: text, required: true}
    - {key: citation, label: Citation, type: text, required: true}
    - {key: kind, label: Kind, type: select, required: true,
       options: [Statute, Regulation, Incorporated standard, Code, Guideline or policy,
                 Contractual requirement]}
    - {key: applies_because, label: Applies because, type: longtext, required: true}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: how_met, label: How it is met, type: longtext, required: true}
    - {key: consolidation_read, label: Consolidation or version read, type: text, required: true}
    - {key: edition_named, label: Edition named by the instrument, type: text}
    - {key: edition_current, label: Current published edition, type: text}
    - {key: not_yet_in_force, label: Enacted but not yet in force, type: longtext}
    - {key: last_evaluated, label: Last evaluated, type: date, required: true}
    - {key: compliant, label: Compliant at last evaluation, type: select, required: true,
       options: ["Yes", "No", Partially, Not yet evaluated]}
    - {key: next_due, label: Next evaluation due, type: date, required: true}

declares:
  obligation:
    id: cohs.legislative-review
    activity: Review of the register against the current consolidations, and evaluation of compliance with what it lists
    cadence: each quarter
    authority: ISO 45001:2018 clause 9.1.2 requires compliance to be evaluated at planned intervals; COR 2020 requires applicable legislation to be identified and kept current. Neither sets an interval
    interval_basis: chosen
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/construction/legal-requirements.md
    escalate: {after: 4w, to: senior-management}
---

What this artifact must establish: every legal and other requirement that binds
this organisation's construction health and safety, which version of it was read,
and whether it is currently being met.

It must say for each requirement **why it applies** — the province, the kind of
work, the equipment, the headcount, the client. A register of everything that
might apply somewhere is unusable, and a requirement listed without its trigger
cannot be maintained when the trigger changes.

**The edition columns are the substance of this artifact and they are what most
legal registers omit.** Ontario construction law incorporates standards by
reference, and it incorporates **specific editions**, several of which are two
editions behind what the standards body now publishes. So there are three
different claims an organisation can make and they need three different pieces of
evidence:

- *We comply with the regulation* — which requires conformance to the **edition
  the regulation names**.
- *We comply with the current standard* — a different and usually stronger claim.
- *We comply with the standard* — which, unqualified, is not a claim anybody can
  check.

Titles drift between editions as well as numbers, so a specification citing a
standard by its name may be citing a document that no longer exists under that
name. And at least one incoming Ontario requirement names a standard **with no
edition year at all**, which means that obligation floats to whatever is current —
the opposite behaviour from every other reference around it, and it needs its own
row and its own watch.

**`not_yet_in_force` is not future-gazing; it is the cheapest risk control in the
register.** Ontario publishes enacted-but-not-commenced instruments, and in this
domain they carry real work: an elevating work platform regime replacing the
current one on a known date, with a **per-worker** transition anchored to each
worker's original training date; a head protection requirement becoming
standard-referenced on a later date. Both need action before they commence, and
both are invisible to a register that only records what is in force today.

It must include the requirements that do **not** come from law. A client's site
rules, a prequalification scheme's conditions, a collective agreement and an
insurer's terms all bind the programme, and an organisation held to a client
standard it never wrote down discovers it during an audit of that client's making.

It must record **who read what, and when**. That is the whole difference between
this register and a bibliography, and it is why the review obligation records into
this same file: the evaluation and the register are one artifact rather than a
document plus a log of having read it.

**The quarterly review is this organisation's choice.** Neither the standard nor
the accreditation scheme sets an interval. A quarter is chosen because
consolidations and commencement dates move on that sort of rhythm, and because a
change that takes effect on 1 January must be seen before December.

A caution belongs in the document itself: an instrument's published consolidation
is not always the whole answer. At least one construction-adjacent requirement in
Ontario is varied by an order from a regulator rather than by an amendment to the
regulation, and a register built only from the consolidated text will be wrong
about it while looking complete. Where the organisation knows of such a case, the
row should say so.
