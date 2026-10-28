<!-- blueprint
type: architecture
name: tenancy
version: 3.0.0
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
public half of its identity. A tenancy a tenant cannot leave is not hosting.

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
