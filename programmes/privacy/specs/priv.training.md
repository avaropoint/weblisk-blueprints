---
id: priv.training
kind: procedure
title: Privacy Training
structure: procedure
path: procedures/privacy-training.md

satisfies:
  - pipeda:PIPEDA-1
  - quebec_law25:GA-2
  - fippa_mfippa:FM-11
  - iso_27001:A.6.3

requires: [priv.policy]

declares:
  obligation:
    id: priv.training
    activity: Deliver privacy training and record who completed it
    cadence: each year
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/privacy-training.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Privacy Training Record
    note: >
      One row per delivery cycle. Roles that handle personal information daily —
      reception, sales, HR, support — are counted separately from everybody else,
      because a single organisation-wide completion rate hides whether the people
      who actually receive the requests and make the mistakes were reached.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: delivered_on, label: Delivered on, type: date, required: true}
      - {key: audience, label: Audience, type: text, required: true}
      - {key: topics, label: Topics covered, type: longtext, required: true}
      - {key: people_in_scope, label: People in scope, type: int, required: true}
      - {key: completed, label: Completed, type: int, required: true}
      - {key: high_contact_roles, label: People in roles handling personal information daily, type: int, required: true}
      - {key: high_contact_completed, label: Of those, completed, type: int, required: true}
      - {key: actions, label: Follow-up, type: longtext, required: true}
---

What this document must establish for THIS organisation: what people are told
about handling personal information, and who has to be told it.

It must teach recognition before procedure. The most valuable thing anybody in
the organisation can learn is what an access request looks like when it is not
labelled as one, and what a breach looks like on the day it happens — a
misdirected email is a breach, and most people do not know that, which is why
most breaches are reported late or not at all.

It must be specific to the role. Reception and support staff handle requests and
identity verification; HR holds the most sensitive records in most
organisations; developers and IT decide where data goes. A single module for
everybody teaches nobody what to do on Tuesday.

It must say what to do rather than what the law says. "Forward it to the privacy
officer the same day and do not delete the original" is training; a summary of
the ten principles is a compliance artefact.

It must reach contractors and temporary staff who handle personal information.
The accountability principle covers information under the organisation's control
regardless of who is touching it.
