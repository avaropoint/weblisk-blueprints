---
id: incident-report
label: Incident / Near-Miss Report
description: Reported when it happens, not when it is resolved. A near miss is an incident.
path: records/incidents/untitled-incident.md
# `kind: reference` is what THIS FILE is: a blank template, which is not
# evidence of anything and must never count as coverage. What the CREATED
# document is appears under `frontmatter:` below — that is the kind that
# reaches the chain, once a person has filled the form in.
template: true
kind: reference
order: 130
frontmatter:
  title: Incident Report
  kind: evidence
  status: draft
  reference:
  occurred_on:
---

# Incident / Near-Miss Report

> [!IMPORTANT]
> **Critical injury or death: do not wait for this form.** Notify the Ministry of
> Labour, Immigration, Training and Skills Development immediately by telephone,
> and the joint health and safety committee or health and safety representative
> and the trade union. **Preserve the scene** — nothing may be disturbed except to
> save life, relieve suffering, maintain an essential public utility or prevent
> unnecessary damage (OHSA s. 51). A written report follows within 48 hours.

> [!NOTE]
> A **near miss is an incident**. A register that holds only injuries records the
> ones that were not prevented, and the organisation loses the only cheap
> warnings it gets.
>
> `reference` is the identity the whole chain joins on: the investigation cites
> it and the corrective action arising from that investigation cites it again. It
> must be issued when the incident is reported and must never be reused.
>
> Each report opens one row in the **Incident Register**
> (`registers/incidents.md`), from which the investigation obligation is raised.

```wl:table
id: records
title: Incident report
columns:
  - {key: reference, label: Reference, type: text, required: true, help: "Issued on report. Never reused — two incidents can share a date, a location and a reporter and nothing else tells them apart."}
  - {key: occurred_on, label: Occurred on, type: date, required: true}
  - {key: occurred_at, label: Time, type: text, required: true}
  - {key: reported_on, label: Reported on, type: date, required: true}
  - {key: project, label: Project, type: text, required: true}
  - {key: location, label: Exact location, type: text, required: true}
  - {key: kind, label: Kind, type: select, options: [Near miss, First aid, Medical aid, Lost time, Critical injury, Fatality, Occupational illness, Property damage, Environmental], required: true}
  - {key: notifiable, label: May require a notice to the Ministry or the Board, type: bool, required: true, help: "Death, critical injury, an injury needing medical attention or preventing usual work, an occupational illness, or a prescribed occurrence such as an accident, explosion, fire, flood, inrush of water, failure of equipment, cave-in, subsidence or rockburst."}
  - {key: person_affected, label: Person affected, type: text}
  - {key: their_employer, label: Their employer, type: text, required: true, help: "Ours, a sub-trade's, or another employer on the project. This decides who must report to whom."}
  - {key: reported_by, label: Reported by, type: text, required: true}
  - {key: witnesses, label: Witnesses, type: longtext}
  - {key: description, label: What happened, type: longtext, required: true, help: "What the person was doing, what changed, what the outcome was. No blame and no conclusions — the investigation is where causes are decided."}
  - {key: injury_detail, label: Injury or damage, type: longtext}
  - {key: treatment, label: Treatment given, type: select, options: [None, First aid on site, Sent to a clinic or hospital, Ambulance, Not applicable]}
  - {key: immediate_action, label: Immediate action taken, type: longtext, required: true}
  - {key: scene_preserved, label: Scene preserved, type: bool}
  - {key: jhsc_notified, label: Committee or representative notified, type: bool, required: true}
  - {key: photos, label: Photographs and attachments, type: attachment}
  - {key: reporter_signature, label: Reported by (signature), type: signature, required: true}
layout: form
review: required
approvers: [health-safety-lead]
```

| Reference | Occurred on | Time | Reported on | Project | Exact location | Kind | May require a notice to the Ministry or the Board | Person affected | Their employer | Reported by | Witnesses | What happened | Injury or damage | Treatment given | Immediate action taken | Scene preserved | Committee or representative notified | Photographs and attachments | Reported by (signature) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## What happens next

The investigation is **a record of its own**, raised from this report and due on
its own clock. That is deliberate: a column is filled in or it is not; it has no
due date, nobody owns it, and an investigation that never happened looks exactly
like one where somebody left the field blank.
