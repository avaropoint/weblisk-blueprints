---
id: privacy-public-sector-on
title: Public Sector Records (FIPPA and MFIPPA, Ontario)
order: 44
domains: [records_management, data_protection, vendor_management, compliance_audit, governance]
conforms_to: [fippa_mfippa, iso_27001]

tiers:
  - id: essential
    title: Required to hold an institution's records
    rationale: >
      What an organisation must be able to say before it holds anything for an
      Ontario institution: which records are in the institution's custody or
      control, what the contract requires, and who is told within hours when
      something goes wrong. An organisation that cannot answer the first
      question cannot answer an access request, and the institution's
      thirty-day clock is already running when it asks.
  - id: conformant
    title: Able to satisfy an institution's audit
    requires: essential
    rationale: >
      Handling rules written down, flow-down to subcontractors verified, and
      retention and secure disposal scheduled rather than assumed. This is what
      a broader-public-sector procurement assessment asks for, and what a
      renewal turns on.

artifacts:
  # ── essential ──────────────────────────────────────────────────────────────
  - {id: fipa.institutional-records, tier: essential}
  - {id: fipa.flow-down, tier: essential}
  - {id: priv.breaches, tier: essential}
  - {id: fipa.breach-notice, tier: essential}
  # ── conformant ─────────────────────────────────────────────────────────────
  - {id: fipa.handling, tier: conformant}
  - {id: isec.policy, tier: conformant}
  - {id: isec.classification, tier: conformant}
  - {id: isec.access-control, tier: conformant}
  - {id: isec.supplier-register, tier: conformant}
  - {id: isec.supplier-security, tier: conformant}
  - {id: rec.policy, tier: conformant}
  - {id: rec.retention-schedule, tier: conformant}
  - {id: rec.disposition, tier: conformant}
---

For organisations that hold an Ontario institution's records — and, deliberately,
not for institutions themselves.

**FIPPA and MFIPPA bind institutions, not companies.** The *Freedom of
Information and Protection of Privacy Act* binds provincial institutions —
ministries, agencies, universities, hospitals — and the *Municipal Freedom of
Information and Protection of Privacy Act* binds municipal ones: municipalities,
school boards, police services boards, health units, transit commissions and
library boards. Neither binds a private-sector supplier directly. What binds a
supplier is the **contract**, and the duties in this programme are the ones
institutions flow down through it.

That distinction is why this is a separate programme rather than artifacts in
the general privacy one. An organisation with no public-sector clients owes none
of this; an organisation with one owes all of it, on terms the statute does not
set and the contract does. Adopting it speculatively produces obligations with
no counterparty.

**A broader-public-sector supplier is the intended reader.** The IT services
firm with a school board contract, the payroll provider serving a municipality,
the records storage company holding a hospital's files, the software vendor whose
platform holds a police service's data. For most of them the first genuine
finding is not a security gap: it is discovering that records they thought were
their own are in the institution's control, and are therefore subject to an
access request they have never prepared for.

**Retention is the institution's rule, not the supplier's.** Institutions set
retention by by-law or records schedule, and the supplier's own schedule does not
override it — which is why the records programme's retention schedule and
disposition procedure are placed here rather than restated, with the authority
column carrying the institution's instrument rather than the organisation's
preference.

**The notification clock is contractual and it is the shortest one in this
corpus.** The obligation here is due twenty-four hours after discovery because
that is what institutional contracts commonly require, and it is recorded with
`interval_basis: required` for the same reason: the period was given to the
organisation, not chosen by it.
