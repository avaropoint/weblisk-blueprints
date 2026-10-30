---
id: document-control.procedure
version: 1.2.0
kind: procedure
title: Document Control Procedure
structure: procedure
path: procedures/document-control.md
template: procedure

satisfies:
  # The method: how a document comes into force, who approves it, which version
  # governs. Cited by id only; the control text is the standard's.
  - iso_9001:7.5
  - iso_45001:7.5
  - iso_27001:A.5.37
  # Protection of records: the method says how a controlled document and the
  # records it leaves are kept from loss, destruction and falsification.
  # Moved here from the register, which carries no claim of its own.
  - iso_27001:A.5.33
requires: [document-control.policy]

declares:
  obligation:
    id: document-control.periodic-review
    # Record-origin, not a calendar. `cadence: each year` would produce ONE
    # occurrence a year for the whole estate, so a document due in March and one
    # due in November would be the same annual task, and nobody could say which
    # document was late — only that the year's review had not happened.
    #
    # The register carries a next-review date per document, so each row is its
    # own occurrence, due before that date rather than after it. The trigger
    # register and the recording register are deliberately different files: a
    # self-recording trigger would discharge every occurrence the moment it
    # created it, and report a hundred per cent having checked nothing.
    activity: Review of a controlled document reaching its review date
    for:
      records: registers/controlled-documents.md
      due: 30d before next_review
      key: document
    responsible: document-controller
    # The organisation, not "every controlled document": the record trigger
    # already produces one occurrence per document, and applies_to answers a
    # different question — where each of those occurrences is expected.
    applies_to: the organisation
    records: registers/document-reviews.md
  register:
    title: Document Review Record
    note: >
      One row per document reviewed. The outcome is what makes the review
      evidence: "reviewed, unchanged" and "reviewed, amended" are different
      facts, and a review with no outcome recorded is a date.
    columns:
      - {key: reviewed_on, label: Reviewed on, type: date, required: true}
      - {key: document, label: Document, type: relation, required: true,
         target: /registers/controlled-documents.md#records, display: document}
      - {key: reviewer, label: Reviewed by, type: user, required: true}
      - {key: outcome, label: Outcome, type: select, required: true,
         options: [Unchanged, Amended, Withdrawn]}
      - {key: next_review, label: Next review due, type: date}
      - {key: notes, label: Notes, type: longtext}
---

What this document must establish: the method that puts the policy into
practice, in enough detail that two different people follow it the same way.

It must carry a document from drafting through review, approval, issue and
eventual withdrawal, and say at each step who acts and what evidence that step
leaves behind. A step that leaves no record cannot be shown to have happened,
and "we always do that" is not evidence.

It must state how a change is proposed and approved, and how urgent changes are
handled differently — because they will be handled differently whether or not
the procedure admits it, and an undocumented exception route is the one nobody
audits.

It must say how a controlled document, its superseded versions and the records
each step leaves are protected from loss, destruction and falsification: where
they are kept, who may change them, and how an alteration is detected. A record
that anybody can quietly edit evidences nothing, however carefully the step
that produced it was followed.

It must say how a document's next review date is set and what happens when it
passes. That date is what the obligation above discharges against, so a
procedure that leaves it to judgement produces a register nobody can act on.
