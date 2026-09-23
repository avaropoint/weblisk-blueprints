---
id: ohs.return-to-work
kind: procedure
title: Return to Work and Disability Management
structure: procedure
path: procedures/disability-management.md

satisfies:
  - cor_2020:COR-19

requires: [ohs.incident-reporting-procedure]

declares:
  obligation:
    id: ohs.return-to-work-review
    activity: Review of an open return-to-work plan
    cadence: each month
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/return-to-work-plan-reviews.md
  register:
    title: Return to Work Review Record
    note: >
      One row per review of an open plan, not one per worker. A plan is reviewed
      repeatedly as the person recovers, and a register keyed to the worker would
      overwrite the history that shows whether the accommodation was working.
      Nothing clinical belongs in these columns — see the note in the document.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: case_ref, label: Case reference, type: text, required: true}
      - {key: restrictions_current, label: Restrictions still accurate, type: bool, required: true}
      - {key: duties_available, label: Suitable duties available, type: bool, required: true}
      - {key: hours, label: Hours per week, type: int}
      - {key: progressing, label: Progressing to full duties, type: select, required: true,
         options: [On plan, Behind plan, Plan needs revision, Returned to full duties]}
      - {key: next_review, label: Next review due, type: date, required: true}
      - {key: reviewer, label: Reviewed by, type: user, required: true}
---

What this document must establish for THIS organisation: how an injured worker
gets back to work safely, and who arranges it.

It must open with the boundary this procedure lives on. The organisation is
entitled to know what a worker CAN DO — the restrictions and the duration. It is
not entitled to the diagnosis. A procedure that collects clinical information
because a form has a box for it has created a disclosure risk in the course of
managing an injury, and the register above is deliberately restricted to
capability and progress for that reason.

It must name who owns a case and who the worker deals with, because a worker
recovering from an injury should not be negotiating with four people.

It must set out how suitable duties are identified against real restrictions,
rather than a list of light jobs. "Suitable" is a judgement about this workplace
and this person, and duties invented to occupy somebody are visible as such and
corrosive.

It must say what happens when there are no suitable duties, and that saying so is
an allowed outcome. A procedure with no such path produces accommodations that
exist on paper.

It must connect to the incident reporting procedure, so an injury does not become
a claim in one system and a case in another with no join between them.

Where the jurisdiction imposes obligations — a duty to re-employ, notice periods,
reporting to a board — the document must record them as external requirements
rather than as this organisation's policy, and the register of legal requirements
is where they are tracked.
