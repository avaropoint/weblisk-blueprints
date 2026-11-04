<!-- blueprint
type: architecture
name: engine
version: 1.0.0
requires: [architecture/generation, architecture/cli, schemas/change, schemas/run-statement, schemas/instruction, schemas/kinds, schemas/family, schemas/blocks, protocol/conventions]
platform: any
tier: free
-->
<!-- wl:ids complete -->

# Engine

The one implementation that executes the corpus. Every operation a person or
a script can perform on a corpus or a tenant is an operation of the engine,
and the CLI and Studio are two front ends that present the same operations.
The engine reads everything it acts on from the corpus and knows nothing of
its own about what it reads.

## Overview

**The corpus drives all behaviour, the build process included.** A behaviour
the corpus does not describe is one no tool has. The engine is how that
holds: it interprets the closed vocabularies the corpus declares, runs the
build steps this file declares, and calls a model only with instructions the
corpus writes. Two front ends drive it, and a conformance test proves that
every operation is reachable from both.

The engine is a Go module inside the tools' repository (today the CLI's, to
be renamed `weblisk-tools`), and Studio imports that module. It is not part of
the corpus, because the corpus is a build input every tenant clones and
fingerprints, and it stays language-neutral.

Why it exists, measured, and the order in which today's tools become it, is
[`ENGINE_PLAN.md`](../ENGINE_PLAN.md)'s. That plan is history and migration;
this file is the authority for what the engine is.

### The parts, and the line between them

| Part | Why it exists | Holds | Never holds |
|---|---|---|---|
| **Corpus** | It is the one description of what anything is, how it is built and how it is checked | Specifications, schemas, criteria, declared checks and vectors, the build steps as data, every instruction a model is given, published content | Executable logic. Tenant facts |
| **Engine** | So that the corpus is executed once, by one implementation | Interpreters for the closed vocabularies the corpus declares ([Closed vocabularies](#closed-vocabularies)), and mechanics: processes, caches, digests, signing, transport, streaming | A family, kind, component, language, route, code, threshold, list or sentence of the corpus |
| **CLI** | So that a person or a script can drive the engine from a terminal | Presentation: panes, prompts and `--json`; and its host's notes: where a tenant listens, and which identity to use | An operation the engine lacks. Any decision |
| **Studio** | So that a person can drive the engine from a browser, across every tenant they can reach | Presentation: the areas, the editor surface and the renderers; and its host's notes, as a client may keep | An operation the engine lacks. A tenant's answer. A verdict it computed itself |
| **Model** | So that text the corpus cannot fix in advance can be written: code, tests and repairs | Nothing. It is called, given corpus instructions and named inputs, and its output is recorded | A verdict. A plan the corpus fixes. A name the corpus declares. Its own instructions |
| **Tenant** | So that the customer's system, and the system of record for everything about it, belongs to the customer | Its code, its tests, its record of every build, its changes, content, identities, grants and model; and the engine itself, hosted as its change service | Anything only a client holds |

**Meaning in the corpus, mechanics in the engine, presentation in the front
ends.** A line of engine code that names something is a missing corpus
declaration, and a line of front-end code that decides something is a missing
engine operation.

The engine MUST NOT hold a family, kind, component, language, route, error
code, threshold, list or sentence that the corpus declares; it reads each one
from the corpus file that declares it. <!-- wl:id engine-names-nothing -->

A front end MUST NOT compute a verdict, a threshold or a list. What it shows
is an operation's events, and what it asks is an operation's questions. <!-- wl:id front-end-decides-nothing -->

### Closed vocabularies

The engine knows how to read and how to run, and nothing about what it reads.
What it implements is stated as closed vocabularies that the corpus declares
and versions, the way capabilities are closed in code and kinds are open data
([`schemas/kinds`](../schemas/kinds.md#the-model-open-kinds-closed-capabilities)).

| Vocabulary | Declared by |
|---|---|
| The family grammar's keywords | [`schemas/family`](../schemas/family.md#the-grammar-keywords) |
| Block types | [`schemas/blocks`](../schemas/blocks.md#blocks) |
| Check kinds, the `check` of a `verifies` entry | [`schemas/blocks`](../schemas/blocks.md#definitions) |
| `use` and `send` | [`schemas/family`](../schemas/family.md#the-grammar-keywords) |
| Capabilities | [`schemas/kinds`](../schemas/kinds.md#capabilities) |
| Executors | [`schemas/change`](../schemas/change.md#executors) |
| Build steps | this file, [The build steps](#the-build-steps) |
| Event types | this file, [Events](#events) |

The engine MUST name, in its manifest, the version of the declaring file of
each vocabulary it implements, and MUST refuse a corpus whose declaring file
is at a later major than the one it implements, naming the file and both
versions. <!-- wl:id vocabularies-versioned -->

### Three hosts

The engine runs in three hosts and is the same in each: the CLI, Studio, and
the tenant, where it is the tenant's change service. Where an operation's act
happens is its executor: `local`, `tenant-api` or `cli-in-tenant`
([`schemas/change`](../schemas/change.md#executors)).

A client MUST reach a `cli-in-tenant` operation only through `tenant-api`, by
asking the engine inside the tenant to run it; it never runs one on its own
host against a tenant. <!-- wl:id cli-in-tenant-through-tenant -->

An operation acting on a tenant MUST use the tenant's model, through the
tenant. Only a `local` operation outside any tenant uses the host's model, and
Studio has no model of its own. <!-- wl:id model-is-the-acts-owner -->

---

## Responsibilities

### Owns

- The operations API: one command, one stream of events, and the manifest
  that lists every operation
- The event envelope and the event types every operation shares
- The build steps, their order, and what the model may and may not do in each
- The one conformance suite: what a criterion is, its digest, and when a
  translated test counts
- How the record makes a build incremental: action reuse, test translation
  keyed by the criterion's digest, verdicts carried forward
- The tools' own conformance: neutrality and front-end parity

### Does NOT Own

- How a plan is made, a file generated, a tree repaired or gated. That is
  [`architecture/generation`](generation.md), which the steps run
- The record's fields. That is [`schemas/run-statement`](../schemas/run-statement.md)
  for a run and [`schemas/change`](../schemas/change.md) for a change
- The words a model is given. Each is an instruction in
  [`instructions/`](../instructions/README.md), of the family
  [`schemas/instruction`](../schemas/instruction.md)
- The check kinds' data shapes. Those are [`schemas/blocks`](../schemas/blocks.md)'s
- How a terminal or a browser presents an operation. That is
  [`architecture/cli`](cli.md) for the terminal

---

## Operations

### The shape of an operation

An operation is `<noun> <verb>`, in the grammar of
[`architecture/cli`](cli.md#command-grammar). Family nouns and resource kinds
are read from the corpus and from the tenant; operational nouns and verbs are
a closed set in the engine.

Every operation MUST return exactly one stream of events, whichever front end
started it and whatever it does; an operation has no other output. <!-- wl:id one-command-one-stream -->

### The manifest

The engine publishes its catalogue as one manifest, which the CLI prints as
`weblisk commands --json` and Studio serves unchanged from its operations
route.

```yaml
manifest:
  engine: {module: <module path>, version: <engine version>}
  vocabularies:                    # one per row of Closed vocabularies
    - {ref: <full ref of the declaring file>, version: <its version>}
  operations:
    - operation: <noun verb>
      executor: local | tenant-api | cli-in-tenant
      capability: <the capability that gates it, or always>
      parameters:
        - {name: <name>, type: <a scalar of schemas/blocks>, required: <bool>}
      events: [<event type>]       # the types beyond the common six
```

The engine's manifest MUST list exactly the operations of
[The operation catalogue](#the-operation-catalogue), each with the executor
and events the catalogue gives it. <!-- wl:id manifest-is-the-catalogue -->

Both front ends MUST build their commands, help and menus from the manifest,
and hold no list of operations of their own. <!-- wl:id front-ends-render-manifest -->

### Events

Every event has the same envelope.

```yaml
event:
  operation: <noun verb>
  invocation: <uuid>               # one per invocation, as protocol/conventions writes a uuid
  seq: <integer>                   # 1 for the first event, then each one more
  at: <timestamp>                  # as protocol/conventions writes an instant
  type: <event type>
  body: {}                         # the type's fields, below
```

Each event MUST be one JSON object in the RFC 8785 canonical form. Under
`--json` the CLI writes one per line, and Studio's stream route carries the
same objects, so the two streams of one invocation are equal byte for byte
once `invocation` and `at` are normalised. <!-- wl:id streams-byte-equal -->

An invocation's stream MUST open with exactly one `started` event and close
with exactly one `finished` event, with `seq` rising by one from 1 and no
event after `finished`. <!-- wl:id stream-bracketed -->

Six types are common to every operation, and are not repeated in the
catalogue:

| Type | Carries |
|---|---|
| `started` | the inputs as resolved, and the corpus pins read |
| `step` | which declared step began or ended, with its id from [The build steps](#the-build-steps) |
| `progress` | a count against a known total, or silence observed |
| `question` | something only a person can give ([Questions](#questions)). The stream waits for an answer |
| `warning` | something the run continued past, with its reason |
| `finished` | the result, with exit status, and what was recorded |

An operation adds its own types from this closed list:

| Type | Carries |
|---|---|
| `item` | one row of a read |
| `artifact` | a file written, with its path and digest |
| `model` | one model call: the instruction refs and digests, the input digest, the output digest and the model the backend reported |
| `check` | one test or check run: the criterion id, the result and its reason |
| `gap` | a criterion left unsettled or unmet: its class, its reach and the exposure statement |
| `verdict` | a component's verdict, as [`schemas/run-statement`](../schemas/run-statement.md#the-verdict-a-run-ends-with) writes it |
| `event` | a tenant event relayed |

### Questions

A `question` is how the two front ends stay interchangeable: the CLI answers
one in a pane, Studio in a dialog, and neither has a flow the other lacks.

```yaml
question:
  kind: passphrase | vault | step-up | signature | confirm | secret | choice
  about: [<full ref>]              # what the answer is for
  choices: [<text>]                # kind choice only
```

An answer is sent back to the invocation with the `seq` of the question it
answers, and the stream resumes.

When an operation needs something only a person can give, it MUST emit a
`question` and wait for its answer. It never reads a terminal, a file or an
environment variable for it, and never assumes one. <!-- wl:id question-is-the-only-ask -->

The answer to a question of kind `passphrase`, `secret` or `signature` MUST
NOT appear in any event, record, transcript or log; a `signature` answer
reaches the record only as the signed artifact it produced. <!-- wl:id secret-answers-never-recorded -->

A question that is declined, or that its front end cannot answer, MUST end
the operation refused, naming the question; the engine never proceeds on a
default. <!-- wl:id unanswered-is-refused -->

### The operation catalogue

Every operation the engine publishes. `<family>` stands for each noun a family
declaration gives ([`schemas/family`](../schemas/family.md)), and `<kind>` for
each resource kind the tenant's catalogue declares
([`architecture/admin`](admin.md#resources-one-api-for-every-kind)). `events`
lists the types beyond the common six, and `driven_by` the corpus files that
say what the operation does. The CLI's commands as built today, and what each
is renamed to, are [`architecture/cli`](cli.md#the-command-surface)'s; the
check that holds both against this catalogue is
[`checks/front-end-parity.py`](../checks/front-end-parity.py).

```yaml
operations:
  # The manifest itself.
  - ops: [commands]
    executor: local
    events: [item]
    records: nothing
    driven_by: [architecture/engine]
  # Corpus: each reads a source the person holds, and none touches a tenant.
  - ops: [corpus sources, corpus update]
    executor: local
    events: [item]
    records: the source cache, which is a cache
    driven_by: [architecture/cli]
  - ops: [<family> validate, <family> walk, <family> show, <family> list]
    executor: local
    events: [item, check]
    records: nothing
    driven_by: [schemas/family, schemas/blocks]
  - ops: [<family> deps, <family> diff]
    executor: local
    events: [item]
    records: nothing
    driven_by: [architecture/generation, schemas/common]
  - ops: [<family> new, <family> rename, <family> retire, <family> release]
    executor: local
    events: [artifact]
    records: the file and its own history
    driven_by: [schemas/authoring, RETIRED.md, schemas/common]
  - ops: [schema export]
    executor: local
    events: [item]
    records: nothing
    driven_by: [schemas/family]
  - ops: [platform list, platform show]
    executor: local
    events: [item]
    records: nothing
    driven_by: [schemas/language, schemas/platform]
  # Tenant lifecycle.
  - ops: [tenant new]
    executor: local
    events: [artifact, model, check, gap, verdict]
    records: the first change and its run statements, config, the tenant's keys, on the host that will hold the tenant
    driven_by: [architecture/cli, schemas/config, schemas/programme]
  - ops: [tenant connect]
    executor: tenant-api
    events: [item]
    records: the host's note of address and operator name; the token in memory only
    driven_by: [architecture/cli, architecture/admin]
  - ops: [tenant status]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [protocol/spec, architecture/admin]
  - ops: [tenant verify]
    executor: tenant-api
    events: [check, gap, verdict]
    records: runtime verdicts in the record
    driven_by: [architecture/engine]
  - ops: [tenant export, tenant rebuild]
    executor: cli-in-tenant
    events: [artifact, check]
    records: a bundle, or a rebuild run in the record
    driven_by: [architecture/tenancy, architecture/cli]
  - ops: [component start, component stop, component logs]
    executor: cli-in-tenant
    events: [item, check]
    records: process state, which is a note
    driven_by: [architecture/cli, schemas/config]
  # Builds and changes: tenant-api once the tenant runs its change service,
  # cli-in-tenant until then (architecture/cli, Until a tenant runs a change service).
  - ops: [change plan]
    executor: tenant-api
    events: [item, gap]
    records: the change, at .weblisk/changes/<id>.json
    driven_by: [architecture/generation, schemas/change, architecture/change-management, schemas/programme]
  - ops: [change list, change show]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [schemas/change]
  - ops: [change approve, change reject]
    executor: tenant-api
    events: []
    records: the approval or rejection on the change
    driven_by: [architecture/cli, protocol/types]
  - ops: [change apply]
    executor: tenant-api
    events: [model, artifact, check, gap, verdict]
    records: run statements with their actions and criteria; outcomes on the change
    driven_by: [architecture/engine, architecture/generation, schemas/run-statement]
  - ops: [change verify]
    executor: tenant-api
    events: [check, verdict]
    records: a verify run; verify on the change
    driven_by: [architecture/engine]
  - ops: [change revert]
    executor: tenant-api
    events: [item, gap]
    records: a new change of kind revert
    driven_by: [schemas/change]
  - ops: [build]
    executor: local
    events: [model, artifact, check, gap, verdict]
    records: run statements in the output directory
    driven_by: [architecture/engine, architecture/generation]
  - ops: [run status]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [schemas/run-statement]
  - ops: [acceptance propose, acceptance decide]
    executor: tenant-api
    events: [item]
    records: the change's acceptance block
    driven_by: [ACCEPTANCE_PLAN.md, schemas/change, schemas/config]
  - ops: [test run]
    executor: tenant-api
    events: [check, gap, verdict]
    records: verdicts in the record
    driven_by: [architecture/engine]
  - ops: [record show]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [schemas/run-statement]
  - ops: [impact]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [architecture/fabric, architecture/change-management]
  - ops: [cache status, cache prune]
    executor: local
    events: [item]
    records: the cache
    driven_by: [architecture/generation]
  # Integrations and platforms.
  - ops: [provider list]
    executor: [local, tenant-api]
    events: [item]
    records: nothing
    driven_by: [architecture/orchestrator, architecture/model-service]
  - ops: [model choose]
    executor: tenant-api
    events: [check]
    records: the tenant's model setting, in the tenant
    driven_by: [architecture/orchestrator]
  - ops: [integration list, integration add, integration check, integration remove]
    executor: tenant-api
    events: [item, check]
    records: the tenant's integration records
    driven_by: []
    undriven: the integration service is proposed and not yet a blueprint
  - ops: [content backend list, content backend add, content backend check]
    executor: tenant-api
    events: [item, check]
    records: the tenant's configuration, through a change
    driven_by: [architecture/content]
  # Operations on a running tenant.
  - ops: [resource list, resource show]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [architecture/admin, schemas/resource]
  - ops: [<kind> list, <kind> show, <kind> create, <kind> update, <kind> delete, <kind> <verb>, <kind> watch]
    executor: tenant-api
    events: [item, event]
    records: the tenant's own record of the act
    driven_by: [architecture/admin, schemas/resource]
  - ops: [approval list, approval show, approval accept, approval reject]
    executor: tenant-api
    events: [item]
    records: the decision, at its owner
    driven_by: [protocol/types, architecture/admin]
  - ops: [audit]
    executor: tenant-api
    events: [item, event]
    records: nothing
    driven_by: [architecture/admin]
  - ops: [identity init, identity store, identity path]
    executor: local
    events: [item]
    records: the host's own identity, which is the installation's
    driven_by: [architecture/cli, protocol/identity]
  - ops: [identity register, identity token, identity attest, identity rotate]
    executor: tenant-api
    events: []
    records: the host's own identity and its credential at the tenant
    driven_by: [architecture/cli, protocol/identity]
  - ops: [secret list, secret set, secret get, secret delete, secret rotate]
    executor: local
    events: [item]
    records: the secret source
    driven_by: [patterns/secrets]
  # Content.
  - ops: [content list, content read, content history]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [architecture/content]
  - ops: [content write, content move, content remove]
    executor: tenant-api
    events: [check, artifact]
    records: the tenant's content commit and change statement
    driven_by: [architecture/content, patterns/content-git, documents/families/README.md]
  - ops: [content reconcile]
    executor: tenant-api
    events: [item, gap]
    records: content's records
    driven_by: [architecture/content]
  - ops: [document check]
    executor: [tenant-api, local]
    events: [check, gap]
    records: nothing
    driven_by: [documents/families/README.md, schemas/family]
  - ops: [standard adopt]
    executor: tenant-api
    events: [artifact]
    records: the tenant's standard file, linking the published one
    driven_by: [schemas/standard]
  - ops: [programme adopt]
    executor: tenant-api
    events: [item, gap]
    records: the change, and the adoption record
    driven_by: [schemas/programme]
  - ops: [fabric trace]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [architecture/fabric]
  - ops: [attest]
    executor: tenant-api
    events: []
    records: the tenant's attestation record
    driven_by: [architecture/content]
    undriven: the statement vocabulary of an attestation has no corpus home yet
```

---

## The build steps

`change apply`, and a scratch `build`, run these eight steps. How the plan,
generate and repair steps and the verification gate work is
[`architecture/generation`](generation.md)'s; this list is their order, what
each needs declared, and what a model may do in each. A step is
**determined** when everything it decides is read from the corpus, and
**guessed** when something is left to the engine or the model.

The engine MUST run the steps in the order below, each step beginning only
after the one before it ended, and MUST emit a `step` event as each begins
and ends. <!-- wl:id steps-in-order -->

A step for which the corpus does not declare what it needs MUST be recorded as
guessed, naming each declaration it lacked; the engine never supplies a
default of its own in its place. <!-- wl:id guessed-is-reported -->

```yaml
steps:
  - id: resolve
    does: Takes the build set and the context set, versions, pins and the conflicts C1 to C8
    model: none
    declares: >-
      The two closures and the conflicts (architecture/generation); how many of
      each kind a tenant may run, runs_with, and the protocol section each kind
      binds (schemas/kinds); component order (the services table of
      schemas/programme); the default target, and the languages and platforms
  - id: plan
    does: Fixes the files, packages, names and order, wherever the corpus can fix them
    model: called
    inputs: [requirements, package-plan, blueprints, tenant-state]
    declares: >-
      A layout per language and platform: packages, the file-per-section rule,
      the entry point (schemas/language); boundary names; module-path
      derivation; manifest and export extraction per language; duplicate rules
      across packages; ownership of shared packages
    model_may: >-
      Divide each package's work into files, name them and say what each is
      for; name a private helper inside one file where the layout leaves room.
      Its division is recorded and reused, never asked again
    model_may_not: >-
      Choose a package, a boundary name or an entry point; place a declared
      symbol; invent a name the corpus does not declare
  - id: translate
    does: Writes one executable test per translated criterion, from the criterion and the declared contract alone, before any code exists
    model: called
    inputs: [criterion, contract, plan-names, language-test]
    declares: >-
      Durable criterion ids and digests; the check kinds and their data
      (schemas/blocks); the test path, header form and test command per
      language; the fixtures
    model_may: >-
      Write a test from one criterion, the declared contract (types,
      operations, codes, fixtures) and the plan's names; report a criterion as
      untestable
    model_may_not: >-
      See any implementation; weaken a criterion; decide a verdict
  - id: generate
    does: Writes each planned file
    model: called
    inputs: [plan-entry, declarations, file-set, platform, checklists, blueprints, tenant-state, tests]
    declares: >-
      The prompt contract (architecture/generation), the instructions, and the
      rules the model must not settle: missing names, ties, scope
    model_may: >-
      Write a planned file; read the translated tests
    model_may_not: >-
      Write or edit a test; invent a name the corpus does not declare, which
      it reports as a gap; settle a tie or a contradiction, which it reports;
      add scope
  - id: build
    does: Builds the tree, starts it sealed, and runs the suite
    model: none
    declares: >-
      The build, run and test commands per language; the diagnostic grammar,
      load-failure and dependency-fault markers per language; the sealed
      environment; ports; which routes are essential
  - id: repair
    does: Edits files until the suite passes, class by class
    model: called
    inputs: [failure, governing-section, repair-set, declarations, blueprints]
    declares: >-
      The instruction per repair kind; the governing section given with each
      failure; which files a diagnostic implicates, per language; the class
      order; the round ceilings as configuration
    model_may: >-
      Edit files in the repair set, given the failing test's output and the
      governing section
    model_may_not: >-
      Edit a test, a name the plan fixes, or a file outside the set
  - id: accept
    does: Applies the build gate, and proposes runtime acceptance
    model: called
    inputs: [criterion, tree]
    declares: >-
      Classes and their derivation; environments; withholding
    model_may: >-
      Read the tree; its reading is printed as advice
    model_may_not: >-
      Move any verdict, in either direction
  - id: record
    does: Writes what every step did; the next change starts from it
    model: none
    declares: >-
      The record's shape (schemas/run-statement); the rebuild table
      (architecture/generation); a diff by part id; impact by binding
      (architecture/change-management)
```

Which instructions each step's prompt carries is read from each instruction's
`in` ([`schemas/instruction`](../schemas/instruction.md)), and this list does
not repeat it.

### What the model may not do

A model MUST NOT move a verdict, in either direction. Its reading of a tree,
at any step, is printed as advice and is never counted toward acceptance. <!-- wl:id model-reads-are-advice -->

The engine MUST refuse a model's answer that writes outside what its step
permits: a test path from a generate or repair answer, a name the plan fixes
changed, or a file outside the repair set. A refused answer is asked again
with its reason, as any answer that is not acceptable is. <!-- wl:id model-output-bounded -->

A conflict between two corpus texts that a model reports MUST be recorded as
a corpus finding, and settled only by a corpus change a person makes. It is
never accepted on the model's word, and never settles a verdict. <!-- wl:id conflict-is-proposed -->

### Instructions

The engine MUST give a model no sentence of its own. Every instruction in a
model's prompt is a file of [`instructions/`](../instructions/README.md),
given as [`schemas/instruction`](../schemas/instruction.md) says, and every
other part of the prompt is a declared input, labelled with its name. <!-- wl:id no-engine-sentences -->

The engine MUST tell the model which revision of each instruction it is
following, by ref and version, and MUST record that revision's digest on the
action ([`schemas/run-statement`](../schemas/run-statement.md#actions)). <!-- wl:id instruction-revision-recorded -->

A tenant's agent work is a different thing. It stays in a programme's
`skills:` and the prompt worker
([`architecture/prompt-worker`](prompt-worker.md)), and nothing in
`instructions/` is given to a tenant's agent.

---

## The one conformance suite

One suite, derived from the corpus, decides whether a component conforms. It
replaces every hand-written suite and every verdict a model gives.

A tool MUST NOT hold a conformance test, a check or a verdict rule of its own;
what conformance runs is derived from the corpus as below, and nothing else
counts. <!-- wl:id one-suite -->

### The unit is a criterion

A **criterion** is one checklist item, or one requirement (`wl:id`) that no
checklist item covers. Each has a durable id and a digest.

A criterion's id, once minted, MUST NOT be derived again or changed. A
criterion whose text changes keeps its id and takes a new digest. <!-- wl:id criterion-id-frozen -->

A criterion's digest MUST cover its text and every definition it cites, such
as an error code's status, a type's fields or an operation's route, so a
change to a cited definition moves the digest of every criterion that cites
it. <!-- wl:id criterion-digest-covers-citations -->

The digest is the SHA-256 of the RFC 8785 bytes of this object, written
`sha256:<hex>` ([`patterns/content-identity`](../patterns/content-identity.md)):

```yaml
criterion_digest_input:
  text: <the criterion's text, its id marker removed, each run of whitespace one space, trimmed>
  cites:                           # sorted by ref; empty when it cites nothing
    - ref: <full ref of the cited definition: a type, an error, an operation, a check's data>
      digest: <that definition's digest, over its value, as schemas/family digests a block entry>
```

A `wl:check <id> covers <ids>` comment is today's spelling of a `verifies`
entry ([`schemas/blocks`](../schemas/blocks.md#definitions)): id, `covers`,
`check` and `assertion`. A criterion is settled in one of two ways, which its
`check` names: by a **declared check** of a kind
[`schemas/blocks`](../schemas/blocks.md) declares, whose data is written in
the corpus, or by a **translated test**, which is the default and is written
`translated`.

### How the suite is derived

| Layer | Written by | Lives | Runs |
|---|---|---|---|
| **Declared checks**: `verifies` entries of a declared kind | corpus authors, with a model's help in a corpus change a person reviews | in the corpus, beside the requirement; large fixtures in `vectors/<blueprint>/` | by the engine's interpreter for that kind, which is language-neutral |
| **Translated tests**: one per `translated` criterion | the translate step, from the criterion alone | in the tenant, with its code, at the path the language declares, each with a header carrying the criterion's id, its digest and the translating action | by the language's declared test command |
| **Published vectors** | the corpus | delivered to `testdata/weblisk-vectors/` ([`architecture/generation`](generation.md#published-test-vectors)) | through the tests that name them |

A translated test that a corpus author later writes as declared data is
**promoted**: it moves into the corpus, is owed by every tenant, and the
tenant's copy is retired.

### What makes a translated test count

A translated test MUST count toward acceptance only when all four of these
hold, and the record MUST show each of them for it. <!-- wl:id translated-test-counts -->

1. **It was written apart from the code.** The translate step runs before
   generation and is given no implementation; the order and the inputs of
   the record's actions prove both.
2. **It fails on nothing.** Before any code is generated, it is run against a
   stub built from the plan's declarations alone, and it fails there. A test
   that passes against nothing tests nothing.
3. **It is frozen.** Generation and repair cannot write a test path.
4. **Its verdict is the run's.** Pass, fail or error comes from the test
   command's exit and output, in the grammar the language declares.

The translate step MUST be given no file of the implementation, and no
output of a generate or repair action. <!-- wl:id translated-apart -->

Before any code is generated, each translated test MUST be run against a stub
built from the plan's declarations alone; a test that does not fail there
does not count, and is reported as testing nothing. <!-- wl:id fails-on-nothing -->

A generate or repair action MUST NOT write a test path, and a test whose
bytes changed outside a translate action MUST be refused as an edited file is
refused. <!-- wl:id tests-frozen -->

A test's verdict MUST be read from the test command's exit status and output,
in the grammar the language declares, and from nothing else. <!-- wl:id verdict-is-the-runs -->

Code generation may read the translated tests, and can never write them. A
criterion the translate step reports untestable
([`instructions/corpus-finding`](../instructions/corpus-finding.md)) is
recorded as a corpus finding against it, and stays unsettled until the corpus
changes it.

In production, a security (S) or contract (J) criterion MUST be settled only
by a check declared in the corpus. A translated test settles one in the
development and network environments, and a reviewed translated test is
promoted into the corpus to settle one in production. The classes and the
environments are [`ACCEPTANCE_PLAN.md`](../ACCEPTANCE_PLAN.md)'s. <!-- wl:id production-s-j-declared -->

### Build time and run time

At build time, the whole suite runs in the sealed environment, and its
results are the build gate. At run time, a check runs against a live tenant
only where it declares that it may: `live: safe` or `live: sealed-only`, a
field of a `verifies` entry.

A check MUST run against a live tenant only when it declares `live: safe`;
one that declares nothing is `sealed-only`. <!-- wl:id live-only-safe -->

`tenant verify` and `test run --live` run the safe checks against the running
tenant, on demand or on the cadence the tenant configures. The build gate
counts the sealed results by class, and a runtime acceptance cites the latest
live results.

When a live check fails after acceptance, the affected operations of a
security (S) criterion MUST be withheld automatically; for a contract (J)
criterion the acceptance MUST be marked contradicted, and shown so wherever
the acceptance is shown. <!-- wl:id live-failure-after-acceptance -->

---

## The record

The record lives in the tenant, in its repository, and is written by the
tenant's change service; until a tenant runs a change service, the engine on
the tenant's host writes it in the same shape. It is an answer about the
customer's system.

A client MUST NOT hold the record. Front ends read it through the tenant's
routes ([`architecture/admin`](admin.md#changes-and-builds)), and any index
over it is a cache, rebuilt from the statements. <!-- wl:id record-in-tenant -->

It is not a second ledger. It is the run statement
([`schemas/run-statement`](../schemas/run-statement.md)), one immutable file
per run, which gains its [actions](../schemas/run-statement.md#actions) and
[criteria](../schemas/run-statement.md#criteria); and the change
([`schemas/change`](../schemas/change.md)), whose plan names the tests a
change translates. Their fields are those files', and are not restated here.

Each model action's transcript MUST be kept in the tenant's record, as the
account of how the action was done, and cited from the action by digest. <!-- wl:id transcripts-kept -->

### How the record makes builds incremental

Before the engine runs any action, deterministic or model, it MUST look for a
completed action with the same step, the same instruction digests and the
same input digests, and where one exists it MUST reuse that action's outputs
and record the reuse. A model is never asked the same question twice. <!-- wl:id action-reused -->

A revision of an instruction MUST NOT by itself make a recorded output stale:
a plan, a file or a test made under an earlier revision is kept, and is
marked made under an older instruction. Making it again is a change somebody
makes on purpose. <!-- wl:id older-instruction-kept -->

A translated test MUST be translated again only when its criterion's digest
moves. <!-- wl:id test-follows-criterion-digest -->

A file MUST be rebuilt only when the rebuild table of
[`architecture/generation`](generation.md#deciding-whether-a-file-must-be-rebuilt)
says so, read through the criteria the file is answerable for. <!-- wl:id rebuild-by-table -->

A verdict MAY be carried forward to a later run while its test's digest and
the digest of everything the test reaches are unchanged, and the record MUST
say which verdicts were carried and from which run. A black-box test reaches
the whole component, so it runs again whenever the component is rebuilt. <!-- wl:id verdict-carried -->

A build MUST start from the record of the build before it: the first from an
empty record, `tenant rebuild` from the exported record, and none from
scratch. <!-- wl:id never-from-scratch -->

---

## The tools' own conformance

The tools are specified in the corpus, so the corpus checks them, with
controls, as [`checks/`](../checks/README.md) checks the corpus.

### Neutrality: the engine holds no corpus knowledge

| Proof | How | Control |
|---|---|---|
| **A fake corpus** | `vectors/engine/` holds a miniature corpus with invented families, kinds, components, check kinds and a fake language (extending [`vectors/mapping/fake-language.md`](../vectors/mapping/fake-language.md)), whose build, run and test commands are scripts it declares. The engine builds it, and the record equals the expected record | An engine with one corpus name compiled in fails on the renamed one |
| **A renamed corpus** | The real corpus, with every declared name renamed consistently, gives the same plan, tests and record, modulo the renaming | Renaming one family in the corpus and not in a copy of the expected record is reported |
| **No literals** | [`checks/engine-neutrality.py`](../checks/engine-neutrality.py) reads the tools' source at a pinned commit and lists every string literal equal to a name the corpus declares. The list is held to its `known` entries, which can only shrink | Adding one corpus name to a copy of the source is reported |
| **Closed vocabularies only** | The engine's manifest lists the vocabularies it implements and their versions, each one the corpus declares | A manifest naming an undeclared check kind is reported |

The engine MUST build the fake corpus of `vectors/engine/` to exactly its
expected record, and the real corpus renamed consistently to the record of the
real corpus under the same renaming. <!-- wl:id neutral-by-renaming -->

The tools' source MUST hold no string literal equal to a name the corpus
declares beyond the `known` entries of `checks/engine-neutrality.json`, and an
entry leaves that list when its literal leaves the source. <!-- wl:id no-corpus-literals -->

### Parity: the CLI and Studio are interchangeable

| Proof | How | Control |
|---|---|---|
| **One catalogue** | Each front end exposes the engine's manifest unchanged: `weblisk commands --json`, and Studio's operations route. [`checks/front-end-parity.py`](../checks/front-end-parity.py) compares each with [The operation catalogue](#the-operation-catalogue) and with each other, at pinned commits | A front end missing one operation, or having one of its own, is reported |
| **The same streams** | A parity test drives every operation through the CLI (`--json`, under a pseudo-terminal) and through Studio's stream route, against the fake corpus and a sealed fixture tenant, with the same scripted answers to each `question`. The two streams are equal once invocation ids and instants are normalised | An operation whose `question` one front end cannot answer is reported |
| **No decisions in a front end** | The neutrality check runs over both front ends' sources | Adding a posture threshold to a copy of the Studio source is reported |

Every operation of the catalogue MUST be reachable from both front ends, and
each front end MUST expose the engine's manifest unchanged. <!-- wl:id front-end-parity -->

---

## Security

The model is given no tool, no file and no shell, and the engine writes every
file itself after checking its path, as
[`architecture/generation`](generation.md#security) and
[`architecture/cli`](cli.md#generated-output-is-untrusted) say for generation;
the translate and accept steps are held to the same. A `question` is the one
way a secret reaches an operation, and its answer is never recorded
([Questions](#questions)). An operation's act happens where its executor says,
and a host never runs a `cli-in-tenant` operation for a tenant it does not
host ([Three hosts](#three-hosts)).

---

## Implementation Notes

**Normalise before comparing streams.** Two streams of one invocation differ
in `invocation` and in every `at`; everything else is equal or one of them is
wrong.

**A stub that fails is the point.** The stub a translated test first runs
against declares every name the plan fixes and does nothing. A test that
passes against it is reported, never quietly kept.

**Reuse is a lookup, not a judgement.** An action's reuse key is the step,
the instruction digests and the input digests, each as recorded. Nothing else
is consulted, and nothing about the model's answer is.

---

## Verification Checklist

- [ ] No string literal of the tools' source equals a name the corpus declares beyond the `known` list, and adding one to a copy of the source is reported ([Neutrality: the engine holds no corpus knowledge](#neutrality-the-engine-holds-no-corpus-knowledge)) <!-- wl:check tools-hold-no-corpus-names covers engine-names-nothing no-corpus-literals -->
- [ ] The engine builds the fake corpus of `vectors/engine/` to its expected record, and a consistently renamed corpus to the renamed record ([Neutrality: the engine holds no corpus knowledge](#neutrality-the-engine-holds-no-corpus-knowledge)) <!-- wl:check fake-and-renamed-corpus covers neutral-by-renaming engine-names-nothing -->
- [ ] The manifest names each vocabulary's declaring file and version, and a corpus whose declaring file is a later major is refused, naming the file and both versions ([Closed vocabularies](#closed-vocabularies)) <!-- wl:check vocabulary-versions-refused covers vocabularies-versioned -->
- [ ] Studio, asked for a `cli-in-tenant` operation on a tenant, asks the tenant's engine through `tenant-api` and runs nothing on its own host ([Three hosts](#three-hosts)) <!-- wl:check client-asks-tenant covers cli-in-tenant-through-tenant -->
- [ ] An operation acting on a tenant calls the tenant's model through the tenant, and Studio calls no model of its own ([Three hosts](#three-hosts)) <!-- wl:check tenant-model-for-tenant-acts covers model-is-the-acts-owner -->
- [ ] Every operation in the manifest returns one event stream opened by one `started` and closed by one `finished`, with `seq` rising by one from 1 ([Events](#events)) <!-- wl:check streams-bracketed covers one-command-one-stream stream-bracketed -->
- [ ] The manifest lists exactly the catalogue's operations with their executors and events, and each front end exposes it unchanged ([The manifest](#the-manifest), [The operation catalogue](#the-operation-catalogue)) <!-- wl:check manifest-equals-catalogue covers manifest-is-the-catalogue front-ends-render-manifest front-end-parity -->
- [ ] Driving one operation through the CLI under `--json` and through Studio's stream route, with the same scripted answers, gives streams equal byte for byte once `invocation` and `at` are normalised ([Events](#events)) <!-- wl:check streams-equal covers streams-byte-equal front-end-parity -->
- [ ] An operation needing a passphrase emits a `question` and waits; with no answer it ends refused naming the question; and the answer appears in no event, record, transcript or log ([Questions](#questions)) <!-- wl:check questions-asked-and-kept-secret covers question-is-the-only-ask secret-answers-never-recorded unanswered-is-refused -->
- [ ] A front end shows a verdict, threshold or list only as an operation's events carry it, and the neutrality check over its source reports one computed in it ([The parts, and the line between them](#the-parts-and-the-line-between-them)) <!-- wl:check front-end-computes-nothing covers front-end-decides-nothing -->
- [ ] `change apply` emits a `step` event as each of resolve, plan, translate, generate, build, repair, accept and record begins and ends, in that order ([The build steps](#the-build-steps)) <!-- wl:check steps-ordered covers steps-in-order -->
- [ ] A step whose corpus declaration is missing is recorded as guessed, naming what it lacked, and no engine default is used in its place ([The build steps](#the-build-steps)) <!-- wl:check guessed-step-recorded covers guessed-is-reported -->
- [ ] A model's reading never moves a verdict; a conflict it reports is recorded as a corpus finding and settles nothing; an answer writing a test path, a plan-fixed name or a file outside the repair set is refused with its reason ([What the model may not do](#what-the-model-may-not-do)) <!-- wl:check model-bounded covers model-reads-are-advice conflict-is-proposed model-output-bounded -->
- [ ] Every sentence of every model prompt is an instruction file's folded text or a labelled declared input, and the action records each instruction's ref, version and digest ([Instructions](#instructions)) <!-- wl:check prompts-are-corpus-text covers no-engine-sentences instruction-revision-recorded -->
- [ ] Conformance runs only the declared checks, the translated tests and the published vectors, and no tool holds a test, check or verdict rule of its own ([The one conformance suite](#the-one-conformance-suite)) <!-- wl:check suite-is-derived covers one-suite -->
- [ ] A criterion keeps its id when its text changes; its digest moves when its text or any definition it cites changes, and not otherwise ([The unit is a criterion](#the-unit-is-a-criterion)) <!-- wl:check criterion-id-and-digest covers criterion-id-frozen criterion-digest-covers-citations -->
- [ ] A translated test counts only with all four conditions shown on the record: the translate action precedes every generate action and was given no implementation, the test failed against the stub, no generate or repair action wrote it, and its verdict is the test command's ([What makes a translated test count](#what-makes-a-translated-test-count)) <!-- wl:check translated-test-conditions covers translated-test-counts translated-apart fails-on-nothing tests-frozen verdict-is-the-runs -->
- [ ] In production, an S or J criterion settled only by a translated test is unsettled ([What makes a translated test count](#what-makes-a-translated-test-count)) <!-- wl:check production-needs-declared covers production-s-j-declared -->
- [ ] A check with no `live` declaration is not run against a live tenant; a live S check failing after acceptance withholds the affected operations, and a live J check failing marks the acceptance contradicted ([Build time and run time](#build-time-and-run-time)) <!-- wl:check live-checks covers live-only-safe live-failure-after-acceptance -->
- [ ] The record is written in the tenant and read by front ends through the tenant's routes, and each model action cites a transcript the tenant holds ([The record](#the-record)) <!-- wl:check record-held-by-tenant covers record-in-tenant transcripts-kept -->
- [ ] An action whose step, instruction digests and input digests equal a completed action's is not run again and records the reuse; an instruction revision alone re-runs nothing ([How the record makes builds incremental](#how-the-record-makes-builds-incremental)) <!-- wl:check actions-reused covers action-reused older-instruction-kept -->
- [ ] A test is translated again only when its criterion's digest moves, a file is rebuilt only as the rebuild table says, a carried verdict names the run it came from, and every build starts from the record before it ([How the record makes builds incremental](#how-the-record-makes-builds-incremental)) <!-- wl:check incremental-from-record covers test-follows-criterion-digest rebuild-by-table verdict-carried never-from-scratch -->
