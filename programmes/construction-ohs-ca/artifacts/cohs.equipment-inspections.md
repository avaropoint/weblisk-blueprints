---
id: cohs.equipment-inspections
kind: procedure
title: Machinery and Equipment Inspection
structure: procedure
path: procedures/equipment-inspection.md

satisfies:
  - construction_safety_ca:CSA-SITE-2
  - cor_2020:COR-12
  - isnetworld:ISN-SAFE-09

requires: [cohs.constructor-duties]

declares:
  obligation:
    id: cohs.equipment-inspection
    activity: Inspection of the machinery and equipment at the project by a supervisor or competent person
    cadence: each week
    authority: O. Reg. 213/91 s. 14(3)–(4) — all machinery and equipment inspected at least once a week
    interval_basis: required
    responsible: site-supervisor
    applies_to: each project
    records: registers/equipment-inspections.md
    escalate: {after: 3d, to: health-safety-lead}
  register:
    title: Equipment Inspection Record
    note: >
      One row per weekly inspection of a project's plant. `removed_from_service`
      is a separate column from `defects` because a defect found and a machine
      stopped are two different facts, and the pair of them is what shows whether
      a finding changed anything.
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: inspector, label: Inspected by, type: user, required: true}
      - {key: competent, label: Inspector is a competent person for this equipment, type: bool, required: true}
      - {key: items_inspected, label: Items inspected, type: longtext, required: true}
      - {key: defects, label: Defects found, type: longtext}
      - {key: removed_from_service, label: Removed from service, type: longtext}
      - {key: returned_to_service_on, label: Returned to service on, type: date}
      - {key: operator_manuals_present, label: Operating manuals available at the machine, type: bool}
---

What this document must establish for THIS organisation: which plant is inspected,
by whom, against what, and what happens to a machine that fails.

The **weekly interval is the law's**. A supervisor or a competent worker
designated by the supervisor inspects all machinery and equipment at the project
at least once a week, and the wording is "all" — the inspection is of the
project's plant, not of a sample of it. This is one of the shortest recurring
legal clocks in Ontario construction and one of the least often recorded, because
it reads like housekeeping.

It must define **competent person** the way the Act does and hold to it: a person
qualified by knowledge, training and experience to organise the work and its
performance, familiar with the Act and the regulations applying to the work, and
with knowledge of any potential or actual danger. A person can be competent for a
skid steer and not for a tower crane, and a single name signing for both is a
record that will not survive being questioned.

It must not silently absorb the inspections that have their own regime and their
own clock. Hoisting cables and chains, fall protection equipment, elevating work
platforms and suspended access equipment each have their own artifact and their
own intervals, most of them also weekly and some of them recorded in a log that
must travel with the machine. A general weekly plant inspection does not
discharge any of them.

It must require removal from service to be a physical act, not a note. A defect
recorded on a form beside a machine that is still running is a document proving
the organisation knew.

It must say who may return equipment to service and on what evidence — because
the return is the decision nobody writes down, and it is the one that matters
after a failure.
