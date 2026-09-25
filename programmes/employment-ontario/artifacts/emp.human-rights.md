---
id: emp.human-rights
kind: policy
title: Human Rights and Non-Discrimination
structure: policy
path: policies/human-rights-and-non-discrimination.md

satisfies:
  - ohrc_ontario:5(1)
  - ohrc_ontario:5(2)
  - ohrc_ontario:7(2)
  - ohrc_ontario:8
  - ohrc_ontario:11
  - ohrc_ontario:1
  - ohrc_ontario:46.3

approved_by: [senior-management]

declares:
  obligation:
    id: emp.human-rights-review
    activity: Review the human rights policy, the complaints received and what they show
    cadence: each year
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/human-rights-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Human Rights Review Record
    note: >
      One row per review. Complaints are counted by ground rather than in total,
      because a pattern on one ground is the finding and a total is a number.
      Where the count is small enough that a ground identifies a person, the
      column is left at a total and the reason recorded — a register that
      exposes a complainant is its own Code problem.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: policy_current, label: Policy current and communicated, type: bool, required: true}
      - {key: training_delivered, label: Training delivered in the period, type: bool, required: true}
      - {key: complaints, label: Complaints received, type: int, required: true}
      - {key: grounds, label: Grounds raised, type: longtext, required: true}
      - {key: accommodations_active, label: Accommodations in place, type: int, required: true}
      - {key: accommodations_refused, label: Accommodation requests refused, type: int, required: true}
      - {key: systemic_issues, label: Systemic issues identified, type: longtext, required: true}
      - {key: changes_made, label: Changes made, type: longtext, required: true}
---

What this document must establish for THIS organisation: that every person has a
right to equal treatment here, on which grounds, and what to do when they do not
get it.

It must list the protected grounds as the Code lists them — race, ancestry,
place of origin, colour, ethnic origin, citizenship, creed, sex, sexual
orientation, gender identity, gender expression, age, record of offences,
marital status, family status and disability — because a policy that summarises
them as "discrimination is not tolerated" gives nobody a basis on which to
recognise or raise one.

It must state the organisation's own liability. Under section 46.3 an act of an
officer, official, employee or agent in the course of employment is the
organisation's act, with no need to show it was authorised. That is why this is
a governance document: a manager's decision is the organisation's decision, and
policy, training and a complaint process that is actually followed are the
practical defences available.

It must cover constructive discrimination. A neutral rule — a uniform
requirement, a scheduling practice, a physical test, an attendance standard —
that disadvantages a protected group is a breach unless it is reasonable and
bona fide and the group cannot be accommodated without undue hardship. This is
the provision most organisations do not know applies to them, and the one behind
most findings.

It must be explicit that the duty to accommodate has exactly three factors:
cost, outside sources of funding, and health and safety. Inconvenience,
disruption to other staff, customer preference and morale are not among them,
and a document that implies otherwise will be quoted back to the organisation.

It must distinguish Code harassment from the workplace harassment duties in the
Occupational Health and Safety Act, and point at the artifact that carries the
second. They overlap and they are not the same: the Code creates a right and a
liability on protected grounds, and the OHSA requires a policy, a programme and
an investigation for workplace harassment generally.

It must protect people who complain. Reprisal is a separate and independently
actionable breach, and a complainant who is reassigned, managed more closely or
left off a project after raising a concern has a claim that can succeed even
where the original complaint fails.
