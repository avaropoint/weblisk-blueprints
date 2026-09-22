---
id: cohs.notifiable-events
kind: register
title: Register of Notifiable Events
structure: standard
path: registers/construction/notifiable-events.md

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

requires: [cohs.constructor-duties]

register:
  title: Register of Notifiable Events
  note: >
    One row per event that may require a notice to somebody outside the
    organisation — a death or critical injury, an injury requiring medical
    attention or preventing usual work, an occupational illness, or one of the
    prescribed project-site occurrences such as an accident, explosion, fire,
    flood, inrush of water, failure of equipment, cave-in, subsidence or
    rockburst. It is deliberately NOT the incident register: near misses,
    property damage and first aid belong in the incident process and only a
    subset of those become notifiable. Keeping the two apart is what stops a
    statutory clock being buried under a hundred rows that do not carry one.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: occurred_on, label: Occurred on, type: date, required: true}
    - {key: became_aware_on, label: The organisation became aware on, type: date, required: true}
    - {key: project, label: Project, type: relation, required: true,
       target: /registers/construction/projects.md#records, display: project_id}
    - {key: category, label: Category, type: select, required: true,
       options: [Death, Critical injury, Injury requiring medical attention or preventing usual work,
                 Occupational illness, Project-site occurrence, Workplace violence]}
    - {key: person_affected, label: Person affected, type: user}
    - {key: their_employer, label: Their employer, type: text, required: true}
    - {key: our_role, label: Our role in relation to them, type: select, required: true,
       options: [Their employer, Constructor only, Constructor and their employer, Neither]}
    - {key: description, label: What happened, type: longtext, required: true}
    - {key: scene_preserved, label: Scene left undisturbed, type: bool, required: true}
    - {key: immediate_notice_given, label: Inspector notified immediately by direct means, type: bool}
    - {key: immediate_notice_at, label: Immediate notice given at, type: text}
    - {key: closed_on, label: Closed on, type: date}
---

What this artifact must establish: every event that starts a statutory clock, the
moment it started, and who the organisation was to the person it happened to.

It is separate from the general incident register on purpose. Incidents are
reported broadly and that is right — near misses are the cheapest information a
safety programme ever gets. But only some incidents carry a notice duty, and those
duties run in **hours and days from the event**, not from when somebody got round
to categorising it. A register where four notifiable events sit among two hundred
rows produces exactly one outcome, repeatedly: the notice is late.

`our_role` is required because on a construction project the duties split. A
death or critical injury must be notified by **the constructor and the employer**;
a prescribed project-site occurrence is notified by **the constructor**. An
organisation that is a sub-trade on somebody else's site has different duties from
one that is the constructor on its own, and the same organisation is both in the
same month. The column makes the question answerable per row rather than per
organisation.

`became_aware_on` is separate from `occurred_on` because some clocks run from
awareness rather than from the event — an occupational illness in particular is
usually learned about long afterwards, sometimes from a claim rather than from the
worker.

**`scene_preserved` is a column because it is a duty and it is immediate.** Where
a person is killed or critically injured, the scene must not be disturbed except
to save life, relieve suffering, maintain an essential public utility or prevent
unnecessary damage. It is the duty most likely to be breached in the first ten
minutes by well-meaning people tidying up, and the only defence is that somebody
knew it was a duty before it happened.

The register records that the immediate notice was given and when. The **written**
notices, with their own deadlines and their own recipients, are raised as work by
the statutory notices procedure and recorded there — one clock, one record,
joined by this row's reference.

**No retention period is declared on this register**, and the reason is worth
stating rather than leaving as an omission: the periods that reach these records
come from several different instruments with different clocks, and at least one of
them — the first aid record — has **no prescribed retention period at all**. The
organisation should set its own, generous, and record which rule it is
implementing. A number inherited from a pack would be a guess wearing a
citation.
