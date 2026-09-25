---
id: fleet.vehicles
kind: register
title: Register of Commercial Motor Vehicles
structure: standard
path: registers/vehicles.md

# A register carries no `satisfies:`.
#
# It is the evidence that work happened, not the document that answers a
# control. `implements` onto a control may be asserted by a blueprint, a policy
# or a procedure and by nothing else, so a register citing one would sit at
# `present_uncited` permanently and cap the tier's readiness at a number no
# amount of work could move. The citation belongs on the procedure that declares
# this register.

requires: [fleet.policy]

register:
  title: Register of Commercial Motor Vehicles
  note: >
    One row per commercial motor vehicle the organisation operates. This is the
    spine of the programme: the trip inspection, the periodic inspection, the
    securement check and the maintenance service are all one occurrence per
    vehicle, raised from these rows. `in_service_on` and `out_of_service_on` are
    the window a vehicle is expected to have work done in, so a unit sold in
    March stops being expected in April rather than accruing gaps forever.
    `cvor_vehicle` is required and is not decoration — see the brief. A vehicle
    that does not belong on the CVOR fleet does not belong in this register.
  columns:
    - {key: unit_number, label: Unit number, type: text, required: true}
    - {key: description, label: Make, model and year, type: text, required: true}
    - {key: vehicle_type, label: Type, type: select, required: true,
       options: [Truck — single unit, Truck tractor, Trailer, Dump truck,
                 Float or lowbed trailer, Boom or picker truck, Tow truck,
                 Bus, Other]}
    - {key: plate, label: Plate, type: text, required: true}
    - {key: vin, label: Vehicle identification number, type: text, required: true}
    - {key: registered_gross_weight_kg, label: Registered gross weight (kg), type: int, required: true}
    - {key: cvor_vehicle, label: Counted on the CVOR fleet, type: bool, required: true}
    - {key: air_brakes, label: Equipped with air brakes, type: bool, required: true}
    - {key: inspection_schedule, label: Trip inspection schedule that applies, type: select, required: true,
       options: ["Schedule 1 — trucks, tractors and trailers",
                 "Schedule 2 — buses",
                 "Schedule 3 — school purposes vehicles",
                 "Schedule 4 — motor coaches",
                 Not yet determined]}
    - {key: home_terminal, label: Home terminal, type: text, required: true}
    - {key: in_service_on, label: In service from, type: date, required: true}
    - {key: out_of_service_on, label: Out of service from, type: date}
    - {key: inspection_expires_on, label: Periodic inspection sticker expires on, type: date, required: true}
    - {key: inspection_interval, label: Periodic inspection interval, type: select, required: true,
       options: [12 months, 6 months, Not yet determined]}
    - {key: maintenance_interval, label: Maintenance interval set for this vehicle, type: text}
    - {key: ownership, label: Held as, type: select, required: true,
       options: [Owned, Leased — long term, Leased or rented — short term,
                 Owner-operator, Subcontractor's vehicle]}
    - {key: operator_of_record, label: Operator of record, type: text, required: true}
---

What this artifact must establish: which vehicles the organisation is the
**operator** of, which of them count on its CVOR fleet, and the handful of facts
that decide what each one owes.

**The boundary of this register is the most consequential decision in the
programme.** It holds commercial motor vehicles: a truck, or a truck and trailer
combination, with a registered gross weight or an actual weight of more than
4,500 kg — plus buses, which are caught by seating capacity rather than weight,
and tow trucks, which are caught regardless of either. A pickup, a van or a car
below that weight is not one, and putting it in here is not caution. Every row
in this register raises a daily trip inspection, a quarterly securement check, a
quarterly maintenance service and an annual periodic inspection. Thirty pickups
added "to be safe" manufacture roughly eleven thousand expected records a year
that no instrument asks for and that nobody will produce, and the readiness
number that results is wrong in the discouraging direction for as long as the
rows are there.

`cvor_vehicle` is a separate required column from the weight because the two
questions are not identical and both are needed. The weight decides whether the
vehicle is a commercial motor vehicle; the CVOR fleet count is a figure declared
to the Ministry and is the **denominator of the violation rate**. A company that
has grown and not updated the declared count is being measured against an
exposure it no longer has.

`operator_of_record` and `ownership` exist because the operator is not always
the registered owner. A vehicle held under a lease may be the lessee's
responsibility; an owner-operator's truck may be on the organisation's CVOR or
on the owner-operator's own. Getting it wrong does not produce a gap — it
produces **the wrong company's record accumulating the events**, which is
discovered at the point somebody reads an abstract and cannot account for what
is on it. The organisation must record, for each vehicle, who is answerable for
it, and the procedure that declares this register must say how that is
determined from the lease rather than from habit.

`inspection_schedule` is a column and not an inference. O. Reg. 199/07
prescribes the trip inspection schedules by vehicle type, and the schedule must
be carried in the vehicle. A driver inspecting a trailer against a bus schedule
has produced a thorough report about the wrong components.

`inspection_interval` is separate from `inspection_expires_on` for the same
reason: a truck's sticker runs twelve months and a bus is on a shorter cycle, so
the interval is a property of the vehicle rather than something derived from the
last date.

**`out_of_service_on` is not decoration.** A vehicle that has been sold,
written off or parked is a vehicle that should stop raising daily inspections,
and a register with no closing column cannot say so. It also means the
obligations know a vehicle's *life*: a unit that ran until the 28th of a month
owed that month's work, and judging liveness at the moment a record was due
would write off the last period of every vehicle the organisation ever ran.
