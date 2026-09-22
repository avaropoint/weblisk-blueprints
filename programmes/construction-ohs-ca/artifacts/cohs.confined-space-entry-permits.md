---
id: cohs.confined-space-entry-permits
kind: register
title: Confined Space Entry Permits
structure: standard
path: registers/construction/confined-space-entry-permits.md

# A register carries no `satisfies:`.
#
# It is the evidence that work happened, not the document that answers a
# control — and the relation vocabulary says so structurally: `implements`
# onto a control may be asserted by a blueprint, a policy or a procedure,
# and by nothing else. A register citing a control could never be recorded
# as answering it, so it sat at `present_uncited` permanently and capped the
# tier's readiness at a number no amount of work could move.
#
# The citation belongs on the procedure that declares this register, which
# is where the organisation states what it does; this file is where it
# records having done it.

requires: [cohs.confined-space]

register:
  title: Confined Space Entry Permits
  note: >
    One row per ENTRY, not one per space and not one per day. A separate permit
    is required each time before entry, because the permit is a statement about
    the conditions at that moment: the atmosphere tested, the isolation verified,
    the attendant named, the rescue arrangement in place. A permit reused for a
    second entry is a statement about a moment that has passed.
  layout: form
  review: required
  approvers: [site-supervisor]
  retention:
    keep: 1y
    from: project-finished
    authority: O. Reg. 632/05 s. 21(2) — on a project, the records shall be kept available at the project and retained for one year after the project is finished
    reason: >
      The clock runs from the project ending rather than from the record being
      created, so a permit written in the first month of a three-year job is kept
      for four years and a permit written in the last week is kept for one. A
      retention counted from creation would dispose of the early records while
      the project was still running.
  columns:
    - {key: permit_id, label: Permit, type: text, required: true}
    - {key: project, label: Project, type: relation, required: true,
       target: /registers/construction/projects.md#records, display: project_id}
    - {key: space, label: Space, type: text, required: true}
    - {key: entry_on, label: Date of entry, type: date, required: true}
    - {key: entry_from, label: Permit valid from, type: text, required: true}
    - {key: entry_to, label: Permit valid to, type: text, required: true}
    - {key: work, label: Work to be done, type: longtext, required: true}
    - {key: hazards, label: Hazards identified in the assessment, type: longtext, required: true}
    - {key: isolation, label: Isolation and lockout verified, type: bool, required: true}
    - {key: initial_test_oxygen, label: Oxygen at initial test, type: number, required: true}
    - {key: initial_test_flammable, label: Flammable gas or vapour at initial test, type: number, required: true}
    - {key: initial_test_toxic, label: Toxic contaminants at initial test, type: longtext, required: true}
    - {key: tester, label: Testing done by, type: user, required: true}
    - {key: continuous_monitoring, label: Continuous monitoring in place, type: bool, required: true}
    - {key: ventilation, label: Ventilation, type: longtext}
    - {key: attendant, label: Attendant, type: user, required: true}
    - {key: entrants, label: Entrants, type: longtext, required: true}
    - {key: rescue_arrangement, label: Rescue arrangement in place, type: longtext, required: true}
    - {key: issued_by, label: Issued by, type: user, required: true}
    - {key: closed_on, label: Entry closed and all entrants accounted for, type: date, required: true}
---

What this artifact must establish: that before each entry into each confined
space, somebody with authority confirmed a specific list of conditions — and that
the confirmation survives the entry.

It is a **form and not a grid**, and this is the clearest case in the programme
for the distinction. A grid commits every keystroke to the record, so a
half-completed permit would land in the governance repository as a permit while
somebody was still working out whether the space had been isolated. A permit is a
statement that a set of conditions holds at one moment, made by one person who
can be identified afterwards. That requires one attributable act.

The atmospheric results are **numbers and not a pass/fail box**. A permit
recording "atmosphere acceptable" cannot be reviewed afterwards, cannot be
trended, and cannot show that the same space reads differently in July than in
February. The value is the evidence; the judgement is what the issuer added to it.

`closed_on` and its label are not administrative tidiness. The permit is not
finished when the work is; it is finished when every entrant is out and accounted
for, and a register full of permits with no closure cannot answer the only
question that matters during an emergency.

The retention runs from **the project being finished**, which is an event rather
than a date on the record. Until the project register records a closing date the
platform will report the disposal date as unresolvable, and that is the correct
behaviour: it keeps the record rather than disposing of it early on a guess.

It must be kept **available at the project**, not only in a head office system.
The regulation says so, and the practical reason is the same as the legal one: an
inspector and a rescue team both need it where the space is.
