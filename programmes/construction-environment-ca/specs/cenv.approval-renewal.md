---
id: cenv.approval-renewal
kind: procedure
title: Approval and Permit Renewal
structure: procedure
path: procedures/approval-renewal.md

satisfies:
  - epa_ontario:20.2
  - epa_ontario:20.21
  - owra_ontario:34

requires: [cenv.environmental-approvals]

declares:
  obligation:
    id: cenv.approval-renewal
    activity: Instrument renewed, amended, re-registered or deliberately allowed to lapse before it expires
    for:
      records: registers/environmental-approvals.md
      due: 90d before expires_on
      key: approval_id
    authority: >
      The instrument sets its own expiry; no statute sets a renewal lead time,
      because a lapsed instrument is simply an unauthorised activity from the
      day after. Ninety days is this organisation's, chosen because an
      application to renew a permit to take water requires a qualified
      professional's supporting work that cannot be commissioned and completed
      inside a month, and because the Director's queue is not something the
      applicant controls
    interval_basis: chosen
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/approval-renewals.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Approval Renewal Record
    note: >
      One row per instrument that has an expiry date, raised ninety days before
      it. "Allowed to lapse" is a legitimate outcome and it is recorded as a
      decision with a reason, because the alternative is an instrument that
      quietly expires and a register that cannot tell that apart from one
      somebody forgot. `activity_continued_after_expiry` is the only field on the
      row that can describe an offence, and it is required.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 7y
      authority: No instrument prescribes a retention period for a renewal record
      reason: >
        Seven years is this organisation's, matched to O. Reg. 406/19 s. 28 so
        that one period covers every environmental record. Said plainly because
        a keeping period with no authority is a number somebody chose, and it is
        better for the reader to know that than to be shown a citation that does
        not exist.
    columns:
      - {key: approval, label: Approval, type: relation, required: true,
         target: /registers/environmental-approvals.md#records, display: approval_id}
      - {key: expires_on, label: Expires on, type: date, required: true}
      - {key: still_needed, label: The activity will continue past the expiry, type: bool, required: true}
      - {key: action, label: Action, type: select, required: true,
         options: ["Renewal applied for",
                   "Amendment applied for",
                   "Re-registered in the Environmental Activity and Sector Registry",
                   "Allowed to lapse — the activity has ended",
                   "Allowed to lapse — replaced by another instrument",
                   "Surrendered",
                   Outstanding]}
      - {key: applied_on, label: Applied on, type: date}
      - {key: qualified_professional, label: Qualified professional engaged for the supporting work, type: text}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: ["Issued or confirmed",
                   "Refused",
                   "Issued with conditions that changed",
                   "Awaiting the Director's decision",
                   "Not applicable — lapsed or surrendered",
                   Outstanding]}
      - {key: new_number, label: New number, type: text}
      - {key: new_expires_on, label: New expiry, type: date}
      - {key: conditions_changed, label: The conditions changed, type: bool, required: true}
      - {key: what_changed, label: What changed in the conditions, type: longtext}
      - {key: activity_continued_after_expiry, label: The activity continued after the instrument expired, type: bool, required: true}
      - {key: handled_by, label: Handled by, type: user}
      - {key: evidence, label: Application and the new instrument, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: who watches an expiry
date that nobody is standing next to, and what the ninety days before it are for.

It exists because **an expiry is the one clock in this programme that no activity
generates.** Every other obligation here is raised by something somebody does —
soil is excavated, a truck leaves, an observation is made, a spill happens. An
instrument expires whether or not anybody works that week, and the first evidence
of the lapse is usually a provincial officer asking to see a current permit.

**Ninety days is this organisation's and no statute sets one.** It is chosen from
the shape of the work: a renewed permit to take water needs the same qualified
professional's supporting material the original did, the professional needs to be
engaged, and the Director's decision is on somebody else's timetable. A thirty-day
window would be a window in which the only available action is to stop work.

**"Allowed to lapse" is an outcome and it is the one that must be recorded most
carefully.** Not renewing is frequently the right answer — the dewatering is
finished, the crusher has left the site, the activity is now covered by a
different instrument — and an organisation that treats every expiry as a renewal
spends money on authorisations for work it no longer does. What makes the
difference between a decision and a failure is a row saying which it was, when,
and on whose judgement. `still_needed` is asked first for that reason.

**`conditions_changed` is required because a renewal is not a continuation.** A
reissued approval can carry different limits, different monitoring and different
reporting, and the site carries on doing exactly what it did before because the
number on the certificate did not change. Where the conditions changed, the
condition check that follows is against the new ones, and the procedure must say
who tells the site.

**`activity_continued_after_expiry` is required and the honest answer is
sometimes yes.** Operating past an expiry is operating without the instrument, and
a register that cannot record it will record nothing. The organisation that knows
it happened for eleven days and wrote that down is in a materially better position
than the one whose records are silent.
