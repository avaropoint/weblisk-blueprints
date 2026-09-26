---
id: isec.departure-actions
kind: procedure
title: Removing Access and Recovering Assets on Departure
structure: procedure
path: procedures/departure-actions.md

satisfies:
  - iso_27001:A.5.11
  - iso_27001:A.5.18
  - iso_27001:A.6.5
  - cis_controls:5.3
  - soc2:CC6.2

# The access control policy is the parent — this procedure removes access
# rights under it — and the departures register is the trigger. The
# personnel security procedure's quarterly verification CHECKS this work and
# is not its parent, which is why it is not named here: the IT operations
# programme places this procedure without placing that one.
requires: [isec.access-control, isec.departures]

declares:
  obligation:
    id: isec.departure-actions
    # Record-origin, and it could not be anything else. A departure happens
    # once, on a date somebody else chose; asking which quarter it belongs to
    # has no answer. The quarterly verification that already existed asks
    # whether this work was done — it is not the work, and a programme that has
    # only the check discovers every failure between one and ninety days late,
    # by design.
    activity: Remove a leaver's access, recover what they hold, and confirm both
    for:
      records: registers/departures.md
      due: 1d after access_ends_on
      key: reference
    authority: >-
      ISO/IEC 27001:2022 A.5.18 requires access rights to be removed on
      termination of employment, and A.5.11 requires assets to be returned. The
      standard sets no interval for either
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/departure-actions.md
    escalate: {after: 48h, to: information-security-lead}
    satisfies:
      - iso_27001:A.5.18
      - cis_controls:5.3
  register:
    title: Departure Action Record
    note: >
      One row per departure, keyed by the departure's reference. It is not a
      checklist somebody ticks at the end: each column is a separate act by a
      separate person, and the value of the register is that it shows which of
      them did not happen rather than that the whole thing was "completed".

      `confirmed_by` is required and is deliberately a different person from
      whoever did the work. A leaver process confirmed by the person who ran it
      has recorded an intention.
    layout: form
    review: required
    approvers: [it-manager]
    retention:
      keep: 7y
      from: modified
      authority: >-
        No standard or statute prescribes a keeping period for the record that a
        leaver's access was removed and their equipment recovered
      reason: >
        Seven years is this organisation's, and it matches the departure
        verification record this discharges. Access left open to somebody who has
        gone is found long after they went, and the Limitations Act, 2002 s. 5 runs
        from discovery rather than from the act — a record that expired with the
        employment would be gone before the question is asked.
    columns:
      - {key: reference, label: Departure, type: relation, required: true,
         target: /registers/departures.md#records, display: person}
      - {key: completed_on, label: Completed on, type: date, required: true}
      - {key: accounts_disabled_on, label: Accounts disabled on, type: date, required: true}
      - {key: privileged_removed, label: Privileged access removed, type: select, required: true,
         options: [Removed, None held, Still held — reason recorded]}
      - {key: shared_credentials_changed, label: Shared or service credentials changed, type: select, required: true,
         options: [Changed, None known to them, Not changed — reason recorded]}
      - {key: remote_access_removed, label: Remote access and VPN removed, type: bool, required: true}
      - {key: third_party_accounts, label: Supplier and third-party accounts closed, type: select, required: true,
         options: [Closed, None held, Outstanding]}
      - {key: mail_handled, label: Mailbox and files dealt with, type: select, required: true,
         options: [Delegated to a named position, Retained under hold, Deleted per schedule, Outstanding]}
      - {key: assets_returned, label: Equipment and keys returned, type: select, required: true,
         options: [All returned, Partially returned, None returned, Nothing held]}
      - {key: assets_outstanding, label: What is still outstanding, type: longtext, required: true}
      - {key: devices_wiped, label: Returned devices wiped or reissued securely, type: bool, required: true}
      - {key: obligations_confirmed, label: Continuing obligations confirmed in writing, type: bool, required: true}
      - {key: performed_by, label: Performed by, type: user, required: true}
      - {key: confirmed_by, label: Confirmed by somebody else, type: user, required: true}
      - {key: notes, label: Anything left open, and who holds it, type: longtext, required: true}
---

What this document must establish for THIS organisation: what actually happens
on the day somebody's access is due to end, in what order, and who confirms it.

It must be written so it can be run by whoever is available. The leaver process
fails on holidays, at the end of quarters, and when the person who normally does
it is the person leaving. A procedure that depends on one named individual
knowing the order is a procedure that has already failed for at least one
departure.

It must state the **order**, because for a contested departure the order is the
control: access ends first, the conversation happens second. Say who may decide
that a departure is handled that way and how the decision reaches the person who
closes the accounts — usually before anybody else is told, which is the whole
difficulty.

It must cover what the identity system does not: accounts at suppliers, SaaS
tools bought on a card, source control, the shared password on a device in a
cupboard, physical keys, a fob, a vehicle, a laptop at somebody's house. The
register's `systems_held` and `assets_held` columns are filled in by the
leaver's manager and this procedure has to say when they are asked, because
after the last day nobody can ask them.

It must say what happens to the leaver's **mail and files**, and say it in terms
of a decision somebody makes rather than a default the mail system applies.
Delegating a mailbox to a named position, putting it under a legal hold, and
deleting it on the retention schedule are three different answers and all three
are sometimes right.

It must require confirmation by somebody other than the person who did the work,
and must say what happens when something cannot be completed — equipment not
returned, a credential that cannot be changed without an outage. An outstanding
item recorded with an owner is a managed risk; the same item completed on a
checklist is a false statement.

It must connect to the quarterly departure verification without restating it.
This procedure is the work; that verification is the check that the work
happened, and it reads this register. If both documents describe "checking that
access was removed", one of them is wrong.
