---
id: cohs.elevating-work-platforms
kind: procedure
title: Elevating Work Platforms
structure: procedure
path: procedures/construction/elevating-work-platforms.md

satisfies:
  - construction_safety_ca:CSA-SITE-2
  - cor_2020:COR-16
  - iso_45001:7.2

requires: [cohs.credential-register]

declares:
  obligation:
    id: cohs.ewp-operator-verification
    activity: Verify that every worker operating an elevating work platform holds training that is current and specific to that make and model
    cadence: each month
    authority: O. Reg. 117/26 ss. 9, 10, 11 (in force 1 January 2027) — operator training valid five years, with make and model familiarisation. No verification interval is prescribed
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/construction/elevating-work-platform-verifications.md
    escalate: {after: 1w, to: health-safety-lead}
  register:
    title: Elevating Work Platform Verification Record
    note: >
      One row per project per month. Training and familiarisation are counted
      separately because they are separate requirements with different triggers:
      the training has a five-year clock, the familiarisation has no clock at all
      and is triggered by a machine the operator has not used before.
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/construction/projects.md#records, display: project_id}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: machines_on_site, label: Platforms on site, type: int, required: true}
      - {key: operators, label: Workers who operate them, type: int, required: true}
      - {key: with_current_training, label: With training that has not passed five years, type: int, required: true}
      - {key: with_practical_record, label: With a record of theory and practical training, type: int, required: true}
      - {key: with_familiarisation, label: With make and model familiarisation for the machine they use, type: int, required: true}
      - {key: earliest_expiry, label: Earliest training expiry on site, type: date}
      - {key: outstanding, label: Who is outstanding, type: longtext}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: who may operate an
elevating work platform, what their training must have covered, and how the
organisation will be ready for a rule that changes on a known date.

**This is a forward-dated artifact and the document must say so on its first
page.** The elevating work platform provisions of the construction projects
regulation are **revoked and replaced by a standalone regulation on 1 January
2027**, applying to **all projects**. From that date operator training must cover
seventeen prescribed topics, must include **theory and practical** components with
demonstrated proficiency, must include **make and model familiarisation**, must be
recorded in a prescribed form, and is **valid for five years** from successful
completion. Until that date the current provisions apply. A programme that
silently adopts the new rule early is claiming compliance with an instrument that
is not yet in force; a programme that ignores it will discover on the first
Monday of 2027 that a proportion of its operators are untrained.

**The transition is per worker, and this is the part that requires action now.**
Training completed under the existing provision **before** the commencement date
stands for **five years from the date it was completed** — not five years from
commencement. An organisation that has never recorded the completion dates of its
historical platform training cannot compute those expiries, and will find them
distributed unpredictably across the following five years. Backfilling those dates
into the register of statutory credentials is work to do before the date, not
after it.

**The five years is the law's, from 2027.** Today there is no statutory interval.
Any three-year or five-year figure quoted today comes from a training provider or
from a standard, not from Ontario law, and the three-year figure in particular is
frequently a misreading of a **records** provision — the employer must supply
written proof to a departed worker who asks within three years of the training
being delivered. That is a retention duty, not a retraining interval, and the
document must not convert one into the other.

**Make and model familiarisation has no clock at all.** It is triggered by an
operator being put on a machine they have not been familiarised with, which is an
event a date-driven engine cannot see. The document must name who is responsible
for noticing it — in practice the supervisor who assigns the machine — and must
record it, which is why the verification register counts it separately from
training.

On design standards, the document should be careful in the opposite direction
from most. The incoming regulation continues to name **older design standards**
than the ones the industry commonly cites, and Ontario has **not** adopted the
current safe-use and operator-training standards in that family. A programme
claiming conformance to those is **exceeding** the Ontario design requirement
rather than meeting it — which is a legitimate choice, and a different statement
from compliance.

**The monthly verification is this organisation's choice.** Nothing prescribes
one; the duty is that operators be trained, continuously.
