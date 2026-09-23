---
id: ohs.policy
kind: policy
title: Health and Safety Policy
structure: policy
path: policies/health-and-safety-policy.md

satisfies:
  # 4.3 is the scope of the management system, and a policy that does not say
  # what it covers has not been written. Added when the pack grew past six
  # artifacts: with one procedure the scope was obvious, with twenty-three it
  # is a statement somebody has to make.
  - iso_45001:4.3
  - iso_45001:5.1
  - iso_45001:5.2
  - cor_2020:COR-01
  - isnetworld:ISN-SAFE-03

declares:
  obligation:
    id: ohs.management-review
    activity: Management review of the health and safety programme
    cadence: each year
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/programme-reviews.md
    satisfies:
      - iso_45001:9.3
  register:
    title: Management Review Record
    note: >
      One row per review. ISO 45001 9.3 names the inputs a management review
      must consider; a record that lists none of them evidences a meeting.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: chaired_by, label: Chaired by, type: user, required: true}
      - {key: inputs, label: Inputs considered, type: longtext, required: true}
      - {key: performance, label: Performance against objectives, type: longtext, required: true}
      - {key: decisions, label: Decisions and actions, type: longtext, required: true}
      - {key: next_review, label: Next review due, type: date}
---

What this document must establish for THIS organisation: the commitment senior
management makes about the health and safety of the people who work here, in the
organisation's own words rather than a recital of the standard.

It must state who the policy applies to — including workers who are not
employees, contractors and visitors, and say so explicitly rather than by
omission — what management undertakes to provide, and how workers and their
representatives are consulted about decisions that affect their safety. It must
name the roles that carry authority for the programme by position, never by
person, because every obligation in the rest of the programme is assigned to a
position and an unfilled position is a finding.

It is the parent document: every other artifact in this programme inherits its
scope from here, so a vague scope here produces procedures that quietly disagree
about who they cover.
