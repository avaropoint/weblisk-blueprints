---
id: rec.policy
kind: policy
title: Records Management Policy
structure: policy
path: policies/records-management-policy.md

satisfies:
  - iso_27001:A.5.33
  - iso_27001:A.5.37
  - iso_9001:7.5
  - pipeda:PIPEDA-5
  - iso_22301:7.5
  - soc2:C1.2

approved_by: [senior-management]

declares:
  obligation:
    id: rec.programme-review
    activity: Review the records management programme and the retention schedule as a whole
    cadence: each year
    interval_basis: chosen
    responsible: records-manager
    applies_to: the organisation
    records: registers/records-programme-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Records Management Programme Review Record
    note: >
      One row per review. `classes_without_authority` is the column that makes
      the schedule defensible: a keeping period with no citation is a number
      somebody chose, and the difference between that and a requirement is the
      whole of the difference between a schedule and a habit.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: classes_total, label: Record classes in the schedule, type: int, required: true}
      - {key: classes_without_authority, label: Classes with no cited authority, type: int, required: true}
      - {key: classes_added, label: Classes added, type: int, required: true}
      - {key: legal_changes, label: Legal or contractual changes affecting retention, type: longtext, required: true}
      - {key: disposals_completed, label: Disposals completed in the period, type: int, required: true}
      - {key: disposals_overdue, label: Disposals overdue, type: int, required: true}
      - {key: holds_active, label: Legal holds active, type: int, required: true}
      - {key: actions, label: Actions arising, type: longtext, required: true}
---

What this document must establish for THIS organisation: what counts as a
record, who owns it, how long it is kept and who may destroy it.

It must define a record in a way that covers the places records actually are.
Email, chat messages, shared drives, the CRM, a subcontractor's system and a
phone in somebody's pocket all hold records, and a policy that describes filing
cabinets governs a fraction of the estate.

It must state the two failures it exists to prevent, because they pull in
opposite directions and an organisation that names only one will commit the
other. Destroying a record too early — before a statutory period expires, or
while a proceeding is contemplated — is spoliation and a contravention.
Destroying nothing is the commoner failure: keeping everything forever multiplies
what a breach exposes, what an access request must search, what a discovery
order reaches, and what the organisation pays to store.

It must say who decides. A retention period is a legal judgement rather than a
preference, and the policy must name the position that owns the schedule and the
route by which a business area proposes a change.

It must say that nothing is destroyed while it is under legal hold, and that the
hold overrides the schedule in every case. That single sentence is the most
important one in the document, and the only thing that makes automated
disposition safe.

It must cover records held by others on the organisation's behalf. A cloud
service that never deletes, a payroll provider with its own retention defaults,
and a storage company with a box nobody has looked at since 2009 are all within
the schedule's scope and outside most organisations' control.
