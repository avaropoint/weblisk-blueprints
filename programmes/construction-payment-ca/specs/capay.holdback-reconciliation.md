---
id: capay.holdback-reconciliation
kind: procedure
title: Holdback Reconciliation
structure: procedure
path: procedures/holdback-reconciliation.md

satisfies:
  - construction_act_ontario:8.1
  - construction_act_ontario:10
  - construction_act_ontario:39

requires: [capay.holdback-account]

declares:
  obligation:
    id: capay.holdback-reconciliation
    activity: Reconcile the holdback account against the ledger, and report what is retained, what is releasable, what is being withheld, and what was not checked
    cadence: each month
    authority: >
      Construction Act s. 8.1 requires a trustee of construction trust money to
      deposit it in a bank account in the trustee's name and to keep written
      records of it; s. 39 entitles a subcontractor to be told the state of
      accounts, including the holdback retained. Neither sets an interval
    interval_basis: chosen
    responsible: finance-lead
    applies_to: the organisation
    records: registers/holdback-reconciliations.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Holdback Reconciliation
    note: >
      One row per period. It is the sweep that catches what the record-origin
      obligations cannot see: a contract with no holdback row at all, a row whose
      substantial performance date was never entered, a release that fell due
      against a date somebody typed wrongly. Those produce no occurrence, so
      without a periodic sweep they produce no signal.
    layout: form
    review: required
    approvers: [finance-lead, senior-management]
    approval_order: sequential
    columns:
      - {key: period, label: Period, type: text, required: true}
      - {key: reconciled_on, label: Reconciled on, type: date, required: true}
      - {key: contracts_in_account, label: Contracts in the account, type: int, required: true}
      - {key: retained_out, label: Holdback we are retaining, type: currency, required: true}
      - {key: retained_from_us, label: Holdback retained from us, type: currency, required: true}
      - {key: ledger_balance, label: Trust ledger balance, type: currency, required: true}
      - {key: variance, label: Variance, type: currency, required: true}
      - {key: releasable_total, label: Falling due in the next ninety days, type: currency, required: true}
      - {key: overdue_total, label: Past due and unreleased, type: currency, required: true}
      - {key: withheld_total, label: Withheld, type: currency, required: true}
      - {key: rows_certified_not_published, label: Certified and not published, type: int, required: true}
      - {key: rows_without_current_clearance, label: Counterparties with no current clearance, type: int, required: true}
      - {key: rows_without_current_insurance, label: Counterparties with no current insurance, type: int, required: true}
      - {key: rows_not_checked, label: Counterparties whose documents were not checked, type: int, required: true}
      - {key: note, label: Note, type: longtext}
---

What this artifact must establish: that once a month somebody compares the
holdback register against the money, and says out loud what does not agree.

**The record-origin obligations in this pack are blind in one direction.** They
raise one occurrence per row, against a date that row carries, which is exactly
right for work that exists because a contract exists — and completely silent
about a contract that was never entered in the register, a date nobody filled in,
or a release date typed a year out. A programme built only from triggers reports
nothing wrong in precisely the cases where nothing is being tracked at all. That
is what this obligation is for, and it is why the chain terminates in a cadence
rather than in another trigger.

**`variance` is the column that makes it a reconciliation.** Two numbers that
were produced by the same person from the same spreadsheet always agree. The
register's total and the trust ledger's balance were produced by different
systems for different purposes, and the difference between them is the finding.
A reconciliation that reports only one number is a report.

**`rows_not_checked` is the most important column here and it is deliberately
not a percentage.** It is the count of counterparties whose documentary state
this organisation does not know — not the ones known to be out of date, the ones
nobody looked at. Every other number on this row is only as good as that one is
small. A month in which forty sub-trades were checked and two were expired is a
good month; a month in which two were checked, both were current, and thirty-eight
were not looked at reports the same "100% current" if the column is missing, and
it is the worse month by a long way.

**`rows_certified_not_published` is the silent-state counter.** It is the number
of contracts carrying a certification date and no publication date — the state in
which everybody believes the lien clock is running and it is not. It belongs on a
monthly report rather than in an alert, because it is not urgent on any particular
day and it is severe cumulatively.

**Why monthly, and why the basis is `chosen`.** The Act requires the records and
requires the information to be given on demand. It sets no interval for either.
Monthly is this organisation's decision, made because that is the cycle its
accounts already run on, and because a quarter is long enough for a wrongly-typed
release date to become a missed statutory deadline.
