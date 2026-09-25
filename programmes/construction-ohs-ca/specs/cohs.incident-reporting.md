---
id: cohs.incident-reporting
kind: procedure
title: Project Incident Reporting
structure: procedure
path: procedures/project-incident-reporting.md

satisfies:
  - ohsa_ontario:25(2)(a)
  - ohsa_ontario:9(26)
  - cor_2020:COR-17
  - iso_45001:10.2
  - isnetworld:ISN-SAFE-06

requires: [cohs.policy, cohs.project-register]

approved_by: [senior-management]

declares:
  obligation:
    id: cohs.incident-investigation
    # Record-origin: one occurrence per reported incident, on its own clock.
    #
    # A cadence here would be a monthly meeting about a pile. It could not say
    # that the incident reported on the 2nd was still uninvestigated on the
    # 20th — only that this month's review had or had not happened. An incident
    # has no period, and asking which month it belongs to has no answer.
    #
    # Three days after it was REPORTED, not after it occurred. The clock this
    # organisation controls starts when it finds out, and on a construction
    # project the gap between the two is routinely days: a sub-trade's worker
    # tells their own foreman, and the constructor hears on Monday.
    activity: Investigation of an incident reported on a project
    for:
      records: registers/project-incidents.md
      due: 3d after reported_on
      key: reference
    authority: >
      ISO 45001:2018 cl. 10.2 and COR 2020 require incidents to be investigated.
      No Ontario provision sets an interval for investigating an incident that is
      not a notifiable event — the clocks that ARE set in law run on the NOTICES,
      and they are in the statutory notice procedure
    interval_basis: chosen
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/project-incident-investigations.md
    # Two days past a three-day deadline, and it becomes the site supervisor's
    # problem as well. Short on purpose: the value of investigating decays fast
    # on a construction project, because the site itself changes. The excavation
    # is backfilled, the scaffold is struck, the crew has moved to another job.
    escalate: {after: 2d, to: site-supervisor}
    satisfies: [iso_45001:10.2, cor_2020:COR-17]
  register:
    title: Project Incident Investigation Record
    note: >
      One row per investigation, keyed by the incident it belongs to so the two
      registers join, and carrying the project so an investigation can be read
      without opening the incident. `cause_category` is a select rather than
      free text because the point of collecting causes is to count them:
      fourteen investigations each describing a slightly different lapse of
      attention are one finding, and prose cannot be added up.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: reference, label: Incident, type: relation, required: true,
         target: /registers/project-incidents.md#records, display: reference}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: investigated_on, label: Investigated on, type: date, required: true}
      - {key: investigator, label: Investigated by, type: user, required: true}
      - {key: worker_representative, label: Worker member or representative who took part, type: user}
      - {key: employers_involved, label: Employers whose workers took part, type: longtext, required: true}
      - {key: sequence, label: Sequence of events, type: longtext, required: true}
      - {key: immediate_cause, label: Immediate cause, type: longtext, required: true}
      - {key: cause_category, label: Underlying cause, type: select, required: true,
         options: [Equipment or design, Procedure absent or unclear, Procedure not followed,
                   Training or competence, Supervision, Planning or sequencing,
                   Coordination between employers, Communication, Ground or weather conditions,
                   Housekeeping, Other]}
      - {key: root_cause, label: Underlying cause, detail, type: longtext, required: true}
      - {key: pre_task_assessment_covered, label: The hazard was on that shift's pre-task assessment, type: select, required: true,
         options: ["Yes", "No", No assessment was done, Not applicable]}
      - {key: recurrence_risk, label: Could recur, type: select, required: true,
         options: [Likely, Possible, Unlikely]}
      - {key: recurs_on_other_projects, label: The same exposure exists on other projects, type: select, required: true,
         options: ["Yes", "No", Not yet checked]}
      - {key: committee_informed_on, label: Committee or representative informed on, type: date}
      - {key: evidence, label: Photographs, statements and measurements, type: attachment}
      - {key: reviewed_by, label: Reviewed by, type: user}
---

What this document must establish for THIS organisation: how anybody on any of
its projects reports something that hurt somebody or nearly did, what happens in
the hours afterwards, and how the organisation learns from it across every job
rather than on the one it happened on.

It must say that **reporting is owed by every worker of every employer on the
project**, to the constructor and not only to their own employer. This is the
sentence that makes the register a constructor's register rather than an
employer's, and it is the one most often missing: a sub-trade that reports
internally and says nothing has left the person answerable for the whole project
unable to answer for it.

It must define the **classes the organisation uses** and be explicit that a near
miss and a first aid are both incidents. It must then say which of those classes
carry an **external duty**, with the time limit attached to each, and must send
the reader to the statutory notice procedure rather than restating the clocks —
they are severe, they change, and a second copy of them will be the one somebody
reads at two in the morning after it has gone out of date.

It must separate the **immediate response** from the investigation. Make safe,
get care, preserve the scene where a person was killed or critically injured,
account for everybody, and only then find out why. A procedure whose first
numbered step is "complete the incident form" has got the order wrong, and the
order is the part that matters in the first ten minutes.

It must state **who investigates what**, proportionate to severity, and must
never leave an incident to be investigated only by the person accountable for
the area. A supervisor investigating an incident in their own crew is being
asked to find their own supervision at fault, and on a construction project the
equivalent error is a constructor accepting a sub-trade's own investigation of
its own worker's injury as the whole of the answer.

It must require the **people who do the work** to be involved, and must involve
the committee or the health and safety representative where the project has one.
An investigation conducted from the form arrives at the cause the form's fields
allow.

It must not treat **"human error" as a finding**. It is where an investigation
stopped, not what it found, and a programme whose causes are mostly human error
has a procedure that ends one question early. The next question is what made the
error easy to make and hard to notice.

It must say what happens when **the same exposure exists on another project**.
This is the one thing a multi-site constructor can do that a single-workplace
employer cannot, and it is the whole value of holding incidents centrally: an
investigation that finds an unguarded opening on one job and does not cause
somebody to walk the other eleven has learned nothing the organisation can use.
The column is on the record so that "not yet checked" is a visible state rather
than an omission.

It must say what happens when the cause is **a document**. Where an
investigation finds a procedure absent, unclear or unfollowable, the change
belongs in the document control programme, on that programme's clock, and not in
a note on this form.

**The three-day interval is this organisation's choice and the document must say
so.** No Ontario provision sets a time limit for investigating an incident that
is not a notifiable event. Three days is chosen because the site is still in the
state it was in, the people involved are still on the job, and the crew has not
yet rotated — and because anything longer is, in practice, a decision not to
investigate. The escalation after two more days is also this organisation's.
