---
id: it.change-requests
kind: register
title: Change Register
structure: standard
path: registers/change-requests.md

requires: [it.change-management]

register:
  title: Change Register
  note: >
    One row per change to a production system, service or configuration, opened
    when it is proposed rather than when it is done. An emergency change is
    still a row — recorded afterwards, marked as emergency, and reviewed like
    any other. A register that holds only planned changes describes an
    organisation that has never had an outage at 4 p.m. on a Friday.

    `implemented_on` is what the post-implementation review is triggered from, so
    a change that was made and never dated cannot be reviewed.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: raised_on, label: Raised on, type: date, required: true}
    - {key: raised_by, label: Raised by, type: user, required: true}
    - {key: system, label: System or service, type: text, required: true}
    - {key: description, label: What is changing, type: longtext, required: true}
    - {key: reason, label: Why, type: longtext, required: true}
    - {key: type, label: Type, type: select, required: true,
       options: [Standard, Normal, Emergency]}
    - {key: risk, label: Risk if it goes wrong, type: select, required: true,
       options: [Low, Medium, High]}
    - {key: security_impact, label: Security or privacy impact assessed, type: bool, required: true}
    - {key: backout, label: How it is backed out, type: longtext, required: true}
    - {key: approved_by, label: Approved by, type: user}
    - {key: implemented_on, label: Implemented on, type: date}
    - {key: outcome, label: Outcome, type: select,
       options: [Not yet implemented, Successful, Partially successful, Backed out, Failed]}
---

What this artifact must establish: every change that could have caused the
outage, in one place, with dates.

It exists so that the first question after an incident — what changed? — has an
answer that is not somebody's memory. That is its primary value, and it is worth
more than the approval workflow most change registers are built around.

`backout` is required on every row because the plan for undoing a change is
written before it is needed or it is not written at all. A change with "restore
from backup" as its backout plan has just made the restore test in this
programme load-bearing.

`security_impact` is a required boolean rather than a free-text field so that
the unanswered case is visible. A change that opened a firewall port and was
never assessed reads identically to one that changed a report layout, unless
somebody was made to tick a box.
