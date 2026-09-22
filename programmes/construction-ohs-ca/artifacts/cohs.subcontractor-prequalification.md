---
id: cohs.subcontractor-prequalification
kind: procedure
title: Sub-Trade Prequalification and Management
structure: procedure
path: procedures/subcontractor-prequalification.md

satisfies:
  - cor_2020:COR-15
  - isnetworld:ISN-SAFE-12
  - iso_45001:8.1.4

requires: [cohs.clearance-certificates]

declares:
  obligation:
    id: cohs.subcontractor-requalification
    activity: Requalification of every sub-trade on the approved list
    cadence: each year
    authority: ISO 45001:2018 clause 8.1.4.2 requires contractors to be controlled; COR 2020 requires contractor management. Neither sets a requalification interval
    interval_basis: chosen
    responsible: procurement-lead
    applies_to: the organisation
    records: registers/subcontractor-requalifications.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Sub-Trade Requalification Record
    note: >
      One row per sub-trade per requalification. `performance_on_our_sites` sits
      beside the documentary checks on purpose: a contractor whose paperwork is
      immaculate and whose crews have been sent home twice is a contractor the
      documents cannot describe, and a requalification that only reads files will
      approve them every year.
    columns:
      - {key: contractor, label: Contractor, type: text, required: true}
      - {key: trades, label: Trades, type: text, required: true}
      - {key: qualified_on, label: Qualified on, type: date, required: true}
      - {key: qualified_by, label: Qualified by, type: user, required: true}
      - {key: clearance_valid, label: Valid clearance certificate held, type: bool, required: true}
      - {key: insurance_valid, label: Insurance certificates current, type: bool, required: true}
      - {key: written_programme, label: Written health and safety programme reviewed, type: bool, required: true}
      - {key: accreditation, label: Accredited management system held, type: select, required: true,
         options: [None, Certificate of recognition, ISO 45001, Other accredited system, Equivalency certificate]}
      - {key: accreditation_expires, label: Accreditation expires, type: date}
      - {key: statistics_reviewed, label: Injury statistics reviewed, type: longtext}
      - {key: performance_on_our_sites, label: Performance on our sites since the last review, type: longtext, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Approved, Approved with conditions, Suspended, Removed from the list]}
      - {key: conditions, label: Conditions, type: longtext}
---

What this document must establish for THIS organisation: how a sub-trade gets on
the list, what it has to produce, what happens on site, and how it comes off.

It must begin from the constructor's position, because that is what makes this
different from ordinary vendor management. The constructor must ensure that
**every employer and every worker on the project complies**. Prequalification is
not procurement hygiene here; it is the mechanism by which a duty about other
people's employees is discharged before they arrive.

It must set out what is collected before engagement: the clearance certificate and
the insurance, the written health and safety programme, the training records for
the people who will actually attend, the injury statistics, and any accredited
management system the contractor holds. It must say who reviews each of those and
against what — a programme received and filed unread is a contractor qualified on
the fact that they own a printer.

**On accredited systems, the document must be accurate and even-handed.** Ontario
has accredited several occupational health and safety management systems, and
since the start of 2026 a public-sector buyer that requires one as a condition of
eligibility, of a contract, or of bid evaluation **must treat all accredited
systems as equivalent** for construction work — with a substantial monetary
penalty, publishable, for failing to. An organisation that prequalifies its own
sub-trades is not bound by that rule; an organisation bidding into the public
sector benefits from it. Neither should be described as a ranking of one
certificate above another. No authority ranks them, the accreditation body's own
published comparison declines to, and a programme asserting that one exceeds the
other is asserting something no source supports.

It should note, without overstating it, that an equivalency route exists in
Ontario for holders of an accredited international certificate, that it depends on
the certificate bearing the insignia of a recognised accreditation body and on the
audit scope covering representative provincial operations, and that the
equivalency certificate is **renewed annually** — a shorter clock than the
certificate it derives from, and one that belongs in the register of statutory
credentials.

It must say what happens **on site**, because prequalification without site
control is a filing exercise. The sub-trade's supervisor, orientation, pre-task
assessments, training verification and incident reporting all run through this
organisation's programme while they are on its project, and the document must say
which of the organisation's processes they participate in rather than duplicate.

It must define the exits: conditions, suspension, removal. A list nobody has ever
been removed from is not a qualified list, and the register records the outcome as
a state so that "approved with conditions" cannot quietly become "approved".

**The annual requalification is this organisation's choice.** Nothing prescribes
one. A year is chosen because the documents it depends on — insurance, clearances,
accreditation — mostly move on annual cycles, and because performance on site
needs a period long enough to have a pattern in it.
