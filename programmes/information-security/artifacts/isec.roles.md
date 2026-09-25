---
id: isec.roles
kind: standard
title: Information Security Roles and Segregation of Duties
structure: standard
path: standards/information-security-roles.md

satisfies:
  - iso_27001:A.5.2
  - iso_27001:A.5.3
  - iso_27001:A.5.5
  - nist_csf_2:GV.RR-02
  - can_ciosc_104:CIOSC-L1-15
  - soc2:CC1.3

requires: [isec.policy]
---

What this document must establish for THIS organisation: which position does
what, so that every obligation in the rest of the programme has an owner who
exists.

It must name positions, never people. Every obligation in this programme assigns
work to a position, and an unfilled position is a finding the platform can
report; a named individual who has left is a document that looks correct.

It must state the conflicts the organisation cannot allow one position to hold
at once — requesting and approving access, developing and deploying to
production, administering a system and reviewing its logs. Where the
organisation is too small to separate them, and many are, it must say so
explicitly and name the compensating control: a second pair of eyes after the
fact is a legitimate answer, and pretending the separation exists is not.

It must say who contacts an authority and who may speak for the organisation to
a regulator, a police service or a cyber centre. A.5.5 exists because the middle
of an incident is the wrong moment to discover that nobody is authorised to make
the call.
