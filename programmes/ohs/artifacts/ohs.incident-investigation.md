---
id: ohs.incident-investigation
kind: procedure
title: Incident Investigation
structure: procedure
path: procedures/incident-investigation.md

satisfies:
  - iso_45001:10.2
  - cor_2020:COR-17

requires: [ohs.incident-reporting-procedure]

declares:
  obligation:
    id: ohs.corrective-action
    # Record-origin again, one link further along the chain. An investigation
    # that names a cause and produces no action is where most of this loop
    # actually breaks — and it breaks silently, because a report reads as
    # completed work.
    #
    # Fourteen days after the investigation, not after the incident: the action
    # cannot be specified until the cause is known.
    activity: Corrective action arising from an investigation
    for:
      records: registers/investigations.md
      due: 14d after investigated_on
      key: reference
    responsible: health-safety-lead
    # A week, because specifying a corrective action needs the cause understood
    # and sometimes needs a quote or a shutdown window. Longer than the
    # investigation's grace and still short enough that the action is agreed
    # while the incident is remembered.
    escalate: {after: 7d, to: site-supervisor}
    applies_to: each project
    records: registers/corrective-actions.md
    satisfies: [iso_45001:10.2]
  register:
    title: Corrective Action Record
    note: >
      One row per action, keyed by the investigation or finding it arose from so
      the chain joins end to end. `effectiveness` is the column most programmes
      omit and the only one that distinguishes an action taken from a problem
      solved: an action closed on time whose hazard recurred twice is a finding
      about the action, not a success.
    columns:
      - {key: reference, label: Reference, type: text, required: true}
      - {key: arose_from, label: Arose from, type: select, required: true,
         options: [Investigation, Inspection, Audit, Committee, Management review,
                   Legal evaluation, Worker concern, Other]}
      - {key: action, label: Action, type: longtext, required: true}
      - {key: kind, label: Kind, type: select, required: true,
         options: [Corrective — stops it recurring, Preventive — stops it happening,
                   Containment — holds the line meanwhile]}
      - {key: owner, label: Owner, type: user, required: true}
      - {key: due_on, label: Due on, type: date, required: true}
      - {key: closed_on, label: Closed on, type: date}
      - {key: effectiveness, label: Effectiveness checked, type: select, required: true,
         options: [Not yet checked, Effective, Recurred, Superseded]}
      - {key: checked_on, label: Effectiveness checked on, type: date}
---

What this document must establish for THIS organisation: how a reported incident
is investigated, by whom, and what the investigation must produce.

It must separate the IMMEDIATE cause from the underlying one, and require both.
"The worker slipped" is an immediate cause; it explains the injury and predicts
nothing. Why the floor was wet, why nobody was assigned to it, why the last three
reports of it went nowhere — that is the part an organisation can act on, and an
investigation that stops at the immediate cause is a description.

It must not treat "human error" as a finding. It is where an investigation stops
rather than what it found, and a programme whose causes are mostly human error has
a procedure that ends one question early. The document should say so, and name the
next question: what made the error easy to make and hard to notice.

It must require the people who do the work to be involved. An investigation
conducted entirely from the incident form arrives at the cause the form's fields
allow.

It must set who may investigate what — proportionate to severity, and never the
person accountable for the area alone. A supervisor investigating an incident in
their own crew is being asked to find their own supervision at fault.

It must state what the investigation OWES: a cause, a judgement about whether it
could recur, and a corrective action if it could. The obligation above is the
platform's half of that promise — an investigation recorded without an action
arising is visible as work outstanding rather than as a finished report.

It must say what happens when the cause is a document. Where an investigation
finds a procedure absent, unclear or unfollowable, the change belongs in the
document control programme rather than in a note on this form.
