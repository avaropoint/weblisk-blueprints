---
id: priv.policy
kind: policy
title: Privacy Policy
structure: policy
path: policies/privacy-policy.md

satisfies:
  - pipeda:PIPEDA-1
  - pipeda:PIPEDA-8
  - pipeda:PIPEDA-10
  - quebec_law25:GA-1
  - quebec_law25:GA-2
  - iso_27001:A.5.34
  - soc2:P1.1

approved_by: [senior-management]

declares:
  obligation:
    id: priv.programme-review
    activity: Review of the privacy programme
    cadence: each year
    authority: PIPEDA Schedule 1, 4.1 — accountability for personal information under the organisation's control
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/privacy-programme-reviews.md
    escalate: {after: 4w, to: senior-management}
    satisfies:
      - pipeda:PIPEDA-1
      - pipeda:PIPEDA-10
  register:
    title: Privacy Programme Review Record
    note: >
      One row per review. `new_processing_unassessed` is the column that catches
      what nothing else can: a privacy impact assessment is triggered by a
      change rather than by a clock, so the only way to find the changes nobody
      assessed is to ask once a year how many there were.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: inventory_current, label: Personal information inventory verified current, type: bool, required: true}
      - {key: new_processing, label: New or changed processing in the period, type: int, required: true}
      - {key: new_processing_unassessed, label: Of those, not assessed, type: int, required: true}
      - {key: requests_received, label: Access and correction requests received, type: int, required: true}
      - {key: requests_late, label: Of those, answered late, type: int, required: true}
      - {key: breaches, label: Breaches recorded, type: int, required: true}
      - {key: breaches_reported, label: Of those, reported to a regulator, type: int, required: true}
      - {key: complaints, label: Complaints received, type: int, required: true}
      - {key: changes_made, label: Changes made to the programme, type: longtext, required: true}
---

What this document must establish for THIS organisation: who is accountable for
personal information, what the organisation does with it, and how a person
challenges any of that.

It must name the individual accountable by position. PIPEDA's first principle is
accountability and it is the only one that requires a designation: an
organisation with no named privacy officer has not met principle 4.1 however
well it handles the other nine.

It must state which privacy law applies to the organisation and why, because
that is not obvious and getting it wrong shapes everything downstream. For an
Ontario company, PIPEDA applies federally to personal information collected,
used or disclosed in the course of commercial activity — including, in Ontario,
employee information only where the employer is a federal work, undertaking or
business. Ontario has no private-sector privacy statute of general application,
which means there is no provincial law to cite in its place and no equivalent of
Alberta's or British Columbia's PIPA. If the organisation is a health
information custodian, PHIPA governs the health information in its custody and a
separate programme answers it. If it handles the records of an Ontario
institution under contract, FIPPA or MFIPPA reaches it through that contract. If
it collects personal information about people in Quebec in the course of an
enterprise, Law 25 binds it too. The document must say which of these sentences
is true here rather than reciting all of them.

It must be internal and distinguishable from the privacy notice. This document
tells staff what to do; the notice tells the public what the organisation does.
An organisation with one document doing both has either a notice full of
internal procedure or a procedure that explains nothing.

It must state the complaint route, and that it exists before the regulator's
does. Principle 10 requires a procedure to receive and respond to complaints and
that the organisation inform people of it — an organisation whose only route is
to the Privacy Commissioner has made every complaint a regulatory matter.
