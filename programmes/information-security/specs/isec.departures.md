---
id: isec.departures
kind: register
title: Departures and Role Changes Register
structure: standard
path: registers/departures.md

satisfies:
  - iso_27001:A.6.5
  - iso_27001:A.5.11
  - soc2:CC6.2

register:
  title: Departures and Role Changes Register
  note: >
    One row per person leaving, or changing what they do enough that their
    access should change with them. The quarterly departure verification asks
    whether the leaver process worked; this register is what it works ON, and
    without it the verification is a count of the departures somebody
    remembered.

    `access_ends_on` is the column the work is raised from, and it is
    deliberately not `last_day`. For a resignation the two are the same date.
    For a dismissal, access ends before the conversation does, and a register
    that can only express the last working day cannot express the case that
    matters most.

    A row is opened when the departure is KNOWN, not when it happens. Notice
    periods are where the useful time is: everything on the row except the
    confirmations can be filled in weeks ahead.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: person, label: Person leaving, type: text, required: true}
    - {key: position, label: Position held, type: text, required: true}
    - {key: manager, label: Reporting position, type: text, required: true}
    - {key: change, label: Change, type: select, required: true,
       options: [Resignation, End of contract, End of engagement, Retirement,
                 Dismissal, Role change, Leave of absence]}
    - {key: notified_on, label: Known on, type: date, required: true}
    - {key: last_day, label: Last working day, type: date}
    - {key: access_ends_on, label: Access ends on, type: date, required: true}
    - {key: risk, label: Departure risk, type: select, required: true,
       options: [Routine, Holds privileged access, Holds regulated information,
                 Contested or involuntary, Going to a competitor]}
    - {key: systems_held, label: Systems and accounts held, type: longtext, required: true}
    - {key: privileged_access, label: Privileged or administrative access held, type: bool, required: true}
    - {key: assets_held, label: Equipment and keys held, type: longtext, required: true}
    - {key: shared_credentials, label: Knew shared or service credentials, type: bool, required: true}
    - {key: continuing_obligations, label: Continuing confidentiality obligations, type: select, required: true,
       options: [In contract, Separate undertaking, None identified]}
    - {key: status, label: Status, type: select, required: true,
       options: [Known, In progress, Completed, Reopened]}
---

What this artifact must establish: who is leaving, when their access must stop,
and what they hold that has to come back.

It exists because the security programme already measures the leaver process and
had nothing to measure it against. The quarterly verification counts accounts
still active for people who have gone; the number is only meaningful if there is
a list of who went.

`risk` is a column rather than a judgement made on the day, because the
difference between a routine leaver and a contested one is a difference in
sequence, not in thoroughness. A row marked *contested or involuntary* is one
where access ends before the conversation, and that decision has to be
recordable in advance by somebody who is not in the room.

`shared_credentials` is the column organisations discover they needed. An
individual account is closed by a process; a shared password the leaver knew is
closed by somebody deciding to change it, and nobody decides that unless the
register asks.

**A role change belongs here.** The accumulation of permissions across a career
is the access failure that no leaver process catches, and giving it a row makes
it the same piece of work rather than a good intention in a procedure.
