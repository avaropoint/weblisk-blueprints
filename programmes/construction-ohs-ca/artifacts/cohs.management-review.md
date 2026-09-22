---
id: cohs.management-review
kind: procedure
title: Management Review
structure: procedure
path: procedures/construction/management-review.md

satisfies:
  - cor_2020:COR-02
  - iso_45001:9.3
  - iso_45001:10.3

requires: [cohs.policy]

declares:
  obligation:
    id: cohs.management-review
    activity: Management review of the construction health and safety programme
    cadence: each year
    authority: ISO 45001:2018 clause 9.3 requires review at planned intervals; COR 2020 requires management review. Neither names an interval
    interval_basis: chosen
    responsible: senior-management
    applies_to: the organisation
    records: registers/construction/management-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Management Review Record
    note: >
      One row per review. The inputs are enumerated because the standard
      enumerates them: a record that lists attendance and decisions but not what
      was put in front of the meeting evidences a meeting rather than a review,
      and it is the difference an auditor tests first.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: chaired_by, label: Chaired by, type: user, required: true}
      - {key: attendees, label: Attendees, type: longtext, required: true}
      - {key: worker_input, label: How workers and their representatives were consulted, type: longtext, required: true}
      - {key: legal_evaluation, label: Compliance evaluation results considered, type: longtext, required: true}
      - {key: incidents_and_actions, label: Incidents, nonconformities and corrective actions, type: longtext, required: true}
      - {key: audit_results, label: Audit results considered, type: longtext, required: true}
      - {key: performance, label: Performance against objectives, type: longtext, required: true}
      - {key: risks_and_changes, label: Changes in the work, the risks and the law, type: longtext, required: true}
      - {key: resources, label: Adequacy of resources, type: longtext, required: true}
      - {key: decisions, label: Decisions and actions, with owners and dates, type: longtext, required: true}
      - {key: next_review, label: Next review due, type: date}
---

What this document must establish for THIS organisation: who reviews the whole
programme, what is put in front of them, and what has to come out of it.

It must name **senior management** and mean it. A review chaired by the safety
lead reporting to the safety lead is a departmental meeting. The reason the
standard puts this at the top is that most of the decisions a programme needs —
resources, priorities, whether a schedule may be allowed to compress a control —
cannot be taken anywhere else.

It must enumerate the **inputs**, because that is where this review is
distinguishable from every other meeting: the status of actions from the last
review, changes in external and internal issues including legal requirements,
performance information covering incidents, corrective actions, monitoring results
and audit results, the compliance evaluation, consultation and participation of
workers, risks and opportunities, and the adequacy of resources.

Two of those are worth saying out loud for a construction organisation. The first
is **worker consultation**, which is the clause with no analogue in the quality or
environmental standards and consequently the one most often under-evidenced — the
committee's minutes and its written recommendations are the evidence, and "the
committee exists" is not.

The second is **climate**, which is now part of what the standard asks the
organisation to determine as a relevant issue. For construction this is not
abstract: heat, wildfire smoke, and extreme weather are the risks that changed
most in a decade, and they belong in the review as hazards rather than as
sustainability reporting.

It must produce **decisions with owners and dates**, and it must record the ones
that were declined. A review whose output is a list of things everybody agreed
were important is a review that will be repeated verbatim next year.

**The annual interval is this organisation's choice.** The standard says planned
intervals and names no number, and neither does the accreditation scheme. A year
is chosen to align with the policy review the Act does require annually, so that
one preparation serves both — and the document should say that is the reason,
because an organisation whose programme changes quickly should review more often
and should not feel it is departing from a requirement by doing so.

It should note that the standard the organisation certifies to is itself under
revision, with a new edition expected and a transition period expected to follow.
The practical consequence is a design one: the programme's mapping to clause
numbers should be re-pointable, so that a new edition is a re-mapping exercise
rather than a rewrite. Nothing about the content of that future edition should be
stated as a requirement, because it is not published.
