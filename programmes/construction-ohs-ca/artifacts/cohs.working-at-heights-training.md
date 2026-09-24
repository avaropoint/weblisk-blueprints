---
id: cohs.working-at-heights-training
kind: procedure
title: Working at Heights Training
structure: procedure
path: procedures/working-at-heights-training.md

satisfies:
  - o_reg_297_13:6
  - o_reg_297_13:7
  - o_reg_297_13:8(1)
  - o_reg_297_13:10
  - o_reg_213_91:26.2
  - cor_2020:COR-16
  - iso_45001:7.2

requires: [cohs.fall-protection, cohs.credential-register]

declares:
  obligation:
    id: cohs.heights-training-verification
    activity: Verify that everyone using a fall protection system on the project holds both a current Working at Heights certificate and a s. 26.2 training record
    cadence: each month
    authority: O. Reg. 297/13 s. 8(1) sets a three-year validity; O. Reg. 213/91 s. 26.2 requires system training with no interval. Neither sets a verification interval
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/working-at-heights-verifications.md
    escalate: {after: 1w, to: health-safety-lead}
  register:
    title: Heights Training Verification Record
    note: >
      One row per project per month. The two counts are deliberately separate.
      They are two different requirements with two different regulations behind
      them, and an organisation that records a single "trained" number has built
      the exact confusion this artifact exists to prevent.
    layout: form
    review: required
    approvers: [training-coordinator]
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: workers_at_height, label: Workers who may use a fall protection system, type: int, required: true}
      - {key: with_working_at_heights, label: With a current Working at Heights certificate, type: int, required: true}
      - {key: with_system_training, label: With a signed s. 26.2 system training record, type: int, required: true}
      - {key: expiring_within_90_days, label: Certificates expiring within ninety days, type: int, required: true}
      - {key: outstanding, label: Who is outstanding, type: longtext}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: who must hold Working at
Heights training, from whom, how long it lasts, and why holding it is not
sufficient.

**The three-year validity is the law's.** A Working at Heights certificate is
valid for three years from the date of successful completion, and after that the
worker may not lawfully use a fall protection system on a project. Training must
be delivered by a provider approved by the Chief Prevention Officer under an
approved programme; a course that is not on that list is not this training,
however good it is.

**It must state that Working at Heights and s. 26.2 system training are
cumulative.** Both regulations say so in terms. Working at Heights is generic:
the hazard, the hierarchy, the equipment in principle. Section 26.2 is about the
specific system this worker will use on this project — the anchor, the connector,
the clearance, the rescue — and it must be recorded in writing, signed, with the
worker's name and the dates. A worker with a valid card and no system training is
not trained, and this is the most common single misconception in Ontario fall
protection. The verification register counts the two separately for that reason.

It must state that **s. 26.2 training has no expiry in law**. If the organisation
refreshes it, that is its own policy and the document must say so.

It must say what happens to a worker whose certificate is about to expire on a
project where the only work available is at height. The honest answer is planned
in advance, which is why the verification counts certificates expiring within
ninety days: the renewal obligation elsewhere in this programme raises the work,
and this count is how a supervisor sees it coming on their own site.

**The monthly verification is this organisation's choice.** Nothing requires the
records to be reconciled against the people on site at any interval; the duty is
that the training be held, continuously. Monthly is chosen to sit inside the
ninety-day renewal margin, so that a lapse discovered here can still be booked
out of.

It must not treat the training as transferable evidence of competence. A
certificate says a person attended an approved programme and passed. Whether they
can rig a horizontal lifeline on this building is a judgement somebody has to
make, record, and be prepared to defend.
