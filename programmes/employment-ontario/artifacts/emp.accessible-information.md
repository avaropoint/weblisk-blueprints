---
id: emp.accessible-information
kind: procedure
title: Accessible Information and Communication
structure: procedure
path: procedures/accessible-information.md

satisfies:
  - aoda_ontario:11
  - aoda_ontario:12
  - aoda_ontario:13
  - aoda_ontario:14
  - aoda_ontario:26
  - ohrc_ontario:1

requires: [emp.accessibility-feedback]

declares:
  obligation:
    id: emp.accessibility-conformance-check
    activity: Check the organisation's website and public information against the accessibility requirements
    cadence: each year
    authority: IASR s. 14 — internet websites and web content conform with WCAG 2.0 Level AA (large organisations, since 1 January 2021)
    interval_basis: chosen
    responsible: it-manager
    applies_to: the organisation
    records: registers/accessibility-conformance-checks.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Accessibility Conformance Check Record
    note: >
      One row per check. `automated_only` is recorded because automated testing
      finds roughly a third of WCAG failures: a report of "no errors" from a
      scanner alone is a statement about what the scanner tests, and keyboard
      navigation, focus order, meaningful link text and video captions are not
      in it.
    layout: form
    review: required
    approvers: [it-manager]
    columns:
      - {key: checked_on, label: Checked on, type: date, required: true}
      - {key: checked_by, label: Checked by, type: user, required: true}
      - {key: scope, label: Sites and content checked, type: longtext, required: true}
      - {key: standard, label: Standard applied, type: select, required: true,
         options: [WCAG 2.0 Level A, WCAG 2.0 Level AA, WCAG 2.1 Level AA, WCAG 2.2 Level AA]}
      - {key: automated_only, label: Automated testing only, type: bool, required: true}
      - {key: assistive_tech_tested, label: Tested with assistive technology, type: bool, required: true}
      - {key: failures_found, label: Failures found, type: int, required: true}
      - {key: failures_fixed, label: Fixed, type: int, required: true}
      - {key: third_party_content, label: Third-party embedded content assessed, type: bool, required: true}
      - {key: documents_accessible, label: Public documents available in accessible formats, type: bool, required: true}
      - {key: actions, label: Actions and timescales, type: longtext, required: true}
---

What this document must establish for THIS organisation: how information the
organisation publishes reaches somebody who cannot use the format it was
produced in.

It must state the website obligation precisely, because it is the accessibility
requirement with the widest gap between what is required and what is done. A
large organisation's internet websites and web content must conform with WCAG
2.0 Level AA — excluding the success criteria on live captions and pre-recorded
audio descriptions — and that has been in force since 1 January 2021. It applies
to content the organisation controls directly or through a contractual
relationship permitting modification, so an embedded booking tool or payment
form is not outside it.

It must cover the on-request duty, which applies far more widely than the website
one: accessible formats and communication supports, provided or arranged in a
timely manner, at no more than the regular cost, in consultation with the person.
Timely means at substantially the same time as everybody else receives it — a
format provided three weeks later has not met it.

It must include emergency procedures and public safety information, which every
obligated organisation must provide in an accessible format on request
regardless of size. That duty catches organisations that correctly concluded the
website requirement did not apply to them.

It must cover information employees need to do their job, which is a separate
requirement: where an employee with a disability asks, the employer consults and
provides accessible formats and communication supports for the information they
need for the work and for information generally available in the workplace.

It must be honest about testing. Automated tools find a minority of failures; a
keyboard-only pass and a screen-reader pass on the main journeys find most of
the rest, and a check that has only been automated should be recorded as such
rather than reported as conformance.
