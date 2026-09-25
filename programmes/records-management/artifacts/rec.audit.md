---
id: rec.audit
kind: procedure
title: Records Management Audit
structure: procedure
path: procedures/records-management-audit.md

satisfies:
  - iso_27001:A.5.35
  - iso_27001:A.5.36
  - iso_9001:9.2
  - fippa_mfippa:FM-07
  - soc2:CC4.1

requires: [rec.retention-schedule, rec.disposition]

declares:
  obligation:
    id: rec.audit
    activity: Audit records management — what is held, what should have gone, and what cannot be found
    cadence: each year
    interval_basis: chosen
    responsible: records-manager
    applies_to: the organisation
    records: registers/records-audits.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Records Management Audit Record
    note: >
      One row per audit. `held_beyond_retention` and `disposed_early` are both
      counted because the programme has two opposite failure modes, and an audit
      that measures only one of them will report the organisation as improving
      while it gets worse in the other direction.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: audited_on, label: Audited on, type: date, required: true}
      - {key: auditor, label: Auditor, type: user, required: true}
      - {key: auditor_independent, label: Auditor independent of the records function, type: bool, required: true}
      - {key: classes_sampled, label: Record classes sampled, type: int, required: true}
      - {key: held_beyond_retention, label: Classes held beyond their retention period, type: int, required: true}
      - {key: disposed_early, label: Cases of disposal before the period expired, type: int, required: true}
      - {key: records_not_found, label: Records that could not be located, type: int, required: true}
      - {key: disposals_without_record, label: Disposals with no disposition record, type: int, required: true}
      - {key: unscheduled_repositories, label: Repositories not covered by the schedule, type: int, required: true}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: actions, label: Actions and owners, type: longtext, required: true}
---

What this document must establish for THIS organisation: how somebody checks
that the schedule is being followed in both directions.

It must sample the estate rather than review the schedule. A schedule can be
perfect and unexecuted, and reading it proves nothing: the audit has to go to the
shared drive, the mailbox, the storage boxes and the supplier's system and ask
what is actually there.

It must look for repositories the schedule has never heard of. Every
organisation has them — a departed manager's drive, a project archive, a backup
server kept "just in case", a box in a basement — and they hold records under no
retention rule at all, which means everything in them is discoverable and nothing
in them is disposed of.

It must count disposals that happened without a disposition record. Those are
the ones that cannot be defended later, and they are more common than disposals
under the schedule in most organisations.

It must check the joins, not just the contents: whether the personal information
inventory's retention classes exist in the schedule, whether the employment
records the Employment Standards Act requires are covered, and whether classes
under legal hold have had their disposition suspended.

It must not duplicate the document control programme's internal audit. That one
asks whether controlled documents are current and approved; this one asks whether
records are kept for as long as they should be and no longer.
