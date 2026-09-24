---
id: cohs.hoisting-rigging
kind: procedure
title: Cranes, Hoisting and Rigging
structure: procedure
path: procedures/hoisting-and-rigging.md

satisfies:
  - o_reg_213_91:150
  - o_reg_213_91:152
  - o_reg_213_91:170
  - cor_2020:COR-08
  - cor_2020:COR-12

requires: [cohs.pre-task-hazard-assessment, cohs.credential-register]

declares:
  obligation:
    id: cohs.crane-cable-inspection
    activity: Visual inspection of crane cables and rigging chains by a competent worker, recorded in the operator's crane log
    cadence: each week
    authority: O. Reg. 213/91 s. 170 — cables visually inspected by a competent worker at least weekly when in use and recorded in the operator's log; s. 176 — chains at least weekly
    interval_basis: required
    responsible: site-supervisor
    applies_to: each project
    records: registers/crane-log-inspections.md
    escalate: {after: 3d, to: health-safety-lead}
  register:
    title: Crane Log Inspection Record
    note: >
      One row per machine per week. This register is the organisation's copy; the
      regulation requires the entry to be made in the OPERATOR'S crane log, which
      stays with the machine. Both exist on purpose — the log is what an
      inspector asks the operator for, and this register is what tells a head
      office that a machine on a site four hours away has not been logged in
      three weeks.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: machine, label: Machine, type: text, required: true}
      - {key: inspector, label: Inspected by, type: user, required: true}
      - {key: cables, label: Cables, type: select, required: true,
         options: [Serviceable, Wear noted, Removed from service]}
      - {key: chains_and_rigging, label: Chains and rigging, type: select, required: true,
         options: [Serviceable, Wear noted, Removed from service, Not applicable]}
      - {key: findings, label: Findings, type: longtext}
      - {key: logged_in_operator_log, label: Entered in the operator's crane log, type: bool, required: true}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: who may operate a
hoisting device, what has to be inspected and how often, how a lift is planned,
and who is entitled to stop one.

It must state the **certificate of qualification** requirements by class, because
they are tied to the weight of the machine rather than to the job title: a mobile
crane over the higher threshold requires the senior mobile crane operator
certificate; between the two thresholds either that or the second class; tower
cranes have their own. It must also state that a worker **shall carry written
proof of training while operating** — a certificate in a filing cabinet does not
satisfy a requirement to carry it.

**The weekly cable and chain inspections are the law's interval**, and the
recording place is the law's too: the entry goes in the **operator's crane log**,
which travels with the machine. An organisation that keeps only a central
spreadsheet has the record in the wrong place, and an organisation that keeps only
the log cannot see across its fleet. Both, and the register says which.

It must state that the rated capacity is established in accordance with the
standard the regulation names, at the edition the regulation names, and that a
load chart is meaningless without the configuration it belongs to — boom length,
radius, counterweight, outrigger extension, quadrant of operation.

It must require a **lift plan** for anything outside routine, and must define
outside routine rather than leaving it to judgement: multiple cranes, blind
lifts, lifts over occupied areas or public ways, personnel platforms, lifts near
energized conductors, and anything above a stated proportion of chart capacity.

It must cover **signalling**, and must state it accurately: signallers must be
given oral training plus written and oral instructions, the written instructions
must be **kept at the project**, and there is **no prescribed interval and no
certificate**. Likewise, and this surprises people: **no rigger training mandate
exists in the construction regulation at all**. Competence is the requirement,
demonstrated and recorded by the employer, and any card an organisation requires
is its own standard or a client's. The document should say which, because a
programme that presents a vendor card as a legal requirement will eventually be
asked to name the section.

It must say what happens when wind, visibility or ground conditions exceed the
limits: who stops, who may restart, and where the decision is recorded. The
operator's authority to refuse a lift is not a courtesy and the document should
state it as a duty.
