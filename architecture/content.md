<!-- blueprint
type: architecture
name: content
version: 4.1.1
requires: [protocol/types, protocol/identity, patterns/content-identity, patterns/scope, patterns/contract, patterns/principal-identity, patterns/approval, patterns/secrets, architecture/enforcement, architecture/storage, architecture/orchestrator]
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
    version: ">=3.0.0 <5.0.0"
    bindings:
      types:
        # The service serves the two probes and renews its lease
        # (protocol/types, Health and Presence)
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: LeaseRenewal
          fields_used: [ready, checks, timestamp]
        - name: ErrorResponse
          fields_used: [code, error, category, retryable]
        # pass_routes is how the admin gateway learns what a person's request
        # may reach here and what each needs. See Registration and
        # Standalone Operation
        - name: AgentManifest
          fields_used: [name, capabilities, pass_routes]
        - name: PassRoute
          fields_used: [method, path, capabilities, body]
        - name: BodyRequirement
          fields_used: [field, equals, capabilities]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, via, action, target, status]
        - name: ProposedChange
          fields_used: [path, action]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=2.1.0 <3.0.0"
    bindings:
      types:
        # identity_id is who a change names; type and aud say a person's
        # request arrived on a pass addressed here; act names the gateway that
        # carried it; identity_key is the person's current identity key;
        # record_keys and cid say which key may sign the change it carries
        - name: WLToken
          fields_used: [cap, identity_id, type, aud, act, identity_key, cid, record_keys]
    # The change statement is a fixed-form statement, registered there
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
    version: ">=2.3.0 <3.0.0"
    bindings:
      types:
        # An enum: it declares values, not fields, so nothing is bound FROM it.
        - name: ScopeLevel
        - name: ScopeDeclaration
          fields_used: [level, context, custom_labels]
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
    version: ">=1.8.0 <2.0.0"
    bindings:
      types:
        # What a change statement carries, so a verifier needs no hub
        - name: Attestation
          fields_used: [identity_id, identity_public_key, credential_public_key, hub_id, purpose, not_after, signature]
      behaviors:
        # What keeps a person-only capability away from a service and an agent
        - name: service-subject-constraints
        - name: agent-delegation
        # Who may sign a change statement, and how it is checked
        - name: record-signing
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
    version: ">=1.1.0 <3.0.0"
    bindings:
      behaviors:
        # How a remote's credential is held (see Declaring a remote)
        - name: secret-access
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/enforcement
    version: ">=2.0.0 <3.0.0"
    bindings:
      types:
        - name: ViolationRecord
          fields_used: [boundary, agent, operation, violation_type, scope_required, scope_actual, detail, severity]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/storage
    version: ">=1.4.2 <2.0.0"
    bindings:
      types:
        # The change log's own key, succession and checkpoint entries
        - name: LogKey
          fields_used: [key_id, public_key, not_after, key_protection, attested_by, attesting_key, signature]
        - name: LogSuccession
          fields_used: [outgoing, outgoing_key, incoming, incoming_key, outgoing_signature, incoming_signature]
        - name: LogCheckpoint
          fields_used: [seq, tip, issued_at, key, signature]
      behaviors:
        - name: sealed-log
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=2.15.0 <4.0.0"
    bindings:
      behaviors:
        # What a pass this service accepts rests on. See Who may move an entry
        - name: token-exchange
          usage: Relied on, never called here. Every pass this service accepts was minted by the exchange, for an operator token the orchestrator judged live then, carrying no capability the person could not use then
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
│  │  Change Log                (one per repository)    │  │
│  │  - every change made or observed, in order         │  │
│  │  - chained, and sealed with ML-DSA-65 checkpoints  │  │
│  │  - held in the service's own state, never content  │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Custody Reconciler        (shared custody only)   │  │
│  │  - detects out-of-band change by digest            │  │
│  │  - records provenance: authored | external         │  │
│  │  - never classifies external change as tampering   │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Remote Sender             (push-only)             │  │
│  │  - sends each remote what it lacks, in order       │  │
│  │  - holds every send until it can leave a           │  │
│  │    signed egress record of what left               │  │
│  │  - from the service's own record, never the store  │  │
│  │  - never reads from a remote                       │  │
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

**Change Log** records every change this service makes to a repository and
every change it observes made around it, one entry each, in order. It is the
evidence of record, and it is signed. See [The Change Log](#the-change-log).

**Custody Reconciler** exists only where a second authority can write. It
converts an unexplained change from an alarm into a recorded fact.

**Remote Sender** sends each of a repository's remotes what it has not yet
received, and takes nothing back. It sends nothing until a send can leave the
signed egress record it owes, and holds every remote until then. See
[Remotes](#remotes) and the [Remote Send Flow](#remote-send-flow).

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
- An entry's scope: where it is declared, on the change and in the bytes,
  what the log records of it, and the rule that it only rises
- Remotes: copies of a repository sent to a second place, the census that
  precedes one, and the effective custody every copy adds to
- Precondition semantics for writes (digest match, refusal on mismatch)
- Proposals: staging a change for a person to decide, the decision, and the
  separation of duties it records
- Who a change was for: the attribution a `ContentChange` carries, and which
  party asserts each part of it
- The change log: what each entry covers, who signs it, and what a verifier
  checks without this service
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
- Repositories outside any tenant — authored, versioned, validated and offered
  where no tenant has declared them. This service holds none of them, and what
  one holds reaches a tenant only as
  [Repositories Outside a Tenant](#repositories-outside-a-tenant) says

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
| POST | /v1/content/repositories/{repository}/remotes | DeclareRemote | yes | Declare a remote of a repository. Without `if_match`, returns the census of what would leave and declares nothing |
| GET | /v1/content/repositories/{repository}/remotes | Remotes | yes | A repository's remotes, retired ones included, with state and ceiling |
| DELETE | /v1/content/repositories/{repository}/remotes/{remote} | RetireRemote | yes | Stop sending to a remote. Deletes nothing at its destination |
| POST | /v1/content/reconcile | Reconcile | yes | Detect out-of-band change (shared custody only) |
| POST | /v1/content/proposals | Propose | yes | Stage a change to one entry for a person to decide. Writes no entry |
| GET | /v1/content/proposals | Proposals | yes | List proposals in scope, cursor-paginated |
| GET | /v1/content/proposals/{id} | Proposal | yes | Read one proposal, with the bytes it proposes, under the entry's own read check |
| POST | /v1/content/proposals/{id}/decision | Decide | yes | Apply or reject a proposal. Applying writes the entry |
| GET | /v1/content/repositories/{repository}/log | Log | yes | A repository's change log, its lines exactly as stored, from a sequence number. Whole or refused, never filtered |
| GET | /v1/content/repositories/{repository}/log/head | LogHead | yes | The log's id, its tip, its latest checkpoint and the key entry that introduced its key, and how many entries are unsealed. Names no path |
| POST | /v1/content/repositories/{repository}/log/checkpoint | SealLog | yes | Seal the log now, where the tip has moved since the last checkpoint, and return its head |
| GET | /livez | Livez | no | Liveness, for the supervisor that restarts the service. Served with or without an orchestrator |
| GET | /readyz | Readyz | no | Readiness, for the supervisor waiting on its start. Served with or without an orchestrator |

**An entry's bytes travel as base64.** Wherever a JSON body carries an entry's
bytes — the response of `GET /v1/content/entry`, the request of
`PUT /v1/content/entry`, and the `bytes` of a proposal — they are one string
of standard base64 (RFC 4648 §4, with padding). They are never carried as
text. An entry is any bytes, and a JSON parser may replace bytes that are not
valid UTF-8 before the service sees them, so a digest computed after it would
be the digest of bytes nobody sent. A string that is not valid base64 is
refused with `INVALID_REQUEST` ([`protocol/spec`](../protocol/spec.md)).

**A write and a removal carry their request as a JSON body.**
`PUT /v1/content/entry` carries an `EntryWrite`, and `DELETE /v1/content/entry`
carries an `EntryRemoval`. A person's `statement` sits in that body in both. A
removal's request is a body, and not a query string or a header, because a
`ChangeStatement` carries a whole attestation, several kilobytes, and neither
has room for it. Anything between a client and this service passes a DELETE
body through unchanged.

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

    - path: /v1/content/repositories/{repository}/remotes
      methods: [GET, POST]
      description: GET lists a repository's remotes, retired ones included.
        POST declares one. Without if_match it returns the census of what
        would leave and declares nothing; with it, it reserves the remote,
        creates its credential, demonstrates the destination and confirms
      served_by: content-service

    - path: /v1/content/repositories/{repository}/remotes/{remote}
      methods: [DELETE]
      description: Retire a remote. Nothing more is sent to it, its
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

    - path: /v1/content/repositories/{repository}/log
      methods: [GET]
      description: A repository's change log, its lines byte for byte as
        stored, from a sequence number. Refused whole unless the caller may
        read the highest scope the log records, and never filtered
      served_by: content-service

    - path: /v1/content/repositories/{repository}/log/head
      methods: [GET]
      description: The log id, the tip, the latest checkpoint with the key
        entry that introduced its key, and the count of unsealed entries.
        Names no path
      served_by: content-service

    - path: /v1/content/repositories/{repository}/log/checkpoint
      methods: [POST]
      description: Issue a checkpoint now, where the tip has moved since the
        last one, and return the log's head
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
      signature: (repository, path, bytes, if_match, scope, statement) → (ContentIdentity, ContentChange)
      description: Replace bytes when the precondition holds; refuse otherwise.
        Called for a person, never for an agent — content:write is person only
      called_by: [gateway]

    - name: DeleteEntry
      signature: (repository, path, if_match, statement) → ContentChange
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

    - name: DeclareRemote
      signature: (repository, RemoteDeclaration) → (ContentRemote, RemoteCensus)
      description: Declare a remote. Returns the census and declares nothing
        when attempted unseen, and reports a declaration that did not finish
        rather than rolling it back. Called for a person, never for an agent —
        content:replicate and content:connect are person only
      called_by: [gateway]

    - name: ListRemotes
      signature: repository → [ContentRemote]
      description: A repository's remotes, retired ones included
      called_by: [gateway, agents, admin]

    - name: RetireRemote
      signature: (repository, remote) → ContentRemote
      description: Stop sending to a remote and destroy its credential.
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

    - name: ReadLog
      signature: (repository, LogQuery) → LogPage
      description: The change log's stored lines from seq from, each exactly
        as stored
      called_by: [gateway, agents, admin]

    - name: ReadLogHead
      signature: repository → LogHead
      description: The log id, tip, latest checkpoint and unsealed count
      called_by: [gateway, agents, admin]

    - name: SealLog
      signature: repository → LogHead
      description: Issue a checkpoint where the tip has moved, then report the
        head. Refused with CONTENT_SEALING_PAUSED while no log key can sign
      called_by: [gateway, agents, admin]

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
        attestations or a remote's were re-verified weaker than before, a
        remote was confirmed with a lower ceiling, or its backend found a
        copy nobody declared — naming the content now above the ceiling

    - topic: content.remote_declared
      direction: publish
      description: A remote was confirmed, with who holds its destination,
        its ceiling and the repository's ceiling as it now stands

    - topic: content.remote_state
      direction: publish
      description: A remote's state changed — behind, diverged, unreachable,
        current — naming a held version's path and why it is held. Never
        carries bytes

    - topic: content.remote_retired
      direction: publish
      description: A remote was retired, naming who retired it. Its
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

**Each code's HTTP status follows its Category**, and a code is returned with
that status wherever this service refuses: `validation` 400, `auth` 401,
`policy` 403, `enforcement` 403, `conflict` 409, `integrity` 409, `io` 503 and
`partial` 207. A code whose behaviour is not a refusal, such as
`CONTENT_CUSTODY_UNDECLARED`, is reported and never returned as an error
status. The Category column classes the fault. It is not
`ErrorResponse.category`: there, an `io` or `partial` code is `transient` and
`retryable`, and every other code is `permanent` and not `retryable`. A code
another blueprint registers, such as `SCOPE_INVALID_LEVEL`, `FORBIDDEN`,
`PASS_REQUIRED` or `PASS_AUDIENCE_MISMATCH`, keeps the status that blueprint
gives it ([`protocol/types`](../protocol/types.md#errorresponse)).

A backend's own blueprint may register codes under this service's `CONTENT_`
prefix, for a fault only that backend can meet, as
[`patterns/content-git`](../patterns/content-git.md#error-handling) registers
`CONTENT_PLACEMENT_PARTIAL` and `CONTENT_LINE_UNSETTLED`. This service returns
each with the status its Category gives under the rule above, and no backend
may register a code the table below registers.

Four codes take another status than their Category's. `CONTENT_STATEMENT_INVALID`
is 400: the token was accepted and the statement it carried was not, so a
client told to authenticate again would send the same statement.
`CONTENT_REPOSITORY_UNKNOWN`, `CONTENT_PROPOSAL_UNKNOWN` and
`CONTENT_REMOTE_UNKNOWN` are 404, because the request was well formed and
names nothing the caller may see.

`CONTENT_STATEMENT_INVALID` is this surface's wire form of
[`patterns/principal-identity`](../patterns/principal-identity.md#error-handling)'s
`credential_purpose_mismatch` and `algorithm_not_permitted` where a change
statement fails for either reason, as `architecture/admin`'s Error Handling
gives wire forms for the operator routes. The pattern holds the rule, and one
code here is enough, because a client does the same thing for both.

| Code | Category | When | Behaviour |
|---|---|---|---|
| `CONTENT_PRECONDITION_FAILED` | conflict | `if_match` does not equal the identity of what it names — an entry's stored digest on a write or a proposal, a placement's census digest on an adoption, a remote census's digest, over what would leave and where it would go, on a remote declaration, a proposal's `before` on a decision to apply it. The empty string where an entry exists, on a write, a proposal to create, or a decision to apply one | Refuse. Return both digests. Never merge, never overwrite, never adopt. On a decision to apply, record the proposal `stale` and write nothing |
| `CONTENT_IF_MATCH_REQUIRED` | validation | A write, a removal or a proposal arrived with no `if_match`. The empty string is a precondition, not its absence | Refuse. A write with no precondition is a blind overwrite, and a proposal with none cannot be told stale |
| `CONTENT_CUSTODY_CEILING_EXCEEDED` | policy | Declared scope exceeds the repository ceiling, or something a remote would receive exceeds that remote's ceiling, or a records repository's derived ceiling is below `restricted`, or a declaration's `scope_floor` is above the ceiling derived at declaration. See [`scope_floor`](#scope_floor-covers-what-declares-nothing) | Refuse, naming required and actual, and on a remote each path above it. Never downgrade the scope |
| `CONTENT_RECORDS_REPOSITORY_REQUIRED` | policy | A write or a proposal whose bytes carry the label `pii`, into a repository that is not a records repository. See [Where an entry labelled `pii` is kept](#where-an-entry-labelled-pii-is-kept) | Refuse, naming the path and the `scope_path`'s records repository where there is one. Nothing is written, and the label is never dropped to fit |
| `CONTENT_SCOPE_LOWERED` | policy | A write or a proposal declares a scope below its path's recorded scope, below the scope its own bytes declare, or below the `maps_to` of a label its bytes carry that the tenant registers, or declares none where a recorded scope, the bytes or such a label give one; or its bytes declare a scope below the path's recorded scope. A removal never ends a recorded scope, so this also refuses a path created again below the scope last recorded for it. An adoption whose `scope_floor` is below the census's `highest_scope` is refused with it too. See [An Entry's Scope](#an-entrys-scope) and [`scope_floor`](#scope_floor-covers-what-declares-nothing) | Refuse, naming both levels and where each was declared. Never record the lower scope, and never raise the declared one to fit |
| `SCOPE_INVALID_LEVEL` | validation | A write or a proposal declares a scope, on the change or under `scope:` or `classification:` in its bytes, that is not a `ScopeLevel`. The code is [`patterns/scope`](../patterns/scope.md#scope-related-errors)'s | Refuse, naming where the value was found and the value |
| `CONTENT_CUSTODY_UNDECLARED` | policy | Repository has no declared custody | Treat as `opaque`, apply the `internal` ceiling, and record the degradation |
| `CONTENT_PATH_REFUSED` | validation | Traversal segment or escaping symlink — including a placement locator that is absolute, carries a scheme or an authority, or climbs out of its backend's root | Refuse the request as written. Do not normalise and proceed |
| `CONTENT_RESERVED_PATH` | policy | A segment of the path, or of a placement's locator, is a reserved name — `.weblisk` or `.git` — as any filesystem could resolve it, or the backend's blueprint reserves the path — including a path in anything a remote would receive. See [Reserved Paths](#reserved-paths) | Refuse, for every operation including list, stat, propose, declare and declaring a remote. Installation state and control state are never content, and never leave: a version holding one is never sent to a remote already declared, and holds it ([Remote Send Flow](#remote-send-flow)) |
| `CONTENT_UNREADABLE` | io | Bytes cannot be read | Identity is `unknown`, never `current` and never `stale` |
| `CONTENT_REPOSITORY_UNKNOWN` | validation | No repository of that id in the caller's scope | Refuse without disclosing whether it exists elsewhere |
| `CONTENT_DISPOSITION_REQUIRED` | validation | A declaration arrived without a disposition | Refuse. A declaration that does not say whether it expects bytes is a blind adoption |
| `CONTENT_REPOSITORY_EXISTS` | conflict | The id is already declared at that `scope_path`, or is reserved there by an unfinished establish whose arguments differ from this request's; or the declaration names itself a records repository and the `scope_path` has one | Refuse, naming the declared repository's placement. Never re-declare in place. An identical retry against an unfinished establish is a resumption, not this |
| `CONTENT_ADOPTION_UNSEEN` | conflict | `disposition: adopt` with no `if_match` | Refuse and return the `ContentAdoption` census. Nothing is declared. The caller re-submits with the census digest |
| `CONTENT_NOT_EMPTY` | conflict | `disposition: establish` and the placement already holds entries, including on a resumed establish whose store has since been written to; or a remote's destination holds something this service would not send | Refuse. Establishing over bytes somebody else wrote is adoption under the wrong word, and sending over them would overwrite them |
| `CONTENT_BACKEND_UNKNOWN` | validation | The placement names a backend this service does not hold for that `scope_path` | Refuse without disclosing whether the name exists under another scope |
| `CONTENT_ESTABLISH_UNSUPPORTED` | policy | `disposition: establish` against a backend that cannot bring a store into existence, or cannot represent an empty one without an entry in it | Refuse. Never write a placeholder to make the store representable. `adopt` against the same backend is unaffected |
| `CONTENT_ESTABLISH_INCOMPLETE` | partial | The declaration was reserved and the create or the custody demonstration did not finish; or a remote was reserved and its credential, or the demonstration of its destination, did not finish | Report what completed, carrying the `ContentRepository` and its `RepositoryEstablishment`, or the `ContentRemote` with its `RemoteEstablishment` and credential. Roll nothing back, claim no success, and do not report that nothing happened |
| `CONTENT_PRECONDITION_NOT_APPLICABLE` | validation | `if_match` does not fit the act: any `if_match` with `disposition: establish`; the empty string on a removal, or on a proposal to modify or remove; a digest on a proposal to create | Refuse. A precondition that contradicts the act, or that nothing can evaluate, must not be accepted as though it held |
| `CONTENT_PLACEMENT_DECLARED` | conflict | The placement is equal to, inside, or contains an already-declared repository; or a remote's destination is equal to, inside or contains a declared repository's placement or another remote's destination | Refuse. Two ceilings over one set of bytes means the lower one is unenforceable, and a remote sent into a store would make a copy a source |
| `CONTENT_PROPOSAL_UNKNOWN` | validation | No proposal of that id in the caller's scope | Refuse without disclosing whether it exists elsewhere |
| `CONTENT_PROPOSAL_DECIDED` | conflict | A decision arrived for a proposal that is no longer `open`, including the second of two decisions that raced | Refuse, returning the proposal as recorded. A proposal leaves `open` once |
| `CONTENT_SEPARATION_REQUIRED` | policy | A decision to apply was made by the identity the proposal names as its `actor` or its `on_behalf_of`, and the change's scope is above the repository's `self_decision_ceiling`, the change has no scope, or the repository declares no ceiling. Or a repository declaration whose `self_decision_ceiling` is `critical`. See [Separation of duties](#separation-of-duties) | Refuse, naming the scope, or that there is none, and the ceiling. Nothing is recorded and the proposal stays `open` |
| `CONTENT_IDENTITY_REQUIRED` | auth | A write, removal, proposal, decision, remote declaration or retirement arrived on a token that carries no `identity_id` | Refuse. Never record a name, an address or a token's `sub` in its place |
| `CONTENT_STATEMENT_INVALID` | auth | A write, removal or decision carried a `ChangeStatement` that does not verify: the attestation's `purpose` is not `sign-records`, its `identity_id` is not the token's, its identity key is not the operator's current one, its signature fails, its credential key is not ML-DSA-65, or its `not_after` has passed or is more than 90 days ahead; its credential key is not one of the token's `record_keys`, or is the credential the token's `cid` names; `signed_at` is more than 300 seconds from the service's clock; or the signature does not verify over the statement rebuilt from the change. See [The change statement](#the-change-statement) | Refuse, naming the check that failed. Nothing is written and a proposal stays `open`. The change is never recorded unsigned instead. Log as a security event |
| `CONTENT_WRITE_UNCONFIRMED` | io | The digest of the bytes read back after a write is not the digest of the decoded bytes submitted | Refuse. The reservation is settled as one whose path holds neither `before` nor the reserved `after`: an `observe` entry under shared custody, an integrity anomaly under exclusive custody. No `change` entry records the write, because a statement over the submitted bytes could not be checked against other ones. See [Write Flow](#write-flow) |
| `CONTENT_LOG_NOT_BEGUN` | conflict | A log route named a repository that is `establishing`. Its log begins with the `declare` entry when it is recorded `declared` | Refuse. The caller learns the repository's state from `GET /v1/content/repositories` |
| `CONTENT_SEALING_PAUSED` | io | A checkpoint was asked for and no log key can sign one: none is live and the long-lived key cannot introduce another | Refuse, carrying the `LogHead`, whose `unsealed` counts what waits. Nothing is appended. The request may be repeated once sealing resumes |
| `CONTENT_LOG_BROKEN` | integrity | The repository's change log failed this service's check from its latest checkpoint, because a line breaks the chain or cannot be read, and the request would append to it: a write, a removal, a decision to apply, a reconcile or a checkpoint. See [A log that does not verify](#a-log-that-does-not-verify) | Refuse, naming the `seq` where the check failed. Nothing is written to the store and nothing is appended. Reads, the log's included, are still served |
| `CONTENT_REMOTE_UNSEEN` | conflict | A remote declaration with no `if_match` | Refuse and return the `RemoteCensus`. Nothing is recorded and nothing is sent. The caller re-submits with the census digest |
| `CONTENT_SCOPE_UNDECLARED` | policy | A remote declaration where a version that would leave is unclassified, and the declaration carries no `history_scope`. See [What would leave](#what-would-leave). Or an adoption whose census reports `keeps_history`, and the declaration carries no `scope_floor`. See [`scope_floor` covers what declares nothing](#scope_floor-covers-what-declares-nothing) | Refuse, naming how many versions are unclassified, or, on an adoption, returning the census, whose `highest_scope` is the least floor it may carry. Nothing is recorded and nothing is sent. No version is assumed to be at any level |
| `CONTENT_REMOTE_EXISTS` | conflict | The remote id is taken in that repository, by a remote that is not `establishing` or whose recorded arguments differ from this request's | Refuse, naming the recorded destination. An identical retry against an `establishing` remote is a resumption, not this |
| `CONTENT_REMOTE_UNKNOWN` | validation | No remote of that id in that repository | Refuse |
| `CONTENT_REMOTE_UNSUPPORTED` | policy | The destination's backend cannot receive a remote, or cannot receive one of the repository's backend | Refuse. Nothing is recorded |
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
   A declaration carrying `self_decision_ceiling` or `scope_floor` MUST come
   from a caller holding `content:decide` as well as `content:declare`
   (`FORBIDDEN` otherwise), both named by the `cap` of a pass
   ([Who may move an entry](#who-may-move-an-entry)).
   A declaration naming itself a records repository at a `scope_path` that
   has one → `CONTENT_REPOSITORY_EXISTS`. A `scope_floor` that is not a
   `ScopeLevel` → `SCOPE_INVALID_LEVEL`. A `self_decision_ceiling` of
   `critical` → `CONTENT_SEPARATION_REQUIRED`, because separation at
   `critical` is not configurable
   ([Separation of duties](#separation-of-duties))
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
   `CONTENT_PRECONDITION_FAILED` and returns both digests. Where the census
   reports `keeps_history` and the declaration carries no `scope_floor`, it
   refuses with `CONTENT_SCOPE_UNDECLARED`, returns the census, and declares
   nothing ([`scope_floor` covers what declares nothing](#scope_floor-covers-what-declares-nothing)).
   `adopt` never creates
7. Each claimed attestation is demonstrated — on `establish`, against the store
   that now exists. An undemonstrated claim becomes `false`; a declaration with
   no custody is recorded `opaque` and the degradation is recorded, per
   `CONTENT_CUSTODY_UNDECLARED`
8. The ceiling is derived from what was demonstrated. It is never taken from the
   request. A records repository whose ceiling is below `restricted`, or a
   `scope_floor` above the ceiling → `CONTENT_CUSTODY_CEILING_EXCEEDED`; on
   `adopt`, a `scope_floor` below the census's `highest_scope` →
   `CONTENT_SCOPE_LOWERED`. The repository stays `establishing` on
   `establish`, or is not declared on `adopt`
9. The repository is recorded `state: declared`. On adoption, every entry the
   census found is recorded with provenance `unknown` — the service did not
   write them and observed no change, so it can establish nothing about them —
   and with the scope its bytes declare, where they declare one this service
   can read ([An Entry's Scope](#an-entrys-scope)).
   The repository's change log begins, with its `declare` entry (see
   [The Change Log](#the-change-log))
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
5. Under shared custody, the digest is compared against the path's recorded
   digest ([What an entry covers](#what-an-entry-covers)); a difference
   produces a `ContentObservation` with provenance `external` and the scope
   the bytes read are at ([A change this service did not make](#a-change-this-service-did-not-make)),
   appended to the change log as an `observe` entry, and does **not** fail
   the read
6. Bytes and `ContentIdentity` are returned; the read leaves the bytes unchanged

### Write Flow
1. Caller submits an `EntryWrite`: bytes, a declared scope where one applies
   ([Where a scope is declared](#where-a-scope-is-declared)), and `if_match` —
   the identity it believes it is replacing, or the empty string for an entry
   it believes does not exist yet — and, where the person signs, a
   `ChangeStatement` as `statement`. A removal submits an `EntryRemoval`
   instead, and runs the same steps with no bytes and no scope or ceiling
   check, the storage proxy intercepting with operation `delete`
2. Path Resolver confines the path as above
3. Scope and ceiling check. First the declared scope against the rules of
   [A scope only rises](#a-scope-only-rises): none, or one below the path's
   recorded scope or below the scope the bytes declare, where either exists;
   one below the `maps_to` of a registered label the bytes carry; or bytes
   whose frontmatter names a level below the recorded one → refuse with
   `CONTENT_SCOPE_LOWERED`; a scope that is not a `ScopeLevel` → refuse with
   `SCOPE_INVALID_LEVEL`. Nothing is raised to fit. Then the declared scope
   against the repository's derived ceiling; a change that declares none is
   checked at `patterns/scope`'s `default_level`, the level it is decided at in
   place. Exceeded → refuse, publish `content.ceiling_exceeded`. Bytes that
   carry `pii`, into a repository that is not a records repository → refuse
   with `CONTENT_RECORDS_REPOSITORY_REQUIRED`
4. The token is checked ([Who may move an entry](#who-may-move-an-entry)).
   Only a pass addressed to this service carries a person's request. Any
   other token that reaches this step, a registered component's or a
   channel's, is refused with `FORBIDDEN` whatever its `cap`, and so is a
   pass whose `cap` does not name `content:write`. The pass's `identity_key`
   is what step 6 checks a statement against. Then the enforcement storage proxy
   intercepts with operation `create` when `if_match` is the empty string,
   and `modify` otherwise
5. Precondition Gate reads the current digest and compares it to `if_match`.
   Mismatch → refuse with both digests. No merge is attempted
6. A statement, where one was sent, is verified against the change this write
   would record ([The change statement](#the-change-statement)). One that does
   not verify refuses the write with `CONTENT_STATEMENT_INVALID`
7. The change is reserved
   ([A change is reserved before it is made](#a-change-is-reserved-before-it-is-made))
8. Bytes are written durably; the new digest is computed from what was written,
   not from what was submitted. Where it differs from the digest of the decoded
   bytes, the write fails with `CONTENT_WRITE_UNCONFIRMED` and the reservation
   is settled as one whose path holds neither `before` nor the reserved
   `after`
9. A `ContentChange` is appended to the repository's change log as a `change`
   entry, with provenance `authored`, the declared scope and its
   `scope_basis` where the change declared one, the token's
   `identity_id` for `actor`, the correlation id of the enforcement decision,
   and the statement where one verified. The reservation is released in the
   same write
10. `content.changed` is published

### Proposal Flow
1. Caller submits a `ProposalRequest`: a repository, a `ProposedChange` naming
   the path and the action, `if_match`, and — for `create` and `modify` — the
   proposed `bytes` and, where one applies, their declared scope, with
   `on_behalf_of`, `agent`, `run` and a reason where they apply. An `action`
   other than `create`, `modify` or `delete`, `bytes` missing on a `create` or
   `modify`, or `bytes` or `scope` present on a `delete`, is refused with
   `INVALID_REQUEST`
   ([`protocol/spec`](../protocol/spec.md)). `bytes` longer than
   `max_entry_bytes` are refused as a write of that length would be
2. Path Resolver confines the path as for a write; traversal, escaping symlinks
   and reserved paths are refused
3. Scope and ceiling check, as Write Flow step 3, over the proposed bytes and
   their declared scope. A proposal to delete has neither
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
1. Caller submits a `DecisionRequest` for one proposal: `apply` or `reject`,
   and, where the person signs an `apply`, a `ChangeStatement`
2. The proposal must be in the caller's scope (`CONTENT_PROPOSAL_UNKNOWN`) and
   `open` (`CONTENT_PROPOSAL_DECIDED`). The token is checked as Write Flow
   step 4 says, and must be a pass whose `cap` names `content:decide`. When
   step 5 runs the Write Flow for an `apply`, its step 4 checks the same pass,
   and the capability it requires there is `content:decide`, never
   `content:write`: a decider applies a proposal without holding
   `content:write`, and is refused with `FORBIDDEN` only when the pass's `cap`
   does not name `content:decide`
3. `reject` → the decision is recorded, the proposal becomes `rejected`, and
   `content.proposal_decided` is published. Nothing else happens
4. `apply` → separation is checked: a decider whose token's `identity_id` equals
   the proposal's `actor` or its `on_behalf_of` is refused with
   `CONTENT_SEPARATION_REQUIRED` unless the change has a scope — the
   proposal's, or on a `delete` the recorded scope of the path it removes —
   and that scope is at or below the repository's `self_decision_ceiling`. A
   change with no scope is never self-decided
   ([Separation of duties](#separation-of-duties))
5. The write runs for the decider, with the proposal's `before` as `if_match`,
   or the empty string when it has none. For a `create` or `modify`, Write
   Flow steps 2 to 8 run with the proposal's path, bytes and scope, and with
   the decider's statement where one was sent, verified against the proposal.
   For a `delete`, the same steps run as a removal: no bytes and no scope or
   ceiling check, the enforcement storage proxy intercepting with operation
   `delete`, and the entry is removed and its identity retired
6. `before` no longer matches → refuse with `CONTENT_PRECONDITION_FAILED` and
   both digests, record the decision with the proposal `stale`, write nothing,
   and publish `content.proposal_decided`. Any other refusal leaves the
   proposal `open` and records nothing on it
7. A `ContentChange` is appended to the repository's change log as a `change`
   entry, with provenance `authored`: `scope`, `actor` and `on_behalf_of` from
   the proposal, `scope_basis` as step 5 found it, the decider's
   `identity_id` in `approved_by`, the proposal's
   id in `proposal`, the `separation` step 4 found, the correlation id of the
   decider's enforcement decision, and the decider's statement where one
   verified. The proposal becomes `applied` in the same record write, and the
   reservation is released — none of them is durable without the others
8. `content.changed` and `content.proposal_decided` are published. Neither
   carries the proposed bytes

### Reconciliation Flow (shared custody only)
1. Reconcile is invoked for a repository, on a schedule or on demand
2. For each entry with a recorded digest, the current digest is computed
3. Unchanged entries produce nothing
4. A changed entry produces a `ContentObservation`: both digests, provenance
   `external`, the scope the new bytes are at
   ([A change this service did not make](#a-change-this-service-did-not-make)),
   and the writing identity when `attributable_writes` is attested
5. An unreadable entry produces an observation with state `unknown` — never
   `stale`, never `current`, and never a deletion
6. Observations are recorded and surfaced. One of state `changed` or `removed`
   is appended to the repository's change log as an `observe` entry. **No
   observation from this flow is an integrity anomaly**; that classification
   belongs to exclusive custody

### Custody Re-verification Flow
1. On declaration and on a schedule, each attestation property is tested — the
   store's, and each remote's that is not retired, with its `anonymous_read`
2. A property that cannot be demonstrated becomes `false`
3. The backend reports any copy of the store it can see that no remote
   declares, and each one not yet in `reported_copies` is added to it
4. The ceiling is recomputed from every place the bytes live (see
   [Effective custody](#effective-custody))
5. If the ceiling dropped, `content.custody_degraded` is published naming the
   content now sitting above it. Existing content is not moved and not
   reclassified — it is reported

### Remote Declaration Flow
1. Caller submits a `RemoteDeclaration` for a repository: an id, a
   `destination`, a claimed custody, claimed attestations, a `history_scope`
   where versions that would leave are unclassified, and `if_match`
2. Enforcement storage proxy intercepts with operation `create` and the
   repository's `scope_path` as the resource scope
3. The token is checked as Write Flow step 4 says. The caller must hold
   `content:replicate` and `content:connect`, both named by the `cap` of a
   pass, which carries only what the person's role carried at the exchange
   (see [Who may declare a remote](#who-may-declare-a-remote) and
   [Who may move an entry](#who-may-move-an-entry))
4. The destination is resolved as a placement is: its backend must be one this
   service holds for that `scope_path` (`CONTENT_BACKEND_UNKNOWN`) and able to
   receive a remote of the repository's backend
   (`CONTENT_REMOTE_UNSUPPORTED`), and its locator is confined to that
   backend's root (`CONTENT_PATH_REFUSED`, `CONTENT_RESERVED_PATH`). It must not
   be equal to, inside or containing a declared repository's placement or
   another remote's destination (`CONTENT_PLACEMENT_DECLARED`)
5. The id must be free in that repository (`CONTENT_REMOTE_EXISTS`). A remote
   in `establishing` whose recorded id, destination, custody, attestations and
   `history_scope` equal this request's is resumed at step 9
6. The service computes a `RemoteCensus` of what would leave and where it
   would go, for this request's destination and claims. With no `if_match`, it
   returns the census, refuses with `CONTENT_REMOTE_UNSEEN`, and records
   nothing
7. Checked in order: an `if_match` that does not equal the census digest just
   computed → `CONTENT_PRECONDITION_FAILED`, which is also the answer when the
   destination, who holds it, or the claims differ from those of the census
   the caller saw; a reserved path in anything that would leave →
   `CONTENT_RESERVED_PATH`; an unclassified version that would leave, with no
   `history_scope` → `CONTENT_SCOPE_UNDECLARED`; anything that would leave
   above the census's prospective remote ceiling →
   `CONTENT_CUSTODY_CEILING_EXCEEDED`
8. The remote is **reserved** — recorded durably with `state: establishing`,
   sending nothing and counting toward nothing
9. The credential is created and held, unless the reservation already has one
10. The destination is demonstrated with that credential: it holds nothing
    this service would not send (`CONTENT_NOT_EMPTY`); each claimed custody
    property and attestation; and `anonymous_read`. The remote's ceiling is
    derived from what was demonstrated. Anything that would leave above it →
    `CONTENT_CUSTODY_CEILING_EXCEEDED`, and the remote stays `establishing`
11. The remote is **confirmed**. From here on it counts toward the
    repository's effective custody and ceiling, whether or not anything ever
    reaches its destination (see [Effective custody](#effective-custody)).
    Both are recomputed, the remote becomes `behind`, or `current` when there
    is nothing to send, and `content.remote_declared` is published. Sending
    begins once a send can leave its egress record
    ([Remote Send Flow](#remote-send-flow), step 4)
12. Should step 9 or 10 not finish, nothing is sent and nothing is rolled back:
    the caller is answered with `CONTENT_ESTABLISH_INCOMPLETE` carrying the
    remote, its `RemoteEstablishment` and its credential

### Remote Send Flow
1. After each version is recorded, and every `remote_retry_interval`, each
   remote that is neither `establishing` nor `retired` is sent what it lacks,
   oldest first
2. Before sending, the service checks that the destination holds only what the
   service sent it. If it holds anything else, the remote becomes
   `diverged`, what was found is recorded, and nothing is sent
3. Every version that would be sent is checked, oldest first, before any of
   it is sent. A version may not be sent when it holds a reserved path
   anywhere, not only among the paths it changed (`reserved-path`); when it is
   unclassified and the remote's census did not count it (`unclassified`); or
   when its scope is above the remote's ceiling (`above-ceiling`). The first
   such version is **held**: the remote is `behind`, `held_path` names the
   path and `held_reason` says which of the three it is, and neither that
   version nor anything recorded after it is sent. What was recorded before it
   is sent, as step 4 allows
4. **Nothing is sent before its egress record can be.** A send owes a signed
   record of what left, which this service cannot yet make
   ([The Change Log](#the-change-log), the gap on what a send leaves). Until it can,
   what step 3 would let leave is not sent: the remote is `behind` with
   `held_reason` `egress-unrecorded` and no `held_path`, unless step 3 held a
   version first, and steps 5 and 6 send nothing. Steps 2 and 3 still run,
   because they read and send nothing, so a held version and a changed
   destination are reported as before
5. A destination that cannot be reached, or that refuses the credential, makes
   the remote `unreachable` until the next attempt succeeds
6. What was sent is recorded with `checked_at`. With nothing left to send, the
   remote is `current`
7. Each change of state publishes `content.remote_state`

---

## Registration and Standalone Operation

The content service is a component in the mesh: it registers with the
orchestrator, claims the `content.*` namespace exclusively, verifies caller
tokens against the orchestrator's public key, and takes a person's request
only on a pass addressed to it
([Who may move an entry](#who-may-move-an-entry)).

Its manifest declares `protocol_version` `"1"` — the wire protocol version from
[`protocol/types`](../protocol/types.md), **not** the component's own semver.
Its routes are guarded by the `content:` family that document declares:

| Capability | Guards |
|---|---|
| `content:read` | `GET /v1/content`, `GET /v1/content/entry`, `GET /v1/content/stat`, `GET /v1/content/proposals`, `GET /v1/content/proposals/{id}`, `GET /v1/content/repositories/{repository}/log` |
| `content:write` | `PUT /v1/content/entry`, `DELETE /v1/content/entry`. Person only |
| `content:propose` | `POST /v1/content/proposals` |
| `content:decide` | `POST /v1/content/proposals/{id}/decision`; `POST /v1/content/repositories` carrying `scope_floor` or `self_decision_ceiling` — required **in addition to** `content:declare` ([Declaration Flow](#declaration-flow) step 4). Person only |
| `content:describe` | `GET /v1/content/repositories`, `GET /v1/content/repositories/{repository}/remotes`, `GET /v1/content/repositories/{repository}/log/head`, `POST /v1/content/repositories/{repository}/log/checkpoint` |
| `content:declare` | `POST /v1/content/repositories` |
| `content:establish` | `POST /v1/content/repositories` with `disposition: establish` — required **in addition to** `content:declare`, because creating a store is more than declaring one |
| `content:reconcile` | `POST /v1/content/reconcile` |
| `content:replicate` | `POST /v1/content/repositories/{repository}/remotes`, with `content:connect`; `DELETE /v1/content/repositories/{repository}/remotes/{remote}`. Person only |
| `content:connect` | `POST /v1/content/repositories/{repository}/remotes` — required **in addition to** `content:replicate`, because it gives the tenant a credential that reaches outside its store. Person only |
| `content:declassify` | No route yet: every lowering of a recorded scope is refused until one is specified, a person's own decision made with a step-up and a second person's only where the tenant declares one ([A scope only rises](#a-scope-only-rises)). Person only |

A capability name is `family:verb`. An invented name is refused at registration,
so these MUST be the names `protocol/types` declares and no others. *Person
only* is `protocol/types`' marking too, and what it does to a grant is
[Who may move an entry](#who-may-move-an-entry).

**Its manifest declares every route the table guards as a pass route**
([`protocol/types`](../protocol/types.md#passroute), `pass_routes`), because a
person may reach each on a pass, and this table is the one statement of what
each requires. Each route's entry names in `capabilities` every capability its
rows give it on every request — both `content:replicate` and `content:connect`
for declaring a remote — and in `body` each one its rows tie to the body.
For `POST /v1/content/repositories` that is:

```yaml
method: POST
path: /v1/content/repositories
capabilities: [content:declare]
body:
  - {field: disposition, equals: establish, capabilities: [content:establish]}
  - {field: scope_floor, capabilities: [content:decide]}
  - {field: self_decision_ceiling, capabilities: [content:decide]}
```

The admin gateway carries a person's request here only on a route this list
declares, and names on its pass exactly the capabilities the route's entry
calls for ([`architecture/admin`](admin.md#contracts),
`admin-gateway-authorization`). So a route the table guards that the list
leaves out is one no person can reach, and a capability the list leaves out
is refused here with `FORBIDDEN`: the two MUST agree, and when a row changes,
the list changes with it.

**Guarding a capability is not holding it.** The capabilities a manifest
declares become the `cap` of the token the orchestrator issues the service at
registration ([`protocol/spec`](../protocol/spec.md), `POST /v1/register`), so
they are what the service may do as a caller as well as what it serves. Its
manifest therefore declares every capability in the table except the five
that are person only: `content:write`, `content:decide`, `content:replicate`,
`content:connect` and `content:declassify`. It checks those on the requests it serves and never
holds them, and registration refuses a manifest that declares one, with
`CAPABILITY_PERSON_ONLY`. For the same reason no channel grant to this service
can carry one, because a grant is the intersection of what the requester
holds and what the target's manifest declares
([`architecture/orchestrator`](orchestrator.md)).

### Startup Sequence

The order is not free, because the key this service authenticates with arrives
in the registration response:

```
1. Load configuration and open storage
2. Load or generate the ML-DSA-65 key pair, and mint the log key it
   introduces into each change log (architecture/storage, The log key)
3. Check every change log from its latest checkpoint (A log that does not
   verify), then settle every reserved change in each log that passed, then
   reconcile the configured repositories against the registry — establish the
   ones not yet recorded, verify the custody attestations of the ones that
   are. Nothing here is fatal
4. Construct the authenticator WITHOUT an issuer key — it refuses every token
   until one arrives, which is the correct standalone behaviour
5. Register HTTP routes and start listening
6. Register with the orchestrator, if an orchestrator URL is configured
7. On the registration response, set the issuer public key on the authenticator
8. Start the reconcile, re-verify and checkpoint loops
9. Serve until signalled, then seal every change log whose tip has moved, where
   a log key can sign one
```

Step 3 is fatal in neither direction: a configured repository that could not be
established is left `establishing` or recorded as a `DeclinedRepository`, a
repository whose log fails its check is broken, the `checks` its lease carries
name each `not_ready`, and the service stays ready and serves everything else. A backend
that is briefly unreachable at boot MUST NOT stop a hub from starting, and MUST
NOT be reported as though the repository were fine.

Steps 4 to 7 are stated because the obvious order fails in a way that cannot
recover: a service that requires the orchestrator's public key in order to
construct its authenticator exits before step 6, so it can never obtain the key
it refused to start without.

**An orchestrator is not required in order to start.** Where no orchestrator URL
is configured:

- The service MUST start and MUST serve `GET /livez` and `GET /readyz`
  unauthenticated.
- Every protected endpoint MUST refuse with `401` and a structured
  `ErrorResponse`. It holds no issuer key, so it can verify no token, and a
  component that cannot verify a token MUST NOT accept one.
- `GET /readyz` MUST answer not ready, because the service cannot serve its
  purpose, and `GET /livez` MUST answer live, because nothing about it has
  failed. It logs that no orchestrator is configured, the one place it can
  name the cause, since `/readyz` says nothing but `ready`.
- It holds no lease, so no `checks` carry a repository left `establishing`,
  declined or broken, and its protected listing refuses every caller. It
  MUST log each such repository by `id` with its state when it records it,
  and the log is where a standalone operator reads them.

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
   repository whose effective custody is shared or opaque MUST carry that it
   is incomplete. This service sees the path through it and cannot see the
   path around it, or a reader of a copy. A partial record
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
   exposed place a copy of it lives. A remote therefore lowers what the
   repository may hold and never raises it, and bytes that have left are never
   counted as returned. A remote is only ever sent to. What comes back from a
   place this service does not control is somebody's write, never the truth.

9. **The log is the evidence, and the log is what is signed** — What a claim
   cites about a repository's history is its change log, signed with ML-DSA-65
   by this service and, where they choose, by the people who moved its
   entries. A backend's history, a commit and a signature on a commit are
   copies and conveniences, never evidence. A verifier needs the log, the
   public keys and ordinary tools, and nothing of this service's, in order to
   check the log: the service MUST NOT be needed to check its own record, as
   [`architecture/fabric`](fabric.md) Design Principle 9 says of the fabric.
   What the verifier checks is still, in part, this service's word. A
   checkpoint is the service's own statement that the log is what it recorded,
   and it is reported `uncountersigned`, because this contract defines no
   countersignature. A checkpoint somebody else kept does not change that
   verdict; it is what exposes a log rewritten after it
   ([`architecture/storage`](storage.md#verifying-a-sealed-log)). A person's
   statement is that person's; the order, the completeness and everything the
   service witnessed rest on its seal.

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
place. A repository with remotes lives in more than one, and its ceiling is
the lowest of them (see [Effective custody](#effective-custody)).

**A remote's ceiling** starts from the same table, applied to what was
demonstrated about its destination. The first of these rows that applies then
gives it:

| The remote's destination | Ceiling |
|---|---|
| It holds nothing but ciphertext under a key the tenant alone holds, as the blueprint that specifies its backend demonstrates | the ceiling of the repository's own store |
| Anyone can read it, or its refusal of a read with no credential (`anonymous_read`) was not demonstrated | `public` |
| Its custody is not `exclusive`, and it has not demonstrated `enumerable_principals` | `public` |
| It is **plain**: it holds the bytes as they are, so whoever can read it reads them | the lower of the table's and `confidential` |

A **sealed** remote, the first row, takes the ceiling of whoever holds its
key, and only the tenant does: whoever reads the destination reads
ciphertext, wherever it is and whoever else holds it. The second and third
rows give `public` because, away from the store, a place nobody can say who
reads cannot be told apart from a place anyone reads (Design Principle 2).
The fourth holds whoever holds the destination and whatever custody it
demonstrated. The `restricted` row of the table rests on approval and masking
remaining enforceable, and nobody reading a destination passes through
either. No backend this corpus specifies demonstrates the first row yet.

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

## An Entry's Scope

An entry's **scope** is how much protection its content deserves. It is a
`ScopeLevel`, one of the five levels
[`patterns/scope`](../patterns/scope.md#level-hierarchy) declares, and that
section's order is the only order they compare in. Custody says what a place
can deliver; the scope is what the ceiling of a place is compared with. A
scope is declared. It is never inferred from a path, a file name or what the
text appears to say.

### Where a scope is declared

An entry's scope is declared in three places, and nowhere else: on the
change, in the bytes, and, for every entry of a repository, by the
repository's `scope_floor`. A remote's `history_scope` classifies versions
for that remote alone ([What would leave](#what-would-leave)).

- **On the change.** A write, and a proposal to create or modify an entry,
  may carry `scope` (`EntryWrite`, `ProposalRequest`). It is a level a person
  chose for the bytes, or the level the bytes or the path's recorded scope
  already give. A client sends no other. It never fills one in by default, and
  a model never chooses one. A change that carries none declares nothing on
  the change.
- **In the bytes.** A document whose first line is `---` opens with a YAML
  frontmatter block, which ends at the next line that is `---`. A top-level
  `scope:` key in that block is the document's own declaration of its level.
  A top-level `scope_metadata:` beside it may carry `custom_labels`, as
  `patterns/scope`'s `ScopeDeclaration` does, and nothing else in
  `scope_metadata:` is read. How a label combines with the level beside it is
  [`patterns/scope`](../patterns/scope.md#a-label-and-its-level)'s. An entry
  in any other form declares nothing in its bytes.

**`classification:` is read, and never written.** In a document whose
frontmatter has `classification:` and no `scope:`, it declares that level
exactly as `scope:` would. A document carrying both declares the higher of
the two. Whatever writes a document writes `scope:`, and never
`classification:`. The alias exists so that nothing a person wrote goes
unread, and it is never written so that the second spelling does not spread.

**A registered label counts.** Wherever this contract reads the scope bytes
declare, bytes that carry a label the tenant registers declare at least
that label's `maps_to`, with or without a level beside it
([`patterns/scope`](../patterns/scope.md#a-label-and-its-level), rule 4). A
write is refused when the level its bytes name, or the scope
it declares, is below such a label's `maps_to`, or when neither names one
([A scope only rises](#a-scope-only-rises), rule 4), so this reading
decides the level only of bytes nothing checked: an adopted store's files
and history, an observed edit, a version made in the store directly. It is
what their `AdoptedEntry.scope`, `ContentObservation.scope`,
`ContentEntry.scope`, [What would leave](#what-would-leave) and the
census's `highest_scope` all read, so a version that carries `pii`
registered at `restricted` is never recorded, counted or sent below
`restricted`.

**Where the tenant registers a label.** Throughout this contract, a label the
tenant registers is one in this service's own `scope.custom_labels`
configuration ([Configuration](#configuration), in
[`patterns/scope`](../patterns/scope.md#label-registration)'s shape), and it
is the one registry for every repository the service holds, at every
`scope_path`. No domain's registry applies to a repository, and two
repositories never read a label differently.

- **On the repository.** A declaration may carry `scope_floor`: the least
  scope of every entry the repository holds, has held or will hold. It is the
  one statement that covers entries whose bytes declare no level, such as a
  programme's spec files, and history nobody classified. See [`scope_floor` covers what declares nothing](#scope_floor-covers-what-declares-nothing).

**The level in the bytes travels with them.** A copy of the file carries it, a
plain editor shows it, and a reader who holds only the file can see it. The
scope on a change is known only to this service and its log, and the floor
only to this service, its log and the repository's declaration.

### The recorded scope

The change log records a scope each time this service learns one for a path:

- on the `declare` entry, for each adopted entry whose bytes declare one
  (`AdoptedEntry.scope`);
- on each `change` that writes bytes (`ContentChange.scope`);
- on each `observe` whose bytes are at one (`ContentObservation.scope`).

A path's **recorded scope** is the last one the log recorded for it. Because a
scope only rises, it is also the highest. A removal does not end it, whether
this service made the removal or observed it: a path created again starts at
the last scope recorded for it. A version the log recorded keeps the scope
recorded with it, whatever happens to its path afterwards.

**The floor is recorded for every path.** A repository declared with a
`scope_floor` records it on its `declare` entry, and no path's recorded scope
is below it: a path the log records nothing for is at the floor, and one it
records a lower scope for is at the floor too. So in such a repository no
entry and no version is unclassified, and every rule below that reads a
recorded scope reads the floor with it.

An entry's scope, as `ContentEntry.scope` reports it, is the higher of its
path's recorded scope and the scope its bytes declare. An entry with neither
is **unclassified**. It is reported with no scope, never as `internal` or any
other level. The enforcement storage proxy still needs a resource scope to
decide an operation on it, and is given `patterns/scope`'s `default_level`.
That is a rule for deciding in place and never a declaration: an unclassified
entry stays unclassified for everything that would leave
([What would leave](#what-would-leave)).

> **Gap — a repository does not yet report what it holds.** The highest
> scope recorded for any of a repository's paths (`scope_held`), and how many
> of its entries are unclassified, are not yet fields of `ContentRepository`.
> Nor are an adoption's count of entries at each scope, and of those above the
> ceiling derived for it, fields of `ContentAdoption`. A remote's census
> counts what would leave unclassified or above that remote's ceiling
> (`RemoteCensus`), and nothing counts the rest. Until they are specified,
> what a repository holds is read entry by entry, from each entry's scope.

### A scope only rises

[`patterns/scope`](../patterns/scope.md#key-distinction-classification-vs-enforcement)
makes a classification permanent, and nothing in this contract lowers one.

1. A write or a proposal is refused with `CONTENT_SCOPE_LOWERED` when the
   scope it declares is below its path's recorded scope, or below the scope
   its own bytes declare. It is refused the same way when it declares no scope
   and either of those exists. The refusal names both levels, or the one level
   and that the change declared none.
2. It is refused the same way when the level its bytes' frontmatter names is
   below the path's recorded scope, whatever the change declares. A file that
   understates its own level misstates it wherever a copy of it goes.
3. A write or a proposal whose declared scope, on the change or in its bytes,
   is not a `ScopeLevel` is refused with `SCOPE_INVALID_LEVEL`, naming the
   value and where it was found. A level somebody wrote and nobody can read is
   not the absence of one.
4. A write or a proposal is refused with `CONTENT_SCOPE_LOWERED` when its
   bytes carry a label the tenant has registered, and the level its bytes
   name beside that label, or the scope it declares on the change, is below
   the label's `maps_to`, or neither names a level
   ([`patterns/scope`](../patterns/scope.md#a-label-and-its-level)). The
   refusal names the label and both levels.

No scope is raised on a person's behalf either. The service never records a
scope higher than the one the change declared: it refuses, and the person
declares the level. So the scope a change records is the highest declaration
that applies to it, a person's statement signs that scope
([The change statement](#the-change-statement)), and the ceiling is checked
against it (Write Flow, step 3). A change that declares none, on a path with
no recorded scope and bytes that declare none, records none. The version it
produces is unclassified.

**The log says where a change's scope came from.** `ContentChange.scope_basis`
is `bytes` when the bytes declare the recorded scope, `recorded` when the
path's recorded scope gives it and the bytes declare less, and `chosen` when
neither gives it, so that the change's own declaration is all that stands
behind it. `chosen` is asserted, unless the person's statement signs the
change: this service cannot tell a level a person chose from one a client
filled in, which is why a client never fills one in.

The rules run again when a proposal is applied, because the Write Flow runs
for the decider. A path whose recorded scope rose after the proposal was made
refuses the decision, and the proposal stays `open`. A removal declares no
scope and is checked against none. It does not lower the path's recorded
scope, so a write that creates the path again is checked against it.

**No route lowers a scope.** Lowering a path's recorded scope is
**declassification**, and this contract has no operation for it. Every
request that would lower one is refused by the rules above. A level set too
high stays on the path it was set on, and on every version recorded under it.

> **Gap — declassification has no route yet.** The act it needs is person
> only: one person's decision, made with a step-up
> ([`architecture/admin`](admin.md#contracts), `destructive-action-step-up`),
> recorded and signed with ML-DSA-65, and never lowering the scope the
> repository holds. A second person decides it too only where the tenant
> declares one, routing the decision to
> [`patterns/approval`](../patterns/approval.md)'s multi-party. Its
> capability, `content:declassify`, is in
> [`protocol/types`](../protocol/types.md#capability)' list, and the `admin`
> role carries it and no other role does
> ([`architecture/admin`](admin.md#operator-roles)). No route is specified for
> it, so none admits it, and until one is the refusal above is the whole
> answer.

**A copy is a new entry.** Bytes written to another path carry the level they
declare in themselves, and nothing else of the entry they were copied from. An
entry whose level was declared only on its changes arrives, copied, at
whatever the new change declares, or unclassified. Declaring the level in the
bytes is what makes it travel with them. This limit is stated here, as Design
Principle 5 requires.

### A change this service did not make

An observation reads the bytes it observed. Its `scope` is the higher of the
path's recorded scope and the scope those bytes declare. A lower level in the
bytes does not lower it: the recorded scope stands, and the observation is
recorded like any other, as Design Principle 4 requires. A value that is not a
`ScopeLevel`, in bytes this service did not write, declares nothing. An
observation with neither records no scope, and the version it observed is
unclassified. Nothing here raises an alarm or rewrites the file.

### Where an entry labelled `pii` is kept

`pii` is a label this service acts on, whether or not the tenant registers it
([`patterns/scope`](../patterns/scope.md#a-label-and-its-level)). An entry
whose bytes carry it is about a person, and it is kept in a **records
repository**: a repository whose declaration names it one (`records: true`).

- **One per scope.** A `scope_path` has at most one records repository. A
  second declaration naming itself one at the same `scope_path` is refused
  with `CONTENT_REPOSITORY_EXISTS`, naming the first.
- **Declared where it can hold `restricted`.** A declaration naming itself a
  records repository is refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`,
  naming both levels, when the ceiling derived at declaration is below
  `restricted`. Its ceiling can still fall later, as any repository's can,
  and every write above it is then refused by the ordinary check.
- **Nowhere else.** A write or a proposal whose bytes carry `pii`, into a
  repository that is not a records repository, is refused with
  `CONTENT_RECORDS_REPOSITORY_REQUIRED`, naming the path and, where the
  `scope_path` has one, its records repository. An adoption does not refuse
  such an entry, because an adoption records what a store already holds; every
  later write to it is refused.
- **The log keeps the label.** A change and an observation record the labels
  their bytes carry (`labels`), so where an entry about a person was kept can
  be read from the log. An entry carrying `pii` that a person puts in another
  repository out of band is observed like any other change, as Design
  Principle 4 requires, and its observation records the label.
- **Removing it is not erasing it.** A removal of a path whose last recorded
  labels include `pii` records `erasure_complete` on its `ContentChange`.
  It is `false` where the placement's backend keeps earlier versions of its
  entries, as the blueprint that specifies it says, or where any remote was
  sent a version holding the entry, because those bytes remain there; and
  `true` only where neither holds. The change log keeps the path and digests
  it recorded either way. A statement that a person's data was erased MUST
  NOT be made from a removal whose `erasure_complete` is `false`, for the
  reason a statement of who has accessed content carries `access_complete:
  false` wherever this service cannot see every path to it
  ([The Custody Model](#the-custody-model)).

`records` is declared through `POST /v1/content/repositories` and fixed there.
It is never configured: choosing where a tenant keeps records about people is
an act somebody performs and the audit trail names, not a line in a file read
at boot.

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
`RepositoryEstablishment`, and the `checks` the service's lease carries name it
`not_ready`. It is never
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
does not need `content:establish`. It needs `content:declare` alone only where
the declaration carries neither `scope_floor` nor `self_decision_ceiling`; one
carrying either also needs `content:decide`, on a pass
([Declaration Flow](#declaration-flow) step 4). An adoption whose census
reports `keeps_history` must carry a `scope_floor`, so adopting a store that
keeps history, every git store included, is a person's act
([`scope_floor` covers what declares nothing](#scope_floor-covers-what-declares-nothing)).

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

### `scope_floor` covers what declares nothing

A declaration may carry `scope_floor`, a `ScopeLevel`: the least scope of
every entry the repository holds, has held or will hold, recorded as every
path's least recorded scope ([The recorded scope](#the-recorded-scope)). It is
the repository's own statement of its level, made once by the person who
declares it, and it is what lets a repository whose entries cannot declare a
level in their bytes reach a remote at all. A programme's spec files are the
case that needs it: they are published with no `scope:` of their own, because
[`schemas/programme`](../schemas/programme.md#artifact_scope-is-never-spelled-scope)
gives the level of what a spec creates as `artifact_scope` and a `scope:` would
classify the spec file itself. Without a floor, every new spec version is
unclassified and holds every remote.

- **It only raises.** An entry's scope is the higher of what its path records,
  what its bytes declare and the floor. A write or a proposal declaring a
  scope below the floor is refused with `CONTENT_SCOPE_LOWERED`, as one below
  any recorded scope is ([A scope only rises](#a-scope-only-rises)).
- **Only a person declares it.** A floor classifies every entry and version
  that declares nothing, history included, so it is a person's judgement, as
  a scope on a change is, and a model never chooses one. A declaration
  carrying `scope_floor` requires `content:decide` as well as
  `content:declare`, and is checked with the orchestrator before it is
  recorded, as `self_decision_ceiling` is
  ([Who may move an entry](#who-may-move-an-entry)). `content:decide` is
  person only, so no service and no agent can declare a store public.
- **It is required where adopting takes in history.** A backend whose store
  keeps earlier versions of its entries that this service can read, such as
  one under version control, says so in the blueprint that specifies it, and
  the census over such a store reports `keeps_history`. Nobody classified
  that history, and a remote would send it. So an adoption whose census
  reports `keeps_history` and whose declaration carries no `scope_floor` is
  refused with `CONTENT_SCOPE_UNDECLARED`, returning the census. `establish`
  takes in nothing, and needs none.
- **It is at least what the store already declares.** On `adopt`, the census
  reports `highest_scope`: the highest scope the entries it found declare in
  their bytes, a registered label's `maps_to` included
  ([A registered label counts](#where-a-scope-is-declared)). A
  `scope_floor` below it is refused with `CONTENT_SCOPE_LOWERED`, naming
  both, so a floor never states that a store is less sensitive than its own
  files say. It is the least floor the census proposes to the person.
- **It fits the place.** A `scope_floor` above the ceiling derived at
  declaration is refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`, because
  every entry would be above it.
- **It is declared, never configured, and never lowered.** It is fixed when
  the repository is declared, recorded on the `declare` entry and reported on
  `ContentRepository`. Lowering it would declassify every entry it covers, and
  no route lowers a scope. A repository declared without one, and every
  configured repository, stays without one (see the gap under
  [A store that already exists is the normal case](#a-store-that-already-exists-is-the-normal-case)).

A remote's `history_scope` ([What would leave](#what-would-leave)) is a
narrower act for a repository without a floor: one person classifies, for one
remote, the versions its census counted unclassified.

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
> stays as declared: its placement, its `self_decision_ceiling` and its
> `scope_floor`, or the absence of either. A repository declared without one,
> and every configured repository, cannot be given one. Naming an amending verb needs the
> same care as retiring, because an amendment that lowered separation would
> weaken a control over bytes already written under the stronger one.

---

## Repositories Outside a Tenant

Everything else in this document describes a repository a tenant has declared.
Some repositories belong to no tenant: the published corpus, a repository of
standards somebody is writing, a programme authored to be offered to
organisations that have not taken it. No tenant has declared them, so nothing
here — custody, scope, proposals, the change log — covers them, and this service
holds none of them.

**What one may be.** It may be authored, versioned, validated and offered: edited
where it lives, kept under version control, checked against the schema for each
family it holds ([`schemas/README`](../schemas/README.md#schema-files) names
which schema governs which), and listed to somebody deciding whether to take it.

**What it never is.** A claim that a tenant conforms — that it meets a standard,
a control or an obligation — the evidence chain under such a claim, and an
export of either MUST NOT cite it, or anything it holds. What they cite comes
from a tenant — for content, an entry of a repository the tenant declared, at a
version its change log records ([The Change Log](#the-change-log)). A
repository outside a tenant has no declared custody, no recorded scope and no
log, and anybody who reaches it can change it with no record any tenant can
see. Its own history is a copy and a convenience, as a backend's is (Design
Principle 9), never evidence.

**What it holds reaches a tenant only by the tenant's own act**, made in the
tenant and recorded there:

- **The tenant declares it**, as a store that already holds bytes —
  `disposition: adopt` ([Declaring a Repository](#declaring-a-repository)). From
  then on it is that tenant's repository, governed as any other, and no longer
  outside a tenant. Every entry it holds is recorded with provenance `unknown`,
  and the census records the digest of each one it could read
  ([What an adopted entry is, and is not](#what-an-adopted-entry-is-and-is-not)).
- **The tenant installs a copy** into a repository it has declared — a standard
  it will be measured against, a programme it takes on
  ([`schemas/programme`](../schemas/programme.md#installation-checklist))
  — written as any change is ([Who may move an entry](#who-may-move-an-entry)),
  so the change log of the repository written to holds the digest of every
  file written. The copy is the tenant's, and the repository it came from stays
  outside. Where the copy came from belongs in the tenant: the commit the
  repository was read at, where it has commits, and the digest of every file
  taken. That record may give the repository's name or address, to say where
  to look, and nothing in the record joins on either: a repository outside a
  tenant has no durable identifier, and both move.

> **Gap.** No field of this contract records where a copy came from. Neither
> `EntryWrite` nor `ContentChange` carries an origin, so the log of the
> repository written to shows each file written and not what it was taken
> from. Until a field does, whatever installs a copy MUST say with its answer
> that the copy's origin is not recorded in the tenant (Design Principle 5).
> This line exists so the absence is a known gap rather than an oversight.

A build that reads such a repository as a blueprint source records it, with its
revision, in the provenance it writes into what it generates
([`architecture/cli`](cli.md#weblisk-server-init)). Where the build is a
tenant's, that record and what the build generated are the tenant's. The
repository it names stays outside either way. Verifying what the build generated
against its blueprints is a different claim, about an implementation rather than
a tenant's conformance ([`architecture/testing`](testing.md#architecture)): the
checks its result names come from those blueprints, and it cites them at the
revision that record holds.

**Each repository has exactly one home**: the tenant that declared it, or none.
It is never kept outside a tenant while a tenant holds it, and never declared by
two tenants. A copy a tenant installs is not a second home for the repository it
came from; it is content of a repository with a home of its own. A remote is
not a repository outside a tenant: it is a tenant's repository sent to a second
place, counted in that repository's [effective custody](#effective-custody).
Nor is a copy of a tenant's repository that a backend reports and no remote
declares, such as a git remote its history was pushed to: it counts in the same
effective custody, where the repository records it in `reported_copies`.
Nor is a client's installation state a home ([Reserved Paths](#reserved-paths)).
What a client keeps there for a repository outside a tenant is a reference to
where it lives, or a cache of it, never the repository itself. A cache is taken
from where the repository lives — a copy of it, or what was derived from reading
it — and refreshed only from there. The client never edits the repository's
files in it, so losing it costs a fetch or a re-read and nothing else: the
repository is still where it lives. The CLI's blueprint cache
is one, for each source no tenant has declared
([`weblisk blueprint update`](cli.md#weblisk-blueprint-update)).

**The rule can be checked only where both homes are visible.** This service sees
its own placements alone — among which
[One placement, one repository](#one-placement-one-repository) already refuses an
overlap — and neither another tenant's nor what a client keeps outside every
tenant. A client that keeps repositories outside a tenant can check the rule only
against local paths. It refuses to keep, as outside a tenant, a path that equals,
contains or sits inside a path it knows is a tenant's — an overlap in either
direction, as One placement, one repository refuses one:

- a **tenant directory** it recorded: the directory a tenant was built into,
  which [`weblisk tenant create`](cli.md#weblisk-tenant-create-name) produces
  and which holds the tenant's keys. A path that encloses one holds what the
  tenant's builds generated, which is the tenant's;
- a path at which it reads a tenant's repository itself, where it reads one at
  a local path.

It refuses too a path that is, or sits inside, its own installation state,
where it keeps no repository. Two paths are compared as the filesystem holding
them resolves them, never as strings: a string comparison puts `/x/tenant-2`
inside `/x/tenant`, and lets a link, or a letter in another case, take a
tenant's path outside the tenant. Every link in either path is resolved first,
and the two are then compared segment by segment, two segments matching
wherever that filesystem opens one entry for both — without regard to case
where it folds case — as [Reserved Paths](#reserved-paths) compares a name by
what is opened rather than by its bytes.

It cannot see where a tenant keeps any other repository — a placement names a
backend, never a location
([A placement names a backend, never a location](#a-placement-names-a-backend-never-a-location))
— so a path that passes has been shown only not to overlap a path that client
knows is a tenant's, never to belong to no tenant (Design Principle 5).

---

## Remotes

A **remote** is a copy of a repository that this service keeps at a second
place, its **destination**. The service sends the repository's entries there
and, where the backend keeps versions, every version it has recorded. It takes
nothing back.

A remote is how a tenant keeps a copy of its content off the machine that holds
the store, and how it publishes one. Both put the tenant's bytes somewhere its
own service does not control. So a remote is declared the way a repository is
adopted, by a person who has seen what would leave, and the place it names
lowers what the repository may hold. It is a destination as
[`patterns/scope`](../patterns/scope.md#destination-ceilings) defines one, and
this section is where its ceiling and its gate are specified.

### A remote is sent to, and never read from

- **Push-only.** The service sends to a remote. It never reads an entry, a
  digest, a version or a history from one, and never takes a change made there
  into the repository. The one thing it asks a destination is whether it still
  holds only what the service sent. What counts as held at a destination is
  what the blueprint that specifies its backend says.
- **Never a source of truth.** Nothing this service answers comes from a
  remote: not a read, a census or a recovery. A store rebuilt from a remote's
  copy is a new store. It comes under governance by adoption, with a census, and
  every entry in it is recorded with provenance `unknown`.
- **A remote that diverged is reported, never pulled.** A destination that
  holds something this service did not send makes the remote `diverged`. The
  service records what it found, sends nothing more, and never overwrites the
  destination to make it match. The remote leaves `diverged` by itself once
  the destination again holds only what the service sent, and sending
  resumes then only where [Remote Send Flow](#remote-send-flow) step 4
  lets anything leave. A change somebody made at the
  destination reaches the repository only as that person's own write or
  proposal.
- **Sending never holds up a write.** A write is complete when the repository
  holds it. Sending follows, in the order the versions were recorded, once
  [Remote Send Flow](#remote-send-flow) step 4 lets anything leave, and
  until then the remote is `behind`.
- **What is sent comes from the service's own record.** It is never read from
  the store at the moment of sending, because another authority can change the
  store. The blueprint that specifies the backend says where that record is
  kept.

### Declaring a remote

`POST /v1/content/repositories/{repository}/remotes`, operation
`DeclareRemote`. The steps and their order are the
[Remote Declaration Flow](#remote-declaration-flow).

**Nothing leaves unseen, and nowhere unseen.** Declaring a remote is
adoption's two-step, over what would leave and where it would go rather than
over what a placement holds. A first call carries no `if_match`: the service
returns a `RemoteCensus`, refuses with `CONTENT_REMOTE_UNSEEN`, and records
nothing. The caller re-submits with the census `digest`.

The digest is computed as an adoption census's is (see
[`if_match` on a declaration](#if_match-on-a-declaration)), over the ordered
`(path, entry digest)` pairs of every version that would leave. Two more pairs
follow them, each with an empty path, in this order:

1. **The terms.** The digest, in RFC 8785 canonical form, of an object whose
   members are the census's `destination`, `held_by`, `custody`,
   `attestations` and, where there is one, `history_scope`: where the bytes
   would go, who holds that place, and what the declaration claims. This pair
   is always present.
2. **The backend's report**, bound as an adoption census binds it, where the
   backend's blueprint declares one.

So the digest changes when a version is recorded between the two calls. It
also changes when the confirming declaration names another destination, or
claims other custody, attestations or `history_scope`, and when the
destination's backend has since been declared held by somebody else. Each is
refused with `CONTENT_PRECONDITION_FAILED`. There is no other way to obtain
the precondition, so a remote cannot be declared by somebody who has not been
told what it would receive, where it would go, and who holds that place.

**It is reserved before anything is made, as a store is.** A confirmed
declaration follows establish's order, for the reason given under
[A create that does not finish](#a-create-that-does-not-finish): the durable
record comes before the act that cannot be undone. The remote is reserved
first, in `establishing`, sending nothing. Only then is its credential created,
and only then is the destination demonstrated. A repeated declaration with
identical arguments against a remote in `establishing` resumes where it
stopped and creates no second credential. A completed declaration is not
idempotent: repeating it is `CONTENT_REMOTE_EXISTS`.

**The credential is the tenant's, for one destination.** A remote is reached
with a credential the service creates for that remote alone and holds through
[`patterns/secrets`](../patterns/secrets.md). Its secret part never leaves the
service. `ContentRemote.credential` carries the part a person registers at
the destination. The service presents it only there
([`architecture/orchestrator`](orchestrator.md), *Presenting a credential to a
component*). Retiring the remote destroys it. A credential that a person or a
client brought would be one the tenant does not control, and could be presented
anywhere it was valid.

**The destination is demonstrated, not claimed.** The declaration's custody and
attestations are claims, demonstrated against the destination before they take
effect. The blueprint that specifies the destination's backend says how its
custody is demonstrated. A destination whose custody that blueprint does not
demonstrate is recorded `opaque`, whatever was claimed, and its ceiling is
derived from that as every remote's is
([Derived Scope Ceiling](#derived-scope-ceiling)). The service also
demonstrates that the
destination holds nothing it would not send, which is otherwise refused with
`CONTENT_NOT_EMPTY`, and it tests `anonymous_read` by trying to read the
destination with no credential. A destination that cannot be reached yet —
the ordinary case, before a person has registered the credential there —
answers `CONTENT_ESTABLISH_INCOMPLETE`, carrying the remote and its credential.
Nothing has been sent.

**Not in configuration.** A remote is never declared in a configuration file,
for the reason adoption is not: a file cannot hold a census digest that did not
exist when it was written, and a file that could send a repository's history
would send it on every fresh start, unread.

### Who may declare a remote

| Capability | Lets the holder | Worst case in the wrong hands |
|---|---|---|
| `content:replicate` | Declare a remote, with `content:connect`. Retire one | every version of a repository sent to a destination of their choosing |
| `content:connect` | Have the service create and hold a credential that reaches outside the tenant's store | the tenant holding a key to a place outside itself |

Declaring a remote requires both. Neither alone sends a byte anywhere: a
remote with no credential reaches nothing, and a credential with no remote is
sent nothing. Sending a repository outside the tenant therefore takes two
grants, the rule `content:establish` already follows beside `content:declare`
(see [Creating is not declaring](#creating-is-not-declaring)). Retiring a remote
needs `content:replicate` alone, because it only ever reduces where bytes go.

Two grants separate two people only where two people hold them, and today
nothing makes them: only the `admin` role carries either
([`architecture/admin`](admin.md#operator-roles)), and a role is a fixed
bundle, so every admin holds both and one admin can declare a remote alone.
What the two grants guarantee is that no other role, and nothing that is not
a person, can.

Both are *person only* in [`protocol/types`](../protocol/types.md). Sending a
tenant's history to another place is a judgement, and a service has none to
exercise (principal-identity Design Principle 11). The rules that keep a
person-only capability with people are stated once, under
[Who may move an entry](#who-may-move-an-entry), and hold here unchanged.

### What would leave

Wherever a remote is concerned, a version's **scope** is what was declared
for it ([An Entry's Scope](#an-entrys-scope)):

- A version a `ContentChange` recorded is at that change's `scope`, which the
  Write Flow has made the highest declaration that applies to it. A change
  that recorded none leaves its version unclassified.
- Any other version — one the store held before it was adopted, one recorded
  for an observation, one a person made in the store directly — takes, for
  each entry it adds or changes, the higher of the scope that entry's bytes
  declare, a registered label's `maps_to` included
  ([Where a scope is declared](#where-a-scope-is-declared)), and its path's
  recorded scope. The version is at the highest of those.

A path's recorded scope is never cleared by a removal
([The recorded scope](#the-recorded-scope)), so an earlier version of a path
that no entry holds now is still classified by it.

A version that only removes entries needs no scope, because it adds no bytes.
A version is **unclassified** when an entry it adds or changes has no scope by
either rule. Nothing declared its level, and it is never assumed to be at any
level.

The census reports, for the repository and the destination:

- the destination, who holds it, and the custody and attestations the
  declaration claims for it;
- the entries now, and every earlier version that would leave with them;
- the paths an earlier version holds and no entry holds now, because a person
  looking at today's entries cannot see them;
- the highest scope recorded for anything that would leave;
- how many versions that would leave are unclassified, as `unclassified`;
- each path that would leave above the remote's prospective ceiling, and each
  reserved path that would leave. Either refuses the declaration, and the census
  names them so the person can see why before confirming;
- the ceilings the remote and the repository would have, computed from the
  claims. The demonstration can only lower them;
- what the backend's blueprint binds in `backend_report` — for a store under
  version control, the names every earlier version was recorded under.

**Unclassified history is classified once, by a person, or it does not
leave.** A declaration whose census counts unclassified versions is refused
with `CONTENT_SCOPE_UNDECLARED` unless it carries `history_scope`. That is one
scope, which the declaring person gives every version the census counted
unclassified, in one recorded act. It covers exactly those versions and no
version recorded after the census. For every check made for that remote, each
of them is then at `history_scope`, so one above the remote's ceiling refuses
the declaration and, should that ceiling later drop, holds the remote. The census
reports the `history_scope` it was computed under, and its digest binds it.

An unclassified version recorded after the census is not covered. It is held,
never sent (Remote Send Flow, step 3).

**A repository with a floor makes no unclassified version.** Its floor is
every path's least recorded scope
([The recorded scope](#the-recorded-scope)), so every version it records is
at a declared scope. In a repository declared without one, a write that
declares no scope for a path that has none, and, under shared custody, an
entry a person creates in the store directly with no scope in its bytes, each
make an unclassified version, and a remote held on it stays `behind`, and
says so. An edit to an entry that already has a recorded scope does not,
because the recorded scope carries to it. Nothing in this contract classifies
a version after it is recorded, and no verb adds a floor to a repository
already declared (see the gap under
[A store that already exists is the normal case](#a-store-that-already-exists-is-the-normal-case)).

A reserved path refuses the declaration even where it appears only in an
earlier version, put there by somebody out of band. One that appears after the
census holds the remote (Remote Send Flow, step 3). Installation state and
control state never leave.

### Who holds a destination

Every backend says who holds the store it reaches: the tenant, or a third party
(`held_by`, under [Configuration](#configuration)). A backend that does not say
is a third party's. It is never inferred from a host, a URL or a provider name,
as custody is not.

`held_by` is an operator's statement, and nothing this service does
demonstrates it. That limit is stated here, as Design Principle 5 requires. The
census reports `held_by` and its digest binds it, so the person confirming has
seen what the operator said, and `content.remote_declared` carries it.

A remote whose destination a third party holds is declared, checked and sent
to by every rule in this section, and by no rule of its own. Two of those rules
are what make it safe to declare:

- **Nothing leaves unclassified.** Every version a remote receives is at a
  scope declared for it ([What would leave](#what-would-leave)). A version that
  is not is held, never sent.
- **A remote's ceiling does not depend on who holds it.** Its destination's
  ceiling is derived from what was demonstrated about it, and a plain one is
  capped, wherever it is and whoever holds it
  ([Derived Scope Ceiling](#derived-scope-ceiling)).

A copy on a machine the tenant owns, away from the machine that holds the
store, is capped the same way, because whoever can read that machine reads the
copy without passing through this service. Where nothing demonstrates who else
can read it, as nothing does for a destination reached by a key registered
there ([`patterns/content-git`](../patterns/content-git.md)), its ceiling is
`public` by the third row of the remote table under
[Derived Scope Ceiling](#derived-scope-ceiling), and confirming it makes the repository's
ceiling `public` for good ([Effective custody](#effective-custody)). Such a
copy gives durability only to a repository that holds nothing above
`public`. That limit is stated here, as Design Principle 5 requires, rather
than read into the words "the tenant's own machine".

### Effective custody

A repository's bytes live wherever a copy of them lives. Its **effective
custody** is the most permissive custody of any place they live, in the order
`exclusive`, `shared`, `opaque`: its store, and every remote that has been
confirmed, retired or not. Its **ceiling** is the lowest ceiling of those
places.

- `custody` stays the store's. It says who else can write the bytes this
  service reads, and reconciliation and the anomaly rules of
  `architecture/data-security` depend on exactly that. A remote writes
  nothing here, so it does not change it.
- `effective_custody` says who else can read a copy. Every statement about
  access is made from it: an `AccessStatement` carries `access_complete: false`
  unless effective custody is `exclusive`.
- `ceiling` is the effective ceiling, and the ceiling check of every write and
  every proposal uses it. `store_ceiling` is what the store alone allows. A
  consumer that reads only `ceiling` gets the safer answer.
- A remote's own ceiling is derived from what was demonstrated about its
  destination, as [Derived Scope Ceiling](#derived-scope-ceiling) derives a
  remote's.
- **Bytes that have left have left.** Retiring a remote never raises the
  ceiling and never narrows effective custody.
- **An undeclared copy counts.** A backend that can see a copy of the store
  that no remote declares MUST report it. It counts as a place whose custody
  is `opaque` and whose ceiling is `public`, by the second row of the remote
  table under [Derived Scope Ceiling](#derived-scope-ceiling): it is a copy
  away from the store, nothing demonstrates who reads it, and its anonymous
  read is never tested, because the service does not reach it. A copy nobody
  declared is trusted no more than a remote declared at the same place
  would be. Effective custody becomes `opaque`, the ceiling becomes
  `public`, and `content.custody_degraded` is published naming the content
  now above it. A copy once reported counts for good, as a retired remote
  does: the repository records where it was seen, in `reported_copies`, and a
  later report that no longer names it removes nothing, because what was
  copied there may still be read. So a store whose history may have been
  sent to a place such as a public forge accepts nothing above `public` from
  the first report of that copy, and removing the git remote that pointed there
  does not raise the ceiling again.

**A remote counts from the moment it is confirmed** (Remote Declaration
Flow, step 11), whether or not anything has reached its destination, and it
never stops counting. Whether bytes have arrived is something the service
learns late and can be wrong about: a send whose answer was lost may have
landed. Counting from confirmation also means nothing is written through this
service that the remote could not then receive. A remote in `establishing`
counts toward nothing, so what is written while a person registers its
credential is checked against it when it is confirmed (Remote Declaration
Flow, step 10).

### States

| State | Means |
|---|---|
| `establishing` | Reserved and not yet confirmed. Nothing has been sent |
| `current` | The destination held every recorded version when last checked |
| `behind` | Versions are recorded and not yet sent. `held_reason` says why, where something holds them back: a version the service will not send, which `held_path` names, or `egress-unrecorded`, which holds every send ([Remote Send Flow](#remote-send-flow), step 4) |
| `diverged` | The destination holds something this service did not send. Nothing is sent |
| `unreachable` | The last attempt could not reach the destination, or its credential was refused |
| `retired` | A person retired it. Nothing is sent, its credential is destroyed, and its record stays |

A version that may not be sent — one that holds a reserved path, one that is
unclassified and was not counted by the census, one above the remote's
ceiling — is held, never skipped. Nothing recorded after it is sent either,
because a destination that received later versions without it would hold a
history with a hole in it.

Every count a remote reports is as of its `checked_at`, and is absent when it
cannot be established. `behind_by` is never 0 for a remote the service could
not check.

### Retiring a remote

`DELETE /v1/content/repositories/{repository}/remotes/{remote}`, operation
`RetireRemote`. The remote becomes `retired`: nothing more is sent, its
credential is destroyed, and its record stays, naming who retired it. Nothing
at the destination is deleted, because the service never writes there except to
send. The response says that the destination still holds what was sent and
that the credential registered there is for a person to remove.

A remote in `establishing` may be retired too. It was never confirmed, so it
never counted toward effective custody.

Retiring a remote that is already `retired` changes nothing. It returns the
remote as recorded, naming the person who retired it first.

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
hides no content, because none of it was ever content. Because nothing
observes one arrive, a remote census names each that would leave, and every
version is checked for one before it is sent to a remote
([Remote Send Flow](#remote-send-flow)). A backend's control
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
`content:decide` **person only**, and `content:replicate` and
`content:connect` with them (see [Who may declare a remote](#who-may-declare-a-remote)).
Three rules keep every person-only capability with people:

- **No service holds one.** A hub refuses a person-only capability in a
  service subject's grant and in every token minted for one
  ([`patterns/principal-identity`](../patterns/principal-identity.md),
  `service-subject-constraints`), and refuses a registration whose manifest
  declares one ([`protocol/spec`](../protocol/spec.md), `POST /v1/register`).
  Both refusals carry `CAPABILITY_PERSON_ONLY`, the wire form
  [`protocol/types`](../protocol/types.md#error-handling) registers for
  principal-identity's `capability_person_only`. A registered component that
  runs agents can therefore only propose their output.
- **This service honours one only on a pass.** A person-only capability
  counts only on a pass addressed to this service
  ([`protocol/identity`](../protocol/identity.md#the-pass) rule 6), which the
  orchestrator mints for a person's operator token, a token a hub mints for an
  operator, a person, through a credential that person's identity attested
  ([`architecture/admin`](admin.md#operator-token)). On any other token — a
  registered component's, a channel's — this service treats it as absent. A
  hub that issued one by mistake has still opened no route.
- **No agent holds a person's token.** An agent acts under an authorisation
  that never names a person-only capability (principal-identity,
  `agent-delegation`), or under a service identity, and a console never gives
  one a token minted with a person's credential, narrowed or not
  ([`architecture/admin`](admin.md), `console-credential-use`). So an agent's
  work reaches this service as a proposal made under a service identity, or
  in a request its person submits as their own act. For a run its person
  attends, a console may send reads here through the tenant's admin gateway,
  which carries each on a pass naming `content:read` or `content:describe`.
  Such a read is the person's, and it changes nothing.

A decision is judgement, and a service has none to exercise
(principal-identity Design Principle 11).

**A person's request arrives on a pass.** Before it performs a write, a
removal, a decision, a remote declaration or retirement, or a repository
declaration that carries `self_decision_ceiling` or `scope_floor`, this
service looks at the token. One that is not a pass addressed to it does not
hold the capability the act needs, as the rule above says, so the act is
refused with `FORBIDDEN`, whatever its `cap` or the request carries; an
operator token is refused before this, on every route, with `PASS_REQUIRED`
([`protocol/identity`](../protocol/identity.md#the-pass)). On a pass, it
authorises the act against the pass's `cap`, which the orchestrator computed
at the exchange from what the operator's role carried then, never beyond the
token's `cap`, and only for a token it judged live then
([`architecture/orchestrator`](orchestrator.md#token-exchange-post-v1tokenexchange),
`token-exchange`). This service asks nothing again. So a removed operator, a
revoked credential and a lowered role reach this service at the person's next
request, and a pass minted before lives at most 30 seconds. The audit entry
for a request a pass carried names the person as `actor`, by the pass's
`identity_id`, and the gateway that carried it as `via`, by its
`act.identity_id`.

Every other request — a read, a listing, a proposal, a description, a
checkpoint — is authorised on the token as verified. A person's arrives on a
pass too, so the same 30 seconds bound it. That window is stated here, as Design Principle 5
requires.

**What the tenant cannot see.** A token is a bearer credential. This service can
tell whose credential a request used. It cannot tell whether that person sent
the request or software they run sent it with their credential. The first two
rules hold at the tenant for every service and every registered component, and
no client can loosen them. The third holds in the console: a request an agent
sent with a person's token would be that person's to this service, and a
console that let an agent use one would produce changes recorded as that
person's own acts. These limits are stated here, as Design Principle 5
requires, rather than hidden behind the two rules that do hold. One limit is
not among them: what this service is sent on a person's behalf is a pass
addressed to it alone, so it holds nothing of that person's it could present
elsewhere ([`protocol/identity`](../protocol/identity.md#the-pass)).

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
`on_behalf_of`. The person who started an agent is a requester of its
proposal: its `actor`, where that person submitted it under their own token,
or its `on_behalf_of`, where a service submitted it for them.

Requester and decider are compared by identity id and by nothing else (see
[Who a change was for](#who-a-change-was-for)). A name, an email address or a
token's `sub` is never compared: the same person can appear under several of
them, and a comparison across two of them finds two people where there is one
(principal-identity Design Principle 10).

An identity id survives a change of identity key: the hub keeps it
([`architecture/admin`](admin.md#changing-an-identity-key)), so a person who
proposed a change and then changed their key is still its requester. It does
not survive being admitted twice. A person registered again under a new name,
after losing a key, or registered under a second name at all, has two identity
ids, and this service cannot see that they are one person. That limit is
stated here, as Design Principle 5 requires. The hub's audit trail names the
admin who approved each registration.

A decision to apply is made by someone who is not a requester, and the
resulting `ContentChange` records `separation: independent`. This is
[`patterns/approval`](../patterns/approval.md) Design Principle 2, applied to a
proposal.

A repository MAY allow one person to decide their own change, up to a scope it
declares. This is the one exception `patterns/approval` names to its separation
of duties, and it is bounded there as it is here. `self_decision_ceiling` on
the repository's declaration is the highest `ScopeLevel` at which it is
allowed, and it is never `critical`: `patterns/approval` Design Principle 2
requires a different approver for a critical change and makes that not
configurable, so a declaration naming `critical` is refused with
`CONTENT_SEPARATION_REQUIRED`. A `critical` change is therefore never
self-decided, whatever a repository declares:

- **Absent**, the default: a requester's decision to apply is refused with
  `CONTENT_SEPARATION_REQUIRED`.
- **Present**: a requester may apply a change whose scope is at or below it —
  the proposal's scope, or on a `delete` the recorded scope of the path it
  removes ([The recorded scope](#the-recorded-scope)) — and the
  `ContentChange` records `separation: self`. Above it, the decision is
  refused with `CONTENT_SEPARATION_REQUIRED`.
- **A change with no scope is never self-decided.** A proposal that declares
  none, on a path with no recorded scope, and a `delete` of a path with no
  recorded scope, are unclassified. Nothing says they are at or below any
  level, so a requester's decision to apply one is refused with
  `CONTENT_SEPARATION_REQUIRED`, whatever `self_decision_ceiling` says. In a
  repository with a `scope_floor` there is no such change.

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

- **signed** — the person's own record-signing credential signed a statement
  of the change, and the service verified it before writing
  ([The change statement](#the-change-statement)). Only the person who moved
  the entry can be signed: the writer on a direct write, the decider on an
  applied proposal;
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
| `actor` | The subject who prepared the change: the writer on a direct write, the proposer on an applied proposal | Always | witnessed; signed on a direct write that carries the writer's `statement` |
| `on_behalf_of` | The person the proposer acted for | The change applied a proposal whose request stated one | asserted |
| `approved_by` | The person whose decision applied the change | The change applied a proposal | witnessed; signed when the change carries the decider's `statement` |
| `proposal` | The proposal the change applied | The change applied a proposal | recorded |
| `separation` | Whether a requester decided: `independent` or `self` | The change applied a proposal | recorded |
| `statement` | The signature of the person who moved the entry, with the attestation that binds their key to them | They sent one, and it verified | recorded. It is what makes that person's part signed |
| `version` | The backend's own marker for the state the change produced | The backend keeps one | recorded |

- **`actor`** is who prepared the change, which is not always whose grant let
  it land. On a direct write it is the writer. On a change that applied a
  proposal it is the proposal's `actor` and not the decider: one subject
  prepared the change and another let it land, and the record names both. The
  second is `approved_by`.
- **`on_behalf_of`** is absent on a direct write. A direct write needs
  `content:write`, which counts only on a pass, a person's, so the writer acts for
  themselves and `actor` already names them. On a proposal, a client that
  carries out a person's instruction under its own service identity MUST send
  it. Without it that person is absent from the record, and separation cannot
  see them. A person who submits an agent's work under their own token needs
  none: the token names that person, so `actor` is them, witnessed. A
  scheduled job is not a person and is never `on_behalf_of`. It names itself
  in `run`, and `on_behalf_of` names the person it acts for, where there is
  one.
- **`agent` and `run`**: a client submitting a change that an agent prepared
  MUST send `agent` and `run` with the proposal, and `on_behalf_of` as well
  where it submits under its own service identity for a person.
  principal-identity Design Principle 13 requires the record to name the agent
  and the run that used a subject's authority, and the proposal is where the
  record holds them. Both are asserted. `proposal` leads from the change to
  them.
- **`approved_by`** is witnessed. The service authenticated the person who
  decided, and without a statement that is all it can say: it is not a
  signature under that person's sole control. It is signed only when the
  change carries that person's `statement`. It is a list, and under this
  contract it holds one person.
- **An approval is reported with its basis.** A consumer that reports an
  approval MUST say `signed` only where the change carries a verified
  `statement` by the approver, and `witnessed` otherwise. An approval somebody
  says was given outside the Decision Flow — in a client's own workflow, or by
  a person a client names — reached this service as nobody's decision. This
  service records no such approval, and a consumer that shows one MUST label
  it `asserted`. Whether an approval was `independent` rests on
  `on_behalf_of`, which is asserted (see
  [Separation of duties](#separation-of-duties)).
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

## The Change Log

Every declared repository has a **change log**: one entry for each change this
service made to the repository's entries, and one for each change it observed
made around it, in the order it recorded them. The log is the evidence of
record. What a claim, an export or an audit cites about a repository's history
is its log.

The log is an owned record under exclusive custody. It is held in the service's
own record store and never in a store a placement names, so it is never
content, never an entry and never sent to a remote. It shares its chain with no
other log, for the reason [`architecture/fabric`](fabric.md) Design Principle 6
gives: two writers on one chain fork it, and a fork cannot be told from
tampering.

It is a sealed log, as
[`architecture/storage`](storage.md#sealing-a-chained-log) defines one. That
section says how its entries are stored and chained, how the service's log key
is introduced, how a change of the service's own key is recorded, what a
checkpoint signs and how a verifier checks all of it. This
section says what the content log's own entries hold, who signs what, and what
a verifier checks beyond the chain.

### What an entry covers

Each entry records one act, once:

| `act` | Appended when | Holds |
|---|---|---|
| `declare` | The repository is recorded `declared`. Always the first entry, so its digest is the log id | `LogDeclaration`: the repository's id, `scope_path`, disposition, custody, store ceiling, `self_decision_ceiling` and `scope_floor`, and on adoption every entry the census found, with the scope its bytes declared |
| `change` | This service made a change: a write, a removal, or a decision that applied a proposal | `ContentChange`, with the person's `ChangeStatement` where one verified |
| `observe` | This service observed a change it did not make — an observation of state `changed` or `removed`, from the Custody Reconciler or from a read | `ContentObservation` |
| `key` | This service introduced a log key | `LogKey`, from [`architecture/storage`](storage.md#types) |
| `succession` | This service's registered key changed while it still held the one before | `LogSuccession`, from [`architecture/storage`](storage.md#types) |
| `checkpoint` | This service sealed the log | `LogCheckpoint`, from [`architecture/storage`](storage.md#types) |

**Every change this service makes is exactly one `change` entry.** Nothing else
is recorded as one. An observation of state `unknown` changes nothing and is not
appended. A proposal that is `open`, `rejected` or `stale` changed no entry and
is not in the log; the proposal is its record ([Proposals](#proposals)). Reads,
remote sends and custody re-verification change no entry either.

> **Gap — a remote send would leave no signed record of what left, so
> nothing is sent.** A send owes a signed egress record of what left, for
> which destination, and under what demonstrated ceiling, and this service
> cannot yet make one. That record is the next gap after this contract, and it
> waits on its own specification: what it records, who signs it, and, if it is
> a fixed-form statement of its own, a prefix with published test vectors
> ([`protocol/identity`](../protocol/identity.md#fixed-form-statements)). The
> signing that seals this log is specified
> ([`architecture/storage`](storage.md#sealing-a-chained-log)) and its three
> prefixes' vectors are published. The egress record is not specified here.
> Until it is, the
> [Remote Send Flow](#remote-send-flow) sends nothing to any remote
> (step 4), and a consumer MUST NOT report what a remote holds, or that it
> holds nothing above a level, from `checked_at` or from the remote's
> state.

**A path's recorded digest is its last entry.** The last `change` or `observe`
entry that names a path, or, where there is none, the `declare` entry, records
the identity the path holds as far as this service knows. It is what the Read
Flow and the Custody Reconciler compare the current bytes against, so a change
made around the service is observed once, and every read after it compares
against what was observed.

**An entry cites; it never copies.** It records paths, content identities and
the identity ids of the parties. It never holds an entry's bytes or a
proposal's: a digest binds the bytes without holding them. This is
[`architecture/fabric`](fabric.md) Design Principle 7, for the same reason. A
log that held bytes would be a copy of the repository, readable around the
access decision.

**Paths are in plaintext.** A path is a name, and a name can identify a
person, such as a record filed under somebody's name. The log records each path
as it is, and not as a keyed digest that would hide the name and keep the join.
That choice is bounded twice. The log is read whole or not at all, and only by
a caller who may read everything the repository has held
([Reading the log](#reading-the-log)). And a copy of the log carries what it
holds wherever it goes. An export that includes log lines discloses every path
in them, the identity id of every party they name, and, in each statement, the
signer's identity public key and any `device_label` their attestation carries.
An identity id is the fingerprint of the key a person registered with, so it
is the same at every hub they joined with that key, and those lines can link
a person across tenants. That is why
[`patterns/content-git`](../patterns/content-git.md) keeps identity ids out of
a store's history.

### A change is reserved before it is made

A crash between writing the bytes and appending the entry would leave the
service's own write unrecorded. Under shared custody the reconciler would then
record it as `external`, and under exclusive custody it would be an integrity
anomaly: the tenant's own write reported as somebody else's. So every change is
**reserved** before the backend is touched:

1. The service records, in its own state and not in the log, the repository,
   path and operation, `before`, the `after` of the bytes it is about to write,
   and everything the `change` entry will carry.
2. It writes the bytes and reads them back, as the Write Flow does.
3. It appends the `change` entry and releases the reservation in one record
   write — for a decision, with the proposal becoming `applied`.

Before it serves anything, the service settles every reservation it finds.
Where the path holds the reserved `after`, or nothing for a removal, it appends
the `change` entry the crash interrupted, with `version` as the backend reports
it, and applies the proposal where there is one. Where the path still holds
`before`, nothing was written and the reservation is released. Anything else is
handled as a change the service did not make: an `observe` entry under shared
custody, and under exclusive custody an integrity anomaly, reported as
[`architecture/data-security`](data-security.md) reports one.

### A log that does not verify

This service checks each change log as `architecture/storage` requires of an
owner: from its latest checkpoint to the tip, before its first append after it
starts and before each checkpoint
([`architecture/storage`](storage.md#an-owner-checks-its-own-log)). At start it
checks every log before it settles any reservation, so no reservation is ever
settled onto a log that fails.

A repository whose log fails the check is **broken**, and stays so:

- Every act that would append to its log is refused with `CONTENT_LOG_BROKEN`,
  naming the `seq` where the check failed: a write, a removal, a decision to
  apply a proposal, a reconcile and a checkpoint. Nothing is written to the
  repository's store, so no change is made that the log cannot record. A
  reservation found at start is left as it is.
- Everything else is served. Reads of entries, of proposals and of the log
  itself go on, because refusing them would hide the evidence somebody now
  needs. A proposal may still be made or rejected, since neither appends. A
  difference a read finds under shared custody is reported with the read and
  not appended.
- The `checks` the service's lease carries name the repository `not_ready`,
  and the log's `LogHead` names that `seq` in `chain` and `broken_at`.

Nothing repairs, truncates or re-chains the log. The log is held under
exclusive custody, so a failure means its stored lines changed after they were
written, and it is also an integrity anomaly, reported as
[`architecture/data-security`](data-security.md) reports one.

### Who signs

Two parties sign, and nobody else.

- **This service, as witness.** It seals the log with checkpoints, signed by a
  log key its registered ML-DSA-65 key introduces
  ([`architecture/storage`](storage.md#the-log-key)). A checkpoint says that
  these entries, in this order, are what this service recorded. It covers every
  entry before it. It vouches for what the service witnessed and recorded, and
  for nothing a caller asserted.
- **The person who moved the entry, where they send a statement.** A person who
  writes or removes an entry, or decides to apply a proposal, may send a
  `ChangeStatement` with the request: a signature by their own record-signing
  credential over the change this service is about to record
  ([The change statement](#the-change-statement)). Where it verifies, the entry
  carries it, and that person's part in the change is `signed`.

An agent, a schedule and a service sign nothing here. Only a person moves an
entry (Design Principle 7), and no agent holds a person's token
([Who may move an entry](#who-may-move-an-entry)). Their part is witnessed,
where the token that carried it names them, or asserted.

The service's registered key is the long-lived key `architecture/storage`
names, and the tenant's service directory lists it (`ServiceEntry.public_key`,
[`protocol/types`](../protocol/types.md)). Its fingerprint is the one a
verifier brings ([`architecture/storage`](storage.md#verifying-a-sealed-log)),
and it takes it from the tenant, never from the log. When the service rotates
that key, it appends a succession entry to every change log that has an
authority ([`architecture/storage`](storage.md#a-change-of-long-lived-key)), so
the key the directory lists now vouches for every key the log used before it.
A change log has an authority once it holds a key entry
([`architecture/storage`](storage.md#the-log-key)), so a rotation before its
first key entry appends nothing. A key generated afresh because the one before it was
lost has no succession entry.
A verifier holding only the directory's key then reports every earlier
authority `unvouched`, and the service's latest checkpoint still seals
everything before it.

### The change statement

```
"weblisk/content-change/v1" 0x00 <log id> 0x00 <role> 0x00 <path> 0x00 <operation> 0x00 <before> 0x00 <after> 0x00 <scope> 0x00 <proposal> 0x00 <signed_at>

<log id>     the repository's log id, as 64 lowercase hex characters
<role>       write, for a person who wrote or removed the entry directly;
             apply, for a person who decided to apply a proposal
<path>       the entry's path, as ContentChange records it
<operation>  create, modify or delete
<before>     the identity the change replaces, written <algorithm>:<digest>,
             such as sha256:<64 hex>; empty on create
<after>      the identity of the bytes the change writes, in the same form;
             empty on delete
<scope>      the scope the change declares; empty on delete, and on a
             change that declares none
<proposal>   the id of the proposal applied; empty on write
<signed_at>  when the person signed, in decimal Unix seconds, UTC
```

It is a fixed-form statement
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)). The
person's own client builds it from what it has checked itself: the bytes it
read and hashed, and the proposal it showed its person. It never signs bytes
this service or anybody else hands it.

**The service rebuilds the statement; it never takes one.** From the change it
is about to record, it rebuilds the bytes — on a write, `if_match` as `before`
and the digest of the decoded bytes as `after`; on a decision, the proposal's
path, scope, `before`, `after` and id — and verifies the signature over those.
A signature over anything else does not verify, so a signature never attaches
to bytes its signer did not sign.

A `ChangeStatement` verifies when all of these hold. They are checked before
anything is written:

1. The pass's `identity_id` is the attestation's `identity_id`. Only a person
   signs here, and only for themselves: a token that is not a pass was
   refused with `FORBIDDEN` before any statement is read
   ([Who may move an entry](#who-may-move-an-entry)). The fingerprint of the
   attestation's `identity_public_key` is the pass's `identity_key`, the
   person's current identity key as the orchestrator held it at the exchange
   ([`protocol/identity`](../protocol/identity.md#the-pass)).
2. The attestation's `purpose` is `sign-records`, and its signature verifies
   under `identity_public_key`
   ([`patterns/principal-identity`](../patterns/principal-identity.md),
   `record-signing`).
3. Its `credential_public_key` is an ML-DSA-65 public key. Its `not_after` has
   not passed, and is no more than 90 days ahead of the service's clock, the
   cap [`architecture/admin`](admin.md) puts on every attestation a hub
   records.
4. The hub vouches for the key, and it is not the key that signed the person
   in: the fingerprint of `credential_public_key` is one of the token's
   `record_keys`, and is not the token's `cid`. A key the hub does not hold for
   signing records, or has revoked, is named by no token minted since, and the
   key a client holds in order to obtain a token never signs the change that
   token carries.
5. `signed_at` is within 300 seconds of the service's clock, the replay window
   `protocol/identity` sets for registration. Replaying a statement therefore
   needs the same person's live token, within five minutes, against the same
   `before`, and on a decision a proposal that can be decided only once.
6. The signature verifies under `credential_public_key` over the rebuilt
   statement.

A statement that fails any check refuses the request with
`CONTENT_STATEMENT_INVALID`, naming the check. Nothing is written, and a
proposal stays `open`. The change is never recorded unsigned instead: a person
who meant to sign would otherwise find an unsigned change recorded as their
act.

The service does not compare the attestation's `hub_id` itself, because a
registered component is not told its hub's. Check 4 covers it: a key in the
token's `record_keys` is one the hub recorded, and a hub refuses an attestation
that names another hub. The statement is bound to one log by its log id, which
is what stops it being spent anywhere else. A verifier who knows the tenant's
hub_id checks the attestation against it.

Revoking a sign-records credential at the hub reaches this service through
the tokens: a token minted after the revocation does not name the key, so
check 4 fails once the tokens minted before it expire. Nothing already
recorded changes
([`patterns/principal-identity`](../patterns/principal-identity.md),
`record-signing`).

A statement is optional. A write, removal or decision without one is recorded
as it always was, and that person's part is `witnessed`. So a client that
relays a person's statement can drop it and still have the change recorded. A
client that sent a statement MUST check that the `ContentChange` it gets back
carries it, and report the change as unsigned where it does not.
`weblisk/content-change/v1` has test vectors
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)), and
every empty field above appears in one; which cases they cover is the file's
to say.
A client that signs a statement and this service, which verifies it, each test
against them. One that verifies is recorded, and one that fails refuses the
request, as [Security](#security) requires.

### Design Principle 6, strictly

[`patterns/principal-identity`](../patterns/principal-identity.md) Design
Principle 6 lets a classical key prove a live session, and forbids it to sign
any record meant to outlive one. The log is meant to outlive every session, so
the principle holds here with no exception:

- Every signature in the log is ML-DSA-65: each key entry, each checkpoint,
  each change statement and the attestation it carries.
- A signature made with a classical key — a passkey assertion, or an SSH,
  OpenPGP or X.509 signature — is never recorded as a signature and never makes
  a party `signed`. A statement under one is refused.
- A backend's own signatures are not evidence. This service signs no commit
  ([`patterns/content-git`](../patterns/content-git.md) Design Principle 1). A
  signature a person puts on their own commit is theirs, and the log records it
  nowhere.
- There is no transport exception. A transport credential authenticates one
  session to a third party's service, which is why `protocol/identity` lets it
  be classical, and it signs nothing this log holds.

### Approvals and separation in the log

An applied change records who approved it and whether they were separate from
its requester. Those fields, and the rules that set them, are
[Who a change was for](#who-a-change-was-for) and
[Separation of duties](#separation-of-duties). The log adds no rule to them. It
lets a verifier check them without this service:

- The `declare` entry records the repository's `self_decision_ceiling` and
  `scope_floor`, which are fixed at declaration.
- A `change` entry recording `separation: independent` names an `approved_by`
  that is neither its `actor` nor its `on_behalf_of`.
- A `change` entry recording `separation: self` names an `approved_by` that is
  one of them, with a scope at or below that ceiling: the change's `scope`, or
  for a removal the path's recorded scope as the log gives it before that
  entry, the floor included ([The recorded scope](#the-recorded-scope)).

A change whose separation does not fit its own parties is reported as
inconsistent, and so is a `separation: self` on a change with no scope by
those rules: this service never self-decides an unclassified change. The
log holds every scope the rule reads, so the check never needs anything
else. It is only as strong as `on_behalf_of`, which is asserted.

### Reading the log

`GET /v1/content/repositories/{repository}/log` takes a `LogQuery` and returns
a `LogPage`, as `application/json` like every other route. Its `lines` are the
stored lines from `seq` `from` on, at most `limit` of them, in order. Each is
one stored line's text without its line feed, as a JSON string. A stored line
is RFC 8785 output, which is valid UTF-8 and holds no raw line feed, so the
string decodes to exactly the stored bytes. Nothing is re-serialised: what a
caller decodes is what it hashes and verifies, and writing each line with one
line feed after it holds the log as this service stores it.

A caller continues from `next`. A page without `next` ended at the tip as it
stood when the page was read, which `tip` reports, and a `from` beyond the tip
returns no lines and no `next`. The log is paged by `seq`, not by the opaque
cursor a store's list operations use
([`architecture/storage`](storage.md#implementation-notes)), because `seq` is
part of what a verifier checks, and a caller resuming from the last `seq` it
holds needs nothing else from the service.

**The log is read whole or refused, and never filtered.** A log with lines left
out cannot be verified, because each missing line breaks the chain at the next.
The enforcement storage proxy intercepts with operation `read`, the
repository's `scope_path`, and as the resource scope the highest scope the log
records: the `store_ceiling` in its `declare` entry and the `scope` of every
`change`. A caller who may not read everything the repository has held reads
none of its log, and is refused with the code the storage proxy gives
([`architecture/enforcement`](enforcement.md)).

`GET /v1/content/repositories/{repository}/log/head` returns a `LogHead`: the
log id, the tip, the latest checkpoint with the key entry that introduced its
key, how many entries are unsealed, and what the service's own check of the
chain found. It names no path, so `content:describe` is enough. A person's
client reads it to learn the log id it signs with, so a client that signs for a
person needs `content:describe` beside `content:write` or `content:decide`. A
verifier keeps it as its own copy of a checkpoint, which is what exposes a log
rewritten later ([`architecture/storage`](storage.md#verifying-a-sealed-log)).

`POST /v1/content/repositories/{repository}/log/checkpoint` issues a checkpoint
first, where the tip has moved, and returns the head, so an export can be
sealed to its last entry. Where sealing is paused, because no log key can sign,
it appends nothing and refuses with `CONTENT_SEALING_PAUSED`, carrying the head,
whose `unsealed` counts what is not sealed. An export made then says that its
tail is unsealed.

All three routes refuse a repository not in the caller's scope with
`CONTENT_REPOSITORY_UNKNOWN`, and one still `establishing` with
`CONTENT_LOG_NOT_BEGUN`: its log begins when it is recorded `declared`
([Declaration Flow](#declaration-flow)). A query whose `from` or `limit` is not
an integer or is below 1, or whose `limit` is above 10000, is refused with
`INVALID_REQUEST` ([`protocol/spec`](../protocol/spec.md)).

### Verifying a log without this service

A verifier needs what `architecture/storage` lists for any sealed log, with the
content service's registered key, from the tenant, as the fingerprint it brings
([Who signs](#who-signs)). To check what people signed, it also needs:

- the tenant's hub_id, to check that each attestation names it;
- which identity id belongs to each person it wants to name, from the tenant's
  own records. The log names people by identity id and never by name, and it
  cannot vouch for whose an identity is;
- the identity keys the tenant records for each such identity id — an
  operator's `public_key` and its `retired_keys`, each with its `retired_at`
  ([`protocol/types`](../protocol/types.md#operator)) — because an identity id
  is kept across a change of identity key, and a statement signed after one
  carries an attestation by the new key;
- an RFC 8785 canonicaliser, for one purpose: an attestation's signature is
  over its canonical JSON (`Attestation` in principal-identity). Everything
  else is a digest of stored bytes or a fixed-form statement.

After storage's three steps — chain, keys, checkpoint — it checks:

4. **Statements.** For each `change` entry that carries a `statement`: rebuild
   the `weblisk/content-change/v1` bytes from the entry, with `role` `apply`
   where the entry records a `proposal` and `write` where it does not. Check
   the attestation as the service did in checks 2 and 3, with the entry's
   `recorded_at`, which the service witnessed and a checkpoint seals, in place
   of the service's clock: `not_after` no earlier than `recorded_at`, and no
   more than 90 days after it. Check its `hub_id` against the tenant's. Check
   that `signer` is the attestation's `identity_id`, that the attestation's
   identity key is one the tenant records for that identity id and, where it
   is a retired one, that the entry's `recorded_at` is before that key's
   `retired_at`, and that `signer` is the `actor` on a write or in
   `approved_by` on an apply. Then verify the signature. A key retired before
   the entry was recorded had had every credential it attested revoked, so
   the service could not have accepted its attestation then.
5. **Separation.** As [Approvals and separation in the log](#approvals-and-separation-in-the-log)
   says.
6. **A file.** Compute the SHA-256 of its bytes. The last `change` or `observe`
   entry for its path — or, where there is none, the `declare` entry — records
   the identity the path held last. A file that equals it is that version. One
   that equals an earlier entry for the path is an earlier version, and one
   that equals none is not a version this log knows.

For each party to each change, the verifier reports a basis, computed from the
log and never stored:

| Basis | When |
|---|---|
| `signed` | The entry carries that party's `statement`, and it passed step 4 |
| `witnessed` | The service took the party from the token it verified — `actor`, and each `approved_by` — and no statement of theirs passed step 4 |
| `asserted` | A caller or the backend stated it: `on_behalf_of`, an `observe` entry's `writer` |
| `unknown` | No party can be named: an `observe` entry with no `writer`, and every entry the `declare` entry adopted |

**A verified log proves what this service recorded, in order, and nothing it
did not see.** Under shared or opaque `effective_custody`, a change made around
the service appears only once it is observed, and until then a file can differ
from its last entry with nothing in the log to say so (Design Principle 5). An
unsealed entry is recorded and not yet signed. A statement proves that a
record-signing key attested by that identity signed the change. It does not
prove who held the key. Check 4 of [The change statement](#the-change-statement)
— that the hub named the key in the pass the person's request arrived on, and
that it was not the key that obtained the person's token — is the service's to
witness. The log does not hold the pass, so a verifier has that check only on
the service's seal.

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
          opaque. A remote does not change it — see effective_custody
      effective_custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: true
        description: The most permissive custody of any place the bytes live
          — the store, every remote that has been confirmed, retired or not,
          and every copy in reported_copies. Equal to custody for a repository
          with no remote and no reported copy
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
          Never critical. Fixed at declaration
      scope_floor:
        type: ScopeLevel
        required: false
        description: The least scope of every entry the repository holds, has
          held or will hold. Absent means none was declared. Fixed at
          declaration. See scope_floor covers what declares nothing
      records:
        type: bool
        required: true
        description: Whether this is its scope_path's records repository, the
          one that may hold an entry labelled pii. Fixed at declaration. See
          Where an entry labelled pii is kept
      backend_report:
        type: object
        required: false
        description: What the blueprint that specifies the repository's backend
          says it reports about the store — its control state, and whether the
          store is as the service left it — in the form that blueprint
          declares. Absent when that blueprint declares none
      reported_copies:
        type: "[]string"
        required: false
        description: Where each copy of the store that no remote declares was
          seen, as the backend's report named it, in the order first reported.
          Only ever added to. A copy the backend stops reporting stays, as a
          retired remote does, because bytes that have left have left. See
          Effective custody

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
          proposal, and never critical, which is refused with
          CONTENT_SEPARATION_REQUIRED. Absent means no requester may. Declaring
          it requires content:decide as well as content:declare, so only a
          person declares it. Not configurable
      scope_floor:
        type: ScopeLevel
        required: false
        description: The least scope of every entry the repository will hold,
          past versions included. Declaring it requires content:decide as
          well as content:declare, so only a person declares it. Required on
          adopt where the census reports keeps_history. Refused above the
          derived ceiling, and on adopt below the census's highest_scope. Not
          configurable, and never lowered. See scope_floor covers what
          declares nothing
      records:
        type: bool
        required: false
        default: false
        description: Declare this repository its scope_path's records
          repository. Refused where the scope_path has one, or where the
          derived ceiling is below restricted. Not configurable

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
      highest_scope:
        type: ScopeLevel
        required: false
        description: The highest scope the entries found are at by their
          bytes, each at the level it declares or, where higher, the maps_to
          of a label it carries that the tenant registers. The least
          scope_floor the declaration may carry. Absent when no entry declares
          a level or carries such a label this service can read
      keeps_history:
        type: bool
        required: true
        description: True when the placement's backend keeps earlier versions
          of its entries that this service can read, as the blueprint that
          specifies it says. A declaration adopting it MUST then carry
          scope_floor. See scope_floor covers what declares nothing
      backend_report:
        type: object
        required: false
        description: The facts beyond its entries that the blueprint specifying
          the placement's backend binds into the census, in the form that
          blueprint declares. When present, digest covers it
      issued_at:
        type: timestamp
        required: true

  RemoteDeclaration:
    description: The body of POST /v1/content/repositories/{repository}/remotes.
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
        description: Which backend, and where within it, the remote is sent
          to. Resolved and confined as a repository's placement is
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: false
        description: What the caller claims about who else can reach the
          destination. Absent is opaque. It takes effect only as the
          destination's backend's blueprint demonstrates it, and is recorded
          opaque where that blueprint demonstrates none
      attestations:
        type: CustodyAttestations
        required: false
        description: What the caller claims the destination can demonstrate.
          An undemonstrated claim is recorded false
      history_scope:
        type: ScopeLevel
        required: false
        description: The scope the declaring person gives every version the
          census counted unclassified, in one recorded act. It covers those
          versions and no version recorded after the census. Absent while the
          census counts any unclassified version, the declaration is refused
          with CONTENT_SCOPE_UNDECLARED. See What would leave
      if_match:
        type: string
        required: false
        description: The digest of the RemoteCensus this declaration confirms.
          Absent returns the census and declares nothing. It matches only a
          census taken for this destination, who holds it and these claims

  RemoteCensus:
    description: What a remote would receive, issued by the service so a
      person can declare it knowingly. Returned with CONTENT_REMOTE_UNSEEN
    fields:
      repository:
        type: string
        required: true
      digest:
        type: string
        required: true
        description: Computed as an adoption census digest is, over the ordered
          (path, entry digest) pairs of every version that would leave,
          followed by the pair that binds the terms — destination, held_by,
          custody, attestations and history_scope — and then the pair that
          binds backend_report where there is one. See Declaring a remote.
          The value a confirming declaration passes as if_match
      destination:
        type: Placement
        required: true
        description: Where the bytes would go, as the declaration named it and
          the service resolved it
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: true
        description: The custody the declaration claims for the destination,
          opaque where it claims none. A claim, not a demonstration
      attestations:
        type: CustodyAttestations
        required: true
        description: The attestations the declaration claims for the
          destination, each false where it claims none. Claims, not
          demonstrations
      history_scope:
        type: ScopeLevel
        required: false
        description: The history_scope the declaration carries, which every
          version counted in unclassified is taken to be at. Absent where it
          carries none
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
        items: string
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
        description: How many versions that would leave are unclassified —
          nothing declared a scope for them (see What would leave). Never
          assumed to be at any level. Non-zero with no history_scope refuses
          the declaration with CONTENT_SCOPE_UNDECLARED
      above_ceiling:
        type: list
        items: CensusPath
        required: true
        description: Each path, with its scope, that would leave above the
          prospective remote ceiling — an unclassified version's at
          history_scope. Non-empty refuses the declaration
      reserved:
        type: list
        items: CensusPath
        required: true
        description: Each reserved path in anything that would leave, with no
          scope. Non-empty refuses the declaration
      held_by:
        type: enum
        values: [tenant, third-party]
        required: true
        description: Who holds the destination, as its backend declares
      prospective_ceiling:
        type: ScopeLevel
        required: true
        description: The remote's ceiling as its claims would derive it (see
          Derived Scope Ceiling). The demonstration can only lower it
      prospective_repository_ceiling:
        type: ScopeLevel
        required: true
        description: The repository's ceiling once the remote counts, as its
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

  CensusPath:
    description: One path a RemoteCensus names, in the version that holds it
    fields:
      path:
        type: string
        required: true
      version:
        type: string
        required: false
        description: The backend's own marker for the version that holds it —
          a locator, never an identity. Absent when the backend keeps none
      scope:
        type: ScopeLevel
        required: false
        description: The scope it would leave at. Present in above_ceiling,
          absent in reserved

  ContentRemote:
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
        type: RemoteEstablishment
        required: false
        description: Present while state is establishing, and on a remote
          whose declaration did not finish
      held_by:
        type: enum
        values: [tenant, third-party]
        required: true
        description: Who holds the destination, as its backend declared it when
          the remote was declared
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: true
        description: Who else can reach the destination, as demonstrated.
          Undeclared or undemonstrated is opaque
      attestations:
        type: CustodyAttestations
        required: true
        description: What the destination demonstrated. Unknown is false
      anonymous_read:
        type: enum
        values: [refused, readable, unknown]
        required: true
        description: Whether the destination can be read with no credential.
          readable and unknown both give the remote the ceiling public
      ceiling:
        type: ScopeLevel
        required: true
        description: Derived from what the destination demonstrated, as
          Derived Scope Ceiling derives a remote's. Never configured
      credential:
        type: string
        required: false
        description: The part of the remote's credential a person registers at
          the destination, in the form the backend's blueprint declares. The
          secret part is never returned. Absent once retired
      credential_fingerprint:
        type: string
        required: false
        description: Names the credential without carrying it, in the form the
          backend's blueprint declares
      history_scope:
        type: ScopeLevel
        required: false
        description: Recorded. The scope the declaring person gave the
          versions the census counted unclassified. Absent where it counted
          none
      confirmed_at:
        type: timestamp
        required: false
        description: When the remote left establishing. From then on it counts
          toward effective custody and the repository's ceiling, retired or
          not, whether or not anything was sent. Absent while establishing and
          on a remote retired before it was confirmed
      first_sent_at:
        type: timestamp
        required: false
        description: When the destination was first sent anything. A record
          only; whether the remote counts is decided by confirmed_at
      behind_by:
        type: integer
        required: false
        description: Versions recorded and not yet sent, as of checked_at.
          Absent when it cannot be established, never 0 then
      held_path:
        type: string
        required: false
        description: The path that holds a version back, while state is behind
          because of it — the reserved path, or a path the version changes
      held_reason:
        type: enum
        values: [reserved-path, unclassified, above-ceiling, egress-unrecorded]
        required: false
        description: Why versions are held — a version holds a reserved path;
          it is unclassified and the census did not count it; or its scope is
          above the remote's ceiling; or, with no held_path, no send can yet
          leave the signed egress record it owes, which holds every remote.
          See Remote Send Flow
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
          says it reports about the destination — for a diverged remote, what
          was found there — in the form that blueprint declares

  RemoteEstablishment:
    description: What a remote declaration did and did not complete. Written
      durably before the credential is created, and updated as each step
      succeeds, in the manner of RepositoryEstablishment
    fields:
      reserved_at:
        type: timestamp
        required: true
      credential_created:
        type: boolean
        required: true
        description: Whether the remote's credential exists
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
        required: false
        description: The higher of the path's recorded scope and the scope the
          entry's bytes declare. Absent when neither exists — the entry is
          unclassified, and no level is assumed for it. See An Entry's Scope
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
      scope:
        type: ScopeLevel
        required: false
        description: Recorded. The scope the change declared — the write's, or
          the applied proposal's — against which its ceiling check was made.
          Never below the path's recorded scope or the scope the bytes declare
          (see A scope only rises). Absent on delete, and on a change that
          declared none, whose version is unclassified. It is what classifies
          the version the change produced (see What would leave)
      scope_basis:
        type: enum
        values: [bytes, recorded, chosen]
        required: false
        description: Recorded. Where scope came from — bytes when the bytes
          declare it, recorded when the path's recorded scope gives it and the
          bytes declare less, chosen when neither gives it and the change's
          own declaration is all that stands behind it. chosen is asserted
          unless the change carries the person's statement. Present exactly
          when scope is
      labels:
        type: "[]string"
        required: false
        description: Recorded. The custom_labels the bytes carry under
          scope_metadata. Absent when they carry none, and on delete
      erasure_complete:
        type: bool
        required: false
        description: Recorded. Present on a delete of a path whose last
          recorded labels include pii. False where the placement's backend
          keeps earlier versions of its entries or a remote was sent a
          version holding the entry, true only where neither holds. See
          Where an entry labelled pii is kept
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
        items: string
        required: false
        description: Witnessed. The identity ids of the persons whose decision
          applied the change — one, under this contract, taken from the
          decider's token. Present exactly when proposal is. Not a signature,
          unless statement is the decider's
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
      statement:
        type: ChangeStatement
        required: false
        description: Recorded. The signature of the person who moved the entry
          — the writer on a direct write, the decider on an applied proposal —
          present when they sent one and it verified. See The change statement
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
      scope:
        type: ScopeLevel
        required: false
        description: Recorded. On a change, the higher of the path's recorded
          scope and the scope the observed bytes declare. Absent when neither
          exists, and on a removal. See A change this service did not make
      labels:
        type: "[]string"
        required: false
        description: Recorded. The custom_labels the observed bytes carry under
          scope_metadata. Absent when they carry none, and on a removal
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

  EntryWrite:
    description: The body of PUT /v1/content/entry. One entry's new bytes, and
      the precondition they are written under
    fields:
      repository:
        type: string
        required: true
      path:
        type: string
        required: true
      bytes:
        type: string
        required: true
        description: The bytes to write, as standard base64 (RFC 4648 §4)
      if_match:
        type: string
        required: true
        description: The digest of the entry the write replaces, or the empty
          string where the caller believes the path holds nothing. Absent is
          refused with CONTENT_IF_MATCH_REQUIRED
      scope:
        type: ScopeLevel
        required: false
        description: The declared scope of the bytes — a level a person chose,
          or the one the bytes or the path's recorded scope give. Never filled
          in by default. At least the path's recorded scope and the scope the
          bytes declare, and present whenever either exists, or the write is
          refused with CONTENT_SCOPE_LOWERED. Absent where neither exists and
          nobody chose one. See Where a scope is declared
      statement:
        type: ChangeStatement
        required: false
        description: The writer's signature over the change this write would
          record. Without signer, which the service sets from the token

  EntryRemoval:
    description: The body of DELETE /v1/content/entry, carried as JSON as a
      write's is. One entry to remove, and the precondition it is removed under
    fields:
      repository:
        type: string
        required: true
      path:
        type: string
        required: true
      if_match:
        type: string
        required: true
        description: The digest of the entry the removal retires. Absent is
          refused with CONTENT_IF_MATCH_REQUIRED, and the empty string with
          CONTENT_PRECONDITION_NOT_APPLICABLE
      statement:
        type: ChangeStatement
        required: false
        description: The remover's signature over the change this removal would
          record. Without signer, which the service sets from the token

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
        description: The declared scope of the proposed bytes, as
          EntryWrite's is, and checked as EntryWrite's is. Absent on delete
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
      statement:
        type: ChangeStatement
        required: false
        description: The decider's signature over the change applying the
          proposal would record. Only on apply. Without signer, which the
          service sets from the token

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
        items: ContentProposal
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

  ContentLogEntry:
    description: One line of a repository's change log, stored as its RFC 8785
      bytes and a line feed, and chained as architecture/storage's Sealing a
      Chained Log requires. Holds exactly one payload, the one act names. Paths
      in it are plaintext (see What an entry covers)
    fields:
      seq:
        type: integer
        required: true
        description: 1 for the declare entry, then one more for each entry
      previous_digest:
        type: string
        required: true
        description: The SHA-256 of the previous stored line, lowercase hex. 64
          zeros on the declare entry
      recorded_at:
        type: timestamp
        required: true
      act:
        type: enum
        values: [declare, change, observe, key, succession, checkpoint]
        required: true
      declaration:
        type: LogDeclaration
        required: false
        description: Present when act is declare
      change:
        type: ContentChange
        required: false
        description: Present when act is change
      observation:
        type: ContentObservation
        required: false
        description: Present when act is observe. Never of state unknown
      key:
        type: LogKey
        required: false
        description: Present when act is key
      succession:
        type: LogSuccession
        required: false
        description: Present when act is succession
      checkpoint:
        type: LogCheckpoint
        required: false
        description: Present when act is checkpoint

  LogDeclaration:
    description: The first entry of a change log. What the repository was when
      it was declared, including everything a verifier needs to check a
      separation later
    fields:
      repository:
        type: string
        required: true
      scope_path:
        type: string
        required: true
      disposition:
        type: enum
        values: [establish, adopt]
        required: true
      custody:
        type: enum
        values: [exclusive, shared, opaque]
        required: true
        description: As demonstrated at declaration
      attestations:
        type: CustodyAttestations
        required: true
        description: As demonstrated at declaration
      store_ceiling:
        type: ScopeLevel
        required: true
        description: As derived at declaration. The least resource scope at
          which the log may be read
      self_decision_ceiling:
        type: ScopeLevel
        required: false
        description: As declared. Absent means no requester may apply their own
          proposal
      scope_floor:
        type: ScopeLevel
        required: false
        description: As declared. Every path's least recorded scope, so a
          verifier reads it with every scope the log records
      records:
        type: bool
        required: true
        description: As declared. Whether the repository may hold an entry
          labelled pii
      adoption:
        type: ContentAdoption
        required: false
        description: The census the declaration adopted against. Present on
          adopt
      adopted:
        type: list
        items: AdoptedEntry
        required: false
        description: Every entry the census found, in census order. Present on
          adopt. Each has provenance unknown

  AdoptedEntry:
    description: One entry a repository held when it was adopted
    fields:
      path:
        type: string
        required: true
      identity:
        type: ContentIdentity
        required: false
        description: Absent when the entry could not be read, which the census
          counted in unreadable
      scope:
        type: ScopeLevel
        required: false
        description: Recorded. The scope the entry's bytes declared when it
          was adopted. Absent when they declared none this service could read.
          See The recorded scope

  ChangeStatement:
    description: A person's signature over a change, by their record-signing
      credential. Sent with a write, a removal or a decision to apply, and
      recorded on the ContentChange when it verifies. See The change statement
    fields:
      signer:
        type: string
        required: false
        description: Recorded. The identity id whose statement this is — the
          token's identity_id. Set by the service and never taken from a
          request. Always present on a recorded statement
      signed_at:
        type: int64
        required: true
        description: When the person signed, in Unix seconds, UTC. Within 300
          seconds of the service's clock when received
      attestation:
        type: Attestation
        required: true
        description: The attestation binding the signing key to the signer's
          identity, with purpose sign-records (patterns/principal-identity)
      signature:
        type: string
        required: true
        description: ML-DSA-65 signature by the attestation's
          credential_public_key over the weblisk/content-change/v1 statement,
          base64url

  LogQuery:
    description: The query of GET /v1/content/repositories/{repository}/log.
      Paged by seq, not by an opaque cursor, because seq is part of what a
      verifier checks (Reading the log)
    fields:
      from:
        type: integer
        required: false
        description: The seq of the first line to return. 1 when absent, and
          at least 1. Beyond the tip returns no lines
      limit:
        type: integer
        required: false
        description: The most lines to return. 1000 when absent, at least 1 and
          at most 10000

  LogPage:
    description: The response of GET /v1/content/repositories/{repository}/log
    fields:
      repository:
        type: string
        required: true
      log:
        type: string
        required: true
        description: The log id
      tip:
        type: integer
        required: true
        description: The seq of the tip when the page was read
      lines:
        type: list
        items: string
        required: true
        description: The stored lines from seq from, in order, each its text
          without the line feed. Empty when from is beyond the tip
      next:
        type: integer
        required: false
        description: The seq to ask for next. Absent when the page ended at tip

  LogHead:
    description: The response of the log head and checkpoint routes. Names no
      path
    fields:
      repository:
        type: string
        required: true
      log:
        type: string
        required: true
        description: The log id — the SHA-256 of the declare entry's stored
          line
      seq:
        type: integer
        required: true
        description: The seq of the tip
      sealed_through:
        type: integer
        required: false
        description: The seq the latest checkpoint covers. Absent when no
          checkpoint has been issued
      unsealed:
        type: integer
        required: true
        description: How many entries after sealed_through no checkpoint
          covers yet, checkpoint entries excluded
      checkpoint:
        type: LogCheckpoint
        required: false
        description: The latest checkpoint. What a verifier keeps
      key:
        type: LogKey
        required: false
        description: The key entry that introduced the latest checkpoint's key.
          Its key_protection is how the service's registered key is protected,
          development-only included
      sealing:
        type: enum
        values: [active, paused]
        required: true
        description: paused while no log key can sign a checkpoint for this
          log, because none is live and the long-lived key cannot introduce
          another (architecture/storage, The log key). unsealed then counts
          what waits
      chain:
        type: enum
        values: [continuous, broken, unreadable]
        required: true
        description: What the service's own check of the log found, from its
          latest checkpoint to the tip (A log that does not verify). Not a
          verification of the whole log, which is a verifier's
      broken_at:
        type: integer
        required: false
        description: The seq where that check failed. Present exactly when
          chain is broken or unreadable
```

---

## Configuration

```yaml
content:
  backends:
    - name: <backend-name>       # what a placement names
      driver: <driver-name>      # the blueprint that specifies this backend, by
                                 # the driver name that blueprint declares
      root: <root>               # what every locator on it is confined to, in
                                 # the form the driver's blueprint declares
      options: {}                # in the shape the driver's blueprint declares.
                                 # Root, options and credentials are that
                                 # blueprint's, per Design Principle 6
      held_by: tenant|third-party  # who holds the store it reaches; see
                                 # Who holds a destination
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
  reverify_custody_interval: 24h # the store's, and each remote's
  remote_retry_interval: 15m     # how often a remote that lacks versions is
                                 # sent them, besides after each version
  checkpoint_interval: 15m       # how often a change log whose tip has moved
                                 # is sealed; 0 seals only at shutdown and on
                                 # request (architecture/storage)
  max_entry_bytes: 10485760
  scope:
    custom_labels: {}            # the labels the tenant registers, for every
                                 # repository this service holds, in
                                 # patterns/scope's Label Registration shape
```

`held_by` is stated where the host is named, and what it means is under
[Who holds a destination](#who-holds-a-destination).
No key declares a remote: see [Declaring a remote](#declaring-a-remote).

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
decide their own proposal in it, and no `scope_floor`. See
[Separation of duties](#separation-of-duties) and
[`scope_floor` covers what declares nothing](#scope_floor-covers-what-declares-nothing).

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
start after the first, and would be named `not_ready` on its lease for the rest
of its life for having worked.

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
repositories that were recorded, and the `checks` the service's lease carries
name it `not_ready`. A
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
    - boundary: Content Service → Remote. Crossed outward only. Nothing a
        destination holds is read back as content, history or truth
    - boundary: Content Service → Change Log. Only the service appends. The
        log is in its own state, reached through no content route and sent to
        no remote, and read only whole

  enforcement:
    - rule: Every change this service makes is one entry in its repository's
        change log, and a crash loses none of them
      mechanism: Reserve, write, read back, then append the entry and release
        the reservation in one record write. Reservations are settled before
        the service serves anything
    - rule: A change log is read whole or not at all
      mechanism: The storage proxy runs read at the highest scope the log
        records, the declare entry's store_ceiling and every change's scope.
        The route never filters, because a filtered log cannot be verified
    - rule: A person's signature covers the change this service records, never
        what a request says
      mechanism: The service rebuilds the weblisk/content-change/v1 statement
        from if_match and the digest of the decoded bytes, or from the proposal,
        and verifies it before anything is written, by a builder and verifier
        tested against that prefix's published vectors (protocol/identity,
        Fixed-Form Statements). A statement that fails refuses the request, and
        the change is never recorded unsigned instead
    - rule: Nothing in a change log is signed with a classical key, and no
        backend signature is evidence
      mechanism: Every key entry, checkpoint and change statement is ML-DSA-65.
        A classical signature makes no party signed. No commit is signed by
        this service (patterns/content-git)
    - rule: A key a console holds never makes a change signed
      mechanism: A change statement needs a sign-records credential the token
        names in record_keys, and never the credential its cid names. A hub
        records a key under one purpose only, and a console never holds a
        sign-records key (architecture/admin, console-credential-use)
    - rule: A change log verifies without this service
      mechanism: Sealed per architecture/storage, which lists what a verifier
        needs. The one fingerprint it brings is the service's registered key,
        from the tenant's service directory, and a rotation of that key is recorded by
        a succession entry both keys sign in every log that has an authority.
        Checking a person's statement needs what Verifying a log without this
        service adds
    - rule: Nothing is appended to a change log that does not verify
      mechanism: The service checks each log from its latest checkpoint at
        start, before settling reservations, and before each checkpoint. A
        broken log refuses every act that would append, with
        CONTENT_LOG_BROKEN, and still serves reads; the lease's checks name
        it not_ready
    - rule: A remote is declared only by a person who has seen what would
        leave, where it would go, and who holds that place
      mechanism: Two-step declaration; the first call returns the census and
        records nothing. The census digest binds every version that would
        leave, the destination, held_by and the claims made for it, so a
        census taken for one destination confirms no other. content:replicate
        and content:connect are both required and both person only
    - rule: Nothing is sent to a remote before the send can leave a signed
        egress record of what left
      mechanism: The Remote Send Flow holds every remote with held_reason
        egress-unrecorded, and sends nothing, until that record is specified
        (the gap under The Change Log)
    - rule: Nothing is sent to a remote that holds a reserved path, that
        nothing classified, or that is above the remote's ceiling
      mechanism: The census refuses each at declaration, an unclassified
        version unless a person records history_scope; the Remote Sender
        checks every version before it is sent and holds the first that fails,
        sending nothing after it
    - rule: A remote is never read from, and a diverged one is never
        overwritten
      mechanism: Remote Sender sends from the service's own record and asks a
        destination only whether it holds just what was sent; a destination
        holding anything else stops sending
    - rule: A remote holds nothing above the ceiling its destination
        demonstrated, and a plain one is capped, whoever holds its destination
      mechanism: The Derived Scope Ceiling derives every remote's ceiling from
        what was demonstrated, lowers it for a plain remote and for one that
        demonstrated no enumerable_principals; the census refuses what would
        leave above it, and the Remote Sender holds any later version above
        it. held_by is reported and bound by the census, and decides nothing
    - rule: A repository's ceiling is the lowest of every place its bytes live,
        and retiring a remote never raises it
      mechanism: ceiling is derived from the store and every remote confirmed,
        retired or not and whether or not it was sent anything, and from any
        copy the backend reports that no remote declares
    - rule: A remote's credential is the tenant's, for one destination
      mechanism: Created by the service at declaration, held through
        patterns/secrets, presented only at that destination, destroyed at
        retirement. Its secret part is never returned
    - rule: A remote is never configured
      mechanism: No configuration key declares one; the census digest a
        declaration needs cannot exist in a file
    - rule: A write, a removal or a proposal without a precondition is refused
      mechanism: Precondition Gate; if_match is required. The empty string is
        the precondition that nothing is there, and no value matches anything
    - rule: A write whose scope exceeds the repository ceiling is refused, never
        downgraded
      mechanism: Ceiling check before the storage proxy, publishing
        content.ceiling_exceeded
    - rule: A scope only rises, is never raised on a person's behalf, and is
        never lowered by any route
      mechanism: Write Flow step 3 refuses a declared scope below the path's
        recorded scope or the scope the bytes declare, no declared scope where
        either exists, and bytes that declare less than the recorded scope,
        with CONTENT_SCOPE_LOWERED. A removal leaves the recorded scope in
        place. The change records the scope it declared and where it came
        from, which a person's statement signs. An observation keeps the
        recorded scope whatever the bytes say. No operation declassifies
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
        RepositoryEstablishment; state establishing in the listing; the
        lease's checks name it not_ready
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
        declares either. This service honours them only on a pass addressed
        to it, which the orchestrator mints at the exchange for an operator
        token it judges live then (protocol/identity, The pass). A console
        gives no agent a person's token, narrowed or not
        (architecture/admin, console-credential-use). What the tenant cannot
        see, a person's credential used by software, is stated with the rule
    - rule: Only a person allows self-decision or sets a floor
      mechanism: A declaration carrying self_decision_ceiling or scope_floor
        requires content:decide as well as content:declare, both named by a
        pass, before it is recorded
    - rule: History a store kept is classified before it is adopted
      mechanism: An adoption whose census reports keeps_history carries a
        scope_floor, at or above the census's highest_scope, or is refused
        with CONTENT_SCOPE_UNDECLARED
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
        recorded as asserted; approved_by is reported as a signature only when
        the change carries the decider's verified statement. A token without
        identity_id cannot write, remove, propose or decide
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
  `not_ready` check on the service's lease forever, which is the honest
  reading of the situation.

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

- **Read a level only where it is declared.** The declaration in the bytes is
  a top-level `scope:` or `classification:` in a frontmatter block that begins
  on the first line. The same word further down, in a code fence, a table or
  quoted text, is text. Reading it would let any quoted example reclassify the
  document it sits in.

- **Compute `base` when asked, never store it.** An entry can change between
  one listing and the next, and a stored `current` is a claim about a moment
  that has passed.

- **Send a remote from the service's own record, never from the store.** A
  store under shared custody can be changed between the moment a version was
  recorded and the moment it is sent, and so can the store's own idea of where
  its copies go. What a remote receives is what the service recorded.

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

- **Hash the line you stored, not the object you meant.** An entry is
  canonicalised once, when it is written, and those bytes are what is chained,
  served and verified. Re-serialising an entry in order to hash it or serve it
  changes nothing only until two libraries format one number differently, and
  then every verifier holding the stored bytes finds a break the service
  cannot see.

- **Rebuild the statement, never accept one.** A request carries a signature,
  never the bytes it signs. The service builds those bytes from what it is
  about to record, so the only signature that verifies is one over exactly
  that change.

- **Settle reservations before serving.** A reservation left from a crash is
  a change that may have happened. Serving before settling it lets the
  reconciler, or the next write's precondition, meet those bytes first and
  record the tenant's own write as somebody else's.

- **A `declare` entry is one line however large the adoption.** It lists every
  adopted entry, because a file adopted and never changed is in the log
  nowhere else. Splitting it across entries would give the log a state in which
  it has begun and does not yet say what it began with.

---

## Verification Checklist

- [ ] A write submitted without `if_match` is refused with `CONTENT_IF_MATCH_REQUIRED`
- [ ] A write whose `if_match` differs from the stored digest is refused with both digests returned, and the stored bytes are unchanged
- [ ] The digest recorded after a write equals the digest of the bytes read back from the backend
- [ ] A full read pass over a corpus leaves every entry's digest unchanged
- [ ] A repository with no declared custody reports `custody: opaque` and a ceiling of `internal`
- [ ] An attestation declared in configuration but not demonstrated at verification resolves to `false`, and the ceiling reflects the demonstrated set
- [ ] A write declaring a scope above the repository ceiling is refused with `CONTENT_CUSTODY_CEILING_EXCEEDED` naming both levels, and the scope is not downgraded
- [ ] A write declaring `internal` whose bytes carry `scope: confidential` in their frontmatter is refused with `CONTENT_SCOPE_LOWERED` naming both levels and nothing is written; the same write declaring `confidential` is recorded at `confidential`
- [ ] A write declaring a scope below its path's recorded scope, or whose bytes declare a scope below it, is refused with `CONTENT_SCOPE_LOWERED`, and nothing is written
- [ ] A write or a proposal whose frontmatter carries a `scope:` or `classification:` that is not a `ScopeLevel` is refused with `SCOPE_INVALID_LEVEL` naming the value
- [ ] A document whose frontmatter carries `classification: restricted` and no `scope:` declares `restricted`; one carrying `scope: internal` and `classification: confidential` declares `confidential`
- [ ] A label in the service's `scope.custom_labels` configuration is applied to writes in every repository the service holds, at every `scope_path`, and a label only a domain's configuration registers is not applied to any
- [ ] Where the tenant registers `pii` with `maps_to: restricted`, a write declaring `confidential` whose bytes carry `scope: confidential` and `scope_metadata: {custom_labels: [pii]}` is refused with `CONTENT_SCOPE_LOWERED` naming `pii`; where it registers no `pii`, the same write is recorded at `confidential`
- [ ] A frontmatter `scope: pii` is refused with `SCOPE_INVALID_LEVEL`, whether or not `pii` is a registered label
- [ ] A `scope:` line inside a fenced block, or anywhere but a frontmatter block that begins on the first line, declares nothing
- [ ] An adopted entry whose bytes declare `scope: confidential` is recorded with that scope on the `declare` entry, and an out-of-band edit that removes the line is observed at `confidential`
- [ ] An entry with no recorded scope and no scope in its bytes reports no `scope`, never `internal`
- [ ] A write whose bytes carry `scope_metadata: {custom_labels: [pii]}` into a repository whose `records` is false is refused with `CONTENT_RECORDS_REPOSITORY_REQUIRED` and nothing is written; the same write into the `scope_path`'s records repository is recorded with `labels` `[pii]`
- [ ] A second declaration with `records: true` at a `scope_path` that has a records repository is refused with `CONTENT_REPOSITORY_EXISTS`, and one whose derived ceiling is below `restricted` with `CONTENT_CUSTODY_CEILING_EXCEEDED`
- [ ] Removing an entry labelled `pii` from a records repository whose backend keeps earlier versions, the git backend among them, records `erasure_complete: false` on its `ContentChange`, as does removing one that any remote was sent; only where the backend keeps none and no remote was sent it is `erasure_complete` true, and a removal of an entry not labelled `pii` carries no `erasure_complete`
- [ ] No configuration key declares a records repository
- [ ] After a removal of an entry recorded at `restricted`, a write creating the same path that declares `internal`, or declares no scope, is refused with `CONTENT_SCOPE_LOWERED`, and one declaring `restricted` is recorded at `restricted`
- [ ] In a repository with no `scope_floor`, a write that declares no scope, to a path with no recorded scope whose bytes declare none, records a `ContentChange` with no `scope` and no `scope_basis`, and the version it produces is counted `unclassified` by a remote census
- [ ] A write declaring `confidential` to a path with no recorded scope, whose bytes declare none, records `scope_basis` `chosen`; one whose bytes declare `scope: confidential` records `bytes`; one declaring the path's recorded scope, with bytes that declare less, records `recorded`
- [ ] No request lowers a path's recorded scope: every write, proposal and decision that would is refused with `CONTENT_SCOPE_LOWERED`, on an admin's pass naming `content:declassify` as on any other
- [ ] A remote census counts an earlier version of a path that no entry holds now at the scope the log recorded for it
- [ ] A proposal whose path's recorded scope rose above the proposal's scope after it was made is refused with `CONTENT_SCOPE_LOWERED` when applied, and stays `open`
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
- [ ] With no orchestrator URL configured, the service starts, serves `GET /livez` and `GET /readyz`, and does not exit
- [ ] With no orchestrator URL configured, every protected endpoint refuses with `401` and a structured `ErrorResponse`
- [ ] With no orchestrator URL configured, `GET /readyz` answers not ready and `GET /livez` live, and the service logs that no orchestrator is configured
- [ ] A declaration with no `disposition` is refused with `CONTENT_DISPOSITION_REQUIRED`, and nothing is recorded
- [ ] A declaration with `disposition: establish` over a placement holding entries is refused with `CONTENT_NOT_EMPTY`, and the entries are neither adopted nor touched
- [ ] A first declaration with `disposition: adopt` and no `if_match` is refused with `CONTENT_ADOPTION_UNSEEN`, returns a `ContentAdoption`, and records no repository
- [ ] A declaration with `disposition: adopt` whose `if_match` does not equal a freshly computed census digest is refused with `CONTENT_PRECONDITION_FAILED`
- [ ] A declaration re-using an id already declared at that `scope_path` is refused with `CONTENT_REPOSITORY_EXISTS`, and the declared repository is unchanged
- [ ] A declaration whose placement equals, contains or sits inside a declared repository's is refused with `CONTENT_PLACEMENT_DECLARED`
- [ ] Every entry present at adoption is recorded with provenance `unknown`, never `authored` and never `external`
- [ ] A declaration claiming attestations that are not demonstrated is recorded with the demonstrated set, and its ceiling follows the demonstrated set
- [ ] A declaration carrying no `custody` is recorded `opaque` with the `internal` ceiling, and the degradation is recorded
- [ ] A configured repository whose placement is not empty is refused, appears in `GET /v1/content/repositories` as a `DeclinedRepository`, and the `checks` the service's lease carries name it `not_ready`
- [ ] `content:declare` is required to declare a repository, and a caller holding only `content:write` is refused
- [ ] A declaration whose placement names a backend the service does not hold for that `scope_path` is refused with `CONTENT_BACKEND_UNKNOWN`, and the refusal does not disclose whether that name exists under another scope
- [ ] A declaration whose placement locator is absolute, carries a scheme or an authority, or contains a `..` segment is refused as written with `CONTENT_PATH_REFUSED`, and nothing is created anywhere
- [ ] A successful `establish` leaves a store that `GET /v1/content` lists as an empty page, that survives a restart of the service, and that a subsequent write succeeds against with no further step
- [ ] A successful `establish` leaves no entry at all in the store it created, and a census over it returns the digest of the empty set
- [ ] `establish` against a backend that cannot create is refused with `CONTENT_ESTABLISH_UNSUPPORTED`, no placeholder is written, and `adopt` against that same backend succeeds
- [ ] The declaration is durable with `state: establishing` before the adapter is asked to create anything, demonstrated by killing the service between the two and finding the record on restart
- [ ] A repository in `establishing` appears in `GET /v1/content/repositories` reporting `custody: opaque`, every attestation `false`, `ceiling: internal` and no `verified_at`; it serves no read, accepts no write, and the `checks` the service's lease carries name it `not_ready`
- [ ] A create that fails after the store exists answers `CONTENT_ESTABLISH_INCOMPLETE` with `store_created: true`, and no repository is reported as declared
- [ ] A repeated `establish` with identical arguments against a repository in `establishing` completes it, creates no second store, and increments `attempts`
- [ ] A repeated `establish` differing in `placement`, `custody` or `attestations` is refused with `CONTENT_REPOSITORY_EXISTS`, and the reserved declaration is unchanged
- [ ] A repeated `establish` with identical arguments against a repository already `declared` is refused with `CONTENT_REPOSITORY_EXISTS` and is not treated as a no-op
- [ ] A resumed `establish` whose store has since been written to is refused with `CONTENT_NOT_EMPTY`, and the entries are neither adopted nor touched
- [ ] A caller holding `content:declare` and not `content:establish` is refused `disposition: establish` and succeeds at `disposition: adopt` of a store whose census does not report `keeps_history`, with a declaration carrying neither `scope_floor` nor `self_decision_ceiling`
- [ ] A caller holding `content:declare` and not `content:decide`, a registered component's included, cannot adopt a store whose census reports `keeps_history`: confirmed with the census digest and without a `scope_floor` it is refused with `CONTENT_SCOPE_UNDECLARED`, with one it is refused with `FORBIDDEN`, and no repository is recorded either way
- [ ] A configured repository already `declared` with the same `id`, `scope_path` and `placement` is reconciled on every subsequent start — nothing is created, nothing is refused, and the lease's `checks` do not name it `not_ready`
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
- [ ] A `ProposalRequest` whose `action` is not `create`, `modify` or `delete`, whose `bytes` is missing on `create` or `modify`, whose `bytes` or `scope` is present on `delete`, or whose `bytes` is not valid base64, is refused with `INVALID_REQUEST`, and no proposal is recorded
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
- [ ] With `self_decision_ceiling` `confidential`, a requester applying a proposal that declares no scope on a path with no recorded scope, or a `delete` of a path with no recorded scope, is refused with `CONTENT_SEPARATION_REQUIRED`, and the proposal stays `open`
- [ ] A decision to apply by a person who is neither the proposal's `actor` nor its `on_behalf_of` records `separation` `independent`
- [ ] A person whose token's `identity_id` is a proposal's `on_behalf_of`, deciding to apply it in a repository with no `self_decision_ceiling`, is refused with `CONTENT_SEPARATION_REQUIRED` whatever the token's `sub` says
- [ ] The proposal's `on_behalf_of` may reject it with no `self_decision_ceiling` declared, and no `separation` is recorded
- [ ] A `ContentChange` from `PUT /v1/content/entry` carries no `on_behalf_of`, `approved_by`, `proposal` or `separation`
- [ ] A write or proposal whose body names an `actor` records the verified token's `identity_id`, never the named one and never the token's `sub`
- [ ] A write, removal, proposal or decision on a token that carries no `identity_id` is refused with `CONTENT_IDENTITY_REQUIRED`, and nothing is recorded
- [ ] A token that is not a pass and whose `cap` holds `content:write`, a registered component's or a channel's, is refused `PUT /v1/content/entry` with `FORBIDDEN`, as though it did not hold it, whether or not the request carries a `statement`; a person's operator token is refused there with `PASS_REQUIRED` whatever its `cap`, and a pass addressed to another component with `PASS_AUDIENCE_MISMATCH`
- [ ] The service's own manifest declares none of `content:write`, `content:decide`, `content:replicate`, `content:connect` and `content:declassify`, and its registration succeeds
- [ ] The manifest's `pass_routes` declare every route the guard table guards and no other, each with the capabilities its rows give it, `POST /v1/content/repositories/{repository}/remotes` with both `content:replicate` and `content:connect`, and `POST /v1/content/repositories` with `content:declare` and the three body requirements for `disposition: establish`, `scope_floor` and `self_decision_ceiling`; the directory entry the orchestrator publishes carries them unchanged
- [ ] A declaration carrying `self_decision_ceiling` from a caller holding `content:declare` and not `content:decide` is refused, and no repository is recorded
- [ ] A decider whose token's `cap` names `content:decide` and not `content:write` applies a proposal, and the write is recorded; the same token is refused with `FORBIDDEN` at `PUT /v1/content/entry`
- [ ] A declaration whose `self_decision_ceiling` is `critical` is refused with `CONTENT_SEPARATION_REQUIRED` and no repository is recorded; one at `restricted` is declared, and a requester's decision to apply a `critical` change in it is refused with `CONTENT_SEPARATION_REQUIRED`
- [ ] A declaration carrying `scope_floor` from a caller holding `content:declare` and not `content:decide`, a registered component's included, is refused with `FORBIDDEN`, and no repository is recorded
- [ ] A declaration carrying `self_decision_ceiling` or `scope_floor` is recorded only on a pass whose `cap` names both `content:declare` and `content:decide`; on a pass naming `content:declare` alone it is refused with `FORBIDDEN` and records no repository
- [ ] An adoption of a store whose census reports `keeps_history`, confirmed with the census digest and carrying no `scope_floor`, is refused with `CONTENT_SCOPE_UNDECLARED`, returns the census, and declares nothing; the same adoption carrying a `scope_floor` at or above the census's `highest_scope` is declared
- [ ] A census over a store holding an entry that declares no level and carries a label the tenant registers reports a `highest_scope` at least that label's `maps_to`, and an adoption carrying a `scope_floor` below it is refused with `CONTENT_SCOPE_LOWERED`
- [ ] Where the tenant registers `pii` with `maps_to: restricted`, an adopted entry whose bytes carry `custom_labels: [pii]` beside `scope: internal`, or beside no level, is recorded at `restricted` on the `declare` entry and reported with `ContentEntry.scope` `restricted`; an out-of-band edit that adds the label to an `internal` entry is observed at `restricted`; and a version from before adoption that carries the label, in a repository floored at `internal`, is classified `restricted` for a remote and held from a plain one with `held_reason` `above-ceiling`
- [ ] Where `pii` is registered with `maps_to: restricted`, a write whose bytes carry `custom_labels: [pii]` beside `scope: internal` is refused with `CONTENT_SCOPE_LOWERED` even when the change declares `restricted`, and one whose bytes carry the label and no level, declaring `restricted` on the change, is recorded at `restricted`
- [ ] A repository declared with `scope_floor` `internal` reports an entry whose bytes and path declare nothing at `internal`, records its floor on the `declare` entry, refuses a write declaring `public` or declaring none with `CONTENT_SCOPE_LOWERED`, and has no version a remote census counts `unclassified`
- [ ] An adoption whose census reports `highest_scope` `confidential` is refused with `CONTENT_SCOPE_LOWERED` when it carries `scope_floor` `internal`, and a declaration whose `scope_floor` is above its derived ceiling is refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`
- [ ] `ContentChange.version` is absent when the backend keeps no version marker
- [ ] A census over a placement whose backend's blueprint binds a `backend_report` covers that report in its `digest`, and an adoption whose store's report changed since the census is refused with `CONTENT_PRECONDITION_FAILED`
- [ ] A first `POST /v1/content/repositories/{repository}/remotes` with no `if_match` is refused with `CONTENT_REMOTE_UNSEEN`, returns a `RemoteCensus`, records no remote, creates no credential and sends nothing
- [ ] A remote declaration whose `if_match` differs from a freshly computed census `digest`, because a version was recorded between the two calls, is refused with `CONTENT_PRECONDITION_FAILED`
- [ ] A caller holding `content:replicate` and not `content:connect`, or `content:connect` and not `content:replicate`, is refused a remote declaration; a token that is not a pass is refused it whatever its `cap` holds
- [ ] A remote declaration whose destination backend has no `held_by`, or `held_by: third-party`, is confirmed like any other remote when everything that would leave is classified and at or below its ceiling, and its census reports `held_by: third-party`
- [ ] A plain remote whose destination demonstrates `shared` custody with all three attestations, and refuses anonymous read, has the ceiling `confidential`, whoever holds it; declaring it for a repository holding a `restricted` version is refused with `CONTENT_CUSTODY_CEILING_EXCEEDED` naming that version's path
- [ ] A remote declaration where an earlier version holds a path under `.weblisk` is refused with `CONTENT_RESERVED_PATH`, though no entry holds that path now
- [ ] A remote declaration against a destination that holds something this service did not send is refused with `CONTENT_NOT_EMPTY`, and nothing at the destination is changed
- [ ] A confirmed declaration against a destination that has not yet registered the credential answers `CONTENT_ESTABLISH_INCOMPLETE` carrying `credential`, the remote is `establishing`, and nothing has been sent; the same declaration repeated after registration completes it with no second credential
- [ ] Confirming, on an `exclusive` repository, a remote whose destination demonstrates neither its custody nor any attestation, and refuses anonymous read, records the remote `opaque` whatever its declaration claimed, and makes the repository's `ceiling` `public` and its `effective_custody` `opaque`, leaves `store_ceiling` `critical` and `custody` `exclusive`, and a write declaring `internal` is then refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`
- [ ] A remote whose destination can be read with no credential, or whose anonymous read could not be tested, has `ceiling` `public`
- [ ] A remote whose destination demonstrates `shared` custody with `attributable_writes` and `tamper_evident` but not `enumerable_principals`, and refuses anonymous read, has `ceiling` `public`
- [ ] Retiring a confirmed remote, whether or not it was sent anything, leaves the repository's `ceiling` and `effective_custody` unchanged, destroys its credential, and deletes nothing at the destination
- [ ] A remote confirmed while its destination is unreachable, and sent nothing, lowers the repository's `ceiling` at confirmation, and a write declaring a scope above the remote's ceiling is refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`
- [ ] Retiring a remote that is already `retired` changes nothing and returns it with the first `retired_by`
- [ ] A destination changed by somebody else makes its remote `diverged`; nothing is sent to it, nothing from it enters the repository, and once the destination again holds only what was sent the remote leaves `diverged` by itself
- [ ] No version is sent to any remote: a confirmed remote of a repository that holds a version is `behind` with `held_reason` `egress-unrecorded` and no `held_path`, unless step 3 of the Remote Send Flow held a version first, and its destination receives nothing
- [ ] A version above a remote's ceiling holds the remote `behind` with `held_path` naming it and `held_reason` `above-ceiling`, and no version recorded after it is sent
- [ ] A remote declaration confirming a census taken for another destination, or with other claimed custody, attestations or `history_scope`, is refused with `CONTENT_PRECONDITION_FAILED`, and so is one whose destination's backend changed `held_by` since the census
- [ ] A remote declaration whose census counts unclassified versions and that carries no `history_scope` is refused with `CONTENT_SCOPE_UNDECLARED`; the same declaration with a `history_scope` at or below the prospective remote ceiling, and the digest of a census taken with it, is confirmed and records `history_scope`
- [ ] An unclassified version recorded after a remote's census — an entry a person created in the store with no scope in its bytes, whether observed or not — holds the remote `behind` with `held_reason` `unclassified`, and nothing recorded after it is sent
- [ ] An out-of-band edit, after a remote's census, to an entry whose path has a recorded scope is classified at that scope, or at the higher scope its bytes declare, and holds no remote back when that is at or below the remote's ceiling, which is then `behind` with `held_reason` `egress-unrecorded`, never `above-ceiling`
- [ ] A version recorded after a remote was confirmed that holds a path under `.weblisk`, anywhere in what it holds, holds the remote `behind` with `held_reason` `reserved-path` naming that path; it is never sent, and nothing recorded after it is sent
- [ ] A backend's report of a copy of the store that no remote declares makes `effective_custody` `opaque`, lowers `ceiling` to `public`, as a remote declared at a place that demonstrated nothing would, and publishes `content.custody_degraded`; a write at `internal` is then refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`
- [ ] A copy the backend reported once and no longer reports stays in `reported_copies`; `effective_custody` stays `opaque` and `ceiling` stays `public`, and a write at `internal` is still refused with `CONTENT_CUSTODY_CEILING_EXCEEDED`
- [ ] No configuration key declares a remote, and a configuration file naming one declares nothing
- [ ] Every write, removal and applied proposal appends exactly one `change` entry to its repository's change log, and every observation of state `changed` or `removed` one `observe` entry; an observation of state `unknown` appends nothing
- [ ] A repository's first log entry has `act` `declare` and `seq` 1, records its `self_decision_ceiling`, its `scope_floor` and, on adoption, every entry the census found; the SHA-256 of its stored line is the `log` its `LogHead` reports
- [ ] Killing the service after an entry's bytes are written and before its `change` entry is appended, then restarting it, appends that `change` entry with provenance `authored` before anything is served, and records no `observe` entry for those bytes
- [ ] The `lines` of a `LogPage` decode to exactly the stored lines, and their `previous_digest` chain verifies with SHA-256 alone
- [ ] `GET /v1/content/repositories/{repository}/log` with no query returns at most 1000 lines from `seq` 1; a page that reaches the tip has no `next`; a `from` beyond the tip returns no lines; a `limit` above 10000, or a `from` or `limit` below 1 or not an integer, is refused with `INVALID_REQUEST`
- [ ] Each log route answers an `establishing` repository with `CONTENT_LOG_NOT_BEGUN` and one outside the caller's scope with `CONTENT_REPOSITORY_UNKNOWN`
- [ ] With the log key unavailable, `POST /v1/content/repositories/{repository}/log/checkpoint` appends nothing and is refused with `CONTENT_SEALING_PAUSED` carrying a `LogHead` whose `sealing` is `paused`
- [ ] `DELETE /v1/content/entry` reads an `EntryRemoval` from its JSON body, and, once `weblisk/content-change/v1` has test vectors, a `statement` in it is verified and recorded as a write's is
- [ ] A write whose read-back digest differs from the digest of its decoded bytes is refused with `CONTENT_WRITE_UNCONFIRMED`, and no `change` entry records it
- [ ] An `observe` entry becomes its path's recorded digest: a second read of the same changed bytes under shared custody appends nothing
- [ ] A caller whom the storage proxy refuses `read` at the highest scope the log records is refused the whole log, and is never served part of it
- [ ] `GET /v1/content/repositories/{repository}/log/head` names no path, and a caller holding `content:describe` and not `content:read` is served it
- [ ] No log entry holds an entry's bytes or a proposal's bytes
- [ ] Once `weblisk/content-change/v1` has test vectors, a write carrying a `statement` that verifies records it on its `ContentChange` with `signer` set to the token's `identity_id`, and an offline verifier rebuilding `weblisk/content-change/v1` from the entry verifies it
- [ ] Once `weblisk/content-change/v1` has test vectors, a write whose `statement` was signed over other bytes, another path or another `before` is refused with `CONTENT_STATEMENT_INVALID`, and nothing is written or recorded
- [ ] Once `weblisk/content-change/v1` has test vectors, a `statement` whose attestation has no `purpose`, or `purpose` `authenticate`, is refused with `CONTENT_STATEMENT_INVALID`
- [ ] Once `weblisk/content-change/v1` has test vectors, a `statement` whose `signed_at` is more than 300 seconds from the service's clock is refused with `CONTENT_STATEMENT_INVALID`
- [ ] Once `weblisk/content-change/v1` has test vectors, a `statement` whose attestation names an `identity_id` other than the pass's, or whose attestation's identity key is not the one whose fingerprint the pass's `identity_key` carries, is refused with `CONTENT_STATEMENT_INVALID`
- [ ] Through the admin gateway, a write, removal or decision on an unexpired operator token whose operator was removed, or whose credential was revoked, after it was minted is refused by the exchange with `OPERATOR_REVOKED` or `CREDENTIAL_REVOKED`, and one whose operator's role no longer carries the capability with `FORBIDDEN`; in each, this service is sent nothing and nothing is written
- [ ] A write, removal, decision or remote declaration on a pass whose `exp` has passed is refused with `TOKEN_EXPIRED`, and nothing is written, decided or recorded; one on an unexpired pass naming the capability is performed with the orchestrator unreachable, because this service asks the orchestrator nothing about a pass
- [ ] The audit entry for a request a pass carried names the pass's `identity_id` as `actor` and its `act.identity_id` as `via`
- [ ] Once `weblisk/content-change/v1` has test vectors, a `statement` signed by the credential key the token's `cid` names is refused with `CONTENT_STATEMENT_INVALID`, even where that key was also attested with `purpose` `sign-records`
- [ ] Once `weblisk/content-change/v1` has test vectors, a `statement` whose credential key is not one of the token's `record_keys` — never recorded at the hub, or revoked before the token was minted — is refused with `CONTENT_STATEMENT_INVALID`
- [ ] Once `weblisk/content-change/v1` has test vectors, a `statement` whose attestation's `not_after` is more than 90 days ahead of the service's clock is refused with `CONTENT_STATEMENT_INVALID`
- [ ] Once `weblisk/content-change/v1` has test vectors, a decision to apply that carries the decider's `statement` records it, and an offline verifier reports that approval `signed`; the same decision without one is reported `witnessed`
- [ ] Once `weblisk/content-change/v1` has test vectors, an offline verifier does not report `signed` a statement whose attestation is by one of the signer's retired identity keys and whose entry was recorded at or after that key's `retired_at`, and does report `signed` one recorded before it
- [ ] Once `weblisk/content-change/v1` has test vectors, a decision whose `statement` fails is refused with `CONTENT_STATEMENT_INVALID`, and the proposal stays `open`
- [ ] An offline verifier reports inconsistent a `change` entry recording `separation` `independent` whose `approved_by` is its `actor`, one recording `separation` `self` whose `scope` is above the `self_decision_ceiling` in the `declare` entry, and one recording `separation` `self` on a change with no scope — none declared, and on a removal no recorded scope for the path, the floor included
- [ ] Every signature in a change log is ML-DSA-65, and a signature on a commit in a version-controlled store appears nowhere in the log
- [ ] With the log key unavailable, writes still succeed, their entries are appended, and `LogHead.unsealed` counts them; once a log key can sign, the next checkpoint covers them all
- [ ] For every vector in [`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json) under `weblisk/content-change/v1`, the service, which verifies that statement and does not sign it, passes the test [`architecture/generation`](generation.md#published-test-vectors) gives for a component that verifies
- [ ] Once `weblisk/log-key/v1`, `weblisk/log-checkpoint/v1` and `weblisk/log-succession/v1` have test vectors, `POST /v1/content/repositories/{repository}/log/checkpoint` on a log whose tip has moved appends a `checkpoint` entry covering the tip, and on one whose tip has not moved appends nothing
- [ ] A service started over a change log whose lines after its latest checkpoint were altered settles no reservation in it, refuses writes, removals, decisions to apply, reconciles and checkpoints on that repository with `CONTENT_LOG_BROKEN` naming the `seq`, still serves its entries and its log, names it `not_ready` in its lease's `checks`, and reports `chain` `broken` with that `broken_at` in its `LogHead`
- [ ] Once `weblisk/log-key/v1`, `weblisk/log-checkpoint/v1` and `weblisk/log-succession/v1` have test vectors, rotating the service's registered key appends a succession entry to every change log that has an authority, and a verifier that brings only the key the tenant's service directory now lists verifies checkpoints sealed before the rotation
