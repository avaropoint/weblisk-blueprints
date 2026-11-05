<!-- blueprint
type: pattern
name: repository
version: 1.0.0
requires: [patterns/scope, patterns/content-identity, patterns/principal-identity]
platform: any
tier: free
-->

# Repository Pattern

The shapes in which the content service and the backends that hold its stores
speak of a repository: what is declared, what a backend demonstrated about the
store, what a census found, what leaves to a remote, and what changed.

## Overview

[`architecture/content`](../architecture/content.md) specifies the content
service: when a repository is declared, adopted or established, when a remote
may be sent to, and when a change is recorded. A backend driver, such as
[`patterns/content-git`](content-git.md), holds a store for that service and
fills in some of the same records: a census, a custody demonstration, a change,
an observation.

Both read and write one set of shapes, and this pattern declares them, so that
each binds them from here. A backend then needs nothing of the service's beyond
these types, and the service requires the pattern rather than the pattern
requiring the service.

What each field means to the service, and every rule about when a record is
made, stay in [`architecture/content`](../architecture/content.md). A type's
description that says "See" a section names a section of that document, and
the words Recorded, Witnessed and Asserted that open a field's description are
its, as [Who a change was for](../architecture/content.md#who-a-change-was-for)
gives them.

---

## Dependencies

```yaml
requires:
  - blueprint: patterns/scope
    version: ">=2.3.0 <4.0.0"
    bindings:
      types:
        # An enum: it declares values, not fields, so nothing is bound FROM it.
        # The scope a repository, a remote, a census path or a change carries
        - name: ScopeLevel
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/content-identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        # What a change's before and after are
        - name: ContentIdentity
          fields_used: [algorithm, digest, size]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/principal-identity
    version: ">=1.8.0 <3.0.0"
    bindings:
      types:
        # The attestation a change statement carries, with purpose
        # sign-records
        - name: Attestation
          fields_used: [identity_id, credential_public_key, purpose, not_after, signature]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **The shapes are shared; the rules are the service's** — A backend and the
   service fill in the same records, so the records are declared once, apart
   from both. Every rule about when one is made, and what it obliges, is
   `architecture/content`'s, and is not restated here.

2. **A backend adds no field of its own** — What a backend knows about a store
   that the shapes do not carry goes in `backend_report`, in the form the
   backend's own blueprint declares. A field added to one of these types for
   one backend would be a field every other backend leaves empty.

3. **A placement is a name, never a location** — `Placement` carries the name
   of a backend and a locator under that backend's root, so no record of a
   repository holds where its bytes physically are.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: backend-report
      description: What a backend reports about a store beyond its entries, and where it is carried
      required: true
      rules:
        - A backend whose blueprint reports anything about a store beyond its entries MUST declare the form of that report in that blueprint, and the report MUST be carried as backend_report on ContentRepository, ContentAdoption, ContentRemote and RemoteCensus in that form alone
        - A backend whose blueprint declares no report MUST leave backend_report absent on each of them, never present and empty
        - A field of the report that is a time of observation MUST be named so by the backend's blueprint, so that a digest taken over the report can leave it out (architecture/content, if_match on a declaration)
    - name: placement-names-backend
      description: A placement names a backend and a place under its root, never a location
      required: true
      rules:
        - A Placement MUST carry the name of a backend and a locator relative to that backend's root, and MUST NOT carry a host, a URL, a scheme, a mount, a share, a bucket or an absolute path (architecture/content, A placement names a backend, never a location)
    - name: custody-demonstrated
      description: The custody a record carries is what was demonstrated against the store that exists
      required: true
      rules:
        - The CustodyAttestations a ContentRepository or a ContentRemote carries MUST be those demonstrated against the store or destination that exists, never those a backend could offer in the abstract (architecture/content, What a backend owes once the store exists)
```

---

## Types

Each is used whole by [`architecture/content`](../architecture/content.md),
which records them, and in part by the backend that fills one in, which binds
the fields it writes or reads.

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
        description: tenant/org/project confinement this repository belongs to.
          Each segment after the tenant's is the name of an organisation or a
          project the orchestrator records (architecture/orchestrator, The
          tenant's organisations and projects)
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
          bytes declare none, chosen when neither gives it and the change's
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
        type: timestamp
        required: true
        description: When the person signed. Within 300
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
          credential_public_key over the weblisk/content-change/v2 statement,
          base64url
```

---

## Implementation Notes

- These types are generated into the contract package once, from here, for the
  content service and for every backend built with it. A backend's own types,
  such as the form of its `backend_report`, stay in its own blueprint.
- A field this pattern declares but a backend never writes is left absent by
  that backend; the service decides whether its absence is a refusal.

---

## Verification Checklist

- [ ] `architecture/content` and every backend that fills one of these records in bind its type from this pattern, and no other blueprint declares a type of the same name ([Types](#types)) <!-- wl:check architecture-content-backend-fills-records-bind -->
- [ ] A backend whose blueprint declares a report carries it as `backend_report` on `ContentRepository`, `ContentAdoption`, `ContentRemote` and `RemoteCensus`, in the form that blueprint declares ([Contracts](#contracts), `backend-report`) <!-- wl:check backend-blueprint-declares-report-carries -->
- [ ] A backend whose blueprint declares no report leaves `backend_report` absent on all four ([Contracts](#contracts), `backend-report`) <!-- wl:check backend-blueprint-declares-no-report-leaves -->
- [ ] A `Placement` holds a backend's name and a locator under its root, and no host, URL, scheme, mount, share, bucket or absolute path ([Contracts](#contracts), `placement-names-backend`) <!-- wl:check placement-holds-backends-name-locator-under -->
- [ ] The `CustodyAttestations` on a repository or a remote are those demonstrated against the store or destination that exists ([Contracts](#contracts), `custody-demonstrated`) <!-- wl:check custodyattestations-repository-remote -->
