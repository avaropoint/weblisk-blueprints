---
id: priv.request-response
kind: procedure
title: Responding to a Privacy Request
structure: procedure
path: procedures/responding-to-a-privacy-request.md

satisfies:
  - pipeda:PIPEDA-9
  - pipeda:PIPEDA-6
  - quebec_law25:IR-1
  - quebec_law25:IR-2
  - quebec_law25:IR-3
  - fippa_mfippa:FM-03
  - soc2:P5.1
  - soc2:P6.1

requires: [priv.requests, priv.inventory]
template: privacy-request-response

declares:
  obligation:
    id: priv.request-response
    activity: Respond to a privacy request within the statutory period
    for:
      records: registers/privacy-requests.md
      due: 30d after received_on
      key: reference
    authority: PIPEDA s. 8(3) — response no later than thirty days after receipt
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/privacy-request-responses.md
    escalate: {after: 7d, to: senior-management}
    satisfies:
      - pipeda:PIPEDA-9
  register:
    title: Privacy Request Response Record
    note: >
      One row per response, keyed by the request's reference. `withheld_reason`
      is required whenever anything was withheld: an organisation that refuses
      part of an access request must tell the individual why, in writing, and
      tell them they may complain to the Commissioner — and a record that says
      only "partial" cannot show that it did.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: reference, label: Request, type: relation, required: true,
         target: /registers/privacy-requests.md#records, display: reference}
      - {key: responded_on, label: Responded on, type: date, required: true}
      - {key: responded_by, label: Responded by, type: user, required: true}
      - {key: within_deadline, label: Within the statutory deadline, type: bool, required: true}
      - {key: systems_searched, label: Systems and records searched, type: longtext, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Granted in full, Granted in part, Refused, Corrected, Consent withdrawn and actioned, No records held]}
      - {key: withheld_reason, label: What was withheld and why, type: longtext}
      - {key: third_party_information, label: Third-party information involved, type: bool, required: true}
      - {key: fee_charged, label: Fee charged, type: currency}
      - {key: complaint_rights_given, label: Told of the right to complain to the Commissioner, type: bool, required: true}
---

What this document must establish for THIS organisation: how a request is
answered completely, on time, and without disclosing somebody else's
information.

It must say how identity is verified, and be proportionate. Demanding
government identification for a routine access request is itself an excessive
collection of personal information, and refusing to answer until it is supplied
does not stop the clock.

It must name the places that have to be searched. This is where the personal
information inventory earns its existence: an organisation searching from memory
answers with what the privacy officer thought of, which is why "we hold nothing
about you" is so often wrong. Backups, email, ticketing systems, call
recordings, the CRM's deleted-records table and a supplier's system that holds
the data on the organisation's behalf are all in scope.

It must state the thirty-day deadline as a deadline and say when an extension is
available, what the individual must be told about it, and by when — a response
that arrives on day forty-five with no notice given by day thirty is a deemed
refusal under PIPEDA, not merely a late answer.

It must say what is withheld and on what basis: solicitor-client privilege,
information that would reveal another individual, confidential commercial
information, and the narrow other exceptions. Everything not withheld must be
provided, and where information about another person cannot be severed, the rest
of the record must still be released.

It must cover correction, withdrawal of consent and deletion as distinct
outcomes with distinct consequences. Withdrawal of consent may mean the service
cannot continue, and the individual has to be told that before rather than after.

It must be able to say where else the corrected or withdrawn information went. A
correction that is not passed to the third parties who received the original
leaves the error in circulation, which the accuracy principle requires be fixed.
