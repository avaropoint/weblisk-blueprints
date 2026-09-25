---
id: priv.service-providers
kind: procedure
title: Service Providers and Transfers
structure: procedure
path: procedures/service-provider-privacy.md

satisfies:
  - pipeda:PIPEDA-1
  - pipeda:PIPEDA-7
  - quebec_law25:BS-4
  - fippa_mfippa:FM-02
  - fippa_mfippa:FM-09
  - fippa_mfippa:FM-12
  - iso_27001:A.5.19
  - soc2:P6.1

requires: [priv.inventory, priv.policy]

declares:
  obligation:
    id: priv.service-provider-review
    activity: Review the service providers that handle personal information
    cadence: each year
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/service-provider-privacy-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Service Provider Privacy Review Record
    note: >
      One row per review period, listing what changed rather than one row per
      supplier — the per-supplier security assessment lives in the security
      programme's supplier review, and this is the privacy overlay on the same
      list. `without_terms` is the number that matters: a provider handling
      personal information under no written commitment is an accountability gap
      the organisation cannot close after the fact.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: providers_in_scope, label: Providers handling personal information, type: int, required: true}
      - {key: without_terms, label: Of those, with no written privacy terms, type: int, required: true}
      - {key: outside_canada, label: Storing or processing outside Canada, type: int, required: true}
      - {key: notice_discloses, label: Privacy notice discloses the transfers, type: bool, required: true}
      - {key: sub_processors_changed, label: Sub-processors added in the period, type: int, required: true}
      - {key: incidents_reported, label: Provider incidents reported in the period, type: int, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: what happens when
somebody else holds the organisation's personal information.

It must state the accountability position plainly: under PIPEDA the organisation
remains responsible for personal information transferred to a third party for
processing, and must use contractual or other means to provide a comparable
level of protection. Outsourcing the processing does not outsource the
accountability, and a supplier's certificate is evidence of care rather than a
transfer of the duty.

It must set out what the written terms have to contain: the purposes the
provider may use it for and no others, the safeguards required, where it may be
held, whether sub-processors are permitted and on what notice, breach
notification to the organisation and how quickly, cooperation with access
requests, and return or destruction at the end.

It must address transfers outside Canada explicitly. There is no general
prohibition on them under PIPEDA, but the organisation must be transparent about
them and must consider that the information becomes subject to the laws of that
country — including lawful access by its authorities. An organisation handling
an Ontario institution's records under FIPPA or MFIPPA may have contractual data
residency requirements that go further, and an organisation with Quebec
customers must conduct a privacy impact assessment before communicating personal
information outside Quebec, taking the receiving jurisdiction's legal framework
into account.

It must not duplicate the supplier security review. That review asks whether the
supplier protects the information; this one asks whether the organisation is
permitted to have given it to them and whether the notice says so.
