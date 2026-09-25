---
id: it.change-management
kind: procedure
title: Change Management
structure: procedure
path: procedures/change-management.md

satisfies:
  - iso_27001:A.8.32
  - iso_27001:A.8.19
  - iso_27001:A.8.31
  - can_ciosc_104:CIOSC-L1-20
  - nist_csf_2:PR.PS-01
  - soc2:CC8.1

requires: [it.asset-register]

declares:
  obligation:
    id: it.change-review
    # Record-origin: a change is implemented once, on a date, and the review is
    # due relative to that date. There is no period a change belongs to.
    activity: Post-implementation review of a change
    for:
      records: registers/change-requests.md
      due: 5d after implemented_on
      key: reference
    responsible: it-manager
    applies_to: the organisation
    records: registers/it-change-reviews.md
    escalate: {after: 7d, to: information-security-lead}
    satisfies:
      - iso_27001:A.8.32
  register:
    title: IT Change Review Record
    note: >
      One row per review of one change, keyed by the change's reference.
      `caused_incident` is the column that connects this register to the
      security incident register, and it is how an organisation learns that a
      third of its incidents are its own changes.
    layout: form
    review: required
    approvers: [it-manager]
    columns:
      - {key: reference, label: Change, type: relation, required: true,
         target: /registers/change-requests.md#records, display: reference}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: as_intended, label: Did what it was supposed to, type: bool, required: true}
      - {key: caused_incident, label: Caused an incident or degradation, type: bool, required: true}
      - {key: documentation_updated, label: Documentation and configuration records updated, type: bool, required: true}
      - {key: asset_register_updated, label: Asset register updated, type: bool, required: true}
      - {key: lessons, label: What would be done differently, type: longtext, required: true}
---

What this document must establish for THIS organisation: how a change to a
production system gets agreed, made, and checked afterwards.

It must be proportionate or it will be bypassed. Three classes are usually
enough: standard changes that are pre-approved because they are routine and
reversible, normal changes that need an approval, and emergency changes that are
made first and recorded immediately after. An organisation that requires a
committee for a password reset has a shadow change process, and nothing in it is
recorded.

It must state who approves what, and never let the person making the change be
the only approver for a high-risk one. Where the organisation is too small for
that to be possible, it must say so and name the compensating control — a review
afterwards by somebody else is a legitimate answer.

It must require the security and privacy impact to be considered before
approval, not after. A change that opens a network path, adds a data flow to a
new supplier or alters who can see personal information is a change that belongs
in the risk register or the record of processing, and the only moment anybody
will notice is at approval.

It must require a backout plan and say what happens when there is not one. Some
changes genuinely cannot be undone; the answer is to know that in advance and
decide accordingly, not to leave the field blank.

It must say what happens to the emergency change afterwards. An emergency
process with no retrospective approval step becomes the normal process within a
quarter.

Five days for the review, escalating after seven more. Short enough that the
person who made the change still remembers what they did, and long enough for
whatever was going to break to have broken.
