---
id: equipment-inspection
label: Equipment Inspection Record
description: One machine or item, inspected by a competent worker, with defects and what was done about them.
path: records/equipment-inspections/untitled-inspection.md
# `kind: reference` is what THIS FILE is: a blank template, which is not
# evidence of anything and must never count as coverage. What the CREATED
# document is appears under `frontmatter:` below — that is the kind that
# reaches the chain, once a person has filled the form in.
template: true
kind: reference
order: 160
frontmatter:
  title: Equipment Inspection Record
  kind: evidence
  status: draft
  project:
  inspected_on:
---

# Equipment Inspection Record

> [!IMPORTANT]
> **Competent** is a defined word (OHSA s. 1): qualified because of knowledge,
> training and experience; familiar with the Act and the regulations that apply;
> and knowledgeable about the actual and potential danger to health and safety in
> the work. An inspection signed by somebody who is not competent is not the
> inspection the regulation asked for, and the field exists so the claim is on
> the record rather than assumed.

> [!NOTE]
> **Defective equipment comes out of service.** *Removed from service* is the
> field that matters: an inspection that finds a defect and leaves the machine
> running has documented the hazard rather than controlled it. It goes back into
> service on a date, after a named person says why.
>
> Each completed record is one row in **Equipment Inspection Record**
> (`registers/equipment-inspections.md`). Fall-protection equipment has its own
> asset register; hoisting and rigging has its own weekly inspection and the
> crane's own log.

```wl:table
id: records
title: Equipment inspection
columns:
  - {key: inspected_on, label: Inspected on, type: date, required: true}
  - {key: project, label: Project, type: text, required: true}
  - {key: item, label: Equipment, type: text, required: true}
  - {key: identifier, label: Unit or serial number, type: text, required: true, help: A make and model is not an identity. Two of the same machine on one site is the common case.}
  - {key: category, label: Category, type: select, options: [Powered mobile equipment, Elevating work platform, Crane or hoist, Rigging, Ladder or scaffold, Power tool, Generator or compressor, Fall protection, Other], required: true}
  - {key: inspector, label: Inspected by, type: text, required: true}
  - {key: competent, label: Inspector is competent for this equipment, type: bool, required: true}
  - {key: manufacturer_procedure, label: "Inspected per the manufacturer's instructions", type: bool, required: true}
  - {key: manual_present, label: Operating manual present with the machine, type: bool, required: true}
  - {key: hours_or_reading, label: Hour meter or reading, type: text}
  - {key: structure, label: "Structure, welds and mountings", type: select, options: [Pass, Fail, Not applicable]}
  - {key: guards, label: Guards and interlocks, type: select, options: [Pass, Fail, Not applicable]}
  - {key: controls_brakes, label: "Controls, brakes and steering", type: select, options: [Pass, Fail, Not applicable]}
  - {key: hydraulics, label: "Hydraulics, hoses and leaks", type: select, options: [Pass, Fail, Not applicable]}
  - {key: electrical_cords, label: "Electrical, cords and grounding", type: select, options: [Pass, Fail, Not applicable]}
  - {key: lifting_gear, label: "Slings, chains, hooks and cables", type: select, options: [Pass, Fail, Not applicable]}
  - {key: safety_devices, label: "Alarms, lights, horn and fire extinguisher", type: select, options: [Pass, Fail, Not applicable]}
  - {key: defects, label: Defects found, type: longtext, required: true, help: "\"None\" is an answer. Describe what, where and how bad."}
  - {key: removed_from_service, label: Removed from service, type: bool, required: true}
  - {key: tag_applied, label: Out-of-service tag applied, type: bool}
  - {key: repair_required, label: Repair or certification required, type: longtext}
  - {key: returned_to_service_on, label: Returned to service on, type: date}
  - {key: returned_by, label: Returned to service by, type: text}
  - {key: attachments, label: Photographs or certificates, type: attachment}
  - {key: inspector_signature, label: "Inspector's signature", type: signature, required: true}
layout: form
review: required
approvers: [health-safety-lead]
```

| Inspected on | Project | Equipment | Unit or serial number | Category | Inspected by | Inspector is competent for this equipment | Inspected per the manufacturer's instructions | Operating manual present with the machine | Hour meter or reading | Structure, welds and mountings | Guards and interlocks | Controls, brakes and steering | Hydraulics, hoses and leaks | Electrical, cords and grounding | Slings, chains, hooks and cables | Alarms, lights, horn and fire extinguisher | Defects found | Removed from service | Out-of-service tag applied | Repair or certification required | Returned to service on | Returned to service by | Photographs or certificates | Inspector's signature |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
