---
id: capay.subcontract-payment
kind: procedure
title: Paying Down the Chain, and the Trust
structure: procedure
path: procedures/subcontract-payment.md

satisfies:
  - construction_act_ontario:6.5
  - construction_act_ontario:6.7
  - construction_act_ontario:8
  - construction_act_ontario:8.1
  - construction_act_ontario:10
  - construction_act_ontario:13

requires: [capay.policy, capay.holdback-account]

approved_by: [senior-management]

declares:
  obligation:
    id: capay.subcontractor-payment
    # Record-origin, triggered by the date the organisation was PAID rather than
    # by the date the invoice arrived. That is the Act's own trigger, and it is
    # also the honest one: the duty is to pass on money received.
    #
    # The trigger column is empty until the owner pays, so no occurrence is
    # raised before then. That silence is correct and it is also indistinguishable
    # from an invoice nobody recorded — which is why the chain terminates in the
    # monthly payment position review rather than here.
    activity: Pay each subcontractor whose work was included in the invoice this organisation was paid for, or give a notice of non-payment
    for:
      records: registers/proper-invoices-received.md
      due: 7d after owner_paid_on
      key: invoice_id
    authority: >
      Construction Act s. 6.5 (1) — a contractor who receives full payment of a
      proper invoice shall, no later than seven days after receiving payment, pay
      each subcontractor whose services or materials were included in that
      invoice; s. 6.5 (4) applies the same seven days to a partial payment
    interval_basis: required
    responsible: finance-lead
    applies_to: the organisation
    records: registers/subcontract-payments.md
    escalate: {after: 3d, to: senior-management}
  register:
    title: Subcontract Payment Record
    note: >
      One row per invoice that became payable, keyed by the invoice. It records
      the payment, or the notice of non-payment that stood in its place, and
      **who decided**. A breach of trust reaches individuals personally, and the
      only thing that distinguishes a decision from a drift is a name against it.
    layout: form
    review: required
    approvers: [finance-lead]
    columns:
      - {key: invoice_id, label: Invoice, type: relation, required: true,
         target: /registers/proper-invoices-received.md#records, display: invoice_id}
      - {key: actioned_on, label: Actioned on, type: date, required: true}
      - {key: actioned_by, label: Actioned by, type: user, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Paid in full within seven days, Paid in part within seven days,
                   Notice of non-payment given within the prescribed time,
                   "Paid late", "Not paid and no notice given"]}
      - {key: amount_received_for_this_work, label: Amount we received on account of this work, type: currency, required: true}
      - {key: amount_paid, label: Amount paid on, type: currency, required: true}
      - {key: holdback_retained, label: Holdback retained, type: currency, required: true}
      - {key: amount_withheld, label: Amount withheld, type: currency, required: true}
      - {key: withholding_reason, label: Reason, in the terms the notice gave, type: longtext}
      - {key: notice_form_used, label: The prescribed form was used, type: select,
         options: [Not applicable, "Yes", "No"]}
      - {key: paid_from_trust_account, label: Paid from the account holding the trust funds, type: bool, required: true}
      - {key: trust_record_updated, label: The written trust record was updated, type: bool, required: true}
      - {key: documents_current, label: Clearance certificate and insurance current at the date of payment, type: select, required: true,
         options: ["Both current", "Clearance not current", "Insurance not current", "Neither current", Not checked]}
      - {key: decided_by, label: Decided by, type: user, required: true}
---

What this document must establish for THIS organisation: how money received for
somebody else's work reaches that person, within the days the Act allows, out of
the account the Act requires it to be in.

It must state the **trust** first, because everything else in this procedure is a
consequence of it. Amounts owing to and received by a contractor on account of
the contract price — **including holdback** — are a trust fund for the benefit of
the subcontractors and suppliers who have not been paid. The organisation is the
trustee. Paying a subcontractor is not a discretionary commercial act; it is the
discharge of a trust, and it discharges the trust only to the extent of the
payment made.

It must state the **account and the records** duty concretely, because it is the
one that is silently not done. Trust funds are deposited into a bank account in
the trustee's name, and written records are maintained detailing amounts
received into and paid out of the trust, transfers made for its purposes, and
the other prescribed information. Funds of more than one trust may share an
account only on the conditions the section sets. An organisation running a single
operating account with no trust ledger is in breach every day, and has no defence
available to it when a subcontractor is not paid.

It must name the **personal liability**, without softening it. Every director or
officer, and any person with effective control of the corporation or its
relevant activities — including an employee or agent — is liable in an action for
breach of trust where they assent to or acquiesce in conduct they know or
reasonably ought to know is a breach. The people who approve the payment run are
the people exposed. The document must say so plainly and must say it to them.

It must set out the **seven-day clock and its trigger**. It runs from receipt of
payment, not from receipt of the invoice, and it applies to each subcontractor
whose services or materials were included in the invoice that was paid. Where
the owner pays only part, the subcontractors are paid from what was received,
within the same seven days, in the order the section and the contract require.
The organisation must know which subcontract invoices rolled up into which
invoice to the owner, and the register beside this one is where that is written
down.

It must set out the **notice of non-payment**: when it may be given, in what
form, within what time, and that it must specify the amount and detail the
reasons. It must distinguish a notice passed down because the owner did not pay
— which has its own form and timing and may require an undertaking to refer the
matter to adjudication — from a notice given on the organisation's own grounds.
Those are different documents and conflating them loses the protection of both.

It must be explicit that **reasons for non-payment may include set-off** under
the trust set-off and lien set-off provisions, and that this is narrower than
the general commercial right of set-off an organisation may believe it has.

It must say what the organisation does about **documentary conditions** —
clearance certificates, certificates of insurance, WSIB standing. Those are
conditions precedent under most subcontracts and they are **not** grounds the
Act provides. They may support a contractual withholding; they do not suspend
the statutory clock, and they are never a reason to withhold statutory holdback.
The column on the record exists so that a payment made with a documentary gap is
a decision somebody made, on the record, on the day.

**Seven days is the Act's.** The three-day escalation to senior management is
this organisation's, and it is short because the exposure is personal and
because a payment run that has already been missed once will be missed again at
the next cycle.
