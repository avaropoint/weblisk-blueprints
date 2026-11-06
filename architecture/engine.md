<!-- blueprint
type: architecture
name: engine
version: 1.7.0
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
| Endpoint auth, the `auth` of a served endpoint, and so which endpoints are protected | [`schemas/blocks`](../schemas/blocks.md#which-endpoints-are-protected) |
| Probe roles, `live` and `ready`, and each one's route and answer | [`protocol/spec`](../protocol/spec.md#get-livez-and-get-readyz), its `probes` block |
| `use` and `send` | [`schemas/family`](../schemas/family.md#the-grammar-keywords) |
| Capabilities | [`schemas/kinds`](../schemas/kinds.md#capabilities) |
| Executors | [`schemas/change`](../schemas/change.md#executors) |
| Build steps | this file, [The build steps](#the-build-steps) |
| Build order: its roles, unit forms, orders, phases and integration | this file, [Build order](#build-order) |
| Event types | this file, [Events](#events) |

The engine MUST name, in its manifest, the version of the declaring file of
each vocabulary it implements, and MUST refuse a corpus whose declaring file
is at a later major than the one it implements, naming the file and both
versions. <!-- wl:id vocabularies-versioned -->

### Three hosts

The engine runs in three hosts and is the same in each: the CLI, Studio, and
the tenant, where it is the tenant's change service
([`architecture/change-service`](change-service.md)), which says which
operations it hosts and at which route. Where an operation's act
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
- The build order: the layers a change's units are built in, what gates each,
  and what a suite is run against
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

### Front-end-only commands

Three commands describe the tool itself rather than act on a corpus or a
tenant, so they are a front end's and not the engine's: `version` (the front
end's version and the engine's it embeds), `help` (the manifest, rendered),
and `commands` (the manifest, printed). In Studio they are the about panel,
the help it renders and the operations route. They are not operations: the
manifest does not list them, they return no event stream, and parity does not
compare them, because each front end presents them its own way (owner's
decision, 2026-11-04).

**The signer's entry point is not a front end's command.** `weblisk sign`
([`architecture/cli`](cli.md#weblisk-sign)) is the CLI acting as the person's
signer on a pointer ([`protocol/identity`](../protocol/identity.md#a-signer-acting-on-a-pointer)):
it runs one of the catalogue's operations that needs a signature, as that
operation, and is never a console's, because a console never signs
([`architecture/admin`](admin.md#contracts), `console-never-drives-signer`).

A front end MUST hold no command other than the manifest's operations and
these three, and, in a signer, `sign`; and each of the three MUST read nothing
but the manifest and the front end's own build. <!-- wl:id front-end-only-three -->

**Commands no corpus document drives leave the tools** until a corpus document
defines them: `doctor`, `update`, `app *`, `marketplace *`, `deps audit` and
`gateway policy *`. A behaviour the corpus does not describe is one no tool
has ([Overview](#overview)). Each returns when the document that defines it
lands, as an operation of [The operation catalogue](#the-operation-catalogue).
The CLI's commands as built today, and when each is removed, are
[`ENGINE_PLAN.md`](../ENGINE_PLAN.md#2-the-engines-operations)'s.

The tools MUST NOT offer `doctor`, `update`, `app *`, `marketplace *`,
`deps audit` or `gateway policy *` while no corpus document defines it. <!-- wl:id undriven-commands-absent -->

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

An event MUST carry exactly the envelope's six fields, under the names above
and no others: the instant is `at`, never `instant` or `time`, so that two
front ends' streams compare without a mapping between them (owner's decision,
2026-11-04). <!-- wl:id envelope-names-fixed -->

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
| `step` | which declared step began or ended, with its id from [The build steps](#the-build-steps); during a build, the layer and the unit it is about ([Build order](#build-order)), and for a unit not built, `skipped` with what it waited for |
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
  pointer:                         # kind signature only: the act, for the person's signer
    hub_id: <the hub's hub_id>
    operation: <the pointer's operation, as protocol/identity's pointer table names it>
    arguments: [<text>]
    text: weblisk sign <hub_id> <operation> <argument>...
    link: weblisk://sign/<hub_id>/<operation>/<argument>...
  compare: [<text>]                # kind signature only: the short forms the signer will show
```

An answer is sent back to the invocation with the `seq` of the question it
answers, and the stream resumes.

```yaml
answer:
  seq: <the question's seq>
  form: value | handoff | declined
  value: <text>                    # form value
  record: <full ref>               # form handoff: the owner's record of the act
```

**A signature is handed off, never carried.** Where the person is at a
console, a `signature` question is answered by their signer
([`protocol/identity`](../protocol/identity.md#a-signer-acting-on-a-pointer)),
which reads the subject from its owner, shows it, signs, and submits the act
itself; the console shows the `pointer` and the `compare` short forms, and
answers with form `handoff` and the record's ref once the owner's record shows
the act ([`architecture/admin`](admin.md#contracts), `console-hands-off-signing`).
At the CLI the CLI is the signer, and answers its own question the same way.
The engine reads the subject at its owner before it asks, on the invoking
front end's own token, and again on a `handoff`.

The engine MUST end an operation `finished` on a `handoff` answer only where
the owner's record, read by the engine itself and never taken from the
answer, is of the operation and subject the question was `about`; was not on
the subject when the question was asked; names as its signer the pass's
`identity_id`; and is `signed` — for a change, an `approval` or `rejection`
whose `signature` verifies over the rebuilt `weblisk/change-decision/v1`
statement under its `attestation`, whose `purpose` is `sign-records` and whose
`identity_id` is that signer's. Any other `handoff` ends the operation refused
naming the question, and the `records` of a finished event are the owner's
record in both front ends. <!-- wl:id signature-handoff-answer -->

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
  # Builds and changes: tenant-api, hosted by the tenant's change service
  # (architecture/change-service, The operation catalogue), and cli-in-tenant
  # until a tenant runs one (architecture/cli, Until a tenant runs a change service).
  - ops: [change plan]
    executor: tenant-api
    events: [item, gap]
    records: the change, at .weblisk/changes/<id>.json
    driven_by: [architecture/generation, schemas/change, architecture/change-management, schemas/programme, architecture/change-service]
  - ops: [change list, change show]
    executor: tenant-api
    events: [item]
    records: nothing
    driven_by: [schemas/change, architecture/change-service]
  - ops: [change approve, change reject]
    executor: tenant-api
    events: []
    records: the approval or rejection on the change
    driven_by: [architecture/cli, protocol/types, architecture/change-service]
  - ops: [change apply]
    executor: tenant-api
    events: [model, artifact, check, gap, verdict]
    records: run statements with their actions and criteria; outcomes on the change
    driven_by: [architecture/engine, architecture/generation, schemas/run-statement, architecture/change-service]
  - ops: [change stop]
    executor: tenant-api
    events: []
    records: the build run ended stopped, and its run statement's result stopped
    driven_by: [architecture/change-service, schemas/run-statement]
  - ops: [change verify]
    executor: tenant-api
    events: [check, verdict]
    records: a verify run; verify on the change
    driven_by: [architecture/engine, architecture/change-service]
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
    driven_by: [schemas/run-statement, architecture/change-service]
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

The engine MUST run the steps in the order below for each unit, each step
beginning only after the one before it ended, and MUST emit a `step` event as
each begins and ends. Which unit goes through them when, and how a layer's
units share the build step, is [Build order](#build-order)'s. <!-- wl:id steps-in-order -->

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
    inputs: [requirements, package-plan, blueprints, tenant-state, rejection]
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
    inputs: [plan-entry, declarations, file-set, platform, checklists, blueprints, tenant-state, tests, rejection]
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
      environment; ports; which routes are essential; the probes and their
      answers (the probes block of protocol/spec)
  - id: repair
    does: Edits files until the suite passes, class by class
    model: called
    inputs: [failure, governing-section, repair-set, declarations, blueprints, rejection]
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
with its reason, the step's input `rejection`, as any answer that is not
acceptable is. <!-- wl:id model-output-bounded -->

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

## Build order

The build steps say what happens to one unit of a tenant's code. This section
says in which order the units go through them, and when a unit's tests may
run. It is where the order of
[`ACCEPTANCE_PLAN.md`](../ACCEPTANCE_PLAN.md#order) becomes normative: a
component is built and tested only once everything it depends on has been
built and accepted, and it is tested against those accepted builds, never
against a half-built tree or a stub standing in for one.

Why, measured on one adoption of the development tenant:

- A component's model-route install compiled while another component's tree
  was half rebuilt, and failed for a reason that was not its own.
- Each component's rebuild regenerated the shared contract package under the
  others: one plan rebuilt the orchestrator, then admin and content, because
  the orchestrator rewrote the package they link against.
- Content's suite ended at startup before any behaviour of its own was
  tested: its registration needs an orchestrator, and the sealed run started
  it beside none.

### Layers

A change's units are arranged in layers. Each layer is computed from the
corpus and from the change's build set, never from a list in a tool.

```yaml
build_order:
  foundation:
    - role: contract
      units: one
      from: union
      means: >-
        The layout's contract package (schemas/language, layout.contract),
        holding every declared name of every component the tenant holds once
        the change is applied: the union of each one's declared names, of the
        kinds layout.contract.holds lists. Generated first
    - role: library
      units: per-blueprint
      order: requires
      means: >-
        Each library package a component of the tenant requires, one unit per
        library blueprint, generated after the contract package in the order
        requires gives: a library after every library it requires
  components:
    role: component
    units: per-component
    order: [needs, runs_with, depends_on]
    tie: services
    means: >-
      Each component of the build set, layered by what it needs running first:
      the orchestrator's layer is 1, and a component is in the layer above the
      deepest component it needs; a kind that runs_with another is a unit of
      its host's layer; within a layer, the services table's order, then the
      domain services, then the published agents, each by name
  phases: [generate, compile, test, accept]
  integration: whole-hub
```

| Key | Means |
|---|---|
| `foundation` | Layer 0: the units every component links against, in the order listed, each role's units in its own `order` |
| `components` | Layers 1 and up |
| `role` | A layout role ([`schemas/language`](../schemas/language.md#the-layout-block)). Every package of the tenant is in exactly one role, so every package is in exactly one layer |
| `units` | `one`: the role's packages are one unit. `per-blueprint`: one unit per blueprint the layout maps to the role. `per-component`: one unit per component, its own package and its entry |
| `from: union` | The unit is made from the union of what every component of the tenant declares, never from the declarations of one |
| `order: requires` | Ordered by `requires` among the role's blueprints, which is acyclic ([`schemas/common`](../schemas/common.md#field-constraints), [`checks/acyclic.py`](../checks/acyclic.py)) |
| `order: needs` | The services table's *needs running first* ([`schemas/programme`](../schemas/programme.md#the-services-in-the-order-they-are-built)) |
| `order: runs_with` | [`schemas/kinds`](../schemas/kinds.md#component-kinds)' `runs_with`: the unit is built in its host's layer and tested in its host's process |
| `order: depends_on` | A domain service's or a published agent's `depends_on` |
| `tie: services` | The services table's order decides between two units of one layer |
| `phases` | What a layer does, in order, before the layer above begins ([Within a layer](#within-a-layer)) |
| `integration: whole-hub` | After the last layer, the whole hub runs once ([Integration](#integration)) |

The engine MUST compute a change's layers from `build_order`, the layout of
the tenant's language, the services table, `schemas/kinds`' `component_kinds`
and the `requires` and `depends_on` of the blueprints the build set reaches,
and MUST hold no order of its own. A `requires` or `depends_on` cycle among the
units of one role is refused before any model call, naming the cycle. <!-- wl:id layers-from-corpus -->

Layer 0 MUST be the foundation: the contract package first, then the library
packages in the order `requires` gives. Then the component layers, from the
orchestrator's. A unit MUST NOT be generated before, or placed in a layer
below, a unit it requires, needs, or depends on. <!-- wl:id layer-order -->

`change plan` MUST show a change's layers, each with its units, and for each
component unit what it needs running first and what it requires; and every
`step` event of an apply MUST name the layer and the unit it is about. <!-- wl:id layers-shown -->

### Within a layer

Every unit of a layer goes through plan, translate and generate before any
unit of it reaches build. The build step is then the layer's: every unit of
the layer is compiled, with the language's `build_package` for a unit with no
entry and its `build_component` for a component
([`schemas/language`](../schemas/language.md#the-toolchain-block)), and only
once the whole layer compiles does any unit's suite run. Repair and accept
follow, unit by unit.

The engine MUST generate every file of every unit in a layer, and compile the
layer as a whole, before it runs any test of any unit in that layer. <!-- wl:id generate-compile-then-test -->

A layer that does not compile MUST be recorded as a build verdict: its repair
works from the toolchain's diagnostics, the build classes first, and no
conformance check or translated test of the layer runs, or is counted, until
the layer compiles. A compile failure is never reported as a test failure. <!-- wl:id compile-failure-is-build -->

A toolchain command that compiles more than one layer, such as the
language's `build` over every package of the module, MUST NOT run while any
layer of a change is still being built; and a step the engine performs on a
component's tree outside generation, such as wiring a route the platform
provides into it, MUST run only once that component's layer and every layer
below it are complete. <!-- wl:id no-cross-layer-compile -->

### Concurrency

The files of one unit's plan are generated level by level: a level is every
file whose in-plan dependencies are all in lower levels, so the files of one
level are independent of each other by construction, and each is given what
the contract package, the plan's declared names and the lower levels hold.
The repairs one round asks for are likewise each written from the tree the
round started on. How many of those model calls are in flight at once is
declared here, and is the engine's whole bound on it.

```yaml
concurrency:
  files_in_flight: 4
```

`files_in_flight` is a positive integer: the most files of one level the
engine generates at once, and the most repairs of one round it asks for at
once. Where the corpus declares no `concurrency` block, or `files_in_flight`
is not a positive integer, the bound is 1: every call waits for the one
before it.

The engine MUST NOT have more than `files_in_flight` generation or repair
calls of one unit in flight at once, and MUST take their results in the
plan's order, so that what a run produces, banks and records does not depend
on the order calls answered in. A file of a level MUST be given only what
lower levels and the plan hold, never what another file of its own level
returned. <!-- wl:id files-in-flight -->

A unit's prepare step, such as the language's dependency resolution, MUST be
run again before a build only where the module's manifest, or an import of
the tree that neither the module itself nor the language's standard library
satisfies, has changed since its last run that succeeded; otherwise the last
run's result stands, and a layer whose units bring no new dependency resolves
once. Where the engine cannot read a source's imports, prepare runs. <!-- wl:id prepare-when-moved -->

### Gating

A layer starts when every unit of every layer below it has ended. A unit in it
is built only where every unit it depends on was **build-accepted**: its
conformance `established` or `accepted`, as
[`architecture/generation`](generation.md#build-acceptance) decides. What a unit
depends on is the contract package, the libraries its blueprint requires, and
the components it needs running first.

A unit whose dependency was not build-accepted MUST NOT be generated, compiled
or tested. Its outcome is `skipped`, naming each dependency it waited for and
that dependency's own outcome, and every unit that depends on it is skipped
the same way. <!-- wl:id dependant-skipped -->

The contract package and the library packages are what every component above
them links against, so a refused one skips every component that requires it. A
component that nothing above it needs skips nothing.

### Shared code

The contract package is generated once per change, first in layer 0, before any
component, and is not touched by any later unit of the change. Layer 0 is
planned as one plan whose files lie only in the foundation's packages, so the
contract and the libraries agree on every name they share, and is generated
in its units' order: the contract package's files, then each library's after
the libraries it requires. Generating it
reads the declared names of every component the tenant holds, not only those
the change builds, so a component the change keeps still finds every name it
was built against.

The engine MUST generate the contract package once per change, first in layer 0, from
the union of the declared names every component of the tenant needs, and a
component's plan MUST NOT place a file in the contract package: a name the
contract holds is imported from it. This replaces a later component adding its
own declared names to the package beside another's. <!-- wl:id contract-once-per-change -->

A library package is likewise a unit of its own layer, generated from its
blueprint once per change, and a component's plan MUST NOT place a file in a
library package. A library has no process, so its suite is the layer compiling
and any declared check of kind `structure` its blueprint carries; the criteria
it answers are owed and judged through every component that requires it
([What a component owes](#what-a-component-owes)). <!-- wl:id library-unit-once -->

### The test environment

A component's suite runs in the sealed environment against its dependencies'
**accepted builds**: the trees each dependency was build-accepted with, built
into a scratch directory of their own when the dependant's layer begins, before
any unit of that layer is generated. Nothing a later layer writes reaches them.

The engine MUST run a component's suite with every component it needs running
first started from its accepted build, in the services table's order, brought
up as [`architecture/testing`](testing.md#bringing-up-accepted-dependencies)
declares, and the component under test pointed at the accepted orchestrator.
It MUST NOT start a mock or a stub for a dependency that has an accepted build. <!-- wl:id tested-against-accepted -->

| Who is started | When |
|---|---|
| the accepted builds of what it needs running first | every suite run of a component that needs anything running first, and every check whose `start` is `orchestrator: built` or names `with` |
| the mock orchestrator | only a check whose own `start` is `orchestrator: mock`: one that tests a component's client of the orchestrator in isolation, or the orchestrator itself. It is never put in place of the accepted orchestrator for any other check |
| nothing | a check whose `start` is `orchestrator: none`, such as L4-04's standalone operation |

A dependency that cannot be brought up from its accepted build MUST make the
dependant's run unsettled, naming the dependency and why; it is never replaced
by a mock, and the dependant's checks are never run against nothing. <!-- wl:id bring-up-failure-unsettled -->

### Integration

When every component layer has ended, the whole hub runs once, sealed: every
accepted component started together from its accepted build, in the services
table's order, brought up as for a suite, and then the checks that span
components.

After the last layer, the engine MUST start every build-accepted component of
the change and every component of the tenant it kept, from their accepted
builds, in the services table's order; each MUST start and answer its `live`
probe, and every check of kind `topology` and every check whose `start` is
`orchestrator: built` or names `with` MUST run against them. A failure here is
recorded on the change as an integration verdict naming the components it
involves, and moves no component's own build verdict. <!-- wl:id whole-hub-integration -->

### A fresh build

A change of kind `fresh` ([`schemas/change`](../schemas/change.md#shape))
builds the whole hub again from the corpus as it now is, in the layers above:
the foundation, then every component of the services table the tenant holds or
its programmes need, and every domain service and published agent it holds.
Nothing generated before is kept or reused as a build: it is a rebuild, not a
repair.

A fresh change MUST replace every file a generation recorded in the tenant's
code directories, an edited one included, and MUST keep everything under
`.weblisk/`, which holds the tenant's keys, data, configuration and identity,
and every file no generation recorded. Its plan MUST list each file it removes,
and the files it keeps that no generation wrote, before anything is removed.
Nothing is removed until the change is applied, and then only as each unit's
layer begins. <!-- wl:id fresh-replaces-generated-keeps-tenant -->

### Incremental

A change rebuilds the units its moved inputs reach and nothing else, and
re-tests what depends on what it rebuilt.

| What moved | Rebuilt | Re-tested |
|---|---|---|
| a declared name the contract holds | the contract package, and every unit that binds the moved name | every component above a rebuilt unit |
| a library blueprint | that library, every library above it that requires it, and every component that requires one of them | every component that needs a rebuilt one running first |
| a component's own blueprint | that component | every component that needs it running first |
| nothing a unit reads | nothing | nothing |

A change MUST rebuild exactly the units its moved inputs reach, through the
rebuild table of [`architecture/generation`](generation.md#deciding-whether-a-file-must-be-rebuilt)
read per unit, plus every unit above them that binds what moved; and every
component that needs a rebuilt unit running first MUST be tested again against
that unit's new accepted build, in the same change. A unit nothing reached
keeps its build and its verdict. <!-- wl:id incremental-by-layer -->

---

## The one conformance suite

One suite, derived from the corpus, decides whether a component conforms. It
replaces every hand-written suite and every verdict a model gives.

A tool MUST NOT hold a conformance test, a check or a verdict rule of its own;
what conformance runs is derived from the corpus as below, and nothing else
counts. <!-- wl:id one-suite -->

### The unit is a criterion

A **criterion** is one checklist item that carries a `wl:check` id, one
requirement marked `wl:id`, or one entry of a `requirements` block, each keyed
`<file path without .md>:<id>`. A requirement a checklist item covers is still
its own criterion: the item's check settles it by naming it in `covers`, and a
declared check may settle it by naming it alone. This is the set
[`checks/acceptance-classes.json`](../checks/acceptance-classes.json) classes,
and the suite derives exactly it, so every criterion the register classes is
one a check can settle and the suite runs. Each has a durable id and a
digest. <!-- wl:id criterion-set-is-the-register -->

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
    - ref: '<full ref of the cited definition: a type, an error, an operation, a check''s data>'
      digest: <that definition's digest, over its value, as schemas/family digests a block entry>
```

A `wl:check <id> covers <ids>` comment is today's spelling of a `verifies`
entry ([`schemas/blocks`](../schemas/blocks.md#definitions)): id, `covers`,
`check` and `assertion`. A criterion is settled in one of two ways, which its
`check` names: by a **declared check** of a kind
[`schemas/blocks`](../schemas/blocks.md) declares, whose data is written in
the corpus, or by a **translated test**, which is the default and is written
`translated`.

### What a component owes

A component is built from one blueprint: the one the services table of
[`schemas/programme`](../schemas/programme.md#the-services-in-the-order-they-are-built)
gives its kind, or, for a kind whose components are `named`
([`schemas/kinds`](../schemas/kinds.md#component-kinds)), the agent's or the
domain's own. That is its **own blueprint**. Every other blueprint some
component kind is built from is **another component's**. A blueprint no
component kind is built from (a protocol, a pattern, a schema, a library
architecture such as `architecture/agent` or `architecture/storage`, a
language or a platform) is a **library blueprint**.

A component MUST be held to the criteria of its own blueprint and of the
library blueprints that blueprint requires, followed through `requires`
from library to library but never into another component's blueprint, and to
no other criterion except one whose check's `applies_to` names its kind or a
selector its kind meets. So the orchestrator, whose blueprint requires
`architecture/admin`, does not owe `architecture/admin`'s criteria: that is
the admin gateway's blueprint. <!-- wl:id component-owes-own-and-libraries -->

`applies_to` works in both directions. On a check in a library blueprint it
narrows: an agent-only check of `protocol/spec` is not owed by the
orchestrator. On a check anywhere it reaches: `architecture/testing`'s L4
checks are owed by every component that registers, whether its blueprint
requires `architecture/testing` or not, and a criterion of another
component's blueprint that a component must meet, such as an administrative
route the orchestrator serves and `architecture/admin` specifies, is owed by
it only through a check whose `applies_to` names it. A component kind that
`runs_with` another is still its own component and owes its own blueprint's
criteria, checked in its host's process.

The language and platform blueprints a component is generated for are
library blueprints it requires, so a Go component owes `languages/go`'s
criteria and a Rust component does not.

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
| **The same streams** | A parity test drives every operation through the CLI (`--json`, under a pseudo-terminal) and through Studio's stream route, against the fake corpus and a sealed fixture tenant, with the same scripted answers to each `question`; a `signature` question is answered in both with a `handoff`, after a signer holding a vector key has made the act. The two streams are equal once invocation ids and instants are normalised | An operation whose `question` one front end cannot answer is reported |
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
- [ ] Every operation in the manifest returns one event stream opened by one `started` and closed by one `finished`, with `seq` rising by one from 1, and every event carries exactly `operation`, `invocation`, `seq`, `at`, `type` and `body` ([Events](#events)) <!-- wl:check streams-bracketed covers one-command-one-stream stream-bracketed envelope-names-fixed -->
- [ ] The manifest lists exactly the catalogue's operations with their executors and events, and each front end exposes it unchanged ([The manifest](#the-manifest), [The operation catalogue](#the-operation-catalogue)) <!-- wl:check manifest-equals-catalogue covers manifest-is-the-catalogue front-ends-render-manifest front-end-parity -->
- [ ] Each front end offers the manifest's operations and `version`, `help` and `commands` and nothing else; the three read only the manifest and the front end's own build; and neither front end offers `doctor`, `update`, `app *`, `marketplace *`, `deps audit` or `gateway policy *` ([Front-end-only commands](#front-end-only-commands)) <!-- wl:check front-end-own-commands covers front-end-only-three undriven-commands-absent -->
- [ ] Driving one operation through the CLI under `--json` and through Studio's stream route, with the same scripted answers, gives streams equal byte for byte once `invocation` and `at` are normalised ([Events](#events)) <!-- wl:check streams-equal covers streams-byte-equal front-end-parity -->
- [ ] An operation needing a passphrase emits a `question` and waits; with no answer it ends refused naming the question; and the answer appears in no event, record, transcript or log ([Questions](#questions)) <!-- wl:check questions-asked-and-kept-secret covers question-is-the-only-ask secret-answers-never-recorded unanswered-is-refused -->
- [ ] Given the signer fixture `handoff-answer-wrong-subject`, a `handoff` whose record is another subject's ends the operation refused naming the question, as does one whose record was on the subject before the question, is another identity's, or is not signed; and a correct `handoff` ends `finished` with the same `records` in Studio's stream as in the CLI's ([Questions](#questions)) <!-- wl:check handoff-answer-verified covers signature-handoff-answer front-end-parity -->
- [ ] A front end shows a verdict, threshold or list only as an operation's events carry it, and the neutrality check over its source reports one computed in it ([The parts, and the line between them](#the-parts-and-the-line-between-them)) <!-- wl:check front-end-computes-nothing covers front-end-decides-nothing -->
- [ ] `change apply` emits a `step` event as each of resolve, plan, translate, generate, build, repair, accept and record begins and ends, in that order ([The build steps](#the-build-steps)) <!-- wl:check steps-ordered covers steps-in-order -->
- [ ] Given a corpus whose services table, `component_kinds` and `requires` are changed, a change's layers change with them and with nothing else; a `requires` cycle among one role's blueprints is refused before any model call, naming the cycle; layer 0 holds the contract package and then the libraries by `requires`, then the components by what each needs running first, and no unit is generated before, or sits below, a unit it requires, needs or depends on ([Layers](#layers)) <!-- wl:check layers-computed-from-corpus covers layers-from-corpus layer-order -->
- [ ] `change plan` lists each layer with its units, and each component unit with what it needs running first and what it requires; every `step` event of an apply names its layer and unit ([Layers](#layers)) <!-- wl:check layers-in-plan-and-events covers layers-shown -->
- [ ] In an apply's record, every generate action of a layer precedes that layer's compile, and the compile precedes every check and translated test of the layer; a layer that does not compile is recorded as a build verdict with no check counted; and no command compiling more than one layer, and no route wiring of a component, runs before that component's layer and those below it are complete ([Within a layer](#within-a-layer)) <!-- wl:check layer-generated-compiled-tested covers generate-compile-then-test compile-failure-is-build no-cross-layer-compile -->
- [ ] With a dependency refused, every unit that depends on it, directly or through another, is `skipped` naming what it waited for and that dependency's outcome, and none of them is generated, compiled or tested ([Gating](#gating)) <!-- wl:check refused-dependency-skips-dependants covers dependant-skipped -->
- [ ] A change generates the contract package once, first in layer 0, holding the declared names of every component the tenant holds after it; a component plan or a library plan placing a file in the contract package, or a component plan placing one in a library package, is refused ([Shared code](#shared-code)) <!-- wl:check contract-and-libraries-once covers contract-once-per-change library-unit-once -->
- [ ] A dependant's suite starts what it needs running first from their accepted builds, in the services table's order, as `architecture/testing` brings them up, and no mock or stub in their place; a dependency that cannot be brought up leaves the dependant's run unsettled, naming it ([The test environment](#the-test-environment)) <!-- wl:check suite-against-accepted-builds covers tested-against-accepted bring-up-failure-unsettled -->
- [ ] After the last layer the whole hub is started from accepted builds in order, each answers its `live` probe, and every `topology` check and every check starting `orchestrator: built` or `with` runs against it; a failure there is the change's integration verdict and moves no component's own ([Integration](#integration)) <!-- wl:check whole-hub-run-after-last-layer covers whole-hub-integration -->
- [ ] A `fresh` change plans every component in layers from the corpus, lists every recorded file it removes and every unrecorded file it keeps, removes nothing under `.weblisk/` and no file no generation wrote, and removes a unit's files only as that unit's layer begins ([A fresh build](#a-fresh-build)) <!-- wl:check fresh-change-replaces-generated-only covers fresh-replaces-generated-keeps-tenant -->
- [ ] A change in which one library blueprint moved rebuilds that library, the libraries above it that require it and the components that require one of them, re-tests every component that needs a rebuilt one running first against its new accepted build, and rebuilds nothing else ([Incremental](#incremental)) <!-- wl:check incremental-rebuilds-reached-layers covers incremental-by-layer -->
- [ ] With `files_in_flight` N, a unit's generation and one repair round never have more than N model calls in flight; the files, the bank and the record are the same as with N = 1 under the same answers; and a file of a level is given nothing another file of its level returned ([Concurrency](#concurrency)) <!-- wl:check files-in-flight-bounded covers files-in-flight -->
- [ ] A build whose module manifest and unsatisfied imports are what its last successful prepare left does not run prepare again; one that imports a package neither the module nor the standard library holds, or whose manifest moved, does ([Concurrency](#concurrency)) <!-- wl:check prepare-only-when-moved covers prepare-when-moved -->
- [ ] A step whose corpus declaration is missing is recorded as guessed, naming what it lacked, and no engine default is used in its place ([The build steps](#the-build-steps)) <!-- wl:check guessed-step-recorded covers guessed-is-reported -->
- [ ] A model's reading never moves a verdict; a conflict it reports is recorded as a corpus finding and settles nothing; an answer writing a test path, a plan-fixed name or a file outside the repair set is refused with its reason ([What the model may not do](#what-the-model-may-not-do)) <!-- wl:check model-bounded covers model-reads-are-advice conflict-is-proposed model-output-bounded -->
- [ ] Every sentence of every model prompt is an instruction file's folded text or a labelled declared input, and the action records each instruction's ref, version and digest ([Instructions](#instructions)) <!-- wl:check prompts-are-corpus-text covers no-engine-sentences instruction-revision-recorded -->
- [ ] Conformance runs only the declared checks, the translated tests and the published vectors, and no tool holds a test, check or verdict rule of its own ([The one conformance suite](#the-one-conformance-suite)) <!-- wl:check suite-is-derived covers one-suite -->
- [ ] A criterion keeps its id when its text changes; its digest moves when its text or any definition it cites changes, and not otherwise ([The unit is a criterion](#the-unit-is-a-criterion)) <!-- wl:check criterion-id-and-digest covers criterion-id-frozen criterion-digest-covers-citations -->
- [ ] The suite's criteria are exactly the register's: every checklist item carrying a `wl:check` id, every `wl:id` requirement and every `requirements` entry, a requirement an item covers among them, so a check covering a requirement alone is run ([The unit is a criterion](#the-unit-is-a-criterion)) <!-- wl:check criteria-are-the-register covers criterion-set-is-the-register -->
- [ ] The suite holds a component to its own blueprint's criteria and those of the library blueprints it requires, never through another component's blueprint, and to another criterion only through a check whose `applies_to` names its kind: the orchestrator is not held to `architecture/admin`'s, and every registering component is held to `architecture/testing`'s L4 checks ([What a component owes](#what-a-component-owes)) <!-- wl:check component-owes covers component-owes-own-and-libraries -->
- [ ] A translated test counts only with all four conditions shown on the record: the translate action precedes every generate action and was given no implementation, the test failed against the stub, no generate or repair action wrote it, and its verdict is the test command's ([What makes a translated test count](#what-makes-a-translated-test-count)) <!-- wl:check translated-test-conditions covers translated-test-counts translated-apart fails-on-nothing tests-frozen verdict-is-the-runs -->
- [ ] In production, an S or J criterion settled only by a translated test is unsettled ([What makes a translated test count](#what-makes-a-translated-test-count)) <!-- wl:check production-needs-declared covers production-s-j-declared -->
- [ ] A check with no `live` declaration is not run against a live tenant; a live S check failing after acceptance withholds the affected operations, and a live J check failing marks the acceptance contradicted ([Build time and run time](#build-time-and-run-time)) <!-- wl:check live-checks covers live-only-safe live-failure-after-acceptance -->
- [ ] The record is written in the tenant and read by front ends through the tenant's routes, and each model action cites a transcript the tenant holds ([The record](#the-record)) <!-- wl:check record-held-by-tenant covers record-in-tenant transcripts-kept -->
- [ ] An action whose step, instruction digests and input digests equal a completed action's is not run again and records the reuse; an instruction revision alone re-runs nothing ([How the record makes builds incremental](#how-the-record-makes-builds-incremental)) <!-- wl:check actions-reused covers action-reused older-instruction-kept -->
- [ ] A test is translated again only when its criterion's digest moves, a file is rebuilt only as the rebuild table says, a carried verdict names the run it came from, and every build starts from the record before it ([How the record makes builds incremental](#how-the-record-makes-builds-incremental)) <!-- wl:check incremental-from-record covers test-follows-criterion-digest rebuild-by-table verdict-carried never-from-scratch -->
