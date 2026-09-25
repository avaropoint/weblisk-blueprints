---
id: capay.invoices-received
kind: register
title: Register of Proper Invoices Received
structure: standard
path: registers/proper-invoices-received.md

# A register carries no `satisfies:`. The citation belongs on the procedure that
# governs paying down the chain; this file is where each invoice received and
# the clock it starts are recorded.

requires: [capay.subcontract-payment]

register:
  title: Register of Proper Invoices Received
  note: >
    One row per proper invoice received from a subcontractor or supplier. Two
    date columns drive everything and they are different clocks: `received_on`
    is when the organisation got the invoice, and `owner_paid_on` is when the
    organisation was paid for the work that invoice covers. The seven-day duty to
    pay a subcontractor runs from the **second** of those, and an organisation
    that counts from the first will pay early and one that has no column for it
    will pay late without knowing which.

    `owner_paid_on` is empty until it happens, and an empty date raises no work.
    That silence is real and is the reason the monthly payment position review
    exists: an invoice nobody has been paid for and an invoice nobody entered
    look identical from here.
  layout: form
  columns:
    - {key: invoice_id, label: Invoice number, type: text, required: true}
    - {key: subcontractor, label: Subcontractor or supplier, type: text, required: true}
    - {key: holdback, label: Subcontract, type: relation, required: true,
       target: /registers/holdback-account.md#records, display: holdback_id}
    - {key: project, label: Project, type: relation,
       target: /registers/projects.md#records, display: project_id}
    - {key: received_on, label: Received on, type: date, required: true}
    - {key: period, label: Period or milestone it relates to, type: text, required: true}
    - {key: amount, label: Amount claimed, type: currency, required: true}
    - {key: holdback_retained, label: Holdback to be retained, type: currency, required: true}
    - {key: is_proper, label: Is it a proper invoice, type: select, required: true,
       options: [Yes — every prescribed particular is present,
                 "No — a particular is missing, and it is named",
                 Not yet checked]}
    - {key: included_in_our_invoice, label: Included in our invoice to the owner, type: relation,
       target: /registers/proper-invoices-given.md#records, display: invoice_id}
    - {key: owner_paid_on, label: We were paid for this work on, type: date}
    - {key: owner_paid_in_full, label: Paid in full by the owner, type: select, required: true,
       options: [Not yet paid, In full, In part, Refused with a notice of non-payment]}
    - {key: subcontract_payment_due_on, label: Payment to the subcontractor falls due on, type: date}
    - {key: our_notice_deadline_on, label: Our notice of non-payment is due by, type: date}
    - {key: our_notice_given_on, label: Notice of non-payment given on, type: date}
    - {key: amount_withheld, label: Amount we are not paying, type: currency}
    - {key: withholding_basis, label: Basis for withholding, type: select,
       options: [Not withholding, "Owner did not pay — notice passed down",
                 Set-off under the trust provisions, Lien set-off,
                 Defective or incomplete work, Documents not current]}
    - {key: paid_on, label: Paid on, type: date}
    - {key: amount_paid, label: Amount paid, type: currency}
    - {key: status, label: Status, type: select, required: true,
       options: [Received, Awaiting payment from the owner, Payable — clock running,
                 Paid in full, Paid in part, Notice of non-payment given,
                 "Overdue with no notice", In dispute]}
---

What this artifact must establish: every request for payment made to this
organisation under a subcontract, what it was for, whether the organisation has
itself been paid for that work, and the day the money must move.

**`overdue with no notice` on this register is the organisation's own exposure,
and it is worse than the same status on the register above.** Amounts received
on account of a contract price are trust funds for the benefit of the people who
supplied the services and materials. A director or officer — and any person with
effective control who assents to or acquiesces in it — is **personally liable**
for a breach of that trust. Paying a subcontractor late out of money already
received for that subcontractor's work is not only a prompt payment
contravention; it is the fact pattern the trust provisions exist to reach, and
the liability does not stop at the corporation.

**`included_in_our_invoice` is a relation and it is the join the Act's chain
depends on.** The seven-day duty attaches to the subcontractors whose services
or materials were included in the proper invoice the organisation was paid for.
Where the owner pays only part, the contractor must still pay subcontractors
out of what it received, on the same clock. That calculation cannot be done at
all without knowing which subcontract invoices rolled up into which invoice to
the owner, and most organisations hold that mapping in one person's spreadsheet.

**`withholding_basis` is a closed list and one of its options is a trap worth
naming.** "Owner did not pay — notice passed down" is legitimate and has its own
prescribed form and timing, and it is not the same as simply not paying. The
other bases are the organisation's own and stand or fall on their own merits.
"Documents not current" — an expired clearance certificate or certificate of
insurance — is a contractual condition under most subcontracts and is **not a
statutory ground**; the release procedure beside this one makes that decision
attributable rather than automatic, and this column records which kind of
decision was made.

**`is_proper` matters as much here as on an invoice given, and in the opposite
direction.** An invoice from a subcontractor that is not proper does not start a
clock — but treating a proper invoice as improper in order to buy time is the
manoeuvre the section was written against, and a register that records the
judgement makes it reviewable.
