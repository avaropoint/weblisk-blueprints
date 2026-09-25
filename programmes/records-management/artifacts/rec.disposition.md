---
id: rec.disposition
kind: procedure
title: Records Disposition
structure: procedure
path: procedures/records-disposition.md

satisfies:
  - iso_27001:A.5.33
  - iso_27001:A.7.14
  - iso_27001:A.8.10
  - pipeda:PIPEDA-5
  - fippa_mfippa:FM-07
  - quebec_law25:BS-3
  - soc2:C1.2

requires: [rec.retention-schedule]

declares:
  obligation:
    id: rec.disposition
    # Record-origin. Each class of record reaches its disposition date on its
    # own schedule; a quarterly sweep of everything would dispose of some
    # classes late and raise work for classes with nothing due.
    activity: Dispose of the records in a class whose retention period has expired
    for:
      records: registers/retention-schedule.md
      due: 30d before next_disposition_on
      key: reference
    responsible: records-manager
    applies_to: the organisation
    records: registers/disposition-records.md
    escalate: {after: 2w, to: senior-management}
    satisfies:
      - iso_27001:A.5.33
      - pipeda:PIPEDA-5
  register:
    title: Records Disposition Record
    note: >
      One row per disposal, keyed by the record class it discharges. This
      register is itself a permanent record: the evidence that a document was
      destroyed under an approved schedule rather than by somebody who wanted it
      gone is the difference between routine disposition and spoliation, and it
      is needed most in the years after the records are gone.

      `hold_checked` is required and is checked at the moment of disposal rather
      than at approval, because a hold can be imposed in between.
    layout: form
    review: required
    approvers: [records-manager, senior-management]
    approval_order: sequential
    columns:
      - {key: reference, label: Record class, type: relation, required: true,
         target: /registers/retention-schedule.md#records, display: record_class}
      - {key: disposed_on, label: Disposed on, type: date, required: true}
      - {key: period_covered, label: Records covered — period or range, type: text, required: true}
      - {key: volume, label: Volume disposed of, type: text, required: true}
      - {key: hold_checked, label: Legal hold checked immediately before disposal, type: bool, required: true}
      - {key: authorised_by, label: Authorised by, type: user, required: true}
      - {key: method, label: Method used, type: select, required: true,
         options: [Secure shredding, Certified destruction service, Secure electronic deletion,
                   Cryptographic erasure, Physical destruction of media, Transferred to archive,
                   Returned to the client]}
      - {key: carried_out_by, label: Carried out by, type: text, required: true}
      - {key: certificate, label: Certificate of destruction reference, type: text}
      - {key: backups_addressed, label: Backups and secondary copies addressed, type: select, required: true,
         options: [Deleted, Will expire with the backup cycle, Retained under hold, Not applicable]}
      - {key: next_disposition_on, label: Next disposition due for this class, type: date, required: true}
---

What this document must establish for THIS organisation: how records are
actually destroyed, by whom, with what proof, and what is checked first.

It must require the legal hold check at the moment of disposal rather than at
approval. A disposal approved in March and carried out in June, with a hold
imposed in April, destroys evidence under an authorisation that was valid when it
was given — and the record will show it was approved, which is worse than no
record.

It must name the method by medium and be specific. Paper shredded to a stated
standard; disks physically destroyed or cryptographically erased; a cloud
service's deletion function, which almost never removes the data immediately and
sometimes never removes it from backups at all.

It must address the copies. The commonest failure in disposition is not the
primary record: it is the backup, the archive, the export somebody took for a
project, the copy in a supplier's system, and the email attachment. A disposal
that addresses only the system of record has reduced the exposure by a fraction
and recorded it as complete, which is worse than doing nothing, because the
organisation now believes the information is gone.

It must produce evidence that survives the records. The disposition record is
kept permanently — it is the answer to "where is the 2019 file", and the answer
"destroyed on this date, under this class, on this authority, by this person" is
the only one that closes the question.

It must say what happens when a class cannot be disposed of on time. A system
that cannot delete selectively, a supplier who will not, a backup cycle longer
than the retention period — these are real and they are risks with owners, not
reasons to leave the row open indefinitely.

Thirty days before the date rather than on it, because a disposal usually needs a
supplier booking, an approval and a window — and a disposition that opens on the
day it is already due produces a note rather than a destruction.
