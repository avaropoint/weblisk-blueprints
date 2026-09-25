---
id: ohs.preventive-maintenance
kind: procedure
title: Preventive Maintenance
structure: procedure
path: procedures/preventive-maintenance.md

satisfies:
  - cor_2020:COR-12
  - isnetworld:ISN-SAFE-09

requires: [ohs.hazard-assessment-procedure]

declares:
  obligation:
    id: ohs.maintenance-due
    activity: Scheduled maintenance or inspection of safety-critical equipment
    cadence: each month
    responsible: site-supervisor
    applies_to: the organisation
    records: registers/maintenance.md
  register:
    title: Maintenance Record
    note: >
      One row per item serviced. `due_on` beside `serviced_on` is what makes the
      schedule auditable: a register of work performed cannot show the service
      that was thirty days late, and lateness is the finding.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: item, label: Item, type: text, required: true}
      - {key: identifier, label: Serial or unit number, type: text, required: true}
      - {key: due_on, label: Due on, type: date, required: true}
      - {key: serviced_on, label: Serviced on, type: date, required: true}
      - {key: work, label: Work performed, type: longtext, required: true}
      - {key: defects, label: Defects found, type: longtext}
      - {key: out_of_service, label: Removed from service, type: bool, required: true}
      - {key: certification, label: Certificate or standard applied, type: text}
      - {key: serviced_by, label: Serviced by, type: text, required: true}
---

What this document must establish for THIS organisation: which equipment is
safety-critical, how often each item is serviced, and what happens when a defect
is found.

The list must come from the hazard assessments. Equipment is safety-critical when
its failure is a hazard control failing — fall protection, lifting gear, guards,
gas detection, respirators, vehicles, electrical isolation. A maintenance schedule
built from an asset register instead lists what the organisation owns rather than
what protects anybody.

It must separate the intervals set by LAW or by the manufacturer from those the
organisation chose. The first are not negotiable when a schedule slips, and a
document that presents them identically invites the wrong thing to be deferred.

It must state how a defect takes an item out of service, and how it is prevented
from coming back — a tag, a lock, a physical removal. "Report it to
maintenance" is not a control while the item is still on the rack.

It must cover operator pre-use checks as distinct from scheduled service. The
pre-use check is what catches the failure that developed since the service, and a
programme with only the schedule is inspecting on a calendar while the equipment
fails on its own timetable.

Where equipment carries a statutory certificate, the document must say who holds
it and where it is kept, because an inspector asks for the certificate rather than
for the maintenance record.
