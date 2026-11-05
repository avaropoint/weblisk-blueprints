# The Weblisk tools: one engine, two front ends, driven by the corpus

> **Status: adopted by the owner on 2026-11-03, with the decisions recorded in
> [Decisions](#decisions), including the reversals in
> [Text already adopted that this proposal would change](#text-already-adopted-that-this-proposal-would-change).**
> It is the plan of work. It stays at the corpus root as a plan, because a
> file under `architecture/` is a blueprint and its MUST lines are read as
> requirements. Each part becomes normative only when it lands in the
> document [What changes where](#what-changes-where) names for it, and from
> then on that document, not this plan, is the authority.
>
> **Landed in phase C0** (each section below says where): the engine itself
> in [`architecture/engine.md`](architecture/engine.md) (sections 1 to 5 and
> 7), the instruction family in [`schemas/instruction`](schemas/instruction.md)
> and [`instructions/`](instructions/README.md) (section 4), and the record's
> fields in [`schemas/run-statement`](schemas/run-statement.md) and
> [`schemas/change`](schemas/change.md) (section 6). What remains here is the
> measurement, the gaps still open, the migration and the decisions.
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

**Landed in [`architecture/engine.md`](architecture/engine.md#the-parts-and-the-line-between-them)**: the parts
and what each holds and never holds, the line between meaning, mechanics and
presentation, the closed vocabularies and their versions
([Closed vocabularies](architecture/engine.md#closed-vocabularies)), the three hosts and whose
model an act uses ([Three hosts](architecture/engine.md#three-hosts)). That file is the
authority; this section is no longer restated here.

---

## 2. The engine's operations

**Landed in [`architecture/engine.md`](architecture/engine.md#operations)**: the shape of an operation, the
manifest (`weblisk commands --json`), the event envelope and its common and
operation types, the `question` event, and the operation catalogue
([The operation catalogue](architecture/engine.md#the-operation-catalogue)), with the executor,
events, records and driving documents of each operation. What remains here is
migration: which of today's commands fold into which operation.

**The envelope's instant is `at`.** The CLI's first streams wrote it as
`instant`; [`architecture/engine`](architecture/engine.md#events) keeps `at`
as normative (owner's decision, 2026-11-04), and the CLI changes to it.

**Folded or deleted**

| Today | Becomes |
|---|---|
| `server init`, `component <kind> init`, `agent create`, `domain create`, `gateway create` | `change plan --adopt`, then `change apply` |
| `server verify`, `agent verify`, `test conformance` | `test run` |
| `server start` · `stop` · `logs` · `status`, `agent start`, `domain start`, `gateway start` | `component start` · `stop` · `logs`, and `tenant status` |
| `test mock-orchestrator` | Deleted from the tools. The mock that [`architecture/testing`](architecture/testing.md#mock-orchestrator) specifies is built from that specification, like any other component |
| `pattern apply` | Deleted: it is a legacy pipeline with no plan, no ownership check, no build and no conformance |
| `deploy rollback` | `change revert` |
| `app new` · `dev` · `build` · `vendor`, `update`, `marketplace *`, `deps audit`, `gateway policy *`, `doctor` | Leave the tools until a corpus document defines them (decision 8, with `doctor` and `update` added on 2026-11-04) |
| `version`, `help`, `commands` | Stay, as front-end-only commands: they describe the tool itself, so they are not operations and the manifest does not list them (2026-11-04; [`architecture/engine`](architecture/engine.md#front-end-only-commands)) |

---

## 3. What executing the corpus means

**Landed in [`architecture/engine.md`](architecture/engine.md#the-build-steps)**: the eight steps, their order,
what each does and what each needs the corpus to declare, determined against
guessed, and what the model may and may not do in each. What remains here is
measured: where each step is still guessed today.

| # | Step | Gaps today, from the audits |
|---|---|---|
| 1 | **Resolve** | Kind cardinality is in CLI Go (`singletonKinds`, four constructors). The section-to-kind binding is a Go switch. Service order and ports have a second copy in the CLI. An unknown platform falls back to Go |
| 2 | **Plan** | `generation.md` said the plan is the model's (now packages are the language's layout, 2.0.0). go.md's package table was prose and nothing enforced it, so all 48 library files landed in one package and 3 types were defined in 3 packages. Export extraction exists only for Go and JS |
| 3 | **Translate** | 2,643 of 2,835 checklist items have no id. Check kinds for a tenant (`exchange`, `vector`, `join`, `record`, `topology`, `structure`) are in `ACCEPTANCE_PLAN` only. Vectors are never delivered. The instruction home now exists ([`instructions/`](instructions/README.md)) |
| 4 | **Generate** | The CLI tells the model to invent missing names, settle ties in a comment, and ignore the scope prohibition, all against `generation.md`. The model-gateway source is CLI-embedded Go |
| 5 | **Build and test** | The diagnostic grammars are Go in Go (so Rust and Node cannot be repaired). The load-failure words are in `generation.md`, not `languages/go.md`. Essential routes are a CLI list. The Go toolchain check looks up a moved file and never runs |
| 6 | **Repair** | Repair prompts are Go literals with rules found nowhere in the corpus. A repair sees the model's evidence and not the blueprint section. The ceilings are CLI constants |
| 7 | **Accept** | The threat model's controls are prose. There is no registration slot. The environment and the development flag have no home. Withholding does not exist |
| 8 | **Record**, then **change incrementally** | No actions or criteria are recorded. Nothing writes the build lock. There is no structured diff, so every blueprint edit rebuilds a whole component |

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

**Landed** in [`architecture/engine.md`](architecture/engine.md#the-build-steps) (each step's `model_may` and
`model_may_not`, and [What the model may not do](architecture/engine.md#what-the-model-may-not-do)),
and in the instruction family: [`schemas/instruction`](schemas/instruction.md)
and [`instructions/`](instructions/README.md), whose first files are the five
`generation.md` 2.0.0 gave as written and the step instructions `plan`,
`translate`, `generate`, `repair` and `advise`. The per-kind repair
instructions (`instructions/repair/<kind>.md`) are not written: the repair
kinds are not yet declared, and until they are, instruction `failure` tells
the kinds apart by the failure input's `kind`. The CLI's plan, generate and
repair prompts are composed from these and the steps' declared inputs alone
(E4): the instructions that read each input (`requirements`, `package-plan`,
`tenant-state`, `plan-shape`, `plan-entry`, `declarations`, `repair-set`,
`failure`, `edit-form`, `rejection`) were written from the literals they
replace. The accept step's reading and conflict question wait on E3, which
decides their shape as advice. Studio's prompts, counted again at S1
(2026-11-05), are 24 literals, the audit's 16 less one retired with its route
plus 9 it missed, and none belongs to a build step: each is assistant,
authoring, drafting, review or scheduling work, which is a programme's
`skills:` run by the tenant's prompt worker and never an instruction. So none
moved to `instructions/`; they leave Studio with the prompt worker (S2).

---

## 5. The one conformance suite

**Landed in [`architecture/engine.md`](architecture/engine.md#the-one-conformance-suite)**: the criterion as the
unit, its frozen id and its digest over its text and the definitions it cites
(decisions 4 and 9), the three layers, the four conditions a translated test
must meet to count, promotion, settling S and J (decision 3), live and sealed
checks and a live failure after acceptance (decision 6). What remains here is
the minting pass, which is the corpus lane's, and what the suite replaces.

- The 192 items that carry a `wl:check` keep their ids. The other 2,643 get an
  id minted once, from their text at the time of minting (decision 9).
- `check:` names how a criterion is settled: a declared kind from
  `schemas/blocks`, or `translated`, the default. `live:` is the field that
  says whether a check may run against a live tenant; it lands in
  `schemas/blocks` with the check kinds.
- `requirement-ids.py` grows to hold that every checklist item in a file marked
  complete has an id.

### What it replaces

`dispatch/conformance.go`, `conformance_register.go` and `interop.go`;
`internal/test` (`weblisk test`); `selfverify.go` as a verdict; `corpus_conflict`
as a verdict; `verify.go`'s phrase-bound structural checks; `checklist.go`'s
`mechanicalChecks`; `methodless.go`; the essential-route list in
`pkg/tenant/route`; and, in tests only, `operator/fakehub`. Each is deleted only
after its replacement runs ([§8](#8-migration)).

---

## 6. The record

**Landed.** Where the record lives, that a client never holds it, transcripts
kept in the tenant (decision 10), and the five rules that make a build
incremental, action reuse among them, are
[`architecture/engine.md`](architecture/engine.md#the-record)'s. The fields are
[`schemas/run-statement`](schemas/run-statement.md#actions)'s `actions` (each
with its instruction refs and digests, input and output digests, transcript
and reuse) and [`criteria`](schemas/run-statement.md#criteria) (each with its
digest over its text and cited definitions, its tests and the four
conditions, its reach, verdict and gap), with their rules and vectors in
[`vectors/run-statement/`](vectors/run-statement/README.md). A translated
test's place in a change's plan, and the verdicts `translate` and `review`
because `older-instruction`, are [`schemas/change`](schemas/change.md#verdicts)'s.

---

## 7. The tools' own conformance

**Landed in [`architecture/engine.md`](architecture/engine.md#the-tools-own-conformance)**, with its checks:
[`checks/engine-neutrality.py`](checks/engine-neutrality.py), whose `known`
list began as the CLI audit's restated knowledge at CLI `4d54da8` and is
held at the commit `checks/engine-neutrality.json` pins, and
[`checks/front-end-parity.py`](checks/front-end-parity.py), which replaces
`command-surface.py`. Not yet built: the fake corpus in `vectors/engine/`, the
renamed-corpus run, the stream parity test, and neutrality over Studio's
source. Both front ends publish a manifest (S1): the CLI's `weblisk commands
--json` and Studio's `GET /api/operations`, each pinned in
[`checks/front-ends.json`](checks/front-ends.json). They are the engine's
one manifest and agree with each other. Held to the `local` and `tenant-api`
operations, as S1 is, each differs from the catalogue by the same 66 measured
gaps, the file's `expected_gaps`: the engine still publishes today's spellings
(`providers`, `walk`, `validate`, `status`, `doctor`, `operator *`, `agents *`)
and names its builds and changes `cli-in-tenant`, where the catalogue has
`provider list`, `identity *`, `<family> walk`, `tenant status` and those
operations as `tenant-api`. Each gap closes in the engine (E2 to E4, T1), not
in a front end, and leaves the list when it does.

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
| The tenant-record stores (22k): change ledger, attestations, evidence, audit, retention, access, comments, chat | the tenant's routes, store by store in [S2](#s2-which-tenant-route-replaces-which-studio-store) | each route, which is G11 in Studio's TENANT_CONNECTION_PLAN |
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
| **T1, the change service** | the engine hosted in the tenant as its change service, with the `/v1/admin/changes` and `/v1/admin/build` routes, as [`architecture/change-service`](architecture/change-service.md) specifies them | `cli-in-tenant` as the way any client builds | the parity test passes for every operation |
| **S2, Studio as a client** | each tenant route Studio needs | each local store and service copy, one area at a time | each area reads only from the tenant |
| **F, the terminal front end** | the CLI's pane presentation over the same streams | — | the parity test passes under a pseudo-terminal |

E2 comes before E3 for the reason that ends the CLI audit: without a check
layer, thinning the judge removes the only judge there is. T1 comes before
Studio drives builds, because a client never runs a `cli-in-tenant` operation.

### S2: which tenant route replaces which Studio store

Written 2026-11-05 against corpus `9342483` and Studio `b538565a`, from the
Studio drift audit's class (d) and Studio's own classification of its state
(`internal/server/server_state_dir.go`, and TENANT_CONNECTION_PLAN §G11). It
is the order of S2 above, area by area. A row says which tenant route takes
over a store, and what Studio deletes once that route answers in the
development tenant. Until a route answers, the area says *not served by this
tenant* and does not read the local store (see "What Studio stops doing
locally" above).

**Where each store goes.** "Specified" means a tenant blueprint already
held the home before this pass. "Added" means this pass wrote it.

| Studio store or service | Tenant home | State of the home |
|---|---|---|
| The programme-service copy (`obligations`, `obligation_status`, `obligation_discharge`, `due`, `program_events`, `register*`, `programme*`, `handlers_program*`; 17.0k lines) | [`architecture/programme-service`](architecture/programme-service.md): `/v1/programme/obligations`, `/occurrences`, `/due`, `/readiness`, `/items`, `/installations`; [`execution`](architecture/execution.md) for starts and runs; [`notification`](architecture/notification.md) for telling | Specified. Still open there: programme objectives, and reading attestations |
| `jobs.json`, tenant jobs | an operation in a programme map the organisation holds, installed by the programme service, its start at execution | Specified. A platform job (installation housekeeping) stays Studio's and is never handed tenant data |
| `workflows.json` | programme workflows, run by execution with its waits | Specified |
| `due-notices.json` | the programme service's record of each advance and whether notification accepted it, and notification's deduplication | Specified |
| `trigger-conditions.json` | the programme service's counted conditions and execution's `Condition` | Specified |
| `studio-agents.json` (named instructions) | a `skill` file in the organisation's content, run unattended by an `agent:` item through the prompt worker, or by a console for a person who is present | Specified for both paths. A console run's record is **added** (next row) |
| `agent-runs/` (65 MB of transcripts) | execution's run ledger. Unattended work is recorded through the prompt worker's dispatch. A console's interactive run is **`POST /v1/execution/console-runs`**, `…/{run}/turns`, `…/{run}/end` | **Added**: [`architecture/execution`](architecture/execution.md#a-run-a-console-ran) 1.4.0, `execution:record`, `Run.definition_kind` `console`, `RunStep.asked`, `reported` and `withheld` ([`protocol/types`](protocol/types.md) 6.7.0), and the console's leave to record ([`architecture/admin`](architecture/admin.md) 5.7.0, `console-credential-use`) |
| The agent runner and its prompts (10.9k lines) | the prompt worker for unattended work; the console's run for interactive work; instruction text in [`instructions/`](instructions/README.md) or a programme's `skills:` | Specified, apart from the console run above |
| `changes/` ledger and pending changes | content's change log, proposals and decisions, with separation of duties | Specified |
| `trash/` (pre-images) | **`GET /v1/content/entry?version=`**, where the backend keeps history. A restore is a write | **Added**: [Reading an earlier version](architecture/content.md#reading-an-earlier-version) |
| `attestations/log.jsonl`, `reseals.jsonl` | **`/v1/content/attestations`**, kept in a sealed, chained store. A re-seal is that log's key succession | **Added**: [Entry attestations](architecture/content.md#entry-attestations), the `weblisk/content-attestation/v1` statement ([`protocol/identity`](protocol/identity.md) 3.5.0, no vectors yet) |
| `attestations/invitations.jsonl`, `envelopes.jsonl` | **`/v1/content/attestation-requests`**, `order: sequential` for an envelope | **Added** for operators. Signers outside the tenant are an owner decision (below) |
| `attestations/signing-key.json`, `keyring.json` | none. They are Studio's own seal key | Stays until attestations move, and then nothing needs it |
| `evidence.json`, `evidence-files/` | an entry in a content repository, with what it proves as a fabric `proves` relationship | Specified. Evidence strength and posture have no corpus home (§3, H2 and M3) |
| `compliance-snapshots.json` | none. A posture is derived, and a snapshot that is cited needs the posture rule first | Gap, behind H2 |
| `relationships.log` | the fabric's ledger, `/v1/fabric/*` | Specified. A person's assertions work on their pass now. Studio's unattended sync needs its service identity (G8), which admin specifies no route for |
| project `audit.log` | each tenant service's own audit, and `/v1/admin/audit` | Specified. Studio's local audit keeps only the installation's own acts |
| `events.json`, `integrations.json` | [`INTEGRATION_PLAN.md`](INTEGRATION_PLAN.md) | Proposed, not adopted |
| `retention/` | **`/v1/content/retention`**, **`/v1/content/holds`**, **`/v1/content/disposals`** | **Added**: [Retention and holds](architecture/content.md#retention-and-holds) |
| `comments/` | **`/v1/content/comments`** | **Added**: [Comments](architecture/content.md#comments) |
| `document-requests/` | **`/v1/content/document-requests`**, answered by a proposal | **Added** for operators. Outside parties are the same owner decision as external signers |
| `chat/` | none | Owner decision (below) |
| `section-access.json` | none | Owner decision (below) |
| `access.json`, `principals.json` (the customer's half) | the orchestrator's `grant` kind and admin's operators | Specified. Studio already reads grants (G11) |
| `identity/keys.jsonl` (escrowed seeds) | none. Nothing moves: [`architecture/admin`](architecture/admin.md)'s `console-no-sign-records` forbids a console from holding anyone's sign-records key | Delete. There is no migration |
| `identity/service-identities.jsonl` | Studio's own service identity at the hub (G8) | Gap. Not this lane's |
| `webhooks/hooks.jsonl`, `deliveries.jsonl` | [`agents/webhook`](agents/webhook.md), a published agent a tenant adopts | Specified as an agent. Notification has no webhook channel adapter |
| `mail-profiles.json` | [`agents/email-send`](agents/email-send.md)'s sender | A relay per organisation or project is not specified |
| `hierarchy.json`, `tenancy-identity.json` | the orchestrator's `organisation` and `project` kinds | Specified. Studio already reads them for a tenant that serves them |

**The kinds added** are `entry-attestation`, `attestation-request`,
`document-request`, `comment`, `retention-schedule` and `legal-hold`
([`schemas/kinds`](schemas/kinds.md) 1.8.0), each declared at the uniform
address ([`architecture/content`](architecture/content.md#resources) 5.6.0).
The capabilities added are `content:attest`, `content:request`,
`content:comment`, `content:retain`, `content:hold` and `execution:record`,
all six person only. The roles carry them as [`architecture/admin`](architecture/admin.md#operator-roles)
gives them: a viewer may attest. Each route has its checks in its file's
Verification Checklist, with ids minted.

**The order.** Each step deletes nothing until its route answers in the
development tenant. Content comes first because most stores land there and
every later area reads it.

| Step | Area | Tenant routes it becomes a client of | Gated on | Studio deletes after |
|---|---|---|---|---|
| S2.1 | Documents and their history | content's entry, proposal, decision and log routes; `GET /v1/content/entry?version=` | the content service running in the development tenant (G11 steps D and F) | `changes/`, `trash/`, the local apply, gate, approver and separation paths, and the direct path through `resolveSourcePath` |
| S2.2 | Evidence | content entries in an evidence repository; the fabric's `proves` | S2.1, and the fabric service running | `evidence.json`, `evidence-files/`, the evidence-scan writer (H5). `compliance-snapshots.json` stops being written, and posture says *unscoreable* until H2 has a home |
| S2.3 | Relationships | `/v1/fabric/*` | the fabric service; G8 for unattended sync | `relationships.log` as system of record. The `relate` package stays, as the fold of what the fabric answers |
| S2.4 | Attestation and sign-off | `/v1/content/attestations`, `/v1/content/attestation-requests` | S2.1; vectors for `weblisk/content-attestation/v1` before anything is reported `signed` | `attestations/log`, `invitations`, `envelopes` and `reseals`, then the seal key and keyring. External signing is shown *not served* until the owner decides |
| S2.5 | Retention and holds | `/v1/content/retention`, `/holds`, `/disposals` | S2.1 | `retention/`, `program_retention.go`'s local reckoning |
| S2.6 | Comments and requests | `/v1/content/comments`, `/v1/content/document-requests` | S2.1 | `comments/`, `document-requests/` (operators only). `chat/` waits for the owner |
| S2.7 | Programmes and what is due | the programme service, execution and notification | all three running; the programme service reading attestations for sign-off | the 17.0k-line programme copy, tenant jobs in `jobs.json`, `workflows.json`, `due-notices.json`, `trigger-conditions.json` |
| S2.8 | Agents | the prompt worker for unattended work; `/v1/execution/console-runs` for interactive work | S2.7; the model service route | `agent-runs/`, the agent scheduler, `studio-agents.json` (its instructions become skill files), the 16 prompt literals (with S1) |
| S2.9 | People and access | orchestrator grants and admin operators | already served (G11) | the customer's half of `access.json` and `principals.json`; `identity/keys.jsonl` at once, since it is forbidden rather than unhomed |
| S2.10 | Integrations, webhooks and mail | [`INTEGRATION_PLAN.md`](INTEGRATION_PLAN.md), `agents/webhook`, `agents/email-send` | an adopted integration plan; a notification webhook channel; a per-scope sender | `integrations.json`, `events.json`, `webhooks/`, `mail-profiles.json` |

**What needs the owner** is listed in [Open items](#open-items), each from
this pass.

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

| Text | Says | Would say | Where it stands |
|---|---|---|---|
| [`architecture/generation`](architecture/generation.md#the-plan) | "A generator MUST NOT impose a file structure. It asks the model for one" | The corpus fixes the structure wherever it can | Reversed: packages from the layout in 2.0.0, and the model's division recorded and reused in 3.0.0 ([What the model still decides](architecture/generation.md#what-the-model-still-decides)) |
| [`architecture/generation`](architecture/generation.md#does-not-own) | Does not own prompt wording | The corpus owns every instruction's text | Reversed in 3.0.0: every sentence is an instruction in [`instructions/`](instructions/README.md) |
| [`architecture/generation`](architecture/generation.md#the-run-statement) | A test named by the covering check's id is written by the generator | Tests are translated before generation, and never by the generator | Reversed in 3.0.0, and in [`schemas/run-statement`](schemas/run-statement.md#rules) rule 3 |
| `ACCEPTANCE_PLAN` "What counts" | A test the generator wrote does not count | That stays true; a test translated under the four conditions counts | Open: the row is ACCEPTANCE_PLAN's to amend; the four conditions are [`architecture/engine`](architecture/engine.md#what-makes-a-translated-test-count)'s |
| Studio's MISSION.md | Studio's standards, adoption and evidence work needs no CLI equivalent | Every operation is reachable from both front ends | Open: Studio's to amend |

## Open items

Deferred by the owner on 2026-11-04, each until the condition its row names.
The rows from "A signer outside the tenant" to "Retention beyond content"
were found on 2026-11-05, specifying the tenant homes S2 needs, and each waits
for the owner. Nothing here is decided; each row says what stays true until
it is.

| Item | Stays | Until | Where it is stated |
|---|---|---|---|
| The Rust crate for ML-DSA | **UNFILLED**. A generation for Rust is refused before any model call, naming the row | the owner names a crate | [`languages/rust`](languages/rust.md#primitive-mapping) |
| A signer outside the tenant | Attesting, and answering a document request, need an operator's pass, so only the tenant's own operators can sign or supply a document. Studio's external signing is shown *not served* | the owner decides whether a tenant has a door for a person with no operator identity, which component serves it, and how that person is identified. Found 2026-11-05 | [`architecture/content`](architecture/content.md#what-is-still-open) |
| Who may change the attestation words | `attestation_statements` is closed and the corpus's | the owner decides whether a tenant may add words, which would make a signed word's meaning depend on the tenant | [`architecture/content`](architecture/content.md#entry-attestations) |
| Restricting one section of an entry | not specified: an entry's scope is the whole entry's, and `section-access.json` has no home | the owner chooses between splitting such an entry and a redacted read, which answers bytes that are not the entry's | [`architecture/content`](architecture/content.md#what-is-still-open) |
| People's chat | no tenant service keeps it, and `chat/` has no home | the owner decides whether people's chat is in the product, or is left to the integrations it already names (Slack, Teams) | this plan, [S2](#s2-which-tenant-route-replaces-which-studio-store) |
| Reading another person's console run | its words are answered only to its person | the owner decides whether an auditor may read them | [`architecture/execution`](architecture/execution.md#known-gaps) |
| A console recording its run | admitted, as a MAY in `console-credential-use`: a console may record the run at execution on the person's token, and do nothing else | the owner confirms the widening, which is the first write a console sends that a person did not choose item by item | [`architecture/admin`](architecture/admin.md#contracts) |
| The roles that carry the new capabilities | a viewer may attest; only an admin may hold or record a console run; operators carry the rest | the owner confirms, in particular whether a viewer may comment | [`architecture/admin`](architecture/admin.md#operator-roles) |
| What an attestation proves | `entry-attestation` has no capability, so nothing counts it as evidence | the programme service reads attestations for sign-off and occurrences, and the owner decides whether the kind takes `proves` | [`schemas/kinds`](schemas/kinds.md#declared-kinds) |
| Retention beyond content | a schedule or a hold governs content's entries only | the owner decides whether one hold reaches runs, notifications and audit logs | [`architecture/content`](architecture/content.md#what-is-still-open) |
| A storage conditional-put primitive | not required of any backend | more than one instance may answer for a hub (`instances.max` above 1 in [`schemas/kinds`](schemas/kinds.md#component-kinds)) | [`architecture/storage`](architecture/storage.md#what-a-backend-must-be) |

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
   them: `app *`, `marketplace *`, `deps audit` and `gateway policy *`, and,
   added on 2026-11-04, `doctor` and `update`. `version`, `help` and
   `commands` stay as front-end-only commands, because they describe the tool
   itself ([`architecture/engine`](architecture/engine.md#front-end-only-commands)).
9. **Ids for the unmarked checklist items** are minted in one mechanical pass,
   then frozen.
10. **Model transcripts are kept in the tenant's record**, as the account of
    how each action was done.
11. **Model instructions are a new `instructions/` family.**

The adopted texts listed above are reversed as this plan's parts land; the
table says where each stands.
