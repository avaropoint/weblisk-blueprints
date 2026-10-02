<!-- blueprint
type: protocol
name: identity
version: 1.11.0
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
party's service in that service's own protocol, such as the SSH key a content
replica is pushed with ([`patterns/content-git`](../patterns/content-git.md)).
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
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, public_key]
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: AgentMessage
          fields_used: [from, to, action, payload, signature]
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
- NEVER hardcode or share private keys

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
   development, but SHOULD support encrypted keys whose passphrase comes from a
   secret source ([`protocol/secret-source`](secret-source.md)).
3. Production deployments SHOULD encrypt service keys with a passphrase
   supplied at startup by a secret source, such as a secrets manager or a
   secret the platform mounts.
4. The passphrase is NEVER stored on disk. It exists only in memory
   during the decrypt operation. This binds the implementation, which never
   writes a passphrase anywhere; a secret source MAY keep one under its own
   protection, as [`protocol/secret-source`](secret-source.md) describes.
5. Failed passphrase attempts log `security.key_decrypt_failed` and
   exit with code 2 (auth error). No retry loop — the operator
   re-runs the command.

### Service Key Protection

Rules 2 and 3 above date from a model in which a service held one
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

1. Object keys sorted lexicographically by Unicode code point
2. No insignificant whitespace
3. Numbers serialized per ES2015 `JSON.stringify` rules (no trailing zeros,
   no positive sign on exponent)
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
| `weblisk/log-key/v1` | A log owner's long-lived key, introducing the key that signs the log's checkpoints | [`architecture/storage`](../architecture/storage.md#sealing-a-chained-log) |
| `weblisk/log-checkpoint/v1` | A log key, over the log's tip | [`architecture/storage`](../architecture/storage.md#sealing-a-chained-log) |
| `weblisk/log-succession/v1` | A log owner's outgoing and incoming long-lived keys, each over the change from one to the other | [`architecture/storage`](../architecture/storage.md#a-change-of-long-lived-key) |
| `weblisk/content-change/v1` | A person's sign-records credential, over a change to a content entry | [`architecture/content`](../architecture/content.md#the-change-statement) |
| `weblisk/holder-probe/v1` | An identity held by a secret source, proving that the reference reaches it. Nothing accepts it as anything else | [`protocol/secret-source`](secret-source.md#an-identity-held-by-a-source) |

A kind of statement is registered here before any implementation signs it. A
prefix names one layout for good. A changed layout gets a new prefix and a new
row, and a verifier refuses a prefix it does not know.

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
- `iat` (issued at): Unix timestamp
- `exp` (expires at): Unix timestamp (0 = no expiry)
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
  credential's
- `type`: what the token is for, where one issuer mints more than one kind
  (optional). `operator` administers a hub. `attestation` does one thing: it
  submits an attestation for its subject
  ([`architecture/admin`](../architecture/admin.md#operator-token)). An agent
  token and a channel token carry none, so a verifier that requires a `type`
  refuses them. An empty `type` is no `type`
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
  registered. It is the issuer's statement, under its
  signature, of who the subject is. A verifier that records who acted records
  this claim and never `sub`, which is a name
  ([`patterns/principal-identity`](../patterns/principal-identity.md) Design
  Principle 10). A token that carries none names nobody a record can join on
- `record_keys`: on an operator token, the id of each sign-records credential
  the subject held at the issuer, active and unexpired, when the token was
  minted (optional). Each is the fingerprint of that credential's public key.
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

### A token names no audience

A WLT carries no audience claim. A component a token is presented to can
present it again, at any route of any component that accepts its issuer's
tokens, as far as its capabilities reach, until it expires. So whoever holds
an operator token, a console, the CLI or a script that took one from it,
MUST present it to a component other than the orchestrator that issued it
only when it was minted with `cap` naming nothing but what the requests sent
there need ([`architecture/admin`](../architecture/admin.md#contracts),
operator-token-issuance). A token minted with no `cap` carries its role's
full set, and is presented to that orchestrator alone. An admin's token
presented to the content service therefore carries `content:` capabilities
and never `admin:*`, which the content service could otherwise replay at
`/v1/admin/*`. This is the one statement of the rule; a blueprint whose
client holds operator tokens points here.

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
            description: Issued at (Unix epoch seconds)
          exp:
            type: int64
            description: Expires at (Unix epoch seconds, 0 = no expiry)
          cap:
            type: "list<string>"
            description: Granted capability names. Always present on an operator token, an empty list included; an operator token whose cap is absent or empty may use no capability
            required: false
          cid:
            type: string
            description: The record the issuer minted this token under and can
              withdraw — a channel for a channel token, a credential for an
              operator token
            required: false
          type:
            type: string
            description: What the token is for. Absent on agent and channel
              tokens
            required: false
            constraints:
              enum: [operator, attestation]
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
              registered. What a verifier records as who acted, never sub
            required: false
          record_keys:
            type: "list<string>"
            description: On an operator token, the ids of the subject's
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
        type: int64
        description: Unix epoch seconds (replay window 300s)

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
        type: string
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
    expiry: 24 hours (agent auth), 1 hour (channel)
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
   `POST /v1/admin/agents/:name/revoke-key`
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
```

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
- Key rotation is atomic — old key is invalid immediately after rotation
- Federation key rotation uses dual-signature (old + new) for zero-downtime transitions
- ML-DSA-65 signatures are ~3.3 KB — larger than classical algorithms but necessary for
  quantum resistance. This is an acceptable tradeoff for security
- AES-256-GCM remains quantum-resistant (128-bit equivalent under Grover’s algorithm)
- Argon2id key derivation is unaffected by quantum computing (symmetric primitive)
- No quantum-vulnerable algorithm signs an identity, a token, an attestation or a record anywhere in the framework. The one classical key it admits is a credential that proves a live session, such as a transport credential in a third party's protocol, and no such key signs anything the framework keeps

---

## Verification Checklist

Implementation MUST:
- [ ] Generate ML-DSA-65 key pairs (FIPS 204) for every identity, operating credential, sign-records credential, log key and token this protocol specifies — no other signing algorithm is permitted there
- [ ] Reject any identity key, attestation, record signature or token using a non-ML-DSA-65 algorithm. A transport credential a blueprint specifies for a third party's protocol is that blueprint's, and signs nothing this protocol verifies
- [ ] Generate keys with cryptographically secure random source
- [ ] Store private keys with restricted permissions (readable only by owning process)
- [ ] Encrypt operator private keys with Argon2id + AES-256-GCM (passphrase required, min 12 chars)
- [ ] Every operator private key written, handed to a secret source or received from one is the `weblisk-key-v1` envelope with `kdf = argon2id` — never unencrypted, whoever holds it (rule 1)
- [ ] Support encrypted service keys whose passphrase comes from a secret source
- [ ] Never accept a private key, other key material or a passphrase from an environment variable, except an installation's master key on a hosted deployment that protects no private key (rule 9)
- [ ] Sign and verify with pure ML-DSA-65 and an empty context string, never HashML-DSA
- [ ] Every fixed-form statement an implementation signs begins with a prefix the Fixed-Form Statements registry lists, followed by one `0x00` byte, and a verifier refuses a prefix the registry does not list
- [ ] A verb, route or function that signs for another program builds the bytes itself and never signs the caller's, and a secret source is asked to sign only bytes its caller built itself
- [ ] A proof of an identity to a service that is not a hub is a signature over `weblisk/auth/v1`, the service's audience and a nonce it issued, spent by its first use and expiring within 300 seconds; the service rebuilds those bytes and never verifies the nonce alone, and no hub accepts one
- [ ] Parse weblisk-key-v1 format correctly (magic, algorithm=ml-dsa-65, kdf, params, ciphertext)
- [ ] Never store passphrase on disk — only hold in memory during decrypt
- [ ] A failed passphrase terminates the operation immediately — no retry loop, no passphrase enumeration. The platform blueprint states how termination is signalled
- [ ] Verify all signatures before trusting data, using the signature algorithm's verification primitive
- [ ] Verify token `alg` header is exactly `ML-DSA-65` — reject all other values
- [ ] Check token expiry on every verification
- [ ] A record of who acted names the token's `identity_id`, never its `sub`
- [ ] An operator token always carries `cap`, and one whose `cap` is absent or empty is read as naming no capability, never as carrying its role's full set
- [ ] An operator token presented to a component other than the orchestrator that issued it, by any holder, was minted with `cap` naming only what the requests sent there need, and one minted with no `cap` is presented to that orchestrator alone
- [ ] Enforce replay protection window (300 seconds) on registration
- [ ] Validate public key size (1952 bytes) and signature size (3309 bytes)
- [ ] Use constant-time comparison for signature verification
- [ ] Never log or expose private keys
- [ ] Key rotation registers new public key signed by old key and by the new key, and the hub keeps the operator's identity id across it
- [ ] A rotated operator key is retired, not revoked: once no hub records it, or each hub that still does was abandoned by the person, its private half is destroyed and only its public half is kept for audit
- [ ] Production deployments have minimum 2 registered operators for recovery
- [ ] Backup operator can remove a compromised operator, whose person then registers again under a new name and a new identity id
- [ ] Bootstrap reset (all keys lost) requires orchestrator restart and re-registration
- [ ] No identity, token, attestation or signed record uses a quantum-vulnerable algorithm (Ed25519, ECDSA, RSA)
