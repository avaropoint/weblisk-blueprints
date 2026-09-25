---
id: phipa.annual-report
kind: procedure
title: Annual Report to the Commissioner
structure: procedure
path: procedures/health-privacy-annual-report.md

satisfies:
  - phipa_ontario:6.4
  - phipa_ontario:12(3)

requires: [phipa.breach]

declares:
  obligation:
    id: phipa.annual-statistics
    activity: Report the previous year's privacy breach statistics to the Information and Privacy Commissioner
    cadence: each year
    authority: O. Reg. 329/04 s. 6.4 — report by 1 March each year for the previous calendar year
    interval_basis: required
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/health-privacy-annual-reports.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Annual Health Privacy Report Record
    note: >
      One row per reporting year. The counts are split the way the Commissioner's
      online form splits them, so the record is the submission rather than a
      summary somebody then has to re-derive under time pressure in February.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reporting_year, label: Calendar year reported, type: text, required: true}
      - {key: submitted_on, label: Submitted on, type: date, required: true}
      - {key: submitted_by, label: Submitted by, type: user, required: true}
      - {key: stolen, label: Information stolen, type: int, required: true}
      - {key: lost, label: Information lost, type: int, required: true}
      - {key: used_without_authority, label: Used without authority, type: int, required: true}
      - {key: disclosed_without_authority, label: Disclosed without authority, type: int, required: true}
      - {key: total, label: Total, type: int, required: true}
      - {key: reported_during_year, label: Of those, reported to the Commissioner during the year, type: int, required: true}
      - {key: confirmation, label: Submission confirmation reference, type: text}
---

What this artifact must establish: that the annual statistical report was made,
by the deadline, from a record that can support the numbers.

It is a small obligation with a hard date, which is exactly the kind that gets
missed. By 1 March each year every health information custodian reports to the
Commissioner how many times in the previous calendar year personal health
information in its custody was stolen, lost, used without authority or disclosed
without authority — including the breaches that were never individually
reportable.

The number is a count of breaches, and a custodian that has kept no breach
record will produce a zero. A zero submitted by an organisation of any size is a
statement the Commissioner reads, and it is the statement most likely to be
wrong: in a year with no recorded breaches, either nothing happened or nothing
was recorded, and only one of those is defensible.

The deadline is statutory, which is why `interval_basis` is recorded as required
here and as chosen almost everywhere else in this corpus. The distinction
matters: a reader seeing an annual cadence cannot otherwise tell whether the
date was set by the regulator or by the organisation.
