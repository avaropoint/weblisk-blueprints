---
id: ohs.orientation
kind: procedure
title: Orientation and Awareness
structure: procedure
path: procedures/orientation.md

satisfies:
  - iso_45001:7.3
  - isnetworld:ISN-SAFE-07

requires: [ohs.competency-matrix]

declares:
  obligation:
    id: ohs.orientation-delivered
    # Periodic, for the same reason as ohs.change-review: there is no register of
    # arrivals to trigger occurrences from, and "on each occurrence" is not a
    # cadence the platform can parse. Each orientation is still a row below; what
    # is scheduled is the check that no arrival was missed.
    activity: Confirmation that everyone who started in the period was oriented
    cadence: each month
    responsible: training-coordinator
    applies_to: each project
    records: registers/orientations.md
  register:
    title: Orientation Record
    note: >
      One row per person oriented. `short_service` is a flag rather than a
      separate register because a short-service worker is an ordinary worker
      under extra supervision, and splitting them into two lists is how one of
      the lists stops being maintained.
    columns:
      - {key: delivered_on, label: Delivered on, type: date, required: true}
      - {key: person, label: Person, type: user, required: true}
      - {key: kind, label: Orientation, type: select, required: true,
         options: [New to the organisation, New to this site, Returning after absence, Change of role]}
      - {key: hazards_covered, label: Site-specific hazards covered, type: longtext, required: true}
      - {key: short_service, label: Short-service worker, type: bool, required: true}
      - {key: mentor, label: Assigned mentor, type: user}
      - {key: understood, label: Understanding confirmed, type: bool, required: true}
      - {key: delivered_by, label: Delivered by, type: user, required: true}
---

What this document must establish for THIS organisation: what somebody is told
before they start work, and how anyone can tell afterwards that they understood
it.

Awareness is not competence and this document must not pretend otherwise. The
competency matrix records that a person can DO something; orientation records
that they know where they are, what is dangerous about it, who to tell and what
to do when the alarm sounds. A programme that treats a signed orientation sheet
as competence has a paper trail and an untrained crew.

It must separate the organisation's orientation from the SITE's. Somebody who has
worked here for ten years arriving at a new site is new to that site's hazards,
its muster point and its traffic plan, and a procedure that orients people once
on hiring has not covered the case where the hazard is the location.

It must require understanding to be CHECKED rather than declared. A signature
confirms attendance.

It must address the worker who is new to this kind of work regardless of age or
employment history — short service, however the organisation defines it. Those
workers are over-represented in serious incidents, and what the standard asks for
is a period of heightened supervision with a named mentor, not a longer video.

It must say what triggers a repeat: a change of role, a long absence, a new
hazard introduced on a site somebody already works at.
