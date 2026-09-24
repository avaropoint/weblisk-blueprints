---
id: cohs.competency-requirements
kind: standard
title: Competency Requirements by Position and Trade
structure: standard
path: standards/competency-requirements.md

satisfies:
  - ohsa_ontario:25(2)(c)
  - o_reg_297_13:2
  - cor_2020:COR-16
  - iso_45001:7.2
  - isnetworld:ISN-SAFE-04

requires: [cohs.credential-register]

declares:
  obligation:
    id: cohs.competency-requirement-review
    activity: Review of the competency requirements against the work the organisation actually does and the law as it now stands
    cadence: each year
    authority: ISO 45001:2018 clause 7.2 and COR 2020 require competence to be determined and maintained. Neither sets a review interval
    interval_basis: chosen
    responsible: training-coordinator
    applies_to: the organisation
    records: registers/competency-requirement-reviews.md
    escalate: {after: 4w, to: health-safety-lead}
  register:
    title: Competency Requirement Review Record
    note: >
      One row per review. `requirements_added` is separated from `changes_in_law`
      because the two reasons a matrix changes are different: the organisation
      started doing work it did not do before, or the law moved. Both happen, and
      an organisation that only watches the second will be caught by the first.
    layout: form
    review: required
    approvers: [training-coordinator]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: positions_covered, label: Positions covered, type: int, required: true}
      - {key: new_work_types, label: Kinds of work taken on since the last review, type: longtext}
      - {key: requirements_added, label: Requirements added, type: longtext}
      - {key: requirements_removed, label: Requirements removed, and why, type: longtext}
      - {key: changes_in_law, label: Changes in law or standards taken into account, type: longtext, required: true}
      - {key: gaps_found, label: People currently below requirement, type: int, required: true}
      - {key: plan, label: How the gaps will be closed, type: longtext}
---

What this artifact must establish: for each position and each kind of work, what
a person must hold before they may do it — and which of those requirements is the
law's, which is a client's, and which is the organisation's own.

It is the statement the register of statutory credentials is measured against. The
register says what people hold; without this, nobody can say whether that is
enough. The two must be read together and neither is useful alone.

**Every row must say where its requirement comes from**, and the three sources
behave completely differently:

- **Required by law**, for this work, in this province. Working at Heights before
  using a fall protection system. A certificate of qualification for a compulsory
  trade. A hoisting engineer's certificate by machine capacity. Suspended access
  training before going over the edge. These are non-negotiable and a person
  without one must not do the work.
- **Required by a client or a prequalification scheme.** Common, legitimate, and
  frequently mistaken for law — a traffic control card, a confined space card, a
  site-specific induction from an owner. These bind by contract, they vary by
  client, and they must be recorded as contractual so that losing the client
  removes the requirement.
- **Required by this organisation.** A refresher where the law sets none, a
  second person trained as cover, an internal authorisation to sign a permit.
  These are decisions and the matrix should say who made them.

It must distinguish a **credential** from **competence**. A certificate says
somebody attended an approved programme and passed a test. Competence is a
judgement that this person can do this work safely on this site, and on a
construction project it is usually made by a supervisor watching. The matrix must
say who makes that judgement, on what evidence, and where it is recorded, because
the statutory definition of a competent person is about knowledge, training,
experience and familiarity with the Act — not about a card.

It must cover the positions whose competence requirements are about the programme
rather than the work: the supervisor, who must have awareness training within a
week of starting and who carries personal duties; the committee's certified
members, whose certification has a live three-year refresher clock and who cease
to be certified without it; the first aid attendants, whose numbers are driven by
shift size; and the worker trained in cardiopulmonary resuscitation and
defibrillator use who must be present whenever work is in progress.

It must handle **short-service workers** — people new to the organisation, or new
to this kind of work — as a category with its own requirements, because the injury
rate in the first months is not a matter of opinion. Whether the organisation
calls that a short-service employee programme or something else, the matrix is
where the extra supervision and the buddy arrangement are written down.

**The annual review is this organisation's choice.** Nothing sets an interval. The
reason to hold one at all is that the matrix goes stale in two directions at once:
the organisation takes on work it has not done before, and the law changes under
the work it always did.
