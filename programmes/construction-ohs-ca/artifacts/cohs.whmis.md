---
id: cohs.whmis
kind: procedure
title: WHMIS and Hazardous Products
structure: procedure
path: procedures/construction/whmis.md

satisfies:
  - construction_safety_ca:CSA-TR-2
  - cor_2020:COR-16

requires: [cohs.site-orientation]

declares:
  obligation:
    id: cohs.whmis-review
    activity: Review of the WHMIS training and of each worker's familiarity with it, in consultation with the committee or representative
    cadence: each year
    authority: OHSA s. 42(3) — "at least annually", and s. 42(4) more often on the committee's advice or on a change in circumstances
    interval_basis: required
    responsible: health-safety-lead
    applies_to: the organisation
    records: registers/construction/whmis-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: WHMIS Review Record
    note: >
      One row per review. `change_in_circumstances` is a column because the real
      retraining trigger is not the calendar: a new product, a reformulated
      product, a changed safety data sheet or a changed label is what makes
      training out of date, and an annual review that does not ask what changed
      has reviewed nothing.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: consulted, label: Committee or representative consulted, type: bool, required: true}
      - {key: workers_covered, label: Workers covered, type: int, required: true}
      - {key: familiarity_assessed_how, label: How familiarity was assessed, type: longtext, required: true}
      - {key: change_in_circumstances, label: Changes in circumstances since the last review, type: longtext, required: true}
      - {key: retraining_required, label: Retraining required, type: bool, required: true}
      - {key: retraining_for, label: For whom, and by when, type: longtext}
      - {key: inventory_reconciled, label: Product inventory reconciled to the data sheets held, type: bool, required: true}
---

What this document must establish for THIS organisation: which hazardous products
are on its sites, how a worker finds out what is in one, and what the annual
review actually consists of.

**"WHMIS expires annually" is a misstatement of a review duty and the document
must not repeat it.** Ontario law sets no expiry on WHMIS training. What it
requires is that the training programme **and each worker's familiarity with it**
be reviewed at least annually, in consultation with the committee or the
representative, and more often on the committee's advice or **on a change in
circumstances**. The annual interval is the law's; the thing it applies to is a
review, not a re-sitting.

It must name the change-in-circumstances trigger as the real one, because it is.
A new product on site, a reformulated product under the same trade name, a
revised safety data sheet or a changed label is what makes a worker's knowledge
wrong — and none of those arrives on an anniversary. The industry-wide
realignment of hazardous products classification to the current international
system, whose transition ended in December 2025, is precisely such a change:
labels and data sheets across whole product ranges now read differently, and a
worker trained before it is trained on a classification scheme that no longer
matches what is printed on the drum in front of them.

It must be explicit that there is **no regulatory requirement to keep WHMIS
training records** in Ontario — and then require them anyway, with the reason
stated as the organisation's own. Nothing else can answer "was this worker
trained before they handled it", which is the question that is actually asked.

It must cover the site realities the generic guidance skips. On a construction
project the products arrive with sub-trades, the inventory changes weekly, and
the data sheets that matter are for the products present today rather than for
the list assembled at mobilisation. The document must say who maintains the
inventory, where the data sheets are available on site, and what happens when a
product arrives without one.

It must cover supplier labels lost in decanting, workplace labels on transfer
containers, and the special case of a product transferred by a sub-trade into an
unlabelled vessel — which is the most common finding in this area and the one
most often treated as trivial.

Designated substances and asbestos are **not** WHMIS matters and have their own
artifacts. A programme that files silica and asbestos under WHMIS has filed a
control programme under a labelling regime.
