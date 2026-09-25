---
id: privacy
title: Privacy Programme
order: 40
domains: [data_protection, governance, records_management, incident_response,
          vendor_management, compliance_audit]
conforms_to: [pipeda, casl, quebec_law25, iso_27001, soc2]

tiers:
  - id: essential
    title: Required by law
    rationale: >
      What an organisation that collects personal information in the course of
      commercial activity must be able to do: say who is accountable, say what
      it holds and why, answer a person who asks, and respond when the
      information goes somewhere it should not. Below this line the organisation
      is not immature, it is in breach — and the first three of these are what
      an investigator asks for before anything else.
  - id: conformant
    title: Demonstrably accountable
    requires: essential
    rationale: >
      Accountability that can be shown rather than asserted: changes are
      assessed before they happen, service providers are bound in writing, the
      people who handle personal information have been trained, and the breach
      record is reviewed rather than accumulated.
  - id: certifiable
    title: Assurable to a client or an auditor
    requires: conformant
    rationale: >
      The programme produces evidence somebody else can test — retention is
      scheduled and disposals are recorded, commercial messaging can prove its
      consent, and the whole is reviewed annually with numbers rather than
      assurances.

artifacts:
  # ── essential ──────────────────────────────────────────────────────────────
  - {id: priv.policy, tier: essential}
  - {id: priv.inventory, tier: essential}
  - {id: priv.notice, tier: essential}
  - {id: priv.collection-and-consent, tier: essential}
  - {id: priv.requests, tier: essential}
  - {id: priv.request-response, tier: essential}
  - {id: priv.breaches, tier: essential}
  - {id: priv.breach-response, tier: essential}
  # ── conformant ─────────────────────────────────────────────────────────────
  - {id: priv.impact-assessment, tier: conformant}
  - {id: priv.assessments, tier: conformant}
  - {id: priv.service-providers, tier: conformant}
  - {id: priv.training, tier: conformant}
  - {id: priv.breach-review, tier: conformant}
  # Safeguards are a privacy obligation and a security one. Rather than writing
  # a second set, the programme places the security artifacts that answer
  # PIPEDA principle 7, together with the two they depend on — an organisation
  # adopting only this programme still gets them, and one adopting both gets
  # them once.
  - {id: isec.policy, tier: conformant}
  - {id: isec.classification, tier: conformant}
  - {id: isec.access-control, tier: conformant}
  - {id: isec.security-incidents, tier: conformant}
  - {id: isec.incident-response, tier: conformant}
  # ── certifiable ────────────────────────────────────────────────────────────
  - {id: priv.casl, tier: certifiable}
  - {id: rec.policy, tier: certifiable}
  - {id: rec.retention-schedule, tier: certifiable}
  - {id: rec.disposition, tier: certifiable}
---

Privacy for an organisation whose privacy law is federal, because Ontario's is.

**The jurisdiction question is the whole programme, and getting it wrong is the
most expensive mistake available here.** PIPEDA applies to personal information
an organisation collects, uses or discloses in the course of commercial activity
— which covers essentially every Ontario business — and Ontario has **no
private-sector privacy statute of general application**. There is no Ontario
equivalent of Alberta's or British Columbia's PIPA, and an organisation told
otherwise will go looking for a law that does not exist. PIPEDA also does not
cover employee information for a provincially regulated Ontario employer at all:
it reaches employee information only for federal works, undertakings and
businesses, which leaves employee privacy in Ontario governed by contract, the
common law tort of intrusion upon seclusion, the Employment Standards Act's
electronic monitoring policy requirement, and — for a union — the collective
agreement. That is an unusual position and the policy has to say so rather than
imply a statute.

**Three regimes bind by role rather than by geography, and each is scoped
somewhere else.** PHIPA binds health information custodians and their agents —
the `privacy-health-on` programme. FIPPA and MFIPPA bind Ontario institutions
and reach their suppliers through contract — the `privacy-public-sector-on`
programme. Quebec's Law 25 binds an organisation that carries on an enterprise
in Quebec, and it is cited in this map because an Ontario company with Quebec
customers is bound by it for those customers: the artifacts here answer it where
the duty is common, and the places where Law 25 goes further — mandatory privacy
impact assessments, automated decision disclosure, portability, de-indexing —
are called out in the artifacts rather than assumed.

**CASL is here because it binds and is usually nobody's job.** Every commercial
electronic message an Ontario company sends is in scope, the burden of proving
consent is on the sender, and the penalties reach ten million dollars. It sits
at the certifiable tier not because it is optional but because an organisation
that cannot yet answer an access request should fix that first.

**Three obligations are record-origin.** A privacy request is answered within
thirty days of the day it arrived — a statutory deadline, recorded with
`interval_basis: required`, and the only obligation in this corpus where the
clock is set by an Act rather than chosen. A breach is assessed within three days
of discovery. A collection of personal information is reviewed before its own
review date. Each chain ends in a cadence, because a trigger whose recording
register is its own trigger register discharges every occurrence the moment it
creates one.

**The privacy impact assessment deliberately has no obligation.** It is
triggered by a change, and a change has no period; attaching a cadence would
raise occurrences for work nobody asked for and report as complete in a quarter
where nothing changed. What makes a missing assessment visible is the annual
review, which counts new or changed processing against assessments completed —
and that column is the honest version of a control nothing can schedule.
