---
id: cohs.ohsms-audit
kind: procedure
title: Audit of the Management System
structure: procedure
path: procedures/management-system-audit.md

satisfies:
  - ohsa_ontario:7.6.1
  - iso_45001:9.2
  - cor_2020:COR-02

requires: [cohs.management-review, cohs.regulatory-currency]

declares:
  obligation:
    id: cohs.ohsms-audit
    activity: Audit of the occupational health and safety management system, of the type this year's position in the certification cycle requires
    cadence: each year
    authority: ISO/IEC 17021-1:2015 §9.1.3.3 — an accredited certification body shall conduct a surveillance or recertification audit in each calendar year, the first no later than twelve months after the certification decision. ISO 45001:2018 clause 9.2 separately requires internal audit at planned intervals
    interval_basis: required
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/management-system-audits.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Management System Audit Record
    note: >
      One row per audit. `audit_type` and `cycle_year` are both required because
      the question a certificate holder must be able to answer is not "did we
      audit this year" but "did we hold the audit this year of the cycle
      required" — and the two schemes in this industry answer it differently.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: audited_on, label: Audit completed on, type: date, required: true}
      - {key: scheme, label: Scheme, type: select, required: true,
         options: [ISO 45001, Certificate of recognition, Both, Internal only]}
      - {key: audit_type, label: Type, type: select, required: true,
         options: [Internal audit, Certification stage 1, Certification stage 2,
                   External surveillance, Recertification, External certifying audit,
                   Internal maintenance audit]}
      - {key: cycle_year, label: Year of the certificate cycle, type: int, required: true}
      - {key: auditor, label: Auditor, type: text, required: true}
      - {key: auditor_independent, label: Auditor independent of the work audited, type: bool, required: true}
      - {key: scope, label: Scope, type: longtext, required: true}
      - {key: projects_sampled, label: Projects sampled, type: longtext, required: true}
      - {key: score, label: Score or result, type: text}
      - {key: legislated_items_result, label: Result on legislated items, type: text}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: actions_raised, label: Actions raised, type: longtext, required: true}
      - {key: certificate_expires, label: Certificate expires, type: date}
      - {key: next_audit_due, label: Next audit due, type: date, required: true}
---

What this document must establish for THIS organisation: who audits the
programme, against what, how often, and what the audit result actually governs.

**It must not transplant one certification cycle onto the other, and this is the
most consequential paragraph in the artifact.** The two schemes in common use in
Canadian construction run on genuinely different rhythms:

- **An accredited ISO 45001 certificate** requires an audit by the certification
  body **in every calendar year** — surveillance or recertification — with the
  first surveillance no later than twelve months after the certification decision.
  A three-year certificate is not three years without an external auditor; a
  missed surveillance suspends or withdraws the certificate. The internal audit
  requirement in the standard is **separate and additional** and never substitutes
  for surveillance.
- **A certificate of recognition** runs an external certifying audit in year one
  and **internal maintenance audits** in years two and three, reviewed by the
  certifying partner, with re-application at the end.

An organisation that budgets the second cycle against the first loses its
certificate; one that budgets the first against the second overspends. The
register records the scheme, the type and the year of the cycle so that the
question "what is due next" has an answer that does not depend on somebody
remembering which scheme they are in.

It must state the scoring thresholds of the recognition scheme where the
organisation is in it, and must be precise that a **pass on the overall score and
on each element is not sufficient**: the legislated items must be met in full.
That is a different kind of threshold from a percentage and it is the one that
fails an otherwise good audit.

It must require the internal auditor to be **independent of the work audited**.
On a small contractor this is genuinely hard, and the honest answers are a
reciprocal arrangement with another organisation, a consultant, or a person from a
different part of the business — not the safety lead auditing their own programme
and recording that they found it satisfactory.

It must require the audit to **go to projects**. A management system audit
conducted entirely in a head office samples documents, and documents are the part
of this programme least likely to be wrong. `projects_sampled` is a required
column for that reason.

It must connect findings to the corrective action process with owners and dates
rather than leaving them in a report, and must require the **effectiveness** of
those actions to be checked before the next audit — an action closed on time whose
finding recurs is a finding about the action.

**The annual interval here is required**, and it is required by the certification
rules rather than by the health and safety standard, which asks only for planned
intervals. The document should say which of the two it is relying on, because an
organisation that is not certified is choosing its own interval and should know
that it is choosing.
