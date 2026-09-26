---
id: access_control
requires: [policy, procedure, register, triggered-work]
boundaries:
  hr_security: >-
    Who may hold an account and what it may reach. The employment relationship behind the person is hr_security's.
  network_security: >-
    Who the requester is and what they are entitled to. Where the request may travel from is network_security's.
  physical_security: >-
    Logical entry: accounts, credentials, privilege. A door, a badge reader and a locked cabinet are physical_security's.
  vendor_management: >-
    What any account may reach, whoever holds it. Whether the third party behind it should have been engaged is vendor_management's.
---

## What this covers

Who may reach what, and on what evidence they are who they claim to be: identity, authentication, authorisation, privilege, and the review of all of it. It covers accounts held by employees, by contractors and by machines.

## Why these requirements

Triggered work, because the failures in this domain are almost entirely about timing: an account outlives the person, a privilege outlives the project. Those are events, not a calendar — somebody joins, moves or leaves, and the work is raised by that. A programme with only a periodic access review will always be discovering leavers up to a quarter late. A register, because entitlement that is not recorded cannot be reviewed.

## How it goes wrong

The review happens and nothing is removed. A review that has never once resulted in a revocation is not evidence that access is correct; it is evidence that nobody is looking.
