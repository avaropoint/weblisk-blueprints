---
id: cohs.fire-protection
kind: procedure
title: Fire Protection on a Project
structure: procedure
path: procedures/project-fire-protection.md

satisfies:
  - o_reg_213_91:52
  - o_reg_213_91:53
  - o_reg_213_91:54
  - o_reg_213_91:55
  - o_reg_213_91:57
  - cor_2020:COR-14
  - iso_45001:8.1.2
  - isnetworld:ISN-SAFE-11

requires: [cohs.constructor-duties, cohs.project-register]

approved_by: [senior-management]

declares:
  obligation:
    id: cohs.fire-equipment-inspection
    activity: Inspection of every fire extinguisher on the project by a competent worker, with the date recorded on the extinguisher's own tag
    cadence: each month
    authority: O. Reg. 213/91 s. 55 — every fire extinguisher shall be inspected for defects or deterioration at least once a month by a competent worker, who shall record the date on a tag attached to it
    interval_basis: required
    responsible: site-supervisor
    applies_to: the organisation
    per:
      listed_in: registers/projects.md
      key: project_id
      label: name
      from: start_on
      until: finished_on
    records: registers/project-fire-protection-inspections.md
    escalate: {after: 1w, to: health-safety-lead}
  register:
    title: Project Fire Protection Inspection Record
    note: >
      One row per project per month. It records the monthly extinguisher
      inspection that the regulation requires, and — in the same pass, because
      nobody walks a site twice — the state of the other fire provisions that
      change as a building goes up: the standpipe's distance behind the work
      level, the access route a fire appliance would actually use today, and
      whether combustible waste has accumulated. The tag is the statutory
      record and stays on the extinguisher; this row is the organisation's
      evidence that the inspection happened and what it found.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: inspected_by, label: Inspected by, type: user, required: true}
      - {key: extinguishers_on_site, label: Extinguishers on the project, type: int, required: true}
      - {key: extinguishers_inspected, label: Inspected and tagged this month, type: int, required: true}
      - {key: extinguishers_defective, label: Defective, discharged or missing, type: int, required: true}
      - {key: replaced_or_recharged_on, label: Defective units replaced or recharged on, type: date}
      - {key: rating_conforms, label: Every unit is a pressure-discharge type rated at least 4A40BC, type: bool, required: true}
      - {key: locations_marked, label: Locations readily accessible and adequately marked, type: bool, required: true}
      - {key: protected_from_damage_and_freezing, label: Protected from physical damage and from freezing, type: bool, required: true}
      - {key: workers_trained, label: Every worker who may be required to use one has been trained, type: bool, required: true}
      - {key: standpipe_required, label: A standpipe is required on this project, type: select, required: true,
         options: ["Yes", "No — the building needs no permanent standpipe", Not yet applicable]}
      - {key: storeys_behind_work_level, label: Storeys between the standpipe and the uppermost work level, type: int}
      - {key: hose_outlets_and_connections, label: Hose outlets and the fire department connection serviceable and identified, type: bool}
      - {key: access_route_usable, label: A fire appliance could reach the building today by the planned route, type: bool, required: true}
      - {key: access_obstructions, label: What is obstructing it, type: longtext}
      - {key: combustible_waste, label: Combustible waste accumulation, type: select, required: true,
         options: [None, Some — removed during the inspection, Significant — action raised]}
      - {key: flammable_storage_conforms, label: Flammable and combustible liquids stored as the procedure requires, type: bool, required: true}
      - {key: temporary_heating, label: Temporary heating in use, and how it is controlled, type: longtext}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: what burns on a
construction project, what puts it out, who checks that the equipment is there
and works, and how the fire route keeps up with a building that is changing
shape every week.

It must state the **provision duty** plainly: fire extinguishing equipment at
readily accessible and adequately marked locations, and at least one extinguisher
wherever flammable liquids or combustible materials are stored, handled or used,
and where oil- or gas-fired equipment is in use. Extinguishers must be a
pressure-discharge type with a rating of at least **4A40BC** — a number worth
printing, because the small units bought for a truck cab do not meet it and are
the ones most often found hanging on a hoarding.

It must require **training for every worker who may be required to use one**.
That is a duty in the regulation and it is the one almost universally treated as
covered by orientation. Standing in front of an extinguisher and being told where
they are is not training in its use.

It must say what happens **after an extinguisher is used**: refilled or replaced
**immediately**, not at the next service visit. A discharged extinguisher hanging
in its bracket is worse than no extinguisher, because somebody will reach for it.

**The monthly inspection interval is the law's and this artifact says so.** The
regulation sets the interval, sets who may do it — a competent worker — and sets
the record: the date written on a tag attached to the extinguisher. The tag is
the statutory record. The row this obligation produces is the organisation's own
evidence that the walk happened, what was found and what was done, which the tag
cannot hold.

It must cover **the standpipe as the building grows**. In a building of two or
more storeys, a permanent or temporary standpipe must be kept within two storeys
of the uppermost work level as construction proceeds, unless the Building Code
requires no permanent standpipe in that building. This is the provision most
likely to fall behind, because it is the only one whose compliance changes when
nobody has done anything: the crew pours another floor and the site is
non-compliant by Friday. The column is a **number of storeys behind**, not a
tick, so the trend is visible before the breach.

It must cover the things that are not equipment at all: the **access route a fire
appliance would use today** given the current hoarding, spoil pile, crane pad and
site trailer; where combustible waste is accumulating; how flammable and
combustible liquids are stored and how much of them is on site; and how
**temporary heating** is fuelled, controlled and shut down. Temporary heat and
combustible waste together are the two ingredients in most construction fires,
and neither is in the regulation's extinguisher sections.

**It must state that the Ontario Fire Code is a separate statute with separate
duties, and that this document does not discharge them.** A construction or
demolition site is subject to the Fire Code as well as to the construction
regulation, the local chief fire official administers it, and many
municipalities add a by-law of their own — commonly requiring a written
construction fire safety plan, a named site fire safety coordinator, and
notification before certain work. The specific article numbers and the
municipality's requirements must be read from the current consolidation and from
the municipality the project is in, and recorded in the legal requirements
register. They are **not reproduced here**, because a number copied into a pack
is the number somebody will rely on after it has changed.

It must name **who the fire safety coordinator is on each project** and how that
is handed over when the site supervisor changes, and must say how sub-trades'
hot work, their own extinguishers and their own flammable storage are brought
under one project-wide arrangement rather than nine.
