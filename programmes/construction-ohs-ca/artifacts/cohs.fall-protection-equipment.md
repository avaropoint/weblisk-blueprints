---
id: cohs.fall-protection-equipment
kind: register
title: Register of Fall Protection Equipment
structure: standard
path: registers/fall-protection-equipment.md

# A register carries no `satisfies:`.
#
# It is the evidence that work happened, not the document that answers a
# control — and the relation vocabulary says so structurally: `implements`
# onto a control may be asserted by a blueprint, a policy or a procedure,
# and by nothing else. A register citing a control could never be recorded
# as answering it, so it sat at `present_uncited` permanently and capped the
# tier's readiness at a number no amount of work could move.
#
# The citation belongs on the procedure that declares this register, which
# is where the organisation states what it does; this file is where it
# records having done it.

requires: [cohs.policy]

register:
  title: Register of Fall Protection Equipment
  note: >
    One row per item of fall protection equipment the organisation owns or
    controls — harnesses, lanyards and energy absorbers, self-retracting devices,
    rope grabs and lifelines, anchorage connectors, descent and rescue devices.
    `standard_edition` is not bureaucracy: the regulation names SPECIFIC and in
    several cases older editions of the CSA standards, and an item certified only
    to a newer edition is a different compliance argument from one certified to
    the edition named. Recording the edition is what makes the difference
    answerable later.
  columns:
    - {key: asset_id, label: Asset number, type: text, required: true}
    - {key: item, label: Item, type: text, required: true}
    - {key: category, label: Category, type: select, required: true,
       options: [Full body harness, Energy absorber or lanyard, Self-retracting device,
                 Fall arrester or vertical lifeline, Horizontal lifeline,
                 Anchorage connector, Body belt or saddle, Descent or rescue device, Other]}
    - {key: manufacturer, label: Manufacturer, type: text, required: true}
    - {key: model, label: Model, type: text, required: true}
    - {key: serial, label: Serial number, type: text, required: true}
    - {key: standard_edition, label: Standard and edition marked on the item, type: text, required: true}
    - {key: manufactured_on, label: Date of manufacture, type: date}
    - {key: in_service_on, label: Placed in service on, type: date, required: true}
    - {key: issued_to, label: Issued to, type: user}
    - {key: project, label: Currently at, type: relation,
       target: /registers/projects.md#records, display: project_id}
    - {key: last_inspected_on, label: Last recorded inspection, type: date}
    - {key: next_inspection_due, label: Next inspection due, type: date, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [In service, Quarantined pending inspection, Removed from service, Destroyed]}
    - {key: removed_reason, label: Why it was removed, type: longtext}
---

What this artifact must establish: every piece of fall protection equipment the
organisation is responsible for, what standard it was built to, and when it was
last looked at by somebody competent to judge it.

It is a register and not a procedure because the work has to be driven from it.
Fall protection equipment does not fail on a schedule the organisation sets; it
fails on a date the manufacturer set, after an arrest nobody recorded, or because
it sat in a truck for two winters. One piece of work per item, due before that
item's own next inspection date, is the only shape that produces a named missing
inspection rather than a monthly invitation to read a table.

**`standard_edition` is load-bearing.** O. Reg. 213/91 names particular editions
of the CSA Z259 standards, and several of those named editions are now two
editions behind what CSA publishes. The named edition is what binds. An
organisation that writes "meets CSA" in a specification, buys to the current
edition, and is asked to show compliance with the edition the regulation names,
has three answers and no record of which is true for which item. Recording what
is marked **on the item** settles it without anybody having to reason about it.

Titles drift between editions as well as numbers, so an internal specification
citing a standard by name may be citing a document that no longer exists under
that name. The marked designation on the item is the durable fact.

It must record **removal from service and destruction as distinct states**. A
harness that has arrested a fall, or that cannot be positively identified, does
not go back on the rack; quarantine is a state, destruction is an act, and a
register whose only negative option is "removed" cannot show whether the item can
still turn up on a job.

It must hold anchorages and connectors as items in their own right. A permanent
anchor point is the part of the system nobody carries home and therefore the part
nobody inspects, and it is the part the whole system hangs from.

`next_inspection_due` is set from the **manufacturer's instructions** and from the
programme's own rules, not from a legal interval — Ontario prescribes no periodic
inspection frequency for this equipment. That is why the date is a column rather
than a constant: the clock belongs to the manufacturer, and it differs by item.
