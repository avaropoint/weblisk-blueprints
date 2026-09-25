---
id: priv.inventory
kind: register
title: Personal Information Inventory
structure: standard
path: registers/personal-information.md

satisfies:
  - pipeda:PIPEDA-2
  - pipeda:PIPEDA-4
  - pipeda:PIPEDA-5
  - quebec_law25:GA-2
  - fippa_mfippa:FM-01
  - iso_27001:A.5.34
  - soc2:P1.1

register:
  title: Personal Information Inventory
  note: >
    One row per collection of personal information — a purpose and a population,
    not a system. "Customer contact details, for fulfilling orders" is a row;
    "the CRM" is a system that may hold four rows' worth.

    `retention_rule` points at a class in the retention schedule rather than
    repeating a period, so that the schedule stays the single place a keeping
    period is decided.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: information, label: Information held, type: longtext, required: true}
    - {key: about_whom, label: About whom, type: select, required: true,
       options: [Customers, Prospects, Employees, Job applicants, Contractors,
                 Suppliers' staff, Website visitors, Members of the public, Other]}
    - {key: purpose, label: Purpose it was collected for, type: longtext, required: true}
    - {key: authority, label: Basis, type: select, required: true,
       options: [Express consent, Implied consent, Necessary for the contract,
                 Employment relationship, Required by law, Permitted without consent, Unclear]}
    - {key: sensitivity, label: Sensitivity, type: select, required: true,
       options: [Ordinary, Sensitive, Health information, Financial, Government identifier]}
    - {key: source, label: Where it comes from, type: text, required: true}
    - {key: systems, label: Systems it is held in, type: longtext, required: true}
    - {key: shared_with, label: Shared with, type: longtext}
    - {key: location, label: Where it is stored, type: select, required: true,
       options: [Canada, United States, European Union, Other, Multiple, Unknown]}
    - {key: retention_rule, label: Retention class, type: text, required: true}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: review_due, label: Next review due, type: date, required: true}
---

What this artifact must establish: every kind of personal information the
organisation holds, why it has it, and where it is.

It is the artifact the rest of the privacy programme is impossible without. A
breach cannot be scoped without it, an access request cannot be answered
completely without it, a retention schedule has nothing to schedule, and the
notice describes practices nobody has verified. It is also the artifact
organisations most often skip, because it is the only one that requires going
and looking.

`authority: Unclear` is a legitimate and valuable answer. An honest inventory of
a real organisation has rows where nobody can say why the information was
collected or on what basis it is held, and those rows are the work. Recording
them as consent because the form has to be filled in converts an open question
into a false answer.

`sensitivity` drives everything downstream: the safeguards required, whether
express consent was needed, and whether a breach is likely to cause a real risk
of significant harm. Health information in the hands of an organisation that is
not a health information custodian — an employer holding medical certificates,
for instance — is sensitive information under PIPEDA and is not PHIPA
information, and the row is where that distinction is recorded.

It is one inventory, not two. The information asset inventory in the security
programme records the same estate from the security side and carries a
`personal_information` flag; this register is where the privacy questions about
those assets are answered. Two separate inventories of one organisation disagree
within a year.
