---
id: cohs.return-to-work
kind: procedure
title: Return to Work and Re-employment in Construction
structure: procedure
path: procedures/construction/return-to-work.md

satisfies:
  - cor_2020:COR-19

requires: [cohs.wsib-account]

declares:
  obligation:
    id: cohs.return-to-work-review
    activity: Review of every open claim and of the suitable work offered on each
    cadence: each month
    authority: Workplace Safety and Insurance Act, 1997 s. 40 — the co-operation duty is continuous and no review interval is set
    interval_basis: chosen
    responsible: return-to-work-coordinator
    applies_to: the organisation
    records: registers/construction/return-to-work-reviews.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Return to Work Review Record
    note: >
      One row per review per claim. `contact_since_last_review` is a required
      column because the co-operation duty is made of contact: the penalty
      provisions bite on failing to stay in touch and failing to attempt suitable
      work, and both are invisible in a register that only records outcomes.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: claim, label: Claim, type: text, required: true}
      - {key: worker, label: Worker, type: user, required: true}
      - {key: injured_on, label: Injured on, type: date, required: true}
      - {key: status, label: Status, type: select, required: true,
         options: [Off work, Modified work, Returned to pre-injury work, Not co-operating,
                   In dispute, Claim closed]}
      - {key: contact_since_last_review, label: Contact since the last review, type: longtext, required: true}
      - {key: suitable_work_offered, label: Suitable work offered, type: longtext, required: true}
      - {key: most_similar_offered, label: The most similar available job was offered, type: bool, required: true}
      - {key: offer_declined, label: Offer declined, and the reason given, type: longtext}
      - {key: board_notified_of_dispute, label: Board notified of any dispute, type: bool, required: true}
      - {key: accommodation, label: Accommodation in place, type: longtext}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
---

What this document must establish for THIS organisation: what it owes an injured
worker, when the duty starts, when it ends, and who does the work of it.

**The construction rules are different and the difference is in the
organisation's favour nowhere.** For employers generally, the re-employment
obligation applies only where twenty or more workers are regularly employed and
the worker had a year's continuous employment. **In construction neither test
applies.** A construction employer — one whose predominant business activity falls
in the construction class — owes the obligation to a worker who is unable to work,
full stop. A four-person contractor is bound. A worker hired three weeks ago is
covered. Every summary written for general industry gets this wrong for
construction, and an organisation that reads one will believe it has no obligation
at all.

It must state the offer rule as it stands: where several construction jobs are
available, the employer must offer **the one most similar in nature and earnings**
to the pre-injury position. Offering the easiest job to spare is not compliance;
`most_similar_offered` is a column because the decision has to be made and
recorded rather than reached by default.

It must set out the **co-operation duty** as a set of acts, because that is how it
is enforced: contact the worker as soon as possible after the injury, stay in
contact, **attempt to provide suitable work**, give the board the information it
asks for, offer re-employment where the obligation applies, and **notify the board
of any dispute**. The penalties escalate — a proportion of wage-loss benefits at
first, rising to the full benefits plus the cost of return-to-work training if
non-co-operation continues, for up to a year. Simultaneous failures attract the
single higher penalty; failures at different points in the same claim attract
several.

It must state the duration: the obligation ends at the earliest of two years from
the injury, a year after the worker is medically able to do the essential duties
of the pre-injury job, or the worker reaching the statutory age. And it must note
that terminating a re-employed worker **within six months** raises a presumption
that the obligation was not met — which is a reversal of onus, and the only
defence is a record made at the time.

It must distinguish the compensation duty from the **human rights duty to
accommodate**, which is broader, applies whether or not the injury was work
related, and has no analogue in the compensation statute. Undue hardship is a
narrow test — cost, outside sources of funding, and health and safety
requirements — and nothing else counts. An organisation that treats the end of
the re-employment period as the end of accommodation has confused two regimes.

It must say who actually does this. On a construction project the pre-injury job
may not exist by the time the worker is ready — the phase has finished, the crew
has moved. Modified work on a construction site takes planning, and the position
that owns it needs enough standing to place somebody on a project that did not
ask for them.

**The monthly review is this organisation's choice.** The duty is continuous and
no interval is set. A month is chosen because the penalty clocks run in business
days and weeks, and a review that ran quarterly would meet its own schedule while
missing every one of them.
