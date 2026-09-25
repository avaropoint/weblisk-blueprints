---
id: isec.security-reporting
kind: procedure
title: Security Performance Reporting
structure: procedure
path: procedures/security-performance-reporting.md

satisfies:
  - nist_csf_2:GV.OC-01
  - iso_22301:9.1
  - soc2:CC4.2

requires: [isec.policy]

declares:
  obligation:
    id: isec.security-report
    activity: Report security performance to senior management
    cadence: each quarter
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/security-performance-reports.md
  register:
    title: Security Performance Report Record
    note: >
      One row per report. The counts are deliberately of work outstanding rather
      than of work done: a report of activity completed always improves, and a
      report of what is overdue is the only one that can get worse in a period
      where nothing was done.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reported_on, label: Reported on, type: date, required: true}
      - {key: period, label: Period covered, type: text, required: true}
      - {key: incidents_opened, label: Incidents opened, type: int, required: true}
      - {key: incidents_open_at_period_end, label: Incidents still open, type: int, required: true}
      - {key: risks_above_appetite, label: Risks above appetite, type: int, required: true}
      - {key: risk_reviews_overdue, label: Risk reviews overdue, type: int, required: true}
      - {key: access_reviews_overdue, label: Access reviews overdue, type: int, required: true}
      - {key: supplier_reviews_overdue, label: Supplier reviews overdue, type: int, required: true}
      - {key: audit_findings_open, label: Audit findings open, type: int, required: true}
      - {key: training_completion, label: Awareness training completion (%), type: percent, required: true}
      - {key: commentary, label: What the numbers mean, type: longtext, required: true}
      - {key: decisions_requested, label: Decisions requested of management, type: longtext, required: true}
---

What this document must establish for THIS organisation: what senior management
is told about security, how often, and in terms they can act on.

It must report exposure rather than effort. Hours spent, tickets closed and
patches applied are activity; risks above appetite, overdue reviews and open
findings are exposure, and only the second kind gives management something to
decide.

It must carry the numbers that can get worse. A report built from completed work
improves every quarter regardless of the state of the organisation, and an
audience that has seen four improving reports will not believe the fifth.

It must ask for something. `decisions_requested` is a required column because a
report that requests nothing is an update, and the reason for reporting to
management at all is that some of these problems can only be solved by a
decision about money or priority.

It must be the input to the annual management review rather than a separate
exercise. Four quarterly reports make the review's evidence; an organisation
that produces both and connects neither does the work twice.
