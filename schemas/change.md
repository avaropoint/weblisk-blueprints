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
repository, written by the tenant's change service and by nothing else. A
client never opens it: Studio and a remote CLI read a change through the
tenant's API and render the same JSON. A change is never reopened once it has
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
| `change plan` | `tenant-api` | the change service runs the CLI (`cli-in-tenant`) to resolve and plan, and writes the change |
| `change list`, `change show` | `tenant-api` | reads changes |
| `change approve`, `change reject` | `tenant-api` | records the person's signed decision at the change service, the owner of the request, as the change's `approval` or `rejection` |
| `change apply` | `tenant-api` | the change service runs the CLI on the tenant host, under the tenant's `generation` credential, with the tenant's model (D26) |
| `change verify` | `tenant-api` | the change service runs the CLI's verification and records the result |
| `change revert` | `tenant-api` | plans a new change of kind `revert` |

## Shape

```yaml
change:
  id: <32 hex>
  kind: adopt | upgrade | remove | revert
  request: [<ref or citation>]     # what was asked for, as asked
  reverts: <change id>             # kind revert only
  requested_by: <identity id>      # the operator who asked
  requested_at: <unix seconds>
  strict: <bool>                   # C2 refuses when true, as it does for Studio
  state: planned | approved | rejected | applied | verified | failed | superseded
  base:                            # what the plan read; apply refuses if any moved
    corpus: <revision>
    lock: sha256:<hex>             # digest of .weblisk/build.lock as read
    fabric_tip: sha256:<hex> | unreported
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
  approver_position: <position id> # a knowledge change: the position its spec names (schemas/position), set by the plan
  approval:                        # present from state approved on
    by: <identity id>
    position: <position id>        # equals approver_position, which the approver holds
    signature: <base64url ML-DSA-65 over the plan digest>
    plan_digest: sha256:<hex>
    at: <unix seconds>
    development: <bool>            # the tenant is flagged development
  rejection:                       # state rejected only: the person's signed refusal
    by: <identity id>
    reason: <text>
    signature: <base64url ML-DSA-65 over the plan digest>
    plan_digest: sha256:<hex>
    at: <unix seconds>
  applied_run: <run id>            # the run statement apply wrote
  verify: {result: pass | fail | repair, run: <run id>}
```

A conflict is `{code: C1..C8, refs: [<ref>], detail: <text>}`, with the codes
[`architecture/generation`](../architecture/generation.md#resolving-a-request-of-many-roots)
names.

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
| `regenerate` | `reached-by-change` |
| `review` | `reached-by-change` (a node a person must look at, such as a document or a control) |
| `redeploy` | `reached-by-change` |
| `keep` | `unchanged` |
| `assessed-unchanged` | `reached-by-change` (row five: the change touches nothing it is answerable for) |
| `refused` | `edited`, `unowned`, `opt-in`, `downgrade` |
| `blocked` | `version-bump` (a dependant's range excludes the new major; `detail` names it) |
| `halt` | `removed` |

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
  - id: plan-not-empty
    rule: plan has at least one entry; an empty plan is a plan that could not be computed, never a clean one
  - id: plan-target
    rule: each entry names exactly one of unit and output
  - id: plan-verdict
    rule: verdict is one of the table's, and because is one the table allows for it
  - id: plan-phase-f
    rule: an entry of phase F has an output, never a unit
  - id: approval-present
    rule: approval is present in states approved, applied, verified and failed, absent in planned and rejected, and either in superseded, which a change reaches from planned or approved
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
```

## Reading one

- A change whose `base` no longer matches the tenant — another corpus
  revision, another lock digest, or a fabric tip that has moved — is stale.
  `apply` refuses it, and the client renders it as stale, never as ready.
- An entry of phase F is labelled as the model's proposed files wherever it is
  shown, until part ids make that phase deterministic.
- `shown_roots` is display. The roots each output traces to are recorded in its
  run statement ([`schemas/run-statement`](run-statement.md)) and nowhere else.
