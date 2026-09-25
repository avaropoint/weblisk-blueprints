---
id: cenv.soil-reuse-planning
kind: procedure
title: Excess Soil Reuse Planning
structure: procedure
path: procedures/excess-soil-reuse-planning.md

satisfies:
  - o_reg_406_19:11
  - o_reg_406_19:12
  - o_reg_406_19:13
  - o_reg_406_19:15
  - o_reg_406_19:26

requires: [cenv.excavation-projects]

declares:
  obligation:
    id: cenv.soil-reuse-planning
    activity: Reuse planning determined for the project area and, where a notice is owed, the qualified person's documents obtained
    for:
      records: registers/excavation-projects.md
      due: 30d before excavation_start_on
      key: area_id
    authority: >
      O. Reg. 406/19 ss. 11, 12, 13 and 26. The regulation requires these
      documents to exist BEFORE the Registry notice is filed, and the notice
      before soil is removed. It sets no lead time for either
    interval_basis: chosen
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/excess-soil-reuse-plans.md
    escalate: {after: 1w, to: project-manager}
  register:
    title: Excess Soil Reuse Plan Record
    note: >
      One row per project area. Four documents are recorded separately because
      three of them are conditional and the conditions differ: an assessment of
      past uses is owed wherever a notice is owed, a sampling and analysis plan
      only where a potentially contaminating activity is identified or the area
      is or was an enhanced investigation project area or a stormwater
      management pond is being dug out, a soil characterization report only
      where a sampling and analysis plan was required, and a destination
      assessment report wherever a notice is owed. "Not required" is an outcome
      and must be recordable as one, with the reason beside it.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 7y
      authority: O. Reg. 406/19 s. 28 (1) — every document and record created or acquired under the Regulation is retained for at least seven years after it is created or acquired
      reason: >
        Seven years from creation, not from the project finishing. A reuse plan
        written two years before a long job completes is disposable five years
        after the job ends, and a schedule that ran from project completion
        would keep it longer than the law asks and be indefensible as a habit
        rather than a requirement.
    columns:
      - {key: area, label: Project area, type: relation, required: true,
         target: /registers/excavation-projects.md#records, display: area_id}
      - {key: assessed_on, label: Planning completed on, type: date, required: true}
      - {key: qualified_person, label: Qualified person, type: text}
      - {key: conflict_declared, label: Qualified person's conflict of interest confirmed clear, type: bool, required: true}
      - {key: past_uses, label: Assessment of past uses, type: select, required: true,
         options: [Obtained,
                   "Not required — a phase one environmental site assessment exists",
                   "Not required — stormwater management pond",
                   "Not required — no Registry notice is owed",
                   Outstanding]}
      - {key: sampling_plan, label: Sampling and analysis plan, type: select, required: true,
         options: [Obtained,
                   "Not required — no potentially contaminating activity identified",
                   "Not required — soil is going to a Class 1 soil management site",
                   "Not required — no Registry notice is owed",
                   Outstanding]}
      - {key: characterization_report, label: Soil characterization report, type: select, required: true,
         options: [Obtained, "Not required — no sampling and analysis plan was required", Outstanding]}
      - {key: destination_report, label: Excess soil destination assessment report, type: select, required: true,
         options: [Obtained, "Not required — no Registry notice is owed", Outstanding]}
      - {key: segregation_procedure, label: Written stockpile segregation procedure in place, type: bool, required: true}
      - {key: destinations, label: Destinations identified, type: longtext, required: true}
      - {key: contingency_site, label: Contingency destination identified, type: text}
      - {key: standards_table, label: Excess Soil Standards table the soil is expected to meet, type: text}
      - {key: documents, label: The documents themselves, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: who decides that a
qualified person is needed, how one is engaged, what the four documents are for,
and what has to be true about the ground before anybody books a truck.

It must set out the four documents and **which conditions bring each of them
into play**, because they are not a package. An **assessment of past uses**
under s. 11 is owed wherever a Registry notice is owed, and is excused only where
a phase one environmental site assessment within the meaning of O. Reg. 153/04
already exists for the project, or where the work is excavation at a stormwater
management pond. A **sampling and analysis plan** under s. 12 is owed only where
the assessment of past uses or the phase one identifies a **potentially
contaminating activity**, or any part of the area is or has been an enhanced
investigation project area, or the project involves excavating a stormwater
management pond — and it is not required at all if the soil is going to a Class 1
soil management site. A **soil characterization report** follows from a sampling
and analysis plan and from nothing else. An **excess soil destination assessment
report** under s. 13 is owed wherever a notice is owed.

It must state that the documents must exist **before the notice is filed**, and
that the notice must be filed before soil is removed. That is the sequence the
regulation sets, and it is the sequence that gets inverted on a job in a hurry:
soil is moved, the notice is filed afterwards to tidy up, and the qualified
person's report is commissioned to describe what has already left.

**Thirty days is this organisation's choice and the law's is nothing at all.**
The regulation sets no lead time for reuse planning. Thirty days is chosen
because a qualified person cannot assess past uses, get a sampling plan into the
field, wait on a laboratory and write a characterization report inside a week,
and because a result that comes back worse than expected changes the destination
and therefore the notice. Where a project area is mobilised in less than thirty
days the duty is unchanged; the margin is simply gone, and the programme should
show that rather than hide it.

It must require the **segregation of stockpiles in writing**. Section 12 (4) (b)
makes written procedures for segregating and stockpiling soil, and keeping
sampled soil apart, a duty of the project leader in its own right — not advice.
A sampling result belongs to a pile, and a pile that has been pushed together
with another one has no result.

It must cover **conflict of interest**. A qualified person may not act on a
project in which they hold a direct or indirect interest, although they may act
where their employer does. On design-build work where the same consultancy is
doing the engineering, that is a question somebody has to actually ask, and the
register records the answer rather than the assumption.

It must say what happens when the ground disagrees with the paperwork. Section 15
requires a **written record created immediately** where later testing shows the
characterization report does not reflect the soil going to a reuse site, where an
area of potential environmental concern not in the assessment of past uses turns
up, or where soil is going to a reuse site the destination report does not name —
and a qualified person's review and amendment of all the documents **within 30
days**. That 30 days is the regulation's, not ours. The immediate record is
raised on the environmental incident register so the clock is visible; this
procedure must say who raises it.
