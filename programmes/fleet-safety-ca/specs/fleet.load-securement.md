---
id: fleet.load-securement
kind: procedure
title: Load Securement
structure: procedure
path: procedures/load-securement.md

satisfies:
  - hta_ontario:HTA-LOAD-01
  - hta_ontario:HTA-LOAD-02
  - hta_ontario:HTA-LOAD-03
  - hta_ontario:HTA-LOAD-04
  - hta_ontario:HTA-LOAD-05
  - hta_ontario:HTA-CVOR-03
  - nsc_ca:NSC-10
  - cor_2020:COR-07
  - iso_45001:8.1.2

requires: [fleet.policy, fleet.vehicles, fleet.drivers]

declares:
  obligation:
    id: fleet.securement-check
    activity: Supervisory check of the securement equipment carried on the vehicle and of how loads on it are actually secured
    cadence: each quarter
    authority: >
      O. Reg. 363/04 (Security of Loads), Ontario's adoption of National Safety
      Code Standard 10 — cargo must be contained, immobilised or secured, the
      securement system must withstand the prescribed forces, and the DRIVER
      must inspect the load before driving and re-examine it within the first
      80 km and thereafter at intervals of no more than 3 hours or 240 km. Those
      are per-trip duties on the driver and they are not this obligation. What
      the regulation does NOT require is any periodic supervisory verification
      that the equipment is serviceable and the practice is right. The quarter
      is this organisation's, chosen because working load limits are only
      countable while the markings are legible and straps degrade in service.
    interval_basis: chosen
    responsible: fleet-manager
    applies_to: the organisation
    per:
      listed_in: registers/vehicles.md
      key: unit_number
      label: description
      from: in_service_on
      until: out_of_service_on
    records: registers/load-securement-checks.md
    escalate: {after: 4w, to: fleet-manager}
    satisfies:
      - hta_ontario:HTA-LOAD-02
      - hta_ontario:HTA-LOAD-05
      - nsc_ca:NSC-10
  register:
    title: Load Securement Check Record
    note: >
      One row per vehicle per quarter. `aggregate_wll` and `markings_legible`
      are asked together because a tiedown whose marking cannot be read has no
      working load limit that can be counted toward the aggregate — which is the
      commonest way a load that looks over-secured is not secured at all.
      Damaged equipment found here is raised as a DEFECT in the defect register
      rather than being noted and quietly replaced, so that the repair
      obligation sees it.
    layout: form
    review: required
    approvers: [fleet-manager]
    columns:
      - {key: vehicle, label: Vehicle, type: relation, required: true,
         target: /registers/vehicles.md#records, display: unit_number}
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: driver_observed, label: Driver observed, type: relation,
         target: /registers/drivers.md#records, display: driver_id}
      - {key: typical_cargo, label: What this vehicle actually carries, type: longtext, required: true}
      - {key: commodity_specific_rules, label: Commodity-specific rules that apply, type: select, required: true,
         options: ["None — the general duty only",
                   "Heavy vehicles, equipment and machinery",
                   "Dressed lumber or building materials",
                   "Metal coils, pipe or structural steel",
                   "Intermodal containers",
                   "Aggregate, soil or demolition debris — general duty, tarp and tailgate",
                   Other]}
      - {key: tiedowns_count, label: Tiedowns carried, type: int, required: true}
      - {key: markings_legible, label: Every tiedown's working load limit marking is legible, type: bool, required: true}
      - {key: aggregate_wll, label: Aggregate working load limit of the tiedowns carried (kg), type: int}
      - {key: heaviest_load_kg, label: Heaviest load this vehicle carries (kg), type: int}
      - {key: aggregate_sufficient, label: The aggregate is at least half the weight of the heaviest load, type: select, required: true,
         options: ["Yes", "No", "Cannot be determined — markings or weights unknown"]}
      - {key: equipment_condition, label: Condition of straps, chains, binders, edge protection and tarps, type: longtext, required: true}
      - {key: damaged_equipment_withdrawn, label: Damaged equipment withdrawn from use, type: bool, required: true}
      - {key: defects_raised, label: Defect numbers raised in the defect register, type: text}
      - {key: load_observed, label: A loaded vehicle was observed, type: bool, required: true}
      - {key: minimum_tiedowns_met, label: The minimum tiedown count was met on the load observed, type: select, required: true,
         options: ["Yes", "No", "No load was observed"]}
      - {key: accessory_equipment_secured, label: Booms, blades, buckets and outriggers lowered and secured separately, type: select, required: true,
         options: ["Yes", "No", "Not applicable to this vehicle"]}
      - {key: driver_knows_recheck_rule, label: The driver could state the 80 km and 3 hour or 240 km re-examination rule, type: bool, required: true}
      - {key: findings, label: Findings, type: longtext, required: true}
      - {key: actions, label: Actions, with owners and dates, type: longtext}
---

What this document must establish for THIS organisation: what it actually
carries, how each of those things is secured, and who checks that the equipment
on the truck can do it.

**The duty is about the outcome, not about the equipment.** Cargo must be
contained, immobilised or secured so that it cannot leak, spill, blow off, fall
from, fall through or be dislodged, and cannot shift so as to affect the
vehicle's stability or manoeuvrability. A load with the right number of straps
that can still shift is not secured. The procedure must say that in those terms,
because the counting rules invite the opposite belief.

**The numbers are the floor and the performance criteria are the rule.** The
securement system must withstand 0.8 g forward, 0.5 g rearward and 0.5 g
lateral without the cargo shifting, and the aggregate working load limit of the
tiedowns must be at least **half the weight** of the cargo they secure. An
article not blocked against forward movement needs at least one tiedown at
1.52 m or less and 500 kg or less, at least two if it is longer or heavier, and
one more for every further 3.04 m or part of it. Meeting the count does not
establish that a load is secured; failing it establishes that it is not.

**Working load limit is not breaking strength, and an unmarked strap counts for
nothing.** The working load limit is marked on the tiedown by its manufacturer.
A strap whose label has worn off has no working load limit that can be counted
toward the aggregate — so a truck carrying twelve straps, four of them
unreadable, is carrying eight. This is the single most common way a load that
looks over-secured is not, and it is why the quarterly check looks at markings
before it looks at anything else.

**For a contractor, the commodity rule that bites is heavy equipment.** An item
over the prescribed weight must be restrained at a minimum of four separate
points against movement in every direction, and accessory equipment — a boom, a
blade, a bucket, an outrigger — must be lowered and secured **separately from
the machine itself**. The second half is the one that is skipped, and it is the
one that comes off.

**Aggregate, soil and demolition debris are not on the commodity list**, and
they are not therefore unregulated: they fall under the general duty, where the
operative words are *leak, spill or blow off*. A loaded dump box is a securement
question about the tarp and the tailgate rather than about straps, and a
procedure that only discusses tiedowns has nothing to say about the majority of
this fleet's loads.

**The driver's re-examination duties are per trip and belong in the driver's
hands.** The load is inspected before driving, re-examined within the first
80 km, and thereafter at intervals of no more than 3 hours or 240 km or at each
change of duty status, whichever comes first. The first re-examination exists
because tiedowns bed in and go slack over the first few kilometres. On a local
haul of under 80 km **it never falls due at all**, which means the pre-trip
check is the only one there will be — the procedure must say so plainly rather
than letting a driver assume the rule protects them.

**This quarterly check is the organisation's, not the regulation's.** Its
purpose is to catch what a per-trip duty cannot: equipment degrading, markings
wearing off, and a practice that has drifted. It is written as an observation of
a real load wherever one can be observed, because a check of the strap locker
finds none of that.
