---
id: cohs.policy
kind: policy
title: Occupational Health and Safety Policy
structure: policy
path: policies/occupational-health-and-safety-policy.md

satisfies:
  - construction_safety_ca:CSA-OHS-1
  - cor_2020:COR-01
  - iso_45001:5.1
  - iso_45001:5.2
  - isnetworld:ISN-SAFE-03

approved_by: [senior-management]

declares:
  obligation:
    id: cohs.policy-review
    activity: Review of the written occupational health and safety policy
    cadence: each year
    authority: OHSA s. 25(2)(j) — "prepare and review at least annually a written occupational health and safety policy"
    interval_basis: required
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/construction/policy-reviews.md
    escalate: {after: 4w, to: senior-management}
    satisfies:
      - cor_2020:COR-01
      - iso_45001:5.2
  register:
    title: Policy Review Record
    note: >
      One row per review. `changed` and `reissued_on` are separate from
      `reviewed_on` because the duty is to review annually, not to change
      annually: a policy read, considered and left alone is a discharged
      obligation, and a register that can only record amendments pushes somebody
      towards a cosmetic edit to have something to show.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: changes_considered, label: What was considered, type: longtext, required: true}
      - {key: changed, label: Policy amended, type: bool, required: true}
      - {key: summary_of_change, label: Summary of the amendment, type: longtext}
      - {key: signed_by, label: Signed by, type: signature}
      - {key: reissued_on, label: Reissued and posted on, type: date}
      - {key: posting_method, label: How it was made available, type: select,
         options: [Posted at each project, Electronic, Both]}
---

What this document must establish for THIS organisation: the commitment senior
management makes about the health and safety of everyone on its projects,
written in the organisation's own words and signed by a person with the
authority to bind it.

It must say whether the organisation acts as a **constructor**, as an employer,
or as both, and on which kinds of project. That single statement decides which
of the duties in this programme land on it. An owner who undertakes all or part
of a project itself, or through more than one employer, is a constructor whether
or not it calls itself one — and engaging an architect or engineer solely to
oversee quality control does not make an owner the constructor. A policy that
leaves the role unstated leaves every downstream artifact guessing at its own
scope.

It must extend to people who are not employees. On a construction project the
constructor's duty reaches every employer and every worker present, including
sub-trades, independent operators and visitors, and a policy scoped to "our
employees" contradicts the statute in its first paragraph.

It must name positions and never people, because every obligation in this
programme is assigned to a position and an unfilled position is a finding rather
than a blank.

The annual review is a statutory duty under OHSA s. 25(2)(j) and the interval is
the law's, not this organisation's. The exemption for a workplace where five or
fewer workers are regularly employed (s. 25(4)) is real and narrow, and a growing
contractor crosses it without noticing; the document should say which side of it
the organisation is on and what happens when that changes. The policy must be
posted at each project, or made available in a readily accessible electronic
format — the electronic option is a 2024 amendment and older guidance still says
posting is the only route.

If the organisation already holds a health and safety policy under a general
management-system programme, this IS that document, extended to say what the
construction role requires. Two health and safety policies is one too many, and
the one nobody reads will be the one an inspector finds.
