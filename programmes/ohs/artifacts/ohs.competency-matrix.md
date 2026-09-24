---
id: ohs.competency-matrix
kind: standard
title: Competency Matrix
structure: standard
path: standards/competency-matrix.md

satisfies:
  - iso_45001:7.2
  - cor_2020:COR-16
  - isnetworld:ISN-SAFE-04

requires: [ohs.policy]

declares:
  obligation:
    id: ohs.competency-review
    activity: Competency review
    cadence: each year
    responsible: training-coordinator
    applies_to: the organisation
    records: registers/competency-reviews.md
  register:
    title: Competency Review Record
    note: >
      One row per person reviewed. The expiry date is what makes competence
      measurable rather than asserted — without it the platform cannot tell a
      current ticket from one that lapsed two years ago.
    layout: form
    review: required
    approvers: [training-coordinator]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: person, label: Person, type: user, required: true}
      - {key: position, label: Position held, type: text, required: true}
      - {key: competency, label: Competency or ticket, type: text, required: true}
      - {key: evidence, label: Evidence seen, type: text, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Competent, Competent with supervision, Not yet competent]}
      - {key: expires_on, label: Expires on, type: date}
      - {key: reviewer, label: Reviewed by, type: user, required: true}
---

What this document must establish for THIS organisation: which competencies each
position must hold before it may do the work assigned to it, and how holding one
is demonstrated.

It is organised by POSITION, not by person. Every obligation in this programme
is assigned to a position, so the matrix is what joins the obligation to the
evidence that whoever holds that position can actually discharge it. A matrix
listing people goes out of date on the day somebody is hired.

For each competency it must record what evidence counts — a certificate, an
assessed demonstration, an in-house sign-off — who may assess it, and whether it
expires. An expiry with no renewal path produces a workforce that is quietly
non-current, which is the finding this artifact exists to prevent. It should be
explicit about which competencies are legally required and which the
organisation requires of itself; the distinction changes what happens when
somebody lacks one.

It is deliberately reusable: the same matrix serves quality and environmental
programmes, and it should be written so that adding a competency from another
programme does not mean writing a second matrix.
