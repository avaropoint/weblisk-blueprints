---
id: cenv.excavation-projects
kind: register
title: Register of Excavation Project Areas
structure: standard
path: registers/excavation-projects.md

# A register carries no `satisfies:`. It is the evidence that work happened,
# not the document that answers a control — and a register citing a control
# could never be recorded as answering it, so it would sit at
# `present_uncited` permanently and cap the tier's readiness at a number no
# amount of work could move. The citations belong on the procedures that
# declare obligations over these rows.

requires: [cenv.policy, cohs.project-register]

register:
  title: Register of Excavation Project Areas
  note: >
    One row per project area from which soil is, or may be, excavated and
    removed. This is the spine of the programme, and it is deliberately not the
    same list as the construction project register: a "project area" under
    O. Reg. 406/19 is a single property or adjoining properties on which the
    project is carried out, so one construction contract can be several project
    areas and a linear job can be one project area spanning several sites. The
    relation onto the project register keeps them joined without pretending they
    are the same thing. Every column below except the two dates exists to answer
    one question — is a Registry notice owed here — and the answer is recorded
    rather than remembered, because the three criteria in subsection 8 (1.1) and
    the seven exemptions in Schedule 2 are not a rule anybody carries in their
    head correctly.
  columns:
    - {key: area_id, label: Project area reference, type: text, required: true}
    - {key: project, label: Construction project, type: relation, required: true,
       target: /registers/projects.md#records, display: project_id}
    - {key: address, label: Location of the project area, type: text, required: true}
    - {key: our_role, label: Our role for this project area, type: select, required: true,
       options: [Project leader,
                 Operator of the project area,
                 Project leader and operator,
                 "Neither — another party decides and operates",
                 Not yet determined]}
    - {key: project_leader_name, label: Who the project leader is, type: text, required: true}
    - {key: excavation_start_on, label: Excavation expected to start, type: date, required: true}
    - {key: soil_removal_complete_on, label: Last load of excess soil removed on, type: date}
    - {key: estimated_volume_m3, label: Excess soil expected to be removed, in cubic metres, type: number, required: true}
    - {key: settlement_area, label: Any part is in an area of settlement, type: bool, required: true}
    - {key: property_use, label: Use of the whole project area, type: select, required: true,
       options: [Agricultural or other, Commercial, Community, Industrial,
                 Institutional, Parkland, Residential, "Mixed — not all one use"]}
    - {key: enhanced_investigation, label: Is or has been an enhanced investigation project area, type: select, required: true,
       options: ["Yes", "No", Not yet determined]}
    - {key: past_uses_basis, label: What the opinion on past uses was based on, type: longtext, required: true}
    - {key: remediation_excavation, label: Excavated to reduce contaminant concentrations, type: bool, required: true}
    - {key: infrastructure_project, label: Infrastructure project within the meaning of the regulation, type: bool, required: true}
    - {key: registry_notice_required, label: Registry notice required, type: select, required: true,
       options: ["Yes",
                 "No — no criterion in s. 8 (1.1) is met",
                 "No — Schedule 2 applies",
                 "No — we are not the project leader",
                 Not yet determined]}
    - {key: exemption_ground, label: Which criterion or exemption was relied on, and why, type: longtext}
    - {key: qualified_person, label: Qualified person engaged, type: text}
    - {key: qualified_person_firm, label: Qualified person's firm, type: text}
    - {key: note, label: Note, type: longtext}
---

What this artifact must establish for THIS organisation: every place it is
digging, whether it is the party the regulation makes answerable there, and
whether soil leaving that place needs a Registry notice before it moves.

It exists because **the duty is triggered by a project area and a determination,
never by a date in a calendar**, and because the determination is the thing that
actually goes wrong. A programme that files a notice for every load is wrong and
will be ignored inside a month; a programme that files none is unlawful on the
jobs that needed one. The only way to be neither is to record the reasoning, per
project area, before the first truck.

**`our_role` is the first column that matters and the one most often assumed.**
The reuse planning and Registry duties in sections 8 to 16 run against the
**project leader** — the person or persons ultimately responsible for making
decisions relating to the planning and implementation of the project. That is
frequently the owner and frequently this organisation, and on a design-build or a
self-performed development it is almost always this organisation. Two duties do
not care: the written procedure for an observation suggesting contamination
(s. 23) is owed by the project leader **or** the operator of the project area,
and the hauling record (s. 18) is owed by the owner or operator of the site
where the load is put on the truck. So "Neither" is a real and common row, and
it does not mean there is nothing to do here.

**The three criteria in subsection 8 (1.1) are why five of these columns exist.**
A notice is owed where the project area is or has ever been, in whole or in part,
an **enhanced investigation project area** — used for an industrial use, as a
garage, as a bulk liquid dispensing facility including a gasoline outlet, or for
dry cleaning equipment — or where any part is in an **area of settlement** within
the meaning of the *Planning Act* and **2,000 m³ or more** will be removed, or
where the excavation is a **remediation**. The settlement-area criterion has an
exclusion that is routinely read backwards: it does **not** apply where the
*whole* project area is in residential, institutional, parkland, or agricultural
and other use. The consequence is that a commercial, community or industrial
project area in a settlement area is caught at 2,000 m³ and a residential one is
not, and a project area of mixed use is caught because the whole of it is not one
of the four. `property_use` is a select over the O. Reg. 153/04 categories for
that reason, with a "Mixed" option because the exclusion turns on the whole.

**`past_uses_basis` is required, and it is the column an inspector reads.** The
criterion is that the project leader "is of the opinion", after making reasonable
efforts to take into consideration any past reports and other available
information. An opinion with nothing behind it is not the opinion the regulation
asks for, and the effort is only evidenced if somebody wrote down what they
looked at.

**`registry_notice_required` has four negative options rather than one.** "No"
is three different findings with three different consequences: no criterion was
met at all, a criterion was met and Schedule 2 exempted it, or this organisation
is not the party who owes it. Collapsing them into a single "No" loses the only
information that could ever show the determination was made properly, and hides
the case that changes — volume creeping past 2,000 m³, or a role changing on a
change order.

**`soil_removal_complete_on` is not decoration.** The Registry notice must be
updated within 30 days after all soil that will become excess soil has been
removed, and that clock starts from the last load rather than from the job
finishing. A register with no closing date cannot start it, and the close-out is
the most commonly missed obligation in the regulation because it falls due after
everybody's attention has moved to the next job.
