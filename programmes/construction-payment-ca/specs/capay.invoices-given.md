---
id: capay.invoices-given
kind: register
title: Register of Proper Invoices Given
structure: standard
path: registers/proper-invoices-given.md

# A register carries no `satisfies:`. The citation belongs on the procedure that
# governs how invoices are given and what is done when payment does not arrive;
# this file is where each invoice and its clock are recorded.

requires: [capay.prompt-payment]

register:
  title: Register of Proper Invoices Given
  note: >
    One row per proper invoice this organisation gives to an owner or to a
    payer above it. It is the **date of receipt by the payer** that starts the
    clock, so that column is required and is separate from the invoice date:
    an invoice dated the 30th and delivered on the 4th is due on a day nobody
    can work out from the invoice.

    `is_proper` is a required select and not a tick, because almost every
    dispute about prompt payment is really a dispute about whether the document
    was a proper invoice at all. An invoice missing a prescribed particular does
    not start the clock, and an organisation counting twenty-eight days from a
    document that was never proper is counting from nothing.
  layout: form
  columns:
    - {key: invoice_id, label: Invoice number, type: text, required: true}
    - {key: holdback, label: Contract, type: relation, required: true,
       target: /registers/holdback-account.md#records, display: holdback_id}
    - {key: project, label: Project, type: relation,
       target: /registers/projects.md#records, display: project_id}
    - {key: payer, label: Payer, type: text, required: true}
    - {key: period, label: Period or milestone it relates to, type: text, required: true}
    - {key: invoice_date, label: Date of the invoice, type: date, required: true}
    - {key: given_on, label: Received by the payer on, type: date, required: true}
    - {key: delivery_evidence, label: How receipt is evidenced, type: text, required: true}
    - {key: amount, label: Amount claimed, type: currency, required: true}
    - {key: holdback_shown, label: Holdback shown separately, type: currency, required: true}
    - {key: is_proper, label: Is it a proper invoice, type: select, required: true,
       options: [Yes — every prescribed particular is present,
                 "No — a particular is missing, and it is named",
                 Not yet checked]}
    - {key: proper_gaps, label: What is missing or disputed, type: longtext}
    - {key: certification_condition_asserted, label: The payer asserts payment is conditional on certification or approval, type: bool, required: true}
    - {key: payment_due_on, label: Payment falls due on, type: date, required: true}
    - {key: notice_deadline_on, label: The payer's notice of non-payment is due by, type: date, required: true}
    - {key: notice_received_on, label: Notice of non-payment received on, type: date}
    - {key: notice_in_prescribed_form, label: The notice was in the prescribed form and gave reasons, type: select,
       options: ["Yes", "No", Not applicable]}
    - {key: amount_withheld, label: Amount the payer says it will not pay, type: currency}
    - {key: paid_on, label: Paid on, type: date}
    - {key: amount_paid, label: Amount paid, type: currency}
    - {key: interest_accruing_from, label: Interest accruing from, type: date}
    - {key: status, label: Status, type: select, required: true,
       options: [Given, Paid in full, Paid in part, Notice of non-payment received,
                 Overdue with no notice, Referred to adjudication, Lien preserved, Written off]}
---

What this artifact must establish: every request for payment this organisation
has made under a construction contract, the day the payer received it, and the
two dates that follow from that day and from nothing else.

**The two dates are the whole register.** Twenty-eight days to pay, fourteen days
to give a notice of non-payment, both counted from receipt of a proper invoice.
They are the only dates in this programme that the organisation does not control
and cannot negotiate after the fact, and an organisation that does not know them
per invoice discovers a late payment as a cash flow problem months later rather
than as a breach on the day.

**`overdue with no notice` is the status that matters.** A payer who pays late
is a commercial problem. A payer who neither pays within twenty-eight days nor
gives a notice of non-payment within fourteen is in a different position
entirely: interest runs automatically with no demand required, and the dispute
can be referred to adjudication. Most organisations never notice the difference,
because their accounts receivable ageing shows one number for both.

**`certification_condition_asserted` is a column because the clause is common and
is of no force.** A contract provision making the giving of a proper invoice
conditional on the prior certification of a payment certifier or on the owner's
prior approval does not operate. Contracts still contain them, payers still
invoke them, and the organisation's own staff still wait for a certificate
before invoicing — which delays the only clock that protects them. Recording the
assertion is how the pattern becomes visible across a payer rather than being
argued once per invoice.

**`is_proper` is checked before the invoice is given, not after it is disputed.**
The prescribed particulars are short, they are the same every month, and a
missing one hands the payer the whole argument. The procedure should carry the
checklist; this column records that somebody applied it.

**It joins to the holdback account by contract, not by project.** A project with
nine subcontracts has nine sets of payment clocks, and the ten per cent retained
against this invoice belongs to this contract's own holdback and its own
release date. `holdback_shown` is separate from `amount` for the same reason the
holdback account exists: the holdback is documentation expressed as money, and
an invoice that does not show it cannot be reconciled against the account.
