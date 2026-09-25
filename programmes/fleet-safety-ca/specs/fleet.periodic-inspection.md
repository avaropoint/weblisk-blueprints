---
id: fleet.periodic-inspection
kind: procedure
title: Periodic Motor Vehicle Inspection
structure: procedure
path: procedures/periodic-motor-vehicle-inspection.md

satisfies:
  - hta_ontario:HTA-PMVI-01
  - hta_ontario:HTA-PMVI-02
  - hta_ontario:HTA-PMVI-04
  - hta_ontario:HTA-CVOR-03
  - nsc_ca:NSC-11
  - cor_2020:COR-12

requires: [fleet.policy, fleet.vehicles]

declares:
  obligation:
    id: fleet.periodic-inspection
    activity: Book, obtain and file the periodic inspection before the vehicle's sticker expires
    for:
      records: registers/vehicles.md
      due: 30d before inspection_expires_on
      key: unit_number
    authority: >
      R.R.O. 1990, Reg. 611 (Safety Inspections) under the Highway Traffic Act,
      Ontario's adoption of the periodic inspection half of National Safety Code
      Standard 11 — a commercial motor vehicle must be inspected at a licensed
      motor vehicle inspection station and display a valid sticker showing the
      month and year the inspection expires. The TWELVE MONTHS is the law's and
      is not optional; what this obligation sets is the THIRTY DAYS OF NOTICE
      before the sticker's own expiry date, and that interval is this
      organisation's — chosen because a licensed station needs booking and a
      vehicle that fails needs time to be repaired and re-presented.
    interval_basis: chosen
    responsible: maintenance-lead
    applies_to: the organisation
    records: registers/periodic-inspections.md
    escalate: {after: 2w, to: fleet-manager}
    satisfies:
      - hta_ontario:HTA-PMVI-01
      - hta_ontario:HTA-PMVI-02
      - nsc_ca:NSC-11
  register:
    title: Periodic Inspection Record
    note: >
      One row per periodic inspection of a vehicle. `outcome` distinguishes a
      pass from a pass after repair and from a failure, because a vehicle that
      needed work to earn its sticker is telling the maintenance programme
      something a bare "passed" hides. `new_expiry` is what the next occurrence
      is measured from, so it must be copied back onto the vehicle register —
      the procedure says who does that, and it is the step most often missed.
    layout: form
    review: required
    approvers: [maintenance-lead]
    columns:
      - {key: vehicle, label: Vehicle, type: relation, required: true,
         target: /registers/vehicles.md#records, display: unit_number}
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: station_name, label: Inspection station, type: text, required: true}
      - {key: station_licence, label: Station licence number, type: text, required: true}
      - {key: technician, label: Technician, type: text, required: true}
      - {key: odometer, label: Odometer reading, type: int, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: ["Passed", "Passed after repair at the inspection",
                   "Failed — repaired and re-presented",
                   "Failed — vehicle withdrawn from service", "Not yet determined"]}
      - {key: defects_found, label: What was found, type: longtext}
      - {key: repairs_made, label: What was repaired, type: longtext}
      - {key: certificate_number, label: Inspection certificate number, type: text, required: true}
      - {key: sticker_issued, label: Sticker issued, type: bool, required: true}
      - {key: previous_expiry, label: Previous sticker expiry, type: date}
      - {key: new_expiry, label: New sticker expires on, type: date, required: true}
      - {key: register_updated, label: The vehicle register has been updated with the new expiry, type: bool, required: true}
      - {key: cost, label: Cost, type: currency}
      - {key: attachment, label: Inspection certificate, type: attachment}
    retention:
      keep: 2y
      authority: >
        The operator keeps the inspection certificate or report. No period is
        stated in Reg. 611 for the operator's own copy; two years is this
        organisation's, set to cover a facility audit's review period.
      reason: This is the document a facility audit asks for first, and the one most often missing for a vehicle acquired mid-year.
---

What this document must establish for THIS organisation: who books the annual
inspection, what happens when a vehicle fails it, and how the next one comes to
be known about.

**The twelve months is the law's; the thirty days is ours, and the distinction
is worth a sentence in the document.** A truck or trailer's sticker is valid for
twelve months and a bus is on a shorter cycle. Nothing about that is
discretionary. What the programme can act on is the sticker's **own expiry
date**, which is a fact sitting on the vehicle's row — so the work is triggered
by the record rather than by a calendar, and the thirty days of notice is a
number the organisation picked because a licensed station has a waiting list.
`interval_basis: chosen` here means the notice period is chosen. It does not
mean the inspection is.

**The sticker is the one compliance item an officer can read from outside the
vehicle**, which is why an expired one is among the most reliably caught
contraventions in the whole regime, and why it lands on the CVOR record without
anybody having inspected anything.

**The inspection is done at a licensed motor vehicle inspection station against
the prescribed standard.** The organisation's own shop cannot issue a sticker
unless it holds that licence, and the procedure must say which stations are
used and who approves a new one. Where the organisation *is* a licensed
station, it must say how the person inspecting is independent of the person
answerable for the fleet's availability.

**A failure is the useful outcome, and the procedure must have a path for it.**
A vehicle that fails is a vehicle that may not be operated until it is
repaired, and the organisation needs to know who is told, what replaces it on
the job, and by when it is re-presented. A procedure that only describes a pass
is one nobody reads on the day they need it.

**The certificate is the record, and the sticker is not.** The inspection
produces a certificate or report recording what was inspected, what was found,
what was repaired and who did it, and the operator keeps it. A fleet with
current stickers and no certificates has a defence at the roadside and none at
an audit.

**Copying the new expiry date back onto the vehicle register is part of the
work**, not administration afterwards. It is the fact the next occurrence is
measured from, and a register left at last year's date will either chase a
vehicle that is current or, worse, go quiet about one that is not.
