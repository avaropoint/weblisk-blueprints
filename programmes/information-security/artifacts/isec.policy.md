---
id: isec.policy
kind: policy
title: Information Security Policy
structure: policy
path: policies/information-security-policy.md

satisfies:
  - iso_27001:A.5.1
  - iso_27001:A.5.4
  - iso_27001:A.5.36
  - nist_csf_2:GV.PO-01
  - nist_csf_2:GV.RR-01
  - can_ciosc_104:CIOSC-L1-15
  - soc2:CC1.1

approved_by: [senior-management]

declares:
  obligation:
    id: isec.management-review
    activity: Management review of the information security management system
    cadence: each year
    authority: ISO/IEC 27001:2022 clause 9.3 — management review at planned intervals
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/isms-management-reviews.md
    escalate: {after: 4w, to: senior-management}
    satisfies:
      - iso_27001:A.5.4
      - soc2:CC4.2
  register:
    title: ISMS Management Review Record
    note: >
      One row per review. Clause 9.3 names the inputs a management review must
      consider; a record that lists none of them evidences a meeting rather than
      a review. The two columns that make it a decision are `decisions` and
      `resources_agreed` — a review that identifies a shortfall and commits no
      resource has restated the shortfall.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: chaired_by, label: Chaired by, type: user, required: true}
      - {key: inputs, label: Inputs considered, type: longtext, required: true}
      - {key: incidents_in_period, label: Security incidents in the period, type: int, required: true}
      - {key: audit_findings_open, label: Audit findings still open, type: int, required: true}
      - {key: risks_above_appetite, label: Risks above appetite, type: int, required: true}
      - {key: decisions, label: Decisions and actions, type: longtext, required: true}
      - {key: resources_agreed, label: Resources agreed, type: longtext, required: true}
      - {key: next_review, label: Next review due, type: date}
---

What this document must establish for THIS organisation: what senior management
commits to protecting, why, and who holds the authority to say no.

It must state the scope in the organisation's own terms — which parts of the
business, which systems, which locations, which people, and what is deliberately
outside it and why. An undeclared exclusion is what turns an audit into a
surprise, and every other artifact in this programme inherits its scope from
here.

It must name the objectives the organisation is steering by, not repeat the
standard's clause headings. "Customer data is not disclosed to anybody outside
the engagement" is an objective; "we shall maintain confidentiality, integrity
and availability" is a recital.

It must assign authority by position: who owns the programme, who may accept a
risk, who may grant an exception and for how long, and who is told when an
exception is granted. A policy with no exception route is a policy people work
around silently, and the exception register is the honest version of what the
workarounds already are.

It must say what happens when it is not followed, and connect that to the
disciplinary process rather than implying one. A.6.4 expects the consequence to
exist and be known; a policy that threatens unspecified action has not made it
known.
