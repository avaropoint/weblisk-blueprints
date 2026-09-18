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

**1 — `languages/`, and `intl/` reserved.** `platforms/{go,rust}.md` move;
`node.md` splits, its JS/TS conventions becoming `languages/typescript.md` and
its runtime parts staying. `cloudflare.md` stops restating them. Corpus only —
no Studio impact, and the CLI keeps working while `--platform` still resolves,
because the *files* move but the flag's meaning is unchanged until step 3.

**2 — `frameworks/`, with `frameworks/weblisk`.** `standards/`'s framework files
move. `standards/code.md` and `standards/project-structure.md` split between
`languages/` and `frameworks/weblisk/`. Touches `schemas/standard.md` and
`validate_corpus.go`, which asserts `standards/` holds nine files.

**3 — `--language` and `--platform` as separate flags.** CLI. `PlatformBlueprint`
is a hard-coded switch whose `default:` silently returns Go, so an unknown
platform is built as Go today; it becomes a declared lookup. `platform` threads
through roughly eight dispatch files. **Coordinate — this repository's consumer
is under active work.**

**4 — `standards/` repurposed to industry standards.** The name frees up only
after step 2. Studio holds 38 framework definitions today; what moves is their
*declaration*, not a customer's adoption of them.

**5 — `programmes/`.** Studio's `packs/` and the substance of
PROGRAM_ARCHITECTURE and PROGRAM_CONSTRUCTION, plus `schemas/programme.md` for
the form. The largest step, and the one with the most product behind it.

**6 — a programme declares what it needs built.** Agents, workflows, tasks and
forms, so `weblisk programme <id> init` can bootstrap an operating programme from
the specification, the standards it conforms to, and the tenant's knowledge. This
is the step that makes the collection worth having; the five before it are moving
furniture so that this one is possible.

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
