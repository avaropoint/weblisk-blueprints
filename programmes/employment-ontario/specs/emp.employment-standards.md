---
id: emp.employment-standards
kind: procedure
title: Employment Standards Compliance
structure: procedure
path: procedures/employment-standards-compliance.md

satisfies:
  - employment_standards_ontario:2
  - employment_standards_ontario:23
  - employment_standards_ontario:17
  - employment_standards_ontario:18
  - employment_standards_ontario:22
  - employment_standards_ontario:24
  - employment_standards_ontario:33
  - employment_standards_ontario:11
  - employment_standards_ontario:46

approved_by: [senior-management]

declares:
  obligation:
    id: emp.esa-review
    activity: Review employment standards compliance — rates, hours, overtime, holidays, vacation and leaves
    cadence: each year
    authority: Employment Standards Act, 2000 — minimum wage rates are adjusted on 1 October each year
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/employment-standards-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Employment Standards Review Record
    note: >
      One row per review. Each column is a place the Act is commonly missed
      rather than a heading from the statute: the rate that was correct until
      1 October, the excess-hours agreement nobody re-signed, the public holiday
      pay divisor, and the vacation entitlement that changed at five years.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: poster_current, label: Current Minister's poster displayed and issued to staff, type: bool, required: true}
      - {key: minimum_wage_current, label: All rates at or above the current minimum, type: bool, required: true}
      - {key: hours_agreements, label: Excess hours agreements in force and valid, type: int, required: true}
      - {key: overtime_method, label: Overtime calculated weekly or under an averaging agreement, type: select, required: true,
         options: [Weekly, Averaging agreement with approval, Mixed, Not applicable]}
      - {key: public_holiday_method, label: Public holiday pay calculated correctly, type: bool, required: true}
      - {key: vacation_entitlements, label: Vacation entitlements correct at the five-year step, type: bool, required: true}
      - {key: leaves_administered, label: Statutory leaves administered with benefits continued, type: bool, required: true}
      - {key: wage_statements, label: Wage statements carry every required element, type: bool, required: true}
      - {key: exempt_roles_reviewed, label: Roles treated as exempt reviewed against the regulations, type: int, required: true}
      - {key: findings, label: Findings and corrections made, type: longtext, required: true}
---

What this document must establish for THIS organisation: how it keeps to the
Employment Standards Act, and who checks.

It must state which employees are covered and which are not, and be careful
about it. The Act does not apply to employees of federal works, undertakings and
businesses — banking, telecommunications, interprovincial transport, ports,
broadcasting — who are covered by the Canada Labour Code instead. It also has
role-based exemptions and special rules set by regulation, and treating a role
as exempt because of its title is the most expensive error available here: the
test is the work, not the label, and the remedy runs back years.

It must name what changes on a schedule. Minimum wage rates are adjusted every
1 October by reference to the Ontario Consumer Price Index, and a rate that was
correct last year is a contravention this year. The Minister's poster is
reissued from time to time and the current version must be posted and given to
each employee within thirty days of hire.

It must say who calculates overtime and on what basis. Overtime is weekly, at
one and a half times the regular rate after forty-four hours, unless an
averaging agreement with the required approval is in place — and time off in
lieu requires a written agreement and is also at time and a half.

It must record the written agreements the Act requires and where they are kept:
excess daily or weekly hours, overtime averaging, and electronic agreement to
receive wage statements. An agreement the employer cannot produce does not exist,
and an employee may revoke the excess hours one on two weeks' notice.

It must cover the leaves as entitlements rather than as favours, and say that
benefit plan participation continues and service accrues throughout. The Act
lists more than a dozen, several of them recent, and the organisation's own
policies must not be more restrictive than the statute.

It must say what happens when an error is found: it is corrected, the employee
is made whole, and the correction is recorded. An employer that finds a
systematic error and fixes it going forward has kept the liability for
everything before.
