---
id: cohs.incidents
kind: register
title: Register of Project Incidents
structure: standard
path: registers/project-incidents.md

# A register carries no `satisfies:`.
#
# It is the evidence that work happened, not the document that answers a
# control — and the relation vocabulary says so structurally: `implements`
# onto a control may be asserted by a blueprint, a policy or a procedure,
# and by nothing else. A register citing a control could never be recorded
# as answering it, so it sat at `present_uncited` permanently and capped the
# tier's readiness at a number no amount of work could move.
#
# The citation belongs on the procedure that declares this register, which
# is where the organisation states what it does; this file is where it
# records having done it.

requires: [cohs.incident-reporting]

register:
  title: Register of Project Incidents
  note: >
    One row per incident, on one project, opened when it is REPORTED rather
    than when it is resolved. A near miss is an incident and a first aid
    treatment is an incident: a register that holds only lost-time injuries
    records the ones that were not prevented, which is the smallest and
    latest slice of what the organisation could have known.

    `project` is a relation and not a typed-in location, and that is the
    reason this register exists separately from the generic one. Almost every
    question a constructor is actually asked — by an owner, by a
    prequalification reviewer, by its own board — is per job site: how many
    near misses on this job, how many first aids this month, how does this
    site compare with the other eleven. A free-text `location` column cannot
    answer any of them, because "Bay St", "Bay Street" and "bay st." are three
    sites to a machine and one to a person.

    It is deliberately NOT the notifiable events register. Only some of these
    rows carry a statutory clock; those are opened here AND there, joined by
    `notifiable_event`, so that four events with a notice duty are never
    buried among two hundred rows that have none.
  layout: form
  columns:
    # The stable identity the whole chain joins on. Two incidents can share a
    # date, a project and a reporter and nothing else here tells them apart,
    # and a row number renumbers under a signature that still verifies.
    - {key: reference, label: Reference, type: text, required: true}
    - {key: project, label: Project, type: relation, required: true,
       target: /registers/projects.md#records, display: project_id}
    - {key: occurred_on, label: Occurred on, type: date, required: true}
    - {key: occurred_at, label: Time of day, type: text}
    - {key: reported_on, label: Reported on, type: date, required: true}
    - {key: reported_by, label: Reported by, type: user, required: true}
    - {key: exact_location, label: Where on the project, type: text, required: true}
    - {key: kind, label: Kind, type: select, required: true,
       options: [Near miss, First aid only, Medical aid, Modified or restricted work,
                 Lost time, Occupational illness, Property damage, Environmental release,
                 Utility strike, Fire, Security or trespass]}
    - {key: person_affected, label: Person affected, type: user}
    - {key: their_employer, label: Their employer, type: text, required: true}
    - {key: our_role, label: Our role in relation to them, type: select, required: true,
       options: [Their employer, Constructor only, Constructor and their employer, Neither]}
    - {key: activity, label: What the work was, type: longtext, required: true}
    - {key: description, label: What happened, type: longtext, required: true}
    - {key: immediate_action, label: Immediate action taken, type: longtext, required: true}
    - {key: potential_severity, label: Had it gone worst-case, type: select, required: true,
       options: [Fatality or critical injury, Serious injury, Minor injury,
                 No injury possible]}
    - {key: first_aid_given, label: First aid given, and by whom, type: text}
    - {key: hazard_class, label: Hazard, type: select, required: true,
       options: [Fall from height, Struck by, Caught in or between, Contact with electricity,
                 Overexertion or ergonomic, Slip, trip or fall on the level,
                 Excavation or ground failure, Hoisting or rigging, Mobile equipment or vehicle,
                 Hazardous substance exposure, Confined space, Fire or explosion, Other]}
    - {key: notifiable_event, label: Also entered on the notifiable events register as, type: relation,
       target: /registers/notifiable-events.md#records, display: reference}
    - {key: wsib_reportable, label: Reportable to the workers' compensation board, type: select, required: true,
       options: ["Yes", "No", Not yet determined]}
    - {key: closed_on, label: Closed on, type: date}
---

What this artifact must establish: every event on every project that hurt
somebody or could have, recorded when it is REPORTED, against the job it
happened on.

**The project relation is the artifact.** The generic incident register in the
occupational health and safety programme carries a free-text `location`, which
is right for an employer with one workplace and wrong for a constructor with
fourteen. Counting near misses per job site is not a report somebody runs
afterwards from prose; it is a join, and a join needs a key. Every row here
cites a row of the project register by its `project_id`, so the same identity
that carries the notice of project, the committee threshold and the
defibrillator duty also carries the incident count.

**A near miss is an incident, and a first aid is an incident.** They are the two
classes organisations most often leave out, and they are the two with the most
information in them: they are frequent enough to trend on a single job, and they
cost nothing to collect. An organisation that records only lost time is steering
by the smallest, latest and noisiest signal it has. This is also the register
that makes `cohs.safety-statistics` honest — the near-miss and first-aid counts
on that monthly row must be **counted from these rows**, not typed in from
memory, and the document should say where each figure came from.

**`potential_severity` is separate from `kind`, and it is the column that earns
the register.** What happened is history; what could have happened is the only
thing in a near miss worth acting on. A scaffold plank dropped four storeys into
an empty hoarding is `Near miss` and `Fatality or critical injury`, and an
organisation that sorts by `kind` alone will never look at it again.

**It must be reportable by the person closest to the event, without
permission.** A procedure that routes reporting through a supervisor
under-reports exactly the incidents supervisors are involved in, and on a
construction project it also under-reports everything a sub-trade would rather
the constructor did not hear about. The document must say plainly that reporting
is expected of every worker of every employer on the project, that it is never
a disciplinary event in itself, and what happens to somebody who is
discouraged from reporting.

**It is a form and not a table.** A table commits every keystroke, so a
half-typed account of an injury lands in the governance repository as a
statement of fact while somebody is still finding out what happened. A form
drafts and commits once, attributably, which is also what gives the
investigation clock a single moment to run from. It is deliberately **not**
`review: required`: the investigation is owed three days after the incident was
reported, and a report waiting for a manager's approval would stop that clock
starting at the moment the organisation actually found out.

**`our_role` is required for the same reason it is required on the notifiable
events register.** On a construction project the duties split, and the same
organisation is a constructor on one job and a sub-trade on another in the same
month. An incident to a sub-trade's worker on our project is our incident as
constructor whether or not it is our worker, and a register that cannot say
which will produce a statistic that means nothing.

**`notifiable_event` is a relation and not a boolean**, because the two
registers are joined and the join has to be checkable in both directions. An
incident marked notifiable with no row on the other register is the single most
expensive error this programme can make, and it is visible as an empty cell
rather than as a tick somebody made.

**No retention period is declared here, and that is stated rather than
omitted.** The periods that reach these records come from several instruments
with different clocks, and at least one of them — the first aid record under the
first aid regulation — has **no prescribed retention period at all**. A worker's
claim can be reopened years later and the incident record is the only
contemporaneous account of it. The organisation should set its own period,
generously, and record which rule it is implementing. A number inherited from
this pack would be a guess wearing a citation.
