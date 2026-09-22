---
id: cohs.fall-protection
kind: procedure
title: Fall Protection Programme
structure: procedure
path: procedures/fall-protection.md

satisfies:
  - construction_safety_ca:CSA-FP-1
  - cor_2020:COR-10
  - iso_45001:8.1.2

requires: [cohs.pre-task-hazard-assessment, cohs.fall-protection-equipment]

approved_by: [senior-management, health-safety-lead]

declares:
  obligation:
    id: cohs.fall-protection-inspection
    activity: Inspection of an item of fall protection equipment before its next inspection falls due
    for:
      records: registers/fall-protection-equipment.md
      due: 7d before next_inspection_due
      key: asset_id
    authority: O. Reg. 213/91 s. 26.1 and the manufacturer's instructions. Ontario prescribes no periodic inspection interval for fall protection equipment
    interval_basis: chosen
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/fall-protection-inspections.md
    escalate: {after: 3d, to: site-supervisor}
    satisfies:
      - construction_safety_ca:CSA-FP-2
  register:
    title: Fall Protection Inspection Record
    note: >
      One row per inspection of one item, keyed by the asset number so the two
      registers join. `outcome` has no option that means "looked at and left
      alone with reservations": an item is serviceable, quarantined, or destroyed.
      Fall protection equipment in a fourth state is equipment somebody will clip
      on to.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: asset_id, label: Item, type: relation, required: true,
         target: /registers/fall-protection-equipment.md#records, display: asset_id}
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: inspector, label: Inspected by, type: user, required: true}
      - {key: competence, label: Basis of the inspector's competence, type: text, required: true}
      - {key: against, label: Inspected against, type: text, required: true}
      - {key: webbing_and_stitching, label: Webbing, stitching and hardware, type: longtext, required: true}
      - {key: arrest_indicator, label: Arrest or impact indicator deployed, type: bool, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Serviceable, Quarantined, Destroyed]}
      - {key: next_due, label: Next inspection due, type: date, required: true}
      - {key: notes, label: Notes, type: longtext}
---

What this document must establish for THIS organisation: when fall protection is
required, which method is used, who may authorise a lower-ranked method, and how
a worker hanging in a harness is got down.

It must state the triggers as the regulation states them, because there is more
than one and the familiar number is only the first. Fall protection is required
where a worker may fall **more than 3 m**; **more than 1.2 m** where the working
surface is used as a path for a wheelbarrow or similar equipment; into operating
machinery; into water or another liquid; into or onto a hazardous substance or
object; or through an opening in a work surface. Separately, a **guardrail is
required at a perimeter or open side where a worker may fall 2.4 m or more**.
"Three metres" as the single answer is wrong in five of those six cases.

It must put the methods in the order the regulation puts them. A **guardrail
first**. Only where a guardrail is impracticable may another method be used, and
then it must be the **highest-ranked practicable** one: travel restraint, then a
fall restricting system, then a fall arrest system, then a safety net. "We use
harnesses" is not a fall protection programme; it is the fourth answer given
first, and the document should require the reason a guardrail was impracticable
to be written down at the time rather than reconstructed afterwards.

**It must contain the rescue plan, and the rescue plan is a written employer
duty.** Before any use of a fall arrest system or a safety net, the worker's
employer must develop **written procedures for rescuing the worker after a fall
has been arrested**. This is the single most frequently missing document in
Ontario construction fall protection, it is frequently mis-cited to the wrong
subsection, and it is the one that matters in the twenty minutes that decide
whether suspension trauma kills somebody. The plan must be specific enough to
execute: who, with what, from where, and how long it will take — and "call 911"
is a plan only where somebody has established that 911 can reach that worker at
that height in that time.

It must be explicit that **s. 26.2 training and Working at Heights training are
cumulative and neither substitutes for the other**. Both regulations say so
expressly. A Working at Heights card does not satisfy the employer's duty to train
a worker on the specific fall protection system that worker will use, and a
s. 26.2 record does not satisfy the Working at Heights requirement. The s. 26.2
training must be recorded in writing, signed, with the worker's name and the
dates.

It must say that s. 26.2 training has **no expiry and no refresher interval in
law**. The "fall protection every three years" figure in wide circulation is the
Working at Heights clock misattributed. If this organisation refreshes system
training on a cycle, that cycle is its own policy and the document must say so in
those words rather than presenting it as a requirement.

**The inspection obligation's seven days is this organisation's choice**, and so,
in most cases, is the due date it counts back from: Ontario prescribes no periodic
inspection frequency for fall protection equipment. The dates come from the
manufacturer's instructions, item by item, which is why they live in the register
and not in this document. Seven days of margin is chosen so that an item can be
recalled from a site before it falls due rather than after.

None of that displaces the **pre-use check by the worker**, every time, which is
not an occurrence and is not recorded here. The document must make the two
distinct: the periodic inspection is the organisation's, the pre-use check is the
worker's, and neither one covers for the other.
