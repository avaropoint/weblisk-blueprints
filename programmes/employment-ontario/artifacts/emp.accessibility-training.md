---
id: emp.accessibility-training
kind: procedure
title: Accessibility Training
structure: procedure
path: procedures/accessibility-training.md

satisfies:
  - aoda_ontario:7
  - aoda_ontario:80.49
  - aoda_ontario:25
  - ohrc_ontario:5(1)

requires: [emp.accessibility-policy]

declares:
  obligation:
    id: emp.accessibility-training
    activity: Deliver accessibility training and keep the record of dates and participants
    cadence: each year
    authority: IASR ss. 7 and 80.49 — training as soon as practicable, and on every change to the policies, with records of the dates and number of participants
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/accessibility-training.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Accessibility Training Record
    note: >
      One row per delivery. The regulation requires a record of the dates on
      which training was provided and the number of individuals trained, which
      is why those two columns are required and why the register is the evidence
      rather than a byproduct.

      Volunteers and third parties acting on the organisation's behalf are
      counted separately because they are in scope and are almost always left
      out.
    layout: form
    review: required
    approvers: [hr-lead]
    columns:
      - {key: delivered_on, label: Delivered on, type: date, required: true}
      - {key: audience, label: Audience, type: text, required: true}
      - {key: content, label: Content covered, type: longtext, required: true}
      - {key: employees_trained, label: Employees trained, type: int, required: true}
      - {key: volunteers_trained, label: Volunteers trained, type: int, required: true}
      - {key: third_parties_trained, label: Third parties acting on our behalf, type: int, required: true}
      - {key: policy_developers_trained, label: People who develop our policies, type: int, required: true}
      - {key: triggered_by_change, label: Delivered because the policies changed, type: bool, required: true}
      - {key: outstanding, label: People in scope not yet trained, type: int, required: true}
---

What this document must establish for THIS organisation: who has to be trained on
accessibility, on what, and when.

It must state the scope the regulation sets, which is wider than employees: every
person who deals with the public on the organisation's behalf, every person who
participates in developing its policies, and every other person who provides
goods, services or facilities for it — which reaches volunteers, contractors,
agency staff and a franchisee's employees.

It must cover both required subjects. Section 7 requires training on the
requirements of the accessibility standards and on the Human Rights Code as it
pertains to persons with disabilities. Section 80.49 requires customer service
training on how to interact with people with various types of disability, with
people who use assistive devices or are accompanied by a service animal or
support person, and on what to do when a person is having difficulty accessing
the organisation's goods or services.

It must be delivered as soon as practicable rather than at the next annual
cycle, and again whenever the policies change. A person hired in February and
first trained in November has dealt with the public untrained for nine months.

It must keep the record the regulation asks for: the dates and the number of
individuals trained. That is an unusually specific evidentiary requirement and
it is the thing an accessibility compliance report attests to.
