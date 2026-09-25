---
id: rec.legal-holds
kind: register
title: Legal Hold Register
structure: standard
path: registers/legal-holds.md

satisfies:
  - iso_27001:A.5.31
  - iso_27001:A.5.33
  - iso_27001:A.5.28

requires: [rec.legal-hold]

register:
  title: Legal Hold Register
  note: >
    One row per hold, opened when litigation, an investigation, an audit or a
    regulatory request becomes reasonably foreseeable — not when it is served.
    The duty to preserve arises from anticipation, and an organisation that
    waits for the statement of claim has had a month of routine deletion running
    over the evidence.

    `review_due` drives the review obligation, because a hold that outlives its
    matter is its own problem: it defeats the retention schedule, and an
    organisation with eleven-year-old holds is keeping everything by accident.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: matter, label: Matter, type: text, required: true}
    - {key: trigger, label: What triggered it, type: select, required: true,
       options: [Claim served, Litigation anticipated, Regulatory investigation, Audit,
                 Access request, Insurance claim, Internal investigation, Other]}
    - {key: issued_on, label: Issued on, type: date, required: true}
    - {key: issued_by, label: Issued by, type: user, required: true}
    - {key: scope, label: Records and systems in scope, type: longtext, required: true}
    - {key: custodians, label: Custodians notified, type: longtext, required: true}
    - {key: automated_deletion_suspended, label: Automated deletion suspended, type: bool, required: true}
    - {key: schedule_entries, label: Retention schedule entries affected, type: longtext, required: true}
    - {key: review_due, label: Next review due, type: date, required: true}
    - {key: released_on, label: Released on, type: date}
    - {key: status, label: Status, type: select, required: true,
       options: [Active, Under review, Released, Superseded]}
---

What this artifact must establish: every preservation obligation currently in
force, what it covers, and who was told.

It exists because the retention schedule is otherwise a destruction instruction.
Automated disposition is exactly what an organisation wants until the moment a
claim is anticipated, and the only thing standing between those two states is a
register somebody checks.

`automated_deletion_suspended` is a required boolean because it is the step that
is forgotten. Notifying custodians stops people deleting deliberately; it does
nothing about the mailbox policy that removes anything over two years old, and
that policy will quietly destroy the most relevant material in the case.

`custodians` names people rather than systems, because the preservation notice
has to reach the individuals who hold the records and be repeated. A hold issued
once, two years ago, to a group that has since turned over by half is a hold
nobody current has heard of.

A released hold stays on the register. The question of when a preservation
obligation ended is asked far more often than the question of when it began.
