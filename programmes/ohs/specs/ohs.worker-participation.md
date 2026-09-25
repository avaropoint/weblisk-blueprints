---
id: ohs.worker-participation
kind: procedure
title: Worker Participation and the Health and Safety Committee
structure: procedure
path: procedures/worker-participation.md

satisfies:
  - iso_45001:4.2
  - iso_45001:5.4
  - cor_2020:COR-05

requires: [ohs.responsibilities]

declares:
  obligation:
    id: ohs.committee-meeting
    activity: Health and safety committee meeting
    cadence: each quarter
    responsible: health-safety-lead
    applies_to: each project
    records: registers/committee-meetings.md
  register:
    title: Committee Meeting Record
    note: >
      One row per meeting. Attendance is split between worker and employer
      members because the balance is what makes the meeting a committee: a
      quorum met entirely by management is a management meeting, and a record
      that reports only a headcount cannot show the difference.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: met_on, label: Met on, type: date, required: true}
      - {key: location, label: Site or workplace, type: text, required: true}
      - {key: worker_members, label: Worker members present, type: int, required: true}
      - {key: employer_members, label: Employer members present, type: int, required: true}
      - {key: concerns_raised, label: Concerns raised, type: longtext, required: true}
      - {key: actions, label: Actions agreed, type: longtext, required: true}
      - {key: outstanding, label: Actions still open from last time, type: int}
      - {key: minutes_posted, label: Minutes posted, type: bool, required: true}
      - {key: chair, label: Chaired by, type: user, required: true}
---

What this document must establish for THIS organisation: how workers take part
in decisions about their own safety, and what happens to what they say.

It must set out the committee — who sits on it, how worker members are chosen
rather than appointed, how often it meets and what quorum it needs. Selection is
the part that decides whether the committee represents anybody: members chosen
by management are a consultation exercise, and the standard asks for
participation.

It must say how a concern raised by a worker is answered, by when, and by whom —
and what a worker may do when it is not. A participation procedure whose only
route is "tell your supervisor" has no path for the case where the supervisor is
the concern.

It must establish how the outcome gets back to the people who raised it. Minutes
posted where nobody reads them satisfy a filing requirement and not this one.

It must also record who OUTSIDE the organisation has an interest — a regulator, a
client's safety group, a union, a neighbouring occupier on a shared site — and
what each of them is owed, because those expectations bind the programme whether
or not they are written down.
