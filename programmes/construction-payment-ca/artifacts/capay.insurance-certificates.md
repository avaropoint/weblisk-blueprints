---
id: capay.insurance-certificates
kind: register
title: Register of Insurance Certificates
structure: standard
path: registers/insurance-certificates.md

# A register carries no `satisfies:`. The citation belongs on the procedure
# that declares the obligation — here, `capay.insurance-renewal`.

requires: [capay.policy]

register:
  title: Register of Insurance Certificates
  note: >
    One row per policy, per insured party, per contract. Not one per
    subcontractor and not one per project: a sub-trade carries several policies
    with different expiry dates and different limits, and an organisation
    holding "their insurance certificate" holds whichever one arrived last. The
    question this register has to answer is narrower and harder — was THIS
    coverage, at THIS limit, in force for the whole of THIS contract.
  columns:
    - {key: policy_number, label: Policy number, type: text, required: true}
    - {key: insured, label: Insured party, type: text, required: true}
    - {key: insurer, label: Insurer, type: text, required: true}
    - {key: coverage, label: Coverage, type: select, required: true,
       options: [Commercial general liability, Automobile, Contractors' pollution,
                 Professional liability, Builder's risk, Excess or umbrella, Other]}
    - {key: limit, label: Limit, type: currency, required: true}
    - {key: contract, label: Contract or subcontract number, type: text, required: true}
    - {key: project, label: Project, type: relation,
       target: /registers/projects.md#records, display: project_id}
    - {key: we_are_additional_insured, label: We are named as an additional insured, type: bool, required: true}
    - {key: effective_from, label: Effective from, type: date, required: true}
    - {key: expires_on, label: Expires on, type: date, required: true}
    - {key: contract_ends, label: Contract expected to end, type: date, required: true}
    - {key: verified_with_insurer, label: Verified with the insurer or broker, type: bool, required: true}
    - {key: certificate, label: Certificate, type: attachment}
    - {key: status, label: Status, type: select, required: true,
       options: [Current, Expiring, Expired, Not obtained, Cancelled by the insurer]}
---

What this artifact must establish: that for every party this organisation
contracted with, the insurance the contract required was in force for the whole
time that party was working — and that somebody checked, rather than filed.

**Nothing in Ontario statute requires this register.** The duty is contractual:
the subcontract says what coverage the sub-trade carries, at what limit, naming
whom, and evidenced how. That makes this the one register in the pack whose
authority is the organisation's own paperwork, and the brief says so plainly
rather than borrowing a statute to make it look heavier. What makes it belong in
a *payment* programme is what happens when it lapses — a certificate that has
expired is discovered at the moment money is about to move, which is the last
moment it can be acted on and the worst moment to discover it.

**`contract_ends` sits beside `expires_on` for the same reason it does on the
clearance register.** A policy is written for a period and a contract runs for a
different one; when the second date is later than the first, somebody has work
to do, and the register is the only place that comparison is visible. An
organisation that keeps the latest certificate per sub-trade cannot make it at
all.

**A certificate of insurance is not insurance.** It is a broker's statement,
usually carrying its own disclaimer, that a policy existed when it was typed. It
does not bind the insurer, it does not survive a cancellation, and it is often
issued for a policy that is then cancelled for non-payment without anybody
telling the certificate holder. That is what `verified_with_insurer` is for, and
why `status` carries "Cancelled by the insurer" as an outcome distinct from
"Expired": one is a date arriving and the other is a fact nobody here observed.

**`we_are_additional_insured` is a boolean because the answer is checkable and
the consequence is total.** Coverage the organisation is not named on is
coverage that responds to somebody else's claim. A register that records a limit
without recording whether this organisation is inside it records a number with
no bearing on anything.
