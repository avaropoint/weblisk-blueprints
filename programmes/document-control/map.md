---
id: document-control
version: 1.1.0
title: Document Control Programme
order: 10
domains: [governance]
# Only frameworks whose control set holds a documented-information requirement
# are named. Each artifact cites its controls by id under `satisfies`; what a
# cited control requires is read from ../../standards/<id>.json at the edition
# the tenant adopted, and is never restated here.
conforms_to: [iso_9001, iso_45001, iso_27001]

tiers:
  - id: essential
    title: Required to operate
    rationale: >
      The two documents without which no other programme can be trusted: a
      stated rule for how controlled documents come into force, and the method
      that puts it into practice. Below this line an organisation has documents
      but no way to say which version governs, who approved it, or whether the
      copy somebody is reading is the current one.
  - id: conformant
    title: Audit-ready
    requires: essential
    rationale: >
      The programme can be shown to work. There is a register naming every
      controlled document, its owner, its version and when it is next due for
      review — so "is this current?" has an answer that is not somebody's
      memory.
  - id: certifiable
    title: Externally auditable
    requires: conformant
    rationale: >
      The organisation checks itself on a cycle and keeps the record of having
      done so, which is what a certifying body asks for first and what nobody
      can reconstruct after the fact.

# The standing work adopting it takes on, and who is told when it slips. The
# services these need, and the build plan adopting emits, are derived from
# them (../../schemas/programme.md, "What a programme runs on").
operations:
  - id: due-sweep
    title: What is due
    does: due-sweep
    schedule: {cadence: daily, at: "07:00"}
    why: >
      Three obligations, two of them yearly and one per controlled document,
      and a review is owed on the day it lapses whether or not anybody opens
      the register. Daily, at the start of an office day, so that a review
      coming due is told to the document controller once, when it advances,
      and an overdue one again only when it escalates. It never remediates.
  - id: programme-readiness
    title: Programme readiness
    does: programme-readiness
    schedule: {cadence: monthly, at: "07:00", day: 1}
    why: >
      Whether the four documents exist and are cited, and whether their
      obligations are producing attested records. Monthly, because document
      control does not move week to week. It reports and drafts nothing.

notices:
  - id: review-overdue
    on: [obligation.overdue]
    to: [senior-management]
    says: >
      A document-control review is overdue: say which review it was, whose it
      was, and how late it is.
    why: >
      None of this programme's obligations declares an escalation, and each
      is owed once a year or once per document, so the first lapse is the one
      to hear about. An organisation whose controlled documents are past
      review cannot say which version governs, and senior management own the
      management system it undermines; they are told once, when it falls
      overdue, and the document controller it belongs to is told by the
      obligation itself.

artifacts:
  - {id: document-control.policy, tier: essential}
  - {id: document-control.procedure, tier: essential}
  - {id: document-control.register, tier: conformant}
  - {id: document-control.internal-audit-procedure, tier: certifiable}
---

The management-system spine, and the one programme that is not about an industry.

Every framework a tenant can be measured against assumes underneath it that the
organisation controls its own documents: that there is one current version, that
somebody owns it, that changes are approved rather than merely made, and that the
record of all this survives the person who kept it. None of those assumptions is
specific to what the organisation does.

Four artifacts, deliberately: enough to demonstrate the whole loop — a policy
that governs, a procedure that implements it, a register its obligations write
into, and an audit that checks the result — without asserting anything about an
industry nobody has named.

**Offered and adopted like every other programme.** It used to be compiled into
the product and loaded into every scope's catalogue, which gave it no corpus
revision to pin, no adoption record to refuse a second adoption against, and no
way for an organisation to decline it. Not being about an industry makes it a
good first programme to adopt, not a reason for it to be present uninvited.
[`../README.md`](../README.md#what-is-here) says where it sits among the rest.

**It holds the generic names.** A path is unique across every programme an
organisation adopts, so `procedures/internal-audit.md` and
`registers/controlled-documents.md` belong to this programme, and a programme
written for one industry qualifies its own against them.

**Its `templates/` are the generic starting shapes** — a blank document, a
policy, a procedure, a standard and a control matrix — offered to anybody
in a scope that has adopted this programme who starts a document of that kind
from nothing, whether or not a spec names them. They arrive with the adoption
and only with it: a scope that has not adopted `document-control` has no blank,
policy or procedure form at all, and is told so rather than handed one. The control matrix carries no control: its rows are generated from the
standards the scope has adopted, each naming only the standard and the control
id. The edition and text digest a row was made against are a `generated_from`
fabric claim recorded when the document is created, never bytes in it — a
document carries nothing of that reference
([`../../schemas/standard.md`](../../schemas/standard.md#outputs-cite-the-control-text-they-were-made-from),
"What records the reference").
