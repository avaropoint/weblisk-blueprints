---
id: cohs.work-refusals
kind: register
title: Register of Work Refusals
structure: standard
path: registers/work-refusals.md

# A register carries no `satisfies:`. The citation belongs on the procedure that
# says what this organisation does when a worker refuses; this file is where it
# records that it happened, and when.

requires: [cohs.work-refusal]

register:
  title: Register of Work Refusals
  note: >
    One row per refusal, on one project, opened when the worker reports it and
    not when it is resolved. The register exists because the statute's process
    is timed and staged and because the whole of it happens in minutes: the
    worker reports, the work stops, the first investigation happens **in the
    worker's presence** and in the presence of a worker representative, and only
    if the worker still has reasonable grounds does an inspector attend.

    It is deliberately NOT part of the incident register. A refusal is not an
    incident; it is the Act working. Filing them together teaches an
    organisation to count refusals as bad news, which is the attitude that
    produces the reprisal this register also exists to make visible.
  layout: form
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: project, label: Project, type: relation, required: true,
       target: /registers/projects.md#records, display: project_id}
    - {key: reported_on, label: Reported on, type: date, required: true}
    - {key: reported_at, label: Time reported, type: text, required: true}
    - {key: worker, label: Worker, type: user, required: true}
    - {key: their_employer, label: Their employer, type: text, required: true}
    - {key: our_role, label: Our role in relation to them, type: select, required: true,
       options: [Their employer, Constructor only, Constructor and their employer, Neither]}
    - {key: reported_to, label: Reported to, type: user, required: true}
    - {key: work_refused, label: The work refused, type: longtext, required: true}
    - {key: grounds, label: The worker's grounds, type: longtext, required: true}
    - {key: ground_class, label: Class of ground, type: select, required: true,
       options: [Equipment or machine likely to endanger, Physical condition of the workplace,
                 Contravention likely to endanger, Workplace violence, Other]}
    - {key: work_stopped, label: The work stopped, type: bool, required: true}
    - {key: worker_in_safe_place, label: The worker remained in a safe place near the work station, type: bool, required: true}
    - {key: others_assigned, label: Anybody else was assigned to the refused work, type: bool, required: true}
    - {key: others_advised, label: If so, they were advised of the refusal and its grounds in the presence of a representative, type: bool}
    - {key: excluded_worker, label: The worker is in a class the right does not extend to, type: select, required: true,
       options: ["No", "Yes — the danger is inherent or a normal condition of the work",
                 "Yes — the refusal would directly endanger another person's life, health or safety",
                 Not yet determined]}
    - {key: stage, label: Stage reached, type: select, required: true,
       options: [Reported, First investigation under way, Resolved at the first stage,
                 Continued refusal, Inspector notified, Inspector attended,
                 Inspector's decision received, Closed]}
    - {key: outcome, label: Outcome, type: longtext}
    - {key: inspector_decision, label: Inspector's decision, type: longtext}
    - {key: no_reprisal_confirmed_on, label: No-reprisal check completed on, type: date}
    - {key: closed_on, label: Closed on, type: date}
---

What this artifact must establish: every occasion on which a worker on one of
this organisation's projects exercised the right to refuse unsafe work, what was
done in the minutes and hours that followed, and what became of the worker
afterwards.

**It is not a disciplinary record and the document must say so on its face.** A
refusal is the Act operating as designed. An organisation whose register of
refusals is empty across fourteen live projects and several years has not
achieved anything; it has either never told anybody the right exists, or it has
made using it expensive. That is a finding, and it is only visible if the
register is kept.

**`our_role` is required because a constructor's position is different from an
employer's.** The right runs against the worker's own employer, and it is the
employer's investigation. But the refusal happens on the constructor's project,
the hazard is frequently the constructor's or another trade's, and the
constructor is the one who must ensure every employer on the project complies.
A register that cannot say which hat the organisation was wearing cannot say
whose investigation was owed.

**`others_assigned` and `others_advised` are a pair, and they are here because
this is the part that is skipped.** Where the refused work is given to another
worker, that worker must be advised of the refusal and the reasons for it, in
the presence of a worker representative. Assigning the work quietly to somebody
who was not told is both a contravention and the fastest way to turn one
refusal into an injury.

**`excluded_worker` is a select with a "not yet determined" option** because the
exclusions are narrow, they are legal questions, and they are routinely asserted
on the spot by a supervisor who wants the work done. Whether a danger is inherent
in the work or a normal condition of it, and whether the refusal would directly
endanger another life, are not decisions to be recorded as a supervisor's
opinion. A boolean would force a guess to be written down as a finding.

**`no_reprisal_confirmed_on` is a column and not a sentence in a policy.** The
prohibition on reprisal is a separate section of the Act with its own
consequences, and the reprisal that follows a refusal is almost never a
dismissal on the day — it is fewer hours next month, a transfer to a worse crew,
a lay-off in the next slow week. A date on this row is the organisation
recording that somebody looked, deliberately, after enough time had passed for
it to be possible.

**Timestamps are recorded to the minute, not the day.** Every stage of the
statutory process is measured against the moment before it and the record is
otherwise unreconstructable. `reported_at` is text for the same reason the
inspector-notification time is text on the notifiable events register: what
matters is that a human wrote down the clock time they saw.
