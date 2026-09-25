---
id: cenv.contaminated-soil-response
kind: procedure
title: Unexpected Soil Contamination
structure: procedure
path: procedures/unexpected-soil-contamination.md

satisfies:
  - o_reg_406_19:23
  - o_reg_406_19:24
  - o_reg_406_19:15

requires: [cenv.soil-observations, cenv.soil-reuse-planning]

declares:
  obligation:
    id: cenv.contaminated-soil-response
    activity: Observation assessed, the affected soil determined and segregated, and the qualified person's documents reviewed and amended
    for:
      records: registers/soil-contamination-observations.md
      due: 30d after observed_on
      key: observation_id
    authority: >
      O. Reg. 406/19 s. 15 (2) — within 30 days of the circumstance becoming
      known, a qualified person shall review all documents prepared under
      sections 11, 12 and 13 and amend them, and give any further written
      recommendations needed to keep disposal lawful. Section 15 (1) requires a
      written record to be created IMMEDIATELY, and s. 23 requires excavation to
      cease immediately and the project leader to be notified immediately: those
      three duties have no period at all and none is set here
    interval_basis: required
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/soil-contamination-assessments.md
    escalate: {after: 3d, to: project-manager}
  register:
    title: Unexpected Soil Contamination Assessment
    note: >
      One row per observation. The four document columns are separate booleans
      rather than one select because s. 15 (2) asks the qualified person to
      review ALL of the documents prepared under ss. 11, 12 and 13 and amend
      them — which is frequently more than one and occasionally none — and a
      single field could only ever record the last one somebody thought of.
      `written_record_created_on` is the s. 15 (1) record, which is owed
      immediately and separately from everything below it; if it is later than
      the observation the programme should show that rather than smooth it.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 7y
      authority: O. Reg. 406/19 s. 28 (1) — every document and record created or acquired under the Regulation is retained for at least seven years after it is created or acquired
      reason: >
        This is the record of what the ground turned out to be, and it outlives
        the project. It is the document a purchaser's phase one consultant will
        look for, and its absence is read as an absence of contamination rather
        than as an absence of records.
    columns:
      - {key: observation, label: Observation, type: relation, required: true,
         target: /registers/soil-contamination-observations.md#records, display: observation_id}
      - {key: written_record_created_on, label: Written record under s. 15 (1) created on, type: date, required: true}
      - {key: became_known_on, label: Date the circumstance became known, type: date, required: true}
      - {key: qualified_person, label: Qualified person, type: text}
      - {key: qualified_person_engaged_on, label: Qualified person engaged on, type: date}
      - {key: further_sampling, label: Further sampling carried out, type: bool, required: true}
      - {key: finding, label: Finding, type: select, required: true,
         options: ["Contamination confirmed — documents amended",
                   "Contamination confirmed — no amendment to the documents was needed",
                   "An area of potential environmental concern not previously identified was found",
                   "Soil quality differs from the characterization report",
                   "No contamination — excavation resumed",
                   "A notice is now owed for this project area",
                   Outstanding]}
      - {key: past_uses_amended, label: Assessment of past uses amended, type: bool, required: true}
      - {key: sampling_plan_amended, label: Sampling and analysis plan amended, type: bool, required: true}
      - {key: characterization_amended, label: Soil characterization report amended, type: bool, required: true}
      - {key: destination_report_amended, label: Destination assessment report amended, type: bool, required: true}
      - {key: registry_notice_updated, label: Registry notice updated, type: select, required: true,
         options: ["Updated", "Not required — no notice was filed", "Not required — nothing in the notice changed", Outstanding]}
      - {key: destination_changed, label: The soil's destination changed as a result, type: bool, required: true}
      - {key: revised_destination, label: Where the affected soil went, type: relation,
         target: /registers/soil-destinations.md#records, display: site_id}
      - {key: within_30_days, label: Documents reviewed and amended within the 30 days, type: bool, required: true}
      - {key: resumption_authorised_on, label: Excavation authorised to resume on, type: date}
      - {key: recommendations, label: The qualified person's further written recommendations, type: longtext}
      - {key: documents, label: The amended documents, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: the written procedure
s. 23 requires, and what happens in the thirty days after somebody uses it.

It must be recognisable as **the procedure the section describes**, because
s. 23 (2) sets a minimum content and an organisation that writes a general
"report environmental concerns to your supervisor" has not written it. At a
minimum the procedure must require: **all excavation in the project area to cease
immediately** until the project leader directs otherwise; **immediate
notification** of the project leader or the operator of the project area; and,
before excavation resumes, that all necessary steps are taken to **identify and
segregate the affected soil**, to **determine the affected portion of the project
area**, and to **dispose of excess soil from it in accordance with the
Regulation**. Where a qualified person's documents were required, the project
leader must obtain the qualified person's advice on those steps and ask whether
any document needs revision **before authorising any soil to be removed**.

**This duty is owed on every project area.** It is not triggered by volume, it is
not removed by Schedule 2, and it does not wait for a Registry notice. It is also
owed by the **operator** of the project area as well as the project leader, which
means this organisation owes it on jobs where somebody else decides everything
else. An organisation that has concluded it is rarely the project leader still
needs this procedure, and needs it on every site.

It must set out **s. 15** as the clock. A written record is created
**immediately**, including the date the circumstance became known, where
additional testing reveals the characterization report does not accurately
reflect the quality of soil bound for a reuse site, where an area of potential
environmental concern not identified in the assessment of past uses is found, or
where soil is to go to a reuse site the destination assessment report does not
name. Then **within 30 days** a qualified person reviews all the documents
prepared under ss. 11, 12 and 13, amends them, and gives whatever further written
recommendations are needed to keep disposal lawful. The thirty days runs from
when the circumstance **became known**, not from when the excavation resumed and
not from when the laboratory reported.

**Nothing here is this organisation's interval, and the procedure must say so.**
`interval_basis: required` is the truthful declaration: the thirty days is the
regulation's, "immediately" is the regulation's, and the only judgement this
organisation exercises is who it puts on the end of the telephone.

It must state what **stopping actually means** on a live site. "Cease
immediately" reaches the excavator, and it does not reach a truck already loaded
with soil from an unaffected part of the project area — but deciding which is
which is the project leader's call and not the operator's. The procedure must say
who makes it and how a machine operator reaches that person out of hours, because
the duty is discharged in the ten minutes after the bucket comes up, by whoever
is standing there.

It must cover **s. 24**: soil, excess soil and crushed rock at a project area are
stored in accordance with the Soil Rules, except where an instrument regulates
soil management at the site. Segregated soil is stored soil, and the pile that
was separated for good reason and then rained into the next one has destroyed the
evidence the sampling was for.

Finally, it must say what happens when the answer is **that a notice is now
owed**. A project area that was exempt at 1,800 m³ and has just become an
enhanced investigation project area is inside the Registry regime from that
moment, with reuse planning, a notice and a tracking system all owed before the
next load. That is a finding this procedure produces and the excess soil registry
procedure acts on, and neither document may assume the other noticed.
