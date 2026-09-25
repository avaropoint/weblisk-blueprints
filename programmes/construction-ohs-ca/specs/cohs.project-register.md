---
id: cohs.project-register
kind: register
title: Register of Construction Projects
structure: standard
path: registers/projects.md

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

requires: [cohs.policy]

register:
  title: Register of Construction Projects
  note: >
    One row per project this organisation is a constructor or an employer on.
    This is the spine of the programme: almost every start-up duty in Ontario
    construction is triggered by a project beginning rather than by a date in a
    calendar, and several obligations here raise one occurrence per row of this
    register. It is also where the thresholds live — a project expected to last
    three months or more with twenty or more workers regularly employed carries
    duties that a six-week job of eight people does not — so the numbers are
    columns rather than something somebody remembers.
  columns:
    - {key: project_id, label: Project number, type: text, required: true}
    - {key: name, label: Project name, type: text, required: true}
    - {key: address, label: Address, type: text, required: true}
    - {key: our_role, label: Our role, type: select, required: true,
       options: [Constructor, Employer, Constructor and employer, Owner only]}
    - {key: constructor_name, label: Constructor, type: text, required: true}
    - {key: start_on, label: Work expected to start, type: date, required: true}
    - {key: expected_end, label: Work expected to finish, type: date, required: true}
    - {key: expected_months, label: Expected duration in months, type: int, required: true}
    - {key: peak_workers, label: Workers regularly employed at peak, type: int, required: true}
    - {key: labour_and_materials, label: Cost of labour and materials, type: currency}
    - {key: notice_of_project_required, label: Notice of project required, type: select, required: true,
       options: ["Yes", "No", Not yet determined]}
    - {key: form_1000_held, label: Registration forms held for every employer, type: bool, required: true}
    - {key: jhsc_required, label: Committee required, type: bool, required: true}
    - {key: certified_members_required, label: Certified members required, type: bool, required: true}
    - {key: defibrillator_required, label: Defibrillator required, type: bool, required: true}
    - {key: finished_on, label: Project finished on, type: date}
---

What this artifact must establish: every project this organisation is on, what
role it holds there, and the four or five numbers that decide which duties
apply.

It exists because the duties are triggered by projects, not by months. A notice
of project, a registration form for every employer, the owner's designated
substance list, a posted constructor notice, a committee, a defibrillator — all
of them are owed at or before a start date that is different for every job, and
a programme that can only ask "has this been done this quarter" cannot tell
which of eleven live projects is the one missing its notice.

The thresholds are columns because they are arithmetic, not judgement, and
because they are the ones most often got wrong:

- A **joint health and safety committee** is required where twenty or more
  workers are regularly employed — and s. 9 does not apply at all to a project
  expected to last less than three months. Below a committee, and above five
  workers regularly employed, a health and safety representative is required.
- **Certified members** are a separate and higher threshold: not required for a
  project with fewer than fifty workers regularly employed, or one lasting under
  three months. Committee at twenty, certification at fifty. Conflating the two
  is the most common error in this area and it fails in both directions —
  organisations that certify unnecessarily, and organisations that reach fifty
  workers and do not.
- A **defibrillator** is the constructor's duty where twenty or more workers are
  regularly employed, and does not apply where the work is expected to last less
  than three months. Same two numbers as the committee, different duty holder,
  and it is new law as of 1 January 2026.
- A **notice of project** has its own list of triggers, most of which are not
  about headcount at all. `notice_of_project_required` is a select with a third
  option because "not yet determined" is a real and temporary state, and a
  boolean would force a guess to be recorded as a decision.

`finished_on` is not decoration. At least one statutory retention period in this
programme runs from the project being finished rather than from the record being
created, and a register with no closing date cannot start that clock.

`our_role` includes "Owner only" because an owner who is not the constructor
still owes the designated substance list, and an organisation that develops as
well as builds will hold both kinds of row.
