---
id: capay.substantial-performance
kind: procedure
title: Certification, Declaration and Publication of Substantial Performance
structure: procedure
path: procedures/substantial-performance-certification.md

satisfies:
  - construction_act_ontario:32
  - construction_act_ontario:33
  - construction_act_ontario:31

requires: [capay.holdback-account]

declares:
  obligation:
    id: capay.substantial-performance-publication
    activity: Certify or declare substantial performance, give the copies the Act requires, and publish
    for:
      records: registers/holdback-account.md
      due: 7d after substantially_performed_on
      key: holdback_id
    authority: >
      Construction Act ss. 31, 32 and 33. The Act prescribes the steps — who
      certifies or declares, who receives a copy, and that the contractor
      publishes — and it prescribes periods for them. The seven days here is this
      organisation's own deadline, set inside them
    interval_basis: chosen
    responsible: contract-administrator
    applies_to: the organisation
    records: registers/substantial-performance-certifications.md
    escalate: {after: 1w, to: senior-management}
  register:
    title: Substantial Performance Certification Record
    note: >
      One row per contract or subcontract certified, declared or certified
      complete. The point of the row is the gap between `certified_on` and
      `published_on`: until publication the clock in s. 31 has not started, every
      lien is alive, and the holdback cannot be released — while everybody
      involved believes the opposite, because the certificate exists.
    layout: form
    review: required
    approvers: [contract-administrator, senior-management]
    approval_order: sequential
    columns:
      - {key: holdback_id, label: Holdback, type: relation, required: true,
         target: /registers/holdback-account.md#records, display: holdback_id}
      - {key: contract, label: Contract or subcontract, type: text, required: true}
      - {key: instrument, label: What was issued, type: select, required: true,
         options: [Certificate of substantial performance by the payment certifier,
                   Declaration of substantial performance by the owner and contractor,
                   Certificate of completion of a subcontract]}
      - {key: applied_for_on, label: Applied for on, type: date}
      - {key: certified_on, label: Certified or declared on, type: date, required: true}
      - {key: copy_given_on, label: Copy given on, type: date, required: true}
      - {key: published_on, label: Published on, type: date}
      - {key: publication_reference, label: Where it was published, type: text}
      - {key: published_by_us, label: Published by us, type: bool, required: true}
      - {key: lien_expiry_on, label: Liens expire on, type: date}
      - {key: holdback_release_due_on, label: Holdback falls due on, type: date}
      - {key: note, label: Note, type: longtext}
---

What this artifact must establish: who applies for certification, who issues it,
who receives a copy, who publishes it, and what the organisation does when the
party who is supposed to publish does not.

**This is the step the whole programme turns on and the one most often treated
as paperwork.** Substantial performance is what starts the sixty-day lien
preservation period; publication is what starts it running. Until publication,
liens remain alive, the basic holdback cannot be safely released, and the
finishing holdback has not begun its own course. The register is therefore
designed around a single comparison — `certified_on` against `published_on` —
because a certificate that was issued and never published is the most expensive
silent state in this Act. Nothing looks wrong. The clock simply is not running.

**`published_by_us` is a boolean because the duty can migrate.** Publication is
the contractor's in the first instance, and where the contractor does not
publish, another person may. That means the organisation's exposure depends on
which side of the contract it is on: as a contractor it must publish; as an owner
or a payer it must notice that nobody has, and be able to act. A register that
recorded only "published: yes" would lose the distinction between having done it
and having been rescued by somebody else doing it.

**Certification of completion of a subcontract is in the same register on
purpose.** A subcontract certified complete runs that sub-trade's lien period
against its own work rather than against the improvement as a whole, which is
the mechanism by which an early trade — excavation, foundations — can be paid out
long before the project is substantially performed. It is the single most useful
provision in the Act for a general contractor's relationship with the trades it
finishes with first, and it is very widely unused. Keeping it here, as one of
three values of `instrument`, is what makes it visible at the moment somebody is
thinking about a release.

**An empty `substantially_performed_on` raises no work, and that is deliberate.**
This obligation triggers off the holdback account, one occurrence per row, due
seven days after the date that row carries. A contract that has not been
substantially performed carries no date and produces no occurrence — which is
correct, and is also why it produces no signal at all. The monthly
reconciliation asks, out loud, which rows are silent because nothing is due and
which are silent because nobody has filled the date in.

**The interval basis is `chosen` and the authority is cited anyway.** The Act
prescribes its own periods for certification, for delivering the copy and for
publication. Seven days is this organisation's internal deadline, set inside
them, and the distinction matters: a product that rendered the two identically
would eventually tell an auditor that a preference is a requirement.
