---
id: emp.workplace-policies
kind: policy
title: Disconnecting From Work and Electronic Monitoring
structure: policy
path: policies/disconnecting-and-electronic-monitoring.md

satisfies:
  - employment_standards_ontario:21.1.1
  - employment_standards_ontario:41.1.1
  - iso_27001:A.5.34

requires: [emp.employment-standards]
approved_by: [senior-management]

declares:
  obligation:
    id: emp.policy-distribution
    activity: Confirm the two statutory workplace policies are in place before 1 March and have been distributed
    cadence: each year
    authority: ESA ss. 21.1.1 and 41.1.1 — in place before 1 March each year for employers with 25 or more employees on 1 January
    interval_basis: required
    responsible: hr-lead
    applies_to: the organisation
    records: registers/workplace-policy-distributions.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Statutory Workplace Policy Record
    note: >
      One row per year. `headcount_on_1_january` is the first column because it
      is what decides whether the duty applies at all, and an employer that
      crossed twenty-five during the previous year owes both policies by 1 March
      without anybody having told it.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: year, label: Year, type: text, required: true}
      - {key: headcount_on_1_january, label: Employees on 1 January, type: int, required: true}
      - {key: required, label: Policies required this year, type: bool, required: true}
      - {key: disconnecting_in_place_on, label: Disconnecting policy in place on, type: date}
      - {key: monitoring_in_place_on, label: Electronic monitoring policy in place on, type: date}
      - {key: distributed_on, label: Distributed to employees on, type: date}
      - {key: new_hires_covered, label: Process in place to issue within 30 days of hire, type: bool, required: true}
      - {key: changed_this_year, label: Changed this year, type: bool, required: true}
      - {key: superseded_retained, label: Superseded versions retained three years, type: bool, required: true}
---

What this document must establish for THIS organisation: whether employees are
expected to answer messages outside working hours, and what the employer watches.

It must first record the headcount test. Both policies are required of an
employer with twenty-five or more employees in Ontario on 1 January of a year,
and both must be in place before 1 March of that year. An employer that grows
past twenty-five during a year acquires the duty on the following 1 January and
has two months, which is why the count belongs in a register rather than in
somebody's recollection.

It must say something real about disconnecting. The Act does not set a content
standard, which means the compliance question is only whether the policy exists,
is current and reached everybody — but a policy that says nothing is a document
the workforce reads once and correctly disregards. Expectations about after-hours
email, about on-call, about response times and about who may set them are what
make it worth the page.

It must describe electronic monitoring accurately, because here the Act does set
content: whether the employer monitors employees electronically and, if so, a
description of how and in what circumstances, and the purposes for which the
information collected may be used. That includes the things employers do not
think of as monitoring — location tracking on a phone or vehicle, badge and door
logs, call recording, screen or keystroke tooling, and the audit logs kept for
security purposes.

It must agree with the acceptable use policy in the IT programme, which
describes the same monitoring from the security side. Two documents describing
one practice differently is worse than one, and an employee who finds the
difference has found the organisation's credibility gap.

It must be distributed, not published. A copy within thirty days of preparing it
or changing it, and within thirty days of hire for a new employee — and the
distribution is the evidence, which is what the register records.

It must be kept after it is replaced. Superseded versions are retained for three
years after they cease to be in effect, which makes the retention schedule's
entry for these policies a statutory one.
