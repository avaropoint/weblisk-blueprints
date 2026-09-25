---
id: isec.supplier-register
kind: register
title: Supplier and Service Register
structure: standard
path: registers/suppliers.md

satisfies:
  - iso_27001:A.5.19
  - nist_csf_2:GV.SC-01
  - can_ciosc_104:CIOSC-L1-16

register:
  title: Supplier and Service Register
  note: >
    One row per supplier or service that holds the organisation's information,
    processes it, or can reach a system that does. That includes the cloud
    services nobody procured formally: a free file-sharing account with client
    documents in it is a supplier relationship whether or not money changed
    hands.

    `review_due` is what makes the register live — it is the date the supplier
    security review is triggered from, and a row without one is a supplier
    nobody will look at again.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: supplier, label: Supplier, type: text, required: true}
    - {key: service, label: Service provided, type: text, required: true}
    - {key: owner, label: Relationship owner (position), type: text, required: true}
    - {key: information_held, label: Information they hold or reach, type: longtext, required: true}
    - {key: classification, label: Highest classification involved, type: select, required: true,
       options: [Public, Internal, Confidential, Restricted]}
    - {key: personal_information, label: Personal information involved, type: bool, required: true}
    - {key: data_location, label: Where the data is held, type: select, required: true,
       options: [Canada, United States, European Union, Other, Unknown]}
    - {key: criticality, label: Criticality to operations, type: select, required: true,
       options: [Low, Medium, High, Cannot operate without it]}
    - {key: agreement, label: Security terms agreed, type: select, required: true,
       options: [In contract, Separate agreement, Standard terms only, None]}
    - {key: assurance, label: Assurance held, type: select, required: true,
       options: [None, Questionnaire, SOC 2 report, ISO 27001 certificate, Audit right exercised, Other]}
    - {key: contract_ends, label: Contract ends, type: date}
    - {key: review_due, label: Next review due, type: date, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [Active, Being onboarded, Being exited, Ended]}
---

What this artifact must establish: every third party that holds the
organisation's information or can reach it, and what the organisation knows
about how they protect it.

It is the register three separate duties depend on. Supplier security review is
triggered from these rows; the privacy programme's accountability for transfers
to service providers is answered from the same list; and continuity planning
needs the `criticality` column to know which supplier failing stops the
business.

`data_location` is a column rather than a note because it is the question asked
first when personal information is involved, and "Unknown" is a legitimate and
important answer. Recording it as unknown is a finding somebody can act on;
leaving the column out is the same ignorance with nothing to show for it.

`agreement: Standard terms only` is the honest answer for most small suppliers
and it is worth being able to say. An organisation that can see it has signed
the supplier's own terms for its most sensitive service has learned something a
register of contract dates would never have told it.
