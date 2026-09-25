---
id: isec.internal-audit
kind: procedure
title: Information Security Internal Audit
structure: procedure
path: procedures/information-security-audit.md

satisfies:
  - iso_27001:A.5.35
  - iso_27001:A.5.36
  - iso_27001:A.8.34
  - iso_22301:9.2
  - nist_csf_2:GV.OC-05
  - soc2:CC4.1

requires: [isec.policy, isec.statement-of-applicability]

declares:
  obligation:
    id: isec.isms-audit
    activity: Internal audit of the information security management system
    cadence: each year
    authority: ISO/IEC 27001:2022 clause 9.2 — internal audits at planned intervals
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/isms-audits.md
    escalate: {after: 4w, to: senior-management}
    satisfies:
      - iso_27001:A.5.35
      - soc2:CC4.1
  register:
    title: ISMS Internal Audit Record
    note: >
      One row per audit. `auditor_independent` is a required column because an
      audit conducted by the person who operates the control is a self-
      assessment, and recording it as an audit is how an organisation arrives
      at certification believing it has been checked.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: audited_on, label: Audited on, type: date, required: true}
      - {key: scope, label: Scope audited, type: longtext, required: true}
      - {key: auditor, label: Auditor, type: user, required: true}
      - {key: auditor_independent, label: Auditor independent of the area audited, type: bool, required: true}
      - {key: criteria, label: Criteria used, type: text, required: true}
      - {key: conformities, label: Areas found conforming, type: longtext, required: true}
      - {key: nonconformities, label: Nonconformities raised, type: int, required: true}
      - {key: major_nonconformities, label: Of those, major, type: int, required: true}
      - {key: observations, label: Observations and opportunities, type: longtext, required: true}
      - {key: report_issued_on, label: Report issued on, type: date, required: true}
---

What this document must establish for THIS organisation: how the management
system is checked by somebody other than the person who runs it.

It must plan the programme rather than the audit. An annual audit of everything
is an audit of nothing in particular; a programme that covers the whole scope
over a cycle and weights it by risk and by what went wrong last time is what the
clause asks for and what produces findings.

It must state how independence is achieved in an organisation too small to have
a separate audit function. Swapping areas between managers, using a peer from a
different part of the business, or buying a day of somebody external are all
legitimate answers; "the security lead audits their own programme" is not, and
saying so plainly is more useful than an aspiration.

It must define what a nonconformity is and distinguish it from an observation.
Without the distinction every finding is negotiable, and the audit becomes a
conversation about wording.

It must say what happens to findings: who owns them, by when, and how closure is
verified. An audit whose findings are not tracked anywhere produces the same
findings next year, which is the most reliable sign in this whole programme that
nothing is being read.

It must not duplicate the document control programme's internal audit procedure.
That one checks that documents are controlled; this one checks that the security
controls the organisation declared applicable are in place and working.
