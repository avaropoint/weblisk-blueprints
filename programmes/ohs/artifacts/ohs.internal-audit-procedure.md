---
id: ohs.internal-audit-procedure
kind: procedure
title: Internal Audit
structure: procedure
path: procedures/programme-audit.md

satisfies:
  - iso_45001:9.2
  - cor_2020:COR-02

requires: [ohs.policy, ohs.hazard-assessment-procedure]

declares:
  obligation:
    id: ohs.internal-audit
    activity: Internal audit of the health and safety programme
    cadence: each year
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/programme-audits.md
  register:
    title: Internal Audit Record
    note: >
      One row per audit. What was examined is required even when nothing was
      found — the procedure says an unaudited programme and an exemplary one are
      indistinguishable unless the scope is recorded.
    columns:
      - {key: audited_on, label: Audited on, type: date, required: true}
      - {key: auditor, label: Auditor, type: user, required: true}
      - {key: independent, label: Independent of the work audited, type: bool, required: true}
      - {key: scope, label: What was examined, type: longtext, required: true}
      - {key: findings, label: Findings raised, type: int}
      - {key: findings_detail, label: Findings detail, type: longtext}
      - {key: closed_on, label: All findings closed on, type: date}
---

What this document must establish for THIS organisation: how the programme is
checked against what it says about itself, by someone who did not write it.

It must define the audit scope in terms of this programme's own artifacts and
the obligations they declare, so an audit asks "did the hazard assessments
happen, and are they recorded" rather than re-reading the policy. It must
require independence appropriate to the organisation's size — in a small
organisation that may mean a different site's supervisor rather than a separate
department, and saying so honestly is better than claiming an independence that
does not exist.

It must say how findings are graded, who owns closing them, and what happens to
a finding that is not closed by its date. It must feed the management review the
policy declares, because an audit whose findings never reach the people who can
authorise the resources to fix them is a document produced for an auditor rather
than for the organisation.
