---
id: isec.asset-management
kind: procedure
title: Information Asset Management
structure: procedure
path: procedures/information-asset-management.md

satisfies:
  - iso_27001:A.5.9
  - iso_27001:A.5.10
  - iso_27001:A.5.11
  - iso_27001:A.7.9
  - iso_27001:A.7.10
  - iso_27001:A.7.14
  - iso_27001:A.8.10
  - nist_csf_2:ID.AM-01
  - can_ciosc_104:CIOSC-L1-14

requires: [isec.asset-inventory]

declares:
  obligation:
    id: isec.asset-inventory-review
    activity: Verify the information asset inventory against what is actually held
    cadence: each quarter
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/asset-inventory-reviews.md
  register:
    title: Asset Inventory Verification Record
    note: >
      One row per verification. `assets_found_unlisted` is the column that makes
      this a verification rather than a reading: an inventory checked against
      itself is always complete.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: verified_on, label: Verified on, type: date, required: true}
      - {key: verified_by, label: Verified by, type: user, required: true}
      - {key: assets_listed, label: Assets listed, type: int, required: true}
      - {key: assets_found_unlisted, label: Assets found that were not listed, type: int, required: true}
      - {key: assets_retired, label: Assets retired or disposed of, type: int, required: true}
      - {key: owners_vacant, label: Assets whose owner position is vacant, type: int, required: true}
      - {key: media_disposed, label: Media and equipment securely disposed of, type: int, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: how information gets
into the inventory, how it leaves, and what happens to the media it was on.

It must say who adds an asset and when. An inventory maintained only at review
time is an inventory that is wrong for eleven weeks in twelve; the moment a new
system is bought, a new data set is collected or a supplier is given a feed, the
row exists or the asset is invisible.

It must cover return of assets when somebody leaves — devices, keys, tokens,
documents and the accounts that are not physical but are still held. A.5.11 is
routinely read as equipment only, and the information a departing person holds
in a personal cloud account is the part nobody asks for back.

It must state how media and equipment are disposed of, by whom, and what record
proves it. "Wiped" is not a method and a certificate from the disposal contractor
is not proof that this device was on that truck: the serial number has to appear
somewhere.

It must set how acceptable use is communicated for each classification. The
acceptable use policy in the IT programme states the rules; this procedure is
what connects a rule to the asset it applies to, so a person handling restricted
information knows that is what they are handling.
