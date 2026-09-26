---
id: isec.continuity-policy
kind: policy
title: Business Continuity Policy
structure: policy
path: policies/business-continuity-policy.md

satisfies:
  # 5.2 is a named control for exactly this document, and nothing in the corpus
  # answered it: the programme had a continuity PROCEDURE, an exercise
  # obligation and a backup regime, and no statement of what the organisation
  # undertakes to keep running or who may declare that it is not.
  - iso_22301:5.2
  - iso_22301:5.3
  - iso_22301:6.2
  - iso_27001:A.5.29
  - can_ciosc_104:CIOSC-L1-22

requires: [isec.policy]

approved_by: [senior-management]
---

What this document must establish for THIS organisation: what it undertakes to
keep running, how long it may be down, and who is entitled to say that normal
operation has stopped.

It must state the **scope honestly** — which activities, sites and services are
covered and which are deliberately not. An organisation that claims everything
is covered has not chosen, and the choosing is the work: a continuity policy
whose scope is "the business" produces a plan that is equally thin everywhere.

It must set the **recovery objectives as commitments of the organisation, not
of the IT function**. How much work may be lost and how long the wait may be are
business decisions with a cost attached, and the numbers in the backup regime
and the system recovery profiles have to descend from here. Where they descend
the other way — where the agreed objective is whatever the current tooling
achieves — the policy has recorded a capability and called it a decision.

It must name **who may declare a disruption**, by position, and who may declare
it over. This is the single authority that cannot be derived from anything else
and the one most plans omit: invoking continuity arrangements costs money and
interrupts people, so in the absence of a named authority nobody invokes
anything for the first two hours.

It must name **who may spend, and up to what**, during a disruption, and who may
authorise departing from normal procedure — procurement, change control,
approval thresholds. A continuity plan that requires the ordinary change process
is a plan that will be ignored in the event and cannot be defended afterwards.

It must state the commitment to **exercise** the arrangements, and that an
exercise that finds nothing is reported as such. The programme already carries
an annual exercise; what the policy adds is that senior management asked for it
and reads the result.

It must say what the organisation expects of **suppliers it cannot operate
without**, and connect that to the criticality already recorded in the supplier
register rather than starting a second list.

It must state **who communicates** during a disruption — to staff, to customers,
to regulators, to the public — and that nobody else does. Disruption and
security incident communications are the same discipline and frequently the same
event; where the incident policy already names the spokesperson, say so here
rather than naming a different one.
