---
id: cohs.asbestos-management
kind: procedure
title: Asbestos on Construction Projects
structure: procedure
path: procedures/asbestos.md

satisfies:
  - o_reg_278_05:12
  - o_reg_278_05:19
  - o_reg_278_05:21
  - cor_2020:COR-06
  - cor_2020:COR-08

requires: [cohs.designated-substances]

declares:
  obligation:
    id: cohs.asbestos-work-report
    activity: Asbestos work report for every worker who worked in a Type 2 or Type 3 operation, sent to the Provincial Physician with a copy to the worker
    cadence: each year
    authority: O. Reg. 278/05 s. 21(1) — at least once every twelve months, and on termination of employment
    interval_basis: required
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/asbestos-work-reports.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Asbestos Work Report Record
    note: >
      One row per report submitted. The copy to the worker is a column and not an
      assumption: the report is the worker's own occupational exposure history and
      it will matter to them decades after they have left, at a point when the
      organisation may no longer exist.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reported_on, label: Report submitted on, type: date, required: true}
      - {key: period_from, label: Period from, type: date, required: true}
      - {key: period_to, label: Period to, type: date, required: true}
      - {key: workers_covered, label: Workers covered, type: int, required: true}
      - {key: type_2_operations, label: Type 2 operations in the period, type: int, required: true}
      - {key: type_3_operations, label: Type 3 operations in the period, type: int, required: true}
      - {key: submitted_by, label: Submitted by, type: user, required: true}
      - {key: copy_to_workers_on, label: Copy given to each worker on, type: date, required: true}
      - {key: terminations_reported, label: Reports made on termination of employment, type: longtext}
      - {key: evidence, label: Copy of the report, type: attachment}
---

What this document must establish for THIS organisation: how asbestos is
identified before work starts, how the work is classified, who may do Type 3
work, and what the organisation owes each exposed worker afterwards.

It must be built on the **right regulation**. Asbestos on a construction project,
in a building, or in a repair operation is governed by the asbestos regulation
made under the Occupational Health and Safety Act. It is **not** an environmental
regulation, and it is **not** the designated substances regulation, whose asbestos
reach is limited to mines, manufacturing and certain maintenance operations with a
control programme in effect since the mid-1980s. A programme citing the wrong one
is citing a regulation that does not apply to it.

It must set out the **three operation types** and the controls that attach to
each, and must be clear that the classification determines everything downstream:
the enclosure, the ventilation, the respiratory protection, the clearance, and
who may be on site.

It must state the training position accurately, because it is unusual. There is a
general instruction requirement for any worker who may be exposed, with **no
refresher**. There is a separate approved abatement worker and supervisor training
programme, which applies to **Type 3 operations only**, and the document issued on
completing it is made **conclusive proof** by the regulation **with no time
qualifier** — that is, it does not expire. An organisation may choose to refresh
it, and that choice is its own.

**The one real recurring clock is the work report**, and it is the law's: at least
once every twelve months, and on the termination of a worker's employment, a
report of the worker's asbestos work in Type 2 and Type 3 operations goes to the
Provincial Physician, with a copy to the worker. It is the obligation this
artifact declares, and it is the one that is most often missed because it is not
about the work site at all.

It must also say what the organisation does about **asbestos waste**, and must
place it correctly: asbestos waste is dealt with under the environmental waste
regulation, where it is **excluded from subject waste** — no manifest, no registry
entry — while carrying its own strict requirements for rigid sealed containers,
prominent lettering on every vehicle and container, a driver trained in asbestos
waste management, direct transport with no transfer stations, no other cargo and
no compaction, and deposit only at a landfill adapted to receive it. The absence
of a manifest is exactly the sort of thing that reads as an absence of
requirements, and it is the opposite.

It must state that **there is no mandatory asbestos registry for Ontario
construction projects.** A voluntary, worker-facing exposure self-tracker exists
and is a good thing to tell workers about; it is not a compliance obligation and
should never be described as one.
