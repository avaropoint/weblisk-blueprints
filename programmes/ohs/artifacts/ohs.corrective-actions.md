---
id: ohs.corrective-actions
kind: procedure
title: Corrective and Preventive Action
structure: procedure
path: procedures/corrective-action.md

satisfies:
  - iso_45001:10.2
  - iso_45001:10.3
  - cor_2020:COR-02

requires: [ohs.incident-investigation]

declares:
  obligation:
    id: ohs.corrective-action-overdue
    # A CADENCE here, deliberately, and it terminates the chain.
    #
    # The obvious next link would be record-origin on this register — verify each
    # action after it closes. But the verification would be recorded in this same
    # register, and a trigger whose recording register is its own trigger register
    # discharges every occurrence the moment it creates one: a hundred per cent
    # recorded, nothing checked. So the chain ends with a periodic sweep of what
    # is open and late, which is the question a management review actually asks.
    activity: Review of corrective actions open past their due date
    cadence: each month
    responsible: health-safety-lead
    # A missed monthly review of what is open and late is itself the thing that
    # lets actions drift, so it escalates too — and it escalates to the position
    # that owns the programme rather than to a site.
    escalate: {after: 14d, to: health-safety-lead}
    applies_to: the organisation
    records: registers/corrective-action-reviews.md
  register:
    title: Overdue Action Review Record
    note: >
      One row per monthly sweep, not one per action. It is the terminal link of
      the incident chain and it records a COUNT and a decision: how many actions
      were open, how many were past their due date, how old the oldest one was,
      and what was done about them. A sweep that names no oldest action and
      raises nothing is a sweep that read the register and changed nothing,
      which is the failure this review exists to make visible.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: open_actions, label: Actions open, type: int, required: true}
      - {key: overdue_actions, label: Actions past their due date, type: int, required: true}
      - {key: oldest_overdue, label: Oldest overdue action, type: text}
      - {key: oldest_overdue_days, label: Days past due, type: int}
      - {key: extended, label: Extended, with the reason, type: longtext}
      - {key: escalated, label: Escalated, and to whom, type: longtext}
      - {key: accepted_as_risk, label: Accepted as a risk, and by whom, type: longtext}
---

What this document must establish for THIS organisation: how a finding becomes an
action with an owner and a date, and how anyone can tell later whether it worked.

It must accept findings from every source, not only from incidents. Inspections,
audits, committee meetings, legal evaluations and a worker raising a concern all
produce actions, and an organisation with a separate list per source has no way to
see that the same action is open on four of them.

It must distinguish CONTAINMENT from CORRECTION. Barricading the hole stops
somebody falling in today; it does not stop the hole. Both are legitimate and only
one closes the finding, and a register that cannot tell them apart will show a
programme closing actions while the hazard persists.

It must require an owner who is a person and a date that is a date. "Ongoing" is
not a date, and "the team" is not an owner — those two words are how an action
register becomes a list of intentions.

It must require EFFECTIVENESS to be checked after the fact, and say when. This is
the requirement most programmes drop, and dropping it is what makes continual
improvement unmeasurable: an action closed on time whose hazard recurred twice is
a finding about the action. The register records that as a state rather than
letting it disappear into a closed row.

It must say what happens when an action cannot be completed — extended with a
reason, escalated, or accepted as a risk by somebody with the authority to accept
it. An action quietly rolled forward four times is the clearest signal a programme
has stopped being managed, and the register should make that visible rather than
tidy.
