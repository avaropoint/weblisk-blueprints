---
id: cohs.work-refusal
kind: procedure
title: Refusal of Unsafe Work, and Reprisal
structure: procedure
path: procedures/work-refusal.md

satisfies:
  - ohsa_ontario:43
  - ohsa_ontario:50
  - ohsa_ontario:25(2)(a)
  - ohsa_ontario:25(2)(i)
  - iso_45001:5.4
  - cor_2020:COR-05

requires: [cohs.constructor-duties]

approved_by: [senior-management]

declares:
  obligation:
    id: cohs.work-refusal-investigation
    # Record-origin. The statute's word is "forthwith" and there is no interval
    # in it, so the twenty-four hours below is not the law's and the basis says
    # so. What the record origin buys is that an unresolved refusal is a thing
    # the platform can name: a refusal reported on Tuesday and still sitting at
    # "reported" on Thursday is work outstanding, not a blank field.
    activity: Investigation of a work refusal, in the worker's presence, and its resolution
    for:
      records: registers/work-refusals.md
      due: 24h after reported_on
      key: reference
    authority: >
      OHSA s. 43(4) requires the investigation to be carried out FORTHWITH, in the
      presence of the worker and of a worker representative. The Act sets no
      number of hours; twenty-four is this organisation's outer limit for a
      refusal that has not been closed, not a permission to take a day
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: the organisation
    records: registers/work-refusal-investigations.md
    escalate: {after: 24h, to: health-safety-lead}
  register:
    title: Work Refusal Investigation Record
    note: >
      One row per refusal investigated, keyed by the refusal it belongs to.
      The two columns that make it evidence rather than a note are the
      **presence** columns: the Act requires the investigation to be carried out
      in the presence of the worker and of a worker member of the committee, a
      health and safety representative, or a worker chosen by the workers because
      of knowledge, experience and training. An investigation conducted without
      them is not the investigation the Act describes, however sound its
      conclusion.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: reference, label: Refusal, type: relation, required: true,
         target: /registers/work-refusals.md#records, display: reference}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: investigated_on, label: Investigated on, type: date, required: true}
      - {key: investigated_at, label: Time the investigation began, type: text, required: true}
      - {key: investigated_by, label: Investigated by, type: user, required: true}
      - {key: worker_present, label: The refusing worker was present, type: bool, required: true}
      - {key: representative_present, label: A worker representative was present, type: bool, required: true}
      - {key: representative, label: Who the representative was, and in what capacity, type: text, required: true}
      - {key: findings, label: What was found, type: longtext, required: true}
      - {key: action_taken, label: What was done about it, type: longtext, required: true}
      - {key: worker_satisfied, label: The worker returned to the work, type: select, required: true,
         options: ["Yes", "No — the refusal continued", Reassigned by agreement]}
      - {key: inspector_notified_at, label: Inspector notified at, type: text}
      - {key: workers_advised_of_continuing_refusal, label: Workers assigned the work were advised, in a representative's presence, type: select, required: true,
         options: ["Yes", "No other worker was assigned", "No — this was not done"]}
      - {key: corrective_action_reference, label: Corrective action raised, type: text}
      - {key: evidence, label: Statements, photographs and measurements, type: attachment}
---

What this document must establish for THIS organisation: what happens in the
first fifteen minutes after a worker says they will not do the work, who does
what, and what must never happen afterwards.

It must state the right **as a right**, in the words a worker would use, and
must be posted where workers can read it rather than filed. A refusal procedure
kept in the safety binder in the trailer office is a procedure that exists for
the auditor.

It must set out **the stages in order** and must not compress them:

- The worker **reports the refusal** promptly to their supervisor or employer,
  with the reason, and **remains in a safe place near the work station** during
  the first investigation unless directed elsewhere.
- The employer or supervisor **investigates forthwith, in the presence of the
  worker** and in the presence of a worker member of the committee, a health and
  safety representative, or a worker selected by the workers because of
  knowledge, experience and training. There is no lawful version of this step
  conducted alone.
- If the worker has **reasonable grounds to believe the danger persists** after
  that investigation, the refusal continues, and **an inspector is notified**.
  The inspector investigates in the presence of the same people and gives a
  written decision.
- The worker **stays available** at a safe place during the inspector's
  investigation and may be assigned reasonable alternative work; they may not be
  sent home without pay as a way of ending the refusal.
- Where the refused work is **given to another worker**, that worker is advised
  of the refusal and the reasons for it **in the presence of a worker
  representative**.

It must name **the exclusions accurately and narrowly**, and say that they are
legal questions rather than a supervisor's call. The right does not extend to
circumstances in which the danger is **inherent in the work or a normal
condition of it**, or in which the refusal would **directly endanger the life,
health or safety of another person** — and it applies differently to certain
classes of worker, which the document must list for the classes this
organisation actually employs rather than reciting all of them. A supervisor
told that "it's construction, it's always dangerous" is inherent danger has been
given a phrase that will end most refusals wrongly.

It must say what the **constructor** does when the refusing worker is a
sub-trade's. The employer owes the investigation; the constructor owes the
project. The document must say that the constructor may not treat it as somebody
else's problem, who from the organisation attends, and what happens if the
employer's investigation is not carried out or is not carried out in the
worker's presence.

It must state the **reprisal prohibition** in its own section, name the
consequence, and say how a worker raises a concern about reprisal to somebody
other than the person who would have committed it. It must also say that the
organisation will look for reprisal rather than wait to be told — the
`no_reprisal_confirmed_on` column on the register is that promise, and a
procedure that makes the promise without a date is making it to nobody.

It must say what is **written down and by whom**, and that the record is made
contemporaneously. A refusal is one of the few events in this programme where
the organisation's account and the worker's account may later be compared
directly, in a proceeding, and the only defence against that comparison is a
record made at the time in the presence of the people who were there.

**Twenty-four hours is this organisation's, and the document must be explicit
that the Act's word is "forthwith".** Nothing here licenses waiting a day: the
first investigation is owed immediately, and the interval exists only so that a
refusal still open the next morning is visible as outstanding work rather than
as a form nobody filled in.
