---
id: isec.incident-policy
kind: policy
title: Security Incident Management Policy
structure: policy
path: policies/security-incident-management-policy.md

satisfies:
  # A.5.24 is the preparation half — processes, ROLES and RESPONSIBILITIES
  # defined and communicated. The response plan answers the processes; the roles
  # and the authority to use them are a decision of management and had no
  # document.
  - iso_27001:A.5.24
  - nist_csf_2:RS.MA-03
  - nist_csf_2:RS.CO-02
  - soc2:CC7.4

requires: [isec.policy]

approved_by: [senior-management]
---

What this document must establish for THIS organisation: what counts as a
security incident, who is entitled to say so, and who decides who is told.

The response plan already says what is done. Every sentence below is a decision
the plan cannot make for itself, and each one is made badly under pressure by
whoever is in the room at two in the morning if it has not been made in advance.

It must **define what an incident is**, in this organisation's terms, and say
that a suspected incident is treated as one until somebody with authority says
otherwise. The failure mode is not over-reporting; it is the four hours spent
deciding whether something qualifies.

It must set the **severity scheme** — the levels, what distinguishes them, and
what each one commits the organisation to in terms of response and of hours. The
scheme belongs in the policy because it is what the organisation has promised
itself, and because a severity scale invented during an incident is always
chosen to justify the response already underway.

It must name **who may declare an incident, who may declare its severity, and
who may declare it closed**, by position, with a route that works when that
position is unreachable or is the subject of the incident. Declaration is an
authority, not a task: it commits money, interrupts people and may stop a
service.

It must state that **reporting is mandatory and attracts no penalty** — for
staff, for contractors, and for the person who clicked the link. The single
greatest determinant of how bad a security incident becomes is how long it takes
the first person who noticed to say something, and that is set by what they
expect to happen to them. Say it plainly, and say it applies to the person who
caused it.

It must name **who decides on notification and who performs it** — to
customers, to a regulator, to a privacy commissioner, to the police, to an
insurer, to affected individuals. These are legal decisions with clocks attached
and they are not the incident responder's to make. Where a privacy programme
already holds the breach assessment, say that it governs and do not restate its
test here: two documents describing the same notification threshold differently
is worse than one.

It must say **who may speak publicly and who may not**, including on social
media and to customers asking directly, and what everybody else says instead.

It must state the position on **evidence**: that preservation comes before
restoration where the two conflict, who may authorise reimaging or a password
reset that destroys evidence, and that the decision is recorded. The response
plan holds the technique; this holds the priority, because the pressure to
restore service is what actually decides it.

It must say when **outside help** is engaged — forensics, counsel, the insurer,
the Cyber Centre — and who may commit that money without a procurement cycle. An
insurer that must be notified before a responder is retained, in a policy nobody
read, is the common and expensive surprise.

It must require the organisation to **learn**, and connect that to the incident
review the programme already runs rather than describing a second one.
