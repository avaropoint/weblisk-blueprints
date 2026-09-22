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

## Nothing here yet

The location exists so consumers can learn to resolve it while the packs are
still in their old home. Both locations resolve; the move follows, and only then
does the old location go. See [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md) step 5.
