---
id: fleet.drivers
kind: register
title: Register of Commercial Drivers
structure: standard
path: registers/drivers.md

# A register carries no `satisfies:` — see fleet.vehicles for why.

requires: [fleet.policy]

register:
  title: Register of Commercial Drivers
  note: >
    One row per person the organisation dispatches in a commercial motor
    vehicle. The driver abstract review and the hours-of-service audit are both
    one occurrence per driver, raised from these rows, and the licence renewal
    is triggered off `licence_expires_on`. `hours_basis` and
    `operates_extra_provincially` are required because the two of them decide
    WHICH records this driver owes, and both are facts about how the person is
    actually dispatched rather than about the job title.
  columns:
    - {key: driver_id, label: Driver number, type: text, required: true}
    - {key: name, label: Name, type: text, required: true}
    - {key: person, label: Person, type: user}
    - {key: licence_number, label: Licence number, type: text, required: true}
    - {key: licence_class, label: Licence class, type: select, required: true,
       options: ["A", "AZ", "AR", "D", "DZ", "B", "C", "E", "F", "G", "GZ", Other]}
    - {key: air_brake_z, label: Air brake (Z) endorsement held, type: bool, required: true}
    - {key: licence_expires_on, label: Licence expires on, type: date, required: true}
    - {key: licence_verified_on, label: Last verified against the Ministry record, type: date}
    - {key: medical_due_on, label: Next medical due, type: date}
    - {key: hours_basis, label: How this driver's hours are recorded, type: select, required: true,
       options: ["Daily log",
                 "160 km radius exemption — time record kept by the operator",
                 "Not subject to hours of service",
                 Not yet determined]}
    - {key: cycle, label: Cycle, type: select, required: true,
       options: ["Cycle 1 — 70 hours in 7 days", "Cycle 2 — 120 hours in 14 days",
                 Not applicable, Not yet determined]}
    - {key: operates_extra_provincially, label: Crosses a provincial or international boundary, type: select, required: true,
       options: ["No — Ontario only", "Occasionally", "Regularly", Not yet determined]}
    - {key: home_terminal, label: Home terminal, type: text, required: true}
    - {key: vehicles_authorised, label: Vehicles this driver may be assigned, type: longtext}
    - {key: hired_on, label: Driving for the organisation from, type: date, required: true}
    - {key: left_on, label: Stopped driving on, type: date}
    - {key: abstract_last_obtained_on, label: Abstract last obtained on, type: date}
---

What this artifact must establish: who the organisation dispatches in a
commercial motor vehicle, what each of them is licensed to drive, and — the two
facts that decide what records the organisation owes for them — how their hours
are recorded and whether they leave the province.

**A licence class alone does not authorise a vehicle.** Class A covers a
combination whose towed vehicle exceeds 4,600 kg; Class D covers a truck
exceeding 11,000 kg gross weight, or a combination whose towed vehicle does not.
Independently of either, a vehicle equipped with air brakes may be driven only
by a person whose licence carries the **Z** endorsement. This is where a
contractor's fleet most often comes unstuck, because the endorsement is not
visible in the class name a dispatcher has in their head and a Class G driver
moving a tandem with air brakes is wrong twice over. `air_brake_z` is therefore
its own required column and not something to be read out of `licence_class`, and
`vehicles_authorised` exists so the match between person and machine is written
down rather than assumed at six in the morning.

**`licence_verified_on` is a different fact from `licence_expires_on`.**
Verifying a licence from the driver's card establishes what the card said on the
day it was printed. Verifying it from the Ministry's record establishes what the
licence is today — and between those two lie a downgrade for a missed medical
and a suspension for accumulated demerit points, neither of which changes the
plastic in the driver's wallet. The date in this column is the date somebody
looked at the Ministry's record.

**`hours_basis` is a status recorded per driver and tested per day.** Most
construction fleets operate under the 160 km radius exemption, and the exemption
is conditional day by day: it holds only where the driver stayed within the
radius, returned to the home terminal to begin at least eight consecutive hours
off duty, and the operator kept an accurate and legible time record. A driver
marked exempt here is a driver whose exemption the monthly audit must actually
check — `fleet.hours-of-service` records whether the conditions held, and a
single day outside the radius is a day that required a log.

**`operates_extra_provincially` is the column that keeps the federal and
provincial halves apart.** An Ontario carrier's certificate is the same piece of
paper whether or not it crosses a boundary, so nothing announces the transition.
A driver who runs into Quebec twice a year is under the federal *Commercial
Vehicle Drivers Hours of Service Regulations* for those trips, and the federal
electronic logging device requirement follows the federal instrument. "Not yet
determined" is a real and temporary state and is an option, because a boolean
would force a guess to be recorded as a decision.

`left_on` closes the window. A driver who has gone should stop having monthly
hours audits raised against them, and a register with no leaving date cannot say
so. It is also the start of the retention clock for anything kept from the point
the employment ended.

**Nothing in this register is a competency judgement**, and it must not become
one. Whether somebody is a good driver is a matter for the collision review and
for whatever the organisation does about it. This register records what the
person is *licensed* to do, and confusing the two produces a document a driver
will reasonably grieve.
