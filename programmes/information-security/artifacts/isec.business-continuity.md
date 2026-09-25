---
id: isec.business-continuity
kind: procedure
title: Business Continuity and ICT Readiness
structure: procedure
path: procedures/business-continuity.md

satisfies:
  - iso_27001:A.5.29
  - iso_27001:A.5.30
  - iso_27001:A.8.14
  - iso_22301:8.2.2
  - iso_22301:8.3
  - iso_22301:8.4
  - iso_22301:8.5
  - nist_csf_2:RC.RP-01
  - nist_csf_2:RC.RP-05
  - can_ciosc_104:CIOSC-L1-22
  - soc2:A1.2

requires: [isec.policy, isec.risk-assessment]
approved_by: [senior-management]

declares:
  obligation:
    id: isec.continuity-exercise
    activity: Exercise the business continuity plan and report what it found
    cadence: each year
    authority: ISO 22301:2019 clause 8.5 — exercises at planned intervals and when significant changes occur
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/continuity-exercises.md
    escalate: {after: 4w, to: senior-management}
    satisfies:
      - iso_22301:8.5
      - iso_27001:A.5.29
  register:
    title: Continuity Exercise Record
    note: >
      One row per exercise. `objectives_met` is recorded against the recovery
      times the business impact analysis set, not against whether the exercise
      went smoothly — an exercise everybody enjoyed that restored a system in
      three times its recovery objective was a successful exercise and a failed
      capability, and those must not be recorded as the same thing.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: exercised_on, label: Exercised on, type: date, required: true}
      - {key: scenario, label: Scenario, type: longtext, required: true}
      - {key: type, label: Type, type: select, required: true,
         options: [Walkthrough, Tabletop, Simulation, Technical failover, Live invocation]}
      - {key: participants, label: Participants, type: longtext, required: true}
      - {key: activities_tested, label: Prioritised activities tested, type: longtext, required: true}
      - {key: objectives_met, label: Recovery objectives met, type: select, required: true,
         options: [All met, Partially met, Not met, Not measured]}
      - {key: actual_recovery, label: Actual recovery time achieved, type: text, required: true}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: plan_updated, label: Plan updated as a result, type: bool, required: true}
      - {key: actions, label: Actions arising, type: longtext, required: true}
---

What this document must establish for THIS organisation: what must keep running,
how quickly it must be back, and what people do while it is not.

It must start with the business impact analysis rather than with the technology.
Which activities the organisation cannot be without, how long it can be without
each, and how much data it can afford to lose are business judgements; recovery
objectives chosen by the people who will have to meet them are preferences
dressed as requirements.

It must name who may invoke the plan and who may stand it down, by position and
with a deputy. Authority that rests with one person unreachable at 3 a.m. is
authority nobody has, and this is the single most common reason a plan is not
used during the disruption it was written for.

It must say how people will communicate when the usual means are the thing that
is down. A contact list held only in the email system, or a plan stored only on
the file share, is a plan that exists exactly when it is not needed.

It must cover the ICT half specifically — what is backed up, how it is restored,
and by whom — and point at the IT programme's backup and recovery procedure
rather than restating it. A.5.30 is about readiness, and readiness means
somebody has done the restore, not that the backup job reports success.

It must include the suppliers whose failure stops the business. The criticality
column in the supplier register exists for this, and a continuity plan that
assumes every supplier is available has planned for the wrong outage.

The exercise is annual by the organisation's own choice, not by any rule cited
here: ISO 22301 requires exercises at planned intervals and leaves the interval
to the organisation, which is why the basis is declared as chosen.
