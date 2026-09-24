---
id: cohs.wsib-account
kind: procedure
title: Workers' Compensation Registration and Reporting
structure: procedure
path: procedures/workers-compensation-account.md

satisfies:
  - wsia_ontario:12.2
  - wsia_ontario:75
  - wsia_ontario:78
  - wsia_ontario:80
  - isnetworld:ISN-SAFE-02
  - cor_2020:COR-19

requires: [cohs.policy]

declares:
  obligation:
    id: cohs.wsib-reconciliation
    activity: Annual reconciliation of insurable earnings reported to the board against actual payroll
    cadence: each year
    authority: Workplace Safety and Insurance Act, 1997 and the board's reporting requirements — the annual reconciliation is due 31 March
    interval_basis: required
    responsible: payroll-administrator
    applies_to: the organisation
    records: registers/workers-compensation-reconciliations.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Workers' Compensation Reconciliation Record
    note: >
      One row per reconciliation per account. An organisation with more than one
      account has more than one row, and that is deliberate: classification,
      rates and several prequalification schemes operate per account, and a
      consolidated figure hides the account that is drifting.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reconciled_on, label: Reconciled on, type: date, required: true}
      - {key: account, label: Account number, type: text, required: true}
      - {key: period, label: Period, type: text, required: true}
      - {key: classification, label: Classification and subclass, type: text, required: true}
      - {key: earnings_reported, label: Insurable earnings reported, type: currency, required: true}
      - {key: earnings_actual, label: Insurable earnings actual, type: currency, required: true}
      - {key: variance, label: Variance, type: currency, required: true}
      - {key: adjustment_filed_on, label: Adjustment filed on, type: date}
      - {key: reporting_frequency, label: Reporting frequency, type: select, required: true,
         options: [Monthly, Quarterly, Annually]}
      - {key: all_periods_filed, label: Every period in the year filed, including nil periods, type: bool, required: true}
      - {key: exempt_officers, label: Exempt partners or executive officers on file, type: longtext}
      - {key: reconciled_by, label: Reconciled by, type: user, required: true}
---

What this document must establish for THIS organisation: which accounts it holds,
who must be covered, when earnings are reported, and who checks that the picture
the board holds matches the payroll.

**Construction coverage is different and the difference is the most expensive
thing in this artifact.** Outside construction, an independent operator, sole
proprietor, partner or executive officer is generally not automatically covered.
In construction they are **deemed workers**, and **before any non-exempt
construction work commences the person or entity must register as a deemed
employer**. An organisation that engages an unregistered independent operator has
not saved a premium; it has acquired one.

There are exactly two exemptions and the document must state them narrowly.
**Exempt home renovation work** is construction on an existing private residence
occupied by the person who **directly retains** the contractor, or by a member of
their family — and it expressly does **not** extend to subcontractors retained by
that contractor, which is where the belief that "residential is exempt" comes
from and where it fails. **One partner or executive officer** who **does no
construction work** may be exempted on the prescribed form, with periodic site
visits permitted; the exemption takes effect **on the date the board receives the
signed form** and is not retroactive, and a change must be notified within ten
days. "We filed it eventually" is not an exemption for the period before it
arrived.

It must state the reporting rhythm by band — monthly above the higher earnings
threshold, quarterly in the middle band, annually below the lower one — and must
say that **a return is due even when payroll is nil**. The **annual reconciliation
is due 31 March** and the late penalty accrues monthly to a cap. An estimate
exceeded must be updated within ten days.

It must record the **classification** and say who owns it. Classification drives
the class rate, and the class rate drives everything else; an organisation
misclassified across two subclasses is paying the wrong premium in a way nobody
notices until an audit covering the current year and the two before it.

It must **not** describe the superseded experience-rating programmes. The
construction experience-rating programme and its general-industry siblings all
ended between 2018 and 2021, there are **no rebates or surcharges under the
current model**, and rate groups have been replaced by a classification based on
industry codes. A safety programme that promises a rebate under a programme that
no longer exists is promising something it cannot deliver, and it is a surprisingly
common paragraph in construction safety manuals.

The current mechanism is different in kind: an individual risk-adjusted rate
moving within bands, with a limit on how far it may move in a year and a faster
path for sustained poor performance, over a multi-year experience window. What
that means operationally is that claims cost affects premium slowly and
persistently rather than as an annual settlement, and the document should say so
plainly because it changes what "fixing it this year" is worth.

It should also describe the current voluntary health and safety incentive
programme accurately: topic-based action plans with a rebate per completed topic,
capped against prior-year premiums, and mutually exclusive with the accredited
employer programme. It carries **no recognition of, or credit for, an external
certificate of recognition**, and a fatality in the qualifying window disqualifies
the plan.
