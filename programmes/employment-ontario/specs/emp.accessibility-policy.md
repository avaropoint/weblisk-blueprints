---
id: emp.accessibility-policy
kind: policy
title: Accessibility Policy and Multi-Year Plan
structure: policy
path: policies/accessibility-policy.md

satisfies:
  - aoda_ontario:3
  - aoda_ontario:4
  - aoda_ontario:5
  - aoda_ontario:6
  - aoda_ontario:80.46
  - aoda_ontario:80.47
  - aoda_ontario:80.48
  - ohrc_ontario:1

approved_by: [senior-management]

declares:
  obligation:
    id: emp.accessibility-plan-review
    activity: Review the accessibility policy and the multi-year accessibility plan, and report progress
    cadence: each year
    authority: IASR (O. Reg. 191/11) s. 4 — the multi-year plan is reviewed and updated at least once every five years, with an annual status report
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/accessibility-plan-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Accessibility Plan Review Record
    note: >
      One row per year. The annual status report is a requirement in its own
      right and the five-year plan update is a separate one, so
      `plan_updated_this_year` sits beside `status_report_published` — an
      organisation that has published four status reports on a plan it has not
      revisited has met one duty and missed the other.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: employees, label: Employees in Ontario, type: int, required: true}
      - {key: policies_documented, label: Policies documented and publicly available, type: bool, required: true}
      - {key: plan_last_updated, label: Multi-year plan last updated, type: date}
      - {key: plan_updated_this_year, label: Plan updated this year, type: bool, required: true}
      - {key: status_report_published, label: Annual status report published, type: bool, required: true}
      - {key: barriers_removed, label: Barriers removed in the period, type: longtext, required: true}
      - {key: procurement_criteria, label: Accessibility criteria used in procurement, type: bool, required: true}
      - {key: feedback_received, label: Accessibility feedback received in the period, type: int, required: true}
      - {key: actions, label: Actions planned for the coming year, type: longtext, required: true}
---

What this document must establish for THIS organisation: its commitment to
accessibility, the specific things it will do, and when.

It must record the employee count, because almost every obligation in the
Integrated Accessibility Standards Regulation scales with it. Every obligated
organisation with at least one employee owes the general requirements, the
training duty and the customer service standard. At twenty or more the
accessibility compliance report is filed. At fifty or more — a large organisation
— the policies must be in writing and publicly available, the multi-year plan is
required, and websites must meet WCAG 2.0 Level AA. An organisation that has
grown past fifty and is still operating as a small one is in breach of three
requirements at once and nothing will have told it.

It must include the statement of commitment the regulation requires: to meet the
accessibility needs of persons with disabilities in a timely manner.

It must set out the multi-year plan as a plan — barriers identified, what will be
done about each, and by when — rather than as a restatement of the regulation.
The status report each year is against those commitments, which is only possible
if they were specific.

It must cover the customer service requirements in the same document or point
clearly at where they are: how the organisation serves people with disabilities
in a way that respects dignity and independence, use of assistive devices,
service animals and support persons, and notice of a temporary disruption to a
facility or service people with disabilities rely on — with the reason, the
expected duration and the alternatives, posted where people will see it.

It must say how accessibility is built into buying things. Accessibility design,
criteria and features are incorporated when procuring goods, services or
facilities except where it is not practicable — and where it is not, an
explanation must be available on request. Accessibility that is not in the
requirement at purchase is bought out of the organisation for the life of the
asset.
