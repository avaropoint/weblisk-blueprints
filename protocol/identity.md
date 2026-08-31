<!-- blueprint
type: protocol
name: identity
version: 1.0.0
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

Where a platform's standard library does not provide a primitive named here, the
**platform blueprint** names what does. That is a platform blueprint's entire
purpose: translating these requirements into the native terms of one language or
runtime. Concretely, `platforms/go.md` carries a Primitive Mapping table because
Go ships neither a post-quantum signature implementation nor a memory-hard
key-derivation function, and something has to say where a Go implementation gets
them.

Two rules follow, and both have been broken already:

- This document MUST NOT name a module, package, API or language construct. A
  checklist item once read *"verify all signatures … using ML_DSA_65.Verify"*,
  which is an identifier, not a requirement — and no Rust or JavaScript
  implementation has a symbol by that name.
- A platform blueprint MUST NOT restate a requirement from here. `platforms/go.md`
  once carried the key-derivation algorithm with its RFC number and its
  parameters, which made a second normative copy of this section, free to drift
  from it. It may name the module that provides the primitive; it may not
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

All algorithms are quantum-resistant. Weblisk does not use any
quantum-vulnerable algorithms (no RSA, no ECDSA, no Ed25519, no
classical Diffie-Hellman).

**Why ML-DSA-65?** ML-DSA is a lattice-based digital signature scheme
selected by NIST after an 8-year international evaluation process
(FIPS 204, finalized August 2024). It is resistant to both classical
and quantum attacks. ML-DSA-65 provides NIST Security Level 3
(equivalent to AES-192 against classical and quantum adversaries).

**Why not Ed25519?** Ed25519 (elliptic curve) is vulnerable to Shor's
algorithm on quantum computers. Per NIST IR 8547, all elliptic curve
and RSA algorithms will be deprecated by 2030 and removed from NIST
standards by 2035. Weblisk eliminates this class of vulnerability
entirely by using only post-quantum algorithms.

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
  input is impossible (containers, CI, headless servers)
- Restrictive file permissions are the sole protection layer

### Key Categories

| Category | KDF | Passphrase Source | Use Case |
|----------|-----|------------------|----------|
| **Operator keys** | `argon2id` | A non-echoing channel operated by a human | Human-operated tooling |
| **Service keys** (orchestrator, gateway, agent) | `argon2id` or `none` | An injected credential channel, or none | Automated processes |

**Rules:**
1. Operator key generation MUST require a passphrase. It cannot be skipped, and
   the minimum is 12 characters. The channel it arrives over is the platform
   blueprint's to name; a headless implementation uses rules 7 and 8 rather than
   asking a human who is not there.
2. Service key generation defaults to `kdf = none` but SHOULD support
   encrypted keys with passphrase supplied via secure configuration.
3. Production deployments SHOULD encrypt service keys with passphrase
   supplied via secure configuration or secrets manager at startup.
4. The passphrase is NEVER stored on disk. It exists only in memory
   during the decrypt operation.
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

9. A key or passphrase MUST NOT be supplied through an environment
   variable. Environment is readable via `/proc`, container
   inspection, crash dumps and diagnostic output, and it is inherited
   by every child process.

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
2. Current passphrase is required (decrypts existing key)
3. New ML-DSA-65 key pair is generated
4. New passphrase is set (encrypts new key)
5. New public key is registered with orchestrator (signed by old key)
6. Orchestrator validates old-key signature → stores new public key
7. Old key is marked as revoked (preserved for audit)
```

Service keys follow the same rotation protocol but use
secure configuration (secrets manager, environment) instead of
interactive prompts.

### Key Recovery

If an operator loses their passphrase, the encrypted private key is
**unrecoverable by design**. There is no backdoor, no master key, and
no reset mechanism. This section defines the recovery procedures.

#### Recovery via Backup Operator

The primary recovery path is another registered operator:

```
1. Second operator (already registered, admin role) authenticates
2. Revokes the compromised operator's identity
3. Orchestrator invalidates old operator's public key and token
4. Compromised operator generates a new key pair
5. Compromised operator submits a new registration request
6. Registration appears in approvals queue (not auto-approved)
7. Second operator approves the registration
8. Access restored with new identity
```

**Requirement:** Every production deployment MUST have at least two
registered operators. A single-operator deployment has no recovery
path if the passphrase is lost.

#### Recovery via Bootstrap Reset

If ALL operator keys are lost (catastrophic scenario):

```
1. Stop the orchestrator
2. Delete the operator registry from orchestrator storage
3. Restart the orchestrator (enters bootstrap mode)
4. First operator to register becomes admin (same as initial setup)
5. All existing operator tokens are invalidated
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
  3. Return verify(publicKey, data, signature)
  4. Return false on any decode error
```

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
```json
{
  "sub": "seo",
  "iss": "orchestrator",
  "iat": 1712160000,
  "exp": 1712246400,
  "cap": ["file:read", "llm:chat", "agent:message"],
  "cid": ""
}
```

Fields:
- `sub` (subject): agent name or identity
- `iss` (issuer): who created the token ("orchestrator" or agent name)
- `iat` (issued at): Unix timestamp
- `exp` (expires at): Unix timestamp (0 = no expiry)
- `cap` (capabilities): granted capability names (optional)
- `cid` (channel ID): for channel-scoped tokens (optional)

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
            description: Granted capability names
            required: false
          cid:
            type: string
            description: Channel ID for channel-scoped tokens
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
| Channel scoping | Not in JWT | `"cid": "..."` claim | Agent-to-agent channel tokens |
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
- Single-algorithm design (ML-DSA-65 only) eliminates algorithm confusion and downgrade attacks
- The `alg` header field MUST be `ML-DSA-65` — any other value is rejected
- Key rotation is atomic — old key is invalid immediately after rotation
- Federation key rotation uses dual-signature (old + new) for zero-downtime transitions
- ML-DSA-65 signatures are ~3.3 KB — larger than classical algorithms but necessary for
  quantum resistance. This is an acceptable tradeoff for security
- AES-256-GCM remains quantum-resistant (128-bit equivalent under Grover’s algorithm)
- Argon2id key derivation is unaffected by quantum computing (symmetric primitive)
- No quantum-vulnerable algorithms are used anywhere in the framework

---

## Verification Checklist

Implementation MUST:
- [ ] Generate ML-DSA-65 key pairs (FIPS 204) — no other signing algorithm is permitted
- [ ] Reject any key, signature, or token using a non-ML-DSA-65 algorithm
- [ ] Generate keys with cryptographically secure random source
- [ ] Store private keys with restricted permissions (readable only by owning process)
- [ ] Encrypt operator private keys with Argon2id + AES-256-GCM (passphrase required, min 12 chars)
- [ ] Support encrypted service keys via secure configuration
- [ ] Parse weblisk-key-v1 format correctly (magic, algorithm=ml-dsa-65, kdf, params, ciphertext)
- [ ] Never store passphrase on disk — only hold in memory during decrypt
- [ ] A failed passphrase terminates the operation immediately — no retry loop, no passphrase enumeration. The platform blueprint states how termination is signalled
- [ ] Verify all signatures before trusting data, using the signature algorithm's verification primitive
- [ ] Verify token `alg` header is exactly `ML-DSA-65` — reject all other values
- [ ] Check token expiry on every verification
- [ ] Enforce replay protection window (300 seconds) on registration
- [ ] Validate public key size (1952 bytes) and signature size (3309 bytes)
- [ ] Use constant-time comparison for signature verification
- [ ] Never log or expose private keys
- [ ] Key rotation registers new public key signed by old key before revoking old key
- [ ] Revoked keys stored as .key.revoked for audit trail
- [ ] Production deployments have minimum 2 registered operators for recovery
- [ ] Backup operator can revoke and re-register a compromised operator
- [ ] Bootstrap reset (all keys lost) requires orchestrator restart and re-registration
- [ ] No quantum-vulnerable algorithms (Ed25519, ECDSA, RSA) are used anywhere
