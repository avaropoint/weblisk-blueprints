---
id: ohs.emergency-response-plan
kind: procedure
title: Emergency Response Plan
structure: procedure
path: procedures/emergency-response.md

satisfies:
  - iso_45001:8.2
  - cor_2020:COR-13
  - isnetworld:ISN-SAFE-11

requires: [ohs.policy]

declares:
  obligation:
    id: ohs.emergency-drill
    activity: Emergency drill
    cadence: each year
    responsible: site-supervisor
    applies_to: each project
    records: registers/emergency-drills.md
  register:
    title: Emergency Drill Record
    note: >
      One row per drill. The time taken and what went wrong are the substance:
      a drill that records only that it happened tests attendance rather than
      the plan.
    columns:
      - {key: held_on, label: Held on, type: date, required: true}
      - {key: location, label: Location, type: text, required: true}
      - {key: scenario, label: Scenario, type: text, required: true}
      - {key: led_by, label: Led by, type: user, required: true}
      - {key: participants, label: Participants, type: int, required: true}
      - {key: evacuation_time, label: Time to clear (minutes), type: number}
      - {key: shortcomings, label: What did not work, type: longtext, required: true}
      - {key: actions, label: Actions arising, type: longtext}
---

What this document must establish for THIS organisation: what people do in the
first ten minutes of an emergency, before anyone with authority has arrived.

It must be written per site type rather than once for the whole organisation,
because an office, a shop floor and a remote work site have different exits,
different hazards and different distances from help. For each, it must name the
credible emergencies, the alarm, the route out, the muster point, the person who
accounts for who is present, and how someone who cannot self-evacuate is
assisted.

It must carry the contacts a person can reach without a network — printed,
posted, and current — and state who is responsible for keeping them current. It
must say when the plan is rehearsed and what a rehearsal must demonstrate to
count, because the drill this document declares is the only evidence that any of
the above is true rather than merely written.
