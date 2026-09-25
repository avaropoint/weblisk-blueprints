---
id: fipa.handling
kind: standard
title: Handling Institutional Information
structure: standard
path: standards/institutional-information-handling.md

satisfies:
  - fippa_mfippa:FM-05
  - fippa_mfippa:FM-06
  - fippa_mfippa:FM-08
  - fippa_mfippa:FM-09
  - iso_27001:A.5.12

requires: [fipa.institutional-records]
---

What this document must establish for THIS organisation: the handling rules that
apply to an institution's records specifically, where they differ from the
organisation's own.

It must state the use and disclosure limits as the institution's, not the
organisation's. Personal information held for an institution may be used only
for the purpose it was obtained or a consistent purpose, and disclosed only as
the Act and the contract permit — which means a supplier may not use it for its
own analytics, product improvement or marketing, however anonymised it believes
the result to be.

It must set the safeguards by sensitivity, and name the ones institutions
routinely require by contract: encryption in transit and at rest, access limited
to named individuals, no removable media, no personal accounts, and separation
from the organisation's other clients' information.

It must address data residency as a rule rather than a preference. Where the
contract requires records to stay in Canada, that constrains the cloud region,
the backup destination, the support model and the help-desk tooling — and the
support model is the one that is forgotten, because a support engineer in
another country viewing a screen is an access.

It must cover accuracy and correction, which under FIPPA and MFIPPA run to the
institution rather than to the supplier: a request to correct is passed on, and a
correction made by the institution has to reach every copy the supplier holds,
including the backups it will restore from.

It carries no obligation of its own. The recurring work is the annual contract
review and the confirmation of what is held; this standard is the criterion
those measure against, and a third recurring activity would duplicate both.
