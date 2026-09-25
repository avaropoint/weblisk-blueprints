---
id: fleet.defect-repair
kind: procedure
title: Defect Repair and Return to Service
structure: procedure
path: procedures/defect-repair-and-return-to-service.md

satisfies:
  - hta_ontario:HTA-TRIP-04
  - hta_ontario:HTA-TRIP-06
  - hta_ontario:HTA-PMVI-04
  - hta_ontario:HTA-CVOR-03
  - nsc_ca:NSC-11
  - nsc_ca:NSC-13
  - cor_2020:COR-12

requires: [fleet.vehicle-defects]

declares:
  obligation:
    id: fleet.defect-repair
    activity: Decide what is done about a reported defect, and record the repair and the return to service
    for:
      records: registers/vehicle-defects.md
      due: 24h after reported_on
      key: reference
    authority: >
      O. Reg. 199/07 — the operator must repair a defect reported to it, and a
      vehicle with a major defect must not be driven until the defect is
      repaired. Neither the regulation nor the Code sets a deadline for the
      decision or for the repair. The twenty-four hours is this organisation's,
      and it is a deadline on the DECISION rather than on the work: a major
      defect has already stopped the vehicle, and a minor one that nobody has
      decided about within a day is a minor defect nobody is tracking.
    interval_basis: chosen
    responsible: maintenance-lead
    applies_to: the organisation
    records: registers/defect-repairs.md
    escalate: {after: 48h, to: fleet-manager}
    satisfies:
      - hta_ontario:HTA-TRIP-06
      - hta_ontario:HTA-PMVI-04
      - nsc_ca:NSC-11
  register:
    title: Defect Repair Record
    note: >
      One row per defect decided about. `decision` and `repaired_on` are
      separate columns because deciding and doing are separate acts, and the
      whole value of this register is the interval between them.
      `returned_to_service_by` is required for a major defect and is the
      signature that matters: it is the moment somebody took responsibility for
      the vehicle being fit to drive again.
    layout: form
    review: required
    approvers: [maintenance-lead]
    columns:
      - {key: defect, label: Defect, type: relation, required: true,
         target: /registers/vehicle-defects.md#records, display: reference}
      - {key: vehicle, label: Vehicle, type: relation, required: true,
         target: /registers/vehicles.md#records, display: unit_number}
      - {key: decided_on, label: Decision made on, type: date, required: true}
      - {key: decided_by, label: Decided by, type: user, required: true}
      - {key: decision, label: Decision, type: select, required: true,
         options: ["Repair now — the vehicle is out of service until it is done",
                   "Repair now — minor defect, the vehicle may continue",
                   "Defer — minor defect, controlled, with a date",
                   "Not a defect — with the reason recorded",
                   "Vehicle withdrawn from service permanently"]}
      - {key: deferred_until, label: Deferred until, type: date}
      - {key: work_done, label: What was done, type: longtext}
      - {key: repaired_on, label: Repaired on, type: date}
      - {key: repaired_by, label: Repaired by, type: text}
      - {key: repairer_type, label: Who carried out the work, type: select,
         options: ["Own shop", "Licensed motor vehicle inspection station",
                   "Other third-party shop", "Roadside or mobile repair", Other]}
      - {key: parts, label: Parts fitted, type: longtext}
      - {key: cost, label: Cost, type: currency}
      - {key: invoice_reference, label: Invoice or work order number, type: text}
      - {key: returned_to_service_on, label: Returned to service on, type: date}
      - {key: returned_to_service_by, label: Returned to service by, type: user}
      - {key: verification, label: How it was verified before the vehicle moved, type: longtext}
      - {key: attachment, label: Work order or invoice, type: attachment}
    retention:
      keep: 2y
      authority: >
        No retention period is prescribed for a repair record in O. Reg. 199/07.
        A facility audit under National Safety Code Standard 15 examines the
        operator's records over a review period of up to two years, so two years
        is this organisation's choice, set to cover it.
      reason: The repair record is what shows that a defect reported on a trip inspection was actually answered.
---

What this document must establish for THIS organisation: what happens between a
defect being reported and the vehicle moving again, and who says it may.

**The obligation is on the decision, not on the wrench.** A defect is raised at
a moment and has no period, so the work is triggered by the row rather than by a
calendar. Twenty-four hours is long enough to get a fitter to look at it and
short enough that a minor defect cannot quietly become a permanent condition of
the vehicle. The regulation sets no deadline at all, and the procedure should
say so rather than implying otherwise.

**A major defect has already stopped the vehicle before this procedure
starts.** There is no decision to make about whether it may be driven; the only
decisions are what is done, by whom, and who says it is fit again. The
procedure must name the position that may return a vehicle to service and say
what evidence they act on. That is the decision nobody writes down, and it is
the one that is examined after a wheel-off.

**Deferring a minor defect is lawful, and it must be recorded as a decision
rather than as an absence.** "Deferred — minor and controlled" needs a date and
a name against it. A defect register in which deferrals look identical to
forgotten items is a register that reports a clean fleet for a fleet nobody is
maintaining.

**"Not a defect" is a determination and must be defensible.** It is the option
that will be reached for under pressure, and the procedure should require the
reason to be written and the same person not to be both the reporter and the
dismisser.

**The repair is also the moment the defect is diagnosed as a pattern or not.**
Where the same system on the same vehicle, or the same system across the fleet,
keeps generating defects, the answer is the maintenance programme rather than
another repair — and the procedure must route that to the monthly compliance
review instead of leaving it to whoever happens to notice.

**Where the work is done matters to the record.** A repair by a licensed motor
vehicle inspection station, by the organisation's own shop, or at the roadside
produce different documents, and the one an auditor will ask for is the
document from the third party. `attachment` exists so the invoice sits with the
record instead of in an accounts folder organised by supplier.
