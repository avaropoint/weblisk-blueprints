---
id: isec.physical-security
kind: procedure
title: Physical and Environmental Security
structure: procedure
path: procedures/physical-security.md

satisfies:
  - iso_27001:A.7.1
  - iso_27001:A.7.2
  - iso_27001:A.7.3
  - iso_27001:A.7.4
  - iso_27001:A.7.6
  - iso_27001:A.7.7
  - iso_27001:A.7.8
  - iso_27001:A.7.11
  - iso_27001:A.7.12
  - soc2:CC6.4

requires: [isec.policy]

declares:
  obligation:
    id: isec.physical-inspection
    activity: Inspection of physical security at each site the organisation controls
    cadence: each year
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/physical-security-inspections.md
  register:
    title: Physical Security Inspection Record
    note: >
      One row per inspection of one site. Clear desk and clear screen are
      counted rather than confirmed, because "compliant" as a yes or no on a
      walk round a floor of thirty desks is a judgement nobody can reproduce.
    layout: form
    review: required
    approvers: [information-security-lead]
    columns:
      - {key: inspected_on, label: Inspected on, type: date, required: true}
      - {key: site, label: Site, type: text, required: true}
      - {key: inspected_by, label: Inspected by, type: user, required: true}
      - {key: perimeter_ok, label: Perimeter and entry controls working, type: bool, required: true}
      - {key: access_list_current, label: Access list current, type: bool, required: true}
      - {key: visitors_logged, label: Visitors logged and escorted, type: bool, required: true}
      - {key: desks_checked, label: Desks checked, type: int, required: true}
      - {key: desks_with_findings, label: Of those, with information left out, type: int, required: true}
      - {key: equipment_rooms, label: Equipment rooms secured, type: bool, required: true}
      - {key: utilities_ok, label: Power, cooling and cabling in order, type: bool, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: which physical spaces
matter, who may be in them, and what is done about the ones the organisation
does not control.

It must define the areas in terms the organisation has — a floor, a server
cupboard, a records room, a site office — rather than describing a data centre
it does not own. Where the equipment is in somebody else's facility, the control
is the supplier's and the evidence is their assurance report, and this document
should say so and point at the supplier register.

It must cover who lets people in and what is recorded. Visitor logs, contractor
access, deliveries and the door that is propped open in summer are the whole of
A.7.2 in most organisations.

It must state the clear desk and clear screen expectation and be specific about
what it applies to. A rule that covers everything is a rule that is broken
everywhere; a rule that covers restricted and confidential information, printed
material and unattended screens is one people can meet.

It must cover the places that are not the office at all. Home working, a laptop
in a car, a site trailer and a client's premises are where most information
physically is, and A.7.9 asks what protects it there.

It must include the supporting utilities and the cabling, which is the part
everybody skips. An organisation whose comms cabinet shares a room with the
water heater has a physical risk that no access control addresses.
