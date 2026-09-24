---
id: cohs.traffic-protection
kind: procedure
title: Traffic Protection
structure: procedure
path: procedures/traffic-protection.md

satisfies:
  - o_reg_213_91:67(2)
  - o_reg_213_91:67(4)
  - o_reg_213_91:67(6)
  - cor_2020:COR-07
  - isnetworld:ISN-SAFE-05

requires: [cohs.pre-task-hazard-assessment]

declares:
  obligation:
    id: cohs.traffic-protection-review
    activity: Review of the written traffic protection plan against the work zone as it now stands
    cadence: each week
    authority: O. Reg. 213/91 s. 67(4)–(5) requires the plan in writing and kept at the project. No review interval is prescribed
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/traffic-protection-reviews.md
    escalate: {after: 3d, to: health-safety-lead}
  register:
    title: Traffic Protection Review Record
    note: >
      One row per project per week the work zone is live. `plan_current` and
      `plan_matches_site` are two questions, not one: a plan can be the latest
      revision on file and still describe a taper that was moved on Tuesday, and
      only the second question is answered by walking the zone.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: work_zone, label: Work zone, type: text, required: true}
      - {key: posted_speed, label: Posted speed limit, type: int, required: true}
      - {key: plan_current, label: The written plan on site is the current revision, type: bool, required: true}
      - {key: plan_matches_site, label: The plan matches what is on the ground, type: bool, required: true}
      - {key: measures, label: Measures in place, type: longtext, required: true}
      - {key: barriers_or_trucks, label: Barriers or crash trucks where required, type: bool}
      - {key: workers_directing_traffic, label: Workers directing traffic, type: int, required: true}
      - {key: instructions_at_project, label: Their written instructions are kept at the project, type: bool, required: true}
      - {key: garments_conform, label: High-visibility garments conform, type: bool, required: true}
      - {key: night_work, label: Night work, type: bool, required: true}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: how workers are
protected from vehicular traffic, what the written plan must contain, and what a
worker directing traffic is entitled to before they stand in a live lane.

**Every employer shall develop in writing and implement a traffic protection
plan.** It must specify the hazards and the measures, and it must be **kept at
the project** and made available to an inspector or a worker on request. Existence
is the failure mode here: the plan is not a periodic obligation with a date, it is
a document whose absence is the contravention, which is why the review register
asks whether the plan on site is current **and** whether it matches the ground.

It must set out what a worker setting up or removing traffic protection measures
is owed: they must be a **competent worker**, they must do **no other work** while
doing it, and they must be given **written and oral instructions in a language
they understand**. The same applies to a worker directing traffic, whose written
instructions — including the signals to be used — **must be kept at the project**.

It must state the limits on directing traffic plainly: **one lane only**, and
**never where the posted speed limit exceeds 90 km/h**. Those are hard lines and
they are the two that get negotiated on site at seven in the morning.

It must specify the high-visibility garment as the regulation specifies it —
fluorescent blaze or international orange, two yellow stripes, minimum areas front
and back, the back stripes arranged diagonally, retro-reflective and fluorescent
material, a tear-away feature on nylon vests, and additional retro-reflective
silver stripes encircling each arm and leg for night work. Buying to a
catalogue's description of "Class 2" is not buying to this.

It must specify the paddle and the barrier requirements as the regulation does
rather than by reference to a manual.

**Two things that are widely believed and are not so.** The phrase "traffic
control person" does not appear in the construction regulation at all; the
regulation speaks of a competent worker who directs traffic. And the provincial
traffic manual commonly cited as the standard is a **guideline issued by the
transport ministry, not law**, and is not incorporated into the construction
regulation, the highway legislation or its regulations. Neither "refresher" nor
"recertification" nor any three-year interval appears in it. A vendor card with a
three-year expiry is the vendor's policy. If a client's contract requires that
card, that is a contractual requirement and the document should say so as one.

**The weekly review is this organisation's choice.** No interval is prescribed.
A week is chosen because a work zone on a linear project moves, and a plan drawn
at mobilisation is describing a different road by the second month. Where the
zone changes daily, the plan changes with it and the review interval should
shorten; the document must say who decides that.
