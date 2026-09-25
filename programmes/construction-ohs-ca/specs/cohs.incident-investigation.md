---
id: cohs.incident-investigation
kind: procedure
title: Project Incident Investigation
structure: procedure
path: procedures/project-incident-investigation.md

satisfies:
  - ohsa_ontario:25(2)(h)
  - cor_2020:COR-17
  - cor_2020:COR-02
  - iso_45001:10.2
  - isnetworld:ISN-SAFE-06

requires: [cohs.incident-reporting]

declares:
  obligation:
    id: cohs.incident-corrective-action
    # Record-origin again, one link along the chain. An investigation that names
    # a cause and produces no action is where this loop actually breaks, and it
    # breaks silently, because a completed report reads as completed work.
    #
    # Fourteen days after the investigation, not after the incident: the action
    # cannot be specified until the cause is known, and on a construction
    # project it often needs a quote, a shutdown window or a design change.
    activity: Corrective action arising from the investigation of a project incident
    for:
      records: registers/project-incident-investigations.md
      due: 14d after investigated_on
      key: reference
    authority: >
      ISO 45001:2018 cl. 10.2 requires action to eliminate the causes of an
      incident. No Ontario provision sets an interval for it
    interval_basis: chosen
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/project-corrective-actions.md
    escalate: {after: 7d, to: site-supervisor}
    satisfies: [iso_45001:10.2, iso_45001:10.3]
  register:
    title: Project Corrective Action Record
    note: >
      One row per action, keyed by the investigation or finding it arose from so
      the chain joins end to end, and carrying the project it applies to — or
      none, where the action is a change to the way the organisation works
      everywhere. `effectiveness` is the column most programmes omit and the only
      one that distinguishes an action taken from a problem solved: an action
      closed on time whose hazard recurred twice is a finding about the action.
    columns:
      - {key: reference, label: Reference, type: text, required: true}
      - {key: arose_from, label: Arose from, type: select, required: true,
         options: [Incident investigation, Site inspection, Equipment inspection,
                   Pre-task assessment, Committee, Management system audit,
                   Management review, Regulatory order or field visit,
                   Sub-trade requalification, Worker concern or work refusal, Other]}
      - {key: source_reference, label: Reference of the finding it arose from, type: text, required: true}
      - {key: project, label: Project, type: relation,
         target: /registers/projects.md#records, display: project_id}
      - {key: applies_everywhere, label: Applies to every project, not only this one, type: bool, required: true}
      - {key: action, label: Action, type: longtext, required: true}
      - {key: control_level, label: Where it sits in the hierarchy of controls, type: select, required: true,
         options: [Elimination, Substitution, Engineering control, Administrative control,
                   Personal protective equipment]}
      - {key: kind, label: Kind, type: select, required: true,
         options: ["Corrective — stops it recurring", "Preventive — stops it happening",
                   "Containment — holds the line meanwhile"]}
      - {key: owner, label: Owner, type: user, required: true}
      - {key: due_on, label: Due on, type: date, required: true}
      - {key: closed_on, label: Closed on, type: date}
      - {key: effectiveness, label: Effectiveness checked, type: select, required: true,
         options: [Not yet checked, Effective, Recurred, Superseded]}
      - {key: checked_on, label: Effectiveness checked on, type: date}
      - {key: checked_by, label: Effectiveness checked by, type: user}
---

What this document must establish for THIS organisation: how a reported incident
on a project is investigated, by whom, and what the investigation must produce.

It must separate the **immediate cause from the underlying one**, and require
both. "The worker slipped" is an immediate cause; it explains the injury and
predicts nothing. Why the surface was wet, why nobody was assigned to it, why the
last three reports of it went nowhere — that is the part an organisation can act
on, and an investigation that stops at the immediate cause is a description.

It must reach for **the sequence, not the moment**. Construction incidents are
almost never a single act: a crane lift happens late because a delivery was late,
so it happens in the dark, with a crew who were told about it at the end of the
shift, on ground that was not the ground the lift plan assumed. An investigation
that examines only the last link finds the rigger.

It must require the investigator to ask whether **the hazard was on that shift's
pre-task assessment**, and to say so on the record. Three answers are possible
and they are three different findings: it was assessed and the control failed, it
was assessed and the control was not used, or no assessment was done. Only the
first is a problem with the control.

It must set out **what the investigation owes**: a cause, a judgement about
whether it could recur, whether the same exposure exists on the organisation's
other projects, and a corrective action where it could. The obligation above is
the platform's half of that promise — an investigation recorded with no action
arising is visible as work outstanding rather than as a finished report.

It must require the action to be placed in the **hierarchy of controls** and say
why that column is not decoration. A corrective action that is "retrain the
crew" or "remind workers at the toolbox talk" is at the bottom of the hierarchy,
it is the most common action recorded in this industry, and it is the one least
likely to survive the crew changing. An organisation whose actions are
overwhelmingly administrative has an investigation process that stops at the
worker, and the register should be able to show that as a pattern rather than
one row at a time.

It must say what happens when the incident involved **a sub-trade's worker**.
The employer investigates its own worker's injury; the constructor is
answerable for the project and may not simply receive the employer's report. The
document must say what the constructor does with a sub-trade investigation it
does not accept, and who decides.

It must say when an investigation becomes **a serious-injury investigation** with
external involvement: when the scene must not be disturbed, when a Ministry
inspector will be on site, when legal advice is taken before statements are
recorded, and who speaks to the family. That paragraph is written before it is
needed or it is not written at all.

**Fourteen days for the action to be specified is this organisation's choice.**
Nothing in Ontario law sets it. It is chosen to be long enough that a real
engineering or procurement answer can be obtained rather than a reminder issued,
and short enough that the action is agreed while the incident is remembered. The
seven-day escalation is chosen for the same reason.
