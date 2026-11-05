# Schema: Change

One act of changing what a tenant is built from: adopting a blueprint,
upgrading one, removing one, or reverting an earlier change. A change is
planned, approved by a person, applied in the tenant and verified, and it is
the one record of each of those steps.

How the plan is resolved — the two closures, version selection, the conflicts
C1 to C8 and `on_change` — is [`architecture/generation`](../architecture/generation.md#resolving-a-request-of-many-roots)'s.
How a plan reaches the files it names is [`architecture/fabric`](../architecture/fabric.md)'s
reach. Who may approve is [`architecture/cli`](../architecture/cli.md#who-may-approve-a-change)'s.
The routes a client calls are [`architecture/admin`](../architecture/admin.md#changes-and-builds)'s.
This file says what a change holds and when one is well formed.

---

## Where it lives

One file per change, at `.weblisk/changes/<change id>.json` in the tenant
repository, written by the tenant's change service and by nothing else, or,
until a tenant runs one, by the CLI on the tenant's own host
([Executors](#executors)). A client never opens it: Studio and a remote CLI
read a change through the tenant's API and render the same JSON. A change is never reopened once it has
ended: a revert is a new change of kind `revert`, and a plan made stale by a
moved corpus, lock or ledger is superseded by a new change.

## Executors

Every command declares where it runs (D24). The vocabulary is closed:

| Executor | Runs | Used by |
|---|---|---|
| `local` | outside any tenant, on files in a repository the person holds | any client |
| `tenant-api` | in the tenant, reached through its admin gateway | a client acting on a tenant; the only executor Studio uses for one |
| `cli-in-tenant` | the CLI on the tenant's own host | an operator at that host, and the tenant's change service. Never Studio |

Each change verb's executor, and so where the act happens:

| Verb | Executor | What the tenant does |
|---|---|---|
| `change plan` | `tenant-api` | the change service runs the engine it hosts to resolve and plan, and writes the change |
| `change list`, `change show` | `tenant-api` | reads changes |
| `change approve`, `change reject` | `tenant-api` | records the person's signed decision at the change service, the owner of the request, as the change's `approval` or `rejection` |
| `change apply` | `tenant-api` | the change service runs the engine in the tenant, with the tenant's model (D26), and restarts what it built |
| `change verify` | `tenant-api` | the change service runs the suite and records the result |
| `change revert` | `tenant-api` | plans a new change of kind `revert` |
| `change stop` | `tenant-api` | ends the build run under way `stopped`; the change keeps its state |

Each route, who may call it and the decision's signed statement are
[`architecture/change-service`](../architecture/change-service.md)'s.

Until a tenant runs a change service, four of these verbs run as
`cli-in-tenant` instead, and an apply stands on the operator's word where an
approval would be: which verbs, and how, is
[`architecture/cli`](../architecture/cli.md#until-a-tenant-runs-a-change-service)'s.
The file they write is this one.

## Shape

```yaml
change:
  id: <32 hex>
  kind: adopt | upgrade | remove | revert
  request: [<ref or citation>]     # what was asked for, as asked
  reverts: <change id>             # kind revert only
  requested_by: <identity id>      # the operator who asked
  requested_at: <instant>
  strict: <bool>                   # C2 refuses when true, as it does for Studio
  state: planned | approved | rejected | applied | verified | failed | superseded
  base:                            # what the plan read; apply refuses if any moved
    corpus: <full commit>          # the first pin's revision
    lock: sha256:<hex>             # digest of .weblisk/build.lock as read
    lock_of: <text>                # present only while the tenant writes no build.lock:
                                   # what lock is a digest of instead
    fabric_tip: sha256:<hex> | unreported
    pins:                          # every corpus source the plan read, in resolution order
      - kind: project | custom | core   # architecture/cli, Where blueprints come from
        origin: <the repository a clone is of, or the directory read in place>
        revision: <full commit>
  shown_roots: [<ref>]             # the roots the plan computed, for display
  resolution:                      # phase R: deterministic, no model call
    build_set:
      - component: <component ref>
        added_by: <component ref>  # present when a dependency pulled it in
    lock_diff:
      - {ref: <ref>, from: <version or absent>, to: <version or absent>}
    conflicts:
      found: [<conflict>]          # between the roots of this plan
      introduced: [<conflict>]     # present at the target, absent at the pinned revision
      cleared: [<conflict>]        # present at the pinned revision, absent at the target
  plan:                            # one entry per unit or output reached
    - unit: <ref>                  # a component, blueprint or mapping rule; or
      output: <path>               # a file in the tenant repository
      phase: R | F                 # F: the model's proposed files
      verdict: <verdict>
      because: <reason>
      implements: [<requirement ref>]
      detail: <text>
  unassessed:                      # components whose standing cannot be said
    - unit: <component ref>
      detail: <why — no recorded inputs, its latest run did not complete, a source unreachable>
  approver_position: <position id> # a knowledge change: the position its spec names (schemas/position), set by the plan
  approval:                        # present from state approved on
    by: <identity id>
    position: <position id>        # equals approver_position, which the approver holds
    signature: <base64url ML-DSA-65 over the weblisk/change-decision/v1 statement>
    plan_digest: sha256:<hex>
    at: <instant>                  # the statement's signed_at
    attestation: <Attestation>     # the sign-records attestation the signature verifies under
    development: <bool>            # the tenant's hub.environment is development (schemas/config)
  rejection:                       # state rejected only: the person's signed refusal
    by: <identity id>
    reason: <text>
    signature: <base64url ML-DSA-65 over the weblisk/change-decision/v1 statement>
    plan_digest: sha256:<hex>
    at: <instant>
    attestation: <Attestation>
  without_approval: true           # applied with no approval, on the operator's word
  applied_run: <run id>            # the run statement apply wrote
  outcomes:                        # one per component apply built or tried to, in build order
    - component: <component ref>
      result: built | failed | refused | skipped
      verdict:                     # the build's own, never the plan's
        outcome: verified | failed | inconclusive | unchecked
        detail: <text>
  config_edits:                    # a backend driver change the plan was made as though done
    - path: <schemas/config path, e.g. content.backends[local].driver>
      kind: <service section>
      backend: <backend name>
      from: <driver>
      to: <driver>
      blueprint: <the opt-in blueprint that declares to among its drivers>
      applied: true                # set once apply wrote it, after that component built
  replace_edited:                  # generated or unowned files the operator named, each with why
    - component: <component ref>
      path: <tenant path>
      why: <the operator's reason, as given>
      digest: sha256:<hex>         # the bytes the plan saw; apply refuses if they moved
      unowned: true                # no generation wrote it: apply removes it before the build
  config_written: [<section>]      # each .weblisk/config.yaml section apply wrote
  verify: {result: pass | fail | repair, run: <run id>}
```

A conflict is `{code: C1..C8, refs: [<ref>], detail: <text>}`, with the codes
[`architecture/generation`](../architecture/generation.md#resolving-a-request-of-many-roots)
names.

### What a plan is bound to

**`pins` is every source the plan read, each at a full commit**, in the order
[`architecture/cli`](../architecture/cli.md#where-blueprints-come-from)
resolves them, and `corpus` is the first one's revision. A short commit names
nothing once the repository grows, and a tree with uncommitted changes names
nothing at all, so a plan that read one is not written.

**`apply` reads the corpus at `base.pins`, never at a source's head or its
latest cached copy**, and re-derives the plan's decision from what it reads
there; a decision that differs is refused. The person approved, or the
operator vouched for, what the plan read. A source that moved between plan and
apply would build something nobody looked at, under a change that says they did.

**`lock_of` exists because the lock does not yet.** Until the tenant's change
service writes `.weblisk/build.lock` ([`schemas/build-lock`](build-lock.md)),
`lock` is a digest of something else that moves when a build moves, today each
component's recorded inputs, and `lock_of` says what. Absent, `lock` is the
build lock's digest. Either way a moved digest makes the change stale.

### Unassessed is not a verdict

A component whose standing cannot be said is listed in `unassessed`, with why,
and is never a plan entry: it has no recorded inputs, the latest run that built
it did not complete ([`schemas/run-statement`](run-statement.md#a-run-that-did-not-complete)),
or a source it needs could not be read. No verdict in the table below means
"unknown", and borrowing one says something nobody established: `keep` would
call the component current, `regenerate` would rebuild it on a guess. A client
shows an unassessed component as unassessed, never as current.

### Verdicts

One vocabulary for every node a plan reaches. `verdict` is what will be done;
`because` is why. For a generated file the verdict is the rebuild decision's
([`architecture/generation`](../architecture/generation.md#deciding-whether-a-file-must-be-rebuilt))
under these names, one per row of its table, so neither restates the other:

| Rebuild decision row | Its action | `verdict` | `because` |
|---|---|---|---|
| 1, the file is absent | Generate | `generate` | `absent` |
| 2, its digest differs | Refuse | `refused` | `edited` |
| 3, it no longer declares or serves what its entry assigns | Generate | `generate` | `non-compliant` |
| 4, a change touches what it is answerable for | Generate | `regenerate` | `reached-by-change` |
| 5, a change reached it and touches nothing it is answerable for | Keep, reported as assessed | `assessed-unchanged` | `reached-by-change` |
| 6, nothing changed | Keep | `keep` | `unchanged` |

A node reached only through `generated_from`, never through `implements`, is
one that row five covers. Resolution adds the rest: `review` and `redeploy`
for reached nodes that are not generated files, the refusals `unowned`,
`opt-in` and `downgrade`, and `blocked` and `halt` from `on_change`.
[`checks/change-vectors.py`](../checks/change-vectors.py) reads the table
below and nothing else.

| `verdict` | `because` may be |
|---|---|
| `generate` | `absent`, `non-compliant` |
| `regenerate` | `reached-by-change`, `incomplete` (the second for a component its latest run did not finish building: apply resumes that run, and every file it banked is reused) |
| `repair` | `refuted`, `unverified` (a component whose latest run completed and whose verification refuted it, or reached no verdict on it: apply resumes its repair loop on the tree that run ended on) |
| `translate` | `absent`, `criterion-moved` (a translated test: the first for a criterion with no test yet, the second for one whose criterion's digest moved since its test was translated) |
| `review` | `reached-by-change`, `unmaintained`, `older-instruction` (the first for a node a person must look at, such as a document or a control; the second for a component an input reaches whose bytes moved and whose version did not; the third for a test, a plan or a file made under an instruction since revised, which is kept until somebody chooses to make it again) |
| `redeploy` | `reached-by-change` |
| `keep` | `unchanged` |
| `assessed-unchanged` | `reached-by-change` (row five: the change touches nothing it is answerable for) |
| `refused` | `edited`, `unowned`, `opt-in`, `downgrade` |
| `blocked` | `version-bump` (a dependant's range excludes the new major; `detail` names it) |
| `halt` | `removed` |

**An input whose bytes moved without its version moving is `review`, because
`unmaintained`, and is never regenerated on.** It is the row of
[`schemas/programme`](programme.md#version-and-version_hash-are-not-alternatives)'s
table that says upstream moved and made no claim about it, and the rule there
holds here: never taken unread. A version is the author's statement of what a
change may break; with none, a regeneration would rebuild on a change nobody
classified, and `keep` would call it current when its inputs are not what it
was built from. A component a versioned change also reaches is `regenerate` as
row four says, and its `detail` names the unmaintained inputs it will read; one
reached only by unmaintained inputs is `review`, and `apply` builds nothing for
it. The corpus forbids the state outright
([`schemas/common`](common.md#blueprint-versions)), so a tenant meets it only
where an edit escaped that rule, and a plan says so rather than deciding for
the author.

**A build that is refuted, unverified or unfinished is never `keep`.** An
adoption's plan asks of a component the tenant has generated whether it was
built, and reads the answer from the component's latest run statement
([`schemas/run-statement`](run-statement.md#the-verdict-a-run-ends-with)): a
run that did not complete is `regenerate`, because `incomplete`; one that
completed with its conformance `refuted` is `repair`, because `refuted`; one
that completed with conformance `not-run` is `repair`, because `unverified`.
Only a complete run whose conformance is `established` is `keep`. Each is a
`build_set` component, and apply builds each as its verdict says: `generate`
and `regenerate` through generation, the second resuming its run; `repair`
never through generation — it takes the tree the run ended on, plans nothing
and generates nothing, and runs the build gate, the repair loop and
conformance on it against the blueprints as they are now, refusing a tree that
is not that run's ([`architecture/generation`](../architecture/generation.md#a-rebuild-input-must-not-be-something-the-build-changes)). A
plan that asks whether a component's inputs are current, an upgrade's, still
lists one whose latest run did not complete as unassessed
([Unassessed is not a verdict](#unassessed-is-not-a-verdict)): the two plans
ask different questions of the same record.

**A change that generates a service a programme runs on writes its
configuration section.** Where `.weblisk/config.yaml` holds no section for
it, apply writes one with the service's conventional port
([`schemas/config`](config.md#the-services-a-programme-runs-on)), and the
change records each section it wrote in `config_written`; a section already
present is left as it is and not recorded.

**A translated test is a plan entry of its own.** Each criterion a change
owes that is settled by a translated test
([`architecture/engine`](../architecture/engine.md#the-unit-is-a-criterion))
has an entry whose `output` is the test's path, in phase R, because the
criteria and the paths the language declares fix it before any model is
asked. Its verdict is `translate` when the test is absent or its criterion's
digest moved, `keep` when neither, and `review`, because `older-instruction`,
when only the translate instruction was revised since: a test is translated
again only when its criterion moves
([`architecture/engine`](../architecture/engine.md#how-the-record-makes-builds-incremental)).
`implements` names the criterion. No generate or repair entry names a test's
path.

A component a dependency pulled in is marked by its `build_set` entry's
`added_by`, never in a plan entry's `because`, which keeps its verdict's own
reason; it is built only on approval.

## Rules

Each rule has an id; the [vectors](../vectors/change/README.md) cite them.

```yaml
rules:
  - id: change-id
    rule: id is 32 lowercase hex characters
  - id: change-kind
    rule: kind is adopt, upgrade, remove or revert
  - id: change-request
    rule: request is non-empty, and each entry is a ref or citation in the grammar of schemas/names.md; a path is refused, because a path is a coordinate on one host
  - id: change-reverts
    rule: reverts is present exactly when kind is revert
  - id: change-base
    rule: base names corpus and lock, and every digest is written sha256:<hex>
  - id: base-pins
    rule: base.pins is non-empty; each entry has kind (project, custom or core), origin and revision; each revision is a full commit, 40 or 64 lowercase hex characters, never a short commit or one marked dirty; and base.corpus equals the first entry's revision
  - id: base-lock-of
    rule: lock_of, when present, is non-empty text naming what lock is a digest of; absent, lock is the digest of .weblisk/build.lock
  - id: unassessed-entry
    rule: each unassessed entry has unit and detail and no verdict or because, and no unit is both unassessed and the unit of a plan entry
  - id: plan-not-empty
    rule: plan has at least one entry; an empty plan is a plan that could not be computed, never a clean one
  - id: plan-target
    rule: each entry names exactly one of unit and output
  - id: plan-verdict
    rule: verdict is one of the table's, and because is one the table allows for it
  - id: plan-phase-f
    rule: an entry of phase F has an output, never a unit
  - id: approval-present
    rule: approval is present in states approved, applied, verified and failed, absent in planned and rejected, and either in superseded, which a change reaches from planned or approved; in applied, verified and failed it is absent exactly when without_approval is true
  - id: without-approval
    rule: without_approval, when present, is true, and only in states applied, verified and failed
  - id: approval-signed
    rule: approval has by, signature, plan_digest and at, and signature is the unpadded base64url of 3309 bytes, the length of an ML-DSA-65 signature (4412 characters). Whether it verifies is the change service's check, against the signer's key
  - id: approval-self
    rule: approval.by equals requested_by only when approval.development is true
  - id: approval-position
    rule: when approver_position is present, approval, if present, has position equal to it; position is never present without approver_position
  - id: rejection-present
    rule: rejection is present exactly in state rejected, and has by, reason, signature, plan_digest and at, with signature shaped as approval-signed says
  - id: approval-conflicts
    rule: a change is approved only when conflicts.found is empty, or holds only C2 conflicts and strict is false
  - id: applied-run
    rule: applied_run is present exactly in states applied, verified and failed
  - id: replace-edited
    rule: each replace_edited entry has component, path, a non-empty why and a sha256 digest; an edited file the plan reaches is regenerated only when an entry names it, and is otherwise refused because edited
  - id: unowned-named
    rule: a file in a component's package that no record names is never kept silently; the plan refuses its component because unowned, naming the file and the tenant packages it imports, until a replace_edited entry with unowned true names it, and apply removes it before that component is built
  - id: config-edit
    rule: each config_edits entry names path, kind, backend, from, to and blueprint, and to is a driver blueprint declares; applied is set only in states applied, verified and failed, and only after that component was built
  - id: outcomes-present
    rule: outcomes is present only in states applied, verified and failed; each entry has component, a result of built, failed, refused or skipped, and a verdict whose outcome is verified, failed, inconclusive or unchecked
```

## Reading one

- A change whose `base` no longer matches the tenant — another corpus
  revision, another lock digest, or a fabric tip that has moved — is stale.
  `apply` refuses it, and the client renders it as stale, never as ready.
- `without_approval: true` is shown wherever the change is, as `development:
  true` is: nobody approved it, and the operator at the tenant's host applied it.
- An outcome's `verdict` is the build's own ([`architecture/generation`](../architecture/generation.md#the-verification-gate)).
  An applied change says what was built and whether it was verified; it never
  turns a build that was not verified into a pass.
- An entry of phase F is labelled as the model's proposed files wherever it is
  shown, until part ids make that phase deterministic.
- `shown_roots` is display. The roots each output traces to are recorded in its
  run statement ([`schemas/run-statement`](run-statement.md)) and nowhere else.
