---
id: cohs.corrective-actions
kind: procedure
title: Corrective and Preventive Action Across Projects
structure: procedure
path: procedures/project-corrective-action.md

satisfies:
  - cor_2020:COR-02
  - iso_45001:10.2
  - iso_45001:10.3
  - iso_45001:9.1.2
  - isnetworld:ISN-SAFE-06

requires: [cohs.incident-investigation]

declares:
  obligation:
    id: cohs.corrective-action-sweep
    # A CADENCE here, deliberately, and it TERMINATES the chain.
    #
    # The obvious next link would be record-origin on the corrective action
    # register — verify each action after it closes. But the verification would
    # be recorded in that same register, and a trigger whose recording register
    # is its own trigger register discharges every occurrence the moment it
    # creates one: a hundred per cent recorded, nothing checked. So the chain
    # ends with a periodic sweep of what is open and late.
    #
    # And it is ONE sweep for the organisation rather than one per project. The
    # question it answers is whether actions are drifting across the business —
    # per-project sweeps would hide the site that is quietly carrying all of
    # them, which is the only site anybody needs to know about.
    activity: Review of corrective actions open past their due date across every project
    cadence: each month
    authority: >
      ISO 45001:2018 cl. 10.2 requires the effectiveness of corrective action to
      be reviewed. No Ontario provision requires this review or sets an interval
    interval_basis: chosen
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/project-corrective-action-reviews.md
    escalate: {after: 14d, to: senior-management}
  register:
    title: Overdue Action Review Record
    note: >
      One row per monthly sweep, not one per action. It is the terminal link of
      the incident chain and it records COUNTS and a decision: how many actions
      were open, how many were past their due date, how old the oldest was, which
      project is carrying the most, and what was done about them. A sweep that
      names no oldest action and raises nothing is a sweep that read the register
      and changed nothing, which is the failure this review exists to make
      visible.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: incidents_reported, label: Incidents reported in the period, type: int, required: true}
      - {key: incidents_uninvestigated, label: Of those, still uninvestigated past three days, type: int, required: true}
      - {key: open_actions, label: Actions open, type: int, required: true}
      - {key: overdue_actions, label: Actions past their due date, type: int, required: true}
      - {key: oldest_overdue, label: Oldest overdue action, type: text}
      - {key: oldest_overdue_days, label: Days past due, type: int, required: true}
      - {key: worst_project, label: Project carrying the most overdue actions, type: relation,
         target: /registers/projects.md#records, display: project_id}
      - {key: recurred, label: Actions closed and then recurred, type: int, required: true}
      - {key: extended, label: Extended, with the reason, type: longtext}
      - {key: escalated, label: Escalated, and to whom, type: longtext}
      - {key: accepted_as_risk, label: Accepted as a risk, and by whom, type: longtext}
      - {key: projects_not_reporting, label: Live projects that reported no incident at all this period, type: longtext, required: true}
---

What this document must establish for THIS organisation: how a finding from any
source becomes an action with an owner and a date, and how anybody can tell later
whether it worked.

It must **accept findings from every source**, not only from incidents. Site
inspections, equipment inspections, pre-task assessments, committee meetings, a
Ministry field visit, a sub-trade's requalification, a worker's concern and a
work refusal all produce actions. An organisation with a separate list per source
cannot see that the same action is open on four of them, and it will close it on
one and report it.

It must distinguish **containment from correction**. Barricading the opening
stops somebody falling in today; it does not stop the opening. Both are
legitimate and only one closes the finding, and a register that cannot tell them
apart will show a programme closing actions while the hazard persists.

It must require an **owner who is a person and a date that is a date**.
"Ongoing" is not a date and "the site team" is not an owner: those two are how an
action register becomes a list of intentions.

It must require **effectiveness to be checked** after the fact, and say when.
This is the requirement most programmes drop, and dropping it is what makes
improvement unmeasurable. An action closed on time whose hazard recurred twice is
a finding about the action, and the register records that as a state rather than
letting it disappear into a closed row.

It must say what happens when an action **cannot be completed** — extended with a
reason, escalated, or accepted as a risk by somebody with the authority to accept
it. An action quietly rolled forward four times is the clearest signal a
programme has stopped being managed.

**The count this review must not omit is the projects that reported nothing.**
On a construction programme, a live job with no incidents, no near misses and no
first aids in a month is far more likely to be a job that is not reporting than a
job with nothing to report. A sweep that counts only what arrived measures the
sites that are participating and is silent about the ones that are not — and
silence reads as a good month. `projects_not_reporting` is required so that the
absence is written down by name, and so that the safety statistics compiled from
the same rows can be read with it beside them.

**The monthly interval is this organisation's choice.** Nothing in Ontario law
requires this review. A month is chosen because it matches the statistics
compilation and the committee cycle, so the same numbers are discussed once
rather than assembled three times; and because a sweep run less often than the
shortest action deadline cannot catch an action before it is stale.
