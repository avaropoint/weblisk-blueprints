---
id: fleet.vehicle-defects
kind: register
title: Register of Vehicle Defects
structure: standard
path: registers/vehicle-defects.md

# A register carries no `satisfies:` — see fleet.vehicles for why.

requires: [fleet.vehicles, fleet.trip-inspection]

register:
  title: Register of Vehicle Defects
  note: >
    One row per defect reported, from wherever it came — a trip inspection, a
    driver noticing something in service, a periodic inspection, a maintenance
    service or a roadside inspection. Each row raises one repair decision, due
    24 hours after it was reported. `classification` is the column the whole
    regime turns on: a MAJOR defect means the vehicle must not be driven, and a
    minor one means it may continue. A row with no classification has not been
    decided about and is not a minor defect by default.
  columns:
    - {key: reference, label: Defect number, type: text, required: true}
    - {key: reported_on, label: Reported on, type: date, required: true}
    - {key: vehicle, label: Vehicle, type: relation, required: true,
       target: /registers/vehicles.md#records, display: unit_number}
    - {key: reported_by, label: Reported by, type: user, required: true}
    - {key: source, label: How it came to light, type: select, required: true,
       options: [Trip inspection, Driver report in service, Periodic inspection,
                 Preventive maintenance service, Roadside inspection,
                 Reported by another person, Other]}
    - {key: trip_inspection, label: Trip inspection report, type: relation,
       target: /registers/trip-inspections.md#records, display: reference}
    - {key: classification, label: Classification, type: select, required: true,
       options: ["Major — the vehicle must not be driven",
                 "Minor — the vehicle may continue in service",
                 Not yet classified]}
    - {key: system, label: System affected, type: select, required: true,
       options: [Brakes, Steering, Suspension, Tyres and wheels, Lighting and electrical,
                 Coupling devices, Frame and body, Cargo securement equipment,
                 Fuel system, Exhaust, Glass and mirrors, Emergency equipment, Other]}
    - {key: description, label: What was found, type: longtext, required: true}
    - {key: vehicle_out_of_service, label: Vehicle taken out of service, type: bool, required: true}
    - {key: out_of_service_at, label: Taken out of service on, type: date}
    - {key: status, label: Status, type: select, required: true,
       options: [Open, Repaired, "Deferred — minor and controlled", Not a defect]}
    - {key: closed_on, label: Closed on, type: date}
---

What this artifact must establish: every defect reported on a vehicle, what kind
of defect it was, and whether the vehicle kept moving.

It exists as a register of its own rather than as a column on the trip
inspection report for a reason worth stating, because it is the modelling
decision most likely to be undone by somebody tidying up. **Most trip
inspections find nothing.** If the repair obligation were triggered off the
inspection report, every clean inspection would raise a repair occurrence — a
fleet of thirty vehicles would generate seven thousand pieces of expected work a
year, all but a handful of them for nothing, and the few that mattered would be
invisible inside them. A defect register has one row per piece of actual work,
and each row raises exactly one decision.

**`classification` is prescribed, not a judgement.** Each of the regulation's
inspection schedules states which findings are major and which are minor. A
major defect means the driver stops: the vehicle must not be driven, the defect
is reported to the operator immediately, and the vehicle stays where it is until
it is repaired. A minor defect is recorded, reported, and the vehicle may
continue. An organisation that records defects without recording which kind they
were has kept the fact and thrown away the decision — and the decision is the
part the regulation is about. "Not yet classified" is an option because it is a
real and temporary state at the moment a driver phones in, and the alternative
is a guess recorded as a determination.

**`vehicle_out_of_service` is a separate column from `classification`, and the
gap between them is the finding.** A defect classified major on a vehicle that
was never taken out of service is not a paperwork discrepancy: it is a record
that the organisation knew the vehicle should not be driven and drove it. The
programme's daily watch is built to look for exactly that pair, and it can only
do so if the two facts are recorded separately.

`source` matters because a defect found by an enforcement officer at the
roadside is also an entry on the CVOR record, weighted by severity, and an
out-of-service order is among the heaviest. A defect the organisation found
itself is a functioning programme; the same defect found at a scale is a
functioning programme and an entry on the record, and the monthly review should
be able to tell what proportion of the year's defects the organisation is
finding for itself.

**`status` is not the same as whether a repair was done**, which is recorded
against the repair itself. This column is the register's own view of whether the
item is still live, so the daily watch can list what is open without opening
every repair record. "Deferred — minor and controlled" is an option because
deferring a minor defect is lawful and common, and an organisation with no way
to record a deliberate deferral will record it as closed.
