---
id: cohs.suspended-access
kind: procedure
title: Suspended Access Equipment
structure: procedure
path: procedures/suspended-access.md

satisfies:
  - o_reg_213_91:7.1
  - o_reg_213_91:138
  - o_reg_213_91:138.1
  - cor_2020:COR-08

requires: [cohs.fall-protection, cohs.credential-register]

declares:
  obligation:
    id: cohs.suspended-access-review
    activity: Review of each suspended access installation on the project — the design, the notification, and the training of everyone who installs, inspects or uses it
    cadence: each month
    authority: O. Reg. 213/91 ss. 7.1, 138, 138.1. The notification and the three-year training clocks are prescribed; no review interval is
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: the organisation
    per:
      listed_in: registers/projects.md
      key: project_id
      label: name
      from: start_on
      until: finished_on
    records: registers/suspended-access-reviews.md
    escalate: {after: 1w, to: health-safety-lead}
  register:
    title: Suspended Access Review Record
    note: >
      One row per installation per month. `proof_carried` is a column because the
      requirement is that the worker carry written proof of training — the
      organisation holding a record somewhere does not satisfy it, and the only
      way to know is to have asked on site.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: installation, label: Installation, type: text, required: true}
      - {key: type, label: Type, type: select, required: true,
         options: [Suspended work platform system, Single-point suspended platform,
                   Multi-point suspended platform, Boatswain's chair, Mast climber, Other]}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: notice_given_on, label: Notification given to the Ministry on, type: date}
      - {key: first_used_on, label: First used on, type: date}
      - {key: design_by_engineer, label: Design and drawings by a professional engineer held on site, type: bool, required: true}
      - {key: users_trained, label: Users with training within the last three years, type: int, required: true}
      - {key: installers_trained, label: Installers or inspectors with training within the last three years, type: int, required: true}
      - {key: proof_carried, label: Every worker asked was carrying written proof, type: bool, required: true}
      - {key: fall_arrest_independent, label: Fall arrest attached to an independent anchor, type: bool, required: true}
      - {key: findings, label: Findings, type: longtext}
---

What this document must establish for THIS organisation: when a suspended access
system may be used, who must be notified before it is, what the training clocks
are, and what a worker must have on them while they are over the edge.

**The forty-eight hours is the law's.** A suspended work platform system requires
notification at least forty-eight hours before it is first used on a project. It
is easy to miss because it is a separate duty from the notice of project and
because the equipment often arrives to a schedule set by somebody else.

**The three-year training clocks are the law's**, and there are two of them, for
two different populations: the worker who **uses** the equipment, and the worker
who **installs or inspects** it. Both are expressed as "as often as is necessary,
but at least every three years" — which is a **ceiling with independent event
triggers**, not a plain expiry. The three years is the outer limit; a change of
equipment, an incident, or a long period without use requires retraining sooner,
and a programme that treats the date as the whole requirement will report a
worker current who has not been on a stage in two years. The document must say
both halves.

It must require **written proof carried by the worker** while they use the
equipment. The duty is on the worker to have it; the practical duty on the
organisation is to make sure it exists and is issued, and the review asks whether
anybody actually checked.

It must require the professional engineer's design and drawings to be **on the
project**, and must state which configurations require them. Where the equipment
is designed to a standard the regulation names, it is the **named edition** that
binds, and the clause references in an older edition do not survive into a newer
one — a specification written against the current edition of a standard the
regulation names at an earlier edition is describing a different document.

It must require the **fall arrest system to be attached to an anchor independent
of the suspended platform**. This is the single control that distinguishes a bad
day from a fatality and it is the one that is compromised when anchors are scarce.

**The monthly review is this organisation's choice.** No review interval is
prescribed; the notification and the training limits are. A month is chosen
because an installation is reconfigured as the building is worked around, and the
review is the point at which the drawings, the training and the hardware are
compared to each other rather than each to itself.
