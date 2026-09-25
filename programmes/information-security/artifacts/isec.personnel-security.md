---
id: isec.personnel-security
kind: procedure
title: Personnel Security
structure: procedure
path: procedures/personnel-security.md

satisfies:
  - iso_27001:A.6.1
  - iso_27001:A.6.2
  - iso_27001:A.6.4
  - iso_27001:A.6.5
  - iso_27001:A.6.6
  - iso_27001:A.5.11
  - fippa_mfippa:FM-11
  - soc2:CC1.4

requires: [isec.policy, isec.access-control]

declares:
  obligation:
    id: isec.offboarding-verification
    activity: Verify that access was removed and assets returned for everyone who left in the period
    cadence: each quarter
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/offboarding-verifications.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Departure Verification Record
    note: >
      One row per verification period. This is a check on the leaver process,
      not the process itself: the accounts are meant to be closed on the day.
      `accounts_still_active` is therefore the whole point of the register, and
      a verification that has never found one has probably never looked.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: verified_on, label: Verified on, type: date, required: true}
      - {key: period, label: Period covered, type: text, required: true}
      - {key: departures, label: Departures in the period, type: int, required: true}
      - {key: accounts_still_active, label: Accounts still active, type: int, required: true}
      - {key: assets_outstanding, label: Assets not returned, type: int, required: true}
      - {key: confidentiality_reminded, label: Continuing obligations confirmed in writing, type: int, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: what is checked before
somebody is given access to information, what they agree to, and what survives
their leaving.

It must state what screening is done for which roles, and keep it proportionate
and lawful. Screening must be appropriate to the classification of information
the role reaches, and in Ontario it runs into the Human Rights Code — a record
of offences is a protected ground, and a blanket criminal record check for every
role is both a Code problem and a control nobody can justify under A.6.1.

It must say what the terms of employment carry: the security responsibilities
that continue after the relationship ends, the confidentiality undertaking, and
the ownership of what the person produces. A.6.5 and A.6.6 are about what
remains true after the last day, and they are enforceable only if they were
agreed before the first one.

It must connect a security failure to the disciplinary process that already
exists rather than inventing a second one. A.6.4 asks for a formalised process
that is communicated; an organisation that has an HR disciplinary procedure and
a separate security sanctions policy has two processes that will one day reach
different outcomes on the same facts.

It must say what happens on the day somebody leaves and who confirms each part:
accounts, devices, keys, tokens, building access, and the accounts nobody thinks
of — the shared mailbox they administered, the supplier portal registered in
their name, the domain registrar login. The quarterly verification above exists
because that list is always longer than the checklist.
