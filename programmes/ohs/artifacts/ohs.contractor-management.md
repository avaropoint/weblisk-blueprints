---
id: ohs.contractor-management
kind: procedure
title: Contractor and Subcontractor Management
structure: procedure
path: procedures/contractor-management.md

satisfies:
  - iso_45001:8.1.4
  - cor_2020:COR-15
  - isnetworld:ISN-SAFE-12

requires: [ohs.responsibilities]

declares:
  obligation:
    id: ohs.contractor-evaluation
    activity: Evaluation of an engaged contractor's health and safety performance
    cadence: each year
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/contractor-evaluations.md
  register:
    title: Contractor Evaluation Record
    note: >
      One row per contractor evaluated. `prequalified_on` and `evaluated_on` are
      separate dates on purpose: prequalification is a judgement made before the
      work and evaluation is a judgement made after it, and a programme that
      records only the first has never checked whether the judgement was right.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: contractor, label: Contractor, type: text, required: true}
      - {key: work_performed, label: Work performed, type: text, required: true}
      - {key: prequalified_on, label: Prequalified on, type: date}
      - {key: evaluated_on, label: Evaluated on, type: date, required: true}
      - {key: incidents, label: Incidents on our sites, type: int, required: true}
      - {key: findings, label: Findings raised against them, type: int, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Approved, Approved with conditions, Not to be re-engaged]}
      - {key: conditions, label: Conditions, type: longtext}
      - {key: evaluator, label: Evaluated by, type: user, required: true}
---

What this document must establish for THIS organisation: how somebody else's
workers become safe on our site, and whose duty that is.

It must be clear about the duty first. Engaging a contractor transfers work and
not accountability, and a procedure written as though it did produces the exact
gap this control exists to close: two organisations each believing the other was
supervising.

It must set out what is required BEFORE engagement — the safety programme, the
insurance and clearance certificates, the statistics, the competency evidence for
the specific work — and who checks it rather than who collects it. A file of
certificates nobody read is prequalification theatre.

It must cover the work while it is happening: orientation to OUR hazards, whose
rules apply where they conflict, how our inspections cover their work, and how a
concern about their crew reaches somebody who can act.

It must cover the layer down. A subcontractor engaged by a contractor is on the
site under the same duty, and a procedure that stops at the first tier stops
where the risk usually is.

It must say what ends an engagement, and that the decision is recorded — because
a contractor removed from a site and re-engaged next season by a different
project manager is the failure this register exists to prevent.
