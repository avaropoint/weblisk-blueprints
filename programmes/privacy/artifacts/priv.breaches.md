---
id: priv.breaches
kind: register
title: Privacy Breach Record
structure: standard
path: registers/privacy-breaches.md

satisfies:
  - pipeda:PIPEDA-BR-2
  - quebec_law25:BS-2

register:
  title: Privacy Breach Record
  note: >
    One row per breach of security safeguards involving personal information —
    every one, not only the ones that had to be reported. PIPEDA requires a
    record of every breach to be kept for 24 months and to be produced to the
    Commissioner on request, and an organisation that records only the reportable
    ones has no way to show the others were assessed.

    A breach is a loss, unauthorised access, or unauthorised disclosure. An
    email sent to the wrong recipient is a breach; so is a laptop left on a
    train, whether or not anybody ever opened it.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: discovered_on, label: Discovered on, type: date, required: true}
    - {key: occurred_on, label: Occurred on, type: date}
    - {key: discovered_by, label: Discovered by, type: user, required: true}
    - {key: security_incident, label: Related security incident, type: text}
    - {key: kind, label: Kind, type: select, required: true,
       options: [Misdirected communication, Lost or stolen device, Unauthorised access,
                 Unauthorised disclosure, System compromise, Improper disposal,
                 Supplier breach, Other]}
    - {key: information_involved, label: Information involved, type: longtext, required: true}
    - {key: individuals_affected, label: Individuals affected, type: int, required: true}
    - {key: sensitivity, label: Sensitivity of the information, type: select, required: true,
       options: [Ordinary, Sensitive, Health information, Financial, Government identifier]}
    - {key: contained_on, label: Contained on, type: date}
    - {key: status, label: Status, type: select, required: true,
       options: [Open, Assessed, Notified, Closed]}
  retention:
    keep: 24m
    from: created
    authority: PIPEDA s. 10.3 and the Breach of Security Safeguards Regulations — a record of every breach kept for 24 months after the day the organisation determines the breach occurred
    reason: >
      The Commissioner may request the records of every breach, including the
      ones assessed as not posing a real risk of significant harm. Twenty-four
      months is the floor, not the ceiling: a breach that led to a claim, a
      complaint or a regulatory file is kept under the legal hold register until
      that matter ends.
---

What this artifact must establish: every privacy breach, including the ones that
did not have to be reported.

The record-keeping duty is separate from the reporting duty and is the one
organisations miss. PIPEDA requires a record of every breach of security
safeguards involving personal information under the organisation's control,
kept for twenty-four months from the day the organisation determined the breach
occurred, and the Commissioner may ask for all of them — including the ones
assessed as not posing a real risk of significant harm. An organisation that can
produce only its reported breaches has either had none or kept no record, and
the Commissioner cannot tell which.

`discovered_on` starts the clock, and it is a different date from `occurred_on`.
A breach that happened in March and was discovered in July is reported now: the
obligation is to report as soon as feasible after the organisation determines
the breach occurred.

`security_incident` links to the security incident register where one exists,
because most privacy breaches are security incidents with a second set of
statutory duties attached. The two registers are separate because the duties are:
one is investigated under the incident procedure, and the other is assessed for
harm and notification under this programme's, on a clock the incident procedure
does not know about.
