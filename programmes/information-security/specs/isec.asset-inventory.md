---
id: isec.asset-inventory
version: 1.0.0
kind: register
title: Information Asset Inventory
structure: standard
path: registers/information-assets.md

# A register carries no `satisfies:`. It is the evidence that work happened,
# not the document that answers a control: `implements` onto a control may be
# asserted by a blueprint, a policy or a procedure and by nothing else
# (schemas/kinds.md, Relations), so a register's citation could never be
# recorded as answering. Its former claims:
# - iso_27001:A.5.9 withdrawn, answered by isec.asset-management.
# - can_ciosc_104:CIOSC-L1-14 withdrawn, answered by isec.asset-management.
# - nist_csf_2:ID.AM-05 moved to isec.asset-management.
# - cis_controls:3.1 moved to isec.asset-management.

register:
  title: Information Asset Inventory
  note: >
    One row per information asset — a body of information the organisation
    holds, not the box it sits in. Customer contracts, payroll data, the source
    code, the CAD drawings and the CRM contents are assets; the laptop is
    equipment and belongs in the IT asset register.

    `owner` is a position that can make decisions about the information:
    classify it, approve access to it, and agree it may be deleted. An asset
    owned by "IT" is an asset whose owner is whoever last touched the system.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: asset, label: Information asset, type: text, required: true}
    - {key: description, label: What it contains, type: longtext, required: true}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: classification, label: Classification, type: select, required: true,
       options: [Public, Internal, Confidential, Restricted]}
    - {key: personal_information, label: Contains personal information, type: bool, required: true}
    - {key: systems, label: Systems and services it lives in, type: longtext, required: true}
    - {key: location, label: Where it is held, type: select, required: true,
       options: [On premises, Canada — cloud, Outside Canada — cloud, Third party, Mixed]}
    - {key: retention_class, label: Retention class, type: text}
    - {key: review_due, label: Next review due, type: date, required: true}
---

What this artifact must establish: what information the organisation holds, who
owns it, how sensitive it is, and where it actually is.

It is the register the rest of the programme depends on. Classification has
nothing to classify without it, access control has no object, the retention
schedule has no subject, and a privacy breach cannot be scoped — the first
question after an incident is what was in there, and an organisation that
cannot answer it reports the worst case or guesses.

`personal_information` and `location` are here rather than in a separate privacy
inventory because they are facts about the same asset, and two inventories of
one estate disagree within a year. The privacy programme's record of processing
cites these rows rather than restating them.

It records information assets, not equipment. The distinction matters because
they have different owners, different lifecycles and different questions asked
of them: a laptop is replaced, and the information that was on it is not.
