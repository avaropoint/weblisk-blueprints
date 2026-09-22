# Programmes

One directory per pack: **what a body of work requires in order to exist and to
keep running.** Occupational health and safety, document control, quality
management, a maintenance regime.

Governed by [`../schemas/programme.md`](../schemas/programme.md).

## What a programme declares

Which documents ought to exist, what each of them answers, what it depends on,
and the recurring work the organisation takes on by adopting it — the
obligations, the registers those obligations record into, who is responsible,
how long the records are kept, and what happens when something is late.

It declares all of that in **tiers**, which is the difference between a roadmap
and a wall. Adopting a standard without them means being handed two hundred gaps
at once, and that is indistinguishable from being told the programme is
hopeless.

## What a programme is not

**Not a standard.** A standard in [`../standards/`](../standards/README.md)
declares what a published authority requires. A programme declares what an
organisation must build and operate to answer it, and cites the controls it
answers. One is the ruler; the other is the work. A programme with no framework
at all is still a valid programme.

**Not a document.** A spec here says a hazard assessment procedure must exist,
what it answers, and what it must establish *for this organisation*. It does not
say what that organisation's procedure says. That is drafted from the `brief`,
grounded in the organisation's own context, and it must never be canned.

**Not a tenant's programme.** What ships here is the programme as an industry
would recognise it. What an organisation does with it — its positions, its
evidence, its amendments — is the customer's, in the customer's repositories.
**Programmes are generic until a tenant customises them.** Nothing here may
record who holds a position, what was inspected, or how anybody is doing.

**Not a maturity model of ours.** The tiers are the pack author's. A tier may
mirror an accreditation body's audit thresholds, a regulator's phase-in dates or
a customer's rollout, and no engine can tell the difference — which is exactly
why it is data here and not a judgement in code.

## The shape on disk

    programmes/<pack>/programs/<programme>.md      the map: tiers and placements
    programmes/<pack>/artifacts/<artifact>.md      one artifact, and its brief

The **parent directory alone** says what a file is. The segment above it names
the pack, so provenance survives being merged with every other pack an
installation has. Anything else in a pack directory is ignored, so a `README.md`
beside them costs nothing.

Markdown with YAML frontmatter, because the most valuable field in an artifact
spec is its brief and the most valuable field in a tier is its rationale — and a
paragraph inside a JSON string cannot be reviewed, diffed or edited. Standards
are JSON here for the opposite reason.

## Why they are here and not in a product

They were in Weblisk Studio's own repository, which made a programme definition
invisible to the CLI, unversionable by a customer, and unreachable by anything
else that might want one — including the tooling that has to resolve the
standards a programme cites.

*"Its source"* means the product binary's source tree, not this corpus. A
programme map is a specification of what a compliance programme requires, which
is the same shape as a blueprint specifying what a component must serve. It
belongs here, and it reaches an installation the way every blueprint does: a
local checkout, then `WL_BLUEPRINT_SOURCES`, then the shared cache.

**The specification moves; the implementation does not.** Studio keeps its
planner and its engine and reads the maps from here. Anything else is a rewrite
wearing a move's clothes.

## Vertical neutrality is a property of the product, not of this directory

A programme here is **offered**, never shipped into every installation. An
occupational health and safety programme compiled into a binary means a finance
function, a software team and a design studio all carry a hazard programme they
never asked for and cannot remove.

So an industry programme is listed to somebody deciding, and becomes real when
they install it into a source their organisation owns. The one exception is the
management-system floor — controlling your own documents — which is not a claim
about anybody's industry.

## What is here

**[`construction-ohs-ca/`](construction-ohs-ca/)** — occupational health and
safety for construction work in Ontario. One programme map, **43 artifact
specifications**, 36 of which declare an obligation, placed across three tiers:
`essential` (36 artifacts — lawful to put a worker on a project), `conformant`
(5 — showable to somebody who was not there) and `certifiable` (2 — on the cycle
a certifying body actually runs). It is written against five standards in
[`../standards/`](../standards/README.md) — `construction_safety_ca`, `cor_2020`,
`iso_45001`, `isnetworld`, `csa_z462` — and cites their controls without
containing any of them.

Nine of its artifacts are **standing registers**, whose rows are the subjects the
obligations multiply over; eight obligations are **record-origin**, raised one per
row of a trigger register rather than one per period — a clearance certificate
renewed `14d before expires_on`, a notice of project filed before a start date.

It was **authored here, not moved here**, which is the whole of the argument in
the section above: a programme specification written in a product's source tree
is invisible to the CLI and unversionable by a customer, and this one never was.

## What is deliberately not here

**`document-control` is still in the product.** It is the management-system floor
named above — controlling your own documents — and it is the one pack that ships
rather than being offered, because it makes no claim about anybody's industry.
Moving it here would make the floor an option.

**Studio's `packs/ohs` has not moved either.** Both locations resolve and neither
is wrong; that move is [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md) step 5b, and it
waits on 5a being released rather than on anybody's opinion.
