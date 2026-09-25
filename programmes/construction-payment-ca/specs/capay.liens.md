---
id: capay.liens
kind: register
title: Register of Construction Liens
structure: standard
path: registers/construction-liens.md

# A register carries no `satisfies:`. The citation belongs on the procedure that
# governs what is done about a lien; this file is where each one and its two
# statutory dates are recorded.

requires: [capay.lien-administration]

register:
  title: Register of Construction Liens
  note: >
    One row per claim for lien, in either direction: one this organisation has
    preserved, and one preserved against a project it is on. Both are recorded
    here because both are governed by the same two dates and because an
    organisation that keeps only the liens against it has no record of the
    remedy it has and is about to lose.

    Two dates and no others decide the outcome. A lien is preserved by
    registration on title, or by giving the owner a copy of the claim where it
    does not attach, before it expires; and a preserved lien expires unless it
    is **perfected** within the ninety days after the last day it could have
    been preserved. Missing either is not a procedural stumble — the security is
    gone and it cannot be recovered.
  layout: form
  columns:
    - {key: lien_id, label: Reference, type: text, required: true}
    - {key: direction, label: Which way, type: select, required: true,
       options: [We preserved it, It was preserved against a project we are on,
                 Preserved against us by a subcontractor or supplier]}
    - {key: claimant, label: Claimant, type: text, required: true}
    - {key: holdback, label: Contract, type: relation,
       target: /registers/holdback-account.md#records, display: holdback_id}
    - {key: project, label: Project, type: relation,
       target: /registers/projects.md#records, display: project_id}
    - {key: premises, label: Premises or property identifier, type: text, required: true}
    - {key: attaches_to_premises, label: The lien attaches to the premises, type: select, required: true,
       options: ["Yes", "No — the owner is given a copy of the claim instead", Not yet determined]}
    - {key: last_supply_on, label: Last day services or materials were supplied, type: date, required: true}
    - {key: substantial_performance_published_on, label: Certificate of substantial performance published on, type: date}
    - {key: subcontract_certified_complete_on, label: Subcontract certified complete on, type: date}
    - {key: preservation_deadline_on, label: Last day the lien could be preserved, type: date, required: true}
    - {key: preserved_on, label: Preserved on, type: date}
    - {key: amount_claimed, label: Amount claimed, type: currency, required: true}
    - {key: perfection_deadline_on, label: Last day it may be perfected, type: date}
    - {key: perfected_on, label: Perfected on, type: date}
    - {key: written_notice_of_lien_received_on, label: Written notice of lien received on, type: date}
    - {key: security_posted, label: Security posted or bond obtained to vacate, type: currency}
    - {key: outcome, label: Outcome, type: select, required: true,
       options: [Open — within the preservation period, Preserved — within the perfection period,
                 Perfected, Vacated on posting security, Discharged by agreement,
                 Expired unpreserved, Expired unperfected, Satisfied, Withdrawn]}
    - {key: counsel, label: Counsel instructed, type: text}
    - {key: closed_on, label: Closed on, type: date}
---

What this artifact must establish: every lien this organisation holds or faces,
the last day it can be acted on, and what was done.

**It exists because the deadlines are unforgiving and are not on anybody's
calendar.** A lien expires. A preserved lien that is not perfected expires. No
notice is given, nothing is refused, and the only signal is that a date passed.
Every other clock in this programme produces a consequence somebody will hear
about; these two produce silence and the loss of the only security the
organisation had.

**Both directions are in one register because they are the same fact from two
sides.** A lien preserved by a sub-trade against a project is a claim against
the organisation's holdback and a defence to releasing it; a lien the
organisation preserved is its own remedy against an owner who has not paid. An
organisation that tracks only the first is well informed about its risk and
blind to its remedy, and it is usually the one with the cash flow problem.

**`preservation_deadline_on` is a required column and it is a derived date the
organisation must work out and write down.** It depends on which event applies
— the last supply, the publication of a certificate of substantial performance,
the certification of a subcontract as complete — and on whose lien it is. The
register does not compute it, deliberately: it is a legal determination on the
facts of that contract, and a formula in a pack would produce a confident wrong
date. What the register insists on is that somebody determined it, and when.

**`attaches_to_premises` decides how the lien is preserved at all.** Where it
attaches, preservation is by registering a claim for lien on title in the proper
land registry office. Where it does not — most obviously on Crown land, and on
premises the Act exempts — it is preserved by giving the owner a copy of the
claim, and an organisation that assumes registration is the only method will
preserve nothing.

**`written_notice_of_lien_received_on` is separate from `preserved_on`** because
a written notice of lien is a different instrument with a different effect: it
affects what the payer may safely pay out, and it arrives before, or instead of,
a registered claim. Recording it in the same place as a registration is how an
organisation comes to pay out against a contract it had been warned about.

**Nothing in this register is a reason to withhold statutory holdback other than
on the grounds the Act allows.** A preserved lien against the holdback is one of
those grounds; an unregistered grumble is not. The holdback release procedure
reads this register, and the connection between the two is the reason both exist.
