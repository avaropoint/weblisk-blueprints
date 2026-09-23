---
id: cohs.pre-task-hazard-assessment
kind: procedure
title: Pre-Task Hazard Assessment
structure: procedure
path: procedures/pre-task-hazard-assessment.md

satisfies:
  - ohsa_ontario:25(2)(h)
  - cor_2020:COR-06
  - iso_45001:6.1.2
  - iso_45001:6.1.4

requires: [cohs.daily-crew-assignments]

declares:
  obligation:
    id: cohs.pre-task-assessment
    activity: Pre-task hazard assessment completed by the crew before work begins
    for:
      records: registers/daily-crew-assignments.md
      due: 1d after work_date
      key: assignment_id
    authority: OHSA s. 25(2)(h) — every precaution reasonable in the circumstances. No Ontario provision prescribes a pre-task assessment or its frequency
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/pre-task-hazard-assessments.md
    escalate: {after: 1d, to: health-safety-lead}
    satisfies:
      - ohsa_ontario:25(2)(h)
      - iso_45001:6.1.2
  register:
    title: Pre-Task Hazard Assessment Record
    note: >
      One row per crew per shift, keyed to the assignment it answers. The
      controls are required, not optional: the choice between eliminating a
      hazard and putting equipment on a person is the whole content of the
      assessment, and a record naming only the hazard cannot show which way round
      it was made. Submitted as a form so that a half-finished assessment is not
      committed to the governance repository as somebody types it — a partly
      filled hazard assessment is a false statement about a crew's morning.
    layout: form
    review: required
    approvers: [site-supervisor]
    columns:
      - {key: assignment_id, label: Assignment, type: relation, required: true,
         target: /registers/daily-crew-assignments.md#records, display: assignment_id}
      - {key: assessed_on, label: Assessed on, type: date, required: true}
      - {key: led_by, label: Led by, type: user, required: true}
      - {key: participants, label: Everyone who took part, type: longtext, required: true}
      - {key: task, label: Task, type: longtext, required: true}
      - {key: conditions, label: Conditions today, type: longtext, required: true}
      - {key: hazards, label: Hazards identified, type: longtext, required: true}
      - {key: fall_exposure, label: Work at height today, type: bool, required: true}
      - {key: controls, label: Controls, and why these, type: longtext, required: true}
      - {key: highest_control, label: Highest control applied, type: select, required: true,
         options: [Eliminated, Substituted, Engineering control, Administrative control,
                   Personal protective equipment only]}
      - {key: changed_since_plan, label: Changed from what was planned, type: longtext}
      - {key: work_stopped, label: Work stopped or changed as a result, type: bool, required: true}
      - {key: escalated_to, label: Escalated to, type: user}
---

What this document must establish for THIS organisation: how a crew works out,
before it starts, what could hurt somebody today and what it is going to do about
it.

It must distinguish the assessment done **once for a kind of work** from the one
done **at the start of this shift, in these conditions**. The first is the safe
job procedure and it is written in an office. The second is the only one that
knows it rained overnight, that the crane is on the other side of the building,
that the crew is two people short and one of them is new. An organisation that
has only the first is assessing a workplace it is not standing in.

It must require the crew to take part and record who they were. An assessment
completed by a supervisor before anyone arrives is a briefing, and a briefing
does not surface the thing the apprentice noticed on the way in.

It must require the **highest control applied** to be named, not just the
controls. Elimination before substitution, engineering before administration,
protective equipment last — that order is the content of the decision, and a
record listing "hard hats, gloves, high-vis" against a fall hazard has documented
the wrong answer legibly.

**Neither the assessment nor its frequency is prescribed by Ontario law.** The
duty behind it is the general one: every precaution reasonable in the
circumstances, and the employer's duty to provide information, instruction and
supervision. A per-shift assessment is the construction industry's answer to that
duty and it is a very good one, but it is this organisation's commitment rather
than a statutory interval, and the document must say so in those words. What is
not optional is that if the organisation commits to it, an assessment that did
not happen is a commitment broken.

It must say what happens when the assessment finds something the crew cannot
control: who stops, who is called, and how the decision is recorded either way.
A procedure with no stop-work path has already decided the answer.

The occurrence is raised from the crew assignment rather than from a calendar, so
a project running four crews is four pieces of work a day. That is the point, and
the register it is triggered from exists for no other reason.
