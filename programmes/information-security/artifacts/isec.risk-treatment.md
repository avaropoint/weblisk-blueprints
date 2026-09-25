---
id: isec.risk-treatment
kind: procedure
title: Risk Treatment and Review
structure: procedure
path: procedures/risk-treatment.md

satisfies:
  - nist_csf_2:ID.RA-06
  - nist_csf_2:GV.RM-02
  - iso_27001:A.5.36
  - soc2:CC3.4

requires: [isec.risk-register]

declares:
  obligation:
    id: isec.risk-review
    # Record-origin, not a cadence: risks are reviewed on their own dates,
    # because a severe risk carried against a supplier contract that ends in
    # March and a minor one reviewed every second year do not share a clock.
    activity: Review and re-score a risk before its review date
    for:
      records: registers/information-security-risks.md
      due: 30d before review_due
      key: reference
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/risk-reviews.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - nist_csf_2:ID.RA-06
  register:
    title: Risk Review Record
    note: >
      One row per review of one risk, keyed by the risk's reference. The column
      that earns the register is `treatment_effective`: a treatment applied on
      time whose risk has not moved is a finding about the treatment, and
      without the column the review records only that somebody looked.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: reference, label: Risk reviewed, type: relation, required: true,
         target: /registers/information-security-risks.md#records, display: reference}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: still_valid, label: Risk still valid, type: bool, required: true}
      - {key: score_changed, label: Score changed, type: select, required: true,
         options: [Unchanged, Increased, Decreased, Closed]}
      - {key: treatment_effective, label: Treatment effective, type: select, required: true,
         options: [Not yet assessable, Effective, Partially effective, Ineffective]}
      - {key: action, label: Action taken or agreed, type: longtext, required: true}
      - {key: next_review, label: Next review due, type: date, required: true}
---

What this document must establish for THIS organisation: what happens to a risk
between the day it is written down and the day it stops being true.

It must say who reviews what. A risk owned by a position is reviewed by that
position, and a review conducted entirely by the security lead reaches the
conclusions the security lead already holds.

It must require the review to reach one of four outcomes — unchanged, worse,
better, closed — and to say why. "Reviewed" with no movement recorded for three
consecutive cycles is either a stable risk or a register nobody is reading, and
the two look identical without the reason.

It must state what happens when a treatment turns out not to work. That is the
interesting case and the one most registers cannot express: the action was
completed, on time, and the exposure did not move. The next step belongs here —
re-treat, escalate, or accept at the higher score with a name against it.

Thirty days before the review date, not on it. A treatment that needs a
purchase, a supplier change or a maintenance window cannot be arranged in the
week after somebody notices it was due, and a review that opens on the day it is
already late has no room to produce anything but a note.
