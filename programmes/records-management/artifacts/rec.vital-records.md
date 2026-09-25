---
id: rec.vital-records
kind: standard
title: Vital Records
structure: standard
path: standards/vital-records.md

satisfies:
  - iso_27001:A.5.33
  - iso_27001:A.5.29
  - iso_22301:8.2.2
  - iso_9001:7.5

requires: [rec.retention-schedule]

declares:
  obligation:
    id: rec.vital-records-check
    activity: Verify that vital records are identified, protected and recoverable
    cadence: each year
    interval_basis: chosen
    responsible: records-manager
    applies_to: the organisation
    records: registers/vital-records-checks.md
  register:
    title: Vital Records Verification Record
    note: >
      One row per verification. `recovered_in_test` is a separate column from
      `backed_up` for the same reason the restore test exists: a record that is
      backed up and has never been retrieved is a record the organisation
      believes it has.
    layout: form
    review: required
    approvers: [records-manager]
    columns:
      - {key: verified_on, label: Verified on, type: date, required: true}
      - {key: verified_by, label: Verified by, type: user, required: true}
      - {key: classes_identified, label: Vital record classes identified, type: int, required: true}
      - {key: originals_located, label: Originals located where they should be, type: int, required: true}
      - {key: backed_up, label: Classes with a protected copy, type: int, required: true}
      - {key: recovered_in_test, label: Classes actually retrieved in a test, type: int, required: true}
      - {key: offsite, label: Classes with a copy away from the primary site, type: int, required: true}
      - {key: gaps, label: Gaps found, type: longtext, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: which records the
business could not be reconstructed without, and what protects them.

It must name them specifically. Incorporation documents, the minute book and
share register, title and lease documents, insurance policies, signed customer
and supplier contracts, intellectual property registrations, licences and
permits, the accounting records, and the security credentials and recovery keys
without which nothing else can be reached. The list is short and almost every
organisation has never written it down.

It must say where the original is and where the protected copy is, and require
them to be in different places. A fire-safe in the office holding the only copy
of everything is a single point of failure with a certificate on it.

It must include the records held by others — the lawyer with the minute book,
the accountant with the ledgers, the registrar with the trade marks — and record
how to obtain them. A dependency on a third party is fine when it is known and
catastrophic when it is discovered.

It must connect to the continuity plan rather than duplicating it. The business
impact analysis says which activities have to resume; this standard says which
records those activities cannot resume without, and it is the part most
continuity plans assume rather than check.

It must require the copies to be retrieved rather than merely maintained. A
vital record held in a format nothing current can open — a 2009 accounting
package, an encrypted archive whose key holder has left — is a record the
organisation does not actually have.
