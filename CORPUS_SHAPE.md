# The shape of the corpus

> **Status: proposal, for review. Nothing has moved.**
> Written 2026-09-18. It records what each family is *for*, names three that are
> currently misfiled, and sequences the work.

## The problem

`platforms/` holds four files that are not the same sort of thing:

| file | really a |
|---|---|
| `go.md` | programming language |
| `rust.md` | programming language |
| `node.md` | runtime, for the JS/TS language |
| `cloudflare.md` | platform, for the JS/TS language |

`node` and `cloudflare` share a language and nothing can see it, so the shared
JS/TS conventions are stated twice. And "build this in TypeScript, for AWS" is
not expressible: there is no axis for it.

`standards/` has the opposite problem. It is described as *"best practice
guidance… how developers build **with** the framework"*, and its files are
`islands` · `components` · `pages` · `theme` · `assets` · `connections` ·
`global`. Those are not general project standards — **they are the Weblisk
client framework's own concepts.** The framework axis already exists here,
under a name that means something else to everyone outside this repository.

And `standards` means something specific in the product this corpus serves: an
**industry standard** — ISO 27001, SOC 2, NIST 800-53, CSA B51. That is the
sense a customer uses, and the corpus currently spends the word on something
else.

## What this corpus is for

The families below are not a filing convention. They are the reason the
framework is worth having **as a collection**: enough declared, in one place,
that a model can build a working enterprise capability from it without guesswork.

The target, stated as a person would ask for it:

> *"I need a programme to run occupational health and safety."*

and within minutes the model has built and bootstrapped what it takes to operate
one — from three inputs:

| input | supplies |
|---|---|
| the **programme** specification | what the programme requires: artifacts, obligations, registers, agents, workflows, tasks, forms, at which tier |
| the **industry standards** it conforms to | the controls those artifacts must answer |
| the **tenant's** knowledge | what the organisation already has, and what is therefore missing |

Then it connects to Studio, where people collaborate on it, govern it and run it.

**Programmes are generic until a tenant customises them.** What ships here is the
programme as an industry would recognise it; what a tenant does with it is the
tenant's.

**And Studio reads all of this rather than containing it.** Industry standards
and programme definitions buried in a product's Go packages are invisible to the
CLI, unversionable by a customer, and unavailable to anything else that might
want them.

### The programme packs are already blueprints

This is not a proposal to invent a form. `packs/ohs/` in Studio already declares:

```yaml
id: ohs.ppe-programme
kind: procedure                       # the declared kind vocabulary
satisfies: [cor_2020:COR-10, ...]     # relations onto industry-standard controls
requires: [ohs.hazard-assessment-procedure]
declares:
  obligation: {activity, cadence, responsible, applies_to, records}
  register:   {title, columns…}
```

Frontmatter, `requires`, `declares`, and relations onto controls — structurally a
blueprint, already using the kinds vocabulary, already citing standards the way
`implements: [control:…]` does. And a programme map declares `conforms_to` and
its **tiers** (essential · conformant · certifiable), which is how a roadmap
appears instead of two hundred gaps at once.

### What a programme cannot yet declare

Obligations and registers, yes — including a register's column schema. But
**nothing declares the agents, workflows, tasks or forms a programme needs.**
That is the gap between what exists and the sentence at the top of this section,
and it is the substance of the work rather than a detail of the move.

### The pipeline is the one that already exists

    weblisk component content init    architecture/content.md  → a service
    weblisk programme ohs init        programmes/ohs.md        → agents, forms,
                                                                 registers,
                                                                 workflows,
                                                                 documents

Same dispatch, same verification gate, same conformance discipline. A programme
blueprint declares what must exist and what it depends on, exactly as an
architecture blueprint does; only the target differs.

### Two differences of form to reconcile

- Packs use **YAML frontmatter**; corpus blueprints use a `<!-- blueprint -->`
  declaration block governed by `schemas/common.md`. One of the two wins, and the
  loser is converted — not left as a second dialect.
- Packs say `satisfies:`; the relation vocabulary says `implements` onto a
  `control`. Same claim, two words.

#### What driving a programme end to end measured

Recorded here rather than acted on: **the reconciliation is still the user's
decision**, and the measurement changes what is being decided.

**The two words are at different layers, and may not be in conflict at all.** A
pack spec's `satisfies:` is a *specification-level* claim — what an artifact must
answer, asserted by the pack author before any document exists. A **document's**
citation is a claim about a file that does exist, and `schemas/kinds.md` makes
`implements` the one declared relation a content kind may assert onto a
`control`, saying why: it exists *"to state which control a document answers,
instead of leaving it to keyword inference."* Converting one word into the other
would flatten two claims into one rather than remove a dialect.

**What was in conflict is what the drafted documents carried.** They copied the
pack's `satisfies:` key into the document's own frontmatter, where nothing reads
it as a relation. So the only citations that reached the ledger were the
conformance producer's keyword guesses — **2 of 5 controls on the first real
document, both merely `suggested`.** Every artifact stayed `present_uncited`, the
plan never subtracted it, and a programme that had been drafted and filed
reported as not begun.

**The framework-qualified form is the one that works.** Verified against a live
ledger: `implements: [control:iso_45001:5.1]` resolves and clears the citation.
The bare form is ambiguous, and measurably so: **four standards in `standards/`
declare a control called `5.1`** (`iso_45001`, `iso_9001`, `pci_dss`,
`cis_controls`). An unqualified control id is a join key onto whichever framework
answers first, which is exactly the guess the relation exists to stop. Nothing
refuses it, so `schemas/kinds.md`'s example now shows the qualified form — an
example is what gets copied. `skills/kinds/SKILL.md` still shows the bare one;
that copy is mirrored into the CLI and has to move with it.

**And the two bullets above are one problem, not two.** The producer that turns a
declaration into a ledger edge has to recognise the header the declaration is
written in. A vocabulary agreed in a form nothing reads is not agreed.

---

## Four axes, not two

Generation, and governance, resolve along four independent questions:

| axis | answers | examples |
|---|---|---|
| **what** | what am I building? | orchestrator, agent, content service, a CLI |
| **language** | what is it written in, and in what style? | Go, Rust, TypeScript |
| **framework** | built *with* what? | weblisk, astro, next |
| **platform** | running on what, offering what services? | Cloudflare Workers, Node, AWS, Microsoft 365 |

A framework constrains a language and often a platform without dictating either,
which is why it is its own axis rather than a flavour of one.

**A platform needs a language too.** Driving Microsoft 365 means writing a client
— in some language, against that platform's surface. The axes hold for governing
a provider exactly as they do for generating a tenant.

## Target families

| family | holds | today |
|---|---|---|
| `schemas/` | how a blueprint is written | unchanged |
| `protocol/` | wire contracts | unchanged |
| `architecture/` | components to build | unchanged |
| `patterns/` | cross-cutting patterns | unchanged |
| `agents/` | agent blueprints | unchanged |
| **`languages/`** | Go, Rust, TypeScript — what code is written in | split out of `platforms/` |
| **`platforms/`** | Cloudflare, Node, AWS, M365 — what it runs on and offers | narrowed |
| **`frameworks/`** | **weblisk**, astro, next — what it is built *with* | mostly from `standards/` |
| **`standards/`** | **industry standards** — ISO, SOC 2, NIST, CSA | repurposed |
| **`programmes/`** | programme definitions: artifacts, obligations, registers, tiers — and, to be added, the agents, workflows, tasks and forms a programme needs | **moved out of Studio** |
| `intl/` | **reserved** — locale and spoken-language constructs | new, empty |

`frameworks/weblisk` is Weblisk's own client framework, a peer to Astro and Next
rather than a special case. `frameworks/` should read as *frameworks in general,
given a language* — not as this one framework's rules.

`intl` is reserved now and built later. It is the ECMA/ICU word, so it reads
unambiguously, and reserving it keeps "language" meaning *programming language*
everywhere else without having to qualify it.

## A rule that needs reconciling, not breaking

MISSION and Studio's CLAUDE.md say:

> Standards, packs, templates and domain catalogues are **complimentary
> content**… They ship with the platform and **do not live in its source**.

Read literally, that forbids programmes moving here. It should not, and the
reason is what this repository already is: blueprints resolve **local checkout →
`WL_BLUEPRINT_SOURCES` → the shared cache at `~/.weblisk/blueprints`**. That is
precisely the complimentary-content delivery model — shipped with the platform,
overridable, replaceable.

So *"its source"* means **the product binary's source tree**, not the
specification corpus. A programme map is a specification of what artifacts a
compliance programme requires, which is the same shape as a blueprint specifying
what a component must serve. It belongs here.

The wording in CLAUDE.md should say so, or the next reader will reach the
opposite conclusion from the same sentence.

## Sequence

Ordered cheapest and safest first. Each step stands alone.

**1 — `languages/`, and `intl/` reserved.** In two halves, for the reason below.

**1a.** The corpus gains `languages/`, and every consumer learns to resolve a
platform binding from **either** family. Nothing moves yet, so nothing breaks
whichever corpus a reader has. **DONE.**

**1b.** `platforms/{go,rust}.md` move to `languages/`. **Done.**

~~`node.md` splits, its JS/TS conventions becoming `languages/typescript.md`~~ —
**refuted, see below.**

**2 — `frameworks/`, with `frameworks/weblisk`. DONE.** All nine moved;
`schemas/standard.md` became `schemas/framework.md`; `standards/` is reserved.

`code.md` and `project-structure.md` went to `frameworks/weblisk/` whole rather
than splitting: `code.md` is *client* code conventions — the HTML, CSS and
JavaScript a browser receives — which is the framework's output, not a language's
rules.

**3 — `--language` and `--platform` as separate flags.** CLI. `PlatformBlueprint`
is a hard-coded switch whose `default:` silently returns Go, so an unknown
platform is built as Go today; it becomes a declared lookup. `platform` threads
through roughly eight dispatch files. **Coordinate — this repository's consumer
is under active work.**

**4 — `standards/` repurposed to industry standards. DONE.** 37 authored
standards moved from Studio's Go packages — 167 families, 951 controls — with
`schemas/standard.md` written from the data rather than ahead of it. Studio keeps
an embedded copy so a fresh install needs no network call, guarded against drift,
which is the fourth use of that pattern after skills, the kind declaration and
the fabric.

`weblisk_framework.json` stayed: it is generated from `schemas/`, and copying a
derived artifact into the corpus would create a second copy free to drift from
what derived it.

Found on arrival and left alone: four mappings in `pipeda.json` cite GDPR
controls that do not exist — GDPR's identifiers are article citations, so these
are a naming scheme it never used rather than a missing prefix. Repairing them is
a compliance judgement, not a formatting fix.

**4a — a standard says where it has force. DONE.** `applies_in` on
`schemas/standard.md`: a list of ISO 3166-1 alpha-2 codes, ISO 3166-2
subdivision codes, or the single token `international`. All 37 standards
backfilled, and Studio's embedded copy with them.

Geography was carried only by convention — inside the `id`
(`ontario_building_code`, `quebec_law25`) and in `scope` prose — so *"which
standards apply to a company operating in Ontario"* had no answer, and
`construction_safety_ca` was indistinguishable from California by anything but a
person reading the description. That question is the one a programme asks when
the same structure must bind to different standards per country or province,
which is step 6's problem arriving early.

**Optional, and the transition is the reason.** The prerequisite below says a
corpus change is not real until it is pushed, and that consumers must tolerate
both states in the meantime. A required tenth field would have made every
customer-authored standard invalid the moment a build learned about it, and
every standard here invalid on any build that had not. So it is optional, an
absent value means *unstated* rather than *global*, and the corpus is filled in
completely — which is what lets it be promoted to required later, once no
supported build predates it.

**Not `jurisdiction`.** `protocol/federation.md` already spends that word on
data residency, on the orchestrator manifest and in `JurisdictionSpec`. Same
shape of answer — a list of ISO 3166 codes — to a different question: where an
authority's writ runs, versus where bytes may come to rest. An organisation
governed by Ontario law can contract that its data resides in Germany, and a
word that answered both would be wrong in one of them half the time.

**5 — `programmes/`.** Studio's `packs/` and the substance of
PROGRAM_ARCHITECTURE and PROGRAM_CONSTRUCTION, plus `schemas/programme.md` for
the form. The largest step, and the one with the most product behind it.

**5a — the location and the schema. DONE.** `programmes/` exists with a README,
and [`schemas/programme.md`](schemas/programme.md) declares the form — derived
from the loader that reads these files rather than written ahead of it. Studio
resolves **either** location: the corpus is consulted first and `packs/` answers
for every name it does not carry, on exactly the terms `packs/` was already
offered on. Nothing moved, and the planner and the engine are untouched.

The most valuable part of that schema turned out to be the **closed
vocabularies**, because none of them is enforced when a file loads. `applies_to`
outside `the organisation` / `each project`, an unreadable `cadence`, a `cadence`
and a `for:` together, an unparseable `escalate.after` — every one of those
produces a file that parses, renders and reviews cleanly, and is discovered
later as an obligation reported "undeclarable", or as a readiness number that is
wrong in the flattering direction. They were stated in Go comments, in three
packages, and nowhere an author would look.

Three things found while deriving it, all left alone. A pack may declare a
`creates:` card and have it **silently dropped** — the field exists only on the
engine's own obligation type, and the YAML decoder discards what it cannot place.
`kind:` is not checked against [`schemas/kinds.md`](schemas/kinds.md), so packs
carry kinds the corpus does not declare and nothing says so. And an
`escalate.after` that does not parse is **silently inert**: the code beside it
states that an unreadable escalation "is NOT silently ignored", and the only
caller returns without a word — an obligation with an unreadable escalation path
is indistinguishable from one that declared none.

**5b — the packs themselves. DONE.** `packs/ohs` is now
[`programmes/ohs/`](programmes/ohs/) — 29 artifacts and one map. `packs/` in
Studio still resolves and is now what it should always have been: where an
*installation* may drop a pack, not where we keep one. `document-control` stays
embedded in the product; it is the management-system floor and moving it here
would make the floor an option.

Four things the move surfaced, all of which were invisible while the pack sat in
the product tree beside nothing it could collide with.

**A path is only unique within the pack that wrote it.** Merged into one
catalogue, `ohs` and `construction-ohs-ca` both wanted
`procedures/return-to-work.md` and `registers/emergency-drills.md`, and `ohs`
wanted `procedures/internal-audit.md` — which `document-control`, present on
every installation, already produces. Seven collisions in all. The loader reports
a derived register colliding with anything; it says nothing about two AUTHORED
artifacts at one path, which is the commoner case and the one a person browsing
either pack cannot see.

**`kind:` still is not checked, and two packs still carry undeclared kinds.**
`ohs` had `kind: plan` and `kind: matrix`, neither of which
[`schemas/kinds.md`](schemas/kinds.md) declares, so both resolved to the zero
value — a node with no capabilities, answering controls it could not count
toward. The same fault 11d5714 fixed in `construction-ohs-ca`, found the same way
and not by any check.

**`plans/` was a directory contradicting its only occupant**, exactly as it was
in the other pack: one file, whose own `structure:` said `procedure`.

**An obligation triggered by rows that nothing produces reports as no work.**
`ohs` chained incident → investigation → corrective action and each artifact
declared the register named after ITSELF rather than the one its obligation
writes into, so every block sat one link upstream of where the engine
materialises it: the incident register at the head of the chain was never
produced at all, and `registers/investigations.md` was created carrying incident
columns. The loader checked `records:` and not `for.records:`, so the chain the
programme's own overview describes could not start and nothing said so. Studio
now reports it.

**5c — the word. DONE.** The container was called a **pack** in Studio's code and
a **programme** everywhere a person reads: `programmes/` is the family here,
`schemas/programme.md` is the declaring schema, and what a customer adopts is a
programme. Two words, one thing — the fault this corpus already names for
`satisfies`/`implements` and Studio names for platform/provider/integration.

The distinction a pack *could* have carried is the container: a shipping unit
holding a programme the way a crate holds what is in it. Nothing used it that
way, and four measurements say so. Every provided container holds exactly one
map. A container holding no map is not offered at all, so what makes one
offerable is the programme in it. The name is carried for provenance and nothing
joins on it. And **a path is unique across containers, not within one** — stated
three sections above as a finding — so the container is not even a namespace. The
capability was called `programme-packs`, which is the two words already conceding
they name one thing.

So programme won and pack was converted, in Studio: Go identifiers, the file
names, the API routes (`/api/programmes/…`, with the old paths kept as aliases
for a browser holding an older page), the UI, and the source capability — whose
id is *persisted* in every installation's taxonomy and is therefore read under
both spellings, converted once at load, and never written again. The on-disk layout inside a programme was left alone at the time — it is content
in this corpus and in every tenant's copy, and moving it was its own decision.

**5d — that decision, taken.** `artifacts/` became `specs/`, because *artifact*
everywhere else in the product means a real document at a real path and these
files are specifications for documents. `programs/`, a directory holding one file
and spelled two letters from its own parent `programmes/`, became that one file:
`map.md`. `templates/` kept its name and started travelling with an install,
which it never had. Studio reads every earlier spelling forever, so no tenant's
adopted copy was touched and there was no cutover.

**6 — a programme declares what it needs built.** Agents, workflows, tasks and
forms, so `weblisk programme <id> init` can bootstrap an operating programme from
the specification, the standards it conforms to, and the tenant's knowledge. This
is the step that makes the collection worth having; the five before it are moving
furniture so that this one is possible.

**7 — `positions/`, and the audience the corpus did not have. DONE.**

Every skill in [`skills/`](skills/README.md) is a **builder's** skill —
`agents`, `blueprints`, `changes`, `cloudflare`, `domains`, `gateways`, `go`,
`hubs`, `kinds`, `node`, `operators`, `rust`, `tenants`. Not one is for a person
doing a job *inside* a tenant, which is the audience every programme in
[`programmes/`](programmes/README.md) is written for.

The programmes already name those people, as data, with weight: measured across
the corpus, **twenty-one positions named 475 times** through `responsible`,
`escalate.to`, `approvers` and `approved_by`. So a role brief is **derived**,
and [`positions/`](positions/README.md) holds only the half derivation cannot
reach — what to do first, what good looks like, how it goes wrong.

**The derived half is rendered on read and is never a file.** It is a function
of which programmes an organisation adopted and at which tier, and neither is
knowable here: one position id resolves to 15 obligations and 17 inbound
escalations under `construction_ohs_ca`, and to 15 obligations and 1 under
`ohs`. Same id, different job. This is the same decision taken for
`weblisk_framework.json` in step 4, for the same reason.

**It is not a directory under `skills/`, and that is the load-bearing part.** A
skill there is named for a verb, is installed by the CLI when that verb runs,
and is embedded in the CLI byte-for-byte with a guard. Fourteen generated files
would mean regenerating, copying them into a second repository, and editing a
README table on every programme edit — and the guard's red light would come to
mean *"you forgot to run the generator"* rather than *"two copies disagree"*.

**The seam is a file boundary.** The generator reads `positions/<id>.md` and
never writes one: no merge, no managed region, no markers. A generator that owns
part of a file eventually owns the rest of it. A guide is refused if it names an
artifact id or a register path — those are the two shapes that drift — and
reported as an orphan if no programme names its position.

Four things the derivation surfaced, recorded in the report and in the code that
now guards them: Studio's existing `programPositions` has no escalation duty at
all, so the position that catches every overdue thing in an organisation was
reported as having one obligation; a derived register spec was double-counting
every approver; an unresolvable programme id produced an empty brief that read
as *"this position does nothing"*; and **143 of 151 registers in the corpus name
exactly one approver**, so sole approval is how this corpus is written rather
than a fact about any one position.

## Refuted: there is no JavaScript blueprint to extract

The plan said `platforms/node.md` was mostly JavaScript conventions and that
`cloudflare.md` restated twelve of the same sections, so a shared
`languages/typescript.md` would remove the duplication. **That was measured
wrong.**

The twelve shared *headings* are shared because `schemas/platform.md` requires
them. Every platform blueprint answers the same questions — that is the schema
working, not duplication. The content under them is different and correctly so:

| | node.md | cloudflare.md |
|---|---|---|
| Primitive Mapping | "Provided in Node.js by" — `node:crypto`, `node:fs` | "Provided on Workers by" — Web Crypto, KV |
| Storage | flat-file JSONL via `node:fs`; every SQLite option is third-party | Workers KV, Durable Objects, R2 |
| Conventions | single-threaded event loop, `node:worker_threads` | V8 isolates |

Measured: **31 identical substantial lines out of 731**, about 4%, and those are
the schema's own explanation of what a Primitive Mapping is — repeated for a
reader's benefit, already linking to `schemas/platform.md`, and not language
conventions at all.

**So the split was counting headings and calling them content.** There is no
JavaScript material sitting inside node.md waiting to be lifted out: it is Node
guidance throughout, and Cloudflare guidance throughout, for two different
runtimes that execute the same language.

**What that means for the model:** Go and Rust moved to `languages/` because
they are languages whose runtime is implicit — there is no separate platform to
name. Node and Cloudflare stay in `platforms/` because they are runtimes. The
four files were misfiled in one direction only, and that is now corrected.

A `languages/typescript.md` remains *possible* — conventions true of TypeScript
wherever it runs: module style, naming, error idioms, what the type system is
for. But it would be **written**, not extracted, and nothing currently needs it.
Writing one to justify a directory would be worse than leaving the directory with
two files in it.

**A blocker found on the way, which still stands if that blueprint is ever
written.** A platform or language binding's `requires:` are skipped
(`isPlatformBlueprint(r) { continue }` in the CLI), because a binding's
requirements describe every component type rather than the one being built. So a
platform blueprint cannot pull in a language blueprint by declaring it —
`GenerationRoots` would have to return both bindings, and the platform would have
to declare which language it runs.

---

## A prerequisite discovered by attempting step 1

**Moving a file in this corpus does not take effect until the move is pushed.**

Blueprints resolve **a local `blueprints/` directory → `WL_BLUEPRINT_SOURCES` →
the shared cache at `~/.weblisk/blueprints`**, and that cache is a **git clone of
the remote**. Running the CLI from its own repository, there is no local
`blueprints/`, so every resolution goes to the cache — which carries whatever was
last pushed.

Attempted here: `platforms/{go,rust}.md` moved to `languages/`, the CLI updated
to resolve both families. Six tests failed, and the reason was not the code:
`languages/go.md` is not in the graph, because the cache had never heard of it.
This repository is currently **three commits ahead of origin**, so the corpus a
build reads is three commits behind the corpus being edited.

That is the fault already recorded as *blueprints never reached builds*, arriving
from a new direction. It has two consequences for this plan:

1. **Any family move must be pushed before it is real.** Editing and testing
   locally proves nothing about what a build will read.
2. **A move needs a transition**, or it is a flag day. Either both locations
   resolve for a release, or the corpus and every consumer move together in one
   push — which across two repositories they cannot.

**Recommended:** each family move is split in two — first the corpus gains the
new location and the consumers learn to resolve *either*; that is pushed; only
then does the old location go. The step-1 attempt bundled both halves and could
not have worked whichever order it was done in.

**Also learned, and separable from the move:** `PlatformBlueprint`'s
`default: return "platforms/go.md"` means `--platform pyhton` builds a Go tenant
silently. Removing it is a change to the command's surface — it decides what
`--platform Go` and `--platform wasm` do, and there are tests stating the current
behaviour deliberately. It belongs in its own change, not bundled into a move.

## Risks

**Two meanings of `standards` will coexist during steps 2–4.** Unavoidable, and
the reason step 4 waits: renaming into a word still in use by the same repository
is how the `platform` collision happened.

**`--platform` is load-bearing in an actively-changing CLI.** Step 3 is the only
step that changes a command's surface, and it should be taken when that
repository is quiet.

**Programmes have live product behind them.** Step 5 moves specification, not
implementation: Studio keeps its planner and its engine, and reads the maps from
here instead of from its own tree. Anything else is a rewrite wearing a move's
clothes.
