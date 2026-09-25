---
id: fleet.compliance-review
kind: procedure
title: Fleet Compliance Review
structure: procedure
path: procedures/fleet-compliance-review.md

satisfies:
  - hta_ontario:HTA-CVOR-03
  - hta_ontario:HTA-CVOR-05
  - hta_ontario:HTA-HOS-07
  - hta_ontario:HTA-TRIP-06
  - hta_ontario:HTA-PMVI-03
  - nsc_ca:NSC-14
  - nsc_ca:NSC-15
  - cor_2020:COR-02
  - cor_2020:COR-18
  - iso_45001:9.1.2
  - iso_45001:9.3

requires: [fleet.policy, fleet.cvor]

declares:
  obligation:
    id: fleet.compliance-review
    activity: Review of the fleet programme as a whole — what is open, what is late, and what the records are showing
    cadence: each month
    authority: >
      Nothing requires this review and nothing sets its interval. It exists
      because a facility audit under National Safety Code Standard 15 examines
      the operator's own records rather than its vehicles, and the finding that
      decides its outcome is usually an absence. The month is this
      organisation's, chosen so that the sweep runs inside the six-month
      retention of the hours and trip-inspection records it reads, and so that
      an open major defect or an unclosed collision action cannot age past a
      quarter unseen.
    interval_basis: chosen
    responsible: fleet-manager
    applies_to: the organisation
    records: registers/fleet-compliance-reviews.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - nsc_ca:NSC-15
      - cor_2020:COR-02
      - iso_45001:9.1.2
  register:
    title: Fleet Compliance Review Record
    note: >
      One row per monthly review. Every count here is asked as a pair — what was
      expected and what exists — because a single number cannot distinguish a
      quiet month from a month nobody recorded. `registers_unreadable` is
      required and is the most important field in the register: a review that
      could not read a source has refuted nothing, and reporting that as a clean
      month is worse than reporting nothing at all.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: period_start, label: Period from, type: date, required: true}
      - {key: period_end, label: Period to, type: date, required: true}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: vehicles_in_service, label: Vehicles in service, type: int, required: true}
      - {key: drivers_active, label: Drivers active, type: int, required: true}
      - {key: trip_inspections_expected, label: Trip inspections expected, type: int, required: true}
      - {key: trip_inspections_recorded, label: Trip inspections recorded, type: int, required: true}
      - {key: defects_open, label: Defects open at the end of the period, type: int, required: true}
      - {key: major_defects_open, label: Of those, classified major, type: int, required: true}
      - {key: defects_unclassified, label: Defects with no classification, type: int, required: true}
      - {key: vehicles_moved_with_open_major, label: Vehicles that moved with an open major defect, type: int, required: true}
      - {key: defects_found_by_us, label: Defects the organisation found itself, type: int, required: true}
      - {key: defects_found_at_roadside, label: Defects found at a roadside inspection, type: int, required: true}
      - {key: repairs_overdue, label: Repair decisions past their deadline, type: int, required: true}
      - {key: hours_audits_expected, label: Hours audits expected, type: int, required: true}
      - {key: hours_audits_done, label: Hours audits done, type: int, required: true}
      - {key: days_requiring_a_log_without_one, label: Days that required a log and had none, type: int, required: true}
      - {key: licences_lapsed, label: Licences or medicals lapsed, type: int, required: true}
      - {key: stickers_lapsed, label: Periodic inspection stickers lapsed, type: int, required: true}
      - {key: maintenance_overdue, label: Maintenance services overdue, type: int, required: true}
      - {key: collisions_in_period, label: Collisions in the period, type: int, required: true}
      - {key: collision_reviews_overdue, label: Collision reviews past their deadline, type: int, required: true}
      - {key: open_actions_from_reviews, label: Open actions from collision reviews and audits, type: longtext, required: true}
      - {key: cvor_position, label: CVOR position at the last abstract, type: text, required: true}
      - {key: registers_unreadable, label: Registers that could not be read, and why, type: longtext, required: true}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: actions, label: Actions, with owners and dates, type: longtext, required: true}
      - {key: escalated_to_management, label: Escalated to senior management, type: bool, required: true}
    retention:
      keep: 2y
      authority: >
        No retention period is prescribed. Two years is this organisation's, set
        to cover the period a facility audit reviews over, so that the audit can
        be answered with the organisation's own monthly account of the same
        period.
      reason: A facility audit's finding is usually an absence; a monthly record of having looked is the only thing that answers it in advance.
---

What this document must establish for THIS organisation: who reads the whole
programme once a month, what is put in front of them, and what has to come out
of it.

**This is where the record-origin chains stop.** A defect raises a repair
decision; a collision raises a review. Both of those could go on raising work
forever, and a chain of triggers has to terminate in something periodic or the
last link is never swept. Everything still open and everything still late
arrives here, which is why this obligation has a cadence and not a trigger.

**A facility audit examines records, not vehicles, and the finding that decides
its outcome is usually an absence.** A month in which nothing was recorded and a
month in which nothing happened are the same shape from outside, so every count
in this register is a pair — expected against actual. A review that reports
"twelve trip inspections" has said nothing; one that reports "twelve of an
expected six hundred and sixty" has said everything.

**The finding this review exists to produce is a vehicle that moved when it
should not have.** A defect classified major on a vehicle still appearing on
trip inspections after the date it was reported is not a paperwork discrepancy:
it is a record that the organisation knew and drove anyway. It is named first on
the form for that reason, and the procedure must say what happens the day it is
found rather than at the next monthly meeting.

**Where the defects are coming from is a measure of the programme, not of the
fleet.** A defect the organisation found itself is a functioning trip
inspection. The same defect found at a scale is a functioning trip inspection
that nobody did, plus an entry on the CVOR record. The ratio between the two is
the most honest single number in this programme and it is why both are counted.

**Unclassified defects are counted separately from open ones.** A defect with
no classification has not been decided about, and it is not a minor one by
default. An organisation whose unclassified count is rising has a reporting
route that works and a decision route that does not.

**It must say what could not be read.** `registers_unreadable` is required
because a check that could not parse its source has refuted nothing, and an
empty result reported as a clean one is the failure mode that destroys
confidence in every other number on the page. A confident zero is worse than an
honest gap.

**This is a compliance review and not the management review.** Its audience is
the person who runs the fleet, monthly, in operational terms. Where it produces
something the fleet manager cannot resolve — a vehicle that has to come off the
road, a driver who has to stop driving, money for maintenance the schedule will
not absorb — it escalates, and `escalated_to_management` records that it did.

**And it feeds the policy review.** The annual policy review asks whether this
organisation is still the organisation the policy describes. Twelve of these are
the evidence for that answer.
