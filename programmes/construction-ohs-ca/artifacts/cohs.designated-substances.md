---
id: cohs.designated-substances
kind: procedure
title: Designated Substances and Silica
structure: procedure
path: procedures/designated-substances.md

satisfies:
  - ohsa_ontario:30
  - o_reg_278_05:8
  - o_reg_278_05:10
  - cor_2020:COR-06
  - iso_45001:6.1.2

requires: [cohs.project-register]

declares:
  obligation:
    id: cohs.designated-substance-list
    activity: Obtain the owner's designated substance list and pass it to every prospective contractor before a binding contract
    for:
      records: registers/projects.md
      due: 21d before start_on
      key: project_id
    authority: OHSA s. 30 — the owner shall determine the designated substances present and include the list in the tender; s. 30(4) the constructor shall pass it to every prospective contractor before a binding contract
    interval_basis: chosen
    responsible: project-manager
    applies_to: the organisation
    records: registers/designated-substance-lists.md
    escalate: {after: 1w, to: constructor-representative}
  register:
    title: Designated Substance List Record
    note: >
      One row per project. `list_received` and `list_distributed` are two facts
      and the civil liability attaches to both: an owner who fails to provide the
      list, and a constructor who fails to pass it on, each answer for what
      follows. A single "handled" column would hide which of the two failed.
    layout: form
    review: required
    approvers: [project-manager]
    columns:
      - {key: project_id, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: requested_on, label: Requested from the owner on, type: date, required: true}
      - {key: list_received, label: List received, type: bool, required: true}
      - {key: received_on, label: Received on, type: date}
      - {key: substances, label: Substances listed, type: longtext}
      - {key: surveys_held, label: Supporting surveys or reports held, type: attachment}
      - {key: list_distributed, label: Distributed to every prospective contractor, type: bool, required: true}
      - {key: distributed_on, label: Distributed on, type: date}
      - {key: silica_expected, label: Silica-generating work expected, type: bool, required: true}
      - {key: controls_planned, label: Controls planned, type: longtext}
      - {key: gap, label: Anything missing, and what was done, type: longtext}
---

What this document must establish for THIS organisation: how it finds out what is
in a building before it starts cutting into it, and what it does with the answer.

**The designated substance list is the owner's duty and it has a deadline that is
not a date.** Before entering into a binding contract for a project, the owner
must determine whether any designated substances are present at the project site
and must include that list **in the tender documents**. The constructor must then
pass the list to **every prospective contractor or subcontractor**. Both failures
carry civil liability, which is the rare case where the statute itself has
attached a consequence in damages rather than only a penalty.

It must say what the organisation does when the list does not arrive. Bidding
without it, or starting without it, is common and is the point at which the
organisation inherits a problem it did not create. The answer is a written
request, an escalation, and a decision recorded by somebody with authority — not
an assumption that an old building has nothing in it.

**Silica on a construction project: the document must get the route right.** The
designated substances regulation's silica provisions **expressly exclude
construction at a project**. Silica exposure on a project is governed instead by
the general control-of-exposure regulation, which sets the occupational exposure
limits. There is **no silica-specific training mandate, no statutory silica
control programme and no prescribed interval** for construction in Ontario. Nor
does the forty-year record retention rule that applies to designated substances
reach a project. Each of those is a real requirement somewhere and none of them is
a requirement here, and a programme that asserts them is citing a regulation that
disclaims it.

It must state the occupational exposure limits as the Ontario regulation states
them, and must not quote a lower figure from a consensus body as though it were
law. A tighter internal limit is a legitimate and admirable choice; presenting it
as a legal requirement is not, and it makes every other number in the document
suspect.

What the absence of a prescribed silica programme does **not** remove is the
general duty: exposure must be controlled, and cutting, grinding, chasing and
drilling masonry or concrete without water or extraction is the most common
uncontrolled exposure on a Canadian construction site. The document must name the
work, name the controls, and say who chooses between them.

**Asbestos is not covered here.** It has its own regulation and its own artifact,
and the boundary matters: the designated substances regulation's asbestos
provisions are limited to mines, manufacturing and certain long-standing
maintenance operations, and do **not** cover asbestos on a construction project.

**The twenty-one days is this organisation's choice.** The statutory deadline is
"before a binding contract", which in practice means before the tender closes —
earlier than three weeks before work starts on many jobs and later on some. The
margin here exists so the obligation surfaces while there is still time to chase
an owner who has not answered.
