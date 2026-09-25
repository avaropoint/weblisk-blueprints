---
id: isec.incident-review
kind: procedure
title: Learning From Security Incidents
structure: procedure
path: procedures/security-incident-review.md

satisfies:
  - iso_27001:A.5.27
  - nist_csf_2:RS.AN-06
  - nist_csf_2:ID.IM-01
  - nist_csf_2:ID.IM-02
  - soc2:CC4.2

requires: [isec.incident-response]

declares:
  obligation:
    id: isec.incident-trend-review
    # The chain terminates in a cadence on purpose. A trigger whose recording
    # register is its own trigger register discharges every occurrence the
    # moment it creates one, so the last link is a periodic sweep of what is
    # open and late.
    activity: Review security incidents, their causes and what is still open
    cadence: each quarter
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/security-incident-reviews.md
  register:
    title: Security Incident Review Record
    note: >
      One row per review period. `investigations_overdue` is what makes this a
      sweep rather than a summary: the point of the quarterly review is to find
      the incidents whose investigation never happened, and a report of closed
      incidents cannot show them.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: period, label: Period covered, type: text, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: incidents_opened, label: Incidents opened, type: int, required: true}
      - {key: incidents_closed, label: Incidents closed, type: int, required: true}
      - {key: investigations_overdue, label: Investigations overdue, type: int, required: true}
      - {key: repeat_causes, label: Causes seen more than once, type: longtext, required: true}
      - {key: controls_changed, label: Controls changed as a result, type: longtext, required: true}
      - {key: risks_raised, label: Risks added or re-scored, type: int, required: true}
---

What this document must establish for THIS organisation: what the organisation
does with a pile of closed incidents.

It must look for the cause that appears twice. One incident is an event; the
same underlying cause in three incidents is a control that does not work, and
nothing in the per-incident investigation can see it because each investigation
sees one.

It must connect back to the risk register. An incident is a risk that was
realised, and either it was on the register — in which case the score or the
treatment was wrong — or it was not, in which case the assessment missed
something. Both outcomes are rows, and a review that produces neither has
decided that nothing was learned.

It must count what is still open, and name it. A review that reports only on
closed incidents produces a picture that improves as the backlog grows.

It must be the quarterly sweep that catches what the record-origin chain cannot:
an incident reported and never investigated raises one overdue occurrence and
then stays exactly as overdue as it was, which is easy to stop noticing.
