---
id: cenv.registry-closeout
kind: procedure
title: Excess Soil Registry Updating and Close-Out
structure: procedure
path: procedures/excess-soil-registry-close-out.md

satisfies:
  - o_reg_406_19:9
  - o_reg_406_19:27

requires: [cenv.excess-soil-registry]

declares:
  obligation:
    id: cenv.registry-closeout
    activity: Filed Registry notice updated with what was actually deposited and where, and closed out
    for:
      records: registers/excavation-projects.md
      due: 30d after soil_removal_complete_on
      key: area_id
    authority: >
      O. Reg. 406/19 s. 9 (2) — within 30 days after all soil that will become
      excess soil has been removed from the project area, the notice must be
      updated with the amount deposited at each class of destination and the date
      of the last load. Section 9 (3) requires an update within 30 days of
      becoming aware that the notice is no longer complete or accurate
    interval_basis: required
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/excess-soil-registry-updates.md
    escalate: {after: 1w, to: project-manager}
  register:
    title: Excess Soil Registry Update Record
    note: >
      One row per project area per update, including the close-out. There is
      usually more than one: the destinations in a filed notice have to be
      corrected before soil is deposited anywhere the notice does not name, and
      the close-out comes last. The row that matters most is the one nobody
      files — `within_30_days` exists so that a late close-out is recorded as
      late rather than as done.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 7y
      authority: O. Reg. 406/19 s. 28 (1) — every document and record created or acquired under the Regulation is retained for at least seven years after it is created or acquired
      reason: >
        The close-out is the last thing this organisation does on a project area
        and the first thing a purchaser's consultant asks for. Seven years runs
        from the record's creation, which is the end of the job, so it is also
        the longest-lived record in the programme.
    columns:
      - {key: area, label: Project area, type: relation, required: true,
         target: /registers/excavation-projects.md#records, display: area_id}
      - {key: registry_number, label: Registry notice number, type: text}
      - {key: update_type, label: Why the notice was updated, type: select, required: true,
         options: ["Close-out — all excess soil has been removed",
                   "Destination corrected before deposit",
                   "Volume or soil quality changed",
                   "Project leader or qualified person changed",
                   "Correction after becoming aware the notice was inaccurate",
                   "No update required — no notice was filed for this project area",
                   "No update required — we are not the project leader"]}
      - {key: became_aware_on, label: Date the circumstance became known, type: date}
      - {key: last_load_on, label: Date of the last load removed, type: date}
      - {key: updated_on, label: Notice updated on, type: date}
      - {key: within_30_days, label: Updated within the 30 days the Regulation allows, type: bool, required: true}
      - {key: volume_reuse_m3, label: Deposited at reuse sites, in cubic metres, type: number}
      - {key: volume_class1_m3, label: Deposited at Class 1 soil management sites, in cubic metres, type: number}
      - {key: volume_class2_m3, label: Deposited at Class 2 soil management sites, in cubic metres, type: number}
      - {key: volume_transfer_m3, label: Deposited at local waste transfer facilities, in cubic metres, type: number}
      - {key: volume_landfill_m3, label: Deposited at landfilling sites or dumps, in cubic metres, type: number}
      - {key: destinations_as_filed, label: Every destination used was named in the notice before deposit, type: bool, required: true}
      - {key: updated_by, label: Updated by, type: user}
      - {key: evidence, label: Copy of the updated notice, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: who goes back to a
Registry notice after the job has moved on, what they put in it, and how the
thirty days are counted.

It exists because **the close-out is the most commonly missed obligation in the
regulation, and the reason is structural rather than cultural.** Every other duty
in O. Reg. 406/19 falls due while somebody is standing on the site wanting to
move soil. This one falls due thirty days after the last truck, when the crew has
gone to the next job, the project manager's attention went with them, and nothing
on any site is waiting for it. A programme that does not raise it on a clock of
its own will not raise it at all.

It must state the three separate duties in **s. 9** rather than collapsing them
into "update the notice":

- **Before depositing** excess soil at any Class 1 or Class 2 soil management
  site, reuse site, local waste transfer facility, landfilling site or dump, the
  project leader must ensure the destination information in the filed notice **is
  the information for the actual location**. This is not a thirty-day duty. It is
  owed before the load is tipped, and it is the duty that a change of destination
  on a Friday afternoon breaks.
- **Within 30 days** after all soil that will become excess soil has been removed
  from the project area, the local waste transfer facility or the Class 2 soil
  management site, the notice is updated with the **amount deposited at each
  class of destination** and the **date of the last load**.
- **Within 30 days of becoming aware** that the notice is no longer complete or
  accurate, it is updated. The clock runs from awareness, which is why the
  register records the date the circumstance became known separately from the
  date it was acted on.

**The thirty days is the regulation's and it is marked `required`.** Nothing here
is this organisation's judgement. What is this organisation's is the decision to
be told about it, and the trigger is the last load rather than the end of the
contract — a project area can finish removing soil months before the job is
handed over, and the clock does not wait for practical completion.

It must say **who holds the volumes**, because this is where the close-out
actually fails. The amount deposited at each class of destination is a number
that has to come from the tracking system and the hauling records, per class, and
nobody can produce it from memory in the thirty-first day. The procedure must
require the figures to be carried forward from the monthly reconciliation rather
than assembled at the end, and must say so in terms.

It must name the case where **nothing is owed and a row is still created.** A
project area with no notice has no close-out, and recording "no update required"
against it is what distinguishes a determination that was made from a duty that
was forgotten. A blank is not an answer.

It must state the **form** requirement in s. 27: a notice, and any declaration,
document or record under the Regulation or the Soil Rules, is prepared in the
form approved by the Director where one has been approved. An update written in
this organisation's own words into a field that expects the Director's form is an
update the Registry may not accept, and the thirty days does not pause while that
is sorted out.
