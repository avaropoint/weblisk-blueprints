---
id: rec.legal-hold
kind: procedure
title: Legal Hold
structure: procedure
path: procedures/legal-hold.md

satisfies:
  - iso_27001:A.5.31
  - iso_27001:A.5.28
  - iso_27001:A.5.33
  - soc2:C1.2

requires: [rec.policy]

declares:
  obligation:
    id: rec.hold-review
    activity: Review an active legal hold — still needed, still complete, still known to the custodians
    for:
      records: registers/legal-holds.md
      due: 14d before review_due
      key: reference
    responsible: records-manager
    applies_to: the organisation
    records: registers/legal-hold-reviews.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Legal Hold Review Record
    note: >
      One row per review of one hold, keyed by its reference.
      `custodians_changed` is the column that finds the real failure: people
      leave, and a hold whose custodian list has not been revisited is a hold
      over records nobody current knows to preserve.
    layout: form
    review: required
    approvers: [records-manager]
    columns:
      - {key: reference, label: Hold, type: relation, required: true,
         target: /registers/legal-holds.md#records, display: matter}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: still_required, label: Still required, type: bool, required: true}
      - {key: scope_changed, label: Scope changed, type: bool, required: true}
      - {key: custodians_changed, label: Custodians changed since issue, type: bool, required: true}
      - {key: custodians_renotified, label: Custodians re-notified, type: bool, required: true}
      - {key: deletion_still_suspended, label: Automated deletion still suspended, type: bool, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Continue, Continue with a wider scope, Continue with a narrower scope, Release]}
      - {key: next_review, label: Next review due, type: date, required: true}
---

What this document must establish for THIS organisation: who may impose a hold,
what happens within the hour, and how it is lifted.

It must state the trigger as anticipation rather than service. The duty to
preserve arises when litigation, an investigation or a regulatory proceeding is
reasonably foreseeable, which is usually weeks before anything is served — a
serious incident, a dismissal likely to be challenged, a formal complaint, a
regulator's questions.

It must name who may issue one and require it to be issued in writing to named
custodians, telling them what to preserve, that they must not delete, and who to
ask if unsure. It must also require the automated deletion to be suspended by
somebody technical, because that is a separate act from notifying people and the
people cannot do it.

It must say who may release a hold, and that release is a decision recorded
rather than an absence of activity. A hold that simply stops being mentioned
leaves the organisation both unable to dispose and unable to say why.

It must interact with the disposition procedure in one direction only: a hold
stops a disposal, and a scheduled disposal never overrides a hold. The
disposition record's `hold_checked` column is the enforcement point.

It must cover what happens when a person under hold leaves. Their mailbox and
files are exactly the material at issue, the leaver process is designed to remove
them, and the two procedures have to agree in writing about which wins.

Fourteen days before the review date. A hold review usually needs a conversation
with counsel, and one that opens on the day it is due becomes a rubber stamp.
