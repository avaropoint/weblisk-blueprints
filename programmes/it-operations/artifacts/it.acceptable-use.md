---
id: it.acceptable-use
kind: policy
title: Acceptable Use of Technology
structure: policy
path: policies/acceptable-use-policy.md

satisfies:
  - iso_27001:A.5.10
  - iso_27001:A.8.1
  - iso_27001:A.8.23
  - iso_27001:A.6.2
  - can_ciosc_104:CIOSC-L1-08
  - cis_controls:4.8
  - soc2:CC1.1

approved_by: [senior-management]

declares:
  obligation:
    id: it.acceptable-use-acknowledgement
    activity: Reissue the acceptable use policy and record who has acknowledged it
    cadence: each year
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/acceptable-use-acknowledgements.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Acceptable Use Acknowledgement Record
    note: >
      One row per issue of the policy, not per person. What it answers is
      whether the current version reached everybody: `outstanding` against
      `in_scope` is the number, and a register that records only the people who
      signed cannot produce it.
    layout: form
    review: required
    approvers: [it-manager]
    columns:
      - {key: issued_on, label: Issued on, type: date, required: true}
      - {key: version, label: Policy version, type: text, required: true}
      - {key: what_changed, label: What changed, type: longtext, required: true}
      - {key: in_scope, label: People in scope, type: int, required: true}
      - {key: acknowledged, label: Acknowledged, type: int, required: true}
      - {key: outstanding, label: Outstanding, type: int, required: true}
      - {key: contractors_included, label: Contractors and temporary staff included, type: bool, required: true}
      - {key: notes, label: Follow-up, type: longtext, required: true}
---

What this document must establish for THIS organisation: what people may and may
not do with the organisation's technology and information, in language a person
without a technical background can follow.

It must be written as rules people can keep. A policy that bans personal use of
email outright, in an organisation where everybody uses their work laptop to
check a bank balance at lunch, teaches the whole workforce that these documents
describe an imaginary workplace. Say what is permitted, say what is not, and be
able to defend the line.

It must cover the specific things that cause harm here: credentials shared
between people, work information in personal cloud accounts, unapproved software
and browser extensions, personal devices, removable media, and the handling of
information a client has classified.

It must say what monitoring the organisation performs, in plain terms. In
Ontario, an employer with 25 or more employees is separately required by the
Employment Standards Act to have a written policy on electronic monitoring that
says whether it monitors, how, in what circumstances, and for what purposes —
that policy is in the employment programme, and this one must agree with it. Two
documents describing the same monitoring differently is worse than one.

It must state the consequence of breaking it, and connect that to the
disciplinary process that already exists rather than inventing a parallel one.

It must be reissued when it changes, not only annually, and the acknowledgement
must be of the current version. An acknowledgement gathered against a version
nobody can produce is evidence of nothing.
