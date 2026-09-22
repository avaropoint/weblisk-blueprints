---
id: cohs.notice-of-project
kind: procedure
title: Notice of Project and Prescribed Notifications
structure: procedure
path: procedures/notice-of-project.md

satisfies:
  - cor_2020:COR-04
  - iso_45001:6.1.3

requires: [cohs.project-register]

declares:
  obligation:
    id: cohs.notice-of-project
    activity: Notice of project filed, and any other prescribed notification given
    for:
      records: registers/projects.md
      due: 5d before start_on
      key: project_id
    authority: O. Reg. 213/91 ss. 6, 7, 7.1
    interval_basis: chosen
    responsible: project-manager
    applies_to: each project
    records: registers/notices-of-project.md
    escalate: {after: 3d, to: constructor-representative}
  register:
    title: Notice of Project Record
    note: >
      One row per project. `trigger` is a select and not free text because the
      triggers are a closed list in the regulation and the point of recording
      which one applied is to be able to defend the decision later — including
      the decision that none applied, which is why "None — no notice required"
      is an option and not a blank row.
    layout: form
    review: required
    approvers: [constructor-representative]
    columns:
      - {key: project_id, label: Project, type: relation, required: true,
         target: /registers/projects.md#records, display: project_id}
      - {key: trigger, label: Trigger, type: select, required: true,
         options: [Cost over the prescribed threshold,
                   Erection or structural alteration over two storeys or 7.5 m,
                   Demolition at or over 4 m high and 30 sq m,
                   Bridge or retaining structure over 3 m,
                   Silo or chimney over 7.5 m,
                   Work in compressed air,
                   Tunnel caisson cofferdam or well a person may enter,
                   Trench a person may enter over the prescribed size,
                   Ice road,
                   Work required to be designed by an engineer,
                   "None — no notice required"]}
      - {key: filed_on, label: Filed on, type: date}
      - {key: filed_by, label: Filed by, type: user}
      - {key: method, label: How it was filed, type: select,
         options: [Electronically, Ministry office]}
      - {key: posted_at_project_on, label: Posted at the project on, type: date}
      - {key: trench_notice_given, label: Trench notice given where required, type: bool}
      - {key: suspended_platform_notice_on, label: Suspended platform notice given on, type: date}
      - {key: evidence, label: Filed copy, type: attachment}
---

What this document must establish for THIS organisation: which projects require a
notice of project, who files it, and where the filed copy lives afterwards.

It must reproduce the triggers as the regulation sets them rather than summarise
them as a cost threshold, because most of them are not about cost. Height,
demolition size, bridges and retaining structures, silos and chimneys, compressed
air, tunnels and caissons, trenches of a prescribed length or depth, ice roads,
and **any work required to be designed by an engineer** — the last of which
catches jobs whose price would never have reached the money threshold. A
procedure that says "over the threshold, file a notice" is wrong for most of the
list.

It must say that the notice is **posted at the project** and kept posted. Filing
it discharges one duty; posting discharges another, and an organisation that
files electronically and never prints anything has half-complied in a way nothing
in the filing system will reveal.

It must cover the two neighbouring notifications that are not the notice of
project and are routinely confused with it. A **trench more than 1.2 m deep**
that does not reach a notice-of-project trigger still requires notification
before any work begins. A **suspended work platform system** requires
notification **at least forty-eight hours before it is first used** — that
forty-eight hours is the law's number, not a margin anybody chose, and it is the
only hard lead time in this artifact.

**The five days is this organisation's choice.** The regulation sets no lead time
for the notice of project itself; filing it the morning work starts is lawful.
Five days is chosen so that a project whose trigger was assessed wrongly can be
corrected before anybody is on site, and so the forty-eight-hour suspended
platform notice is not discovered on the day the swing stage arrives. Where a
project mobilises in less than five days the duty is unchanged; the margin is
simply gone.

It must require the filed copy to be kept. The organisation's evidence that it
filed is the copy it kept, and the Ministry's acknowledgement is not something
that arrives reliably enough to be the record.
