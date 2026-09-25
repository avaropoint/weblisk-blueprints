---
id: cohs.safety-statistics
kind: register
title: Safety Performance Statistics
structure: standard
path: registers/safety-performance-statistics.md

satisfies:
  - cor_2020:COR-18
  - isnetworld:ISN-SAFE-01

requires: [cohs.notifiable-events, cohs.incidents]

register:
  title: Safety Performance Statistics
  note: >
    One row per reporting period per account. The denominator is a required
    column and it is the reason this register exists as data rather than as a
    monthly slide: a rate without the hours it was computed from cannot be
    checked, cannot be compared with anybody else's, and cannot be recomputed
    when a claim is reclassified six months later.
  columns:
    - {key: period, label: Period, type: text, required: true}
    - {key: period_end, label: Period ending, type: date, required: true}
    - {key: account, label: Account or business unit, type: text, required: true}
    - {key: hours_worked, label: Hours worked, type: number, required: true}
    - {key: workers, label: Workers, type: int, required: true}
    - {key: fatalities, label: Fatalities, type: int, required: true}
    - {key: lost_time_injuries, label: Lost time injuries, type: int, required: true}
    - {key: medical_aid_injuries, label: Medical aid injuries, type: int, required: true}
    - {key: restricted_or_transferred, label: Restricted work or job transfer cases, type: int, required: true}
    - {key: first_aid_only, label: First aid only, type: int, required: true}
    - {key: near_misses, label: Near misses reported, type: int, required: true}
    - {key: recordable_rate, label: Total recordable rate, type: number}
    - {key: lost_time_rate, label: Lost time rate, type: number}
    - {key: dart_rate, label: Days away, restricted or transferred rate, type: number}
    - {key: rate_basis, label: Basis of the rates, type: text, required: true}
    - {key: experience_rating, label: Experience modifier, if a client requires one, type: number}
    - {key: leading_inspections, label: Inspections completed against planned, type: text, required: true}
    - {key: leading_assessments, label: Pre-task assessments completed against expected, type: text, required: true}
    - {key: leading_actions_closed, label: Corrective actions closed on time, type: text, required: true}
    - {key: compiled_by, label: Compiled by, type: user, required: true}

declares:
  obligation:
    id: cohs.statistics-compilation
    activity: Compilation of the period's safety performance statistics
    cadence: each month
    authority: Owner prequalification schemes and COR 2020 require injury statistics to be compiled and communicated. No Ontario provision requires them
    interval_basis: chosen
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/safety-performance-statistics.md
    escalate: {after: 2w, to: senior-management}
---

What this artifact must establish: the numbers this organisation will be asked
for, computed the same way each time, from data somebody can point at.

It must carry the **denominator and the basis** alongside every rate. Hours worked
and the multiplier used are what make a rate comparable, and a programme that
publishes a rate without them cannot answer the first question a prequalification
reviewer asks. `rate_basis` is required for the same reason: the multiplier
differs between schemes and jurisdictions, and two organisations reporting "1.8"
may not be reporting the same thing.

It must carry the **leading indicators** beside the lagging ones, and this is the
part organisations skip. Inspections completed against planned, pre-task
assessments completed against expected, and corrective actions closed on time are
measures of whether the programme is being operated. Injury counts measure what
happened afterwards, they are small numbers on a small contractor, and a good
month is indistinguishable from a lucky one. A programme that steers by injury
counts alone is steering by a lagging, noisy signal — and, worse, it creates a
quiet incentive against reporting, which degrades the only data it has.

It must say **who classifies an injury** and against what definition, and must
keep the classification stable. Most of the argument about safety statistics is
really an argument about whether a case was recordable, and an organisation that
reclassifies under pressure produces a series that cannot be trended.

It must be explicit that **no Ontario provision requires these statistics at all**.
They are required by clients, by prequalification services and by the recognition
scheme, and they are useful to the organisation. Presenting them as a legal
obligation would be wrong, and it would undermine the statements elsewhere in this
programme that are legal obligations.

**The monthly compilation is this organisation's choice.** A month is chosen
because it is short enough that a trend is visible within a project's life and
long enough that the numbers are not noise — and because most of the schemes that
ask for these figures ask annually, so an organisation compiling only when asked
will be reconstructing a year from memory.

It must say how the numbers reach the people who can act on them: the management
review, the committee, and the supervisors whose sites the numbers came from. A
statistic that only ever travels upward is a report, not a control.
