---
id: isec.supplier-policy
kind: policy
title: Third-Party and Supplier Security Policy
structure: policy
path: policies/third-party-security-policy.md

satisfies:
  # A.5.19 is the requirement that the organisation HAS a position on supplier
  # risk, not that it follows steps — the supplier-security procedure answers
  # the steps and cites the same control for its own half.
  - iso_27001:A.5.19
  # GV.SC-01 is explicit that the supply-chain programme is "established and
  # agreed to by organizational stakeholders": agreement by named people is
  # what a policy is and a procedure is not.
  - nist_csf_2:GV.SC-01
  - can_ciosc_104:CIOSC-L1-16
  - soc2:CC9.2

requires: [isec.policy, isec.classification]

approved_by: [senior-management]
---

What this document must establish for THIS organisation: what the organisation
is willing to put in somebody else's hands, on whose authority, and what it
will not put there at any price.

It must state the rule that nothing reaches a supplier before the relationship
is on the register and the terms are agreed — and then say honestly what happens
when somebody has already signed. A policy that pretends procurement is always
consulted first describes a company that does not exist; one that names the
route to bring an existing arrangement into the register describes one that
could.

It must say **who may enter the relationship and who may sign**, by position,
and at what value or exposure the decision moves up. This is the fact the
procedure cannot supply: the steps for reviewing a supplier are the same whether
the reviewer had authority to engage them or not.

It must set, in the organisation's own classification terms, **which
information may go to a third party at all** — which classifications, to which
jurisdictions, and under what conditions. "Our most sensitive classification is
not processed outside Canada" is a position; "suppliers shall be assessed
appropriately" is a sentence. Where the answer is *it depends*, say what it
depends on and who decides.

It must state the position on **sub-processors**: whether a supplier may
sub-contract at all, whether notice is required or consent, and what the
organisation does with the notice when it arrives. A supplier's supplier is
where the assurance chain usually ends without anybody choosing that.

It must state the position on **cloud and services bought outside procurement**,
because that is how most third-party exposure actually begins — a card, a
signup, a free tier that becomes the system of record. Name the route to approve
one quickly, and say what happens to one found in use. A prohibition with no
fast route is a prohibition people route around.

It must say **what the organisation requires of a supplier when they have an
incident** — that they tell us, how quickly, and to whom — and what the
organisation undertakes to do in return. The obligation is worthless if it lives
only in one contract that one person read.

It must name **who may accept a third-party risk that does not meet this
policy, and for how long**. An exception with no expiry is a change of policy
made by somebody who was not entitled to make one, and the exception register is
the honest record of what the standing position actually is.

It must state what happens at the end: that access is revoked and information is
returned or destroyed, and that somebody confirms it rather than assuming it.
The procedure carries the steps; the policy carries the commitment that an exit
is not optional when the relationship ends quietly rather than badly.
