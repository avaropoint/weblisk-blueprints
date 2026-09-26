---
id: network_security
requires: [policy, procedure, register]
boundaries:
  access_control: >-
    The path: segmentation, firewalls, remote access, what may reach what. Who is at the other end is access_control's.
  encryption: >-
    The network path and what may traverse it. Protecting the payload regardless of path is encryption's.
---

## What this covers

The path: what may reach what, from where. Segmentation, perimeter and internal filtering, remote access, wireless, and the rules that express all of it.

## Why these requirements

A register, because a rule set nobody has inventoried is a rule set nobody can prune, and the accumulated exception is how a segmented network quietly becomes a flat one. A procedure, because adding a rule is easy and removing one requires knowing why it was added.

## How it goes wrong

Rules are only ever added. The absence of any record of a rule being removed is the signal.
