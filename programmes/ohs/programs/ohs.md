---
id: ohs
title: Occupational Health and Safety Programme
order: 10
domains: [health_safety, training_competency, incident_response]
conforms_to: [iso_45001, cor_2020, isnetworld]

tiers:
  - id: essential
    title: Legally required
    rationale: >
      What an employer must have in place to operate lawfully: a stated
      commitment, a method for finding hazards before work begins, a way for
      workers to report harm, and a plan for the day something goes badly
      wrong. Below this line the organisation is exposed, not merely
      unaccredited.
  - id: conformant
    title: Audit-ready
    requires: essential
    rationale: >
      The programme can be shown to work. Competence is recorded against the
      roles that carry the obligations, so an auditor asking "who was trained
      to do this, and when" has an answer that is not a filing cabinet.
  - id: certifiable
    title: Externally auditable
    requires: conformant
    rationale: >
      The programme audits itself on a cycle and produces the evidence a
      certifying body or a prequalification service asks for without a
      scramble.

artifacts:
  # ── essential: what an employer must have to operate lawfully ──────────────
  - { id: ohs.policy, tier: essential }
  - { id: ohs.responsibilities, tier: essential }
  - { id: ohs.worker-participation, tier: essential }
  - { id: ohs.legal-requirements, tier: essential }
  - { id: ohs.hazard-assessment-procedure, tier: essential }
  - { id: ohs.safe-work-practices, tier: essential }
  - { id: ohs.safe-job-procedures, tier: essential }
  - { id: ohs.ppe-programme, tier: essential }
  - { id: ohs.incident-reporting-procedure, tier: essential }
  - { id: ohs.incidents, tier: essential }
  - { id: ohs.incident-investigation, tier: essential }
  - { id: ohs.emergency-response-plan, tier: essential }
  - { id: ohs.first-aid, tier: essential }
  # ── conformant: the programme can be shown to work ─────────────────────────
  - { id: ohs.competency-matrix, tier: conformant }
  - { id: ohs.training-records, tier: conformant }
  - { id: ohs.training-renewal, tier: conformant }
  - { id: ohs.orientation, tier: conformant }
  - { id: ohs.workplace-inspections, tier: conformant }
  - { id: ohs.contractor-management, tier: conformant }
  - { id: ohs.return-to-work, tier: conformant }
  - { id: ohs.objectives, tier: conformant }
  - { id: ohs.management-of-change, tier: conformant }
  - { id: ohs.corrective-actions, tier: conformant }
  # ── certifiable: it audits itself and produces what is asked for ───────────
  - { id: ohs.internal-audit-procedure, tier: certifiable }
  - { id: ohs.preventive-maintenance, tier: certifiable }
  - { id: ohs.statistics, tier: certifiable }
  - { id: ohs.fitness-for-duty, tier: certifiable }
  - { id: ohs.prequalification-records, tier: certifiable }
  - { id: ohs.certificate-renewal, tier: certifiable }
---

Twenty-nine artifacts across three tiers. It began as six — enough to
demonstrate the whole loop and honest about being a starting point — and was
built out on 2026-08-25 against the controls the three cited frameworks actually
declare, rather than against a template.

The gap that drove it was measurable. The six original artifacts answered 18
citations, and **35 of the 53 real occupational-health controls in these three
frameworks had no artifact answering them at all**. An organisation could
complete every artifact in the programme and still be unable to answer a COR
auditor on inspections, contractors, first aid, personal protective equipment,
return to work or statistics — because the programme had never asked for them.

Three obligations are RECORD-ORIGIN rather than scheduled, and they are the
reason the machinery for that exists. An incident has no period: asking which
month it belongs to has no answer, so "investigate this within three days of it
being reported" cannot be a cadence. The chain is incident → investigation →
corrective action, each triggered by a row in the register before it and each
overdue on its own clock — so the platform can say that INC-014's investigation
is eleven days late rather than that this month's review has not happened.

The chain terminates in a cadence on purpose. A trigger whose recording register
is its own trigger register discharges every occurrence the moment it creates
one, reporting a hundred per cent having checked nothing, so the last link is a
periodic sweep of what is open and late.

The chain could not START until 2026-09-22. Each of the three artifacts declared
the register named after ITSELF rather than the one its obligation writes into,
and a declared register is materialised at the obligation's `records:` path — so
every schema sat one link upstream of where it landed, `registers/investigations.md`
was created carrying incident columns, and the incident register at the head of
the chain was produced by nothing at all. No rows, so no occurrence, so no work:
it reported as a programme with nothing to do rather than as one that could not
run. The incident register is an artifact of its own now (`ohs.incidents`), which
is what makes it drafted, reviewable and countable; the loader reports an
unproduced `for.records:` the way it already reported an unproduced `records:`.

One control is deliberately left to another programme: `iso_45001:7.5`,
documented information, is answered by the document-control pack. Citing it here
as well would double-count a gap that one document closes.

Three frameworks are cited because they overlap heavily rather than because
three programmes are needed. Adopting the second and third should mostly add
citations to documents that already exist. Where a framework in this build's
catalogue has no control for something, nothing is cited: an absent citation is
recoverable, and an invented one reads as a compliance claim nobody can defend.
