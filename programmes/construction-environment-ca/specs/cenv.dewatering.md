---
id: cenv.dewatering
kind: procedure
title: Dewatering and Discharge
structure: procedure
path: procedures/dewatering-and-discharge.md

satisfies:
  - owra_ontario:30
  - owra_ontario:34
  - owra_ontario:53
  - epa_ontario:20.21
  - epa_ontario:14

requires: [cenv.dewatering-operations, cenv.approvals-determination]

declares:
  obligation:
    id: cenv.dewatering
    activity: Each operating discharge inspected, its volume recorded, and its water quality checked against what the instrument and the receiving body will take
    cadence: weekly
    per:
      listed_in: registers/dewatering-operations.md
      key: operation_id
      label: discharge_point
      from: started_on
      until: ended_on
    authority: >
      Ontario Water Resources Act s. 30 makes it an offence to discharge material
      of any kind into or in any waters, on a shore or bank, or into any place
      that may impair the quality of any waters, and sets no monitoring interval
      whatever. O. Reg. 63/16 requires daily volumes to be recorded for a
      registered taking and reported annually, and an instrument's own conditions
      set whatever frequency they set. Weekly is this organisation's floor where
      nothing else applies. WHERE AN INSTRUMENT SETS A FREQUENCY, THAT FREQUENCY
      GOVERNS, and this obligation confirms it happened rather than replacing it
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: the organisation
    records: registers/dewatering-discharge-checks.md
    escalate: {after: 3d, to: environmental-lead}
  register:
    title: Dewatering Discharge Check
    note: >
      One row per dewatering operation per week while it is running. The
      water-quality columns are deliberately a mix: a required visual
      observation anybody can make, and optional instrument readings for the
      operations whose instrument asks for them. A register that demanded a
      turbidity meter reading from a labourer with a sump pump would be filled in
      with invented numbers, and invented numbers in a compliance record are
      worse than an honest visual note. `discharge_reaching_water` and
      `exceeded_the_permitted_rate` are the two fields that can describe an
      offence, and both are required.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 5y
      authority: O. Reg. 63/16 requires records relating to an activity registered in the Environmental Activity and Sector Registry, including the record of daily volumes taken, to be retained for five years
      reason: >
        Five years is the prescribed period for the instrument these checks most
        often sit under, and it is applied to all of them rather than sorted by
        which instrument a row cites. Where a permit to take water imposes a
        longer period, the permit's period governs and the procedure says so.
    columns:
      - {key: operation, label: Dewatering operation, type: relation, required: true,
         target: /registers/dewatering-operations.md#records, display: operation_id}
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: checked_by, label: Checked by, type: user}
      - {key: running, label: The discharge was running at the time of the check, type: bool, required: true}
      - {key: volume_taken_litres, label: Highest daily volume taken in the week, in litres, type: number, required: true}
      - {key: daily_volumes_recorded, label: Daily volumes recorded for every day of the week, type: bool, required: true}
      - {key: exceeded_the_permitted_rate, label: The taking exceeded what the instrument permits, type: bool, required: true}
      - {key: clarity, label: Appearance of the discharge, type: select, required: true,
         options: ["Clear",
                   "Slightly turbid",
                   "Visibly turbid — discharge stopped",
                   "Sheen, colour or odour present — discharge stopped",
                   "Not running at the time of the check"]}
      - {key: turbidity_ntu, label: Turbidity, in NTU, type: number}
      - {key: total_suspended_solids, label: Total suspended solids, in mg/L, type: number}
      - {key: ph, label: pH, type: number}
      - {key: sample_taken, label: A sample was taken and sent for analysis, type: bool, required: true}
      - {key: within_limits, label: Results within every limit the instrument or the by-law sets, type: select, required: true,
         options: ["Within limits", "Outside a limit — reported", "Outside a limit — not yet reported",
                   "No limits are set for this discharge", "Awaiting results"]}
      - {key: treatment_condition, label: Condition of the settling, filtration and flocculation in use, type: longtext, required: true}
      - {key: erosion_controls_intact, label: Erosion and sediment controls at the discharge point intact, type: bool, required: true}
      - {key: discharge_reaching_water, label: Sediment or discoloured water is reaching a watercourse, ditch or sewer, type: bool, required: true}
      - {key: incident_raised, label: An environmental incident was raised, type: relation,
         target: /registers/environmental-incidents.md#records, display: incident_id}
      - {key: action_taken, label: What was done, type: longtext}
      - {key: photographs, label: Photographs of the discharge point, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: how water taken out of
an excavation is treated, where it is allowed to go, who looks at it, and what
stops it.

It must state the **two separate prohibitions** and never let them merge. Taking
is governed by OWRA s. 34: more than 50,000 litres on any day requires a permit,
unless the activity is instead registered in the Environmental Activity and
Sector Registry under O. Reg. 63/16, which is the route prescribed for taking
ground water or storm water to create or maintain a dewatered work area within a
construction site. Discharge is governed by OWRA s. 30, which is an offence
provision with no threshold at all: discharging any material of any kind into or
in any waters, on a shore or bank, or into any place that **may impair** the
quality of any waters. A site can be perfectly authorised to take the water and
committing an offence with what it does next.

**The most likely offence this organisation will ever commit is turbid water in a
ditch, and it will not feel like one.** It is sediment, not a chemical; the pump
is running as designed; nobody has spilled anything. Section 30 does not require
impairment to be proved, and the notification duty in the same section — forthwith,
to the Ministry, for a discharge not in the normal course of events or material
escaping from a person's control — is engaged by it. The procedure must say in
terms that a discharge running visibly dirty is stopped first and reported
second, and that it is an environmental incident.

It must set out **the treatment train** this organisation actually uses —
settling tanks, filter bags, flocculant, a vegetated discharge area — and the
one thing about each of them that makes it stop working: a settling tank that has
filled with sediment is a pipe, a filter bag left in place past its life bursts,
and a flocculant used off-label is itself a material discharged into waters.

It must state that **the sewage works question is answered before the pump runs,
not after.** The pumps, tanks, filter bags and pipework that collect, settle,
filter and discharge water from a dewatered excavation are **sewage works** and
need an approval under OWRA s. 53, unless the activity is instead covered by the
Registry registration. And a **discharge to a municipal storm or sanitary sewer
engages a separate consent from the municipality** under its sewer-use by-law,
which the provincial instrument does not supply and which frequently carries
tighter limits than the province's.

**Weekly is this organisation's floor and it is not the answer where an
instrument speaks.** A registration under O. Reg. 63/16 requires daily volumes to
be recorded; a permit to take water sets its own monitoring; a municipal consent
sets sampling frequencies and limits of its own. Where any of those applies, its
frequency governs and this weekly check exists to confirm that it happened. The
declaration says `interval_basis: chosen` because the week is ours; it must never
be read as saying the instrument's frequency is optional.

**Where the check finds sediment reaching water, the row is not the end of it.**
`discharge_reaching_water` is a required boolean because it is the trigger for a
different duty entirely — an environmental incident, a notification, and the
s. 93 duty to do everything practicable to prevent, eliminate and ameliorate.
The register carries a relation onto the incident so the two records join, and
the procedure must say who raises it, because a supervisor who has just stopped a
pump at four on a Friday will not go looking for a second form.
