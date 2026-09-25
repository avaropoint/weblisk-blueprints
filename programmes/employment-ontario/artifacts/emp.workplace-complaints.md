---
id: emp.workplace-complaints
kind: register
title: Workplace Complaint Register
structure: standard
path: registers/workplace-complaints.md

requires: [emp.complaint-investigation]

register:
  title: Workplace Complaint Register
  note: >
    One row per complaint of workplace harassment, violence or discrimination,
    opened on the day it is received. A complaint does not have to be in writing
    or use any particular word to start the employer's duty to investigate, and
    the row is what stops a verbal report to a supervisor disappearing.

    Access to this register is restricted. It names people in the most sensitive
    situation the workplace produces, and a register visible to everybody is one
    nobody will file a complaint into.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: received_on, label: Received on, type: date, required: true}
    - {key: received_by, label: Received by, type: user, required: true}
    - {key: route, label: How it was raised, type: select, required: true,
       options: [To a supervisor, To HR, To senior management, Through the committee,
                 Anonymously, Observed by the employer, Other]}
    - {key: type, label: Type, type: select, required: true,
       options: [Harassment, Sexual harassment, Violence or threat, Discrimination,
                 Reprisal, More than one, Unclear]}
    - {key: grounds, label: Protected ground engaged, type: text}
    - {key: parties_known, label: Respondent identified, type: bool, required: true}
    - {key: interim_measures, label: Interim measures put in place, type: longtext, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [Received, Under investigation, Concluded, Withdrawn, Referred externally]}
---

What this artifact must establish: every complaint, with the date it arrived on
it, and what was done in the meantime.

It is a register of its own because an investigation has to be able to be late,
and lateness here has consequences beyond the process: an employee who complained
and heard nothing for two months is an employee the organisation has failed twice,
and a constructive dismissal claim frequently starts there.

`interim_measures` is required on every row. The period between a complaint and
a conclusion is when the risk is highest, and doing nothing because the facts are
not yet established is itself a decision — one that leaves a complainant working
beside the person they complained about.

`route: Anonymously` exists because anonymous complaints arrive and the duty to
investigate does not depend on the complainant's cooperation. What changes is
what can be investigated, and that has to be recorded rather than used as a
reason to close the row.

`type: Unclear` is a real first answer. A complaint about a manager's conduct may
be harassment, discrimination, a performance dispute or all three, and
classifying it prematurely narrows the investigation before it begins.
