---
id: cohs.ppe
kind: procedure
title: Protective Equipment on a Project
structure: procedure
path: procedures/protective-equipment.md

satisfies:
  - ohsa_ontario:25(1)
  - o_reg_213_91:21
  - o_reg_213_91:22
  - o_reg_213_91:23
  - cor_2020:COR-10
  - isnetworld:ISN-SAFE-08

requires: [cohs.pre-task-hazard-assessment]

declares:
  obligation:
    id: cohs.protective-equipment-check
    activity: Check that the protective equipment in use on the project meets the prescribed performance and fits each worker
    cadence: each month
    authority: O. Reg. 213/91 ss. 21–25; OHSA s. 25(1)(b.1) — the duties are continuous and no inspection interval is prescribed
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/protective-equipment-checks.md
    escalate: {after: 2w, to: health-safety-lead}
  register:
    title: Protective Equipment Check Record
    note: >
      One row per check. `fit_exceptions` is a column because proper fit became a
      strict employer duty in December 2024 and it fails for real, identifiable
      people — a worker for whom the standard-issue harness or respirator does not
      fit is an exclusion with a name, not a preference, and a register with
      nowhere to record it produces a clean sheet and an unprotected person.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: head_protection, label: Head protection conforms and is in good condition, type: bool, required: true}
      - {key: footwear, label: Footwear conforms, type: bool, required: true}
      - {key: eye_protection, label: Eye protection appropriate to the work in use, type: bool, required: true}
      - {key: high_visibility, label: High-visibility garments conform where required, type: bool, required: true}
      - {key: fit_exceptions, label: Workers for whom issued equipment does not fit, type: longtext}
      - {key: fit_action, label: What was done about them, type: longtext}
      - {key: removed_from_service, label: Equipment removed from service, type: longtext}
      - {key: instruction_given, label: Workers instructed in care and use before wearing, type: bool, required: true}
---

What this document must establish for THIS organisation: which protective
equipment is required for which work on a project, what it must actually meet,
and how it is kept fit to use.

It must state the Ontario requirements as the regulation states them, because the
common shorthand is wrong today. **Head protection** must have a shell and
suspension adequate against impact and flying or falling small objects, with a
shell that withstands a dielectric strength test at twenty thousand volts
phase-to-ground — the section names **no CSA standard at all**. **Footwear** must
have a box toe resisting at least 125 joules and a sole and insole resisting a
1.2 kilonewton penetration load — again, **no CSA standard is named**.
Green-triangle footwear satisfies those numbers, but the numbers are the legal
test and a purchasing specification written to the symbol rather than the
performance is buying the right boot for the wrong reason. **Eye protection** is
required to be "appropriate in the circumstances" and cites nothing.

A document asserting "must meet CSA Z94.1" is not accurate today. It **becomes**
accurate on 1 July 2027, when the head protection section is replaced by a
standard-referenced requirement — Type 2 to CSA Z94.1 or Type II to ANSI Z89.1
where a side-impact hazard exists, otherwise the general standard, plus a chin
strap or retention system where headwear may dislodge. That new reference is
unusual in naming **no edition year**, so it will float to whatever edition is
current. An organisation with a written specification should diarise the change
rather than discover it.

**Proper fit is now a strict duty on the employer** and it is not a footnote.
Equipment that fits a mannequin and not a person is not protection, and the
failure is concentrated in the people a standard size was never drawn for. The
document must say who a worker tells, who decides, and who pays — and the answer
to the last one must not be the worker.

It must place equipment where the hierarchy puts it: last. Equipment is what
remains after elimination, substitution and engineering, and a programme that
opens with the kit list teaches the opposite of the pre-task assessment it
depends on.

It must tie each requirement to a **hazard** rather than to a job title. "Head
protection everywhere inside the hoarding" is enforceable; "head protection for
labourers" leaves the visiting engineer bare-headed under the same crane.

It must require workers to be adequately instructed and trained in the care and
use of the equipment **before** they wear or use it, and must say where that
instruction is recorded.

**The monthly check is this organisation's choice.** The duties are continuous
and no inspection interval is prescribed for general protective equipment. Fall
protection equipment is a separate artifact with a separate regime and this check
does not discharge it.
