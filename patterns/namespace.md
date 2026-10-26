<!-- blueprint
type: pattern
name: namespace
version: 1.0.0
requires: [protocol/types, protocol/identity, patterns/principal-identity]
related: [architecture/storage, architecture/hub, architecture/tenancy]
platform: any
tier: free
adoption: opt-in
-->

# Namespace Registry Pattern

Who holds a namespace, how a holder hands it on, and how anyone checks a
release published under it, with no party trusted for more than its own
signature.

## Overview

[`schemas/names`](../schemas/names.md) says what a namespace is, how one is
written, which names are reserved and which are confusable with them. It does
not say who holds one. This pattern does.

A **registry** is a sealed log ([`architecture/storage`](../architecture/storage.md#sealing-a-chained-log))
of signed statements about namespaces. Each hub runs one, privately, for the
namespaces its own tenant uses. The weblisk.dev directory hub runs the public
one ([`architecture/hub`](../architecture/hub.md#the-public-namespace-registry)).
A registry decides nothing a statement does not already prove: a claim is the
claimant's own signature, a transfer carries both holders' signatures, and the
registry's part is to refuse what its rules refuse, append what they accept, and
seal the result.

Four kinds of fixed-form statement ([`protocol/identity`](../protocol/identity.md#fixed-form-statements))
are defined here. Three are acts on a registry, and one is a release a holder
publishes:

| Statement | Signed by | Does |
|---|---|---|
| `weblisk/namespace-claim/v1` | the claimant | takes an unheld name, first come |
| `weblisk/namespace-grant/v1` | the holder | lets another identity publish under the namespace, or withdraws that |
| `weblisk/namespace-transfer/v1` | the outgoing and the incoming holder; for a retirement, the outgoing holder alone | hands the namespace on, follows a key rotation, or retires it for good |
| `weblisk/catalog-release/v1` | the holder, or an identity it granted `publish` | publishes the index of the namespace's parts at one release |

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <5.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=2.3.0 <3.0.0"
    bindings:
      types:
        - name: SigningKeyPair
          fields_used: [public_key, sign, verify]
    # The four statements are fixed-form statements, registered there
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/principal-identity
    version: ">=1.9.0 <2.0.0"
    bindings:
      types:
        # Who may hold a namespace: an enrolled identity whose kind is user
        - name: Identity
          fields_used: [id, public_key, kind, status]
      behaviors:
        - name: service-subject-constraints
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

A pattern requires nothing above its layer, so
[`architecture/storage`](../architecture/storage.md), whose sealed log a
registry keeps, is `related:` and not required: this pattern cites the sealed
log's rules and binds none of its types. The hub that runs a registry
([`architecture/hub`](../architecture/hub.md)) and the tenancy that claims its
first name ([`architecture/tenancy`](../architecture/tenancy.md)) require this
pattern, never the other way round.

---

## Design Principles

1. **A signature is the claim.** A registry records what holders signed; it
   never acts for a holder, so the log proves every holding without trusting
   the hub that keeps it.
2. **First come, and never back.** An unheld name goes to the first claim the
   rules allow, and a retired one goes to nobody, ever. Disputes are settled by
   a ruling that is itself in the log, never by an edit.
3. **Both sides sign a hand-over.** A namespace never moves on one party's
   word, as a sealed log's authority never does.
4. **A person holds a name.** A service may publish under one by grant; it never
   holds one, so every namespace answers to a person.
5. **A release is checkable anywhere.** A catalog release names no registry and
   needs no hub to verify: its signature, its index and a registry's public log
   are enough.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: namespace-registry
      description: Decide claims, grants and transfers, and keep what was decided in a sealed log
      required: true
      rules:
        - Decides each statement by the steps of Deciding a statement, in order, giving the first refusal that applies
        - Meets claim-first-come, holder-is-a-person, reserved-and-confusable-refused, transfer-needs-both, retired-never-returns, rotation-keeps-the-binding, statements-bound-to-one-registry and log-is-the-record (Requirements)
        - Gives every step of vectors/namespace-registry.json its stated verdict
    - name: release-verification
      description: Verify a catalog release against a registry's state
      required: true
      rules:
        - Meets release-by-holder-or-publisher and release-continues (Requirements)
        - Decides each release by Deciding a statement's steps for a catalog release, in order, giving the first refusal that applies
        - Gives every release step of vectors/namespace-registry.json its stated verdict
  guarantees:
    - Who holds a namespace is read from a sealed log, never from a hub's say-so
    - A retired namespace and a retired part id are never issued again
```

---

## Requirements

Each requirement is a part of this file:
`requirement://weblisk/patterns/namespace:<id>`.

```yaml
requirements:
  - id: claim-first-come
    level: must
    text: An unheld, unreserved name goes to the first claim the registry
      accepts. A claim of a name the registry already records as held, frozen
      or retired is refused.
  - id: holder-is-a-person
    level: must
    text: Only an identity the registry's hub has enrolled with kind user may
      claim a namespace or receive one by transfer. A service identity never
      holds one, though a holder may grant it publish.
  - id: reserved-and-confusable-refused
    level: must
    text: A claim is refused for every name schemas/names.md says can never be
      claimed, compared as that file says.
  - id: transfer-needs-both
    level: must
    text: A transfer or a rotation is accepted only with valid signatures by
      both the outgoing and the incoming holder. Either signature alone is
      refused.
  - id: retired-never-returns
    level: must
    text: A retired namespace is never claimed, granted, transferred or
      released again, by anyone, its last holder included.
  - id: rotation-keeps-the-binding
    level: must
    text: A rotation moves the namespace to the holder's incoming key and keeps
      its claim and its grants. A transfer to another identity ends every grant
      the outgoing holder made.
  - id: statements-bound-to-one-registry
    level: must
    text: Every claim, grant and transfer names the log id of the one registry
      it is made at, and every other registry refuses it.
  - id: log-is-the-record
    level: must
    text: What a registry accepted is exactly what its sealed log holds. It
      appends an accepted statement, with its signatures, before it answers,
      and appends nothing for a refused one.
  - id: release-by-holder-or-publisher
    level: must
    text: A catalog release verifies only when, at its own released_at as the
      registry's log records it, the namespace was held and not frozen and its
      signer was the holder or an identity the holder had granted publish. A
      release made before a rotation, a transfer, a withdrawn grant or a
      retirement still verifies after it.
  - id: release-continues
    level: must
    text: A release continues the release before it, as the releases a verifier
      holds record it. Release 1 names no previous; release N names release
      N-1's index as previous, is dated no earlier than it, and its index keeps
      every ref release N-1's index held, a retired ref still retired. A second
      index for a release number the verifier holds is refused.
```

---

## The Statements

Each is a fixed-form statement: the prefix, then each field in the order
given, each preceded by one 0x00 byte ([`protocol/identity`](../protocol/identity.md#fixed-form-statements)).
A fingerprint is [Key Fingerprint](../protocol/identity.md#key-fingerprint)'s
64 lowercase hex characters. A time is decimal Unix seconds, UTC, with no sign
and no leading zeros. `<registry>` is the registry's log id
([`architecture/storage`](../architecture/storage.md#what-a-sealed-log-holds)).

### Claim

```
"weblisk/namespace-claim/v1" 0x00 <registry> 0x00 <namespace> 0x00 <holder> 0x00 <issued_at>

<namespace>  the name claimed, as schemas/names.md's grammar writes it
<holder>     the claimant's fingerprint; the claim is signed by that key
```

### Grant

```
"weblisk/namespace-grant/v1" 0x00 <registry> 0x00 <namespace> 0x00 <grantee> 0x00 <role> 0x00 <issued_at>

<grantee>  the fingerprint of the identity the grant is for
<role>     publish, or none, which withdraws an earlier grant to the grantee
```

Signed by the namespace's holder at the registry's tip. A grantee may be any
enrolled identity, a service among them; a grant never makes it the holder.

### Transfer

```
"weblisk/namespace-transfer/v1" 0x00 <registry> 0x00 <namespace> 0x00 <from> 0x00 <to> 0x00 <kind> 0x00 <issued_at>

<from>  the outgoing holder's fingerprint
<to>    the incoming holder's fingerprint; empty for a retirement
<kind>  transfer, rotation or retirement
```

- **transfer** hands the namespace to another identity. Both `from` and `to`
  sign the same bytes. Every grant `from` made ends.
- **rotation** follows the holder's own change of key
  ([`protocol/identity`](../protocol/identity.md#key-rotation)): `from` is the
  outgoing key and `to` the incoming one, and both sign, as a log's succession
  entry is signed by both keys ([`architecture/storage`](../architecture/storage.md#a-change-of-long-lived-key)).
  The claim and every grant stand.
- **retirement** ends the namespace. `to` is empty and only `from` signs, since
  there is nobody to take it on. A retired namespace is a tombstone
  ([`schemas/names`](../schemas/names.md#namespaces), "Retired is never
  reused").

A holder that has lost its key cannot sign a rotation. Only a ruling can then
move the namespace.

### Catalog release

```
"weblisk/catalog-release/v1" 0x00 <namespace> 0x00 <release> 0x00 <index> 0x00 <previous> 0x00 <released_at>

<release>   the release's number in decimal: 1 for the first, one more for each next
<index>     the digest of the release's index, written sha256:<hex>
<previous>  the previous release's <index>, written the same way; empty for release 1
```

A release names no registry, since it is published to be read anywhere. Its
verifier reads the namespace's state from a registry it trusts, as that
registry's log recorded it at the release's `released_at`, and refuses a
release whose signer was neither the holder nor a `publish` grantee then
(`release-by-holder-or-publisher`). Judging at the release's own time, rather
than at the registry's tip, is what keeps a release checkable after its signer's
authority ends: a holder's rotation, a transfer or a withdrawn grant ends what
a key may release from then on, never what it released before.

The signer writes `released_at`, so an identity whose authority has ended could
date a release back into the time it held it. The chain bounds that
(`release-continues`): a release must be the next number after the latest a
verifier holds, name that release's index, and be dated no earlier than it, so a
back-dated release cannot follow one made after its signer's authority ended,
and cannot replace a release a verifier already holds.

**The index** is UTF-8 text, one line per file and per part the namespace's
catalog holds, each line the item's full ref ([`schemas/names`](../schemas/names.md#the-grammar)),
one space, and either its digest — the file's bytes, or the part's projection
digest ([`patterns/content-identity`](content-identity.md)), written
`sha256:<hex>` — or the word `retired`. Lines are in bytewise order of the ref,
no ref appears twice, each line ends with one line feed, and nothing else is in
the file. A ref in one release's index is in every later one: a ref that
disappears, and a `retired` ref that comes back with a digest, make the later
release invalid (`release-continues`). That is how a validator holds a part id
to "retired is never reused" against the previous signed release.

---

## The Registry

### What the log holds

A registry's log is a sealed log, and every rule of
[Sealing a Chained Log](../architecture/storage.md#sealing-a-chained-log)
applies to it: its log id is what every statement's `<registry>` names, and its
owner, the hub, seals it with log keys and checkpoints. Its first entry records
that the log is a namespace registry. Each later owner entry is one of:

- an **accepted statement**: the prefix, the fields in order, each signature
  with the fingerprint of the key that made it, and the public key of every
  signer the log has not recorded before;
- a **ruling**: the hub owner's recorded decision to `freeze`, `unfreeze` or
  `reassign` a namespace, with the reason in words and, for `reassign`, the
  incoming holder's fingerprint.

**Rulings** answer what no holder's signature can: a holder who lost the key,
a name taken in bad faith, a dispute. A frozen namespace accepts no grant,
transfer or release until it is unfrozen. A reassignment makes the incoming
identity, which must be an enrolled user, the holder, and ends every grant, as
a transfer does. A ruling never un-retires a namespace. Every ruling is in the
log with its reason, so it is as visible as any claim.

A namespace's **state** is read from the log alone, in order: `held` by a
holder, with its grants; `frozen`; or `retired`. A name the log never accepted
a claim for is `unheld`.

### Deciding a statement

A registry decides each statement by these steps, in order, and the first that
fails gives the refusal. The registry's clock is `now`.

1. The prefix is one of the three a registry accepts — or, for a catalog
   release a verifier decides, `weblisk/catalog-release/v1` — the field count
   is the prefix's, and every field is in its stated form, `to` empty exactly when
   `kind` is `retirement` — else `NAMESPACE_MALFORMED`.
2. `<registry>` is this registry's log id — else `NAMESPACE_WRONG_REGISTRY`.
3. Every signature the request carries verifies, by
   [Verify Signature](../protocol/identity.md#verify-signature), under a public
   key whose fingerprint is the one the signature names — else
   `NAMESPACE_SIGNATURE_INVALID`.
4. `issued_at` is within the replay window of `now`, either side — else
   `NAMESPACE_STATEMENT_STALE`. The window is
   [`protocol/identity`](../protocol/identity.md#security)'s
   `replay_protection` window, and is not restated here. The log does not
   already hold these bytes — else `NAMESPACE_STATEMENT_REPLAYED`.
5. `<namespace>` is in the grammar of [`schemas/names`](../schemas/names.md#the-grammar)
   — else `NAMESPACE_INVALID`.
6. For a **claim**: the name is not retired (`NAMESPACE_RETIRED`), not one
   that can never be claimed (`NAMESPACE_RESERVED` for a reserved name, place
   code or issuer code; `NAMESPACE_CONFUSABLE` for a name whose skeleton is a
   reserved name's), and not held or frozen (`NAMESPACE_HELD`). `<holder>` is
   an identity the hub has enrolled and not revoked
   (`NAMESPACE_IDENTITY_UNKNOWN`) whose kind
   is user (`NAMESPACE_SERVICE_IDENTITY`), and the claim is signed by
   `<holder>` (`NAMESPACE_NOT_HOLDER`).
7. For a **grant** or a **transfer**: the namespace has been claimed
   (`NAMESPACE_UNKNOWN`), is not retired (`NAMESPACE_RETIRED`) and not frozen
   (`NAMESPACE_FROZEN`). A grant is signed by the holder, and a transfer's
   `<from>` is the holder and has signed (`NAMESPACE_NOT_HOLDER`). A transfer
   or a rotation is signed by `<to>` as well (`NAMESPACE_TRANSFER_ONE_SIDED`).
   `<grantee>` or `<to>` is enrolled and not revoked
   (`NAMESPACE_IDENTITY_UNKNOWN`), and `<to>` is a user
   (`NAMESPACE_SERVICE_IDENTITY`).

An accepted statement is appended before the registry answers
(`log-is-the-record`). A refusal appends nothing.

A **ruling** carries no holder's signature, but is decided all the same, and
a refused one is not recorded: the namespace has been claimed
(`NAMESPACE_UNKNOWN`) and is not retired (`NAMESPACE_RETIRED`); for
`reassign`, the incoming identity is enrolled and not revoked
(`NAMESPACE_IDENTITY_UNKNOWN`) and is a user (`NAMESPACE_SERVICE_IDENTITY`).
Freezing a frozen namespace, or unfreezing a held one, is recorded and changes
nothing.

A **catalog release** is decided by a verifier rather than appended, by these
steps, in order:

1. Steps 1 and 3 above, for its own form and signature. The index the release
   names, as the verifier fetched it, has that digest and is in the index's
   form (The index) — else `NAMESPACE_MALFORMED`.
2. `released_at` is no later than the replay window past `now` — else
   `NAMESPACE_STATEMENT_STALE`. A release from further ahead cannot be judged
   yet, since the state at its time is not yet recorded. A release is not
   refused for being old.
3. Step 5 above, for `<namespace>`.
4. Against the namespace's state at `released_at` — the registry's log entries
   whose `recorded_at` ([`architecture/storage`](../architecture/storage.md#what-a-sealed-log-holds))
   is at or before it: the namespace had been claimed (`NAMESPACE_UNKNOWN`),
   was not retired (`NAMESPACE_RETIRED`) and not frozen (`NAMESPACE_FROZEN`),
   and the signer was its holder or a `publish` grantee
   (`NAMESPACE_NOT_PUBLISHER`).
5. Against the releases the verifier already holds for the namespace
   (`release-continues`): if it holds this release number, the index is the
   same; otherwise release 1 names no previous, and for release N the verifier
   holds release N-1 (fetched from where it found release N), and N names its index as
   `previous`, is dated no earlier, and keeps every ref of its index, a retired
   ref still `retired` — else `NAMESPACE_RELEASE_BROKEN`. A release that passes
   is one the verifier now holds.

### Private and public

A hub's own registry answers for the hub's own tenant: its tenant's namespace
is the first name claimed in it, by the tenant's owner
([`architecture/tenancy`](../architecture/tenancy.md#interfaces)). Holding a
name there gives nothing outside that hub. Publishing under a namespace to
anyone else — a listing, a catalog release offered on the network — needs the
same name held by the same identity at the public registry, where it is first
come like anywhere else.

A holder MAY show that it controls a DNS name; a registry that checks this
records it beside the namespace as a badge. A badge never decides who holds a
name. How it is proven is not specified yet.

### Endpoints

| Method | Path | Operation | Purpose |
|--------|------|-----------|---------|
| POST | /v1/namespaces | ClaimNamespace | A claim: the statement's fields, its signature, the claimant's public key |
| GET | /v1/namespaces/{namespace} | ShowNamespace | The namespace's state, holder, grants and badge, and the seq of each entry they come from |
| POST | /v1/namespaces/{namespace}/grants | GrantNamespace | A grant, signed by the holder |
| POST | /v1/namespaces/{namespace}/transfers | TransferNamespace | A transfer, rotation or retirement, with its signatures |
| GET | /v1/namespace-log | RegistryLog | The log's stored lines from a given seq, and its latest checkpoint |

No fixed path segment sits where `{namespace}` does, since any word the
grammar accepts can be claimed: the log is read at its own path.

A refusal is an `ErrorResponse` whose `code` is one of the codes below. A
read needs nothing but a way to reach the registry — the public registry serves
anyone, a hub's own registry whoever may reach that hub — because the log
proves itself.

---

## Error Handling

| Code | Status | When |
|------|--------|------|
| `NAMESPACE_MALFORMED` | 400 | Unknown prefix, wrong field count, or a field not in its form; for a release, an index that is not its digest's or not in its form |
| `NAMESPACE_WRONG_REGISTRY` | 400 | `<registry>` names another registry's log |
| `NAMESPACE_SIGNATURE_INVALID` | 401 | A signature does not verify under the key it names |
| `NAMESPACE_STATEMENT_STALE` | 400 | `issued_at` is outside the replay window of the registry's clock; a release's `released_at` is further ahead of the verifier's clock than that window |
| `NAMESPACE_STATEMENT_REPLAYED` | 409 | The log already holds these bytes |
| `NAMESPACE_INVALID` | 400 | The name is not in the namespace grammar |
| `NAMESPACE_RESERVED` | 403 | A reserved name, place code or issuer code |
| `NAMESPACE_CONFUSABLE` | 403 | A name whose skeleton is a reserved name's |
| `NAMESPACE_HELD` | 409 | The name is held or frozen |
| `NAMESPACE_RETIRED` | 410 | The name was retired, and stays retired |
| `NAMESPACE_UNKNOWN` | 404 | No claim for the name was ever accepted |
| `NAMESPACE_FROZEN` | 423 | A ruling froze the namespace |
| `NAMESPACE_NOT_HOLDER` | 403 | Not signed by the holder the act needs |
| `NAMESPACE_TRANSFER_ONE_SIDED` | 403 | A transfer or rotation without the incoming holder's signature |
| `NAMESPACE_IDENTITY_UNKNOWN` | 403 | The holder, grantee or incoming holder, a reassignment's included, is not enrolled at this hub, or is revoked |
| `NAMESPACE_SERVICE_IDENTITY` | 403 | A service identity as claimant or incoming holder, a reassignment's included |
| `NAMESPACE_NOT_PUBLISHER` | 403 | A release signed by neither the holder nor a `publish` grantee at its `released_at` |
| `NAMESPACE_RELEASE_BROKEN` | 409 | A release that does not continue the one before it: a number out of turn, another `previous`, an earlier date, a ref dropped or a retired ref given a digest, or a second index for one number |

---

## Test Vectors

The four statements have vectors in
[`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json),
with every other fixed-form statement. The registry's decisions have their own,
[`vectors/namespace-registry.json`](../vectors/namespace-registry.json):
sequences of statements and rulings, each step with the verdict this pattern
gives it and each sequence with the state it leaves. Every implementation of a
registry, and every verifier of a release, is bound by both.

---

## Implementation Notes

- A request carries the public key of each signer; the fingerprint a
  signature names is checked against it, and an enrolled identity's key is the
  one its hub enrolled ([`patterns/principal-identity`](principal-identity.md)).
- Deciding and appending are one serialised step, as every append to a sealed
  log is, so two claims of one name cannot both be accepted.
- A registry with no tenant to serve still runs: a public registry has no
  tenant namespace, and its first claim is whoever comes first.
- Which component of a tenant serves this pattern is not yet declared, which is
  why the pattern is `adoption: opt-in`.

---

## Verification Checklist

- [ ] Every vector for the four prefixes verifies with OpenSSL, circl and noble, and in each of the three every vector fails with one byte of its message changed ([`checks/statements.py`](../checks/statements.py), [`checks/ml-dsa`](../checks/ml-dsa/main.go))
- [ ] Every step of every registry vector gets its stated verdict, and every sequence leaves its stated state ([`checks/namespace-registry.py`](../checks/namespace-registry.py))
- [ ] A second claim of a held name, a reserved or confusable name, a one-sided transfer and a claim of a retired name are each refused with their code
- [ ] A rotation keeps the claim and its grants; a transfer ends the grants
- [ ] A statement made at one registry is refused at every other
- [ ] Nothing is appended for a refused statement, and an accepted one is in the log before the answer
- [ ] A release is judged at its own `released_at`: one made before a rotation, a transfer or a withdrawn grant still verifies after it, and the old key cannot release after it
- [ ] A release whose index drops a ref, revives a retired one, skips a number, names another `previous`, is dated before the release it follows, or gives a held number a second index is refused with `NAMESPACE_RELEASE_BROKEN`
