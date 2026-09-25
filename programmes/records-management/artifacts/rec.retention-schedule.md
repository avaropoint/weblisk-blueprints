---
id: rec.retention-schedule
kind: register
title: Records Retention Schedule
structure: standard
path: registers/retention-schedule.md

satisfies:
  - iso_27001:A.5.33
  - iso_9001:7.5
  - pipeda:PIPEDA-5
  - fippa_mfippa:FM-07
  - employment_standards_ontario:15
  - soc2:C1.2

requires: [rec.policy]

register:
  title: Records Retention Schedule
  note: >
    One row per class of record — a kind of record with a common keeping period,
    not an individual document. "Employee time and wage records" is a class;
    "Ahmed's timesheet for March" is a record in it.

    `authority` is what separates a schedule from a habit. A period with a
    citation is a requirement somebody can defend; a period without one is a
    number somebody chose, and both look identical in a table until the column
    exists.

    `trigger_event` is here because most statutory periods do not run from
    creation. Three years after the work was performed, seven years after the
    end of the tax year, twenty-four months after the breach was determined, and
    the length of employment plus a period afterwards are all common, and a
    schedule that measures everything from a file date will dispose of things
    early.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: record_class, label: Record class, type: text, required: true}
    - {key: description, label: What it covers, type: longtext, required: true}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: system, label: Where it is held, type: text, required: true}
    - {key: personal_information, label: Contains personal information, type: bool, required: true}
    - {key: trigger_event, label: Retention runs from, type: text, required: true}
    - {key: keep_for, label: Keep for, type: text, required: true}
    - {key: authority, label: Authority, type: text, required: true}
    - {key: disposition, label: Disposition, type: select, required: true,
       options: [Destroy securely, Transfer to archive, Retain permanently, Return to the client, Review again]}
    - {key: method, label: Method of destruction, type: select, required: true,
       options: [Secure shredding, Certified destruction service, Secure electronic deletion,
                 Cryptographic erasure, Physical destruction of media, Not applicable]}
    - {key: legal_hold, label: Under legal hold, type: bool, required: true}
    - {key: next_disposition_on, label: Next disposition due, type: date, required: true}
    - {key: review_due, label: Schedule entry reviewed by, type: date, required: true}
---

What this artifact must establish: for every kind of record the organisation
holds, how long it is kept, on whose authority, and what happens to it then.

This is the register the product enforces, and it is the one artifact in this
programme that cannot be prose. The disposition obligation is triggered from
these rows, the privacy programme's retention decisions point at them, and the
information asset inventory's `retention_class` column joins to them — so a
schedule written as a document rather than a register leaves three other
programmes with nothing to reference.

**Ontario has no general private-sector records retention statute**, which is why
`authority` is free text and will hold a dozen different sources: the Employment
Standards Act for employment records, the Income Tax Act and Excise Tax Act for
books of account, the Occupational Health and Safety Act and its regulations for
exposure and training records, the Workplace Safety and Insurance Act for claim
records, PIPEDA for personal information no longer needed for its purpose, the
Limitations Act for the period a claim can still be brought, and the
organisation's own contracts — which frequently require longer than any of them.
A programme that sets one organisation-wide period has picked a number that is
too short for some classes and too long for the rest.

`next_disposition_on` is what makes the schedule operate rather than describe.
It is the date the disposition obligation is raised from, and it moves forward
each time a disposal is carried out — which is why a class with no date raises no
work and a schedule full of them reports as a programme with nothing to do.

`legal_hold` on the row is the safety catch. Automated disposition without it is
how an organisation destroys the documents it needed for the case it is in, and
the column is checked before every disposal rather than remembered.
