---
id: toolbox-talk
label: Toolbox Talk Record
description: The topic, who delivered it, who was there, and what the crew raised back.
path: records/toolbox-talks/untitled-talk.md
# `kind: reference` is what THIS FILE is: a blank template, which is not
# evidence of anything and must never count as coverage. What the CREATED
# document is appears under `frontmatter:` below — that is the kind that
# reaches the chain, once a person has filled the form in.
template: true
kind: reference
order: 140
frontmatter:
  title: Toolbox Talk
  kind: evidence
  status: draft
  project:
  held_on:
---

# Toolbox Talk Record

> [!NOTE]
> A toolbox talk is not a signature sheet with a topic written at the top. The
> evidence an auditor and a court look for is **what was said, who heard it, and
> what came back** — a talk that raised nothing from the crew is a talk nobody
> was listening to, and the field is there so that is visible rather than
> flattering.

**Why this exists.** OHSA s. 25(2)(a) requires the employer to provide
information, instruction and supervision to protect a worker's health and safety.
ISO 45001:2018 cl. 7.3 requires workers to be aware of the hazards and of the
incidents relevant to them, and cl. 5.4 requires consultation and participation
of non-managerial workers — which is the half of a toolbox talk most records
leave out.

Pick the topic from the work in front of the crew, not from a calendar of
generic subjects. A talk about ladder safety on a week of excavation is a
document produced instead of a conversation.

```wl:table
id: records
title: Toolbox talk
columns:
  - {key: held_on, label: Held on, type: date, required: true}
  - {key: project, label: Project, type: text, required: true}
  - {key: topic, label: Topic, type: text, required: true}
  - {key: why_this_topic, label: "Why this topic, this week", type: longtext, required: true, help: "The work in front of the crew, a finding from the last inspection, an incident elsewhere, a change in conditions."}
  - {key: delivered_by, label: Delivered by, type: text, required: true}
  - {key: duration_minutes, label: Duration (minutes), type: int, required: true}
  - {key: attendees, label: Who attended, type: longtext, required: true, help: "Every name, including sub-trades and visitors who took part."}
  - {key: attendee_count, label: Number present, type: int, required: true}
  - {key: subs_present, label: Sub-trades present, type: longtext}
  - {key: key_points, label: What was covered, type: longtext, required: true}
  - {key: hazards_discussed, label: Hazards on this site it applies to, type: longtext, required: true}
  - {key: raised_by_crew, label: Raised by the crew, type: longtext, required: true, help: "Questions, disagreements, near misses mentioned, conditions nobody had written down. \"Nothing\" is an answer, and a run of it is a finding."}
  - {key: actions, label: "Actions arising, with owner and date", type: longtext}
  - {key: materials, label: Handout or material used, type: attachment}
  - {key: sign_in_sheet, label: Signed attendance sheet, type: attachment, help: Attach the paper sheet if the crew signed on site.}
  - {key: delivered_by_signature, label: Delivered by (signature), type: signature, required: true}
layout: form
review: required
approvers: [site-supervisor]
```

| Held on | Project | Topic | Why this topic, this week | Delivered by | Duration (minutes) | Who attended | Number present | Sub-trades present | What was covered | Hazards on this site it applies to | Raised by the crew | Actions arising, with owner and date | Handout or material used | Signed attendance sheet | Delivered by (signature) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
