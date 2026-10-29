<!-- blueprint
type: architecture
name: tenancy
version: 3.1.0
requires: [protocol/types, protocol/identity, architecture/orchestrator, architecture/storage, patterns/principal-identity, patterns/versioning, patterns/namespace]
platform: any
tier: free
adoption: opt-in
-->

# Weblisk Tenancy

Hosting many hubs on shared infrastructure without the host becoming part of any
tenant's trust boundary.

## Overview

A Weblisk deployment is a hub, and a hub is self-sovereign: it owns its agents, its
data and its identity. Nothing in the framework has said what happens when one party
operates the infrastructure for **many** hubs belonging to **other** parties.

That is what this blueprint specifies. A **host** provisions and operates infrastructure;
a **tenant** owns everything that runs on it. The host can create a tenant, suspend one
for non-payment and delete one on request. It cannot read a tenant's records, act as one
of its operators, or recover its identity — and none of those are promises, they are
properties of how components are bound.

Tenancy is `adoption: opt-in`. A deployment that hosts nobody serves none of this
surface, which is a correct deployment rather than an unfinished one.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category, retryable, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        # The tenant's identity: Export produces its public half, and the
        # host holds no private half (Does NOT own)
        - name: SigningKeyPair
          fields_used: [algorithm, public_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=2.0.0 <5.0.0"
    bindings:
      types:
        # Provisioning binds a tenant's orchestrator to that tenant's own
        # stores, and an upgrade keeps the binding (Data Flow)
        - name: OrchestratorConfig
          fields_used: [storage_dsn]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/storage
    version: ">=1.0.0 <3.0.0"
    bindings:
      behaviors:
        # A tenant's records outlive its components: an upgrade replaces
        # them and a suspension stops serving, and neither loses a record
        # (Data Flow, Verification Checklist)
        - name: durable-records
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/principal-identity
    version: ">=1.0.0 <3.0.0"
    bindings:
      types:
        # The identity that claims a tenant, recorded as
        # Tenant.owner_public_key
        - name: Identity
          fields_used: [public_key]
      behaviors:
        # A host operator reaches a tenant only on an invitation its owner
        # issues, and loses that access when the owner revokes it (Security)
        - name: principal-invitation
        - name: revocation
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/versioning
    version: ">=1.0.0 <4.0.0"
    bindings:
      behaviors:
        # The schema migration a tenant's first request after an upgrade
        # runs (Data Flow)
        - name: version-migration
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/namespace
    version: ">=1.0.0 <3.0.0"
    bindings:
      behaviors:
        # The owner's claim of the tenant's namespace, the first name the
        # tenant hub's registry accepts (Interfaces)
        - name: namespace-registry
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
   ┌──────────────────────────────────────────────────────────┐
   │ CONTROL PLANE — the host operates this                   │
   │                                                          │
   │  tenant registry · admission · artifact registry ·       │
   │  fleet deployments · quotas · billing state · audit      │
   │                                                          │
   │  Holds NO tenant records.                                │
   └───────────────────────┬──────────────────────────────────┘
                           │ provisions, upgrades, suspends
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │ TENANT  │        │ TENANT  │        │ TENANT  │
   │  orgs   │        │  orgs   │        │  orgs   │
   │ projects│        │ projects│        │ projects│
   │  hub    │        │  hub    │        │  hub    │
   │ own     │        │ own     │        │ own     │
   │ store   │        │ store   │        │ store   │
   │ own     │        │ own     │        │ own     │
   │ identity│        │ identity│        │ identity│
   └─────────┘        └─────────┘        └─────────┘

   No tenant component holds a handle to another tenant's state.
```

**Tenant** is the durable top-level context. It holds one or more **orgs**, each holding
one or more **projects**. Tenant is the outer boundary rather than org because
organisations are bought, sold, merged and wound up, and the context that survives those
events is the one worth binding identity, billing and data ownership to.

**Hub** is the tenant's federation surface, specified by `architecture/hub`. A tenant has
at most one. Tenancy is about hosting hubs; the hub is what is hosted.

**Control plane** is the host's own component. It records which tenants exist, what they
are entitled to, and which artifact version each runs. It holds no tenant business data,
so compromising it exposes billing metadata rather than any tenant's records.

---

## Responsibilities

**Owns**

- The host's provisioning registry of tenants, orgs and projects, and the lifecycle
  state of each. It records what the host provisioned, not the tenant's own structure
  (the gap under [Endpoints](#endpoints))
- Admission control — whether a new tenant may be created now
- The artifact registry: which component versions exist, and their provenance
- Fleet deployment: rolling a version across tenants, and pinning individual tenants
- Quota accounting and enforcement points
- The audit record of every host action taken against a tenant

**Does NOT own**

- Any tenant's records, knowledge, agents or configuration — those belong to the tenant
- Any tenant's identity or key material
- Operator authority over a tenant. The host holds none by default and acquires it only
  by invitation (§Security)
- Agent registration and namespace ownership — that is `architecture/orchestrator`,
  once per tenant
- Federation and peer trust — that is `architecture/hub` and `protocol/federation`

---

## Endpoints

| Method | Path | Operation | Auth | Purpose |
|--------|------|-----------|------|---------|
| POST | /v1/tenants | ProvisionTenant | yes | Create a tenant and its components |
| GET | /v1/tenants | ListTenants | yes | Tenants this principal may see |
| GET | /v1/tenants/{tenant} | GetTenant | yes | Lifecycle state, version, quota usage |
| POST | /v1/tenants/{tenant}/suspend | SuspendTenant | yes | Stop serving; retain all state |
| POST | /v1/tenants/{tenant}/resume | ResumeTenant | yes | Resume a suspended tenant |
| POST | /v1/tenants/{tenant}/export | ExportTenant | yes | Produce a portable copy of everything the tenant owns |
| DELETE | /v1/tenants/{tenant} | DeleteTenant | yes | Destroy a tenant and every resource bound to it |
| GET | /v1/tenants/{tenant}/orgs | ListOrgs | yes | Orgs within a tenant |
| POST | /v1/tenants/{tenant}/orgs | CreateOrg | yes | Add an org |
| GET | /v1/artifacts | ListArtifacts | yes | Artifact versions available to deploy |
| POST | /v1/fleet/deployments | StartDeployment | yes | Roll an artifact version across tenants in batches |
| GET | /v1/fleet/deployments/{id} | DeploymentStatus | yes | Progress, batch state, halt reason |
| POST | /v1/tenants/{tenant}/pin | PinVersion | yes | Hold a tenant on a named artifact version |

> **Gap — nothing inside a tenant declares its organisations and projects.** The
> registry this blueprint owns is the host's: `ListOrgs` and `CreateOrg` answer,
> under the host's authority, which orgs a host provisioned, and exist only where
> a deployment is hosted at all. No route lists a tenant's projects, at either
> plane. Inside the tenant an organisation or a project appears only as a segment
> of a content repository's `scope_path` ([`architecture/content`](content.md)):
> a name, which can move, never an identity a record can join on. So a tenant
> cannot answer which organisations and projects it has, what durable id each
> carries, or which organisation a project belongs to, which
> [adoption at the organisation](../schemas/programme.md#one-act-by-a-person-at-the-organisation)
> needs in order to refuse a project's adoption by naming it. The structure is
> the customer's, so the answer belongs to the tenant's own hub, not to the
> control plane and not to a client. Which component holds it, the routes and
> capabilities that read and change it, and how the control plane's registry
> relates to it are not specified. Until they are, a client that holds an
> organisation or project the tenant does not declare says so, held by that
> client and not by the tenant, rather than presenting it as the tenant's
> record.

---

## Interfaces

**Provisioning** accepts a tenant name, an owner identity's public key, the tenant's
namespace, and an artifact version. It returns when
every resource the tenant needs exists and its hub answers, or it returns nothing and
leaves no resource behind.

**The namespace is minted at creation.** The host records it as it records the
tenant's name (`Tenant.namespace`). When provisioning is asked, before any
resource exists and before the tenant's registry does, it refuses a name by the
claim rules that need no registry's log
([`patterns/namespace`](../patterns/namespace.md#deciding-a-statement), step 6):
one outside the namespace grammar (`NAMESPACE_INVALID`), a reserved name, place
code or issuer code (`NAMESPACE_RESERVED`), and a name confusable with a
reserved one (`NAMESPACE_CONFUSABLE`). Whether a name is held, frozen or retired
is a registry's state, and the tenant's registry has none yet: that is decided
when the owner's claim is made there, below. The namespace
appears in the tenant's own files and no one else's
([`schemas/names`](../schemas/names.md#namespaces)).

Where the tenant's hub runs a namespace registry, the owner signs its claim of the
namespace ([`patterns/namespace`](../patterns/namespace.md#claim)) there before
provisioning returns. The claim names that registry's log id, so it is signed once
the registry exists, and it is the first name the registry accepts; a claim that
fails undoes provisioning as any failed step does. No tenant component serves that
pattern yet ([`patterns/namespace`](../patterns/namespace.md#implementation-notes)),
so until one does, provisioning records the namespace and signs no claim, and the
owner's claim is the first statement that registry accepts when it first runs. The
host never signs a claim for a tenant.

**Export** is the tenant's exit. It MUST produce everything the tenant owns in a form
that can be read without the host: records, configuration, agent definitions, and the
public half of its identity. A tenancy a tenant cannot leave is not hosting. What it
produces is at least what the tenant is rebuilt from
([Rebuilding a Tenant](#what-a-tenant-is-rebuilt-from)), so a tenant that leaves can be
stood up again without the host.

**Fleet deployment** takes an artifact version and a batch policy, and reports progress
per batch. It halts on error-rate regression rather than completing.

**Pinning** binds one tenant to a named version. A pinned tenant is skipped by fleet
deployment until unpinned.

---

## Data Flow

**Provisioning.** A request arrives at the control plane, which checks admission, records
the tenant and the identity public key its owner presented, creates the tenant's
storage and components bound only to that tenant's resources, applies the schema, and
records the routing entry. The components are at least the tenant's orchestrator and its
admin gateway ([`architecture/admin`](admin.md#the-admin-gateway-as-a-component)), the
minimum set every tenant has: without the gateway no person's request reaches it. Every step is compensating: a failure at step *n* undoes
*n-1…1*. The owner generates that key and keeps its private half
([`patterns/principal-identity`](../patterns/principal-identity.md)); the control plane
never generates one.

**A request to a tenant.** The host's request path resolves the tenant from the request,
rejects unknown, suspended and unprovisioned tenants, applies quota, and dispatches to
that tenant's components. The resolved tenant is carried as execution context. It is
never read from the request body, and never accepted as a parameter from a caller.

**Upgrade.** A new artifact version is registered. Fleet deployment replaces components
tenant by tenant in batches, preserving each tenant's resource bindings. Schema migration
runs on the tenant's first request after its components change, so a rollout never
requires a synchronous sweep.

**Deletion.** Export first if the tenant asked for one. Then every resource bound to the
tenant is destroyed, the routing entry is removed, and the audit record of the deletion
remains in the control plane. The audit record is the only thing that survives.

---

## Design Principles

1. **The host is not a party to the tenant's trust.** Every guarantee here is a property
   of what components are bound to, not a promise about how the host behaves. A guarantee
   that depends on the host's good conduct has not been specified.
2. **Tenant identity is ambient.** It is resolved from the authenticated request and
   injected by the runtime. No interface accepts it as a parameter, so no caller — and no
   agent acting on a caller's instructions — can name a tenant other than its own.
3. **One component, one tenant.** A component is bound to exactly one tenant's resources
   for its whole lifetime. Cross-tenant access is not prevented by a check; it is absent
   from what the component can address.
4. **Provisioning is a compensating transaction.** Partial provisioning leaves orphaned
   resources that consume quota and are attributable to nobody.
5. **Built once per version, deployed many times.** Components are produced from
   blueprints once per artifact version and deployed unchanged. A tenant is never a build.
6. **Every tenant can leave.** Export is a first-class operation, not a support request.
7. **Admission is a throttle, not a queue for its own sake.** The number of tenants that
   may be created in a window is a stated policy, because unbounded creation exhausts
   whatever the platform's ceilings are.

---

## Rebuilding a Tenant

A tenant MUST be rebuildable: from what it holds and the corpus it was built
from, with nothing a client keeps, it can be stood up again in an empty
directory and come back as **the same tenant** — the same hub identity, the
same repositories at the same heads, the same adoptions, the same operators,
and components that pass as the originals passed. This section is the one home
of what that takes. It holds whether or not anybody hosts the tenant: a tenant
on one machine, operated by its owner, is rebuilt by the same contract.

Three acts share words with this one and are not it:

- **Rebuilding a file** is [`architecture/generation`](generation.md#deciding-whether-a-file-must-be-rebuilt)'s
  per-file decision, inside one build. A tenant rebuild runs builds, and each
  of them makes that decision over a directory where every file is absent.
- **`ExportTenant`** is the host's endpoint ([Interfaces](#interfaces)). It
  MUST produce at least what [What a tenant is rebuilt from](#what-a-tenant-is-rebuilt-from)
  lists, so a tenant that leaves a host can be rebuilt without it.
- **A successor tenant** is a new tenant made with
  [`weblisk tenant create`](cli.md#weblisk-tenant-create-name) that adopts a
  former tenant's stores ([`architecture/content`](content.md#a-store-that-already-exists-is-the-normal-case)).
  It has a new hub identity, new change logs that begin at a census, and every
  entry in them recorded with provenance `unknown`, as content records a store
  rebuilt from a remote's copy ([`architecture/content`](content.md#a-remote-is-sent-to-and-never-read-from)).
  That is what is left when the rebuild set is not whole, and a rebuild is never
  reported where a successor is what was made.

### What a tenant is rebuilt from

Everything in this table is a fact nothing can derive again. The **holder** is
who must still have it on the day of the rebuild. The export
([`weblisk tenant export`](cli.md#weblisk-tenant-export)) writes the
**manifest**, a `TenantManifest`, and copies into its bundle what the last
column says it copies; everything else it names by reference and digest, and
the holder brings.

| What | Where it lives | Holder | In the bundle |
|---|---|---|---|
| **The corpus pin** — the corpus revision each component was built at, and each blueprint, mapping and adopted transcription at its digest | `.weblisk/build.lock` ([`schemas/build-lock`](../schemas/build-lock.md)); for a component no applied change has locked, the sources and revisions its build recorded ([`architecture/cli`](cli.md#weblisk-server-init)) | the tenant | the lock, copied; each revision named in `TenantManifest.corpus` |
| **The run statements** — what each build read and wrote | `provenance/runs/` ([`schemas/run-statement`](../schemas/run-statement.md#where-it-lives)) | the tenant | copied |
| **The declared configuration** | `.weblisk/config.yaml` ([`schemas/config`](../schemas/config.md)) and `.weblisk/model.json` ([`architecture/orchestrator`](orchestrator.md#the-tenants-model)) | the tenant | copied |
| **The repositories** — each store and the git history on its line, which holds every entry, every adoption record (`adoption.md`, `standards/<id>.json`) and every register, the [position-holders register](../schemas/position.md#who-holds-a-position) among them | at its placement: a backend's root and a locator ([`architecture/content`](content.md#a-placement-names-a-backend-never-a-location)) | whoever holds the backend's root (`held_by`) | never copied; each named by id, `scope_path`, placement, line and head |
| **The record stores** — each service's own records: the operator, credential and namespace registries and the audit log; the content service's repository registry, change logs, proposals, pseudonym map, anchors and record mirror; programme adoptions and installed items; execution's schedules and runs; notification's preferences; the fabric's ledger | each service's own store ([`architecture/storage`](storage.md)) under `.weblisk/data/` | the tenant | each captured at a consistent point by its store's `backup-restore` ([`architecture/storage`](storage.md#contracts)), as the platform formats it |
| **The keys** — the orchestrator's, whose fingerprint is the hub identity; each service key; the admin gateway's registration key and its TLS key and certificate; each remote's credential | `.weblisk/keys/`, `.weblisk/tls/`, or a secret source ([`patterns/secrets`](../patterns/secrets.md)) | a secret source, or the operator's own backup of the encrypted key ([`protocol/identity`](../protocol/identity.md#key-backup-policy)) | never; each named by its fingerprint and where it is held. The certificate, being public, is copied |
| **The references to secrets** — every `key_passphrase` and every other `<source>:<reference>` the configuration holds | `.weblisk/config.yaml` | the secret source each names | the references only, never what they open |
| **The operators** — each name, identity id, role and status | the orchestrator's operator store ([`architecture/admin`](admin.md#operator-storage)) | the tenant holds the records; each operator holds their own private key | listed, and carried in the orchestrator's record store |

**The change log is not in git.** A repository's history on its line is a copy
of the record for a reader who has only git
([`patterns/content-git`](../patterns/content-git.md#design-principles), 1);
the evidence of record is the change log, held in the content service's own
store and never in a store a placement names
([`architecture/content`](content.md#the-change-log)). So is the pseudonym
map that turns a commit's author back into a person. A rebuild with the stores
and without the record stores is a successor, not this tenant.

**The bundle holds the tenant's records**, the pseudonym map and every path in
every log among them. It is held as the record stores are: by the tenant, under
exclusive custody, and is never a content remote's destination. A host that
produces one for `ExportTenant` keeps it no longer than
`export.retention_seconds` ([Configuration](#configuration)).

### What is derived, and never kept

What the rebuild set and the corpus produce again is not exported, and an
export that copied it would be a second home that drifts:

| Derived | From |
|---|---|
| Every file generation wrote — each component's source, `bin/`, `.weblisk/generation/` | the corpus at the pin, the configuration and, for a programme's services, the build plan its adoption emits ([`schemas/programme`](../schemas/programme.md#adoption-emits-a-build-plan)) |
| The service directory and every lease | each component registering when it starts ([`architecture/orchestrator`](orchestrator.md#what-a-tenant-consists-of-and-where-that-is-declared)) |
| Every claim a fabric producer made | running the producer again ([`architecture/fabric`](fabric.md#the-ledger)). A claim a person confirmed, rejected or retired is not derived; it is in the fabric's record store |
| Occurrences, the four adoption states, staleness | computed on each read ([`schemas/programme`](../schemas/programme.md#the-tenants-copy-is-the-tenants)) |
| Sessions, tokens, challenges, the bootstrap secret, `.weblisk/run/`, `.weblisk/logs/` | nothing: they end, and a person signs in again |

**Generation is not byte-repeatable.** The same blueprints at the same pin may
be generated into different files. A rebuilt component is therefore judged by
what it does — its conformance verdict — and never by its bytes
([A rebuild is accepted when](#a-rebuild-is-accepted-when)).

**A generated file a person edited is not derived.** Its digest differs from
its latest run statement's ([`architecture/generation`](generation.md#deciding-whether-a-file-must-be-rebuilt)),
and generating it again would not bring the edit back. The export lists each
such file in `TenantManifest.unheld`, and the rebuild names it as not
reproduced.

### What a rebuild cannot bring back

Stated so that nobody learns it on the day:

- **A key whose holder no longer has it.** The rebuild refuses rather than
  minting a new one. A new orchestrator key is a new hub: every operator's
  credential names the old `hub_id`, every client's pin is for the old
  certificate, every change log's earlier authorities are `unvouched`
  ([`architecture/content`](content.md#who-signs)), and a namespace claim
  signed for the old registry names a log that is gone. What remains is a
  successor, made by a person, and every operator registers there again
  ([`protocol/identity`](../protocol/identity.md#key-recovery)). A
  development key kept with `kdf = none` in `.weblisk/keys/` alone is held by
  nothing else, and the export says so.
- **The record stores.** Without them the stores come back only by adoption:
  new logs, provenance `unknown`, open proposals and pseudonyms lost, operators
  bootstrapped and approved again, schedules paused.
- **What a client holds.** A rebuild reads nothing from a client. Any fact
  about the tenant that only a client keeps is not in the rebuild set, and is
  not rebuilt ([Known gaps](#known-gaps)).
- **A pin nobody can read.** A component built from a corpus with uncommitted
  changes names a revision no commit reproduces
  ([`architecture/cli`](cli.md#weblisk-server-init)), and the export
  refuses it.

What a person does again even when the set is whole: unlocks each secret
source, signs in, and starts a build, which asks the model the CLI resolves at
that moment.

### The rebuild, in order

[`weblisk tenant rebuild`](cli.md#weblisk-tenant-rebuild) takes a bundle and an
empty directory. Each step is refused before the next begins, and a refusal
leaves the directory as the step before it left it, with nothing started:

1. **Read the bundle.** Every file's digest equals the manifest's, and the
   manifest is a `TenantManifest`.
2. **Resolve the corpus at the pin.** Every blueprint is read at the revision
   the manifest names for the component it builds, never at a source's `HEAD`
   ([`architecture/cli`](cli.md#where-blueprints-come-from)).
3. **Write the declared files** — configuration, model configuration, lock,
   run statements and certificate — and the `.gitignore`
   [`weblisk tenant create`](cli.md#weblisk-tenant-create-name) writes. A
   backend whose root is elsewhere on this host is given its new root here,
   by the person; its placements do not change.
4. **Place every key** from its holder, each with the fingerprint the manifest
   names.
5. **Find every store** at its placement, on its line, at the head the
   manifest names.
6. **Restore every record store** from the bundle, by its store's
   `backup-restore`.
7. **Generate every component** the manifest names, in the order
   [`schemas/programme`](../schemas/programme.md#the-services-in-the-order-they-are-built)
   gives, each from the corpus at its pin.
8. **Start them.** The orchestrator finds its operators and emits no bootstrap
   secret ([`architecture/admin`](admin.md#bootstrap-flow)); the content
   service checks every change log, finds every configured repository already
   declared and reconciles it rather than establishing it
   ([`architecture/content`](content.md#configuration)), and the record
   mirror shows each store is the one it recorded.
9. **Accept it**, below, and report.

### A rebuild is accepted when

The rebuilt tenant is exported, and its manifest compared with the one the
rebuild began from. A rebuild is reported done only where every row holds:

| Compared | Equal when |
|---|---|
| Hub identity | the same `hub_id` |
| Repositories | the same set of `id`, `scope_path` and placement, each with the same line and head, and the same log id. A log's tip may have moved, because the content service introduces a log key into every log when it starts; the exported tip's entry is still the entry at that `seq` |
| Adoptions | the same programmes and standards, at the same organisations, each at the same pinned version, revision and digest |
| Components | the same set of names registered with a live lease |
| Conformance | the same verdict class at each level [`weblisk test conformance`](cli.md#weblisk-test-conformance) runs: `passed`, `failed` or `not-run` |
| Operators | the same names, identity ids, roles and statuses |

A row that differs is reported, naming both values, and the rebuild exits
non-zero. The rebuilt tenant is left as it is for a person to look at, and is
never reported rebuilt.

### Proving it with no live hub

The round trip is the test, run in a scratch directory:

1. Create a tenant there, with every port chosen free, a secret source in the
   scratch directory and a `HOME` of its own, and every orchestrator address
   any step could fall back to set to one nothing listens on, so no step can
   reach a running tenant.
2. Declare a repository, adopt a standard into it, admit a second operator,
   and run conformance.
3. Export, stop the tenant and delete its directory, leaving its stores and
   the bundle.
4. Rebuild into a new directory in the scratch directory, and require the
   comparison above to find nothing.
5. Each control: delete one record store from the bundle, then one key from
   the secret source, then one commit from a store's line. Each rebuild MUST
   be refused at its own step, naming what is missing.

The comparison itself is a function of two manifests, and is tested on
manifests alone with no tenant at all.

### Known gaps

- **Nothing in the tenant declares its organisations and projects**
  ([Endpoints](#endpoints), the gap). A manifest carries a repository's
  `scope_path`, which names them and does not identify them, so a rebuild
  restores the names and nothing a record could join on. Where a client holds
  an organisation's or a project's durable id, that id is not rebuilt.
- **Who may do what, beyond an operator's role, has no store in the tenant.**
  The operator store holds operators and their roles
  ([`architecture/admin`](admin.md#operator-storage)). A `Grant` scoped
  narrower than the hub ([`patterns/principal-identity`](../patterns/principal-identity.md#types))
  is specified and no hub store holds one, and a person who is not an operator
  has no record at all, so a client that keeps either keeps what no rebuild
  reads.
- **The position-holders register has a home and may be empty.** It is the
  records repository's ([`schemas/position`](../schemas/position.md#the-register)),
  and the `position-holder` kind is declared-unavailable until content serves
  a register's rows ([`schemas/position`](../schemas/position.md#known-gaps)).
  A holding a client keeps instead of writing it there is not rebuilt.
- **Schedules, notices and preferences have homes that are not yet running.**
  The `schedule`, `programme-adoption`, `installed-item`, `notification` and
  `preference` kinds ([`schemas/kinds`](../schemas/kinds.md)) live in
  execution, the programme service and notification. Until a tenant runs
  those services, standing work held anywhere else is not rebuilt.
- **A tenant's presentation has no home.** No tenant service declares a
  tenant's theme, and one held by a client is not rebuilt.
- **No record store declares `backup-restore` yet.** The contract is
  optional in [`architecture/storage`](storage.md#contracts), and the export
  refuses a store that cannot be captured at a consistent point.
- **A store lost from its placement cannot be brought back from the record
  mirror.** The mirror holds every commit the service recorded, and nothing
  specifies restoring a store from it.

---

## Types

```yaml
types:
  Tenant:
    description: The durable top-level context that owns orgs, projects and a hub
    fields:
      tenant_id:
        name: TenantID
        type: string
        required: true
        description: "Stable identifier, never reused after deletion"
      display_name:
        name: DisplayName
        type: string
        required: true
        description: "Human-readable name"
      state:
        name: State
        type: string
        required: true
        description: "`provisioning`, `active`, `suspended`, `exporting`, `deleting`, `deleted`"
      owner_public_key:
        name: OwnerPublicKey
        type: string
        required: true
        description: "Public half of the identity that claimed the tenant"
      namespace:
        name: Namespace
        type: string
        required: true
        description: "The tenant's namespace, in the grammar of schemas/names, fixed at creation (Interfaces)"
      artifact_version:
        name: ArtifactVersion
        type: string
        required: true
        description: "Artifact version this tenant's components were built from"
      pinned:
        name: Pinned
        type: bool
        required: false
        description: "When true, fleet deployment skips this tenant"
      created_at:
        name: CreatedAt
        type: timestamp
        required: true
  Org:
    description: An organisation within a tenant
    fields:
      org_id:
        name: OrgID
        type: string
        required: true
        description: "Unique within its tenant"
      tenant_id:
        name: TenantID
        type: string
        required: true
        description: "Owning tenant"
      display_name:
        name: DisplayName
        type: string
        required: true
        description: "Human-readable name"

  Project:
    description: A unit of work within an org
    fields:
      project_id:
        name: ProjectID
        type: string
        required: true
        description: "Unique within its org"
      org_id:
        name: OrgID
        type: string
        required: true
        description: "Owning org"
      display_name:
        name: DisplayName
        type: string
        required: true
        description: "Human-readable name"

  ArtifactVersion:
    description: A set of component builds produced from one blueprint revision
    fields:
      version:
        name: Version
        type: string
        required: true
        description: "Identifier for this artifact set"
      blueprint_revision:
        name: BlueprintRevision
        type: string
        required: true
        description: "The corpus revision the components were generated from"
      digest:
        name: Digest
        type: string
        required: true
        description: "Content digest over the artifact set"
      conformance:
        name: Conformance
        type: string
        required: true
        description: "Result of the conformance run that gated publication"

  FleetDeployment:
    description: A rolling replacement of components across tenants
    fields:
      deployment_id:
        name: DeploymentID
        type: string
        required: true
        description: "Unique identifier"
      artifact_version:
        name: ArtifactVersion
        type: string
        required: true
        description: "Version being deployed"
      batch_size:
        name: BatchSize
        type: int
        required: true
        description: "Tenants replaced per batch"
      state:
        name: State
        type: string
        required: true
        description: "`running`, `halted`, `complete`, `rolled-back`"
      halt_reason:
        name: HaltReason
        type: string
        required: false
        description: "Why the rollout stopped, when it did"

  AdmissionPolicy:
    description: What limits tenant creation
    fields:
      max_concurrent_trials:
        name: MaxConcurrentTrials
        type: int
        required: true
        description: "Ceiling on simultaneously live trial tenants"
      inactivity_window:
        name: InactivityWindow
        type: int
        required: true
        description: "Seconds of inactivity after which a trial becomes reclaimable"

  TenantManifest:
    description: What a tenant is rebuilt from, written by an export as
      manifest.json in its bundle, as RFC 8785 canonical bytes so its digest is
      recomputable with sha256sum (Rebuilding a Tenant)
    fields:
      manifest:
        name: Manifest
        type: int
        required: true
        description: "The manifest's form; 1"
      hub_id:
        name: HubID
        type: string
        required: true
        description: "Fingerprint of the orchestrator's key, protocol/identity's Key Fingerprint: the tenant's identity"
      hub_name:
        name: HubName
        type: string
        required: true
        description: "The configuration's hub.name"
      exported_at:
        name: ExportedAt
        type: timestamp
        required: true
      corpus:
        name: Corpus
        type: "[]ManifestPin"
        required: true
        description: "Each component's pin. One entry per component the service directory lists with a live lease at export, in the order its build is planned"
      files:
        name: Files
        type: "[]ManifestFile"
        required: true
        description: "Every file the bundle holds besides the manifest, each with its digest"
      repositories:
        name: Repositories
        type: "[]ManifestRepository"
        required: true
        description: "Every repository the content service records declared. Empty where the tenant runs no content service, which components then says"
      adoptions:
        name: Adoptions
        type: "[]ManifestAdoption"
        required: true
        description: "Every adoption record found in the repositories: each adoption.md and each standards/<id>.json carrying extends"
      records:
        name: Records
        type: "[]ManifestRecordStore"
        required: true
        description: "Each service's record store as the bundle holds it"
      keys:
        name: Keys
        type: "[]ManifestKey"
        required: true
        description: "Every key the tenant's components use, by fingerprint and holder"
      secret_references:
        name: SecretReferences
        type: "[]string"
        required: true
        description: "Every <source>:<reference> the configuration holds, sorted. Never what any opens"
      operators:
        name: Operators
        type: "[]ManifestOperator"
        required: true
        description: "Every operator the orchestrator records, revoked included"
      conformance:
        name: Conformance
        type: "map[string]string"
        required: true
        description: "Per level weblisk test conformance runs, `passed`, `failed` or `not-run`"
      unheld:
        name: Unheld
        type: "[]ManifestUnheld"
        required: true
        description: "What the export found that the rebuild will not bring back. Empty is a claim, never a default"

  ManifestPin:
    description: The corpus one component was built from
    fields:
      component:
        name: Component
        type: string
        required: true
        description: "The name the component registers under (schemas/programme, The services, in the order they are built)"
      sources:
        name: Sources
        type: "[]ManifestSource"
        required: true
        description: "Every blueprint source its build read, in the resolver's order"
      run_id:
        name: RunID
        type: string
        required: true
        description: "The latest run statement that wrote the component's files"

  ManifestSource:
    description: One blueprint source at one revision
    fields:
      origin:
        name: Origin
        type: string
        required: true
        description: "Where it is read from: a locator, never an identity"
      revision:
        name: Revision
        type: string
        required: true
        description: "The full commit object name. Never one carrying -dirty"

  ManifestFile:
    description: One file the bundle holds
    fields:
      path:
        name: Path
        type: string
        required: true
        description: "Relative to the bundle's root"
      digest:
        name: Digest
        type: string
        required: true
        description: "sha256:<hex> of its bytes, as patterns/content-identity spells it"

  ManifestRepository:
    description: One declared repository, as a rebuild must find it again
    fields:
      id:
        name: ID
        type: string
        required: true
      scope_path:
        name: ScopePath
        type: string
        required: true
      backend:
        name: Backend
        type: string
        required: true
      locator:
        name: Locator
        type: string
        required: true
      line:
        name: Line
        type: string
        required: true
        description: "The branch the store follows (patterns/content-git)"
      head:
        name: Head
        type: string
        required: true
        description: "The commit the line named at export"
      log_id:
        name: LogID
        type: string
        required: true
      log_seq:
        name: LogSeq
        type: int
        required: true
        description: "The change log's tip at export"
      log_tip_digest:
        name: LogTipDigest
        type: string
        required: true
        description: "SHA-256 of the stored line at log_seq"

  ManifestAdoption:
    description: One adoption record, as it was found
    fields:
      kind:
        name: Kind
        type: string
        required: true
        description: "`programme` or `standard`"
      id:
        name: ID
        type: string
        required: true
        description: "The programme's or standard's id, as the record carries it"
      scope_path:
        name: ScopePath
        type: string
        required: true
        description: "The organisation it was adopted at"
      repository:
        name: Repository
        type: string
        required: true
        description: "The id of the repository the record is in"
      path:
        name: Path
        type: string
        required: true
      digest:
        name: Digest
        type: string
        required: true
        description: "sha256:<hex> of the record's bytes"

  ManifestRecordStore:
    description: One service's record store, captured by its backup-restore
    fields:
      service:
        name: Service
        type: string
        required: true
        description: "The name the service registers under"
      path:
        name: Path
        type: string
        required: true
        description: "Where the capture is in the bundle"
      captured_at:
        name: CapturedAt
        type: timestamp
        required: true

  ManifestKey:
    description: One key, named and never carried
    fields:
      use:
        name: Use
        type: string
        required: true
        description: "What signs or listens with it: a component's service key, the admin gateway's TLS key, a remote's credential"
      fingerprint:
        name: Fingerprint
        type: string
        required: true
      holder:
        name: Holder
        type: string
        required: true
        description: "The <source>:<reference> that holds it, or `tenant-directory` where only the tenant's own directory does"

  ManifestOperator:
    description: One operator the orchestrator records
    fields:
      name:
        name: Name
        type: string
        required: true
      identity_id:
        name: IdentityID
        type: string
        required: true
      role:
        name: Role
        type: string
        required: true
      status:
        name: Status
        type: string
        required: true
        description: "protocol/types OperatorStatus"

  ManifestUnheld:
    description: One thing the export found and the rebuild will not bring back
    fields:
      what:
        name: What
        type: string
        required: true
        description: "A path, a key's use, or a store's service"
      reason:
        name: Reason
        type: string
        required: true
        description: "`edited-output`, `key-in-directory-only`, or another reason the export states in words"
```

---

## Configuration

```yaml
tenancy:
  admission:
    max_concurrent_trials:
      type: int
      default: 50
      description: Ceiling on simultaneously live trial tenants
    inactivity_window_seconds:
      type: int
      default: 1209600
      description: Inactivity after which a trial tenant becomes reclaimable
    reclaim_warning_seconds:
      type: int
      default: 259200
      description: Notice given before a trial tenant is reclaimed
  fleet:
    batch_size:
      type: int
      default: 25
      description: Tenants replaced per deployment batch
    halt_on_error_rate:
      type: float
      default: 0.02
      description: Error rate across a batch above which the rollout halts
  export:
    retention_seconds:
      type: int
      default: 604800
      description: How long an export remains retrievable
```

---

## Security

```yaml
security:
  trust_model:
    description: |
      The host is excluded from every tenant's trust boundary by construction
      rather than by policy. It operates infrastructure, records who owns what,
      and enforces quota; it holds no tenant's records and no tenant's key
      material. A host that can read a tenant's data, or act as one of its
      operators without invitation, has not implemented this blueprint.

      Isolation is a property of binding, not of checking. A component is bound
      to one tenant's resources for its lifetime, so cross-tenant access is not
      refused at a boundary — there is no address at which another tenant's
      state can be named.

  boundaries:
    - boundary: Caller → Control plane. Every request resolves to exactly one
        tenant before any tenant resource is reached, from authenticated context
        rather than from the request body
    - boundary: Control plane → Tenant components. The control plane provisions,
        suspends and replaces components; it does not read through them into a
        tenant's records
    - boundary: Tenant component → Tenant store. A component's bindings name one
        tenant's resources only, for its whole lifetime
    - boundary: Host operator → Tenant. Crossed only by an invitation the tenant
        owner issues and can revoke, and never by a host-held credential
    - boundary: Tenant → Tenant. Not a boundary that is guarded, but one that is
        absent — no component holds a handle to a second tenant's state

  enforcement:
    - rule: A tenant identifier supplied by a caller is never used to select
        tenant state
      mechanism: Tenant resolved from authenticated context and injected as
        execution context; no interface accepts it as a parameter
    - rule: No component may hold bindings to more than one tenant's resources
      mechanism: Bindings attached at provisioning, per component, and asserted
        by an audit over provisioned components
    - rule: The host holds no operator authority over a tenant by default
      mechanism: No host credential appears in any tenant's operator registry;
        access requires an invitation the owner issues and can revoke
    - rule: A tenant's identity cannot be recovered or replaced by the host
      mechanism: Recovery follows protocol/identity — a second registered
        operator, not a host action. The host holds no key that attests a
        tenant's identity
    - rule: Failed provisioning leaves no resource behind
      mechanism: Compensating transaction; each step's undo runs in reverse on
        failure
    - rule: A suspended tenant serves no request and loses no data
      mechanism: Lifecycle state checked at resolution, before dispatch;
        suspension changes routing rather than storage
    - rule: Deletion destroys every resource bound to the tenant
      mechanism: Resources enumerated from the provisioning record rather than
        discovered, so nothing provisioned can be missed
    - rule: Every host action against a tenant is attributable
      mechanism: Control-plane audit records principal, tenant, action, and
        time for provisioning, suspension, deployment, pinning and deletion
```

---

## Implementation Notes

- **Resolve the tenant once, at the edge of the request.** Every later stage receives it
  as context. A component that can re-resolve it can resolve it differently.
- **Enumerate resources for deletion from the provisioning record**, not by discovery. A
  resource created outside the record is a resource deletion will miss, which is why
  provisioning writes the record before it creates anything.
- **Admission and reclamation are one mechanism.** A ceiling with no reclamation is a
  ceiling that is eventually hit and never falls.
- **Pin before a tenant needs it.** Pinning exists so a tenant in a change freeze or a
  peak trading period can be held on a known-good version. It is worth far more offered in
  advance than granted after an incident.
- **Test the reclamation path before raising the admission ceiling.** A reclaimer that has
  never run is discovered at the moment the ceiling is reached, which is the moment it
  matters most.
- **Export is a product feature and a safety property.** It is what makes the host's
  exclusion from the trust boundary credible rather than asserted.

---

## Verification Checklist

- [ ] A tenant identifier supplied in a request body or a tool argument MUST NOT select tenant state ([Data Flow](#data-flow), [Design Principles](#design-principles) 2, [Security](#security))
- [ ] A provisioned component's bindings MUST reference only its own tenant's resources ([Design Principles](#design-principles) 3, [Security](#security))
- [ ] Provisioning failure at any step MUST leave no resource attributable to the tenant ([Data Flow](#data-flow), [Security](#security))
- [ ] Provisioning MUST refuse, before any resource exists, a namespace outside the grammar, reserved, a place or issuer code, or confusable with a reserved name, and, where the tenant's hub runs a namespace registry, MUST NOT return until the owner's claim is the first name that registry accepted ([Interfaces](#interfaces))
- [ ] A suspended tenant MUST serve no request and MUST retain every record ([Security](#security))
- [ ] `ExportTenant` MUST produce every record, configuration and agent definition the tenant owns ([Interfaces](#interfaces))
- [ ] `DeleteTenant` MUST destroy every resource named in the provisioning record ([Security](#security), [Implementation Notes](#implementation-notes))
- [ ] The host MUST hold no credential registered as an operator of any tenant it did not create for itself ([Security](#security))
- [ ] A pinned tenant MUST be skipped by fleet deployment ([Interfaces](#interfaces))
- [ ] A fleet deployment MUST halt when a batch's error rate exceeds the configured threshold ([Interfaces](#interfaces), [Configuration](#configuration))
- [ ] Tenant creation MUST be refused when the admission ceiling is reached ([Design Principles](#design-principles) 7, [Configuration](#configuration))
- [ ] Every host action against a tenant MUST appear in the control-plane audit with principal, tenant, action and time ([Security](#security))
- [ ] An export's `TenantManifest` MUST name every item [What a tenant is rebuilt from](#what-a-tenant-is-rebuilt-from) lists, and its bundle MUST hold no private key, no passphrase and no file generation wrote ([What a tenant is rebuilt from](#what-a-tenant-is-rebuilt-from), [What is derived, and never kept](#what-is-derived-and-never-kept))
- [ ] A generated file whose digest differs from its latest run statement's MUST be listed in `TenantManifest.unheld` with reason `edited-output` ([What is derived, and never kept](#what-is-derived-and-never-kept))
- [ ] A rebuild MUST read every blueprint at the revision its component's `ManifestPin` names, never at a source's `HEAD` ([The rebuild, in order](#the-rebuild-in-order) step 2)
- [ ] A rebuild whose key, record store or store at its head is missing MUST stop at its own step with nothing started, and MUST NOT mint a key or adopt a store in its place ([The rebuild, in order](#the-rebuild-in-order), [What a rebuild cannot bring back](#what-a-rebuild-cannot-bring-back))
- [ ] A rebuilt tenant's orchestrator MUST emit no bootstrap secret, and its content service MUST reconcile every configured repository rather than establish it ([The rebuild, in order](#the-rebuild-in-order) step 8)
- [ ] A rebuild MUST be reported done only where every row of the comparison holds, and a differing row MUST be reported with both values ([A rebuild is accepted when](#a-rebuild-is-accepted-when))
- [ ] The round trip in a scratch directory MUST reach no running tenant, and each of its three controls MUST be refused at its own step ([Proving it with no live hub](#proving-it-with-no-live-hub))
