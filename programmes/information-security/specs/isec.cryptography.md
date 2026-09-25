---
id: isec.cryptography
kind: standard
title: Cryptographic Controls
structure: standard
path: standards/cryptographic-controls.md

satisfies:
  - iso_27001:A.8.24
  - iso_27001:A.5.17
  - nist_csf_2:PR.DS-01
  - nist_csf_2:PR.DS-02
  - can_ciosc_104:CIOSC-L1-07
  - soc2:CC6.7

requires: [isec.classification]
---

What this document must establish for THIS organisation: where encryption is
required, what is acceptable, and who holds the keys.

It must state the requirement by classification and by state — at rest, in
transit, on portable media, in backups — rather than as a general commitment to
encrypt. "All data is encrypted" is a sentence that survives an audit until
somebody asks about the backup drive in the cabinet.

It must name what is acceptable today rather than pointing at "industry
standard", and say who decides when that changes. An algorithm judgement has a
shelf life, and a document that does not say who revisits it is one that will
still recommend what was current when it was written.

It must address key management as the harder half: who generates keys, where
they are held, who can recover data if the holder is unavailable, how a key is
rotated, and what happens to data encrypted under a key that has been
compromised. An organisation whose only copy of a recovery key is in the same
system it protects has an availability incident waiting for a bad morning.

It must say what happens to encrypted information when somebody leaves. A
personally-held key is an asset that walks out, and A.5.11 does not mention it.

It carries no obligation of its own. What recurs is the review of the standard
itself, which happens through the document control programme's periodic review,
and the checking of whether systems conform, which is the internal audit's work
— inventing a third recurring activity here would create occurrences that
duplicate both.
