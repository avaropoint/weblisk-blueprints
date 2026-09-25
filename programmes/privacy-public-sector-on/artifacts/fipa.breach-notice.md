---
id: fipa.breach-notice
kind: procedure
title: Notifying the Institution of a Breach
structure: procedure
path: procedures/notifying-the-institution.md

satisfies:
  - fippa_mfippa:FM-10
  - fippa_mfippa:FM-06

requires: [fipa.flow-down, priv.breaches]

declares:
  obligation:
    id: fipa.institution-notification
    # Record-origin from the same breach register the privacy programme uses.
    # The duty here is to the institution rather than to the individual or the
    # regulator: the institution holds the statutory notification duty and
    # cannot discharge it until it has been told.
    activity: Notify the institution of a breach involving its records
    for:
      records: registers/privacy-breaches.md
      due: 24h after discovered_on
      key: reference
    authority: The institution's contract — notification periods are contractual and are usually shorter than any statutory one
    interval_basis: required
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/institution-breach-notifications.md
    escalate: {after: 24h, to: senior-management}
  register:
    title: Institution Breach Notification Record
    note: >
      One row per breach involving an institution's records, keyed by the breach
      reference. `contract_period` is recorded beside `notified_within` because
      the deadline is different for every institution, and a notification that
      was prompt by the organisation's standards and late by the contract's is
      a breach of the contract as well as of the safeguards.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: reference, label: Breach, type: relation, required: true,
         target: /registers/privacy-breaches.md#records, display: reference}
      - {key: institution, label: Institution, type: text, required: true}
      - {key: notified_on, label: Notified on, type: date, required: true}
      - {key: notified_by, label: Notified by, type: user, required: true}
      - {key: contact, label: Who at the institution was told, type: text, required: true}
      - {key: contract_period, label: Notification period the contract requires, type: text, required: true}
      - {key: notified_within, label: Notified within the contractual period, type: bool, required: true}
      - {key: records_affected, label: Institutional records affected, type: longtext, required: true}
      - {key: institution_direction, label: Direction received from the institution, type: longtext, required: true}
      - {key: containment, label: Containment and recovery, type: longtext, required: true}
---

What this document must establish for THIS organisation: who at the institution
is told when its records are involved in a breach, and how fast.

It must be clear about whose duty is whose. The institution holds the statutory
obligations — to notify affected individuals where required, and to report to
the Information and Privacy Commissioner of Ontario where its own rules require
it. The supplier's duty is to tell the institution, promptly and completely
enough for it to act. A supplier that assesses the harm itself and decides not
to escalate has made a decision that was not its to make.

It must record the contractual deadline, because it is usually the shortest
clock in the organisation. Twenty-four hours is common and some institutions
require immediate notification; either is shorter than PIPEDA's "as soon as
feasible" and shorter than the organisation's own internal assessment.

It must name a real contact at each institution and keep it current. A
notification sent to a general mailbox at 6 p.m. on a Friday is a notification
the organisation can prove it sent and cannot prove was received.

It must say what happens next: the institution directs, and the supplier follows
— including on what the individuals are told, which is the institution's message
to make rather than the supplier's.
