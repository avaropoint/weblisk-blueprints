---
id: privacy-health-on
title: Health Information Privacy (PHIPA, Ontario)
order: 42
domains: [data_protection, governance, access_control, logging_monitoring,
          incident_response, records_management]
conforms_to: [phipa_ontario, pipeda, iso_27001]

tiers:
  - id: essential
    title: Required of a custodian
    rationale: >
      What the Act requires of anybody who is a health information custodian:
      information practices that comply and are followed, a named contact
      person, a public statement, and notification when health information goes
      where it should not. There is no threshold and no small-custodian
      exemption — a single-practitioner clinic owes all of it.
  - id: conformant
    title: Able to show it
    requires: essential
    rationale: >
      The duties that separate a custodian who has written the policy from one
      who can demonstrate compliance: agents bound and informed, access to
      records audited rather than merely logged, and the annual report to the
      Commissioner made from a record that supports it.

artifacts:
  # ── essential ──────────────────────────────────────────────────────────────
  - {id: phipa.information-practices, tier: essential}
  - {id: priv.breaches, tier: essential}
  - {id: phipa.breach, tier: essential}
  # Access and correction under PHIPA ss. 52 and 55 run on the same thirty-day
  # clock as a PIPEDA access request, and the privacy programme's request
  # register and response procedure answer both. Placed rather than rewritten.
  - {id: priv.inventory, tier: essential}
  - {id: priv.requests, tier: essential}
  - {id: priv.request-response, tier: essential}
  # ── conformant ─────────────────────────────────────────────────────────────
  - {id: phipa.agents, tier: conformant}
  - {id: phipa.access-audit, tier: conformant}
  - {id: phipa.annual-report, tier: conformant}
  - {id: isec.policy, tier: conformant}
  - {id: isec.classification, tier: conformant}
  - {id: isec.access-control, tier: conformant}
  - {id: rec.policy, tier: conformant}
  - {id: rec.retention-schedule, tier: conformant}
---

For health information custodians only, and the first job of this programme is
to make an organisation decide whether it is one.

**PHIPA binds by role, not by geography or by industry.** A health information
custodian is one of the persons listed in section 3 of the Act: a health care
practitioner, a hospital, a psychiatric facility, a long-term care home, a
pharmacy, a laboratory, a specimen collection centre, an ambulance service, a
community care access corporation, a medical officer of health and the others
named there. An employer that holds sick notes is not a custodian. An insurer is
not a custodian. A software company serving a clinic is not a custodian — but it
is almost certainly an electronic service provider, bound by section 10(4) and
by O. Reg. 329/04, and the agents artifact here is the one it needs.

**An organisation that is not a custodian should not adopt this programme.**
Adopting obligations nobody owes produces gaps that can never be closed and
teaches everybody to ignore the report. The general `privacy` programme answers
PIPEDA, which is what a commercial organisation holding health-related personal
information is bound by instead.

**Where PHIPA is stricter than PIPEDA, this programme says so.** Two places in
particular. The notice duty to the individual has **no harm threshold** — every
theft, loss or unauthorised use or disclosure is notified at the first
reasonable opportunity, where PIPEDA notifies only on a real risk of significant
harm. And there is an **annual statistical report** to the Information and
Privacy Commissioner by 1 March, counting every breach including the ones that
were never individually reportable, which is why the breach record has to hold
them all.

**The access audit is the artifact that distinguishes this programme.** The
Commissioner's health orders are dominated by insider snooping, and in nearly
every case the electronic audit log existed and nobody read it. A monthly audit
with targeted queries is the control; a system that can produce a log on request
is not.

Five artifacts are authored here and five are placed from the privacy, security
and records programmes. Access and correction run on the same thirty-day clock
as a PIPEDA request; safeguards under section 12 are the same safeguards; and
retention and secure disposal under section 13 is the retention schedule doing
its job. A custodian adopting this programme alone still gets all of them.
