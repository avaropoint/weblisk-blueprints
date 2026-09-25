---
id: fipa.flow-down
kind: procedure
title: Institutional Contract Requirements
structure: procedure
path: procedures/institution-contract-requirements.md

satisfies:
  - fippa_mfippa:FM-02
  - fippa_mfippa:FM-12
  - fippa_mfippa:FM-11
  - iso_27001:A.5.19

requires: [fipa.institutional-records]

declares:
  obligation:
    id: fipa.contract-review
    activity: Review institutional contracts and subcontracts for privacy and security flow-down
    cadence: each year
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/institutional-contract-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Institutional Contract Review Record
    note: >
      One row per review. Subcontractors are counted separately because the
      flow-down duty is the one that breaks: an organisation that has accepted
      strict terms from an institution and passed none of them to the
      subcontractor doing the work has kept the liability and given away the
      control.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: contracts, label: Institutional contracts in force, type: int, required: true}
      - {key: with_privacy_terms, label: With privacy and security terms, type: int, required: true}
      - {key: residency_terms, label: With data residency requirements, type: int, required: true}
      - {key: subcontractors, label: Subcontractors touching institutional records, type: int, required: true}
      - {key: subcontractors_bound, label: Of those, bound by equivalent terms, type: int, required: true}
      - {key: staff_screened, label: Staff with access confirmed as screened and under confidentiality, type: bool, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: what the institution's
contract requires, and how those requirements reach everybody who touches the
records.

It must treat the contract as the source of the obligation. FIPPA and MFIPPA do
not bind a private-sector supplier directly; the institution's duties reach the
supplier through terms, and what those terms say is therefore the whole of the
requirement. An organisation that has read the statute and not the schedule has
studied the wrong document.

It must name the terms that are usually there and check each one: purpose
limitation, security safeguards, no disclosure without the institution's
direction, cooperation with access requests, notification of a privacy breach to
the institution, restrictions on where the data may be held, return or
destruction at the end, audit rights, and screening and confidentiality
undertakings for staff.

It must pass every one of them down. A subcontractor, a cloud service or an
offshore development team touching institutional records without equivalent
terms is the single most common finding in a public-sector supplier audit, and
the organisation carries the liability for it.

It must record where the data is. Institutions frequently require records to
remain in Canada, and an organisation whose supplier moved a workload between
regions without notice has breached a term it never re-read.

It must connect to the security programme's supplier register rather than
keeping a second list. The register already records data location, sub-processor
changes and assurance held; what this procedure adds is the institutional
overlay on those rows.
