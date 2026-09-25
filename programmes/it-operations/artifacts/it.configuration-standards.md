---
id: it.configuration-standards
kind: standard
title: System Configuration Standards
structure: standard
path: standards/system-configuration-standards.md

satisfies:
  - iso_27001:A.8.9
  - iso_27001:A.8.18
  - can_ciosc_104:CIOSC-L1-04
  - cis_controls:4.1
  - cis_controls:4.2
  - cis_controls:4.7
  - nist_csf_2:PR.PS-01
  - soc2:CC7.1

requires: [it.asset-register, it.change-management]

declares:
  obligation:
    id: it.baseline-review
    activity: Review the configuration baselines against current guidance and what is deployed
    cadence: each year
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/configuration-baseline-reviews.md
  register:
    title: Configuration Baseline Review Record
    note: >
      One row per review. `drift_found` is what the review is for: a baseline
      that is documented and not deployed is a description of an intention, and
      the only way to tell is to compare it with a live system.
    layout: form
    review: required
    approvers: [it-manager]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: baselines, label: Baselines in scope, type: longtext, required: true}
      - {key: systems_compared, label: Systems compared against baseline, type: int, required: true}
      - {key: drift_found, label: Systems differing from baseline, type: int, required: true}
      - {key: baselines_updated, label: Baselines updated, type: int, required: true}
      - {key: default_credentials, label: Default credentials found, type: int, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: what a correctly built
laptop, server or account looks like, so that "correctly built" is a thing that
can be checked rather than a thing that is assumed.

It must be a baseline the organisation can actually hold, derived from a
published benchmark rather than invented. Taking the CIS Benchmark or the
vendor's security baseline and recording the deviations the organisation has
chosen, with reasons, is a day of work; writing one from first principles is a
project that never finishes.

It must record the deviations as deviations. A baseline adopted with six
settings relaxed for compatibility is a defensible position; a baseline
described as adopted with the relaxations undocumented is a claim that fails the
first comparison.

It must cover the accounts and services shipped by default: administrative
accounts renamed or disabled, default credentials changed, unnecessary services
turned off, and privileged utility programs restricted. A.8.18 is the control
that stops a support tool being the easiest route to domain administrator.

It must say who may deviate from a baseline on a particular system and how that
is recorded — which is the change management process, not a second one.
