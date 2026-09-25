---
id: cenv.soil-observations
kind: register
title: Register of Observations Suggesting Soil Contamination
structure: standard
path: registers/soil-contamination-observations.md

# A register carries no `satisfies:`. The duty to have a written procedure and
# to apply it belongs to cenv.contaminated-soil-response, which declares the
# obligation these rows trigger.

requires: [cenv.excavation-projects]

register:
  title: Register of Observations Suggesting Soil Contamination
  note: >
    One row per observation made during excavation that suggests the soil may be
    affected by the discharge of a contaminant — a stain, an odour, a sheen,
    buried drums, a reading on a field instrument. This register is deliberately
    NOT the environmental incident register. An incident is something this
    organisation did to the environment; an observation is something the ground
    told us, usually about somebody else's history, and it carries a completely
    different response: excavation stops, the project leader is told, and a
    qualified person is asked whether the reuse planning documents still hold.
    Merging the two would raise a qualified person's soil assessment against
    every fuel spill and a spill report against every rusty drum, and a
    programme that asks for work nobody owes is one that gets switched off.
    Rows are opened by whoever saw it, not by whoever will deal with it: an
    observation nobody recorded is the failure this register exists to remove.
  columns:
    - {key: observation_id, label: Observation reference, type: text, required: true}
    - {key: area, label: Project area, type: relation, required: true,
       target: /registers/excavation-projects.md#records, display: area_id}
    - {key: observed_on, label: Observed on, type: date, required: true}
    - {key: observed_time, label: Time observed, type: text}
    - {key: observed_by, label: Observed by, type: text, required: true}
    - {key: location_in_area, label: Where in the project area, type: text, required: true}
    - {key: observation_type, label: What was observed, type: select, required: true,
       options: ["Visual — staining or discolouration",
                 "Visual — buried material, drums, ash or debris",
                 "Olfactory — odour",
                 "Sheen on water in the excavation",
                 "Field screening instrument reading",
                 "Fill of unknown origin",
                 Other]}
    - {key: description, label: What was seen or smelled, type: longtext, required: true}
    - {key: excavation_ceased, label: All excavation in the project area ceased immediately, type: bool, required: true}
    - {key: ceased_at, label: Time excavation ceased, type: text}
    - {key: notified_on, label: Project leader or operator notified on, type: date, required: true}
    - {key: notified_who, label: Who was notified, type: text, required: true}
    - {key: soil_segregated, label: Affected soil identified and segregated, type: bool, required: true}
    - {key: estimated_volume_m3, label: Estimated volume affected, in cubic metres, type: number}
    - {key: qp_documents_required, label: A qualified person's documents were required for this project area, type: bool, required: true}
    - {key: resumed_on, label: Excavation resumed on, type: date}
    - {key: resumed_authorised_by, label: Resumption authorised by, type: text}
    - {key: status, label: Status, type: select, required: true,
       options: [Open — excavation stopped,
                 Open — qualified person engaged,
                 "Closed — contamination confirmed and managed",
                 "Closed — no contamination found",
                 "Closed — outside our project area"]}
    - {key: photographs, label: Photographs, type: attachment}
    - {key: note, label: Note, type: longtext}
---

What this artifact must establish for THIS organisation: that a person who sees
or smells something wrong in an excavation has somewhere to write it down within
minutes, and that writing it down starts a clock rather than ending an
obligation.

It exists because **s. 23 is the duty in O. Reg. 406/19 that is owed on every
project area regardless of volume, regardless of destination and regardless of
whether any notice was ever filed** — and because it is the only duty in the
regulation whose first step is to stop work. The project leader **or** the
operator of the project area must have a written procedure, so this is also the
duty this organisation owes on jobs where somebody else is the project leader and
the rest of the programme is quiet.

**`excavation_ceased` is a required boolean and the honest answer is sometimes
no.** The section requires all excavation in the project area to cease
immediately until the project leader directs otherwise. A register that cannot
record that digging carried on has no value at all: the one thing a later
investigation will ask is when the machine stopped, and a field that only accepts
"yes" answers it dishonestly. The same applies to `resumed_on` — resumption is an
authorised act by a named person, not the absence of a reason to stay stopped.

**`qp_documents_required` decides which of two very different responses
follows.** Where a qualified person's documents were required for the project
area, the project leader must obtain the qualified person's advice on the steps
to be taken and must ask whether any of the documents need revision, **before**
authorising any soil to be removed. Where they were not, the duty is still to
identify and segregate the affected soil, determine the affected portion of the
project area, and dispose of excess soil from it in accordance with the
Regulation — which will very often mean that a project area that owed no notice
now does. Recording the answer on the observation is what lets the programme tell
those two paths apart without a person reading every row.

**The identity is the observation, not the day.** `observation_id` is what the
assessment record cites and it must be stable: two observations on one project
area on one morning are two rows, because they may be two different areas of
potential environmental concern with two different outcomes, and a key made from
a date and a site would silently merge them.
