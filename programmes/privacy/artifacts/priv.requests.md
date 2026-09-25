---
id: priv.requests
kind: register
title: Privacy Request Register
structure: standard
path: registers/privacy-requests.md

register:
  title: Privacy Request Register
  note: >
    One row per request from an individual about their own personal information,
    opened on the day it arrives rather than on the day somebody decides it is a
    formal request. The statutory clock starts on receipt, and an organisation
    that dates the row from when it was recognised has already lost days it
    cannot get back.

    A request does not have to say "PIPEDA", be in writing, or go to the privacy
    officer. An email to a salesperson asking what you have about me is an
    access request, and the row is how it stops being lost.
  columns:
    - {key: reference, label: Reference, type: text, required: true}
    - {key: received_on, label: Received on, type: date, required: true}
    - {key: received_by, label: Received by, type: user, required: true}
    - {key: channel, label: How it arrived, type: select, required: true,
       options: [Email, Letter, Telephone, In person, Web form, Through a regulator, Other]}
    - {key: type, label: Type of request, type: select, required: true,
       options: [Access, Correction, Withdrawal of consent, Deletion, Portability,
                 Information about disclosures, Complaint, Unclear]}
    - {key: requester_verified, label: Identity verified, type: bool, required: true}
    - {key: scope, label: What is being asked for, type: longtext, required: true}
    - {key: due_on, label: Response due on, type: date, required: true}
    - {key: extended, label: Extension taken, type: bool, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [Open, Awaiting identity verification, In progress, Responded, Refused, Withdrawn]}
---

What this artifact must establish: every request an individual has made about
their own information, with the date it arrived on it.

It is a register of its own rather than a set of columns on the response
procedure because a response has to be able to be late, and "late" is a
statutory fact with consequences rather than a workload observation. These rows
are what the response obligation is triggered from, which is what lets the
platform say that a request is four days from its deadline.

`received_on` is the date the request reached the organisation, not the date it
reached the privacy officer. Under PIPEDA the thirty days run from receipt by
the organisation, and the gap between those two dates is the most common reason
a response is late.

`type: Unclear` is deliberate. A person writing to complain about a marketing
email may be withdrawing consent, making an access request, or both, and the
correct first step is to ask them — which takes days, during which the clock is
running and the row must exist.
