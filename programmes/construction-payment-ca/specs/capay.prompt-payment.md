---
id: capay.prompt-payment
kind: procedure
title: Prompt Payment — Invoicing and Collection
structure: procedure
path: procedures/prompt-payment.md

satisfies:
  - construction_act_ontario:6.1
  - construction_act_ontario:6.3
  - construction_act_ontario:6.4
  - construction_act_ontario:6.9
  - construction_act_ontario:39

requires: [capay.policy, capay.holdback-account]

approved_by: [senior-management]

declares:
  obligation:
    id: capay.owner-payment-outcome
    # Record-origin. Twenty-eight days after the PAYER RECEIVED the invoice is
    # the statutory deadline, and it is the day the organisation must know one
    # of exactly three things: paid, notice given, or neither. "Neither" is the
    # one with consequences and the one nobody currently looks for.
    activity: Confirm what the payer did with a proper invoice by the day it fell due
    for:
      records: registers/proper-invoices-given.md
      due: 28d after given_on
      key: invoice_id
    authority: >
      Construction Act s. 6.4 (1) — an owner shall pay the amount payable under a
      proper invoice no later than 28 days after receiving it, subject to a notice
      of non-payment given no later than 14 days after receiving it
    interval_basis: required
    responsible: contract-administrator
    applies_to: the organisation
    records: registers/owner-payment-outcomes.md
    escalate: {after: 7d, to: finance-lead}
  register:
    title: Payment Outcome Record
    note: >
      One row per invoice that reached its due date, keyed by the invoice.
      Three outcomes and no fourth: paid, a notice of non-payment was given, or
      neither happened. The third is recorded as an outcome rather than as an
      absence, because an absence looks identical to nobody having checked — and
      it is the only one of the three that starts interest running and opens
      adjudication.
    layout: form
    review: required
    approvers: [finance-lead]
    columns:
      - {key: invoice_id, label: Invoice, type: relation, required: true,
         target: /registers/proper-invoices-given.md#records, display: invoice_id}
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: outcome, label: What the payer did, type: select, required: true,
         options: [Paid in full by the due date, Paid in part with a notice of non-payment,
                   Nothing paid, with a notice of non-payment,
                   "Nothing paid and no notice given", Paid late]}
      - {key: amount_outstanding, label: Amount outstanding, type: currency, required: true}
      - {key: notice_assessed, label: If a notice was given, is it in the prescribed form and does it give reasons, type: select,
         options: [Not applicable, "Yes", "No — and the defect is recorded"]}
      - {key: set_off_claimed, label: Set-off claimed, and on what basis, type: longtext}
      - {key: interest_claimed_from, label: Interest claimed from, type: date}
      - {key: interest_rate_basis, label: Rate applied, and why, type: text}
      - {key: action, label: What was decided, type: select, required: true,
         options: [Nothing — paid, Chase and re-present, Written demand sent,
                   Notice of adjudication being prepared, Lien to be preserved,
                   Accepted commercially, with the reason recorded]}
      - {key: decided_by, label: Decided by, type: user, required: true}
      - {key: reason, label: Reason, type: longtext, required: true}
---

What this document must establish for THIS organisation: how it gets paid on
time under the Act, and what it does on the day it is not.

It must carry **the proper invoice checklist**, in the organisation's own
invoice format, so that the particulars the Act prescribes are present every
time: the contractor's name and address, the date of the invoice and the period
or milestone it relates to, the information the subsection requires, and
whatever further requirements the contract adds. A document that is not a proper
invoice does not start the clock, and the whole of Part I.1 rests on that one
fact. The checklist is short; not having it is expensive.

It must say that **invoices are given monthly unless the contract provides
otherwise**, and that a contract term making a proper invoice conditional on
prior certification or the owner's prior approval is **of no force or effect**.
The document must tell the organisation's own staff not to hold the invoice
waiting for a certificate — that is the single most common way a contractor
volunteers away the protection the Act gave it.

It must define the **three outcomes at twenty-eight days** and what each one
requires. Paid: nothing. A notice of non-payment in the prescribed form, within
fourteen days, specifying the amount and detailing the reasons: the dispute is
live and the undisputed balance should still have been paid. Neither payment nor
notice: **interest runs automatically, with no demand required**, and the matter
may be referred to adjudication. The document must name who decides which of
those is pursued, and by when.

It must state the **interest rate rule** and require it to be applied rather than
waived by habit. Interest accrues at the prejudgment rate under the Courts of
Justice Act or, where the contract specifies a rate for the purpose, at the
greater of the two. Organisations routinely do not claim it, then find that not
claiming it is treated as their practice.

It must say what happens to **the undisputed balance**. A notice of non-payment
covers the amount the payer says it will not pay and specifies it; the rest is
still due on the same clock. A payer withholding the entire invoice over a
disputed item is not complying with the section, and the organisation should
recognise that on the record rather than in a phone call.

It must cover **the request for information**. A person with a lien, a trust
beneficiary or a mortgagee may require, in writing, information about the
contract — the parties, the date it was entered into, the date the procurement
process began, the contract price and further particulars — to be provided
within a reasonable time **not exceeding twenty-one days**. This organisation
both makes and receives those requests, and the document must say who answers
one and where the answer is recorded, because the deadline is short and the
request usually arrives addressed to nobody in particular.

It must say what is **not** in this document. The holdback is retained and
released under its own procedure and on its own clock; a disputed invoice is not
a reason to withhold statutory holdback, and a holdback is not a reason to pay
an invoice late.

**Twenty-eight days is the Act's, and the record says so.** The seven-day
escalation to the finance lead is this organisation's: an invoice that is
overdue with no notice, and that nobody has decided about within a week of
falling due, is one that will be decided about by default.
