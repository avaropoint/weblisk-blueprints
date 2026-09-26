---
id: system-recovery-profile
label: System Recovery Profile
description: One system — what is backed up, how far back it goes, how it comes back, and who confirms the contents are right.
path: records/recovery-profiles/untitled-recovery-profile.md
# `kind: reference` is what THIS FILE is: a blank template, which is not
# evidence of anything and must never count as coverage. What the CREATED
# document is appears under `frontmatter:` below.
template: true
kind: reference
order: 230
frontmatter:
  title: System Recovery Profile
  kind: evidence
  status: draft
  system:
  owner:
  reviewed_on:
---

# System Recovery Profile

> [!IMPORTANT]
> **One of these per system, filled in before the outage, not during it.** The
> question under pressure is never "do we take backups" — it is whether *this
> particular thing* comes back, in what state, and how long it takes. A general
> commitment cannot answer that at two in the morning.

## The system

- **System or data set:**  **Owner (position):**
- **What the business does with it:**
- **What stops if it is gone:**
- **Classification:**

## What may be lost, and for how long

| | Agreed | Where the number came from |
|---|---|---|
| **Recovery point** — how much work may be lost |  |  |
| **Recovery time** — how long the wait may be |  |  |

> [!WARNING]
> Both numbers come from the business impact analysis, not from what the
> current tooling happens to achieve. A regime designed around the backup
> window is one that gets discovered to be inadequate on the worst possible
> day. If the agreed number and the achievable number differ, write both and
> name who accepted the gap.

- **Achievable today:**  **Accepted by:**  **On:**

## What is backed up

- **What is included:**
- **What is deliberately excluded, and why:**
- **Method and schedule:**
- **How far back the copies go:**

## Where the copies are

| Copy | Location | Reachable by | Immutable / offline |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |

> [!CAUTION]
> At least one copy must be beyond the reach of whoever administers the
> system — offline, immutable, or in an account with separate credentials. A
> backup on a share the domain administrator can write to is not a backup from
> the threat most organisations will actually face.

## What it needs before it can come back

*Dependencies, in order: identity, network, licences, certificates, keys, other
systems. A restore blocked on a certificate nobody could find is the usual way
a recovery time objective is missed.*

- **Credentials and keys needed, and where they are held:**

## How it comes back

*Ordered steps, written for somebody who did not build it. Name the tooling and
the account each step is run as.*

1.
2.
3.

## Who confirms it is right

- **Contents verified by (position, not IT):**
- **What they check:**

> [!NOTE]
> A restore that completes and produces a database nobody opened has tested the
> tooling, not the backup. The verifier is somebody who uses the data and would
> recognise it being wrong.

## When a backup fails

- **Who is told, by what means, within:**
- **What happens if the failure repeats:**

## Last proved

- **Last successful restore test:**  **Outcome:**
- **Next due:**
