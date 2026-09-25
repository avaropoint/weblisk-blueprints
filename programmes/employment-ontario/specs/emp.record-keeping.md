---
id: emp.record-keeping
kind: procedure
title: Employment Record Keeping
structure: procedure
path: procedures/employment-record-keeping.md

satisfies:
  - employment_standards_ontario:15
  - employment_standards_ontario:41.1.1
  - iso_27001:A.5.33
  - pipeda:PIPEDA-5

requires: [emp.employment-standards]

declares:
  obligation:
    id: emp.record-check
    activity: Verify that the employment records the Act requires are kept, complete and retained
    cadence: each year
    authority: Employment Standards Act, 2000 s. 15 — records retained three years, five years for vacation records
    interval_basis: chosen
    responsible: hr-lead
    applies_to: the organisation
    records: registers/employment-record-checks.md
  register:
    title: Employment Record Check Record
    note: >
      One row per check. `records_missing` is counted rather than described
      because the Act's remedy for missing records is that the employee's
      account is generally preferred — a count is the organisation's exposure,
      and a narrative is not.
    layout: form
    review: required
    approvers: [hr-lead]
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: employees_sampled, label: Employee files sampled, type: int, required: true}
      - {key: records_missing, label: Files missing a required record, type: int, required: true}
      - {key: hours_recorded, label: Daily and weekly hours recorded for all non-exempt staff, type: bool, required: true}
      - {key: vacation_records, label: Vacation time and pay records retained five years, type: bool, required: true}
      - {key: leave_documents, label: Leave documents retained three years after the leave, type: bool, required: true}
      - {key: agreements_retained, label: Written agreements retained as required, type: bool, required: true}
      - {key: readily_available, label: Records readily available for inspection, type: bool, required: true}
      - {key: disposal_on_schedule, label: Records past retention disposed of on schedule, type: bool, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: what has to be written
down about each employee, for how long, and where it is.

It must list what section 15 requires: name, address and start date; date of
birth for a student under eighteen; the hours worked each day and each week; the
information in every wage statement; and the documents relating to each leave
taken. Hours are the one organisations skip for salaried staff, and they are the
records an employment standards officer asks for first when overtime is in
dispute.

It must state the retention periods as the Act sets them, not as a single
number: three years after the work was performed for most records, five years
after the vacation entitlement year for vacation time and pay, three years after
they expire for excess-hours and averaging agreements, and three years after the
leave ended for leave documents. Those periods belong in the records programme's
retention schedule with this Act as the authority, rather than only here.

It must require the records to be readily available for inspection. Records in a
payroll provider's system the organisation cannot export, or in a departed
manager's spreadsheet, are records the organisation cannot produce.

It must say what happens when a record is missing. The practical consequence is
that the employee's version is generally what stands, so a missing hours record
is not a paperwork gap — it is the loss of the only evidence the employer would
have had.

It must cover the electronic monitoring policy's own retention: the Act requires
it to be kept for three years after it ceases to be in effect, which means
superseded versions are retained rather than replaced.

It must respect that employee records are personal information. In Ontario there
is no private-sector statute governing an employer's handling of employee
information — PIPEDA reaches employee information only for federally regulated
employers — which does not make the records unprotected: they are governed by
the employment relationship, by the common law, and by this organisation's own
security and retention rules. That is worth stating plainly, because the absence
of a statute is routinely mistaken for the absence of a duty.
