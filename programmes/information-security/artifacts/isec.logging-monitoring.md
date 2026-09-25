---
id: isec.logging-monitoring
kind: procedure
title: Logging and Monitoring
structure: procedure
path: procedures/logging-and-monitoring.md

satisfies:
  - iso_27001:A.8.15
  - iso_27001:A.8.16
  - iso_27001:A.8.17
  - iso_27001:A.8.34
  - nist_csf_2:DE.CM-01
  - nist_csf_2:DE.CM-03
  - nist_csf_2:DE.AE-02
  - nist_csf_2:DE.AE-03
  - can_ciosc_104:CIOSC-L1-19
  - cis_controls:8.1
  - cis_controls:8.2
  - soc2:CC7.2

requires: [isec.policy]

declares:
  obligation:
    id: isec.monitoring-review
    activity: Review security alerts, logs and what they were not able to show
    cadence: each month
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/security-monitoring-reviews.md
    escalate: {after: 2w, to: information-security-lead}
  register:
    title: Security Monitoring Review Record
    note: >
      One row per review period. `sources_not_logging` is the column that makes
      it a control: an alert review that only reads the alerts that arrived
      cannot see the system that stopped sending any, and a source that went
      quiet is the failure mode this review exists to catch.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: period, label: Period covered, type: text, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: alerts_raised, label: Alerts raised, type: int, required: true}
      - {key: alerts_investigated, label: Alerts investigated, type: int, required: true}
      - {key: incidents_opened, label: Incidents opened from alerts, type: int, required: true}
      - {key: sources_expected, label: Log sources expected, type: int, required: true}
      - {key: sources_not_logging, label: Sources not logging, type: int, required: true}
      - {key: retention_verified, label: Retention period verified, type: bool, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: what is logged, who
looks at it, and how long it is kept.

It must name the sources and say why each one is on the list — authentication,
privileged use, changes to access, changes to configuration, data export, and
the security tooling itself. A log that exists because the product produces one
is not a decision.

It must state the retention period and the reason for it. Most organisations
discover the answer during an incident, when the question is whether the logs
reach back to the first access — and by then the period is whatever the default
was. Where personal information is in the logs, the retention period is also a
privacy decision and belongs in the retention schedule, not only here.

It must say who reviews, how often, and what they do about what they find. A
monitoring capability with no reviewer is a data collection exercise, and it is
the most expensive way to be surprised.

It must protect the logs from the people the logs are about. A.8.34 and the
segregation rule in the roles standard meet here: an administrator who can edit
the record of their own actions makes every other control in this programme
unprovable.

It must say what the organisation cannot see. An honest statement that endpoint
activity is not centrally logged is worth more than a monitoring policy that
implies coverage nobody has, because the incident response plan is written
against what is actually available.
