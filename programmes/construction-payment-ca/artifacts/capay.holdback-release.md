---
id: capay.holdback-release
kind: procedure
title: Holdback Release
structure: procedure
path: procedures/holdback-release.md

satisfies:
  - construction_act_ontario:22
  - construction_act_ontario:26
  - construction_act_ontario:27
  - construction_act_ontario:39

requires: [capay.holdback-account, capay.insurance-certificates, cohs.clearance-certificates]

declares:
  obligation:
    id: capay.holdback-release
    activity: Release the holdback that has fallen due, or record who decided not to and on what grounds
    for:
      records: registers/holdback-account.md
      due: 14d before release_due_on
      key: holdback_id
    authority: >
      Construction Act ss. 22, 26 and 27 — the holdback is retained until the
      liens it secures have expired or been satisfied, discharged or otherwise
      provided for, and is then paid; s. 26 requires a release following each
      anniversary of the date the contract was entered into. The Act sets the
      date the money falls due. The fourteen days of warning before it is this
      organisation's own
    interval_basis: chosen
    responsible: finance-lead
    applies_to: the organisation
    records: registers/holdback-releases.md
    escalate: {after: 1w, to: senior-management}
  register:
    title: Holdback Release Record
    note: >
      One row per release that fell due, whether or not it was paid. A row is
      raised by the date arriving, not by somebody deciding to pay — which is
      what makes a release that was quietly not made visible instead of absent.
    layout: form
    review: required
    approvers: [contract-administrator, finance-lead]
    approval_order: sequential
    columns:
      - {key: holdback_id, label: Holdback, type: relation, required: true,
         target: /registers/holdback-account.md#records, display: holdback_id}
      - {key: counterparty, label: Counterparty, type: text, required: true}
      - {key: amount_due, label: Amount falling due, type: currency, required: true}
      - {key: release_due_on, label: Fell due on, type: date, required: true}
      - {key: basis, label: Why it fell due, type: select, required: true,
         options: [Liens expired after publication of substantial performance,
                   Anniversary of the contract, Subcontract certified complete,
                   Finishing holdback, Phased release under the contract]}
      - {key: liens_expired, label: Liens against this holdback have expired or been provided for, type: bool, required: true}
      - {key: lien_preserved, label: A lien has been preserved or perfected against this holdback, type: bool, required: true}
      - {key: notice_of_non_payment_given, label: A notice of non-payment was given in the prescribed form and time, type: bool, required: true}
      - {key: clearance, label: Clearance certificate relied on, type: relation,
         target: /registers/clearance-certificates.md#records, display: reference}
      - {key: clearance_current, label: A valid clearance certificate was held on this date, type: bool, required: true}
      - {key: insurance, label: Insurance certificate relied on, type: relation,
         target: /registers/insurance-certificates.md#records, display: policy_number}
      - {key: insurance_current, label: The required coverage was in force on this date, type: bool, required: true}
      - {key: deliverables_outstanding, label: Contract close-out deliverables still outstanding, type: bool, required: true}
      - {key: documents_checked_on, label: Documents checked on, type: date, required: true}
      - {key: documents_checked_by, label: Documents checked by, type: user, required: true}
      - {key: decision, label: Decision, type: select, required: true,
         options: [Released in full, Released in part,
                   Released with a documentary gap accepted,
                   Withheld — lien preserved,
                   Withheld — notice of non-payment given,
                   Withheld — contractual condition not met,
                   Not yet decided]}
      - {key: decided_by, label: Decided by, type: user, required: true}
      - {key: amount_released, label: Amount released, type: currency, required: true}
      - {key: paid_on, label: Paid on, type: date}
      - {key: grounds, label: Grounds, type: longtext}
---

What this artifact must establish: that on the day a holdback fell due, somebody
named looked at what the money was being paid against, made a decision, and
recorded the grounds for it.

**This is where the programme stops being about paperwork and starts being about
money.** Everything else in this pack and in the health and safety programme
beside it — clearances, insurance certificates, training records, sign-offs — is
documentation somebody chases. A holdback release is the moment that
documentation becomes irreversible: once the ten per cent is paid, the
organisation's leverage over the sub-trade is gone, and so is most of its ability
to recover anything the paperwork would have protected it from.

## Say precisely what the gate is, because getting this wrong is a breach

The Construction Act requires the holdback to be **paid** once the conditions in
ss. 26 and 27 are met. Withholding it is permitted only in the circumstances the
Act prescribes and by the notices it prescribes — a preserved lien, a notice of
non-payment in the prescribed form and within the prescribed time. **"The
sub-trade's clearance certificate has expired" is not one of them.** A procedure
that told somebody otherwise would be instructing them to breach the Act and to
start interest running against their own company.

What the documentary state *is* is two other things, and both are worth more
than the withholding right would have been:

- **A condition precedent to payment under the subcontract.** Most subcontracts
  make current evidence of clearance and insurance a condition of *any* payment,
  which is a contractual right with its own notice requirements — not a right to
  ignore the statutory clock, but a live question at exactly this moment.
- **An exposure that does not end when the money moves.** A principal who pays
  out to a contractor without a valid clearance certificate may be left liable
  for that contractor's unpaid workers' compensation premiums, up to the labour
  portion of the contract. That liability survives the payment. Releasing the
  holdback is the last moment at which it can be priced, and the first moment at
  which it can no longer be set off.

So this procedure does not block a release. **It forces the decision to be
attributable.** `Released with a documentary gap accepted` is a first-class
outcome, it requires `decided_by` and `grounds`, and it goes through the same
sequential approval as any other. An organisation that pays anyway has made a
commercial judgement, which is legitimate; an organisation that pays anyway and
has no record of who made it has an exposure with nobody's name on it.

## Why the row exists before the decision does

The occurrence is raised fourteen days before `release_due_on`, from the holdback
account, one per holdback. It is not raised by somebody opening the register and
deciding to pay. That ordering is the whole mechanism: a release that nobody made
produces an overdue occurrence with a counterparty's name on it, where a release
that is simply never entered produces nothing at all. `Not yet decided` exists so
that the row can be filed on time and honestly while the decision is still open —
the alternative is that somebody picks a decision to make the form submit.

`liens_expired` and `lien_preserved` are both required booleans and they are not
each other's inverse. "All liens have expired" and "a lien has been preserved"
can both be false — which is the ordinary state of a contract mid-course — and a
single field would force somebody to assert one of them.

## The number this register makes answerable

Because every release carries `clearance_current`, `insurance_current` and
`documents_checked_on`, the proportion of releases made against current
documentation is a figure that can be read off the register per counterparty and
overall. It must always be reported with the count of releases where the
documents were **not checked at all**, and that count must never be folded into
the compliant side. A hundred per cent because everything was checked and a
hundred per cent because nothing was are the same number and opposite facts.

It is submitted as a form and approved sequentially — the contract administrator
first, because they are the one who can say what the subcontract requires, then
finance, because they are the one who moves the money. A grid would commit every
keystroke, so a half-entered release would report money as paid before anybody
said so.
