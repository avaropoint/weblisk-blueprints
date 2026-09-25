---
id: cenv.excess-soil-registry
kind: procedure
title: Excess Soil Registry Filing
structure: procedure
path: procedures/excess-soil-registry-filing.md

satisfies:
  - o_reg_406_19:8
  - o_reg_406_19:27

requires: [cenv.soil-reuse-planning]

declares:
  obligation:
    id: cenv.excess-soil-registry
    activity: Registry notice filed, or the determination that none is owed recorded, before soil leaves the project area
    for:
      records: registers/excavation-projects.md
      due: 5d before excavation_start_on
      key: area_id
    authority: >
      O. Reg. 406/19 s. 8 (1). The notice must be filed BEFORE removing from the
      project area soil that will become excess soil once removed. The
      regulation sets no lead time; filing it the morning the first truck
      arrives is lawful
    interval_basis: chosen
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/excess-soil-registry-filings.md
    escalate: {after: 3d, to: project-manager}
  register:
    title: Excess Soil Registry Filing Record
    note: >
      One row per project area, including the ones where nothing was filed.
      `outcome` is a select and not free text because the reasons for not filing
      are a closed list in the regulation and the point of recording which one
      applied is to be able to defend the decision years later — including the
      decision that none applied, which is why "no notice required" is an
      outcome and not a blank row. The Registry number is the join between this
      organisation's record and the Authority's.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 7y
      authority: O. Reg. 406/19 s. 28 (1) — every document and record created or acquired under the Regulation is retained for at least seven years after it is created or acquired
      reason: >
        The filed notice and the declaration in it are the organisation's
        evidence that it filed. The Registry holds its own copy; a regulator's
        system is not this organisation's record-keeping.
    columns:
      - {key: area, label: Project area, type: relation, required: true,
         target: /registers/excavation-projects.md#records, display: area_id}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Notice filed,
                   "No notice — no criterion in s. 8 (1.1) is met",
                   "No notice — Schedule 2, 100 m3 or less directly to a waste disposal site",
                   "No notice — Schedule 2, 100 m3 or less to a local waste transfer facility",
                   "No notice — Schedule 2, immediate danger, a s. 93 duty, or an order",
                   "No notice — Schedule 2, maintaining infrastructure in a fit state of repair",
                   "No notice — Schedule 2, topsoil taken directly to a reuse site",
                   "No notice — Schedule 2, landscaping of 100 m3 or less with a qualified person's report",
                   "No notice — Schedule 2, infrastructure project to the project leader's or a public body's reuse site",
                   "No notice — Schedule 2, temporary removal or a single larger planned initiative",
                   "No notice — we are not the project leader",
                   Outstanding]}
      - {key: filed_on, label: Filed on, type: date}
      - {key: registry_number, label: Registry notice number, type: text}
      - {key: filed_by, label: Filed by, type: user}
      - {key: declaration_made_by, label: Who made the project leader's declaration, type: text}
      - {key: estimated_volume_m3, label: Volume declared, in cubic metres, type: number}
      - {key: destinations_declared, label: Destinations declared, type: longtext}
      - {key: first_load_on, label: First load removed on, type: date}
      - {key: filed_before_first_load, label: Filed before the first load left, type: bool, required: true}
      - {key: evidence, label: Copy of the filed notice, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: who files a notice in
the Excess Soil Registry, what goes in it, what evidence is kept, and — the part
that is actually hard — how the decision that no notice is owed gets made and
written down.

It must state the rule as the regulation states it: the **project leader** shall
ensure that, **before removing from the project area soil that will become excess
soil once removed**, a notice setting out the sixteen items in Schedule 1 is
filed in the Registry. The Registry is the one described in s. 50 of the
*Resource Recovery and Circular Economy Act, 2016* and is operated by the
Resource Productivity and Recovery Authority; the filing is made in the form
approved by the Director.

It must set out **Schedule 1** rather than summarise it as "project details".
The items that are most often missing at the moment of filing are the ones that
require somebody else's work: the geographic coordinates of the centroid of each
property, measured by GPS and projected on UTM; the volume broken down by the
Excess Soil Standards table the soil meets if it is going to a reuse site for
final placement; every intended Class 1 and Class 2 soil management site, local
waste transfer facility, reuse site, landfill and dump; and the applicable excess
soil quality standards for each reuse site. It must also state that the filing
ends in a **declaration by the project leader** — that reasonable inquiries were
made, that the qualified person was given the information and the access, that
the information is complete and accurate, and that the necessary procedures will
be developed and applied. Somebody's name goes on that, which is why the register
records whose.

**Five days is this organisation's choice and the regulation's lead time is
none.** It is chosen so that a determination made wrongly can be corrected before
anybody is on site, and so that a destination that turns out not to be accepting
soil is discovered before the notice has to be amended. A notice filed on the
morning of the first load is lawful and is also the version of this duty that
fails the first time a laboratory is late.

**A notice is not owed on most jobs, and saying so is the substance of this
procedure.** It is owed only where the project area meets one of the three
criteria in subsection 8 (1.1). Schedule 2 then removes seven further sets of
circumstances, and two of them will cover a great deal of ordinary work: 100 m³
or less transported directly to a waste disposal site that is not a Class 2 soil
management site, and 100 m³ or less deposited at a local waste transfer facility.
So the honest shape of this obligation is a **determination recorded for every
project area** and a filing on the minority of them. A programme that made every
load a Registry filing would be wrong, would cost the organisation money it does
not owe, and would be abandoned — and the abandonment would take the filings that
were owed with it.

**The exemption that ended on 1 January 2026 must be named and then closed.**
Until then, clause 8 (2) (b) exempted a project where the project leader had
entered into a contract with another person for the management of excess soil
from the project **before 1 January 2022**. That clause was revoked on 1 January
2026. Any long-running job that was relying on it is now inside the Registry
regime, and the first place that shows up is a project area whose row has never
had a notice and whose soil is still moving. This procedure must say so, because
an organisation that learned the rule during the phase-in learned a rule that no
longer exists.

**`filed_before_first_load` is required and the honest answer is sometimes no.**
A register that cannot record a late filing will be filled in as though every
filing was early, and the contravention will be invisible in the one system that
could have found it.
