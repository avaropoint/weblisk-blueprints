---
id: cohs.excavation-trenching
kind: procedure
title: Excavation and Trenching
structure: procedure
path: procedures/excavation-and-trenching.md

satisfies:
  - construction_safety_ca:CSA-SITE-1
  - cor_2020:COR-08

requires: [cohs.pre-task-hazard-assessment]

declares:
  obligation:
    id: cohs.excavation-inspection
    activity: Inspection of every excavation a worker may enter, its soil classification and its support or sloping
    cadence: each working day
    authority: O. Reg. 213/91 ss. 227, 234. The regulation prescribes no inspection interval except where an engineer's written opinion states one under s. 234(4)
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/excavation-inspections.md
    escalate: {after: 1d, to: health-safety-lead}
  register:
    title: Excavation Inspection Record
    note: >
      One row per excavation per working day it is open and enterable. The soil
      type is recorded on every inspection and not only at the start, because
      soil is reclassified by rain, by vibration, by a spoil pile moved, and by
      the excavation reaching a different stratum. A type recorded once at the
      top of a job is a statement about a hole that no longer exists.
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: location, label: Excavation, type: text, required: true}
      - {key: inspector, label: Inspected by, type: user, required: true}
      - {key: depth, label: Depth in metres, type: number, required: true}
      - {key: is_trench, label: It is a trench, type: bool, required: true}
      - {key: soil_type, label: Soil type, type: select, required: true,
         options: [Type 1, Type 2, Type 3, Type 4, Sound and stable rock]}
      - {key: soil_basis, label: How the classification was made, type: longtext, required: true}
      - {key: protection, label: Protection in place, type: select, required: true,
         options: [Support system, Sloped, Engineer's written opinion,
                   "Under 1.2 m and no worker enters", "No worker enters"]}
      - {key: engineer_opinion_ref, label: Engineer's opinion reference, type: text}
      - {key: services_located, label: Underground services located and marked, type: bool, required: true}
      - {key: access_egress, label: Access and egress, type: longtext, required: true}
      - {key: spoil_and_loads, label: Spoil, equipment and loads set back from the edge, type: bool, required: true}
      - {key: second_worker, label: A worker above ground in close proximity, type: bool, required: true}
      - {key: water, label: Water accumulation, type: longtext}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: how soil is classified,
when a support system is required, who may decide it is not, and what has to be
true before a worker steps into a hole.

It must set out the **four soil types** and the rule that where more than one type
is present, the excavation is classified as **the highest-numbered type present**.
It must state that previously excavated soil is expressly Type 3 — which catches
almost every urban service trench and is the classification most often
optimistically avoided. It must require the walls to be examined **at the walls
and within a horizontal distance equal to the depth**, because a classification
made from the top of the spoil pile is not the classification the regulation
asks for.

It must set out the exceptions to the support requirement exactly, because they
are narrow and each of them is a trap when half-remembered: less than 1.2 m deep;
no worker enters; not a trench and no worker closer to a wall than its height;
sound and stable rock; **Type 1 or 2 sloped at one vertical to one horizontal**;
**Type 3 sloped at one to one**; **Type 4 sloped at one vertical to three
horizontal**; or an engineer's written opinion, which is not available for a
trench and not available for Type 4. Where an engineer's opinion is used, it must
state **the frequency of inspections** and a copy must be kept on the project —
which is the one case in this artifact where the inspection interval IS set by an
authority, and it is set per excavation rather than in general.

It must require that **no worker works in a trench unless another worker is above
ground in close proximity**. That is a person, not a camera, and the register
records it as a fact per inspection because it is the control that is quietly
dropped when the crew is short.

It must cover locating underground services before breaking ground, set-back of
spoil and equipment, access and egress, and water — including what happens when a
trench that was dry yesterday is not.

**The daily inspection interval is this organisation's choice.** The regulation
prescribes none except through an engineer's opinion. A working day is chosen
because the conditions the classification depends on change overnight: rain,
frost, vibration from adjacent work, a spoil pile grown. An organisation that
prefers a different interval may set one, and must record that it is theirs.

It must say who stops the work and how the decision to re-enter is made. An
excavation that showed tension cracks and is entered again the next morning is a
decision somebody made, and it should be written down by the person who made it.
