---
id: document-control
version: 1.0.1
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
starting a document of that kind from nothing, whether or not a spec names
them. The control matrix carries no control: its rows are generated from the
standards the scope has adopted, each citing the control by id, edition and text
digest, as [`../../schemas/standard.md`](../../schemas/standard.md#outputs-cite-the-control-text-they-were-made-from)
requires of every output made from a standard.
