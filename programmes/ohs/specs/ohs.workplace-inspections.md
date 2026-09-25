---
id: ohs.workplace-inspections
kind: procedure
title: Workplace Inspections
structure: procedure
path: procedures/workplace-inspection.md

satisfies:
  - cor_2020:COR-11
  - isnetworld:ISN-SAFE-10

requires: [ohs.hazard-assessment-procedure]

declares:
  obligation:
    id: ohs.workplace-inspection
    activity: Workplace inspection
    cadence: each month
    responsible: site-supervisor
    applies_to: each project
    records: registers/workplace-inspections.md
  register:
    title: Workplace Inspection Record
    # Records are SUBMITTED, not typed.
    #
    # A grid autosaves every keystroke, so a half-finished inspection is committed
    # to the repository as it is being written — and an inspection is evidence that
    # discharges an obligation, which is exactly the record that must not exist in
    # a half state. A form drafts in the browser and commits once, as one
    # attributable version, which is also what gives the occurrence a single act to
    # attest.
    layout: form
    # The supervisor performs the inspection and the health and safety lead signs
    # it off, so the record carries two names rather than one. Declared here rather
    # than configured per organisation afterwards, which is the whole point: a
    # programme should arrive operating.
    review: required
    approvers: [health-safety-lead]
    note: >
      One row per inspection. `findings_closed` against `findings_raised` is the
      column pair that makes the programme measurable: inspections that raise
      findings nobody closes are a schedule being met and a hazard being
      recorded repeatedly, and a count of inspections alone cannot tell those
      apart.
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: location, label: Site or work area, type: text, required: true}
      - {key: scope, label: What was inspected, type: text, required: true}
      - {key: worker_participant, label: Worker who took part, type: user}
      - {key: findings_raised, label: Findings raised, type: int, required: true}
      - {key: findings_closed, label: Of those, closed, type: int, required: true}
      - {key: unsafe_stopped, label: Work stopped, type: bool, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
      - {key: inspector, label: Inspected by, type: user, required: true}
---

What this document must establish for THIS organisation: who inspects what, how
often, and what happens to what they find.

It must distinguish an INSPECTION from a hazard assessment, because the two are
routinely confused and answer different questions. A hazard assessment asks what
could go wrong before work begins. An inspection asks whether the controls that
were chosen are actually in place, in the workplace as it is now. An organisation
doing only the first has decided what should be true and never looked.

It must set a schedule that names the LOCATION and the frequency, and say what
drives the frequency — hazard, occupancy, rate of change. A single organisation-
wide interval treats a quiet office and an active excavation as the same risk.

It must require a worker to take part, not merely be informed. An inspection
conducted entirely by management finds what management already knows about.

It must say what happens to a finding: who owns it, by when, and how closure is
recorded. This is the half that decides whether the programme improves anything —
and it is why the register above counts findings closed as well as raised.

It must say what stops work immediately rather than becoming a finding. An
inspection procedure with no stop-work threshold has decided that everything can
wait for the report.
