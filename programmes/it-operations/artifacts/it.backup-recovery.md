---
id: it.backup-recovery
kind: procedure
title: Backup and Recovery
structure: procedure
path: procedures/backup-and-recovery.md

satisfies:
  - iso_27001:A.8.13
  - iso_27001:A.8.14
  - can_ciosc_104:CIOSC-L1-07
  - cis_controls:11.1
  - cis_controls:11.2
  - cis_controls:11.3
  - cis_controls:11.4
  - cis_controls:11.5
  - nist_csf_2:RC.RP-02
  - nist_csf_2:RC.RP-03
  - soc2:A1.2

requires: [it.asset-register]

declares:
  obligation:
    id: it.restore-test
    activity: Restore from backup and verify the result
    cadence: each quarter
    authority: ISO/IEC 27001:2022 A.8.13 — backups tested regularly
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/restore-tests.md
    escalate: {after: 2w, to: information-security-lead}
    satisfies:
      - iso_27001:A.8.13
      - cis_controls:11.5
  register:
    title: Restore Test Record
    note: >
      One row per restore test. `data_verified_by` is a required column and it
      is the whole point: a restore that completed is an IT result, and a
      restore whose contents were confirmed correct by somebody who uses the
      data is a business result. Only the second one means the backup works.
    layout: form
    review: required
    approvers: [it-manager]
    columns:
      - {key: tested_on, label: Tested on, type: date, required: true}
      - {key: system, label: System or data set, type: text, required: true}
      - {key: backup_date, label: Backup restored from, type: date, required: true}
      - {key: performed_by, label: Performed by, type: user, required: true}
      - {key: restore_target, label: Restored to, type: select, required: true,
         options: [Isolated test environment, Alternate system, Production, Cloud sandbox]}
      - {key: time_taken, label: Time taken, type: text, required: true}
      - {key: objective_met, label: Recovery time objective met, type: bool, required: true}
      - {key: data_verified_by, label: Contents verified correct by, type: user, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Successful, Successful with issues, Failed]}
      - {key: issues, label: Issues found, type: longtext, required: true}
---

What this document must establish for THIS organisation: what is backed up, how
far back it goes, how quickly it can come back, and who has proved it.

It must name the systems and data sets rather than saying "all data". The
question a backup procedure has to answer under pressure is whether this
particular thing is recoverable, and a general commitment cannot answer it.

It must state the recovery point and recovery time for each — how much work may
be lost and how long the wait may be — and those numbers have to come from the
business impact analysis in the continuity plan rather than from what the
current tooling happens to achieve. A backup regime designed around the backup
window is one that will be discovered to be inadequate on the worst possible day.

It must require at least one copy that ransomware cannot reach: offline,
immutable, or in an account with separate credentials. A backup on a share the
domain administrator can write to is not a backup from the only threat most
organisations will actually face, and this is the single most valuable sentence
in the document.

It must say who is told when a backup fails, and by what means. A backup job
that has failed silently for five months is the most common finding here, and it
is always discovered during a restore.

It must require restores to be tested with the data checked by somebody who
knows what it should look like. A restore that completes and produces a database
nobody opened has tested the tooling, not the backup.

Quarterly is the organisation's own choice. The control requires testing
regularly and names no interval, which is why the basis is declared as chosen —
and a smaller interval is worth choosing for anything whose loss would end the
business.
