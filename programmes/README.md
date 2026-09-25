# Programmes

One directory per programme: **what a body of work requires in order to exist
and to keep running.**

There is no second noun. Studio's code called this container a *pack* for a
while; the container and the programme are the same thing, and CORPUS_SHAPE.md
step 5c records why the word went. Occupational health and safety, document control, quality
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

**Not a maturity model of ours.** The tiers are the programme author's. A tier may
mirror an accreditation body's audit thresholds, a regulator's phase-in dates or
a customer's rollout, and no engine can tell the difference — which is exactly
why it is data here and not a judgement in code.

## The shape on disk

    programmes/<programme>/programs/<map>.md        the map: tiers and placements
    programmes/<programme>/artifacts/<artifact>.md  one artifact, and its brief

The **parent directory alone** says what a file is. The segment above it names
the programme, so provenance survives being merged with every other programme an
installation has. Anything else in the directory is ignored, so a `README.md`
beside them costs nothing.

`programmes/` is also accepted in place of `programs/` inside a programme,
because the rest of this corpus and all of Studio spell the word that way and a
directory that spelled it naturally used to load its artifacts, carry no map, and
report nothing. Existing ones keep `programs/`; neither spelling is wrong.

### The paths a programme declares

An artifact's `path:` is **flat, kind-first, two segments** — `<kind>/<subject>.md`
— and the kind directory is one of the stems
[`../schemas/kinds.md`](../schemas/kinds.md) declares. There is no subject
segment: the subject is in the programme's `domains:` and in the directory name,
and a third copy in the path is a third thing to keep in step. It is also read
first by the classifier, so an unvetted word there decides a node's kind by luck.

A **procedure** is named for the activity, **singular**. A **register** is named
for the things collected, **plural**. So a procedure can never share a basename
with the register it declares. No kind suffix in a filename — the directory
already says it.

**A path is unique across every programme an installation loads, not within
one.** This is also why the container is not a namespace, and so why it never
needed a noun of its own. Two programmes producing one path means one document,
and whichever is drafted second
overwrites the first. The generic name belongs to the document that is generic:
`document-control` is on every installation and holds the unqualified names; a
programme that is one industry's qualifies against it.

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
a certifying body actually runs). It is written against the Ontario instruments that actually bind — the
*Occupational Health and Safety Act* and its construction, training, confined
space, asbestos, naloxone and WHMIS regulations, the *Workplace Safety and
Insurance Act, 1997* and its first aid regulation — together with `cor_2020`,
`iso_45001`, `isnetworld` and `csa_z462`, all in
[`../standards/`](../standards/README.md), and cites their controls without
containing any of them.

Nine of its artifacts are **standing registers**, whose rows are the subjects the
obligations multiply over; eight obligations are **record-origin**, raised one per
row of a trigger register rather than one per period — a clearance certificate
renewed `14d before expires_on`, a notice of project filed before a start date.

It was **authored here, not moved here**, which is the whole of the argument in
the section above: a programme specification written in a product's source tree
is invisible to the CLI and unversionable by a customer, and this one never was.

**[`ohs/`](ohs/)** — occupational health and safety, generic: the programme any
employer with workers needs, with no jurisdiction in it. One programme map, **29
artifact specifications** across three tiers — `essential` (13), `conformant`
(10) and `certifiable` (6) — citing `iso_45001`, `cor_2020` and `isnetworld`.

It **moved here from Studio's `packs/ohs`** on 2026-09-22
([`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md) step 5b), which is the other half of
the argument above: it is the programme that proves a specification kept in a
product's source tree drifts unseen. Four faults were found in it by the move
alone, three of them the same faults `construction-ohs-ca` had been corrected for
two commits earlier.

It overlaps `construction-ohs-ca` heavily and the two are **alternatives, not
layers**: a constructor in Ontario adopts the second, everybody else the first.
Where both name one document their paths are deliberately different, so an
installation carrying both is told which programme each document belongs to
rather than silently keeping two of it.

**[`information-security/`](information-security/)** — an information security
management system aligned to **ISO/IEC 27001:2022**, using the 2022 Annex A
control set of four themes and 93 controls rather than the 2013 annex. One map,
**24 artifact specifications** authored here and eleven more placed from the IT
and records programmes, across three tiers. It also cites `nist_csf_2`,
`can_ciosc_104` — the Canadian small-and-medium baseline behind CyberSecure
Canada — `iso_22301` for continuity, and `soc2` where an artifact genuinely
answers a trust services criterion. Three obligations are record-origin: a
security incident is investigated five days after it is reported, a risk is
re-scored before its own review date, and a supplier is reassessed before its
own. Secure development (A.8.25–A.8.33) is deliberately excluded and belongs in
the Statement of Applicability's exclusions rather than as ten permanently
unanswerable gaps.

**[`it-operations/`](it-operations/)** — the operational half: acceptable use,
IT assets, endpoints and mobile devices, backup and recovery, change management,
account provisioning, remote access, patching, software and cloud approval,
network security and configuration baselines. **12 artifacts** citing
`cis_controls`, `can_ciosc_104` and ISO/IEC 27001. Split from the security
programme because the two are done by different people on different rhythms, and
several of its artifacts are placed into the security map rather than written
twice.

**[`privacy/`](privacy/)** — PIPEDA and CASL, for any Ontario company. **14
artifacts** across three tiers. The jurisdiction question is the programme:
PIPEDA applies federally to commercial activity, **Ontario has no private-sector
privacy statute of general application**, and PIPEDA does not reach employee
information for a provincially regulated Ontario employer at all. Quebec's
`quebec_law25` is cited because an Ontario company with Quebec customers is
bound by it for those customers. A privacy request is answered 30 days after it
arrived — the one obligation in this corpus whose interval is recorded as
`required` because an Act sets it — and a breach is assessed three days after
discovery.

**[`privacy-health-on/`](privacy-health-on/)** — **PHIPA**, for health
information custodians and their agents and electronic service providers, and
for nobody else. **5 artifacts** authored plus nine placed. It exists separately
because PHIPA binds by role rather than by geography: an employer holding sick
notes is not a custodian, and adopting these obligations where they are not owed
produces gaps that can never be closed. Two duties are stricter than PIPEDA's and
are the reason the programme is worth having — notice to the individual with **no
harm threshold**, and an annual statistical report to the Commissioner by 1 March.

**[`privacy-public-sector-on/`](privacy-public-sector-on/)** — **FIPPA and
MFIPPA**, for organisations that hold an Ontario institution's records. **4
artifacts** authored plus nine placed. Neither Act binds a private-sector supplier
directly; what binds it is the institution's contract, which is why the flow-down
of terms to subcontractors and a 24-hour contractual notification clock are the
substance of it.

**[`employment-ontario/`](employment-ontario/)** — the **Employment Standards
Act, 2000**, the **Human Rights Code**, the **AODA** and its Integrated
Accessibility Standards Regulation, and the OHSA's workplace violence and
harassment duties. **16 artifacts** across three tiers, covering the recent
amendments that are most often missed: the disconnecting-from-work and
electronic-monitoring policies required at 25 employees, the prohibition since
July 2024 on engaging unlicensed temporary help agencies and recruiters, and the
job-posting requirements in force 1 January 2026. Accessibility obligations step
up at 20 and at 50 employees, so the headcount is a column on two registers
rather than an assumption.

Workplace violence and harassment sits here rather than in `ohs/` because the
generic occupational health and safety programme does not carry the OHSA
ss. 32.0.1–32.0.8 duties at all — only `construction-ohs-ca` does, written for a
constructor. `emp.violence-harassment` answers it for a single-workplace
employer, at a different path, and an organisation carrying both programmes
removes one from its plan.

**[`records-management/`](records-management/)** — retention, disposition, legal
hold and vital records. **8 artifacts**, built around a register rather than a
document because **Ontario has no general private-sector retention statute**: the
schedule holds a dozen authorities at once and the `authority` column is what
separates a defensible period from a habit. It is placed into five other
programmes rather than restated, so a change to a keeping period reaches every
programme that depends on it.

## What is deliberately not here

**`document-control` is still in the product.** It is the management-system floor
named above — controlling your own documents — and it is the one that ships
rather than being offered, because it makes no claim about anybody's industry.
Moving it here would make the floor an option.
