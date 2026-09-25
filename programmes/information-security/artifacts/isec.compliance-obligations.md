---
id: isec.compliance-obligations
kind: register
title: Legal, Regulatory and Contractual Security Obligations
structure: standard
path: registers/security-compliance-obligations.md

satisfies:
  - iso_27001:A.5.31
  - iso_27001:A.5.32
  - iso_27001:A.5.34
  - iso_22301:4.2
  - nist_csf_2:GV.OC-03
  - soc2:CC2.3

requires: [isec.policy]

register:
  title: Legal, Regulatory and Contractual Security Obligations
  note: >
    One row per obligation the organisation is under that constrains how it
    handles information — statute, regulation, contract clause, certification
    commitment or insurance condition. A contractual security commitment is on
    this register for the same reason a statute is: it binds, and breaching it
    costs the contract.

    `how_met` names the artifact or control that answers it. An obligation with
    nothing in that column is one nobody has assigned, which is the finding the
    register exists to surface.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: obligation, label: Obligation, type: longtext, required: true}
    - {key: source, label: Source, type: select, required: true,
       options: [Statute, Regulation, Contract, Certification, Insurance, Client policy, Other]}
    - {key: citation, label: Citation, type: text, required: true}
    - {key: applies_because, label: Why it applies to us, type: longtext, required: true}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: how_met, label: How it is met, type: longtext, required: true}
    - {key: evidence, label: Where the evidence is, type: text}
    - {key: review_due, label: Next review due, type: date, required: true}
---

What this artifact must establish: every rule about information the organisation
is actually bound by, and why each one applies to it.

`applies_because` is the column that stops this register becoming a list of
every law somebody has heard of. PIPEDA applies because the organisation
collects personal information in the course of commercial activity; PHIPA
applies only if it is a health information custodian or an agent of one; FIPPA
applies only if it is an institution or is handling an institution's records
under contract. An organisation that adopts obligations it does not owe reports
gaps it cannot close and learns to ignore the register.

It carries intellectual property and privacy obligations as well as security
ones, because A.5.32 and A.5.34 sit in the same family and because a licence
condition on software is enforced by the same people who enforce everything else
here.

It is a register rather than a section of the policy because obligations arrive
one at a time — a new client contract, a new jurisdiction, a new certification —
and a paragraph in a policy is updated at review time, which is up to a year
after the obligation started binding.
