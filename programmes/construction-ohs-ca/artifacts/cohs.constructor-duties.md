---
id: cohs.constructor-duties
kind: procedure
title: Constructor, Employer and Supervisor Duties
structure: procedure
path: procedures/duty-holders.md

satisfies:
  - cor_2020:COR-03
  - cor_2020:COR-04
  - iso_45001:5.3

requires: [cohs.policy, cohs.project-register]

approved_by: [senior-management]

declares:
  obligation:
    id: cohs.project-start-up
    activity: Project start-up duties completed before work begins
    for:
      records: registers/projects.md
      due: 14d before start_on
      key: project_id
    authority: OHSA s. 23(1); O. Reg. 213/91 ss. 5, 13, 14
    interval_basis: chosen
    responsible: constructor-representative
    applies_to: each project
    records: registers/project-start-ups.md
    escalate: {after: 1w, to: senior-management}
  register:
    title: Project Start-Up Record
    note: >
      One row per project, keyed by its project number so it joins to the
      register of projects. Each column is a duty owed before work begins rather
      than a task somebody invented, which is why they are booleans with dates
      beside them: "the supervisor is appointed" is a fact with a day attached,
      and a free-text status field would let "in progress" stand in for either.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: project_id, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: completed_on, label: Completed on, type: date, required: true}
      - {key: completed_by, label: Completed by, type: user, required: true}
      - {key: registrations_collected, label: Registration form held for every employer, type: bool, required: true}
      - {key: employers_listed, label: Employers and trades listed, type: longtext, required: true}
      - {key: supervisor_appointed, label: Supervisor appointed, type: bool, required: true}
      - {key: supervisor, label: Supervisor, type: user}
      - {key: notice_posted_on, label: Constructor notice posted on, type: date}
      - {key: representative_names_posted_on, label: Committee or representative names posted on, type: date}
      - {key: outstanding, label: Anything outstanding, and why, type: longtext}
---

What this document must establish for THIS organisation: who owes what on a
construction project, and what has to be true before the first worker arrives.

It must set out the duty holders in the terms the Act uses, because they are not
interchangeable. The **constructor** must ensure that the prescribed measures are
carried out, that **every employer and every worker on the project complies**,
and that the health and safety of workers on the project is protected — a duty
about other people's employees that has no analogue in an ordinary workplace. The
**employer** carries the strict duties of s. 25(1), including the requirement
added in December 2024 that protective equipment be a proper fit and appropriate
in the circumstances, and the reasonableness-qualified duties of s. 25(2),
including the general duty to take every precaution reasonable in the
circumstances. The **supervisor** carries s. 27, including that same general
duty. The **worker** carries s. 28. **Directors and officers** must take all
reasonable care to ensure the corporation complies — a personal duty that
survives the corporation, and one this document should name rather than leave to
be discovered.

It must state which of these the organisation holds on which kind of project, and
say what changes when it is a sub-trade on somebody else's site rather than the
constructor on its own.

It must cover the start-up acts that are easy to miss because nothing rejects
them. Every constructor and every employer completes an approved **registration
form before beginning work**, and the constructor keeps each employer's copy **at
the project** — it is not filed with the Ministry, so nothing outside the
organisation will notice its absence until an inspector asks. The constructor
posts its own notice; the names of the committee members or the health and safety
representative, the trades and the employers, are added **within forty-eight
hours** of being selected. A constructor appoints a **supervisor** wherever five
or more workers work at the same time.

**The fourteen days is this organisation's choice and the law's is not.** The
statute says before work begins; fourteen days is a working margin chosen because
several of these acts depend on somebody else — an employer producing its
registration form, a committee selecting its members — and an organisation that
starts asking on the day work starts is asking too late to matter. Where a
project is mobilised faster than that, the duties do not move; only the margin
does.

It must say what happens when a sub-trade will not produce its registration or
will not name a supervisor. The constructor's duty is not discharged by having
asked, and the only effective answer is control of site access.

It must name the aggravating factors the penalty provisions now list, because one
of them is **motivation to increase revenue or decrease costs** — which is to say
that a schedule-driven decision to skip a control is not a mitigating
circumstance, it is an aggravating one. The maximum penalties are $500,000 and
twelve months' imprisonment for an individual, $2,000,000 for a corporation, and
$1,500,000 for a director or officer contravening s. 32. Widely-circulated
figures of $100,000 and $500,000 are superseded and should not appear in the
organisation's own training material.
