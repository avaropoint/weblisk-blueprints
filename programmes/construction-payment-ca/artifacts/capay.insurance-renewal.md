---
id: capay.insurance-renewal
kind: procedure
title: Insurance Certificate Renewal
structure: procedure
path: procedures/insurance-certificate-renewal.md

satisfies:
  - isnetworld:ISN-SAFE-02
  - cor_2020:COR-15

requires: [capay.insurance-certificates]

declares:
  obligation:
    id: capay.insurance-renewal
    activity: Obtain a replacement certificate of insurance before the current one expires, or stop the work
    for:
      records: registers/insurance-certificates.md
      due: 30d before expires_on
      key: policy_number
    authority: >
      The subcontract. No Ontario statute requires a subcontractor to carry or to
      evidence insurance; the requirement and the limits are contractual, and the
      notice period is nobody's but this organisation's
    interval_basis: chosen
    responsible: contract-administrator
    applies_to: the organisation
    records: registers/insurance-certificate-renewals.md
    escalate: {after: 1w, to: project-manager}
  register:
    title: Insurance Certificate Renewal Record
    note: >
      One row per policy acted on, keyed by the policy it replaces. The register
      of certificates says what is held; this says that somebody asked before a
      date, and what happened when the answer came back wrong.
    layout: form
    review: required
    approvers: [contract-administrator]
    columns:
      - {key: policy_number, label: Policy renewed, type: relation, required: true,
         target: /registers/insurance-certificates.md#records, display: policy_number}
      - {key: insured, label: Insured party, type: text, required: true}
      - {key: requested_on, label: Requested on, type: date, required: true}
      - {key: reminders_sent, label: Reminders sent, type: int, required: true}
      - {key: received_on, label: Replacement received on, type: date}
      - {key: new_policy_number, label: New policy number, type: text}
      - {key: new_expires_on, label: New expiry, type: date}
      - {key: verified_with_insurer, label: Verified with the insurer or broker, type: bool, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Renewed, Insurer declined, Sub-trade uninsured, Limits reduced below contract,
                   Contract ended, Not required]}
      - {key: work_continued_uninsured, label: Work continued while the coverage was not in force, type: bool, required: true}
      - {key: note, label: Note, type: longtext}
---

What this artifact must establish: that a certificate about to expire was chased
before it expired, by whom, how many times, and what happened to the sub-trade's
work if nothing came back.

**Thirty days, and the number is this organisation's own.** It is longer than
the fourteen the clearance renewal uses, and the reason is worth writing down:
a clearance certificate is produced by a board on request in minutes, whereas a
renewal certificate comes from a broker who is renewing a policy, and a policy
that is going to be declined or re-rated is declined at renewal. Thirty days is
roughly the distance at which a sub-trade still has somewhere else to go.

**`reminders_sent` is a column because chasing costs money and nobody measures
it.** It is the number that turns "we chase our subs for paperwork" into a
figure — how many asks a certificate takes, and which sub-trades take four. It
is also the honest record behind an automated chase: a system that sends three
notices and gets nothing has not achieved compliance, it has achieved three
notices, and the register should be able to say which.

**"Limits reduced below contract" is an outcome, not a note.** A renewed policy
at half the limit the subcontract requires arrives looking exactly like a
success — a current certificate, a future expiry date, a green row — and it is
the failure that actually reaches this organisation, because the shortfall is
discovered by a claim. A renewal that produces a compliant date and a
non-compliant limit must be recordable as what it is.

**`work_continued_uninsured` is required and the honest answer is sometimes
yes.** A register that cannot record it will not be filled in, and a gap
acknowledged is a risk somebody can price. It is also the column that makes the
connection this pack exists to make: a sub-trade that worked uninsured is a
sub-trade whose holdback release is about to be a decision rather than a
payment.

It escalates to the position that controls site access rather than to the one
chasing the certificate, for the same reason the clearance renewals do: the
person sending the reminder cannot send anybody home.

It is submitted as a form rather than typed into a grid, because a renewal
discharges an occurrence and an occurrence needs one attributable act. A grid
commits every keystroke, so a half-entered renewal would report a sub-trade as
insured before anybody said so.
