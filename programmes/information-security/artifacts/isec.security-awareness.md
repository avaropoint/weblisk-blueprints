---
id: isec.security-awareness
kind: procedure
title: Security Awareness and Training
structure: procedure
path: procedures/security-awareness-training.md

satisfies:
  - iso_27001:A.6.3
  - can_ciosc_104:CIOSC-L1-06
  - cis_controls:14.1
  - cis_controls:14.2
  - cis_controls:14.3
  - soc2:CC1.4

requires: [isec.policy]

declares:
  obligation:
    id: isec.security-awareness
    activity: Deliver security awareness training and record who completed it
    cadence: each year
    authority: ISO/IEC 27001:2022 A.6.3 — awareness, education and training, and regular updates
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/security-awareness-training.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Security Awareness Training Record
    note: >
      One row per delivery cycle, not per person — the per-person record lives
      in the organisation's training records. What this answers is whether the
      cycle ran, what it covered, and how many people it did not reach.
      `not_completed` is the column that matters: a completion rate reported as
      a percentage of those who started is a number that is always high.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: delivered_on, label: Delivered on, type: date, required: true}
      - {key: audience, label: Audience, type: text, required: true}
      - {key: topics, label: Topics covered, type: longtext, required: true}
      - {key: people_in_scope, label: People in scope, type: int, required: true}
      - {key: completed, label: Completed, type: int, required: true}
      - {key: not_completed, label: Not completed, type: int, required: true}
      - {key: phishing_simulation, label: Phishing simulation run, type: bool, required: true}
      - {key: simulation_click_rate, label: Simulation click rate (%), type: percent}
      - {key: actions, label: Follow-up for those who did not complete, type: longtext, required: true}
---

What this document must establish for THIS organisation: what people are told
about security, when, and what happens when the training does not reach them.

It must cover the specific things that go wrong here rather than a generic
curriculum. If the organisation's real exposure is invoice fraud and
supplier-payment changes, the training is about that; a module on nation-state
threat actors delivered to an office of twelve is time everybody knows was
wasted, and it teaches them that security training is not serious.

It must reach contractors, temporary staff and anybody else with an account. The
control covers "personnel of the organisation and, where relevant, interested
parties", and the account that gets compromised is rarely the one on the
employee list.

It must be delivered at hire and on change, not only annually. A person who
joins in February and is first trained the following November has been operating
on guesswork for nine months.

It must say what happens when somebody does not complete it. An organisation
with no answer has an awareness programme with a completion rate and no
consequence, and the rate stops moving at whatever it reached in the first
fortnight.

Where phishing simulations are used, it must say what the results are for. A
simulation whose click rate is used to discipline people produces a workforce
that stops reporting, which costs more than the simulation measures.
