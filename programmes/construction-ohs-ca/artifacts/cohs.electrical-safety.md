---
id: cohs.electrical-safety
kind: procedure
title: Electrical Safety and Control of Hazardous Energy
structure: procedure
path: procedures/electrical-safety.md

satisfies:
  - o_reg_213_91:181
  - o_reg_213_91:182
  - o_reg_213_91:188
  - o_reg_213_91:191
  - csa_z462:Z462-01
  - csa_z462:Z462-02
  - csa_z462:Z462-03
  - csa_z462:Z462-04
  - cor_2020:COR-08

requires: [cohs.pre-task-hazard-assessment]

declares:
  obligation:
    id: cohs.electrical-safety-review
    activity: Review of electrical work on the project — the measures for work near energized conductors, the permits issued, and the isolations in force
    cadence: each month
    authority: O. Reg. 213/91 ss. 181, 188, 191. The duties are continuous and no review interval is prescribed
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/electrical-safety-reviews.md
    escalate: {after: 1w, to: health-safety-lead}
  register:
    title: Electrical Safety Review Record
    note: >
      One row per project per month. `written_measures_issued` records the
      CONSTRUCTOR's duty rather than the employer's: where work will be done near
      an energized overhead conductor, the constructor establishes written
      measures and makes them available to every employer on the project, and an
      employer that has not received them cannot have explained them to its
      workers.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: overhead_conductors_present, label: Energized overhead conductors in or near the work, type: bool, required: true}
      - {key: highest_voltage, label: Highest conductor voltage, type: text}
      - {key: minimum_distance, label: Minimum distance required, type: text}
      - {key: written_measures_issued, label: Constructor's written measures issued to every employer, type: bool}
      - {key: operator_notified, label: Operators notified in writing before work began, type: bool}
      - {key: signs_at_operator_station, label: Legible sign at each operator's station, type: bool}
      - {key: permits_issued, label: Energized electrical work permits issued this period, type: int, required: true}
      - {key: isolations_in_force, label: Isolations and lockouts in force, type: longtext}
      - {key: rescue_capable_worker, label: Competent worker able to perform rescue including CPR stationed where required, type: bool}
      - {key: findings, label: Findings, type: longtext}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: who may work on or near
electrical equipment, what distance must be kept from energized conductors, how
energy is isolated and proved dead, and who can get a person off a conductor.

It must state the **minimum distances from an energized overhead conductor** as
the regulation states them — 3 m from 750 V to 150 kV, 4.5 m above 150 kV to
250 kV, and 6 m above 250 kV — and must be clear that these are distances for
**any part of the equipment, the load or the worker**, not for the operator's
seat.

It must place the duty to establish written measures and procedures for work near
those conductors where the regulation places it: **on the constructor**, made
available to every employer on the project, including warning devices visible to
the operator, **written notification to the operator before work begins**, and a
legible sign at the operator's station. The **employer** must then give the worker
a copy and explain it. Two duty holders, two acts, and an organisation that is
both must do both.

It must state that work on or near a transmission or distribution system is to be
performed in accordance with the electrical utility safety rules the regulation
incorporates — **and by the revision the regulation names**. An incorporated
document binds at the named revision, not at whatever the publisher currently
sells, and the year in the regulation is the one to work to. Where the publisher
has since issued a newer revision, the difference between the two is a decision
somebody has to make and record, not a detail to be resolved by buying the
current book.

It must require a **competent worker able to perform rescue, including
cardiopulmonary resuscitation, stationed in sight** where work is done at or above
the prescribed voltage. This is a staffing requirement, not a training one, and it
is satisfied only by a person who is there.

It must set out the organisation's programme for the control of hazardous energy
as a whole: isolation, lockout, verification of the absence of voltage before
anything is touched, group lockout, shift handover, and the removal of a lock
whose owner has gone home. Verification of absence of voltage is the step that is
skipped, and it is the step that kills.

It must cover the energized work permit: when work may proceed energized at all,
who may authorise it, what the shock and arc flash assessment must establish, and
what boundaries and arc-rated protective equipment follow from it. Energized work
is the exception and the permit exists so that the exception is a decision by a
named person rather than a habit.

Certification and licensing belong here as a boundary rather than as content.
Electrical work in Ontario requires certified trades and, for a contractor,
licensing and notification to the electrical authority; that is a trade-licensing
and code-compliance regime with its own programme, and this document should point
at it rather than restate it.

**The monthly review is this organisation's choice.** The duties are continuous
and no review interval is prescribed.
