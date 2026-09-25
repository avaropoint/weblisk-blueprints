---
id: cenv.compliance-review
kind: procedure
title: Environmental Compliance Review
structure: procedure
path: procedures/environmental-compliance-review.md

satisfies:
  - epa_ontario:14
  - o_reg_406_19:28
  - o_reg_406_19:22

requires:
  - cenv.policy
  - cenv.excavation-projects
  - cenv.excess-soil-registry
  - cenv.registry-closeout
  - cenv.soil-hauling
  - cenv.contaminated-soil-response
  - cenv.spill-reporting
  - cenv.approvals-determination
  - cenv.approval-conditions
  - cenv.approval-renewal

declares:
  obligation:
    id: cenv.compliance-review
    activity: Every open determination, notice, observation, incident and instrument read across the whole organisation, and what is open and late named
    cadence: each quarter
    authority: >
      No instrument requires this review. O. Reg. 406/19 s. 28 makes the
      organisation answerable for records it must be able to produce for seven
      years, and Environmental Protection Act s. 14 makes it answerable for a
      discharge it caused or permitted — neither sets a review interval, and
      neither contemplates one. Each quarter is this organisation's, chosen
      because it is the shortest cycle at which the thing this review is for
      shows up: not a late record, which the due sweep already finds, but a
      pattern of late records that says a determination is being made by whoever
      is standing there
    interval_basis: chosen
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/environmental-compliance-reviews.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Environmental Compliance Review
    note: >
      One row per quarter, for the whole organisation. The counts are integers
      rather than a narrative because the value of this record is in comparing
      it with the last one: three project areas with an outstanding determination
      is a number, and three in each of four consecutive quarters is a finding.
      Every count has an honest zero available and none of them has a default —
      a review that could not read a register records that it could not, in
      `not_readable`, rather than reporting nothing found. A confident zero is
      worse than an honest gap.
    layout: form
    review: required
    approvers: [senior-management]
    retention:
      keep: 7y
      authority: O. Reg. 406/19 s. 28 (1) — every document and record created or acquired under the Regulation is retained for at least seven years after it is created or acquired
      reason: >
        This is the record of the organisation having looked. In a prosecution
        under the Environmental Protection Act the question is what the
        organisation did to prevent the thing happening, and a quarterly review
        with findings and actions is the most direct answer to it that any of
        these registers holds.
    columns:
      - {key: period, label: Quarter reviewed, type: text, required: true}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user}
      - {key: project_areas_active, label: Project areas removing soil in the period, type: int, required: true}
      - {key: determinations_outstanding, label: Project areas with no recorded Registry determination, type: int, required: true}
      - {key: approvals_outstanding, label: Project areas with no recorded approval determination, type: int, required: true}
      - {key: notices_filed, label: Registry notices filed in the period, type: int, required: true}
      - {key: notices_filed_late, label: Notices filed after the first load left, type: int, required: true}
      - {key: closeouts_overdue, label: Project areas past 30 days from the last load with no close-out, type: int, required: true}
      - {key: loads_unacknowledged, label: Loads still without an acknowledgement at the destination, type: int, required: true}
      - {key: landfill_deposits_undeclared, label: Landfill deposits with no qualified person's s. 22 declaration, type: int, required: true}
      - {key: observations_open, label: Contamination observations still open, type: int, required: true}
      - {key: assessments_late, label: Observations whose documents were not reviewed inside 30 days, type: int, required: true}
      - {key: incidents_open, label: Environmental incidents still open, type: int, required: true}
      - {key: incidents_not_forthwith, label: Incidents where notification was not made forthwith, type: int, required: true}
      - {key: approvals_expiring, label: Instruments expiring within 90 days, type: int, required: true}
      - {key: approvals_expired, label: Instruments that expired with the activity continuing, type: int, required: true}
      - {key: conditions_unmet, label: Instruments with a condition recorded as not met, type: int, required: true}
      - {key: dewatering_checks_missed, label: Weeks an operating discharge went unchecked, type: int, required: true}
      - {key: not_readable, label: Registers that could not be read, and why, type: longtext, required: true}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: patterns, label: What is recurring, rather than what is late, type: longtext, required: true}
      - {key: actions, label: Actions, with an owner and a date, type: longtext, required: true}
      - {key: previous_actions_closed, label: Actions from the last review that are now closed, type: int, required: true}
      - {key: escalated_to_senior_management, label: Matters taken to senior management, type: longtext}
      - {key: evidence, label: Extracts the review was built from, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: who reads the whole of
the environmental programme at once, on a clock, and what they are looking for
that nothing else can see.

It exists because **every other obligation in this programme is triggered by a
row, and a row that was never created triggers nothing.** A project area whose
Registry determination was never recorded raises no filing occurrence, no
close-out and no approval determination — it is not late, it is absent, and the
due list is silent about it. The daily sweep can only report on work the data
knows about. This review is the one artifact that asks what is missing rather
than what is overdue, and it is the reason the record-origin chains in this
programme terminate somewhere rather than running out.

It must be built from **counts that are compared with the last quarter's**, not
from a narrative. Three outstanding determinations is a fact; three outstanding
determinations in each of four quarters, with three different project areas each
time, is the finding — the determination is being made on site by whoever is
standing there, and the register is being completed afterwards to match what
happened. `patterns` is a required field for exactly that reason, and it is asked
separately from `findings` because the two are different acts of reading.

**`not_readable` is required and it is the most important field on the row.** A
review that could not open the tracking system's export, or that found the
observation register empty because nobody had ever been shown it, has refuted
nothing. Recording a zero in that situation is worse than recording nothing: it
is a confident statement of compliance derived from an absence of data, and it
will be quoted back by somebody who believes it. The procedure must require the
reviewer to say plainly what could not be read, and must forbid a count from
being entered for a register that could not be opened.

It must cover **the things that are nobody's occurrence**. Some of these have no
obligation anywhere because there is no row to hang one on:

- a project area that has been excavating for two months and has no row in the
  excavation project register at all;
- a sub-trade hauling soil off a site this organisation is the constructor of,
  under its own arrangements, with no hauling records coming back;
- a landfill deposit made on price, with no qualified person's s. 22 declaration,
  which is a prohibition rather than a paperwork gap;
- an instrument held by the owner that this organisation has been relying on and
  has never seen.

Each of those is found by a person looking across the programme and by nothing
else, and each has a count above it.

**Quarterly is this organisation's, and the statutes require no review at all.**
What they require is that the discharge does not happen and that the records
exist. The review is chosen at a quarter because it is short enough that a
pattern is still correctable and long enough that the counts mean something: a
monthly version of this becomes a form somebody fills in, and an annual one
discovers in March what went wrong the previous May.

It must end in **actions with an owner and a date**, and the following quarter
must count how many of the last quarter's were closed. A review that produces
findings nobody was given is the specific failure that makes a governance
programme decorative, and `previous_actions_closed` is a required integer so that
the failure is visible in the record rather than in somebody's memory.
