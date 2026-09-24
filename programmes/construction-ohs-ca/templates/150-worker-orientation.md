---
id: worker-orientation
label: Site Orientation Record
description: What a worker was told before they started on this project, what they hold, and that they understood it.
path: records/orientations/untitled-orientation.md
# `kind: reference` is what THIS FILE is: a blank template, which is not
# evidence of anything and must never count as coverage. What the CREATED
# document is appears under `frontmatter:` below — that is the kind that
# reaches the chain, once a person has filled the form in.
template: true
kind: reference
order: 150
frontmatter:
  title: Site Orientation Record
  kind: evidence
  status: draft
  project:
  delivered_on:
---

# Site Orientation Record

> [!IMPORTANT]
> Before a worker starts on the project, and before a sub-trade's worker starts.
> An orientation given in the second week documents the first week as
> unsupervised.

> [!NOTE]
> Ontario requires the **Working at Heights** training programme approved by the
> Chief Prevention Officer (O. Reg. 297/13) for a worker on a construction
> project who uses a fall protection system — and it expires. Ontario also
> requires the **worker and supervisor health and safety awareness** training
> (O. Reg. 297/13), which does not. Record which the person holds and when the
> heights training was taken, because that is the date the renewal is measured
> from.
>
> Each completed record is one row in **Orientation Verification Record**
> (`registers/site-orientation.md`). Credentials go to the credential register.

```wl:table
id: records
title: Site orientation
columns:
  - {key: delivered_on, label: Delivered on, type: date, required: true}
  - {key: project, label: Project, type: text, required: true}
  - {key: person, label: Worker, type: text, required: true}
  - {key: employer, label: Their employer, type: text, required: true}
  - {key: trade, label: Trade, type: text}
  - {key: engagement, label: Engagement, type: select, options: [Our employee, Sub-trade, Agency or temporary help, Independent operator, Visitor], required: true}
  - {key: first_day, label: First day on this project, type: date, required: true}
  - {key: new_or_returning, label: New to the industry within six months, type: bool, required: true, help: "Short-service workers are over-represented in serious injuries. If yes, name the mentor."}
  - {key: mentor, label: Mentor, type: text}
  - {key: awareness_training, label: Worker or supervisor awareness training held, type: bool, required: true}
  - {key: working_at_heights, label: Working at Heights training held, type: bool, required: true}
  - {key: working_at_heights_on, label: Working at Heights taken on, type: date, help: "The renewal clock runs from this date, not from the orientation."}
  - {key: whmis_training, label: WHMIS training held, type: bool, required: true}
  - {key: other_credentials, label: Other credentials produced, type: longtext, help: "Confined space, elevating work platform, propane, traffic control, first aid."}
  - {key: credentials_verified, label: Credentials seen and copied, type: bool, required: true}
  - {key: topics_site_hazards, label: Site hazards covered, type: longtext, required: true}
  - {key: topics_emergency, label: "Emergency procedures, muster point and first aid covered", type: bool, required: true}
  - {key: topics_reporting, label: "How to report a hazard, an incident and a near miss covered", type: bool, required: true}
  - {key: topics_refusal, label: Right to refuse unsafe work explained, type: bool, required: true, help: OHSA s. 43. A worker who does not know they may refuse does not have the right.}
  - {key: topics_jhsc, label: "Committee or representative, and how to reach them", type: bool, required: true}
  - {key: topics_ppe, label: Protective equipment required and issued, type: longtext, required: true}
  - {key: topics_violence, label: Workplace violence and harassment programme explained, type: bool, required: true}
  - {key: restrictions, label: Restrictions placed on this worker, type: longtext, help: Work they may not do until a credential or a familiarisation is complete.}
  - {key: understood, label: Worker confirmed they understood and had a chance to ask, type: bool, required: true}
  - {key: delivered_by, label: Delivered by, type: text, required: true}
  - {key: worker_signature, label: "Worker's signature", type: signature, required: true}
layout: form
review: required
approvers: [health-safety-lead]
```

| Delivered on | Project | Worker | Their employer | Trade | Engagement | First day on this project | New to the industry within six months | Mentor | Worker or supervisor awareness training held | Working at Heights training held | Working at Heights taken on | WHMIS training held | Other credentials produced | Credentials seen and copied | Site hazards covered | Emergency procedures, muster point and first aid covered | How to report a hazard, an incident and a near miss covered | Right to refuse unsafe work explained | Committee or representative, and how to reach them | Protective equipment required and issued | Workplace violence and harassment programme explained | Restrictions placed on this worker | Worker confirmed they understood and had a chance to ask | Delivered by | Worker's signature |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
