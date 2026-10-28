<!-- blueprint
type: architecture
name: fabric
version: 3.0.1
requires: [protocol/types, protocol/identity, patterns/content-identity, patterns/scope, architecture/content, architecture/storage, architecture/enforcement, architecture/orchestrator]
platform: any
tier: free
adoption: opt-in
-->

# Weblisk Relationship Fabric

The tenant service that records what implements what — an append-only ledger of
claims, each made by somebody, at a moment, about both artifacts as they were
then.

## Overview

[`architecture/content`](content.md) holds the bytes a tenant governs.
[`architecture/storage`](storage.md) holds its records. Neither holds the thing
an auditor actually asks for: **the assertion that this procedure answers that
control, made by that person, against that version of both.**

This document defines the service that holds it. Its distinguishing concern is
**the claim**. A claim is not a property of either artifact — it changes on a
clock of its own, it can be confirmed, re-scoped or rejected without a byte of
either side moving, and it must survive both sides being edited afterwards
without quietly becoming a statement about something else.

Read downward, the ledger is implementation: this policy is answered by that
procedure, which is served by that component. Read upward it is assurance: this
control is met, and here is who said so and what they were looking at. Those are
the same edges traversed from opposite ends, which is why an edge is stored once
and is reachable from either.

> **Scope boundary:** this file defines the **ledger contract and the assertion
> model**. What sorts of thing may be related, and which relations are
> meaningful between them, are declared in
> [`schemas/kinds.md`](../schemas/kinds.md) and are not restated here. Digest
> semantics remain [`patterns/content-identity`](../patterns/content-identity.md).
> Custody remains [`architecture/content`](content.md). No backend is named —
> [`architecture/storage`](storage.md) Design Principle 6 governs here unchanged.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=3.0.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category, retryable]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, via, action, target, status]
        # pass_routes is how the admin gateway learns which of these routes a
        # person's request may reach and what each needs. See Registration
        # and Standalone Operation
        - name: AgentManifest
          fields_used: [name, capabilities, pass_routes]
        - name: PassRoute
          fields_used: [method, path, capabilities]
        - name: Capability
          fields_used: [name, resources]
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: LeaseRenewal
          fields_used: [ready, checks]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.14.4 <4.0.0"
    bindings:
      types:
        # type and aud say a person's request reached this service on a pass
        # addressed to it, the only token fabric:attest counts on; cap is what
        # it may use; identity_id names who acted on an entry, never sub; act
        # names the gateway that carried it
        - name: WLToken
          fields_used: [type, aud, act, cap, identity_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/content-identity
    version: ">=1.2.0 <2.0.0"
    bindings:
      types:
        - name: ContentIdentity
          fields_used: [algorithm, digest, size, projection]
        - name: VersionedReference
          fields_used: [target_id, target_version, recorded_at, recorded_by]
        - name: StalenessVerdict
          fields_used: [state, recorded_digest, current_digest]
      behaviors:
        - name: content-digest
        - name: reference-with-version
        - name: staleness-evaluation
        - name: read-without-mutation
        - name: digest-spelling
        - name: projection-digest
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/scope
    version: ">=2.0.0 <4.0.0"
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

  - blueprint: architecture/content
    version: ">=2.22.10 <6.0.0"
    bindings:
      types:
        - name: ContentEntry
          fields_used: [path, identity, scope, modified_at, provenance]
        - name: ContentRepository
          fields_used: [id, scope_path, custody, effective_custody, attestations, ceiling]
        - name: CustodyAttestations
          fields_used: [enumerable_principals, attributable_writes, tamper_evident]
        - name: ContentObservation
          fields_used: [repository, path, recorded_digest, current_digest, state, observed_at]
        - name: AccessStatement
          fields_used: [repository, access_complete]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/storage
    version: ">=1.0.0 <3.0.0"
    bindings:
      behaviors:
        - name: durable-records
        - name: concurrent-access
        - name: cursor-pagination
        - name: retention
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/enforcement
    version: ">=2.0.0 <4.0.0"
    bindings:
      types:
        - name: ViolationRecord
          fields_used: [boundary, agent, operation, violation_type, scope_required, scope_actual, detail, severity]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/orchestrator
    version: ">=2.15.0 <5.0.0"
    bindings:
      behaviors:
        # What a pass this service accepts rests on. See This service honours
        # fabric:attest only on a pass
        - name: token-exchange
          usage: Relied on, never called here. Every pass this service accepts was minted by the exchange, for an operator token the orchestrator judged live then, carrying no capability the person could not use then
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Requirements

Each requirement is a part of this file, named in the id grammar of
[`schemas/names.md`](../schemas/names.md):
`requirement://weblisk/architecture/fabric:<id>`. Every other file that needs
one of these facts cites it by that name and does not state it again.

```yaml
requirements:
  - id: reach-max-depth
    level: must
    value: 10
    text: A reach walks at most 10 hops from each node it starts at, in either
      direction. Reaching the bound is reported on the answer's completeness,
      never as nothing further. A caller may ask for less and never for more.
    refs: [Impact, AnswerCompleteness]
  - id: adoption-follows-credential-layer
    level: must
    text: This component is opt-in until the credential layer (identity,
      credential, grant) exists in the tenant. From then on it is required in
      every tenant the CLI generates. Until then no run statement is signed with
      a person's identity key to make up for the missing service credential.
  - id: declared-at-write-time
    level: must
    text: What a generation run wrote, and what each output was made from and
      claims to implement, is declared by that run's statement when the files
      are written, and reaches the ledger through the generation-statements
      producer. No producer infers afterwards an edge a statement declares.
  - id: statements-ingest-once
    level: must
    text: The generation-statements producer ingests every run statement it has
      not seen, and ingesting the same statements again appends no entry.
  - id: entries-name-their-run
    level: must
    text: An entry appended from a run statement names that run by id and
      statement digest, and the identity the run acted on behalf of. Run facts
      (tool, model, prompt) stay in the statement.
  - id: observed-connections
    level: must
    text: What the tenant connects to is recorded from what its own services
      observe, through the observer producers this file declares, never from a
      settings file.
  - id: no-content-writes
    level: must
    text: No fabric write path reaches a content write operation. The fabric is
      a client of the content service for identity and listing only.
  - id: reach-by-diff
    level: must
    text: A reach may start from a diff between two versions of one ref, and
      then starts at each changed, added or retired part, and at nothing else.
    refs: [Impact]
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Fabric Service                                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Endpoint Resolver              (one, for all)     │  │
│  │  - reference → NodeRef, before anything is written │  │
│  │  - fills Kind and Source only; never the id,       │  │
│  │    the anchor or the cited version                 │  │
│  │  - two sources answering is no answer              │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Assertion Gate                                    │  │
│  │  - which actor may set which status                │  │
│  │  - a Claim carries no status field at all          │  │
│  │  - a person's decision is deferred to, not revised │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Ledger              (append-only, hash-chained)   │  │
│  │  - one log per scope; never per kind or relation   │  │
│  │  - exclusive lock, tip re-read under it, fsync     │  │
│  │  - producer run writes as one batch                │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Derivation            (nothing here is stored)    │  │
│  │  - health, coverage, gaps, impact, projection      │  │
│  │  - every answer carries its own completeness       │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Producer Registry                                 │  │
│  │  - partitions, input digests, watermarks           │  │
│  │  - what has never been scanned, stated as such     │  │
│  └────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────┘
                            │  Stat and List only — never Read
                            ▼
                 architecture/content
```

**Endpoint Resolver** turns a caller's reference into an endpoint before any
write. It is one implementation because four independent ones disagreed: a claim
that resolved its own endpoints landed beside another producer's record of the
same fact instead of on it, so a person's confirmation settled a rival copy.

**Assertion Gate** decides what an actor may say. It is structural rather than
procedural — the type a producer submits has nowhere to put a status — so a
producer cannot express confirmation even by mistake.

**Ledger** is the only thing in this component that persists. Everything else is
computed from it on demand.

**Derivation** answers questions by folding the log. It writes nothing, which is
what makes every answer safe to recompute and impossible to leave stale.

**Producer Registry** is what separates *nothing was found* from *nothing ever
looked*. Without it a coverage figure of zero is unattributable, and an
unattributable zero reads as a finding.

---

## Responsibilities

### Owns
- The relationship ledger — one append-only, hash-chained log per scope
- The claim contract: what a claim is about, and what makes two claims the same
  claim
- Endpoint resolution: one reference-to-endpoint answer for every write path
- The assertion model: which actor may set which status, and the deferral rule
  that protects a person's decision from a producer
- Derived health, coverage, gaps, impact and the byte-stable projection
- The completeness statement attached to every answer
- Producer registration, partitions, input digests and watermarks
- Retiring and re-anchoring a relationship whose content moved

### Does NOT Own
- What sorts of thing exist, and which relations are meaningful between which
  of them (owned by [`schemas/kinds.md`](../schemas/kinds.md); a relation
  asserted outside that declaration is a producer fault, not a new relation)
- Digest semantics, staleness comparison and retirement (owned by
  [`patterns/content-identity`](../patterns/content-identity.md))
- Content bytes, paths, custody classification and the access decision on
  content (owned by [`architecture/content`](content.md) and
  [`architecture/enforcement`](enforcement.md))
- The audit log (owned by the orchestrator, per
  [`architecture/storage`](storage.md)) — the ledger is a separate chain, for
  reasons stated under Design Principle 6
- Classification — deciding a document's kind is one question with one
  implementation, and this is not it
- Regeneration. A stale edge is a review, never a rebuild
- Producer logic. What a scanner looks for is the producer's; this owns only
  how its claims are recorded and retired
- Cross-tenant relationships, which are federation and are not this

---

## Endpoints

| Method | Path | Operation | Auth | Capability | Purpose |
|--------|------|-----------|------|------------|---------|
| POST | /v1/fabric/sync | Sync | yes | `fabric:produce` | A producer states its full current view for one partition; what it no longer sees is retired |
| POST | /v1/fabric/observations | Observe | yes | `fabric:observe` | Report one relationship incrementally. Withdraws nothing, ever |
| POST | /v1/fabric/attestations | Attest | yes | `fabric:attest` | A person asserts a relationship themselves |
| POST | /v1/fabric/decisions | Decide | yes | `fabric:attest` | A person judges a relationship already recorded |
| POST | /v1/fabric/relocations | Relocate | yes | `fabric:attest` | Re-anchor a confirmed relationship whose content moved. No destination is accepted |
| GET | /v1/fabric/edges | Touching | yes | `fabric:read` | Live relationships with either end at a node, cursor-paginated |
| GET | /v1/fabric/reach | Impact | yes | `fabric:read` | Everything reachable from a node, or from each changed part of a diff (`?diff=`), to the depth `reach-max-depth` bounds, in both directions |
| GET | /v1/fabric/answers | Coverage | yes | `fabric:read` | What answers a criterion, what it rests on, and what is unanswered |
| GET | /v1/fabric/lineage | History | yes | `fabric:read` | Every entry ever recorded for one relationship, in order, with each actor |
| GET | /v1/fabric/projection | Graph | yes | `fabric:read` | The byte-stable graph of the live ledger |
| GET | /v1/fabric/chain | Verify | yes | `fabric:read` | Verify the hash chain over a range of sequence numbers |
| GET | /v1/fabric/producers | Producers | yes | `fabric:read` | Producers in scope, their partitions, watermarks and last run |
| GET | /livez | Livez | no | | Liveness, for the supervisor that restarts the service. Served with or without an orchestrator |
| GET | /readyz | Readyz | no | | Readiness, for the supervisor waiting on its start. Served with or without an orchestrator |

**On the operation names.** `Sync`, `Observe`, `Attest`, `Decide` and
`Relocate` echo their paths, which
[`schemas/architecture.md`](../schemas/architecture.md) discourages. They are
kept because they are not path words that happen to be verbs — they are the
assertion vocabulary, the distinction between them is the whole authority model,
and renaming one to avoid the echo would give the same act two names in one
system. The rule exists so a generator has a stable name to derive symbols
from; these are the most stable names available.

> **Gap — no route serves the kinds declaration this service judges by.** A
> claim whose relation or pair of kinds [`schemas/kinds.md`](../schemas/kinds.md)
> does not declare is skipped and reported as a producer fault
> (`FABRIC_RELATION_UNDECLARED`). Nothing records which revision of that
> declaration a tenant's fabric holds, and no route, here or at any other
> component, returns it, so a client classifies with whatever copy it carries.
> Where the two differ, one file is two nodes depending on which side asked,
> the fault `schemas/kinds.md` rule 7 forbids, carried across the wire. Which
> component serves the declaration, at which route, and under what capability
> are not specified.

---

## Interfaces

```yaml
interfaces:
  endpoints:
    - path: /v1/fabric/sync
      methods: [POST]
      description: A producer's full view of one partition. Claims it no longer
        makes are retired, bounded by (producer, scope, partition)
      served_by: fabric-service

    - path: /v1/fabric/observations
      methods: [POST]
      description: One relationship, reported incrementally. Nothing arriving
        here can retract itself
      served_by: fabric-service

    - path: /v1/fabric/attestations
      methods: [POST]
      description: A person asserting a relationship, confirmed or rejected
      served_by: fabric-service

    - path: /v1/fabric/decisions
      methods: [POST]
      description: A person judging a relationship already on the ledger
      served_by: fabric-service

    - path: /v1/fabric/relocations
      methods: [POST]
      description: Repair the address of a confirmed relationship whose content
        moved. The caller names the relationship, never the destination
      served_by: fabric-service

    - path: /v1/fabric/edges
      methods: [GET]
      description: Live relationships touching a node, cursor-paginated, each
        with derived health
      served_by: fabric-service

    - path: /v1/fabric/reach
      methods: [GET]
      description: Bounded traversal from a node in both directions, or, with
        diff=<ref>@<a>..<b>, from each part that differs between two versions
        of one ref. See Reach from a diff
      served_by: fabric-service

    - path: /v1/fabric/answers
      methods: [GET]
      description: What answers a criterion, with the completeness of the answer
      served_by: fabric-service

    - path: /v1/fabric/lineage
      methods: [GET]
      description: The full recorded history of one relationship
      served_by: fabric-service

    - path: /v1/fabric/projection
      methods: [GET]
      description: A byte-stable graph of the live ledger, recomputable by a
        reader holding the content
      served_by: fabric-service

    - path: /v1/fabric/chain
      methods: [GET]
      description: Hash chain verification over a sequence range
      served_by: fabric-service

    - path: /v1/fabric/producers
      methods: [GET]
      description: Registered producers, their partitions and watermarks — what
        has been scanned and what never has
      served_by: fabric-service

  methods:
    - name: ResolveEndpoint
      signature: (reference, scope) → NodeRef
      description: The one place a reference becomes an endpoint. Fills kind and
        source only; refuses rather than guessing between two sources
      called_by: [fabric-service]

    - name: Sync
      signature: (producer, scope, partition, [RelationshipClaim]) → SyncResult
      description: Record a producer's full view for a partition and retire what
        it no longer claims within it
      called_by: [agents, gateway]

    - name: Observe
      signature: (observer, scope, RelationshipClaim) → RelationshipEdge
      description: Record one incremental claim. Retires nothing
      called_by: [agents, gateway]

    - name: Attest
      signature: (actor, scope, RelationshipClaim, status) → RelationshipEdge
      description: Record a person's own assertion at confirmed or rejected
      called_by: [gateway]

    - name: Decide
      signature: (actor, RelationshipIdentity, status, note) → RelationshipEdge
      description: Record a person's judgement on an existing relationship
      called_by: [gateway]

    - name: Relocate
      signature: (actor, RelationshipIdentity) → RelocationResult
      description: Find where the cited content now lives, re-read it, retire the
        old record with a note, and assert the new address
      called_by: [gateway]

    - name: Touching
      signature: (NodeRef, cursor, limit) → ([RelationshipEdge], next_cursor, AnswerCompleteness)
      description: Live relationships with either end at a node
      called_by: [gateway, agents]

    - name: Impact
      signature: (NodeRef | DiffStart, depth) → ([ImpactPath], AnswerCompleteness)
      description: Bounded, undirected traversal, never deeper than
        reach-max-depth. Transitive relationships are joined here and never
        stored. Started from a diff, it walks from each changed part only
      called_by: [gateway, agents]

    - name: Coverage
      signature: (criterion, scope) → CoverageAnswer
      description: What answers a criterion, what each answer rests on, and what
        could not be checked
      called_by: [gateway, agents]

    - name: History
      signature: RelationshipIdentity → [LedgerEntry]
      description: Every entry ever recorded for one relationship, in order
      called_by: [gateway, agents]

    - name: Graph
      signature: scope → Projection
      description: Build the projection from the live ledger. Byte-stable for an
        unchanged ledger
      called_by: [gateway, agents]

    - name: Verify
      signature: (scope, from_seq, to_seq) → ChainVerdict
      description: Recompute the chain over a range and name the first entry that
        does not follow
      called_by: [gateway, admin]

    - name: Producers
      signature: scope → [ProducerPartition]
      description: What is registered, what it partitions by, and where each
        watermark stands
      called_by: [gateway, agents]

  events:
    - topic: fabric.relationship.recorded
      direction: publish
      description: An edge was added or revised, carrying the scope, the
        partition and both node keys so a listener knows its blast radius

    - topic: fabric.relationship.withdrawn
      direction: publish
      description: An edge was retired, with the reason and, for a relocation,
        where the content went

    - topic: fabric.relationship.stale
      direction: publish
      description: An endpoint moved away from the version a claim cited. This
        asks for a review and never for a rebuild

    - topic: fabric.relationship.deferred
      direction: publish
      description: A producer's claim disagreed with a person's decision and was
        left alone

    - topic: fabric.chain.broken
      direction: publish
      description: An entry's chain digest does not follow its predecessor. An
        integrity fault, not an observation

    - topic: content.changed
      direction: subscribe
      description: An entry's identity changed. Mark the partitions that read it
        for re-derivation; regenerate nothing

    - topic: content.custody_degraded
      direction: subscribe
      description: A repository can attest less than it did. Recompute the
        completeness carried by every answer citing it
```

Every published topic sits under `fabric.`, which is the namespace this
component claims exclusively at registration. A topic outside it would be a
second component's to publish, and the orchestrator refuses the claim.

---

## Error Handling

**Each code's HTTP status follows its Category**, and a code is returned with
that status wherever this service refuses: `validation` 400, `policy` 403,
`enforcement` 403, `conflict` 409, `integrity` 409 and `io` 503. A code whose
behaviour is not a refusal, such as `FABRIC_ENDPOINT_UNREACHABLE`, is reported
and never returned as an error status. A code another blueprint registers,
such as `FORBIDDEN`, `PASS_REQUIRED` or `PASS_AUDIENCE_MISMATCH`, keeps the
status that blueprint gives it
([`protocol/types`](../protocol/types.md#errorresponse)).

| Code | Category | When | Behaviour |
|---|---|---|---|
| `FABRIC_REFERENCE_UNQUALIFIED` | validation | A reference names a path and no source, and more than one source in scope answers to it | Refuse. Name every candidate. Two sources answering is no answer |
| `FABRIC_RELATION_UNDECLARED` | validation | The relation, or the pair of kinds, is not declared in the kind taxonomy | Skip the claim and report it as a producer fault. A claim nothing can justify is worse than an absent one |
| `FABRIC_STATUS_NOT_ASSERTABLE` | policy | A producer or agent submitted a status only a person may set | Refuse. Confirmation records who vouches, not how certain a machine is |
| `FABRIC_DECISION_DEFERRED` | conflict | A producer's claim disagrees with an edge a person decided | Leave the edge alone, record the deferral, report it. Never revise |
| `FABRIC_VERSION_REQUIRED` | validation | A claim about a `versioned` artifact carries no cited version | Refuse. A claim with no version is a claim about nothing in particular |
| `FABRIC_ENDPOINT_UNREACHABLE` | io | The cited artifact could not be read from here | Health is `unreachable`. Never `broken`, never `current`, and never `gap` |
| `FABRIC_RELOCATION_AMBIGUOUS` | conflict | More than one artifact holds the content the edge cited | Refuse and name every candidate. Re-pointing evidence at an archive copy is worse than reporting a break |
| `FABRIC_RELOCATION_UNSEARCHABLE` | validation | The edge records no size, so the search cannot be pruned | Decline. The alternative is hashing a workspace to answer one question |
| `FABRIC_PARTITION_UNKNOWN` | validation | A sync named a partition the producer has not declared | Refuse the whole batch. Retirement is bounded by the partition, and an unknown one has no bound |
| `FABRIC_CHAIN_BROKEN` | integrity | An entry's chain digest does not follow its predecessor | Refuse further appends in that scope, publish `fabric.chain.broken`, and report the first entry that does not follow |
| `FABRIC_LEDGER_TRUNCATED` | integrity | The log's byte length decreased | Re-read in full and report. Never continue from an incremental parse |
| `FABRIC_SCOPE_MISMATCH` | policy | A claim's scope lies outside the caller's declared scope | Refuse with a `ScopeViolation`. Never narrow the claim to fit |
| `ENFORCEMENT_DATA_CONTRACT_VIOLATION` | enforcement | The claim's endpoints lie outside the agent's declared operational data contract | Refuse via the boundary proxy |

---

## Data Flow

### Producer Flow
1. A producer registers its name, its partition granularity and the scopes it
   covers
2. It asks which of its partitions have moved since its watermark; a partition
   whose recorded input digests are unchanged is skipped entirely — not scanned,
   not reconciled, no edges touched
3. For each remaining partition it submits its full current view as claims
4. The resolver turns each claim's references into endpoints, filling only the
   kind and the source
5. Each endpoint's version is resolved through the content service's identity
   lookup, which transfers no bytes
6. The gate records each claim as `inferred`; an edge a person decided is
   deferred to, not revised
7. Claims in that partition which the producer no longer makes are retired
8. The whole run is appended as one batch — one lock, one durability barrier —
   because a crash mid-batch leaves a valid prefix, and a producer's claims can
   be derived again by running it

### Person Flow
1. A person submits an assertion or a judgement, naming the relationship,
   through the tenant's admin gateway, which carries it here on a pass
   addressed to this service
   ([`protocol/identity`](../protocol/identity.md#the-pass))
2. A token that is not a pass is refused with `FORBIDDEN`, and an operator
   token with `PASS_REQUIRED`. A pass is refused with `FORBIDDEN` unless its
   `cap` names `fabric:attest`
   ([This service honours `fabric:attest` only on a pass](#registration-and-standalone-operation))
3. The resolver lands it on the same identity a producer's claim would reach, so
   the confirmation sits **on** the inference rather than beside it
4. The entry is appended alone. A producer's work can be re-derived; a person's
   act cannot, so it is never batched behind one
5. The entry records the person as its `actor` by the pass's `identity_id`,
   never by its `sub`, which is a name
   ([`protocol/identity`](../protocol/identity.md#payload-claims),
   `identity_id`). So does every attestation, decision and relocation, and an
   edge a person's act settles names them in `asserted_by` the same way

### Answer Flow
1. A caller asks what touches a node, what a criterion is answered by, or what a
   change reaches
2. The ledger is folded to the set of live edges in the scopes in view
3. Each edge's health is derived by comparing the version it cited against the
   artifact now; nothing is read from a stored flag
4. Transitive relationships are joined here. Only direct edges were ever stored
5. A clause-level edge reaches its document through a synthesised containment
   step, which is reported as synthesised so the path stays auditable
6. The answer carries its completeness: which producers contributed, which
   partitions have never been scanned, which endpoints were unreachable, and
   whether any repository in scope reported incomplete access

### Relocation Flow
1. An endpoint is found missing at its recorded address
2. Nothing is searched unless that has happened, and nothing is searched for an
   edge with no recorded size
3. Candidates are those entries whose size equals the size recorded on the edge.
   Identical content is necessarily identical in length, so this prunes exactly
   rather than heuristically and every possible match is still examined
4. Exactly one candidate resolves the address; two or more is refused
5. The destination is re-read before anything is written; a search may answer
   from a stored listing, a write never does
6. The old record is retired with a note naming where the content went, and a
   new one is asserted at the new address. It is not revised in place, because a
   record's lineage is computed from its endpoints

---

## Design Principles

1. **A claim is about a version, and the version is not its identity** — an edge
   MUST record the content identity of both endpoints as they were when the
   claim was made, and that identity MUST NOT form part of what makes two claims
   the same claim. Putting it in the key would mint a new record on every edit,
   which leaves the ledger no way to say the one thing it exists to say: this
   claim has not been reviewed against what the thing became.

2. **A path alone is never an identity** — an endpoint is a source and an
   artifact identity, and where the artifact carries a durable identifier of its
   own that identifier outranks the address. An unqualified reference that more
   than one source answers MUST be refused rather than filed against a guess. A
   coordinate that happens to be unique today is not a name.

3. **A derived value is never part of a key** — an artifact's kind is read off
   its address and its content, so a kind inside an identity means two faults at
   once: two classifiers make one file into two nodes, and re-declaring a
   classification rule silently re-keys relationships a customer already
   recorded. A kind whose name is unique only within a namespace keeps that
   namespace in its identity; the taxonomy declares which is which, and nothing
   here switches on a kind.

4. **Confirmation records who vouches, never how certain a machine is** — a
   status of `confirmed` MUST be reachable only by a person. Machine certainty
   is a separate, numeric field, and a recorded derivation is an inference of the
   highest confidence rather than a confirmation. The type a producer submits
   MUST carry no status field, so this is structural and not a convention
   somebody has to remember.

5. **Derived, never stored** — health, coverage, gaps and reachability MUST be
   computed at read time. A stored staleness flag is a cache of a fact about
   other data and is wrong from the moment either side moves, which in a
   compliance product means confidently reporting cover that is not there. A gap
   is an absence, so nothing writes one and a gap cannot go stale.

6. **The ledger is an owned record under exclusive custody; what it cites is
   not** — see The Custody Question below. One consequence is normative here: the
   ledger MUST NOT share a chain with any other log. Two writers on one chain
   fork it, a fork is indistinguishable from tampering, and a compliance
   relationship and an audit entry do not have the same retention.

7. **A citation, never a copy** — an edge MUST record an artifact's address,
   identity and size, and MUST NOT record its content. A ledger holding the bytes
   becomes a mirror that answers around the content service's access decision,
   and a restricted document would be readable through a relationship to it. This
   is also what keeps the ledger compatible with erasure: a chained leaf commits
   to what it holds, and it holds no content.

8. **Never a confident zero** — every answer MUST state its own completeness. An
   empty result with no statement of what was scanned, what was skipped and what
   could not be read is a claim this service is not entitled to make. *Nothing
   was found* and *nothing ever looked* are different facts and only one of them
   is something for an organisation to act on.

9. **Verifiable without this service** — every judgement the projection reports
   MUST be recomputable by a reader holding the ledger and the content, using a
   published digest algorithm and ordinary tools. Capability lives in the
   platform; the platform MUST NOT be the trust anchor for its own output.

---

## The Custody Question

[`architecture/content`](content.md)'s distinguishing concern is that a content
repository may live on a share other people also write to. The fabric's is the
opposite, and the difference decides the shape of this component.

**The ledger is an owned record store under exclusive custody.** Nobody authors
an edge in a text editor; there is no second writer, and no legitimate
out-of-band change. That has three consequences, each of which is a rule rather
than an observation.

**There is no reconciliation here in the content service's sense.** That verb
answers *did somebody else change these bytes*, and converts an unexplained
change from an alarm into a recorded fact. Under exclusive custody the same
mechanism would reclassify real tampering as an ordinary external edit — which
is the inverse of the fault it exists to fix, and is why
[`architecture/content`](content.md) forbids running its reconciler where custody
is exclusive. A ledger entry that does not chain is an integrity fault and MUST
be reported as one.

The word is reused for a different act, and the collision has to be named or it
will be conflated: this component's `Sync` is a **producer** restating its full
current view so that what it has stopped seeing can be retired. It is a claim
about the world, not about the store, and the two must never be merged into one
endpoint.

**Custody flows from the endpoint to the claim, and never the other way.** The
ledger being exclusive says nothing about what may be asserted through it. An
edge citing content in a repository whose `effective_custody` is `shared` or
`opaque` — its store's custody, or any remote's
([`architecture/content`](content.md#effective-custody)) — inherits that
repository's limits: every answer quoting it MUST carry that access is
incomplete, and that flag MUST survive into every export and evidence package
downstream. A consumer that drops it has turned a qualified statement into a
false one.

**An artifact this installation cannot read stays in the ledger, and nothing is
claimed about its content.** That a policy cites a document is a fact about the
policy, recorded regardless of who can open the document. Its health is
`unreachable` — not `broken`, which reports evidence as destroyed when the file
is intact, and not `current`, because nothing was read and so nothing was
verified. Coverage counts an unreachable answer as needing review. A control
reported as met on the strength of a document nobody here could open is the
dashboard lie in its purest form, and the access decision remains the holder's
to make at the moment of asking.

### Why this is its own component

Three options were weighed: a capability of the content service, a capability of
the orchestrator, and a component of its own. It is a component of its own, and
a **client** of the content service for every byte-level fact it needs.

| | Content service | Fabric service |
|---|---|---|
| Custody | shared by design — a second writer is expected | exclusive — a second writer is a fault |
| A difference it did not make | an ordinary recorded observation | an integrity fault |
| Retention | the content's own | none; a compliance relationship is permanent |
| Subjects | a confined tree of bytes | also controls, providers, integrations, components and runs, none of which it can read or hash |
| Adoption | a tenant that governs text has one | opt-in until the credential layer exists, then required (`adoption-follows-credential-layer`) |

Folding the ledger into the content service would put two contradictory trust
models in one process, and the contradiction would be internal rather than
visible at a boundary. It would also make an opt-in surface a conditional half
of a component that is not — which is the declared-rather-than-inferred problem
created deliberately. And it would ask a service whose subject is a confined tree
of bytes to be the home of claims about an external provider's configuration,
which it cannot read, hash or own.

Folding it into the orchestrator is worse: the orchestrator is deliberately small
and holds no application data, and a ledger behind the trust anchor's identity
would put a component's state where every other component must trust it blindly.

**As a client it reads nothing directly.** Version resolution uses the content
service's identity lookup, which returns an entry's identity without transferring
bytes, and relocation uses listing plus identity lookup for the same reason. The
fabric therefore needs no path onto a repository and holds no content credential
beyond the capabilities below. A component that needs the filesystem of the thing
it describes is not a client of it.

> **Not settled here.** How a tenant that adopts this surface causes it to be
> built is a question about how a tenant declares its component set, and it is
> not this blueprint's to answer. `adoption: opt-in` states that a deployment
> without it is correct rather than unfinished; it does not by itself make the
> surface reachable, because a generation target resolved from a fixed list is
> a specification living in the tooling. That is the precondition, and it is
> named rather than assumed.

**When opt-in ends.** The fabric becomes required in every tenant the CLI
generates once the credential layer — identity, credential, grant — exists
there (`adoption-follows-credential-layer`), because the run statements it
ingests are signed by the tenant's `generation` service credential, and before
that credential exists there is nothing to sign them with but a person's own
identity key, which never signs one. Until then the header says `opt-in`, and
that is the honest value rather than an unfinished one.

### Where the content service is

Being a client of the content service means the fabric resolves that service's
address out of the service directory, and a tenant's components may
legitimately be on different hosts. So this is the first place in the corpus
where one component presents a credential across a host boundary, and it is
worth working through rather than assuming.

The directory is the orchestrator's as read from the fabric's anchor by
[`GET /v1/services`](../protocol/spec.md#get-v1services), or as pushed to the
fabric's `POST /v1/services` with a signature that verifies under the
orchestrator's key ([`protocol/spec`](../protocol/spec.md#post-v1services),
the signed push). Either way it says only that the orchestrator published the
address a registrant claimed, never that the address is the tenant's
([`architecture/orchestrator`](orchestrator.md#what-the-directory-attests-and-what-it-does-not)).
What keeps the fabric's credential in bounds is therefore the table below,
which never sends it off the anchor's host whoever claimed the address. On
that host a registered address can still choose the port, and a listener there is the
same-host residual the threat model records
([`architecture/threat-model`](threat-model.md#residual-risk-register)).

The fabric's **anchor** is the orchestrator address it was configured with. It
holds `content:read` and `content:describe`, and it calls identity lookup and
listing. Nothing about those two facts says where the content service is.

| The directory says | What the fabric does |
|---|---|
| Content is on the anchor's host | Call it with its own registered credential. The ordinary single-host tenant, unchanged |
| Content is elsewhere, `address_provenance: self-asserted` | **Refuse.** No credential is sent. The repository is `unreachable` and every answer citing it says which fact was missing — the tenant has not declared that address |
| Content is elsewhere, `address_provenance: declared` or `verified` | The address is authorised, and the fabric's own credential is still bound to its anchor. It needs a grant naming that address for those two capabilities, and it has no way to obtain one |

The last row is the honest state, and the reason is worth stating because the
obvious fix is wrong. `POST /v1/channel` issues exactly the grant required —
an orchestrator signature over `target_url` and `target_pub_key`, with a scoped
token that expires — but it requires `agent:message`, and **the fabric MUST NOT
declare `agent:message` in order to reach the content service.** That
capability is the whole agent mesh. Taking it to solve an addressing problem
would widen this service's declared reach from two content verbs to every
component in the tenant, and the widening would be invisible: it would look
like a routing detail and read, at the registry, as a general-purpose
messenger. The gap is in the grant path, and it is named where the grant path
lives — [`architecture/orchestrator`](orchestrator.md#presenting-a-credential-to-a-component).

**Until it is closed, a tenant that places its content service on another host
has a fabric that cannot resolve versions, and that is reported rather than
worked around.** The model for reporting it already exists here and needs no
addition: an endpoint this installation cannot read is `unreachable`, not
`broken` and not `current`, and coverage counts it as needing review. A remote
content service is the same condition arrived at by a different route — nothing
was read, so nothing is claimed — and it lands on the one status that says so.

The alternative, which must not be taken, is for the fabric to follow the
address with its anchor credential because the directory names it. That would
put a credential holding `content:read` over a tenant's whole governed corpus
onto a host chosen by whatever last registered under that name, or by whatever
last pushed the fabric a directory. Even read from the anchor, the directory
says only that this orchestrator accepted the registration; it was never a
statement that the tenant chose the address.

---

## The Claim Model

### What makes two claims the same claim

A claim's identity is **both endpoints, the relation, and the scope**, and
nothing else.

| Part | What it is | Why it is in the key |
|---|---|---|
| endpoint | source, artifact identity, and the anchor within it | a claim about clause 4.2 and a claim about the document are two legitimate claims, and collapsing them discards the only one an auditor can check |
| relation | the declared verb | *mentions* and *implements* are different claims about the same two things |
| scope | where the claim was made | the same two artifacts may be related differently in two projects |

And what is deliberately **not** in it: the kind, which is derived; the cited
version, which is what the claim was about; the confidence; the status; the
actor; and the time. Those are properties of the record, and a change to any of
them is a new entry about the same claim rather than a new claim.

An artifact identity follows the declaration for its kind — source and path for a
file, a namespaced identifier for a criterion, a durable identifier for a
provider, an integration or a component. Where the content carries an identifier
of its own, that is the identity and the address travels beside it as a mutable
attribute, refreshed on every claim. This is what makes a move cost nothing for
an identified artifact: the key does not contain the address, so the next claim
lands on the same record. Any comparison asking *has this been re-pointed* MUST
therefore compare addresses and not keys.

### Who may assert what

| Path | Who uses it | Status it may set |
|---|---|---|
| `Sync` | a producer the platform runs, stating its full view | `inferred` only |
| `Observe` | an agent or integration reporting incrementally | `inferred` only |
| `Attest` | a person asserting a relationship themselves | `confirmed` or `rejected` |
| `Decide` | a person judging an existing relationship | `confirmed`, `rejected` or `retired` |

A producer may revise only what it last asserted. Anything a person decided is
reported as deferred and left untouched — and the same rule that stops a scan
overruling a compliance lead is what stops it repairing their record, which is
why an explicit relocation exists at all.

A person's judgement also outranks the taxonomy. An inferred edge may be gated
on whether its kind counts toward coverage; a confirmed one may not, because a
classifier's guess is not evidence against somebody who put their name to a
claim.

An agent asserting on a person's behalf is a real requirement and is
deliberately absent: it is explicit, conditional, bounded by both the agent's
skills and that person's declared tolerances, and it is never a default. Until
that is specified, `confirmed` is reachable by a person and by nothing else.

### Sync and Observe answer different questions

`Sync` is a difference: a producer states everything it can currently see for a
partition, and what it has stopped seeing is retired. That is right for a
scanner the platform runs and whose whole view is cheap to restate.

`Observe` never withdraws. Something reporting over a connection knows one thing
at a time, and requiring it to restate its history so the ledger can diff would
make every reporter keep its own copy of the ledger. The cost is real and is
accepted rather than hidden: nothing arriving through `Observe` can retract
itself, so such a relationship is retired by a person or by the connection being
removed.

### Declared at write time

A generation run knows, when it writes a file, which requirements the file is
meant to implement, which requirements and mapping rules it was made from, and
which run made it. That is a declaration, and it is recorded as one
(`declared-at-write-time`): the run writes it into its **run statement**
([`schemas/run-statement.md`](../schemas/run-statement.md)), one immutable file
per run, and the `generation-statements` producer below carries it to the
ledger. A scanner that inferred the same edges from the generated code
afterwards would be a second record of one fact, and the weaker of the two.

The statement is the outbox. It is written on the first build, offline, with no
fabric running; when the fabric starts, the producer ingests every statement it
has not seen. Run facts — the tool, the model the backend reported, the prompt
digest — stay in the statement. An entry names the run by id and statement
digest (`entries-name-their-run`) and never copies them.

**Anchors on generated code.** An output is anchored by `symbol` only where its
language mapping ships a symbol extractor. Elsewhere the claim is about the
whole file, and every answer that rests on such a claim counts it in
`file_level_endpoints`, so a file-level answer is never read as a symbol-level
one.

### Producers this file declares

| Producer | Runs in | Operation | Partition | Relations | What each end cites |
|---|---|---|---|---|---|
| `generation-statements` | the tenant's generation service † | `Sync` | one run statement, by run id; its input digest is the statement's | `implements` (output to requirement), `generated_from` (output to requirement, mapping rule or control), `produced_by` (output to run), `verifies` (generated test to check) | the output's digest as the statement records it; the requirement's, rule's or control's projection digest |
| `integrations` | the tenant's integrations service † | `Observe` | — | `consumes` (component or agent to integration), `reached_through` (provider to integration) | the integration's connection record digest |
| `registry` | the orchestrator's service registry | `Sync` | one component | `deployed_as` (blueprint to component or agent), `hosted_by` (component or agent to provider) | the blueprint's digest at its resolved version; the component's manifest digest |
| `provider-configuration` | the tenant's integrations service † | `Sync` | one provider | `enforced_by` (policy, standard or procedure to provider) | on the provider end, the projection digest of its configuration as the provider reports it |

† **A precondition, not a service that exists.** No blueprint in this corpus
defines a tenant generation service or a tenant integrations service yet. A
producer marked † runs only in a tenant that runs that service, and is not built
in one that does not; until a blueprint defines the service, these rows say what
the producer asserts once it has somewhere to run, and nothing is observed or
synced in the meantime. The run statement's `builder` names the generation
service by ref for the same reason ([`schemas/run-statement`](../schemas/run-statement.md)).

Each is an ordinary producer: it registers its partitions, is skipped where its
input digests are unchanged, and asserts at `inferred` only. Ingesting the same
statements twice appends nothing (`statements-ingest-once`), because a
partition whose input digest is unchanged is skipped before any claim is
resolved.

**The provider end cites its configuration.** Because a provider's cited
version is the digest of its settings, an `enforced_by` edge reads `stale` when
those settings change: a person re-reads whether the provider still enforces the
policy, and nothing is rebuilt. A provider that reports no configuration is
cited with no version, and the edge reads `unversioned`, never `current`.

**What a statement does not prove.** A statement is signed by the tenant's
`generation` service credential, recording `on_behalf_of` the operator who
asked for the run, once the credential layer exists
(`adoption-follows-credential-layer`). Until then statements are unsigned and
the producer records each entry's run citation with `signed: false`; a
person's identity key never signs one in its place.

### Health

| Health | Means | The response it asks for |
|---|---|---|
| `current` | both ends are at the version the claim cited | nothing |
| `stale` | an endpoint changed since the claim was made | a person re-reads it |
| `moved` | an endpoint is gone from its address, and content matching the cited version is elsewhere | correct the address |
| `broken` | an endpoint no longer exists anywhere in scope | investigate |
| `unreachable` | the endpoint could not be read from here at all | connect the source, grant access, or accept it is unverifiable |
| `unversioned` | there is nothing to compare — the end cites no version: its kind declares none and it cites no projection digest | nothing |

`moved` is not a sixth coverage state and MUST NOT disturb the status. The
content matches what was confirmed byte for byte, so the confirmation still means
what it meant and there is nothing to re-judge — only an address to correct.
Asking somebody to re-read a document that has not changed a byte is how a
control comes to be ignored.

These map onto the staleness verdict the corpus already defines rather than
replacing it: `current` and `stale` are that verdict, `unreachable` is its
`unknown`, and `moved` and `broken` are facts about an address that a
single-reference verdict has no way to express.

**What an end is compared on is what it cites, not what its kind is.** An end
whose `cited_version` names a projection
([`patterns/content-identity`](../patterns/content-identity.md), projection-digest)
is compared on that projection's digest, recomputed from the end as it is now,
whatever its kind declares: a control on its text digest
([`schemas/standard.md`](../schemas/standard.md#outputs-cite-the-control-text-they-were-made-from)),
a requirement or mapping rule on its part's projection digest, a provider on the
projection of its reported configuration. Each reads `stale` when that
projection changes and `current` when only formatting around it did. An end
that cites the whole artifact is compared on its stored bytes. `unversioned` is
the honest answer for an end that cites nothing to compare — a kind that
declares no version, cited with no projection digest. Treating it as current
would be a claim nobody made.

### Where relationships do not live

**Not in a document.** A relationship changes on a clock of its own, so writing
it into either side would rewrite a file nobody edited — changing its content
identity, repudiating every signature on it, and doing so across the corpus at
once. It would also scatter one graph across every file it spans, so *what would
this change break* becomes a parse of everything.

**Not in a sidecar beside the document.** The same mistake in a second file.

**Not in a store per feature.** Four of those grew independently in one
implementation and none agreed; the view that read relationships read a different
store from the tool that wrote them.

This is stated as a prohibition rather than a preference because the design it
forbids was attempted, removed, and is attractive enough to be attempted again.

---

## The Ledger

**Append-only.** An entry is written once and never edited. A revision, a
retirement and a relocation are all new entries; the live state of a
relationship is the fold of its entries, and its history is all of them.

**Chained.** Each entry commits to the digest of its predecessor, so an entry
cannot be altered or removed without every later entry failing to follow. The
mechanism is the one [`architecture/storage`](storage.md) already specifies for
its own chained log — each entry stored as its RFC 8785 bytes and one line feed,
`seq` from 1, each `previous_digest` the SHA-256 of the line before without
its line feed — and what differs is the chain, not how it is computed, with one
difference of spelling: every digest here is written `sha256:<hex>`
([`patterns/content-identity`](../patterns/content-identity.md), digest-spelling),
the first entry's `previous_digest` included, where storage's own logs still
write bare hex.
[`vectors/fabric-ledger.json`](../vectors/fabric-ledger.json) is a worked chain
that a verifier checks with nothing but SHA-256 and an RFC 8785 canonicaliser.

**One log per scope, and by no other axis.** A project's growth cannot slow
another's queries or its first parse, unlinking a project is dropping a
partition rather than a scan across a global log, and tampering is localised and
independently detectable per scope. It MUST NOT be partitioned by kind or by
relation: every question worth asking crosses kinds, so that would turn the
common case into a fan-out over every partition.

**Durability is part of the contract, not an implementation detail.** An append
MUST take an exclusive lock over its log, re-read the chain tip **under that
lock**, and reach durable storage before it is reported as written. Reading the
tip before taking the lock lets a second process interleave, and the result is a
forked chain — which is indistinguishable from tampering, and is exactly what
[`architecture/storage`](storage.md) requires a mutual exclusion primitive to
prevent.

**A producer run is one batch; a person's act is not.** A batch takes one lock
and pays one durability barrier, and a crash part way through truncates the
chain rather than corrupting it, leaving a valid prefix. A producer's claims can
be derived again by running it; a person's cannot, so each is written alone and
survives on its own.

**Reading may be incremental, and the invalidation key is the log's byte
length.** Nothing rewrites the log, so its length increases on every write and on
no other occasion: unchanged length means unchanged contents, for another
process appending as much as for this one. A partial final line caught mid-append
MUST be left for the next read rather than parsed and skipped permanently, and a
log that has **shrunk** is outside this contract — it MUST be re-read in full and
reported, never continued from.

**Sequence numbers make catching up a suffix read.** Every entry carries one, so
*what has changed since N* is answered by reading forward from N. A subscriber
that stopped, crashed or was added catches up from its watermark and never by
re-reading history.

### Two ledgers, and that is correct

Packs, standards catalogues, templates and domain material are given freely, and
live in repositories outside any tenant, never resident in an installation
([`architecture/content`](content.md#repositories-outside-a-tenant)). Each
tenant keeps a ledger over its own. No tenant keeps one over what lies outside
every tenant, so a ledger over those repositories is a cache, as content defines
one: whatever reads them may keep it, it holds only what producers derived from
them — every claim `inferred` — and it is rebuilt by reading them again and
never cited. No person's judgement is kept there — nothing in it is
`confirmed`, `rejected` or `retired` — because a judgement is not derived from
the repositories and reading them again cannot rebuild it: it is kept only in a
tenant's ledger. That is not duplication; it is the same split custody already
makes, and both follow this blueprint's claim model.

A citation across the split is an ordinary edge whose far endpoint names another
scope's source, which the endpoint model already carries. It records that the
citation exists, and nothing more: it never makes what lies outside every tenant
something a claim that a tenant conforms may cite, which
[`architecture/content`](content.md#repositories-outside-a-tenant) forbids. What
it is **not** is federation: relationships spanning two tenants are a different
question with a different trust model and are outside this blueprint.

### Scale

Three costs are usually conflated and must be separated, because only one of them
is hard.

| Cost | Grows with | Shape of the answer |
|---|---|---|
| Append | nothing | constant, given the tip is read backwards from the end |
| Query | the ledger | a node-keyed index maintained beside the incremental parse |
| Re-derivation | corpus × producers × change rate | partitions, input digests, and a diff that decides the blast radius |

**Never materialise a transitive relationship.** Only direct edges are stored;
*which policy does this ultimately serve* is a traversal at read time. This is
what makes layering affordable — re-deriving one layer touches no other, and the
composite answer stays correct because it was never written down. Had the closure
been stored, one edit would rewrite every path through it and each new layer
would multiply rather than add.

**A producer declares its own partition**, and retirement binds to producer,
scope **and** partition. Without that the only choices are a correct full scan or
an incremental path that never retires. The partition key MUST be a durable
identity rather than an address: a key derived from a path breaks when the file
moves, and a move that reads as a deletion would retire every edge in the
partition.

**A partition whose input digests are unchanged is skipped entirely.** This is
exact rather than heuristic, on the same ground as the byte-length rule: a
producer is a pure function of its inputs, so identical input bytes produce
identical claims. A producer for which that is not true is the fault.

**The diff decides the blast radius.** A change that touches no binding reaches
no dependent partition, however much of the document moved. This is what converts
*that specification changed*, whose radius is everything citing it, into *that
field changed*, whose radius is the few things that use it.

### Staleness and rebuild are different questions

| | Answers | Applies to | Triggered by |
|---|---|---|---|
| Staleness | this claim is unreviewed against what the thing became | any node, from either end | any endpoint's version changing |
| Rebuild | this artifact must be produced again | artifacts a specification derived | that specification's bindings changing |

An edit to a policy MUST mark every edge citing it stale, and MUST NOT cause
anything to be regenerated. *Somebody should review whether this still holds* and
*produce this file again* are different instructions, and a platform that
conflated them would rewrite a tenant's source because an author fixed a typo.

Staleness is the universal signal; a rebuild is one possible response to it and
is available only where the derivation was recorded. Everything else resolves to
a review — by a person, or by an agent that proposes and does not apply.

### Reach from a diff

`GET /v1/fabric/reach?diff=<ref>@<a>..<b>` answers *what does this change
reach* (`reach-by-diff`). The two versions are compared by part: each part
whose projection digest differs, and each part added or retired, is a starting
node, and nothing else is. A change to explaining prose that no part owns
starts nothing. From each starting node the walk follows `implements`,
`verifies`, `generated_from`, `deployed_as`, `enforced_by` and `consumes`, to
the depth `reach-max-depth` bounds, and returns one set of paths per starting
node.

The fabric reads no content, so the part digests of both versions come from the
content service as identity: the walked projection it returns for a ref at a
version, which carries each part's id and projection digest and no bytes.

> **Gap — the content service serves no part digests.**
> [`architecture/content`](content.md) specifies identity lookup for a whole
> entry, not the per-part projection this needs. Until it does, a reach from a
> diff answers with `answerable` false and says why, rather than starting from
> the whole file and presenting that as the change's reach.

A requirement nobody implements reaches nothing, and that is an answer, carried
with its completeness like any other. Never-scanned partitions are counted, and
reaching the bound is reported, never read as "nothing further".

---

## Types

```yaml
types:
  NodeRef:
    description: One end of a claim. An address, an identity, and where in it
    fields:
      source:
        type: string
        required: true
        description: The source the artifact belongs to. A path with no source is
          not an identity
      artifact_id:
        type: string
        required: true
        description: The artifact's identity as its kind declares identity. Where
          the content carries a durable identifier, that identifier
      address:
        type: string
        required: false
        description: Where it currently sits. A mutable attribute, refreshed on
          every claim, never part of the key
      kind:
        type: string
        required: false
        description: Derived, open, and reported as undeclared when unrecognised.
          Never part of the key, and nothing branches on its name
      anchor:
        type: ClaimAnchor
        required: false
        description: Where in the artifact. Absent means the whole artifact — a
          weaker claim, made honestly
      cited_version:
        type: ContentIdentity
        required: false
        description: What this end was when the claim was made — the digest
          of its stored bytes, or, where `projection` is set, of the declared
          projection that names (a control's text, a requirement's or mapping
          rule's part, a provider's reported configuration). Staleness is
          evaluated on whichever it is. Absent only for an end that has
          neither, which reads `unversioned`
      cited_size:
        type: integer
        required: false
        description: Byte length at the time of the claim. What makes a relocation
          search prunable rather than a scan of the workspace

  ClaimAnchor:
    description: The place within an artifact that a claim is about
    fields:
      kind:
        type: enum
        values: [block, section, symbol, path, lines, cell]
        required: true
        description: block survives editing best; lines are meaningful only
          together with a version. section names a slot of a walked file by
          its family's slot key, never by heading text, so rewording a heading
          moves nothing. symbol names a declaration in generated code, and
          exists only where the language mapping ships a symbol extractor
      value:
        type: string
        required: true
        description: The block uid, slot key, qualified symbol, dotted path,
          range or cell reference

  RelationshipIdentity:
    description: What makes two claims the same claim. Nothing else belongs here
    fields:
      from:
        type: NodeRef
        required: true
      to:
        type: NodeRef
        required: true
      relation:
        type: string
        required: true
        description: A declared relation, normalised from its accepted spellings
          on the way in
      scope:
        type: ScopeDeclaration
        required: true

  RelationshipClaim:
    description: What a producer, agent or integration submits. It has no status
      field, and that absence is the authority model
    fields:
      identity:
        type: RelationshipIdentity
        required: true
      confidence:
        type: number
        required: true
        description: Machine certainty, never a substitute for a person. A
          recorded derivation is the highest confidence and is still inferred
      basis:
        type: string
        required: true
        description: What the producer matched on, in terms a person can check
      observed_at:
        type: timestamp
        required: false
        description: For a claim about a service we do not hold, what was reported
          and when, in place of a version we computed

  RelationshipEdge:
    description: One live relationship, folded from its entries. Health is added
      at read time and is never part of the record
    fields:
      identity:
        type: RelationshipIdentity
        required: true
      status:
        type: enum
        values: [inferred, confirmed, rejected, retired]
        required: true
      asserted_by:
        type: string
        required: true
        description: The producer, agent or person whose assertion stands, by identity id, as the entry that made it records its actor
      confidence:
        type: number
        required: true
      compliance_state:
        type: enum
        values: [meets, partial, gap, unknown]
        required: false
        description: For a claim about a service we do not hold. unknown is
          first-class and MUST NOT be collapsed into gap — checked and wrong, and
          could not check, are different facts
      seq:
        type: integer
        required: true
        description: The sequence of the entry this state came from
      recorded_at:
        type: timestamp
        required: true

  LedgerEntry:
    description: One append. Written once, never edited, and committing to its
      predecessor
    fields:
      seq:
        type: integer
        required: true
      scope:
        type: ScopeDeclaration
        required: true
      partition:
        type: string
        required: false
        description: Present on a producer entry. Retirement binds to it
      act:
        type: enum
        values: [assert, revise, retire, defer, relocate]
        required: true
      claim:
        type: RelationshipClaim
        required: true
      status:
        type: enum
        values: [inferred, confirmed, rejected, retired]
        required: true
        description: Set on the entry by the gate, never carried in on a claim
      actor:
        type: string
        required: true
        description: Who acted, by identity id. A person's is the identity_id claim of the pass their request arrived on; a producer's or an agent's is the identity_id claim of the token it presented. Never the token's sub, which is a name
      note:
        type: string
        required: false
        description: On a retirement, where the content went or why it was withdrawn
      run:
        type: RunCitation
        required: false
        description: Present on an entry appended from a run statement. Names
          the run; the run's facts stay in its statement
      on_behalf_of:
        type: string
        required: false
        description: The identity id of the person a service credential acted
          for, as the run statement records it. Present only with run
      previous_digest:
        type: string
        required: true
        description: The SHA-256 of the preceding entry's stored line, written
          as sha256:<hex>; on the first entry, the sha256 prefix and 64 zeros.
          vectors/fabric-ledger.json is a worked chain
      recorded_at:
        type: timestamp
        required: true

  RunCitation:
    description: A run, as an entry cites it
    fields:
      id:
        type: string
        required: true
        description: The run's full ref, run://<namespace>/<run id>
      statement_digest:
        type: string
        required: true
        description: sha256:<hex> of the run statement file's bytes
      signed:
        type: boolean
        required: true
        description: Whether the statement carried a signature that verified
          under the tenant's generation service credential. False until the
          credential layer exists

  DiffStart:
    description: Where a reach from a diff starts
    fields:
      ref:
        type: string
        required: true
      from_version:
        type: string
        required: true
      to_version:
        type: string
        required: true

  EdgeHealth:
    description: Derived on read from both endpoints. Never stored
    fields:
      state:
        type: enum
        values: [current, stale, moved, broken, unreachable, unversioned]
        required: true
      endpoint:
        type: enum
        values: [from, to, both]
        required: false
        description: Which end is not current
      recorded_digest:
        type: string
        required: false
      current_digest:
        type: string
        required: false
        description: Absent when nothing could be read, which is the whole point
          of unreachable

  AnswerCompleteness:
    description: What an answer does not know. Present on every answer, always
    fields:
      answerable:
        type: boolean
        required: true
        description: False when the ledger could not be read at all. A caller
          MUST report that it cannot answer rather than that nothing is related
      producers_contributing:
        type: list
        required: true
      partitions_never_scanned:
        type: integer
        required: true
        description: A count above zero means an absence here is not evidence of
          absence
      endpoints_unreachable:
        type: integer
        required: true
      file_level_endpoints:
        type: integer
        required: true
        description: Endpoints in generated code anchored to the whole file
          because their language mapping ships no symbol extractor. Above
          zero, the answer is file-level for those, and says so
      depth_bound_reached:
        type: boolean
        required: true
        description: True when a walk stopped at reach-max-depth with edges
          still unfollowed. Never read as nothing further
      access_complete:
        type: boolean
        required: true
        description: False whenever any cited repository's effective custody
          is shared or opaque. Derived, and no caller may set it

  CoverageAnswer:
    description: What answers a criterion, and what the answer rests on
    fields:
      criterion:
        type: NodeRef
        required: true
      answers:
        type: list
        required: true
        description: Edges answering it, each carried whole so the clause travels
          with the answer
      needs_review:
        type: list
        required: true
        description: Answers that are stale or unreachable. Counted here, never
          as answered
      completeness:
        type: AnswerCompleteness
        required: true

  ImpactPath:
    description: One route from the node asked about to something it reaches
    fields:
      steps:
        type: list
        required: true
        description: Each step names its relation and whether it was stored or
          synthesised
      terminates_at:
        type: NodeRef
        required: true
      weakest_step:
        type: string
        required: true
        description: The least authoritative status on the path. A chain is worth
          its weakest hop, and presenting a recorded derivation and a keyword
          match identically is how a governance claim stops being trustworthy

  ProducerPartition:
    description: What a producer covers, and what it has actually done
    fields:
      producer:
        type: string
        required: true
      partition:
        type: string
        required: true
        description: A durable identity, never an address
      input_digests:
        type: list
        required: true
        description: What was read last time. Unchanged means the partition is
          skipped entirely
      watermark:
        type: integer
        required: false
        description: Absent means never run, which is not the same as found nothing
      last_run_at:
        type: timestamp
        required: false

  SyncResult:
    description: What one producer run changed
    fields:
      asserted:
        type: integer
        required: true
      retired:
        type: integer
        required: true
      deferred:
        type: integer
        required: true
        description: Claims left alone because a person had decided them
      skipped_partitions:
        type: integer
        required: true
      faults:
        type: list
        required: false
        description: Claims refused, each naming the rule it broke

  RelocationResult:
    description: The outcome of repairing an address
    fields:
      resolved:
        type: boolean
        required: true
      candidates:
        type: list
        required: true
        description: Every artifact whose content matched. More than one is
          reported and never resolved
      retired_seq:
        type: integer
        required: false
      asserted_seq:
        type: integer
        required: false

  Projection:
    description: The live graph, built on demand and byte-stable
    fields:
      nodes:
        type: list
        required: true
      edges:
        type: list
        required: true
        description: Each carrying both the version cited and the version observed
          when the projection was built
      chain_tip:
        type: string
        required: true
        description: Stands in place of a generation time, so an unchanged ledger
          projects to identical bytes
      completeness:
        type: AnswerCompleteness
        required: true

  ChainVerdict:
    description: Whether the log still follows itself
    fields:
      valid:
        type: boolean
        required: true
      checked_from:
        type: integer
        required: true
      checked_to:
        type: integer
        required: true
      broken_at:
        type: integer
        required: false
        description: The first entry that does not follow its predecessor
```

---

## Configuration

```yaml
fabric:
  ledger:
    partition_by: scope            # never by kind and never by relation
    retention: none                # a compliance relationship is a permanent record
    batch_producer_writes: true    # one lock and one durability barrier per producer run
  resolution:
    unqualified_reference: refuse  # two sources answering is no answer
    prefer_content_identifier: true
  traversal:
    # No depth here: the bound is requirement reach-max-depth, and a setting
    # that could raise it would be a second home for one number.
    max_edges_per_answer: 5000     # exceeded is reported on the answer, never trimmed silently
  producers:
    - name: <producer>
      partition: <granularity>
      skip_unchanged_inputs: true
      scopes: ["<tenant>/<org>", "<tenant>/<org>/<project>"]
```

Configuration declares which producers exist and how they partition. It does not
declare what is related: every relationship in the ledger was asserted by
somebody, and a relationship that came from a settings file was asserted by
nobody.

A traversal limit that is reached MUST be reported on the answer's completeness.
An answer trimmed to a limit and presented as whole is the confident zero in a
different costume.

---

## Registration and Standalone Operation

The fabric service is a component in the mesh: it registers with the
orchestrator, claims the `fabric.*` namespace exclusively, and verifies caller
tokens against the orchestrator's public key.

Its manifest declares the wire protocol version from
[`protocol/types`](../protocol/types.md) — not this blueprint's semver. Its
routes are guarded by the `fabric:` family that document declares:

| Capability | Guards |
|---|---|
| `fabric:read` | the six read operations, and `GET /v1/fabric/producers` |
| `fabric:produce` | `POST /v1/fabric/sync` |
| `fabric:observe` | `POST /v1/fabric/observations` |
| `fabric:attest` | `POST /v1/fabric/attestations`, `/decisions` and `/relocations`. Person only |

`fabric:attest` is *person only* ([`protocol/types`](../protocol/types.md)):
only a person reaches `confirmed`, so the fabric's own manifest never declares
it, and no service subject and no agent is granted it
([`patterns/principal-identity`](../patterns/principal-identity.md)). A person
holds it through a role, and
[`architecture/admin`](admin.md#operator-roles)'s roles table says which roles
carry it, and `fabric:read`.

**This service honours `fabric:attest` only on a pass.** It counts only on a
pass addressed to this service
([`protocol/identity`](../protocol/identity.md#the-pass) rule 6), which the
orchestrator mints for a person's operator token, a token minted through a
credential that person's identity attested
([`architecture/admin`](admin.md#operator-token)). On any other token, a
registered component's or a channel's, this service treats it as absent and
refuses the request with `FORBIDDEN`. A hub that minted it on one by mistake
has still opened no person route.

**A person's act arrives on a pass.** Before it appends an attestation, a
decision or a relocation, this service looks at the token. One that is not a
pass addressed to it is refused with `FORBIDDEN`, as the rule above says, and
an operator token is refused before this, on every route, with
`PASS_REQUIRED`. On a pass, it authorises the act against the pass's `cap`,
which the orchestrator computed at the exchange from what the operator's role
carried then, never beyond the token's `cap`, and only for a token it judged
live then
([`architecture/orchestrator`](orchestrator.md#token-exchange-post-v1tokenexchange),
`token-exchange`). This service asks nothing again. So a removed operator, a
revoked credential and a role lowered below `fabric:attest` reach this service
at the person's next act, and a pass minted before lives at most 30 seconds.
A read on a pass is bounded the same way, and its audit entry names the
gateway that carried it as `via`, beside the person as `actor`.

A capability name is `family:verb`, and an invented one is refused at
registration — which is why these belong in
[`protocol/types`](../protocol/types.md) before this component is built.

**Its manifest declares the person's routes as pass routes**
([`protocol/types`](../protocol/types.md#passroute), `pass_routes`): the three
`fabric:attest` routes and the seven `fabric:read` routes of
[Endpoints](#endpoints), each with the one capability the table above gives
it and no body requirement. `POST /v1/fabric/sync` and
`POST /v1/fabric/observations` are a producer's, which no person reaches, and
are not among them. The admin gateway carries a person's request here only on
a route this list declares, on a pass naming that capability
([`architecture/admin`](admin.md#contracts), `admin-gateway-authorization`),
so the list and the table MUST agree.

**It also holds two capabilities as a client**, and they are the only reach it
has outside itself: `content:read`, for the identity lookup and listing that
version resolution and relocation need, and `content:describe`, for the custody
facts that decide what an answer may claim. It holds `content:read` and MUST NOT
use it to transfer entry bytes — a ledger does not need content in order to cite
it, and one that holds content answers around the access decision it was supposed
to respect.

Both are exercised at an address resolved from the directory, and the fabric
MUST NOT decide for itself which addresses are in bounds — see
[Where the content service is](#where-the-content-service-is). It declares no
`agent:message`, and MUST NOT acquire one to reach a content service on another
host.

Startup follows the same order every mesh component follows, and for the same
reason: the key this service authenticates with arrives in the registration
response, so an authenticator that demanded it up front would exit before it
could be obtained. The one addition is that the chain is verified from the last
known-good sequence before the service accepts a write, and a broken chain leaves
the service refusing appends while still answering reads, and naming the
chain `not_ready` in the `checks` its lease carries — refusing to read would hide the evidence somebody now needs.

**An orchestrator is not required in order to start.** Where none is configured,
`GET /livez` and `GET /readyz` are served unauthenticated, `/readyz` answering
`ready: false`, and the service logs that no orchestrator is configured; every
protected endpoint refuses, because a component holding no
issuer key can verify no token and MUST NOT accept one. Where an orchestrator is
configured, a failed registration is fatal.

---

## Security

```yaml
security:
  trust_model:
    description: |
      The service trusts its own appends and the chain that binds them, and
      nothing else. It is the only writer of the ledger, so a difference it did
      not make is an integrity fault rather than an observation — the opposite
      of the content service's posture, and deliberately so. It trusts no
      claim's self-description: an endpoint is resolved here before anything is
      written, a status is set here and never carried in, and a relation is
      accepted only if the taxonomy declares it between those kinds. It makes no
      statement about content it did not read, and it never becomes a way to
      reach content a caller could not otherwise reach.

  boundaries:
    - boundary: Caller → Fabric Service. Every claim's scope is confined to the
        caller's before any resolution or write
    - boundary: Fabric Service → Content Service. Identity and listing only. The
        fabric never opens a repository and never transfers entry bytes
    - boundary: Fabric Service → Enforcement. Every operation passes the boundary
        proxy; the fabric supplies the resource scope and does not make the
        access decision. For a content entry that is its ContentEntry.scope,
        and for an unclassified entry the default_level architecture/content
        gives the storage proxy (The recorded scope), never a level of the
        fabric's own
    - boundary: Producer → Ledger. A producer's reach is bounded by its own
        declared partitions; it can retire nothing outside them
    - boundary: Machine → Person. A confirmation is reachable only through a
        person's own act, and the claim type has nowhere to carry one

  enforcement:
    - rule: A producer or agent cannot record a confirmation
      mechanism: The submitted claim type has no status field; the gate sets it
    - rule: A producer cannot revise or retire an edge a person decided
      mechanism: Deferral check before every write, reported on the result and
        published as fabric.relationship.deferred
    - rule: A producer can retire only within a partition it declared
      mechanism: Retirement is bounded by producer, scope and partition; an
        undeclared partition refuses the whole batch
    - rule: An unqualified reference that two sources answer is refused
      mechanism: Endpoint Resolver; ambiguity is reported, never resolved
    - rule: A relocation cannot name its destination
      mechanism: The operation accepts an identity and no target; a caller that
        could name a destination could attach somebody's confirmation to a
        document of its own choosing
    - rule: A relocation with more than one candidate is refused
      mechanism: Candidate set is returned whole; silently re-pointing evidence
        at an archive copy is worse than reporting a break
    - rule: The chain cannot fork
      mechanism: Exclusive lock held across reading the tip and writing the
        entry, per architecture/storage's concurrency requirement
    - rule: A ledger that shrank is never continued from
      mechanism: Byte-length invalidation; a decrease forces a full re-read and
        is reported
    - rule: An unreadable endpoint never reports as covered
      mechanism: Health is unreachable; coverage counts it as needing review
    - rule: An answer citing shared or opaque content is marked incomplete
      mechanism: Completeness is derived from the effective custody of every
        repository cited and cannot be set by a caller
    - rule: The ledger never holds content
      mechanism: Only address, identity and size are recorded; version resolution
        uses the content service's identity lookup, which transfers no bytes
    - rule: The fabric's credential never leaves the host it is anchored to
      mechanism: A content service on another host is reached only through a
        grant naming that address; absent one the repository is unreachable and
        the answer says so, per architecture/orchestrator's reach rule
```

---

## Implementation Notes

- **Resolve the endpoint before anything else, in one place.** Four independent
  write paths each assembled their own endpoints and disagreed about the source
  and the kind, so a person's confirmation landed beside a producer's inference
  instead of on it. The resolver may fill only the kind and the source: the
  identity, the anchor, the cited version and the recorded size are what the
  claim was *made* about, and a resolver that changed any of them would be
  re-pointing somebody's evidence rather than naming it.

- **Read the chain tip backwards from the end of the log.** Parsing the whole
  file to find the last line makes each append linear in the ledger and building
  one quadratic; at twenty thousand edges that stops finishing.

- **Measure the durability barrier before batching anything else.** In one
  implementation it was 97% of an append's cost, and a producer run finding a
  thousand relationships spent seconds in it. Batching a producer run is the
  fix; batching a person's act is not, because the two differ in whether the work
  can be re-derived.

- **Prune a relocation search by size, and read candidates at lookup time.**
  Identical content is necessarily identical in length, so a candidate whose size
  differs need never be opened; this is exact, so the ambiguity rule stays
  complete. Reading candidates when they are needed rather than during the walk
  costs nothing and means an entry removed since the walk is simply not found,
  rather than being named as the place somebody's evidence now lives.

- **Never let a producer read what a sync writes.** A projection once shared a
  path with a producer's input; the next run parsed the projection, recognised
  no relationships, and withdrew every one in the ledger. Nothing this service
  writes may sit inside anything a producer scans.

- **Report an unrecognised kind as unrecognised.** It is representable, it gains
  no capability, and it is never defaulted into one. Two implementations
  defaulted an unknown kind into an evidence layer, which put unclassified
  documents into a chain and scored them.

- **Keep `unknown` out of `gap`.** For a claim about a service we do not hold,
  *we checked and it is wrong* and *we could not check* are different facts, and
  only one of them is something to fix. Collapsing them produces a work queue
  full of items nobody can action.

- **Do not implement the content service's reconciliation here.** There is no
  second writer, so every difference is genuinely an anomaly, and running that
  mechanism would reclassify tampering as an ordinary edit.

- **An agent reacting to an event MUST scope its work to that event's
  partition.** An agent that answers *one file changed* by rescanning a corpus
  will look correct, because it will be correct. It will simply be quadratic, and
  it reintroduces exactly the cost partitioning removes.

- **Hold no personal data in an entry.** An entry names artifacts by durable
  identifier and actors by identity id, and holds no content, which is what lets an erasure
  obligation be answered at the identity layer rather than by rewriting a chained
  leaf. Whether erasing the identity itself is compatible with an immutable chain
  is a contract question, it belongs to the privacy pattern, and it is not
  answered here.

- **When this blueprint migrates to a single declaration block, the chain is the
  first thing to declare a machine-checkable predicate for.** *Every entry's
  recorded predecessor digest equals the digest of the prior entry* is exactly
  what a declared check is good at, and unlike prose matching it cannot be wrong
  in the persuasive way.

- **The ledger is deliberately not among the stores
  [`architecture/storage`](storage.md) enumerates.** Those name the components of
  the mandatory mesh, and adding an opt-in component's store there would make
  every tenant answerable for a store it does not have. The consequence is that a
  generator reads this component's operations from its own interfaces rather than
  from the storage table, which is the same route the content service takes.

---

## Verification

Each check names the requirements it covers. A generated test is named by its
check id, so verification is keyed by id and never by a line number.

```yaml
verifies:
  - id: no-write-path-reaches-content-writer
    covers: [no-content-writes]
    assertion: From each write handler — Sync, Observe, Attest, Decide and
      Relocate — no call path reaches a content write operation. The fabric's
      content client exposes identity lookup, listing and describe and nothing
      else, and a test named for this check fails when a write is added to it.
  - id: ledger-vector-verifies
    covers: [entries-name-their-run]
    assertion: vectors/fabric-ledger.json verifies with SHA-256 and an RFC 8785
      canonicaliser alone, and a copy with one entry altered fails at exactly
      that entry.
  - id: second-ingest-appends-nothing
    covers: [statements-ingest-once, declared-at-write-time]
    assertion: Ingesting a set of run statements appends their edges, each
      citing its run; ingesting the same set again appends no entry.
  - id: reach-stops-at-the-bound
    covers: [reach-max-depth]
    assertion: On a chain longer than reach-max-depth hops, a reach returns
      paths of at most that many steps and its completeness says the bound was
      reached; a request for a greater depth is answered at the bound.
  - id: diff-reach-starts-at-changed-parts
    covers: [reach-by-diff]
    assertion: Between two versions that differ in one part's value and in
      prose no part owns, a reach from the diff starts at that one part.
  - id: provider-settings-go-stale
    covers: [observed-connections]
    assertion: When a provider's reported configuration changes, every
      enforced_by edge to it reads stale and nothing is regenerated.
  - id: unsigned-until-credential-layer
    covers: [adoption-follows-credential-layer]
    assertion: In a tenant without the credential layer, run statements are
      unsigned, their entries cite the run with signed false, and no statement
      carries a signature by a person's identity key.
```

---

## Verification Checklist

- [ ] Two claims about the same two artifacts, the same anchors, the same relation and the same scope resolve to one relationship, whatever kind each producer assigned ([What makes two claims the same claim](#what-makes-two-claims-the-same-claim))
- [ ] Changing an artifact's classification does not change the key of any relationship recorded against it ([What makes two claims the same claim](#what-makes-two-claims-the-same-claim), [Design Principles](#design-principles) 3)
- [ ] A claim submitted with a `status` field is refused, and the submitted type has nowhere to carry one ([Design Principles](#design-principles) 4, [Security](#security))
- [ ] A producer's claim that disagrees with an edge a person decided leaves that edge unchanged, returns a deferral, and publishes `fabric.relationship.deferred` ([Who may assert what](#who-may-assert-what), [Security](#security))
- [ ] A producer's `Sync` retires only edges matching its own producer name, scope and declared partition ([Scale](#scale), [Security](#security))
- [ ] A `Sync` naming a partition the producer has not declared refuses the whole batch rather than retiring anything ([Error Handling](#error-handling), [Security](#security))
- [ ] Editing one endpoint of a confirmed relationship leaves the relationship recorded, its status unchanged, and its health `stale` ([Health](#health))
- [ ] An endpoint that cannot be read yields health `unreachable`, never `broken` and never `current`, and coverage counts it as needing review ([The Custody Question](#the-custody-question), [Health](#health))
- [ ] Moving a file to which a confirmed relationship points yields health `moved`, and the status is not demoted ([Health](#health))
- [ ] An artifact carrying its own durable identifier keeps its relationships across a move with no repair, and its recorded address is refreshed on the next claim ([What makes two claims the same claim](#what-makes-two-claims-the-same-claim))
- [ ] A relocation whose content matches in two places is refused with both candidates named, and nothing is written ([Relocation Flow](#relocation-flow), [Security](#security))
- [ ] A relocation on an edge with no recorded size declines rather than hashing the workspace ([Relocation Flow](#relocation-flow), [Error Handling](#error-handling))
- [ ] A relocation request carrying a destination is refused ([Security](#security))
- [ ] A reference naming a path that two sources in scope answer is refused, and both candidates are named ([Design Principles](#design-principles) 2, [Error Handling](#error-handling))
- [ ] A relation the kind taxonomy does not declare between those two kinds is skipped and reported as a producer fault ([Error Handling](#error-handling))
- [ ] A second process appending concurrently cannot produce two entries with the same predecessor digest ([The Ledger](#the-ledger), [Security](#security))
- [ ] An entry altered on disk makes `Verify` report `valid` false and name the first entry that does not follow ([Interfaces](#interfaces), [Types](#types), [Error Handling](#error-handling))
- [ ] A ledger whose byte length decreased is re-read in full and reported, and no answer is served from the incremental parse ([The Ledger](#the-ledger), [Security](#security))
- [ ] A producer run writes one batch, and a person's act writes alone ([The Ledger](#the-ledger))
- [ ] Every answer carries an `AnswerCompleteness`, and a coverage result of zero states how many partitions have never been scanned ([Design Principles](#design-principles) 8, [Answer Flow](#answer-flow), [Types](#types))
- [ ] An answer whose traversal limit was reached says so on its completeness rather than returning a trimmed result as whole ([Configuration](#configuration))
- [ ] Every answer citing a repository whose `effective_custody` is shared or opaque carries `access_complete` false, and no caller can set it true ([The Custody Question](#the-custody-question), [Security](#security))
- [ ] No fabric code path transfers content bytes; version resolution and relocation use identity lookup and listing only ([Why this is its own component](#why-this-is-its-own-component), [Security](#security))
- [ ] A content service whose `ServiceEntry` is on another host is reached only with a grant for that address; absent one the repository is `unreachable` and no credential is sent ([Where the content service is](#where-the-content-service-is), [Security](#security))
- [ ] The fabric's manifest declares no `agent:message`, and a remote content service does not cause it to be added ([Registration and Standalone Operation](#registration-and-standalone-operation), [Where the content service is](#where-the-content-service-is))
- [ ] The fabric's manifest declares no `fabric:attest`, and its registration succeeds; a component whose manifest declares `fabric:attest` is refused at registration with `CAPABILITY_PERSON_ONLY` ([`protocol/types`](../protocol/types.md#capability)), and an agent's authorisation naming it is refused
- [ ] The fabric's manifest's `pass_routes` declare the three `fabric:attest` routes with `[fabric:attest]` and the seven `fabric:read` routes with `[fabric:read]`, and neither `POST /v1/fabric/sync` nor `POST /v1/fabric/observations` ([Registration and Standalone Operation](#registration-and-standalone-operation), [Endpoints](#endpoints))
- [ ] An attestation on a pass addressed to this service whose `cap` names `fabric:attest` is recorded; the same request on a registered component's token or a channel token is refused with `FORBIDDEN`, whatever capabilities that token names, on a person's operator token with `PASS_REQUIRED`, and on a pass addressed to another component with `PASS_AUDIENCE_MISMATCH` ([Registration and Standalone Operation](#registration-and-standalone-operation), [Error Handling](#error-handling))
- [ ] Through the admin gateway, an attestation, a decision or a relocation on an operator token minted before its operator was removed, its credential revoked, or its role lowered to one without `fabric:attest` is refused by the exchange with `OPERATOR_REVOKED`, `CREDENTIAL_REVOKED` or `FORBIDDEN` ([`architecture/admin`](admin.md#contracts), `token-status-on-use`), and this service is sent nothing and appends nothing
- [ ] A person's attestation, decision or relocation records the pass's `identity_id` as the entry's `actor`, never its `sub`, so renaming the operator changes nothing the ledger holds, and its audit entry names the pass's `act.identity_id` as `via`; a producer's claims record the `identity_id` claim of the token it presented ([Person Flow](#person-flow), [Registration and Standalone Operation](#registration-and-standalone-operation), [Types](#types))
- [ ] With the orchestrator unreachable, an attestation on an unexpired pass whose `cap` names `fabric:attest` is recorded, because this service asks the orchestrator nothing about a pass, and one on a pass whose `exp` has passed is refused with `TOKEN_EXPIRED` ([The pass](../protocol/identity.md#the-pass), rule 3, and [`protocol/identity`](../protocol/identity.md#error-handling)) and appends nothing
- [ ] Recording, confirming, rejecting or retiring a relationship leaves both artifacts byte-identical ([Where relationships do not live](#where-relationships-do-not-live))
- [ ] Projecting an unchanged ledger twice produces identical bytes, and every judgement in the projection can be recomputed from the content with a published digest tool ([Design Principles](#design-principles) 9, [Interfaces](#interfaces))
- [ ] Every relationship reachable from one endpoint is reachable from the other, and a synthesised containment step is reported as synthesised ([Overview](#overview), [Answer Flow](#answer-flow))
- [ ] An impact path reports its weakest step, and a recorded derivation and an inferred match never render identically ([Types](#types))
- [ ] A partition whose recorded input digests are unchanged is skipped entirely, with no edge touched and no claim resolved ([Producer Flow](#producer-flow), [Scale](#scale))
- [ ] An edit to a governing document marks dependent edges stale and causes nothing to be regenerated ([Staleness and rebuild are different questions](#staleness-and-rebuild-are-different-questions))
- [ ] With no orchestrator configured, the service starts, serves `GET /livez` live and `GET /readyz` not ready, logs that no orchestrator is configured, and refuses every protected endpoint ([Registration and Standalone Operation](#registration-and-standalone-operation))
- [ ] A broken chain leaves the service refusing appends while still answering reads ([Registration and Standalone Operation](#registration-and-standalone-operation))
- [ ] Every digest the ledger writes as one string reads `sha256:<hex>`, the first entry's `previous_digest` included ([The Ledger](#the-ledger))
- [ ] An entry appended from a run statement carries `run` with the statement's digest and `signed`, and `on_behalf_of` as the statement records it; the statement's model, tool and prompt digest appear in no entry ([Declared at write time](#declared-at-write-time), [Types](#types))
- [ ] An edge to generated code in a language whose mapping ships no symbol extractor is anchored to the whole file, and an answer resting on it counts it in `file_level_endpoints` ([Declared at write time](#declared-at-write-time))
- [ ] A `section` anchor survives a reworded heading unchanged, because its value is the slot key ([Types](#types))
- [ ] No setting raises the reach depth above `reach-max-depth` ([Configuration](#configuration), [Reach from a diff](#reach-from-a-diff))
