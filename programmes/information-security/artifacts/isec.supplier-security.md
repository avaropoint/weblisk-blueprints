---
id: isec.supplier-security
kind: procedure
title: Supplier Security
structure: procedure
path: procedures/supplier-security.md

satisfies:
  - iso_27001:A.5.19
  - iso_27001:A.5.20
  - iso_27001:A.5.21
  - iso_27001:A.5.22
  - iso_27001:A.5.23
  - nist_csf_2:GV.SC-02
  - can_ciosc_104:CIOSC-L1-10
  - can_ciosc_104:CIOSC-L1-16
  - soc2:CC9.2

requires: [isec.supplier-register]

declares:
  obligation:
    id: isec.supplier-review
    activity: Review a supplier's security before its review date
    for:
      records: registers/suppliers.md
      due: 30d before review_due
      key: reference
    responsible: procurement-lead
    applies_to: the organisation
    records: registers/supplier-security-reviews.md
    escalate: {after: 2w, to: information-security-lead}
    satisfies:
      - iso_27001:A.5.21
  register:
    title: Supplier Security Review Record
    note: >
      One row per review of one supplier, keyed by the supplier's reference.
      `assurance_seen` distinguishes a review from a reminder: a supplier whose
      SOC 2 report was requested and never produced has been reviewed, and the
      finding is that nothing was seen.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: reference, label: Supplier, type: relation, required: true,
         target: /registers/suppliers.md#records, display: supplier}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: assurance_seen, label: Assurance evidence seen, type: select, required: true,
         options: [None requested, Requested and not provided, Questionnaire returned,
                   SOC 2 report reviewed, ISO 27001 certificate verified, Audit performed]}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: incidents_reported, label: Incidents they reported in the period, type: int, required: true}
      - {key: subprocessors_changed, label: Sub-processors changed, type: bool, required: true}
      - {key: terms_current, label: Security terms still current, type: bool, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Continue, Continue with conditions, Remediation required, Exit planned]}
      - {key: next_review, label: Next review due, type: date, required: true}
---

What this document must establish for THIS organisation: what is asked of a
supplier before they are given anything, what is checked afterwards, and what
happens when the answer is unsatisfactory.

It must set the requirement proportionate to what the supplier holds. A
questionnaire sent to every supplier including the coffee company produces
returns nobody reads; the classification and criticality columns in the register
are there so the depth of review is a consequence of the exposure rather than of
who remembered to ask.

It must state what goes into an agreement: what the supplier may do with the
information, where it may be held, who may sub-contract and on what notice, what
they must tell the organisation when they have an incident and how quickly, what
happens to the data at the end, and whether there is a right to audit or to
receive an assurance report instead.

It must cover the cloud services specifically. A.5.23 exists because a cloud
service is procured in minutes by somebody who is not in procurement, and the
control that works is a route to approval that is faster than the workaround.

It must say what happens at the end of the relationship — return or destruction
of information, revocation of access, and confirmation that it happened. An
exit is the moment the organisation has the least leverage and the most data
outside it.

It must not ask for assurance it will not read. A SOC 2 report received and
filed unopened is worse than none requested, because the register then says
assurance is held.
