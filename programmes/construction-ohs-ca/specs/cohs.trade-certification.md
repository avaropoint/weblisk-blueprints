---
id: cohs.trade-certification
kind: procedure
title: Compulsory Trade Certification and Apprenticeship
structure: procedure
path: procedures/trade-certification.md

satisfies:
  - skilled_trades_ontario:6
  - skilled_trades_ontario:7
  - skilled_trades_ontario:8
  - skilled_trades_ontario:876-1
  - skilled_trades_ontario:877-2
  - skilled_trades_ontario:872-1
  - cor_2020:COR-16

requires: [cohs.credential-register, cohs.project-register]

approved_by: [senior-management]

declares:
  obligation:
    id: cohs.trade-authorisation-check
    activity: Verify that everyone doing compulsory trade work on the project is authorised to do it, and that the ratio on the work is observed
    cadence: each month
    authority: >
      Building Opportunities in the Skilled Trades Act, 2021 ss. 6–8 prohibit
      unauthorised practice of a compulsory trade and the employing or engaging of
      an unauthorised individual, and set the ratios. The Act sets no verification
      interval; a monthly check is this organisation's
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: the organisation
    per:
      listed_in: registers/projects.md
      key: project_id
      label: name
      from: start_on
      until: finished_on
    records: registers/trade-authorisation-checks.md
    escalate: {after: 1w, to: senior-management}
  register:
    title: Trade Authorisation Check Record
    note: >
      One row per project per month. The counts are per compulsory trade and not
      per project, because the prohibition and the ratio are both per trade: a
      project with authorised plumbers and an unauthorised electrician is not
      ninety per cent compliant, it is in contravention on the electrical work.
      `unauthorised_found` is required and is an integer, so that zero is a
      number somebody wrote rather than an empty cell.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: trades_on_site, label: Compulsory trades being practised on the project, type: longtext, required: true}
      - {key: individuals_checked, label: Individuals doing compulsory trade work, type: int, required: true}
      - {key: with_certificate, label: Holding a certificate of qualification, type: int, required: true}
      - {key: with_provisional, label: Holding a provisional certificate of qualification, type: int, required: true}
      - {key: registered_apprentices, label: Apprentices under an unsuspended registered training agreement, type: int, required: true}
      - {key: exempt, label: Exempted by regulation, with the exemption named, type: longtext}
      - {key: unauthorised_found, label: Individuals who could not produce proof, type: int, required: true}
      - {key: unauthorised_detail, label: Who, on what trade, and for which employer, type: longtext}
      - {key: work_stopped, label: The work was stopped, type: select, required: true,
         options: [Not applicable — nobody unauthorised, "Yes", "No — the reason is recorded"]}
      - {key: ratio_observed, label: The ratio was observed on every trade, type: bool, required: true}
      - {key: ratio_detail, label: Ratio counted, per trade, type: longtext, required: true}
      - {key: proof_sighted, label: Proof was sighted, not asserted, type: bool, required: true}
      - {key: expiring_within_90_days, label: Certificates expiring within ninety days, type: int, required: true}
      - {key: action, label: Action taken, type: longtext}
---

What this document must establish for THIS organisation: which of the trades it
performs or engages are compulsory, how it satisfies itself that every person
doing that work is authorised, and what happens on the day somebody is not.

**This is a licensing duty, not a safety duty, and the document must say so.**
Whether the person is allowed to do the work and whether they are doing it
safely are two questions with two statutes behind them, and an organisation that
answers one believes it has answered both. A worker with a current Working at
Heights certificate, a site orientation and a signed hazard assessment may still
be doing electrical work they may not lawfully do.

It must state the **prohibition in both directions**. The individual may not
practise a compulsory trade unless authorised; and no person may employ **or
otherwise engage** an individual to do so. "Otherwise engage" reaches a
subcontract, a labour broker and a day worker paid in cash — which is where this
duty is almost always breached, and where the organisation's own defence that
"they are not our employee" does not answer the section.

It must identify **which trades the organisation actually touches**, and separate
prescribed from compulsory. There are 144 prescribed trades and 23 of them are
compulsory; only the compulsory ones carry the prohibitions. A document that
lists all 144, or that says "all trades must be certified", is one nobody can
apply and it will be ignored on the first non-compulsory trade.

It must say what **proof** is, and that it must be produced rather than
described. The prescribed forms are a Skilled Trades Ontario document confirming
a certificate of qualification or provisional certificate of qualification, or
one confirming that the individual is an apprentice under a registered training
agreement. A photocopy in the office, a foreman's recollection, or "they have
been doing it twenty years" is not proof, and the last of those is the commonest
answer a site will give.

It must be explicit about **the certificate's own clock**. A certificate of
qualification in a compulsory trade carries a term set under the Act, and it is
the shortest recurring credential period in this programme — short enough that a
worker who was authorised at orientation may not be authorised in the same
calendar year. The expiry date goes on the statutory credentials register with
its `interval_source` recorded as set in law and its `consequence` recorded as
**the work becomes unlawful**, because it does.

It must explain the **ratio** and say that it is counted on the work rather than
on the payroll. The default is one apprentice to each journeyperson, prescribed
per trade; a provisional certificate holder counts as an apprentice for the
calculation. This is the requirement most likely to be breached by accident: the
journeyperson goes to another job for the afternoon and the ratio on the work
changes without anybody making a decision. That is why the check is per project
per month and why the record asks for the ratio **counted, per trade**, rather
than for a tick.

It must say what happens when **a sub-trade's people** cannot produce proof.
Prequalification is where this should be caught, and the subcontractor
prequalification procedure must ask for it; the check on site is the second
line, and the document must say who has authority to stop the work, because
somebody will have to, on a Friday, on a job that is already late.

It must name **who enforces this and what they may do**: inspectors appointed
under the Act, who are Ministry employees, may enter and investigate, and may
issue an educational enforcement measure, a compliance order, or a notice of
contravention carrying an administrative monetary penalty — **against the
employer as well as against the individual**. An organisation that treats
certification as the worker's own problem is mistaken about who receives the
penalty.

It must record the organisation's position on the **Ontario College of Trades**,
which no longer exists. It was wound up when this Act came into force on
1 January 2022; Skilled Trades Ontario is the Crown agency now responsible for
apprenticeship, trade standards and certification, and compliance moved to the
Ministry. Any document, contract clause or induction slide that names the
College, its membership fees or its membership card is out of date and should be
found and changed — the register of legal requirements is where that is tracked.

**The monthly interval is this organisation's choice.** The Act sets no
verification interval. A month is chosen to match the other per-project
verifications so one walk answers several of them, and because a trade crew
composition changes on a timescale of weeks. The document should say that a new
sub-trade mobilising is checked on arrival rather than at the next monthly pass.
