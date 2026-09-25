---
id: it.software-approval
kind: procedure
title: Software and Cloud Service Approval
structure: procedure
path: procedures/software-and-cloud-service-approval.md

satisfies:
  - iso_27001:A.8.19
  - iso_27001:A.5.22
  - iso_27001:A.5.23
  - iso_27001:A.5.32
  - can_ciosc_104:CIOSC-L1-10
  - cis_controls:2.1
  - cis_controls:2.3
  - cis_controls:2.5
  - nist_csf_2:PR.PS-01
  - soc2:CC6.8

requires: [it.asset-register, it.acceptable-use]

declares:
  obligation:
    id: it.software-review
    activity: Review the software and cloud services in use against what is approved
    cadence: each quarter
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/software-reviews.md
  register:
    title: Software and Service Review Record
    note: >
      One row per review. `services_found_unapproved` is the measurement that
      matters, and it is usually large the first time. A review that reports
      zero has checked the approved list against itself.
    layout: form
    review: required
    approvers: [it-manager]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: approved_count, label: Approved software and services, type: int, required: true}
      - {key: services_found_unapproved, label: Found in use and not approved, type: int, required: true}
      - {key: handling_personal_information, label: Of those, handling personal information, type: int, required: true}
      - {key: unsupported, label: Approved items now unsupported, type: int, required: true}
      - {key: licences_reconciled, label: Licences reconciled with use, type: bool, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: how something new gets
permission to hold the organisation's information, and how fast that permission
can be obtained.

It must be faster than the workaround. A cloud service is signed up for in four
minutes with a corporate credit card and an email address; an approval process
that takes three weeks does not prevent that, it only prevents anybody
mentioning it. A named person, a short set of questions and a two-day answer is
a control; a committee is a shadow IT generator.

It must ask the questions that decide the answer: what information goes in, is
any of it personal, where is it held, who else can reach it, what happens to it
if the service is stopped, and what it costs to leave. Anything that holds
personal information also needs the privacy programme's service provider
assessment, and anything critical to operations goes on the supplier register.

It must say what happens to software already in use when it is discovered. The
first review always finds a list; the useful response is to approve most of it,
replace some, and record the decisions — not to demand removal of the tools the
work is being done with.

It must cover licensing as well as security. A.5.32 sits in this family because
unlicensed software is a legal exposure with the same root cause as unapproved
software: nobody knows what is installed.

It must be connected to the asset register rather than keeping a second list.
An approved software list that is not the asset register is the second source of
truth that drifts.
