# Standards

**Industry standards** — the published criteria an organisation is measured
against. ISO 27001, ISO 45001, SOC 2, NIST 800-53, CSA B51, COR 2020, and the
rest.

53 of them, as JSON. Governed by [`../schemas/standard.md`](../schemas/standard.md).

## What a standard here is, and is not

A standard **declares**: its identity, authority, scope, status and the places it
has force; its families; and its controls, each with an identifier, what it
requires, and how conformance is judged.

A standard does **not** know who adopted it. Which standards an organisation is
measured against, how well it does, and what evidence answers which control are
**tenant content** — the customer's, in the customer's repositories. A standard
here is the ruler, never the measurement.

## Why they are here and not in a product

They were embedded in Weblisk Studio's Go packages. That made them invisible to
the CLI, unversionable by a customer, and unavailable to anything else that might
want them — including a programme in [`../programmes/`](../CORPUS_SHAPE.md) that
needs to cite the standards it operationalises. A citation that cannot resolve is
not a citation.

Studio still carries a copy, embedded so a fresh install is useful without a
network call, and guarded against drifting from this one. Authored here; copied
there. See [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md).

## One is generated, and is not here

`weblisk_framework.json` — the Weblisk Framework standard — is **derived from
`schemas/`** by a generator rather than authored. It stays where it is generated.
Copying a derived artifact into the corpus would create a second copy free to
drift from the thing it was derived from.

## JSON, in a corpus of Markdown

Deliberate. A control set is data a tool reads, not prose a person reads
end-to-end, and the format a customer edits it in should be the one their tools
already handle. `MISSION.md` says complimentary content is "JSON and Markdown",
and this is the JSON half.

## The corporate governance layer, added 2026-09-24

Six standards were added to make the corporate programmes — information
security, IT, privacy, employment and records — citable rather than merely
described. Every one of them binds an Ontario-incorporated company, or is scoped
precisely so that it is clear when it does not.

| id | what it is | reach |
|---|---|---|
| `phipa_ontario` | *Personal Health Information Protection Act, 2004* and O. Reg. 329/04 | `CA-ON`, and **only** health information custodians, their agents and their electronic service providers |
| `employment_standards_ontario` | *Employment Standards Act, 2000*, including the Working for Workers amendments in force to 1 January 2026 | `CA-ON`, provincially regulated employers only |
| `ohrc_ontario` | *Human Rights Code* | `CA-ON`, every employer regardless of size |
| `aoda_ontario` | AODA and the Integrated Accessibility Standards Regulation (O. Reg. 191/11) | `CA-ON`, every organisation with at least one employee |
| `iso_22301` | Business Continuity Management Systems, 2019 | `international` |
| `casl` | Canada's Anti-Spam Legislation | `CA` |

**`employment_standards_ontario` is not `esa_oesc`.** The latter is the
Electrical Safety Authority's Ontario Electrical Safety Code and shares only an
abbreviation. The ids are deliberately unlike each other for that reason.

**None of the six carries `mapped_controls`.** The equivalences are real and
several are obvious — PHIPA's safeguards duty and PIPEDA principle 7, the Code's
harassment right and the OHSA's harassment programme — but a mapping must be
stated from both sides or a reader can only see it from one, and adding the
reciprocal would mean rewriting 41 existing standards. The relationships are
stated in the control descriptions instead, where they can be read and cannot be
mistaken for a machine-resolvable claim.

## Known faults, found on arrival

Checked mechanically when these moved here. The corpus satisfies every
structural rule in the schema — 53 standards, 242 families, 1,235 controls, all
ids unique, every control naming a family that exists — with one exception.

**Four mappings in `pipeda.json` cite GDPR controls that do not exist.**
`GDPR-ACC-1`, `GDPR-LB-1`, `GDPR-SEC-1` and `GDPR-DSR-1`, on controls
PIPEDA-1, -3, -7 and -9. GDPR's control identifiers are article citations —
`Art.5(1)(a)`, `Art.6` — so these are not a missing `gdpr:` prefix but a naming
scheme GDPR never used.

**Left as they are, deliberately.** Repairing them means deciding which GDPR
article each PIPEDA control maps to, and that is a compliance judgement, not a
formatting fix. A mapping invented to make a checklist pass would be worse than
a dangling one, because a dangling one is visible.

The other 234 mappings are well-formed `<standard>:<control>` and resolve.
