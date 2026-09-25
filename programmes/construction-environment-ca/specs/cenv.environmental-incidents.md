---
id: cenv.environmental-incidents
kind: register
title: Register of Environmental Incidents
structure: standard
path: registers/environmental-incidents.md

# A register carries no `satisfies:`. The reporting duty belongs to
# cenv.spill-reporting, which declares the obligation these rows trigger.

requires: [cenv.policy]

register:
  title: Register of Environmental Incidents
  note: >
    One row per spill, discharge or escape — every one, including the ones that
    turn out not to be reportable. The register is deliberately wider than the
    word "spill": the Environmental Protection Act's Part X duty is about a
    pollutant spilled from a container, s. 15 catches a discharge of a
    contaminant out of the normal course of events whether or not anything
    spilled, and the Ontario Water Resources Act s. 30 catches material escaping
    from a person's control into or near any waters. Sediment-laden water
    reaching a roadside ditch engages the third and neither of the first two, and
    a register built around the word "spill" will not have a row for it.
    A row is opened on discovery, by whoever discovered it, before anybody has
    decided whether it is reportable. That decision is the next artifact's, and a
    register that only accepts confirmed reportable spills has thrown away the
    evidence that the decision was ever made.
  columns:
    - {key: incident_id, label: Incident reference, type: text, required: true}
    - {key: discovered_on, label: Discovered on, type: date, required: true}
    - {key: discovered_time, label: Time discovered, type: text, required: true}
    - {key: occurred_on, label: Occurred on, if different, type: date}
    - {key: discovered_by, label: Discovered by, type: text, required: true}
    - {key: location, label: Where it happened, type: text, required: true}
    - {key: project, label: Construction project, type: relation,
       target: /registers/projects.md#records, display: project_id}
    - {key: area, label: Project area, type: relation,
       target: /registers/excavation-projects.md#records, display: area_id}
    - {key: category, label: What kind of incident, type: select, required: true,
       options: ["Spill of a pollutant from a container, vehicle or structure",
                 "Discharge to water, or on a shore or bank",
                 "Discharge to land",
                 "Discharge to air — dust, odour, smoke",
                 "Discharge of noise or vibration",
                 "Sediment-laden water leaving the site",
                 "Escape of material from our control",
                 "Uncontrolled dewatering discharge",
                 "Near miss — contained on a prepared surface"]}
    - {key: substance, label: What was discharged, type: text, required: true}
    - {key: estimated_quantity, label: Estimated quantity, type: text, required: true}
    - {key: source, label: Where it came from, type: text, required: true}
    - {key: whose_pollutant, label: Owner of the pollutant, type: text}
    - {key: control_of_pollutant, label: Who had control of it, type: text, required: true}
    - {key: entered_water, label: Reached, or may reach, any waters, type: bool, required: true}
    - {key: pathway, label: Drainage or migration pathway, type: longtext}
    - {key: adverse_effect, label: Adverse effect that occurred, or may occur, type: longtext, required: true}
    - {key: immediate_actions, label: What was done in the first hour, type: longtext, required: true}
    - {key: contained_on, label: Contained on, type: date}
    - {key: third_party_involved, label: A sub-trade, hauler or supplier was involved, type: bool, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: ["Open — response under way",
                 "Open — reported, remediation under way",
                 "Remediation complete, awaiting confirmation",
                 "Closed",
                 "Closed — not reportable, record kept"]}
    - {key: photographs, label: Photographs, type: attachment}
    - {key: note, label: Note, type: longtext}
---

What this artifact must establish for THIS organisation: a single place where
every environmental incident is recorded at the moment it is discovered, by the
person who discovered it, with no gate in front of it.

It exists because **the duty to report is owed forthwith and the decision to
report is made by somebody who is not there.** The person who sees hydraulic oil
in a trench is not the person who can say whether O. Reg. 675/98 exempts it, and
a register that asks them to make that call before they may open a row will
receive nothing. So the row records what happened; whether it was reportable, and
whether it was reported, belongs to the spill reporting record and not here.

**`discovered_on` and `discovered_time` are both required and they are the
load-bearing fields.** Every duty in this area runs from knowledge: the s. 92
notification duty takes effect "the moment the person knows or ought to know",
and the s. 93 duty to mitigate and restore takes effect on the same footing,
independently of whether anybody was notified. A record with a date and no time
cannot show that a call made at 14:20 followed a discovery at 14:05, which is the
entire question. `occurred_on` is separate and frequently unknown — a leaking
drum found on a Monday may have been leaking since Friday — and guessing it into
the discovery field destroys the only defensible fact in the row.

**`entered_water` is a boolean and it is asked of every row**, because it decides
which statute is engaged. The *Ontario Water Resources Act* s. 30 is not a
subset of the *Environmental Protection Act*: it reaches any material of any kind
discharged into or in any waters, on a shore or bank, or into any place that may
impair the quality of any waters, and "may impair" does not require impairment to
be proved. A construction organisation's most frequent engagement with it is not
fuel — it is turbid water, and nobody calls turbid water a spill.

**`category` includes near misses and noise, and that is deliberate.** A
contaminant under s. 14 reaches dust, odour, noise and vibration, so the register
must have somewhere to put the complaint from the house beside the site at
06:30. A near miss contained on a prepared surface is recorded because the
675/98 exemption for motor vehicle fluid depends on exactly that fact and on
remediation being arranged and carried out immediately — the exemption is proved
by the record, and an unreported exempt spill has its own two-year retention.

**`third_party_involved` exists because a sub-trade's spill is this
organisation's problem more often than the contract suggests.** The duty under
s. 92 falls on the person having control of the pollutant *and* on the person who
spills or causes or permits a spill, and control includes an employee or agent.
A hauler tipping the wrong load in the wrong place does not become somebody
else's incident because there is an indemnity in the subcontract.
