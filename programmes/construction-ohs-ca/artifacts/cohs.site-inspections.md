---
id: cohs.site-inspections
kind: procedure
title: Workplace Inspections
structure: procedure
path: procedures/site-inspection.md

satisfies:
  - ohsa_ontario:8(6)
  - ohsa_ontario:9(26)
  - o_reg_213_91:14
  - cor_2020:COR-11
  - isnetworld:ISN-SAFE-10

requires: [cohs.jhsc]

declares:
  obligation:
    id: cohs.workplace-inspection
    activity: Inspection of the physical condition of the project by the committee member or representative
    cadence: each month
    authority: OHSA ss. 9(26)–(28), 8(6)–(8) — at least once a month, or where that is not practicable, at least annually with a part inspected each month
    interval_basis: required
    responsible: health-safety-lead
    applies_to: each project
    records: registers/site-inspections.md
    escalate: {after: 1w, to: constructor-representative}
  register:
    title: Workplace Inspection Record
    note: >
      One row per inspection. `by_whom` distinguishes the statutory inspection —
      a designated worker member of the committee, or the representative — from a
      supervisor's own walk, because only the first discharges the duty and both
      look identical in a photograph of a clipboard.
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: by_whom, label: Carried out by, type: select, required: true,
         options: [Designated worker member of the committee, Health and safety representative,
                   Supervisor, Other]}
      - {key: inspector, label: Name, type: user, required: true}
      - {key: area, label: Area inspected, type: text, required: true}
      - {key: whole_project, label: Whole project inspected, type: bool, required: true}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: hazards_reported, label: Hazards reported to the employer, type: longtext}
      - {key: stop_work, label: Work stopped, type: bool, required: true}
      - {key: actions_raised, label: Actions raised, type: longtext}
---

What this document must establish for THIS organisation: who inspects a project,
how often, what they look at, and what happens to what they find.

It must be clear that the statutory inspection belongs to the **worker side**. A
designated worker member of the committee, or the health and safety
representative, inspects the physical condition of the workplace at least once a
month. A supervisor's daily walk is valuable and is not this. An organisation
whose only inspection records are signed by supervisors has no evidence of the
duty being met, however diligent the walks were.

Where inspecting the whole project monthly is not practicable, the law allows the
whole to be inspected **at least annually, a part of it each month** — which is a
real accommodation for a long linear project and a temptation everywhere else.
The document should say which of the two the organisation operates and, if the
second, how the parts add up to the whole inside a year. `whole_project` is a
column so that question has an answer rather than an impression.

**The monthly interval is the law's**, and so is the annual fallback. Nothing
here is a chosen number.

It must say what the inspector is entitled to: to be paid for the time, to have
the employer provide the information and assistance required, and to have the
findings answered. An inspection whose findings go into a folder is a hazard
register the organisation has chosen not to read.

It must connect findings to corrective action with an owner and a date, and must
not allow a finding to be closed by being repeated next month. The clearest
signal a programme has stopped working is the same item appearing on four
consecutive inspections, each time as a new finding.

It must state the stop-work path explicitly and by position. An inspection that
can only recommend is an inspection that will eventually document a hazard
nobody stopped.
