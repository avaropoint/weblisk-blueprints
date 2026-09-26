---
id: configuration_management
requires: [procedure, register, approval]
boundaries:
  asset_management: >-
    How a thing is configured. Whether the organisation owns it and who has it is asset_management's.
  change_management: >-
    The state: baselines, what a system is actually set to, and drift from it. The authorisation to move it is change_management's.
  vulnerability_management: >-
    The intended baseline and drift from it. A weakness present even at the correct baseline is vulnerability_management's.
---

## What this covers

The intended state of a system and the distance between that and its actual state: baselines, hardening standards, approved settings, and the detection and correction of drift.

## Why these requirements

A register of baselines, because 'hardened to CIS' is not a baseline, it is a citation — the baseline is the specific set this organisation adopted, with its documented deviations. An approval, because a deviation is an accepted risk and somebody has to have accepted it. A procedure, because drift is found by a repeated comparison.

## How it goes wrong

The baseline is written once and the estate moves. A baseline that has not been revised across two operating-system versions is describing a system nobody runs.
