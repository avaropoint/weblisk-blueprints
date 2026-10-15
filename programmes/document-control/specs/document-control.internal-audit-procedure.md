---
id: document-control.internal-audit-procedure
version: 1.1.0
kind: procedure
title: Internal Audit Procedure
structure: procedure
path: procedures/internal-audit.md
template: procedure

satisfies:
  # Only the internal-audit clause of each standard. The clauses on correcting
  # a nonconformity are NOT claimed: this procedure finds nonconformities and
  # does not govern how they are corrected. Cited by id only.
  - iso_9001:9.2
  - iso_45001:9.2
requires: [document-control.policy]

declares:
  obligation:
    id: document-control.internal-audit
    activity: Internal audit of the document control programme
    cadence: each year
    responsible: internal-auditor
    applies_to: the organisation
    records: registers/internal-audits.md
  register:
    title: Internal Audit Record
    note: >
      One row per audit. What was examined is required even when nothing was
      found — an audit that records no findings and no scope is
      indistinguishable from an audit that did not happen.
    columns:
      - {key: audited_on, label: Audited on, type: date, required: true}
      - {key: auditor, label: Auditor, type: user, required: true}
      - {key: independent, label: Independent of the work audited, type: bool, required: true}
      - {key: scope, label: What was examined, type: longtext, required: true}
      - {key: findings, label: Findings, type: int}
      - {key: findings_detail, label: Findings detail, type: longtext}
      - {key: closed_on, label: All findings closed on, type: date}
---

What this document must establish: how the organisation checks that what it
wrote down is what it actually does.

It must say who may audit and on what basis they are independent of the work
they audit — self-assessment by the person who owns the process is not an audit,
and a certifying body will say so. It must state how findings are recorded,
who is accountable for closing each one, and how closure is verified rather than
merely reported.

It must say what happens when an audit finds nothing. A programme that has never
recorded a finding is either exemplary or unaudited, and the two are
indistinguishable from the outside unless the audit records what was examined
and not only what was wrong.
