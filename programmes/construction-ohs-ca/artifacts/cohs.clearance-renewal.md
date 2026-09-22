---
id: cohs.clearance-renewal
kind: procedure
title: Clearance Certificate Renewal
structure: procedure
path: procedures/construction/clearance-renewal.md

satisfies:
  - isnetworld:ISN-SAFE-02
  - cor_2020:COR-15

requires: [cohs.clearance-certificates]

declares:
  obligation:
    id: cohs.clearance-renewal
    activity: Renew a clearance certificate before it expires, or stop the contractor
    for:
      records: registers/construction/clearance-certificates.md
      due: 14d before expires_on
      key: reference
    authority: Workplace Safety and Insurance Act, 1997 ss. 141.1, 141.2 and the board's clearance policy — a clearance is valid for up to ninety days and must be renewed for the whole duration of the contract. No notice period is prescribed
    interval_basis: chosen
    responsible: procurement-lead
    applies_to: the organisation
    records: registers/construction/clearance-renewals.md
    escalate: {after: 1w, to: project-manager}
  register:
    title: Clearance Renewal Record
    note: >
      One row per clearance acted on, keyed by the number of the certificate it
      replaces. The register of clearances says what is held; this says that
      somebody acted before a date and what happened when the answer came back
      wrong. "Contractor stopped" is an outcome and not a failure of the process —
      it is the process working.
    layout: form
    review: required
    approvers: [procurement-lead]
    columns:
      - {key: reference, label: Clearance renewed, type: relation, required: true,
         target: /registers/construction/clearance-certificates.md#records, display: reference}
      - {key: contractor, label: Contractor, type: text, required: true}
      - {key: requested_on, label: Requested on, type: date, required: true}
      - {key: received_on, label: Replacement received on, type: date}
      - {key: new_reference, label: New clearance number, type: text}
      - {key: new_expires_on, label: New expiry, type: date}
      - {key: verified_with_board, label: Verified with the board, type: bool, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Renewed, Refused by the board, Contractor stopped, Contract ended,
                   Contractor removed from site, Not required]}
      - {key: work_continued, label: Work continued while the clearance was not valid, type: bool, required: true}
      - {key: note, label: Note, type: longtext}
---

What this artifact must establish: that a clearance about to expire was acted on
before it expired, by whom, and what happened to the contractor's work if it was
not renewed.

The register of clearances already knows every expiry date. What a register cannot
do is produce one piece of work per certificate. A monthly sweep asks a person to
read a table and notice something, and a table that was read and misread is
indistinguishable from one read correctly. This obligation raises one occurrence
per certificate, due against that certificate's own expiry, so the work exists, is
attributable, and is visibly late.

**Fourteen days is this organisation's choice.** The ninety-day validity is the
board's; no notice period is prescribed. Fourteen days is chosen because a
clearance is issued by somebody else, and because a contractor whose account is in
arrears will not be able to produce one at all — which is information the
organisation wants two weeks before the current one lapses rather than on the
morning it does.

**A refused clearance is the important outcome, not an edge case.** It means the
contractor's account is not in good standing, which is exactly the circumstance
the liability provision exists for, and it is the moment the organisation's
exposure to the labour portion of that contract becomes real. The procedure must
say who decides to stop the work, how quickly, and who tells the contractor.

`work_continued` is a required boolean because the honest answer is sometimes yes
and a register that cannot record it will simply not be filled in. A gap
acknowledged is a risk somebody can price; a gap hidden is one that surfaces in
an assessment years later.

It escalates to the position that controls site access, for the same reason the
credential renewals do: the person chasing a certificate cannot send anybody home.

It is submitted as a form rather than typed into a grid, because a renewal
discharges an occurrence and an occurrence needs one attributable act. A grid
commits every keystroke, so a half-entered renewal would report a contractor as
cleared before anybody said so.
