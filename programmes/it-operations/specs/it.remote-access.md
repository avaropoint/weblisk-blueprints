---
id: it.remote-access
kind: procedure
title: Remote Access and Remote Working
structure: procedure
path: procedures/remote-access.md

satisfies:
  - iso_27001:A.6.7
  - iso_27001:A.8.20
  - iso_27001:A.8.21
  - iso_27001:A.8.22
  - can_ciosc_104:CIOSC-L1-05
  - can_ciosc_104:CIOSC-L1-09
  - cis_controls:12.6
  - nist_csf_2:PR.AA-05
  - nist_csf_2:PR.IR-01
  - soc2:CC6.6

requires: [it.acceptable-use, isec.access-control]

declares:
  obligation:
    id: it.remote-access-review
    activity: Review who has remote access, by what means, and whether it is still needed
    cadence: each quarter
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/remote-access-reviews.md
    escalate: {after: 2w, to: information-security-lead}
  register:
    title: Remote Access Review Record
    note: >
      One row per review. `third_party_accounts` is separated from staff
      accounts because it is the category that is granted for a project and
      never withdrawn — a support vendor's standing access is the access nobody
      remembers granting and nobody owns.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: methods_in_use, label: Remote access methods in use, type: longtext, required: true}
      - {key: staff_accounts, label: Staff accounts with remote access, type: int, required: true}
      - {key: third_party_accounts, label: Third-party accounts with remote access, type: int, required: true}
      - {key: mfa_enforced, label: Accounts with multi-factor authentication enforced, type: int, required: true}
      - {key: removed, label: Accounts removed, type: int, required: true}
      - {key: unapproved_methods, label: Unapproved methods found in use, type: int, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: how somebody working
away from the office reaches the organisation's systems, and what has to be true
of them and their device before they can.

It must name the approved methods and say that anything else is not permitted.
The failure here is not usually an insecure method; it is three methods, two of
which nobody manages because they were set up for a project in 2022.

It must require multi-factor authentication on every route in from the internet,
without exception, and treat any exception as a risk with an owner and a date.
This is the single control that most reliably distinguishes organisations that
have a credential-stuffing incident from those that do not, and every framework
cited here expects it.

It must cover third-party and vendor access as a separate case with its own
rules: time-limited, requested for a purpose, approved by the system owner, and
withdrawn on completion rather than on the next review.

It must say what is required of the place a person works from as well as the
device — who else can see the screen, whether the household network is
acceptable, what happens on public Wi-Fi, and how paper is handled at home.
A.6.7 is about remote working, not only about remote connecting, and the paper
half is the half with no technical control available.

It must connect to the access control policy rather than restating it. The rule
about who may have access lives there; what lives here is how the connection is
made and what makes it safe.
