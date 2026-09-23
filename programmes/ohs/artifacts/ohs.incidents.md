---
id: ohs.incidents
kind: register
title: Incident Register
structure: standard
path: registers/incidents.md

# A register carries no `satisfies:`. The citation belongs on the procedure that
# says what this organisation does about incidents; this file is where it
# records them having happened. See ohs.incident-reporting-procedure.

requires: [ohs.incident-reporting-procedure]

register:
  title: Incident Register
  note: >
    One row per incident, opened when it is reported rather than when it is
    resolved. A near miss is an incident: a register that holds only injuries
    records the ones that were not prevented.

    The investigation used to be three columns here — investigator, cause,
    corrective action — and that is why nothing could be overdue. A column is
    filled in or it is not; it has no due date, nobody owns it, and an
    investigation that never happened looks exactly like one where somebody
    left the field blank. It is a register of its own now, triggered by these
    rows, so "INC-014's investigation is eleven days late" is a thing the
    platform can say.
  columns:
    # The stable identity every occurrence and attestation cites. Added when
    # the investigation obligation became record-origin: a trigger needs a key
    # that survives the row moving, and no other column is one — two incidents
    # can share a date, a location and a reporter.
    - {key: reference, label: Reference, type: text, required: true}
    - {key: occurred_on, label: Occurred on, type: date, required: true}
    - {key: reported_on, label: Reported on, type: date, required: true}
    - {key: location, label: Location, type: text, required: true}
    - {key: kind, label: Kind, type: select, required: true,
       options: [Near miss, First aid, Medical aid, Lost time, Property damage, Environmental]}
    - {key: reported_by, label: Reported by, type: user, required: true}
    - {key: description, label: What happened, type: longtext, required: true}
    - {key: immediate_action, label: Immediate action taken, type: longtext, required: true}
    - {key: closed_on, label: Closed on, type: date}
---

What this artifact must establish: every event that hurt somebody or could have,
recorded when it is REPORTED rather than when it is resolved.

It is a register of its own rather than columns on the reporting procedure
because the investigation has to be able to be late. A column is filled in or it
is not; it has no due date, nobody owns it, and an investigation that never
happened looks exactly like one where somebody left the field blank. These rows
are what the investigation obligation is triggered from, so "INC-014's
investigation is eleven days late" is a thing the platform can say.

A near miss is an incident. A register that holds only injuries records the ones
that were not prevented, and the organisation loses the only cheap warnings it
gets.

`reference` is the identity the whole chain joins on — the investigation cites
it, and the corrective action arising from that investigation cites it again. It
must be issued when the incident is reported and must never be reused, because
two incidents can share a date, a location and a reporter and nothing else here
tells them apart.
