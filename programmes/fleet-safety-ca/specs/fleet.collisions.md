---
id: fleet.collisions
kind: register
title: Register of Collisions
structure: standard
path: registers/collisions.md

# A register carries no `satisfies:` — see fleet.vehicles for why.

requires: [fleet.vehicles, fleet.drivers]

register:
  title: Register of Collisions
  note: >
    One row per collision involving a vehicle the organisation operates,
    reportable or not. Each row raises one collision review, due 14 days after
    it occurred. Near misses and minor yard contacts belong here too: a register
    holding only the collisions that were reported to police records the events
    the organisation could no longer conceal, which is the smallest and latest
    slice of what it could have learned.
  columns:
    - {key: reference, label: Collision number, type: text, required: true}
    - {key: occurred_on, label: Occurred on, type: date, required: true}
    - {key: vehicle, label: Vehicle, type: relation, required: true,
       target: /registers/vehicles.md#records, display: unit_number}
    - {key: driver, label: Driver, type: relation, required: true,
       target: /registers/drivers.md#records, display: driver_id}
    - {key: location, label: Location, type: text, required: true}
    - {key: severity, label: Severity, type: select, required: true,
       options: [Fatality, Personal injury, Property damage only,
                 "Yard or off-highway contact", "Near miss — no contact"]}
    - {key: reportable, label: Reportable to police, type: select, required: true,
       options: ["Reported to police", "Below the reporting threshold",
                 "Not yet determined"]}
    - {key: police_report_number, label: Police report number, type: text}
    - {key: injuries, label: People injured, type: int, required: true}
    - {key: fatalities, label: Fatalities, type: int, required: true}
    - {key: third_party_involved, label: Another party involved, type: bool, required: true}
    - {key: cargo_involved, label: Cargo shifted, spilled or was lost, type: bool, required: true}
    - {key: estimated_damage, label: Estimated damage, type: currency}
    - {key: vehicle_towed, label: A vehicle had to be towed, type: bool, required: true}
    - {key: expected_on_cvor, label: Expected on the CVOR record, type: select, required: true,
       options: ["Expected to appear", "Not expected to appear",
                 "Confirmed on the abstract", "Not yet determined"]}
    - {key: description, label: What happened, type: longtext, required: true}
    - {key: wsib_claim, label: A workplace injury claim arose, type: bool}
---

What this artifact must establish: every collision a vehicle of the
organisation's was involved in, with enough recorded at the time that somebody
can review it two weeks later.

**It is here because a collision is one of the four things that lands on the
CVOR record.** A reportable collision is weighted and counted against the
operator's violation rate whether or not the driver was at fault, and it stays
on the record for a fixed period. The organisation cannot argue with it after
the fact; what it can do is know about every one of them, review them, and be
able to say what changed. `expected_on_cvor` is a select with four options
because at the moment of recording nobody knows, and the abstract review is
where the expectation is confirmed against the Ministry's actual record — an
entry appearing that the organisation had not expected is itself a finding,
usually about a driver who did not report something.

**Near misses and yard contacts are in the same register as fatalities, and that
is deliberate.** They have the same causes and a hundredth of the cost, and a
register that starts at the police reporting threshold is a register of the
events that were too large to absorb quietly.

`driver` and `vehicle` are relations rather than typed-in text. Every question
the organisation is actually asked about collisions is a join — which driver,
how many this year, which unit, whether the same intersection — and "Hwy 401",
"401" and "hwy401" are three locations to a machine. A free-text field cannot
answer any of it, and the monthly review depends on being able to.

`cargo_involved` is a separate column because a load that shifted, spilled or
came off is simultaneously a collision and a securement failure, and the review
has to reach the securement practice rather than stopping at the driving.

**This register records what happened. It does not record who was at fault.**
Preventability is a determination made in `fleet.collision-review`, after
somebody has looked, and it belongs there rather than in a field filled in at
the roadside by the person most exposed by the answer. The one exception is the
facts that are simply facts — injuries, fatalities, whether a vehicle was towed —
and those are here because they decide how urgently the review is done and
because nobody can reconstruct them later.
