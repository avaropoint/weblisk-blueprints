---
id: emp.termination
kind: procedure
title: Ending the Employment Relationship
structure: procedure
path: procedures/ending-employment.md

satisfies:
  - employment_standards_ontario:54
  - employment_standards_ontario:64
  - employment_standards_ontario:58
  - employment_standards_ontario:74
  - ohrc_ontario:5(1)
  - iso_27001:A.6.5

requires: [emp.employment-standards]

declares:
  obligation:
    id: emp.termination-review
    activity: Review terminations in the period against notice, severance and final pay requirements
    cadence: each quarter
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/termination-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Termination Review Record
    note: >
      One row per review period rather than per person, so the register records
      compliance rather than becoming a second personnel file. `severance_owed`
      and `severance_paid` are separate columns because severance is the
      entitlement most often missed entirely — it is additional to notice, and
      an employer under the payroll threshold one year may be over it the next.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: terminations, label: Terminations in the period, type: int, required: true}
      - {key: notice_or_pay_correct, label: Statutory notice or pay in lieu correct in every case, type: bool, required: true}
      - {key: severance_owed, label: Cases where severance was owed, type: int, required: true}
      - {key: severance_paid, label: Of those, paid, type: int, required: true}
      - {key: mass_termination, label: Mass termination thresholds reached, type: bool, required: true}
      - {key: form_1_filed, label: Form 1 filed where required, type: bool, required: true}
      - {key: final_pay_on_time, label: Final pay and accrued vacation paid on time, type: bool, required: true}
      - {key: benefits_continued, label: Benefits continued through the notice period, type: bool, required: true}
      - {key: access_removed, label: System access and assets recovered, type: bool, required: true}
      - {key: claims, label: Claims or complaints arising, type: int, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: what is owed when
employment ends, who calculates it, and what else has to happen that day.

It must separate statutory minimums from common-law entitlement, and say so
plainly. The Employment Standards Act sets a floor — one week's notice per year
of service to a maximum of eight, plus severance where the organisation's payroll
is $2.5 million or more and the employee has five years' service. The common law
usually requires considerably more reasonable notice unless the employment
contract validly limits it, and a termination clause that could pay less than the
statutory minimum in any circumstance is void in its entirety, which returns the
employee to the common-law entitlement. An organisation that treats the ESA
amount as the answer is budgeting for a fraction of its exposure.

It must state that benefits continue through the statutory notice period and
that vacation pay accrues on it, because those are the two errors that turn a
clean termination into a complaint.

It must cover mass termination as a distinct regime: fifty or more employees at
an establishment in a four-week period triggers eight, twelve or sixteen weeks'
notice depending on the number, and the notice does not begin to run until the
Form 1 is received by the Director. Filing late extends every employee's notice
period, which is an expensive administrative oversight.

It must require the reason to be recorded contemporaneously. Where a termination
follows a complaint, a leave, an accommodation request or a safety refusal, the
burden of proving that the Act was not contravened falls on the employer — and a
reason constructed afterwards reads exactly like one constructed afterwards.

It must connect the same-day security steps to the security programme rather
than restating them: access removed, assets returned, and continuing
confidentiality obligations confirmed in writing. The quarterly verification in
that programme exists because this list is always longer than the checklist.
