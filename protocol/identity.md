<!-- blueprint
type: protocol
name: identity
version: 3.1.0
requires: [protocol/types]
platform: any
tier: free
-->

# Weblisk Identity & Security Specification

Cryptographic identity for all agents and orchestrators. Every entity
generates a key pair and uses it for signing, verification, and
token-based authentication.

## Overview

The Weblisk Identity specification defines how agents and orchestrators
establish cryptographic identity, sign messages, verify signatures,
and manage authentication tokens. Every entity generates a key pair on
first run, uses it for registration signature verification, and receives
a Weblisk Token (WLT) for subsequent authenticated requests. This
specification is the single source of truth for all identity and
cryptographic operations in the Weblisk framework.

### What this document specifies, and what it does not

Every requirement here is stated in terms of algorithms, formats and behaviour —
never in terms of a language, a runtime, a module or an API. That is deliberate.
A hub generated for Go and a hub generated for Cloudflare must be able to verify
each other's signatures and read each other's key files, which is only true if
what they conform to is the algorithm and the format rather than one platform's
way of reaching them.

Where a language's or platform's standard library does not provide a primitive
named here, the **language or platform blueprint** names what does. That is such
a blueprint's entire purpose: translating these requirements into the native
terms of one language or runtime. Concretely, `languages/go.md` carries a
Primitive Mapping table because Go ships neither a post-quantum signature
implementation nor a memory-hard key-derivation function, and something has to
say where a Go implementation gets them.

Two rules follow, and both have been broken already:

- This document MUST NOT name a module, package, API or language construct. A
  checklist item once read *"verify all signatures … using ML_DSA_65.Verify"*,
  which is an identifier, not a requirement — and no Rust or JavaScript
  implementation has a symbol by that name.
- A language or platform blueprint MUST NOT restate a requirement from here.
  `platforms/go.md` once carried the key-derivation algorithm with its RFC number
  and its parameters, which made a second normative copy of this section, free to
  drift from it. It may name the module that provides the primitive; it may not
  redefine the primitive.

**Notation.** Where a process below reads `sign(privateKey, data)` or
`verify(publicKey, data, signature)`, those name the signature algorithm's own
primitives as defined by its standard — not a function in any library. An
implementation calls whatever its platform blueprint maps them to.

### Post-Quantum Cryptography

Weblisk adopts NIST's post-quantum cryptography standards (released
August 2024) to protect against future quantum computing threats.

| Purpose | Algorithm | Standard |
|---------|-----------|----------|
| Digital signatures | **ML-DSA-65** (CRYSTALS-Dilithium) | FIPS 204 |
| Key encapsulation | **ML-KEM-768** (CRYSTALS-Kyber) | FIPS 203 |
| Backup signatures | **SLH-DSA-SHA2-128s** (SPHINCS+) | FIPS 205 |
| Symmetric encryption | **AES-256-GCM** | FIPS 197 |
| Key derivation | **Argon2id** | RFC 9106 |

All algorithms are quantum-resistant. Weblisk does not use a
quantum-vulnerable algorithm (no RSA, no ECDSA, no Ed25519, no
classical Diffie-Hellman) for an identity, a token, an attestation or a
signed record. Whoever breaks the algorithm of one of those can forge it,
at any time afterwards.

A credential that **proves a live session** is different, and
[`patterns/principal-identity`](../patterns/principal-identity.md) Design
Principle 6 says why: it signs nothing that outlives the session, so it may be
classical. That includes a transport credential a hub presents to a third
party's service in that service's own protocol, such as the SSH key for pushing
to a content remote ([`patterns/content-git`](../patterns/content-git.md)).
The blueprint that specifies such a transport states what its key exchange
must be. A credential that **signs records**, attested with the purpose
`sign-records`, is not such a credential: what it signs outlives every session,
so it is ML-DSA-65 like everything else that signs (principal-identity,
`record-signing`).

**Why ML-DSA-65?** ML-DSA is a lattice-based digital signature scheme
selected by NIST after an 8-year international evaluation process
(FIPS 204, finalized August 2024). It is resistant to both classical
and quantum attacks. ML-DSA-65 provides NIST Security Level 3
(equivalent to AES-192 against classical and quantum adversaries).

**Why not Ed25519?** Ed25519 (elliptic curve) is vulnerable to Shor's
algorithm on quantum computers. Per NIST IR 8547, all elliptic curve
and RSA algorithms will be deprecated by 2030 and removed from NIST
standards by 2035. Weblisk removes this class of vulnerability from
everything it signs by using only post-quantum algorithms there.

**Why AES-256-GCM?** Grover's algorithm reduces AES-256 to ~128-bit
equivalent security against quantum attacks. 128-bit security remains
far beyond brute-force feasibility. NIST considers AES-256
quantum-resistant and recommends no change.

**Backup algorithm:** SLH-DSA-SHA2-128s (FIPS 205) is a stateless
hash-based signature scheme that provides a conservative fallback if
lattice-based cryptography is ever compromised. It is slower and
produces larger signatures than ML-DSA but relies only on the security
of hash functions.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.15.0 <7.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, public_key]
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: AgentMessage
          fields_used: [from, to, action, payload, signature]
        # Where a component records a person's request a pass carried, and
        # the gateway that carried it (The pass, rule 5)
        - name: AuditEntry
          fields_used: [actor, via, authorisation, run]
        # A person's authorisation of unattended work, and the exchange that
        # mints a work pass under it (The work pass)
        - name: WorkAuthorisation
          fields_used: [id, owner, definition, actors, capabilities, authorised_by, not_after, status]
        - name: WorkExchangeRequest
          fields_used: [authorisation, audience, scope, run]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Conventions

- Signing algorithm: ML-DSA-65 (FIPS 204) — the sole signing algorithm
- Key encapsulation: ML-KEM-768 (FIPS 203) — for any key exchange operations
- Key sizes: 1952-byte public key, 4032-byte private key, 3309-byte signature
- Encoding: base64url for all keys and signatures (size-efficient for
  ML-DSA's larger key material)
- JSON signing: RFC 8785 JSON Canonicalization Scheme (JCS) — mandatory
  for all JSON values that are signed
- Token format: `base64url(header).base64url(payload).base64url(signature)`
- All three token parts use base64url encoding WITHOUT padding (RFC 4648 §5)
- Algorithm header: the token header `alg` field MUST be `ML-DSA-65`.
  Tokens with any other `alg` value MUST be rejected

## Key Management

### Generation
- Generate a fresh ML-DSA-65 key pair on first run
- Use cryptographically secure random source (e.g., crypto/rand, Web Crypto API)
- NEVER hardcode or share private keys. A published test vector's key is
  no one's ([Fixed-Form Statements](#fixed-form-statements))

### Storage
- Keys MUST be stored in a dedicated directory with restricted access
- Private key files MUST have restrictive permissions (readable only by the owning process)
- Public key files contain the base64url-encoded public key
- On startup: load existing keys if present, generate new ones if absent

### Key Fingerprint

A public key's **fingerprint** is the lowercase hexadecimal SHA-256 digest of
the decoded public key bytes: 64 characters. It names a key without carrying it.
A fingerprint changes only when the key does, and it is never derived from a
name or an address.

[`patterns/principal-identity`](../patterns/principal-identity.md) names a hub
and a credential by fingerprint.

### Private Key Format

Private keys are stored encrypted at rest. The file format is:

```
weblisk-key-v1
<algorithm>
<kdf>
<kdf-params>
<ciphertext>
```

| Field | Value | Description |
|-------|-------|-------------|
| Magic | `weblisk-key-v1` | Format identifier |
| Algorithm | `ml-dsa-65` | Key algorithm |
| KDF | `argon2id` or `none` | Key derivation function |
| KDF Params | Base64url JSON | `{salt, time, memory, parallelism}` or `{}` |
| Ciphertext | Base64url | AES-256-GCM encrypted private key (or plaintext if KDF = none) |

### Encryption Scheme

When `kdf = argon2id`:

```
1. passphrase → Argon2id(passphrase, salt, time=3, memory=65536, parallelism=4) → 32-byte key
2. AES-256-GCM(derived_key, nonce=first_12_bytes_of_salt, plaintext=private_key_hex) → ciphertext
3. Store ciphertext + tag as base64url
```

Decryption reverses the process — obtains the passphrase, derives the key,
decrypts.

**How a passphrase reaches an implementation is not specified here.** It MUST
arrive over a channel that does not echo it, does not persist it and does not log
it; which channel that is belongs to the platform blueprint. A runtime with a
terminal will prompt; a runtime without one — a Worker, a container, a scheduled
task — cannot, and a specification that says "prompt" has excluded it.

When `kdf = none`:
- The private key is stored as hex (no encryption)
- Used ONLY for automated service keys in environments where passphrase
  input is impossible (containers, CI, headless servers), and ONLY in
  development (rule 6). Never for an operator key (rule 1)
- Restrictive file permissions are the sole protection layer

### Key Categories

| Category | KDF | Passphrase Source | Use Case |
|----------|-----|------------------|----------|
| **Operator keys** | `argon2id` wherever the key is written, never `none` (rule 1) | A non-echoing channel operated by a human, or a secret source (rule 1) | Human-operated tooling |
| **Service keys** (orchestrator, gateway, agent) | `argon2id`, or `none` in development only (rule 6) | A secret source, or none | Automated processes |

**Rules:**
1. Every operator private key an implementation writes, hands to a secret
   source, or receives from one MUST be the `weblisk-key-v1` envelope with
   `kdf = argon2id`, opened by a passphrase of at least 12 characters that
   cannot be skipped. It is never stored unencrypted, whoever holds it — a key
   file, a keychain or a vault. A passphrase a person chooses arrives over a
   channel the platform blueprint names; a headless implementation uses rules 7
   and 8 rather than asking a human who is not there. Where a secret source
   holds the key, [`protocol/secret-source`](secret-source.md#an-identity-held-by-a-source)
   says where the passphrase comes from. A key that never leaves a secret source
   that signs is never written, handed over or received, so this rule does not
   reach it. `kdf = none` is for service keys alone, and for those only in
   development (rule 6).
2. Service key generation defaults to `kdf = none`, which rule 6 confines to
   development, and MUST support encrypted keys whose passphrase comes from a
   secret source ([`protocol/secret-source`](secret-source.md)): rule 3 keeps
   a key with `kdf = none` out of production, so a generator that could not
   encrypt one could make no key production may run.
3. In production a service key MUST NOT be kept with `kdf = none` (rule 6).
   One kept encrypted takes its passphrase at startup from a secret source,
   such as a secrets manager or a secret the platform mounts, which is
   rule 8's injected passphrase.
4. The passphrase is NEVER stored on disk. It exists only in memory
   during the decrypt operation. This binds the implementation, which never
   writes a passphrase anywhere; a secret source MAY keep one under its own
   protection, as [`protocol/secret-source`](secret-source.md) describes.
5. Failed passphrase attempts log `identity.key_decrypt_failed` and
   fail the operation. No retry loop — the operator re-runs the command.
   How the failure is signalled is the platform blueprint's: the CLI
   exits with its auth-error code ([`architecture/cli`](../architecture/cli.md#exit-codes)).

### Service Key Protection

Rule 2's default dates from a model in which a service held one
long-lived key on disk, and `kdf = none` was the only way a headless
process could start unattended. That trade is no longer necessary, and
it is no longer permitted in production.

A service key protected by file permissions alone is a permanent and
SILENT compromise. Anyone who reads the file — from a backup, a
container image, a mounted volume, a crash dump, or a co-located
process — holds that identity indefinitely. Nothing about the theft is
observable: there is no passphrase to fail, no presence check to miss,
and no expiry to reach. A stolen operator key is noticed; a stolen
service key is not.

The resolution is not stronger encryption of a long-lived key. It is
to stop persisting one.

**Rules:**

6. A production service MUST NOT hold a long-lived private key
   protected by file permissions alone. `kdf = none` is permitted ONLY
   in development, and an implementation MUST report such a key as
   development-only rather than treating it as ordinary.

7. A service's OPERATING credential MUST be short-lived, minted at
   process start, held in memory only, and never written to disk. Its
   lifetime SHOULD be hours, and MUST NOT exceed the rotation interval
   for the key that attested it.

8. The long-lived material that attests those credentials MUST be
   protected by one of, in descending preference:

   | Protection | Mechanism |
   |------------|-----------|
   | Hardware | TPM, secure enclave, HSM — key is non-extractable |
   | Platform attestation | The runtime proves the workload's identity (workload identity, instance metadata, TPM quote) and the key is released only to a matching measurement |
   | Managed secret | KMS or secrets manager, authenticated by platform identity, never materialised on disk |
   | Injected passphrase | Supplied at start via a credential channel, held in memory only |

   Where something other than the implementation holds the material — a
   keychain, a vault, a hardware token — the implementation reaches it through
   [`protocol/secret-source`](secret-source.md), which also says which of these
   rows each way of holding it earns.

9. No private key (an identity's, a credential's or any other), no other key
   material, and no passphrase MAY be supplied through an environment variable.
   Environment is readable via `/proc`, container inspection, crash dumps and
   diagnostic output, and it is inherited by every child process. **Key
   material** here is a private key or the seed it is derived from, and any
   symmetric key that encrypts data at rest or protects another key. A
   **passphrase** is a secret that opens key material. The one exception is an
   installation's master key on a hosted deployment, and only a master key that
   protects no private key, as
   [`protocol/secret-source`](secret-source.md#an-installations-master-key)
   states. A secret shared with another system — an API key, a password, a
   webhook's shared secret — is neither key material nor a passphrase in this
   rule; [`patterns/secrets`](../patterns/secrets.md) says how it is delivered.

10. In-memory key material MUST be zeroised after use, SHOULD be
    excluded from swap where the platform allows it, and MUST be
    excluded from core dumps.

11. Where platform attestation is available, a service SHOULD hold no
    long-lived private key at all: the platform identity is the root of
    trust, and every credential the service uses is short-lived and
    re-minted.

Rules 6–11 raise the bar set by rules 2 and 3. A deployment relying on
`kdf = none` outside development is NOT conformant.

### Key Loading Flow
```
1. Check if a stored key exists for this identity
2. If yes:
   a. Parse stored key format and validate header
   b. Read KDF field
   c. If encrypted (KDF applied):
      - Obtain passphrase over a non-echoing channel (the platform blueprint names it)
      - Derive decryption key via the configured KDF with stored params
      - Decrypt ciphertext with authenticated encryption
      - Decode → ML-DSA-65 private key
   d. If unencrypted:
      - Decode directly → ML-DSA-65 private key
   e. Derive public key from private key
3. If no: generate new key pair → encrypt → save → return
```

### Key Rotation

Operator keys can be rotated without losing hub access:

```
1. Operator initiates key rotation
2. The current key is unlocked as its holder unlocks it: by its passphrase,
   or by the secret source that holds it
3. A new ML-DSA-65 key pair is made: generated and protected as the identity's
   holder protects one, or, for a source that signs and never releases a key,
   created with that source's own tools (protocol/secret-source)
4. The new key is kept beside the old one until every hub has it
5. The new public key is sent to each hub, signed by the old key and by the
   new one (POST /v1/admin/operators/{name}/key, architecture/admin)
6. Each hub validates both signatures → stores the new public key, keeps the
   operator's name, role and identity id, records the old key as retired with
   the time of the change, and revokes every credential the old key attested
7. When every hub that recorded the old key has either taken the new one or
   been abandoned by the person (architecture/cli, rotate --abandon), the old
   key's private half is destroyed and its public half kept for audit. While
   any hub is still pending, the old private key is kept
8. The operator attests a new credential at each hub with the new key
```

Because the hub keeps the operator's identity id, what was recorded under the
old key and what is recorded under the new one name the same operator. The
old key signs nothing more at that hub, and is never accepted there again. It
is **retired**, not revoked: a signature it made before its `retired_at` still
verifies, and one dated at or after it does not. How the CLI carries the steps
out, a rotation some hubs have not yet received included, is
[`architecture/cli`](../architecture/cli.md#weblisk-operator-rotate)'s.

A registered component's key does not rotate through these steps, which are
an operator's. It rotates through `POST /v1/rotate-key`
([`protocol/spec`](spec.md#post-v1rotate-key)), signed by its current key and
its new one, with any passphrase from a secret source
([`protocol/secret-source`](secret-source.md)) instead of an interactive
prompt — never from the environment (rule 9). Its identity id is the
fingerprint of the key it registered with (`protocol/spec`), so unlike an
operator's it changes with its key, and `protocol/spec` states that gap.

### Key Recovery

If an operator loses their passphrase, the encrypted private key is
**unrecoverable by design**. There is no backdoor, no master key, and
no reset mechanism. This section defines the recovery procedures.

#### Recovery via Backup Operator

The primary recovery path is another registered operator:

```
1. Second operator (already registered, admin role) authenticates
2. Removes the compromised operator (DELETE /v1/admin/operators/{name})
3. Orchestrator keeps the record as revoked, and revokes its credentials, so
   every token resting on them ends at its next request
4. Compromised operator generates a new key pair
5. Compromised operator submits a new registration request under a NEW name.
   A removed operator's name stays with its revoked record and is never
   reused (protocol/types OperatorStatus)
6. Registration appears in approvals queue (not auto-approved)
7. Second operator approves the registration
8. Access restored with new identity, and a new identity id
```

A key that is lost cannot be rotated: only the key the hub recorded can sign
the continuity [Key Rotation](#key-rotation) needs. So a recovered operator is
a new operator, with a new identity id, and records made under the old one
still name the old one.

**Requirement:** Every production deployment MUST have at least two
registered operators. A single-operator deployment has no recovery
path if the passphrase is lost.

#### Recovery via Bootstrap Reset

If ALL operator keys are lost (catastrophic scenario):

```
1. Stop the orchestrator
2. Delete the operator registry from orchestrator storage
3. Restart the orchestrator (enters bootstrap mode, and emits a new bootstrap secret)
4. The operator who registers presenting that secret becomes admin, as at
   first start ([`architecture/admin`](../architecture/admin.md#bootstrap-flow))
5. All existing operator tokens and credentials are invalidated
```

This is destructive — it resets the entire operator trust chain.
Agent registrations and data are preserved, but all operator
permissions must be re-established.

#### Key Backup Policy

Operators SHOULD maintain an encrypted backup of their key in a
separate secure location (hardware security key, printed paper key,
safety deposit box). The backup is the encrypted key itself —
never the raw private key or passphrase.

| Policy | Recommendation |
|--------|---------------|
| Minimum operators per deployment | 2 (production), 1 (development) |
| Key backup storage | Offline, physically separated from primary |
| Passphrase storage | Memory only — or written and stored in physical safe |
| Recovery test frequency | Quarterly (verify backup operator can revoke/re-register) |

## Message Signing

### Sign
```
input: data (bytes)
output: base64url-encoded ML-DSA-65 signature (3309 bytes)
process: sig = sign(privateKey, data)
```

`sign` is pure ML-DSA-65, the `ML-DSA.Sign` of FIPS 204, with an empty context
string. It is never the pre-hash variant, HashML-DSA, and never carries a
context. [Verify Signature](#verify-signature) uses the same empty context, so a
signature made any other way does not verify. Whatever holds the key signs this
way, including a secret source that signs
([`protocol/secret-source`](secret-source.md)).

### Sign JSON
```
input: any JSON-serializable value
output: base64url-encoded ML-DSA-65 signature
process: data = canonicalize(value) → Sign(data)
```

**Canonical JSON (RFC 8785):** All JSON signing MUST use
[RFC 8785 JSON Canonicalization Scheme (JCS)](https://www.rfc-editor.org/rfc/rfc8785).
This guarantees identical byte output across all languages and platforms:

1. Object keys sorted by their UTF-16 code units, which is not code-point
   order for a character outside the Basic Multilingual Plane
2. No insignificant whitespace
3. Numbers serialized as ES2015 serializes a double (no trailing zeros; an
   exponent keeps its sign, as in `1e+30`)
4. Strings use minimal \uXXXX escaping (only required characters)

Native `JSON.stringify` is NOT sufficient — key ordering varies across
languages (Go sorts by default, Python 3.7+ preserves insertion order,
JavaScript preserves insertion order). Implementations MUST use a
compliant JCS library or implement the RFC 8785 algorithm directly.

### Verify Signature
```
input: publicKey (bytes), signature (bytes), data (bytes)
output: boolean
process:
  1. Validate public key is 1952 bytes
  2. Validate signature is 3309 bytes
  3. Return verify(publicKey, data, signature), with an empty context string
  4. Return false on any decode error
```

### Fixed-Form Statements

A signer that signs a JSON value uses [Sign JSON](#sign-json). A signer that
signs a statement it builds from a few named fields, so that a verifier can
rebuild the bytes without a canonicaliser, uses a **fixed-form statement**:

```
<prefix> 0x00 <field> 0x00 <field> ... 0x00 <field>
```

- `<prefix>` is ASCII text from the registry below. One 0x00 byte follows it,
  and one separates each field from the next. Nothing follows the last field.
- A field is UTF-8 text in the form the defining document gives it. An empty
  field is zero bytes. No field may contain a 0x00 byte, so the bytes split
  back into their fields in exactly one way.
- The signature is [Sign](#sign) over those bytes.

**The prefix is the domain separation.** Every registered prefix begins with
`weblisk/`. A canonical JSON value begins with `{`, `[`, `"`, a digit, `-`,
`t`, `f` or `n`. So no fixed-form statement is a JSON value, and no two kinds of
statement share bytes. One key can sign more than one kind of statement, and a
signature made for one kind is never valid as another.

**Nothing offers to sign a caller's bytes.** A party that offers signing to
another program — a command-line verb, a route, or a function another component
calls — MUST build the bytes itself, as a fixed-form statement or under
[Sign JSON](#sign-json), from fields it has checked. It MUST NOT sign bytes the
caller hands it. A key that signs whatever it is given is an oracle for every
statement that key can make.

A key holder reached through [`protocol/secret-source`](secret-source.md) is
the one signer that signs a message as it is given, because it does not read
the message. The rule then binds whoever asks it. Only a signer that built the
bytes itself, in one of those two forms, may ask a secret source to sign them
([`protocol/secret-source`](secret-source.md#actions), `sign`).

| Prefix | Signed by | Defined in |
|---|---|---|
| `weblisk/auth/v1` | An identity, proving that it holds its key to a service that is not a hub | [Proving an identity to a service that is not a hub](#proving-an-identity-to-a-service-that-is-not-a-hub) |
| `weblisk/credential-auth/v1` | A credential, to obtain an operator token | [`architecture/admin`](../architecture/admin.md#minting-a-token-with-the-credential) |
| `weblisk/step-up/v1` | An operator's identity, over a hub's `hub_id`, the nonce of the token request it rides on and the act that asked, re-confirming the person for a destructive act. A passkey's assertion is made over the same bytes as its WebAuthn challenge | [`architecture/admin`](../architecture/admin.md#re-confirming-for-a-destructive-act) |
| `weblisk/log-key/v2` | A log owner's long-lived key, introducing the key that signs the log's checkpoints | [`architecture/storage`](../architecture/storage.md#sealing-a-chained-log) |
| `weblisk/log-checkpoint/v2` | A log key, over the log's tip | [`architecture/storage`](../architecture/storage.md#sealing-a-chained-log) |
| `weblisk/log-succession/v1` | A log owner's outgoing and incoming long-lived keys, each over the change from one to the other | [`architecture/storage`](../architecture/storage.md#a-change-of-long-lived-key) |
| `weblisk/content-change/v2` | A person's sign-records credential, over a change to a content entry | [`architecture/content`](../architecture/content.md#the-change-statement) |
| `weblisk/holder-probe/v1` | An identity held by a secret source, proving that the reference reaches it. Nothing accepts it as anything else | [`protocol/secret-source`](secret-source.md#an-identity-held-by-a-source) |
| `weblisk/hub-proof/v1` | A hub, by the key its `hub_id` is the fingerprint of, over an address it is reached at and a client's challenge, proving that the hub at that address holds that key | [`architecture/admin`](../architecture/admin.md#proving-the-hub-at-an-address) |
| `weblisk/directory/v2` | An orchestrator, by its signing key, over the service directory it pushes and serves | [`protocol/spec`](spec.md#post-v1services) |
| `weblisk/namespace-claim/v2` | A person's identity, claiming a namespace at one registry | [`patterns/namespace`](../patterns/namespace.md#claim) |
| `weblisk/namespace-grant/v2` | A namespace's holder, letting another identity publish under it or withdrawing that | [`patterns/namespace`](../patterns/namespace.md#grant) |
| `weblisk/namespace-transfer/v2` | A namespace's outgoing and incoming holders, each over a transfer or rotation; the outgoing holder alone over a retirement | [`patterns/namespace`](../patterns/namespace.md#transfer) |
| `weblisk/catalog-release/v2` | A namespace's holder or `publish` grantee, over the index of one release | [`patterns/namespace`](../patterns/namespace.md#catalog-release) |

A kind of statement is registered here before any implementation signs it. A
prefix names one layout for good. A changed layout gets a new prefix and a new
row, and a verifier refuses a prefix it does not know.

**Test vectors come before a signer.** An implementation signs under a prefix
only once this corpus publishes test vectors for it — the field values, the
exact bytes signed, a public key with its fingerprint, and a signature over
them — made with Cloudflare's circl and verified with OpenSSL 3.5 or later and
with @noble/post-quantum. Every implementation, a hub's, a client's or a
verifier's, tests against those same vectors. They are published in one place,
[`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json):
a data file no blueprint requires, so no build carries it in its prompt, and
every build receives it as test data
([`architecture/generation`](../architecture/generation.md#published-test-vectors)).
It holds vectors for `weblisk/auth/v1`, `weblisk/credential-auth/v1`,
`weblisk/step-up/v1`, `weblisk/log-key/v2`, `weblisk/log-checkpoint/v2`,
`weblisk/log-succession/v1`, `weblisk/content-change/v2`,
`weblisk/directory/v2`, `weblisk/namespace-claim/v2`,
`weblisk/namespace-grant/v2`, `weblisk/namespace-transfer/v2` and
`weblisk/catalog-release/v2`. None is published
yet for `weblisk/holder-probe/v1` or `weblisk/hub-proof/v1`, so no
implementation may yet sign under either.

Each vector key is made from a seed the file publishes, and each signature is
FIPS 204's deterministic variant, so a signer that can sign deterministically
reproduces every signature byte for byte, and any other signer's signature
verifies under the same key. **A vector key is no one's identity.** Its seed is
public, which is the one place a private key is shared
([Generation](#generation)): anyone can sign with it, so a signature by it
proves nothing. No implementation accepts a vector key as an identity, a
credential, a hub's key or a log's, and none ships one outside its tests.

The document that defines a prefix, the last column above, states what a
conforming implementation does until that prefix has vectors, and never
requires the signature before then. A rule there that needs one holds from
the day they are published.

### Proving an identity to a service that is not a hub

A service that is not a hub sometimes needs to know that a person holds an
identity. A console does, before it links an identity to one of its accounts.
It asks for a signature by the identity key over a fixed-form statement:

```
"weblisk/auth/v1" 0x00 <audience> 0x00 <nonce>

<audience>  the name the verifying service gives this purpose. A signature made
            for one audience is never valid at another
<nonce>     the challenge the service issued, as the text it issued
```

- The service issues the nonce: at least 128 bits from a cryptographically
  secure random source, bound to what the proof is for, spent by its first
  use whether or not the signature verifies, and expiring within 300 seconds.
- The signer refuses an empty audience or nonce, and one that contains a 0x00
  byte. It builds the bytes itself from the two it is given.
- The service rebuilds the bytes from its own audience and the nonce it issued,
  and verifies the signature under the identity public key the proof is about.
  It never verifies the nonce alone.

The proof shows that whoever answered held the key at that moment, and nothing
more. It is not a session, and no hub accepts it: a hub is entered by a
credential, never by the identity
([`patterns/principal-identity`](../patterns/principal-identity.md) Design
Principle 4).

## Token System

Tokens are signed claims used for authentication between agents and
the orchestrator. They are self-contained — the verifier only needs
the issuer's public key.

### Token Format
```
base64url(header) . base64url(payload) . base64url(signature)
```

All three parts use base64url encoding WITHOUT padding (RFC 4648 §5).

### Header
```json
{"alg": "ML-DSA-65", "typ": "WLT"}
```
- `alg`: signing algorithm — MUST be `ML-DSA-65`
- `typ`: token type identifier — MUST be `WLT`

Verifiers MUST check the `alg` field is exactly `ML-DSA-65`. Tokens
with any other `alg` value MUST be rejected.

### Payload (Claims)

The example is a **registration token**: the one `POST /v1/register` issues
a component ([`protocol/spec`](spec.md)). Some blueprints call it an *agent
token*. It is the same token, under two names.

```json
{
  "sub": "seo",
  "iss": "orchestrator",
  "iat": 1712160000,
  "exp": 1712246400,
  "cap": ["file:read", "llm:chat", "agent:message"],
  "identity_id": "<fingerprint of the public key seo registered>"
}
```

Fields:
- `sub` (subject): agent name or identity
- `iss` (issuer): who created the token ("orchestrator" or agent name)
- `iat` (issued at): an RFC 7519 NumericDate
- `exp` (expires at): an RFC 7519 NumericDate (0 = no expiry)
- `cap` (capabilities): granted capability names (optional). An operator
  token always carries `cap`, an empty list included, and names no capability
  its `cap` does not name: an operator token whose `cap` is absent or empty
  may use none, and is never read as carrying its role's full set
  ([`architecture/admin`](../architecture/admin.md#contracts),
  operator-token-issuance)
- `cid`: the id of the record the issuer minted this token under, and can
  withdraw before `exp` (optional). An empty `cid` is no `cid`, and a verifier
  that asks whether a token carries one treats it so. A registration token
  carries none. A channel token carries its channel's id. An operator token
  carries the id of the credential that obtained it
  ([`architecture/admin`](../architecture/admin.md#obtaining-a-token)), and says
  it is one in its `type` claim, so a verifier never takes a channel's id for a
  credential's. A pass carries the `cid` of the operator token it was
  exchanged for, and a work pass the id of the work authorisation it was
  minted under ([The work pass](#the-work-pass))
- `type`: what the token is for, where one issuer mints more than one kind
  (optional). `operator` administers a hub. `attestation` does one thing: it
  submits an attestation for its subject
  ([`architecture/admin`](../architecture/admin.md#operator-token)). `pass`
  carries one person's request from the admin gateway to one component
  ([The pass](#the-pass)). `work` carries one request of a run nobody is
  present for, on its owner's authority, to one component
  ([The work pass](#the-work-pass)). An agent token and a channel token carry none, so a
  verifier that requires a `type` refuses them. An empty `type` is no `type`
- `aud` (audience): on a pass and a work pass alone, the identity id of the
  one component it is addressed to ([The pass](#the-pass),
  [The work pass](#the-work-pass)). No other token carries one
- `act` (actor): on a pass, the gateway that obtained it, and on a work pass,
  the component doing the run's work, each as an object carrying that
  component's `sub` and `identity_id`, as RFC 8693 §4.1 shapes `act`. No
  other token carries one
- `definition`: on a work pass alone, the definition its work authorisation
  names, as its owner wrote it ([The work pass](#the-work-pass))
- `run`: on a work pass alone, the run the request belongs to, as the actor
  named it when the pass was minted ([The work pass](#the-work-pass))
- `identity_key`: on a pass alone, the fingerprint of its person's identity
  public key when the pass was minted
- `step_up_at`: when the subject last completed a step-up, a NumericDate
  (optional). An operator token carries it only where the orchestrator minted
  it through an interactive re-confirmation it verified itself, the
  operator's identity signing `weblisk/step-up/v1` or a user-verified passkey
  ([`architecture/admin`](../architecture/admin.md#re-confirming-for-a-destructive-act),
  `operator-token-issuance`), and it is then the time of issue. A token
  minted by a credential alone, however recent, carries none, so a silent
  renewal is never a step-up. A pass carries its person's token's, unchanged
  <!-- wl:id step-up-at-only-on-reconfirmation -->
- `role`: the operator's role when an operator token was issued (optional). A
  verifier that holds the operator's record authorises against the role that
  record holds now, never against this claim alone
- `identity_id`: the identity id of the subject the token was minted for
  (optional). An operator token carries the `identity_id` of the credential
  named by `cid`: the operator's identity id at the issuer, which is the
  fingerprint of the identity key it registered with and is kept across every
  change of identity key the issuer accepts
  ([`architecture/admin`](../architecture/admin.md#changing-an-identity-key)).
  A registration token carries the fingerprint of the public key its manifest
  registered, a pass the `identity_id` of the operator token it was
  exchanged for, and a work pass its owner's: the component whose authority
  the run uses, never the actor's and never a person's. It is the issuer's statement, under its
  signature, of who the subject is. A verifier that records who acted records
  this claim and never `sub`, which is a name
  ([`patterns/principal-identity`](../patterns/principal-identity.md) Design
  Principle 10). A token that carries none names nobody a record can join on
- `record_keys`: on an operator token or a pass, the id of each sign-records
  credential the subject held at the issuer, active and unexpired, when the
  token was minted (optional). Each is the fingerprint of that credential's public key.
  It is the issuer's statement, under its signature, of which keys may sign
  records for that subject
  ([`patterns/principal-identity`](../patterns/principal-identity.md),
  `record-signing`). A verifier that receives a signed record with the token
  accepts a signature only by a key named here, and never by the credential
  `cid` names. A revoked credential is missing from every token minted after
  its revocation

### Token Creation
```
1. Serialize header to JSON → base64url encode → headerB64
2. Serialize payload to JSON → base64url encode → payloadB64
3. signingInput = headerB64 + "." + payloadB64
4. signature = sign(privateKey, bytes(signingInput))
5. token = signingInput + "." + base64url(signature)
```

### Token Verification
```
1. Split token on "." → must have exactly 3 parts
2. Decode header (parts[0]) → verify alg == "ML-DSA-65"
3. signingInput = parts[0] + "." + parts[1]
4. Decode signature (parts[2])
5. Verify: verify(issuerPublicKey, bytes(signingInput), signature)
6. Decode payload (parts[1]) → parse claims
7. If exp > 0 and current_time > exp → token expired
8. Return claims
```

### Token Lifetimes
- Agent auth tokens: 24 hours (TokenTTL)
- Channel tokens: 1 hour
- Operator tokens: [`architecture/admin`](../architecture/admin.md#operator-token) states theirs
- Passes: 30 seconds at most ([The pass](#the-pass))
- Work passes: 30 seconds at most ([The work pass](#the-work-pass))

### The pass

Of the WLTs, only a pass names an audience. A component that is presented
an operator token, a registration token or a channel token can present it
again, at any route of any component that accepts its issuer's tokens, as far
as its capabilities reach, until it expires. A person's operator token reaches the
furthest, so no component is ever given one:

- **A person's operator token is presented at the tenant's admin gateway and
  nowhere else.** Every holder of one, a console, the CLI or a script that
  took one from either, sends every request it makes at the tenant to the
  admin gateway, the tenant's one door for people
  ([`architecture/admin`](../architecture/admin.md#contracts),
  `admin-gateway-authorization`). The gateway presents it to one party: the
  orchestrator that issued it, to have it exchanged, and with a request for a
  group the orchestrator itself provides, which the orchestrator judges
  itself. The issuer holds the records the token rests on, so presenting it
  there tells no new party anything.
- **Every other component is reached on a pass.** For each request it
  carries to a component other than the orchestrator, the gateway has the
  orchestrator exchange the person's token for a pass addressed to that one
  component
  ([`architecture/orchestrator`](../architecture/orchestrator.md#token-exchange-post-v1tokenexchange),
  `token-exchange`), and sends the request on the pass. The component never
  holds the person's token, so it holds nothing it could replay elsewhere.
- **The orchestrator never presents a token it received to anyone.** What it
  reports, it reports from the state it holds.

A pass is a WLT the orchestrator signs, shaped as OAuth 2.0 Token Exchange
([RFC 8693](https://www.rfc-editor.org/rfc/rfc8693)) shapes an issued token:
the person's token is the subject token, and the gateway is the actor. It is
signed as every WLT is, under ML-DSA-65, and carries:

| Claim | On a pass |
|---|---|
| `type` | `pass` |
| `aud` | The identity id of the one component it is addressed to: the fingerprint of the public key that component registered, which its own registration token carries as `identity_id` |
| `sub`, `identity_id`, `cid` | The person's token's: its operator, that operator's identity id at the issuer, and the credential the token rests on |
| `act` | The gateway that obtained it, as `{ "sub": <its registered name>, "identity_id": <its registration's identity id> }` |
| `cap` | The intersection of what the exchange was asked for and what the person may use at the exchange, which is what their role carries then and never beyond their token's `cap`. A pass that would carry nothing is not minted |
| `identity_key` | The fingerprint of the person's identity public key at the exchange, which differs from `identity_id` once that person has changed their identity key |
| `record_keys` | The person's sign-records credentials at the issuer that are active and unexpired at the exchange |
| `step_up_at` | The person's token's, unchanged, where that token carries one; absent otherwise |
| `iat`, `exp` | `exp` no more than 30 seconds after `iat` |

1. The orchestrator mints a pass at the exchange alone, and only for an
   operator token it judges live at that moment. A component holding a pass
   therefore holds the orchestrator's judgement of the person's token from
   within the last 30 seconds, and asks nothing again: a removed operator, a
   revoked credential or a lowered role reaches every component at the
   person's next request.
2. A pass is never exchanged again. The exchange takes an operator token as
   its subject, and nothing else.
3. A component accepts a pass only when it verifies under its own
   orchestrator's key, its `type` is `pass`, its `aud` is that component's own
   identity id, and it has not expired. A pass addressed to another component
   is refused with `PASS_AUDIENCE_MISMATCH` and logged as a security event,
   and so is a pass presented to the orchestrator, which is the audience of
   none.
4. Every component but the orchestrator and the admin gateway refuses an
   operator token on every route with `PASS_REQUIRED`, whatever its `cap`, and
   logs a security event: no holder may present one there.
5. A component authorises a person's request against the pass's `cap` alone.
   It records who acted by the pass's `identity_id`, and the gateway that
   carried the request by `act.identity_id`, never by either `sub`: an audit
   entry's `actor` and `via` ([`protocol/types`](types.md#auditentry)).
6. A person-only capability ([`protocol/types`](types.md#capability)) counts
   on an operator token at the orchestrator and on a pass at a component,
   which are a person's, and on no other token.
7. A security event logged under rule 3 or 4 names the refused token by its
   claims, never by the token: its `type`, `sub`, `identity_id` and `cid`, and
   for a pass its `aud` and `act.identity_id`. It never records the
   `Authorization` header or any part of the token's bytes. A refused
   operator token is a live, full-role person's token until it expires, and
   the component's log is the place the pass exists to keep it out of.

This is the one statement of the rule. A blueprint whose client holds operator
tokens, or whose component serves people, points here. Work nobody is present
for is carried on a work pass instead, below.

### The work pass

Some work runs with nobody present: a programme's schedule firing, a
workflow started by an event, an `agent:` instruction the prompt worker runs,
a notice told to the people who hold its positions. No person's operator token
exists for that work, so no pass can be minted for it (rule 2 above), and none
should be: work that runs unattended is never a person's
([`architecture/programme-service`](../architecture/programme-service.md#who-may-do-what),
rule 4). Nor is it the authority of the component that does the work.
Execution and the prompt worker are runners, which
[`patterns/principal-identity`](../patterns/principal-identity.md) Design
Principle 13 calls agents: they act under a subject and are never one.

The subject is the definition's **owner**: the registered component whose
definition is running, such as the programme service for an installed
operation or a domain controller for its workflow. The component doing the
work is the **actor**. A **work pass** carries one request of a run from its
actor to one component, on the owner's authority, as far as a person allowed
it and no further. It rests on a **work authorisation**: a record the
orchestrator holds, made by a person. It is principal-identity's
`agent-delegation` for a service subject, with the orchestrator as the hub
that holds the authorisation.

#### The work authorisation

A `WorkAuthorisation` ([`protocol/types`](types.md#workauthorisation)) names
its owner, the one definition it covers, the actors that may act under it,
its `capabilities`, the person who made it and when it ends.

1. **Only a person makes one.** A person makes a work authorisation at the
   orchestrator, on their own operator token, able to use `work:authorise`
   ([`architecture/admin`](../architecture/admin.md#work-authorisations)). No
   registration token, pass or work pass makes, renews or widens one, because
   nothing that cannot judge may delegate
   ([`patterns/principal-identity`](../patterns/principal-identity.md#implementation-notes)).
   The person is recorded as `authorised_by`: the voucher and the named
   human owner that `service-subject-constraints` requires of a service. Their
   authority is not lent. The work runs on the owner's, and the person is
   recorded as who allowed it, never as who ran it.
2. **Its ceiling is no wider than its maker's.** Every capability it names is
   one the person may use when they make it: their role carries it then, and
   their token's `cap` names it. It names no capability
   [`protocol/types`](types.md#capability) marks *person only*, refused with
   `CAPABILITY_PERSON_ONLY`. It names no `admin:` capability, and none of
   `token:exchange`, `work:exchange` and `work:authorise`, refused with
   `INVALID_REQUEST`, because a work pass reaches no administrative route and
   delegates nothing. Authority is delegated, never invented
   (`principal-invitation`).
3. **It always ends.** `not_after` is required, and is no more than 90 days
   after the authorisation was made or last renewed. Renewing it is a
   person's act under rules 1 and 2, judged against what that person may use
   at the renewal. Past its `not_after`, it mints nothing, and its owner
   reports the definition as not authorised rather than run. Neglect then
   ends in work visibly not running, never in a standing authority nobody
   remembers (principal-identity, Service accounts drift).
4. **Revoking it is immediate, and narrows.** A person revokes one on their
   own operator token: the person it records as `authorised_by`, who made or
   last renewed it, able to use `work:authorise`, or a person able to use
   `admin:*`. Its owner may revoke one that names it
   as owner, on its own registration token, because revoking only narrows; it
   does so when the work it covers is withdrawn
   ([`architecture/programme-service`](../architecture/programme-service.md#withdrawing)).
   A revoked authorisation mints nothing from that moment, so no work pass
   under it outlives the revocation by more than its 30 seconds. The record
   is kept, with who revoked it, when and why, and its id is never reused.
5. **A person who leaves does not stop the work.** Removing an operator
   revokes none of the authorisations they made, because the authority those
   use was never theirs. The orchestrator surfaces them instead: removing the
   operator records each live authorisation they made, and the list of
   authorisations can be filtered to them
   ([`architecture/admin`](../architecture/admin.md#work-authorisations)), as
   `service-subject-constraints` requires of a service whose human owner is
   offboarded. Each still ends at its `not_after` unless another person, under
   rules 1 and 2, renews it.
6. **It names components by identity id, and follows a rotation.** Owner and
   actors are named by identity id, never by name. When a component it names
   changes its key through `POST /v1/rotate-key`, which the old key and the
   new one both sign ([`protocol/spec`](spec.md#post-v1rotate-key)), the
   orchestrator replaces that identity id in every authorisation that names
   it, and records each replacement. A component that registers under a new
   key without rotating is a new subject, and no authorisation names it.

#### Minting a work pass

An actor obtains a work pass from the orchestrator for each request of a run
it sends to a component, at `POST /v1/token/work`
([`architecture/orchestrator`](../architecture/orchestrator.md#work-exchange-post-v1tokenwork),
`work-exchange`). It authenticates with its own registration token, whose
registration declares `work:exchange`, and names the authorisation, the
audience, the capabilities the request needs and its run
(`WorkExchangeRequest`). The orchestrator mints one only while the
authorisation is live, names the caller among its actors, and names an owner
registered there now under the identity id it records. Otherwise it answers
`WORK_AUTHORISATION_UNKNOWN` for an authorisation it does not hold or that
does not name the caller, alike, `WORK_AUTHORISATION_REVOKED` or
`WORK_AUTHORISATION_EXPIRED` for one that has ended, and
`WORK_OWNER_UNREGISTERED` for one whose owner is not registered now, and mints
nothing. Each answer tells the actor a different remedy, so a run it could
not carry out is reported as not authorised for that reason, never as run.

A work pass is a WLT the orchestrator signs, under ML-DSA-65 as every WLT is,
and carries:

| Claim | On a work pass |
|---|---|
| `type` | `work` |
| `aud` | The identity id of the one component it is addressed to |
| `sub`, `identity_id` | The owner's registered name and identity id |
| `act` | The actor that obtained it, as `{ "sub": <its registered name>, "identity_id": <its registration's identity id> }` |
| `cid` | The id of the work authorisation it was minted under |
| `definition` | The definition that authorisation names |
| `run` | The run the actor named |
| `cap` | The intersection of what the request asked for, the authorisation's `capabilities`, and what the owner's, the actor's and the audience's registered manifests each declare. A work pass that would carry nothing is not minted, except one addressed to the owner itself (rule 11) |
| `iat`, `exp` | `exp` no more than 30 seconds after `iat` |

It carries no `identity_key`, `record_keys`, `step_up_at` or `role`. Those are
a person's, and a work pass carries nobody's.

The intersection is the one [`schemas/programme`](../schemas/programme.md#needs-is-a-ceiling-on-an-agent-and-is-refused-beside-does)
states for an agent: its ceiling, the worker's own declaration and what the
identity underneath may do. Here the identity underneath is the owner's
registration, narrowed by what a person allowed for that one definition.

7. **A work pass is never exchanged again, and the orchestrator is the
   audience of none.** Neither exchange takes one as its subject, and the
   orchestrator refuses one on every route with `PASS_AUDIENCE_MISMATCH`,
   logged as a security event.
8. **A component accepts a work pass only when it verifies under its own
   orchestrator's key**, its `type` is `work`, its `aud` is that component's
   own identity id, and it has not expired. One addressed to another
   component is refused with `PASS_AUDIENCE_MISMATCH` and logged as a
   security event, named by its claims as rule 7 of
   [The pass](#the-pass) names a refused token, with its `run`.
9. **A work pass is admitted only where its receiver admits a registered
   component acting in its own right.** It is refused with `FORBIDDEN` on
   every `/v1/admin/*` route, on every route that admits only a person's
   pass, and for every act a blueprint reserves to a person, whatever its
   `cap`. A person-only capability never counts on one: rule 6 of
   [The pass](#the-pass) counts it on a person's tokens alone.
10. **A component authorises a work pass's request against its `cap` alone,
    and records it in full.** Its audit entry's `actor` is the pass's
    `identity_id`, the owner; `via` is `act.identity_id`, the actor;
    `authorisation` is its `cid`; and `run` is its `run`
    ([`protocol/types`](types.md#auditentry)). It never records either `sub`.
    The authorisation names the person who allowed the work, so an auditor
    joins any act of a run to that person through the orchestrator's records.
11. **An owner presented a work pass under its own name checks the
    definition.** Where the pass's `identity_id` is the receiving component's
    own, it accepts the request only when `definition` names a definition it
    holds now, and refuses it with `NOT_FOUND` otherwise, as it answers a
    withdrawn definition. On that check it admits the work that definition is
    its own to do, fetching it and running an action it names, whatever the
    pass's `cap`, which may be empty: that work is the owner's own authority,
    and the pass is the proof that a person allowed it to be fired. This is
    how execution proves to an owner that it is firing that owner's
    definition: only a person can make the authorisation that names it, and
    only the orchestrator signs the pass.
12. **No work pass decides, signs or attests.** It carries no `record_keys`,
    so a record signature presented with one is refused
    ([`patterns/principal-identity`](../patterns/principal-identity.md),
    `record-signing`), and no `step_up_at`, so it never satisfies a step-up.
13. **An actor holds a work pass in memory, for the one request it was minted
    for.** It never writes one to disk or to a log, and never presents one to
    any component but its audience. It is a short-lived operating credential
    under rule 7 of [Service Key Protection](#service-key-protection), and the
    long-lived key that attests it is the orchestrator's, held under rule 8.

#### What each threat reaches

| Threat | What it reaches | What bounds it |
|---|---|---|
| A compromised actor | A work pass under each live authorisation that names it, at any time, not only while a run is firing | Each authorisation's `capabilities`, which a person chose and which never hold a person-only capability, so no direct write to content, no decision, no signature and no attestation (rules 2, 9 and 12). Every mint is audited at the orchestrator with its run. Revoking the authorisation, or deregistering the actor, stops every further mint at once, and the last pass expires within 30 seconds |
| A compromised owner | Nothing it did not hold. It cannot make, renew or widen an authorisation (rule 1). It can serve execution a changed definition, which still runs within the `capabilities` a person allowed for that definition, never wider | Rule 1, and the intersection in every pass's `cap` |
| A stolen work pass | One request's worth at one component | Its `aud`, its `cap`, and at most 30 seconds. It cannot be exchanged (rule 7) |
| A stale authorisation: the adopted map changed, or the work was withdrawn and the authorisation not revoked | At most what it allowed when made, until its `not_after` | 90 days at most (rule 3). The owner refuses a definition it no longer holds (rule 11), and revokes what it withdraws (rule 4). A wider `needs:` in a changed map needs a new authorisation, because none widens |
| A person who leaves | Nothing of theirs: the work never ran on their authority | Their authorisations are surfaced when they are removed, and each ends at its `not_after` unless another person renews it (rules 3 and 5) |
| A person's stolen credential | Authorisations within what that person may use, which their own token already reaches directly | Rule 2, and the record: each authorisation names who made it, and the person who made it, or an admin, revokes it (rule 4) |

> **Gap — an actor's own registration still carries what it declares.**
> A registration is not yet an enrolment
> ([`protocol/spec`](spec.md#post-v1register)), so an actor's registration
> token carries whatever its signed manifest declares, and an actor that
> declares `content:read` or `content:propose` for its work under an
> authorisation can use them on its own token too, with no authorisation and
> no run behind them. The work pass therefore bounds each run to what a
> person allowed for that definition, and records it, but does not yet
> confine an actor that sets out to act outside its runs. That confinement
> is enrolment's: a registration admitted by a person, with what it may hold
> on its own token decided then.

### ID Generation
```
Generate 16 cryptographically random bytes → hex encode → 32-char string
```

## Types

```yaml
types:
  Ed25519KeyPair:
    description: "DEPRECATED — replaced by SigningKeyPair. Do not use."

  SigningKeyPair:
    description: ML-DSA-65 key pair for agent/orchestrator identity (FIPS 204)
    fields:
      algorithm:
        type: string
        description: Signing algorithm identifier
        constraints:
          enum: [ML-DSA-65]
      public_key:
        type: string
        format: base64url
        description: 1952-byte ML-DSA-65 public key, base64url-encoded
      private_key:
        type: string
        format: base64url
        description: 4032-byte ML-DSA-65 private key, base64url-encoded

  WLToken:
    description: Weblisk Token — signed claims for authentication
    fields:
      header:
        type: object
        description: Token header with algorithm and type
        fields:
          alg:
            type: string
            description: Signing algorithm
            constraints:
              enum: [ML-DSA-65]
          typ:
            type: string
            description: Token type identifier
            constraints:
              enum: [WLT]
      payload:
        type: object
        description: Token claims
        fields:
          sub:
            type: string
            description: Subject (agent name or identity)
          iss:
            type: string
            description: Issuer (orchestrator or agent name)
          iat:
            type: int64
            description: Issued at, an RFC 7519 NumericDate (protocol/conventions, Instant)
          exp:
            type: int64
            description: Expires at, an RFC 7519 NumericDate; 0 = no expiry
          cap:
            type: "list<string>"
            description: Granted capability names. Always present on an operator token, an empty list included; an operator token whose cap is absent or empty may use no capability
            required: false
          cid:
            type: string
            description: The record the issuer minted this token under and can
              withdraw — a channel for a channel token, a credential for an
              operator token, for a pass the credential of the operator
              token it was exchanged for, and for a work pass the work
              authorisation it was minted under
            required: false
          type:
            type: string
            description: What the token is for. Absent on agent and channel
              tokens
            required: false
            constraints:
              enum: [operator, attestation, pass, work]
          aud:
            type: string
            description: On a pass and a work pass alone, the identity id of
              the one component it is addressed to
            required: false
          act:
            type: object
            description: On a pass, the gateway that obtained it; on a work
              pass, the actor that obtained it
            required: false
            fields:
              sub:
                type: string
                description: That component's registered name
              identity_id:
                type: string
                description: The identity id of that component's registration
          definition:
            type: string
            description: On a work pass alone, the definition its work
              authorisation names
            required: false
          run:
            type: string
            description: On a work pass alone, the run the request belongs to
            required: false
          identity_key:
            type: string
            description: On a pass alone, the fingerprint of its person's
              identity public key when the pass was minted
            required: false
          step_up_at:
            type: int64
            description: When the subject last completed a step-up, a NumericDate
              (RFC 7519) like iat. A pass carries its person's token's, unchanged
            required: false
          role:
            type: string
            description: The operator's role when an operator token was issued.
              Authorisation reads the role the issuer's records hold now
            required: false
          identity_id:
            type: string
            description: The identity id of the subject. On an operator token,
              the identity_id of the credential cid names, which the issuer
              keeps across a change of the operator's identity key. On a
              registration token, the fingerprint of the key the manifest
              registered. On a work pass, its owner's. What a verifier records
              as who acted, never sub
            required: false
          record_keys:
            type: "list<string>"
            description: On an operator token or a pass, the ids of the subject's
              sign-records credentials at the issuer that were active and
              unexpired when it was minted. The only keys a verifier holding
              the token accepts a record signature from
            required: false
      signature:
        type: string
        format: base64url
        description: ML-DSA-65 signature over header.payload

  KeyRotationRequest:
    description: Request to rotate an agent or orchestrator key (dual-signed)
    fields:
      agent_id:
        type: string
        description: Agent identifier issued at registration
      new_public_key:
        type: string
        format: base64url
        description: New ML-DSA-65 public key (1952 bytes, base64url-encoded)
      current_signature:
        type: string
        format: base64url
        description: Agent manifest signed with current private key
      new_signature:
        type: string
        format: base64url
        description: Same agent manifest signed with new private key
      timestamp:
        type: timestamp
        description: Replay window 300s

  Signature:
    description: A detached ML-DSA-65 signature over canonicalized content
    fields:
      algorithm:
        type: string
        description: Signing algorithm
        constraints:
          enum: [ML-DSA-65]
      value:
        type: string
        format: base64url
        description: 3309-byte ML-DSA-65 signature, base64url-encoded
      signer:
        type: string
        description: Public key of the signer (base64url)
        required: false

  SignatureVerification:
    description: Operations for verifying signed messages and preventing replay
    operations:
      verify_signature:
        input: [message_bytes, signature_base64url, public_key_base64url]
        output: bool
        description: Verify an ML-DSA-65 signature against the signer's public key
      check_replay:
        input: [message_id, timestamp]
        output: bool
        description: Return true if message_id has been seen within the replay window (5 minutes)

  KeyRotationAnnouncement:
    description: A hub telling its peers that its signing key has changed, signed by both keys
    fields:
      hub_name:
        type: string
        description: The hub whose key is rotating
      old_key:
        type: string
        format: base64url
        description: The public key being retired
      new_key:
        type: string
        format: base64url
        description: The public key taking its place
      old_signature:
        type: string
        format: base64url
        description: Announcement signed with the retiring key, proving continuity of the identity
      new_signature:
        type: string
        format: base64url
        description: Announcement signed with the new key, proving possession of it
      timestamp:
        type: timestamp
        format: rfc3339
        description: When the rotation was announced, for replay rejection
```

---

## Authentication

```yaml
authentication:
  mechanism: token
  token_format:
    structure: base64url(header).base64url(payload).base64url(signature)
    fields: [sub, iss, iat, exp, cap, cid]
    signing: ML-DSA-65
    expiry: 24 hours (agent auth), 1 hour (channel), 30 seconds at most (pass, work pass)
    verification: >
      Split on ".", decode header, verify alg == "ML-DSA-65",
      verify signature against issuer public key, check expiry
  flow:
    - step: Agent generates ML-DSA-65 key pair on first run
    - step: Agent signs manifest with private key
    - step: Orchestrator verifies signature with agent public key
    - step: Orchestrator issues WLT token with capabilities
    - step: Agent includes token in all subsequent requests
    - step: Token is verified on every protected endpoint
```

---

## Registration Signature Flow

When an agent registers with the orchestrator:

```
Agent side:
  1. manifest = AgentManifest{name, version, url, public_key, ...}
  2. manifestJSON = canonicalize(manifest)   // RFC 8785 JCS
  3. signature = sign(agent_private_key, manifestJSON)
  4. Send: {manifest, signature, timestamp: now()}

Orchestrator side:
  1. Receive {manifest, signature, timestamp}
  2. Verify |now() - timestamp| < 300 seconds (replay protection)
  3. manifestJSON = canonicalize(manifest)   // RFC 8785 JCS
  4. Verify: verify(manifest.public_key, signature, manifestJSON)
  5. If valid: issue token, register agent
  6. If invalid: reject with 401
```

## Agent-to-Agent Message Signing

When agents communicate directly:

```
Sender:
  1. payload = {from, to, action, payload}
  2. payloadJSON = canonicalize(payload)   // RFC 8785 JCS
  3. signature = sign(sender_private_key, payloadJSON)
  4. Include signature in message

Receiver:
  1. Look up sender's public key from service directory
  2. payloadJSON = canonicalize({from, to, action, payload})   // RFC 8785 JCS
  3. Verify: verify(sender_public_key, signature, payloadJSON)
  4. If invalid: reject with 401
```

## Key Rotation

Key rotation replaces an agent's ML-DSA-65 key pair without
interrupting service. This is required when a key is compromised,
when operational policy mandates periodic rotation, or when an
agent migrates between hosts.

### Rotation Flow

```
Agent side:
  1. Generate new ML-DSA-65 key pair
  2. Sign current manifest with CURRENT private key → current_signature
  3. Sign current manifest with NEW private key → new_signature
  4. Send POST /v1/rotate-key to orchestrator:
     {agent_id, new_public_key, current_signature, new_signature, timestamp}

Orchestrator side:
  1. Look up agent by agent_id
  2. Verify current_signature against agent's current public key
  3. Verify new_signature against new_public_key (proves possession)
  4. Verify |now() - timestamp| < 300 seconds (replay protection)
  5. Update agent's public key in service directory
  6. Broadcast updated service directory to all agents
  7. Respond with updated RegisterResponse (new WLT token)

Agent side (on success):
  1. Replace stored key material (private and public key files)
  2. Begin using new key for all future signing
  3. Old key is no longer valid
```

### Rotation Rules

| Rule | Requirement |
|------|-------------|
| Authentication | Rotation request MUST be signed by current key |
| Atomicity | Directory update and token reissue are atomic |
| Propagation | All agents receive updated directory within 5 seconds |
| Replay protection | Same 300-second window as registration |
| Overlap | No overlap period — old key is invalid immediately |
| Revocation | Old key's tokens are invalidated on rotation |

### Federation Key Rotation

When a hub rotates its federation key, the rotation must be
communicated to all federation peers:

```
1. Hub generates new federation key pair
2. Hub signs rotation announcement with current key
3. Hub sends KeyRotation message to all connected peers
4. Peers verify announcement with hub's current key
5. Peers update their trust store with new public key
6. Hub switches to new key
```

See the Federation protocol spec for the full peer key rotation
handshake and trust store update procedure.

### Recommended Rotation Schedule

| Key Type | Recommended Interval | Mandatory |
|----------|--------------------|-----------|
| Agent keys | 90 days | On compromise |
| Orchestrator key | 90 days | On compromise |
| Federation keys | 180 days | On compromise |
| Channel tokens | 1 hour (automatic) | Built-in expiry |
| Auth tokens | 24 hours (automatic) | Built-in expiry |

**An orchestrator's first key leaves token signing and is kept.** The key
whose fingerprint is its `hub_id` stops signing tokens when the orchestrator
rotates its key, and is kept as a service key to sign `weblisk/hub-proof/v1`
and nothing else, for as long as the hub keeps that `hub_id`
([`architecture/admin`](../architecture/admin.md#proving-the-hub-at-an-address)).
So rotating the orchestrator key does not end a compromise of that first key:
only a new `hub_id`, which a hub regenerated without its state has, does.

---

## Multi-Key Scenarios

### Orchestrator High Availability

In a multi-instance orchestrator deployment, all instances MUST
share the same ML-DSA-65 key pair. The key is loaded from shared
storage (not generated per instance).

### Agent Migration

When an agent moves to a new host:
1. Copy the existing key files to the new host
2. Start the new instance (it registers with the same key)
3. Stop the old instance
4. If key files cannot be copied, perform a key rotation instead

### Key Compromise Recovery

1. Generate new key pair on a clean system
2. Operator uses admin gateway to force-revoke the compromised key:
   `POST /v1/admin/agents/{name}/revoke-key`
3. Agent re-registers with the new key
4. All tokens issued to the old key are invalidated
5. Admin reviews audit trail for unauthorized activity

---

## Standards Alignment: WLT and JWT

The Weblisk Token (WLT) format is structurally identical to JSON Web
Tokens ([RFC 7519](https://www.rfc-editor.org/rfc/rfc7519)) and JSON
Web Signatures ([RFC 7515](https://www.rfc-editor.org/rfc/rfc7515)),
with deliberate deviations:

### What We Adopted from JWT/JWS

| Feature | JWT/JWS Reference | WLT Implementation |
|---------|-------------------|--------------------|
| Three-part structure | RFC 7515 §3 | `header.payload.signature` |
| Base64url encoding | RFC 4648 §5 | Same, no padding |
| Standard claims | RFC 7519 §4.1 | `sub`, `iss`, `iat`, `exp` — same semantics |
| Audience | RFC 7519 §4.1.3 | `aud`, on a pass alone, naming exactly one component by its identity id |
| Actor | RFC 8693 §4.1 | `act`, on a pass alone, naming the gateway that obtained it |
| Signature input | RFC 7515 §5.1 | `base64url(header) + "." + base64url(payload)` |

### What We Customized (and Why)

| Feature | JWT Standard | WLT Choice | Rationale |
|---------|-------------|------------|-----------|
| Token type | `"typ": "JWT"` | `"typ": "WLT"` | Distinguish from generic JWTs; prevent cross-system token confusion |
| Algorithm | JWT Standard | WLT Choice | Rationale |
|---------|-------------|------------|----------|
| Algorithm | RS256, ES256, etc. | `"alg": "ML-DSA-65"` | ML-DSA-65 provides NIST Level 3 post-quantum security; single algorithm eliminates `alg` header confusion attacks |
| Capabilities | Not in JWT | `"cap": [...]` claim | Core to Weblisk's capability-based auth model |
| Issuing record | Not in JWT | `"cid": "..."` claim | Names the channel or credential a token was minted under, so the issuer can end it before `exp` |
| Record-signing keys | Not in JWT | `"record_keys": [...]` claim | Names the subject's live sign-records credentials, so a service that is not the issuer can tell a key that may sign a record, and a revoked one drops out within a token's lifetime |
| Algorithm agility | Multiple algorithms | Single algorithm (ML-DSA-65 only) | Eliminates downgrade attacks entirely; post-quantum from day one |

### Interoperability

WLT tokens are NOT valid JWTs and MUST NOT be sent to JWT-consuming
services. The `typ: WLT` header prevents accidental cross-system use.
For integration with external JWT-based systems (OAuth providers,
API gateways), the `patterns/auth-token` pattern handles JWT
issuance and validation separately.

---

## Error Handling

```yaml
error_codes:
  - code: INVALID_SIGNATURE
    status: 401
    description: ML-DSA-65 signature verification failed
    retryable: false
  - code: TOKEN_EXPIRED
    status: 401
    description: Token past expiry — re-register to get a new one
    retryable: true
  - code: INVALID_REQUEST
    status: 400
    description: Malformed token, key, or rotation request
    retryable: false
  - code: KEY_DECODE_ERROR
    status: 400
    description: Public key or signature could not be decoded
    retryable: false
  - code: PASS_AUDIENCE_MISMATCH
    status: 401
    description: A pass presented to a component its aud does not name,
      the orchestrator included (The pass, rule 3). Logged as a security
      event
    retryable: false
  - code: PASS_REQUIRED
    status: 401
    description: An operator token presented to a component other than the
      orchestrator and the admin gateway (The pass, rule 4). Logged as a
      security event
    retryable: false
  - code: WORK_AUTHORISATION_UNKNOWN
    status: 404
    description: A work pass asked under an authorisation the orchestrator
      does not hold, or one that does not name the caller among its actors.
      The two are answered alike, so a caller learns nothing of an
      authorisation it may not use (The work pass)
    retryable: false
  - code: WORK_AUTHORISATION_REVOKED
    status: 403
    description: A work pass asked under a revoked authorisation (The work
      pass, rule 4). Nothing is minted
    retryable: false
  - code: WORK_AUTHORISATION_EXPIRED
    status: 403
    description: A work pass asked under an authorisation past its not_after
      (The work pass, rule 3). Nothing is minted until a person renews it
    retryable: false
  - code: WORK_OWNER_UNREGISTERED
    status: 409
    description: A work pass asked under an authorisation whose owner is not
      registered now under the identity id it names. Nothing is minted
    retryable: true
```

Each is registered with its HTTP status in [`protocol/types`](types.md),
which is the registry; this list names the codes this document's rules answer
with.

---

## Security

```yaml
security:
  transport:
    - Private keys MUST be stored with restrictive permissions (readable only by owning process)
    - Key directory MUST have restrictive permissions (accessible only by owning process)
    - Private keys MUST NOT be logged, exposed, or transmitted
  signing:
    algorithm: ML-DSA-65 (FIPS 204)
    key_sizes:
      public_key: 1952 bytes
      private_key: 4032 bytes
      signature: 3309 bytes
    process: sign(privateKey, data) → 3309-byte signature
  verification:
    process: verify(publicKey, data, signature) → boolean
  trust_model:
    description: >
      Self-sovereign identity. Each agent generates its own key pair.
      Trust is established through registration signature verification.
      The orchestrator is the root of trust — it issues tokens after
      verifying the agent's self-signed manifest.
  key_security:
    - Use cryptographically secure random source (crypto/rand, Web Crypto API)
    - NEVER hardcode or share private keys
    - Use constant-time comparison for signature verification
    - Validate public key length (1952 bytes for ML-DSA-65) before use
    - Validate signature length (3309 bytes for ML-DSA-65) before use
  replay_protection:
    window: 300 seconds
    applies_to: registration signatures, key rotation requests
```

---

## Implementation Notes

- Keys are stored in a dedicated directory relative to the working directory
- All keys use base64url encoding for portable, size-efficient storage
- Token lifetimes are deliberately short (24h auth, 1h channel) to limit blast radius
- WLT is structurally similar to JWT but uses `typ: WLT` to prevent cross-system confusion
- Single-algorithm design (ML-DSA-65 for everything this protocol signs) eliminates algorithm confusion and downgrade attacks
- The `alg` header field MUST be `ML-DSA-65` — any other value is rejected
- Key rotation is atomic — old key is invalid immediately after rotation, save an orchestrator's first key, which is kept to sign its hub proof and nothing else (Recommended Rotation Schedule)
- Federation key rotation uses dual-signature (old + new) for zero-downtime transitions
- ML-DSA-65 signatures are ~3.3 KB — larger than classical algorithms but necessary for
  quantum resistance. This is an acceptable tradeoff for security
- AES-256-GCM remains quantum-resistant (128-bit equivalent under Grover’s algorithm)
- Argon2id key derivation is unaffected by quantum computing (symmetric primitive)
- No quantum-vulnerable algorithm signs an identity, a token, an attestation or a record anywhere in the framework. The one classical key it admits is a credential that proves a live session, such as a transport credential in a third party's protocol, and no such key signs anything the framework keeps

---

## Verification Checklist

Implementation MUST:
- [ ] Generate ML-DSA-65 key pairs (FIPS 204) for every identity, operating credential, sign-records credential, log key and token this protocol specifies — no other signing algorithm is permitted there ([Post-Quantum Cryptography](#post-quantum-cryptography), [Conventions](#conventions))
- [ ] Reject any identity key, attestation, record signature or token using a non-ML-DSA-65 algorithm. A transport credential a blueprint specifies for a third party's protocol is that blueprint's, and signs nothing this protocol verifies ([Post-Quantum Cryptography](#post-quantum-cryptography))
- [ ] Generate keys with cryptographically secure random source ([Generation](#generation))
- [ ] Store private keys with restricted permissions (readable only by owning process) ([Storage](#storage))
- [ ] Encrypt operator private keys as [Encryption Scheme](#encryption-scheme) says, behind a passphrase as [Key Categories](#key-categories) rule 1 requires it
- [ ] Every operator private key written, handed to a secret source or received from one is the `weblisk-key-v1` envelope with `kdf = argon2id` — never unencrypted, whoever holds it ([Key Categories](#key-categories), rule 1)
- [ ] Support encrypted service keys whose passphrase comes from a secret source ([Key Categories](#key-categories), rule 2)
- [ ] Never accept a private key, other key material or a passphrase from an environment variable, except an installation's master key on a hosted deployment that protects no private key ([Service Key Protection](#service-key-protection), rule 9)
- [ ] Sign and verify with pure ML-DSA-65 and an empty context string, never HashML-DSA ([Sign](#sign))
- [ ] Every fixed-form statement an implementation signs begins with a prefix the [Fixed-Form Statements](#fixed-form-statements) registry lists, followed by one `0x00` byte, and a verifier refuses a prefix the registry does not list
- [ ] An operator token minted on a credential's answer alone carries no `step_up_at`, and one minted on a request whose `weblisk/step-up/v1` re-confirmation verified carries its time of issue; a pass carries its person's token's `step_up_at` unchanged ([Payload (Claims)](#payload-claims)) <!-- wl:check step-up-at-set-once covers step-up-at-only-on-reconfirmation -->
- [ ] A verb, route or function that signs for another program builds the bytes itself and never signs the caller's, and a secret source is asked to sign only bytes its caller built itself ([Fixed-Form Statements](#fixed-form-statements))
- [ ] A proof of an identity to a service that is not a hub is the `weblisk/auth/v1` signature [Proving an identity to a service that is not a hub](#proving-an-identity-to-a-service-that-is-not-a-hub) gives, over a nonce spent and expiring as that section says; the service rebuilds those bytes and never verifies the nonce alone, and no hub accepts one
- [ ] Parse the weblisk-key-v1 format correctly, every field [Private Key Format](#private-key-format) gives
- [ ] Never store passphrase on disk — only hold in memory during decrypt ([Key Categories](#key-categories), rule 4)
- [ ] A failed passphrase fails the operation immediately — no retry loop, no passphrase enumeration — and the platform blueprint states how that is signalled ([Key Categories](#key-categories), rule 5)
- [ ] Verify all signatures before trusting data, using the signature algorithm's verification primitive ([Verify Signature](#verify-signature))
- [ ] Verify token `alg` header is exactly `ML-DSA-65` — reject all other values ([Header](#header))
- [ ] Check token expiry on every verification ([Token Verification](#token-verification))
- [ ] A record of who acted names the token's `identity_id`, never its `sub` ([Payload (Claims)](#payload-claims))
- [ ] An operator token always carries `cap`, and one whose `cap` is absent or empty is read as naming no capability, never as carrying its role's full set ([Payload (Claims)](#payload-claims))
- [ ] A person's operator token is presented by its holder at the tenant's admin gateway alone, and by the gateway to the orchestrator that issued it alone; every other component is sent a person's request on a pass ([The pass](#the-pass))
- [ ] A pass is minted only by the token exchange, for an operator token judged live at that moment, carries the claims [The pass](#the-pass) gives it, expires no more than 30 seconds after it was issued, and is refused as the subject of another exchange
- [ ] A component accepts a pass only when it verifies under its own orchestrator's key and its `aud` is that component's identity id; a pass addressed to another component, or presented to the orchestrator, is refused with `PASS_AUDIENCE_MISMATCH` and logged as a security event ([The pass](#the-pass), rule 3)
- [ ] Every component but the orchestrator and the admin gateway refuses an operator token on every route with `PASS_REQUIRED`, whatever its `cap`, and logs a security event ([The pass](#the-pass), rule 4)
- [ ] The security event for a refused operator token or a foreign pass names the token by the claims [The pass](#the-pass) rule 7 gives, and holds no part of the token or the `Authorization` header
- [ ] A component records a person's act by the pass's `identity_id` and the gateway that carried it by `act.identity_id`, as its audit entry's `actor` and `via` ([The pass](#the-pass), rule 5)
- [ ] The orchestrator never presents a token it received to any party ([The pass](#the-pass))
- [ ] A work authorisation is made and renewed only on a person's operator token able to use `work:authorise`, names no capability that person may not use then, and is refused with `CAPABILITY_PERSON_ONLY` for a person-only capability and `INVALID_REQUEST` for an `admin:` or exchange capability ([The work pass](#the-work-pass), rules 1 and 2)
- [ ] A work authorisation always carries a `not_after` no more than 90 days after it was made or renewed, and mints nothing past it or once revoked ([The work pass](#the-work-pass), rules 3 and 4)
- [ ] Removing an operator revokes none of the work authorisations they made, and records each live one ([The work pass](#the-work-pass), rule 5)
- [ ] A component's key rotation through `POST /v1/rotate-key` replaces its identity id in every work authorisation that names it, and records each replacement ([The work pass](#the-work-pass), rule 6)
- [ ] A work pass is minted only at `POST /v1/token/work`, for an actor the authorisation names, carries the claims and the intersected `cap` [The work pass](#the-work-pass) gives it, and expires no more than 30 seconds after it was issued
- [ ] A work pass presented to the orchestrator, or to a component its `aud` does not name, is refused with `PASS_AUDIENCE_MISMATCH` and logged as a security event ([The work pass](#the-work-pass), rules 7 and 8)
- [ ] A work pass is refused with `FORBIDDEN` on every `/v1/admin/*` route, on every route that admits only a person's pass, and for every act reserved to a person ([The work pass](#the-work-pass), rule 9)
- [ ] A component records a work pass's request with the pass's `identity_id` as `actor`, `act.identity_id` as `via`, `cid` as `authorisation` and `run` as `run` ([The work pass](#the-work-pass), rule 10)
- [ ] An owner presented a work pass under its own identity id refuses it with `NOT_FOUND` unless its `definition` names a definition the owner holds now ([The work pass](#the-work-pass), rule 11)
- [ ] An actor holds a work pass in memory for the one request it was minted for, and never writes it to disk or a log ([The work pass](#the-work-pass), rule 13)
- [ ] Enforce the replay protection window on registration that [Registration Signature Flow](#registration-signature-flow) and [Security](#security) give
- [ ] Validate public key and signature sizes as [Verify Signature](#verify-signature) does
- [ ] Use constant-time comparison for signature verification ([Security](#security))
- [ ] Never log or expose private keys ([Security](#security))
- [ ] Key rotation registers new public key signed by old key and by the new key, and the hub keeps the operator's identity id across it ([Key Rotation](#key-rotation))
- [ ] A rotated operator key is retired, not revoked: once no hub records it, or each hub that still does was abandoned by the person, its private half is destroyed and only its public half is kept for audit ([Key Rotation](#key-rotation))
- [ ] Production deployments have the minimum number of registered operators [Recovery via Backup Operator](#recovery-via-backup-operator) requires
- [ ] Backup operator can remove a compromised operator, whose person then registers again under a new name and a new identity id ([Recovery via Backup Operator](#recovery-via-backup-operator))
- [ ] Bootstrap reset (all keys lost) requires orchestrator restart and re-registration ([Recovery via Bootstrap Reset](#recovery-via-bootstrap-reset))
- [ ] No identity, token, attestation or signed record uses a quantum-vulnerable algorithm ([Post-Quantum Cryptography](#post-quantum-cryptography))
