# Schema: Run Statement

What one generation run read and wrote, and what each output traces to, in one
immutable file the tenant holds.

A run statement is the declared source of every edge a build creates in the
fabric ([`architecture/fabric`](../architecture/fabric.md#declared-at-write-time),
`declared-at-write-time`). It is written when the files are written, so it
exists on the first build, offline, before any fabric runs; the fabric's
`generation-statements` producer ingests it later. How a run is planned and
gated is [`architecture/generation`](../architecture/generation.md#the-run-statement)'s;
this file says only what the statement holds and how it is read.

---

## Where it lives

One file per run, at `provenance/runs/<run id>.json` in the tenant repository,
written once and never edited. A run that is repeated is a new run with a new
statement. Nothing else records run facts: the fabric's ledger names a run by
its id and statement digest (`RunCitation`), and the build lock holds resolved
versions and no roots.

## Shape

The statement is an [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md)
whose predicate is [SLSA Provenance v1](https://slsa.dev/spec/v1.0/provenance),
so a general tool reads it without knowing Weblisk. What Weblisk adds sits in
the places those specifications leave for a build type's own parameters and for
annotations on a resource. The statement's type is `RunStatement`, declared in
the `types` block below, and its build type is that type's full ref,
`type://weblisk/schemas/run-statement:RunStatement`.

Each subject carries the record [`architecture/generation`](../architecture/generation.md#deciding-whether-a-file-must-be-rebuilt)
requires for every file it writes — its plan entry, its digest as written, the
digest of each blueprint it was generated from, and what it is answerable for —
so the rebuild decision reads its per-file inputs here and nowhere else.

```yaml
run_statement:
  _type: https://in-toto.io/Statement/v1
  predicateType: https://slsa.dev/provenance/v1
  subject:                         # one per output file the run wrote
    - name: <path in the tenant repository>
      digest: {sha256: <hex>}
      annotations:
        roots: [<ref>]             # the roots this output traces to: which of the
                                   # run's requested roots it was generated for
        plan_entry:                # the plan entry that produced it; its path is `name`
          purpose: <text>
          declares: [<symbol>]
          serves: [<operation ref>]
        implements: [<requirement ref>]  # from its plan entry
        generated_from: [<requirement, mapping rule or control ref>]
        blueprints:                # each blueprint this file was generated from,
          - uri: <full ref>        # at the digest the run read it
            digest: {sha256: <hex>}
        answerable_for:            # what a change must reach to make it a rebuild
          bindings: [<type or operation ref it binds>]
          assertions: [<check ref>]
  predicate:
    buildDefinition:
      buildType: type://weblisk/schemas/run-statement:RunStatement
      externalParameters:
        component: <component kind>
        roots: [<ref>]             # what the run was asked to build from
        plan_digest: sha256:<hex>
      internalParameters:
        tool: {name: weblisk, version: <cli version>}
        backend: <the backend the run used>
        model: <the id the backend reported at run time, or unreported>
        prompt_digests: [sha256:<hex>]
        on_behalf_of: <identity id of the operator who asked for the run>
        result: complete | failed | stopped   # how the run ended; see A run that did not complete
        verdict:                   # a complete run's verification; see The verdict a run ends with
          conformance: established | accepted | refuted | not-run
          classes:                 # per class, as the gate counted the criteria; a class it did not count is absent
            S: {met: <count>, unmet: <count>, unsettled: <count>}   # and J, B, E, F likewise
          assertions: <count>      # the checklist's assertions, and how each ended
          satisfied: <count>
          unmet: <count>
          unverifiable: <count>
          unanswered: <count>
          conflicts: <count>       # requirements read as contradicting the corpus
        actions: [<action>]        # every thing a step did, in the order done; see Actions
        criteria: [<criterion>]    # every criterion the run owed; see Criteria
      resolvedDependencies:        # every blueprint and mapping rule read
        - uri: <full ref>
          digest: {sha256: <hex>}
          annotations: {version: <resolved version>}
    runDetails:
      builder: {id: <full ref of the tenant's generation service>}
      metadata:
        invocationId: <run id>
        startedOn: <RFC 3339>
        finishedOn: <RFC 3339>
      byproducts:                  # one per model action's transcript; see Actions
        - name: provenance/transcripts/<run id>/<action id>.json
          digest: {sha256: <hex>}
```

```yaml
types:
  RunStatement:
    description: One generation run's statement, an in-toto Statement v1 with a
      SLSA Provenance v1 predicate, in the shape above. Its fields are those
      specifications' own; this file adds only the subject annotations and the
      build parameters the shape shows
    fields:
      _type:
        type: string
        description: https://in-toto.io/Statement/v1
      predicateType:
        type: string
        description: https://slsa.dev/provenance/v1
      subject:
        type: list
        description: One entry per output file the run wrote, each with its
          name, digest and the annotations the shape shows
      predicate:
        type: object
        description: The SLSA Provenance v1 predicate, whose buildType is this
          type's full ref
```

## Rules

1. **`model` is what the backend reported, never what was configured.** It is
   the model id the backend returned for this run, at run time. A configured
   name is a request, and the backend may have served something else under it.
   A backend that reports none gives `model: unreported`, and what that does to
   caching is [`architecture/generation`](../architecture/generation.md#the-run-statement)'s
   to say.
2. **`roots` is per output.** A run of several roots records, on each subject,
   which of them that file was generated for. `change plan --upgrade` takes its
   roots from the latest statement of each component; the lock never holds them.
3. **`implements` is per planned file**, copied from the plan entry that
   produced it ([`architecture/generation`](../architecture/generation.md#what-a-plan-declares)).
   No marker is written into the generated code. Verification confirms each
   claim through the requirement's criterion, settled by its declared check or
   its translated test ([Criteria](#criteria)), never by a test the generator
   wrote; where the language has no symbol extractor the confirmation is
   file-level and says so.
4. **Every digest is written as `patterns/content-identity` spells it**:
   `sha256:<hex>` as one string, `{sha256: <hex>}` where in-toto's digest set is
   the field.
5. **Every ref is a full ref** in the grammar of [`names.md`](names.md), because
   a statement is read without the file that named it.
6. **The file is always a DSSE envelope, stored as RFC 8785 canonical bytes**
   (Signing, below), signed or not, so the statement digest an entry cites is
   the SHA-256 of the file as stored, recomputable with `sha256sum`, and does
   not change form when signing begins.
7. **A subject's `blueprints` are a subset of `resolvedDependencies`, at the
   same digests.** The run's list is everything it read; a subject's is what
   that file was made from.
8. **`result` is `complete`, `failed` or `stopped`, and only a `complete` run
   is read as what its component was built from**
   ([A run that did not complete](#a-run-that-did-not-complete)).
9. **A complete run carries its `verdict`, and a run that did not complete
   carries none** ([The verdict a run ends with](#the-verdict-a-run-ends-with)).
10. **A result written by anything but the run itself carries
   `established_by`**, and only `weblisk build verify` writes one
   ([A run that did not complete](#a-run-that-did-not-complete)).

## A run that did not complete

A run ends `complete` when it generated every file its plan named and its
verification gate returned a verdict; `failed` when it ended on a fault; and
`stopped` when something outside it ended it, a person, a limit the model
backend reported, or a host going down. **Only a `complete` run is read as
what its component was built from.**

- The statement is written when the run reaches one of these, with its
  `result`, and `finishedOn` is when it did. A run killed before it could write
  one may leave a record of having started, written wherever its
  implementation keeps one; any record of a run with no `result` is read as
  `stopped`.
- **What a component was built from is read from its latest run, and only when
  that run is `complete`.** When the latest run is not, the component's
  standing is unassessed ([`schemas/change`](change.md#unassessed-is-not-a-verdict)),
  naming the run and its result. It is never read from that run, whose inputs
  the component only partly holds, and never from the complete run before it,
  whose files the later run has partly replaced. A run that stopped and is
  read as the inputs makes a component look nearly current exactly when it is
  least so.
- **A run records its accepted plan before it generates a file**, in its
  record of having started: every entry, written or not, the `plan_digest`
  its statement carries, the blueprints the plan was made from at the digests
  read, and, as it banks each file, the cache entry it banked it under. A
  subject carries the plan entry of a file the run wrote, so a statement alone
  cannot say what a run that stopped at file six of forty-nine had still to
  write.
- **A resume is generated from the plan of the run it resumes**, and every
  file that run banked is reused from the entry it was banked under
  ([`schemas/change`](change.md#verdicts), `incomplete`). The model is never
  asked to plan a resume. The plan is made again only when a blueprint it was
  made from moved, was added or is no longer read, at the digests recorded, and
  the run names which. The instructions the model was given are not among
  those inputs: an instruction revised since has not changed what the
  tenant's blueprints require, and the plan is kept, marked made under an
  older instruction ([`architecture/engine`](../architecture/engine.md#how-the-record-makes-builds-incremental)). A record from before plans were
  recorded is resumed from the banked plan whose entries match every file its
  run recorded, by path, purpose and declarations, and from the banked files
  whose digests it recorded; where none matches, the run says the plan is
  missing and makes one.
- A subject of a run that did not complete is still a true record of the file
  it names: that file was written, from those blueprints, at that digest. The
  rebuild decision ([`architecture/generation`](../architecture/generation.md#deciding-whether-a-file-must-be-rebuilt))
  reads it for that file, so a resumed run keeps what the stopped one wrote and
  does not refuse it as edited.
- **A record from before `result` existed can be established, never
  asserted.** `weblisk build verify <component>` ([`architecture/cli`](../architecture/cli.md#until-a-tenant-runs-a-change-service))
  checks that the tree holds every file the record names at the digest it
  recorded, reads the record's inputs again at the commits it names, builds the
  tree and runs its conformance. Every test that ran passed, with none failed
  or unreachable, establishes `complete`; a failure, or a tree that does not
  build or run, establishes `failed`; anything less establishes nothing and
  the record still reads as `stopped`. What it writes carries `established_by`
  beside it: the verify run's id, when, the command, the commits read, its
  verdict, the files it found edited and the files no generation wrote. A
  result established this way is never read as one its run wrote.

`result` sits in `internalParameters` because SLSA Provenance has no field for
how a build ended, and that block is the place it leaves to a build type.

## The verdict a run ends with

A complete run's statement carries the verdict its verification gate
([`architecture/generation`](../architecture/generation.md#the-verification-gate))
returned on the tree the run ended on, with the counts it was reached from:

| `conformance` | When |
|---|---|
| `established` | the gate verified the artifact: every criterion owed settled as met |
| `accepted` | build acceptance holds ([`architecture/generation`](../architecture/generation.md#build-acceptance)): it builds and starts, no conformance test counts against it, and every S and J criterion is met; gaps of class B, E or F are recorded |
| `refuted` | the gate settled against it: a conformance test failing, an S, J or unclassed criterion not met, or a build that does not build or start |
| `not-run` | the run completed and the gate reached no verdict: inconclusive, or not reached |

The counts are the gate's, as it counted them; one the gate did not count is
absent, never `0`. `classes` counts the run's criteria by their class
([`architecture/generation`](../architecture/generation.md#how-a-criterion-gets-its-class)):
`met` those whose verdict is `pass`, `unmet` those whose verdict is `fail` or
`error`, `unsettled` those whose verdict is `not-run`. Each gap is on its
criterion ([Criteria](#criteria)), never repeated on the verdict. An
`accepted` verdict is never read or shown as `established`.

**A component whose latest run is not complete with conformance `established`
or `accepted` is never kept as built**: an adoption's plan names it
`regenerate` or `repair` ([`schemas/change`](change.md#verdicts)), so a build
that failed is never mistaken for a service the tenant has. One whose latest
run is `accepted` is kept, and planned `repair`, because `gaps`, so adopting is
always the act that closes them.

## Signing

Every statement is stored in a [DSSE](https://github.com/secure-systems-lab/dsse)
envelope: `payloadType` `application/vnd.in-toto+json`, `payload` the base64
of the statement's RFC 8785 bytes, and `signatures`. A signature is ML-DSA-65
([`protocol/identity`](../protocol/identity.md)) over DSSE's pre-authentication
encoding, `PAE(payloadType, payload)` with the payload's decoded bytes — never
over the envelope or the statement's JSON as serialised — made by the tenant's
`generation` service credential, admitted once by a person, with `keyid` its
identity id. The statement records `on_behalf_of` the operator.

That credential is part of the credential layer (identity, credential,
grant), which does not exist yet. **Until it does, the envelope's `signatures`
is empty**, the statement is read as unsigned, and the fabric records each entry's run citation
with `signed: false`. A person's identity key never signs a statement in the
credential's place; that would make a person the author of every file a model
wrote.

## Reading one

- A statement whose `_type` or `predicateType` is not the one above is not a
  run statement, and is reported, not guessed at.
- A subject whose file is absent or whose digest differs is reported as such:
  the statement says what was written, and the file says what is there now. An
  edited output is refused for regeneration
  ([`architecture/generation`](../architecture/generation.md#deciding-whether-a-file-must-be-rebuilt)).
- A statement is never rewritten to correct it. A correction is a new run.

## Actions

One entry per thing a step of [`architecture/engine`](../architecture/engine.md#the-build-steps)
did, deterministic or model, in the order the run did them. An action is the
unit the engine reuses: one whose step, instruction digests and input digests
equal a completed action's is not run again
([`architecture/engine`](../architecture/engine.md#how-the-record-makes-builds-incremental)).

```yaml
action:
  id: <action id>                  # unique in the run: lowercase letters, digits and hyphens
  step: <step id>                  # one architecture/engine declares
  kind: deterministic | model
  instructions:                    # model actions only, in the order the prompt carried them
    - {ref: <full ref of instructions/<id>>, version: <its version>, digest: sha256:<hex>}
  inputs:                          # every input the action read, by name
    - {name: <input name>, digest: sha256:<hex>}
  outputs:                         # every output it produced, by name or tenant path
    - {name: <name or path>, digest: sha256:<hex>}
  criterion: <criterion ref>       # a translate action: the criterion it translated
  model: <the id the backend reported, or unreported>   # model actions only
  transcript: sha256:<hex>         # a model action that called a model: its byproduct's digest
  reused_from: {run: <run id>, action: <action id>}     # an action not run again
  result: done | refused | failed
  started: <timestamp>
  finished: <timestamp>
```

- **An input's digest** is the SHA-256 of what the action was given under that
  name: a file's bytes, a block's value as
  [`schemas/family`](family.md#the-projection) digests it, or the RFC 8785
  bytes of a structured input. Two actions given the same thing under the same
  name record the same digest, which is what makes reuse a lookup.
- **An instruction's digest** is the SHA-256 of the instruction file's bytes as
  read, at the version recorded ([`schemas/instruction`](instruction.md#versions-and-digests)).
- **The transcript** is the account of how a model action was done, kept in
  the tenant (ENGINE_PLAN decision 10): a JSON file in the tenant repository
  at `provenance/transcripts/<run id>/<action id>.json`, holding the prompt as
  sent and the answer as received, each part labelled by the instruction or
  input it came from, and the model the backend reported. It is a byproduct of
  the run, so the run's `byproducts` name it with its digest, and the action
  cites that digest. The answer to a `question` of kind `passphrase`,
  `secret` or `signature` never appears in it
  ([`architecture/engine`](../architecture/engine.md#questions)).
- **A reused action** carries `reused_from`, naming the completed action whose
  outputs it took, and the same step, instruction digests, input digests and
  outputs. It made no model call, so it has no transcript of its own.

## Criteria

One entry per criterion the run owed: every checklist item and every
uncovered requirement of the blueprints the run built from
([`architecture/engine`](../architecture/engine.md#the-unit-is-a-criterion)).

```yaml
criterion:
  id: <full ref of the requirement or check>
  digest: sha256:<hex>             # over its text and the definitions it cites
  class: S | J | B | E | F
  class_by: <the rule, and the ref, that gave the class>
  settled_by: declared | vector | translated | unsettled
  check: <full ref of the declared check or vector>      # declared and vector only
  unsettled:                       # unsettled only: why no test or check counts for it
    why: untestable | model-finding | unresolved-cite | no-check
    reported_by: {run: <run id>, action: <action id>}     # untestable and model-finding: the action whose answer was the finding
    finding: <the finding's text, as the model gave it>  # untestable and model-finding
    cite: <the ref, as the criterion writes it, that resolves to nothing>   # unresolved-cite
  tests:                           # translated only
    - path: <tenant path>
      digest: sha256:<hex>
      translated_by: {run: <run id>, action: <action id>}
      criterion_digest: sha256:<hex>   # the criterion's digest the test was translated under
      instruction_current: <bool>      # false: translated under an older instruction
      stub: failed | passed | not-run  # its run against the stub of the plan's declarations
      promoted: <full ref of the declared check that replaced it>
  reach:                           # what the criterion's tests or check reach
    files: [<tenant path>]
    symbols: [<symbol>]
    operations: [<operation ref>]
    component: <bool>              # true: a black-box test, which reaches the whole component
  verdict:
    result: pass | fail | error | not-run
    environment: <environment the result was reached in>
    reason: <the test command's or the executor's own reason>
    carried_from: <run id>         # a verdict carried forward, and the run it came from
  gap:                             # present when the criterion is not met
    result: unmet | unsettled | failed
    reason: <text>
    premise: <the premise, and the test that settles it, of an IF requirement>
    reaches: [<component ref>]     # components in this tenant that bind what it governs
  readings:                        # a model's readings of the criterion: advice, never counted
    - action: <action id>          # the accept action that read it
      says: met | unmet | unsure   # the reading's first word, as instructions/advise asks for it
      reason: <the model's reasons, as it gave them>
```

- **The digest** is [`architecture/engine`](../architecture/engine.md#the-unit-is-a-criterion)'s:
  the SHA-256 of the RFC 8785 bytes of `{text, cites}`, where `text` is the
  criterion's text with its id marker removed and each run of whitespace one
  space, and `cites` lists each definition it cites by full ref and digest,
  sorted by ref. Its worked values are
  [`vectors/run-statement/criterion-digest.json`](../vectors/run-statement/criterion-digest.json).
- **A test counts only when its record shows the four conditions**
  ([`architecture/engine`](../architecture/engine.md#what-makes-a-translated-test-count)):
  its `translated_by` is a translate action given no output of a generate or
  repair action, and every translate action of the run comes before its first
  generate action; its `stub` is `failed`; no generate or repair action wrote
  its path; and its verdict is the test command's.
- **Unsettled** is the form of a criterion no test or check counts for: the
  translate step reported it untestable, a model reported a finding against
  it, it cites a definition that resolves to nothing, or no check is declared
  where one is required (an S or J criterion in production,
  [`architecture/engine`](../architecture/engine.md#what-makes-a-translated-test-count)).
  It has no tests and no check, its verdict is `not-run`, and its gap's result
  is `unsettled`, so it is unmet for acceptance and never read as passed.
- **A reading** is what a model said of the criterion at the accept step,
  recorded in full whichever way it went, so a shadow run (ENGINE_PLAN, phase
  E2) keeps the model's reading beside the suite's verdict, a reading that
  says `met` included. A reading never moves the verdict or the gap
  ([`architecture/engine`](../architecture/engine.md#what-the-model-may-not-do),
  `model-reads-are-advice`): delete every reading from a statement and its
  verdicts and gaps are unchanged. It is the gap's advice that
  [`ACCEPTANCE_PLAN.md`](../ACCEPTANCE_PLAN.md#on-the-run-statement) names,
  kept on the criterion so that a reading of a criterion that has no gap has a
  home too.
- **A gap's fields** are the ones [`ACCEPTANCE_PLAN.md`](../ACCEPTANCE_PLAN.md#on-the-run-statement)
  gives a gap. The check, class, covers, files and reach it lists are the
  criterion's own fields above, so they are not repeated inside `gap`.

## Rules for actions and criteria

Each rule has an id; the [vectors](../vectors/run-statement/README.md) cite
them, and [`checks/run-statement-vectors.py`](../checks/run-statement-vectors.py)
reads this block and nothing else.

```yaml
rules:
  - id: action-id
    rule: every action has an id, unique in the run, of lowercase letters, digits and hyphens
  - id: action-step
    rule: every action's step is a step architecture/engine declares
  - id: action-model
    rule: an action of kind model is of a step whose model is called, and has instructions and model; one of kind deterministic has neither, nor a transcript
  - id: action-digests
    rule: every input, output and instruction digest is written sha256:<hex>, and every instruction names ref, version and digest
  - id: action-transcript
    rule: a model action that was not reused has a transcript, and its digest is the digest of one of the run's byproducts
  - id: action-reuse
    rule: an action with reused_from has no transcript; when reused_from names an action of the same run, that action is earlier and has the same step, instruction digests, input digests and outputs
  - id: criterion-id
    rule: every criterion has an id, unique in the run, and a digest written sha256:<hex>
  - id: criterion-settled
    rule: settled_by translated has tests and no check; declared and vector have a check and no tests; unsettled has neither, and names why
  - id: unsettled-not-passed
    rule: a criterion settled_by unsettled has verdict not-run and a gap whose result is unsettled
  - id: reading-action
    rule: every reading names a model action of the run whose step is accept, and says met, unmet or unsure
  - id: test-translated-by
    rule: every test's translated_by names a translate action, and when that action is of this run, its criterion is this criterion
  - id: translate-first
    rule: no translate action of the run comes after its first generate action
  - id: translate-apart
    rule: no translate action's inputs carry the digest of an output of a generate or repair action of the run
  - id: test-not-written
    rule: no generate or repair action's outputs name the path of a test
  - id: test-counts
    rule: a criterion settled by translated tests has verdict pass only when each of its tests has stub failed
  - id: verdict-result
    rule: every verdict's result is pass, fail, error or not-run; a gap's result is unmet, unsettled or failed
  - id: verdict-classes
    rule: a run's verdict conformance is established, accepted, refuted or not-run; where it carries classes, each is S, J, B, E or F and counts that class's criteria, met those whose verdict is pass, unmet fail or error, unsettled not-run; an accepted verdict counts no S or J criterion unmet or unsettled, and an established one none of any class
```
