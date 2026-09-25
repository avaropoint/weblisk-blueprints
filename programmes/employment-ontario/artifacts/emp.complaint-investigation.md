---
id: emp.complaint-investigation
kind: procedure
title: Workplace Complaint Investigation
structure: procedure
path: procedures/workplace-complaint-investigation.md

satisfies:
  - ohsa_ontario:32.0.7
  - ohsa_ontario:32.0.8
  - ohrc_ontario:5(2)
  - ohrc_ontario:8
  - ohrc_ontario:46.3

requires: [emp.violence-harassment]

declares:
  obligation:
    id: emp.complaint-investigation
    # Record-origin. A complaint arrives on a date and the investigation runs
    # from it. There is no period a complaint belongs to, and an employer whose
    # investigations are "reviewed quarterly" has no way to say that this one is
    # six weeks late.
    activity: Investigate a workplace complaint and inform both parties of the results
    for:
      records: registers/workplace-complaints.md
      due: 30d after received_on
      key: reference
    authority: OHSA s. 32.0.7 — an investigation appropriate in the circumstances, and written results to both parties
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/workplace-complaint-investigations.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - ohsa_ontario:32.0.7
  register:
    title: Workplace Complaint Investigation Record
    note: >
      One row per investigation, keyed by the complaint reference.
      `results_to_complainant` and `results_to_respondent` are separate required
      columns because the Act requires both to be informed in writing, and an
      organisation that told one is in breach with respect to the other.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reference, label: Complaint, type: relation, required: true,
         target: /registers/workplace-complaints.md#records, display: reference}
      - {key: investigator, label: Investigator, type: user, required: true}
      - {key: investigator_independent, label: Investigator independent of both parties, type: bool, required: true}
      - {key: external, label: External investigator used, type: bool, required: true}
      - {key: started_on, label: Started on, type: date, required: true}
      - {key: concluded_on, label: Concluded on, type: date, required: true}
      - {key: complainant_interviewed, label: Complainant interviewed, type: bool, required: true}
      - {key: respondent_interviewed, label: Respondent interviewed and given the allegations, type: bool, required: true}
      - {key: witnesses, label: Witnesses interviewed, type: int, required: true}
      - {key: finding, label: Finding, type: select, required: true,
         options: [Substantiated, Partly substantiated, Not substantiated, Unable to determine, Withdrawn]}
      - {key: results_to_complainant, label: Results given to the complainant in writing on, type: date}
      - {key: results_to_respondent, label: Results given to the respondent in writing on, type: date}
      - {key: corrective_action, label: Corrective action taken, type: longtext, required: true}
      - {key: systemic, label: Systemic issue identified, type: bool, required: true}
---

What this document must establish for THIS organisation: how a complaint is
investigated fairly, by somebody who can be fair, and what both people are told
at the end.

It must name who investigates and rule out the people who cannot. A supervisor
investigating a complaint about their own conduct, or about somebody they manage,
is being asked to find their own supervision at fault. Where the complaint is
about the employer or a senior manager, the OHSA requires the programme to say
how the worker reports it and, in practice, that means an external investigator
and saying so in advance rather than deciding under pressure.

It must give the respondent the allegations. An investigation that concludes
without putting the substance to the person accused is procedurally unfair, and
the finding will not survive being challenged — which helps nobody, least of all
the complainant.

It must set a target period and say what happens when it cannot be met. Thirty
days is a working standard rather than a statutory one: the Act requires an
investigation appropriate in the circumstances, and appropriate for a
two-witness incident is not appropriate for a pattern over three years. What is
not acceptable is silence, so the procedure must require both parties to be told
of a delay and of the new expected date.

It must require the results to be given to both parties in writing, along with
any corrective action that will be taken. This is an express OHSA duty, it is
routinely missed, and it is the one most likely to be raised by an inspector.

It must protect against reprisal explicitly and say how that is monitored after
the file is closed. Reprisal is a separate breach under both the Code and the
OHSA, and the period after an investigation is when it happens.

It must say what is kept, for how long, and who may see it. An investigation
file contains the most sensitive personal information the employer holds, its
retention belongs in the records schedule, and an organisation that destroys it
early loses its own evidence — while one that keeps it in a shared drive has
created a different problem entirely.
