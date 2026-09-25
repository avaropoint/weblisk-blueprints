---
id: emp.accessibility-report
kind: procedure
title: Accessibility Compliance Report
structure: procedure
path: procedures/accessibility-compliance-report.md

satisfies:
  - aoda_ontario:86.1

requires: [emp.accessibility-policy, emp.accessibility-training]

declares:
  obligation:
    id: emp.accessibility-report
    # Annual, and deliberately so, for a filing that is triennial. The cadence
    # vocabulary has no three-year period and inventing one would be worse than
    # this: what recurs annually is the CHECK of whether a report is due and
    # whether the organisation could file a true one, which is the work that
    # actually has to happen every year. The interval is therefore recorded as
    # chosen — the authority requires the filing, not the annual check.
    activity: Confirm whether an accessibility compliance report is due and that the organisation could file a true one
    cadence: each year
    authority: IASR s. 86.1 — organisations with 20 or more employees file an accessibility compliance report, currently every three years by 31 December
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/accessibility-compliance-reports.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Accessibility Compliance Report Record
    note: >
      One row per year, whether or not a report was due. `due_this_year` and
      `filed_on` are separate from `would_answer_yes_to_all` because the useful
      finding is the one discovered in a non-filing year: an organisation that
      could not truthfully answer the questions has two years to fix it, and an
      organisation that only looks in December of a filing year has none.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: year, label: Year, type: text, required: true}
      - {key: employees, label: Employees in Ontario, type: int, required: true}
      - {key: in_scope, label: Organisation in scope to report, type: bool, required: true}
      - {key: due_this_year, label: Report due this year, type: bool, required: true}
      - {key: would_answer_yes_to_all, label: Could truthfully answer yes to every question, type: bool, required: true}
      - {key: exceptions, label: Requirements not yet met, type: longtext, required: true}
      - {key: filed_on, label: Filed on, type: date}
      - {key: filed_by, label: Filed by, type: user}
      - {key: certified_by, label: Certified by, type: user}
      - {key: confirmation, label: Submission confirmation, type: text}
---

What this document must establish for THIS organisation: whether it has to file
an accessibility compliance report, when, and who signs it.

It must record the threshold test. Organisations with twenty or more employees in
Ontario, and every designated public sector organisation, file an accessibility
compliance report with a director appointed under the Act — currently every three
years, by 31 December of the reporting year. An organisation that crossed twenty
employees since the last cycle is now in scope and will not have been told.

It must treat the report as a self-certification with consequences. It is signed
by a person with authority and it states that the organisation has met named
requirements; filing it while a requirement is unmet is a statement somebody has
to be able to stand behind, and an accessibility compliance director can inspect,
issue orders and impose administrative penalties.

It must require the annual check even in a year with no filing. That is the whole
point of the obligation above: the questions on the report are the requirements
in this programme, and finding two years early that the organisation could not
answer one of them truthfully is the difference between a plan and a scramble.

It must name who holds the file. The report is submitted online, a confirmation
is issued, and an organisation that cannot produce its last confirmation cannot
show it filed.
