---
id: it.network-security
kind: procedure
title: Network Security
structure: procedure
path: procedures/network-security.md

satisfies:
  - iso_27001:A.8.20
  - iso_27001:A.8.21
  - iso_27001:A.8.22
  - iso_27001:A.8.23
  - can_ciosc_104:CIOSC-L1-09
  - can_ciosc_104:CIOSC-L1-11
  - can_ciosc_104:CIOSC-L1-21
  - can_ciosc_104:CIOSC-L2-06
  - cis_controls:12.1
  - cis_controls:13.1
  - nist_csf_2:PR.IR-01
  - soc2:CC6.6

requires: [it.asset-register]

declares:
  obligation:
    id: it.network-configuration-review
    activity: Review network and firewall configuration against what is intended
    cadence: each year
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/network-configuration-reviews.md
    escalate: {after: 4w, to: information-security-lead}
  register:
    title: Network Configuration Review Record
    note: >
      One row per review. `rules_with_no_owner` is the column that finds the
      real exposure: firewall rules accumulate, each one was added for a reason
      somebody had at the time, and the ones nobody can explain are the ones
      nobody dares remove.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: rules_reviewed, label: Rules reviewed, type: int, required: true}
      - {key: rules_removed, label: Rules removed, type: int, required: true}
      - {key: rules_with_no_owner, label: Rules nobody could account for, type: int, required: true}
      - {key: inbound_exposed, label: Services reachable from the internet, type: int, required: true}
      - {key: segmentation, label: Segmentation between networks as intended, type: bool, required: true}
      - {key: guest_network, label: Guest and visitor network separated, type: bool, required: true}
      - {key: default_credentials, label: Devices found with default credentials, type: int, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: what is reachable from
where, and who decided.

It must state what is exposed to the internet and why each one is. That list is
the organisation's actual attack surface, it is almost always longer than
anybody expects, and producing it is more valuable than any other activity in
this document.

It must cover segmentation in terms the organisation has: the office network,
the guest Wi-Fi, the systems that hold regulated information, and anything
industrial or building-related — the door controller, the HVAC, the camera
recorder — which are routinely on the same flat network as the finance system
and are never patched.

It must say who may change a firewall rule and how that is recorded. Every rule
review that finds unexplainable rules is finding the absence of this, years
later.

It must name the filtering and protective services in use — web filtering, DNS
protection, mail filtering — and what they are configured to block. A.8.23 is
cheap, effective and usually half-configured.

It must cover the devices themselves: default credentials changed, management
interfaces not reachable from the internet, firmware supported and updated. A
router past its support date is an unpatchable asset at the perimeter.
