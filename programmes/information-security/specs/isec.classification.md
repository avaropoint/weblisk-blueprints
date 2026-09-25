---
id: isec.classification
kind: standard
title: Information Classification and Handling
structure: standard
path: standards/information-classification.md

satisfies:
  - iso_27001:A.5.12
  - iso_27001:A.5.13
  - iso_27001:A.5.14
  - iso_27001:A.5.33
  - iso_27001:A.8.11
  - iso_27001:A.8.12
  - can_ciosc_104:CIOSC-L1-17
  - nist_csf_2:ID.AM-05
  - soc2:C1.1

requires: [isec.policy]
---

What this document must establish for THIS organisation: how many levels there
are, what each one means in this business, and what changes about handling at
each step up.

It must define the levels in terms a person can apply without asking. "Would it
harm a client if a competitor read this" is a test; "high sensitivity" is a
label. Four levels is the common answer and three is often the honest one — a
scheme with six levels is a scheme where everything is filed at level three.

It must state, for each level, what handling changes: who may see it, how it may
be sent, whether it may leave the country, whether it may be printed, what
happens to it at rest, and how it is destroyed. A classification that does not
change any behaviour is decoration, and that is the usual failure.

It must say how information is labelled, and be realistic about it. A scheme
that requires every email to carry a banner produces banners nobody reads; a
scheme that labels the repository, the folder and the system is one people can
actually follow.

It must address transfer to third parties explicitly — what may be sent to a
supplier, under what agreement, and by what means. A.5.14 is the control most
often answered by a policy sentence and contradicted by daily practice, and the
gap is usually email.

It depends on the policy rather than on the inventory, which is the way round it
reads at first: the scheme inherits its scope from the policy, and the inventory
applies the scheme to each asset rather than producing it.

It carries no obligation of its own. Classification is a criterion the rest of
the programme measures against — the inventory records each asset's level, and
the access review checks the levels are honoured — and inventing a recurring
activity for it would produce occurrences nobody agreed to.
