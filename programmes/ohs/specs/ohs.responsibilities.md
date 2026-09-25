---
id: ohs.responsibilities
kind: standard
title: Health and Safety Roles and Responsibilities
structure: standard
path: standards/health-and-safety-responsibilities.md

satisfies:
  - iso_45001:5.3
  - cor_2020:COR-03

requires: [ohs.policy]

declares:
  obligation:
    id: ohs.responsibility-review
    activity: Review of health and safety responsibilities against who holds each position
    cadence: each year
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/responsibility-reviews.md
  register:
    title: Responsibility Review Record
    note: >
      One row per position reviewed. The holder is recorded as a person and the
      duty as a position, because that is the join the platform needs: an
      obligation belongs to the position and is discharged by whoever holds it,
      and a review that names only the person cannot survive them changing jobs.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: position, label: Position, type: text, required: true}
      - {key: holder, label: Held by, type: user}
      - {key: duties_current, label: Duties still correct, type: bool, required: true}
      - {key: gap, label: Duty with no holder, type: longtext}
      - {key: reviewer, label: Reviewed by, type: user, required: true}
---

What this document must establish for THIS organisation: which positions carry
which health and safety duties, and what authority each one has to act.

It must name duties against POSITIONS, not against people. Every obligation this
programme declares has a `responsible` position, and this is the document that
says what that position is accountable for — so an obligation whose position
nobody holds is visible as a gap rather than as a task quietly not being done.

It must state, for each position, what that holder may DO and not only what they
are answerable for. A supervisor accountable for stopping unsafe work who has no
stated authority to stop it has a duty they cannot discharge, and that gap is the
one that appears in evidence after an incident rather than before.

It must include the duties the law assigns directly — an employer's, a
supervisor's, a worker's — and say where they came from, because those are not
the organisation's to redistribute. Where a duty is delegated, it must record
that the accountability was not.
