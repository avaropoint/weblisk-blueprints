---
id: site-inspection
label: Site Inspection Record
description: The monthly workplace inspection of the physical condition of a project, and what was found.
path: records/site-inspections/untitled-inspection.md
# `kind: reference` is what THIS FILE is: a blank template, which is not
# evidence of anything and must never count as coverage. What the CREATED
# document is appears under `frontmatter:` below — that is the kind that
# reaches the chain, once a person has filled the form in.
template: true
kind: reference
order: 120
frontmatter:
  title: Site Inspection Record
  kind: evidence
  status: draft
  project:
  inspected_on:
---

# Site Inspection Record

> [!IMPORTANT]
> The **statutory** inspection belongs to the worker side. A designated worker
> member of the joint health and safety committee, or the health and safety
> representative, inspects the physical condition of the workplace at least once
> a month (OHSA ss. 9(26)–(28) and 8(6)–(8)). A supervisor's daily walk is
> valuable and **is not this**. Record which one this was in *Carried out by* —
> an organisation whose only inspection records are signed by supervisors has no
> evidence of the duty being met, however diligent the walks were.

> [!NOTE]
> Where inspecting the whole project monthly is not practicable, the law allows
> the whole to be inspected at least annually with a part inspected each month.
> *Whole project inspected* is a field so that question has an answer rather than
> an impression.
>
> Each completed record is one row in **Workplace Inspection Record**
> (`registers/site-inspections.md`).

```wl:table
id: records
title: Site inspection
columns:
  - {key: inspected_on, label: Inspected on, type: date, required: true}
  - {key: project, label: Project, type: text, required: true}
  - {key: by_whom, label: Carried out by, type: select, options: [Designated worker member of the committee, Health and safety representative, Supervisor, Other], required: true}
  - {key: inspector, label: Name, type: text, required: true}
  - {key: accompanied_by, label: Accompanied by, type: text}
  - {key: area, label: Area inspected, type: text, required: true}
  - {key: whole_project, label: Whole project inspected, type: bool, required: true}
  - {key: access_egress, label: "Access, egress and housekeeping", type: longtext, required: true}
  - {key: fall_protection, label: "Fall protection, guardrails and openings", type: longtext, required: true}
  - {key: excavations, label: Excavations and trenches, type: longtext}
  - {key: scaffolds_ladders, label: "Scaffolds, platforms and ladders", type: longtext}
  - {key: equipment, label: "Equipment, hoisting and rigging", type: longtext}
  - {key: electrical, label: Electrical and overhead lines, type: longtext}
  - {key: hazardous_materials, label: "Hazardous materials, labels and SDS", type: longtext}
  - {key: ppe_in_use, label: Protective equipment in use, type: longtext}
  - {key: first_aid_emergency, label: "First aid, emergency access and signage", type: longtext}
  - {key: findings, label: Findings, type: longtext, required: true, help: "What is wrong, where, and how you know."}
  - {key: hazards_reported, label: Hazards reported to the employer, type: longtext}
  - {key: stop_work, label: Work stopped, type: bool, required: true}
  - {key: actions_raised, label: "Actions raised, with owner and date", type: longtext, help: A finding with no owner and no date is a finding that will be recorded again next month.}
  - {key: repeat_findings, label: Repeats of a previous finding, type: longtext, help: "The clearest signal a programme has stopped working is the same item appearing on four consecutive inspections, each time as new."}
  - {key: inspector_signature, label: "Inspector's signature", type: signature, required: true}
layout: form
review: required
approvers: [constructor-representative]
```

| Inspected on | Project | Carried out by | Name | Accompanied by | Area inspected | Whole project inspected | Access, egress and housekeeping | Fall protection, guardrails and openings | Excavations and trenches | Scaffolds, platforms and ladders | Equipment, hoisting and rigging | Electrical and overhead lines | Hazardous materials, labels and SDS | Protective equipment in use | First aid, emergency access and signage | Findings | Hazards reported to the employer | Work stopped | Actions raised, with owner and date | Repeats of a previous finding | Inspector's signature |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## What the inspector is entitled to

To be paid for the time. To be given the information and assistance required. To
have the findings **answered**, in writing, by the employer. An inspection whose
findings go into a folder is a hazard register the organisation has chosen not to
read.
