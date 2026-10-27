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
are defined here, each an act at one registry, which decides it and, if it is
accepted, records it in its log:

| Statement | Signed by | Does |
|---|---|---|
| `weblisk/namespace-claim/v1` | the claimant | takes an unheld name, first come |
| `weblisk/namespace-grant/v1` | the holder | lets another identity publish under the namespace, or withdraws that |
| `weblisk/namespace-transfer/v1` | the outgoing and the incoming holder; for a retirement, the outgoing holder alone | hands the namespace on, follows a key rotation, or retires it for good |
| `weblisk/catalog-release/v1` | the holder, or an identity it granted `publish` | publishes the index of the namespace's parts at one release, which counts once the registry's log records it |

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
5. **A release is checkable anywhere, and dated by the log.** A catalog release
   needs no hub to verify: its signature, its index and the public log of the
   registry it names are enough. Its time is when that log recorded it, never a
   time its signer wrote, so a key whose authority has ended cannot date a
   release back into the time it had it.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: namespace-registry
      description: Decide claims, grants and transfers, and keep what was decided in a sealed log
      required: true
      rules:
        - Decides each statement, a catalog release included, by the steps of Deciding a statement, in order, giving the first refusal that applies
        - Meets claim-first-come, holder-is-a-person, reserved-and-confusable-refused, transfer-needs-both, retired-never-returns, rotation-keeps-the-binding, statements-bound-to-one-registry, log-is-the-record, release-by-holder-or-publisher and release-continues (Requirements)
        - Gives every step of vectors/namespace-registry.json its stated verdict
    - name: release-verification
      description: Verify a catalog release against the log of the registry it names
      required: true
      rules:
        - Meets release-is-recorded (Requirements)
        - Decides each release by the steps of Verifying a release, in order, giving the first refusal that applies
        - Gives every verify step of vectors/namespace-registry.json its stated verdict
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
  - id: revoked-holder-cannot-act
    level: must
    text: A grant, transfer, rotation or retirement is accepted only while the
      holder who signs it is an identity the hub has enrolled and not revoked.
      A revoked holder's namespace is handed on only by a ruling.
  - id: retired-never-returns
    level: must
    text: A retired namespace is never claimed, granted, transferred or
      released again, by anyone, its last holder included.
  - id: rotation-keeps-the-binding
    level: must
    text: A rotation moves the namespace to the holder's incoming key and keeps
      its claim and its grants. Its incoming key is the same identity's, as the
      hub records an identity across a key rotation; a rotation to another
      identity's key is refused. A transfer to another identity ends every grant
      the outgoing holder made.
  - id: statements-bound-to-one-registry
    level: must
    text: Every claim, grant, transfer and catalog release names the log id of
      the one registry it is made at, and every other registry refuses it.
  - id: log-is-the-record
    level: must
    text: What a registry accepted is exactly what its sealed log holds. It
      appends an accepted statement, with its signatures, before it answers,
      and appends nothing for a refused one.
  - id: release-by-holder-or-publisher
    level: must
    text: A registry accepts a catalog release only when, at its own clock as
      it decides, the namespace is held and not frozen and the release is
      signed by the holder or by an identity the holder has granted publish,
      whose identity the hub has enrolled and not revoked. A time the signer
      wrote never stands in for the registry's clock.
  - id: release-continues
    level: must
    text: A release continues the latest release the registry's log records for
      the namespace. Release 1 is the first and names no previous; release N
      follows release N-1, names its index as previous, and its index keeps
      every ref release N-1's index held, a retired ref still retired. A number
      the log already records is never recorded again.
  - id: release-is-recorded
    level: must
    text: A catalog release verifies only when the sealed log of the registry
      it names holds its exact bytes, signed there by the same key, as an
      accepted entry. A
      release the log does not hold is refused, however it was offered and
      whatever it is dated, and one it holds still verifies after its signer's
      authority ends.
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
"weblisk/catalog-release/v1" 0x00 <registry> 0x00 <namespace> 0x00 <release> 0x00 <index> 0x00 <previous> 0x00 <issued_at>

<release>   the release's number in decimal: 1 for the first, one more for each next
<index>     the digest of the release's index, written sha256:<hex>
<previous>  the previous release's <index>, written the same way; empty for release 1
```

A release is made at a registry, as a claim is: the signer sends it, with the
index's text, and the registry decides it at its own clock
(`release-by-holder-or-publisher`), holds it to the latest release its log
records (`release-continues`), and appends it. A release on the network names
the public registry. Only then does it count: a verifier anywhere refuses a
release that registry's log does not hold (`release-is-recorded`).

That is what makes a change of authority final. `issued_at` is the signer's
word and is only held to the replay window, as every statement's is; when the
release happened is when the log recorded it. So once a rotation, a transfer, a
withdrawn grant or a revocation is in the log, the key it took authority from
cannot release again, dated back or not: the registry refuses it, and no
verifier accepts a release the log does not hold. A release the log recorded
before the change still verifies after it, because the entry it rests on does
not move.

What a verifier must hold to be safe is the registry's log, verified as a
sealed log, up to a checkpoint that includes the release. A verifier that
accepts a release on its signature alone, or on releases fetched beside it, is
not verifying one.

**The index** is UTF-8 text, one line per file and per part the namespace's
catalog holds, each line the item's full ref ([`schemas/names`](../schemas/names.md#the-grammar)),
one space, and either its digest — the file's bytes, or the part's projection
digest ([`patterns/content-identity`](content-identity.md)), written
`sha256:<hex>` — or the word `retired`. Lines are in bytewise order of the ref,
no ref appears twice, each line ends with one line feed, and nothing else is in
the file. A ref in one release's index is in every later one: a ref that
disappears, and a `retired` ref that comes back with a digest, make the later
release refused (`release-continues`). That is how a validator holds a part id
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
  signer the log has not recorded before; for a catalog release, also the
  index's text, so the log alone shows what each release continues;
- a **ruling**: the hub owner's recorded decision to `freeze`, `unfreeze` or
  `reassign` a namespace, with the reason in words and, for `reassign`, the
  incoming holder's fingerprint.

**Rulings** answer what no holder's signature can: a holder who lost the key,
a name taken in bad faith, a dispute. A frozen namespace accepts no grant,
transfer or release until it is unfrozen. A reassignment makes the incoming
identity, which must be an enrolled user, the holder, and ends every grant, as
a transfer does; it changes nothing else, so a frozen namespace stays frozen
under its new holder until a ruling unfreezes it. A ruling never un-retires a
namespace. Every ruling is in the
log with its reason, so it is as visible as any claim.

A namespace's **state** is read from the log alone, in order: `held` by a
holder, with its grants; `frozen`; or `retired`. A name the log never accepted
a claim for is `unheld`.

### Deciding a statement

A registry decides each statement by these steps, in order, and the first that
fails gives the refusal. The registry's clock is `now`.

1. The prefix is one of the four, the field count is the prefix's, and every
   field is in its stated form, `to` empty exactly when `kind` is
   `retirement`; for a release, the index text it carries has the digest
   `<index>` names and is in the index's form (The index) — else
   `NAMESPACE_MALFORMED`.
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
   `<from>` is the holder and has signed (`NAMESPACE_NOT_HOLDER`). The holder
   who signs it is enrolled and not revoked (`NAMESPACE_IDENTITY_UNKNOWN`), for
   a grant, a transfer, a rotation and a retirement alike: a revoked holder's
   namespace moves only by a ruling. A transfer
   or a rotation is signed by `<to>` as well (`NAMESPACE_TRANSFER_ONE_SIDED`).
   `<grantee>` or `<to>` is enrolled and not revoked
   (`NAMESPACE_IDENTITY_UNKNOWN`), and `<to>` is a user
   (`NAMESPACE_SERVICE_IDENTITY`). For a rotation, `<to>` is a key of the same
   identity as `<from>`, as the hub records one identity across a key rotation
   ([`protocol/identity`](../protocol/identity.md#key-rotation),
   [`patterns/principal-identity`](principal-identity.md), identity-rotation) —
   else `NAMESPACE_ROTATION_OTHER_IDENTITY`: a hand-over to another identity is
   a transfer, and ends the grants.
8. For a **catalog release**: the namespace has been claimed
   (`NAMESPACE_UNKNOWN`), is not retired (`NAMESPACE_RETIRED`) and not frozen
   (`NAMESPACE_FROZEN`), all now. It is signed by the holder or by a `publish`
   grantee (`NAMESPACE_NOT_PUBLISHER`), whose identity is enrolled and not
   revoked (`NAMESPACE_IDENTITY_UNKNOWN`). It continues the latest release the
   log records for the namespace (`release-continues`): its number is one more
   than that release's, or 1 when there is none; `<previous>` is that release's
   `<index>`, or empty for release 1; and its index keeps every ref of that
   release's index, a retired ref still `retired` — else
   `NAMESPACE_RELEASE_BROKEN`.

An accepted statement is appended before the registry answers
(`log-is-the-record`). A refusal appends nothing.

A **ruling** carries no holder's signature, but is decided all the same, and
a refused one is not recorded: the namespace has been claimed
(`NAMESPACE_UNKNOWN`) and is not retired (`NAMESPACE_RETIRED`); for
`reassign`, the incoming identity is enrolled and not revoked
(`NAMESPACE_IDENTITY_UNKNOWN`) and is a user (`NAMESPACE_SERVICE_IDENTITY`).
Freezing a frozen namespace, or unfreezing a held one, is recorded and changes
nothing.

### Verifying a release

Anyone may verify a catalog release offered to it, by these steps, in order,
against the sealed log of the registry the release names — the public
registry's, for a release on the network — verified up to a checkpoint as
[Sealing a Chained Log](../architecture/storage.md#sealing-a-chained-log) says:

1. Steps 1 and 3 of Deciding a statement, for its form, the index as the
   verifier fetched it, and its signature.
2. Step 5, for `<namespace>`.
3. The log holds an accepted entry with exactly these bytes, signed there by
   the key this release's signature names — else
   `NAMESPACE_RELEASE_UNRECORDED`.

`issued_at` is not judged here: a release is not refused for being old, and
one the log holds verifies after its signer's authority ends
(`release-is-recorded`). A verifier MAY also re-decide step 8 from the entries
before it, to hold the registry to its own rules; revocation is the hub's
record and not the log's, so that one part of step 8 it takes from the log's
acceptance.

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
| POST | /v1/namespaces/{namespace}/releases | PublishRelease | A catalog release, its signature and its index's text |
| GET | /v1/namespaces/{namespace}/releases/{release} | ShowRelease | A recorded release, its index's text, and the seq of its entry |
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
| `NAMESPACE_STATEMENT_STALE` | 400 | `issued_at` is outside the replay window of the registry's clock |
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
| `NAMESPACE_IDENTITY_UNKNOWN` | 403 | The holder, grantee or incoming holder, a reassignment's included, or a release's signer, is not enrolled at this hub, or is revoked |
| `NAMESPACE_SERVICE_IDENTITY` | 403 | A service identity as claimant or incoming holder, a reassignment's included |
| `NAMESPACE_ROTATION_OTHER_IDENTITY` | 403 | A rotation whose incoming key is another identity's |
| `NAMESPACE_NOT_PUBLISHER` | 403 | A release signed by neither the holder nor a `publish` grantee, as the registry decides it |
| `NAMESPACE_RELEASE_BROKEN` | 409 | A release that does not continue the latest the log records: a number out of turn, a number already recorded, another `previous`, or a ref dropped or a retired ref given a digest |
| `NAMESPACE_RELEASE_UNRECORDED` | 404 | A verifier was offered a release the log of the registry it names does not hold |

---

## Test Vectors

The four statements have vectors in
[`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json),
with every other fixed-form statement. The registry's decisions have their own,
[`vectors/namespace-registry.json`](../vectors/namespace-registry.json):
sequences of statements, rulings and verifications, each step with the
verdict this pattern gives it and each sequence with the state it leaves. Every implementation of a
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
- [ ] A rotation keeps the claim and its grants; a transfer ends the grants; a rotation to another identity's key is refused with `NAMESPACE_ROTATION_OTHER_IDENTITY`
- [ ] A grant, transfer, rotation and retirement signed by a holder whose identity the hub revoked are each refused with `NAMESPACE_IDENTITY_UNKNOWN`, and a reassignment then hands the namespace on
- [ ] A reassignment of a frozen namespace changes its holder and leaves it frozen
- [ ] A statement made at one registry is refused at every other
- [ ] Nothing is appended for a refused statement, and an accepted one is in the log before the answer
- [ ] A release is decided at the registry's clock and counts once its log records it: after a rotation, a transfer, a withdrawn grant or a revocation the old key's release is refused, dated back or not, and a verifier refuses it as `NAMESPACE_RELEASE_UNRECORDED`; a release the log recorded before the change still verifies after it
- [ ] A release whose index drops a ref, revives a retired one, skips a number, reuses a recorded number, or names another `previous` is refused with `NAMESPACE_RELEASE_BROKEN`
