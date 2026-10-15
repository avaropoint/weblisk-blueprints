---
id: document-control.policy
version: 1.1.0
kind: policy
title: Document Control Policy
structure: policy
path: policies/document-control-policy.md
template: policy

satisfies:
  # The rule that documented information is controlled at all, and the policy
  # about policies. Cited by id only: the control text is the standard's, read
  # at the edition the tenant adopted.
  - iso_9001:7.5
  - iso_45001:7.5
  - iso_27001:A.5.1

# A policy that says controlled documents are approved before they govern, and
# that is itself in force on nobody's authority, has failed its own first rule.
approved_by: [senior-management]

declares:
  obligation:
    id: document-control.management-review
    activity: Management review of the document control programme
    cadence: each year
    responsible: document-controller
    applies_to: the organisation
    records: registers/management-reviews.md
  register:
    title: Management Review Record
    note: >
      One row per review. The inputs considered and the decisions taken are
      both required: a review that records neither is a meeting, and a
      certifying body reads it as one.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: chaired_by, label: Chaired by, type: user, required: true}
      - {key: inputs, label: Inputs considered, type: longtext, required: true}
      - {key: decisions, label: Decisions and actions, type: longtext, required: true}
      - {key: next_review, label: Next review due, type: date}
---

What this document must establish for THIS organisation: the rule that decides
when a document governs and when it is merely a draft somebody wrote.

It must say which documents are controlled and which are not, because an
organisation that controls everything controls nothing — the distinction is the
first thing an auditor tests. It must name the roles that approve, issue and
withdraw a controlled document by POSITION rather than by person, so the
programme survives somebody leaving; an unfilled position is then a finding
rather than a silence.

It must state how a reader knows the copy in front of them is current, and what
happens to superseded versions. Retaining them is usually required and always
wise, but a superseded version that is indistinguishable from the current one is
worse than one that was destroyed.

It is the parent document: every other artifact here inherits its scope from
this one, so a vague scope produces procedures that quietly disagree about what
they cover.
