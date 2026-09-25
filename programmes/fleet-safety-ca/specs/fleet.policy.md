---
id: fleet.policy
kind: policy
title: Commercial Vehicle Safety Policy
structure: policy
path: policies/commercial-vehicle-safety-policy.md

satisfies:
  - hta_ontario:HTA-CVOR-01
  - hta_ontario:HTA-CVOR-03
  - hta_ontario:HTA-CVOR-06
  - nsc_ca:NSC-14
  - nsc_ca:NSC-15
  - mvta_canada:MVTA-01
  - cor_2020:COR-01
  - cor_2020:COR-04
  - iso_45001:5.2

approved_by: [senior-management]

declares:
  obligation:
    id: fleet.policy-review
    activity: Review of the written commercial vehicle safety policy
    cadence: each year
    authority: >
      No Ontario instrument requires an operator to hold a written fleet safety
      policy or sets an interval for reviewing one. What tests it is the
      facility audit under National Safety Code Standard 15, which asks to see
      the written programme the operator says it runs; ISO 45001 cl. 5.2
      requires a policy reviewed at planned intervals and names no interval.
      The year is this organisation's.
    interval_basis: chosen
    responsible: fleet-manager
    applies_to: the organisation
    records: registers/fleet-policy-reviews.md
    escalate: {after: 4w, to: senior-management}
    satisfies:
      - nsc_ca:NSC-15
      - cor_2020:COR-01
      - iso_45001:5.2
  register:
    title: Commercial Vehicle Safety Policy Review Record
    note: >
      One row per review. `scope_still_correct` is asked separately from
      `changed` because the question this policy gets wrong over time is not its
      wording but its reach: a company that bought its first float, started
      running into Quebec, or sold the last truck over 4,500 kg has changed
      which regime it is in without changing a sentence of the document.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: vehicles_over_threshold, label: Vehicles over 4,500 kg operated, type: int, required: true}
      - {key: scope_still_correct, label: The policy still describes the operation, type: select, required: true,
         options: ["Yes — unchanged",
                   "No — the fleet or the work has changed and the policy has been amended",
                   "No — the fleet or the work has changed and the policy has not yet been amended"]}
      - {key: extra_provincial_work, label: Extra-provincial or cross-border work in the period, type: select, required: true,
         options: [None, Occasional, Regular, Not yet determined]}
      - {key: legal_changes, label: Changes in the Act, the regulations or the Code considered, type: longtext, required: true}
      - {key: changed, label: The policy was amended, type: bool, required: true}
      - {key: changes, label: What changed, type: longtext}
      - {key: reissued_on, label: Reissued on, type: date}
      - {key: communicated, label: How it was put in front of drivers, type: longtext, required: true}
      - {key: next_review, label: Next review due, type: date}
---

What this document must establish for THIS organisation: that it operates
commercial motor vehicles, who is answerable for that, and what the people who
drive them are required to do.

**It must start by saying whether this organisation is in the regime at all,
and on what evidence.** The line is 4,500 kg of registered or actual gross
weight for a truck or a truck and trailer combination, with buses caught by
capacity and tow trucks caught regardless. A policy that opens with a mission
statement instead of that sentence has skipped the only question that decides
whether every other duty in the programme applies. A company all of whose
vehicles are below the line should not hold this policy at all — see the
programme map — and one that is partly in is fully in for the vehicles that
are.

**It must name the operator, not the owner.** The Act makes the *operator* —
the person responsible for the operation of the vehicle — answerable for the
conduct of its drivers and the mechanical condition of its vehicles, and the
operator is not always the registered owner and not always the driver's
employer. Where the organisation runs leased trucks, owner-operators or a
subcontractor's float, the policy must say how it is decided whose CVOR the
vehicle sits on, because getting that wrong does not produce a gap in a record:
it produces the wrong company's record accumulating the events.

**It must say which half of the regime each kind of work falls in.** Ontario's
regulations govern intra-provincial operation; the federal *Motor Vehicle
Transport Act* and the *Commercial Vehicle Drivers Hours of Service
Regulations* govern an undertaking that crosses a provincial, territorial or
international boundary. It turns on where the vehicle goes, not where the
company is based, and the numbers being identical on both sides is precisely
why nobody notices. One paragraph naming the trips that cross a boundary, and
what changes for them, is worth more here than a recital of either instrument.

**It must be a policy and not a manual.** The detail of how a trip inspection is
conducted, what makes a defect major, how hours are audited and what securement
a machine needs belongs in the procedures this programme declares. What belongs
here is the organisation's position on the handful of things a procedure cannot
settle: that a driver who reports a major defect will not be dispatched anyway,
that a trip which cannot be completed inside the driver's remaining hours will
not be assigned, that a licence is verified against the Ministry's record rather
than against a photocopy, and who has authority to take a vehicle out of
service and to put it back.

**It must state the consequence of dispatch pressure in the organisation's own
words.** The operator's duty is not to request, require or allow a
contravention, and the contravention happens at the moment the trip is assigned
rather than at the moment the hours run out. A policy that does not say a
dispatcher may refuse, and to whom it escalates, leaves the driver to carry a
decision the Act puts on the company.

**The annual review is this organisation's interval, and the document should
say so** rather than implying a statutory one. What the review is actually for
is the scope: the fleet, the weights, and whether any of last year's work
crossed a boundary.
