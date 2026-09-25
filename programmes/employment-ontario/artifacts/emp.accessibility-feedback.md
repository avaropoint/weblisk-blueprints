---
id: emp.accessibility-feedback
kind: register
title: Accessibility Feedback Register
structure: standard
path: registers/accessibility-feedback.md

satisfies:
  - aoda_ontario:11
  - aoda_ontario:80.50

requires: [emp.accessibility-policy]

register:
  title: Accessibility Feedback Register
  note: >
    One row per piece of feedback about how the organisation provides goods,
    services or facilities to people with disabilities, however it arrived. The
    regulation requires the feedback process itself to be accessible — in
    person, by telephone, in writing, by electronic text or otherwise — so the
    channel column records whether the routes offered are the routes being used.

    Feedback here is not a complaint process for employees; that is the
    workplace complaint register. This one is about barriers.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: received_on, label: Received on, type: date, required: true}
    - {key: channel, label: How it arrived, type: select, required: true,
       options: [In person, Telephone, Email, Web form, Letter, Through a third party, Other]}
    - {key: from_whom, label: From, type: select, required: true,
       options: [Member of the public, Customer, Employee, Applicant, Anonymous, Other]}
    - {key: barrier, label: Barrier or issue raised, type: longtext, required: true}
    - {key: area, label: Area, type: select, required: true,
       options: [Physical premises, Website or digital, Printed information, Customer service,
                 Employment, Event or facility, Other]}
    - {key: accessible_format_requested, label: Accessible format or communication support requested, type: bool, required: true}
    - {key: response_due, label: Response due on, type: date, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [Received, Being addressed, Responded, Closed, No response possible]}
---

What this artifact must establish: what people have told the organisation about
the barriers they met, and what happened next.

The regulation requires a feedback process, requires it to be accessible, and
requires the organisation to notify the public that it exists. It does not
require a register — but a feedback process with no record cannot show that any
feedback was ever acted on, and the accessibility compliance report attests that
the process is in place.

`accessible_format_requested` is a column of its own because it starts a distinct
duty: on request, the organisation provides or arranges for accessible formats
and communication supports, in a timely manner, at no more than the regular cost
charged to others, and in consultation with the person about what would actually
work for them. Most organisations can do this and have never been asked, which
means the first request is handled badly.

`status: No response possible` exists for anonymous feedback. It is still
feedback, it still identifies a barrier, and closing it as unactionable would
lose the only part that mattered.
