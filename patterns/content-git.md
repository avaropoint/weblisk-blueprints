<!-- blueprint
type: pattern
name: content-git
version: 1.3.0
requires: [architecture/content, patterns/content-identity, protocol/identity, patterns/secrets, patterns/principal-identity]
platform: any
tier: free
adoption: opt-in
-->

# Content Git Backend Pattern

A content backend that keeps each repository as one git repository, and
records every change the content service makes there as exactly one commit.

## Overview

[`architecture/content`](../architecture/content.md) specifies the content
service and names no backend, as its Design Principle 6 requires. This
blueprint specifies two drivers:

- `git`, a store. A backend whose `driver` is `git` keeps each repository it
  holds as one git repository, and the content service records each
  `ContentChange` it makes there as one commit.
- `git-remote`, a replica destination and nothing else. A backend whose
  `driver` is `git-remote` reaches bare git repositories on another host over
  SSH, and the content service pushes a git store's history there, as
  architecture/content's Replicas section describes.

Three terms are used throughout:

- The **store** is the git repository a repository's placement names.
- The **line** is the one branch the store follows. It is chosen once, when the
  repository is declared, and never chosen again.
- The **record mirror** is a bare git repository in the content service's own
  state. It holds every commit the service has recorded, and nothing else
  writes to it.

What this blueprint changes, and what it does not:

- It says what each content operation does on git. It never changes what an
  operation means. That is content.md's, and where the two seem to differ,
  content.md is right.
- The evidence of record is the content service's own record, the
  `ContentChange`. A commit repeats that record for a reader who has only git.
  Nothing here is signed. Signing belongs to the service's change log, not to
  git.
- Git names its objects by SHA-1. Nothing joins on an object id. Every join is
  on the sha256 of the bytes, as
  [`patterns/content-identity`](content-identity.md) requires, and every
  commit carries that digest.

`adoption: opt-in` means a deployment that configures no `git` or `git-remote`
backend serves none of this, and is complete. One that configures either owes
all of what this blueprint says about it.

> **Scope boundary:** this blueprint specifies the content service's git
> drivers. It does not specify a repository any other component keeps, the
> CLI's blueprint cache, or how a person uses git in a working tree the service
> shares with them.

---

## Dependencies

```yaml
requires:
  - blueprint: architecture/content
    version: ">=1.9.0 <2.0.0"
    bindings:
      types:
        - name: ContentChange
          fields_used: [repository, path, operation, before, after, scope, actor, on_behalf_of, approved_by, proposal, separation, version, correlation_id]
        - name: ContentObservation
          fields_used: [repository, path, current_digest, state]
        - name: ContentRepository
          fields_used: [placement, custody, attestations, backend_report]
        - name: ContentAdoption
          fields_used: [digest, entries, backend_report]
        - name: ContentReplica
          fields_used: [destination, state, custody, anonymous_read, attestations, credential, credential_fingerprint, held_path, held_reason, backend_report]
        - name: ReplicaCensus
          fields_used: [digest, unclassified, above_ceiling, reserved, backend_report]
        - name: CensusPath
          fields_used: [path, version]
        - name: Placement
          fields_used: [backend, locator]
        - name: CustodyAttestations
          fields_used: [enumerable_principals, attributable_writes, tamper_evident]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/content-identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ContentIdentity
          fields_used: [algorithm, digest]
      behaviors:
        - name: content-digest
        - name: read-without-mutation
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  # Rules 6 to 10, which hold the replica's private key, and the scope of the
  # quantum-vulnerable ban, which allows it to be classical
  - blueprint: protocol/identity
    version: ">=1.5.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/secrets
    version: ">=1.1.0 <2.0.0"
    bindings:
      behaviors:
        # Where the replica's private key is held
        - name: secret-access
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  # Design Principle 6, which forbids git signing and allows a classical
  # transport credential
  - blueprint: patterns/principal-identity
    version: ">=1.5.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **The record is the evidence; a commit is a copy of it** — What a claim, an
   export or an audit cites is the content service's `ContentChange`. A commit
   repeats it so that a person with only git can read the history. Where a
   commit and the record disagree, the record is right and the commit is
   reported. Nothing is git-signed: git signs with OpenPGP, X.509 or SSH keys,
   and [`patterns/principal-identity`](principal-identity.md) Design Principle
   6 forbids a classical signature on any record meant to outlive the session.

2. **An object id finds; a digest proves** — A git object id is SHA-1, and
   SHA-1 collisions can be made. An id is therefore a locator, the way
   `ContentChange.version` already is. A record joins history by the sha256 of
   the bytes, which anyone can recompute with ordinary tools. An id that
   matches proves nothing.

3. **One record, one commit** — Each `ContentChange` is one commit that
   changes exactly its path. A change made outside the service is its own
   commit. An edit a person has not committed is never swept into a commit
   made for somebody else.

4. **History names a person by a pseudonym** — History is what a replica
   later publishes. An identity id is the same at every hub its person joins,
   so publishing one lets anyone link that person across tenants. A commit
   names each person by a pseudonym, and only the tenant can map it back. A
   service it names is named the same way, so no rule depends on telling the
   two apart.

5. **The store's control state is somebody else's input** — Where another
   authority can reach the store, its configuration, hooks and attributes are
   written by somebody else. The service runs git as though each of them were
   hostile. It reads none of the host's git configuration, and none of the
   store's that could run a program, reach a network or change bytes.

6. **Nothing is repaired automatically** — A store that is not as the service
   left it is reported. It is not reset, merged, rebased or re-checked-out, and
   the service serves nothing from it until a person puts it right. A repair
   the service chose would be a change nobody decided.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: git-store
      description: What a placement names, and how a store comes under governance
      required: true
      rules:
        - A placement's locator names the top level of exactly one git repository, and the whole of it. Establishing or adopting a locator inside a git repository that is not its top level is refused with CONTENT_PLACEMENT_PARTIAL
        - Adopting a store whose git directory, common directory or object store lies outside the locator, that borrows objects through alternates, or that is shallow or a partial clone, is refused with CONTENT_PLACEMENT_PARTIAL. Such a store does not hold its own history
        - establish runs git init with no template, so nothing is copied into the git directory, with the backend's object_format and with default_line as the initial branch, bare when the backend's worktree option is none. The line is left unborn. The service writes no commit, no .gitignore and no README, per architecture/content's rule that it writes nothing into a store it establishes
        - On adopt, the line is the branch the store's HEAD names when the census is taken. The census shows it, and the census digest covers it
        - Adopting a store whose HEAD names no branch, that is in the middle of a merge, rebase, cherry-pick, revert or bisect, whose index has unmerged entries, or whose working tree differs from its line, is refused with CONTENT_LINE_UNSETTLED. A person settles it with git and takes a new census
        - After declaration the service never reads HEAD to choose the line. In a store with a working tree, HEAD is only compared with the line
        - In a store with a working tree, an entry is a file in the working tree, and its bytes are the file's. In a bare store, an entry is a blob on the line, and its bytes are the blob's. Either way a reserved path is not an entry
        - The service moves no ref in the store but the line. It creates no tag and no other branch

    - name: git-change-commit
      description: How one change becomes one commit
      required: true
      rules:
        - Each ContentChange is exactly one commit whose tree differs from its parent's at that change's path and nowhere else
        - The commit is built on a private index, never the person's. The blob is written with hash-object --no-filters, so no attribute can change the bytes recorded. An existing entry keeps its mode, and a new one is 100644
        - The line is moved with update-ref naming the head the commit was built on as the old value, or the empty value on an unborn line. A move that fails means the line moved. If the new head does not descend from the old one, the repository is diverted. Otherwise, if the path on the new head still holds the change's before, the commit is rebuilt on the new head; if it does not, the write is refused with CONTENT_PRECONDITION_FAILED. Nothing is ever merged
        - In a store with a working tree, when the path's bytes in the working tree differ from the line's, the difference is dealt with first. Under shared custody it is recorded as a ContentObservation and committed on its own with Provenance external. Under exclusive custody the write is refused with CONTENT_PRECONDITION_FAILED, returning the line's digest and the working tree's, and nothing is written or committed. A second writer is an anomaly there, which is architecture/data-security's to report, never an observation
        - In a store with a working tree, the file is written after the line has moved, by an atomic replace, and only while it still holds the change's before. A file that no longer does is left alone, and the person's bytes are observed as an external change on top of the commit
        - The person's index is updated for that path only, and only where it recorded the line's previous blob. It is skipped while git's index lock is held
        - The write is durable when the line names the commit, with objects and references synced to stable storage
        - The recorded after is the sha256 of the blob read back from the object store, and in a store with a working tree also of the file read back. ContentChange.version is the commit id
        - Each ContentObservation of state changed or removed that the line does not already hold is committed on its own, with Provenance external. An observation of state unknown commits nothing
        - Commits a person makes on the line themselves are neither rewritten nor committed again. The paths they change are observed through the Reconciliation Flow

    - name: git-commit-identity
      description: Who a commit names, and how
      required: true
      rules:
        - The committer is the content service, under the name it registered with and the address <identity id>@service.invalid, where the identity id is the fingerprint of its key
        - The author of a commit for a ContentChange is the change's actor. The author of a commit for an observation is the content service, and Provenance external says the bytes were not written through it
        - Every identity a commit names other than the content service - the author of a change, On-Behalf-Of and each Approved-By, whether a person's or a service's - is named only by its pseudonym. An identity id, a name or an email address is never written into a commit for one
        - A pseudonym is 16 bytes from a cryptographically secure random source, written as 32 lowercase hexadecimal characters. It is minted the first time an identity is named in a repository, recorded, and never changed or reused. The address beside it is <pseudonym>@pseudonym.invalid
        - The mapping from pseudonym to identity id is held in the content service's own record store, under exclusive custody. It is never written into a store, a commit, the record mirror or a replica
        - Author and committer dates are the time the commit was made, in UTC with a +0000 offset
        - The message is one subject line, a blank line, and the trailers in Commit Form, in that order and no others
        - The service never signs a commit or a tag. It runs every git process with commit.gpgsign and tag.gpgsign set false, so no configuration can sign in its place. A signature a person puts on their own commit is theirs; the service neither relies on it nor removes it

    - name: git-record-join
      description: How a record joins history without trusting SHA-1
      required: true
      rules:
        - A record is joined to a commit only when the sha256 of the bytes the commit holds at the record's path equals the record's after, or, for a delete, when the path is absent and the first parent's bytes there equal the record's before. The bytes are read with cat-file blob, which applies no filter and no text conversion
        - A commit is found by ContentChange.version, or by its trailers where history was rewritten or the reader holds only a copy. Finding it proves nothing until the digest check passes
        - Content-After and Content-Before are the commit's claim. A commit whose bytes disagree with its own trailer is reported and joined to nothing
        - Nothing is joined on an object id alone, and two objects with equal ids are never taken to hold equal bytes
        - For each commit it records, the service keeps an anchor, the sha256 of the commit object's bytes, in its own record store. A commit whose bytes do not hash to its anchor is not the recorded commit, whatever its id
        - Every commit the service records is added to the record mirror, by fast-forward only, with transfer.fsckObjects on. Nothing else writes to the mirror, and no recorded commit is ever pruned from it

    - name: git-reserved-paths
      description: Paths this backend cannot let the content service reach, per architecture/content's third reserved row
      required: true
      rules:
        - A path inside a nested git repository, one below the store's top level that holds its own git directory, is reserved
        - A path the line records as a gitlink or as a symbolic link is reserved
        - In a store with a working tree, a path that is not on the line and that the store's own ignore rules match is reserved. A person told git not to record it, and this backend records everything it holds
        - Every git process runs with core.protectNTFS and core.protectHFS true, so git's own path check refuses the names architecture/content reserves on every host
        - .gitattributes, .gitignore and .gitmodules are entries, not reserved paths. .gitattributes changes nothing the service writes, because it writes blobs with no filters

    - name: git-invocation
      description: How every git process is run
      required: true
      rules:
        - The environment is built from empty. It holds GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=/dev/null, a HOME that is an empty directory of the service's own, GIT_TERMINAL_PROMPT=0, GIT_NO_REPLACE_OBJECTS=1, GIT_LITERAL_PATHSPECS=1 and LC_ALL=C, with GIT_OPTIONAL_LOCKS=0 on every process that only reads
        - The repository is always named with --git-dir, and the working tree with --work-tree where there is one, so git never discovers a repository by walking up the directory tree
        - Every process carries these -c settings, which outrank the store's own configuration - core.hooksPath=/dev/null, core.fsmonitor=false, credential.helper set empty, commit.gpgsign=false, tag.gpgsign=false, protocol.allow=never, transfer.fsckObjects=true, safe.directory set to that repository's exact path, core.fsync=objects,reference, gc.auto=0, core.protectNTFS=true and core.protectHFS=true
        - A process that must reach another repository allows only the transport it needs, on that process alone - file, for the record mirror to fetch from its store; ssh, to push to a replica or ask a replica's head; and, with no credential, the transports of a replica's read addresses, to test anonymous read
        - The service runs only these git commands - init, rev-parse, symbolic-ref, for-each-ref, cat-file, ls-tree, ls-files, check-ignore, hash-object, read-tree, update-index, write-tree, commit-tree, update-ref, merge-base, rev-list, diff-tree with --no-ext-diff and --no-textconv, config reading the store's own file, fetch run in the record mirror from its store, push from the record mirror to a replica, and ls-remote against a replica
        - The service never runs gc, repack or prune on a store, and never checks out, resets, merges, rebases or stashes
        - The git binary is found once, at start, by absolute path. Below version 2.36.0, the release that added core.fsync for references, or where no git is found, the backend is unavailable. The service does not exit, health reports degraded naming the backend and what was found, and every operation on the backend's repositories answers CONTENT_UNREADABLE

    - name: git-control-census
      description: What an adoption census reports about the store's control state
      required: true
      rules:
        - The census reports the line, the head it names, whether the store has a working tree, its object format, and each finding in Control State
        - The report is the census's backend_report, and the census digest covers it without its observed_at, per architecture/content
        - Custody re-verification re-runs the census's control part. A new finding is reported in ContentRepository.backend_report. A condition that would refuse adoption, appearing after it, diverts the repository
        - A remote finding, whether present at adoption or found later, is a copy of the store that no replica declares, and is reported as architecture/content's Effective custody requires

    - name: git-custody
      description: What a git store can demonstrate, per architecture/content's attestation properties
      required: true
      rules:
        - enumerable_principals is never demonstrated by this driver. It cannot list who may read the store's files on the host that holds them
        - attributable_writes is never demonstrated by this driver. A git author is whatever the writer typed
        - tamper_evident is demonstrated only while the record mirror verifies. Every anchored commit is present in it, each hashes to its anchor, and the store's line descends from the mirror's line. Re-verification that finds any of those failing records it false

    - name: git-diverted
      description: When a declared store is not as the service left it
      required: true
      rules:
        - A repository is diverted when its line is missing, when the line does not descend from the record mirror's line, when the store has become partial, or when its backend is unavailable
        - A repository with a working tree is also diverted when HEAD does not name the line, when a merge, rebase, cherry-pick, revert or bisect is in progress, or when the index has unmerged entries
        - While a repository is diverted, every read and write answers CONTENT_UNREADABLE, with identity unknown, never current and never stale. Health reports degraded naming the repository and the reason, and backend_report carries it
        - Nothing is repaired automatically. A diverted repository is served again once the condition has cleared, which is checked on each request and at re-verification

    - name: git-remote-destination
      description: What a git-remote backend is, and how the service reaches it
      required: true
      rules:
        - A git-remote backend is a replica destination and nothing else. A repository declaration whose placement names one is refused with CONTENT_BACKEND_UNKNOWN, because the service holds no store backend of that name
        - Only a repository on a git backend replicates to a git-remote backend, and a git repository replicates to nothing else. Any other pairing is refused with CONTENT_REPLICA_UNSUPPORTED
        - Its root is an ssh URL naming a host and a directory. A replica's locator names a bare repository under it, which a person creates. The service never creates one there
        - The replica's credential is an ssh-ed25519 key pair the service generates for that replica alone. ContentReplica.credential is its public key in OpenSSH form, and credential_fingerprint is its SHA256 fingerprint in the form ssh-keygen prints
        - The key is classical, and protocol/identity allows that for a transport credential - it authenticates one session and signs no record
        - The private key is a long-lived private key, and is held as protocol/identity rules 6 to 10 require of one. Outside development it is never protected by file permissions alone, so patterns/secrets holds it in a store that meets rule 8, never in its default file store. In memory it is zeroised after use
        - The private key is never written to a file, not even for one process. For each git process that reaches a replica, the service starts an ssh-agent of its own, listening on a socket in a directory only the service's own user can reach, loads the key into it from memory with ssh-add reading standard input, and stops the agent when the process ends. ssh selects the key by its public half, which may be written to a file because it is public
        - ssh runs with no configuration file, in batch mode, offering only the replica's key, with no agent but the one the service started for that process, no forwarding, and the host key checked strictly against the backend's host_keys alone, never learning a new one
        - ssh runs with KexAlgorithms set to mlkem768x25519-sha256 alone - ML-KEM-768, from protocol/identity's algorithm table, combined with X25519 - so that a push recorded now cannot be read once classical key exchange is broken
        - A destination whose host key is not among host_keys, or that does not offer that key exchange, cannot be reached. Nothing is presented to it and nothing is sent
        - This driver demonstrates neither exclusive nor shared custody for a destination, and no attestation. A key registered at a destination cannot show who else can read it, and a destination's history is not the service's to vouch for. A replica on a git-remote backend is therefore recorded opaque whatever its declaration claimed, and architecture/content's Derived Scope Ceiling table gives it internal at most

    - name: git-replica-send
      description: How a git store is sent to a replica
      required: true
      rules:
        - What a git store sends is its line. A destination holds only what the service sent when its line is absent or names a commit on the record mirror's line
        - Pushes come from the record mirror, never from the store, and send only commits the service has anchored
        - Each push names one refspec, the commit to send and refs/heads/<line> at the destination. It is never forced and sends no tag and no other ref
        - A commit is a version. It is classified when it is the commit of a ContentChange, found by ContentChange.version, that carries scope or that removes an entry. Every other commit is unclassified - one from before adoption, one the service made for an observation, one a person made on the line
        - The commits a push could send are those reachable from the record mirror's newest anchored commit and not from the destination's head. Before each push, every one of them is checked, oldest first in topological order, as architecture/content's Replica Send Flow requires - every path its whole tree holds, recursively, against architecture/content's reserved names and this blueprint's reserved paths, every gitlink and symbolic link included, and not only the paths it changes; whether it is unclassified and the replica's census did not count it; and whether its scope is above the replica's ceiling
        - The first commit that fails holds the replica, with held_reason reserved-path, unclassified or above-ceiling. held_path is the reserved path it holds, or else the first path, in git's order, that it changes from its first parent. The commit to send is then the newest anchored commit on the record mirror's line that does not descend from it, and nothing is pushed when the destination already holds that commit
        - Before each push the service asks the destination for its line's head with ls-remote, over the same transport. That is the only thing it reads there. It never fetches
        - A destination whose line names a commit that is not on the record mirror's line makes the replica diverged. Its head is recorded in backend_report, and pushing resumes by itself once the destination's line again names a commit on the mirror's line
        - A destination's refs other than its line are not the replica. They are counted in backend_report, and never sent, fetched or removed
        - anonymous_read is tested with ls-remote against the replica's locator at each of the backend's read_addresses, presenting no credential, and with an attempt over the replica's own ssh transport presenting no key. It is refused when every attempt is refused, readable when any lists a ref, and unknown when any cannot finish

    - name: git-replica-census
      description: What a replica census binds for a git store
      required: true
      rules:
        - The versions a replica census counts are the commits reachable from the record mirror's head. Each is checked as a push checks it, and unclassified, above_ceiling and reserved are computed from them. CensusPath.version is the commit id
        - The replica census's backend_report names the line, the record mirror's head, and every distinct author and committer recorded on the commits that would leave, as GitIdentity records
        - A commit a person made on the line carries whatever name and address they gave git, and a replica publishes it. The census lists it so the person confirming has seen it
        - The census digest covers the report without its observed_at, per architecture/content
```

---

## Commit Form

A commit for a change has one subject line, a blank line, and trailers:

```
<operation> <path>

Content-Before: sha256:<hex>
Content-After: sha256:<hex>
Provenance: authored
Correlation-Id: <id>
Proposal: <id>
Separation: independent
Approved-By: <pseudonym>
On-Behalf-Of: <pseudonym>
```

The subject's `<operation>` is `create`, `modify` or `delete`: what the commit
does to the path. The path is written as git writes an unusual path in its own
output with `core.quotePath` on: unchanged when it holds only printable ASCII
other than `"` and `\`, and otherwise in double quotes with C-style escapes. The
subject says nothing else, because it is published with the history.

| Trailer | Value | Present when |
|---|---|---|
| `Content-Before` | The identity of the bytes the path held before, as `sha256:` and 64 lowercase hex | The path held bytes before |
| `Content-After` | The identity of the bytes the path holds in this commit, in the same form. This is the identity trailer, and the join key | The path holds bytes after |
| `Provenance` | `authored` for a `ContentChange`, `external` for an observation | Always |
| `Correlation-Id` | The change's `correlation_id` | The commit records a `ContentChange` |
| `Proposal` | The id of the proposal the change applied | The change applied a proposal |
| `Separation` | The change's `separation` | The change applied a proposal |
| `Approved-By` | The pseudonym of each person in `approved_by`, one trailer each | The change applied a proposal |
| `On-Behalf-Of` | The pseudonym of the change's `on_behalf_of` | The change names one |

The actor has no trailer, because the author is the actor. A commit carries these
trailers and no others.

**Authors are pseudonymous by default.** Writing a person's name in place of their
pseudonym would need that person's recorded consent. This blueprint defines no way
to record it, so a conforming implementation writes a pseudonym for everyone.

---

## Joining a Record to History

A reader holding a `ContentChange` and a copy of the store proves that a commit
holds the recorded change like this, with git and `sha256sum` and nothing of
Weblisk's:

1. **Find.** Take the commit `version` names. If history was rewritten, or the
   reader holds only a copy of the store, find instead the commit that changes
   the record's path and whose `Content-After` equals the record's `after` (for a
   delete, whose `Content-Before` equals its `before`).
2. **Prove.** Run `git cat-file blob <commit>:<path>` and compute the sha256 of
   what it prints. It must equal the record's `after`. For a delete, the path is
   absent from the commit, and the same command against its first parent prints
   bytes whose sha256 is the record's `before`.
3. **Decide.** A match joins the record to the commit. A mismatch joins nothing,
   whatever the id and whatever the trailers say.

SHA-1 is used in step 1 and nowhere else. It helps find a commit and proves
nothing about it. A commit substituted by a SHA-1 collision holds different bytes,
so step 2 fails for it unless someone can also produce a sha256 collision.

The anchor closes the other half. Step 2 binds what the commit holds at the path.
The anchor binds what the commit says: its author, its trailers, and the ids of
its tree and parents. The service checks it by hashing `git cat-file commit <id>`
with sha256 and comparing with the anchor it kept. Neither check relies on SHA-1.

---

## Control State

The census reports each finding below, and custody re-verification looks for new
ones. None is an entry, and none is refused at adoption. A person adopting sees
them and takes them on knowingly.

| Finding | What it is | Why it is reported |
|---|---|---|
| `nested` | A directory below the top level that holds its own git directory | Its paths are reserved, so the content service cannot see them |
| `gitlink` | A gitlink on the line, pointing into another repository | It is reserved, and what it points at is another store |
| `symlink` | A symbolic link on the line | It is reserved |
| `attributes` | An attribute on the line or in the store's `info/attributes` that sets a filter, `text`, `eol`, `ident` or `working-tree-encoding` | The service writes blobs with no filters, but a person's checkout applies them, so the bytes a person sees can differ from the bytes recorded |
| `replace` | A ref under `refs/replace/` | The service ignores it, and a person's git does not, so the two see different history |
| `hook` | An executable in the store's hooks directory | The service never runs it. A person's git runs it |
| `config` | A key in the store's own configuration outside the allowlist in Implementation Notes | Somebody configured the store to do something the service does not expect |
| `remote` | A configured remote | A copy of the store may exist that no replica declares, and it counts toward the repository's effective custody as architecture/content requires |
| `config` for `url.*` | A URL rewrite | It changes where a person's git sends the store, so it is reported whether or not a remote exists yet |

---

## Types

```yaml
types:
  GitBackendOptions:
    description: The options of a backend whose driver is git. They govern
      stores the backend establishes; an adopted store is taken as it is
    fields:
      default_line:
        type: string
        required: false
        description: The line a store this backend establishes follows.
          Default main
      worktree:
        type: enum
        values: [none, attached]
        required: false
        description: none establishes a bare store that only the service
          writes. attached establishes one with a working tree a person may also
          edit, which is shared custody. Default none
      object_format:
        type: enum
        values: [sha1, sha256]
        required: false
        description: The object format of a store this backend establishes.
          Default sha1, which every git host reads. The join key is sha256
          either way

  GitStoreReport:
    description: The backend_report of a git store, on a ContentAdoption and
      on a ContentRepository
    fields:
      line:
        type: string
        required: false
        description: The branch the store follows. Absent in a census when HEAD
          names no branch
      head:
        type: string
        required: false
        description: The commit id the line names. A locator. Absent on an
          unborn line
      worktree:
        type: enum
        values: [none, attached]
        required: true
      object_format:
        type: enum
        values: [sha1, sha256]
        required: true
      state:
        type: enum
        values: [following, unsettled, diverted]
        required: true
        description: following when the store is as the service left it.
          unsettled only in a census, when adoption would be refused with
          CONTENT_LINE_UNSETTLED. diverted only on a declared repository
      reason:
        type: enum
        values: [no-line, head-off-line, operation-in-progress, unmerged, worktree-differs, line-missing, line-rewritten, store-partial, backend-unavailable]
        required: false
        description: Present when state is unsettled or diverted
      differs:
        type: list
        required: false
        description: In a census whose reason is worktree-differs, each path
          whose working-tree bytes differ from the line's, including paths
          on only one side
      findings:
        type: list
        required: true
        description: GitFinding records. Empty means none was found
      observed_at:
        type: timestamp
        required: true
        description: When the report was taken. The census digest does not
          cover it

  GitFinding:
    description: One thing the census found in a store's control state
    fields:
      kind:
        type: enum
        values: [nested, gitlink, symlink, attributes, replace, hook, config, remote]
        required: true
      path:
        type: string
        required: false
        description: Where it was found, relative to the store's top level or
          its git directory
      key:
        type: string
        required: false
        description: For config and remote, the configuration key
      detail:
        type: string
        required: false

  AuthorPseudonym:
    description: The tenant's mapping from a pseudonym to the identity it
      stands for. Held in the content service's own record store and never
      in a store, a commit, the record mirror or a replica
    fields:
      repository:
        type: string
        required: true
      identity_id:
        type: string
        required: true
      pseudonym:
        type: string
        required: true
        description: 32 lowercase hexadecimal characters from 16 random bytes.
          Never changed and never reused
      minted_at:
        type: timestamp
        required: true

  GitRemoteOptions:
    description: The options of a backend whose driver is git-remote
    fields:
      host_keys:
        type: list
        required: true
        description: The destination host's public keys, in known_hosts form.
          The only keys ssh accepts from it. Never learned on first use
      read_addresses:
        type: list
        required: false
        description: Every other address at which a stranger could read a
          repository under this root, as a URL the locator is appended to.
          anonymous_read is tested at each. An address not listed is one the
          service cannot know of

  GitReplicaCensusReport:
    description: The backend_report of a ReplicaCensus for a git store
    fields:
      line:
        type: string
        required: true
      head:
        type: string
        required: false
        description: The record mirror's head. A locator. Absent on an unborn
          line
      authors:
        type: list
        items: GitIdentity
        required: true
        description: Every distinct author and committer recorded on the
          commits that would leave
      observed_at:
        type: timestamp
        required: true
        description: The census digest does not cover it

  GitIdentity:
    description: A name and address as a commit records them, for an author
      or a committer
    fields:
      name:
        type: string
        required: true
      address:
        type: string
        required: true
        description: What the commit holds between the angle brackets, as it
          holds it. For a commit the service made, a pseudonym's or its own
          .invalid address

  GitReplicaReport:
    description: The backend_report of a ContentReplica on a git-remote backend
    fields:
      destination_head:
        type: string
        required: false
        description: What the destination's line named when last asked. Absent
          when it has none. A locator
      other_refs:
        type: integer
        required: false
        description: How many refs other than the line the destination holds,
          when last asked. Absent when unknown
      observed_at:
        type: timestamp
        required: true

  RecordAnchor:
    description: The sha256 of one recorded commit object, kept by the service
      so the commit can be recognised without trusting its id
    fields:
      repository:
        type: string
        required: true
      version:
        type: string
        required: true
        description: The commit id. A locator
      commit_digest:
        type: ContentIdentity
        required: true
        description: sha256 over the bytes git cat-file commit prints for it
      recorded_at:
        type: timestamp
        required: true
```

---

## Configuration

```yaml
content:
  backends:
    - name: <backend-name>
      driver: git
      root: <absolute directory on the content service's host>
      options:                   # GitBackendOptions
        default_line: main
        worktree: none           # none | attached
        object_format: sha1      # sha1 | sha256

    - name: <backend-name>
      driver: git-remote
      root: ssh://<host>[:<port>]/<directory>/
      held_by: tenant            # tenant | third-party. Absent is third-party
      options:                   # GitRemoteOptions
        host_keys:
          - <known_hosts line>
        read_addresses: []
```

A `git` backend's `root` is a directory. A placement's locator names a store
inside it, as architecture/content's Placement rule requires. The service keeps
each store's record mirror, pseudonyms and anchors in its own state, never under
`root`.

A `git-remote` backend's `root` names a host and a directory on it, and a
replica's locator names a bare repository in that directory. `held_by` is the
operator's statement of who holds that host; a copy on a machine the tenant
owns is `tenant`.

---

## Error Handling

| Code | Category | When | Behaviour |
|---|---|---|---|
| `CONTENT_PLACEMENT_PARTIAL` | validation | On establish or adopt, the locator is inside a git repository and is not its top level; or, on adopt, the store's git directory, common directory or objects lie outside the locator, it borrows objects through alternates, or it is shallow or a partial clone | Refuse. Create nothing and adopt nothing. A placement governs a whole store or none of one |
| `CONTENT_LINE_UNSETTLED` | conflict | On adopt, HEAD names no branch, an operation is in progress, the index has unmerged entries, or the working tree differs from the line | Refuse, with the census, whose `backend_report` says why. Declare nothing |

A diverted repository, and one whose backend is unavailable, answers with
architecture/content's `CONTENT_UNREADABLE`. A move of the line that loses to a
change at the same path answers with its `CONTENT_PRECONDITION_FAILED`, and so
does a write under exclusive custody to a path whose working-tree bytes differ
from the line's, returning both of those digests.

---

## Implementation Notes

- **Invoke the git binary; do not link a git library.** A library reimplements
  git's object, index and ref formats, and nobody reading this blueprint can tell
  which version of git's behaviour it copied. The hardening above is written
  against git itself.

- **The configuration allowlist is small on purpose.** These keys in a store's
  own configuration are not reported as findings: `core.repositoryformatversion`,
  `core.bare`, `core.filemode`, `core.logallrefupdates`, `core.ignorecase`,
  `core.precomposeunicode`, `core.symlinks`, `extensions.objectformat` and
  `extensions.refstorage`. Everything else is reported. A key the service's `-c`
  settings already override is still reported, because a person's git obeys it.

- **Build every commit on a private index.** Point `GIT_INDEX_FILE` at a file of
  the service's own, `read-tree` the line's head into it (or `read-tree --empty`
  on an unborn line), apply the one change, and `write-tree`. Using the person's
  index would sweep in whatever they had staged.

- **Move the line last, then touch the working tree.** Writing the file first
  and losing the race on the line leaves the working tree holding bytes no commit
  holds, which the next reconcile would record as somebody else's edit.

- **Feed the record mirror by fast-forward only.** A recorded commit the mirror
  cannot fast-forward to means the line was rewritten, and that is a diversion
  to report, not a push to force.

- **Nothing here compacts a store.** `gc.auto=0` stops git from starting a
  collection as a side effect. A collection in a store another authority uses
  can prune the only copy of history the line no longer names.

- **A pseudonym is per repository.** The same person has a different pseudonym
  in each repository, so two published histories cannot be linked to each other
  by their authors either.

> **Gap.** Nothing here accepts a rewrite. A line moved to a commit that does
> not descend from the record mirror's line stays diverted until a person moves
> it back to a descendant. Accepting the rewrite would mean a person deciding
> that recorded history the line no longer holds is withdrawn, and the records
> of it would still stand. No verb for that is specified, and this line says so
> rather than leaving it to be guessed.

---

## Verification Checklist

- [ ] After `establish`, the store has an unborn line named `default_line`, no commit, and no file outside its git directory, and a census over it has `entries` 0
- [ ] A `ContentChange` produces exactly one commit, whose tree differs from its parent's only at the change's `path`
- [ ] The commit's author is the actor's pseudonym and its committer is the content service; neither is an identity id, a name or a real email address
- [ ] The same identity gets the same pseudonym on every commit in one repository, and a different one in another repository
- [ ] The sha256 of `git cat-file blob <version>:<path>` equals the change's `after` and the commit's `Content-After`
- [ ] A commit's `Content-After` that disagrees with the bytes at its path is reported and joined to no record
- [ ] With a signing key and `commit.gpgsign=true` in the host's global git configuration, a commit the service makes carries no signature
- [ ] A hook the store's configuration names, and a `core.fsmonitor` program, are not run by any operation of the service
- [ ] A person's uncommitted edit to one path is not included in a commit the service makes for another path
- [ ] A write racing a person's commit that changed the same path is refused with `CONTENT_PRECONDITION_FAILED`, and the line keeps the person's commit
- [ ] Adopting a subdirectory of a git repository is refused with `CONTENT_PLACEMENT_PARTIAL`, and so is adopting a store that uses alternates or is shallow
- [ ] Adopting a store with a detached HEAD, or whose working tree differs from its line, is refused with `CONTENT_LINE_UNSETTLED`, and the census's `backend_report` names the reason
- [ ] An adoption whose store gained a configured remote after the census is refused with `CONTENT_PRECONDITION_FAILED`
- [ ] After a person resets the line to an earlier commit, every read and write answers `CONTENT_UNREADABLE`, health reports degraded naming `line-rewritten`, and nothing in the store is changed by the service
- [ ] A path inside a nested repository, and a path the line records as a symbolic link, are refused with `CONTENT_RESERVED_PATH`
- [ ] With git below 2.36.0 on the host, the service starts, health reports degraded naming the backend, and reads of its repositories answer `CONTENT_UNREADABLE`
- [ ] `tamper_evident` is false after an anchored commit is removed from the record mirror, and the ceiling is recomputed
- [ ] A replica on a `git-remote` backend returns `credential` as an OpenSSH `ssh-ed25519` public key, and the private key appears in no response, log or event, and in no file at any time, including while a push runs
- [ ] Outside development, a replica's private key is held in a store that meets `protocol/identity` rule 8, never under file permissions alone
- [ ] A replica on a `git-remote` backend whose declaration claims `exclusive` custody and every attestation is recorded `custody` `opaque`, with every attestation `false` and a `ceiling` no higher than `internal`
- [ ] Under exclusive custody with a working tree, a write to a path a person edited in the working tree is refused with `CONTENT_PRECONDITION_FAILED` returning the line's and the working tree's digests, and no commit is made
- [ ] A change whose `actor` is a service's identity id names that service by its pseudonym as author, never by its identity id
- [ ] A push to a replica is made from the record mirror, names one refspec for the line, is never forced, and sends no tag
- [ ] A destination whose host key is not in `host_keys`, or that does not offer `mlkem768x25519-sha256`, is sent nothing and is not presented the key
- [ ] A destination whose line was moved to a commit not on the record mirror's line makes the replica `diverged`, records the destination's head in `backend_report`, and receives nothing more until its line again names a commit on the mirror's line
- [ ] No operation fetches from a replica
- [ ] A replica census over a store whose history holds a commit a person made with a real address lists that name and address in `backend_report`
- [ ] A person's commit on the line, made after a replica was confirmed, that adds `.weblisk/secrets/x`, a gitlink or a symbolic link holds the replica `behind` with `held_reason` `reserved-path` naming the path; the commit is never pushed, and neither is any anchored commit that descends from it
- [ ] A commit the service made for an observation after a replica's census holds the replica `behind` with `held_reason` `unclassified`, and the push sends the newest anchored commit before it
- [ ] A repository declaration whose placement names a `git-remote` backend is refused with `CONTENT_BACKEND_UNKNOWN`
- [ ] A store with a configured remote reports a `remote` finding, and its repository's `effective_custody` is `opaque`
