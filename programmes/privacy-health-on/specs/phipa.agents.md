---
id: phipa.agents
kind: procedure
title: Agents and Electronic Service Providers
structure: procedure
path: procedures/health-information-agents.md

satisfies:
  - phipa_ontario:17
  - phipa_ontario:10(4)
  - phipa_ontario:12

requires: [phipa.information-practices]

declares:
  obligation:
    id: phipa.agent-confirmation
    activity: Confirm that every agent and electronic service provider is bound, informed and still needed
    cadence: each year
    authority: PHIPA s. 17 — the custodian is responsible for personal health information in the custody of its agents
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/health-agent-confirmations.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Agent and Service Provider Confirmation Record
    note: >
      One row per confirmation period. Agents and electronic service providers
      are counted separately because the duties are different: an agent acts on
      the custodian's behalf and may only do what the custodian permits, and an
      electronic service provider is bound by section 10(4) not to use or
      disclose the information at all except as necessary to provide the service.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: confirmed_on, label: Confirmed on, type: date, required: true}
      - {key: confirmed_by, label: Confirmed by, type: user, required: true}
      - {key: agents, label: Agents acting on our behalf, type: int, required: true}
      - {key: agents_informed, label: Of those, confirmed as informed of their duties, type: int, required: true}
      - {key: service_providers, label: Electronic service providers, type: int, required: true}
      - {key: providers_with_agreements, label: Of those, with a written agreement, type: int, required: true}
      - {key: network_providers, label: Health information network providers, type: int, required: true}
      - {key: access_reviewed, label: Their access reviewed and reduced where possible, type: bool, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: who acts on the
custodian's behalf, what they are permitted to do, and how they are told.

It must distinguish an agent from an electronic service provider, because PHIPA
does and the duties differ. An agent — an employee, a contractor, a student, a
volunteer, a locum — may collect, use, disclose, retain or dispose of personal
health information only on the custodian's behalf, only for a purpose the
custodian permits, only where the custodian would itself be permitted, and only
as necessary for their duties. An electronic service provider supplies the means
rather than acting on the custodian's behalf, and section 10(4) forbids it from
using the information except as necessary to provide the service and from
disclosing it at all.

It must state the notification duty in the direction people forget: an agent
must notify the custodian at the first reasonable opportunity of an unauthorised
use, disclosure, theft or loss. The custodian's own reporting clock starts from
that notification, and an agent who does not know to make it is how a breach is
discovered months late.

It must cover the health information network provider case if one is used — a
supplier serving more than one custodian carries additional duties under O. Reg.
329/04, including a plain-language description of its services, notice of
unauthorised access, a threat risk assessment made available, and a written
agreement. The custodian has to know whether its supplier is one.

It must require access to be given at the level of the duty, not at the level of
the system. The commonest PHIPA finding is not an outsider getting in; it is an
insider with more access than their role needs, looking at a record they had no
reason to open.
