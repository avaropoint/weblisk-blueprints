---
id: subcontractor-prequalification
label: Subcontractor Prequalification
description: What a sub-trade must produce before they are on the approved list — and the dates every one of those documents expires on.
path: records/prequalification/untitled-prequalification.md
# `kind: reference` is what THIS FILE is: a blank template, which is not
# evidence of anything and must never count as coverage. What the CREATED
# document is appears under `frontmatter:` below — that is the kind that
# reaches the chain, once a person has filled the form in.
template: true
kind: reference
order: 170
frontmatter:
  title: Subcontractor Prequalification
  kind: evidence
  status: draft
  contractor:
  qualified_on:
---

# Subcontractor Prequalification

> [!IMPORTANT]
> Every document a sub-trade hands over is **a statement about a date**. A
> clearance certificate, a certificate of insurance and a training card all
> expire, and a prequalification file with no expiry dates in it is a filing
> cabinet that reports itself as compliant. Fill in every *expires on* field —
> those dates are what the renewal work is raised from, one piece of work per
> certificate, not one monthly reminder to read a table.

> [!NOTE]
> **A clearance certificate is not insurance, and neither is a WSIB account
> number.** A clearance certificate says the board has no outstanding claim
> against that contractor's account as at a date, and it protects the
> principal from the contractor's unpaid premiums. Ask for it per contract, and
> again when it expires.
>
> The completed record is one row in **Sub-Trade Requalification Record**
> (`registers/subcontractor-prequalification.md`); each certificate is a row in
> the certificate register, which is what the chasing is driven from.

```wl:table
id: records
title: Subcontractor prequalification
columns:
  - {key: contractor, label: Contractor, type: text, required: true}
  - {key: legal_name, label: Legal name, type: text, required: true, help: "The name on the insurance certificate and the WSIB account, which is often not the name on the truck."}
  - {key: contact_name, label: Contact, type: text, required: true}
  - {key: contact_email, label: Contact email, type: text, required: true}
  - {key: trades, label: Trades, type: longtext, required: true}
  - {key: workers_typical, label: Typical crew size, type: int}
  - {key: qualified_on, label: Assessed on, type: date, required: true}
  - {key: qualified_by, label: Assessed by, type: text, required: true}
  - {key: wsib_account, label: WSIB account number, type: text, required: true}
  - {key: clearance_reference, label: Clearance certificate reference, type: text, required: true}
  - {key: clearance_expires_on, label: Clearance expires on, type: date, required: true}
  - {key: independent_operator, label: Independent operator declaration held, type: bool, help: Only where the contractor is genuinely exempt. An exemption assumed is a premium the principal pays.}
  - {key: cgl_insurer, label: General liability insurer, type: text, required: true}
  - {key: cgl_limit, label: General liability limit, type: currency, required: true}
  - {key: cgl_expires_on, label: General liability expires on, type: date, required: true}
  - {key: auto_expires_on, label: Automobile liability expires on, type: date}
  - {key: additional_insured, label: We are named as additional insured, type: bool, required: true}
  - {key: written_programme, label: Written health and safety programme provided, type: bool, required: true}
  - {key: policy_signed_current_year, label: Health and safety policy signed this year, type: bool, required: true}
  - {key: competent_supervisor, label: Names a competent supervisor for our sites, type: bool, required: true}
  - {key: training_matrix, label: Training records provided, type: bool, required: true}
  - {key: working_at_heights_all, label: All workers at height hold Working at Heights, type: bool, required: true}
  - {key: whmis_all, label: All exposed workers hold WHMIS, type: bool, required: true}
  - {key: accreditation, label: Accreditation, type: select, options: [None, COR, SECOR, ISO 45001, Other]}
  - {key: accreditation_expires_on, label: Accreditation expires on, type: date}
  - {key: isn_or_equivalent, label: Prequalification service and grade, type: text, help: "ISNetworld, Avetta, ComplyWorks. A green grade is somebody else's assessment, not ours."}
  - {key: statistics_reviewed, label: Injury statistics and experience rating reviewed, type: bool, required: true}
  - {key: convictions, label: "Convictions, orders or stop-work in the last three years", type: longtext, required: true}
  - {key: performance_on_our_sites, label: Performance on our sites, type: longtext}
  - {key: documents, label: Documents received, type: attachment}
  - {key: outcome, label: Outcome, type: select, options: [Approved, Approved with conditions, Declined, Pending information], required: true}
  - {key: conditions, label: Conditions, type: longtext, help: "What must be produced, by when, and what happens if it is not."}
  - {key: next_review_on, label: Requalify by, type: date, required: true}
layout: form
review: required
approvers: [procurement-lead]
```

| Contractor | Legal name | Contact | Contact email | Trades | Typical crew size | Assessed on | Assessed by | WSIB account number | Clearance certificate reference | Clearance expires on | Independent operator declaration held | General liability insurer | General liability limit | General liability expires on | Automobile liability expires on | We are named as additional insured | Written health and safety programme provided | Health and safety policy signed this year | Names a competent supervisor for our sites | Training records provided | All workers at height hold Working at Heights | All exposed workers hold WHMIS | Accreditation | Accreditation expires on | Prequalification service and grade | Injury statistics and experience rating reviewed | Convictions, orders or stop-work in the last three years | Performance on our sites | Documents received | Outcome | Conditions | Requalify by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Assigning responsibilities

Prequalifying is not the same as telling a contractor what they are responsible
for on **this** project. Record the assignment against the contract — who is the
constructor, who provides first aid, who owns the hoist, who controls access, and
which of our procedures they are required to follow — and have somebody with
authority on their side acknowledge it.
