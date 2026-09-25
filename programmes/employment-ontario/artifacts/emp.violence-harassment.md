---
id: emp.violence-harassment
kind: procedure
title: Workplace Violence and Harassment
structure: procedure
path: procedures/workplace-violence-and-harassment.md

satisfies:
  - ohsa_ontario:32.0.1
  - ohsa_ontario:32.0.2
  - ohsa_ontario:32.0.3
  - ohsa_ontario:32.0.4
  - ohsa_ontario:32.0.5
  - ohsa_ontario:32.0.6
  - ohsa_ontario:32.0.7
  - ohsa_ontario:32.0.8
  - ohrc_ontario:5(2)
  - ohrc_ontario:7(2)

requires: [emp.human-rights]
approved_by: [senior-management]

declares:
  obligation:
    id: emp.violence-harassment-review
    activity: Review the workplace violence policy, the workplace harassment policy and the harassment programme
    cadence: each year
    authority: OHSA ss. 32.0.1(1)(c) and 32.0.7(1)(c) — both policies and the harassment programme reviewed at least annually
    interval_basis: required
    responsible: hr-lead
    applies_to: the organisation
    records: registers/workplace-violence-harassment-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Workplace Violence and Harassment Review Record
    note: >
      One row per review. The violence risk assessment is a separate column from
      the policy review because it is a separate duty on a different trigger:
      the policies are reviewed annually, and the assessment is reassessed as
      often as is necessary — an event-driven duty with no clock, where the
      event is usually a change in the work, the workplace or who is in it.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: violence_policy_reviewed, label: Violence policy reviewed, type: bool, required: true}
      - {key: harassment_policy_reviewed, label: Harassment policy reviewed, type: bool, required: true}
      - {key: harassment_programme_reviewed, label: Harassment programme reviewed, type: bool, required: true}
      - {key: consulted, label: Committee or health and safety representative consulted, type: bool, required: true}
      - {key: risk_assessment_current, label: Violence risk assessment current, type: bool, required: true}
      - {key: risk_assessment_last_done, label: Risk assessment last carried out, type: date}
      - {key: domestic_violence_measures, label: Domestic violence measures in place where a risk is known, type: bool, required: true}
      - {key: incidents_in_period, label: Incidents and complaints in the period, type: int, required: true}
      - {key: investigations_completed, label: Investigations completed, type: int, required: true}
      - {key: results_in_writing, label: Results given in writing to both parties in every case, type: bool, required: true}
      - {key: changes_made, label: Changes made, type: longtext, required: true}
---

What this document must establish for THIS organisation: the two policies the
Occupational Health and Safety Act requires, the programme that implements the
harassment one, and the measures that implement the violence one.

It must keep violence and harassment separate, because the Act does. Workplace
violence is the exercise or threat of physical force; workplace harassment is a
course of vexatious comment or conduct that is known or ought reasonably to be
known to be unwelcome, and it expressly includes workplace sexual harassment. The
duties differ: violence requires a risk assessment and control measures, and
harassment requires a written programme setting out how complaints are made and
investigated.

It must set out how a worker reports — including how to report when the person
to report to is the employer or the supervisor, which is the case the Act names
and the one most programmes omit.

It must say how an investigation is conducted, by whom, and what both parties
are told. The Act requires an investigation appropriate in the circumstances and
requires the worker who complained and the alleged harasser, if a worker, to be
informed in writing of the results and of any corrective action. A programme that
investigates and tells nobody the outcome has met neither.

It must cover domestic violence. Where an employer becomes aware, or ought
reasonably to be aware, that domestic violence may occur and would likely expose
a worker to physical injury, it must take every precaution reasonable in the
circumstances — a duty that reaches into the workplace from outside it and is
frequently unaddressed.

It must connect to the Human Rights Code without duplicating it. Harassment on a
protected ground engages both statutes at once, and the investigation that
satisfies the OHSA is the same investigation — what differs is the remedy and
the liability, which is the human rights policy's ground.

**Where an organisation has also adopted the Ontario construction health and
safety programme, it already has this artifact** as `cohs.violence-harassment`,
written for a constructor with multiple projects. The two are deliberately at
different paths and must not both be in force: adopt this one for a single
workplace, that one for a construction operation, and remove the other from the
plan. The generic occupational health and safety programme carries neither,
which is why this duty sits here for every other kind of employer.
