---
id: emp.accommodation
kind: procedure
title: Workplace Accommodation
structure: procedure
path: procedures/workplace-accommodation.md

satisfies:
  - ohrc_ontario:11
  - ohrc_ontario:17
  - aoda_ontario:28
  - aoda_ontario:26
  - aoda_ontario:27
  - aoda_ontario:29
  - aoda_ontario:30

requires: [emp.human-rights]
template: individual-accommodation-plan

declares:
  obligation:
    id: emp.accommodation-plan
    # Record-origin. An accommodation request arrives on a date and the duty to
    # respond runs from it; there is no month a request belongs to.
    activity: Agree and document an individual accommodation plan
    for:
      records: registers/accommodation-requests.md
      due: 10d after requested_on
      key: reference
    authority: Human Rights Code s. 17 and IASR s. 28 — the procedural duty to consider accommodation individually and without delay
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/accommodation-plans.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - ohrc_ontario:17
      - aoda_ontario:28
  register:
    title: Individual Accommodation Plan Record
    note: >
      One row per plan, keyed by the request it answers. `undue_hardship_basis`
      is required whenever an accommodation is declined, and it is the whole
      defence: the three factors are cost, outside sources of funding, and
      health and safety, and a refusal recorded without them is a refusal with
      no basis on the record.

      Emergency response information is a column because IASR s. 27 requires it
      to be part of the plan and it is the part most often absent.
    layout: form
    review: required
    approvers: [hr-lead, senior-management]
    approval_order: sequential
    columns:
      - {key: reference, label: Request, type: relation, required: true,
         target: /registers/accommodation-requests.md#records, display: reference}
      - {key: agreed_on, label: Agreed on, type: date, required: true}
      - {key: employee_participated, label: Employee took part in developing it, type: bool, required: true}
      - {key: representative_offered, label: Representative or bargaining agent offered, type: bool, required: true}
      - {key: assessment_used, label: Assessment relied on, type: select, required: true,
         options: [Employee's own account, Treating practitioner, Independent assessment at employer expense,
                   Occupational health, No assessment needed]}
      - {key: measures, label: Measures agreed, type: longtext, required: true}
      - {key: emergency_information, label: Individualised emergency response information included, type: select, required: true,
         options: [Included, Not needed, Consent to share refused, Outstanding]}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Accommodated, Accommodated in an alternative role, Partially accommodated, Declined — undue hardship, Withdrawn]}
      - {key: undue_hardship_basis, label: If declined, the undue hardship basis, type: longtext}
      - {key: reasons_given, label: Reasons given to the employee in writing, type: bool, required: true}
      - {key: review_due, label: Next review due, type: date}
---

What this document must establish for THIS organisation: how a request for
accommodation is handled, by whom, and how quickly.

It must treat the process as part of the duty. The Human Rights Code's
accommodation obligation is procedural as well as substantive: an employer that
reaches the right outcome after an unexplained delay, or without individual
assessment, has breached it. That is why the obligation above runs from the date
the request was made rather than from when a plan was ready.

It must require individual assessment. A blanket rule — that a particular role
can never be done part time, that a return requires full clearance, that a
particular device is not supported — is the opposite of accommodation, and the
Code's undue hardship test is applied to this person in this role, not to the
category.

It must state what information the employer may ask for and what it may not.
Functional limitations, restrictions and prognosis, yes; diagnosis, no. Where an
independent assessment is sought, IASR s. 28 requires it to be at the employer's
expense.

It must name the three undue hardship factors and nothing else, and require any
refusal to be given in writing with reasons. Cost, outside sources of funding,
health and safety. An organisation that declines on grounds of fairness to other
employees, customer preference or morale has given a reason the Tribunal does not
recognise.

It must produce a written plan for large employers, containing what IASR s. 28
requires — how the employee participated, how they were assessed individually,
how a representative could be involved, the steps taken to protect their
personal information, the review cycle, the format the plan is provided in, and
the reasons if it was denied.

It must include individualised workplace emergency response information where
the employee's disability makes it necessary and the employer is aware. That
duty applies to employers of every size, it needs the employee's consent before
the information goes to a designated helper, and it has to be reviewed when the
person moves location or when the plan or the general emergency procedures are
reviewed.

It must cover return to work as a case of accommodation rather than a separate
process, while saying plainly that it does not displace the return-to-work
process under the Workplace Safety and Insurance Act for a work-related injury —
that one is in the occupational health and safety programme and has its own
statutory obligations.
