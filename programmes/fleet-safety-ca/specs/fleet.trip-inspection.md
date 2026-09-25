---
id: fleet.trip-inspection
kind: procedure
title: Daily Trip Inspection
structure: procedure
path: procedures/daily-trip-inspection.md

satisfies:
  - hta_ontario:HTA-TRIP-01
  - hta_ontario:HTA-TRIP-02
  - hta_ontario:HTA-TRIP-03
  - hta_ontario:HTA-TRIP-04
  - hta_ontario:HTA-TRIP-05
  - hta_ontario:HTA-TRIP-06
  - hta_ontario:HTA-PMVI-04
  - hta_ontario:HTA-CVOR-03
  - nsc_ca:NSC-13
  - cor_2020:COR-11

requires: [fleet.policy, fleet.vehicles, fleet.drivers]

declares:
  obligation:
    id: fleet.trip-inspection
    activity: Trip inspection of the vehicle before it is driven, and monitoring of its condition through the day
    cadence: each day
    authority: >
      O. Reg. 199/07 (Commercial Motor Vehicle Inspections), Ontario's adoption
      of National Safety Code Standard 13 — a commercial motor vehicle must be
      inspected before it is driven on a day, and the inspection report is valid
      for 24 hours from the time the inspection was conducted.
    interval_basis: required
    responsible: fleet-manager
    applies_to: the organisation
    per:
      listed_in: registers/vehicles.md
      key: unit_number
      label: description
      from: in_service_on
      until: out_of_service_on
    records: registers/trip-inspections.md
    escalate: {after: 24h, to: senior-management}
    satisfies:
      - hta_ontario:HTA-TRIP-01
      - hta_ontario:HTA-TRIP-03
      - nsc_ca:NSC-13
  register:
    title: Daily Trip Inspection Report
    note: >
      One row per vehicle per day it is driven. This is the statutory inspection
      report and it carries what the regulation requires the report to carry —
      the vehicle, the operator, the date AND the time the inspection was
      conducted, the person who conducted it, the odometer, and every defect
      found or an express statement that none was found. `defects_found` is a
      required yes/no rather than an optional free-text field because a blank
      defect field asserts nothing: "none found" is a statement somebody is
      answerable for. A vehicle in the register that was not driven on a day has
      no report to make and no obligation to discharge; record that with
      `not_driven` rather than filing an inspection nobody did.
    layout: form
    columns:
      - {key: reference, label: Report number, type: text, required: true}
      - {key: inspected_on, label: Date of inspection, type: date, required: true}
      - {key: inspected_at, label: Time the inspection was conducted, type: text, required: true}
      - {key: vehicle, label: Vehicle, type: relation, required: true,
         target: /registers/vehicles.md#records, display: unit_number}
      - {key: driver, label: Inspected by, type: relation, required: true,
         target: /registers/drivers.md#records, display: driver_id}
      - {key: operator_of_record, label: Operator, type: text, required: true}
      - {key: odometer, label: Odometer reading, type: int, required: true}
      - {key: schedule_used, label: Inspection schedule used, type: select, required: true,
         options: ["Schedule 1 — trucks, tractors and trailers",
                   "Schedule 2 — buses",
                   "Schedule 3 — school purposes vehicles",
                   "Schedule 4 — motor coaches"]}
      - {key: schedule_carried, label: The schedule and the report are carried in the vehicle, type: bool, required: true}
      - {key: trailer_units, label: Trailers or towed units inspected with it, type: longtext}
      - {key: not_driven, label: The vehicle was not driven on this day, type: bool, required: true}
      - {key: defects_found, label: Defects found, type: select, required: true,
         options: ["None found", "Minor defect(s) found", "Major defect(s) found",
                   "Both major and minor defects found"]}
      - {key: defects, label: What was found, type: longtext}
      - {key: defect_records, label: Defect numbers raised in the defect register, type: text}
      - {key: reported_to_operator_at, label: Time the defect was reported to the operator, type: text}
      - {key: vehicle_driven_after, label: The vehicle was driven after the inspection, type: bool, required: true}
      - {key: in_service_defects, label: Defects found or reported during the day, type: longtext}
      - {key: declaration, label: Signed by the person who conducted the inspection, type: signature, required: true}
    retention:
      keep: 6m
      authority: O. Reg. 199/07 — the operator keeps the inspection reports for six months at the place where the vehicle is based
      reason: The reports are the evidence a facility audit asks for; an operator that lets them travel with the vehicle has done the inspections and cannot show it.
---

What this document must establish for THIS organisation: who inspects what,
against which schedule, before a vehicle moves — and what stops the vehicle.

**The interval here is the law's, and it is the only one in this programme that
is.** The vehicle is inspected before it is driven on a day and the report is
valid for twenty-four hours from the time the inspection was conducted. Two
consequences the procedure must spell out, because both are routinely got
wrong: a vehicle driven on yesterday's report is being driven without one, and
the twenty-four hours run from the **time** on the report, which is why the
time and not only the date is a required field.

**The schedule is prescribed by vehicle type and is carried in the vehicle.**
Trucks, tractors and trailers, buses, school purposes vehicles and motor
coaches each have their own schedule listing the components to be inspected
and, for each, what counts as a major defect and what counts as a minor one. A
driver inspecting a trailer against a bus schedule has produced a thorough
report about the wrong components. The procedure must say where the schedule
lives in each vehicle and who replaces it when it goes missing, because a
schedule that is not in the cab is a contravention that an officer reads before
they read anything else.

**Major and minor is the whole point, and it is prescribed rather than
judged.** On finding or being informed of a **major** defect the driver must
not drive the vehicle: it stops where it is, the defect is reported to the
operator immediately, and it stays out of service until it is repaired. On
finding a **minor** defect the driver records it, reports it, and the vehicle
may continue. The procedure must name who the driver reports to at five in the
morning, what happens when that person does not answer, and — the sentence most
organisations will not want to write — that nobody may instruct a driver to
move a vehicle with an open major defect.

**The duty does not end when the vehicle leaves.** The driver monitors the
vehicle's condition through the day and records any defect found or reported
during it. Most of the major defects that matter — a wheel fastener, a brake, a
load-bearing component — develop in service rather than overnight in the yard,
and a report that can only be written at 06:00 will never hold one.

**It must say how a defect becomes a row in the defect register.** The
inspection report and the defect register are different documents on purpose:
most inspections find nothing, and triggering a repair decision off the
inspection would raise thousands of empty obligations a year and bury the few
that mattered. The procedure must therefore describe the hand-off — who raises
the defect number, and by when — and the report records that number so the two
can be joined afterwards.

**Trailers are vehicles.** A tractor and a trailer are separately inspected,
and a contractor whose trailers are not in the vehicle register has a fleet
that is half inspected and fully compliant on paper.

**The operator's own duties are three and they are separable**: require the
inspection to be conducted, repair a defect reported to it, and keep the
reports for six months at the place where the vehicle is based. The third is
the one that fails quietly — reports left in the cab are evidence the
organisation cannot produce.
