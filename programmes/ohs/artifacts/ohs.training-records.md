---
id: ohs.training-records
kind: register
title: Register of Training and Certification Held
structure: standard
path: registers/training-records.md

satisfies:
  - iso_45001:7.2
  - isnetworld:ISN-SAFE-04

requires: [ohs.competency-matrix]

register:
  title: Register of Training and Certification Held
  note: >
    One row per credential held by one person. `expires_on` is the reason this
    register exists separately from the competency matrix: the matrix says what
    a position must hold, and a review says somebody judged a person competent,
    but neither of those is a dated card that stops being true on a particular
    day whether or not anybody looked.
  columns:
    - {key: reference, label: Certificate or card number, type: text, required: true}
    - {key: person, label: Person, type: user, required: true}
    - {key: credential, label: Training or certification, type: text, required: true}
    - {key: issuer, label: Issued by, type: text, required: true}
    - {key: issued_on, label: Issued on, type: date, required: true}
    - {key: expires_on, label: Expires on, type: date}
    - {key: evidence, label: Evidence seen, type: attachment}
    - {key: required_for, label: Work it permits, type: text}
---

What this artifact must establish: which dated credentials each person actually
holds, who issued each one, and when it stops being valid.

It is separate from the competency matrix on purpose. The matrix is a statement
about POSITIONS — what a role must hold before it may do the work. A competency
review is a statement about a PERSON at a moment. Neither of those expires. A
card does, on a date somebody else chose, and an organisation that keeps all
three in one table ends up unable to answer the only question that is ever asked
in an audit or after an incident: was this person permitted to do this work on
this day.

Every row must carry the issuer's own reference. It is what the issuer will ask
for when the credential is verified or replaced, and it is what makes one row
about one card rather than about a person in general — a person may hold several
credentials, and several of the same credential over the years.

`expires_on` is not required, because some credentials do not expire and
recording a false date is worse than recording none. A row without one is
understood to be current until it is removed, and no renewal work is raised for
it.

It must hold the evidence, not a claim about it. A training record that says a
card was seen, without the card, is the assertion an auditor will not accept and
the one a subcontractor is most likely to have stretched.

It is a register rather than prose so that renewal can be driven from it: one
piece of work per credential, due before its own expiry date, rather than a
periodic invitation to read a table and notice something.
