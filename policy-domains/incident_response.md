---
id: incident_response
requires: [policy, procedure, register, triggered-work, retention]
boundaries:
  business_continuity: >-
    An event that has happened and is being worked. An interruption long enough to need the organisation to run differently is business_continuity's.
  health_safety: >-
    The response: triage, containment, investigation, corrective action, notification. An injury or near miss as a safety event is health_safety's.
  logging_monitoring: >-
    What is done once something is known. Producing the signal that makes it known is logging_monitoring's.
---

## What this covers

What the organisation does when something has gone wrong: recognising it, triaging it, containing it, investigating it, correcting it, telling whoever must be told, and closing it out. The event may be a breach, an outage, an injury or a near miss — the machinery is the same and the duty to notify differs.

## Why these requirements

Triggered work, because this is the domain triggers exist for. An incident raises an investigation, an investigation raises a corrective action, and each has a clock started by the one before it. A programme expressing this as a monthly review has described a filing cabinet. Retention, because the investigation record is the thing an inquiry asks for, often years later.

## How it goes wrong

Incidents are recorded and corrective actions are not tracked to closure. The register fills up, the count goes up, and the same incident recurs — which reads, from the numbers alone, like diligent reporting.
