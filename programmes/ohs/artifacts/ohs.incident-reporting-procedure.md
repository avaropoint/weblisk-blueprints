---
id: ohs.incident-reporting-procedure
kind: procedure
title: Incident Reporting and Investigation
structure: procedure
path: procedures/incident-reporting.md

satisfies:
  - iso_45001:10.2
  - cor_2020:COR-17

requires: [ohs.policy]

declares:
  obligation:
    id: ohs.incident-investigation
    # Record-origin: one occurrence per reported incident, on its own clock.
    #
    # `cadence: each month` was a monthly meeting about a pile. It could not say
    # that INC-014 reported on the 2nd was still uninvestigated on the 20th —
    # only that this month's review had or had not happened. An incident has no
    # period; asking which month it belongs to has no answer, which is exactly
    # what the record origin exists for.
    #
    # Three days after it was REPORTED, not after it occurred: the clock the
    # organisation controls starts when it finds out.
    activity: Investigation of a reported incident
    for:
      records: registers/incidents.md
      due: 3d after reported_on
      key: reference
    responsible: health-safety-lead
    # Two days past a three-day deadline, and it becomes the site supervisor's
    # problem too. Short on purpose: the value of investigating an incident
    # decays fast — memories, the state of the workplace, whether the people
    # involved are still on shift — so a grace period measured in weeks
    # escalates something already too late to investigate properly.
    escalate: {after: 2d, to: site-supervisor}
    applies_to: each project
    records: registers/investigations.md
    satisfies: [iso_45001:10.2]
  register:
    title: Investigation Record
    note: >
      One row per investigation, keyed by the incident it belongs to so the two
      registers join. `cause_category` is a select rather than free text because
      the point of collecting causes is to count them: fourteen investigations
      each describing a slightly different lapse of attention are one finding,
      and prose cannot be added up.
    columns:
      - {key: reference, label: Reference, type: text, required: true}
      - {key: investigated_on, label: Investigated on, type: date, required: true}
      - {key: investigator, label: Investigated by, type: user, required: true}
      - {key: sequence, label: Sequence of events, type: longtext, required: true}
      - {key: immediate_cause, label: Immediate cause, type: longtext, required: true}
      - {key: cause_category, label: Underlying cause, type: select, required: true,
         options: [Equipment or design, Procedure absent or unclear, Procedure not followed,
                   Training or competence, Supervision, Planning or scheduling,
                   Communication, Environmental conditions, Other]}
      - {key: root_cause, label: Underlying cause, detail, type: longtext, required: true}
      - {key: recurrence_risk, label: Could recur, type: select, required: true,
         options: [Likely, Possible, Unlikely]}
      - {key: reviewed_by, label: Reviewed by, type: user}
---

What this document must establish for THIS organisation: how a worker reports
something that hurt somebody or nearly did, what happens in the hours after,
and how the organisation learns from it.

It must be reportable by the person closest to the event without permission,
because a procedure that routes reporting through a supervisor is a procedure
that under-reports what supervisors are involved in. It must define the classes
the organisation uses — injury, near miss, property damage, dangerous
occurrence — and state which of them carry an external reporting duty to a
regulator or insurer, with the time limit attached to each. Getting that list
wrong is the failure with a statutory consequence, so it must be written from
the jurisdictions this organisation actually operates in.

It must separate the immediate response from the investigation, require the
investigation to reach a cause rather than a person, and connect each corrective
action to a named position and a date. The obligation this document declares is
the platform's half of that: every row of the incident register raises an
investigation due three days after the incident was reported, so an incident
nobody looked into is visible as work outstanding rather than as a form that was
filled in.
