---
id: isec.risk-assessment
kind: procedure
title: Information Security Risk Assessment
structure: procedure
path: procedures/information-security-risk-assessment.md

satisfies:
  - nist_csf_2:ID.RA-01
  - nist_csf_2:ID.RA-04
  - nist_csf_2:ID.RA-05
  - nist_csf_2:GV.RM-01
  - iso_27001:A.5.7
  - soc2:CC3.2
  - can_ciosc_104:CIOSC-L2-08

requires: [isec.policy, isec.asset-inventory]

declares:
  obligation:
    id: isec.risk-assessment
    activity: Information security risk assessment
    cadence: each year
    authority: ISO/IEC 27001:2022 clause 6.1.2 — risk assessments at planned intervals and when significant changes occur
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/risk-assessments.md
    satisfies:
      - nist_csf_2:ID.RA-01
      - soc2:CC3.2
  register:
    title: Risk Assessment Record
    note: >
      One row per assessment of the whole estate, not per risk — the individual
      risks live in the risk register. What this record answers is when the
      organisation last looked, what it looked at, and what changed as a result.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: assessed_on, label: Assessed on, type: date, required: true}
      - {key: assessed_by, label: Assessed by, type: user, required: true}
      - {key: scope, label: Scope of the assessment, type: longtext, required: true}
      - {key: method, label: Method and criteria used, type: longtext, required: true}
      - {key: risks_identified, label: Risks identified, type: int, required: true}
      - {key: risks_new, label: Of those, new since the last assessment, type: int, required: true}
      - {key: risks_above_appetite, label: Risks above appetite, type: int, required: true}
      - {key: changes_since_last, label: What changed since the last assessment, type: longtext, required: true}
---

What this document must establish for THIS organisation: how a risk is
identified, how it is measured, and what "too much" means here.

It must state the criteria before it states any risk. Likelihood and impact
scales, and the threshold above which a risk may not simply be lived with, are
the organisation's own judgement; without them written down, two assessors
produce two different registers from the same estate and neither is wrong.

It must name what the assessment covers — the information assets, the systems
that hold them, the suppliers that reach them, and the people who can act on
them. An assessment scoped to the servers finds server risks.

It must say what triggers an assessment out of cycle: a new system, a new
supplier holding regulated data, a merger, a significant incident, a change in
what the law requires. The annual cadence above is the floor and the
organisation's own choice, which is why it is declared as chosen rather than
required — no standard here sets the interval, they set the duty.

It must say who may accept a risk rather than treat it, and record that
acceptance as a decision with a name and a date on it. An unaccepted risk that
nobody treats is not accepted; it is ignored, and the difference matters after
an incident.
