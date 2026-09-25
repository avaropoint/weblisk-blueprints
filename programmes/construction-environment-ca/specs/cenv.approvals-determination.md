---
id: cenv.approvals-determination
kind: procedure
title: Environmental Approvals Determination
structure: procedure
path: procedures/environmental-approvals-determination.md

satisfies:
  - epa_ontario:9
  - epa_ontario:20.2
  - epa_ontario:20.21
  - epa_ontario:27
  - owra_ontario:34
  - owra_ontario:53

requires: [cenv.environmental-approvals, cenv.excavation-projects]

declares:
  obligation:
    id: cenv.approvals-determination
    activity: Whether the work at this project area needs an approval, a registration or a permit determined and recorded, and the instrument obtained
    for:
      records: registers/excavation-projects.md
      due: 60d before excavation_start_on
      key: area_id
    authority: >
      Environmental Protection Act ss. 9, 20.21 and 27 and Ontario Water
      Resources Act ss. 34 and 53 each prohibit the activity until the approval,
      registration or permit is in place. None of them sets a lead time, because
      none of them contemplates the activity happening first. Sixty days is this
      organisation's, chosen because a registration in the Environmental Activity
      and Sector Registry cannot be made until a qualified professional has
      prepared a water taking report and a discharge report, and because an
      application for an environmental compliance approval has no service
      standard the applicant controls
    interval_basis: chosen
    responsible: environmental-lead
    applies_to: the organisation
    records: registers/approval-determinations.md
    escalate: {after: 2w, to: senior-management}
  register:
    title: Environmental Approval Determination
    note: >
      One row per project area, including every project area that needs nothing.
      Five separate determination columns rather than one, because the five
      instruments have five different triggers and an organisation that records a
      single "no approval required" cannot show which five questions it asked.
      Each is a select with a reasoned negative, and "Not yet determined" is a
      real state: an open determination on a job mobilising in three weeks is the
      thing this register exists to make visible.
    layout: form
    review: required
    approvers: [environmental-lead]
    retention:
      keep: 7y
      authority: O. Reg. 63/16 requires records relating to a registered activity to be kept for five years. O. Reg. 406/19 s. 28 (1) sets seven years for records created under that Regulation
      reason: >
        Seven years is this organisation's, chosen as the longer of the two so
        that one rule covers every environmental record. A five-year schedule
        beside a seven-year one is two rules that somebody has to apply
        correctly to each document, and the document most often filed under the
        wrong one is the determination that says no instrument was needed.
    columns:
      - {key: area, label: Project area, type: relation, required: true,
         target: /registers/excavation-projects.md#records, display: area_id}
      - {key: determined_on, label: Determined on, type: date, required: true}
      - {key: determined_by, label: Determined by, type: user}
      - {key: dewatering_expected, label: Dewatering expected, type: bool, required: true}
      - {key: peak_taking_litres_per_day, label: Highest expected taking, in litres a day, type: number}
      - {key: water_taking, label: Water taking, type: select, required: true,
         options: ["Not required — 50,000 litres or less on every day",
                   "Registration in the Environmental Activity and Sector Registry",
                   "Permit to take water",
                   "A permit already in effect for the site covers it",
                   "Not yet determined"]}
      - {key: sewage_works, label: Sewage works approval, type: select, required: true,
         options: ["Required — applied for",
                   "Required — in force",
                   "Not required — covered by the Registry registration",
                   "Not required — no sewage works",
                   "Not yet determined"]}
      - {key: air_noise, label: Air, noise and vibration approval, type: select, required: true,
         options: ["Required — applied for",
                   "Required — in force",
                   "Not required — no plant, structure or equipment that may discharge a contaminant",
                   "Not required — an exempt class under the regulations",
                   "Not yet determined"]}
      - {key: waste, label: Waste approval, type: select, required: true,
         options: ["Required — we operate a waste management system or disposal site",
                   "Required — in force",
                   "Not required — we are not the operator of any waste activity",
                   "Not yet determined"]}
      - {key: municipal_consent, label: Municipal sewer-use consent, type: select, required: true,
         options: [Obtained, "Applied for", "Not required — no discharge to a sewer", "Not yet determined"]}
      - {key: conservation_authority, label: Conservation authority permission, type: select, required: true,
         options: [Obtained, "Applied for", "Not required — the work is outside a regulated area", "Not yet determined"]}
      - {key: approval, label: The instrument obtained, type: relation,
         target: /registers/environmental-approvals.md#records, display: approval_id}
      - {key: reasoning, label: What the determination was based on, type: longtext, required: true}
      - {key: qualified_professional, label: Qualified professional engaged, type: text}
      - {key: work_started_before_instrument, label: Work began before the instrument was in place, type: bool, required: true}
      - {key: evidence, label: Supporting reports and correspondence, type: attachment}
      - {key: note, label: Note, type: longtext}
---

What this document must establish for THIS organisation: how, before a machine
arrives, somebody works out whether what is about to happen needs a piece of
paper from the Ministry of the Environment, Conservation and Parks.

It must set out **five questions and keep them apart**, because they are five
statutes' worth of different triggers and construction practice blurs them into
"do we need an ECA":

- **Taking water.** OWRA s. 34 prohibits taking more than 50,000 litres on any
  day except under a permit. The exceptions — domestic use, livestock, fire
  fighting and emergencies, electricity dams — do not reach construction
  dewatering. Taking ground water or storm water to create or maintain a
  dewatered work area within a construction site is instead **prescribed for
  registration** in the Environmental Activity and Sector Registry under
  O. Reg. 63/16. So the question on site is not *whether* an instrument applies
  but *which*, and a permit already in effect keeps the taking out of the
  Registry route.
- **Sewage works.** OWRA s. 53 requires an approval before sewage works are used,
  operated, established, altered, extended or replaced — and **the pumps,
  settling tanks, filter bags and pipework that treat water out of an excavation
  are sewage works.** This is the determination most often missed, because
  nothing about a filter bag sounds like sewage. It is displaced where the
  activity is instead covered by the Registry registration, and it is not
  displaced by the municipality's permission to discharge.
- **Air, noise and vibration.** EPA s. 9 requires an approval before using,
  operating, constructing, altering, extending or replacing any plant, structure,
  equipment, apparatus, mechanism or thing that may discharge a contaminant into
  any part of the natural environment other than water. Routine maintenance,
  motor vehicles subject to the *Highway Traffic Act*, and classes exempted by
  regulation are outside it — which covers most of a construction site and does
  not cover a fixed crusher, a concrete batching plant or a fixed generator set.
- **Waste.** EPA s. 27 requires an approval to use, operate, establish, alter,
  enlarge or extend a waste management system or a waste disposal site. This
  organisation usually answers "we are not the operator", and the answer changes
  the moment it opens a soil processing or stockpiling operation of its own.
- **Municipal and conservation authority consents**, which are not provincial
  approvals at all and are the two most likely to stop a job. **A provincial
  approval does not supply the municipality's consent to discharge to its sewer**
  under a sewer-use by-law, and s. 53 says nothing about it.

**Sixty days is this organisation's and the law's lead time is none.** It is
chosen from the shape of the work rather than from a rule: an EASR registration
requires a water taking report and a discharge report prepared by a qualified
professional *before* the registration can be made, and an environmental
compliance approval is an application to a Director with a queue this
organisation does not control. Where a project area mobilises inside sixty days
the duty is unchanged and the margin is simply gone — and the programme should
show that rather than round it away.

**`work_started_before_instrument` is required and the honest answer is sometimes
yes.** A register that cannot record that dewatering ran for a fortnight before
the registration was confirmed will be completed as though it never did, and the
one system that could have caught it reports clean.

It must say that **the determination is recorded even when the answer is no.**
Five negatives with reasons is a defensible position; a blank row is
indistinguishable from a question nobody asked, and that is the difference
between a finding and a charge.
