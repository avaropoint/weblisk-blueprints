---
id: document-control.register
version: 2.0.0
kind: register
title: Register of Controlled Documents
path: registers/controlled-documents.md

# A register carries no `satisfies:`. It is the evidence that documents are
# controlled, not the document that answers a control: `implements` onto a
# control may be asserted by a blueprint, a policy or a procedure and by
# nothing else (schemas/kinds.md, Relations), so a register's citation could
# never be recorded as answering. Its two former claims are the procedure's:
# iso_9001:7.5 it already made, and iso_27001:A.5.33 moved there.
requires: [document-control.procedure]

register:
  title: Register of Controlled Documents
  note: >
    One row per controlled document. A document that governs and is not listed
    here is not controlled, whatever it says about itself.
  columns:
    - {key: document, label: Document, type: text, required: true}
    - {key: owner, label: Owner (position), type: text, required: true}
    - {key: version, label: Version, type: text, required: true}
    - {key: approved, label: Approved on, type: date, required: true}
    - {key: next_review, label: Next review due, type: date, required: true}
    - {key: status, label: Status, type: select, required: true,
       options: [Current, Superseded, Withdrawn]}
---

What this artifact must establish: one place that answers, for every controlled
document, which version governs and when it was last agreed to be right.

It must carry at minimum the document's title, its owner by position, its
current version, the date it was approved and the date it is next due for
review. Without the last two the periodic-review obligation has nothing to
discharge against, and readiness cannot be measured — only asserted.

It is a register rather than prose, so it is a table with a schema the platform
can read: rows are records, and each row can be signed for on its own. A
register kept as a paragraph is a document about records rather than the records
themselves.
