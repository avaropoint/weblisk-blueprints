---
id: ohs.management-of-change
kind: procedure
title: Management of Change
structure: procedure
path: procedures/management-of-change.md

satisfies:
  - iso_45001:8.1.3

requires: [ohs.hazard-assessment-procedure]

declares:
  obligation:
    id: ohs.change-review
    # A PERIODIC confirmation, not one occurrence per change.
    #
    # "on each occurrence" is not a cadence this platform can parse, and an
    # obligation whose cadence does not parse is reported as undeclarable — worse
    # than declaring none. Nor is it record-origin: that form triggers occurrences
    # from the rows of an existing register, and there is no register of PROPOSED
    # changes to trigger from. What is checkable is the assurance an auditor asks
    # for — that in this period, every change was reviewed before it took effect —
    # and the register below is the evidence for it.
    activity: Confirmation that changes in the period were reviewed before taking effect
    cadence: each quarter
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/change-reviews.md
  register:
    title: Change Review Record
    note: >
      One row per change reviewed. `reviewed_before` records whether the review
      happened before the change took effect, because a review conducted
      afterwards is an investigation with better manners, and a register that
      cannot tell them apart will report full compliance either way.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: change, label: Change, type: text, required: true}
      - {key: kind, label: Kind, type: select, required: true,
         options: [Process, Equipment, Substance, Staffing, Site, Legal, Organisational]}
      - {key: reviewed_before, label: Reviewed before it took effect, type: bool, required: true}
      - {key: hazards_introduced, label: New hazards identified, type: longtext, required: true}
      - {key: documents_to_update, label: Documents needing revision, type: longtext}
      - {key: approved, label: Approved to proceed, type: select, required: true,
         options: [Approved, Approved with controls, Refused]}
      - {key: reviewer, label: Reviewed by, type: user, required: true}
---

What this document must establish for THIS organisation: which changes get a
safety review before they happen, and what the review has to answer.

It must define the trigger broadly enough to catch the changes that actually hurt
people. New equipment and new processes are the obvious ones. The ones programmes
miss are a substitution of material, a shift-pattern change, a crew halved, a new
site with a different layout, a supervisor leaving, and a legal requirement
changing under an unchanged process — and every one of those alters a hazard
assessment somebody already signed.

It must be a review BEFORE, and say what happens when a change has already
happened. Both are real; treating them as the same thing is what lets a programme
report that every change was reviewed.

It must ask, at minimum: what hazards does this introduce or alter, which existing
assessments and procedures are now wrong, who needs retraining, and does anything
need to be told to somebody outside the organisation.

It must produce a list of DOCUMENTS to revise, and hand that list to the document
control programme rather than tracking revisions itself. A change reviewed and
approved that leaves six procedures describing the old process has moved the
hazard from the workplace into the documents.

It must say who may approve, and that refusal is available. An approval step with
no possible refusal is a notification step.
