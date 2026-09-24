---
id: pre-task-hazard-assessment
label: Pre-Task Hazard Assessment (FLRA)
description: The card a crew fills in before work starts — task, conditions today, hazards, controls, and the highest control actually applied.
path: records/pre-task-hazard-assessments/untitled-flra.md
# `kind: reference` is what THIS FILE is: a blank template, which is not
# evidence of anything and must never count as coverage. What the CREATED
# document is appears under `frontmatter:` below — that is the kind that
# reaches the chain, once a person has filled the form in.
template: true
kind: reference
order: 110
frontmatter:
  title: Pre-Task Hazard Assessment
  kind: evidence
  status: draft
  project:
  assessed_on:
---

# Pre-Task Hazard Assessment

> [!NOTE]
> Fill this in **with the crew, at the workface, before work starts** — not in
> the trailer the night before. An assessment completed before anyone arrives is
> a briefing, and a briefing does not surface the thing the apprentice noticed on
> the way in.
>
> Each completed card is one row in **Pre-Task Hazard Assessment Record**
> (`registers/pre-task-hazard-assessments.md`). The register is the log; this is
> the card.

**Why this exists.** OHSA s. 25(2)(h) requires every precaution reasonable in the
circumstances, and s. 25(2)(a) requires information, instruction and supervision.
Neither the assessment nor its frequency is prescribed by Ontario law — a
per-shift assessment is the industry's answer to that duty and is this
organisation's own commitment. ISO 45001:2018 cl. 6.1.2 requires hazard
identification to be ongoing and proactive; cl. 8.1.2 requires the hierarchy of
controls to be applied.

```wl:table
id: records
title: Pre-task hazard assessment
columns:
  - {key: assessed_on, label: Date, type: date, required: true}
  - {key: project, label: Project, type: text, required: true}
  - {key: work_area, label: Work area, type: text, required: true}
  - {key: crew, label: Crew, type: text, required: true}
  - {key: led_by, label: Assessment led by, type: text, required: true}
  - {key: participants, label: Everyone who took part, type: longtext, required: true, help: "Names. If a name is missing, that person was not part of the assessment."}
  - {key: task, label: Task to be done today, type: longtext, required: true}
  - {key: conditions, label: Conditions today, type: longtext, required: true, help: "Weather, ground, overhead, who else is working nearby, what changed overnight."}
  - {key: hazards, label: Hazards identified, type: longtext, required: true}
  - {key: fall_exposure, label: Work at height today, type: bool, required: true}
  - {key: overhead_lines, label: Overhead powerlines in the work zone, type: bool, required: true}
  - {key: excavation, label: Excavation anyone may enter, type: bool, required: true}
  - {key: confined_space, label: Confined space entry, type: bool, required: true}
  - {key: controls, label: "Controls, and why these", type: longtext, required: true}
  - {key: highest_control, label: Highest control applied, type: select, options: [Eliminated, Substituted, Engineering control, Administrative control, Personal protective equipment only], required: true, help: Hard hats against a fall hazard is the wrong answer written legibly. Name the highest control you actually applied.}
  - {key: permits_required, label: Permits required and held, type: longtext, help: "Confined space entry, hot work, energised electrical work, road occupancy."}
  - {key: changed_since_plan, label: Changed from what was planned, type: longtext}
  - {key: work_stopped, label: Work stopped or changed as a result, type: bool, required: true}
  - {key: escalated_to, label: Escalated to, type: text, help: Who was called when the crew could not control the hazard themselves.}
  - {key: led_by_signature, label: Signed by the person who led it, type: signature, required: true}
layout: form
review: required
approvers: [site-supervisor]
```

| Date | Project | Work area | Crew | Assessment led by | Everyone who took part | Task to be done today | Conditions today | Hazards identified | Work at height today | Overhead powerlines in the work zone | Excavation anyone may enter | Confined space entry | Controls, and why these | Highest control applied | Permits required and held | Changed from what was planned | Work stopped or changed as a result | Escalated to | Signed by the person who led it |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## If the crew cannot control it

Stop. Call the site supervisor. Record what was found, what was decided, and who
decided it — **including when the decision was to carry on**. A procedure with no
stop-work path has already decided the answer.
