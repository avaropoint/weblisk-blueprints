---
id: capay.holdback-account
kind: register
title: Holdback Account
structure: standard
path: registers/holdback-account.md

# A register carries no `satisfies:`.
#
# It is the evidence that work happened, not the document that answers a
# control — and the relation vocabulary says so structurally: `implements`
# onto a control may be asserted by a blueprint, a policy or a procedure,
# and by nothing else. The citation belongs on the procedures that declare
# this register's obligations; this file is where the facts are recorded.

requires: [capay.policy]

register:
  title: Holdback Account
  note: >
    One row per contract or subcontract on which this organisation retains
    holdback or has holdback retained from it. Not one row per project and not
    one per counterparty: the holdback is a statutory ten per cent of the price
    of a particular contract, it is released against that contract's own clock,
    and a project with nine sub-trades on it has nine separate release dates.
    `position` is first because every other column is read differently
    depending on it — the same row means "money we are holding" or "money we are
    owed".
  columns:
    - {key: holdback_id, label: Holdback reference, type: text, required: true}
    - {key: position, label: Which side we are on, type: select, required: true,
       options: [We retain the holdback, Our holdback is retained]}
    - {key: counterparty, label: Counterparty, type: text, required: true}
    - {key: contract, label: Contract or subcontract number, type: text, required: true}
    - {key: project, label: Project, type: relation,
       target: /registers/projects.md#records, display: project_id}
    - {key: contract_date, label: Contract entered into on, type: date, required: true}
    - {key: contract_price, label: Contract price, type: currency, required: true}
    - {key: holdback_kind, label: Kind of holdback, type: select, required: true,
       options: [Basic, Finishing]}
    - {key: retained_to_date, label: Retained to date, type: currency, required: true}
    - {key: released_to_date, label: Released to date, type: currency, required: true}
    - {key: substantially_performed_on, label: Substantially performed on, type: date}
    - {key: published_on, label: Certificate published on, type: date}
    - {key: lien_expiry_on, label: Liens expire on, type: date}
    - {key: release_due_on, label: Next release falls due on, type: date, required: true}
    - {key: lien_preserved, label: A lien has been preserved against this holdback, type: bool, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [Retained, Release due, Released in full, Withheld — lien preserved,
                 Withheld — notice of non-payment given, Withheld — contractual condition not met,
                 In dispute]}
---

What this artifact must establish: for every contract and subcontract this
organisation is party to under which a lien may arise, how much holdback is
being held, by whom, against which clock, and what has been released.

**`release_due_on` is the whole point of the register.** Ten per cent retained
is easy; knowing the day it falls due is not, because three different events can
set that day and they are not the same event. The basic holdback becomes payable
by reference to the expiry of the liens it secures, which runs from the
**publication** of the certificate or declaration of substantial performance —
not from its issue. The finishing holdback runs its own separate course. And
independently of both, the Act requires a release on **each anniversary of the
date the contract was entered into**, which is why `contract_date` is a required
column on a register that otherwise looks like a ledger: the anniversary is
computed from it, and an organisation that does not hold that date cannot tell
whether it is late.

**`position` exists because the exposure is asymmetric.** Holdback this
organisation retains is money it is holding in trust and will have to produce on
a date somebody else can enforce. Holdback retained *from* this organisation is
money it has already earned, and the only way to get it is to make somebody
else's release date arrive — which means knowing when it is, and being able to
demand the state of accounts. One register, because they are the same statutory
mechanism seen from two ends, and an organisation that keeps two loses the
ability to answer "what is our net holdback position" at all.

**`lien_preserved` is a required boolean and not a status.** It is the one fact
that lawfully changes what may be paid, it is knowable independently of anybody's
opinion of the sub-trade, and it must be answerable on a row whose `status` says
something else entirely. A preserved lien on a holdback that the register also
reports as released is a finding, and a register that folded the two into one
field could not produce it.

**Dates left empty are not zeros.** A row with no `substantially_performed_on`
has not been substantially performed; a row with a certification date and no
`published_on` is the dangerous state — the certificate exists, everybody
believes the clock is running, and it is not. The obligations that trigger off
this register are written so that an empty date raises no work, which means an
empty date is silent. Whether that silence is correct is what
`capay.holdback-reconciliation` exists to ask, monthly, out loud.

**No retention period is declared here.** A holdback record is evidence in a
lien action and in a trust claim, and the period an organisation should keep it
for follows from the limitation periods on those, which this pack does not
purport to state. Set one, and record what was chosen and why.
