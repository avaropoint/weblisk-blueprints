---
id: emp.accommodation-requests
kind: register
title: Accommodation Request Register
structure: standard
path: registers/accommodation-requests.md

requires: [emp.accommodation]

register:
  title: Accommodation Request Register
  note: >
    One row per request for accommodation, opened when it is made rather than
    when it is agreed. A request does not have to use the word: an employee
    saying they cannot do the early shift because of childcare, or that the
    screen is unreadable, has triggered the duty, and this row is what stops it
    being handled as an operational preference.

    **This register records the existence and status of a request, never the
    medical detail.** What an employer is entitled to is the functional
    limitation and the prognosis for return, not a diagnosis; medical
    documentation is held separately, under restricted access, and this register
    points at it rather than containing it.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: requested_on, label: Requested on, type: date, required: true}
    - {key: ground, label: Ground, type: select, required: true,
       options: [Disability, Family status, Creed, Sex or pregnancy, Age, Gender identity or expression, Other, Not stated]}
    - {key: nature, label: Functional need identified, type: longtext, required: true}
    - {key: source, label: Raised by, type: select, required: true,
       options: [Employee, Manager, Job applicant, Union or representative, Occupational health, Other]}
    - {key: information_requested, label: Supporting information requested, type: bool, required: true}
    - {key: information_received_on, label: Supporting information received on, type: date}
    - {key: interim_measure, label: Interim measure in place, type: bool, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [Open, Information awaited, Plan agreed, In place, Under review, Declined, Withdrawn, Closed]}
    - {key: review_due, label: Next review due, type: date}
---

What this artifact must establish: every accommodation request, with the date it
was made on it.

It is a register of its own because the duty to accommodate has a procedural
half that is breached by delay alone. An employer that eventually accommodates
somebody after four months of nobody owning the request has failed the
procedural duty even if the substantive outcome was correct, and only a dated
row can show how long it took.

`interim_measure` is required because the obligation to act does not wait for
the medical documentation. Something has to be in place while the information is
sought, and an employee left doing unsuitable work for six weeks while a form is
chased is the commonest complaint in this area.

`ground: Not stated` is a real answer. An employee is not obliged to name a
protected ground to trigger the duty, and an employer that requires them to
before opening a file has built a barrier into its own process.

The register deliberately holds no medical information. Under-collecting is
correctable; a diagnosis sitting in a shared register is a privacy breach that
cannot be undone, and in Ontario health information held by an employer is
sensitive personal information without being PHIPA information — protected by
the organisation's own safeguards rather than by a statute, which makes those
safeguards the whole of the protection.
