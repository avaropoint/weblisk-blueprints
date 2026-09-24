---
id: cohs.jhsc
kind: procedure
title: Joint Health and Safety Committee and Health and Safety Representative
structure: procedure
path: procedures/joint-health-and-safety-committee.md

satisfies:
  - ohsa_ontario:8(1)
  - ohsa_ontario:9(2)
  - ohsa_ontario:9(33)
  - cor_2020:COR-05
  - iso_45001:5.4

requires: [cohs.constructor-duties]

declares:
  obligation:
    id: cohs.jhsc-meeting
    activity: Joint health and safety committee meeting
    cadence: each quarter
    authority: OHSA s. 9(33) — "at least once every three months"
    interval_basis: required
    responsible: health-safety-lead
    applies_to: each project
    records: registers/joint-health-and-safety-committee-meetings.md
    escalate: {after: 2w, to: constructor-representative}
    satisfies:
      - ohsa_ontario:9(33)
      - cor_2020:COR-05
      - iso_45001:5.4
  register:
    title: Committee Meeting Record
    note: >
      One row per meeting. `recommendations_made` and `response_due` are separate
      columns because the committee's power is the written recommendation and the
      employer owes a written response within twenty-one days — a meeting record
      that captures attendance and not recommendations evidences a gathering.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: met_on, label: Met on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: format, label: Format, type: select, required: true,
         options: [At the workplace, Virtual, Hybrid]}
      - {key: worker_members_present, label: Worker members present, type: int, required: true}
      - {key: management_members_present, label: Management members present, type: int, required: true}
      - {key: certified_present, label: A certified member from each side present, type: bool}
      - {key: co_chairs, label: Co-chairs, type: text, required: true}
      - {key: matters, label: Matters considered, type: longtext, required: true}
      - {key: recommendations_made, label: Written recommendations made, type: longtext}
      - {key: response_due, label: Written response due by, type: date}
      - {key: response_given_on, label: Written response given on, type: date}
      - {key: minutes, label: Minutes, type: attachment}
---

What this document must establish for THIS organisation: when a committee is
required, when a representative is required instead, who sits on it, and what it
is entitled to.

It must get the three thresholds right, because they are three different numbers
and mixing them is the most common failure in this area:

- s. 9 **does not apply at all** to a project expected to last less than three
  months. A ten-week job with sixty workers needs no committee.
- A **committee** is required where **twenty or more** workers are regularly
  employed. At least two members under fifty workers, at least four at fifty or
  more; at least half must be workers who do not exercise managerial functions;
  two co-chairs, one chosen by each side.
- **Certified members** — one from each side — are required only at **fifty or
  more** workers regularly employed, and not for a project lasting under three
  months. Certification is not a property of having a committee; it is a separate
  and higher threshold.
- Where no committee is required and the number of workers regularly exceeds
  five, a **health and safety representative** is required instead. The
  representative is not a lesser version of a committee with lesser rights; the
  inspection and recommendation duties run in parallel.

The **three-month meeting interval is the law's**, and so is the **twenty-one
days** the employer has to respond in writing to a written recommendation. The
response clock is the part organisations lose: a recommendation minuted and
answered verbally at the next meeting is a contravention with a paper trail
proving it.

Since October 2024 the words "at the workplace" no longer appear in the meeting
provision, so a committee may meet virtually. Material still in wide circulation
says otherwise, and a procedure that forbids what the law now allows will be
quietly ignored, which is worse than either.

It must set out certification training as a credential with a real clock. A
certified member must complete refresher training **within three years** of
certification and then within three years of each refresher; failing to do so
means the person is **no longer certified**, which can leave a project of fifty
or more workers non-compliant without anybody having left. Part One to Part Two
is **twelve months**, not six. Those records belong in the register of statutory
credentials so that the renewal machinery sees them.

It must say what the committee is entitled to beyond meeting: to inspect, to be
told of an incident, to accompany an inspector, to be present when a work refusal
is investigated — and, where possible, that the member attending a second-stage
refusal is a certified one.
