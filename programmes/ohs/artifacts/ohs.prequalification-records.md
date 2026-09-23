---
id: ohs.prequalification-records
kind: register
title: Register of Insurance and Clearance Certificates
structure: standard
path: registers/prequalification-records.md

satisfies:
  - isnetworld:ISN-SAFE-02

requires: [ohs.contractor-management]

register:
  title: Register of Insurance and Clearance Certificates
  note: >
    One row per certificate held, ours and our contractors'. `expires_on` is
    required and is the entire point: a certificate is a statement about a date,
    and a register of certificates with no expiry is a filing cabinet that
    reports itself as compliant.
  columns:
    - {key: holder, label: Held by, type: text, required: true}
    - {key: kind, label: Certificate, type: select, required: true,
       options: [Workers compensation clearance, Liability insurance, Vehicle insurance, Bonding, Trade licence, Other]}
    - {key: issuer, label: Issued by, type: text, required: true}
    - {key: reference, label: Reference or policy number, type: text, required: true}
    - {key: issued_on, label: Issued on, type: date, required: true}
    - {key: expires_on, label: Expires on, type: date, required: true}
    - {key: coverage, label: Coverage or limit, type: text}
    - {key: verified_with_issuer, label: Verified with the issuer, type: bool, required: true}
    - {key: held_for, label: Work it covers, type: text}

declares:
  obligation:
    id: ohs.certificate-check
    activity: Check for certificates expiring within the next period
    cadence: each month
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/prequalification-records.md
---

What this artifact must establish: which insurance and clearance certificates
this organisation and its contractors hold, and when each one stops being true.

It must be checked BEFORE expiry rather than at it. A clearance certificate that
lapsed last week means work proceeded uninsured, and discovering that from the
certificate itself is discovering it too late — which is why the obligation above
looks ahead rather than reconciling the past.

It must record whether the certificate was verified WITH THE ISSUER rather than
accepted as a document. A workers-compensation clearance is a statement about an
account in good standing at a moment, and a PDF is not that statement; several
boards publish a live check for exactly this reason.

It must cover the organisation's own certificates and its contractors'. They
expire the same way and are asked for in the same audit, and separating them into
two registers guarantees one of them is stale.

It must name what work each certificate covers where that matters. A liability
policy excluding the work being performed is worse than an absent one, because it
was relied upon.

It is a register rather than prose, so it is a table with a schema the platform
can read: rows are records, and each row can be signed for on its own.
