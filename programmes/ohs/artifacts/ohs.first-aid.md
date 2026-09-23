---
id: ohs.first-aid
kind: procedure
title: First Aid
structure: procedure
path: procedures/first-aid.md

satisfies:
  - cor_2020:COR-14

requires: [ohs.emergency-response-plan]

declares:
  obligation:
    id: ohs.first-aid-check
    activity: Check of first aid supplies and attendant coverage
    cadence: each month
    responsible: site-supervisor
    applies_to: each project
    records: registers/first-aid-checks.md
  register:
    title: First Aid Check Record
    note: >
      One row per check. Coverage and supplies are checked together because
      either alone is not first aid: a stocked cabinet nobody is certified to
      open, and a certified attendant with an empty cabinet, both fail the same
      way.
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: location, label: Site or work area, type: text, required: true}
      - {key: attendants_required, label: Attendants required, type: int, required: true}
      - {key: attendants_current, label: Attendants with current certification, type: int, required: true}
      - {key: supplies_complete, label: Supplies complete, type: bool, required: true}
      - {key: expired_items, label: Items expired or used and not replaced, type: longtext}
      - {key: action, label: Action taken, type: longtext}
      - {key: checked_by, label: Checked by, type: user, required: true}
---

What this document must establish for THIS organisation: who can give first aid,
what they have to give it with, and how an injury becomes a record.

It must derive the requirement from the workplace rather than state a number. How
many attendants, what level of certification and what supplies are required
depends on the hazard, the headcount, the shift pattern and the distance to
medical aid — and a document naming one number is wrong for every site but one.

It must name, for each work location, how far away help is and what that distance
changes. A remote site is not an ordinary site with a longer drive; it needs a
different plan, and the plan belongs where the distance is recorded.

It must say how an injury is recorded and how that record reaches the incident
reporting procedure, including the minor ones. First aid records are the earliest
evidence of a pattern, and an organisation that keeps them separately from its
incident reporting has the pattern and cannot see it.

It must state what is confidential. A first aid record contains health
information, and the person who needs to know an attendant was called is not
necessarily entitled to know what for.
