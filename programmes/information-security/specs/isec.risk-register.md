---
id: isec.risk-register
kind: register
title: Information Security Risk Register
structure: standard
path: registers/information-security-risks.md

requires: [isec.risk-assessment]

register:
  title: Information Security Risk Register
  note: >
    One row per risk, opened when it is identified rather than when it is
    treated. `review_due` is what makes the register live: a risk nobody has
    looked at for two years is being carried at whatever level it was first
    scored, and the treatment obligation is triggered from that date.

    A risk with no owner is a risk nobody is carrying. The owner is a position,
    because people change jobs and the risk does not move with them.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: risk, label: Risk, type: longtext, required: true}
    - {key: asset, label: Asset or service affected, type: text, required: true}
    - {key: identified_on, label: Identified on, type: date, required: true}
    - {key: likelihood, label: Likelihood, type: select, required: true,
       options: [Rare, Unlikely, Possible, Likely, Almost certain]}
    - {key: impact, label: Impact, type: select, required: true,
       options: [Negligible, Minor, Moderate, Major, Severe]}
    - {key: treatment, label: Treatment, type: select, required: true,
       options: [Treat, Accept, Transfer, Avoid]}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: accepted_by, label: Accepted by, type: user}
    - {key: review_due, label: Next review due, type: date, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [Open, Treated, Accepted, Closed]}
---

What this artifact must establish: every information security risk the
organisation knows about, what is being done about it, and when somebody will
next look.

It is a register rather than a section of the assessment procedure because a
risk has to be able to go stale. A paragraph in a document is either current or
not and nothing can tell; a row with a review date is overdue or it is not, and
the platform can say which.

`reference` is the identity the rest of the programme joins on. A treatment
review cites it, an exception cites it, and an incident investigation that finds
a known risk realised cites it — which is the sentence that makes a risk
register worth keeping at all: this was known, scored, and carried.

Scoring is deliberately two columns rather than one computed number. A product
of two ordinals is a number nobody can defend in a meeting, and the moment it is
the only column, the conversation becomes about the arithmetic instead of the
exposure.
