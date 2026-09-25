---
id: fleet.licence-renewal
kind: procedure
title: Driver Licence and Medical Renewal
structure: procedure
path: procedures/driver-licence-renewal.md

satisfies:
  - hta_ontario:HTA-DRIVER-01
  - hta_ontario:HTA-DRIVER-02
  - hta_ontario:HTA-DRIVER-03
  - nsc_ca:NSC-04
  - nsc_ca:NSC-06

requires: [fleet.drivers, fleet.driver-qualification]

declares:
  obligation:
    id: fleet.licence-renewal
    activity: Confirm the driver's licence and medical are renewed before the licence expires, and record the new dates
    for:
      records: registers/drivers.md
      due: 60d before licence_expires_on
      key: driver_id
    authority: >
      A driver must hold the class of licence that covers the vehicle driven,
      and a commercial class carries a medical examination on the Ministry's own
      cycle. Renewal is the driver's act and the Ministry's cycle; nothing
      requires the operator to give notice of it and no notice period is
      prescribed. The sixty days is this organisation's, chosen so that a
      medical appointment and a Ministry visit both fit inside it — a driver
      whose licence expires is a driver who cannot work that morning.
    interval_basis: chosen
    responsible: fleet-manager
    applies_to: the organisation
    records: registers/licence-renewals.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - hta_ontario:HTA-DRIVER-01
      - hta_ontario:HTA-DRIVER-02
      - nsc_ca:NSC-06
  register:
    title: Licence and Medical Renewal Record
    note: >
      One row per renewal, raised sixty days before a driver's licence expiry
      date. `new_expiry` is copied back onto the driver register and that step
      is a column here, because a renewal recorded only in this register leaves
      the driver register still holding the old date — which will either raise
      the same occurrence forever or, worse, stop raising anything.
      `still_dispatched` exists so a driver who has stopped driving is closed
      out rather than chased.
    layout: form
    review: required
    approvers: [fleet-manager]
    columns:
      - {key: driver, label: Driver, type: relation, required: true,
         target: /registers/drivers.md#records, display: driver_id}
      - {key: raised_on, label: Raised on, type: date, required: true}
      - {key: previous_expiry, label: Previous licence expiry, type: date, required: true}
      - {key: still_dispatched, label: This person is still dispatched in a commercial vehicle, type: bool, required: true}
      - {key: driver_notified_on, label: Driver notified on, type: date}
      - {key: medical_required, label: A medical is required for this renewal, type: select, required: true,
         options: ["Yes", "No", Not yet determined]}
      - {key: medical_completed_on, label: Medical completed on, type: date}
      - {key: medical_submitted, label: The medical report was submitted to the Ministry, type: bool}
      - {key: renewed_on, label: Licence renewed on, type: date}
      - {key: new_expiry, label: New licence expiry, type: date}
      - {key: class_after_renewal, label: Class after renewal, type: text}
      - {key: air_brake_retained, label: Air brake (Z) endorsement retained, type: bool}
      - {key: verified_against_ministry, label: Verified against the Ministry's record rather than the card, type: bool, required: true}
      - {key: verified_on, label: Verified on, type: date}
      - {key: register_updated, label: The driver register has been updated, type: bool, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: ["Renewed — driver continues", "Renewed at a lower class — dispatch restricted",
                   "Not renewed — driver removed from driving duties",
                   "No longer dispatched — closed", Not yet determined]}
      - {key: notes, label: Notes, type: longtext}
---

What this document must establish for THIS organisation: how a licence expiry
becomes somebody's work before it becomes somebody's problem.

**This is triggered by a date on a row, not by a cadence, and the document
should explain why.** A licence expires on a date the Ministry set, in the
driver's birth month, on a cycle that is not the same for everybody. There is
no period to divide the year into, so the work is raised from the driver
register's own expiry date and the only number the organisation chooses is how
much warning it wants.

**The sixty days is ours.** Nothing obliges an operator to warn a driver about
their own licence. What obliges the operator is that it may not put an
unlicensed driver in a commercial vehicle, and a licence that lapses on a
Tuesday takes a truck off a job that morning. Sixty days is enough for a
medical appointment, a report reaching the Ministry, and a renewal — and the
procedure should say the organisation picked it.

**The medical is the part that actually fails.** A commercial class requires a
medical examination and report on the Ministry's cycle, shortening with age,
and a medical not submitted results in the class being downgraded or the licence
suspended. The driver books it, the physician completes it, the Ministry
processes it — three parties, none of them the employer, and the employer bears
the outcome. The procedure must say who reminds the driver, how far ahead, and
what the organisation does when the date passes without evidence.

**Renewal must be confirmed against the Ministry's record and not against the
new card.** A downgrade is not always visible to the driver, and a renewal that
quietly dropped a class or an endorsement is the worst case here because
everybody believes it went well. `verified_against_ministry` is a required field
for that reason.

**Copying the new expiry date back onto the driver register is part of the
work.** It is the fact the next occurrence is measured from. A register left at
the old date will raise the same occurrence forever, which reads as an
organisation that never renews anything.

**A driver who has left is closed, not chased.** `still_dispatched` and the
driver register's `left_on` do that together. The alternative is an overdue
renewal against somebody who stopped working here in March, which is the kind
of gap that teaches people to ignore the list.
