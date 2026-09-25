---
id: fleet.collision-review
kind: procedure
title: Collision Review and Preventability Determination
structure: procedure
path: procedures/collision-review.md

satisfies:
  - hta_ontario:HTA-CVOR-03
  - hta_ontario:HTA-CVOR-04
  - hta_ontario:HTA-CVOR-05
  - nsc_ca:NSC-14
  - nsc_ca:NSC-15
  - cor_2020:COR-17
  - iso_45001:10.2

requires: [fleet.collisions, fleet.drivers]

declares:
  obligation:
    id: fleet.collision-review
    activity: Review the collision, determine whether it was preventable, and decide what changes
    for:
      records: registers/collisions.md
      due: 14d after occurred_on
      key: reference
    authority: >
      Nothing in the Highway Traffic Act requires an operator to review a
      collision or sets a deadline for doing so. What makes it matter is
      HTA-CVOR-03 and the record: a reportable collision is weighted onto the
      operator's own CVOR record whether or not the driver was at fault, and a
      facility audit under National Safety Code Standard 15 asks what the
      operator did about the collisions on its record. ISO 45001 cl. 10.2
      requires incidents to be investigated and names no interval. The fourteen
      days is this organisation's, chosen because memory and physical evidence
      are both mostly gone at a month.
    interval_basis: chosen
    responsible: fleet-manager
    applies_to: the organisation
    records: registers/collision-reviews.md
    escalate: {after: 1w, to: senior-management}
    satisfies:
      - hta_ontario:HTA-CVOR-03
      - nsc_ca:NSC-14
      - iso_45001:10.2
  register:
    title: Collision Review Record
    note: >
      One row per collision reviewed. `preventable` is determined HERE and
      deliberately not on the collision register: it is a judgement made after
      somebody has looked, and a field filled in at the roadside by the person
      most exposed by the answer is not a determination. `securement_factor` and
      `hours_factor` are asked explicitly because those two causes are
      systematically under-found — a review that starts from the driving reaches
      the driver and stops.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: collision, label: Collision, type: relation, required: true,
         target: /registers/collisions.md#records, display: reference}
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: driver_interviewed, label: The driver was interviewed, type: bool, required: true}
      - {key: scene_evidence, label: Evidence considered, type: longtext, required: true}
      - {key: preventable, label: Preventability, type: select, required: true,
         options: ["Preventable", "Not preventable",
                   "Preventable in part — contributing factors within the organisation's control",
                   Not yet determined]}
      - {key: preventability_reasoning, label: Why, type: longtext, required: true}
      - {key: vehicle_factor, label: A vehicle condition contributed, type: select, required: true,
         options: ["No", "Yes — a defect had been reported", "Yes — a defect had not been reported",
                   Not yet determined]}
      - {key: hours_factor, label: Hours of service or fatigue contributed, type: select, required: true,
         options: ["No", "Yes — the driver was within the limits",
                   "Yes — the driver was over a limit", Not yet determined]}
      - {key: securement_factor, label: Load or securement contributed, type: select, required: true,
         options: ["No", "Yes — the load shifted, spilled or came off",
                   "Yes — weight or loading of the vehicle", Not yet determined]}
      - {key: qualification_factor, label: Licence, endorsement or competence contributed, type: select, required: true,
         options: ["No", "Yes — the driver was not authorised for the vehicle",
                   "Yes — training or experience", Not yet determined]}
      - {key: dispatch_factor, label: Dispatch, scheduling or route contributed, type: select, required: true,
         options: ["No", "Yes", Not yet determined]}
      - {key: confirmed_on_cvor, label: Confirmed on the CVOR abstract, type: select, required: true,
         options: ["Confirmed present", "Confirmed absent", "Not yet checked"]}
      - {key: corrective_actions, label: Corrective actions, with owners and dates, type: longtext, required: true}
      - {key: fleet_wide_change, label: Something changed for the whole fleet, type: bool, required: true}
      - {key: fleet_wide_change_detail, label: What changed, type: longtext}
      - {key: driver_outcome, label: Outcome for the driver, type: select, required: true,
         options: ["No action", "Coaching or retraining", "Restricted dispatch",
                   "Removed from driving duties", "Handled as a personnel matter outside this record",
                   Not yet determined]}
      - {key: closed_on, label: Closed on, type: date}
    retention:
      keep: 7y
      authority: >
        No retention period is prescribed for a carrier's collision review.
        Seven years is this organisation's, chosen against the period over which
        a civil claim arising from a collision may still be brought and
        defended, and long enough to outlive the CVOR record's own window.
      reason: The review is the organisation's own account of what it knew and what it changed, and it is asked for years later by somebody else's lawyer.
---

What this document must establish for THIS organisation: who reviews a
collision, what they are deciding, and what has to come out of it.

**Fault and preventability are different questions, and this review asks the
second.** Fault is for the police, the insurer and eventually a court.
Preventability asks whether anything the organisation controls could have
changed the outcome — and a collision can be entirely somebody else's fault and
entirely preventable by this organisation, which is the case the review exists
to find. A procedure that lets "not at fault" close a file has bought a defence
and learned nothing.

**The determination belongs here and not on the collision register.** The
register records what happened, at the time, by whoever was there. Preventability
is a judgement made after somebody has looked, and putting it on a form filled
in at the roadside asks the person most exposed by the answer to write it down.

**The fourteen days is ours, and the reason is evidence.** Nothing requires a
review or sets a deadline. What decides the number is that a driver's memory, a
photograph nobody took, and a component nobody kept are all mostly gone at a
month. The procedure should say the organisation chose it.

**A reportable collision lands on the CVOR record whether or not the driver was
at fault**, is weighted by severity and stays for a fixed period. That is what
makes this an operating matter rather than an insurance one, and it is why the
review must confirm, at the next abstract, that what the organisation expected
to appear did appear — and, more usefully, that nothing appeared that it had not
recorded.

**The review must reach past the driving, and the register forces it to.** The
four factors asked explicitly — vehicle condition, hours and fatigue, load and
securement, and licence or competence — are the ones a review that starts from
the driving never reaches. A load that shifted is simultaneously a collision and
a securement failure; a driver in the fourteenth hour is a dispatch decision. A
review that stops at the driver has found the last link in the chain and called
it the cause.

**Near misses and yard contacts are reviewed too**, on the same clock and with
the same questions. They have the same causes and a hundredth of the cost, and
an organisation that only reviews what the police attended is only learning from
the events it could not absorb quietly.

**It must separate the corrective action from the discipline.** What changes for
the fleet, and what happens to the individual, are different decisions made by
different people for different reasons, and merging them guarantees that the
next driver reports less. The procedure must say where a personnel outcome is
recorded, and it is not in this register.

**The chain ends in the monthly review.** A collision review that identifies a
fleet-wide change and nothing that checks it was made is a document with a good
conclusion. `fleet.compliance-review` is where open actions from this register
are swept, and the procedure should say so.
