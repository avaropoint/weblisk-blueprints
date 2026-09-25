---
id: it.access-provisioning
kind: procedure
title: User Account Provisioning
structure: procedure
path: procedures/user-access-provisioning.md

satisfies:
  - iso_27001:A.5.16
  - iso_27001:A.5.17
  - iso_27001:A.5.18
  - iso_27001:A.8.2
  - cis_controls:5.1
  - cis_controls:5.3
  - cis_controls:6.1
  - cis_controls:6.2
  - can_ciosc_104:CIOSC-L1-12
  - nist_csf_2:PR.AA-01
  - soc2:CC6.2
  - soc2:CC6.3

requires: [isec.access-control]

declares:
  obligation:
    id: it.account-reconciliation
    activity: Reconcile system accounts against the people who should have them
    cadence: each month
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/account-reconciliations.md
    escalate: {after: 2w, to: information-security-lead}
  register:
    title: Account Reconciliation Record
    note: >
      One row per reconciliation. This is the operational check that runs
      monthly; the quarterly access review in the security programme is the
      governance one that asks whether the access is appropriate. They are
      different questions — does this account belong to a real current person,
      and should that person have this — and an organisation that does only the
      second finds the first by accident.
    layout: form
    review: required
    approvers: [it-manager]
    columns:
      - {key: reconciled_on, label: Reconciled on, type: date, required: true}
      - {key: reconciled_by, label: Reconciled by, type: user, required: true}
      - {key: systems_covered, label: Systems covered, type: longtext, required: true}
      - {key: accounts_total, label: Accounts found, type: int, required: true}
      - {key: accounts_no_owner, label: Accounts with no current owner, type: int, required: true}
      - {key: accounts_leavers, label: Accounts belonging to leavers, type: int, required: true}
      - {key: service_accounts, label: Service and shared accounts, type: int, required: true}
      - {key: service_accounts_owned, label: Of those, with a named owning position, type: int, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: how an account comes to
exist, how it changes when somebody changes role, and how it stops existing.

It must describe joiners, movers and leavers as three separate paths, because
the middle one is where the failure is. A person who has changed role three
times and kept every permission each role needed is how an organisation ends up
with a handful of people who can do anything, and no single decision anybody
made was wrong.

It must name who requests, who approves and who performs, and require that the
request records what the access is for. An access request with no stated
purpose cannot be reviewed later — the reviewer is left asking whether this
person should have this, with nothing to compare it against.

It must set what happens to the account rather than only to the access: disabled
or deleted, when, and what happens to the mailbox, the files and the licences.
Deleting an account on the last day has destroyed evidence more than once;
disabling it and retaining it for a stated period is usually the better rule and
belongs in the retention schedule.

It must require unique identification and forbid shared accounts, then be honest
about the ones that exist anyway. A shared account with a named owning position,
a rotated credential and a record of who is given it is a managed weakness; an
unlisted one is an unattributable action.

It must cover service accounts explicitly. They outlive every person, hold more
privilege than any of them, and belong to nobody by default.
