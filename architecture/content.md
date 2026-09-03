<!-- blueprint
type: architecture
name: content
version: 1.0.0
requires: [protocol/types, patterns/content-identity, patterns/scope, patterns/contract, architecture/enforcement]
platform: any
tier: free
-->

# Weblisk Content Repository

The tenant service that holds authored text — policies, procedures, standards,
blueprints, evidence — as files whose bytes are their identity, on backends that
may not be ours alone.

## Overview

`architecture/storage` defines how the system persists **records**: opaque rows
in owned stores, addressed by id, paginated by cursor. `patterns/file-upload`
defines how it persists **assets**: blobs addressed by handle and delivered by
URL. Neither describes the thing a tenant actually governs — a tree of authored
documents where the path is the name, the bytes are the identity, and a human
with a text editor is a legitimate second author.

This document defines that service. Its distinguishing concern is **custody**:
a record store is written only by the component that owns it, but a content
repository may live on a share, a synced drive or a repository that other
people and other systems also write to. Where a second authority exists, our
permissions are not the only permissions and our audit trail is not the whole
history. A design that ignores this does not become safer by ignoring it — it
becomes confidently wrong, reporting that nobody read a file that half an
organisation can open.

> **Scope boundary:** this file defines the **content service contract and the
> custody model**. It does not name a backend, a filesystem or a product — see
> `architecture/storage` Design Principle 6, which governs here unchanged.
> Binary assets remain `patterns/file-upload`. Digest semantics remain
> `patterns/content-identity`.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category, retryable]
        - name: AgentManifest
          fields_used: [name, capabilities]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, action, target, status]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/content-identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ContentIdentity
          fields_used: [algorithm, digest, size]
        - name: StalenessVerdict
          fields_used: [state, recorded_digest, current_digest]
      behaviors:
        - name: content-digest
        - name: read-without-mutation
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/scope
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        # An enum: it declares values, not fields, so nothing is bound FROM it.
        - name: ScopeLevel
        - name: ScopeDeclaration
          fields_used: [level, context]
        - name: ScopeViolation
          fields_used: [expected_scope, actual_scope, entity]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/contract
    version: ">=1.0.0 <2.0.0"
    bindings:
      behaviors:
        - name: contract-validation
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/enforcement
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ViolationRecord
          fields_used: [boundary, agent, operation, violation_type, scope_required, scope_actual, detail, severity]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Content Service                                         │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Repository Registry                               │  │
│  │  - repositories declared for this tenant           │  │
│  │  - custody class per repository                    │  │
│  │  - derived scope ceiling                           │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Path Resolver                                     │  │
│  │  - scope confinement (tenant → org → project)      │  │
│  │  - traversal and symlink refusal                   │  │
│  │  - reserved-path refusal (.weblisk/)               │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Precondition Gate                                 │  │
│  │  - if_match digest compared before every write     │  │
│  │  - refuses on mismatch; never merges               │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Custody Reconciler        (shared custody only)   │  │
│  │  - detects out-of-band change by digest            │  │
│  │  - records provenance: authored | external         │  │
│  │  - never classifies external change as tampering   │  │
│  └────────────────────────────────────────────────────┘  │
│                          │                               │
│                          ▼                               │
│              ┌────────────────────────┐                  │
│              │  Backend Adapter       │  (not specified  │
│              │  read/write/list/stat  │   by this file)  │
│              └────────────────────────┘                  │
└──────────────────────────────────────────────────────────┘
                           │
        enforcement storage proxy intercepts every operation
                           ▼
              architecture/enforcement
```

**Repository Registry** holds the repositories a tenant has declared, each with
its custody class. Custody is a property of the *connection*, established when
the repository is declared and re-verified on use — never inferred per request.

**Path Resolver** confines a caller-supplied path to one repository within the
caller's scope. It refuses traversal segments outright rather than normalising
them: rewriting `/../x` to `/x` yields an in-bounds path that is not the one
requested, and silently answering a different question is worse than refusing.

**Precondition Gate** compares a caller-supplied digest against the stored bytes
before writing. This is the whole of the concurrency model — there is no merge,
no last-writer-wins and no lock.

**Custody Reconciler** exists only where a second authority can write. It
converts an unexplained change from an alarm into a recorded fact.

---

## Responsibilities

### Owns
- The content repository contract — list, read, write, delete, stat over a
  confined tree
- The custody model: classification, attestation properties, and the scope
  ceiling derived from them
- Precondition semantics for writes (digest match, refusal on mismatch)
- Out-of-band change detection and provenance recording for shared custody
- Reserved-path refusal for installation state
- Declaration of what a repository cannot attest, as a first-class answer

### Does NOT Own
- Digest algorithm or reference semantics (owned by `patterns/content-identity`)
- Concrete backends — filesystem, share, object store, version control (owned
  by platform blueprints, per `architecture/storage` Design Principle 6)
- Binary asset upload, processing and delivery (owned by `patterns/file-upload`)
- Record stores (owned by `architecture/storage`)
- The access decision itself (owned by `architecture/enforcement`; this service
  supplies the resource scope and custody facts the decision is made from)
- The backend's own permission system — this service reads it where it can and
  declares it unknown where it cannot; it never administers it

---

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | /v1/content | yes | List entries beneath a path, cursor-paginated |
| GET | /v1/content/entry | yes | Read one entry's bytes and identity |
| PUT | /v1/content/entry | yes | Write one entry; `if_match` required |
| DELETE | /v1/content/entry | yes | Remove one entry and retire its identity |
| GET | /v1/content/stat | yes | Identity and metadata without transferring bytes |
| GET | /v1/content/repositories | yes | Repositories in scope, with custody and ceiling |
| POST | /v1/content/reconcile | yes | Detect out-of-band change (shared custody only) |
| GET | /v1/health | no | Content service health. Served with or without an orchestrator |

---

## Interfaces

```yaml
interfaces:
  endpoints:
    - path: /v1/content
      methods: [GET]
      description: List entries beneath a path in a repository, cursor-paginated
      served_by: content-service

    - path: /v1/content/entry
      methods: [GET, PUT, DELETE]
      description: Read, write or remove one entry. PUT requires if_match
      served_by: content-service

    - path: /v1/content/stat
      methods: [GET]
      description: Identity and metadata for one entry without transferring bytes
      served_by: content-service

    - path: /v1/content/repositories
      methods: [GET]
      description: Repositories visible in the caller's scope, with custody,
        attestations and derived ceiling
      served_by: content-service

    - path: /v1/content/reconcile
      methods: [POST]
      description: Compare recorded digests against current bytes for a shared
        repository and record observations. Shared custody only
      served_by: content-service

  methods:
    - name: ListEntries
      signature: (repository, path, cursor, limit) → (entries, next_cursor)
      description: Ordered traversal beneath a confined path
      called_by: [gateway, agents]

    - name: ReadEntry
      signature: (repository, path) → (bytes, ContentIdentity, ContentEntry)
      description: Read bytes and identity without mutating either
      called_by: [gateway, agents]

    - name: WriteEntry
      signature: (repository, path, bytes, if_match, scope) → (ContentIdentity, ContentChange)
      description: Replace bytes when the precondition holds; refuse otherwise
      called_by: [gateway, agents]

    - name: DeleteEntry
      signature: (repository, path, if_match) → ContentChange
      description: Remove an entry and retire its identity
      called_by: [gateway, agents]

    - name: DescribeRepository
      signature: repository → ContentRepository
      description: Custody, attestations and derived ceiling
      called_by: [gateway, agents, admin]

    - name: Reconcile
      signature: (repository, since_cursor) → [ContentObservation]
      description: Detect and record out-of-band change. Shared custody only
      called_by: [content-service, agents]

  events:
    - topic: content.changed
      direction: publish
      description: An entry's identity changed, with provenance authored or external

    - topic: content.custody_degraded
      direction: publish
      description: A repository's attestations were re-verified and are weaker
        than when declared; its ceiling has dropped

    - topic: content.ceiling_exceeded
      direction: publish
      description: A write was refused because its scope exceeded the ceiling
```

---

## Error Handling

| Code | Category | When | Behaviour |
|---|---|---|---|
| `CONTENT_PRECONDITION_FAILED` | conflict | `if_match` does not equal the stored digest | Refuse. Return both digests. Never merge, never overwrite |
| `CONTENT_IF_MATCH_REQUIRED` | validation | A write arrived without a precondition | Refuse. A write with no precondition is a blind overwrite |
| `CONTENT_CUSTODY_CEILING_EXCEEDED` | policy | Declared scope exceeds the repository ceiling | Refuse, naming required and actual. Never downgrade the scope |
| `CONTENT_CUSTODY_UNDECLARED` | policy | Repository has no declared custody | Treat as `opaque`, apply the `internal` ceiling, and record the degradation |
| `CONTENT_PATH_REFUSED` | validation | Traversal segment, escaping symlink, or reserved path | Refuse the request as written. Do not normalise and proceed |
| `CONTENT_RESERVED_PATH` | policy | Path resolves into installation state (`.weblisk/`) | Refuse. Installation keys and state are never content |
| `CONTENT_UNREADABLE` | io | Bytes cannot be read | Identity is `unknown`, never `current` and never `stale` |
| `CONTENT_REPOSITORY_UNKNOWN` | validation | No repository of that id in the caller's scope | Refuse without disclosing whether it exists elsewhere |
| `ENFORCEMENT_DATA_CONTRACT_VIOLATION` | enforcement | Path is outside the agent's declared operational data contract | Refuse via the storage proxy |

---

## Data Flow

### Read Flow
1. Caller requests an entry, naming a repository and a path
2. Path Resolver confines the path to that repository within the caller's scope;
   traversal, escaping symlinks and reserved paths are refused
3. Enforcement storage proxy intercepts with operation `read`, the resolved
   path, and the entry's resource scope
4. On `allow`, bytes are read and the digest computed over the exact stored
   bytes — no normalisation, no reformatting
5. Under shared custody, the digest is compared against the last recorded
   digest; a difference produces a `ContentObservation` with provenance
   `external` and does **not** fail the read
6. Bytes and `ContentIdentity` are returned; the read leaves the bytes unchanged

### Write Flow
1. Caller submits bytes, a declared scope, and `if_match` — the identity it
   believes it is replacing
2. Path Resolver confines the path as above
3. Ceiling check: declared scope against the repository's derived ceiling.
   Exceeded → refuse, publish `content.ceiling_exceeded`
4. Enforcement storage proxy intercepts with operation `modify` or `create`
5. Precondition Gate reads the current digest and compares it to `if_match`.
   Mismatch → refuse with both digests. No merge is attempted
6. Bytes are written durably; the new digest is computed from what was written,
   not from what was submitted
7. A `ContentChange` is recorded with provenance `authored`, the acting
   identity, and the correlation id of the enforcement decision
8. `content.changed` is published

### Reconciliation Flow (shared custody only)
1. Reconcile is invoked for a repository, on a schedule or on demand
2. For each entry with a recorded digest, the current digest is computed
3. Unchanged entries produce nothing
4. A changed entry produces a `ContentObservation`: both digests, provenance
   `external`, and the writing identity when `attributable_writes` is attested
5. An unreadable entry produces an observation with state `unknown` — never
   `stale`, never `current`, and never a deletion
6. Observations are recorded and surfaced. **No observation from this flow is
   an integrity anomaly**; that classification belongs to exclusive custody

### Custody Re-verification Flow
1. On declaration and on a schedule, each attestation property is tested
2. A property that cannot be demonstrated becomes `false`
3. The ceiling is recomputed
4. If the ceiling dropped, `content.custody_degraded` is published naming the
   content now sitting above it. Existing content is not moved and not
   reclassified — it is reported

---

## Registration and Standalone Operation

The content service is a component in the mesh: it registers with the
orchestrator, claims the `content.*` namespace exclusively, and verifies caller
tokens against the orchestrator's public key.

Its manifest declares `protocol_version` `"1"` — the wire protocol version from
[`protocol/types`](../protocol/types.md), **not** the component's own semver —
and these capabilities, which are the `content:` family that document declares:

| Capability | Guards |
|---|---|
| `content:read` | `GET /v1/content`, `GET /v1/content/entry`, `GET /v1/content/stat` |
| `content:write` | `PUT /v1/content/entry`, `DELETE /v1/content/entry` |
| `content:describe` | `GET /v1/content/repositories` |
| `content:reconcile` | `POST /v1/content/reconcile` |

A capability name is `family:verb`. An invented name is refused at registration,
so these MUST be the names `protocol/types` declares and no others.

### Startup Sequence

The order is not free, because the key this service authenticates with arrives
in the registration response:

```
1. Load configuration and open storage
2. Load or generate the ML-DSA-65 key pair
3. Verify each declared repository's custody attestations
4. Construct the authenticator WITHOUT an issuer key — it refuses every token
   until one arrives, which is the correct standalone behaviour
5. Register HTTP routes and start listening
6. Register with the orchestrator, if an orchestrator URL is configured
7. On the registration response, set the issuer public key on the authenticator
8. Start the reconcile and re-verify loops
9. Serve until signalled
```

Steps 4 to 7 are stated because the obvious order fails in a way that cannot
recover: a service that requires the orchestrator's public key in order to
construct its authenticator exits before step 6, so it can never obtain the key
it refused to start without.

**An orchestrator is not required in order to start.** Where no orchestrator URL
is configured:

- The service MUST start and MUST serve `GET /v1/health` unauthenticated.
- Every protected endpoint MUST refuse with `401` and a structured
  `ErrorResponse`. It holds no issuer key, so it can verify no token, and a
  component that cannot verify a token MUST NOT accept one.
- Health MUST report `degraded`, naming the absent orchestrator. It MUST NOT
  report `healthy`, because the service cannot serve its purpose, and MUST NOT
  report `unhealthy`, because nothing about it has failed.

Where an orchestrator URL IS configured, registration failure is fatal: a
service that believes it is part of a mesh and is not would answer requests
under an authority nobody granted.

This is stated because the alternative is not obvious and is wrong in a
specific way. Making the orchestrator key mandatory at startup means the
component cannot be built, tested or conformance-checked in isolation — it
exits before serving anything, and the failure is reported as a component that
does not work rather than a component that was not given a mesh.

---

## Design Principles

1. **Custody is a property of the store, not of the content** — what a
   repository can guarantee is decided by who else can reach its bytes, never by
   how sensitive the material in it is. A classification states what protection
   content deserves; custody states what protection the place can actually
   deliver. Where they disagree the place wins, because the content does not
   enforce itself.

2. **An unproven property is false** — an attestation MUST be demonstrated
   before it takes effect. A repository that has not been verified, or that
   declares nothing, MUST be treated as conceding everything. Assuming a
   protection nobody checked is how a system comes to report a guarantee it
   never had.

3. **Refuse, never downgrade** — a write above a repository's ceiling MUST be
   refused and MUST NOT be silently reclassified to fit. A level the system
   lowered on the author's behalf is a classification nobody made, and the
   record then understates its own content.

4. **A second writer is expected, not hostile** — where custody is shared, a
   change this service did not make is ordinary. It MUST be detected, recorded
   with `external` provenance, and surfaced. It MUST NOT be reported as
   tampering. A control that alarms on normal work is switched off, and a
   switched-off control is worse than one never claimed.

5. **State the limit with the answer** — any statement about access from a
   shared or opaque repository MUST carry that it is incomplete. This service
   sees the path through it and cannot see the path around it. A partial record
   labelled partial is evidence; the same record labelled complete is a false
   statement about everything else the system says.

6. **The blueprint names a contract, never a product** — as
   [`architecture/storage`](storage.md) Design Principle 6 requires, this
   document specifies operations and guarantees. It does not name a filesystem,
   a share protocol, a version control system or a vendor, and no implementation
   is non-conformant for the backend it satisfies the contract with.

---

## The Custody Model

A repository's custody states **who else can reach the bytes**. It is the
property from which every other guarantee in this document is derived.

| Custody | Definition |
|---|---|
| `exclusive` | No authority other than this tenant's own service can read or write the bytes |
| `shared` | Another authority can read or write the same bytes, and that authority is identifiable |
| `opaque` | Another authority may exist and cannot be enumerated |

**An undeclared repository is `opaque`.** Custody MUST NOT be inferred from a
path, a URL or a provider name. A backend that has not stated what it concedes
MUST be treated as conceding everything, because the alternative is to assume a
protection nobody verified.

### Attestation Properties

Custody alone is too coarse to set a ceiling — two shared backends can differ
enormously. Three properties determine what a repository can actually attest:

| Property | Question it answers | Attested when |
|---|---|---|
| `enumerable_principals` | Who else can reach this content? | The backend can list every principal holding read or write access, and the list can be re-read on demand |
| `attributable_writes` | Who made this change? | An out-of-band write carries an identity the service can record |
| `tamper_evident` | What happened between our reads? | The backend exposes a history the service can traverse, or reveals modification in a way that cannot be forged by an ordinary writer |

A property MUST be recorded `true` only when demonstrated. `unknown` MUST be
recorded as `false` — this follows `patterns/content-identity` Design Principle 4 and its
`unknown` verdict: a system that cannot check has not established the fact.

### Derived Scope Ceiling

The highest `ScopeLevel` that MAY be placed in a repository is derived from its
custody and attestations. It MUST be computed and MUST NOT be configured.

| Custody | Attestations | Ceiling | Rationale |
|---|---|---|---|
| `exclusive` | — | `critical` | One authority; the full integrity model of `architecture/data-security` applies as written |
| `shared` | all three | `restricted` | Access is enumerable, change is attributable and history is visible. Approval and masking remain enforceable; sole custody does not |
| `shared` | `enumerable_principals` only | `confidential` | Access can be stated and audited on our side, but a change cannot be attributed |
| `shared` | fewer | `internal` | Neither access nor change can be established |
| `opaque` | — | `internal` | Nothing can be established about who else holds the bytes |

A write whose declared scope exceeds the repository's ceiling MUST be refused
with `CONTENT_CUSTODY_CEILING_EXCEEDED`, and the refusal MUST name both levels.
It MUST be refused at the boundary, and MUST NOT be downgraded or merely warned
about — a classification
the system quietly lowered is a classification nobody made.

**The ceiling is a property of placement, not of intent.** Moving a document
from an exclusive repository to a shared one is a scope event, and the service
MUST refuse the move rather than silently reclassify the document.

### What Shared Custody Changes

`architecture/data-security` Storage Integrity Verification treats a record
with no corresponding enforcement audit entry as an integrity anomaly. That
inference is sound under exclusive custody and **invalid under shared custody**,
where an authorised person editing a document out-of-band produces exactly that
signature. Under shared custody:

- An unexplained change MUST be recorded as `external` provenance and surfaced.
  It is **not** an integrity anomaly and **MUST NOT** raise a tampering alert.
- A digest that changed between reads MUST yield a `ContentObservation`, not a
  violation.
- Any statement about who has accessed content **MUST** carry
  `access_complete: false`. The service's audit trail covers the path through
  it and cannot cover the path around it.

The last point is the one that matters to an auditor. A partial access record
labelled partial is evidence. The same record labelled complete is a false
statement, and the system that made it cannot be trusted about the rest.

---

## Types

```yaml
types:
  ContentRepository:
    description: A declared content store with its custody posture
    fields:
      id:
        type: string
        required: true
        description: Stable identifier, survives rename and re-placement
      scope_path:
        type: string
        required: true
        description: tenant/org/project confinement this repository belongs to
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: true
        description: Who else can reach the bytes. Undeclared is opaque
      attestations:
        type: CustodyAttestations
        required: true
      ceiling:
        type: ScopeLevel
        required: true
        description: Derived from custody and attestations. Never configured
      verified_at:
        type: timestamp
        required: false
        description: When attestations were last demonstrated. Absent means never

  CustodyAttestations:
    description: What a repository can demonstrate. Unknown is recorded as false
    fields:
      enumerable_principals:
        type: boolean
        required: true
      attributable_writes:
        type: boolean
        required: true
      tamper_evident:
        type: boolean
        required: true

  ContentEntry:
    description: One addressable entry in a repository
    fields:
      path:
        type: string
        required: true
        description: Repository-relative path. The name, not the identity
      identity:
        type: ContentIdentity
        required: true
        description: Digest of the exact stored bytes
      scope:
        type: ScopeLevel
        required: true
      modified_at:
        type: timestamp
        required: true
      provenance:
        type: enum
        values: [authored, external, unknown]
        required: true
        description: authored when this service wrote it; external when another
          authority did; unknown when it cannot be established

  ContentChange:
    description: A change this service made, recorded at the time it was made
    fields:
      repository:
        type: string
        required: true
      path:
        type: string
        required: true
      operation:
        type: enum
        values: [create, modify, delete]
        required: true
      before:
        type: ContentIdentity
        required: false
        description: Absent on create
      after:
        type: ContentIdentity
        required: false
        description: Absent on delete
      actor:
        type: string
        required: true
      correlation_id:
        type: string
        required: true
        description: The enforcement decision that authorised this change
      recorded_at:
        type: timestamp
        required: true

  ContentObservation:
    description: A change this service did not make, observed after the fact
    fields:
      repository:
        type: string
        required: true
      path:
        type: string
        required: true
      recorded_digest:
        type: string
        required: false
      current_digest:
        type: string
        required: false
        description: Absent when the entry could not be read
      state:
        type: enum
        values: [changed, removed, unknown]
        required: true
      writer:
        type: string
        required: false
        description: Present only when attributable_writes is attested
      observed_at:
        type: timestamp
        required: true

  AccessStatement:
    description: An answer about who has reached content, honest about its limits
    fields:
      repository:
        type: string
        required: true
      entries:
        type: list
        required: true
      access_complete:
        type: boolean
        required: true
        description: False whenever custody is shared or opaque. The service
          cannot see the path around itself
      principals:
        type: list
        required: false
        description: Present only when enumerable_principals is attested
```

---

## Configuration

```yaml
content:
  repositories:
    - id: <stable-id>
      scope_path: <tenant>/<org>[/<project>]
      custody: exclusive|shared|opaque
      attestations:
        enumerable_principals: <bool>
        attributable_writes: <bool>
        tamper_evident: <bool>
  reconcile_interval: 15m        # shared custody only; 0 disables scheduled runs
  reverify_custody_interval: 24h
  max_entry_bytes: 10485760
```

Configuration declares what a repository **claims**. Every claim is
demonstrated before it takes effect: an attestation asserted here and not
demonstrated at verification becomes `false`, and the ceiling follows the
demonstration, not the claim.

---

## Security

```yaml
security:
  trust_model:
    description: |
      The service trusts its own writes and nothing else. Under exclusive
      custody it is the only writer and its records are the whole history.
      Under shared custody it is one writer among several, its records are
      partial by construction, and every statement it makes about access or
      history carries that limit explicitly. Custody is fail-closed:
      undeclared means opaque, unverified means false, and the ceiling
      follows what was demonstrated rather than what was claimed.

  boundaries:
    - boundary: Caller → Content Service. Every path is confined to one
        repository within the caller's scope before any I/O occurs
    - boundary: Content Service → Enforcement. Every operation passes the
        storage proxy; the service supplies resource scope and custody facts
        and does not make the access decision
    - boundary: Content Service → Backend. The only boundary the service does
        not control on both sides. Everything beyond it is attested or unknown
    - boundary: Content → Installation state. `.weblisk/` holds keys, secrets
        and run state and is never reachable through this service

  enforcement:
    - rule: A write without a precondition digest is refused
      mechanism: Precondition Gate; if_match is a required parameter
    - rule: A write whose scope exceeds the repository ceiling is refused, never
        downgraded
      mechanism: Ceiling check before the storage proxy, publishing
        content.ceiling_exceeded
    - rule: An undeclared or unverified repository is treated as opaque
      mechanism: Registry default; attestation defaults to false
    - rule: A path containing a traversal segment or resolving outside the
        repository through a symlink is refused as written
      mechanism: Path Resolver; refusal rather than normalisation
    - rule: A path resolving into installation state is refused
      mechanism: Reserved-path check in the resolver, applied to every operation
    - rule: An access statement from a shared or opaque repository is marked
        incomplete
      mechanism: access_complete is derived from custody and cannot be set by
        a caller
    - rule: An out-of-band change under shared custody is recorded as external
        provenance, not as an integrity anomaly
      mechanism: Custody Reconciler; the anomaly rules of
        architecture/data-security apply to exclusive custody only
    - rule: Reading never changes stored bytes
      mechanism: patterns/content-identity read-without-mutation; demonstrated
        by digesting a corpus before and after a full read pass
```

---

## Implementation Notes

- **Compute the digest from what was written, not what was submitted.** Reading
  back after a write costs one read and is the only way the recorded identity is
  the identity of the bytes on the backend. A digest of the request body is a
  digest of an intention.

- **Refuse traversal, do not clean it.** `filepath.Clean("/../x")` yields `/x`,
  which is inside the repository and is not what the caller asked for. Answering
  a different question quietly is the failure mode this avoids.

- **Resolve symlinks on the deepest existing ancestor.** A textual containment
  check validates the requested path only; the write follows links. For a path
  that does not exist yet, the final component cannot be a link, so resolving
  its nearest existing ancestor is sufficient.

- **Custody is a property of the connection, established once and re-verified
  on a schedule** — not re-derived per request. Per-request derivation makes the
  ceiling a function of transient backend behaviour, and a ceiling that moves
  under load is not a control.

- **Do not implement reconciliation under exclusive custody.** There is no
  second writer, so every difference is genuinely an anomaly and belongs to
  `architecture/data-security`. Running the reconciler there would reclassify
  real tampering as an ordinary external edit — the inverse of the bug this
  model exists to fix.

- **`access_complete: false` is not a defect to be fixed later.** It is the
  correct answer for shared custody and must survive into every report,
  export and evidence package that quotes it. A downstream consumer that drops
  the flag has turned a qualified statement into a false one.

- **The backend adapter surface is deliberately five operations** — read, write,
  list, stat, delete. A backend that cannot express one of them is not
  disqualified; it declares the corresponding attestation `false` and accepts
  the lower ceiling.

- **Retirement, not deletion.** A removed entry's identity is retired per
  `patterns/content-identity` Design Principle 6. A reference to it resolves to
  "removed at version N", never to nothing and never to a later entry that
  reused the path.

---

## Verification Checklist

- [ ] A write submitted without `if_match` is refused with `CONTENT_IF_MATCH_REQUIRED`
- [ ] A write whose `if_match` differs from the stored digest is refused with both digests returned, and the stored bytes are unchanged
- [ ] The digest recorded after a write equals the digest of the bytes read back from the backend
- [ ] A full read pass over a corpus leaves every entry's digest unchanged
- [ ] A repository with no declared custody reports `custody: opaque` and a ceiling of `internal`
- [ ] An attestation declared in configuration but not demonstrated at verification resolves to `false`, and the ceiling reflects the demonstrated set
- [ ] A write declaring a scope above the repository ceiling is refused with `CONTENT_CUSTODY_CEILING_EXCEEDED` naming both levels, and the scope is not downgraded
- [ ] An out-of-band change under shared custody produces a `ContentObservation` with provenance `external` and raises no tampering alert
- [ ] An out-of-band change under exclusive custody is not produced by the reconciler, which is absent for exclusive repositories
- [ ] An `AccessStatement` from a shared or opaque repository carries `access_complete: false`, and no caller can set it to true
- [ ] A path containing a `..` segment is refused as written rather than normalised
- [ ] A symlink inside a repository pointing outside it is refused
- [ ] A path resolving into `.weblisk/` is refused for every operation including list and stat
- [ ] An unreadable entry yields state `unknown`, never `stale`, `current` or `removed`
- [ ] A repository whose re-verification lowers its ceiling publishes `content.custody_degraded` naming the content now above it, and no content is moved or reclassified
- [ ] Every content operation appears in the enforcement audit trail with the correlation id recorded on the resulting `ContentChange`
- [ ] With no orchestrator URL configured, the service starts, serves `GET /v1/health`, and does not exit
- [ ] With no orchestrator URL configured, every protected endpoint refuses with `401` and a structured `ErrorResponse`
- [ ] With no orchestrator URL configured, health reports `degraded` and names the absent orchestrator — never `healthy`, never `unhealthy`
- [ ] With an orchestrator URL configured, a failed registration is fatal
