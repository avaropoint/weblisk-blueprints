---
id: it-operations
title: IT Operations and Acceptable Use
order: 35
domains: [configuration_management, change_management, asset_management, access_control,
          business_continuity, vulnerability_management, network_security, governance]
conforms_to: [iso_27001, can_ciosc_104, cis_controls, nist_csf_2, soc2]

tiers:
  - id: essential
    title: What keeps the lights on and the doors shut
    rationale: >
      The five things an organisation of any size has to be able to say: people
      know what they may do with the technology, somebody knows what the
      organisation owns, the machines are configured safely, changes are
      recorded, and the data can be brought back. An organisation missing the
      last of those is one bad morning from not existing, and every cyber
      insurance proposal form asks about it.
  - id: conformant
    title: Managed rather than maintained
    requires: essential
    rationale: >
      The difference between an IT function that fixes what breaks and one that
      can say what state the estate is in: accounts reconciled against real
      people, vulnerabilities on a clock, remote access reviewed, and software
      approved rather than merely present.
  - id: certifiable
    title: Demonstrable to somebody else
    requires: conformant
    rationale: >
      Configuration is written down as a baseline and compared with what is
      deployed, and the network's exposure is reviewed against what was
      intended. This is the tier where an auditor or a client's assessor can
      check the claims rather than accept them.

artifacts:
  # ── essential ──────────────────────────────────────────────────────────────
  - {id: it.acceptable-use, tier: essential}
  - {id: it.asset-register, tier: essential}
  - {id: it.endpoint-security, tier: essential}
  - {id: it.backup-recovery, tier: essential}
  - {id: it.change-requests, tier: essential}
  - {id: it.change-management, tier: essential}
  # Three artifacts from the security programme, placed rather than rewritten.
  # An IT function provisioning accounts against no stated rule provisions them
  # against whatever was asked for, and an access control policy with no
  # classification behind it cannot say what "least privilege" means here.
  - {id: isec.policy, tier: essential}
  - {id: isec.classification, tier: essential}
  - {id: isec.access-control, tier: essential}
  # ── conformant ─────────────────────────────────────────────────────────────
  - {id: it.access-provisioning, tier: conformant}
  - {id: it.vulnerability-management, tier: conformant}
  - {id: it.remote-access, tier: conformant}
  - {id: it.software-approval, tier: conformant}
  # ── certifiable ────────────────────────────────────────────────────────────
  - {id: it.network-security, tier: certifiable}
  - {id: it.configuration-standards, tier: certifiable}
---

The operational half of information security, separated from it on purpose.

The security programme states what must be true and who decides; this one is the
work that makes it true — patching, backups, accounts, changes, devices,
networks. They are split because they are done by different people on different
rhythms: a security lead sets the access control policy once a year and an IT
manager reconciles accounts every month, and a single programme containing both
gives one of them a document they never open.

**Every artifact here answers a security control, and several are placed in the
information security programme as well.** That is the intended shape: an
artifact is standalone and a programme is a curated selection, so acceptable
use, backups, patching and change management appear in both maps without being
written twice. An organisation adopting only this programme still gets an
acceptable use policy and a restore test; one adopting both gets them once.

**CIS Controls v8.1 and CAN/CIOSC 104 do most of the work here.** ISO/IEC 27001
says a control shall exist; CIS says what to configure and CAN/CIOSC 104 — the
Canadian baseline behind CyberSecure Canada — says which of them matter first
for an organisation under 500 people. Where a framework in this build's
catalogue has no control for something, nothing is cited: an absent citation is
recoverable, and an invented one reads as a compliance claim nobody can defend.

**One obligation is record-origin.** A change is implemented once, on a date,
and its review is due five days after that date — not in the month it happens to
fall in. Everything else here is genuinely periodic: a reconciliation, a patch
review, a restore test and an endpoint check are sweeps of a whole estate, and
they have a period because the estate does.

**The restore test is the artifact to keep if only one survives.** Backups that
have never been restored are the most widely held false assurance in this
catalogue, and the register above is deliberately built so that a restore which
completed but was never checked by somebody who knows the data cannot be
recorded as a success.
