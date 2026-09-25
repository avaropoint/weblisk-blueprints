---
id: ohs.training-renewal
kind: procedure
title: Training Renewal
structure: procedure
path: procedures/training-renewal.md

satisfies:
  - iso_45001:7.2
  - cor_2020:COR-16

requires: [ohs.training-records]

declares:
  obligation:
    id: ohs.training-renewal
    activity: Renew a credential before it expires
    for:
      records: registers/training-records.md
      due: 60d before expires_on
      key: reference
    responsible: training-coordinator
    applies_to: the organisation
    records: registers/training-renewals.md
    escalate: {after: 14d, to: site-supervisor}
  register:
    title: Training Renewal Record
    note: >
      One row per credential renewed, keyed by the reference on the card it
      replaces. What this records is that somebody acted before a date — the
      register of credentials records what is held, and holding a lapsed card is
      not the same as having done nothing about it.
    layout: form
    review: required
    approvers: [training-coordinator]
    columns:
      - {key: reference, label: Credential renewed, type: relation,
         target: /registers/training-records.md#records, display: reference}
      - {key: person, label: Person, type: user, required: true}
      - {key: booked_on, label: Course booked on, type: date}
      - {key: completed_on, label: Completed on, type: date}
      - {key: new_reference, label: New certificate number, type: text}
      - {key: new_expires_on, label: New expiry, type: date}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Renewed, Booked, Lapsed, Work restricted, No longer required]}
      - {key: restriction, label: Work restricted to, type: longtext}
---

What this artifact must establish: that a credential due to expire was acted on
before it expired, and what happened to the person's work if it was not.

Sixty days, where a certificate is chased at thirty. A replacement insurance
certificate is issued on request; a training ticket requires a seat on a course
that runs when the provider runs it, and a mandatory refresher that everybody
leaves until the last month is a refresher nobody can book. The interval is the
lead time of the slowest step, not a round number.

It must record BOOKED as an outcome distinct from RENEWED. A seat held on a
course three weeks from now is the correct state of a piece of work in progress,
and a register whose only positive outcome is completion forces the person doing
the chasing to either lie or leave it blank.

It must record what happened to the work when a credential lapsed. A person
whose fall-protection training has expired has not merely fallen behind on
paperwork — there is work they may no longer do, and somebody decided either to
restrict them or not to. That decision is the evidence, and it is the one most
likely to be missing after an incident.

It escalates to whoever controls what work is assigned, because that is the only
person who can act on a lapse. The training coordinator can book a course; they
cannot stop somebody climbing.

It is submitted as a form rather than typed into a grid, because a renewal
discharges an occurrence and an occurrence needs one attributable act.
