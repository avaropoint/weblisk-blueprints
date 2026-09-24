---
id: construction_payment_ca
title: Construction Payment, Holdback and Lien Programme (Canada — Ontario)
order: 25
domains:
  - trade_regulatory
  - records_management
conforms_to:
  - construction_act_ontario
  - wsia_ontario

tiers:
  - id: statutory
    title: What the Act requires of anybody holding a holdback
    rationale: >
      Below this line the organisation is holding somebody else's money without a
      record of whose it is, and the people who control it are personally liable
      for the difference. Everything here is a duty the day the first subcontract
      is signed: retain the ten per cent, know the date it falls due, publish the
      certificate that starts the clock, and pay on the day the Act says.
      The two certificate registers sit at this tier and not a later one, and the
      reason is the dependency rather than the law: the release obligation here
      cannot be discharged without them, and a tier that deferred them would hand
      somebody a release procedure whose evidence was in next year's plan.
  - id: assured
    title: The release is a decision, not a payment run
    requires: statutory
    rationale: >
      The Act tells this organisation when to pay. Nothing in it tells it that the
      sub-trade it is paying is still insured, still cleared with the board, or
      still solvent on the day the money moves — and those are the facts that
      decide whether the payment can ever be recovered. This tier is where the
      documentary state is kept current rather than merely recorded, and where
      the whole account is swept monthly so that a contract nobody entered is
      visible as an absence rather than as silence.

artifacts:
  # ── statutory: the money, the clock, and the day it falls due ──────────────
  - { id: capay.policy, tier: statutory }
  - { id: capay.holdback-account, tier: statutory }
  - { id: capay.substantial-performance, tier: statutory }
  - { id: capay.holdback-release, tier: statutory }
  - { id: capay.insurance-certificates, tier: statutory }
  - { id: cohs.clearance-certificates, tier: statutory }
  # ── assured: the documents are current, and the account is swept ───────────
  - { id: capay.insurance-renewal, tier: assured }
  - { id: capay.holdback-reconciliation, tier: assured }
---

Seven artifacts for a contractor, subcontractor or owner working on improvements
to land in Ontario, covering the statute that is for most construction companies
the largest legal exposure that is not a safety matter — and the one an
occupational health and safety programme never touches.

It is deliberately a **sibling** of the construction health and safety programme
rather than part of it. They answer to different authorities, they are read by
different people, and an organisation may well adopt one without the other. What
they share is a subject: the sub-trade. That is why this programme places
`cohs.clearance-certificates` — an artifact the health and safety pack defines —
in its own first tier rather than declaring a second register of the same
certificates. An organisation running both programmes keeps one register of
clearances; an organisation running only this one is told the artifact is
required and is not handed a duplicate.

## The argument this programme exists to make

A holdback is documentation expressed as money.

Every other register in a construction programme records a document: a clearance
certificate, a certificate of insurance, a training card, a sign-off. Chasing
them costs real money and produces nothing anybody outside the office can see,
which is why it is the first thing that slips. The holdback is the point at
which all of it becomes a number — ten per cent of a contract price, on a date
somebody else can enforce — and the point at which the organisation's ability to
do anything about a missing document ends. Once the ten per cent is paid, the
leverage is gone and so is most of the recovery.

So the connection this programme draws is the one that makes the documentary
work legible to the people who fund it: **this sub-trade's documents are current**
therefore **this sub-trade's holdback can be released**, and where they are not,
somebody with a name decided to pay anyway, on the record, on the day.

## What it must not be read as saying

**The documentary gate is not a right to withhold statutory holdback.** The Act
requires the holdback to be paid once the liens it secures have expired or been
provided for, and permits withholding only on the grounds and by the notices it
prescribes — a preserved lien, a notice of non-payment in the prescribed form and
time. An expired clearance certificate is not among them, and a programme that
implied otherwise would be instructing somebody to breach the Act and to start
interest running against their own company.

What the documentary state is, is a condition precedent under most subcontracts
and a liability that survives the payment. `capay.holdback-release` therefore
does not block anything. It forces the decision to be attributable, and it makes
"released with a documentary gap accepted" a first-class, approved, named
outcome rather than an omission.

## The three clocks, and which of them is anybody's choice

The pack beside this one states the rule and it holds here: a product that
renders a chosen interval and a legal one identically eventually tells an
auditor that a preference is a requirement. So every obligation declares
`interval_basis`.

- **The dates the Act sets** are the ones that matter and none of them is an
  interval this platform schedules: the expiry of liens sixty days from
  publication, perfection ninety days after that, the release following each
  anniversary of the date the contract was entered into. They are recorded as
  **dates on a row** — `lien_expiry_on`, `release_due_on` — and every obligation
  here triggers off them.
- **The warnings before those dates** are entirely this organisation's: fourteen
  days before a holdback falls due, thirty days before a certificate of insurance
  expires, seven days after substantial performance to certify and publish. Each
  is `chosen`, each cites the authority for the *activity* beside it, and each
  artifact's brief says in words why that number and not another.
- **The monthly reconciliation** is `chosen` too. The Act requires the trust
  records and requires the state of accounts to be given on demand; it sets no
  interval for either.

## Where the silences are

Two of the three record-origin obligations here trigger off a **date column that
is empty until something happens** — `substantially_performed_on`,
`release_due_on`. An empty date raises no occurrence, which is correct and is
also completely silent. A contract that was never entered in the register at all
is silent in the same way, and looks identical.

That is why the chain terminates in a cadence rather than in another trigger.
`capay.holdback-reconciliation` sweeps the whole account monthly and reports four
counts that no trigger can produce: contracts certified and not published,
counterparties with no current clearance, counterparties with no current
insurance, and — the one that governs the value of the other three —
counterparties whose documents were **not checked at all**.

A hundred per cent current because everything was checked and a hundred per cent
current because nothing was are the same number and opposite facts. Every figure
this programme produces is reported beside the count of what was not looked at.

## Positions this programme names

`finance-lead`, `contract-administrator`, `project-manager` and
`senior-management`. Two of those will be new to an organisation that has only
run the health and safety programme, and a position with no holder means an
approval with nowhere to go and an escalation into silence. They are created
once, in the product, and they are the first thing to check after adopting this.

## What this programme does not cover

Prompt payment and adjudication are cited by the policy and are **not**
operationalised here. The proper-invoice clock, the fourteen-day notice of
non-payment and the thirty-day adjudicator's determination are real, they are
severe, and they turn on documents and deadlines this pack could model the same
way — but they run per invoice rather than per contract, and an invoice register
is a different subject with a different volume. They are named here so that an
organisation reading a clean screen does not conclude that the Act has been
answered in full.
