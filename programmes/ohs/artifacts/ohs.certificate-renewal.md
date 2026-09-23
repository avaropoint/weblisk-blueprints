---
id: ohs.certificate-renewal
kind: procedure
title: Certificate Renewal
structure: procedure
path: procedures/certificate-renewal.md

satisfies:
  - isnetworld:ISN-SAFE-02
  - iso_45001:8.1.4

requires: [ohs.prequalification-records]

declares:
  obligation:
    id: ohs.certificate-renewal
    activity: Renew a certificate before it expires
    for:
      records: registers/prequalification-records.md
      due: 30d before expires_on
      key: reference
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/certificate-renewals.md
    escalate: {after: 7d, to: site-supervisor}
  register:
    title: Certificate Renewal Record
    note: >
      One row per certificate renewed, keyed by the reference on the certificate
      it replaces. This register is not the register of certificates — it is the
      record that somebody acted before a date, which is the thing an auditor
      asks for and the thing a monthly sweep cannot produce.
    layout: form
    review: required
    approvers: [health-safety-lead]
    columns:
      - {key: reference, label: Certificate renewed, type: relation,
         target: /registers/prequalification-records.md#records, display: reference}
      - {key: holder, label: Held by, type: text, required: true}
      - {key: chased_on, label: First asked for on, type: date}
      - {key: received_on, label: Replacement received on, type: date, required: true}
      - {key: new_expires_on, label: New expiry, type: date, required: true}
      - {key: verified_with_issuer, label: Verified with the issuer, type: bool, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Renewed, Lapsed, Contractor removed from site, Not required]}
      - {key: note, label: Note, type: longtext}
---

What this artifact must establish: that a certificate due to expire was acted on
before it expired, by whom, and with what result.

The register of certificates already knows every expiry date. What it cannot do
is produce one piece of work per certificate: a monthly sweep asks a person to
read a table and notice something, and a table that was read and misread is
indistinguishable from one that was read correctly. This obligation is
record-origin — one occurrence per certificate, due thirty days before that
certificate's own expiry date — so the work exists, is attributable, and is late
in a way the platform can see.

Thirty days because a replacement certificate is issued by somebody else. A
workers-compensation board, an insurer and a licensing body each work to their
own timetable, and an organisation that starts asking on the expiry date is
asking after it is too late to matter.

It must escalate to whoever controls site access rather than upward for its own
sake. A lapsed liability policy or clearance certificate is not an
administrative lapse; it is a contractor who must not be working. The person who
can act on that is the person who can send them home, which is why the
escalation goes to the site supervisor and not back to the inbox that has
already let thirty days pass.

It must record the outcome honestly, including the outcomes nobody wants. A
certificate that lapsed, or a contractor removed from site because it lapsed, is
evidence the programme worked — a register that can only record success is a
register that will be quietly not filled in.

It must record whether the replacement was verified WITH THE ISSUER, for the
same reason the register of certificates does: the document is not the statement
it stands for.

It is submitted as a form rather than typed into a grid, because a renewal
discharges an occurrence and an occurrence needs one attributable act. A grid
commits every keystroke, so a half-entered renewal would report a certificate as
handled before anybody said it was.
