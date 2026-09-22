---
id: cohs.credential-register
kind: register
title: Register of Statutory Credentials and Training
structure: standard
path: registers/construction/statutory-credentials.md

satisfies:
  - iso_45001:7.2
  - isnetworld:ISN-SAFE-04

requires: [cohs.policy]

register:
  title: Register of Statutory Credentials and Training
  note: >
    One row per credential held by one person. `interval_source` is the most
    important column in this programme and it is required: it says WHOSE clock
    the expiry date is. A training provider's card date recorded in the same
    field as a statutory validity period turns a vendor's commercial policy into
    a legal requirement, and every downstream number inherits the error.
    `expires_on` is deliberately optional — most construction training in Ontario
    has no expiry at all, and recording an invented date is worse than recording
    none.
  columns:
    - {key: reference, label: Certificate or card number, type: text, required: true}
    - {key: person, label: Person, type: user, required: true}
    - {key: credential, label: Credential, type: text, required: true}
    - {key: issuer, label: Issued by, type: text, required: true}
    - {key: issued_on, label: Issued on, type: date, required: true}
    - {key: expires_on, label: Expires on, type: date}
    - {key: interval_source, label: Who sets the expiry, type: select, required: true,
       options: ["Set in law", "Set by a standard", "Set by the training provider",
                 "Convention — not legally set", "No expiry"]}
    - {key: authority, label: Authority for the interval, type: text}
    - {key: consequence, label: Consequence of lapse, type: select, required: true,
       options: [The work becomes unlawful, A contravention but nothing becomes invalid,
                 Contractual or prequalification only, None]}
    - {key: permits, label: Work it permits, type: longtext, required: true}
    - {key: evidence, label: Evidence seen, type: attachment}
    - {key: verified_with_issuer_on, label: Verified with the issuer on, type: date}
---

What this artifact must establish: which dated credentials each person actually
holds, who issued each one, when it stops being valid, and — the question almost
every training matrix gets wrong — **who decided that date**.

Ontario construction has roughly eleven legally-set recurring training clocks.
Almost everything else sold as an expiry is a training provider's card policy or
an industry convention. A compliance product that asserts a legal expiry where
none exists is wrong in the most damaging direction: it manufactures
non-compliance, it spends money on refreshers nobody required, and it teaches the
organisation to distrust its own register. `interval_source` exists so the two
can never share a field.

The clocks that **are** set in law include: Working at Heights, valid three years
from successful completion; a Transportation of Dangerous Goods training
certificate, thirty-six months for road, rail and vessel and twenty-four for air;
a propane Record of Training, three years; suspended access training for both
users and installers, at least every three years; joint health and safety
committee certification refresher, three years; and — from 1 January 2027 —
elevating work platform operator training, five years.

The ones that are **not** include: worker and supervisor health and safety
awareness training, which has no expiry and no refresher anywhere in the
regulation; WHMIS, which has no expiry in Ontario law and an annual **review**
duty that is a different thing; fall protection system training under s. 26.2;
traffic control, for which no programme, certificate or interval is prescribed at
all; lift truck operation, for which no training section exists in the
construction regulation; and confined space training on a project, for which the
annual review in the confined spaces regulation is expressly disapplied. A first
aid certificate is a genuine case of a required credential whose three-year
period comes from the certifying programme rather than from the regulation's
text, and it should be recorded that way.

`consequence` is a separate column from `interval_source` because being late is
not one thing. A lapsed Working at Heights certificate makes the work unlawful:
the worker must stop. An overdue committee meeting is a contravention and nothing
becomes invalid. A lapsed prequalification card is a commercial problem. A single
red cell that cannot tell those apart produces either panic or indifference, and
over time it produces both.

Every row must carry the issuer's own reference, because that is what the issuer
asks for when a credential is verified or replaced, and it is what makes a row
about one card rather than about a person in general.

It must hold the evidence and not a claim about it. "Card seen" without the card
is the assertion an auditor will not accept and the one a sub-trade is most
likely to have stretched.

**No single retention period is declared on this register, because no single
authority sets one.** The periods that reach these records are different rules
with different clocks: two years after a dangerous goods certificate expires;
proof producible to a departed worker who asks within six months; and, from
1 January 2027, proof producible to a departed worker within three years of the
training being delivered. The organisation should set its own period at or above
the longest of those and record which rule it is implementing, rather than
inherit a number from this pack that is right for one credential and wrong for
the rest.
