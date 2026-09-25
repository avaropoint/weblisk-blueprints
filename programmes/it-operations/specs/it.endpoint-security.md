---
id: it.endpoint-security
kind: procedure
title: Endpoint and Mobile Device Security
structure: procedure
path: procedures/endpoint-and-mobile-devices.md

satisfies:
  - iso_27001:A.8.1
  - iso_27001:A.8.7
  - iso_27001:A.7.9
  - iso_27001:A.7.10
  - can_ciosc_104:CIOSC-L1-03
  - can_ciosc_104:CIOSC-L1-04
  - can_ciosc_104:CIOSC-L1-08
  - can_ciosc_104:CIOSC-L1-13
  - can_ciosc_104:CIOSC-L1-21
  - cis_controls:10.1
  - nist_csf_2:PR.PS-05
  - soc2:CC6.8

requires: [it.asset-register]

declares:
  obligation:
    id: it.endpoint-compliance-check
    activity: Check endpoints against the security baseline and report what is not compliant
    cadence: each quarter
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/endpoint-compliance-checks.md
    escalate: {after: 2w, to: information-security-lead}
  register:
    title: Endpoint Compliance Check Record
    note: >
      One row per check. `devices_unmanaged` is the column that makes it honest:
      a compliance rate measured over managed devices only is a percentage of
      the machines that were already fine.
    layout: form
    review: required
    approvers: [it-manager]
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: devices_in_register, label: Devices in the asset register, type: int, required: true}
      - {key: devices_managed, label: Devices reporting to management tooling, type: int, required: true}
      - {key: devices_unmanaged, label: Devices not reporting, type: int, required: true}
      - {key: encryption_enabled, label: With disk encryption enabled, type: int, required: true}
      - {key: protection_active, label: With security software active and current, type: int, required: true}
      - {key: os_unsupported, label: Running unsupported operating systems, type: int, required: true}
      - {key: screen_lock, label: With screen lock enforced, type: int, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: what must be true of a
device before it holds the organisation's information, and how that is kept true.

It must set the baseline as a short list of things that are either on or off:
disk encryption, screen lock, security software running and current, automatic
updates enabled, administrative rights not held by the everyday account, and a
supported operating system. A baseline with thirty settings is one nobody can
check by hand when the tooling does not cover a device.

It must say what happens with personal devices. Most organisations have them
whether or not they are permitted, and a policy of "no personal devices" that
coexists with a mailbox synchronised to a personal phone is a policy that has
already failed. The honest options are to permit them under conditions that can
be enforced, or to make the work device available enough that the personal one
is unnecessary.

It must cover the device that leaves — lost, stolen, or simply taken home. What
is reported, to whom, how quickly, what can be wiped remotely, and what cannot.
A device with no remote wipe is not a failure as long as somebody knows that
before it goes missing.

It must cover removable media explicitly, including whether it is permitted at
all. USB storage is the control most organisations have never made a decision
about, and an unmade decision defaults to permitted.

It must say how a device is prepared for disposal or reassignment, and connect
that to the information asset procedure's secure disposal requirement rather
than restating it.
