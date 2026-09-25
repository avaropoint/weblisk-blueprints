---
id: ohs.statistics
kind: register
title: Health and Safety Statistics
structure: standard
path: registers/health-and-safety-statistics.md

satisfies:
  - cor_2020:COR-18
  - isnetworld:ISN-SAFE-01

requires: [ohs.incident-reporting-procedure]

register:
  title: Health and Safety Statistics
  note: >
    One row per reporting period. Hours worked is required because every rate
    here is a ratio against it: counts alone make a growing organisation look
    like a deteriorating one, and a shrinking one look like it is improving.
  columns:
    - {key: period, label: Period, type: text, required: true}
    - {key: hours_worked, label: Hours worked, type: int, required: true}
    - {key: fatalities, label: Fatalities, type: int, required: true}
    - {key: lost_time_injuries, label: Lost-time injuries, type: int, required: true}
    - {key: medical_aid, label: Medical-aid injuries, type: int, required: true}
    - {key: first_aid, label: First-aid only, type: int, required: true}
    - {key: near_misses, label: Near misses reported, type: int, required: true}
    - {key: trir, label: TRIR, type: text}
    - {key: ltir, label: LTIR, type: text}
    - {key: emr, label: Experience modification rate, type: text}
    - {key: prepared_by, label: Prepared by, type: user, required: true}

declares:
  obligation:
    id: ohs.statistics-prepared
    activity: Preparation of health and safety statistics for the period
    cadence: each quarter
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/health-and-safety-statistics.md
---

What this artifact must establish: the organisation's health and safety
performance as numbers, for the period, on a basis that can be compared with the
last one.

It must record HOURS WORKED alongside every count. Rates are what prequalification
schemes and clients ask for, they are what make one period comparable with
another, and they cannot be recomputed later from counts alone.

It must count near misses. An organisation reporting zero near misses is not
safe; it has a reporting culture problem, and the number is worth having precisely
because a rise in it is usually good news.

It must say what each rate MEANS here — the formula, the multiplier, the
population — because TRIR and LTIR are defined differently in different
jurisdictions and schemes, and a rate quoted without its basis cannot be audited
or compared.

It must be honest about revision. Injuries are reclassified as facts arrive: a
medical-aid case becomes lost-time weeks later. A period restated must show that
it was, and the version history of this file is that record.

It is a register rather than prose, so it is a table with a schema the platform
can read: rows are records, and each row can be signed for on its own.
