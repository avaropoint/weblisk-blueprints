---
id: cohs.site-emergency-response
kind: procedure
title: Project Emergency Response Plan
structure: procedure
path: procedures/project-emergency-response.md

satisfies:
  - o_reg_213_91:52
  - o_reg_213_91:55
  - cor_2020:COR-13
  - iso_45001:8.2
  - isnetworld:ISN-SAFE-11

requires: [cohs.constructor-duties]

approved_by: [senior-management]

declares:
  obligation:
    id: cohs.emergency-drill
    activity: Emergency drill appropriate to the project's hazards and its stage of construction
    cadence: each quarter
    authority: ISO 45001:2018 clause 8.2 requires the response to be periodically tested. No Ontario construction provision sets a drill interval
    interval_basis: chosen
    responsible: site-supervisor
    applies_to: each project
    records: registers/project-emergency-drills.md
    escalate: {after: 2w, to: health-safety-lead}
  register:
    title: Emergency Drill Record
    note: >
      One row per drill. `time_to_first_response` and `shortfalls` are the point:
      a drill that records only that it happened has tested nothing. The number
      that matters is how long it took, and the finding that matters is what did
      not work.
    columns:
      - {key: held_on, label: Held on, type: date, required: true}
      - {key: project, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: scenario, label: Scenario, type: select, required: true,
         options: [Evacuation, Fire, Medical emergency, High-angle or suspension rescue,
                   Confined space rescue, Trench collapse, Utility strike, Severe weather,
                   Spill or release, Other]}
      - {key: run_by, label: Run by, type: user, required: true}
      - {key: participants, label: Who took part, and from which employers, type: longtext, required: true}
      - {key: announced, label: Announced in advance, type: bool, required: true}
      - {key: time_to_first_response, label: Time to first effective response, type: text, required: true}
      - {key: muster_complete, label: All persons accounted for, type: bool, required: true}
      - {key: external_services_involved, label: External services involved, type: text}
      - {key: shortfalls, label: What did not work, type: longtext, required: true}
      - {key: actions, label: Actions raised, type: longtext}
---

What this document must establish for THIS organisation: what could go badly wrong
on a project, what happens in the first ten minutes, and who is responsible for
each part of it.

It must be **written for the project rather than for the organisation**. A
construction emergency plan that is a corporate template with a site name typed
in is the commonest and least useful document in the industry. What it needs to
contain is specific: the muster point for this phase of the build, the access
route a fire appliance can actually use given the current hoarding and the
excavation across the entrance, the nearest hospital and how long it takes at
four in the afternoon, whether there is mobile coverage in the basement, and who
meets the ambulance at the gate.

It must state that it is **the constructor's plan and covers every employer on the
project**. Sub-trades do not each run an evacuation; they participate in one. The
plan must say how their workers are counted, and who holds the list.

It must enumerate the scenarios the project's own hazards produce rather than a
generic list — and must include the **rescue plans that other artifacts require**
by reference rather than by duplication: fall arrest rescue, confined space
rescue, trench rescue. Those are written where the hazard is managed, and the
emergency plan's job is to say how they connect to everything else: who calls, who
meets the responders, who stops adjacent work.

It must be explicit about **what external services will and will not do**. A plan
that names the fire service as the rescue capability for a suspended worker is a
plan only where somebody has confirmed that service has the capability, will
enter, and can reach that location in a time that matters — in writing. Assumed
external rescue is the most dangerous single assumption in a construction
emergency plan.

It must cover the ordinary things that are missed because they are not dramatic:
how the plan changes as the building grows, who briefs a sub-trade arriving in
month nine, how workers who do not speak the site's working language are
instructed, and how a night or weekend shift with four people and no office is
covered.

**The quarterly drill interval is this organisation's choice.** No Ontario
construction provision sets a drill frequency. A quarter is chosen so that a
project of ordinary length is tested more than once and so the test falls in
different phases of the build, which is where a plan written at mobilisation
stops matching the site. A short project should be drilled once early rather than
not at all, and the document should say so.

It must require the drill to record **what did not work**. A drill with no
findings has either been rehearsed or not been examined, and both are worse than
not holding it: a clean drill record is the evidence an organisation will produce
after a real emergency went badly, and it will not survive the comparison.
