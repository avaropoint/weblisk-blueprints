---
id: capay.lien-administration
kind: procedure
title: Lien Administration, Bonds and Adjudication
structure: procedure
path: procedures/lien-administration.md

satisfies:
  - construction_act_ontario:31
  - construction_act_ontario:33
  - construction_act_ontario:34
  - construction_act_ontario:36
  - construction_act_ontario:13.5
  - construction_act_ontario:13.13
  - construction_act_ontario:13.19
  - construction_act_ontario:85.1

requires: [capay.policy, capay.substantial-performance]

approved_by: [senior-management]

declares:
  obligation:
    id: capay.lien-perfection
    # Record-origin on the preservation date, because perfection is measured
    # from the last day the lien COULD have been preserved rather than from the
    # day it was. Ninety days is the statutory window; the trigger is set at
    # seventy-five so that the decision is made with two weeks in hand, and the
    # authority below says which number is whose.
    activity: Decide and act on a preserved lien before it expires — perfect it, vacate it, discharge it or provide for it
    for:
      records: registers/construction-liens.md
      due: 75d after preserved_on
      key: lien_id
    authority: >
      Construction Act s. 36 (2) — a preserved lien expires unless it is perfected
      before the end of the 90-day period following the last day on which the lien
      could have been preserved. The seventy-five days here is this organisation's
      working deadline inside that period, not the statutory one
    interval_basis: chosen
    responsible: contract-administrator
    applies_to: the organisation
    records: registers/lien-actions.md
    escalate: {after: 7d, to: senior-management}
  register:
    title: Lien Action Record
    note: >
      One row per lien acted on, keyed by the lien. It records the decision and
      the date the decision was made against the date it had to be made by,
      because a lien perfected on the eighty-ninth day and a lien perfected on the
      ninety-first differ by one day and by everything.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: lien_id, label: Lien, type: relation, required: true,
         target: /registers/construction-liens.md#records, display: lien_id}
      - {key: decided_on, label: Decided on, type: date, required: true}
      - {key: decided_by, label: Decided by, type: user, required: true}
      - {key: statutory_deadline_on, label: Statutory deadline, type: date, required: true}
      - {key: days_in_hand, label: Days in hand when the decision was made, type: int, required: true}
      - {key: counsel_instructed_on, label: Counsel instructed on, type: date}
      - {key: decision, label: Decision, type: select, required: true,
         options: [Perfect it, Negotiate and discharge, Vacate by posting security,
                   Vacate by bond, Refer the underlying dispute to adjudication,
                   Let it expire, with the reason recorded, Already satisfied]}
      - {key: reason, label: Reason, type: longtext, required: true}
      - {key: amount_at_stake, label: Amount at stake, type: currency, required: true}
      - {key: security_or_bond, label: Security posted or bond furnished, type: currency}
      - {key: notified_insurer_or_surety_on, label: Insurer or surety notified on, type: date}
      - {key: action_completed_on, label: Action completed on, type: date}
      - {key: evidence, label: Registration particulars, order or agreement, type: attachment}
---

What this document must establish for THIS organisation: who watches the lien
clocks, who decides, and what the organisation does with the three remedies the
Act gives it that most contractors never use.

It must set out **the two lien deadlines and what starts each of them**.
Preservation: during the supply of services or materials, or at any time before
the lien expires — by registering a claim for lien on title where the lien
attaches to the premises, or by giving the owner a copy of the claim where it
does not. Perfection: a preserved lien expires unless it is perfected before the
end of the **ninety-day period following the last day on which the lien could
have been preserved**, which is not the same as ninety days after it was
preserved and is the arithmetic most often got wrong. The document must work
both calculations through with an example, because a worked example is what
somebody will copy.

It must name **who determines the deadline date** and say that it is a legal
determination rather than a data entry. The trigger event differs by whose lien
it is and by what has happened on the contract — the last supply, the
publication of a certificate of substantial performance, the certification of a
subcontract as complete. The organisation should take advice on the date rather
than derive it from a table, and the register records the date somebody
determined.

It must cover **certification of a subcontract as complete**, which is the
remedy a general contractor has and almost never exercises. On the application of
a subcontractor whose subcontract is finished, the payment certifier — or the
owner and contractor together where there is none — may certify it complete.
Doing so runs that subcontractor's lien period against its own work rather than
against the improvement as a whole, which closes exposure early on long projects
and releases that subcontract's holdback on its own clock. The document must say
who may make the application and who signs.

It must cover **vacating a lien**, the practical remedy on a live job: posting
security or furnishing a bond in the amount the Act and the court require, so
that title is cleared and the work continues while the dispute proceeds. The
cost of that security is a project cost and the decision is a commercial one,
and it must be made by somebody with authority to spend, quickly, because the
owner's own contract will be putting the organisation in default in the
meantime.

It must cover **adjudication**, and must say why it is here rather than in the
prompt payment procedure. A party may refer a dispute respecting a prescribed
matter — or any matter the parties agree — to adjudication, and a party to a
subcontract may do the same. A notice of adjudication in respect of a contract
may not be given more than **ninety days after the contract is completed,
abandoned or terminated** unless the parties agree otherwise: adjudication has
its own expiry and it is short. The adjudicator determines the matter within
**thirty days** of receiving the documents, extendable only as the section
allows, and an amount determined payable must be paid **within fifteen days** of
the determination being communicated. The document must say who in the
organisation can authorise a referral, and must be blunt that the process is
fast enough that a party who has not assembled its documents in advance will
lose on the record rather than on the merits.

It must cover **bonds on a public contract**. Where the owner is the Crown, a
municipality or a broader public sector organisation and the contract price
exceeds the prescribed amount for that owner, the contractor must furnish the
prescribed bonds — a labour and material payment bond and a performance bond —
in the prescribed coverage. The document must say who obtains them, when in the
procurement they must be in place, what the surety needs from the organisation,
and where the bond and the surety's contact details are kept. It must also say
what a **claim under somebody else's** labour and material payment bond is worth
to this organisation when it is the unpaid party, because that is a remedy
sitting beside the lien and it is routinely forgotten.

It must name the **notification duties to the organisation's own insurer and
surety**, with the day count each requires, and must say that a lien is
frequently the first written notice the surety receives that something is wrong.

**Seventy-five days is this organisation's working deadline and the document
must say so in the same breath as the ninety.** A decision taken on the
eighty-ninth day is not a decision; it is whatever counsel can achieve in an
afternoon. The fifteen days in hand are there so that vacating, negotiating and
perfecting are all still available.
