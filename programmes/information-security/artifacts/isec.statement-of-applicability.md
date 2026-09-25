---
id: isec.statement-of-applicability
kind: standard
title: Statement of Applicability
structure: standard
path: standards/statement-of-applicability.md

# No `satisfies:` deliberately. The Statement of Applicability is required by
# clause 6.1.3 d) of ISO/IEC 27001:2022, and this build's catalogue holds the
# standard's Annex A control set rather than its management-system clauses —
# so there is no control here to cite. An absent citation is recoverable; an
# invented one reads as a compliance claim nobody can defend.

requires: [isec.policy, isec.risk-assessment, isec.risk-register]
approved_by: [senior-management]

declares:
  obligation:
    id: isec.soa-review
    activity: Review the Statement of Applicability against the risk treatment decisions
    cadence: each year
    authority: ISO/IEC 27001:2022 clause 6.1.3 d)
    interval_basis: chosen
    responsible: information-security-lead
    applies_to: the organisation
    records: registers/soa-reviews.md
  register:
    title: Statement of Applicability Review Record
    note: >
      One row per review. `exclusions_changed` and `justifications_updated` are
      the columns an auditor reads first: a Statement of Applicability whose
      exclusions have not been revisited since it was written is a document
      about an organisation that no longer exists.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: controls_applicable, label: Controls applicable, type: int, required: true}
      - {key: controls_excluded, label: Controls excluded, type: int, required: true}
      - {key: controls_implemented, label: Of the applicable, implemented, type: int, required: true}
      - {key: exclusions_changed, label: Exclusions added or removed, type: int, required: true}
      - {key: justifications_updated, label: Justifications updated, type: int, required: true}
      - {key: notes, label: Findings and actions, type: longtext, required: true}
---

What this document must establish for THIS organisation: which of the 93 Annex A
controls of ISO/IEC 27001:2022 apply, which do not, why not, and where each
applicable one is implemented.

It must be derived from the risk treatment decisions rather than written
alongside them. A Statement of Applicability produced by going down the annex
and marking most things applicable is a document that cannot be defended
control by control, and the defence is the entire purpose of it.

It must give a reason for every exclusion in the organisation's own terms. "Not
applicable — no software development" is a reason; "not applicable" is a claim.
An auditor tests the exclusions first, because that is where an organisation
quietly removes the controls it found inconvenient.

It must point at where each applicable control is implemented — the artifact,
the system, or the supplier's assurance report — so that the chain from control
to evidence exists before anybody asks for it.

It uses the 2022 Annex A control set: four themes, 93 controls. A Statement of
Applicability still written against the 2013 annex's 114 controls in fourteen
clauses is the clearest possible signal that the management system has not been
reviewed since the transition, and the transition deadline has passed.
