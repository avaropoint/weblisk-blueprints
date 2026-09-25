---
id: priv.casl
kind: procedure
title: Commercial Electronic Messages
structure: procedure
path: procedures/commercial-electronic-messages.md

satisfies:
  - casl:6(1)
  - casl:6(2)
  - casl:6(2)(c)
  - casl:10(1)
  - casl:10(9)
  - casl:20
  - pipeda:PIPEDA-3

requires: [priv.policy]

declares:
  obligation:
    id: priv.casl-review
    activity: Review consent records, unsubscribe handling and message content against CASL
    cadence: each quarter
    authority: CASL s. 10(1) — the person who alleges consent has the burden of proving it
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/casl-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: CASL Compliance Review Record
    note: >
      One row per review. `implied_consent_expiring` is the column that prevents
      the most common contravention: implied consent from a purchase lasts two
      years and from an enquiry six months, and a list built on it decays
      silently whether or not anybody maintains it.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: lists_reviewed, label: Lists and campaigns reviewed, type: longtext, required: true}
      - {key: addresses_total, label: Addresses on commercial lists, type: int, required: true}
      - {key: express_consent, label: Held on express consent, type: int, required: true}
      - {key: implied_consent, label: Held on implied consent, type: int, required: true}
      - {key: implied_consent_expiring, label: Implied consent expiring within the next quarter, type: int, required: true}
      - {key: no_recorded_consent, label: With no recorded consent, type: int, required: true}
      - {key: unsubscribes, label: Unsubscribe requests received, type: int, required: true}
      - {key: unsubscribes_late, label: Of those, actioned after 10 business days, type: int, required: true}
      - {key: content_compliant, label: Identification and unsubscribe present in every message, type: bool, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: which messages are
commercial electronic messages, what consent the organisation holds for each
address, and how an unsubscribe is honoured.

It must decide, in the organisation's own terms, which of its messages are in
scope. A newsletter clearly is; a renewal reminder, an invitation to a trade
show, a follow-up after a quote and a survey may all be, because the test is
whether it would be reasonable to conclude that one of the purposes is to
encourage participation in a commercial activity. A transactional message about
an order the customer placed is treated differently, and the distinction has to
be written down before somebody is deciding it at send time.

It must record consent with its provenance: what form it took, when it was
given, by what means, and what the person was shown at the time. The burden of
proving consent is on the sender, which makes the record the entire defence — an
organisation that can produce a list but not its origins has no consent it can
demonstrate.

It must track implied consent as something that expires. Two years from a
purchase or contract, six months from an enquiry, and the conspicuous-publication
route which only supports messages relevant to the person's business role. A
list bought from a third party supports neither.

It must ensure every message carries the sender's identity, a mailing address, a
working contact method valid for sixty days, and an unsubscribe mechanism that
can be performed with one response and is honoured within ten business days
without further action by the recipient. A confirmation step the recipient must
complete is a contravention, not a courtesy.

It must connect to the due diligence defence. Administrative monetary penalties
reach ten million dollars for an organisation, directors and officers can be
personally liable, and the only defence is that due diligence was exercised —
which is established by a documented programme with training, consent records,
complaint handling and review, and by nothing else. That is what this procedure
and the register above are for.
