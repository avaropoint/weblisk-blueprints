---
id: cohs.defibrillator
kind: procedure
title: Defibrillators on Projects
structure: procedure
path: procedures/defibrillator.md

satisfies:
  - cor_2020:COR-13
  - iso_45001:8.2

requires: [cohs.site-emergency-response]

declares:
  obligation:
    id: cohs.defibrillator-inspection
    activity: Inspection of the project's defibrillator by a competent worker in accordance with the manufacturer's instructions
    cadence: each quarter
    authority: O. Reg. 213/91 s. 27.1(7)–(8) — inspected quarterly by a competent worker, the record kept with the defibrillator showing the date and the name and signature of the worker
    interval_basis: required
    responsible: site-supervisor
    applies_to: each project
    records: registers/defibrillator-inspections.md
    escalate: {after: 2w, to: health-safety-lead}
  register:
    title: Defibrillator Inspection Record
    note: >
      One row per unit per quarter. The statutory record is the one kept WITH the
      defibrillator — date, name and signature — and this register does not
      replace it. `record_with_unit` is a column so that the organisation can see
      the difference between a unit that was inspected and a unit whose
      inspection an inspector will be able to find.
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: unit, label: Unit and serial number, type: text, required: true}
      - {key: inspector, label: Inspected by, type: user, required: true}
      - {key: per_manufacturer, label: Inspected per the manufacturer's instructions, type: bool, required: true}
      - {key: status_indicator, label: Status indicator normal, type: bool, required: true}
      - {key: pad_expiry, label: Electrode pad expiry, type: date, required: true}
      - {key: battery_expiry, label: Battery expiry or replacement due, type: date, required: true}
      - {key: accessories_complete, label: Prescribed accessories present and complete, type: bool, required: true}
      - {key: accessories_missing, label: What was missing, type: longtext}
      - {key: signage, label: Signage at the unit and throughout the project, type: bool, required: true}
      - {key: unobstructed, label: Storage protected and unobstructed, type: bool, required: true}
      - {key: trained_worker_present, label: A worker trained in CPR and defibrillator use present whenever work is in progress, type: bool, required: true}
      - {key: record_with_unit, label: Inspection record kept with the unit, dated and signed, type: bool, required: true}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: which projects require a
defibrillator, who provides it, where it lives, who checks it, and who must be on
site to use it.

**This is new law and it is construction-specific.** Since 1 January 2026, where
**twenty or more workers are regularly employed** at a project, **the
constructor** must ensure a defibrillator is installed and maintained — and the
duty does not apply where the work is expected to last **less than three months**.
Those are the same two thresholds as the joint health and safety committee, with a
different duty holder, which is precisely why they belong as columns on the
register of projects rather than as something a project manager recalls.

It must record who the duty falls on. It is the **constructor's**, not each
employer's, and an organisation that is a sub-trade on a large site should know
that it is relying on somebody else's unit and should have confirmed that it
exists.

It must list the accessories the regulation prescribes to be stored with the unit,
and must treat the list as a list rather than as a suggestion: a CPR mask, a pair
of scissors, two pairs of disposable medical-grade gloves, a disposable razor, a
garbage bag and four absorbent towels. The device must be licensed for sale in
Canada.

It must cover storage and signage as prescribed: protected, unobstructed, marked
with the recognised symbol, and with location signs throughout the project. A
defibrillator nobody can find in ninety seconds is a defibrillator that will not
be used.

**The quarterly inspection is the law's, and so is where the record goes.** The
inspection is by a **competent worker**, in accordance with the manufacturer's
instructions, and the record — the date of each inspection and the **name and
signature** of the worker — is kept **with the defibrillator**. An organisation
that keeps only a central register has the record in the wrong place, which is a
contravention of a subsection specifically about where the record lives.

**And the staffing duty is continuous.** At all times when work is in progress, a
worker trained in cardiopulmonary resuscitation and in the operation of a
defibrillator must be **present**. That is a rostering constraint, not a training
target, and it is the part that fails on a Saturday pour or a night shift.

It must state that **no CPR or defibrillator certificate interval is set in
Ontario law**. The familiar three-year card is the certifying body's period. It is
a real constraint on whether a certificate is accepted and it is not a statutory
one, and the register of statutory credentials records it that way.

It should note that a reimbursement programme exists for a unit purchased within a
defined window, capped per qualifying project, with a claim deadline — and that
the enabling section is scheduled to be repealed on a day yet to be named. An
organisation that intends to claim should claim early rather than plan around it.
