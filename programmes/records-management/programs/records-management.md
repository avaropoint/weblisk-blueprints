---
id: records-management
title: Records and Retention
order: 60
domains: [records_management, data_protection, compliance_audit, governance, business_continuity]
conforms_to: [iso_27001, iso_9001, pipeda, fippa_mfippa, iso_22301]

tiers:
  - id: essential
    title: Know what is kept and for how long
    rationale: >
      A stated rule, a schedule with an authority against every period, and a
      way to stop destruction when a claim is anticipated. Below this line an
      organisation is exposed in both directions at once: it cannot show that a
      record was destroyed properly, and it cannot show that one it no longer
      has was destroyed at all.
  - id: conformant
    title: The schedule is executed
    requires: essential
    rationale: >
      Disposition actually happens, on the class's own date, with the legal hold
      checked at the moment of disposal and a record that outlives the records.
      This is the tier at which keeping everything forever stops being the
      organisation's de facto policy.
  - id: certifiable
    title: Checked by somebody else
    requires: conformant
    rationale: >
      The estate is sampled rather than the schedule re-read, vital records are
      retrieved rather than assumed, and both failure modes — kept too long and
      destroyed too early — are counted.

artifacts:
  # ── essential ──────────────────────────────────────────────────────────────
  - {id: rec.policy, tier: essential}
  - {id: rec.retention-schedule, tier: essential}
  - {id: rec.legal-holds, tier: essential}
  - {id: rec.legal-hold, tier: essential}
  # ── conformant ─────────────────────────────────────────────────────────────
  - {id: rec.disposition, tier: conformant}
  - {id: rec.classification, tier: conformant}
  # ── certifiable ────────────────────────────────────────────────────────────
  - {id: rec.vital-records, tier: certifiable}
  - {id: rec.audit, tier: certifiable}
---

The programme every other programme's evidence depends on, and the one most
organisations have never written down.

**Ontario has no general private-sector records retention statute**, and that
absence is the reason this programme is built around a register rather than a
document. There is no single period to cite, so the schedule holds a dozen
authorities at once: the Employment Standards Act for employment records — three
years, five for vacation records; the Income Tax Act and Excise Tax Act for books
of account; the Occupational Health and Safety Act and its regulations for
exposure, training and committee records; the Workplace Safety and Insurance Act
for claim records; PIPEDA for personal information that is no longer needed for
the purpose it was collected for; the Limitations Act for the period in which a
claim can still be brought; and the organisation's own contracts, which
frequently require longer than any statute. An organisation that sets one
company-wide period has chosen a number that is too short for some classes and
too long for all the rest.

**The schedule has an `authority` column because a period without a citation is
a habit.** That single column is what makes the difference between a disposal an
organisation can defend to a court, a regulator or a client, and one it merely
decided on — and the annual review counts the classes that lack one, because the
gap is invisible in a table where every row looks equally official.

**Two obligations are record-origin, and both are due before their date rather
than on it.** A class of records is disposed of thirty days before its
disposition date, because a disposal needs an approval, a supplier and a window.
A legal hold is reviewed fourteen days before its review date, because that
review usually needs a conversation with counsel. An obligation that opens on the
day it is already due produces a note rather than the act.

**The legal hold is what makes automated disposition safe.** A retention schedule
is, read plainly, a standing instruction to destroy things, and the only thing
standing between that and destroying the evidence in a live matter is a register
somebody checks at the moment of disposal rather than at approval. That is why
`hold_checked` is a required column on the disposition record and why the hold
register carries a boolean for whether automated deletion was actually suspended
— notifying people stops deliberate deletion and does nothing about the mailbox
policy.

**It is placed into four other programmes rather than restating them.** The
security, privacy, employment, health-privacy and public-sector programmes each
need retention decided and disposal recorded, and each places
`rec.retention-schedule` — and in two cases `rec.disposition` — into its own map.
One schedule, cited five times, is the only arrangement in which a change to a
keeping period reaches every programme that depends on it.
