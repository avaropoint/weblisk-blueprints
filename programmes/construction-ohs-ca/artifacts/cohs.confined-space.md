---
id: cohs.confined-space
kind: procedure
title: Confined Space Programme
structure: procedure
path: procedures/confined-space.md

satisfies:
  - cor_2020:COR-08
  - iso_45001:8.1.2

requires: [cohs.pre-task-hazard-assessment, cohs.site-emergency-response]

approved_by: [health-safety-lead]

declares:
  obligation:
    id: cohs.confined-space-programme-review
    activity: Review of the confined space programme, its hazard assessments and its entry plans
    cadence: each year
    authority: O. Reg. 632/05 s. 5 requires the programme. The annual review in s. 8(4) is expressly DISAPPLIED to projects by s. 8(0.1), so no review interval is set for construction
    interval_basis: chosen
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/confined-space-programme-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Confined Space Programme Review Record
    note: >
      One row per review. `spaces_added` and `spaces_reclassified` are columns
      because the programme decays through the inventory rather than through the
      text: a space nobody assessed is not covered by a programme however well
      written, and the review that does not reconcile the list has reviewed the
      document instead of the risk.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: consulted, label: Committee or representative consulted, type: bool, required: true}
      - {key: spaces_in_inventory, label: Spaces in the inventory, type: int, required: true}
      - {key: spaces_added, label: Spaces added since the last review, type: longtext}
      - {key: spaces_reclassified, label: Spaces reassessed or reclassified, type: longtext}
      - {key: rescue_capability, label: Rescue capability tested since the last review, type: bool, required: true}
      - {key: entries_since, label: Entries made since the last review, type: int, required: true}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: changes_made, label: Changes made to the programme, type: longtext}
---

What this document must establish for THIS organisation: which spaces are
confined spaces, what must be done before anybody enters one, who watches, and
who gets them out.

**It must be built on the right regulation.** Confined space entry on a
construction project is governed by O. Reg. 632/05, which applies to every
workplace the Act applies to. The construction projects regulation mentions
confined space exactly once, in connection with a well or augered caisson deeper
than 1.2 m. The old confined spaces part of the construction regulation was
**revoked in July 2011** and is still widely cited; a procedure citing it is
citing nothing.

It must carry the structure the governing regulation requires: a **programme**, a
**hazard assessment** of each space, a **plan**, an **entry permit issued
separately for every entry**, a **rescue** arrangement, an **attendant**, and
**atmospheric testing**. The permit per entry is the part most often reduced to a
permit per space or per day, and the reduction is the failure: the permit exists
because the conditions changed since the last time.

It must state that on a project, every assessment, plan, co-ordination document,
training record, entry permit and test record must be **available at the
project** and retained for **one year after the project is finished**. That is a
retention clock that runs from an event rather than from a date, and the entry
permit register declares it.

**The annual review is this organisation's choice, and the reason matters.** The
governing regulation does contain an annual review requirement — and it is
expressly disapplied to projects. This is a genuine trap: a programme written
from a reading of the regulation without the disapplication will cite an interval
that does not bind it, and an auditor who knows the regulation better than the
author will find a false citation rather than a conservative practice. An annual
review is good practice here. It is not law here. The document must say which.

It must say the same about training: **there is no prescribed confined space
retraining interval for projects.** Any cycle the organisation runs is its own.

It must require the rescue capability to be **demonstrated rather than
described**. A rescue plan naming the fire service is a plan only where somebody
has confirmed that service will enter that space, in that time, with that
equipment — and has it in writing. Entrant self-rescue, attendant-assisted
non-entry rescue, and entry rescue are three different capabilities requiring
three different sets of equipment and people, and a plan that does not say which
one applies has not chosen.

It must forbid the attendant from doing anything else, and must say what happens
when the attendant needs to leave.
