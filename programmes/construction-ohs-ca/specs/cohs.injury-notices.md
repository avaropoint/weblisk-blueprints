---
id: cohs.injury-notices
kind: procedure
title: Statutory Notices and Injury Reporting
structure: procedure
path: procedures/statutory-notice.md

satisfies:
  - ohsa_ontario:51(1)
  - ohsa_ontario:52(1)
  - ohsa_ontario:53(1)
  - wsia_ontario:21
  - cor_2020:COR-17
  - iso_45001:10.2

requires: [cohs.notifiable-events]

declares:
  obligation:
    id: cohs.statutory-notice
    activity: Give every notice a reportable event requires, to every recipient it is owed to
    for:
      records: registers/notifiable-events.md
      due: 48h after occurred_on
      key: reference
    authority: OHSA s. 51(1) — written report within forty-eight hours of a death or critical injury. The other notices in this procedure run on their own shorter or longer clocks
    interval_basis: required
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/statutory-notices.md
    escalate: {after: 24h, to: senior-management}
  register:
    title: Statutory Notice Record
    note: >
      One row per event, keyed by the reference on the notifiable events
      register. Every recipient is its own column because they are separate
      duties owed to separate people, and an organisation that notified the
      Ministry and not the committee has complied with half of one section. The
      due date is set by the shortest clock the event triggers; the columns
      record whether each of the others was met.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: reference, label: Event, type: relation, required: true,
         target: /registers/notifiable-events.md#records, display: reference}
      - {key: prepared_by, label: Prepared by, type: user, required: true}
      - {key: inspector_notified_at, label: Inspector notified immediately at, type: text}
      - {key: written_report_to_director_on, label: Written report to a Director sent on, type: date}
      - {key: committee_notified_on, label: Committee or representative notified on, type: date}
      - {key: union_notified_on, label: Union notified on, type: date}
      - {key: constructor_notified_on, label: Constructor notified on, type: date}
      - {key: board_report_sent_on, label: Report to the workers' compensation board sent on, type: date}
      - {key: board_report_within_three_business_days, label: Board report received within three business days, type: bool}
      - {key: copy_to_worker_on, label: Copy of the board report given to the worker on, type: date}
      - {key: wages_paid_for_day_of_injury, label: Full wages and benefits paid for the day or shift of injury, type: bool}
      - {key: outstanding, label: Anything outstanding, and why, type: longtext}
      - {key: evidence, label: Copies of the notices, type: attachment}
---

What this document must establish for THIS organisation: who has to be told what,
by when, in what form, when somebody is hurt.

It must lay out the clocks separately, because they are different and none of them
is generous:

- **Death or critical injury from any cause.** The constructor **and** the
  employer notify an inspector **immediately** by telephone or other direct
  means, and also the committee or representative and the union. The employer
  sends a **written report within forty-eight hours**. The scene is not to be
  disturbed. This is the shortest clock in the programme and it is the one this
  obligation is dated from.
- **An injury that disables a worker from their usual work or requires medical
  attention**, including one from workplace violence: **written notice within four
  days** to the committee or representative and the union, and to a Director where
  an inspector requires it.
- **An occupational illness, or a claim for one**: **four days**, to a Director,
  to the committee or representative, and to the union.
- **A prescribed occurrence at a project site** — accident, explosion, fire,
  flood, inrush of water, failure of equipment, cave-in, subsidence, rockburst:
  **the constructor**, in writing, **within two days**.
- **The workers' compensation report**, where the worker needs health care, is
  absent from regular work, earns less than regular pay, requires modified work at
  less than regular pay, or requires modified work at regular pay for more than
  seven calendar days. The board must **receive** the completed report **within
  three business days** of the employer learning of the obligation, the **worker
  must receive a copy**, and the employer must pay **full wages and benefits for
  the day or shift of injury**. First aid alone does not trigger it. Late filing
  carries a penalty, and a materially late one carries a larger penalty.

It must state clearly that **"critical injury" is a defined term**, defined in a
regulation rather than left to judgement, and that the definition should be
reproduced in the organisation's own document and posted where supervisors can
reach it at two in the morning. A supervisor deciding on the spot whether an
injury is critical is being asked to apply a definition they have never read.

It must name **who makes the call out of hours** and how they are reached. The
duty is immediate; a procedure whose first step is to email the safety manager has
built a delay into the only clock measured in minutes.

It must not let the workers' compensation report stand in for the health and
safety notices, or the reverse. They go to different bodies, on different clocks,
for different purposes, and one of the most common findings after a serious injury
is an organisation that filed one of them promptly and believed itself finished.

It must say what happens when the injured person works for a sub-trade. The
employer's duties are theirs; the constructor's duties are the organisation's; and
the constructor's duty to ensure that every employer on the project complies means
"their form to file" is not an answer.

**Forty-eight hours is the law's**, and so is every other interval named above.
The escalation after twenty-four hours is this organisation's — chosen because a
notice that has not moved in half of its window will not move on its own.
