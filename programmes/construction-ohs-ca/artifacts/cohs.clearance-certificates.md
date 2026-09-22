---
id: cohs.clearance-certificates
kind: register
title: Register of Clearance Certificates
structure: standard
path: registers/construction/clearance-certificates.md

# A register carries no `satisfies:`.
#
# It is the evidence that work happened, not the document that answers a
# control — and the relation vocabulary says so structurally: `implements`
# onto a control may be asserted by a blueprint, a policy or a procedure,
# and by nothing else. A register citing a control could never be recorded
# as answering it, so it sat at `present_uncited` permanently and capped the
# tier's readiness at a number no amount of work could move.
#
# The citation belongs on the procedure that declares this register, which
# is where the organisation states what it does; this file is where it
# records having done it.

requires: [cohs.wsib-account]

register:
  title: Register of Clearance Certificates
  note: >
    One row per clearance held for one contractor for one contract. Not one per
    contractor: a clearance is valid for a period and for a relationship, and an
    organisation that keeps the latest certificate per company cannot show it held
    a valid one for the WHOLE duration of a contract, which is the actual duty.
    `covers_from` and `covers_to` are what make that answerable.
  columns:
    - {key: reference, label: Clearance number, type: text, required: true}
    - {key: contractor, label: Contractor, type: text, required: true}
    - {key: contractor_account, label: Their account number, type: text, required: true}
    - {key: contract, label: Contract or purchase order, type: text, required: true}
    - {key: project, label: Project, type: relation,
       target: /registers/construction/projects.md#records, display: project_id}
    - {key: directly_retained, label: Directly retained by us, type: bool, required: true}
    - {key: obtained_on, label: Obtained on, type: date, required: true}
    - {key: covers_from, label: Covers from, type: date, required: true}
    - {key: expires_on, label: Expires on, type: date, required: true}
    - {key: contract_ends, label: Contract expected to end, type: date, required: true}
    - {key: labour_portion, label: Labour portion of the contract, type: currency}
    - {key: status, label: Status, type: select, required: true,
       options: [Valid, Expiring, Expired, Not obtained, Contractor stopped]}
    - {key: evidence, label: Certificate, type: attachment}
---

What this artifact must establish: that for every contractor this organisation
directly retained, a valid clearance was held for the whole time they were
working.

**The exposure is specific and it is not a fine.** A principal who permits work
without a valid clearance may be held liable for the contractor's workers'
compensation obligations **up to the value of the labour portion of the
contract**. That is why `labour_portion` is a column: it is the size of the risk
being carried on each row, and it is the number that turns an administrative
lapse into a decision somebody would have made differently.

The duties are four and they are sequential. Obtain a clearance **before**
directly retaining the contractor. Do not permit work without a valid one.
**Renew it for the whole duration** of the contract. Retain the records. The
third is the one that fails, because a clearance is valid for a limited period
and most contracts outlive it — which is why this register is keyed to a contract
and carries both the clearance's expiry and the contract's expected end. When the
second date is later than the first, somebody has work to do.

Clearances are valid for **up to ninety calendar days** and most expire on fixed
quarterly dates rather than ninety days from issue, which means a certificate
obtained late in a quarter is valid for far less than ninety days. An organisation
that assumes ninety days from the date it received the document will be out of
clearance without anything having changed.

`directly_retained` matters because the duty follows the direct relationship. A
sub-subcontractor is the subcontractor's obligation, not this organisation's —
and an organisation that collects clearances for everybody on site is doing more
than it has to while possibly still missing the one it owed.

It must hold the certificate and not a note that one was seen. The certificate is
also verifiable with the board, and where verification was done the register
should say so — the document is not the statement it stands for.

**No retention period is declared here.** The duty to retain records is real and
no period is prescribed in the material this pack was written from. The
organisation should set one at or beyond the limitation period for the liability
it is protecting itself against, and record what it chose and why. An invented
number in this field would be exactly the kind of confident wrong answer this
register exists to prevent.
