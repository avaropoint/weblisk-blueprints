---
id: priv.breach-review
kind: procedure
title: Privacy Breach Record Review
structure: procedure
path: procedures/privacy-breach-record-review.md

satisfies:
  - pipeda:PIPEDA-BR-2
  - pipeda:PIPEDA-10
  - quebec_law25:BS-2

requires: [priv.breach-response]

declares:
  obligation:
    id: priv.breach-record-review
    # The chain terminates in a cadence on purpose. A trigger whose recording
    # register is its own trigger register discharges every occurrence the
    # moment it creates one, so the last link is a periodic sweep of what is
    # open, late, or approaching the end of its retention period.
    activity: Review the privacy breach record — what is unassessed, what is due to be disposed of, and what keeps happening
    cadence: each quarter
    authority: PIPEDA s. 10.3 — records of every breach kept for 24 months
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/privacy-breach-record-reviews.md
  register:
    title: Privacy Breach Record Review
    note: >
      One row per review period. `unassessed` is what the sweep is for: a breach
      recorded and never assessed raises one overdue occurrence and then stays
      exactly as overdue, which is easy to stop seeing.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: period, label: Period covered, type: text, required: true}
      - {key: breaches_recorded, label: Breaches recorded in the period, type: int, required: true}
      - {key: unassessed, label: Breaches not yet assessed, type: int, required: true}
      - {key: reported, label: Reported to a regulator, type: int, required: true}
      - {key: repeat_causes, label: Causes seen more than once, type: longtext, required: true}
      - {key: records_due_disposal, label: Records reaching 24 months, type: int, required: true}
      - {key: actions, label: Actions arising, type: longtext, required: true}
---

What this document must establish for THIS organisation: what is done with the
breach record between breaches.

It must look for the cause that repeats. Misdirected email is the most common
privacy breach in every organisation that measures it, and it is fixable — a
delay on external sending, a warning on external recipients, a different address
book layout. One breach is an event; the fourth is a control that does not
exist.

It must check that every recorded breach was assessed. The record-keeping duty
covers all of them and the assessment is what decides notification; a breach
sitting unassessed for a quarter is a notification decision nobody made, and
under the Act that is the same as deciding not to notify.

It must watch the twenty-four month boundary. The records must be kept that
long, and after that they fall under the retention schedule like anything else —
keeping them forever is its own privacy problem, because a breach record
contains the personal information of the people affected.

It must feed the annual privacy programme review rather than duplicating it.
Four quarterly sweeps produce the numbers that review reads.
