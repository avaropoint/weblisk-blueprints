---
id: capay.payment-position
kind: procedure
title: Monthly Payment Position Review
structure: procedure
path: procedures/payment-position-review.md

satisfies:
  - construction_act_ontario:6.9
  - construction_act_ontario:8.1
  - construction_act_ontario:13.5

requires: [capay.prompt-payment, capay.subcontract-payment, capay.lien-administration]

declares:
  obligation:
    id: capay.payment-position-review
    # A CADENCE, and it terminates both prompt payment chains.
    #
    # Every trigger in this programme fires off a date column that is EMPTY
    # until something happens — the owner pays, the invoice is received, the
    # lien is preserved. An empty date raises no occurrence, which is correct
    # and completely silent, and a contract nobody entered in the register is
    # silent in exactly the same way. Only a periodic sweep of the whole account
    # can tell the two apart, and only a sweep can count what was never looked
    # at.
    activity: Review the whole payment position — what is owed to us, what we owe, and what was not checked
    cadence: each month
    authority: >
      The Construction Act requires the trust records to be maintained and
      requires information to be given on request; it sets no interval for a
      review of the account. The monthly cycle is this organisation's
    interval_basis: chosen
    responsible: finance-lead
    applies_to: the organisation
    records: registers/payment-position-reviews.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Payment Position Review Record
    note: >
      One row per monthly sweep, not one per invoice. Every figure is a count,
      and the last one governs the value of all the others: how many contracts
      and invoices were **not checked at all**. A hundred per cent current
      because everything was examined and a hundred per cent current because
      nothing was are the same number and opposite facts.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: period, label: Period, type: text, required: true}
      # ── money owed to us ──────────────────────────────────────────────────
      - {key: invoices_given, label: Proper invoices given in the period, type: int, required: true}
      - {key: given_paid_on_time, label: Paid in full by the due date, type: int, required: true}
      - {key: given_with_notice, label: Answered with a notice of non-payment, type: int, required: true}
      - {key: given_overdue_no_notice, label: Overdue with neither payment nor notice, type: int, required: true}
      - {key: receivable_overdue_value, label: Value overdue, type: currency, required: true}
      - {key: interest_accrued, label: Interest accrued and not claimed, type: currency, required: true}
      # ── money we owe ──────────────────────────────────────────────────────
      - {key: invoices_received, label: Proper invoices received in the period, type: int, required: true}
      - {key: received_paid_within_seven_days, label: Paid within seven days of our being paid, type: int, required: true}
      - {key: received_with_notice, label: Answered with a notice of non-payment, type: int, required: true}
      - {key: received_overdue_no_notice, label: Payable, unpaid, and no notice given, type: int, required: true}
      - {key: payable_overdue_value, label: Value payable and overdue, type: currency, required: true}
      - {key: trust_account_reconciled, label: The trust account and the written trust record reconcile, type: bool, required: true}
      - {key: trust_variance, label: Variance, and what it is, type: longtext}
      # ── disputes and security ─────────────────────────────────────────────
      - {key: liens_open, label: Liens open, type: int, required: true}
      - {key: liens_inside_thirty_days_of_a_deadline, label: Liens within thirty days of a statutory deadline, type: int, required: true}
      - {key: adjudications_live, label: Adjudications live, type: int, required: true}
      - {key: adjudication_determinations_unpaid, label: Determinations unpaid past fifteen days, type: int, required: true}
      - {key: information_requests_open, label: Requests for information open, and the oldest, type: text, required: true}
      # ── the count that governs the rest ───────────────────────────────────
      - {key: contracts_not_checked, label: Contracts in the account not examined this period, type: int, required: true}
      - {key: invoices_not_entered, label: Invoices known to exist and not entered in a register, type: int, required: true}
      - {key: what_was_not_looked_at, label: What was not looked at, and why, type: longtext, required: true}
      - {key: actions, label: Actions raised, type: longtext}
---

What this document must establish for THIS organisation: once a month, the whole
picture — what is owed to it, what it owes, what is in dispute, and what nobody
looked at.

**It exists because every other obligation in this programme is triggered by a
date that starts empty.** The owner pays, or does not. The invoice is entered, or
is not. The lien is preserved, or nobody hears about it. A trigger on an empty
column raises no work, which is right, and is also the same silence as a contract
that was never recorded. The sweep is the only thing in the programme that can
see an absence.

It must produce the counts **in both directions in one place**. An organisation
that reviews receivables in one meeting and payables in another has no view of
the thing that actually kills construction companies: money received and not
passed on, while money owed and not received is being carried. Those two numbers
belong on one row, in one month, read by one person.

It must reconcile **the trust account against the written trust record**, and
must record a variance as a variance rather than as a reconciling item to be
looked at later. The trust records are a statutory duty and the personal
liability that sits behind them does not wait for the year end.

It must count **interest accrued and not claimed**. Interest on late payment runs
automatically, with no demand required. An organisation that never records it has
decided not to claim it without anybody deciding, and has established a course of
dealing it will later be held to.

It must flag **liens inside thirty days of a statutory deadline** as a count of
its own, separate from liens open. A lien open for three weeks and a lien open
for eighty days need completely different attention, and a single "liens open"
figure gives them the same.

It must count **determinations unpaid past fifteen days**, because an
adjudicator's determination that has not been paid is enforceable and because
this organisation is as likely to be the party that has not paid one as the party
waiting.

**The last three columns are the point of the review and they must be filled in
before the others are believed.** Contracts not examined, invoices known to exist
and not entered, and a sentence saying what was not looked at and why. Every
other figure on this row is a statement about the records; those three are the
statement about the records' completeness, and without them a clean month and an
unexamined month produce the same report.

**The monthly interval is this organisation's choice.** Nothing in the Act
requires this review. A month is chosen because it matches the invoicing cycle
the Act itself assumes, and because the shortest statutory clock in the
programme — seven days — is already too short for a sweep to catch: the sweep
exists to find what the triggers could not raise, not to do their work.
