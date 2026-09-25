---
id: cohs.first-aid-stations
kind: procedure
title: First Aid Stations and Coverage
structure: procedure
path: procedures/first-aid-station.md

satisfies:
  - reg_1101_first_aid:1
  - reg_1101_first_aid:5
  - reg_1101_first_aid:6
  - cor_2020:COR-14

requires: [cohs.site-emergency-response]

declares:
  obligation:
    id: cohs.first-aid-box-inspection
    activity: Inspection of the first aid boxes and of attendant coverage at the project
    cadence: each quarter
    authority: R.R.O. 1990 Reg. 1101 s. 6 — first aid boxes inspected at not less than quarter-yearly intervals, the card dated and signed
    interval_basis: required
    responsible: site-supervisor
    applies_to: the organisation
    per:
      listed_in: registers/projects.md
      key: project_id
      label: name
      from: start_on
      until: finished_on
    records: registers/first-aid-station-inspections.md
    escalate: {after: 2w, to: health-safety-lead}
  register:
    title: First Aid Station Inspection Record
    note: >
      One row per station per quarter. Coverage and contents are checked together
      because either alone is not first aid: a stocked box nobody is certified to
      open, and a certified attendant with an empty box, fail the same way. The
      inspection card at the station is the statutory record and is dated and
      signed there; this register is the organisation's view across its sites.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: station, label: Station, type: text, required: true}
      - {key: inspector, label: Inspected by, type: user, required: true}
      - {key: workers_per_shift, label: Workers on the largest shift, type: int, required: true}
      - {key: required_level, label: Level of certificate required, type: select, required: true,
         options: [Basic or Emergency First Aid, Intermediate or Standard First Aid,
                   Intermediate plus stretcher and blankets, First aid room with a nurse or attendant]}
      - {key: attendants_on_duty, label: Certificate holders on duty, type: int, required: true}
      - {key: certificates_posted, label: Valid certificates posted on the notice board, type: bool, required: true}
      - {key: form_posted, label: The prescribed first aid notice posted, type: bool, required: true}
      - {key: contents_complete, label: Contents complete, type: bool, required: true}
      - {key: expired_or_used, label: Items expired or used and not replaced, type: longtext}
      - {key: naloxone_required, label: Naloxone kit required at this workplace, type: bool, required: true}
      - {key: naloxone_expiry, label: Earliest naloxone expiry date, type: date}
      - {key: naloxone_names_posted, label: Names and locations of the trained workers posted near the kit, type: bool}
      - {key: card_signed, label: Inspection card dated and signed at the station, type: bool, required: true}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: who can give first aid on
each project, what they have to give it with, how far away help is, and how a
first aid treatment becomes a record.

It must size the stations from the regulation rather than from habit, by the
number of workers **per shift**: an emergency-level certificate holder for five or
fewer; a standard-level holder from six to fifteen; a standard-level holder plus a
stretcher and two blankets from sixteen to one hundred and ninety-nine; and a
first aid room with a nurse or a standard-level holder who does no other work
likely to impair their ability to respond, at two hundred or more.

**The construction-specific provisions are the ones organisations miss**, and they
are where the duty lands on the general contractor. A construction, repair or
demolition site is deemed a place of employment for these purposes. The station is
maintained in the time office, or in a vehicle or building on the site. And where
the work is in the charge of a general contractor, **the general contractor
provides and maintains the stations for the workers as if it were their
employer** — which means the sub-trades' workers are covered by the general
contractor's stations, not by their own. Heavy equipment operators need a kit on
the machine where a station is not readily available.

It must require the station to carry the **notice board** the regulation
prescribes: the prescribed first aid notice, the **valid certificates of the
trained workers on duty**, and the **inspection card**. The card is the statutory
inspection record and it is dated and signed at the station; the register in this
artifact is the organisation's view across its projects, not a replacement for it.

**The quarterly inspection interval is the law's.** The **three-year validity of a
first aid certificate is not in the regulation's text** — the regulation requires
a valid certificate, and the three-year period comes from the certifying
programme. That distinction belongs in the register of statutory credentials, and
it is a good example of a clock that is real, enforceable and not statutory.

It must state that the **accident record** required at each station is its own
record, and what it must contain: the circumstances as described by the worker,
the date and time, the witnesses, the nature and exact location of the injuries,
and the date, time and nature of each first aid treatment. **No retention period
is prescribed for it**, and a document asserting three years is asserting
something the regulation does not say. The organisation should set its own period,
long, and record that it chose it.

It must cover **naloxone** where the workplace requires it: the kit's contents are
prescribed, no refresher interval is set for the training, and the real trackable
clock is **the drug's own expiry date**. The **names and workplace locations of
the trained workers in charge of the kit must be posted conspicuously near it** —
a posting duty that is quietly not done almost everywhere.

**Defibrillators are not required by this regulation** and are not part of a first
aid station's prescribed contents. They are a separate construction duty with a
separate artifact, and merging them produces a programme that satisfies neither.

It must say how a first aid record reaches the incident process, including the
minor ones, and what is confidential. A first aid record contains health
information, and the person entitled to know an attendant was called is not
necessarily entitled to know what for.
