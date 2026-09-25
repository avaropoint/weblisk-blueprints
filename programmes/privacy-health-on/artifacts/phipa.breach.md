---
id: phipa.breach
kind: procedure
title: Health Privacy Breach Notification
structure: procedure
path: procedures/health-privacy-breach.md

satisfies:
  - phipa_ontario:12(2)
  - phipa_ontario:12(3)
  - phipa_ontario:13

requires: [phipa.information-practices, priv.breaches]

declares:
  obligation:
    id: phipa.breach-notification
    # Record-origin, triggered from the same breach register the general
    # privacy programme uses. PHIPA's individual-notice duty has no harm
    # threshold, so this obligation is raised for EVERY breach involving
    # personal health information — which is why it is separate from the
    # PIPEDA assessment rather than a column on it.
    activity: Notify the individual and determine whether the Commissioner must be told
    for:
      records: registers/privacy-breaches.md
      due: 48h after discovered_on
      key: reference
    authority: PHIPA s. 12(2) — notice to the individual at the first reasonable opportunity
    interval_basis: required
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/health-privacy-notifications.md
    escalate: {after: 24h, to: senior-management}
  register:
    title: Health Privacy Notification Record
    note: >
      One row per breach involving personal health information, keyed by the
      breach reference. `prescribed_circumstance` is a select rather than a
      boolean because the reporting trigger under O. Reg. 329/04 s. 6.3 is a
      list of named situations, and recording which one applied is what makes
      the decision reviewable.
    layout: form
    review: required
    approvers: [privacy-officer, senior-management]
    approval_order: sequential
    columns:
      - {key: reference, label: Breach, type: relation, required: true,
         target: /registers/privacy-breaches.md#records, display: reference}
      - {key: assessed_on, label: Assessed on, type: date, required: true}
      - {key: assessed_by, label: Assessed by, type: user, required: true}
      - {key: individual_notified_on, label: Individual notified on, type: date}
      - {key: notice_method, label: How the individual was notified, type: select, required: true,
         options: [In writing, In person, By telephone, Substitute decision-maker notified,
                   Public notice, Exception applies — not notified]}
      - {key: complaint_rights_given, label: Told of the right to complain to the Commissioner, type: bool, required: true}
      - {key: prescribed_circumstance, label: Reporting circumstance under O. Reg. 329/04 s. 6.3, type: select, required: true,
         options: [None applies, Use or disclosure by a person who knew it was not permitted,
                   Stolen information, Further unauthorised use or disclosure, Pattern of similar breaches,
                   Disciplinary action against a college member, Disciplinary action against another person,
                   Significant breach, More than one applies]}
      - {key: commissioner_notified_on, label: Commissioner notified on, type: date}
      - {key: college_notified, label: Regulatory college notified, type: bool, required: true}
      - {key: containment, label: Containment and recovery, type: longtext, required: true}
      - {key: prevention, label: What is being changed, type: longtext, required: true}
---

What this document must establish for THIS organisation: who is told when
personal health information goes where it should not, and how quickly.

It must state plainly that PHIPA's notice duty has no harm threshold. Under
PIPEDA the individual is notified where there is a real risk of significant
harm; under PHIPA the individual is notified at the first reasonable opportunity
when their personal health information is stolen or lost or is used or disclosed
without authority, full stop. A custodian that applies the PIPEDA test to health
information will under-notify, and that is the most common error in a
multi-regime organisation.

It must name the prescribed circumstances that require the Commissioner to be
told, and record which one applied. Disciplinary action taken — or that would
have been taken but for the person resigning — against a member of a regulatory
college is one of them, which means an insider snooping case is reportable even
where one record was viewed and no harm followed.

It must cover the annual statistical report separately, because it is a
different duty: by 1 March each year the custodian reports to the Commissioner
the number of breaches in the previous calendar year, counting every one and not
only the reportable ones. That is why the breach record has to hold them all.

It must say who notifies the regulatory college where the person involved is a
member of one, and who tells the individual when the individual cannot be
reached — a substitute decision-maker, or public notice where the Act permits.

Forty-eight hours, escalating after another twenty-four. The Act says at the
first reasonable opportunity and sets no number; this is the organisation's
working deadline against a duty whose interval is required but unquantified, and
the record above is what shows it was met.
