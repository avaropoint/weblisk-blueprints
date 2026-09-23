---
id: ohs.objectives
kind: standard
title: Health and Safety Objectives and Improvement
structure: standard
path: standards/health-and-safety-objectives.md

satisfies:
  - iso_45001:6.2
  - iso_45001:10.3

requires: [ohs.policy]

declares:
  obligation:
    id: ohs.objective-review
    activity: Review of progress against health and safety objectives
    cadence: each quarter
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/objective-reviews.md
  register:
    title: Objective Review Record
    note: >
      One row per objective per review. `leading` marks whether the measure
      predicts harm or counts it after the fact — an objective set entirely on
      lagging measures can be met by a quiet quarter, and the programme cannot
      tell luck from improvement without both.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: objective, label: Objective, type: text, required: true}
      - {key: measure, label: Measure, type: text, required: true}
      - {key: leading, label: Leading measure, type: bool, required: true}
      - {key: target, label: Target, type: text, required: true}
      - {key: actual, label: Actual, type: text, required: true}
      - {key: on_track, label: On track, type: select, required: true,
         options: [On track, Behind, Achieved, Abandoned]}
      - {key: why, label: What the number is telling us, type: longtext, required: true}
      - {key: reviewer, label: Reviewed by, type: user, required: true}
---

What this document must establish for THIS organisation: what the programme is
trying to achieve this year, how progress is measured, and who is accountable for
each objective.

An objective must be something an organisation can DO, not a state it hopes for.
"Reduce injuries" is an aspiration; "every critical task has a safe job procedure
reviewed within twelve months" is an objective, because somebody can be
accountable for it and its progress is countable at any moment.

It must set measures that predict as well as count. Injury rates say what already
happened, and a programme steering by them is steering by the wake — but a
programme with no lagging measures cannot tell whether any of its leading ones
matter. Both, deliberately, is what the register above records.

Each objective must name a position accountable, a target and a date. An
objective belonging to "the organisation" belongs to nobody.

It must say what happens when an objective is not met — revised, resourced, or
abandoned with the reason recorded. Objectives quietly rolled forward year after
year are the clearest signal a programme has stopped being managed, and
abandoning one honestly is a better record than carrying it a third time.

Continual improvement is not a separate exercise from this document. The findings
from inspections, incidents, audits and management review are the input to next
year's objectives, and this is where that loop closes.
