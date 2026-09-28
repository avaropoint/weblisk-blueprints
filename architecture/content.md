<!-- blueprint
type: architecture
name: content
version: 1.8.0
requires: [protocol/types, protocol/identity, patterns/content-identity, patterns/scope, patterns/contract, patterns/principal-identity, patterns/approval, patterns/secrets, architecture/enforcement]
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
        - name: ProposedChange
          fields_used: [path, action]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.4.0 <2.0.0"
    bindings:
      types:
        # identity_id is who a change names; type says whose token it is
        - name: WLToken
          fields_used: [cap, identity_id, type]
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

  - blueprint: patterns/principal-identity
    version: ">=1.5.0 <2.0.0"
    bindings:
      behaviors:
        # What keeps a person-only capability away from a service and an agent
        - name: service-subject-constraints
        - name: agent-delegation
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/approval
    version: ">=1.1.0 <2.0.0"
    bindings:
      behaviors:
        # Its self-approval rejection, and the one exception it names for a
        # content proposal (see Separation of duties)
        - name: approval-decision
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/secrets
    version: ">=1.1.0 <2.0.0"
    bindings:
      behaviors:
        # How a replica's credential is held (see Declaring a replica)
        - name: secret-access
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
│  │  - reserved-path refusal (installation and         │  │
│  │    control state)                                  │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Precondition Gate                                 │  │
│  │  - if_match digest compared before every write     │  │
│  │  - refuses on mismatch; never merges               │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Proposal Store                                    │  │
│  │  - changes staged for a person to decide           │  │
│  │  - held in the service's own state, never content  │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Custody Reconciler        (shared custody only)   │  │
│  │  - detects out-of-band change by digest            │  │
│  │  - records provenance: authored | external         │  │
│  │  - never classifies external change as tampering   │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Replica Sender            (push-only)             │  │
│  │  - sends each replica what it lacks, in order      │  │
│  │  - from the service's own record, never the store  │  │
│  │  - never reads from a replica                      │  │
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

**Precondition Gate** compares a caller-supplied `if_match` against the stored
bytes before writing. `if_match` is the digest of the bytes the caller believes
the path holds, or the empty string when it believes the path holds nothing.
Both are preconditions, and either can fail: a digest where nothing is there,
or the empty string where an entry is. An absent `if_match` is no
precondition, and no value matches whatever is there. This is the whole of the
concurrency model — there is no merge, no last-writer-wins and no lock.

**Proposal Store** holds changes that were proposed and not yet decided. A
proposal is not content until a person applies it, so its bytes live in the
service's own record store, under exclusive custody, and never in the
repository. They are read only through the Proposal Read Flow, under the same
check as the entry they would change. See [Proposals](#proposals).

**Custody Reconciler** exists only where a second authority can write. It
converts an unexplained change from an alarm into a recorded fact.

**Replica Sender** sends each of a repository's replicas what it has not yet
received, and takes nothing back. See [Replicas](#replicas).

---

## Responsibilities

### Owns
- The content repository contract — list, read, write, delete, stat over a
  confined tree
- Declaration: what it takes to bring a store under governance, and the
  difference between establishing an empty one and adopting one that is not
- Establishment: bringing a store into existence — how a placement is named,
  what the backend owes once the store exists, and the ordering that makes a
  create which did not finish recoverable rather than orphaned
- The custody model: classification, attestation properties, and the scope
  ceiling derived from them
- Replicas: copies of a repository sent to a second place, the census that
  precedes one, and the effective custody every copy adds to
- Precondition semantics for writes (digest match, refusal on mismatch)
- Proposals: staging a change for a person to decide, the decision, and the
  separation of duties it records
- Who a change was for: the attribution a `ContentChange` carries, and which
  party asserts each part of it
- Out-of-band change detection and provenance recording for shared custody
- Reserved-path refusal for installation state and control state
- Declaration of what a repository cannot attest, as a first-class answer

### Does NOT Own
- Digest algorithm or reference semantics (owned by `patterns/content-identity`)
- Concrete backends — filesystem, share, object store, version control (owned
  by the blueprint that specifies each backend, per `architecture/storage`
  Design Principle 6)
- Binary asset upload, processing and delivery (owned by `patterns/file-upload`)
- Record stores (owned by `architecture/storage`)
- The access decision itself (owned by `architecture/enforcement`; this service
  supplies the resource scope and custody facts the decision is made from)
- The backend's own permission system — this service reads it where it can and
  declares it unknown where it cannot; it never administers it

---

## Endpoints

| Method | Path | Operation | Auth | Purpose |
|--------|------|-----------|------|---------|
| GET | /v1/content | List | yes | List entries beneath a path, cursor-paginated |
| GET | /v1/content/entry | Read | yes | Read one entry's bytes and identity |
| PUT | /v1/content/entry | Write | yes | Write one entry; `if_match` required |
| DELETE | /v1/content/entry | Remove | yes | Remove one entry and retire its identity |
| GET | /v1/content/stat | Stat | yes | Identity and metadata without transferring bytes |
| GET | /v1/content/repositories | Repositories | yes | Repositories in scope, with custody and ceiling |
| POST | /v1/content/repositories | DeclareRepository | yes | Bring a store under governance — establish, which creates an empty one, or adopt one that already holds bytes |
| POST | /v1/content/repositories/{repository}/replicas | DeclareReplica | yes | Declare a replica of a repository. Without `if_match`, returns the census of what would leave and declares nothing |
| GET | /v1/content/repositories/{repository}/replicas | Replicas | yes | A repository's replicas, retired ones included, with state and ceiling |
| DELETE | /v1/content/repositories/{repository}/replicas/{replica} | RetireReplica | yes | Stop sending to a replica. Deletes nothing at its destination |
| POST | /v1/content/reconcile | Reconcile | yes | Detect out-of-band change (shared custody only) |
| POST | /v1/content/proposals | Propose | yes | Stage a change to one entry for a person to decide. Writes no entry |
| GET | /v1/content/proposals | Proposals | yes | List proposals in scope, cursor-paginated |
| GET | /v1/content/proposals/{id} | Proposal | yes | Read one proposal, with the bytes it proposes, under the entry's own read check |
| POST | /v1/content/proposals/{id}/decision | Decide | yes | Apply or reject a proposal. Applying writes the entry |
| GET | /v1/health | Health | no | Content service health. Served with or without an orchestrator |

**An entry's bytes travel as base64.** Wherever a JSON body carries an entry's
bytes — the response of `GET /v1/content/entry`, the request of
`PUT /v1/content/entry`, and the `bytes` of a proposal — they are one string
of standard base64 (RFC 4648 §4, with padding). They are never carried as
text. An entry is any bytes, and a JSON parser may replace bytes that are not
valid UTF-8 before the service sees them, so a digest computed after it would
be the digest of bytes nobody sent. A string that is not valid base64 is
refused with `INVALID_REQUEST` ([`protocol/spec`](../protocol/spec.md)).

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
      methods: [GET, POST]
      description: GET lists repositories visible in the caller's scope, with
        custody, attestations, derived ceiling, and the ones that were declined.
        POST declares one. establish creates an empty store at the placement
        and declares it; adopt takes on one that already holds bytes and
        requires if_match over a census the service issued
      served_by: content-service

    - path: /v1/content/repositories/{repository}/replicas
      methods: [GET, POST]
      description: GET lists a repository's replicas, retired ones included.
        POST declares one. Without if_match it returns the census of what
        would leave and declares nothing; with it, it reserves the replica,
        creates its credential, demonstrates the destination and confirms
      served_by: content-service

    - path: /v1/content/repositories/{repository}/replicas/{replica}
      methods: [DELETE]
      description: Retire a replica. Nothing more is sent to it, its
        credential is destroyed, its record stays, and nothing at its
        destination is deleted
      served_by: content-service

    - path: /v1/content/reconcile
      methods: [POST]
      description: Compare recorded digests against current bytes for a shared
        repository and record observations. Shared custody only
      served_by: content-service

    - path: /v1/content/proposals
      methods: [GET, POST]
      description: POST stages a change to one entry for a person to decide,
        and writes nothing. GET lists proposals in the caller's scope,
        cursor-paginated
      served_by: content-service

    - path: /v1/content/proposals/{id}
      methods: [GET]
      description: Read one proposal, with the bytes it proposes, for a caller
        the enforcement storage proxy allows to read the entry it would change
      served_by: content-service

    - path: /v1/content/proposals/{id}/decision
      methods: [POST]
      description: Apply or reject a proposal. Applying writes the entry
        through the Write Flow, against the bytes the proposal was made on. A
        proposal whose base has moved on is recorded stale and nothing is
        written
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
      description: Replace bytes when the precondition holds; refuse otherwise.
        Called for a person, never for an agent — content:write is person only
      called_by: [gateway]

    - name: DeleteEntry
      signature: (repository, path, if_match) → ContentChange
      description: Remove an entry and retire its identity. Called for a
        person, never for an agent — content:write is person only
      called_by: [gateway]

    - name: DescribeRepository
      signature: repository → ContentRepository
      description: Custody, attestations and derived ceiling
      called_by: [gateway, agents, admin]

    - name: DeclareRepository
      signature: (declaration, if_match) → (ContentRepository, ContentAdoption)
      description: Bring a store under governance. Creates an empty store and
        declares it, or adopts an existing one against a census the service
        issued. Returns the census and declares nothing when adoption is
        attempted unseen, and reports a create that did not finish rather than
        rolling it back
      called_by: [admin, agents]

    - name: DeclareReplica
      signature: (repository, ReplicaDeclaration) → (ContentReplica, ReplicaCensus)
      description: Declare a replica. Returns the census and declares nothing
        when attempted unseen, and reports a declaration that did not finish
        rather than rolling it back. Called for a person, never for an agent —
        content:replicate and content:connect are person only
      called_by: [gateway]

    - name: ListReplicas
      signature: repository → [ContentReplica]
      description: A repository's replicas, retired ones included
      called_by: [gateway, agents, admin]

    - name: RetireReplica
      signature: (repository, replica) → ContentReplica
      description: Stop sending to a replica and destroy its credential.
        Called for a person — content:replicate is person only
      called_by: [gateway]

    - name: Reconcile
      signature: (repository, since_cursor) → [ContentObservation]
      description: Detect and record out-of-band change. Shared custody only
      called_by: [content-service, agents]

    - name: ProposeChange
      signature: ProposalRequest → ContentProposal
      description: Record a change to one entry without making it
      called_by: [gateway, agents]

    - name: ListProposals
      signature: ProposalQuery → ProposalPage
      description: Proposals in the caller's scope, filtered by repository,
        path and state. Omits, and counts, any the caller may not read
      called_by: [gateway, agents]

    - name: ReadProposal
      signature: id → ContentProposal
      description: One proposal, including the bytes it proposes, for a caller
        who may read the entry it would change
      called_by: [gateway, agents]

    - name: DecideProposal
      signature: (id, DecisionRequest) → ContentProposal
      description: Apply or reject a proposal. Called for a person, never for
        an agent — content:decide is person only
      called_by: [gateway]

  events:
    - topic: content.repository_declared
      direction: publish
      description: A store came under governance, with its disposition, derived
        ceiling and — on adoption — how many entries it arrived holding

    - topic: content.changed
      direction: publish
      description: An entry's identity changed, with provenance authored or external

    - topic: content.custody_degraded
      direction: publish
      description: A repository's ceiling has dropped — its store's
        attestations or a replica's were re-verified weaker than before, a
        replica was confirmed with a lower ceiling, or its backend found a
        copy nobody declared — naming the content now above the ceiling

    - topic: content.replica_declared
      direction: publish
      description: A replica was confirmed, with who holds its destination,
        its ceiling and the repository's ceiling as it now stands

    - topic: content.replica_state
      direction: publish
      description: A replica's state changed — behind, diverged, unreachable,
        current — naming a held version's path and why it is held. Never
        carries bytes

    - topic: content.replica_retired
      direction: publish
      description: A replica was retired, naming who retired it. Its
        destination still holds what was sent

    - topic: content.ceiling_exceeded
      direction: publish
      description: A write was refused because its scope exceeded the ceiling

    - topic: content.proposed
      direction: publish
      description: A change to an entry was proposed. Nothing was written.
        Carries the proposal's id, repository, path and action, never the
        proposed bytes

    - topic: content.proposal_decided
      direction: publish
      description: A proposal left open — applied, rejected or stale — naming
        who decided it and, when applied, the separation recorded. Never
        carries the proposed bytes
```

---

## Error Handling

| Code | Category | When | Behaviour |
|---|---|---|---|
| `CONTENT_PRECONDITION_FAILED` | conflict | `if_match` does not equal the identity of what it names — an entry's stored digest on a write or a proposal, a placement's census digest on an adoption, a replica census's digest on a replica declaration, a proposal's `before` on a decision to apply it. The empty string where an entry exists, on a write, a proposal to create, or a decision to apply one | Refuse. Return both digests. Never merge, never overwrite, never adopt. On a decision to apply, record the proposal `stale` and write nothing |
| `CONTENT_IF_MATCH_REQUIRED` | validation | A write, a removal or a proposal arrived with no `if_match`. The empty string is a precondition, not its absence | Refuse. A write with no precondition is a blind overwrite, and a proposal with none cannot be told stale |
| `CONTENT_CUSTODY_CEILING_EXCEEDED` | policy | Declared scope exceeds the repository ceiling, or something a replica would receive exceeds that replica's ceiling | Refuse, naming required and actual, and on a replica each path above it. Never downgrade the scope |
| `CONTENT_CUSTODY_UNDECLARED` | policy | Repository has no declared custody | Treat as `opaque`, apply the `internal` ceiling, and record the degradation |
| `CONTENT_PATH_REFUSED` | validation | Traversal segment or escaping symlink — including a placement locator that is absolute, carries a scheme or an authority, or climbs out of its backend's root | Refuse the request as written. Do not normalise and proceed |
| `CONTENT_RESERVED_PATH` | policy | A segment of the path, or of a placement's locator, is a reserved name — `.weblisk` or `.git` — as any filesystem could resolve it, or the backend's blueprint reserves the path — including a path in anything a replica would receive. See [Reserved Paths](#reserved-paths) | Refuse, for every operation including list, stat, propose, declare and declaring a replica. Installation state and control state are never content, and never leave |
| `CONTENT_UNREADABLE` | io | Bytes cannot be read | Identity is `unknown`, never `current` and never `stale` |
| `CONTENT_REPOSITORY_UNKNOWN` | validation | No repository of that id in the caller's scope | Refuse without disclosing whether it exists elsewhere |
| `CONTENT_DISPOSITION_REQUIRED` | validation | A declaration arrived without a disposition | Refuse. A declaration that does not say whether it expects bytes is a blind adoption |
| `CONTENT_REPOSITORY_EXISTS` | conflict | The id is already declared at that `scope_path`, or is reserved there by an unfinished establish whose arguments differ from this request's | Refuse, naming the declared repository's placement. Never re-declare in place. An identical retry against an unfinished establish is a resumption, not this |
| `CONTENT_ADOPTION_UNSEEN` | conflict | `disposition: adopt` with no `if_match` | Refuse and return the `ContentAdoption` census. Nothing is declared. The caller re-submits with the census digest |
| `CONTENT_NOT_EMPTY` | conflict | `disposition: establish` and the placement already holds entries, including on a resumed establish whose store has since been written to; or a replica's destination holds something this service would not send | Refuse. Establishing over bytes somebody else wrote is adoption under the wrong word, and sending over them would overwrite them |
| `CONTENT_BACKEND_UNKNOWN` | validation | The placement names a backend this service does not hold for that `scope_path` | Refuse without disclosing whether the name exists under another scope |
| `CONTENT_ESTABLISH_UNSUPPORTED` | policy | `disposition: establish` against a backend that cannot bring a store into existence, or cannot represent an empty one without an entry in it | Refuse. Never write a placeholder to make the store representable. `adopt` against the same backend is unaffected |
| `CONTENT_ESTABLISH_INCOMPLETE` | partial | The declaration was reserved and the create or the custody demonstration did not finish; or a replica was reserved and its credential, or the demonstration of its destination, did not finish | Report what completed, carrying the `ContentRepository` and its `RepositoryEstablishment`, or the `ContentReplica` with its `ReplicaEstablishment` and credential. Roll nothing back, claim no success, and do not report that nothing happened |
| `CONTENT_PRECONDITION_NOT_APPLICABLE` | validation | `if_match` does not fit the act: any `if_match` with `disposition: establish`; the empty string on a removal, or on a proposal to modify or remove; a digest on a proposal to create | Refuse. A precondition that contradicts the act, or that nothing can evaluate, must not be accepted as though it held |
| `CONTENT_PLACEMENT_DECLARED` | conflict | The placement is equal to, inside, or contains an already-declared repository; or a replica's destination is equal to, inside or contains a declared repository's placement or another replica's destination | Refuse. Two ceilings over one set of bytes means the lower one is unenforceable, and a replica sent into a store would make a copy a source |
| `CONTENT_PROPOSAL_UNKNOWN` | validation | No proposal of that id in the caller's scope | Refuse without disclosing whether it exists elsewhere |
| `CONTENT_PROPOSAL_DECIDED` | conflict | A decision arrived for a proposal that is no longer `open`, including the second of two decisions that raced | Refuse, returning the proposal as recorded. A proposal leaves `open` once |
| `CONTENT_SEPARATION_REQUIRED` | policy | A decision to apply was made by the identity the proposal names as its `actor` or its `on_behalf_of`, and the change's scope is above the repository's `self_decision_ceiling`, or the repository declares none | Refuse, naming the scope and the ceiling. Nothing is recorded and the proposal stays `open` |
| `CONTENT_IDENTITY_REQUIRED` | auth | A write, removal, proposal, decision, replica declaration or retirement arrived on a token that carries no `identity_id` | Refuse. Never record a name, an address or a token's `sub` in its place |
| `CONTENT_REPLICA_UNSEEN` | conflict | A replica declaration with no `if_match` | Refuse and return the `ReplicaCensus`. Nothing is recorded and nothing is sent. The caller re-submits with the census digest |
| `CONTENT_REPLICA_UNCLASSIFIED` | policy | A replica declaration whose destination a third party holds, where the classification gate is not present or does not pass. See [A third party's replica waits for classification](#a-third-partys-replica-waits-for-classification) | Refuse. Nothing is recorded and nothing is sent |
| `CONTENT_REPLICA_EXISTS` | conflict | The replica id is taken in that repository, by a replica that is not `establishing` or whose recorded arguments differ from this request's | Refuse, naming the recorded destination. An identical retry against an `establishing` replica is a resumption, not this |
| `CONTENT_REPLICA_UNKNOWN` | validation | No replica of that id in that repository | Refuse |
| `CONTENT_REPLICA_UNSUPPORTED` | policy | The destination's backend cannot receive a replica, or cannot receive one of the repository's backend | Refuse. Nothing is recorded |
| `ENFORCEMENT_DATA_CONTRACT_VIOLATION` | enforcement | Path is outside the agent's declared operational data contract | Refuse via the storage proxy |

---

## Data Flow

### Declaration Flow
1. Caller submits a `RepositoryDeclaration`: an id, a `scope_path`, a
   `placement`, a claimed custody, claimed attestations, and a required
   `disposition`
2. Enforcement storage proxy intercepts with operation `create` and the declared
   `scope_path` as the resource scope. An out-of-scope declaration is refused
   there, not here — this service supplies the scope and does not make the
   decision
3. The placement is resolved: its backend must be one this service holds for
   that `scope_path` (`CONTENT_BACKEND_UNKNOWN`), and its locator is confined to
   that backend's root by the same Path Resolver every entry passes through,
   refused as written rather than normalised (`CONTENT_PATH_REFUSED`, or
   `CONTENT_RESERVED_PATH` for a reserved segment)
4. Registry checks: the id must be free at that `scope_path`
   (`CONTENT_REPOSITORY_EXISTS`), and the placement must not be equal to, inside
   or containing a placement already declared (`CONTENT_PLACEMENT_DECLARED`).
   A declaration carrying `self_decision_ceiling` MUST come from a caller
   holding `content:decide` as well as `content:declare`
5. `establish` — the caller MUST hold `content:establish` as well as
   `content:declare`; a backend that cannot create is refused with
   `CONTENT_ESTABLISH_UNSUPPORTED`; a placement already holding entries is
   refused with `CONTENT_NOT_EMPTY`. The declaration is then **reserved** —
   recorded durably with `state: establishing`, governing nothing — and only
   then is the adapter asked to create the store. A reservation whose recorded
   arguments equal this request's is resumed from where it stopped; the store is
   never created twice
6. `adopt` — the service computes a `ContentAdoption` census over the placement.
   With no `if_match`, it returns the census, refuses with
   `CONTENT_ADOPTION_UNSEEN`, and declares nothing. With an `if_match` that does
   not equal the census digest it has just computed, it refuses with
   `CONTENT_PRECONDITION_FAILED` and returns both digests. `adopt` never creates
7. Each claimed attestation is demonstrated — on `establish`, against the store
   that now exists. An undemonstrated claim becomes `false`; a declaration with
   no custody is recorded `opaque` and the degradation is recorded, per
   `CONTENT_CUSTODY_UNDECLARED`
8. The ceiling is derived from what was demonstrated. It is never taken from the
   request
9. The repository is recorded `state: declared`. On adoption, every entry the
   census found is recorded with provenance `unknown` — the service did not
   write them and observed no change, so it can establish nothing about them
10. `content.repository_declared` is published, carrying the disposition, the
    derived ceiling and the adopted entry count
11. Should step 5's create or step 7's demonstration fail, nothing is rolled
    back and nothing is hidden: the repository stays `establishing` and the
    caller is answered with `CONTENT_ESTABLISH_INCOMPLETE` carrying what
    completed

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
   believes it is replacing, or the empty string for an entry it believes does
   not exist yet
2. Path Resolver confines the path as above
3. Ceiling check: declared scope against the repository's derived ceiling.
   Exceeded → refuse, publish `content.ceiling_exceeded`
4. Enforcement storage proxy intercepts with operation `create` when `if_match`
   is the empty string, and `modify` otherwise
5. Precondition Gate reads the current digest and compares it to `if_match`.
   Mismatch → refuse with both digests. No merge is attempted
6. Bytes are written durably; the new digest is computed from what was written,
   not from what was submitted
7. A `ContentChange` is recorded with provenance `authored`, the token's
   `identity_id` for `actor`, and the correlation id of the enforcement
   decision
8. `content.changed` is published

### Proposal Flow
1. Caller submits a `ProposalRequest`: a repository, a `ProposedChange` naming
   the path and the action, `if_match`, and — for `create` and `modify` — the
   proposed `bytes` and their declared scope, with `on_behalf_of`, `agent`,
   `run` and a reason where they apply. An `action` other than `create`,
   `modify` or `delete`, or `bytes` or `scope` missing on a `create` or
   `modify` or present on a `delete`, is refused with `INVALID_REQUEST`
   ([`protocol/spec`](../protocol/spec.md)). `bytes` longer than
   `max_entry_bytes` are refused as a write of that length would be
2. Path Resolver confines the path as for a write; traversal, escaping symlinks
   and reserved paths are refused
3. Ceiling check: declared scope against the repository's derived ceiling.
   Exceeded → refuse, publish `content.ceiling_exceeded`
4. Enforcement storage proxy intercepts with the operation the proposal would
   perform — `create`, `modify` or `delete` — for the proposer
5. Precondition Gate compares `if_match` to the entry's current digest — for
   `create`, the empty string to a path that holds nothing. An `if_match` that
   does not fit the action is refused with
   `CONTENT_PRECONDITION_NOT_APPLICABLE`, and a mismatch with
   `CONTENT_PRECONDITION_FAILED`. A proposal that is stale when made is not
   recorded
6. The service decodes the proposed bytes, holds them in its own state,
   computes `after` over what it holds, and records a `ContentProposal` in
   state `open`, with the token's `identity_id` for `actor` and the
   correlation id of the enforcement decision
7. `content.proposed` is published, carrying no proposed bytes. No entry is
   written

### Proposal Read Flow
1. Caller asks for one proposal by id, or for a page of proposals
2. A proposal must be in the caller's scope (`CONTENT_PROPOSAL_UNKNOWN`)
3. Path Resolver confines the proposal's path to its repository within the
   caller's scope, as for reading the entry. A path it refuses is refused here
4. Enforcement storage proxy intercepts with operation `read`, the proposal's
   path, and for the resource scope the higher of the proposal's `scope` and
   the scope recorded for the entry — the proposal's alone on a `create`, the
   entry's alone on a `delete`. It runs for every caller, the proposer and the
   decider alike: having made a proposal gives no standing to read it later,
   and a decider reads what they are asked to decide only if they may read
   what it would change
5. By id, a denial refuses the request as the Read Flow would refuse the
   entry. In a page, a proposal the check denies is omitted, and `withheld`
   counts the proposals omitted, so a page with nothing to show can be told
   from a page that hid something
6. `base` is computed for each open proposal returned and never stored.
   Proposed bytes are returned only by id

### Decision Flow
1. Caller submits a `DecisionRequest` for one proposal: `apply` or `reject`
2. The proposal must be in the caller's scope (`CONTENT_PROPOSAL_UNKNOWN`) and
   `open` (`CONTENT_PROPOSAL_DECIDED`)
3. `reject` → the decision is recorded, the proposal becomes `rejected`, and
   `content.proposal_decided` is published. Nothing else happens
4. `apply` → separation is checked: a decider whose token's `identity_id` equals
   the proposal's `actor` or its `on_behalf_of` is refused with
   `CONTENT_SEPARATION_REQUIRED` unless the change's scope is at or below the
   repository's `self_decision_ceiling`
5. The write runs for the decider, with the proposal's `before` as `if_match`,
   or the empty string when it has none. For a `create` or `modify`, Write
   Flow steps 2 to 6 run with the proposal's path, bytes and scope. For a
   `delete`, the same steps run as a removal: no bytes and no ceiling check,
   the enforcement storage proxy intercepting with operation `delete`, and the
   entry is removed and its identity retired
6. `before` no longer matches → refuse with `CONTENT_PRECONDITION_FAILED` and
   both digests, record the decision with the proposal `stale`, write nothing,
   and publish `content.proposal_decided`. Any other refusal leaves the
   proposal `open` and records nothing on it
7. A `ContentChange` is recorded with provenance `authored`: `actor` and
   `on_behalf_of` from the proposal, the decider's `identity_id` in
   `approved_by`, the proposal's id in `proposal`, the `separation` step 4
   found, and the correlation id of the decider's enforcement decision. The
   proposal becomes `applied` in the same record write — neither is durable
   without the other
8. `content.changed` and `content.proposal_decided` are published. Neither
   carries the proposed bytes

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
1. On declaration and on a schedule, each attestation property is tested — the
   store's, and each replica's that is not retired, with its `anonymous_read`
2. A property that cannot be demonstrated becomes `false`
3. The backend reports any copy of the store it can see that no replica
   declares
4. The ceiling is recomputed from every place the bytes live (see
   [Effective custody](#effective-custody))
5. If the ceiling dropped, `content.custody_degraded` is published naming the
   content now sitting above it. Existing content is not moved and not
   reclassified — it is reported

### Replica Declaration Flow
1. Caller submits a `ReplicaDeclaration` for a repository: an id, a
   `destination`, a claimed custody, claimed attestations, and `if_match`
2. Enforcement storage proxy intercepts with operation `create` and the
   repository's `scope_path` as the resource scope
3. The caller must hold `content:replicate` and `content:connect`, both on a
   person's token (see [Who may declare a replica](#who-may-declare-a-replica))
4. The destination is resolved as a placement is: its backend must be one this
   service holds for that `scope_path` (`CONTENT_BACKEND_UNKNOWN`) and able to
   receive a replica of the repository's backend
   (`CONTENT_REPLICA_UNSUPPORTED`), and its locator is confined to that
   backend's root (`CONTENT_PATH_REFUSED`, `CONTENT_RESERVED_PATH`). It must not
   be equal to, inside or containing a declared repository's placement or
   another replica's destination (`CONTENT_PLACEMENT_DECLARED`)
5. The id must be free in that repository (`CONTENT_REPLICA_EXISTS`). A replica
   in `establishing` whose recorded id, destination, custody and attestations
   equal this request's is resumed at step 9
6. The service computes a `ReplicaCensus` of what would leave. With no
   `if_match`, it returns the census, refuses with `CONTENT_REPLICA_UNSEEN`, and
   records nothing
7. Checked in order: an `if_match` that does not equal the census digest just
   computed → `CONTENT_PRECONDITION_FAILED`; a reserved path in anything that
   would leave → `CONTENT_RESERVED_PATH`; a destination a third party holds,
   without the classification gate present and passing →
   `CONTENT_REPLICA_UNCLASSIFIED`; anything that would leave above the
   census's prospective replica ceiling → `CONTENT_CUSTODY_CEILING_EXCEEDED`
8. The replica is **reserved** — recorded durably with `state: establishing`,
   sending nothing and counting toward nothing
9. The credential is created and held, unless the reservation already has one
10. The destination is demonstrated with that credential: it holds nothing
    this service would not send (`CONTENT_NOT_EMPTY`); each claimed custody
    property and attestation; and `anonymous_read`. The replica's ceiling is
    derived from what was demonstrated. Anything that would leave above it →
    `CONTENT_CUSTODY_CEILING_EXCEEDED`, and the replica stays `establishing`
11. Effective custody and the repository's ceiling are recomputed, the replica
    becomes `behind`, or `current` when there is nothing to send, and
    `content.replica_declared` is published. Sending begins
12. Should step 9 or 10 not finish, nothing is sent and nothing is rolled back:
    the caller is answered with `CONTENT_ESTABLISH_INCOMPLETE` carrying the
    replica, its `ReplicaEstablishment` and its credential

### Replica Send Flow
1. After each version is recorded, and every `replica_retry_interval`, each
   replica that is neither `establishing` nor `retired` is sent what it lacks,
   oldest first
2. Before sending, the service checks that the destination holds only what the
   service sent it. If it holds anything else, the replica becomes
   `diverged`, what was found is recorded, and nothing is sent
3. A version above the replica's ceiling is held: the replica is `behind`, it
   names the version's path and why, and nothing recorded after it is sent
4. A destination that cannot be reached, or that refuses the credential, makes
   the replica `unreachable` until the next attempt succeeds
5. What was sent is recorded with `checked_at`. With nothing left to send, the
   replica is `current`
6. Each change of state publishes `content.replica_state`

---

## Registration and Standalone Operation

The content service is a component in the mesh: it registers with the
orchestrator, claims the `content.*` namespace exclusively, and verifies caller
tokens against the orchestrator's public key.

Its manifest declares `protocol_version` `"1"` — the wire protocol version from
[`protocol/types`](../protocol/types.md), **not** the component's own semver.
Its routes are guarded by the `content:` family that document declares:

| Capability | Guards |
|---|---|
| `content:read` | `GET /v1/content`, `GET /v1/content/entry`, `GET /v1/content/stat`, `GET /v1/content/proposals`, `GET /v1/content/proposals/{id}` |
| `content:write` | `PUT /v1/content/entry`, `DELETE /v1/content/entry`. Person only |
| `content:propose` | `POST /v1/content/proposals` |
| `content:decide` | `POST /v1/content/proposals/{id}/decision`. Person only |
| `content:describe` | `GET /v1/content/repositories`, `GET /v1/content/repositories/{repository}/replicas` |
| `content:declare` | `POST /v1/content/repositories` |
| `content:establish` | `POST /v1/content/repositories` with `disposition: establish` — required **in addition to** `content:declare`, because creating a store is more than declaring one |
| `content:reconcile` | `POST /v1/content/reconcile` |
| `content:replicate` | `POST /v1/content/repositories/{repository}/replicas`, with `content:connect`; `DELETE /v1/content/repositories/{repository}/replicas/{replica}`. Person only |
| `content:connect` | `POST /v1/content/repositories/{repository}/replicas` — required **in addition to** `content:replicate`, because it gives the tenant a credential that reaches outside its store. Person only |

A capability name is `family:verb`. An invented name is refused at registration,
so these MUST be the names `protocol/types` declares and no others. *Person
only* is `protocol/types`' marking too, and what it does to a grant is
[Who may move an entry](#who-may-move-an-entry).

**Guarding a capability is not holding it.** The capabilities a manifest
declares become the `cap` of the token the orchestrator issues the service at
registration ([`protocol/spec`](../protocol/spec.md), `POST /v1/register`), so
they are what the service may do as a caller as well as what it serves. Its
manifest therefore declares every capability in the table except the four
that are person only: `content:write`, `content:decide`, `content:replicate`
and `content:connect`. It checks those on the requests it serves and never
holds them, and registration refuses a manifest that declares one, with
`capability_person_only`. For the same reason no channel grant to this service
can carry one, because a grant is the intersection of what the requester
holds and what the target's manifest declares
([`architecture/orchestrator`](orchestrator.md)).

### Startup Sequence

The order is not free, because the key this service authenticates with arrives
in the registration response:

```
1. Load configuration and open storage
2. Load or generate the ML-DSA-65 key pair
3. Reconcile the configured repositories against the registry — establish
   the ones not yet recorded, verify the custody attestations of the ones that
   are. Nothing here is fatal
4. Construct the authenticator WITHOUT an issuer key — it refuses every token
   until one arrives, which is the correct standalone behaviour
5. Register HTTP routes and start listening
6. Register with the orchestrator, if an orchestrator URL is configured
7. On the registration response, set the issuer public key on the authenticator
8. Start the reconcile and re-verify loops
9. Serve until signalled
```

Step 3 is fatal in neither direction: a configured repository that could not be
established is left `establishing` or recorded as a `DeclinedRepository`, health
reports `degraded` naming it, and the service serves everything else. A backend
that is briefly unreachable at boot MUST NOT stop a hub from starting, and MUST
NOT be reported as though the repository were fine.

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
   is non-conformant for the backend it satisfies the contract with. Naming a
   path in order to refuse it is not naming a backend: `.git` is refused on
   every backend (see [Reserved Paths](#reserved-paths)), and no backend is
   required by that.

7. **A person moves an entry; everything else proposes** — an agent, a service
   or a schedule may stage a change to an entry, and only a person makes one,
   by writing it or by deciding a proposal. This MUST hold at the tenant, and
   not in a client's setting: a rule one client enforces is a rule the next
   client does not. The tenant holds it for every service and every registered
   component, through capabilities none of them can hold. It cannot see
   software that uses a person's own credential, and that limit is stated
   with the rule, per Design Principle 5 (see
   [Who may move an entry](#who-may-move-an-entry)). A proposal whose base has
   moved on MUST NOT be merged into what is there now. Merged bytes are bytes
   nobody proposed and nobody decided.

8. **A copy is a place** — a repository is only as protected as the most
   exposed place a copy of it lives. A replica therefore lowers what the
   repository may hold and never raises it, and bytes that have left are never
   counted as returned. A replica is only ever sent to. What comes back from a
   place this service does not control is somebody's write, never the truth.

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

**Every place a copy lives counts.** The table derives the ceiling of one
place. A repository with replicas lives in more than one, and its ceiling is
the lowest of them (see [Effective custody](#effective-custody)).

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

## Declaring a Repository

Everything above describes a repository the service already holds. This section
is how one arrives, and it is the operation with the most to lose: a repository
is the unit custody is declared on, so declaring one wrong misstates the
protection of every byte inside it for as long as it exists.

`POST /v1/content/repositories`, operation `DeclareRepository`, guarded by
`content:declare`. It is a separate capability from `content:write` on purpose.
Writing a document and deciding which stores a tenant governs are different
acts by different people, and a single capability covering both would mean
anyone who may edit a policy may also place the tenant's name over a directory
nobody has looked at.

### A declaration says what it expects to find

`disposition` is required. There is no default, and a declaration without one
is refused with `CONTENT_DISPOSITION_REQUIRED`.

| Disposition | Means | Refused when |
|---|---|---|
| `establish` | Bring this store into existence; it will hold nothing and the tenant is its first author | The placement already holds entries — `CONTENT_NOT_EMPTY` |
| `adopt` | This store already holds bytes the tenant is taking responsibility for | The caller has not seen a census of them — `CONTENT_ADOPTION_UNSEEN` |

The two cannot be one operation with a lenient default, because the lenient
default is the failure. A create that finds bytes and proceeds is how a tenant
comes to govern somebody else's files: nothing was declared about them, nobody
read them, and from that moment the system reports them as governed content
with a custody class and a ceiling that were decided for a store presumed
empty.

Refusing `establish` over a non-empty placement is not an inconvenience. The
remedy is one word, and typing it is the act of saying *I know what is in
there*.

### `establish` brings the store into existence

`establish` does **not** mean *declare over an empty place somebody else made*.
It means the tenant's own service **creates the store and is its first author**.

The other reading was left open when the disposition was named, and it is the
wrong one. A declaration that can only point at what already exists puts the act
of making a store back on somebody with a shell on the machine the backend runs
on — and that is precisely the act this product exists to remove. A client of a
tenant cannot reach the tenant's filesystem. If the tenant's service cannot
create, then nobody working through the product can create, and every new
repository begins with a request to an operator, out of band, unrecorded.

So `establish` is two acts in one operation — **create, and declare** — and
because one of them cannot be undone by refusing, their naming, their
obligations, their order and their retry are all specified below rather than
left to the adapter to decide differently each time. Which comes first is not
the obvious answer, and it is settled under *A create that does not finish*.

`adopt` never creates. A locator that names nothing yields a census of zero
entries, which is the same answer an empty store gives, and
`ContentAdoption.entries` already says what to do with it: *"zero means the
placement is empty and establish is the correct disposition"*.

### A placement names a backend, never a location

Everything above this line has used the word *placement* with no field to carry
it. `RepositoryDeclaration` now has one, and it is not a path.

A `Placement` is a **backend name** and a **locator relative to that backend's
root**. The backend is one the service already holds for that `scope_path`; its
root, its driver and its credentials are the service's configuration and are
never in a request. The locator is in the same form as `ContentEntry.path` — the
name, not the identity — and is resolved by the same Path Resolver every entry
passes through.

| The declaration supplies | The service resolves it against | It never supplies |
|---|---|---|
| `backend` | the backends held for that `scope_path` | a host, a URL, a scheme, a mount, a share, a bucket |
| `locator` | that backend's root, confined | an absolute path, or one that climbs out of the root |

- A backend name this service does not hold for that `scope_path` is refused
  with `CONTENT_BACKEND_UNKNOWN`, and the refusal MUST NOT disclose whether the
  name exists under another scope — the rule `CONTENT_REPOSITORY_UNKNOWN`
  already applies to repository ids, for the same reason.
- A locator that is absolute, carries a scheme or an authority, contains a
  traversal segment, or resolves outside the root through a link is refused **as
  written**, with `CONTENT_PATH_REFUSED`. It is not normalised and then created.
- A locator with a reserved segment (see [Reserved Paths](#reserved-paths)) is
  refused as written, with `CONTENT_RESERVED_PATH`.

The rule is the same one reading and writing already obey. It matters more here,
and the reason is worth stating without euphemism: **a create that accepts a
caller-supplied absolute path is an arbitrary-write primitive.** Every other
operation in this service acts on bytes that already sit somewhere the service
already reached. `establish` is the only one that reaches somewhere new. A path
in the request would let the holder of one capability cause the service to
materialise a store anywhere its process can write, and the confinement every
other operation rests on would be a lock on the inside of an open door.

That the locator names something which does not exist yet is the *normal* case
for `establish`, which is why the resolver's rule about the **deepest existing
ancestor** (Implementation Notes) is load-bearing here rather than an
optimisation.

### What a backend owes once the store exists

What creating *is* differs by backend, and naming any of those acts is not this
document's business — Design Principle 6 holds here as everywhere else. What is
this document's business is the state a caller is entitled to afterwards. On a
successful `establish`, every one of these MUST hold:

1. **It exists and is addressable.** `GET /v1/content` over the repository
   returns an empty page, not an error. Nothing further is required to make it
   usable.
2. **It is empty.** A census over it yields `entries: 0`, and its census digest
   is the digest of the empty set.
3. **It is durable.** It survives the service restarting. A store that exists
   only inside the process that made it is not a store.
4. **It reports a custody class.** Custody and attestations were demonstrated
   against **the store that now exists**, not against the backend in the
   abstract, and the ceiling was derived from that demonstration. This is why
   verification cannot precede creation — there are no principals to enumerate
   on a store that is not there.
5. **It is writable under the ordinary rules.** There is no second
   initialisation step and no state in which a repository is declared but not
   yet usable.

And one obligation that takes the form of a prohibition:

> **The service MUST NOT write an entry into a store it establishes.** Not a
> marker, not a placeholder, not a `README`. Such an entry makes obligation 2
> false on the first read, gives the repository a first census digest that is
> not the empty one, and puts content under the tenant's name that no person
> authored — recorded `authored`, by this service, truthfully and uselessly.

A backend that cannot create a store at all — because the tenant holds access to
it and not administration of it — or that cannot represent an empty one without
something in it, MUST declare so. `establish` against it is refused with
`CONTENT_ESTABLISH_UNSUPPORTED`; `adopt` against it is unaffected. Refusing is
the honest answer. Writing a placeholder so that an empty store becomes
representable is a confident success, and it would be the system's own bytes it
was confident about.

### A create that does not finish

Creation is the first thing in this service that **cannot be undone by
refusing**. Every other refusal here leaves the world as it was. The failure
that matters is the one between the two acts: the store was made and the
declaration was not recorded. That leaves an **orphan** — capacity on the
tenant's backend that no repository governs, that no listing mentions, that the
next establish would either duplicate or trip over, and that no error code
describes, because `CONTENT_NOT_EMPTY` is false of it and a census of it says
nothing.

The ordering is therefore fixed, and it is **write-ahead**: the durable record
is written *before* the irreversible act, never after.

```
1. reserve   record the declaration durably with state: establishing
             — it takes the id and the placement, so a concurrent declaration
               is refused, and it governs nothing
2. create    the adapter brings the store into existence
3. confirm   demonstrate attestations against the store, derive the ceiling,
             set state: declared, publish content.repository_declared
```

A repository in `establishing` is **recorded and not governed**. It reports
`custody` and `effective_custody` `opaque`, every attestation `false`,
`ceiling` and `store_ceiling` `internal`, and no `verified_at` — the
fail-closed values, because nothing has been demonstrated
about a store that may not exist. It serves no read and accepts no write. It
appears in `GET /v1/content/repositories` with its `state` and its
`RepositoryEstablishment`, and health reports `degraded` naming it. It is never
omitted: a half-made repository that a listing hides is the confident zero of
Design Principle 5, one operation earlier than the listing that hides declined
ones.

Because the record precedes the store, every crash lands in the same state:

| Crash after | On the backend | What the service knows | Recovery |
|---|---|---|---|
| reserve | nothing | the declaration, `store_created: false` | retry `establish` |
| create | an empty store | the declaration, `store_created: true` | retry `establish` |
| confirm | an empty store | the declaration, custody not yet demonstrated | retry `establish` |

There is no fourth row in which a store exists and nothing knows of it. **The
orphan is not handled; it is made unreachable.**

**What the caller is told.** A create that fails at step 2 or 3 returns neither
a bare failure nor a success. It returns `CONTENT_ESTABLISH_INCOMPLETE` —
category `partial` in the `ErrorResponse` vocabulary
[`protocol/types`](../protocol/types.md) declares, `retryable: true` — carrying
the `ContentRepository` as recorded and the `RepositoryEstablishment` saying
which of the three steps completed. The caller learns the three things it would
otherwise have to guess: the id is now taken, the declaration is durable, and
whether a store was made. Answering *nothing happened* when a store was made is
exactly the lie this ordering exists to prevent, and it is worse than an error,
because the caller's reasonable next act on hearing it is to try somewhere else.

`CONTENT_ESTABLISH_INCOMPLETE` is not a `DeclinedRepository`. A declined
repository was **refused** — nothing durable was attempted, and nothing changes
without a new declaration. An establishing one was **accepted and not
finished**, and it completes by being retried. Both are reported, and
conflating them would make a backend that was briefly unreachable look like a
request that was rejected.

### A retry is not a second store

A caller whose request timed out cannot know which step it reached. The rule has
to make retrying safe, because the alternative is that the safe move after a
timeout is to do nothing — and doing nothing strands the reservation for good,
since **nothing retires a repository**.

> A repeated `establish` against a repository in `establishing`, with
> **identical arguments**, is a no-op on whatever already succeeded and a
> resumption of whatever did not. It is not an error.

Identical means the recorded `id`, `scope_path`, `placement`, claimed `custody`
and claimed `attestations` all equal this request's. The comparison is against
the reserved declaration — not a clock, and not a nonce the caller would have to
have kept. The caller's own name for the thing is the better idempotency key,
because it is the one thing it is certain to still have after a timeout.

- Any of those arguments differing → `CONTENT_REPOSITORY_EXISTS`, naming the
  recorded placement, exactly as before. A different request is a different
  request, whatever state the first one is in.
- The store already exists and is empty → creation is skipped and the retry goes
  on to confirm. It MUST NOT create a second store, and the reservation is why
  it cannot: the placement was taken durably before the first store was made.
- The store exists and holds entries the service did not write →
  `CONTENT_NOT_EMPTY`, and here the code means what it says. Bytes really are
  there, the tenant is not their first author, and taking them on is a decision
  a person makes after reading a census.

**A completed establish is not idempotent, and MUST NOT be made so.** Once the
repository is `declared`, a repeat with identical arguments is
`CONTENT_REPOSITORY_EXISTS`. `establish` asserts *this store held nothing and
the tenant is its first author* — a claim about a moment that has passed, and
one the tenant may have falsified itself by writing a hundred documents since. A
second establish that quietly returned success would be answering "empty" about
a store that is full. Idempotency belongs to the unfinished operation, and it
ends when the operation does.

### Creating is not declaring

`establish` requires `content:declare` **and** `content:establish`. `adopt`
requires `content:declare` alone.

The argument that split `content:declare` off `content:write` was that writing a
document and deciding which stores a tenant governs are different acts by
different people. Creation is a third act, and the test is the one already
applied: what can the holder of a capability do that the holder of its
neighbour cannot?

| Capability | Worst case in the wrong hands |
|---|---|
| `content:write` | a document says something it should not — over a precondition, against a ceiling, in the audit trail |
| `content:declare` | the tenant governs a store it should not — bounded by the stores that exist |
| `content:establish` | the tenant's backend accumulates stores nobody asked for — unbounded, and with no verb that retires one, permanent |

Those are three different risks, so they are not one grant.

The decisive argument is not the taxonomy, though. Folding creation into
`content:declare` would hand **every principal already holding
`content:declare`** a power nobody granted them, at the moment this
specification landed. A governance product cannot widen a live grant by editing
its own specification; the grant is a record of a decision somebody made, and
this would silently make that decision mean more than it meant when it was
taken. Requiring the intersection leaves every existing grant worth exactly what
it was worth, and makes adding creation a thing somebody does on purpose and
that the audit trail can show.

Capability names live in [`protocol/types`](../protocol/types.md) and nowhere
else; `content:establish` belongs to the `content:` family it declares.

### `if_match` on a declaration

`if_match` means the same thing here as it does on
`PUT /v1/content/entry` — **the identity of the thing I believe I am acting
on** — over a different subject. A write's subject is one entry's bytes. A
declaration's subject is the set of entries the placement holds, and its
identity is a **census digest**.

- `establish` MUST NOT carry `if_match`, the empty string included, and one
  that does is refused with
  `CONTENT_PRECONDITION_NOT_APPLICABLE`. There is nothing to have seen, and a
  precondition over an empty set is one that always holds — which is the same
  as none, and accepting it would let a caller believe it had a guarantee
  nothing checked. A caller that supplied one expected bytes, which means
  `adopt` is the word it wanted.
- `adopt` MUST carry one, and a first adoption call can therefore never
  succeed. The service computes the census, returns it, refuses with
  `CONTENT_ADOPTION_UNSEEN`, and declares nothing. The caller re-submits with
  the census digest it was given. If the placement changed in between — an
  ordinary thing under shared custody — the digests differ and the declaration
  is refused with `CONTENT_PRECONDITION_FAILED`, exactly as a write is.

The census digest is computed per
[`patterns/content-identity`](../patterns/content-identity.md) over the ordered
list of `(path, entry digest)` pairs, so it changes when anything is added,
removed or edited, and does not change when nothing is. It costs one full pass,
which adoption earns exactly once.

**A backend may bind more than its entries.** The blueprint that specifies a
backend MAY name facts about a store, beyond its entries, that a person
adopting it must have seen: for a store under version control, which history it
follows and what its control state would do. The census carries them in
`backend_report`, and the digest covers them. After the `(path, entry digest)`
pairs comes one more pair, whose path is empty and whose digest is that of the
report in RFC 8785 canonical form, without any field that blueprint names as a
time of observation. No entry has an empty path, so that pair is never mistaken
for one. A store whose report changed since the census is refused with
`CONTENT_PRECONDITION_FAILED`, as one whose entries changed is.

This is what makes silent adoption structurally impossible rather than
discouraged. A caller cannot adopt without having been told what it is
adopting, because the only way to obtain the precondition is to ask and read
the answer.

### What an adopted entry is, and is not

Every entry the census finds is recorded with provenance `unknown`.

Not `authored`: this service did not write it, and saying otherwise would put
the tenant's name on authorship it cannot demonstrate. Not `external` either:
`external` is the verdict of the reconciler, which compares a digest it
recorded earlier against one it reads now. At adoption there is no earlier
digest, so nothing has been observed to change. `unknown` is the only honest
answer, and `ContentEntry.provenance` already carries it — *"unknown when it
cannot be established"*.

The consequence is deliberate and should not be smoothed away: a freshly
adopted repository reports that it cannot establish the provenance of anything
in it. That is the truth about a tree the tenant has just met, and it resolves
itself as the tenant writes.

### The ceiling is derived at declaration, not supplied

`RepositoryDeclaration` has no `ceiling` and no `verified_at`. Both are
outputs. Custody and attestations are **claims** in the request; each is
demonstrated before it takes effect, per Design Principle 2, and the ceiling
follows the demonstration. A declaration claiming three attestations and
demonstrating one is recorded with one, and its ceiling says so.

A declaration with no `custody` is recorded `opaque` with the `internal`
ceiling and the degradation is recorded, per `CONTENT_CUSTODY_UNDECLARED`. It
is not refused: declaring a store you can say little about is a legitimate act,
and refusing it pushes the content somewhere the service cannot see at all.

### One placement, one repository

A declaration whose placement equals, contains or sits inside an
already-declared repository's is refused with `CONTENT_PLACEMENT_DECLARED`. Two
repositories reaching the same bytes means two ceilings over them, and the
lower one is then unenforceable — a write refused through one id succeeds
through the other, and the refusal was theatre.

A placement reserved by an unfinished `establish` counts as declared for this
check, and that is the point of reserving it. The reservation is what stops two
concurrent establishes from creating two stores over the same bytes, and it
holds from before the first store is made rather than from after.

**This check sees only what has been declared.** The registry knows every
placement it holds and can compare them; it cannot know that a backend reaches
the same bytes by another route it was never told about. That limit is stated
with the answer, per Design Principle 5, and is not closed by pretending the
check is wider than it is.

### A store that already exists is the normal case

A tenant's policies, procedures and evidence usually predate the tenant. The
expected *first* declaration is therefore an adoption, not an establishment,
and the two-step exists because that is the common path rather than the exotic
one.

Every declaration after the first tends the other way. A tenant is never
finished being built: a new programme, a new project's evidence, a second
organisation's procedures each want a store that does not exist yet. So
adoption is the common **first** act and establishment is the common
**subsequent** one, and a product where the second of those requires an
operator with a shell is a product that works once.

Whether the backing store is version controlled, on a share, or a directory
somebody made this morning is not this document's business — Design Principle 6
holds. What matters about it is already expressible: a backend exposing a
history the service can traverse attests `tamper_evident`, and one that does
not, does not. Nothing new is needed to say "this repository is under version
control", and naming the system would be naming a product.

> **Gap.** There is no verb that retires a repository. A declaration is
> therefore permanent, and a store declared by mistake stays declared. Naming
> that verb requires deciding what happens to the entries' recorded identities
> — `patterns/content-identity` retires an identity rather than deleting it,
> and a repository holding thousands is not the same act as one entry. It is
> left unspecified rather than guessed at, and this line exists so the absence
> is a known gap rather than an oversight.
>
> **`establish` makes that gap more urgent, and this change does not close
> it.** Until now the gap cost a tenant a wrong row in a registry — a store it
> should not have adopted stayed adopted. A tenant that can create can also
> accumulate: a mistaken establish leaves both a declaration that cannot be
> retired *and* a store on the backend that nothing in this contract can
> remove, and the two cannot be separated, because retiring the declaration
> while saying nothing about the store is how the orphan the section above
> just made unreachable walks back in through the other door. Naming the verb
> now needs one more answer than it did — whether retiring a repository the
> tenant created also destroys what it created, and who may decide that — and
> guessing that here would be worse than leaving it unnamed.
>
> **Nor is there a verb that amends a declaration.** What a declaration fixed
> stays as declared: its placement, and its `self_decision_ceiling` or the
> absence of one. A repository declared without that ceiling, and every
> configured repository, cannot be given one. Naming an amending verb needs the
> same care as retiring, because an amendment that lowered separation would
> weaken a control over bytes already written under the stronger one.

---

## Replicas

A **replica** is a copy of a repository that this service keeps at a second
place, its **destination**. The service sends the repository's entries there
and, where the backend keeps versions, every version it has recorded. It takes
nothing back.

A replica is how a tenant keeps a copy of its content off the machine that holds
the store, and how it publishes one. Both put the tenant's bytes somewhere its
own service does not control. So a replica is declared the way a repository is
adopted, by a person who has seen what would leave, and the place it names
lowers what the repository may hold.

### A replica is sent to, and never read from

- **Push-only.** The service sends to a replica. It never reads an entry, a
  digest, a version or a history from one, and never takes a change made there
  into the repository. The one thing it asks a destination is whether it still
  holds only what the service sent.
- **Never a source of truth.** Nothing this service answers comes from a
  replica: not a read, a census or a recovery. A store rebuilt from a replica's
  copy is a new store. It comes under governance by adoption, with a census, and
  every entry in it is recorded with provenance `unknown`.
- **A replica that diverged is reported, never pulled.** A destination that
  holds something this service did not send makes the replica `diverged`. The
  service records what it found, sends nothing more, and never overwrites the
  destination to make it match. Sending resumes by itself once the destination
  again holds only what the service sent. A change somebody made at the
  destination reaches the repository only as that person's own write or
  proposal.
- **Sending never holds up a write.** A write is complete when the repository
  holds it. Sending follows, in the order the versions were recorded.
- **What is sent comes from the service's own record.** It is never read from
  the store at the moment of sending, because another authority can change the
  store. The blueprint that specifies the backend says where that record is
  kept.

### Declaring a replica

`POST /v1/content/repositories/{repository}/replicas`, operation
`DeclareReplica`. The steps and their order are the
[Replica Declaration Flow](#replica-declaration-flow).

**Nothing leaves unseen.** Declaring a replica is adoption's two-step, over what
would leave rather than over what a placement holds. A first call carries no
`if_match`: the service returns a `ReplicaCensus`, refuses with
`CONTENT_REPLICA_UNSEEN`, and records nothing. The caller re-submits with the
census `digest`. The digest is computed as an adoption census's is (see
[`if_match` on a declaration](#if_match-on-a-declaration)), over the ordered
`(path, entry digest)` pairs of every version that would leave, and it covers
the backend's report where the backend's blueprint declares one. A version
recorded between the two calls changes it, and the declaration is then refused
with `CONTENT_PRECONDITION_FAILED`. There is no other way to obtain the
precondition, so a replica cannot be declared by somebody who has not been told
what it would receive.

**It is reserved before anything is made, as a store is.** A confirmed
declaration follows establish's order, for the reason given under
[A create that does not finish](#a-create-that-does-not-finish): the durable
record comes before the act that cannot be undone. The replica is reserved
first, in `establishing`, sending nothing. Only then is its credential created,
and only then is the destination demonstrated. A repeated declaration with
identical arguments against a replica in `establishing` resumes where it
stopped and creates no second credential. A completed declaration is not
idempotent: repeating it is `CONTENT_REPLICA_EXISTS`.

**The credential is the tenant's, for one destination.** A replica is reached
with a credential the service creates for that replica alone and holds through
[`patterns/secrets`](../patterns/secrets.md). Its secret part never leaves the
service. `ContentReplica.credential` carries the part a person registers at
the destination. The service presents it only there
([`architecture/orchestrator`](orchestrator.md), *Presenting a credential to a
component*). Retiring the replica destroys it. A credential that a person or a
client brought would be one the tenant does not control, and could be presented
anywhere it was valid.

**The destination is demonstrated, not claimed.** The declaration's custody and
attestations are claims, demonstrated against the destination before they take
effect, exactly as a repository's are. The service also demonstrates that the
destination holds nothing it would not send, which is otherwise refused with
`CONTENT_NOT_EMPTY`, and it tests `anonymous_read` by trying to read the
destination with no credential. A destination that cannot be reached yet —
the ordinary case, before a person has registered the credential there —
answers `CONTENT_ESTABLISH_INCOMPLETE`, carrying the replica and its credential.
Nothing has been sent.

**Not in configuration.** A replica is never declared in a configuration file,
for the reason adoption is not: a file cannot hold a census digest that did not
exist when it was written, and a file that could send a repository's history
would send it on every fresh start, unread.

### Who may declare a replica

| Capability | Lets the holder | Worst case in the wrong hands |
|---|---|---|
| `content:replicate` | Declare a replica, with `content:connect`. Retire one | every version of a repository sent to a destination of their choosing |
| `content:connect` | Have the service create and hold a credential that reaches outside the tenant's store | the tenant holding a key to a place outside itself |

Declaring a replica requires both. Neither alone sends a byte anywhere: a
replica with no credential reaches nothing, and a credential with no replica is
sent nothing. Sending a repository outside the tenant therefore takes two
grants, the rule `content:establish` already follows beside `content:declare`
(see [Creating is not declaring](#creating-is-not-declaring)). Retiring a replica
needs `content:replicate` alone, because it only ever reduces where bytes go.

Both are *person only* in [`protocol/types`](../protocol/types.md). Sending a
tenant's history to another place is a judgement, and a service has none to
exercise (principal-identity Design Principle 11). The rules that keep a
person-only capability with people are stated once, under
[Who may move an entry](#who-may-move-an-entry), and hold here unchanged.

### What would leave

The census reports, for the repository and the destination:

- the entries now, and every earlier version that would leave with them;
- the paths an earlier version holds and no entry holds now, because a person
  looking at today's entries cannot see them;
- the highest scope recorded for anything that would leave;
- how many versions carry no scope a person declared, as `unclassified`. They
  are counted and never assumed to be at any level;
- each path that would leave above the replica's prospective ceiling, and each
  reserved path that would leave. Either refuses the declaration, and the census
  names them so the person can see why before confirming;
- who holds the destination, and the ceilings the replica and the repository
  would have, computed from the claims. The demonstration can only lower them;
- what the backend's blueprint binds in `backend_report` — for a store under
  version control, the names every earlier version was recorded under.

A reserved path refuses the declaration even where it appears only in an
earlier version, put there by somebody out of band. Installation state and
control state never leave.

### A third party's replica waits for classification

Every backend says who holds the store it reaches: the tenant, or a third party
(`held_by`, under [Configuration](#configuration)). A backend that does not say
is a third party's. It is never inferred from a host, a URL or a provider name,
as custody is not.

A replica whose destination a third party holds is refused with
`CONTENT_REPLICA_UNCLASSIFIED` unless the classification gate is present and
passes for everything that would leave. The gate is present when this contract
classifies every version a replica would receive, so that each carries a scope
a person declared, and applies the plain-replica cap: a replica that holds the
bytes readably is capped at `confidential`, whatever its custody would
otherwise allow. Where the gate is not present, every such replica is refused.

A replica the tenant holds is not refused by this rule. A copy on a machine the
tenant owns, away from the machine that holds the store, gives durability
without disclosure, and it exercises every other rule in this section before a
third party is involved.

### Effective custody

A repository's bytes live wherever a copy of them lives. Its **effective
custody** is the most permissive custody of any place they live, in the order
`exclusive`, `shared`, `opaque`: its store, and every replica that has been
sent anything, retired or not. Its **ceiling** is the lowest ceiling of those
places.

- `custody` stays the store's. It says who else can write the bytes this
  service reads, and reconciliation and the anomaly rules of
  `architecture/data-security` depend on exactly that. A replica writes
  nothing here, so it does not change it.
- `effective_custody` says who else can read a copy. Every statement about
  access is made from it: an `AccessStatement` carries `access_complete: false`
  unless effective custody is `exclusive`.
- `ceiling` is the effective ceiling, and the ceiling check of every write and
  every proposal uses it. `store_ceiling` is what the store alone allows. A
  consumer that reads only `ceiling` gets the safer answer.
- A replica's own ceiling is derived from what was demonstrated about its
  destination, by the [Derived Scope Ceiling](#derived-scope-ceiling) table.
  `anonymous_read` comes first: a destination that anyone can read, or whose
  anonymous read was not demonstrated to be refused, has the ceiling `public`.
- **Bytes that have left have left.** Retiring a replica never raises the
  ceiling and never narrows effective custody.
- **An undeclared copy counts.** A backend that can see a copy of the store
  that no replica declares MUST report it. It counts as a place whose custody
  is `opaque`, with the `internal` ceiling the table gives that custody; its
  anonymous read is not tested, because the service does not reach it.
  Effective custody becomes `opaque`, the ceiling is `internal` at most, and
  `content.custody_degraded` is published naming the content now above it.

A replica in `establishing` has been sent nothing and counts toward nothing.
Only confirming it lowers the ceiling, so what is written while a person
registers its credential is checked again when the replica is confirmed
(Replica Declaration Flow, step 10).

### States

| State | Means |
|---|---|
| `establishing` | Reserved and not yet confirmed. Nothing has been sent |
| `current` | The destination held every recorded version when last checked |
| `behind` | Versions are recorded and not yet sent. `held_path` and `held_reason` name a version the service will not send, if there is one |
| `diverged` | The destination holds something this service did not send. Nothing is sent |
| `unreachable` | The last attempt could not reach the destination, or its credential was refused |
| `retired` | A person retired it. Nothing is sent, its credential is destroyed, and its record stays |

A version above the replica's ceiling is held, never skipped. Nothing recorded
after it is sent either, because a destination that received later versions
without it would hold a history with a hole in it.

Every count a replica reports is as of its `checked_at`, and is absent when it
cannot be established. `behind_by` is never 0 for a replica the service could
not check.

### Retiring a replica

`DELETE /v1/content/repositories/{repository}/replicas/{replica}`, operation
`RetireReplica`. The replica becomes `retired`: nothing more is sent, its
credential is destroyed, and its record stays, naming who retired it. Nothing
at the destination is deleted, because the service never writes there except to
send. The response says that the destination still holds what was sent and
that the credential registered there is for a person to remove.

A replica in `establishing` may be retired too. It was sent nothing, so it never
counted toward effective custody.

---

## Reserved Paths

Some paths in a store are not content. No operation of this service reaches
them: not a read, a write, a removal, a stat, a listing or a proposal, and not
a placement's locator on a declaration.

| Reserved | What it holds | Declared by |
|---|---|---|
| `.weblisk` | Installation state: keys, secrets and run state | this document |
| `.git` | A version-control tool's control state: its configuration, its hooks and its object store | this document |
| What a backend cannot let this service reach | Its own control state, kept beside the entries in order to do its job, and paths it cannot write safely, such as those inside a second store of its own kind nested in this one | the blueprint that specifies that backend |

A path is reserved when **any** of its segments is a reserved name, at any
depth, or when the blueprint that specifies its backend reserves it. A store
that holds several projects can hold several `.weblisk` directories, and a tree
can hold a `.git` at any level. A name that only begins with a reserved name,
such as `.gitignore`, is not reserved by this rule.

**The comparison is on every name a filesystem could open, not on the bytes of
the name, and it is the same on every backend.** A store can be read later on a
filesystem other than the one that holds it now — through a synced drive, a
share or a copy — so a name that is harmless where it was written can open a
reserved directory where it is read. A segment is a reserved name when any of
these makes it one, whatever filesystem holds the store:

- compared without regard to case;
- with trailing dots and spaces removed;
- with the code points any filesystem ignores in a name removed;
- read as a short name that a filesystem could give a reserved name — up to
  its first six characters without the leading dot, then `~` and a digit, such
  as `git~1` for `.git` and `weblis~1` for `.weblisk`;
- with an alternate data stream suffix removed, such as the one in
  `.git::$INDEX_ALLOCATION`.

A byte comparison says `.WEBLISK` and `.weblisk` differ. A case-insensitive
filesystem opens the same directory for both, so a guard that compares bytes
serves the key material to anyone who capitalises the path. A guard that folds
only where its own filesystem folds is no better: bytes written as `.GIT` where
case is distinguished are opened as `.git` by the next machine that syncs them.

A reserved path is refused **as written**, with `CONTENT_RESERVED_PATH`. It is
not rewritten to a nearby name that is allowed.

**A reserved path is not an entry.** A listing does not return one, a census
neither counts nor digests one, and the reconciler never observes one. This
hides no content, because none of it was ever content. A backend's control
state is still a fact about custody. The blueprint that specifies the backend
says how it is reported, in `ContentRepository.backend_report`, and it is never
reported as entries.

### Why `.git` is named here

`.git` is refused on every backend, not only on one under version control. A
`.git` directory written into any tree makes that tree a repository to any
version-control tool run inside it, and such a tool runs the hooks and applies
the configuration it finds there. A service that let a caller write one would
let the holder of `content:write` choose a command that runs as whoever next
runs the tool in that tree. That is true whatever backend wrote the bytes, so
it is not left to a version-controlled backend to declare.

---

## Proposals

A **proposal** is a change to one entry that has been recorded and not made. It
names the entry, the bytes it would write and the identity of the bytes it
would replace. Recording it writes nothing. A person decides it: applying it
writes the entry through the ordinary Write Flow, and rejecting it writes
nothing.

Proposals exist for Design Principle 7. An agent's work, a service's import and
a scheduled job's output all reach an entry the same way: as a proposal a
person applies.

### Who may move an entry

| Capability | Lets the holder | May be held by |
|---|---|---|
| `content:write` | Write or remove an entry directly | A person only |
| `content:propose` | Record a proposal | A person, a service, or an agent acting under either |
| `content:decide` | Apply or reject a proposal | A person only |

[`protocol/types`](../protocol/types.md) marks `content:write` and
`content:decide` **person only**. Three rules keep them with people:

- **No service holds one.** A hub refuses a person-only capability in a
  service subject's grant and in every token minted for one
  ([`patterns/principal-identity`](../patterns/principal-identity.md),
  `service-subject-constraints`), and refuses a registration whose manifest
  declares one ([`protocol/spec`](../protocol/spec.md), `POST /v1/register`).
  Both refusals carry `capability_person_only`. A client that runs agents under
  its own service identity can therefore only propose their output.
- **This service honours one only on a person's token.** A person-only
  capability counts only on a token whose `type` is `operator`, which a hub
  mints for an operator, a person, through a credential that person's identity
  attested ([`architecture/admin`](admin.md#operator-token)). On any other
  token — a registered component's, a channel's — this service treats it as
  absent. A hub that issued one by mistake has still opened no route.
- **An agent runs under a credential that holds neither.** A console runs every
  agent under its own service identity, whether or not anybody is watching
  ([`architecture/admin`](admin.md), `console-credential-use`), so the
  credential the run uses holds neither capability. An agent's authorisation
  never names one either (principal-identity, `agent-delegation`).

A decision is judgement, and a service has none to exercise
(principal-identity Design Principle 11).

**What the tenant cannot see.** A token is a bearer credential. This service can
tell whose credential a request used. It cannot tell whether that person sent
the request or software they run sent it with their credential. The first two
rules hold at the tenant for every service and every registered component, and
no client can loosen them. The third holds at the tenant for a console's
service identity, and in the console for a person's credential. A console that
ran an agent under a person's credential would produce a change recorded as
that person's direct write. This limit is stated here, as Design Principle 5
requires, rather than hidden behind the two rules that do hold.

`content:write` and `content:propose` do not imply each other. A person who
holds both may still propose, to ask for a review.

### A proposal is made against bytes

A proposal says which bytes it replaces, as a write does, and `if_match` is
required on every proposal. It means what it means on a write (see the
Precondition Gate under [Architecture](#architecture)): for `modify` and
`delete`, the digest of the entry the proposal replaces or removes; for
`create`, the empty string, which asserts that the path holds nothing. An
`if_match` that contradicts the action — the empty string on a `modify` or
`delete`, a digest on a `create` — is refused with
`CONTENT_PRECONDITION_NOT_APPLICABLE`.

A proposal passes the checks a write passes, when it is made: the Path
Resolver, the ceiling, the Precondition Gate and the enforcement storage proxy,
for the proposer. A change its proposer could not be authorised to make is
refused before anyone is asked to decide it. When the proposal is applied, the
proxy runs again for the decider, so neither of them can cause a write beyond
their own reach.

The service holds the proposed bytes itself. They arrive in `bytes`, as base64
(see [Endpoints](#endpoints)), and `after` is computed over the decoded bytes
it holds, never taken from the request. `ProposedChange` names the path and the
action. Its text fields — `original`, `modified` and `diffs` — are not read: an
entry is bytes, and a text field cannot carry them exactly. The service already
holds the bytes the proposal was made against, and a copy the caller supplies
is only a claim about them. `max_entry_bytes` bounds a proposal's bytes as it
bounds a write's. The proposed bytes stay in the service's own state and never
in the repository, because they are not content until a person applies them.

A proposal's bytes are read under the check that guards the entry they would
change, whoever asks (see the Proposal Read Flow). A proposal to change a
restricted entry is restricted reading, and holding `content:read` for the
repository does not open it.

### States

| State | Means |
|---|---|
| `open` | Recorded and waiting for a decision |
| `applied` | A person decided to apply it, and its change was written |
| `rejected` | A person decided not to apply it. Nothing was written |
| `stale` | A person decided to apply it, and the entry no longer held its `before`. Nothing was written |

A proposal leaves `open` once, and every other state is final. It is never
re-opened, and a `stale` proposal is never applied: the proposer proposes
again, against the bytes that are there now. Of two decisions that race, one is
recorded and the other is refused with `CONTENT_PROPOSAL_DECIDED`.

There is no separate verb to withdraw a proposal. A person holding
`content:decide` rejects it, and that person may be its requester, because a
rejection writes nothing and needs no separation.

### A proposal whose base has moved on is stale

On a decision to apply, the proposal's `before` is the precondition. If the
entry no longer holds it — somebody edited it, or, for a `create`, an entry has
appeared at the path — the decision is refused with
`CONTENT_PRECONDITION_FAILED` and both digests, the proposal is recorded
`stale`, and nothing is written.

It is never merged: not by a three-way merge, not by re-applying a patch to the
new bytes, not by a rebase. Each of those produces bytes nobody proposed, and
applying them would record a person's decision about text that person never
saw.

A decider can see this before deciding. While a proposal is `open`, reading or
listing it reports `base`: `current` when the entry still holds `before`,
`moved` when it does not, and `unknown` when the entry cannot be read. `base`
is computed each time it is asked for and never stored, because the entry can
change between one read and the next.

### Separation of duties

The **requester** of a proposal is its `actor` and, when present, its
`on_behalf_of`. The person who dispatched an agent is a requester of the
agent's proposal, as much as the service the agent ran under.

Requester and decider are compared by identity id and by nothing else (see
[Who a change was for](#who-a-change-was-for)). A name, an email address or a
token's `sub` is never compared: the same person can appear under several of
them, and a comparison across two of them finds two people where there is one
(principal-identity Design Principle 10).

A decision to apply is made by someone who is not a requester, and the
resulting `ContentChange` records `separation: independent`. This is
[`patterns/approval`](../patterns/approval.md) Design Principle 2, applied to a
proposal.

A repository MAY allow one person to decide their own change, up to a scope it
declares. This is the one exception `patterns/approval` names to its separation
of duties, and it is bounded there as it is here. `self_decision_ceiling` on
the repository's declaration is the highest `ScopeLevel` at which it is
allowed:

- **Absent**, the default: a requester's decision to apply is refused with
  `CONTENT_SEPARATION_REQUIRED`.
- **Present**: a requester may apply a change whose scope is at or below it —
  the proposal's scope, or on a `delete` the scope of the entry it removes —
  and the `ContentChange` records `separation: self`. Above it, the decision
  is refused with `CONTENT_SEPARATION_REQUIRED`.

It never lets a service or an agent decide. A decider holds `content:decide`,
which is person only, so the exception can only ever let a person agree with
themselves. It exists so that an organisation of one person can use proposals
at all. Without it, that person's only way to land an agent's work would be to
write it directly, and a direct write records no decision, no proposal and no
separation. `separation: self` records exactly what happened: one person asked,
and the same person agreed.

**It is declared on the repository.** Custody and ceiling are already decided
per repository, and separation protects the same bytes. A register that names
people beside their injuries and a programme's procedures sit in different
stores with different ceilings, and one person's leave to decide alone over the
second is no reason to extend it to the first.

**It is not configurable, and only a person declares it.** Allowing a person to
decide their own change weakens a control. That is an act somebody performs
through `POST /v1/content/repositories`, and a declaration that carries
`self_decision_ceiling` requires `content:decide` as well as `content:declare`.
`content:decide` is person only, so no service and no agent can weaken a
control whose purpose is a person's decision. The audit trail shows who did it.
It is never a line in a file read at boot with no caller. It is fixed when the
repository is declared, because this contract has no verb that amends a
declaration (see the gap under
[A store that already exists is the normal case](#a-store-that-already-exists-is-the-normal-case)).
A repository declared without one, and every configured repository, stays
without one until that verb exists.

**It is no stronger than `on_behalf_of`.** The service witnessed `actor` and
did not witness `on_behalf_of` (see below). A client that leaves out the person
it acted for makes that person's own decision look independent. The record
says which part was asserted, as Design Principle 5 requires.

A rejection needs no separation, and records none.

### Who a change was for

A `ContentChange` says who prepared the change, who it was for and who let it
land. Each part has a **basis**, which says what stands behind it:

- **witnessed** — the service took it from the credential it verified on the
  request, and never from a request body;
- **asserted** — the caller stated it, and the service records the statement
  as made and establishes nothing about it;
- **recorded** — the service produced it itself.

**Every party is named by identity id**: the identifier the issuing hub
records for the subject's identity, and never a name, an email address or a
token's `sub` (principal-identity Design Principle 10). This service takes the caller's
identity id from the `identity_id` claim of the token it verified
([`protocol/identity`](../protocol/identity.md#payload-claims)). On a person's
token that is the identity that attested the credential the token's `cid`
names. On a registered component's token it is the fingerprint of the key the
component registered. The hub that issued the token sets the claim from its own
records and signs it, so the service reads it and resolves nothing itself. A
write, removal, proposal or decision whose token carries no `identity_id` is
refused with `CONTENT_IDENTITY_REQUIRED`. It is never recorded under a name
instead. The service passes the same identity id as the actor of the
enforcement request each of those routes makes, so the audit entry and the
record name the same party.

| Field | What it says | Present when | Basis |
|---|---|---|---|
| `actor` | The subject who prepared the change: the writer on a direct write, the proposer on an applied proposal | Always | witnessed |
| `on_behalf_of` | The person the proposer acted for | The change applied a proposal whose request stated one | asserted |
| `approved_by` | The person whose decision applied the change | The change applied a proposal | witnessed |
| `proposal` | The proposal the change applied | The change applied a proposal | recorded |
| `separation` | Whether a requester decided: `independent` or `self` | The change applied a proposal | recorded |
| `version` | The backend's own marker for the state the change produced | The backend keeps one | recorded |

- **`actor`** is who prepared the change, which is not always whose grant let
  it land. On a direct write it is the writer. On a change that applied a
  proposal it is the proposal's `actor` and not the decider: one subject
  prepared the change and another let it land, and the record names both. The
  second is `approved_by`.
- **`on_behalf_of`** is absent on a direct write. A direct write needs
  `content:write`, which only a person's token carries, so the writer acts for
  themselves and `actor` already names them. On a proposal, a client that
  carries out a person's instruction under its own service identity MUST send
  it; an agent run that a person dispatched is the ordinary case. Without it
  that person is absent from the record, and separation cannot see them. A
  scheduled job is not a person and is never `on_behalf_of`. It names itself
  in `run`, and `on_behalf_of` names the person it acts for, where there is
  one.
- **`agent` and `run`**: a client submitting a change that an agent prepared
  MUST send `agent` and `run` with the proposal, as well as `on_behalf_of`.
  principal-identity Design Principle 13 requires the record to name the agent
  and the run that used a subject's authority, and the proposal is where the
  record holds them. Both are asserted. `proposal` leads from the change to
  them.
- **`approved_by`** is witnessed, not signed. The service authenticated the
  person who decided, and that is all it can say. It is not a signature under
  that person's sole control, and a consumer that reports an approval MUST NOT
  report it as signed. It is a list, and under this contract it holds one
  person.
- **`correlation_id`** names the enforcement decision that authorised the
  write. On a change that applied a proposal that is the decider's decision,
  and its audit entry names the same identity as `approved_by`. The
  proposer's decision is on the proposal, as its own `correlation_id`.
- **`version`** is a locator, never an identity. A backend under version
  control records its revision id there, and what any backend records is for
  the blueprint that specifies that backend to say. Nothing joins on it. The
  join key is the entry's `ContentIdentity`, which
  [`patterns/content-identity`](../patterns/content-identity.md) defines, so a
  history rewritten on the backend changes `version` and leaves every digest
  as it was.

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
      placement:
        type: Placement
        required: true
        description: Where the bytes live, as resolved at declaration and
          recorded. Resolved once, never re-derived per request
      state:
        type: enum
        values: [establishing, declared]
        required: true
        description: establishing while the store is being brought into
          existence — recorded, governing nothing, serving no read and
          accepting no write. declared once custody was demonstrated and the
          ceiling derived. A consumer that does not read this field sees an
          establishing repository as opaque, internal-ceilinged and empty,
          which is both safe and true
      establishment:
        type: RepositoryEstablishment
        required: false
        description: Present while state is establishing, and on a repository
          whose establish did not finish. Absent on an adopted repository
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: true
        description: Who else can reach the bytes in the store. Undeclared is
          opaque. A replica does not change it — see effective_custody
      effective_custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: true
        description: The most permissive custody of any place the bytes live
          — the store, every replica that has been sent anything, and any copy
          the backend reports that no replica declares. Equal to custody for a
          repository with no replica
      attestations:
        type: CustodyAttestations
        required: true
      ceiling:
        type: ScopeLevel
        required: true
        description: The effective ceiling — the lowest of store_ceiling and
          the ceiling of every place effective_custody counts. Every ceiling
          check uses it. Derived, never configured
      store_ceiling:
        type: ScopeLevel
        required: true
        description: What the store alone allows, derived from custody and
          attestations. Never configured
      verified_at:
        type: timestamp
        required: false
        description: When attestations were last demonstrated. Absent means never
      self_decision_ceiling:
        type: ScopeLevel
        required: false
        description: The highest scope at which a requester may apply their own
          proposal, recording separation self. Absent means no requester may.
          Fixed at declaration
      backend_report:
        type: object
        required: false
        description: What the blueprint that specifies the repository's backend
          says it reports about the store — its control state, and whether the
          store is as the service left it — in the form that blueprint
          declares. Absent when that blueprint declares none

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

  Placement:
    description: Where a repository's bytes live, named in the tenant's own
      terms — a backend this service already holds, and a locator relative to
      that backend's root. Never an absolute location, and never a URL
    fields:
      backend:
        type: string
        required: true
        description: The name of a backend this service holds for that
          scope_path. A name it does not hold is refused with
          CONTENT_BACKEND_UNKNOWN, without disclosing whether the name exists
          under another scope
      locator:
        type: string
        required: true
        description: Path relative to that backend's root, in the same form as
          ContentEntry.path. Absolute, scheme-bearing, authority-bearing and
          traversing locators are refused as written with CONTENT_PATH_REFUSED,
          never normalised and then created. A locator with a reserved segment
          is refused with CONTENT_RESERVED_PATH

  RepositoryEstablishment:
    description: What a create did and did not complete. Written durably before
      the backend is touched, and updated as each step succeeds, so a crash
      leaves a record of something that may not have happened rather than
      something that happened with no record
    fields:
      reserved_at:
        type: timestamp
        required: true
        description: When the declaration was recorded. Always earlier than the
          store it governs
      store_created:
        type: boolean
        required: true
        description: Whether the backend has reported the store into existence
      custody_verified:
        type: boolean
        required: true
        description: Whether attestations were demonstrated against the store
          that now exists. False while state is establishing
      attempts:
        type: integer
        required: true
        description: How many establishes have run against this reservation.
          More than one is a resumption, never a second store
      last_attempt_at:
        type: timestamp
        required: false
      last_error_code:
        type: string
        required: false
        description: The code the most recent attempt stopped on
      last_error:
        type: string
        required: false

  RepositoryDeclaration:
    description: A request to bring a store under governance. Claims only —
      custody and attestations are demonstrated before they take effect, and
      the ceiling is derived from what was demonstrated
    fields:
      id:
        type: string
        required: true
        description: Stable identifier, chosen by the caller. Unique within
          scope_path. Survives rename and re-placement
      scope_path:
        type: string
        required: true
        description: tenant/org/project confinement this repository will belong
          to. Also the resource scope the enforcement decision is made on
      placement:
        type: Placement
        required: true
        description: Which backend, and where within it. The caller names a
          backend the service holds and a locator relative to its root; it
          never supplies a location
      disposition:
        type: enum
        values: [establish, adopt]
        required: true
        description: establish creates the store, expects it to hold nothing
          afterwards, and additionally requires the content:establish
          capability; adopt expects entries and requires if_match over a census
          the service issued. There is no default — see
          CONTENT_DISPOSITION_REQUIRED
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: false
        description: What the caller claims. Absent is opaque, recorded as a
          degradation. Never inferred from a path, URL or provider name
      attestations:
        type: CustodyAttestations
        required: false
        description: What the caller claims the backend can demonstrate. An
          undemonstrated claim is recorded false
      if_match:
        type: string
        required: false
        description: The census digest this declaration is adopting against.
          Required for adopt, refused for establish
      self_decision_ceiling:
        type: ScopeLevel
        required: false
        description: The highest scope at which a requester may apply their own
          proposal. Absent means no requester may. Declaring it requires
          content:decide as well as content:declare, so only a person declares
          it. Not configurable

  ContentAdoption:
    description: What a placement holds, issued by the service so a caller can
      adopt it knowingly. Returned with CONTENT_ADOPTION_UNSEEN, and recorded
      on the declaration that follows
    fields:
      scope_path:
        type: string
        required: true
      digest:
        type: string
        required: true
        description: Census digest over the ordered (path, entry digest) pairs.
          The value a subsequent declaration passes as if_match
      entries:
        type: integer
        required: true
        description: How many entries the census found. Zero means the
          placement is empty and establish is the correct disposition
      unreadable:
        type: integer
        required: true
        description: How many entries could not be read. Their identity is
          unknown, and adopting them adopts content the service cannot digest
      backend_report:
        type: object
        required: false
        description: The facts beyond its entries that the blueprint specifying
          the placement's backend binds into the census, in the form that
          blueprint declares. When present, digest covers it
      issued_at:
        type: timestamp
        required: true

  ReplicaDeclaration:
    description: The body of POST /v1/content/repositories/{repository}/replicas.
      Claims only — custody, attestations and anonymous read are demonstrated
      against the destination before they take effect
    fields:
      id:
        type: string
        required: true
        description: Stable identifier, chosen by the caller. Unique within the
          repository
      destination:
        type: Placement
        required: true
        description: Which backend, and where within it, the replica is sent
          to. Resolved and confined as a repository's placement is
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: false
        description: What the caller claims about who else can reach the
          destination. Absent is opaque
      attestations:
        type: CustodyAttestations
        required: false
        description: What the caller claims the destination can demonstrate.
          An undemonstrated claim is recorded false
      if_match:
        type: string
        required: false
        description: The digest of the ReplicaCensus this declaration confirms.
          Absent returns the census and declares nothing

  ReplicaCensus:
    description: What a replica would receive, issued by the service so a
      person can declare it knowingly. Returned with CONTENT_REPLICA_UNSEEN
    fields:
      repository:
        type: string
        required: true
      digest:
        type: string
        required: true
        description: Computed as an adoption census digest is, over the ordered
          (path, entry digest) pairs of every version that would leave,
          followed by the pair that binds backend_report where there is one.
          The value a confirming declaration passes as if_match
      entries:
        type: integer
        required: true
        description: How many entries the repository holds now
      versions:
        type: integer
        required: true
        description: How many versions would leave, the entries now included.
          Equal to entries where the backend keeps no versions
      history_only:
        type: list
        required: true
        description: Paths an earlier version holds and no entry holds now
      unreadable:
        type: integer
        required: true
        description: How many versions could not be read. Their identity is
          unknown
      highest_scope:
        type: ScopeLevel
        required: false
        description: The highest scope recorded for anything that would leave.
          Absent when none is recorded
      unclassified:
        type: integer
        required: true
        description: How many versions carry no scope a person declared. Never
          assumed to be at any level
      above_ceiling:
        type: list
        required: true
        description: Each path, with its scope, that would leave above the
          prospective replica ceiling. Non-empty refuses the declaration
      reserved:
        type: list
        required: true
        description: Each reserved path in anything that would leave. Non-empty
          refuses the declaration
      held_by:
        type: enum
        values: [tenant, third-party]
        required: true
        description: Who holds the destination, as its backend declares
      prospective_ceiling:
        type: ScopeLevel
        required: true
        description: The replica's ceiling as its claims would derive it. The
          demonstration can only lower it
      prospective_repository_ceiling:
        type: ScopeLevel
        required: true
        description: The repository's ceiling once the replica counts, as its
          claims would derive it
      backend_report:
        type: object
        required: false
        description: What the blueprint specifying the repository's backend
          binds into the census about what would leave, in the form that
          blueprint declares. When present, digest covers it
      issued_at:
        type: timestamp
        required: true

  ContentReplica:
    description: A copy of a repository kept at a destination, sent to and
      never read from
    fields:
      repository:
        type: string
        required: true
      id:
        type: string
        required: true
        description: Stable identifier, unique within the repository
      destination:
        type: Placement
        required: true
        description: As resolved at declaration and recorded
      state:
        type: enum
        values: [establishing, current, behind, diverged, unreachable, retired]
        required: true
      establishment:
        type: ReplicaEstablishment
        required: false
        description: Present while state is establishing, and on a replica
          whose declaration did not finish
      held_by:
        type: enum
        values: [tenant, third-party]
        required: true
        description: Who holds the destination, as its backend declared it when
          the replica was declared
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: true
        description: Who else can reach the destination, as demonstrated.
          Undeclared is opaque
      attestations:
        type: CustodyAttestations
        required: true
        description: What the destination demonstrated. Unknown is false
      anonymous_read:
        type: enum
        values: [refused, readable, unknown]
        required: true
        description: Whether the destination can be read with no credential.
          readable and unknown both give the replica the ceiling public
      ceiling:
        type: ScopeLevel
        required: true
        description: Derived from what the destination demonstrated. Never
          configured
      credential:
        type: string
        required: false
        description: The part of the replica's credential a person registers at
          the destination, in the form the backend's blueprint declares. The
          secret part is never returned. Absent once retired
      credential_fingerprint:
        type: string
        required: false
        description: Names the credential without carrying it, in the form the
          backend's blueprint declares
      first_sent_at:
        type: timestamp
        required: false
        description: When the destination was first sent anything. From then on
          the replica counts toward effective custody, retired or not
      behind_by:
        type: integer
        required: false
        description: Versions recorded and not yet sent, as of checked_at.
          Absent when it cannot be established, never 0 then
      held_path:
        type: string
        required: false
        description: The path of the version the service will not send, while
          state is behind because of it
      held_reason:
        type: enum
        values: [above-ceiling]
        required: false
        description: Why held_path is held
      checked_at:
        type: timestamp
        required: false
        description: When the destination was last checked. Absent means never
      verified_at:
        type: timestamp
        required: false
        description: When custody, attestations and anonymous read were last
          demonstrated
      declared_by:
        type: string
        required: true
        description: Witnessed. The identity id of the person who declared it
      declared_at:
        type: timestamp
        required: true
      correlation_id:
        type: string
        required: true
        description: The enforcement decision that admitted the declaration
      retired_by:
        type: string
        required: false
        description: Witnessed. The identity id of the person who retired it
      retired_at:
        type: timestamp
        required: false
      backend_report:
        type: object
        required: false
        description: What the blueprint specifying the destination's backend
          says it reports about the destination — for a diverged replica, what
          was found there — in the form that blueprint declares

  ReplicaEstablishment:
    description: What a replica declaration did and did not complete. Written
      durably before the credential is created, and updated as each step
      succeeds, in the manner of RepositoryEstablishment
    fields:
      reserved_at:
        type: timestamp
        required: true
      credential_created:
        type: boolean
        required: true
        description: Whether the replica's credential exists
      destination_verified:
        type: boolean
        required: true
        description: Whether the destination was demonstrated. False while
          state is establishing
      attempts:
        type: integer
        required: true
        description: How many declarations have run against this reservation.
          More than one is a resumption, never a second credential
      last_attempt_at:
        type: timestamp
        required: false
      last_error_code:
        type: string
        required: false
      last_error:
        type: string
        required: false

  DeclinedRepository:
    description: A repository that was declared and could not be recorded. It
      is reported rather than omitted, so a caller can tell a tenant with no
      repositories from a tenant whose repositories were refused
    fields:
      id:
        type: string
        required: true
      scope_path:
        type: string
        required: true
      code:
        type: string
        required: true
        description: The error code the declaration was refused with
      reason:
        type: string
        required: true
      declined_at:
        type: timestamp
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
        description: Witnessed. The identity id of the subject who prepared
          the change — the writer on a direct write, the proposer on a change
          that applied a proposal. Taken from the verified token's identity_id
          claim, never from sub and never from a request body
      on_behalf_of:
        type: string
        required: false
        description: Asserted. The identity id of the person the proposer acted
          for, as the proposal stated it. Absent on a direct write, whose
          writer is a person acting for themselves
      approved_by:
        type: list
        required: false
        description: Witnessed. The identity ids of the persons whose decision
          applied the change — one, under this contract, taken from the
          decider's token. Present exactly when proposal is. Not a signature
      proposal:
        type: string
        required: false
        description: Recorded. The id of the ContentProposal this change
          applied. Absent on a direct write
      separation:
        type: enum
        values: [independent, self]
        required: false
        description: Recorded. Present exactly when proposal is. self when the
          person who decided was the proposal's actor or on_behalf_of, which
          the repository's self_decision_ceiling allowed
      version:
        type: string
        required: false
        description: Recorded. The backend's own marker for the state this
          change produced — a version-controlled backend's revision id. A
          locator, never an identity, and nothing joins on it. Absent when the
          backend keeps none
      correlation_id:
        type: string
        required: true
        description: The enforcement decision that authorised this change — on
          a change that applied a proposal, the decider's, whose audit entry
          names the identity in approved_by
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
        description: False unless effective_custody is exclusive. The service
          cannot see the path around itself, or a reader of a copy
      principals:
        type: list
        required: false
        description: Present only when enumerable_principals is attested

  ProposalRequest:
    description: The body of POST /v1/content/proposals. A change to one entry,
      staged for a person to decide. Writes nothing
    fields:
      repository:
        type: string
        required: true
      change:
        type: ProposedChange
        required: true
        description: path, and action — create, modify or delete. Its text
          fields, original, modified and diffs, are not read
      bytes:
        type: string
        required: false
        description: The proposed bytes, as standard base64 (RFC 4648 §4), the
          encoding PUT /v1/content/entry carries them in. Required for create
          and modify, absent on delete
      if_match:
        type: string
        required: true
        description: As PUT /v1/content/entry takes it. The digest of the entry
          the proposal replaces or removes for modify and delete; the empty
          string for create
      scope:
        type: ScopeLevel
        required: false
        description: The declared scope of the proposed bytes. Required for
          create and modify, absent on delete
      on_behalf_of:
        type: string
        required: false
        description: Asserted. The identity id of the person the caller acted
          for. A client carrying out a person's instruction under its own
          service identity MUST send it. Never a scheduled job, which names
          itself in run
      agent:
        type: string
        required: false
        description: Asserted. The agent that prepared the change. A client
          submitting a change an agent prepared MUST send it
      run:
        type: string
        required: false
        description: Asserted. The run that prepared the change — an agent's
          run, or a scheduled job's. A client submitting a change an agent or a
          schedule prepared MUST send it
      reason:
        type: string
        required: false
        description: Asserted. Why, in the proposer's words

  ContentProposal:
    description: A change to one entry, recorded and not made. Returned by
      every proposal route
    fields:
      id:
        type: string
        required: true
        description: Assigned by the service. Stable and never reused
      repository:
        type: string
        required: true
      change:
        type: ProposedChange
        required: true
        description: path and action
      bytes:
        type: string
        required: false
        description: The proposed bytes, as base64. Present only when one
          proposal is read by id, by a caller the Proposal Read Flow allows. A
          listing omits it. Absent on delete
      before:
        type: ContentIdentity
        required: false
        description: The identity of the entry the proposal was made against.
          Absent on create
      after:
        type: ContentIdentity
        required: false
        description: Computed by the service over the bytes it holds for the
          proposal, never taken from the request. Absent on delete
      scope:
        type: ScopeLevel
        required: false
        description: The declared scope of the proposed bytes. Absent on delete
      state:
        type: enum
        values: [open, applied, rejected, stale]
        required: true
        description: open until a person decides. Every other state is final
      base:
        type: enum
        values: [current, moved, unknown]
        required: false
        description: Present while state is open. Whether the entry still holds
          before — for a create, whether the path still holds nothing. unknown
          when the entry cannot be read. Computed on every read and listing,
          never stored
      actor:
        type: string
        required: true
        description: Witnessed. The identity id of the proposer, from the
          verified token's identity_id claim
      on_behalf_of:
        type: string
        required: false
        description: Asserted, as the request stated it
      agent:
        type: string
        required: false
        description: Asserted, as the request stated it
      run:
        type: string
        required: false
        description: Asserted, as the request stated it
      reason:
        type: string
        required: false
        description: Asserted, as the request stated it
      proposed_at:
        type: timestamp
        required: true
      correlation_id:
        type: string
        required: true
        description: The enforcement decision that admitted the proposal
      decision:
        type: ProposalDecision
        required: false
        description: Present once state is not open

  ProposalDecision:
    description: What a person decided about a proposal. Recorded once
    fields:
      decision:
        type: enum
        values: [apply, reject]
        required: true
      decided_by:
        type: string
        required: true
        description: Witnessed. The identity id of the person who decided,
          from the verified token's identity_id claim
      decided_at:
        type: timestamp
        required: true
      reason:
        type: string
        required: false
        description: Asserted, as the decision request stated it
      change:
        type: ContentChange
        required: false
        description: The change the decision wrote, carrying approved_by and
          separation. Present when state is applied

  DecisionRequest:
    description: The body of POST /v1/content/proposals/{id}/decision
    fields:
      decision:
        type: enum
        values: [apply, reject]
        required: true
      reason:
        type: string
        required: false

  ProposalQuery:
    description: The query of GET /v1/content/proposals
    fields:
      repository:
        type: string
        required: false
        description: Absent lists every repository in the caller's scope
      path:
        type: string
        required: false
        description: Proposals for this entry only
      state:
        type: enum
        values: [open, applied, rejected, stale]
        required: false
        description: Absent lists every state
      cursor:
        type: string
        required: false
      limit:
        type: integer
        required: false

  ProposalPage:
    description: One page of GET /v1/content/proposals, in the order the
      proposals were recorded, oldest first, so a cursor survives proposals
      made while paging
    fields:
      proposals:
        type: list
        required: true
        description: ContentProposal records the caller may read, each without
          bytes
      withheld:
        type: integer
        required: true
        description: How many proposals this page omitted because the caller
          may not read the entry they would change. Zero means none was
          omitted
      next_cursor:
        type: string
        required: false
        description: Absent on the last page
```

---

## Configuration

```yaml
content:
  backends:
    - name: <backend-name>       # what a placement names
      driver: <driver-name>      # the blueprint that specifies this backend, by
                                 # the driver name that blueprint declares. Its
                                 # root, options and credentials are that
                                 # blueprint's, per Design Principle 6
      held_by: tenant|third-party  # who holds the store it reaches. Absent is
                                 # third-party. Read when it is a replica's
                                 # destination
  repositories:
    - id: <stable-id>
      scope_path: <tenant>/<org>[/<project>]
      placement:
        backend: <backend-name>  # must be one of the names above
        locator: <path relative to that backend's root>
      custody: exclusive|shared|opaque
      attestations:
        enumerable_principals: <bool>
        attributable_writes: <bool>
        tamper_evident: <bool>
  reconcile_interval: 15m        # shared custody only; 0 disables scheduled runs
  reverify_custody_interval: 24h # the store's, and each replica's
  replica_retry_interval: 15m    # how often a replica that lacks versions is
                                 # sent them, besides after each version
  max_entry_bytes: 10485760
```

`held_by` is an operator's statement about a host, made where the host is
named. It decides whether a replica sent there is a third party's (see
[A third party's replica waits for classification](#a-third-partys-replica-waits-for-classification)),
and it is never inferred from the host's name. No key declares a replica: see
[Declaring a replica](#declaring-a-replica).

The placement rule is the same in configuration as it is in a request, and it
is not a formality here either: `backends` is where a root is named, and a
repository names a backend. A configuration that could give a locator without a
backend would be a file that writes anywhere, read at boot, with no caller and
no capability to check.

Configuration declares what a repository **claims**. Every claim is
demonstrated before it takes effect: an attestation asserted here and not
demonstrated at verification becomes `false`, and the ceiling follows the
demonstration, not the claim.

A configured repository carries no `self_decision_ceiling`, so nobody may
decide their own proposal in it. See
[Separation of duties](#separation-of-duties).

**A configuration entry is processed as `establish`, and that is a limit rather
than a choice.** Adoption requires `if_match` over a census the service issued,
and a static file cannot hold a value that did not exist when it was written.
So a configured entry whose placement already holds entries is refused with
`CONTENT_NOT_EMPTY`, and adopting it is an act somebody performs through
`POST /v1/content/repositories` after reading what is in there. This is the
whole point of the disposition rule and MUST NOT be relaxed for configuration:
a file that could adopt would adopt on every fresh start, unread.

**A configured entry therefore creates**, with the same obligations, the same
reserve-create-confirm ordering and the same reported incompleteness as a
request. It needs no capability, because there is no caller: an operator who can
write `.weblisk/config.yaml` already holds more than any capability confers, and
inventing a check against a principal that does not exist would be theatre. What
it does need is the reservation, because a hub crashing mid-boot is at least as
likely as a client timing out.

**Reading the file again is not a new act.** A configured entry whose `id`,
`scope_path` and `placement` match an already-`declared` repository is
**reconciled, not re-declared**: its claimed attestations are re-verified by the
ordinary re-verification flow, and nothing is created. Without that rule a
configured repository would be refused with `CONTENT_REPOSITORY_EXISTS` on every
start after the first, and would report `degraded` for the rest of its life for
having worked.

This is the one place where configuration and the API deliberately differ, and
the difference is what the two things *are*. The file is declarative — it states
which repositories exist, and re-reading a statement asserts nothing new. The
endpoint is imperative — it asks for one to be made, and asking twice is two
asks. Hence a repeated `POST` against a `declared` repository is
`CONTENT_REPOSITORY_EXISTS` while a repeated boot is silent, and neither of them
creates a second store.

**A configured entry that matches an `establishing` repository resumes it**, on
exactly the rule a retried request follows. The boot path *is* the retry path,
and it runs on every start, which is what stops a hub that died mid-create from
needing an operator to notice.

**A refused entry is reported, never dropped.** It is recorded as a
`DeclinedRepository`, `GET /v1/content/repositories` returns it beside the
repositories that were recorded, and health reports `degraded` naming it. A
caller must be able to tell a tenant with no repositories from a tenant whose
repositories were refused — a listing that silently omits them is a confident
zero, and the caller's next act is to conclude the tenant governs nothing.

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
    - boundary: Content → Reserved state. Installation state (`.weblisk`) and
        control state (`.git`, and what the backend declares) are never
        reachable through this service
    - boundary: Proposal → Entry. Crossed only by a person's decision, and only
        against the bytes the proposal was made on
    - boundary: Content Service → Replica. Crossed outward only. Nothing a
        destination holds is read back as content, history or truth

  enforcement:
    - rule: A replica is declared only by a person who has seen what would
        leave
      mechanism: Two-step declaration; the first call returns the census and
        records nothing. content:replicate and content:connect are both
        required and both person only
    - rule: A replica is never read from, and a diverged one is never
        overwritten
      mechanism: Replica Sender sends from the service's own record and asks a
        destination only whether it holds just what was sent; a destination
        holding anything else stops sending
    - rule: A replica whose destination a third party holds is refused unless
        the classification gate is present and passes
      mechanism: held_by on the destination's backend, absent meaning
        third-party; CONTENT_REPLICA_UNCLASSIFIED
    - rule: A repository's ceiling is the lowest of every place its bytes live,
        and retiring a replica never raises it
      mechanism: ceiling is derived from the store and every replica sent
        anything, retired or not, and from any copy the backend reports that no
        replica declares
    - rule: A replica's credential is the tenant's, for one destination
      mechanism: Created by the service at declaration, held through
        patterns/secrets, presented only at that destination, destroyed at
        retirement. Its secret part is never returned
    - rule: A replica is never configured
      mechanism: No configuration key declares one; the census digest a
        declaration needs cannot exist in a file
    - rule: A write, a removal or a proposal without a precondition is refused
      mechanism: Precondition Gate; if_match is required. The empty string is
        the precondition that nothing is there, and no value matches anything
    - rule: A write whose scope exceeds the repository ceiling is refused, never
        downgraded
      mechanism: Ceiling check before the storage proxy, publishing
        content.ceiling_exceeded
    - rule: An undeclared or unverified repository is treated as opaque
      mechanism: Registry default; attestation defaults to false
    - rule: A declaration with no disposition is refused
      mechanism: disposition is a required field of RepositoryDeclaration
    - rule: A declaration adopting a placement is refused unless it carries the
        census digest the service issued for that placement
      mechanism: Two-step adoption; the first call returns the census and
        declares nothing, so bytes cannot be adopted unseen
    - rule: A declaration establishing over a placement that already holds
        entries is refused, never adopted instead
      mechanism: Emptiness check before the registry write
    - rule: The ceiling on a new repository is derived from demonstrated
        attestations and is never read from the request
      mechanism: RepositoryDeclaration carries no ceiling field
    - rule: A declaration names a backend the service already holds and a
        locator relative to that backend's root. A request never supplies a
        location
      mechanism: Placement resolution against the backends held for that
        scope_path, then Path Resolver confinement. A create that accepted an
        absolute path would be an arbitrary-write primitive
    - rule: Creating a store requires content:establish in addition to
        content:declare
      mechanism: Capability intersection, checked before the reservation.
        adopt is unaffected, so no existing grant gains a power by this rule
        existing
    - rule: A store is never brought into existence before the declaration that
        governs it is durable
      mechanism: reserve, then create, then confirm. The record precedes the
        irreversible act, so no store can exist that nothing knows of
    - rule: A create that did not finish is neither reported as success nor as
        nothing having happened
      mechanism: CONTENT_ESTABLISH_INCOMPLETE carrying the repository and its
        RepositoryEstablishment; state establishing in the listing; health
        degraded naming it
    - rule: A retried establish never creates a second store
      mechanism: The placement is reserved durably before creation. An
        identical retry resumes; one differing in any argument is
        CONTENT_REPOSITORY_EXISTS
    - rule: A store this service established is empty, and this service writes
        nothing into it
      mechanism: No placeholder entry, ever. A backend that cannot represent an
        empty store declares CONTENT_ESTABLISH_UNSUPPORTED instead
    - rule: Declaring a repository requires content:declare, which writing an
        entry does not confer
      mechanism: Separate capability; the orchestrator refuses an unregistered
        capability name at registration
    - rule: A path containing a traversal segment or resolving outside the
        repository through a symlink is refused as written
      mechanism: Path Resolver; refusal rather than normalisation
    - rule: A path with a reserved segment is refused, on every backend
      mechanism: Reserved-path check in the resolver, applied to every
        operation and to a placement's locator, comparing each segment as any
        filesystem could resolve it rather than byte for byte, the same way on
        every backend
    - rule: Only a person moves an entry
      mechanism: content:write and content:decide are person only in
        protocol/types. A hub grants neither to a service subject, mints no
        token for one that carries either, and refuses a registration that
        declares either. This service honours them only on a token of type
        operator. A console runs every agent under its own service identity.
        What the tenant cannot see, a person's credential used by software, is
        stated with the rule
    - rule: Only a person allows self-decision
      mechanism: A declaration carrying self_decision_ceiling requires
        content:decide as well as content:declare
    - rule: A proposal writes nothing
      mechanism: Proposed bytes are held in the service's own state, never in
        the repository, until a decision applies them
    - rule: A proposal's bytes are read only by a caller who may read the entry
        it would change
      mechanism: Proposal Read Flow; the storage proxy runs read at the higher
        of the proposal's scope and the entry's, for proposer and decider
        alike, and a page omits and counts what it denies
    - rule: Proposed bytes arrive exactly as sent
      mechanism: bytes travel as base64 and after is computed over the decoded
        bytes. No text field is read
    - rule: A proposal whose base has moved on is never applied and never merged
      mechanism: The proposal's before is the precondition of the write that
        applies it. A mismatch refuses the decision and records the proposal
        stale
    - rule: A requester does not decide their own proposal above the scope the
        repository allows
      mechanism: Decider compared against the proposal's actor and on_behalf_of
        before the write; self_decision_ceiling is declared by a caller and is
        never configured
    - rule: Who a change was for says what stands behind each part of it
      mechanism: actor, approved_by and decided_by are the identity_id claim
        of the verified token, never its sub; on_behalf_of, agent and run are
        recorded as asserted; approved_by is never reported as a signature. A
        token without identity_id cannot write, remove, propose or decide
    - rule: An access statement from a repository whose effective custody is
        shared or opaque is marked incomplete
      mechanism: access_complete is derived from effective_custody and cannot
        be set by a caller
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

- **The backend adapter surface is five operations, and creation is an optional
  sixth** — read, write, list, stat, delete, and `create`. A backend that cannot
  express one of the five is not disqualified; it declares the corresponding
  attestation `false` and accepts the lower ceiling. A backend that cannot
  express `create` is not disqualified either; it declares so, `establish`
  against it is refused with `CONTENT_ESTABLISH_UNSUPPORTED`, and `adopt`
  against it is unchanged. The asymmetry is deliberate: a missing attestation
  lowers a ceiling, a missing `create` removes an operation, and collapsing the
  two would mean faking creation with a placeholder entry.

- **Reserve before creating, never the other way round.** The temptation is the
  opposite order, because creating first means never recording a repository
  whose store failed to appear. That trade is the wrong way up: a record with no
  store is visible, reported and retryable, while a store with no record is
  invisible and permanent. Prefer the failure you can see.

- **Resolve a placement once, at declaration, and record what it resolved to.**
  Re-resolving per request makes confinement a function of configuration that
  may have changed since. A backend renamed or re-rooted under a declared
  repository must surface as a failure to reach it — not as a repository that
  quietly moved and kept its ceiling.

- **An absent locator and an empty store are the same answer to a census, and
  that is correct.** Both give `entries: 0`. Do not improve on it by
  distinguishing them, because the only use for the distinction is to let
  `adopt` create the absent one so it has something to count, and `adopt` never
  creates.

- **`attempts` is a count, not a limit.** Nothing in this contract gives up on a
  reservation after N tries, because there is no verb that retires one and
  abandoning it would strand the id. A backend that fails forever is a
  `degraded` health report forever, which is the honest reading of the
  situation.

- **Compute the census at adoption, not at the first read.** Deferring it
  means the repository is governed before anything is known about what is in
  it, and the window between the two is exactly when a report claims coverage
  it does not have.

- **A census of an unreadable entry is not a census without it.** An entry that
  cannot be read is counted in `unreadable` and included in the digest by path
  with its identity marked unknown, per `CONTENT_UNREADABLE`. Silently skipping
  it would make the digest stable across a change in the one place the service
  can see least.

- **Retirement, not deletion.** A removed entry's identity is retired per
  `patterns/content-identity` Design Principle 6. A reference to it resolves to
  "removed at version N", never to nothing and never to a later entry that
  reused the path.

- **Compare reserved names the way any filesystem could open them.** Fold
  case, drop trailing dots and spaces, drop code points a filesystem ignores,
  and read short names and alternate data streams as the names they resolve
  to, before comparing. Do it on every backend, whether or not the filesystem
  under this one does any of it, and on every segment, not on a prefix. Git
  applies the same comparison to its own control path when both
  `core.protectNTFS` and `core.protectHFS` are set, and those checks are a
  reference for the full set. A check that passes `.WEBLISK/secrets` on a
  case-insensitive filesystem has checked the spelling and let the kernel open
  the keys.

- **Hold the proposed bytes, not a patch.** Applying a proposal writes exactly
  the bytes that were proposed, over exactly the bytes they were proposed
  against. A patch re-applied to whatever is there now is a merge by another
  name, and it produces text the decider never saw.

- **Record the change and the proposal's new state in one write.** A change
  recorded without its proposal becoming `applied` leaves an open proposal
  that can never be applied again; the reverse leaves an applied proposal with
  no change to show for it.

- **Decode, then digest; never read bytes as text.** A proposal's bytes, like
  a write's, are decoded from base64 and digested as decoded. Reading them
  through a text field lets a parser replace what is not valid UTF-8, and the
  digest then describes bytes the proposer never sent.

- **Check the entry's scope on every proposal read.** A proposal carries the
  bytes of a change to an entry, so reading it is reading that entry. A check
  made once, when the proposal was recorded, has nothing to say about a caller
  who asks today.

- **Compute `base` when asked, never store it.** An entry can change between
  one listing and the next, and a stored `current` is a claim about a moment
  that has passed.

- **Send a replica from the service's own record, never from the store.** A
  store under shared custody can be changed between the moment a version was
  recorded and the moment it is sent, and so can the store's own idea of where
  its copies go. What a replica receives is what the service recorded.

- **Ask a destination one question.** Before sending, the service checks that
  the destination holds only what it sent. That is the only thing it ever
  reads there, and the answer is used to stop, never to take anything in.

- **An unknown anonymous read is `public`.** A test that could not finish has
  not shown that strangers are refused, and Design Principle 2 counts what was
  not shown as false. The remedy is to make the test finish, not to assume it
  would have passed.

- **Hold, do not skip.** A version that may not be sent stops everything after
  it. Sending the later versions past it would leave the destination with a
  history that silently lacks one, which is worse than a destination that is
  visibly behind.

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
- [ ] An `AccessStatement` from a repository whose `effective_custody` is shared or opaque carries `access_complete: false`, and no caller can set it to true
- [ ] A path containing a `..` segment is refused as written rather than normalised
- [ ] A symlink inside a repository pointing outside it is refused
- [ ] A path resolving into `.weblisk/` is refused for every operation including list and stat
- [ ] An unreadable entry yields state `unknown`, never `stale`, `current` or `removed`
- [ ] A repository whose re-verification lowers its ceiling publishes `content.custody_degraded` naming the content now above it, and no content is moved or reclassified
- [ ] Every content operation appears in the enforcement audit trail with the correlation id recorded on the resulting `ContentChange`
- [ ] A repository declaration appears in the enforcement audit trail with operation `create` and the declared `scope_path` as the resource scope, including the declaration that was refused
- [ ] A declaration with `disposition: establish` carrying `if_match` is refused with `CONTENT_PRECONDITION_NOT_APPLICABLE`
- [ ] With no orchestrator URL configured, the service starts, serves `GET /v1/health`, and does not exit
- [ ] With no orchestrator URL configured, every protected endpoint refuses with `401` and a structured `ErrorResponse`
- [ ] With no orchestrator URL configured, health reports `degraded` and names the absent orchestrator — never `healthy`, never `unhealthy`
- [ ] A declaration with no `disposition` is refused with `CONTENT_DISPOSITION_REQUIRED`, and nothing is recorded
- [ ] A declaration with `disposition: establish` over a placement holding entries is refused with `CONTENT_NOT_EMPTY`, and the entries are neither adopted nor touched
- [ ] A first declaration with `disposition: adopt` and no `if_match` is refused with `CONTENT_ADOPTION_UNSEEN`, returns a `ContentAdoption`, and records no repository
- [ ] A declaration with `disposition: adopt` whose `if_match` does not equal a freshly computed census digest is refused with `CONTENT_PRECONDITION_FAILED`
- [ ] A declaration re-using an id already declared at that `scope_path` is refused with `CONTENT_REPOSITORY_EXISTS`, and the declared repository is unchanged
- [ ] A declaration whose placement equals, contains or sits inside a declared repository's is refused with `CONTENT_PLACEMENT_DECLARED`
- [ ] Every entry present at adoption is recorded with provenance `unknown`, never `authored` and never `external`
- [ ] A declaration claiming attestations that are not demonstrated is recorded with the demonstrated set, and its ceiling follows the demonstrated set
- [ ] A declaration carrying no `custody` is recorded `opaque` with the `internal` ceiling, and the degradation is recorded
- [ ] A configured repository whose placement is not empty is refused, appears in `GET /v1/content/repositories` as a `DeclinedRepository`, and health reports `degraded` naming it
- [ ] `content:declare` is required to declare a repository, and a caller holding only `content:write` is refused
- [ ] A declaration whose placement names a backend the service does not hold for that `scope_path` is refused with `CONTENT_BACKEND_UNKNOWN`, and the refusal does not disclose whether that name exists under another scope
- [ ] A declaration whose placement locator is absolute, carries a scheme or an authority, or contains a `..` segment is refused as written with `CONTENT_PATH_REFUSED`, and nothing is created anywhere
- [ ] A successful `establish` leaves a store that `GET /v1/content` lists as an empty page, that survives a restart of the service, and that a subsequent write succeeds against with no further step
- [ ] A successful `establish` leaves no entry at all in the store it created, and a census over it returns the digest of the empty set
- [ ] `establish` against a backend that cannot create is refused with `CONTENT_ESTABLISH_UNSUPPORTED`, no placeholder is written, and `adopt` against that same backend succeeds
- [ ] The declaration is durable with `state: establishing` before the adapter is asked to create anything, demonstrated by killing the service between the two and finding the record on restart
- [ ] A repository in `establishing` appears in `GET /v1/content/repositories` reporting `custody: opaque`, every attestation `false`, `ceiling: internal` and no `verified_at`; it serves no read, accepts no write, and health reports `degraded` naming it
- [ ] A create that fails after the store exists answers `CONTENT_ESTABLISH_INCOMPLETE` with `store_created: true`, and no repository is reported as declared
- [ ] A repeated `establish` with identical arguments against a repository in `establishing` completes it, creates no second store, and increments `attempts`
- [ ] A repeated `establish` differing in `placement`, `custody` or `attestations` is refused with `CONTENT_REPOSITORY_EXISTS`, and the reserved declaration is unchanged
- [ ] A repeated `establish` with identical arguments against a repository already `declared` is refused with `CONTENT_REPOSITORY_EXISTS` and is not treated as a no-op
- [ ] A resumed `establish` whose store has since been written to is refused with `CONTENT_NOT_EMPTY`, and the entries are neither adopted nor touched
- [ ] A caller holding `content:declare` and not `content:establish` is refused `disposition: establish` and succeeds at `disposition: adopt`
- [ ] A configured repository already `declared` with the same `id`, `scope_path` and `placement` is reconciled on every subsequent start — nothing is created, nothing is refused, and health does not report `degraded` for it
- [ ] A configured repository left `establishing` by a crashed boot is resumed on the next start with no operator action
- [ ] With an orchestrator URL configured, a failed registration is fatal
- [ ] A read, write, stat, list or proposal naming `.git`, `.GIT`, `.git.`, `git~1` or `docs/.git/config` is refused with `CONTENT_RESERVED_PATH`, and nothing is written
- [ ] A path naming `.WEBLISK/keys` is refused with `CONTENT_RESERVED_PATH`, exactly as `.weblisk/keys` is
- [ ] A declaration whose `placement` `locator` has a `.git` or `.weblisk` segment is refused with `CONTENT_RESERVED_PATH`, and nothing is created
- [ ] A path segment `.gitignore` is not refused as reserved
- [ ] `GET /v1/content` over a directory that holds a `.git` directory returns no entry for that `.git` directory or anything inside it, and lists the entries beside it unless the backend's blueprint reserves them; a `ContentAdoption` census over it neither counts nor digests anything inside the `.git`
- [ ] A path whose segment is `.GIT`, `.git.`, `.git ` or `git~1` is refused with `CONTENT_RESERVED_PATH` on a backend whose filesystem distinguishes case and keeps trailing dots, exactly as on one that does not
- [ ] `POST /v1/content/proposals` returns a `ContentProposal` with `state` `open`, and the entry's digest is unchanged
- [ ] A `ProposalRequest` with no `if_match` is refused with `CONTENT_IF_MATCH_REQUIRED`, whatever its `action`
- [ ] A `ProposalRequest` with `action` `create` and an `if_match` other than `""`, or with `action` `modify` or `delete` and `if_match` `""`, is refused with `CONTENT_PRECONDITION_NOT_APPLICABLE`
- [ ] A `ProposalRequest` with `action` `create` and `if_match` `""` at a path that holds an entry is refused with `CONTENT_PRECONDITION_FAILED`, and no proposal is recorded
- [ ] A `ProposalRequest` whose `action` is not `create`, `modify` or `delete`, whose `bytes` or `scope` is missing on `create` or `modify` or present on `delete`, or whose `bytes` is not valid base64, is refused with `INVALID_REQUEST`, and no proposal is recorded
- [ ] A proposal of bytes that are not valid UTF-8 records an `after` equal to the digest of exactly those bytes, and applying it writes exactly those bytes
- [ ] `PUT /v1/content/entry` with `if_match` `""` creates the entry at a path that holds none, and is refused with `CONTENT_PRECONDITION_FAILED` at a path that holds one
- [ ] `DELETE /v1/content/entry` with `if_match` `""` is refused with `CONTENT_PRECONDITION_NOT_APPLICABLE`
- [ ] A `ProposalRequest` whose `if_match` differs from the entry's digest is refused with `CONTENT_PRECONDITION_FAILED`, and no proposal is recorded
- [ ] A `ProposalRequest` whose `scope` exceeds the repository ceiling is refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`, and no proposal is recorded
- [ ] A proposal's `after` equals the digest of the bytes the service holds for it, whatever the request claimed
- [ ] A caller holding `content:propose` and not `content:write` is refused `PUT /v1/content/entry`
- [ ] A caller holding `content:propose` and not `content:decide` is refused `POST /v1/content/proposals/{id}/decision`
- [ ] Applying a proposal whose entry changed after it was made is refused with `CONTENT_PRECONDITION_FAILED` returning both digests, the entry is unchanged, and the proposal's `state` is `stale`
- [ ] Applying a `create` proposal after an entry has appeared at its path is refused with `CONTENT_PRECONDITION_FAILED`, and the proposal's `state` is `stale`
- [ ] A proposal in `state` `applied`, `rejected` or `stale` refuses every further decision with `CONTENT_PROPOSAL_DECIDED`
- [ ] Of two concurrent decisions on one `open` proposal, exactly one is recorded and the other is refused with `CONTENT_PROPOSAL_DECIDED`
- [ ] An `open` proposal whose entry has changed is listed with `base` `moved`, and listing it changes neither the proposal nor the entry
- [ ] A `ContentProposal` in a `ProposalPage` carries no `bytes`, and `GET /v1/content/proposals/{id}` returns them
- [ ] A caller holding `content:read` whom the storage proxy refuses a `restricted` entry is refused `GET /v1/content/proposals/{id}` for a proposal to modify it, and `GET /v1/content/proposals` omits that proposal and counts it in `withheld`
- [ ] A proposer refused `read` on the entry after proposing is refused `GET /v1/content/proposals/{id}` for their own proposal
- [ ] A `ProposalPage` lists proposals oldest first, and a proposal recorded while a caller pages appears on a later page, never on one already returned
- [ ] `content.proposed` and `content.proposal_decided` carry no proposed bytes
- [ ] Applying a `delete` proposal removes the entry and retires its identity, with the storage proxy intercepting `delete` for the decider
- [ ] Applying a proposal records a `ContentChange` whose `actor` is the proposal's `actor`, whose `on_behalf_of` is the proposal's, whose `approved_by` holds the decider's `identity_id`, whose `proposal` is the proposal's `id`, and whose `correlation_id` is the decider's enforcement decision
- [ ] A decision to apply by the proposal's `actor` or `on_behalf_of`, in a repository with no `self_decision_ceiling`, is refused with `CONTENT_SEPARATION_REQUIRED`, and the proposal stays `open`
- [ ] With `self_decision_ceiling` `internal`, the proposal's `on_behalf_of` applying an `internal` proposal succeeds with `separation` `self`, and applying a `confidential` one is refused with `CONTENT_SEPARATION_REQUIRED`
- [ ] A decision to apply by a person who is neither the proposal's `actor` nor its `on_behalf_of` records `separation` `independent`
- [ ] A person whose token's `identity_id` is a proposal's `on_behalf_of`, deciding to apply it in a repository with no `self_decision_ceiling`, is refused with `CONTENT_SEPARATION_REQUIRED` whatever the token's `sub` says
- [ ] The proposal's `on_behalf_of` may reject it with no `self_decision_ceiling` declared, and no `separation` is recorded
- [ ] A `ContentChange` from `PUT /v1/content/entry` carries no `on_behalf_of`, `approved_by`, `proposal` or `separation`
- [ ] A write or proposal whose body names an `actor` records the verified token's `identity_id`, never the named one and never the token's `sub`
- [ ] A write, removal, proposal or decision on a token that carries no `identity_id` is refused with `CONTENT_IDENTITY_REQUIRED`, and nothing is recorded
- [ ] A token whose `type` is not `operator` and whose `cap` holds `content:write` is refused `PUT /v1/content/entry` as though it did not hold it
- [ ] The service's own manifest declares none of `content:write`, `content:decide`, `content:replicate` and `content:connect`, and its registration succeeds
- [ ] A declaration carrying `self_decision_ceiling` from a caller holding `content:declare` and not `content:decide` is refused, and no repository is recorded
- [ ] `ContentChange.version` is absent when the backend keeps no version marker
- [ ] A census over a placement whose backend's blueprint binds a `backend_report` covers that report in its `digest`, and an adoption whose store's report changed since the census is refused with `CONTENT_PRECONDITION_FAILED`
- [ ] A first `POST /v1/content/repositories/{repository}/replicas` with no `if_match` is refused with `CONTENT_REPLICA_UNSEEN`, returns a `ReplicaCensus`, records no replica, creates no credential and sends nothing
- [ ] A replica declaration whose `if_match` differs from a freshly computed census `digest`, because a version was recorded between the two calls, is refused with `CONTENT_PRECONDITION_FAILED`
- [ ] A caller holding `content:replicate` and not `content:connect`, or `content:connect` and not `content:replicate`, is refused a replica declaration; a token whose `type` is not `operator` is refused it whatever its `cap` holds
- [ ] A replica declaration whose destination backend has no `held_by`, or `held_by: third-party`, is refused with `CONTENT_REPLICA_UNCLASSIFIED` where the classification gate is not present, and nothing is recorded or sent
- [ ] A replica declaration where an earlier version holds a path under `.weblisk` is refused with `CONTENT_RESERVED_PATH`, though no entry holds that path now
- [ ] A replica declaration against a destination that holds something this service did not send is refused with `CONTENT_NOT_EMPTY`, and nothing at the destination is changed
- [ ] A confirmed declaration against a destination that has not yet registered the credential answers `CONTENT_ESTABLISH_INCOMPLETE` carrying `credential`, the replica is `establishing`, and nothing has been sent; the same declaration repeated after registration completes it with no second credential
- [ ] Confirming, on an `exclusive` repository, a replica whose destination demonstrates no attestation and refuses anonymous read makes the repository's `ceiling` `internal` and its `effective_custody` `opaque`, leaves `store_ceiling` `critical` and `custody` `exclusive`, and a write declaring `confidential` is then refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`
- [ ] A replica whose destination can be read with no credential, or whose anonymous read could not be tested, has `ceiling` `public`
- [ ] Retiring a replica that was sent anything leaves the repository's `ceiling` and `effective_custody` unchanged, destroys its credential, and deletes nothing at the destination
- [ ] A destination changed by somebody else makes its replica `diverged`; nothing is sent to it, nothing from it enters the repository, and sending resumes by itself once the destination again holds only what was sent
- [ ] A version above a replica's ceiling holds the replica `behind` with `held_path` naming it, and no version recorded after it is sent
- [ ] A backend's report of a copy of the store that no replica declares makes `effective_custody` `opaque`, lowers `ceiling` to `internal` at most, and publishes `content.custody_degraded`
- [ ] No configuration key declares a replica, and a configuration file naming one declares nothing
