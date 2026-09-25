---
id: phipa.access-audit
kind: procedure
title: Auditing Access to Health Records
structure: procedure
path: procedures/health-information-access-audit.md

satisfies:
  - phipa_ontario:6(3)
  - phipa_ontario:12
  - phipa_ontario:19

requires: [phipa.information-practices]

declares:
  obligation:
    id: phipa.access-audit
    activity: Audit the electronic record of who accessed personal health information
    cadence: each month
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/health-information-access-audits.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Health Information Access Audit Record
    note: >
      One row per audit. `flagged_for_review` and `confirmed_unauthorised` are
      separate columns because an audit that reports only confirmed snooping
      cannot show that it looked: the value is in how many accesses were
      questioned, not only in how many turned out to be wrong.
    layout: form
    review: required
    approvers: [privacy-officer]
    columns:
      - {key: audited_on, label: Audited on, type: date, required: true}
      - {key: period, label: Period covered, type: text, required: true}
      - {key: audited_by, label: Audited by, type: user, required: true}
      - {key: method, label: Method — targeted, random or triggered, type: select, required: true,
         options: [Random sample, Targeted — same surname, Targeted — VIP or staff record,
                   Targeted — high volume user, Triggered by a complaint, System-generated alerts]}
      - {key: accesses_reviewed, label: Accesses reviewed, type: int, required: true}
      - {key: flagged_for_review, label: Flagged for explanation, type: int, required: true}
      - {key: confirmed_unauthorised, label: Confirmed unauthorised, type: int, required: true}
      - {key: breaches_raised, label: Breaches raised as a result, type: int, required: true}
      - {key: lockbox_honoured, label: Express instructions honoured where in force, type: bool, required: true}
      - {key: actions, label: Actions taken, type: longtext, required: true}
---

What this document must establish for THIS organisation: how it finds out that
somebody looked at a record they had no business opening.

This is the single most distinctive duty in Ontario health privacy and the one
most custodians have not implemented. The Information and Privacy Commissioner's
health orders are dominated by unauthorised access by insiders — a colleague, a
neighbour, a family member, a public figure — and in almost every case the
system had the log and nobody was reading it.

It must state what the audit looks for. Random sampling alone finds very little;
targeted queries find most of it — accesses to records sharing a surname or
address with the user, accesses to staff members' own records or those of their
family, accesses by a user whose volume is out of line with their role, and
accesses to a record that has been in the news.

It must say who audits, and it cannot be the person whose access is being
audited. Where the organisation is small, the answer may be that the custodian
does it personally or that it is bought in; what it cannot be is the same
administrator whose actions are in the log.

It must say what happens when an access cannot be explained. That is a privacy
breach under PHIPA, the individual must be notified at the first reasonable
opportunity, and the Commissioner must be notified where the prescribed
circumstances apply — which expressly include disciplinary action being taken or
that would have been taken against a college member. An organisation that
handles snooping as an HR matter alone has missed two statutory duties.

It must cover the express instruction — the lock-box. Where an individual has
withheld or withdrawn consent to a disclosure, the system has to be able to
honour it, and the audit is where the organisation finds out whether it did.
