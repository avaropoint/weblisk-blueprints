---
id: priv.collection-and-consent
kind: procedure
title: Collection, Use and Consent
structure: procedure
path: procedures/collection-use-and-consent.md

satisfies:
  - pipeda:PIPEDA-2
  - pipeda:PIPEDA-3
  - pipeda:PIPEDA-4
  - pipeda:PIPEDA-5
  - pipeda:PIPEDA-6
  - quebec_law25:CT-1
  - quebec_law25:GA-4
  - soc2:P2.1
  - soc2:P4.1

requires: [priv.inventory]

declares:
  obligation:
    id: priv.inventory-review
    # Record-origin. Each collection is reviewed on its own date: a customer
    # database that has not changed in three years and a new marketing
    # integration do not share a review cycle.
    activity: Review a collection of personal information — still needed, still accurate, still on a lawful basis
    for:
      records: registers/personal-information.md
      due: 30d before review_due
      key: reference
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/personal-information-reviews.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - pipeda:PIPEDA-4
      - pipeda:PIPEDA-5
  register:
    title: Personal Information Review Record
    note: >
      One row per review of one collection, keyed by its reference.
      `still_necessary` is the question the whole regime turns on: information
      kept because deleting it is work is information held without a purpose,
      and the limiting-retention principle says it must go.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: reference, label: Collection reviewed, type: relation, required: true,
         target: /registers/personal-information.md#records, display: information}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: still_necessary, label: Still necessary for the stated purpose, type: bool, required: true}
      - {key: basis_confirmed, label: Basis confirmed, type: bool, required: true}
      - {key: minimised, label: Fields no longer needed identified, type: int, required: true}
      - {key: accuracy_checked, label: Accuracy checked, type: bool, required: true}
      - {key: notice_matches, label: Privacy notice describes it correctly, type: bool, required: true}
      - {key: action, label: Action taken, type: longtext, required: true}
      - {key: next_review, label: Next review due, type: date, required: true}
---

What this document must establish for THIS organisation: how somebody decides
that a piece of personal information may be collected, and what they have to
tell the person at the time.

It must apply the necessity test before the consent one. PIPEDA limits
collection to what is necessary for identified purposes, and consent does not
rescue an unnecessary collection — an organisation asking for a date of birth on
a contact form with the person's agreement is still collecting information it
does not need.

It must say when express consent is required rather than implied. Sensitive
information, a purpose a reasonable person would not expect, and any secondary
use are the three cases; everything else can be implied from the transaction if
the purposes were identified at or before collection.

It must state the rule for a new purpose. Personal information collected for one
purpose and used for another requires fresh consent unless a statutory exception
applies, and this is the most common contravention in practice: the customer
list used for marketing, the recruitment records used for analytics, the
security camera footage used for performance management.

It must cover accuracy and the correction route, which is the principle that is
easiest to meet and most often unimplemented. Information used to make a
decision about somebody must be accurate enough for that decision.

It must name what triggers a privacy impact assessment: a new collection, a new
purpose, a new service provider, a new system holding personal information, a
transfer to a new jurisdiction, or any automated decision-making. That trigger
is the connection between this procedure and the assessment one.
