---
id: cohs.violence-harassment
kind: procedure
title: Workplace Violence and Workplace Harassment
structure: procedure
path: procedures/violence-and-harassment.md

satisfies:
  - ohsa_ontario:32.0.1
  - ohsa_ontario:32.0.2
  - ohsa_ontario:32.0.3
  - ohsa_ontario:32.0.6
  - ohsa_ontario:32.0.7
  - ohsa_ontario:32.0.8
  - cor_2020:COR-09
  - iso_45001:6.1.2
  - iso_45001:6.1.3

requires: [cohs.policy]

declares:
  obligation:
    id: cohs.violence-harassment-review
    activity: Review of the workplace violence policy, the workplace harassment policy and the harassment programme
    cadence: each year
    authority: OHSA ss. 32.0.1(1)(c) and 32.0.7(1)(c) — both policies and the harassment programme reviewed at least annually
    interval_basis: required
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/violence-and-harassment-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Violence and Harassment Review Record
    note: >
      One row per review. The violence risk assessment is a separate column from
      the policy review because it is a separate duty on a different trigger:
      the policies are reviewed annually, and the assessment is reassessed "as
      often as is necessary" — which is an event-driven duty with no clock, and
      the event is usually a new site or a change in who works there.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: consulted, label: Committee or representative consulted on the harassment programme, type: bool, required: true}
      - {key: violence_policy_reviewed, label: Violence policy reviewed, type: bool, required: true}
      - {key: harassment_policy_reviewed, label: Harassment policy reviewed, type: bool, required: true}
      - {key: harassment_programme_reviewed, label: Harassment programme reviewed, type: bool, required: true}
      - {key: risk_assessment_current, label: Violence risk assessment current for every site, type: bool, required: true}
      - {key: risk_assessment_last_done, label: Risk assessment last carried out, type: date}
      - {key: incidents_in_period, label: Incidents and complaints in the period, type: int, required: true}
      - {key: investigations_completed, label: Investigations completed, type: int, required: true}
      - {key: results_given_in_writing, label: Results given in writing to both parties in every case, type: bool, required: true}
      - {key: changes_made, label: Changes made, type: longtext}
      - {key: posting_method, label: How the policies are made available, type: select, required: true,
         options: [Posted at each project, Electronic, Both]}
---

What this document must establish for THIS organisation: the two policies, the
two programmes, the risk assessment, and what actually happens when somebody
reports something.

It must treat **violence and harassment as separate regimes**, because the Act
does. Violence requires a policy, a programme, a **risk assessment** reassessed as
often as necessary, provisions for domestic violence that may occur in the
workplace, and — where a worker can be expected to encounter a person with a
history of violent behaviour — **disclosure of that history** so far as is
reasonably necessary to protect them. Harassment requires a policy and a **written
programme developed in consultation with the committee or representative**, an
investigation appropriate in the circumstances, and **results provided in writing
to the complainant and to the alleged harasser**.

**The annual reviews are the law's**, all three of them: the violence policy, the
harassment policy and the harassment programme.

**The risk assessment has no clock.** It must be reassessed as often as is
necessary — which is an event-driven duty, and on a construction project the
events are ordinary: a new site with a different public interface, night work,
lone work, a change in the composition of the crew. A programme that assesses once
at head office and never again has satisfied a requirement it has misread as
periodic.

It must reflect that harassment now expressly includes conduct carried out
**virtually, through information and communications technology**. Group chats,
project messaging and social media are within scope, and a policy that describes
harassment as something that happens on a site is describing half of it.

It must correct a framing error that is common enough to be worth naming in the
document itself: the Ontario **violence and harassment provisions are in the
Occupational Health and Safety Act, not in the Human Rights Code**. The two
regimes coexist — the Code is ground-based, individually enforced at the Tribunal,
and carries a duty to accommodate that has no analogue in the Act; the Act's
provisions are **ground-neutral** and enforced by an inspector. Conduct based on a
protected ground breaches both, and an organisation whose only harassment process
is a human rights complaints procedure has no answer to an inspector at all.

It must say what happens when the person complained about is the person who would
normally investigate, and must provide a route that does not run through them.
An inspector may order an **impartial third-party investigation at the employer's
expense**, and that order is usually the consequence of an organisation having no
such route.

It must state that the policies are posted at a conspicuous place **or made
available in a readily accessible electronic format** — the electronic option is
recent and much of the circulating guidance predates it — and must note the narrow
exemption where five or fewer workers are regularly employed.

It must connect to the **work refusal** right, because workplace violence is an
express ground for refusal on a construction project and the ordinary refusal
procedure applies to it.
