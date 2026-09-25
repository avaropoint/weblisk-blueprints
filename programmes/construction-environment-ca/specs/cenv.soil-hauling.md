---
id: cenv.soil-hauling
kind: procedure
title: Excess Soil Hauling and Tracking
structure: procedure
path: procedures/excess-soil-hauling-and-tracking.md

satisfies:
  - o_reg_406_19:16
  - o_reg_406_19:17
  - o_reg_406_19:18
  - o_reg_406_19:18.1
  - o_reg_406_19:22

requires: [cenv.excess-soil-registry, cenv.soil-destinations]

declares:
  obligation:
    id: cenv.soil-hauling
    activity: Hauling records and tracking-system entries for the project area reconciled against the loads that left it, and every destination confirmed as one the filed notice names
    cadence: monthly
    per:
      listed_in: registers/excavation-projects.md
      key: area_id
      label: address
      from: excavation_start_on
      until: soil_removal_complete_on
    authority: >
      O. Reg. 406/19 s. 16 requires the tracking system to be developed and
      applied BEFORE soil is removed, and s. 18 requires a hauling record per
      load, created and confirmed as accurate by the owner or operator of the
      loading site before the load leaves and completed on arrival. Neither sets
      any interval for checking that the records exist. Monthly is this
      organisation's, chosen because a hauling record is completed by a third
      party at the far end and a month is the longest gap after which a missing
      acknowledgement can still be chased to a driver who remembers the load
    interval_basis: chosen
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/soil-tracking-reconciliations.md
    escalate: {after: 2w, to: project-manager}
  register:
    title: Excess Soil Tracking Reconciliation
    note: >
      One row per project area per month while soil is being removed from it.
      This is not the hauling record: the hauling record travels with the load,
      is created per load, and lives in the tracking system. This is the monthly
      act of checking that the tracking system agrees with what left the site —
      the count that went out against the count that arrived and was
      acknowledged. `loads_missing_an_acknowledgement` is the number that matters
      and it is recorded rather than described, because a load that left here and
      was never acknowledged there is the one fact in this programme that can
      mean soil went somewhere nobody has written down.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 7y
      authority: O. Reg. 406/19 s. 28 (1) — every document and record created or acquired under the Regulation is retained for at least seven years after it is created or acquired. Section 28 (4) sets a shorter period of two years for the hauling records themselves, measured from when the soil was loaded
      reason: >
        Two periods, deliberately not blended. The hauling records are kept for
        the two years the Regulation gives them; this reconciliation is a record
        created under the Regulation and is kept for seven, because it is the
        document that shows the two-year records were being looked at while they
        still existed.
    columns:
      - {key: area, label: Project area, type: relation, required: true,
         target: /registers/excavation-projects.md#records, display: area_id}
      - {key: period, label: Month reconciled, type: text, required: true}
      - {key: reconciled_on, label: Reconciled on, type: date, required: true}
      - {key: tracking_system, label: How loads are tracked, type: select, required: true,
         options: ["Electronic tracking system", "Paper hauling records", "Both",
                   "No notice is owed for this project area — s. 16 does not apply"]}
      - {key: loads_removed, label: Loads removed in the period, type: int, required: true}
      - {key: loads_with_a_record, label: Loads with a hauling record created before leaving, type: int, required: true}
      - {key: loads_missing_an_acknowledgement, label: Loads never acknowledged at the destination, type: int, required: true}
      - {key: loads_exempt, label: Loads exempt under s. 18 (5 m3 or less of dry soil, or a packaged product), type: int}
      - {key: destination, label: Principal destination in the period, type: relation,
         target: /registers/soil-destinations.md#records, display: site_id}
      - {key: destinations_match_the_notice, label: Every destination used is one the filed notice names, type: bool, required: true}
      - {key: unmatched_destinations, label: Destinations used that the notice does not name, type: longtext}
      - {key: contingency_communicated, label: Contingency measures communicated to every driver, type: bool, required: true}
      - {key: vehicles_compliant, label: Vehicles leakproof, covered and fit for the load, type: bool, required: true}
      - {key: landfill_deposits, label: Loads deposited at a landfill or dump, type: int}
      - {key: landfill_declarations_held, label: Qualified person's s. 22 declaration held for each landfill deposit, type: select,
         options: ["Held for every load", "Not required — the soil was used for cover, roads, berms or an ancillary use",
                   "Not required — no landfill deposits", "Outstanding"]}
      - {key: reconciled_by, label: Reconciled by, type: user}
      - {key: action_taken, label: What was done about what did not reconcile, type: longtext}
      - {key: evidence, label: Extract from the tracking system, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: how a load of excess
soil is recorded before it leaves, how it is acknowledged when it arrives, and
who notices when the two do not meet.

It must set out **the hauling record as s. 18 sets it out**, because the section
is specific and the industry's habit is a weigh ticket. The record must be
available at all times during transportation and must carry the loading location,
the date and time of loading, the quantity, whether the load includes
salt-impacted or asphalt-impacted soil, a **named contact at the loading site who
can answer questions about the soil quality**, the transporting firm, the driver
and the vehicle plate, the destination, and a named contact there. Before the
load leaves, the owner or operator of the loading site must ensure the record has
been created and must **confirm in it that the information is accurate** — a
positive act by this organisation, not the hauler's paperwork. On arrival the
record is completed with the date and time of deposit, the name and telephone
number of the individual who acknowledges it, and that individual's declaration
of the deposit, and a copy goes to both contacts.

**Section 18 is owed whatever the volume and whether or not a notice was filed.**
This is the single most consequential sentence in this procedure. The Registry
regime in s. 8 is triggered and mostly does not apply; the hauling record is a
duty on the owner or operator of the site where the soil is loaded, with only two
narrow exceptions — 5 m³ or less of dry excess soil, and soil packaged as a
landscaping or gardening product — and even then the information must be given to
a provincial officer on request. An organisation that reads "no notice is owed"
as "no paperwork is owed" has the exemptions exactly backwards, and it is the
commonest error in this area.

**The tracking system under s. 16 is a different duty from the record under
s. 18**, and it is owed only where a notice is required. It must be developed and
applied *before* soil is removed and must track each load through transportation
and deposit, including movements to and from a Class 2 soil management site. The
procedure must say which system this organisation uses and who administers it.

It must cover **s. 18.1**, which is one sentence and is almost never done: the
owner or operator of the loading site must identify the contingency measures if
the soil cannot be deposited where the record says — an alternate site, or the
circumstances in which the load comes back — and must **communicate them to the
driver**. Not to the hauling firm's office. To the person driving.

It must cover **s. 17**, the vehicle itself: constructed so the soil can be
transferred safely and without nuisance, leakproof, able to withstand abrasion
and corrosion, and covered where necessary to stop material falling or blowing or
dust being released. Liquid soil adds lockable valves, locked when unattended,
and the owner or operator present at every transfer.

It must state the **s. 22 prohibition** plainly, because it is where money and
law disagree. Reusable excess soil may not be deposited at a landfill or dump
unless it is going to daily or final cover, roads, berms or another ancillary use
supporting the site, or unless a qualified person has determined that one of
three grounds makes reuse inappropriate — a parameter with no applicable standard
where final placement may cause an adverse effect, invasive species that should
not be relocated, or soil unsuitable as structural fill for which reasonable
efforts found no reuse site — and has completed a declaration and given it to the
landfill's operator. Those declarations are held for two years after deposit.

**Monthly is ours and the law's interval is none.** The regulation asks for a
record per load and a system that tracks them; it never asks anybody to look. A
reconciliation that happens only when a provincial officer asks is one that
discovers a missing acknowledgement eighteen months after the driver who could
have explained it left the firm.
