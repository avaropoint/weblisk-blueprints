# The Weblisk tools: one engine, two front ends, driven by the corpus

> **Status: adopted by the owner on 2026-11-03, with the decisions recorded in
> [Decisions](#decisions), including the reversals in
> [Text already adopted that this proposal would change](#text-already-adopted-that-this-proposal-would-change).**
> It is the plan of work, not yet normative. It stays
> at the corpus root as a plan, because a file under `architecture/` is a
> blueprint and its MUST lines are read as requirements. Each part becomes
> normative only when it lands in the document
> [What changes where](#what-changes-where) names for it, and from then on that
> document, not this plan, is the authority.
>
> Written 2026-11-03 against corpus `42ccc8d`, from the owner's decisions of
> that date, [`ACCEPTANCE_PLAN.md`](ACCEPTANCE_PLAN.md) (adopted the same day),
> and three drift audits of the CLI, of Studio and of the development tenant's
> last rebuild.

---

## The problem, measured

| | Measured |
|---|---|
| 1 | About 22% of the CLI's 84k lines restate the corpus and 10% hold knowledge the corpus lacks: component kinds, file layout per platform, service order and ports, accept routes, toolchains, compiler-diagnostic grammars, the env allow-list |
| 2 | The CLI writes 2,237 lines of its own Go source (the model gateway) into every Go tenant |
| 3 | A model decides whether every checklist item is met. On the last orchestrator build, at least 281 of 284 "satisfied" had no mechanical confirmation, and 41% of assertions were "unverifiable" |
| 4 | The 31 `declaration.checks` in `architecture/orchestrator.md` are parsed and never run. No `wl:check` id is executed. Published vectors are never delivered to a build |
| 5 | Generation writes no tests. The tenant's 12 test files were written by hand, and 10 of them test code that regeneration has since replaced |
| 6 | Two hand-written conformance suites exist (`dispatch/conformance.go`, `internal/test`), and their ids contradict each other and `architecture/testing.md` |
| 7 | The model chooses the plan, because `architecture/generation.md` tells it to. The same ten blueprints, byte for byte, gave plans of 49 and 51 files, with 55 symbols moved. 30 of 159 repairs chased placement rules no per-file edit can meet |
| 8 | About 26k of Studio's Go lines run tenant services (a programme-service copy, a prompt worker) and 22k keep tenant records. 16 model prompts are Studio literals, and none loads a corpus skill |
| 9 | Five places in Studio and three CLI prompt wordings already contradict the corpus and give wrong answers today |

One sentence covers all of it. **Behaviour that belongs to the corpus is held
in two tools, in two languages, and each copy drifts on its own.**

---

## The decisions this rests on

Made by the owner on 2026-11-03, and binding on everything below.

1. **The corpus drives all behaviour**, the build process included. A behaviour
   the corpus does not describe is one no tool may have.
2. **One engine executes the corpus.** It is a shared Go module with one
   operations API. Every operation is a command that returns a stream of
   events. The engine holds no corpus knowledge and reads all of it. The model
   is a tool the engine calls, and the corpus supplies every instruction the
   model is given.
3. **Two interchangeable front ends.** The CLI presents in a terminal and Studio
   presents in a browser. Both have the same capabilities, and a conformance
   test proves that every operation is reachable from both.
4. **Criteria become tests.** Each test is written from its criterion alone,
   before code generation and in a separate step. It carries the criterion's id
   and the digest of the criterion's text. Its verdict comes from running it,
   and it is regenerated only when that text changes.
5. **One conformance suite**, derived from the corpus. It replaces both
   hand-written suites and every verdict a model gives.
6. **Acceptance follows [`ACCEPTANCE_PLAN.md`](ACCEPTANCE_PLAN.md).**
7. **Builds are incremental, from a record of what was done.** A change touches
   only what moved, and a build never starts from scratch.

---

## 1. The parts, and the line between them

| Part | Why it exists | Holds | Never holds |
|---|---|---|---|
| **Corpus** | It is the one description of what anything is, how it is built and how it is checked | Specifications, schemas, criteria, declared checks and vectors, the build steps as data, every instruction a model is given, published content | Executable logic. Tenant facts |
| **Engine** | So that the corpus is executed once, by one implementation | Interpreters for the closed vocabularies the corpus declares: the family grammar, block types, check kinds, step kinds and executors. It also holds mechanics: processes, caches, digests, signing, transport, streaming | A family, kind, component, language, route, code, threshold, list or sentence of the corpus |
| **CLI** | So that a person or a script can drive the engine from a terminal | Presentation: panes, prompts and `--json`. It also holds its host's notes: where a tenant listens, and which identity to use | An operation the engine lacks. Any decision |
| **Studio** | So that a person can drive the engine from a browser, across every tenant they can reach | Presentation: the areas, the editor surface and the renderers. It also holds its host's notes, as Studio's CLAUDE.md allows a client to keep | An operation the engine lacks. A tenant's answer. A verdict it computed itself |
| **Model** | So that text the corpus cannot fix in advance can be written: code, tests and repairs | Nothing. It is called, given corpus instructions and named inputs, and its output is recorded | A verdict. A plan the corpus fixes. A name the corpus declares. Its own instructions |
| **Tenant** | So that the customer's system, and the system of record for everything about it, belongs to the customer | Its code, its tests, its record of every build, its changes, content, identities, grants and model. It also hosts the engine as its change service | Anything only a client holds |

Four rules follow.

- **Meaning in the corpus, mechanics in the engine, presentation in the front
  ends.** A line of front-end code that decides something is a missing engine
  operation. A line of engine code that names something is a missing corpus
  declaration.
- **The engine knows how to read and how to run, and nothing about what it
  reads.** What it implements is stated as closed vocabularies that the corpus
  declares and versions, the way capabilities are closed in code and kinds are
  open data ([`schemas/kinds`](schemas/kinds.md)). The engine says which
  version of each vocabulary it implements, and it refuses a corpus that needs
  a later one.
- **The engine runs in three hosts and is the same in each**: the CLI, Studio,
  and the tenant, as its change service. Where an operation's act happens is
  its executor: `local`, `tenant-api` or `cli-in-tenant`
  ([`schemas/change`](schemas/change.md#executors), D24). Studio, or any
  client, reaches a `cli-in-tenant` operation only through `tenant-api`, by
  asking the engine inside the tenant to run it.
- **The model belongs to whoever owns the act.** An operation acting on a
  tenant uses the tenant's model, through the tenant. Only a `local` operation
  outside any tenant uses the host's model. Studio has no model of its own.

---

## 2. The engine's operations

### The shape of an operation

- An operation is `<noun> <verb>`, in the grammar of
  [`architecture/cli`](architecture/cli.md#command-grammar). Family nouns and
  resource kinds are read from the corpus and from the tenant. Operational
  nouns and verbs are a closed set in the engine.
- The engine publishes its catalogue as one manifest (`weblisk commands
  --json`, already specified). For each operation it gives the parameters, the
  capability, the executor and the event types. Both front ends render from the
  manifest and hold no list of their own.
- **Every operation returns one stream of events.** Each event has the same
  envelope: operation, invocation id, sequence, instant, type and body. Six
  types are common to every operation:

| Event | Carries |
|---|---|
| `started` | the inputs as resolved, and the corpus pins read |
| `step` | which declared step began or ended, with its id from the corpus |
| `progress` | a count against a known total, or silence observed |
| `question` | something only a person can give: a passphrase, a vault approval, a step-up, a signature, a confirmation. The stream waits for an answer |
| `warning` | something the run continued past, with its reason |
| `finished` | the result, with exit status, and what was recorded |

  Operations add their own: `item` (one row of a read), `artifact` (a file
  written, with its digest), `model` (one model call, with the instruction ref,
  input digest, output digest and the model the backend reported), `check` (one
  test or check run: criterion id, result, reason), `gap` (a class, a reach and
  an exposure statement), `verdict`, and `event` (a tenant event relayed).
- **A `question` is how the two front ends stay interchangeable.** The CLI
  answers one in a pane, and Studio in a dialog. Neither one has a flow the
  other lacks.
- `--json` on the CLI, and the stream route on Studio, carry the same events,
  byte for byte.

### The operations

The list is derived from `weblisk --help` and every subcommand's help, from
[`architecture/cli`](architecture/cli.md#the-command-surface)'s Command Surface
under its [renamed](architecture/cli.md#renamed-commands) spellings, from what
Studio does today (Studio's TENANT_CHANGE_CYCLE.md §2),
and from what the owner needs. The common events are not repeated in the
tables.

**Corpus**: every operation here is `local`. Each reads a source the person
holds, and none touches a tenant.

| Operation | Inputs | Events | Records | Driven by |
|---|---|---|---|---|
| `corpus sources` · `corpus update` | — | `item` per source: origin, revision, held or not | the source cache, which is a cache | [`architecture/cli`](architecture/cli.md#where-blueprints-come-from) |
| `<family> validate` · `walk` · `show` · `list` | a ref, file or repository | `item` (a projection or entry), `check` per rule | nothing | [`schemas/family`](schemas/family.md), [`schemas/blocks`](schemas/blocks.md), each family's declaration |
| `<family> deps` · `diff` | refs, or ref@a ref@b | `item` per closure entry or changed part, marked when only prose changed | nothing | [`architecture/generation`](architecture/generation.md#resolving-a-request-of-many-roots), [`schemas/common`](schemas/common.md) |
| `<family> new` · `rename` · `retire` · `release` | a ref, a template, a reason | `artifact` | the file and its own history | [`schemas/authoring`](schemas/authoring.md), the family's template, [`RETIRED.md`](RETIRED.md), [`schemas/common`](schemas/common.md#blueprint-versions) |
| `schema export` | a family or block type | `item` (JSON Schema) | nothing | [`schemas/family`](schemas/family.md) |
| `platform list` · `show` | — | `item` per language or platform, with toolchain and layout | nothing | `languages/`, `platforms/`, [`schemas/language`](schemas/language.md), [`schemas/platform`](schemas/platform.md) |

**Tenant lifecycle**

| Operation | Executor | Inputs | Events | Records | Driven by |
|---|---|---|---|---|---|
| `tenant new` | `local`, on the host that will hold it (decision 7) | name, language or platform, the first identity, the model backend | `step` per declared create step, then all of `change apply`'s events | the first change and its run statements, config, the tenant's keys | create steps declared in [`architecture/cli`](architecture/cli.md#weblisk-tenant-create-name), [`schemas/config`](schemas/config.md), [`schemas/programme`](schemas/programme.md#the-services-in-the-order-they-are-built) |
| `tenant connect` | `tenant-api` | address, identity | `question` (vault or passphrase), `item` (probes: reachable, admitted) | the host's note of address and operator name; the token in memory only | [`architecture/cli`](architecture/cli.md#weblisk-operator-connect), [`architecture/admin`](architecture/admin.md) |
| `tenant status` | `tenant-api`; process state is `cli-in-tenant` | — | `item` per component: recorded, running or stale; probes; standing | nothing | [`protocol/spec`](protocol/spec.md) probes, [`architecture/admin`](architecture/admin.md) |
| `tenant verify` (was `tenant accept`) | `tenant-api` | component or all | `check`, `gap`, `verdict` | runtime verdicts in the record | the conformance suite's live subset ([§5](#5-the-one-conformance-suite)) |
| `tenant export` · `tenant rebuild` | `cli-in-tenant` | an output path, or a bundle and keys | `step`, `artifact`, `check` | a bundle, or a rebuild run in the record | [`architecture/tenancy`](architecture/tenancy.md), [`architecture/cli`](architecture/cli.md#tenant-export-and-rebuild-codes) |
| `component start` · `stop` · `logs` | `cli-in-tenant` | component | `step`, `item` (log line), `check` (does the acceptance cover this environment?) | process state, which is a note | [`architecture/cli`](architecture/cli.md#weblisk-server-start), [`schemas/config`](schemas/config.md), the services table, `ACCEPTANCE_PLAN` runtime acceptance |

**Builds and changes**: these are `tenant-api` once the tenant runs its
change service, and `cli-in-tenant` until then, exactly as
[`architecture/cli`](architecture/cli.md#until-a-tenant-runs-a-change-service)
already says.

| Operation | Inputs | Events | Records | Driven by |
|---|---|---|---|---|
| `change plan` (`--adopt` · `--upgrade` · `--remove`) | refs, strict, driver edits, named replacements | `step` (resolve), `item` per plan entry with verdict and reason, `gap` (unassessed), `warning` (conflict) | the change, at `.weblisk/changes/<id>.json` | [`architecture/generation`](architecture/generation.md#resolving-a-request-of-many-roots), [`schemas/change`](schemas/change.md), [`architecture/change-management`](architecture/change-management.md), [`schemas/programme`](schemas/programme.md#adoption-emits-a-build-plan) |
| `change list` · `show` | filters, id | `item` | nothing | [`schemas/change`](schemas/change.md) |
| `change approve` · `reject` (forms of `approval accept` · `reject`) | id, the person's signature | `question` (step-up, signature) | `approval` or `rejection` on the change | [`architecture/cli`](architecture/cli.md#who-may-approve-a-change), [`protocol/types`](protocol/types.md#approvalrequest) |
| `change apply` | change id | `step` for each of resolve, plan, translate, generate, build, test, repair and accept ([§3](#3-what-executing-the-corpus-means)); `model`, `artifact`, `check`, `gap`, `verdict` | run statements with their actions and criteria ([§6](#6-the-record)); outcomes on the change | everything in [§3](#3-what-executing-the-corpus-means) |
| `change verify` | change id | `check`, `verdict` | a verify run; `verify` on the change | the conformance suite |
| `change revert` | change id | as `change plan` | a new change of kind `revert` | [`schemas/change`](schemas/change.md) |
| `build` (a scratch build, outside any tenant) | refs, an output directory | as `change apply` | run statements in the output directory | as `change apply`; `local` |
| `run status` (was `build status`) | component or all | `item`: standing (established, accepted with gaps by class, refuted, unassessed) | nothing | [`schemas/run-statement`](schemas/run-statement.md), `ACCEPTANCE_PLAN` |
| `acceptance propose` · `decide` | change, environment | `item` per gap with reach and exposure statement, `question` (the signed decision) | the change's `acceptance` block | `ACCEPTANCE_PLAN`, then [`schemas/change`](schemas/change.md) and [`schemas/config`](schemas/config.md) |
| `test run` | component, criterion or check ids; `--sealed` or `--live` | `check`, `gap`, `verdict` | verdicts in the record | [§5](#5-the-one-conformance-suite) |
| `record show` | a criterion, file, run or action | `item`: criterion, tests, reach, verdict history, actions | nothing | [§6](#6-the-record) |
| `impact` | ref@a..@b | `item` per node reached | nothing | [`architecture/fabric`](architecture/fabric.md), [`architecture/change-management`](architecture/change-management.md) |
| `cache status` · `prune` | an age | `item` | the cache | [`architecture/generation`](architecture/generation.md) |

**Integrations and platforms**

| Operation | Executor | Inputs | Events | Records | Driven by |
|---|---|---|---|---|---|
| `provider list` (was `providers`) | `local` for the host; `tenant-api` for a tenant | — | `item` per backend, with the models the backend reports live | nothing | [`architecture/orchestrator`](architecture/orchestrator.md) (the tenant's model), [`architecture/model-service`](architecture/model-service.md) |
| `model choose` | `tenant-api` | backend, model | `check` (the backend answers) | the tenant's model setting, in the tenant | [`architecture/orchestrator`](architecture/orchestrator.md) |
| `integration list` · `add` · `check` · `remove` | `tenant-api` | provider kind, fields, a secret through `question` | `item`, `check`, `question` (secret, step-up) | the tenant's integration records | `INTEGRATION_PLAN.md` (proposed on a parallel lane, not yet on main), then `architecture/integration.md` |
| `content backend list` · `add` · `check` | `tenant-api` | backend, driver, root | `item`, `check` | the tenant's configuration, through a change | [`architecture/content`](architecture/content.md#configuration), the same proposal's part B |

**Operations**: every operation here is `tenant-api`.

| Operation | Inputs | Events | Records | Driven by |
|---|---|---|---|---|
| `resource list` · `show` | kind | `item`, including `declared-unavailable` with its reason | nothing | [`architecture/admin`](architecture/admin.md#resources-one-api-for-every-kind), [`schemas/resource`](schemas/resource.md) |
| `<kind> list` · `show` · `create` · `update` · `delete` · `<verb>` · `watch` (agents, domains, workflows, objectives, federations and operators are kinds) | uid, `--set`, `If-Match`, filters | `item`, `question` (step-up, confirm), `event` | the tenant's own record of the act | the same, and each kind's Resources block |
| `approval list` · `show` · `accept` · `reject` | id, reason | `item`, `question` | the decision, at its owner | [`protocol/types`](protocol/types.md#approvalrequest), [`architecture/admin`](architecture/admin.md) |
| `audit` | filters, follow | `item`, `event` | nothing | [`architecture/admin`](architecture/admin.md), `AuditEntry` |
| `identity init` · `store` · `path` · `register` · `token` · `attest` · `rotate` | name, holder, hub | `question` (passphrase, vault) | the host's own identity, which is the installation's | [`architecture/cli`](architecture/cli.md#identity-commands), [`protocol/identity`](protocol/identity.md) |
| `secret list` · `set` · `get` · `delete` · `rotate` (`local`) | agent, key | `question` (value, confirm) | the secret source | [`patterns/secrets`](patterns/secrets.md) |

**Content**: every operation here is `tenant-api`. Studio's editor is how
Studio presents these operations, and the CLI presents the same operations.

| Operation | Inputs | Events | Records | Driven by |
|---|---|---|---|---|
| `content list` · `read` · `history` | scope, path or uid | `item` | nothing | [`architecture/content`](architecture/content.md) |
| `content write` · `move` · `remove` | bytes, `If-Match`, a message | `check` (structure against its family), `artifact` | the tenant's content commit and change statement | [`architecture/content`](architecture/content.md), [`patterns/content-git`](patterns/content-git.md), [`documents/families`](documents/families/README.md) |
| `content reconcile` | remote | `item`, `gap` (diverged) | content's records | [`architecture/content`](architecture/content.md) |
| `document check` (also `local`) | file | `check` per slot, `gap` | nothing | [`documents/families`](documents/families/README.md), [`schemas/family`](schemas/family.md) |
| `standard adopt` | standard@edition, a control catalogue | `artifact` | the tenant's standard file, linking the published one | [`schemas/standard`](schemas/standard.md) |
| `programme adopt` | programme ref | as `change plan --adopt`, plus the adoption record | the change; `adoption.md` | [`schemas/programme`](schemas/programme.md) |
| `fabric trace` | a node | `item` per edge, with staleness | nothing | [`architecture/fabric`](architecture/fabric.md) |
| `attest` (a person's statement over a document) | document digest, statement | `question` (signature) | the tenant's attestation record | [`architecture/content`](architecture/content.md); the statement vocabulary has no corpus home yet |

**Folded or deleted**

| Today | Becomes |
|---|---|
| `server init`, `component <kind> init`, `agent create`, `domain create`, `gateway create` | `change plan --adopt`, then `change apply` |
| `server verify`, `agent verify`, `test conformance` | `test run` |
| `server start` · `stop` · `logs` · `status`, `agent start`, `domain start`, `gateway start` | `component start` · `stop` · `logs`, and `tenant status` |
| `test mock-orchestrator` | Deleted from the tools. The mock that [`architecture/testing`](architecture/testing.md#mock-orchestrator) specifies is built from that specification, like any other component |
| `pattern apply` | Deleted: it is a legacy pipeline with no plan, no ownership check, no build and no conformance |
| `deploy rollback` | `change revert` |
| `app new` · `dev` · `build` · `vendor`, `update`, `marketplace *`, `deps audit`, `gateway policy *`, `doctor` | Not yet driven by the corpus (decision 8) |

---

## 3. What executing the corpus means

`change apply`, and a scratch `build`, run eight steps in a fixed order. The
order is itself corpus data in [`architecture/generation`](architecture/generation.md).
A step is **determined** when everything it decides is read from the corpus. It
is **guessed** when something is left to the engine or the model. Every row's
last column is a guess that has to be closed.

| # | Step | What it does | What the corpus must declare | Gaps today, from the audits |
|---|---|---|---|---|
| 1 | **Resolve** | Takes the build set and the context set, versions, pins and conflicts C1 to C8. No model call | The two closures and the conflicts (exist); how many of each kind a tenant may run, and `runs_with`; which protocol section binds which kind; component order (the services table exists); the default target, and the list of languages and platforms | Kind cardinality is in CLI Go (`singletonKinds`, four constructors). The section-to-kind binding is a Go switch. Service order and ports have a second copy in the CLI. An unknown platform falls back to Go |
| 2 | **Plan** | Fixes the files, packages, names and order, wherever the corpus can fix them | A machine-readable `layout` per language and platform: packages, the file-per-section rule, the entry point. Boundary names (exist for endpoints, types and operations). Module-path derivation. Manifest and export extraction per language. Duplicate rules that cross packages. Ownership of shared packages | `generation.md` says the plan is the model's. go.md's package table is prose and nothing enforces it, so all 48 library files landed in one package and 3 types were defined in 3 packages. Export extraction exists only for Go and JS |
| 3 | **Translate** | Writes one executable test per criterion, from the criterion and the declared contract alone, before any code exists | Durable criterion ids and digests. The check kinds and their data. The test path and header form per language. The test command per language. The fixtures. The translation instruction | 2,643 of 2,835 checklist items have no id. Check kinds for a tenant (`exchange`, `vector`, `join`, `record`, `topology`, `structure`) are in `ACCEPTANCE_PLAN` only. Vectors are never delivered. There is no instruction home |
| 4 | **Generate** | Writes each planned file | The prompt contract (exists), the instruction text, and the rules the model must not settle: missing names, ties, scope | The CLI tells the model to invent missing names, settle ties in a comment, and ignore the scope prohibition, all against `generation.md`. The model-gateway source is CLI-embedded Go |
| 5 | **Build and test** | Builds the tree, starts it sealed and runs the suite ([§5](#5-the-one-conformance-suite)) | The build, run and test commands per language; the diagnostic grammar, load-failure and dependency-fault markers per language; the sealed environment (the env allow-list exists); ports; which routes are essential | The diagnostic grammars are Go in Go (so Rust and Node cannot be repaired). The load-failure words are in `generation.md`, not `languages/go.md`. Essential routes are a CLI list. The Go toolchain check looks up a moved file and never runs |
| 6 | **Repair** | Edits files until the suite passes, class by class | The instruction per repair kind; the governing section given with each failure; which files a diagnostic implicates, per language; the class order (`ACCEPTANCE_PLAN`); the round ceilings as configuration | Repair prompts are Go literals with rules found nowhere in the corpus. A repair sees the model's evidence and not the blueprint section. The ceilings are CLI constants |
| 7 | **Accept** | Applies the build gate; proposes runtime acceptance | Classes and their derivation; environments; withholding (`ACCEPTANCE_PLAN`) | The threat model's controls are prose. There is no registration slot. The environment and the development flag have no home. Withholding does not exist |
| 8 | **Record**, then **change incrementally** | Writes what every step did; the next change starts from it | The record's shape ([§6](#6-the-record)); the rebuild table (exists); a diff by part id; impact by binding (exists in change-management) | No actions or criteria are recorded. Nothing writes the build lock. There is no structured diff, so every blueprint edit rebuilds a whole component |

### Where the corpus says WHAT and not HOW

These are the measured places where the model had to decide something because
the corpus did not. Each one needs corpus text before a build can be
determined.

| Gap | Kind | Where |
|---|---|---|
| `jti` records "shared by every instance": no mechanism given | HOW missing (now `IF` under R1) | [`architecture/admin`](architecture/admin.md) |
| `operates_in` checked against ISO 3166, with no code list shipped | data missing | [`architecture/orchestrator`](architecture/orchestrator.md) |
| `omitempty` forbidden by go.md, while "optional fields MAY be omitted" by types.md | contradiction | [`languages/go`](languages/go.md), [`protocol/types`](protocol/types.md) |
| The go.mod example against the Primitive Mapping | contradiction | [`languages/go`](languages/go.md) |
| "No other algorithm" against es256 and eddsa passkeys | contradiction | [`protocol/identity`](protocol/identity.md), [`architecture/admin`](architecture/admin.md) |
| Who may publish `scope.violation` | contradiction | [`patterns/scope`](patterns/scope.md), [`protocol/spec`](protocol/spec.md) |
| The structure of generated code: packages, files, the file-per-section rule | HOW left to the model on purpose | [`architecture/generation`](architecture/generation.md#the-plan), `languages/*` |
| Posture thresholds, evidence strength, attestation statements, review fields, enforcement rules, position derivation, the `wl:table` format | no corpus home; Studio holds them | the Studio audit's H2, H16, M1 to M3, M12, M16, M19 |

---

## 4. What the model may and may not do

| Step | The model may | The model may not | Its instructions live in |
|---|---|---|---|
| Resolve | nothing | — | — |
| Plan | name private helpers inside one file, where the layout leaves room. Until the layout is declared, propose files inside the declared packages, with the proposal recorded as the model's and reused | choose a package, a boundary name or an entry point; place a declared symbol | `instructions/plan.md` |
| Translate | write a test from one criterion, the declared contract (types, operations, codes, fixtures) and the plan's names; report a criterion as untestable | see any implementation; weaken a criterion; decide a verdict | `instructions/translate.md`, plus each language's test section |
| Generate | write a planned file | edit a test; invent a name the corpus does not declare (it reports the gap); settle a tie or a contradiction (it reports it); add scope | `instructions/generate.md`, plus each language's generation section |
| Build and test | nothing | — | — |
| Repair | edit files in the repair set, given the failing test's output and the governing section | edit a test, a plan-fixed name, or a file outside the set | `instructions/repair/<kind>.md` |
| Accept | nothing. Its reading of the tree may be printed as advice | move any verdict, in either direction | `instructions/advise.md` |
| Record | nothing | — | — |

A model that finds two corpus texts in conflict **proposes** the conflict. A
conflict is recorded as a corpus finding and is settled by a corpus change that
a person makes. It is never accepted on the model's word, which today is what
`corpus_conflict` does.

`instructions/` would be a new corpus family. Each file is one step's
instruction, with named slots the engine fills from declared inputs. The engine
adds no sentence of its own. The model is told which instruction revision it
is following, and the record holds that revision's digest. This replaces the
CLI's prompt literals and the 16 Studio prompts. A tenant's agent work is a
different thing: it stays in programmes' `skills:` and the prompt worker, and
Studio's drafter, reconcile and assistant prompts move there.

---

## 5. The one conformance suite

### The unit is a criterion

A **criterion** is one checklist item, or one requirement (`wl:id`) that no
checklist item covers. Each has a durable id and a digest of its text.

**`wl:check` is absorbed, not replaced.** A `wl:check <id> covers <ids>`
comment is today's spelling of a `verifies` entry
([`schemas/blocks`](schemas/blocks.md#definitions)): id, `covers`, `check` and
`assertion`. Every checklist item becomes one:

- The 192 items that carry a `wl:check` keep their ids.
- The other 2,643 get an id minted once, from their text at the time of
  minting. The id is then frozen and never derived again (decision 9).
- `check:` names how the criterion is settled. It is either a declared kind
  (`exchange`, `vector`, `join`, `record`, `topology` or `structure`, from
  `ACCEPTANCE_PLAN`), whose data is written in the corpus, or `translated`,
  which is the default.
- `requirement-ids.py` grows to hold that every checklist item in a file marked
  complete has an id.

### How the suite is derived

| Layer | Written by | Lives | Runs |
|---|---|---|---|
| **Declared checks**: `verifies` entries of a declared kind, and L1 to L4 rewritten as `join` and `exchange` data | corpus authors, with a model's help in a corpus change a person reviews | in the corpus, beside the requirement; large fixtures in `vectors/<blueprint>/` | by the engine's interpreter for that kind, which is language-neutral |
| **Translated tests**: one per `translated` criterion | the translate step, from the criterion alone | in the tenant, with its code, at the path the language declares, each with a header carrying the criterion id, the text digest and the translating action | by the language's declared test command |
| **Published vectors** | the corpus | delivered to `testdata/weblisk-vectors/` (already required, never done) | through the tests that name them |

A translated test that a corpus author later writes as declared data is
**promoted**: it moves into the corpus and is owed by every tenant, and the
tenant's copy is retired.

### What makes a translated test count

A test counts only if all four of these hold:

1. **It was written apart from the code.** The translate step runs before
   generation, and it is given no implementation. The record proves both by the
   order and the inputs of its actions.
2. **It fails on nothing.** Before any code is generated, it is run against a
   stub built from the plan's declarations alone, and it has to fail. A test
   that passes against nothing tests nothing. This is the control that every
   check in `checks/` already carries.
3. **It is frozen.** Generation and repair cannot write a test path. A test
   that changed outside translation is refused, as an edited file is refused
   today.
4. **Its verdict is the run's.** Pass, fail or error comes from the test
   command's exit and output, in the grammar the language declares.

This amends one row of `ACCEPTANCE_PLAN` "What counts". "A test the generator
wrote, even named by a check id" still does not count. A test translated under
these four conditions does (decision 3).

### Build time and run time

- **At build time**, the whole suite runs in the sealed environment that
  `ACCEPTANCE_PLAN` defines. Its results are the build gate.
- **At run time**, each check declares whether it may run against a live
  tenant (`live: safe` or `live: sealed-only`). `tenant verify` and `test run
  --live` run the safe ones against the running tenant, on demand or on the
  cadence the tenant configures. Today's `tenant accept` route list becomes the
  first of these.
- **Results feed acceptance.** The build gate counts the sealed results by
  class. A runtime acceptance cites the latest live results. When a live S or J
  check fails after acceptance, the acceptance is marked *contradicted*, and
  that is shown everywhere the acceptance is shown (decision 6).

### What it replaces

`dispatch/conformance.go`, `conformance_register.go` and `interop.go`;
`internal/test` (`weblisk test`); `selfverify.go` as a verdict; `corpus_conflict`
as a verdict; `verify.go`'s phrase-bound structural checks; `checklist.go`'s
`mechanicalChecks`; `methodless.go`; the essential-route list in
`pkg/tenant/route`; and, in tests only, `operator/fakehub`. Each is deleted only
after its replacement runs ([§8](#8-migration)).

---

## 6. The record

### Its home

The record lives in the tenant, in its repository, and is written by the
tenant's change service. Until a tenant runs a change service, the CLI on the
tenant's host writes it in the same shape. It is an answer about the customer's
system, so under Studio's CLAUDE.md's rule no client
holds it. Front ends read it through `/v1/admin/build` and its sub-routes.

It is not a second ledger. It extends the run statement
(`provenance/runs/<run id>.json`, one immutable file per run), which is
already the fabric's outbox. Any index over it is a cache, rebuilt from the
statements.

### Its shape

The run statement gains two lists. What is in it today stays.

| | Holds |
|---|---|
| **actions** | One per thing a step did: id, step, the declared instruction ref and its digest (for a model action), the input digests, the output digests, the model the backend reported, the result, and when |
| **criteria** | One per criterion the run owed: id, text digest, class and the rule that gave it; its tests (path, digest, the action that translated it, and whether it is promoted); its reach (files, symbols, operations); its verdict in this run, with environment and reason; and its gap, if it has one, as `ACCEPTANCE_PLAN` gives the fields |

The per-file rebuild record that run statements already hold is unchanged.

### How it makes builds incremental

1. **An action is reused when its inputs are.** Before the engine runs any
   action, deterministic or model, it looks for a completed action with the
   same step, instruction digest and input digests. If one exists, the engine
   reuses its outputs. A model is never asked the same question twice. That
   also removes most of the plan variance measured above, because a plan made
   from the same inputs is the same plan.
2. **A test is regenerated only when its criterion's digest moves.** A change
   to the instruction or the language only marks the test "translated under an
   older instruction", and re-translating it is a change someone makes on
   purpose.
3. **A file is rebuilt only when the rebuild table says so**, now read through
   the criteria it is answerable for.
4. **A verdict is carried forward** while its test's digest and the digest of
   everything the test reaches are unchanged. A black-box test reaches the
   whole component, so it runs again whenever the component is rebuilt. Tests
   are cheap, and the record says which verdicts were carried and from which
   run.
5. **A build never starts from scratch.** The first build starts from an empty
   record. Every later one starts from the record of the one before.
   `tenant rebuild` starts from the exported record.

---

## 7. The tools' own conformance

The tools are specified in the corpus, so the corpus checks them, with
controls, as `checks/` already checks the corpus.

### The engine holds no corpus knowledge

| Proof | How | Control |
|---|---|---|
| **A fake corpus** | `vectors/engine/` holds a miniature corpus with invented families, kinds, components, check kinds and a fake language (extending [`vectors/mapping/fake-language.md`](vectors/mapping/fake-language.md)). Its build, run and test commands are scripts that the fake language declares. The engine builds it, and the record has to equal the expected record | An engine with one corpus name compiled in fails on the renamed one |
| **A renamed corpus** | The real corpus, with every declared name renamed consistently, gives the same plan, tests and record, modulo the renaming | Renaming one family in the corpus and not in a copy of the expected record is reported |
| **No literals** | `checks/engine-neutrality.py` reads the engine source at a pinned commit, and lists every literal equal to a name the corpus declares (family, kind, heading, route, code, language, instruction sentence). The list is held to a `known` file that can only shrink, as `checklist-cites.json` is | Adding one corpus name to a copy of the source is reported |
| **Closed vocabularies only** | The engine's manifest lists the vocabularies it implements and their versions. Each has to be one the corpus declares | A manifest naming an undeclared check kind is reported |

### The CLI and Studio are interchangeable

| Proof | How | Control |
|---|---|---|
| **One catalogue** | Each front end exposes the engine's manifest unchanged: `weblisk commands --json`, and Studio's operations route. `checks/front-end-parity.py` (replacing `command-surface.py`) compares both with the engine's manifest at pinned commits | A front end missing one operation, or having one of its own, is reported |
| **The same streams** | A parity test drives every operation in the catalogue through the CLI (`--json`, under a pseudo-terminal) and through Studio's HTTP stream route, against the fake corpus and a sealed fixture tenant, with the same scripted answers to each `question`. The two event streams have to be equal after the invocation ids and instants are normalised | An operation whose `question` one front end cannot answer is reported |
| **No decisions in a front end** | Neither front end may compute a verdict, threshold or list. The same neutrality check runs over both front ends' sources | Adding a posture threshold to a copy of the Studio source is reported |

This replaces MISSION.md's line that what Studio does about standards, adoption
and evidence "needs no command-line equivalent". Under decision 3, everything
has an equivalent.

---

## 8. Migration

### The CLI's packages

From the CLI audit's keep, thin and rewrite table.

| Disposition | Packages |
|---|---|
| **Become the engine** (moved as they are) | `internal/grammar`; `internal/operator` (identity, keychain, vault, mint, rotation); the provider and local-CLI streaming; caches, locks, upstream, pins; process, overlay and typecheck plumbing; snapshot and transaction mechanics from `repair_txn`; fault, transient and exit classification; reconcile digests; `rebuild.go`, cited by row id; change, upgrade, derive and adopt mechanics; `pkg/tenant` lifecycle mechanics; `internal/admin` and `admingw` clients; `startenv` mechanics; `buildplan/services.go` |
| **Thinned into the engine** (Go copy deleted, corpus table read) | `plan.go`, `generate.go`, `requirements.go`, `requires.go`, `declarednames.go`, `fieldbindings.go`, `shared.go`, `skills.go`, `buildtools.go`, `locate.go`; `server/hubconfig`, `tenantstart`, `lifecycle`, `commands`; `pkg/tenant` preflight, gitignore and create steps; `pkg/tenant/route`; `buildplan/needs.go`; `internal/protocol` (generated from `types` blocks); `doctor`; `safepath` |
| **Rewritten in the engine as interpreters** | the check executor (one interpreter per declared check kind, replacing `verify.go`'s structural checks, `checklist.go` and `methodless.go`); the suite runner (replacing `conformance*.go`, `interop.go` and `internal/test`); layout and kind handling (replacing `layout.go` and `component.go`); per-language diagnostics read from `languages/*` (replacing the grammars in `repair_txn`, `repair_group`, `repair_clash`, `repair_refs`, `depfault` and `typecheck`); the translate step (new); the record writer (new) |
| **Moved to the corpus, then deleted** | `modelgw_src/model_gateway.go.txt` and its provider catalogue (to a corpus resource that `architecture/orchestrator.md` declares); `validate_corpus`, `validate_programmes`, `validate_standards` and `validate_yaml_blocks` (to `checks/*.py`); every prompt literal (to `instructions/`) |
| **Deleted** | `selfverify.go` and `corpus_conflict.go` as verdicts (their mechanics survive only as advice and proposed conflicts); `PatternApply`; `relevance.go`; the fallback start commands in `locate.go` and `server/commands.go`; `validate.go`'s "protocol markers"; `operator/fakehub` once vectors cover it |
| **The CLI front end** (what is left) | command parsing from the manifest, the terminal panes, `question` prompts, `--json`, and the host's notes |

### What Studio stops doing locally

From the Studio audit.

| Stops | Replaced by | Gated on |
|---|---|---|
| Running `weblisk` as a subprocess | importing the engine | engine phase E1 |
| Computing verdicts: posture thresholds, compliance levels, the impact analyzer, the standards author, evidence strength | engine operations over corpus declarations; the impact analyzer and standards author are deleted | the corpus homes ([§3](#where-the-corpus-says-what-and-not-how)) |
| Its 16 prompt literals | `instructions/` (engine steps), or programme `skills:` (tenant agent work) | the instruction family |
| The programme-service copy (17k lines) and the agent runner (10.9k) | the tenant's programme service and prompt worker, through `tenant-api` | those tenant routes |
| The tenant-record stores (22k): change ledger, attestations, evidence, audit, retention, access, comments, chat | the tenant's routes | each route, which is G11 in Studio's TENANT_CONNECTION_PLAN |
| Spec documents it owns (`FORMS_ARCHITECTURE`, attestation law) and docs that restate the corpus | corpus schemas; the Studio docs are cut to pointers | — |

Until a route exists, Studio labels the area *not served by this tenant*. It
never falls back to a local store, because rebuilding an area on top of a local
fallback recreates the drift in new code.

### Order: nothing is removed before its replacement runs

| Phase | Builds | Then removes | Done when |
|---|---|---|---|
| **C0, corpus** | `architecture/engine.md`; `instructions/` and its schema; ids minted for every criterion; the check kinds in `schemas/blocks`; L1 to L4 as data; the `layout`, toolchain, diagnostics and test sections per language; kind cardinality; the WHAT-versus-HOW fixes; the record fields | — | `checks/run.sh` holds them, with controls |
| **E1, the engine extracted** | the engine module from the "become" row; the CLI imports it; the manifest | nothing; behaviour is unchanged | the CLI's own tests pass on the engine |
| **E2, the suite in shadow** | the check interpreters, the translate step, the suite runner and the record. They run beside today's judging, and both verdicts are recorded | nothing | one rebuild of the development tenant shows declared, translated and model verdicts side by side |
| **E3, the switch** | verdicts from the suite only | `selfverify` and `corpus_conflict` as verdicts, the phrase checks, `mechanicalChecks`, `methodless`, both hand suites | a full build accepts or refuses on the suite alone |
| **E4, the thinning** | the plan from `layout`; diagnostics, ports, order, routes and toolchains read from the corpus; instructions read from `instructions/` | each Go copy, as its table lands | `engine-neutrality.py`'s `known` list is empty |
| **S1, Studio on the engine** | Studio imports the engine; the operations route and the event stream | the subprocess calls; Studio's verdict code and prompt literals | `front-end-parity.py` passes for `local` and `tenant-api` operations |
| **T1, the change service** | the engine hosted in the tenant as its change service, with the `/v1/admin/changes` and `/v1/admin/build` routes | `cli-in-tenant` as the way any client builds | the parity test passes for every operation |
| **S2, Studio as a client** | each tenant route Studio needs | each local store and service copy, one area at a time | each area reads only from the tenant |
| **F, the terminal front end** | the CLI's pane presentation over the same streams | — | the parity test passes under a pseudo-terminal |

E2 comes before E3 for the reason that ends the CLI audit: without a check
layer, thinning the judge removes the only judge there is. T1 comes before
Studio drives builds, because a client never runs a `cli-in-tenant` operation.

---

## What changes where

### Corpus

- **`architecture/engine.md` (new)**: the parts and their boundary; the
  operation and event model; the closed vocabularies and their versions; the
  three hosts; the record; the engine's own requirements and `verifies`, with
  the neutrality and parity checks.
- **[`architecture/cli`](architecture/cli.md)**: rewritten as the terminal
  front end. The Command Surface becomes the engine's manifest. The `question`
  presentation and panes. The executor table stays.
- **`architecture/studio.md` (new)**: the browser front end. The operations
  route and the stream, what Studio may keep as a host, the areas as
  presentations of operations, and the rule that Studio never falls back to a
  local store.
- **[`architecture/generation`](architecture/generation.md)**: the eight steps
  as data. The plan is fixed by the corpus, which reverses "Why the structure is
  the model's". Instructions are corpus text, which reverses "Does NOT own:
  prompt wording". The translate step. Action reuse. The model's permissions
  per step. The CLI-descriptive text and the Go-toolchain detail move to
  `languages/go.md`.
- **[`architecture/testing`](architecture/testing.md)**: the one suite, L1 to L4
  as declared data, live and sealed checks, and the mock orchestrator as a
  component built from it.
- **`instructions/` (new family)** and **`schemas/instruction.md`**.
- **[`schemas/blocks`](schemas/blocks.md)**: the tenant check kinds and
  `translated`; `live`.
- **[`schemas/language`](schemas/language.md)** and **[`schemas/platform`](schemas/platform.md)**:
  `layout`, `toolchain`, test command, test path and header, diagnostic
  grammar, load-failure and dependency-fault markers, export extraction, and
  module-path derivation. Then each `languages/*.md` and `platforms/*.md`
  fills them in.
- **[`schemas/kinds`](schemas/kinds.md)**: cardinality, `runs_with`, and the
  protocol section each kind binds.
- **[`schemas/run-statement`](schemas/run-statement.md)**: `actions` and
  `criteria`.
- **`checks/`**: `engine-neutrality.py`, `front-end-parity.py` (absorbing
  `command-surface.py`), and `requirement-ids.py` extended. `vectors/engine/`.
- The WHAT-versus-HOW fixes in the files the table in [§3](#where-the-corpus-says-what-and-not-how)
  names.

### Elsewhere

- **The engine module**, in the home decision 1 picks.
- **The CLI**: the migration above.
- **Studio**: MISSION.md's parity sentence; HUB_ARCHITECTURE.md and
  TENANT_CHANGE_CYCLE.md §2 cut to pointers at `architecture/engine.md`, since
  the corpus becomes the one home of what the tools are.

---

## Text already adopted that this proposal would change

| Text | Says | Would say |
|---|---|---|
| [`architecture/generation`](architecture/generation.md#the-plan) | "A generator MUST NOT impose a file structure. It asks the model for one" | The corpus fixes the structure wherever it can |
| [`architecture/generation`](architecture/generation.md#does-not-own) | Does not own prompt wording | The corpus owns every instruction's text |
| [`architecture/generation`](architecture/generation.md#the-run-statement) | A test named by the covering check's id is written by the generator | Tests are translated before generation, and never by the generator |
| `ACCEPTANCE_PLAN` "What counts" | A test the generator wrote does not count | That stays true; a test translated under the four conditions counts |
| Studio's MISSION.md | Studio's standards, adoption and evidence work needs no CLI equivalent | Every operation is reachable from both front ends |

---

## Decisions

Decided by the owner on 2026-11-03.

1. **The engine is its own Go module inside the CLI repository**, which is to be
   renamed `weblisk-tools`, and Studio imports that module. Decided as a
   separate repository first, then changed the same day to keep three
   repositories with one job each: the corpus (all behaviour and every
   document of it), the tools (the engine and the terminal front end), and
   Studio (the browser front end). The engine stays out of the corpus, because
   the corpus is a build input every tenant clones and fingerprints, and it
   stays language-neutral.
2. **The corpus fixes packages and boundary names.** The model's split of a
   package into files is recorded and reused, never re-asked.
3. **Settling S and J.** A translated test may settle a security or contract
   requirement in the development and network environments. In production,
   only a check declared in the corpus settles one; a reviewed translated test
   is promoted into the corpus to do so.
4. **A criterion's digest covers its text and the definitions it cites**, such
   as an error code's status or a type's fields.
5. **Code generation may read translated tests**, and can never write them.
6. **A live check failing after acceptance.** For a security (S) requirement,
   the affected operations are withheld automatically. For a contract (J)
   requirement, the acceptance is marked contradicted and shown.
7. **Either front end may create a tenant**, on the host the tenant will live
   on, by a signed-in operator.
8. **Commands no corpus document drives leave the tools** until one defines
   them: `app *`, `marketplace *`, `deps audit` and `gateway policy *`.
9. **Ids for the unmarked checklist items** are minted in one mechanical pass,
   then frozen.
10. **Model transcripts are kept in the tenant's record**, as the account of
    how each action was done.
11. **Model instructions are a new `instructions/` family.**

The adopted texts listed above are reversed as this plan's parts land.
