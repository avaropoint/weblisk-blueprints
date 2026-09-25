---
id: ohs.legal-requirements
kind: register
title: Register of Applicable Legal and Other Requirements
structure: standard
path: registers/legal-and-other-requirements.md

satisfies:
  - iso_45001:6.1.3
  - iso_45001:9.1.2
  - cor_2020:COR-04

requires: [ohs.responsibilities]

register:
  title: Register of Applicable Legal and Other Requirements
  note: >
    One row per requirement that binds this organisation. `last_evaluated` and
    `compliant` are what separate this register from a reading list: a statute
    listed and never evaluated against is a citation, not a control, and the two
    look identical without a date beside them.
  columns:
    - {key: requirement, label: Requirement, type: text, required: true}
    - {key: source, label: Instrument, type: text, required: true}
    - {key: applies_because, label: Applies because, type: longtext, required: true}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: how_met, label: How it is met, type: longtext, required: true}
    - {key: last_evaluated, label: Last evaluated, type: date, required: true}
    - {key: compliant, label: Compliant at last evaluation, type: select, required: true,
       options: [Yes, No, Partially, Not yet evaluated]}
    - {key: next_due, label: Next evaluation due, type: date, required: true}

declares:
  obligation:
    id: ohs.legal-evaluation
    activity: Evaluation of compliance with applicable legal requirements
    cadence: each year
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/legal-and-other-requirements.md
---

What this artifact must establish: every legal and other requirement that binds
this organisation's health and safety, and whether it is currently being met.

It must say for each requirement WHY it applies — the jurisdiction, the industry,
the equipment, the headcount that brings it into scope. A register of everything
that might apply somewhere is unusable, and a register that lists a requirement
without its trigger cannot be maintained when the trigger changes.

"Other requirements" is not padding. A client's site rules, a prequalification
scheme's conditions, a collective agreement and an insurer's terms all bind the
programme, and an organisation held to a client standard it never wrote down
discovers it during an audit of that client's making.

It must carry the date of the last evaluation and the next one due, because the
standard asks for compliance to be EVALUATED rather than assumed. That is the
whole difference between this register and a bibliography, and it is why the
obligation above records into this same file: the evaluation and the register are
one artifact, not a document plus a log of reading it.

It is a register rather than prose, so it is a table with a schema the platform
can read: rows are records, and each row can be signed for on its own.
