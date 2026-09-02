<!-- blueprint
type: pattern
name: content-identity
version: 1.0.0
requires: [protocol/types, patterns/versioning]
platform: any
tier: free
-->

# Content Identity Pattern

Defines how an artifact is identified by the bytes it contains rather than by
where it is stored, so that a reference to it can be verified independently, and
so that anything derived from it becomes knowably stale when it changes.

## Overview

A system that records relationships between artifacts — this procedure
implements that policy, this evidence answers that control — must answer two
questions long after the fact: *which version was that*, and *is it still
true*. Referring to an artifact by path or name answers neither. Paths move,
names change, and a reference that survives both changes silently now points at
something nobody checked.

This pattern makes the CONTENT the identity. The digest of an artifact's exact
bytes is its version identity, computed the same way by every party, verifiable
with a general-purpose tool and no knowledge of the system that produced it.

Two consequences follow, and both are the point:

- **A reference can be verified by a stranger.** An auditor holding a file and a
  recorded relationship recomputes the digest and knows whether they hold the
  version that was cited. No parser, no API, no trust in the recorder.
- **Staleness is derived, never stored.** If an edge records the digest of what
  it cited, and the artifact's current digest differs, the edge is stale. This
  is computed on read, so it cannot drift, cannot be forgotten on write, and
  cannot be wrong.

The pattern is deliberately narrow. It says how identity is computed and what
that identity obliges; it does not say what artifacts are, how they are stored,
or what relationships mean.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/versioning
    version: ">=1.0.0 <2.0.0"
    bindings:
      behaviors:
        - name: version-declaration
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Identity is computed from bytes, not assigned** — An artifact's version
   identity is the digest of its exact serialized bytes. No component assigns
   it, no registry allocates it, and two parties holding the same bytes compute
   the same identity without communicating. An identity that must be looked up
   is a coordinate, not an identity.

2. **The digest is the join key** — Where a system records history, references,
   signatures or evidence, those records MUST join on the content digest. Joining
   on a path or a name means a rename silently re-points every record that used
   it. This is the difference between a citation and a guess.

3. **Never rewrite an artifact on read** — Opening, parsing, indexing or
   displaying an artifact MUST NOT change its bytes. A system that normalises on
   open changes the identity of everything it touches, at a moment nobody
   authored, invalidating every recorded reference and every signature at once.
   Deferred corrections are applied on the next authored write, never before.

4. **Staleness is derived, never stored** — Whether a reference is current is
   computed by comparing the digest it recorded against the artifact's digest
   now. It MUST NOT be persisted as a flag. A stored flag is a cache of a fact
   that changes without notice, and a wrong "current" is worse than no answer.

5. **Verifiable without the producing system** — The digest algorithm MUST be a
   published standard computable by ordinary tools. A holder of the bytes and
   the recorded digest can verify a citation with no access to the system that
   made it. Capability may live in the platform; verifiability must not.

6. **Retirement, not deletion** — When an identified artifact or part is
   removed, its identity is retired and MUST NOT be reused. A reference to a
   retired identity resolves to "removed at version N", never to nothing and
   never to something else. Reuse turns a dangling reference into a false one.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: content-digest
      description: Compute an artifact's version identity from its bytes
      required: true
      rules:
        - The digest MUST be computed over the exact serialized bytes as stored
        - The algorithm MUST be declared alongside the digest, never assumed
        - Implementations MUST NOT normalise, reformat or reorder before hashing
        - The same bytes MUST produce the same digest on every platform

    - name: reference-with-version
      description: Record a reference that names what it saw
      required: true
      rules:
        - A reference MUST record the digest of the artifact as it was when cited
        - A reference MUST record the artifact's stable identifier as well, so a
          stale reference can still locate what it referred to
        - A reference MUST NOT be expressed as a path alone

    - name: staleness-evaluation
      description: Decide whether a reference is still current
      required: true
      rules:
        - Staleness MUST be computed by comparing recorded and current digests
        - Staleness MUST NOT be persisted
        - An artifact that cannot be read yields "unknown", never "current"

    - name: read-without-mutation
      description: Reading never changes identity
      required: true
      rules:
        - Any read path MUST leave the stored bytes unchanged
        - Deferred normalisation MUST be applied only during an authored write
        - A system MUST be able to demonstrate this by digesting before and after
          a full read pass over a corpus

  guarantees:
    - Two parties with the same bytes agree on identity without coordinating
    - A citation names a version, not a location
    - No reference reports "current" about content it has not compared
    - A removed identity is never reused
```

---

## Types

```yaml
types:
  ContentIdentity:
    description: The version identity of an artifact
    fields:
      algorithm:
        type: string
        required: true
        description: Published digest algorithm, e.g. "sha256". Declared, never assumed
      digest:
        type: string
        required: true
        description: Lowercase hex digest of the exact stored bytes
      size:
        type: integer
        required: false
        description: Byte length. A cheap mismatch check before hashing

  VersionedReference:
    description: A reference that records what it saw
    fields:
      target_id:
        type: string
        required: true
        description: Stable identifier of the artifact — survives rename and move
      target_version:
        type: ContentIdentity
        required: true
        description: The artifact's identity when the reference was recorded
      recorded_at:
        type: timestamp
        required: true
      recorded_by:
        type: string
        required: true

  StalenessVerdict:
    description: Derived on read. Never stored
    fields:
      state:
        type: enum
        values: [current, stale, unknown, retired]
        required: true
        description: unknown when the target could not be read; retired when its
          identity was withdrawn
      recorded_digest:
        type: string
        required: true
      current_digest:
        type: string
        required: false
        description: Absent when state is unknown or retired
```

---

## Error Handling

| Code | Category | When | Behaviour |
|------|----------|------|-----------|
| `algorithm_unknown` | validation | Recorded algorithm is not supported | Verdict is `unknown`. MUST NOT assume a default algorithm |
| `target_unreadable` | io | The artifact cannot be read | Verdict is `unknown`, never `stale` and never `current` |
| `target_retired` | validation | The identity was withdrawn | Verdict is `retired`, naming the version at which it went |
| `identity_reused` | integrity | A retired identity reappears | Reject and log as an integrity fault — this breaks Design Principle 6 |
| `mutation_on_read` | integrity | Digest changed across a read-only pass | Reject and log. Every reference in the system is now suspect |

`unknown` is a first-class answer. An implementation that reports `current`
because it could not check has stated something it does not know, which this
pattern exists to prevent.

---

## Implementation Notes

**Hash what is stored, not what is parsed.** The digest must be taken over the
bytes on disk or on the wire. Hashing a parsed and re-serialised form makes the
identity depend on the serializer's version, so an unrelated library upgrade
invalidates every recorded reference at once.

**The read-without-mutation rule is easy to violate accidentally.** Normalising
line endings, sorting keys, adding a missing identifier, or rewriting an index
on open all breach it. Implementations SHOULD carry a test that digests a corpus,
performs a full read pass, and digests again — the two sets must be identical.
That test is cheap and catches an entire class of silent corruption.

**Size before digest.** Comparing byte length first rejects most mismatches
without reading the whole artifact, which matters when staleness is evaluated
across a large corpus on every read.

**Stable identifier and content identity are different things, and both are
required.** The stable identifier answers "which artifact", survives rename and
move, and is never derived from a path. The content identity answers "which
version". A reference carrying only the first cannot detect change; one carrying
only the second cannot locate its target after an edit.

**This pattern does not define relationships.** It defines how a reference names
a version. What a relationship MEANS — implements, evidences, supersedes — and
what a system does when one goes stale belong to the domain that records them.

---

## Verification Checklist

1. The same bytes hashed on two platforms produce identical digests.
2. A recorded reference whose target is unchanged evaluates to `current`.
3. Editing the target by one byte makes the same reference evaluate to `stale`.
4. Renaming or moving the target leaves the reference resolvable and `current`.
5. A full read pass over a corpus leaves every artifact's digest unchanged.
6. An unreadable target yields `unknown`, and never `current` or `stale`.
7. Staleness appears in no persisted record — searching storage for a staleness
   field returns nothing.
8. A retired identity resolves to `retired` with the version at which it was
   withdrawn, and never to a different artifact.
9. Reusing a retired identity is rejected with `identity_reused`.
10. A digest recorded with an unsupported algorithm yields `unknown` rather than
    being verified under an assumed default.
