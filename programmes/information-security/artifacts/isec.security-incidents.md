---
id: isec.security-incidents
kind: register
title: Security Incident Register
structure: standard
path: registers/security-incidents.md

requires: [isec.incident-response]

register:
  title: Security Incident Register
  note: >
    One row per security event that was assessed as an incident, opened when it
    is reported rather than when it is understood. A suspected incident is an
    incident until somebody decides otherwise, and that decision is a column
    here rather than a reason not to open the row.

    `reference` is the identity the whole chain joins on: the investigation
    cites it, a privacy breach assessment cites it where personal information
    was involved, and a risk that was realised cites it. It must be issued on
    report and never reused.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: detected_on, label: Detected on, type: date, required: true}
    - {key: reported_on, label: Reported on, type: date, required: true}
    - {key: reported_by, label: Reported by, type: user, required: true}
    - {key: category, label: Category, type: select, required: true,
       options: [Phishing, Malware, Account compromise, Unauthorised access, Data loss or exposure,
                 Denial of service, Physical, Lost or stolen device, Supplier incident, Other]}
    - {key: severity, label: Severity, type: select, required: true,
       options: [Low, Medium, High, Critical]}
    - {key: assets_affected, label: Assets or systems affected, type: longtext, required: true}
    - {key: personal_information, label: Personal information involved, type: bool, required: true}
    - {key: description, label: What happened, type: longtext, required: true}
    - {key: containment, label: Immediate containment taken, type: longtext, required: true}
    - {key: closed_on, label: Closed on, type: date}
---

What this artifact must establish: every security event that mattered, recorded
when it was reported rather than when somebody had time to write it up.

It is a register of its own, and not columns on the response procedure, because
an investigation has to be able to be late. A field is filled in or it is not;
it has no due date and nobody owns it, so an investigation that never happened
looks exactly like one where somebody left the box empty. These rows are what
the investigation obligation is triggered from, which is what lets the platform
say that INC-014 is eleven days overdue.

`personal_information` is a column on every row because the answer decides
whether a second clock has started. A privacy breach is a security incident with
statutory notification duties attached, and an organisation that discovers the
personal information involvement three weeks later has missed them.

A near miss belongs here. A phishing message nobody clicked, a device recovered
before it was opened, an access granted in error and withdrawn within the hour —
a register that holds only the incidents that succeeded records the ones the
organisation failed to prevent and loses every cheap warning it was given.
