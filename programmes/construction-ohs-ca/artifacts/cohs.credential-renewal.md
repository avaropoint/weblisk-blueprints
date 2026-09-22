---
id: cohs.credential-renewal
kind: procedure
title: Credential Renewal
structure: procedure
path: procedures/construction/credential-renewal.md

satisfies:
  - iso_45001:7.2
  - isnetworld:ISN-SAFE-04

requires: [cohs.credential-register]

declares:
  obligation:
    id: cohs.credential-renewal
    activity: Renew a statutory credential before it expires, or restrict the work
    for:
      records: registers/construction/statutory-credentials.md
      due: 90d before expires_on
      key: reference
    authority: the issuing authority named on each row — see the register's `interval_source` and `authority` columns
    interval_basis: chosen
    responsible: training-coordinator
    applies_to: the organisation
    records: registers/construction/credential-renewals.md
    escalate: {after: 2w, to: site-supervisor}
  register:
    title: Credential Renewal Record
    note: >
      One row per credential acted on, keyed by the reference on the card it
      replaces. What this records is that somebody acted before a date. The
      register of credentials records what is HELD; holding a lapsed card and
      having done nothing about it are the same row there and different rows
      here.
    layout: form
    review: required
    approvers: [training-coordinator]
    columns:
      - {key: reference, label: Credential, type: relation, required: true,
         target: /registers/construction/statutory-credentials.md#records, display: reference}
      - {key: person, label: Person, type: user, required: true}
      - {key: first_chased_on, label: First acted on, type: date, required: true}
      - {key: booked_on, label: Seat booked on, type: date}
      - {key: course_date, label: Course date, type: date}
      - {key: completed_on, label: Completed on, type: date}
      - {key: new_reference, label: New certificate number, type: text}
      - {key: new_expires_on, label: New expiry, type: date}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Renewed, Booked, Lapsed, Work restricted, Left the organisation,
                   "No longer required"]}
      - {key: restriction, label: Work the person may no longer do, type: longtext}
      - {key: restriction_lifted_on, label: Restriction lifted on, type: date}
---

What this artifact must establish: that a credential due to expire was acted on
before it expired, and what happened to the person's work if it was not.

**Ninety days, where a certificate is often chased at thirty.** A replacement
insurance certificate is issued on request. A training ticket requires a seat on
a course that runs when the provider runs it, and in construction those courses
fill: Working at Heights and committee certification both have limited approved
delivery, both are three-year clocks that arrive for whole cohorts at once, and a
mandatory refresher everybody leaves until the last month is a refresher nobody
can book. The interval is the lead time of the slowest step, and it is this
organisation's number rather than anybody's requirement — the law sets the expiry,
not the notice period.

It must record BOOKED as an outcome distinct from RENEWED. A seat held on a
course three weeks from now is the correct state of a piece of work in progress,
and a register whose only positive outcome is completion forces the person doing
the chasing either to misstate it or to leave it blank.

**It must record what happened to the work when a credential lapsed.** This is
the heart of the artifact. A worker whose Working at Heights certificate has
expired has not fallen behind on paperwork: there is work they may no longer
lawfully do, and somebody either restricted them or did not. That decision is the
evidence, it is the one most likely to be missing after an incident, and it is
why `restriction` and `restriction_lifted_on` are columns rather than notes.

It must distinguish the credentials whose lapse makes the work unlawful from
those whose lapse is a contravention with nothing invalidated, and from those
that are only a client's condition. The register of credentials carries that
distinction on each row; this procedure must act on it differently in each case,
and must say so. Treating all three the same means either stopping work that
could lawfully continue or continuing work that could not.

It escalates to whoever controls what work is assigned, because that is the only
position that can act on a lapse. The training coordinator can book a course;
they cannot stop somebody climbing.

It is submitted as a form rather than typed into a grid, because a renewal
discharges an occurrence and an occurrence needs one attributable act.
