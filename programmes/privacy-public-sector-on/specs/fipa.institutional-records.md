---
id: fipa.institutional-records
kind: procedure
title: Records in Institutional Custody or Control
structure: procedure
path: procedures/institutional-records.md

satisfies:
  - fippa_mfippa:FM-01
  - fippa_mfippa:FM-03
  - fippa_mfippa:FM-04
  - fippa_mfippa:FM-05

declares:
  obligation:
    id: fipa.records-confirmation
    activity: Confirm which records held are in an institution's custody or control
    cadence: each year
    interval_basis: chosen
    responsible: records-manager
    applies_to: the organisation
    records: registers/institutional-records-confirmations.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Institutional Records Confirmation Record
    note: >
      One row per confirmation. `records_unclear` is the column that earns the
      register: whether a record is in an institution's control is a legal test
      rather than a filing decision, and the rows nobody can classify are the
      ones that will be argued about when an access request arrives.
    layout: form
    review: required
    approvers: [records-manager]
    columns:
      - {key: confirmed_on, label: Confirmed on, type: date, required: true}
      - {key: confirmed_by, label: Confirmed by, type: user, required: true}
      - {key: institutions, label: Institutions we hold records for, type: int, required: true}
      - {key: record_classes, label: Classes of record held, type: longtext, required: true}
      - {key: records_unclear, label: Classes whose custody or control is unclear, type: int, required: true}
      - {key: systems, label: Systems they are held in, type: longtext, required: true}
      - {key: personal_information, label: Classes containing personal information, type: int, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: which of the records it
holds belong, in law, to a public institution.

It must apply the custody-or-control test rather than asking who has the file.
A record created by a contractor in the course of delivering a service to an
institution can be in that institution's control even though the institution has
never seen it — the questions are whether the institution has a right to possess
it, whether it relates to the institution's mandate and functions, and what the
contract says. A supplier that assumes its own records are its own will discover
otherwise during an access request with a statutory deadline running.

It must say what happens when an institution receives an access request that
reaches into the organisation's systems: who is told, how quickly, what is
searched, and what is produced. The institution's clock is thirty days and it
starts when the institution receives the request, not when it reaches the
contractor.

It must state the collection rule as it applies through the institution.
Collection of personal information by an institution must be authorised by
statute, used for law enforcement, or necessary to a lawfully authorised
activity, and a contractor collecting on the institution's behalf collects under
the institution's authority rather than its own. A supplier that decides to
collect an extra field because it is useful has exceeded an authority it never
held.

It must be explicit that this programme is for organisations bound through an
institution. FIPPA binds provincial institutions and MFIPPA binds municipal ones
— municipalities, school boards, police services boards, health units, transit
and library boards — and neither binds a private company directly. What binds
the company is its contract, which is why the flow-down artifact sits beside
this one.
