---
id: cohs.hot-work-permits
kind: register
title: Hot Work Permits
structure: standard
path: registers/hot-work-permits.md

# A register carries no `satisfies:`. The citation belongs on the procedure that
# governs hot work; this file is where each permit is recorded.

requires: [cohs.fire-protection]

register:
  title: Hot Work Permits
  note: >
    One row per instance of hot work, not one per trade and not one per day. A
    permit is a statement about the conditions in a particular place at a
    particular hour — what was moved, what was covered, who is watching, and for
    how long afterwards — and a permit reused tomorrow is a statement about a
    place that has changed.

    `fire_watch_until` is the column that makes this register worth keeping.
    Most construction fires attributed to hot work start after the work has
    stopped, in material that was smouldering while the crew packed up. A permit
    that records the work and not the watch has recorded the safe part.
  layout: form
  review: required
  approvers: [site-supervisor]
  columns:
    - {key: permit_id, label: Permit, type: text, required: true}
    - {key: project, label: Project, type: relation, required: true,
       target: /registers/projects.md#records, display: project_id}
    - {key: issued_on, label: Date, type: date, required: true}
    - {key: valid_from, label: Valid from, type: text, required: true}
    - {key: valid_to, label: Valid to, type: text, required: true}
    - {key: location, label: Exactly where, type: text, required: true}
    - {key: work, label: The work, type: longtext, required: true}
    - {key: process, label: Process, type: select, required: true,
       options: [Welding, Cutting — oxy-fuel, Cutting or grinding — abrasive, Brazing or soldering,
                 Torch-applied roofing, Thawing or heating, Other spark-producing work]}
    - {key: performed_by, label: Who is doing the work, type: user, required: true}
    - {key: their_employer, label: Their employer, type: text, required: true}
    - {key: could_be_avoided, label: Could this be done by a method that is not hot work, type: select, required: true,
       options: ["No", "Yes — and it will be", "Yes — but it will not be, for the reason recorded"]}
    - {key: avoidance_reason, label: Why hot work is still being used, type: longtext}
    - {key: combustibles_removed, label: Combustibles removed within the required radius, type: bool, required: true}
    - {key: combustibles_protected, label: What could not be moved is covered or shielded, type: bool, required: true}
    - {key: openings_covered, label: Floor and wall openings, ducts and conveyors covered, type: bool, required: true}
    - {key: below_and_beyond_checked, label: The area below and on the far side of the work was checked, type: bool, required: true}
    - {key: detection_isolated, label: Fire detection isolated, and the isolation recorded for reinstatement, type: select, required: true,
       options: [Not applicable — no system in service, Isolated and recorded, "Not isolated"]}
    - {key: extinguisher_present, label: Extinguisher of the required rating at the work, type: bool, required: true}
    - {key: gas_test, label: Atmosphere tested, where a flammable atmosphere is possible, type: text}
    - {key: fire_watch, label: Fire watch, type: user, required: true}
    - {key: fire_watch_trained, label: The watch is trained in the extinguisher's use, type: bool, required: true}
    - {key: fire_watch_until, label: Watch maintained until, type: text, required: true}
    - {key: post_work_check_at, label: Final check of the area at, type: text, required: true}
    - {key: post_work_check_by, label: Final check by, type: user, required: true}
    - {key: issued_by, label: Permit issued by, type: user, required: true}
    - {key: closed_at, label: Permit closed at, type: text, required: true}
---

What this artifact must establish: every occasion on which somebody made sparks
or flame on one of this organisation's projects, what was done before, who
watched afterwards, and when the area was last looked at.

**No Ontario provision requires a hot work permit by that name, and the
procedure that declares this register must say so.** The duties that reach hot
work on a construction project are the general fire provisions of the
construction regulation, the Ontario Fire Code's requirements for hazardous
processes as the local chief fire official applies them, the organisation's
property insurer's conditions, and — for a contractor that holds one — the
recognition scheme's operational control requirement. A permit is the
organisation's chosen mechanism for discharging them, and recording it as a
legal requirement would be wrong in the direction this corpus is most careful
about. Several of those sources are contractual rather than statutory, and on
most commercial projects the **owner's** permit system governs and this register
records the permit obtained, not a second one issued.

**`could_be_avoided` is first among the control columns on purpose.** The
cheapest hot work control is not doing hot work: a bolted connection instead of
a welded one, a cold-cut instead of a torch, a mechanically-fixed membrane
instead of a torch-applied one. Torch-applied roofing in particular is the
single process most associated with serious construction fires, and a permit
system that never asks the question issues permits for work nobody needed to do
that way.

**`fire_watch_until` and `post_work_check_at` are separate columns and both are
required.** The watch during the work is the part everybody does. The continuous
watch after it stops, and the final check of the area some time after that, are
the parts that catch the fire — and they are separated here because they are two
different durations and a single "fire watch: yes" collapses them. The procedure
must set both periods for this organisation, must say where those numbers came
from, and must say that they are longer wherever the insurer, the owner or the
Fire Code says so.

**`below_and_beyond_checked` is a column because gravity is the failure mode.**
Slag and sparks fall, and they travel along the far side of a wall, through a
floor opening, into a duct, into a pile of insulation on the level below that
nobody looked at because the work was up here. A permit that inspects only the
immediate work area is a permit for the place the fire will not start.

**`detection_isolated` has three options and one of them is "not isolated".**
Hot work inside an occupied or partly-occupied building routinely requires the
detection or suppression system to be isolated, and the standing failure is that
it is isolated and then not put back. Recording the isolation is how the
reinstatement becomes owed to somebody.

It must record **which employer** is doing the work, because on a project the
hot work is usually a sub-trade's and the fire is everybody's. The constructor's
permit system covers every employer on the project or it covers nothing.
