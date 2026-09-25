---
id: fleet.hours-of-service
kind: procedure
title: Hours of Service
structure: procedure
path: procedures/hours-of-service.md

satisfies:
  - hta_ontario:HTA-HOS-01
  - hta_ontario:HTA-HOS-02
  - hta_ontario:HTA-HOS-03
  - hta_ontario:HTA-HOS-04
  - hta_ontario:HTA-HOS-05
  - hta_ontario:HTA-HOS-06
  - hta_ontario:HTA-HOS-07
  - hta_ontario:HTA-CVOR-03
  - mvta_canada:CVDHS-01
  - mvta_canada:CVDHS-02
  - mvta_canada:CVDHS-03
  - mvta_canada:CVDHS-04
  - mvta_canada:CVDHS-05
  - mvta_canada:CVDHS-07
  - mvta_canada:CVDHS-08
  - mvta_canada:CVDHS-09
  - mvta_canada:CVDHS-10
  - mvta_canada:CVDHS-11
  - nsc_ca:NSC-09

requires: [fleet.policy, fleet.drivers]

declares:
  obligation:
    id: fleet.hours-audit
    activity: Audit the driver's hours records for the period against the limits, on whichever basis actually applied
    cadence: each month
    authority: >
      O. Reg. 555/06 s. 30 and the federal Commercial Vehicle Drivers Hours of
      Service Regulations — the operator must monitor its drivers' compliance
      and must not request, require or allow a contravention. Both instruments
      impose the duty to monitor and NEITHER sets an interval for it. The month
      is this organisation's, chosen against the six-month retention of the
      records being audited and against the fourteen-day window a driver must
      carry: a quarterly audit reads records that are half gone and finds
      breaches nobody can still ask the driver about.
    interval_basis: chosen
    responsible: fleet-manager
    applies_to: the organisation
    per:
      listed_in: registers/drivers.md
      key: driver_id
      label: name
      from: hired_on
      until: left_on
    records: registers/hours-of-service-audits.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - hta_ontario:HTA-HOS-07
      - mvta_canada:CVDHS-07
      - mvta_canada:CVDHS-11
      - nsc_ca:NSC-09
  register:
    title: Hours of Service Audit Record
    note: >
      One row per driver per month. `basis_applied` is asked here as well as on
      the driver register because the exemption is CONDITIONAL DAY BY DAY and
      not a status a driver holds: what the register records is how this driver
      is normally dispatched, and what this audit records is what actually
      happened in the period. `days_requiring_a_log_without_one` is therefore
      separate from every limit breach — it is the count of days on which the
      exemption did not hold and no log exists, which is a records failure
      rather than an hours one, and an audit that merged them would report a
      clean month for a fleet that had been outside the radius all of it.
    layout: form
    review: required
    approvers: [fleet-manager]
    columns:
      - {key: driver, label: Driver, type: relation, required: true,
         target: /registers/drivers.md#records, display: driver_id}
      - {key: period_start, label: Period from, type: date, required: true}
      - {key: period_end, label: Period to, type: date, required: true}
      - {key: audited_on, label: Audited on, type: date, required: true}
      - {key: audited_by, label: Audited by, type: user, required: true}
      - {key: instrument, label: Which regulation governed the period, type: select, required: true,
         options: ["Ontario — O. Reg. 555/06 throughout",
                   "Federal — SOR/2005-313 throughout",
                   "Both — some trips crossed a boundary",
                   Not yet determined]}
      - {key: basis_applied, label: How this driver's hours were actually recorded, type: select, required: true,
         options: ["Daily logs throughout",
                   "160 km radius exemption throughout — operator time records",
                   "Mixed — logs on some days, the exemption on others",
                   "Nothing was kept", Not yet determined]}
      - {key: days_worked, label: Days worked in the period, type: int, required: true}
      - {key: records_obtained, label: Days for which a record was obtained, type: int, required: true}
      - {key: exemption_conditions_held, label: On every exempt day the driver stayed inside 160 km and returned to the home terminal for 8 consecutive hours off, type: select, required: true,
         options: ["Yes — on every exempt day", "No — named days are listed below",
                   "Not applicable — no exempt days", Not yet determined]}
      - {key: time_record_adequate, label: The operator's time record shows on-duty times and the hour each duty status began and ended, type: bool, required: true}
      - {key: days_requiring_a_log_without_one, label: Days that required a log and have none, type: int, required: true}
      - {key: days_outside_radius, label: Days on which the driver went outside the radius, type: longtext}
      - {key: driving_limit_breaches, label: Days over 13 hours driving, type: int, required: true}
      - {key: on_duty_limit_breaches, label: Days over 14 hours on duty, type: int, required: true}
      - {key: elapsed_16_breaches, label: Days driven after 16 hours elapsed, type: int, required: true}
      - {key: off_duty_breaches, label: Days without 10 hours off, 8 of them consecutive, type: int, required: true}
      - {key: cycle_breaches, label: Cycle limit breaches, type: int, required: true}
      - {key: cycle_resets_taken, label: Cycle resets taken in the period, type: int}
      - {key: eld_used, label: An electronic logging device was in use, type: bool, required: true}
      - {key: dispatch_contributed, label: Dispatch contributed to a breach, type: select, required: true,
         options: ["No", "Yes — a trip could not be completed within the remaining hours",
                   "Yes — other, described below", Not yet determined]}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: actions, label: Actions, with owners and dates, type: longtext}
      - {key: driver_spoken_to, label: The driver was spoken to about the findings, type: bool, required: true}
    retention:
      keep: 6m
      authority: >
        O. Reg. 555/06 and SOR/2005-313 — the operator keeps daily logs, time
        records and supporting documents for six months. This audit is the
        operator's own record of having looked at them and is kept on the same
        clock so that the audit and the records it read expire together.
      reason: An audit surviving the records it examined cannot be checked; records surviving no audit cannot show the operator monitored anything.
---

What this document must establish for THIS organisation: which of its drivers
are inside the hours regime, on what basis each day's hours are recorded, and
who actually reads them.

**The limits are the same on both sides of the federal line, and the instrument
is not.** Thirteen hours driving, fourteen hours on duty, sixteen hours elapsed
since coming on duty after eight consecutive off, ten hours off a day with
eight of them consecutive, twenty-four consecutive hours off in fourteen days,
and a cycle of seventy hours in seven days or one hundred and twenty in
fourteen. Ontario's O. Reg. 555/06 governs intra-provincial operation; the
federal *Commercial Vehicle Drivers Hours of Service Regulations* govern a
driver on a trip that crosses a provincial, territorial or international
boundary. Nothing goes visibly wrong until somebody asks which regulation the
record was kept under, and by then the answer is fixed. The procedure must say
which trips cross a boundary and what changes for them — including the federal
**electronic logging device** requirement, which follows the federal
instrument and which Ontario does not impose for intra-provincial work.

**The three daily limits run at once and the first one reached stops the
driver.** On-duty time is everything that is not off-duty time: loading,
unloading, waiting, inspecting, fuelling, repairing, and work for anybody else.
A contractor's driver who spent six hours on a machine and four driving has
spent ten hours on duty, and a procedure that talks only about driving time has
described a third of the rule.

**The cycle does not reset because the week ended.** It resets only when the
driver takes the consecutive off-duty time that resets it — thirty-six hours for
Cycle 1, seventy-two for Cycle 2. A payroll week closing, a pay period ending or
a move to a different vehicle reset nothing, and this is the misunderstanding
that produces a driver in breach on a Monday with everybody satisfied.

## The 160 km radius exemption, which is how this fleet probably operates

A driver need not fill out a daily log where **all three** of these hold: the
driver operates within a radius of 160 km of the home terminal, returns to the
home terminal to begin at least eight consecutive hours off duty, and **the
operator keeps accurate and legible records showing the driver's on-duty times
and the hour at which each duty status began and ended**.

Three things about it decide whether this organisation is actually inside it,
and every one of them must be in the document:

1. **It exempts the log and nothing else.** Every driving, on-duty, off-duty
   and cycle limit continues to apply in full, and the operator must still be
   able to show they were met.
2. **It is conditional day by day, not a status a driver holds.** One trip
   beyond the radius, or one night not spent at the home terminal, means *that
   day* required a log. A driver marked "log exempt" on a spreadsheet is a
   driver nobody is checking.
3. **The time record is a condition of the exemption, not an alternative to
   record-keeping.** An operator keeping no time record has not used the
   exemption — it has no hours records at all, which is a worse position than
   having imperfect logs.

The procedure must therefore describe the time record the organisation actually
keeps, name where it comes from — a timesheet, a dispatch sheet, a telematics
export — and confirm that it shows the **hour each duty status began and
ended** rather than a daily total. A payroll timesheet showing "9.5 hours" does
not satisfy the condition, and it is the commonest thing an operator offers when
asked.

## What the audit is, and why collecting is not monitoring

**The operator's duty is to monitor, and it cannot be discharged by
collecting.** A shelf of logs nobody read is a shelf of evidence against the
organisation: the records exist, the breaches are in them, and the operator was
answerable for looking. This audit is the act of looking, and its record is what
makes it demonstrable.

**It must also reach dispatch.** The operator must not request, require or
allow a driver to contravene the regulation, and the contravention occurs at the
moment a trip is assigned that cannot be completed within the driver's remaining
hours. `dispatch_contributed` is a required field because an audit that only
finds driver breaches turns a company decision into a personnel matter.

**The monthly interval is this organisation's** and the document should say so.
The records are kept for six months and a driver carries the current log and
the preceding fourteen days; an audit spaced further apart than that is reading
a period nobody can still explain.

**And a fleet whose vehicles are all below the threshold is outside this
entirely.** The regime is keyed to the commercial motor vehicle. Building hours
records nobody owes is not caution; it is a month of expected work that will
never be done.
