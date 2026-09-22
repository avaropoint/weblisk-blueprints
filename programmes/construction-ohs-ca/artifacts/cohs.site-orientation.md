---
id: cohs.site-orientation
kind: procedure
title: Site Orientation and Awareness Training
structure: procedure
path: procedures/construction/site-orientation.md

satisfies:
  - construction_safety_ca:CSA-TR-1
  - cor_2020:COR-16
  - iso_45001:7.3

requires: [cohs.constructor-duties]

declares:
  obligation:
    id: cohs.orientation-verification
    activity: Verification that everyone on the project has been oriented and holds awareness training
    cadence: each week
    authority: OHSA s. 25(2)(a), (c); O. Reg. 297/13 ss. 1–2 — awareness training is required, no verification interval is set
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/construction/orientation-verifications.md
    escalate: {after: 1w, to: health-safety-lead}
  register:
    title: Orientation Verification Record
    note: >
      One row per project per week. This register records the CHECK, not the
      orientations — each worker's own orientation record is a document in its
      own right, signed by the worker and by whoever delivered it. What is
      counted here is the gap: how many people were on site, how many had a
      record, and who the difference was.
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: workers_on_site, label: Workers on site, type: int, required: true}
      - {key: oriented, label: With a site orientation on file, type: int, required: true}
      - {key: worker_awareness, label: With worker awareness training on file, type: int, required: true}
      - {key: supervisor_awareness, label: Supervisors with supervisor awareness training on file, type: int, required: true}
      - {key: outstanding, label: Who is outstanding, and since when, type: longtext}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: what a person is told
before they are allowed to work, who tells them, and how anyone proves afterwards
that they were told.

It must separate the two things that are routinely merged. **Awareness training**
is a regulated minimum about the Act itself — a worker completes it as soon as
practicable, a supervisor **within one week** of beginning work as a supervisor,
and neither has an expiry or a refresher anywhere in the regulation. **Site
orientation** is about this project: its hazards, its access and egress, its
emergency arrangements, who the supervisor is, where the first aid station and
the defibrillator are, and what the stop-work route is. One transfers between
employers and the other does not, and a contractor arriving with a valid
awareness certificate has satisfied none of the second.

There is no expiry on awareness training and the document must not imply one. A
provider's card that carries a date is the provider's policy; the regulation
requires the training once and requires proof to be produced on request. It also
requires written proof to be supplied to a **departed** worker who asks within
six months of leaving, which is a records duty the organisation will only meet if
the records survive the person.

It must say what happens for a worker who arrives mid-week, mid-shift, or as a
one-day delivery. The honest answer is usually a short, recorded, site-specific
briefing rather than the full session, and a procedure that does not provide for
it produces either unrecorded briefings or unbriefed people.

**The weekly verification is this organisation's choice.** Nothing in Ontario law
sets an interval for checking that the orientation records match the people
actually on site; the duty is that they be oriented, continuously. A week is
chosen because it is the shortest interval a supervisor can sustain across a
crew that changes, and because the supervisor awareness duty itself is expressed
in weeks. An organisation with high daily churn should shorten it, and should
record that it did.

It must record the outstanding names rather than a count alone. A number tells a
reader that four people were unaccounted for; only the names tell the next
reader whether it was the same four.
