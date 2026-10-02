<!-- blueprint
type: protocol
name: secret-source
version: 1.3.0
requires: [protocol/identity, patterns/principal-identity]
platform: any
tier: free
-->

# Weblisk Secret Source Protocol

How a Weblisk component keeps a secret in whatever store its owner already
uses — a keychain, a vault, a hardware token, or no store at all — without
knowing which one it is.

## Overview

A **secret source** is a store that keeps secrets for a caller and gives them
back when asked: an operating system's keychain, a password vault, a cloud
secrets manager, a hardware token. A **caller** is the Weblisk component that
needs the secret — the CLI, for an operator identity; a console, for the secrets
of its own installation; a service, for the passphrase of its key.

This protocol makes every source look the same to a caller. A source has a name
and answers a small set of requests. A caller that speaks the protocol can use a
source it has never heard of, and nothing in the caller changes when its owner
changes vault, or stops using one.

**A source is always optional.** An identity kept in an encrypted key file, with
a passphrase a person types, needs no source at all
([`protocol/identity`](identity.md#key-management)). A source moves a secret
somewhere better protected. It is never the only way to hold one.

This document specifies:

- the **source contract** — what every source answers, however it is reached
- **discovery** — how a caller finds the program that speaks for a source
- the **holder reference** — how a caller records where an identity is held,
  without recording the secret
- the **wire protocol** — one request, one response, and seven error codes
- **signing** — when a caller receives a private key, and when it never does
- **protection** — which `key_protection` value each way of holding a key earns
- **where a secret is never stored**

**The subject of this protocol is a platform facility.** It starts a program and
speaks to it over that program's standard input and output, which is the
exception [`schemas/common`](../schemas/common.md#platform-neutrality) allows.
Where a runtime cannot start a process — a Worker, for one — there are no
helpers. Only the sources an implementation carries built in exist there, and
the platform blueprint names them.

> **Scope boundary:** the key format, the key-derivation function, and the rules
> for what may protect an identity key belong to
> [`protocol/identity`](identity.md). What an identity, a credential and
> `key_protection` *are* belongs to
> [`patterns/principal-identity`](../patterns/principal-identity.md). How an
> agent declares and reads its own secrets belongs to
> [`patterns/secrets`](../patterns/secrets.md). This document states how a
> secret is reached. It names no vault product's interface, and which keychain a
> platform offers, and how a source talks to it, is implementation.

---

## Dependencies

```yaml
requires:
  # Fixed-form statements, which a caller builds before it asks a source to
  # sign, and the holder probe registered there
  - blueprint: protocol/identity
    version: ">=1.7.0 <2.0.0"
    bindings:
      types:
        - name: SigningKeyPair
          fields_used: [algorithm, public_key, private_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/principal-identity
    version: ">=1.1.0 <2.0.0"
    bindings:
      types:
        - name: Identity
          fields_used: [kind, key_protection]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Conventions

- A helper MUST read exactly one request from its standard input, as one JSON
  object (RFC 8259) in UTF-8, write exactly one response to its standard output
  as one JSON object, and then exit.
- **The response governs, never the exit status.** When a helper has written a
  valid `SecretSourceResponse`, that response is its answer, and the caller
  ignores how the helper exited. A helper that writes
  `{"error": {"code": "not_found", …}}` and exits 1 has answered `not_found`.
  A helper that wrote no valid response has not spoken this protocol
  ([Error Handling](#error-handling)).
- Every secret value, message and signature on the wire is base64url without
  padding (RFC 4648 §5), the encoding [`protocol/identity`](identity.md) uses for
  every key and signature. A value is carried as bytes; how a source stores it
  internally is its own.
- Nothing from a request is ever placed on a helper's command line or in its
  environment. The command line is fixed by discovery, before any request
  exists.
- A source name matches `[a-z0-9][a-z0-9-]*` and is at most 64 characters, so
  one name maps to one program name on every filesystem.
- Every request carries `version: 1`. A helper MUST answer a version it does not
  speak with `unsupported`. A helper ignores request fields it does not know; a
  caller ignores response fields it does not know.
- How long to wait for a helper is the caller's decision, never the helper's
  (see [Security](#security)).

---

## Sources

### The source contract

Every source answers the same actions, however it is reached:

| Action | Asks for | Answers with | Required of a source |
|---|---|---|---|
| `capabilities` | what this source can do | `actions`, `sign_algs`, `named_fields`, `withheld_fields` | Yes |
| `get` | one secret, by reference and field | `value` | Yes, for every field the source does not withhold |
| `store` | keep these fields, somewhere the source chooses | `reference` | No |
| `erase` | forget what a reference names | an empty object | No |
| `sign` | an ML-DSA-65 signature from a key that never leaves the source | `signature` | No — OPTIONAL |

A source lists the actions it answers in `capabilities`. A caller MUST ask for
`capabilities` before it uses `store`, `erase` or `sign`, and a source MUST
answer an action it did not list with `unsupported`.

`named_fields` says whether one reference holds several named values, as a vault
item holds fields, or exactly one. An identity held whole needs a source with
named fields. A source without them holds one value per reference — a
passphrase, or a master key.

`withheld_fields` names the fields a source holds and never releases through
`get`, whatever the reference. A hardware token that signs lists `private_key`.
A source MUST answer `get` of a withheld field with `unsupported`. Every field
not listed is one the source releases.

A `capabilities` response that leaves a field out is read as the smaller claim:
`named_fields` false, `sign_algs` empty, `withheld_fields` empty.

**A source never puts a secret where another process can read it.** A
source, built in or a helper, MUST NOT place a secret value, a passphrase or a
key on the command line or in the environment of any program it runs, its
store's own command-line tool included. It hands one to that program on the
program's standard input, or through an interface no other process can read,
such as a library call or a descriptor it opened. A store whose tool takes a
secret only as an argument is not written through that tool: a keychain's
command that sets a password from its command line, such as `security
add-generic-password -w <value>` or `cmdkey /pass:<value>`, puts on view to
every local process the very passphrase a source keeps beside an identity
(see [An identity held by a source](#an-identity-held-by-a-source)).

A source is reached in one of two ways, and a caller cannot tell them apart on
the wire:

- **Built in** — the implementation carries it. A built-in source MUST answer
  exactly as a helper would: the same requests, responses and codes. Being built
  in changes how a source is reached, never what it says.
- **A helper** — a separate program that speaks this protocol for one source.

A **keychain** — the store an operating system keeps for its user's secrets — is
one kind of source. So are a password vault, a cloud secrets manager and a
hardware token. None is required, and none is special.

### The built-in sources

| Source | Carried by | Holds |
|---|---|---|
| `1password` | the CLI | what its vault item holds, as named fields |
| `file` | every caller that runs unattended | one value, read from a file ([Headless references](#headless-references-file-and-fd)) |
| `fd` | every caller that runs unattended | one value, read from an inherited file descriptor |
| `keychain` | the CLI, on each platform below | an identity whole, or only its passphrase where the person asks ([An identity held by a source](#an-identity-held-by-a-source)) |

**The CLI MUST carry a `1password` source built in, and MUST reach it through
this protocol.** That makes it the protocol's first user: every request the CLI
makes of 1Password is one a helper could answer, so nothing about 1Password is
known outside that source. It needs nothing installed beyond the vault's own
command-line tool, and answers `not_installed` where that tool is missing.

**The CLI MUST carry a `keychain` source built in** for its platform's
keychain, reached through this protocol as every source is: macOS's first,
then the Secret Service on Linux, then Windows', in that order. It holds an
identity whole unless the person asks it to remember only the passphrase. On
a platform it carries none for, it answers `not_installed`. No CLI carries
one yet, so until it does, a person who wants a keychain names a helper that
speaks for it.

### Discovery

A caller finds what speaks for a source by the source's name. It looks in this
order and uses the first it finds:

1. **The registry** — `~/.weblisk/secret-sources.json`, in the home directory of
   the user the caller runs as. Each entry is a `SecretSourceRegistryEntry`,
   keyed by source name.
2. **A built-in source** of that name.
3. **A program on the search path** named `weblisk-secret-<name>`. An empty or
   relative entry in the search path is skipped. Each names the current
   directory, which is wherever the caller happened to be started.

The registry comes first because it is a person's explicit choice. A built-in
comes before the search path so that a program which happens to appear on the
path cannot quietly take over a source the caller already speaks for; replacing
a built-in is done deliberately, in the registry.

`file` and `fd` are never looked up. The caller reads them itself, and a registry
entry or a program on the path with either name is ignored.

When nothing is found, the caller reports `not_installed`, naming the source and
the program name it looked for.

```json
{
  "team-vault": {
    "command": ["/usr/local/bin/weblisk-secret-team-vault"],
    "timeout_s": 20,
    "interactive_timeout_s": 300
  }
}
```

A registered `command` names its program by an absolute path. The registry
holds commands and deadlines, never a secret.

**Who may change what a caller runs.** The registry and the search path decide
which programs receive a person's secrets, so nobody but that person, or the
machine's administrators, may be able to change either. A caller **trusts** a
file only when the file and the directory that holds it are each owned by the
user the caller runs as or by an administrator, and nobody else can write
either. A caller MUST refuse a registry file it does not trust. It MUST refuse
to run a helper program it does not trust, whether the registry named it or the
search path found it. It reports the refusal as `denied`, naming the file and
the reason, and uses nothing in its place: falling back to another program would
run one the person did not choose.

### The holder reference

A **holder reference** records where an identity's private half, or only its
passphrase, is held. It names a source and says where in that source to look. It never contains a
secret, so it may be written to disk, logged and printed.

It is written as `holder.json` beside the identity's public key, in the place
the identity lives ([`architecture/cli`](../architecture/cli.md#where-an-identity-lives)).
An identity with no `holder.json` is held in an encrypted key file whose
passphrase a person types, and no source is asked. An identity whose
`holder.json` records `holds: ["passphrase"]` is held in an encrypted key file
too, and the source remembers only its passphrase
([An identity held by a source](#an-identity-held-by-a-source)).

```json
{
  "version": 2,
  "source": "team-vault",
  "reference": "weblisk/identity-7f3a9c",
  "options": { "account": "operations" }
}
```

- `source` names the source.
- `reference` says where the identity is within that source. **A reference is
  opaque outside its source:** no caller parses it, splits it or builds one.
  Only the source reads it. A source MUST return a reference that keeps naming
  the same item when a person renames that item, and SHOULD return one that
  survives renaming what holds the item, such as a vault or a folder — a name
  moves, and what a record joins on must not.
- `options` are strings the source needs on every request, such as which
  account or which vault. They pass to the source unchanged and are never
  secrets.
- `holds` says what the source holds. Absent, the source holds the identity's
  private half. `["passphrase"]` means the source remembers only the passphrase
  of the encrypted key file beside the reference
  ([An identity held by a source](#an-identity-held-by-a-source)). A caller
  refuses any other value, naming it.

**The flag form** is `<source>:<reference>`, split at the first colon. So
`team-vault:weblisk/identity-7f3a9c` names the source `team-vault` and the
reference `weblisk/identity-7f3a9c`. A reference may contain colons; a source
name cannot.

**Version 1.** A `holder.json` with no `version` field, of the form
`{"kind": "1password", "reference": "…", "account": "…"}`, is read as version 2
with `source` set to `1password`, the same `reference`, and `options.account`
set from `account` when it is present. It is read and never rewritten on read: a
record changed by opening it acquires a history nobody made. An implementation
writes version 2 only. A version-1 record whose `kind` is anything other than
`1password` is refused, naming the kind, and so is a record whose `version` is
anything other than 2, naming the version.

### Actions

A request names its action. Examples below show one request and its response.

**`capabilities`** takes no reference.

```json
{ "version": 1, "action": "capabilities", "options": {} }
{ "actions": ["capabilities", "get", "store", "erase"], "sign_algs": [], "named_fields": true, "withheld_fields": [] }
```

**`get`** returns one value. `field` names which, and is omitted for a source
without named fields. A reference that names nothing, or a field the item does
not have, is `not_found`. A field the source withholds is `unsupported`.

```json
{ "version": 1, "action": "get", "reference": "weblisk/identity-7f3a9c", "field": "public_key", "options": { "account": "operations" } }
{ "value": "<base64url>" }
```

**`store`** keeps `fields` and returns the reference that now names them. The
source chooses where from `options`. `label` is a name a person will recognise
in the source's own interface; it is never a secret and never used to find the
item again — the returned reference is. A source without named fields accepts
exactly one field, named `value`. A store that fails part way MUST NOT return a
reference, and the caller then records nothing. `store` keeps what a caller
gives it. No action of this protocol creates a key inside a source.

```json
{ "version": 1, "action": "store", "label": "weblisk identity alice", "fields": { "private_key": "<base64url>", "passphrase": "<base64url>", "public_key": "<base64url>" }, "options": { "vault": "operations" } }
{ "reference": "weblisk/identity-7f3a9c" }
```

**`erase`** forgets what a reference names. Erasing something already gone is
`not_found`, which a caller that is erasing treats as done.

```json
{ "version": 1, "action": "erase", "reference": "weblisk/identity-7f3a9c", "options": {} }
{}
```

**`sign`** is OPTIONAL. A source lists it only if the key the reference names
can sign without leaving the source. `alg` is `ml-dsa-65`, the one signing
algorithm [`protocol/identity`](identity.md) permits, and a source that can sign
lists it in `sign_algs`. The signature is over `message` exactly as given, made
as [`protocol/identity`](identity.md#sign) defines a signature, so it verifies
wherever any other Weblisk signature does. Whether it is deterministic is the
source's own; a caller MUST NOT depend on it.

A source signs what it is given because it cannot read it, so the caller is
what keeps the key from becoming an oracle
([`protocol/identity`](identity.md#fixed-form-statements)). A caller MUST ask a
source to sign only bytes it built itself, from fields it has checked: a
fixed-form statement whose prefix `protocol/identity` registers, or a value
under its Sign JSON. It MUST NOT pass on to `sign` a message another program
handed it. A caller that did would be offering signing over a caller's bytes,
which `protocol/identity` forbids.

```json
{ "version": 1, "action": "sign", "reference": "weblisk/identity-7f3a9c", "alg": "ml-dsa-65", "message": "<base64url>", "options": {} }
{ "signature": "<base64url, 3309 bytes decoded>" }
```

**An error** replaces the result. A response carries `error` or a result, never
both.

```json
{ "error": { "code": "locked", "message": "the vault is locked" } }
```

### An identity held by a source

A source holds an identity in one of three ways. The holder reference's `holds`
tells the last apart from the other two, and the source's `capabilities` tell
the first two apart.

| Way | The source holds | Beside the holder reference | `holds` |
|---|---|---|---|
| **Whole** | the private key as a `weblisk-key-v1` envelope, the passphrase that opens it, and the public key | the public key | absent |
| **Signing** | a key it signs with and never releases, and the public key | the public key | absent |
| **Passphrase only** | the passphrase of an encrypted key file | the public key and the encrypted key file | `["passphrase"]` |

**Whole.** A source with named fields holds the identity as three fields under
one reference:

| Field | Value |
|---|---|
| `private_key` | the private key in the `weblisk-key-v1` envelope ([`protocol/identity`](identity.md#private-key-format)) — encrypted, never the raw key |
| `passphrase` | the passphrase that opens that envelope |
| `public_key` | the identity's public key, so the identity can be rebuilt from the source alone |

When a caller creates an identity in a source, it generates the passphrase: at
least 256 bits from a cryptographically secure random source, encoded as text.
Nobody types it, because nobody needs to. The envelope stays encrypted even
though its passphrase sits beside it: a field shown on a screen, copied, or
exported on its own is then not a key, and a private key has one form wherever
it is written. Every private key a caller hands to a source, or receives from
one, is that envelope with `kdf = argon2id`
([`protocol/identity`](identity.md) rule 1).

A caller stores the three fields together unless the operator asks for the
passphrase alone to be kept.

**Signing.** A source that signs with `ml-dsa-65` and withholds `private_key`
keeps the key in whatever form it uses, releases `public_key`, and signs when
asked. No caller ever sees that key, so it has no envelope and no passphrase,
and nothing a caller writes or receives holds it. No action of this protocol
creates such a key. The source's own tools generate it, under
[`patterns/principal-identity`](../patterns/principal-identity.md) Design
Principle 1, and a caller then maps it.

**Passphrase only — a remembered passphrase.** A source MAY hold only the
`passphrase` of an identity whose encrypted key file stays where it is. A caller
does that only when the operator asks for it;
[`architecture/cli`](../architecture/cli.md#where-an-identity-lives) says how
they ask. The passphrase is the one the person chose, so the key file still
opens without the source. Before a caller has a source keep a passphrase, it
checks that the passphrase opens the key file.

Where a source holds an identity's passphrase, the caller does not ask a person
for one.

**Mapping an identity that is already in a source.** A caller reads
`public_key` from the source. Before it records the holder reference, or writes
the public key beside it, it MUST prove that the reference works and names that
key. It signs a **probe** through the reference, as
[Signing with a held identity](#signing-with-a-held-identity) describes, and
verifies the signature against the `public_key` it read. A reference that cannot
be read, or whose key does not match its `public_key`, is refused. Finding that
out at the first real signature means finding it out in the middle of something
else.

The probe is a fixed-form statement
([`protocol/identity`](identity.md#fixed-form-statements)):

```
"weblisk/holder-probe/v1" 0x00 <nonce>

<nonce>  32 bytes from a cryptographically secure random source, which the
         caller generates for this probe alone, as 64 lowercase hex characters
```

Nothing accepts it as anything else, so a signature made to prove a reference
proves nothing more, and the caller discards it once it has verified.

### Signing with a held identity

A caller that needs a signature from an identity held by a source asks that
source for `capabilities` first.

- **The source can sign** — it lists `sign`, with `ml-dsa-65` in `sign_algs`.
  The caller MUST ask it to sign, and MUST NOT ask it for `private_key`. The key
  never leaves the source.
- **The source cannot sign.** The caller gets `private_key` and `passphrase`,
  decrypts the envelope in memory, signs, and zeroises the key and the
  passphrase ([`protocol/identity`](identity.md) rule 10). Neither is written
  anywhere.
- **The source remembers the passphrase only.** The caller gets `passphrase`,
  decrypts the key file in memory, signs, and zeroises both.

An identity kept in an encrypted key file is decrypted in memory the same way,
with the passphrase from a person or from a source that remembers it. It is
never written anywhere in the clear, and is zeroised after use
([`protocol/identity`](identity.md) rule 10).

### Protection

`key_protection` on an `Identity`
([`patterns/principal-identity`](../patterns/principal-identity.md)) says how the
identity's long-lived key is protected, using the ranking of
[`protocol/identity`](identity.md) rule 8. A caller derives it from where the
key is held and from how the source answers `capabilities` — the actions it
answers and the fields it withholds. It never derives it from a name, label or
description a source gives itself:

| Where the private half is held | `key_protection` |
|---|---|
| A source that lists `sign` with `ml-dsa-65` in `sign_algs`, and lists `private_key` in `withheld_fields` — it signs, and will not hand the key out | `hardware` |
| A source that holds the identity whole and releases `private_key`, whether or not it can also sign | `secrets-manager` |
| A service's key held by a source its platform carries, which releases the key only to the running workload and never writes it to a filesystem. The platform blueprint declares that its source is one | `secrets-manager` |
| An encrypted key file, its passphrase typed by a person or remembered by a source | `passphrase` |
| An encrypted key file, its passphrase delivered by `file` or `fd` | `passphrase`. It is `platform-attestation` only where the deployment declares that its platform releases that secret to an attested workload alone — a caller cannot observe that, so it is never inferred |
| A key file with `kdf = none` | `development-only`. Refused for an operator identity, and for a service anywhere but development ([`protocol/identity`](identity.md) rules 1 and 6) |

A caller MUST NOT report a stronger value than this table gives. Where it cannot
tell which row applies, it reports the weaker.

`hardware` still rests on what a source answers. A caller can see that a source
signs and refuses to release the key, and cannot see inside it. The value is
trusted exactly as far as the person trusts the program they chose to speak for
that source ([Security](#security)).

### Headless references: `file` and `fd`

A service with nobody to type a passphrase, or a console on a server with no
keychain, gets a secret from what its platform delivers. Two built-in sources
read it:

- **`file:<path>`** reads the file at `<path>`, which MUST be absolute. It is
  for a secret the platform mounts as a file — a credentials directory a service
  manager provides, or a secret volume a container platform mounts.
- **`fd:<n>`** reads the inherited file descriptor numbered `<n>` to its end,
  once, and closes it. It is for a secret a parent process hands over without
  the secret touching a filesystem.

Each holds one value: the content read, less one trailing line ending if there
is one. Each answers `get` without a `field`, and every other action with
`unsupported`. A missing file, or a descriptor that is not open, is `not_found`.
A relative path, or a descriptor that is not a number, is `invalid_reference`. A
file the caller may not read is `denied`.

A caller MUST refuse a `file:` reference to a file it does not trust
([Discovery](#discovery) says when it does), and reports that as `denied`. A
secret somebody else can replace is not one the caller can rely on.

### An installation's master key

An **installation's master key** is the symmetric key under which an
installation — a console, or a service that keeps secrets of its own at rest —
encrypts those secrets. It is not an identity's key, and it signs nothing. It is
key material, so [`protocol/identity`](identity.md) rule 9 governs it, and this
section states the one exception that rule allows.

It comes from a secret source: a keychain where the installation runs as a
person's program, and `file:` or `fd:` where it runs unattended.

**A master key is the one secret an installation keeps that is not encrypted
under a master key**, since nothing can be encrypted under itself. A `file:`
master key therefore lives outside the installation's state: in a file the
platform mounts, or in a directory that the state's backups and replicas do not
include.
A master key kept beside what it encrypts is copied wherever they are, and
protects nothing from anyone who holds the copy.

**A master key that protects a private key never arrives through an environment
variable.** That holds whether it encrypts the private key directly or through a
key derived from it, such as a key bound to one purpose. An installation keeps
private keys at rest — its own credential's key, an attestation signing key —
only under a master key from a keychain, `file:` or `fd:`.

**On a hosted deployment, a master key that protects no private key MAY come
from an environment variable.** A hosted deployment is one whose platform starts
the installation and delivers its configuration, with no person present and no
keychain to ask. Some such platforms deliver a secret only as an environment
variable. Where the master key arrives that way, the installation MUST say so
wherever it reports how its secrets are protected, so anyone reading that report
knows the key can be read wherever the environment can. `file:` and `fd:` are
the alternatives, and an installation SHOULD use one where its platform offers
it. An installation that must take one master key from the environment and also
keeps a private key at rest has two master keys, and the one from the
environment protects no private key.

The rule that only `not_found` may lead to creating something
([Error Handling](#error-handling)) matters most here. A master key that could
not be read is not a missing one, and generating a replacement makes every
secret encrypted under the old key unreadable.

### A console never holds the secrets of an identity it acts for

A console's own keys are its installation's secrets: the key of its own service
identity, where it has one, and the key of each credential it holds at a hub. A
credential is not an identity
([`patterns/principal-identity`](../patterns/principal-identity.md) Design
Principle 4), so a credential a person's identity attested to the console is
among them. The console keeps them at rest under a master key it reaches through
this protocol, as [An installation's master key](#an-installations-master-key)
says.

What a console never reaches is the identity of anyone it acts for, a person's
or another service's. A console that uses this protocol for its own
installation's secrets MUST NOT use it to reach such an identity's. For those,
the console asks the CLI to act — to connect, or to sign — and the CLI asks the
source. Nothing a source returns for such an identity is ever given to a
console.

A passphrase a person types into a console, for an identity kept in an
encrypted key file, is not something a source returned. It is governed by
[`architecture/admin`](../architecture/admin.md#bootstrap-without-a-shell) rule 1.

### Where a secret is never stored

- **Unencrypted, for an operator's key.** Every operator private key a caller
  writes, hands to a source, or receives from one is the `weblisk-key-v1`
  envelope ([`protocol/identity`](identity.md) rule 1). A key that never leaves
  a source that signs is never written or received, so it has no such form.
- **Kept by a caller.** A caller never persists a secret it obtained from a
  source — `public_key` is not one — and never persists a passphrase. Only a
  source keeps a passphrase, under its own protection
  ([`protocol/identity`](identity.md) rule 4).
- **In anything this protocol records or passes along in the clear** — a holder
  reference, the registry, a request's `options` or `label`, a helper's command
  line or environment, or a helper's standard error.
- **In an environment variable** — no private key, no other key material and no
  passphrase ([`protocol/identity`](identity.md) rule 9). An installation's
  master key is the one bounded exception, stated
  [above](#an-installations-master-key).
- **In a tenant's content or records.** A holder reference belongs to the
  machine that holds the identity, not to any tenant.
- **In a console's own state, in the clear.** What a console keeps at rest is
  encrypted under a master key. A master key itself is kept as
  [An installation's master key](#an-installations-master-key) says.

### Passkeys are not a secret source

A passkey's private key never leaves its authenticator, and nothing can `get`
it. A vault that syncs passkeys is acting as an authenticator, not as a source.
There is no `passkey` source. A passkey is a credential, used through WebAuthn
by the relying party that registered it
([`patterns/principal-identity`](../patterns/principal-identity.md) Design
Principle 6). It is never an identity, and never a secret a caller reads.

### Reporting a source that did not answer

A caller that cannot get what it asked for reports three things: the source's
name, the helper it ran (or that the source is built in), and the code. For
example: *the secret source `team-vault` (`weblisk-secret-team-vault`) did not
answer within 30s — it may be locked, or waiting for an approval.*

It MUST NOT report an identity, a key or a secret as missing for any code other
than `not_found`. Telling a person "no key" when their vault is locked sends
them to create an identity they already have.

A caller that reports to another program — the CLI's machine-readable output,
read by a console — carries `source` and `code` as fields, so the reader decides
what to show from them rather than by matching the words of a message.

---

## Types

```yaml
types:
  HolderReference:
    description: >-
      Where an identity's private half, or only its passphrase, is held,
      written as holder.json beside the identity's public key. Never a secret
    fields:
      version:
        type: int
        required: true
        enum: [2]
        description: >-
          The record's version. A record with no version field is version 1,
          read as a legacy form and never written. Any other version is refused,
          naming it
      source:
        type: string
        required: true
        max: 64
        description: The source's name, matching the pattern [a-z0-9][a-z0-9-]*
      reference:
        type: string
        required: true
        description: Where the identity is within that source. Opaque outside it, and never a secret
      options:
        type: object
        required: false
        description: String options passed unchanged to the source on every request. Never a secret
      holds:
        type: "list<string>"
        required: false
        description: >-
          What the source holds. Absent means the identity's private half.
          ["passphrase"] means only the passphrase of the encrypted key file
          beside this reference. Any other value is refused, naming it

  SecretSourceRequest:
    description: One request to a source, and the whole of a helper's standard input
    fields:
      version:
        type: int
        required: true
        enum: [1]
        description: The protocol version. A helper that does not speak it answers unsupported
      action:
        type: string
        required: true
        enum: [capabilities, get, store, erase, sign]
        description: What is asked
      reference:
        type: string
        required_when: action in (get, erase, sign)
        description: What the request is about, in the source's own terms
      field:
        type: string
        required: false
        description: For get, which named field. Omitted for a source without named fields
      fields:
        type: object
        required_when: action = store
        description: For store, field name to base64url value
      label:
        type: string
        required: false
        description: For store, a name a person will recognise in the source's own interface. Never used to find the item again
      alg:
        type: string
        required_when: action = sign
        enum: [ml-dsa-65]
        description: For sign, the signing algorithm
      message:
        type: string
        format: base64url
        required_when: action = sign
        description: For sign, the exact bytes to sign. The caller built them itself, as a fixed-form statement protocol/identity registers or under its Sign JSON, and never passes on bytes another program handed it
      options:
        type: object
        required: false
        description: The holder reference's options, unchanged

  SecretSourceResponse:
    description: >-
      One response from a source, and the whole of a helper's standard output.
      It carries error or a result, never both
    fields:
      value:
        type: string
        format: base64url
        required: false
        description: For get, the value asked for
      reference:
        type: string
        required: false
        description: For store, the reference that now names what was stored
      actions:
        type: "list<string>"
        required: false
        description: For capabilities, the actions this source answers
      sign_algs:
        type: "list<string>"
        required: false
        description: For capabilities, the algorithms sign accepts. Empty or absent when the source cannot sign, and absent means empty
      named_fields:
        type: bool
        required: false
        description: For capabilities, whether one reference holds several named values. Absent means false
      withheld_fields:
        type: "list<string>"
        required: false
        description: >-
          For capabilities, the fields this source holds and never releases
          through get, whatever the reference. Absent means none. A get of a
          withheld field is answered unsupported
      signature:
        type: string
        format: base64url
        required: false
        description: For sign, the ML-DSA-65 signature over the message
      error:
        type: object
        required: false
        description: A SecretSourceError, in place of any result

  SecretSourceError:
    description: Why a source did not answer the request
    fields:
      code:
        type: string
        required: true
        enum: [not_found, locked, denied, timeout, not_installed, invalid_reference, unsupported]
        description: What happened. Only not_found means the thing asked for does not exist
      message:
        type: string
        required: true
        description: For a person. Never a secret

  SecretSourceRegistryEntry:
    description: >-
      One entry in the registry file, keyed by source name. Names the program
      that speaks for that source, and the caller's deadlines for it
    fields:
      command:
        type: "list<string>"
        required: true
        description: The program and its fixed arguments. Nothing from a request is ever added
      timeout_s:
        type: int
        required: false
        unit: seconds
        description: How long the caller waits when no person is at a terminal. The caller's own default applies when absent
      interactive_timeout_s:
        type: int
        required: false
        unit: seconds
        description: How long the caller waits when a person is at a terminal and may be approving. The caller's own default applies when absent
```

---

## Error Handling

This protocol is not HTTP, so a code has no status. It travels in
`SecretSourceResponse.error`. A helper produces most codes; the caller produces
`timeout` when its own deadline passes and `not_installed` when discovery finds
nothing, and reports them exactly as if a helper had.

**Only `not_found` means the thing asked for does not exist, so it is the only
code on which a caller MAY create something in its place** — an identity, a
master key, any secret. Every other code means the source did not answer the
question. Creating a replacement then orphans what already exists: every grant
attested for the old identity, every secret encrypted under the old master key.

A helper that exits without writing a response, or writes one that is not a
`SecretSourceResponse`, has not spoken this protocol. The caller reports that as
`unsupported`, naming the helper. A helper's exit status decides nothing either
way ([Conventions](#conventions)).

```yaml
error_format:
  type: SecretSourceError
  carried_in: SecretSourceResponse.error
  fields:
    code: string (required, one of the codes below)
    message: string (required, for a person and never a secret)

error_codes:
  - code: not_found
    description: >-
      The reference names nothing in this source, or the item has no such
      field. The only code that means absent
    retryable: false
    may_create: true
  - code: locked
    description: >-
      The source is locked, and could not be unlocked without a person, or the
      person did not unlock it
    retryable: true
    may_create: false
  - code: denied
    description: >-
      The source refused. A person declined the request, or this caller may not
      read that item. Also produced by the caller when it refuses a registry
      file, a helper program or a file: reference that it does not trust
    retryable: false
    may_create: false
  - code: timeout
    description: >-
      No answer in time. Produced by the caller when its deadline passes, or by
      a helper whose own store did not answer
    retryable: true
    may_create: false
  - code: not_installed
    description: >-
      Nothing speaks for this source. No registry entry, built-in source or
      program on the search path was found, or the helper's own tooling is
      missing
    retryable: false
    may_create: false
  - code: invalid_reference
    description: >-
      The reference is not one this source can read. Distinct from not_found,
      which is a readable reference to nothing
    retryable: false
    may_create: false
  - code: unsupported
    description: >-
      The source does not answer this action, algorithm, field or protocol
      version, or the helper did not answer in this protocol at all
    retryable: false
    may_create: false
```

---

## Security

```yaml
security:
  transport:
    - >-
      A request and its response cross only the helper's standard input and
      output. Nothing from a request is placed on the helper's command line,
      which every local process can read, or in its environment, which every
      child process inherits.
    - >-
      The caller starts a helper with an environment reduced to what finding
      programs and reaching the person's desktop session need, namely the
      search path, the home directory, the locale, and the variables the
      platform uses to reach that session. Nothing the caller was itself given
      as a secret passes through.
    - >-
      A helper never prompts on its standard input or output, which are the
      protocol channel, and SHOULD NOT prompt on a terminal at all. It reaches a
      person, when it must, through its own interface, such as a desktop
      application or the operating system's own prompt, because a caller may
      have no terminal, as when a console drives the CLI.
    - >-
      A helper's standard error is for diagnostics. It never carries a secret,
      and a caller MAY show it to a person.
    - >-
      A source, built in or a helper, places no secret, passphrase or key on
      the command line or in the environment of any program it runs, its
      store's own command-line tool included. It hands one over on that
      program's standard input, or through an interface no other process can
      read. The rule for the hop from caller to helper holds for every hop
      after it.
  signing:
    algorithm: ML-DSA-65 (FIPS 204), named ml-dsa-65 on the wire
    process: >-
      A source that can sign is asked to sign, and the key never leaves it. From
      any other source the caller gets the encrypted envelope and its
      passphrase, or the passphrase of a key file, decrypts in memory, signs,
      and zeroises both. Every signature is made as protocol/identity Sign
      defines it, over bytes the caller built itself, because a source signs
      whatever it is given
  timeouts:
    - >-
      Every deadline is the caller's. When one passes, the caller terminates
      the helper and every process the helper started, and reports timeout.
      Terminating the helper alone leaves anything it started holding the
      output open, and the caller waits on it anyway.
    - >-
      A caller SHOULD wait longer when a person is at a terminal who may be
      approving the request, and MUST wait a bounded time when nobody is, such
      as when a console drives it. A registry entry MAY set either deadline for
      one source.
  trust_model:
    description: >-
      A caller trusts the program that speaks for a source exactly as far as it
      trusts the source, because it hands that program the secret or asks it to
      sign. Which program that is must therefore be the person's own choice,
      made in the registry or by what is installed, and nobody else may change
      it. That is why a caller reads only a registry, and runs only a helper,
      that no other user can write, and skips empty and relative entries in the
      search path. A source is trusted to keep what it is given and to answer
      truly what it will do. key_protection is derived from those answers, the
      actions a source answers and the fields it withholds, and never from a
      name or description a source gives itself. The answers are still the
      source's own. A caller cannot look inside a source, so hardware means a
      source that answered as a non-extractable holder answers, trusted as far
      as the person trusts the program they chose.
```

---

## Implementation Notes

- The shape follows the credential helpers that version-control and container
  tools already use: a small program per store, one request per run, the
  secret on a pipe. A person who has written one of those can write one of
  these.
- A caller may ask for `capabilities` once per process and keep the answer. It
  says what the source can do, which does not change while the caller runs.
- A caller SHOULD bound how much of a helper's output it reads. A response is
  small, and an unbounded read lets a faulty helper exhaust the caller's
  memory.
- A caller deciding whether to ask a person for a passphrase asks the holder
  reference, not the filesystem. A passphrase a source holds is never asked
  for, and asking for one anyway invites a person to invent a secret that
  protects nothing.
- `public_key` crosses the wire as the key's bytes, base64url-encoded like every
  other value. A source may keep it in whatever encoding its own interface
  shows people.
- An implementation may offer its built-in sources to other callers as a
  command that speaks this protocol, so a console can reach them without
  installing a helper. That command is then a helper like any other.

---

## Verification Checklist

- [ ] A caller resolves a source from the registry `~/.weblisk/secret-sources.json` first, then from its built-in sources, then from `weblisk-secret-<name>` on the search path, skipping empty and relative search-path entries
- [ ] `file` and `fd` are read by the caller itself, and a registry entry or program on the path with either name is ignored
- [ ] A registry file, a helper program, registered or found on the search path, and a `file:` reference are each refused as `denied` unless the file and its directory are owned by the caller's user or an administrator and nobody else can write them; nothing is used in a refused program's place
- [ ] A registered command names its program by an absolute path
- [ ] No field of a `SecretSourceRequest` appears on a helper's command line or in its environment
- [ ] While a source, built in or a helper, runs its store's own tool to store, read or erase a secret, no secret value, passphrase or key appears on that tool's command line or in its environment, as `ps` or the process's environment would show; the `1password` source and a keychain source included
- [ ] A helper's environment carries no variable holding a secret the caller was given
- [ ] A helper answers a request whose `version` it does not speak with `unsupported`
- [ ] A valid response is the helper's answer whatever its exit status, and only a helper that wrote no valid response is reported as `unsupported`
- [ ] A caller asks for `capabilities` before using `store`, `erase` or `sign`, and a source answers an unlisted action with `unsupported`
- [ ] A source answers `get` of a field it lists in `withheld_fields` with `unsupported`, and a `capabilities` response missing a field is read as `named_fields` false, `sign_algs` empty and `withheld_fields` empty
- [ ] A `holder.json` with no `version` and `kind: 1password` is read as `source: 1password` with `options.account` from `account`, and the file is not rewritten
- [ ] A version-1 `holder.json` with any other `kind` is refused, naming the kind, and a `holder.json` with a `version` other than 2 is refused, naming the version
- [ ] A `holds` other than absent or `["passphrase"]` is refused
- [ ] A caller never parses a `reference` outside its source
- [ ] A caller creates an identity, a master key or any secret in place of one it could not read only when the source answered `not_found`
- [ ] A caller never reports an identity, a key or a secret as missing for `locked`, `denied`, `timeout`, `not_installed`, `invalid_reference` or `unsupported`
- [ ] A report of a source failure names the source, the helper and the code, and machine-readable output carries `source` and `code` as fields
- [ ] When a caller's deadline passes, the helper and every process it started are terminated and `timeout` is reported
- [ ] A source that lists `sign` with `ml-dsa-65` in `sign_algs` is asked to sign and is never asked for `private_key`
- [ ] From a source that cannot sign, the caller gets `private_key` and `passphrase`, decrypts in memory, signs, and zeroises both
- [ ] An identity created in a source is stored as the `weblisk-key-v1` envelope with `kdf = argon2id`, a generated `passphrase` of at least 256 bits from a cryptographically secure random source, and its `public_key`, never as a raw key
- [ ] A source keeps only an identity's passphrase only when the operator asked for it, and only after the caller checked that the passphrase opens the key file
- [ ] A holder reference is recorded only after a `weblisk/holder-probe/v1` signature made through it, over a nonce the caller generated for it, verifies against the `public_key` read from it
- [ ] A caller asks a source to `sign` only a fixed-form statement `protocol/identity` registers, or a value under Sign JSON, that it built itself, and never a message another program handed it
- [ ] `key_protection` is `hardware` only for a source that lists `sign` with `ml-dsa-65` and lists `private_key` in `withheld_fields`, and is never reported stronger than the Protection table gives
- [ ] `file:` with a relative path answers `invalid_reference`
- [ ] A master key that protects a private key, directly or through a key derived from it, never comes from an environment variable
- [ ] An installation whose master key came from an environment variable reports that it did
- [ ] A `file:` master key is outside the installation's state and outside that state's backups and replicas
- [ ] A console never receives a value a source returned for the identity of anyone it acts for
