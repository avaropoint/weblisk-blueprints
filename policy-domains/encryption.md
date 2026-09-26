---
id: encryption
requires: [policy, procedure, register]
boundaries:
  data_protection: >-
    The mechanism: algorithms, keys, their generation, rotation and destruction. What the protected data is and whether it may be held is data_protection's.
  network_security: >-
    Protecting the data itself, at rest and in transit, and the keys that do it. The network the transit crosses is network_security's.
---

## What this covers

Protecting data by making it unreadable without a key: what must be protected, by what mechanism, at rest and in transit, and the whole life of the keys that do it — generation, custody, rotation, escrow and destruction.

## Why these requirements

A register, and this is the requirement that matters: the keys. An organisation that cannot say which keys exist, who holds them and when they were last rotated has not implemented encryption, it has enabled it. A procedure, because rotation and recovery are the operations that go wrong, and both are done rarely enough to be forgotten.

## How it goes wrong

The policy names an algorithm and stops. Algorithm choice is the easy part and almost never the failure; the failure is a key nobody can find during a recovery, or one that has not moved in six years.
