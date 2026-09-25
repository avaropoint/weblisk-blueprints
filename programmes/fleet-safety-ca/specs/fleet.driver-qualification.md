---
id: fleet.driver-qualification
kind: procedure
title: Driver Qualification and the Driver File
structure: procedure
path: procedures/driver-qualification.md

satisfies:
  - hta_ontario:HTA-DRIVER-01
  - hta_ontario:HTA-DRIVER-02
  - hta_ontario:HTA-DRIVER-03
  - hta_ontario:HTA-DRIVER-04
  - hta_ontario:HTA-CVOR-03
  - nsc_ca:NSC-04
  - nsc_ca:NSC-06
  - nsc_ca:NSC-07
  - cor_2020:COR-16
  - iso_45001:7.2

requires: [fleet.policy, fleet.drivers]

declares:
  obligation:
    id: fleet.driver-abstract-review
    activity: Obtain the driver's abstract with their authorisation, verify the licence class and endorsements, and review the driver file
    cadence: each year
    authority: >
      National Safety Code Standard 7 expects a carrier to maintain a profile
      for each of its drivers, and the Highway Traffic Act makes the operator
      answerable for the conduct of the drivers of its commercial motor
      vehicles. Neither requires a periodic abstract and neither sets an
      interval. The year is this organisation's, chosen because a licence is
      renewed on a multi-year cycle while a suspension, a downgrade for a missed
      medical and an accumulation of demerit points all happen between renewals
      and change nothing about the card in the driver's wallet.
    interval_basis: chosen
    responsible: fleet-manager
    applies_to: the organisation
    per:
      listed_in: registers/drivers.md
      key: driver_id
      label: name
      from: hired_on
      until: left_on
    records: registers/driver-abstract-reviews.md
    escalate: {after: 4w, to: senior-management}
    satisfies:
      - hta_ontario:HTA-DRIVER-03
      - hta_ontario:HTA-DRIVER-04
      - nsc_ca:NSC-07
  register:
    title: Driver Abstract Review Record
    note: >
      One row per driver per year. `licence_status_on_abstract` is what the
      MINISTRY says the licence is, and it is a different fact from the class
      written on the card the driver produced; where the two disagree, this
      register is where the disagreement is recorded and dated. The review also
      answers a question nobody else asks — whether the vehicles this driver is
      actually dispatched in match the class and endorsement they hold.
    layout: form
    review: required
    approvers: [fleet-manager]
    columns:
      - {key: driver, label: Driver, type: relation, required: true,
         target: /registers/drivers.md#records, display: driver_id}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: authorisation_held, label: The driver's written authorisation to obtain the abstract is held, type: bool, required: true}
      - {key: abstract_obtained_on, label: Abstract obtained on, type: date, required: true}
      - {key: abstract_type, label: Kind of abstract, type: select, required: true,
         options: ["Driver's licence abstract", "Commercial driver's abstract (3-year)",
                   "Driver's licence history", Other]}
      - {key: licence_status_on_abstract, label: Licence status on the Ministry's record, type: select, required: true,
         options: [Valid, "Valid — conditions or restrictions", Downgraded,
                   Suspended, Expired, Not yet determined]}
      - {key: class_on_abstract, label: Class shown on the Ministry's record, type: text, required: true}
      - {key: air_brake_on_abstract, label: Air brake (Z) endorsement on the Ministry's record, type: bool, required: true}
      - {key: matches_register, label: The register matches the Ministry's record, type: bool, required: true}
      - {key: discrepancy, label: Where they disagree, and what was done, type: longtext}
      - {key: convictions_since_last, label: Convictions since the last review, type: int, required: true}
      - {key: demerit_points, label: Demerit points, type: int, required: true}
      - {key: medical_status, label: Medical, type: select, required: true,
         options: ["Current", "Due inside 90 days", "Overdue — licence at risk",
                   "Not applicable to this class", Not yet determined]}
      - {key: vehicles_dispatched_in, label: Vehicles this driver was actually dispatched in, type: longtext, required: true}
      - {key: authorised_for_those_vehicles, label: The licence and endorsements cover every one of them, type: bool, required: true}
      - {key: collisions_since_last, label: Collisions since the last review, type: int, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: ["Continues to drive", "Continues, with conditions or training",
                   "Restricted to particular vehicles", "Removed from driving duties",
                   Not yet determined]}
      - {key: actions, label: Actions, with owners and dates, type: longtext}
      - {key: next_review, label: Next review due, type: date}
    retention:
      keep: 2y
      authority: >
        No retention period is prescribed for a carrier's driver file in
        Ontario. Two years is this organisation's, set to cover a facility
        audit's review period and to run past the end of an employment.
      reason: A driver abstract carries personal information; keeping it longer than it is needed is its own exposure.
---

What this document must establish for THIS organisation: how somebody becomes
authorised to drive one of its commercial vehicles, what is kept on file about
them, and what is looked at on a cycle.

**Checking the card is not checking the licence.** Verifying from the driver's
plastic establishes what the card said on the day it was printed. Verifying from
the Ministry's record establishes what the licence is today — and between the
two lie a downgrade for a missed medical and a suspension for accumulated
demerit points, neither of which changes the card. This is where a suspended
driver keeps working, and it is the single most valuable thing this procedure
does.

**The abstract needs the driver's authorisation, and that is a step with a
record.** The procedure must say how consent is obtained, how often it is
renewed, and where it is held — and it must say what happens when a driver
declines, because "we did not check" and "they would not let us" are different
positions and only one of them is answerable.

**The class alone does not authorise the vehicle.** Class A covers a
combination whose towed vehicle exceeds 4,600 kg; Class D covers a truck over
11,000 kg or a combination whose towed vehicle does not exceed 4,600 kg;
independently of either, a vehicle with air brakes may be driven only by a
driver holding the **Z** endorsement. The review must compare the licence
against the vehicles the driver was **actually dispatched in**, which is why
that is a required field. Checking a licence in the abstract and never against
the dispatch record finds the expired licence and misses the Class G driver in
a tandem with air brakes.

**Medical fitness is between the driver and the Ministry, and its consequence
lands on the operator.** A commercial class carries a medical examination on a
cycle set by age, and a medical not submitted results in a downgrade or a
suspension. The operator cannot file it and cannot chase the Ministry; what it
can do is know the date and know the status, which is what the register's
`medical_status` is for.

**Demerit points are a trend, not an outcome.** The same convictions that
accumulate against a driver's licence are weighted onto the operator's own CVOR
record, so a driver approaching a suspension is simultaneously moving the
company toward an intervention. An operator that tracks only whether a licence
is currently valid is watching the result and not the trend, and the procedure
should say what point on that trend triggers a conversation.

**The driver file is a personnel record and must be handled as one.** An
abstract contains personal information about convictions and health; the
procedure must say who may see it, where it is kept, and that the outcome
reaching a dispatcher is "may drive units 12 and 14" rather than the abstract
itself.

**This is a qualification review and not a performance appraisal.** Whether
somebody is a good driver is a matter for the collision review and for whatever
the organisation does about it. Mixing the two produces a document a driver will
reasonably grieve, and an abstract used as evidence in a discipline the driver
never consented to it being used for.

**Entry-level training is not the carrier's duty and should not be claimed as
one.** Mandatory Entry Level Training is a licensing condition administered
between the driver and the Ministry. What belongs here is recording that the
class was obtained, not asserting the organisation delivered the training.
