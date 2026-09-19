# Standards

**Industry standards** — the published criteria an organisation is measured
against. ISO 27001, ISO 45001, SOC 2, NIST 800-53, CSA B51, COR 2020, and the
rest.

37 of them, as JSON. Governed by [`../schemas/standard.md`](../schemas/standard.md).

## What a standard here is, and is not

A standard **declares**: its identity, authority, scope and status; its families;
and its controls, each with an identifier, what it requires, and how conformance
is judged.

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

## Known faults, found on arrival

Checked mechanically when these moved here. The corpus satisfies every
structural rule in the schema — 37 standards, 167 families, 951 controls, all
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
