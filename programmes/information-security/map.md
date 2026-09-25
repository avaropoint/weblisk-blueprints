---
id: information-security
title: Information Security Management System
order: 30
domains: [governance, risk_management, access_control, data_protection, incident_response,
          business_continuity, vendor_management, asset_management, hr_security,
          logging_monitoring, physical_security, compliance_audit]
conforms_to: [iso_27001, nist_csf_2, can_ciosc_104, iso_22301, soc2]

tiers:
  - id: essential
    title: What every organisation needs
    rationale: >
      The controls whose absence is not a maturity gap but an exposure: nobody
      owns security, nothing says what the organisation holds, anybody can reach
      anything, and a breach is discovered by the customer. Below this line an
      organisation is not unaccredited, it is uninsurable — and the questions on
      a cyber insurance proposal form are drawn almost exactly from this tier.
  - id: conformant
    title: Audit-ready
    requires: essential
    rationale: >
      The programme can be shown to work to somebody who was not in the room.
      Suppliers are assessed rather than trusted, logs are read rather than
      collected, people are trained and their access is taken away when they
      leave, and there is a plan for the day the systems are not there. This is
      the tier a client's security questionnaire asks about.
  - id: certifiable
    title: Externally auditable
    requires: conformant
    rationale: >
      The management system audits itself, states which of the 93 Annex A
      controls apply and why, and reports its own performance to the people who
      can fund it. This is what a certification body asks for first, and what
      nobody can reconstruct after the fact.

artifacts:
  # ── essential ──────────────────────────────────────────────────────────────
  - {id: isec.policy, tier: essential}
  - {id: isec.roles, tier: essential}
  - {id: isec.asset-inventory, tier: essential}
  - {id: isec.asset-management, tier: essential}
  - {id: isec.classification, tier: essential}
  - {id: isec.access-control, tier: essential}
  - {id: isec.risk-assessment, tier: essential}
  - {id: isec.risk-register, tier: essential}
  - {id: isec.risk-treatment, tier: essential}
  - {id: isec.security-incidents, tier: essential}
  - {id: isec.incident-response, tier: essential}
  - {id: isec.security-awareness, tier: essential}
  # From the IT operations programme. Placed rather than restated: one artifact
  # serves several programmes, and a second acceptable use policy written here
  # would be the second one an organisation has to keep in step with the first.
  - {id: it.acceptable-use, tier: essential}
  - {id: it.backup-recovery, tier: essential}
  - {id: it.asset-register, tier: essential}
  # ── conformant ─────────────────────────────────────────────────────────────
  - {id: isec.personnel-security, tier: conformant}
  - {id: isec.supplier-register, tier: conformant}
  - {id: isec.supplier-security, tier: conformant}
  - {id: isec.cryptography, tier: conformant}
  - {id: isec.logging-monitoring, tier: conformant}
  - {id: isec.physical-security, tier: conformant}
  - {id: isec.business-continuity, tier: conformant}
  - {id: isec.compliance-obligations, tier: conformant}
  - {id: isec.incident-review, tier: conformant}
  - {id: it.vulnerability-management, tier: conformant}
  - {id: it.change-management, tier: conformant}
  - {id: it.endpoint-security, tier: conformant}
  - {id: it.remote-access, tier: conformant}
  - {id: it.access-provisioning, tier: conformant}
  # ── certifiable ────────────────────────────────────────────────────────────
  - {id: isec.statement-of-applicability, tier: certifiable}
  - {id: isec.internal-audit, tier: certifiable}
  - {id: isec.security-reporting, tier: certifiable}
  - {id: it.configuration-standards, tier: certifiable}
  - {id: rec.policy, tier: certifiable}
  - {id: rec.retention-schedule, tier: certifiable}
---

An information security management system aligned to ISO/IEC 27001:2022, using
the 2022 Annex A control set — four themes and 93 controls, not the 2013
annex's fourteen clauses and 114.

It is the corporate counterpart to the occupational health and safety programme:
the same management-system shape — policy, risks, controls, competence,
incidents, audit, review — applied to information rather than to people's
physical safety. An organisation that already runs one of them is adopting a
second body of controls, not a second way of working.

**Five frameworks, because they overlap rather than because five are needed.**
ISO/IEC 27001:2022 is the spine. NIST CSF 2.0 says the same things in outcome
language and is what a North American client is more likely to ask about.
CAN/CIOSC 104 is the Canadian baseline behind CyberSecure Canada certification
and is sized for an organisation under 500 people — it is the most useful map
for a small business, and almost every artifact at the essential tier answers
one of its thirty-odd controls. ISO 22301 supplies the continuity discipline
that ISO 27001's A.5.29 and A.5.30 point at without containing. SOC 2 is cited
where an artifact genuinely answers a trust services criterion, because a
client's questionnaire will ask.

**Twenty-four artifacts are authored here and eleven are placed from the IT and
records programmes.** Acceptable use, the IT asset register, backups, patching,
change management, endpoints, remote access, account provisioning and
configuration baselines are IT operations work that answers security controls;
the records policy and retention schedule are the records programme's. They are
placed here rather than written again, which is what makes adopting a second
overlapping framework mostly a matter of adding citations to documents that
already exist. The three programmes are designed to be adopted together and to
work individually.

**Three obligations are record-origin rather than scheduled**, and they are the
ones that make the programme operate rather than report. A security incident has
no period — asking which month it belongs to has no answer — so its
investigation is triggered by the row and due five days after the report. A risk
is reviewed before its own review date, not on a calendar the whole register
shares. A supplier is reassessed before its review date, for the same reason.
Each of those chains terminates in a cadence, because a trigger whose recording
register is its own trigger register discharges every occurrence the moment it
creates one and reports a hundred per cent having checked nothing.

**What is deliberately not here.** Secure development and application security —
A.8.25 to A.8.33 — are not in this programme, because an organisation that does
not build software would carry ten permanently-unanswerable gaps, and one that
does needs a development programme rather than five artifacts bolted onto this
one. The Annex A controls for them are excluded in the Statement of
Applicability with a reason, which is exactly what that document is for.
