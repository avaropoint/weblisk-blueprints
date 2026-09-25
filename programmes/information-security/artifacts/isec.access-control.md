---
id: isec.access-control
kind: policy
title: Access Control Policy
structure: policy
path: policies/access-control-policy.md

satisfies:
  - iso_27001:A.5.15
  - iso_27001:A.5.16
  - iso_27001:A.5.17
  - iso_27001:A.5.18
  - iso_27001:A.8.2
  - iso_27001:A.8.3
  - iso_27001:A.8.5
  - nist_csf_2:PR.AA-01
  - nist_csf_2:PR.AA-03
  - nist_csf_2:PR.AA-05
  - can_ciosc_104:CIOSC-L1-05
  - can_ciosc_104:CIOSC-L1-12
  - can_ciosc_104:CIOSC-L1-18
  - cis_controls:5.1
  - cis_controls:6.1
  - soc2:CC6.1

requires: [isec.policy, isec.classification]
approved_by: [senior-management]

declares:
  obligation:
    id: isec.access-review
    activity: Review of who has access to what, against what their role requires
    cadence: each quarter
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/access-reviews.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - iso_27001:A.5.18
      - nist_csf_2:PR.AA-05
      - cis_controls:5.3
  register:
    title: Access Review Record
    note: >
      One row per review of one system or one group of systems. The columns that
      make it evidence are `accounts_removed` and `privileged_accounts`: a review
      that removes nothing, quarter after quarter, is either an organisation
      where nobody ever changes role or a review nobody performs.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: system, label: System or service, type: text, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: confirmed_by_owner, label: Confirmed by the asset owner, type: bool, required: true}
      - {key: accounts_reviewed, label: Accounts reviewed, type: int, required: true}
      - {key: privileged_accounts, label: Of those, privileged, type: int, required: true}
      - {key: accounts_removed, label: Accounts removed or reduced, type: int, required: true}
      - {key: dormant_accounts, label: Dormant accounts found, type: int, required: true}
      - {key: shared_accounts, label: Shared accounts in use, type: int, required: true}
      - {key: mfa_gaps, label: Accounts without multi-factor authentication, type: int, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: who may reach what, on
what authority, and how that authority is taken away again.

It must state the rule the organisation actually works by — least privilege,
granted against a role rather than a person, requested by a manager and approved
by the owner of the information. Where the organisation is small enough that the
requester and the approver are sometimes the same person, it must say what
happens then rather than leaving a rule everybody knows is broken.

It must treat privileged access as a separate thing with its own rules: who may
hold it, whether it is held permanently or claimed for a task, how it is logged,
and how it differs from the person's ordinary account. A privileged account used
for daily work is the single most common finding in this family.

It must state the authentication requirement in terms of what it protects, not
in terms of a password length. Multi-factor authentication on anything reachable
from the internet is the current baseline that every framework cited here
expects; where a system cannot support it, that is an exception with a name, a
date and a compensating control, recorded rather than tolerated.

It must say what happens on the day somebody leaves or changes role, and how
fast. "Promptly" is not a standard; same day for a departure and five days for a
role change are, and the quarterly review above exists to catch what the process
missed rather than to be the process.

It must cover the accounts nobody owns — service accounts, shared logins,
vendor-support accounts, the account the payroll system uses. They survive every
leaver process, because no leaver process has ever named one.
