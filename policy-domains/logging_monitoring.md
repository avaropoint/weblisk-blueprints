---
id: logging_monitoring
requires: [procedure, register, retention]
boundaries:
  incident_response: >-
    Producing and keeping the signal: what is logged, watched, alerted on, and for how long. What happens after the alert is incident_response's.
  records_management: >-
    What is logged and watched, and how long the log is kept to be useful. The organisation's records schedule as a whole is records_management's.
---

## What this covers

Producing, keeping and watching the signal: what events are recorded, where they go, who looks at them, what raises an alert, and how long any of it survives.

## Why these requirements

Retention, because a log's keeping period is the whole of its usefulness — an intrusion found after ninety days cannot be investigated from sixty days of logs, and that is discovered exactly once, at the worst possible moment. A register, because 'we log everything' is never true and the list of what is not logged is the interesting one. No policy is required: the decisions here are operational and belong in the procedure.

## How it goes wrong

Logs are collected and never read. Collection is measurable and review is not, so collection is what gets reported.
