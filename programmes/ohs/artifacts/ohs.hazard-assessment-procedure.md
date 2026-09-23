---
id: ohs.hazard-assessment-procedure
kind: procedure
title: Hazard Assessment and Control
structure: procedure
path: procedures/hazard-assessment.md

satisfies:
  - iso_45001:6.1.2
  - iso_45001:6.1.4
  - cor_2020:COR-06

requires: [ohs.policy]

declares:
  obligation:
    id: ohs.hazard-assessment
    activity: Hazard assessment
    cadence: each working day
    responsible: site-supervisor
    # A daily assessment missed for two days is not a paperwork gap: work has
    # been proceeding without one, which is the condition the procedure exists to
    # prevent.
    escalate: {after: 2d, to: health-safety-lead}
    applies_to: each project
    records: registers/hazard-assessments.md
  register:
    title: Hazard Assessment Record
    note: >
      One row per assessment. The controls chosen are required, not optional:
      the procedure requires elimination before substitution and engineering
      before PPE, and a record that names only the hazard cannot show which
      way round the choice was made.
    columns:
      - {key: assessed_on, label: Assessed on, type: date, required: true}
      - {key: location, label: Location or work area, type: text, required: true}
      - {key: task, label: Task assessed, type: text, required: true}
      - {key: assessor, label: Assessed by, type: user, required: true}
      - {key: hazards, label: Hazards identified, type: longtext, required: true}
      - {key: controls, label: Controls applied, type: longtext, required: true}
      - {key: residual, label: Residual risk, type: select,
         options: [Low, Medium, High]}
      - {key: work_stopped, label: Work stopped, type: bool, required: true}
      - {key: escalated_to, label: Escalated to, type: user}
---

What this document must establish for THIS organisation: the method by which
hazards are identified before work begins, who may authorise work to proceed,
and how residual risk is recorded and escalated.

It must distinguish the assessment done once for a kind of work from the one
done at the start of each task in the conditions of that day, because they
answer different questions and an organisation that has only the first is
assessing a workplace it is not standing in. It must set out how controls are
chosen — elimination before substitution, engineering before administration,
personal protective equipment last — and require that choice to be recorded, so
a control chosen for convenience is visible as such.

It must say what happens when the assessment finds a risk that cannot be
controlled to an acceptable level: who stops the work, who is told, and how the
decision is recorded. A procedure that has no stop-work path is a procedure that
has already decided the answer.
