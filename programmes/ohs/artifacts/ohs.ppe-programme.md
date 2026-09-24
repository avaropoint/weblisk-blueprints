---
id: ohs.ppe-programme
kind: procedure
title: Personal Protective Equipment Programme
structure: procedure
path: procedures/personal-protective-equipment.md

satisfies:
  - cor_2020:COR-10
  - isnetworld:ISN-SAFE-08

requires: [ohs.hazard-assessment-procedure]

declares:
  obligation:
    id: ohs.ppe-inspection
    activity: Inspection of issued personal protective equipment
    cadence: each month
    responsible: site-supervisor
    applies_to: each project
    records: registers/ppe-inspections.md
  register:
    title: PPE Inspection Record
    note: >
      One row per inspection. `condition` and `action` are separate columns
      because finding a defect and doing something about it are two facts, and a
      record that collapses them cannot show equipment that was inspected,
      failed, and stayed in service.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: location, label: Site or work area, type: text, required: true}
      - {key: equipment, label: Equipment type, type: text, required: true}
      - {key: quantity, label: Items checked, type: int, required: true}
      - {key: condition, label: Condition, type: select, required: true,
         options: [Serviceable, Wear noted, Removed from service]}
      - {key: action, label: Action taken, type: longtext}
      - {key: inspector, label: Inspected by, type: user, required: true}
---

What this document must establish for THIS organisation: which protective
equipment is required for which work, who pays for it, and how it is kept fit for
use.

It must be explicit that this is the LAST control, not the first. Equipment is
what remains after elimination, substitution and engineering have been applied,
and a programme that opens with the equipment list teaches the opposite of the
hierarchy the hazard assessment procedure requires.

It must tie each requirement to a hazard rather than to a job title. "Hard hats
in the yard" is enforceable; "hard hats for labourers" leaves the visiting
engineer bare-headed under the same crane.

It must cover selection against a standard, fit — including the cases where a
generic size does not fit a specific person, which is a real exclusion and not a
preference — training in use and limitations, inspection, and the point at which
equipment is removed from service. Removal is the part most programmes leave out,
and worn equipment in service is worse than none because it is trusted.

It must say who provides and pays for what. Where the law assigns that, the
document must not read as though it were the organisation's choice.
