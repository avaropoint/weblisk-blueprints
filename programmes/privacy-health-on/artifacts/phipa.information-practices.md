---
id: phipa.information-practices
kind: policy
title: Health Information Practices
structure: policy
path: policies/health-information-practices.md

satisfies:
  - phipa_ontario:10
  - phipa_ontario:15
  - phipa_ontario:16
  - phipa_ontario:29
  - phipa_ontario:30
  - phipa_ontario:12

approved_by: [senior-management]

declares:
  obligation:
    id: phipa.information-practices-review
    activity: Review the information practices and the written public statement
    cadence: each year
    authority: PHIPA s. 10(1) — a custodian shall have information practices that comply with the Act and shall comply with them
    interval_basis: chosen
    responsible: privacy-officer
    applies_to: the organisation
    records: registers/health-information-practice-reviews.md
    escalate: {after: 4w, to: senior-management}
  register:
    title: Health Information Practice Review Record
    note: >
      One row per review. `practices_followed` is a separate column from
      `practices_current` because PHIPA makes both a duty: having information
      practices that comply, and complying with them. A practice that is
      correct on paper and not followed is a contravention in its own right,
      and one column cannot record two findings.
    layout: form
    review: required
    approvers: [senior-management]
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: reviewed_by, label: Reviewed by, type: user, required: true}
      - {key: practices_current, label: Practices still describe what is done, type: bool, required: true}
      - {key: practices_followed, label: Verified as being followed, type: bool, required: true}
      - {key: statement_current, label: Public statement current and available, type: bool, required: true}
      - {key: contact_person, label: Contact person in post, type: text, required: true}
      - {key: agents_informed, label: Agents informed of their duties, type: bool, required: true}
      - {key: changes_made, label: Changes made, type: longtext, required: true}
---

What this document must establish for THIS organisation: that it is a health
information custodian, what that means for the health information in its
custody, and who answers for it.

It must first establish that the Act applies. A health information custodian is
one of the persons listed in section 3 — a health care practitioner, a hospital,
a pharmacy, a laboratory, a long-term care home, an ambulance service, a medical
officer of health and the others named there. An employer that holds medical
certificates for sick leave is **not** a custodian; a company that provides
software to a clinic is not a custodian either, though it is very likely an
electronic service provider and bound through section 10(4). Getting this
sentence wrong at the top produces either a programme of obligations nobody owes
or a clinic operating under a policy written for a commercial business.

It must set out the information practices themselves, because PHIPA's central
duty is to have them and follow them: how personal health information is
collected, used, disclosed, modified, retained, transferred and disposed of, and
how the custodian protects it.

It must name the contact person under section 15 and say what they do —
facilitate compliance, ensure agents know their duties, respond to the public,
handle access and correction requests, and receive complaints. Where no contact
person is designated the custodian performs those functions itself; the duty
does not lapse for want of an appointment, so leaving the post empty makes the
custodian personally answerable rather than excused.

It must produce the written public statement required by section 16 and say
where it is available. It has to describe the information practices in general,
say how to contact the contact person, describe how to obtain access or request
correction, and describe how to complain to the custodian and to the Information
and Privacy Commissioner.

It must apply the minimisation test of section 30 in the organisation's own
work: not to collect, use or disclose personal health information if other
information will serve the purpose, and not more than is reasonably necessary.
That is the test that decides whether a whole chart may be sent when one result
was asked for.
