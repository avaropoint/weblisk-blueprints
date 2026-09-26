---
id: change_management
requires: [procedure, register, approval, triggered-work]
boundaries:
  configuration_management: >-
    The decision: what is being changed, who assessed it, who authorised it, how it is backed out. The resulting state of the system is configuration_management's.
  secure_development: >-
    Authorising and recording a release. How the thing being released was built is secure_development's.
  vulnerability_management: >-
    Authorising and recording a change. Deciding that the change is needed because of a weakness is vulnerability_management's.
---

## What this covers

Authorising and recording alteration to things in service: what is changing, who assessed the effect, who agreed to it, how it is reversed, and whether it worked. It covers the emergency change as well as the planned one.

## Why these requirements

An approval, because the authorisation is the control and everything else is paperwork around it. A register, because the value is retrospective — the question this domain answers is 'what changed just before it broke', and that can only be answered by a record kept at the time. Triggered work, because the post-implementation review is raised by the change, not by the calendar. No policy: the decisions are procedural.

## How it goes wrong

Emergency changes are outside the process rather than inside it with a shorter path. An organisation whose register contains no emergency changes is not one that has none.
