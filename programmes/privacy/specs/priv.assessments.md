---
id: priv.assessments
kind: register
title: Privacy Impact Assessment Register
structure: standard
path: registers/privacy-impact-assessments.md

satisfies:
  - quebec_law25:GA-3
  - soc2:P1.1

requires: [priv.impact-assessment]

register:
  title: Privacy Impact Assessment Register
  note: >
    One row per assessment. There is no cadence attached to this register and
    that is deliberate: an assessment is triggered by a change — a new
    collection, a new purpose, a new system, a new supplier, a new jurisdiction,
    an automated decision — and a change has no period. What makes the absent
    ones visible is the annual programme review, which counts new or changed
    processing against assessments completed.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: initiative, label: Initiative assessed, type: text, required: true}
    - {key: trigger, label: What triggered it, type: select, required: true,
       options: [New collection, New purpose, New system, New service provider,
                 Transfer outside Canada, Automated decision-making, Change to an existing process, Other]}
    - {key: started_on, label: Started on, type: date, required: true}
    - {key: assessed_by, label: Assessed by, type: user, required: true}
    - {key: information_involved, label: Personal information involved, type: longtext, required: true}
    - {key: risks_identified, label: Risks identified, type: longtext, required: true}
    - {key: mitigations, label: Mitigations agreed, type: longtext, required: true}
    - {key: residual_risk, label: Residual risk, type: select, required: true,
       options: [Low, Medium, High, Not acceptable]}
    - {key: decision, label: Decision, type: select, required: true,
       options: [Proceed, Proceed with conditions, Do not proceed, Deferred]}
    - {key: decided_by, label: Decided by, type: user, required: true}
    - {key: completed_on, label: Completed on, type: date}
---

What this artifact must establish: which changes were assessed before they
happened, and what was decided.

It exists to make the absence visible. An assessment done well and filed in a
project folder cannot be counted; a row here can be compared against the changes
the organisation actually made, and the difference is the finding.

`decision: Proceed with conditions` is the outcome that matters most and the one
most easily lost. A condition agreed at assessment and never implemented is the
common failure mode, and the mitigations column is what a later review reads.

An organisation operating in Quebec is required to conduct these assessments for
projects involving personal information; elsewhere in Canada they are best
practice rather than statute. That difference belongs in the procedure's text
rather than in the register, because the register is the same either way.
